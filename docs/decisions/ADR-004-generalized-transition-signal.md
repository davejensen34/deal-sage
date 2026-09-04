# ADR-004: Generalized transition signals

Status: accepted.

## Context

Possible owner death is the initial differentiator, not the entire product category.

## Decision

Model events as typed `TransitionSignal` records, initially centered on `possible_death`, with future retirement, succession, ownership change, founder exit, estate transition, dissolution, leadership change, and other types.

## Rationale

The evidence and identity-resolution workflow applies across transition types and should not require a domain rewrite.

## Consequences

UI language and APIs must avoid assuming every signal is an obituary or death.
