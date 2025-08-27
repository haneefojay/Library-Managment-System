from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from.config import settings
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from typing import AsyncIterator

load_dotenv()

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
    )

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session