"""Lesson 80: local configuration from environment variables or .env."""
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8-sig", extra="ignore"
    )
    database_hostname: str = "localhost"
    database_port: int = 5432
    database_name: str = "fastapi"
    database_username: str = "postgres"
    database_password: SecretStr = SecretStr("")
    secret_key: SecretStr = Field(min_length=32)
    algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)
    cors_origins: list[str] = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ])

    @property
    def sqlalchemy_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg", username=self.database_username,
            password=self.database_password.get_secret_value(),
            host=self.database_hostname, port=self.database_port,
            database=self.database_name,
        )


settings = Settings()
