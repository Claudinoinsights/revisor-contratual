---
type: dashboard
title: "ADR Index — Revisor Contratual"
project: revisor-contratual
last_updated: "2026-05-15"
status: active
sprint: "6.x AGGRESSIVE"
etapa: "Phase 14.1+ Sprint 6.x — ADR-023/024/025 ACCEPTED 2026-05-15 (Sequential LLM Inference + Redator Tier Strategy audit-honored + Cascade Fallback graceful degradation — Eric directive 'nível melhor que adequado'). ADR-021 Dual Content-Type POST /revisar ACCEPTED 2026-05-14. ADR-020 Multi-Doctype Dispatcher v2 ACCEPTED 2026-05-09."
maintained_by: "@architect (Aria)"
tags:
  - project/revisor-contratual
  - dashboard
  - adr-index
  - architecture
---

# ADR Index — Revisor Contratual

```
[@architect · Aria (Visionary)] — etapa 2.0 · ADR Index canônico
SPRINT: 01 · ETAPA: 2.0 · DOMÍNIO: SoftwareDev/legaltech
```

> **Nota Aria:** ADRs criadas na Etapa 2.0 da Sprint 01 com base em PRD v1.0.2 (score 8.7/10) validado por 2 iterações de tribunal severo. Cada ADR rastreia seu DP-ID/F-ID/EV-ID origem em `prd/prd-v1.0.2.md`, `qa/smith-adversarial-rereview-prd-v1.0.2.md` ou `qa/sati-ux-rereview-prd-v1.0.2.md`.

---

## Por Domínio

### Estado & Workflow

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-001](adr/adr-001-gerenciamento-de-estado.md) | Gerenciamento de estado: LangGraph + SqliteSaver | ✅ Accepted | 2026-05-01 | R-NEW-SMITH-10 (PRAGMA integrity_check) |

### Design System & UX

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-002](adr/adr-002-design-system.md) | Design system: Streamlit nativo + tokens CSS injetados | ✅ Accepted | 2026-05-01 | Notas Sati Seção 4 (anexo UX) |

### Personas Internas

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-003](adr/adr-003-implementacao-tecnica-4-personas.md) | Implementação técnica das 4 personas internas | ✅ Accepted | 2026-05-01 | DP-04 (threshold Juiz) |
| [ADR-010](adr/adr-010-sabia-q4-mitigation.md) | Mitigação TD-LLM-SABIA-Q4-OUTPUT — fallback Qwen 7B + LLM_TIER configurable | ✅ Accepted | 2026-05-05 | TD-LLM-SABIA-Q4-OUTPUT (HIGH arquitetural) + TD-LLM-FORMAT-JSON-ECONOMISTA |

### Segurança & Audit

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-004](adr/adr-004-validacao-semantica-citacoes.md) | Validação semântica de citações: similarity + NLI híbrido | ✅ Accepted | 2026-05-01 | R-NEW-SMITH-02 (paráfrase invertida) |
| [ADR-005](adr/adr-005-audit-log-integrity-hmac.md) | Audit log integrity: hash chain Merkle com HMAC GENESIS | ✅ Accepted | 2026-05-01 | R-NEW-SMITH-03 (GENESIS anchor) |
| [ADR-006](adr/adr-006-preview-seguro-pdf.md) | Preview seguro de PDF: server-side rendering via pdf2image | ✅ Accepted | 2026-05-01 | R-NEW-SMITH-04 (iframe XSS) |

### Vault & RAG

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| ~~[ADR-007](adr/adr-007-schema-sqlite-vec.md)~~ | ~~Schema sqlite-vec final + estratégia de índices~~ | 🔄 Superseded by ADR-017 | 2026-05-01 | DP-08 (load test) |

### Pipeline & Scraping

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-008](adr/adr-008-pipeline-scraping-multi-uf.md) | Pipeline scraping multi-UF + heartbeat semanal | ✅ Accepted | 2026-05-01 | R-NEW-SMITH-05 (false negative) |

