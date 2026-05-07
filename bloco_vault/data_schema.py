"""Pydantic schemas para Vault Data Bundling Strategy (ADR-012).

Schemas canônicos para sumulas STJ e súmulas vinculantes STF, com versioning
forward-compatible (`schema_version: "1.0"`) e audit fields (hash_sha256,
fetched_at, fonte_url) para integrity verification.

Reference: governance/architecture/adr/adr-012-vault-data-bundling.md
Story: VAULT-FIX-01 (Sprint 03 Phase 0)
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class SumulaSTJ(BaseModel):
    """Súmula STJ — schema canônico per ADR-012.

    Numero pode incluir revisão: '1', '28-A', '342-revogada'
    """

    numero: str = Field(..., min_length=1, max_length=20)
    texto: str = Field(..., min_length=10)
    data_aprovacao: date | None = None  # algumas súmulas antigas sem data documented
    revogada: bool = False
    area: Literal[
        "civil",
        "penal",
        "processual_civil",
        "processual_penal",
        "tributario",
        "trabalhista",
        "administrativo",
        "outras",
    ] = "outras"
    fonte_url: HttpUrl
    fetched_at: datetime
    hash_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @field_validator("texto")
    @classmethod
    def texto_must_have_content(cls, v: str) -> str:
        """Rejects empty or placeholder texto."""
        if v.strip() == "" or v.strip() == "...":
            raise ValueError("Texto não pode ser vazio ou placeholder")
        return v


class SumulaVinculanteSTF(BaseModel):
    """Súmula Vinculante STF — schema canônico per ADR-012.

    SVs têm numeração simples 1-N (não revisões na mesma forma do STJ).
    """

    numero: int = Field(..., ge=1, le=999)
    texto: str = Field(..., min_length=10)
    data_aprovacao: date | None = None
    revogada: bool = False
    fonte_url: HttpUrl
    fetched_at: datetime
    hash_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @field_validator("texto")
    @classmethod
    def texto_must_have_content(cls, v: str) -> str:
        """Rejects empty or placeholder texto."""
        if v.strip() == "" or v.strip() == "...":
            raise ValueError("Texto não pode ser vazio ou placeholder")
        return v


class VaultDataset(BaseModel):
    """Top-level dataset wrapper — schema versioning + audit fields.

    Schema_version "1.0" prevê forward-compatible migration para Sprint 04+.
    """

    schema_version: Literal["1.0"] = "1.0"
    source: Literal["stj", "stf"]
    last_updated: datetime
    last_refresh_method: Literal["manual_import", "scraper", "seed"] = "seed"
    last_refresh_audit_log: str | None = None  # caminho relativo audit entry
    total_entries: int = Field(..., ge=0)
    entries: list[SumulaSTJ] | list[SumulaVinculanteSTF]

    @model_validator(mode="after")
    def total_must_match_entries(self) -> VaultDataset:
        """Garantia de consistency total_entries == len(entries) (model-level)."""
        if self.total_entries != len(self.entries):
            raise ValueError(
                f"total_entries ({self.total_entries}) deve ser igual a "
                f"len(entries) ({len(self.entries)})"
            )
        return self


__all__ = ["SumulaSTJ", "SumulaVinculanteSTF", "VaultDataset"]
