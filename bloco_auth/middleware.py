"""FastAPI dependency-based JWT authentication + RLS context (SP04-AUTH-01).

Idiomático FastAPI 2024+ — usa ``Depends()`` em rotas autenticadas em vez de
middleware global. Rotas pré-login (signup, /login) NÃO declaram ``Depends``
e operam sem RLS context.

Fluxo de uma rota autenticada típica::

    from fastapi import APIRouter, Depends
    from bloco_auth.middleware import get_current_user, apply_rls_context
    from bloco_auth.db import get_sessionmaker

    @router.get("/api/tenant/users")
    async def list_users(
        current: tuple[UUID, UUID] = Depends(get_current_user),
    ):
        tenant_id, user_id = current
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session, apply_rls_context(session, tenant_id):
            # RLS filtra automaticamente users do tenant atual
            result = await session.execute(select(User))
            return result.scalars().all()

Cross-references:
    governance/stories/sp04-auth-01-multi-tenant-auth.md AC-05 (JWT middleware)
    governance/architecture/adr/adr-017-multi-tenant-isolation-rls.md §4
"""

from __future__ import annotations

from uuid import UUID

from fastapi import Header, HTTPException, status

from bloco_auth.db import with_tenant_context
from bloco_auth.jwt_utils import JWTError, decode_jwt


_BEARER_PREFIX = "Bearer "


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> tuple[UUID, UUID]:
    """FastAPI dependency que extrai e valida JWT do header ``Authorization``.

    Args:
        authorization: header ``Authorization: Bearer <token>``. Quando ausente,
            FastAPI passa ``None`` (default) — neste path, raise 401.

    Returns:
        ``(tenant_id, user_id)`` UUIDs decodificados do JWT.

    Raises:
        HTTPException(401): header ausente, formato errado, JWT inválido,
            JWT expirado, claim faltante. Sempre com header
            ``WWW-Authenticate: Bearer`` (RFC 6750 §3).
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith(_BEARER_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header deve seguir formato 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[len(_BEARER_PREFIX) :].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token vazio",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_jwt(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return (payload.tenant_id, payload.user_id)


# Re-export semântico — rotas autenticadas usam ``apply_rls_context`` ao invés
# de importar de ``bloco_auth.db`` diretamente. Mantém todas as primitivas de
# auth + RLS no mesmo namespace ``bloco_auth.middleware``.
apply_rls_context = with_tenant_context


__all__ = ["get_current_user", "apply_rls_context"]
