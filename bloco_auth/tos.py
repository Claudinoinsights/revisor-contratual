"""TOS/EULA (Terms of Service) flow — Sprint 04 SP04-LGPD-01 AC-02/AC-04.

Mirror estrutural de ``bloco_auth/dpa.py`` (ADR-019 padrão validado +
Tank Phase 13.3a LIGHT Item 1 — sem desvio).

Diferença material vs DPA:
- TOS declara **operador posture** Eric=operador, escritório=controlador
  (Art. 5º LGPD); DPA descreve **tratamento** dos dados pessoais
- Schema ``tos_acceptances`` é mirror de ``dpa_acceptances`` (ADR-019)
- Texto canônico armazenado em ``governance/legal/tos-templates/{version}.md``

Endpoints REST:
- GET  /api/tenant/tos/text/{version}  (público — escritório lê pré-aceite)
- POST /api/tenant/tos/accept          (auth — registra aceitação)
- GET  /api/tenant/tos/status          (auth — lista aceitações do tenant)

Helpers públicos (reuso por ``onboarding.py`` quintuple insert):
- ``compute_tos_hash(text)``: SHA-256 hex de texto NFC-normalized
- ``get_tos_text(version)``: leitura cached do filesystem (TTL 5min)
- ``accept_tos(...)``: persistência transaction-aware (chamável dentro de
  ``complete_onboarding`` no quintuple insert atômico)

Cross-references:
    governance/stories/sp04-lgpd-01-compliance-flows-operador.md AC-04
    governance/architecture/adr/adr-019-dpa-storage-schema.md (pattern espelhado)
    governance/legal/tos-templates/v1.0.0.md (texto canônico atual)
"""

from __future__ import annotations

import hashlib
import os
import re
import time
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi import Path as FastAPIPath
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bloco_audit.chain import append_audit_entry
from bloco_auth.db import get_sessionmaker, with_tenant_context
from bloco_auth.middleware import get_current_user
from bloco_auth.models import TosAcceptance

router = APIRouter(prefix="/api/tenant/tos", tags=["tos"])


# ──────────────────────────────────────────────────────────────────────────────
# Constants & validation
# ──────────────────────────────────────────────────────────────────────────────

_DEFAULT_TOS_DIR = "governance/legal/tos-templates"
_CACHE_TTL_SECONDS = 300  # 5min — TOS texto raramente muda (mirror dpa.py)
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


# ──────────────────────────────────────────────────────────────────────────────
# Cache TTL manual (filesystem read reduction)
# ──────────────────────────────────────────────────────────────────────────────

# {version: (text, expires_at_unix)}
_TOS_TEXT_CACHE: dict[str, tuple[str, float]] = {}


def clear_tos_cache() -> None:
    """Limpa cache filesystem de textos TOS (uso em tests)."""
    _TOS_TEXT_CACHE.clear()


def get_tos_dir() -> Path:
    """Resolve diretório de templates TOS (env override OR default).

    Default: ``governance/legal/tos-templates`` relativo ao CWD do processo
    (que é a raiz do projeto quando rodando uvicorn/pytest).
    """
    env_dir = os.getenv("TOS_TEMPLATES_DIR")
    return Path(env_dir) if env_dir else Path(_DEFAULT_TOS_DIR)


def get_tos_text(version: str) -> str:
    """Lê texto canônico ``v{version}.md`` com cache TTL 5min.

    Args:
        version: semver do TOS (ex.: "1.0.0").

    Returns:
        Conteúdo bruto do arquivo (frontmatter + body Markdown).

    Raises:
        FileNotFoundError: se ``v{version}.md`` não existe em ``TOS_TEMPLATES_DIR``.
        ValueError: se ``version`` não bate com regex semver (anti path-traversal).
    """
    if not _SEMVER_RE.match(version):
        raise ValueError(
            f"TOS version inválida: {version!r} — deve seguir semver MAJOR.MINOR.PATCH "
            "(anti path-traversal)"
        )

    now = time.time()
    cached = _TOS_TEXT_CACHE.get(version)
    if cached is not None and cached[1] > now:
        return cached[0]

    tos_path = get_tos_dir() / f"v{version}.md"
    if not tos_path.is_file():
        raise FileNotFoundError(
            f"TOS versão {version} não encontrada em {tos_path}. "
            "Texto canônico deve existir antes de aceite."
        )
    text = tos_path.read_text(encoding="utf-8")
    _TOS_TEXT_CACHE[version] = (text, now + _CACHE_TTL_SECONDS)
    return text


