"""Testes unitários do bloco_workflow/personas/juiz.py.

Cobertura: 3 vereditos canônicos (APROVADO_100/HITL/REJEITADO) + 3 checagens isoladas
+ hard-fails FR-CALC-01 + reprodutibilidade FR-JUIZ-01.

NFR-MAINT-02: ≥70% em bloco_workflow.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from bloco_contratos import BacenData, TeseAdvogado
from bloco_contratos.personas import FundamentoInvocado
from bloco_workflow.personas import juiz_revisar
from bloco_workflow.personas.juiz import (
    _check_c1_divergencia_bacen,
    _check_c2_peso_vinculante,
    _check_c3_jurisdicao,
    _classificar_veredito,
)

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures auxiliares
# ──────────────────────────────────────────────────────────────────────────────


def _bacen(taxa_media: str = "0.5") -> BacenData:
    """BacenData mínimo. taxa_media em mesma unidade que taxa_contratual_aa_decimal (decimal)."""
    return BacenData(
        codigo_sgs=25471,
        modalidade="CDC_VEICULOS_PF",
        mes_ref="2024-03",
        taxa_media=taxa_media,
        fonte_url="https://api.bcb.gov.br/dados/serie/bcdata.sgs.25471/dados",
        fetched_at=datetime.now(timezone.utc),
    )


def _fundamento(
    id_doc: str = "STJ-S539",
    peso: int = 4,
    court_id: str = "STJ",
) -> FundamentoInvocado:
    return FundamentoInvocado(
        id_doc=id_doc,
        citacao_textual="É permitida a capitalização infra-anual em SFN com pactuação expressa...",
        peso_vinculacao=peso,
        court_id=court_id,
    )


def _tese(fundamentos: list[FundamentoInvocado] | None = None) -> TeseAdvogado:
    funds = fundamentos if fundamentos is not None else [_fundamento()]
    docs_ids = [f.id_doc for f in funds]
    return TeseAdvogado(
        tese_principal=("Argumento revisional fundamentado em Súmula 539 STJ. " * 2).strip(),
        fundamentos_invocados=funds,
        docs_consultados_ids=docs_ids + ["STF-SV4", "TJBA-A100"],
        docs_efetivamente_citados_ids=docs_ids,
        confianca=0.85,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Veredito APROVADO_100 — todos os 3 checks PASS
# ──────────────────────────────────────────────────────────────────────────────


def test_aprovado_100_todos_checks_pass():
    """C1 PASS (divergência ≥0.5pp) + C2 PASS (peso=4 STJ Tema) + C3 PASS (TJBA)."""
    fundamentos = [
        _fundamento(id_doc="STJ-S539", peso=4, court_id="STJ"),
        _fundamento(id_doc="TJBA-A100", peso=1, court_id="TJBA"),
    ]
    v = juiz_revisar(
        taxa_contratual_aa_decimal="2.0",  # vs BACEN 0.5 → divergência 1.5pp ≥ 0.5
        bacen_data=_bacen(taxa_media="0.5"),
        tese=_tese(fundamentos),
        uf_contrato="BA",
    )
    assert v.veredito == "APROVADO_100"
    assert v.aderencia == 100.0
    assert v.c1_score == 1.0
    assert v.c2_score == 1.0
    assert v.c3_score == 1.0


# ──────────────────────────────────────────────────────────────────────────────
# Veredito APROVADO_COM_RISCO_HITL — 70 ≤ aderência < 100
# ──────────────────────────────────────────────────────────────────────────────


def test_hitl_quando_c2_falha_parcial():
    """C1 PASS + C2 PARCIAL (peso=2 → 0.5) + C3 PASS → aderência ≈83.3%."""
    fundamentos = [
        _fundamento(id_doc="STJ-A1", peso=2, court_id="STJ"),  # peso baixo
    ]
    v = juiz_revisar(
        taxa_contratual_aa_decimal="2.0",
        bacen_data=_bacen(taxa_media="0.5"),
        tese=_tese(fundamentos),
        uf_contrato="BA",
    )
    assert v.veredito == "APROVADO_COM_RISCO_HITL"
    assert 70.0 <= v.aderencia < 100.0
    assert v.c2_score == 0.5  # 2/4


def test_hitl_quando_c1_parcial_outros_pass():
    """C1 PARCIAL (divergência 0.25pp → 0.5) + C2 PASS + C3 PASS → aderência ≈83.3%."""
    v = juiz_revisar(
        taxa_contratual_aa_decimal="0.75",  # vs BACEN 0.5 → divergência 0.25pp
        bacen_data=_bacen(taxa_media="0.5"),
        tese=_tese([_fundamento(peso=4, court_id="STJ")]),
        uf_contrato="BA",
    )
    assert v.veredito == "APROVADO_COM_RISCO_HITL"
    assert v.c1_score == 0.5


# ──────────────────────────────────────────────────────────────────────────────
# Veredito REJEITADO — aderência < 70
# ──────────────────────────────────────────────────────────────────────────────


def test_rejeitado_quando_c3_falha():
    """C1 PASS + C2 PASS + C3 FAIL (sem TJ/STJ/STF) → aderência ≈66.7% (REJEITADO)."""
    fundamentos = [
        _fundamento(id_doc="TJSP-A99", peso=4, court_id="TJSP"),  # SP, contrato é BA
    ]
    v = juiz_revisar(
        taxa_contratual_aa_decimal="2.0",
        bacen_data=_bacen(taxa_media="0.5"),
        tese=_tese(fundamentos),
        uf_contrato="BA",
    )
    assert v.veredito == "REJEITADO"
    assert v.aderencia < 70.0
    assert v.c3_score == 0.0


def test_rejeitado_quando_dois_checks_falham():
    """C1 FAIL + C2 FAIL + C3 PASS → aderência ≈33.3% (REJEITADO)."""
    fundamentos = [
        _fundamento(id_doc="TJBA-A1", peso=1, court_id="TJBA"),  # peso=1 (TJ)
    ]
    v = juiz_revisar(
        taxa_contratual_aa_decimal="0.5",  # = BACEN, divergência 0
        bacen_data=_bacen(taxa_media="0.5"),
        tese=_tese(fundamentos),
        uf_contrato="BA",
    )
    assert v.veredito == "REJEITADO"
    assert v.aderencia < 70.0


# ──────────────────────────────────────────────────────────────────────────────
# Reprodutibilidade FR-JUIZ-01 — mesma entrada → mesma saída
# ──────────────────────────────────────────────────────────────────────────────


def test_reprodutibilidade_mesmo_input_mesmo_output():
    """Critério auditabilidade jurídica: 1000 execuções DEVEM produzir resultado idêntico."""
    fundamentos = [_fundamento(peso=4, court_id="STJ")]
    bacen = _bacen(taxa_media="0.5")
    tese = _tese(fundamentos)

    resultados = [
        juiz_revisar(
            taxa_contratual_aa_decimal="1.5",
            bacen_data=bacen,
            tese=tese,
            uf_contrato="BA",
        )
        for _ in range(10)
    ]
    primeiro = resultados[0]
    for r in resultados[1:]:
        assert r.aderencia == primeiro.aderencia
        assert r.c1_score == primeiro.c1_score
        assert r.c2_score == primeiro.c2_score
        assert r.c3_score == primeiro.c3_score
        assert r.veredito == primeiro.veredito


# ──────────────────────────────────────────────────────────────────────────────
# Hard-fails FR-CALC-01 (float)
# ──────────────────────────────────────────────────────────────────────────────


def test_juiz_rejeita_float_na_taxa_contratual():
    with pytest.raises(TypeError, match="float é PROIBIDO"):
        juiz_revisar(
            taxa_contratual_aa_decimal=1.5,  # type: ignore[arg-type]
            bacen_data=_bacen(),
            tese=_tese(),
            uf_contrato="BA",
        )


# ──────────────────────────────────────────────────────────────────────────────
# Validação UF
# ──────────────────────────────────────────────────────────────────────────────


def test_juiz_uf_invalido_falha():
    with pytest.raises(ValueError, match="sigla 2 letras"):
        juiz_revisar(
            taxa_contratual_aa_decimal="1.5",
            bacen_data=_bacen(),
            tese=_tese(),
            uf_contrato="BAHIA",  # 5 letras
        )


def test_juiz_uf_lowercase_aceito():
    """C3 deve normalizar UF para uppercase."""
    fundamentos = [_fundamento(id_doc="TJBA-A1", peso=4, court_id="TJBA")]
    v = juiz_revisar(
        taxa_contratual_aa_decimal="1.5",
        bacen_data=_bacen(),
        tese=_tese(fundamentos),
        uf_contrato="ba",  # lowercase
    )
    assert v.c3_score == 1.0


# ──────────────────────────────────────────────────────────────────────────────
# Checagens isoladas (cobertura branch)
# ──────────────────────────────────────────────────────────────────────────────


def test_c1_divergencia_zero_score_zero():
    score, razao = _check_c1_divergencia_bacen("0.5", _bacen(taxa_media="0.5"))
    assert score == Decimal("0.0")
    assert "PARCIAL" in razao or "FAIL" in razao or "0.0000" in razao


def test_c1_divergencia_acima_limiar_score_um():
    score, razao = _check_c1_divergencia_bacen("3.0", _bacen(taxa_media="0.5"))
    assert score == Decimal("1.0")
    assert "PASS" in razao


def test_c1_divergencia_negativa_usa_abs():
    """Taxa contratual < BACEN também é divergência (em módulo)."""
    score, _ = _check_c1_divergencia_bacen("0.0", _bacen(taxa_media="2.0"))
    assert score == Decimal("1.0")  # |-2.0| = 2.0 ≥ 0.5


def test_c2_sem_fundamentos_score_zero():
    """Tese sem fundamentos invocados — model Pydantic exige min_length=1, mas teste de defesa."""
    # Construímos manualmente para bypassar Pydantic e testar comportamento defensivo
    class _MockTese:
        fundamentos_invocados: list = []

    score, razao = _check_c2_peso_vinculante(_MockTese())  # type: ignore[arg-type]
    assert score == Decimal("0.0")
    assert "FAIL" in razao


def test_c2_peso_5_sumula_vinculante_pass():
    score, _ = _check_c2_peso_vinculante(_tese([_fundamento(peso=5, court_id="STF")]))
    assert score == Decimal("1.0")


def test_c2_peso_3_sumula_stj_parcial():
    """peso=3 (Súmula STJ comum, não Tema) → score 0.75 (3/4)."""
    score, _ = _check_c2_peso_vinculante(_tese([_fundamento(peso=3, court_id="STJ")]))
    assert score == Decimal("0.75")


def test_c3_stf_aceito():
    score, _ = _check_c3_jurisdicao(
        _tese([_fundamento(id_doc="STF-SV4", peso=5, court_id="STF")]),
        uf_contrato="BA",
    )
    assert score == Decimal("1.0")


def test_c3_tj_outra_uf_falha():
    """Contrato BA + cita TJSP → C3 FAIL (não atende jurisdição)."""
    score, razao = _check_c3_jurisdicao(
        _tese([_fundamento(id_doc="TJSP-A1", peso=4, court_id="TJSP")]),
        uf_contrato="BA",
    )
    assert score == Decimal("0.0")
    assert "FAIL" in razao


# ──────────────────────────────────────────────────────────────────────────────
# Classificador de veredito (boundary tests)
# ──────────────────────────────────────────────────────────────────────────────


def test_classificar_aderencia_100_aprovado():
    assert _classificar_veredito(Decimal("100.0")) == "APROVADO_100"


def test_classificar_aderencia_99_9_hitl():
    """Boundary: 99.9 < 100 → HITL (não APROVADO_100)."""
    assert _classificar_veredito(Decimal("99.9")) == "APROVADO_COM_RISCO_HITL"


def test_classificar_aderencia_70_exato_hitl():
    """Boundary: 70.0 == limiar → ainda HITL (inclusivo)."""
    assert _classificar_veredito(Decimal("70.0")) == "APROVADO_COM_RISCO_HITL"


def test_classificar_aderencia_69_9_rejeitado():
    """Boundary: 69.9 < 70 → REJEITADO."""
    assert _classificar_veredito(Decimal("69.9")) == "REJEITADO"


def test_classificar_aderencia_zero_rejeitado():
    assert _classificar_veredito(Decimal("0.0")) == "REJEITADO"


# ──────────────────────────────────────────────────────────────────────────────
# Razões devem ser preservadas no veredito (audit log FR-JUIZ-03)
# ──────────────────────────────────────────────────────────────────────────────


def test_veredito_preserva_razoes_textuais_para_audit():
    """razoes deve incluir 1 linha por checagem + linha resumo."""
    v = juiz_revisar(
        taxa_contratual_aa_decimal="2.0",
        bacen_data=_bacen("0.5"),
        tese=_tese([_fundamento(peso=4, court_id="STJ")]),
        uf_contrato="BA",
    )
    assert len(v.razoes) >= 4  # C1, C2, C3, resumo
    assert any("C1" in r for r in v.razoes)
    assert any("C2" in r for r in v.razoes)
    assert any("C3" in r for r in v.razoes)
    assert any("Aderência" in r for r in v.razoes)
