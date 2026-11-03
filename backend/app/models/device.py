"""
Device models for network monitoring.
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    DateTime,
    Enum,
    String,
    Boolean,
    Integer,
    ForeignKey,
    Text,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DeviceType(str, PyEnum):
    """Known device types."""
    COMPUTER = "computer"
    PHONE = "phone"
    TABLET = "tablet"
    SMART_TV = "smart_tv"
    PRINTER = "printer"
    ROUTER = "router"
    NAS = "nas"
    IOT = "iot"
    GAMING = "gaming"
    UNKNOWN = "unknown"


class Device(Base):
    """Network device model."""
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mac_address: Mapped[str] = mapped_column(
        String(17), unique=True, index=True, nullable=False
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), index=True, nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_type: Mapped[DeviceType] = mapped_column(
        Enum(DeviceType, native_enum=False),
        default=DeviceType.UNKNOWN,
        nullable=False,
    )
    os_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_known: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_authorized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    history: Mapped[list["DeviceHistory"]] = relationship(
        "DeviceHistory",
        back_populates="device",
        lazy="selectin",
        order_by="DeviceHistory.timestamp.desc()",
    )
    permissions: Mapped[list["SharePermission"]] = relationship(
        "SharePermission",
        back_populates="device",
        lazy="selectin",
    )
    pairing_requests: Mapped[list["PairingRequest"]] = relationship(
        "PairingRequest",
        back_populates="device",
        lazy="selectin",
    )

    # Indexes
    __table_args__ = (
        Index("ix_devices_ip_mac", "ip_address", "mac_address"),
        Index("ix_devices_online_known", "is_online", "is_known"),
    )

    def __repr__(self) -> str:
        return f"<Device(mac='{self.mac_address}', ip='{self.ip_address}', name='{self.hostname}')>"


class DeviceHistory(Base):
    """Historical record of device events."""
    __tablename__ = "device_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    device: Mapped["Device"] = relationship(
        "Device",
        back_populates="history",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DeviceHistory(device_id={self.device_id}, event='{self.event_type}')>"