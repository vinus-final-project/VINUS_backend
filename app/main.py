from fastapi import FastAPI
import uvicorn
from app.db.routers import categories, stores
from app.db.routers import menus  # 우리가 만든 라우터들 import

app = FastAPI(
    title="VINUS Kiosk Backend API",
    description="카테고리, 가게, 메뉴 API 테스트 문서입니다.",
    version="1.0.0"
)

# 라우터 등록
app.include_router(categories.router)
app.include_router(stores.router)
app.include_router(menus.router)

@app.get("/")
async def root():
    return {"message": "VINUS 백엔드 서버가 정상 구동 중입니다!"}

if __name__ == "__main__":
    # 로컬에서 터미널 없이 스크립트로 바로 실행할 수 있도록 설정
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)