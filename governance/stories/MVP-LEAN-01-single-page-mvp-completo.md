---
type: story
id: "MVP-LEAN-01"
title: "MVP-LEAN-01 — Single-page MVP completo (5 camadas LGPD + APScheduler + Tema 1378 + 3 deliverables D1+D2+D3)"
status: Ready
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

- [ ] **Task 1 — Layout-base + estrutura HTMX swap** (~2h)
  - Topbar persistente (`--topbar-h` 56px) com nome de usuário + CTA "Sair"
  - Banner Tema 1378 persistente (componente C2 — visível S1-S8)
  - `<main id="app-main" aria-live="polite">` como target de HTMX swap
  - Footer C7 (versão + link audit.jsonl + LGPD disclaimer)
  - **Mapeia a:** AC-MVP-09/15 (estrutura) + ADR-013 §2.3 + ux-spec layout-base

- [ ] **Task 2 — S1 Login + C1 Login form** (~3h)
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
