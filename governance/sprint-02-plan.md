---
type: sprint-plan
title: "Sprint 02 — Plan"
project: revisor-contratual
sprint: "02"
version: "1.0.0"
owner: "@pm (Morgan)"
date: "2026-05-05"
status: ready-for-execution
predecessor:
  - "Sprint 01 — closed (15 stories Done, MVP v0.1.0 release)"
  - "REV-INT-01 — merged em main commit f6b935c (UI redesign FastAPI+HTMX)"
  - "PRD v1.0.2 (PRD canônico anterior)"
delivers:
  - "governance/prd/prd-v1.0.3-DELTA.md (PATCH PRD)"
  - "Stories planejadas: 5 (REV-INT-02, UI-1, DEVOPS-01, VAULT-LOAD-TEST, DOCS-02)"
  - "Release candidate v0.2.0 (gate condition definida)"
tags:
  - project/revisor-contratual
  - sprint-plan
  - sprint-02
---

# Sprint 02 — Plan

> **Sprint 01 foi sobre **construir** o MVP. Sprint 02 é sobre **validar** o MVP empiricamente, **conectar** UI ao pipeline real e **endereçar** débitos antes do release v0.2.0 público.**

---

## 1. Objetivo do Sprint

| | |
|---|---|
| **Goal** | Entregar Revisor Contratual v0.2.0 com pipeline INTEGRAL validado empiricamente (Ollama real), UI conectada ao pipeline (não mais mock), e zero violações HIGH (LGPD CDN endereçada) |
| **Sucesso = entregar** | (a) primeiro veredito real de contrato PDF processado end-to-end, (b) UI Web exibe veredito real do pipeline, (c) release v0.2.0 publicada |
| **Duração estimada** | 12-18h dev autônomo (~2-3 sessões longas) |
| **Branch principal** | main (trunk-based, solo dev) |

---

## 2. Backlog consolidado

### 2.1 Origem do backlog

| Origem | Quantidade |
|---|---|
| **Sprint 01 closure** (TECH-DEBT.md original) | 13 active debts (2 MEDIUM + 11 LOW) + 1 active finding LOW |
| **REV-INT-01 closure** (TECH-DEBT.md apêndice) | 8 debts (1 HIGH + 3 MEDIUM + 4 LOW) — 1 já resolvido (TD-WEB-RUFF-UP037) |
| **PRD v1.0.2 deferred R-NEW** | 6 R-NEW (3 Sati + 3 Smith) para PATCH v1.0.3 |
| **Pendência operacional Sprint 01** | 1 (deletar feature branch remoto, item 14 PROJECT-CHECKPOINT) |
| **Lição aprendida sessão 81** | Setup Ollama documentado/automatizado (Action Item Sprint 02) |
| **Total** | **29 itens** (13 + 7 + 6 + 1 + 2) |

### 2.2 Mapa de prioridades (filtragem para v0.2.0)

| Prioridade | Critério | Itens | Ação |
|---|---|---|---|
| 🔴 **MUST (release blocker)** | Sem isso, v0.2.0 não sai | TD-WEB-LGPD-CDN-01, TD-PIPELINE-SMOKE-REAL, conexão UI↔pipeline | Stories REV-INT-02, DEVOPS-01, UI-1 |
| 🟡 **SHOULD (release-influencer)** | Reduz risco; já tem TD/PRD action | 4 web debts MEDIUM (UI-1 cluster), R-NEW Sati 1+3 | UI-1 absorve maioria; DOCS-02 absorve R-NEW Sati |
| 🟢 **COULD (Sprint 03+)** | Não bloqueia release; melhora qualidade | TD-VAULT-LOAD-TEST, R-NEW Sati 2 + Smith 6+8+9, TD-CI-* (4), TD-VAULT-* (3 LOW), TD-PIPELINE-* (2 LOW), TD-CLI-* (3) | Documentado no DELTA, defer |
| 🔵 **WON'T (não Sprint 02)** | Fora do tema do sprint | TD-VAULT-TJ (8h+ por TJ), R-NEW que dependem de outcomes reais | Mantido em TECH-DEBT |

