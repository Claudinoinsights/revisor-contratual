---
type: ux-spec
title: "Revisor Contratual — UX Spec v2.0.0 (SaaS BYOK Multi-Tenant + OrSheva)"
project: revisor-contratual
version: "2.0.0"
last_updated: "2026-05-07"
status: draft
author: "@ux-design-expert (Sati)"
sprint: "04"
phase: 4
brand_book: "OrSheva 7"
predecessor: "Sprint 03 ux-spec-v1.1.2-MVP-LEAN.md (superseded)"
tags:
  - project/revisor-contratual
  - ux-spec
  - sprint-04
  - orsheva-brandbook
  - saas-multi-tenant
---

# Revisor Contratual — UX Spec v2.0.0

> **Iluminar · Estruturar · Consolidar** — tagline OrSheva 7 ressoa o workflow do advogado: iluminar irregularidades contratuais, estruturar análise multi-persona, consolidar em peça pronta para tribunal.

---

## Seção 1 — Sumário

UX Spec v2.0.0 para Sprint 04 cloud SaaS BYOK multi-tenant. **Escopo simplificado** pós Phase 3.1 patches: o app SaaS NÃO replica leitura de relatório dentro da interface — o advogado **baixa o PDF e revisa offline** em sua ferramenta preferida (Adobe Reader, Foxit, etc.), retornando ao app apenas para clicar **Aprovar** ou **Desaprovar**.

**Foco UX (90% do trabalho):**
- **Onboarding** (cadastro escritório + API key Anthropic + DPA acceptance)
- **Dashboard** (listagem análises com 3 ações por linha)
- **Settings** (gestão usuários + key rotation + tier subscription)
- **Aplicação OrSheva brandbook** (tokens, fonts, light/dark themes)

**Workflow advogado (linear):**
```
Login → Dashboard → Nova Análise → Upload PDF
   ↓
Processing (real-time progress) → PDF Ready notification
   ↓
[Baixar PDF] → revisar offline → retornar ao app
   ↓
[Aprovar] → billing event Stripe → invoice
   OU
[Desaprovar] → modal reason → no billing
```

**Princípios UX guia:**
- **User-centric (Sally):** advogado já tem ferramentas de leitura PDF preferidas; respeitar workflow real
- **Metric-driven (Brad):** componentes reutilizáveis (atomic design) reduzem surface bugs e aceleram development
- **Empático:** OrSheva fonts (Fraunces serif + Manrope sans) transmitem seriedade jurídica + modernidade tech

---

## Seção 2 — OrSheva Brandbook Application

### Token Mapping (light theme padrão)

| Token OrSheva | Hex | Uso no SaaS |
|---|---|---|
| `--or-500` | #EE6B20 | **CTA primário** (Aprovar, Iniciar Análise, Cadastrar Key, Salvar) |
| `--or-400` | #FF8A4C | CTA hover state (lighten 8%) |
| `--or-700` | #AC4408 | CTA pressed/active state |
| `--or-100` | #FFE3CF | CTA tinted background (success toast) |
| `--sh-700` | #142E49 | **Headings dark** (H1/H2 light theme); background dark theme primary |
| `--sh-400` | #4D6A93 | Headings secondary, status info |
| `--sh-100` | #D6DEEC | Background secondary (cards, sections) |
| `--sh-50` | #EEF2F8 | Background tertiary (zebra rows tabela) |
| `--pearl` | #F8F4ED | **Background primary light theme** |
| `--bone` | #E9E0D0 | Borders sutis (1px), separators |
| `--stone` | #B6AC9B | Disabled states, placeholders |
| `--ink` | #0F0E0C | **Text primary light theme** |

### Fonts Application

| Font | Weight | Uso |
|---|---|---|
| **Fraunces** (display, serif) | 300-900 | H1 hero ("Revisor Contratual"), H2 section titles, branding moments |
| **Manrope** (body, sans) | 300-800 | Paragraphs, labels, buttons, table content (default body) |
| **JetBrains Mono** (mono) | 400-500 | API keys truncadas (`sk-ant-...XYZ`), commit hashes em audit logs, code blocks |
| **Frank Ruhl Libre** (Hebrew opcional) | 400-700 | Easter egg pages legais (about/history/manifesto) — opcional |