### Legal Compliance & LGPD

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-019](adr/adr-019-dpa-storage-schema.md) | DPA Storage Schema — Multi-Tenant Acceptance Tracking with Audit Evidence (level=spec) | ✅ Accepted | 2026-05-07 | Smith F-012 CRITICAL (ANPD audit defensible) |
| ~~[ADR-009](adr/adr-009-backup-dir-pseudonimizacao-lgpd.md)~~ | ~~BACKUP_DIR external path + pseudonimização HMAC LGPD~~ | 🔄 Superseded by ADR-017 | 2026-05-01 | R-NEW-SMITH-01 + R-NEW-SMITH-07 |

### Infra & Runtime (Sprint 03)

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| ~~[ADR-011](adr/adr-011-auto-ollama-lifecycle.md)~~ | ~~Auto-Ollama Lifecycle Management — subprocess Python + detect-then-spawn~~ | 🔄 Superseded by ADR-014 | 2026-05-05 | Setup manual Eric + AC-9 smoke E2E real bloqueado v0.2.0 |

### Data & Vault (Sprint 03)

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-012](adr/adr-012-vault-data-bundling.md) | Vault Data Bundling Strategy — bundled dataset + optional refresh scrapers | ✅ Accepted | 2026-05-05 | STJ scraper fragility + STF SSL/anti-bot + AC-9 smoke E2E real bloqueado |

### MVP Lean Strategy & Deployment (Sprint 03 course-correction)

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| ~~[ADR-013](adr/adr-013-mvp-lean-strategy-deployment-path.md)~~ | ~~MVP Lean Strategy + Deployment Path — 5 decisões consolidadas~~ | 🔄 Superseded by ADR-015 (parcial — Vision OCR pivot) | 2026-05-06 | PRD v1.1.2.1 caminho híbrido + Smith re-review #2 PASS |

### Multi-Tenant Architecture (Sprint 04 — BACKBONE)

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-017](adr/adr-017-multi-tenant-isolation-rls.md) | Multi-Tenant Pool+RLS + LGPD Operador (BACKBONE) — supersedes ADR-007 + ADR-009 | ✅ Accepted | 2026-05-07 | Atlas v2 Section 2+4 + Smith CC.41 cloud pivot motivation |

### Provider & LLM Stack (Sprint 04)

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-014](adr/adr-014-provider-abstraction-byok.md) | Provider Abstraction Anthropic + BYOK + pgcrypto — supersedes ADR-010 + ADR-011 | ✅ Accepted | 2026-05-07 | Atlas v2 Section 1 + Eric A1 Anthropic only Phase 1.7 |
| [ADR-015](adr/adr-015-vision-ocr-architecture.md) | Vision OCR Architecture — Sonnet 4.6 vision + caching SHA-256 (partial supersede ADR-013) | ✅ Accepted | 2026-05-07 | Atlas v1 vision OCR landscape + Smith CC.41 RAM constraint |
| ~~[ADR-016](adr/adr-016-multi-doctype-dispatcher.md)~~ | ~~Multi-Doctype Dispatcher Strategy — 4 doctypes (FIES/Veicular/Bancário/Imobiliário)~~ | 🔄 Superseded by ADR-020 | 2026-05-07 | Eric escopo B Phase 1.7.1 + Atlas v2 doctype strategy |
| [ADR-020](adr/adr-020-multi-doctype-dispatcher-v2.md) | Multi-Doctype Dispatcher v2 — Strategy hierárquica 7 doctypes (CCB/Veículo/Consignado/Cartão/Imobiliário/FIES/Geral) com BancarioBaseStrategy + GeralDispatcher catch-all (level=spec) | ✅ Accepted | 2026-05-09 | Eric SPA OrSheva 7 (DEC-ERIC-DIV-01 + RATIFY Opção A) — supersedes ADR-016 |

### Frontend-Backend Integration (Sprint 6 Bloco β)

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-021](adr/adr-021-dual-content-type-post-revisar.md) | Dual Content-Type para POST /revisar — JSON (SPA) + HTML (Jinja2 legacy) — pattern mirror POST /login | ✅ Accepted | 2026-05-14 | TD-SP06-SPA-CONNECT-01 Wave 2 unblock (Sprint 6 AGGRESSIVE) |

