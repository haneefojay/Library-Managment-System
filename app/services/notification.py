from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Notification
from app.realtime.manager import ws_manager
from typing import Optional

async def create_notification_and_push(
    db: AsyncSession,
    user_id: Optional[int],
    message: str,
) -> Notification:

    notif = Notification(
        user_id=user_id,
        message=message,
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(notif)
    await db.flush()
    await db.refresh(notif)

    if user_id is not None:
        await ws_manager.send_to_user(
            user_id,
            {
                "type": "notification",
                "data": {
                    "id": notif.id,
                    "message": notif.message,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at.isoformat(),
                },
            },
        )
    return notif
