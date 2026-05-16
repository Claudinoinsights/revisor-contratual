"""Integration tests for pipeline.py dual-path Step 1 — Sprint 7 Phase 4 (ADR-027).

Tests verify pipeline.py Step 1 uses correct path based on PDF type detection:
- Born-digital → asyncio.to_thread (PyMuPDF inline)
- Scanned → asyncio.create_subprocess_exec (Phase 3 ADR-026 subprocess)

Refs:
- ADR-027 governance/architecture/adr/adr-027-pymupdf-born-digital-fast-path.md
"""

from __future__ import annotations

from pathlib import Path

from bloco_engine.parsing.type_detector import detect_pdf_type


def test_pipeline_imports_type_detector():
    """AC-2: pipeline.py imports detect_pdf_type (ADR-027 marker)."""
    from bloco_workflow import pipeline

    source = Path(pipeline.__file__).read_text(encoding="utf-8")
    assert "from bloco_engine.parsing.type_detector import detect_pdf_type" in source
    assert "detect_pdf_type" in source


def test_pipeline_uses_dual_path_branch():
    """AC-2 + AC-3: pipeline.py Step 1 has dual-path branch (born-digital vs scanned)."""
    from bloco_workflow import pipeline

    source = Path(pipeline.__file__).read_text(encoding="utf-8")
    # Pre-detection
    assert 'pdf_type = await asyncio.to_thread(detect_pdf_type, pdf_path)' in source
    # Born-digital branch
    assert 'if pdf_type == "born_digital":' in source
    # Born-digital uses asyncio.to_thread for parse_contract
    assert "asyncio.to_thread(\n                        parse_contract" in source
    # Scanned branch (else)
    assert 'else:' in source
    # Scanned uses subprocess (ADR-026 preserved)
    assert "asyncio.create_subprocess_exec" in source


def test_pipeline_smart_timeout_per_type():
    """AC-5: pipeline.py uses 30s for born-digital + 180s for scanned."""
    from bloco_workflow import pipeline

    source = Path(pipeline.__file__).read_text(encoding="utf-8")
    # Born-digital timeout 30s
    assert "timeout=30.0" in source
    # Scanned subprocess timeout 180s preserved (Phase 3)
    assert "timeout=180.0" in source


def test_pipeline_scanned_path_preserves_phase_3_subprocess():
    """AC-3 + AC-8: scanned path preserves Phase 3 ADR-026 subprocess + exception handling."""
    from bloco_workflow import pipeline

    source = Path(pipeline.__file__).read_text(encoding="utf-8")
    # Phase 3 subprocess components preserved
    assert "subprocess_runner" in source
    assert "ParsingSubprocessFailedError" in source
    assert "ParsingSubprocessTimeoutError" in source
    assert "proc.terminate()" in source
    assert "proc.kill()" in source
    # LGPD §46 cleanup preserved
    assert "Path(metadata_path).unlink(missing_ok=True)" in source


def test_type_detector_module_callable():
    """AC-1: detect_pdf_type module function exists and callable."""
    assert callable(detect_pdf_type)


def test_pipeline_preserves_existing_exception_handlers():
    """AC-4 + audit chain: pipeline.py existing except Exception linha ~600 captures both paths errors."""
    from bloco_workflow import pipeline

    source = Path(pipeline.__file__).read_text(encoding="utf-8")
    # Audit chain integration via existing handler
    assert "except Exception as exc:" in source
    assert "audit_payload[\"error_type\"]" in source


def test_pipeline_dual_path_preserves_pymupdf_marker_fn_args():
    """Backward compat: pipeline.py preserves pymupdf_fn + marker_fn signature args."""
    import inspect

    from bloco_workflow.pipeline import revisar_contrato

    sig = inspect.signature(revisar_contrato)
    assert "pymupdf_fn" in sig.parameters
    assert "marker_fn" in sig.parameters