### AI/LLM Pipeline (Sprint 6 Bloco γ)

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-022](adr/adr-022-persona-redator-revisional.md) | Persona Redator Revisional — sabia-7b primary + Qwen 2.5 7B fallback + hardening anti-hallucination (Pydantic strict + vault-restricted citations + validador post-LLM) | ✅ Accepted | 2026-05-14 | PRD-SP06-GAMMA v0.1.0 + Smith Fase 7-A gap (backend não gera peça revisional formal) + Smith Bloco β F-D3-β-06 SSE-OWNERSHIP-CHECK |
| [ADR-023](adr/adr-023-sequential-llm-inference.md) | Sequential LLM Inference (Advogado → Economista) — F-PROD-NEW-18 Capacity Resolution | ✅ Accepted | 2026-05-15 | F-PROD-NEW-18 (VPS load 151 → 0.17 baseline) + Smith D-SMITH-S06-015 + Operator D-OPS-S06-017b capacity discovery |
| [ADR-024](adr/adr-024-redator-tier-strategy.md) | Redator Tier Strategy — Audit-Honored Tier Parameter (Caminho C) — TIER_TO_MODEL_REDATOR all-3b mapping + audit chain `redator_tier_consumed` intent capture | ✅ Accepted | 2026-05-15 | Smith F-S21-03 HIGH + TD-SP07-TIER-SEMANTIC-DECISION + Neo D-DEV-S06-023 DeprecationWarning band-aid |
| [ADR-025](adr/adr-025-redator-cascade-fallback-strategy.md) | Redator Cascade Fallback Strategy — Graceful Degradation Synthetic (Caminho A) — synthetic RelatorioInviabilidade em vez de fallback qwen2.5:7b cascade risk | ✅ Accepted | 2026-05-15 | Smith F-S21-05 MEDIUM + TD-SP07-REDATOR-FALLBACK-CASCADE-RISK + F-PROD-NEW-19 audit evidence 2026-05-15T15:55:43 |

### SaaS Pricing & Billing (Sprint 04)

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-018](adr/adr-018-saas-pricing-billing-event.md) | SaaS Pricing Hybrid + Billing State Machine — per-approval billing + Stripe webhook | ✅ Accepted | 2026-05-07 | Eric D-c per-approval Phase 1.7.1 + Atlas v2 Section 3 pricing ranges |

---

## Arquivados (Superseded)

| ADR | Motivo | Superseded By |
|-----|--------|---------------|
| ADR-007 | Migração SQLite → PostgreSQL multi-tenant | ADR-017 |
| ADR-009 | Migração LGPD on-premise → LGPD operador SaaS | ADR-017 |
| ADR-010 | Migração Sabia/Qwen local → Anthropic cloud | ADR-014 |
| ADR-011 | Migração Ollama local → Anthropic API cloud (sem Ollama) | ADR-014 |
| ADR-013 (parcial) | Substituição parcial OCR local → Vision OCR cloud | ADR-015 |
| ADR-016 | Expansão 4 → 7 doctypes operacionais via SPA OrSheva 7 sidebar (DEC-ERIC-DIV-01 Opção A) | ADR-020 |

---

## Pendências para próximas iterações (não-bloqueantes)

| Item | Origem | Próxima ADR? |
|------|--------|--------------|
| Política retenção LGPD (DP-05) | PRD v1.0.2 | ADR-014+ (re-numerada — ADR-011/012/013 alocados Sprint 03) |
| Política outcomes registry | PRD v1.0.2 | ADR-015+ (re-numerada) |
| R-NEW Sati R-NEW-01..03 (UX) | qa/sati-ux-rereview | PATCH PRD v1.0.3 (não-arquitetural) |
| R-NEW-SMITH-06 (HITL anti-bypass refinement) | qa/smith-adversarial-rereview | PATCH PRD v1.0.3 |
| R-NEW-SMITH-08 (IP fingerprint UX mobilidade) | qa/smith-adversarial-rereview | PATCH PRD v1.0.3 |
| R-NEW-SMITH-09 (vigência citação UI) | qa/smith-adversarial-rereview | Endossa Sati R-NEW-02 |

