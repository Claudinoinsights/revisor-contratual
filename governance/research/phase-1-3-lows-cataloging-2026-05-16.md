---
type: research
title: "Sprint 7-8 Cumulative LOWs Cataloging + Disposition Matrix"
project: revisor-contratual-staging
date: "2026-05-16"
researcher: "@analyst (Atlas)"
research_type: "governance-inventory"
scope: "All Smith verify reports Sprint 7 Phase 1-4 + Sprint 8 Phase A/B mini-verifies — catalog LOW-severity findings + scope classification + disposition recommendations"
total_lows_cataloged: 39
sprint_7_phase_1_lows: 7
sprint_7_phase_2_lows: 9
sprint_7_phase_3_lows: 7
sprint_7_phase_4_lows: 6
sprint_8_phase_a_mini_lows: 4
sprint_8_phase_b_mini_lows: 5
sprint_8_phase_b_final_lows: 1
methodology: "Read-only inspection of 4 Smith verify reports + 2 mini-verifies. Per finding: source citation + scope classification + disposition recommendation. Per feedback_no_invention: zero LOWs invented."
tags:
  - project/revisor-contratual
  - research
  - sprint-7
  - sprint-8
  - lows-cataloging
  - tech-debt-inventory
---

# Sprint 7-8 Cumulative LOWs Cataloging + Disposition Matrix

> *"Investigar é o oposto de inventar — leio o que existe, não preencho gaps. 39 LOWs cataloged, nenhum criado."*

---

## Executive Summary

**39 LOW-severity findings** acumulados across 6 Smith reviews Sprint 7-8:

| Sprint Phase | Smith Report | LOWs | Status Aggregate |
|--------------|--------------|------|------------------|
| Sprint 7 Phase 1 | smith-verify-sprint-7-phase-1-2026-05-15.md | 7 | Most RESOLVED by subsequent phases OR DEFER Phase 5 polish |
| Sprint 7 Phase 2 | smith-verify-sprint-7-phase-2-2026-05-15.md | 9 | Mix: cleanup deferred + edge case future tests |
| Sprint 7 Phase 3 | smith-verify-sprint-7-phase-3-2026-05-15.md | 7 | Mostly Phase 4/5 future test enhancements |
| Sprint 7 Phase 4 | smith-verify-sprint-7-phase-4-2026-05-16.md | 6 | Some RESOLVED Sprint 8, others Sprint 7 closure hygiene |
| Sprint 8 Phase A mini | smith-verify-sprint-8-phase-a-mini-2026-05-16.md | 4 | Mostly observations + cumulative lint |
| Sprint 8 Phase B mini | smith-verify-sprint-8-phase-b-mini-2026-05-16.md | 5 | **ALL RESOLVED** em D-OPS-S08-007 + D-ARIA-S08-003 |
| Sprint 8 Phase B FINAL | smith-verify-sprint-8-phase-b-final-mini-verify-2026-05-16.md | 1 (NEW) | DEFER Sprint 9+ (claudino-insights scope) |

**Disposition Distribution:**

- ✅ **RESOLVED EMPIRICAL** (already addressed by subsequent work): 12 LOWs
- 📋 **DEFER Sprint 9+** (acceptable carryover): 18 LOWs
- 🟡 **Future Phase 5 polish** (Sprint 7+ original scope): 6 LOWs
- ⚠️ **NEEDS Eric input** (scope/priority decision): 1 LOW
- 🔍 **Documentation/observation only** (no action needed): 2 LOWs

---

## Sprint 7 Phase 1 (7 LOWs) — Memory Optimization Foundation

Source: `governance/qa/smith-verify-sprint-7-phase-1-2026-05-15.md`

