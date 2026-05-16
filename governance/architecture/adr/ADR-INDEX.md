---
type: dashboard
title: "ADR Index — Revisor Contratual"
project: revisor-contratual
last_updated: "2026-05-16"
total_adrs: 30
active_adrs: 24
superseded_adrs: 4
deprecated_adrs: 1
proposed_adrs: 4
tags:
  - project/revisor-contratual
  - adr
  - dashboard
  - moc
---

# ADR Index — Revisor Contratual

> **MOC (Map of Content)** seguindo `adr-governance.md` — agrupamento por domínio (NÃO sequencial numérica). Superseded ADRs em seção separada com strikethrough.
> **Created:** 2026-05-16 (Sprint 8 Phase B Story #11, junto com ADR-031).
> **Total ADRs:** 30 (ADR-001 → ADR-031, ADR-030 reserved para offsite backup Sprint 9+).

---

## Por Domínio

### Backup, Encryption & LGPD Compliance

| ADR | Título | Status | Data |
|-----|--------|--------|------|
| [ADR-005](adr-005-audit-log-integrity-hmac.md) | Audit log integrity: HMAC chain Merkle + GENESIS anchor | ✅ Accepted | 2026-05-01 |
| ~~[ADR-009](adr-009-backup-dir-pseudonimizacao-lgpd.md)~~ | ~~BACKUP_DIR external path + pseudonimização HMAC LGPD~~ | 🔄 Superseded by ADR-029 | 2026-05-01 |
| [ADR-019](adr-019-dpa-storage-schema.md) | DPA Storage Schema — Multi-Tenant Acceptance Tracking | ✅ Accepted | 2026-05-07 |
| [ADR-029](adr-029-backup-strategy.md) | Backup Strategy — APScheduler Embedded + Visibility + Retention 30d | ✅ Accepted (§3 amended by ADR-031) | 2026-05-16 |
| [ADR-031](adr-031-backup-encryption.md) | Backup Encryption — restic AES-256-CTR + Poly1305 MAC (Defense-in-Depth) | ✅ Accepted | 2026-05-16 |
| ADR-030 *(reserved)* | Offsite Backup S3/B2/Hetzner (Sprint 9+ future) | 🔲 Planned | — |

### Security & Audit

| ADR | Título | Status | Data |
|-----|--------|--------|------|
| [ADR-004](adr-004-validacao-semantica-citacoes.md) | Validação semântica citações: similarity + NLI híbrido | ✅ Accepted | 2026-05-01 |
| [ADR-006](adr-006-preview-seguro-pdf.md) | Preview seguro PDF server-side via pdf2image | ✅ Accepted | 2026-05-01 |
| [ADR-014](adr-014-provider-abstraction-byok.md) | Provider Abstraction Anthropic Only + BYOK Key Management | ✅ Accepted | 2026-05-07 |

### Personas & Orquestração LLM

| ADR | Título | Status | Data |
|-----|--------|--------|------|
| [ADR-003](adr-003-implementacao-tecnica-4-personas.md) | Implementação técnica 4 personas + threshold Juiz definitivo | ✅ Accepted | 2026-05-01 |
| ~~[ADR-010](adr-010-sabia-q4-mitigation.md)~~ | ~~Mitigação TD-LLM-SABIA-Q4-OUTPUT — fallback Qwen 7B com LLM_TIER~~ | 🔄 Superseded by ADR-024+025 | 2026-05-05 |
| [ADR-022](adr-022-persona-redator-revisional.md) | Persona Redator Revisional — sabia-7b primary + Qwen 2.5 fallback | ✅ Accepted | 2026-05-14 |
| [ADR-023](adr-023-sequential-llm-inference.md) | Sequential LLM Inference (Advogado → Economista) F-PROD-NEW-18 | ✅ Accepted | 2026-05-15 |
| [ADR-024](adr-024-redator-tier-strategy.md) | Redator Tier Strategy — Audit-Honored Tier Parameter (Caminho C) | ✅ Accepted | 2026-05-15 |
| [ADR-025](adr-025-redator-cascade-fallback-strategy.md) | Redator Cascade Fallback Strategy — Graceful Degradation Synthetic (Caminho A) | ✅ Accepted | 2026-05-15 |

### Infraestrutura & Runtime

| ADR | Título | Status | Data |
|-----|--------|--------|------|
| ~~[ADR-011](adr-011-auto-ollama-lifecycle.md)~~ | ~~Auto-Ollama Lifecycle Management — subprocess Python + detect-then-spawn~~ | 🔄 Superseded by ADR-028 | 2026-05-05 |
| [ADR-012](adr-012-vault-data-bundling.md) | Vault Data Bundling Strategy — bundled dataset + optional refresh scrapers | ✅ Accepted | 2026-05-05 |
| ~~[ADR-013](adr-013-mvp-lean-strategy-deployment-path.md)~~ | ~~MVP Lean Strategy + Deployment Path~~ | ⚠️ Deprecated (Sprint 7+ stack evolved) | 2026-05-06 |
| [ADR-015](adr-015-vision-ocr-architecture.md) | Vision OCR Architecture — Claude Sonnet 4.6 + caching + multi-page paralelo | 🟡 Proposed | 2026-05-07 |
| [ADR-026](adr-026-marker-subprocess-isolation-parsing.md) | Marker Subprocess Isolation — RESOLVE F-PROD-NEW-22 silent worker exit (Sprint 7 Phase 3) | ✅ Accepted | 2026-05-15 |
| [ADR-027](adr-027-pymupdf-born-digital-fast-path.md) | PyMuPDF Born-Digital Fast Path — Dual-Path Pipeline Step 1 (Sprint 7 Phase 4) | ✅ Accepted | 2026-05-16 |
| [ADR-028](adr-028-ollama-single-container-consolidation.md) | Ollama Single-Container Consolidation — 2 → 1 ollama-shared (Cenário Y++ Phase 2) | ✅ Accepted | 2026-05-15 |

### Data, Schema & Multi-Tenancy

| ADR | Título | Status | Data |
|-----|--------|--------|------|
| ~~[ADR-007](adr-007-schema-sqlite-vec.md)~~ | ~~Schema sqlite-vec final + estratégia índices~~ | 🔄 Superseded (vault schema iterated) | 2026-05-01 |
| [ADR-008](adr-008-pipeline-scraping-multi-uf.md) | Pipeline scraping multi-UF + heartbeat semanal anti-false-negative | ✅ Accepted | 2026-05-01 |
| [ADR-017](adr-017-multi-tenant-isolation-rls.md) | Multi-Tenant Isolation PostgreSQL Pool+RLS + LGPD Operador | 🟡 Proposed | 2026-05-07 |

### Workflow & State Management

| ADR | Título | Status | Data |
|-----|--------|--------|------|
| [ADR-001](adr-001-gerenciamento-de-estado.md) | Gerenciamento estado: LangGraph + SqliteSaver com PRAGMA integrity_check + asyncio.gather paralelo | ✅ Accepted | 2026-05-01 |

### Frontend, Backend & Design

| ADR | Título | Status | Data |
|-----|--------|--------|------|
| [ADR-002](adr-002-design-system.md) | Design system: Streamlit nativo + tokens CSS injetados + tipografia serif jurídica + Lora local | ✅ Accepted | 2026-05-01 |
| [ADR-021](adr-021-dual-content-type-post-revisar.md) | Dual Content-Type POST /revisar — JSON (SPA) + HTML (Jinja2 legacy) | ✅ Accepted | 2026-05-14 |

### Business, Pricing & Doctype Strategy

| ADR | Título | Status | Data |
|-----|--------|--------|------|
| ~~[ADR-016](adr-016-multi-doctype-dispatcher.md)~~ | ~~Multi-Doctype Dispatcher v1 — Strategy Pattern 4 doctypes~~ | 🔄 Superseded by ADR-020 | 2026-05-07 |
| [ADR-018](adr-018-saas-pricing-billing-event.md) | SaaS Pricing Hybrid + Billing Event State Machine | 🟡 Proposed | 2026-05-07 |
| [ADR-020](adr-020-multi-doctype-dispatcher-v2.md) | Multi-Doctype Dispatcher v2 — Strategy hierárquica 7 doctypes (supersedes ADR-016) | ✅ Accepted | 2026-05-09 |

---

## Por Status

### ✅ Accepted (24 active decisions)

ADRs ativos representando decisões em vigor:

ADR-001, ADR-002, ADR-003, ADR-004, ADR-005, ADR-006, ADR-008, ADR-012, ADR-014, ADR-019, ADR-020, ADR-021, ADR-022, ADR-023, ADR-024, ADR-025, ADR-026, ADR-027, ADR-028, **ADR-029** (§3 amended), **ADR-031** (new)

### 🟡 Proposed (4 pending acceptance)

ADRs em discussão, ainda não aplicados em produção:

| ADR | Domínio | Bloqueio para Accept |
|-----|---------|----------------------|
| [ADR-015](adr-015-vision-ocr-architecture.md) | Vision OCR | Aguarda Sprint que active OCR (atualmente born-digital fast path ADR-027 cobre 95%+ casos) |
| [ADR-017](adr-017-multi-tenant-isolation-rls.md) | Multi-tenancy PostgreSQL RLS | Aguarda decisão SaaS B2B multi-tenant evolution (atual single-tenant Eric operador) |
| [ADR-018](adr-018-saas-pricing-billing-event.md) | SaaS pricing | Aguarda decisão pricing model concreto (BYOK customer pays direct API) |

### 🔄 Superseded (4 arquivados)

ADRs que foram substituídos por decisões posteriores:

| ADR Antigo | Superseded By | Motivo |
|-----------|---------------|--------|
| [ADR-007](adr-007-schema-sqlite-vec.md) | (vault schema iterated organically) | Schema evoluiu sem ADR formal substituto |
| [ADR-009](adr-009-backup-dir-pseudonimizacao-lgpd.md) | [ADR-029](adr-029-backup-strategy.md) | Backup strategy completa supersedes pseudonimização parcial |
| [ADR-010](adr-010-sabia-q4-mitigation.md) | [ADR-024](adr-024-redator-tier-strategy.md) + [ADR-025](adr-025-redator-cascade-fallback-strategy.md) | Tier strategy + cascade fallback expandem Q4 mitigation original |
| [ADR-011](adr-011-auto-ollama-lifecycle.md) | [ADR-028](adr-028-ollama-single-container-consolidation.md) | Single-container consolidation supersedes multi-container subprocess management |
| [ADR-016](adr-016-multi-doctype-dispatcher.md) | [ADR-020](adr-020-multi-doctype-dispatcher-v2.md) | v2 expandiu 4 → 7 doctypes hierárquicos |

### ⚠️ Deprecated (1 no longer recommended)

| ADR | Razão |
|-----|-------|
| [ADR-013](adr-013-mvp-lean-strategy-deployment-path.md) | MVP Lean Strategy — Sprint 7+ stack evolved significantly. §2.4 APScheduler decision preserved em ADR-029 cross-reference |

### 🔲 Reserved (1 pre-allocated future)

| ADR | Domínio | Planned For |
|-----|---------|-------------|
| ADR-030 | Offsite Backup (S3/B2/Hetzner Storage Box) | Sprint 9+ (leverages ADR-031 restic foundation) |

---

## Cross-Reference Map

### ADR Chains (supersede relationships)

```text
ADR-007 → (organic iteration, no formal supersedure)
ADR-009 → ADR-029 (backup strategy)
ADR-010 → ADR-024 + ADR-025 (tier + cascade)
ADR-011 → ADR-028 (single-container consolidation)
ADR-013 §2.4 → ADR-029 (APScheduler preserved cross-ref) + Deprecated overall
ADR-016 → ADR-020 (v1 → v2 dispatcher)
ADR-029 §3 → ADR-031 (encryption decision promoted)
```

### Related ADR Clusters (work-together patterns)

| Cluster | ADRs | Theme |
|---------|------|-------|
| **Backup & Encryption** | ADR-005 + ADR-029 + ADR-031 | HMAC audit + APScheduler + restic encryption |
| **LLM Pipeline** | ADR-003 + ADR-022 + ADR-023 + ADR-024 + ADR-025 | 4 personas + redator + sequential + tier + cascade |
| **Container Architecture** | ADR-026 + ADR-027 + ADR-028 | subprocess isolation + dual-path + ollama consolidation |
| **Multi-Doctype** | ADR-020 (supersedes ADR-016) | 7 doctypes hierárquicos |
| **Multi-Tenancy** | ADR-017 + ADR-018 + ADR-019 | RLS + pricing + DPA storage |

---

## Anti-Padrão Detection (per adr-governance.md)

Verificação periódica (Architect responsibility):

| Anti-Padrão | Status Revisor-Contratual 2026-05-16 |
|-------------|---------------------------------------|
| ADR sem "Razão" (por que essa decisão) | ✅ Compliant — todos ADRs têm Context + Decision com rationale |
| ADR sem "Alternativas Consideradas" | ✅ Compliant — padrão seguido (ADR-031 documenta 4 alternatives) |
| ADR superseded sem link para substituto | ✅ Compliant — supersede chain documentada acima |
| ADR Index não atualizado após novo ADR | ✅ Resolved — este index criado 2026-05-16 com ADR-031 |
| Múltiplos ADRs aceitos no mesmo domínio sem relação explícita | ⚠️ Watch — Backup cluster (ADR-005 + ADR-029 + ADR-031) relationships explícitos OK; LLM Pipeline cluster pode beneficiar de meta-ADR consolidator futuramente |

---

## Próximas Reviews Programadas (per adr-governance.md "Max 10 ADRs accepted per domain antes review")

| Domínio | ADRs Accepted | Review Trigger |
|---------|---------------|----------------|
| Personas & Orquestração LLM | 5 (ADR-003, 022, 023, 024, 025) | Continue OK — sob limite 10 |
| Infraestrutura & Runtime | 4 active (ADR-012, 026, 027, 028) | Continue OK |
| Backup & LGPD | 4 active (ADR-005, 019, 029, 031) + 1 superseded (ADR-009) | Continue OK |
| Backend | 3 (ADR-023, 024, 025) | Continue OK |

---

*ADR Index criado por @architect (Aria) 2026-05-16 — Sprint 8 Phase B Story #11. Reflete state pós-ADR-031 publicação. Mantido manualmente conforme adr-governance.md (sem ferramenta automated indexing nesta sprint).*
