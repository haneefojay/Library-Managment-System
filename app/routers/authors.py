from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_
from typing import List, Optional

from app.database import get_db
from app.models import Book, User, Role
from .. import schemas
from ..dependencies import role_required, get_current_user

router = APIRouter(
    prefix="/users",
    tags=["Authors"]
)

@router.get("/authors", response_model=List[schemas.UserOut])
async def get_authors(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(role_required(Role.Member)),
    limit: int = 10, skip: int = 0,
    search: Optional[str] = Query(None, description="Search by name or email")
    ):
    
    query = select(User).where(User.role == Role.Author)
    
    if search:
        query = query.where(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    result = await db.execute(query.offset(skip).limit(limit))
    authors = result.scalars().all()    
    return authors


@router.get("/members", response_model=List[schemas.UserOut])
async def get_members(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(role_required(Role.Member)),
    limit: int = 10, skip: int = 0,
    search: Optional[str] = Query(None, description="Search by name or email")):
    
    query = select(User).where(User.role == Role.Member)
    
    if search:
        query = query.where(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    result = await db.execute(query.offset(skip).limit(limit))
    members = result.scalars().all()
    
    return members