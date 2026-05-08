"""Integration tests — RLS isolation tenant A vs tenant B (CRITICAL BLOCKING).

Story SP04-AUTH-01 critical scenario #1: tenant A signup → user A1; tenant B
signup → user B1; tenant A login + JWT; com JWT_a → GET /tenant/users → assert
apenas user A1, NOT user B1. **MUST PASS** para Sprint 04 não mentir sobre
multi-tenancy.

Pre-requisito: PostgreSQL 16 rodando + ``DATABASE_URL`` env setada + migration
``sp04_001_auth_multitenant.sql`` aplicada. Quando ausente, tests skip com
clear marker para qa-gate G5 (rule story-lifecycle.md G5).

Setup local (Operator OR Eric):
    docker run -d --name revisor-pg-sp04 \\
      -e POSTGRES_USER=revisor -e POSTGRES_PASSWORD=revisor \\
      -e POSTGRES_DB=revisor_sp04 -p 5432:5432 postgres:16
    PGPASSWORD=revisor psql -h localhost -U revisor -d revisor_sp04 \\
      -f bloco_database/migrations/sp04_001_auth_multitenant.sql
    export DATABASE_URL=postgresql+asyncpg://revisor:revisor@localhost:5432/revisor_sp04
    export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
    pytest tests/integration/test_auth_rls_isolation.py -v

Cross-references:
    governance/stories/sp04-auth-01-multi-tenant-auth.md AC-08 + critical scenario #1
    governance/architecture/adr/adr-017-multi-tenant-isolation-rls.md §3 (RLS policies)
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest

from bloco_auth import db as sp04_db
from bloco_auth import jwt_utils, onboarding


# Skip TODO O MÓDULO se DATABASE_URL ausente — tests requerem PostgreSQL real.
# Marker explícito para qa-gate G5 ler em CI logs.
_REQUIRES_POSTGRES = pytest.mark.skipif(
    os.getenv("DATABASE_URL") is None,
    reason=(
        "RLS isolation test BLOCKING requer PostgreSQL real. "
        "Setup: docker run postgres:16 + apply migration + export DATABASE_URL. "
        "Ver docstring do módulo para comando exato. "
        "qa-gate G5 deve endereçar antes story closure."
    ),
)


_TEST_SECRET = "0123456789abcdef" * 4  # 64 bytes >= 32 bytes mín


@pytest.fixture(autouse=True)
def _jwt_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setup env vars JWT válidas para todos os tests do módulo."""
    monkeypatch.setenv("JWT_SECRET_KEY", _TEST_SECRET)
    monkeypatch.setenv("JWT_EXPIRY_HOURS", "24")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    jwt_utils._load_secret.cache_clear()
    yield
    jwt_utils._load_secret.cache_clear()


@pytest.fixture
async def db_engine() -> AsyncIterator[None]:
    """Reset do engine singleton entre tests para evitar cross-test pollution."""
    await sp04_db.reset_engine()
    yield
    await sp04_db.reset_engine()


@pytest.fixture
async def clean_db(db_engine: None) -> AsyncIterator[None]:
    """TRUNCATE tenants CASCADE entre tests (limpa users + dpa_acceptances)."""
    onboarding.reset_sessions()
    if os.getenv("DATABASE_URL") is None:
        yield
        return
    from sqlalchemy import text

    sessionmaker = sp04_db.get_sessionmaker()
    async with sessionmaker() as session:
        # TRUNCATE requer privilégio — em DBs gerenciados pode falhar; nesse
        # caso fallback DELETE FROM. Tabelas devem existir (migration aplicada).
        try:
            await session.execute(text("TRUNCATE tenants CASCADE"))
            await session.commit()
        except Exception:  # noqa: BLE001
            await session.rollback()
            await session.execute(text("DELETE FROM dpa_acceptances"))
            await session.execute(text("DELETE FROM users"))
            await session.execute(text("DELETE FROM tenants"))
            await session.commit()
    yield


# ──────────────────────────────────────────────────────────────────────────────
# Helper — full signup flow (steps 1-4) via Python API direto
# (evita dependência de TestClient HTTP — testa lógica pura de RLS)
# ──────────────────────────────────────────────────────────────────────────────


