# ADR-012: Single-organization pilot authorization

Status: accepted for Milestone 6.

## Context

OIDC established durable identity and attribution, but every authenticated user retained the same effective access. The pilot needs server-side separation between reading evidence, analyst judgment, source/model spending, and access administration without introducing enterprise organizations or an external policy service.

## Decision

Persist one role on each pilot user: `viewer`, `analyst`, `operator`, or `administrator`. New just-in-time OIDC users start as `viewer`. The role hierarchy is implemented as named permissions rather than route-name checks:

| Role | Permissions |
| --- | --- |
| viewer | Authenticated read access |
| analyst | Personal saved research/watchlists/alerts, review decisions, and bounded export |
| operator | Analyst permissions plus source refresh and live model execution |
| administrator | Operator permissions plus local user-access administration |

Existing users are migrated to `administrator` because they previously possessed every capability. `demo` is a visibly non-production identity with all demo capabilities and is never persisted as a pilot role. User role and active state changes occur through the local operator command and append an audit event. Deactivation is enforced on the next authenticated request.

Every denied permission appends only the actor, named permission, method, and route; request bodies are never retained. OIDC-mode unsafe API methods also require `X-DealSage-CSRF: 1`. A browser form cannot set that custom header, and the existing restrictive CORS allowlist controls which origins may send it with credentials.

## Consequences

Authorization remains suitable for one trusted pilot organization, not tenant isolation. There is no browser-only security boundary: the API decides every permission. Administrators still require local host/database access to change roles; a self-service administration UI, invitations, SCIM, organization hierarchy, and external policy engine remain out of scope.
