from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.domain.models import User


@dataclass(frozen=True)
class Identity:
    user_id: int | None
    provider: str
    subject: str
    email: str | None
    display_name: str
    avatar_url: str | None = None


def email_permitted(email: str | None, settings: Settings) -> bool:
    if not settings.allowed_email_set and not settings.allowed_domain_set:
        return True
    if not email: return False
    normalized = email.lower()
    domain = normalized.rsplit("@", 1)[-1] if "@" in normalized else ""
    return normalized in settings.allowed_email_set or domain in settings.allowed_domain_set


def provision_user(db: Session, provider: str, claims: dict, settings: Settings) -> User:
    subject, email = claims.get("sub"), claims.get("email")
    if not subject: raise ValueError("OIDC identity is missing a subject")
    if not email_permitted(email, settings): raise PermissionError("This account is not permitted for the DealSage pilot")
    user = db.scalar(select(User).where(User.provider == provider, User.subject == subject))
    if not user:
        user = User(provider=provider,subject=subject,email=email,display_name=claims.get("name") or email or "DealSage user",avatar_url=claims.get("picture"))
        db.add(user)
    else:
        user.email, user.display_name, user.avatar_url = email, claims.get("name") or user.display_name, claims.get("picture")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(user)
    return user


def current_identity(request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> Identity:
    if settings.auth_mode == "demo":
        return Identity(None,"demo","local-demo",None,settings.demo_analyst_name)
    user_id = request.session.get("user_id")
    user = db.get(User, user_id) if user_id else None
    if not user or not user.active: raise HTTPException(401,"Authentication required")
    return Identity(user.id,user.provider,user.subject,user.email,user.display_name,user.avatar_url)
