---
type: story
id: "MVP-LEAN-01"
title: "MVP-LEAN-01 — Single-page MVP completo (5 camadas LGPD + APScheduler + Tema 1378 + 3 deliverables D1+D2+D3)"
status: InProgress
priority: alta
sprint: "03"
epic: "Sprint-03-Phase-1-MVP-LEAN"
fase: "Phase 1 — pós CC course-correction"
owner: "@dev (Neo)"
estimated_effort: "41-55h"
created: "2026-05-06"
created_by: "@sm (River — Niobe)"
branch_sugerido: "feat/mvp-lean-01-single-page"
project: revisor-contratual
predecessor_handoff: ".lmas/handoffs/handoff-morpheus-to-river-2026-05-06-cc4-rebase-3-stories.yaml"
references:
  - "PRD v1.1.2.1 (governance/prd/prd-v1.1.2-PATCH.md) — 13 FRs ativos MVP + 3 deliverables D1+D2+D3 + 17 BL-* deferred"
  - "ADR-013 MVP Lean Strategy + Deployment Path (governance/architecture/adr/adr-013-mvp-lean-strategy-deployment-path.md) — 5 decisões consolidadas"
  - "ux-spec MVP-LEAN-01 (governance/ux-spec-v1.1.2-MVP-LEAN.md) — 8 estados S1-S8 + 7 componentes C1-C7 + microcopy PT-BR + WCAG AA verificado"
  - "tokens.css (bloco_interface/web/static/tokens.css 129 linhas) — 4 conceitos novos pós side-fix (warning + disabled + focus-ring + surface-hover)"
predecessor_decisions:
  - "ADR-009 NFR-LGPD-01 100% on-premise (princípio NÃO-NEGOCIÁVEL preservado)"
  - "ADR-011 Auto-Ollama Lifecycle (FastAPI lifespan etapa 1)"
  - "ADR-012 Vault Data Bundling (FastAPI lifespan etapa 2)"
  - "ADR-013 §2.3 Defense-in-depth LGPD 5 camadas"
  - "ADR-013 §2.4 APScheduler embedded cross-platform + ordem lifespan startup determinística"
  - "ADR-013 §2.5 Dual-layer Tema 1378 STJ (Camada 1 auto + Camada 2 SOP-005 manual + auto-trigger)"
predecessor_stories:
  - "VAULT-FIX-01 (Done — committed 3d055c6 em feature/sprint-03-vault-fix-01) — FastAPI lifespan compartilhado per ADR-013 §2.4"
  - "OLLAMA-MGR-01 (Ready — paralela; lifespan etapa 1 per ADR-011 + ADR-013 §2.4)"
  - "REV-INT-01 (Done) — substituiu Streamlit por FastAPI + HTMX + Jinja2"
  - "REV-INT-02 (Done) — self-hosted woff2 fonts (LGPD on-premise — zero CDN)"
parallel_story: "OLLAMA-MGR-01 (paralela; code paths independentes; lifespan compartilhado mas implementações separadas)"
resolves:
  - "Sprint Goal Sprint 03 Phase 1: MVP single-page completo shippable"
  - "Eric escolha 'opção B perfeição' (sessão 87 CC course-correction)"
  - "13 FRs ativos PRD v1.1.2.1 implementados em código"
  - "8 estados S1-S8 + 7 componentes C1-C7 ux-spec implementados"
  - "Defense-in-depth LGPD 5 camadas (FR-LGPD-MVP-01a..e)"
  - "APScheduler cross-platform Linux+macOS+Windows (FR-BACKUP-MVP-01)"
  - "Dual-layer Tema 1378 STJ (FR-MONITOR-01a..c)"
  - "D3 Apelação Cível dual-input (decisão adversa + contrato)"
unblocks:
  - "Beta release v0.2.0 (após BL-VAULT-BULK-IMPORT + BL-GOLDEN-SET PRE-RELEASE BLOCKERS)"
  - "v1.1+ modalidades roadmap (Bancário Genérico → Imobiliária → Crédito) — esta story estabelece padrão arquitetural single-page reusável"
tags:
  - project/revisor-contratual
  - story
  - mvp-lean
  - sprint-03
  - cc-course-correction-complete
  - phase-1
  - p0-mvp
---

# MVP-LEAN-01 — Single-page MVP completo

```
[@sm · River (Niobe — Facilitator)] — Sprint 03 Phase 1 · MVP-LEAN-01
DOMÍNIO: SoftwareDev · STATUS: Draft (aguarda CC.5 Keymaker validate)
TRAJETÓRIA: pós CC.1A + CC.2 + CC.3 + bridge tokens.css (CC course-correction completa)
```

---

## Story Preamble

> **Como** advogado consumerista bancário,
> **quero** uma aplicação local single-page que receba upload de contrato CDC PF Veículos (e opcionalmente decisão adversa) e retorne 3 deliverables (D1 Relatório Contábil + D2 Petição Inicial + D3 Apelação Cível), com defense-in-depth LGPD, banner regulatório Tema 1378 STJ persistente e audit chain HMAC,
> **para que** eu possa atender clientes em regime 100% local sem violar LGPD.

---

## Contexto e Trajetória CC course-correction

Esta story consolida toda a fundação produzida pela course-correction Sprint 03:

| Etapa | Resultado | Artefato |
|---|---|---|
| **CC.1A** | PRD ratificado (Smith trajetória 13 → 6 → 3 → 0 findings) | `prd/prd-v1.1.2-PATCH.md` (frontmatter version 1.1.2.1) |
| **CC.2** | ADR-013 ratificada (Smith 10→5 LOW debt; 4 HIGH=0) | `architecture/adr/adr-013-mvp-lean-strategy-deployment-path.md` |
| **CC.3** | ux-spec ratificada (Smith 20→16 debt; 4 HIGH endereçados inline; F-CC3-11 contraste corrigido empiricamente) | `ux-spec-v1.1.2-MVP-LEAN.md` |
| **Bridge** | tokens.css side-fix (4 conceitos / 7 declarações; contraste --warning 5.49:1 verificado 3-vetores) | `bloco_interface/web/static/tokens.css` |

O Sprint Goal Sprint 03 Phase 1 é entregar o MVP shippable. Esta story é **a** story dessa fase — todas as outras (VAULT-FIX-01 Done, OLLAMA-MGR-01 Ready) são dependências preservadas.

---

## Acceptance Criteria

> **Princípio:** ACs são tech-agnostic per `quality-gate-enforcement.md` — descrevem **O QUÊ** (comportamento), não **COMO** (implementação). Cada AC rastreia a **FR/AC do PRD v1.1.2.1**, **decisão de ADR-013**, ou **§ específico de ux-spec**. **No Invention.**

### Estados UI (mapeados a ux-spec §3 S1-S8)

