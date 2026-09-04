# ADR-006: Provider-neutral pilot identity

Status: accepted. The real Google flow was subsequently validated on localhost in Milestone 2.2; current setup and validation status are in `docs/deployment/pilot-authentication.md`.

## Context

DealSage needs real pilot-user identity and attributable actions without managing passwords or building enterprise organizations and RBAC. Credential-free local development must remain simple.

## Decision

Support `demo` and `oidc` authentication modes behind one internal identity dependency. OIDC uses the standard authorization-code flow through Authlib, with Google discovery as the initial provider. DealSage stores an internal user keyed by provider plus stable subject, not email, and stores no provider access token. Server sessions contain only the internal user ID.

Pilot deployments use a unique signing secret, HTTPS-only HttpOnly SameSite cookies, OIDC state/nonce validation supplied by the library, and optional exact-email/domain allowlists. Demo mode returns an explicitly marked local identity. Audit records preserve their historical actor text while new authenticated actions also record internal user ID.

## Consequences

Google login provides no Google API access and requests only OpenID profile/email scopes. Future standards-compliant providers can reuse the internal user boundary. Invitations, organizations, multi-tenancy, RBAC, token persistence, and Entra ID remain out of scope. Mocked OIDC behavior is CI-validated; Google remains implemented but not live-provider validated until credentials are supplied.
