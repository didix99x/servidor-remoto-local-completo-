"""
Media schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class MediaFileBase(BaseModel):
    """Base media file fields."""
    name: str
    path: str  # relative to share root
    share_id: int
    size: int
    mime_type: str
    modified_at: datetime


class MediaFileResponse(MediaFileBase):
    """Media file response."""
    model_config = ConfigDict(from_attributes=True)

    id: str  # composite: share_id:path
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None  # seconds
    width: Optional[int] = None
    height: Optional[int] = None
    metadata: Optional[dict] = None


class MediaLibraryResponse(BaseModel):
    """Media library response."""
    movies: List[MediaFileResponse]
    series: List[MediaFileResponse]
    music: List[MediaFileResponse]
    total_count: int
    total_size: int


class StreamRequest(BaseModel):
    """Stream request with range support."""
    share_id: int
    path: str
    range_header: Optional[str] = None


class ThumbnailRequest(BaseModel):
    """Thumbnail generation request."""
    share_id: int
    path: str
    timestamp: Optional[float] = None  # specific timestamp for video
    width: int = 320
    height: int = 180


class SubtitleFile(BaseModel):
    """Subtitle file info."""
    name: str
    path: str
    language: Optional[str] = None
    is_default: bool = False