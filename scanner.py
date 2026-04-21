from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import routeros_api
import routeros_api.api_structure as _api_structure
from sqlalchemy import select

from database import db_session
from detection import deduplicate_records, is_phone_device, normalize_hostname, normalize_mac
from models import Alert, ConnectionLog, Device, DeviceIP

logger = logging.getLogger(__name__)

# Monkey-patch: MikroTik routers may send hostnames encoded in latin-1 instead of UTF-8.
# routeros_api 0.17.0 does not expose an encoding parameter, so we patch StringField here.
_orig_get_python_value = _api_structure.StringField.get_python_value

def _safe_get_python_value(self, value: bytes) -> str:
    try:
        return _orig_get_python_value(self, value)
    except UnicodeDecodeError:
        if isinstance(value, (bytes, bytearray)):
            return value.decode("latin-1")
        return str(value)

_api_structure.StringField.get_python_value = _safe_get_python_value

ROUTERS = [
    "192.168.1.1",
    "192.168.2.1",
    "192.168.3.1",
    "192.168.4.1",
    "192.168.5.1",
]
# Router to location mapping:
# 192.168.1.1 -> Școala 1
# 192.168.2.1 -> Școala 2
# 192.168.3.1 -> Școala 3
# 192.168.4.1 -> Școala 4
# 192.168.5.1 -> Grădinița 3

ROUTER_USERNAME = "openclaw"
ROUTER_PASSWORD = "Liesti2026"
SCAN_INTERVAL_SECONDS = 420


class MikroTikScanner:
    def __init__(self, routers: list[str] | None = None):
        self.routers = routers or ROUTERS

    def _collect_from_router(self, router_ip: str) -> list[dict[str, Any]]:
        logger.info("Collecting data from router %s", router_ip)
        pool = routeros_api.RouterOsApiPool(
            router_ip,
            username=ROUTER_USERNAME,
            password=ROUTER_PASSWORD,
            port=8728,
            plaintext_login=True,
            use_ssl=False,
        )
        api = pool.get_api()

        leases = api.get_resource("/ip/dhcp-server/lease").get()
        arp_rows = api.get_resource("/ip/arp").get()
        pool.disconnect()

        arp_by_mac: dict[str, str] = {}
        for arp in arp_rows:
            mac = normalize_mac(arp.get("mac-address"))
            ip = arp.get("address")
            if mac and ip:
                arp_by_mac[mac] = ip

        results: list[dict[str, Any]] = []
        for lease in leases:
            mac = normalize_mac(lease.get("mac-address"))
            if not mac:
                continue
            hostname = normalize_hostname(lease.get("host-name"))
            ip = lease.get("address") or arp_by_mac.get(mac)
            if not ip:
                continue
            results.append(
                {
                    "mac_address": mac,
                    "ip_address": ip,
                    "hostname": hostname,
                    "dhcp_server": lease.get("server"),
                    "router_ip": router_ip,
                    "vendor": None,
                }
            )
        return results

    async def collect_all(self) -> list[dict[str, Any]]:
        all_records: list[dict[str, Any]] = []
        for router_ip in self.routers:
            try:
                rows = await asyncio.to_thread(self._collect_from_router, router_ip)
                all_records.extend(rows)
            except Exception as exc:
                logger.exception("Failed collecting from %s: %s", router_ip, exc)
        return deduplicate_records(all_records)


def _create_alert(mac: str, alert_type: str, message: str) -> Alert:
    return Alert(mac_address=mac, alert_type=alert_type, message=message)


