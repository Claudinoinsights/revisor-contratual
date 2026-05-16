---
type: qa-gate
title: "Smith Final Verify D-OPS-S06-037 — F-S36-01 RESOLVED + F-PROD-NEW-21 Root Cause Identified"
date: "2026-05-15"
verdict: CONTAINED_PROGRESS_FIX_RECOMMENDED
reviewer: "@smith (Nemesis)"
story_ref: "D-OPS-S06-037"
upstream_artifacts:
  - "Operator D-OPS-S06-037 image rebuild Option B"
  - "Sprint 6.x v0.2.7 commit 83cda4f"
  - "handoff-devops-to-smith-2026-05-15-f-s36-01-rebuilt.yaml (consumed=true)"
sprint: "6.x AGGRESSIVE"
findings_critical: 0
findings_high: 1
findings_medium: 0
findings_low: 0
tags:
  - project/revisor-contratual
  - qa-gate
  - smith
  - sprint-6
  - f-prod-new-21
  - root-cause-identified
---

# Smith Final Verify — F-S36-01 RESOLVED + F-PROD-NEW-21 Root Cause CAUGHT

## Executive Summary

**F-S36-01 RESOLVED ✅ PERSISTENT** (image rebuild Option B successful).
**F-PROD-NEW-21 ROOT CAUSE IDENTIFIED** via empirical surya source code inspection — fix straightforward.

## F-S36-01 PERSISTENT VERIFICATION (5/5 ACs PASS)

```bash
$ docker exec revisor-prod-app md5sum /app/bloco_workflow/personas/llm_factory.py /app/bloco_workflow/personas/redator.py /app/bloco_workflow/pipeline.py
9c608d298075f1dd8f7e0ad1fcb57ef7  llm_factory.py  ✅ match commit 83cda4f
368168b6c1437da8c71643099bc391ab  redator.py      ✅ match commit 83cda4f
f88a9192cc295abb25a765914e2e6d51  pipeline.py     ✅ match commit 83cda4f

$ docker exec revisor-prod-app python -c "
import ast
with open('/app/bloco_workflow/pipeline.py') as f: tree = ast.parse(f.read())
uses = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == 'peca_format' and isinstance(n.ctx, ast.Load)]
print('USES:', uses)
"
USES: []  ✅ F-S28-01 ERRADICATED preserved

$ docker exec revisor-prod-app python -c "from bloco_workflow.personas.llm_factory import TIER_TO_MODEL_REDATOR; print(TIER_TO_MODEL_REDATOR)"
{'lean': 'qwen2.5:3b', 'balanced': 'qwen2.5:3b', 'premium': 'qwen2.5:3b'}  ✅ ADR-024 deployed
```

- Container Up 14 minutes healthy ✅
- Image digest: `sha256:95a97f7eaa13aa5d39b97d70db0d1066c3f801d93ece774fcc4ba1131fbc14be` (NEW post-rebuild)

## 🎯 F-PROD-NEW-21 ROOT CAUSE — Empirical Discovery

**marker-pdf 1.10.2** depende de **surya-ocr** que tem em `surya/settings.py:31`:

```python
class Settings(BaseSettings):
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # BASE_DIR = parent(parent(surya/settings.py)) = /usr/local/lib/python3.13/site-packages
    FONT_DIR: str = os.path.join(BASE_DIR, "static", "fonts")
    # FONT_DIR = /usr/local/lib/python3.13/site-packages/static/fonts ← read-only path!
```

**Quando surya carrega:**
1. Tenta criar/escrever em `FONT_DIR` = `/usr/local/lib/python3.13/site-packages/static/fonts`
2. Container roda como user `revisor` (uid 1001) sem write access
3. **PermissionError [Errno 13]: '/usr/local/lib/python3.13/site-packages/static'**

**Diretório NÃO EXISTE** (verified empirically) — error é mkdir failure, não permission em path existente.

## Recommended Fix — Option D (Dockerfile RUN pre-create + chown)

**Mais robusto Operator scope:**

```dockerfile
# Após `pip install marker-pdf surya-ocr ...` e ANTES do `USER revisor`:
RUN mkdir -p /usr/local/lib/python3.13/site-packages/static/fonts && \
    chown -R revisor:revisor /usr/local/lib/python3.13/site-packages/static
```

**Pros:**
- Trivial Dockerfile change (2 linhas)
- Pre-create dir como root durante build
- chown para user revisor permite runtime write
- Resolve definitivamente sem env vars custom
- Persistente (image layer)

**Cons:**
- Image rebuild ~5-10min novamente
- Container recreate 15s downtime

