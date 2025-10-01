from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    backend_port: int = 8000
    database_url: str = "sqlite:///./vibecoder.db"
    redis_url: str = "redis://localhost:6379/0"
    object_storage_endpoint: str = "http://localhost:9000"
    object_storage_bucket: str = "vibecoder"
    object_storage_access_key: str = "minioadmin"
    object_storage_secret_key: str = "minioadmin"
    preview_base_host: str = "preview.localtest.me"
    github_token: str | None = None

    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    clerk_publishable_key: str | None = None
    clerk_secret_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
