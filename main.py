import asyncio
from datetime import datetime

import uvicorn
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# ⚠ .env 로드는 반드시 app 모듈 import 보다 먼저 실행되어야 한다.
#    whisperService 가 import 시점에 os.getenv("STT_DEVICE") 를 읽으므로,
#    이 줄이 아래 import 들보다 늦으면 .env 의 STT_DEVICE 설정이 무시된다.
load_dotenv(dotenv_path=".env")

from fastapi import FastAPI, Request  # 👈 Request 임포트 추가
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware  # 👈 BaseHTTPMiddleware 임포트 추가
from starlette.responses import Response  # 👈 Response 임포트 추가

from app.core.constants import (
    SESSION_TTL_SECONDS,
    SESSION_SWEEP_INTERVAL_SECONDS,
)
from app.controllers.systemController import SystemController
from app.memory.session.sessionMemory import SessionMemory


from app.db.database import Base, async_engine

from app.db.models.allergies import Allergies
from app.db.models.categories import Categories
from app.db.models.ingredients import Ingredients
from app.db.models.menuAllergies import MenuAllergies
from app.db.models.menuIngredients import MenuIngredients
from app.db.models.menus import Menus
from app.db.models.optionGroups import OptionGroups
from app.db.models.options import Options
from app.db.models.orders import Orders
from app.db.models.orderMenus import OrderMenus
from app.db.models.orderMenuOptions import OrderMenuOptions
from app.db.models.voice import Voice
from app.db.models.sessionLogs import SessionLogs
from app.db.models.sessions import Sessions



from app.routers.categories import router as categories_router
from app.routers.menus import router as menus_router
from app.routers.voice import router as voice_router
from app.routers.payment import router as payment_router
from app.routers.session import router as session_router
from app.routers.order import router as order_router
from app.routers.cart import router as cart_router
from app.routers import websocket


# ──────────────────────────────────────────────────────────────
# 세션 TTL 스위퍼 — 마지막 활동 후 TTL 경과한 세션 자동 만료
#    (EXPIRE_SESSION 과 동일하게 상태 표기 후 메모리에서 제거)
# ──────────────────────────────────────────────────────────────
async def _sweep_expired_sessions():
    while True:
        await asyncio.sleep(SESSION_SWEEP_INTERVAL_SECONDS)
        now = datetime.now()
        # 순회 중 삭제 대비 — 목록 복사
        for session in list(SessionMemory.sessions.values()):
            idle = (now - session.last_active_at).total_seconds()
            if idle >= SESSION_TTL_SECONDS:
                await SystemController.expire_session_controllers_systemController(
                    session,
                )
                print(f"[TTL] 세션 만료 처리: {session.session_id} (유휴 {int(idle)}초)")


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

    # 세션 TTL 스위퍼 시작
    sweeper_task = asyncio.create_task(_sweep_expired_sessions())

    # Whisper 모델 웜업 — 실제 서버 프로세스에서만 1회 로드
    #    (import 시점 로드였을 때 --reload 의 reloader 프로세스까지
    #     이중 로드되던 문제 방지. 첫 발화 지연도 제거)
    from app.ai.stt.whisperService import WhisperService
    await asyncio.to_thread(WhisperService.get_model_stt_whisper)

    yield

    # 스위퍼 정지 후 엔진 정리
    sweeper_task.cancel()
    await async_engine.dispose()


app = FastAPI(lifespan=lifespan)


# 1. 안전한 커스텀 CORS 주입 미들웨어 (에러가 나도 강제로 헤더를 붙여줌)
class SuperCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # OPTIONS 요청(프리플라이트)은 바로 200 OK로 빠르게 통과시킴
        if request.method == "OPTIONS":
            response = Response(status_code=200)
        else:
            response = await call_next(request)
            
        # 모든 응답에 폰(웹뷰) 주소와 커스텀 헤더를 강제로 주입
        response.headers["Access-Control-Allow-Origin"] = "https://localhost"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, Origin, X-Requested-With, ngrok-skip-browser-warning"
        return response

# 커스텀 미들웨어를 가장 먼저 실행되도록 등록
app.add_middleware(SuperCORSMiddleware)


# CORS — 키오스크 프론트(React/Vite) 주소. 실제 포트에 맞게 조정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://localhost",
        "http://localhost",
        "https://localhost:3000",
        "http://localhost:3000",
        "https://localhost:5173",
        "http://localhost:5173",
        "https://localhost:4173",
        "http://localhost:4173",
        "https://3.38.240.185",
        "http://3.38.240.185",
        "https://voice-in-us.com",
        "http://voice-in-us.com",
        "https://api.voice-in-us.com:8081",  # 추가
        "https://api.voice-in-us.com",       # 추가
        "http://api.voice-in-us.com:8081",  # 추가
        "http://api.voice-in-us.com",       # 추가
        
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
app.include_router(payment_router)
app.include_router(session_router)
app.include_router(order_router)
app.include_router(cart_router)
app.include_router(websocket.router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,          # AI 서버가 8000이면 충돌 피해서 8081
        reload=True,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
