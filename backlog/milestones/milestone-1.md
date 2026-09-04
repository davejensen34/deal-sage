# Milestone 1 — Evidence and Analyst Foundation

Status: in_progress (reconciliation)

Outcome: a locally runnable fictional-data product that demonstrates evidence-centered candidate review and preserves human decisions.

| Capability | Status | Evidence |
|---|---|---|
| Dashboard from persisted data | validated | API/frontend startup and PostgreSQL response |
| Candidate browse/search/filter/pagination | validated | API tests and rendered workflow |
| Candidate sorting | validated | API test and rendered table control |
| Candidate details and three scores | validated | rendered workflow and API tests |
| Source provenance and demo labeling | validated | rendered evidence cards |
| Conflicts and missing evidence | validated | rendered collision/false-positive cases |
| Decisions, rationale, notes, audit | validated | API persistence tests and rendered controls |
| SQLite minimal mode | validated | local startup/tests |
| PostgreSQL Docker mode | validated | full Compose stack and persisted metrics |
| Deterministic scoring functions | validated | unit tests |
| Evidence-derived score recalculation | partial | fixture scores are curated |
| OpenAI/Anthropic summary | implemented, not validated | adapters exist; no live request |
| Initial schema migration | validated | upgraded an empty SQLite database to head |
| Live acquisition | deferred | Milestone 2/3 |
