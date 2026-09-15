# Durable discovery runs

Issue #158 implements Milestone 8.2. `/discover` creates a `ResearchCase` and a frozen `DiscoveryRun`; it reuses `SearchService`, `ResearchQuery` and `SourceCandidate` rather than creating a second evidence store. A run discovers links. It does not retrieve their pages, establish ownership, run separate analysis, promote candidates or send communications. Those links remain visible, useful, unverified clues in the existing case brief.

## Configuration and authorization

Authenticated reviewers prepare signal-first, business-first or hybrid research. Only business-first requires a business name. An operator saves append-only `DiscoveryProfile` defaults and explicitly executes each search under the existing `execute_ai` permission. The profile is a convenience for future forms: its contents are copied into a run and cannot enlarge an existing run.

The strict setup contract bounds CO/UT/TX, eight supported signal families, 1–365 lookback days, 1–100 unique source links, 1–30 total attempts, 0–500 USD cents and 60–3600 elapsed seconds. Each selected state/family combination gets one exact dated query. Extra attempt capacity allows explicit retries; a link ceiling is not a promise of that many companies or valid matches. Time starts at the first attempt. Source/provider limits remain upper bounds.

Preview freezes `discovery-run-v1`, the signal policy, assessment date, settings, provider configuration/pricing, submitted queries and exact OpenAI request bodies. Creation checks the canonical JSON SHA-256 against a fresh preview and records actor and profile version. Creation keys are UUIDs; reuse with a different plan fails. Case and run creation share one transaction so concurrent creation cannot orphan a case. Plans older than seven days cannot execute.

## Execution and recovery

Execution is one explicit HTTP action per query, with durable SQL state rather than a background worker. Each attempt has a UUID, actor, slot, reservation, status and recovery deadline. A compare-and-swap on run revision/status claims the run and commits its reservation and unique attempt before network I/O. A repeated attempt key returns progress without another call; another concurrent action loses the claim. The browser retains the same payload when retrying a lost response. Reopening the run loads persisted progress.

Success retains query lineage and staged links; an empty response is a legitimate zero-result outcome. Failures retain reservations and safe error classes, never exception bodies. An operator may explicitly retry the last failed slot using a new attempt within the original attempt, time, record and cost caps. SDK automatic retries are disabled. Reservations are conservative ceilings, not measured invoices or refunds.

A process interruption can leave a `running` attempt after its reservation committed. After its request timeout plus a 60-second grace period, explicit recovery marks it `unknown`, retains its reservation and advances past the uncertain slot. Recovery makes no call and cannot replay an unknown outcome. The recovery audit and state transition commit together. A late provider response must acquire the same revision lock inside the result-staging transaction; it cannot append records or overwrite a recovered outcome. Public deadline timestamps carry UTC offsets even when SQLite stores them without timezone information.

`completed` means the final planned query succeeded; it does not assert earlier slots all succeeded or any opportunity was established. Attempt history preserves those distinctions. A partial run whose caps are exhausted cannot make another call. Recovery does not extend its original time ceiling.

## Provider envelope and deployment

Credential-free fixtures require **all three** settings: disabled web search, `demo_mode=true` and `auth_mode=demo`. They return an explicitly fictional `example.test` clue and perform no network I/O. Other disabled configurations may save a plan but cannot execute it.

Live execution currently reuses the reviewed M7 `gpt-5-mini-2025-08-07` envelope from `recent_discovery.py`: 12 cents reserved per call, one search tool call, at most 1,000 output tokens and no SDK retries. Pricing was checked September 14, 2026 and is valid through September 21. The full-context reservation is deliberately conservative. Other model names, missing credentials, changed provider limits/request contracts or expired pricing block execution before reservation. Updating this reviewed envelope requires code review and a new plan; changing workspace defaults cannot bypass it. Credentials stay in environment configuration and never appear in plans. No new live evaluation or price verification was performed for this increment.

Apply the normal migration workflow before deploying: Alembic revision `c158a0b1d832` follows `b144f0a9c721` and adds the three tables. Its downgrade refuses to discard any retained profile/run/attempt history. Follow [pilot recovery](../deployment/pilot-recovery.md) for a real database; the validation database is fictional and separate from the research corpus.

Validation includes permission checks, immutable defaults, exact preview/idempotency, empty results, failed reservations/retries, concurrent claims, late-response recovery, record/time ceilings, pricing expiry/configuration drift, database reopen/retry and destructive-downgrade refusal. Browser checks cover preview, save, fictional execution, reload/history and unverified case clues at desktop and 390px. Live source access, evidence retrieval and investigation are the next 8.3 increment; M8 human quality gates remain open.
