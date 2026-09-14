from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import DATABASE_URL
from database.models import Base

# asyncpg requiere postgresql+asyncpg://...
_url = DATABASE_URL.replace('postgres://', 'postgresql+asyncpg://', 1) \
                   .replace('postgresql://', 'postgresql+asyncpg://', 1)

engine = create_async_engine(_url, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Crea las tablas si no existen."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
