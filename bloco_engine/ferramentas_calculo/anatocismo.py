"""Classificação jurídica de anatocismo (FR-CALC-03).

Baseado em jurisprudência vinculante:
  - STF Súmula 121 (capitalização anual permitida desde 1963)
  - STJ Súmula 539 (capitalização infra-anual permitida em SFN com pactuação expressa)
  - STJ Tema 247 (Repetitivo — limite à capitalização infra-anual em contratos pós-MP 2.170-36/2001)
  - MP 2.170-36/2001 (autoriza capitalização infra-anual em SFN)

4 vereditos canônicos (FR-CALC-03 + Pydantic ClassificacaoAnatocismo):
  - SEM_ANATOCISMO        — diferença Price vs Simples < R$ 0.01 (taxa zero ou n=1)
  - ANATOCISMO_LICITO     — instituição SFN + pactuação expressa + pós-MP 2.170-36/2001
  - ANATOCISMO_QUESTIONAVEL — SFN sem pactuação clara → flagar HITL
  - ANATOCISMO_ILICITO    — fora SFN OU pré-MP sem outra base legal
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

ClassificacaoAnatocismo = Literal[
    "SEM_ANATOCISMO",
    "ANATOCISMO_LICITO",
    "ANATOCISMO_QUESTIONAVEL",
    "ANATOCISMO_ILICITO",
]

# Marco temporal MP 2.170-36 (autoriza capitalização infra-anual em SFN)
_MP_2170_DATA = date(2001, 8, 23)

_TOLERANCIA_SEM_ANATOCISMO = Decimal("0.01")


def classificar_anatocismo(
    pmt_price: Decimal | str,
    pmt_simples: Decimal | str,
    *,
    instituicao_sfn: bool,
    pactuacao_expressa: bool,
    data_assinatura: date,
) -> ClassificacaoAnatocismo:
    """Classifica anatocismo segundo Súmula 121 STF + Súmula 539 STJ + Tema 247 STJ.

    Args:
        pmt_price: parcela calculada em Tabela Price (juros compostos)
        pmt_simples: parcela em juros simples (referência)
        instituicao_sfn: contrato com instituição integrante do Sistema Financeiro Nacional
        pactuacao_expressa: cláusula expressa de capitalização infra-anual no contrato
        data_assinatura: data da assinatura do contrato (relevante para MP 2.170-36/2001)

    Returns:
        Um dos 4 vereditos canônicos.
    """
    p_price = _ensure_decimal(pmt_price)
    p_simples = _ensure_decimal(pmt_simples)
    diferenca = p_price - p_simples

    # 1. SEM_ANATOCISMO: diferença insignificante (taxa zero, n=1, ou cálculo equivalente)
    if abs(diferenca) < _TOLERANCIA_SEM_ANATOCISMO:
        return "SEM_ANATOCISMO"

    # 2. ANATOCISMO_LICITO: SFN + pactuação expressa + pós-MP 2.170
    if instituicao_sfn and pactuacao_expressa and data_assinatura >= _MP_2170_DATA:
        return "ANATOCISMO_LICITO"

    # 3. ANATOCISMO_QUESTIONAVEL: SFN sem pactuação clara → HITL
    if instituicao_sfn and not pactuacao_expressa and data_assinatura >= _MP_2170_DATA:
        return "ANATOCISMO_QUESTIONAVEL"

    # 4. ANATOCISMO_ILICITO: fora SFN OU pré-MP (sem outra base legal)
    return "ANATOCISMO_ILICITO"


def sumulas_aplicaveis(classificacao: ClassificacaoAnatocismo) -> list[str]:
    """Retorna ids canônicos das súmulas/temas aplicáveis a cada classificação.

    Mapeia para o vault (FR-RAG-01 IDs no formato AAA-NNN).
    """
    mapping: dict[ClassificacaoAnatocismo, list[str]] = {
        "SEM_ANATOCISMO": [],
        "ANATOCISMO_LICITO": ["STF-S121", "STJ-S539", "STJ-T247"],
        "ANATOCISMO_QUESTIONAVEL": ["STJ-S539", "STJ-T247"],  # HITL — pactuação ambígua
        "ANATOCISMO_ILICITO": ["STF-S121"],  # Súmula 121 sustenta tese de ilicitude
    }
    return mapping[classificacao]


def _ensure_decimal(v: Decimal | str | int) -> Decimal:
    """FR-CALC-01: float é PROIBIDO."""
    if isinstance(v, float):
        raise TypeError(
            f"float é PROIBIDO em cálculos jurídicos (FR-CALC-01). "
            f"Use Decimal ou string. Recebido: {v!r}"
        )
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))
