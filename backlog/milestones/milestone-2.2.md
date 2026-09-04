# Milestone 2.2 — Live Local Google Authentication

Status: complete (September 4, 2026).

## Goal

Validate the real Google OIDC authorization-code flow end to end on localhost through the browser-facing DealSage proxy, without committing credentials or beginning Milestone 3.

## Definition of done

- Google console uses `http://localhost:3000` and the exact `/api/auth/callback` redirect.
- Compose accepts ignored `.env` OIDC settings instead of forcing demo mode.
- Login, verified email, JIT user creation, signed session, authenticated workspace, and audit attribution work with the live Google provider in a real browser. Allowlist rejection, logout, and subsequent sign-in are covered by automated integration tests.
- Automated authentication tests and the full stack remain green.
- Live-provider status and local-only security exception are documented accurately.

## Validation result

The localhost Compose stack completed Google's authorization-code flow through `http://localhost:3000/api/auth/callback`. Google discovery, token exchange, ID-token validation, the verified-email requirement, signed-session recovery, and the authenticated dashboard all succeeded. PostgreSQL contained one active Google-backed user, and opening a candidate while authenticated created a user-attributed `candidate_viewed` audit event.

No OAuth credentials or provider tokens were committed or persisted. The browser-facing diagnostic exposed only non-secret configuration. `SESSION_COOKIE_SECURE=false` remains an explicit localhost-only exception; a deployed environment must use HTTPS, a deployment-specific callback URI, and secure cookies.
