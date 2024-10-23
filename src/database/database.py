# database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings
from sqlalchemy.ext.declarative import declarative_base
from contextlib import asynccontextmanager
# Create the Base class to be used by models
Base = declarative_base()
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def get_db() -> AsyncSession:
    session: AsyncSession = async_session()
    try:
        yield session
    finally:
        await session.close()
