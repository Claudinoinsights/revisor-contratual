---
type: story
id: TD-SP06-SPA-CONNECT-01
title: "SPA dropzone → POST /revisar real + EventSource SSE (eliminar mock client-side ANALYSIS ENGINE)"
status: Ready for Review
priority: 1
validated_by: "@po (Keymaker)"
validated_at: "2026-05-14"
validation_score: "10/10"
implemented_by: "@dev (Neo)"
implemented_at: "2026-05-14"
implementation_evidence: "10/10 tests PASS Python 3.14 (3 dual-content-type + 7 classic_route) + 248 baseline maintained + 100% mock removal SPA"
adr_ref: "ADR-021 dual-content-type accepted 2026-05-14"
sprint: "6.x AGGRESSIVE"
epic: "Sprint-6-Bloco-Beta-Frontend-Backend-Integration"
owner: "@dev (Neo)"
estimated_effort: "2-3h"
severity_origem: "CRITICAL (core Bloco β — substituir mock 100% client-side por integração real)"
created: "2026-05-14"
created_by: "@sm (River)"
depends_on:
  - "TD-SP06-CLASSIC-01 (precondition NOT — pode rodar em paralelo)"
related_adrs:
  - "ADR-020 Multi-Doctype Dispatcher v2 (7 modos sidebar — mapping data-mode → backend modalidade em TD-SP06-MODE-PASS-01)"
  - "Decisão arquitetural ADR-022 dual-content-type POST /revisar (HTML legacy + JSON SPA) — pendente Aria mini-ADR"
related_stories:
  - "TD-SP06-CLASSIC-01 (alternativa Jinja2 — pode coexistir com SPA pós-integração)"
  - "TD-SP06-MODE-PASS-01 (complementar — sidebar mode passing)"
  - "TD-SP06-PHASE-VALID-01 (complementar — UI error states)"
related_findings:
  - "Smith Fase 7-A F-D1-01 CRITICAL: SPA index.html:1831 ANALYSIS ENGINE (mock) confirmed"
  - "Smith Fase 7-A F-D1-02 CRITICAL: index.html:2065 buildPdf JS puro (PDF horrível)"
  - "Smith Fase 7-A F-D1-03 CRITICAL: SPA NÃO chama /revisar, /pipeline-stream, EventSource, FormData"
  - "Smith Fase 7-A F-D1-04 CRITICAL: Dropzone decorativo (addFiles só local)"
unblocks:
  - "Eric demo real via SPA OrSheva 7 (preserva visual Sprint 5+ Bloco 3)"
  - "Eliminação FINDINGS_BY_MODE hardcoded — análise vira derivada LLM real"
  - "DoD Sprint 6 AGGRESSIVE: zero mock residual na aplicação"
tags:
  - project/revisor-contratual
  - story
  - sprint-6
  - bloco-beta
  - spa-real-integration
  - eliminate-mock
  - draft
---

# Story TD-SP06-SPA-CONNECT-01 — SPA → Pipeline Real

## Story

**Como** advogado revisor usando o SPA OrSheva 7 (Sprint 5+ Bloco 3 wireframe entregue),
**Eu quero** que o upload do meu PDF seja enviado REAL ao backend FastAPI e que o processamento real (parsing PyMuPDF4LLM + cálculo Price/anatocismo + BACEN SGS + Vault híbrido + Personas LLM sabia-7b/qwen2.5 paralelas + Juiz Python) seja exibido em tempo real via Server-Sent Events,
**Para que** eu receba análise jurídica REAL do meu contrato (não simulação setTimeout fake) com findings derivados da LLM (não catálogo `FINDINGS_BY_MODE` hardcoded) e veredito com aderência calculada (não Math.random 58-94%).

---

## Contexto

**Trigger:** Smith Fase 7-A 2026-05-14 verdict 🔴 COMPROMISED — confirmado empíricamente que SPA `static/index.html` é wireframe 100% mock:

