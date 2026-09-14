from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import DATABASE_URL
from database.models import Base

engine = None
AsyncSessionLocal = None


def _build_url() -> str:
    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL no configurada. "
            "Agrégala en Railway Variables (Postgres → Variables → DATABASE_URL)."
        )
    url = DATABASE_URL
    url = url.replace('postgres://', 'postgresql+asyncpg://', 1)
    url = url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    return url


async def init_db() -> None:
    """Inicializa el engine y crea las tablas si no existen."""
    global engine, AsyncSessionLocal

    url = _build_url()

    engine = create_async_engine(url, echo=False, pool_pre_ping=True)
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
