"""Unit tests state machine BYOK lifecycle (SP04-BYOK-01 chunk 6 / AC-05+06+07).

Mocks AsyncSession + TenantAPIKey rows para validate state transitions sem
PostgreSQL real. Integration tests com DB ficam em chunk 7.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from bloco_auth.byok_lifecycle import (
    BYOKNotFoundError,
    RotationConflictError,
    get_status,
    revoke,
    start_rotation,
)
from bloco_auth.byok_encryption import _load_master_key


@pytest.fixture(autouse=True)
def _master_key_env(monkeypatch):
    _load_master_key.cache_clear()
    monkeypatch.setenv("MASTER_ENCRYPTION_KEY", "0123456789abcdef" * 4)
    yield
    _load_master_key.cache_clear()


def _make_session_with_key_row(key_row):
    """Helper: AsyncSession mock cujo execute(...) retorna scalar_one_or_none() == key_row.

    Para encrypt_api_key chamado dentro start_rotation, o segundo execute() retorna
    bytes encrypted via scalar_one(). Precisamos sequência execute results.
    """
    db_session = MagicMock()

    # Sequence: 1st execute() → SELECT key_row, 2nd execute() → encrypt_api_key, 3rd → UPDATE
    select_result = MagicMock()
    select_result.scalar_one_or_none = MagicMock(return_value=key_row)

    encrypt_result = MagicMock()
    encrypt_result.scalar_one = MagicMock(return_value=b"new-encrypted-blob")

    update_result = MagicMock()  # UPDATE não usa scalar

    # AsyncMock side_effect cycles through results
    db_session.execute = AsyncMock(side_effect=[select_result, encrypt_result, update_result, update_result])
    return db_session


def _make_session_select_only(key_row):
    """Helper para get_status / revoke (sem encrypt_api_key call)."""
    db_session = MagicMock()
    select_result = MagicMock()
    select_result.scalar_one_or_none = MagicMock(return_value=key_row)
    update_result = MagicMock()
    db_session.execute = AsyncMock(side_effect=[select_result, update_result, update_result])
    return db_session


# ──────────────────────────────────────────────────────────────────────────────
# start_rotation — state transitions
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_rotation_active_to_pending():
    """start_rotation em status='active' → transition pending_rotation."""
    tenant_id = uuid4()
    key_row = MagicMock(
        tenant_id=tenant_id,
        status="active",
        key_fingerprint="sk-ant-...OLD",
        rotation_started_at=None,
    )
    db_session = _make_session_with_key_row(key_row)

    result = await start_rotation(tenant_id, "sk-ant-fresh-rotation-key-NEW", db_session)

    assert result["status"] == "pending_rotation"
    assert "started_at" in result
    assert "complete_at" in result
    assert result["old_fingerprint"] == "sk-ant-...OLD"
    assert result["new_fingerprint"] == "sk-ant-...NEW"


@pytest.mark.asyncio
async def test_start_rotation_concurrent_raises_conflict():
    """start_rotation em status='pending_rotation' → RotationConflictError."""
    tenant_id = uuid4()
    key_row = MagicMock(
        tenant_id=tenant_id,
        status="pending_rotation",
        rotation_started_at=datetime.now(timezone.utc),
    )
    db_session = _make_session_select_only(key_row)

    with pytest.raises(RotationConflictError, match="Rotation já em andamento"):
        await start_rotation(tenant_id, "sk-ant-new", db_session)


@pytest.mark.asyncio
async def test_start_rotation_revoked_raises_lifecycle_error():
    """start_rotation em status='revoked' → BYOKLifecycleError (re-onboarding necessário)."""
    from bloco_auth.byok_lifecycle import BYOKLifecycleError
    tenant_id = uuid4()
    key_row = MagicMock(tenant_id=tenant_id, status="revoked")
    db_session = _make_session_select_only(key_row)

    with pytest.raises(BYOKLifecycleError, match="revoked"):
        await start_rotation(tenant_id, "sk-ant-new", db_session)


@pytest.mark.asyncio
async def test_start_rotation_no_byok_raises_not_found():
    """start_rotation em tenant sem BYOK → BYOKNotFoundError."""
    tenant_id = uuid4()
    db_session = _make_session_select_only(None)

    with pytest.raises(BYOKNotFoundError, match="não tem BYOK"):
        await start_rotation(tenant_id, "sk-ant-new", db_session)


# ──────────────────────────────────────────────────────────────────────────────
# revoke — purge
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_revoke_active_to_revoked():
    """revoke em status='active' → status='revoked' + tenant suspended."""
    tenant_id = uuid4()
    user_id = uuid4()
    key_row = MagicMock(
        tenant_id=tenant_id,
        status="active",
        key_fingerprint="sk-ant-...OLD",
    )
    db_session = _make_session_select_only(key_row)

    result = await revoke(tenant_id, user_id, "suspected_compromise", db_session)

    assert result["status"] == "revoked"
    assert result["reason"] == "suspected_compromise"
    assert "revoked_at" in result
    assert result["old_fingerprint"] == "sk-ant-...OLD"
    # Verifica que execute foi chamado 3x (SELECT + UPDATE tenant_api_keys + UPDATE tenants)
    assert db_session.execute.await_count == 3


@pytest.mark.asyncio
async def test_revoke_no_byok_raises_not_found():
    """revoke em tenant sem BYOK → BYOKNotFoundError."""
    tenant_id = uuid4()
    user_id = uuid4()
    db_session = _make_session_select_only(None)

    with pytest.raises(BYOKNotFoundError, match="não tem BYOK"):
        await revoke(tenant_id, user_id, "off_boarding", db_session)


# ──────────────────────────────────────────────────────────────────────────────
# get_status — read-only
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_status_active_returns_fingerprint():
    """get_status em status='active' retorna fingerprint truncated + null rotation."""
    tenant_id = uuid4()
    created_at = datetime.now(timezone.utc)
    key_row = MagicMock(
        tenant_id=tenant_id,
        status="active",
        key_fingerprint="sk-ant-...XYZ",
        created_at=created_at,
        last_used_at=None,
        rotation_started_at=None,
    )
    db_session = _make_session_select_only(key_row)

    result = await get_status(tenant_id, db_session)

    assert result["status"] == "active"
    assert result["key_fingerprint"] == "sk-ant-...XYZ"
    assert result["rotation"] is None
    assert result["last_used_at"] is None


@pytest.mark.asyncio
async def test_get_status_pending_rotation_includes_rotation_info():
    """get_status em status='pending_rotation' retorna rotation info."""
    tenant_id = uuid4()
    started_at = datetime.now(timezone.utc) - timedelta(hours=2)
    key_row = MagicMock(
        tenant_id=tenant_id,
        status="pending_rotation",
        key_fingerprint="sk-ant-...OLD",
        pending_fingerprint="sk-ant-...NEW",
        created_at=started_at,
        last_used_at=None,
        rotation_started_at=started_at,
    )
    db_session = _make_session_select_only(key_row)

    result = await get_status(tenant_id, db_session)

    assert result["status"] == "pending_rotation"
    assert result["rotation"] is not None
    assert result["rotation"]["pending_fingerprint"] == "sk-ant-...NEW"
    assert "started_at" in result["rotation"]
    assert "complete_at" in result["rotation"]
