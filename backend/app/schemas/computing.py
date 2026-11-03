"""
Schemas for centralized computing / game streaming API.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SessionType(str, Enum):
    DESKTOP = "desktop"
    GAME = "game"
    APP = "app"


class SessionStatus(str, Enum):
    CONNECTING = "connecting"
    ACTIVE = "active"
    ENDED = "ended"
    ERROR = "error"


class VideoEncoder(str, Enum):
    NVENC = "nvenc"
    AMF = "amf"
    QSV = "qsv"
    VAAPI = "vaapi"
    SOFTWARE = "software"


# =============================================================================
# Sunshine Config
# =============================================================================

class SunshineConfigBase(BaseModel):
    host: str = Field(default="0.0.0.0", pattern=r"^(\d{1,3}\.){3}\d{1,3}$|^0\.0\.0\.0$|^::1$|^\[?::\]?$")
    port: int = Field(default=47989, ge=1024, le=65535)
    web_port: int = Field(default=47990, ge=1024, le=65535)
    username: str = Field(default="admin", min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=128)  # Plain password for input
    is_enabled: bool = True
    auto_start: bool = True
    video_encoder: VideoEncoder = VideoEncoder.NVENC
    audio_encoder: str = Field(default="opus", pattern=r"^(opus|aac)$")
    max_bitrate: int = Field(default=50000, ge=1000, le=200000)  # kbps
    max_fps: int = Field(default=60, ge=15, le=240)
    resolution: str = Field(default="1920x1080", pattern=r"^\d+x\d+$")
    gpu_device_id: Optional[str] = None
    enable_hevc: bool = True
    enable_av1: bool = False


class SunshineConfigCreate(SunshineConfigBase):
    pass


class SunshineConfigUpdate(BaseModel):
    host: Optional[str] = Field(default=None, pattern=r"^(\d{1,3}\.){3}\d{1,3}$|^0\.0\.0\.0$|^::1$|^\[?::\]?$")
    port: Optional[int] = Field(default=None, ge=1024, le=65535)
    web_port: Optional[int] = Field(default=None, ge=1024, le=65535)
    username: Optional[str] = Field(default=None, min_length=1, max_length=64)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    is_enabled: Optional[bool] = None
    auto_start: Optional[bool] = None
    video_encoder: Optional[VideoEncoder] = None
    audio_encoder: Optional[str] = Field(default=None, pattern=r"^(opus|aac)$")
    max_bitrate: Optional[int] = Field(default=None, ge=1000, le=200000)
    max_fps: Optional[int] = Field(default=None, ge=15, le=240)
    resolution: Optional[str] = Field(default=None, pattern=r"^\d+x\d+$")
    gpu_device_id: Optional[str] = None
    enable_hevc: Optional[bool] = None
    enable_av1: Optional[bool] = None


class SunshineConfigResponse(BaseModel):
    id: int
    host: str
    port: int
    web_port: int
    username: str
    is_enabled: bool
    auto_start: bool
    video_encoder: VideoEncoder
    audio_encoder: str
    max_bitrate: int
    max_fps: int
    resolution: str
    gpu_device_id: Optional[str]
    enable_hevc: bool
    enable_av1: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Sunshine Status
# =============================================================================

class SunshineStatus(BaseModel):
    is_running: bool
    process_id: Optional[int] = None
    version: Optional[str] = None
    uptime_seconds: Optional[float] = None
    config: Optional[SunshineConfigResponse] = None
    active_sessions: int = 0
    max_sessions: int = 0


# =============================================================================
# Streaming Sessions
# =============================================================================

class StreamingSessionBase(BaseModel):
    session_type: SessionType
    sunshine_session_id: Optional[str] = None
    client_ip: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None


class StreamingSessionCreate(StreamingSessionBase):
    device_id: Optional[UUID] = None


class StreamingSessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    ended_at: Optional[datetime] = None
    error_message: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None


class StreamingSessionResponse(StreamingSessionBase):
    id: UUID
    user_id: UUID
    device_id: Optional[UUID] = None
    status: SessionStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# Discovered Apps
# =============================================================================

class DiscoveredAppBase(BaseModel):
    name: str
    executable_path: Optional[str] = None
    working_directory: Optional[str] = None
    launch_args: Optional[str] = None
    app_type: Optional[str] = None
    publisher: Optional[str] = None
    version: Optional[str] = None


class DiscoveredAppCreate(DiscoveredAppBase):
    sunshine_app_id: Optional[str] = None
    is_sunshine_app: bool = False
    sunshine_image_url: Optional[str] = None


class DiscoveredAppUpdate(BaseModel):
    name: Optional[str] = None
    executable_path: Optional[str] = None
    working_directory: Optional[str] = None
    launch_args: Optional[str] = None
    app_type: Optional[str] = None
    publisher: Optional[str] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None


class DiscoveredAppResponse(DiscoveredAppBase):
    id: UUID
    sunshine_app_id: Optional[str] = None
    is_sunshine_app: bool
    sunshine_image_url: Optional[str] = None
    detected_at: datetime
    last_seen_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# =============================================================================
# Stream URL / Connection
# =============================================================================

class StreamUrlRequest(BaseModel):
    session_type: SessionType = SessionType.DESKTOP
    app_id: Optional[UUID] = None
    quality_profile: Optional[str] = Field(default="balanced", pattern=r"^(ultra|high|balanced|economy|mobile)$")
    device_type: Optional[str] = Field(default=None, pattern=r"^(android|ios|tvos|windows|mac|linux)$")


class StreamUrlResponse(BaseModel):
    moonlight_url: str
    sunshine_url: str
    qr_code_base64: Optional[str] = None
    connection_info: Dict[str, Any]


# =============================================================================
# App Launch
# =============================================================================

class AppLaunchRequest(BaseModel):
    app_id: UUID
    session_type: SessionType = SessionType.APP
    quality_profile: Optional[str] = Field(default="balanced", pattern=r"^(ultra|high|balanced|economy|mobile)$")


class AppLaunchResponse(BaseModel):
    session_id: UUID
    stream_url: str
    message: str


# =============================================================================
# GPU Info
# =============================================================================

class GPUInfo(BaseModel):
    name: str
    memory_total_mb: int
    memory_used_mb: int
    utilization_percent: float
    temperature_c: Optional[float] = None
    encoder_support: List[str] = []


class SystemComputingInfo(BaseModel):
    cpu_percent: float
    cpu_count: int
    memory_percent: float
    memory_total_gb: float
    memory_used_gb: float
    memory_available_gb: float
    disk_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_free_gb: float
    gpus: List[GPUInfo] = []
    recommended_encoder: VideoEncoder = VideoEncoder.NVENC
    sunshine_status: Optional[SunshineStatus] = None


# =============================================================================
# Quality Profiles
# =============================================================================

class QualityProfile(BaseModel):
    name: str
    label: str
    resolution: str
    fps: int
    bitrate_kbps: int
    codec: str
    description: str


QUALITY_PROFILES: Dict[str, QualityProfile] = {
    "ultra": QualityProfile(
        name="ultra",
        label="Ultra (4K 60fps)",
        resolution="3840x2160",
        fps=60,
        bitrate_kbps=80000,
        codec="hevc",
        description="LAN Gigabit, melhor qualidade"
    ),
    "high": QualityProfile(
        name="high",
        label="Alto (1440p 120fps)",
        resolution="2560x1440",
        fps=120,
        bitrate_kbps=50000,
        codec="hevc",
        description="LAN / WiFi 6, alta taxa de atualização"
    ),
    "balanced": QualityProfile(
        name="balanced",
        label="Equilibrado (1080p 60fps)",
        resolution="1920x1080",
        fps=60,
        bitrate_kbps=25000,
        codec="h264",
        description="WiFi 5, uso geral"
    ),
    "economy": QualityProfile(
        name="economy",
        label="Econômico (720p 30fps)",
        resolution="1280x720",
        fps=30,
        bitrate_kbps=10000,
        codec="h264",
        description="WiFi 4 / Internet, banda limitada"
    ),
    "mobile": QualityProfile(
        name="mobile",
        label="Mobile (720p 60fps)",
        resolution="1280x720",
        fps=60,
        bitrate_kbps=15000,
        codec="hevc",
        description="4G/5G, dispositivos móveis"
    ),
}


def get_quality_profile(name: str) -> QualityProfile:
    """Get quality profile by name, fallback to balanced."""
    return QUALITY_PROFILES.get(name, QUALITY_PROFILES["balanced"])