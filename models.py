from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    mac_address: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    seen_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_offline: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_phone: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    ips: Mapped[list["DeviceIP"]] = relationship(
        "DeviceIP",
        back_populates="device",
        cascade="all, delete-orphan",
        order_by="DeviceIP.timestamp.desc()",
    )

    def refresh_offline_status(self) -> None:
        threshold = datetime.now(timezone.utc) - timedelta(minutes=10)
        self.is_offline = self.last_seen < threshold


class DeviceIP(Base):
    __tablename__ = "device_ips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    vlan: Mapped[str | None] = mapped_column(String(255), nullable=True)
    router_ip: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    device: Mapped[Device] = relationship("Device", back_populates="ips")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    mac_address: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ConnectionLog(Base):
    __tablename__ = "connection_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    mac_address: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vlan: Mapped[str | None] = mapped_column(String(255), nullable=True)
    router_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    old_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    old_vlan: Mapped[str | None] = mapped_column(String(255), nullable=True)
    old_router_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
