def test_dashboard_uses_persisted_seed_data(client):
    response=client.get("/api/dashboard")
    assert response.status_code==200
    assert response.json()["metrics"]["total"]==18
    assert response.json()["metrics"]["evidence_items"]==36

def test_candidate_search_and_filter(client):
    response=client.get("/api/candidates",params={"q":"Alder","status":"validated"})
    assert response.status_code==200
    assert response.json()["total"]==1
    assert response.json()["items"][0]["business"]=="Alder Ridge Toolworks"

def test_status_update_persists_and_audits(client):
    response=client.patch("/api/candidates/2/status",json={"status":"watchlist","reason":"Ambiguous identity","note":"Monitor for a second source."})
    assert response.status_code==200
    detail=client.get("/api/candidates/2").json()
    assert detail["status"]=="watchlist"
    assert any(event["action"]=="status_changed" for event in detail["audit"])
    assert detail["review"]["analyst_notes"][-1]["note"]=="Monitor for a second source."

def test_decision_requires_reason_and_note(client):
    assert client.patch("/api/candidates/2/status",json={"status":"rejected","reason":"","note":""}).status_code==422

def test_note_persists_and_audits(client):
    assert client.post("/api/candidates/3/notes",json={"note":"Registered agent is not ownership."}).status_code==200
    detail=client.get("/api/candidates/3").json()
    assert detail["review"]["analyst_notes"][-1]["note"].startswith("Registered agent")
    assert any(event["action"]=="analyst_note_added" for event in detail["audit"])
