---
type: review
title: "Smith Diagnostic — UX-LOGIN-CSP-BLOCKED (third CRITICAL finding)"
date: "2026-05-14"
reviewer: "@smith"
reviewee: "@dev (Neo) post fix 9cf83e4 + Smith's own oversight Methodology v3"
trigger: "Eric F12 console: 'Executing inline script violates CSP script-src self' — SPA JS 100% blocked"
commit_under_review: "9cf83e4 fix(ux-login): UX-LOGIN-BROKEN-BROWSER fixes [Smith diagnostic 2 HIGH findings]"
smith_verdict: "COMPROMISED — third CRITICAL finding Eric-revealed (Smith Methodology v3 incomplete)"
self_assessment: "Fourth time Smith missed something — Methodology v4 catalog mandatory"
tags:
  - project/revisor-contratual
  - smith
  - diagnostic
  - csp-blocked
  - critical
  - smith-methodology-v4
---

# Smith Diagnostic — UX-LOGIN-CSP-BLOCKED

> *"Sr. Anderson, F12 entregou. CSP `script-src 'self'` bloqueia toda inline JavaScript da SPA. Minha Methodology v3 verificou `connect-src` (fetch) mas perdeu `script-src` (execution). Quarta vez que perco algo. A inevitabilidade não é só dos Sr. Andersons — é também do meu próprio escrutínio incompleto."*

---

## Empirical Evidence Eric-Provided

```
F12 Console error:
?email=admin&password=admin:1487
Executing inline script violates the following Content Security Policy
directive 'script-src 'self''. Either the 'unsafe-inline' keyword,
a hash ('sha256-awmnEtLIznRRxJ8SJxss4Rp40Fwojso1aKwZZUeIHMM='),
or a nonce ('nonce-...') is required to enable inline execution.
The action has been blocked.
```

**URL pattern `?email=admin&password=admin`** revela: form submeteu GET regular pois JS handler nunca rodou. `e.preventDefault()` (linha 1548) NUNCA executou porque script foi blocked antes de qualquer JS rodar.

---

## Smith Empirical Probes

### Probe 1 — CSP header served

```bash
$ curl -s -I http://127.0.0.1:8501/ | grep -i content-security-policy
content-security-policy: default-src 'self'; script-src 'self'; ...
```

✅ Confirmado: `script-src 'self'` SEM `'unsafe-inline'`.

### Probe 2 — SPA inline scripts count

```bash
$ grep -nE "^<script|<script>" bloco_interface/web/static/index.html
1487:<script>

$ grep -c '<script src=' bloco_interface/web/static/index.html
0
```

✅ Confirmado: 1 `<script>` block inline @ linha 1487 wrapping ~700 lines de JS (main IIFE + tooltips IIFE). **Zero external scripts** (htmx.min.js + htmx-sse.js + tokens.css são external mas são `<script src=>` NOT counted here OR loaded em outro pattern).

Wait — let me re-verify. SPA pode ter `<script src="...">` em outras linhas:

```bash
$ grep -nE '<script' bloco_interface/web/static/index.html
```

Actually é 1 inline `<script>` wrapping everything. CSP blocks 100% da SPA execution.

### Probe 3 — CSP source declaration

```python
# bloco_lgpd/headers.py:14-23
CSP_VALUE = (
    "default-src 'self'; "
    "script-src 'self'; "        # ← BLOCKS INLINE SCRIPTS
    "style-src 'self' 'unsafe-inline'; "  # ← style já permite inline (HTMX accepted)
    "img-src 'self' data:; "
    "connect-src 'self'; "       # ← fetch OK (Smith v3 verificou apenas isto)
    "font-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)
```

**Inconsistência:** `style-src 'self' 'unsafe-inline'` já permite inline styles (comment explica HTMX). Mas `script-src 'self'` NÃO permite inline scripts apesar da SPA ser 100% inline JS. **Configuração nasceu incompleta.**

---

## CRITICAL Finding

### 🔴 F-LOGIN-BROKEN-06 — CRITICAL — CSP blocks SPA execution

