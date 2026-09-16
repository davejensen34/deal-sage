# Extraction clues and corroboration gaps

Issue #203 adds a deterministic read-only interpretation of #201 batch output. Exact quotation is a citation check, not proof that a model chose the correct field. This stage retains observations as useful research clues while identifying the next questions. It does not resolve business identity, establish facts, execute searches, calculate target fit or recommend opportunities.

## Contract

Authenticated readers call `GET /api/research/cases/{case_id}/extraction-batches/{batch_id}/assessment?assessment_date=2026-09-16`. The optional date defaults to the UTC date. `extraction-clue-assessment-v1` returns the batch status/profile, considered document coverage, attempt outcomes, original observations, diagnostic reasons, limited normalization, possible competing clues and prioritized questions. Each clue carries attempt/proposal/evidence identifiers, source hash, frozen publisher and passage metadata. Method, input fingerprints, reference date and result hash make repeat reads inspectable. This is a computed view, not a newly saved immutable assessment version.

The batch plan/hash, selected child plan/hash, evidence association, proposal case/task/outcome and supported evidence must agree. Malformed or cross-case output cannot contribute observations. Failed/unknown/pending attempts remain outcomes, not negative business findings. Original completed model observations and unresolved questions remain unchanged; no claims, audit events, scores, human decisions or other database records are written by this endpoint. Source bytes are not reread and no external calls occur.

## Narrow diagnostics

- Workforce clues require an integer adjacent to an employee unit, or an explicit “employs N people/staff” phrase. Partner/branch/tenure counts, decimals, ranges, estimates and several negated/historical qualifiers require more context. A recognized count still lacks reconciled business identity, population scope and observation date, so it is not an authoritative fit input.
- Website clues require ordinary public HTTP URL syntax. Tickers, non-URL text, credentials and obvious local hosts are flagged. Valid syntax does not establish affiliation, availability, publisher permission or safe network resolution. No URL is fetched or authorized by this check.
- Exact ISO or English month-name dates can be normalized as clues. Publication/announcement wording, planned language and future dates cannot silently become completed transitions. Year-only or other ambiguous dates remain unresolved. Date roles still require contextual interpretation.
- A quoted name adjacent to a person role can indicate a mislabeled business name. All names still require identity reconciliation; name-only matching is insufficient. Reported roles remain relationship clues and do not automatically establish ownership or sale intent. Financials retain currency, period, subject and measure questions rather than becoming invented annual revenue.

These are deliberately narrow lexical checks, not general natural-language entailment or truth verification. A clean diagnostic is not a verified observation; unsupported patterns remain clues. Every observation has `eligible_for_fit: false`, and the result has `readiness: not_assessed`. The existing target-fit service continues to require its separately typed, cited and reconciled source claims. No old observation is removed for being ambiguous or “unverifiable.”

## Reconciliation work and priorities

Exact same-source/field/value/quote repeats link to their first observation while preserving every original. Distinct content hashes and publisher labels are reported, but independence is never inferred from those counts. Different values under the same field are possible competing clues: subjects, dates, units or reporting periods may differ. They are not automatically entered as contradictions or merged under a common business name.

Questions prioritize business identity, transition timing and independently originated support, then frozen profile factors. Required factors precede optional size preferences; acquisition's private-company criterion does not silently apply to marketing. Each question references related observations and diagnostic ambiguities. Missing evidence stays unknown, not mismatch. Question text and priorities are deterministic planning input; model-generated questions remain separately labeled in attempt outcomes and cannot supply executable instructions.

The next orchestration stage must resolve subjects and dates, generate and execute bounded corroborating queries, preserve source-access boundaries and feed a versioned cited assessment. This endpoint does not establish the end-to-end intelligence outcome, and #187 acceptance remains paused for #194.

## Validation

All 658 backend/API tests pass. Regressions use fictional examples of the retained failure patterns: partner/branch/tenure versus employees, person versus business, ticker versus website, publication/planned/future dates and ambiguous financials. Tests also cover positive quoted unit clues, duplicate preservation, competing subjects, required versus preferred factors, stable fingerprints, unchanged records, invalid lineage/output, pending batches and case-scoped viewer access. No UI change, migration, live source/model call or operational-corpus write occurred.
