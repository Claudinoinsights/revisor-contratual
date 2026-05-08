"""bloco_auth — Sprint 04 multi-tenant authentication + onboarding (SP04-AUTH-01).

Foundation P0 do Sprint 04 Cloud SaaS BYOK pivot. Implementa:

- Schema PostgreSQL ``tenants`` + ``users`` (ADR-017 BACKBONE pattern)
- JWT HS256 login com claims ``tenant_id`` + ``user_id`` (FR-AUTH-03)
- Bcrypt password hashing (cost factor 12)
- DPA acceptance flow integrado (ADR-019 ``dpa_acceptances``)
- Onboarding wizard 4 passos (Sati S2 UX wireframe)
- Audit chain HMAC adapt para multi-tenant (ADR-005 preservado)

Cross-references:
    governance/stories/sp04-auth-01-multi-tenant-auth.md (story spec — 8 ACs)
    governance/architecture/adr/adr-017-multi-tenant-isolation-rls.md (BACKBONE)
    governance/architecture/adr/adr-019-dpa-storage-schema.md (level=spec)
    governance/architecture/adr/adr-014-provider-abstraction-byok.md (BYOK)
    governance/prd/prd-v2.0.0-DRAFT.md Section 4 (FR-AUTH-01..03)
"""

__all__: list[str] = []
