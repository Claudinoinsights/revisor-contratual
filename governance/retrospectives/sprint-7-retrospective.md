---
type: retrospective
title: "Sprint 7 Retrospective — Cenário Y++ DoD Architectural"
sprint: 07
status: closed
start_date: 2026-05-15
end_date: 2026-05-16
duration_actual: ~7.5h cumulative
duration_estimate: 8-12 dias
velocity_speed_bonus: ~95%
project: revisor-contratual
participants:
  - "@architect (Aria) — ADR-026 + ADR-027 + ADR-028 specs"
  - "@dev (Neo) — implementação 4 phases (subprocess + dual-path + ENV optimization)"
  - "@devops (Operator) — 5 deploys VPS (v0.2.7.3 + 7.4 + 8.0 + 9.0 + 10.0)"
  - "@smith (Nemesis) — 4 adversarial verifies (1 per phase)"
  - "Eric Claudino — directives + closure decisions"
tags:
  - project/revisor-contratual
  - sprint-07
  - retrospective
  - cenario-y-plus-plus
  - closure
---

# Sprint 7 Retrospective — Cenário Y++ DoD Architectural

## Sprint Goal

**Cenário Y++ refinado (B+C+D+E+F+G+H+I)** — endereçar Sprint 6.x F-PROD-NEW-22 architectural blocker (silent worker exit pós OCR) + atingir Cenário Y++ DoD final criterion (pipeline E2E REAL com ≥9 audit keys + parser_used registered + container preserved).

## Outcome

✅ **DoD Architectural 100% atingido empirically.**
⚠️ **DoD Business Validation deferred to Sprint 8** (real CDC PDF fixture com financial fields).

**Smith verdict final:** CONTAINED + GREENLIGHT (10/10 ACs PASS empirical, 180x speedup proven, HMAC chain INTACT).

---

## What Went Well ✅

### 1. Conservative Cadence Pattern (Smith verify entre cada Phase)

Eric directive Smith verify ANTES proceeding next Phase pagou consistently:
- **Phase 1 → Phase 2:** Smith CONTAINED catched OLLAMA_NUM_CTX deprecated → hotfix imediato v0.2.7.4
- **Phase 2 → Phase 3:** Smith CONTAINED catched terminology imprecision (image preserved vs container instance) → ADR-026 absorption
- **Phase 3 → Phase 4:** Smith CONTAINED + F-PROD-NEW-22 RESOLVED architecturally (audit chain growth empirical proof)
- **Phase 4 → Closure:** Smith CONTAINED + GREENLIGHT (10/10 ACs PASS, 180x speedup proven)

**Lesson:** Conservative cadence cost ~30min Smith verify per phase = 2h cumulative. Avoided cascading bugs that would cost dias. Net positive.

### 2. Speed Bonus Velocity (~95%)

| Phase | Estimate (Aria) | Actual (cumulative) | Speed Bonus |
|-------|-----------------|---------------------|-------------|
| Phase 1 | 1-2 dias | ~1h | ~95% |
| Phase 2 | 4-6 dias | ~1h | ~98% |
| Phase 3 | 1-2 dias | ~3h | ~85% |
| Phase 4 | 1.5-2 dias | ~2h Neo + ~25min Operator | ~95% |
| **Total Sprint 7** | **8-12 dias** | **~7.5h** | **~95%** |

**Lesson:** Pattern confirmed. LMAS Skill chain (Architect → Neo → Operator → Smith) com handoffs YAML structurados elimina re-context overhead.

### 3. Empirical Proof Architectural

Phase 4 proof EMPIRICAL (audit chain analysis):
- Pre-Phase-4 (lines 8-10): parser=None subprocess timeout
- Post-Phase-4 (line 11): parser=pymupdf4llm + Step 2 reached + 985ms latency
- **180x speedup quantitative empirical** (vs 180s subprocess timeout)
- HMAC chain integrity preserved (11/11 entries) — LGPD §46 robusto

**Lesson:** Architectural proofs com NUMBERS empíricos (audit data + latency metrics) eliminam disputes interpretativas. Smith verdict baseado em SSH probes objetivos.

### 4. ADR-Driven Architecture (3 ADRs Sprint 7)

ADRs criadas Sprint 7:
- ADR-026 Marker subprocess isolation parsing (Phase 3)
- ADR-027 PyMuPDF born-digital fast path dual-path (Phase 4)
- ADR-028 Ollama single container consolidation (Phase 2)

Cada ADR foi spec ANTES implementation + Smith verified spec compliance pós-deploy. Zero invention pattern preserved.

**Lesson:** ADR-driven workflow elimina "guess implementation" risk. Aria spec → Neo implement contra spec → Smith verify spec compliance.

### 5. Operator Honesty Score Evolution

| Phase | Honesty Score | Notes |
|-------|---------------|-------|
| Phase 1 | 4/6 | Initial deploy report |
| Phase 2 | 4/7 | Volume migration (+1 step rigor) |
| Phase 3 | **5/5** | ADR-026 terminology precision absorbed (image rebuilt vs container preserved) |
| Phase 4 | **5/5** | Pattern maintained — terminology precision per ADR-026 |

