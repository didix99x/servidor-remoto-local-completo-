"""
Computing service for centralized computing / game streaming.
Manages Sunshine integration, streaming sessions, and app discovery.
"""
import asyncio
import json
import logging
import os
import platform
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import qrcode
import requests
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.models.computing import (
    DiscoveredApp,
    SessionStatus,
    SessionType,
    StreamingSession,
    SunshineConfig,
    VideoEncoder,
)
from app.models.device import Device
from app.models.user import User
from app.services.websocket_manager import get_websocket_manager

logger = logging.getLogger(__name__)


class ComputingService:
    """Service for managing Sunshine game streaming host and sessions."""

    def __init__(self):
        self.settings = get_settings()
        self._sunshine_process: Optional[subprocess.Popen] = None
        self._sunshine_start_time: Optional[float] = None
        self._sunshine_exe: Optional[Path] = None
        self._config_cache: Optional[SunshineConfig] = None
        self._apps_cache: List[Dict[str, Any]] = []
        self._apps_cache_time: float = 0
        self._apps_cache_ttl: int = 60  # seconds
        self._status_task: Optional[asyncio.Task] = None

        # Sunshine default paths on Windows
        self._sunshine_paths = [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Sunshine" / "sunshine.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Sunshine" / "sunshine.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Sunshine" / "sunshine.exe",
            Path.home() / "Sunshine" / "sunshine.exe",
        ]

        # Sunshine config path
        self._sunshine_config_path = Path(os.environ.get("APPDATA", "")) / "Sunshine" / "config.json"

    # -------------------------------------------------------------------------
    # Sunshine Process Management
    # -------------------------------------------------------------------------

    def _find_sunshine_exe(self) -> Optional[Path]:
        """Find Sunshine executable."""
        if self._sunshine_exe and self._sunshine_exe.exists():
            return self._sunshine_exe

        for path in self._sunshine_paths:
            if path.exists():
                self._sunshine_exe = path
                logger.info(f"Found Sunshine at: {path}")
                return path

        # Try to find via where/which
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["where", "sunshine"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            else:
                result = subprocess.run(
                    ["which", "sunshine"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            if result.returncode == 0 and result.stdout.strip():
                path = Path(result.stdout.strip().split("\n")[0])
                if path.exists():
                    self._sunshine_exe = path
                    logger.info(f"Found Sunshine via PATH: {path}")
                    return path
        except Exception as e:
            logger.debug(f"Could not find Sunshine via PATH: {e}")

        logger.warning("Sunshine executable not found")
        return None

    async def get_sunshine_status(self) -> Dict[str, Any]:
        """Get current Sunshine status."""
        is_running = self._sunshine_process is not None and self._sunshine_process.poll() is None

        status = {
            "is_running": is_running,
            "process_id": self._sunshine_process.pid if is_running else None,
            "version": None,
            "uptime_seconds": None,
            "active_sessions": 0,
            "max_sessions": 0,
        }

        if is_running and self._sunshine_start_time:
            status["uptime_seconds"] = time.time() - self._sunshine_start_time

        # Try to get version and session info from Sunshine API
        if is_running:
            try:
                api_info = await self._call_sunshine_api("GET", "/api/status")
                if api_info:
                    status["version"] = api_info.get("version")
                    status["active_sessions"] = len(api_info.get("sessions", []))
                    status["max_sessions"] = api_info.get("max_sessions", 0)
            except Exception as e:
                logger.debug(f"Could not get Sunshine API status: {e}")

        return status

    async def start_sunshine(self) -> bool:
        """Start Sunshine process."""
        if self._sunshine_process and self._sunshine_process.poll() is None:
            logger.info("Sunshine already running")
            return True

        exe = self._find_sunshine_exe()
        if not exe:
            logger.error("Sunshine executable not found")
            return False

        try:
            # Ensure config exists
            await self._ensure_sunshine_config()

            # Start Sunshine
            # Sunshine runs as a background service, we start it detached
            if platform.system() == "Windows":
                self._sunshine_process = subprocess.Popen(
                    [str(exe)],
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                self._sunshine_process = subprocess.Popen(
                    [str(exe)],
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            self._sunshine_start_time = time.time()

            # Wait a bit for startup
            await asyncio.sleep(3)

            # Verify it's running
            if self._sunshine_process.poll() is None:
                logger.info(f"Sunshine started (PID: {self._sunshine_process.pid})")
                await self._broadcast_sunshine_status()
                return True
            else:
                logger.error("Sunshine process exited immediately")
                return False

        except Exception as e:
            logger.error(f"Failed to start Sunshine: {e}")
            return False

    async def stop_sunshine(self) -> bool:
        """Stop Sunshine process."""
        if not self._sunshine_process or self._sunshine_process.poll() is not None:
            logger.info("Sunshine not running")
            return True

        try:
            if platform.system() == "Windows":
                # On Windows, use taskkill to properly terminate the process group
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self._sunshine_process.pid)],
                    capture_output=True,
                )
            else:
                self._sunshine_process.terminate()
                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(self._sunshine_process.wait),
                        timeout=10,
                    )
                except asyncio.TimeoutError:
                    self._sunshine_process.kill()
                    await asyncio.to_thread(self._sunshine_process.wait)

            self._sunshine_process = None
            self._sunshine_start_time = None
            logger.info("Sunshine stopped")
            await self._broadcast_sunshine_status()
            return True

        except Exception as e:
            logger.error(f"Failed to stop Sunshine: {e}")
            return False

    async def restart_sunshine(self) -> bool:
        """Restart Sunshine process."""
        await self.stop_sunshine()
        await asyncio.sleep(2)
        return await self.start_sunshine()

    # -------------------------------------------------------------------------
    # Configuration Management
    # -------------------------------------------------------------------------

    async def _ensure_sunshine_config(self) -> None:
        """Ensure Sunshine config file exists with our settings."""
        config = await self.get_config_db()
        if not config:
            return

        self._sunshine_config_path.parent.mkdir(parents=True, exist_ok=True)

        # Read existing config or create default
        sunshine_config = {}
        if self._sunshine_config_path.exists():
            try:
                with open(self._sunshine_config_path, "r") as f:
                    sunshine_config = json.load(f)
            except Exception:
                pass

        # Update with our settings
        sunshine_config.update({
            "host": config.host,
            "port": config.port,
            "web_port": config.web_port,
            "username": config.username,
            "password": config.password_hash,  # Sunshine stores hash
            "video": {
                "encoder": config.video_encoder.value,
                "bitrate": config.max_bitrate * 1000,  # Convert kbps to bps
                "fps": config.max_fps,
                "width": int(config.resolution.split("x")[0]),
                "height": int(config.resolution.split("x")[1]),
                "hevc": bool(config.enable_hevc),
                "av1": bool(config.enable_av1),
            },
            "audio": {
                "encoder": config.audio_encoder,
            },
        })

        if config.gpu_device_id:
            sunshine_config["video"]["gpu_device_id"] = config.gpu_device_id

        # Write config
        try:
            with open(self._sunshine_config_path, "w") as f:
                json.dump(sunshine_config, f, indent=2)
            logger.info(f"Sunshine config written to {self._sunshine_config_path}")
        except Exception as e:
            logger.error(f"Failed to write Sunshine config: {e}")

    async def get_config_db(self) -> Optional[SunshineConfig]:
        """Get Sunshine configuration from database."""
        async with get_session() as db:
            result = await db.execute(select(SunshineConfig).where(SunshineConfig.id == 1))
            return result.scalar_one_or_none()

    async def get_config(self) -> Optional[SunshineConfig]:
        """Get Sunshine configuration (cached)."""
        if self._config_cache is None:
            self._config_cache = await self.get_config_db()
        return self._config_cache

    async def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update Sunshine configuration."""
        async with get_session() as db:
            config = await db.get(SunshineConfig, 1)
            if not config:
                # Create default config
                from app.services.auth_service import get_auth_service
                auth = get_auth_service()
                config = SunshineConfig(
                    id=1,
                    password_hash=auth.hash_password("sunshine123"),  # Default, should be changed
                )
                db.add(config)

            # Update fields
            for key, value in updates.items():
                if hasattr(config, key) and key != "id":
                    if key == "password":
                        from app.services.auth_service import get_auth_service
                        auth = get_auth_service()
                        setattr(config, "password_hash", auth.hash_password(value))
                    elif key == "is_enabled" or key == "auto_start":
                        setattr(config, key, 1 if value else 0)
                    else:
                        setattr(config, key, value)

            config.updated_at = datetime.now(timezone.utc)
            await db.flush()
            self._config_cache = config

        # Rewrite Sunshine config file
        await self._ensure_sunshine_config()

        # Restart if running
        if self._sunshine_process and self._sunshine_process.poll() is None:
            await self.restart_sunshine()

        return True

    # -------------------------------------------------------------------------
    # Sunshine API Communication
    # -------------------------------------------------------------------------

    async def _call_sunshine_api(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
    ) -> Optional[Dict[str, Any]]:
        """Call Sunshine local REST API."""
        config = await self.get_config_db()
        if not config:
            return None

        url = f"http://localhost:{config.web_port}{endpoint}"

        try:
            # Sunshine uses basic auth
            auth = (config.username, "sunshine123")  # We'd need to store actual password
            # For now, try without auth (some versions allow local unauthenticated)

            response = requests.request(
                method,
                url,
                json=data,
                timeout=5,
                auth=auth if config.username else None,
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.debug("Sunshine API requires authentication")
                return None
            else:
                logger.warning(f"Sunshine API error: {response.status_code}")
                return None

        except requests.exceptions.ConnectionError:
            logger.debug("Sunshine API not reachable")
            return None
        except Exception as e:
            logger.error(f"Sunshine API call failed: {e}")
            return None

    # -------------------------------------------------------------------------
    # App Discovery
    # -------------------------------------------------------------------------

    async def discover_apps(self, force: bool = False) -> List[Dict[str, Any]]:
        """Discover applications/games from Sunshine and system."""
        # Check cache
        if not force and self._apps_cache and (time.time() - self._apps_cache_time) < self._apps_cache_ttl:
            return self._apps_cache

        apps = []

        # 1. Try to get from Sunshine API
        try:
            sunshine_apps = await self._call_sunshine_api("GET", "/api/apps")
            if sunshine_apps:
                for app in sunshine_apps.get("apps", []):
                    apps.append({
                        "sunshine_app_id": app.get("id"),
                        "name": app.get("name", "Unknown"),
                        "executable_path": app.get("exe"),
                        "working_directory": app.get("cwd"),
                        "launch_args": app.get("args"),
                        "app_type": self._categorize_app(app.get("name", "")),
                        "is_sunshine_app": True,
                        "sunshine_image_url": app.get("image"),
                    })
        except Exception as e:
            logger.debug(f"Could not get apps from Sunshine: {e}")

        # 2. Fallback: Scan common locations
        if not apps:
            apps = await self._scan_system_apps()

        # 3. Update database
        await self._sync_apps_to_db(apps)

        # Update cache
        self._apps_cache = apps
        self._apps_cache_time = time.time()

        return apps

    def _categorize_app(self, name: str) -> str:
        """Categorize app by name."""
        name_lower = name.lower()

        # Games
        game_keywords = [
            "steam", "epic", "gog", "battle.net", "origin", "uplay", "ea app",
            "minecraft", "roblox", "valorant", "league of legends", "cs2", "csgo",
            "dota 2", "overwatch", "apex", "fortnite", "pubg", "warzone",
            "gta", "red dead", "witcher", "cyberpunk", "elden ring", "baldur's gate",
            "halo", "forza", "flight simulator", "starfield",
        ]
        for kw in game_keywords:
            if kw in name_lower:
                return "game"

        # Browsers
        browser_keywords = ["chrome", "firefox", "edge", "brave", "opera", "vivaldi"]
        for kw in browser_keywords:
            if kw in name_lower:
                return "browser"

        # System/Utilities
        util_keywords = ["explorer", "cmd", "powershell", "terminal", "control panel",
                         "task manager", "settings", "calculator", "notepad", "paint"]
        for kw in util_keywords:
            if kw in name_lower:
                return "utility"

        return "unknown"

    async def _scan_system_apps(self) -> List[Dict[str, Any]]:
        """Scan system for installed applications."""
        apps = []
        scan_paths = []

        if platform.system() == "Windows":
            # Windows common paths
            scan_paths = [
                Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")),
                Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")),
                Path(os.environ.get("LOCALAPPDATA", "")),
                Path(os.environ.get("APPDATA", "")),
            ]

            # Steam
            steam_path = Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Steam" / "steamapps" / "common"
            if steam_path.exists():
                scan_paths.append(steam_path)

            # Epic Games
            epic_path = Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Epic Games"
            if epic_path.exists():
                scan_paths.append(epic_path)

        for base_path in scan_paths:
            if not base_path.exists():
                continue

            try:
                for exe_file in base_path.rglob("*.exe"):
                    # Skip obvious non-apps
                    if any(skip in str(exe_file).lower() for skip in [
                        "uninstall", "setup", "install", "update", "crash", "dump",
                        "vc_redist", "vcredist", "directx", "dotnet", "runtime"
                    ]):
                        continue

                    # Get relative name
                    try:
                        rel_path = exe_file.relative_to(base_path)
                        name = rel_path.parts[0] if rel_path.parts else exe_file.stem
                    except Exception:
                        name = exe_file.stem

                    apps.append({
                        "name": name.replace("_", " ").replace("-", " ").title(),
                        "executable_path": str(exe_file),
                        "working_directory": str(exe_file.parent),
                        "app_type": self._categorize_app(name),
                        "is_sunshine_app": False,
                    })

                    # Limit to avoid too many
                    if len(apps) >= 200:
                        break

            except Exception as e:
                logger.debug(f"Error scanning {base_path}: {e}")

        return apps

    async def _sync_apps_to_db(self, apps: List[Dict[str, Any]]) -> None:
        """Sync discovered apps to database."""
        async with get_session() as db:
            for app_data in apps:
                # Check if exists
                sunshine_id = app_data.get("sunshine_app_id")
                if sunshine_id:
                    result = await db.execute(
                        select(DiscoveredApp).where(DiscoveredApp.sunshine_app_id == sunshine_id)
                    )
                else:
                    # Match by executable path
                    exe_path = app_data.get("executable_path")
                    if exe_path:
                        result = await db.execute(
                            select(DiscoveredApp).where(DiscoveredApp.executable_path == exe_path)
                        )
                    else:
                        result = None

                existing = result.scalar_one_or_none() if result else None

                if existing:
                    # Update
                    existing.name = app_data["name"]
                    existing.executable_path = app_data.get("executable_path")
                    existing.working_directory = app_data.get("working_directory")
                    existing.launch_args = app_data.get("launch_args")
                    existing.app_type = app_data.get("app_type")
                    existing.is_sunshine_app = 1 if app_data.get("is_sunshine_app") else 0
                    existing.sunshine_image_url = app_data.get("sunshine_image_url")
                    existing.last_seen_at = datetime.now(timezone.utc)
                    existing.is_active = 1
                else:
                    # Create new
                    new_app = DiscoveredApp(
                        sunshine_app_id=sunshine_id,
                        name=app_data["name"],
                        executable_path=app_data.get("executable_path"),
                        working_directory=app_data.get("working_directory"),
                        launch_args=app_data.get("launch_args"),
                        app_type=app_data.get("app_type"),
                        is_sunshine_app=1 if app_data.get("is_sunshine_app") else 0,
                        sunshine_image_url=app_data.get("sunshine_image_url"),
                    )
                    db.add(new_app)

    # -------------------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------------------

    async def create_session(
        self,
        user_id: UUID,
        session_type: SessionType,
        device_id: Optional[UUID] = None,
        app_id: Optional[UUID] = None,
        quality_profile: str = "balanced",
    ) -> StreamingSession:
        """Create a new streaming session record."""
        from app.schemas.computing import get_quality_profile

        profile = get_quality_profile(quality_profile)

        async with get_session() as db:
            session = StreamingSession(
                id=uuid.uuid4().bytes,
                user_id=user_id.bytes if isinstance(user_id, UUID) else user_id,
                device_id=device_id.bytes if isinstance(device_id, UUID) else device_id,
                session_type=session_type,
                status=SessionStatus.CONNECTING,
                resolution=profile.resolution,
                fps=profile.fps,
                bitrate=profile.bitrate_kbps,
                codec=profile.codec,
            )
            db.add(session)
            await db.flush()
            await db.refresh(session)
            return session

    async def update_session_status(
        self,
        session_id: UUID,
        status: SessionStatus,
        sunshine_session_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[StreamingSession]:
        """Update streaming session status."""
        async with get_session() as db:
            session = await db.get(StreamingSession, session_id.bytes)
            if not session:
                return None

            session.status = status
            if sunshine_session_id:
                session.sunshine_session_id = sunshine_session_id
            if status == SessionStatus.ENDED or status == SessionStatus.ERROR:
                session.ended_at = datetime.now(timezone.utc)
            if error_message:
                session.error_message = error_message

            await db.flush()
            await db.refresh(session)

            # Broadcast via WebSocket
            ws = get_websocket_manager()
            await ws.broadcast({
                "type": "session_update",
                "data": {
                    "session_id": session_id.hex(),
                    "status": status.value,
                    "sunshine_session_id": sunshine_session_id,
                }
            })

            return session

    async def get_active_sessions(self) -> List[StreamingSession]:
        """Get all active streaming sessions."""
        async with get_session() as db:
            result = await db.execute(
                select(StreamingSession).where(
                    StreamingSession.status.in_([SessionStatus.CONNECTING, SessionStatus.ACTIVE])
                ).order_by(StreamingSession.started_at.desc())
            )
            return list(result.scalars().all())

    async def get_session_history(self, limit: int = 50) -> List[StreamingSession]:
        """Get streaming session history."""
        async with get_session() as db:
            result = await db.execute(
                select(StreamingSession)
                .order_by(StreamingSession.started_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def terminate_session(self, session_id: UUID) -> bool:
        """Terminate a streaming session."""
        # Update DB
        await self.update_session_status(session_id, SessionStatus.ENDED)

        # Try to terminate via Sunshine API
        session = await self.get_session_by_id(session_id)
        if session and session.sunshine_session_id:
            await self._call_sunshine_api("DELETE", f"/api/sessions/{session.sunshine_session_id}")

        return True

    async def get_session_by_id(self, session_id: UUID) -> Optional[StreamingSession]:
        """Get session by ID."""
        async with get_session() as db:
            return await db.get(StreamingSession, session_id.bytes)

    # -------------------------------------------------------------------------
    # Stream URL Generation
    # -------------------------------------------------------------------------

    async def generate_stream_url(
        self,
        session_type: SessionType = SessionType.DESKTOP,
        app_id: Optional[UUID] = None,
        quality_profile: str = "balanced",
        device_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate Moonlight/Sunshine connection URL."""
        from app.schemas.computing import get_quality_profile

        profile = get_quality_profile(quality_profile)
        config = await self.get_config_db()

        if not config:
            raise ValueError("Sunshine not configured")

        # Get local IP
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            local_ip = "127.0.0.1"

        # Build Moonlight URL
        # Format: moonlight://<host>:<port>?app=<app_id>&width=<w>&height=<h>&fps=<fps>&bitrate=<bps>
        params = {
            "width": profile.resolution.split("x")[0],
            "height": profile.resolution.split("x")[1],
            "fps": str(profile.fps),
            "bitrate": str(profile.bitrate_kbps * 1000),
            "codec": profile.codec,
        }

        if app_id and session_type != SessionType.DESKTOP:
            params["app"] = str(app_id)

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        moonlight_url = f"moonlight://{local_ip}:{config.port}?{query_string}"
        sunshine_url = f"sunshine://{local_ip}:{config.port}?{query_string}"

        # Generate QR code
        qr_code_base64 = None
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(moonlight_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            import io
            import base64
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            qr_code_base64 = base64.b64encode(buf.getvalue()).decode()
        except Exception as e:
            logger.warning(f"Failed to generate QR code: {e}")

        return {
            "moonlight_url": moonlight_url,
            "sunshine_url": sunshine_url,
            "qr_code_base64": qr_code_base64,
            "connection_info": {
                "host": local_ip,
                "port": config.port,
                "web_port": config.web_port,
                "username": config.username,
                "quality_profile": quality_profile,
                "resolution": profile.resolution,
                "fps": profile.fps,
                "bitrate_kbps": profile.bitrate_kbps,
                "codec": profile.codec,
            }
        }

    # -------------------------------------------------------------------------
    # App Launch
    # -------------------------------------------------------------------------

    async def launch_app(
        self,
        user_id: UUID,
        app_id: UUID,
        session_type: SessionType = SessionType.APP,
        quality_profile: str = "balanced",
    ) -> Dict[str, Any]:
        """Launch an app/game via Sunshine."""
        # Get app details
        async with get_session() as db:
            app = await db.get(DiscoveredApp, app_id.bytes)
            if not app:
                raise ValueError("App not found")

        # Create session record
        session = await self.create_session(user_id, session_type, quality_profile=quality_profile)

        # Generate stream URL
        stream_info = await self.generate_stream_url(session_type, app_id, quality_profile)

        # Update session with stream info
        await self.update_session_status(
            UUID(bytes=session.id),
            SessionStatus.ACTIVE,
        )

        return {
            "session_id": UUID(bytes=session.id),
            "stream_url": stream_info["moonlight_url"],
            "app_name": app.name,
            "message": f"Iniciando {app.name}... Conecte via Moonlight usando o link ou QR code."
        }

    async def launch_desktop(
        self,
        user_id: UUID,
        quality_profile: str = "balanced",
    ) -> Dict[str, Any]:
        """Launch full desktop streaming."""
        session = await self.create_session(user_id, SessionType.DESKTOP, quality_profile=quality_profile)
        stream_info = await self.generate_stream_url(SessionType.DESKTOP, quality_profile=quality_profile)

        await self.update_session_status(UUID(bytes=session.id), SessionStatus.ACTIVE)

        return {
            "session_id": UUID(bytes=session.id),
            "stream_url": stream_info["moonlight_url"],
            "message": "Iniciando desktop remoto... Conecte via Moonlight."
        }

    # -------------------------------------------------------------------------
    # WebSocket Broadcasting
    # -------------------------------------------------------------------------

    async def _broadcast_sunshine_status(self) -> None:
        """Broadcast Sunshine status via WebSocket."""
        status = await self.get_sunshine_status()
        ws = get_websocket_manager()
        await ws.broadcast({
            "type": "sunshine_status",
            "data": status
        })

    async def _broadcast_session_started(self, session: StreamingSession) -> None:
        """Broadcast session started event."""
        ws = get_websocket_manager()
        await ws.broadcast({
            "type": "session_started",
            "data": {
                "session_id": UUID(bytes=session.id).hex(),
                "session_type": session.session_type.value,
                "status": session.status.value,
                "started_at": session.started_at.isoformat() if session.started_at else None,
            }
        })

    async def _broadcast_session_ended(self, session_id: UUID) -> None:
        """Broadcast session ended event."""
        ws = get_websocket_manager()
        await ws.broadcast({
            "type": "session_ended",
            "data": {
                "session_id": session_id.hex(),
            }
        })


# Singleton instance
_computing_service: Optional[ComputingService] = None


def get_computing_service() -> ComputingService:
    """Get or create the computing service singleton."""
    global _computing_service
    if _computing_service is None:
        _computing_service = ComputingService()
    return _computing_service