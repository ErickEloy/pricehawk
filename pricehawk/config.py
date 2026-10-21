"""Configuração do PriceHawk usando pydantic-settings."""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = Field(default="sqlite:///pricehawk.db", alias="DATABASE_URL")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Alertas
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    discord_webhook_url: str = Field(default="", alias="DISCORD_WEBHOOK_URL")

    # White-label
    app_name: str = Field(default="PriceHawk", alias="APP_NAME")
    brand_color: str = Field(default="#2563eb", alias="BRAND_COLOR")
    primary_color: str = Field(default="#2563eb", alias="PRIMARY_COLOR")
    secondary_color: str = Field(default="#1e40af", alias="SECONDARY_COLOR")
    currency_symbol: str = Field(default="R$", alias="CURRENCY_SYMBOL")
    check_interval_minutes: int = Field(default=60, alias="CHECK_INTERVAL_MINUTES")


settings = Settings()