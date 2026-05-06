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
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from bloco_interface import ollama_manager
from bloco_interface.ollama_manager import OllamaBinaryNotFound, OllamaSpawnFailed
from bloco_interface.web import auth
from bloco_vault import open_vault
from bloco_vault.populate import BUNDLED_DATA_DIR, populate_vault_if_needed
from bloco_workflow import revisar_contrato

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"
PROJECT_ROOT = WEB_DIR.parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"

# Default paths para pipeline real (alinhado com cli.py)
DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "revisor-contratual"
DEFAULT_VAULT_DB = DEFAULT_DATA_DIR / "vault.db"
DEFAULT_AUDIT_PATH = DEFAULT_DATA_DIR / "audit.jsonl"
DEFAULT_BACEN_CACHE = DEFAULT_DATA_DIR / "bacen-cache"


def _read_app_version() -> str:
    """MVP-LEAN-01 Task 1: lê version de pyproject.toml para footer C7."""
    try:
        import tomllib

        with PYPROJECT_PATH.open("rb") as f:
            data = tomllib.load(f)
        return f"v{data['project']['version']}"
    except (FileNotFoundError, KeyError, OSError):
        return "v0.0.0+unknown"


APP_VERSION = _read_app_version()


# MVP-LEAN-01 Task 1: layout-base context defaults.
# tema_1378 mock por enquanto (Task 7 implementa lógica FR-MONITOR real).
DEFAULT_TEMA_1378 = {
    "nivel": "verde",
    "mensagem": "✓ Tema 1378 STJ — sem alterações na última verificação automática.",
    "acoes": [],
}


def _layout_context(request: Request) -> dict[str, Any]:
    """MVP-LEAN-01 Task 1: contexto compartilhado para base.html (topbar + banner + footer C7).

    Task 2 instala SessionMiddleware → request.session sempre disponível.
    """
    return {
        "session_user": request.session.get("user"),
        "tema_1378": DEFAULT_TEMA_1378,
        "app_version": APP_VERSION,
        "audit_url": "/audit.jsonl",
    }

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


