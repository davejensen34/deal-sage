# Milestone 3.1 bounded public-case validation plan

Status: seven-slot protocol approved and executed September 4, 2026. Results are recorded in `milestone-3-1-live-validation-results.md`; the version-two follow-up is implemented and offline-validated in `../architecture/model-evaluation.md` without reopening this protocol.

## Purpose

This is a product validation exercise, not an unrestricted discovery campaign. It tests whether DealSage can move from a public transition or business signal to a reviewable conclusion while preserving evidence, uncertainty, negative results, and cost. The cohort and limits are declared before research so favorable examples cannot be selected after seeing model output.

## Seven-case cohort

Use retrospective, publicly documented cases distributed across Colorado, Utah, and Texas. Each state should appear at least twice. Utah cases may use bounded official lookups and public web evidence while the separately licensed BEL delivery is pending; this work must not imitate or bypass that dataset.

| Slot | Origin | Expected condition | What it tests |
| --- | --- | --- | --- |
| 1 | signal first | explicit owner/founder relationship with corroborated active business | successful convergence |
| 2 | signal first | explicit owner/founder relationship with corroborated active business | repeatability in another state/source mix |
| 3 | signal first | former owner, sold business, or retired before the transition | temporal/relationship negative evidence |
| 4 | signal first | associated business is inactive, dissolved, or otherwise not operating | operating-status negative evidence |
| 5 | signal first | common name or insufficient geography/timeline support | ambiguity and correct non-resolution |
| 6 | hybrid | credible sources conflict about current ownership | contradiction retention and escalation |
| 7 | business first | public business signal leads to a person and transition evidence | reverse-direction parity |

The exact case manifest is local and ignored until approved. Committed results use case IDs and aggregate measures; they do not turn a validation subject into a published DealSage lead list.

## Selection and approval gate

1. Apply the slot definitions, state balance, and date window before evaluating candidates. Prefer retrospective events from the prior 24 months with enough public evidence to establish an expected condition independently of model output.
2. Use public professional/business facts and public death notices only. Do not collect private contact details, infer sensitive facts, contact families or businesses, or research living relatives beyond what is necessary to interpret an explicit business relationship.
3. During qualification, retain only candidate URLs and short selection notes locally. Stop at paywalls, authentication, CAPTCHAs, robots restrictions, access prohibitions, or unclear reuse terms.
4. Present the proposed seven-slot manifest for human approval before persisting case evidence or making model calls. Replacement cases must satisfy the same pre-declared slot; record the replacement reason.

## Per-case execution budget

- At most 6 search queries.
- At most 8 opened source documents and 5 persisted evidence items.
- At most 2 model calls per provider: one structured extraction and one evidence-bounded analysis.
- At most 20 minutes elapsed research time.
- At most 25 US cents estimated model cost per provider. Stop before a call when the current published price cannot keep the case under this ceiling.
- No retries after a valid response. One retry is permitted only for a transient provider failure and still counts against the two-call limit.

These are ceilings, not targets. Research stops earlier when the expected condition is supported, the identity remains ambiguous after the permitted corroboration attempts, a required source is inaccessible, evidence conflicts require analyst review, or any budget is exhausted.

## Evidence packet and model boundary

Search/acquisition and model reasoning remain separate. DealSage builds one canonical packet per case containing source URL and publisher, source type, publication/event/retrieval dates, content hash, a bounded relevant excerpt, and deterministic normalized facts. OpenAI and Anthropic receive the same packet and versioned task/schema in alternating provider order. Neither provider receives authority to search the web, follow links, alter persisted source material, merge identities, calculate confidence, or change workflow state.

Structured output must distinguish quoted/source-supported claims, uncertainty, contradictions, and proposed next questions. Unsupported output is rejected or labeled; hidden reasoning is never requested or stored. Provider/model, prompt/schema version, latency, token use, estimated cost, outcome, and analyst disposition are retained. OpenAI response storage remains disabled.

## Measures and passing evidence

Report results by case slot and in aggregate:

- exact relationship and temporal-language extraction accuracy;
- operating-status and identity-resolution outcome against the pre-labeled expectation;
- unsupported-claim rate and schema-validation failures;
- contradiction detection and correct ambiguous/non-resolution behavior;
- source references supporting each accepted claim;
- agreement/disagreement between providers and analyst disposition;
- queries, documents, model calls, tokens, estimated cost, latency, and stop reason.

This cohort is too small to establish market conversion rates or statistical superiority. It can expose failure modes and demonstrate whether the workflow is safe, reconstructable, and useful enough to justify broader Milestone 4 evaluation.

## Execution sequence

1. Add keys locally and select one provider at a time.
2. Run the one-call synthetic connectivity check for each provider.
3. Qualify and approve the seven-case manifest without model assistance.
4. Capture and sanitize the shared evidence packets.
5. Pre-label expected outcomes from explicit public evidence.
6. Run both providers within the same limits and compare structured outputs.
7. Perform analyst review, publish aggregate-safe results, and reconcile Milestone 3.1 truth claims.

## Provider smoke-validation record

Synthetic connectivity checks contained no personal or public-case data. OpenAI received two calls: the first reached the provider but exposed an overly exact local response assertion; after that assertion was limited to cosmetic punctuation/whitespace normalization, the repeat passed with 105 total tokens and 2,705 ms latency. Anthropic then passed on its first call with 33 total tokens and 2,323 ms latency. The exercised models were `gpt-5-mini` and `claude-sonnet-4-5`. These results prove local connectivity only, not extraction quality or public-case performance.
