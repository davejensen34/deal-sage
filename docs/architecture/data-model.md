# Data model

- `Business`: legal identity, location, industry, registration, and explicitly estimated business attributes.
- `Person`: identity attributes and aliases, independent of any company or signal.
- `BusinessRelationship`: typed person-to-business role with dates, activity, confidence, and evidence references.
- `TargetProfile`: sourced acquisition criteria whose estimated attributes remain distinguishable from authoritative facts.
- `ResearchTrail` and `ResearchStage`: the ordered, auditable business → anchor → web → person → owner-ready path, with stage-local status, confidence, provenance, support, contradictions, and gaps.
- `Source`: publisher, canonical URL, dates, jurisdiction, reliability metadata, and demo marker.
- `Evidence`: subject-linked extracted and normalized facts, strength, extraction provenance, and fact/inference classification.
- `TransitionSignal`: generalized possible event; Milestone 1 primarily uses `possible_death` and one succession example.
- `CandidateMatch`: joins the person, business, relationship, signal, independent scores, conflicts, gaps, and recommendation.
- `ReviewCase`: assignment, status, decision, reason codes, and currently embedded analyst-note records.
- `SavedResearch`: analyst-owned, replayable candidate-queue criteria keyed to the stable identity-provider subject; it stores no evidence or inferred facts.
- `Watchlist` / `WatchlistEntry`: analyst-owned named collections that reference existing `CandidateMatch` rows. Membership rationale and attribution are retained, while additions and removals append candidate audit events.
- `AlertSubscription` / `AlertEvent`: analyst-owned opt-in rules and immutable in-app outcomes for manual source refresh failures or quarantine. Each event resolves its durable `SourceRefresh` link into source, acquisition-run, freshness, safe failure, and aggregate-only quarantine context. Events neither initiate refreshes nor deliver data outside DealSage; successful refreshes intentionally remain quiet.
- `AuditEvent`: append-oriented record of meaningful system and analyst actions.
- `AIExecution`: legacy candidate-summary execution metadata; it remains for compatibility while productized research uses evidence-linked proposals.
- `ModelProposal`: immutable bounded-execution result with case-local evidence/claim lineage, task/provider/model/prompt/schema provenance, structured proposed output, explicit outcome, timing, split tokens, cost, and safe error class.
- `AcquisitionRun`, `RawArtifact`, `CuratedRecord`, and `FieldLineage`: replayable source acquisition, content-addressed raw evidence, parser/schema versions, quarantine state, and field-level provenance.
- `ResearchCase`, `CaseEvidence`, `EvidenceClaim`, and `ResearchInference`: the shared signal-first, business-first, or hybrid case spine, with source-supported claims kept distinct from DealSage reasoning.
- `SourceCandidate` and `ResearchQuery`: bounded search provenance and discovered links that are not promoted to evidence or reusable connectors automatically.
- `ResearchFrontierItem` and `ResearchStep`: durable questions, attempts, budgets, actions, provider metadata, results, and explicit stopping behavior.
- `IdentityResolution`, `ClaimContradiction`, `ConfidenceAssessment`, and `AnalystConclusion`: reviewable identity hypotheses, intact conflicts, versioned deterministic confidence factors, and the separate human conclusion layer.

The research-to-review bridge consumes typed transition claims under `transition-policy-v1`. A completed proposal must have a latest separate acceptance linking both selected claims and their same-case evidence. An explicit owner/co-owner claim must identify the requested business. Person events require an explicit same-document owner/event anchor or shared business plus a non-name address/registration identifier across documents. Business events always require an explicit matching entity and identifier; an entity event without resolved owner evidence stays in research. Open contradictions, cancelled events, unsupported types and stopped cases remain investigable without candidate creation. The bridge copies evidence, opens human review, retains policy/claim/disposition lineage in its audit and never treats promotion as validation.

Typed `EvidenceClaim.object_value` uses `signal_type`, `event_status` (unknown/planned/reported/completed/cancelled), optional ISO `event_date`, and person/business identifiers appropriate to the policy subject. Claim creation validates structure, not truth. Exact legacy `reported death`/`reported_death` aliases remain readable without rewriting stored claims. Narratives retain claim classification, evidence links, separate publication/retrieval times, unknowns and policy-specific questions. Unsupported legacy values remain visible.

`BusinessRelationship.active` is nullable from revision `a729e10b3c42`: null means unknown. New promotions preserve the source owner/co-owner role and unknown current activity instead of inferring former ownership or inactivity from an event. Existing true/false history remains unchanged. Source-reported event status stays in the case claim and promotion audit; a candidate event date does not establish completion. Downgrade refuses to erase unknown activity.

Candidate export is a derived, non-persistent projection rather than a second evidence store. Version `dealsage-candidate-export-v1` retains IDs and public source links needed to return to DealSage evidence, the recorded relationship classification, immutable score-assessment provenance, evidence and research timestamps, and the separate analyst disposition. It does not copy retained source content or analyst narrative into downstream systems, and every exported candidate is recorded in `AuditEvent`.

Workflow-effectiveness reporting is also a derived projection. Candidate attribution exists only when `ResearchCase.candidate_match_id` connects through `CaseEvidence.raw_artifact_id` and `RunArtifact` to an `AcquisitionRun.source_key`. Candidates lacking that chain are counted as unattributed. If a deployed database has not received the evidence-lineage migration, the projection reports that schema capability as unavailable and declines all attribution rather than inferring it. Multi-source case counts must not be summed as unique candidates, and reported source cost covers durable `SourceRefresh` records only.

Partial seams: analyst notes are JSON records rather than a dedicated table; research jobs have an execution interface but no persistent job entity. Colorado and Texas provide bounded entity-corroboration adapters. Utah's three-file importer has been exercised against a delivered bounded sample and retains explicit owner roles as unvalidated relationship assertions. No live search or transition-signal provider exists. These are tracked honestly rather than hidden behind premature abstractions.
