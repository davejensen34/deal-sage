import pytest
from pydantic import ValidationError

from app.core.config import Settings


def secure_pilot(**overrides):
    values = {
        "deployment_environment":"pilot",
        "demo_mode":False,
        "auth_mode":"oidc",
        "session_secret":"a-unique-session-secret-at-least-32-characters",
        "session_cookie_secure":True,
        "web_app_url":"https://pilot.example.com",
        "google_redirect_uri":"https://pilot.example.com/api/auth/callback",
        "cors_origins":"https://pilot.example.com",
        "allowed_hosts":"pilot.example.com",
        "allowed_domains":"example.com",
        "database_url":"postgresql+psycopg://dealsage:unique-password@postgres/dealsage",
    }
    values.update(overrides)
    return Settings(**values)


def test_secure_pilot_configuration_is_accepted():
    settings = secure_pilot()
    assert settings.deployment_environment == "pilot"
    assert settings.allowed_host_set == {"pilot.example.com"}


def test_pilot_accepts_explicit_public_and_internal_health_hosts():
    settings = secure_pilot(allowed_hosts="pilot.example.com,api,127.0.0.1")
    assert settings.allowed_host_set == {"pilot.example.com", "api", "127.0.0.1"}


@pytest.mark.parametrize("override",[
    {"demo_mode":True},
    {"auth_mode":"demo"},
    {"session_secret":"too-short"},
    {"session_cookie_secure":False},
    {"web_app_url":"http://pilot.example.com"},
    {"google_redirect_uri":"http://pilot.example.com/api/auth/callback"},
    {"cors_origins":"http://pilot.example.com"},
    {"allowed_hosts":"*"},
    {"allowed_emails":"","allowed_domains":""},
    {"database_url":"postgresql+psycopg://dealsage:dealsage-local@postgres/dealsage"},
])
def test_insecure_pilot_configuration_fails_closed(override):
    with pytest.raises(ValidationError):
        secure_pilot(**override)
