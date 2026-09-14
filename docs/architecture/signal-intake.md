# Recent-signal intake

Issue #144 adds `signal-intake-v1` to configured research cases. This is a research-priority and pre-analysis gate, not an ownership score, verified date, or finding that a business is attractive. The existing confidence recency multiplier remains historical evidence weighting; its retrieval fallback cannot qualify an event here.

Create a new case through `ResearchCaseService.create_case(..., signal_intake_policy={"version": "signal-intake-v1", "assessment_date": "2026-09-14", "lookback_days": 90})`. The JSON policy is persisted separately from budgets. Dates must be ISO calendar dates and lookback must be an integer from 1 through 3650. Ninety days is a provisional offline evaluation choice, not an activated product default. No policy means historical behavior; migration `b144f0a9c721` leaves existing cases null. Use a new case for a different assessment window rather than reinterpreting a completed run. Downgrade refuses to discard any configured policy.

Transition claims retain `event_date` and `event_status`; intake also recognizes an optional `announcement_date`. Each supplied date needs its own `event_date_excerpt` or `announcement_date_excerpt` in the claim's `object_value`, exactly contained in that evidence's retained `relevant_excerpt`. Claim creation owns semantic date normalization and attribution. Substring agreement checks provenance, not semantic truth: an analyst must distinguish actual event/announcement language from a dateline, copyright notice or repost. Search-provider dates, publication metadata and retrieval timestamps alone never establish eligibility. Missing support produces date-verification work, not negative ownership evidence.

Routing uses an inclusive `[assessment_date - lookback_days, assessment_date]` interval:

| Route | Meaning | Model analysis eligible |
| --- | --- | --- |
| recent_event | Cited reported/completed event in the window; reported status remains reported | Yes |
| recent_announcement | Cited announcement in the window, event date unknown | Yes, without claiming completion |
| planned_event | Future planned event with a cited recent announcement | Yes, without claiming completion |
| background | Old event/announcement or cancelled event | No, retained as background |
| date_verification | Unsupported/malformed/unknown dates, future non-plan, passed planned date, unresolved conflict | No, retain for investigation |

An old event remains background even after a new publication or announcement. A cited recent event can qualify within an older updated source. Conflicting event dates for the same named subject and signal type, cancellation conflicts, and explicit open claim conflicts require review. This comparison is not identity resolution and may need analyst disambiguation when a subject has multiple separate events. All same-case assertions participate before filtering to a selected packet, preventing date cherry-picking across evidence IDs.

`SearchService` appends bounded date hints and stores the actual submitted query. Provider interpretation is not guaranteed and an empty result remains empty. Date hints apply to all searches in an opted-in case; unrestricted historical/background research should use a separate case until per-action search purposes are implemented. Access decisions and budgets remain in their existing paths.

`ResearchPlanner.start_step` gates model analysis before a step is reserved. `ModelAnalysisService` separately requires an eligible transition among the selected evidence **and claim IDs**, before any provider call. Background evidence can accompany that recent signal. A content-free `signal_intake_analysis` audit records the policy, routes, references and provider/version metadata before an allowed call, including calls that subsequently fail. Case narratives expose current routes and counts. Discovery priority v2 adds 20 points for a qualifying signal or subtracts 15 for wholly historical signals; source access still controls the permissible action. These are heuristics, not calibrated scores.

## Remaining Issue #144 work

The historical Milestone 7 preparation/revision/execution scripts are unchanged and do not invoke this gate. Their old approvals are exhausted. The next evaluation must introduce a separately versioned, hash-bound intake manifest and execution contract, capture cited date assertions before paid analysis, freeze routing/exclusion counts, and refuse stale or empty cohorts before reserving slots. The application gate alone does not fulfill that protocol acceptance criterion. Do not replay old bundles to bypass it. No new live run or data migration was performed with this increment.
