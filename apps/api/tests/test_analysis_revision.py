from copy import deepcopy
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from app.research import analysis_execution as execution, analysis_revision as revision
from app.research.analysis_preparation import canonical_bytes


def legacy():
    request = {"model":"fixture", "input":json.dumps({"case_origin":"hybrid","sources":[{"source_id":"1","text":"Fictional company clue"}]}),
               "instructions":"old", "text":{"format":{"type":"json_schema","name":"old","strict":True,"schema":{}}},
               "tools":[],"store":False,"truncation":"disabled","max_output_tokens":2000}
    return {"protocol":"old","limits":{"calls":3,"max_output_tokens_per_call":2000,"reserved_cents_total":15},
            "requests":[{"slot":str(i),"request":deepcopy(request),"request_sha256":"old",
                         "preflight_expectation":"EXPECTED ANSWER - DO NOT SEND","raw_sha256":"source-hash"} for i in range(3)]}


def revised_fixture(monkeypatch):
    old = legacy()
    monkeypatch.setattr(revision,"LEGACY_BUNDLE_SHA256",sha256(canonical_bytes(old)).hexdigest())
    return old, revision.revise_bundle(old)


def test_revision_preserves_sources_expectations_and_original_bundle(monkeypatch):
    old, new = revised_fixture(monkeypatch)
    assert old == legacy() and new['approval_status']=='not_authorized'
    for before, after in zip(old['requests'], new['requests']):
        assert before['request']['input']==after['request']['input']
        assert before['raw_sha256']==after['raw_sha256']
        assert before['preflight_expectation']==after['preflight_expectation']
        request=after['request']
        assert request['max_output_tokens']==6000 and request['tools']==[] and request['store'] is False
        assert 'research_disposition' not in request['text']['format']['schema']['properties']
        assert 'EXPECTED ANSWER' not in json.dumps(request)
        assert after['request_sha256']==sha256(canonical_bytes(request)).hexdigest()


def test_revision_refuses_unreviewed_inputs():
    with pytest.raises(ValueError,match='Legacy bundle'):
        revision.revise_bundle(legacy())


class Client:
    max_retries=0

    def __init__(self, output):
        self.output=output; self.responses=self; self.calls=0

    async def post(self, *args, **kwargs):
        return {"input_tokens":100}

    async def create(self, **request):
        self.calls+=1
        assert request['max_output_tokens']==6000
        return SimpleNamespace(status='completed',model='fixture',output=[],
                               usage=SimpleNamespace(input_tokens=100,output_tokens=2100),
                               output_text=json.dumps(self.output))


def observation():
    return dict(case_origin='hybrid',identity_resolution='unresolved',relationship='unclear',
                relationship_time='unclear',operating_status='unknown',contradiction_state='none',
                supported_source_ids=['1'],contradictions=[],unresolved_questions=['Verify the clue'],
                summary='Fictional useful clue',state_fit='unknown',private_company_fit='unknown')


@pytest.mark.asyncio
async def test_v3_end_to_end_derives_disposition_and_keeps_claims_separate(tmp_path,monkeypatch):
    _, data=revised_fixture(monkeypatch)
    payload=canonical_bytes(data); path=tmp_path/'bundle.json'; path.write_bytes(payload)
    monkeypatch.setattr(execution,'BUNDLE_V3_SHA256',sha256(payload).hexdigest())
    old_claim=tmp_path/f'.{execution.PROTOCOL}.claimed'; old_claim.write_text('history')
    client=Client(observation())
    result=await execution.execute(path,tmp_path/'out.json',client,revision.PROTOCOL_V3)
    assert client.calls==3 and result['reserved_cents']==15
    for row in result['calls']:
        assert row['status']=='completed' and row['model_observation']==observation()
        assert row['deterministic_research_disposition']=='needs_more_research'
        assert 'research_disposition' not in row['model_observation']
    assert old_claim.read_text()=='history'
    with pytest.raises(FileExistsError):
        await execution.execute(path,tmp_path/'other.json',client,revision.PROTOCOL_V3)
    assert client.calls==3


@pytest.mark.asyncio
@pytest.mark.parametrize('bad', ['approval','hash','retries'])
async def test_v3_gates_fail_before_network_or_claim(tmp_path,monkeypatch,bad):
    _, data=revised_fixture(monkeypatch); payload=canonical_bytes(data)
    path=tmp_path/'bundle.json'; path.write_bytes(payload)
    monkeypatch.setattr(execution,'BUNDLE_V3_SHA256',sha256(payload).hexdigest())
    approval=revision.PROTOCOL_V3; client=Client(observation())
    if bad=='approval': approval=execution.PROTOCOL
    if bad=='hash': path.write_bytes(payload+b' ')
    if bad=='retries': client.max_retries=1
    with pytest.raises(ValueError): await execution.execute(path,tmp_path/'out.json',client,approval)
    assert client.calls==0 and not list(tmp_path.glob('*.claimed'))


@pytest.mark.asyncio
async def test_v3_rejects_model_disposition_without_saving_payload(tmp_path,monkeypatch):
    _, data=revised_fixture(monkeypatch); payload=canonical_bytes(data)
    path=tmp_path/'bundle.json'; path.write_bytes(payload)
    monkeypatch.setattr(execution,'BUNDLE_V3_SHA256',sha256(payload).hexdigest())
    output={**observation(),'research_disposition':'candidate_supported'}
    result=await execution.execute(path,tmp_path/'out.json',Client(output),revision.PROTOCOL_V3)
    assert all(r['status']=='invalid' and r['diagnostic_codes']==['observation_schema'] for r in result['calls'])
    assert all('model_observation' not in r for r in result['calls'])