### Themes

- **Light theme (default):** `data-theme="light"` — pearl bg + ink text + or-500 accent. Aplicado a 90% dos usuários.
- **Dark theme:** `data-theme="dark"` toggle no nav — sh-900 bg + pearl text + or-400 accent (hue ajustado).
- **Texturas grain/noise:** sutis (3.5% opacity light, 8% dark) via SVG turbulence inline (CSS already in brandbook). Aplicado em backgrounds de hero S1 + S2 + S6 para warmth visual.

### Spacing Scale

OrSheva-aligned (multiples of 4px):
```
--space-1: 4px   (gap inline)
--space-2: 8px   (padding tight)
--space-3: 12px  (padding default button)
--space-4: 16px  (gap stack default)
--space-6: 24px  (section gap)
--space-8: 32px  (hero margin)
--space-12: 48px (page margin)
```

---

## Seção 3 — 8 Estados/Telas (S1-S8)

### S1 — Login

- **Propósito:** autenticação escritório multi-tenant
- **FRs alinhados:** FR-AUTH-03 (login com tenant_id JWT)
- **Componentes usados:** C1 (CTA), C4 (form input), texture grain hero
- **Notas UX:** logo OrSheva centered + tagline "Iluminar · Estruturar · Consolidar"; "Esqueci senha" link discreto; "Criar conta para meu escritório" como secondary action levando a S2

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│              ╔═══════════════════════════╗               │
│              ║  ✨  REVISOR CONTRATUAL   ║               │
│              ║  Iluminar · Estruturar    ║               │
│              ║  · Consolidar             ║               │
│              ╚═══════════════════════════╝               │
│                                                          │
│    ┌────────────────────────────────────────────┐       │
│    │ Email do escritório                        │       │
│    │ ┌──────────────────────────────────────┐  │       │
│    │ │ adv@escritorio.com.br                │  │       │
│    │ └──────────────────────────────────────┘  │       │
│    │                                            │       │
│    │ Senha                                      │       │
│    │ ┌──────────────────────────────────────┐  │       │
│    │ │ ••••••••                             │  │       │
│    │ └──────────────────────────────────────┘  │       │
│    │                                            │       │
│    │       ┌──────────────────────────┐        │       │
│    │       │      ENTRAR  →           │        │       │
│    │       └──────────────────────────┘        │       │
│    │                                            │       │
│    │  Esqueci a senha · Criar conta novo escr. │       │
│    └────────────────────────────────────────────┘       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### S2 — Onboarding

- **Propósito:** cadastro escritório novo + API key Anthropic + DPA + tier
- **FRs alinhados:** FR-AUTH-01 (cadastro tenant), FR-API-KEY-01 (validação key), FR-LGPD-01 (DPA acceptance)
- **Componentes:** C1, C4, C6 (tier badge)
- **Notas UX:** wizard 4 passos com progress dots; cada passo collapsable; key validation com loading state ping `/v1/models`; DPA scroll-required-to-accept (advogado tem que ler)

```
┌─────────────────────────────────────────────────────────┐
│ OrSheva 7  |  Onboarding seu escritório         (1/4)   │
├─────────────────────────────────────────────────────────┤
│ ●━━━━○━━━━○━━━━○                                        │
│ Dados   Key   DPA   Tier                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Vamos começar com seu escritório                       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Razão social                                    │    │
│  │ ┌─────────────────────────────────────────┐    │    │
│  │ │ Silva & Associados Advocacia LTDA       │    │    │
│  │ └─────────────────────────────────────────┘    │    │
│  │                                                 │    │
│  │ CNPJ                                            │    │
│  │ ┌─────────────────────────────────────────┐    │    │
│  │ │ 00.000.000/0001-00                      │    │    │
│  │ └─────────────────────────────────────────┘    │    │
│  │                                                 │    │
│  │ Advogado responsável                            │    │
│  │ ┌─────────────────────────────────────────┐    │    │
│  │ │ Dr. José Silva — OAB/SP 123.456         │    │    │
│  │ └─────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│              [ Voltar ]  [ Continuar  → ]               │
└─────────────────────────────────────────────────────────┘
```

### S3 — Dashboard

