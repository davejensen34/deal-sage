# Pilot authentication setup

## Local demo mode

Keep `AUTH_MODE=demo` and `SESSION_COOKIE_SECURE=false`. No external account or credentials are required. The UI and audit trail identify the actor as the configured demo analyst.

## Google pilot mode

1. In Google Cloud, create an OAuth 2.0 Web application client.
2. Add the exact authorized redirect URI used by DealSage, for example `https://pilot.example.com/api/auth/callback`.
3. Configure the deployment with:

```dotenv
AUTH_MODE=oidc
OIDC_PROVIDER=google
GOOGLE_CLIENT_ID=replace-at-deploy-time
GOOGLE_CLIENT_SECRET=replace-at-deploy-time
GOOGLE_REDIRECT_URI=https://pilot.example.com/api/auth/callback
WEB_APP_URL=https://pilot.example.com
SESSION_SECRET=generate-a-long-random-deployment-secret
SESSION_COOKIE_SECURE=true
ALLOWED_EMAILS=pilot1@example.com,pilot2@example.com
ALLOWED_DOMAINS=
```

Use either or both allowlist settings. Leaving both empty permits any identity accepted by the configured provider and is not recommended for a private pilot. Secrets belong in deployment configuration, never source control.

Login starts at `/api/auth/login`; the callback validates the provider response, creates or refreshes a DealSage user by `(provider, subject)`, and establishes a 12-hour server-signed session. Logout clears the DealSage session. Provider tokens are not persisted, and DealSage requests no Google API permissions.

OIDC startup fails closed when client credentials or a unique session secret are missing. Authentication errors return a branded, non-sensitive login message. Google behavior is covered by integration tests and was validated against the live provider on localhost on September 4, 2026. Every deployed callback host still requires its own provider-console configuration and live smoke test.

## Local Google validation with Docker Compose

In the Google OAuth web-client settings, add exactly:

- Authorized JavaScript origin: `http://localhost:3000`
- Authorized redirect URI: `http://localhost:3000/api/auth/callback`

Copy `.env.example` to the repository-root `.env`, set `AUTH_MODE=oidc`, insert the client ID and secret, generate a unique local session secret, and optionally allow the test email. Keep `SESSION_COOKIE_SECURE=false` only because localhost uses HTTP. Then run `docker compose up --build` and open `http://localhost:3000`; do not enter through port 8000 because the callback cookie and browser origin must remain consistent.

The non-secret `GET /api/auth/config` diagnostic reports the mode, provider, configured state, and effective callback URI. It never returns credentials. Google test-mode OAuth clients must also list the signing-in account as a test user when the consent screen is not published.

The completed localhost validation confirmed Google discovery and token exchange, verified-email enforcement, JIT user creation, signed-session recovery, protected workspace access, and user-linked audit attribution. Logout, repeat sign-in, and allowlist rejection are also exercised by the authentication integration suite. Do not carry `SESSION_COOKIE_SECURE=false` into a deployed environment.
