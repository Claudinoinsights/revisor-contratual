---
type: pm-synthesis
id: TRINITY-STATUS-SPRINT-5-REMAINING-2026-05-13
title: "Trinity Status Sprint 5+ Remaining Synthesis — Bloco 3 Candidate"
project: revisor-contratual
date: 2026-05-13
ordem: 20.1
sdc_phase: "1-synthesis (Trinity PRD authority)"
strategist: "@pm (Morgan/Trinity)"
predecessor_handoff: ".lmas/handoffs/handoff-morpheus-to-trinity-2026-05-13-sprint-5-remaining-synthesis.yaml"
predecessor_route: "governance/qa/morpheus-route-sprint-5-remaining-2026-05-13.md"
recommendation: "Bloco 3 candidate = TD-SP04-S4-V1 Imobiliário Wireframe Variant (Sati Eixo 4 NEEDS CHANGES Sprint 06+ pull-forward)"
prd_update_needed: false
next_skill: "Atlas @analyst *research wireframe precedentes Imobiliário SFH/SFI (gap unclear) OR River @sm *draft TD-SP04-S4-V1 direto"
tags:
  - project/revisor-contratual
  - pm-synthesis
  - sprint-5-plus
  - bloco-3-candidate
  - trinity-status
---

# Trinity Status Sprint 5+ Remaining Synthesis

> *"Smith disse que sou precisa na execução, incompleta na especificação. Hoje provo o contrário — síntese formal com AC mensuráveis."*

---

## Task 1 — TECH-DEBT acumulado analysis

### Sprint 04 (1 HIGH + 8 MEDIUM + 1 LOW ≈ 55h)

| ID | Severity | Effort | Attackable Bloco 3? | Razão |
|----|----------|--------|---------------------|-------|
| TD-SP04-01 | LOW | 2h | NÃO | Memory swallow logging — refinement, não feature |
| TD-SP04-02 | MED | 2h | NÃO | Redis session Sprint 06+ defer |
| TD-SP04-03 | LOW | 1h | NÃO | structlog logger pattern — refinement |
| TD-SP04-04 | MED | 4h | NÃO | APScheduler fallback (pg_cron) — Sprint 06+ |
| TD-SP04-05 | MED | 6h | NÃO | last_used_at strategy promotion — scale-trigger |
| TD-SP04-06 | MED | 4h | NÃO | byok_middleware refactor Depends pattern — architectural |
| TD-SP04-07 | MED | 6h | PARTIAL | Integration tests `_REQUIRES_POSTGRES` retest — Smoke E2E blocker |
| TD-SP04-08 | LOW | 2h | NÃO | Indexes seletivos scale-trigger |
| TD-SP04-09 | MED | 6h | PARTIAL | LGPD integration tests stubs — Smoke E2E blocker |
| TD-SP04-10 | HIGH | 9.5h | NÃO | Advogado externo Eric — external |

### Sprint 5+ Analytics (3 LOW + 1 MED ≈ 11h)

| ID | Severity | Effort | Attackable Bloco 3? | Razão |
|----|----------|--------|---------------------|-------|
| TD-ANALYTICS-L4 | LOW | 3h | ✅ SIM | Cronjob `analytics_chain_verify` daily APScheduler — completa Bloco 2 |
| TD-ANALYTICS-L5 | MED | 4h | ✅ SIM | `analytics_admin BYPASSRLS` role — CLI prod-ready |
| TD-ANALYTICS-L6 | LOW | 2h | ✅ SIM | `session_rotated` event + rotation_count metric |
| TD-ANALYTICS-L7 | LOW | 2h | NÃO | Host pytest env setup docs — DevOps responsibility |

---

## Task 2 — Sati Ratify Post-Hoc Sprint 04 Re-Analysis

**6 eixos identificados em `governance/qa/sati-ratify-post-hoc-sidebar-7-modos-2026-05-09.md`:**

