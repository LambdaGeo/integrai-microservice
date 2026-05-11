"""
Avaliacoes Service settings.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Avaliacoes Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8002

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "avaliacoes_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    USERS_SERVICE_URL: str = "http://localhost:8000"
    GESTANTES_SERVICE_URL: str = "http://localhost:8001"
    R_API_URL: str = "http://predition_api:8000/predict"

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
