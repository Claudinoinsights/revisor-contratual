"""Unit tests for bloco_engine.parsing.type_detector — Sprint 7 Phase 4 (ADR-027).

Tests PDF type detection (born-digital vs scanned) via PyMuPDF heuristic.

Refs:
- ADR-027 governance/architecture/adr/adr-027-pymupdf-born-digital-fast-path.md
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
import pytest

from bloco_engine.parsing.type_detector import detect_pdf_type


@pytest.fixture
def born_digital_pdf(tmp_path):
    """Generate a born-digital PDF inline via PyMuPDF (text-extractable)."""
    pdf_path = tmp_path / "born_digital.pdf"
    doc = fitz.open()
    page = doc.new_page()
    # Insert >500 chars text (above threshold)
    text = (
        "CONTRATO DE FINANCIAMENTO DE VEÍCULO — CRÉDITO DIRETO AO CONSUMIDOR\n"
        "Modalidade: CDC_VEICULOS_PF\n"
        "Valor financiado: R$ 50.000,00\n"
        "Taxa de juros mensal: 1,99%\n"
        "Prazo: 60 meses\n"
        "Cliente: João Silva — CPF 123.456.789-00\n"
        "Bem: Veículo Honda Civic 2023, placa ABC-1234\n"
        "Garantia: alienação fiduciária do veículo objeto do contrato\n"
        "Foro de eleição: Comarca de São Paulo, Estado de São Paulo\n"
        "Data de assinatura: 2025-12-01\n"
    ) * 2  # ~1200 chars total — well above 500 threshold
    page.insert_text((50, 50), text)
    doc.save(pdf_path)
    doc.close()
    return pdf_path


@pytest.fixture
def scanned_pdf(tmp_path):
    """Generate a scanned-style PDF inline (image-only, no text layer)."""
    pdf_path = tmp_path / "scanned.pdf"
    doc = fitz.open()
    # Empty page (no text inserted) simulates scanned PDF without text layer
    doc.new_page()
    doc.new_page()
    doc.save(pdf_path)
    doc.close()
    return pdf_path


@pytest.fixture
def empty_pdf(tmp_path):
    """Generate an empty PDF (0 pages)."""
    pdf_path = tmp_path / "empty.pdf"
    doc = fitz.open()
    doc.save(pdf_path)
    doc.close()
    return pdf_path


@pytest.fixture
def single_page_born_digital(tmp_path):
    """Generate single-page born-digital PDF (multiline text fits page)."""
    pdf_path = tmp_path / "single_born.pdf"
    doc = fitz.open()
    page = doc.new_page()
    # 30 lines × 30 chars = 900 chars (above 500 threshold, fits standard A4)
    text = "\n".join(["Linha " + str(i) + " texto contrato CDC veiculo PF" for i in range(30)])
    page.insert_text((50, 50), text)
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def test_detect_born_digital_pdf(born_digital_pdf):
    """AC-1: PDF with substantial text → born_digital."""
    assert detect_pdf_type(born_digital_pdf) == "born_digital"


def test_detect_scanned_pdf(scanned_pdf):
    """AC-1: PDF without text layer → scanned."""
    assert detect_pdf_type(scanned_pdf) == "scanned"


def test_detect_empty_pdf(empty_pdf):
    """Edge case: empty PDF (0 pages) → scanned."""
    assert detect_pdf_type(empty_pdf) == "scanned"


def test_detect_single_page_born_digital(single_page_born_digital):
    """Edge case: single-page PDF samples only that page."""
    assert detect_pdf_type(single_page_born_digital) == "born_digital"


def test_detect_corrupt_pdf_returns_scanned(tmp_path):
    """Edge case: corrupt PDF → scanned (defer to subprocess fallback)."""
    corrupt = tmp_path / "corrupt.pdf"
    corrupt.write_bytes(b"%PDF-1.4\n" + b"\x00" * 50)  # Invalid PDF
    assert detect_pdf_type(corrupt) == "scanned"


def test_detect_threshold_calibration(tmp_path):
    """Threshold customization works."""
    pdf_path = tmp_path / "moderate.pdf"
    doc = fitz.open()
    page = doc.new_page()
    # 10 lines × 30 chars = ~300 chars total per page
    text = "\n".join(["Linha curta texto " + str(i) for i in range(10)])
    page.insert_text((50, 50), text)
    doc.save(pdf_path)
    doc.close()

    # Default threshold 500 → scanned (300 < 500)
    assert detect_pdf_type(pdf_path) == "scanned"
    # Custom threshold 100 → born_digital (300 > 100)
    assert detect_pdf_type(pdf_path, text_threshold_per_page=100) == "born_digital"


def test_detect_sample_pages_default_2():
    """Function signature: sample_pages defaults to 2."""
    import inspect
    sig = inspect.signature(detect_pdf_type)
    assert sig.parameters["sample_pages"].default == 2
