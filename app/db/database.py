from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import settings

#비동기 db연결 생성하는 함수(비동기적으로 db와 연결한다)
async_engine=create_async_engine(settings.db_url, echo=False)
# echo 모든 SQL 쿼리 콘솔 로그 여부

# 비동기 엔진과 연결된 세션사용하려고
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

# 동기 db연결 생성하는 함수 (동기적으로 db와 연결한다)
sync_engine=create_engine(settings.sync_db_url, pool_pre_ping=True)

# 기본 클래스 설정(Base)
Base=declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session