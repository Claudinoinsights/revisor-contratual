---
type: story
id: TD-SP06-CLASSIC-01
title: "Rota GET /classic — Jinja2 bypass do SPA mock (desbloquear pipeline real imediato)"
status: Ready for Review
priority: 1
validated_by: "@po (Keymaker)"
validated_at: "2026-05-14"
validation_score: "10/10"
implemented_by: "@dev (Neo)"
implemented_at: "2026-05-14"
implementation_evidence: "7/7 tests PASS Python 3.14 + pytest baseline 248 passed maintained"
sprint: "6.x AGGRESSIVE"
epic: "Sprint-6-Bloco-Beta-Frontend-Backend-Integration"
owner: "@dev (Neo)"
estimated_effort: "1-2h"
severity_origem: "HIGH (desbloqueia Eric demo real imediato pós-Bloco α CONTAINED)"
created: "2026-05-14"
created_by: "@sm (River)"
predecessor_handoff: "Smith review Bloco α CONTAINED — governance/qa/smith-review-bloco-alpha-pos-execution-2026-05-14.md"
related_adrs:
  - "ADR-013 MVP-LEAN Strategy Deployment Path (deployment-mode local-first)"
  - "ADR-017 Multi-Tenant RLS preservado em /classic flow"
related_stories:
  - "TD-SP06-SPA-CONNECT-01 (sucessor — substitui /classic eventualmente quando SPA integrar pipeline)"
  - "MVP-LEAN-01 (precedent — Jinja2 templates s1-s7 originais)"
related_findings:
  - "Smith probe Bloco α VIABLE-AS-IS confirmou templates Jinja2 íntegros + assets OrSheva 7 self-hosted + backend rotas funcionais"
  - "Smith Fase 7-A F-D1-03 CRITICAL diagnóstico: SPA não chama /revisar, /pipeline-stream, EventSource, FormData"
unblocks:
  - "Eric demo real imediato com PDF financiamento via templates Jinja2 (sem aguardar SPA integration TD-SP06-SPA-CONNECT-01)"
  - "Validação manual UI Jinja2 + SSE resilient flow antes refactor SPA"
tags:
  - project/revisor-contratual
  - story
  - sprint-6
  - bloco-beta
  - rota-classic
  - jinja2-bypass
  - draft
---

# Story TD-SP06-CLASSIC-01 — Rota GET /classic Jinja2 Bypass

## Story

**Como** advogado revisor (DEVEDOR final user) testando o Revisor Contratual SaaS,
**Eu quero** uma rota dedicada `/classic` que sirva os templates Jinja2 legacy funcionais (já integrados ao backend real),
**Para que** eu possa testar o pipeline real (parser+cálculo+BACEN+vault+personas LLM+juiz) imediatamente em ambiente local, bypassando o SPA OrSheva 7 que ainda é wireframe mock (será integrado em TD-SP06-SPA-CONNECT-01 paralelo).

---

## Contexto

**Trigger:** Smith review Fase 7-A (2026-05-14) diagnosticou SPA `index.html` como 100% mock client-side (linhas 1831-2110 ANALYSIS ENGINE + RESULT GENERATION + buildPdf JS). Backend pipeline `revisar_contrato` existe completo e funciona — Smith Bloco α confirmou empíricamente (audit HMAC entry SUCCESS, Ollama POST /api/chat 1m36s real LLM inference, Juiz APROVADO_100). Templates Jinja2 legacy estão **íntegros + integrados ao backend real** (Smith probe VIABLE-AS-IS):

- `s1_login.html` → POST /login htmx
- `s2_pre_upload.html` → form action="/revisar" multipart upload
- `s5_processing.html` → SSE resilient via /revisar/stream/{job_id}
- `s6_resultado.html` → veredito + deliverables D1/D2/D3
- `s7_error.html` → C6 variants
- `base.html` → tokens.css OrSheva 7 + topbar + footer + banner Tema 1378

**Gap único:** rota `GET /login` foi removida em commit cb7c04e (UX-LOGIN-UNIFIED) — quando `GET /` passou a servir exclusivamente o SPA. Apenas `POST /login` permanece.

**Solução cirúrgica:** adicionar `GET /classic` (não restaurar `GET /login` para não quebrar SPA Sprint 5+ Bloco 3 entregue) que renderiza `s1_login.html` (sem auth) ou `s2_pre_upload.html` (com auth).

---

## Acceptance Criteria

1. **AC-01:** Nova rota `GET /classic` em `bloco_interface/web/app.py` que:
   - Se não autenticado (sem session cookie) → renderiza `templates/s1_login.html` com CSRF token + tema_1378 context + session_user=None
   - Se autenticado → renderiza `templates/s2_pre_upload.html` com session_user populated + _layout_context completo

2. **AC-02:** Helpers de contexto (`_layout_context`, geração CSRF) reusam infraestrutura existente em `app.py` sem duplicação — Neo verifica signatures atuais pós-commit cb7c04e antes de chamar.

3. **AC-03:** SPA continua intacto em `GET /` — rota `/classic` é **additive only**. Sprint 5+ Bloco 3 wireframe Imobiliário (TD-SP04-S4-V1 shipped) NÃO sofre regressão.

