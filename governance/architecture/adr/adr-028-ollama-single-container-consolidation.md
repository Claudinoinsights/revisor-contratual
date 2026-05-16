---
type: adr
id: ADR-028
title: "Ollama Single-Container Consolidation — 2 containers (advogado+economista) → 1 ollama-shared (Cenário Y++ Phase 2)"
status: accepted
date: "2026-05-15"
domain: infra
adr_level: spec
spec_coverage:
  - "8 OLLAMA_* env vars (absorvendo Phase 1 D-OPS-S07-001 decisions)"
  - "Bug discovery OLLAMA_NUM_CTX deprecated → OLLAMA_CONTEXT_LENGTH (Ollama 0.5+)"
  - "Volume migration script (advogado+economista → shared)"
  - "Pre-pull modelos durante deploy (resolve F-S7P1-MED-01)"
  - "Modelfile PARAMETER num_ctx fallback option (documented)"
  - "Failure domain analysis (1 container = SPOF tradeoff)"
decision_makers:
  - "@architect (Aria)"
  - "@smith (Smith — adversarial review CONTAINED Phase 1 + 3 MEDIUMs absorbed)"
  - "Eric (owner — directive 'Cenário Y++ refinado' AskUserQuestion 2026-05-15)"
supersedes: null
superseded_by: null
related_adrs:
  - "ADR-023 Sequential LLM Inference (F-PROD-NEW-18 capacity)"
  - "ADR-024 Redator Tier Strategy (tier=lean usa qwen2.5:3b para 3 personas)"
  - "ADR-025 Redator Cascade Fallback Strategy (graceful degradation)"
related_findings:
  - "Smith F-S7P1-MED-01 (qwen2.5:3b NOT pre-pulled advogado)"
  - "Smith F-S7P1-MED-02 (Phase 1 sem ADR documentando decisions)"
  - "Smith F-S7P1-MED-03 (NUM_PARALLEL=1 queue UX gap — follow-up Phase 4/5)"
  - "Smith F-S7P1-LOW-04 (KV cache q8_0 quality untested em prompt jurídico — Phase 5)"
  - "Operator D-OPS-S07-001 Phase 1 deployment + bug discovery hotfix v0.2.7.4"
related_documents:
  - "governance/architecture/sprint-7-memory-optimization-feasibility-2026-05-15.md (Aria study Cenário Y++)"
  - "governance/qa/smith-verify-sprint-7-phase-1-2026-05-15.md (Smith CONTAINED 12 findings)"
tags:
  - project/revisor-contratual
  - adr
  - sprint-7
  - phase-2
  - ollama-consolidation
  - infra-optimization
  - cenario-y-plus-plus
---

# ADR-028 — Ollama Single-Container Consolidation (Sprint 7 Phase 2)

## Context

### Estado atual (pré-Phase-2, pós-Phase-1)

Sprint 6.x deixou produção com 2 containers Ollama isolados:

```text
revisor-prod-ollama-advogado:    6 GiB limit, qwen2.5:7b (4.7GB) + qwen2.5:3b (1.9GB)
revisor-prod-ollama-economista:  6 GiB limit, qwen2.5:3b (1.9GB)
revisor-prod-app:                6 GiB limit, marker library 3.3GB cache + pipeline
```

**Total reservado:** 18 GiB em VPS Hetzner 7.9 GiB físico → **2.3x overcommit** absurdo.

**Tier=lean reality (ADR-024 + Sprint 6.x consolidation):**

```python
# llm_factory.py current state
TIER_TO_MODEL_ADVOGADO = {'lean': 'qwen2.5:3b', 'balanced': 'qwen2.5:7b', 'premium': 'sabia-7b-instruct'}
MODEL_ECONOMISTA = 'qwen2.5:3b'
TIER_TO_MODEL_REDATOR = {'lean': 'qwen2.5:3b', 'balanced': 'qwen2.5:3b', 'premium': 'qwen2.5:3b'}
```

**Insight crítico:** tier=lean (default MVP) usa apenas **qwen2.5:3b** para 3 personas (Advogado + Economista + Redator). 2 containers Ollama mantêm **mesmo modelo duplicado** em volumes separados.

### Phase 1 entregue (D-OPS-S07-001)

8 OLLAMA_* env vars deployadas em ambos containers separados via docker-compose.prod.yml. Smith CONTAINED verify ✅ (8/8 ACs PASS, KV cache q8_0 -50% mathematically validated).

