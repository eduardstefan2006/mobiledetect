from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from database import get_db
from detection import is_phone_device
from models import Alert, ConnectionLog, Device, DeviceIP

router = APIRouter()


def _latest_ip_payload(device: Device) -> dict | None:
    latest = device.ips[0] if device.ips else None
    if not latest:
        return None
    return {
        "ip_address": latest.ip_address,
        "vlan": latest.vlan,
        "router_ip": latest.router_ip,
        "timestamp": latest.timestamp,
    }


def _connection_timestamp_maps(
    db: Session,
) -> tuple[dict[str, datetime | None], dict[str, datetime | None]]:
    last_connected_sq = (
        select(
            ConnectionLog.mac_address,
            func.max(ConnectionLog.timestamp).label("connected_at"),
        )
        .where(ConnectionLog.event_type == "connected")
        .group_by(ConnectionLog.mac_address)
        .subquery()
    )
    last_disconnected_sq = (
        select(
            ConnectionLog.mac_address,
            func.max(ConnectionLog.timestamp).label("disconnected_at"),
        )
        .where(ConnectionLog.event_type == "disconnected")
        .group_by(ConnectionLog.mac_address)
        .subquery()
    )

    connected_map = {
        row.mac_address: row.connected_at
        for row in db.execute(select(last_connected_sq)).all()
    }
    disconnected_map = {
        row.mac_address: row.disconnected_at
        for row in db.execute(select(last_disconnected_sq)).all()
    }
    return connected_map, disconnected_map


@router.get("/devices")
def get_devices(phones_only: bool = False, db: Session = Depends(get_db)) -> list[dict]:
    query = select(Device).options(joinedload(Device.ips)).order_by(Device.last_seen.desc())
    if phones_only:
        query = query.where(Device.is_phone.is_(True))
    devices = db.scalars(query).unique().all()
    connected_map, disconnected_map = _connection_timestamp_maps(db)
    response = []
    for device in devices:
        response.append(
            {
                "mac_address": device.mac_address,
                "vendor": device.vendor,
                "hostname": device.hostname,
                "first_seen": device.first_seen,
                "last_seen": device.last_seen,
                "seen_count": device.seen_count,
                "is_trusted": device.is_trusted,
                "is_offline": device.is_offline,
                "is_phone": device.is_phone,
                "latest_network": _latest_ip_payload(device),
                "connected_at": connected_map.get(device.mac_address),
                "disconnected_at": disconnected_map.get(device.mac_address),
            }
        )
    return response


@router.post("/devices/re-evaluate-mobile-devices")
@router.post("/devices/re-evaluate-phones")
@router.post("/devices/reevaluate")
def re_evaluate_phone_flags(db: Session = Depends(get_db)) -> dict:
    devices = db.scalars(select(Device).execution_options(yield_per=500))
    updated = 0
    total = 0
    for device in devices:
        total += 1
        new_value = is_phone_device(device.hostname, device.vendor, device.mac_address)
        if device.is_phone != new_value:
            device.is_phone = new_value
            updated += 1
    db.commit()
    return {"updated": updated, "total": total}


@router.post("/devices/merge-duplicates")
def merge_duplicate_devices(db: Session = Depends(get_db)) -> dict:
    duplicate_hostnames = db.execute(
        select(func.lower(Device.hostname).label("hostname_key"))
        .where(Device.hostname.is_not(None))
        .group_by(func.lower(Device.hostname))
        .having(func.count(Device.id) > 1)
    ).all()

    merged = 0
    for row in duplicate_hostnames:
        hostname_key = row.hostname_key
        devices_with_hostname = db.scalars(
            select(Device)
            .where(func.lower(Device.hostname) == hostname_key)
            .order_by(Device.seen_count.desc(), Device.last_seen.desc())
        ).all()

        if len(devices_with_hostname) < 2:
            continue

        primary = devices_with_hostname[0]
        duplicates = devices_with_hostname[1:]

        for duplicate in duplicates:
            db.execute(
                update(DeviceIP)
                .where(DeviceIP.device_id == duplicate.id)
                .values(device_id=primary.id)
            )
            db.execute(
                update(ConnectionLog)
                .where(ConnectionLog.mac_address == duplicate.mac_address)
                .values(mac_address=primary.mac_address)
            )

            primary.seen_count += duplicate.seen_count
            if duplicate.last_seen and (not primary.last_seen or duplicate.last_seen > primary.last_seen):
                primary.last_seen = duplicate.last_seen
            if duplicate.first_seen and (not primary.first_seen or duplicate.first_seen < primary.first_seen):
                primary.first_seen = duplicate.first_seen

            db.delete(duplicate)
            merged += 1

    db.commit()
    return {"merged": merged}


