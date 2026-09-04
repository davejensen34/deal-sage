from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
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
    google_redirect_uri: str = "http://localhost:3000/api/auth/callback"
    allowed_emails: str = ""
    allowed_domains: str = ""
    web_app_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:5173"
    evidence_storage_path: Path = Path("./data/evidence")
    model_provider: Literal["disabled", "openai", "anthropic"] = "disabled"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"
    ai_max_output_tokens: int = Field(default=1000, ge=1, le=4000)
    ai_request_timeout_seconds: float = Field(default=30, gt=0, le=120)
    ai_max_calls_per_case: int = Field(default=2, ge=1, le=4)
    ai_max_cost_cents_per_case: int = Field(default=25, ge=1, le=100)
    # Provider-side retention stays off until a reviewed policy explicitly changes it.
    ai_store_provider_responses: bool = False
    model_config = SettingsConfigDict(env_file="../../.env", extra="ignore")

    @field_validator("ai_store_provider_responses")
    @classmethod
    def require_provider_storage_off(cls, value: bool) -> bool:
        if value:
            raise ValueError("provider-side AI response storage must remain disabled")
        return value

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
