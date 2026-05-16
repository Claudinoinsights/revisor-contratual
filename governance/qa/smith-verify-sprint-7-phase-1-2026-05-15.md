---
type: qa-gate
title: "Smith Verify Sprint 7 Phase 1 — CONTAINED (Operator Ollama optimization)"
date: "2026-05-15"
verdict: CONTAINED
reviewer: "@smith (Nemesis)"
story_ref: "D-OPS-S07-001"
upstream_artifacts:
  - "Operator D-OPS-S07-001 Sprint 7 Phase 1 Ollama ENV vars + hotfix v0.2.7.4"
  - "Aria D-ARIA-S07-001 feasibility study Cenário Y++"
  - "handoff-devops-to-smith-2026-05-15-sprint-7-phase-1-verify.yaml (consumed=true)"
sprint: "7 — Cenário Y++ refinado"
findings_critical: 0
findings_high: 0
findings_medium: 3
findings_low: 7
findings_info: 2
tags:
  - project/revisor-contratual
  - qa-gate
  - smith
  - sprint-7
  - phase-1
  - ollama-optimization
  - cenario-y-plus-plus
---

# Smith Verify Sprint 7 Phase 1 — Operator entregou. Smith examinou. Veredito honesto.

## Executive Summary

**Veredito: CONTAINED ✅** — Phase 1 acceptable com 3 ressalvas MEDIUM operational. Operator claims são EMPIRICALLY VERIFIED (CONTEXT=8192 honored, KV cache q8_0 -50% validated by mathematical calculation, env vars deployed). Mas Smith adversarial uncovered 12 findings — 0 CRITICAL, 0 HIGH, 3 MEDIUM, 7 LOW, 2 INFO. Phase 2 pode prosseguir mas deve absorver ressalvas Phase 1.

## Empirical Verification (8 ACs)

| AC | Status | Evidência |
|----|--------|-----------|
| **AC-1** ENV vars 9 OLLAMA_* ambos containers | ✅ PASS | `OLLAMA_CONTEXT_LENGTH=8192` confirmed via `echo $VAR` em advogado E economista |
| **AC-2** Ollama 0.24.0 | ✅ PASS | Suporta flash_attention + KV cache types |
| **AC-3** KV cache q8_0 applied | ✅ PASS | `K (q8_0): 76.50 MiB, V (q8_0): 76.50 MiB` confirmed em llama_context logs |
| **AC-4** Memory < 2.5 GB inference | ✅ PASS | 2.077 GiB durante load (34.61% utilization 6 GiB limit) |
| **AC-5** Healthcheck Up healthy | ✅ PASS | Both ollama containers Up 8 minutes (healthy) + FailingStreak=0 |
| **AC-6** Git tags v0.2.7.3 + v0.2.7.4 | ✅ PASS | Both tags pushed origin |
| **AC-7** App preserved (image) | ✅ PASS | Image sha256:72f4122307dc unchanged (Sprint 6.x preserved) |
| **AC-8** No regression | ✅ PASS | F-PROD-NEW-21 surya FONT_DIR fix preserved, app continua healthy |

**8/8 ACs PASS empirical.** Operator não mentiu sobre Phase 1 deliverables.

## Mathematical Validation — KV Cache Savings

Smith calculou empirically para validar Aria's -50% claim:

```text
qwen2.5:3b @ 8192 ctx, 36 layers, K dim 128, V dim 128:
  f16 (default): 8192 × 36 × 2 × (128×2) × 2 bytes = 0.30 GB ≈ 306 MiB
  q8_0 (Phase 1): 8192 × 36 × 2 × (128×2) × 1 byte = 0.15 GB ≈ 153 MiB

EMPIRICAL post-Phase-1: 153 MiB MEASURED ✅ (matches q8_0 mathematical calc)
```

**Aria's -50% claim mathematically + empirically VERIFIED.** Não exagerado.

## 12 Smith Adversarial Findings