| Eixo | Verdict | Sprint Action | Status atual |
|------|---------|---------------|--------------|
| 2.1 Sidebar brandbook | 🟢 PASS | Nada | ✅ Validated TD-SP04-15 |
| 2.2 Cognitive load Miller's law | 🟡 BORDERLINE | Analytics empirical validation | ⚠️ **Bloco 2 dados analytics permitirão validar empíricamente quando 50+ sessions** |
| 2.3 Hierarchy ordering | 🟢 PASS | Validar via analytics Pareto | ⚠️ Same as 2.2 — aguarda dados |
| 2.4 S4 Wireframe Variants | 🟡 **NEEDS CHANGES (Sprint 06+)** | TD-SP04-S4-V1 Imobiliário + V2 FIES + V3 Geral catch-all | 🔴 **NÃO IMPLEMENTADO** — current state placeholder "Modo Avançado em desenvolvimento" |
| 2.5 Analytics tracking | 🔴 MANDATORY | TD-SP04-04-ANALYTICS | ✅ **DONE Bloco 2** |
| 2.6 Geral catch-all | 🟢 PASS (vigilância) | Validar via analytics | ⚠️ Same as 2.2 — aguarda dados |

**Trinity conclusion:** Eixo 5 era único MANDATORY pre-release v0.3.0 ✅ done. **Eixo 4 NEEDS CHANGES Sprint 06+ tem 3 sub-items TD-S4-V1/V2/V3** — não MANDATORY mas necessário antes v0.3.0 release público para não entregar produto com "Modo Avançado em desenvolvimento" placeholder em 3 doctypes (Imobiliário + FIES + Geral).

---

## Task 3 — PRD Canonical State Verification

**INDEX.md analysis:**
- **v2.0.5.1 ⭐ ACTIVE** — Sprint 5+ Ordem 19.2 Fase 1.6 (Trinity inplace bump pos Smith INFECTED)
- 9 versões historicamente cataloged
- File path: `governance/prd/prd-v2.0.5.0-PATCH-ANALYTICS-EIXO-5.md` (inplace bump 2.0.5.0→2.0.5.1)

**PRD update needed?** **NÃO neste momento.**

Razão: v2.0.5.1 captura completamente Eixo 5 Analytics. Bloco 3 candidate (Eixo 4 wireframe variants) seria PRD bump separado v2.0.6.0 OR new PRD `prd-v2.0.6.0-PATCH-EIXO-4-WIREFRAMES.md` quando story finalizada. **Defer PRD update para post-River draft** quando AC + scope concretos exist.

INDEX.md updates necessárias: 0 agora; +1 entry quando v2.0.6.0 bump pos-Bloco 3 closure.

---

## Task 4 — Bloco 3 Candidate Identification

### Critérios filtragem Eric directive

| Critério | Cumprimento |
|----------|-------------|
| Feature code work (não governance/external) | MUST |
| Domain software-dev | MUST |
| AC mensuráveis | MUST |
| Smith H2 envelope honest estimate | MUST |
| RTK token economy + Skill chain estrito | MUST |
| Strategic value v0.3.0 release | SHOULD |

### Top 3 candidates ordenados

| # | Candidate | Severity | Effort | Strategic Value v0.3.0 |
|---|-----------|----------|--------|------------------------|
| **1** | **TD-SP04-S4-V1 Imobiliário Wireframe Variant** | MEDIUM | ~6-8h Smith H2 honest | 🔥 **HIGH** — fecha Eixo 4 Sati gap, remove placeholder "em desenvolvimento" Imobiliário |
| 2 | TD-ANALYTICS-L4 Cronjob analytics_chain_verify | LOW | 3h | MEDIUM — completa Bloco 2 polish |
| 3 | TD-SP04-S4-V2 FIES Wireframe Variant | MEDIUM | ~6-8h | HIGH — paralelo Imobiliário, mesma natureza |

### 🥇 Recommendation: TD-SP04-S4-V1 Imobiliário

**Story stub:**

```
Story: TD-SP04-S4-V1-IMOBILIARIO-WIREFRAME-VARIANT
Como Eric (Orsheva founder),
Eu quero o doctype Imobiliário ter wireframe S4 com campos específicos
  (matrícula RGI + valor avaliação + garantia (alienação fiduciária vs
  hipoteca) + índice (TR/IPCA/IGP-M)),
Para que escritórios advocacia possam revisar contratos imobiliários SFH/SFI
  empíricamente, removendo placeholder "Modo Avançado em desenvolvimento"
  que prejudica perceived quality e onboarding.

AC mensuráveis (estimate 8 ACs):
  1. SPA exibe campos específicos Imobiliário (não placeholder genérico)
  2. Campos: matrícula RGI (string format X.X.XXX) + valor avaliação (Decimal
     R$) + tipo garantia (enum 2 valores) + índice (enum 4 valores TR/IPCA/IGP-M/PRÉ)
  3. Backend Pydantic schema valida ImobiliarioContractData strict
  4. Análise LLM usa prompt template Imobiliário (sumarização específica vs
     CDC bancário genérico)
  5. CET calculation considera índice variable (TR/IPCA) vs fixo (PRÉ)
  6. Analytics doctype_selected captura "imobiliario" mais empíricamente
     pós-fix (gap percepção atual = drop-off rate elevado vs 4 doctypes
     bancários)
  7. Tests pytest unit ImobiliarioContractData strict validation + LLM
     prompt template smoke
  8. Constitution Art. I CLI First + Art. IV regression baseline ≥400 tests
```

