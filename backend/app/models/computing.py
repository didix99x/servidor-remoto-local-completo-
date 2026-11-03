"""
Computing models for centralized computing / game streaming.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.orm import relationship

from app.database import Base


class SessionType(PyEnum):
    """Type of streaming session."""
    DESKTOP = "desktop"
    GAME = "game"
    APP = "app"


class SessionStatus(PyEnum):
    """Status of streaming session."""
    CONNECTING = "connecting"
    ACTIVE = "active"
    ENDED = "ended"
    ERROR = "error"


class VideoEncoder(PyEnum):
    """Video encoder types supported by Sunshine."""
    NVENC = "nvenc"
    AMF = "amf"
    QSV = "qsv"
    VAAPI = "vaapi"
    SOFTWARE = "software"


class StreamingSession(Base):
    """Active or historical streaming session."""
    __tablename__ = "streaming_sessions"

    id = Column(BLOB(16), primary_key=True, default=lambda: uuid.uuid4().bytes)
    user_id = Column(BLOB(16), ForeignKey("users.id"), nullable=False)
    device_id = Column(BLOB(16), ForeignKey("devices.id"), nullable=True)

    session_type = Column(Enum(SessionType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    sunshine_session_id = Column(String(128), nullable=True, index=True)
    client_ip = Column(String(45), nullable=True)

    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(Enum(SessionStatus, values_callable=lambda x: [e.value for e in x]), default=SessionStatus.CONNECTING, nullable=False)

    # Stream quality settings
    resolution = Column(String(16), nullable=True)  # e.g., "1920x1080"
    fps = Column(Integer, nullable=True)
    bitrate = Column(Integer, nullable=True)  # kbps
    codec = Column(String(16), nullable=True)  # h264, hevc, av1

    # Error info
    error_message = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", backref="streaming_sessions")
    device = relationship("Device", backref="streaming_sessions")

    def __repr__(self):
        return f"<StreamingSession {self.id.hex()[:8]} {self.session_type.value} {self.status.value}>"


class SunshineConfig(Base):
    """Singleton configuration for Sunshine streaming host."""
    __tablename__ = "sunshine_config"

    id = Column(Integer, primary_key=True, default=1)
    __table_args__ = (UniqueConstraint("id", name="singleton_config"),)

    # Network
    host = Column(String(64), default="0.0.0.0", nullable=False)
    port = Column(Integer, default=47989, nullable=False)  # Stream port
    web_port = Column(Integer, default=47990, nullable=False)  # Web UI port

    # Authentication (Sunshine uses its own auth)
    username = Column(String(64), default="admin", nullable=False)
    password_hash = Column(String(256), nullable=False)

    # Behavior
    is_enabled = Column(Integer, default=1, nullable=False)  # SQLite bool
    auto_start = Column(Integer, default=1, nullable=False)

    # Video encoding
    video_encoder = Column(Enum(VideoEncoder, values_callable=lambda x: [e.value for e in x]), default=VideoEncoder.NVENC, nullable=False)
    audio_encoder = Column(String(32), default="opus", nullable=False)
    max_bitrate = Column(Integer, default=50000, nullable=False)  # kbps
    max_fps = Column(Integer, default=60, nullable=False)
    resolution = Column(String(16), default="1920x1080", nullable=False)

    # Hardware
    gpu_device_id = Column(String(64), nullable=True)  # Specific GPU to use
    enable_hevc = Column(Integer, default=1, nullable=False)
    enable_av1 = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<SunshineConfig enabled={bool(self.is_enabled)} encoder={self.video_encoder.value}>"


class DiscoveredApp(Base):
    """Application/game discovered by Sunshine or system scan."""
    __tablename__ = "discovered_apps"

    id = Column(BLOB(16), primary_key=True, default=lambda: uuid.uuid4().bytes)
    sunshine_app_id = Column(String(128), nullable=True, unique=True, index=True)

    name = Column(String(256), nullable=False)
    executable_path = Column(String(512), nullable=True)
    working_directory = Column(String(512), nullable=True)
    launch_args = Column(String(512), nullable=True)

    # Metadata
    app_type = Column(String(32), nullable=True)  # game, browser, utility, system
    publisher = Column(String(256), nullable=True)
    version = Column(String(64), nullable=True)

    # Sunshine integration
    is_sunshine_app = Column(Integer, default=0, nullable=False)
    sunshine_image_url = Column(String(512), nullable=True)

    # Detection
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Integer, default=1, nullable=False)

    def __repr__(self):
        return f"<DiscoveredApp {self.name} ({self.app_type})>"