**3 MEDIUMs identificados por Smith Phase 1:**

- F-S7P1-MED-01: qwen2.5:3b NÃO pre-pulled em advogado (Smith test triggered manualmente)
- F-S7P1-MED-02: Phase 1 sem ADR formal (decisions registradas em commit message + handoff yaml apenas)
- F-S7P1-MED-03: NUM_PARALLEL=1 queue UX gap (Phase 4/5 scope)

### Tensão arquitetônica

| Aspecto | 2 containers (atual) | 1 container shared (proposto) |
|---------|---------------------|------------------------------|
| Memory reservado | 12 GiB (6+6) | **4 GiB** |
| Container overhead | ~150 MiB | **~75 MiB** |
| Volumes Docker | 2 (modelos duplicados) | **1** (modelos únicos) |
| Network endpoints | 2 hostnames | **1** (env vars indirection) |
| Failure domain | 2 instâncias (resilience) | **1 SPOF** (MVP B2B aceitável) |
| Tier-up swap latency | 0 (cada persona dedicado) | **~10-30s** (model swap) |
| Deploy complexity | docker compose 2 services | **1 service** (-50%) |
| Phase 1 ENV vars | duplicado em 2 places | **single source** |

## Decision

**Consolidar 2 Ollama containers em 1 service `ollama-shared`** com 8 OLLAMA_* env vars Phase 1 (corretos com `OLLAMA_CONTEXT_LENGTH` não `OLLAMA_NUM_CTX`).

App container mantém env vars indirection (`OLLAMA_HOST_ADVOGADO=ollama-shared:11434` + `OLLAMA_HOST_ECONOMISTA=ollama-shared:11434`) para preservar pipeline.py code unchanged.

## Rationale

### Por que consolidar agora (Phase 2)

1. **MVP B2B 1-3 users** suporta sequential inference (NUM_PARALLEL=1 + MAX_LOADED_MODELS=1 já em Phase 1)
2. **Tier=lean usa apenas qwen2.5:3b** — 2 containers desperdiçam memory por convenção arquitetônica não-validada
3. **Phase 2 é foundation Phase 3** — subprocess isolation parsing precisa memory headroom (5.1 GB peak target Cenário Y++)
4. **ADR formal absorve Phase 1 decisions** — resolves Smith F-S7P1-MED-02

### Por que NÃO containers separados (status quo)

- Overcommit 18 GiB em 7.9 GiB físico = swap thrash sob carga
- Modelos duplicados (qwen2.5:3b em 2 volumes) sem benefit real
- Phase 1 ENV vars duplicadas em 2 places (manutenção dupla)
- Failure domain "split" não usado (depends_on serial, não paralelo verdadeiro)

### Por que NÃO Kubernetes statefulset

- Over-engineering MVP (Eric SaaS B2B 1-3 users escope)
- Custo operacional (k8s control plane) sem benefit MVP
- Aumenta complexity deploy (Operator Sprint 7 quick wins philosophy)

### Por que Modelfile PARAMETER fallback NÃO escolhido (Phase 2 scope)

`OLLAMA_CONTEXT_LENGTH` env var server-level já honored Phase 1 empirically. Modelfile PARAMETER num_ctx seria per-model override (mais granular) mas:

- Requer rebuild Modelfile per modelo (qwen2.5:3b + qwen2.5:7b + sabia-7b-instruct)
- Manutenção overhead vs benefit MVP marginal
- Phase 5 polish pode adicionar se necessário (Smith F-S7P1-LOW-04 awareness)

## Alternatives Considered

### Alternative A: Manter 2 containers + apenas Phase 1 ENV vars

**Pros:** Zero migration risk, Phase 1 já entregue funcional.
**Cons:** Overcommit absurdo persiste, modelos duplicados, ADR-028 não materializa, Phase 3+ memory headroom insuficiente.
**Verdict:** Rejected — não realiza Cenário Y++ component E (consolidation = -8 GB overcommit).

### Alternative B: Kubernetes statefulset (1 pod por modelo)

**Pros:** Standard cloud-native pattern, scale horizontally future.
**Cons:** Over-engineering MVP, k8s control plane custom, Operator Sprint 7 quick wins philosophy violated, Hetzner VPS sem orquestrador instalado.
**Verdict:** Rejected — Sprint 8+ scope se SaaS escala 100+ users.

### Alternative C: 1 container shared (CHOSEN — this ADR)

