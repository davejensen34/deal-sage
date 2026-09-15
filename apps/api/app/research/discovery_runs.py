"""Explicit, durable discovery attempts. No worker queue or automatic replay."""
import asyncio
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from app.domain.models import AuditEvent, DiscoveryAttempt, DiscoveryProfile, DiscoveryRun, ResearchCase, SourceCandidate
from app.research.cases import DEFAULT_RESEARCH_BUDGET
from app.research.search import FixtureSearchProvider, SearchResult, SearchService
from app.research.search_openai import search_request
from app.research.signal_freshness import dated_query

VERSION = "discovery-run-v1"
STATES = {"CO": "Colorado", "UT": "Utah", "TX": "Texas"}
SIGNALS = {"possible_death": "business owner obituary company", "retirement": "business owner retirement",
           "succession": "family business succession", "ownership_change": "private business ownership transfer",
           "founder_exit": "company founder departure", "dissolution": "business dissolution notice",
           "restructuring": "business restructuring", "leadership_change": "business leadership change"}


class DiscoverySettings(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    origin: Literal["signal_first", "business_first", "hybrid"] = "signal_first"
    objective: str = Field(default="Find recent business transitions worth reviewing", min_length=10, max_length=160)
    business_name: str = Field(default="", max_length=100)
    states: list[Literal["CO", "UT", "TX"]] = Field(default=["CO"], min_length=1, max_length=3)
    signals: list[str] = Field(default=["retirement"], min_length=1, max_length=8)
    lookback_days: int = Field(default=90, ge=1, le=365)
    max_records: int = Field(default=25, ge=1, le=100)
    max_queries: int = Field(default=3, ge=1, le=30)
    max_cost_cents: int = Field(default=100, ge=0, le=500)
    max_elapsed_seconds: int = Field(default=900, ge=60, le=3600)

    @model_validator(mode="after")
    def coherent(self):
        if self.origin == "business_first" and not self.business_name.strip():
            raise ValueError("Business-first discovery requires a business name")
        if not self.objective.strip() or any(s not in SIGNALS for s in self.signals):
            raise ValueError("Use a research objective and supported signal families")
        if len(set(self.states)) != len(self.states) or len(set(self.signals)) != len(self.signals):
            raise ValueError("States and signals must not repeat")
        if len(self.states) * len(self.signals) > self.max_queries:
            raise ValueError("Query ceiling must cover each selected state/signal combination")
        return self


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def provider_snapshot(settings, today):
    if settings.web_search_provider == "disabled" and settings.demo_mode and settings.auth_mode == "demo":
        return {"key": "fixture", "model": None, "reservation_cents": 0, "timeout_seconds": 5,
                "max_results": 5, "max_output_tokens": 0, "ready": True, "reason": "Fictional demo; no network calls"}
    # Reuse the reviewed M7 conservative envelope, never a guessed price for a
    # different model. A new price/version needs review, not a mutable UI field.
    from app.research.recent_discovery import MODEL, prepare
    pricing = prepare(today.isoformat())["pricing"]
    fresh = datetime.fromisoformat(pricing["checked_date"]).date() <= today <= datetime.fromisoformat(pricing["checked_date"]).date() + timedelta(days=7)
    ready = settings.web_search_provider == "openai" and bool(settings.openai_api_key) and settings.openai_model == MODEL and fresh
    return {"key": settings.web_search_provider, "model": settings.openai_model,
            "reservation_cents": 12, "timeout_seconds": settings.ai_request_timeout_seconds,
            "max_results": settings.web_search_max_results, "max_output_tokens": settings.web_search_max_output_tokens,
            "pricing": pricing, "ready": ready,
            "reason": "Configured bounded search" if ready else "Enable search with credentials and the reviewed pinned model/pricing envelope"}


def preview(config, settings, *, today=None):
    today = today or datetime.now(timezone.utc).date()
    policy = {"version": "signal-intake-v1", "assessment_date": today.isoformat(), "lookback_days": config.lookback_days}
    queries = [f"{config.objective.strip()} {config.business_name.strip()} {STATES[state]} {SIGNALS[signal]}".strip()
               for state in config.states for signal in config.signals]
    plan = {"version": VERSION, "settings": config.model_dump(), "policy": policy,
            "provider": provider_snapshot(settings, today), "queries": queries,
            "submitted_queries": [dated_query(q, policy) for q in queries],
            "retrieval_calls": 0, "analysis_calls": 0}
    if any(len(q) > 500 for q in plan["submitted_queries"]):
        raise ValueError("Research query is too long")
    plan["requests"] = [search_request(q, plan["provider"]["model"], plan["provider"]["max_output_tokens"])
                        for q in plan["submitted_queries"]] if plan["provider"]["key"] == "openai" else []
    plan["provider_retries"] = 0
    return {"plan": plan, "hash": digest(plan)}


def create_run(db, config, settings, *, request_key, expected_hash, actor, profile_id=None):
    key = str(UUID(str(request_key)))
    existing = db.scalar(select(DiscoveryRun).where(DiscoveryRun.request_key == key))
    if existing:
        if existing.plan_hash != expected_hash or existing.actor != actor or existing.plan["settings"] != config.model_dump():
            raise ValueError("Creation key already belongs to a different request")
        return existing
    prepared = preview(config, settings)
    if prepared["hash"] != expected_hash:
        raise ValueError("Plan changed; preview the current configuration before creating a run")
    if profile_id is not None and db.get(DiscoveryProfile, profile_id) is None:
        raise ValueError("Saved defaults version does not exist")
    case = ResearchCase(origin_strategy=config.origin, research_budget={**DEFAULT_RESEARCH_BUDGET,
        "max_queries": config.max_queries, "max_documents": 0, "max_steps": config.max_queries,
        "max_cost_cents": config.max_cost_cents, "max_elapsed_seconds": config.max_elapsed_seconds},
        signal_intake_policy=prepared["plan"]["policy"])
    try:
        db.add(case); db.flush()
        run = DiscoveryRun(request_key=key, case_id=case.id, profile_id=profile_id,
                           plan=prepared["plan"], plan_hash=expected_hash, actor=actor)
        db.add(run); db.commit(); db.refresh(run)
        return run
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(DiscoveryRun).where(DiscoveryRun.request_key == key))
        if existing and existing.plan_hash == expected_hash and existing.actor == actor:
            return existing
        raise ValueError("Concurrent creation conflicts with this request") from None


