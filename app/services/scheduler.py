import asyncio
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models import Book, BookStatus, BorrowRecord, Notification, User, Role, NotificationType
from app.services.notification import create_notification_and_push

CHECK_INTERVAL = 30
REMINDER_DAYS_BEFORE = 1


async def scan_due_and_overdue_once() -> None:
    async with get_session() as db:
        now = datetime.now(timezone.utc)
        reminder_window_end = now + timedelta(minutes=REMINDER_DAYS_BEFORE)
        
        stmt = (
            select(BorrowRecord)
            .options(selectinload(BorrowRecord.book), selectinload(BorrowRecord.user))
            .where(
                BorrowRecord.returned_at.is_(None),
                or_(
                    (BorrowRecord.due_at < now) & (BorrowRecord.overdue_notified == False),
                    (BorrowRecord.due_at <= reminder_window_end)
                    & (BorrowRecord.due_at > now)
                    & (BorrowRecord.reminder_sent_at.is_(None)),
                ),
            )
        )

        result = await db.execute(stmt)
        records_to_process: List[BorrowRecord] = result.scalars().all()

        if not records_to_process:
            print("[scheduler] No records to process.")
            return

        print(f"[scheduler] Processing {len(records_to_process)} records.")

        for borrow in records_to_process:
            book = borrow.book
            user = borrow.user
            
            if borrow.due_at < now and not borrow.overdue_notified:
                print(f"[scheduler] Processing overdue book '{book.title}' for user '{user.name}'.")
                book.status = BookStatus.Overdue
                db.add(book)
                
                await create_notification_and_push(
                    db,
                    user_id=user.id,
                    message=f"The book '{book.title}' was due on {borrow.due_at.date()}.",
                    type=NotificationType.Overdue
                )
                
                librarian_result = await db.execute(select(User).where(User.role == Role.Librarian))
                librarians = librarian_result.scalars().all()
                
                for librarian in librarians:
                    await create_notification_and_push(
                    db,
                    user_id=librarian.id,
                    message=f"User '{user.name}' has an overdue book: '{book.title}'.",
                    type=NotificationType.System
                )                
                
                borrow.overdue_notified = True
                db.add(borrow)
                
                
            elif borrow.reminder_sent_at is None:
                print(f"[scheduler] Sending reminder for '{book.title}' to user '{user.name}'.")
                
                await create_notification_and_push(
                    db,
                    user_id=user.id,
                    message=f"The book '{book.title}' is due on {borrow.due_at.date()}.",
                    type=NotificationType.Reminder
                )
                
                borrow.reminder_sent_at = now
                db.add(borrow)
                
        await db.commit()
        print("[scheduler] Scan complete. All changes committed.")


async def scheduler_loop(interval: int = CHECK_INTERVAL) -> None:
    
    print("[scheduler] Scheduler loop started.")
    while True:
        try:
            print(f"[scheduler] Running scan at {datetime.now(timezone.utc)}")
            await scan_due_and_overdue_once()
        except Exception as e:
            print(f"[Scheduler Error] An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[scheduler] Next scan in {interval} seconds.")
        await asyncio.sleep(interval)