# Case brief versions

Issue #170 adds `case-brief-snapshot-v1`, an explicit saved view of existing case records. It makes no source/model calls and changes no score, proposal disposition, analyst conclusion or candidate state. The live inbox projection remains unchanged.

## Content and interpretation

The snapshot freezes the existing source-backed brief, source references/hashes and excerpts, transition assertions, quoted extraction proposals, human reviews/conclusions, frontier questions and conflicts. Claim fingerprints detect included claim changes without exporting internal provenance. Model observations are included only for completed cited-extraction proposals linked to retained evidence in the same case. Other or unsuccessful proposals are counted explicitly and remain in case research history.

Original model text remains labeled as interpretation, including rejected or corrected proposals. Review decisions and human-authored corrections are separate records. A changed source hash or excerpt flags the older extraction; quotation matching does not verify its meaning. Saving a version does not accept a model proposal. Missing ownership, timing, financials and sale intent remain unknown under the existing brief rules.

Changes identify added, changed and removed retained record IDs by category. They do not establish a real-world business event, independent corroboration or calibrated opportunity value. Preview compares current included inputs to the latest saved version; opening an old version never rewrites it with current data.

## API and persistence

Authenticated case routes provide `GET brief-preview`, `GET brief-versions?page=1`, and `GET brief-versions/{version}`. History returns ten summaries per page. `POST brief-versions` requires review permission and the preview's content hash/latest version plus a UUID request key. A case-row write serializes version admission; a stale preview conflicts rather than silently saving different inputs. The same actor/request/hash/version replays a committed result after a lost response. Unchanged inputs cannot create a duplicate version. The version and attributable audit event commit together.

Migration `f170a0b1d835` adds `case_brief_versions`, unique case/version and request-key constraints. There is no update/delete API. Downgrade refuses to discard retained versions. This is a bounded saved projection, not a backup or a claim of global snapshot isolation against every concurrent corpus writer.

Each case collection is capped at 200 records, except claims at 500. The encoded snapshot ceiling is 256,000 UTF-8 bytes. Exceeding scope fails explicitly without a partial version. Source display excerpts cap at 2,000 characters with a truncation label; citations/model quotations remain separately retained. History/detail responses exclude storage keys, credentials and raw artifact bytes.

## Observed validation

All 522 backend/API tests and 43 frontend tests passed; TypeScript and production build passed with the existing chunk warning. Tests cover stale inputs, duplicate retries, actor/case boundaries, viewer denial, pagination, audit, size limits, migration/reopen/downgrade protection, rejected proposals and safe text rendering.

The isolated fictional demo saved version 1, added a fictional source, previewed one added source, saved version 2 and reopened version 1 after reload. The earlier brief preserved its original unknown business identity while the later version cited the new source-reported name. Desktop and 390px rendering passed without horizontal page overflow. Only the isolated demo received the migration; no live calls or operational-corpus changes ran. Frontier execution and the full 8.1-to-8.3 workflow acceptance gate remain open.
