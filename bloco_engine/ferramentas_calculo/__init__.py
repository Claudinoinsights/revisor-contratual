"""bloco_engine/ferramentas_calculo — Núcleo determinístico do Perito (P-INT-01).

DECIMAL EVERYWHERE — float é PROIBIDO neste módulo (FR-CALC-01 + CI gate).
Todas as operações monetárias usam `decimal.Decimal` com `getcontext().prec=28`.

Componentes:
  - price.py — Tabela Price (PMT, tabela de amortização, juros simples comparativo)
  - anatocismo.py — Classificação SEM/LICITO/QUESTIONAVEL/ILICITO (STF-S121 + STJ-S539 + STJ-T247)
"""

from bloco_engine.ferramentas_calculo.anatocismo import (
    classificar_anatocismo,
    sumulas_aplicaveis,
)
from bloco_engine.ferramentas_calculo.price import (
    PMT_PRECISION,
    aa_to_am,
    calcular_pmt_price,
    calcular_pmt_simples,
    gerar_tabela_amortizacao,
)

__all__ = [
    # price
    "calcular_pmt_price",
    "calcular_pmt_simples",
    "gerar_tabela_amortizacao",
    "aa_to_am",
    "PMT_PRECISION",
    # anatocismo
    "classificar_anatocismo",
    "sumulas_aplicaveis",
]
