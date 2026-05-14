---
type: story
id: TD-SP06.2-WWW-AUTHENTICATE-MIDDLEWARE
title: "Override error_handler middleware — preservar WWW-Authenticate header em 401 (RFC 7235 compliance)"
status: Ready for Review
priority: 1
sprint: "6.2 middleware override"
validated_by: "@po (Keymaker)"
validated_at: "2026-05-14"
validation_score: "10/10"
validation_verdict: "GO"
epic: "Sprint-6-Bloco-Gamma-Peca-Revisional-AI (post-launch hotfix series)"
wave: "6.2.1 (single story)"
owner: "@dev (Neo)"
estimated_effort: "3h"
severity_origem: "MEDIUM (RFC 7235 compliance — clientes HTTP standard não auto-prompt re-auth)"
created: "2026-05-14"
created_by: "@sm (River)"
related_adrs:
  - "ADR-022 D7 SSE-OWNERSHIP-CHECK (precedent /download endpoint)"
related_findings:
  - "Smith Sprint 6.1 F-6.1-01 LOW (parcial fix source-level apenas)"
  - "TD-SP06.2-WWW-AUTHENTICATE-MIDDLEWARE catalogated Sprint 6.1 Wave 6.1.3"
related_stories:
  - "TD-SP06.1-DOWNLOAD-EDGE-CASES (Sprint 6.1 — partial fix WWW-Authenticate source-level)"
  - "TD-SP06-DOWNLOAD-ROUTES-01 (Bloco γ original — endpoint base)"
tags:
  - project/revisor-contratual
  - story
  - sprint-6-2
  - middleware-override
  - http-standard
  - rfc-7235
  - ready
---

# Story TD-SP06.2-WWW-AUTHENTICATE-MIDDLEWARE — Override middleware preservar headers

## Story

**Como** cliente HTTP standard (curl, Python requests, browser non-SPA) consumindo a API Revisor Contratual SaaS,
**Eu quero** receber o header `WWW-Authenticate: Session` em responses 401 conforme RFC 7235,
**Para que** eu possa auto-prompt re-autenticação programaticamente sem precisar inferir o auth scheme empiricamente.

---

## Contexto

Sprint 6.1 Wave 6.1.3 (Smith F-γ-08 fix) implementou `headers={"WWW-Authenticate": "Session"}` em `HTTPException 401` no endpoint `/download/{job_id}`. Source verificado correto (`app.py:909` linha do raise).

**Problema:** Middleware `error_handler` do projeto (instalado em `bloco_interface/web/error_handler.py`) intercepta responses 401 e reescreve para HTML `s7_error.html` template, **swallowing custom headers** passados via `HTTPException(headers=...)` kwarg.

Smith Sprint 6.1 review classificou como TD partial fix (LOW) — Sprint 6.2 scope override middleware preservation.

---

## Acceptance Criteria

- **AC-01:** Endpoint `/download/{job_id}` 401 Response inclui header `WWW-Authenticate: Session` accessível pelo cliente (verificável via `response.headers.get("www-authenticate") == "Session"`)
- **AC-02:** Substituir test `test_401_endpoint_specifies_www_authenticate_in_exception` (Sprint 6.1 workaround source-level) por `test_401_includes_www_authenticate_header_in_response` (validação direct header read)
- **AC-03:** Comportamento middleware error_handler `s7_error.html` HTML fallback preservado para casos SEM custom headers (backward compat — Bloco β SPA HTML rendering)
- **AC-04:** Outros endpoints que possam raise 401 (POST /login com auth falha, GET /api/me sem session, etc) também preservam WWW-Authenticate quando explicitly setado em HTTPException(headers={...}) — consistency check
- **AC-05:** Pytest baseline 492 → **493+ PASS ZERO regressões** (existing test_download_401_unauthenticated_rejected continua PASS + novo test 6.2)
- **AC-06:** Existing test `test_401_endpoint_specifies_www_authenticate_in_exception` removido OR atualizado para assertion direta no response header

---

## Tasks / Subtasks

- [x] Task 1: Debug middleware behavior atual
  - [x] 1.1 Ler `bloco_interface/web/error_handler.py` — entender how 401 é processed
  - [x] 1.2 Identificar onde custom headers de `HTTPException(headers=...)` são swallowed
  - [x] 1.3 Confirmar se é middleware OR exception handler global
- [x] Task 2: Implementar fix (Neo escolhe approach — Niobe recomenda Approach A)
  - [x] 2.1 Custom exception handler para HTTPException com exc.headers preservation
  - [x] 2.2 Backward compat HTML s7_error preservado para casos sem custom headers
  - [x] 2.3 Localização: `error_handler.py` OR registration em `app.py`
- [x] Task 3: Atualizar test existente
  - [x] 3.1 Substituir test source-level (Sprint 6.1) por test direct response header (Sprint 6.2)
  - [x] 3.2 Assertion: `response.headers.get("www-authenticate") == "Session"`
- [ ] Task 4: Consistency check outros 401s (DEFERRED Sprint 6.3 — handoff Keymaker explicit "opcional Sprint 6.2 OR defer se scope creep")
  - [ ] 4.1 Identificar outros endpoints raise 401 (POST /login, GET /api/me, etc)
  - [ ] 4.2 Adicionar WWW-Authenticate header se aplicável
  - [ ] 4.3 Test cross-endpoint consistency (opcional Sprint 6.2 OR defer Sprint 6.3)