- **AC-MVP-01 (S1 Login):** sistema renderiza tela de login para usuário não-autenticado e impede acesso ao pipeline antes de autenticação válida. *Rastreia: FR-LGPD-MVP-01a + ux-spec §3 S1.*
- **AC-MVP-02 (S2 Pré-upload dual-input):** sistema oferece 2 áreas de upload — contrato CDC (obrigatório) e decisão adversa (opcional para D3); CTA "Iniciar análise" só fica habilitado após contrato válido. *Rastreia: FR-PARSE + FR-UPLOAD + ux-spec §3 S2 + F-CC3-06 endereçado.*
- **AC-MVP-03 (S3 Upload em curso):** sistema mostra progresso de upload com possibilidade de cancelamento. *Rastreia: FR-UPLOAD + ux-spec §3 S3.*
- **AC-MVP-04 (S4 Validação MIME/size erro):** uploads inválidos (não-PDF, >10MB, CSRF inválido) renderizam mensagem estruturada Diagnóstico/Causa/Solução/Alternativa sem aceitar o upload. *Rastreia: FR-PARSE + FR-LGPD-MVP-01d + ux-spec §3 S4 + §C6.*
- **AC-MVP-05 (S5 Processing 4 personas SSE):** sistema mostra estado de execução das 5 fases do pipeline (parsing + Advogado + Economista + Validador + Juiz) com tempos parciais e tempo total decorrido. *Rastreia: FR-CALC + FR-BACEN + FR-RAG + FR-TESE + FR-JUIZ-01 + FR-ECONOMISTA-01 + ux-spec §3 S5.*
- **AC-MVP-06 (S6 Resultado consolidado):** após análise completa, sistema mostra veredicto consolidado (tese + confiança + citações validadas) e cards de download para 3 deliverables, com lógica condicional D3 (S6.a/S6.b conforme decisão adversa enviada ou não). *Rastreia: FR-DELIV-01 + FR-DELIV-04 + FR-DELIV-D3 + FR-AUDIT + ux-spec §3 S6 + F-CC3-06.*
- **AC-MVP-07 (S7 Erro pipeline estruturado):** falhas de pipeline (LLM timeout, parsing OCR, validação semântica, juiz HITL bypass) renderizam mensagem com Diagnóstico/Causa/Solução/Alternativa. *Rastreia: SOP-003 padrão + ux-spec §3 S7 + §C6.*
- **AC-MVP-08 (S8 Banner Tema 1378 CRITICAL):** quando Tema 1378 entra em estado CRITICAL (julgamento detectado OU Camada 1 falha 2 execuções consecutivas OU maintainer trigger manual), sistema desabilita main e exibe banner não-fechável até ack. *Rastreia: FR-MONITOR-01b + ADR-013 §2.5 + ux-spec §3 S8.*

### Componentes (mapeados a ux-spec §4 C1-C7)

- **AC-MVP-09 (C1 Login form):** form com campos Usuário/Senha + CSRF token hidden + tratamento de erro de auth (mensagem genérica, não revela qual campo errou). *Rastreia: FR-LGPD-MVP-01a/d + ux-spec §C1.*
- **AC-MVP-10 (C2 Banner Tema 1378 3 níveis):** componente renderiza 3 estados (verde info / amarelo warn 1 falha auto / vermelho CRITICAL) com hierarquia de bloqueio (verde fechável → amarelo fechável após ack 24h → vermelho não-fechável até CLI ack). *Rastreia: FR-MONITOR-01 + ADR-013 §2.5 + ux-spec §C2.*
- **AC-MVP-11 (C3 Upload zone com prop tipo):** componente parametrizado por `tipo: contrato | decisao_adversa` com microcopy + a11y label diferenciados. *Rastreia: FR-PARSE + ux-spec §C3 + F-CC3-06.*
- **AC-MVP-12 (C4 Processing pane SSE):** lista 5 fases com status pending/running/done/error e tempos parciais; abre EventSource ao entrar em S5; trata heartbeat + timeout + retry. *Rastreia: ux-spec §C4 + ux-spec §3 S5 Connection drop handling.*
- **AC-MVP-13 (C5 Resultado pane lógica condicional D3):** props `deliverables[i].disponivel` controla se card D3 renderiza estado disponível (botão Baixar) ou indisponível (CTA "Enviar decisão" volta a S2 mantendo `pdf_hash` do contrato). *Rastreia: FR-DELIV-D3 + ux-spec §C5 + F-CC3-06.*
- **AC-MVP-14 (C6 Error pane padrão SOP-003):** todas as mensagens de erro seguem estrutura Diagnóstico → Causa → Solução → Alternativa; variante catch-all `infra` mapeia exception types via handler central. *Rastreia: SOP-003 + ux-spec §C6 + F-CC3-08 endereçado.*
- **AC-MVP-15 (C7 Footer):** footer mostra versão + link para `audit.jsonl` + LGPD compliance disclaimer. *Rastreia: FR-AUDIT + ux-spec §C7.*

### Decisões arquiteturais transversais

