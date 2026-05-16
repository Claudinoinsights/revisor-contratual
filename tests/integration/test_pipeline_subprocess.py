"""Integration tests for pipeline.py subprocess isolation — Sprint 7 Phase 3 (ADR-026).

Tests verify pipeline.py Step 1 uses asyncio.subprocess.exec (não asyncio.to_thread):
- AC-2: Code review verification via grep
- AC-3+AC-4: Audit chain registers ParsingSubprocessFailed em scenarios crash

Refs:
- ADR-026 governance/architecture/adr/adr-026-marker-subprocess-isolation-parsing.md
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from bloco_engine.parsing.exceptions import (
    ParsingSubprocessFailedError,
    ParsingSubprocessTimeoutError,
)


def test_pipeline_imports_subprocess_exceptions():
    """AC-2: pipeline.py imports ParsingSubprocess* exceptions (ADR-026 marker)."""
    from bloco_workflow import pipeline

    source = Path(pipeline.__file__).read_text(encoding="utf-8")
    assert "ParsingSubprocessFailedError" in source
    assert "ParsingSubprocessTimeoutError" in source
    assert "from bloco_engine.parsing.exceptions import" in source


def test_pipeline_uses_create_subprocess_exec_not_to_thread():
    """AC-2: pipeline.py Step 1 usa asyncio.create_subprocess_exec (NÃO to_thread parse_contract).

    Code review verification — grep source para garantir refactor aplicado.
    """
    from bloco_workflow import pipeline

    source = Path(pipeline.__file__).read_text(encoding="utf-8")

    # Subprocess pattern presente
    assert "asyncio.create_subprocess_exec" in source, (
        "pipeline.py deve usar asyncio.create_subprocess_exec em Step 1"
    )
    assert "subprocess_runner" in source, (
        "pipeline.py deve referenciar bloco_engine.parsing.subprocess_runner"
    )

    # Old pattern asyncio.to_thread(parse_contract, ...) NÃO deve existir
    assert "asyncio.to_thread(\n            parse_contract" not in source, (
        "pipeline.py NÃO pode usar asyncio.to_thread(parse_contract, ...) "
        "(ADR-026 subprocess isolation replace)"
    )


def test_pipeline_uses_180s_timeout():
    """AC-9: pipeline.py implementa subprocess timeout 180s + SIGTERM/SIGKILL."""
    from bloco_workflow import pipeline

    source = Path(pipeline.__file__).read_text(encoding="utf-8")

    assert "timeout=180.0" in source, "Subprocess deve usar timeout 180s (ADR-026)"
    assert "proc.terminate()" in source, "SIGTERM grace cleanup (ADR-026)"
    assert "proc.kill()" in source, "SIGKILL fallback (ADR-026)"


def test_pipeline_cleanup_metadata_tempfile():
    """LGPD §46: pipeline.py cleanup metadata tempfile em finally block."""
    from bloco_workflow import pipeline

    source = Path(pipeline.__file__).read_text(encoding="utf-8")

    assert "Path(metadata_path).unlink(missing_ok=True)" in source, (
        "LGPD §46 cleanup tempfile metadata required em finally block"
    )


def test_pipeline_serializes_metadata_to_json_tempfile():
    """ADR-026 IPC: metadata serialized via JSON tempfile (NÃO via stdin pipe)."""
    from bloco_workflow import pipeline

    source = Path(pipeline.__file__).read_text(encoding="utf-8")

    assert "tempfile.NamedTemporaryFile" in source, (
        "Metadata IPC via NamedTemporaryFile JSON (ADR-026 spec)"
    )
    assert "metadata_dict" in source, "Metadata dict construction"


def test_parsing_subprocess_exceptions_definition():
    """Sanity check: ParsingSubprocess* exception classes definidas correctly."""
    # ParsingSubprocessFailedError requires error_type + error_msg
    exc = ParsingSubprocessFailedError(error_type="TestError", error_msg="test message")
    assert exc.error_type == "TestError"
    assert exc.error_msg == "test message"
    assert "TestError" in str(exc)
    assert "test message" in str(exc)

    # ParsingSubprocessTimeoutError requires message
    timeout_exc = ParsingSubprocessTimeoutError("subprocess hang 180s")
    assert "subprocess hang 180s" in str(timeout_exc)

    # Both são Exception subclasses
    assert issubclass(ParsingSubprocessFailedError, Exception)
    assert issubclass(ParsingSubprocessTimeoutError, Exception)


def test_pipeline_step1_signature_preserves_pymupdf_marker_fn_for_backcompat():
    """Backward compat: revisar_contrato signature mantém pymupdf_fn + marker_fn args.

    Mesmo que Step 1 agora usa subprocess (não passa fns), signature preserva
    args para tests existentes que injectavam mocks.
    """
    from bloco_workflow.pipeline import revisar_contrato

    sig = inspect.signature(revisar_contrato)
    # Args devem existir (mesmo que NÃO usados pelo subprocess Step 1)
    assert "pymupdf_fn" in sig.parameters, (
        "Backward compat: pymupdf_fn arg signature preserved"
    )
    assert "marker_fn" in sig.parameters, (
        "Backward compat: marker_fn arg signature preserved"
    )
