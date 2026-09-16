"""Preserve quoted model clues and explain the next corroboration work.

Narrow lexical checks detect known type mistakes; they do not establish semantic
truth, resolve a business identity, or authorize research/provider calls.
"""
from datetime import date, datetime
import re
from urllib.parse import urlsplit

from jsonschema import ValidationError, validate
from sqlalchemy import select

from app.domain.models import CaseEvidence, ExtractionAttempt, ModelProposal
from app.research import extraction_attempts as extraction, extraction_batches as batches
from app.research.retrieval import assert_nonlocal_url
from app.research.search import canonicalize_public_url
from app.research.target_fit import TargetProfile

VERSION = 'extraction-clue-assessment-v1'
DATE_FIELDS = {'event_date', 'announcement_date', 'planned_event_date'}


def check(observation, packet, assessment_date):
    """Return diagnostic interpretation with the original observation intact."""
    field, value, quote = (observation[k] for k in ('field', 'value', 'quote'))
    result = {'original': dict(observation), 'interpretation': 'unverified_clue',
              'normalized': None, 'reasons': [], 'eligible_for_fit': False}
    reasons = result['reasons']
    if not quote.strip() or quote not in packet['excerpt'] or not value.strip() or value not in quote:
        result['interpretation'] = 'citation_mismatch'
        reasons.append('quote_or_value_not_in_frozen_passage')
        return result
    if observation['certainty'] == 'tentative':
        reasons.append('model_marked_tentative')
    if field == 'employee_count':
        # A number elsewhere in a sentence mentioning employees is insufficient.
        # Require this exact value next to a workforce unit, with no range/estimate.
        number = re.fullmatch(r'(?:0|[1-9]\d{0,8}|[1-9]\d{0,2}(?:,\d{3}){1,2})', value)
        unit = re.search(r'(?<![\w\d,.])' + re.escape(value) + r'\s+(?:full-time\s+|part-time\s+)?employees\b', quote, re.I)
        employs = re.search(r'\bemploys\s+' + re.escape(value) + r'\s+(?:people|staff)\b', quote, re.I)
        qualified = re.search(r'\b(?:about|approximately|over|under|more than|less than|between|up to|nearly|no|not|former|previously|per branch|per location)\b|\d\s*[-–+]\s*\d?', quote, re.I)
        if number and (unit or employs) and not qualified:
            result['normalized'] = {'value': int(value.replace(',', '')), 'unit': 'employees'}
            reasons.append('explicit_workforce_unit_in_quote')
        else:
            result['interpretation'] = 'needs_context'
            reasons.append('workforce_value_or_unit_ambiguous')
        reasons.append('business_subject_and_observation_date_unresolved')
    elif field == 'business_website':
        try:
            parts = urlsplit(value)
            if parts.username or parts.password or re.search(r'\s', value) or '.' not in (parts.hostname or ''):
                raise ValueError('Not an ordinary public URL')
            canonical, _ = canonicalize_public_url(value)
            assert_nonlocal_url(canonical)
        except ValueError:
            result['interpretation'] = 'needs_context'
            reasons.append('value_is_not_a_public_http_url')
        else:
            result['normalized'] = {'url': canonical}
            reasons.append('url_syntax_only_business_affiliation_unverified')
    elif field in DATE_FIELDS:
        parsed = None
        for fmt in ('%Y-%m-%d', '%B %d, %Y', '%b %d, %Y'):
            try:
                parsed = datetime.strptime(value, fmt).date()
                break
            except ValueError:
                pass
        if parsed:
            result['normalized'] = {'date': parsed.isoformat(), 'proposed_date_role': field}
            if parsed > assessment_date:
                reasons.append('future_date_not_a_completed_transition')
        else:
            reasons.append('exact_date_unresolved')
        if field == 'event_date' and re.search(r'\b(?:published|posted|publication|announced|announcement)\b', quote, re.I):
            reasons.append('announcement_or_publication_is_not_event_timing')
        if field == 'event_date' and re.search(r'\b(?:will|plans?|planned|expected|scheduled|intends?)\b', quote, re.I):
            reasons.append('planned_language_not_completed_event')
        result['interpretation'] = 'needs_context'
        reasons.append('date_role_requires_event_context')
    elif field == 'business_name':
        name = re.escape(value)
        if re.search(name + r'\s*,?\s+(?:(?:the|a|an)\s+)?(?:CEO|president|chairman|chairwoman|director|founder|owner|he|she)\b', quote, re.I):
            reasons.append('person_role_may_be_mislabeled_business')
            result['interpretation'] = 'needs_context'
        reasons.append('name_alone_does_not_resolve_business_identity')
    elif field == 'reported_relationship':
        reasons.append('role_does_not_establish_ownership_or_sale_intent')
    elif field in {'revenue', 'ebitda'}:
        result['interpretation'] = 'needs_context'
        reasons.append('currency_period_business_subject_and_measure_require_reconciliation')
    else:
        reasons.append('field_meaning_requires_corroboration')
    return result


