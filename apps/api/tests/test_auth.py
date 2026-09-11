from sqlalchemy import select

from app.auth import routes as auth_routes
from app.auth.service import Identity, ROLE_PERMISSIONS, email_permitted, provision_user
from app.core.config import Settings
from app.domain.models import AuditEvent, User
from app.main import app, settings as app_settings
from app.ops.users import update_user_access


def test_demo_identity_requires_no_external_provider(client):
    response=client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["provider"] == "demo"
    assert response.json()["display_name"] == "Morgan Lee"
    assert response.json()["role"] == "demo"


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
    assert second.role == "viewer"


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
        assert client.get("/api/auth/me").json()["role"] == "viewer"
        user=override_db_session.scalar(select(User).where(User.subject == "google-subject"))
        user.role="analyst"; override_db_session.commit()
        client.patch("/api/candidates/2/status",headers={"X-DealSage-CSRF":"1"},json={"status":"watchlist","reason":"Pilot review","note":"Keep under review."})
        event=override_db_session.scalar(select(AuditEvent).where(AuditEvent.action == "status_changed").order_by(AuditEvent.id.desc()))
        assert event.actor == "Pilot Analyst"
        assert event.user_id is not None
        assert client.post("/api/auth/logout",headers={"X-DealSage-CSRF":"1"}).json()["status"] == "signed_out"
        assert client.get("/api/auth/me").status_code == 401
        assert client.get("/api/auth/callback",follow_redirects=False).status_code == 307
        assert client.get("/api/auth/me").json()["display_name"] == "Pilot Analyst"
    finally:
        auth_routes.settings.auth_mode=original_mode


def test_auth_config_never_exposes_credentials(client):
    data=client.get("/api/auth/config").json()
    assert data == {"mode":"demo","provider":"demo","configured":True,"redirect_uri":None}
    assert "secret" not in str(data).lower()


def test_viewer_denial_is_audited_without_request_body(client, monkeypatch, override_db_session):
    viewer = Identity(None, "google", "viewer-subject", "viewer@example.com", "Read Only", role="viewer")
    # FastAPI dependencies are closure instances, so override the shared identity
    # dependency instead and let the real permission dependency produce the audit.
    from app.auth.service import current_identity
    app.dependency_overrides[current_identity] = lambda: viewer
    try:
        response = client.patch("/api/candidates/2/status", json={"status":"rejected","reason":"secret-reason","note":"secret-note"})
        assert response.status_code == 403
        event = override_db_session.scalar(select(AuditEvent).where(AuditEvent.action == "authorization_denied").order_by(AuditEvent.id.desc()))
        assert event is not None
        assert "permission=review" in event.detail
        assert "secret" not in event.detail
    finally:
        app.dependency_overrides.pop(current_identity, None)


def test_oidc_mutations_require_same_origin_header(client):
    original_mode = app_settings.auth_mode
    app_settings.auth_mode = "oidc"
    try:
        response = client.patch("/api/candidates/2/status", json={"status":"watchlist","reason":"test","note":"test"})
        assert response.status_code == 403
        assert response.json()["detail"] == "Missing same-origin mutation signal"
    finally:
        app_settings.auth_mode = original_mode


def test_operator_can_change_role_and_deactivate_user(override_db_session):
    user = User(provider="google",subject="access-subject",email="access@example.com",display_name="Access User",role="viewer")
    override_db_session.add(user); override_db_session.commit()
    changed = update_user_access(override_db_session,provider="google",subject="access-subject",role="operator",active=False)
    assert changed.role == "operator"
    assert changed.active is False
    event = override_db_session.scalar(select(AuditEvent).where(AuditEvent.action == "user_access_changed").order_by(AuditEvent.id.desc()))
    assert event.before_state == {"role":"viewer","active":True}
    assert event.after_state == {"role":"operator","active":False}


def test_cost_permissions_begin_at_operator_role():
    assert "operate_sources" not in ROLE_PERMISSIONS["analyst"]
    assert "execute_ai" not in ROLE_PERMISSIONS["analyst"]
    assert {"operate_sources", "execute_ai"}.issubset(ROLE_PERMISSIONS["operator"])
    assert "administer_users" in ROLE_PERMISSIONS["administrator"]
