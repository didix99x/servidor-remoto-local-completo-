"""
Media service for video/audio library scanning and streaming.
"""
import os
import asyncio
import logging
import mimetypes
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple

from app.config import get_settings

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".flv", ".wmv", ".ts", ".m2ts"}
AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".opus", ".wma"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


def _is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def _is_audio(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_EXTENSIONS


def scan_directory_for_media(directory: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Scan a directory recursively for media files."""
    result: Dict[str, List[Dict[str, Any]]] = {"videos": [], "audio": [], "images": []}

    if not directory.exists() or not directory.is_dir():
        return result

    for root, dirs, files in os.walk(directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for filename in sorted(files):
            if filename.startswith("."):
                continue
            filepath = Path(root) / filename
            suffix = filepath.suffix.lower()
            rel_path = str(filepath.relative_to(directory))
            stat = filepath.stat()

            entry = {
                "name": filename,
                "path": rel_path,
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "mime_type": mimetypes.guess_type(filename)[0] or "application/octet-stream",
            }

            if suffix in VIDEO_EXTENSIONS:
                result["videos"].append(entry)
            elif suffix in AUDIO_EXTENSIONS:
                result["audio"].append(entry)
            elif suffix in IMAGE_EXTENSIONS:
                result["images"].append(entry)

    return result


def get_video_info_ffprobe(filepath: Path) -> Optional[Dict[str, Any]]:
    """Get video metadata using ffprobe."""
    settings = get_settings()
    ffprobe = settings.ffmpeg_path.replace("ffmpeg", "ffprobe")

    try:
        cmd = [
            ffprobe, "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", str(filepath)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        info = {}

        # Duration
        fmt = data.get("format", {})
        duration = fmt.get("duration")
        if duration:
            info["duration"] = float(duration)

        # Video stream
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                info["width"] = stream.get("width")
                info["height"] = stream.get("height")
                info["codec"] = stream.get("codec_name")
                break

        return info
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return None


def generate_thumbnail_ffmpeg(
    video_path: Path,
    output_path: Path,
    timestamp: float = 5.0,
    width: int = 320,
    height: int = 180,
) -> bool:
    """Generate thumbnail from video using ffmpeg."""
    settings = get_settings()

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            settings.ffmpeg_path,
            "-ss", str(timestamp),
            "-i", str(video_path),
            "-vframes", "1",
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease",
            "-y",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_thumbnail_path(video_path: Path, cache_dir: Path) -> Path:
    """Get the expected thumbnail path for a video."""
    import hashlib
    path_hash = hashlib.md5(str(video_path).encode()).hexdigest()
    return cache_dir / f"{path_hash}.jpg"


def categorize_media(filename: str) -> str:
    """Guess if a video is a movie or TV series."""
    name = filename.lower()
    # Common TV patterns: S01E01, 1x01, Season 1, etc.
    import re
    tv_patterns = [
        r's\d+e\d+', r'\d+x\d+', r'season[\s._-]\d+',
        r'episode[\s._-]\d+', r'ep[\s._-]\d+',
    ]
    for pattern in tv_patterns:
        if re.search(pattern, name):
            return "series"
    return "movies"


class StreamChunkResponse:
    """Video streaming with range support."""

    @staticmethod
    def get_range_header(file_size: int, range_header: Optional[str]) -> Tuple[int, int, int]:
        """Parse range header and return start, end, chunk_size."""
        if not range_header:
            return 0, file_size - 1, file_size

        # Parse "bytes=start-end"
        try:
            range_spec = range_header.replace("bytes=", "")
            start_str, end_str = range_spec.split("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            end = min(end, file_size - 1)
            chunk_size = end - start + 1
            return start, end, chunk_size
        except (ValueError, AttributeError):
            return 0, file_size - 1, file_size