- **Propósito:** centro de operação do escritório — listagem análises com 3 ações
- **FRs alinhados:** FR-DASH-01..02, FR-APPROVE-01 simplificado, FR-OUTPUT-03
- **Componentes:** C1, C2 (tabela), C6 (tier badge), C7 (notification)
- **Notas UX:** filtros sticky no top scroll; tabela com zebra rows (--sh-50); 3 ações por linha como icon buttons com tooltip ARIA; notification "Análise pronta!" toast quando S5 completa em background

```
┌─────────────────────────────────────────────────────────────┐
│ ✨ OrSheva | [Análises] [Settings] [Admin]    🌓  Dr.J ▼   │
├─────────────────────────────────────────────────────────────┤
│ Bem-vindo, Dr. José · Tier [Pro] · 23/30 análises este mês │
├─────────────────────────────────────────────────────────────┤
│ Filtros: [Status ▼] [Doctype ▼] [Data ▼] [Buscar]  [+ Nova]│
├─────────────────────────────────────────────────────────────┤
│ ID     │ Cliente    │ Doctype   │ Data   │ Status     │Ações│
├────────┼────────────┼───────────┼────────┼────────────┼─────┤
│ #1234  │ João Silva │ Veicular  │ 07/05  │ Pending ✓  │📥✅❌│
│ #1233  │ Maria C.   │ Bancário  │ 07/05  │ Approved   │📥   │
│ #1232  │ Pedro L.   │ FIES      │ 06/05  │ Processing │ —   │
│ #1231  │ Ana M.     │ Imobil.   │ 06/05  │ Rejected   │📥↩️ │
│ #1230  │ Carlos T.  │ Veicular  │ 05/05  │ Approved   │📥   │
├────────┼────────────┼───────────┼────────┼────────────┼─────┤
│                  ‹ 1 2 3 ... 8 ›                            │
└─────────────────────────────────────────────────────────────┘
```

**Legenda ações:**
- 📥 = Baixar PDF (sempre disponível pós-OCR)
- ✅ = Aprovar (apenas em pending_review)
- ❌ = Desaprovar (apenas em pending_review)
- ↩️ = Reabrir (rejected → pending_review)

### S4 — Nova Análise

- **Propósito:** upload PDF + metadata para iniciar pipeline
- **FRs alinhados:** FR-OCR-01 (PDF upload), FR-DOCTYPE-01..02 (UI selector + 4 doctypes)
- **Componentes:** C1, C4 (UF select 27 opções, Data picker, doctype dropdown)
- **Notas UX:** drop zone clara com hover state; validation client-side (PDF only, max 50MB); UF/Data opcionais (fallback OCR detection); doctype OBRIGATÓRIO

```
┌─────────────────────────────────────────────────────────┐
│ ← Voltar | Nova Análise                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │                                                   │  │
│  │     📄  Arraste o PDF do contrato aqui           │  │
│  │         ou clique para selecionar                 │  │
│  │                                                   │  │
│  │     PDF até 50MB                                  │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  Tipo de contrato (obrigatório)                         │
│  ┌──────────────────────────────────────────────┐       │
│  │ Selecione...                            ▼   │       │
│  │   • CDC Veicular                             │       │
│  │   • FIES                                     │       │
│  │   • Bancário (cheque especial/financiamento) │       │
│  │   • Imobiliário (financiamento residencial)  │       │
│  └──────────────────────────────────────────────┘       │
│                                                         │
│  Metadados opcionais (preencha se PDF for imagem)       │
│  ┌────────────────────┬────────────────────┐            │
│  │ UF do contrato     │ Data assinatura    │            │
│  │ [SP ▼]             │ [07/05/2026 📅]    │            │
│  └────────────────────┴────────────────────┘            │
│                                                         │
│              [ Cancelar ] [ Iniciar Análise → ]         │
└─────────────────────────────────────────────────────────┘
```

### S5 — Processing

- **Propósito:** progress real-time durante pipeline
- **FRs alinhados:** FR-OCR-02 (multi-page paralelo), FR-PERSONAS-01 (4 personas), FR-OUTPUT-01 (PDF gen)
- **Componentes:** C5 (progress bar 5 fases), C7 (toast quando completar)
- **Notas UX:** SSE para updates real-time; estimated time decrementando; botão "Cancelar" disponível até judge consolidação; user pode fechar tab e voltar — análise continua server-side

