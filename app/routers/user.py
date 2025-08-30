from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import User, Role
from ..schemas import UserRegister, UserOut, UserPreferencesUpdate
from ..utils import hash_password
from ..dependencies import get_current_user

router = APIRouter(
    tags=["Authentication"]
)

@router.post("/register", response_model=UserOut, status_code=201)
async def register_user(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    # Only allow Author or Member to self-register
    if payload.role not in (Role.Author, Role.Member):
        raise HTTPException(status_code=403, detail="Only Authors or Members can self-register")


    # Check if email exists
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")


    user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        role=payload.role,
        bio=payload.bio,
        birthdate=payload.birthdate
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.patch("/me/preference", response_model=UserOut)
async def update_my_preference(
    preferences: UserPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    
    current_user.notification_preference = preferences.notification_preference
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user