- **AC-MVP-LGPD (5 camadas defense-in-depth):** sistema implementa Auth (L1) + Sessão segura com CSRF/samesite (L2) + Headers HTTP CSP/X-Frame/X-Content (L3) + Encryption-at-rest de uploads (L4) + Permissões filesystem chmod 600/700 (L5). Cada camada cobre um vetor distinto Art. 46 LGPD. Auth elaborada FR-AUTH-01..04 fica deferred a `BL-AUTH-01` v1.1+. *Rastreia: FR-LGPD-MVP-01a..e + ADR-013 §2.3.*
- **AC-MVP-MONITOR (dual-layer Tema 1378):** sistema executa job semanal de monitoramento automático (Camada 1) e expõe SOP-005 + CLI subcommand `revisor monitor-tema --manual-trigger` com 6 flags (Camada 2 manual). Camada 1 falha 2 execuções consecutivas → CRITICAL alert + auto-trigger SOP-005. *Rastreia: FR-MONITOR-01a..c + ADR-013 §2.5.*
- **AC-MVP-BACKUP (APScheduler cross-platform):** sistema executa backup diário (cron 02:00) e rotação semanal (interval 7d) de `vault.db` + `audit.jsonl` para `~/.local/share/revisor-contratual/backups/{YYYY-MM-DD}/`; funciona Linux + macOS + Windows nativamente sem cron OS-específico nem Task Scheduler. *Rastreia: FR-BACKUP-MVP-01a..b + ADR-013 §2.4.*
- **AC-MVP-D3-DUAL-INPUT:** D3 Apelação Cível só é gerada quando decisão adversa é enviada (em S2 dropzone 2 OU re-upload via S6.b CTA "Enviar decisão"); fluxo permite gerar D1+D2 primeiro e D3 depois sem reprocessar D1+D2. *Rastreia: FR-DELIV-D3 + ux-spec §3 S2/S6 + §C5 + F-CC3-06.*
- **AC-MVP-SSE-RESILIENT:** SSE protocol implementa heartbeat 10s server-side + client timeout 60s + EventSource onerror retry com backoff 5s + audit entry `pipeline_lost_connection` quando conexão é perdida. *Rastreia: ux-spec §3 S5 Connection drop handling + F-CC3-05 endereçado.*
- **AC-MVP-ERRORS:** padrão Diag/Causa/Solução/Alternativa em S4+S7 + variante catch-all `infra` parametrizada por exception type (`EXCEPTION_TO_C6_VARIANT` mapping em handler central) + 7 variantes adicionais (`disk_full_audit`, `disk_full_uploads`, `vault_db_locked`, `fernet_key_missing`, `session_secret_missing`, `ollama_subprocess_crash`, `bacen_api_down`, `weasyprint_render_fail`). *Rastreia: ux-spec §C6 + F-CC3-08 endereçado.*
- **AC-MVP-A11Y (WCAG AA):** sistema atinge WCAG AA — contrast ratios verificados (8 combinações, incluindo `--warning #8B5A0B` 5.49:1 verificado empiricamente WCAG 2.1) + keyboard nav (Tab order match visual + Enter/Space ativa botões e drop-zone + Escape cancela upload) + ARIA-live regions (`<main aria-live="polite">` + banner CRITICAL `role="alert" aria-live="assertive"`) + reduced-motion (`@media (prefers-reduced-motion: reduce)`) + focus-ring tokens (`--focus-ring-*`). *Rastreia: ux-spec §6 + WCAG 2.4.7 Focus Visible.*
- **AC-MVP-AUDIT (HMAC chain imutável):** todas as transições de estado de pipeline geram entries em `audit.jsonl` com chain HMAC GENESIS (sequencial, imutável); inclui eventos especiais `pipeline_lost_connection` (com `job_id` + `last_phase` + timestamp) e `pipeline_cancelled` (com `phase_at_cancel`). *Rastreia: FR-AUDIT + ADR-005 + F-CC3-05/F-CC3-07 endereçados.*
- **AC-MVP-LIFESPAN-ORDER:** FastAPI `@asynccontextmanager` lifespan executa startup em ordem determinística — (1) Auto-Ollama detect-then-spawn (ADR-011) → (2) Vault populate idempotente (ADR-012) → (3) APScheduler register backup jobs → (4) Tema 1378 schedule; yield para servir requests; shutdown em ordem inversa (4→3→2→1); falha em qualquer etapa → log CRITICAL + raise abort (não degradação silenciosa). *Rastreia: ADR-013 §2.4 + ux-spec §3 S5 lifespan order.*
- **AC-MVP-TOKENS:** implementação usa os 4 conceitos novos de `tokens.css` corretamente — `--warning`/`--warning-soft` no banner C2 nível AMARELO (Manrope ≥600 16px); `--opacity-disabled` + `--cursor-disabled` em S8 main desabilitado e em CTAs disabled; `--focus-ring-width/offset/color` em todos elementos interativos; `--surface-hover` em drop-zone hover (S2→S3) + button hover + card lift. *Rastreia: tokens.css + ux-spec §2.2.*

---

## Tasks/Subtasks

> **Total estimado: 41-55h** consistente com PRD v1.1.2.1 §2.6. Tasks ordenadas por dependência arquitetural (Layout-base primeiro permite empilhamento dos demais estados).

- [x] **Task 1 — Layout-base + estrutura HTMX swap** (~2h) — DONE sessão 91 CC.10 (Neo)
  - Topbar persistente (`--topbar-h` 56px) com nome de usuário + CTA "Sair"
  - Banner Tema 1378 persistente (componente C2 — visível S1-S8)
  - `<main id="app-main" aria-live="polite">` como target de HTMX swap
  - Footer C7 (versão + link audit.jsonl + LGPD disclaimer)
  - **Mapeia a:** AC-MVP-09/15 (estrutura) + ADR-013 §2.3 + ux-spec layout-base

- [x] **Task 2 — S1 Login + C1 Login form** (~3h) — DONE sessão 91 CC.11 (Neo)
  - Template Jinja2 S1 Login com Fraunces 500 H1 + form HTMX
  - C1 Login form com CSRF token hidden + bcrypt verify + Starlette SessionMiddleware
  - Erro auth genérico (mitiga enumeration); aria-live="polite"
  - Test E2E login flow + auth fail
  - **Mapeia a:** AC-MVP-01 + AC-MVP-09 + AC-MVP-LGPD (L1)

- [ ] **Task 3 — S2 Pré-upload + C3 Upload zone dual-input** (~4h)
  - Template S2 com 2 drop-zones (D1 contrato obrigatório + D2 decisão adversa opcional)
  - C3 Upload zone parametrizado (`tipo: "contrato" | "decisao_adversa"`) com microcopy + aria-label diferenciados
  - Client-side validation (extensão .pdf + size ≤10MB) antes de POST
  - CTA "Iniciar análise" disabled (`--opacity-disabled` + `--cursor-disabled`) até D1 ter PDF
  - Test E2E upload válido + inválido (variantes MIME/size)
  - **Mapeia a:** AC-MVP-02 + AC-MVP-11 + AC-MVP-D3-DUAL-INPUT + AC-MVP-TOKENS

- [ ] **Task 4 — S5 Processing + C4 Processing pane + SSE resilient** (~6h)
  - Template S5 com lista de 5 fases (Parsing + Advogado + Economista + Validador + Juiz)
  - SSE endpoint backend (`/revisar/stream/{job_id}`) emitindo events: `phase-start`, `phase-done`, `phase-error`, `complete`, `ping`
  - Client-side EventSource com:
    - Heartbeat: server `event: ping` a cada 10s; client reseta `lastEventTs`
    - Timeout: `setInterval` 5s checa `Date.now() - lastEventTs > 60000` → synthetic phase-error → S7 variant `connection_drop`
    - `EventSource.onerror`: 1 retry com backoff 5s; falha → mesma synthetic
  - Audit entry `pipeline_lost_connection` quando connection drop detectado
  - Test integration: SSE happy path + timeout + onerror
  - **Mapeia a:** AC-MVP-05 + AC-MVP-12 + AC-MVP-SSE-RESILIENT + AC-MVP-AUDIT

- [ ] **Task 5 — S6 Resultado + C5 Resultado pane + D3 condicional** (~5h)
  - Template S6 com 2 variantes (S6.a D3 disponível / S6.b D3 indisponível)
  - C5 props `deliverables[i].disponivel: bool` controla rendering D3
  - Card D3 indisponível: `--surface-2` opacity 0.85 + CTA secundário "Enviar decisão" → volta a S2 mantendo `pdf_hash` do contrato
  - Backend re-processa apenas D3 (não reprocessa D1+D2) quando decisão adversa enviada via S6.b
  - Sumário Juiz em Fraunces 500 (gravidades jurídica)
  - Hash audit truncado (4+4 chars) em JetBrains Mono com tooltip clipboard
  - Test E2E S6.a + S6.b + transição S6.b → S2 → S6.a
  - **Mapeia a:** AC-MVP-06 + AC-MVP-13 + AC-MVP-D3-DUAL-INPUT + AC-MVP-AUDIT

