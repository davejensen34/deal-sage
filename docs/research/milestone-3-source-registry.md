# Milestone 3 source registry

Reviewed against official state sources on September 4, 2026. This is a decision record for bounded experiments, not legal advice or permission to crawl an interactive service.

## Registry rules

Every adapter proposal must identify the source owner, jurisdiction, evidence purpose, canonical entry point, permitted access path, expected refresh, cost, authoritative fields, prohibited inferences, and a source-contract fingerprint. If an access method, schema, terms, or expected content changes, ingestion must quarantine the result until the contract is reviewed.

The source portfolio must distinguish discovery sources from lookup and corroboration sources. State entity registries do not define the candidate universe: signal-first research may begin with a person or transition event and use registries only after business clues emerge. Transition-signal sources require their own primary-source access and responsible-research review before implementation.

Raw evidence must retain retrieval time, request parameters that are safe to retain, response content hash, media type, source record identifier, canonical URL, and adapter/parser version. Credentials, session tokens, payment details, and hidden authentication material are never evidence and must not be stored with artifacts.

## Colorado

1. **Business Entities in Colorado (`4ykn-tg5h`)** — retained as the no-cost entity anchor already exercised in Milestone 2. It supports entity identity, status, addresses, formation dates, and registered-agent evidence. The measured sample had no owner/controller fields, so it cannot satisfy owner discovery.
2. **Secretary of State Business Search and document index** — the official search accepts business name, trademark, trade name, entity ID, or document number and describes the office as a filing registry. Use only for a bounded manual contract and representative-record review until an official programmatic access path and reuse constraints are confirmed.
3. **Business Master File** — the official order form lists weekly delivery at $12,000 or monthly delivery at $3,000 for a one-year subscription. Reject for the low-cost pilot unless the product economics materially change.

Official references:

- https://data.colorado.gov/Business/Business-Entities-in-Colorado/4ykn-tg5h
- https://sos.state.co.us/biz/FileDocSearchCriteria.do?quitButtonDestination=BusinessFunctions
- https://www.sos.state.co.us/pubs/business/PDFFillable/BusinessMasterFile.pdf

## Utah

1. **Utah.gov Business Entity List (BEL)** — the official order page says the list includes business names and addresses plus registered officers, principals, partners, and agents. Its published example separates entity, information, and principal/member-position CSV lists joined by Entity ID. This is the strongest currently documented owner/controller experiment candidate, but it is paid: a custom request starts at $5 for 200 records and a full list is $0.01 per record. The minimum purchase was explicitly authorized in Issue #32; delivery is pending. The importer accepts the original ZIP, bounds and validates its entries, and retains the exact archive as immutable private evidence.
2. **Division of Corporations Business Search and filed documents** — suitable for bounded entity/detail corroboration. Utah states that filed images can be purchased through Business Search for $2 each. Do not automate or purchase records until the exact access contract and sample budget are approved.
3. **Division of Professional Licensing lookup** — a public corroboration candidate for regulated firms and people. Its coverage is sector-limited, and a professional or business license does not establish ownership.

Official references:

- https://secure.utah.gov/datarequest/businesses/index.html
- https://secure.utah.gov/datarequest/businesses/listExample.html
- https://secure.utah.gov/feedback/faq.html?id=382
- https://secure.utah.gov/llv/search/index.html

## Texas

1. **Comptroller Franchise Tax Account Status / Taxable Entity Search** — the official search advertises API access and accepts taxpayer number, entity name, or Secretary of State file number. The Comptroller states that public officer/director information comes from the latest processed Public Information Report (PIR). Treat those roles as relationship evidence, not ownership, and record possible annual-report staleness.
2. **Comptroller open-data datasets** — the official open-records page lists Active Franchise Taxpayers and Active Sales Tax Permits as downloadable open data. Dataset `9cir-efmm` was exercised with a bounded ten-record Texas request through the public Socrata API. All ten records landed without quarantine at zero marginal cost, with 85.6% contracted-field completeness. Tax or permit status does not establish ownership; the adapter explicitly records zero ownership-supported assertions.
3. **Secretary of State SOSDirect** — the official service charges $1 per search and additional document or certificate fees. Defer automation and purchases until its access terms, cost ceiling, and unique evidence value are approved.

Texas explicitly states that Ownership Information Report data is confidential and not displayed online. DealSage must not represent that unavailable data as discoverable through the Comptroller source.

Official references:

- https://comptroller.texas.gov/taxes/franchise/account-status/
- https://comptroller.texas.gov/taxes/franchise/pir-oir-filing-req.php
- https://comptroller.texas.gov/about/policies/open-records/
- https://www.sos.state.tx.us/corp/sosda/index.shtml

## Next experiments

- Colorado: preserve the validated Socrata adapter as the first raw-to-curated implementation fixture; separately review a small set of filing-detail records without assuming an automated route.
- Utah: inspect the pending authorized $5 BEL delivery, then run the exact archive through the bounded three-CSV importer and publish aggregate-only results.
- Texas: retain the now-validated Active Franchise Taxpayers adapter for entity/tax corroboration, monitor its contract fingerprint, and keep SOSDirect deferred.

These experiments must report retrieval success, latency, field completeness, role yield, stale/ambiguous rate, duplicate/conflict rate, and marginal cost. A source moves from ready to implemented or validated only with stored, reproducible evidence.

## Signal-first research result

Recent state vital records are not a practical discovery feed. Utah keeps death certificates private for 50 years; Texas exposes aggregate dashboards while recent person-level records and indexes use restricted or controlled request paths; no timely open Colorado statewide person-level feed was verified. These sources are therefore corroboration or aggregate context, not lead generation.

Probate/public-notice repositories can discover names by date, county, and notice category without a business name. Colorado law provides for a statewide newspaper notice repository, Utah law requires probate notices under a common heading, and Texas press/court portals expose estate or probate categories. Their public search interfaces do not by themselves establish an automation or reuse contract. The next step is publisher or court-operator permission plus a bounded manual coverage study, not scraping.

OfficialObituary documents a no-auth, state-filtered public browse API and labels responses with `public-browse` and `obituary-browse` contracts. A bounded aggregate check on September 4, 2026 succeeded for all target states but found only six total records (CO 1, UT 3, TX 2); the newest reported dates ranged from January to May 2026. The public response exposed `edit_token` and `creation_session_id` fields. Milestone 3.1 now proves that an explicit allowlist can keep the needed public facts while dropping those fields and all unknown fields in memory, with a final normalized-name persistence guard. This separates response safety from usefulness: the source is technically sanitizable but remains only a supplemental candidate because of poor coverage and has not been promoted into a persistent connector.

Official signal references:

- https://officialobituary.com/docs/api-reference
- https://officialobituary.com/terms
- https://coloradopressassociation.com/
- https://www.coloradojudicial.gov/media/8775
- https://utahpress.com/services/legal-notices/
- https://le.utah.gov/xcode/Title75/Chapter1/C75-1-S404_2025050720250507.pdf
- https://texaspublicnotices.netlify.app/
- https://topics.txcourts.gov/CitationsPublic/SearchCitationNoticeDoc
- https://vitalrecords.utah.gov/death
- https://www.dshs.texas.gov/center-health-statistics/vital-statistics-data/request-procedures

The practical portfolio is therefore federated: authorized obituary/publisher feeds and probate notices discover people; curated clues and later intelligent analysis propose business candidates; state entity, tax, licensing, and filing sources validate those candidates. Comprehensive statewide business downloads are optional accelerators, never a prerequisite.
