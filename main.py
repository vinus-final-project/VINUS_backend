import uvicorn
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, async_engine

from app.db.models.allergies import ModelsAllergies
from app.db.models.categories import ModelsCategories
from app.db.models.ingredients import ModelsIngredients
from app.db.models.menuAllergies import ModelsMenuAllergies
from app.db.models.menuIngredients import ModelsMenuIngredients
from app.db.models.menus import ModelsMenus
from app.db.models.optionGroups import ModelsOptionGroups
from app.db.models.options import ModelsOptions
from app.db.models.orders import ModelsOrders
from app.db.models.orderMenus import ModelsOrderMenus
from app.db.models.orderMenuOptions import ModelsOrderMenuOptions
from app.db.models.voice import ModelsVoice
from app.db.models.sessionLogs import ModelsSessionLogs
from app.db.models.sessions import ModelsSessions



from app.routers.categories import router as categories_router
from app.routers.menus import router as menus_router
from app.routers.voice import router as voice_router
from app.routers import paymentRouter


load_dotenv(dotenv_path=".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 시드 — seed.py 만들면 아래 주석 해제
    from app.db.database import AsyncSessionLocal
    from app.db.seed import run_all_seeds
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await run_all_seeds(session)

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
app.include_router(paymentRouter.router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,          # AI 서버가 8000이면 충돌 피해서 8081
        reload=True,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )