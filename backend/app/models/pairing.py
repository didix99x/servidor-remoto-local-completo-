"""
Pairing request model for device authorization.
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    DateTime,
    Enum,
    String,
    Text,
    ForeignKey,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PairingStatus(str, PyEnum):
    """Status of a pairing request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PairingRequest(Base):
    """Device pairing/authorization request."""
    __tablename__ = "pairing_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requester_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[PairingStatus] = mapped_column(
        Enum(PairingStatus, native_enum=False),
        default=PairingStatus.PENDING,
        nullable=False,
        index=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    responded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    device: Mapped["Device"] = relationship(
        "Device",
        back_populates="pairing_requests",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_pairing_device_status", "device_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<PairingRequest(device={self.device_id}, status='{self.status}')>"