---
type: prd
title: "Revisor Contratual — PRD v1.0.3 DELTA (PATCH)"
project: revisor-contratual
version: "1.0.3"
predecessor: "prd/prd-v1.0.2.md"
status: active
last_updated: "2026-05-05"
owner: "@pm (Morgan)"
date: "2026-05-05"
sprint: "02 (planning)"
patch_basis: "REV-INT-01 stack migration + 6 R-NEW deferred + Eric reclassification TD-PIPELINE-SMOKE-REAL"
tags:
  - project/revisor-contratual
  - prd
  - prd-delta
  - sprint-02
  - patch
---

# PRD v1.0.3 — DELTA Section (PATCH)

> **Esta é uma PATCH section sobre o PRD v1.0.2 canônico. Não substitui o PRD principal — adiciona/modifica seções específicas.**
> Per `.claude/rules/prd-governance.md`: a partir de v1.0.0+, cada PATCH/MINOR DEVE conter Delta section + Changelog. Este arquivo é a ENTRADA v1.0.3 do Changelog do PRD.

---

## Frontmatter — atualização de versão

PRD v1.0.2 frontmatter `version: "1.0.2"` → v1.0.3 frontmatter `version: "1.0.3"`. Decisão de bump:

| Bump considerado | Justificativa | Decisão |
|---|---|---|
| **PATCH** (1.0.2 → 1.0.3) | Stack migration (Streamlit → FastAPI) é refinement de implementação; ACs comportamentais permanecem; 6 R-NEW são extensions de FRs existentes | ✅ **ESCOLHIDA** — alinha com convenção PRD v1.0.2 (que aplicou PATCH para mudanças substantivas) |
| **MINOR** (1.0.2 → 1.1.0) | Tecnicamente, mudança de stack visible-to-user pode justificar MINOR | ❌ rejeitada — convenção projeto é PATCH para tudo que não é breaking semântico |

---

## Delta (v1.0.2 → v1.0.3) — Por Módulo

### Módulo: Stack & UI Web (impacto REV-INT-01)

#### FR-AUTH-01 (Autenticação) — UPDATED

| Antes (v1.0.2) | Depois (v1.0.3) |
|---|---|
| "Sistema NÃO renderiza nenhuma funcionalidade antes de login bem-sucedido (Streamlit)" | "Sistema NÃO renderiza nenhuma funcionalidade antes de login bem-sucedido (FastAPI + HTMX)" |
| "Cookie de sessão Streamlit com expiração configurável" | "Cookie de sessão FastAPI com expiração configurável (Starlette `SessionMiddleware`)" |

**Razão:** REV-INT-01 substituiu Streamlit por FastAPI + HTMX + Jinja2 + uvicorn. Acceptance Criteria comportamentais inalterados — apenas implementação técnica.

**Note Sprint 02 (UI-1):** Esta FR ainda NÃO está implementada na UI Web. Implementação nesta sprint via story UI-1 (ou story dedicada AUTH-01 conforme decisão Aria).

#### FR-CONFIG-01 (Página Configurações Avançadas) — UPDATED

| Antes (v1.0.2) | Depois (v1.0.3) |
|---|---|
| "Toggle visual + 'Aplicar e reiniciar' (Streamlit)" | "Toggle visual + 'Aplicar e reiniciar' (uvicorn / `revisor-web`)" |

**Razão:** Mesma migração stack. Comportamento preservado.

#### FR-NEW: FR-CONFIG-02 — Aviso de perda de sessão antes de reiniciar (NOVO em v1.0.3 — Sati R-NEW-01)

- Antes de aplicar configurações que exigem reinício (`LLM_TIER`, `LLM_PROVIDER`, etc.), UI DEVE exibir modal de confirmação informando que sessão atual será perdida.
- Modal contém: lista de mudanças pendentes, botão "Aplicar e reiniciar" (destrutivo, vermelho), botão "Cancelar" (default).
- AC: 100% das mudanças que exigem reinício passam por modal antes da reinício efetivo (verificável via teste E2E).
- AC: Aviso contém microcopy explícito: "Esta ação reiniciará o servidor. Trabalho não-salvo desde o último veredito será perdido."

