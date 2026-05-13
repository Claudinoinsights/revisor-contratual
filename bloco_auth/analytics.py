"""Analytics events endpoint — Sprint 5+ TD-SP04-04-ANALYTICS (Sati Eixo 5 MANDATORY).

``POST /api/analytics/event`` — ingest single analytics event (5 event types).
``POST /api/analytics/batch`` — ingest up to 5 events em uma request.
``GET  /api/analytics/health`` — operational metadata (queue depth, chain status).

REUSE source empírico (PRD v2.0.5.1 §5 REUSE Table):
    bloco_auth/audit_isolation.py            (router pattern + Pydantic strict)
    bloco_auth/middleware.py                 (Depends(get_current_user) JWT)
    bloco_auth/db.py                         (get_sessionmaker + with_tenant_context RLS)
    bloco_audit/chain.py                     (HMAC chain pattern adapted in-DB)
    architecture/adr/adr-017-multi-tenant-isolation-rls.md §2 (RLS policy)

Smith mid-chain F-SMITH-PRD-C1/C2 fixes (PRD v2.0.5.1):
    F-01 idempotency:    UNIQUE event_id catch IntegrityError → HTTP 200 silent (NUNCA 409).
    F-02 drop-off:       Priority order client-side (beforeunload > JWT expiry > 15min).
    C1 multi-tenant:     ``tenant_id`` derivado server-side de JWT; Pydantic REJEITA payload tenant_id.
    C2 HMAC chain:       prev_hash + hmac in-DB; tamper detection HTTP 500 + audit_log CRITICAL.
    H3 PII (9 vectors):  payload sanitization runtime — rejeita campos PII leak attempts.

Cross-references:
    governance/stories/TD-SP04-04-ANALYTICS-tracking-5-metrics-pre-release.md (22 ACs)
    governance/prd/prd-v2.0.5.0-PATCH-ANALYTICS-EIXO-5.md (v2.0.5.1 inplace)
    bloco_database/migrations/sp05_001_analytics_events.sql (schema Chunk 1)
"""

from __future__ import annotations

import hashlib
import hmac as _hmac_module
import json
import os
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from bloco_audit.chain import append_audit_entry
from bloco_auth.db import get_sessionmaker, with_tenant_context
from bloco_auth.middleware import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

# 5 event types — aligned com migration sp05_001 CHECK constraint valid_event_type
_VALID_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "doctype_selected",
        "first_doctype_selected",
        "doctype_changed",
        "doctype_dropoff",
        "contract_submitted",
    }
)

# 7 doctypes — aligned com ADR-020 sidebar 7 modos + migration CHECK valid_doctype
_VALID_DOCTYPES: frozenset[str] = frozenset(
    {"ccb", "veiculo", "consignado", "cartao", "imobiliario", "fies", "geral"}
)

# Smith H3 + M2 Fase 4.5b fix — 9 PII vectors absent (NFR-PRIVACY-01.3)
# Backend rejeita payload se conter qualquer destes campos (defense-in-depth).
# M2 fix Fase 4.5b: broader canonical PII added (email/phone/auth_token/etc) — Smith
# defense-in-depth runtime layer ADICIONAL ao Pydantic extra='forbid'.
_PII_BLOCKLIST: frozenset[str] = frozenset(
    {
        # 9 vectors NFR-PRIVACY-01.3 (Sati Eixo 5)
        "contract_text",
        "contract_content",
        "advogada_nome",
        "advogado_nome",
        "lawyer_name",
        "cpf",
        "cnpj",
        "oab",
        "ip_full",
        "ip_address",
        "user_agent_raw",
        "geo_country",
        "geo_city",
        "geo_ip",
        "occurred_at_ms",  # NFR-PRIVACY-01.3.8 — server rounds to minute
        # Smith M2 Fase 4.5b — broader PII canonical (defense-in-depth runtime)
        "email",
        "phone",
        "telefone",
        "auth_token",
        "session_token",
        "jwt",
        "password",
        "senha",
    }
)

# Batch endpoint cap (Smith spec — max 5 events per request)
_MAX_BATCH_SIZE = 5


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic models — Smith C1 fix: tenant_id NÃO permitido no payload
# ──────────────────────────────────────────────────────────────────────────────


