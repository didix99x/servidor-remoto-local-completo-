"""
Share schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.share import ShareType, PermissionLevel


class ShareBase(BaseModel):
    """Base share fields."""
    name: str = Field(..., min_length=1, max_length=100)
    path: str = Field(..., min_length=1, max_length=500)
    share_type: ShareType = ShareType.FOLDER


class ShareCreate(ShareBase):
    """Share creation request."""
    pass


class ShareUpdate(BaseModel):
    """Share update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    path: Optional[str] = Field(None, min_length=1, max_length=500)


class ShareResponse(ShareBase):
    """Share response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime


class ShareContentItem(BaseModel):
    """File/folder item in share listing."""
    name: str
    path: str  # relative path within share
    is_dir: bool
    size: Optional[int] = None
    modified_at: datetime
    mime_type: Optional[str] = None


class ShareContentResponse(BaseModel):
    """Share directory listing response."""
    items: List[ShareContentItem]
    current_path: str
    parent_path: Optional[str] = None


class SharePermissionCreate(BaseModel):
    """Permission grant request."""
    device_id: int
    permission: PermissionLevel = PermissionLevel.READ


class SharePermissionUpdate(BaseModel):
    """Permission update request."""
    permission: PermissionLevel


class SharePermissionResponse(BaseModel):
    """Permission response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    share_id: int
    device_id: int
    permission: PermissionLevel
    granted_by: Optional[int] = None
    granted_at: datetime


class UploadResponse(BaseModel):
    """File upload response."""
    filename: str
    path: str
    size: int
    mime_type: Optional[str] = None


class BulkOperationRequest(BaseModel):
    """Bulk file operation request."""
    paths: List[str]
    operation: str = Field(..., pattern="^(delete|move|copy)$")
    destination: Optional[str] = None  # for move/copy