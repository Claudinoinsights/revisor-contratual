"""Integration tests for subprocess_runner stdout isolation — D-DEV-S08-005 fix (D-OPS-S08-010 empirical).

Tests verify subprocess_runner.py isolates marker library stdout noise so that
only the final JSON ParsedContract reaches the parent worker.

Background:
- D-OPS-S08-010 (2026-05-17): Operator empirical E2E test with scanned PDF revealed
  marker library prints "=== Document parser messages ===" + progress bars to stdout
  BEFORE the final `print(parsed.model_dump_json())`. Parent worker pipeline.py
  fails with Pydantic ValidationError: "Invalid JSON: expected value at line 1
  column 1, input_value='=== Document parser mess...{...}'".
- Fix: contextlib.redirect_stdout(io.StringIO()) wraps parse_contract call.
  Only final JSON line reaches stdout.

Refs:
- ADR-026 governance/architecture/adr/adr-026-marker-subprocess-isolation-parsing.md
- D-OPS-S08-010 governance/CHECKPOINT-active.md Sessão 2026-05-17 Operator E2E test
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Source-code review tests (consistent with test_pipeline_subprocess.py pattern)
# ─────────────────────────────────────────────────────────────────────────────


def test_subprocess_runner_imports_contextlib_and_io():
    """D-DEV-S08-005: subprocess_runner.py imports contextlib + io for stdout isolation."""
    from bloco_engine.parsing import subprocess_runner

    source = Path(subprocess_runner.__file__).read_text(encoding="utf-8")
    assert "import contextlib" in source, (
        "subprocess_runner.py must import contextlib for redirect_stdout (D-DEV-S08-005 fix)"
    )
    assert "import io" in source, (
        "subprocess_runner.py must import io for StringIO sink (D-DEV-S08-005 fix)"
    )


def test_subprocess_runner_wraps_parse_contract_in_redirect_stdout():
    """D-DEV-S08-005: parse_contract call wrapped in contextlib.redirect_stdout sink.

    Marker library + surya print diagnostic messages to stdout. Without isolation,
    these contaminate JSON output → Pydantic ValidationError em parent worker.
    """
    from bloco_engine.parsing import subprocess_runner

    source = Path(subprocess_runner.__file__).read_text(encoding="utf-8")
    assert "contextlib.redirect_stdout(io.StringIO())" in source, (
        "parse_contract call must be wrapped in contextlib.redirect_stdout(io.StringIO()) "
        "to isolate marker library stdout noise (D-OPS-S08-010 root cause)"
    )


def test_subprocess_runner_final_print_after_redirect_block():
    """D-DEV-S08-005: print(parsed.model_dump_json()) must execute AFTER redirect_stdout block.

    Source review verification — final JSON print must be outside the `with`
    block to reach real stdout (not the StringIO sink).
    """
    from bloco_engine.parsing import subprocess_runner

    source = Path(subprocess_runner.__file__).read_text(encoding="utf-8")
    # Find order: contextlib.redirect_stdout block, then print(parsed.model_dump_json())
    redirect_pos = source.find("contextlib.redirect_stdout(io.StringIO())")
    final_print_pos = source.find("print(parsed.model_dump_json())")

    assert redirect_pos > 0, "redirect_stdout block must exist"
    assert final_print_pos > 0, "final print(parsed.model_dump_json()) must exist"
    assert final_print_pos > redirect_pos, (
        "print(parsed.model_dump_json()) must execute AFTER redirect_stdout block "
        "(must reach real stdout, not StringIO sink)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Runtime smoke test — execute subprocess_runner end-to-end with noisy parser
# ─────────────────────────────────────────────────────────────────────────────


def _create_minimal_born_digital_pdf(path: Path) -> None:
    """Generate minimal born-digital PDF via PyMuPDF (avoids fpdf2 dependency).

    Born-digital PDF (text layer present) → pipeline uses PyMuPDF path (no marker).
    Sufficient to test stdout isolation contract (any parse_contract call works).
    """
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 points
    text = (
        "CONTRATO DE CREDITO DIRETO AO CONSUMIDOR\n"
        "CDC VEICULOS - PESSOA FISICA\n"
        "\n"
        "Local: Sao Paulo, SP\n"
        "Data: 15 de maio de 2025\n"
        "\n"
        "Valor financiado: R$ 35.000,00\n"
        "Numero de parcelas: 48\n"
        "Taxa de juros: 1,89% a.m.\n"
        "Modalidade: CDC_VEICULOS_PF\n"
    )
    page.insert_text((72, 72), text, fontsize=11)
    doc.save(str(path))
    doc.close()


@pytest.mark.integration
def test_subprocess_runner_stdout_is_pure_json(tmp_path):
    """D-DEV-S08-005 runtime: subprocess_runner stdout MUST be parseable as pure JSON.

    Executes subprocess_runner as real subprocess (mimics pipeline.py invocation)
    and asserts stdout starts with `{` and parses as valid JSON (no contamination
    from parse_contract internal prints).

    NOTE: Uses born-digital PDF (PyMuPDF path) — sufficient to test contract.
    Scanned PDF (marker path) would also work but adds runtime cost (~30s OCR)
    and depends on marker library installed in test env. Born-digital test is
    necessary AND sufficient for stdout isolation contract verification.
    """
    pdf_path = tmp_path / "test_contract.pdf"
    _create_minimal_born_digital_pdf(pdf_path)

    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        json.dumps({"uf_override": "SP", "data_override": "2025-05-15"}),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "bloco_engine.parsing.subprocess_runner",
            str(pdf_path),
            str(metadata_path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )

    # Exit code MUST be 0 (success path)
    assert result.returncode == 0, (
        f"subprocess_runner failed: exit={result.returncode} "
        f"stderr={result.stderr[:500]}"
    )

    # Stdout MUST be parseable as JSON (no contamination)
    stdout_clean = result.stdout.strip()
    assert stdout_clean.startswith("{"), (
        f"subprocess_runner stdout MUST start with '{{' (pure JSON). "
        f"D-OPS-S08-010 detected contamination: '{stdout_clean[:200]}'"
    )

    try:
        parsed = json.loads(stdout_clean)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"subprocess_runner stdout is NOT valid JSON (D-OPS-S08-010 regression): "
            f"{exc}\nstdout: {stdout_clean[:500]}"
        )

    # Validate it looks like ParsedContract structure
    assert "metadata" in parsed, "JSON should contain 'metadata' key (ParsedContract)"
    assert "markdown_extracted" in parsed, "JSON should contain 'markdown_extracted' key"
    assert "parser_used" in parsed, "JSON should contain 'parser_used' key"


@pytest.mark.integration
def test_subprocess_runner_isolates_noisy_stdout(tmp_path, monkeypatch):
    """D-DEV-S08-005 fault-injection: simulates parse_contract printing noise.

    Monkeypatches parse_contract to print noise to stdout (mimics marker library
    behavior). Without redirect_stdout, parent worker would see contamination.
    With fix, stdout MUST contain only the final JSON.
    """
    from bloco_contratos.contrato import ContratoMetadata, ParsedContract
    from bloco_engine.parsing import subprocess_runner

    # Mock parse_contract to simulate marker library stdout noise
    def noisy_parse_contract(pdf_path, **kwargs):
        # This is exactly what marker library does — vazem para stdout
        print("=== Document parser messages ===")
        print("Recognizing layout: 100%|##########|")
        print("Processing pages: 100%|##########|")

        # Return minimal valid ParsedContract
        from datetime import date, datetime
        return ParsedContract(
            metadata=ContratoMetadata(
                contract_hash="a" * 64,
                uf_contrato="SP",
                data_assinatura=date(2025, 5, 15),
                modalidade="CDC_VEICULOS_PF",
                valor_financiado="35000.00",
                n_parcelas=48,
                taxa_contratual_am="1.89",
                taxa_contratual_aa=None,
            ),
            markdown_extracted="Test markdown content",
            parser_used="pymupdf4llm",
            parsed_at=datetime.now(),
            pages_count=1,
            fidelity_score=0.7,
        )

    monkeypatch.setattr(subprocess_runner, "parse_contract", noisy_parse_contract)

    # Capture stdout via subprocess (real isolation test)
    pdf_path = tmp_path / "fake.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake content")  # subprocess_runner only checks is_file()
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text("{}")

    # Patch sys.argv + invoke main() directly (in-process to use monkeypatched fn)
    import io
    import contextlib

    captured_stdout = io.StringIO()
    monkeypatch.setattr(sys, "argv", [
        "subprocess_runner",
        str(pdf_path),
        str(metadata_path),
    ])

    with contextlib.redirect_stdout(captured_stdout):
        exit_code = subprocess_runner.main()

    assert exit_code == 0, "main() should return 0 on success"

    stdout_text = captured_stdout.getvalue().strip()

    # Critical assertion: stdout MUST NOT contain marker noise
    assert "=== Document parser messages ===" not in stdout_text, (
        "Marker stdout noise leaked into output — redirect_stdout fix not working "
        f"(D-OPS-S08-010 regression): {stdout_text[:300]}"
    )
    assert "Recognizing layout" not in stdout_text, (
        "Progress bar noise leaked into output (D-OPS-S08-010 regression)"
    )

    # Stdout MUST be pure JSON
    assert stdout_text.startswith("{"), (
        f"stdout should start with '{{' (pure JSON), got: {stdout_text[:200]}"
    )
    parsed = json.loads(stdout_text)
    assert parsed["fidelity_score"] == 0.7, "JSON content preserved correctly"
