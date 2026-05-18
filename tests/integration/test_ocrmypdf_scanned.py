"""Integration tests for OCRmyPDF parser — D-DEV-S08-008 fix (D-OPS-S08-016 hardware limit).

Tests verify OCRmyPDF replacement of Marker for low-memory scanned OCR:
- Source review: orchestrator uses parse_pdf_ocrmypdf when fidelity low
- Source review: contract Literal accepts ocrmypdf_tesseract parser_used
- Runtime guard: parse_pdf_ocrmypdf raises ParserOCRRequired if not installed
- Runtime (skip if ocrmypdf not installed): end-to-end scanned PDF → markdown

Background:
- D-OPS-S08-016 (2026-05-17): Operator confirmed VPS 7.8GB RAM insufficient
  for Marker CPU layout inference (OOM SIGKILL 2x reproduced).
- Eric chose Option A: OCRmyPDF (Tesseract wrapper, ~600MB RAM vs Marker 4-6GB).
- Architectural advantage: OCRmyPDF adds text layer → PyMuPDF dual-path (ADR-027)
  reusable integralmente — minimal architectural disruption.

Refs:
- ADR-033 governance/architecture/adr/adr-033-ocrmypdf-replace-marker.md
- D-OPS-S08-016 hardware limit catalog
- D-DEV-S08-008 this fix
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bloco_engine.parsing.marker_parser import ParserOCRRequired
from bloco_engine.parsing.ocrmypdf_parser import (
    parse_pdf_ocrmypdf,
    _is_ocrmypdf_available,
)

pytestmark = [pytest.mark.integration]


# ─────────────────────────────────────────────────────────────────────
# Source review tests
# ─────────────────────────────────────────────────────────────────────


def test_orchestrator_imports_ocrmypdf_parser():
    """D-DEV-S08-008: orchestrator.py imports parse_pdf_ocrmypdf."""
    from bloco_engine.parsing import orchestrator

    source = Path(orchestrator.__file__).read_text(encoding="utf-8")
    assert "from bloco_engine.parsing.ocrmypdf_parser import parse_pdf_ocrmypdf" in source, (
        "orchestrator must import OCRmyPDF parser (ADR-033 D-DEV-S08-008)"
    )


def test_orchestrator_keeps_ocrmypdf_as_emergency_rollback_import():
    """ADR-034 D-DEV-S08-013: orchestrator default mudou para tesseract_direct,
    mas mantém import de parse_pdf_ocrmypdf como emergency rollback (noqa F401)."""
    from bloco_engine.parsing import orchestrator

    source = Path(orchestrator.__file__).read_text(encoding="utf-8")
    # OCRmyPDF preserved como import emergency rollback (ADR-033 → ADR-034 transition)
    assert "parse_pdf_ocrmypdf" in source, (
        "orchestrator must keep parse_pdf_ocrmypdf import (emergency rollback per ADR-034)"
    )
    assert "deprecated emergency rollback" in source or "ADR-034" in source, (
        "Import must be marked as deprecated/rollback for clarity"
    )


def test_parsed_contract_accepts_ocrmypdf_tesseract_parser_used():
    """D-DEV-S08-008: ParsedContract.parser_used Literal includes ocrmypdf_tesseract."""
    from bloco_contratos.contrato import ParsedContract

    # Pydantic v2 — check via model_fields metadata
    field_info = ParsedContract.model_fields["parser_used"]
    # The Literal type appears in field annotation
    annotation_str = str(field_info.annotation)
    assert "ocrmypdf_tesseract" in annotation_str, (
        f"parser_used Literal must accept 'ocrmypdf_tesseract', got: {annotation_str}"
    )


def test_pyproject_ocr_extras_includes_ocrmypdf():
    """D-DEV-S08-008: pyproject.toml [project.optional-dependencies].ocr lists ocrmypdf."""
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    content = pyproject_path.read_text(encoding="utf-8")
    assert "ocrmypdf" in content, "pyproject.toml ocr extras must include ocrmypdf"
    assert 'ocr = [' in content, "ocr extras section must exist"


# ─────────────────────────────────────────────────────────────────────
# Runtime tests
# ─────────────────────────────────────────────────────────────────────


def test_parse_pdf_ocrmypdf_raises_if_not_installed(tmp_path, monkeypatch):
    """D-DEV-S08-008: ParserOCRRequired raised with helpful PT-BR message if ocrmypdf missing.

    Simulates ocrmypdf not installed via monkeypatch of _is_ocrmypdf_available.
    """
    from bloco_engine.parsing import ocrmypdf_parser

    # Force "not available" state
    monkeypatch.setattr(
        ocrmypdf_parser, "_is_ocrmypdf_available", lambda: False
    )

    # Create dummy PDF (won't be processed since ocrmypdf "not available")
    pdf_path = tmp_path / "fake.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    with pytest.raises(ParserOCRRequired) as exc_info:
        parse_pdf_ocrmypdf(pdf_path)

    error_msg = str(exc_info.value)
    assert "OCRmyPDF" in error_msg or "OCR" in error_msg, (
        "Error must mention OCR/OCRmyPDF in user-facing message"
    )
    assert "pip install" in error_msg, (
        "Error must include actionable installation instructions"
    )


def test_parse_pdf_ocrmypdf_accepts_parser_fn_injection(tmp_path):
    """D-DEV-S08-008: parser_fn injection for testability (consistent with marker_parser)."""
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    def _mock_parser(p: Path) -> tuple[str, int]:
        return ("Mock markdown content from injected parser", 1)

    markdown, pages = parse_pdf_ocrmypdf(pdf_path, parser_fn=_mock_parser)
    assert markdown == "Mock markdown content from injected parser"
    assert pages == 1


@pytest.mark.skipif(
    not _is_ocrmypdf_available(),
    reason="ocrmypdf not installed (only available in production container with [ocr] extras)",
)
def test_parse_pdf_ocrmypdf_end_to_end_scanned(tmp_path):
    """D-DEV-S08-008: scanned PDF → OCRmyPDF + PyMuPDF → markdown not empty.

    Only runs in environments with ocrmypdf installed (skipped in test envs without [ocr]).
    """
    import fitz
    from PIL import Image, ImageDraw

    # Create scanned PDF (image only, no text layer)
    img = Image.new("RGB", (1240, 1754), "white")
    draw = ImageDraw.Draw(img)
    draw.text((100, 100), "TESTE OCR CONTRATO CDC VEICULOS", fill="black")
    draw.text((100, 200), "Valor R$ 35000 48 parcelas 1.89am", fill="black")

    png_path = tmp_path / "scan.png"
    img.save(png_path, "PNG", dpi=(150, 150))

    pdf_path = tmp_path / "scanned.pdf"
    pdf = fitz.open()
    page = pdf.new_page(width=595, height=842)
    page.insert_image(page.rect, filename=str(png_path))
    pdf.save(str(pdf_path))
    pdf.close()

    # Verify scanned (zero text layer)
    verify = fitz.open(str(pdf_path))
    assert len(verify[0].get_text()) == 0, "Fixture must be scanned (no text layer)"
    verify.close()

    # Run OCRmyPDF + PyMuPDF pipeline
    markdown, pages_count = parse_pdf_ocrmypdf(pdf_path)
    assert pages_count == 1, f"Expected 1 page, got {pages_count}"
    assert len(markdown) > 0, f"Markdown must not be empty after OCR, got: {markdown!r}"
    # Loose assertion — OCR quality varies but should detect at least some keywords
    markdown_lower = markdown.lower()
    has_some_recognizable_text = any(
        kw in markdown_lower for kw in ["teste", "ocr", "contrato", "cdc", "veiculos", "valor", "parcelas"]
    )
    assert has_some_recognizable_text, (
        f"OCR should extract at least 1 recognizable keyword from markdown: {markdown[:300]!r}"
    )