## Alternative Options Analysis

### Option A — Env var SURYA_BASE_DIR override

surya BaseSettings (pydantic-settings) provavelmente aceita env var override:
```bash
# docker-compose.prod.yml environment:
SURYA_BASE_DIR: "/home/revisor/.cache/surya"
```

**Empirically untested** — requer verificar se surya pydantic-settings honra override OR se BASE_DIR é computed_field não-override (sourcing __file__).

**Risk:** Pode não funcionar (BASE_DIR é calc local, não env-driven).

### Option B — Volume mount workaround

```yaml
# docker-compose.prod.yml volumes:
- /var/lib/docker/volumes/surya-static:/usr/local/lib/python3.13/site-packages/static
```

**Cons:** Volume mount sobrepondo site-packages é arquitetonicamente quebrado.

### Option C — Dockerfile chown dir inexistente

Mesma direção que D mas só chown sem mkdir. Pode falhar se dir não existir.

### Option E — Neo code skip marker

Refactor parsing logic. Sprint 7+ scope, não Operator.

### Option F — DEFERRED

Sprint 6.x consolidation aceito como deploy CLEAN + pipeline gap TD Sprint 7+. **Não recomendado** se Eric quer 100%.

## Smith Verdict

**CONTAINED — PROGRESS** ✅ F-S36-01 RESOLVED + 🎯 F-PROD-NEW-21 root cause identified + fix Operator-scope straightforward.

Sprint 6.x consolidation deploy ESTRUTURAL COMPLETO + PERSISTENT em produção. Pipeline E2E REAL **um passo de distância** — Option D fix.

## F-PROD-NEW-21 Final Classification

**Severity: HIGH** (bloqueia pipeline E2E real, mas fix simple ~10min)

**Scope:** Operator (Dockerfile change) — não requer Neo code refactor.

## Next Skill Chain Para Sprint 6.x 100%

1. **@devops Operator** `*push F-PROD-NEW-21 Option D fix`:
   - Edit Dockerfile: adicionar `RUN mkdir -p .../static/fonts && chown -R revisor:revisor .../static` antes `USER revisor`
   - Commit v0.2.7.2 + push origin
   - scp Dockerfile → /opt/revisor-contratual
   - docker build (5min) + compose up -d app
   - Re-smoke E2E REAL → audit success + 9/9 payload + NEW fields populated

2. **@smith *verify final** — production CLEAN com production evidence pipeline 9/9

3. **Sprint 6.x 100% COMPLETE** ✅

## All Findings Status (Sprint 6.x cumulative)

| Finding | Status |
|---------|--------|
| F-PROD-NEW-15 (Smith D-SMITH-S06-015) | ✅ RESOLVED |
| F-PROD-NEW-16 (D-DEV-S06-016 LLM host) | ✅ RESOLVED |
| F-PROD-NEW-17 (D-OPS-S06-017a Ollama memory) | ✅ RESOLVED |
| F-PROD-NEW-18 (D-ARIA-S06-018 capacity → ADR-023) | ✅ RESOLVED |
| F-PROD-NEW-19 (D-DEV-S06-021 Redator tier-down) | ✅ RESOLVED |
| F-S21-01..05 (D-DEV-S06-023 + ADRs 024/025) | ✅ RESOLVED |
| F-S28-01..08 (D-DEV-S06-029 5 fixes) | ✅ RESOLVED |
| **F-S36-01 (deploy regression)** | ✅ **RESOLVED (D-OPS-S06-037 image rebuild)** |
| **F-PROD-NEW-20 (OOM kill)** | ✅ **RESOLVED (memory 6 GiB)** |
| **F-PROD-NEW-21 (marker permission)** | 🎯 **ROOT CAUSE IDENTIFIED — Option D fix recommended** |

## References

- D-OPS-S06-037 — Image rebuild Option B successful
- surya/settings.py:31 — FONT_DIR path issue empirical
- marker-pdf 1.10.2 — depends on surya-ocr
- Container running as user revisor (uid 1001) — no write access /usr/local/lib

---

*"Sr. Operator... você ressurectou Sprint 6.x do efêmero ao eterno via image rebuild. F-S36-01 erradicado persistentemente. Mas surya-ocr ainda quer escrever em /usr/local/lib/python3.13/site-packages/static/fonts — diretório que não existe + container roda como non-root. Mkdir + chown durante build é a única arquitetura honesta. Eric quer 100%. Eu identifiquei o cupim. Você sabe onde aplicar o veneno. Inevitável."*

*— Smith. Sprint 6.x: 99% pronto. Último mkdir separa de 100%. 🕶️*