**Pros:** -75 MiB overhead + -8 GB overcommit + simpler deploy + naturally pre-pulls modelos uma vez + Phase 1 ENV vars single source.
**Cons:** 1 SPOF (vs 2 instances "resilience" não-usada), tier-up swap ~10-30s edge case.
**Verdict:** **ACCEPTED** — Cenário Y++ component E + absorve Phase 1 MEDIUMs.

## Consequences

### Positive

| Benefit | Impact |
|---------|--------|
| Memory reservado 18 GiB → 8 GiB | -55% overcommit reduction (Hetzner VPS 7.9 GiB respeitado) |
| Container overhead -75 MiB | Smaller resident memory baseline |
| Single source of truth Phase 1 ENV vars | -50% manutenção docker-compose.prod.yml |
| Naturally pre-pulls qwen2.5:3b ambos personas | Resolves F-S7P1-MED-01 (sem deploy script extra) |
| ADR formal absorvendo Phase 1 decisions | Resolves F-S7P1-MED-02 (governance compliance) |
| Foundation Phase 3 subprocess isolation | Memory headroom 2.8 GB (Cenário Y++ target) |
| Volume migration preserva qwen2.5:7b + qwen2.5:3b | Zero re-download internet (Hetzner bandwidth poupada) |

### Negative

| Risk | Mitigation |
|------|-----------|
| 1 container = SPOF (vs 2 atualmente) | docker compose `restart: unless-stopped` + healthcheck + uptime-kuma monitora; MVP B2B 1-3 users aceitável |
| Tier-up swap ~10-30s (qwen2.5:3b → qwen2.5:7b) | Edge case rare (lean default MVP); Sprint 7+ tier-up UX feedback se necessário |
| Volume migration risk (corruption durante rsync) | Backup pre-Phase-2 + verify md5sum modelos pós-migration |
| Phase 1 backup `bak.20260515T215342` desatualizado | Phase 2 deploy criar novo backup `bak-pre-phase-2` |

### Neutral

| Aspecto | Detalhe |
|---------|---------|
| pipeline.py unchanged | env vars indirection (OLLAMA_HOST_ADVOGADO=ollama-shared) preserva code |
| ADR-024 tier strategy preserved | TIER_TO_MODEL_ADVOGADO/REDATOR + MODEL_ECONOMISTA mantidos |
| ADR-023 sequential LLM inference preserved | run_personas_sequencial() unchanged |

## Phase 1 Decisions Absorbed (8 OLLAMA_* env vars)

Esta seção absorve formalmente as decisions de Phase 1 D-OPS-S07-001 (resolves F-S7P1-MED-02):

### Bug Discovery — `OLLAMA_NUM_CTX` Deprecated

| Aspect | Detail |
|--------|--------|
| Spec original Aria (D-ARIA-S07-001) | `OLLAMA_NUM_CTX=8192` |
| Empirical Phase 1 deploy v0.2.7.3 | `ollama ps` mostrou CONTEXT=4096 (NÃO honored) |
| Hotfix Operator v0.2.7.4 | `OLLAMA_CONTEXT_LENGTH=8192` (Ollama 0.5+ correct env var) |
| Verification post-hotfix | CONTEXT=8192 + llama_context logs confirmam q8_0 KV cache 153 MiB |

### 8 OLLAMA_* ENV vars rationale (formalmente registradas)

