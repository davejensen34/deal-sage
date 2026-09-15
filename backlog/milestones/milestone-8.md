# Milestone 8 — Reviewer Workbench and Opportunity Development

Status: in_progress. The user approved activation September 15, 2026 after planning PR #155. GitHub milestone [13](https://github.com/davejensen34/deal-sage/milestone/13) tracks execution. Milestone 7 remains closed with its recorded quality limitations.

## Execution record

- 8.1: [Issue #156](https://github.com/davejensen34/deal-sage/issues/156) implements a paginated case-first landing inbox, individual case URLs, state/signal/date filters, candidate provenance, dependable error states, role-aware candidate actions and pilot sign-out. Existing research and candidate routes remain supported. No new scoring, research execution or promotion is introduced.
- 8.1 validation: 481 backend/API tests, 30 frontend tests and TypeScript/production build passed (existing large-chunk warning). Rendered desktop/390px, keyboard case navigation, Utah filter, provenance expansion and missing-candidate screen were inspected against a fresh fictional database with disabled providers. Health responded `ok`. No live calls or research-corpus changes. Large-corpus filtering and fresh Google sign-in were not exercised.
- 8.2: [Issue #158](https://github.com/davejensen34/deal-sage/issues/158) implements discovery setup, versioned SQL defaults, frozen request/policy/provider limits and durable operator-controlled attempts. Reservations precede calls; duplicate keys/concurrent claims cannot repeat execution. Bounded retry retains failure history; interrupted recovery keeps unknown outcomes/reservations and rejects late responses. Case links expose unverified clues, not evidence or established matches.
- 8.2 validation: 490 backend/API tests, 32 frontend tests and TypeScript/production build passed (existing chunk warning). Desktop/390px fictional preview → save → execute → reload/history → case-clue navigation was inspected without page overflow. Migration/reopen/retry, permissions, caps, provider drift/pricing expiry, concurrency and recovery tests pass. No live calls or operational-corpus changes. Live search is limited to the reviewed pinned-model pricing envelope through September 21, 2026; stale/config-changed providers require a new reviewed plan.
- 8.2 usability follow-up [Issue #160](https://github.com/davejensen34/deal-sage/issues/160): show the required state × family query count before submission and offer an explicit attempt-limit adjustment without changing spend limits. The reported CO/TX six-family selection now previews successfully; 33 frontend tests and build pass, rendered demo inspected, no live calls.
- 8.3 first slice: [Issue #162](https://github.com/davejensen34/deal-sage/issues/162) connects attributable source-access review and paginated retained evidence/claim inspection to case pages. Atomic access decisions preserve history; approval neither verifies evidence nor retrieves content. 492 backend/API tests, 35 frontend tests and build pass; fictional desktop/390px review inspected without overflow. No live calls or migration.
- 8.3 remains in progress for bounded retrieval/extraction/frontier execution and versioned brief updates; 8.4–8.6 remain pending. The live cohort and cost envelope must be frozen before validation calls.


## Outcome

A reviewer can start bounded discovery, inspect recent business-transition evidence, ask a targeted follow-up, record a reasoned decision and create a useful opportunity-development handoff **inside DealSage**, without a coding agent or local JSON exchange.

The objective includes relevant marketing/business introductions, succession/continuity advisory and acquisition exploration. Purpose changes what evidence a decision needs; it does not change the truth of a source claim. A death or executive departure never establishes sale intent, successor ownership or distress.

Inputs: [whole-app audit](../../docs/product/reviewer-workflow-audit.md), [interaction concept](../../docs/product/design/milestone-8/index.html), [Milestone 7 quality outcome](../../docs/research/milestone7-closeout.md).

## Approved increments

Each increment receives an implementation-ready Issue, short-lived branch, PR, appropriate tests/rendered review and squash merge. Deliver and validate each slice before claiming its outcome.

| Sequence | Deliverable | Acceptance and dependencies |
| --- | --- | --- |
| 8.1 | Reviewer inbox and dependable navigation | Paginated case-first inbox shows business identified/unknown, event versus announcement date, freshness, next question and reviewer state. Existing candidate details remain linked. Include UT and signal/recency filters, honest data-origin/score provenance, useful empty/error/not-found handling, role-aware controls and sign-out. Fix empty dashboard and ambiguous current-review counts. Preserve existing score methods. |
| 8.2 | Research setup and one bounded durable run | Signal-first, business-first and hybrid starts; business name optional unless business-first. Reviewer selects objective, states, signal families, recency and limits; an operator can authorize execution under existing permissions. Persist profile defaults, exact run policy/provider versions, reservations, progress and partial outcomes. Budgeted corrective retries preserve attempts; duplicate submissions/restarts cannot duplicate spend. Show blocked access and resumable versus terminal failures. Depends on 8.1. |
| 8.3 | Evidence-to-insight investigation | Connect existing source review/retrieval, retained evidence, claims, extraction/analysis and frontier execution to the case UI. A reviewer can follow up a specific unknown and see a new brief version with citations. Preserve search clues before verification, source independence, exact date semantics, relevant business facts and explicit missing financials. Source text cannot instruct the system. At least one case must complete 8.1→8.3 before expanding scope. |
| 8.4 | Reviewer decision and opportunity-development handoff | Persist case conclusions separately from model dispositions and candidate status. Decisions: more research, monitor, dismiss, create development brief. Capture reviewer, rationale, purpose, supporting/contradicting evidence version, next action and correction history. Development briefs retain unknowns, business-contact source/date and communication readiness; export a reviewed handoff, not a claim of sale. No automatic sending or candidate promotion. Depends on 8.3. |
| 8.5 | Monitoring and practical workflow measures | Save unresolved cases as well as candidates; record review dates and monitoring questions. Explicit refresh produces material-change summaries linked to source versions. Surface actual review decisions, due work, usefulness, missing judgments and cost. Keep review time separate from claimed time saved. Reuse existing alerts/watchlists where possible. Depends on 8.4. |
| 8.6 | End-to-end user validation and closeout | Exercise the production UI journey on fictional regression cases and a separately approved bounded recent real-source cohort. Obtain actual human judgments and reconcile the whole product record. The quality gate below cannot be passed by agent ratings, fresh dates alone, fixture agreement or a successful model response. |

## Design and data boundaries

**One case, several decisions.** Keep `ResearchCase` as the primary research record, `CaseEvidence`/`EvidenceClaim`/inferences as provenance, model proposals/dispositions as model review, and attributable `AnalystConclusion` as evidence judgment. Add only the minimal case workflow/run/profile/development metadata justified by each slice. Continue to use `CandidateMatch` for its established downstream reviewed-match contract; do not duplicate the corpus or force unresolved leads into it.

**Three independent questions.** What does the evidence support? Why could this business/event fit our stated purpose? What does the reviewer authorize next? Present these separately. Existing deterministic evidence scores remain versioned and unchanged unless a separate scoring design is approved. New target-fit guidance must expose its factors and unknowns; avoid percentage language implying calibration.

**Bounded single-box execution.** Prefer existing SQL storage and services with persisted run state over a new distributed queue. Reserve before each external operation, store safe outcomes, use idempotency/concurrency controls and recover interrupted work conservatively. A browser closing must not lose a reservation. No silent retries beyond the approved envelope, and no need to reapprove an ordinary retry already within it.

**Configuration with units.** Persist target-profile defaults and a frozen copy per run: states, purpose, signal families, lookback days, discovered-record ceiling, document/model/query/time limits and total cost. Operator changes to defaults affect future runs only. Environment/provider/source limits remain upper bounds. Pagination is independent. Credentials remain environment-managed; no secrets editor or secret export is planned.

**Source and contact use.** Separate source access review from confidence and source usefulness. Existing bounded official entity adapters do not supply comprehensive ownership. Show relevant public business contact provenance and reviewer-selected recipient/channel; do not infer a family's consent to contact from a public obituary or automatically use surviving relatives as sales contacts. Outbound sending and campaign automation are outside this milestone.

## Quality gates

The approved plan supplies these evaluation targets; they are not achieved measurements:

- A reviewer completes five tasks without CLI assistance: start signal-first research with no company name, inspect an uncertain lead, execute a permitted follow-up, record a rationale, and retrieve a development brief/monitoring item. The acceptance exercise must also demonstrate a no-match outcome.
- All displayed material assertions have inspectable source or interpretation attribution; planned/past/unknown timing and conflicting evidence survive the journey. No automatic ownership, successor or sale-intent assertion from a name, role or death.
- Empty database, source failure, partial model output, access restriction, duplicate submission, restart and exhausted-budget regressions preserve data and reservations. Permission denial is understandable in the UI and enforced on the server.
- A ten-lead recent real-source evaluation receives ten actual reviewer usefulness judgments with reasons. Target: at least six useful for the selected purpose, with no critical fabricated ownership/sale claim in a selected brief. Define the selection protocol and what “useful” means before acquisition; preserve every discovery miss, exclusion, retry and denominator. Do not silently replace unhelpful leads to meet the target. Use purpose-specific review rather than equating every leadership change with acquisition value.
- Report median/individual review time, source/analysis cost and missing financial/contact evidence. Do not claim time saved without a measured comparison. This small cohort is directional evidence, not population precision.
- All required CI jobs pass; inspect real UI at desktop and narrow widths, including keyboard and error states. Reconcile current state, roadmap and backlog in the closing PR. A failed human-quality gate requires remediation or an explicit user decision on scope; routine engineering completion alone does not make it pass.

## Scope held for later

Automated marketing/email delivery, CRM synchronization, scraped personal-contact enrichment, family-contact automation, comprehensive ownership coverage, valuation estimates without evidence, recurrent unattended discovery, multi-tenant collaboration, vector infrastructure and national expansion. Minimal reviewer identity/assignment can be designed within the current pilot; enterprise workflow is not required.

## Execution boundaries

The workflow, six slices and usefulness target were approved when the user activated Milestone 8. The concept is a design artifact; only completed execution records establish product functionality. Freeze a concrete live cohort and cost envelope when 8.6 is ready. No live source/model calls were made for 8.1.
