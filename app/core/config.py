import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Project Management Platform"
    database_url: str = Field(
        default_factory=lambda: "sqlite:////tmp/jira_pm_demo.db" if os.getenv("VERCEL") else "sqlite:///./local.db"
    )
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60 * 24
    auto_create_tables: bool = bool(os.getenv("VERCEL"))
    seed_on_startup: bool = bool(os.getenv("VERCEL"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
