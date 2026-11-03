"""
Computing router — Centralized computing / game streaming API.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.models.computing import (
    DiscoveredApp,
    SessionStatus,
    SessionType,
    StreamingSession,
    SunshineConfig,
)
from app.models.device import Device
from app.models.user import User, UserRole
from app.routers.auth import get_current_user
from app.schemas.computing import (
    AppLaunchRequest,
    AppLaunchResponse,
    DiscoveredAppResponse,
    QualityProfile,
    QUALITY_PROFILES,
    SessionType as SchemaSessionType,
    SessionStatus as SchemaSessionStatus,
    StreamUrlRequest,
    StreamUrlResponse,
    StreamingSessionResponse,
    SunshineConfigCreate,
    SunshineConfigResponse,
    SunshineConfigUpdate,
    SunshineStatus,
    SystemComputingInfo,
    VideoEncoder,
)
from app.services.computing_service import get_computing_service

router = APIRouter(prefix="/computing", tags=["computing"])


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _uuid_to_bytes(uuid_obj: UUID) -> bytes:
    return uuid_obj.bytes


def _bytes_to_uuid(b: bytes) -> UUID:
    return UUID(bytes=b)


def _session_to_response(session: StreamingSession) -> StreamingSessionResponse:
    return StreamingSessionResponse(
        id=_bytes_to_uuid(session.id),
        user_id=_bytes_to_uuid(session.user_id),
        device_id=_bytes_to_uuid(session.device_id) if session.device_id else None,
        session_type=SchemaSessionType(session.session_type.value),
        sunshine_session_id=session.sunshine_session_id,
        client_ip=session.client_ip,
        status=SchemaSessionStatus(session.status.value),
        started_at=session.started_at,
        ended_at=session.ended_at,
        error_message=session.error_message,
        resolution=session.resolution,
        fps=session.fps,
        bitrate=session.bitrate,
        codec=session.codec,
    )


def _app_to_response(app: DiscoveredApp) -> DiscoveredAppResponse:
    return DiscoveredAppResponse(
        id=_bytes_to_uuid(app.id),
        sunshine_app_id=app.sunshine_app_id,
        name=app.name,
        executable_path=app.executable_path,
        working_directory=app.working_directory,
        launch_args=app.launch_args,
        app_type=app.app_type,
        publisher=app.publisher,
        version=app.version,
        is_sunshine_app=bool(app.is_sunshine_app),
        sunshine_image_url=app.sunshine_image_url,
        detected_at=app.detected_at,
        last_seen_at=app.last_seen_at,
        is_active=bool(app.is_active),
    )


def _config_to_response(config: SunshineConfig) -> SunshineConfigResponse:
    # Handle both enum object and string value from database
    video_encoder_val = config.video_encoder.value if hasattr(config.video_encoder, 'value') else config.video_encoder
    return SunshineConfigResponse(
        id=config.id,
        host=config.host,
        port=config.port,
        web_port=config.web_port,
        username=config.username,
        is_enabled=bool(config.is_enabled),
        auto_start=bool(config.auto_start),
        video_encoder=VideoEncoder(video_encoder_val),
        audio_encoder=config.audio_encoder,
        max_bitrate=config.max_bitrate,
        max_fps=config.max_fps,
        resolution=config.resolution,
        gpu_device_id=config.gpu_device_id,
        enable_hevc=bool(config.enable_hevc),
        enable_av1=bool(config.enable_av1),
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


# -------------------------------------------------------------------------
# Sunshine Status
# -------------------------------------------------------------------------

@router.get("/status", response_model=SystemComputingInfo)
async def get_computing_status(
    current_user: User = Depends(get_current_user),
):
    """Get complete computing status: system info + GPU + Sunshine."""
    service = get_computing_service()
    settings = get_settings()

    # Get system info from system_service
    from app.services.system_service import get_system_info
    sys_info = get_system_info()

    # Get GPU info
    gpus = []
    recommended_encoder = VideoEncoder.NVENC
    try:
        import GPUtil
        gpu_list = GPUtil.getGPUs()
        for gpu in gpu_list:
            encoders = ["nvenc"] if "NVIDIA" in gpu.name.upper() else []
            if "AMD" in gpu.name.upper() or "RADEON" in gpu.name.upper():
                encoders.append("amf")
            if "INTEL" in gpu.name.upper() or "UHD" in gpu.name.upper() or "IRIS" in gpu.name.upper() or "ARC" in gpu.name.upper():
                encoders.append("qsv")

            gpus.append({
                "name": gpu.name,
                "memory_total_mb": int(gpu.memoryTotal),
                "memory_used_mb": int(gpu.memoryUsed),
                "utilization_percent": gpu.load * 100,
                "temperature_c": gpu.temperature if gpu.temperature > 0 else None,
                "encoder_support": encoders,
            })

            # Prefer NVIDIA > AMD > Intel > Software
            if "NVIDIA" in gpu.name.upper():
                recommended_encoder = VideoEncoder.NVENC
            elif "AMD" in gpu.name.upper() or "RADEON" in gpu.name.upper():
                recommended_encoder = VideoEncoder.AMF
            elif "INTEL" in gpu.name.upper() and recommended_encoder == VideoEncoder.NVENC:
                recommended_encoder = VideoEncoder.QSV

    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.debug(f"GPU detection failed: {e}")

    # Get Sunshine status
    sunshine_status = await service.get_sunshine_status()

    return SystemComputingInfo(
        cpu_percent=sys_info.get("cpu_percent", 0),
        cpu_count=sys_info.get("cpu_count", 0),
        memory_percent=sys_info.get("memory_percent", 0),
        memory_total_gb=sys_info.get("memory_total_gb", 0),
        memory_used_gb=sys_info.get("memory_used_gb", 0),
        memory_available_gb=sys_info.get("memory_available_gb", 0),
        disk_percent=sys_info.get("disk_percent", 0),
        disk_total_gb=sys_info.get("disk_total_gb", 0),
        disk_used_gb=sys_info.get("disk_used_gb", 0),
        disk_free_gb=sys_info.get("disk_free_gb", 0),
        gpus=gpus,
        recommended_encoder=recommended_encoder,
        sunshine_status=SunshineStatus(**sunshine_status) if sunshine_status else None,
    )


# -------------------------------------------------------------------------
# Sunshine Control
# -------------------------------------------------------------------------

@router.post("/sunshine/start")
async def start_sunshine(
    current_user: User = Depends(get_current_user),
):
    """Start Sunshine streaming host."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")

    service = get_computing_service()
    success = await service.start_sunshine()

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to start Sunshine")

    return {"success": True, "message": "Sunshine iniciado com sucesso"}


