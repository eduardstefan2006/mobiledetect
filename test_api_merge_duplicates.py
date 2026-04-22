from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from api import merge_duplicate_devices
from database import Base
from models import ConnectionLog, Device, DeviceIP


def test_merge_duplicate_devices_groups_by_hostname_case_insensitive() -> None:
    engine = create_engine('sqlite+pysqlite:///:memory:', future=True)
    Base.metadata.create_all(bind=engine)

    now = datetime.now(timezone.utc)

    with Session(engine) as db:
        primary = Device(
            mac_address='aa:aa:aa:aa:aa:aa',
            hostname='S25-al-utilizatorului-Madalina',
            seen_count=5,
            first_seen=now - timedelta(days=3),
            last_seen=now - timedelta(hours=1),
        )
        duplicate = Device(
            mac_address='bb:bb:bb:bb:bb:bb',
            hostname='s25-AL-utilizatorului-madalina',
            seen_count=2,
            first_seen=now - timedelta(days=5),
            last_seen=now,
        )
        other = Device(
            mac_address='cc:cc:cc:cc:cc:cc',
            hostname='Alt-dispozitiv',
            seen_count=1,
            first_seen=now - timedelta(days=1),
            last_seen=now - timedelta(minutes=10),
        )

        db.add_all([primary, duplicate, other])
        db.flush()

        db.add_all([
            DeviceIP(device_id=primary.id, ip_address='192.168.3.10', vlan='v1', router_ip='192.168.3.1', timestamp=now - timedelta(hours=1)),
            DeviceIP(device_id=duplicate.id, ip_address='192.168.3.55', vlan='v55', router_ip='192.168.3.1', timestamp=now),
            ConnectionLog(mac_address=duplicate.mac_address, event_type='connected', ip_address='192.168.3.55', vlan='v55', router_ip='192.168.3.1', timestamp=now),
        ])
        db.commit()

        result = merge_duplicate_devices(db)
        assert result == {'merged': 1}

        devices = db.scalars(select(Device).order_by(Device.mac_address)).all()
        assert [device.mac_address for device in devices] == ['aa:aa:aa:aa:aa:aa', 'cc:cc:cc:cc:cc:cc']

        merged_primary = db.scalar(select(Device).where(Device.mac_address == 'aa:aa:aa:aa:aa:aa'))
        assert merged_primary is not None
        assert merged_primary.seen_count == 7
        assert merged_primary.last_seen.replace(tzinfo=timezone.utc) == now
        assert merged_primary.first_seen.replace(tzinfo=timezone.utc) == now - timedelta(days=5)

        ips = db.scalars(select(DeviceIP).order_by(DeviceIP.ip_address)).all()
        assert len(ips) == 2
        assert all(ip.device_id == merged_primary.id for ip in ips)

        logs = db.scalars(select(ConnectionLog)).all()
        assert len(logs) == 1
        assert logs[0].mac_address == merged_primary.mac_address