**Effort Smith H2 honest envelope:** ~6-8h chunked (similar Bloco 1 TD-SP04-15 + lighter scope).

**Risks (1 HIGH + 2 MED + 5 LOW antecipado):**

- R-01 HIGH: LLM prompt template Imobiliário require advogada review (loop external Eric advogada) — MITIGAÇÃO: ship com placeholder prompt + advogada review parallel Sprint 6+ refinement
- R-02 MED: CET calculation com índice variable é complexity nova (não cobre TR/IPCA até hoje)
- R-03 MED: Schema migration sp06_001 adicional (ImobiliarioContractData table OR JSON field analyses table)
- R-04..R-08 LOW: edge cases standard (validation, error handling, drop-off compatibility)

---

## Task 5 — Output + Próxima Skill Handoff

### Trinity decisions (D-PM-S05-Trinity-Status-001..003)

- **D-PM-S05-Trinity-Status-001:** Bloco 3 candidate = TD-SP04-S4-V1 Imobiliário Wireframe Variant. Strategic value HIGH v0.3.0 release (remove placeholder de 1 dos 3 doctypes "em desenvolvimento").
- **D-PM-S05-Trinity-Status-002:** PRD update bump v2.0.6.0 defer post-River draft (AC + scope finalize primeiro).
- **D-PM-S05-Trinity-Status-003:** Bloco 3 escopo focado em 1 doctype (Imobiliário) NÃO bundle FIES + Geral. Razão Smith H2 envelope honest — single doctype delivered properly > 3 doctypes shipped half. FIES (V2) + Geral (V3) ficam Sprint 6+ next.

### Próxima Skill — opções

**Opção A (RECOMENDADA):** Direto River @sm `*draft TD-SP04-S4-V1-IMOBILIARIO-WIREFRAME-VARIANT`

Razão: Story stub clear + AC well-defined + Smith H2 envelope estimated + risks identified. River pode draft formal story usando este synthesis como base. Atlas research pode acontecer parallel se Sprint 6+ wants validation jurídica.

**Opção B:** Atlas @analyst `*research wireframe precedentes Imobiliário SFH/SFI + LLM prompts advogada review`

Razão: Se Eric quer validate antes commit Sprint 5+ Bloco 3 effort. Heavier path mas reduce risk LLM prompt template advogada review external dependency.

**Opção C:** Trinity PRD direto v2.0.6.0 bump primeiro, depois River draft

Razão: PRD-first strict per Constitution Art. III Deliverable-Driven. Slowest path mas máxima governance rigor.

### Recommendation Trinity → Opção A

Bloco 2 precedent: River drafted TD-SP04-04-ANALYTICS direto sem Atlas research (PRD v2.0.5.1 era suficiente). Bloco 3 TD-S4-V1 Imobiliário tem mais clareza upfront (Sati ratify identified campos específicos) — River pode draft direto.

**Next Skill handoff:** `LMAS:agents:sm` River com prompt `*draft TD-SP04-S4-V1-IMOBILIARIO-WIREFRAME-VARIANT` baseado nesta synthesis.

Smith Fase Trinity.5 mid-chain review **OBRIGATÓRIO** antes River start (Eric rigor heavy directive).

---

## Files modified Trinity Ordem 20.1

- `governance/qa/trinity-status-sprint-5-remaining-2026-05-13.md` (NEW — este)
- `.lmas/handoffs/handoff-trinity-to-smith-2026-05-13-fase-trinity-5-midchain-status.yaml` (NEW — próximo)

— Morgan/Trinity, planejando o futuro 📊
