"""Integration tests E2E — BYOK lifecycle (SP04-BYOK-01 chunk 7 / AC-04 + AC-05 + AC-06).

Full cycle: signup → tenant_api_keys row → first inference call (decrypt + inject SDK)
→ rotate flow → revoke flow → re-onboarding cycle. Pre-requisito: PostgreSQL 16
rodando + migrations sp04_001 + sp04_002 aplicadas + MASTER_ENCRYPTION_KEY env.

Setup local (Operator/Eric runbook qa-gate G5):
    docker run -d --name revisor-pg-sp04 \\
      -e POSTGRES_USER=revisor -e POSTGRES_PASSWORD=revisor \\
      -e POSTGRES_DB=revisor_sp04 -p 5432:5432 postgres:16
    PGPASSWORD=revisor psql -h localhost -U revisor -d revisor_sp04 \\
      -f bloco_database/migrations/sp04_001_auth_multitenant.sql
    PGPASSWORD=revisor psql -h localhost -U revisor -d revisor_sp04 \\
      -f bloco_database/migrations/sp04_002_byok_keys.sql
    export DATABASE_URL=postgresql+asyncpg://revisor:revisor@localhost:5432/revisor_sp04
    export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
    export MASTER_ENCRYPTION_KEY=$(openssl rand -hex 32)
    pytest tests/integration/test_byok_lifecycle_e2e.py -v

Cross-references:
    governance/stories/sp04-byok-01-anthropic-key-lifecycle.md AC-04 + AC-08
    governance/architecture/adr/adr-014-provider-abstraction-byok.md
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bloco_auth import byok_encryption, byok_lifecycle, db as sp04_db


_REQUIRES_POSTGRES = pytest.mark.skipif(
    os.getenv("DATABASE_URL") is None,
    reason=(
        "BYOK lifecycle E2E test requer PostgreSQL real + sp04_002_byok_keys.sql aplicada. "
        "Ver docstring para setup. qa-gate G5 deve endereçar antes story closure."
    ),
)


_TEST_MASTER_KEY = "0123456789abcdef" * 4
_TEST_API_KEY = "sk-ant-api03-test-fake-key-for-byok-encryption-roundtrip-XYZ"


@pytest.fixture(autouse=True)
def _byok_env(monkeypatch):
    monkeypatch.setenv("MASTER_ENCRYPTION_KEY", _TEST_MASTER_KEY)
    byok_encryption._load_master_key.cache_clear()
    yield
    byok_encryption._load_master_key.cache_clear()


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_byok_encrypt_decrypt_roundtrip_real_postgres():
    """Encrypt + decrypt roundtrip via pgcrypto real (não mock)."""
    sessionmaker = sp04_db.get_sessionmaker()
    async with sessionmaker() as session:
        encrypted = await byok_encryption.encrypt_api_key(_TEST_API_KEY, session)
        assert encrypted != _TEST_API_KEY.encode()
        assert isinstance(encrypted, bytes)

        decrypted = await byok_encryption.decrypt_api_key(encrypted, session)
        assert decrypted == _TEST_API_KEY


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_onboarding_creates_tenant_api_keys_row():
    """E2E onboarding wizard 4 steps cria row tenant_api_keys com encrypted + fingerprint."""
    # Stub — full impl deferred qa-gate G5 (requires complete onboarding state setup)
    pytest.skip("E2E onboarding test stub — qa-gate G5 retest com DB completo")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_get_anthropic_client_decrypts_and_returns_sdk():
    """Middleware get_anthropic_client decrypta blob real + retorna Anthropic SDK."""
    pytest.skip("Middleware E2E stub — qa-gate G5 retest com mock anthropic.Anthropic + DB")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_rotation_flow_pending_to_active():
    """start_rotation → wait 24h (mock datetime) → pg_cron complete_pending_rotations()."""
    pytest.skip("Rotation E2E stub — qa-gate G5 retest com pg_cron simulation")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_revoke_purges_encrypted_and_suspends_tenant():
    """revoke → encrypted_key=NULL + tenant.status='suspended_byok' + 403 subsequent."""
    pytest.skip("Revoke E2E stub — qa-gate G5 retest com get_anthropic_client 403 verify")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_re_onboarding_after_revoke_restores_tenant():
    """Pós-revoke + re-onboarding step2 → tenant.status='active' + nova encrypted blob."""
    pytest.skip("Re-onboarding E2E stub — qa-gate G5 retest com flow completo")