@router.post("/sunshine/stop")
async def stop_sunshine(
    current_user: User = Depends(get_current_user),
):
    """Stop Sunshine streaming host."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")

    service = get_computing_service()
    success = await service.stop_sunshine()

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to stop Sunshine")

    return {"success": True, "message": "Sunshine parado com sucesso"}


@router.post("/sunshine/restart")
async def restart_sunshine(
    current_user: User = Depends(get_current_user),
):
    """Restart Sunshine streaming host."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")

    service = get_computing_service()
    success = await service.restart_sunshine()

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to restart Sunshine")

    return {"success": True, "message": "Sunshine reiniciado com sucesso"}


# -------------------------------------------------------------------------
# Sunshine Configuration
# -------------------------------------------------------------------------

@router.get("/sunshine/config", response_model=SunshineConfigResponse)
async def get_sunshine_config(
    current_user: User = Depends(get_current_user),
):
    """Get Sunshine configuration."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")

    service = get_computing_service()
    config = await service.get_config()

    if not config:
        # Return default config response
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuração não encontrada")

    return _config_to_response(config)


@router.put("/sunshine/config", response_model=SunshineConfigResponse)
async def update_sunshine_config(
    updates: SunshineConfigUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update Sunshine configuration."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")

    service = get_computing_service()

    # Convert to dict, excluding None values
    update_dict = updates.model_dump(exclude_unset=True, exclude_none=True)

    # Convert enum values
    if "video_encoder" in update_dict:
        update_dict["video_encoder"] = update_dict["video_encoder"].value

    success = await service.update_config(update_dict)

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update config")

    config = await service.get_config()
    return _config_to_response(config)


# -------------------------------------------------------------------------
# App Discovery
# -------------------------------------------------------------------------

@router.get("/apps", response_model=List[DiscoveredAppResponse])
async def list_apps(
    force_refresh: bool = Query(False, description="Forçar nova descoberta"),
    app_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    current_user: User = Depends(get_current_user),
):
    """List discovered applications/games."""
    service = get_computing_service()

    if force_refresh:
        apps_data = await service.discover_apps(force=True)
    else:
        # Get from DB
        async with get_session() as db:
            query = select(DiscoveredApp).where(DiscoveredApp.is_active == 1)
            if app_type:
                query = query.where(DiscoveredApp.app_type == app_type)
            query = query.order_by(DiscoveredApp.name)
            result = await db.execute(query)
            apps = list(result.scalars().all())
            return [_app_to_response(a) for a in apps]

    return [_app_to_response(a) for a in apps_data]


@router.post("/apps/refresh")
async def refresh_apps(
    current_user: User = Depends(get_current_user),
):
    """Force refresh of app discovery."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")

    service = get_computing_service()
    apps = await service.discover_apps(force=True)

    return {"success": True, "count": len(apps), "message": f"{len(apps)} aplicações descobertas"}