**Razão (Sati R-NEW-01):** PRD v1.0.2 menciona "Aplicar e reiniciar" mas não especifica UX de aviso. Lei de Hick + princípio de respeito ao usuário exigem confirmação destrutiva visível.

**Owner implementação:** UI-1 (story Sprint 02) ou story dedicada CONFIG-01.

#### F-HIGH-07 (Streamlit single-process bloqueia) — RESOLVED INCIDENTAL

| Status v1.0.2 | Status v1.0.3 |
|---|---|
| DEFERRED como tech debt | ✅ **RESOLVED INCIDENTAL** (REV-INT-01 substituiu Streamlit por FastAPI async-nativo) |

**Razão:** Migração stack tornou o problema inexistente. FastAPI + uvicorn handle concurrent requests nativamente via async event loop. Documentado para fechar tracking.

---

### Módulo: LGPD & On-Premise (impacto REV-INT-01)

#### NFR-LGPD-01 (100% on-premise + whitelist HTTP) — UPDATED com ressalva

| Antes (v1.0.2) | Depois (v1.0.3) |
|---|---|
| "Whitelist HTTP estrita: STJ + STF apenas. PDFs e dados do contrato nunca saem da máquina." | "Whitelist HTTP estrita: STJ + STF apenas para vault. PDFs e dados do contrato nunca saem da máquina. **Tech debt rastreável (TD-WEB-LGPD-CDN-01):** UI Web v0.1.0 puxa Google Fonts CDN — endereçado em REV-INT-02 (Sprint 02) com self-host fontes. Antes do release v0.2.0 público, UI será 100% offline."

**Razão (TD-WEB-LGPD-CDN-01):** Oracle QA Gate REV-INT-01 identificou Google Fonts CDN como leak de IP do operador. Não viola "PDFs e dados não saem" mas vaza metadata de uso. Mitigação obrigatória antes de v0.2.0.

**Status:** PENDING (story REV-INT-02 Sprint 02).

---

### Módulo: Setup, Backup e Recovery (impacto Sati R-NEW-03)

#### FR-NEW: FR-SETUP-02 — Mensagens de erro/WARN estruturadas em FR-SETUP-01 (NOVO em v1.0.3 — Sati R-NEW-03)

Estende FR-SETUP-01 e FR-BACKUP-01 com formato de erro/WARN especificado:

- Mensagens DEVEM seguir 4-bloco PT-BR estruturado (já adotado em STORY 13 hardening + STORY 14 docs):
  ```
  ❌ DIAGNÓSTICO: o que falhou em uma frase
  CAUSA: por que aconteceu (1-3 frases)
  SOLUÇÃO: o que fazer agora (passos numerados)
  ALTERNATIVA: workaround se solução principal não aplicável
  ```
- AC: 100% das mensagens de erro de FR-SETUP-01 (Ollama não encontrado, modelo não baixado, disco insuficiente) seguem formato 4-bloco.
- AC: 100% das mensagens de WARN de FR-BACKUP-01 (backup atrasado, espaço em disco baixo) seguem formato 4-bloco.
- AC: Reproduzir formato em SOPs (sop-populate-vault, sop-revisar-pdf) — cross-story consistency principle.

**Razão (Sati R-NEW-03):** PRD v1.0.2 não detalhava formato. STORY 13 hardening + STORY 14 docs estabeleceram padrão 4-bloco PT-BR consensus para mensagens. Documentar como contrato impede regressão.

**Owner implementação:** DEVOPS-01 (Ollama install errors) + DOCS-02 (atualizar SOPs com novos formatos REV-INT-01 e DEVOPS-01) — Sprint 02.

---

### Módulo: Pipeline Smoke E2E Real (Eric reclassificação sessão 85)

#### TD-PIPELINE-SMOKE-REAL (era pré-requisito Eric — agora work item @devops)

| Antes (v1.0.2 + Sprint 01 closure) | Depois (v1.0.3) |
|---|---|
| Owner: Eric (manual) — "Pré-requisito: Eric instala Ollama (~30min) + baixa Sabia-7B (~5GB) + Qwen 3B (~2GB)" | Owner: @devops (Operator) autônomo — story DEVOPS-01 Sprint 02 — "Operator instala Ollama Windows automatizado + pull Sabia-7B (via Modelfile customizado se não disponível em registry oficial — Maritaca AI distribui via Hugging Face) + pull qwen2.5:3b + smoke test pipeline integral" |