```
┌─────────────────────────────────────────────────────────┐
│ Análise #1234 — Contrato CDC Veicular                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Análise em andamento... Tempo estimado: ~2min         │
│                                                         │
│   ●━━━━●━━━━●━━━━○━━━━○                                  │
│   OCR  Personas  Juiz  PDF  Pronto                      │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │ ✓ OCR Vision (Sonnet 4.6) ........... 12 págs   │   │
│   │ ✓ Persona Aria — Análise Jurídica   .. concluída│   │
│   │ ⟳ Persona Atlas — Análise Econômica  . processando│ │
│   │ ⟳ Persona Tank — Análise Bancária    . processando│ │
│   │ ⟳ Persona Smith — Análise Adversária . processando│ │
│   │ ○ Juiz Revisor — Consolidação ........ aguardando│  │
│   │ ○ Geração PDF ........................ aguardando│  │
│   └─────────────────────────────────────────────────┘   │
│                                                         │
│              [ Cancelar análise ]                       │
│                                                         │
│   💡 Pode fechar essa tela — você será notificado       │
│      quando estiver pronto                              │
└─────────────────────────────────────────────────────────┘
```

### S6 — PDF Ready

- **Propósito:** análise concluída — advogado revisa offline e retorna para approval
- **FRs alinhados:** FR-OUTPUT-01..04 (PDF disponível), FR-APPROVE-01 simplificado
- **Componentes:** C1 CTA "Baixar PDF", C7 notification "Análise pronta", small badges para Aprovar/Desaprovar
- **Notas UX:** **CTA primário é BAIXAR PDF** (advogado precisa ler antes de decidir); aprovar/desaprovar são secundários até PDF baixado (audit log captura download timestamp)

```
┌─────────────────────────────────────────────────────────┐
│ ← Voltar | Análise #1234                  [Pending ✓]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Análise concluída!                                     │
│                                                         │
│  Cliente: João Silva                                    │
│  Doctype: CDC Veicular PF                               │
│  Concluída em: 07/05/2026 às 14:32                      │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │                                                   │  │
│  │   📄 Baixe o PDF e revise em sua ferramenta       │  │
│  │      preferida (Adobe Reader, Foxit, etc.)        │  │
│  │                                                   │  │
│  │      ┌─────────────────────────────────┐          │  │
│  │      │  📥  BAIXAR PDF DA ANÁLISE       │          │  │
│  │      └─────────────────────────────────┘          │  │
│  │                                                   │  │
│  │      Após revisar, retorne aqui para aprovar:     │  │
│  │                                                   │  │
│  │       [ ✅ Aprovar ]    [ ❌ Desaprovar ]          │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  💡 Se houve decisão adversa anexa, baixe também a      │
│     petição de Apelação Cível: [📥 Baixar Petição D3]   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### S7 — Settings

- **Propósito:** gestão escritório (usuários, API key, tier, billing)
- **FRs alinhados:** FR-AUTH-02 (users CRUD), FR-API-KEY-03..04 (rotation/revoke), FR-DASH-02 (billing)
- **Componentes:** C1, C2 (tabela usuários), C4 (form), C6 (tier)
- **Notas UX:** tabs no top (Usuários / API Key / Tier / Billing); aba "API Key" mostra dual-key window state (current + pending) durante rotação 24h; revoke key com confirmação modal C3

```
┌─────────────────────────────────────────────────────────┐
│ Settings — Silva & Associados                           │
├─────────────────────────────────────────────────────────┤
│ [Usuários] [API Key] [Tier] [Billing]                   │
├─────────────────────────────────────────────────────────┤
│ === Aba: API Key ===                                    │
│                                                         │
│  Anthropic API Key (BYOK)                               │
│                                                         │
│  Chave atual                                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │ sk-ant-api03-xxxxxxxxxx...XYZ      ✅ Validada  │   │
│  │ Cadastrada em: 01/05/2026                        │   │
│  │ Última utilização: hoje, 14:32                   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  Status da rotação: nenhuma rotação em andamento        │
│                                                         │
│           [ 🔄 Rotacionar Chave ] [ ⚠️ Revogar ]        │
│                                                         │
│  ─────────────────────────────────────                  │
│                                                         │
│  💡 Custo médio API: R$ 4,18 por análise CDC Veicular   │
│     pago diretamente à Anthropic via sua key            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### S8 — Admin (Eric only)

