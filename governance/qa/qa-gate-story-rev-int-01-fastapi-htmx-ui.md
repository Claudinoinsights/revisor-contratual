---
type: qa-gate
story_id: REV-INT-01
story_title: "Frontend FastAPI + HTMX + Jinja2 (substituir Streamlit)"
gate_decision: CONCERNS
reviewer: "@qa (Oracle)"
review_date: "2026-05-05"
session: 85
spec_document: governance/design-spec-fastapi-htmx-ui.md
implementation_handoff: .lmas/handoffs/handoff-dev-to-qa-2026-05-05-revint01-qa-gate.yaml
tags:
  - project/revisor-contratual
  - qa-gate
  - sprint-02
  - rev-int-01
---

# QA Gate — Story REV-INT-01

## Verdict: **CONCERNS** ⚠️

**Resumo:** Implementação cumpre 100% dos acceptance criteria do spec Sati. Suite testes verde (232 passed, 1 skipped). Smoke probes confirmam funcionalidade end-to-end. Porém, foram identificadas **8 findings** (1 HIGH + 3 MEDIUM + 4 LOW) que devem ser endereçadas — algumas são out-of-scope desta story (acceptable como tech debt rastreável), uma é violação do princípio LGPD on-premise do PRD que merece atenção antes de qualquer release público.

---

## Acceptance Criteria — Auditoria

### Funcionalidade (7/7 PASS)