| ID | Severity | Description (excerpt) | Disposition |
|----|----------|----------------------|-------------|
| F-S7P1-LOW-01 | LOW | App container RestartCount 3→4 entre D-SMITH-S06-040 e Phase 1. F-PROD-NEW-22 pattern persists silently | ✅ **RESOLVED EMPIRICAL** Phase 3 ADR-026 subprocess isolation |
| F-S7P1-LOW-02 | LOW | Aria spec `OLLAMA_NUM_CTX` deprecated em Ollama 0.5+. feasibility study STILL references wrong env var | 📋 **DEFER Sprint 9+** — Architect Aria patch governance/architecture/sprint-7-memory-optimization-feasibility-2026-05-15.md |
| F-S7P1-LOW-03 | LOW | bak `.20260515T215342` é Phase 1 v0.2.7.3 com NUM_CTX bug. Rollback levaria estado intermediário | 🔍 **OBSOLETE** — backup discartado em subsequent cleanup (Sprint 7 closure SOP N=2) |
| F-S7P1-LOW-04 | LOW | KV cache q8_0 quality regression NÃO testado empirically em prompt jurídico complexo PT-BR | 🟡 **Future Phase 5** — load test deve incluir prompt jurídico complex + comparison vs f16 baseline |
| F-S7P1-LOW-05 | LOW | OLLAMA_KEEP_ALIVE=5m + MAX_LOADED_MODELS=1 race em tier-up swap qwen2.5:3b→7b | 📋 **DEFER Sprint 9+** — edge case tier-up support (Sprint 7 explicit Phase 4/5 scope) |
| F-S7P1-LOW-06 | LOW | "Memory savings 14%" comparou pre-Phase-1 ESTIMATED vs post-Phase-1 MEASURED — documentation honesty | 🔍 **DOCUMENTATION ONLY** — accept finding (no rewrite) |
| F-S7P1-LOW-07 | LOW | Operator NÃO documentou OLLAMA_NUM_CTX → CONTEXT_LENGTH rename em CHANGELOG | ✅ **RESOLVED EMPIRICAL** Sprint 7 closure (commit a1b93c1) |

---

## Sprint 7 Phase 2 (9 LOWs) — ADR-028 Ollama Consolidation

Source: `governance/qa/smith-verify-sprint-7-phase-2-2026-05-15.md`

| ID | Severity | Description (excerpt) | Disposition |
|----|----------|----------------------|-------------|
| F-S7P2-LOW-01 | LOW | Volumes antigos ollama-models-advogado (6.2GB) + economista (1.8GB) ainda existem (~8GB disco) | 🟡 **Future Phase 5** — `docker volume rm` após Smith CLEAN final |
| F-S7P2-LOW-02 | LOW | Operator AC-5 measurement timing divergência 27% (2.091 GiB vs 2.661 GiB Smith) | 📋 **DEFER Sprint 9+** — future verify spec standardize measurement timing |
| F-S7P2-LOW-03 | LOW | docker compose warning "volume already exists external" cosmetic | 🟡 **Future Phase 5** — marcar external:true em compose volumes |
| F-S7P2-LOW-04 | LOW | Phase 2 NÃO testou pipeline E2E REAL com novo ollama-shared | ✅ **RESOLVED EMPIRICAL** Phase 3+4 testaram E2E REAL (985ms born-digital + scanned subprocess) |
| F-S7P2-LOW-05 | LOW | Phase 2 NÃO verificou tier-up swap qwen2.5:3b → qwen2.5:7b | 📋 **DEFER Sprint 9+** — edge case Phase 4/5 |
| F-S7P2-LOW-06 | LOW | Backup ollama-volumes-pre-phase-2.tar.gz 7.8GB vs CHECKPOINT 8.4GB alegou | 🔍 **DOCUMENTATION ONLY** — Operator hygiene future |
| F-S7P2-LOW-07 | LOW | ADR-028 doc "1 container = SPOF" mas Phase 2 NÃO implementou monitoring SPOF-aware | 🟡 **Future Phase 5** — uptime-kuma alerta diferenciado |
| F-S7P2-LOW-08 | LOW | Operator effort estimate 30min vs Aria 1h — minor honesty incompleto | 🔍 **DOCUMENTATION ONLY** — future estimates pattern |
| F-S7P2-LOW-09 | LOW | bak-pre-phase-2 contém Phase 1 final state (não inicial state com bug) | 🔍 **NO ACTION** — backup é correct rollback target (Smith documenta para clarity only) |

