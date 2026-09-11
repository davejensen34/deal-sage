"""Small process-local counters for failures the primary database cannot retain."""

from threading import Lock

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.domain.models import AuditEvent

_lock = Lock()
_audit_write_failures = 0


def audit_write_failures() -> int:
    with _lock:
        return _audit_write_failures


@event.listens_for(Session, "before_flush")
def _mark_audit_flush(session: Session, *_args: object) -> None:
    if any(isinstance(row, AuditEvent) for row in session.new):
        session.info["dealsage_audit_flush_pending"] = True


@event.listens_for(Session, "after_commit")
def _clear_audit_flush(session: Session) -> None:
    session.info.pop("dealsage_audit_flush_pending", None)


@event.listens_for(Session, "after_rollback")
def _count_failed_audit_flush(session: Session) -> None:
    global _audit_write_failures
    if session.info.pop("dealsage_audit_flush_pending", None):
        with _lock:
            _audit_write_failures += 1
