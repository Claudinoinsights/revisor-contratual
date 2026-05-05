"""P-INT-03 Juiz Revisor — Python puro (FR-JUIZ-01..03 + ADR-003).

Auditabilidade jurídica é não-negociável: Juiz NÃO pode ser LLM.
Cálculo é determinístico, reprodutível e justificável em juízo.

3 checagens determinísticas (FR-JUIZ-01):
  C1: divergência entre taxa contratual e taxa BACEN da modalidade+mês ≥0.5pp
  C2: max(peso_vinculacao) dos docs citados ≥4 (Súmula Vinculante / Tema Repetitivo)
  C3: ≥1 doc citado pertence a {STF, STJ, TJ{UF_contrato}}

Aderência = média(c1+c2+c3) * 100

Threshold (DP-04 resolvido em ADR-003):
  - aderência == 100  → APROVADO_100 (segue para FR-DELIV-06 CFOAB)
  - 70 ≤ aderência < 100 → APROVADO_COM_RISCO_HITL (painel HITL FR-JUIZ-02)
  - aderência < 70  → REJEITADO (Relatório de Inviabilidade — NUNCA petição)
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from bloco_contratos import BacenData, TeseAdvogado, VeredictoJuiz

# ──────────────────────────────────────────────────────────────────────────────
# Constantes do critério (parametrizáveis em config futura — não hardcoded em UI)
# ──────────────────────────────────────────────────────────────────────────────

C1_DIVERGENCIA_BACEN_PP_LIMIAR = Decimal("0.5")
"""Divergência mínima em pontos percentuais para C1 PASS (FR-JUIZ-01)."""

C2_PESO_VINCULACAO_MIN = 4
"""Peso mínimo de jurisprudência para C2 PASS (NFR-GOV-01: ≥4 = Tema Repetitivo / Repercussão Geral)."""

THRESHOLD_APROVADO_100 = Decimal("100.0")
THRESHOLD_HITL_MIN = Decimal("70.0")
"""ADR-003: 70%/100% definitivo (DP-04 resolvido)."""

VereditoTipo = Literal["APROVADO_100", "APROVADO_COM_RISCO_HITL", "REJEITADO"]


# ──────────────────────────────────────────────────────────────────────────────
# 3 checagens determinísticas (privadas — testáveis isoladamente)
# ──────────────────────────────────────────────────────────────────────────────


def _check_c1_divergencia_bacen(
    taxa_contratual_aa_decimal: Decimal | str, bacen_data: BacenData
) -> tuple[Decimal, str]:
    """C1: divergência taxa contratual vs taxa BACEN ≥0.5pp.

    Score linear no intervalo [0, 1]: divergência ≥ limiar → 1.0; senão proporcional.

    Returns:
        (score, razao) — razão é mensagem explicativa para audit log.
    """
    if isinstance(taxa_contratual_aa_decimal, float):
        raise TypeError(
            f"float é PROIBIDO (FR-CALC-01). Use Decimal/str. Recebido {taxa_contratual_aa_decimal!r}"
        )
    if isinstance(bacen_data.taxa_media, float):  # defensivo (Pydantic já bloqueia)
        raise TypeError("BacenData.taxa_media veio como float — bug serialização")

    taxa_contrato = (
        taxa_contratual_aa_decimal
        if isinstance(taxa_contratual_aa_decimal, Decimal)
        else Decimal(str(taxa_contratual_aa_decimal))
    )
    # bacen_data.taxa_media é % a.m. (Decimal-as-string) → comparar em mesma unidade requer conversão
    # Simplificação MVP: assumimos AMBAS já normalizadas para mesma unidade.
    # (conversão a.m. ↔ a.a. fica em chamador via aa_to_am de bloco_engine)
    taxa_bacen = Decimal(bacen_data.taxa_media)
    divergencia = abs(taxa_contrato - taxa_bacen)

    if divergencia >= C1_DIVERGENCIA_BACEN_PP_LIMIAR:
        return Decimal("1.0"), (
            f"C1 PASS: divergência {divergencia} pp ≥ limiar {C1_DIVERGENCIA_BACEN_PP_LIMIAR} pp"
        )
    score = divergencia / C1_DIVERGENCIA_BACEN_PP_LIMIAR
    return score, (
        f"C1 PARCIAL: divergência {divergencia} pp < limiar — score {score:.4f}"
    )


def _check_c2_peso_vinculante(tese: TeseAdvogado) -> tuple[Decimal, str]:
    """C2: peso_vinculacao máximo dos docs citados ≥4 (Súmula Vinculante / Tema Repetitivo)."""
    if not tese.fundamentos_invocados:
        return Decimal("0.0"), "C2 FAIL: nenhum fundamento invocado"

    max_peso = max(f.peso_vinculacao for f in tese.fundamentos_invocados)
    if max_peso >= C2_PESO_VINCULACAO_MIN:
        return Decimal("1.0"), (
            f"C2 PASS: max(peso_vinculacao)={max_peso} ≥ {C2_PESO_VINCULACAO_MIN}"
        )
    score = Decimal(max_peso) / Decimal(C2_PESO_VINCULACAO_MIN)
    return score, (
        f"C2 PARCIAL: max(peso_vinculacao)={max_peso} < {C2_PESO_VINCULACAO_MIN} — score {score:.4f}"
    )


def _check_c3_jurisdicao(tese: TeseAdvogado, uf_contrato: str) -> tuple[Decimal, str]:
    """C3: ≥1 doc citado pertence a {STF, STJ, TJ{UF}} — score binário."""
    jurisdicoes_aceitas = {"STF", "STJ", f"TJ{uf_contrato.upper()}"}
    docs_jurisdicao = [
        f for f in tese.fundamentos_invocados if f.court_id in jurisdicoes_aceitas
    ]
    if docs_jurisdicao:
        nomes_courts = sorted({f.court_id for f in docs_jurisdicao})
        return Decimal("1.0"), (
            f"C3 PASS: {len(docs_jurisdicao)} doc(s) de {nomes_courts}"
        )
    return Decimal("0.0"), (
        f"C3 FAIL: nenhum doc de {sorted(jurisdicoes_aceitas)} citado"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Função principal — Juiz Revisor (FR-JUIZ-01..03)
# ──────────────────────────────────────────────────────────────────────────────


def juiz_revisar(
    *,
    taxa_contratual_aa_decimal: Decimal | str,
    bacen_data: BacenData,
    tese: TeseAdvogado,
    uf_contrato: str,
) -> VeredictoJuiz:
    """3 checagens determinísticas + scoring + veredito (FR-JUIZ-01..03).

    Reprodutibilidade absoluta: mesma entrada → mesma saída sempre.
    Auditável: cada score acompanha razão textual gravada no audit log.

    Args:
        taxa_contratual_aa_decimal: taxa do contrato em forma DECIMAL (não percentual)
        bacen_data: resposta python-bcb com taxa BACEN da modalidade+mês
        tese: output do Advogado (FR-TESE-01) com fundamentos invocados
        uf_contrato: UF do contrato (ex: "BA") — para C3 jurisdição

    Returns:
        VeredictoJuiz Pydantic (validador interno garante consistência aderência ↔ scores)
    """
    if not isinstance(uf_contrato, str) or len(uf_contrato) != 2:
        raise ValueError(f"uf_contrato deve ser sigla 2 letras (ex: 'BA'), recebido {uf_contrato!r}")

    c1_score, c1_razao = _check_c1_divergencia_bacen(taxa_contratual_aa_decimal, bacen_data)
    c2_score, c2_razao = _check_c2_peso_vinculante(tese)
    c3_score, c3_razao = _check_c3_jurisdicao(tese, uf_contrato)

    aderencia_raw = (c1_score + c2_score + c3_score) / Decimal("3") * Decimal("100")
    # Arredondamento HALF_EVEN (banker's) com 1 casa decimal — consistente com VeredictoJuiz validator
    aderencia = aderencia_raw.quantize(Decimal("0.1"))

    veredito = _classificar_veredito(aderencia)

    razoes = [c1_razao, c2_razao, c3_razao, f"Aderência total: {aderencia}% → {veredito}"]

    return VeredictoJuiz(
        c1_score=float(c1_score),
        c2_score=float(c2_score),
        c3_score=float(c3_score),
        aderencia=float(aderencia),
        veredito=veredito,
        razoes=razoes,
    )


def _classificar_veredito(aderencia: Decimal) -> VereditoTipo:
    """Threshold definitivo (DP-04 resolvido em ADR-003)."""
    if aderencia >= THRESHOLD_APROVADO_100:
        return "APROVADO_100"
    if aderencia >= THRESHOLD_HITL_MIN:
        return "APROVADO_COM_RISCO_HITL"
    return "REJEITADO"