- [ ] **Task 6 — S4+S7 Error pane + C6 catch-all `infra` + 7 variantes** (~4h)
  - Template C6 Error pane com props {titulo, diagnostico, causa, solucao, alternativa, acoes}
  - Handler central Python `EXCEPTION_TO_C6_VARIANT` mapping em `bloco_interface/web/error_handler.py`
  - 7 variantes catalogadas: `disk_full_audit` + `disk_full_uploads` + `vault_db_locked` + `fernet_key_missing` + `session_secret_missing` + `ollama_subprocess_crash` + `bacen_api_down` + `weasyprint_render_fail`
  - Variante catch-all `infra_unknown` para exceptions não-mapeadas
  - Test integration: cada variante reproduz exception → renderiza C6 correto
  - **Mapeia a:** AC-MVP-04 + AC-MVP-07 + AC-MVP-14 + AC-MVP-ERRORS

- [ ] **Task 7 — S8 Banner CRITICAL + C2 Banner 3 níveis + auto-trigger SOP-005** (~3h)
  - C2 Banner componente renderiza 3 níveis (verde/amarelo/vermelho) com hierarquia de bloqueio
  - State file `~/.local/share/revisor-contratual/tema_1378_status.json` persiste estado
  - Auto-trigger: 2 execuções consecutivas Camada 1 fail-loud → CRITICAL alert + state file flag VERMELHO
  - Banner VERMELHO: `role="alert" aria-live="assertive"` + main desabilitado + ack via CLI `revisor monitor-tema --acknowledge`
  - POST `/monitor-tema/acknowledge` registra ack na audit chain → desce para amarelo
  - Test integration: trigger fail 2× consecutivas → renderiza S8 + main disabled
  - **Mapeia a:** AC-MVP-08 + AC-MVP-10 + AC-MVP-MONITOR

- [ ] **Task 8 — FR-LGPD 5 camadas + FR-BACKUP APScheduler + FR-MONITOR dual-layer** (~14-16h — task mais densa)
  - **L1 Auth (preservada/integrada):** bcrypt + AUTH_USERNAME + AUTH_PASSWORD_HASH em `.env`
  - **L2 Sessão segura:** Starlette `SessionMiddleware(https_only=True, samesite="strict")` + CSRF middleware + `SESSION_SECRET` ≥32 bytes em `.env` (gerado via `secrets.token_urlsafe(32)`)
  - **L3 Headers HTTP:** middleware adicionando CSP `default-src 'self'; ... ; frame-ancestors 'none'` + X-Frame-Options DENY + X-Content-Type-Options nosniff + HSTS opcional
  - **L4 Encryption-at-rest:** `cryptography.fernet` com `FERNET_KEY` em `.env`; encrypt-on-upload em POST `/revisar` → decrypt in-memory para parsing → delete pós-pipeline; audit log inclui hash do PDF original
  - **L5 Permissões filesystem:** `audit.jsonl` chmod 600 + `uploads/` chmod 700 (cross-platform — pathlib + stat em Linux/macOS; ACL no Windows quando possível)
  - **APScheduler embedded:** `BackgroundScheduler` em FastAPI lifespan; jobs `backup_daily` (cron 02:00) + `backup_rotation` (interval 1d, deleta backups >7 dias)
  - **FR-MONITOR Camada 1:** `bloco_dataset/scraper_tema_1378.py` com httpx retry exponencial (2s/4s/8s) + parser regex resilient com seletores fallback (CSS class + tag semantic + text-pattern); fail-loud em zero seletores match
  - **FR-MONITOR Camada 2:** SOP-005 já documentado em `docs/sop-monitoramento-tema-1378.md` (preservado de PRD v1.1.2 PATCH); CLI subcommand `revisor monitor-tema` com 6 flags (`--manual-trigger`, `--status`, `--tese-text`, `--data-julgamento`, `--data-arquivamento`, `--acknowledge`)
  - **Auto-trigger:** lifespan job de monitoramento Camada 1 → 2 fails consecutivas → state file flag CRITICAL → log audit entry CRITICAL_ALERT
  - Tests: integration cada camada LGPD + backup restore simulado + Tema 1378 fail 2× → CRITICAL
  - **Mapeia a:** AC-MVP-LGPD + AC-MVP-MONITOR + AC-MVP-BACKUP + AC-MVP-LIFESPAN-ORDER + ADR-013 §2.3/2.4/2.5

- [ ] **Task 9 — AC validation E2E + audit chain verification** (~4-5h)
  - Smoke E2E real (Ollama + Sabia/Qwen 7B + Qwen 7B economista + httpx STJ/STF + PDF físico)
  - Verificação audit chain HMAC integridade (`audit.jsonl` entries sequenciais, hash chain válido)
  - Verificação encryption-at-rest: `file uploads/*.bin` retorna `data` (não `PDF document`)
  - Verificação backup: simular delete de `vault.db` → restaurar último backup → 100% recuperação
  - Verificação cross-platform: tests CI Linux + macOS + Windows
  - Verificação a11y: contrast ratios (WebAIM Contrast Checker), keyboard navigation manual, screen reader smoke (target NVDA — `BL-A11Y-AUDIT` é debt formal pós-MVP)
  - Test report consolidado em `governance/qa/qa-gate-mvp-lean-01.md` (futuro QA gate)
  - **Mapeia a:** Todos os ACs (cobertura E2E)

---

## Dev Notes

### Cross-references obrigatórias

Neo (durante implementação) DEVE consultar:

| Documento | Para |
|---|---|
| **PRD v1.1.2.1** §7.1.1 (FR-LGPD-MVP-01) | Detalhes implementação 5 camadas LGPD (Fernet, Starlette config, samesite=strict, CSP exata, chmod) |
| **PRD v1.1.2.1** §7.10 (FR-BACKUP-MVP-01 + FR-MONITOR-01) | APScheduler + dual-layer Tema 1378 |
| **PRD v1.1.2.1** §2.3 (D3) | Fluxo dual-input D3 + parser decisão adversa |
| **ADR-013** §2.3 | Padrão arquitetural defense-in-depth (não detalhes implementação — esses estão no PRD) |
| **ADR-013** §2.4 | Ordem lifespan startup determinística (4 etapas) |
| **ADR-013** §2.5 | Mitigação fragilidade Camada 1 (httpx retry + parser resilient + auto-trigger) |
| **ux-spec** §2 | Tokens (4 conceitos novos já em tokens.css) |
| **ux-spec** §3 | Wireframes 8 estados (S1-S8) |
| **ux-spec** §4 | Componentes 7 (C1-C7) com props + microcopy |
| **ux-spec** §5 | Microcopy completa PT-BR (~58 mensagens) + glossário |
| **ux-spec** §6 | A11y WCAG AA (8 contrast ratios verificados) |
| **ux-spec** §7 | Flows HTMX swap + SSE protocol |