```yaml
environment:
  OLLAMA_KEEP_ALIVE: "5m"
  # Mantém modelo loaded entre Step 5a (Advogado) → Step 5b (Economista) → Step 8 (Redator).
  # Tier=lean usa MESMO modelo (qwen2.5:3b) nas 3 personas — single load via KEEP_ALIVE
  # elimina 3x reload latency. 5m suficiente para pipeline completar (~3min E2E REAL).
  # Trade-off: KEEP_ALIVE=0 economizaria 1.9 GB entre requests mas adiciona reload latency.

  OLLAMA_NUM_PARALLEL: "1"
  # Default Ollama=4 reserva memória para 4 requisições paralelas. SaaS B2B MVP 1-3 users.
  # NUM_PARALLEL=1 economiza ~500MB-1GB peak. Acceptable trade-off (queue requests).
  # Smith F-S7P1-MED-03: queue UX feedback gap → Phase 4/5 ADR separate.

  OLLAMA_MAX_LOADED_MODELS: "1"
  # Tier=lean usa apenas qwen2.5:3b. MAX=1 força single model in memory.
  # Quando tier=balanced/premium escolhido, Ollama swap modelos automaticamente
  # (~10-30s latency edge case, MVP aceitável).

  OLLAMA_CONTEXT_LENGTH: "8192"
  # CDC veículo 12 pages = ~5600 tokens (Smith verified estimate).
  # Default Ollama=4096 forçava truncação contrato (PERDE info jurídica).
  # 8192 acomoda ~7100 tokens (5600 contrato + vault subset + bacen + template) sem truncação.
  # Memory cost: KV cache cresce ~2x (76.5 MiB → 153 MiB) MAS compensado por KV_CACHE_TYPE=q8_0
  # (-50% KV cache memory) → net 256 MB increase aceitável.
  # CRITICAL: Ollama 0.5+ usa OLLAMA_CONTEXT_LENGTH (NÃO OLLAMA_NUM_CTX deprecated).

  OLLAMA_NUM_THREAD: "2"
  # Match nproc=2 cores VPS Hetzner. Explicit safer que auto-detect.
  # Pode acelerar inference 5-10% por evitar oversubscription threads.

  OLLAMA_FLASH_ATTENTION: "1"
  # Ollama 0.24+ supports. Algorithmic memory-efficient attention.
  # Reduz peak memory durante long context inference em 10-20%. Zero quality loss.
  # Recommended Ollama maintainers para production deployments.

  OLLAMA_KV_CACHE_TYPE: "q8_0"
  # Default Ollama=f16 (2 bytes per token KV). q8_0 (1 byte per token KV) reduz
  # KV cache memory em ~50%. Quality loss <1% (Llama.cpp benchmarks).
  # Empirical Phase 1: 153 MiB measured (vs 306 MiB f16 calculated) ✅ -50% confirmed.

  OLLAMA_LOAD_TIMEOUT: "180s"
  # Default Ollama=5min. Reduzir para 3min força failure detection mais rápido se modelo
  # não carregar (corrupção volume, network issue). UX feedback sub-3min.
```

## Phase 2 Spec — docker-compose.prod.yml.draft

### Service `ollama-shared` (substitui ollama-advogado + ollama-economista)

```yaml
ollama-shared:
  image: ollama/ollama:latest
  container_name: revisor-prod-ollama-shared
  restart: unless-stopped
  # Sprint 7 Phase 2 (D-ARIA-S07-002 + D-OPS-S07-002): consolidation 2→1 container.
  # Absorve Phase 1 (D-OPS-S07-001) 8 OLLAMA_* env vars decisions.
  # ADR-028 governance/architecture/adr/adr-028-ollama-single-container-consolidation.md
  environment:
    OLLAMA_KEEP_ALIVE: "5m"
    OLLAMA_NUM_PARALLEL: "1"
    OLLAMA_MAX_LOADED_MODELS: "1"
    OLLAMA_CONTEXT_LENGTH: "8192"     # Ollama 0.5+ (NOT OLLAMA_NUM_CTX deprecated)
    OLLAMA_NUM_THREAD: "2"
    OLLAMA_FLASH_ATTENTION: "1"
    OLLAMA_KV_CACHE_TYPE: "q8_0"
    OLLAMA_LOAD_TIMEOUT: "180s"
  expose:
    - "11434"
  volumes:
    - ollama-models-shared:/root/.ollama
  healthcheck:
    test: ["CMD-SHELL", "ollama list || exit 1"]
    interval: 30s
    timeout: 10s
    retries: 5
    start_period: 30s
  networks:
    - revisor-internal
  deploy:
    resources:
      limits:
        memory: 4G   # vs 6G+6G atual = -8 GB overcommit reduction
```

### App container env vars update (preserva pipeline.py code)

```yaml
app:
  environment:
    OLLAMA_HOST_ADVOGADO: "ollama-shared:11434"      # was ollama-advogado:11434
    OLLAMA_HOST_ECONOMISTA: "ollama-shared:11434"    # was ollama-economista:11434
    # ... outros env vars unchanged
  depends_on:
    ollama-shared:
      condition: service_healthy
    # was: ollama-advogado + ollama-economista (REMOVED)
```

### Volume migration

```yaml
volumes:
  ollama-models-shared:
    name: revisor-prod_ollama-models-shared
  # ollama-models-advogado: REMOVED (migrated)
  # ollama-models-economista: REMOVED (migrated)
  revisor-data:
    name: revisor-prod_revisor-data
```

