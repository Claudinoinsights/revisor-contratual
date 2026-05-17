"""Pydantic models do contrato bancário e cálculos determinísticos.

Decimal everywhere (FR-CALC-01) — float é PROIBIDO em wire format.
Uso interno via Decimal puro; serialização sempre como string para evitar perda de precisão JSON.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ──────────────────────────────────────────────────────────────────────────────
# Metadados do contrato (input do usuário + extração FR-PARSE-02)
# ──────────────────────────────────────────────────────────────────────────────

ModalidadeContrato = Literal[
    "CDC_VEICULOS_PF",  # MVP foco
    "CDC_BENS_PF",
    "CDC_IMOBILIARIO",
    "CARTAO_ROTATIVO",
    # Adicionar novas modalidades não exige refactor (NFR-MAINT-01)
]

UF = Literal[
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]


class ContratoMetadata(BaseModel):
    """Metadados coletados no upload (FR-UPLOAD-01) + extraídos (FR-PARSE-02)."""

    contract_hash: str = Field(..., description="sha256(pdf_bytes) — anti-duplicata + recovery key")
    uf_contrato: UF
    data_assinatura: date = Field(..., description="ISO 8601, faixa 1986-presente")
    modalidade: ModalidadeContrato = "CDC_VEICULOS_PF"
    valor_financiado: str | None = Field(None, description="Decimal-as-string (opcional)")
    taxa_contratual_aa: str | None = Field(None, description="Decimal-as-string % a.a.")
    taxa_contratual_am: str | None = Field(None, description="Decimal-as-string % a.m.")
    n_parcelas: int | None = Field(None, ge=1, le=480)

    @field_validator("data_assinatura")
    @classmethod
    def data_dentro_da_janela(cls, v: date) -> date:
        if v.year < 1986:
            raise ValueError("Contratos pré-1986 fora do escopo (Plano Cruzado/inflação)")
        if v > date.today():
            raise ValueError("Data de assinatura no futuro é inválida")
        return v


# ──────────────────────────────────────────────────────────────────────────────
# Resultado do cálculo determinístico (Perito P-INT-01 — Python puro)
# ──────────────────────────────────────────────────────────────────────────────

ClassificacaoAnatocismo = Literal[
    "SEM_ANATOCISMO",
    "ANATOCISMO_LICITO",
    "ANATOCISMO_QUESTIONAVEL",
    "ANATOCISMO_ILICITO",
]


class LinhaAmortizacao(BaseModel):
    """Uma linha da tabela Price/SAC (FR-CALC-02)."""

    n_parcela: int = Field(..., ge=1)
    saldo_inicial: str  # Decimal-as-string
    juros: str
    amortizacao: str
    valor_parcela: str
    saldo_final: str

    @field_validator("saldo_inicial", "juros", "amortizacao", "valor_parcela", "saldo_final")
    @classmethod
    def parseavel_como_decimal(cls, v: str) -> str:
        try:
            Decimal(v)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Valor monetário não-Decimal: {v!r}") from exc
        return v


class ResultadoCalculo(BaseModel):
    """Output do Perito (FR-CALC-01..03)."""

    pmt_composto: str = Field(..., description="Tabela Price PMT")
    pmt_simples: str = Field(..., description="PMT em juros simples (referência anatocismo)")
    diferenca_anatocismo: str = Field(..., description="pmt_composto - pmt_simples")
    classificacao_anatocismo: ClassificacaoAnatocismo
    sumulas_aplicaveis: list[str] = Field(
        default_factory=list,
        description="Ex: ['STF-S121', 'STJ-S539', 'STJ-T247']",
    )
    tabela_amortizacao: list[LinhaAmortizacao]
    taxa_contratual_aa_decimal: str = Field(
        ...,
        description="Taxa anual em Decimal-as-string usada no cálculo",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Output do parsing (FR-PARSE-01)
# ──────────────────────────────────────────────────────────────────────────────


class ParsedContract(BaseModel):
    """Resultado do bloco_engine/parsing/. Saída para o orchestrator."""

    metadata: ContratoMetadata
    markdown_extracted: str = Field(..., description="PyMuPDF4LLM output")
    parser_used: Literal["pymupdf4llm", "marker_ocr", "ocrmypdf_tesseract"] = "pymupdf4llm"
    parsed_at: datetime
    pages_count: int = Field(..., ge=1)
    fidelity_score: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="≥0.95 esperado para tabela de amortização (FR-PARSE-01 AC)",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Resposta BACEN (FR-BACEN-01..03)
# ──────────────────────────────────────────────────────────────────────────────


class BacenData(BaseModel):
    """Resposta python-bcb (cache + retry + fallback)."""

    codigo_sgs: int = Field(..., description="Ex: 25471 (Veículos PF média mensal)")
    modalidade: ModalidadeContrato
    mes_ref: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="ISO YYYY-MM")
    taxa_media: str = Field(..., description="Decimal-as-string % a.m.")
    fonte_url: str = Field(..., description="https://api.bcb.gov.br/...")
    fetched_at: datetime
    is_fallback: bool = Field(
        default=False,
        description="True se veio do cache 'última taxa conhecida' (FR-BACEN-03)",
    )