def run_models(run):
    from app.domain.models import FollowupRun, FollowupAttempt
    return (FollowupRun, FollowupAttempt) if isinstance(run, FollowupRun) else (DiscoveryRun, DiscoveryAttempt)


def run_view(db, run):
    _, Attempt = run_models(run)
    attempts = db.scalars(select(Attempt).where(Attempt.run_id == run.id).order_by(Attempt.id)).all()
    count = db.scalar(select(func.count(SourceCandidate.id)).where(SourceCandidate.case_id == run.case_id)) or 0
    return {"id": run.id, "case_id": run.case_id, "profile_id": getattr(run, "profile_id", None), "frontier_id": getattr(run, "frontier_id", None), "plan": run.plan,
            "plan_hash": run.plan_hash, "actor": run.actor, "status": run.status, "revision": run.revision,
            "next_slot": run.next_slot, "reserved_cents": run.reserved_cents,
            "deadline_at": utc(run.deadline_at) if run.deadline_at else None,
            "record_count": count, "attempts": [{"id": a.id, "request_key": a.request_key, "slot": a.slot,
                "status": a.status, "reserved_cents": a.reserved_cents, "result_count": a.result_count,
                "error_code": a.error_code, "actor": a.actor, "recovery_after": utc(a.recovery_after)} for a in attempts]}


