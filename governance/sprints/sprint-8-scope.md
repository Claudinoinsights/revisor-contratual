---
type: sprint-scope
title: "Sprint 8 Scope — DoD Business Validation + Tech Debt Cleanup"
sprint: 08
status: scoped
start_date: TBD (post Sprint 7 closure 2026-05-16)
end_date: TBD
predecessor_sprint: 07 (Cenário Y++ DoD Architectural)
project: revisor-contratual
tags:
  - project/revisor-contratual
  - sprint-08
  - scope
  - business-validation
  - tech-debt-cleanup
---

# Sprint 8 Scope — DoD Business Validation + Tech Debt Cleanup

## Sprint Goal

**Cenário Y++ DoD Final 100% (architectural + business validation real-world)** + **Sprint 7 cumulative LOWs cleanup** + **operational hygiene improvements**.

**Não é "Sprint 7.5"** — é Sprint 8 dedicado a:
1. Real-world business validation (status=success exato com real CDC veículo PDF)
2. TD-MARKER-CACHE-EPHEMERAL polish (cold start optimization)
3. Cumulative tech debt absorption (~16 LOWs Sprint 7 Phase 1-4)
4. Operational hygiene (handoff template, env hygiene VPS)

---

## Stories

### Story #1 — Real CDC Veículo PDF Born-Digital Fixture (HIGH PRIORITY)

**Origin:** Smith F-S7P4-MED-01 (D-SMITH-S07-004)
**Owner:** @dev (Neo)
**Estimate:** 30-60min fixture creation + integration test

**Description:**
Gerar real CDC veículo PDF born-digital com regex-extractable financial fields para empirical proof Cenário Y++ DoD final criterion (`status=success` exato).

**Acceptance Criteria:**
1. Real CDC veículo PDF gerado via PyPDF2 OR fitz contract template
2. PDF born-digital classified por type_detector ✅
3. PDF contém regex-extractable: valor_financiado + n_parcelas + taxa + prazo
4. POST /revisar com PDF retorna status=success ✅
5. audit chain registra parser_used=pymupdf4llm + 9 keys + status=success
6. Pipeline atinge Step 9 (Veredito final) — não apenas Step 2 Cálculo
7. Latency < 30s (born-digital fast path target)

**Smith verify expected:** CLEAN OR CONTAINED+GREENLIGHT (Cenário Y++ DoD final 100% atingido)

---

### Story #2 — TD-MARKER-CACHE-EPHEMERAL Volume Mount (MEDIUM PRIORITY)

**Origin:** TD-SP07-P4-LOW-MARKER-CACHE-EPHEMERAL + TD-SP07-P3-LOW-MARKER-CACHE-VOLUME (D-SMITH-S07-003+004)
**Owner:** @devops (Operator)
**Estimate:** 1-2h volume mount config + container recreate verify

**Description:**
Persistir marker model cache entre container recreates via Docker volume mount. Subprocess marker actualmente re-download cada container recreate (~2-3min cold start scanned PDFs).

**Acceptance Criteria:**
1. docker-compose.prod.yml adiciona volume `marker-cache:/root/.cache/marker` no app service
2. Volume named declaration adicionada
3. Container recreate preserva cache marker (verify: cold start time <30s vs ~2-3min pré-fix)
4. Audit chain integrity preserved
5. Pipeline scanned PDFs continua funcionando normalmente

**Smith verify expected:** CONTAINED ou CLEAN

---

### Story #3 — Phase 4 LOWs Cleanup (LOW PRIORITY — Cumulative)

**Origin:** TECH-DEBT.md Sprint 7 closure (5 active LOWs Phase 4)
**Owner:** @devops (Operator) + @architect (Aria)
**Estimate:** ~3h cumulative

**Items:**
1. **TD-SP07-P4-LOW-OLLAMA-NAME-CONVENTION** (15min) — Operator handoff template usar full compose names
2. **TD-SP07-P4-LOW-TRAEFIK-G9OQ-STALE** (30min) — Cleanup VPS stale traefik-g9oq stack
3. **TD-SP07-P4-LOW-ADR-027-NARRATIVE** (1h) — ADR-027 narrative refinement (RESTORES + ADDS + PRESERVES)
4. **TD-SP07-P4-LOW-MARKER-CACHE-EPHEMERAL** — RESOLVED via Story #2 (consolidated)

---

### Story #4 — Phase 1-3 LOWs Cumulative Cleanup (LOW PRIORITY)

**Origin:** TECH-DEBT.md Sprint 7 closure (~10 active LOWs Phase 1-3)
**Owner:** @devops + @qa
**Estimate:** ~5h cumulative

**Items prioritized:**
1. **TD-SP07-P3-LOW-PRE-WARM-MODELS** (1-2h) — Pre-warm marker models em Dockerfile RUN
2. **TD-SP07-P3-LOW-PSUTIL-MEMORY-VERIFICATION** (30min) — Document born-digital path memory profile
3. **TD-SP07-P2-LOW-OLLAMA-LOAD-TIMEOUT-180S** (30min) — Stress test cold start
4. **TD-SP07-P2-LOW-NUM-THREAD-2-EMPIRICAL** (30min) — Benchmark NUM_THREAD=2 vs default
5. **TD-SP07-P2-LOW-FLASH-ATTENTION-SUPPORT** (15min) — Verify Ollama logs flash_attn enabled
6. **TD-SP07-P2-LOW-KV-CACHE-Q8-VS-F16** (1h) — Quality regression test q8_0 vs f16
7. **TD-SP07-P1-LOW-MAX-LOADED-MODELS-1-IMPACT** (30min) — Measure model swap latency
8. **TD-SP07-P1-LOW-NUM-PARALLEL-1-CONCURRENCY** (1h) — Stress test concurrent /revisar
9. **TD-SP07-P1-LOW-KEEP-ALIVE-5M-IDLE-MEMORY** (30min) — Measure idle vs hot pipeline latency

