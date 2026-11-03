"""
System info router — CPU, RAM, disk, uptime.
"""
import sys
import platform
from fastapi import APIRouter, Depends
from app.services.system_service import get_system_info
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info")
async def system_info(current_user: User = Depends(get_current_user)):
    """Get current system stats."""
    return get_system_info()


@router.get("/version")
async def version():
    """Get server version info (public)."""
    return {
        "name": "Home Network Control Center",
        "version": "1.0.0",
        "python": sys.version.split()[0],
        "platform": platform.system(),
    }
