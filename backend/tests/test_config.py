import pytest

from app.core.config import Settings, validate_production_configuration


def test_production_rejects_example_secret():
    settings = Settings(
        environment="production",
        secret_key="replace-with-a-long-random-secret-at-least-32-characters",
        github_webhook_secret="replace-with-a-long-random-secret",
        cors_origins="https://review.example.org",
    )
    with pytest.raises(ValueError, match="SECRET_KEY"):
        validate_production_configuration(settings)


def test_production_accepts_long_non_placeholder_secrets():
    settings = Settings(
        environment="production",
        secret_key="a" * 48,
        github_webhook_secret="b" * 48,
        cors_origins="https://review.example.org",
    )
    validate_production_configuration(settings)
