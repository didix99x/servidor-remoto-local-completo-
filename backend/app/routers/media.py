"""
Media center router — library, streaming, thumbnails.
"""
import os
import mimetypes
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse, FileResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.services.file_service import get_file_service
from app.services.media_service import (
    scan_directory_for_media,
    get_video_info_ffprobe,
    generate_thumbnail_ffmpeg,
    get_thumbnail_path,
    categorize_media,
    StreamChunkResponse,
)
from app.services.auth_service import get_auth_service
from app.models.user import User, UserRole

router = APIRouter(prefix="/media", tags=["media"])
settings = get_settings()
security = HTTPBearer(auto_error=False)


async def get_current_user_media(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: get authenticated user from JWT token (header or query string)."""
    auth_svc = get_auth_service()

    # Try header first
    token_str = credentials.credentials if credentials else None

    # Fallback to query string
    if not token_str:
        token_str = token

    if not token_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = auth_svc.decode_token(token_str)
    if not payload or payload.type != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = await auth_svc.get_user_by_id(db, int(payload.sub))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


@router.get("/library")
async def get_media_library(
    current_user: User = Depends(get_current_user_media),
    db: AsyncSession = Depends(get_db),
):
    """Scan all shares for media files and return organized library."""
    svc = get_file_service()
    shares = await svc.get_shares(db)

    movies = []
    series = []
    music = []
    total_size = 0

    for share in shares:
        share_path = svc.shares_root / share.path
        if not share_path.exists():
            continue

        media = scan_directory_for_media(share_path)

        for video in media["videos"]:
            category = categorize_media(video["name"])
            entry = {
                **video,
                "share_id": share.id,
                "share_name": share.name,
                "id": f"{share.id}:{video['path']}",
                "thumbnail_url": f"/api/media/thumbnail?share_id={share.id}&path={video['path']}",
                "stream_url": f"/api/media/stream?share_id={share.id}&path={video['path']}",
            }
            if category == "series":
                series.append(entry)
            else:
                movies.append(entry)
            total_size += video.get("size", 0)

        for audio in media["audio"]:
            entry = {
                **audio,
                "share_id": share.id,
                "share_name": share.name,
                "id": f"{share.id}:{audio['path']}",
                "stream_url": f"/api/media/stream?share_id={share.id}&path={audio['path']}",
            }
            music.append(entry)
            total_size += audio.get("size", 0)

    return {
        "movies": sorted(movies, key=lambda x: x["name"].lower()),
        "series": sorted(series, key=lambda x: x["name"].lower()),
        "music": sorted(music, key=lambda x: x["name"].lower()),
        "total_count": len(movies) + len(series) + len(music),
        "total_size": total_size,
    }


@router.get("/stream")
async def stream_media(
    share_id: int,
    path: str,
    request: Request,
    current_user: User = Depends(get_current_user_media),
    db: AsyncSession = Depends(get_db),
):
    """Stream a media file with range request support."""
    svc = get_file_service()
    file_path = await svc.download_file(db, share_id, path)
    if not file_path or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found")

    file_size = file_path.stat().st_size
    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

    range_header = request.headers.get("Range")
    start, end, chunk_size = StreamChunkResponse.get_range_header(file_size, range_header)

    def iterfile(start: int, chunk_size: int):
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = chunk_size
            while remaining > 0:
                read_size = min(65536, remaining)
                data = f.read(read_size)
                if not data:
                    break
                remaining -= len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(chunk_size),
        "Content-Type": mime_type,
    }

    status_code = 206 if range_header else 200
    return StreamingResponse(
        iterfile(start, chunk_size),
        status_code=status_code,
        headers=headers,
        media_type=mime_type,
    )


@router.get("/thumbnail")
async def get_thumbnail(
    share_id: int,
    path: str,
    width: int = 320,
    height: int = 180,
    current_user: User = Depends(get_current_user_media),
    db: AsyncSession = Depends(get_db),
):
    """Get or generate thumbnail for a video file."""
    svc = get_file_service()
    file_path = await svc.download_file(db, share_id, path)
    if not file_path or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    cache_dir = Path(settings.thumbnail_cache_dir)
    thumbnail_path = get_thumbnail_path(file_path, cache_dir)

    if not thumbnail_path.exists():
        success = generate_thumbnail_ffmpeg(file_path, thumbnail_path, width=width, height=height)
        if not success:
            # Return placeholder SVG thumbnail
            svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#1a1a2e"/>
  <polygon points="{width//2-20},{height//2-20} {width//2+20},{height//2} {width//2-20},{height//2+20}" fill="#00d4ff" opacity="0.8"/>
  <text x="{width//2}" y="{height-15}" text-anchor="middle" fill="#666" font-size="11" font-family="Arial">{file_path.name[:25]}</text>
</svg>'''
            return Response(content=svg, media_type="image/svg+xml")

    return FileResponse(str(thumbnail_path), media_type="image/jpeg")


@router.get("/info")
async def get_media_info(
    share_id: int,
    path: str,
    current_user: User = Depends(get_current_user_media),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed media file information."""
    svc = get_file_service()
    file_path = await svc.download_file(db, share_id, path)
    if not file_path or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    info = get_video_info_ffprobe(file_path) or {}
    stat = file_path.stat()

    return {
        "name": file_path.name,
        "size": stat.st_size,
        "mime_type": mimetypes.guess_type(str(file_path))[0],
        **info,
    }


@router.get("/subtitles")
async def get_subtitles(
    share_id: int,
    path: str,
    current_user: User = Depends(get_current_user_media),
    db: AsyncSession = Depends(get_db),
):
    """Find subtitle files for a video."""
    svc = get_file_service()
    file_path = await svc.download_file(db, share_id, path)
    if not file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    subtitle_extensions = {".srt", ".vtt", ".ass", ".ssa", ".sub"}
    subtitles = []

    parent = file_path.parent
    stem = file_path.stem

    for ext in subtitle_extensions:
        for sub_file in parent.glob(f"{stem}*{ext}"):
            subtitles.append({
                "name": sub_file.name,
                "path": str(sub_file),
                "language": None,
            })

    return {"subtitles": subtitles}
