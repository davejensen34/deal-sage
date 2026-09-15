# Milestone 8 acceptance acquisition and review

Subsequent user feedback: these packets are too light on insight for reviewer handoff. The review request below is **suspended**, and #194 must deliver discovery/capture/corroboration/reconciliation and supported recommendations before #187 resumes. This is diagnostic acquisition history, not ten individual usefulness judgments or a completed intelligence transaction. [Remediation plan](../product/milestone8-intelligence-remediation.md).

September 15, 2026. Issue #187 remains open. Live acquisition is complete; usefulness and unassisted human workflow completion are **not assessed**. This record does not close Milestone 8.

## Scope and retained execution

The user approved the [acceptance protocol](milestone8-human-acceptance.md): public-business introductions, CO/UT/TX, 90 days ending September 15. Six exact possible-death/succession queries were frozen in discovery run 1 before execution. The isolated OIDC app uses a fresh evaluation database and evidence directory under `.local-validation/m8-acceptance/`; it is not the retained operational research corpus. Existing operator identity was preserved. Secrets remain in local environment configuration.

| Operation | Observed result | Approved maximum |
| --- | --- | --- |
| Search | 6 succeeded; 30 distinct unverified links | 12 attempts |
| Document retrieval | 19 attempts: 18 succeeded, 1 failed | 30 documents |
| All source HTTP requests | 27, including 8 robots checks | Conservatively held below 30 |
| Cited extraction | 13 attempts: 9 completed, 3 invalid, 1 incomplete | 20 attempts; at most 2 per case |
| Saved case views | 10 immutable version-1 briefs | 10 selected leads |
| Human judgments | 0/10 at preparation | 10, with reasons and review seconds |

Search reserved 72 cents and extraction reserved 26 cents: **98 cents reserved** against the $5 ceiling. No failed reservation was refunded. Model usage totaled 9,438 input and 7,648 output tokens; the frozen rates imply $0.0176555 before per-attempt rounding, while the persisted rounded estimates sum to 13 cents. Search actual spend, invoices and infrastructure costs are unknown. These are not interchangeable totals or a claim of measured total spend. There were no automatic retries, outbound communications or candidate promotions.

The initial raw-HTML excerpt failure was fixed through Issue #189 / PR #190; raw artifact hashes remained intact. Issue #191 / PR #192 froze minimal reasoning under the same model/token/cost limits after the first extraction returned incomplete. Its explicit retry completed. Mo’ Bettahs and Redemption Bank each received one further attempt on an already-retained context excerpt after invalid primary output: Redemption completed; Mo’ Bettahs remained invalid and exhausted its per-case allowance. Source evidence remains available when model extraction fails. No failed output was promoted or substituted with invented observations.

## Selection and limits

All 30 search links remain in discovery order. Eight original links were considered for retrieval: one was excluded after a robots access failure; seven document attempts yielded six retained documents and one failure. Retained Colorado transaction pages contained anonymous businesses; the alternate Utah listing was a loading/subscription shell. Two Texas articles declared metered access and were excluded from readable extraction. Other search links remain unverified or uninspected; broad advice, archive and statute results are not established recent business matches. This is bounded acquisition, not exhaustive examination of every linked page.

The retained Utah Business listing (original source 11, artifact 3) supplied 20 ordered article cards. Twelve business/service-provider articles were retrieved. Two were excluded from the ten-lead cohort because retained text did not establish in-scope business geography: Palladyne AI and Phygital International (cases 6 and 8). A person's Salt Lake City connection does not establish the company's geography. Five university/civic/charitable governance cards were excluded by the agent's business-scope interpretation; a second Bank of Utah card was a duplicate business. Two later cards were beyond the ten selected leads and were not retrieved. These selection judgments and excluded cases remain inspectable; they are not usefulness ratings.

All ten selected leads therefore come from **one Utah publisher**, largely company-supplied announcements. The cohort includes public companies and a hospital operator for the marketing-introduction purpose. It does not validate private-company acquisition fit, independent corroboration, broad geographic coverage or population precision. The agent assembled source-linked cases and saved views using existing services; this does not demonstrate unassisted human completion of the app workflow. Publication dates establish inspectable announcements, not necessarily event occurrence. No typed authoritative transition/ownership claims were added to make the date gate appear passed.

