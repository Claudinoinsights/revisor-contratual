---
type: dashboard
title: "PRD Index — Revisor Contratual"
project: revisor-contratual
last_updated: "2026-05-05"
tags:
  - project/revisor-contratual
  - prd-index
---

# PRD Index — Revisor Contratual

> **Owner:** @pm (Morgan). Versão ativa marcada com ⭐ ACTIVE.

## Versões

| Versão | Status | Bump | Arquivo | Data | Razão |
|---|---|---|---|---|---|
| **v1.1.2** | ⭐ **ACTIVE** | PATCH | [prd-v1.1.2-PATCH.md](./prd-v1.1.2-PATCH.md) | 2026-05-05 | Smith re-review CC.1A' endereçado (6/6 findings) — defense-in-depth LGPD (CSRF+CSP+encryption-at-rest) + cross-platform backup (APScheduler) + SOP-005 fallback Tema 1378 + D3 Apelação reestimado 6-8h. Eric escolheu opção B perfeição |
| v1.1.1 | superseded | PATCH | [prd-v1.1.1-PATCH.md](./prd-v1.1.1-PATCH.md) | 2026-05-05 | Tribunal CC.1A endereçado (14/14 findings) — FR-LGPD-MVP-01 + FR-MONITOR-01 ATIVO + FR-BACKUP-MVP-01 + FR-ECONOMISTA-01 + D3 Apelação + validação OAB |
| v1.1.0 | superseded | MAJOR | [prd-v1.1.0-MAJOR.md](./prd-v1.1.0-MAJOR.md) | 2026-05-05 | Course-correction Eric — caminho híbrido enxuto + roadmap 5 modalidades + decisão FIES projeto-irmão |
| v1.0.3 | superseded | PATCH | [prd-v1.0.3-DELTA.md](./prd-v1.0.3-DELTA.md) | 2026-05-05 | Sprint 02 planning — REV-INT-01 stack migration + 3 R-NEW absorvidas |
| v1.0.2 | superseded | PATCH | [prd-v1.0.2.md](./prd-v1.0.2.md) | 2026-05-01 | Tribunal severo etapa 1.1 — endereçando 6 CRITICAL + 11 HIGH Smith + 4 EV-ID Sati |
| v1.0.1 | superseded | PATCH | [prd-v1.0.1.md](./prd-v1.0.1.md) | 2026-04-XX | Pre-tribunal versão preliminar |

## Anexos

| Anexo | Arquivo | Owner |
|---|---|---|
| Integrations Detail | [integrations-detail-v1.0.md](./integrations-detail-v1.0.md) | @pm |
| UX Spec Detail v1.0 | [ux-spec-detail-v1.0.md](./ux-spec-detail-v1.0.md) | @ux-design-expert (Sati) |
| **UX Spec MVP-LEAN v1.1.0** (pending) | _governance/ux-spec-v1.1.0-MVP-LEAN.md_ (a criar — CC.3) | @ux-design-expert (Sati) |

## Roadmap modalidades (per v1.1.0)

| Versão | Modalidade | Status | Estimativa | ID Backlog |
|---|---|---|---|---|
| **v1.0 MVP** | CDC PF Veículos | em curso (course-correction CC.1A) | 25-35h restantes | n/a |
| v1.1 | Bancário Genérico (CDC não-veicular não-imobiliário) | roadmap | 20-30h | (story futura) |
| v1.2 | Imobiliária (CDC SFH/SFI) | roadmap | 30-40h | (story futura) |
| v1.3 | Crédito Bancário (cartão rotativo + cheque especial) | roadmap | 25-35h | (story futura) |
| Fase 2+ | **Revisor FIES** (projeto-irmão separado) | avaliação Sprint 04+ | a definir | BL-FIES |

## Backlog Deferred — fonte canônica em `governance/TECH-DEBT.md`

> **NOTA v1.1.1:** Backlog Deferred migrado para `governance/TECH-DEBT.md` como registry duradouro (mitigação F-CHK-02). PRD §11 lista resumo; TECH-DEBT.md é fonte de verdade canônica.

**14 BL-* entries em TECH-DEBT.md (atualização v1.1.1):**

| ID | Descrição | Versão alvo | Status v1.1.1 |
|---|---|---|---|
| BL-AUTH-01 | Auth elaborada (bcrypt + cookies + audit log tentativas) | v1.1+ | preservado (FR-LGPD-MVP-01 cobre MVP) |
| BL-AUTH-02 | Sessão IP fingerprint | v1.1+ | preservado |
| BL-DELIV-03 | D4 Comparativo Taxas | v1.1+ | preservado |
| BL-DELIV-04 | D5 Parcelas Reais Incontroversas | v1.1+ | preservado |
| BL-DELIV-05a | Embargos Declaração + Agravo + Recurso Especial | v1.1+ | **splitado em v1.1.1** (D3 Apelação Cível incorporada MVP) |
| BL-MULTI-UF | Multi-UF first-class roadmap | v1.2+ | preservado |
| BL-ML-LOOP | ML feedback loop estágio 1 | Fase 2 | preservado |
| BL-BACKUP | Backup/Recovery elaborado (vs MVP mínimo) | v1.1+ | preservado (FR-BACKUP-MVP-01 cobre MVP) |
| BL-CONFIG-UI | Página Configurações UI + modal aviso | v1.1+ | preservado |
| BL-HITL-ELAB | Painel HITL elaborado (bigram diversity) | v1.1+ | preservado |
| ~~BL-MONITOR-1378~~ | Monitoramento ATIVO Tema 1378 STJ | ~~v1.1+~~ | **MOVIDO para MVP v1.1.1** (FR-MONITOR-01 ATIVO) |
| BL-FIES | Projeto-irmão Revisor FIES | Fase 2+ | preservado |
| **BL-VAULT-BULK-IMPORT** | One-shot bulk import oficial vault (≥600 STJ + ≥58 STF SV) | **MVP PRE-RELEASE BLOCKER** | NOVO v1.1.1 |
| **BL-GOLDEN-SET** | Curadoria 50 contratos sintéticos + 50 queries golden RAG | **MVP PRE-RELEASE BLOCKER** | NOVO v1.1.1 |

---

*PRD Index — atualizado a cada nova versão. Owner @pm (Morgan).*
