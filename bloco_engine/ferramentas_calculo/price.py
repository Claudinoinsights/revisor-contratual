"""Tabela Price (sistema francês de amortização) com Decimal puro.

FR-CALC-01: Decimal everywhere — float é PROIBIDO (CI lint enforça).
Precisão: getcontext().prec = 28 (igual a NumPy Financial PMT em precisão; superior em determinismo).

Fórmulas:
    PMT_price = PV * (i * (1+i)^n) / ((1+i)^n - 1)         (juros compostos)
    PMT_simples = PV * (1 + i*n) / n                        (juros simples — referência anatocismo)
    aa_to_am: i_am = (1 + i_aa)^(1/12) - 1                  (equivalência composta)

Referências:
  - FR-CALC-01..03 (PRD v1.0.2)
  - ADR-003 (Perito P-INT-01 = Função Python pura, sem LLM)
  - Sumula 121 STF + Sumula 539 STJ + Tema 247 STJ (anatocismo)
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, getcontext
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bloco_contratos import LinhaAmortizacao  # noqa: F401

# Precisão global (FR-CALC-01)
getcontext().prec = 28
PMT_PRECISION: int = 28
"""Precisão Decimal do contexto. NÃO alterar sem revisar todos os cálculos."""

_TWO_DECIMAL = Decimal("0.01")
"""Tolerância R$ 0.01 conforme FR-CALC-02 AC (saldo[n] - amortização[n] = saldo[n+1])."""

_TWELVE = Decimal("12")
_ONE = Decimal("1")
_HUNDRED = Decimal("100")


# ──────────────────────────────────────────────────────────────────────────────
# Conversão de taxas
# ──────────────────────────────────────────────────────────────────────────────


def aa_to_am(taxa_aa: Decimal | str) -> Decimal:
    """Converte taxa anual (% a.a.) em taxa mensal equivalente em juros COMPOSTOS.

    Fórmula: i_am = (1 + i_aa/100)^(1/12) - 1
    Implementação: i_am = exp(ln(1 + i_aa/100) / 12) - 1
    (Decimal não tem ** racional nativo; ln/exp do contexto Decimal são determinísticos.)

    Args:
        taxa_aa: percentual anual (ex: Decimal('24') → 24% a.a.)

    Returns:
        Taxa mensal em forma DECIMAL (não percentual).
        Ex: 24% a.a. → ~0.018087 (≈1.8087% a.m.)
    """
    taxa = _ensure_decimal(taxa_aa) / _HUNDRED
    base = _ONE + taxa
    log_div = base.ln() / _TWELVE
    return log_div.exp() - _ONE


# ──────────────────────────────────────────────────────────────────────────────
# PMT (Tabela Price — juros compostos)
# ──────────────────────────────────────────────────────────────────────────────


def calcular_pmt_price(capital: Decimal | str, taxa_am: Decimal | str, n_parcelas: int) -> Decimal:
    """Calcula a parcela fixa (PMT) da Tabela Price.

    Fórmula: PMT = PV * (i * (1+i)^n) / ((1+i)^n - 1)

    Args:
        capital: valor financiado (PV) — Decimal-as-string aceito
        taxa_am: taxa mensal em forma DECIMAL (ex: 0.018 para 1.8%)
        n_parcelas: número de parcelas (1 ≤ n ≤ 480)

    Returns:
        PMT em Decimal (não-arredondado — cálculo interno preserva precisão).

    Raises:
        ValueError: se n_parcelas < 1, taxa <= -1 (impossível) ou capital <= 0.
    """
    pv = _ensure_decimal(capital)
    i = _ensure_decimal(taxa_am)
    if n_parcelas < 1:
        raise ValueError(f"n_parcelas deve ser >= 1, recebido {n_parcelas}")
    if pv <= 0:
        raise ValueError(f"capital deve ser > 0, recebido {pv}")
    if i <= -_ONE:
        raise ValueError(f"taxa_am inválida (<=-100%): {i}")

    # Caso degenerado: taxa zero → PMT = PV / n
    if i == 0:
        return pv / Decimal(n_parcelas)

    # Fórmula Price padrão
    fator = (_ONE + i) ** n_parcelas
    return pv * (i * fator) / (fator - _ONE)


# ──────────────────────────────────────────────────────────────────────────────
# PMT em juros simples (referência para detectar anatocismo)
# ──────────────────────────────────────────────────────────────────────────────


def calcular_pmt_simples(
    capital: Decimal | str, taxa_am: Decimal | str, n_parcelas: int
) -> Decimal:
    """Calcula a parcela média em regime de JUROS SIMPLES — referência anti-anatocismo.

    Fórmula: PMT_simples = PV * (1 + i*n) / n

    Esta é uma simplificação: em juros simples puros, a parcela varia, mas como
    referência média para comparação com Price, usamos a fórmula consolidada
    (montante final / n parcelas) — consistente com jurisprudência do STJ.
    """
    pv = _ensure_decimal(capital)
    i = _ensure_decimal(taxa_am)
    if n_parcelas < 1:
        raise ValueError(f"n_parcelas deve ser >= 1, recebido {n_parcelas}")
    if pv <= 0:
        raise ValueError(f"capital deve ser > 0, recebido {pv}")

    montante = pv * (_ONE + i * Decimal(n_parcelas))
    return montante / Decimal(n_parcelas)


# ──────────────────────────────────────────────────────────────────────────────
# Tabela de amortização completa (FR-CALC-02)
# ──────────────────────────────────────────────────────────────────────────────


def gerar_tabela_amortizacao(
    capital: Decimal | str,
    taxa_am: Decimal | str,
    n_parcelas: int,
) -> list[dict[str, str]]:
    """Gera tabela de amortização Price com integridade aritmética validada.

    Cada linha: saldo_inicial, juros, amortização, valor_parcela, saldo_final.
    AC FR-CALC-02: saldo[n] - amortização[n] = saldo[n+1] com tolerância R$ 0.01.

    Returns:
        Lista de dicts (Decimal-as-string) prontos para LinhaAmortizacao Pydantic.
    """
    pv = _ensure_decimal(capital)
    i = _ensure_decimal(taxa_am)
    pmt = calcular_pmt_price(pv, i, n_parcelas)

    linhas: list[dict[str, str]] = []
    saldo = pv

    for n in range(1, n_parcelas + 1):
        juros = saldo * i
        amortizacao = pmt - juros
        saldo_final = saldo - amortizacao

        # Última parcela: ajuste para zerar exatamente o saldo (residual de centavos)
        if n == n_parcelas:
            amortizacao = saldo
            saldo_final = Decimal("0")
            # Recalcula valor_parcela para refletir o ajuste
            valor_parcela = juros + amortizacao
        else:
            valor_parcela = pmt

        linhas.append(
            {
                "n_parcela": n,  # type: ignore[dict-item]
                "saldo_inicial": _quantize(saldo),
                "juros": _quantize(juros),
                "amortizacao": _quantize(amortizacao),
                "valor_parcela": _quantize(valor_parcela),
                "saldo_final": _quantize(saldo_final),
            }
        )
        saldo = saldo_final

    # Validação cruzada: integridade aritmética FR-CALC-02 AC
    for linha in linhas:
        si = Decimal(linha["saldo_inicial"])
        am = Decimal(linha["amortizacao"])
        sf = Decimal(linha["saldo_final"])
        if abs(si - am - sf) > _TWO_DECIMAL:
            raise RuntimeError(
                f"Integridade quebrada na parcela {linha['n_parcela']}: "
                f"saldo_inicial({si}) - amortização({am}) != saldo_final({sf}); "
                f"tolerância R$ 0.01 (FR-CALC-02 AC)."
            )

    return linhas


# ──────────────────────────────────────────────────────────────────────────────
# Helpers privados
# ──────────────────────────────────────────────────────────────────────────────


def _ensure_decimal(v: Decimal | str | int) -> Decimal:
    """Aceita Decimal/str/int. NUNCA aceita float (FR-CALC-01)."""
    if isinstance(v, float):
        raise TypeError(
            f"float é PROIBIDO em cálculos jurídicos (FR-CALC-01). "
            f"Use Decimal ou string. Recebido: {v!r}"
        )
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _quantize(v: Decimal) -> str:
    """Arredonda para 2 casas decimais usando ROUND_HALF_EVEN (banker's rounding)."""
    return str(v.quantize(_TWO_DECIMAL, rounding=ROUND_HALF_EVEN))
