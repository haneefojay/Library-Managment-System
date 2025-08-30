from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, null, text, ForeignKey, Enum as SAEnum, Date, DateTime, func, Text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
import enum
from .database import Base
from datetime import datetime, date
from typing import Optional, List


class Role(enum.Enum):
    Librarian = "Librarian"
    Author = "Author"
    Member = "Member"

class BookStatus(enum.Enum):
    Available = "Available"
    Borrowed = "Borrowed"
    Overdue = "overdue"

class NotificationType(str, enum.Enum):
    Reminder = "Reminder"
    Overdue = "Overdue"
    System = "System"


class NotificationPreference(str, enum.Enum):
    WEBSOCKET = "websocket"
    EMAIL = "email"
    ALL = "all"

class User(Base):
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer,primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(80), nullable=False)
    role: Mapped[Role] = mapped_column(SAEnum(Role), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    birthdate: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notification_preference: Mapped[NotificationPreference] = mapped_column(SAEnum(NotificationPreference), nullable=False, server_default=NotificationPreference.WEBSOCKET.value)
    
    books_uploaded: Mapped[List["Book"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
        )
    borrow_records: Mapped[List["BorrowRecord"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Book(Base):
    
    __tablename__ = "books"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    isbn: Mapped[str] = mapped_column(String(13), unique=True, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_date: Mapped[Optional[date]] = mapped_column(Date, server_default=func.now(), nullable=False)
    status: Mapped[BookStatus] = mapped_column(SAEnum(BookStatus), default=BookStatus.Available, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),nullable=False)
    
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    author: Mapped["User"] = relationship(back_populates="books_uploaded")
    borrow_records: Mapped[List["BorrowRecord"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    
    @hybrid_property
    def author_name(self):
        return self.author.name if self.author else None
    

class BorrowRecord(Base):
    
    __tablename__ = "borrow_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("books.id"), index=True, nullable=False)
    
    borrowed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    overdue_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    #Relationships
    user: Mapped["User"] = relationship(back_populates="borrow_records")
    book: Mapped["Book"] = relationship(back_populates="borrow_records")

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    message: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType), default=NotificationType.Reminder, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="notifications")