# -------------------------------------------------------------------------
# Stream URL Generation
# -------------------------------------------------------------------------

@router.post("/stream-url", response_model=StreamUrlResponse)
async def generate_stream_url(
    request: StreamUrlRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate Moonlight/Sunshine connection URL."""
    service = get_computing_service()

    try:
        result = await service.generate_stream_url(
            session_type=SessionType(request.session_type.value),
            app_id=request.app_id,
            quality_profile=request.quality_profile,
            device_type=request.device_type,
        )
        return StreamUrlResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# -------------------------------------------------------------------------
# App Launch
# -------------------------------------------------------------------------

@router.post("/apps/launch", response_model=AppLaunchResponse)
async def launch_app(
    request: AppLaunchRequest,
    current_user: User = Depends(get_current_user),
):
    """Launch an app/game via Sunshine."""
    service = get_computing_service()

    try:
        result = await service.launch_app(
            user_id=current_user.id,
            app_id=request.app_id,
            session_type=SessionType(request.session_type.value),
            quality_profile=request.quality_profile,
        )
        return AppLaunchResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/desktop/launch", response_model=AppLaunchResponse)
async def launch_desktop(
    quality_profile: str = Query("balanced", pattern=r"^(ultra|high|balanced|economy|mobile)$"),
    current_user: User = Depends(get_current_user),
):
    """Launch full desktop streaming."""
    service = get_computing_service()

    try:
        result = await service.launch_desktop(
            user_id=current_user.id,
            quality_profile=quality_profile,
        )
        return AppLaunchResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# -------------------------------------------------------------------------
# Session Management
# -------------------------------------------------------------------------

@router.get("/sessions", response_model=List[StreamingSessionResponse])
async def list_sessions(
    active_only: bool = Query(False, description="Apenas sessões ativas"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    """List streaming sessions (active or history)."""
    service = get_computing_service()

    if active_only:
        sessions = await service.get_active_sessions()
    else:
        sessions = await service.get_session_history(limit=limit)

    # Filter by user if not admin
    if current_user.role != UserRole.ADMIN:
        sessions = [s for s in sessions if UUID(bytes=s.user_id) == current_user.id]

    return [_session_to_response(s) for s in sessions]


@router.post("/sessions/{session_id}/terminate")
async def terminate_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Terminate a streaming session."""
    service = get_computing_service()

    # Check ownership
    session = await service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada")

    if current_user.role != UserRole.ADMIN and UUID(bytes=session.user_id) != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para encerrar esta sessão")

    success = await service.terminate_session(session_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao encerrar sessão")

    return {"success": True, "message": "Sessão encerrada com sucesso"}


# -------------------------------------------------------------------------
# Quality Profiles
# -------------------------------------------------------------------------

@router.get("/quality-profiles")
async def get_quality_profiles(
    current_user: User = Depends(get_current_user),
):
    """Get available quality profiles."""
    return {
        "profiles": [
            {
                "name": p.name,
                "label": p.label,
                "resolution": p.resolution,
                "fps": p.fps,
                "bitrate_kbps": p.bitrate_kbps,
                "codec": p.codec,
                "description": p.description,
            }
            for p in QUALITY_PROFILES.values()
        ]
    }


# Import logging at the top
import logging
logger = logging.getLogger(__name__)