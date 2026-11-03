"""
Configuration management for Home Network Control Center.
Uses Pydantic Settings for environment variable parsing and validation.
"""
from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server bind address")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")

    # Security
    secret_key: str = Field(
        default="",
        description="Secret key for JWT signing (auto-generated if empty)",
    )
    access_token_expire_minutes: int = Field(
        default=720, description="Access token lifetime in minutes (12 hours default)"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Refresh token lifetime in days"
    )
    argon2_time_cost: int = Field(default=3, description="Argon2 time cost")
    argon2_memory_cost: int = Field(default=65536, description="Argon2 memory cost (KB)")
    argon2_parallelism: int = Field(default=4, description="Argon2 parallelism")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/hncc.db",
        description="Database connection URL",
    )

    # Network Scanning
    scan_interval_minutes: int = Field(
        default=5, description="Interval between network scans in minutes"
    )
    arp_scan_timeout: int = Field(default=3, description="ARP scan timeout in seconds")
    nmap_path: str = Field(default="nmap", description="Path to nmap executable")

    # File Sharing
    shares_root: str = Field(
        default="./shares", description="Root directory for shared folders"
    )
    max_upload_size_mb: int = Field(
        default=2048, description="Maximum upload size in MB"
    )
    allowed_video_extensions: List[str] = Field(
        default=["mp4", "mkv", "avi", "mov", "webm"],
        description="Allowed video file extensions",
    )
    allowed_audio_extensions: List[str] = Field(
        default=["mp3", "flac", "wav", "ogg", "m4a"],
        description="Allowed audio file extensions",
    )

    # Media
    ffmpeg_path: str = Field(default="ffmpeg", description="Path to ffmpeg executable")
    thumbnail_cache_dir: str = Field(
        default="./cache/thumbnails", description="Thumbnail cache directory"
    )

    # Security
    allowed_networks: List[str] = Field(
        default=["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12"],
        description="Allowed network CIDRs for CORS",
    )
    rate_limit_auth: str = Field(
        default="100/minute", description="Rate limit for auth endpoints"
    )
    rate_limit_api: str = Field(
        default="1000/minute", description="Rate limit for API endpoints"
    )

    @field_validator("secret_key", mode="before")
    @classmethod
    def generate_secret_key(cls, v: str) -> str:
        """Generate a secure secret key if not provided."""
        if not v:
            import secrets
            return secrets.token_urlsafe(32)
        return v

    @field_validator("shares_root", "thumbnail_cache_dir", mode="before")
    @classmethod
    def expand_path(cls, v: str) -> str:
        """Expand user home directory and resolve path."""
        return str(Path(v).expanduser().resolve())

    @property
    def shares_root_path(self) -> Path:
        """Get shares root as Path object."""
        return Path(self.shares_root)

    @property
    def thumbnail_cache_path(self) -> Path:
        """Get thumbnail cache dir as Path object."""
        return Path(self.thumbnail_cache_dir)

    @property
    def allowed_networks_cidr(self) -> List[str]:
        """Get allowed networks as CIDR strings."""
        return self.allowed_networks


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency injection for FastAPI."""
    return settings