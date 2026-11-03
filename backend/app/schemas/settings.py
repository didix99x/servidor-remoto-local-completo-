"""
Settings schemas.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SettingsResponse(BaseModel):
    """Settings response."""
    model_config = ConfigDict(from_attributes=True)

    scan_interval_minutes: int
    arp_scan_timeout: int
    max_upload_size_mb: int
    allowed_video_extensions: list[str]
    allowed_audio_extensions: list[str]
    thumbnail_cache_dir: str
    shares_root: str


class SettingsUpdate(BaseModel):
    """Settings update request."""
    scan_interval_minutes: Optional[int] = Field(None, ge=1, le=1440)
    arp_scan_timeout: Optional[int] = Field(None, ge=1, le=60)
    max_upload_size_mb: Optional[int] = Field(None, ge=1, le=10240)
    allowed_video_extensions: Optional[list[str]] = None
    allowed_audio_extensions: Optional[list[str]] = None


class SystemInfoResponse(BaseModel):
    """System information response."""
    version: str
    python_version: str
    platform: str
    cpu_count: int
    memory_total_gb: float
    disk_usage: Dict[str, Any]
    uptime_seconds: float