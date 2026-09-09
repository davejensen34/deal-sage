# Milestone 4.7 transition-packet preflight

Issue #86 preflighted a three-case public-evidence cohort on September 9, 2026 without paid search or model calls. The ignored local manifest retains case subjects, URLs, exact excerpts, evidence IDs, artifact IDs, and full content hashes. This committed record remains aggregate-safe.

## Result

| Slot | State | Origin | Retrieved evidence | Result |
| --- | --- | --- | ---: | --- |
| M47-CO-1 | Colorado | signal first | 2 | retrieved, excerpt-verified, and hashed |
| M47-UT-1 | Utah | business first | 2 | retrieved, excerpt-verified, and hashed |
| M47-TX-1 | Texas | hybrid timeline | 2 | retrieved, excerpt-verified, and hashed |

All six ordinary public pages passed the same safe HTTP retrieval path used by the application. Together they contain 1,687,894 bytes. Every selected excerpt appears in the landed bytes, every stored artifact matches its SHA-256 content hash, and no page encountered authentication, paywall, CAPTCHA, unsupported media, or quarantine. Search-result snippets were used only to locate candidate URLs and were not persisted as evidence.

The candidate manifest hash is `ab440ac86ddb2b49be9483d7d9c48cf9dbe0aa1348b95c88b1a4f35a6df2f0cc`; the resulting frozen-packet file hash is `a8d535ed00ade57f3775dd9ad13bcc9b2f48998b077035d1922aa223ebbf84f9`. The packet may be replayed from local artifacts without refetching. Changing a subject, source, excerpt, or artifact requires a new packet version before provider output is observed.

## Gate to Issue #87

Preflight resolves the source-reproducibility failure from the earlier Milestone 4 evaluation. It does not authorize AI spending or establish an opportunity. Issue #87 must freeze the exact model tasks and pre-labels, validate that both providers receive the same six evidence items, and obtain explicit approval for providers, models, case count, call ceiling, and dollar ceiling before execution.
