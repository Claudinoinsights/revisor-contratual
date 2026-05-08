"""Unit tests JWT middleware FastAPI Depends (sem DB).

Cobre `bloco_auth/middleware.py` get_current_user — async function que
extrai/valida Bearer JWT e retorna (tenant_id, user_id) tuple. Tests chamam
diretamente como async function (sem TestClient HTTP), focando lógica de
parsing + HTTPException paths.

Story SP04-AUTH-01 AC-08 unit coverage middleware.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException

from bloco_auth import jwt_utils
from bloco_auth.jwt_utils import _load_secret, encode_jwt
from bloco_auth.middleware import get_current_user


_TEST_SECRET = "0123456789abcdef" * 4  # 64 bytes >= 32 mín


@pytest.fixture(autouse=True)
def _jwt_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setup JWT env vars + reset cache entre tests (consistente test_jwt.py)."""
    monkeypatch.setenv("JWT_SECRET_KEY", _TEST_SECRET)
    monkeypatch.setenv("JWT_EXPIRY_HOURS", "24")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    _load_secret.cache_clear()
    yield
    _load_secret.cache_clear()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_no_auth_header() -> None:
    """authorization=None → HTTPException 401 + WWW-Authenticate Bearer."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization=None)
    assert exc_info.value.status_code == 401
    assert "ausente" in exc_info.value.detail.lower()
    assert exc_info.value.headers.get("WWW-Authenticate", "").lower().startswith("bearer")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_no_bearer_prefix() -> None:
    """Header sem prefix 'Bearer ' → 401."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="Token abc123")
    assert exc_info.value.status_code == 401
    assert "Bearer" in exc_info.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_empty_bearer() -> None:
    """Header 'Bearer ' (apenas prefix + espaço) → 401 'token vazio'."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="Bearer ")
    assert exc_info.value.status_code == 401
    assert "vazio" in exc_info.value.detail.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_invalid_jwt() -> None:
    """Bearer token não-JWT → 401 (JWTError caught)."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="Bearer not-a-jwt-string")
    assert exc_info.value.status_code == 401


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_valid_jwt_returns_tuple() -> None:
    """Bearer JWT válido → tuple (tenant_id, user_id) UUIDs originais."""
    tenant_id = uuid4()
    user_id = uuid4()
    token = encode_jwt(tenant_id=tenant_id, user_id=user_id)

    result = await get_current_user(authorization=f"Bearer {token}")
    assert result == (tenant_id, user_id)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_expired_jwt() -> None:
    """JWT expirado (expiry_hours=-1) → HTTPException 401 'expirado'."""
    expired = encode_jwt(tenant_id=uuid4(), user_id=uuid4(), expiry_hours=-1)
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization=f"Bearer {expired}")
    assert exc_info.value.status_code == 401
    assert "expirado" in exc_info.value.detail.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_tampered_jwt() -> None:
    """JWT com payload tampered → 401 (signature inválida)."""
    valid = encode_jwt(tenant_id=uuid4(), user_id=uuid4())
    parts = valid.split(".")
    payload = parts[1]
    middle = len(payload) // 2
    flipped = "Z" if payload[middle] != "Z" else "Y"
    tampered_payload = payload[:middle] + flipped + payload[middle + 1 :]
    tampered = f"{parts[0]}.{tampered_payload}.{parts[2]}"

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization=f"Bearer {tampered}")
    assert exc_info.value.status_code == 401


@pytest.mark.unit
@pytest.mark.asyncio
async def test_apply_rls_context_re_export() -> None:
    """apply_rls_context é re-export semântico de with_tenant_context."""
    from bloco_auth.db import with_tenant_context
    from bloco_auth.middleware import apply_rls_context

    assert apply_rls_context is with_tenant_context, (
        "apply_rls_context deve ser re-export idêntico de db.with_tenant_context"
    )
