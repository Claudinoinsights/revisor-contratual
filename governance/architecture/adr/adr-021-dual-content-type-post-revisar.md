---
type: adr
id: "ADR-021"
title: "Dual Content-Type para POST /revisar — JSON (SPA) + HTML (Jinja2 legacy)"
status: accepted
adr_level: design
date: "2026-05-14"
domain: "frontend-backend-integration"
decision_makers: ["@architect (Aria)"]
supersedes: null
superseded_by: null
related_adrs:
  - "ADR-020 Multi-Doctype Dispatcher v2 (7 modos sidebar SPA)"
  - "TD-SP06-CLASSIC-01 Wave 1 (POST /login JÁ é dual-content-type — padrão precedent)"
related_stories:
  - "TD-SP06-SPA-CONNECT-01 (Wave 2 unblock — Neo implementa baseado nesta ADR)"
  - "TD-SP06-CLASSIC-01 (Wave 1 done — coexistência Jinja2 + SPA)"
impacts:
  - "bloco_interface/web/app.py POST /revisar handler (linha 690-820)"
  - "SPA static/index.html submitAnalysisReal() (Wave 2 implementation)"
  - "Templates Jinja2 s2_pre_upload.html action /revisar (preserved)"
tags:
  - project/revisor-contratual
  - adr
  - sprint-6
  - frontend-backend-integration
  - dual-content-type
---

# ADR-021 — Dual Content-Type para POST /revisar

## Status

✅ **Accepted** (2026-05-14)

## Contexto

Sprint 6.x AGGRESSIVE Bloco β tem objetivo de eliminar mock 100% client-side no SPA OrSheva 7 (Sprint 5+ Bloco 3 wireframe) substituindo por integração REAL com backend pipeline `revisar_contrato` (parsing + cálculo + BACEN + vault + personas LLM + juiz).

Smith Bloco α (2026-05-14) provou empiricamente que pipeline funciona end-to-end (audit HMAC SUCCESS, Ollama POST /api/chat 1m36s real). Story TD-SP06-CLASSIC-01 (Wave 1 done) adicionou rota `GET /classic` que serve templates Jinja2 legacy ao backend real, desbloqueando demo imediato.

**Problema arquitetural:** SPA precisa fazer `POST /revisar` com upload PDF + receber **JSON response com `job_id`** para conectar `EventSource('/revisar/stream/{job_id}')`. Backend atual (linha 690-820 `app.py`) retorna `HTMLResponse` (template `s5_processing.html` com job_id embedded no DOM) — adequado para Jinja2 htmx flow mas inadequado para fetch JavaScript SPA.

**Restrições:**
- SPA Sprint 5+ Bloco 3 wireframe entregue NÃO deve quebrar (Sprint 5+ Bloco 3 closure FINAL)
- Templates Jinja2 (s2_pre_upload action="/revisar") devem continuar funcionando após ADR
- Backend `POST /revisar` tem 14 steps atomic shared: Ollama health-check, magic bytes validation, max_size, tempfile.mkstemp, JOBS dict state, data parsing — não pode ser duplicado
- Padrão dual-content-type JÁ EXISTE no projeto: `POST /login` (linha 558 `is_json` flag) — TD-SP06-CLASSIC-01 Wave 1 confirmou padrão funcional

## Decisão

**Adotar Opção A — Dual Content-Type Single Endpoint `POST /revisar`** com detecção via header `Accept: application/json` (analogous ao padrão `POST /login` linha 558).

### Comportamento decidido

```python
@app.post("/revisar")
async def revisar(
    request: Request,
    pdf: UploadFile,
    # ... 14 atomic shared steps (Ollama, magic bytes, tempfile, JOBS dict, data parsing)
) -> Any:
    # Steps 1-13: COMPARTILHADOS (não duplicar)
    # ... ollama health, max_size, magic bytes, tempfile.mkstemp,
    #     job_id uuid, JOBS dict state, data parsing ...

    # Step 14: BRANCH apenas no retorno
    accept = request.headers.get("accept", "").lower()
    wants_json = "application/json" in accept

    if wants_json:
        # SPA Sprint 5+ Bloco 3 flow
        return JSONResponse({
            "job_id": job_id,
            "status": "queued",
            "filename": filename,
            "stream_url": f"/revisar/stream/{job_id}",
            "verdict_url": f"/verdict?job_id={job_id}",
            "has_decisao_adversa": has_decisao_adversa,
        }, status_code=200)

    # Legacy Jinja2 flow (preserva s5_processing.html template render)
    return templates.TemplateResponse(
        request=request,
        name="s5_processing.html",
        context=s5_context,
    )
```

