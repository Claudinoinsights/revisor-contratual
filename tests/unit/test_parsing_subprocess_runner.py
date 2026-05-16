"""Unit tests for bloco_engine.parsing.subprocess_runner — Sprint 7 Phase 3 (ADR-026).

Tests subprocess_runner CLI standalone behavior:
- AC-1: Born-digital PDF returns valid JSON ParsedContract
- AC-4: Corrupt PDF returns error JSON em stderr + exit code 1
- Usage error scenarios (bad argv + missing files)

Refs:
- ADR-026 governance/architecture/adr/adr-026-marker-subprocess-isolation-parsing.md
- handoff-architect-to-dev-2026-05-15-sprint-7-phase-3-subprocess-implementation.yaml
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


# Existing real PDF para born-digital test (se disponível em documentos-para-teste)
REAL_PDF_PATH = Path(
    "documentos-para-teste/Financiamento Veiculo/Contrato Financiamento Veículo.pdf"
)


@pytest.fixture
def metadata_json(tmp_path):
    """Cria arquivo metadata.json minimal para subprocess_runner argv."""
    metadata_file = tmp_path / "metadata.json"
    metadata_file.write_text(
        json.dumps({"uf_override": "SP", "data_override": "2025-12-01"})
    )
    return metadata_file


@pytest.fixture
def corrupt_pdf(tmp_path):
    """Cria PDF corrupto (100 bytes truncated) para testar error handling."""
    corrupt_file = tmp_path / "corrupt.pdf"
    # PDF magic bytes seguidos de bytes truncated — invalid PDF structure
    corrupt_file.write_bytes(
        b"%PDF-1.4\n" + b"\x00" * 80 + b"%%EOF"
    )
    return corrupt_file


def test_subprocess_runner_usage_error_no_args():
    """AC: subprocess_runner returns exit 2 sem args."""
    result = subprocess.run(
        [sys.executable, "-m", "bloco_engine.parsing.subprocess_runner"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    assert "ERROR: usage" in result.stderr


def test_subprocess_runner_pdf_not_found(metadata_json, tmp_path):
    """AC-4: subprocess_runner returns error JSON quando PDF não existe."""
    nonexistent_pdf = tmp_path / "nonexistent.pdf"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "bloco_engine.parsing.subprocess_runner",
            str(nonexistent_pdf),
            str(metadata_json),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    error = json.loads(result.stderr)
    assert error["error_type"] == "PDFNotFound"
    assert "nonexistent.pdf" in error["error_msg"]


def test_subprocess_runner_metadata_not_found(corrupt_pdf, tmp_path):
    """AC: subprocess_runner returns error JSON quando metadata.json não existe."""
    nonexistent_metadata = tmp_path / "nonexistent_metadata.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "bloco_engine.parsing.subprocess_runner",
            str(corrupt_pdf),
            str(nonexistent_metadata),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    error = json.loads(result.stderr)
    assert error["error_type"] == "MetadataFileNotFound"


def test_subprocess_runner_corrupt_pdf_error(corrupt_pdf, metadata_json):
    """AC-4: subprocess_runner returns error JSON em stderr para corrupt PDF."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "bloco_engine.parsing.subprocess_runner",
            str(corrupt_pdf),
            str(metadata_json),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    # Exit code 1 (Python exception caught) — stderr contém error JSON
    assert result.returncode == 1
    error = json.loads(result.stderr)
    assert "error_type" in error
    assert "error_msg" in error
    # Não pode ser PDFNotFound (PDF existe, mas é corrupt)
    assert error["error_type"] != "PDFNotFound"


@pytest.mark.skipif(
    not REAL_PDF_PATH.exists(),
    reason="Real PDF fixture not available (documentos-para-teste/...)",
)
def test_subprocess_runner_real_pdf_success(metadata_json):
    """AC-1: subprocess_runner returns valid JSON ParsedContract para real PDF.

    SLOW test (pode demorar 30-90s para Marker OCR PDF imagem).
    Skipped se PDF fixture não disponível.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "bloco_engine.parsing.subprocess_runner",
            str(REAL_PDF_PATH),
            str(metadata_json),
        ],
        capture_output=True,
        text=True,
        timeout=180,  # match production subprocess timeout
    )
    assert result.returncode == 0, f"stderr: {result.stderr[:500]}"
    parsed = json.loads(result.stdout)
    # ParsedContract schema validation
    assert "metadata" in parsed
    assert "markdown_extracted" in parsed
    assert "parser_used" in parsed
    assert "pages_count" in parsed
    assert parsed["pages_count"] >= 1


def test_subprocess_runner_invalid_metadata_json(corrupt_pdf, tmp_path):
    """AC: subprocess_runner returns error se metadata.json não é JSON válido."""
    bad_metadata = tmp_path / "bad_metadata.json"
    bad_metadata.write_text("not valid json {{{")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "bloco_engine.parsing.subprocess_runner",
            str(corrupt_pdf),
            str(bad_metadata),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    error = json.loads(result.stderr)
    assert error["error_type"] == "JSONDecodeError"