| AC | Status | Evidência |
|----|--------|-----------|
| GET / retorna HTML idle + sidebar 3 mock items | ✅ PASS | curl: HTTP 200, 2488b; grep confirma 3 .hist-item |
| POST /revisar (multipart pdf+uf+data+tier) → processing.html | ✅ PASS | curl multipart: HTTP 200, 2353b |
| GET /pipeline-stream emite 7 SSE events em ~3s | ✅ PASS | timeout 4s curl: 7 events + done sentinel |
| HTMX swap workspace ao receber done:true | ✅ PASS | JS handler em processing.html linha 25-28 |
| GET /verdict retorna mock APROVADO_HITL 78% | ✅ PASS | curl: HTTP 200, 938b com 3 critérios |
| POST /reset volta para idle.html | ✅ PASS | curl: HTTP 200, 804b |
| Static files /static/* servidos | ✅ PASS | tokens.css 1288b, app.css 9493b, htmx 50KB, sse 9KB |

### Visual (5/5 PASS — verificação code-level; smoke browser pendente Eric)

| AC | Status | Evidência |
|----|--------|-----------|
| 1 viewport sem scroll em 1080p (idle) | ✅ PASS | container max-width 720px + sidebar 240px caben em 1080p |
| Cores Orsheva #EE6B20 em mark/btn/accent | ✅ PASS | tokens.css linha 11: `--or-500: #EE6B20` |
| Manrope corpo + Fraunces APENAS verdict | ✅ PASS | app.css: body usa --f-ui (Manrope); .verdict-status/.verdict-num/.criterio-score usam --f-display |
| Zero texto explicativo | ✅ PASS | templates auditados — só labels de ação ("PDF do contrato", "Revisar contrato →", "Nova revisão") |
| Sidebar 3 items + badges veredito | ✅ PASS | grep confirma 3 .hist-item; CSS .badge.{aprovado-100,hitl,rejeitado} |

### Quality (3/3 PASS)

| AC | Status | Evidência |
|----|--------|-----------|
| Sem deps JS externas além HTMX local | ✅ PASS | base.html: apenas /static/htmx.min.js + /static/htmx-sse.js |
| tokens.css (vars) + app.css (classes) separados | ✅ PASS | 2 arquivos distintos |
| Suite 232/1 não quebra | ✅ PASS | pytest --no-cov: 232 passed, 1 skipped (61.86s) |

### Cleanup (3/3 PASS)

| AC | Status | Evidência |
|----|--------|-----------|
| streamlit_app.py removido | ✅ PASS | ls bloco_interface/ confirma ausência |
| streamlit_tokens.css removido | ✅ PASS | ls bloco_interface/ confirma ausência |
| streamlit deps removidas | ✅ PASS | grep streamlit pyproject.toml: 0 matches |

### Deploy (4/4 PASS)

| AC | Status | Evidência |
|----|--------|-----------|
| uvicorn :8501 sobe sem erro | ✅ PASS | startup log: "Application startup complete" |
| HTTP 200 em / e assets | ✅ PASS | smoke test 7 endpoints |
| HTMX presente em network tab | ✅ PASS | base.html linha 12-13 |
| Form submit end-to-end funciona | ✅ PASS | curl multipart → processing.html partial |

**Total: 22/22 AC PASS (100%).**

---

## Adversarial Probes — 6 categorias

### Probe 1 — XSS via filename ✅ DEFENDIDO

**Vetor:** Upload PDF com filename `<script>alert(1)</script>.pdf`

**Resultado:**
```
<div class="processing-head">Analisando <code>&lt;script&gt;alert(1)&lt;/script&gt;.pdf</code></div>
```

**Análise:** Jinja2 autoescape (default em FastAPI Jinja2Templates) converte caracteres HTML especiais. Filename é renderizado como texto literal, sem execução de script.

### Probe 2 — Path traversal /static ✅ DEFENDIDO

**Vetores testados:**
- `GET /static/../app.py` → HTTP 404
- `GET /static/..%2Fapp.py` (URL-encoded) → HTTP 404
- `GET /static/../../../../../etc/passwd` → HTTP 404

**Análise:** Starlette `StaticFiles` sanitiza path normalization. Source code Python e arquivos do sistema não são acessíveis via /static/.

### Probe 3 — Multipart edge cases ⚠️ FINDINGS

| Cenário | HTTP | Observação |
|---------|------|------------|
| Sem field `pdf` | 422 | ✅ FastAPI valida required UploadFile |
| PDF vazio (0 bytes) | 200 | ⚠️ aceito (mock OK; pipeline real precisa validar) |
| Não-PDF (HTML upload) | 200 | ⚠️ aceito (sem magic bytes / content-type validation) |
| Tier inválido (`DROP_TABLES`) | 200 | ⚠️ aceito (sem enum validation) |

**Análise:** Para mock UI atual estes são MEDIUM/LOW. Para Sprint 02 STORY UI-1 (pipeline real), são MUST FIX.

### Probe 4 — SSE robustness ⚠️ FINDING

**Vetores:**
- Disconnect mid-stream (timeout 1s) → SSE não vaza recursos no servidor (verificado no log)
- `GET /pipeline-stream` direto sem prévio `POST /revisar` → emite 7 events normalmente

**Análise:** SSE não tem session binding. Cliente pode bypassar /revisar e ir direto para /pipeline-stream → /verdict. Aceitável para mock, mas inadequado quando pipeline real for conectado em STORY UI-1.

### Probe 5 — LGPD CDN leakage 🔴 HIGH FINDING

**Vetor:** `curl -s http://127.0.0.1:8501/ | grep -oE 'https?://[^"]+' | sort -u`

**Resultado:**
```
https://fonts.googleapis.com
https://fonts.gstatic.com
```

**Análise:** **Violação do princípio "100% on-premise LGPD"** declarado no PRD e na landing/index.html linha 7-8 ("PDFs e dados do contrato nunca saem da máquina"). Embora dados de contrato realmente não saiam, **o IP do operador é exposto a Google a cada page load** via Google Fonts CDN. Isso pode ser visto como inconsistência reputacional para um produto que vende "100% local" como diferencial.

**Mitigação recomendada (BAIXO esforço):**
- **Opção A (preferida):** Self-host fontes em `bloco_interface/web/static/fonts/` (download Manrope + Fraunces + JetBrains Mono via google-webfonts-helper). +200KB no bundle, zero CDN.
- **Opção B:** Fallback para fontes do sistema (`system-ui, sans-serif` + `Georgia, serif` + `ui-monospace`) — preserva LGPD com 0 KB extra mas sacrifica identidade visual Orsheva.

**Severidade:** HIGH para release público (`v0.2.0` ou release marketing). Aceitável como CONCERNS para esta iteração interna de mock UI desde que registrado em TECH-DEBT.md com remediation_date.

### Probe 6 — Static analysis (ruff) ⚠️ LOW FINDING

```
UP037 [*] Remove quotes from type annotation
   --> bloco_interface\web\app.py:119:36
async def event_generator() -> "asyncio.AsyncIterator[str]":
```

**Análise:** Type hint quoted desnecessariamente (Python 3.9+ não exige forward reference para builtins). Trivial — auto-fixable com `ruff --fix`.

---

## Findings Summary

| ID | Severity | Description | Acceptance | Action |
|----|----------|-------------|------------|--------|
| **F-LGPD-01** | 🔴 **HIGH** | Google Fonts CDN leak de IP do operador | Não-bloqueante p/ mock; bloqueante p/ release público | TECH-DEBT registrar; remediation antes de v0.2.0 |
| **F-VAL-01** | 🟡 MEDIUM | Sem validação magic bytes / content-type em /revisar | Aceitável p/ mock; bloqueante p/ STORY UI-1 | TECH-DEBT registrar |
| **F-LEAK-01** | 🟡 MEDIUM | Event listener leak em processing.html (cada swap adiciona listener) | Funcional para 1-2 ciclos; cumulative depois | TECH-DEBT registrar; fix simples (use `htmx.config` ou register no `htmx:load`) |
| **F-NFR-01** | 🟡 MEDIUM | Sem upload size limit (DoS vector) | Aceitável on-premise solo; risco se exposto a rede | TECH-DEBT registrar |
| **F-SSE-01** | 🟢 LOW | /pipeline-stream sem session binding | Aceitável p/ mock; obrigatório STORY UI-1 | TECH-DEBT registrar |
| **F-VAL-02** | 🟢 LOW | Tier sem enum validation (Form aceita string livre) | Aceitável p/ mock | TECH-DEBT registrar |
| **F-RUF-01** | 🟢 LOW | Type hint quoted (ruff UP037) | Trivial cosmetic | Fix imediato (1 linha) ou batch posterior |
| **F-CSP-01** | 🟢 LOW | Inline `<script>` em processing.html | Aceitável; CSP estrito requer movê-lo | Tech debt informacional |

**Total:** 1 HIGH + 3 MEDIUM + 4 LOW = 8 findings. Zero CRITICAL.

---

## Decisão de Gate: CONCERNS

**Justificativa:**

- ✅ **22/22 acceptance criteria PASS** — funcionalidade, visual, quality, cleanup e deploy todos satisfeitos
- ✅ **Zero CRITICAL findings** — não há bloqueio absoluto
- ⚠️ **1 HIGH (F-LGPD-01)** — viola princípio nuclear do PRD, mas é mitigável em <30min e fora do escopo desta story (LGPD CDN era debt pré-existente também na Streamlit UI)
- ⚠️ **3 MEDIUM** — aceitáveis para mock UI; obrigatórios antes de pipeline real (STORY UI-1)
- ✅ **Spec section 11 (out-of-scope)** explicita que esta story é mock — pipeline real fica para STORY UI-1

**CONCERNS** comunica: "implementação aprovada, mas com débitos rastreáveis que devem ser endereçados antes de release público ou conexão com pipeline real".

---

## Action Items (delegados via tech debt)

1. **F-LGPD-01 (HIGH)** — Owner: @dev | Remediation by: antes de v0.2.0 release | Self-host Google Fonts em /static/fonts/
2. **F-VAL-01 (MEDIUM)** — Owner: @dev | Remediation by: STORY UI-1 (Sprint 02) | Magic bytes + content-type validation em /revisar
3. **F-LEAK-01 (MEDIUM)** — Owner: @dev | Remediation by: STORY UI-1 | Mover listener para `htmx:load` event uma vez ou usar HTMX native sse-swap
4. **F-NFR-01 (MEDIUM)** — Owner: @dev | Remediation by: STORY UI-1 | Adicionar `max_size` em UploadFile via Starlette `MAX_BODY_SIZE`
5. **F-SSE-01 (LOW)** — Owner: @dev | Remediation by: STORY UI-1 | Bind /pipeline-stream a session/job_id retornado por /revisar
6. **F-VAL-02 (LOW)** — Owner: @dev | Remediation by: STORY UI-1 | Substituir `tier: str = Form(...)` por Pydantic Enum
7. **F-RUF-01 (LOW)** — Owner: @dev | Remediation by: imediato | `ruff check --fix bloco_interface/web/app.py`
8. **F-CSP-01 (LOW)** — Owner: @dev | Remediation by: opcional | Mover inline script para arquivo externo

---

## Próximo passo

1. ✅ **Gate decision: CONCERNS** — Story REV-INT-01 PASSA com débitos rastreados
2. ⚠️ **Smoke browser test pendente do Eric** — Oracle revisou via curl/code; Eric deve abrir `revisor-web` no browser para validar UX visual final
3. **Handoff Operator (@devops)** para commit + git push + PR — registrar findings como TECH-DEBT antes do commit
4. **TECH-DEBT.md update** — registrar 8 findings com IDs TD-{N}

— Oracle, guardião da qualidade 🛡️
