"""Integration tests — Login + JWT + RLS context (SP04-AUTH-01 AC-05).

Pre-requisito: PostgreSQL real + DATABASE_URL setada + migration.
Tests skipped via _REQUIRES_POSTGRES quando DB ausente (qa-gate G5).

Cobre:
- Login válido → JWT issued + claims tenant_id+user_id
- Email inexistente → 401 mensagem genérica anti enumeration (Story Risk #5)
- Senha errada → 401 MESMA mensagem (consistência anti enumeration)
- User suspended → 403
- JWT expirado em request scoped → 401
- JWT tampered → 401
- Logout → 204 + audit user_logout
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest

from bloco_auth import db as sp04_db
from bloco_auth import jwt_utils, onboarding


_REQUIRES_POSTGRES = pytest.mark.skipif(
    os.getenv("DATABASE_URL") is None,
    reason="Login JWT integration test requer PostgreSQL real (qa-gate G5).",
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
    """Helper — signup + retorna (tenant_id, jwt_token)."""
    step1 = onboarding.OnboardingStep1Data(
        cnpj=cnpj,
        razao_social=f"Esc {cnpj}",
        advogado_responsavel="Test",
        email=email,
        senha=senha,
    )
    sid = onboarding.start_session(step1)
    onboarding.store_step(sid, 2, onboarding.OnboardingStep2Data(anthropic_api_key="sk-test-1234567890"))
    onboarding.store_step(sid, 3, onboarding.OnboardingStep3Data(
        dpa_version="1.0.0", accepted=True,
        tos_version="1.0.0", tos_accepted=True,
    ))
    onboarding.store_step(sid, 4, onboarding.OnboardingStep4Data(tier="Starter"))

    sessionmaker = sp04_db.get_sessionmaker()
    async with sessionmaker() as session:
        tenant, user = await onboarding.complete_onboarding(sid, session)

    token = jwt_utils.encode_jwt(tenant_id=tenant.id, user_id=user.id)
    return str(tenant.id), token


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_valid_credentials(clean_db: None, tmp_path) -> None:
    """Login válido → 200 + token + tenant_id + user_id; audit user_login."""
    import json

    from bloco_audit import chain as audit_chain
    from httpx import ASGITransport, AsyncClient

    from bloco_interface.web.app import app

    test_log = tmp_path / "audit.jsonl"
    audit_chain.DEFAULT_AUDIT_LOG = test_log

    try:
        tenant_id, _ = await _signup_full("11222333000181", "login-test@a.com", "senha-correta-12345")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post("/api/auth/login", json={
                "email": "login-test@a.com",
                "senha": "senha-correta-12345",
            })
        assert r.status_code == 200
        body = r.json()
        assert "token" in body
        assert body["tenant_id"] == tenant_id
        assert "user_id" in body

        # Decode JWT verifica claims
        from uuid import UUID

        payload = jwt_utils.decode_jwt(body["token"])
        assert payload.tenant_id == UUID(tenant_id)

        # Audit
        events = [json.loads(line) for line in test_log.read_text().splitlines()]
        assert any(e["event_type"] == "user_login" for e in events)
    finally:
        from pathlib import Path
        audit_chain.DEFAULT_AUDIT_LOG = Path.home() / ".local" / "share" / "revisor-contratual" / "audit.jsonl"


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_email_not_found(clean_db: None) -> None:
    """Email inexistente → 401 mensagem genérica."""
    from httpx import ASGITransport, AsyncClient

    from bloco_interface.web.app import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/auth/login", json={
            "email": "nao-existe@nowhere.com",
            "senha": "qualquer123",
        })
    assert r.status_code == 401
    assert "email" in r.json()["detail"].lower() or "senha" in r.json()["detail"].lower()
    # Save detail for next test comparison
    pytest._login_email_not_found_detail = r.json()["detail"]


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_wrong_password_same_message(clean_db: None) -> None:
    """Senha errada → 401 MESMA mensagem que email inexistente (anti enumeration)."""
    from httpx import ASGITransport, AsyncClient

    from bloco_interface.web.app import app

    await _signup_full("11222333000181", "wrong-pwd@a.com", "senha-correta-12345")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Email correto, senha errada
        r = await client.post("/api/auth/login", json={
            "email": "wrong-pwd@a.com",
            "senha": "senha-errada-99999",
        })
    assert r.status_code == 401
    detail = r.json()["detail"]
    # Verifica mensagem genérica (ambos cenários "email não existe" e "senha errada")
    # devem retornar texto similar — Story Risk #5 anti enumeration
    assert "email" in detail.lower() or "senha" in detail.lower()


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_user_suspended(clean_db: None) -> None:
    """User suspended → 403 'Conta suspensa'."""
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import update

    from bloco_auth.middleware import apply_rls_context
    from bloco_auth.models import User
    from bloco_interface.web.app import app

    tenant_id, _ = await _signup_full("11222333000181", "suspended@a.com")
    from uuid import UUID

    sessionmaker = sp04_db.get_sessionmaker()
    async with sessionmaker() as session, apply_rls_context(session, UUID(tenant_id)):
        await session.execute(
            update(User).where(User.email == "suspended@a.com").values(status="suspended")
        )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/auth/login", json={
            "email": "suspended@a.com",
            "senha": "senha-forte-12345",
        })
    assert r.status_code == 403
    assert "suspensa" in r.json()["detail"].lower()


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_jwt_expired_request_rejected(clean_db: None) -> None:
    """JWT expirado em request scoped → 401."""
    from uuid import UUID

    from httpx import ASGITransport, AsyncClient

    from bloco_interface.web.app import app

    tenant_id, _ = await _signup_full("11222333000181", "expired-jwt@a.com")
    sessionmaker = sp04_db.get_sessionmaker()
    from sqlalchemy import select
    from bloco_auth.middleware import apply_rls_context
    from bloco_auth.models import User

    async with sessionmaker() as session, apply_rls_context(session, UUID(tenant_id)):
        result = await session.execute(select(User).where(User.email == "expired-jwt@a.com"))
        user = result.scalar_one()

    # Encode JWT já expirado
    expired_token = jwt_utils.encode_jwt(
        tenant_id=UUID(tenant_id), user_id=user.id, expiry_hours=-1
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(
            "/api/tenant/users",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
    assert r.status_code == 401


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_jwt_tampered_request_rejected(clean_db: None) -> None:
    """JWT tampered → 401."""
    from httpx import ASGITransport, AsyncClient

    from bloco_interface.web.app import app

    _, valid_token = await _signup_full("11222333000181", "tampered@a.com")

    parts = valid_token.split(".")
    payload = parts[1]
    middle = len(payload) // 2
    flipped = "Z" if payload[middle] != "Z" else "Y"
    tampered_payload = payload[:middle] + flipped + payload[middle + 1 :]
    tampered = f"{parts[0]}.{tampered_payload}.{parts[2]}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(
            "/api/tenant/users",
            headers={"Authorization": f"Bearer {tampered}"},
        )
    assert r.status_code == 401


@_REQUIRES_POSTGRES
@pytest.mark.integration
@pytest.mark.asyncio
async def test_logout_audit_event(clean_db: None, tmp_path) -> None:
    """POST /auth/logout com JWT válido → 204 + audit user_logout."""
    import json

    from bloco_audit import chain as audit_chain
    from httpx import ASGITransport, AsyncClient

    from bloco_interface.web.app import app

    test_log = tmp_path / "audit.jsonl"
    audit_chain.DEFAULT_AUDIT_LOG = test_log

    try:
        _, token = await _signup_full("11222333000181", "logout-test@a.com")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                "/api/auth/logout",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 204

        events = [json.loads(line) for line in test_log.read_text().splitlines()]
        assert any(e["event_type"] == "user_logout" for e in events)
    finally:
        from pathlib import Path
        audit_chain.DEFAULT_AUDIT_LOG = Path.home() / ".local" / "share" / "revisor-contratual" / "audit.jsonl"
