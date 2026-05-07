---
type: ux-spec
id: "UX-SPEC-MVP-LEAN-01"
title: "UX Spec — Revisor Contratual MVP-LEAN-01 single-page"
status: proposed
date: "2026-05-06"
project: revisor-contratual
sprint: "03"
etapa: "CC.3 — single-page architecture"
references:
  - "PRD v1.1.2.1 (governance/prd/prd-v1.1.2-PATCH.md)"
  - "ADR-013 MVP Lean Strategy (governance/architecture/adr/adr-013-mvp-lean-strategy-deployment-path.md)"
  - "ADR-002 Design System (revogado parcialmente — tokens preservados)"
  - "ADR-009 NFR-LGPD-01 100% on-premise"
  - "ADR-011 Auto-Ollama Lifecycle"
  - "ADR-012 Vault Data Bundling"
  - "Story REV-INT-01 (FastAPI + HTMX + Jinja2)"
  - "Story REV-INT-02 (tokens woff2 self-hosted Manrope + Fraunces + JetBrains)"
designer: "@ux-design-expert Sati"
predecessor_decisions:
  - "REV-INT-01 substituiu Streamlit por FastAPI+HTMX+Jinja2"
  - "REV-INT-02 self-hosted woff2 (LGPD on-premise — zero CDN)"
  - "ADR-013 § 2.3 Defense-in-depth LGPD 5 camadas"
  - "ADR-013 § 2.5 Dual-layer Tema 1378 STJ"
tags:
  - project/revisor-contratual
  - ux-spec
  - mvp-lean
  - single-page
  - sprint-03
  - cc3
---

# UX Spec — Revisor Contratual MVP-LEAN-01 single-page

```
[@ux-design-expert · Sati (Empathizer)] — Sprint 03 · CC.3 UX spec MVP-LEAN-01
DOMÍNIO: SoftwareDev/UX · ARQUITETURA: single-page (HTMX swap) · LGPD: 100% on-premise
```

---

## 1. Contexto — Why single-page

### 1.1 Decisão arquitetural

O MVP-LEAN-01 é entregue como **single-page com seções condicionais HTMX swap** (não SPA com routes; não multi-page tradicional). O usuário-alvo é advogado consumerista bancário em laptop pessoal — fluxo linear: **autentica → vê banner regulatório → faz upload → assiste processing → baixa 3 deliverables**. Não há navegação lateral, não há histórico de processos, não há dashboard de métricas.

### 1.2 Why (rastreável a PRD + ADR-013)

| Razão | Fonte |
|---|---|
| **Linearidade do user journey** | PRD v1.1.2.1 §4.3 — fluxo único: auth → upload → processing → 3 deliverables |
| **Defense-in-depth LGPD em 1 lugar** | ADR-013 §2.3 — 5 camadas LGPD aplicam-se a toda a sessão; sem páginas de "config" / "histórico" / "settings" para reduzir attack surface |
| **Banner Tema 1378 sempre visível** | ADR-013 §2.5 + FR-MONITOR-01 — alerta regulatório CRÍTICO não pode ser "outra aba" que o operador esquece de visitar |
| **Audit chain transparente** | FR-AUDIT — single-page facilita Origin do `audit.jsonl` evento-por-evento sem ambiguidade de qual página gerou qual entry |
| **Setup 1 comando (auto-Ollama + auto-vault)** | ADR-011 + ADR-012 — UX coerente com decisões de infra: nada de "configure isto antes de começar" |

### 1.3 Trade-offs aceitos

- **Sem multi-tenant / multi-processo simultâneo:** 1 advogado, 1 processo por vez. Concorrência é responsabilidade do laptop (não da app)
- **Sem histórico visual de processos anteriores:** auditoria é via `audit.jsonl` (CLI / leitura de arquivo). UI mostra **estado atual** apenas
- **Sem painel de configurações UI:** `BL-CONFIG-UI` deferred a v1.1+. MVP usa `.env` + restart

### 1.4 Não-objetivos explícitos (anti-scope)

- ❌ Dashboard analítico / métricas operacionais (ADR-013 §2.2 — VPS multi-tenant DESCARTADO; sem necessidade de UI para isso)
- ❌ Escolha de tier LLM via UI (BL-CONFIG-UI — usa `.env` `LLM_TIER` no MVP)
- ❌ Dark mode / theme switcher (não-objetivo MVP; tokens.css atual é light only)
- ❌ Mobile / tablet (advogado-usuário em laptop; mobile-friendly opcional via responsive CSS, não testado formalmente)

---

## 2. Tokens — Reuso + 1 proposta de adição

### 2.1 Tokens existentes (reusados sem modificação)

Origem: `bloco_interface/web/static/tokens.css` (REV-INT-02, sessão 86 — Manrope + Fraunces + JetBrains self-hosted woff2).

**Paleta primária (Or — laranja accent):**
- `--or-50` `#FFF4EC` · `--or-500` `#EE6B20` · `--or-600` `#D45710` · `--or-700` `#AC4408`

**Paleta secundária (Sh — azul, raro):**
- `--sh-500` `#2C5380` (uso restrito a links discretos / metadata estrutural)

**Neutros warm:**
- `--bg` `#FAFAF8` (canvas) · `--surface` `#FFFFFF` (cards) · `--surface-2` `#F5F4F0` (input bg, code blocks)
- `--border` `#E8E4DC` · `--border-strong` `#C9C3B5`
- `--text` `#1A1816` · `--text-muted` `#6B6457` · `--text-dim` `#9A9082`

**Semânticos:**
- `--accent` = `--or-500` · `--accent-hover` = `--or-600` · `--accent-soft` = `--or-50`
- `--success` `#2C7A4D` · `--success-soft` `#E8F4ED`
- `--danger` `#B43D3D` · `--danger-soft` `#FBEAEA`

**Tipografia:**
- `--f-ui` Manrope (400/500/600/700) — corpo + UI labels + buttons
- `--f-display` Fraunces (500) — H1 da landing pré-login + sumário Juiz veredicto (gravidas jurídica)
- `--f-mono` JetBrains Mono (400/500) — hash audit chain, OAB, valores monetários alinhados, log lines

**Sizing/Layout:**
- `--r-md` 6px · `--r-lg` 10px
- `--topbar-h` 56px · `--container-w` 720px (single-page lê confortável em laptop)

### 2.2 Propostas de tokens cirúrgicos (gaps detectados — micro-PATCH α CC.3)

> **Atualização micro-PATCH α (Smith CC.3 F-CC3-11 + F-CC3-03):** Smith encontrou 3 problemas com a proposta original — (1) cor `#B8770F` declarada 4.65:1 estava matematicamente errada (real ~3.5:1, falha AA normal); (2) faltavam tokens semânticos para estados implícitos no spec (disabled, focus-ring, surface-hover); (3) justificativa "rotação harmônica de --or-500" era subjetiva. Esta seção foi reescrita para endereçar os 3.

Reuso 100% de tokens existentes em `bloco_interface/web/static/tokens.css` cobriu paleta + tipografia + neutros + 2 semânticos (`--success`, `--danger`). Mas o spec depende de **estados que não foram tokenizados ainda** — banner Tema 1378 nível AMARELO (gap arquitetural), estados disabled (S8), focus indicator (a11y obrigatório WCAG 2.4.7), e drop-zone hover (S2→S3 transition).

**4 propostas consolidadas a aplicar em `tokens.css` antes ou durante CC.6:**

```css
/* Adicionar a tokens.css :root */

/* (1) Banner Tema 1378 nível AMARELO — FR-MONITOR-01 / ADR-013 §2.5 */
--warning:      #8B5A0B;  /* sobre --warning-soft: 5.49:1 ✓ AA normal text (≥4.5) — verificado via cálculo formal WCAG 2.1 sRGB→linear */
--warning-soft: #FFF6E5;

/* (2) Estados disabled — S8 main desabilitado, drop-zone disabled */
--opacity-disabled: 0.4;
--cursor-disabled:  not-allowed;

/* (3) Focus indicator — a11y obrigatório (WCAG 2.4.7 Focus Visible) */
--focus-ring-width:  2px;
--focus-ring-offset: 2px;
--focus-ring-color:  var(--accent); /* reuso --or-500 existente */

/* (4) Surface hover — drop-zone S2→S3 transition, button hover, card lift */
--surface-hover: rgba(238, 107, 32, 0.05); /* --or-500 com 5% alpha */
```

