# Architecture

## Implemented now

```mermaid
flowchart LR
  Signal[Transition-signal sources] --> Jobs[Acquisition / job seam]
  Registry[Business and licensing sources] --> Jobs
  Seed[Fictional demo sources] --> Jobs
  Jobs --> Landing[Immutable raw and curated landing]
  Landing --> Extract[Structured evidence]
  Extract --> Resolve[Person and business resolution]
  Resolve --> Graph[Evidence domain model]
  Graph --> Score[Deterministic scoring]
  Score --> Review[Human review]
  Review --> App[DealSage web application]
  AI[OpenAI / Claude] -. optional extraction and synthesis .-> Extract
  AI -. optional analyst summary .-> Review
```

React/Vite provides the analyst workspace. FastAPI exposes REST/OpenAPI contracts. SQLAlchemy supports SQLite and PostgreSQL. Local evidence storage sits behind an interface. Demo authentication supplies one analyst. Request IDs are logged; model executions and analyst actions persist separately.

Source facts, normalized facts, DealSage inferences, and human decisions are separate concepts. `BusinessRelationship` preserves role semantics: registered-agent or executive status never proves ownership.

Discovery is not business-name dependent. A research path may begin with a transition signal or unresolved person, then discover and validate a candidate business; known-business and hybrid paths remain supported. Authoritative registries corroborate entities and relationships but do not define the only acquisition universe.

## Future extension points

Source adapters can add HTTPX, Trafilatura, Playwright, or Scrapy under source-specific rules. Persistent jobs may start in-process and later use a queue when scale proves the need. Local storage can move to S3-compatible storage. PostgreSQL can add pg_trgm and pgvector. OIDC, managed PostgreSQL, distributed workers, Kubernetes, and enterprise telemetry remain options—not dependencies.
