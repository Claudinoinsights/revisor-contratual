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
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, TypedDict

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from bloco_audit.chain import AuditChainError  # noqa: F401  (compat checks)
from bloco_auth import api as sp04_auth_api
from bloco_auth import byok_api as sp04_byok_api
from bloco_auth import dpa as sp04_dpa
from bloco_auth import jwt_utils as sp04_jwt_utils
from bloco_backup.scheduler import create_scheduler
from bloco_dataset import tema_1378_state
from bloco_interface import ollama_manager
from bloco_interface.ollama_manager import OllamaBinaryNotFound, OllamaSpawnFailed
from bloco_interface.web import auth, error_handler
from bloco_lgpd.headers import HeadersMiddleware
from bloco_lgpd.permissions import apply_audit_permissions, apply_uploads_dir_permissions
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
    """MVP-LEAN-01 Task 1+7: contexto compartilhado para base.html.

    Task 2 instala SessionMiddleware → request.session sempre disponível.
    Task 7 substitui DEFAULT_TEMA_1378 mock por tema_1378_state.get_current() dinâmico
    e adiciona main_disabled flag quando nivel == 'vermelho' (CRITICAL).
    """
    tema_1378 = tema_1378_state.get_current()
    return {
        "session_user": request.session.get("user"),
        "tema_1378": tema_1378,
        "main_disabled": tema_1378.get("nivel") == "vermelho",
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

# MVP-LEAN-01 Task 4: 5 fases canônicas (per ux-spec §3 S5 + §4 C4 linhas 695-700)
MVP_LEAN_PHASES = [
    "Parsing PDF",
    "Advogado (Sabia/Qwen 7B)",
    "Economista (Qwen 7B)",
    "Validador semântico",
    "Juiz HITL",
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
    has_decisao_adversa: bool  # MVP-LEAN-01 Task 5: controla disponibilidade D3 em S6


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
        # Etapa 0 — Sprint 04 SP04-AUTH-01: JWT config eager validation
        # (Story Risk #3 — falha cedo no startup é melhor que falha no primeiro
        # request prod). Se JWT_SECRET_KEY ausente OR < 32 bytes, ConfigError
        # é raised aqui e impede app start (silent fail bloqueado).
        try:
            sp04_jwt_utils.validate_config()
            logger.info("Lifespan startup: SP04 JWT config validated (HS256 + secret >= 32 bytes)")
        except sp04_jwt_utils.ConfigError as exc:
            # Em dev sem JWT_SECRET_KEY setado, log warning ao invés de abortar
            # — preserva DX Sprint 03 (dev pode rodar sem Sprint 04 deps prontas).
            # Em prod, ops deve setar JWT_SECRET_KEY e este path não dispara.
            logger.warning(
                "Lifespan startup: SP04 JWT config inválida (Sprint 04 endpoints "
                "vão falhar com 500 — setar JWT_SECRET_KEY para habilitar): %s",
                exc,
            )

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

        # MVP-LEAN-01 Task 8 — LGPD L5: aplicar permissões filesystem (chmod 600/700 cross-platform)
        try:
            if DEFAULT_AUDIT_PATH.exists():
                apply_audit_permissions(DEFAULT_AUDIT_PATH)
            uploads_dir = DEFAULT_DATA_DIR / "uploads"
            if uploads_dir.exists():
                apply_uploads_dir_permissions(uploads_dir)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Lifespan startup: LGPD L5 chmod falhou (não-bloqueante): %s", exc)

        # MVP-LEAN-01 Task 8 — APScheduler embedded backup
        try:
            app.state.scheduler = create_scheduler()
            app.state.scheduler.start()
            logger.info("Lifespan startup: APScheduler started (backup_daily + rotation)")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Lifespan startup: APScheduler falhou — backup automático desabilitado: %s",
                exc,
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
    # MVP-LEAN-01 Task 8 — APScheduler shutdown primeiro (graceful, evita threads zombies)
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler is not None:
        try:
            scheduler.shutdown(wait=True)
            logger.info("Lifespan shutdown: APScheduler stopped")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Lifespan shutdown: APScheduler shutdown falhou: %s", exc)

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
# MVP-LEAN-01 Task 8 — LGPD L3: security headers (CSP + X-Frame + X-Content-Type-Options + ...)
app.add_middleware(HeadersMiddleware)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Sprint 04 SP04-AUTH-01: registra routers Auth + Onboarding + Users CRUD
# (multi-tenant cloud SaaS BYOK). Coexiste com cookie auth Sprint 03 (admin
# single-user via auth.py) — Sprint 03 path é fallback durante transição;
# deprecation TODO em story posterior Sprint 04 backlog.
app.include_router(sp04_auth_api.router)
# Sprint 04 chunk 5 — DPA flow ADR-019 (3 endpoints: GET text/{version},
# POST accept, GET status). Fecha AC-06 do story SP04-AUTH-01.
app.include_router(sp04_dpa.router)
# Sprint 04 SP04-BYOK-01 — BYOK Anthropic key lifecycle (3 endpoints:
# POST rotate, POST revoke, GET status). Tank-ratified Phase 12.3a.
app.include_router(sp04_byok_api.router)


# CC.39 fix F-06 (Smith CC.37): cache busting automático via mtime hash dos
# arquivos /static/. Bumpa automaticamente quando qualquer JS/CSS é modificado,
# eliminando dependência de disciplina humana para bumpar ?v= manual.
def _compute_static_version() -> str:
    import hashlib

    if not STATIC_DIR.exists():
        return "dev"
    mtimes = sorted(
        str(f.stat().st_mtime)
        for f in STATIC_DIR.rglob("*")
        if f.is_file() and f.suffix in (".js", ".css")
    )
    return hashlib.sha256("|".join(mtimes).encode()).hexdigest()[:8]


STATIC_VERSION = _compute_static_version()
templates.env.globals["static_version"] = STATIC_VERSION


# ── Custom exception handler (Phase D — UI-1; Task 6 refactor C6 catch-all) ──
# Sprint 02 UI-1 mapping legacy preservado para partials/error.html (intacto).
ERROR_TYPE_MAP = {
    400: "invalid_pdf",
    413: "file_too_large",
    422: "invalid_tier",
    500: "pipeline_failure",
}

# MVP-LEAN-01 Task 6: HTTP status → variant_key (S4 upload errors via HTTPException).
HTTP_STATUS_TO_C6_VARIANT = {
    400: "infra_unknown",  # invalid_pdf — fallback (raramente cai aqui)
    413: "disk_full_uploads",  # file too large reuso semântico
    422: "infra_unknown",  # invalid_tier — fallback
}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> HTMLResponse:
    """MVP-LEAN-01 Task 6: renderiza S7 Error pane com C6 component.

    HTTPException → variant_key via HTTP_STATUS_TO_C6_VARIANT; fallback infra_unknown.
    Status code 401 (auth) preserva comportamento atual (partials/error.html legacy).
    """
    # Auth errors mantêm fluxo legacy (não convertem para S7)
    if exc.status_code in (401, 403):
        error_type = ERROR_TYPE_MAP.get(exc.status_code, "pipeline_failure")
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={"error_type": error_type, "error_message": exc.detail},
            status_code=exc.status_code,
        )

    # Demais HTTPExceptions → S7 Error pane com C6 (Task 6)
    variant_key = HTTP_STATUS_TO_C6_VARIANT.get(exc.status_code, "infra_unknown")
    payload = error_handler.get_c6_payload(variant_key, exc=None)
    # Override diagnostico para mostrar exc.detail user-friendly
    if exc.detail and variant_key == "infra_unknown":
        payload["diagnostico"] = str(exc.detail)
    s7_context: dict[str, Any] = dict(payload)
    s7_context.update(_layout_context(request))
    return templates.TemplateResponse(
        request=request,
        name="s7_error.html",
        context=s7_context,
        status_code=exc.status_code,
    )


# MVP-LEAN-01 Task 6 — global Exception handler para catch-all infra_unknown
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> HTMLResponse:
    """Catch-all para exceptions não-HTTPException (Task 6 catch-all infra_unknown).

    Classifica via error_handler.classify_exception → renderiza S7 com C6 correto.
    """
    if isinstance(exc, HTTPException):
        # Já tratado por http_exception_handler — não chamado aqui em prática
        return await http_exception_handler(request, exc)

    variant_key = error_handler.classify_exception(exc)
    logger.error("global_exception_handler: variant=%s exc=%s", variant_key, exc, exc_info=True)
    payload = error_handler.get_c6_payload(variant_key, exc=exc)
    s7_context: dict[str, Any] = dict(payload)
    s7_context.update(_layout_context(request))
    return templates.TemplateResponse(
        request=request,
        name="s7_error.html",
        context=s7_context,
        status_code=500,
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


# MVP-LEAN-01 Task 7 — AC-MVP-08 + AC-MVP-MONITOR: ack endpoint para banner CRITICAL
@app.post("/monitor-tema/acknowledge", response_class=HTMLResponse)
async def monitor_tema_acknowledge(request: Request) -> HTMLResponse:
    """Maintainer ack via web → state desce VERMELHO → AMARELO + audit entry.

    Per ux-spec linha 603: banner não-fechável até maintainer ack
    (via CLI revisor monitor-tema --acknowledge OR esta rota).
    """
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="auth required")
    new_state = tema_1378_state.acknowledge(audit_path=DEFAULT_AUDIT_PATH)
    response = HTMLResponse(content="", status_code=200)
    response.headers["HX-Redirect"] = "/"  # reload reflete novo state (amarelo)
    response.headers["X-Tema-1378-Nivel"] = new_state.get("nivel", "unknown")
    return response


@app.post("/revisar", response_class=HTMLResponse)
async def revisar(
    request: Request,
    pdf: UploadFile,
    pdf_decisao_adversa: UploadFile | None = None,  # MVP-LEAN-01 Task 3+5: D2 opcional
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
    # MVP-LEAN-01 Task 5 — AC-MVP-D3-DUAL-INPUT: D2 enviado controla disponibilidade D3
    has_decisao_adversa = bool(
        pdf_decisao_adversa and pdf_decisao_adversa.filename and pdf_decisao_adversa.size,
    )
    # CC.42 fix F-A2 (Smith CC.41 CRITICAL): converter data string YYYY-MM-DD → date
    # ANTES de armazenar JOBS. Permite revisar_stream passar data_override real
    # ao pipeline (corrige bug pré-existente data_override=None hardcoded).
    from datetime import date as _date  # noqa: PLC0415 — local scope para parsing
    data_obj: _date | None = None
    if data:
        try:
            data_obj = _date.fromisoformat(data)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Data inválida: '{data}' (esperado YYYY-MM-DD).",
            ) from exc
    JOBS[job_id] = {
        "status": "queued",
        "pdf_path": pdf_path,
        "tier": tier,
        "uf": uf,
        "data": data_obj,  # CC.42: agora é date | None, não string
        "filename": filename,
        "verdict": None,
        "error": None,
        "has_decisao_adversa": has_decisao_adversa,
    }

    # MVP-LEAN-01 Task 4: render S5 Processing (substitui partials/processing.html no MVP-LEAN)
    s5_context: dict[str, Any] = {
        "filename": filename,
        "uf": uf,
        "data": data,
        "tier": tier,
        "phases": MVP_LEAN_PHASES,
        "job_id": job_id,
    }
    s5_context.update(_layout_context(request))
    return templates.TemplateResponse(
        request=request,
        name="s5_processing.html",
        context=s5_context,
    )


# MVP-LEAN-01 Task 4 — AC-MVP-05 + AC-MVP-SSE-RESILIENT: SSE com 5 events + heartbeat
@app.get("/revisar/stream/{job_id}")
async def revisar_stream(job_id: str) -> StreamingResponse:
    """SSE MVP-LEAN-01 — emite 5 events + ping heartbeat 10s.

    Events:
        phase-start: {phase, started_at}
        phase-done:  {phase, elapsed_s}
        phase-error: {phase, diagnostic, cause, solution, alternative}
        complete:    {deliverables, job_id}
        ping:        {ts}  (heartbeat 10s)
    """

    async def event_generator() -> AsyncIterator[str]:
        if job_id not in JOBS:
            yield (
                f"event: phase-error\ndata: "
                f"{json.dumps({'phase': 'parsing', 'diagnostic': 'job_id inválido'})}\n\n"
            )
            return

        job = JOBS[job_id]
        try:
            if not DEFAULT_VAULT_DB.exists():
                JOBS[job_id]["status"] = "error"
                error_data = {
                    "phase": "vault",
                    "diagnostic": "Vault não encontrado",
                    "cause": f"DB ausente em {DEFAULT_VAULT_DB}",
                    "solution": "Rode: revisor populate-vault --source all",
                    "alternative": "Verifique configuração local",
                }
                yield f"event: phase-error\ndata: {json.dumps(error_data)}\n\n"
                return

            JOBS[job_id]["status"] = "running"
            started_total = asyncio.get_event_loop().time()

            # Fase 0: Parsing PDF — emit phase-start imediato
            phase_start_ts = asyncio.get_event_loop().time()
            yield (
                f"event: phase-start\ndata: "
                f"{json.dumps({'phase': MVP_LEAN_PHASES[0], 'started_at': phase_start_ts})}\n\n"
            )
            # CC.40 fix F-07: ping inicial removido (loop heartbeat CC.35/CC.38 cobre).

            # CC.35 fix TD-SSE-WATCHDOG-60S-PDF-OCR: pipeline pode levar minutos
            # (OCR PDF imagem + LLMs). Roda revisar_contrato em background task
            # e emite ping heartbeat a cada 10s para evitar UI watchdog 60s.
            conn = open_vault(str(DEFAULT_VAULT_DB))
            try:
                # CC.38 fix F-04: timeout global 30min para evitar hang infinito
                # se Surya OCR travar OU outros bugs runtime.
                # CC.42 fix F-A2: data_override agora vem do form S2 (era None hardcoded).
                pipeline_task = asyncio.create_task(
                    asyncio.wait_for(
                        revisar_contrato(
                            Path(job["pdf_path"]),
                            audit_path=DEFAULT_AUDIT_PATH,
                            vault_conn=conn,
                            uf_override=job["uf"] or None,
                            data_override=job["data"],  # date | None (CC.42)
                            tier_advogado=job["tier"],
                            bacen_cache_dir=DEFAULT_BACEN_CACHE,
                        ),
                        timeout=1800,  # 30min hard ceiling
                    )
                )
                while not pipeline_task.done():
                    try:
                        await asyncio.wait_for(asyncio.shield(pipeline_task), timeout=10)
                    except asyncio.TimeoutError:
                        yield (
                            f"event: ping\ndata: "
                            f"{json.dumps({'ts': asyncio.get_event_loop().time()})}\n\n"
                        )
                veredito = await pipeline_task
            finally:
                conn.close()

            JOBS[job_id]["verdict"] = (
                veredito.model_dump() if hasattr(veredito, "model_dump") else dict(veredito)
            )
            JOBS[job_id]["status"] = "done"

            # Pipeline real terminou — emit phase-done para todas as fases sequencialmente
            # (visual feedback: pipeline completou; UI animação não bloqueia veredito)
            for i, phase in enumerate(MVP_LEAN_PHASES):
                now_ts = asyncio.get_event_loop().time()
                if i > 0:  # Phase 0 já teve phase-start
                    start_payload = json.dumps({"phase": phase, "started_at": now_ts})
                    yield f"event: phase-start\ndata: {start_payload}\n\n"
                elapsed = round(now_ts - phase_start_ts, 1)
                done_payload = json.dumps({"phase": phase, "elapsed_s": elapsed})
                yield f"event: phase-done\ndata: {done_payload}\n\n"
                phase_start_ts = asyncio.get_event_loop().time()
                await asyncio.sleep(0.1)

            total_elapsed = round(asyncio.get_event_loop().time() - started_total, 1)
            complete_data = {
                "job_id": job_id,
                "total_elapsed_s": total_elapsed,
                "deliverables": JOBS[job_id]["verdict"],
            }
            yield f"event: complete\ndata: {json.dumps(complete_data)}\n\n"
        except Exception as exc:  # noqa: BLE001
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = str(exc)
            error_data = {
                "phase": "pipeline",
                "diagnostic": "Erro durante execução do pipeline",
                "cause": str(exc),
                "solution": "Re-execute. Se persistir, verifique audit.jsonl",
                "alternative": "Inspecione logs do servidor para detalhes",
            }
            yield f"event: phase-error\ndata: {json.dumps(error_data)}\n\n"
        finally:
            # LGPD cleanup OBRIGATÓRIO
            pdf_path_str = JOBS[job_id]["pdf_path"]
            if pdf_path_str:
                pdf_path_obj = Path(pdf_path_str)
                if pdf_path_obj.exists():  # noqa: ASYNC240
                    try:
                        pdf_path_obj.unlink()  # noqa: ASYNC240
                    except OSError:
                        pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# MVP-LEAN-01 Task 4 — AC-MVP-AUDIT: client reporta connection drop → grava audit.jsonl entry
@app.post("/audit/connection-drop")
async def audit_connection_drop(
    request: Request,
    job_id: str = Form(...),
    last_phase: str = Form(default="unknown"),
) -> HTMLResponse:
    """Grava entry pipeline_lost_connection em audit.jsonl quando client detecta drop SSE."""
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="auth required")
    entry = {
        "type": "pipeline_lost_connection",
        "job_id": job_id,
        "last_phase": last_phase,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    try:
        DEFAULT_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with DEFAULT_AUDIT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as exc:
        logger.error("audit_connection_drop: erro gravando audit.jsonl: %s", exc)
        raise HTTPException(status_code=500, detail="Falha ao gravar audit") from exc
    return HTMLResponse(content="", status_code=204)


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


def _truncate_hash(full_hash: str | None, head: int = 4, tail: int = 4) -> str:
    """MVP-LEAN-01 Task 5: hash audit truncado 4+4 chars per ux-spec linha 519."""
    if not full_hash or len(full_hash) <= head + tail:
        return full_hash or ""
    return f"{full_hash[:head]}…{full_hash[-tail:]}"


def _format_deliverables_for_c5(
    verdict_data: dict[str, Any] | None,
    has_decisao_adversa: bool,
) -> list[dict[str, Any]]:
    """MVP-LEAN-01 Task 5: mapeia verdict raw para 3 cards C5 com flag disponivel.

    D1 (Relatório Contábil) e D2 (Petição Inicial) sempre disponíveis.
    D3 (Apelação Cível) disponível apenas se decisão adversa foi enviada em S2.
    """
    return [
        {
            "tipo": "D1",
            "label": "Relatório Contábil",
            "descricao": "Tabela Price + cálculos abusivos",
            "formato": "PDF",
            "paginas": 12,  # placeholder — real virá de verdict_data quando workflow popular
            "download_url": "/download/d1",
            "disponivel": True,
        },
        {
            "tipo": "D2",
            "label": "Petição Inicial",
            "descricao": "Fundamentos + jurisprudência + pedidos",
            "formato": "DOCX",
            "paginas": 18,
            "download_url": "/download/d2",
            "disponivel": True,
        },
        {
            "tipo": "D3",
            "label": "Apelação Cível",
            "descricao": (
                "Pré-redigida 100% — para decisão adversa"
                if has_decisao_adversa
                else "D3 só é gerada com decisão adversa enviada."
            ),
            "formato": "DOCX" if has_decisao_adversa else "—",
            "paginas": 24 if has_decisao_adversa else None,
            "download_url": "/download/d3" if has_decisao_adversa else None,
            "disponivel": has_decisao_adversa,
        },
    ]


@app.get("/verdict", response_class=HTMLResponse)
async def verdict(request: Request, job_id: str = "") -> HTMLResponse:
    """MVP-LEAN-01 Task 5: renderiza S6 Resultado consolidado (3 deliverables + D3 condicional)."""
    if not request.session.get("user"):
        return RedirectResponse("/login", status_code=303)

    if job_id and job_id in JOBS and JOBS[job_id].get("verdict"):
        verdict_data = JOBS[job_id]["verdict"]
        filename = JOBS[job_id]["filename"]
        has_decisao_adversa = JOBS[job_id].get("has_decisao_adversa", False)
    else:
        verdict_data = MOCK_VERDICT
        filename = MOCK_VERDICT.get("filename", "contrato.pdf")
        has_decisao_adversa = False

    # Hash truncado 4+4 chars (placeholder; real virá de verdict.audit_hash quando workflow popular)
    full_hash = verdict_data.get("audit_hash", "7a3fb91c-b8d1") if verdict_data else ""
    deliverables = _format_deliverables_for_c5(verdict_data, has_decisao_adversa)

    s6_context: dict[str, Any] = {
        "verdict": verdict_data,
        "filename": filename,
        "deliverables": deliverables,
        "has_decisao_adversa": has_decisao_adversa,
        "hash_full": full_hash,
        "hash_truncado": _truncate_hash(full_hash),
        "audit_entry_id": verdict_data.get("audit_entry_id", 137) if verdict_data else 0,
        "tempo_total": verdict_data.get("tempo_total", "2min 47s") if verdict_data else "—",
        "veredicto_tese": (
            verdict_data.get("tese", "Há indícios de abusividade na taxa de juros pactuada.")
            if verdict_data
            else "—"
        ),
        "confianca": verdict_data.get("confianca", 0.83) if verdict_data else None,
        "citacoes_validadas": (
            verdict_data.get("citacoes_validadas", "4/4") if verdict_data else "—"
        ),
        "job_id": job_id,
    }
    s6_context.update(_layout_context(request))
    return templates.TemplateResponse(
        request=request,
        name="s6_resultado.html",
        context=s6_context,
    )


# MVP-LEAN-01 Task 5 — AC-MVP-D3-DUAL-INPUT: stub para re-rodar D3 quando S6.b CTA clicada
@app.post("/revisar/d3", response_class=HTMLResponse)
async def revisar_d3(
    request: Request,
    job_id: str = Form(...),
    pdf_decisao_adversa: UploadFile | None = None,
) -> HTMLResponse:
    """Stub D3 re-run — atualmente apenas marca has_decisao_adversa=True e redireciona.

    Tech debt: TD-MVP-LEAN-05-D3-RE-RUN — refatorar revisar_contrato para suportar
    re-run apenas D3 sem reprocessar D1+D2 (pós-MVP).
    """
    if not request.session.get("user"):
        return RedirectResponse("/login", status_code=303)
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    if not (pdf_decisao_adversa and pdf_decisao_adversa.size):
        raise HTTPException(status_code=400, detail="PDF de decisão adversa obrigatório")
    JOBS[job_id]["has_decisao_adversa"] = True
    return RedirectResponse(f"/verdict?job_id={job_id}", status_code=303)


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
