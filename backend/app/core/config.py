from functools import lru_cache
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Code Review Assistant"
    environment: str = "development"
    secret_key: str = "unsafe-development-key-change-before-production"
    access_token_expire_minutes: int = 30
    database_url: str = "sqlite+pysqlite:///./dev.db"
    cors_origins: str = "http://localhost:5173"
    max_code_chars: int = 50000
    ai_provider: str = "disabled"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-latest"
    github_webhook_secret: str = ""
    log_level: str = "INFO"

    @field_validator("ai_provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        value = value.lower().strip()
        if value not in {"disabled", "ollama", "openai", "anthropic"}:
            raise ValueError("AI_PROVIDER must be disabled, ollama, openai, or anthropic")
        return value

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.environment.lower() == "production":
            if self.secret_key == "unsafe-development-key-change-before-production" or len(self.secret_key) < 32:
                raise ValueError("Production requires a unique SECRET_KEY of at least 32 characters")
            if "*" in self.cors_origins:
                raise ValueError("Wildcard CORS origins are not allowed in production")
            if self.ai_provider == "openai" and not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when AI_PROVIDER=openai")
            if self.ai_provider == "anthropic" and not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required when AI_PROVIDER=anthropic")
            if not self.github_webhook_secret:
                # GitHub integration can be unused, but the webhook endpoint remains disabled until configured.
                pass
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_production_configuration(settings: Settings) -> None:
    """Fail fast on known unsafe production defaults."""
    if settings.environment.lower() == "production":
        secret = settings.secret_key.lower()
        if (
            len(settings.secret_key) < 32
            or settings.secret_key == "unsafe-development-key-change-before-production"
            or any(marker in secret for marker in ("replace", "change-me", "example", "placeholder"))
        ):
            raise ValueError("Production requires a unique, non-placeholder SECRET_KEY of at least 32 characters")
        webhook_secret = settings.github_webhook_secret.lower()
        if (
            len(settings.github_webhook_secret) < 32
            or any(marker in webhook_secret for marker in ("replace", "change-me", "example", "placeholder"))
        ):
            raise ValueError("Production requires a unique, non-placeholder GITHUB_WEBHOOK_SECRET of at least 32 characters")
        if not settings.cors_origin_list or "*" in settings.cors_origin_list:
            raise ValueError("Production CORS_ORIGINS must list explicit trusted origins")