### Dependências preservadas

- **VAULT-FIX-01 (Done):** lifespan etapa 2 já implementada (`populate_vault_if_needed` idempotente). Não tocar.
- **OLLAMA-MGR-01 (Ready, paralela):** lifespan etapa 1. Pode ser implementada em paralelo com MVP-LEAN-01 OU antes (caminho crítico para test E2E real).

### Anti-patterns explícitos (NÃO fazer)

- ❌ Reimplementar VAULT-FIX-01 — apenas integrar via FastAPI lifespan
- ❌ Mensagens de erro genéricas tipo "500 Erro Interno" — toda mensagem segue Diag/Causa/Solução/Alternativa
- ❌ Token hardcoded em código (cor `#B8770F`, `#8B5A0B`, etc) — usar `var(--warning)` etc do `tokens.css`
- ❌ Cron OS-específico ou Windows Task Scheduler — usar APScheduler embedded
- ❌ HSM cloud para FERNET_KEY (viola ADR-009 NFR-LGPD-01) — chave em `.env` local apenas
- ❌ Multi-tenant ou SaaS (ADR-013 §2.2 DESCARTADO permanente)
- ❌ Auth elaborada FR-AUTH-01..04 no MVP (deferred a `BL-AUTH-01` v1.1+)

### Performance baseline

- Pipeline E2E: ~180-300s total (Sabia premium pode chegar a 300s; Qwen balanced ~250s)
- Encryption-at-rest overhead: ~5-10ms per upload (negligível vs análise)
- Backup overhead: <1s diário em background (não bloqueia pipeline)

---

## File List (a popular durante implementação)

### Task 1 (CC.10 / sessão 91 — Neo) — Layout-base ✅

- [x] `bloco_interface/web/templates/base.html` (M) — topbar+user+logout, banner Tema 1378 C2 (3 níveis), `<main id="app-main" aria-live="polite">`, footer C7
- [x] `bloco_interface/web/static/app.css` (M) — `.topbar-user`, `.topbar-logout`, `.banner-tema-1378` (3 níveis), `.footer-c7` + focus-ring
- [x] `bloco_interface/web/app.py` (M) — `_read_app_version()`, `APP_VERSION`, `DEFAULT_TEMA_1378`, `_layout_context()`, GET `/` context merge, POST `/logout` HX-Redirect
- [x] `tests/integration/test_layout_base.py` (NEW) — 8 tests integration cobrindo AC-MVP-09 + AC-MVP-15 + AC-MVP-LGPD-L1 + WCAG aria-labels

### Task 2 (CC.11 / sessão 91 — Neo) — S1 Login + C1 form ✅

- [x] `bloco_interface/web/auth.py` (NEW) — `get_secret_key()`, `get_admin_credentials()`, `verify_password()` bcrypt, `authenticate()` anti-enumeration constant-time, `generate_csrf_token()`, `verify_csrf_token()` hmac.compare_digest
- [x] `bloco_interface/web/app.py` (M) — SessionMiddleware (24h max_age, samesite=lax, https_only=env-toggle), GET `/login` (gera CSRF + renderiza S1), POST `/login` (CSRF verify + bcrypt + session fixation mitigation), GET `/` protegida (303 redirect /login se sem session), helper `_render_login_error()`
- [x] `bloco_interface/web/templates/s1_login.html` (NEW) — `{% extends "base.html" %}` com h1 Fraunces 500, form HTMX hx-post=/login + hx-swap=outerHTML, CSRF hidden, autofocus username, aria-live="polite" no erro; tema_1378="oculto" + session_user=None pré-auth (per ux-spec §3 S1)
- [x] `bloco_interface/web/static/app.css` (M) — `.login-container`, `.login-title` (Fraunces), `.login-subtitle`, `.login-form` + inputs + focus-ring, `.login-submit` + hover, `.login-error` (danger soft + border-left)
- [x] `pyproject.toml` (M) — `bcrypt>=4.0` + `itsdangerous>=2.0` adicionadas
- [x] `tests/integration/test_login_flow.py` (NEW) — 9 tests: GET /login form + CSRF, banner/topbar omissões pré-auth, login success HX-Redirect=/, anti-enumeration (wrong password vs wrong username retornam mesma 401 + msg), CSRF inválido 403, GET / redirect 303, integração logout
- [x] `tests/integration/test_layout_base.py` (M) — fixture refatorado: env vars test + login automático antes de yield (Task 2 protege GET /)

### Backend Python

- [ ] `bloco_interface/web/app.py` — FastAPI lifespan (4 etapas determinísticas) + middleware (Session + CSRF + Headers HTTP)
- [ ] `bloco_interface/web/error_handler.py` — `EXCEPTION_TO_C6_VARIANT` mapping + 8 variantes
- [ ] `bloco_interface/web/routes/*` — `/login`, `/logout`, `/revisar`, `/revisar/stream/{job_id}`, `/monitor-tema/acknowledge`, `/audit/download`
- [ ] `bloco_lgpd/encryption.py` — Fernet encrypt/decrypt PDFs uploads
- [ ] `bloco_lgpd/headers.py` — CSP + X-Frame-Options + X-Content-Type-Options middleware
- [ ] `bloco_lgpd/permissions.py` — chmod cross-platform (Linux/macOS/Windows)
- [ ] `bloco_backup/scheduler.py` — APScheduler embedded + jobs `backup_daily` + `backup_rotation`
- [ ] `bloco_dataset/scraper_tema_1378.py` — Camada 1 com httpx retry + parser resilient
- [ ] `bloco_dataset/tema_1378_state.py` — state file management + auto-trigger logic
- [ ] `bloco_audit/chain.py` (preservada — VAULT-FIX-01) — adicionar entry types `pipeline_lost_connection`, `pipeline_cancelled`

### Frontend (Jinja2 + HTMX)

- [ ] `bloco_interface/web/templates/base.jinja2` — layout-base
- [ ] `bloco_interface/web/templates/components/banner_tema_1378.jinja2` — C2 (3 níveis)
- [ ] `bloco_interface/web/templates/components/upload_zone.jinja2` — C3 (parametrizado por tipo)
- [ ] `bloco_interface/web/templates/components/processing_pane.jinja2` — C4
- [ ] `bloco_interface/web/templates/components/resultado_pane.jinja2` — C5 (lógica condicional D3)
- [ ] `bloco_interface/web/templates/components/error_pane.jinja2` — C6
- [ ] `bloco_interface/web/templates/states/s1_login.jinja2` ... `s8_banner_critical.jinja2`
- [ ] `bloco_interface/web/static/js/sse_resilient.js` — heartbeat + timeout + retry client-side

### CLI

- [ ] `bloco_cli/monitor_tema.py` — subcommand `revisor monitor-tema` com 6 flags

### Tests

- [ ] `tests/integration/test_lifespan_order.py` — verifica ordem startup determinística (1→2→3→4)
- [ ] `tests/integration/test_lgpd_5_camadas.py` — cada camada
- [ ] `tests/integration/test_apscheduler_backup.py` — backup + rotation cross-platform
- [ ] `tests/integration/test_tema_1378_dual_layer.py` — Camada 1 fail 2× → CRITICAL
- [ ] `tests/integration/test_sse_resilient.py` — heartbeat + timeout + retry
- [ ] `tests/integration/test_d3_dual_input.py` — S6.a + S6.b + transição
- [ ] `tests/integration/test_error_variants.py` — 8 variantes C6
- [ ] `tests/e2e/test_smoke_real.py` — pipeline E2E real (Ollama + STJ/STF + PDF físico)

---

## Change Log

### Task 2 done 2026-05-06 (Neo sessão 91 CC.11)

**Status:** InProgress (Tasks 1+2 done; Tasks 3-9 pending)

**Implementação Task 2 — S1 Login + C1 Login form (~3h estimado, ~2h real):**

- **Módulo `bloco_interface/web/auth.py` (NEW):**
  - `get_secret_key()` — env `REVISOR_SECRET_KEY` OR efêmera-on-startup com warning (sessões expiram a cada restart em dev)
  - `get_admin_credentials()` — env `ADMIN_USERNAME` + `ADMIN_PASSWORD_HASH` (default `admin`/bcrypt de `admin` em dev)
  - `verify_password()` — bcrypt.checkpw com tratamento defensivo de hash malformado (não levanta para evitar info leak)
  - `authenticate()` — anti-enumeration: `hmac.compare_digest` em username + bcrypt check sempre executado (mesmo se user errado), retorna boolean único
  - `generate_csrf_token()` — `secrets.token_hex(32)` (256-bit entropy)
  - `verify_csrf_token()` — `hmac.compare_digest` constant-time

- **`bloco_interface/web/app.py`:**
  - `SessionMiddleware` instalado (max_age=24h conforme ux-spec §3 S1 linha 199; samesite=lax; https_only via env `REVISOR_HTTPS_ONLY=1`)
  - GET `/login` — gera CSRF + grava em session + renderiza s1_login.html com `tema_1378.nivel="oculto"` + `session_user=None` (ux-spec §3 S1: sem banner/usuário pré-auth)
  - POST `/login` — verifica CSRF (constant-time) → 403 "Sessão expirada" se falha; auth → 401 "Usuário ou senha inválidos" se falha; success → `request.session.clear()` (mitiga session fixation) + grava `user` + retorna 200 + `HX-Redirect=/`
  - GET `/` — agora protegida: sem `session.get("user")` → 303 redirect `/login`
  - Helper `_render_login_error()` — re-renderiza S1 com erro + refresh CSRF para próxima tentativa

- **Template `s1_login.html`:**
  - Herda base.html
  - h1 "Revisor Contratual" em `var(--f-display)` Fraunces 500
  - Subtitle "Análise de contratos CDC PF Veículos" Manrope 400 muted
  - Form HTMX (`hx-post="/login"` + `hx-swap="outerHTML"` + `hx-target="this"`) com:
    - CSRF hidden
    - Label/input Usuário (autofocus, autocomplete=username, aria-required)
    - Label/input Senha (type=password, autocomplete=current-password)
    - Botão "Entrar" (PT-BR per ux-spec linha 625; não "Login")
    - Erro condicional `role="alert"` + `aria-live="polite"` + `data-testid="login-error"`

- **CSS (.login-* classes):** `.login-container` (max-w 360px, margin 96px auto), `.login-title` (Fraunces 32px), `.login-form` (flex column gap 6px), inputs (focus-ring tokens), `.login-submit` (accent bg + hover), `.login-error` (danger-soft + border-left)

- **`pyproject.toml`:** `bcrypt>=4.0` + `itsdangerous>=2.0` adicionadas

**Quality gate empírico Neo (não Oracle):**
- ruff `All checks passed` em 4 arquivos modificados (`app.py` + `auth.py` + `test_login_flow.py` + `test_layout_base.py`) ✅
- pytest baseline: 289 → **298 passed, 1 skipped** em 61.53s ✅ (+9 tests novos, zero regressão)

**Tests novos (9 em `tests/integration/test_login_flow.py`):**
1. `test_get_login_renders_s1_form` — form + CSRF + autofocus + heading + "Entrar"
2. `test_get_login_omits_banner_tema_1378_pre_auth` — banner suprimido pré-auth
3. `test_get_login_omits_topbar_user_pre_auth` — topbar sem nome usuário pré-auth
4. `test_post_login_success_returns_hx_redirect` — credenciais OK → 200 + HX-Redirect=/
5. `test_post_login_wrong_password_generic_error` — senha errada → 401 + msg genérica
6. `test_post_login_wrong_username_same_generic_error` — username errado → MESMA 401 + msg (anti-enumeration)
7. `test_post_login_invalid_csrf_returns_403` — CSRF mismatch → 403 "Sessão expirada"
8. `test_get_root_redirects_to_login_if_unauthenticated` — GET / sem session → 303 /login
9. `test_post_logout_clears_session_then_root_redirects` — integração Task 1 logout + Task 2 redirect

**Tests Task 1 retrofitted (8 em `test_layout_base.py`):** fixture refatorado com env vars test + login automático antes de yield (necessário pois GET / agora protegida)

**ACs cobertos:**
- ✅ **AC-MVP-01 (S1 Login):** GET /login + POST /login + protect GET /
- ✅ **AC-MVP-09 (C1 component):** form fields + autofocus + aria-live error
- ✅ **AC-MVP-LGPD-L1 (auth defense-in-depth):** bcrypt 12 rounds + anti-enumeration timing-constant + CSRF hmac.compare_digest

**Anti-patterns evitados (per restrições handoff CC.11):**
- ❌ NÃO mexeu `bloco_interface/ollama_manager.py` (Done preservado)
- ❌ NÃO alterou FastAPI lifespan (ADR-013 §2.4 ordem preservada)
- ❌ NÃO criou C2/C3/C4/C5/C6 (Tasks 1+3-7 ownership; C7 já feito Task 1)
- ❌ NÃO inventou features fora ACs declarados (No Invention)
- ❌ NÃO push (Operator EXCLUSIVE)
- ❌ Password sempre bcrypt hashed (nunca plaintext)
- ❌ Anti-enumeration: mesma resposta wrong-user vs wrong-pwd