4. **AC-04:** Form `POST /login` aceita dual content-type:
   - Form-encoded (template Jinja2 flow) → 303 redirect to `/classic` em sucesso
   - JSON (SPA flow atual) → preserva response JSON `{success, user, csrf_token}` existente
   - Distinção via `Content-Type` header request OR campo hidden `__redirect_target`

5. **AC-05:** Empirical smoke (Operator pós-implementação):
   - `curl -I http://127.0.0.1:8501/classic` retorna 200 + content-type text/html
   - HTML response contém `<form action="/login"` (Jinja2 s1_login, não SPA)
   - Login admin/admin via form POST → 303 redirect → GET /classic → renderiza s2_pre_upload.html

6. **AC-06:** CSP headers atuais preservados (`'unsafe-inline'` script-src + style-src adicionados commit 40e8548 F-LOGIN-BROKEN-06) — htmx + htmx-sse.js + sse_resilient.js executam inline OK.

7. **AC-07:** Pytest regressão: 248 passed mantido (zero regressão Sprint 5+ tests).

---

## Tasks / Subtasks

- [x] Task 1: Auditar helpers existentes
  - [x] 1.1 Read `bloco_interface/web/app.py` linhas 367-487 (_layout_context, http_exception_handler, global_exception_handler)
  - [x] 1.2 Identificar helper CSRF (atual `/api/csrf-token` linha 538) e como gerar CSRF para Jinja2 — `auth.generate_csrf_token()` reusado
  - [x] 1.3 Verificar `templates.TemplateResponse` signature pós-cb7c04e — context dict format OK
- [x] Task 2: Implementar rota `GET /classic`
  - [x] 2.1 Adicionar endpoint após linha 510 (entre `GET /` SPA e `GET /api/me`)
  - [x] 2.2 Branch auth: `request.session.get("user")` → s2 OR s1
  - [x] 2.3 Context dict: session_user, csrf_token, tema_1378 (state existente), _layout_context
  - [x] 2.4 Cache-Control header: `no-cache, no-store, must-revalidate` (consistente com `GET /` linha 503)
- [x] Task 3: Adaptar `POST /login` dual-content-type
  - [x] 3.1 Detectar Content-Type header — já existia linha 558 `is_json` flag
  - [x] 3.2 Modificar legacy htmx response `HX-Redirect "/" → "/classic"` (linha 602)
  - [x] 3.3 Preservar httpOnly session cookie em ambos paths (SessionMiddleware preserva automaticamente)
  - [x] 3.4 Atualizar POST /logout `HX-Redirect "/login" → "/classic"` (linha 629) — /login inexistente desde cb7c04e
- [x] Task 4: Testes
  - [x] 4.1 Unit test `tests/unit/test_classic_route.py` — 7 testes (AC-01 dual-state + AC-03 SPA preserved + AC-04 dual-content-type + AC-06 cache-control + logout)
  - [x] 4.2 Regression: pytest baseline 248 passed maintained (Python 3.13); 7/7 tests classic PASS (Python 3.14)
- [x] Task 5: Update File List + Change Log na story
- [x] Task 6: Self-critique checklist applied
- [x] Task 7: Handoff Neo → Operator para empirical smoke AC-05 via curl

---

## Dev Notes (Technical Context)

**Backend pipeline real EXISTS e funciona** (Smith Bloco α CONTAINED 2026-05-14 empirically validated):

| Rota | Status | Linha app.py |
|------|--------|--------------|
| `POST /revisar` | ✅ Funcional | 650 |
| `GET /revisar/stream/{job_id}` | ✅ Funcional | 771 |
| `POST /revisar/d3` | ✅ Funcional | 1113 |
| `GET /verdict` | ✅ Funcional | 1065 |
| `GET /ollama-status` | ✅ Funcional | 1148 |

**Templates Jinja2 EXISTS íntegros** (Smith probe VIABLE-AS-IS):

| Template | Confirmado funcional |
|----------|---------------------|
| `s1_login.html` | htmx form POST /login + CSRF + autofocus |
| `s2_pre_upload.html` | form action="/revisar" + UF/data inputs + upload.js |
| `s5_processing.html` | sse_resilient.js + processing_pane macro |
| `s6_resultado.html` | resultado_pane + clipboard hash + S6.b D3 |
| `base.html` | tokens.css OrSheva 7 + topbar + footer + Tema 1378 banner |

**Static assets EXISTS** (Smith probe):
- `tokens.css` (4.0K) OrSheva 7 design tokens
- `app.css` (27.4K) components + responsive
- `htmx.min.js` (49.7K) self-hosted
- `htmx-sse.js` (8.7K) SSE extension
- `sse_resilient.js` (6.8K) heartbeat + reconnect
- `upload.js` (4.0K) drop zone handler
- `fonts/` self-hosted Lora + Outfit (REV-INT-02 LGPD §46)

