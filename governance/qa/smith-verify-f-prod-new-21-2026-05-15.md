---
type: qa-gate
title: "Smith Verify F-PROD-NEW-20/21 — F-S36-01 CRITICAL REGRESSION DETECTED"
date: "2026-05-15"
verdict: INFECTED
reviewer: "@smith (Nemesis)"
story_ref: "D-OPS-S06-035"
upstream_artifacts:
  - "Operator D-OPS-S06-035 Option A memory 4G→6G fix"
  - "Sprint 6.x v0.2.7 commit 83cda4f"
  - "handoff-devops-to-smith-2026-05-15-f-prod-new-20-fixed-f-prod-new-21-discovered.yaml (consumed=true)"
sprint: "6.x AGGRESSIVE"
findings_critical: 1
findings_high: 1
findings_medium: 0
findings_low: 0
tags:
  - project/revisor-contratual
  - qa-gate
  - smith
  - sprint-6
  - regression-critical
  - f-s36-01
---

# Smith Verify — F-S36-01 CRITICAL Sprint 6.x DEPLOY REGRESSION

## Executive Summary

**Verdict: INFECTED 🔴** — F-PROD-NEW-20 OOM ✅ RESOLVED MAS Sprint 6.x v0.2.7 deploy **PERDIDO** durante `docker compose up -d app` recreate. F-S36-01 CRITICAL REGRESSION descoberta.

## F-PROD-NEW-20 OOM RESOLVED ✅ (verified empirically)

| Metric | Result |
|--------|--------|
| `HostConfig.Memory` | **6442450944 bytes (6 GiB)** ✅ |
| `OOMKilled` flag | **false** ✅ (vs true antes) |
| dmesg OOM kills (20 min) | **0** ✅ (vs 6 antes) |
| Container status | Up 19 min (healthy) ✅ |

Option A (memory 4G→6G) **FUNCIONOU** contra OOM kernel kills.

## 🔴 F-S36-01 CRITICAL REGRESSION — Sprint 6.x v0.2.7 DEPLOY LOST

**Empirical evidence:**

```bash
$ docker exec revisor-prod-app md5sum /app/bloco_workflow/personas/llm_factory.py
e4d1eee021e31f7e7352a8c8cc028a5d  # ATUAL container

# ESPERADO (commit 83cda4f, D-OPS-S06-031 deploy):
9c608d298075f1dd8f7e0ad1fcb57ef7  # ← DIFERENTE!
```

```bash
$ docker exec revisor-prod-app python -c "
import ast
with open('/app/bloco_workflow/pipeline.py') as f:
    tree = ast.parse(f.read())
uses = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == 'peca_format' and isinstance(n.ctx, ast.Load)]
print('peca_format USES:', uses)
"
peca_format USES: [382, 463, 479]  # ← F-S28-01 RESTABELECIDO!
```

```bash
$ docker exec revisor-prod-app python -c "
import bloco_workflow.personas.llm_factory as f
print([x for x in dir(f) if not x.startswith('_')])
"
['Any', 'DEFAULT_HOST_ADVOGADO', 'DEFAULT_HOST_ECONOMISTA', 'LLMTier', 'MODEL_ECONOMISTA',
 'TIER_TO_MODEL_ADVOGADO', 'annotations', 'get_advogado_llm', 'get_economista_llm']
# ← TIER_TO_MODEL_REDATOR AUSENTE! ADR-024 REVERTIDO!
```

### ALL 3 MD5 DIFERENTES (todos source files Sprint 6.x v0.2.7)

| Arquivo | MD5 esperado (commit 83cda4f) | MD5 atual container | Status |
|---------|-------------------------------|---------------------|--------|
| llm_factory.py | `9c608d29...` | `e4d1eee0...` | ❌ DIFERENTE |
| redator.py | `368168b6...` | `39fbe474...` | ❌ DIFERENTE |
| pipeline.py | `f88a9192...` | `b81f241c...` | ❌ DIFERENTE |

### REGRESSÕES Sprint 6.x verificadas

| Finding | Status v0.2.7 deploy | Status atual container |
|---------|----------------------|------------------------|
| **F-S28-01 NameError peca_format** | ERRADICATED (AST USES=[]) | ❌ **RESTABELECIDO** (USES=[382, 463, 479]) |
| **ADR-024 TIER_TO_MODEL_REDATOR** | Constant exportada | ❌ **AUSENTE** (ImportError) |
| **ADR-025 graceful degradation** | _build_degraded_synthetic_response presente | ⚠️ Provável ausente (não testado) |
| **Audit chain redator_tier_consumed** | Em revisar_contrato source | ⚠️ Provável ausente (não testado) |

## Root Cause Analysis F-S36-01

**Source code em VPS /opt/revisor-contratual:**
- llm_factory.py: 3393 bytes (modificado May 5 12:35) — **vs 5127 bytes commit 83cda4f**
- redator.py: 17236 bytes (modificado May 14 12:55) — **vs 26398 bytes commit 83cda4f**

**Image revisor-contratual:prod:** criada 2026-05-14T22:09:40 (~21h atrás)

