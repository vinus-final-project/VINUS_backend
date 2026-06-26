import uvicorn
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import async_engine

from app.routers.categories import router as categories_router
from app.routers.menus import router as menus_router
from app.routers.voice import router as voice_router


load_dotenv(dotenv_path=".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 테이블 생성은 alembic이 담당 (create_all 안 씀)

    # 시드 — seed.py 만들면 아래 주석 해제
    # from app.db.database import AsyncSessionLocal
    # from app.db.seed import run_all_seeds
    # async with AsyncSessionLocal() as session:
    #     async with session.begin():
    #         await run_all_seeds(session)

    yield
    await async_engine.dispose()


app = FastAPI(lifespan=lifespan)

# CORS — 키오스크 프론트(React/Vite) 주소. 실제 포트에 맞게 조정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:4173",
    ],
    allow_origin_regex=r"https://.*\.ngrok-free\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(categories_router)
app.include_router(menus_router)
app.include_router(voice_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,          # AI 서버가 8000이면 충돌 피해서 8081
        reload=True,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )