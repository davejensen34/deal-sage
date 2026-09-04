from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DealSage"
    database_url: str = "sqlite:///./dealsage.db"
    demo_mode: bool = True
    demo_analyst_name: str = "Morgan Lee"
    cors_origins: str = "http://localhost:5173"
    evidence_storage_path: Path = Path("./data/evidence")
    model_provider: str = "disabled"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"
    model_config = SettingsConfigDict(env_file="../../.env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
