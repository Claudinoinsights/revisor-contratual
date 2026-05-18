"""Integration tests for Tesseract Direct parser — D-DEV-S08-013 (D-OPS-S08-028 fix).

Tests verify pdf2image + pytesseract direct pipeline replaces OCRmyPDF,
eliminating Ghostscript dependency that blocked Debian bookworm production.

Background:
- D-OPS-S08-026/028 (2026-05-18): Ghostscript 10.0.0 regression bloqueou OCRmyPDF
  em paths internos (image rendering, validation) mesmo com output_type='pdf'
  workaround D-DEV-S08-012.
- ULTRATHINK conclusion: OCRmyPDF depende fundamentalmente de Ghostscript.
  Cada workaround revela próximo path Ghostscript-dependent.
- Solução DEFINITIVA: eliminar OCRmyPDF, usar pdf2image (poppler-utils, sem gs)
  + pytesseract direto.

Refs:
- ADR-034 (replaces ADR-033 OCRmyPDF) — ZERO Ghostscript dependency
- D-DEV-S08-013 (this fix)
- D-OPS-S08-028 (empirical detection — OCRmyPDF + Ghostscript dead end)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bloco_engine.parsing.marker_parser import ParserOCRRequired
from bloco_engine.parsing.tesseract_direct_parser import (
    parse_pdf_tesseract_direct,
    _is_tesseract_direct_available,
)

pytestmark = [pytest.mark.integration]


# ─────────────────────────────────────────────────────────────────────
# Source review tests
# ─────────────────────────────────────────────────────────────────────


def test_tesseract_direct_module_zero_ghostscript_reference():
    """D-DEV-S08-013: tesseract_direct_parser.py must NOT reference Ghostscript."""
    from bloco_engine.parsing import tesseract_direct_parser

    source = Path(tesseract_direct_parser.__file__).read_text(encoding="utf-8")
    # Module should explicitly state ZERO Ghostscript dependency
    assert "ZERO" in source or "sem Ghostscript" in source, (
        "Module docstring should highlight Ghostscript elimination (D-OPS-S08-028)"
    )
    # No imports of ocrmypdf
    assert "import ocrmypdf" not in source, (
        "tesseract_direct must NOT import ocrmypdf (eliminates Ghostscript dep chain)"
    )


def test_orchestrator_uses_tesseract_direct_when_no_marker_fn():
    """D-DEV-S08-013: orchestrator default OCR path is tesseract_direct."""
    from bloco_engine.parsing import orchestrator

    source = Path(orchestrator.__file__).read_text(encoding="utf-8")
    assert "parse_pdf_tesseract_direct(pdf_path)" in source, (
        "orchestrator must call parse_pdf_tesseract_direct as default OCR path"
    )
    assert 'parser_used = "tesseract_direct"' in source, (
        "parser_used must be tagged 'tesseract_direct' when used"
    )


def test_parsed_contract_accepts_tesseract_direct_parser_used():
    """D-DEV-S08-013: ParsedContract.parser_used Literal includes tesseract_direct."""
    from bloco_contratos.contrato import ParsedContract

    field_info = ParsedContract.model_fields["parser_used"]
    annotation_str = str(field_info.annotation)
    assert "tesseract_direct" in annotation_str, (
        f"parser_used Literal must accept 'tesseract_direct', got: {annotation_str}"
    )


def test_pyproject_ocr_extras_includes_pytesseract():
    """D-DEV-S08-013: pyproject.toml [project.optional-dependencies].ocr lists pytesseract."""
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    content = pyproject_path.read_text(encoding="utf-8")
    assert "pytesseract" in content, "pyproject.toml ocr extras must include pytesseract"


# ─────────────────────────────────────────────────────────────────────
# Runtime tests
# ─────────────────────────────────────────────────────────────────────


def test_parse_pdf_tesseract_direct_raises_if_not_installed(tmp_path, monkeypatch):
    """D-DEV-S08-013: ParserOCRRequired raised se pdf2image OR pytesseract missing."""
    from bloco_engine.parsing import tesseract_direct_parser

    monkeypatch.setattr(
        tesseract_direct_parser, "_is_tesseract_direct_available", lambda: False
    )

    pdf_path = tmp_path / "fake.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    with pytest.raises(ParserOCRRequired) as exc_info:
        parse_pdf_tesseract_direct(pdf_path)

    error_msg = str(exc_info.value)
    assert "OCR" in error_msg, "Error must mention OCR in user-facing message"
    assert "pip install" in error_msg, (
        "Error must include actionable installation instructions"
    )


def test_parse_pdf_tesseract_direct_accepts_parser_fn_injection(tmp_path):
    """D-DEV-S08-013: parser_fn injection for testability (consistent pattern)."""
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    def _mock_parser(p: Path) -> tuple[str, int]:
        return ("Mock markdown content from injected parser", 1)

    markdown, pages = parse_pdf_tesseract_direct(pdf_path, parser_fn=_mock_parser)
    assert markdown == "Mock markdown content from injected parser"
    assert pages == 1
