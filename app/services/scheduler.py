from datetime import datetime, timedelta, timezone
from typing import List

import asyncio
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select, update

from app.database import get_session
from app.models import BorrowRecord, Book, BookStatus, Notification, User, NotificationType

CHECK_INTERVAL = 60 * 60

async def scan_due_and_overdue_once() -> None:
    async with get_session() as db:
        now = datetime.now(timezone.utc)
        
        result = await db.execute(
            select(BorrowRecord)
            .options(
                selectinload(BorrowRecord.book), 
                selectinload(BorrowRecord.user)
            )
            .where(BorrowRecord.returned_at.is_(None))
        )
        active_borrows = result.scalars().all()
        
        for borrow in active_borrows:
            book = borrow.book
            user = borrow.user
            due_at = borrow.due_at
            
            if not due_at:
                continue
        
        if now < due_at and (due_at - now) <= timedelta(hours=24):
            message = f"Reminder: The book '{book.title}' is due tomorrow ({due_at.date()})."
            db.add(Notification(
                user_id=user.id,
                message=message,
                is_read=False,
                created_at=now
            ))
            
        elif now > due_at:
            await db.execute(
                update(Book)
                .where(Book.id == book.id)
                .values(status=BookStatus.Overdue)
            )
            
            db.add(Notification(
                user_id=user.id,
                message=f"Overdue: The book '{book.title}' was due on {due_at.date()}.",
                is_read=False,
                created_at=now
            ))
            
            db.add(Notification(
                user_id=None,
                message=f"User '{user.name}' has an overdue book '{book.title}'.",
                is_read=False,
                created_at=now
            ))
            
        await db.commit()

async def scheduler_loop(interval: int = CHECK_INTERVAL) -> None:
    
    while True:
        try:
            print(f"[scheduler] Running scan at {datetime.now(timezone.utc)}")
            await scan_due_and_overdue_once()
        except Exception as e:
            print(f"[Scheduler Error] {e}")
        await asyncio.sleep(interval)