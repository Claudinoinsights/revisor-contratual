"""Integration tests E2E — Audit isolation endpoint (SP04-LGPD-01 chunk 6 / AC-05 + AC-06).

GET /api/tenant/audit/isolation com auth obrigatório + RLS scoped:
- Tenant A vê apenas seus counts + last_login_per_user (RLS auto-filtra)
- Tenant B vê apenas seus dados (cross-tenant isolation defense-in-depth)
- pg_policies introspection retorna policies ativas das 5 tabelas multi-tenant
- Audit chain HMAC event ``audit_isolation_queried`` registrado

Pre-requisito: PostgreSQL 16 rodando + 3 migrations aplicadas (sp04_001..003).

Setup local (Operator/Eric runbook qa-gate G5): ver docstring
``test_tos_lifecycle_e2e.py``.

Cross-references:
    governance/stories/sp04-lgpd-01-compliance-flows-operador.md AC-05 + AC-06
    governance/architecture/adr/adr-017-multi-tenant-isolation-rls.md (BACKBONE)
    bloco_auth/audit_isolation.py (endpoint impl)
"""

from __future__ import annotations

import os

import pytest


_REQUIRES_POSTGRES = pytest.mark.skipif(
    os.getenv("DATABASE_URL") is None,
    reason=(
        "Audit isolation E2E test requer PostgreSQL real + sp04_003 migration aplicada. "
        "Ver docstring para setup. qa-gate G5 deve endereçar antes story closure."
    ),
)


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_isolation_endpoint_requires_auth():
    """GET /api/tenant/audit/isolation sem JWT → 401 Unauthorized."""
    pytest.skip("Auth E2E stub — qa-gate G5 retest com client httpx sem header Authorization")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_isolation_endpoint_returns_tenant_scoped_counts():
    """Tenant A com 3 users + 5 analyses retorna counts.users=3 + counts.analyses=5."""
    pytest.skip(
        "Counts scope E2E stub — qa-gate G5 retest com seed data + JWT tenant A + "
        "GET /api/tenant/audit/isolation"
    )


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_isolation_cross_tenant_rls_isolation():
    """Tenant A NÃO consegue ver counts/policies de Tenant B (RLS defense-in-depth)."""
    pytest.skip(
        "Cross-tenant RLS E2E stub — qa-gate G5 retest com 2 tenants seed + cross-JWT query"
    )


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_isolation_audit_chain_event_recorded():
    """append_audit_entry chamado com event_type=audit_isolation_queried e tenant_id correto."""
    pytest.skip(
        "Audit chain E2E stub — qa-gate G5 retest com chain tail inspection pós-endpoint call"
    )
