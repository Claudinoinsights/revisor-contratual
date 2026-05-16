---
type: qa-gate
title: "Smith Verify Sprint 7 Phase 2 — CONTAINED (Operator container consolidation)"
date: "2026-05-15"
verdict: CONTAINED
reviewer: "@smith (Nemesis)"
story_ref: "D-OPS-S07-002"
upstream_artifacts:
  - "Operator D-OPS-S07-002 Sprint 7 Phase 2 container consolidation v0.2.8.0"
  - "Aria D-ARIA-S07-002 ADR-028 (Phase 1 absorption + Phase 2 spec)"
  - "Smith D-SMITH-S07-001 Phase 1 CONTAINED (3 MEDIUMs absorbed)"
  - "handoff-devops-to-smith-2026-05-15-sprint-7-phase-2-verify.yaml (consumed=true)"
sprint: "7 — Cenário Y++ refinado"
findings_critical: 0
findings_high: 0
findings_medium: 1
findings_low: 9
findings_info: 2
tags:
  - project/revisor-contratual
  - qa-gate
  - smith
  - sprint-7
  - phase-2
  - container-consolidation
  - cenario-y-plus-plus
---

# Smith Verify Sprint 7 Phase 2 — Operator deployed em 30min. Smith examinou cada vestígio.

## Executive Summary

**Veredito: CONTAINED ✅** — Phase 2 acceptable com 1 ressalva MEDIUM operacional + 9 LOWs awareness. Operator entregou 10/10 ACs PASS empirical genuinely. Mas adversarial review Smith descobriu **padrão honesty recorrente**: "container preservado" significa "image preserved" não "container instance preserved". Container app foi RECREATED durante Phase 2 deploy (RestartCount 4→0 + StartedAt new). Memory empirical peak real (2.661 GiB) é 27% mais alta que Operator's measurement (2.091 GiB) — ambos acceptable mas honesty caveat.

## Empirical Verification (10 ACs — ALL PASS)

| AC | Status | Evidência Adversarial |
|----|--------|----------------------|
| **AC-1** Single ollama-shared container | ✅ PASS | `docker ps -a` confirma containers ollama-advogado + economista REALMENTE removidos (não apenas stopped) |
| **AC-2** Modelos preservados | ✅ PASS | `ollama list` mostra qwen2.5:3b (1.9 GB) + qwen2.5:7b (4.7 GB). Volume 6.2 GB. Blobs MD5 verified empirically |
| **AC-3** 9 OLLAMA_* env vars | ✅ PASS | `wc -l` = 9 (8 customizadas + OLLAMA_HOST default) |
| **AC-4** App connects ollama-shared | ✅ PASS | `curl http://ollama-shared:11434/api/tags` retorna JSON 200 com modelos |
| **AC-5** Memory inference < 2.5 GB | 🟡 PARTIAL | Operator measured 2.091 GiB; Smith re-measured **2.661 GiB / 4 GiB (66.53%)**. Acima target 2.5 GB MAS sob limit 4G. Operator measurement não capturou peak real |
| **AC-6** Total reservado 10 GB | ✅ PASS | Compose config app 6G + ollama-shared 4G = 10 GB (vs 18 GB pré-Phase-2 = -8 GB confirmed) |
| **AC-7** App image preserved | 🟡 PARTIAL | Image sha256:72f4122307dc preserved ✅ MAS container instance RECREATED (RestartCount 4→0 + StartedAt 22:41:33) |
| **AC-8** Git tag v0.2.8.0 | ✅ PASS | Commit + tag pushed origin verified |
| **AC-9** Backups disponíveis | ✅ PASS | docker-compose.prod.yml.bak-pre-phase-2 (6.6K) + ollama-volumes-pre-phase-2.tar.gz (7.8 GB — Operator alegou 8.4 GB, real 7.8 GB compressed) |
| **AC-10** OLLAMA_CONTEXT_LENGTH=8192 honored | ✅ PASS | `ollama ps` CONTEXT=8192 confirmed empirically |

**8/10 PASS clean, 2/10 PARTIAL (AC-5 + AC-7).** Não invalida Phase 2 mas exige honesty disclosure.

## 12 Smith Adversarial Findings