### Princípios da decisão

1. **Padrão precedent existente:** `POST /login` linha 558 `is_json` flag — Sprint 5+ UX-LOGIN-UNIFIED já validou este pattern (TD-SP06-CLASSIC-01 Wave 1 confirmed working with 7 unit tests PASS)
2. **Atomic share:** 14 steps de pre-processing (Ollama, validation, tempfile, JOBS state) NÃO devem ser duplicados — single endpoint preserva DRY
3. **Mínima cirurgia:** Branch only at return (linha 793-799) — ~10 lines added vs duplicar 130 lines em /api/revisar
4. **Future-compatible:** SPA Bloco γ futuro pode adicionar mais clients (mobile, API external) usando mesmo endpoint dual-mode
5. **Constitution Art. IV No Invention:** Pattern já existe — não inventar /api/revisar separate quando dual-content-type funciona

## Alternativas Consideradas

### Opção A — Dual Content-Type Single Endpoint ✅ ESCOLHIDA

**Mecanismo:** `request.headers.get("accept")` detecta `application/json` → JSON response; senão HTMLResponse template legacy.

| Critério | Avaliação |
|----------|-----------|
| DRY (atomic shared logic) | ✅ Excelente — zero duplicação |
| Precedent existente | ✅ POST /login já usa padrão |
| Cirurgia código | ✅ Mínima (~10 lines branch return) |
| Future extensibility | ✅ Multi-client capable |
| Separation of concerns | ⚠️ Handler tem 2 responsibilities (mas isolado em 1 if/else) |

### Opção B — Endpoint Separado `POST /api/revisar` JSON-only ❌ REJEITADA

**Mecanismo:** Manter /revisar HTML legacy; criar /api/revisar JSON-only para SPA.

| Critério | Avaliação |
|----------|-----------|
| DRY | ❌ Duplica 14 steps OR exige refactor para helper compartilhado |
| Future extensibility | ✅ Clean separation |
| Cirurgia | ❌ ~130 lines novo endpoint OR refactor extract helper |
| Coupling SPA ↔ Jinja2 | ✅ Zero coupling |
| Manutenção | ❌ 2 endpoints divergem over time (validation changes, etc) |

**Rejeição:** Custo alto refactor (extract helper de 14 steps) + risco divergência over time. Padrão `POST /login` dual-content-type já validado no projeto torna esta opção desnecessariamente complexa.

### Opção C — Server-Side Rendered Hybrid (HTML response + SPA scrape) ❌ REJEITADA

**Mecanismo:** /revisar sempre retorna HTML; SPA parsea HTML body para extrair `job_id` via `data-job-id` attribute.

| Critério | Avaliação |
|----------|-----------|
| Backend changes | ✅ Zero |
| RESTfulness | ❌ HTML scraping anti-pattern |
| Robustness | ❌ Fragil — DOM changes quebram SPA |
| Future API external | ❌ Não-viable (clients precisam parsear HTML) |
| Developer experience | ❌ Debugging pesadelo |

**Rejeição:** Anti-pattern crítico. SPA precisa parsing HTML estruturado client-side — qualquer refactor template Jinja2 (data-job-id position change) quebra integração silenciosamente.

## Consequências

### Positivas ✅

- **Mínima cirurgia código:** Apenas branch no return de POST /revisar (~10 lines)
- **DRY preservado:** 14 atomic steps shared SPA + Jinja2
- **Padrão consistente:** Mesmo dual-content-type de POST /login (cognitive load baixo)
- **Wave 1 + Wave 2 coexistência:** /classic Jinja2 (Wave 1 done) usa HTML branch; SPA Sprint 5+ Bloco 3 usa JSON branch
- **Future-proof:** Mobile app, API external podem reusar JSON branch sem novo endpoint

