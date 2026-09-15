import asyncio
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.database import Base
from app.domain.models import DiscoveryAttempt, DiscoveryProfile, DiscoveryRun, ResearchCase, SourceCandidate
from app.research.discovery_runs import DiscoverySettings, create_run, execute_attempt, preview, recover
from app.research.search import FixtureSearchProvider, SearchResult


@pytest.fixture
def db():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


def settings():
    return Settings(_env_file=None, demo_mode=True, auth_mode="demo", web_search_provider="disabled")


def make(db, config=None, cfg=None, key=None):
    config, cfg = config or DiscoverySettings(), cfg or settings()
    prepared = preview(config, cfg)
    return create_run(db, config, cfg, request_key=key or uuid4(), expected_hash=prepared["hash"], actor="Test reviewer")


def test_creation_is_atomic_idempotent_and_defaults_cannot_change_run(db):
    key = uuid4()
    first = make(db, key=key)
    assert make(db, key=key).id == first.id
    assert db.scalar(select(func.count(ResearchCase.id))) == 1
    db.add(DiscoveryProfile(settings=DiscoverySettings(max_records=100).model_dump(), actor="Other operator")); db.commit()
    assert db.get(DiscoveryRun, first.id).plan["settings"]["max_records"] == 25
    with pytest.raises(ValueError, match="different request"):
        make(db, DiscoverySettings(max_records=50), key=key)
    with pytest.raises(ValueError, match="Business-first"):
        DiscoverySettings(origin="business_first")
    with pytest.raises(ValueError):
        DiscoverySettings(max_queries=1, states=["CO", "UT"])


def test_exact_plan_and_disabled_providers_are_enforced(db):
    cfg = Settings(_env_file=None, demo_mode=False, auth_mode="demo", web_search_provider="disabled")
    run = make(db, cfg=cfg)
    with pytest.raises(ValueError, match="unavailable"):
        asyncio.run(execute_attempt(db, run, cfg, request_key=uuid4(), expected_revision=0, actor="Operator"))
    assert db.scalar(select(func.count(DiscoveryAttempt.id))) == 0
    with pytest.raises(ValueError, match="Plan changed"):
        create_run(db, DiscoverySettings(max_records=1), cfg, request_key=uuid4(), expected_hash=run.plan_hash, actor="Operator")


def test_pricing_expiry_and_configuration_drift_block_before_reservation(db):
    from app.research.discovery_runs import provider_snapshot
    cfg = Settings(_env_file=None, web_search_provider="openai", openai_api_key="fictional-test-key",
        openai_model="gpt-5-mini-2025-08-07")
    assert provider_snapshot(cfg, date(2026, 9, 15))["ready"]
    assert not provider_snapshot(cfg, date(2026, 9, 22))["ready"]
    plan = preview(DiscoverySettings(), cfg, today=date(2026, 9, 15))["plan"]
    assert plan["requests"][0]["max_tool_calls"] == 1 and plan["provider_retries"] == 0
    assert "fictional-test-key" not in str(plan)
    run = make(db)
    changed = settings().model_copy(update={"demo_mode": False})
    with pytest.raises(ValueError, match="changed/unavailable"):
        asyncio.run(execute_attempt(db, run, changed, request_key=uuid4(), expected_revision=0, actor="Operator"))
    assert db.scalar(select(func.count(DiscoveryAttempt.id))) == 0 and run.reserved_cents == 0


def test_empty_results_are_success_not_manufactured_matches_and_key_cannot_replay(db):
    run = make(db)
    key = uuid4()
    result = asyncio.run(execute_attempt(db, run, settings(), request_key=key, expected_revision=0,
        actor="Operator", provider=FixtureSearchProvider()))
    assert result["status"] == "completed" and result["record_count"] == 0
    replay = asyncio.run(execute_attempt(db, run, settings(), request_key=key, expected_revision=0, actor="Operator"))
    assert len(replay["attempts"]) == 1
    assert replay["attempts"][0]["result_count"] == 0


def test_failed_calls_keep_reservations_and_retry_consumes_new_budget(db, monkeypatch):
    # A synthetic priced fixture tests accounting without time-dependent prices.
    import app.research.discovery_runs as runs
    original = runs.provider_snapshot
    monkeypatch.setattr(runs, "provider_snapshot", lambda settings, today: {**original(settings, today), "reservation_cents": 12})
    cfg = settings()
    run = make(db, DiscoverySettings(max_cost_cents=24), cfg)
    failure = asyncio.run(execute_attempt(db, run, cfg, request_key=uuid4(), expected_revision=0,
        actor="Operator", provider=FixtureSearchProvider(error=RuntimeError("private error body"))))
    assert failure["reserved_cents"] == 12 and failure["attempts"][0]["error_code"] == "search_failed"
    retried = asyncio.run(execute_attempt(db, run, cfg, request_key=uuid4(), expected_revision=run.revision,
        actor="Operator", retry_last=True, provider=FixtureSearchProvider(error=RuntimeError())))
    assert retried["reserved_cents"] == 24 and len(retried["attempts"]) == 2
    assert "private error body" not in str(retried)
    with pytest.raises(ValueError, match="ceiling exhausted"):
        asyncio.run(execute_attempt(db, run, cfg, request_key=uuid4(), expected_revision=run.revision,
            actor="Operator", retry_last=True, provider=FixtureSearchProvider()))


