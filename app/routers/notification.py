from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db, get_session
from app.models import Book, User, Role, BorrowRecord, Notification
from .. import schemas
from ..dependencies import role_required, get_current_user
from ..services.scheduler import scan_due_and_overdue_once


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

@router.get("/", response_model=List[schemas.NotificationOut])
async def list_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    unread: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = 50):
    
    stmt = select(Notification).where(Notification.user_id == current_user.id)
    
    if unread is not None:
        stmt = stmt.where(Notification.is_read == unread)
    
    stmt = stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)    
    return result.scalars().all()

@router.patch("/{id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_as_read(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    
    result = await db.execute(
        select(Notification).where(
            Notification.id == id,
            Notification.user_id == current_user.id
            )
        )
    notify = result.scalars().first()
    
    if not notify:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Notificaton not found")
    
    notify.is_read = True
    await db.commit()
    await db.refresh(notify)
    return None

@router.get("/overdue", response_model=List[schemas.OverdueBorrowOut])
async def list_overdue(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(role_required(Role.Librarian)),
    search: Optional[str] = Query(None),
    limit: int = 50,
    skip: int = 0
    ):
    
    now = datetime.now(timezone.utc)
    
    stmt = (
        select(BorrowRecord)
        .options(
            selectinload(BorrowRecord.user),
            selectinload(BorrowRecord.book))
        .where(BorrowRecord.returned_at.is_(None), BorrowRecord.due_at < now)
        )
    
    if search:
        stmt = (
            stmt.join(BorrowRecord.user).join(BorrowRecord.book)
            .where(
                or_(
                    User.name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    Book.title.ilike(f"%{search}%")                    
                )
            )
        )
    
    stmt = stmt.order_by(BorrowRecord.due_at.asc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/scan", status_code=status.HTTP_200_OK)
async def manual_scan(
    _: User = Depends(role_required(Role.Librarian))):
    async with get_session() as db:
        await scan_due_and_overdue_once()
    return {"detail": "Manual scan completed"}