def compute_tos_hash(text: str) -> str:
    """SHA-256 hex de texto NFC-normalized (consistência cross-OS).

    Razão NFC: Mac usa NFD (decomposed) em filesystem; Linux usa NFC
    (composed). Mesmo texto pode ter bytes diferentes em disco. NFC garante
    hash idêntico independente de origem do filesystem.

    Args:
        text: conteúdo do TOS (frontmatter + body).

    Returns:
        Hash SHA-256 hex (64 chars).
    """
    normalized = unicodedata.normalize("NFC", text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schemas (request/response)
# ──────────────────────────────────────────────────────────────────────────────


class TosTextResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    text: str
    hash: str  # SHA-256 hex do texto NFC-normalized


class TosAcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tos_version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    accepted: bool


class TosAcceptResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    acceptance_id: UUID
    tos_version: str
    tos_text_hash: str
    accepted_at: datetime


class TosAcceptanceItem(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    tos_version: str
    tos_text_hash: str
    accepted_at: datetime


# ──────────────────────────────────────────────────────────────────────────────
# Internal helper — accept_tos (transaction-aware)
# ──────────────────────────────────────────────────────────────────────────────


async def accept_tos(
    *,
    tenant_id: UUID,
    user_id: UUID,
    version: str,
    request: Request | None,
    db_session: AsyncSession,
) -> TosAcceptance:
    """Persiste aceitação TOS. **Idempotent** — UNIQUE(tenant_id, version)
    violation retorna acceptance existente sem erro.

    Aceita ``db_session`` externa para participar de transactions maiores
    (ex.: ``complete_onboarding`` quintuple insert atômico).

    Args:
        tenant_id: UUID do tenant que está aceitando.
        user_id: UUID do user que clicou em "aceito" (do JWT OR onboarding).
        version: semver do TOS aceito.
        request: FastAPI Request (para IP + user_agent capture). Se ``None``,
            campos ficam null (caso de aceite em background sem HTTP context).
        db_session: AsyncSession SQLAlchemy.

    Returns:
        ``TosAcceptance`` recém-criada ou existente.

    Raises:
        FileNotFoundError: version não existe em filesystem.
        ValueError: version não bate semver.
    """
    text = get_tos_text(version)  # raise se não existe
    text_hash = compute_tos_hash(text)

    ip_address = None
    user_agent = None
    if request is not None:
        if request.client is not None:
            ip_address = request.client.host
        user_agent = request.headers.get("user-agent")

    # Idempotency: pré-lookup
    result = await db_session.execute(
        select(TosAcceptance).where(
            TosAcceptance.tenant_id == tenant_id,
            TosAcceptance.tos_version == version,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    acceptance = TosAcceptance(
        tenant_id=tenant_id,
        tos_version=version,
        tos_text_hash=text_hash,
        accepted_at=datetime.now(UTC),
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
            select(TosAcceptance).where(
                TosAcceptance.tenant_id == tenant_id,
                TosAcceptance.tos_version == version,
            )
        )
        return result.scalar_one()
    await db_session.refresh(acceptance)
    return acceptance


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/text/{version}", response_model=TosTextResponse)
async def get_tos_text_endpoint(
    version: Annotated[str, FastAPIPath(pattern=r"^\d+\.\d+\.\d+$")],
) -> TosTextResponse:
    """Retorna texto canônico TOS + hash. **SEM auth** (info pública por desenho).

    Escritório lê texto antes de criar conta. Hash retornado permite client
    validar consistência (defesa-em-profundidade — server side computa
    novamente em /accept).
    """
    try:
        text = get_tos_text(version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return TosTextResponse(version=version, text=text, hash=compute_tos_hash(text))


@router.post(
    "/accept",
    response_model=TosAcceptResponse,
    status_code=status.HTTP_201_CREATED,
)
async def accept_tos_endpoint(
    data: TosAcceptRequest,
    request: Request,
    current: tuple[UUID, UUID] = Depends(get_current_user),
) -> TosAcceptResponse:
    """Persiste aceitação TOS. **Idempotent** (segundo accept retorna existente)."""
    if not data.accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOS deve ser aceito explicitamente (accepted=True)",
        )

    tenant_id, user_id = current
    sessionmaker = get_sessionmaker()
    try:
        async with sessionmaker() as session, with_tenant_context(session, tenant_id):
            acceptance = await accept_tos(
                tenant_id=tenant_id,
                user_id=user_id,
                version=data.tos_version,
                request=request,
                db_session=session,
            )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    # Audit chain — best-effort (CC.39 hardening pattern dpa.py)
    try:
        append_audit_entry(
            "tos_accepted",
            {
                "tenant_id": str(tenant_id),
                "user_id": str(user_id),
                "tos_version": data.tos_version,
                "tos_text_hash": acceptance.tos_text_hash,
            },
        )
    except Exception:  # noqa: BLE001
        pass

    return TosAcceptResponse(
        acceptance_id=acceptance.id,
        tos_version=acceptance.tos_version,
        tos_text_hash=acceptance.tos_text_hash,
        accepted_at=acceptance.accepted_at,
    )


@router.get("/status", response_model=list[TosAcceptanceItem])
async def get_tos_status(
    current: tuple[UUID, UUID] = Depends(get_current_user),
) -> list[TosAcceptanceItem]:
    """Lista aceitações TOS do tenant atual (RLS auto-filtra), sorted desc."""
    tenant_id, _ = current
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session, with_tenant_context(session, tenant_id):
        result = await session.execute(
            select(TosAcceptance).order_by(TosAcceptance.accepted_at.desc())
        )
        items = result.scalars().all()
        return [TosAcceptanceItem.model_validate(item) for item in items]


__all__ = [
    "router",
    "compute_tos_hash",
    "get_tos_text",
    "get_tos_dir",
    "clear_tos_cache",
    "accept_tos",
]
