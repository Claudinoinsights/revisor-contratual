"""Imobiliário contract data schema — Sprint 5+ Bloco 3 TD-SP04-S4-V1.

Pydantic schema strict (extra='forbid') + FastAPI router para wireframe variant
Imobiliário SFH/SFI per Sati Eixo 4 NEEDS CHANGES pull-forward Sprint 5+.

4 campos específicos (Sati ratify + TECH-DEBT linha 929):
    • matricula_rgi   — formato X.XXX.XXX.XX.XXXX (regional variance Sprint 6+)
    • valor_avaliacao — Decimal R$ ≥0 ≤R$ 100M sanity bound
    • tipo_garantia   — enum alienacao_fiduciaria | hipoteca
    • indice_correcao — enum tr | ipca | igpm | pre

REUSE empirical Bloco 2 pattern (bloco_auth/analytics.py):
    • Pydantic ConfigDict(extra='forbid') strict
    • Field validators regex/bounds
    • Router /api/contracts/imobiliario POST com Depends(get_current_user)
    • with_tenant_context RLS per ADR-017

F-SMITH-RV-L1 (LOW) addressed: # TODO regex regional Sprint 6+ adaptive SP/RJ/MG/BA.

Cross-references:
    governance/stories/TD-SP04-S4-V1-IMOBILIARIO-WIREFRAME-VARIANT.md (13 ACs)
    governance/design/wireframe-variant-imobiliario-2026-05-13.md (Sati spec)
    bloco_database/migrations/sp06_001_imobiliario_contract_data.sql (schema)
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from bloco_auth.db import get_sessionmaker, with_tenant_context
from bloco_auth.middleware import get_current_user

router = APIRouter(prefix="/api/contracts/imobiliario", tags=["imobiliario"])


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

# Matrícula RGI regex format: X.XXX.XXX.XX.XXXX (cartório.livro.folha.X.Y)
# TODO regex regional Sprint 6+ adaptive (R-06 LOW Sprint 6+ — F-SMITH-RV-L1)
# Atual: 1-2 dígitos.3.3.2.1-4 dígitos (SP padrão; RJ/MG/BA podem variar)
_MATRICULA_RGI_REGEX = re.compile(r"^\d{1,2}\.\d{3}\.\d{3}\.\d{2}\.\d{1,4}$")

# Valor avaliação bounds (R$ 0,00 a R$ 100M — R-07 LOW Sprint 6+ override commercial)
_VALOR_MIN = Decimal("0.00")
_VALOR_MAX = Decimal("100000000.00")  # R$ 100 milhões


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic models — Smith C1 pattern strict extra='forbid' (Bloco 2 reuse)
# ──────────────────────────────────────────────────────────────────────────────


class ImobiliarioContractDataIn(BaseModel):
    """Imobiliário contract data input schema — wireframe variant 4 fields.

    Smith C1 pattern: extra='forbid' rejeita campos não-declarados (defense-in-depth).
    """

    model_config = ConfigDict(extra="forbid")

    matricula_rgi: str = Field(..., min_length=1, max_length=40)
    valor_avaliacao: Decimal = Field(..., decimal_places=2)
    tipo_garantia: Literal["alienacao_fiduciaria", "hipoteca"]
    indice_correcao: Literal["tr", "ipca", "igpm", "pre"]
    analysis_id: UUID | None = None  # FK contracts (Sprint 06+ when migrated)

    @field_validator("matricula_rgi")
    @classmethod
    def validate_matricula_rgi(cls, v: str) -> str:
        """Format X.XXX.XXX.XX.XXXX validation (regional variance R-06 LOW Sprint 6+)."""
        if not _MATRICULA_RGI_REGEX.match(v):
            raise ValueError(
                "Formato inválido. Use cartório.livro.folha.X.Y "
                "(ex: 1.234.567.89.0001)"
            )
        return v

    @field_validator("valor_avaliacao")
    @classmethod
    def validate_valor_avaliacao(cls, v: Decimal) -> Decimal:
        """Bounds R$ 0,00 a R$ 100M (R-07 LOW catalogged commercial override Sprint 6+)."""
        if v < _VALOR_MIN:
            raise ValueError("Valor deve ser maior ou igual a zero")
        if v > _VALOR_MAX:
            raise ValueError(
                f"Valor excede limite (R$ {_VALOR_MAX:,.2f}). "
                "Verifique a unidade (real, não centavos)."
            )
        return v


class ImobiliarioContractDataOut(BaseModel):
    """Imobiliário contract data response after INSERT success."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    matricula_rgi: str
    valor_avaliacao: Decimal
    tipo_garantia: str
    indice_correcao: str
    analysis_id: UUID | None
    created_at: str  # ISO format datetime


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/contracts/imobiliario — store Imobiliário contract data (AC-6)
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/", response_model=ImobiliarioContractDataOut, status_code=status.HTTP_201_CREATED)
async def create_imobiliario_contract(
    data: ImobiliarioContractDataIn,
    current: tuple[UUID, UUID] = Depends(get_current_user),
) -> ImobiliarioContractDataOut:
    """Persist Imobiliário contract data — multi-tenant RLS scoped.

    Smith C1: tenant_id derivado server-side de JWT (NÃO do payload — extra='forbid').
    ADR-017 §2: with_tenant_context aplica `SET LOCAL app.tenant_id` (RLS policy auto-filters).
    """
    tenant_id, _user_id = current
    sessionmaker = get_sessionmaker()

    try:
        async with sessionmaker() as session, with_tenant_context(session, tenant_id):
            result = await session.execute(
                text(
                    """
                    INSERT INTO imobiliario_contract_data (
                        tenant_id, analysis_id, matricula_rgi, valor_avaliacao,
                        tipo_garantia, indice_correcao
                    ) VALUES (
                        :tenant_id, :analysis_id, :matricula_rgi, :valor_avaliacao,
                        :tipo_garantia, :indice_correcao
                    )
                    RETURNING id, created_at
                    """
                ),
                {
                    "tenant_id": str(tenant_id),
                    "analysis_id": str(data.analysis_id) if data.analysis_id else None,
                    "matricula_rgi": data.matricula_rgi,
                    "valor_avaliacao": data.valor_avaliacao,
                    "tipo_garantia": data.tipo_garantia,
                    "indice_correcao": data.indice_correcao,
                },
            )
            row = result.first()
            if row is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="INSERT retornou sem ID",
                )

            return ImobiliarioContractDataOut(
                id=row[0],
                tenant_id=tenant_id,
                matricula_rgi=data.matricula_rgi,
                valor_avaliacao=data.valor_avaliacao,
                tipo_garantia=data.tipo_garantia,
                indice_correcao=data.indice_correcao,
                analysis_id=data.analysis_id,
                created_at=row[1].isoformat(),
            )

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao persistir Imobiliário contract data: {exc}",
        ) from exc


__all__ = [
    "router",
    "ImobiliarioContractDataIn",
    "ImobiliarioContractDataOut",
]