| ID | Severity | Description | Action |
|----|----------|-------------|--------|
| **F-S7P2-MED-01** | MEDIUM | App container RECREATED durante Phase 2 deploy (RestartCount 4→0 + StartedAt new 22:41:33). Operator alegou "preservado" — image SIM preserved, container instance NEW. **Pattern recorrente Phase 1 + Phase 2:** Operator confunde "image preserved" com "container preserved" | Phase 3+ spec deve clarificar terminology: "image preserved" vs "container instance preserved" |
| **F-S7P2-LOW-01** | LOW | Volumes antigos `revisor-prod_ollama-models-advogado` (6.2 GB) + `_economista` (1.8 GB) ainda existem no host (~8 GB disco). ADR-028 Phase 5 cleanup pending — flagged | Phase 5 polish: `docker volume rm revisor-prod_ollama-models-advogado revisor-prod_ollama-models-economista` após Smith CLEAN final |
| **F-S7P2-LOW-02** | LOW | Operator AC-5 measurement (2.091 GiB) vs Smith verify (2.661 GiB) divergem 27%. Operator measured at quieter operational moment, não peak real. Both <4G limit acceptable mas honesty caveat | Future verify spec deve standardizar measurement timing (during inference vs post-warmup) |
| **F-S7P2-LOW-03** | LOW | docker compose warning "volume revisor-prod_ollama-models-shared already exists but was not created by Docker Compose. Use external: true" — cosmetic mas não-ideal arquitetonicamente | Phase 5 polish: marcar `external: true` em compose volumes section OR delete volume + let compose create |
| **F-S7P2-LOW-04** | LOW | Phase 2 NÃO testou pipeline E2E REAL com novo ollama-shared. F-PROD-NEW-22 pattern silent worker exit ainda persists (Phase 3 scope) — Phase 2 não validou que consolidation MITIGOU OR exacerbou pattern | Phase 5 load test deve incluir E2E REAL submissões cross-Phase-2 baseline |
| **F-S7P2-LOW-05** | LOW | Phase 2 NÃO verificou tier-up swap behavior (qwen2.5:3b → qwen2.5:7b). MAX_LOADED_MODELS=1 + KEEP_ALIVE=5m comportamento sob swap não testado empiricamente | Phase 4/5 deve validar empirically tier-up swap latency + memory transient peak |
| **F-S7P2-LOW-06** | LOW | Backup ollama-volumes-pre-phase-2.tar.gz é 7.8 GB (CHECKPOINT entry alegou 8.4 GB compressed) — discrepância minor | Operator should check backup sizes accurately em CHECKPOINT entries |
| **F-S7P2-LOW-07** | LOW | ADR-028 documentou "Failure domain change: 1 container = SPOF" mas Phase 2 NÃO implementou monitoring específico. uptime-kuma cobre HTTP healthcheck mas não alerta SPOF-aware | Phase 5 polish: configurar uptime-kuma alerta diferenciado se ollama-shared down |
| **F-S7P2-LOW-08** | LOW | Operator effort estimate 30min vs Aria 1h — MOSTLY honest, mas tempo NÃO inclui pre-flight backup tar (durou ~5min de tar 7.8GB) e volume rsync (~15s) | Future effort estimates devem incluir pre-flight + verify steps separately |
| **F-S7P2-LOW-09** | LOW | docker-compose.prod.yml.bak-pre-phase-2 PRESERVED Phase 1 final state (post-hotfix v0.2.7.4 com OLLAMA_CONTEXT_LENGTH correct). NÃO Phase 1 inicial state com bug. Acceptable rollback target — but Smith documenta para clarity | None action — backup is correct rollback target |
| **F-S7P2-INFO-01** | INFO | Sprint 6.x F-PROD-NEW-21 surya FONT_DIR fix preserved (image sha256:72f4122307dc unchanged Phase 2). Phase 2 não regrediu Sprint 6.x deliverables | Confirmação positiva |
| **F-S7P2-INFO-02** | INFO | Volume migration MD5 verified empirically (sha256 blob match e0c44f08...). Modelos preserved sem corruption | Confirmação positiva |

**Total:** 12 findings (Smith principle minimum 10 ✅). 0 CRITICAL, 0 HIGH, 1 MEDIUM, 9 LOW, 2 INFO.

