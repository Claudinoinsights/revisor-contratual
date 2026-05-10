"""Integration tests audit chain BYOK eventos (SP04-BYOK-01 chunk 7 / AC-08 + ADR-005).

Verifica que eventos byok_key_set/used/rotated/revoked são emitidos em audit
chain HMAC com payload contendo tenant_id + user_id + key_fingerprint truncated
(NUNCA full key — ADR-014 §6 + Tank Phase 12.3a).

Pre-requisito: PostgreSQL 16 + bloco_audit/chain.py configurado + sp04_002 migration.

Cross-references:
    governance/stories/sp04-byok-01-anthropic-key-lifecycle.md AC-08 audit chain
    governance/architecture/adr/adr-005-audit-log-integrity-hmac.md
    governance/architecture/adr/adr-014-provider-abstraction-byok.md §6 (audit truncated)
"""

from __future__ import annotations

import os

import pytest


_REQUIRES_POSTGRES = pytest.mark.skipif(
    os.getenv("DATABASE_URL") is None,
    reason="BYOK audit chain test requer PostgreSQL real. qa-gate G5 retest.",
)


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_byok_key_set_event_emitted_on_onboarding():
    """Onboarding completo → audit chain event byok_key_set com fingerprint truncated."""
    pytest.skip("Audit chain set E2E stub — qa-gate G5 retest")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_byok_key_used_event_on_inference_call():
    """Cada get_anthropic_client call emite byok_key_used (audit best-effort)."""
    pytest.skip("Audit chain used E2E stub — qa-gate G5 retest")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_byok_key_rotated_event_on_rotation_complete():
    """pg_cron complete_pending_rotations() emite byok_key_rotation_completed."""
    pytest.skip("Audit chain rotation E2E stub — qa-gate G5 retest com pg_cron")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_byok_key_revoked_event_emitted_on_revoke():
    """revoke endpoint emite byok_key_revoked com reason payload."""
    pytest.skip("Audit chain revoke E2E stub — qa-gate G5 retest")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_audit_payload_never_contains_full_api_key():
    """Audit log NUNCA contém api_key full — apenas fingerprint truncated 'sk-ant-...XYZ'."""
    pytest.skip("Audit security E2E stub — grep audit log por 'sk-ant-api03' full pattern")