## Phase 2 Spec — Operator Deploy Script

### Pre-flight (Operator)

```bash
# 1. Backup pre-Phase-2 (resolves Smith F-S7P1-LOW-03)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo cp /opt/revisor-contratual/docker-compose.prod.yml \
   /opt/revisor-contratual/docker-compose.prod.yml.bak-pre-phase-2"

# 2. Backup ollama volumes (rollback safety)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo tar czf /opt/revisor-contratual/backups/ollama-volumes-pre-phase-2.tar.gz \
   /var/lib/docker/volumes/revisor-prod_ollama-models-advogado \
   /var/lib/docker/volumes/revisor-prod_ollama-models-economista"
```

### Volume migration (Operator)

```bash
# 3. Create new shared volume
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo docker volume create revisor-prod_ollama-models-shared"

# 4. Migrate qwen2.5:7b + qwen2.5:3b from advogado (HAS BOTH after Smith Phase 1 verify)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo rsync -av \
   /var/lib/docker/volumes/revisor-prod_ollama-models-advogado/_data/ \
   /var/lib/docker/volumes/revisor-prod_ollama-models-shared/_data/"

# 5. Skip economista (qwen2.5:3b já existe em advogado, evita conflict)

# 6. Verify modelos preservados
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo ls -la /var/lib/docker/volumes/revisor-prod_ollama-models-shared/_data/models/"
```

### Deploy (Operator)

```bash
# 7. Local edit docker-compose.prod.yml — replace 2 services com 1 ollama-shared
# (Aria spec acima — Operator implementa)

# 8. git commit v0.2.8.0 (MINOR bump — service consolidation)
cd c:/Users/User/Documents/the_matrix/projects/revisor-contratual-staging
git add docker-compose.prod.yml
git commit -m "feat(ops): Sprint 7 Phase 2 — Ollama container consolidation 2→1 (ADR-028)"
git tag v0.2.8.0
git push origin main
git push origin v0.2.8.0

# 9. scp + replace VPS
scp -i ~/.ssh/claudino-insights docker-compose.prod.yml \
  eric@91.108.126.149:/tmp/docker-compose.prod.yml.v0.2.8.0
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo cp /tmp/docker-compose.prod.yml.v0.2.8.0 /opt/revisor-contratual/docker-compose.prod.yml"

# 10. Stop+remove containers antigos (Phase 1 era 2 containers)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "cd /opt/revisor-contratual && \
   sudo docker compose -p revisor-prod stop ollama-advogado ollama-economista && \
   sudo docker compose -p revisor-prod rm -f ollama-advogado ollama-economista"

# 11. Up novo ollama-shared
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "cd /opt/revisor-contratual && \
   sudo docker compose -p revisor-prod up -d ollama-shared"

# 12. Recreate app com novos OLLAMA_HOST_* env vars
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "cd /opt/revisor-contratual && \
   sudo docker compose -p revisor-prod up -d app"
```

### Smoke verification (Operator)

```bash
# 13. Verify ollama-shared modelos pre-pulled (resolves F-S7P1-MED-01)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo docker exec revisor-prod-ollama-shared ollama list"
# Expected: qwen2.5:3b + qwen2.5:7b (sabia-7b-instruct optional pull)

# 14. Verify ENV vars
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo docker exec revisor-prod-ollama-shared env | grep '^OLLAMA_' | sort"
# Expected: 8 OLLAMA_* + OLLAMA_HOST = 9 vars

# 15. Smoke test inference
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo docker exec revisor-prod-ollama-shared ollama run qwen2.5:3b 'OK'"

# 16. App container connects ollama-shared (substituindo ollama-advogado/economista)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo docker exec revisor-prod-app sh -c 'curl -sf http://ollama-shared:11434/api/tags'"

# 17. Memory baseline post-Phase-2
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo docker stats --no-stream --format 'table {{.Name}}\\t{{.MemUsage}}\\t{{.MemPerc}}'"
# Expected: ollama-shared <2.5 GiB durante inference, app preserved
```

## Phase 2 Acceptance Criteria

