"""Testes unitários da classificação jurídica de anatocismo (FR-CALC-03).

Cobre os 4 vereditos canônicos baseados em STF-S121 + STJ-S539 + STJ-T247 + MP-2170.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from bloco_engine.ferramentas_calculo import classificar_anatocismo, sumulas_aplicaveis

# ──────────────────────────────────────────────────────────────────────────────
# SEM_ANATOCISMO — diferença insignificante
# ──────────────────────────────────────────────────────────────────────────────


def test_sem_anatocismo_quando_diferenca_eh_zero():
    """Taxa zero: PMT_price == PMT_simples → sem anatocismo."""
    classif = classificar_anatocismo(
        pmt_price="1000.00",
        pmt_simples="1000.00",
        instituicao_sfn=True,
        pactuacao_expressa=True,
        data_assinatura=date(2024, 3, 15),
    )
    assert classif == "SEM_ANATOCISMO"


def test_sem_anatocismo_quando_diferenca_menor_que_um_centavo():
    """Tolerância R$0.01."""
    classif = classificar_anatocismo(
        pmt_price="1000.005",
        pmt_simples="1000.00",
        instituicao_sfn=True,
        pactuacao_expressa=True,
        data_assinatura=date(2024, 3, 15),
    )
    assert classif == "SEM_ANATOCISMO"


# ──────────────────────────────────────────────────────────────────────────────
# ANATOCISMO_LICITO — SFN + pactuação expressa + pós-MP-2170
# ──────────────────────────────────────────────────────────────────────────────


def test_anatocismo_licito_sfn_pactuacao_pos_mp():
    """Cenário ideal pós-MP 2.170-36: SFN + pactuação clara."""
    classif = classificar_anatocismo(
        pmt_price="1100.00",
        pmt_simples="1000.00",
        instituicao_sfn=True,
        pactuacao_expressa=True,
        data_assinatura=date(2024, 3, 15),
    )
    assert classif == "ANATOCISMO_LICITO"


def test_anatocismo_licito_sumulas_aplicaveis():
    sumulas = sumulas_aplicaveis("ANATOCISMO_LICITO")
    assert "STF-S121" in sumulas
    assert "STJ-S539" in sumulas
    assert "STJ-T247" in sumulas


# ──────────────────────────────────────────────────────────────────────────────
# ANATOCISMO_QUESTIONAVEL — SFN sem pactuação clara → HITL
# ──────────────────────────────────────────────────────────────────────────────


def test_anatocismo_questionavel_sfn_sem_pactuacao():
    """SFN + pós-MP mas SEM pactuação expressa → HITL (advogado decide)."""
    classif = classificar_anatocismo(
        pmt_price="1100.00",
        pmt_simples="1000.00",
        instituicao_sfn=True,
        pactuacao_expressa=False,  # AMBÍGUO
        data_assinatura=date(2024, 3, 15),
    )
    assert classif == "ANATOCISMO_QUESTIONAVEL"


def test_anatocismo_questionavel_sumulas_excluem_stf_s121():
    """QUESTIONAVEL não cita STF-S121 (que é base de ilicitude)."""
    sumulas = sumulas_aplicaveis("ANATOCISMO_QUESTIONAVEL")
    assert "STF-S121" not in sumulas
    assert "STJ-S539" in sumulas


# ──────────────────────────────────────────────────────────────────────────────
# ANATOCISMO_ILICITO — fora SFN OU pré-MP
# ──────────────────────────────────────────────────────────────────────────────


def test_anatocismo_ilicito_fora_sfn():
    """Não-SFN com capitalização infra-anual → ilícito."""
    classif = classificar_anatocismo(
        pmt_price="1100.00",
        pmt_simples="1000.00",
        instituicao_sfn=False,  # FORA SFN
        pactuacao_expressa=True,
        data_assinatura=date(2024, 3, 15),
    )
    assert classif == "ANATOCISMO_ILICITO"


def test_anatocismo_ilicito_pre_mp_2170():
    """Pré-MP 2.170-36 (antes 2001-08-23): capitalização infra-anual era ilícita."""
    classif = classificar_anatocismo(
        pmt_price="1100.00",
        pmt_simples="1000.00",
        instituicao_sfn=True,
        pactuacao_expressa=True,
        data_assinatura=date(1999, 6, 1),  # PRÉ-MP
    )
    assert classif == "ANATOCISMO_ILICITO"


def test_anatocismo_ilicito_marco_temporal_exato_mp_2170():
    """Data exata da MP (2001-08-23) já é considerada pós-MP."""
    classif = classificar_anatocismo(
        pmt_price="1100.00",
        pmt_simples="1000.00",
        instituicao_sfn=True,
        pactuacao_expressa=True,
        data_assinatura=date(2001, 8, 23),  # EXATO marco MP
    )
    assert classif == "ANATOCISMO_LICITO"


def test_anatocismo_ilicito_sumulas_inclui_stf_s121():
    """ILICITO se baseia em Súmula 121 STF (anti-capitalização)."""
    sumulas = sumulas_aplicaveis("ANATOCISMO_ILICITO")
    assert sumulas == ["STF-S121"]


# ──────────────────────────────────────────────────────────────────────────────
# Sem anatocismo — sem súmulas aplicáveis
# ──────────────────────────────────────────────────────────────────────────────


def test_sem_anatocismo_nao_tem_sumulas():
    assert sumulas_aplicaveis("SEM_ANATOCISMO") == []


# ──────────────────────────────────────────────────────────────────────────────
# Hard-fail FR-CALC-01 (float)
# ──────────────────────────────────────────────────────────────────────────────


def test_classificar_rejeita_float_no_pmt_price():
    with pytest.raises(TypeError, match="float é PROIBIDO"):
        classificar_anatocismo(
            pmt_price=1100.00,  # type: ignore[arg-type]
            pmt_simples="1000.00",
            instituicao_sfn=True,
            pactuacao_expressa=True,
            data_assinatura=date(2024, 3, 15),
        )


def test_classificar_rejeita_float_no_pmt_simples():
    with pytest.raises(TypeError, match="float é PROIBIDO"):
        classificar_anatocismo(
            pmt_price="1100.00",
            pmt_simples=1000.00,  # type: ignore[arg-type]
            instituicao_sfn=True,
            pactuacao_expressa=True,
            data_assinatura=date(2024, 3, 15),
        )


# ──────────────────────────────────────────────────────────────────────────────
# Aceita Decimal indistintamente
# ──────────────────────────────────────────────────────────────────────────────


def test_classificar_aceita_decimal():
    classif = classificar_anatocismo(
        pmt_price=Decimal("1100.00"),
        pmt_simples=Decimal("1000.00"),
        instituicao_sfn=True,
        pactuacao_expressa=True,
        data_assinatura=date(2024, 3, 15),
    )
    assert classif == "ANATOCISMO_LICITO"
