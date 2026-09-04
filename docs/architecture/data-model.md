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
- `AuditEvent`: append-oriented record of meaningful system and analyst actions.
- `AIExecution`: provider/model/prompt version, timing, separate input/output and compatible total token usage where available, outcome, and safe error class.
- `AcquisitionRun`, `RawArtifact`, `CuratedRecord`, and `FieldLineage`: replayable source acquisition, content-addressed raw evidence, parser/schema versions, quarantine state, and field-level provenance.
- `ResearchCase`, `CaseEvidence`, `EvidenceClaim`, and `ResearchInference`: the shared signal-first, business-first, or hybrid case spine, with source-supported claims kept distinct from DealSage reasoning.
- `SourceCandidate` and `ResearchQuery`: bounded search provenance and discovered links that are not promoted to evidence or reusable connectors automatically.
- `ResearchFrontierItem` and `ResearchStep`: durable questions, attempts, budgets, actions, provider metadata, results, and explicit stopping behavior.
- `IdentityResolution`, `ClaimContradiction`, `ConfidenceAssessment`, and `AnalystConclusion`: reviewable identity hypotheses, intact conflicts, versioned deterministic confidence factors, and the separate human conclusion layer.

Partial seams: analyst notes are JSON records rather than a dedicated table; research jobs have an execution interface but no persistent job entity. Colorado and Texas provide bounded entity-corroboration adapters, while Utah has a fixture-tested three-file importer but its authorized live BEL delivery is pending. No owner-capable live adapter or live search provider exists. These are tracked honestly rather than hidden behind premature abstractions.