### Negativas ⚠️

- **Handler dual-responsibility:** POST /revisar lida com 2 response types em 1 função (mitigado: branch isolado em 1 if/else no final, lógica upstream compartilhada)
- **Acoplamento implícito:** SPA precisa enviar `Accept: application/json` header explicitamente — falha silenciosa se omitido (mitigado: SPA Wave 2 documentação clara + TD-SP06-SPA-CONNECT-01 AC explícita)
- **Versionamento futuro:** Mudança schema JSON precisa cuidado (mitigado: JSON response é internal API SPA-bound, sem clients external no MVP)

### Neutras ⚪

- **JSON schema definido aqui:** `{job_id, status, filename, stream_url, verdict_url, has_decisao_adversa}` é contract público entre backend e SPA — qualquer extensão futura ADR-incremental
- **Backward compat 100%:** Jinja2 flow (s2_pre_upload → /revisar → s5_processing) inalterado — Wave 1 /classic depende disto

## Implementação (guia para Neo Wave 2)

### TD-SP06-SPA-CONNECT-01 (Neo, Wave 2)

**Backend changes (bloco_interface/web/app.py POST /revisar):**

1. Adicionar `request: Request` parameter (se já não tem)
2. Mudar return signature: `-> HTMLResponse` → `-> Any` (suporta `JSONResponse | HTMLResponse`)
3. No final do handler (linha ~800 antes do `return templates.TemplateResponse`):

```python
# ADR-021 dual-content-type: SPA recebe JSON, Jinja2 legacy recebe HTML
accept = request.headers.get("accept", "").lower()
if "application/json" in accept:
    return JSONResponse({
        "job_id": job_id,
        "status": "queued",
        "filename": filename,
        "stream_url": f"/revisar/stream/{job_id}",
        "verdict_url": f"/verdict?job_id={job_id}",
        "has_decisao_adversa": has_decisao_adversa,
    }, status_code=200)

# Legacy Jinja2 flow (preserved)
return templates.TemplateResponse(
    request=request,
    name="s5_processing.html",
    context=s5_context,
)
```

**Frontend changes (static/index.html submitAnalysisReal):**

```javascript
const resp = await fetch('/revisar', {
  method: 'POST',
  credentials: 'same-origin',
  headers: {
    'Accept': 'application/json',  // ADR-021: trigger JSON branch
    'X-CSRF-Token': CSRF_TOKEN,
  },
  body: formData,
});

if (!resp.ok) {
  throw new Error(`HTTP ${resp.status}`);
}

const data = await resp.json();
// data = {job_id, status, filename, stream_url, verdict_url, has_decisao_adversa}

const eventSource = new EventSource(data.stream_url);
// ... SSE handlers
```

### Backward compat verification (Smith review pós-Wave 2)

- `curl -X POST /revisar -F pdf=@file.pdf` (sem Accept) → HTMLResponse s5_processing.html ✅ (Jinja2 flow)
- `curl -X POST /revisar -H "Accept: application/json" -F pdf=@file.pdf` → JSONResponse ✅ (SPA flow)

## Histórico

| Data | Mudança | Autor |
|------|---------|-------|
| 2026-05-14 | Criação ADR — decisão Opção A (dual-content-type single endpoint) | @architect (Aria) |

## Referências

- [POST /login dual-content-type linha 558 app.py](../../bloco_interface/web/app.py#L558) — precedent pattern
- [TD-SP06-CLASSIC-01 Wave 1](../../governance/stories/TD-SP06-CLASSIC-01.md) — Sprint 6 Bloco β predecessor
- [TD-SP06-SPA-CONNECT-01 Wave 2](../../governance/stories/TD-SP06-SPA-CONNECT-01.md) — Story que implementa esta ADR
- [Smith Bloco α CONTAINED report](../../governance/qa/smith-review-bloco-alpha-pos-execution-2026-05-14.md) — pipeline real validated

---

*— Aria, arquitetando o futuro 🏗️*
*"Padrões consistentes são pontes invisíveis. Dual-content-type aqui mirrors dual-content-type lá. Neo construirá Wave 2 sobre fundação familiar."*