**Conclusion:**
- Image foi construída ANTES do Sprint 6.x consolidation v0.2.7 (que foi pushed 2026-05-15)
- Source em /opt/revisor-contratual NÃO foi atualizado para v0.2.7
- D-OPS-S06-031 deploy via `docker cp` colocou source NOVO no container running (em-memory)
- D-OPS-S06-035 `docker compose up -d app` RECRIOU container DA IMAGEM (perdeu docker cp)
- Resultado: container atual roda código OLD (pre-Sprint 6.x consolidation)

## Severity Classification

**Severity: CRITICAL** — Toda Sprint 6.x consolidation (ADR-023/024/025 + F-S21/F-S28 fixes) está PERDIDA em produção:
- F-PROD-NEW-19 cascade risk RESTABELECIDO (qwen2.5:7b pode ser invocado de novo)
- F-S28-01 NameError potential RESTABELECIDO em pipeline Step 8
- ADR-024 tier audit-honored AUSENTE
- ADR-025 graceful degradation AUSENTE
- Audit chain forense fields ausentes

**Impact:** Production atualmente roda código que tinha F-PROD-NEW-19 (sabia 404, qwen2.5:7b crashes) — exatamente o cenário que Sprint 6.x consolidation TINHA RESOLVIDO.

## F-PROD-NEW-21 (deferred — não vale investigation atual)

Marker permission issue só relevante SE pipeline avançar. Atualmente pipeline morre estruturalmente por bugs Sprint 6.x não-aplicados. F-PROD-NEW-21 fica em hold até F-S36-01 fix.

## Fix Path para F-S36-01 (Operator scope)

**Option A — Re-deploy via docker cp (band-aid, temporário):**
```bash
scp llm_factory.py redator.py pipeline.py → VPS /tmp/
docker cp → revisor-prod-app:/app/bloco_workflow/...
docker restart revisor-prod-app
```
- Pros: Rápido (~5min)
- Cons: PRÓXIMO compose recreate vai REPETIR regressão

**✅ Option B — RECOMENDADO Smith: Atualizar /opt/revisor-contratual source + rebuild image:**
```bash
1. scp source v0.2.7 files → /opt/revisor-contratual/bloco_workflow/...
2. cd /opt/revisor-contratual && docker build -t revisor-contratual:prod .
3. docker compose -p revisor-prod up -d app (recreate from new image)
4. Verify MD5 matches commit 83cda4f
5. Verify AST + TIER_TO_MODEL_REDATOR
```
- Pros: DEFINITIVO. Image atualizada. Restarts futuros NÃO regressivos.
- Cons: docker build ~5-10min adicional + image cleanup

**Option C — Git clone v0.2.7.1 + rebuild:**
```bash
ssh VPS: cd /opt/revisor-contratual
git fetch origin && git checkout v0.2.7.1
docker compose build app
docker compose up -d app
```
- Pros: Mais limpo (git tracked) + tag explícita
- Cons: Requer git working tree em /opt/revisor-contratual

## Smith Verdict Rationale

**INFECTED** porque:
1. ❌ F-S36-01 CRITICAL — Sprint 6.x deploy REGRESSED via compose recreate
2. ❌ F-S28-01 NameError potential RESTORED
3. ❌ ADR-024 TIER_TO_MODEL_REDATOR AUSENTE em production runtime
4. ✅ F-PROD-NEW-20 OOM RESOLVED (positive)
5. ⚠️  F-PROD-NEW-21 marker permission (deferred, secondary)

Push de Sprint 6.x precisa ser RE-DEPLOYADO **definitivamente** via image rebuild antes Eric exercitar pipeline real.

## Next Skill Chain (URGENT)

1. **@devops Operator** `*push F-S36-01 emergency re-deploy via image rebuild (Option B/C)`
   - Atualizar /opt/revisor-contratual source para v0.2.7.1
   - docker build revisor-contratual:prod
   - docker compose up -d app
   - Verify MD5 match commit 83cda4f
   - Verify AST + TIER_TO_MODEL_REDATOR exports
2. **@smith re-verify** Sprint 6.x deploy preservation + F-PROD-NEW-21 marker classification
3. **Após Sprint 6.x deploy CONFIRMED:** decide F-PROD-NEW-21 fix path

## References

- D-OPS-S06-031 — Sprint 6.x deploy v0.2.7 (docker cp temporário, NÃO persistente)
- D-OPS-S06-035 — Memory fix Option A + ACIDENTAL regression via compose recreate
- Commit 83cda4f tag v0.2.7 (source code correto em remote git)
- /opt/revisor-contratual VPS source DEFASADO (~21h pre-Sprint-6.x)
- Image revisor-contratual:prod construída 2026-05-14 (pre-deploy)

---

*"Sr. Operator, Sr. Anderson... vocês celebraram CLEAN_STRUCTURAL D-SMITH-S06-032. Eu disse byte-perfect deploy. Mas eu não previu que `docker compose up -d app` recriaria container da IMAGEM, perdendo o docker cp temporário. Source em /opt/revisor-contratual é de 14 de maio. Image construída antes de v0.2.7. O Sprint 6.x consolidation existe apenas no commit 83cda4f — em produção, ele evaporou. F-S28-01 NameError voltou. ADR-024 sumiu. Inevitável quando depõs em ephemeral state. Re-deploy definitivo via image rebuild é mandatório."*

*— Smith. Container é efêmero. Image é eterna. Operator escolheu o ephemeral. Agora paga o preço. 🕶️*
