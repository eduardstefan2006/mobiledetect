from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from database import get_db
from detection import is_phone_device
from models import Alert, ConnectionLog, Device

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


@router.get("/devices")
def get_devices(phones_only: bool = False, db: Session = Depends(get_db)) -> list[dict]:
    query = select(Device).options(joinedload(Device.ips)).order_by(Device.last_seen.desc())
    if phones_only:
        query = query.where(Device.is_phone.is_(True))
    devices = db.scalars(query).unique().all()
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
            }
        )
    return response


@router.post("/devices/re-evaluate-phones")
def re_evaluate_phone_flags(db: Session = Depends(get_db)) -> dict:
    devices = db.scalars(select(Device)).all()
    updated = 0
    for device in devices:
        new_value = is_phone_device(device.hostname, device.vendor, device.mac_address)
        if device.is_phone != new_value:
            device.is_phone = new_value
            updated += 1
    return {"processed": len(devices), "updated": updated}


@router.get("/devices/{mac}")
def get_device(mac: str, db: Session = Depends(get_db)) -> dict:
    device = db.scalar(select(Device).options(joinedload(Device.ips)).where(Device.mac_address == mac.lower()))
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    history = [
        {
            "ip_address": ip.ip_address,
            "vlan": ip.vlan,
            "router_ip": ip.router_ip,
            "timestamp": ip.timestamp,
        }
        for ip in device.ips
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
        "history": history,
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