**Decisões técnicas autônomas Neo (per handoff):**
- **User store:** Opção A — env vars `ADMIN_USERNAME` + `ADMIN_PASSWORD_HASH` (single-user MVP)
- **CSRF:** Opção A — custom `secrets.token_hex` + `hmac.compare_digest` (KISS, sem dep externa)
- **C1 partial vs inline:** Opção A — inline em `s1_login.html` (extrair só se Task 6 reusar)

**Detalhes de segurança:**
- Session cookie: `httpOnly=True` (default Starlette), `samesite='lax'`, `https_only` configurável via env (default False dev)
- Session fixation mitigation: `request.session.clear()` antes de gravar `user` no login success
- CSRF refresh: novo token gerado a cada GET /login + a cada erro auth (mitiga replay)
- bcrypt rounds=12 padrão (env hash com rounds=4 em testes para velocidade)

**Observações para Tasks futuras:**
- Task 3 (S2 Pré-upload) já pode assumir `request.session.get("user")` populado em todas as rotas autenticadas
- Task 6 (Error pane C6) pode reusar `_render_login_error` pattern para outros erros user-friendly
- Backend pode chamar `auth.authenticate()` em rota `POST /change-password` futura (escopo pós-MVP)

### Task 1 done 2026-05-06 (Neo sessão 91 CC.10)

**Status:** Ready → InProgress (no início CC.10) → **Ready for Review** (Task 1 done; demais Tasks 2-9 pending — story permanece InProgress mas Task 1 isolada Ready para review)

**Implementação Task 1 — Layout-base + estrutura HTMX swap (~2h estimado, ~1.5h real):**

- **Topbar persistente (C-topbar):** mark + brand + nome usuário (condicional `session_user`) + CTA "Sair" HTMX (`hx-post="/logout"`); altura `var(--topbar-h)` (já existente em tokens.css desde Sprint 02 UI-1); `aria-label="Barra de navegação principal"`
- **Banner Tema 1378 (C2 — 3 níveis):** condicional `tema_1378.nivel != 'oculto'`; `role="status"` (verde/amarelo) ou `role="alert"` (vermelho); `aria-live="polite"|"assertive"`; classes BEM `.banner-tema-1378--{verde|amarelo|vermelho}` mapeando para `var(--success|warning|danger)` + `var(--*-soft)` backgrounds; tokens semânticos `--warning #8B5A0B` (CC.3 bridge) usados; lógica real fica para Task 7 (FR-MONITOR dual-layer)
- **Main com id="app-main":** preserva `<div id="workspace">` interno como swap target dos partials Sprint 02 UI-1 (zero breakage); novo id `app-main` no `<main>` + `aria-live="polite"` + `aria-label="Área principal de conteúdo"` cobre AC-MVP-09 sem renomear hx-target existente
- **Footer C7:** versão dinâmica (lida de `pyproject.toml` via `tomllib` stdlib, fallback `v0.0.0+unknown`); link `audit.jsonl`; LGPD micro-disclaimer "100% local · LGPD §46"; tipografia Manrope 400 13px; centralizado; `aria-label="Rodapé com versão e disclaimers"`
- **POST /logout:** retorna 200 + header `HX-Redirect: /login`; clears `request.scope["session"]` se SessionMiddleware presente (Task 2 instala middleware — checagem defensiva via `"session" in request.scope`)
- **Helper `_layout_context(request)`:** centraliza context dict (session_user + tema_1378 + app_version + audit_url) reutilizável por outras rotas em Tasks futuras

**Quality gate empírico Neo (não Oracle):**
- ruff `All checks passed` em `bloco_interface/web/app.py` + `tests/integration/test_layout_base.py` ✅
- pytest baseline: 281 → **289 passed, 1 skipped** em 61.60s ✅ (+8 tests novos, zero regressão)

**Tests novos (8 em `tests/integration/test_layout_base.py`):**
1. `test_get_root_renders_topbar` — topbar + brand + aria-label
2. `test_get_root_renders_main_with_app_main_id` — `id="app-main"` + `aria-live="polite"`
3. `test_get_root_renders_banner_tema_1378_default_verde` — banner verde default + role="status"
4. `test_get_root_renders_footer_c7` — footer com audit.jsonl link + 100% local + LGPD
5. `test_get_root_footer_has_app_version` — versão dinâmica `v...`
6. `test_post_logout_returns_hx_redirect` — POST /logout 200 + header HX-Redirect=/login
7. `test_main_aria_label_present` — WCAG AA aria-label semântico
8. `test_footer_aria_label_present` — WCAG AA aria-label semântico

**ACs cobertos:**
- ✅ **AC-MVP-09 (estrutura layout):** topbar + main + footer renderizam; `id="app-main"` swap target
- ✅ **AC-MVP-15 (footer C7):** versão dinâmica + audit link + LGPD disclaimer
- ✅ **AC-MVP-LGPD-L1 (banner Tema 1378 persistente):** 3 níveis + role/aria-live corretos

**Anti-patterns evitados (per restrições handoff CC.10):**
- ❌ NÃO mexeu em `bloco_interface/ollama_manager.py` (Done preservado)
- ❌ NÃO alterou FastAPI lifespan (ADR-013 §2.4 ordem preservada)
- ❌ NÃO criou C1/C3/C4/C5/C6 (Tasks 2-7 ownership)
- ❌ NÃO inventou features fora ACs declarados (No Invention per quality-gate-enforcement.md)
- ❌ NÃO push direto (Operator EXCLUSIVE)

**Observações para Tasks futuras:**
- Task 2 (S1 Login + C1) instalará SessionMiddleware → `session_user` populado real
- Task 7 (S8 Banner CRITICAL + auto-trigger SOP-005) substituirá `DEFAULT_TEMA_1378` mock por lógica FR-MONITOR-01 real
- Sidebar histórico (`<aside class="sidebar">`) preservada de Sprint 02 UI-1; Tasks futuras decidem se mantêm (Task 5 Resultado pode reusar) ou removem em favor de single-page puro
- Helper `_read_app_version()` poderá virar utility compartilhada se outras rotas precisarem da versão

### Created 2026-05-06 (River sessão 87 CC.4)

> **Sprint 03 Phase 1 Sprint Goal: MVP single-page completo.**
>
> **Refs:** PRD v1.1.2.1 + ADR-013 + ux-spec-v1.1.2-MVP-LEAN + tokens.css.
>
> **Trajetória CC course-correction Sprint 03 (recapitulação):**
> - **CC.1A:** PRD trajetória 13→6→3→0 findings (v1.0.3 → v1.1.0 → v1.1.1 → v1.1.2 → v1.1.2.1)
> - **CC.2:** ADR-013 ratificada (Smith 10→5 LOW debt; 4 HIGH=0; status accepted)
> - **CC.3:** ux-spec ratificada (Smith 20→16 debt; 4 HIGH endereçados inline; F-CC3-11 contraste falso corrigido empiricamente)
> - **Bridge tokens.css:** side-fix 4 conceitos / 7 declarações; contraste --warning 5.49:1 verificado 3-vetores (Sati + Smith vigilância + Aria validação independente)
>
> Status inicial **Draft** — aguarda CC.5 Keymaker `*validate-story-draft` (10-point checklist) antes de avançar a Ready. Pós-validate: CC.6 Neo implementação paralela com OLLAMA-MGR-01 (Ready preservada).

