"""Integration tests — Users CRUD scoped + cross-tenant isolation (SP04-AUTH-01).

Verifica AC-04 (CRUD scoped via RLS) + critical scenario #1 (RLS cross-tenant
isolation). Pre-requisito: PostgreSQL real + DATABASE_URL setada + migration.

Tests skipped via _REQUIRES_POSTGRES quando DB ausente.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest

from bloco_auth import db as sp04_db
from bloco_auth import jwt_utils, onboarding


_REQUIRES_POSTGRES = pytest.mark.skipif(
    os.getenv("DATABASE_URL") is None,
    reason="Users CRUD test requer PostgreSQL real (qa-gate G5).",
)


_TEST_SECRET = "0123456789abcdef" * 4


@pytest.fixture(autouse=True)
def _jwt_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", _TEST_SECRET)
    monkeypatch.setenv("JWT_EXPIRY_HOURS", "24")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    jwt_utils._load_secret.cache_clear()
    yield
    jwt_utils._load_secret.cache_clear()


@pytest.fixture
async def db_engine() -> AsyncIterator[None]:
    await sp04_db.reset_engine()
    yield
    await sp04_db.reset_engine()


@pytest.fixture
async def clean_db(db_engine: None) -> AsyncIterator[None]:
    onboarding.reset_sessions()
    if os.getenv("DATABASE_URL") is None:
        yield
        return
    from sqlalchemy import text

    sessionmaker = sp04_db.get_sessionmaker()
    async with sessionmaker() as session:
        try:
            await session.execute(text("TRUNCATE tenants CASCADE"))
            await session.commit()
        except Exception:  # noqa: BLE001
            await session.rollback()
    yield


async def _signup_full(cnpj: str, email: str, senha: str = "senha-forte-12345") -> tuple[str, str]:
    """Helper — signup full flow + retorna (tenant_id, jwt_token)."""
    step1 = onboarding.OnboardingStep1Data(
        cnpj=cnpj,
        razao_social=f"Escritório {cnpj}",
        advogado_responsavel="Test User",
        email=email,
        senha=senha,
    )
    sid = onboarding.start_session(step1)
    onboarding.store_step(sid, 2, onboarding.OnboardingStep2Data(anthropic_api_key="sk-test-1234567890"))
    onboarding.store_step(sid, 3, onboarding.OnboardingStep3Data(dpa_version="1.0.0", accepted=True))
    onboarding.store_step(sid, 4, onboarding.OnboardingStep4Data(tier="Starter"))

    sessionmaker = sp04_db.get_sessionmaker()
    async with sessionmaker() as session:
        tenant, user = await onboarding.complete_onboarding(sid, session)

    token = jwt_utils.encode_jwt(tenant_id=tenant.id, user_id=user.id)
    return str(tenant.id), token


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_user_within_tenant(clean_db: None, tmp_path) -> None:
    """JWT_a + POST /tenant/users → 201 + audit user_created tenant_id payload."""
    import json

    from bloco_audit import chain as audit_chain
    from httpx import ASGITransport, AsyncClient

    from bloco_interface.web.app import app

    test_log = tmp_path / "audit.jsonl"
    audit_chain.DEFAULT_AUDIT_LOG = test_log

    try:
        tenant_id, token = await _signup_full("11222333000181", "create-test@a.com")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                "/api/tenant/users",
                json={"email": "novo@a.com", "senha": "senha12345", "nome": "Novo User"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 201
        body = r.json()
        assert body["email"] == "novo@a.com"
        assert body["status"] == "active"

        # Verify audit
        events = [json.loads(line) for line in test_log.read_text().splitlines()]
        user_created = [e for e in events if e["event_type"] == "user_created"]
        assert len(user_created) == 1
        assert user_created[0]["payload"]["tenant_id"] == tenant_id
    finally:
        # restore default
        from pathlib import Path
        audit_chain.DEFAULT_AUDIT_LOG = Path.home() / ".local" / "share" / "revisor-contratual" / "audit.jsonl"


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_users_rls_scoped(clean_db: None) -> None:
    """tenant A vê apenas A users; tenant B vê apenas B users."""
    from httpx import ASGITransport, AsyncClient

    from bloco_interface.web.app import app

    tenant_a_id, token_a = await _signup_full("11222333000181", "adv-a@a.com")
    tenant_b_id, token_b = await _signup_full("11444777000161", "adv-b@b.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Cria user A2
        await client.post("/api/tenant/users",
                          json={"email": "a2@a.com", "senha": "senha12345", "nome": "User A2"},
                          headers={"Authorization": f"Bearer {token_a}"})
        # Cria user B2
        await client.post("/api/tenant/users",
                          json={"email": "b2@b.com", "senha": "senha12345", "nome": "User B2"},
                          headers={"Authorization": f"Bearer {token_b}"})

        # GET /tenant/users com JWT_a — apenas A users (advogado A1 + A2 = 2)
        ra = await client.get("/api/tenant/users", headers={"Authorization": f"Bearer {token_a}"})
        users_a = ra.json()
        assert ra.status_code == 200
        assert len(users_a) == 2
        emails_a = {u["email"] for u in users_a}
        assert "adv-a@a.com" in emails_a
        assert "a2@a.com" in emails_a
        assert "adv-b@b.com" not in emails_a
        assert "b2@b.com" not in emails_a

        # GET com JWT_b — apenas B users
        rb = await client.get("/api/tenant/users", headers={"Authorization": f"Bearer {token_b}"})
        users_b = rb.json()
        assert len(users_b) == 2
        emails_b = {u["email"] for u in users_b}
        assert "adv-b@b.com" in emails_b
        assert "b2@b.com" in emails_b
        assert "adv-a@a.com" not in emails_b


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_patch_user_rls_blocks_cross_tenant(clean_db: None) -> None:
    """JWT_a + PATCH user_b_id → 404 (RLS impede tocar user de B)."""
    from httpx import ASGITransport, AsyncClient

    from bloco_interface.web.app import app

    tenant_a_id, token_a = await _signup_full("11222333000181", "adv-a@a.com")
    tenant_b_id, token_b = await _signup_full("11444777000161", "adv-b@b.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Pega user_id de B
        rb = await client.get("/api/tenant/users", headers={"Authorization": f"Bearer {token_b}"})
        user_b_id = rb.json()[0]["id"]

        # JWT_a tenta atualizar user de B
        r = await client.patch(
            f"/api/tenant/users/{user_b_id}",
            json={"nome": "Hacker"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
    # RLS retorna 404 (não 403 — não revela existência cross-tenant)
    assert r.status_code == 404


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_user_soft_delete(clean_db: None) -> None:
    """DELETE → 204 + status='suspended' + audit user_suspended."""
    from httpx import ASGITransport, AsyncClient

    from bloco_interface.web.app import app

    tenant_id, token = await _signup_full("11222333000181", "soft-del@a.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Cria user A2
        rcreate = await client.post(
            "/api/tenant/users",
            json={"email": "to-delete@a.com", "senha": "senha12345", "nome": "Will Be Deleted"},
            headers={"Authorization": f"Bearer {token}"},
        )
        user_id = rcreate.json()["id"]

        # Soft delete
        rdel = await client.delete(
            f"/api/tenant/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert rdel.status_code == 204

        # User ainda listado mas status='suspended'
        rlist = await client.get("/api/tenant/users", headers={"Authorization": f"Bearer {token}"})
        users = rlist.json()
        deleted = [u for u in users if u["id"] == user_id]
        assert len(deleted) == 1
        assert deleted[0]["status"] == "suspended"


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_user_duplicate_email_per_tenant(clean_db: None) -> None:
    """POST com email duplicado dentro do tenant → 409."""
    from httpx import ASGITransport, AsyncClient

    from bloco_interface.web.app import app

    tenant_id, token = await _signup_full("11222333000181", "dup@a.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Tenta criar user com email do advogado responsável (dup@a.com já existe)
        r = await client.post(
            "/api/tenant/users",
            json={"email": "dup@a.com", "senha": "senha12345", "nome": "Duplicate"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 409
    assert "email" in r.json()["detail"].lower() or "cadastrado" in r.json()["detail"].lower()
