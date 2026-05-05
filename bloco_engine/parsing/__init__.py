"""bloco_engine/parsing — extração PDF → markdown → ContratoMetadata + ParsedContract.

Pipeline (FR-PARSE-01 + FR-PARSE-02):
  - PyMuPDF4LLM (parser primário) → fallback Marker (OCR, opt-in)
  - fidelity_score heurístico decide quando escalar
  - regex PT-BR extrai metadata estruturada

API pública:
  - parse_contract(pdf_path, ...) → ParsedContract
  - extract_metadata_from_markdown(markdown, ...) → ContratoMetadata
  - compute_contract_hash(pdf_bytes) → SHA256 hex
  - compute_fidelity_score(markdown) → float 0..1

Exceções:
  - ParserError (base)
  - PDFEncrypted, PDFInvalid, ParserOCRRequired, MetadataExtractionError
"""

from bloco_engine.parsing.fidelity import compute_fidelity_score
from bloco_engine.parsing.marker_parser import ParserOCRRequired, parse_pdf_marker
from bloco_engine.parsing.orchestrator import (
    FIDELITY_THRESHOLD_DEFAULT,
    MetadataExtractionError,
    compute_contract_hash,
    extract_metadata_from_markdown,
    parse_contract,
)
from bloco_engine.parsing.pymupdf_parser import (
    PDFEncrypted,
    PDFInvalid,
    ParserError,
    parse_pdf_pymupdf,
)

__all__ = [
    # API top-level
    "parse_contract",
    "extract_metadata_from_markdown",
    "compute_contract_hash",
    "compute_fidelity_score",
    # parsers granulares
    "parse_pdf_pymupdf",
    "parse_pdf_marker",
    # exceções
    "ParserError",
    "PDFEncrypted",
    "PDFInvalid",
    "ParserOCRRequired",
    "MetadataExtractionError",
    # config
    "FIDELITY_THRESHOLD_DEFAULT",
]
