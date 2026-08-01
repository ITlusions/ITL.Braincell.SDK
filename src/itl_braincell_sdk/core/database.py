import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator, AsyncGenerator

from .config import get_settings
from .models import Base

settings = get_settings()

# Synchronous engine for sync operations
sync_engine = create_engine(
    settings.database_url.replace("postgresql://", "postgresql://") 
    if "postgresql://" in settings.database_url 
    else settings.database_url,
    poolclass=NullPool if settings.debug else None,
    echo=settings.debug,
)

# Asynchronous engine for async operations
async_engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    if "postgresql://" in settings.database_url
    else settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

# Session factories
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get synchronous database session"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get async database session"""
    async with AsyncSessionLocal() as session:
        yield session


def get_async_engine():
    """Get async engine for migrations and direct queries"""
    return async_engine


def get_session_factory():
    """Get async session factory"""
    return AsyncSessionLocal


def init_db():
    """Initialize database tables (synchronous)"""
    Base.metadata.create_all(bind=sync_engine)


def drop_db():
    """Drop all tables (use with caution)"""
    Base.metadata.drop_all(bind=sync_engine)
