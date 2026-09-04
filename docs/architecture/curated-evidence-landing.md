# Curated evidence landing contract

Milestone 3 separates transport evidence from interpretation so source changes and parser mistakes cannot silently rewrite research history.

## Layers

1. **Acquisition run** — records the source contract fingerprint, jurisdiction, discovery strategy (`signal_first`, `business_first`, or `hybrid`), timing, status, and aggregate outcome.
2. **Immutable raw artifact** — content-addressed bytes plus source record ID, canonical URL, retrieval time, media type, byte size, safe request metadata, and the observed contract fingerprint. Credentials and session material are excluded.
3. **Curated record** — a versioned parser outcome for a `person`, `transition_signal`, `business`, `relationship_assertion`, or `unresolved` subject. It may exist without a business.
4. **Field lineage** — maps every published normalized field to a raw path and a value hash, allowing later verification without placing raw personal data in operational listings.
5. **Quarantine** — a durable non-publishing outcome for invalid content, empty extraction, or source-contract drift. The raw artifact remains available for replay.

## Invariants

- Artifact identity is the SHA-256 hash of its exact bytes within a source. Re-observing the same source content links the run to the existing artifact instead of rewriting it.
- Evidence storage refuses a conflicting write to an existing key.
- Parser version participates in curated identity. A new version creates a replay result while preserving earlier outcomes and without refetching the source.
- Contract fingerprints are checked before an existing parser result can be reused. Changed contracts quarantine even when the returned bytes happen to be unchanged.
- Raw content and safe request metadata are not returned by the acquisition-run summary API.
- A person or signal with no known business is valid curated state. No placeholder business is manufactured.

## Retention boundary

Raw artifacts are retained as evidence while any curated record, research trail, decision, or audit event cites them. Deletion therefore requires a future citation-aware retention workflow; the generic storage delete operation is not an authorization to erase cited evidence. Access tokens, cookies, passwords, payment details, and other authentication material must never enter the landing layer.

## API boundary

`GET /api/research/acquisition-runs` exposes operational counts and status only. Detailed raw evidence access and analyst quarantine resolution remain deferred until authorization, redaction, and retention rules are implemented.
