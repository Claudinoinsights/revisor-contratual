"""Async SQLAlchemy engine + session factory + RLS context helper (SP04-AUTH-01).

Foundation técnica usada pelo middleware FastAPI (chunk 3) e pelos testes de
integração (chunk 4 +). Centraliza:

1. ``get_engine()`` — async engine singleton (lazy, lê ``DATABASE_URL`` do env)
2. ``get_sessionmaker()`` — factory ``AsyncSession`` para uso em dependency
   injection do FastAPI
3. ``with_tenant_context(session, tenant_id)`` — context manager assíncrono que
   executa ``SET LOCAL app.tenant_id = '<uuid>'`` dentro de uma transaction
   PostgreSQL, ativando RLS automaticamente para todas as queries posteriores

Cross-references:
    bloco_database/migrations/sp04_001_auth_multitenant.sql (RLS policies)
    governance/architecture/adr/adr-017-multi-tenant-isolation-rls.md §4
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


class DatabaseConfigError(RuntimeError):
    """``DATABASE_URL`` ausente ou inválida no ambiente."""


def get_engine() -> AsyncEngine:
    """Retorna o async engine singleton (cria sob demanda).

    Lê ``DATABASE_URL`` do environment. Em produção, este valor vem de secret
    manager via Operator (rule deploy-safety.md). Em dev, vem do ``.env``
    carregado por ``python-dotenv`` ou similar.

    Raises:
        DatabaseConfigError: se ``DATABASE_URL`` não estiver setada.
    """
    global _engine
    if _engine is None:
        url = os.getenv("DATABASE_URL")
        if not url:
            raise DatabaseConfigError(
                "DATABASE_URL não setada — ver .env.example seção Sprint 04 "
                "(SP04-AUTH-01 requer PostgreSQL 16 com extension pgcrypto)."
            )
        _engine = create_async_engine(
            url,
            pool_pre_ping=True,  # detecta conexões mortas antes de query
            future=True,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Retorna o sessionmaker async (cria sob demanda)."""
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _sessionmaker


@asynccontextmanager
async def with_tenant_context(
    session: AsyncSession, tenant_id: UUID
) -> AsyncIterator[AsyncSession]:
    """Context manager que ativa RLS para o tenant dentro de uma transaction.

    Uso típico (dentro de request handler FastAPI autenticado)::

        async with sessionmaker() as session, with_tenant_context(session, tid):
            result = await session.execute(select(User))
            # RLS automaticamente filtra users do tenant `tid`

    O ``SET LOCAL`` garante que o ``app.tenant_id`` é descartado ao fim da
    transaction — sem leakage para outras conexões do pool. Caso ``tenant_id``
    seja ``None`` (ex.: rotas pré-login como ``/auth/login``), este helper não
    deve ser usado: chamada explícita sem context.

    Args:
        session: sessão async já aberta (do sessionmaker).
        tenant_id: UUID do tenant cujo escopo deve ativar RLS.

    Raises:
        ValueError: se ``tenant_id`` for ``None`` (anti-bypass).
    """
    if tenant_id is None:
        raise ValueError(
            "with_tenant_context requer tenant_id não-nulo — "
            "rotas pré-login não devem usar este helper"
        )

    async with session.begin():
        await session.execute(
            text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)}
        )
        yield session
        # commit/rollback automático pelo session.begin()


async def reset_engine() -> None:
    """Descarta engine + sessionmaker (uso em testes de integração).

    Tests integration (chunk 4+) precisam recriar o engine por test container
    OR por test database. Esta função zera o singleton para que ``get_engine``
    crie nova instância no próximo call.
    """
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None


__all__ = [
    "DatabaseConfigError",
    "get_engine",
    "get_sessionmaker",
    "with_tenant_context",
    "reset_engine",
]
