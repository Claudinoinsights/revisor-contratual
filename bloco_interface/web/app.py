"""FastAPI app — Revisor Contratual UI Web.

Substitui Streamlit (REV-INT-01). HTMX-driven, partial swaps.

Story UI-1 (Sprint 02) — Production-grade:
  - Phase A: validation MIME (%PDF-) + max_size (10MB) + tier Literal default 'balanced'
    (resolve TD-WEB-VAL-MIME-01 + TD-WEB-NOMAXSIZE-01 + TD-WEB-TIER-ENUM-01 + ADR-010 alignment)
  - Phase C: pipeline real integration via JobState + JOBS dict + asyncio await + LGPD cleanup
    (resolve TD-WEB-SSE-NOSESSION-01)
  - Phase D: 4 error states UX (HTTPException → error.html, não JSON default)

Endpoints:
    GET  /                      → index.html (estado idle)
    POST /revisar               → partials/processing.html (multipart upload com validação real)
    GET  /pipeline-stream       → SSE com 7 steps (real pipeline ou mock se job_id inválido)
    GET  /verdict               → partials/verdict.html (real ou MOCK fallback)
    POST /reset                 → partials/idle.html
    GET  /static/*              → CSS/JS (montado abaixo)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal, TypedDict

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from bloco_vault import open_vault
from bloco_vault.populate import BUNDLED_DATA_DIR, populate_vault_if_needed
from bloco_workflow import revisar_contrato

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

# Default paths para pipeline real (alinhado com cli.py)
DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "revisor-contratual"
DEFAULT_VAULT_DB = DEFAULT_DATA_DIR / "vault.db"
DEFAULT_AUDIT_PATH = DEFAULT_DATA_DIR / "audit.jsonl"
DEFAULT_BACEN_CACHE = DEFAULT_DATA_DIR / "bacen-cache"

# ── Validation constants (Phase A — UI-1) ──────────────────────────────────
# AC-2: max upload size (TD-WEB-NOMAXSIZE-01)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# AC-3: tier validation (TD-WEB-TIER-ENUM-01) + default ADR-010 alignment
LLMTier = Literal["lean", "balanced", "premium"]

# ── Pipeline config ───────────────────────────────────────────────────────
PIPELINE_STEPS = [
    "Parsing PDF",
    "Cálculo Decimal",
    "BACEN SGS",
    "Vault busca",
    "Personas",
    "Juiz",
    "Audit log",
]

# ── Mock fallback (Phase C — usado quando job_id inválido OU vault ausente) ─
MOCK_HISTORY = [
    {"name": "contrato-bb-45.pdf", "verdict": "hitl", "label": "HITL", "score": 78, "when": "12m"},
    {
        "name": "caixa-5829.pdf",
        "verdict": "aprovado-100",
        "label": "100",
        "score": 100,
        "when": "ontem",
    },
    {"name": "santander-1.pdf", "verdict": "rejeitado", "label": "REJ", "score": 65, "when": "3d"},
]

MOCK_VERDICT = {
    "filename": "contrato.pdf",
    "status": "hitl",
    "status_label": "Aprovado com risco",
    "aderencia": 78,
    "criterios": [
        {"tag": "C1", "score": "1.00"},
        {"tag": "C2", "score": "0.50"},
        {"tag": "C3", "score": "1.00"},
    ],
    "is_mock": True,
}


# ── Job state (Phase C — pipeline real session) ───────────────────────────
class JobState(TypedDict):
    """In-memory state per upload job. MVP — Sprint 03 evoluir Redis."""

    status: str  # queued | running | done | error
    pdf_path: str
    tier: LLMTier
    uf: str
    data: str
    filename: str
    verdict: dict[str, Any] | None
    error: str | None


JOBS: dict[str, JobState] = {}


# ── Lifespan (Phase C — VAULT-FIX-01) ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hooks. Idempotent vault population per ADR-012."""
    try:
        result = populate_vault_if_needed(DEFAULT_VAULT_DB, BUNDLED_DATA_DIR)
        if result["populated"]:
            logger.info(
                "Vault populated from bundled: %d STJ + %d STF SV",
                result["stj_count"],
                result["stf_count"],
            )
        else:
            logger.info("Vault populate skipped: %s", result["skipped_reason"])
    except Exception as exc:  # noqa: BLE001
        # Não bloquear startup — pipeline_stream já tem fallback se vault ausente
        logger.exception("Vault populate failed at startup: %s", exc)
    yield


# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(title="Revisor Contratual", version="0.2.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ── Custom exception handler (Phase D — UI-1) ─────────────────────────────
ERROR_TYPE_MAP = {
    400: "invalid_pdf",
    413: "file_too_large",
    422: "invalid_tier",
    500: "pipeline_failure",
}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> HTMLResponse:
    """Retorna error.html user-friendly em vez de JSON default FastAPI."""
    error_type = ERROR_TYPE_MAP.get(exc.status_code, "pipeline_failure")
    return templates.TemplateResponse(
        request=request,
        name="partials/error.html",
        context={"error_type": error_type, "error_message": exc.detail},
        status_code=exc.status_code,
    )


# ── Routes ────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"history": MOCK_HISTORY},
    )


@app.post("/revisar", response_class=HTMLResponse)
async def revisar(
    request: Request,
    pdf: UploadFile,
    uf: str = Form(default=""),
    data: str = Form(default=""),
    tier: LLMTier = Form(default="balanced"),  # noqa: B008 — FastAPI Form pattern (ADR-010 default)
) -> HTMLResponse:
    # AC-2: max_size validation (TD-WEB-NOMAXSIZE-01)
    if pdf.size and pdf.size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo excede {MAX_UPLOAD_SIZE // (1024 * 1024)}MB.",
        )

    # AC-1: magic bytes validation (TD-WEB-VAL-MIME-01)
    header = await pdf.read(5)
    await pdf.seek(0)
    if header != b"%PDF-":
        raise HTTPException(
            status_code=400,
            detail="Arquivo não é um PDF válido (magic bytes %PDF- ausentes).",
        )

    # Phase C: Persistir PDF temporariamente (LGPD: deletado em pipeline_stream finally)
    pdf_bytes = await pdf.read()
    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, "wb") as tmp:
        tmp.write(pdf_bytes)

    # Phase C: Gerar job_id e armazenar state (TD-WEB-SSE-NOSESSION-01)
    job_id = str(uuid.uuid4())
    filename = pdf.filename or "contrato.pdf"
    JOBS[job_id] = {
        "status": "queued",
        "pdf_path": pdf_path,
        "tier": tier,
        "uf": uf,
        "data": data,
        "filename": filename,
        "verdict": None,
        "error": None,
    }

    return templates.TemplateResponse(
        request=request,
        name="partials/processing.html",
        context={
            "filename": filename,
            "uf": uf,
            "data": data,
            "tier": tier,
            "steps": PIPELINE_STEPS,
            "job_id": job_id,  # NOVO Phase C
        },
    )