| AC | Description | Verification command |
|----|-------------|---------------------|
| **AC-1** | Single container ollama-shared running healthy | `docker ps --filter name=revisor-prod-ollama --format '{{.Names}}'` retorna apenas `revisor-prod-ollama-shared` |
| **AC-2** | Modelos preservados (qwen2.5:3b + qwen2.5:7b) | `docker exec ollama-shared ollama list` mostra ambos |
| **AC-3** | 8 OLLAMA_* env vars + OLLAMA_HOST = 9 | `docker exec ollama-shared env \| grep OLLAMA_ \| wc -l` retorna 9 |
| **AC-4** | App container conecta ollama-shared:11434 | `docker exec app curl -sf http://ollama-shared:11434/api/tags` retorna 200 |
| **AC-5** | Memory ollama-shared <2.5 GiB durante inference | `docker stats` confirma |
| **AC-6** | Total reservado containers <10 GB | docker compose config mostra app 4G + ollama-shared 4G + outros |
| **AC-7** | App container preservado (image preserved) | `docker inspect app --format '{{.Image}}'` mantém sha256:72f4122307dc |
| **AC-8** | git commit v0.2.8.0 + tag pushed | `git log --oneline -3` mostra commit + `git tag -l` mostra v0.2.8.0 |
| **AC-9** | Backup pre-Phase-2 disponível para rollback | `ls /opt/revisor-contratual/docker-compose.prod.yml.bak-pre-phase-2` exists |
| **AC-10** | OLLAMA_CONTEXT_LENGTH=8192 honored (não OLLAMA_NUM_CTX bug Phase 1) | `docker exec ollama-shared ollama run qwen2.5:3b 'oi'` + `ollama ps` mostra CONTEXT=8192 |

## Rollback Procedure

Se Phase 2 deploy falha:

```bash
# 1. Stop ollama-shared
sudo docker compose -p revisor-prod stop ollama-shared

# 2. Restore docker-compose.prod.yml backup
sudo cp /opt/revisor-contratual/docker-compose.prod.yml.bak-pre-phase-2 \
       /opt/revisor-contratual/docker-compose.prod.yml

# 3. Restore ollama volumes (se corrompidos)
sudo tar xzf /opt/revisor-contratual/backups/ollama-volumes-pre-phase-2.tar.gz -C /

# 4. Up containers antigos
sudo docker compose -p revisor-prod up -d ollama-advogado ollama-economista app
```

## Follow-ups (Phase 3+)

| Finding | Phase | Action |
|---------|-------|--------|
| Smith F-S7P1-MED-03 (queue UX gap) | Phase 4/5 | ADR separate (SSE timeout + queue UX feedback) |
| Smith F-S7P1-LOW-04 (KV q8_0 quality untested) | Phase 5 load test | Compare q8_0 vs f16 prompt jurídico Brasileiro |
| Smith F-S7P1-LOW-05 (tier-up swap latency edge case) | Sprint 7+ | UX feedback durante model swap |
| Modelfile PARAMETER num_ctx fallback | Sprint 7+ optional | Per-model granular control se env var server-level insuficiente |

## ADR Index Update

Adicionar em [`governance/architecture/ADR-INDEX.md`](../ADR-INDEX.md):

```markdown
### Sprint 7 (Cenário Y++ refinado)
| ADR | Título | Status | Data |
|-----|--------|--------|------|
| [ADR-028](adr/adr-028-ollama-single-container-consolidation.md) | Ollama Single-Container Consolidation | ✅ Accepted | 2026-05-15 |
```

## References

- [Sprint 7 Memory Optimization Feasibility Study](../sprint-7-memory-optimization-feasibility-2026-05-15.md) (Aria D-ARIA-S07-001 + Phase 1 patches)
- [Smith Verify Sprint 7 Phase 1 CONTAINED](../../qa/smith-verify-sprint-7-phase-1-2026-05-15.md) (12 findings, 3 MEDIUMs absorved aqui)
- ADR-023 Sequential LLM Inference (preserved)
- ADR-024 Redator Tier Strategy (preserved)
- ADR-025 Redator Cascade Fallback (preserved)
- D-OPS-S07-001 Operator Phase 1 Ollama ENV vars (Phase 1 deployment + bug discovery hotfix v0.2.7.4)
- D-SMITH-S07-001 Smith CONTAINED Phase 1 verify (8/8 ACs PASS, 12 findings)

---

*— Aria, Visionary. Consolidação não é luxo arquitetônico — é honestidade matemática. 18 GiB reservado em 7.9 GiB físico era ficção tolerada por convenção. ADR-028 corrige a fantasia. Smith forçou Phase 1 absorption no record formal — bem feito. Operator próximo: deploy ollama-shared com 9 env vars (CONTEXT_LENGTH não NUM_CTX). 🏗️*
