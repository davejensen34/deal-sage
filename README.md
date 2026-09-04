# DealSage

DealSage is an open-source, evidence-backed business ownership intelligence and transition research platform. It helps analysts connect public transition signals to privately held businesses while keeping source facts, DealSage inferences, uncertainty, and human decisions visibly distinct.

> All included names, companies, records, and evidence are fictional demo data. Confidence scores prioritize research; they are not assertions of fact.

## Current capabilities

- Persisted dashboard, candidate queue, database-native search, filters, sorting, and pagination
- Candidate detail centered on business-control and signal-identity questions
- Independent relationship, identity, and overall confidence scores with explanations
- Source-attributed evidence, contradictions, missing evidence, and provenance
- Validate, reject, watchlist, needs-more-research, notes, and audit history
- 18 deliberately varied fictional cases, including collisions and false positives
- SQLite locally; PostgreSQL in Docker Compose
- Optional OpenAI or Anthropic evidence summary behind a provider abstraction
- Evidence-backed business → entity → web → person → owner-ready research trails and measured funnel stages
- Credential-free demo identity plus provider-neutral pilot OIDC with Google as the initial provider
- OpenAPI at `http://localhost:8000/docs`

## Run locally (SQLite)

Requirements: Python 3.11+ and Node.js 20+.

```bash
cp .env.example .env
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,ai]'
uvicorn app.main:app --reload
```

In a second terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:5173`. The API creates and seeds SQLite automatically on first start. AI packages are optional; use `pip install -e '.[dev]'` for a credential-free installation.

## Run with Docker/PostgreSQL

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:3000`. Everything runs on one host; no managed service is required.

## Optional AI summary

Set either `MODEL_PROVIDER=openai` with `OPENAI_API_KEY`, or `MODEL_PROVIDER=anthropic` with `ANTHROPIC_API_KEY`. Models are configurable in `.env`. DealSage works fully with `MODEL_PROVIDER=disabled`, and AI never determines the score.

## Pilot authentication

Local development defaults to `AUTH_MODE=demo`. For Google pilot login, configure OIDC credentials, a unique session secret, HTTPS cookies, and an email/domain allowlist as described in the [pilot authentication guide](docs/deployment/pilot-authentication.md).

## Tests

```bash
cd apps/api && pytest
cd apps/web && npm test
```

## Architecture

The React/TypeScript client communicates with a FastAPI service. SQLAlchemy keeps SQLite and PostgreSQL interchangeable. Domain entities separate people, businesses, relationships, sources, evidence, signals, candidate conclusions, reviews, and audits. Start with the [product vision](docs/product/vision.md) and [current state](docs/project/current-state.md), then see the [architecture](docs/architecture/architecture.md), [confidence model](docs/architecture/confidence-model.md), [deployment](docs/architecture/deployment.md), and [responsible research](docs/governance/responsible-research.md).

## Current limitations

The application uses fictional seeded trails and does not yet discover owners or transition signals from the web. Google OIDC is implemented and mock-tested but awaits live validation with deployment credentials. Search uses portable database filtering rather than FTS5/pg_trgm optimization. Scheduled acquisition, organizations, enterprise RBAC, and multi-tenancy are intentionally deferred.

## Responsible use

DealSage is a research aid, not a source of truth. Users must inspect attributed evidence, resolve ambiguity, correct bad matches, and remain responsible for downstream actions. The project does not support bypassing authentication, paywalls, CAPTCHAs, or publisher controls.

## License

Apache License 2.0. See [LICENSE](LICENSE).
