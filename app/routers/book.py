from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models import Book, User, Role
from .. import schemas
from ..dependencies import role_required, get_current_user


router = APIRouter(
    prefix="/books",
    tags=["Books"]
)


@router.post("/", response_model=schemas.BookOut)
async def upload_book(book: schemas.BookUpload, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(role_required(Role.Author))):    
    
    new_book = Book(**book.dict(), author_id=current_user.id)
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    return new_book

@router.get("/", response_model=List[schemas.BookOut])
async def get_all_books(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    
    query = select(Book).options(selectinload(Book.author))
    result = await db.execute(query)
    books = result.scalars().unique().all()
    
    return books

@router.patch("/{id}", response_model=schemas.BookOut)
async def update_book(id: int, book_update: schemas.BookUpdate, db: AsyncSession = Depends(get_db), 
                    _: bool = Depends(role_required(Role.Author))):
    
    result = await db.execute(select(Book).where(Book.id == id))
    book = result.scalars().first()
    
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    for key, value in book_update.model_dump(exclude_unset=True).items():
        setattr(book, key, value)
        
    await db.commit()
    await db.refresh(book)
    return book

@router.delete("/{id}")
async def delete_book(id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(role_required(Role.Author))):
    
    query = await db.execute(select(Book).where(Book.id == id))
    result = query.scalars().first()
    
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    await db.delete(result)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    