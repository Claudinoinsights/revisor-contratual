"""FastAPI app — Revisor Contratual UI Web.

Substitui Streamlit (REV-INT-01). Filosofia: HTMX-driven, partial swaps,
mock data até Sprint 02 STORY UI-1 conectar pipeline real.

Endpoints:
    GET  /                  → index.html (estado idle)
    POST /revisar           → partials/processing.html (multipart upload)
    GET  /pipeline-stream   → SSE com 7 steps (~3s mock)
    GET  /verdict           → partials/verdict.html (mock APROVADO_HITL)
    POST /reset             → partials/idle.html
    GET  /static/*          → CSS/JS (montado abaixo)
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ── Paths ─────────────────────────────────────────────────────────────────
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

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

# ── Mock data (REV-INT-01 — substituído em Sprint 02 STORY UI-1) ─────────
MOCK_HISTORY = [
    {
        "name": "contrato-bb-45.pdf",
        "verdict": "hitl",
        "label": "HITL",
        "score": 78,
        "when": "12m",
    },
    {
        "name": "caixa-5829.pdf",
        "verdict": "aprovado-100",
        "label": "100",
        "score": 100,
        "when": "ontem",
    },
    {
        "name": "santander-1.pdf",
        "verdict": "rejeitado",
        "label": "REJ",
        "score": 65,
        "when": "3d",
    },
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
}

# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(title="Revisor Contratual", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


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
    tier: str = Form(default="premium"),
) -> HTMLResponse:
    filename = pdf.filename or "contrato.pdf"
    return templates.TemplateResponse(
        request=request,
        name="partials/processing.html",
        context={
            "filename": filename,
            "uf": uf,
            "data": data,
            "tier": tier,
            "steps": PIPELINE_STEPS,
        },
    )


@app.get("/pipeline-stream")
async def pipeline_stream() -> StreamingResponse:
    async def event_generator() -> asyncio.AsyncIterator[str]:
        total = len(PIPELINE_STEPS)
        for i in range(total):
            payload = {"index": i, "total": total, "step": PIPELINE_STEPS[i], "done": False}
            yield f"event: step\ndata: {json.dumps(payload)}\n\n"
            await asyncio.sleep(0.4)
        yield f"event: step\ndata: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/verdict", response_class=HTMLResponse)
async def verdict(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="partials/verdict.html",
        context={"verdict": MOCK_VERDICT},
    )


@app.post("/reset", response_class=HTMLResponse)
async def reset(request: Request) -> HTMLResponse:
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
