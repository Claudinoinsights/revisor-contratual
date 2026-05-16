---
type: sprint-scope
title: "Sprint 8 Scope EXPANDED — Production Readiness 100/100 (Post Smith Ultrathink INFECTED 56/100)"
sprint: 08
status: scoped-expanded
version: 2.0
predecessor_version: 1.0 (6 stories core, replaced 2026-05-16)
start_date: TBD (post Eric directive execution order)
end_date: TBD
predecessor_sprint: 07 (Cenário Y++ DoD Architectural)
project: revisor-contratual
estimate_total: "~30-40h estimate / ~15-20h actual com 95% speed bonus pattern"
trigger_expansion: "Smith ultrathink D-SMITH-S07-005 (verdict INFECTED 56/100, 51 findings)"
verify_pattern: "Smith re-ultrathink após Sprint 8 close (NOT entre cada story — sprint-end batch)"
tags:
  - project/revisor-contratual
  - sprint-08
  - scope-expanded
  - production-readiness-100
  - smith-ultrathink-cleanup
  - cenario-y-plus-plus-dod-final
---

# Sprint 8 Scope EXPANDED — Production Readiness 100/100

## Sprint Goal

**Resolver 6 CRITICAL + 11 HIGH findings do Smith ultrathink (D-SMITH-S07-005)** + **Cenário Y++ DoD Final 100% (architectural Sprint 7 + business validation real-world Sprint 8)** + **production readiness scorecard reach 100/100**.

**Sprint 7 closou architectural ✅** (180x speedup empirical, parser_used=pymupdf4llm, HMAC INTACT). **Sprint 8 fecha aplicação completa**: hardware health + LGPD compliance + security hardening + observability + DR + documentation accurate.

**Eric directive Option A** (Smith preference): expanded scope ~17 stories absorber TODOS os CRITICAL + HIGH antes Sprint 9.

---

## 📊 Sprint 8 Scoreboard Target

| Dimensão (Smith ultrathink) | Pre-Sprint-8 | Target Post-Sprint-8 |
|---|---|---|
| User Workflow E2E | 65/100 | **100/100** |
| Hardware VPS Health | 50/100 | **100/100** |
| Marker OCR Subprocess | 45/100 | **100/100** |
| LGPD Compliance + Audit | 55/100 | **100/100** |
| Security Production | 50/100 | **100/100** |
| Monitoring Observability | 30/100 | **90+/100** |
| Documentation User | 25/100 | **95+/100** |
| Production Readiness DR | 40/100 | **95+/100** |
| **Cumulative score** | **56/100 INFECTED** | **95+/100 CONTAINED+GREENLIGHT OR CLEAN** |

---

## 🚀 Sprint 8 Execution Phases

### Phase A — CRITICAL Emergency (~10-13h estimate, ~5-7h actual)

**Goal:** Resolver 6 CRITICAL findings ANTES de qualquer feature work. Production stops degrading.

**Pattern:** Operator + Neo + Architect parallel quando independentes.

