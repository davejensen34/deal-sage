from hashlib import sha256
import json

import pytest

from app.research.analysis_preparation import (
    ELIGIBLE_SLOTS, canonical_bytes, observation_errors, prepare_bundle, prepare_request, verify_text,
)
from scripts.prepare_milestone7_analysis import contained_file


def fixture():
    raw = b'<html><script>unsafe runtime</script><p>A fictional company announcement.</p></html>'
    text = 'A fictional company announcement.'
    packets = [dict(slot=slot, evidence_id=i, raw_sha256=sha256(raw).hexdigest(),
                    text_sha256=sha256(text.encode()).hexdigest(), parser='m7-preflight-html-text-v1',
                    url='https://example.org/notice', assessment='SECRET EXPECTED ANSWER',
                    published_date_observed=None)
               for i, slot in enumerate(sorted(ELIGIBLE_SLOTS), 1)]
    manifest = dict(analysis_eligible_packets=packets, excluded_after_landing=[99])
    return manifest, raw, text


def compile_fixture(manifest, raw, text):
    encoded = canonical_bytes(manifest)
    return prepare_bundle(encoded, lambda _: (raw, text), expected_sha256=sha256(encoded).hexdigest())


def test_preparation_is_deterministic_offline_and_keeps_expectations_out_of_requests(monkeypatch):
    import socket
    monkeypatch.setattr(socket, 'socket', lambda *a, **kw: pytest.fail('network access'))
    manifest, raw, text = fixture()
    bundle = compile_fixture(manifest, raw, text)
    assert bundle == compile_fixture(manifest, raw, text)
    assert bundle['approval_status'] == 'not_authorized'
    assert bundle['limits']['reserved_cents_total'] == 15
    for row in bundle['requests']:
        request = row['request']
        assert 'SECRET EXPECTED ANSWER' not in json.dumps(request)
        assert request['tools'] == [] and request['store'] is False
        assert row['request_sha256'] == sha256(canonical_bytes(request)).hexdigest()
        assert row['publication_age_days_observed'] is None


@pytest.mark.parametrize('change', ['excluded', 'duplicate', 'wrong_slot'])
def test_cohort_cannot_substitute_or_reuse_packets(change):
    manifest, raw, text = fixture()
    packets = manifest['analysis_eligible_packets']
    if change == 'excluded': manifest['excluded_after_landing'].append(packets[0]['evidence_id'])
    if change == 'duplicate': packets[1]['evidence_id'] = packets[0]['evidence_id']
    if change == 'wrong_slot': packets[0]['slot'] = 'M7-CO-1'
    with pytest.raises(ValueError): compile_fixture(manifest, raw, text)


def test_manifest_and_evidence_tampering_are_rejected():
    manifest, raw, text = fixture()
    with pytest.raises(ValueError, match='manifest mismatch'):
        prepare_bundle(canonical_bytes(manifest), lambda _: pytest.fail('loader must not run'))
    with pytest.raises(ValueError, match='Raw evidence'):
        verify_text(manifest['analysis_eligible_packets'][0], raw+b'x', text)
    with pytest.raises(ValueError, match='Extracted evidence'):
        verify_text(manifest['analysis_eligible_packets'][0], raw, text+'x')


def test_complete_serialized_request_has_a_size_gate():
    manifest, _, _ = fixture()
    with pytest.raises(ValueError, match='byte ceiling'):
        prepare_request(manifest['analysis_eligible_packets'][0], 'x'*16000)


def test_path_escape_is_rejected(tmp_path):
    root = tmp_path/'evidence'; root.mkdir()
    (tmp_path/'outside').write_text('outside')
    with pytest.raises(ValueError): contained_file(root, '../outside')


def test_fit_is_independent_and_unknown_fit_cannot_support_a_candidate():
    observation = dict(case_origin='hybrid',identity_resolution='resolved',relationship='current_owner',
                       relationship_time='current_at_signal',operating_status='active',contradiction_state='none',
                       research_disposition='needs_more_research',supported_source_ids=['1'],contradictions=[],
                       unresolved_questions=['Confirm geography'],summary='Fictional fixture',state_fit='unknown',
                       private_company_fit='supported')
    assert observation_errors(observation, {'1'}) == []
    observation['research_disposition'] = 'candidate_supported'
    assert observation_errors(observation, {'1'})
    observation['state_fit'] = 'supported'
    assert observation_errors(observation, {'1'}) == []
    observation['supported_source_ids'] = ['not-in-packet']
    assert observation_errors(observation, {'1'})


def test_cli_loader_preserves_database_and_refuses_lineage_drift(tmp_path, monkeypatch):
    import sqlite3
    from scripts import prepare_milestone7_analysis as command
    from app.research.analysis_preparation import prepare_bundle as compiler
    manifest, raw, text = fixture()
    database = tmp_path/'fixture.db'
    evidence_dir = tmp_path/'evidence'; evidence_dir.mkdir()
    with sqlite3.connect(database) as db:
        db.executescript('CREATE TABLE case_evidence (id,case_id,raw_artifact_id,content_hash,canonical_url);'
                         'CREATE TABLE raw_artifacts (id,content_hash,canonical_url,storage_key,byte_size);')
        for packet in manifest['analysis_eligible_packets']:
            n = packet['evidence_id']
            packet.update(case_id=n, artifact_id=n, text_file=f'text-{n}.txt')
            (tmp_path/packet['text_file']).write_text(text, encoding='utf-8')
            (evidence_dir/f'raw-{n}').write_bytes(raw)
            db.execute('INSERT INTO case_evidence VALUES (?,?,?,?,?)',
                       (n,n,n,packet['raw_sha256'],packet['url']))
            db.execute('INSERT INTO raw_artifacts VALUES (?,?,?,?,?)',
                       (n,packet['raw_sha256'],packet['url'],f'raw-{n}',len(raw)))
    encoded = canonical_bytes(manifest)
    path = tmp_path/'manifest.json'; path.write_bytes(encoded)
    monkeypatch.setattr(command, 'prepare_bundle', lambda payload, loader:
                        compiler(payload, loader, expected_sha256=sha256(encoded).hexdigest()))
    before = database.read_bytes()
    assert len(command.prepare(path, database, evidence_dir)['requests']) == 3
    assert database.read_bytes() == before
    with sqlite3.connect(database) as db:
        db.execute('UPDATE case_evidence SET case_id=999 WHERE id=1')
    with pytest.raises(ValueError, match='lineage mismatch'):
        command.prepare(path, database, evidence_dir)
