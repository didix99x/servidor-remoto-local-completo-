"""
WebSocket connection manager for real-time updates.
"""
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")

    async def disconnect(self, client_id: str) -> None:
        async with self._lock:
            self.active_connections.pop(client_id, None)
        logger.info(f"WebSocket client disconnected: {client_id}")

    async def send_to_client(self, client_id: str, data: dict) -> bool:
        websocket = self.active_connections.get(client_id)
        if not websocket:
            return False
        try:
            await websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(f"Failed to send to client {client_id}: {e}")
            await self.disconnect(client_id)
            return False

    async def broadcast(self, data: dict) -> int:
        """Broadcast to all connected clients. Returns number of successful sends."""
        if not self.active_connections:
            return 0

        disconnected = []
        sent = 0

        async with self._lock:
            clients = list(self.active_connections.items())

        for client_id, websocket in clients:
            try:
                await websocket.send_json(data)
                sent += 1
            except Exception as e:
                logger.warning(f"Failed to broadcast to {client_id}: {e}")
                disconnected.append(client_id)

        for client_id in disconnected:
            await self.disconnect(client_id)

        return sent

    def get_connection_count(self) -> int:
        return len(self.active_connections)

    async def broadcast_device_status(self, device_id: int, is_online: bool) -> None:
        """Broadcast device online/offline status change."""
        await self.broadcast({
            "type": "device_status",
            "data": {
                "device_id": device_id,
                "is_online": is_online,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        })

    async def broadcast_device_discovered(self, device) -> None:
        """Broadcast new device discovery."""
        await self.broadcast({
            "type": "device_discovered",
            "data": {
                "device_id": device.id,
                "mac_address": device.mac_address,
                "ip_address": device.ip_address,
                "hostname": device.hostname,
                "vendor": device.vendor,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        })

    async def broadcast_scan_started(self) -> None:
        await self.broadcast({"type": "scan_started", "data": {"timestamp": datetime.now(timezone.utc).isoformat()}})

    async def broadcast_scan_completed(self, stats: dict) -> None:
        await self.broadcast({"type": "scan_completed", "data": {**stats, "timestamp": datetime.now(timezone.utc).isoformat()}})

    async def broadcast_security_alert(self, alert_type: str, severity: str, message: str, device_id: Optional[int] = None) -> None:
        await self.broadcast({
            "type": "security_alert",
            "data": {
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "device_id": device_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        })

    async def broadcast_system_stats(self, stats: dict) -> None:
        await self.broadcast({"type": "system_stats", "data": stats})

    async def broadcast_sunshine_status(self, status: dict) -> None:
        await self.broadcast({"type": "sunshine_status", "data": status})

    async def broadcast_session_started(self, session_data: dict) -> None:
        await self.broadcast({"type": "session_started", "data": session_data})

    async def broadcast_session_ended(self, session_id: str) -> None:
        await self.broadcast({"type": "session_ended", "data": {"session_id": session_id}})

    async def broadcast_session_update(self, session_data: dict) -> None:
        await self.broadcast({"type": "session_update", "data": session_data})


# Singleton
_manager: Optional[ConnectionManager] = None


def get_websocket_manager() -> ConnectionManager:
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
