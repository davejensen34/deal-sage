# Data model

- `Business`: legal identity, location, industry, registration, and explicitly estimated business attributes.
- `Person`: identity attributes and aliases, independent of any company or signal.
- `BusinessRelationship`: typed person-to-business role with dates, activity, confidence, and evidence references.
- `Source`: publisher, canonical URL, dates, jurisdiction, reliability metadata, and demo marker.
- `Evidence`: subject-linked extracted and normalized facts, strength, extraction provenance, and fact/inference classification.
- `TransitionSignal`: generalized possible event; Milestone 1 primarily uses `possible_death` and one succession example.
- `CandidateMatch`: joins the person, business, relationship, signal, independent scores, conflicts, gaps, and recommendation.
- `ReviewCase`: assignment, status, decision, reason codes, and currently embedded analyst-note records.
- `AuditEvent`: append-oriented record of meaningful system and analyst actions.
- `AIExecution`: provider/model/prompt version, timing, usage where available, outcome, and error.

Partial seams: analyst notes are JSON records rather than a dedicated table; research jobs have an execution interface but no persistent job entity; source-registry metadata is represented in `Source` but no adapter registry exists. These are tracked honestly rather than hidden behind premature abstractions.
