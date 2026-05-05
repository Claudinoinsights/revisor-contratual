"""Fidelity score heurístico — quantifica qualidade da extração markdown.

Score 0.0..1.0 = quão "completo" parece o markdown extraído de um contrato bancário.
Threshold 0.5 default para acionar fallback Marker (configurável no orchestrator).

Heurística (3 dimensões somadas):
  - palavras-chave de contrato bancário (peso 0.5)
  - presença de tabela markdown estruturada (peso 0.3)
  - presença de valores monetários R$ (peso 0.2)

Não é uma métrica acadêmica — é um proxy operacional. Quando markdown vier vazio
ou for só lixo de OCR ruim, score cai abaixo de threshold e o orchestrator decide
escalar para Marker.

NOTA: heurística é INTENCIONALMENTE conservadora. Falso-negativo (PDF bom marcado
como ruim e roteado a Marker) é preferível a falso-positivo (PDF ruim aceito como
bom e gerando peça com dados errados).
"""

from __future__ import annotations

import re

# Palavras-chave esperadas em contratos CDC veículos PF (PT-BR)
KEYWORDS_CONTRATO = (
    "parcela",
    "juros",
    "valor",
    "taxa",
    "saldo",
    "amortização",
    "amortizacao",
    "prestação",
    "prestacao",
    "financiamento",
    "contrato",
    "cdc",
)

# Pattern tabela markdown (linha com 2+ pipes não escapados)
PATTERN_TABELA_MD = re.compile(r"^\s*\|.+\|.+\|", re.MULTILINE)

# Pattern monetário BR (R$ XXX,XX ou R$ X.XXX,XX)
PATTERN_MONETARIO_BR = re.compile(r"R\$\s*[\d]{1,3}(?:\.\d{3})*(?:,\d{2})?")


def compute_fidelity_score(markdown: str) -> float:
    """Calcula score 0.0..1.0 de fidelidade do markdown extraído.

    Args:
        markdown: texto extraído pelo parser.

    Returns:
        0.0 se markdown vazio/None; até 1.0 caso contrário.
    """
    if not markdown or not markdown.strip():
        return 0.0

    text_lower = markdown.lower()

    # Dimensão 1: palavras-chave (peso 0.5)
    found_keywords = sum(1 for kw in KEYWORDS_CONTRATO if kw in text_lower)
    score_keywords = min(found_keywords / 6.0, 1.0) * 0.5  # 6 palavras = score máximo dim

    # Dimensão 2: tabela markdown (peso 0.3 binária)
    score_tabela = 0.3 if PATTERN_TABELA_MD.search(markdown) else 0.0

    # Dimensão 3: monetário BR (peso 0.2 binária)
    score_monetario = 0.2 if PATTERN_MONETARIO_BR.search(markdown) else 0.0

    return round(score_keywords + score_tabela + score_monetario, 4)
