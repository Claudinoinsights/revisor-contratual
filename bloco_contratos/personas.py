"""Pydantic models das 4 personas internas (ADR-003).

D-04 REVOGADA por Morpheus sessão 10 — 4 personas, não 3.
PATCH SUB-C (ADR-003): Economista usa Qwen 2.5 3B (não Sabia compartilhada).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

LLMTier = Literal["lean", "balanced", "premium"]
"""Tier configurável do Advogado (FR-TESE-02). Economista usa Qwen 3B FIXO (ADR-003 PATCH SUB-C)."""


# ──────────────────────────────────────────────────────────────────────────────
# P-INT-02 — Advogado especialista em direito bancário (LLM Sabia-7B)
# ──────────────────────────────────────────────────────────────────────────────


class FundamentoInvocado(BaseModel):
    """Citação jurídica usada na tese (rastreável ao vault)."""

    model_config = ConfigDict(extra="forbid")  # F-LLM-MED-01 hardening: rejeita campos extras alucinados pelo LLM

    id_doc: str = Field(..., description="ID do doc no vault (ex: 'STJ-S539')")
    citacao_textual: str = Field(..., min_length=10, description="Trecho citado pela tese")
    peso_vinculacao: int = Field(..., ge=1, le=5, description="Matriz NFR-GOV-01")
    court_id: str = Field(..., description="STF | STJ | TJ{UF}")


class TeseAdvogado(BaseModel):
    """Output do Advogado LLM (FR-TESE-01).

    Validação cruzada hard-fail: docs_efetivamente_citados_ids ⊆ docs_consultados_ids.
    Anti-fantasma sintático (defesa em profundidade pré-validação semântica ADR-004).
    """

    model_config = ConfigDict(extra="forbid")  # F-LLM-MED-01 hardening: rejeita campos extras alucinados pelo LLM

    tese_principal: str = Field(..., min_length=50)
    fundamentos_invocados: list[FundamentoInvocado] = Field(..., min_length=1)
    docs_consultados_ids: list[str] = Field(..., description="Vault docs disponíveis no top-K")
    docs_efetivamente_citados_ids: list[str] = Field(..., description="Subset usado de fato")
    confianca: float = Field(..., ge=0.0, le=1.0)

    @field_validator("docs_efetivamente_citados_ids")
    @classmethod
    def citados_subset_consultados(cls, v: list[str], info: object) -> list[str]:
        # Pydantic v2: info.data tem campos validados anteriormente
        consultados = info.data.get("docs_consultados_ids", [])  # type: ignore[attr-defined]
        if consultados and not set(v).issubset(set(consultados)):
            fantasmas = set(v) - set(consultados)
            raise ValueError(
                f"CitationFantasma — LLM citou docs fora do RAG: {sorted(fantasmas)}. "
                "Validação cruzada FR-TESE-01 hard-fail."
            )
        return v


# ──────────────────────────────────────────────────────────────────────────────
# P-INT-04 — Economista bancário (LLM Qwen 2.5 3B FIXO — ADR-003 PATCH SUB-C)
# ──────────────────────────────────────────────────────────────────────────────


class AnaliseMacroEconomica(BaseModel):
    """Output do Economista LLM. Análise contextual macro (Selic, atipicidade, peers).

    Promovida a primeira-classe v1.0.2 (mitigação Tema 1378 STJ).
    """

    model_config = ConfigDict(extra="forbid")  # F-LLM-MED-01 hardening: rejeita campos extras alucinados pelo LLM

    ciclo_selic_periodo: str = Field(..., description="Ex: 'alta_2022_2024' | 'baixa_2026'")
    taxa_atipica_bool: bool = Field(..., description="Taxa contratual desviante de pares na época")
    comparacao_peer_modalities: dict[str, str] = Field(
        ...,
        description="Mapeamento modalidade → taxa média BACEN concorrente",
    )
    contexto_macro_resumido: str = Field(..., min_length=50, max_length=2000)


# ──────────────────────────────────────────────────────────────────────────────
# P-INT-03 — Juiz Revisor (Python puro — auditabilidade jurídica)
# ──────────────────────────────────────────────────────────────────────────────

VereditoTipo = Literal["APROVADO_100", "APROVADO_COM_RISCO_HITL", "REJEITADO"]


class VeredictoJuiz(BaseModel):
    """Output do Juiz Python puro (FR-JUIZ-01..03).

    Threshold definitivo (DP-04 resolvido em ADR-003):
      - aderência == 100  → APROVADO_100 (segue para FR-DELIV-06 CFOAB)
      - 70 ≤ aderência < 100 → APROVADO_COM_RISCO_HITL (painel HITL)
      - aderência < 70  → REJEITADO (Relatório de Inviabilidade, NUNCA petição)
    """

    model_config = ConfigDict(extra="forbid")  # F-LLM-MED-01 hardening: rejeita campos extras alucinados pelo LLM

    c1_score: float = Field(..., ge=0.0, le=1.0, description="Divergência BACEN ≥0.5pp")
    c2_score: float = Field(..., ge=0.0, le=1.0, description="max(peso_vinculacao) ≥4")
    c3_score: float = Field(..., ge=0.0, le=1.0, description="≥1 doc da jurisdição")
    aderencia: float = Field(..., ge=0.0, le=100.0)
    veredito: VereditoTipo
    razoes: list[str] = Field(default_factory=list)

    @field_validator("aderencia")
    @classmethod
    def aderencia_consistente_com_scores(cls, v: float, info: object) -> float:
        c1 = info.data.get("c1_score")  # type: ignore[attr-defined]
        c2 = info.data.get("c2_score")  # type: ignore[attr-defined]
        c3 = info.data.get("c3_score")  # type: ignore[attr-defined]
        if c1 is not None and c2 is not None and c3 is not None:
            esperado = round((c1 + c2 + c3) / 3 * 100, 1)
            if abs(v - esperado) > 0.1:  # tolerância arredondamento
                raise ValueError(
                    f"Aderência inconsistente: declarada={v}, esperada={esperado} "
                    f"(média(c1+c2+c3)*100). FR-JUIZ-01 exige reprodutibilidade."
                )
        return v


# ──────────────────────────────────────────────────────────────────────────────
# Validação semântica de citações (ADR-004 — NLI híbrido)
# ──────────────────────────────────────────────────────────────────────────────

NLILabel = Literal["entailment", "neutral", "contradiction"]
ValidacaoVeredito = Literal["PASS", "FAIL_SIMILARITY", "FAIL_POLARITY"]


class ValidacaoSemantica(BaseModel):
    """Output do pipeline NLI híbrido (FR-TESE-04 + ADR-004).

    Bloqueia emissão de peça se houver paráfrase invertida
    (cosine alto + nli=contradiction). Audit log obrigatório.
    """

    model_config = ConfigDict(extra="forbid")  # F-LLM-MED-01 hardening: rejeita campos extras alucinados pelo LLM

    id_doc: str
    frase_tese: str = Field(..., min_length=5)
    ementa_real: str = Field(..., min_length=5)
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    nli_label: NLILabel
    nli_confidence: float = Field(..., ge=0.0, le=1.0)
    veredito: ValidacaoVeredito
    razao: str = Field(..., min_length=5)


# ──────────────────────────────────────────────────────────────────────────────
# P-INT-05 — Redator Revisional (Sprint 6 Bloco γ — ADR-022)
# ──────────────────────────────────────────────────────────────────────────────
#
# Hardening anti-hallucination 3-camadas (ADR-022 D2):
#   1. Pydantic strict extra="forbid" + min_length por field
#   2. Vault-restricted citations (validar_citacoes_vault em redator.py)
#   3. Validador post-LLM (regex valor_causa + length checks)
#
# Filtro veredito FR-PECA-07:
#   APROVADO_100              → PecaRevisional (peça completa)
#   APROVADO_COM_RISCO_HITL   → PecaRevisional (com seção Pontos de Atenção)
#   REJEITADO                 → RelatorioInviabilidade (NÃO petição — análise técnica)

PecaFormat = Literal["PecaRevisional", "RelatorioInviabilidade"]


class PecaRevisional(BaseModel):
    """Peça revisional formal CDC veículos — output do Redator LLM (FR-PECA-01).

    Estrutura CFOAB 8 seções (OAB Provimento 209/2021):
      1. Cabeçalho (Excelentíssimo Sr. Juiz)
      2. Qualificação das Partes
      3. Dos Fatos
      4. Do Direito
      5. Do Pedido
      6. Do Valor da Causa (numerado + por extenso)
      7. Fecho (data + cidade + assinatura placeholder)
      8. Disclaimer LGPD/OAB (Insumo técnico-jurídico — não substitui responsabilidade)

    Layer 1 anti-hallucination: extra="forbid" + min_length por field hard-fail.
    Layer 2: citacoes_jurisprudencia validada vs vault em validar_citacoes_vault.
    Layer 3: regex valor_causa (R$ X,YZ) + post-LLM checks no Redator.
    """

    model_config = ConfigDict(extra="forbid")

    cabecalho: str = Field(
        ...,
        min_length=50,
        description="Excelentíssimo Sr. Juiz da Vara... — cabeçalho da petição",
    )
    qualificacao_partes: str = Field(
        ...,
        min_length=100,
        description="Identificação Autor + Ré com qualificação completa CFOAB",
    )
    dos_fatos: str = Field(
        ...,
        min_length=200,
        description="Narrativa cronológica dos fatos do contrato",
    )
    do_direito: str = Field(
        ...,
        min_length=300,
        description="Fundamentação jurídica com citações Súmulas STJ vault-restricted",
    )
    do_pedido: str = Field(
        ...,
        min_length=100,
        description="Pedidos formais (revisional + restituição em dobro)",
    )
    valor_causa: str = Field(
        ...,
        pattern=r"R\$\s*[\d\.]+,\d{2}",
        description="Valor causa numerado formato BR (ex: 'R$ 5.107,00')",
    )
    valor_causa_extenso: str = Field(
        ...,
        min_length=10,
        description="Valor causa por extenso (ex: 'cinco mil cento e sete reais')",
    )
    fecho: str = Field(
        ...,
        min_length=50,
        description="Termos em que pede deferimento + data + cidade + assinatura placeholder",
    )
    disclaimer_lgpd_oab: str = Field(
        ...,
        min_length=200,
        description="Disclaimer LGPD + OAB Provimento 209/2021 (Insumo técnico-jurídico)",
    )
    citacoes_jurisprudencia: list[str] = Field(
        default_factory=list,
        description="IDs das jurisprudências citadas (rastreáveis ao vault) — ex: ['STJ-S539', 'STJ-S472']",
    )
    pontos_atencao: str | None = Field(
        default=None,
        description="Seção opcional para veredictos APROVADO_COM_RISCO_HITL — riscos identificados pelo Juiz",
    )


class RelatorioInviabilidade(BaseModel):
    """Relatório de Inviabilidade — output do Redator quando veredito=REJEITADO.

    NÃO é petição — é análise técnica explicando por que a revisional não é viável.
    Mitiga risco de protocolar peça inadequada (ética OAB).
    """

    model_config = ConfigDict(extra="forbid")

    cabecalho: str = Field(
        ...,
        min_length=30,
        description="Título 'Relatório de Inviabilidade Revisional' + identificação contrato",
    )
    sintese_analise: str = Field(
        ...,
        min_length=100,
        description="Síntese executiva: por que a revisional foi rejeitada",
    )
    diagnostico_tecnico: str = Field(
        ...,
        min_length=200,
        description="Análise técnica: scores C1/C2/C3 + aderência + razões objetivas",
    )
    motivos_rejeicao: list[str] = Field(
        ...,
        min_length=1,
        description="Lista enumerada de motivos da inviabilidade",
    )
    recomendacao: str = Field(
        ...,
        min_length=100,
        description="Recomendação ao advogado (não protocolar / buscar outros fundamentos)",
    )
    disclaimer_lgpd_oab: str = Field(
        ...,
        min_length=200,
        description="Disclaimer LGPD + OAB Provimento 209/2021",
    )