**Razão (Eric instrução sessão 85):** Eric explicitou que tarefas de ambiente devem ser automatizadas pelo sistema agentic, não manuais. Reclassificação alinha com Action Item Sprint 02 retrospective ("Setup Ollama documentado como pré-requisito de Sprint 02 OU criar STORY dedicada de setup automação").

**Risco a mitigar (story DEVOPS-01):** Sabia-7B pode não estar no Ollama registry oficial. Operator deve criar Modelfile customizado a partir de GGUF do Hugging Face Maritaca AI (`maritaca-ai/sabia-7b`), OU fallback Qwen 2.5 7B com aviso (LLM_TIER=balanced default temporário).

**Status:** PENDING (story DEVOPS-01 Sprint 02). Removido como pré-requisito Eric na lista 🚦 Próximos Passos do PROJECT-CHECKPOINT.

---

### Módulo: Web UI tech debts (REV-INT-01 closure — Sprint 02 incorporação)

7 debts catalogados em TECH-DEBT.md (apêndice REV-INT-01) incorporados oficialmente como debt do produto:

| Tech Debt ID | Resolução prevista | Story |
|---|---|---|
| TD-WEB-LGPD-CDN-01 (HIGH) | Antes de v0.2.0 | REV-INT-02 |
| TD-WEB-VAL-MIME-01 (MED) | Sprint 02 | UI-1 |
| TD-WEB-LISTENER-LEAK-01 (MED) | Sprint 02 | UI-1 |
| TD-WEB-NOMAXSIZE-01 (MED) | Sprint 02 | UI-1 |
| TD-WEB-SSE-NOSESSION-01 (LOW) | Sprint 02 | UI-1 |
| TD-WEB-TIER-ENUM-01 (LOW) | Sprint 02 | UI-1 |
| TD-WEB-CSP-INLINE-01 (LOW) | Defer Sprint 03+ (opcional) | — |

**Razão:** Documentar contratos. PRD não especificava antes desses debts existirem. Após UI-1 closure, FR-UPLOAD-01 (já existente) ganhará AC adicional de magic bytes server-side (já era NFR mas não estava na UI implementada).

---

### Módulo: R-NEW deferred (3 endereçadas, 3 deferred Sprint 03+)

| R-NEW ID | Severidade | Resolução v1.0.3 | Razão |
|---|---|---|---|
| **Sati R-NEW-01** (CONFIG-01 perda de sessão) | MEDIUM | ✅ ENDOSSADA — FR-CONFIG-02 NOVA | Microcopy spec UX clara |
| **Sati R-NEW-02** (RAG-02 vigência UI) | MEDIUM | ⏳ DEFERRED Sprint 03+ | Implementação UI complexa; FR-RAG-02 backend já tem vigente_em + superseded_by |
| **Sati R-NEW-03** (SETUP-01 + BACKUP-01 erro/WARN) | MEDIUM | ✅ ENDOSSADA — FR-SETUP-02 NOVA | Padrão 4-bloco já estabelecido em Sprint 01 |
| **Smith R-NEW-06** (HITL anti-bypass bigram bypassa-ável) | MEDIUM | ⏳ DEFERRED Sprint 03+ | Heurística rasa; precisa estudo NLP dedicado para alternativa |
| **Smith R-NEW-08** (FR-AUTH-04 IP fingerprint UX) | MEDIUM | ⏳ DEFERRED Sprint 03+ | Refatoração UX complexa; aceitável para MVP single-user |
| **Smith R-NEW-09** (vigência UI — endossa Sati R-NEW-02) | MEDIUM | ⏳ DEFERRED com Sati R-NEW-02 | Vinculadas semanticamente |

**Total v1.0.3:** 3 endereçadas (Sati R-NEW-01, Sati R-NEW-03 endossadas; F-HIGH-07 resolved incidental) + 3 deferred (mantidas em backlog Sprint 03+).

---

## Escopo Atual vs Original

