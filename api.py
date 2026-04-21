from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Alert, Device

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
def get_devices(db: Session = Depends(get_db)) -> list[dict]:
    devices = db.scalars(
        select(Device).options(joinedload(Device.ips)).order_by(Device.last_seen.desc())
    ).unique().all()
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
