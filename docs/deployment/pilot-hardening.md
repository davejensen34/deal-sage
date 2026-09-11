# Pilot deployment and performance baseline

The default `docker-compose.yml` remains an explicitly local development stack. It is not a production template. A pilot launch uses the hardening overlay:

```bash
docker compose -f docker-compose.yml -f docker-compose.pilot.yml up --build -d --wait
```

The overlay requires a unique URL-safe PostgreSQL password, a unique 32+ character session secret, Google client credentials, HTTPS web/callback URLs, an explicit public hostname, and an email or domain allowlist. It adds only the explicit `api` and `127.0.0.1` internal hosts needed for proxy and health-check traffic. The application additionally fails startup when `DEPLOYMENT_ENVIRONMENT=pilot` is combined with demo authentication, insecure cookies, HTTP origins, wildcard hosts, an absent allowlist, or the development database password. TLS terminates at the host or cloud ingress; the bundled Nginx container remains private HTTP behind that boundary.

Nginx applies a restrictive content-security policy, clickjacking, content-type, referrer, permissions, and HSTS headers. It forwards the original host, scheme, client chain, and request ID. FastAPI accepts only configured hosts. Uvicorn trusts forwarded headers because its port is not published and only the internal Compose proxy can reach it; do not publish the API container while `FORWARDED_ALLOW_IPS=*` is configured.

Both API and web containers have liveness checks. Web startup waits for the API to become healthy, and Nginx resolves the API through Docker DNS with a short validity period so API recreation does not leave a stale upstream address. The migration container must still finish successfully before API startup.

## Performance baseline

`tests/test_performance_baseline.py` runs five iterations of each representative operation against the deterministic in-process SQLite/fixture stack. It makes no network or model call. The September 11, 2026 observed maxima were:

| Operation | Observed maximum | Pilot regression budget |
| --- | ---: | ---: |
| Candidate queue, 100 rows | 16.6 ms | 250 ms |
| Candidate detail with evidence/audit | 35.5 ms | 250 ms |
| Workflow-effectiveness research aggregate | 4.4 ms | 500 ms |
| Provenance-safe 100-row JSON export | 10.0 ms | 500 ms |
| One-record fixture-backed refresh | 13.0 ms | 1,000 ms |

These are regression budgets, not production load-test claims or service-level objectives. They justify making no new index, PostgreSQL-specific search, cache, queue, or worker change in Milestone 6. Re-measure with realistic pilot volume before changing storage or topology.

## Release checks

CI now builds and waits for the complete PostgreSQL → migration → API → Nginx stack, then verifies public liveness and aggregate readiness. It audits installed Python dependencies (including optional AI adapters), production npm dependencies, and both built container images for fixed high/critical vulnerabilities. A release is blocked by a finding until it is upgraded, shown not to apply, or recorded in a time-bounded Issue with owner and rationale. Scanner output must never include `.env` or credentials.