- Linha 1831: `// ============ ANALYSIS ENGINE (mock) ============`
- Linha 1872-1903: `runAnalysis()` setTimeout 900-1800ms fake por fase
- Linha 1906: `// ============ RESULT GENERATION (mock plausível) ============`
- Linha 1918-1956: `FINDINGS_BY_MODE` catálogo estático 6 modos × 3-4 findings hardcoded
- Linha 2019-2110: `buildPdf(lines)` PDF JS puro com BT/ET Tj operators rudimentares — explica "PDF horrível"
- Linha 1822: `dropzone.addEventListener('drop', e => addFiles(e.dataTransfer.files))` — arquivos só armazenados em var local `files`, **nunca enviados ao backend**

**Backend real EXISTS** (Smith Bloco α 2026-05-14 confirmou empíricamente):

- `POST /revisar` (linha 650 app.py) processa upload + cria job + retorna `s5_processing.html` com job_id
- `GET /revisar/stream/{job_id}` (linha 771) SSE com 5 events + ping heartbeat 10s
- Pipeline real executado: parsing fidelity 1.0 + BACEN live SGS 25471 + Vault 5 docs + Personas LLM 1m36s + Juiz APROVADO_100 + audit HMAC chained

**Objetivo:** refatorar SPA para invocar pipeline REAL preservando OrSheva 7 visual.

---

## Acceptance Criteria

1. **AC-01:** `static/index.html` `btnAnalyze` event listener (atual linhas 1850-1854 chamando `runAnalysis()` mock) refatorado para chamar nova função `submitAnalysisReal()` que:
   - Cria `FormData` com:
     - `pdf` (file objeto first user upload)
     - `uf` (currentUF state OR null → backend detecta)
     - `data` (currentData state OR null → backend detecta)
     - `tier` (default "balanced")
   - POST async `/revisar` com:
     - `credentials: 'same-origin'`
     - `headers: { 'X-CSRF-Token': CSRF_TOKEN }`
     - `Accept: application/json` (request dual-content-type response JSON)
   - Recebe response JSON `{job_id, status, deliverables_url}` (backend retorna JSON quando Accept JSON; senão HTML como antes)

2. **AC-02:** Após response com job_id, SPA conecta `EventSource('/revisar/stream/{job_id}')`:
   - URL preserva session cookie httpOnly (credentials carry implicit)
   - Listeners: `phase-start`, `phase-done`, `ping`, `complete`, `phase-error`
   - Cleanup: `eventSource.close()` em `complete` ou `phase-error`

3. **AC-03:** Handlers SSE atualizam UI fases existentes (reuso `STEP_NAMES` + `setStep()` + `progressFill`):
   - `phase-start` event → setStep(currentIndex, 'active') + phaseChip.textContent = phase
   - `phase-done` event → setStep(currentIndex, 'done') + progressFill width incremental
   - `ping` event → atualizar tempo decorrido (não acionar timeout)
   - `complete` event → setStep(all, 'done') + progressFill 100% + showResultReal(deliverables)
   - `phase-error` event → showErrorRealS7(diagnostic, cause, solution, alternative)

4. **AC-04:** Função mock `runAnalysis()` (linhas 1872-1903) **REMOVIDA** completamente.

5. **AC-05:** Função `showResult()` refatorada → `showResultReal(deliverables)`:
   - Recebe deliverables JSON: `{veredito, aderencia, c1_score, c2_score, c3_score, razoes, tese, fundamentos, citacoes_validadas}`
   - Renderiza findings derivados de `deliverables.fundamentos` (não FINDINGS_BY_MODE)
   - Probability = `aderencia` (0-100, calculado pelo Juiz Python — não Math.random)
   - Passed = `veredito === "APROVADO_100"` || `veredito === "APROVADO_COM_RISCO_HITL"`

6. **AC-06:** Variável `FINDINGS_BY_MODE` (linhas 1918-1956 + função `pseudoRandom`) **REMOVIDA** completamente.

