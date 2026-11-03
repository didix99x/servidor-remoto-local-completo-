# Import all models so SQLAlchemy can discover them
from app.models.user import User, UserRole
from app.models.device import Device, DeviceHistory, DeviceType
from app.models.pairing import PairingRequest, PairingStatus
from app.models.share import Share, SharePermission, ShareType, PermissionLevel
from app.models.audit import AuditLog
from app.models.settings import Setting
from app.models.computing import (
    StreamingSession,
    SessionType,
    SessionStatus,
    SunshineConfig,
    VideoEncoder,
    DiscoveredApp,
)

__all__ = [
    "User", "UserRole",
    "Device", "DeviceHistory", "DeviceType",
    "PairingRequest", "PairingStatus",
    "Share", "SharePermission", "ShareType", "PermissionLevel",
    "AuditLog",
    "Setting",
    "StreamingSession", "SessionType", "SessionStatus",
    "SunshineConfig", "VideoEncoder", "DiscoveredApp",
]
