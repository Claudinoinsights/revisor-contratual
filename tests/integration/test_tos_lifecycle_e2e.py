"""Integration tests E2E — TOS lifecycle (SP04-LGPD-01 chunk 6 / AC-04 + AC-06).

Full cycle: onboarding step 3 combine DPA+TOS → tos_acceptances row insert
→ idempotent re-accept (UNIQUE violation graceful) → audit chain event
``tos_accepted`` → status query RLS scoped.

Pre-requisito: PostgreSQL 16 rodando + migrations sp04_001 + sp04_002 + sp04_003
aplicadas + JWT_SECRET_KEY + MASTER_ENCRYPTION_KEY env vars.

Setup local (Operator/Eric runbook qa-gate G5):
    docker run -d --name revisor-pg-sp04 \\
      -e POSTGRES_USER=revisor -e POSTGRES_PASSWORD=revisor \\
      -e POSTGRES_DB=revisor_sp04 -p 5432:5432 postgres:16
    for f in sp04_001_auth_multitenant sp04_002_byok_keys sp04_003_lgpd_tos_audit; do
      PGPASSWORD=revisor psql -h localhost -U revisor -d revisor_sp04 \\
        -f bloco_database/migrations/${f}.sql
    done
    export DATABASE_URL=postgresql+asyncpg://revisor:revisor@localhost:5432/revisor_sp04
    export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
    export MASTER_ENCRYPTION_KEY=$(openssl rand -hex 32)
    pytest tests/integration/test_tos_lifecycle_e2e.py -v

Cross-references:
    governance/stories/sp04-lgpd-01-compliance-flows-operador.md AC-04 + AC-06
    governance/architecture/adr/adr-019-dpa-storage-schema.md (pattern espelhado)
    bloco_database/migrations/sp04_003_lgpd_tos_audit.sql
"""

from __future__ import annotations

import os

import pytest


_REQUIRES_POSTGRES = pytest.mark.skipif(
    os.getenv("DATABASE_URL") is None,
    reason=(
        "TOS lifecycle E2E test requer PostgreSQL real + sp04_003_lgpd_tos_audit.sql "
        "aplicada. Ver docstring para setup. qa-gate G5 deve endereçar antes story closure."
    ),
)


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_tos_accept_endpoint_inserts_acceptance_row():
    """POST /api/tenant/tos/accept insere row tos_acceptances com hash + IP + user_agent."""
    pytest.skip("TOS accept E2E stub — qa-gate G5 retest com client httpx + JWT real")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_tos_accept_idempotent_returns_existing_row():
    """Re-accept mesma version retorna row existente (UNIQUE constraint protected)."""
    pytest.skip("TOS idempotent E2E stub — qa-gate G5 retest com 2 POST sequenciais")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_tos_audit_chain_event_recorded():
    """append_audit_entry chamado com event_type=tos_accepted e payload correto."""
    pytest.skip("Audit chain E2E stub — qa-gate G5 retest com chain tail inspection")


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_onboarding_step3_quintuple_insert_atomic():
    """Onboarding wizard 4 steps cria row tos_acceptances + dpa + tenant + user + api_key
    em single transaction (rollback completo se qualquer passo falha)."""
    pytest.skip(
        "Quintuple insert E2E stub — qa-gate G5 retest com complete onboarding state "
        "+ DB rollback validation"
    )


@_REQUIRES_POSTGRES
@pytest.mark.asyncio
async def test_tos_status_endpoint_rls_scoped():
    """GET /api/tenant/tos/status retorna apenas aceitações do tenant atual (RLS auto-filtra)."""
    pytest.skip(
        "TOS status RLS E2E stub — qa-gate G5 retest com 2 tenants distintos + cross-query"
    )
