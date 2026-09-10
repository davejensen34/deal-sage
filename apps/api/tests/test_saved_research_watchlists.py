from sqlalchemy import select

from app.domain.models import AuditEvent


def test_saved_research_round_trip_and_criteria_guard(client):
    created = client.post(
        "/api/saved-research",
        json={"name": "Colorado review", "criteria": {"state": "CO", "min_confidence": 60, "sort": "confidence", "order": "desc"}},
    )
    assert created.status_code == 201
    saved = created.json()
    assert saved["criteria"]["state"] == "CO"
    assert any(item["id"] == saved["id"] for item in client.get("/api/saved-research").json())
    assert client.post("/api/saved-research", json={"name": "Unsafe field", "criteria": {"raw_sql": "no"}}).status_code == 422
    assert client.delete(f"/api/saved-research/{saved['id']}").json() == {"status": "deleted"}


def test_watchlist_membership_references_candidate_and_audits(client, override_db_session):
    created = client.post("/api/watchlists", json={"name": "Priority follow-up", "description": "Weekly analyst review"})
    assert created.status_code == 201
    watchlist_id = created.json()["id"]

    added = client.post(
        f"/api/watchlists/{watchlist_id}/candidates",
        json={"candidate_id": 1, "rationale": "Independent records align."},
    )
    assert added.status_code == 201
    lists = client.get("/api/watchlists").json()
    assert lists[0]["candidates"][0]["id"] == 1
    assert lists[0]["candidates"][0]["rationale"] == "Independent records align."
    assert client.post(f"/api/watchlists/{watchlist_id}/candidates", json={"candidate_id": 1}).status_code == 409

    event = override_db_session.scalar(
        select(AuditEvent).where(AuditEvent.action == "candidate_added_to_watchlist").order_by(AuditEvent.id.desc())
    )
    assert event.actor == "Morgan Lee"
    assert event.after_state["watchlist_id"] == watchlist_id
    assert client.delete(f"/api/watchlists/{watchlist_id}/candidates/1").json() == {"status": "deleted"}
