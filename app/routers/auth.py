#from __future__ import annotations


from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.concurrency import run_in_threadpool

from app.database import get_db
from app.models import User
from app.schemas import UserOut,Token
from app.utils import verify_password
from app.oauth2 import create_access_token
from app.dependencies import get_current_user
from app.core.limiter import limiter


router = APIRouter(
    tags=["Authentication"]
)


@router.post("/login", response_model=Token)
@limiter.limit("3/minute")
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    ):
    
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    token_data = {"sub": str(user.id), "role": user.role.value}
    token = create_access_token(token_data)
    return Token(access_token=token)

