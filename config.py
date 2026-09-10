"""
Central configuration management using Pydantic Settings.
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr


class Settings(BaseSettings):
    app_name: str = "PetroNexa API"
    app_version: str = "2.0.0"
    secret_key: SecretStr = Field(default="CHANGE_THIS_IN_PRODUCTION_SECRET_KEY_12345")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./petronexa.db")
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Security
    allowed_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    @property
    def origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
