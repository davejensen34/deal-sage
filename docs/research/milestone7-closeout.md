# Milestone 7 closeout

September 14, 2026. Issue [#130](https://github.com/davejensen34/deal-sage/issues/130). This closes the approved implementation and comparative evaluation scope with **mixed research results and unpassed live product-quality gates**. It does not certify acquisition recommendations or activate another milestone. The user requested completion and authorized live validation and corrective calls; the existing $5 completion ceiling was retained.

## Acceptance reconciliation

| Recorded requirement | Implementation and observed outcome |
| --- | --- |
| Eight typed signal policies | `transition_policies.py`, ADR-004 and #128 cover mortality, retirement, succession, ownership transfer, founder exit, dissolution, restructuring and leadership change, with separate subject, evidence, time and ownership rules. |
| Existing evidence/review path | #129 integrates typed claims, identity/relationship uncertainty, attributable analyst dispositions and deterministic promotion guards. No automatic executive-to-owner inference or production promotion was used in this evaluation. |
| Business-facing rendered review | #144/#145 provide recent-signal intake and API-derived business briefs. The real Utah/Colorado review and additional Texas brief render source assertions, original model synthesis, deterministic guidance and blank human judgments separately. |
| Comparative regressions | The frozen 64-case cohort was rerun on Windows: 16 eligible simulated review promotions, 48 abstentions, zero failures. Each of eight families has supported, unknown-date, executive, agent-role, name-only, cross-business, contradiction and cancelled-event cases. These are fictional service tests, not live precision. |
| Measures and outcomes | Costs, access misses, analysis failures, timing, source counts and actual human outcomes are recorded below and in the immutable local artifacts. Missing denominators remain unavailable. |
| Product-maintenance checkpoint | This closing change reconciles the milestone, backlog items/index, roadmap, architecture and current state. The definition of done permits explicitly recorded unmet quality outcomes; none is silently declared passed. |

## Additional live validation and correction

The targeted Texas retry found [The Goodman Corporation's ownership announcement](https://www.thegoodmancorp.com/news/ownership-transition), published July 15, 2026, and its [company overview](https://www.thegoodmancorp.com/about). The company reports a planned transfer from founder Barry Goodman to longtime leaders Jim Webb, Robert McHaney and Wendy O'Brian. It describes planning, engineering, project management and funding services from Houston and Austin. The announcement is 61 days old at the frozen September 14 assessment and passes the shared recent-announcement gate. Completion date and equity stakes remain unknown.

This is an explicit ownership-transfer clue, unlike the earlier management-only briefs. It is still company self-report, not independent legal confirmation. Client funding above $2 billion and project totals above $3 billion are **not company revenue**. Financial attractiveness, acquisition availability and verified private-company status remain unknown. Neither source is an independent corroborator of the other.

One additional search, four HTTP actions (two robots checks and two pages), and three analysis attempts ran. The reviewed robots rules allow the requested paths; the retained public pages expose no terms/privacy links or access gate. Limited relevant excerpts were approved for this case-specific analysis, not standing automated collection. No blocked publisher was revisited or bypassed.

- Attempt 77 returned a contract-valid narrative of a planned transfer but an unsupported `began_after_signal` timing label. It remains unchanged.
- Attempt 78 corrected the timing to `unclear` but contained NUL inside a name. It remains unchanged and is excluded from the selected review. This is an observed text-quality defect, not a valid final briefing.
- Completion guidance v4 clarifies planned versus observed succession and faithful names. The completion executor now rejects unexpected control characters with a content-free diagnostic instead of repairing model output silently. Five regression cases cover this observed problem and ordinary Unicode/layout preservation.
- Attempt 79 passed the contract and source comparison: the intended ownership successors remain a clue, timing is `unclear`, private-company fit is `unknown`, and deterministic disposition is `needs_more_research`. No candidate was promoted. Agent source comparison is not human ground truth.

The additional case lives in a newly migrated isolated SQLite database. The original completion corpus, live application database, Mac corpus, prior review packages and failed attempts were preserved. No registry request, Utah BEL lookup, live case acceptance or outreach ran.

## Completion ledger

| Action | Attempts | Outcome |
| --- | ---: | --- |
| OpenAI discovery | 21 | 8 partial narratives with retained references, 13 completed responses; references remain untrusted clues |
| Public HTTP | 49 | 48 returned responses and one inspected redirect; includes robots/policies, not 48 usable articles |
| OpenAI analysis | 9 | 1 contract-invalid and 8 contract-valid at execution; intermediate semantic/text defects are retained, with only attempts 70, 71 and 79 selected for review |
| Total | 79 | $3.60 conservatively reserved, $0.3740345 estimated usage, $1.40 unspent reservation capacity; invoice unavailable |

Reservations include failed and superseded attempts without refunds. Twenty-four observed search-tool actions inform the estimate; the provider sometimes exceeded the requested one-action limit, as recorded in the earlier report. This ledger is the new completion envelope only, not a claim that all historical Milestone 7 research cost $0.37. No further calls are scheduled.

The final retained completion cohort has four business cases across two isolated databases: Visionary Homes (UT), Gazette (CO), Zayo (CO), and Goodman (TX). Three recent packets were analyzed and selected; Zayo remains a date-verification lead. Eight distinct retained text artifacts support nine evidence excerpts. This purposively selected cohort spans three states, **not representative three-state coverage or all-family live validation**. No known source-population denominator or verified positive/negative ownership labels exist, so live precision/recall remain unavailable rather than zero or perfect.

## Explicit quality outcome

The original actual human review remains **0/3 useful**, 3/3 reviewed, with 240 self-reported review seconds. The two newer management briefs have 0/2 recorded judgments; the additional Texas brief has 0/1. These missing judgments are not failures, successes, acceptance, or time saved. The user was invited to review; no ratings were inferred from permission to continue development. Feedback remains importable after milestone closeout, bound to its exact package.

The evaluation demonstrates that discovery can produce attributable, recent business-transition clues and preserve useful uncertainty, including an explicit planned ownership transfer. It **does not pass the product-quality gate for trusted opportunity recommendations**. Source sustainability remains unvalidated: approved company pages were useful in this bounded run, while publisher prohibitions, robots exclusions, sparse permitted obituary material, noisy search references and stale results prevent a claim of unattended reliable coverage. Size/financial corroboration, independent entity/control linkage, representative live precision and renewed actual usefulness remain unproven.

Closing the completed engineering/evaluation scope records these outcomes; it does not waive the gates for future live source activation or calibrated recommendation claims. Future enhancement definition should address those demonstrated gaps and actual reviewer feedback. There is no newly approved milestone, recurring acquisition or automatic #92 rerun.

## Reproducible local assets

All paths below are under ignored `.local-validation/m7-completion/`; no source excerpts, credentials or databases enter the public repository.

| Artifact | SHA-256 |
| --- | --- |
| `texas-bundle.json` | `f782a56da1d3f94834370456d60d47269a076ddaaa17fadc82af429ef6d53e7e` |
| `texas-selected-results.json` | `4e6a174c83612fcaf9b596648e0cb2be459e0bca0eb50b05a2e99e1e8c0112a1` |
| `texas-review-package.json` | `3f902406df46b48f4fd9fdc2293dfee06fca5240bb6fe718d8e7486cb68c5a1b` |

Retain the ledger and every request/result, original and normalized source text, `texas-corpus.sqlite3`, `texas-narratives.json`, `final-summary.json`, `final-offline-evaluation.json` and all earlier artifacts described in [the corrective validation record](milestone7-completion-validation.md). The loopback Texas review uses the actual business-brief component at `http://127.0.0.1:5186/.local-validation/texas-review/index.html`; the earlier review remains separately available. These are local review artifacts, not deployment of the live app or recovery of the Mac research history. Transfer local corpus/evidence using [pilot recovery](../deployment/pilot-recovery.md), with separate secure inventory for secrets and external source files.

Validation: 477 backend/API tests, 24 frontend tests, TypeScript and production build; existing deprecation/chunk warnings remain. The frozen 64-case offline evaluation passed again. The final real-source Texas brief was checked in the browser at desktop and narrow width, with blank judgments and separate evidence/model/context. GitHub CI must pass all five required jobs before the closing PR is merged.