**Lesson:** Smith feedback ABSORBED iteratively em handoff narratives. Negative feedback from Phase 1+2 became positive pattern Phase 3+4. Smith adversarial review = quality multiplier real, não burocracy.

---

## What Didn't Go Well ❌

### 1. Test PDF Inline Lacks Financial Fields (F-S7P4-MED-01)

Phase 4 smoke test usou test PDF gerado inline via fitz (lacks `valor_financiado` + `n_parcelas` extractable via regex). Resultado: pipeline atingiu Step 2 mas status=FAILED business validation (NÃO crash).

**Impact:** Cenário Y++ DoD final criterion architectural 100% atingido, mas `status=success` exato real-world não empirically demonstrado. Deferred to Sprint 8 Story #1.

**Root cause:** Operator não preparou real CDC veículo PDF born-digital fixture antes do smoke test. PDF inline foi quick-and-dirty para verificar dual-path branch.

**Mitigation Sprint 8:** Story #1 priority HIGH — real CDC PDF fixture com regex-extractable financial fields.

### 2. Phase 3 Subprocess Timeout 180s NÃO Resolved Pipeline E2E

Phase 3 (ADR-026 subprocess isolation) RESOLVED F-PROD-NEW-22 silent worker exit ARQUITETONICAMENTE (audit registered + container preserved), MAS pipeline E2E ainda timeout 180s para todos os PDFs (subprocess overhead + cold marker model load).

**Impact:** F-S7P3-MED-01 detected by Smith Phase 3 verify. Required Phase 4 dual-path para resolver.

**Root cause:** Aria ADR-026 spec assumed marker subprocess overhead aceitável para Sprint 7 scope. Realidade: subprocess + cold marker = 180s timeout para born-digital pequeno (que deveria ser ~1s).

**Mitigation:** Phase 4 dual-path PyMuPDF inline born-digital path + preserved subprocess scanned path. Both paths funcionam corretamente.

### 3. Operator Handoff Phase 4 Terminology Imprecision (LOW)

Smith F-S7P4-LOW-01: Operator usou `ollama-shared` em vez de `revisor-prod-ollama-shared` (compose project prefix) em handoff yaml. AC-8 inicialmente FALHOU during Smith verify.

**Impact:** ~2min Smith investigation extra para resolver. Não-bloqueante.

**Mitigation Sprint 8:** Operator handoff template — sempre full compose project names em yaml verifies.

### 4. Marker Cache Ephemeral (TD-MARKER-CACHE-EPHEMERAL — LOW)

Subprocess marker model re-download cada container recreate (~2-3min cold start). Phase 4 NÃO endereça (apenas dual-path + scanned ainda usa subprocess).

**Impact:** Cold start latency para scanned PDFs ~2-3min adicional vs ~120s warm.

**Mitigation Sprint 8:** Story #2 — volume mount /root/.cache/marker persistir entre image rebuilds.

### 5. Phase 1 OLLAMA_NUM_CTX Deprecation Discovery Empirical Tardia

Phase 1 deploy v0.2.7.3 falhou silently — OLLAMA_NUM_CTX env var não honrada em Ollama 0.5+ (Ollama 0.24.0). Discovery via Smith verify Phase 1 → hotfix v0.2.7.4 (OLLAMA_CONTEXT_LENGTH).

**Impact:** ~30min hotfix cycle extra Phase 1.

**Root cause:** Ollama documentation desatualizada — env var renamed sem clear deprecation warning.

**Mitigation:** Sprint 8 — Operator pre-deploy check Ollama official changelog para env var renames antes implementing optimization specs.

---

## Lessons Learned 📝

### LMAS Skill Chain Pattern

**Pattern validado Sprint 7:**

```
Eric directive
  → Architect Skill *spec ADR-{NNN}
    → Handoff Architect→Neo (ADR + 10 ACs + spec_coverage)
  → Neo Skill *develop (implementation)
    → Handoff Neo→Operator (commits + tests + version bump)
  → Operator Skill *push (deploy VPS)
    → Handoff Operator→Smith (image + container + 10 ACs)
  → Smith Skill *verify (adversarial review)
    → Handoff Smith→Operator/Architect (verdict + findings + cascade)
```

**Lesson:** Cada link da chain DEVE ser via Skill tool (feedback_workflow_via_skill_strict). Bypass Skill = perda contexto + invention risk.

### Smith Conservative Cadence > Speed

Cadence "Smith verify entre cada Phase" cost 2h cumulative MAS:
- Caught OLLAMA_NUM_CTX deprecation Phase 1 (would have cascaded)
- Caught terminology imprecision Phase 2 (absorbed em ADR-026 Phase 3)
- Caught F-PROD-NEW-22 architectural fix proof Phase 3 (validated antes Phase 4)
- Caught Phase 4 architectural completeness empirical (180x speedup proven)

