# Deployment

## Developer laptop

Run FastAPI with SQLite and Vite as documented in the README. No model credentials are required. Evidence artifacts use the local filesystem.

## Single Docker host (recommended demo)

Run `docker compose up --build` on one modest Linux host. Compose starts Nginx, FastAPI, and PostgreSQL with durable database/evidence volumes. Put HTTPS at the host boundary and back up both volumes. Keep secrets in host environment configuration.

## Future enterprise deployment

The same components can move to Azure, AWS, or GCP with managed PostgreSQL, S3-compatible storage, OIDC, split workers, and OpenTelemetry export. Add autoscaling or Kubernetes only in response to measured demand. These are conceptual extension points, not Milestone 1 requirements.