async def execute_attempt(db, run, settings, *, request_key, expected_revision, actor, retry_last=False, provider=None):
    Run, Attempt = run_models(run)
    from app.research import followups
    is_followup = hasattr(run, "frontier_id")
    key = str(UUID(str(request_key)))
    prior = db.scalar(select(Attempt).where(Attempt.run_id == run.id, Attempt.request_key == key))
    if prior:
        db.refresh(run)
        return run_view(db, run)
    now = datetime.now(timezone.utc)
    if is_followup:
        followups.admit(db, run)
    else:
        # Serialize discovery admission with explicit case date renewal. The
        # exact frozen request must never execute under a different window.
        claim=db.execute(update(ResearchCase).where(ResearchCase.id==run.case_id,
            ResearchCase.status=='open').values(updated_at=ResearchCase.updated_at))
        if claim.rowcount!=1: raise ValueError('Case is stopped; discovery unavailable')
        db.expire_all()
        from app.research.signal_freshness import dated_query
        case=db.get(ResearchCase,run.case_id)
        if [dated_query(q,case.signal_intake_policy) for q in run.plan['queries']]!=run.plan['submitted_queries']:
            raise ValueError('Case date policy changed; prepare a new follow-up')
    frozen = run.plan["provider"]
    if digest(frozen) != digest(provider_snapshot(settings, now.date())) or not frozen["ready"]:
        raise ValueError("Provider configuration or pricing changed/unavailable; prepare a new run")
    if frozen["key"] == "openai" and run.plan.get("requests") != [
        search_request(q, frozen["model"], frozen["max_output_tokens"]) for q in run.plan["submitted_queries"]
    ]:
        raise ValueError("Provider request contract changed; prepare a new run")
    if (now.date() - datetime.fromisoformat(run.plan["policy"]["assessment_date"]).date()).days > 7:
        raise ValueError("Discovery plan is older than seven days; prepare a current plan")
    if run.status == "running" or run.revision != expected_revision:
        raise ValueError("Run is active or changed; reload its progress")
    cfg = run.plan["settings"]
    view = run_view(db, run)
    attempts = view["attempts"]
    slot = run.next_slot
    if retry_last:
        if not attempts or attempts[-1]["status"] != "failed":
            raise ValueError("Only a retained failed attempt can be retried explicitly")
        slot = attempts[-1]["slot"]
    if slot >= len(run.plan["queries"]):
        raise ValueError("No planned queries remain")
    reserve = frozen["reservation_cents"]
    if len(attempts) >= cfg["max_queries"] or run.reserved_cents + reserve > cfg["max_cost_cents"]:
        raise ValueError("Attempt or reservation ceiling exhausted")
    remaining = cfg["max_records"] - view["record_count"]
    deadline = utc(run.deadline_at) if run.deadline_at else now + timedelta(seconds=cfg["max_elapsed_seconds"])
    timeout = min(frozen["timeout_seconds"], (deadline - now).total_seconds())
    if remaining <= 0 or timeout <= 0:
        raise ValueError("Record or elapsed-time ceiling exhausted")
    if provider is None:
        if frozen["key"] == "fixture":
            provider = FixtureSearchProvider([SearchResult(url=f"https://example.test/fictional-discovery/{'followup-'+str(run.id) if is_followup else slot}",
                title="Fictional discovery clue", publisher="Fictional demonstration source",
                relevance_reason="Fictional clue for practicing evidence review; not a real business match.",
                proposed_use="case_specific_research")])
        else:
            provider = settings.build_search_provider()
    if provider is None:
        raise ValueError("Search provider is disabled")
    # CAS and the unique attempt key share the reservation transaction. No external
    # call is made until commit succeeds, including under concurrent HTTP requests.
    claimed = db.execute(update(Run).where(Run.id == run.id,
        Run.revision == expected_revision, Run.status != "running").values(
        status="running", revision=expected_revision + 1, reserved_cents=run.reserved_cents + reserve,
        deadline_at=deadline))
    if claimed.rowcount != 1:
        db.rollback(); raise ValueError("Another request claimed this run")
    attempt = Attempt(run_id=run.id, request_key=key, slot=slot, actor=actor,
        reserved_cents=reserve, recovery_after=now + timedelta(seconds=timeout + 60))
    if is_followup:
        attempt.step_id = followups.start(db, run, actor)
    db.add(attempt); db.commit(); db.refresh(run)
    claimed_revision = run.revision
    outcome, count, error = "succeeded", None, None
    def accept_results():
        # Lock the run in the same transaction as staging. A late response after
        # recovery cannot append records beyond the next attempt's frozen cap.
        accepted = db.execute(update(Run).where(Run.id == run.id,
            Run.revision == claimed_revision, Run.status == "running").values(revision=claimed_revision))
        if accepted.rowcount != 1:
            raise ValueError("Attempt no longer owns this run")
    try:
        results = await asyncio.wait_for(SearchService(db).execute(run.case_id, provider,
            run.plan["queries"][slot], max_results=min(remaining, frozen["max_results"]),
            accept_results=accept_results, authorize_query=accept_results if is_followup else None), timeout=timeout)
        count = len(results)
    except Exception as exc:
        db.rollback()
        outcome, error = "failed", "timeout" if isinstance(exc, TimeoutError) else "search_failed"
    # Cancellation/process death deliberately leaves a running, reserved attempt.
    # Recovery never silently replays it or refunds an unknown provider outcome.
    db.refresh(run); db.refresh(attempt)
    next_slot = max(run.next_slot, slot + 1)
    completed = db.execute(update(Run).where(Run.id == run.id,
        Run.revision == claimed_revision, Run.status == "running").values(
        next_slot=next_slot, revision=claimed_revision + 1,
        status="completed" if outcome == "succeeded" and next_slot == len(run.plan["queries"]) else "partial"))
    if completed.rowcount != 1:
        db.rollback(); db.refresh(run)
        return run_view(db, run)
    attempt.status, attempt.result_count, attempt.error_code = outcome, count, error
    if is_followup:
        followups.finish(db, run, attempt)
    db.commit()
    db.refresh(run)
    return run_view(db, run)


def recover(db, run, *, expected_revision, actor=None, user_id=None):
    Run, Attempt = run_models(run)
    attempt = db.scalar(select(Attempt).where(Attempt.run_id == run.id,
        Attempt.status == "running").order_by(Attempt.id.desc()))
    if not attempt or datetime.now(timezone.utc) < utc(attempt.recovery_after):
        raise ValueError("No interrupted attempt is eligible for recovery yet")
    result = db.execute(update(Run).where(Run.id == run.id,
        Run.revision == expected_revision, Run.status == "running").values(
        status="partial", revision=expected_revision + 1, next_slot=max(run.next_slot, attempt.slot + 1)))
    if result.rowcount != 1:
        db.rollback(); raise ValueError("Run changed; reload before recovery")
    attempt.status, attempt.error_code = "unknown", "interrupted_outcome_unknown"
    if hasattr(run, "frontier_id"):
        from app.research.followups import finish
        finish(db, run, attempt)
    if actor is not None:
        kind = "followup" if hasattr(run, "frontier_id") else "discovery"
        db.add(AuditEvent(actor=actor, user_id=user_id, action=f"{kind}_recovered",
            detail=f"{kind} run {run.id}: retained interrupted outcome; no replay or refund."))
    db.commit(); db.refresh(run)
    return run_view(db, run)