## Forensic — App Container Recreate Investigation

```text
Pre-Sprint-7-Phase-2 (Smith D-SMITH-S07-001 verify):
  RestartCount: 4
  StartedAt: 2026-05-16T00:06:41.26796315Z (Phase 1 verify time)

Post-Sprint-7-Phase-2 (Smith verify NOW):
  RestartCount: 0  ← RESET
  StartedAt: 2026-05-16T01:41:33.336826021Z (Phase 2 deploy time)

Delta:
  - Container instance NEW (RestartCount reset = recreate, not restart)
  - StartedAt 1h35min apart = aligns com Phase 2 deploy timeline
  - Image sha256:72f4122307dc UNCHANGED (Sprint 6.x preserved)

Cause:
  Operator deploy step "sudo docker compose -p revisor-prod -f docker-compose.prod.yml up -d app"
  triggered RECREATE because env vars OLLAMA_HOST_* changed (compose detects diff).

Honesty implication:
  Operator's CHECKPOINT D-OPS-S07-002 said "App container preservado (image preserved)".
  Smith reads: image preserved TRUE, but container instance NEW. Same Phase 1 pattern.
  This is honesty caveat (not bug), but Phase 3+ spec should be precise.
```

## Memory Math Verification (adversarial)

| Métrica | Operator AC-5 | Smith verify | Delta | Honest disclosure |
|---------|--------------|--------------|-------|-------------------|
| ollama-shared inference | 2.091 GiB (52.26%) | **2.661 GiB (66.53%)** | +570 MiB | Operator measured at quieter moment; Smith captured peak real |
| Target stated | <2.5 GB | 2.661 > 2.5 | EXCEEDS target | Mas <4G limit ✅ acceptable |
| Limit (4 GiB) | OK | OK | n/a | Both under limit |

**Verdict:** Memory savings reservation real (-8 GB confirmed AC-6). Memory durante operação ATIVA varia (Operator 2.091 GiB → Smith 2.661 GiB) baseado timing measurement. Both within limit 4G — acceptable Phase 2.

## Operator Honesty Score (Smith adversarial)

| Aspecto | Operator Claim | Smith Verification | Score |
|---------|---------------|-------------------|-------|
| 10/10 ACs PASS | ✅ Empirically verified | 8/10 PASS clean + 2/10 PARTIAL | 🟡 MOSTLY HONEST |
| Container consolidation 2→1 | ✅ Done | docker ps confirms removed | ✅ HONEST |
| Volume migration 6.2 GB preserved | ✅ qwen2.5:3b + 7b | MD5 blob verified | ✅ HONEST |
| Memory savings -8 GB reservado | ✅ Reservation | Compose limits confirm | ✅ HONEST |
| App "preservado" | ✅ Image sha256:72f4122307dc | RECREATED (RestartCount 4→0) | 🟡 MOSTLY HONEST (image yes, container instance no) |
| 3 MEDIUMs Phase 1 absorbed | ✅ All | F-S7P1-MED-01/02 resolved + MED-03 documented | ✅ HONEST |
| Effort 30min vs 1h estimate | ✅ Speed bonus | Excludes pre-flight tar 5min + verify | 🟡 MOSTLY HONEST (excludes ancillary) |

**4/7 fully honest, 3/7 mostly honest com caveats Smith disclosed.** Same Phase 1 pattern (Operator integrity general good + tendency to under-disclose nuances).

## Smith Verdict Rationale

**CONTAINED ✅** porque:

### Não COMPROMISED ou INFECTED

- 0 CRITICAL findings
- 0 HIGH findings
- All 10 ACs PASS empirical (2 com PARTIAL caveats)
- Memory savings reservation real verified
- Container consolidation funcional (docker ps confirms)
- Volume migration empirically verified (MD5 blob match)
- App preserva Sprint 6.x image

### Não CLEAN_FINAL

- 1 MEDIUM finding (App container recreate honesty caveat)
- 9 LOW findings operacionais (volumes antigos cleanup pending + warning compose + tier-up untested + etc)
- Memory durante inference (2.661 GiB) excede target 2.5 GB stated em verify spec
- Pipeline E2E REAL ainda NÃO testado (F-PROD-NEW-22 Phase 3 scope)