- **v1.0.2:** 12 FRs principais + 9 NFRs + 9 DPs
- **v1.0.3:** 12 FRs (com 2 atualizações) + 2 FRs novos (FR-CONFIG-02, FR-SETUP-02) = 14 FRs + 9 NFRs (1 ressalva LGPD-01) + 9 DPs (sem mudança) + 7 web debts incorporados
- **Motivo principal:** REV-INT-01 stack migration + 3 R-NEW absorvidas + Sprint 02 plan publicado

---

## Action Items v1.0.3 Sprint 02

- [ ] **REV-INT-02** — Self-host Google Fonts (resolve TD-WEB-LGPD-CDN-01) — @dev (Neo) — 30min
- [ ] **DEVOPS-01** — Ollama autônomo install + smoke E2E real (resolve TD-PIPELINE-SMOKE-REAL) — @devops (Operator) — 1-2h dev + 30min setup + ~7GB download
- [ ] **UI-1** — Conectar UI ao pipeline real (resolve 5 web debts) — @architect → @dev → @qa — 3-5h
- [ ] **DOCS-02** — Atualizar README + SOPs para FastAPI + 2 R-NEW Sati endereçadas — @dev — 1-2h
- [ ] **OPS-CLEANUP-01** — Cleanup branch remoto + tag v0.1.0 alinhada — @devops — 15min
- [ ] **Release v0.2.0** — Após gate conditions (Sprint 02 plan §6) — @devops — 30min

---

## Changelog (append-only entry para PRD)

### v1.0.3 — 2026-05-05 (Morgan) — PATCH (Sprint 02 planning)

**Stack migration (REV-INT-01 closure):**
- UPDATED FR-AUTH-01: "Streamlit" → "FastAPI + HTMX + uvicorn"
- UPDATED FR-CONFIG-01: "reiniciar Streamlit" → "reiniciar uvicorn / `revisor-web`"
- RESOLVED-INCIDENTAL F-HIGH-07: Streamlit single-process bloqueia → não aplicável (FastAPI async-nativo)

**LGPD/On-Premise:**
- UPDATED NFR-LGPD-01: ressalva temporária para Google Fonts CDN — endereçado em REV-INT-02 antes de v0.2.0

**R-NEW endereçadas:**
- ENDORSED Sati R-NEW-01 → ADDED FR-CONFIG-02 (aviso de perda de sessão antes de reiniciar)
- ENDORSED Sati R-NEW-03 → ADDED FR-SETUP-02 (mensagens 4-bloco PT-BR em FR-SETUP-01 + FR-BACKUP-01)

**R-NEW deferred (Sprint 03+):**
- Sati R-NEW-02 (vigência UI), Smith R-NEW-06 (HITL anti-bypass), Smith R-NEW-08 (IP fingerprint UX), Smith R-NEW-09 (endossa R-NEW-02)

**Operacional:**
- RECLASSIFIED TD-PIPELINE-SMOKE-REAL: owner Eric → @devops (Operator) autônomo (Eric instrução sessão 85, story DEVOPS-01)
- INCORPORATED 7 web debts REV-INT-01 (TD-WEB-*) ao tracking do produto

**Estrutura — Atualizado:**
- ADDED 2 novos FRs: FR-CONFIG-02, FR-SETUP-02
- ADDED 1 ressalva NFR-LGPD-01 (temporária — endereçada antes de v0.2.0)
- CREATED `governance/sprint-02-plan.md` (companheiro deste DELTA)
- CREATED este DELTA section em `governance/prd/prd-v1.0.3-DELTA.md`

**Decisão pendente para Eric (não endereçada nesta versão):**
- DP-05 (política retenção LGPD 24h proposta) — humano confirma (sem mudança vs v1.0.2)
- Política de outcomes — quem registra (sem mudança vs v1.0.2)
- DEVOPS-01 sub-decisão: Sabia-7B custom Modelfile vs Qwen-only fallback (Operator decide com Eric durante story DEVOPS-01)

---

*PRD v1.0.3 DELTA — Morgan (sessão 85, 2026-05-05) · 2 atualizações stack + 2 FRs novos + 3 R-NEW endereçadas + 1 reclassificação ownership · Sprint 02 ready-for-execution.*

— Morgan, planejando o futuro 📊