def test_concurrent_attempt_recovery_rejects_late_results(db):
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        class Slow(FixtureSearchProvider):
            async def search(self, query, max_results):
                entered.set(); await release.wait()
                return [SearchResult("https://example.test/late", "Late", "Untrusted clue", "research")]
        run = make(db)
        key = uuid4()
        first = asyncio.create_task(execute_attempt(db, run, settings(), request_key=key,
            expected_revision=0, actor="Operator", provider=Slow()))
        await entered.wait()
        duplicate = await execute_attempt(db, run, settings(), request_key=key, expected_revision=0, actor="Operator")
        assert duplicate["status"] == "running"
        with pytest.raises(ValueError, match="active or changed"):
            await execute_attempt(db, run, settings(), request_key=uuid4(), expected_revision=0, actor="Operator")
        with pytest.raises(ValueError, match="eligible"):
            recover(db, run, expected_revision=run.revision)
        attempt = db.scalar(select(DiscoveryAttempt))
        attempt.recovery_after = datetime.now(timezone.utc) - timedelta(seconds=1); db.commit()
        recovered = recover(db, run, expected_revision=run.revision)
        assert recovered["attempts"][0]["status"] == "unknown"
        release.set(); await first
        db.expire_all()
        assert db.scalar(select(func.count(SourceCandidate.id))) == 0
        assert db.get(DiscoveryAttempt, attempt.id).status == "unknown"
    asyncio.run(scenario())


def test_record_cap_and_elapsed_limit_stop_new_calls(db):
    run = make(db, DiscoverySettings(states=["CO", "UT"], max_records=1))
    result = asyncio.run(execute_attempt(db, run, settings(), request_key=uuid4(), expected_revision=0, actor="Operator"))
    assert result["record_count"] == 1
    with pytest.raises(ValueError, match="ceiling exhausted"):
        asyncio.run(execute_attempt(db, run, settings(), request_key=uuid4(), expected_revision=run.revision, actor="Operator"))
    other = make(db)
    other.deadline_at = datetime.now(timezone.utc) - timedelta(seconds=1); db.commit()
    with pytest.raises(ValueError, match="elapsed-time"):
        asyncio.run(execute_attempt(db, other, settings(), request_key=uuid4(), expected_revision=0, actor="Operator"))


def test_api_permissions_and_saved_plan_round_trip(client, override_db_session):
    from app.main import app
    from app.auth.service import Identity, current_identity
    from app.core.config import get_settings
    app.dependency_overrides[get_settings] = settings
    role = "viewer"
    app.dependency_overrides[current_identity] = lambda: Identity(None, "demo", "test", None, "Test reviewer", role=role)
    try:
        config = DiscoverySettings().model_dump()
        assert client.post("/api/discovery/preview", json=config).status_code == 403
        role = "analyst"
        prepared = client.post("/api/discovery/preview", json=config).json()
        payload = {"settings": config, "request_key": str(uuid4()), "expected_hash": prepared["hash"]}
        run = client.post("/api/discovery/runs", json=payload).json()
        assert client.post("/api/discovery/runs", json=payload).json()["id"] == run["id"]
        attempt = {"request_key": str(uuid4()), "expected_revision": 0}
        url = f'/api/discovery/runs/{run["id"]}/execute'
        assert client.post(url, json=attempt).status_code == 403
        role = "operator"
        assert client.post("/api/discovery/defaults", json={**config, "max_records": 100}).status_code == 200
        result = client.post(url, json=attempt)
        assert result.status_code == 200
        assert result.json()["record_count"] == 1
        assert result.json()["deadline_at"].endswith(("Z", "+00:00"))
        assert result.json()["attempts"][0]["recovery_after"].endswith(("Z", "+00:00"))
        assert client.get(f'/api/discovery/runs/{run["id"]}').json()["plan"]["settings"]["max_records"] == 25
        assert client.get("/api/discovery/runs/999999").status_code == 404
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(current_identity, None)


def test_migration_preserves_run_history_and_refuses_destructive_downgrade(tmp_path):
    from alembic import command
    from app.ops.schema import alembic_config, upgrade_database
    url = "sqlite:///" + (tmp_path / "runs.db").as_posix()
    command.upgrade(alembic_config(url), "b144f0a9c721")
    upgrade_database(url)
    engine = create_engine(url)
    with Session(engine) as session:
        run = make(session)
        run_id = run.id
        asyncio.run(execute_attempt(session, run, settings(), request_key=uuid4(), expected_revision=0,
            actor="Operator", provider=FixtureSearchProvider(error=RuntimeError())))
    # Reopen the database/session, as a restarted API would.
    with Session(engine) as session:
        run = session.get(DiscoveryRun, run_id)
        assert run.plan["version"] == "discovery-run-v1" and run.status == "partial"
        result = asyncio.run(execute_attempt(session, run, settings(), request_key=uuid4(),
            expected_revision=run.revision, actor="Operator", retry_last=True, provider=FixtureSearchProvider()))
        assert [a["status"] for a in result["attempts"]] == ["failed", "succeeded"]
    with pytest.raises(RuntimeError, match="Cannot discard"):
        command.downgrade(alembic_config(url), "b144f0a9c721")
    engine.dispose()
