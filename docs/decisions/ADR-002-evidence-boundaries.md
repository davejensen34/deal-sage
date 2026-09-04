# ADR-002: Evidence and decision boundaries

Status: accepted.

## Context

The central risk is falsely joining a transition signal to a business-associated person.

## Decision

Represent sources, evidence, relationships, signals, candidate inferences, review cases, and audit events separately. Preserve three confidence values. Registered-agent or executive status does not imply ownership.

## Rationale

Analysts need traceability and the ability to disagree with the system. One lead row or model-generated conclusion cannot provide that trust.

## Consequences

The domain has more entities and joins, but provenance and corrections remain explicit. UX must continue labeling source facts, inference, and analyst decisions.