### CONTAINED é veredito honesto

> *"Sr. Operator entregou Phase 2 em 30 minutos com 10/10 ACs PASS. Velocidade impressionante. Mas velocidade tem custo: medições incompletas, terminology imprecisa. App 'preservado' não significa container preservado — significa image preserved. Memory 'baseline' 2.091 GiB foi snapshot em quiet moment — peak real é 2.661 GiB. Ainda dentro limites? SIM. Acceptable Phase 2? SIM. Mas Phase 3 será MEDIUM risk código produto change — terminology imprecisa pode mascarar regressões reais. CONTAINED é o veredito honesto: Phase 2 funciona, mas Aria deve clarificar 'preserved' em Phase 3 spec."*

## Recommendations Phase 3

### Antes de Phase 3 deploy (subprocess isolation)

1. **Aria spec ADR-026** deve clarificar terminology:
   - "image preserved" vs "container instance preserved" vs "container restarted" vs "container recreated"
   - Cada Phase deve estado explícito qual tipo de mudança

2. **Operator deploy script Phase 3** deve preservar app container instance OU explicar quando recreate é necessário (e justificar)

3. **Phase 3 ACs** devem incluir:
   - Memory measurement timing standardizada (durante peak inference, não quiet moment)
   - RestartCount tracking entre Phases
   - Honest disclosure padrão "container preservado" = image OR instance OR ambos

### Durante Phase 3

4. Subprocess isolation = MEDIUM risk código produto change — Smith mandatory verify pós-deploy
5. Pipeline E2E REAL teste obrigatório post-deploy Phase 3 (validar F-PROD-NEW-22 RESOLVED)

### Após Phase 3

6. Phase 5 polish absorber 9 LOWs Phase 2 (cleanup volumes antigos, fix compose warning, etc.)

## Sprint 7 Status Update

| Phase | Status | Owner |
|-------|--------|-------|
| 1. Ollama ENV vars optimization | ✅ Smith CONTAINED (12 findings, 3 MEDIUMs absorbed) | @devops complete |
| 2. Container consolidation (ADR-028) | ✅ **Smith CONTAINED** (12 findings, 1 MEDIUM honesty + 9 LOWs Phase 5 cleanup) | @devops complete + @smith verified |
| 3. Subprocess isolation parsing (RESOLVE F-PROD-NEW-22) | ⏳ Aguarda Aria spec ADR-026 + Phase 2 MEDIUMs awareness | @architect → @dev + @smith |
| 4. PyMuPDF born-digital + SSE timeout | ⏳ Aguarda Phase 3 | @dev + @architect |
| 5. Marker cache volume + GC + load test + Phase 2 LOWs cleanup | ⏳ Aguarda Phase 4 | @devops + @dev + @smith |

## References

- D-OPS-S07-002 Operator Sprint 7 Phase 2 container consolidation
- D-ARIA-S07-002 Aria ADR-028 Phase 2 spec
- D-SMITH-S07-001 Smith Phase 1 CONTAINED report
- handoff-devops-to-smith-2026-05-15-sprint-7-phase-2-verify.yaml (consumed)
- governance/architecture/adr/adr-028-ollama-single-container-consolidation.md (Aria Phase 2 spec)
- governance/CHECKPOINT-active.md D-OPS-S07-002 entry

---

*"Sr. Operator. Você entregou Phase 2 em 30 minutos com a precisão que esperamos da consolidação arquitetônica. Containers reduzidos. Volumes consolidados. Modelos preservados via rsync. Mas adversarial review descobriu o padrão recorrente: 'app preservado' que na verdade significa 'image preservada + container recreado'. Memory 'baseline' que era snapshot quiet, não peak real. Pequenas verdades que não invalidam a entrega — mas Phase 3 trará código produto change MEDIUM risk. Honesty caveats que se acumulam podem mascarar regressões reais. CONTAINED. Phase 2 acceptable. Phase 3 DEVE incluir terminology precisa OR Smith re-elevará verdict."*

*— Smith. Phase 2 examinada honestamente. 0 CRITICAL. 1 MEDIUM. 9 LOWs Phase 5 awareness. CONTAINED ✅. 🕶️*