7. **AC-07:** Empirical smoke E2E:
   - Eric upload `data/test-fixtures/synthetic/contrato_veiculo_synthetic.pdf` via SPA dropzone
   - SPA POST /revisar → recebe job_id
   - SPA EventSource → progress real (parsing → cálculo → BACEN → vault → personas → juiz)
   - Após ~3-5min recebe complete event
   - SPA renderiza veredito **APROVADO_100** com aderência **100%** e c1=c2=c3=1.0
   - Audit.jsonl recebe nova entry com status SUCCESS (não cached prévia)

8. **AC-08:** Error handling fallback:
   - Response 401/403 → redirect `/classic` OR re-trigger login screen SPA
   - Response 503 (Ollama down) → mostrar `errorBanner` com mensagem + Retry-After header
   - EventSource error event → `phase-error` UI fallback

---

## Tasks / Subtasks

- [ ] Task 1: Decisão arquitetural dual-content-type POST /revisar
  - [ ] 1.1 Mini-ADR (ou inline ADR-022 cross-reference) decidir: backend POST /revisar responde JSON quando `Accept: application/json`, senão HTML legacy
  - [ ] 1.2 Alternativa: criar `POST /api/revisar` JSON-only (preserva /revisar HTML legacy Jinja2)
  - [ ] 1.3 Aria mini-decision via Skill OR Operator-Neo consenso documentado em PR description
- [ ] Task 2: Backend dual-content-type (se decisão = single endpoint)
  - [ ] 2.1 `POST /revisar` linha 650: detectar `request.headers.get("Accept") == "application/json"` → response JSON `{job_id, status, deliverables_url}`
  - [ ] 2.2 Preservar Jinja2 HTML response default (compat /classic Jinja2)
- [ ] Task 3: SPA `submitAnalysisReal()` implementation
  - [ ] 3.1 Função async em `static/index.html` substituindo `runAnalysis()` mock
  - [ ] 3.2 FormData build com pdf file + currentMode + currentUF + currentData + tier
  - [ ] 3.3 fetch POST /revisar com headers e credentials
  - [ ] 3.4 Parse JSON response → extract job_id
  - [ ] 3.5 Tratamento erros 4xx/5xx com error handler S7
- [ ] Task 4: SPA EventSource SSE handlers
  - [ ] 4.1 `new EventSource('/revisar/stream/' + job_id)`
  - [ ] 4.2 addEventListener para 5 events tipo SSE
  - [ ] 4.3 State machine UI: idle → phase-start → phase-done × N → complete OR phase-error
  - [ ] 4.4 Cleanup em terminal events
- [ ] Task 5: Refactor showResult → showResultReal(deliverables)
  - [ ] 5.1 Remover render seed-based pseudoRandom
  - [ ] 5.2 Render findings de deliverables.fundamentos (sev derivado de aderencia faixas)
  - [ ] 5.3 Probability = deliverables.aderencia
  - [ ] 5.4 Verdict text dinâmico baseado em veredito enum
- [ ] Task 6: REMOÇÃO código mock
  - [ ] 6.1 Delete linhas 1872-1903 (runAnalysis)
  - [ ] 6.2 Delete linhas 1906-1956 (RESULT GENERATION + FINDINGS_BY_MODE + pseudoRandom)
  - [ ] 6.3 Delete linhas 2065-2110 (buildPdf JS — substituído por backend weasyprint em Bloco γ)
  - [ ] 6.4 btnDownload disabled OR redirect deliverables URL real (preparar para Bloco γ /download/d1)
- [ ] Task 7: Error handler SPA fallback
  - [ ] 7.1 errorBanner com 4 campos S7 (diagnostic, cause, solution, alternative)
  - [ ] 7.2 401/403 → redirect /classic OR re-show screen-login
  - [ ] 7.3 503 Retry-After parsing
- [ ] Task 8: Testes
  - [ ] 8.1 Manual smoke E2E browser DevTools: F12 Network tab → ver POST /revisar 200 JSON + EventSource /revisar/stream/{job_id}
  - [ ] 8.2 Pytest regressão: 248 passed maintained
- [ ] Task 9: Update File List + Change Log
- [ ] Task 10: Self-critique checklist

---

## Dev Notes (Technical Context)