# ── Lifespan (ordem determinística per ADR-013 §2.4) ──────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hooks integrando OLLAMA-MGR-01 + VAULT-FIX-01.

    Ordem startup determinística (ADR-013 §2.4):

    1. ``ollama_manager.acquire_app_lock()`` — concurrent app prevention (EC-11)
    2. ``ollama_manager.cleanup_orphans_on_startup()`` — recovery EC-06
    3. ``ollama_manager.detect_ollama_binary()`` — raise se binary não existe (EC-01)
    4. detect-then-spawn :11434 + :11435 (preserva Ollama existente)
    5. ``ollama_manager.write_pid_file_atomic()`` (apenas se spawnamos)
    6. ``populate_vault_if_needed()`` — VAULT-FIX-01 (ADR-012)
    7. ``asyncio.create_task(ensure_models_pulled(...))`` — Phase D auto-pull (stub atualmente)

    Shutdown ordem inversa: kill spawned + release lock.

    Falhas em startup levantam exceção → app fail-to-start (não degradação silenciosa).
    """
    lock_fd: int | None = None
    spawned_pids: dict[str, int] = {}
    try:
        # Etapa 1 — acquire app lock (EC-11)
        lock_fd = ollama_manager.acquire_app_lock()
        logger.info("Lifespan startup: app lock acquired (fd=%d)", lock_fd)

        # Etapa 2 — cleanup orphan ollama processes (EC-06)
        ollama_manager.cleanup_orphans_on_startup()

        # Etapa 3 — detect ollama binary (EC-01)
        binary = ollama_manager.detect_ollama_binary()
        if binary is None:
            raise ollama_manager.OllamaBinaryNotFound(
                "Ollama binary não encontrado. "
                "Instale via https://ollama.ai/download "
                "ou aponte OLLAMA_BINARY_PATH no .env."
            )
        logger.info("Lifespan startup: ollama binary -> %s", binary)

        # Etapa 4 — detect-then-spawn 2 instâncias
        host = ollama_manager.DEFAULT_HOST
        for role, port in (
            ("advogado", ollama_manager.DEFAULT_PORT_ADVOGADO),
            ("economista", ollama_manager.DEFAULT_PORT_ECONOMISTA),
        ):
            if await ollama_manager.detect_running_ollama(host, port):
                logger.info(
                    "Lifespan startup: REUSE existing ollama %s:%d (role=%s)",
                    host,
                    port,
                    role,
                )
            else:
                pid = ollama_manager.spawn_ollama(binary, host, port)
                spawned_pids[role] = pid
                logger.info(
                    "Lifespan startup: SPAWNED ollama %s:%d PID=%d (role=%s)",
                    host,
                    port,
                    pid,
                    role,
                )

        # Etapa 5 — persist PID file se spawned algo
        if spawned_pids:
            ollama_manager.write_pid_file_atomic(spawned_pids)

        # Etapa 6 — populate vault (VAULT-FIX-01 / ADR-012)
        try:
            result = populate_vault_if_needed(DEFAULT_VAULT_DB, BUNDLED_DATA_DIR)
            if result["populated"]:
                logger.info(
                    "Lifespan startup: vault populated %d STJ + %d STF SV",
                    result["stj_count"],
                    result["stf_count"],
                )
            else:
                logger.info(
                    "Lifespan startup: vault populate skipped (%s)",
                    result["skipped_reason"],
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Lifespan startup: vault populate failed: %s", exc)

        # Etapa 7 — auto-pull background (Phase D stub atual; tolerância a NotImplementedError)
        try:
            asyncio.create_task(  # noqa: RUF006 — fire-and-forget intencional (background)
                ollama_manager.ensure_models_pulled(list(ollama_manager.REQUIRED_MODELS))
            )
        except NotImplementedError:
            logger.warning(
                "Lifespan startup: ensure_models_pulled é stub (Phase D pending) — "
                "modelos devem estar pre-pulled manualmente"
            )

    except (
        ollama_manager.OllamaBinaryNotFound,
        ollama_manager.AppAlreadyRunning,
        ollama_manager.DiskSpaceInsufficient,
    ):
        logger.critical("Lifespan startup FAIL — abortando app")
        if lock_fd is not None:
            ollama_manager.release_app_lock(lock_fd)
        raise

    yield

    # Shutdown ordem inversa
    try:
        ollama_manager.kill_spawned_ollama()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Lifespan shutdown: kill_spawned_ollama failed: %s", exc)
    if lock_fd is not None:
        ollama_manager.release_app_lock(lock_fd)
        logger.info("Lifespan shutdown: app lock released")


# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(title="Revisor Contratual", version="0.2.0", lifespan=lifespan)
# MVP-LEAN-01 Task 2: SessionMiddleware (FR-LGPD-MVP-01a defense-in-depth camada 1).
# https_only=False em dev; toggle via env REVISOR_HTTPS_ONLY=1 em prod.
app.add_middleware(
    SessionMiddleware,
    secret_key=auth.get_secret_key(),
    https_only=os.environ.get("REVISOR_HTTPS_ONLY", "0") == "1",
    same_site="lax",
    max_age=24 * 60 * 60,  # 24h conforme ux-spec §3 S1 linha 199
)
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
    # MVP-LEAN-01 Task 2 — AC-MVP-01: route protection (sem session válida → /login)
    if not request.session.get("user"):
        return RedirectResponse("/login", status_code=303)
    # MVP-LEAN-01 Task 3 — AC-MVP-02: renderiza S2 Pré-upload (substitui index.html legacy)
    context: dict[str, Any] = {}
    context.update(_layout_context(request))  # topbar + banner + footer (Task 1)
    return templates.TemplateResponse(
        request=request,
        name="s2_pre_upload.html",
        context=context,
    )


# MVP-LEAN-01 Task 2 — AC-MVP-01: S1 Login + C1 Login form
@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request) -> HTMLResponse:
    if request.session.get("user"):
        return RedirectResponse("/", status_code=303)
    csrf = auth.generate_csrf_token()
    request.session["csrf_token"] = csrf
    context = _layout_context(request)
    context["tema_1378"] = {"nivel": "oculto"}  # ux-spec §3 S1: sem banner pré-auth
    context["session_user"] = None  # ux-spec §3 S1: sem nome usuário pré-auth
    context["csrf_token"] = csrf
    context["error"] = None
    return templates.TemplateResponse(
        request=request,
        name="s1_login.html",
        context=context,
    )


@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
) -> HTMLResponse:
    # CSRF verify (constant-time compare)
    session_csrf = request.session.get("csrf_token")
    if not auth.verify_csrf_token(session_csrf, csrf_token):
        return _render_login_error(request, "Sessão expirada. Recarregue a página.", status=403)
    # Auth (anti-enumeration: mesma resposta para user errado vs senha errada)
    if not auth.authenticate(username, password):
        return _render_login_error(request, "Usuário ou senha inválidos.", status=401)
    # Success: regenera session (mitiga session fixation), grava user, redirect
    request.session.clear()
    request.session["user"] = username
    response = HTMLResponse(content="", status_code=200)
    response.headers["HX-Redirect"] = "/"
    return response


def _render_login_error(request: Request, message: str, status: int) -> HTMLResponse:
    """Re-renderiza S1 com erro auth — refresh CSRF para próxima tentativa."""
    csrf = auth.generate_csrf_token()
    request.session["csrf_token"] = csrf
    context = _layout_context(request)
    context["tema_1378"] = {"nivel": "oculto"}
    context["session_user"] = None
    context["csrf_token"] = csrf
    context["error"] = message
    return templates.TemplateResponse(
        request=request,
        name="s1_login.html",
        context=context,
        status_code=status,
    )


# MVP-LEAN-01 Task 1 — AC-MVP-LGPD-L1: logout clears session, retorna HX-Redirect.
@app.post("/logout", response_class=HTMLResponse)
async def logout(request: Request) -> HTMLResponse:
    request.session.clear()
    response = HTMLResponse(content="", status_code=200)
    response.headers["HX-Redirect"] = "/login"
    return response


@app.post("/revisar", response_class=HTMLResponse)
async def revisar(
    request: Request,
    pdf: UploadFile,
    uf: str = Form(default=""),
    data: str = Form(default=""),
    tier: LLMTier = Form(default="balanced"),  # noqa: B008 — FastAPI Form pattern (ADR-010 default)
) -> HTMLResponse:
    # Phase E / AC-7: on-demand health check + lazy respawn (EC-08 Ollama crash mid-revisar)
    host = ollama_manager.DEFAULT_HOST
    for role, port in (
        ("advogado", ollama_manager.DEFAULT_PORT_ADVOGADO),
        ("economista", ollama_manager.DEFAULT_PORT_ECONOMISTA),
    ):
        if not await ollama_manager.detect_running_ollama(host, port):
            try:
                binary = ollama_manager.detect_ollama_binary()
                if binary is None:
                    raise HTTPException(
                        status_code=503,
                        detail="Ollama indisponível (binary não localizado)",
                        headers={"Retry-After": "60"},
                    )
                pid = ollama_manager.spawn_ollama(binary, host, port)
                logger.warning(
                    "revisar: lazy respawn ollama %s:%d PID=%d (role=%s)",
                    host, port, pid, role,
                )
                # Atualizar PID file para tracking shutdown lifespan
                current_pids = ollama_manager.read_pid_file_safely()
                current_pids[role] = pid
                ollama_manager.write_pid_file_atomic(current_pids)
            except (OllamaSpawnFailed, OllamaBinaryNotFound) as exc:
                logger.error("revisar: lazy respawn falhou: %s", exc)
                raise HTTPException(
                    status_code=503,
                    detail=f"Ollama indisponível e respawn falhou: {exc}",
                    headers={"Retry-After": "60"},
                ) from exc

    # Phase D / AC-8: 503 retry-after se modelos LLM ainda baixando (auto-pull background)
    if not ollama_manager.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Modelos LLM baixando — aguarde alguns minutos",
            headers={"Retry-After": "60"},
        )

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


# ── Phase D: SSE /ollama-status (auto-pull progress) ───────────────────────
@app.get("/ollama-status")
async def ollama_status_sse() -> StreamingResponse:
    """SSE stream do status de auto-pull de modelos para UI banner.

    Phase D / OLLAMA-MGR-01 / AC-6. Cliente HTMX (`hx-ext="sse"`) consome
    eventos para renderizar progresso visual durante download de modelos
    (10-30min primeira vez). Loop encerra quando state in (ready, error).
    """

    async def event_generator() -> AsyncIterator[str]:
        while True:
            status = ollama_manager.get_pull_status()
            yield f"event: status\ndata: {json.dumps(status)}\n\n"
            if status.get("state") in ("ready", "error"):
                break
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