- [x] Task 5: Pytest baseline regression check (492 PASS ZERO regressões — test substituído 1:1)
- [x] Task 6: Update File List + Change Log
- [x] Task 7: Self-critique + handoff Smith review pos-Sprint 6.2

---

## Dev Notes (Technical Context)

**Smith Sprint 6.1 review F-6.1-01 LOW:** Layer middleware swallow custom headers. Source fix aplicado mas client-facing behavior pendente. TD-SP06.2 escopo override.

### 3 Approach Options (Neo decide)

#### Approach A (RECOMENDADO Niobe): Custom exception handler FastAPI

```python
# bloco_interface/web/error_handler.py OR app.py
from fastapi import Request
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Preserva exc.headers em Response final (Sprint 6.2 F-6.1-01 fix).

    HTML s7_error fallback ainda invocado para casos sem custom headers (backward compat).
    """
    if exc.headers and any("www-authenticate" == k.lower() for k in exc.headers.keys()):
        # Custom headers path — Response direto, sem template render
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )
    # Default path — preserve middleware error_handler s7_error existing behavior
    return await original_error_handler_middleware(request, exc)
```

**Prós:** Mínima invasão + preserva HTML s7_error legacy + idiomatic FastAPI + escalável (AC-04).
**Contras:** Precisa import/refer middleware original como fallback delegate.

#### Approach B: Middleware order modification

Reorder middleware stack na app init. Mais complexo, pode quebrar fluxos.

#### Approach C: Custom Response no endpoint /download (anti-pattern)

`return Response(status_code=401, headers=..., content=...)` direto. Anti-idiomatic, não escalável para outros 401s.

### Localização sugerida fix

- **Option 1:** `bloco_interface/web/error_handler.py` — adicionar custom_http_exception_handler exportável + app.py register
- **Option 2:** `bloco_interface/web/app.py` — registrar `@app.exception_handler` inline

---

## Testing

**Test novo (substitui Sprint 6.1 source-level workaround):**

```python
def test_401_includes_www_authenticate_header_in_response(
    unauth_client: TestClient, populated_job: str
) -> None:
    """Sprint 6.2 F-6.1-01 completar fix: 401 Response inclui WWW-Authenticate accessible cliente."""
    response = unauth_client.get(f"/download/{populated_job}")
    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Session"
```

**Baseline regressão:** 492 → 493+ PASS ZERO regressões.

---

## Dev Agent Record

**Agent Model Used:** Neo (claude-opus-4-7[1m])

**Debug Log References:**
- Pytest baseline pré-fix: 492 passed + 5 skipped (47.85s)
- Pytest baseline pós-fix: 492 passed + 5 skipped (test substituído 1:1, ZERO regressões)
- Test novo: `tests/unit/test_download_route.py::test_401_includes_www_authenticate_header_in_response` PASS
- Test substituído: `test_401_endpoint_specifies_www_authenticate_in_exception` (Sprint 6.1 source-level workaround usando `inspect.getsource`)

**Completion Notes List:**
- Layer middleware swallow **identificado em `bloco_interface/web/app.py:432`** — NÃO em `error_handler.py` como Sprint 6.1 Wave 6.1.3 suspeitou. O `@app.exception_handler(HTTPException)` decorator já existia e criava `TemplateResponse` para 401/403 sem propagar `exc.headers`.
- Approach A (Niobe recommended) aplicado de forma surgical: custom exception handler já existia — fix foi adicionar loop de propagação `exc.headers` após criação do `TemplateResponse` no path 401/403.
- Backward compat preservado: HTML `s7_error.html` template renderiza normalmente para casos sem custom headers (Bloco β SPA HTML rendering intacto). Headers são propagados apenas quando explicitly setados em `HTTPException(headers={...})`.
- Task 4 (cross-endpoint consistency check) **deferido Sprint 6.3** conforme handoff Keymaker explicit: "Task 4 opcional Sprint 6.2 OR defer Sprint 6.3 se scope creep". Justificativa: scope Sprint 6.2 é single story; criar TD-SP06.3-CROSS-ENDPOINT-401-CONSISTENCY se outros 401s detectados.
- Effort actual: ~30min (vs ~3h estimate) — exception_handler já existia, fix surgical foi loop de 3 linhas.

**File List:**
- `bloco_interface/web/app.py` (MODIFIED) — exception_handler 401/403 path propaga `exc.headers` via loop explicit pós-TemplateResponse (RFC 7235 F-6.1-01 fix)
- `tests/unit/test_download_route.py` (MODIFIED) — substituiu `test_401_endpoint_specifies_www_authenticate_in_exception` (Sprint 6.1 source-level workaround via `inspect.getsource`) por `test_401_includes_www_authenticate_header_in_response` (direct `response.headers.get("www-authenticate") == "Session"` assertion)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-05-14 | @sm (River) | Draft Sprint 6.2 single story — middleware override preservar WWW-Authenticate header (Smith F-6.1-01 LOW partial fix completar — RFC 7235 compliance) |
| 2026-05-14 | @po (Keymaker) | Validate-story-draft GO 10/10 (Constitution Art. III/IV/V PASS) — status Draft → Ready |
| 2026-05-14 | @dev (Neo) | Sprint 6.2 fix implementado: `app.py:432` exception_handler propaga `exc.headers` em 401/403 path (loop explicit pós-TemplateResponse). Test substituído source-level → direct response header (RFC 7235 compliance). Pytest 492 PASS ZERO regressões. Task 4 consistency check defer Sprint 6.3. Status InProgress → Ready for Review. |
