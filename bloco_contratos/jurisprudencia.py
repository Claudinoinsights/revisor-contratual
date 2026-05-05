"""Pydantic models do vault de jurisprudência (ADR-007 schema sqlite-vec).

Schema enriquecido v1.0.2 (Smith F-CRIT-03 absorvido):
  - vigente_em (date | None): None = vigente; date = vigência ATÉ esta data
  - superseded_by (id_doc | None): link para jurisprudência substituta
  - data_ultima_validacao (date): quando vigência foi verificada pela última vez

Embeddings: Legal-BERTimbau-sts-base (768 dims) — não embedded no model
(modelo Pydantic carrega metadados; embedding fica em virtual table sqlite-vec).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

# ──────────────────────────────────────────────────────────────────────────────
# Taxonomias controladas
# ──────────────────────────────────────────────────────────────────────────────

CourtId = Literal[
    "STF", "STJ", "TST",
    "TJAC", "TJAL", "TJAP", "TJAM", "TJBA", "TJCE", "TJDF", "TJES", "TJGO",
    "TJMA", "TJMT", "TJMS", "TJMG", "TJPA", "TJPB", "TJPR", "TJPE", "TJPI",
    "TJRJ", "TJRN", "TJRS", "TJRO", "TJRR", "TJSC", "TJSP", "TJSE", "TJTO",
]
"""Tribunal de origem do doc. UF inicial: BA. Multi-UF first-class via FR-RAG-05."""

TipoDoc = Literal[
    "SUMULA_VINCULANTE",
    "SUMULA",
    "REPERCUSSAO_GERAL",
    "TEMA_REPETITIVO",
    "ACORDAO",
    "LEI",
    "MEDIDA_PROVISORIA",
    "DECRETO",
]
"""Tipo de documento jurídico (ADR-007)."""

PesoVinculacao = Literal[1, 2, 3, 4, 5]
"""Matriz canônica NFR-GOV-01:
  5 = Súmula Vinculante STF
  4 = Tema Repetitivo STJ + Repercussão Geral STF
  3 = Súmula STJ + Súmula TST/TSE
  2 = Acórdão STJ/STF
  1 = Acórdão TJ
"""

LegalTopic = str
"""Taxonomia controlada (ex: 'anatocismo', 'tabela_price', 'capitalizacao_juros'). Manter em
.lmas-core/data ou config — não enum porque é extensível."""


# ──────────────────────────────────────────────────────────────────────────────
# Documento de jurisprudência (ADR-007 schema)
# ──────────────────────────────────────────────────────────────────────────────


class JurisprudenciaItem(BaseModel):
    """Doc do vault (linha da tabela `jurisprudencia` em ADR-007).

    Embedding NÃO está aqui — fica na virtual table sqlite-vec ligada por id_doc.
    """

    id_doc: str = Field(
        ...,
        pattern=r"^[A-Z]+(?:[A-Z]+)?-[A-Z0-9]+\d*$",
        description="Ex: 'STJ-S539', 'STF-SV4', 'TJBA-A12345'",
    )
    court_id: CourtId
    tipo_doc: TipoDoc
    numero: str = Field(..., min_length=1)
    binding: bool = Field(..., description="Vinculante (sumula vinculante OU tema repetitivo)")
    peso_vinculacao: PesoVinculacao
    legal_topic_principal: LegalTopic
    modalidade_relacionada: list[str] = Field(
        default_factory=list,
        description="Modalidades de contrato afetadas (ex: ['CDC_VEICULOS_PF'])",
    )
    ano_julgamento: int = Field(..., ge=1900, le=2100)
    ementa: str = Field(..., min_length=20)
    texto_completo: str = Field(..., min_length=20)
    indexed_at: datetime
    # ── PATCH v1.0.2 (Smith F-CRIT-03 absorvido) ─────────────────────────
    vigente_em: date | None = Field(
        None,
        description="None = vigente; date = vigência ATÉ esta data (anti-superseded)",
    )
    superseded_by: str | None = Field(
        None,
        description="id_doc do substituto (FK lógica para jurisprudencia.id_doc)",
    )
    data_ultima_validacao: date = Field(
        ...,
        description="Quando vigência foi verificada (FR-RAG-01 AC v1.0.2)",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Resultado de busca híbrida (FR-RAG-02)
# ──────────────────────────────────────────────────────────────────────────────


class BuscaHibridaResult(BaseModel):
    """Output de bloco_vault.busca.buscar_hibrida() — top-K com fusion RRF."""

    query: str
    uf_contrato: str  # UF (não o Literal para flexibilidade do scraper)
    data_assinatura_contrato: date
    binding_relax: bool = False
    top_k: int = Field(..., ge=1, le=100)
    docs: list[JurisprudenciaItem]
    latencia_ms: int = Field(..., ge=0, description="NFR-PERF-03: ≤500ms p95")