**Lesson:** Smith verify = quality multiplier real. 95% speed bonus mantido COM Smith verify. Conservative cadence is FASTER than skip-and-fix.

### Empirical Proof > Theoretical Proof

Smith Phase 4 verdict baseado em:
- SSH probes objetivos (10 ACs empirical)
- audit chain HMAC integrity verification (11/11 entries)
- ADR-027 spec compliance check (7/7 markers)
- Latency measurement (985ms vs 180s = 180x speedup)
- Container lifecycle inspection (RestartCount=0 preserved)

**Lesson:** Architectural proofs com NUMBERS eliminam disputes interpretativas. "It works" ≠ proof. "Audit chain GREW + parser_used registered + Step 2 reached + container preserved + HMAC intact + 180x speedup" = proof.

### ADR-027 Narrative Refinement Needed (LOW)

ADR-027 narrative atual: "introduces dual-path". Audit chain pre-Phase-4 (lines 1, 3-7) já tinha pymupdf4llm em Sprint 6.x. Phase 3 quebrou com uniform subprocess. Phase 4 RESTORES inline + ADDS detection branch + PRESERVES subprocess fallback.

**Lesson:** ADR narratives DEVE refletir histórico evolução, não apenas estado final. Sprint 8 Story #5 — ADR-027 narrative refinement.

---

## Action Items para Sprint 8

| # | Action | Owner | Priority | Estimate |
|---|--------|-------|----------|----------|
| 1 | Real CDC veículo PDF born-digital fixture (status=success exato) | @dev | HIGH | 30-60min |
| 2 | TD-MARKER-CACHE-EPHEMERAL volume mount | @devops | MEDIUM | 1-2h |
| 3 | 6 LOWs Phase 4 cleanup | @devops + @architect | LOW | ~3h cumulative |
| 4 | Phase 1-3 cumulative LOWs cleanup | @devops + @qa | LOW | ~5h cumulative |
| 5 | ADR-027 narrative refinement | @architect | LOW | 1h |
| 6 | TECH-DEBT.md cumulative absorption | @devops | RESOLVED Sprint 7 closure | DONE |
| 7 | Operator handoff template (full compose names) | @devops | LOW | 15min |
| 8 | Pre-deploy Ollama changelog check | @devops | LOW (process) | n/a |

---

## Sprint 7 Metrics Summary

| Metric | Value |
|--------|-------|
| Stories completed | 4 phases (Phase 1-4) |
| Architectural decisions (ADRs) | 3 (ADR-026, ADR-027, ADR-028) |
| Smith verifies | 4 (1 per phase) |
| Smith verdicts | 4 CONTAINED (Phase 1-4) + 1 GREENLIGHT (Phase 4 final) |
| ACs PASS cumulative | 29/29 across 4 phases (5+6+8+10) |
| Findings CRITICAL | 0 |
| Findings HIGH | 0 |
| Findings MEDIUM | 1 (F-S7P4-MED-01 — deferred Sprint 8) |
| Findings LOW | ~20 cumulative (catalogados em TECH-DEBT.md) |
| Findings INFO | ~10 cumulative (positive observations) |
| Git tags | 5 (v0.2.7.3, v0.2.7.4, v0.2.8.0, v0.2.9.0, v0.2.10.0) |
| Container memory | 22GB+ → 10GB total (~55% reduction) |
| Pipeline born-digital latency | 180s subprocess → 985ms inline (180x speedup) |
| HMAC chain integrity | INTACT (11/11 entries — LGPD §46 preserved) |
| Velocity speed bonus | ~95% (~7.5h actual vs 8-12 dias estimate) |
| Operator honesty score | 4/6 → 5/5 progression (Phase 1 → Phase 3+4) |

---

## Closure Declaration

**Sprint 7 OFICIALMENTE CLOSED em 2026-05-16.**

- ✅ Cenário Y++ DoD Architectural: **100% atingido empirically**
- ⚠️ Cenário Y++ DoD Business Validation (status=success exato real-world): **deferred Sprint 8**
- ✅ F-PROD-NEW-22 silent worker exit: **ARQUITETONICAMENTE RESOLVED** (Phase 3 + maintained Phase 4)
- ✅ F-S7P3-MED-01 pipeline E2E 9 keys blocked: **ARQUITETONICAMENTE RESOLVED** (Phase 4 — 180x speedup)
- ✅ Memory consolidation: **22GB+ → 10GB total** (~55% reduction)
- ✅ HMAC chain integrity LGPD §46: **PRESERVED** (11/11 entries)

**Smith greenlight final:** CONTAINED + GREENLIGHT (Sprint 7 ready to close).

**Próximo:** Sprint 8 scope definition + execution.

---

*Sprint 7 retrospective documented by @devops (Operator) following Smith CONTAINED+GREENLIGHT verdict (D-SMITH-S07-004). Eric directive Opção A executed.*