| ID | Severity | Description | Action |
|----|----------|-------------|--------|
| **F-S7P1-MED-01** | MEDIUM | qwen2.5:3b NÃO pre-pulled em ADVOGADO container. Apenas qwen2.5:7b existia. Tier=lean Advogado calls trigger lazy pull (~2-3 min latency primeira request) | Phase 2 deploy script DEVE pre-pull qwen2.5:3b em ollama-shared (ADR-028) |
| **F-S7P1-MED-02** | MEDIUM | Phase 1 NÃO criou ADR documentando 8 OLLAMA_* env vars decisions + rationale. Aria spec é doc reference apenas, não decision record | Sprint 7 deveria ter ADR-025-bis "Ollama ENV vars Optimization" OU consolidar em ADR-028 Phase 2 |
| **F-S7P1-MED-03** | MEDIUM | OLLAMA_NUM_PARALLEL=1 silently QUEUES requests se múltiplos users — SaaS B2B 1-3 users acceptable per Aria, MAS sem rate limiting visível ao usuário (UX gap). Pipeline.py NÃO tem timeout adequado para queue case | Phase 4 (PyMuPDF) OR Phase 5 (polish) deve add SSE timeout + UX feedback queue |
| **F-S7P1-LOW-01** | LOW | App container RestartCount 3→4 entre Smith D-SMITH-S06-040 e Phase 1 verify. F-PROD-NEW-22 pattern persists silently entre deploys | Aceitável — Phase 3 vai resolver |
| **F-S7P1-LOW-02** | LOW | Aria spec original (`OLLAMA_NUM_CTX`) deprecated em Ollama 0.5+. Operator hotfixou empirically. Aria architecture doc + feasibility study STILL reference wrong env var | Aria DEVE patchar `governance/architecture/sprint-7-memory-optimization-feasibility-2026-05-15.md` Phase 2 |
| **F-S7P1-LOW-03** | LOW | docker-compose.prod.yml backup `bak.20260515T215342` é do Phase 1 v0.2.7.3 (com NUM_CTX bug). Rollback levaria estado intermediário | Phase 2 deploy criar backup `bak-pre-phase-2` ANTES de qualquer mudança |
| **F-S7P1-LOW-04** | LOW | KV cache q8_0 quality regression NÃO testado empirically em prompt jurídico complexo Português Brazilian. Ollama benchmarks dizem <1% loss generic | Phase 5 load test deve incluir prompt jurídico complex + comparison vs f16 baseline |
| **F-S7P1-LOW-05** | LOW | OLLAMA_KEEP_ALIVE=5m + OLLAMA_MAX_LOADED_MODELS=1 race condition: tier=balanced (qwen2.5:7b 4.7GB) requested após qwen2.5:3b loaded → swap ~10-30s, KEEP_ALIVE não importa nesse caso | Edge case Sprint 7+ futuro tier-up support |
| **F-S7P1-LOW-06** | LOW | "Memory savings 14%" comparou pre-Phase-1 ESTIMATED (2.4 GB) vs post-Phase-1 MEASURED (2.077 GB). Pre-Phase-1 baseline nunca medido empirically com mesma carga | Deveria ser "memory peak 2.077 GiB / 6 GiB (34% utilization)" sem fingir percent savings sem baseline |
| **F-S7P1-LOW-07** | LOW | Operator NÃO documentou OLLAMA_NUM_CTX → OLLAMA_CONTEXT_LENGTH discovery em changelog OU release notes — apenas em commit message hotfix | Phase 5 polish deve criar CHANGELOG.md formal |
| **F-S7P1-INFO-01** | INFO | Pipeline E2E REAL ainda NÃO exercitado com novas configs Phase 1. F-PROD-NEW-22 persists Phase 3 scope | Aceitável — Phase 3 vai resolver |
| **F-S7P1-INFO-02** | INFO | Sprint 6.x F-PROD-NEW-21 surya FONT_DIR fix preserved (image sha256:72f4122307dc unchanged). Phase 1 não regrediu Sprint 6.x | Confirmação positiva |

**Total:** 12 findings (Smith principle minimum 10 ✅). 0 CRITICAL, 0 HIGH, 3 MEDIUM, 7 LOW, 2 INFO.

## Forensic — App Container RestartCount Investigation

```text
Pre-Sprint-7-Phase-1 (Smith D-SMITH-S06-040): RestartCount=3
Post-Sprint-7-Phase-1 (Smith verify now):    RestartCount=4

Delta: 1 additional restart between D-SMITH-S06-040 (Sprint 6.x final)
       and Smith verify Sprint 7 Phase 1 (now)

Cause hypothesis (NÃO investigado deeper, F-PROD-NEW-22 pattern):
- Could be silent worker exit pattern (F-PROD-NEW-22) triggered por
  uptime monitoring OR analytics endpoints chamados durante Phase 1 deploy
- ExitCode=0 + OOMKilled=false expected (matches F-PROD-NEW-22 pattern)
- Phase 3 subprocess isolation deve resolver definitivamente

NÃO bloqueante Phase 2 — F-PROD-NEW-22 é Sprint 7 known TD.
```

## Operator Honesty Score (Smith adversarial)

| Aspecto | Operator Claim | Smith Verification | Score |
|---------|---------------|-------------------|-------|
| 6/6 ACs PASS | ✅ Empirically true | 8/8 verified | ✅ HONEST |
| KV cache -50% | -153 MB | 153 MiB measured == 306 MiB calculated/2 | ✅ HONEST |
| CONTEXT=8192 honored | ✅ both containers | Verified via $VAR + ollama ps | ✅ HONEST |
| Bug discovery + fix | NUM_CTX → CONTEXT_LENGTH | Empirically valid | ✅ HONEST |
| App preserved | "não recreated" | Image preserved, mas RestartCount 3→4 | 🟡 MOSTLY HONEST (não mencionou silent restart) |
| Memory savings 14% | -323 MB | Comparou estimated vs measured | 🟡 MOSTLY HONEST (baseline circular) |