## Frozen review queue

Each case has brief version **1**, original source URL/hash, readable evidence and separate unreviewed model interpretations. Context excerpts share the original artifact and are not independent corroboration.

| Case | Business | Publication | Model result |
| --- | --- | --- | --- |
| 2 | Mo’ Bettahs | September 3 | Two invalid attempts; review source evidence |
| 3 | Highcountry Wealth Management | September 3 | Completed after incomplete attempt |
| 4 | Extra Space Storage Inc. | August 28 | Completed |
| 5 | Bank of Utah | August 28 | Completed |
| 7 | Helix Electric of Utah | August 28 | Completed |
| 9 | WireTech | July 22 | Completed |
| 10 | Stein Collection | July 22 | Completed |
| 11 | CommonSpirit Health | July 22 | Completed |
| 12 | Swire Coca-Cola, USA | July 22 | Completed |
| 13 | Redemption Bank | July 22 | Context extraction completed after invalid attempt |

Completed extraction is not semantic validation. Observed errors include partner/branch/years-of-experience figures labeled employee counts, a stock ticker labeled business website, people labeled business names, and publication dates labeled event dates. Exact quotations passed, but field meanings can still be wrong. These original proposals remain labeled unreviewed; authoritative scores, claims and human decisions were not changed. Source-supported financial clues are uncorroborated, ownership and sale intent are unestablished, and no public-contact readiness review has been supplied. Human acceptance must check the selected briefs for critical fabricated ownership or sale claims.

## Actual reviewer steps

Use the running acceptance app at `http://localhost:3000`, authenticated with the existing Google operator account. Open `/research/cases/{case}` for each case above. Under **Reviewer decision**, load reviewed brief version **1**, select **Marketing introduction**, choose the appropriate outcome, and enter your rationale, next action and supporting sources. Complete **Usefulness for this purpose**, **Usefulness reason** and **Self-reported review seconds**. Record your own judgment, including not-useful outcomes; no target should influence an individual rating. The target is at least six useful out of ten, with all ten assessed. Time saved has no measured baseline.

Separately complete the five hands-on tasks: start signal-first research with no business name, inspect uncertain evidence, execute a permitted follow-up, save a reasoned decision, and retrieve a development brief or monitoring item. Include a no-match case, such as one of the retained geography exclusions. Record friction and whether assistance was needed. The fictional app at `http://127.0.0.1:5186` can exercise these workflow tasks without new external spend; live acquisition results and fictional workflow observations must remain separately labeled. The agent has not counted its own actions as your five tasks.

## Reproducibility and remaining gate

Local-only files retain the exact frozen plan, original search results, ordered listing selection, HTTP attempt ledger, frozen cohort, source artifacts, database and review manifest with saved-version hashes.

- Discovery plan hash: `deb52ac4055e2af46994ef741bdab6f633645958e32e2df84229833fd9de3bfd`.
- Frozen plan file SHA-256: `7cc5e7f4a88a7a0b2b3712d7aa1bc8887c64262ffcaa3f2aee0a7c5372087a3b`.
- Frozen cohort file SHA-256: `c38bf8db33337c1ac2e587102d3383ffc4d6c326227fdb6b60c046258732073a`.

Source bodies and the evaluation database are intentionally not published to GitHub. Preserve them with the repository recovery procedure and a separate inventory of these local-only manifests; a clone does not reproduce this run.

Validation: 566 backend/API tests passed for the extraction fix; all five PR #192 CI jobs passed. PR #190 likewise passed all five jobs. The restarted live app rendered readable source evidence, failed/completed extraction history and the saved brief in the authenticated reviewer form. No new frontend code was introduced by these fixes. Remaining completion requirements are the actual human ratings/timings and five-task observations, remediation of material findings, then the reconciled closeout PR. No next milestone is activated.
