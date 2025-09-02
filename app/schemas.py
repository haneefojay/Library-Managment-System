from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, date
from .models import BookStatus, NotificationPreference

from .models import Role

class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr

class UserRegister(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: Role
    bio: Optional[str] = None
    birthdate: Optional[date] = None

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Role
    created_at: datetime
    notification_preference: NotificationPreference
    bio: Optional[str] = None
    birthdate: Optional[date] = None
    
    class Config:
        from_attributes = True

class UserPreferencesUpdate(BaseModel):
    notification_preference: NotificationPreference

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: int
    role: Role
    exp: int

class BookBase(BaseModel):
    isbn: Optional[str] = None
    title: str
    description: Optional[str] = None
    published_date: Optional[date] = None
    status: Optional[BookStatus] = None

class BookUpload(BookBase):
    pass

class BookUpdate(BaseModel):
    isbn: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    published_date: Optional[date] = None
    status: Optional[BookStatus] = None


class BookOut(BookBase):
    id: int
    author_name: str
    status: BookStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class BorrowBook(BaseModel):
    id: int
    book_id: int
    borrowed_at: datetime
    due_at: datetime
    returned_at: Optional[datetime]
    book: BookOut
    
    class Config:
        from_attributes = True


class BorrowInfo(BorrowBook):
    user: UserBase
    
    class Config:
        from_attributes = True


class AuthorInfo(UserOut):
    book: BookOut    
    class Config:
        from_attributes = True


class NotificationOut(BaseModel):
    id: int
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config: 
        from_attributes = True


class UnreadCount(BaseModel):
    unread: int


class BorrowerMini(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True


class BookMini(BaseModel):
    id: int
    title: str

    class Config:
        from_attributes = True


class OverdueBorrowOut(BaseModel):
    id: int
    borrowed_at: datetime
    due_at: datetime
    user: BorrowerMini
    book: BookMini

    class Config:
        from_attributes = True