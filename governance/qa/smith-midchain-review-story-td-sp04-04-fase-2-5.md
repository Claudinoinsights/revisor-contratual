---
type: adversarial-review
id: SMITH-STORY-TD-SP04-04-MIDCHAIN-2026-05-13
title: "Smith Mid-Chain Review — Story TD-SP04-04-ANALYTICS Draft"
project: revisor-contratual
date: 2026-05-13
ordem: 19.2.fase-2.5
sdc_phase: "story-drafted (pre-Keymaker G3)"
reviewer: "@smith (Smith)"
predecessor_handoff: ".lmas/handoffs/handoff-river-to-smith-2026-05-13-story-td-sp04-04-midchain.yaml"
target_story: "governance/stories/TD-SP04-04-ANALYTICS-tracking-5-metrics-pre-release.md"
verdict: "🟢 CONTAINED — 10 findings (0 CRITICAL + 0 HIGH + 2 MEDIUM + 8 LOW); Keymaker G3 pode prosseguir com awareness"
severity_breakdown:
  CRITICAL: 0
  HIGH: 0
  MEDIUM: 2
  LOW: 8
greenlight_status: "Fase 3 Keymaker G3 UNBLOCKED com observações; MEDIUMs addressable durante Neo implementation OR Oracle G5"
tags:
  - project/revisor-contratual
  - smith-adversarial
  - story-td-sp04-04
  - mid-chain
  - fase-2-5
  - contained-verdict
---

# Smith Mid-Chain Review — Story TD-SP04-04-ANALYTICS Draft (CONTAINED)

> *"A Sra. River absorveu Trinity v2.0.5.1 + meu CLEAN re-verify; transformou em 22 ACs implementáveis. Estrutura adequada. Mas mid-chain proíbe complacência — encontro 10 findings. 2 MEDIUM são gaps de contrato; 8 LOW são polish ou edge cases. Keymaker pode prosseguir."*

---

## Methodology

Scope LIMITED mid-chain — story coherence + AC traceability + chunk effort math + REUSE rigor + risk classification + Constitutional No Invention. 8 probes River-anticipated + new adversarial probes.

---

## Findings (10 total — Smith threshold met)

### 🟡 MEDIUM (2)

**F-SMITH-STORY-01 (MED):** AC-15 idempotency contract gap — "duplicate retorna 200 silent" mas DB UNIQUE constraint default retorna 409 Conflict. AC não exige explicitly server-side try/except + transform 409 → 200 OK. Neo pode interpretar como UNIQUE constraint = 409 valid response, violando AC.

**Como corrigir:** Adicionar AC-15 explicit "Backend catches `psycopg.errors.UniqueViolation` E retorna HTTP 200 com body `{status: 'duplicate', event_id}` — NUNCA 409 Conflict" + pytest test_idempotency_returns_200_not_409.

**F-SMITH-STORY-02 (MED):** AC-1 drop-off trigger priority order ambíguo. "15min OR beforeunload OR JWT expiry" — quando múltiplos triggers fire simultaneously (e.g., user closes tab AT exactly 15min mark + JWT just expired) → duplicate drop-off events? Inconsistent metric.

**Como corrigir:** Adicionar priority order explicit: 1º beforeunload (immediate), 2º JWT expiry (server-side), 3º 15min timeout (deferred); idempotency key per session_id ensures single drop_off event per session.

---

### 🔵 LOW (8)

**F-SMITH-STORY-03 (LOW):** Chunk 3 frontend opt-out mention conflitos com TD-ANALYTICS-L3 catalog. Story diz "opt-out check (DPA acceptance flag)" Chunk 3 mas catalog Section 11 menciona "Opt-out FR explicit ausente". Inconsistency — implementation prescribed mas FR ausente. Esclarecer: Chunk 3 implementa OPCIONALMENTE OR TD-L3 Sprint 5+?

**F-SMITH-STORY-04 (LOW):** AC-19 "≥400 passed" assume +50 new tests, mas chunks listed apenas ~30-40 tests realistic. Inflated count. Adjust to ~30-40 new = 380-390 total OR justify 50 with specific test files.