def questions(profile, observations):
    """Prioritize gaps without treating absent/mislabeled clues as false facts."""
    groups = [
        ('business_identity', 100, True, ['business_name', 'location', 'business_website'],
         'Resolve each business using its location and official business context; separate people and same-name businesses.'),
        ('transition_timing', 95, True, ['transition_description', *sorted(DATE_FIELDS), 'reported_relationship'],
         'Establish what changed, to whom and when; distinguish publication, announcement, planned and completed events.'),
        ('independent_support', 90, True, [],
         'Seek independently originated supporting or conflicting evidence; repeated publisher content is not corroboration.'),
    ]
    if profile.effective_company_types():
        groups.append(('company_type', 85, profile.effective_company_types().required, ['business_name', 'reported_relationship'],
                       'Establish the business company type for this purpose without treating executive or agent roles as ownership.'))
    if profile.industries or profile.excluded_industries:
        groups.append(('industry', 80, bool(profile.excluded_industries) or profile.industries.required, ['industry', 'business_activity'],
                       'Verify current business activity against included and excluded industries.'))
    for factor, rule, fields, question in [
        ('employee_count', profile.employees, ['employee_count'], 'Establish current employee count for the correct business; distinguish branches, partners and years of tenure.'),
        ('annual_revenue', profile.annual_revenue_usd, ['revenue'], 'Find business-specific annual revenue with currency and reporting period; retain missing financials as unknown.'),
    ]:
        if rule:
            groups.append((factor, 80 if rule.required else 50, rule.required, fields, question))
    result = []
    for key, priority, required, fields, question in groups:
        relevant = [o for o in observations if key == 'independent_support' or o['original']['field'] in fields]
        result.append({'key': key, 'priority': priority if required else min(priority, 50),
            'required': required, 'question': question,
            'state': 'needs_corroboration' if relevant else 'missing_evidence',
            'observation_refs': [o['ref'] for o in relevant],
            'ambiguous_refs': [o['ref'] for o in relevant if o['interpretation'] != 'unverified_clue']})
    return sorted(result, key=lambda q: (-q['priority'], q['key']))


