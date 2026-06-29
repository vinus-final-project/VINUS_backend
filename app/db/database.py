from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings import settings

# 비동기 엔진
async_engine = create_async_engine(settings.db_url, echo=False)

# 비동기 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)

# 동기 엔진 (alembic 마이그레이션용)
sync_engine = create_engine(settings.sync_db_url, pool_pre_ping=True)


# 모든 ORM 모델의 기본 클래스
class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session