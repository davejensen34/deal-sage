from hashlib import sha256
import httpx
import pytest

from app.research.validation_budget import ValidationBudget, PROTOCOL
from scripts import milestone7_public_page as pages


@pytest.mark.asyncio
async def test_retained_text_hash_matches_actual_bytes_on_every_platform(tmp_path, monkeypatch):
    async def public(_):
        pass
    original = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(200,
        headers={"content-type": "text/html"},
        text='<p>Public announcement</p><p>September 1, 2026</p><script>private payload</script>'))
    monkeypatch.setattr(pages, "assert_public_network_url", public)
    monkeypatch.setattr(pages.httpx, "AsyncClient", lambda **kwargs: original(transport=transport, **kwargs))
    budget = ValidationBudget(tmp_path, PROTOCOL)
    with budget.locked():
        result = await pages.fetch(budget, "https://example.com/announcement", "article")
    retained = (tmp_path / result["text_file"]).read_bytes()
    assert retained == b"Public announcement\nSeptember 1, 2026"
    assert sha256(retained).hexdigest() == result["text_sha256"]
    assert "private payload" not in retained.decode()


@pytest.mark.asyncio
async def test_capability_redirect_is_not_followed_or_retained(tmp_path, monkeypatch):
    async def public(_):
        pass
    original = httpx.AsyncClient
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(302, headers={"location": "https://example.com/private?access_token=DO-NOT-RETAIN"})
    monkeypatch.setattr(pages, "assert_public_network_url", public)
    monkeypatch.setattr(pages.httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs))
    budget = ValidationBudget(tmp_path, PROTOCOL)
    with budget.locked():
        result = await pages.fetch(budget, "https://example.com/announcement", "article")
    assert len(requests) == 1 and result["status"] == "redirect" and "location" not in result
    assert "DO-NOT-RETAIN" not in (tmp_path / "result-001.json").read_text()