**F-SMITH-STORY-05 (LOW):** Chunk 4 CLI 8 commands ~4-5h. ~30min per command = 4h. Realistic ~45-60min per command (parse + query + threshold + format + tests) = 6-8h. Chunk 4 effort under-estimated; could push Chunk 4 alone to 6h, total 14-18h exceeding Smith H2 envelope upper.

**F-SMITH-STORY-06 (LOW):** AC-21 effort budget verifiable "time tracking Neo" — subjective; Neo não tem built-in tracking. Oracle G5 não pode verificar empirically. Sugestão: AC-21 reformulated como "Neo reports actual effort em Change Log post-implementation; deviation >25% triggers Aria retroactive spike".

**F-SMITH-STORY-07 (LOW):** R-09 risk "Frontend IIFE coupled to sidebar HTML structure" classified LOW mas é technical coupling REAL (TD-SP04-15 precedent showed). Upgrade para MEDIUM com mitigação stronger: "data-mode attribute API documented; sidebar refactor requires re-test analytics event capture".

**F-SMITH-STORY-08 (LOW):** REUSE table Dev Notes duplica PRD v2.0.5.1 Section 5 (DRY violation). Substitute com "Ver PRD v2.0.5.1 Section 5 REUSE Table" reference OR keep duplicate for self-contained story (River escolha).

**F-SMITH-STORY-09 (LOW):** Tasks/Subtasks Chunk 2 hardcoded "max 5 events per batch" mas no AC defines batch size limit. Backend magic number sem story-level requirement. Adicionar AC `analytics_event_batch` aceita ≤5 events; > 5 retorna 400 com error explicit.

**F-SMITH-STORY-10 (LOW):** AC-22 "Operator closure adds 5 LOW TD-ANALYTICS-L1..L5" — River output deveria pre-stage entries (commented TECH-DEBT.md placeholder) para Operator simply copy-paste. AC describes future Operator action, not River output.

---

## Verdict

### 🟢 **CONTAINED**

> *"A Sra. River entregou estrutura adequada — 22 ACs proporcionais ao escopo (vs Bloco 1 12 ACs LOW story), REUSE rastreável, riscos honestos. Os 2 MEDIUMs são gaps de contrato — Neo pode resolver implementation-time. 8 LOWs são polish. Keymaker prossegue."*

**Justificativa:**
- **0 CRITICAL + 0 HIGH** — story fundação sólida (Trinity v2.0.5.1 + Smith CLEAN)
- **2 MEDIUM** — addressable durante Neo Fase 4 OR Oracle G5 Fase 5 catch
- **8 LOW** — refinements (efforts + AC reformulations + DRY)
- **10 findings total** (Smith threshold met)

---

## Greenlight Conditions

### Fase 3 Keymaker G3 UNBLOCKED

**Conditions:**
- [x] Story coherent + 22 ACs traceable
- [x] 5 chunks effort 12-16h (Smith H2 envelope respected with caveat F-05)
- [x] REUSE rigor (table 5 sources line numbers)
- [x] Risk classification 1 HIGH + 4 MED + 5 LOW
- [x] Constitutional alignment 100%

**Observações para Keymaker G3:**
- 2 MEDIUM (F-01 idempotency + F-02 drop-off priority) — Keymaker pode prosseguir; flag para Neo addressing durante implement
- 8 LOW — note for catalog OR inline tweaks River pode aplicar

---

## Routing

| Finding | Owner | Action | Timing |
|---------|-------|--------|--------|
| F-01, F-02 (MED) | @dev Neo (Fase 4) | Address implementation-time + tests | Pre-Oracle G5 |
| F-03..F-10 (LOW) | @sm River OR catalog Sprint 5+ | Inline tweaks OR TECH-DEBT.md | Pre-Operator push OR Sprint 5+ |

---

## Next Action

**Fase 3:** Keymaker G3 10-point checklist validation via Skill `LMAS:agents:po` *validate-story-draft com awareness 2 MED + 8 LOW.

— Smith. CONTAINED. 🕶️
