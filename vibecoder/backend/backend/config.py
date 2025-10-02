from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    backend_port: int = 8000
    database_url: str = "postgresql+psycopg2://vibecoder:vibecoder@localhost:5432/vibecoder"
    redis_url: str = "redis://localhost:6379/0"
    object_storage_endpoint: str = "https://s3.us-west-1.amazonaws.com"
    object_storage_bucket: str = "vibecoder"
    object_storage_access_key: str = "minioadmin"
    object_storage_secret_key: str = "minioadmin"
    preview_base_host: str = "preview.vibe.llmlab.io"
    github_token: str | None = None

    rate_limit_capacity: int = 200
    rate_limit_refill_seconds: int = 24 * 60 * 60

    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    clerk_publishable_key: str | None = None
    clerk_secret_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
