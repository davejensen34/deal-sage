# Milestone 4.7 operational corpus

Issue #83 assembled the first single-database corpus containing bounded real source evidence from Colorado, Utah, and Texas on September 9, 2026. Record-level evidence remains in ignored local storage; the repository retains only aggregate measures.

## Observed result

| State | Acquisition | Artifacts/records | Relationship value |
| --- | --- | ---: | --- |
| Colorado | New bounded request to the public Business Entities Socrata API | 25 artifacts; 50 curated subjects | 25 registered-agent assertions; zero ownership-supported assertions |
| Texas | New bounded request to the public Active Franchise Taxpayers Socrata API | 25 artifacts; 25 curated businesses | Entity/tax corroboration only; zero relationship or ownership assertions |
| Utah | Exact replay of the retained live BEL delivery | 4 artifacts; 661 curated subjects | Reported principal roles, including owner-role candidates, remain unvalidated source assertions |

The combined corpus contains 54 immutable artifacts and 736 curated records with zero quarantine. A second identical execution retained the same artifact and curated-record totals, validating content-addressed deduplication and parser idempotency. Both public refreshes and the Utah replay had zero marginal cost. No search-provider or model call occurred.

## Interpretation

This is now a real operational evidence corpus, but not an opportunity queue. Colorado and Texas establish current business anchors; Utah adds bounded person-role candidates from the prior delivery. None independently proves beneficial ownership or supplies a transition signal. Issue #86 must begin from either a transition signal or a Utah role candidate and freeze only documents that have already been retrieved, excerpt-verified, and hashed.

The replay command rejects missing, extra, non-live, or hash-mismatched Utah artifacts before opening an acquisition run. It does not repurchase Utah data, publish names or addresses, invoke provider search, or run AI.
