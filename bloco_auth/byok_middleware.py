"""BYOK runtime injection middleware FastAPI Depends (SP04-BYOK-01 / AC-04 + ADR-014).

Decrypta ``tenant_api_keys.encrypted_key`` do tenant ativo + instancia
``anthropic.Anthropic(api_key=...)`` SDK per-request. Cache request-scoped via
FastAPI ``Depends`` caching (não cross-request por security — cada request
paga overhead decrypt de ~1-2ms para isolation).

Failure paths:
    - 403 Forbidden: row None OR status='revoked' OR encrypted_key NULL
      (re-onboarding step2 necessário)
    - 503 Service Unavailable: pgp_sym_decrypt falha (master_key mismatch,
      blob corrompido) — audit ``byok_decryption_failed`` + alert operacional

Tank Phase 12.3a Item 5 aplicado: ``last_used_at`` UPDATE inline per-request
(volume MVP 0.005 writes/sec justifica simplicidade; promotion para background
batch em 50K writes/day — TD-SP04-05 Sprint 06+).

Cross-references:
    governance/stories/sp04-byok-01-anthropic-key-lifecycle.md AC-04
    bloco_auth/middleware.py (get_current_user upstream Depends)
    .lmas/handoffs/handoff-dbe-to-dev-2026-05-08-sp04-phase12-ratify-byok-01.yaml
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from anthropic import Anthropic  # type-only import (lazy runtime)

from bloco_auth.byok_encryption import decrypt_api_key
from bloco_auth.middleware import get_current_user
from bloco_auth.models import TenantAPIKey


async def _audit_byok_event(
    db_session: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    action: str,
    key_fingerprint: str | None,
) -> None:
    """Best-effort audit chain emit para eventos BYOK runtime.

    Pattern alinhado SP04-AUTH-01 ``_audit`` helper — try/except: pass por padrão
    (CC.39 hardening Sprint 03 preserva user-facing functionality). TD-SP04-03
    Sprint 06+: adicionar structlog logger para observability.
    """
    try:
        # Lazy import — bloco_audit.chain pode não estar configurado em dev local
        from bloco_audit.chain import append_event  # type: ignore

        await append_event(
            event_type=action,
            payload={
                "tenant_id": str(tenant_id),
                "user_id": str(user_id),
                "action": action,
                "key_fingerprint": key_fingerprint,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            db_session=db_session,
        )
    except Exception:
        # CC.39 hardening — audit best-effort
        pass


async def get_anthropic_client(
    current_user: tuple[UUID, UUID] = Depends(get_current_user),
) -> "Anthropic":
    """FastAPI Depends — decrypta api_key tenant ativo + retorna Anthropic SDK instance.

    **Não** recebe ``db_session`` via Depends pois isto criaria deps cycle no
    middleware stack. Em vez, abre sessão própria via ``get_sessionmaker()``
    para query/UPDATE BYOK + audit (request-scoped lifecycle).

    Args:
        current_user: ``(tenant_id, user_id)`` UUID tuple do JWT decoded.

    Returns:
        ``Anthropic(api_key=...)`` SDK instance pronta para inference call.

    Raises:
        HTTPException(403): BYOK não configurado, revogado, OR encrypted NULL
            — re-onboarding step2 necessário.
        HTTPException(503): decryption failure — master_key mismatch, blob
            corrompido. Audit ``byok_decryption_failed`` + alert operacional.
    """
    from bloco_auth.db import get_sessionmaker, with_tenant_context

    tenant_id, user_id = current_user
    sessionmaker = get_sessionmaker()

    async with sessionmaker() as db_session, with_tenant_context(db_session, tenant_id):
        # RLS aplicado via SET LOCAL app.tenant_id (middleware AUTH-01 pattern)
        result = await db_session.execute(
            select(TenantAPIKey).where(TenantAPIKey.tenant_id == tenant_id)
        )
        key_row = result.scalar_one_or_none()

        if key_row is None or key_row.status == "revoked" or key_row.encrypted_key is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="BYOK não configurado ou revogado — re-onboarding step2 necessário",
            )

        try:
            plain_key = await decrypt_api_key(key_row.encrypted_key, db_session)
        except Exception as exc:
            await _audit_byok_event(
                db_session, tenant_id, user_id,
                "byok_decryption_failed", key_row.key_fingerprint,
            )
            await db_session.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="BYOK decryption failure — operator alert triggered",
            ) from exc

        # inline UPDATE per request (Tank decision Phase 12.3a Item 5;
        # volume MVP 0.005 writes/sec justifica simplicidade;
        # promotion para background batch em 50K writes/day — TD-SP04-05)
        await db_session.execute(
            update(TenantAPIKey)
            .where(TenantAPIKey.tenant_id == tenant_id)
            .values(last_used_at=datetime.now(timezone.utc))
        )

        # Audit byok_key_used (best-effort)
        await _audit_byok_event(
            db_session, tenant_id, user_id,
            "byok_key_used", key_row.key_fingerprint,
        )

        await db_session.commit()

    # Lazy import — anthropic SDK só requer instalado em runtime quando inference
    # call ocorre. Permite skeleton/test loading sem deps instalados.
    from anthropic import Anthropic  # noqa: PLC0415

    return Anthropic(api_key=plain_key)


__all__ = ["get_anthropic_client"]
