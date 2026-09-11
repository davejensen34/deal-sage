"""Explicit local operator controls for the bounded single-organization pilot."""

from __future__ import annotations

import argparse

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.auth.service import ROLE_PERMISSIONS
from app.core.config import get_settings
from app.domain.models import AuditEvent, User


def update_user_access(
    db: Session,
    *,
    provider: str,
    subject: str,
    role: str | None = None,
    active: bool | None = None,
    actor: str = "local-operator",
) -> User:
    """Change one stable provider subject and retain the prior access state."""
    if role is not None and role not in set(ROLE_PERMISSIONS) - {"demo"}:
        raise ValueError(f"Unknown pilot role: {role}")
    user = db.scalar(select(User).where(User.provider == provider, User.subject == subject))
    if user is None:
        raise ValueError("Pilot user not found")
    before = {"role": user.role, "active": user.active}
    if role is not None:
        user.role = role
    if active is not None:
        user.active = active
    after = {"role": user.role, "active": user.active}
    db.add(AuditEvent(
        user_id=user.id,
        candidate_id=None,
        actor=actor,
        action="user_access_changed",
        before_state=before,
        after_state=after,
        detail="Pilot access changed for stable provider subject.",
    ))
    db.commit()
    db.refresh(user)
    return user


def main() -> None:
    parser = argparse.ArgumentParser(description="Change one DealSage pilot user's access")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--role", choices=["viewer", "analyst", "operator", "administrator"])
    state = parser.add_mutually_exclusive_group()
    state.add_argument("--activate", action="store_true")
    state.add_argument("--deactivate", action="store_true")
    args = parser.parse_args()
    if args.role is None and not args.activate and not args.deactivate:
        parser.error("provide --role, --activate, or --deactivate")
    engine = create_engine(get_settings().database_url)
    with Session(engine) as db:
        user = update_user_access(
            db,
            provider=args.provider,
            subject=args.subject,
            role=args.role,
            active=True if args.activate else False if args.deactivate else None,
        )
        print(f"updated user_id={user.id} role={user.role} active={str(user.active).lower()}")


if __name__ == "__main__":
    main()