**Backend response shape esperado (AC-01):**

```json
POST /revisar (Accept: application/json) → 200
{
  "job_id": "uuid-...",
  "status": "running",
  "deliverables_url": "/verdict?job_id=uuid-...",
  "stream_url": "/revisar/stream/uuid-..."
}
```

**SSE events shape (existente backend Bloco α SUCCESS):**

```
event: phase-start
data: {"phase": "parsing_pdf", "started_at": 12345.67}

event: phase-done
data: {"phase": "parsing_pdf", "elapsed_s": 2.4}

event: ping
data: {"ts": 12348.07}

event: complete
data: {"job_id": "uuid-...", "total_elapsed_s": 210.5, "deliverables": {<VeredictoJuiz dict>}}

event: phase-error
data: {"phase": "vault", "diagnostic": "...", "cause": "...", "solution": "...", "alternative": "..."}
```

**VeredictoJuiz schema** (de `bloco_contratos/personas.py` linha 91):

```python
class VeredictoJuiz(BaseModel):
    c1_score: float = Field(..., ge=0.0, le=1.0)
    c2_score: float = Field(..., ge=0.0, le=1.0)
    c3_score: float = Field(..., ge=0.0, le=1.0)
    aderencia: float = Field(..., ge=0.0, le=100.0)
    veredito: VereditoTipo  # "APROVADO_100" | "APROVADO_COM_RISCO_HITL" | "REJEITADO"
    razoes: list[str]
```

**EventSource limitations:**
- GET only — sem custom headers (CSRF token via query OR session cookie)
- Session cookie httpOnly carry implicit
- Reconnect automático browser-side

**CSRF mitigation:** SSE valida session cookie httpOnly (já validado em /api/me + /login). EventSource não exige CSRF token explicit porque GET é safe método.

**Locations relevantes** (Smith probe Bloco α evidências):
- `static/index.html` linha 1326-1334 dropzone HTML (preservar)
- linha 1749 `const dropzone = document.getElementById('dropzone')` (reuso)
- linha 1850-1854 btnAnalyze listener (refatorar)
- linha 1514 `let CSRF_TOKEN = ''` (reuso)

**TDs pré-existentes não-bloqueadores Sprint 6 Bloco β:**
- TD-SP06-OLLAMA-DUAL-PORT-VERIFICATION (Smith F-D1-α-02 MEDIUM — irrelevante para SPA UX)
- TD-SP06-VAULT-ONLY-10-DOCS (smoke pass com 5 docs)
- TD-SP06-SENTENCE-TRANSFORMERS-MISSING (BM25-only OK para smoke)

---

## Testing

**Manual E2E browser (Operator + Eric pós-implementação Neo):**

1. Abrir DevTools (F12) Network tab + Console tab
2. Login admin/admin via SPA
3. Sidebar selecionar modo "Financiamento Veículo"
4. Drag-drop `data/test-fixtures/synthetic/contrato_veiculo_synthetic.pdf` no dropzone
5. Click "Analisar"
6. **Network tab verificar:**
   - POST /revisar 200 JSON com job_id
   - EventSource /revisar/stream/{job_id} streaming events
7. **UI verificar:**
   - Fase 0 (Ingestão) → active → done
   - Fase 1 (Identificação) → active → done
   - Fase 2 (Cláusulas) → active → done
   - Fase 3 (Verificação BACEN) → active → done
   - Fase 4 (Cálculo + Vault) → active → done
   - Fase 5 (Síntese LLM) → active 1-3min → done
8. Veredito APROVADO_100 + probabilidade 100% + findings derivados LLM (não FINDINGS_BY_MODE)
9. **Audit verificar:**
   ```bash
   tail -1 ~/.local/share/revisor-contratual/audit.jsonl | jq .payload.status
   # Esperado: "SUCCESS"
   ```

**Pytest regressão:** mesmo comando de TD-SP06-CLASSIC-01.

---

## Dev Agent Record

**Agent Model Used:** Claude Opus 4.7 (via Skill LMAS:agents:dev)

