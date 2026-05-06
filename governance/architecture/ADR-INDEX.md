---
type: dashboard
title: "ADR Index — Revisor Contratual"
project: revisor-contratual
last_updated: "2026-05-05"
status: active
sprint: "03"
etapa: "Phase 0 — Architectural Foundation (ADR-011 + ADR-012)"
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
| [ADR-007](adr/adr-007-schema-sqlite-vec.md) | Schema sqlite-vec final + estratégia de índices | ✅ Accepted | 2026-05-01 | DP-08 (load test) |

### Pipeline & Scraping

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-008](adr/adr-008-pipeline-scraping-multi-uf.md) | Pipeline scraping multi-UF + heartbeat semanal | ✅ Accepted | 2026-05-01 | R-NEW-SMITH-05 (false negative) |

### LGPD & Backup

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-009](adr/adr-009-backup-dir-pseudonimizacao-lgpd.md) | BACKUP_DIR external path + pseudonimização HMAC LGPD | ✅ Accepted | 2026-05-01 | R-NEW-SMITH-01 + R-NEW-SMITH-07 |

### Infra & Runtime (Sprint 03)

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-011](adr/adr-011-auto-ollama-lifecycle.md) | Auto-Ollama Lifecycle Management — subprocess Python + detect-then-spawn | ✅ Accepted | 2026-05-05 | Setup manual Eric (Ollama desktop + 2ª instância manual) + AC-9 smoke E2E real bloqueado v0.2.0 |

### Data & Vault (Sprint 03)

| ADR | Título | Status | Data | Absorve |
|-----|--------|--------|------|---------|
| [ADR-012](adr/adr-012-vault-data-bundling.md) | Vault Data Bundling Strategy — bundled dataset + optional refresh scrapers | ✅ Accepted | 2026-05-05 | STJ scraper fragility (HTML changed) + STF SSL/anti-bot AWS ELB + AC-9 smoke E2E real bloqueado |

---

## Arquivados

*Nenhum ADR superseded até o momento.*

---

## Pendências para próximas iterações (não-bloqueantes)

| Item | Origem | Próxima ADR? |
|------|--------|--------------|
| Política retenção LGPD (DP-05) | PRD v1.0.2 | ADR-013+ (re-numerada — ADR-011 + ADR-012 alocados Sprint 03 Phase 0) |
| Política outcomes registry | PRD v1.0.2 | ADR-014+ (re-numerada) |
| R-NEW Sati R-NEW-01..03 (UX) | qa/sati-ux-rereview | PATCH PRD v1.0.3 (não-arquitetural) |
| R-NEW-SMITH-06 (HITL anti-bypass refinement) | qa/smith-adversarial-rereview | PATCH PRD v1.0.3 |
| R-NEW-SMITH-08 (IP fingerprint UX mobilidade) | qa/smith-adversarial-rereview | PATCH PRD v1.0.3 |
| R-NEW-SMITH-09 (vigência citação UI) | qa/smith-adversarial-rereview | Endossa Sati R-NEW-02 |

---

## Estatísticas

- **ADRs ativas (accepted):** 12 (ADR-001..012)
- **ADRs proposed (aguardando Eric):** 0
- **Sprint 03 Phase 0 ADRs:** 2 (ADR-011 OLLAMA Lifecycle + ADR-012 Vault Data Bundling — ambos accepted Eric 2026-05-05)
- **ADRs deprecadas/superseded:** 0
- **R-NEW absorvidas em ADRs:** 7 (Smith-01, -02, -03, -04, -05, -07, -10)
- **Tech debts absorvidos em ADRs (Sprint 02):** 2 (TD-LLM-SABIA-Q4-OUTPUT + TD-LLM-FORMAT-JSON-ECONOMISTA via ADR-010)
- **R-NEW diferidas para PATCH v1.0.3:** 6 (Sati R-NEW-01..03 + Smith-06, -08, -09 endossando)
- **Decisões pendentes Eric:** 2 (DP-05 LGPD retenção, outcomes registry) — ADR-010 Path C aprovado sessão 86

---

*Aria, mantendo o índice como mapa vivo da arquitetura. 🏗️*
