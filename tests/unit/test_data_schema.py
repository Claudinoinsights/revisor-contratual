"""Testes unit Pydantic schemas bundled (ADR-012 / VAULT-FIX-01 Phase E).

Cobertura:
  - SumulaSTJ valid + invalid (numero, texto, hash_sha256)
  - SumulaVinculanteSTF valid + invalid (numero range)
  - VaultDataset valid + invalid (total_entries match len(entries))
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from bloco_vault.data_schema import SumulaSTJ, SumulaVinculanteSTF, VaultDataset

pytestmark = [pytest.mark.unit]


# ─────────────────────────────────────────────────────────────────────
# Fixtures comuns
# ─────────────────────────────────────────────────────────────────────


_FONTE_STJ = "https://www.stj.jus.br/sumulas/sumula-297"
_FONTE_STF = "https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp?sumula=1217"
_VALID_HASH = "a" * 64  # 64 hex chars matches r"^[a-f0-9]{64}$"


def _now_utc() -> datetime:
    return datetime.now(UTC)


# ─────────────────────────────────────────────────────────────────────
# SumulaSTJ
# ─────────────────────────────────────────────────────────────────────


def test_sumula_stj_valid() -> None:
    """SumulaSTJ com todos os campos válidos passa Pydantic."""
    s = SumulaSTJ(
        numero="297",
        texto="O Código de Defesa do Consumidor é aplicável às instituições financeiras.",
        data_aprovacao=date(2004, 9, 12),
        revogada=False,
        area="civil",
        fonte_url=_FONTE_STJ,  # type: ignore[arg-type]
        fetched_at=_now_utc(),
        hash_sha256=_VALID_HASH,
    )
    assert s.numero == "297"
    assert s.area == "civil"
    assert s.revogada is False


def test_sumula_stj_invalid_numero_empty() -> None:
    """SumulaSTJ numero vazio falha min_length=1."""
    with pytest.raises(ValidationError):
        SumulaSTJ(
            numero="",
            texto="Texto válido com mais de dez chars.",
            fonte_url=_FONTE_STJ,  # type: ignore[arg-type]
            fetched_at=_now_utc(),
        )


def test_sumula_stj_invalid_texto_placeholder() -> None:
    """SumulaSTJ texto que strip() == '...' falha custom validator (após min_length)."""
    # 10+ chars (passa min_length=10) cujo strip() == '...' → custom validator dispara
    with pytest.raises(ValidationError, match="Texto não pode ser vazio ou placeholder"):
        SumulaSTJ(
            numero="297",
            texto="...       ",  # 10 chars: 3 dots + 7 spaces; strip() == "..."
            fonte_url=_FONTE_STJ,  # type: ignore[arg-type]
            fetched_at=_now_utc(),
        )


def test_sumula_stj_invalid_texto_whitespace_only() -> None:
    """SumulaSTJ texto só whitespace (>=10 chars) falha custom validator (vazio após strip)."""
    with pytest.raises(ValidationError, match="Texto não pode ser vazio ou placeholder"):
        SumulaSTJ(
            numero="297",
            texto=" " * 15,  # 15 spaces; strip() == ""
            fonte_url=_FONTE_STJ,  # type: ignore[arg-type]
            fetched_at=_now_utc(),
        )


def test_sumula_stj_invalid_hash_format() -> None:
    """SumulaSTJ hash_sha256 fora do pattern hex falha."""
    with pytest.raises(ValidationError):
        SumulaSTJ(
            numero="297",
            texto="Texto válido com mais de dez chars.",
            fonte_url=_FONTE_STJ,  # type: ignore[arg-type]
            fetched_at=_now_utc(),
            hash_sha256="not-hex-format",
        )


# ─────────────────────────────────────────────────────────────────────
# SumulaVinculanteSTF
# ─────────────────────────────────────────────────────────────────────


def test_sumula_stf_valid() -> None:
    """SumulaVinculanteSTF numero int válido (1 ≤ N ≤ 999) passa."""
    s = SumulaVinculanteSTF(
        numero=7,
        texto="Norma do §3º do art. 192 da Constituição condicionada a lei complementar.",
        data_aprovacao=date(2008, 6, 12),
        revogada=False,
        fonte_url=_FONTE_STF,  # type: ignore[arg-type]
        fetched_at=_now_utc(),
        hash_sha256=_VALID_HASH,
    )
    assert s.numero == 7
    assert s.revogada is False


def test_sumula_stf_invalid_numero_out_of_range() -> None:
    """SumulaVinculanteSTF numero >999 falha le=999."""
    with pytest.raises(ValidationError):
        SumulaVinculanteSTF(
            numero=1000,
            texto="Texto válido com mais de dez chars.",
            fonte_url=_FONTE_STF,  # type: ignore[arg-type]
            fetched_at=_now_utc(),
        )


def test_sumula_stf_invalid_numero_zero() -> None:
    """SumulaVinculanteSTF numero=0 falha ge=1."""
    with pytest.raises(ValidationError):
        SumulaVinculanteSTF(
            numero=0,
            texto="Texto válido com mais de dez chars.",
            fonte_url=_FONTE_STF,  # type: ignore[arg-type]
            fetched_at=_now_utc(),
        )


# ─────────────────────────────────────────────────────────────────────
# VaultDataset
# ─────────────────────────────────────────────────────────────────────


def _make_stj_entry(numero: str = "297") -> SumulaSTJ:
    return SumulaSTJ(
        numero=numero,
        texto="Texto válido com mais de dez chars.",
        fonte_url=_FONTE_STJ,  # type: ignore[arg-type]
        fetched_at=_now_utc(),
    )


def test_vault_dataset_valid() -> None:
    """VaultDataset com total_entries == len(entries) passa."""
    entries = [_make_stj_entry("297"), _make_stj_entry("380")]
    ds = VaultDataset(
        schema_version="1.0",
        source="stj",
        last_updated=_now_utc(),
        last_refresh_method="seed",
        total_entries=2,
        entries=entries,
    )
    assert ds.total_entries == 2
    assert len(ds.entries) == 2
    assert ds.schema_version == "1.0"


def test_vault_dataset_invalid_total_mismatch() -> None:
    """VaultDataset com total_entries != len(entries) falha custom validator."""
    entries = [_make_stj_entry("297")]  # apenas 1 entry
    with pytest.raises(ValidationError, match="total_entries"):
        VaultDataset(
            schema_version="1.0",
            source="stj",
            last_updated=_now_utc(),
            last_refresh_method="seed",
            total_entries=5,  # mismatch — espera 5 mas len(entries)==1
            entries=entries,
        )
