# ADR-003: Deterministic scoring and provider-neutral AI

## Context

Models can interpret unstructured evidence but are unsuitable as an opaque authority for candidate ranking.

## Decision

Use configurable deterministic scoring and a conjunctive overall formula. Keep optional OpenAI and Anthropic capabilities behind a DealSage-owned provider interface with versioned prompts and execution provenance.

## Rationale

This yields explainable, testable scores while preserving model choice for tasks that benefit from language understanding.

## Consequences

Evidence feature observations must eventually be persisted and recalculated. Provider adapters require explicit live validation before being called validated.
