"""
Device manager router — pairing, authorization, remote access.
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.device import Device, DeviceHistory
from app.models.pairing import PairingRequest, PairingStatus
from app.schemas.security import PairingRequestResponse, PairingActionRequest
from app.schemas.device import DeviceResponse, DeviceUpdate
from app.services.audit_service import get_audit_service
from app.services.websocket_manager import get_websocket_manager
from app.routers.auth import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/pairing/requests", response_model=List[PairingRequestResponse])
async def list_pairing_requests(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List pairing requests."""
    query = select(PairingRequest).order_by(desc(PairingRequest.requested_at))
    if status_filter:
        try:
            query = query.where(PairingRequest.status == PairingStatus(status_filter))
        except ValueError:
            pass

    result = await db.execute(query)
    requests = result.scalars().all()

    # Enrich with device info
    response = []
    for req in requests:
        device = req.device
        response.append(PairingRequestResponse(
            id=req.id,
            device_id=req.device_id,
            device_mac=device.mac_address if device else "unknown",
            device_ip=device.ip_address if device else None,
            device_hostname=device.hostname if device else None,
            device_vendor=device.vendor if device else None,
            requester_name=req.requester_name,
            status=req.status,
            requested_at=req.requested_at,
            responded_at=req.responded_at,
            responded_by=req.responded_by,
        ))

    return response


@router.post("/pairing/request")
async def create_pairing_request(
    device_id: int,
    requester_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Submit a pairing request (can be called without auth, from a new device)."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    # Check if already has a pending request
    existing = await db.execute(
        select(PairingRequest).where(
            PairingRequest.device_id == device_id,
            PairingRequest.status == PairingStatus.PENDING,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pairing request already pending")

    req = PairingRequest(
        device_id=device_id,
        requester_name=requester_name,
        status=PairingStatus.PENDING,
    )
    db.add(req)
    await db.flush()

    # Notify via WebSocket
    ws = get_websocket_manager()
    await ws.broadcast_security_alert(
        "pairing_request", "info",
        f"New pairing request from '{requester_name}' ({device.ip_address})",
        device_id=device_id,
    )

    return {"message": "Pairing request submitted", "request_id": req.id}


@router.post("/pairing/requests/{request_id}/action")
async def respond_to_pairing_request(
    request_id: int,
    body: PairingActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a pairing request."""
    result = await db.execute(select(PairingRequest).where(PairingRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if req.status != PairingStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request already processed")

    now = datetime.now(timezone.utc)
    req.responded_at = now
    req.responded_by = current_user.id
    req.notes = body.notes

    if body.action == "approve":
        req.status = PairingStatus.APPROVED
        # Authorize the device
        device_result = await db.execute(select(Device).where(Device.id == req.device_id))
        device = device_result.scalar_one_or_none()
        if device:
            device.is_authorized = True
            device.is_known = True
            history = DeviceHistory(
                device_id=device.id,
                ip_address=device.ip_address,
                event_type="paired",
                details=f"Device paired and authorized by {current_user.username}",
            )
            db.add(history)
    else:
        req.status = PairingStatus.REJECTED

    audit_svc = get_audit_service()
    await audit_svc.log(
        db, f"pairing_{body.action}d", f"/devices/pairing/{request_id}",
        user_id=current_user.id,
        device_id=req.device_id,
        details=f"Pairing request {body.action}d for device {req.device_id}",
    )

    return {"message": f"Request {body.action}d successfully"}


@router.post("/{device_id}/authorize")
async def authorize_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Directly authorize a device."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    device.is_authorized = True
    device.is_known = True

    history = DeviceHistory(
        device_id=device.id,
        ip_address=device.ip_address,
        event_type="authorized",
        details=f"Authorized by {current_user.username}",
    )
    db.add(history)

    audit_svc = get_audit_service()
    await audit_svc.log(
        db, "device_authorized", f"/devices/{device_id}",
        user_id=current_user.id,
        device_id=device_id,
    )

    return {"message": "Device authorized"}


@router.post("/{device_id}/revoke")
async def revoke_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke device authorization."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    device.is_authorized = False

    history = DeviceHistory(
        device_id=device.id,
        ip_address=device.ip_address,
        event_type="revoked",
        details=f"Authorization revoked by {current_user.username}",
    )
    db.add(history)

    audit_svc = get_audit_service()
    await audit_svc.log(
        db, "device_revoked", f"/devices/{device_id}",
        user_id=current_user.id,
        device_id=device_id,
    )

    return {"message": "Device access revoked"}


@router.post("/{device_id}/block")
async def block_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Block a device (mark as not authorized and log)."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    device.is_authorized = False
    device.is_known = True
    device.notes = (device.notes or "") + f"\n[BLOCKED by {current_user.username}]"

    history = DeviceHistory(
        device_id=device.id,
        ip_address=device.ip_address,
        event_type="blocked",
        details=f"Device blocked by {current_user.username}",
    )
    db.add(history)

    ws = get_websocket_manager()
    await ws.broadcast_security_alert(
        "device_blocked", "warning",
        f"Device {device.hostname or device.ip_address or device.mac_address} has been blocked",
        device_id=device_id,
    )

    return {"message": "Device blocked"}
