"""Database connection management and initialization."""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, StaticPool
from contextlib import asynccontextmanager
import logging

from src.metrics.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: str = None, echo: bool = False):
        """
        Initialize database manager.
        
        Args:
            database_url: Database connection URL. Defaults to SQLite in ./data/metrics.db
            echo: Whether to echo SQL statements (for debugging)
        """
        if database_url is None:
            # Default to SQLite database
            db_dir = "./data"
            os.makedirs(db_dir, exist_ok=True)
            database_url = f"sqlite+aiosqlite:///{db_dir}/metrics.db"
        
        self.database_url = database_url
        
        # Configure engine based on database type
        engine_kwargs = {"echo": echo}
        
        if "sqlite" in database_url:
            # SQLite-specific configuration
            engine_kwargs["poolclass"] = StaticPool
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            # For other databases, use connection pooling
            engine_kwargs["poolclass"] = NullPool
            engine_kwargs["pool_pre_ping"] = True
        
        self.engine = create_async_engine(database_url, **engine_kwargs)
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info(f"Database manager initialized with URL: {database_url}")
    
    async def init_db(self):
        """Initialize database schema."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise
    
    async def close(self):
        """Close database connections."""
        await self.engine.dispose()
        logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session.
        
        Yields:
            AsyncSession: Database session
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database manager instance
_db_manager: DatabaseManager = None


def get_db_manager(database_url: str = None, echo: bool = False) -> DatabaseManager:
    """
    Get or create the global database manager instance.
    
    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL statements
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url, echo)
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database sessions.
    
    Yields:
        AsyncSession: Database session
    """
    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        yield session
