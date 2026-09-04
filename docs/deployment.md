# Deployment

## Developer laptop

Run FastAPI with SQLite and Vite as documented in the README. This is the fewest-moving-parts path and needs no AI credentials. Evidence artifacts use the local filesystem.

## Single Docker host (recommended demo)

Run `docker compose up --build` on one modest Linux VM. Compose starts the static web proxy, API, and PostgreSQL with durable database and evidence volumes. Expose port 3000 behind HTTPS at the host boundary and back up both volumes. Keep secrets in the host environment, not the image or repository.

## Future enterprise deployment (concept only)

Package the same frontend and API for Azure, AWS, or GCP; use managed PostgreSQL and S3-compatible object storage; split scheduled jobs into workers; add autoscaling or Kubernetes only at demonstrated scale; replace demo auth with OIDC/Entra; export OpenTelemetry signals to an enterprise monitor. These are extension points, not current requirements.
