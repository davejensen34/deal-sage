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

OIDC startup fails closed when client credentials or a unique session secret are missing. Authentication errors return a branded, non-sensitive login message. Google behavior is covered by mocked tests but requires one deployment-specific live validation once credentials and a callback host are available.
