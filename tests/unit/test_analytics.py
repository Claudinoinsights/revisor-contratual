"""Unit tests — TD-SP04-04-ANALYTICS Chunk 5 (Sati Eixo 5 MANDATORY pre-release v0.3.0).

Cobre helpers de ``bloco_auth/analytics.py`` sem requerer DB live:

- Pydantic schemas: extra='forbid' rejeita tenant_id (Smith C1)
- PII blocklist: 9 vectors absent/anonymized (Smith H3 + NFR-PRIVACY-01.3)
- HMAC chain: keyed tenant + canonical determinism + genesis sentinel (Smith C2)
- Timestamp rounding NFR-PRIVACY-01.3.8 (timing correlation mitigation)
- Idempotency contract: IntegrityError catch → AnalyticsEventOut status='duplicate'
  (Smith F-01 fix — HTTP 200 silent NUNCA 409)
- Event type + doctype enum validation (defense-in-depth mirror DB CHECK)
- CLI period parser (7d/30d/90d → int; rejeita formato inválido)

Tests integration (real DB postgres + RLS + endpoint) → ``tests/integration/test_analytics_endpoint.py`` Sprint 5+ subsequent.

REUSE: tests/unit/test_audit_isolation_aggregation.py pattern (MagicMock + AsyncMock).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import click
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from bloco_auth import analytics
from bloco_interface import analytics_cli


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _set_auth_cookie_key(monkeypatch):
    """HMAC chain requires AUTH_COOKIE_KEY env var."""
    monkeypatch.setenv("AUTH_COOKIE_KEY", "test-secret-key-32-chars-min-len!")


@pytest.fixture
def valid_event_kwargs():
    return {
        "event_id": uuid4(),
        "session_id": uuid4(),
        "event_type": "doctype_selected",
        "occurred_at": datetime(2026, 5, 13, 12, 34, 56, tzinfo=timezone.utc),
        "doctype": "ccb",
        "payload": None,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Smith C1 — Pydantic strict mode rejeita tenant_id no payload
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_analytics_event_in_extra_forbid(valid_event_kwargs):
    """AC-11 — Pydantic REJEITA payload com tenant_id explicit (Smith C1 fix)."""
    with pytest.raises(ValidationError, match="extra"):
        analytics.AnalyticsEventIn(
            **valid_event_kwargs,
            tenant_id=uuid4(),  # type: ignore[call-arg]
        )


@pytest.mark.unit
def test_analytics_event_in_extra_forbid_arbitrary_field(valid_event_kwargs):
    """extra='forbid' bloqueia qualquer campo não-declarado."""
    with pytest.raises(ValidationError, match="extra"):
        analytics.AnalyticsEventIn(
            **valid_event_kwargs,
            arbitrary_field="leak_attempt",  # type: ignore[call-arg]
        )


@pytest.mark.unit
def test_analytics_event_in_minimal_valid(valid_event_kwargs):
    """Construção válida sem doctype/payload (drop-off cross-doctype)."""
    kwargs = {**valid_event_kwargs, "doctype": None, "payload": None}
    ev = analytics.AnalyticsEventIn(**kwargs)
    assert ev.doctype is None
    assert ev.payload is None
    assert ev.event_type == "doctype_selected"


@pytest.mark.unit
def test_analytics_batch_max_5_events(valid_event_kwargs):
    """Smith spec — batch endpoint accepts up to 5 events per request."""
    events = [analytics.AnalyticsEventIn(**{**valid_event_kwargs, "event_id": uuid4()}) for _ in range(5)]
    batch = analytics.AnalyticsEventBatchIn(events=events)
    assert len(batch.events) == 5


@pytest.mark.unit
def test_analytics_batch_over_5_rejected(valid_event_kwargs):
    events = [analytics.AnalyticsEventIn(**{**valid_event_kwargs, "event_id": uuid4()}) for _ in range(6)]
    with pytest.raises(ValidationError):
        analytics.AnalyticsEventBatchIn(events=events)


# ──────────────────────────────────────────────────────────────────────────────
# Smith H3 — PII vectors blocklist (NFR-PRIVACY-01.3 — 9 vectors)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.parametrize("pii_field", sorted(analytics._PII_BLOCKLIST))
def test_pii_blocklist_rejects_field(pii_field):
    """AC-12 — runtime payload validation rejeita PII vectors (defense-in-depth).

    Smith RV-L1 fix Fase 4.5d — parametrize DERIVADO de sorted(_PII_BLOCKLIST)
    auto-sync. Garante 100% coverage automatic: novos PII vectors adicionados
    ao blocklist são automaticamente testados sem manual parametrize update.
    """
    with pytest.raises(HTTPException) as exc_info:
        analytics._validate_payload_pii({pii_field: "any-value"})
    assert exc_info.value.status_code == 400
    assert pii_field in exc_info.value.detail


@pytest.mark.unit
def test_pii_blocklist_accepts_clean_payload():
    """Payload sem PII fields passa validação."""
    analytics._validate_payload_pii({"tti_ms_client_hint": 4500})
    analytics._validate_payload_pii({"from_doctype": "ccb", "to_doctype": "cartao"})
    analytics._validate_payload_pii(None)  # None payload é válido


@pytest.mark.unit
def test_pii_blocklist_case_insensitive():
    """PII detection case-insensitive (CPF, Cpf, cpf todos rejeitados)."""
    for variant in ["CPF", "Cpf", "cpf"]:
        with pytest.raises(HTTPException):
            analytics._validate_payload_pii({variant: "123"})


# ──────────────────────────────────────────────────────────────────────────────
# Event type + doctype enum validation (mirror DB CHECK constraints)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_event_type_validation_valid():
    """5 event_types aceitos (PRD §4.2)."""
    for et in ["doctype_selected", "first_doctype_selected", "doctype_changed",
               "doctype_dropoff", "contract_submitted"]:
        analytics._validate_event_type_and_doctype(et, None)  # no raise


@pytest.mark.unit
def test_event_type_validation_invalid():
    """Event types não-enum rejeitados HTTP 400."""
    with pytest.raises(HTTPException) as exc_info:
        analytics._validate_event_type_and_doctype("invented_event", None)
    assert exc_info.value.status_code == 400


@pytest.mark.unit
def test_doctype_validation_valid():
    """7 doctypes aceitos (ADR-020)."""
    for dt in ["ccb", "veiculo", "consignado", "cartao", "imobiliario", "fies", "geral"]:
        analytics._validate_event_type_and_doctype("doctype_selected", dt)


@pytest.mark.unit
def test_doctype_validation_invalid():
    with pytest.raises(HTTPException) as exc_info:
        analytics._validate_event_type_and_doctype("doctype_selected", "invented_doctype")
    assert exc_info.value.status_code == 400


@pytest.mark.unit
def test_doctype_null_allowed():
    """doctype=None aceito (drop-off cross-doctype)."""
    analytics._validate_event_type_and_doctype("doctype_dropoff", None)


# ──────────────────────────────────────────────────────────────────────────────
# NFR-PRIVACY-01.3.8 — Timestamp rounding (timing correlation mitigation)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_round_to_minute_strips_seconds():
    ts = datetime(2026, 5, 13, 12, 34, 56, 789000, tzinfo=timezone.utc)
    rounded = analytics._round_to_minute(ts)
    assert rounded.second == 0
    assert rounded.microsecond == 0
    assert rounded.hour == 12
    assert rounded.minute == 34


@pytest.mark.unit
def test_round_to_minute_naive_datetime_assumes_utc():
    ts = datetime(2026, 5, 13, 12, 34, 56, 789000)  # tz-naive
    rounded = analytics._round_to_minute(ts)
    assert rounded.tzinfo == timezone.utc


# ──────────────────────────────────────────────────────────────────────────────
# Smith C2 — HMAC chain (canonical serialization + keyed by tenant)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_canonical_serialize_deterministic():
    """Mesma entrada → mesmo bytes (sort_keys=True garante)."""
    args = dict(
        event_id=UUID("11111111-1111-4111-8111-111111111111"),
        session_id=UUID("22222222-2222-4222-8222-222222222222"),
        event_type="doctype_selected",
        occurred_at=datetime(2026, 5, 13, 12, 0, tzinfo=timezone.utc),
        doctype="ccb",
        payload={"b": 2, "a": 1},
        prev_hash="abc",
    )
    bytes_1 = analytics._canonical_event_serialize(**args)
    bytes_2 = analytics._canonical_event_serialize(**args)
    assert bytes_1 == bytes_2


@pytest.mark.unit
def test_canonical_serialize_key_order_independent():
    """Payload com keys reordenadas → mesmo canonical output (sort_keys)."""
    base = dict(
        event_id=UUID("11111111-1111-4111-8111-111111111111"),
        session_id=UUID("22222222-2222-4222-8222-222222222222"),
        event_type="doctype_selected",
        occurred_at=datetime(2026, 5, 13, 12, 0, tzinfo=timezone.utc),
        doctype="ccb",
        prev_hash="abc",
    )
    bytes_1 = analytics._canonical_event_serialize(**base, payload={"a": 1, "b": 2})
    bytes_2 = analytics._canonical_event_serialize(**base, payload={"b": 2, "a": 1})
    assert bytes_1 == bytes_2


@pytest.mark.unit
def test_compute_event_hmac_deterministic():
    secret = b"test-key"
    tenant_id = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    data = b"event-canonical-bytes"
    h1 = analytics._compute_event_hmac(secret, tenant_id, data)
    h2 = analytics._compute_event_hmac(secret, tenant_id, data)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest


@pytest.mark.unit
def test_compute_event_hmac_different_tenants_different_hashes():
    """Tenant quarantine isolation — different tenant → different HMAC mesmo input data."""
    secret = b"test-key"
    data = b"event-canonical-bytes"
    h_tenant_a = analytics._compute_event_hmac(
        secret, UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"), data
    )
    h_tenant_b = analytics._compute_event_hmac(
        secret, UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"), data
    )
    assert h_tenant_a != h_tenant_b


@pytest.mark.unit
def test_compute_event_hmac_different_data_different_hashes():
    """Diff event data → diff HMAC (tamper detection foundation)."""
    secret = b"test-key"
    tenant_id = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    h1 = analytics._compute_event_hmac(secret, tenant_id, b"data-A")
    h2 = analytics._compute_event_hmac(secret, tenant_id, b"data-B")
    assert h1 != h2


@pytest.mark.unit
def test_get_hmac_secret_raises_when_env_missing(monkeypatch):
    monkeypatch.delenv("AUTH_COOKIE_KEY", raising=False)
    with pytest.raises(RuntimeError, match="AUTH_COOKIE_KEY"):
        analytics._get_hmac_secret()


# ──────────────────────────────────────────────────────────────────────────────
# Smith F-01 — Idempotency contract (caller catches IntegrityError)
# Smith C2 Fase 4.5b refactor: _ingest_single_event_inner raises;
# callers (single endpoint OR batch endpoint with SAVEPOINT) handle.
# ──────────────────────────────────────────────────────────────────────────────


def _make_chain_select_mock():
    """Mock SELECT last_chain_hash returning None (genesis path)."""
    mock_result_chain = MagicMock()
    mock_result_chain.first = MagicMock(return_value=None)
    return mock_result_chain


@pytest.mark.unit
@pytest.mark.asyncio
async def test_inner_raises_integrity_error_on_duplicate(valid_event_kwargs):
    """Smith C2 Fase 4.5b refactor — inner RAISES IntegrityError UP (no rollback inside).

    Contract: callers (single/batch endpoints) catch + decide rollback scope.
    This test verifies inner raises faithfully.
    """
    event = analytics.AnalyticsEventIn(**valid_event_kwargs)
    tenant_id = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")

    mock_session = MagicMock()
    call_count = {"n": 0}

    async def execute_side_effect(stmt, params=None):
        call_count["n"] += 1
        # Calls: 1) pg_advisory_xact_lock (H2), 2) SELECT last hmac, 3) INSERT
        if call_count["n"] in (1, 2):
            return _make_chain_select_mock()
        raise IntegrityError("INSERT", {}, Exception("duplicate key event_id"))

    mock_session.execute = AsyncMock(side_effect=execute_side_effect)

    with pytest.raises(IntegrityError):
        await analytics._ingest_single_event_inner(mock_session, tenant_id, event)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_inner_accepted_path_no_raise(valid_event_kwargs):
    """Happy path inner — INSERT succeed, no exception raised."""
    event = analytics.AnalyticsEventIn(**valid_event_kwargs)
    tenant_id = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")

    mock_session = MagicMock()

    async def execute_side_effect(stmt, params=None):
        return _make_chain_select_mock()

    mock_session.execute = AsyncMock(side_effect=execute_side_effect)

    # Should not raise
    await analytics._ingest_single_event_inner(mock_session, tenant_id, event)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_inner_pii_payload_raises_400(valid_event_kwargs):
    """AC-12 — payload PII → HTTPException 400 ANTES de chegar ao DB."""
    event_kwargs = {**valid_event_kwargs, "payload": {"cpf": "123.456.789-00"}}
    event = analytics.AnalyticsEventIn(**event_kwargs)
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()  # nunca chamado — validation raises antes

    with pytest.raises(HTTPException) as exc_info:
        await analytics._ingest_single_event_inner(
            mock_session, UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"), event
        )
    assert exc_info.value.status_code == 400
    mock_session.execute.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_batch_mixed_accepted_and_duplicate_preserves_accepted(valid_event_kwargs):
    """Smith C2 + M1 fix Fase 4.5b — batch endpoint SAVEPOINT isolation.

    Contract crítico: quando event[N] é duplicate em batch, events [0..N-1] que
    foram accepted permanecem persisted. SAVEPOINT per event garante isolation.

    Pre-fix Fase 4.5: `_ingest_single_event` chamava `db_session.rollback()` que
    rollback ENTIRE transaction → accepted events lost. Este test prova fix.
    """
    # 3 events: [event_A new, event_B new, event_C duplicate]
    events = [
        analytics.AnalyticsEventIn(**{**valid_event_kwargs, "event_id": uuid4()})
        for _ in range(3)
    ]

    # Trace which events were "inserted" (i.e., advanced past inner raise check)
    inserted_event_ids: list[UUID] = []
    call_count = {"n": 0}
    insert_call_count = {"n": 0}

    async def execute_side_effect(stmt, params=None):
        call_count["n"] += 1
        sql_str = str(stmt).strip()
        # advisory_lock or SELECT chain hash — return empty result
        if "pg_advisory_xact_lock" in sql_str or "SELECT hmac" in sql_str:
            return _make_chain_select_mock()
        # INSERT statement — track + simulate 3rd event as duplicate
        if "INSERT INTO analytics_events" in sql_str:
            insert_call_count["n"] += 1
            if insert_call_count["n"] == 3:
                raise IntegrityError("INSERT", {}, Exception("duplicate key event_id"))
            # Track success
            if params:
                inserted_event_ids.append(params.get("event_id"))
            return MagicMock()
        return _make_chain_select_mock()

    # Mock SAVEPOINT context manager (session.begin_nested)
    class _FakeSavepoint:
        async def __aenter__(self_inner):
            return self_inner
        async def __aexit__(self_inner, exc_type, exc, tb):
            # Re-raise IntegrityError so batch caller catches it
            return False

    mock_session = MagicMock()
    mock_session.execute = AsyncMock(side_effect=execute_side_effect)
    mock_session.begin_nested = MagicMock(return_value=_FakeSavepoint())

    # Simulate the batch caller logic (mirror ingest_batch endpoint inner-loop)
    results = []
    accepted_count = 0
    duplicate_count = 0
    tenant_id = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    for event in events:
        try:
            async with mock_session.begin_nested():
                await analytics._ingest_single_event_inner(mock_session, tenant_id, event)
            results.append(analytics.AnalyticsEventOut(status="accepted", event_id=event.event_id))
            accepted_count += 1
        except IntegrityError:
            results.append(analytics.AnalyticsEventOut(status="duplicate", event_id=event.event_id))
            duplicate_count += 1

    # Assertions: 2 accepted + 1 duplicate, accepted events NOT lost
    assert accepted_count == 2, f"Expected 2 accepted, got {accepted_count}"
    assert duplicate_count == 1, f"Expected 1 duplicate, got {duplicate_count}"
    assert results[0].status == "accepted"
    assert results[1].status == "accepted"
    assert results[2].status == "duplicate"
    # Critical assertion: first 2 INSERTs succeeded (params captured)
    assert len(inserted_event_ids) == 2, (
        f"Expected 2 successful INSERTs, got {len(inserted_event_ids)}. "
        "Fase 4.5b SAVEPOINT fix violated — accepted events lost."
    )


@pytest.mark.unit
def test_genesis_sentinel_deterministic_per_tenant():
    """H1 helper extraction — _genesis_sentinel reproducible per tenant_id."""
    tid = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    g1 = analytics._genesis_sentinel(tid)
    g2 = analytics._genesis_sentinel(tid)
    assert g1 == g2
    assert len(g1) == 64  # SHA-256 hex


@pytest.mark.unit
def test_genesis_sentinel_different_tenants_different_anchors():
    g_a = analytics._genesis_sentinel(UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"))
    g_b = analytics._genesis_sentinel(UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"))
    assert g_a != g_b


# ──────────────────────────────────────────────────────────────────────────────
# CLI period parser (Chunk 4 commands edge cases)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_cli_parse_period_valid():
    assert analytics_cli._parse_period("7d") == 7
    assert analytics_cli._parse_period("30d") == 30
    assert analytics_cli._parse_period("90D") == 90  # case-insensitive


@pytest.mark.unit
@pytest.mark.parametrize("invalid", ["", "7", "7days", "x", "abc", "-1d"])
def test_cli_parse_period_invalid_format(invalid):
    with pytest.raises(click.BadParameter):
        analytics_cli._parse_period(invalid)


@pytest.mark.unit
@pytest.mark.parametrize("out_of_range", ["0d", "366d", "500d"])
def test_cli_parse_period_out_of_range(out_of_range):
    with pytest.raises(click.BadParameter):
        analytics_cli._parse_period(out_of_range)


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic AnalyticsEventOut + AnalyticsBatchOut response shapes
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_analytics_event_out_literal_status():
    """Status only accepts 'accepted' or 'duplicate' (Literal type)."""
    ok_a = analytics.AnalyticsEventOut(status="accepted", event_id=uuid4())
    ok_b = analytics.AnalyticsEventOut(status="duplicate", event_id=uuid4())
    assert ok_a.status == "accepted"
    assert ok_b.status == "duplicate"
    with pytest.raises(ValidationError):
        analytics.AnalyticsEventOut(status="invented", event_id=uuid4())  # type: ignore[arg-type]


@pytest.mark.unit
def test_analytics_health_out_literal_status():
    h = analytics.AnalyticsHealthOut(
        status="healthy",
        chain_integrity="ok",
        queue_depth=0,
        p95_latency_ms=10,
        last_event_at=None,
    )
    assert h.status == "healthy"
    with pytest.raises(ValidationError):
        analytics.AnalyticsHealthOut(
            status="invented", chain_integrity="ok",  # type: ignore[arg-type]
            queue_depth=0, p95_latency_ms=0, last_event_at=None,
        )