---

## 3. Story breakdown

### 3.1 Stories Sprint 02 (propostas)

| Story ID | Título | Owner | Esforço | Bloqueia | Bloqueada por | Resolve |
|---|---|---|---|---|---|---|
| **REV-INT-02** | Self-host Google Fonts (LGPD on-premise) | @dev (Neo) | 30min | (release v0.2.0) | — | TD-WEB-LGPD-CDN-01 |
| **DEVOPS-01** | Ollama autônomo install + smoke E2E real | @devops (Operator) | 1-2h dev + 30min setup + ~7GB download | UI-1 (validação), v0.2.0 | — | TD-PIPELINE-SMOKE-REAL + Action Item Sprint 02 (setup automation) |
| **UI-1** | Conectar UI Web ao pipeline real (substituir mocks) | @architect → @dev → @qa | 3-5h | (release v0.2.0) | DEVOPS-01 (smoke validado) | TD-WEB-VAL-MIME-01, TD-WEB-LISTENER-LEAK-01, TD-WEB-NOMAXSIZE-01, TD-WEB-SSE-NOSESSION-01, TD-WEB-TIER-ENUM-01 |
| **DOCS-02** | Atualizar README + SOPs para FastAPI + 3 R-NEW Sati endereçadas | @dev | 1-2h | — | — | R-NEW-SATI-01 + R-NEW-SATI-03 (R-NEW-SATI-02 = UI-1) |
| **OPS-CLEANUP-01** | Cleanup branch remoto obsoleto + tag v0.1.0 alinhada com main | @devops | 15min | — | — | Pendência operacional Sprint 01 |

**Total Sprint 02:** 5 stories · ~7-12h dev efetivo + ~30min setup ambiente + ~7GB download

### 3.2 Stories deferred (Sprint 03+ ou WON'T)

| Item | Razão para defer | Quando entra |
|---|---|---|
| TD-VAULT-LOAD-TEST | Não bloqueia release; útil pré-scaling | Sprint 03 |
| R-NEW-SMITH-06 (HITL anti-bypass) | Heurística rasa precisa estudo NLP dedicado | Sprint 03+ |
| R-NEW-SMITH-08 (IP fingerprint UX) | Mudança UX complexa; FR-AUTH-04 atual aceitável MVP | Sprint 03+ |
| R-NEW-SMITH-09 / R-NEW-SATI-02 (vigência UI) | Já parcialmente implementado em FR-RAG-02; UX refinement Sprint 03 | Sprint 03 |
| TD-CI-COVERAGE-REPORTER | Cobertura local-only suficiente; reporter externo é nice-to-have | Sprint 03 |
| TD-VAULT-TJ | 8h+ por TJ; precisa estratégia de prioridade UF | Sprint 04+ |
| F-CI-LOW-01 | Hipotético (sem cross-package real ainda) | Quando primeira dep cross-package surgir |
| 8 outros LOW (TD-CLI-*, TD-VAULT-LEGAL-BERTIMBAU, TD-PIPELINE-*) | Não-bloqueantes; refinements pós-uso real | Sprint 03+ ou indefinido |

---

## 4. Dependency graph

```
                   ┌─ REV-INT-02 ──┐
                   │  (independente)│
                   ▼                │
                ✅ [paralelo]       │
                                    │
   DEVOPS-01 ─────────► UI-1 ───────┼─► v0.2.0 release
   (Ollama install)    (conecta     │
                        pipeline)    │
                                    │
   DOCS-02 ──────────────────────────┘
   (paralelo, sem deps)              │
                                    │
   OPS-CLEANUP-01 ───────────────────┘
   (paralelo, sem deps)
```

**Caminho crítico:** DEVOPS-01 → UI-1 (depende de Ollama instalado para smoke real)
**Paralelizável:** REV-INT-02, DOCS-02, OPS-CLEANUP-01 podem rodar em qualquer momento

---

## 5. Ordem de execução sugerida

