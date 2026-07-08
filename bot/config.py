"""Application configuration loaded from environment variables.

Uses Pydantic Settings to validate and type-check all configuration
at startup. If a required variable is missing, the application will
fail fast with a clear error message.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Discord bot configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Discord ---
    discord_token: str = Field(
        ...,
        description="Discord bot token from the Developer Portal.",
    )
    discord_dev_guild_id: int | None = Field(
        default=None,
        description="Guild ID for instant slash-command sync during development.",
    )
    bot_owner_ids: list[int] = Field(
        default_factory=list,
        description="Comma-separated list of Discord user IDs who are bot owners.",
    )

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/discord_bot",
        description="Async SQLAlchemy database URL.",
    )
    database_echo: bool = Field(
        default=False,
        description="Echo SQL queries to the log (noisy, only for debugging).",
    )
    database_pool_size: int = Field(
        default=20,
        ge=5,
        le=100,
        description="Database connection pool size.",
    )
    database_max_overflow: int = Field(
        default=10,
        ge=0,
        le=50,
        description="Max overflow connections beyond pool_size.",
    )
    database_pool_recycle: int = Field(
        default=3600,
        description="Recycle connections after this many seconds.",
    )

    # --- Redis ---
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL.",
    )
    redis_max_connections: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Maximum Redis connections.",
    )

    # --- Celery ---
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery message broker URL.",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL.",
    )

    # --- API ---
    api_host: str = Field(default="0.0.0.0", description="API server bind host.")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API server bind port.")
    api_workers: int = Field(default=4, ge=1, le=16, description="API worker count.")

    # --- Dashboard ---
    dashboard_url: str = Field(
        default="http://localhost:3000",
        description="Dashboard frontend URL (for CORS and redirects).",
    )

    # --- OAuth2 ---
    oauth2_client_id: str = Field(
        default="",
        description="Discord OAuth2 application client ID.",
    )
    oauth2_client_secret: str = Field(
        default="",
        description="Discord OAuth2 application client secret.",
    )
    oauth2_redirect_uri: str = Field(
        default="http://localhost:3000/api/auth/callback",
        description="OAuth2 callback redirect URI.",
    )

    # --- JWT ---
    jwt_secret_key: str = Field(
        default="change_this_to_a_random_64_char_hex_string",
        description="Secret key for signing JWT tokens.",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm.")
    jwt_access_token_expire_minutes: int = Field(
        default=60,
        ge=5,
        le=1440,
        description="Access token expiration in minutes.",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Refresh token expiration in days.",
    )

    # --- AI ---
    ai_provider: Literal["gemini", "openai", "none"] = Field(
        default="none",
        description="Active AI provider.",
    )
    gemini_api_key: str = Field(default="", description="Google Gemini API key.")
    openai_api_key: str = Field(default="", description="OpenAI API key.")

    # --- Logging ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Application log level.",
    )
    log_format: Literal["json", "console"] = Field(
        default="console",
        description="Log output format: 'json' for production, 'console' for dev.",
    )

    # --- Environment ---
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment.",
    )
    debug: bool = Field(default=True, description="Enable debug mode.")

    # --- Sentry ---
    sentry_dsn: str = Field(default="", description="Sentry DSN for error tracking.")

    @field_validator("bot_owner_ids", mode="before")
    @classmethod
    def parse_owner_ids(cls, value: str | list[int]) -> list[int]:
        """Parse comma-separated owner IDs string into a list of ints."""
        if isinstance(value, str):
            if not value.strip():
                return []
            return [int(x.strip()) for x in value.split(",") if x.strip()]
        return value

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


@lru_cache(maxsize=1)
def get_settings() -> BotSettings:
    """Get cached application settings.

    Uses lru_cache to ensure settings are loaded only once from disk.
    Call this function anywhere you need access to configuration.

    Returns:
        BotSettings: Validated application settings.
    """
    return BotSettings()
