# Deployment

## Developer laptop

Run FastAPI with SQLite and Vite as documented in the README. No model credentials are required. Evidence artifacts use the local filesystem.

`AUTH_MODE=demo` supplies the clearly marked development analyst. Pilot deployments set `AUTH_MODE=oidc`; see `docs/deployment/pilot-authentication.md`.

## Single Docker host (recommended demo)

Run `docker compose up --build` on one modest Linux host. Compose starts Nginx, FastAPI, and PostgreSQL with durable database/evidence volumes. Put HTTPS at the host boundary and back up both volumes. Keep secrets in host environment configuration.

## Future enterprise deployment

The same components can move to Azure, AWS, or GCP with managed PostgreSQL, S3-compatible storage, another standards-compliant OIDC provider, split workers, and OpenTelemetry export. Add autoscaling or Kubernetes only in response to measured demand.