### Fase A — Quick wins paralelos (~1h total)

1. **REV-INT-02** — self-host fontes (resolve único HIGH, 30min)
2. **OPS-CLEANUP-01** — cleanup branch remoto (15min)
3. **DOCS-02** começa (paralelo, ~1-2h)

**Marco A:** zero HIGH ativos no projeto.

### Fase B — Validação empírica (~2-3h)

4. **DEVOPS-01** — Ollama install autônomo + smoke E2E real
   - **Decisão técnica pré-execução:** Sabia-7B precisa Modelfile customizado (não está no Ollama registry oficial — Maritaca AI distribui via Hugging Face). Operator decide Modelfile vs Qwen-only fallback.

**Marco B:** primeiro veredito REAL de contrato PDF, 100% on-premise, validado empiricamente.

### Fase C — UI conectada (~3-5h)

5. **UI-1** — substitui mocks de `bloco_interface/web/app.py` por chamadas reais ao `bloco_workflow.pipeline`
   - **Pré-decisão arquitetural** (@architect Aria): SSE com session/job_id binding (resolve TD-WEB-SSE-NOSESSION-01) + magic bytes validation (TD-WEB-VAL-MIME-01) + max_size + Pydantic Enum tier + listener leak fix
   - Sidebar histórico real consumindo `audit.jsonl`

**Marco C:** UI Web exibe veredito real do pipeline.

### Fase D — Release v0.2.0 (~30min)

6. **OPS — release v0.2.0** — Operator cria tag, gera changelog, publica GitHub Release alinhada com main HEAD pós-Sprint-02

**Marco D:** v0.2.0 publicada.

---

## 6. Release v0.2.0 — gate conditions

Para fechar Sprint 02 e publicar v0.2.0, todos abaixo MUST estar verdes:

| # | Gate | Validador | Status atual |
|---|---|---|---|
| 1 | TD-WEB-LGPD-CDN-01 RESOLVED (zero CDN externos em base.html) | @qa Oracle smoke probe | ❌ Pending (REV-INT-02) |
| 2 | TD-PIPELINE-SMOKE-REAL RESOLVED (smoke E2E real verde com Ollama) | @qa Oracle ou @devops smoke runner | ❌ Pending (DEVOPS-01) |
| 3 | UI conectada ao pipeline real (não mais mock) | @qa Oracle browser test E2E | ❌ Pending (UI-1) |
| 4 | Suite testes ≥232 passed (zero regressão Sprint 01) | pytest local + CI green | ✅ Atualmente 232/1 |
| 5 | Zero CRITICAL findings novos | Oracle gate cumulativo Sprint 02 | ✅ Atualmente 0 |
| 6 | PRD v1.0.3 PATCH publicado | @pm + Oracle review | ❌ Pending (este planning) |
| 7 | TECH-DEBT.md atualizado por story (não acumular ao final) | Cada story Done atualiza | ✅ Princípio Sprint 02 |
| 8 | Conventional commit + push + tag v0.2.0 | @devops exclusive | ❌ Pending Marco D |

**Out-of-scope para v0.2.0:** TD-VAULT-LOAD-TEST, R-NEW Smith 6/8/9, R-NEW Sati 2 (UI vigência), 8 outros LOW.

---

## 7. Riscos & mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| **Sabia-7B não disponível em Ollama registry oficial** | ALTA (Maritaca distribui via HF) | Bloqueia DEVOPS-01 path principal | Operator cria Modelfile customizado a partir de GGUF do HF; OU fallback Qwen 2.5 7B com aviso (LLM_TIER=balanced default) |
| **Ollama install falha em Windows 11** | BAIXA | Bloqueia smoke E2E | Usar instalador oficial Ollama Windows + WSL fallback; documentar troubleshooting |
| **Pipeline real falha em primeiro PDF** | MÉDIA (mocks ≠ realidade) | Bloqueia UI-1 | Smoke executar com PDF golden set conhecido; iterar até 1 sucesso completo antes de UI-1 |
| **Self-host fontes quebra render** | BAIXA | Bloqueia REV-INT-02 | Smoke browser test obrigatório pós-deploy fontes; rollback rápido |
| **UI-1 SSE com pipeline real introduce race conditions** | MÉDIA | Bloqueia release | Aria desenha session/job_id binding antes de Neo implementar; @qa adversarial probe SSE concurrent jobs |
| **Suite testes quebra com pipeline real** | BAIXA-MÉDIA | Regressão Sprint 01 | Todos testes existentes usam mocks injetados; UI-1 deve preservar essa interface (testes continuam mockados) |

