from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.service import Identity, current_identity, provision_user
from app.core.config import get_settings
from app.core.database import get_db

router = APIRouter(prefix="/api/auth", tags=["authentication"])
settings = get_settings()
oauth = OAuth()
if settings.auth_mode == "oidc" and settings.google_client_id and settings.google_client_secret:
    oauth.register(name="google",client_id=settings.google_client_id,client_secret=settings.google_client_secret,server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",client_kwargs={"scope":"openid email profile","code_challenge_method":"S256"})


@router.get("/config")
def auth_config():
    """Expose only non-secret readiness data needed to diagnose local sign-in."""
    return {"mode":settings.auth_mode,"provider":settings.oidc_provider if settings.auth_mode == "oidc" else "demo","configured":bool(settings.google_client_id and settings.google_client_secret) if settings.auth_mode == "oidc" else True,"redirect_uri":settings.google_redirect_uri if settings.auth_mode == "oidc" else None}


@router.get("/me")
def me(identity: Identity = Depends(current_identity)):
    return identity.__dict__


@router.get("/login")
async def login(request: Request):
    if settings.auth_mode == "demo": return RedirectResponse(settings.web_app_url)
    client = oauth.create_client(settings.oidc_provider)
    if not client: raise HTTPException(503,"External authentication is not configured")
    return await client.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    client = oauth.create_client(settings.oidc_provider)
    if not client: raise HTTPException(503,"External authentication is not configured")
    try:
        token = await client.authorize_access_token(request)
        claims = token.get("userinfo")
        if not claims: raise ValueError("OIDC provider returned no identity claims")
        if claims.get("email_verified") is not True: raise PermissionError("Google email is not verified")
        user = provision_user(db, settings.oidc_provider, dict(claims), settings)
    except PermissionError:
        return RedirectResponse(f"{settings.web_app_url}/login?error=not_permitted")
    except Exception:
        return RedirectResponse(f"{settings.web_app_url}/login?error=invalid_callback")
    # Provider tokens remain transient; only the internal user id enters the session.
    request.session.clear(); request.session["user_id"] = user.id
    return RedirectResponse(settings.web_app_url)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"status":"signed_out"}