@app.get("/pipeline-stream")
async def pipeline_stream(job_id: str = "") -> StreamingResponse:
    """SSE — emite steps reais do pipeline OU fallback mock se job_id inválido."""

    async def event_generator() -> AsyncIterator[str]:
        # Fallback graceful — job_id ausente ou inválido (compat smoke local sem upload)
        if not job_id or job_id not in JOBS:
            total = len(PIPELINE_STEPS)
            for i in range(total):
                payload = {"index": i, "total": total, "step": PIPELINE_STEPS[i], "done": False}
                yield f"event: step\ndata: {json.dumps(payload)}\n\n"
                await asyncio.sleep(0.4)
            yield f"event: step\ndata: {json.dumps({'done': True})}\n\n"
            return

        job = JOBS[job_id]
        try:
            # Vault check — se ausente, fallback mock com aviso
            if not DEFAULT_VAULT_DB.exists():
                JOBS[job_id]["status"] = "error"
                JOBS[job_id]["error"] = (
                    f"Vault não encontrado em {DEFAULT_VAULT_DB}. "
                    "Rode: revisor populate-vault --source all"
                )
                yield f"event: error\ndata: {json.dumps({'message': JOBS[job_id]['error']})}\n\n"
                return

            JOBS[job_id]["status"] = "running"

            # Emit step 0 (Parsing PDF) imediatamente para feedback visual
            step_zero = {
                "index": 0,
                "total": len(PIPELINE_STEPS),
                "step": PIPELINE_STEPS[0],
                "done": False,
            }
            yield f"event: step\ndata: {json.dumps(step_zero)}\n\n"

            conn = open_vault(str(DEFAULT_VAULT_DB))
            try:
                veredito = await revisar_contrato(
                    Path(job["pdf_path"]),
                    audit_path=DEFAULT_AUDIT_PATH,
                    vault_conn=conn,
                    uf_override=job["uf"] or None,
                    data_override=None,  # parsed do PDF; CLI faz parse de --data-assinatura
                    tier_advogado=job["tier"],
                    bacen_cache_dir=DEFAULT_BACEN_CACHE,
                )
            finally:
                conn.close()

            JOBS[job_id]["verdict"] = (
                veredito.model_dump() if hasattr(veredito, "model_dump") else dict(veredito)
            )
            JOBS[job_id]["status"] = "done"

            # Emit steps progressivos rápidos para visual feedback (pipeline já completou)
            for i in range(len(PIPELINE_STEPS)):
                payload = {
                    "index": i,
                    "total": len(PIPELINE_STEPS),
                    "step": PIPELINE_STEPS[i],
                    "done": False,
                }
                yield f"event: step\ndata: {json.dumps(payload)}\n\n"
                await asyncio.sleep(0.1)

            yield f"event: step\ndata: {json.dumps({'done': True, 'job_id': job_id})}\n\n"
        except Exception as exc:  # noqa: BLE001
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = str(exc)
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"
        finally:
            # LGPD cleanup OBRIGATÓRIO (UI-1 Phase C requirement)
            # ASYNC240 noqa: cleanup em finally é best-effort + curto; trio/anyio overkill aqui
            pdf_path_str = JOBS[job_id]["pdf_path"]
            if pdf_path_str:
                pdf_path_obj = Path(pdf_path_str)
                if pdf_path_obj.exists():  # noqa: ASYNC240
                    try:
                        pdf_path_obj.unlink()  # noqa: ASYNC240
                    except OSError:
                        pass  # Best-effort — não bloquear response

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/verdict", response_class=HTMLResponse)
async def verdict(request: Request, job_id: str = "") -> HTMLResponse:
    """Retorna verdict real (se job_id válido) ou fallback MOCK_VERDICT."""
    if job_id and job_id in JOBS and JOBS[job_id].get("verdict"):
        verdict_data = JOBS[job_id]["verdict"]
    else:
        verdict_data = MOCK_VERDICT

    return templates.TemplateResponse(
        request=request,
        name="partials/verdict.html",
        context={"verdict": verdict_data},
    )


@app.post("/reset", response_class=HTMLResponse)
async def reset(request: Request, job_id: str = Form(default="")) -> HTMLResponse:
    """Limpa job state (Phase C session cleanup)."""
    if job_id and job_id in JOBS:
        JOBS.pop(job_id, None)

    return templates.TemplateResponse(
        request=request,
        name="partials/idle.html",
        context={},
    )


# ── Entry point ───────────────────────────────────────────────────────────
def run() -> None:
    import uvicorn

    uvicorn.run(
        "bloco_interface.web.app:app",
        host="127.0.0.1",
        port=8501,
        reload=True,
    )


if __name__ == "__main__":
    run()