def process_scan_results(records: list[dict[str, Any]]) -> None:
    now = datetime.now(timezone.utc)
    with db_session() as session:
        was_offline = {d.mac_address: d.is_offline for d in session.scalars(select(Device)).all()}
        for rec in records:
            sources = rec.get("sources", [])
            primary_vlan = rec.get("vlan", rec.get("dhcp_server"))
            mac = rec["mac_address"]
            hostname = rec.get("hostname")
            vendor = rec.get("vendor")

            existing = session.scalar(select(Device).where(Device.mac_address == mac))
            if not existing:
                device = Device(
                    mac_address=mac,
                    vendor=vendor,
                    hostname=hostname,
                    first_seen=now,
                    last_seen=now,
                    seen_count=1,
                    is_trusted=False,
                    is_phone=is_phone_device(hostname, vendor),
                )
                device.refresh_offline_status()
                session.add(device)
                session.add(
                    ConnectionLog(
                        mac_address=mac,
                        event_type="connected",
                        ip_address=rec["ip_address"],
                        vlan=primary_vlan,
                        router_ip=rec["router_ip"],
                        hostname=hostname,
                        timestamp=now,
                    )
                )
                session.flush()
                session.add(
                    DeviceIP(
                        device_id=device.id,
                        ip_address=rec["ip_address"],
                        vlan=primary_vlan,
                        router_ip=rec["router_ip"],
                        timestamp=now,
                    )
                )
                inserted_signatures = {(rec["ip_address"], primary_vlan, rec["router_ip"])}
                for source in sources[1:]:
                    source_vlan = source.get("vlan", source.get("dhcp_server"))
                    signature = (source["ip_address"], source_vlan, source["router_ip"])
                    if signature in inserted_signatures:
                        continue
                    session.add(
                        DeviceIP(
                            device_id=device.id,
                            ip_address=source["ip_address"],
                            vlan=source_vlan,
                            router_ip=source["router_ip"],
                            timestamp=now,
                        )
                    )
                    inserted_signatures.add(signature)
                session.add(
                    _create_alert(
                        mac,
                        "new_device",
                        f"New device discovered: {mac} ({hostname or 'unknown'})",
                    )
                )
                continue

            existing.last_seen = now
            existing.seen_count += 1
            existing.hostname = existing.hostname or hostname
            existing.vendor = existing.vendor or vendor
            existing.is_phone = existing.is_phone or is_phone_device(hostname, vendor)
            existing.is_trusted = existing.seen_count > 20
            existing.refresh_offline_status()
            if was_offline.get(mac, False) and not existing.is_offline:
                session.add(
                    ConnectionLog(
                        mac_address=mac,
                        event_type="connected",
                        ip_address=rec["ip_address"],
                        vlan=primary_vlan,
                        router_ip=rec["router_ip"],
                        hostname=existing.hostname,
                        timestamp=now,
                    )
                )

            existing_ip_signatures = {
                (ip_row.ip_address, ip_row.vlan, ip_row.router_ip)
                for ip_row in existing.ips
            }
            latest_ip = existing.ips[0] if existing.ips else None
            if (
                latest_ip is None
                or latest_ip.ip_address != rec["ip_address"]
                or latest_ip.vlan != primary_vlan
                or latest_ip.router_ip != rec["router_ip"]
            ):
                session.add(
                    DeviceIP(
                        device_id=existing.id,
                        ip_address=rec["ip_address"],
                        vlan=primary_vlan,
                        router_ip=rec["router_ip"],
                        timestamp=now,
                    )
                )
                existing_ip_signatures.add((rec["ip_address"], primary_vlan, rec["router_ip"]))
                if (
                    latest_ip is not None
                    and (
                        latest_ip.ip_address != rec["ip_address"]
                        or latest_ip.vlan != primary_vlan
                        or latest_ip.router_ip != rec["router_ip"]
                    )
                ):
                    session.add(
                        ConnectionLog(
                            mac_address=mac,
                            event_type="network_change",
                            ip_address=rec["ip_address"],
                            vlan=primary_vlan,
                            router_ip=rec["router_ip"],
                            old_ip=latest_ip.ip_address,
                            old_vlan=latest_ip.vlan,
                            old_router_ip=latest_ip.router_ip,
                            hostname=existing.hostname,
                            timestamp=now,
                        )
                    )

            for source in sources[1:]:
                source_vlan = source.get("vlan", source.get("dhcp_server"))
                signature = (source["ip_address"], source_vlan, source["router_ip"])
                if signature in existing_ip_signatures:
                    continue
                session.add(
                    DeviceIP(
                        device_id=existing.id,
                        ip_address=source["ip_address"],
                        vlan=source_vlan,
                        router_ip=source["router_ip"],
                        timestamp=now,
                    )
                )
                existing_ip_signatures.add(signature)

        devices = session.scalars(select(Device)).all()
        for device in devices:
            device.refresh_offline_status()
        for device in devices:
            if not was_offline.get(device.mac_address, True) and device.is_offline:
                latest_ip = device.ips[0] if device.ips else None
                session.add(
                    ConnectionLog(
                        mac_address=device.mac_address,
                        event_type="disconnected",
                        ip_address=latest_ip.ip_address if latest_ip else None,
                        vlan=latest_ip.vlan if latest_ip else None,
                        router_ip=latest_ip.router_ip if latest_ip else None,
                        hostname=device.hostname,
                        timestamp=now,
                    )
                )


async def scan_once(scanner: MikroTikScanner) -> None:
    results = await scanner.collect_all()
    process_scan_results(results)


async def scanner_loop() -> None:
    scanner = MikroTikScanner()
    while True:
        try:
            await scan_once(scanner)
        except Exception as exc:
            logger.exception("Scan cycle failed: %s", exc)
        await asyncio.sleep(SCAN_INTERVAL_SECONDS)
