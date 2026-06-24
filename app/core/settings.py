import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 기본값은 비워두거나 기본 주소를 적어둡니다. (실제 값은 alembic/.env에서 덮어씌워짐)
    db_url: str = "postgresql+asyncpg://username:password@localhost:5432/dbname"
    sync_db_url: str = "postgresql://username:password@localhost:5432/dbname"
    
    app_name: str = "VINUS"
    secret_key: str = "super-secret-key-change-in-production"
    
    # ⭐ Alembic 폴더 안의 .env 파일을 가리키도록 상대 경로 설정
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "alembic", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()