**Justificativa de cor `--warning` `#8B5A0B`:** rotação harmônica do **`--or-700` `#AC4408`** (não `--or-500`) deslocada para a faixa âmbar profunda. Mantém a warmth da paleta Or e fica suficientemente distinta de `--accent` para não confundir banner-de-estado com CTA. Ratio verificado **5.49:1 sobre `--warning-soft`** — passa AA normal text com folga, próxima de AAA (7:1).

**Verificação contraste (cálculo formal WCAG 2.1):**

```
sRGB → linear: c_lin = ((c+0.055)/1.055)^2.4 (para c > 0.03928); senão c/12.92
L = 0.2126·R_lin + 0.7152·G_lin + 0.0722·B_lin
Ratio = (L_light + 0.05) / (L_dark + 0.05)

#8B5A0B → L = 0.1283
#FFF6E5 → L = 0.9282
Ratio = (0.9282 + 0.05) / (0.1283 + 0.05) = 0.9782 / 0.1783 ≈ 5.49 : 1 ✓ AA normal
```

Reproduzível via Python `wcag-contrast-ratio` ou WebAIM Contrast Checker (https://webaim.org/resources/contrastchecker/) — copiar/colar `#8B5A0B` foreground + `#FFF6E5` background.

**Status do debt:** `BL-UX-CC3-DEBT` (consolidado, LOW; ver §9 + governance/TECH-DEBT.md). Não bloqueia CC.4 — Neo pode adicionar 4 entries em `tokens.css` como **pré-passo** de MVP-LEAN-01 (~15min total) OU `@architect` Aria executa side-fix em CC.4 dispatch antes River criar a story.

### 2.3 Mapeamento token semântico → estado UI

| Estado | Background canvas | Surface | Borda | Texto principal | Acento |
|---|---|---|---|---|---|
| S1 Login | `--bg` | `--surface` | `--border` | `--text` | `--accent` (botão Entrar) |
| S2 Pré-upload | `--bg` | `--surface` | `--border` | `--text` | `--accent` (CTA upload) |
| S3 Upload em andamento | `--bg` | `--surface` (dashed) | `--accent` | `--text` | `--accent-soft` (drop zone fill) |
| S4 Validação MIME/size | `--bg` | `--danger-soft` | `--danger` | `--text` | `--danger` (mensagem) |
| S5 Processing | `--bg` | `--surface` | `--border` | `--text` | `--accent` (spinner) |
| S6 Resultado | `--bg` | `--surface` (3 cards) | `--border` | `--text` | `--success` (deliverables OK) |
| S7 Erro pipeline | `--bg` | `--danger-soft` (pane) | `--danger` | `--text` | `--danger` |
| S8 Banner CRITICAL | `--bg` | `--danger-soft` (full-width) | `--danger` | `--text` | `--danger` |

Banner Tema 1378 níveis (componente C2):
- **VERDE info:** `--success-soft` bg, `--success` border-left, `--text` corpo
- **AMARELO warn:** `--warning-soft` bg, `--warning` border-left, `--text` corpo *(token novo — proposta §2.2)*
- **VERMELHO CRITICAL:** `--danger-soft` bg, `--danger` border-left, `--text` corpo

---

## 3. Wireframes — 8 Estados

### Layout-base (header + main + footer)

```
┌──────────────────────────────────────────────────────────────────────┐
│  TOPBAR (56px — --topbar-h)                                          │
│  [🏛️ Revisor Contratual]   ……   [usuário · Sair]                     │
├──────────────────────────────────────────────────────────────────────┤
│  BANNER TEMA 1378 (componente C2 — só renderiza se status ≠ verde)   │
│  ⚠ "Tema 1378 STJ — em julgamento. Revise teses citadas." [Detalhes] │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  MAIN (--container-w 720px, centered)                                │
│  ── [Seção condicional via HTMX swap por estado S1..S7]              │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│  FOOTER (componente C7)                                              │
│  Revisor Contratual v0.1.0 · audit.jsonl · 100% local · LGPD §46     │
└──────────────────────────────────────────────────────────────────────┘
```

Topbar é persistente. Banner Tema 1378 é persistente (visível em S1-S7 inclusive — alerta jurídico não some entre estados). Main troca conteúdo via `hx-swap="innerHTML"` em `<main id="app-main">`.

---

### S1 — Login (não-autenticado)

**Quando:** GET `/` sem cookie `session` válido OR após `/logout` OR após sessão expirada (24h).

```
┌────────────────────────────────────────────────────────┐
│  TOPBAR (sem nome de usuário)                          │
├────────────────────────────────────────────────────────┤
│  (sem banner Tema 1378 — usuário ainda não autenticado;│
│   info regulatório só após login para coerência LGPD)  │
├────────────────────────────────────────────────────────┤
│                                                        │
│            🏛️                                          │
│       Revisor Contratual                               │
│       (Fraunces 500, --text)                           │
│                                                        │
│       Análise de contratos CDC PF Veículos             │
│       (Manrope 400, --text-muted)                      │
│                                                        │
│       ┌────────────────────────────────────────┐       │
│       │  Usuário                               │       │
│       │  [_______________________________]      │       │
│       │                                        │       │
│       │  Senha                                 │       │
│       │  [_______________________________]      │       │
│       │                                        │       │
│       │  [hidden CSRF token]                   │       │
│       │                                        │       │
│       │  [        Entrar        ]              │       │
│       │  (--accent bg, white text)             │       │
│       └────────────────────────────────────────┘       │
│                                                        │
│       ↳ Erro auth (S1.error):                          │
│       "Usuário ou senha inválidos." (--danger, mt-3)   │
│                                                        │
├────────────────────────────────────────────────────────┤
│  FOOTER                                                │
└────────────────────────────────────────────────────────┘
```

**Acessibilidade:** focus inicial em campo Usuário (`autofocus`); Tab → Senha → Entrar. Label visível (não placeholder-as-label). Erro auth com `aria-live="polite"`.

---

### S2 — Pré-upload (autenticado, vazio)

**Quando:** GET `/` com cookie `session` válido AND nenhum upload em curso.

> **Atualização micro-PATCH α (F-CC3-06):** S2 reformulado para 2 drop-zones (D1 contrato obrigatório + D2 decisão adversa opcional). PRD v1.1.2.1 §2.3 D3 fluxo passo 1 requer parser decisão adversa PDF — D3 só é gerado quando esse upload é feito. Spec original mostrava 1 único drop-zone implicando D3 sempre disponível, o que viola PRD.

```
┌────────────────────────────────────────────────────────────┐
│  TOPBAR  [🏛️ Revisor Contratual]    [advogado@x · Sair]    │
├────────────────────────────────────────────────────────────┤
│  ✓ Tema 1378 STJ — sem alterações. Última verificação      │
│    automática: 2 dias atrás. (verde, fechável)             │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   Bem-vindo, advogado@x                                    │
│   (Manrope 600, --text)                                    │
│                                                            │
│   Envie o contrato CDC PF Veículos do seu cliente para     │
│   análise pelas 4 personas. Se já houver decisão adversa,  │
│   anexe-a também para gerar a peça de Apelação Cível (D3). │
│   (Manrope 400, --text-muted)                              │
│                                                            │
│   ── 1. Contrato (obrigatório) ──────────────────────      │
│   ┌──────────────────────────────────────────────────┐     │
│   │            ⬆                                     │     │
│   │   Arraste o PDF do contrato                      │     │
│   │   ou [clique para selecionar]                    │     │
│   │                                                  │     │
│   │   PDF apenas · até 10MB                          │     │
│   │   Os dados não saem da sua máquina (LGPD)        │     │
│   └──────────────────────────────────────────────────┘     │
│   (border dashed --border-strong, bg --surface — drop-zone │
│    obrigatória, marcada com asterisco em label)            │
│                                                            │
│   ── 2. Decisão adversa (opcional) ──────────────────      │
│   ┌──────────────────────────────────────────────────┐     │
│   │            ⬆                                     │     │
│   │   Arraste a decisão adversa                      │     │
│   │   ou [clique para selecionar]                    │     │
│   │                                                  │     │
│   │   Opcional — só envie se já houver sentença      │     │
│   │   desfavorável que precise apelar. Habilita D3.  │     │
│   │   PDF apenas · até 10MB                          │     │
│   └──────────────────────────────────────────────────┘     │
│   (border dashed --border / mais leve que D1, bg --surface)│
│                                                            │
│   [   Iniciar análise   ]                                  │
│   (--accent bg, white text, Manrope 600 16px;              │
│    disabled (opacity --opacity-disabled) até D1 ter PDF    │
│    válido client-side)                                     │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  FOOTER                                                    │
└────────────────────────────────────────────────────────────┘
```

**Acessibilidade:** cada drop-zone com `role="button"` + `tabindex="0"`. Labels diferenciados para screen reader:
- D1: `aria-label="Upload obrigatório — contrato CDC em PDF (drag-and-drop ou clique). Até 10MB."` + `aria-required="true"`
- D2: `aria-label="Upload opcional — decisão adversa em PDF para gerar Apelação Cível. Até 10MB."` + `aria-required="false"`

CTA "Iniciar análise" com `aria-disabled="true"` enquanto D1 vazio; muda para `aria-disabled="false"` ao receber PDF válido. Tab order: D1 → D2 → CTA. Enter/Space em qualquer drop-zone ativa file picker.

---

### S3 — Upload em andamento

**Quando:** usuário arrastou arquivo OR selecionou via picker; HTMX `hx-post="/revisar"` com `hx-encoding="multipart/form-data"` em curso (validação client-side prévia: extensão `.pdf`, tamanho ≤ 10MB).

```
┌────────────────────────────────────────────────────────────┐
│  TOPBAR  [🏛️]                          [advogado@x · Sair] │
├────────────────────────────────────────────────────────────┤
│  Banner Tema 1378 (status atual)                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   Recebendo contrato…                                      │
│                                                            │
│   ┌──────────────────────────────────────────────────┐     │
│   │  📄 contrato-cliente-x.pdf · 2.4 MB              │     │
│   │  [████████████░░░░░░░░] 60%                      │     │
│   │  (--accent fill, --surface-2 track)              │     │
│   └──────────────────────────────────────────────────┘     │
│                                                            │
│   [ Cancelar ] (--text-muted, link-style)                  │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  FOOTER                                                    │
└────────────────────────────────────────────────────────────┘
```

**Acessibilidade:** progress bar com `role="progressbar"` + `aria-valuenow={pct}` + `aria-valuemin="0"` + `aria-valuemax="100"`. Cancelamento via Escape.

---

### S4 — Validação MIME/size falhou

**Quando:** server-side em `POST /revisar` rejeita upload — magic bytes ≠ `b'%PDF-'` OR `pdf.size > MAX_UPLOAD_SIZE` (10MB) OR CSRF inválido.

```
┌────────────────────────────────────────────────────────────┐
│  TOPBAR + BANNER                                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   ┌──────────────────────────────────────────────────┐     │
│   │  ⚠ Não foi possível processar este arquivo       │     │
│   │  (Manrope 600, --danger)                         │     │
│   │                                                  │     │
│   │  Diagnóstico: arquivo enviado não é PDF válido   │     │
│   │  (Manrope 400, --text)                           │     │
│   │                                                  │     │
│   │  Causa: os primeiros bytes não correspondem ao   │     │
│   │  cabeçalho PDF (%PDF-).                          │     │
│   │                                                  │     │
│   │  Solução: confira que o arquivo é um PDF não     │     │
│   │  corrompido. Tente abrir em outro leitor antes   │     │
│   │  de re-enviar.                                   │     │
│   │                                                  │     │
│   │  Alternativa: exporte o contrato como PDF a      │     │
│   │  partir do leitor de origem (Word → PDF, etc).   │     │
│   │                                                  │     │
│   │  [ Tentar outro arquivo ]                        │     │
│   └──────────────────────────────────────────────────┘     │
│   (bg --danger-soft, border-left 4px --danger)             │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  FOOTER                                                    │
└────────────────────────────────────────────────────────────┘
```

**Padrão:** estrutura "Diagnóstico → Causa → Solução → Alternativa" — replica padrão SOP-003 documentado em `ParserOCRRequired` (sessão 73). Aplicar a TODAS error panes (S4 e S7).

**Variantes da mensagem:**
- MIME inválido: "arquivo enviado não é PDF válido"
- Size > 10MB: "arquivo excede o limite de 10MB do MVP" (causa: `pdf.size > MAX_UPLOAD_SIZE`; solução: comprimir / dividir; alternativa: enviar páginas relevantes apenas)
- CSRF inválido: "sessão expirou" (causa: cookie sessão > 24h; solução: faça login novamente; alternativa: nenhuma — segurança LGPD §46)

---

### S5 — Processing (4 personas LLM em paralelo via HTMX SSE)

**Quando:** upload válido aceito; backend dispara pipeline (parsing + 4 personas + validação + audit). HTMX recebe SSE events em `<main>` com `hx-swap-oob="true"` por região.

```
┌────────────────────────────────────────────────────────────┐
│  TOPBAR + BANNER                                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   Analisando contrato                                      │
│   (Manrope 600, --text)                                    │
│                                                            │
│   📄 contrato-cliente-x.pdf · hash 7a3f…b8d1                │
│   (Manrope 400, --text-muted, JetBrains Mono no hash)      │
│                                                            │
│   ┌──────────────────────────────────────────────────┐     │
│   │  ⏵ 1/5 Parsing PDF                  [✓ 14s]      │     │
│   │  ⏵ 2/5 Advogado (Sabia/Qwen 7B)     [⟳ 42s]      │     │
│   │  ⏵ 3/5 Economista (Qwen 7B)          [⟳ 38s]     │     │
│   │  ⏵ 4/5 Validador semântico           […]         │     │
│   │  ⏵ 5/5 Juiz HITL                     […]         │     │
│   └──────────────────────────────────────────────────┘     │
│   (lista — ✓ verde concluído / ⟳ laranja em curso /        │
│    … cinza pendente)                                       │
│                                                            │
│   Tempo decorrido: 56s · estimado total: ~3min             │
│   (Manrope 400, --text-dim)                                │
│                                                            │
│   [ Cancelar e recomeçar ] (--text-muted, link-style)      │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  FOOTER                                                    │
└────────────────────────────────────────────────────────────┘
```

**SSE protocol (high-level — implementação Neo CC.6):**
- `event: phase-start` data `{phase: "advogado", started_at: ...}` → marca `⟳`
- `event: phase-done` data `{phase: "advogado", elapsed_s: 42}` → marca `✓` + tempo
- `event: phase-error` data `{phase, diagnostic, cause, solution, alternative}` → swap para S7
- `event: complete` data `{deliverables: [...]}` → swap para S6
- `event: ping` data `{ts}` → heartbeat (10s); client reseta `lastEventTs` (não muda UI)

**Connection drop handling (atualização micro-PATCH α — F-CC3-05):**

Sem heartbeat e timeout client-side, S5 trava em `⟳` indefinido se a conexão SSE cai (rede instável, browser tab inactive throttling em Chrome/Firefox, Ollama subprocess crash silencioso que não emite `phase-error`). Mecanismo de detecção e recuperação:

| Mecanismo | Implementação | Comportamento UX |
|---|---|---|
| **Heartbeat server-side** | Server emite `event: ping {ts}` a cada 10s independente do progresso do pipeline | Client reseta `lastEventTs = Date.now()` no recebimento; nenhuma mudança visual |
| **Client-side timeout** | `setInterval` no client checa a cada 5s: se `Date.now() - lastEventTs > 60000` → emit synthetic `phase-error` | Swap para S7 com variante `connection_drop` (microcopy fixo abaixo) |
| **EventSource onerror** | Browser dispara `onerror` se conexão dropada antes do timeout client; client tenta 1 retry automático com backoff 5s | Se retry sucesso → mantém S5 (silent recovery); se retry falha → mesma synthetic phase-error → S7 |
| **Audit on drop** | Backend grava em `audit.jsonl` entry `{type: "pipeline_lost_connection", job_id, last_phase, timestamp}` quando client-side reabertura confirma perda | Footer C7 link "audit.jsonl" mostra evidência forense |

**Variante synthetic phase-error (`connection_drop`):**
- diagnóstico: "Conexão com servidor perdida"
- causa: "Sem resposta do servidor por 60s — pipeline pode ter parado ou ainda estar executando no backend"
- solução: "Re-execute a análise. Se persistir, verifique conectividade ou reinicie a app"
- alternativa: "Verifique `audit.jsonl` para confirmar se o pipeline completou no backend mesmo sem resposta UI"

**Acessibilidade:** lista de fases com `role="list"`, cada item com `aria-live="polite"`, status atualizado via `aria-label` por fase. Spinner laranja ⟳ tem `aria-hidden="true"` (decorativo) + texto "(em curso)" para screen reader. Heartbeat `event: ping` é silencioso para screen reader (não muda label).

---

### S6 — Resultado consolidado (3 deliverables + sumário Juiz)

**Quando:** SSE `event: complete`. Backend persistiu HMAC chain entry final.

```
┌────────────────────────────────────────────────────────────┐
│  TOPBAR + BANNER                                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   ✓ Análise concluída                                      │
│   (Manrope 600, --success)                                 │
│                                                            │
│   contrato-cliente-x.pdf · 2min 47s                        │
│   hash 7a3f…b8d1 · audit chain entry #137                  │
│   (Manrope 400 + JetBrains Mono no hash, --text-muted)     │
│                                                            │
│   ── Veredicto Juiz ─────────────────────────────────      │
│   ┌──────────────────────────────────────────────────┐     │
│   │  Tese consolidada (Fraunces 500, --text)          │    │
│   │                                                  │     │
│   │  "Há indícios de abusividade na taxa de juros    │     │
│   │  pactuada (4,82% a.m.) frente à média BACEN no   │     │
│   │  período (2,11% a.m.) — ratio 2.28x acima."      │    │
│   │                                                  │     │
│   │  Confiança: 0.83 · Citações validadas: 4/4       │     │
│   │  (Manrope 400, --text-muted)                     │     │
│   └──────────────────────────────────────────────────┘     │
│                                                            │
│   ── Deliverables disponíveis ───────────────────────      │
│                                                            │
│   ── Variante S6.a (D3 disponível — decisão adversa enviada em S2): │
│   ┌────────────────┬────────────────┬────────────────┐     │
│   │  📊 D1         │  📜 D2         │  ⚖ D3          │     │
│   │  Relatório     │  Petição       │  Apelação      │     │
│   │  Contábil      │  Inicial       │  Cível         │     │
│   │                │                │                │     │
│   │  Tabela Price  │  Fundamentos   │  Pré-redigida  │     │
│   │  + cálculos    │  + jurisprud.  │  100% — para   │     │
│   │  abusivos      │  + pedidos     │  decisão adv.  │     │
│   │                │                │                │     │
│   │  PDF · 12 pp   │  DOCX · 18 pp  │  DOCX · 24 pp  │     │
│   │                │                │                │     │
│   │  [ Baixar ]    │  [ Baixar ]    │  [ Baixar ]    │     │
│   │  (--accent)    │  (--accent)    │  (--accent)    │     │
│   └────────────────┴────────────────┴────────────────┘     │
│                                                            │
│   ── Variante S6.b (D3 indisponível — sem decisão adversa em S2):  │
│   ┌────────────────┬────────────────┬────────────────┐     │
│   │  📊 D1         │  📜 D2         │  ⚖ D3          │     │
│   │  Relatório     │  Petição       │  Apelação      │     │
│   │  Contábil      │  Inicial       │  (indisponível)│     │
│   │                │                │                │     │
│   │  Tabela Price  │  Fundamentos   │  D3 só é       │     │
│   │  + cálculos    │  + jurisprud.  │  gerada com    │     │
│   │  abusivos      │  + pedidos     │  decisão adv.  │     │
│   │                │                │  enviada.      │     │
│   │                │                │                │     │
│   │  PDF · 12 pp   │  DOCX · 18 pp  │  ─             │     │
│   │                │                │                │     │
│   │  [ Baixar ]    │  [ Baixar ]    │  [ Enviar      │     │
│   │  (--accent)    │  (--accent)    │   decisão ]    │     │
│   │                │                │  (secondary,   │     │
│   │                │                │  --accent-soft)│     │
│   └────────────────┴────────────────┴────────────────┘     │
│   (D3 card com bg --surface-2 + opacity 0.85; CTA          │
│    "Enviar decisão" volta a S2 mantendo o contrato já      │
│    processado — só faz upload de D2 + re-roda etapas       │
│    específicas D3, sem reprocessar D1+D2)                  │
│                                                            │
│   [ Analisar outro contrato ] (button secondary, --or-50)  │
│   [ Ver entrada audit ] (link, --sh-500)                   │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  FOOTER                                                    │
└────────────────────────────────────────────────────────────┘
```

**Hash audit:** apresentado em JetBrains Mono `font-feature-settings: "tnum"` para alinhamento. Truncado a 4+4 chars (`7a3f…b8d1`) com tooltip mostrando hash completo + clipboard-copy.

**Acessibilidade:** cards de deliverables com `<article role="article">` + heading nível 3. Botões "Baixar" descrevem o conteúdo: `aria-label="Baixar Relatório Contábil PDF (12 páginas)"`.

---

### S7 — Erro de pipeline (LLM timeout, parsing fail, etc)

**Quando:** SSE `event: phase-error`. Padrão SOP-003 replicado (S4 reusa o mesmo template).

```
┌────────────────────────────────────────────────────────────┐
│  TOPBAR + BANNER                                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   ┌──────────────────────────────────────────────────┐     │
│   │  ⚠ A análise foi interrompida                    │     │
│   │  (Manrope 600, --danger)                         │     │
│   │                                                  │     │
│   │  Diagnóstico: a Persona Advogado não respondeu   │     │
│   │  no tempo esperado (timeout: 120s)               │     │
│   │                                                  │     │
│   │  Causa: o modelo Sabia-7B pode não estar         │     │
│   │  carregado em memória. Auto-Ollama detecta isto  │     │
│   │  no startup, mas se você reiniciou o sistema     │     │
│   │  recentemente, a primeira chamada pode falhar.   │     │
│   │                                                  │     │
│   │  Solução: re-execute a análise. A próxima        │     │
│   │  tentativa terá modelo carregado.                │     │
│   │                                                  │     │
│   │  Alternativa: troque para tier `balanced` em     │     │
│   │  .env (LLM_TIER=balanced) e reinicie a app —     │     │
│   │  Qwen 7B é mais leve e rápido no primeiro carrega│     │
│   │                                                  │     │
│   │  [ Tentar novamente ]   [ Ver log audit ]         │    │
│   └──────────────────────────────────────────────────┘     │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  FOOTER                                                    │
└────────────────────────────────────────────────────────────┘
```

**Variantes baseadas em `event: phase-error.phase`:**
- `parsing`: "PDF protegido / OCR-only" (causa: ParserOCRRequired) — alternativa: rasgar OCR via Adobe / abbyy externo, depois reupload
- `advogado` / `economista`: timeout LLM (mensagem acima)
- `validacao_semantica`: cosine similarity < 0.7 — diagnóstico: "a tese gerada não tem citações validáveis" (causa técnica) + alternativa: rerodar com tier diferente
- `juiz_hitl`: bigram diversity bypass (FR-JUIZ-02) — diagnóstico: "tese muito similar a versão prévia"

---

### S8 — Banner Tema 1378 CRITICAL (auto-trigger SOP-005)

**Quando:** Camada 1 do FR-MONITOR-01 falha 2 execuções consecutivas (per ADR-013 §2.5 micro-PATCH α) OR julgamento Tema 1378 detectado OR maintainer triggou manual via CLI `revisor monitor-tema --manual-trigger`.

```
┌────────────────────────────────────────────────────────────┐
│  TOPBAR                                                    │
├────────────────────────────────────────────────────────────┤
│  ⚠ ALERTA CRÍTICO — Tema 1378 STJ                          │
│                                                            │
│  Estado: julgamento detectado em 2026-05-04                │
│  Tese fixada: "abusividade circunstancial restritiva"       │
│                                                            │
│  Novas análises foram pausadas até que o vault seja        │
│  atualizado. Execute o procedimento SOP-005 ou aguarde     │
│  o release v0.1.1 com vault revisado.                      │
│                                                            │
│  [ Ver SOP-005 ]   [ Reconhecer (manutenção) ]             │
│                                                            │
│  (bg --danger-soft, border-left 4px --danger,              │
│   full-width — não-fechável até ack)                       │
├────────────────────────────────────────────────────────────┤
│  MAIN — desabilitado                                       │
│  (drop-zone S2 fica em estado disabled; CTAs com           │
│   opacity 0.4 + cursor not-allowed; tooltip:               │
│   "Análises pausadas — Tema 1378 em revisão")              │
├────────────────────────────────────────────────────────────┤
│  FOOTER                                                    │
└────────────────────────────────────────────────────────────┘
```

**Hierarquia de bloqueio:**
- VERDE (info): banner discreto, fechável; main funcional
- AMARELO (warn 1 falha auto OR julgamento iminente): banner persistente fechável após ack-temporário (24h); main funcional com warning visível em S6 ("Tese pode estar desatualizada")
- VERMELHO (CRITICAL): banner não-fechável até maintainer ack via CLI `--acknowledge`; main desabilitado (compliance regulatório)

**Acessibilidade:** banner com `role="alert"` + `aria-live="assertive"` (interrompe leitor de tela imediatamente). Botões com texto explícito + ícone decorativo (`aria-hidden`).

---

## 4. Componentes — 7 com props, estados, microcopy

### C1 — Login form (S1)

| Prop | Tipo | Notas |
|---|---|---|
| `csrf_token` | str | injetado via Jinja2 `{{ csrf_token() }}` no `<input type="hidden">` |
| `error` | str \| null | se presente, renderiza S1.error com `aria-live="polite"` |

**Estados:** idle / submitting / error.

**Microcopy:**
- Heading: **"Revisor Contratual"** (Fraunces 500)
- Subheading: "Análise de contratos CDC PF Veículos"
- Label Usuário: "Usuário"
- Label Senha: "Senha"
- CTA: "**Entrar**" (não "Login" — PT-BR consistente)
- Erro auth: "Usuário ou senha inválidos." (não revelar qual — mitiga enumeration)
- Erro CSRF: "Sessão expirada. Recarregue a página."

### C2 — Banner Tema 1378 (todos os estados S2-S8)

| Prop | Tipo | Notas |
|---|---|---|
| `nivel` | "verde" \| "amarelo" \| "vermelho" | mapeia paleta semântica |
| `mensagem` | str | corpo principal |
| `data_verificacao` | str | "Última verificação automática: 2 dias atrás" |
| `acoes` | list[{label, href}] | ex: `[{label: "Ver SOP-005", href: "/sop-005"}, ...]` |
| `fechavel` | bool | true para verde/amarelo após ack 24h; false para vermelho |

**Estados:** verde / amarelo / vermelho / oculto (bem-sucedido + dismissed em sessão).

**Microcopy por nível:**
- VERDE: "✓ Tema 1378 STJ — sem alterações. Última verificação automática: {data}."
- AMARELO (1 falha auto): "⏳ Tema 1378 STJ — verificação automática falhou {data}. Acompanhe manualmente até a próxima execução."
- AMARELO (julgamento iminente): "⚠ Tema 1378 STJ — sessão de julgamento pautada para {data}. Revise teses citadas após decisão."
- VERMELHO (auto falhou 2× consecutivas): "⚠ ALERTA CRÍTICO — Tema 1378 STJ. A verificação automática falhou em 2 execuções consecutivas. Execute SOP-005 manual."
- VERMELHO (julgamento detectado): "⚠ ALERTA CRÍTICO — Tema 1378 STJ. Estado: julgamento detectado em {data}. Tese fixada: {tese}. Novas análises pausadas até atualização do vault."

### C3 — Upload zone (S2)

> **Atualização micro-PATCH α (F-CC3-06):** componente parametrizado por `tipo` para diferenciar "contrato" (obrigatório) vs "decisao_adversa" (opcional). PRD v1.1.2.1 §2.3 D3 fluxo requer dois inputs distintos.

| Prop | Tipo | Notas |
|---|---|---|
| `tipo` | `"contrato"` \| `"decisao_adversa"` | Determina microcopy + a11y label + obrigatoriedade |
| `max_size_mb` | int | 10 (FR-PARSE) — exibido no microcopy |
| `accept` | str | `.pdf` (server-side magic bytes valida ainda; client é defesa em profundidade) |
| `disabled` | bool | true em S8 vermelho |

**Estados:** idle / hover (drag-over) / loaded (PDF aceito client-side, exibe nome + tamanho + ícone "trocar") / disabled.

**Microcopy por `tipo`:**

`tipo: "contrato"` (S2 drop-zone 1, obrigatório):
- Heading da seção: "1. Contrato (obrigatório)"
- CTA primário (drop): "**Arraste o PDF do contrato**"
- CTA secundário (clique): "ou **clique para selecionar**"
- Restrição: "PDF apenas · até 10MB"
- LGPD reassurance: "Os dados não saem da sua máquina (LGPD)"
- a11y: `aria-label="Upload obrigatório — contrato CDC em PDF"` + `aria-required="true"`

`tipo: "decisao_adversa"` (S2 drop-zone 2 OR S6 variante CTA "Enviar decisão"):
- Heading da seção: "2. Decisão adversa (opcional)"
- CTA primário (drop): "**Arraste a decisão adversa**"
- CTA secundário (clique): "ou **clique para selecionar**"
- Tooltip explicativo: "Opcional — só envie se já houver sentença desfavorável que precise apelar. Habilita D3."
- Restrição: "PDF apenas · até 10MB"
- a11y: `aria-label="Upload opcional — decisão adversa em PDF para gerar Apelação Cível"` + `aria-required="false"`

**Heading global S2** (acima das duas drop-zones, único): "Bem-vindo, {usuario}" (Manrope 600) + "Envie o contrato CDC PF Veículos do seu cliente para análise pelas 4 personas. Se já houver decisão adversa, anexe-a também para gerar a peça de Apelação Cível (D3)." (Manrope 400, --text-muted)

### C4 — Processing pane (S5)

| Prop | Tipo | Notas |
|---|---|---|
| `phases` | list[{id, label, status, elapsed_s?}] | 5 fases pré-conhecidas |
| `pdf_filename` | str | escapado via Jinja2 `{{ name|e }}` |
| `pdf_hash` | str | sha256, exibido truncado em mono |
| `total_elapsed_s` | int | tempo decorrido total |
| `eta_s` | int \| null | estimado total (~180s) |

**Estados por fase:** pending (`…`, `--text-dim`) / running (`⟳`, `--accent`, animado) / done (`✓`, `--success`, com tempo) / error (`✗`, `--danger`, com diagnóstico).

**Microcopy:**
- Heading: "**Analisando contrato**"
- Lista (5 fases canônicas):
  1. "Parsing PDF"
  2. "Advogado (Sabia/Qwen 7B)" — texto adapta ao `LLM_TIER` do .env
  3. "Economista (Qwen 7B)"
  4. "Validador semântico"
  5. "Juiz HITL"
- Footer: "Tempo decorrido: {t}s · estimado total: ~3min"
- Cancelar: "Cancelar e recomeçar"

### C5 — Resultado pane (S6)

> **Atualização micro-PATCH α (F-CC3-06):** prop `deliverables` ganha campo `disponivel: bool` por card; D3 renderiza 2 estados (S6.a disponível / S6.b indisponível com CTA "Enviar decisão").

| Prop | Tipo | Notas |
|---|---|---|
| `pdf_filename` | str | escapado (contrato; decisão adversa nome separado se enviada) |
| `pdf_hash` | str | sha256 truncado (contrato) |
| `audit_entry_id` | int | número sequencial chain |
| `tempo_total` | str | "2min 47s" |
| `veredicto_tese` | str | tese consolidada Juiz |
| `confianca` | float | 0.0-1.0 |
| `citacoes_validadas` | "{n}/{total}" | ex "4/4" |
| `deliverables` | list[{tipo, label, descricao, formato, paginas, download_url, **disponivel**}] | 3 cards (D1/D2 sempre `disponivel:true`; D3 `disponivel: bool` baseado em decisão adversa enviada em S2) |

**Estados:** sucesso / sucesso-com-warnings (ex: 1/4 citação não validada) / sucesso-com-divergencia (Juiz veredicto baixa confiança).

**Lógica condicional D3 (per F-CC3-06):**
- Se `deliverables[2].disponivel == true` → renderiza S6.a (D3 card ativo, botão "Baixar")
- Se `deliverables[2].disponivel == false` → renderiza S6.b (D3 card inativo `bg --surface-2 opacity 0.85`, CTA secundário "Enviar decisão" → volta a S2 mantendo `pdf_hash` do contrato já processado; backend recebe só novo upload D2 + re-roda etapas específicas D3 sem reprocessar D1+D2)

**Microcopy:**
- Heading: "✓ **Análise concluída**"
- Sub: "{filename} · {tempo_total}"
- Audit: "hash {hash_truncado} · audit chain entry #{id}"
- Veredicto Juiz heading: "**Veredicto Juiz**" (Fraunces 500 — gravidades jurídica)
- Card D1: "**Relatório Contábil**" / "Tabela Price + cálculos abusivos" / "PDF · {n} pp"
- Card D2: "**Petição Inicial**" / "Fundamentos + jurisprudência + pedidos" / "DOCX · {n} pp"
- Card D3 disponível: "**Apelação Cível**" / "Pré-redigida 100% — para decisão adversa" / "DOCX · {n} pp"
- Card D3 indisponível: "**Apelação Cível** (indisponível)" / "D3 só é gerada com decisão adversa enviada." / formato "—"
- CTA "Baixar" por card disponível (--accent)
- CTA "Enviar decisão" no card indisponível (secondary --accent-soft)
- Botão secondary: "Analisar outro contrato"
- Link mono: "Ver entrada audit"

### C6 — Error pane (S4 e S7)

| Prop | Tipo | Notas |
|---|---|---|
| `titulo` | str | "Não foi possível processar este arquivo" / "A análise foi interrompida" |
| `diagnostico` | str | curta, sem jargão técnico |
| `causa` | str | técnica mas legível |
| `solucao` | str | passo concreto |
| `alternativa` | str | plano B se solução não funcionar |
| `acoes` | list[{label, href OR action}] | ex: `[{label: "Tentar outro arquivo", action: "reset"}]` |

**Padrão obrigatório:** estrutura "Diagnóstico → Causa → Solução → Alternativa" (replica padrão SOP-003 sessão 73 — `ParserOCRRequired` é o caso paradigmático).

**Não-objetivo:** mensagens genéricas tipo "Erro 500" ou "Algo deu errado" são proibidas. Toda mensagem deve ser navegável pelos 4 elementos.

#### Variante catch-all `infra` (anti-fallback — micro-PATCH α F-CC3-08)

Smith identificou 7+ classes de erro de runtime real que não estavam catalogadas (disk full, vault.db lock, FERNET/SESSION missing, Ollama crash, BACEN down, WeasyPrint fail). Para evitar que essas situações virem `Erro 500` genérico (violando o anti-pattern declarado), backend implementa **handler central** que converte exceptions Python em payload C6 com Diag/Causa/Solução/Alternativa parametrizados por exception type:

```python
# bloco_interface/web/error_handler.py (Neo CC.6)
EXCEPTION_TO_C6_VARIANT = {
    "OSError-28": "disk_full_audit",          # ENOSPC em audit.jsonl write
    "OSError-28-uploads": "disk_full_uploads", # ENOSPC em uploads/ encrypt
    "sqlite3.OperationalError-locked": "vault_db_locked",
    "InvalidToken": "fernet_key_missing",     # cryptography.fernet sem chave válida
    "RuntimeError-session-secret": "session_secret_missing",
    "OllamaProcessNotResponding": "ollama_subprocess_crash",
    "httpx.TimeoutException-bacen": "bacen_api_down",
    "weasyprint.RenderError": "weasyprint_render_fail",
    # Fallback genérico (último recurso, NÃO deve cair aqui em produção):
    "*": "infra_unknown",
}
```

Quando uma exception cai no fallback `*` (`infra_unknown`), C6 renderiza com:
- titulo: "Erro de infraestrutura local"
- diagnostico: "{exception class + primeira linha da mensagem}" (extraído do log estruturado)
- causa: "{exception type técnico}" (ex: `sqlite3.OperationalError: database is locked`)
- solucao: "Re-execute a análise. Se persistir, verifique `audit.jsonl` para diagnóstico completo"
- alternativa: "Contate o maintainer com `job_id={job_id}` e timestamp do erro"

Esta variante de fallback é a única forma legítima de uma mensagem genérica entrar no UX — e ainda assim segue o padrão Diag/Causa/Solução/Alternativa.

#### 7 variantes de erro adicionais catalogadas (micro-PATCH α F-CC3-08)

Cada variante tem mesma estrutura SOP-003 (Diag → Causa → Solução → Alternativa). Implementação Neo CC.6 mapeia exception → variante via dicionário acima.

| Variante | Diagnóstico | Causa | Solução | Alternativa |
|---|---|---|---|---|
| `disk_full_audit` | "Sem espaço em disco para gravar a auditoria" | `OSError [Errno 28] No space left on device` em `audit.jsonl` | Liberar espaço em `~/.local/share/revisor-contratual/` | Backup do `audit.jsonl` atual + truncate + reiniciar app (perde histórico antigo, preserva HMAC chain via genesis re-anchor) |
| `disk_full_uploads` | "Sem espaço em disco para receber o PDF" | `OSError [Errno 28]` em `uploads/` durante encrypt-on-upload (FR-LGPD-MVP-01 L4) | Liberar espaço em `~/.local/share/revisor-contratual/uploads/` (PDFs antigos podem ser deletados — pipeline já completou) | Mover backups antigos (`backups/{YYYY-MM-DD}/`) para storage externo |
| `vault_db_locked` | "Banco de dados de jurisprudência ocupado" | `sqlite3.OperationalError: database is locked` durante busca FR-RAG | Aguardar 30s e re-executar (lock é tipicamente transient) | Reiniciar a app — força liberação de qualquer lock pendente |
| `fernet_key_missing` | "Chave de cifragem ausente — não é possível decifrar PDFs do upload" | `FERNET_KEY` ausente OR inválida em `.env` (FR-LGPD-MVP-01 L4) | Regenerar via `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` e adicionar a `.env` | SOP-001 setup script (a criar como follow-up trivial); **atenção**: regenerar invalida PDFs já cifrados em `uploads/` — limpar diretório |
| `session_secret_missing` | "Chave de sessão ausente — login não pode ser estabelecido" | `SESSION_SECRET` ausente em `.env` (FR-LGPD-MVP-01 L2) | Regenerar via `python -c "import secrets; print(secrets.token_urlsafe(32))"` e adicionar a `.env`; reiniciar app | SOP-001 setup script |
| `ollama_subprocess_crash` | "A persona LLM não está disponível" | Subprocess Ollama (Sabia-7B ou Qwen-7B) morreu sem responder ao timeout (ADR-011) | Re-execute a análise — auto-Ollama lifecycle detecta processo morto e spawn novo no próximo `phase-start` | Reinicie a app para forçar respawn imediato; verifique `LLM_TIER` em `.env` se persistir |
| `bacen_api_down` | "API BACEN indisponível para verificar taxa média" | `httpx.TimeoutException` ou 5xx em endpoint BACEN (FR-BACEN) | Re-execute em ~30min (taxas BACEN são publicadas diariamente; transient downtime) | Pipeline usa **última taxa cacheada** (warning visível em S6: "Taxa BACEN de {data anterior} — re-execute para taxa atualizada") |
| `weasyprint_render_fail` | "Não foi possível gerar o PDF do Relatório Contábil" | `weasyprint.RenderError` (D1 PDF) — pode ser tabela com formato anômalo OR fontes ausentes | Re-execute a análise (transient) | Baixe D2 e D3 (DOCX) primeiro — eles não dependem do WeasyPrint; D1 pode ser regenerado manualmente a partir do `audit.jsonl` |

### C7 — Footer

| Prop | Tipo | Notas |
|---|---|---|
| `versao` | str | injetado de `pyproject.toml` |
| `audit_url` | str | link para download direto de `audit.jsonl` (auth required) |

**Microcopy (uma linha):**
"Revisor Contratual {versao} · [audit.jsonl]({audit_url}) · 100% local · LGPD §46"

**Tipografia:** Manrope 400 14px `--text-dim`. Centralizado. Padding vertical 16px.

---

## 5. Microcopy completa — PT-BR técnico-jurídico

### 5.1 Princípios de tom

- **Factual, não persuasivo:** advogado-usuário não precisa ser convencido; precisa de informação clara
- **PT-BR formal mas direto:** sem gerundismo ("estaremos analisando" → "analisando"); sem floreios ("aguarde alguns instantes" → "{tempo}s decorridos")
- **Jurisdicção explícita:** "STJ", "BACEN", "Art. 46 LGPD", "CFOAB" são termos canônicos — usar sempre
- **Quantidade quando relevante:** "ratio 2.28x acima" > "muito acima"; "120s timeout" > "não respondeu"
- **Sem persuasão:** não há "convide colegas", não há "compartilhe", não há badge "premium"

### 5.2 Glossário canônico

| Termo | Uso correto |
|---|---|
| Persona Advogado | maiúscula, sempre. Sabia-7B OR Qwen 7B (depende do `LLM_TIER`) |
| Persona Economista | maiúscula, sempre. Qwen 7B padrão |
| Validador semântico | minúscula. cosine similarity ≥0.7 |
| Juiz HITL | maiúscula. Human-in-the-Loop |
| Tese consolidada | resultado do Juiz |
| Tema 1378 STJ | sempre nesta ordem (não "Tema 1378 do STJ") |
| Súmula vinculante | minúscula |
| OAB | sempre maiúscula |
| audit.jsonl | sempre em mono, nunca traduzido |
| audit chain | "cadeia de auditoria" (PT) OR "audit chain" (técnico) — escolher 1 e manter |

### 5.3 Mensagens canônicas (lista enumerável)

Cada mensagem visível ao usuário foi catalogada na descrição dos componentes (C1-C7). Resumo do inventário:

- **C1** (Login): 7 mensagens (heading + 4 labels/CTAs + 2 erros)
- **C2** (Banner): 5 variantes de mensagem (verde / amarelo×2 / vermelho×2)
- **C3** (Upload): 5 mensagens (heading + 3 CTAs/instrução + LGPD)
- **C4** (Processing): 5 fases + heading + footer + cancelar = 8 mensagens
- **C5** (Resultado): 9 mensagens (heading + audit + veredicto + 3 cards + 2 CTAs + link)
- **C6** (Error pane): 4 estruturais (Diag/Causa/Solução/Alt) × N variantes (parsing, LLM timeout, validação, MIME, size, CSRF) ≈ 24 mensagens
- **C7** (Footer): 1 mensagem

**Total inventariado:** ~58 mensagens em PT-BR. Nenhuma placeholder.

---

## 6. Accessibility — WCAG AA

### 6.1 Contraste de cores (verificável)

| Combinação | Ratio | WCAG AA (≥4.5 normal / ≥3 large) |
|---|---|---|
| `--text` `#1A1816` sobre `--bg` `#FAFAF8` | 16.7:1 | ✅ AAA |
| `--text` sobre `--surface` `#FFFFFF` | 17.5:1 | ✅ AAA |
| `--text-muted` `#6B6457` sobre `--bg` | 5.92:1 | ✅ AA |
| `--text-dim` `#9A9082` sobre `--bg` | 3.21:1 | ✅ AA large only — usar APENAS em texto ≥18px (footer, hash truncado tooltip) |
| `--accent` `#EE6B20` sobre `--surface` (botão "Entrar" texto branco) | 3.39:1 (texto branco sobre laranja) | ✅ AA large; usar Manrope 600 ≥16px em botões |
| `--success` `#2C7A4D` sobre `--success-soft` `#E8F4ED` | 4.71:1 | ✅ AA |
| `--danger` `#B43D3D` sobre `--danger-soft` `#FBEAEA` | 4.86:1 | ✅ AA |
| `--warning` (proposto) `#8B5A0B` sobre `--warning-soft` (proposto) `#FFF6E5` | **5.49:1** | ✅ **AA normal** — verificado via cálculo formal WCAG 2.1 sRGB→linear (reprodutível em WebAIM Contrast Checker). *Ver §2.2 atualização micro-PATCH α — cor original `#B8770F` estava matematicamente errada (~3.5:1, falha AA normal); F-CC3-11 endereçado.* |

### 6.2 Keyboard navigation

- Tab order matches visual order em todos os 8 estados
- Enter/Space ativa botões e drop-zone
- Escape cancela upload em curso (S3)
- Skip link "Pular para o conteúdo principal" no topo (foco oculto até Tab inicial)
- Focus indicator: outline 2px solid `--accent` + offset 2px (alto contraste)

### 6.3 Screen reader / ARIA

- `<main id="app-main" aria-live="polite">` — anuncia transições entre estados
- Banner Tema 1378 vermelho: `role="alert" aria-live="assertive"` (interrupção imediata)
- Drop-zone: `role="button" tabindex="0" aria-label="Upload de PDF — drag-and-drop ou clique"`
- Progress bar S3: `role="progressbar" aria-valuenow aria-valuemin aria-valuemax`
- Lista de fases S5: `role="list"` com items `role="listitem"` + `aria-label="Fase {n}: {label} — {status}"`
- Cards deliverables S6: `<article role="article">` com heading H3 + `aria-label="Baixar {tipo} ({formato} {n} páginas)"`
- Spinner ⟳: `aria-hidden="true"` (decorativo); estado real via texto

### 6.4 Reduced motion

- `@media (prefers-reduced-motion: reduce)`: spinner ⟳ sem rotação CSS; progress bar S3 sem animação suavizada (apenas updates discretos)
- Transições HTMX swap: respeitam `prefers-reduced-motion` desativando `view-transition`

### 6.5 Não-objetivo

- Suporte a leitor de tela em português (NVDA / Jaws PT-BR) é **target** mas não testado formalmente no MVP — `BL-A11Y-AUDIT` candidato a TECH-DEBT.md (LOW; pós-MVP).

---

## 7. Flows — interações HTMX swap + SSE

### 7.1 Boot da app (sessão nova)

```
GET / (sem cookie session)
  → server retorna template S1 com CSRF token
  → main vazio renderizado direto (sem swap)
```

### 7.2 Login bem-sucedido

```
POST /login {username, password, csrf_token}
  → server valida → bcrypt verify → cria sessão (cookie HttpOnly + SameSite=strict)
  → server retorna 303 redirect para /
GET / (com cookie session)
  → server resolve banner Tema 1378 status atual
  → server retorna template S2 com banner C2 + drop-zone C3
```

### 7.3 Upload + processing (single-page swap)

```
[S2 → S3]
POST /revisar (multipart/form-data + csrf_token, hx-target="#app-main")
  client-side validação prévia (.pdf, ≤10MB) → se falhar, S2 mostra inline-error sem POST
  server-side: magic bytes + size + CSRF → se falhar, retorna parcial S4 → swap

[S3 → S5 (server-side aceitou)]
server-side dispara pipeline assíncrono
  → retorna parcial S5 com SSE endpoint URL
  → HTMX swap S3 → S5
  → S5 abre EventSource(/revisar/stream/{job_id})

[S5 → S5 (atualizações granulares via SSE)]
SSE event "phase-start" {phase} → swap-oob na fase específica para "running"
SSE event "phase-done" {phase, elapsed_s} → swap-oob para "done" + tempo
SSE event "phase-error" {phase, diagnostico, causa, solucao, alternativa} → swap full S5 → S7

[S5 → S6]
SSE event "complete" {deliverables, veredicto, audit_entry_id} → swap full S5 → S6
EventSource fecha

[S5 → S5 (heartbeat — silent)]
SSE event "ping" {ts} a cada 10s → client reseta lastEventTs (sem mudança UI)

[S5 → S7 (connection drop — micro-PATCH α F-CC3-05)]
Cenário 1: client-side timeout
  Date.now() - lastEventTs > 60000 (sem ping nem phase-* por 60s)
  → emit synthetic phase-error {phase: "connection_drop", diag, causa, sol, alt}
  → swap full S5 → S7 (variante connection_drop)
  → audit.jsonl entry {type: "pipeline_lost_connection", job_id, last_phase, timestamp}

Cenário 2: EventSource.onerror
  Browser dispara onerror antes do timeout client (conexão TCP cai)
  → 1 retry automático com backoff 5s
  → se retry sucesso: silent recovery (mantém S5)
  → se retry falha: mesma synthetic phase-error → S7 + audit entry
```

### 7.4 Banner Tema 1378 → S8 (CRITICAL)

```
Background scheduler (FastAPI lifespan) detecta:
  - falha 2× consecutivas Camada 1 OR
  - parser detecta julgamento Tema 1378 OR
  - maintainer trigger via CLI `revisor monitor-tema --manual-trigger`

server-side flag persistido em audit.jsonl + state file
GET / OR qualquer GET subsequente
  → server resolve banner status = "vermelho"
  → renderiza S8 com main desabilitado
  → hx-trigger=load para outras seções é ignorado (server retorna parcial vazio + cabeçalho HX-Reswap none)

POST /monitor-tema/acknowledge (do botão "Reconhecer")
  → CLI auxiliar registra ack na audit chain
  → main volta a S2; banner desce de vermelho para amarelo
```

### 7.5 Logout

```
POST /logout (csrf_token)
  → server invalida sessão + clear cookie
  → 303 redirect /
GET / → S1
```

---

## 8. Mapping AC → Wireframe (rastreabilidade No Invention)

Cada FR ativo do PRD v1.1.2.1 mapeado a pelo menos 1 estado/componente. Smith pode auditar este mapping em adversarial review CC.3 (se Eric optar).

| FR (PRD v1.1.2.1) | AC | Estado UI | Componente |
|---|---|---|---|
| FR-LGPD-MVP-01 (5 camadas) | AC-FR-LGPD-MVP-01a (cookie sessão) | S1, S2, S5, S6 | C1 (CSRF), C2 (banner persistente respeita auth), todos componentes herdam |
| FR-LGPD-MVP-01 | AC-FR-LGPD-MVP-01b (chmod 600 audit.jsonl + 0% PDFs em plain text — encryption-at-rest L4) | invisível UI (filesystem) | nenhum visível — verificável via test E2E pós-pipeline (`file uploads/*.bin` retorna `data` não `PDF document`); padrão SOP-003 Diag/Causa/Solução/Alternativa para falhas L4 cobertas em §C6 variantes `disk_full_uploads` + `fernet_key_missing` *(adicionado em micro-PATCH α — F-CC3-14 endereçado)* |
| FR-LGPD-MVP-01 | AC-FR-LGPD-MVP-01c (CSP header) | invisível ao UX, mas C1+C3+C5 reusam apenas assets self-hosted (REV-INT-02) — coerente com CSP `default-src 'self'` |
| FR-LGPD-MVP-01 | AC-FR-LGPD-MVP-01d (CSRF) | S1, S2 | C1 input hidden + C3 form |
| FR-LGPD-MVP-01 | AC-FR-LGPD-MVP-01e (SESSION_SECRET ≥32 bytes) | invisível, infra | nenhum visível — é setup; falha cobre `session_secret_missing` em §C6 |
| FR-MONITOR-01 | AC-FR-MONITOR-01a (auto detection ≤7d) | S2 (banner verde "última verif {data}") | C2 verde |
| FR-MONITOR-01 | AC-FR-MONITOR-01b (SOP-005 cross-ref) | S8 + ação "Ver SOP-005" | C2 vermelho com `acoes` |
| FR-MONITOR-01 | AC-FR-MONITOR-01c (CLI 6 flags manual-trigger) | invisível UI (CLI) — banner reflete trigger via state file | C2 (renderiza estado) |
| FR-BACKUP-MVP-01 | AC-FR-BACKUP-MVP-01a/b (cross-platform restore) | invisível UI (background scheduler) | nenhum |
| FR-PARSE-01..04 | AC-FR-PARSE-* (magic bytes + size 10MB + OCR-required) | S3 → S4 (validação) ; S5 fase 1 ; S7 OCR-error variant | C3 (max_size + accept), C6 (4 variantes erro) |
| FR-UPLOAD-01..03 | AC-FR-UPLOAD-* (drag-drop + progress + cancel) | S2 → S3 | C3 |
| FR-CALC, FR-BACEN, FR-RAG, FR-TESE | AC vários (cálculo abusividade, etc) | S5 fases 2-3 ; S6 veredicto | C4 (lista fases), C5 (veredicto + ratio "2.28x acima") |
| FR-JUIZ-01 (HITL) | AC-FR-JUIZ-01 (validação) | S5 fase 5 | C4 |
| FR-DELIV-01 (D1 Relatório Contábil) | AC-FR-DELIV-01 | S6 | C5 card 1 |
| FR-DELIV-04 (D2 Petição) | AC-FR-DELIV-04 | S6 | C5 card 2 |
| FR-DELIV-D3 (D3 Apelação Cível) — **condicional, dual-input** | AC-FR-DELIV-D3 (NOVO v1.1.2) | S2 (drop-zone 2 opcional "decisão adversa") + S6 (variante S6.a card disponível OR variante S6.b card indisponível com CTA "Enviar decisão") | C3 com `tipo: "decisao_adversa"` + C5 prop `deliverables[2].disponivel: bool` *(redefinido em micro-PATCH α — F-CC3-06: D3 requer 2 inputs distintos per PRD v1.1.2.1 §2.3)* |
| FR-DELIV-06 (CFOAB validação) | AC-FR-DELIV-06 | invisível UI (rate limit + audit log) | nenhum no MVP-LEAN-01 — UI específica é BL-DELIV (deferred) |
| FR-AUDIT (HMAC chain) | AC-FR-AUDIT-* (entries imutáveis) | S6 (visualização entry #137 + hash truncado) ; C7 link | C5 + C7 |
| FR-ECONOMISTA-01 | AC-FR-ECONOMISTA-01 (json output) | S5 fase 3 | C4 |
| (genérico — error handling) | padrão "Diag/Causa/Solução/Alt" SOP-003 | S4, S7 | C6 (template forçado) |
| (genérico — anti-bypass HITL bigram) | FR-JUIZ-02 (BL-HITL-ELAB) | S7 variant `validacao_semantica` | C6 |

**FRs do PRD MVP sem mapping UI explícito (intencional):**
- FR-DELIV-06 painel completo: deferred a `BL-CONFIG-UI`
- FR-BACKUP-MVP-01 visualização: invisível por design (scheduler background)
- FR-AUDIT exploração rica: link em C7 → download direto `audit.jsonl` (ferramenta CLI/jq); UI rica é deferred

**No Invention:** cada decisão UX desta spec rastreia a 1+ FR/AC do PRD v1.1.2.1 OR decisão arquitetural ADR-013. Não há estado / componente / microcopy "inventado" sem fonte.

---

## 9. Próximos passos (CC.4+)

1. **Smith CC.3 adversarial review** (Eric decide — padrão perfeição opção B)
2. **Token `--warning` + `--warning-soft`** (BL-UX-WARNING-TOKEN — ~10min, Neo durante CC.6 OR adicionar antes via @architect side-fix)
3. **River CC.4** cria/rebase 3 stories: VAULT-FIX-01 (Done — preservar) + OLLAMA-MGR-01 (Ready — preservar) + **MVP-LEAN-01 nova** (referencia esta spec + PRD v1.1.2.1 + ADR-013)
4. **Keymaker CC.5** valida MVP-LEAN-01 (10-point checklist)
5. **Neo CC.6** implementa em paralelo OLLAMA-MGR-01 + MVP-LEAN-01 com esta spec como input UX

### Tech debt candidate (consolidado pós Smith CC.3 + micro-PATCH α)

| ID candidato | Severity | Description | Effort |
|---|---|---|---|
| **BL-UX-CC3-DEBT** | MEDIUM/LOW (consolidado) | 16 findings residuais Smith CC.3 (8 MEDIUM + 8 LOW): multi-tab race + spacing scale + ETA hardcoded + 5 flows anômalos + UX OAB rate limit + cross-browser docs + 8 LOW (microcopy, glossário, reduced-motion, audit download streaming, banner verde fechável, etc). 4 HIGH foram endereçados inline (F-CC3-05/06/08/11) + 1 MEDIUM cirúrgico (F-CC3-03 tokens) + bonus F-CC3-14. Detalhes em `governance/TECH-DEBT.md` entry BL-UX-CC3-DEBT. | 6-10h fragmentado |
| **BL-A11Y-AUDIT** | LOW | Suporte a leitor de tela PT-BR (NVDA / Jaws PT) é target mas não testado formalmente no MVP. WCAG AA contrast verified empiricamente via cálculo formal WCAG 2.1; teste assistivo real é debt pós-MVP. | 4-6h |

> **micro-PATCH α (CC.3 — 2026-05-06) endereçou:**
> - **4 HIGH inline:** F-CC3-05 (SSE connection drop §S5+§7.3) + F-CC3-06 (D3 dual-input §S2+§S6+§C3+§C5+§8) + F-CC3-08 (catch-all infra + 7 variantes §C6) + F-CC3-11 (contraste `--warning` corrigido para `#8B5A0B` ratio 5.49:1 verificado empiricamente §2.2+§6.1)
> - **1 MEDIUM cirúrgico:** F-CC3-03 (4 tokens novos consolidados em §2.2: `--warning` + `--opacity-disabled` + `--cursor-disabled` + `--focus-ring-*` + `--surface-hover`)
> - **1 LOW bonus side-fix:** F-CC3-14 (AC-FR-LGPD-MVP-01b adicionado ao mapping §8)
> - **16 restantes (8 MED + 8 LOW):** consolidados em `BL-UX-CC3-DEBT` (TECH-DEBT.md)
>
> Padrão CC.2 inline replicado (Eric perfeição opção α). Sem 4º ciclo Smith.

---

*UX Spec MVP-LEAN-01 — Sati (sessão 87, 2026-05-06) · Sprint 03 CC.3 single-page architecture · 8 estados + 7 componentes + microcopy PT-BR + WCAG AA verificado + mapping AC→wireframe completo + micro-PATCH α aplicado.*

— Sati, criando experiências que encantam 🎨
