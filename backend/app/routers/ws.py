"""
WebSocket router for real-time updates.
"""
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.websocket_manager import get_websocket_manager
from app.services.auth_service import get_auth_service

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(default=""),
):
    """WebSocket connection for real-time updates."""
    # Validate token
    auth_svc = get_auth_service()
    payload = auth_svc.decode_token(token) if token else None

    client_id = str(uuid.uuid4())
    manager = get_websocket_manager()

    await manager.connect(websocket, client_id)

    try:
        # Send welcome message
        await manager.send_to_client(client_id, {
            "type": "connected",
            "data": {
                "client_id": client_id,
                "authenticated": payload is not None,
            }
        })

        # Keep alive and handle messages
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "ping":
                await manager.send_to_client(client_id, {"type": "pong"})

    except WebSocketDisconnect:
        await manager.disconnect(client_id)
    except Exception:
        await manager.disconnect(client_id)
