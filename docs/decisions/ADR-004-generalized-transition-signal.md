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

## Milestone 7 implementation boundary

Issue #128 introduces the immutable `transition-policy-v1` catalog in `app/domain/transition_policies.py` and authenticated `GET /api/research/transition-policies`. It is research guidance, not a claim validator or promotion permission. Eight initial policies distinguish person, business, and relationship subjects, event versus publication time, and signal-specific ownership limitations. Transfer uses the canonical `ownership_change` key. Unknown stored types remain readable but cannot resolve to a default mortality policy; additional types require explicit policy work. Issue #129 integrates these policies into the existing case and analyst-review path. No schema migration or historical record rewrite is needed for this catalog.
