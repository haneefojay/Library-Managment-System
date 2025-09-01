from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import Book, User, Role, BorrowRecord, BookStatus
from .. import schemas
from ..dependencies import role_required, get_current_user

router = APIRouter(
    prefix="/borrow_book",
    tags=["Borrow Book"]
)

@router.post("/{id}", response_model=schemas.BorrowBook)
async def borrow_book(
    id: int, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(Role.Member))):
    
    result = await db.execute(select(Book).options(selectinload(Book.author)).where(Book.id == id))
    book = result.scalars().first()
    
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    active = await db.execute(select(BorrowRecord).where(BorrowRecord.book_id == id, BorrowRecord.returned_at.is_(None)))
    borrow = active.scalars().first()
    
    if borrow:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book already borrowed")
    
    borrowed = BorrowRecord(
        user_id = current_user.id,
        book_id = id,
        due_at = datetime.now(timezone.utc) + timedelta(days=14)
    )
    db.add(borrowed)
    
    book.status = BookStatus.Borrowed
    await db.commit()
    
    result = await db.execute(
        select(BorrowRecord).
        options(
            selectinload(BorrowRecord.book).selectinload(Book.author),
            selectinload(BorrowRecord.user)
            )
        .where(BorrowRecord.id == borrowed.id)
        )
    new_borrow_record = result.scalars().first()
    
    return new_borrow_record


@router.patch("/{id}/return")
async def return_book(
    id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(Role.Member))):
    
    result = await db.execute(
        select(BorrowRecord)
        .options(selectinload(BorrowRecord.book))
        .where(
            BorrowRecord.book_id == id, 
            BorrowRecord.user_id == current_user.id, 
            BorrowRecord.returned_at.is_(None)
        )
        .order_by(BorrowRecord.borrowed_at.desc()) 
    )
    borrow = result.scalars().first()
    
    if not borrow:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active borrow record found")
    
    borrow.returned_at = datetime.now(timezone.utc)
    borrow.book.status = BookStatus.Available
    
    await db.commit()
    
    result = await db.execute(select(BorrowRecord).options(
        selectinload(BorrowRecord.book),
        ).where(BorrowRecord.id == borrow.id)
    )
    updated_borrow = result.scalars().first()
    
    return updated_borrow


@router.get("/me", response_model=List[schemas.BorrowBook])
async def get_my_borrows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(Role.Member))):
    
    query = await db.execute(
        select(BorrowRecord)
        .options(
            selectinload(BorrowRecord.book).selectinload(Book.author),
            selectinload(BorrowRecord.user)
        )
        .where(BorrowRecord.user_id == current_user.id)
        .order_by(BorrowRecord.borrowed_at.desc())
    )
    
    result = query.scalars().all()
    return result

@router.get("/active", response_model=List[schemas.BorrowInfo])
async def get_active_borrows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(role_required(Role.Librarian))):
    
    result = await db.execute(
        select(BorrowRecord)
        .options(
            selectinload(BorrowRecord.book).selectinload(Book.author),
            selectinload(BorrowRecord.user)
        )
        .where(BorrowRecord.returned_at.is_(None))
        .order_by(BorrowRecord.borrowed_at.desc())
        )
    
    borrows = result.scalars().all()
    
    return borrows