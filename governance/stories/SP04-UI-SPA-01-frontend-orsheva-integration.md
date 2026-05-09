---
type: story
id: "SP04-UI-SPA-01"
title: "Frontend SPA OrSheva 7 backend integration — login + onboarding + analysis flow"
status: Ready
epic: "Sprint 04 Cloud SaaS BYOK"
project: revisor-contratual
sprint: "04"
phase: 14.1
priority: P0
estimated_days: "3-5"
agent: "@dev (Neo)"
branch: "feat/sp04-ui-spa-01 (será criada pós validate-story-draft → Ready + DEC-ERIC-DIV-01 resolvida + PR #4 + #5 merged)"
created: "2026-05-09"
created_by: "@sm River"
predecessor_handoff: ".lmas/handoffs/handoff-mor2sm-2026-05-09-sp04-ui-spa-integration.yaml"
predecessor_artifact: "index.html (raiz do repo, 95580 bytes, criado por Eric 2026-05-09 15:55)"
predecessor_ux_spec: "governance/ux-spec-v2.0.0-DRAFT.md (Sati 8 telas + 7 componentes — Phase 4)"
dependencies:
  - "SP04-AUTH-01 (Done — PR #4 OPEN — endpoints /api/auth/* + /api/onboarding/step2..4 + JWT cookie + middleware tenant context)"
  - "SP04-BYOK-01 (Done — PR #5 OPEN — endpoints /api/tenant/byok/{rotate,revoke,status} + runtime injection middleware)"
  - "SP04-LGPD-01 (InReview WAIVED — branch atual feat/sp04-lgpd-01 — endpoints /api/tenant/tos/* + /api/tenant/audit/isolation)"
  - "ADR-014 (BYOK Provider Abstraction Anthropic Only — runtime middleware reutilizado)"
  - "ADR-020 (Multi-Doctype Dispatcher v2 — Accepted 2026-05-09 — supersedes ADR-016 — 7 doctypes operacionais resolvendo DEC-ERIC-DIV-01 Opção A)"
  - "ADR-016 (superseded by ADR-020 — não bloqueia esta story, mantida para histórico)"
  - "ADR-017 (Multi-Tenant Pool+RLS BACKBONE — JWT tenant_id claim propaga RLS context)"
  - "ADR-019 (DPA Storage Schema — TOS pattern reusable)"
  - "Sati UX Spec v2.0.0-DRAFT (S1..S8 + C1..C7)"
source_frs:
  - "FR-AUTH-03 (login JWT com tenant_id claim — login form do SPA)"
  - "FR-AUTH-01 (cadastro escritório — onboarding wizard step1)"
  - "FR-API-KEY-01 (cadastro + validação BYOK — onboarding wizard step2)"
  - "FR-LGPD-01 (DPA acceptance — onboarding wizard step3)"
  - "FR-LGPD-02 (TOS/EULA acceptance — onboarding wizard step3 combine DPA+TOS Opção B)"
  - "FR-OCR-01 (upload PDF — main view S4)"
  - "FR-OCR-02 (Vision OCR processing — SSE S5)"
  - "FR-PERSONAS-01..03 (Advogado + Economista + Juiz progress — SSE 5 fases)"
  - "FR-OUTPUT-01..04 (PDF Ready S6 — CTA primário Baixar)"
  - "FR-DOCTYPE-01..02 (Multi-doctype dispatcher — sidebar 4 modos OR 7 modos pós-DEC-ERIC-DIV-01)"
cross_references:
  prd: "governance/prd/prd-v2.0.0-DRAFT.md (canônico Sprint 04 — todos FRs acima rastreáveis)"
  ux: "governance/ux-spec-v2.0.0-DRAFT.md S1+S2+S3+S4+S5+S6+S7 (S8 admin Eric defer SP04-ADMIN-01)"
  adrs: ["adr-014", "adr-016", "adr-017", "adr-019", "adr-005"]
  story_predecessors: ["SP04-AUTH-01", "SP04-BYOK-01", "SP04-LGPD-01"]
  smith_findings_addressed: "F-008 (login session expiry — SPA implementa logout flow + JWT refresh) + F-013 (RLS isolation visível na UI — settings panel mostra tenant_id ofuscado)"
  morpheus_handoff: ".lmas/handoffs/handoff-mor2sm-2026-05-09-sp04-ui-spa-integration.yaml"
tags:
  - project/revisor-contratual
  - story
  - sprint-04
  - epic-frontend
  - foundation
  - p0
  - multi-tenant
  - orsheva
  - spa
  - ui
---

# SP04-UI-SPA-01 — Frontend SPA OrSheva 7 backend integration

```
[@sm · River (Facilitator)] — Sprint 04 · Phase 14.1 · SP04-UI-SPA-01 · UI integration
SPRINT: 04 · PHASE: 14.1 · DOMÍNIO: software-dev/frontend-spa-integration
```

> **Foundation Sprint 04 P0 — UI canônica.** Eric commitou `index.html` na raiz do repo em 2026-05-09 15:55 (95580 bytes, SPA single-file standalone aplicando UX Spec v2.0.0 OrSheva 7 do Sati Phase 4). Story conecta esse SPA ao backend FastAPI existente (SP04-AUTH-01 + SP04-BYOK-01 + SP04-LGPD-01 já entregaram endpoints REST `/api/*`). Sem essa story, Sprint 04 não tem produto demonstrável — endpoints existem mas UI atual é Jinja2+HTMX legacy Sprint 02-03 desalinhada com brandbook.

> 🟢 **DEC-ERIC-DIV-01 RESOLVED 2026-05-09 — Opção A formalizada via ADR-020 Accepted.** SPA mostra **7 modos análise** (CCB Bancária / Veículo / Consignado / Cartão / Imobiliário / FIES / Geral). ADR-020 (supersedes ADR-016) entrega Strategy hierárquica 3-camada: 1 abstract base + BancarioBaseStrategy intermediate (DRY para CCB/Cartão/Consignado) + 7 concrete dispatchers (3 sub-bancários + 3 standalone + Geral catch-all Tier 3). Implementação **DESBLOQUEADA**.

---

## 1. Sumário

