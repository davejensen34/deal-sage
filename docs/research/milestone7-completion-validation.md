# Milestone 7 corrective validation

Milestone 7 is complete as an implemented and evaluated research foundation, with the failed/unmeasured live quality outcomes explicitly retained. No milestone is active. The final completion run made 21 searches, 49 HTTP requests and nine model attempts; $3.60 was reserved and $0.3740345 estimated within the $5 ceiling. Three recent packets span Utah, Colorado and Texas, including a company-reported planned ownership transfer at The Goodman Corporation; Zayo remains a date-verification lead. No cases were promoted. The original human review remains 0/3 useful; newer review coverage is 0/2 and 0/1, with usefulness unmeasured. Representative precision, independent ownership/financial corroboration and sustainable unattended sources are not validated. All 477 backend/API tests, 24 frontend tests, TypeScript/build and rendered review checks passed. [Final acceptance reconciliation](milestone7-closeout.md). The following checkpoint history is preserved; earlier active/approval statements describe their recorded point in time.

Issue [#130](https://github.com/davejensen34/deal-sage/issues/130), September 14, 2026. Branch: `codex/research-130-completion-validation`. This is an observed validation record, not a milestone closeout or an acquisition recommendation.

## Authorization and execution

The user explicitly approved $5 **incremental** spending for discovery, permitted public retrieval, enrichment, public-source packets sent to OpenAI, and corrective retries. Routine failures no longer require another approval. Stop at the shared budget ceiling, material access/privacy issues, or actual human usefulness review. Earlier one-shot claims/results and the prior 0/3 useful human review remain immutable. Issue #92 was not rerun.

One ignored `.local-validation/m7-completion/ledger.json` accounts for all new network actions. Each request is written and reserved before I/O, results are immutable, and a process lock prevents concurrent spend. Request/result hashes are checked before continuing. Search reserves 15 cents; analysis reserves five; failures do not refund either. HTTP requests cost zero and have an 80-request ceiling. A protocol flag records the operator's existing authorization; it does not independently grant permission or make a new directory a new budget.

| Action | Observed count | Outcome | Estimated USD |
| --- | ---: | --- | ---: |
| OpenAI discovery | 20 | 8 incomplete narratives with retained references; 12 completed | 0.32336225 |
| Public HTTP, including robots/policies | 45 | 44 returned responses, one inspected redirect | 0 |
| OpenAI analysis | 6 | 1 consistency-invalid, 5 contract-valid; latest two selected for review | 0.02278250 |
| Total | 71 | No promotions or live application database writes | **0.34614475** |

Conservative reservations total **$3.30**, leaving **$1.70** in this envelope. Actual invoice charges are unavailable. Search estimates use returned token counts and the 23 observed search-tool actions; three responses contained two actions despite the requested `max_tool_calls=1`. This provider observation is retained, not represented as a successfully enforced one-action limit. Searches yielded 100 references / 95 distinct URLs; those are clues, not 95 validated sources or matches.

## Failures corrected without erasing attempts

- A new response demonstrated that `incomplete / max_output_tokens` can still contain usable consulted-source references. The completion runner retains these as untrusted clues. Failed, content-filtered or unexpected-model responses cannot supply clues. This does not retrospectively establish the exact cause of the earlier discarded discovery response.
- Increasing the bounded narrative allowance and refining broad legal-noise queries produced completed search responses. Older announcements, generic legal advice, inaccessible pages and irrelevant businesses were not forced into the cohort.
- Windows text-mode writes expanded LF into CRLF after the original hash calculation. Future retrieval writes the exact hashed UTF-8 bytes. Original files and the failed isolated import are preserved; explicit LF-normalized derivatives reproduce the recorded canonical-text hash, with original file hashes and the transformation recorded in artifact metadata. These are retained **extracted text** artifacts; the HTML hash is an observation, not retained replayable HTML.
- One analysis failed `relationship_time_conflicts_with_relationship`. Subsequent source comparison also found management successors labeled as ownership successors and unsupported private-company fit. Versioned additive request guidance makes the existing enum meanings/allowed pairs explicit, requires affirmative private-status evidence, and preserves future management details in prose when the timing vocabulary cannot represent them. Source context is unchanged by guidance; exact effective requests are separately retained.
- An additional exact excerpt from the already retained company announcement answered questions omitted from the first curation. It is another evidence excerpt of the **same document**, not independent corroboration. Both frozen bundle versions and every result remain available.

The latest two observations preserve management-transition information with `non_owner_role`; deterministic ownership-relationship disposition is `no_qualifying_relationship`. This does not discard the useful research clue, establish absence of shares, or authorize promotion. The earlier contract-valid ownership-successor misclassification remains a recorded semantic failure, not a quality success.

## Source selection and limits

The shared intake policy uses a 90-day lookback ending September 14, 2026. Discovery date hints are not proof of event dates. A new, migrated, isolated SQLite corpus contains three cases, six distinct text artifacts and seven evidence excerpts. The actual `research_case_narratives` API projection produced the review's business briefs.

| Case | Source/date result | Treatment |
| --- | --- | --- |
| Visionary Homes, Utah | Company announcement June 24; CEO effective September 1 was planned; co-founder chairman transition planned January 1, 2027 | Recent announcement of a future plan qualifies. Retain the passed CEO date as unconfirmed separately. Company overview supplies activity/geography; the 2,000-home-start figure is a goal, not actual output or revenue. |
| Gazette newspaper chain, Colorado | August 5 third-party opinion article reports an editorial-management change, referring to July 19 reporting | Qualifies as a recent announcement with unknown exact event date. Retain only relevant reported business/role information, excluding political commentary. Private status, legal-entity linkage and independent confirmation remain unknown. |
| Zayo, Colorado | July 14 announcement planned September 1 CEO change; current undated company biography names the successor | Retained date-verification lead, not analyzed. The biography corroborates the role but not its exact effective date. Prior-employer revenue/employee figures are not Zayo financials; investor-relations address is not operating coverage. |

Utah Business and PR Newswire content was excluded from packets after their terms prohibited automated use; the completion retriever now blocks those publishers. TPx's robots policy disallowed DealSage retrieval and was respected. No alias, authentication, paywall or browser workaround was used. One broker page yielded only a site title, not a usable article. An old obituary, older Texas transitions, expansion-only material, statutes and generic advice remain misses/background. Independent company material was used for Visionary Homes, not the excluded distributor's text.

There is **no qualifying Texas packet**, no new registry request or Utah BEL lookup, no verified owner/opportunity match, and no measured revenue, EBITDA or workforce for these selected businesses. This small curated cohort cannot demonstrate three-state coverage, per-family live precision, financial attractiveness or sustainable unattended acquisition. Human usefulness is a separate gate; the new review currently has **0/2 reviewed**, not 0/2 useful. The prior cohort remains **0/3 useful**.

## Frozen review and local operation

| Artifact | SHA-256 |
| --- | --- |
| Final source bundle | `8a323cdcab41fe0184b1f689b91bcf5dc354bd058dc207fee0b30ae204324a26` |
| Selected-results manifest, attempts 70/71 | `d431eec3152c85b21a0e008f7788517f3ffef2d10b30e71a2d1a81ba13034f38` |
| New human-review package | `9b8db67e21342f64fc25d67dba3005daac72536b30719610361a635f36ad2bbe` |

The package is explicitly recognized by the offline usefulness summarizer alongside the historical package. Cross-cohort feedback is rejected. The ignored loopback review harness at `apps/web/.local-validation/completion-review/index.html` uses the existing business-brief and feedback-export components. It loads the actual local artifacts, leaves all judgments blank, and writes no application records. Its preview is `http://127.0.0.1:5186/.local-validation/completion-review/index.html`. The package also works with the existing local-file evaluation review route. The Mac research corpus and the live Windows application database are separate and unchanged.

Run backend commands from `apps/api`. The completion tools are operator commands, not scheduled or automatic product features:

```text
.venv/Scripts/python.exe -m scripts.milestone7_completion --help
.venv/Scripts/python.exe -m scripts.milestone7_public_page --help
.venv/Scripts/python.exe -m scripts.milestone7_completion_analysis --help
.venv/Scripts/python.exe -m scripts.summarize_milestone7_feedback --package ../../.local-validation/m7-completion/review-package.json --feedback <explicit-human-export> --output <new-summary-file>
```

Use the existing shared ledger for any authorized follow-up. Review publisher rules before model use; a successful HTTP response or permissive robots file is not standalone permission. Secrets remain in `.env` and are never included in these artifacts or commits.

Validation: **471 backend/API tests**, **24 frontend tests**, TypeScript and production build passed; existing deprecation and large-chunk warnings remain. The real-source review was inspected at 1280px and 390px with no horizontal overflow, source/model separation, blank judgments and rejection of an empty feedback export. This is rendered review validation, not a claim that the live application was redeployed. Milestone 7 remains open for actual human judgment and the unresolved quality/sustainability decision.
