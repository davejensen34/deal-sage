# Deployment

## Developer laptop

Run FastAPI with SQLite and Vite as documented in the README. No model credentials are required. Evidence artifacts use the local filesystem.

`AUTH_MODE=demo` supplies the clearly marked development analyst. Pilot deployments set `AUTH_MODE=oidc`; see `docs/deployment/pilot-authentication.md`.

## Single Docker host (recommended demo)

Run `docker compose up --build` on one modest Linux host. Compose starts PostgreSQL, runs the one-shot schema migration to completion, and only then starts FastAPI and Nginx. A failed or unrecognized migration prevents application traffic. The migration command supports empty databases, Alembic-versioned databases, and the exact additive gaps left by DealSage's historical `create_all` startup; it refuses incomplete unknown schemas rather than stamping them current. Put HTTPS at the host boundary and back up both durable volumes before upgrades. Keep secrets in host environment configuration.

Direct API development now requires `cd apps/api && alembic upgrade head` before starting Uvicorn. Schema creation is not an application-startup side effect.

## Future enterprise deployment

The same components can move to Azure, AWS, or GCP with managed PostgreSQL, S3-compatible storage, another standards-compliant OIDC provider, split workers, and OpenTelemetry export. Add autoscaling or Kubernetes only in response to measured demand.