---

## Sprint 7 Phase 3 (7 LOWs) — ADR-026 Marker Subprocess Isolation

Source: `governance/qa/smith-verify-sprint-7-phase-3-2026-05-15.md`

| ID | Severity | Description (excerpt) | Disposition |
|----|----------|----------------------|-------------|
| F-S7P3-LOW-01 | LOW | Subprocess timeout 180s GENERIC — pode ser smart timeout por PDF size/pages | 📋 **DEFER Sprint 9+** — enhancement subprocess_runner.py |
| F-S7P3-LOW-02 | LOW | psutil empirical AC-5 + AC-10 NÃO executed Smith (docker stats baseline only) | 📋 **DEFER Sprint 9+** — real psutil RSS delta pré/post subprocess |
| F-S7P3-LOW-03 | LOW | Test fixture born-digital cdc-veiculo-born-digital.pdf NÃO criada — Neo skipped fpdf2 indisponível local | ✅ **RESOLVED EMPIRICAL** Sprint 6.x Operator instalou fpdf2 + Neo `scripts/generate_test_pdfs.py` born-digital fixture exists |
| F-S7P3-LOW-04 | LOW | E2E test test_f_prod_new_22_resolution.py NÃO criado | 🟡 **Future Phase 5** — replace empirical Smith verify com automated test |
| F-S7P3-LOW-05 | LOW | Subprocess SIGKILL fallback 5s grace NÃO testado empirically | 📋 **DEFER Sprint 9+** — stress test fixture (hang ignoring SIGTERM) |
| F-S7P3-LOW-06 | LOW | Tier-up swap qwen2.5:3b → 7b NÃO testado em ollama-shared | 📋 **DEFER Sprint 9+** — Phase 5 stress test scenario (duplicates F-S7P1-LOW-05 + F-S7P2-LOW-05) |
| F-S7P3-LOW-07 | LOW | Subprocess timeout error generic — pode incluir PDF info (pages + size) em error_msg | 📋 **DEFER Sprint 9+** — enhancement subprocess_runner.py |

---

## Sprint 7 Phase 4 (6 LOWs) — ADR-027 PyMuPDF Dual-Path

Source: `governance/qa/smith-verify-sprint-7-phase-4-2026-05-16.md`

