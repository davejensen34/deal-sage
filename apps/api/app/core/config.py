from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DealSage"
    database_url: str = "sqlite:///./dealsage.db"
    demo_mode: bool = True
    demo_analyst_name: str = "Morgan Lee"
    auth_mode: Literal["demo", "oidc"] = "demo"
    session_secret: str = "development-only-change-me"
    session_cookie_secure: bool = False
    oidc_provider: str = "google"
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8000/api/auth/callback"
    allowed_emails: str = ""
    allowed_domains: str = ""
    web_app_url: str = "http://localhost:5173"
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

    @property
    def allowed_email_set(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_emails.split(",") if item.strip()}

    @property
    def allowed_domain_set(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_domains.split(",") if item.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
