# Retained source passages

Issue #199 makes later document context available to the investigation backend. Previously, document retrieval retained raw bytes but extraction could only use the opening 2,000-character excerpt. This increment adds read-only passage preparation and optional passage extraction. It does not implement automatic passage selection, corroborating searches, semantic normalization, target-fit claims or recommendation readiness.

## Source and coverage contract

`source-passages-v1` requires same-case evidence linked to a retained artifact. The artifact URL, declared byte size and SHA-256 must match the evidence and stored bytes. Reads are capped at 1,000,000 bytes; local storage bounds the actual read, including when the file has been replaced with oversized content. Missing, mismatched or unsupported artifacts fail without fetching a replacement. Storage paths and exception bodies are not exposed.

HTML reuses the existing conservative article/main/body parser, hidden-content exclusions and access-marker checks. Plain text and JSON preserve decoded text; malformed UTF-8 uses replacement characters. Text hashes and zero-based, end-exclusive offsets describe this normalized Unicode text, not raw HTML bytes. The original content hash always accompanies it. A source's claims remain unverified.

At most 100,000 characters are exposed in 2,000-character passages with 200-character overlap, in document order. Metadata reports normalized text length, available length, truncation, passage count and both source/text hashes. Ten passages are returned per page. Overlap reduces boundary loss but does not guarantee that every long sentence or quotation fits in a passage. The HTML parser's scope preference can omit surrounding page text; coverage is of the selected readable scope, not all raw markup. Neither a passage count nor successful extraction means the whole source was researched.

## API and execution

Authenticated readers can inspect `GET /api/research/cases/{case_id}/investigation/evidence/{evidence_id}/passages?page=1`. This reads retained storage only; no database writes, source requests or model calls occur.

`GET .../extraction-preview?passage_index=1` freezes one selected passage, its offsets, hashes and coverage metadata in the existing extraction packet. Operator `POST .../extract` accepts the same optional `passage_index` beside the request key and expected hash. Admission re-reads and verifies the retained bytes before reserving capacity. Changed selections or packets require a new preview. A repeated request returns its original frozen outcome without reading storage or calling a provider, but cannot be reused for a different passage.

Omitting the index retains the original excerpt contract and packet shape, including legacy request hashes. No old evidence, briefs, claims, authorizations or model proposals are rewritten. Every new passage extraction consumes the existing attempt/cost allowance; the 24,000-byte request limit, model/output/time limits and no-automatic-retry policy remain. Exact quotes must occur in the selected frozen passage, not merely somewhere in the source. Outputs are model proposals, never authoritative source facts or human decisions.

No UI controls or migration are added. Existing extraction history retains the selected packet for inspection. Orchestration must next choose useful passages within its run-wide allowance and reconcile their proposals; the target-fit service still requires its separately validated typed source claims. This change must not be used to silently promote new model fields into fit evidence.

## Validation

All 606 backend/API tests pass, including later-page employee context, source/text hashes, Unicode offsets, overlap, truncation/pagination, restricted/hidden content, cross-case access, operator permissions, byte/URL/hash/size failures, stale selection, exact citation scope and frozen replay after an artifact becomes unavailable. Existing extraction lifecycle tests continue to pass. Tests use fictional sources and providers; no live calls, migration or research-corpus writes occurred. Human acceptance under #187 remains paused for #194.
