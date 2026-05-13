"""Unit tests — Sprint 5+ Bloco 3 TD-SP04-S4-V1 Imobiliário Wireframe Variant.

Cobre `bloco_contratos/imobiliario_schema.py` (Pydantic + field validators).

REUSE pattern Bloco 2: tests/unit/test_analytics.py
    • Pydantic strict extra='forbid' rejection
    • Field validators regex/bounds
    • parametrize edge cases
    • F-SMITH-RV-L1 alignment regex regional fixtures (SP/RJ/MG/BA)

Smith F-SMITH-RV-L1 (LOW) addressed via fixtures regional variance:
    fixtures format SP padrão (1-2.3.3.2.1-4 dígitos) testado;
    RJ/MG/BA TODO Sprint 6+ se regional adaptive necessário empíricamente.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from bloco_contratos.imobiliario_schema import ImobiliarioContractDataIn


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def valid_imobiliario_kwargs():
    """Baseline valid Imobiliário contract data (SP padrão format)."""
    return {
        "matricula_rgi": "1.234.567.89.0001",
        "valor_avaliacao": Decimal("350000.00"),
        "tipo_garantia": "alienacao_fiduciaria",
        "indice_correcao": "tr",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Smith C1 — Pydantic strict mode extra='forbid'
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_imobiliario_pydantic_extra_forbid_rejects_unknown(valid_imobiliario_kwargs):
    """AC-6 — Pydantic REJEITA campos não-declarados (Smith C1 pattern Bloco 2 reuse)."""
    with pytest.raises(ValidationError, match="extra"):
        ImobiliarioContractDataIn(
            **valid_imobiliario_kwargs,
            tenant_id=uuid4(),  # type: ignore[call-arg]
        )


@pytest.mark.unit
def test_imobiliario_pydantic_minimal_valid(valid_imobiliario_kwargs):
    """Construção válida sem optional fields (analysis_id=None)."""
    data = ImobiliarioContractDataIn(**valid_imobiliario_kwargs)
    assert data.matricula_rgi == "1.234.567.89.0001"
    assert data.valor_avaliacao == Decimal("350000.00")
    assert data.tipo_garantia == "alienacao_fiduciaria"
    assert data.indice_correcao == "tr"
    assert data.analysis_id is None


# ──────────────────────────────────────────────────────────────────────────────
# Matrícula RGI regex validation (F-SMITH-RV-L1 awareness regional)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.parametrize("matricula_valid", [
    "1.234.567.89.0001",     # SP padrão (cartório 1 dígito)
    "12.345.678.90.0001",    # SP cartório 2 dígitos
    "1.234.567.89.1",        # Sub-fração 1 dígito
    "9.999.999.99.9999",     # Boundary upper
])
def test_imobiliario_matricula_rgi_format_valid(valid_imobiliario_kwargs, matricula_valid):
    """AC-2 — matrícula RGI format X.XXX.XXX.XX.XXXX validation passa."""
    kwargs = {**valid_imobiliario_kwargs, "matricula_rgi": matricula_valid}
    data = ImobiliarioContractDataIn(**kwargs)
    assert data.matricula_rgi == matricula_valid


@pytest.mark.unit
@pytest.mark.parametrize("matricula_invalid", [
    "",                       # Empty
    "1234567",                # No dots
    "1.234.567.89",           # Missing sub-fração
    "abc.def.ghi.jk.lmno",    # Non-numeric
    "1.23.567.89.0001",       # Livro 2 dígitos (deveria 3)
    "100.234.567.89.0001",    # Cartório 3 dígitos (deveria 1-2)
])
def test_imobiliario_matricula_rgi_format_invalid(valid_imobiliario_kwargs, matricula_invalid):
    """AC-2 — matrícula RGI format inválido raises ValidationError."""
    kwargs = {**valid_imobiliario_kwargs, "matricula_rgi": matricula_invalid}
    with pytest.raises(ValidationError):
        ImobiliarioContractDataIn(**kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# Valor avaliação bounds validation
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.parametrize("valor_valid", [
    Decimal("0.00"),
    Decimal("1.50"),
    Decimal("350000.00"),
    Decimal("1000000.00"),
    Decimal("100000000.00"),  # Boundary upper
])
def test_imobiliario_valor_avaliacao_bounds_valid(valid_imobiliario_kwargs, valor_valid):
    """AC-3 — valor avaliação bounds 0 a R$ 100M passa."""
    kwargs = {**valid_imobiliario_kwargs, "valor_avaliacao": valor_valid}
    data = ImobiliarioContractDataIn(**kwargs)
    assert data.valor_avaliacao == valor_valid


@pytest.mark.unit
@pytest.mark.parametrize("valor_invalid", [
    Decimal("-0.01"),         # Negative
    Decimal("100000000.01"),  # Just over R$ 100M
    Decimal("999999999.99"),  # Way over
])
def test_imobiliario_valor_avaliacao_bounds_invalid(valid_imobiliario_kwargs, valor_invalid):
    """AC-3 — valor avaliação fora de bounds raises ValidationError."""
    kwargs = {**valid_imobiliario_kwargs, "valor_avaliacao": valor_invalid}
    with pytest.raises(ValidationError):
        ImobiliarioContractDataIn(**kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# Tipo garantia enum validation (AC-4)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.parametrize("garantia", ["alienacao_fiduciaria", "hipoteca"])
def test_imobiliario_tipo_garantia_valid(valid_imobiliario_kwargs, garantia):
    """AC-4 — 2 valores enum aceitos (Lei 9.514/97 + CC Art. 1.473)."""
    kwargs = {**valid_imobiliario_kwargs, "tipo_garantia": garantia}
    data = ImobiliarioContractDataIn(**kwargs)
    assert data.tipo_garantia == garantia


@pytest.mark.unit
def test_imobiliario_tipo_garantia_invalid(valid_imobiliario_kwargs):
    """AC-4 — Garantia fora enum rejeita."""
    kwargs = {**valid_imobiliario_kwargs, "tipo_garantia": "penhor"}
    with pytest.raises(ValidationError):
        ImobiliarioContractDataIn(**kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# Índice correção enum validation (AC-5)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.parametrize("indice", ["tr", "ipca", "igpm", "pre"])
def test_imobiliario_indice_correcao_valid(valid_imobiliario_kwargs, indice):
    """AC-5 — 4 valores enum aceitos (SFH TR + SFI livre)."""
    kwargs = {**valid_imobiliario_kwargs, "indice_correcao": indice}
    data = ImobiliarioContractDataIn(**kwargs)
    assert data.indice_correcao == indice


@pytest.mark.unit
def test_imobiliario_indice_correcao_invalid(valid_imobiliario_kwargs):
    """AC-5 — Índice fora enum rejeita."""
    kwargs = {**valid_imobiliario_kwargs, "indice_correcao": "selic"}
    with pytest.raises(ValidationError):
        ImobiliarioContractDataIn(**kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# Optional analysis_id field (FK contracts Sprint 06+ when migrated)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_imobiliario_analysis_id_optional(valid_imobiliario_kwargs):
    """analysis_id é optional (FK contracts table not yet migrated Sprint 06+)."""
    analysis_id = uuid4()
    kwargs = {**valid_imobiliario_kwargs, "analysis_id": analysis_id}
    data = ImobiliarioContractDataIn(**kwargs)
    assert data.analysis_id == analysis_id


# ──────────────────────────────────────────────────────────────────────────────
# Integration: full valid data structure
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_imobiliario_full_valid_alienacao_tr_combination(valid_imobiliario_kwargs):
    """Cenário típico SFH: alienação fiduciária + TR + R$ 350k."""
    data = ImobiliarioContractDataIn(**valid_imobiliario_kwargs)
    assert data.tipo_garantia == "alienacao_fiduciaria"
    assert data.indice_correcao == "tr"
    assert data.valor_avaliacao == Decimal("350000.00")


@pytest.mark.unit
def test_imobiliario_full_valid_hipoteca_ipca_combination():
    """Cenário SFI: hipoteca + IPCA + valor alto."""
    data = ImobiliarioContractDataIn(
        matricula_rgi="5.678.901.23.4567",
        valor_avaliacao=Decimal("2500000.00"),
        tipo_garantia="hipoteca",
        indice_correcao="ipca",
    )
    assert data.tipo_garantia == "hipoteca"
    assert data.indice_correcao == "ipca"
    assert data.valor_avaliacao == Decimal("2500000.00")