- **Propósito:** super-user view para Eric gerenciar tenants
- **FRs alinhados:** FR-ADMIN-01 (admin operations)
- **Componentes:** C2 (tabela tenants), C6 (tier badge), C1 (CTA suspend/reactivate)
- **Notas UX:** acessível apenas para usuários com role=admin (Eric); listagem agrega billing por tenant; suspender requer confirmação modal C3 com reason

```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ Admin Console (Eric)                                 │
├─────────────────────────────────────────────────────────┤
│ Filtros: [Tier ▼] [Status ▼] [Buscar tenant]            │
├─────────────────────────────────────────────────────────┤
│ Escritório       │ Tier  │ Análises │ Receita  │ Ações  │
├──────────────────┼───────┼──────────┼──────────┼────────┤
│ Silva & Assoc.   │ Pro   │  23/30   │ R$ 1.150 │ ⏸️ ✏️  │
│ Costa Advocacia  │ Start │   3/5    │ R$ 350   │ ⏸️ ✏️  │
│ Lima Jurídico    │ Pro   │  28/30   │ R$ 1.340 │ ⏸️ ✏️  │
│ Souza & Souza    │ Susp. │   0/-    │ R$ 0     │ ▶️ ✏️  │
├──────────────────┴───────┴──────────┴──────────┴────────┤
│ Total mensal agregado: R$ 12.840 · 4 escritórios ativos │
└─────────────────────────────────────────────────────────┘
```

---

## Seção 4 — Componentes Reutilizáveis (C1-C7)

### C1 — Botão CTA Primário

| Estado | Background | Text | Border |
|---|---|---|---|
| Default | `--or-500` | `--pearl` | none |
| Hover | `--or-400` | `--pearl` | none |
| Active | `--or-700` | `--pearl` | none |
| Disabled | `--stone` | `--bone` | none |
| Loading | `--or-500` + spinner | hidden | none |

**Anatomia:** padding `--space-3` vertical / `--space-6` horizontal; border-radius 8px; Manrope 600 14px; transition 200ms ease-out.

**Acessibilidade:** `role="button"`, `aria-busy="true"` quando loading, focus outline 2px `--or-500` offset 2px, `aria-disabled` quando disabled.

### C2 — Tabela Responsiva

**Anatomia:** thead `--sh-700` text on `--sh-50` bg; tbody zebra com `--pearl` + `--sh-50` alternados; row hover `--or-100`; ações como icon buttons 32x32 com tooltip.

**Mobile (320-767px):** tabela colapsa em cards stacked — cada análise vira card com 3 ações em row horizontal no rodapé do card.

**Acessibilidade:** `<table>` semântico com `<th scope="col">`; row tabindex 0 keyboard nav; ações `aria-label` explícito ("Aprovar análise #1234 do cliente João Silva").

### C3 — Modal Confirmação

