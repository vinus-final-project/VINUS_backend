from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

'''BaseSettings 환경변수 기반 설정 관리 클래스 (DB, AI 서버)'''


class CoreSettings(BaseSettings):
    # ===== 설정(Config) =====
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,      # 환경변수 대소문자 구분
        extra="allow",
        populate_by_name=True,
    )

    # ===== 변수 선언 =====
    # DB
    db_user: str = Field(..., alias="DB_USER")
    db_password: str = Field(..., alias="DB_PASSWORD")
    db_host: str = Field("localhost", alias="DB_HOST")
    db_port: int = Field(3306, alias="DB_PORT")
    db_name: str = Field(..., alias="DB_NAME")

    # AI 서버
    ai_server_url: str = Field("http://localhost:8000", alias="AI_SERVER_URL")

    # ===== 함수(프로퍼티) 정의 =====
    # DB 접속 정보 (user:password@host:port/name)
    @property
    def db_credentials(self) -> str:
        return f"{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # 비동기 DB URL
    @property
    def db_url(self) -> str:
        return f"mysql+asyncmy://{self.db_credentials}"

    # 동기 DB URL
    @property
    def sync_db_url(self) -> str:
        return f"mysql+pymysql://{self.db_credentials}"


settings = CoreSettings()