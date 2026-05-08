"""DPA (Data Processing Agreement) flow — Sprint 04 SP04-AUTH-01 AC-06.

ADR-019 (level=spec) define schema ``dpa_acceptances`` + protocolo versioning
semver + retention permanente como evidence ANPD-defensible. Este módulo
implementa:

1. Endpoints REST:
   - GET  /api/tenant/dpa/text/{version}  (público — escritório lê antes de aceitar)
   - POST /api/tenant/dpa/accept          (auth — registra aceitação)
   - GET  /api/tenant/dpa/status          (auth — lista aceitações do tenant)

2. Helpers públicos (reuso por ``onboarding.py``):
   - ``compute_dpa_hash(text)``: SHA-256 hex de texto NFC-normalized
   - ``get_dpa_text(version)``: leitura cached do texto canônico do filesystem
   - ``accept_dpa(...)``: persistência transaction-aware (chamável dentro de
     ``complete_onboarding`` no triple insert atômico)

Cross-references:
    governance/stories/sp04-auth-01-multi-tenant-auth.md AC-06
    governance/architecture/adr/adr-019-dpa-storage-schema.md (canonical)
    governance/legal/dpa-templates/v1.0.0.md (texto canônico atual)
"""

from __future__ import annotations

import hashlib
import os
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path as FastAPIPath, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bloco_audit.chain import append_audit_entry
from bloco_auth.db import get_sessionmaker, with_tenant_context
from bloco_auth.middleware import get_current_user
from bloco_auth.models import DpaAcceptance


router = APIRouter(prefix="/api/tenant/dpa", tags=["dpa"])


# ──────────────────────────────────────────────────────────────────────────────
# Constants & validation
# ──────────────────────────────────────────────────────────────────────────────

_DEFAULT_DPA_DIR = "governance/legal/dpa-templates"
_CACHE_TTL_SECONDS = 300  # 5min — DPA texto raramente muda
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


# ──────────────────────────────────────────────────────────────────────────────
# Cache TTL manual (filesystem read reduction)
# ──────────────────────────────────────────────────────────────────────────────

# {version: (text, expires_at_unix)}
_DPA_TEXT_CACHE: dict[str, tuple[str, float]] = {}


def clear_dpa_cache() -> None:
    """Limpa cache filesystem de textos DPA (uso em tests)."""
    _DPA_TEXT_CACHE.clear()


def get_dpa_dir() -> Path:
    """Resolve diretório de templates DPA (env override OR default).

    Default: ``governance/legal/dpa-templates`` relativo ao CWD do processo
    (que é a raiz do projeto quando rodando uvicorn/pytest).
    """
    env_dir = os.getenv("DPA_TEMPLATES_DIR")
    return Path(env_dir) if env_dir else Path(_DEFAULT_DPA_DIR)


def get_dpa_text(version: str) -> str:
    """Lê texto canônico ``{version}.md`` com cache TTL 5min.

    Args:
        version: semver da DPA (ex.: "1.0.0").

    Returns:
        Conteúdo bruto do arquivo (frontmatter + body Markdown).

    Raises:
        FileNotFoundError: se ``{version}.md`` não existe em ``DPA_TEMPLATES_DIR``.
        ValueError: se ``version`` não bate com regex semver (anti path-traversal).
    """
    if not _SEMVER_RE.match(version):
        raise ValueError(
            f"DPA version inválida: {version!r} — deve seguir semver MAJOR.MINOR.PATCH "
            "(anti path-traversal)"
        )

    now = time.time()
    cached = _DPA_TEXT_CACHE.get(version)
    if cached is not None and cached[1] > now:
        return cached[0]

    dpa_path = get_dpa_dir() / f"v{version}.md"
    if not dpa_path.is_file():
        raise FileNotFoundError(
            f"DPA versão {version} não encontrada em {dpa_path}. "
            "Texto canônico deve existir antes de aceite."
        )
    text = dpa_path.read_text(encoding="utf-8")
    _DPA_TEXT_CACHE[version] = (text, now + _CACHE_TTL_SECONDS)
    return text


