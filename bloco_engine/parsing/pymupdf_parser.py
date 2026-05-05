"""PyMuPDF4LLM parser — parser PRIMÁRIO (FR-PARSE-01).

Wrapper sobre pymupdf4llm.to_markdown + pymupdf.page_count.
parser_fn injetável para testes não-IO.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

ParserFn = Callable[[Path], tuple[str, int]]


class ParserError(Exception):
    """Erro base de parser PDF."""


class PDFEncrypted(ParserError):
    """PDF criptografado — não suportado."""


class PDFInvalid(ParserError):
    """Bytes não formam PDF válido."""


def _default_pymupdf_parser(pdf_path: Path) -> tuple[str, int]:
    """Implementação real (lazy import para testes não exigirem PyMuPDF instalado)."""
    import pymupdf  # type: ignore[import-not-found]
    import pymupdf4llm  # type: ignore[import-not-found]

    try:
        with pymupdf.open(pdf_path) as doc:
            if doc.is_encrypted:
                raise PDFEncrypted(f"PDF criptografado não suportado: {pdf_path}")
            pages_count = doc.page_count
    except pymupdf.FileDataError as exc:
        raise PDFInvalid(f"Bytes inválidos para PDF: {pdf_path}") from exc

    markdown = pymupdf4llm.to_markdown(str(pdf_path))
    return markdown, pages_count


def parse_pdf_pymupdf(pdf_path: Path, parser_fn: ParserFn | None = None) -> tuple[str, int]:
    """Parse PDF retornando (markdown, pages_count).

    Args:
        pdf_path: caminho para o PDF.
        parser_fn: injetável para testes — default usa pymupdf4llm + pymupdf.

    Raises:
        PDFEncrypted, PDFInvalid (subclasses de ParserError).
    """
    fn = parser_fn or _default_pymupdf_parser
    return fn(pdf_path)