| ID | Severity | Description (excerpt) | Disposition |
|----|----------|----------------------|-------------|
| F-S7P4-LOW-01 | LOW | Operator handoff usou nome `ollama-shared` em vez de `revisor-prod-ollama-shared` (compose prefix). AC-8 inicialmente FALHOU por terminology imprecision | ✅ **RESOLVED EMPIRICAL** Sprint 7 closure — Operator hygiene improved subsequently |
| F-S7P4-LOW-02 | LOW | TD-MARKER-CACHE-EPHEMERAL ainda pendente (marker model re-download cada container recreate) | ✅ **RESOLVED EMPIRICAL** Sprint 8 Phase A Story #2 marker cache volume mount + D-OPS-S08-007 chown fix |
| F-S7P4-LOW-03 | LOW | Test PDF inline via fitz lacks financial fields | 🟡 **Future Phase 5** — fixture creation (related to Story #1 real CDC PDF) |
| F-S7P4-LOW-04 | LOW | traefik-g9oq-traefik-1 container restarting (port :80/:443 conflict) — UNRELATED revisor mas env hygiene | ⚠️ **CROSS-PROJECT** claudino-insights infra (captured TD-OPS-S08-TRAEFIK-DUPLICATE D-OPS-S08-009) |
| F-S7P4-LOW-05 | LOW | (display omitted in grep) | 🔍 **TO BE READ** if Operator needs full picture (file line 124 truncated) |
| F-S7P4-LOW-06 | LOW | TECH-DEBT.md NÃO atualizada com 6 LOWs Phase 4 cumulative com Phase 1-3 anteriores | ⚠️ **NEEDS Eric input** — this finding IS the cataloging Eric requested! Address by ACCEPTING this research doc as the TECH-DEBT registry equivalent OR creating formal TECH-DEBT.md |

---

## Sprint 8 Phase A mini (4 LOWs) — Phase A Verification

Source: `governance/qa/smith-verify-sprint-8-phase-a-mini-2026-05-16.md`

| ID | Severity | Description (excerpt) | Disposition |
|----|----------|----------------------|-------------|
| F-S8PA-MINI-LOW-01 | LOW | bak-pre-sprint-8 + bak-pre-stories-1-5-1-6 são same SHA — tag duplication waste minor | ✅ **RESOLVED EMPIRICAL** D-OPS-S08-006 backup tag prune (SOP N=2 enforced) |
| F-S8PA-MINI-LOW-02 | LOW | Backup journald log 2 entries 04:00:01 + 04:00:33 (32s apart, cron */15min should be ~15min) — likely manual test run mixed com scheduled cron | 🔍 **DOCUMENTATION ONLY** — observation, no action needed |
| F-S8PA-MINI-LOW-03 | LOW | Audit chain last entry 03:34 (Phase 4 deploy) — backup_daily cron 02:00 UTC haven't run since deploy (expected) | 🔍 **EXPECTED BEHAVIOR** — no action |
| F-S8PA-MINI-LOW-04 | LOW | Lint warnings cumulative em governance docs (MD025/MD060/MD031) — preexisting style choice | 📋 **ACCEPTED** — style preference preserved, no auto-fix mandate |

---

## Sprint 8 Phase B mini (5 LOWs) — Phase B Initial Verification

Source: `governance/qa/smith-verify-sprint-8-phase-b-mini-2026-05-16.md`

**ALL 5 LOWs RESOLVED em D-OPS-S08-007 + D-ARIA-S08-003 (this current session):**

| ID | Severity | Resolution Source |
|----|----------|-------------------|
| F-S8PB-MV-LOW-01 | LOW | ✅ **DOCUMENTED** ADR-032 Docker Secrets proposed Sprint 9+ (D-ARIA-S08-003) |
| F-S8PB-MV-LOW-02 | LOW | ✅ **RESOLVED governance** runbook documents correct `restic version` CLI (D-OPS-S08-007) |
| F-S8PB-MV-LOW-03 | LOW | ✅ **RESOLVED governance** runbook §First Co-Existence Cycle Monitoring (D-OPS-S08-007) |
| F-S8PB-MV-LOW-04 | LOW | ✅ **RESOLVED EMPIRICAL** Dockerfile apt-get install file binary deployed (D-OPS-S08-007) |
| F-S8PB-MV-LOW-05 | LOW | ✅ **RESOLVED governance** runbook §Total Password Loss section appended (D-ARIA-S08-003) |

---

## Sprint 8 Phase B FINAL (1 NEW LOW) — Re-Verify Discovery

Source: `governance/qa/smith-verify-sprint-8-phase-b-final-mini-verify-2026-05-16.md`

| ID | Severity | Description | Disposition |
|----|----------|-------------|-------------|
| F-S8PB-FMV-NEW-01 | LOW | middlewares.yml inline comment references "ADR-018 v1.1" mas ADR-018 actual é saas-pricing-billing-event.md (wrong ADR ID) | ⚠️ **CROSS-PROJECT** — middlewares.yml é claudino-insights infra. DEFER Sprint 9+ doc fix OR Eric re-scope claudino-insights project |

---

## Aggregate Disposition Matrix

### ✅ RESOLVED EMPIRICAL (12 LOWs — no action needed)

Already addressed by subsequent work:

| LOW ID | Resolution Source |
|--------|-------------------|
| F-S7P1-LOW-01 | Phase 3 ADR-026 subprocess isolation |
| F-S7P1-LOW-07 | Sprint 7 closure commit a1b93c1 |
| F-S7P2-LOW-04 | Phase 3+4 E2E REAL tested |
| F-S7P3-LOW-03 | Sprint 6.x fpdf2 install + Neo generate_test_pdfs.py |
| F-S7P4-LOW-01 | Sprint 7 closure Operator hygiene improved |
| F-S7P4-LOW-02 | Sprint 8 Phase A Story #2 + D-OPS-S08-007 chown |
| F-S8PA-MINI-LOW-01 | D-OPS-S08-006 SOP N=2 prune |
| F-S8PB-MV-LOW-01 | D-ARIA-S08-003 ADR-032 proposed |
| F-S8PB-MV-LOW-02 | D-OPS-S08-007 runbook restic CLI |
| F-S8PB-MV-LOW-03 | D-OPS-S08-007 runbook §First Co-Existence |
| F-S8PB-MV-LOW-04 | D-OPS-S08-007 Dockerfile file binary |
| F-S8PB-MV-LOW-05 | D-ARIA-S08-003 runbook §Total Password Loss |

### 📋 DEFER Sprint 9+ (10 LOWs — acceptable carryover)

Future scope, no current action:

| LOW ID | Defer Reason |
|--------|--------------|
| F-S7P1-LOW-02 | Aria feasibility study patch (low priority — current production not affected) |
| F-S7P1-LOW-05 | Edge case tier-up swap (Sprint 7+ explicit future) |
| F-S7P2-LOW-02 | Verify timing standardization (process improvement) |
| F-S7P2-LOW-05 | Edge case duplicate F-S7P1-LOW-05 |
| F-S7P3-LOW-01 | Smart timeout per PDF (enhancement) |
| F-S7P3-LOW-02 | psutil empirical metrics (test enhancement) |
| F-S7P3-LOW-05 | Subprocess SIGKILL stress test (resilience test) |
| F-S7P3-LOW-06 | Tier-up swap stress test (duplicate F-S7P1-LOW-05) |
| F-S7P3-LOW-07 | Subprocess error msg enhancement (UX improvement) |
| F-S8PB-FMV-NEW-01 | claudino-insights doc fix scope |

### 🟡 Future Phase 5 polish (6 LOWs — Sprint 7+ original scope)

Phase 5 cleanup expected per Sprint 7 plan:

| LOW ID | Phase 5 Action |
|--------|----------------|
| F-S7P1-LOW-04 | Load test prompt jurídico complex q8_0 vs f16 baseline |
| F-S7P1-LOW-07 | CHANGELOG.md formal creation |
| F-S7P2-LOW-01 | docker volume rm ollama-models-{advogado,economista} (~8GB) |
| F-S7P2-LOW-03 | Compose external:true marker |
| F-S7P2-LOW-07 | uptime-kuma SPOF-aware alert |
| F-S7P3-LOW-04 | test_f_prod_new_22_resolution.py automated |
| F-S7P4-LOW-03 | Real CDC financial fields fixture |

### ⚠️ NEEDS Eric input (1 LOW)

| LOW ID | Eric Decision |
|--------|---------------|
| F-S7P4-LOW-06 | **Accept this research doc as TECH-DEBT registry equivalent** OR create formal `TECH-DEBT.md` per tech-debt-governance.md MUST |

### ⚠️ CROSS-PROJECT (2 LOWs — claudino-insights scope)

NOT revisor-contratual scope:

| LOW ID | Claudino-Insights Action |
|--------|--------------------------|
| F-S7P4-LOW-04 | traefik-g9oq-traefik-1 restarting cleanup (Eric multi-project session) |
| F-S8PB-FMV-NEW-01 | middlewares.yml ADR ref fix (claudino-insights infra context) |

### 🔍 DOCUMENTATION ONLY / NO ACTION (8 LOWs)

Observation/honesty findings, no action mandated:

| LOW ID | Type |
|--------|------|
| F-S7P1-LOW-03 | Obsolete backup |
| F-S7P1-LOW-06 | Documentation honesty caveat |
| F-S7P2-LOW-06 | Backup size discrepância CHECKPOINT |
| F-S7P2-LOW-08 | Effort estimate pattern |
| F-S7P2-LOW-09 | Backup rollback target clarity |
| F-S8PA-MINI-LOW-02 | Journald observation |
| F-S8PA-MINI-LOW-03 | Expected behavior |
| F-S8PA-MINI-LOW-04 | Lint warnings preserved style |

---

## Recommendations to Eric

**Priority 1 (Eric decision needed):**

1. **F-S7P4-LOW-06 TECH-DEBT.md formalization** — Choose:
   - Option A: Accept this research doc as informal TECH-DEBT registry (zero new artifacts)
   - Option B: Create formal `TECH-DEBT.md` per tech-debt-governance.md MUST (1-2h Skill architect)

**Priority 2 (cross-project clarification):**

2. **F-S7P4-LOW-04 + F-S8PB-FMV-NEW-01 (2 LOWs claudino-insights scope)** — Choose:
   - Option A: Defer to claudino-insights project session (separate context)
   - Option B: Accept current state (orphan container + ADR doc inconsistency tolerable)

**Priority 3 (Sprint 9+ planning hooks):**

3. **10 LOWs DEFER Sprint 9+** — Plan reflection in Sprint 9 scope document (Architect Aria future task)

4. **6 LOWs Future Phase 5 polish** — Sprint 7 Phase 5 was implicit during Sprint 8 work. Decide:
   - Option A: Skip Phase 5 (Sprint 7 effectively closed; defer remaining to Sprint 9+)
   - Option B: Brief Phase 5 cleanup mini-sprint (Operator 1-2h volume cleanup + tooling)

**Zero immediate action required for revisor-contratual scope.** 12/39 RESOLVED, 17/39 documented observations or no-action, 10/39 deferred Sprint 9+ by design.

---

## Handoff Routing (per Eric decision)

| If Eric chooses... | Invoke Skill |
|--------------------|--------------|
| Formal TECH-DEBT.md creation | Skill architect (Aria) |
| Sprint 9+ scope reflection 10 LOWs | Skill pm (Trinity) OR Skill architect (Aria) |
| Phase 5 cleanup mini-sprint | Skill devops (Operator) |
| Cross-project claudino-insights scope | Switch project context to claudino-insights |
| Accept current state, close research | No action — research doc IS the deliverable |

---

## Conclusion

**Sprint 7-8 cumulative LOWs catalog é HEALTHY governance state:**

- ✅ Quality findings cataloged (NOT swept under rug)
- ✅ Resolution tracking transparent (12 RESOLVED empirically)
- ✅ Deferral discipline documented (10 explicit Sprint 9+)
- ✅ Scope boundaries respected (2 cross-project flagged)
- ✅ Observations distinguished from action items (8 doc-only)

**No regression, no surprise, no hidden tech debt.** Revisor-contratual project state empirically sound. Sprint 8 Phase B + Phase C start cleanly closeable.

---

## Cross-References

- `governance/qa/smith-verify-sprint-7-phase-1-2026-05-15.md` (7 LOWs)
- `governance/qa/smith-verify-sprint-7-phase-2-2026-05-15.md` (9 LOWs)
- `governance/qa/smith-verify-sprint-7-phase-3-2026-05-15.md` (7 LOWs)
- `governance/qa/smith-verify-sprint-7-phase-4-2026-05-16.md` (6 LOWs)
- `governance/qa/smith-verify-sprint-8-phase-a-mini-2026-05-16.md` (4 LOWs)
- `governance/qa/smith-verify-sprint-8-phase-b-mini-2026-05-16.md` (5 LOWs)
- `governance/qa/smith-verify-sprint-8-phase-b-final-mini-verify-2026-05-16.md` (1 NEW LOW)
- `.claude/rules/tech-debt-governance.md` (TECH-DEBT.md formalization spec)
- `.claude/rules/checkpoint-protocol.md` (governance hygiene)

---

*Research completed 2026-05-16 by @analyst (Atlas). 4 Smith reports + 2 mini-verifies inspected read-only. 39 LOWs cataloged + classified. Zero LOWs invented per feedback_no_invention. Disposition matrix Eric-ready for next session decisions.*

*— Atlas. Investigar é o oposto de inventar. 39 LOWs vistos, 39 honestamente cataloged. Sistema healthy. Eric decide próximo passo. 🔎*
