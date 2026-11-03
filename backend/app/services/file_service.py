"""
File service for share management and file operations.
"""
import os
import shutil
import mimetypes
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, BinaryIO
from uuid import uuid4

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.share import Share, SharePermission, ShareType, PermissionLevel
from app.models.device import Device
from app.schemas.share import (
    ShareCreate, ShareUpdate, ShareContentItem, ShareContentResponse,
    SharePermissionCreate, UploadResponse
)
from app.services.websocket_manager import get_websocket_manager


class FileService:
    """Service for file sharing operations."""

    def __init__(self):
        self.settings = get_settings()
        self.shares_root = self.settings.shares_root_path
        self.shares_root.mkdir(parents=True, exist_ok=True)

    def _get_share_path(self, share: Share) -> Path:
        """Get absolute path for a share."""
        # Path is relative to shares_root
        return (self.shares_root / share.path).resolve()

    def _validate_path_within_share(self, share: Share, relative_path: str) -> Path:
        """Validate and resolve a path within a share."""
        share_path = self._get_share_path(share)
        target_path = (share_path / relative_path).resolve()

        # Ensure target is within share path
        try:
            target_path.relative_to(share_path)
        except ValueError:
            raise ValueError("Path traversal attempt detected")

        return target_path

    def _get_mime_type(self, path: Path) -> str:
        """Get MIME type for a file."""
        mime_type, _ = mimetypes.guess_type(str(path))
        return mime_type or "application/octet-stream"

    async def create_share(
        self,
        db: AsyncSession,
        owner_id: int,
        share_data: ShareCreate,
    ) -> Share:
        """Create a new share."""
        # Validate path exists
        share_path = self.shares_root / share_data.path
        if not share_path.exists():
            if share_data.share_type == ShareType.FOLDER:
                share_path.mkdir(parents=True, exist_ok=True)
            else:
                raise ValueError(f"Path does not exist: {share_data.path}")

        share = Share(
            name=share_data.name,
            path=share_data.path,
            share_type=share_data.share_type,
            owner_id=owner_id,
        )
        db.add(share)
        await db.flush()
        await db.refresh(share)
        return share

    async def get_shares(
        self,
        db: AsyncSession,
        owner_id: Optional[int] = None,
    ) -> List[Share]:
        """Get all shares, optionally filtered by owner."""
        query = select(Share).options(selectinload(Share.permissions).selectinload(SharePermission.device))
        if owner_id:
            query = query.where(Share.owner_id == owner_id)
        result = await db.execute(query.order_by(Share.created_at.desc()))
        return result.scalars().all()

    async def get_share(self, db: AsyncSession, share_id: int) -> Optional[Share]:
        """Get a share by ID with permissions."""
        result = await db.execute(
            select(Share)
            .options(selectinload(Share.permissions).selectinload(SharePermission.device))
            .where(Share.id == share_id)
        )
        return result.scalar_one_or_none()

    async def update_share(
        self,
        db: AsyncSession,
        share_id: int,
        share_data: ShareUpdate,
    ) -> Optional[Share]:
        """Update a share."""
        share = await self.get_share(db, share_id)
        if not share:
            return None

        if share_data.name is not None:
            share.name = share_data.name
        if share_data.path is not None:
            # Validate new path
            new_path = self.shares_root / share_data.path
            if not new_path.exists():
                if share.share_type == ShareType.FOLDER:
                    new_path.mkdir(parents=True, exist_ok=True)
                else:
                    raise ValueError(f"Path does not exist: {share_data.path}")
            share.path = share_data.path

        await db.flush()
        await db.refresh(share)
        return share

    async def delete_share(self, db: AsyncSession, share_id: int) -> bool:
        """Delete a share."""
        share = await self.get_share(db, share_id)
        if not share:
            return False

        await db.delete(share)
        return True

    async def list_share_contents(
        self,
        db: AsyncSession,
        share_id: int,
        relative_path: str = "",
    ) -> ShareContentResponse:
        """List contents of a share directory."""
        share = await self.get_share(db, share_id)
        if not share:
            raise ValueError("Share not found")

        if share.share_type == ShareType.FILE:
            raise ValueError("Cannot list contents of a file share")

        target_path = self._validate_path_within_share(share, relative_path)

        if not target_path.exists():
            raise ValueError("Path not found")

        if not target_path.is_dir():
            raise ValueError("Path is not a directory")

        items = []
        for entry in sorted(target_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            stat = entry.stat()
            rel_path = entry.relative_to(self._get_share_path(share))
            items.append(ShareContentItem(
                name=entry.name,
                path=str(rel_path),
                is_dir=entry.is_dir(),
                size=stat.st_size if entry.is_file() else None,
                modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                mime_type=self._get_mime_type(entry) if entry.is_file() else None,
            ))

        parent_path = str(Path(relative_path).parent) if relative_path else None
        if parent_path == ".":
            parent_path = None

        return ShareContentResponse(
            items=items,
            current_path=relative_path,
            parent_path=parent_path,
        )

    async def upload_file(
        self,
        db: AsyncSession,
        share_id: int,
        relative_path: str,
        file_content: bytes,
        filename: str,
    ) -> UploadResponse:
        """Upload a file to a share."""
        share = await self.get_share(db, share_id)
        if not share:
            raise ValueError("Share not found")

        if share.share_type == ShareType.FILE:
            raise ValueError("Cannot upload to a file share")

        # Check permissions (simplified - in real app check device permissions)
        target_dir = self._validate_path_within_share(share, relative_path)
        if not target_dir.exists() or not target_dir.is_dir():
            raise ValueError("Target directory not found")

        # Sanitize filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ").strip()
        if not safe_filename:
            safe_filename = f"upload_{uuid4().hex[:8]}"

        target_file = target_dir / safe_filename

        # Handle duplicates
        counter = 1
        original_name = target_file.stem
        original_suffix = target_file.suffix
        while target_file.exists():
            target_file = target_dir / f"{original_name}_{counter}{original_suffix}"
            counter += 1

        # Write file
        target_file.write_bytes(file_content)

        stat = target_file.stat()
        rel_path = target_file.relative_to(self._get_share_path(share))

        return UploadResponse(
            filename=target_file.name,
            path=str(rel_path),
            size=stat.st_size,
            mime_type=self._get_mime_type(target_file),
        )

    async def download_file(
        self,
        db: AsyncSession,
        share_id: int,
        relative_path: str,
    ) -> Optional[Path]:
        """Get file path for download."""
        share = await self.get_share(db, share_id)
        if not share:
            return None

        if share.share_type == ShareType.FILE:
            # For file shares, the path is the file itself
            share_path = self._get_share_path(share)
            if share_path.is_file():
                return share_path
            return None

        target_path = self._validate_path_within_share(share, relative_path)
        if target_path.exists() and target_path.is_file():
            return target_path
        return None

    async def delete_file(
        self,
        db: AsyncSession,
        share_id: int,
        relative_path: str,
    ) -> bool:
        """Delete a file or folder."""
        share = await self.get_share(db, share_id)
        if not share:
            return False

        target_path = self._validate_path_within_share(share, relative_path)
        if not target_path.exists():
            return False

        if target_path.is_dir():
            shutil.rmtree(target_path)
        else:
            target_path.unlink()
        return True

    async def rename_file(
        self,
        db: AsyncSession,
        share_id: int,
        relative_path: str,
        new_name: str,
    ) -> bool:
        """Rename a file or folder."""
        share = await self.get_share(db, share_id)
        if not share:
            return False

        target_path = self._validate_path_within_share(share, relative_path)
        if not target_path.exists():
            return False

        # Sanitize new name
        safe_name = "".join(c for c in new_name if c.isalnum() or c in "._- ").strip()
        if not safe_name:
            return False

        new_path = target_path.parent / safe_name
        if new_path.exists():
            return False

        target_path.rename(new_path)
        return True

    async def move_file(
        self,
        db: AsyncSession,
        share_id: int,
        relative_path: str,
        destination: str,
    ) -> bool:
        """Move a file or folder."""
        share = await self.get_share(db, share_id)
        if not share:
            return False

        src_path = self._validate_path_within_share(share, relative_path)
        dst_path = self._validate_path_within_share(share, destination)

        if not src_path.exists():
            return False

        if dst_path.exists() and dst_path.is_dir():
            dst_path = dst_path / src_path.name

        shutil.move(str(src_path), str(dst_path))
        return True

    async def copy_file(
        self,
        db: AsyncSession,
        share_id: int,
        relative_path: str,
        destination: str,
    ) -> bool:
        """Copy a file or folder."""
        share = await self.get_share(db, share_id)
        if not share:
            return False

        src_path = self._validate_path_within_share(share, relative_path)
        dst_path = self._validate_path_within_share(share, destination)

        if not src_path.exists():
            return False

        if dst_path.exists() and dst_path.is_dir():
            dst_path = dst_path / src_path.name

        if src_path.is_dir():
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)
        return True

    async def grant_permission(
        self,
        db: AsyncSession,
        share_id: int,
        perm_data: SharePermissionCreate,
    ) -> SharePermission:
        """Grant permission to a device."""
        share = await self.get_share(db, share_id)
        if not share:
            raise ValueError("Share not found")

        # Check device exists
        result = await db.execute(select(Device).where(Device.id == perm_data.device_id))
        device = result.scalar_one_or_none()
        if not device:
            raise ValueError("Device not found")

        # Check if permission already exists
        result = await db.execute(
            select(SharePermission).where(
                SharePermission.share_id == share_id,
                SharePermission.device_id == perm_data.device_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.permission = perm_data.permission
            await db.flush()
            return existing

        permission = SharePermission(
            share_id=share_id,
            device_id=perm_data.device_id,
            permission=perm_data.permission,
        )
        db.add(permission)
        await db.flush()
        await db.refresh(permission)
        return permission

    async def revoke_permission(
        self,
        db: AsyncSession,
        share_id: int,
        device_id: int,
    ) -> bool:
        """Revoke permission from a device."""
        result = await db.execute(
            select(SharePermission).where(
                SharePermission.share_id == share_id,
                SharePermission.device_id == device_id,
            )
        )
        permission = result.scalar_one_or_none()
        if not permission:
            return False

        await db.delete(permission)
        return True

    async def check_permission(
        self,
        db: AsyncSession,
        share_id: int,
        device_mac: str,
        required: PermissionLevel = PermissionLevel.READ,
    ) -> bool:
        """Check if a device has permission on a share."""
        # Get device by MAC
        result = await db.execute(select(Device).where(Device.mac_address == device_mac))
        device = result.scalar_one_or_none()
        if not device:
            return False

        # Check permission
        result = await db.execute(
            select(SharePermission).where(
                SharePermission.share_id == share_id,
                SharePermission.device_id == device.id,
            )
        )
        permission = result.scalar_one_or_none()
        if not permission:
            return False

        # Check permission level hierarchy
        levels = [PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.DELETE]
        try:
            return levels.index(permission.permission) >= levels.index(required)
        except ValueError:
            return False


# Singleton instance
_file_service: Optional[FileService] = None


def get_file_service() -> FileService:
    """Get or create the file service singleton."""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service