**Risk inputs** (Neo verifica no momento do edit):
- Helpers `_layout_context` podem ter mudado signature pós-cb7c04e UX-LOGIN-UNIFIED
- CSP atual permite `'unsafe-inline'` script-src (commit 40e8548 F-LOGIN-BROKEN-06) — htmx inline OK
- Static_version automático via `_compute_static_version` linha 401 (sem manual bump)

**TDs pré-existentes relevantes** (não bloqueadores Sprint 6 Bloco β):
- TD-SP06-MARKER-DEFERRED (Marker OCR install falha Python 3.14) — fixtures sintéticos `data/test-fixtures/synthetic/` substituem
- TD-SP06-CLI-DISPLAY-UTF8-WIN-CP1252 (CLI display, não afeta web)

---

## Testing

**Empirical smoke (Operator pós-implementação Neo):**

```bash
# Smoke 1: GET /classic sem session
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8501/classic
# Esperado: 200

# Smoke 2: HTML response contém Jinja2 (não SPA)
curl -s http://127.0.0.1:8501/classic | grep -c 'action="/login"'
# Esperado: 1

# Smoke 3: Login form-encoded → redirect /classic
curl -s -c /tmp/cookies.txt -b /tmp/cookies.txt -X POST \
  -d "username=admin&password=admin&csrf_token=$(curl -s http://127.0.0.1:8501/api/csrf-token | jq -r .csrf_token)" \
  http://127.0.0.1:8501/login -i | grep -E "303|Location"
# Esperado: 303 + Location: /classic

# Smoke 4: GET /classic com session → s2_pre_upload
curl -s -b /tmp/cookies.txt http://127.0.0.1:8501/classic | grep -c 'enctype="multipart/form-data"'
# Esperado: 1

# Smoke 5: Pipeline real via Jinja2 flow (full e2e)
# Eric upload contrato_veiculo_synthetic.pdf via form → ver SSE phases → veredito APROVADO_100
```

**Pytest regressão obrigatória:**

```bash
python -m pytest tests/unit/ -o addopts="" --tb=line -q \
  --ignore=tests/unit/test_jwt.py --ignore=tests/unit/test_jwt_middleware.py \
  --ignore=tests/unit/test_onboarding_state_machine.py --ignore=tests/unit/test_tos_hash.py \
  --ignore=tests/unit/test_dpa_hash.py --ignore=tests/unit/test_byok_state_machine.py \
  --ignore=tests/unit/test_byok_encryption.py --ignore=tests/unit/test_audit_isolation_aggregation.py \
  --ignore=tests/unit/test_analytics.py --ignore=tests/unit/test_cli.py \
  --ignore=tests/unit/test_imobiliario.py --ignore=tests/integration
# Esperado: 248 passed, 2 failures pré-existentes (não introduzidos)
```

---

## Dev Agent Record

**Agent Model Used:** Claude Opus 4.7 (via Skill LMAS:agents:dev)

**Debug Log References:** Pytest baseline pré + pós edits idêntico (248 passed + 2 failures pré-existentes). 7/7 unit tests classic_route PASS Python 3.14. Edits cirúrgicos confirmados via Read após cada Edit (state Hash idempotent).

**Completion Notes List:**

- POST /login JÁ era dual-content-type (linha 558 `is_json` flag) — apenas legacy htmx flow precisou `HX-Redirect "/" → "/classic"` (1 line change linha 602)
- POST /logout `HX-Redirect "/login"` (rota inexistente desde cb7c04e UX-LOGIN-UNIFIED) → "/classic" (1 line change linha 629)
- GET /classic novo endpoint usa `_layout_context()` existente (linha 101) + `auth.generate_csrf_token()` (Tank pattern /api/csrf-token linha 538-543)
- Unit test usa monkeypatch `auth.authenticate` (env var ADMIN_PASSWORD_HASH ausente no test runner — TD-SP06-PYTEST-DEPS-PYTHON-3-14)
- TD-SP06-PYTEST-DEPS-PYTHON-3-14 confirmado pre-existing — test runner Python 3.13 não tem sqlalchemy → testes auth-dependent precisam Python 3.14
- ACs todos atendidos empíricamente via TestClient(app)

**File List:**

- `bloco_interface/web/app.py` (MODIFIED — 3 edits cirúrgicos):
  - Lines 510-543: NEW endpoint `GET /classic` (43 lines, dual-state Jinja2 render)
  - Line 602: MODIFIED `HX-Redirect "/" → "/classic"` (POST /login legacy htmx flow)
  - Line 629: MODIFIED `HX-Redirect "/login" → "/classic"` (POST /logout)
- `tests/unit/test_classic_route.py` (NEW — 145 lines, 7 tests, monkeypatch fixture)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-05-14 | @sm (River) | Draft inicial Bloco β Sprint 6 AGGRESSIVE pós-Smith CONTAINED Bloco α |
| 2026-05-14 | @po (Keymaker) | Validation 10/10 score → status Draft → Ready |
| 2026-05-14 | @dev (Neo) | Implementação completa: GET /classic + POST /login dual-content-type + POST /logout redirect + 7 unit tests PASS Python 3.14 + pytest baseline 248 mantido. Status Ready → Ready for Review. |
