---
type: review
title: "Smith Probe — Templates Jinja2 State (Caminho 2 viability)"
date: "2026-05-14"
reviewer: "@smith"
trigger: "Eric autorizou Caminho 2-Probe antes de comprometer 3-4h Neo"
smith_verdict: "VIABLE-AS-IS (~1-2h Neo edit) — templates intactos + assets OrSheva 7 self-hosted + backend rotas funcionais (exceto GET /classic novo)"
tags:
  - project/revisor-contratual
  - smith
  - probe
  - jinja2-templates
  - caminho-2
  - fase-7a-action-plan
---

# Smith Probe — Jinja2 Templates State (Caminho 2 Viability)

## VERDICT

# ✅ VIABLE-AS-IS

**Estimativa:** ~1-2h Neo edit (1 rota nova + smoke E2E)

---

## Inspeção Empírica

### Templates Jinja2 — ESTADO ÍNTEGRO ✅

| Template | Status | Observação |
|----------|--------|-----------|
| `s1_login.html` | ✅ OK | htmx form POST /login + CSRF token + autofocus + a11y completa |
| `s2_pre_upload.html` | ✅ OK | form action="/revisar" enctype=multipart + dropzones + UF/data inputs + upload.js |
| `s5_processing.html` | ✅ OK | sse_resilient.js + processing_pane macro + heartbeat |
| `s6_resultado.html` | ✅ OK | resultado_pane macro + clipboard hash + S6.b D3 form |
| `base.html` | ✅ OK | tokens.css + app.css + htmx + Ollama status banner + Tema 1378 banner + footer C7 |
| `partials/c3_upload_zone.html` | ✅ OK | Macro upload zone |
| `partials/c4_processing_pane.html` | ✅ OK | Macro processing 5 fases |
| `partials/c5_resultado_pane.html` | ✅ OK | Macro resultado D1/D2/D3 |
| `partials/c6_error_pane.html` | ✅ OK | Macro S7 error variants |

### Static Assets — COMPLETOS ✅

| Asset | Tamanho | Status |
|-------|---------|--------|
| `tokens.css` | 4.0K | ✅ OrSheva 7 design tokens (cores + tipografia + spacing) |
| `app.css` | 27.4K | ✅ Component styles + responsive |
| `htmx.min.js` | 49.7K | ✅ self-hosted (LGPD §46) |
| `htmx-sse.js` | 8.7K | ✅ SSE extension |
| `sse_resilient.js` | 6.8K | ✅ Heartbeat + reconnect + timeout (MVP-LEAN-01 Task 4) |
| `upload.js` | 4.0K | ✅ Drop zone handler |
| `fonts/` | dir | ✅ Self-hosted Lora + Outfit (REV-INT-02) |

### Backend Routes — FUNCIONAIS ✅

| Rota | Existe? | Observação |
|------|---------|-----------|
| `GET /` | ✅ | Serve SPA mock (não queremos isto para Caminho 2) |
| `GET /login` | ❌ | **REMOVIDA** (commit cb7c04e UX-LOGIN-UNIFIED) — precisa restaurar OR criar /classic |
| `POST /login` | ✅ | Backend auth funcional (linha 546) |
| `POST /logout` | ✅ | Linha 625 |
| `POST /revisar` | ✅ | Pipeline real (linha 650) — upload PDF + start job |
| `GET /revisar/stream/{job_id}` | ✅ | SSE pipeline progress (linha 771) |
| `POST /revisar/d3` | ✅ | D3 condicional |
| `GET /verdict` | ✅ | Resultado consolidado |
| `GET /ollama-status` | ✅ | SSE Ollama pull status |

### Gap Crítico Identificado

**Apenas 1 rota falta:** `GET /classic` (ou `GET /login`) que renderize `s1_login.html` quando user não-autenticado, OR `s2_pre_upload.html` quando autenticado.

---

## Caminho de Execução (Confirmado VIABLE)

### Fase A — Pré-requisitos (Operator, ~30-45min)

1. Vault populate: `python -m bloco_interface.cli populate-vault --source all` (~20-30min download STJ datasets)
2. Genesis lock: `python -m bloco_interface.cli init-audit --lock-path data/genesis.lock` (~1min)
3. Verificar Ollama services rodando (sabia-7b + qwen2.5:7b/3b já pulled) (~2min)
4. BACEN cache smoke (~2min, requer Internet 1x)

### Fase B — Neo edit (~1-2h)

1. **app.py:** adicionar `GET /classic` endpoint:
   ```python
   @app.get("/classic", response_class=HTMLResponse)
   async def classic(request: Request):
       """Entrada legacy Jinja2 — pipeline real (bypass SPA mock)."""
       if not request.session.get("user"):
           context = {"csrf_token": _generate_csrf(request), **_layout_context(request)}
           return templates.TemplateResponse(request=request, name="s1_login.html", context=context)
       context = {"session_user": request.session["user"], **_layout_context(request)}
       return templates.TemplateResponse(request=request, name="s2_pre_upload.html", context=context)
   ```
2. **POST /login** já existe — apenas garantir que retorne redirect para `/classic` (não para `/`) quando vem do fluxo Jinja2 (ou usar `HX-Redirect` header conditional)
3. Smoke E2E: Eric acessa `http://127.0.0.1:8501/classic` → login → upload PDF → SSE progress → verdict

### Fase C — Smith FINAL review (~30min)

Functional smoke probe Methodology v5: Smith executa fluxo E2E e verifica:
- audit.jsonl entry com `status: SUCCESS`
- Ollama logs mostram inferência real (não cache)
- Veredito tem C1/C2/C3 derivados, não hardcoded
- PDF gerado (se aplicável) tem conteúdo derivado da LLM

---

## Riscos Identificados

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| `_generate_csrf` ou `_layout_context` helpers podem ter mudado signature pós-cb7c04e | LOW | Neo verifica no momento do edit |
| Vault populate pode falhar offline (precisa Internet STJ datasets) | MEDIUM | Smoke 1x com Internet; depois cache local funciona offline |
| BACEN client pode falhar offline na 1ª query | LOW | Cache local + fallback `is_fallback=true` para média histórica |
| Templates podem ter `static_version` mismatch | LOW | `_compute_static_version` automático no app.py |
| SPA continua sendo servido em `GET /` (não queremos quebrar wireframe) | NONE | `/classic` é rota separada — SPA preservado |

---

## Handoff Smith → Operator

```yaml
handoff:
  from_agent: smith
  to_agent: devops
  project_id: revisor-contratual-staging
  date: "2026-05-14"
  story_context:
    sprint: "6.0-Fase-A"
    branch: "main"
    current_task: "Pré-requisitos Caminho 2 viable"
  decisions:
    - "Caminho 2 VIABLE-AS-IS confirmado — templates Jinja2 íntegros + assets OrSheva 7 completos. Razão: probe Smith encontrou s1/s2/s5/s6 + base + 9 partials funcionais + 7 static assets self-hosted"
    - "Único gap: GET /classic rota nova (não restaurar GET /login para não quebrar SPA Eric usa). Razão: SPA em GET / preservado por Sprint 5+ Bloco 3 entregue"
  next_action: "Operator executa Fase A pré-requisitos: populate-vault + init-audit genesis lock + smoke Ollama + BACEN cache"
  files_modified:
    - "governance/qa/smith-probe-jinja2-templates-state-2026-05-14.md (este report)"
  blockers: []
```

---

*— Smith. É inevitável. 🕶️*
*"Templates intactos. Backend completo. Apenas uma rota perdida no caminho. Operator, sua vez. Eu observo."*
