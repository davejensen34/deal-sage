# Source coverage matrix

Status values: proposed, ready, in_progress, blocked, implemented, validated, deferred.

| Jurisdiction | Source | Access | Owner/controller value | Key caveat | Status |
|---|---|---|---|---|---|
| Colorado | Department of State, Business Entities in Colorado (`4ykn-tg5h`) | Public Socrata SODA API; bounded request validated | Entity identity, status, address, formation date, and registered-agent evidence; 0% owner/controller yield in 50-record experiment | Official bulk file omits owners, officers, and directors; agent must not imply owner | validated for entity/agent evidence; rejected for owner discovery |
| Utah | Division of Corporations entity search/data availability | Public web; exact programmatic route must be verified | Potential member/manager/officer value varies by entity | Coverage, bulk access, and terms require primary-source research | proposed |

Colorado's bounded adapter and result are documented in `docs/research/colorado-owner-discovery-experiment.md`. Utah remains an experiment candidate, not a validated source; verify current access, terms, fields, representative records, and automated-use constraints before implementation.
