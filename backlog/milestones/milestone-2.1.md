# Milestone 2.1 — Research Trail and Pilot Identity

Status: implemented and validated in Issues #8–#10 and Pull Requests #11–#13.

Historical closeout record. Milestone 2.2 subsequently validated the real local Google flow; use `docs/project/current-state.md` for current authentication status.

## Goal

Make the evidence breadcrumb from target profile to transition-research-ready owner explicit and measurable, while supporting real pilot identities through standards-based OIDC without replacing local demo mode.

## Delivered

- Persisted target profiles, research trails, and ordered stage observations.
- Stage-local provenance, confidence, support, contradictions, gaps, and validation state.
- Deterministic owner-readiness gate and actual funnel counts.
- Progressive-disclosure Research workspace.
- Provider-neutral internal user identity, Google OIDC implementation, JIT provisioning, optional email/domain allowlists, signed server sessions, logout, and user-linked audit attribution.
- Demo identity remains credential-free and visibly distinct.

## Boundaries

No transition acquisition, obituary monitoring, national crawling, enterprise RBAC, organizations, Google API access, or provider-token persistence was added. Google is implemented and mock-validated but not live-provider validated because deployment credentials were not supplied.
