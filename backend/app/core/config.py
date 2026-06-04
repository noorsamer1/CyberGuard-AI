from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CyberGuard AI"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql://cyberguard:cyberguard@localhost:5432/cyberguard"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    secret_key: str = "change-me"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:3001,http://127.0.0.1:3001,"
        "http://localhost:3002,http://127.0.0.1:3002"
    )
    # Optional regex for LAN dev (e.g. http://192.168.1.9:3001). Leave empty in production.
    cors_origin_regex: str = (
        r"^http://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r":(3000|3001|3002|3003)$"
    )

    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    ai_detection_enabled: bool = True
    ai_detection_min_confidence: float = 0.85
    ai_detection_max_events_per_task: int = 20

    reports_dir: str = "./data/reports"

    range_enabled: bool = True
    range_target_url: str = "http://range-target:8088"
    range_public_url: str = "http://127.0.0.1:8088"
    range_shared_secret: str = "dev-range-secret-change-me"

    correlation_enabled: bool = True
    correlation_window_minutes: int = 30

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host.strip() and self.smtp_from.strip())

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
