from sqlalchemy import select

from app.auth import routes as auth_routes
from app.auth.service import email_permitted, provision_user
from app.core.config import Settings
from app.domain.models import AuditEvent, User


def test_demo_identity_requires_no_external_provider(client):
    response=client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["provider"] == "demo"
    assert response.json()["display_name"] == "Morgan Lee"


def test_allowlist_supports_exact_email_or_domain():
    settings=Settings(allowed_emails="pilot@example.com",allowed_domains="allowed.test")
    assert email_permitted("pilot@example.com",settings)
    assert email_permitted("someone@allowed.test",settings)
    assert not email_permitted("outsider@example.net",settings)


def test_jit_user_uses_provider_subject_not_email(override_db_session):
    settings=Settings(allowed_domains="example.com")
    first=provision_user(override_db_session,"google",{"sub":"stable-123","email":"pilot@example.com","name":"Pilot One"},settings)
    second=provision_user(override_db_session,"google",{"sub":"stable-123","email":"renamed@example.com","name":"Pilot Renamed"},settings)
    assert first.id == second.id
    assert override_db_session.scalars(select(User)).all().__len__() == 1
    assert second.email == "renamed@example.com"


def test_authenticated_callback_session_and_audit_attribution(client,monkeypatch,override_db_session):
    class FakeClient:
        async def authorize_access_token(self,request):
            return {"userinfo":{"sub":"google-subject","email":"pilot@example.com","email_verified":True,"name":"Pilot Analyst"}}
    original_mode=auth_routes.settings.auth_mode
    auth_routes.settings.auth_mode="oidc"
    monkeypatch.setattr(auth_routes.oauth,"create_client",lambda name:FakeClient())
    try:
        callback=client.get("/api/auth/callback",follow_redirects=False)
        assert callback.status_code == 307
        assert client.get("/api/auth/me").json()["display_name"] == "Pilot Analyst"
        client.patch("/api/candidates/2/status",json={"status":"watchlist","reason":"Pilot review","note":"Keep under review."})
        event=override_db_session.scalar(select(AuditEvent).where(AuditEvent.action == "status_changed").order_by(AuditEvent.id.desc()))
        assert event.actor == "Pilot Analyst"
        assert event.user_id is not None
        assert client.post("/api/auth/logout").json()["status"] == "signed_out"
        assert client.get("/api/auth/me").status_code == 401
        assert client.get("/api/auth/callback",follow_redirects=False).status_code == 307
        assert client.get("/api/auth/me").json()["display_name"] == "Pilot Analyst"
    finally:
        auth_routes.settings.auth_mode=original_mode


def test_auth_config_never_exposes_credentials(client):
    data=client.get("/api/auth/config").json()
    assert data == {"mode":"demo","provider":"demo","configured":True,"redirect_uri":None}
    assert "secret" not in str(data).lower()
