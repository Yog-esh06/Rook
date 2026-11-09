from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings with a safe local SQLite default."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Rook Control Plane"
    environment: str = "local"
    database_url: str = "sqlite:///./rook.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_enabled: bool = False
    demo_mode: bool = True
    demo_observation_seconds: float = Field(default=0.8, ge=0.05, le=60)
    demo_sample_count: int = Field(default=200, ge=20, le=5000)
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    log_level: str = "INFO"
    auth_enabled: bool = False
    viewer_role_header: str = "X-Rook-Role"
    release_stages: str = "10,25,50,100"
    request_timeout_seconds: float = Field(default=5.0, ge=0.1, le=60)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def rollout_stages(self) -> list[int]:
        values = [int(value.strip()) for value in self.release_stages.split(",") if value.strip()]
        if not values or values[-1] != 100:
            values.append(100)
        return sorted(set(max(1, min(100, value)) for value in values))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