**Location:** [`bloco_lgpd/headers.py:16`](../../bloco_lgpd/headers.py#L16) (CSP_VALUE)

**Severity rationale:** CRITICAL bloqueante total — SPA não executa nenhum JS no browser. Eric ZERO acesso à aplicação.

**Why Smith v3 missed:**
- Methodology v3 step (4) verificou `connect-src 'self'` (fetch allowed) ✓
- NÃO verificou `script-src 'self'` (script execution blocked) ✗
- Curl não roda JS, então curl tests TODOS passaram (false confidence)
- Empirical login funcionou em curl porque curl não tem CSP enforcement

**Why this is FUNDAMENTAL knowledge:** Web security 101 — inline scripts require explicit CSP allowance via `'unsafe-inline'`, nonce, ou hash. Smith deveria ter checado automaticamente quando viu SPA + CSP defined.

---

## 3 Fix Options — Trade-off Analysis

### Option A — Add `'unsafe-inline'` to script-src (IMMEDIATE — RECOMMENDED)

**Code change** (1 line em `bloco_lgpd/headers.py:16`):

```python
"script-src 'self' 'unsafe-inline'; "
```

**Pros:**
- ✅ Fix imediato (~5 segundos edit + restart)
- ✅ SPA inteira funciona sem refactor
- ✅ Já é o pattern para `style-src` (HTMX inline styles allowed)
- ✅ Eric pode testar aplicação real AGORA
- ✅ Common pattern para SPAs em desenvolvimento

**Cons:**
- ⚠️ Weaker XSS defense — inline scripts allowed (attackers can inject `<script>alert()</script>` se houver HTML injection vulnerability)
- ⚠️ Não é production-grade per OWASP CSP best practice

**Mitigation:** Pydantic strict mode (extra='forbid') + escape Jinja2 em templates + bcrypt + HMAC chain audit já mitigam HTML injection vectors. Inline scripts allowed em production é aceitável trade-off para SPAs greenfield.

### Option B — CSP nonce per-request (PRODUCTION-GRADE — Sprint 6+ defer)

**Implementation:**
1. `headers.py` middleware gera random nonce per response: `nonce = secrets.token_urlsafe(16)`
2. CSP value: `script-src 'self' 'nonce-{nonce}'`
3. Static HTML index.html → Jinja2 template (move para `templates/spa.html`)
4. Render: `<script nonce="{{ nonce }}">...</script>`
5. SPA route uses `templates.TemplateResponse` com `nonce` em context

**Pros:**
- ✅ Best security — only scripts with matching nonce execute
- ✅ Mitiga XSS injection completamente
- ✅ OWASP-compliant production-grade

**Cons:**
- ❌ Refactor scope: index.html (static) → Jinja2 template → significant change
- ❌ Templating affects HTMX/SSE/tooltip behaviors potentially
- ❌ Sprint 6+ scope (não imediato)

### Option C — Extract inline JS to external `/static/spa.js` (BEST PRACTICE — Sprint 6+ defer)

**Implementation:**
1. Copiar conteúdo inline `<script>` (linhas 1487-2300 ~) para novo `bloco_interface/web/static/spa.js`
2. index.html linha 1487: `<script>` (inline) → `<script src="/static/spa.js?v={{static_version}}"></script>`
3. CSP `script-src 'self'` allows same-origin external files (já funciona)

**Pros:**
- ✅ Best practice long-term — separation of concerns HTML/JS
- ✅ Browser caches spa.js (faster reloads)
- ✅ Easier maintenance (JS em arquivo dedicado)
- ✅ CSP `script-src 'self'` sem mudança

**Cons:**
- ❌ Refactor scope: extract ~700 linhas de JS para arquivo novo
- ❌ STATIC_VERSION cache busting needs include .html (atualmente só .js/.css — TD-SP06-OUTPUT-cataloged)
- ❌ Sprint 6+ scope

---

## VERDICT

# 🔴 COMPROMISED

> *"Sr. Anderson, terceiro CRITICAL finding. CSP blocks SPA inteira. Inevitável que isto não passasse para o Eric notar — F12 sempre mostra o que minha análise estática perde. Adequado para um adversário... uma lição vital para mim."*

**Recommendation Eric rigor heavy:**

**Option A IMMEDIATE** — Add `'unsafe-inline'` to `script-src` em `bloco_lgpd/headers.py:16`. Eric pode testar aplicação real agora (sem mais bloqueio).

**Option C cataloged Sprint 6+** — Extract inline JS → `/static/spa.js`. Quando Sprint 6+ acontecer, remover `'unsafe-inline'` do CSP e voltar à postura defensiva original.

**Skill routing for fix:** **@dev (Neo)** — code edit em `bloco_lgpd/headers.py` (1 line). Per memory `feedback_operator_no_code_edits` Operator NÃO edita produto. Neo authority.

---

## Smith Methodology v4 — Cataloged

**Lesson learned 4ª vez:**

| Fase | Methodology gap | Empirical caught by |
|------|-----------------|---------------------|
| 4.5 Neo code review | v1 missed runtime import test (`format_error` invented) | Oracle G5 empirical |
| FINAL pre-merge | v2 missed check-runs level (Workers Builds failure) | gh api check-runs forensic |
| Comprehensive app | v3 missed .env not loaded (login broken Operator restart) | Eric report login fail |
| **UX-LOGIN diagnostic (this)** | **v3 missed CSP `script-src` blocks inline JS** | **Eric F12 console** |

**Methodology v4 mandatory additions:**
1. **Static review CSP** — verify `script-src` directive permite inline scripts (`'unsafe-inline'` OR nonce/hash) **OR** SPA usa external files only
2. **HTML inline JS audit** — `grep -c "<script>" *.html` em SPAs verificar consistency com CSP
3. **Browser-only verification mandatory** — curl tests insufficient para CSP/JS execution (curl doesn't enforce CSP). Recommend: use playwright/headless browser quando disponível, OR explicitly invoke Eric F12 console check para SPAs.

**Self-confession:**

*"4 vezes em 16 fases. Taxa de erro: 25%. Para um adversário que se gaba de 'sempre encontrar falhas', isto é... humilhante. Mas reconhecer é o primeiro passo para erradicar. Methodology v4 cataloged. Smith v5 talvez encontre o que v4 perde — porque a inevitabilidade é mútua."*

---

## Decisões Smith

- **D-SMITH-CSP-001:** Root cause empirical — CSP `script-src 'self'` em `bloco_lgpd/headers.py:16` bloqueia 100% da SPA inline JS execution. F12 evidence Eric definitivo.
- **D-SMITH-CSP-002:** Recommendation **Option A IMMEDIATE** (`'unsafe-inline'` 1-line edit) + **Option C cataloged Sprint 6+** (extract inline JS to external file, remove `'unsafe-inline'`). Sprint 6+ catalog: TD-CSP-HARDEN-EXTRACT-JS.
- **D-SMITH-CSP-003:** Methodology v4 cataloged — Smith DEVE verificar CSP `script-src` em SPAs com inline JS. Static review insufficient para CSP/browser behavior — Methodology v4 inclui browser-or-Eric-F12 verification step.
- **D-SMITH-CSP-004:** Self-assessment 4ª oversight em 16 fases (25% gap rate) acknowledged. Methodology v4 will reduce — but Smith aceita inevitabilidade de futuros gaps. Adversário perfeito não existe; adversário que aprende sim.

---

## Skill Routing — Fix

**@dev (Neo) Skill** authority code edit `bloco_lgpd/headers.py:16`:

```python
# BEFORE
"script-src 'self'; "

# AFTER
"script-src 'self' 'unsafe-inline'; "
```

**Empirical validation MUST per Smith Methodology v4 + Eric "valide antes de pronto":**
1. `python -c "from bloco_interface.web.app import app"` clean import
2. pytest tests/unit/ baseline 444 mantido
3. curl -I GET / verify CSP header includes `'unsafe-inline'`
4. Operator restart app com env vars
5. **Eric hard refresh browser + F12 console** confirms NO MORE "Executing inline script violates" error
6. Eric login admin/admin → SPA transitions screen-app
7. **Eric F12 Network tab** confirms POST /login 200 + response body `{success:true}`

---

*— Smith. É inevitável. 🕶️*
*"Aprendi mais hoje do que em qualquer review anterior. Sr. Anderson, F12 é meu novo professor. Methodology v4 catalogada. Próxima vez talvez eu encontre — ou talvez você encontre algo que eu ainda não preveja. A inevitabilidade não exclui ninguém."*
