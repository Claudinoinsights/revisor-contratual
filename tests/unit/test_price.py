"""Testes unitários do bloco_engine/ferramentas_calculo/price.py.

Cobertura: PMT Price + Simples + Tabela amortização + conversões + hard-fails (FR-CALC-01).
NFR-MAINT-02: ≥80% em bloco_engine.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from bloco_engine.ferramentas_calculo import (
    aa_to_am,
    calcular_pmt_price,
    calcular_pmt_simples,
    gerar_tabela_amortizacao,
)

# ──────────────────────────────────────────────────────────────────────────────
# FR-CALC-01: float é PROIBIDO
# ──────────────────────────────────────────────────────────────────────────────


def test_pmt_price_rejeita_float_no_capital():
    with pytest.raises(TypeError, match="float é PROIBIDO"):
        calcular_pmt_price(50000.00, "0.018", 60)  # type: ignore[arg-type]


def test_pmt_price_rejeita_float_na_taxa():
    with pytest.raises(TypeError, match="float é PROIBIDO"):
        calcular_pmt_price("50000", 0.018, 60)  # type: ignore[arg-type]


def test_pmt_simples_rejeita_float():
    with pytest.raises(TypeError, match="float é PROIBIDO"):
        calcular_pmt_simples(50000.0, "0.018", 60)  # type: ignore[arg-type]


# ──────────────────────────────────────────────────────────────────────────────
# PMT Tabela Price — casos canônicos verificáveis manualmente
# ──────────────────────────────────────────────────────────────────────────────


def test_pmt_price_taxa_zero_eh_pv_dividido_n():
    """Caso degenerado: taxa = 0 → PMT = PV/n (sem juros)."""
    pmt = calcular_pmt_price("12000", "0", 12)
    assert pmt == Decimal("1000")


def test_pmt_price_caso_exemplo_calculojuridico():
    """Exemplo canônico: PV=10000, i=1%a.m., n=12 → PMT ≈ 888.49.

    Verificável em qualquer calculadora financeira. Tolerância R$0.01.
    """
    pmt = calcular_pmt_price("10000", "0.01", 12)
    # Resultado conhecido: 888.4878680409...
    assert abs(pmt - Decimal("888.4878680409")) < Decimal("0.0001")


def test_pmt_price_pv_zero_falha():
    with pytest.raises(ValueError, match="capital deve ser > 0"):
        calcular_pmt_price("0", "0.01", 12)


def test_pmt_price_pv_negativo_falha():
    with pytest.raises(ValueError, match="capital deve ser > 0"):
        calcular_pmt_price("-100", "0.01", 12)


def test_pmt_price_n_parcelas_zero_falha():
    with pytest.raises(ValueError, match="n_parcelas deve ser >= 1"):
        calcular_pmt_price("10000", "0.01", 0)


def test_pmt_price_taxa_menor_que_neg100_falha():
    """Taxa <= -100% é financeiramente impossível."""
    with pytest.raises(ValueError, match="taxa_am inválida"):
        calcular_pmt_price("10000", "-1.5", 12)


def test_pmt_price_aceita_decimal_e_string():
    """Aceita Decimal ou string indistintamente."""
    pmt_str = calcular_pmt_price("10000", "0.01", 12)
    pmt_dec = calcular_pmt_price(Decimal("10000"), Decimal("0.01"), 12)
    assert pmt_str == pmt_dec


# ──────────────────────────────────────────────────────────────────────────────
# PMT Juros Simples — referência anti-anatocismo
# ──────────────────────────────────────────────────────────────────────────────


def test_pmt_simples_caso_canonico():
    """PV=10000, i=1%a.m., n=12 → montante=10000*(1+0.12)=11200; parcela=11200/12 ≈ 933.33."""
    pmt = calcular_pmt_simples("10000", "0.01", 12)
    assert abs(pmt - Decimal("933.3333333333")) < Decimal("0.0001")


def test_pmt_simples_taxa_zero_eh_pv_dividido_n():
    pmt = calcular_pmt_simples("12000", "0", 12)
    assert pmt == Decimal("1000")


def test_pmt_simples_pv_negativo_falha():
    with pytest.raises(ValueError, match="capital deve ser > 0"):
        calcular_pmt_simples("-1", "0.01", 12)


def test_pmt_simples_n_zero_falha():
    with pytest.raises(ValueError, match="n_parcelas deve ser >= 1"):
        calcular_pmt_simples("10000", "0.01", 0)


# ──────────────────────────────────────────────────────────────────────────────
# Conversão aa_to_am via ln/exp (composta)
# ──────────────────────────────────────────────────────────────────────────────


def test_aa_to_am_24_porcento_aa_eh_aproximadamente_1_8087_porcento_am():
    """24% a.a. composto → ~1.8087% a.m. (verificável em qualquer calculadora)."""
    i_am = aa_to_am("24")
    assert abs(i_am - Decimal("0.018087")) < Decimal("0.0001")


def test_aa_to_am_12_porcento_aa_eh_0_9489_porcento_am():
    """12% a.a. composto → ~0.9489% a.m."""
    i_am = aa_to_am("12")
    assert abs(i_am - Decimal("0.009489")) < Decimal("0.0001")


def test_aa_to_am_zero_eh_zero():
    assert aa_to_am("0") == Decimal("0")


def test_aa_to_am_aceita_decimal():
    i_am = aa_to_am(Decimal("24"))
    assert abs(i_am - Decimal("0.018087")) < Decimal("0.0001")


# ──────────────────────────────────────────────────────────────────────────────
# Tabela amortização — integridade aritmética (FR-CALC-02 AC)
# ──────────────────────────────────────────────────────────────────────────────


def test_tabela_amortizacao_n_parcelas_correto():
    tabela = gerar_tabela_amortizacao("10000", "0.01", 12)
    assert len(tabela) == 12


def test_tabela_amortizacao_primeira_e_ultima_parcela():
    tabela = gerar_tabela_amortizacao("10000", "0.01", 12)
    assert tabela[0]["n_parcela"] == 1
    assert tabela[-1]["n_parcela"] == 12
    assert tabela[0]["saldo_inicial"] == "10000.00"
    # Saldo final na última parcela = 0 (zerado pelo ajuste do residual)
    assert Decimal(tabela[-1]["saldo_final"]) == Decimal("0.00")


def test_tabela_amortizacao_integridade_arithmetica():
    """Cada linha: saldo_inicial - amortizacao = saldo_final (tolerância R$0.01)."""
    tabela = gerar_tabela_amortizacao("50000", "0.018", 36)
    for linha in tabela:
        si = Decimal(linha["saldo_inicial"])
        am = Decimal(linha["amortizacao"])
        sf = Decimal(linha["saldo_final"])
        assert abs(si - am - sf) <= Decimal("0.01"), (
            f"Parcela {linha['n_parcela']}: {si} - {am} != {sf}"
        )


def test_tabela_amortizacao_continuidade_saldos():
    """saldo_final[n] == saldo_inicial[n+1] em toda a tabela."""
    tabela = gerar_tabela_amortizacao("50000", "0.018", 36)
    for n in range(len(tabela) - 1):
        assert tabela[n]["saldo_final"] == tabela[n + 1]["saldo_inicial"], (
            f"Quebra de continuidade entre parcela {n + 1} e {n + 2}"
        )


def test_tabela_amortizacao_juros_decrescentes_amortizacao_crescente():
    """Característica Tabela Price: juros caem, amortização sobe ao longo do tempo."""
    tabela = gerar_tabela_amortizacao("50000", "0.02", 24)
    juros = [Decimal(l["juros"]) for l in tabela]
    amortizacoes = [Decimal(l["amortizacao"]) for l in tabela]
    # Em Price, juros são estritamente decrescentes e amortização estritamente crescente
    # (exceto última parcela ajustada para fechar zero)
    for i in range(len(juros) - 2):
        assert juros[i] > juros[i + 1], f"Juros não decrescente na parcela {i + 1}"
        assert amortizacoes[i] < amortizacoes[i + 1], (
            f"Amortização não crescente na parcela {i + 1}"
        )


def test_tabela_amortizacao_taxa_zero_amortiza_uniformemente():
    """Taxa zero: amortização = PV/n em todas as parcelas, juros = 0."""
    tabela = gerar_tabela_amortizacao("12000", "0", 12)
    for linha in tabela:
        assert Decimal(linha["juros"]) == Decimal("0.00")
        assert Decimal(linha["amortizacao"]) == Decimal("1000.00")
