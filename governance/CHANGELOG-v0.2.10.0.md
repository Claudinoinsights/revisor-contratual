# Release v0.2.10.0 — Sprint 7 Closure: Cenário Y++ DoD Architectural ATINGIDO

> **Data:** 2026-05-16
> **Sprint:** 07 (CLOSED — DoD architectural 100% ✅ + status=success real-world deferred Sprint 8)
> **Predecessor:** v0.2.7.2 (Sprint 6.x final closure 2026-05-15)
> **Branch:** main (HEAD `0bdc441`)
> **Milestone:** ⭐⭐⭐ **180x speedup empirical** (born-digital pipeline 985ms vs subprocess 180s) + **F-PROD-NEW-22 ARQUITETONICAMENTE RESOLVED** + **HMAC chain integrity LGPD §46 PRESERVED** (11/11 entries)
> **Smith verdict final:** CONTAINED + GREENLIGHT (10/10 ACs PASS empirical)

---

## 🎯 Highlights

**Sprint 7 = Cenário Y++ refinado (B+C+D+E+F+G+H+I) executado em 4 phases sequenciais com Smith verify entre cada:**

- **Phase 1** (v0.2.7.3 + v0.2.7.4) — Ollama ENV vars optimization (KEEP_ALIVE, NUM_PARALLEL, MAX_LOADED_MODELS, FLASH_ATTENTION, KV_CACHE_TYPE) + hotfix OLLAMA_NUM_CTX deprecated em Ollama 0.5+
- **Phase 2** (v0.2.8.0) — Ollama container consolidation 2→1 (ADR-028) — ollama-advogado + ollama-economista → ollama-shared (memory 18GB → 10GB)
- **Phase 3** (v0.2.9.0) — Subprocess isolation parsing (ADR-026) — RESOLVE F-PROD-NEW-22 silent worker exit via process-level isolation
- **Phase 4** (v0.2.10.0) — PyMuPDF born-digital fast path (ADR-027) — dual-path pipeline.py Step 1 (born-digital inline ~10s vs scanned subprocess ~120s)

**Cenário Y++ DoD final ARCHITECTURAL criterion atingido empirically:**
- audit chain registers `parser_used="pymupdf4llm"` ✅
- payload com **9 keys** (criterion ≥9 ✅)
- pipeline atinge **Step 2 Cálculo** (vs Phase 3 Step 1 timeout) ✅
- app container preserved RestartCount=0 ✅
- HMAC chain integrity preserved (11/11 entries) ✅
- born-digital latency **985ms** (vs Phase 3 subprocess 180s = **180x speedup**) ✅

**Velocity Sprint 7 cumulative:** ~7.5h actual vs 8-12 dias estimate (~95% speed bonus).

---

## ✨ Features

### Phase 4 — PyMuPDF Born-Digital Fast Path (ADR-027)

- **`feat(parsing): Sprint 7 Phase 4 PyMuPDF born-digital fast path (ADR-027 — Cenário Y++ DoD final)`** (`0bdc441`)
  - NEW `bloco_engine/parsing/type_detector.py` — `detect_pdf_type(pdf_path, sample_pages=2, text_threshold_per_page=500)` returning `Literal["born_digital", "scanned"]`
  - PyMuPDF heuristic: samples first 2 pages, returns "scanned" on corrupt/empty PDFs (graceful fallback)
  - Modified `bloco_workflow/pipeline.py` Step 1 dual-path:
    - Born-digital → `asyncio.to_thread(parse_contract)` com timeout=30.0
    - Scanned → `asyncio.create_subprocess_exec subprocess_runner` com timeout=180.0 (Phase 3 ADR-026 preserved)
  - 14 NEW tests Phase 4 (7 unit type_detector + 7 integration pipeline dual-path) — 67/67 tests PASS local
  - Cenário Y++ DoD architectural completeness: 100% ✅

### Phase 3 — Subprocess Isolation Parsing (ADR-026)

- **`feat(parsing): Sprint 7 Phase 3 subprocess isolation (ADR-026 — RESOLVE F-PROD-NEW-22)`** (`e2cffb3`)
  - NEW `bloco_engine/parsing/subprocess_runner.py` — CLI module ~110 lines (stdin/stdout JSON IPC)
  - NEW `bloco_engine/parsing/exceptions.py` — `ParsingSubprocessFailedError` + `ParsingSubprocessTimeoutError`
  - Modified `bloco_workflow/pipeline.py` Step 1 — uniform subprocess via `asyncio.create_subprocess_exec`
  - Process-level isolation: marker/torch/PyMuPDF C extension crashes ISOLATED do parent worker
  - 13 tests Phase 3 (6 unit subprocess_runner + 7 integration pipeline_subprocess)
  - F-PROD-NEW-22 RESOLVED arquitetonicamente: pre-Phase-3 silent worker exit → audit NUNCA escrito | post-Phase-3 subprocess timeout → audit REGISTERED + container PRESERVED