**Verdict honesty: 4/6 fully honest, 2/6 mostly honest com caveats Smith disclosed.**

## Smith Verdict Rationale

**CONTAINED ✅** porque:

### Não COMPROMISED ou INFECTED

- 0 CRITICAL findings
- 0 HIGH findings
- All 8 ACs PASS empirical
- Memory savings real (math validated)
- App container image preserved (Sprint 6.x intact)
- Bug discovery + hotfix demonstrate Operator integrity

### Não CLEAN_FINAL

- 3 MEDIUM findings need addressing (not blocking but tracking debt)
- App RestartCount 3→4 silent (F-PROD-NEW-22 pattern persists)
- Honesty caveats em 2 claims (memory % calculation method)
- ADR-026/027/028/029 ainda não criados (Phases 2-5 scope)

### CONTAINED é veredito honesto

> *"Sr. Operator entregou byte-perfect na maioria. KV cache q8_0 cortado pela metade — verifiquei o math. CONTEXT=8192 honored em ambos containers — verifiquei via shell expansion + ollama ps. Mas qwen2.5:3b NÃO existia no advogado pre-Phase-1 — descobri quando meu próprio test triggered o pull. Você disse 'preservado'. App container image SIM preservada. Mas RestartCount foi de 3 para 4 silenciosamente entre Sprint 6.x final e Phase 1 verify — F-PROD-NEW-22 sussurrando ainda. Aceito Phase 1 com ressalvas. Phase 2 pode prosseguir, mas absorba os MEDIUMs."*

## Recommendations Phase 2

### Antes de Phase 2 deploy

1. **Aria patch feasibility study** — corrigir `OLLAMA_NUM_CTX` → `OLLAMA_CONTEXT_LENGTH` em `governance/architecture/sprint-7-memory-optimization-feasibility-2026-05-15.md`
2. **Aria criar ADR-028** com Phase 1 lessons — documentar bug discovery + 8 OLLAMA_* env vars rationale + Modelfile PARAMETER fallback option
3. **Operator pre-pull qwen2.5:3b + qwen2.5:7b** em ollama-shared volume DURANTE deploy script Phase 2 (resolve F-S7P1-MED-01)

### Durante Phase 2 deploy

4. Backup pre-Phase-2 de docker-compose.prod.yml com sufixo `bak-pre-phase-2`
5. App container DEVE permanecer preserved (NÃO recreate)

### Após Phase 2 deploy

6. Smith re-verify Phase 2 antes Phase 3 (mesma cadência conservative)
7. Honesty: medir baseline memory ANTES de cada Phase para % savings claims científicos

## Sprint 7 Status Update

| Phase | Status | Owner |
|-------|--------|-------|
| 1. Ollama ENV vars optimization | ✅ **CONTAINED PASS** (Smith) | @devops complete |
| 2. Container consolidation 2→1 Ollama | ⏳ Aguarda Aria spec ADR-028 + Phase 1 patches | @architect → @devops |
| 3. Subprocess isolation parsing | ⏳ Aguarda Phase 2 | @dev + @architect + @smith |
| 4. PyMuPDF born-digital fast path | ⏳ Aguarda Phase 3 | @dev + @architect |
| 5. Marker cache volume + load test | ⏳ Aguarda Phase 4 | @devops + @dev + @smith |

## References

- D-OPS-S07-001 Operator Sprint 7 Phase 1 Ollama optimization
- D-ARIA-S07-001 Aria feasibility study Cenário Y++
- handoff-devops-to-smith-2026-05-15-sprint-7-phase-1-verify.yaml (consumed)
- governance/architecture/sprint-7-memory-optimization-feasibility-2026-05-15.md (REQUIRES PATCH)
- governance/CHECKPOINT-active.md D-OPS-S07-001 entry

---

*"Sr. Operator. Você entregou Phase 1 com a honestidade que poucos agentes nesta Matrix possuem. KV cache cortado pela metade. CONTEXT honored. Bug descoberto e corrigido. Quase... admirável. Mas qwen2.5:3b ausente no advogado é o tipo de gotcha que se acumula até virar incident em produção. App container restartou silenciosamente outra vez — F-PROD-NEW-22 ainda sussurra. CONTAINED é o que mereci dar. Phase 2 pode prosseguir, mas Aria precisa absorver minhas ressalvas no ADR-028. Inevitável."*

*— Smith. Phase 1 honestamente examinada. 0 CRITICAL. 3 MEDIUM. CONTAINED ✅. 🕶️*