---

### Story #5 — ADR-027 Narrative Refinement (LOW PRIORITY)

**Origin:** Smith F-S7P4-LOW-05 (D-SMITH-S07-004)
**Owner:** @architect (Aria)
**Estimate:** 1h docs refinement

**Description:**
Refinar ADR-027 narrative para refletir histórico evolução: Phase 4 RESTORES inline (Sprint 6.x baseline) + ADDS detection branch + PRESERVES subprocess fallback (Phase 3 ADR-026).

**Acceptance Criteria:**
1. ADR-027 atualizado com seção "Histórico Evolução"
2. Audit chain pre-Phase-4 (lines 1, 3-7 com pymupdf4llm) referenciado como Sprint 6.x baseline
3. Phase 3 break (uniform subprocess parser=None) explicado
4. Phase 4 restoration narrative ("RESTORES + ADDS + PRESERVES") clarified
5. Cross-reference ADR-026 (subprocess scanned preserved) explicit

---

### Story #6 — Operational Hygiene Improvements (LOW PRIORITY)

**Origin:** Smith F-S7P4-LOW-01 + cumulative observations
**Owner:** @devops (Operator)
**Estimate:** ~30min process improvements

**Items:**
1. Operator handoff template — sempre full compose project names em yaml verifies
2. Pre-deploy Ollama official changelog check antes implementing optimization specs
3. Operator pre-deploy fixture verification (ensure smoke test PDFs adequate)

---

## Sprint 8 Stretch Goals (Optional)

Se Stories #1-#6 completed early, considerar:

- **Story #7** — Sprint 6.x AGGRESSIVE backlog absorption (5 active TDs em TECH-DEBT.md Sprint 6.x section): TD-SP06-MARKER-DEFERRED, TD-SP06-VAULT-ONLY-10-DOCS, TD-SP06-SENTENCE-TRANSFORMERS-MISSING, TD-SP06-PYTEST-DEPS-PYTHON-3-14, TD-SP06-MVP-MODALIDADES-RESTRITAS
- **Story #8** — Pipeline E2E full benchmarking (born-digital + scanned + mixed PDFs across multiple modalidades)
- **Story #9** — CHECKPOINT-active.md size optimization (438KB → archive Sprint 7 entries para CHECKPOINT-history-phase-2.md)

---

## Sprint 8 Estimate Summary

| Story | Priority | Estimate |
|-------|----------|----------|
| #1 Real CDC Fixture | HIGH | 30-60min |
| #2 Marker Cache Volume | MEDIUM | 1-2h |
| #3 Phase 4 LOWs Cleanup | LOW | ~3h |
| #4 Phase 1-3 LOWs Cleanup | LOW | ~5h |
| #5 ADR-027 Narrative | LOW | 1h |
| #6 Operational Hygiene | LOW | 30min |
| **Sprint 8 core total** | — | **~11-12h** |
| Stretch Goals (#7-#9) | OPTIONAL | +5-10h |

**Estimate vs reality:** Sprint 7 ~95% speed bonus (7.5h actual vs 8-12 dias estimate). Se mantido: Sprint 8 core ~11-12h estimate → ~6-9h actual.

---

## Conservative Cadence Pattern (Sprint 7 lesson)

Manter pattern Sprint 7:
- Smith verify entre cada Story (NOT entre cada commit)
- Architect Skill *spec ANTES Neo implement
- Operator deploy + Smith verify ANTES proceeding next Story
- Eric directives en stages (pause + decision points)

---

## Cenário Y++ DoD Final Criterion (Sprint 8 Closure)

**Sprint 8 OFICIALMENTE CLOSED** quando:
1. ✅ Story #1 — Real CDC PDF born-digital → status=success exato com 9 keys (Smith verify CLEAN)
2. ✅ Story #2 — Marker cache persistido (cold start <30s scanned PDFs)
3. ✅ Stories #3-#6 — LOWs cleanup completed
4. ✅ Smith verify final Sprint 8 — CONTAINED+GREENLIGHT OR CLEAN
5. ✅ Sprint 8 retrospective documented

**Cenário Y++ DoD final 100%** = architectural (Sprint 7) + business validation real-world (Sprint 8).

---

## Cross-References

- **Sprint 7 retrospective:** `governance/retrospectives/sprint-7-retrospective.md`
- **Sprint 7 CHANGELOG:** `governance/CHANGELOG-v0.2.10.0.md`
- **Sprint 7 TECH-DEBT.md section:** Top of `governance/TECH-DEBT.md`
- **Smith verify reports Sprint 7:** `governance/qa/smith-verify-sprint-7-phase-{1,2,3,4}-2026-05-{15,16}.md`
- **ADRs Sprint 7:** `governance/architecture/adr/adr-{026,027,028}-*.md`

---

*Sprint 8 scope defined by @devops (Operator) following Sprint 7 closure 2026-05-16. Eric directive Opção A executed. Cenário Y++ DoD final business validation deferred from Sprint 7 absorbed em Sprint 8 Story #1 priority HIGH.*
