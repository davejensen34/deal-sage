from app.api import routes
from app.domain.models import AlertEvent, SourceRefresh
from app.research.alerts import evaluate_refresh_alerts
from app.research.refresh import RefreshSource
from app.research.sources.base import SourceAdapter
from tests.test_source_refreshes import DEFINITION, parser


class FailingAlertAdapter(SourceAdapter):
    definition = DEFINITION

    async def fetch_sample(self, limit: int):
        raise ConnectionError("untrusted provider detail")


def test_alerts_require_opt_in_and_are_scoped_to_refresh_outcomes(client, monkeypatch, tmp_path):
    monkeypatch.setattr(routes, "refresh_sources", lambda: {DEFINITION.key: RefreshSource(FailingAlertAdapter(), parser, "fixture-v1")})
    monkeypatch.setattr(routes.settings, "evidence_storage_path", tmp_path)
    assert client.get("/api/research/alerts").json() == []

    subscription = client.post(
        "/api/research/alert-subscriptions",
        json={"source_key": DEFINITION.key, "event_types": ["refresh_failed"]},
    )
    assert subscription.status_code == 201
    subscription_id = subscription.json()["id"]
    refresh = client.post("/api/research/source-refreshes", json={"source_key": DEFINITION.key, "record_limit": 1})
    assert refresh.json()["status"] == "failed"

    alerts = client.get("/api/research/alerts").json()
    assert len(alerts) == 1
    assert alerts[0]["event_type"] == "refresh_failed"
    assert alerts[0]["source_refresh_id"] == refresh.json()["id"]
    assert "untrusted provider detail" not in str(alerts)
    marked = client.patch(f"/api/research/alerts/{alerts[0]['id']}/read")
    assert marked.json()["status"] == "read"

    assert client.delete(f"/api/research/alert-subscriptions/{subscription_id}").json() == {"status": "disabled"}
    client.post("/api/research/source-refreshes", json={"source_key": DEFINITION.key, "record_limit": 1})
    assert len(client.get("/api/research/alerts").json()) == 1


def test_subscription_rejects_success_noise_and_unapproved_sources(client):
    assert client.post(
        "/api/research/alert-subscriptions",
        json={"source_key": DEFINITION.key, "event_types": ["refresh_succeeded"]},
    ).status_code == 422
    assert client.post(
        "/api/research/alert-subscriptions",
        json={"source_key": "utah_business_entity_list", "event_types": ["refresh_failed"]},
    ).status_code == 422


def test_quarantine_alert_is_deterministic(client, override_db_session):
    subscription = client.post(
        "/api/research/alert-subscriptions",
        json={"source_key": "texas_active_franchise_taxpayers", "event_types": ["quarantine_detected"]},
    )
    assert subscription.status_code == 201
    refresh = SourceRefresh(
        source_key="texas_active_franchise_taxpayers", jurisdiction="Texas",
        requested_by_key="demo:local-demo", requested_by_name="Morgan Lee", status="partial",
        record_limit=1, approved_cost_usd=0, actual_cost_usd=0, contract_fingerprint="a" * 64,
        freshness_status="not_measurable_from_record", result_summary={"quarantined": 1},
    )
    override_db_session.add(refresh)
    override_db_session.commit()
    created = evaluate_refresh_alerts(override_db_session, refresh)
    assert created[0].event_type == "quarantine_detected"
    assert "1 curated outcome entered quarantine" in created[0].detail
    evaluate_refresh_alerts(override_db_session, refresh)
    assert override_db_session.query(AlertEvent).filter_by(source_refresh_id=refresh.id).count() == 1
