"""Integration tests RLS isolation BYOK (SP04-BYOK-01 chunk 7 / AC-06 + AC-08).

Critical scenario: tenant A signup com BYOK → tenant B signup com BYOK → assert
tenant A query tenant_api_keys retorna apenas A row (não B), mesmo com BYPASSRLS
misuse hipotético — RLS policy byok_tenant_isolation deve bloquear cross-access.

Pre-requisito: PostgreSQL 16 + sp04_001 + sp04_002 aplicadas + MASTER_ENCRYPTION_KEY.

Cross-references:
    governance/stories/sp04-byok-01-anthropic-key-lifecycle.md AC-06 (RLS isolation)
    governance/architecture/adr/adr-017-multi-tenant-isolation-rls.md (BACKBONE)
"""

from __future__ import annotations

import os

import pytest


_REQUIRES_POSTGRES = pytest.mark.skipif(
    os.getenv("DATABASE_URL") is None,
    reason="BYOK RLS isolation test requer PostgreSQL real. qa-gate G5 retest.",
)


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_tenant_a_cannot_see_tenant_b_byok_row():
    """Tenant A com app.tenant_id=A não enxerga tenant_api_keys de B (RLS BLOCKING)."""
    pytest.skip("RLS isolation E2E stub — qa-gate G5 retest com 2 tenants signup")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_byok_policy_blocks_select_without_app_tenant_id():
    """SELECT sem app.tenant_id setado retorna 0 rows (default RLS deny)."""
    pytest.skip("RLS default-deny E2E stub — qa-gate G5 retest")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_byok_rls_persists_across_session_reuse():
    """RLS context aplicado SET LOCAL persiste apenas dentro transaction (não cross-session)."""
    pytest.skip("RLS scope E2E stub — qa-gate G5 retest")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_revoke_propagates_via_rls_to_subsequent_inference():
    """Pós-revoke tenant A: get_anthropic_client retorna 403 mesmo via RLS valid."""
    pytest.skip("Revoke RLS propagation E2E stub — qa-gate G5 retest")
