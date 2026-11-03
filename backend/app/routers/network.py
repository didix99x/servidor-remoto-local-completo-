"""
Network monitoring router.
"""
import asyncio
import socket
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.device import Device, DeviceHistory, DeviceType
from app.schemas.device import (
    DeviceResponse, DeviceUpdate, DeviceHistoryResponse,
    NetworkMapResponse, NetworkMapNode, NetworkMapEdge, NetworkScanRequest
)
from app.schemas.network import NetworkStatusResponse
from app.services.network_scanner import get_network_scanner
from app.services.websocket_manager import get_websocket_manager
from app.routers.auth import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/network", tags=["network"])


@router.get("/status", response_model=NetworkStatusResponse)
async def get_network_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current network monitoring status."""
    scanner = get_network_scanner()

    total = await db.scalar(select(func.count(Device.id)))
    online = await db.scalar(select(func.count(Device.id)).where(Device.is_online == True))
    unknown = await db.scalar(select(func.count(Device.id)).where(Device.is_known == False))

    # Last scan time from history
    last_history = await db.execute(
        select(DeviceHistory.timestamp).order_by(desc(DeviceHistory.timestamp)).limit(1)
    )
    last_scan = last_history.scalar_one_or_none()

    return NetworkStatusResponse(
        is_scanning=scanner.is_scanning,
        last_scan=last_scan,
        devices_online=online or 0,
        devices_total=total or 0,
        devices_unknown=unknown or 0,
        scan_interval_minutes=scanner.settings.scan_interval_minutes,
    )


@router.post("/scan")
async def trigger_scan(
    background_tasks: BackgroundTasks,
    body: NetworkScanRequest = NetworkScanRequest(),
    current_user: User = Depends(get_current_user),
):
    """Trigger a network scan."""
    scanner = get_network_scanner()

    if scanner.is_scanning:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Scan already in progress")

    async def run_scan():
        ws = get_websocket_manager()
        await ws.broadcast_scan_started()
        stats = await scanner.full_scan()
        await ws.broadcast_scan_completed(stats)

    background_tasks.add_task(run_scan)
    return {"message": "Scan started", "scan_type": body.scan_type}


@router.get("/devices", response_model=List[DeviceResponse])
async def list_devices(
    online_only: bool = False,
    authorized_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all network devices."""
    query = select(Device).order_by(desc(Device.last_seen))

    if online_only:
        query = query.where(Device.is_online == True)
    if authorized_only:
        query = query.where(Device.is_authorized == True)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get device details."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.put("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    body: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update device info."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    if body.hostname is not None:
        device.hostname = body.hostname
    if body.device_type is not None:
        device.device_type = body.device_type
    if body.notes is not None:
        device.notes = body.notes
    if body.is_known is not None:
        device.is_known = body.is_known
    if body.is_authorized is not None:
        old_auth = device.is_authorized
        device.is_authorized = body.is_authorized
        if body.is_authorized and not old_auth:
            history = DeviceHistory(
                device_id=device.id,
                ip_address=device.ip_address,
                event_type="authorized",
                details=f"Device authorized by {current_user.username}",
            )
            db.add(history)

    await db.flush()
    await db.refresh(device)
    return device


@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a device record (admin only)."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    await db.delete(device)
    return {"message": "Device deleted"}


@router.get("/devices/{device_id}/history", response_model=List[DeviceHistoryResponse])
async def get_device_history(
    device_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get device connection history."""
    result = await db.execute(
        select(DeviceHistory)
        .where(DeviceHistory.device_id == device_id)
        .order_by(desc(DeviceHistory.timestamp))
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/map", response_model=NetworkMapResponse)
async def get_network_map(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get network topology map."""
    result = await db.execute(select(Device).order_by(Device.is_online.desc()))
    devices = result.scalars().all()

    # Detect local server IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        server_ip = s.getsockname()[0]
        s.close()
    except Exception:
        server_ip = "127.0.0.1"

    nodes = []
    edges = []

    # Add gateway node
    nodes.append(NetworkMapNode(
        id="gateway",
        label="Router/Gateway",
        ip=None,
        mac="00:00:00:00:00:00",
        type=DeviceType.ROUTER,
        is_online=True,
        is_authorized=True,
        vendor="Router",
    ))

    # Add server node
    nodes.append(NetworkMapNode(
        id="server",
        label="Este Servidor",
        ip=server_ip,
        mac="FF:FF:FF:FF:FF:FF",
        type=DeviceType.COMPUTER,
        is_online=True,
        is_authorized=True,
        vendor="Local",
    ))
    edges.append(NetworkMapEdge(source="server", target="gateway"))

    for device in devices:
        node_id = f"dev_{device.id}"
        label = device.hostname or device.ip_address or device.mac_address
        nodes.append(NetworkMapNode(
            id=node_id,
            label=label,
            ip=device.ip_address,
            mac=device.mac_address,
            type=device.device_type,
            is_online=device.is_online,
            is_authorized=device.is_authorized,
            vendor=device.vendor,
        ))
        edges.append(NetworkMapEdge(source=node_id, target="gateway"))

    return NetworkMapResponse(nodes=nodes, edges=edges)


@router.get("/local-ip")
async def get_local_ip():
    """Get server's local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return {"ip": local_ip}
    except Exception:
        return {"ip": "127.0.0.1"}