| # | Story | Owner | Dependencies | Estimate | Smith Ref |
|---|-------|-------|--------------|----------|-----------|
| **0** | **Disk cleanup ≥80% target + monitoring alert** | @devops Operator | NONE (pode iniciar imediato) | 1h | F-CRIT-01 |
| **1.5** | **Tempfile cleanup audit + integration test** | @dev Neo | NONE (pode iniciar paralelo Story #0) | 3h | F-CRIT-02 |
| **1.6** | **/docs + /openapi.json disable produção (REVISOR_ENV=production guard)** | @dev Neo | NONE (paralelo) | 1h | F-CRIT-03 |
| **2** | **Marker cache volume mount (escalated from MEDIUM to CRITICAL)** | @devops Operator | NONE (paralelo) | 1-2h | F-CRIT-04 |
| **2.5** | **README rewrite reflect v0.2.10.0 + SaaS production state** | @devops + @architect | NONE (paralelo) | 2-3h | F-CRIT-05 |
| **7** | **Backup automation explicit (cron + retention 30d + restore runbook)** | @devops + @architect | NONE (paralelo, mas ADR review needed) | 3-4h | F-CRIT-06 |

**Phase A parallel execution opportunity:** Stories #0, #1.5, #1.6, #2, #2.5, #7 podem rodar **PARALLEL** (sem dependencies cross-story). Speed bonus pattern Sprint 7 ~95% suggest ~5-7h actual cumulative.

**Phase A acceptance:** Smith mini-verify (~30min) verificar 6 CRITICAL RESOLVED antes Phase B.

---

### Phase B — HIGH Cleanup (~10-13h estimate, ~5-7h actual)

**Goal:** Resolver 11 HIGH findings. Score 100/100 atingível.

| # | Story | Owner | Dependencies | Estimate | Smith Ref |
|---|-------|-------|--------------|----------|-----------|
| **8** | **DNS subdomains uptime+cockpit OR /painel implementation per Eric R8.1 directive** | @devops + @architect Sati design | Phase A done (no blocking) | 2-3h | F-HIGH-01 |
| **9** | **claudinoinsights.com root homepage (Cloudflare Pages)** | @devops Operator | NONE | 1-2h | F-HIGH-02 |
| **10** | **Traefik cleanup composite: /api/analytics 401 + dashboard disable + traefik-g9oq-traefik-1 stale removal** | @devops Operator | NONE | 3h | F-HIGH-03 + F-HIGH-06 + F-HIGH-11 |
| **11** | **Backup encryption GPG OR LUKS (decision Architect ADR + Operator implementation)** | @architect ADR + @devops | Story #7 (Phase A) done | 2-3h | F-HIGH-09 |
| **12** | **API JSON responses for /revisar errors (Accept header detection)** | @dev Neo | Story #1.5 (Phase A) done | 1h | F-HIGH-07 |
| **13** | **/health endpoint + HEAD / method support** | @dev Neo | NONE | 1h | F-HIGH-04 + F-HIGH-05 |
| **8.5** | **Backup retention 30 days enforcement** | @devops Operator | Story #7 (Phase A) done | 30min | F-HIGH-08 |
| **8.6** | **Image backup tag SOP retain N≥4 (versioned ultimate backups)** | @devops Operator | NONE | 30min | F-HIGH-10 |

**Phase B parallel execution:** Stories #8, #9, #10, #11, #12, #13, #8.5, #8.6 paralelizáveis (após Phase A done). ~5-7h actual cumulative.

**Phase B acceptance:** Smith mini-verify (~30min) verificar 11 HIGH RESOLVED antes Phase C.

---

### Phase C — Original LOWs Cleanup + Cenário Y++ DoD Final Business Validation (~10-15h estimate, ~5-7h actual)

**Goal:** Original Sprint 8 v1.0 scope (6 stories) — LOWs cleanup + business validation real-world.

| # | Story | Owner | Dependencies | Estimate | Smith Ref |
|---|-------|-------|--------------|----------|-----------|
| **1** (HIGH PRIO original) | **Real CDC veículo PDF born-digital fixture (status=success exato)** | @dev Neo | Phase A done (tempfile fix + marker cache) | 30-60min | F-S7P4-MED-01 (deferred Sprint 7) |
| **3** | **Phase 4 LOWs cleanup (5 active LOWs)** | @devops + @architect | NONE | 3h | TD-SP07-P4-LOW-{01,02,03,04,05} |
| **4** | **Phase 1-3 cumulative LOWs cleanup (~10 active LOWs)** | @devops + @qa | NONE | 5h | TD-SP07-P{1,2,3}-LOW-* |
| **5** | **ADR-027 narrative refinement (RESTORES + ADDS + PRESERVES)** | @architect Aria | NONE | 1h | F-S7P4-LOW-05 |
| **6** | **Operational hygiene improvements (handoff template + Ollama changelog check)** | @devops Operator | NONE | 30min | F-S7P4-LOW-01 |
| **6.5** | **Smith ultrathink 14 LOWs absorption (cumulative)** | @devops + @dev | NONE | 4-6h | Smith F-LOW-01..14 |

**Phase C parallel execution:** Stories #1, #3, #4, #5, #6, #6.5 paralelizáveis. ~5-7h actual cumulative.

**Phase C acceptance:** Smith **ULTRATHINK re-verify** (~1h) — full 12 dimensions audit, target 95+/100 score.

---

## 🎯 Cenário Y++ DoD Final Closure (Sprint 8 close criterion)

**Sprint 8 OFICIALMENTE CLOSED quando:**

1. ✅ Phase A — 6 CRITICAL RESOLVED (Smith mini-verify confirmado)
2. ✅ Phase B — 11 HIGH RESOLVED (Smith mini-verify confirmado)
3. ✅ Phase C — Story #1 real CDC PDF status=success exato (Cenário Y++ DoD final 100%)
4. ✅ Phase C — LOWs absorbed em TECH-DEBT.md cumulative
5. ✅ Smith **ULTRATHINK re-verify** verdict CONTAINED+GREENLIGHT OR CLEAN (target 95+/100 score)
6. ✅ Sprint 8 retrospective documented
7. ✅ Sprint 9+ scope defined (remaining LOWs + features)

**Cenário Y++ DoD Final 100%** = architectural (Sprint 7) + business validation real-world (Sprint 8) + production readiness completo (Sprint 8) + observability + DR + LGPD compliance ongoing.

---

## 📋 Story Inventory (17 Total — Cross-Reference Smith Findings)

| Story | Phase | Severity | Owner | Estimate | Status | Smith Finding |
|-------|-------|----------|-------|----------|--------|---------------|
| #0 | A | CRITICAL | @devops | 1h | scoped | F-CRIT-01 disk 94% |
| #1 | C | HIGH PRIO | @dev | 30-60min | scoped | F-S7P4-MED-01 (Sprint 7 deferred) |
| #1.5 | A | CRITICAL | @dev | 3h | scoped | F-CRIT-02 tempfile LGPD §16 |
| #1.6 | A | CRITICAL | @dev | 1h | scoped | F-CRIT-03 /docs exposed |
| #2 | A | CRITICAL (escalated) | @devops | 1-2h | scoped | F-CRIT-04 marker cache |
| #2.5 | A | CRITICAL | @devops + @architect | 2-3h | scoped | F-CRIT-05 README outdated |
| #3 | C | LOW | @devops + @architect | 3h | scoped | Phase 4 LOWs (6 items) |
| #4 | C | LOW | @devops + @qa | 5h | scoped | Phase 1-3 cumulative LOWs |
| #5 | C | LOW | @architect | 1h | scoped | F-S7P4-LOW-05 ADR-027 narrative |
| #6 | C | LOW | @devops | 30min | scoped | Operational hygiene |
| #6.5 | C | LOW | @devops + @dev | 4-6h | scoped | Smith ultrathink 14 LOWs |
| #7 | A | CRITICAL | @devops + @architect | 3-4h | scoped | F-CRIT-06 backup automation |
| #8 | B | HIGH | @devops + @architect | 2-3h | scoped | F-HIGH-01 monitoring URLs |
| #8.5 | B | HIGH | @devops | 30min | scoped | F-HIGH-08 backup retention |
| #8.6 | B | HIGH | @devops | 30min | scoped | F-HIGH-10 image backup tags |
| #9 | B | HIGH | @devops | 1-2h | scoped | F-HIGH-02 homepage 404 |
| #10 | B | HIGH | @devops | 3h | scoped | F-HIGH-03 + F-HIGH-06 + F-HIGH-11 |
| #11 | B | HIGH | @architect + @devops | 2-3h | scoped | F-HIGH-09 backup encryption |
| #12 | B | HIGH | @dev | 1h | scoped | F-HIGH-07 JSON validation |
| #13 | B | HIGH | @dev | 1h | scoped | F-HIGH-04 + F-HIGH-05 /health + HEAD |

**Total: 20 stories** (17 expanded + 3 sub-stories agrupados em #8, #10, #13). Estimate ~30-40h cumulative, ~15-20h actual com Sprint 7 95% speed bonus pattern.

---

## 🔄 Workflow LMAS Skill Chain (Sprint 8 Expanded Pattern)

**Sprint 7 lesson:** Smith verify entre cada Phase consumed 2h cumulative MAS catched cascading bugs early. Net positive.

**Sprint 8 pattern:** Smith mini-verify entre Phases A/B/C (~30min each) + Smith **ULTRATHINK re-verify** após Phase C close (~1h). Total Smith time ~2.5h vs Sprint 7 ~2h.

```text
Eric directive Option A approved
  ↓
Operator update sprint-8-scope.md (THIS) ✅
  ↓
PHASE A (parallel execution):
  ├─ Operator Story #0 disk cleanup → emergency
  ├─ Neo (via Skill dev) Story #1.5 tempfile audit → code
  ├─ Neo Story #1.6 /docs disable → code
  ├─ Operator Story #2 marker cache volume mount
  ├─ Operator + Architect Story #2.5 README rewrite
  └─ Operator + Architect (via Skill architect) Story #7 backup automation
  ↓
Smith mini-verify Phase A (~30min) — confirm 6 CRIT RESOLVED
  ↓
PHASE B (parallel execution):
  ├─ Operator + Architect Story #8 DNS / painel
  ├─ Operator Story #9 homepage
  ├─ Operator Story #10 traefik cleanup
  ├─ Architect ADR + Operator Story #11 backup encryption
  ├─ Neo Story #12 JSON validation
  ├─ Neo Story #13 /health + HEAD
  ├─ Operator Story #8.5 backup retention
  └─ Operator Story #8.6 image backup tags
  ↓
Smith mini-verify Phase B (~30min) — confirm 11 HIGH RESOLVED
  ↓
PHASE C (parallel execution):
  ├─ Neo Story #1 real CDC PDF fixture → Cenário Y++ DoD final business validation
  ├─ Operator + Architect Story #3 Phase 4 LOWs
  ├─ Operator + QA Story #4 Phase 1-3 LOWs
  ├─ Architect Story #5 ADR-027 narrative refinement
  ├─ Operator Story #6 operational hygiene
  └─ Operator + Neo Story #6.5 Smith 14 LOWs
  ↓
Smith ULTRATHINK re-verify (~1h) — full 12 dimensions audit
  ↓
IF Smith verdict CONTAINED+GREENLIGHT OR CLEAN (target 95+/100):
  → Sprint 8 retrospective + Sprint 8 closure declaration
  → Cenário Y++ DoD Final 100% atingido (architectural + business + production readiness)
  → Sprint 9+ scope definition

IF Smith verdict still INFECTED (gaps remain):
  → Sprint 8 mini-iteration (specific findings address)
  → Re-verify Smith
```

---

## 🚦 Eric Directive Required (Execution Order)

**Sprint 8 expanded scope DEFINED.** Eric escolhe execution cadence:

### Option A1: Phase A first sequential
- Phase A complete → mini-verify → Phase B → mini-verify → Phase C → ultrathink re-verify
- **Estimate:** ~15-20h actual sequential
- **Pros:** Conservative, gradual progression
- **Cons:** Longest duration

### Option A2: Full parallel (all 20 stories simultaneously)
- ALL stories iniciados em paralelo (Operator + Neo + Architect com handoffs paralelos)
- **Estimate:** ~10-13h actual full parallel (limited by longest story chain Story #11 ~3h)
- **Pros:** Fastest closure
- **Cons:** Coordination overhead, dependency conflicts (Story #1 needs #1.5 + #2 done)

### Option A3: Phase A parallel + Phases B+C parallel (RECOMMENDED Smith preference)
- Phase A 6 stories paralelas (~5-7h actual)
- Mini-verify Phase A
- Phases B+C 14 stories paralelas (~7-10h actual)
- Smith ultrathink re-verify
- **Estimate:** ~13-17h actual com 1 mini-verify + 1 ultrathink re-verify
- **Pros:** Balance speed + quality gate, conservative cadence preserved
- **Cons:** Coordination Phase A → Phase B handoff

---

## 🔗 Cross-References

- **Smith ultrathink report:** `governance/qa/smith-ultrathink-aplicacao-completa-hardware-2026-05-16.md`
- **Smith cleanup cascade handoff:** `.lmas/handoffs/handoff-smith-to-operator-2026-05-16-ultrathink-cleanup-cascade.yaml`
- **Sprint 7 closure:** `governance/CHANGELOG-v0.2.10.0.md` + `governance/retrospectives/sprint-7-retrospective.md`
- **Sprint 8 scope v1.0 (deprecated):** Replaced by this version 2.0 expanded
- **TECH-DEBT.md Sprint 7 section:** Top of `governance/TECH-DEBT.md`
- **Smith Phase verifies Sprint 7:** `governance/qa/smith-verify-sprint-7-phase-{1,2,3,4}-2026-05-{15,16}.md`

---

## 📝 Sprint 8 Closure Declaration Criterion

**Sprint 8 OFICIALMENTE CLOSED quando ALL atendidos:**

1. ✅ 17 stories Done (20 sub-stories total)
2. ✅ 6 CRITICAL Smith findings RESOLVED empirical
3. ✅ 11 HIGH Smith findings RESOLVED empirical
4. ✅ Story #1 real CDC PDF status=success exato (Cenário Y++ DoD final business validation)
5. ✅ Smith ULTRATHINK re-verify verdict CONTAINED+GREENLIGHT OR CLEAN
6. ✅ Cumulative score Sprint 8 close ≥95/100 (target 100/100)
7. ✅ TECH-DEBT.md cumulative LOWs absorbed
8. ✅ Sprint 8 retrospective documented
9. ✅ Sprint 9+ scope defined

**Cenário Y++ DoD Final 100%** = architectural (Sprint 7) + business validation real-world (Sprint 8) + production readiness completo (Sprint 8).

---

*Sprint 8 scope v2.0 EXPANDED defined by @devops (Operator) following Smith ultrathink D-SMITH-S07-005 (verdict INFECTED 56/100, 51 findings) + Eric directive Option A (Smith preference). Sprint 8 v1.0 (6 stories core, ~11-12h estimate) replaced by this v2.0 (20 stories total, ~30-40h estimate, ~15-20h actual com 95% speed bonus pattern). Eric escolherá execution order A1/A2/A3 next.*
