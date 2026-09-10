"""Central application configuration for PetroNexa."""
from functools import lru_cache
import secrets
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PetroNexa"
    app_version: str = "1.0.0"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./petronexa.db"
    jwt_secret_key: str | None = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    cors_origins: str = "http://localhost:8501,http://localhost:3000,http://localhost:8080"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "testing", "production"}
        v_clean = v.strip().lower()
        if v_clean not in allowed:
            raise ValueError(f"environment must be one of {allowed}, got '{v}'")
        return v_clean

    @property
    def origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    @property
    def secret(self) -> str:
        if self.jwt_secret_key:
            return self.jwt_secret_key
        if self.environment == "production":
            raise RuntimeError("JWT_SECRET_KEY must be set in production.")
        # Ephemeral development-only secret; never use this for deployed production data.
        return _DEV_SECRET


_DEV_SECRET = secrets.token_urlsafe(48)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
