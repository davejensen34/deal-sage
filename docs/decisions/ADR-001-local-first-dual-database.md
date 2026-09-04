# ADR-001: Local-first dual database

Status: accepted.

## Context

Development and demos need minimal cost while shared testing needs realistic multi-user database behavior.

## Decision

Use SQLAlchemy with SQLite for minimal local mode and PostgreSQL for Docker/shared mode. Keep database-native search behind the API; do not add a search cluster.

## Rationale

This minimizes operations, keeps one domain implementation, and preserves a path to PostgreSQL full-text search and pgvector.

## Consequences

Queries must remain portable until database-specific search adapters are introduced. SQLite concurrency is suitable only for local/demo use.