---

## Estatísticas

- **ADRs ativas (accepted):** 15 (ADR-001..006, 008, 012, 014..015, 017..020) — ADR-016 superseded por ADR-020 em 2026-05-09 + ADR-020 ratify Accepted Eric quote literal 2026-05-09 (post-Smith H1 flip)
- **ADRs proposed (aguardando Eric):** 0
- **Sprint 03 Phase 0 ADRs:** 2 (ADR-012 Vault Data Bundling accepted; ADR-013 partial superseded por ADR-015)
- **Sprint 04 ADRs novos:** 7 (ADR-014..019 + ADR-020 — pivot SaaS BYOK cloud + 7 doctypes UX)
- **ADRs deprecadas/superseded:** 6 (ADR-007 → ADR-017, ADR-009 → ADR-017, ADR-010 → ADR-014, ADR-011 → ADR-014, ADR-013 partial → ADR-015, ADR-016 → ADR-020)
- **R-NEW absorvidas em ADRs:** 7 (Smith-01, -02, -03, -04, -05, -07, -10) + 1 Smith F-012 (ADR-019 Sprint 04)
- **Tech debts absorvidos em ADRs:** 2 Sprint 02 (TD-LLM-SABIA-Q4 + TD-LLM-FORMAT-JSON via ADR-010 superseded)
- **Tech debts NEW Sprint 04 ADR-020:** 2 (TD-SP04-12 vault re-classify + TD-SP04-13 vault gaps Cartão/Consignado curadoria)
- **Smith CRITICAL findings fechados via ADRs:** 1/4 (F-012 via ADR-019; F-003+F-007 via PRD v2.0.1; F-016 cross-domain Eric)
- **R-NEW diferidas para PATCH v1.0.3:** 6 (Sati R-NEW-01..03 + Smith-06, -08, -09 endossando) — Sprint 03 anchor
- **Decisões pendentes Eric:** 3 (DP-05 LGPD retenção, outcomes registry, ADR-020 ratify Accepted) — Sprint 06+ + sessão atual
- **Path A chain progress (Sprint 04 Phase 5):** 3/6 done (Operator commit Smith report ✅, Trinity PRD patches ✅, Aria ADR-019 ✅)
- **Sprint 04 Phase 14 (UI integration):** 1 ADR (ADR-020 Proposed) — desbloqueia SP04-UI-SPA-01 + SP04-DOCTYPE-01 NEW

---

## Nota Glossário PRDs Cross-Version (v2.0.4 — F-D4-LOW-01)

**Para leitores futuros:** Esta nota documenta que os PRDs v1.x.x (Sprint 01 + Sprint 03 anchor — `prd-v1.0.x.md` + `prd-v1.1.x.md`) usam **"Eric"** tanto como **founder/decision-maker** quanto como **operador estrutural** (pré-pivot SaaS BYOK + pré-glossário Orsheva introduzido em PRD v2.0.3).

**A partir do PRD v2.0.3 (2026-05-12):** distinção semântica explícita aplicada via frontmatter `entities`:
- **Orsheva** = entidade empresarial (operador LGPD, Admin super-user, role estrutural)
- **Eric Claudino** = founder Orsheva (decision-maker histórico — autorizações pivot, ratifications, ADR decision_maker)

**Canonical Sprint 04+:** ler PRD v2.0.4 ou posterior (`prd-v2.0.1-DOCTYPE-CONTENT-PATCH.md` canônico). PRDs v1.x.x preservados como histórico Sprint 01/03 — **não atualizados retroativamente** (Morgan 0c scope decision documentada em PRD v2.0.3 Changelog).

**Status review v2.0.4:** Smith F-D4-LOW-01 endereçado via esta nota.

---

*Aria, mantendo o índice como mapa vivo da arquitetura. 🏗️*