def compute_dpa_hash(text: str) -> str:
    """SHA-256 hex de texto NFC-normalized (consistência cross-OS).

    Razão NFC: Mac usa NFD (decomposed) em filesystem; Linux usa NFC
    (composed). Mesmo texto pode ter bytes diferentes em disco. NFC garante
    hash idêntico independente de origem do filesystem.

    Args:
        text: conteúdo do DPA (frontmatter + body).

    Returns:
        Hash SHA-256 hex (64 chars).
    """
    normalized = unicodedata.normalize("NFC", text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schemas (request/response)
# ──────────────────────────────────────────────────────────────────────────────


class DpaTextResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    text: str
    hash: str  # SHA-256 hex do texto NFC-normalized


class DpaAcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dpa_version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    accepted: bool


class DpaAcceptResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    acceptance_id: UUID
    dpa_version: str
    dpa_text_hash: str
    accepted_at: datetime


class DpaAcceptanceItem(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    dpa_version: str
    dpa_text_hash: str
    accepted_at: datetime


# ──────────────────────────────────────────────────────────────────────────────
# Internal helper — accept_dpa (transaction-aware)
# ──────────────────────────────────────────────────────────────────────────────


async def accept_dpa(
    *,
    tenant_id: UUID,
    user_id: UUID,
    version: str,
    request: Request | None,
    db_session: AsyncSession,
) -> DpaAcceptance:
    """Persiste aceitação DPA. **Idempotent** — UNIQUE(tenant_id, version) violation
    retorna acceptance existente sem erro.

    Aceita ``db_session`` externa para participar de transactions maiores
    (ex.: ``complete_onboarding`` triple insert atômico).

    Args:
        tenant_id: UUID do tenant que está aceitando.
        user_id: UUID do user que clicou em "aceito" (do JWT OR onboarding).
        version: semver da DPA aceita.
        request: FastAPI Request (para IP + user_agent capture). Se ``None``,
            campos ficam null (caso de aceite em background sem HTTP context).
        db_session: AsyncSession SQLAlchemy.

    Returns:
        ``DpaAcceptance`` recém-criada ou existente.

    Raises:
        FileNotFoundError: version não existe em filesystem.
        ValueError: version não bate semver.
    """
    text = get_dpa_text(version)  # raise se não existe
    text_hash = compute_dpa_hash(text)

    ip_address = None
    user_agent = None
    if request is not None:
        if request.client is not None:
            ip_address = request.client.host
        user_agent = request.headers.get("user-agent")

    # Idempotency: pré-lookup
    result = await db_session.execute(
        select(DpaAcceptance).where(
            DpaAcceptance.tenant_id == tenant_id,
            DpaAcceptance.dpa_version == version,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    acceptance = DpaAcceptance(
        tenant_id=tenant_id,
        dpa_version=version,
        dpa_text_hash=text_hash,
        accepted_at=datetime.now(timezone.utc),
        accepted_by_user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db_session.add(acceptance)
    try:
        await db_session.flush()
    except IntegrityError:
        # Race condition: outro request inseriu entre lookup e flush
        # Retornar existing (idempotency)
        await db_session.rollback()
        result = await db_session.execute(
            select(DpaAcceptance).where(
                DpaAcceptance.tenant_id == tenant_id,
                DpaAcceptance.dpa_version == version,
            )
        )
        return result.scalar_one()
    await db_session.refresh(acceptance)
    return acceptance


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/text/{version}", response_model=DpaTextResponse)
async def get_dpa_text_endpoint(
    version: Annotated[str, FastAPIPath(pattern=r"^\d+\.\d+\.\d+$")],
) -> DpaTextResponse:
    """Retorna texto canônico DPA + hash. **SEM auth** (info pública por desenho).

    Escritório lê texto antes de criar conta. Hash retornado permite client
    validar consistência (defesa-em-profundidade — server side computa
    novamente em /accept).
    """
    try:
        text = get_dpa_text(version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return DpaTextResponse(version=version, text=text, hash=compute_dpa_hash(text))


@router.post(
    "/accept",
    response_model=DpaAcceptResponse,
    status_code=status.HTTP_201_CREATED,
)
async def accept_dpa_endpoint(
    data: DpaAcceptRequest,
    request: Request,
    current: tuple[UUID, UUID] = Depends(get_current_user),
) -> DpaAcceptResponse:
    """Persiste aceitação DPA. **Idempotent** (segundo accept retorna existente)."""
    if not data.accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DPA deve ser aceita explicitamente (accepted=True)",
        )

    tenant_id, user_id = current
    sessionmaker = get_sessionmaker()
    try:
        async with sessionmaker() as session, with_tenant_context(session, tenant_id):
            acceptance = await accept_dpa(
                tenant_id=tenant_id,
                user_id=user_id,
                version=data.dpa_version,
                request=request,
                db_session=session,
            )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    # Audit chain — best-effort (CC.39 hardening)
    try:
        append_audit_entry(
            "dpa_accepted",
            {
                "tenant_id": str(tenant_id),
                "user_id": str(user_id),
                "dpa_version": data.dpa_version,
                "dpa_text_hash": acceptance.dpa_text_hash,
            },
        )
    except Exception:  # noqa: BLE001
        pass

    return DpaAcceptResponse(
        acceptance_id=acceptance.id,
        dpa_version=acceptance.dpa_version,
        dpa_text_hash=acceptance.dpa_text_hash,
        accepted_at=acceptance.accepted_at,
    )


@router.get("/status", response_model=list[DpaAcceptanceItem])
async def get_dpa_status(
    current: tuple[UUID, UUID] = Depends(get_current_user),
) -> list[DpaAcceptanceItem]:
    """Lista aceitações DPA do tenant atual (RLS auto-filtra), sorted desc."""
    tenant_id, _ = current
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session, with_tenant_context(session, tenant_id):
        result = await session.execute(
            select(DpaAcceptance).order_by(DpaAcceptance.accepted_at.desc())
        )
        items = result.scalars().all()
        return [DpaAcceptanceItem.model_validate(item) for item in items]


__all__ = [
    "router",
    "compute_dpa_hash",
    "get_dpa_text",
    "get_dpa_dir",
    "clear_dpa_cache",
    "accept_dpa",
]