---

## 8. Princípios Sprint 02

Aplicados desde a primeira story (lições Sprint 01):

1. **TECH-DEBT.md atualizado por story** (não acumular para closure) — `.claude/rules/tech-debt-governance.md`
2. **Pre-flight check obrigatório** em operações git remote (push, merge) — Action Item Sprint 01 retrospective
3. **Adversarial probes Python ao vivo** > probes textuais — confirmado em STORY 14 Sprint 01
4. **Cross-story consistency** — quando fix muda mensagem visível, docs DEVEM reproduzir exatamente
5. **PRD versionamento por milestone** — `.claude/rules/prd-governance.md` (review pós-epic)
6. **Squash merge + tag release** — estratégia limpa Sprint 01 confirmada
7. **Operator autônomo desde a primeira story** — Eric NÃO mais responsável por install Ollama (reclassificado em DEVOPS-01)

---

## 9. Mudanças PRD v1.0.2 → v1.0.3

DELTA completo em `governance/prd/prd-v1.0.3-DELTA.md`. Resumo:

| Tipo | Item | Origem |
|---|---|---|
| **PATCH** | FR-AUTH-01 — "Streamlit" → "FastAPI uvicorn" | REV-INT-01 |
| **PATCH** | FR-CONFIG-01 — "reiniciar Streamlit" → "reiniciar uvicorn / `revisor-web`" | REV-INT-01 |
| **PATCH** | F-HIGH-07 (Streamlit single-process bloqueia) → RESOLVED (incidental REV-INT-01) | REV-INT-01 |
| **MINOR** | FR-NEW (R-NEW-SATI-01 endossada) — FR-CONFIG-01 estendida com warning de perda de sessão | Sati R-NEW-01 |
| **MINOR** | FR-NEW (R-NEW-SATI-03 endossada) — FR-SETUP-01 + FR-BACKUP-01 formato erro/WARN especificado | Sati R-NEW-03 |
| **MINOR** | NFR-LGPD-01 ressalva temporária — Google Fonts CDN documentado como tech debt resolvido em REV-INT-02 | TD-WEB-LGPD-CDN-01 |
| **MINOR** | TD-PIPELINE-SMOKE-REAL reclassificado — owner Eric → @devops Operator autônomo | Eric instrução sessão 85 |
| **DOCUMENTAR** (defer) | R-NEW-SATI-02, R-NEW-SMITH-06/08/09 — endereçados em Sprint 03+ | PRD changelog |

---

## 10. Próxima ação

Após esta plan ser aprovada por Eric, Morpheus dispatchará:

1. **DEVOPS-01** primeiro (Ollama install — pode rodar paralelo a outras stories porque download é background) → @devops (Operator)
2. **REV-INT-02** segundo (rápido, paralelizável) → @sm cria story → @dev (Neo) implementa
3. **DOCS-02** terceiro (paralelo, sem deps) → @sm cria story → @dev (Neo) escreve
4. **UI-1** quarto (depende de DEVOPS-01 verde) → @architect (Aria) decide arquitetura SSE binding → @sm story → @dev → @qa
5. **OPS-CLEANUP-01** em qualquer momento conveniente

Cada story segue o pipeline LMAS estrito (@sm → @po → @dev → @qa → @devops).

---

*Sprint 02 plan — Morgan (sessão 85, 2026-05-05) · 5 stories · v0.2.0 release candidate*

— Morgan, planejando o futuro 📊