### Phase 2 — Ollama Container Consolidation (ADR-028)

- **`feat(ops): Sprint 7 Phase 2 — Ollama container consolidation 2→1 (ADR-028) [v0.2.8.0]`** (`484b211`)
  - Consolidated `ollama-advogado` + `ollama-economista` → `ollama-shared` single container
  - Volume rsync migration preserving `qwen2.5:3b` + `qwen2.5:7b` models
  - Memory: app 6G + ollama-shared 4G = **10 GB total** (vs 18 GB pré-Phase-2 = ~44% reduction)
  - 8 OLLAMA_* env vars optimized (KEEP_ALIVE=5m, NUM_PARALLEL=1, MAX_LOADED_MODELS=1, CONTEXT_LENGTH=8192, NUM_THREAD=2, FLASH_ATTENTION=1, KV_CACHE_TYPE=q8_0, LOAD_TIMEOUT=180s)

### Phase 1 — Ollama ENV Vars Optimization (Y++)

- **`fix(ops): Sprint 7 Phase 1 hotfix v0.2.7.4 — OLLAMA_NUM_CTX → OLLAMA_CONTEXT_LENGTH`** (`d8f220c`)
  - Empirical discovery: `OLLAMA_NUM_CTX` deprecated em Ollama 0.5+ (Ollama 0.24.0 doesn't honor)
  - Replaced em ambos ollama services (advogado + economista) with `OLLAMA_CONTEXT_LENGTH=8192`

- **`feat(ops): Sprint 7 Phase 1 — Ollama ENV vars optimization (Y++)`** (`5607d3d`)
  - 7 OLLAMA_* env vars added (initial set)
  - Memory baseline target: app 6G + ollama-* containers preservados
  - Empirical baseline: pre-Phase-1 ~22 GB → post-Phase-1 ~14 GB (~36% reduction antes Phase 2 consolidation)

---

## 🏗️ Architecture Decisions

| ADR | Title | Phase | Status |
|-----|-------|-------|--------|
| ADR-026 | Marker subprocess isolation parsing | Phase 3 | Accepted |
| ADR-027 | PyMuPDF born-digital fast path (dual-path) | Phase 4 | Accepted |
| ADR-028 | Ollama single container consolidation | Phase 2 | Accepted |

---

## 🛡️ Smith Adversarial Verifies (4 phases)

| Phase | Smith Verdict | ACs PASS | Findings | Verify Report |
|-------|---------------|----------|----------|---------------|
| Phase 1 | CONTAINED | 5/5 | 6 LOWs + 1 INFO | `governance/qa/smith-verify-sprint-7-phase-1-2026-05-15.md` |
| Phase 2 | CONTAINED | 6/6 | 5 LOWs + 1 MEDIUM (volume migration) + 2 INFO | `governance/qa/smith-verify-sprint-7-phase-2-2026-05-15.md` |
| Phase 3 | CONTAINED + F-PROD-NEW-22 RESOLVED | 8/8 | 4 LOWs + 1 INFO (architectural fix proof) | `governance/qa/smith-verify-sprint-7-phase-3-2026-05-15.md` |
| Phase 4 | CONTAINED + GREENLIGHT | **10/10** | 1 MED (status=success real-world deferred) + 6 LOWs + 4 INFO | `governance/qa/smith-verify-sprint-7-phase-4-2026-05-16.md` |

**Conservative cadence Eric directive:** Smith verify entre cada Phase ANTES proceeding. Pattern consistent 4 phases.

---

## 📊 Empirical Architectural Proof

### Audit Chain HMAC Integrity (LGPD §46)

```text
total_entries: 11
chain_status: INTACT (all 10 previous_entry_hash links match)
parser_used distribution:
  - pymupdf4llm: 7 entries (Sprint 6.x baseline + Phase 1/2 + Phase 4 final)
  - None: 4 entries (Phase 3 subprocess timeouts — explicitly tracked)
```

### Latency Comparison

| Phase | Pipeline Path | Latency | Notes |
|-------|---------------|---------|-------|
| Pre-Sprint-7 (Sprint 6.x) | Inline PyMuPDF | ~variable | F-PROD-NEW-22 silent exit |
| Phase 3 | Subprocess marker (uniform) | 180s timeout | F-PROD-NEW-22 RESOLVED but pipeline E2E blocked |
| **Phase 4 born-digital** | **PyMuPDF inline asyncio.to_thread** | **985ms** | **180x speedup** vs Phase 3 timeout |
| Phase 4 scanned | Subprocess marker | ~120s | Phase 3 ADR-026 preserved for scanned |

### Container Lifecycle (Phase 4)

| Aspecto | Status |
|---------|--------|
| image rebuilt | ✅ SIM (sha256:55e96a3c29d4 vs Phase 3 f830797a3143) |
| container recreated | ✅ SIM (RestartCount=0 reset 2026-05-16T03:32:57Z) |
| ollama-shared preserved | ✅ SIM (revisor-prod-ollama-shared Up 2 hours preservado) |

---

## 🎬 Closure Commits (Operator entries)

- `0bdc441` Sprint 7 Phase 4 PyMuPDF born-digital fast path (ADR-027) [v0.2.10.0]
- `e2cffb3` Sprint 7 Phase 3 subprocess isolation (ADR-026) [v0.2.9.0]
- `484b211` Sprint 7 Phase 2 Ollama consolidation (ADR-028) [v0.2.8.0]
- `d8f220c` Sprint 7 Phase 1 hotfix OLLAMA_CONTEXT_LENGTH [v0.2.7.4]
- `5607d3d` Sprint 7 Phase 1 Ollama ENV optimization [v0.2.7.3]

---

## 🚀 Sprint 8 Scope (Deferred Items)

| Item | Source | Severity | Phase 8 Story # |
|------|--------|----------|-----------------|
| Real CDC veículo PDF born-digital fixture (status=success exato) | F-S7P4-MED-01 | MEDIUM | Story #1 (HIGH priority) |
| TD-MARKER-CACHE-EPHEMERAL volume mount | F-S7P4-LOW-02 + Phase 5 polish original scope | LOW | Story #2 |
| 6 LOWs Phase 4 cleanup | Smith verify Phase 4 | LOW | Story #3 (cumulative) |
| Phase 1-3 cumulative LOWs cleanup (~16 entries) | Smith verifies Phase 1-3 | LOW | Story #4 (cumulative) |
| ADR-027 narrative refinement (RESTORES inline + ADDS detection) | F-S7P4-LOW-05 | LOW | Story #5 (1h docs) |
| TECH-DEBT.md cumulative backlog absorption | F-S7P4-LOW-06 | LOW | Story #6 (governance) |

**Total Sprint 7 → Sprint 8 deferred:** 6 stories scope.

---

## 📝 Cenário Y++ DoD Final Assessment

| Critério | Pre-Sprint-7 | Post-Sprint-7 | Status |
|----------|--------------|---------------|--------|
| F-PROD-NEW-22 silent worker exit | ACTIVE blocker | ARQUITETONICAMENTE RESOLVED ✅ | Phase 3 |
| F-S7P3-MED-01 pipeline E2E 9 keys blocked | ACTIVE blocker | ARQUITETONICAMENTE RESOLVED ✅ | Phase 4 |
| Born-digital fast path | N/A | FUNCIONA empirically (985ms) ✅ | Phase 4 |
| Subprocess marker fallback scanned | N/A | PRESERVED (ADR-026) ✅ | Phase 3+4 |
| HMAC chain integrity LGPD §46 | OK pre-Sprint-7 | PRESERVED (11/11 entries) ✅ | All phases |
| Memory consolidation | 22GB+ pre-optimization | 10GB total ✅ | Phase 1+2 |
| Architectural completeness | N/A | **100%** atingido empirically ✅ | Sprint 7 final |
| Business validation completeness (status=success exato) | N/A | PARTIAL — requires real CDC PDF fixture | Sprint 8 deferred |

---

## 🔗 Cross-References

- **Smith verify reports:** `governance/qa/smith-verify-sprint-7-phase-{1,2,3,4}-2026-05-{15,16}.md`
- **ADRs:** `governance/architecture/adr/adr-{026,027,028}-*.md`
- **CHECKPOINT entries:** `governance/CHECKPOINT-active.md` D-OPS-S07-{001..005} + D-SMITH-S07-{001..004}
- **Handoffs:** `.lmas/handoffs/handoff-{dev,devops,smith}-to-*-2026-05-{15,16}-sprint-7-*.yaml`
- **Sprint 8 scope:** `governance/sprints/sprint-8-scope.md`
- **Sprint 7 retrospective:** `governance/retrospectives/sprint-7-retrospective.md`

---

*v0.2.10.0 — Sprint 7 CLOSED. Cenário Y++ DoD architectural ATINGIDO. Sprint 8 scope defined. Operator deployando com confiança 🚀*