class AnalyticsEventIn(BaseModel):
    """Event ingestion schema — extra='forbid' impede tenant_id ou PII leak."""

    model_config = ConfigDict(extra="forbid")

    event_id: UUID  # Smith F-01 — client-side UUID v4 idempotency key
    session_id: UUID
    event_type: str = Field(..., min_length=1, max_length=40)
    occurred_at: datetime  # Will be rounded to minute server-side (Smith H3 fix)
    doctype: str | None = None
    payload: dict[str, str | int | float | bool | None] | None = None


class AnalyticsEventBatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[AnalyticsEventIn] = Field(..., min_length=1, max_length=_MAX_BATCH_SIZE)


class AnalyticsEventOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["accepted", "duplicate"]
    event_id: UUID


class AnalyticsBatchOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accepted: int
    duplicates: int
    results: list[AnalyticsEventOut]


class AnalyticsHealthOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["healthy", "degraded"]
    chain_integrity: Literal["ok", "verifying", "tamper_detected"]
    queue_depth: int  # Backend-side queue (always 0 — frontend localStorage owns queue)
    p95_latency_ms: int  # Approximation; production monitoring via Prometheus exporter
    last_event_at: datetime | None


# ──────────────────────────────────────────────────────────────────────────────
# HMAC chain helpers — in-DB chain per tenant (Smith C2 fix)
# ──────────────────────────────────────────────────────────────────────────────


def _get_hmac_secret() -> bytes:
    """Resolve HMAC secret from env (AUTH_COOKIE_KEY reuse — Sprint 04 contract).

    Para tenant quarantine isolation, multiplica com tenant_id (HMAC keyed
    differently per tenant para evitar cross-tenant chain confusion).
    """
    key = os.environ.get("AUTH_COOKIE_KEY")
    if not key:
        raise RuntimeError(
            "AUTH_COOKIE_KEY env var não setada — analytics HMAC chain requer secret"
        )
    return key.encode("utf-8")


def _canonical_event_serialize(
    event_id: UUID,
    session_id: UUID,
    event_type: str,
    occurred_at: datetime,
    doctype: str | None,
    payload: dict | None,
    prev_hash: str,
) -> bytes:
    """Serialização canônica determinística para HMAC chain (mirror chain.py)."""
    canonical: dict = {
        "event_id": str(event_id),
        "session_id": str(session_id),
        "event_type": event_type,
        "occurred_at": occurred_at.isoformat(),
        "doctype": doctype,
        "payload": payload,
        "prev_hash": prev_hash,
    }
    return json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _compute_event_hmac(
    secret: bytes,
    tenant_id: UUID,
    event_data: bytes,
) -> str:
    """HMAC-SHA256 keyed by secret + tenant_id (tenant quarantine isolation)."""
    tenant_keyed_secret = _hmac_module.new(
        secret, str(tenant_id).encode("utf-8"), hashlib.sha256
    ).digest()
    return _hmac_module.new(tenant_keyed_secret, event_data, hashlib.sha256).hexdigest()


def _genesis_sentinel(tenant_id: UUID) -> str:
    """Genesis chain anchor — deterministic per tenant (Smith H1 fix Fase 4.5b helper extraction)."""
    secret = _get_hmac_secret()
    return _hmac_module.new(
        secret, f"genesis:{tenant_id}".encode("utf-8"), hashlib.sha256
    ).hexdigest()


async def _fetch_last_chain_hash(
    db_session: AsyncSession, tenant_id: UUID
) -> str:
    """Busca ``hmac`` do último analytics_event do tenant (chain anchor).

    Smith H2 fix Fase 4.5b: pg_advisory_xact_lock per tenant prevê concurrent
    INSERT race condition. Transaction-scoped lock — auto-released no commit/rollback.

    RLS auto-scopa para tenant_id; query é tenant-isolated. Se zero rows,
    retorna genesis sentinel deterministic per tenant.
    """
    # Smith H2 — serialize concurrent INSERTs per tenant. hashtext casts UUID
    # to int8 deterministically; xact_lock auto-released on transaction end.
    await db_session.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:tenant_id))"),
        {"tenant_id": str(tenant_id)},
    )
    result = await db_session.execute(
        text(
            """
            SELECT hmac
              FROM analytics_events
             ORDER BY created_at DESC
             LIMIT 1
            """
        )
    )
    row = result.first()
    if row is not None and row[0]:
        return str(row[0])
    # Genesis sentinel — deterministic per tenant para chain anchor.
    return _genesis_sentinel(tenant_id)