---

*MVP-LEAN-01 — River (Niobe, Sprint 03 Phase 1, 2026-05-06) · single-page architecture · 13 FRs + 8 estados + 7 componentes + 4 tokens novos + a11y WCAG AA + audit HMAC chain + 41-55h consolidado em uma única story shippable.*

— River, removendo obstáculos 🌊

---

## Validation Section (CC.5 Keymaker — sessão 87 / 2026-05-06)

**Verdict:** **GO** ✅
**Score:** **9/10**
**Validator:** @po Keymaker
**Predecessor handoff:** `H-S03-CC5-MOR2KEY-001` (Morpheus dispatch CC.5)

### 10-Point Checklist Resultados

| # | Critério | Status | Observação |
|---|---|---|---|
| 1 | Story preamble formato canônico | ✅ | Linhas 69-71 — 3 elementos canônicos LMAS (Como advogado consumerista bancário / Quero single-page LGPD-compliant + 3 deliverables / Para atender clientes 100% local sem violar LGPD) |
| 2 | ACs SMART + tech-agnostic | ✅ | 25 ACs (8 estados S1-S8 + 7 componentes C1-C7 + 10 transversais arquiteturais). Todos comportamentais. Tech-specifics em AC-MVP-LIFESPAN-ORDER (FastAPI lifespan), AC-MVP-LGPD (Fernet/Starlette/CSP), AC-MVP-TOKENS (tokens.css) são justificados — decisões arquiteturais fechadas em ADR-009/011/012/013 + REV-INT-01 (per `quality-gate-enforcement.md` exceção tech-specific quando "tecnologia É o requisito") |
| 3 | Tasks atômicas com estimativa | ⚠️ | 8 de 9 tasks atômicas (≤6h cada). **Task 8 (~14-16h)** EXCEDE critério (<8h) — mas decomposta em 9 subtasks visíveis (L1+L2+L3+L4+L5 LGPD + APScheduler + Camada 1 + Camada 2 + Auto-trigger + Tests). River reconheceu explicitamente "task mais densa". Total 41-55h consistente PRD §2.6. **Recomendação a Neo CC.6:** quebrar Task 8 em sub-commits granulares durante implementação (8a LGPD ~6h + 8b APScheduler ~2h + 8c+8d FR-MONITOR ~6h + 8e tests ~2h) |
| 4 | Dev Notes cross-references | ✅ | Tabela 12 entradas com PRD §s específicos (§7.1.1, §7.10, §2.3, §2.6) + ADR-013 §s (§2.3/§2.4/§2.5) + ux-spec §s (§2/§3/§4/§5/§6/§7) |
| 5 | Frontmatter Obsidian | ✅ | type=story, id, title, status, sprint=03, project=revisor-contratual, 4 references canônicas, 6 predecessor_decisions, 4 predecessor_stories, parallel_story, tags incluindo `project/revisor-contratual` + `cc-course-correction-complete` + `p0-mvp` (per `obsidian-format-guard.md`) |
| 6 | No Invention rastreabilidade | ✅ | Cada AC tem "*Rastreia: FR/AC + ADR + ux-spec §*" identificável e verificável. Cross-check spot-check: AC-MVP-D3-DUAL-INPUT cita "FR-DELIV-D3 + ux-spec §3 S2/S6 + §C5 + F-CC3-06" — confirmado existem nos artefatos canônicos |
| 7 | Definition of Done implícito | ✅ | Task 9 cobre 7 verificações: smoke E2E real (Ollama+Sabia/Qwen+httpx STJ/STF+PDF físico) + audit chain HMAC integridade + encryption-at-rest verification + backup restore simulação + cross-platform CI Linux/macOS/Windows + a11y manual + test report consolidado em `qa-gate-mvp-lean-01.md`. *Sugestão: River pode considerar tornar DoD explícito como seção dedicada em PATCH futuro (não-bloqueante)* |
| 8 | Dependências documentadas | ✅ | predecessor_decisions: 6 ADRs (ADR-009 + ADR-011 + ADR-012 + ADR-013 §2.3/§2.4/§2.5); predecessor_stories: 4 (VAULT-FIX-01 Done + OLLAMA-MGR-01 Ready + REV-INT-01 Done + REV-INT-02 Done); parallel_story OLLAMA-MGR-01; AC-MVP-LIFESPAN-ORDER referencia ADR-013 §2.4 ordem startup determinística (4 etapas) |
| 9 | Anti-patterns explícitos | ✅ | Dev Notes "Anti-patterns explícitos (NÃO fazer)" — 7 itens: (1) reimplementar VAULT-FIX-01; (2) mensagens "500 Erro Interno"; (3) token hardcoded; (4) cron OS-específico; (5) HSM cloud (viola ADR-009); (6) multi-tenant/SaaS (viola ADR-013 §2.2); (7) auth elaborada FR-AUTH-01..04 v1.0.2 (deferred BL-AUTH-01) |
| 10 | Status inicial correto | ✅ | Frontmatter linha 5: `status: Draft` (correto pré-validate). Será alterado para `Ready` após este verdict GO. |

**Score consolidado:** **9/10** (1 ressalva ⚠️ Task 8 atomicidade — não-bloqueante)

### Required Fixes
*Nenhum.* Score 9/10 ≥ 7/10 = GO automático per `story-lifecycle.md` G1 gate.

### Ressalvas (não-bloqueantes)
- **Task 8 atomicidade:** 14-16h excede critério `<8h`. Mitigação aceita: subtasks já decompostas em 9 unidades visíveis (LGPD 5 camadas + APScheduler + 2 camadas FR-MONITOR + auto-trigger + tests). **Recomendação operacional a Neo durante CC.6:** quebrar Task 8 em sub-commits granulares (8a/8b/8c/8d/8e) para preservar atomicidade no nível de PR/commit, mantendo a Task 8 como agrupador conceitual da story.

### Decisão
Status alterado de **Draft** → **Ready** ✅

A story passa o G1 gate. Próximo: **Morpheus dispatch CC.6 Neo** para implementação. **Paralelismo viável:** OLLAMA-MGR-01 (Ready preservada) pode ser dev-yolo paralelo a MVP-LEAN-01 (code paths independentes per parallel_story declaration).

---

— Keymaker, equilibrando prioridades 🎯
