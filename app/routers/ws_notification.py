from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.exceptions import HTTPException
from fastapi import status
from jose import jwt, JWTError

from app.config import settings
from app.realtime.manager import ws_manager
from app.models import User
from app.dependencies import get_current_user
from oauth2 import SECRET_KEY, ALGORITHM

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"]
)

def decode_token_user_id(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            ALGORITHM,
            options={"verify_aud": False},
        )
        user_id = int(payload.get("user_id") or payload.get("sub"))
        if not user_id:
            raise ValueError("No user_id in token")
        return user_id
    except(JWTError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from e

@router.websocket("/notifications")
async def ws_notifications(websocket: WebSocket, token: str = Query(..., description="JWT token")):
    
    user_id = decode_token_user_id(token)
    
    await ws_manager.connect(user_id, websocket)
    
    try:
        await websocket.send_json({"type": "hello", "data": {"message": "connected"}})
        
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
    except Exception:
        ws_manager.disconnect(user_id, websocket)
