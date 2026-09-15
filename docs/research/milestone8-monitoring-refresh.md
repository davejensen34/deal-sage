# Milestone 8 monitored refresh acceptance

Issue #184 validates integration of the delivered M8.3-M8.5 services. This is engineering acceptance with fictional sources and agent actions, not real research or human usefulness evaluation.

## Automated regression

`tests/test_monitoring_refresh_journey.py` runs two complete journeys in separate temporary SQLite databases: a new retained source with quoted model output, and an empty follow-up. Each begins with an unresolved signal-first case, saved brief, shared monitor decision and personal due item. Separate follow-up authorization executes despite the original zero query/document/model budget, without enlarging that budget. Repeated search/retrieval/extraction request keys each reuse the first result; counters verify exactly one call per provider.

The positive journey records source access, lands a document/artifact and retains quoted extraction as a model proposal. It creates no evidence claim or model disposition. The empty journey adds no source or model proposal but preserves the new unanswered question. Both save and compare a second brief, retain the prior decision and due item until explicit actions, then record an unassessed review and a separate pause. Database reopen verifies original snapshots, budgets, decisions and monitoring history are intact. No name, role, matching quote or successful call establishes ownership or sale intent.

## Rendered production UI

The existing isolated fictional case 28 was marked due on September 15, 2026. Through the app, the operator saved follow-up run 2, executed one fixture search, reviewed access for source 4, retrieved evidence 18/artifact 3, and executed extraction 4. The fixture returned no supported observations and explicit unknown business/transition/ownership/financials. No source or model network requests occurred.

The app saved brief version 3 and compared it with version 2. The comparison showed one added source, one added extraction record, one added pending question, and changed model-inclusion scope. Version 2 remained at two sources and zero model proposals after reload. Version 3 retained three sources and the unanswered question. These counts describe stored records, not independent corroboration or a new business event.

A new reviewer decision against version 3 retained the unknowns, with usefulness and review duration unassessed. The September 15 reminder remained due after research, brief saving and decision recording. Only a separate manual reschedule moved it to October 1. Previous decision and monitoring records remained visible. Desktop and 390px comparison rendering and reload persistence were inspected.

## Result and limits

All 553 backend/API tests, 57 frontend tests, TypeScript and the production frontend build passed; the existing large-chunk warning remains. No application defect was found in this exercised path. No schema migration, operational-corpus write, credential access or live research call was needed.

The in-policy fictional refresh integration gate is validated. This does not validate refreshing an old case with an expired research/date/provider policy, automatically revisiting a particular URL, unattended monitoring, live-provider behavior, complete cost accounting or actual human usefulness. Old-case policy renewal and complete cost coverage remain M8.5 work. M8.6 still requires its frozen selection protocol/cost envelope and actual human judgments on the real cohort; fictional output cannot satisfy that gate.
