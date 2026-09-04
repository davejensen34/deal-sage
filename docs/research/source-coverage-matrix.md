# Source coverage matrix

Last primary-source review: September 4, 2026. Status values: proposed, ready, in_progress, blocked, implemented, validated, deferred, rejected.

The registry distinguishes a source's authority from the facts it can support. A filing registry, registered agent, officer, license, or tax account does not by itself prove beneficial ownership. “Ready” authorizes a bounded validation experiment, not unrestricted collection or a production connector.

| State | Source | Intended evidence role | Access and cost | Important limitation | Decision |
|---|---|---|---|---|---|
| Colorado | Secretary of State Business Entities in Colorado (`4ykn-tg5h`) | Entity identity, status, address, formation date, registered agent | Public Socrata SODA API; bounded 50-record request validated at no marginal cost | Omits owners, officers, and directors | validated for entity anchoring; rejected for owner discovery |
| Colorado | Secretary of State Business Search and filed-document index | Entity/detail corroboration and filing-document discovery by name, entity ID, or document ID | Public individual web search; programmatic route and document reuse rules still require verification | Filing registry disclaims operational/legal certification; documents may contain personal addresses and role labels need interpretation | ready for bounded manual contract review only |
| Colorado | Secretary of State Business Master File | Broad entity refresh candidate | Official weekly or monthly FTP/CD subscription | Published price is $12,000 weekly or $3,000 monthly per year, incompatible with the current low-cost pilot | rejected for pilot cost |
| Utah | Utah.gov Business Entity List data request | Entity identity plus registered officers, principals, partners, agents, and member-position rows | Official paid list: full list $0.01/record; custom request minimum $5 for 200 records, then $0.05/record | Names and addresses only; role vocabulary must be mapped without promoting agent/officer to owner | ready for a user-approved bounded paid sample |
| Utah | Division of Corporations Business Search and filed documents | Entity/detail corroboration and filing-document evidence | Public individual search; filed images are offered for $2 each | No verified bulk/programmatic contract; documents and optional member/manager fields vary by entity and filing | ready for bounded manual contract review only |
| Utah | Division of Professional Licensing lookup | Licensed business/professional corroboration | Public individual lookup, current-date indicator shown by the state | Covers regulated professions rather than all businesses; license association is not ownership | proposed corroboration source |
| Texas | Comptroller Franchise Tax Account Status / Taxable Entity Search | Entity/status anchoring and latest public officer/director rows from processed PIR filings | Official search advertises API access; API authentication, quotas, and response contract require validation | Officer/director information may lag until the next annual PIR; confidential OIR ownership is not published | ready for bounded API contract validation |
| Texas | Comptroller Open Data: Active Franchise Taxpayers and Active Sales Tax Permits | Broad entity/status/address corroboration and refresh candidates | Official open-data portal supports viewing, subset search, and downloads | Tax or permit presence is not ownership; sales search is not designed for geographic bulk lists | ready for bounded dataset validation |
| Texas | Secretary of State SOSDirect | Filing registry, entity search, and plain/certified document retrieval | Account or temporary access; $1 per search, with additional document/certificate fees | Paid interactive service with no verified automation contract; filing roles do not automatically establish ownership | deferred pending cost and access decision |

Detailed source contracts, links, and state-specific next experiments are in `docs/research/milestone-3-source-registry.md`. The next adapter Issue must cite the applicable source decision and may not broaden its access method implicitly.

## Signal-first portfolio

These sources accept geography, date, or notice-type discovery without a known business name. None is sufficient alone, and “deceased” does not imply “business owner.”

| Coverage | Source | Discovery value | Limitation | Decision |
|---|---|---|---|---|
| CO, UT, TX | OfficialObituary public browse API | Documented state-filtered, paginated obituary metadata API; no account required | September 4 bounded check returned only 1 CO, 3 UT, and 2 TX records, with newest reported death dates in January–May 2026; publisher says it does not fact-check family submissions | validated technically; rejected as primary coverage; retain as supplemental fixture/source |
| Colorado | Colorado newspaper statewide public-notice repository / probate notices | Date-driven notices to creditors can identify decedents without a business name | Repository access contract and automated reuse are not documented; probate notice is lagging and not universal | ready for publisher-permission and bounded manual coverage study |
| Utah | Utah Press Association legal notices | Statewide newspaper notices include a probate heading organized by decedent surname under Utah law | Search is public, but no authorized API or bulk reuse contract was found | ready for publisher-permission and bounded manual coverage study |
| Texas | Texas Press Association public notices and Texas court citation/notices search | Search supports probate/estate categories and county/date discovery | Coverage varies by participating publication/court; no authorized bulk API was verified | ready for publisher/court contract study; no automation yet |
| Colorado | Vital statistics / court records | Named-person corroboration may be possible with eligibility or case context | No timely, open statewide person-level death feed was verified | rejected for population discovery |
| Utah | Vital Records and State Archives | Historical death corroboration | Recent certificates remain private for 50 years | rejected for recent discovery |
| Texas | DSHS Vital Statistics | Aggregate trends and restricted named verification/index processes | Dashboard is aggregate; recent certificates are restricted and index acquisition is a separate controlled process | rejected for automated recent discovery |

Local newspapers and funeral homes remain a source family, not an implicitly authorized connector. DealSage may onboard a publisher-provided API, RSS feed, sitemap, or written data agreement source by source; it must not generalize permission from one publisher to another.
