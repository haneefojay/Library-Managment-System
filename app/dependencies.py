from __future__ import annotations


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError


from app.database import get_db
from app.models import User, Role
from app.schemas import TokenPayload
from app.oauth2 import SECRET_KEY, ALGORITHM


# For Swagger login flow (tokenUrl must match our login endpoint)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        data = TokenPayload(**payload)
    except (JWTError, ValueError):
        raise credentials_exception


    result = await db.execute(select(User).where(User.id == data.sub))
    user = result.scalar_one_or_none()
    if not user:
        raise credentials_exception
    return user


def role_required(*roles: Role):
    async def _role_guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return _role_guard