"""
Share models for file sharing.
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


class ShareType(str, PyEnum):
    """Type of share."""
    FOLDER = "folder"
    FILE = "file"


class PermissionLevel(str, PyEnum):
    """Permission levels for shares."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"


class Share(Base):
    """File/folder share model."""
    __tablename__ = "shares"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    share_type: Mapped[ShareType] = mapped_column(
        Enum(ShareType, native_enum=False),
        default=ShareType.FOLDER,
        nullable=False,
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="shares",
        lazy="selectin",
    )
    permissions: Mapped[list["SharePermission"]] = relationship(
        "SharePermission",
        back_populates="share",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Share(id={self.id}, name='{self.name}', path='{self.path}')>"


class SharePermission(Base):
    """Permission for a device on a share."""
    __tablename__ = "share_permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    share_id: Mapped[int] = mapped_column(
        ForeignKey("shares.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission: Mapped[PermissionLevel] = mapped_column(
        Enum(PermissionLevel, native_enum=False),
        default=PermissionLevel.READ,
        nullable=False,
    )
    granted_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    share: Mapped["Share"] = relationship(
        "Share",
        back_populates="permissions",
        lazy="selectin",
    )
    device: Mapped["Device"] = relationship(
        "Device",
        back_populates="permissions",
        lazy="selectin",
    )
    granted_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="granted_permissions",
        lazy="selectin",
    )

    # Unique constraint: one permission per device per share
    __table_args__ = (
        Index("ix_share_perm_unique", "share_id", "device_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<SharePermission(share={self.share_id}, device={self.device_id}, perm='{self.permission}')>"