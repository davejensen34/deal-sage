import json
from hashlib import sha256
from types import SimpleNamespace

import pytest

from app.research import analysis_execution as execution
from app.research.analysis_preparation import canonical_bytes


class Client:
    max_retries = 0

    def __init__(self, output, *, count=100, failure=False):
        self.output, self.count, self.failure = output, count, failure
        self.responses = self
        self.calls = 0

    async def post(self, *args, **kwargs):
        return {"input_tokens": self.count}

    async def create(self, **kwargs):
        self.calls += 1
        if self.failure:
            raise RuntimeError('secret provider body must not survive')
        return SimpleNamespace(status='completed', model='fixture', output=[],
                               usage=SimpleNamespace(input_tokens=100,output_tokens=50),
                               output_text=json.dumps(self.output))


def bundle(tmp_path, monkeypatch):
    request = dict(model='fixture',input=json.dumps({'sources':[{'source_id':'1'}]}),
                   instructions='fixture',text={},tools=[],truncation='disabled')
    data = {'requests':[{'slot':str(i),'request_sha256':str(i),'request':request} for i in range(3)]}
    path = tmp_path/'bundle.json'; path.write_bytes(canonical_bytes(data))
    monkeypatch.setattr(execution,'BUNDLE_SHA256',sha256(path.read_bytes()).hexdigest())
    return path


@pytest.mark.asyncio
async def test_failed_calls_consume_reservations_and_cannot_rerun(tmp_path, monkeypatch):
    path=bundle(tmp_path,monkeypatch); client=Client({},failure=True)
    result=await execution.execute(path,tmp_path/'out.json',client,execution.PROTOCOL)
    assert client.calls == 3 and result['reserved_cents'] == 15
    assert 'secret provider body' not in json.dumps(result)
    with pytest.raises(FileExistsError):
        await execution.execute(path,tmp_path/'different.json',client,execution.PROTOCOL)
    assert client.calls == 3


@pytest.mark.asyncio
async def test_token_overrun_blocks_analysis_and_remaining_slots(tmp_path, monkeypatch):
    path=bundle(tmp_path,monkeypatch); client=Client({},count=20001)
    result=await execution.execute(path,tmp_path/'out.json',client,execution.PROTOCOL)
    assert client.calls == 0 and result['count_requests'] == 1
    assert result['calls'][0]['status'] == 'failed'


@pytest.mark.asyncio
async def test_missing_approval_cannot_claim_or_execute(tmp_path, monkeypatch):
    path=bundle(tmp_path,monkeypatch); client=Client({})
    with pytest.raises(ValueError):
        await execution.execute(path,tmp_path/'out.json',client,'wrong')
    assert client.calls == 0 and not (tmp_path/f'.{execution.PROTOCOL}.claimed').exists()


@pytest.mark.asyncio
async def test_valid_observations_are_separate_from_invalid_payloads(tmp_path, monkeypatch):
    observation=dict(case_origin='hybrid',identity_resolution='unresolved',relationship='unclear',
                     relationship_time='unclear',operating_status='unknown',contradiction_state='none',
                     research_disposition='needs_more_research',supported_source_ids=['1'],contradictions=[],
                     unresolved_questions=['Verify ownership'],summary='Retained clue',state_fit='unknown',
                     private_company_fit='unknown')
    path=bundle(tmp_path,monkeypatch); client=Client(observation)
    result=await execution.execute(path,tmp_path/'out.json',client,execution.PROTOCOL)
    assert all(r['status']=='completed' and r['observation']==observation for r in result['calls'])


@pytest.mark.asyncio
async def test_invalid_output_does_not_persist_payload(tmp_path, monkeypatch):
    path=bundle(tmp_path,monkeypatch); client=Client({'untrusted':'invalid body'})
    result=await execution.execute(path,tmp_path/'out.json',client,execution.PROTOCOL)
    assert all(r['status']=='invalid' and 'observation' not in r for r in result['calls'])
    assert 'invalid body' not in json.dumps(result)


@pytest.mark.asyncio
@pytest.mark.parametrize('status',['incomplete','refusal'])
async def test_noncompleted_provider_outcomes_preserve_usage_only(tmp_path, monkeypatch, status):
    path=bundle(tmp_path,monkeypatch); client=Client({})
    async def response(**kwargs):
        return SimpleNamespace(status='incomplete' if status=='incomplete' else 'completed',model='fixture',
                               incomplete_details=SimpleNamespace(reason='max_output_tokens'),
                               output=[SimpleNamespace(content=[SimpleNamespace(type='refusal',refusal='private body')])] if status=='refusal' else [],
                               usage=SimpleNamespace(input_tokens=100,output_tokens=2000))
    client.create=response
    result=await execution.execute(path,tmp_path/'out.json',client,execution.PROTOCOL)
    assert all(r['status']==status and r['output_tokens']==2000 for r in result['calls'])
    assert 'private body' not in json.dumps(result)


@pytest.mark.asyncio
async def test_missing_count_reports_safe_reason_without_generation(tmp_path, monkeypatch):
    path=bundle(tmp_path,monkeypatch); client=Client({},count=None)
    result=await execution.execute(path,tmp_path/'out.json',client,execution.PROTOCOL)
    assert client.calls==0
    assert result['calls'][0]['reason']=='input_count_missing_or_invalid'


@pytest.mark.asyncio
async def test_real_sdk_token_count_parsing_with_offline_transport(tmp_path, monkeypatch):
    import httpx
    AsyncOpenAI = pytest.importorskip('openai').AsyncOpenAI
    path=bundle(tmp_path,monkeypatch)
    async def handler(request):
        assert request.url.path == '/v1/responses/input_tokens'
        return httpx.Response(200,json={'input_tokens':20001,'object':'response.input_tokens'})
    async with AsyncOpenAI(api_key='fixture',max_retries=0,
                           http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))) as client:
        result=await execution.execute(path,tmp_path/'out.json',client,execution.PROTOCOL)
    row=result['calls'][0]
    assert row['counted_input_tokens']==20001
    assert row['reason']=='input_count_outside_limit' and not row['analysis_attempted']