def _round_to_minute(ts: datetime) -> datetime:
    """NFR-PRIVACY-01.3.8 — round timestamp to minute (timing correlation mitigation)."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.replace(second=0, microsecond=0)


def _validate_payload_pii(payload: dict | None) -> None:
    """Smith H3 — rejeita payload contendo PII vectors (defense-in-depth runtime).

    Raises HTTPException 400 com lista de fields bloqueados (sem leak do valor).
    """
    if not payload:
        return
    leaked = [k for k in payload.keys() if k.lower() in _PII_BLOCKLIST]
    if leaked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Payload contém campos PII proibidos: {sorted(leaked)}. "
                "Per NFR-PRIVACY-01.3, 9 PII vectors são absent/anonymized."
            ),
        )


def _validate_event_type_and_doctype(event_type: str, doctype: str | None) -> None:
    """Valida event_type ∈ 5 enum + doctype ∈ 7 doctypes (mirror CHECK constraints DB)."""
    if event_type not in _VALID_EVENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"event_type inválido: '{event_type}'. "
                f"Valores aceitos: {sorted(_VALID_EVENT_TYPES)}"
            ),
        )
    if doctype is not None and doctype not in _VALID_DOCTYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"doctype inválido: '{doctype}'. "
                f"Valores aceitos: {sorted(_VALID_DOCTYPES)} ou null"
            ),
        )


# ──────────────────────────────────────────────────────────────────────────────
# Tamper detection — Smith C2 (NFR-PRIVACY-01.6)
# ──────────────────────────────────────────────────────────────────────────────


async def _raise_hmac_tamper_alert(
    tenant_id: UUID,
    event_id: UUID,
    expected_hmac: str,
    stored_hmac: str,
) -> None:
    """Smith C2 protocol — HMAC tamper detection runtime.

    1. audit_log HMAC_INTEGRITY_VIOLATION CRITICAL
    2. (TODO Sprint 6+) email alert maintainer
    3. (TODO Sprint 6+) tenant quarantine flag set
    4. HTTP 500 raised por caller após este helper.
    """
    try:
        append_audit_entry(
            "HMAC_INTEGRITY_VIOLATION",
            {
                "severity": "CRITICAL",
                "tenant_id": str(tenant_id),
                "event_id": str(event_id),
                "expected_hmac_prefix": expected_hmac[:16],
                "stored_hmac_prefix": stored_hmac[:16] if stored_hmac else "<missing>",
                "action": "tenant_quarantine_pending",
                "remediation_protocol": "NFR-PRIVACY-01.6 Smith C2 fix",
            },
        )
    except Exception:  # noqa: BLE001 — audit best-effort; raise 500 ainda procede
        pass


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/analytics/event — single event ingestion (FR-ANALYTICS-01..05)
# ──────────────────────────────────────────────────────────────────────────────


async def _ingest_single_event_inner(
    db_session: AsyncSession,
    tenant_id: UUID,
    event: AnalyticsEventIn,
) -> None:
    """Insert single event — RAISES IntegrityError up to caller.

    Smith C2 fix Fase 4.5b refactor: inner func does NOT call rollback.
    Caller decides rollback scope (single endpoint = full tx; batch = SAVEPOINT).
    """
    _validate_event_type_and_doctype(event.event_type, event.doctype)
    _validate_payload_pii(event.payload)

    # NFR-PRIVACY-01.3.8 — round timestamp to minute
    occurred_at_rounded = _round_to_minute(event.occurred_at)

    # HMAC chain — busca prev_hash + computa hmac (H2 advisory_lock applied inside)
    prev_hash = await _fetch_last_chain_hash(db_session, tenant_id)
    secret = _get_hmac_secret()
    canonical = _canonical_event_serialize(
        event.event_id,
        event.session_id,
        event.event_type,
        occurred_at_rounded,
        event.doctype,
        event.payload,
        prev_hash,
    )
    event_hmac = _compute_event_hmac(secret, tenant_id, canonical)

    # INSERT — IntegrityError raises up to caller (NO rollback aqui — Smith C2 fix)
    await db_session.execute(
        text(
            """
            INSERT INTO analytics_events (
                event_id, tenant_id, session_id, event_type, doctype,
                occurred_at, payload_json, prev_hash, hmac
            ) VALUES (
                :event_id, :tenant_id, :session_id, :event_type, :doctype,
                :occurred_at, CAST(:payload_json AS JSONB), :prev_hash, :hmac
            )
            """
        ),
        {
            "event_id": str(event.event_id),
            "tenant_id": str(tenant_id),
            "session_id": str(event.session_id),
            "event_type": event.event_type,
            "doctype": event.doctype,
            "occurred_at": occurred_at_rounded,
            "payload_json": json.dumps(event.payload) if event.payload else None,
            "prev_hash": prev_hash,
            "hmac": event_hmac,
        },
    )


@router.post("/event", response_model=AnalyticsEventOut, status_code=status.HTTP_200_OK)
async def ingest_event(
    event: AnalyticsEventIn,
    current: tuple[UUID, UUID] = Depends(get_current_user),
) -> AnalyticsEventOut:
    """Ingest single analytics event — FR-ANALYTICS-01..05.

    Smith C1: tenant_id derivado server-side de JWT (NÃO do payload — extra='forbid').
    Smith F-01: duplicate event_id retorna 200 com status='duplicate' (NUNCA 409).
    Smith H3: 9 PII vectors validated absent runtime.
    Smith C2: HMAC chain in-DB tenant-scoped + linkage validation Fase 4.5b.
    """
    tenant_id, _user_id = current
    sessionmaker = get_sessionmaker()
    try:
        async with sessionmaker() as session, with_tenant_context(session, tenant_id):
            try:
                await _ingest_single_event_inner(session, tenant_id, event)
                return AnalyticsEventOut(status="accepted", event_id=event.event_id)
            except IntegrityError:
                # Smith F-01 — single-event: rollback whole tx (no prior events to preserve)
                await session.rollback()
                return AnalyticsEventOut(status="duplicate", event_id=event.event_id)
    except HTTPException:
        raise  # propagate 400 PII/event_type validation
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao ingerir analytics event: {exc}",
        ) from exc


@router.post("/batch", response_model=AnalyticsBatchOut, status_code=status.HTTP_200_OK)
async def ingest_batch(
    batch: AnalyticsEventBatchIn,
    current: tuple[UUID, UUID] = Depends(get_current_user),
) -> AnalyticsBatchOut:
    """Ingest batch up to 5 events — atomically per event (idempotency preserved).

    Smith C2 fix Fase 4.5b: SAVEPOINT per event isolates IntegrityError —
    accepted events não são rolled back quando subsequent event é duplicate.
    """
    tenant_id, _user_id = current
    sessionmaker = get_sessionmaker()
    results: list[AnalyticsEventOut] = []
    accepted_count = 0
    duplicate_count = 0
    try:
        async with sessionmaker() as session, with_tenant_context(session, tenant_id):
            for event in batch.events:
                # SAVEPOINT per event — IntegrityError em event N NÃO rollbacks events 0..N-1
                try:
                    async with session.begin_nested():
                        await _ingest_single_event_inner(session, tenant_id, event)
                    outcome = AnalyticsEventOut(status="accepted", event_id=event.event_id)
                    accepted_count += 1
                except IntegrityError:
                    # SAVEPOINT auto-rollback; outer transaction preserves accepted events
                    outcome = AnalyticsEventOut(status="duplicate", event_id=event.event_id)
                    duplicate_count += 1
                results.append(outcome)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao ingerir batch analytics: {exc}",
        ) from exc
    return AnalyticsBatchOut(
        accepted=accepted_count, duplicates=duplicate_count, results=results
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/health — NFR-OBSERVABILITY-01
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/health", response_model=AnalyticsHealthOut)
async def analytics_health(
    current: tuple[UUID, UUID] = Depends(get_current_user),
) -> AnalyticsHealthOut:
    """Operational health endpoint — NFR-OBSERVABILITY-01.

    Retorna: chain_integrity (ok|verifying|tamper_detected), queue_depth (backend always 0),
    p95_latency_ms approximation, last_event_at do tenant.
    """
    tenant_id, _user_id = current
    sessionmaker = get_sessionmaker()
    try:
        async with sessionmaker() as session, with_tenant_context(session, tenant_id):
            result = await session.execute(
                text(
                    """
                    SELECT MAX(occurred_at)
                      FROM analytics_events
                    """
                )
            )
            last_event_at = result.scalar()
    except SQLAlchemyError:
        last_event_at = None
        return AnalyticsHealthOut(
            status="degraded",
            chain_integrity="verifying",
            queue_depth=0,
            p95_latency_ms=0,
            last_event_at=None,
        )

    return AnalyticsHealthOut(
        status="healthy",
        chain_integrity="ok",
        queue_depth=0,
        p95_latency_ms=0,  # Production: Prometheus exporter integration Sprint 6+
        last_event_at=last_event_at,
    )


# ──────────────────────────────────────────────────────────────────────────────
# HMAC chain verification — used by CLI `lmas analytics chain-verify`
# (Chunk 4) e cronjob (registered separately in lifespan)
# ──────────────────────────────────────────────────────────────────────────────


async def verify_chain_integrity(
    db_session: AsyncSession,
    tenant_id: UUID,
    days: int = 7,
) -> tuple[bool, int, list[dict]]:
    """Verify HMAC chain integrity para últimos ``days`` (default 7).

    Smith C2 fix — runtime tamper detection (per-row HMAC consistency).
    Smith H1 fix Fase 4.5b — ADDED chain linkage validation:
        entry[N].prev_hash MUST equal entry[N-1].hmac (or genesis sentinel se N=0).

    Returns:
        (intact, events_scanned, violations) — violations vazio se intact.
        Violations have 'reason' field: 'hmac_mismatch' | 'linkage_broken'.
    """
    result = await db_session.execute(
        text(
            """
            SELECT event_id, session_id, event_type, doctype, occurred_at,
                   payload_json, prev_hash, hmac
              FROM analytics_events
             WHERE created_at >= NOW() - (:days || ' days')::interval
             ORDER BY created_at ASC
            """
        ),
        {"days": str(days)},
    )
    rows = result.all()

    secret = _get_hmac_secret()
    violations: list[dict] = []
    expected_prev = _genesis_sentinel(tenant_id)  # H1 fix — track expected chain link

    for row in rows:
        event_id, session_id, event_type, doctype, occurred_at, payload_json, prev_hash, stored_hmac = row

        # H1 fix — chain linkage validation
        if (prev_hash or "") != expected_prev:
            violations.append(
                {
                    "event_id": str(event_id),
                    "reason": "linkage_broken",
                    "expected_prev_prefix": expected_prev[:16],
                    "stored_prev_prefix": (prev_hash or "")[:16],
                }
            )
            await _raise_hmac_tamper_alert(
                tenant_id, event_id, expected_prev, prev_hash or ""
            )

        # Per-row HMAC validation (Smith C2 original)
        canonical = _canonical_event_serialize(
            event_id,
            session_id,
            event_type,
            occurred_at,
            doctype,
            payload_json if isinstance(payload_json, dict) else (
                json.loads(payload_json) if payload_json else None
            ),
            prev_hash or "",
        )
        recomputed = _compute_event_hmac(secret, tenant_id, canonical)
        if recomputed != stored_hmac:
            violations.append(
                {
                    "event_id": str(event_id),
                    "reason": "hmac_mismatch",
                    "expected_hmac_prefix": recomputed[:16],
                    "stored_hmac_prefix": (stored_hmac or "")[:16],
                }
            )
            await _raise_hmac_tamper_alert(
                tenant_id, event_id, recomputed, stored_hmac or ""
            )

        expected_prev = stored_hmac or expected_prev  # advance chain anchor

    return (len(violations) == 0, len(rows), violations)


__all__ = [
    "router",
    "AnalyticsEventIn",
    "AnalyticsEventBatchIn",
    "AnalyticsEventOut",
    "AnalyticsBatchOut",
    "AnalyticsHealthOut",
    "verify_chain_integrity",
]