def assess(db, case_id, batch_id, *, assessment_date: date):
    row = batches.require_batch(db, case_id, batch_id)
    if extraction.digest(row.plan) != row.plan_hash:
        raise ValueError('Frozen batch plan integrity check failed')
    profile = TargetProfile.model_validate(row.plan['settings']['target_profile'])
    steps = {batches.child_key(row, i): step for i, step in enumerate(row.plan['steps'])}
    attempts = db.scalars(select(ExtractionAttempt).where(ExtractionAttempt.case_id == case_id,
        ExtractionAttempt.actor_key == batches.child_actor_key(row), ExtractionAttempt.request_key.in_(steps))
        .order_by(ExtractionAttempt.id)).all()
    observations, outcomes, seen, publishers, source_hashes = [], [], {}, set(), set()
    for attempt in attempts:
        step = steps[attempt.request_key]
        proposal = db.get(ModelProposal, attempt.proposal_id) if attempt.proposal_id else None
        source = db.get(CaseEvidence, attempt.evidence_id)
        outcome = {'attempt_id': attempt.id, 'proposal_id': attempt.proposal_id, 'status': attempt.status,
                   'assessment': 'no_completed_output'}
        outcome['input_hash'] = extraction.digest([attempt.plan, attempt.plan_hash, attempt.evidence_id,
            None if source is None else [source.case_id, source.content_hash],
            None if proposal is None else [proposal.case_id, proposal.task, proposal.execution_outcome,
                proposal.supported_evidence_ids, proposal.proposed_output]])
        outcomes.append(outcome)
        if attempt.status != 'completed':
            continue
        if (attempt.plan_hash != step['plan_hash'] or extraction.digest(attempt.plan) != step['plan_hash']
            or attempt.evidence_id != step['evidence_id'] or source is None or source.case_id != case_id
            or source.content_hash != attempt.plan['packet']['content_hash'] or proposal is None
            or proposal.case_id != case_id or proposal.task != 'business_extraction'
            or proposal.execution_outcome != 'completed' or proposal.supported_evidence_ids != [source.id]):
            outcome['assessment'] = 'invalid_lineage'
            continue
        try:
            validate(proposal.proposed_output, extraction.SCHEMA)
        except ValidationError:
            outcome['assessment'] = 'invalid_output_shape'
            continue
        outcome['assessment'] = 'clues_assessed'
        outcome['output_hash'] = extraction.digest(proposal.proposed_output)
        outcome['model_questions'] = proposal.proposed_output['unresolved_questions']
        source_hashes.add(source.content_hash)
        publishers.add((attempt.plan['packet']['publisher'] or '').strip().casefold())
        for index, original in enumerate(proposal.proposed_output['observations']):
            clue = check(original, attempt.plan['packet'], assessment_date)
            clue.update({'ref': f'{attempt.id}:{index}', 'attempt_id': attempt.id, 'proposal_id': proposal.id,
                'evidence_id': source.id, 'content_hash': source.content_hash,
                'passage': attempt.plan['packet'].get('source_passage'),
                'publisher': attempt.plan['packet']['publisher']})
            signature = extraction.digest([source.content_hash, original['field'], original['value'], original['quote']])
            clue['duplicate_of'] = seen.get(signature)
            seen.setdefault(signature, clue['ref'])
            observations.append(clue)
    competing = []
    for field in sorted({o['original']['field'] for o in observations}):
        members = [o for o in observations if o['original']['field'] == field and not o['duplicate_of']
                   and o['interpretation'] != 'citation_mismatch']
        if len({o['original']['value'].casefold() for o in members}) > 1:
            competing.append({'field': field, 'observation_refs': [o['ref'] for o in members],
                'state': 'subjects_or_periods_may_differ', 'confirmed_contradiction': False})
    result = {'method': VERSION, 'case_id': case_id, 'batch_id': batch_id, 'batch_plan_hash': row.plan_hash,
        'batch_status': row.status, 'assessment_date': assessment_date.isoformat(), 'profile': profile.model_dump(),
        'observations': observations, 'attempt_outcomes': outcomes, 'competing_clues': competing,
        'questions': questions(profile, observations), 'coverage': row.plan['coverage'],
        'uninspected_evidence': row.plan['uninspected_evidence'],
        'support': {'distinct_content_hashes': len(source_hashes), 'distinct_publisher_labels': len(publishers - {''}),
                    'independence': 'not_established'},
        'readiness': 'not_assessed', 'authoritative_claims_created': 0}
    result['content_hash'] = extraction.digest(result)
    return result
