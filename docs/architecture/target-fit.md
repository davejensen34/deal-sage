# Target profiles and deterministic fit

Issue #197 is the first implementation slice of #194. It adds a profile contract and a read-only fit service. It does **not** implement recommendation readiness, corroboration orchestration, automatic claim normalization or recommendation UI.

## Frozen profile

`DiscoverySettings.target_profile` is optional. When absent or null, serialization omits it, retaining legacy preview hashes and creation-key replay. When supplied, the existing defaults/preview/create/read APIs retain its full validated value in the immutable discovery plan. Changing purpose or any criterion changes the plan hash. No migration or additional execution is introduced; discovery still only runs its existing searches.

`target-profile-v1` requires purpose: acquisition exploration, marketing introduction or succession advisory. Company-type and industry criteria contain exact normalized lowercase labels and a required/preferred flag. Acquisition defaults to required private-company fit when company types are omitted; marketing and succession have no automatic company-type constraint. An explicit rule overrides the default and remains visible in the plan. Industry exclusions are hard criteria, and overlapping include/exclude labels are rejected. Size ranges support inclusive minimum and/or maximum, with no default numerical thresholds. Employee bounds count people; annual revenue bounds are whole USD per year, not valuation, EBITDA or quarterly revenue. Boolean/numeric-string coercion is rejected. Discovery's existing geography, transition families and recency remain frozen alongside the profile; this slice does not duplicate or evaluate those gates.

`max_fact_age_days` defaults explicitly to 365 and is configurable from 1 to 3650. This is an eligibility window for target facts, not the transition lookback. It is included in the frozen profile. A recent publication cannot make an old revenue reporting period current.

## Source-normalization boundary

`assess_target_fit` accepts a case, stable business key, validated profile and explicit assessment date. The reconciliation stage must establish that key; this function does not resolve identity from a name. It reads only same-case `EvidenceClaim` records and evidence, writing no scores, inferences, decisions or proposals.

Eligible claims have business subject, asserted status, direct source-fact classification and a matching retained quotation on hashed source-fact evidence. Predicates are `company_type`, `industry`, `employee_count` and `annual_revenue`. Their `object_value` must conform to `target-fact-v1`: version, business key, typed value, unit, observation date and quote. Annual revenue also needs start/end dates for a completed 350–371-day reporting period; its age is measured from period end. Categories use unit `category`; employee count uses `employees`; revenue uses `USD/year`. Negative values, ambiguous units, future/stale dates and malformed records remain in `ignored_claims` with reasons. Different-business records, person claims, model inferences and estimates cannot silently become established fit facts.

This is a contract for **already normalized source assertions**, not a validator of natural-language entailment. Exact quotation does not prove that an employee number refers to this business, that a categorization is correct, or that a publisher is truthful. A future normalization/corroboration adapter must test those semantics before emitting eligible claims. No raw model proposal is automatically converted here. Estimates and other clues remain in the original research record for further investigation rather than being deleted. Source independence, operating status, ownership and sale intent are not established by this service.

## Fit outcomes

Every factor retains claim/evidence IDs, source hash, quote, observed date and reporting period. Factors distinguish met, mismatch, unknown, conflicting and not requested. Different eligible values are conservatively conflicting, even if both fall within a range; an open recorded contradiction also prevents a positive factor. Newer claims never silently override older eligible claims. Explicit supersession/reconciliation is future work.

Required-factor precedence is conflict → unresolved; otherwise mismatch → not fit; otherwise unknown → unresolved; otherwise requirements met. If no required factors exist, the result is no required factors. Preferred misses/unknowns remain visible without blocking required fit. Exclusion criteria need known industry evidence; missing industry is unknown, not proof of no exclusion. Every result explicitly reports `readiness: not_assessed`: requirements met is never permission to promote or recommend a business.

The result includes method `target-fit-v1`, frozen profile/effective company rule, case/business/date context and a deterministic hash over its content. It is an internal read-only assessment service for the upcoming orchestrator, not a new public API or persisted assessment table. Existing source/model/human records remain distinct. UI exposure, saved assessment lifecycle, semantically validated capture and the full readiness gate remain #194 work.

## Validation

Regressions cover purpose defaults, strict fields/types/ranges, required versus preferred criteria, unknown/mismatch/conflict precedence, explicit contradictions, excluded industries, business/case isolation, source classification/quote lineage, time windows, annual reporting periods and repeatable read-only hashing. Discovery tests exercise API defaults/preview/create/read round trips, changed-profile admission and legacy omission/replay. No live research, operational data writes or migration are required for this increment.
