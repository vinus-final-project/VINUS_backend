import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, async_engine, AsyncSessionLocal
# from app.db.seed import run_all_seeds
from fastapi.concurrency import asynccontextmanager

# from app.middleware.token_refresh import RefreshTokenMiddleware

# from app.routers.attendance import router as attendance_router
# from app.routers.category import router as category_router
# from app.routers.cloth import router as cloth_router
# from app.routers.friend_todo_view import router as friend_todo_view_router
# from app.routers.friend import router as friend_router
# from app.routers.img import router as img_router
# from app.routers.music import router as music_router
# from app.routers.notification import router as notification_router
# from app.routers.pw_history import router as pw_history_router
# from app.routers.report import router as report_router
# from app.routers.todo import router as todo_router
# from app.routers.user import router as user_router

load_dotenv(dotenv_path=".env")

@asynccontextmanager
async def lifespan(app:FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # async with AsyncSessionLocal() as session:
    #     async with session.begin():
    #         await run_all_seeds(session)
    yield
    await async_engine.dispose()

app=FastAPI(lifespan=lifespan)

# app.add_middleware(RefreshTokenMiddleware)

# 요청 허용 관련 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https://.*\.ngrok-free\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(attendance_router)
# app.include_router(category_router)
# app.include_router(cloth_router)
# app.include_router(friend_router)
# app.include_router(friend_todo_view_router)
# app.include_router(friend_router)
# app.include_router(img_router)
# app.include_router(music_router)
# app.include_router(notification_router)
# app.include_router(pw_history_router)
# app.include_router(report_router)
# app.include_router(todo_router)
# app.include_router(user_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8081, reload=True,
                proxy_headers=True, forwarded_allow_ips="*")