@router.get("/devices/{mac}")
def get_device(mac: str, db: Session = Depends(get_db)) -> dict:
    device = db.scalar(select(Device).options(joinedload(Device.ips)).where(Device.mac_address == mac.lower()))
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    connected_map, disconnected_map = _connection_timestamp_maps(db)

    history = [
        {
            "ip_address": ip.ip_address,
            "vlan": ip.vlan,
            "router_ip": ip.router_ip,
            "timestamp": ip.timestamp,
        }
        for ip in device.ips
    ]

    logs = db.scalars(
        select(ConnectionLog)
        .where(ConnectionLog.mac_address == mac.lower())
        .order_by(ConnectionLog.timestamp.desc())
        .limit(100)
    ).all()

    connection_logs = [
        {
            "event_type": log.event_type,
            "ip_address": log.ip_address,
            "vlan": log.vlan,
            "router_ip": log.router_ip,
            "old_ip": log.old_ip,
            "old_vlan": log.old_vlan,
            "old_router_ip": log.old_router_ip,
            "hostname": log.hostname,
            "timestamp": log.timestamp,
        }
        for log in logs
    ]

    return {
        "mac_address": device.mac_address,
        "vendor": device.vendor,
        "hostname": device.hostname,
        "first_seen": device.first_seen,
        "last_seen": device.last_seen,
        "seen_count": device.seen_count,
        "is_trusted": device.is_trusted,
        "is_offline": device.is_offline,
        "is_phone": device.is_phone,
        "latest_network": _latest_ip_payload(device),
        "connected_at": connected_map.get(device.mac_address),
        "disconnected_at": disconnected_map.get(device.mac_address),
        "history": history,
        "connection_logs": connection_logs,
    }


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db)) -> list[dict]:
    alerts = db.scalars(
        select(Alert).where(Alert.is_resolved.is_(False)).order_by(Alert.created_at.desc())
    ).all()

    return [
        {
            "id": alert.id,
            "mac_address": alert.mac_address,
            "alert_type": alert.alert_type,
            "message": alert.message,
            "created_at": alert.created_at,
            "is_resolved": alert.is_resolved,
        }
        for alert in alerts
    ]


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)) -> dict:
    alert = db.scalar(select(Alert).where(Alert.id == alert_id))
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.is_resolved:
        return {"id": alert.id, "resolved": False, "already_resolved": True}

    alert.is_resolved = True
    db.commit()
    return {"id": alert.id, "resolved": True, "already_resolved": False}


@router.post("/alerts/resolve-all")
def resolve_all_alerts(db: Session = Depends(get_db)) -> dict:
    result = db.execute(
        update(Alert)
        .where(Alert.is_resolved.is_(False))
        .values(is_resolved=True)
    )
    db.commit()
    return {"resolved": True, "updated_count": result.rowcount or 0}


@router.get("/logs")
def get_connection_logs(
    mac: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 200,
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(ConnectionLog).order_by(ConnectionLog.timestamp.desc()).limit(limit)
    if mac:
        query = query.where(ConnectionLog.mac_address == mac.lower())
    if event_type:
        query = query.where(ConnectionLog.event_type == event_type)
    logs = db.scalars(query).all()
    return [
        {
            "id": log.id,
            "mac_address": log.mac_address,
            "event_type": log.event_type,
            "ip_address": log.ip_address,
            "vlan": log.vlan,
            "router_ip": log.router_ip,
            "old_ip": log.old_ip,
            "old_vlan": log.old_vlan,
            "old_router_ip": log.old_router_ip,
            "hostname": log.hostname,
            "timestamp": log.timestamp,
        }
        for log in logs
    ]
