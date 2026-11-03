"""
File sharing router.
"""
import os
from pathlib import Path
from typing import List, Optional

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File,
    Form, Request, BackgroundTasks, status
)
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.schemas.share import (
    ShareCreate, ShareUpdate, ShareResponse,
    ShareContentResponse, SharePermissionCreate, SharePermissionResponse,
    UploadResponse, BulkOperationRequest
)
from app.services.file_service import get_file_service
from app.services.audit_service import get_audit_service
from app.routers.auth import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/shares", response_model=List[ShareResponse])
async def list_shares(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all shares."""
    svc = get_file_service()
    shares = await svc.get_shares(db)
    return shares


@router.post("/shares", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
async def create_share(
    body: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new share."""
    svc = get_file_service()
    try:
        share = await svc.create_share(db, current_user.id, body)
        return share
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/shares/{share_id}", response_model=ShareResponse)
async def get_share(
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get share details."""
    svc = get_file_service()
    share = await svc.get_share(db, share_id)
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found")
    return share


@router.put("/shares/{share_id}", response_model=ShareResponse)
async def update_share(
    share_id: int,
    body: ShareUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a share."""
    svc = get_file_service()
    try:
        share = await svc.update_share(db, share_id, body)
        if not share:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found")
        return share
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/shares/{share_id}")
async def delete_share(
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a share."""
    svc = get_file_service()
    deleted = await svc.delete_share(db, share_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found")
    return {"message": "Share deleted"}


@router.get("/shares/{share_id}/contents", response_model=ShareContentResponse)
async def list_share_contents(
    share_id: int,
    path: str = "",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List contents of a share directory."""
    svc = get_file_service()
    try:
        return await svc.list_share_contents(db, share_id, path)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/shares/{share_id}/upload", response_model=UploadResponse)
async def upload_file(
    share_id: int,
    file: UploadFile = File(...),
    path: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file to a share."""
    settings = get_settings()
    svc = get_file_service()
    audit_svc = get_audit_service()

    # Check file size
    content = await file.read()
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max {settings.max_upload_size_mb}MB",
        )

    try:
        result = await svc.upload_file(db, share_id, path, content, file.filename or "upload")
        await audit_svc.log(
            db, "file_upload", f"/files/shares/{share_id}",
            user_id=current_user.id,
            details=f"Uploaded '{result.filename}' ({result.size} bytes)",
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/shares/{share_id}/download")
async def download_file(
    share_id: int,
    path: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a file from a share."""
    svc = get_file_service()
    audit_svc = get_audit_service()

    file_path = await svc.download_file(db, share_id, path)
    if not file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    await audit_svc.log(
        db, "file_download", f"/files/shares/{share_id}",
        user_id=current_user.id,
        details=f"Downloaded '{path}'",
    )

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )


@router.delete("/shares/{share_id}/delete")
async def delete_file(
    share_id: int,
    path: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a file or folder from a share."""
    svc = get_file_service()
    deleted = await svc.delete_file(db, share_id, path)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return {"message": "Deleted successfully"}


@router.post("/shares/{share_id}/rename")
async def rename_file(
    share_id: int,
    path: str,
    new_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rename a file or folder."""
    svc = get_file_service()
    ok = await svc.rename_file(db, share_id, path, new_name)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rename failed")
    return {"message": "Renamed successfully"}


@router.post("/shares/{share_id}/permissions", response_model=SharePermissionResponse)
async def grant_permission(
    share_id: int,
    body: SharePermissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Grant permission to a device."""
    svc = get_file_service()
    try:
        perm = await svc.grant_permission(db, share_id, body)
        return perm
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/shares/{share_id}/permissions/{device_id}")
async def revoke_permission(
    share_id: int,
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke permission from a device."""
    svc = get_file_service()
    ok = await svc.revoke_permission(db, share_id, device_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    return {"message": "Permission revoked"}


@router.get("/disk-usage")
async def get_disk_usage(
    current_user: User = Depends(get_current_user),
):
    """Get disk usage statistics."""
    import shutil
    settings = get_settings()
    shares_path = Path(settings.shares_root)

    try:
        total, used, free = shutil.disk_usage(shares_path if shares_path.exists() else Path("."))
        shares_size = sum(f.stat().st_size for f in shares_path.rglob("*") if f.is_file()) if shares_path.exists() else 0
    except Exception:
        total, used, free, shares_size = 0, 0, 0, 0

    return {
        "disk_total_gb": round(total / (1024 ** 3), 2),
        "disk_used_gb": round(used / (1024 ** 3), 2),
        "disk_free_gb": round(free / (1024 ** 3), 2),
        "shares_size_mb": round(shares_size / (1024 ** 2), 2),
    }