async def _signup_full(
    cnpj: str, razao_social: str, email: str, senha: str = "password123"
) -> tuple[str, str]:
    """Executa signup completo + retorna (tenant_id, jwt_token).

    Bypassa Anthropic ping (chunk 5+ usa httpx mock; aqui setamos step2 raw).
    """
    step1 = onboarding.OnboardingStep1Data(
        cnpj=cnpj,
        razao_social=razao_social,
        advogado_responsavel=razao_social,  # simplificação test
        email=email,
        senha=senha,
    )
    session_id = onboarding.start_session(step1)

    # Skip ping HTTP — direct store
    step2 = onboarding.OnboardingStep2Data(anthropic_api_key="sk-test-1234567890")
    onboarding.store_step(session_id, 2, step2)

    step3 = onboarding.OnboardingStep3Data(dpa_version="1.0.0", accepted=True)
    onboarding.store_step(session_id, 3, step3)

    step4 = onboarding.OnboardingStep4Data(tier="Starter")
    onboarding.store_step(session_id, 4, step4)

    sessionmaker = sp04_db.get_sessionmaker()
    async with sessionmaker() as session:
        tenant, user = await onboarding.complete_onboarding(session_id, session)

    token = jwt_utils.encode_jwt(tenant_id=tenant.id, user_id=user.id)
    return str(tenant.id), token


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rls_isolation_blocking(clean_db: None) -> None:
    """CRITICAL BLOCKING — tenant A não enxerga users de tenant B (Story #1).

    Cria 2 tenants + 1 user adicional cada (total 4 users no DB). Aplica RLS
    context tenant A → query users → assert apenas 2 rows (não 4).
    """
    from sqlalchemy import select

    from bloco_auth.middleware import apply_rls_context
    from bloco_auth.models import User
    from bloco_auth.passwords import hash_password

    # Tenant A signup (cria advogado responsável A1)
    tenant_a_id, _ = await _signup_full(
        cnpj="11222333000181", razao_social="Escritorio A", email="adv-a@example.com"
    )

    # Tenant B signup (cria advogado responsável B1) — CNPJ válido distinto
    tenant_b_id, _ = await _signup_full(
        cnpj="11444777000161", razao_social="Escritorio B", email="adv-b@example.com"
    )

    # Cria user A2 dentro tenant A (RLS scoped)
    sessionmaker = sp04_db.get_sessionmaker()
    from uuid import UUID

    tenant_a_uuid = UUID(tenant_a_id)
    tenant_b_uuid = UUID(tenant_b_id)

    async with sessionmaker() as session, apply_rls_context(session, tenant_a_uuid):
        session.add(
            User(
                tenant_id=tenant_a_uuid,
                email="user-a2@example.com",
                password_hash=hash_password("password123"),
                nome="User A2",
                status="active",
            )
        )

    # Cria user B2 dentro tenant B
    async with sessionmaker() as session, apply_rls_context(session, tenant_b_uuid):
        session.add(
            User(
                tenant_id=tenant_b_uuid,
                email="user-b2@example.com",
                password_hash=hash_password("password123"),
                nome="User B2",
                status="active",
            )
        )

    # Total no DB: 4 users (A1 + A2 + B1 + B2)
    # Com RLS context tenant A: deve enxergar apenas A1 + A2 (2 users)
    async with sessionmaker() as session, apply_rls_context(session, tenant_a_uuid):
        result = await session.execute(select(User))
        users_a = result.scalars().all()
    assert len(users_a) == 2, (
        f"RLS BLOCKING test FAILED: tenant A enxergou {len(users_a)} users "
        f"(esperado 2 — A1 + A2). LEAK CRITICAL — multi-tenancy quebrada."
    )
    assert all(u.tenant_id == tenant_a_uuid for u in users_a), (
        "RLS BLOCKING test FAILED: tenant A vê user com tenant_id != A"
    )

    # Cross-test: RLS context tenant B → apenas B1 + B2 (2 users)
    async with sessionmaker() as session, apply_rls_context(session, tenant_b_uuid):
        result = await session.execute(select(User))
        users_b = result.scalars().all()
    assert len(users_b) == 2, (
        f"RLS BLOCKING test FAILED: tenant B enxergou {len(users_b)} users "
        f"(esperado 2 — B1 + B2)."
    )

    # Cross-test inverso: emails A não devem aparecer em context B
    emails_b = {u.email for u in users_b}
    assert "adv-a@example.com" not in emails_b, "RLS LEAK: email A em context B"
    assert "user-a2@example.com" not in emails_b, "RLS LEAK: email A2 em context B"


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rls_isolation_dpa_acceptances(clean_db: None) -> None:
    """RLS também isola tabela ``dpa_acceptances`` (ADR-019 spec).

    Chunk 5 popula esta tabela via flow real; aqui validamos que policy
    ``tenant_isolation`` está ativa via INSERT direto + SELECT cross-tenant.
    """
    from datetime import datetime, timezone
    from uuid import UUID, uuid4

    from sqlalchemy import select

    from bloco_auth.middleware import apply_rls_context
    from bloco_auth.models import DpaAcceptance

    tenant_a_id, _ = await _signup_full(
        cnpj="11222333000181", razao_social="Escritorio A", email="adv-a@example.com"
    )
    tenant_a_uuid = UUID(tenant_a_id)

    sessionmaker = sp04_db.get_sessionmaker()
    # Pega user_id do advogado responsável (cross-tenant lookup sem RLS aqui não
    # é trivial — usamos session com context A para pegar user A1 via email)
    async with sessionmaker() as session, apply_rls_context(session, tenant_a_uuid):
        from bloco_auth.models import User

        result = await session.execute(select(User).where(User.email == "adv-a@example.com"))
        user_a1 = result.scalar_one()

        session.add(
            DpaAcceptance(
                tenant_id=tenant_a_uuid,
                dpa_version="1.0.0",
                dpa_text_hash="a" * 64,  # placeholder SHA-256 hex
                accepted_at=datetime.now(timezone.utc),
                accepted_by_user_id=user_a1.id,
                ip_address="192.0.2.1",
                user_agent="pytest",
            )
        )

    # Em context A: deve enxergar 1 dpa_acceptance
    async with sessionmaker() as session, apply_rls_context(session, tenant_a_uuid):
        result = await session.execute(select(DpaAcceptance))
        dpas_a = result.scalars().all()
    assert len(dpas_a) == 1

    # Em context fictício de outro tenant: NÃO deve enxergar a DPA de A
    fake_tenant_uuid = uuid4()
    async with sessionmaker() as session, apply_rls_context(session, fake_tenant_uuid):
        result = await session.execute(select(DpaAcceptance))
        dpas_fake = result.scalars().all()
    assert len(dpas_fake) == 0, "RLS LEAK: dpa_acceptances visível cross-tenant"


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_jwt_required_for_protected_endpoints(clean_db: None) -> None:
    """Sem Authorization header → 401 nos endpoints /api/tenant/users."""
    from httpx import ASGITransport, AsyncClient

    from bloco_interface.web.app import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/tenant/users")
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"].lower().startswith("bearer")


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_create_audit_event(clean_db: None, tmp_path) -> None:
    """POST /api/tenant/users registra event ``user_created`` em audit chain."""
    import json

    import httpx

    from bloco_audit import chain as audit_chain

    # Redirect audit log para tmp_path para isolar test
    test_audit_log = tmp_path / "audit.jsonl"
    original_default = audit_chain.DEFAULT_AUDIT_LOG
    audit_chain.DEFAULT_AUDIT_LOG = test_audit_log

    try:
        tenant_id, token = await _signup_full(
            cnpj="11222333000181",
            razao_social="Escritorio Audit",
            email="audit@example.com",
        )

        from bloco_interface.web.app import app

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/tenant/users",
                json={
                    "email": "novo-user@example.com",
                    "senha": "password123",
                    "nome": "Novo User",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 201, f"Create user falhou: {response.text}"

        # Verifica audit chain
        assert test_audit_log.exists(), "Audit log não foi criado"
        events = [json.loads(line) for line in test_audit_log.read_text().splitlines()]
        event_types = [e["event_type"] for e in events]
        assert "user_created" in event_types, f"Audit events: {event_types}"

        # Verifica payload contém tenant_id (multi-tenant adapt ADR-017 §6)
        user_created = next(e for e in events if e["event_type"] == "user_created")
        assert user_created["payload"]["tenant_id"] == tenant_id
    finally:
        audit_chain.DEFAULT_AUDIT_LOG = original_default
