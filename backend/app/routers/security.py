"""
Security center router — audit logs, alerts, port scanning.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit import AuditLog
from app.models.device import Device, DeviceHistory
from app.schemas.security import AuditLogResponse
from app.services.audit_service import get_audit_service
from app.services.network_scanner import get_network_scanner
from app.routers.auth import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    user_id: Optional[int] = None,
    device_id: Optional[int] = None,
    action: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit logs."""
    audit_svc = get_audit_service()
    logs = await audit_svc.get_logs(db, limit=limit, offset=offset,
                                     user_id=user_id, device_id=device_id, action=action)
    return logs


@router.get("/alerts")
async def get_alerts(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent security alerts."""
    # Recent unknown devices
    unknown_devices = await db.execute(
        select(Device)
        .where(Device.is_known == False, Device.is_online == True)
        .order_by(desc(Device.first_seen))
        .limit(10)
    )
    unknown = unknown_devices.scalars().all()

    alerts = []
    for device in unknown:
        alerts.append({
            "id": f"unknown_{device.id}",
            "alert_type": "unknown_device",
            "severity": "warning",
            "title": "Dispositivo desconhecido na rede",
            "message": f"Dispositivo {device.hostname or device.ip_address or device.mac_address} conectado e não autorizado",
            "device_id": device.id,
            "is_read": False,
            "created_at": device.first_seen.isoformat(),
        })

    # Recent security audit events
    security_actions = ["login_failed", "unauthorized_access", "device_blocked"]
    recent_logs = await db.execute(
        select(AuditLog)
        .where(AuditLog.action.in_(security_actions))
        .order_by(desc(AuditLog.timestamp))
        .limit(20)
    )
    for log in recent_logs.scalars().all():
        alerts.append({
            "id": f"log_{log.id}",
            "alert_type": log.action,
            "severity": "critical" if log.action == "unauthorized_access" else "warning",
            "title": f"Evento: {log.action.replace('_', ' ').title()}",
            "message": log.details or log.resource,
            "device_id": log.device_id,
            "is_read": False,
            "created_at": log.timestamp.isoformat(),
        })

    # Sort by time desc
    alerts.sort(key=lambda x: x["created_at"], reverse=True)
    return {"alerts": alerts[:limit], "total": len(alerts)}


@router.get("/overview")
async def get_security_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get security overview stats."""
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)

    total_devices = await db.scalar(select(func.count(Device.id)))
    authorized_devices = await db.scalar(
        select(func.count(Device.id)).where(Device.is_authorized == True)
    )
    unknown_online = await db.scalar(
        select(func.count(Device.id)).where(
            Device.is_known == False, Device.is_online == True
        )
    )

    # Login failures in last 24h
    login_failures = await db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.action == "login_failed",
            AuditLog.timestamp >= last_24h,
        )
    )

    # New devices in last 24h
    new_devices = await db.scalar(
        select(func.count(Device.id)).where(
            Device.first_seen >= last_24h
        )
    )

    return {
        "total_devices": total_devices or 0,
        "authorized_devices": authorized_devices or 0,
        "unknown_online": unknown_online or 0,
        "login_failures_24h": login_failures or 0,
        "new_devices_24h": new_devices or 0,
        "security_score": _calculate_security_score(
            total_devices or 0, authorized_devices or 0,
            unknown_online or 0, login_failures or 0
        ),
    }


def _calculate_security_score(total: int, authorized: int, unknown_online: int, failures: int) -> int:
    """Calculate a simple security score 0-100."""
    score = 100
    if total > 0:
        unauthorized_ratio = (total - authorized) / total
        score -= int(unauthorized_ratio * 30)
    score -= min(unknown_online * 5, 25)
    score -= min(failures * 2, 20)
    return max(0, score)


@router.post("/scan-ports/{device_id}")
async def scan_device_ports(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Scan open ports on an authorized device."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    if not device.is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only scan authorized devices",
        )

    if not device.ip_address:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device has no IP address")

    scanner = get_network_scanner()
    scan_result = await scanner.nmap_scan(device.ip_address)

    audit_svc = get_audit_service()
    await audit_svc.log(
        db, "port_scan", f"/security/scan-ports/{device_id}",
        user_id=current_user.id,
        device_id=device_id,
        details=f"Port scan on {device.ip_address}: {len(scan_result.get('services', []))} services found",
    )

    return {
        "device_id": device_id,
        "ip_address": device.ip_address,
        "services": scan_result.get("services", []),
        "os_info": scan_result.get("os_info"),
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/events")
async def get_recent_events(
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent device events (connections, disconnections, etc.)."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    result = await db.execute(
        select(DeviceHistory)
        .where(DeviceHistory.timestamp >= since)
        .order_by(desc(DeviceHistory.timestamp))
        .limit(200)
    )
    events = result.scalars().all()

    return {
        "events": [
            {
                "id": e.id,
                "device_id": e.device_id,
                "ip_address": e.ip_address,
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat(),
                "details": e.details,
            }
            for e in events
        ],
        "total": len(events),
    }
