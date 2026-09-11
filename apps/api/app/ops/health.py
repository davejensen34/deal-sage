"""Aggregate-safe operational readiness for the single-host pilot."""

from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import shutil
import tempfile

from alembic.script import ScriptDirectory
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.models import AcquisitionRun, AuditEvent, ModelProposal, ResearchStep, SourceRefresh
from app.ops.schema import alembic_config
from app.ops.telemetry import audit_write_failures


SAFE_FAILURE_CLASS = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,79}$")


def _failure_counts(values: list[str | None]) -> dict[str, int]:
    # Historical error fields are not trusted merely because newer writers store
    # exception classes. Anything shaped like a message/body is collapsed.
    safe = [value if value and SAFE_FAILURE_CLASS.fullmatch(value) else "redacted" for value in values]
    return dict(sorted(Counter(safe).items()))


def _storage_readiness(root: Path) -> dict[str, object]:
    result: dict[str, object] = {"writable": False, "capacity_bytes": None, "free_bytes": None}
    try:
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".readiness-", dir=root, delete=True) as probe:
            probe.write(b"ready")
            probe.flush()
        usage = shutil.disk_usage(root)
        result.update(writable=True, capacity_bytes=usage.total, free_bytes=usage.free)
    except OSError:
        pass
    return result


def operational_readiness(db: Session, settings: Settings, now: datetime | None = None) -> dict[str, object]:
    """Return only aggregates and safe classes from the most recent 24 hours."""
    observed_at = now or datetime.now(timezone.utc)
    cutoff = observed_at - timedelta(hours=24)
    db.execute(text("select 1"))
    current_revision = db.execute(text("select version_num from alembic_version")).scalar_one()
    expected_revision = ScriptDirectory.from_config(alembic_config(settings.database_url)).get_current_head()
    storage = _storage_readiness(settings.evidence_storage_path)

    refreshes = db.scalars(select(SourceRefresh).where(SourceRefresh.created_at >= cutoff)).all()
    acquisitions = db.scalars(select(AcquisitionRun).where(AcquisitionRun.created_at >= cutoff)).all()
    proposals = db.scalars(select(ModelProposal).where(ModelProposal.created_at >= cutoff)).all()
    steps = db.scalars(select(ResearchStep).where(ResearchStep.created_at >= cutoff)).all()
    audit_total = db.scalar(select(func.count(AuditEvent.id)).where(AuditEvent.timestamp >= cutoff)) or 0
    audit_attributed = db.scalar(select(func.count(AuditEvent.id)).where(AuditEvent.timestamp >= cutoff, AuditEvent.user_id.is_not(None))) or 0
    authorization_denials = db.scalar(select(func.count(AuditEvent.id)).where(AuditEvent.timestamp >= cutoff, AuditEvent.action == "authorization_denied")) or 0

    dependencies = {
        "database": {"reachable": True},
        "schema": {"current_revision": current_revision, "expected_revision": expected_revision, "at_head": current_revision == expected_revision},
        "evidence_storage": storage,
    }
    degraded = not dependencies["schema"]["at_head"] or not storage["writable"]
    return {
        "status": "degraded" if degraded else "ready",
        "observed_at": observed_at,
        "window_hours": 24,
        "dependencies": dependencies,
        "activity": {
            "source_refreshes": len(refreshes),
            "acquisition_runs": len(acquisitions),
            "model_proposals": len(proposals),
            "research_steps": len(steps),
        },
        "failures": {
            "source_refresh": _failure_counts([row.error_code for row in refreshes if row.status in {"failed", "partial"}]),
            "acquisition": _failure_counts([row.error for row in acquisitions if row.status in {"failed", "partial"}]),
            "model": _failure_counts([row.error_class for row in proposals if row.execution_outcome != "completed"]),
            "research_step": _failure_counts([row.error_class for row in steps if row.status == "failed"]),
        },
        "recorded_cost": {
            "source_refresh_usd": round(sum(row.actual_cost_usd for row in refreshes), 4),
            "model_proposal_usd": round(sum(row.cost_cents for row in proposals) / 100, 4),
            "research_step_usd": round(sum(row.cost_cents for row in steps) / 100, 4),
            "amounts_are_separate_non_additive_views": True,
        },
        "audit": {
            "events": audit_total,
            "attributed": audit_attributed,
            "unattributed": audit_total - audit_attributed,
            "attribution_percent": round(100 * audit_attributed / audit_total, 1) if audit_total else None,
            "authorization_denials": authorization_denials,
            "write_failures_since_process_start": audit_write_failures(),
            "write_failure_scope": "process_local_database_transaction_rollbacks_containing_new_audit_events",
        },
        "content_boundaries": {
            "raw_evidence_included": False,
            "personal_identifiers_included": False,
            "provider_error_bodies_included": False,
            "record_identifiers_included": False,
        },
    }
