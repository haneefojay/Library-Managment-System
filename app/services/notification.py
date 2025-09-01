from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Notification, User, NotificationPreference,  NotificationType
from app.realtime.manager import ws_manager
from .email import send_email_async, email_enabled
from typing import Optional, Dict, Any

async def dispatch_notification_task(user_id: int, subject: str, message: str, ws_payload: Dict[str, Any]):
    
    from app.database import get_session
    
    async with get_session() as db:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            print(f"[Notification Dispatch] User {user_id} not found.")
            return
        
        preference = user.notification_preference
        print(f"[Notification Dispatch] User {user.name} preference is {preference.name}.")
        
        if preference in [NotificationPreference.WEBSOCKET, NotificationPreference.ALL]:
            print(f"[Notification Dispatch] Sending WebSocket notification to user {user.name}.")
            await ws_manager.send_to_user(user_id, ws_payload)
        
        if preference in [NotificationPreference.EMAIL, NotificationPreference.ALL]:
            print(f"[Notification Dispatch] Sending email notification to user {user.name}.")
            success, error = await send_email_async(to=user.email, subject=subject, body=message)
            
            if not success:
                print(f"[Notification Error] Could not send email to {user.email}: {error}")

async def create_notification_in_db(
    db: AsyncSession,
    user_id: Optional[int],
    message: str,
    type: NotificationType,
    ) -> Notification:
    
    notif = Notification(
        user_id=user_id,
        message=message,
        type=type,
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(notif)
    await db.flush()
    await db.refresh(notif)
    return notif


'''
async def create_notification_and_push(
    db: AsyncSession,
    user_id: Optional[int],
    message: str,
    type: str,
) -> Notification:

    notif = Notification(
        user_id=user_id,
        message=message,
        type=type,
        is_read=False,        
        created_at=datetime.now(timezone.utc),
    )
    db.add(notif)
    await db.flush()
    await db.refresh(notif)

    if user_id is not None:
        await ws_manager.send_to_user(
            user_id,            
            {"type": "notification", "data": {
                "id": notif.id,
                "message": notif.message,
                "is_read": notif.is_read,
                "created_at": notif.created_at.isoformat(),
            }},
        )
    return notif
'''