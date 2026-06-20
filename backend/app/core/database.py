from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from loguru import logger
from typing import AsyncGenerator

from app.core.config import settings
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Async engine creation
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=15,
    max_overflow=25
)

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection yield for FastAPI request scope database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Checks PostGIS extension, registers schemas, and establishes pools."""
    logger.info("Initializing database session pool...")
    try:
        # Check PostGIS extension
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            logger.info("PostGIS extension verified.")
            
            # Create all tables if they don't exist
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables initialized.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise e

async def close_db():
    """Disposes engine connection pools on shutdown."""
    logger.info("Disposing database connection pool...")
    await engine.dispose()
    logger.info("Database pool disposed.")