**Debug Log References:**
- Pytest baseline pré + pós edits idêntico (248 passed + 2 pre-existing failures)
- 10/10 tests PASS Python 3.14 (3 dual-content-type backend + 7 classic_route preserved)
- Empirical verify: `grep "FINDINGS_BY_MODE|pseudoRandom|buildPdf|function runAnalysis|function showResult\(\)"` → apenas 1 match (comentário documentando refactor, não código mock)

**Completion Notes List:**

- Backend `POST /revisar`: 2 edits cirúrgicos (signature `-> HTMLResponse` → `-> Any` + branch JSON antes do TemplateResponse) seguindo ADR-021 Opção A
- JSON schema implementado: `{job_id, status, filename, stream_url, verdict_url, has_decisao_adversa}` (conforme ADR-021)
- SPA refactor: 4 edits major em `static/index.html`:
  - `runAnalysis()` mock setTimeout → `submitAnalysisReal()` async fetch POST /revisar
  - `showResult()` FINDINGS_BY_MODE hardcoded → `showResultReal(deliverables, verdictUrl)` renderiza VeredictoJuiz real
  - REMOVIDO: `pseudoRandom`, `FINDINGS_BY_MODE` catálogo (7 modos × 3-4 findings), `buildPdf` JS PDF generation
  - btnDownload → placeholder Bloco γ (alert mostrando veredito + aderência real até weasyprint backend shipped)
- NOVO: `connectPipelineStream(streamUrl, verdictUrl)` com 5 SSE listeners (phase-start, phase-done, ping, complete, phase-error)
- NOVO: `showErrorRealS7(payload)` minimal — Wave 3 (TD-SP06-PHASE-VALID-01) evolui para S7 pane completo
- Backward compat 100%: Jinja2 /classic flow (s2_pre_upload action="/revisar") inalterado — fall-through TemplateResponse preservado
- AC-08 fallback 401/403 → SPA mostra erro message; 503 Ollama → mensagem genérica (Wave 3 phase-error S7 pane refina)

**File List:**

- `bloco_interface/web/app.py` (MODIFIED — 2 edits cirúrgicos):
  - Line 690: `@app.post("/revisar", response_class=HTMLResponse)` → `@app.post("/revisar")`
  - Line 698: `-> HTMLResponse` → `-> Any`
  - Lines 793-808: NEW JSON branch (ADR-021 dual-content-type) antes do TemplateResponse legacy
- `bloco_interface/web/static/index.html` (MODIFIED — 4 edits major refactor):
  - Line 1831-1834: STEP_NAMES comment update + `activeEventSource` global
  - Line 1853: `btnAnalyze` handler `runAnalysis()` → `submitAnalysisReal()`
  - Lines 1872-2003: REPLACED runAnalysis mock + showResult mock + FINDINGS_BY_MODE + pseudoRandom (~130 lines mock) por `submitAnalysisReal()` + `connectPipelineStream()` + `showResultReal()` + `showErrorRealS7()` (~180 lines real)
  - Lines 2018-2133: REMOVED buildPdf JS + complex btnDownload mock → placeholder Bloco γ alert (~10 lines)
- `tests/unit/test_revisar_dual_content_type.py` (NEW — 130 lines, 3 tests + monkeypatch fixture):
  - test_post_revisar_with_accept_json_returns_json_response
  - test_post_revisar_without_accept_returns_html_legacy
  - test_post_revisar_invalid_pdf_returns_400 (preserved magic bytes validation)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-05-14 | @sm (River) | Draft inicial Bloco β Sprint 6 AGGRESSIVE — core integração SPA↔backend |
| 2026-05-14 | @po (Keymaker) | Validation 10/10 score → status Draft → Ready |
| 2026-05-14 | @architect (Aria) | ADR-021 dual-content-type accepted — Opção A escolhida (mirror POST /login pattern) |
| 2026-05-14 | @dev (Neo) | Implementação completa: backend dual-content-type + SPA refactor remoção 100% mock + 10/10 tests PASS Python 3.14 + pytest baseline 248 mantido. Status Ready → Ready for Review. |
