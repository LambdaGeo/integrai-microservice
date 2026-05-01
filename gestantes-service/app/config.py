"""
Gestantes Service - Settings.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Gestantes Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8001

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "gestantes_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    USERS_SERVICE_URL: str = "http://localhost:8000"
    AVALIACOES_SERVICE_URL: str = "http://localhost:8002"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()

