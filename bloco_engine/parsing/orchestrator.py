"""Orchestrator parsing — escolhe parser + extrai metadata + retorna ParsedContract.

Decisões arquiteturais Morpheus (D-MOR-3.2-A..D):
  - PyMuPDF4LLM = parser PRIMÁRIO sempre
  - Marker = fallback OCR APENAS se PyMuPDF retornar markdown vazio OU fidelity < threshold
  - Marker indisponível → ParserOCRRequired (não silent)
  - parser_used registra qual parser realmente foi usado (auditoria)

FR-PARSE-02 metadata extraction: regex sobre markdown PT-BR.
Campos obrigatórios (uf_contrato, data_assinatura) podem ser fornecidos via override
para evitar falha quando contrato tem layout não-padrão.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable, get_args

from bloco_contratos.contrato import (
    UF,
    ContratoMetadata,
    ModalidadeContrato,
    ParsedContract,
)
from bloco_engine.parsing.fidelity import compute_fidelity_score
from bloco_engine.parsing.marker_parser import ParserOCRRequired, parse_pdf_marker
from bloco_engine.parsing.pymupdf_parser import ParserError, parse_pdf_pymupdf

ParserFn = Callable[[Path], tuple[str, int]]

# Threshold fidelity abaixo do qual fallback Marker é acionado
FIDELITY_THRESHOLD_DEFAULT = 0.5

# UFs válidas (lista derivada do Literal UF em bloco_contratos.contrato)
_UFS_VALIDAS: tuple[str, ...] = get_args(UF)


class MetadataExtractionError(ParserError):
    """Falha em extrair campos metadata obrigatórios (uf_contrato, data_assinatura)."""


# ──────────────────────────────────────────────────────────────────────────────
# Hash do PDF (contract_hash)
# ──────────────────────────────────────────────────────────────────────────────


def compute_contract_hash(pdf_bytes: bytes) -> str:
    """SHA256 dos bytes do PDF — chave anti-duplicata + recovery (PRD)."""
    return hashlib.sha256(pdf_bytes).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Extração de metadata (FR-PARSE-02)
# ──────────────────────────────────────────────────────────────────────────────


def _extract_uf(markdown: str) -> str | None:
    """Procura UF no markdown — primeira ocorrência das 27 siglas válidas."""
    for match in re.finditer(r"\b([A-Z]{2})\b", markdown):
        if match.group(1) in _UFS_VALIDAS:
            return match.group(1)
    return None


def _extract_data_assinatura(markdown: str) -> date | None:
    """Procura data ISO YYYY-MM-DD ou DD/MM/YYYY — primeira ocorrência válida."""
    # ISO
    iso = re.search(r"(\d{4}-\d{2}-\d{2})", markdown)
    if iso:
        try:
            return date.fromisoformat(iso.group(1))
        except ValueError:
            pass
    # BR
    br = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", markdown)
    if br:
        try:
            d, m, y = map(int, br.groups())
            return date(y, m, d)
        except ValueError:
            pass
    return None


def _extract_modalidade(markdown: str) -> ModalidadeContrato:
    """Heurística keyword sobre markdown — default CDC_VEICULOS_PF (foco MVP)."""
    text = markdown.lower()
    # F-PARSE-HIGH-01 fix: parênteses são obrigatórios — precedência Python avalia
    # `A and B or C` como `(A and B) or C`, então sem parens "cartao" isolado
    # disparava CARTAO_ROTATIVO indevidamente em CDC veicular com débito em cartão.
    if "rotativo" in text and ("cartão" in text or "cartao" in text):
        return "CARTAO_ROTATIVO"
    if "imobiliário" in text or "imobiliario" in text or "habitacional" in text:
        return "CDC_IMOBILIARIO"
    if "veículo" in text or "veiculo" in text or "automóvel" in text or "automovel" in text:
        return "CDC_VEICULOS_PF"
    if "bem" in text or "bens" in text:
        return "CDC_BENS_PF"
    return "CDC_VEICULOS_PF"  # default MVP


def _extract_valor_financiado(markdown: str) -> str | None:
    """Procura padrão BR R$ X.XXX,XX e converte para Decimal-as-string canônico."""
    match = re.search(r"R\$\s*([\d]{1,3}(?:\.\d{3})*(?:,\d{2}))", markdown)
    if not match:
        return None
    raw = match.group(1).replace(".", "").replace(",", ".")
    try:
        return str(Decimal(raw))
    except InvalidOperation:
        return None


def _extract_taxa(markdown: str, periodo: str) -> str | None:
    """Procura taxa formato '1,99% a.m.' ou '23.5% a.a.' — periodo em {'aa','am'}."""
    # periodo[1] discrimina 'a' (anual) de 'm' (mensal); periodo[0] é sempre 'a'
    pattern = rf"(\d+[.,]\d+)\s*%\s*a\.?\s*{periodo[1]}\.?"
    match = re.search(pattern, markdown, flags=re.IGNORECASE)
    if not match:
        return None
    raw = match.group(1).replace(",", ".")
    try:
        return str(Decimal(raw))
    except InvalidOperation:
        return None


def _extract_n_parcelas(markdown: str) -> int | None:
    """Procura 'em N parcelas' ou 'N parcelas de'."""
    match = re.search(r"(\d{1,3})\s*parcelas?", markdown, flags=re.IGNORECASE)
    if not match:
        return None
    n = int(match.group(1))
    if 1 <= n <= 480:
        return n
    return None


def extract_metadata_from_markdown(
    markdown: str,
    *,
    contract_hash: str,
    uf_override: str | None = None,
    data_override: date | None = None,
) -> ContratoMetadata:
    """Constrói ContratoMetadata via regex + overrides opcionais.

    Raises:
        MetadataExtractionError se uf_contrato OU data_assinatura ausentes (sem override).
    """
    uf = uf_override or _extract_uf(markdown)
    data = data_override or _extract_data_assinatura(markdown)

    faltantes = []
    if uf is None:
        faltantes.append("uf_contrato")
    if data is None:
        faltantes.append("data_assinatura")
    if faltantes:
        raise MetadataExtractionError(
            f"Campos obrigatórios não extraíveis: {faltantes}. "
            "Forneça via uf_override / data_override ou revise o PDF de origem."
        )

    return ContratoMetadata(
        contract_hash=contract_hash,
        uf_contrato=uf,  # type: ignore[arg-type]
        data_assinatura=data,
        modalidade=_extract_modalidade(markdown),
        valor_financiado=_extract_valor_financiado(markdown),
        taxa_contratual_aa=_extract_taxa(markdown, "aa"),
        taxa_contratual_am=_extract_taxa(markdown, "am"),
        n_parcelas=_extract_n_parcelas(markdown),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Orquestrador top-level
# ──────────────────────────────────────────────────────────────────────────────


def parse_contract(
    pdf_path: Path,
    *,
    pdf_bytes: bytes | None = None,
    uf_override: str | None = None,
    data_override: date | None = None,
    fidelity_threshold: float = FIDELITY_THRESHOLD_DEFAULT,
    pymupdf_fn: ParserFn | None = None,
    marker_fn: ParserFn | None = None,
) -> ParsedContract:
    """Pipeline completo: PDF → markdown → metadata → ParsedContract.

    Args:
        pdf_path: caminho para o PDF.
        pdf_bytes: bytes do PDF para hash; se None, lê de pdf_path.
        uf_override / data_override: bypass extração regex (campos obrigatórios).
        fidelity_threshold: abaixo disso, fallback Marker.
        pymupdf_fn / marker_fn: injetáveis para testes.

    Raises:
        ParserOCRRequired se Marker necessário mas indisponível.
        MetadataExtractionError se metadata obrigatória ausente sem override.
        ParserError (subclasses) em problemas de PDF.
    """
    if pdf_bytes is None:
        pdf_bytes = pdf_path.read_bytes()
    contract_hash = compute_contract_hash(pdf_bytes)

    markdown, pages_count = parse_pdf_pymupdf(pdf_path, parser_fn=pymupdf_fn)
    parser_used: str = "pymupdf4llm"
    fidelity = compute_fidelity_score(markdown)

    if fidelity < fidelity_threshold:
        # Fallback Marker — pode levantar ParserOCRRequired
        markdown, pages_count = parse_pdf_marker(pdf_path, parser_fn=marker_fn)
        parser_used = "marker_ocr"
        fidelity = compute_fidelity_score(markdown)

    metadata = extract_metadata_from_markdown(
        markdown,
        contract_hash=contract_hash,
        uf_override=uf_override,
        data_override=data_override,
    )

    return ParsedContract(
        metadata=metadata,
        markdown_extracted=markdown,
        parser_used=parser_used,  # type: ignore[arg-type]
        parsed_at=datetime.now(),
        pages_count=max(pages_count, 1),
        fidelity_score=fidelity,
    )