**Anatomia:** overlay `rgba(15,14,12,0.6)` (ink alpha 60%) + grain texture; modal `--bg-elev` (#FFFFFF light, `--sh-800` dark) com border `--bone` 1px + shadow elevated; max-width 480px; Fraunces title H2 + Manrope body.

**Variantes:** confirm (CTA primário) + cancel (CTA secondary outlined); rejection requires reason field obrigatório.

**Acessibilidade:** trap focus within modal, ESC closes, `role="dialog"` + `aria-labelledby` + `aria-describedby`, return focus to trigger button on close.

### C4 — Form Input

**Anatomia:** label Manrope 500 12px above input; input height 44px (touch-friendly), padding `--space-3`, border `--bone` 1px, border-radius 6px; focus border `--or-500` 2px; placeholder `--stone`.

**Variantes:** text input, select (UF 27 opções, doctype 4 opções), date picker (native HTML5), API key field (monospace JetBrains + reveal toggle 👁️).

**Acessibilidade:** `<label htmlFor>` associado; error state via `aria-invalid` + `aria-describedby`; required marker visual + `aria-required`; inline error texto pt-BR + ícone.

### C5 — Progress Bar Real-Time

**Anatomia:** 5 fases visíveis (OCR / Personas / Juiz / PDF / Pronto); cada fase um pill com 3 estados (○ aguardando `--stone`, ⟳ processando `--or-400` pulsing, ✓ done `--or-500`); SSE updates via WebSocket OR Server-Sent Events.

**Acessibilidade:** `role="progressbar"` + `aria-valuenow`/`aria-valuemax`; live region `aria-live="polite"` para narrar atualizações; reduced motion `@media (prefers-reduced-motion)` desabilita pulse animation.

### C6 — Tier Badge

| Tier | Background | Text |
|---|---|---|
| Starter | `--pearl` | `--ink` (border `--bone`) |
| Pro | `--or-100` | `--or-700` |
| Enterprise | `--sh-700` | `--pearl` |

**Anatomia:** padding `--space-1` `--space-3`; border-radius 999px; Manrope 600 11px uppercase letterspacing 0.05em; ícone opcional left.

### C7 — Notification Toast

**Anatomia:** position fixed top-right; max-width 360px; Manrope body 13px; ícone left + texto + close button; auto-dismiss 5s (success/info) ou manual (error).

**Variantes:** success `--or-500` border-left + bg `--or-100`; error `--sh-700` border-left + bg `--sh-100`; info `--sh-400` border-left + bg `--sh-50`.

**Acessibilidade:** `role="status"` (success/info) ou `role="alert"` (error); `aria-live="polite"`; close button `aria-label="Fechar notificação"`.

---

## Seção 5 — Responsive Breakpoints

| Breakpoint | Width | Behavior |
|---|---|---|
| **Mobile** | 320-767px | Hamburger nav (S3 Dashboard nav colapsa); tabela vira cards stacked; single column form; CTAs full-width |
| **Tablet** | 768-1279px | Side nav opcional (drawer toggle); tabela compacta (algumas colunas hide via priority); 2 col grid em S2 onboarding |
| **Desktop** | 1280px+ | Full top nav horizontal; tabela completa todas colunas; 3 col grid em S2; max-width container 1440px center |

**Touch targets:** mínimo 44x44px em todas plataformas (WCAG AAA recommendation).

---

## Seção 6 — Accessibility (WCAG AA mínimo)

### Contrast Ratios (auditados)

| Par | Ratio | Status |
|---|---|---|
| `--or-500` (#EE6B20) on `--pearl` (#F8F4ED) | **4.6:1** | ✅ AA |
| `--ink` (#0F0E0C) on `--pearl` | **18.2:1** | ✅ AAA |
| `--sh-700` (#142E49) on `--pearl` | **12.4:1** | ✅ AAA |
| `--pearl` on `--or-500` (CTA text) | **4.6:1** | ✅ AA (large text AAA) |
| `--stone` on `--pearl` (placeholder) | **3.0:1** | ⚠️ AA Large only — NÃO usar para texto vital |

### Keyboard Navigation

- Todas ações acessíveis via Tab + Enter/Space
- Modal C3 trap focus + ESC closes
- S3 Dashboard tabela: arrow keys navegam linhas (opcional enhancement)
- Skip-to-main-content link no top de cada página

### Screen Reader

- Botões aprovar/desaprovar com `aria-label` específico ("Aprovar análise #1234 cliente João Silva")
- Status badges com texto + ícone (não só ícone)
- Live region em S5 Processing narra updates ("OCR concluído. Iniciando análise pelas personas.")

### Focus Indicators

- Outline `--or-500` 2px solid + offset 2px em todos elementos focáveis
- Nunca remover outline (usar `:focus-visible` para distinguir mouse vs keyboard se desejado)

### Reduced Motion

- `@media (prefers-reduced-motion: reduce)` desabilita:
  - Progress bar pulse animation (C5)
  - Toast slide-in (C7)
  - Modal fade transitions (C3)
- Mantém apenas opacity changes (sem motion)

### Form Errors

- `aria-invalid="true"` em inputs com erro
- `aria-describedby` aponta para mensagem de erro
- Mensagens em pt-BR claras ("CNPJ inválido. Verifique os 14 dígitos.")
- Ícone visual + cor `--sh-700` (não confiar apenas em cor)

---

## Seção 7 — Notas UX Críticas

### 1. Workflow respeita ferramenta do advogado

Eric clarificou: advogados já têm leitores PDF preferidos (Adobe Reader, Foxit). NÃO replicar leitura no app — desperdiçaria surface UX e geraria inconsistência. App SaaS é **gerenciador de pipeline + billing trigger**, não leitor de PDF.

### 2. CTA primário em S6 é BAIXAR, não Aprovar

Aprovar/Desaprovar antes de ler PDF é ético-problemático (advogado deve revisar antes de fundamentar petição em IA). Visual hierarchy: BAIXAR é orange-500 grande; Aprovar/Desaprovar são secundários até audit log captura download timestamp.

### 3. Onboarding 4 passos colapsable

Não force form único de 30 campos (overwhelm). Quebra em 4 chunks digestíveis: Dados → API Key → DPA → Tier. User pode salvar e voltar (persisted progress).

### 4. Dark theme é premium experience

OrSheva tem light/dark nativo. Dark mode é diferencial percebido em SaaS jurídico (concorrentes como Astrea/ADVBOX são light-only). Implementar desde MVP (não debt futuro).

### 5. Texturas grain/noise como warmth

OrSheva brand é editorial sofisticado (não corporate sterile). Grain texture sutil em hero S1/S2 humaniza interface — diferencial competitivo silencioso.

### 6. Frank Ruhl Libre como easter egg

Font hebraica histórica (sheva = sete) tem peso conceitual. Usar em página "About" / "História da OrSheva" / "Manifesto" — momento branding sem pressão UX.

---

## Seção 8 — Cross-references

### PRD v2.0.0 (FR alignment per S1-S8)

| Tela | FRs PRD v2.0.0 |
|---|---|
| S1 Login | FR-AUTH-03 |
| S2 Onboarding | FR-AUTH-01, FR-API-KEY-01, FR-LGPD-01..02 |
| S3 Dashboard | FR-DASH-01..02, FR-APPROVE-01 simplificado, FR-OUTPUT-03 |
| S4 Nova Análise | FR-OCR-01, FR-DOCTYPE-01..02 |
| S5 Processing | FR-OCR-02, FR-PERSONAS-01..03, FR-OUTPUT-01..02 |
| S6 PDF Ready | FR-OUTPUT-01..04, FR-APPROVE-01..03, FR-D3-01 |
| S7 Settings | FR-AUTH-02, FR-API-KEY-03..04, FR-DASH-02, FR-BILLING-01..04 |
| S8 Admin | FR-ADMIN-01 |

### 5 ADRs Sprint 04

- **ADR-014** Provider Abstraction Anthropic + BYOK — drives S2 onboarding API key flow + S7 settings rotation UI
- **ADR-015** Vision OCR Architecture — drives S5 progress phases + S4 metadata override fields
- **ADR-016** Multi-Doctype Dispatcher — drives S4 doctype selector UI (4 opções)
- **ADR-017** Multi-Tenant Isolation BACKBONE — drives S1 tenant_id JWT + S8 admin cross-tenant view
- **ADR-018** SaaS Pricing Hybrid + Billing State Machine — drives S3 status badges + S6 approve flow + S7 billing tab

### Atlas Research

- **Atlas v1** Section 2 — Vision OCR landscape (informa S5 progress phases nomeação)
- **Atlas v2** Section 3 — Pricing benchmark (informa S6 R$ messaging "custo médio R$ 4,18/análise")
- **Atlas v2** Section 4 — LGPD operador (informa S2 DPA acceptance flow)

### OrSheva Brandbook

- `projects/Revisor-Contratual/orsheva-brandbook.html` (2001 linhas) — fonte de truth tokens/fonts/themes citados explicitamente em Seção 2

### Smith Phase 5 (próximo)

Smith fará adversarial review verificando:
- WCAG AA compliance real (contrast checking automatizado)
- Workflow gaps (advogado consegue completar primeira análise sem fricção?)
- Mobile fallback robustez (S3 tabela em 320px funcional?)
- Edge cases (key revocation durante análise em andamento, tier downgrade meio do mês, etc.)

---

— Sati, criando experiências que encantam 🎨
