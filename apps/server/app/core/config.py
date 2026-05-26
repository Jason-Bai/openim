from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./openim.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-secret"
    jwt_expires_in: str = "7d"
    bot_gateway_public_url: str = "ws://localhost:8080/bot-gateway/ws"
    plugin_install_command: str = "npm install ./openim-openclaw-bot-plugin-0.1.0.tgz"
    plugin_version: str = "0.1.0"
    auth_timeout_seconds: int = 15
    heartbeat_ttl_seconds: int = 100
    heartbeat_timeout_seconds: int = 90

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

