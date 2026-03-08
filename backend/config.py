from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    anthropic_api_key: str = Field(...)
    claude_model: str = Field(default="claude-sonnet-4-20250514")
    claude_max_tokens: int = Field(default=2000)
    claude_temperature: float = Field(default=0.3)

    bdl_base_url: str = Field(default="https://api.balldontlie.io/v1")
    bdl_api_key: str = Field(default="")
    bdl_request_timeout: float = Field(default=20.0)

    cache_dir: str = Field(default=".pivot_cache")
    cache_ttl_seconds: int = Field(default=86400)
    cache_stats_ttl_seconds: int = Field(default=3600)

    max_concurrent_llm_calls: int = Field(default=5)
    max_concurrent_bdl_calls: int = Field(default=10)

    retry_max_attempts: int = Field(default=4)
    retry_min_wait_seconds: float = Field(default=1.0)
    retry_max_wait_seconds: float = Field(default=60.0)

    @field_validator("anthropic_api_key")
    @classmethod
    def key_must_exist(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("ANTHROPIC_API_KEY missing from .env")
        return v.strip()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()