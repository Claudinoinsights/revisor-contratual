"""Unit tests audit isolation aggregation helpers (SP04-LGPD-01 AC-05/AC-06).

Cobre helpers de ``bloco_auth/audit_isolation.py`` sem requerer DB:
- ``IsolationCounts`` Pydantic schema validation + aggregation result shape
- ``LastLoginEntry`` Pydantic schema (com/sem last_login_at null)
- ``IsolationResponse`` schema completo
- ``_resolve_current_versions`` retorna semver canônico Sprint 04 MVP
- Aggregation queries: graceful fallback via mock AsyncSession

Tests integration de GET /api/tenant/audit/isolation com auth + RLS scoped
ficam em ``tests/integration/test_audit_isolation_endpoint.py`` (chunk 6
_REQUIRES_POSTGRES).
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from bloco_auth import audit_isolation


# ──────────────────────────────────────────────────────────────────────────────
# Helpers — mock AsyncSession factory
# ──────────────────────────────────────────────────────────────────────────────


def _mock_session_with_count_results(counts_per_query: dict[str, int]):
    """Cria mock AsyncSession que retorna count específico por query SQL."""
    session = MagicMock()

    async def execute_side_effect(stmt, *args, **kwargs):
        sql = str(stmt)
        # Match by table name in SQL string
        for table, value in counts_per_query.items():
            if table in sql:
                result = MagicMock()
                result.scalar_one = MagicMock(return_value=value)
                return result
        # Default fallback
        result = MagicMock()
        result.scalar_one = MagicMock(return_value=0)
        return result

    session.execute = AsyncMock(side_effect=execute_side_effect)
    session.rollback = AsyncMock(return_value=None)
    return session


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_isolation_counts_valid_construction() -> None:
    """IsolationCounts aceita 5 inteiros."""
    c = audit_isolation.IsolationCounts(
        users=5, analyses=142,
        dpa_acceptances=1, tos_acceptances=1, audit_events_count=234,
    )
    assert c.users == 5
    assert c.audit_events_count == 234


@pytest.mark.unit
def test_isolation_counts_extra_field_forbidden() -> None:
    """extra='forbid' rejeita campos não declarados."""
    with pytest.raises(ValidationError, match="extra"):
        audit_isolation.IsolationCounts(
            users=5, analyses=10,
            dpa_acceptances=1, tos_acceptances=1, audit_events_count=10,
            unknown_field="rejected",  # type: ignore[call-arg]
        )


@pytest.mark.unit
def test_last_login_entry_with_null_login() -> None:
    """LastLoginEntry permite last_login_at=None (user nunca logou)."""
    e = audit_isolation.LastLoginEntry(
        user_id=uuid4(),
        email="advogado@escritorio.com",
        last_login_at=None,
    )
    assert e.last_login_at is None
    assert e.email == "advogado@escritorio.com"


@pytest.mark.unit
def test_last_login_entry_with_timestamp() -> None:
    """LastLoginEntry com timestamp UTC valido."""
    now = datetime.now(timezone.utc)
    e = audit_isolation.LastLoginEntry(
        user_id=uuid4(),
        email="advogado@escritorio.com",
        last_login_at=now,
    )
    assert e.last_login_at == now


@pytest.mark.unit
def test_isolation_response_complete_construction() -> None:
    """IsolationResponse aceita estrutura completa esperada por endpoint."""
    tid = uuid4()
    response = audit_isolation.IsolationResponse(
        tenant_id=tid,
        counts=audit_isolation.IsolationCounts(
            users=3, analyses=50,
            dpa_acceptances=1, tos_acceptances=1, audit_events_count=78,
        ),
        rls_policies_active=[
            "user_tenant_isolation (users)",
            "tenant_isolation (dpa_acceptances)",
            "tos_tenant_isolation (tos_acceptances)",
        ],
        last_login_per_user=[],
        rls_session_var_set=True,
        current_dpa_version="1.0.0",
        current_tos_version="1.0.0",
    )
    assert response.tenant_id == tid
    assert len(response.rls_policies_active) == 3
    assert response.rls_session_var_set is True


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_resolve_current_versions_returns_canonical_v1() -> None:
    """Sprint 04 MVP retorna ('1.0.0', '1.0.0') hardcoded."""
    dpa_v, tos_v = audit_isolation._resolve_current_versions()
    assert dpa_v == "1.0.0"
    assert tos_v == "1.0.0"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_aggregate_counts_with_legacy_analyses_fallback() -> None:
    """_aggregate_counts gracefully fallback quando tabela analyses não existe."""
    session = MagicMock()

    # Counts default (multi-tenant scoped tables — sempre existem post-migration)
    counts_map = {
        "users": 5,
        "dpa_acceptances": 1,
        "tos_acceptances": 1,
    }
    call_count = {"n": 0}

    async def execute_side_effect(stmt, *args, **kwargs):
        sql = str(stmt)
        call_count["n"] += 1
        # analyses query → SQLAlchemyError (tabela ausente em test env)
        if "analyses" in sql and "audit_events" not in sql:
            raise SQLAlchemyError("table 'analyses' does not exist")
        # audit_events query → também SQLAlchemyError (tabela legacy)
        if "audit_events" in sql:
            raise SQLAlchemyError("table 'audit_events' does not exist")
        # Demais tabelas retornam count fixo
        for table, value in counts_map.items():
            if table in sql:
                result = MagicMock()
                result.scalar_one = MagicMock(return_value=value)
                return result
        result = MagicMock()
        result.scalar_one = MagicMock(return_value=0)
        return result

    session.execute = AsyncMock(side_effect=execute_side_effect)
    session.rollback = AsyncMock(return_value=None)

    counts = await audit_isolation._aggregate_counts(session, uuid4())
    assert counts.users == 5
    assert counts.dpa_acceptances == 1
    assert counts.tos_acceptances == 1
    # Graceful fallbacks → 0 sem crash
    assert counts.analyses == 0
    assert counts.audit_events_count == 0
    # Rollback chamado 2x (analyses + audit_events errors)
    assert session.rollback.await_count >= 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_aggregate_counts_full_population() -> None:
    """_aggregate_counts cenário happy: todas tabelas existem e retornam contagens."""
    session = MagicMock()
    counts_map = {
        "users": 10,
        "dpa_acceptances": 1,
        "tos_acceptances": 1,
        "analyses": 200,
        "audit_events": 500,
    }

    async def execute_side_effect(stmt, *args, **kwargs):
        sql = str(stmt)
        # audit_events tem WHERE tenant_id = :tid; analyses não
        for table, value in counts_map.items():
            if table in sql:
                result = MagicMock()
                result.scalar_one = MagicMock(return_value=value)
                return result
        result = MagicMock()
        result.scalar_one = MagicMock(return_value=0)
        return result

    session.execute = AsyncMock(side_effect=execute_side_effect)
    session.rollback = AsyncMock(return_value=None)

    counts = await audit_isolation._aggregate_counts(session, uuid4())
    assert counts.users == 10
    assert counts.analyses == 200
    assert counts.audit_events_count == 500
    # Sem rollback no cenário happy
    assert session.rollback.await_count == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_rls_policies_query_pg_policies() -> None:
    """_list_rls_policies retorna labels formatados '<policy> (<table>)'."""
    session = MagicMock()
    rows = [
        ("user_tenant_isolation (users)",),
        ("tenant_isolation (dpa_acceptances)",),
        ("tos_tenant_isolation (tos_acceptances)",),
    ]
    result = MagicMock()
    result.all = MagicMock(return_value=rows)
    session.execute = AsyncMock(return_value=result)

    policies = await audit_isolation._list_rls_policies(session)
    assert len(policies) == 3
    assert "user_tenant_isolation (users)" in policies
    assert "tos_tenant_isolation (tos_acceptances)" in policies


@pytest.mark.unit
@pytest.mark.asyncio
async def test_last_login_per_user_with_column_present() -> None:
    """_last_login_per_user happy path com coluna last_login_at."""
    session = MagicMock()
    now = datetime.now(timezone.utc)
    rows = [
        (uuid4(), "user_a@firm.com", now),
        (uuid4(), "user_b@firm.com", None),
    ]
    result = MagicMock()
    result.all = MagicMock(return_value=rows)
    session.execute = AsyncMock(return_value=result)
    session.rollback = AsyncMock(return_value=None)

    logins = await audit_isolation._last_login_per_user(session)
    assert len(logins) == 2
    assert logins[0].last_login_at == now
    assert logins[1].last_login_at is None
    # Sem rollback no cenário happy
    assert session.rollback.await_count == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_last_login_per_user_legacy_column_fallback() -> None:
    """_last_login_per_user fallback quando coluna last_login_at não existe."""
    session = MagicMock()
    rows_fallback = [
        (uuid4(), "user_a@firm.com"),
        (uuid4(), "user_b@firm.com"),
    ]
    result_fallback = MagicMock()
    result_fallback.all = MagicMock(return_value=rows_fallback)

    call_count = {"n": 0}

    async def execute_side_effect(stmt, *args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # Primeira query (com last_login_at) falha
            raise SQLAlchemyError("column 'last_login_at' does not exist")
        # Segunda query (fallback sem last_login_at) sucesso
        return result_fallback

    session.execute = AsyncMock(side_effect=execute_side_effect)
    session.rollback = AsyncMock(return_value=None)

    logins = await audit_isolation._last_login_per_user(session)
    assert len(logins) == 2
    assert all(e.last_login_at is None for e in logins)
    # Rollback chamado 1x antes do retry sem coluna
    assert session.rollback.await_count == 1
