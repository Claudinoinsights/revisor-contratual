"""Integration tests for LGPD §16 tempfile cleanup — Sprint 8 Story #1.5.

Smith F-CRIT-02 empirical: POST /revisar cria PDF tempfile via mkstemp() em /tmp/.
Cleanup só acontece em finally dos SSE generators (revisar_stream + pipeline_stream).
Se user POST mas nunca conecta SSE → PDF orphaned indefinidamente em /tmp/.

Fix: _schedule_pdf_safety_cleanup background task agendado em POST /revisar checa
após N=600s (default) — se JOB ainda queued/running, cleanup PDF + remove JOB.
Plus lifespan shutdown cleanup ALL JOBS PDFs remaining.

Refs:
- Smith ultrathink F-CRIT-02 governance/qa/smith-ultrathink-aplicacao-completa-hardware-2026-05-16.md
- handoff-devops-to-dev-2026-05-16-sprint-8-phase-a-stories-1-5-1-6-code.yaml
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from bloco_interface.web.app import (
    JOBS,
    _schedule_pdf_safety_cleanup,
)


@pytest.fixture(autouse=True)
def _clean_jobs_dict():
    """Reset JOBS dict before/after each test (isolation)."""
    JOBS.clear()
    yield
    JOBS.clear()


def _create_orphan_pdf_tmpfile() -> str:
    """Helper: create real tempfile.mkstemp PDF (mimics app.py:868 pattern)."""
    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
    import os
    with os.fdopen(fd, "wb") as f:
        f.write(b"%PDF-1.4\n%fake test pdf content\n%%EOF\n")
    return pdf_path


@pytest.mark.asyncio
async def test_safety_cleanup_removes_orphan_pdf_if_job_queued():
    """AC-3: PDF orphan (stream nunca consumido) é removido após safety wait."""
    pdf_path = _create_orphan_pdf_tmpfile()
    assert Path(pdf_path).exists(), "fixture should create real PDF tempfile"

    job_id = "test-orphan-queued"
    JOBS[job_id] = {
        "status": "queued",  # SSE stream nunca consumido
        "pdf_path": pdf_path,
        "tier": "balanced",
    }

    # Trigger safety cleanup com delay=0 (skip 600s wait para test)
    await _schedule_pdf_safety_cleanup(job_id, delay_seconds=0)

    assert not Path(pdf_path).exists(), "PDF should be cleaned up by safety net"
    assert job_id not in JOBS, "JOB entry should be removed post-cleanup"


@pytest.mark.asyncio
async def test_safety_cleanup_skips_when_status_completed():
    """AC-4: Safety cleanup NÃO mexe se SSE generator finally já fired (status=completed).

    Caso SSE stream foi consumed e finally cleanup já rodou, status muda para
    'completed' OR 'error'. Safety cleanup deve skip (PDF já removido).
    """
    pdf_path = _create_orphan_pdf_tmpfile()

    job_id = "test-completed-skip"
    JOBS[job_id] = {
        "status": "completed",  # SSE generator finally fired
        "pdf_path": pdf_path,
    }

    await _schedule_pdf_safety_cleanup(job_id, delay_seconds=0)

    # JOB entry preserved (safety NÃO touch quando status terminal)
    assert job_id in JOBS, "JOB should remain when status=completed (safety skips)"
    # Cleanup tempfile manualmente (test isolation — was simulating completed SSE)
    Path(pdf_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_safety_cleanup_handles_missing_pdf_file_gracefully():
    """AC-4 edge case: PDF já removido por SSE finally mas JOB ainda queued (race).

    Status race: SSE finally rodou + cleaned PDF, mas updated status APÓS safety
    iniciou wait. Safety deve handle missing file sem raise.
    """
    job_id = "test-pdf-already-gone"
    JOBS[job_id] = {
        "status": "queued",
        "pdf_path": "/tmp/nonexistent_test_file.pdf",  # PDF não existe
    }

    # Should NOT raise (graceful unlink missing_ok)
    await _schedule_pdf_safety_cleanup(job_id, delay_seconds=0)

    assert job_id not in JOBS, "JOB removed mesmo com PDF missing (cleanup robusto)"


@pytest.mark.asyncio
async def test_safety_cleanup_handles_concurrent_jobs():
    """AC-5: 3 concurrent safety cleanups — todos PDFs removed, todos JOBs limpos."""
    pdfs: list[str] = []
    job_ids: list[str] = []
    for i in range(3):
        pdf_path = _create_orphan_pdf_tmpfile()
        pdfs.append(pdf_path)
        job_id = f"test-concurrent-{i}"
        job_ids.append(job_id)
        JOBS[job_id] = {
            "status": "queued",
            "pdf_path": pdf_path,
        }

    # Trigger 3 cleanups concurrent (asyncio.gather)
    await asyncio.gather(
        *[_schedule_pdf_safety_cleanup(jid, delay_seconds=0) for jid in job_ids]
    )

    for pdf_path in pdfs:
        assert not Path(pdf_path).exists(), f"Concurrent cleanup failed for {pdf_path}"
    for job_id in job_ids:
        assert job_id not in JOBS, f"Concurrent JOB removal failed for {job_id}"


@pytest.mark.asyncio
async def test_safety_cleanup_skips_missing_job_gracefully():
    """Edge case: JOB removed antes safety wait expire (normal flow completed)."""
    # JOB nunca added a JOBS dict → safety should noop sem raise
    await _schedule_pdf_safety_cleanup("nonexistent-job-id", delay_seconds=0)
    # No assertion needed — passes if doesn't raise


@pytest.mark.asyncio
async def test_safety_cleanup_default_delay_is_configurable_via_env():
    """Verify _PDF_SAFETY_CLEANUP_DELAY_SECONDS é configurable via env var."""
    import os
    from bloco_interface.web import app as app_module

    # Default 600s
    assert app_module._PDF_SAFETY_CLEANUP_DELAY_SECONDS == int(
        os.environ.get("REVISOR_PDF_SAFETY_CLEANUP_SECONDS", "600")
    )
