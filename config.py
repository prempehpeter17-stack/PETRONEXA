"""
PetroNexa Centralized Configuration Schema
"""
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = "PetroNexa Core Engine"
    environment: str = Field(default="development", env="ENVIRONMENT")
    secret_key: str = Field(default="SUPER_SECRET_PETRONEXA_KEY_CHANGE_IN_PROD", env="SECRET_KEY")
    database_url: str = Field(default="sqlite:///./petronexa.db", env="DATABASE_URL")
    
    # DB Pool Adjustments
    db_pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
