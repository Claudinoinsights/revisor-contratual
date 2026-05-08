"""BYOK API endpoints (SP04-BYOK-01 / AC-05 + AC-06 + AC-07).

APIRouter ``/api/tenant/byok`` com 3 endpoints autenticados (Depends get_current_user):
    - POST /rotate — start dual-key rotation 24h overlap
    - POST /revoke — purge encrypted + tenant suspended_byok + force re-onboarding
    - GET /status — read-only fingerprint truncated + rotation info

Todos os endpoints usam ``apply_rls_context`` middleware AUTH-01 BACKBONE para
RLS isolation per tenant (defense-in-depth).

Cross-references:
    governance/stories/sp04-byok-01-anthropic-key-lifecycle.md AC-05/06/07
    bloco_auth/byok_lifecycle.py (state machine functions)
    bloco_auth/middleware.py (get_current_user + apply_rls_context)
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from bloco_auth.byok_lifecycle import (
    BYOKLifecycleError,
    BYOKNotFoundError,
    RotationConflictError,
    get_status,
    revoke,
    start_rotation,
)
from bloco_auth.middleware import apply_rls_context, get_current_user
from bloco_auth.onboarding import ping_anthropic_api


router = APIRouter(prefix="/api/tenant/byok", tags=["byok"])


# ──────────────────────────────────────────────────────────────────────────────
# Request/Response schemas
# ──────────────────────────────────────────────────────────────────────────────


class RotateRequest(BaseModel):
    """POST /rotate body — nova API key Anthropic."""

    model_config = ConfigDict(extra="forbid")

    new_api_key: str = Field(..., min_length=10, max_length=200)


class RevokeRequest(BaseModel):
    """POST /revoke body — motivo da revogação (audit trail)."""

    model_config = ConfigDict(extra="forbid")

    reason: Literal["suspected_compromise", "off_boarding", "other"]


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/rotate", status_code=status.HTTP_202_ACCEPTED)
async def rotate_endpoint(
    body: RotateRequest,
    current_user: tuple[UUID, UUID] = Depends(get_current_user),
) -> dict:
    """Inicia rotation dual-key 24h overlap (FR-API-KEY-03).

    Flow:
        1. Validate ``body.new_api_key`` via ``ping_anthropic_api`` (reuse AUTH-01 helper)
        2. ``start_rotation()`` UPDATE pending_* + rotation_started_at
        3. pg_cron auto-complete em 24h (Tank Item 2 — chunk 2 migration)

    Returns:
        202 Accepted: ``{"status": "pending_rotation", "started_at": ..., "complete_at": ...}``

    Raises:
        400 Bad Request: ``new_api_key`` inválida via ping Anthropic
        404 Not Found: tenant sem BYOK configurado
        409 Conflict: rotation já em andamento
    """
    from bloco_auth.db import get_sessionmaker

    tenant_id, _user_id = current_user

    # Validate new key via ping Anthropic (reuse AUTH-01 helper)
    try:
        await ping_anthropic_api(body.new_api_key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"new_api_key inválida — falha ping Anthropic: {exc}",
        ) from exc

    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db_session, apply_rls_context(db_session, tenant_id):
        try:
            result = await start_rotation(tenant_id, body.new_api_key, db_session)
            await db_session.commit()
            return result
        except BYOKNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RotationConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except BYOKLifecycleError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_endpoint(
    body: RevokeRequest,
    current_user: tuple[UUID, UUID] = Depends(get_current_user),
) -> None:
    """Revoga BYOK self-service (FR-API-KEY-04).

    Atomic update: encrypted_key=NULL + status='revoked' + tenant.status='suspended_byok'.

    Subsequent inference calls retornam 403 Forbidden via runtime middleware —
    força re-onboarding step2 para reativar tenant.

    Returns:
        204 No Content (idempotent — revoke já-revoked é no-op)

    Raises:
        404 Not Found: tenant sem BYOK
    """
    from bloco_auth.db import get_sessionmaker

    tenant_id, user_id = current_user
    sessionmaker = get_sessionmaker()

    async with sessionmaker() as db_session, apply_rls_context(db_session, tenant_id):
        try:
            await revoke(tenant_id, user_id, body.reason, db_session)
            await db_session.commit()
        except BYOKNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/status")
async def status_endpoint(
    current_user: tuple[UUID, UUID] = Depends(get_current_user),
) -> dict:
    """Read-only status BYOK para Settings UI panel (AC-07).

    Returns:
        200 OK: ``{"status", "key_fingerprint", "created_at", "last_used_at", "rotation"}``

    Raises:
        404 Not Found: tenant sem BYOK configurado
    """
    from bloco_auth.db import get_sessionmaker

    tenant_id, _user_id = current_user
    sessionmaker = get_sessionmaker()

    async with sessionmaker() as db_session, apply_rls_context(db_session, tenant_id):
        try:
            return await get_status(tenant_id, db_session)
        except BYOKNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


__all__ = ["router"]