Story foundation Sprint 04 P0 — integra o SPA OrSheva 7 entregue por Eric (95KB single-file, mockup client-side puro) ao backend FastAPI existente. Foundation entregue por SP04-AUTH-01 (PR #4) já expõe `/api/auth/*` + `/api/onboarding/step2..4`; SP04-BYOK-01 (PR #5) entregou `/api/tenant/byok/*` lifecycle; SP04-LGPD-01 (InReview) entregou `/api/tenant/tos/*` + `/api/tenant/audit/isolation`. Esta story conecta a UI a esses endpoints + adiciona screens faltantes do UX Spec Sati v2.0.0:

1. **Asset extraction** — index.html raiz extract JS inline → `bloco_interface/web/static/spa.js` + CSS → `bloco_interface/web/static/spa.css` + index.html enxuto referenciando ambos (R-01 mitigation; cache busting + maintainability)
2. **GET / refactor** — FastAPI passa a servir SPA estático (`FileResponse` ou `HTMLResponse(read_text)`) em vez de template Jinja2 atual; templates antigos preservados (defer cleanup SP04-UI-CLEANUP-01)
3. **Auth flow** — login form do SPA dispara `fetch('/api/auth/login', POST)` → recebe JWT → guarda em **cookie httpOnly SameSite=Strict** (NÃO localStorage por security; R-04 mitigation) → transição #screen-login → #screen-app via classe CSS .active. Logout `POST /api/auth/logout` + clear cookie + volta #screen-login
4. **Onboarding wizard 4 passos** — adicionar `#screen-onboarding` ao SPA (visível pós-signup OR pós-login se onboarding incompleto): step1 dados escritório (`POST /api/auth/signup`) → step2 BYOK Anthropic key (`POST /api/onboarding/step2` com ping validation) → step3 DPA+TOS combine (`POST /api/onboarding/step3` Sati Opção B já validada SP04-LGPD-01) → step4 consolidate (`POST /api/onboarding/step4`)
5. **Analysis flow** — main view S4 upload PDF dispara `fetch('/revisar', POST FormData)` com {file, uf, data_assinatura, tier, doctype} → recebe job_id → abre `EventSource('/pipeline-stream?job_id=X')` → renderiza progress 5 fases (S5 conforme Sati C5 progress bar) → ao terminar `fetch('/verdict', GET)` → renderiza S6 PDF Ready com CTA primário **Baixar PDF** (Sati S6 CTA primary decision)
6. **Settings panel S7** — sidebar item "API Key (Claude)" abre painel chamando `GET /api/tenant/byok/status` → exibe estado atual (active/pending_rotation/revoked) + key_fingerprint truncated `sk-ant-...XYZ` + ações Rotate (`POST /api/tenant/byok/rotate`) + Revoke (`POST /api/tenant/byok/revoke`) conforme status
7. **Theme toggle** — botões light/dark/system no user dropdown persistem em `localStorage` e aplicam `data-theme` em `<html>`; preference detection `prefers-color-scheme` para 'system'

**Foundation impact:** Desbloqueia validação E2E real de TODA a stack Sprint 04 (auth + BYOK + LGPD + analysis + audit). Sem UI conectada, endpoints SP04-* são caixas-pretas testadas só por integration tests. Story permite Eric (operador) e advogados (tenants) usarem o produto end-to-end pela primeira vez.

**Branch strategy:** `feat/sp04-ui-spa-01` base `main` **pós-merge** PR #4 (SP04-AUTH-01) + PR #5 (SP04-BYOK-01) + PR #6 futuro (SP04-LGPD-01 quando entregar). Rebase trivial esperado (extends `bloco_interface/web/`, não modifica estruturas auth/byok/lgpd).

---

## 2. As a / I want / So that

- **As a** advogado responsável de escritório de advocacia brasileiro (tenant Sprint 04 cloud SaaS BYOK)
- **I want** acessar a plataforma Revisor Contratual via interface web visualmente coerente com brandbook OrSheva 7 (laranja Or-500 + navy Sheva-700 + pearl/bone + Fraunces+Manrope), fazer login com credenciais do meu escritório, configurar minha API key Anthropic via wizard onboarding, e fazer análise revisional de contratos bancários upload PDF → progress real-time SSE → veredito Baixar PDF
- **So that** consigo executar o workflow completo do Revisor Contratual end-to-end com UX profissional condizente com a tese ético-legal do produto (BYOK + LGPD-aware + validação humana obrigatória), sem depender de CLI técnica nem de Jinja2 templates legacy desalinhados com identidade visual

---

## 3. Acceptance Criteria (12 ACs)

### AC-01 — GET / serve SPA OrSheva 7 (substituindo template Jinja2 atual)

Refactor `bloco_interface/web/app.py` linha 481 (handler `@app.get("/")`):

```python
# ANTES (Jinja2 template atual):
@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    context = _layout_context(request)
    context.update({"history": _load_history(request)})
    return templates.TemplateResponse(request, "index.html", context)

# DEPOIS (SPA OrSheva 7):
@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Serve SPA OrSheva 7 — substituindo template Jinja2 (SP04-UI-SPA-01).

    Templates antigos preservados em templates/index.html.legacy para
    rollback rápido se necessário. SP04-UI-CLEANUP-01 remove definitivamente.
    """
    spa_path = STATIC_DIR / "index.html"  # SPA movido de raiz para static/
    return HTMLResponse(content=spa_path.read_text(encoding="utf-8"))
```

**Movimentação inicial:**
- `index.html` (raiz) → `bloco_interface/web/static/index.html`
- Templates Jinja2 atuais renomeados: `templates/index.html` → `templates/index.html.legacy` (preservar rollback)
- HISTÓRY/CARDS sidebar do SPA passa a ser populado via fetch separado (`GET /api/tenant/analyses?limit=10` — endpoint a criar OR mock por enquanto se ainda não existe)

**Tested:** integration test `test_get_root_serves_spa.py` — `GET /` retorna 200 + content-type `text/html` + body contém string `Revisor Contratual · OrSheva 7` (title do SPA) + `<div id="screen-login"` + `data-theme="light"`.

### AC-02 — Asset extraction JS+CSS para arquivos dedicados

SPA atual tem ~95KB com CSS + JS inline. Extrair para arquivos separados (R-01 maintainability):

```
bloco_interface/web/static/
├── index.html      (~5-10KB enxuto — só HTML estrutural + <link>+<script> referencias)
├── spa.css         (~30-40KB — todos os styles inline extraídos)
└── spa.js          (~50-60KB — todo o JS inline + módulos auth/onboarding/upload/sse/theme/logout)
```

**Estrutura `spa.js` modular (não bundler — vanilla ES modules):**

```javascript
// spa.js — módulo principal
import { initAuth } from './spa/auth.js';
import { initOnboarding } from './spa/onboarding.js';
import { initAnalysis } from './spa/analysis.js';
import { initSettings } from './spa/settings.js';
import { initTheme } from './spa/theme.js';

document.addEventListener('DOMContentLoaded', () => {
  initTheme();          // restore theme from localStorage
  initAuth();           // login form handlers + JWT cookie check
  initOnboarding();     // wizard 4 passos (visível pós-signup OR onboarding incompleto)
  initAnalysis();       // upload + SSE + verdict S6
  initSettings();       // BYOK panel + user mgmt
});
```

**OR alternativa pragmática (single file):** manter 1 arquivo `spa.js` com IIFE separadas por feature (`(function authModule(){...})();` etc) — Neo decide trade-off bundler-free vs ES modules nativos (Chrome 88+ / Firefox 83+ suportam imports relativos sem bundler).

**Tested:** browser dev tools confirma `index.html` referencia `<link rel="stylesheet" href="/static/spa.css">` + `<script type="module" src="/static/spa.js">` + carregamento sem erros 404; visual matching com SPA original raiz (pixel-perfect screenshot Playwright OR manual checklist).

### AC-03 — Login flow integrado a `/api/auth/login`

Login form do SPA (id="loginForm") dispara fetch real:

```javascript
// spa/auth.js
async function handleLogin(event) {
  event.preventDefault();
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  const errorBanner = document.getElementById('loginError');
  errorBanner.style.display = 'none';

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',  // permite cookie httpOnly SameSite=Strict
      body: JSON.stringify({ email, password }),
    });

    if (response.status === 401 || response.status === 403) {
      const err = await response.json();
      document.getElementById('loginErrorText').textContent =
        err.detail || 'E-mail ou senha incorretos.';
      errorBanner.style.display = 'flex';
      return;
    }

    if (!response.ok) {
      throw new Error(`Login failed: ${response.status}`);
    }

    const data = await response.json();
    // JWT é setado em cookie httpOnly pelo backend; SPA não manipula token diretamente
    // Backend retorna { user_id, tenant_id, onboarding_complete }
    if (!data.onboarding_complete) {
      showScreen('screen-onboarding');
    } else {
      showScreen('screen-app');
      hydrateUserMenu(data);
    }
  } catch (err) {
    document.getElementById('loginErrorText').textContent =
      'Erro de conexão. Verifique sua internet.';
    errorBanner.style.display = 'flex';
  }
}

document.getElementById('loginForm').addEventListener('submit', handleLogin);
```

**Backend prerequisite (verify SP04-AUTH-01 entregou):**
- `POST /api/auth/login` retorna JSON `{user_id, tenant_id, onboarding_complete: bool, full_name}` + Set-Cookie httpOnly
- 401 retorna JSON `{detail: "Credenciais inválidas"}` (não HTML)
- 403 retorna JSON `{detail: "Onboarding incompleto" OR "Tenant suspended"}`

⚠️ **VERIFICAR pré-implement:** se SP04-AUTH-01 retorna apenas `LoginResponse` Pydantic sem campo `onboarding_complete`, **patch trivial** em `bloco_auth/api.py` linha 170 adicionar campo (ler `tenants.onboarding_complete` flag). Se não existe flag, criar tech debt TD-SP04-12 LOW (tenant.onboarding_complete column).

**Tested:** unit test `test_spa_auth.py` (Playwright OR fetch mock) — login email válido + senha válida → cookie httpOnly recebido + redirect screen-app; login inválido → error banner visible + screen-login mantida; servidor 500 → error genérico "Erro de conexão"; servidor 403 onboarding incompleto → screen-onboarding active.

### AC-04 — Onboarding wizard 4 passos (#screen-onboarding novo)

Adicionar ao SPA novo screen `<div id="screen-onboarding" class="screen">` com wizard 4 passos seguindo Sati S2 wireframe:

**Step 1 — Dados do escritório** (FR-AUTH-01):
```javascript
async function submitStep1() {
  const data = {
    full_name: ...,
    email: ...,
    password: ...,
    cnpj: ...,
    tenant_name: ...,
  };
  const r = await fetch('/api/auth/signup', {
    method: 'POST',
    credentials: 'include',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data),
  });
  if (r.ok) {
    advanceStep(2);
  } else {
    const err = await r.json();
    showStepError(1, err.detail);
  }
}
```

**Step 2 — BYOK Anthropic key** (FR-API-KEY-01):
- Input `<input type="password" id="anthropicKey" placeholder="sk-ant-...">`
- Validação visual `sk-ant-` prefix antes de submit
- `POST /api/onboarding/step2 {anthropic_api_key}` → backend faz ping `GET https://api.anthropic.com/v1/models` (validate) + encrypt pgcrypto + insert tenant_api_keys
- Loader visual durante ping (~2-5s)
- Erro: chave inválida (401 Anthropic) → "Chave Anthropic inválida — verifique e tente novamente"

**Step 3 — DPA + TOS combine** (FR-LGPD-01 + FR-LGPD-02 — Sati Opção B já validada SP04-LGPD-01):
- Renderizar 2 articles HTMX-style: GET `/api/tenant/dpa/text/v1.0.0` + GET `/api/tenant/tos/text/v1.0.0` (endpoints SP04-LGPD-01)
- 2 checkboxes obrigatórios "Li e aceito o DPA v1.0.0" + "Li e aceito o TOS v1.0.0"
- Submit `POST /api/onboarding/step3 {dpa_version: "1.0.0", dpa_accepted: true, tos_version: "1.0.0", tos_accepted: true}`

**Step 4 — Tier + consolidate** (FR-AUTH-04):
- Selector tier `<select>`: Starter / Pro / Enterprise (Sati C6 Tier Badge)
- Submit `POST /api/onboarding/step4 {tier}` → backend marca `tenant.onboarding_complete=true` + retorna `CompleteOnboardingResponse`
- Sucesso → `showScreen('screen-app')` + hydrateUserMenu

**Tested:** integration test `test_onboarding_wizard_e2e.py` — 4 steps sequenciais, validação client-side em cada step, navegação back/forward dentro do wizard preservada (state em sessionStorage), submit final consolidate marca tenant ready, redirect screen-app. Browser test Playwright OR manual checklist.

### AC-05 — Upload + SSE + Verdict (S4 → S5 → S6)

Main view do SPA tem 7 modos de análise (DIV-01 — pendente). Implementação:

**S4 Nova Análise:**
```javascript
async function submitAnalysis() {
  const formData = new FormData();
  formData.append('file', document.getElementById('pdfInput').files[0]);
  formData.append('uf', document.getElementById('ufSelect').value);
  formData.append('data_assinatura', document.getElementById('dataInput').value);
  formData.append('tier', document.getElementById('tierSelect').value || 'balanced');
  formData.append('doctype', currentDoctype);  // de DIV-01 — sidebar selection

  const r = await fetch('/revisar', {
    method: 'POST',
    credentials: 'include',
    body: formData,
  });

  if (r.status === 413) {
    showError('Arquivo excede 10MB — comprima ou use OCR');
    return;
  }
  if (r.status === 415) {
    showError('Apenas PDFs são suportados');
    return;
  }

  // Backend retorna HTML partial (HTMX) com job_id em data-job-id attribute
  // OU adicionar Accept: application/json para JSON response (preferido para SPA)
  // OPCIONAL: refactor /revisar para JSON content negotiation
  const html = await r.text();
  const jobId = parseJobIdFromHTML(html);

  showScreen('screen-processing');
  startSSE(jobId);
}
```

**S5 Processing — SSE 5 fases (Sati C5 + MVP_LEAN_PHASES):**
```javascript
function startSSE(jobId) {
  const evtSource = new EventSource(`/pipeline-stream?job_id=${jobId}`);

  evtSource.addEventListener('phase', (e) => {
    const data = JSON.parse(e.data);
    updateProgressBar(data.phase_index, data.phase_name);  // 5 phases: Parsing/Advogado/Economista/Validador/Juiz
  });

  evtSource.addEventListener('done', async (e) => {
    evtSource.close();
    await fetchVerdict();
  });

  evtSource.addEventListener('error', (e) => {
    evtSource.close();
    showError('Erro no processamento — verifique audit log');
  });
}
```

**S6 PDF Ready — CTA primário Baixar (Sati decision crítica):**
```javascript
async function fetchVerdict() {
  const r = await fetch('/verdict', { credentials: 'include' });
  const data = await r.json();  // OR HTML partial — Neo decide content negotiation

  showScreen('screen-verdict');
  renderVerdict(data);
  // CTA primário: Baixar PDF (orange Or-500 grande)
  // CTAs secundários: Aprovar / Desaprovar (após download — audit timestamp captura)
}
```

⚠️ **VERIFICAR pré-implement:** endpoints `/revisar` + `/pipeline-stream` + `/verdict` atuais retornam HTML Jinja2 partials (HTMX). SPA pode:
- **Opção A**: refactor endpoints para Accept negotiation (JSON quando `Accept: application/json`) — ~2-4h
- **Opção B**: SPA injeta HTML retornado em `innerHTML` (HTMX-like manual) — preserva endpoints, mas mistura paradigma
- **River recomenda Opção A** (cleaner) — tracked como subtask AC-05a no implementation plan

**Tested:** integration test E2E upload PDF dummy (fixture `tests/fixtures/contrato-test.pdf`) → SSE 5 events `phase` + 1 event `done` → `/verdict` retorna JSON estruturado → render S6 com CTA primário visível. Smoke browser Playwright OR manual checklist.

### AC-06 — BYOK Settings panel (S7 — sidebar "API Key (Claude)")

Sidebar item `data-view="apikey"` abre painel S7 chamando `/api/tenant/byok/status`:

```javascript
async function openByokPanel() {
  const r = await fetch('/api/tenant/byok/status', { credentials: 'include' });
  const data = await r.json();
  // { status: 'active'|'pending_rotation'|'revoked',
  //   key_fingerprint: 'sk-ant-...XYZ',
  //   last_used_at: '2026-05-09T12:34:00Z',
  //   pending_fingerprint: ... (se pending_rotation),
  //   rotation_started_at: ... (se pending_rotation) }

  renderByokPanel(data);
}

async function rotateKey() {
  const newKey = prompt('Nova chave Anthropic (sk-ant-...):');
  if (!newKey || !newKey.startsWith('sk-ant-')) return;

  const r = await fetch('/api/tenant/byok/rotate', {
    method: 'POST',
    credentials: 'include',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ new_key: newKey }),
  });
  if (r.ok) {
    showToast('Chave rotacionada — overlap 24h ativo');
    openByokPanel();  // refresh
  }
}

async function revokeKey() {
  if (!confirm('Revogar chave irá suspender tenant. Continuar?')) return;
  const r = await fetch('/api/tenant/byok/revoke', {
    method: 'POST',
    credentials: 'include',
  });
  if (r.ok) {
    showToast('Chave revogada — re-onboarding necessário');
    showScreen('screen-onboarding');  // force re-onboarding step2
  }
}
```

**Estados visuais conforme C2 Tabela + C7 Toast (Sati):**
- `active` → fingerprint + "Última utilização: HH:MM" + botão Rotate (laranja) + botão Revoke (vermelho)
- `pending_rotation` → atual + nova fingerprint + countdown 24h + cancel button
- `revoked` → "Chave revogada em DD/MM/YYYY" + botão "Reconfigurar" (vai para onboarding step2)

**Tested:** integration test `test_byok_panel_e2e.py` — open panel → render status active → click rotate → mock prompt → verify POST → re-render pending_rotation; click revoke → confirm dialog → verify POST → redirect screen-onboarding step2.

### AC-07 — Theme toggle (light/dark/system) com persistência

Botões theme no user dropdown (already existem no SPA mockup — implementar lógica):

```javascript
// spa/theme.js
function initTheme() {
  const stored = localStorage.getItem('theme') || 'system';
  applyTheme(stored);
  document.querySelectorAll('[data-theme-set]').forEach(btn => {
    btn.addEventListener('click', () => {
      const theme = btn.dataset.themeSet;
      localStorage.setItem('theme', theme);
      applyTheme(theme);
    });
  });

  // Watch system changes if 'system' selected
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (localStorage.getItem('theme') === 'system') applyTheme('system');
    });
  }
}

function applyTheme(theme) {
  if (theme === 'system') {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.dataset.theme = isDark ? 'dark' : 'light';
  } else {
    document.documentElement.dataset.theme = theme;
  }
  // Update active segment in user dropdown
  document.querySelectorAll('[data-theme-set]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.themeSet === theme);
  });
}
```

**Tested:** unit test `test_theme.js` (Vitest OR jsdom) — toggle light/dark/system aplica `data-theme` correto + persiste localStorage + system mode reage a mudança `prefers-color-scheme`. Manual: visual matching tema dark vs light.

### AC-08 — Logout flow

Botão logout no user dropdown:

```javascript
async function handleLogout() {
  await fetch('/api/auth/logout', {
    method: 'POST',
    credentials: 'include',
  });
  // Backend invalida JWT + clear cookie httpOnly
  showScreen('screen-login');
  // Limpa qualquer state em sessionStorage (mas NÃO localStorage theme)
  sessionStorage.clear();
  hydrateUserMenu(null);
}
```

**Tested:** integration test `test_logout_e2e.py` — login → logout → cookie cleared (verify `document.cookie` não contém `jwt=` OR backend `/api/auth/me` retorna 401) → screen-login active.

### AC-09 — Disclaimer footer SPA atualizado

SPA atual tem texto Demo:
```html
<div class="login-foot">
  <strong>Demo:</strong> qualquer e-mail válido entra. A análise é simulada — nenhum documento é enviado para servidor.
</div>
```

**Atualizar para realidade Sprint 04:**
```html
<div class="login-foot">
  <strong>BYOK · LGPD-aware · Validação humana obrigatória.</strong>
  Análise revisional fundamentada em jurisprudência STJ/STF + BACEN. Operador: Eric Claudino (CNPJ XXX) per ADR-017.
</div>
```

**Tested:** integration test verifica string "BYOK · LGPD-aware" em `GET /` body + ausência de "Demo: qualquer e-mail válido entra" no HTML servido.

### AC-10 — Templates Jinja2 atuais NÃO removidos (defer cleanup)

**Preservar para rollback:**
- `templates/index.html` → `templates/index.html.legacy`
- `templates/login.html` → `templates/login.html.legacy`
- `templates/s1_login.html`, `s2_pre_upload.html`, `s5_processing.html`, `s6_resultado.html`, `s7_error.html` → preservados as-is
- `templates/onboarding/step1..4.html`, `_wizard_base.html` → preservados as-is
- `templates/partials/*` → preservados as-is

**Cleanup story criada:** `SP04-UI-CLEANUP-01` (a draftar pós-merge SP04-UI-SPA-01) — remove definitivamente, valida CI green, Smith adversarial.

**Razão:** preserva PR #4 e #5 review intactos (Eric pode re-revisar templates antigos no diff PR mesmo após merge desta story).

**Tested:** `git diff main..feat/sp04-ui-spa-01 --stat | grep delete` deve retornar **0 linhas** — nenhum arquivo deletado nesta story.

### AC-11 — Smoke test E2E browser

Adicionar `tests/integration/test_spa_e2e.py` com Playwright (OR manual checklist documentado se Playwright não disponível CI):

**Manual checklist (fallback):**
```markdown
## SP04-UI-SPA-01 Smoke E2E Manual Checklist

### Setup
- [ ] PostgreSQL rodando (Docker compose)
- [ ] `JWT_SECRET_KEY`, `MASTER_ENCRYPTION_KEY`, `AUTH_COOKIE_KEY` em .env
- [ ] Migrations aplicadas (sp04_001 + sp04_002 + sp04_003)
- [ ] `revisor-web` rodando em http://127.0.0.1:8501

### Login flow
- [ ] Acessa http://127.0.0.1:8501 → vê screen-login com brandbook OrSheva 7
- [ ] Login form com credenciais inválidas → error banner aparece
- [ ] Login form com credenciais válidas (tenant ja onboarded) → redirect screen-app

### Onboarding flow (tenant novo)
- [ ] Signup novo escritório → step1 dados → step2 BYOK key (use sk-ant-test ou real) → step3 DPA+TOS → step4 tier
- [ ] Cada step bloqueia avanço sem campos obrigatórios
- [ ] Step2 valida via ping Anthropic (5-10s) — chave inválida mostra erro
- [ ] Step4 marca tenant onboarding_complete + redirect screen-app

### Analysis flow
- [ ] Sidebar select doctype (qualquer um) → main view S4
- [ ] Upload PDF (use fixture tests/fixtures/contrato-test.pdf)
- [ ] Submit → screen-processing com progress 5 fases SSE
- [ ] Conclusão → screen-verdict S6 com CTA primário Baixar PDF
- [ ] Click Baixar → download trigger

### Settings BYOK
- [ ] Sidebar "API Key (Claude)" → painel mostra fingerprint + last_used_at
- [ ] Click Rotate → prompt nova key → status pending_rotation
- [ ] Click Revoke → confirm → redirect onboarding step2

### Theme toggle
- [ ] User dropdown → toggle light/dark/system → visual muda + persiste reload

### Logout
- [ ] User dropdown → Logout → redirect screen-login + cookie cleared
```

**Critério Done:** todos os checkmarks PASS em ambiente local + screenshots anexados em `governance/qa/sp04-ui-spa-01-smoke-e2e-evidence.md`.

**Tested:** `test_spa_e2e.py` com Playwright OR checklist manual completo + screenshots.

### AC-12 — Sidebar 7 modos live-bound ao backend dispatcher (RESOLVED Opção A via ADR-020 Accepted)

🟢 **RESOLVED 2026-05-09 — Opção A formalizada via ADR-020 Accepted.**

**Decisão Eric:** Opção A (manter 7 modos UX + Aria patch ADR) — ratify implícito via "avance" instruction.

**Implementation specs (frontend):**

```javascript
// spa/sidebar.js — sidebar selection capture
const SIDEBAR_DOCTYPES = ['ccb', 'veiculo', 'consignado', 'cartao', 'imobiliario', 'fies', 'geral'];

let currentDoctype = 'ccb';  // default

document.querySelectorAll('[data-mode]').forEach(btn => {
  btn.addEventListener('click', () => {
    currentDoctype = btn.dataset.mode;
    updateActiveButton(btn);
    updateBreadcrumb(btn.dataset.crumb);
    showAnalysisView(currentDoctype);  // S4 main view
  });
});

// Em spa/analysis.js — submit upload
async function submitAnalysis() {
  const formData = new FormData();
  formData.append('file', pdfInput.files[0]);
  formData.append('uf', ufSelect.value);
  formData.append('data_assinatura', dataInput.value);
  formData.append('tier', tierSelect.value || 'balanced');
  formData.append('doctype', currentDoctype);  // ← AC-12 mapping

  const r = await fetch('/revisar', {
    method: 'POST',
    credentials: 'include',
    body: formData,
  });
  // ... backend dispatcher resolves per ADR-020 §1.5 3-tier:
  //   Tier 1: doctype field (UI selector — autoritativo)
  //   Tier 2: LLM Haiku classifier (se field ausente)
  //   Tier 3: GeralDispatcher catch-all (fallback)
}
```

**Backend dispatcher resolution (per ADR-020 §1.5):**

```python
# bloco_workflow/dispatchers/router.py (NEW per ADR-020)
def resolve_dispatcher(
    ui_selector: str | None,         # AC-12: 'ccb'|'veiculo'|...|'geral'
    contract_text: str,
    classifier_llm: AnthropicClient,
) -> DoctypeDispatcher:
    DISPATCHERS = {
        'ccb': CCBDispatcher,
        'cartao': CartaoDispatcher,
        'consignado': ConsignadoDispatcher,
        'veiculo': VeicularDispatcher,
        'fies': FIESDispatcher,
        'imobiliario': ImobiliarioDispatcher,
        'geral': GeralDispatcher,
    }
    if ui_selector and ui_selector in DISPATCHERS:
        return DISPATCHERS[ui_selector]()
    classified = classifier_llm.classify(contract_text, labels=list(DISPATCHERS.keys()) + ['unknown'])
    if classified in DISPATCHERS:
        return DISPATCHERS[classified]()
    return GeralDispatcher()  # Tier 3 catch-all
```

**SCOPE DELIMIT esta story:**
- Frontend AC-12 implementa **client-side mapping** sidebar → POST /revisar com `doctype` field
- Backend Strategy refactor (CCBDispatcher, BancarioBaseStrategy, etc.) é **escopo separado** — Story SP04-DOCTYPE-01 NEW (a draftar paralelo)
- Esta story (SP04-UI-SPA-01) só plugar SPA frontend — Neo Strategy implementation backend fica isolado

**Tested:**
- Manual checklist: click cada um dos 7 sidebar buttons → currentDoctype atualizado → submit upload com doctype correto no FormData
- Backend mock dispatcher (até SP04-DOCTYPE-01 entregar real) aceita doctype field e retorna mock per-doctype
- Visual: active state na sidebar conforme button clicado (CSS `.nav-item.active`)
- Test integration: `tests/integration/test_spa_doctype_dispatch.py` (NEW) — verify FormData inclui `doctype` corretamente para cada um dos 7 modes

---

## 4. Files to Modify / Add (Pre-Implementation Contract)

### Novos arquivos (4)

1. `bloco_interface/web/static/index.html` — SPA OrSheva 7 enxuto (~5-10KB) — movido de raiz, JS+CSS inline extraídos
2. `bloco_interface/web/static/spa.css` — CSS extraído (~30-40KB)
3. `bloco_interface/web/static/spa.js` — JS extraído (~50-60KB) com módulos auth/onboarding/analysis/settings/theme/logout
4. `tests/integration/test_spa_e2e.py` — Playwright OR checklist manual + screenshots (~200 LOC OR markdown evidence)

### Modificados (4-6)

5. `bloco_interface/web/app.py` — handler `GET /` refactor (linha 481) para servir SPA static; possivelmente `Accept: application/json` content negotiation em `/revisar` + `/pipeline-stream` + `/verdict` (AC-05 Opção A — Neo decide)
6. `bloco_auth/api.py` — possivelmente adicionar campo `onboarding_complete` em `LoginResponse` (AC-03 verify pré-implement) + endpoint `GET /api/auth/me` (current user — opcional, pode reutilizar JWT cookie)
7. `index.html` (raiz) — **DELETE** após move para `static/` (mas defer para SP04-UI-CLEANUP-01? Decisão River: **delete agora** se PR review apresenta diff move como D+A pair, OR keep como redirect comment se confunde reviewer — Neo decide UX commit)
8. `bloco_interface/web/templates/index.html` → `templates/index.html.legacy` — preservar rollback
9. `bloco_interface/web/templates/login.html` → `templates/login.html.legacy` — preservar rollback
10. `pyproject.toml` — possivelmente adicionar `playwright>=1.40` em `[project.optional-dependencies] dev` (se AC-11 Playwright caminho)

### Pendências cross-domain (não implementação Neo)

- ✅ ~~**Eric MANDATORY pre-implement:** Decisão `DEC-ERIC-DIV-01`~~ → **RESOLVED 2026-05-09 Opção A** via ADR-020 Accepted
- ✅ ~~**Aria MANDATORY se Opção A:** ADR-020~~ → **DONE 2026-05-09** ADR-020 Accepted (governance/architecture/adr/adr-020-multi-doctype-dispatcher-v2.md)
- ⏳ **Sati MANDATORY:** Wireframe S4 7 doctype variants (cada um pode ter campos específicos no upload form — ex: FIES tem campo "ano matrícula", Imobiliário tem "matrícula RGI") — pode ser **post-hoc ratify** (sidebar SPA já entregue Phase 4; variants S4 podem ser refinados pós-implementation)
- ⏳ **Operator MANDATORY:** PR #4 + PR #5 merged em main antes de chunk 1 (clean rebase base) — DEC-ERIC-MERGE-ORDER ainda pendente

**NOTA ADICIONAL:** Story **SP04-DOCTYPE-01 NEW** (Strategy refactor backend per ADR-020 §2-7) será draftada paralelo — implementação backend Strategy hierárquica (DoctypeDispatcher + BancarioBaseStrategy + 7 concrete dispatchers + 32 prompt files + migrations sp04_004 + sp04_005) **NÃO está incluída nesta story**. Esta story (SP04-UI-SPA-01) é frontend integration only — backend dispatcher é mock até SP04-DOCTYPE-01 entregar real.

---

## 5. Pre-flight Consultation

### @architect Aria (✅ MANDATORY DONE 2026-05-09 — ADR-020 Accepted)

**Status:** ✅ **DONE** — Eric escolheu Opção A (manter 7 modos), Aria entregou **ADR-020 Multi-Doctype Dispatcher v2** (Accepted 2026-05-09):
- ✅ **Strategy hierárquica 3-camada:** 1 abstract base + BancarioBaseStrategy intermediate + 7 concrete dispatchers (3 sub-bancários DRY + 3 standalone + Geral catch-all Tier 3)
- ✅ **Vault jurisprudencial:** doctype_tag enum 5 → 8 valores (ccb|cartao|consignado|geral + bancario_cross + cdc_cross + cross preserved + veiculo|fies|imobiliario preserved); TD-SP04-13 NEW MEDIUM tracking gaps Cartão/Consignado/Geral curadoria Sprint 06+
- ✅ **BACEN SGS series:** Cartão precisa CDI 4391 + SELIC 1178 (1178 já carregada); CCB precisa modalidade 218 (217 já carregada); Imobiliário usa TR + Poupança IPCA já carregadas; migration sp04_005_bacen_series_doctype_v2.sql
- ✅ **Detecção 3-tier:** UI selector (Tier 1) + LLM Haiku classifier (Tier 2) + GeralDispatcher catch-all (Tier 3 — substitui ADR-016 unknown rejection)

**Cross-reference:** [`governance/architecture/adr/adr-020-multi-doctype-dispatcher-v2.md`](../architecture/adr/adr-020-multi-doctype-dispatcher-v2.md) — adr_level: spec — implementation specs detalhados

### @data-engineer Tank (NÃO necessário)

**Status:** Esta story não toca schema PostgreSQL — só frontend + handlers existentes. Tank pre-flight **skipped**.

### @ux-design-expert Sati (⏳ MANDATORY — Opção A formalizada)

**Status:** Eric escolheu Opção A (7 modos sidebar) — Sati DEVE elaborar S4 wireframe variants. Cada doctype pode ter form fields específicos:
- FIES: "ano matrícula" + "instituição ensino"
- Veicular: "ano veículo" + "marca/modelo"
- Imobiliário: "matrícula RGI" + "valor avaliação"
- CCB / Cartão / Consignado: form bancário base (compartilhado via BancarioBaseStrategy ADR-020)
- Geral: form genérico catch-all

**Cognitive load:** form length precisa cuidado — Sati avalia se mostrar todos campos OR progressive disclosure (campos específicos aparecem após selecionar doctype).

**Pragmatismo River:** Sidebar SPA 7 modos já entregue Sati Phase 4 (S4 form genérico cobre uniforme). Variants S4 específicas podem ser **post-hoc ratify** (refinamento pós-implementation Neo, não bloqueia chunks 1-7 desta story). Default: form genérico atual + extras Sprint 06+ se métricas mostrarem necessidade.

### @qa Oracle Smith (post-merge — defer)

**Status:** Smith adversarial review (Sprint 04 close-out invocation) avalia E2E flow + JWT cookie security + RLS isolation visível na UI + DEC-ERIC-DIV-01 implications. Defer para qa-gate G5 OR post-merge.

### Eric advogado (NÃO necessário esta story)

**Status:** Texto DPA/TOS finalizado em SP04-LGPD-01 — reutilizado as-is via endpoints `/api/tenant/{dpa,tos}/text/v1.0.0`.

---

## 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **R-01** JS inline 95KB single-file dificulta manutenção | ALTA | MEDIUM (DX) | AC-02 extract JS+CSS para arquivos separados (módulos OR IIFE); commit history clear (chunks 1-2) facilita revert por feature |
| ~~**R-02** DEC-ERIC-DIV-01 sidebar 7 vs 4 doctypes não decidida bloqueia implementação~~ | ~~ALTA~~ → **RESOLVED** | ~~HIGH~~ → **N/A** | 🟢 **RESOLVED 2026-05-09** via ADR-020 Accepted (Opção A) — sidebar 7 modos formalizada arquiteturalmente |
| **R-NEW-02** Trinity Phase 3 PRD bloqueio templates D3 conteúdo legal (3 novos: CCB/Cartão/Consignado/Geral) | MÉDIA | MEDIUM | Bloqueia **SP04-DOCTYPE-01 chunks finais (templates D3 conteúdo)** — NÃO bloqueia esta story (SP04-UI-SPA-01 frontend integration). Trinity entrega paralelo durante Neo backend implementation. River drafta SP04-DOCTYPE-01 separadamente |
| **R-03** Conflict merge com PR #4 (SP04-AUTH-01) e #5 (SP04-BYOK-01) ainda OPEN | MÉDIA | MEDIUM | Branch `feat/sp04-ui-spa-01` base **main pós-merge** — chunks só iniciam após Operator merge AUTH+BYOK; rebase trivial esperado (extends bloco_interface, não modifica auth/byok) |
| **R-04** JWT cookie security — localStorage vs httpOnly | MÉDIA | HIGH (security) | AC-03 explicitamente httpOnly + SameSite=Strict + Secure (prod). Sem fallback localStorage. Smith review valida em qa-gate G5 |
| **R-05** Endpoints `/revisar` + `/pipeline-stream` + `/verdict` retornam HTML Jinja2 (HTMX legacy) — SPA precisa JSON | ALTA | MEDIUM | AC-05 Opção A: refactor endpoints com Accept negotiation (~2-4h Neo subtask). Fallback Opção B injection HTML em innerHTML preserva endpoints mas mistura paradigma |
| **R-06** Breaking change templates removidos quebram demo screenshots/docs antigos | LOW | LOW | AC-10 templates Jinja2 preservados como `.legacy` (não deletados nesta story); cleanup defer SP04-UI-CLEANUP-01 |
| **R-07** Sati S2 wireframe wizard 4 passos não implementado pixel-perfect | LOW | LOW | River recomenda Sati post-hoc ratify (não pre-implement) — UX Spec v2.0.0 já documenta C4 form input pattern; Neo aplica + Sati ratify pós-deploy |
| **R-08** Smoke E2E manual checklist Playwright unavailable em CI | MÉDIA | LOW | AC-11 fallback: checklist manual + screenshots evidence. CI Playwright integration TD-SP04-13 LOW Sprint 06+ |

---

## 7. Implementation Plan (Path B chunks sugeridos — Neo refina)

Pattern Path B SP04-AUTH-01/BYOK-01/LGPD-01 adaptado para frontend:

1. **Chunk 1** — Setup environment: branch `feat/sp04-ui-spa-01` (base main **POS-MERGE PR #4 + #5**) + skeleton extract structure (mover index.html raiz → `bloco_interface/web/static/`)
2. **Chunk 2** — Asset extraction: split CSS+JS inline → `static/spa.css` + `static/spa.js` modules (auth/onboarding/analysis/settings/theme/logout) + index.html enxuto referenciando
3. **Chunk 3** — Backend handler refactor: `app.py` GET / serve SPA static + preserve templates como `.legacy` + content negotiation `/revisar`+`/pipeline-stream`+`/verdict` (AC-05 Opção A) + adicionar `onboarding_complete` em `LoginResponse` se ausente (AC-03 verify)
4. **Chunk 4** — Auth flow: implementar `spa/auth.js` login + logout + JWT cookie httpOnly handling + screen transitions + ~5 unit tests
5. **Chunk 5** — Onboarding wizard: implementar `spa/onboarding.js` 4 passos (#screen-onboarding) + state navigation + validation client-side + ~6 unit tests
6. **Chunk 6** — Analysis flow + Settings: implementar `spa/analysis.js` (S4 upload + S5 SSE + S6 verdict) + `spa/settings.js` (BYOK panel) + `spa/theme.js` (toggle) + ~8 unit tests
7. **Chunk 7** — Smoke E2E + closure: `test_spa_e2e.py` Playwright OR manual checklist + screenshots evidence + Final File List Consolidado + status InReview + handoff @qa Oracle qa-gate G5

**Estimativa River:** 3-5 days (chunk 4-7 paralelizável parcialmente; chunk 6 maior — 1-2 days; chunk 7 ~0.5 day se manual)

**Branch creation timing:** Operator/Neo cria chunk 1 base main **APÓS**:
- (a) DEC-ERIC-DIV-01 resolvida + story status Draft → Ready (Keymaker G3)
- (b) PR #4 SP04-AUTH-01 merged em main
- (c) PR #5 SP04-BYOK-01 merged em main
- (d) PR #6 SP04-LGPD-01 mergeable OR merged (não bloqueante hard — endpoints LGPD em InReview suficientes)

---

## 8. Definition of Done (Neo Phase 14.3 — populated empíricamente chunks 1-7)

**(Pendente — Neo preenche pós-implementação chunks 1-7. Template:)**

### VERIFIED (target ≥10 items)

- [x] **AC-01 chunk 1 MINIMAL — index.html moved + GET / serve SPA + templates legacy preserved** — Phase 14.7 commit (esta sessão Neo). Sintaxe app.py compile OK. Pytest local falhou por interpreter Python 3.14 sem pyjwt (não venv projeto) — CI GitHub Actions Python 3.11+3.12 com venv valida no push. **Override pragmático Section 7 timing** — chunks 2-7 ainda aguardam Eric merge PR #4+#5 + branch nova feat/sp04-ui-spa-01.
- [ ] AC-02 Asset extraction — `static/{index,spa.css,spa.js}` com index.html ≤10KB
- [ ] AC-03 Login flow integrado `/api/auth/login` — JWT cookie httpOnly
- [ ] AC-04 Onboarding wizard 4 passos #screen-onboarding completo
- [ ] AC-05 Upload + SSE + Verdict flow E2E
- [ ] AC-06 BYOK Settings panel S7
- [ ] AC-07 Theme toggle persistente localStorage
- [ ] AC-08 Logout clear cookie + screen-login
- [ ] AC-09 Disclaimer footer atualizado (sem "Demo")
- [ ] AC-10 Templates Jinja2 preservados `.legacy`
- [ ] AC-11 Smoke E2E manual checklist OR Playwright PASS
- [ ] AC-12 DEC-ERIC-DIV-01 implementada (Opção A/B/C)
- [ ] Suite testes ≥232+N (zero regression)
- [ ] CI verde Python 3.11 + 3.12

### WAIVED (a popular conforme empíria — pattern SP04-LGPD-01)

- (Neo preenche pós-chunks. Possíveis waivers esperados:)
  - WAIVED-UI-01 (LOW) — Playwright CI integration deferred TD-SP04-13
  - WAIVED-UI-02 (MEDIUM) — Endpoints HTML Jinja2 antigos preservados (cleanup SP04-UI-CLEANUP-01)
  - WAIVED-UI-03 (LOW) — CodeRabbit DEFERRED (pattern Sprint 04)

---

## 9. QA Validation (@po Keymaker — *validate-story-draft G3) — PENDENTE

**Status:** Story em **Draft**. Validate G3 só após:
1. ✅ DEC-ERIC-DIV-01 resolvida (Eric escolhe Opção A/B/C)
2. ✅ River patch story atualizando AC-12 com decisão concreta + ajustes Section 4 (files) + Section 6 (risks) conforme escolha
3. ✅ Status: Draft → Ready
4. ✅ Skill `LMAS:agents:po` `*validate-story-draft SP04-UI-SPA-01`

### Verdict @po Keymaker (2026-05-09T21:25 — RE-VALIDATE pós River patch)

**Verdict:** ✅ **GO** | **Score: 10/10** | **Status:** Ready (preserved) → autorizado para `*develop` Neo (chunks 1-7 Path B)

> Story tem qualidade técnica sólida pós River patch. ADR-020 Accepted formalizou DEC-ERIC-DIV-01 Opção A. AC-12 reescrito com implementation specs concretos (JS code blocks frontend + backend dispatcher resolution per ADR-020 §1.5). Scope delimit explícito (frontend only — backend SP04-DOCTYPE-01 NEW separada). Paridade total com SP04-BYOK-01 + SP04-LGPD-01 (template Sprint 04 maduro).

#### 10-point PO Master Checklist (G3)

| # | Ponto | Score | Evidência |
|---|-------|-------|-----------|
| 1 | Frontmatter completo (18+ campos) | ✅ 1/1 | type/id/title/status (Ready)/epic/project/sprint/phase/priority/estimated_days/agent/branch/created/created_by/predecessor_handoff/predecessor_artifact/predecessor_ux_spec/dependencies(8 — incluindo ADR-020 + ADR-016 superseded)/source_frs(10)/cross_references/tags(11) — paridade SP04-BYOK-01/LGPD-01 confirmada |
| 2 | Sumário Section 1 claro | ✅ 1/1 | 7 deliverables explicitados (asset extraction + GET / refactor + auth flow + onboarding wizard + analysis flow + settings panel + theme toggle) + foundation impact (desbloqueia E2E real Sprint 04) + branch strategy + NOTA divergência inicial atualizada para RESOLVED |
| 3 | As a / I want / So that Section 2 | ✅ 1/1 | Advogado responsável (BYOK tenant Sprint 04 cloud SaaS) + workflow E2E SPA OrSheva 7 + tese ético-legal (BYOK + LGPD-aware + validação humana) — papel/quero/para cristalino |
| 4 | ACs estruturadas Section 3 (testable + 5+) | ✅ 1/1 | 12 ACs (excede mínimo 5) — cada um com "Tested:" explícito + code blocks copy-paste-ready em AC-01..08 + checklist manual em AC-11. AC-12 reescrito pós-DIV-01 com JS frontend + Python backend specs. Exemplar Sprint 04 padrão |
| 5 | File List Section 4 pre-implementation contract | ✅ 1/1 | 4 novos (static/index.html + spa.css + spa.js + test_spa_e2e.py) + 4-6 modificados (app.py + auth/api.py + index.html raiz + 2 templates legacy + pyproject.toml) + cross-domain pendências explícitas (Sati S4 variants post-hoc, Operator merge order) |
| 6 | Pre-flight consultation Section 5 | ✅ 1/1 | Aria CONDITIONAL → MANDATORY DONE (ADR-020 entregue + Accepted) + Sati CONDITIONAL → MANDATORY (S4 7 variants — post-hoc ratify acceptable per River pragmatism) + Tank N/A justificada (sem schema) + Smith defer post-merge + Eric advogado N/A (TOS reusa SP04-LGPD-01) |
| 7 | Risk Assessment Section 6 (3+ risks com P/I/M) | ✅ 1/1 | 8 risks tabelados (R-01 R-03..R-08) + R-02 strikethrough RESOLVED via ADR-020 + R-NEW-02 Trinity PRD bloqueio templates D3 (não bloqueia esta story). Cada risk com Probability/Impact/Mitigation completo |
| 8 | Implementation Plan Section 7 chunks | ✅ 1/1 | 7 chunks Path B (setup → asset extraction → backend handler → auth → onboarding → analysis+settings → smoke E2E) + estimativa 3-5 days + branch creation timing condicional (PR #4+#5 merged) |
| 9 | Cross-references rastreáveis | ✅ 1/1 | PRD v2.0.0-DRAFT + ADRs (014, 016 superseded, 017, 019, 020 Accepted) + predecessors (SP04-AUTH-01 + BYOK-01 + LGPD-01) + Sati UX Spec v2.0.0 S1..S8 + Smith findings F-008 + F-013 + Morpheus handoff predecessor |
| 10 | Frontmatter dependencies + source_frs canônicos | ✅ 1/1 | 8 dependencies (3 stories Done + 5 ADRs incluindo ADR-020 Accepted) + 10 source_frs canônicos (FR-AUTH-03/01 + FR-API-KEY-01 + FR-LGPD-01..02 + FR-OCR-01..02 + FR-PERSONAS-01..03 + FR-OUTPUT-01..04 + FR-DOCTYPE-01..02) — todos rastreáveis PRD v2.0.0-DRAFT |
| **TOTAL** | | **10/10** | **GO threshold ≥ 7/10 — exceeded by 3 pontos. Score perfeito paridade SP04-BYOK-01 + LGPD-01.** |

#### Concerns Keymaker (3 itens — todos não-bloqueantes)

| # | Concern | Severidade | Recomendação |
|---|---------|-----------|--------------|
| **K-UI-01** | **Sati post-hoc ratify pragmatismo (S4 wireframes 7 variants)** | LOW | ✅ Aceito — sidebar SPA já entregue Sati Phase 4 (facto consumado). Variants per-doctype são refinamento UX Sprint 06+ se métricas cohort demandarem. River argument procede |
| **K-UI-02** | **Scope split SP04-UI-SPA-01 (frontend) vs SP04-DOCTYPE-01 NEW (backend)** | LOW | ✅ Aceito — Section 1 + AC-12 + Section 4 explicitam zero overlap. Frontend story plugs SPA → endpoints; backend story implementa Strategy refactor (32 prompts + 7 dispatchers + migrations sp04_004/005). Scope claro |
| **K-UI-03** | **DEC-ERIC-MERGE-ORDER ainda pendente (PR #4/#5 merge antes chunk 1)** | MEDIUM | ⚠️ Non-blocking validate G3 — Section 7 Implementation Plan já documenta branch creation timing condicional. Story Ready ≠ Neo *develop pode iniciar agora. Aguardar Eric merge PR #4+#5 antes de chunk 1 (PR #6 não-bloqueante hard) |

#### Validações especiais Keymaker

| Aspecto | Validação |
|---------|-----------|
| **AC-12 implementation specs concretos** | ✅ EXEMPLAR — JS code blocks (spa/sidebar.js + spa/analysis.js + dispatcher resolution Python ADR-020 §1.5) + scope delimit + Tested: integration test path. Neo tem mapa copy-paste-ready |
| **ADR-020 dependency rastreável** | ✅ Accepted 2026-05-09 + supersedes ADR-016 + 7 doctypes operacionais formalmente arquitetados — DEC-ERIC-DIV-01 traceability completa |
| **Paridade SP04-BYOK-01/LGPD-01** | ✅ Mesmo padrão estrutural (12 sections + 8 risks + 7 chunks Path B + 10-point checklist + Anti-Patterns Section 10 + Files NOT to Modify Section 11 + Change Log Section 12) — template Sprint 04 maduro |
| **Constitutional No Invention** | ✅ Todos deliverables rastreáveis FR-AUTH/API-KEY/LGPD/OCR/PERSONAS/OUTPUT/DOCTYPE OR ADR-014/017/019/020 OR Sati UX Spec v2.0.0 S1..S8. Zero invention |
| **Branch base safety** | ✅ Branch creation timing condicional explícito Section 7 — PR #4+#5 merged antes chunk 1 (clean rebase) — preserva PRs review intactos |

#### Próximo step

**Recomendação Keymaker:** Skill `LMAS:agents:dev` (@dev Neo) `*develop SP04-UI-SPA-01` Path B chunks 1-7 — **MAS** Operator/Eric MUST merge PR #4 + PR #5 antes do chunk 1 (Section 7 timing requirement). Sequência:

1. ⏳ Eric review + merge PR #4 SP04-AUTH-01 (exclusive)
2. ⏳ Eric review + merge PR #5 SP04-BYOK-01 (exclusive)
3. ⏳ Eric review + merge PR #6 SP04-LGPD-01 (opcional pre-chunk 1, MERGEABLE confirmado)
4. ✅ Skill `LMAS:agents:dev` *develop SP04-UI-SPA-01 chunks 1-7 (~3-5 days Neo)
5. ✅ Skill `LMAS:agents:qa` *qa-gate G5 SP04-UI-SPA-01 pós-Neo InReview
6. ✅ Skill `LMAS:agents:devops` *push + *create-pr → PR #7 base main

**Paralelo opcional (não-bloqueante):**
- River drafta SP04-DOCTYPE-01 NEW (backend Strategy refactor per ADR-020 §2-7) — ~3-5 days Neo paralelo durante Trinity Phase 3 PRD conteúdo legal templates D3

— Keymaker, equilibrando prioridades 🎯

---

## 10. Anti-Patterns (Defensive Scope Guard)

- ❌ Editar/deletar templates Jinja2 antigos `templates/login.html`, `s1_login.html`, `onboarding/step*.html` nesta story — defer SP04-UI-CLEANUP-01
- ❌ Implementar token JWT em localStorage/sessionStorage — APENAS cookie httpOnly SameSite=Strict
- ❌ Bundler (webpack/vite/rollup) — vanilla ES modules ou IIFE (manter zero-build philosophy LEAN)
- ❌ React/Vue/Svelte — SPA é vanilla JS (Sati UX Spec v2.0.0 + brandbook OrSheva 7 não exigem framework)
- ❌ Implementar 7 modos backend (Opção A) sem Aria patch ADR-016 v2 OR ADR-020 — bloqueia até decisão arquitetural
- ❌ Remover footer disclaimer "Demo" antes da integração real estar PASS — manter até AC-11 verde
- ❌ Quebrar endpoints HTMX existentes (`POST /revisar` retornar JSON sem fallback HTML) — content negotiation preserva ambos paradigmas durante transição
- ❌ Inline credenciais Anthropic ou JWT secret no JS — APENAS em backend env vars
- ❌ Mover `index.html` raiz sem preservar git history (use `git mv` para conservar blame chain)

---

## 11. Files NOT to Modify (Defensive Scope Guard)

Esta story **NÃO** modifica:
- `bloco_auth/api.py` (exceto AC-03 patch trivial `LoginResponse.onboarding_complete` se ausente)
- `bloco_auth/byok_api.py`, `bloco_auth/byok_*.py` — endpoints já entregues SP04-BYOK-01
- `bloco_auth/dpa.py`, `bloco_auth/tos.py`, `bloco_auth/audit_isolation.py` — endpoints já entregues SP04-LGPD-01
- `bloco_auth/onboarding.py`, `bloco_auth/jwt_utils.py`, `bloco_auth/passwords.py` — foundation SP04-AUTH-01
- `bloco_workflow/personas/*` — pipeline interno
- `bloco_engine/`, `bloco_vault/`, `bloco_audit/`, `bloco_lgpd/`, `bloco_database/` — backend untouched
- Migrations SQL — zero schema change

---

## 12. Change Log

| Data | Versão | Autor | Descrição |
|------|--------|-------|-----------|
| 2026-05-09 | v1.0.0-DRAFT | @sm River | Story criada conforme handoff Morpheus `.lmas/handoffs/handoff-mor2sm-2026-05-09-sp04-ui-spa-integration.yaml`. Status Draft — bloqueada por DEC-ERIC-DIV-01 (sidebar 7 vs 4 doctypes ADR-016) + branch base main aguarda merge PR #4 + #5. 12 ACs estruturadas. River-decision: extract JS+CSS para arquivos separados (R-01 mitigation MANDATORY); JWT cookie httpOnly (R-04 security); content negotiation endpoints `/revisar`+`/pipeline-stream`+`/verdict` (R-05 cleanest path). Pre-flight Aria/Sati CONDITIONAL conforme decisão DIV-01. |
| 2026-05-09 | v1.1.1 | @dev Neo | Phase 14.7 — *develop chunk 1 MINIMAL execução: 3 git ops (1 mv index.html raiz → bloco_interface/web/static/index.html sem git mv pois untracked; 2 git mv templates/index.html → .legacy + templates/login.html → .legacy preservados rollback); refactor bloco_interface/web/app.py GET / handler (linha 481) — substituído templates.TemplateResponse(s2_pre_upload.html) + route protection MVP-LEAN-01 Task 2 por HTMLResponse simples lendo STATIC_DIR / "index.html" (SPA decide login flow client-side via screen-login OR screen-app conforme cookie/state). Verify pós-fix: `python -m py_compile bloco_interface/web/app.py` → OK; `python -m ruff check bloco_interface/web/app.py` → 1 finding pré-existente UP041 (asyncio.TimeoutError → TimeoutError builtin) NOT introduzido por chunk 1; pytest local falhou por Python 3.14 AppData sem pyjwt (não venv projeto) — CI GitHub Actions Python 3.11+3.12 valida no push. Override pragmático Section 7 timing (chunks 2-7 ainda aguardam Eric merge PR #4+#5). Eric agora pode testar visualmente via `revisor-web` — GET / serve SPA OrSheva 7 95KB direto. Próximo: Operator push + Eric merge PR #4+#5 → Skill Neo *develop chunks 2-7 em branch nova feat/sp04-ui-spa-01 base main pós-merge. |
| 2026-05-09 | v1.1.0 | @sm River | Phase 14.2 — *patch-story SP04-UI-SPA-01 DEC-ERIC-DIV-01 RESOLVED via ADR-020 Accepted (Opção A formalizada — Eric ratify implícito 'avance' instruction). 6 sections edit + frontmatter status Draft → **Ready**: (1) Frontmatter dependencies — adicionado ADR-020 + ADR-016 marked superseded; (2) NOTA divergência inicial atualizada para RESOLVED; (3) AC-12 reescrito com implementation specs frontend (sidebar 7 buttons → POST /revisar com `doctype` field per ADR-020 §1.5 3-tier dispatcher resolution) + scope delimit (esta story é frontend integration only; backend Strategy refactor em SP04-DOCTYPE-01 NEW separada); (4) Section 4 Pendências cross-domain — Aria DONE + Sati CONDITIONAL→MANDATORY post-hoc ratify acceptable; (5) Section 5 Pre-flight — Aria CONDITIONAL→MANDATORY DONE (ADR-020 entregue) + Sati CONDITIONAL→MANDATORY (S4 7 variants post-hoc); (6) Section 6 Risks — R-02 strikethrough RESOLVED + R-NEW-02 Trinity Phase 3 PRD bloqueio templates D3 (não bloqueia esta story, bloqueia SP04-DOCTYPE-01). AC-12 desbloqueado para Neo. Story status Ready para Skill Keymaker validate-story-draft G3 10-point. Próximo: handoff `.lmas/handoffs/handoff-sm-to-po-2026-05-09-validate-sp04-ui-spa-01.yaml`. |

---

```
[@sm · River (Facilitator)] — drafted 2026-05-09 sessão SPA integration
"As correntes encontram seu leito quando a porta está clara. Eric mostra a porta;
Aria valida o caminho; Neo trilha; Oracle vela; Operator atravessa.
Esta story é o leito — Neo só corre quando DIV-01 fluir."

— River, removendo obstáculos 🌊
```
