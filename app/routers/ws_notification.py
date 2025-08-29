from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status, HTTPException
from jose import jwt, JWTError
from typing import Optional

from app.realtime.manager import ws_manager
from ..oauth2 import SECRET_KEY, ALGORITHM

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"]
)

def get_user_id_from_token(token: str) -> Optional[int]:
    
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_aud": False}
        )
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except (JWTError, ValueError, TypeError):
        return None

@router.websocket("/notifications")
async def ws_notifications(
    websocket: WebSocket,
    token: str = Query(..., description="JWT Access Token")
    ):
    
    user_id = get_user_id_from_token(token)
    
    if user_id is None:
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token")
        return
    
    await ws_manager.connect(user_id, websocket)
    
    try:
        await websocket.send_json({"type": "status", "data": "Connection successful"})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"Client {user_id} disconnected.")
    except Exception as e:
        print(f"An error occurred with client {user_id}: {e}")
    finally:
        ws_manager.disconnect(user_id, websocket)