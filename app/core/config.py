from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Loyiha konfiguratsiyasi. Barcha qiymatlar qat'iy ravishda faqat .env dan olinadi."""

    # Telegram Bot & Channels
    BOT_TOKEN: str = Field(..., description="Telegram Bot Token")
    ADMIN_IDS: List[int] = Field(..., description="Bosh administratorlar Telegram ID lari")
    MOVIE_CHANNEL_ID: Optional[int] = Field(default=None, description="Kino ombori (baza) kanali ID si (bot yangi kinolarni shu kanaldan oladi)")
    MAIN_CHANNEL_USERNAME: Optional[str] = Field(default=None, description="Asosiy ommaviy kanal username si (kino xabarida 'Kanalimiz: @...' deb chiqadi)")
    MOVIE_CHANNEL_USERNAME: Optional[str] = Field(default=None, description="Eski moslik uchun (MAIN_CHANNEL_USERNAME tavsiya etiladi)")

    # Database & Redis (Faqat .env dan olinadi, kodda hech qanday parol yo'q)
    DB_URL: str = Field(..., description="PostgreSQL ulanish URL manzili")
    REDIS_URL: str = Field(..., description="Redis ulanish URL manzili")

    # App Settings
    DEBUG: bool = Field(default=False)
    DEFAULT_LANGUAGE: str = Field(default="uz")
    LOG_LEVEL: str = Field(default="INFO")

    # Database Pool Settings
    DB_POOL_SIZE: int = Field(default=20)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_ECHO: bool = Field(default=False)

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, (int, float)):
            return [int(v)]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                import json
                return json.loads(v)
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    @property
    def main_channel_username(self) -> Optional[str]:
        """Asosiy kanal username si (MAIN_CHANNEL_USERNAME yoki eski MOVIE_CHANNEL_USERNAME)."""
        val = self.MAIN_CHANNEL_USERNAME or self.MOVIE_CHANNEL_USERNAME
        if val:
            return val.replace("@", "").strip()
        return None

    @property
    def database_url(self) -> str:
        """SQLAlchemy asyncpg drayveri bilan URL."""
        url = self.DB_URL.strip()
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if not url.startswith("postgresql+asyncpg://"):
            return f"postgresql+asyncpg://{url}"
        return url

    @property
    def redis_connection_url(self) -> str:
        """Redis ulanish URL manzili."""
        url = self.REDIS_URL.strip()
        if not url.startswith("redis://"):
            return f"redis://{url}"
        return url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
