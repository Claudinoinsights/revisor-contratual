"""BYOK lifecycle state machine (SP04-BYOK-01 / AC-05 + AC-06 + AC-07 + ADR-014).

Funções state machine BYOK:
    - ``start_rotation`` — current → pending_rotation overlap 24h (FR-API-KEY-03)
    - ``revoke`` — purge encrypted_key + tenant.status='suspended_byok' (FR-API-KEY-04)
    - ``get_status`` — read-only fingerprint truncated + last_used_at + rotation info

Auto-complete rotation 24h é responsabilidade do **pg_cron stored procedure**
``complete_pending_rotations()`` (Tank Phase 12.3a Item 2 — chunk 2 migration).
Este módulo Python expõe apenas os flows trigger + read-only.

Cross-references:
    governance/stories/sp04-byok-01-anthropic-key-lifecycle.md AC-05/06/07
    governance/architecture/adr/adr-014-provider-abstraction-byok.md §5
    bloco_auth/byok_encryption.py (encrypt_api_key + truncate_fingerprint)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bloco_auth.byok_encryption import encrypt_api_key, truncate_fingerprint
from bloco_auth.models import Tenant, TenantAPIKey


_ROTATION_OVERLAP_HOURS = 24


class BYOKLifecycleError(RuntimeError):
    """Erro genérico do lifecycle BYOK."""


class RotationConflictError(BYOKLifecycleError):
    """Tentativa de start_rotation com rotation já em andamento (409 Conflict)."""


class BYOKNotFoundError(BYOKLifecycleError):
    """Tenant não tem ``tenant_api_keys`` row (404 Not Found / nunca onboarded)."""


# ──────────────────────────────────────────────────────────────────────────────
# State machine — start_rotation
# ──────────────────────────────────────────────────────────────────────────────


async def start_rotation(
    tenant_id: UUID,
    new_api_key: str,
    db_session: AsyncSession,
) -> dict[str, str]:
    """Inicia rotation dual-key 24h overlap (Tank Item 1 + ADR-014 §5).

    State machine:
        active → pending_rotation (UPDATE pending_* + rotation_started_at = NOW())

    Background pg_cron procedure ``complete_pending_rotations()`` finaliza
    automaticamente quando ``rotation_started_at + 24h ≤ NOW()`` (chunk 2 migration).

    Args:
        tenant_id: UUID do tenant.
        new_api_key: nova API key Anthropic já validada via ping (caller responsibility).
        db_session: AsyncSession ativa com RLS context aplicado.

    Returns:
        ``{"status": "pending_rotation", "started_at": ISO, "complete_at": ISO}``

    Raises:
        BYOKNotFoundError: tenant não tem row em ``tenant_api_keys`` (não onboarded).
        RotationConflictError: rotation já em andamento (status='pending_rotation').
    """
    result = await db_session.execute(
        select(TenantAPIKey).where(TenantAPIKey.tenant_id == tenant_id)
    )
    key_row = result.scalar_one_or_none()

    if key_row is None:
        raise BYOKNotFoundError(
            f"Tenant {tenant_id} não tem BYOK configurado — re-onboarding necessário"
        )

    if key_row.status == "pending_rotation":
        complete_at = key_row.rotation_started_at + timedelta(hours=_ROTATION_OVERLAP_HOURS)
        raise RotationConflictError(
            f"Rotation já em andamento. Complete at: {complete_at.isoformat()}"
        )

    if key_row.status == "revoked":
        raise BYOKLifecycleError(
            "BYOK revoked — re-onboarding step2 necessário antes de rotation"
        )

    # status == 'active' — proceed rotation
    encrypted_new = await encrypt_api_key(new_api_key, db_session)
    fingerprint_new = truncate_fingerprint(new_api_key)
    started_at = datetime.now(timezone.utc)

    await db_session.execute(
        update(TenantAPIKey)
        .where(TenantAPIKey.tenant_id == tenant_id)
        .values(
            status="pending_rotation",
            pending_encrypted_key=encrypted_new,
            pending_fingerprint=fingerprint_new,
            rotation_started_at=started_at,
        )
    )

    return {
        "status": "pending_rotation",
        "started_at": started_at.isoformat(),
        "complete_at": (started_at + timedelta(hours=_ROTATION_OVERLAP_HOURS)).isoformat(),
        "old_fingerprint": key_row.key_fingerprint,
        "new_fingerprint": fingerprint_new,
    }


# ──────────────────────────────────────────────────────────────────────────────
# State machine — revoke
# ──────────────────────────────────────────────────────────────────────────────


async def revoke(
    tenant_id: UUID,
    user_id: UUID,
    reason: Literal["suspected_compromise", "off_boarding", "other"],
    db_session: AsyncSession,
) -> dict[str, str]:
    """Revoga BYOK com purge encrypted (LGPD compliance — Tank Item 1 invariante).

    Atomic UPDATE:
        - tenant_api_keys: encrypted_key = NULL, pending_* = NULL, status = 'revoked',
          rotation_started_at = NULL
        - tenants: status = 'suspended_byok' (Tank Item 4 enum strict)

    Subsequent inference attempts retornam 403 Forbidden via ``get_anthropic_client``
    middleware (chunk 5) — força re-onboarding step2 para reativar tenant.

    Args:
        tenant_id: UUID do tenant.
        user_id: UUID do user que executou revoke (audit trail).
        reason: motivo (suspected_compromise | off_boarding | other).
        db_session: AsyncSession ativa.

    Returns:
        ``{"status": "revoked", "reason": ..., "revoked_at": ISO}``

    Raises:
        BYOKNotFoundError: tenant não tem row em ``tenant_api_keys``.
    """
    result = await db_session.execute(
        select(TenantAPIKey).where(TenantAPIKey.tenant_id == tenant_id)
    )
    key_row = result.scalar_one_or_none()

    if key_row is None:
        raise BYOKNotFoundError(f"Tenant {tenant_id} não tem BYOK para revogar")

    revoked_at = datetime.now(timezone.utc)

    # Atomic update tenant_api_keys (clear encrypted + pending_*)
    await db_session.execute(
        update(TenantAPIKey)
        .where(TenantAPIKey.tenant_id == tenant_id)
        .values(
            encrypted_key=None,
            pending_encrypted_key=None,
            pending_fingerprint=None,
            status="revoked",
            rotation_started_at=None,
        )
    )

    # Cascade tenants.status = 'suspended_byok' (Tank Item 4 enum strict)
    await db_session.execute(
        update(Tenant)
        .where(Tenant.id == tenant_id)
        .values(status="suspended_byok")
    )

    return {
        "status": "revoked",
        "reason": reason,
        "revoked_at": revoked_at.isoformat(),
        "old_fingerprint": key_row.key_fingerprint,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Read-only — get_status
# ──────────────────────────────────────────────────────────────────────────────


async def get_status(
    tenant_id: UUID,
    db_session: AsyncSession,
) -> dict:
    """Read-only status BYOK para Settings UI panel (AC-07).

    Args:
        tenant_id: UUID do tenant.
        db_session: AsyncSession ativa com RLS context.

    Returns:
        ``{"status": ..., "key_fingerprint": ..., "created_at": ...,
        "last_used_at": ..., "rotation": {...} | None}``

    Raises:
        BYOKNotFoundError: tenant não tem row.
    """
    result = await db_session.execute(
        select(TenantAPIKey).where(TenantAPIKey.tenant_id == tenant_id)
    )
    key_row = result.scalar_one_or_none()

    if key_row is None:
        raise BYOKNotFoundError(f"Tenant {tenant_id} não tem BYOK configurado")

    rotation_info = None
    if key_row.status == "pending_rotation":
        complete_at = key_row.rotation_started_at + timedelta(hours=_ROTATION_OVERLAP_HOURS)
        rotation_info = {
            "pending_fingerprint": key_row.pending_fingerprint,
            "started_at": key_row.rotation_started_at.isoformat(),
            "complete_at": complete_at.isoformat(),
        }

    return {
        "status": key_row.status,
        "key_fingerprint": key_row.key_fingerprint,
        "created_at": key_row.created_at.isoformat() if key_row.created_at else None,
        "last_used_at": key_row.last_used_at.isoformat() if key_row.last_used_at else None,
        "rotation": rotation_info,
    }


__all__ = [
    "BYOKLifecycleError",
    "RotationConflictError",
    "BYOKNotFoundError",
    "start_rotation",
    "revoke",
    "get_status",
]
