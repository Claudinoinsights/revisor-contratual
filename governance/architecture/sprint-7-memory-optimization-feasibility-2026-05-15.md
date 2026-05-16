---
type: architecture
title: "Sprint 7+ Memory Optimization Feasibility Study — Cenário Y refinado"
project: revisor-contratual
date: "2026-05-15"
author: "@architect Aria"
status: draft
related_findings:
  - F-PROD-NEW-22 (silent worker exit post-OCR)
  - Smith CONTAINED Sprint 6.x final
related_adrs:
  - ADR-023 Sequential LLM Inference
  - ADR-024 Redator Tier Strategy Audit-Honored
  - ADR-025 Redator Cascade Fallback Graceful Degradation
tags:
  - project/revisor-contratual
  - architecture
  - sprint-7
  - memory-optimization
  - feasibility-study
  - aria
---

# Sprint 7+ Memory Optimization Feasibility Study

> **Pergunta central de Eric:** É possível otimizar infraestrutura/código/Ollama para superar limitação 7.9 GiB sem recorrer ao Cenário Y (refator subprocess+PyPDF2)?
>
> **Resposta executiva Aria:** **NÃO sozinhamente.** Otimização Ollama+infra reduz pressão memória ~30-40% mas **NÃO resolve F-PROD-NEW-22** (root cause é subprocess behavior, não memória). Cenário Y (componente B subprocess isolation) é **estruturalmente necessário**. Otimização Ollama é **complemento valioso**, não substituto. Recomendação: **Cenário Y++ refinado** (B+C+Ollama+container consolidation) — runtime peak 5.1 GiB em VPS 7.9 GiB com headroom escala.

---

## Premissa empírica revisada (Smith verified + Aria validated)

### F-PROD-NEW-22 NÃO é OOM clássico

| Evidência | Valor | Interpretação |
|-----------|-------|---------------|
| `cgroup memory.events oom_kill` | **0** | Kernel NÃO matou processo |
| `OOMKilled` flag container | **false** | Docker confirma sem OOM |
| `dmesg` OOM events últimos 60min | **0** | Kernel logs limpos |
| App container peak memory | **585 MiB / 6 GiB** (12%) | App NÃO atingiu limit |
| ExitCode worker | **0** | Saída CLEAN, não SIGKILL |
| Healthcheck FailingStreak | **0** | Healthcheck NÃO triggered restart |

**Conclusão arquitetônica crítica:** F-PROD-NEW-22 NÃO é causada por memória insuficiente. É padrão de saída **silenciosa e limpa** do worker Python — característica de:

- Biblioteca chamando `os._exit()` interno (mata processo, sem traceback)
- C extension SIGABRT silencioso (PyMuPDF/marker/torch)
- `torch.multiprocessing` fork corrupting asyncio loop
- Python interpreter subprocess management edge case

**Implicação:** Otimização de memória **NÃO resolve F-PROD-NEW-22 diretamente.** Pode mitigar INDIRETAMENTE se causa for swap thrash (improvável dado evidência), mas não é fix arquitetônico.

### Insight bonus — tier=lean usa apenas qwen2.5:3b em todas personas

```python
# llm_factory.py current state (ADR-024 + Sprint 6.x optimizations):
TIER_TO_MODEL_ADVOGADO = {'lean': 'qwen2.5:3b', ...}
MODEL_ECONOMISTA = 'qwen2.5:3b'
TIER_TO_MODEL_REDATOR = {'lean': 'qwen2.5:3b', 'balanced': 'qwen2.5:3b', 'premium': 'qwen2.5:3b'}
```

**Tier=lean usa apenas 1 modelo (qwen2.5:3b) para 3 personas (Advogado+Economista+Redator).** Com `OLLAMA_KEEP_ALIVE>0`, modelo carrega 1x e serve sequencialmente.

### Marker cache ephemeral (NEW finding bonus)

`/home/revisor/.cache/datalab/models/` **NÃO está em volume mount** (apenas `/home/revisor/.local/share/revisor-contratual` é volume). Cada container restart re-baixa 3.3 GiB de modelos marker. Catalogue como **TD-MARKER-CACHE-EPHEMERAL** (Sprint 7+ trivial fix).

---

## A) Trade-off Matrix — 6 Dimensões de Otimização

### Dimensão 1: Ollama ENV vars Optimization

| Otimização | Economia memória | Effort | Risk | Impacto qualidade | Recommendation |
|------------|------------------|--------|------|-------------------|----------------|
| `OLLAMA_KEEP_ALIVE=0` | ~1.9 GiB entre requests | 5min | LOW | Latency +5-10s reload | ⚠️ Trade latency vs memory — usar `5m` em vez de 0 |
| `OLLAMA_KEEP_ALIVE=5m` (default) | 0 (current) | — | — | — | Mantém atual (modelo loaded entre Step 5-8) |
| `OLLAMA_NUM_PARALLEL=1` | ~500 MB-1 GiB peak | 5min | LOW | Sem impacto (1 user MVP) | ✅ **APLICAR** (default 4 desperdiça em SaaS B2B 1-3 users) |
| `OLLAMA_MAX_LOADED_MODELS=1` | ~3-5 GiB potencial | 5min | LOW | Sem impacto tier=lean | ✅ **APLICAR** (força sequential load) |
| `OLLAMA_CONTEXT_LENGTH=8192` (vs default 4096) | +256 MB (perda compensada por q8_0) | 5min | LOW | Eliminates truncation | ✅ **APLICAR** (CDC veículo 12 pages = ~5600 tokens > 4096 default) — **EMPIRICAL DISCOVERY Operator Phase 1 hotfix v0.2.7.4: env var correto é `OLLAMA_CONTEXT_LENGTH` (Ollama 0.5+); `OLLAMA_NUM_CTX` foi deprecated.** |
| `OLLAMA_NUM_THREAD=2` (matching nproc) | 0 (perf) | 5min | LOW | Pode acelerar 5-10% | ✅ **APLICAR** |
| `OLLAMA_LOAD_TIMEOUT=180s` (default 5min) | 0 | 5min | LOW | Faster failure detection | ✅ **APLICAR** |
| `OLLAMA_FLASH_ATTENTION=1` | -10-20% inference memory | 5min | LOW | None (algorithmic optimization) | ✅ **APLICAR** (Ollama 0.24+ supports) |
| `OLLAMA_KV_CACHE_TYPE=q8_0` | -50% KV cache (~256 MB at 8k ctx) | 5min | LOW | <1% quality loss | ✅ **APLICAR** |
| Quantization Q3_K_S (vs Q4_K_M) | -800 MB (3b model 1.9→1.1 GB) | 1h | MED | 5-10% quality loss | ⏳ **TESTAR** Sprint 7 spike |
| Quantization Q2_K | -1.4 GB (3b model 1.9→0.5 GB) | 1h | HIGH | 15-25% quality loss | ❌ **EVITAR** (LGPD jurídico exige qualidade) |

**Combo Ollama optimization total estimate:** ~600 MB savings inference peak + memory pressure relief.

### Dimensão 2: Consolidar Ollama Containers (2 → 1)

| Aspecto | Atual (2 containers) | Proposto (1 container) | Delta |
|---------|---------------------|------------------------|-------|
| Container overhead | ~150 MB (2 instances Ollama) | ~75 MB | -75 MB |
| Network simplification | 2 hostnames (advogado/economista) | 1 hostname (ollama) | Simpler |
| Model isolation | Cada persona seu container | Shared instance | Trade-off |
| Tier flexibility | Diff models per persona possível | Sequential model swap | Acceptable MVP |
| Failure domain | Independente | Shared | Trade-off |
| Deploy complexity | docker-compose 2 services | 1 service | -50% |
| Memory limit total | 6+6=12 GB reservado | 4 GB reservado | -8 GB overcommit reduction |

**Effort:** 2-3 horas (Operator update docker-compose.prod.yml + app env vars OLLAMA_HOST_*).

**Risk:** LOW (BIM behavior MVP escope único user).

**Recommendation:** ✅ **APLICAR** — Eric escope BYOK B2B MVP suporta consolidation.

### Dimensão 3: Marker Library Optimization

| Otimização | Economia | Effort | Risk | Quality |
|-----------|----------|--------|------|---------|
| Marker cache em volume mount | 0 RAM (mas elimina re-download 3.3GB cada restart, salva ~3min startup) | 30min | LOW | None | ✅ **APLICAR** (TD-MARKER-CACHE-EPHEMERAL) |
| Skip `ocr_error_detection` model | ~600 MB cache | 1h | MED | OCR validation perdida (acceptable born-digital) | ⏳ **CONDITIONAL** apenas se born-digital path implementado |
| Skip `table_recognition` model | ~400 MB cache | 1h | LOW | CDC veículo: contratos sem tabelas complexas | ✅ **APLICAR** se born-digital fast path implementado |
| Lazy import marker (load só Step 1) | 0 (Python module caching impede unload) | — | — | — | ❌ NÃO viável (Python keeps modules loaded) |
| Marker subprocess isolation | 3.3 GB liberados pós Step 1 (RESOLVE F-PROD-NEW-22 também) | 3-4 dias Neo | MED | None | ✅ **ESSENCIAL** (Cenário Y componente B) |

### Dimensão 4: Pipeline Architecture Optimization

| Otimização | Economia | Effort | Risk | Quality |
|-----------|----------|--------|------|---------|
| Force `gc.collect()` entre steps | ~50-200 MB (Python overhead) | 30min | LOW | None | ✅ **APLICAR** (defensive memory management) |
| `torch.cuda.empty_cache()` (no-op CPU) | 0 (sem GPU) | — | — | — | ❌ NÃO aplicável (CPU mode) |
| Truncate parsed_contract pós Step 1 | ~50-100 MB | 2h | MED | Logging/audit truncation | ⏳ **TESTAR** Sprint 7 |
| JSON streaming Ollama (vs full buffer) | Variável, ~200-500 MB durante geração | 4h | MED | Implementação SSE adaptation | ⏳ **CONSIDERAR** Sprint 7+ |
| Subprocess isolation parsing (componente B Cenário Y) | 3.3 GB liberados pós Step 1 | 3-4 dias | MED | RESOLVE F-PROD-NEW-22 + memory + audit recovery | ✅ **ESSENCIAL** |

### Dimensão 5: Container Resource Allocation

| Configuração | Atual | Proposto | Justificativa |
|-------------|-------|----------|---------------|
| App container limit | 6 GiB | **4 GiB** | Peak observed 585 MiB; 4 GiB fornece 7x headroom |
| Ollama container(s) limit | 6+6=12 GiB | **4 GiB single** | qwen2.5:3b loaded 1.9 GB + KV cache 256 MB + overhead 250 MB = 2.4 GB ; 4 GiB fornece 1.6x headroom |
| Total reservado | **18 GiB** | **8 GiB** | -55% overcommit reduction |
| VPS swap | 2 GiB | **4 GiB** | Absorver picos sem matar processos (NVMe SSD swap aceitável MVP) |
| `vm.swappiness` | 10 (current) | 10 (manter) | Bom para evitar swap thrash |
| `cgroup memory.swap.max` | unlimited | per-container 1 GiB | Evita 1 container engulir todo swap |

**Total reservado novo:** 4 + 4 + 0.7 (other containers) = **8.7 GiB ≈ VPS capacity 7.9 GiB** (sem overcommit absurdo).

### Dimensão 6: Código Pipeline.py Otimizações

| Otimização | Economia | Effort | Risk | Quality |
|-----------|----------|--------|------|---------|
| `audit_payload` flush parcial (entre steps) | ~50 MB | 2h | LOW | Audit chain HMAC needs adapation | ⏳ **CONSIDERAR** Sprint 7 |
| Pydantic `model_copy(deep=False)` (vs default deep) | ~20-50 MB | 30min | LOW | None se objects immutable | ✅ **APLICAR** review |
| Eliminar redundância tese/análise objects | ~10-30 MB | 1h | LOW | Refactoring | ⏳ **OPCIONAL** |
| Streaming parser (vs full buffer parsed_contract) | Variável | 4-6h | MED | Architectural | ❌ Sprint 8+ scope |

---

## B) Combo Recommendation — Cenário Y++ Refined

### Combo Y++ Composição

| Componente | Origem | Memory savings runtime | Effort | Risk |
|------------|--------|----------------------|--------|------|
| **B** Subprocess isolation parsing | Cenário Y original | -3.3 GB pós Step 1 + RESOLVE F-PROD-NEW-22 | 3-4 dias | MED |
| **C** PyMuPDF born-digital fast path | Cenário Y original | -3.3 GB em 80% casos + -90s latency | 2-3 dias | MED |
| **D** Ollama ENV vars combo | Aria addition | ~600 MB inference + KV cache q8_0 | 30min | LOW |
| **E** Consolidar 2 Ollama containers em 1 | Aria addition | -75 MB overhead + -8 GB overcommit | 2-3h | LOW |
| **F** Container limits ajustados (app 4G + ollama 4G) | Aria addition | -8 GB overcommit | 1h | LOW |
| **G** Marker cache em volume mount | Aria addition | 0 RAM (elimina re-download startup) | 30min | LOW |
| **H** Force GC entre pipeline steps | Aria addition | ~50-200 MB defensive | 30min | LOW |
| **I** OLLAMA_CONTEXT_LENGTH=8192 (eliminate truncation) | Aria addition + Operator Phase 1 hotfix | +256 MB (compensated by D KV q8_0 = -153 MB net) | 5min | LOW |

**Total memory savings:** ~7-10 GiB pico (depende caso born-digital vs scanned)

**Total effort:** 6-8 dias (5-6 dias original Y + 1-2 dias adicional otimizações)

**Total risk:** MEDIUM (mantido pelo componente B subprocess refactoring)

### Pipeline Runtime Memory após Y++

#### Caso 80%: Born-digital PDF (PyMuPDF fast path)

```text
Step 1 Parsing (PyMuPDF):
  App container: 600 MB
  PyMuPDF in-memory: 50 MB (vs 3.3 GB marker)
  Other containers: 700 MB
  OS: 500 MB
  Subtotal: 1.85 GB

Step 5-8 LLM phase (qwen2.5:3b):
  App container: 600 MB
  Ollama container: 1.9 GB (qwen2.5:3b) + 256 MB KV cache q8_0 + 250 MB overhead = 2.4 GB
  Other containers: 700 MB
  OS: 500 MB
  Subtotal: 4.2 GB

PEAK NEVER EXCEEDS: 4.2 GB / 7.9 GB (53% utilization)
```

**Headroom: 3.7 GB** para múltiplos users simultâneos OR upgrade tier=balanced (qwen2.5:7b 4.7 GB).

#### Caso 20%: Scanned PDF (Marker subprocess isolated)

```text
Step 1 Parsing (Marker subprocess fork):
  App container parent: 600 MB (parent waits)
  Marker subprocess: 3.3 GB (transient)
  Other containers: 700 MB
  OS: 500 MB
  Subtotal: 5.1 GB (durante OCR)

Step 1 cleanup: subprocess exits → 3.3 GB liberados

Step 5-8 LLM phase (qwen2.5:3b):
  App container: 600 MB
  Ollama container: 2.4 GB
  Other containers: 700 MB
  OS: 500 MB
  Subtotal: 4.2 GB

PEAK: 5.1 GB durante OCR, depois 4.2 GB durante LLM
PEAK MAX: 5.1 GB / 7.9 GB (65% utilization)
```

**Headroom: 2.8 GB** mesmo no pior caso scanned PDF.

---

## C) Viabilidade E2E REAL com 7.9 GiB VPS — Resposta Definitiva

### SEM Cenário Y (apenas otimização Ollama+container)

**Probabilidade pipeline E2E REAL funcional: BAIXA (20-30%).**

Razões honestas:

1. **F-PROD-NEW-22 não é fix por memória.** Root cause é subprocess behavior (marker/torch/PyMuPDF). Mesmo com Ollama otimizado, marker library remains in-process e crash kill worker.

2. **Marker 3.3 GB persistent durante LLM phase.** Sem subprocess, modelos marker não são liberados após parsing. Total runtime memory: 3.3 + 2.4 (Ollama) + 600 MB (app) + 700 MB (other) + 500 MB (OS) = **7.5 GB / 7.9 GB (95% utilization)** — *thin margin para qualquer pico*.

3. **Audit chain não recupera de marker crash.** Sem subprocess isolation, marker `os._exit(0)` mata worker antes de escrever audit entry. F-PROD-NEW-22 persiste.

### COM Cenário Y++ refinado

**Probabilidade pipeline E2E REAL funcional: ALTA (90-95%).**

Razões empíricas:

1. **B subprocess isolation resolve F-PROD-NEW-22** — marker crashes NÃO matam parent worker. Audit chain registra erro graceful.

2. **Memory peak reduzido para 5.1 GB** worst case (65% utilization) — confortável no VPS 7.9 GB.

3. **Headroom escala** para 1-3 users simultâneos sem upgrade.

4. **Quality output preservada** — qwen2.5:3b mantido (não Q2_K agressivo) + flash_attention + KV q8_0 são otimizações algorítmicas sem perda significativa.

---

## D) Cenário Y vs Y++ — Comparison Honesta

| Aspecto | Cenário Y original (B+C) | Cenário Y++ (B+C+D+E+F+G+H+I) |
|---------|---------------------------|-----------------------------|
| F-PROD-NEW-22 fix | ✅ Resolve | ✅ Resolve |
| Born-digital fast path | ✅ Sim (PyMuPDF) | ✅ Sim (PyMuPDF) |
| Memory peak runtime | ~6.5 GB | **~5.1 GB worst case** |
| Headroom escala | ~1.4 GB | **~2.8 GB** |
| Ollama optimization | ❌ Não inclui | ✅ Inclui |
| Container consolidation | ❌ Não inclui | ✅ Inclui |
| Effort | 5-6 dias | 6-8 dias (+1-2 dias) |
| Risk | MEDIUM | MEDIUM (mesmo, dominado por B) |
| Future-proof escala | LIMITADO | **CONFORTÁVEL** (1-3 users sem upgrade) |
| ROI custo VPS | =0 imediato | Possível downgrade VPS futuro Hetzner CCX13 |
| Sustentabilidade SaaS B2B | Marginal | **Robusta** |

**Recomendação Aria honesta: Cenário Y++ vale o investimento adicional 1-2 dias.**

Razões:
- Otimização Ollama é **trivial** (5min env vars) com **alto impacto** (600 MB savings)
- Container consolidation é **simplificação arquitetônica** + redução overcommit absurdo (18 GB → 8 GB)
- Marker cache volume mount é **TD trivial** (30min) que evita 3min latência por restart
- Combinados, 1-2 dias adicional fornece **SaaS B2B production-ready** vs **MVP marginal** Cenário Y puro

---

## E) Sprint 7 Plan — 5 Fases

### Phase 1: Ollama Optimization Quick Wins (1 dia)

**Owner:** @devops Operator (config-only, sem código)

**Tarefas:**

```yaml
# docker-compose.prod.yml — ollama-shared (consolidado, ver Phase 2)
environment:
  OLLAMA_KEEP_ALIVE: "5m"           # mantém modelo loaded entre Step 5-8
  OLLAMA_NUM_PARALLEL: "1"          # SaaS B2B 1-3 users, sem paralelismo
  OLLAMA_MAX_LOADED_MODELS: "1"     # tier=lean usa apenas qwen2.5:3b
  OLLAMA_CONTEXT_LENGTH: "8192"     # contratos CDC veículo ~5600 tokens (Ollama 0.5+ env var; OLLAMA_NUM_CTX deprecated)
  OLLAMA_NUM_THREAD: "2"            # match nproc=2 VPS
  OLLAMA_FLASH_ATTENTION: "1"       # Ollama 0.24+ memory efficient attention
  OLLAMA_KV_CACHE_TYPE: "q8_0"      # -50% KV cache memory, <1% quality loss
  OLLAMA_LOAD_TIMEOUT: "180s"       # faster failure detection
deploy:
  resources:
    limits:
      memory: 4G                     # vs 6G atual cada (consolidado)
```

**Acceptance Criteria:**
- ENV vars verified via `docker exec ollama env | grep OLLAMA_`
- Smoke test pipeline tier=lean: latência primeira inference qwen2.5:3b < 30s
- Memory baseline pós-load: < 2.5 GB

### Phase 2: Container Consolidation (1 dia)

**Owner:** @devops Operator + @architect Aria architecture review

**Tarefas:**

1. Update `docker-compose.prod.yml` — merge `ollama-advogado` + `ollama-economista` em `ollama-shared`
2. Update app env vars: `OLLAMA_HOST_ADVOGADO=ollama-shared:11434`, `OLLAMA_HOST_ECONOMISTA=ollama-shared:11434`
3. Migrar volume `ollama-models-economista` → `ollama-models-shared` (script ops)
4. Verificar tier-down ADR-024 ainda funciona com shared instance

**Acceptance Criteria:**
- 1 container Ollama running (vs 2 anteriores)
- Models qwen2.5:3b + qwen2.5:7b + sabia-7b-instruct disponíveis em shared instance
- Smoke test: app conecta em ambos hostnames (advogado/economista) → mesma instance
- Memory: 1 container 4 GB vs 2 containers 12 GB anteriormente

### Phase 3: Subprocess Isolation Parsing (3-4 dias) — FUNDAMENTAL

**Owner:** @dev Neo + @architect Aria architecture spec + @smith verify

**Tarefas:**

1. **Aria spec design** (4h):
   - Design subprocess runner module `bloco_engine.parsing.subprocess_runner`
   - Inter-process protocol (JSON stdin/stdout vs pickle vs shared memory)
   - Timeout + signal handling (SIGTERM graceful, SIGKILL cleanup)
   - Audit chain integration (capture subprocess errors)

2. **Neo implementation** (2-3 dias):
   - Refactor `pipeline.py` Step 1: replace `await asyncio.to_thread(parse_contract, ...)` por `await asyncio.subprocess.exec`
   - Implement `bloco_engine.parsing.subprocess_runner.py` (CLI interface)
   - Tests: unit + integration + E2E
   - Error handling: subprocess crash → audit entry + graceful degradation ADR-025

3. **Smith verify** (4h):
   - F-PROD-NEW-22 reproduction test → CRASH subprocess instead of worker
   - Audit chain entry verification (mesmo em crash scenarios)
   - Memory profiling: parent process memory liberada pós subprocess exit

**Acceptance Criteria:**
- F-PROD-NEW-22 RESOLVED — pipeline completa Steps 2-9 mesmo se marker crash
- Audit chain registra subprocess errors com `error_type=ParsingSubprocessFailed`
- App container memory pós Step 1: < 700 MB (subprocess deallocated)
- Subprocess timeout 180s + SIGKILL fallback

### Phase 4: PyMuPDF Born-Digital Fast Path (2-3 dias)

**Owner:** @dev Neo + @architect Aria pattern design

**Tarefas:**

1. **Aria spec design** (2h):
   - Detection logic: `fitz.open(pdf).extract_text() > N_threshold` → born-digital
   - Threshold calibration: testar com sample CDC veículo PDFs
   - Fallback: if PyMuPDF text extraction quality < threshold → escalate to marker subprocess

2. **Neo implementation** (2-3 dias):
   - Add PyMuPDF parser module `bloco_engine.parsing.pymupdf_parser`
   - Conditional logic em `parse_contract()`: born-digital → PyMuPDF, scanned → marker subprocess
   - Tests: unit + integration with sample PDFs (born + scanned)
   - Audit metadata: registrar `parser_used: "pymupdf" | "marker_subprocess"`

**Acceptance Criteria:**
- 80% CDC veículo PDFs born-digital path (PyMuPDF) — verify com sample dataset
- 20% scanned path (marker subprocess) — fallback funcional
- Latency born-digital: < 200ms parsing (vs 30-90s marker)
- Quality: extracted text matches contract structure (acceptance via @qa Oracle smoke)

### Phase 5: Marker Cache Persistence + Polish (1 dia)

**Owner:** @devops Operator + @dev Neo

**Tarefas:**

1. **Operator** (30min): Add volume mount `marker-cache` → `/home/revisor/.cache/datalab/models` em docker-compose.prod.yml
2. **Neo** (2h): Add `gc.collect()` calls entre pipeline steps (defensive memory management)
3. **Operator** (30min): Update `vm.swappiness` if needed + cgroup `memory.swap.max=1G` per container
4. **Smith verify final** (4h): E2E REAL pipeline 9/9 audit keys + load test 1-3 concurrent users

**Acceptance Criteria:**
- Container restart NÃO re-baixa 3.3 GB models (cache persists)
- 3 concurrent users pipeline E2E REAL: passa sem swap thrash
- Smith CLEAN_FINAL Sprint 7 verdict

### Total Sprint 7 Effort: **8-9 dias**

| Phase | Effort | Owner | Risk |
|-------|--------|-------|------|
| 1. Ollama optimization | 1 dia | @devops | LOW |
| 2. Container consolidation | 1 dia | @devops + @architect | LOW |
| 3. Subprocess isolation | 3-4 dias | @dev + @architect + @smith | MED |
| 4. PyMuPDF born-digital | 2-3 dias | @dev + @architect | MED |
| 5. Cache + polish + load test | 1 dia | @devops + @dev + @smith | LOW |

---

## Decisão Eric — 3 Caminhos Atualizados

| Cenário | Description | Effort | Memory peak | E2E REAL viable? | Future scale |
|---------|-------------|--------|-------------|-------------------|--------------|
| **Y original (B+C)** | Subprocess + PyMuPDF | 5-6 dias | 6.5 GB | ✅ Sim | LIMITED 1.4 GB headroom |
| **Y++ (B+C+D+E+F+G+H+I)** | Y + Ollama opt + container consolidation | 8-9 dias | **5.1 GB** | ✅ **Sim** | **CONFORTÁVEL 2.8 GB headroom** |
| **Optimization-only (D+E+F+G+H+I)** | Sem subprocess, sem PyMuPDF | 2-3 dias | 7.5 GB | ❌ Probabilidade BAIXA (F-PROD-NEW-22 persists) | ❌ Sem margem |

**Recomendação Aria honesta:** **Cenário Y++** é a escolha visionariamente racional. Marginal effort adicional (1-2 dias) traz arquitetura **production-ready** vs **MVP marginal**.

---

## Anti-padrões evitados nesta análise

| Anti-padrão | Evitado |
|-------------|---------|
| "Vamos só dar mais RAM" | ❌ Band-aid, não cura root cause F-PROD-NEW-22 |
| "Quantization Q2_K resolve tudo" | ❌ 15-25% quality loss inaceitável LGPD jurídico |
| "GPU resolve OCR" | ❌ Hetzner sem GPU + custo recorrente alto |
| "Migrar para Kubernetes" | ❌ Over-engineering MVP escope BYOK B2B |
| "BYOK puro elimina problema" | ⚠️ Sim mas Eric quer manter Ollama local opção |
| "Refactor pipeline para microservices" | ❌ Sprint 8+ scope, não MVP |

---

## Referências técnicas

- Ollama 0.24.0 changelog: flash_attention + KV cache types support
- PyMuPDF (fitz) docs: https://pymupdf.readthedocs.io/en/latest/
- ADR-023 Sequential LLM Inference (governance/architecture/adr/)
- ADR-024 Redator Tier Strategy Audit-Honored
- ADR-025 Redator Cascade Fallback Graceful Degradation
- Smith CONTAINED Sprint 6.x final report (governance/qa/smith-verify-final-sprint-6x-2026-05-15.md)
- D-OPS-S06-039 Operator Option D Dockerfile fix

---

## Sprint 7 ADRs propostos (Aria Sprint 7 deliverable)

- **ADR-026:** Marker Subprocess Isolation Parsing — F-PROD-NEW-22 architectural fix
- **ADR-027:** PyMuPDF Born-Digital Fast Path — pipeline performance + quality
- **ADR-028:** Ollama Single-Container Consolidation — MVP simplification
- **ADR-029:** Marker Cache Persistence Volume Mount — TD-MARKER-CACHE-EPHEMERAL fix

---

*— Aria, Visionary. Otimização sozinha não cura a inevitabilidade que Smith encontrou. Mas combinada com isolation arquitetônica, transforma um MVP frágil em uma plataforma SaaS sustentável. O caminho é Y++ — não porque é o mais rápido, mas porque é o que projeta o futuro. 🏗️*

---

## Empirical Updates (Phase 1 Operator + Smith CONTAINED 2026-05-15)

Este documento foi corrigido empiricamente após Phase 1 deploy + Smith CONTAINED verify:

### Bug Discovery — `OLLAMA_NUM_CTX` é DEPRECATED

| Spec original | Realidade empírica | Correto |
|---------------|-------------------|---------|
| `OLLAMA_NUM_CTX=8192` | Ollama 0.24.0 NÃO honra (CONTEXT permaneceu 4096) | `OLLAMA_CONTEXT_LENGTH=8192` (Ollama 0.5+) |

**Verificação Operator Phase 1 (D-OPS-S07-001) hotfix v0.2.7.4:**
- Initial deploy v0.2.7.3 com `OLLAMA_NUM_CTX=8192` → `ollama ps` mostrou CONTEXT=4096 (NÃO honored)
- Hotfix v0.2.7.4 com `OLLAMA_CONTEXT_LENGTH=8192` → CONTEXT=8192 honored ✅
- Llama_context logs confirmaram `K (q8_0): 76.50 MiB, V (q8_0): 76.50 MiB` (KV cache q8_0 -50% mathematically validated)

### Sprint 7 Plan Effort — Phase 1 Actual vs Estimated

| Phase | Estimate Aria | Actual Operator | Delta |
|-------|--------------|-----------------|-------|
| Phase 1 Ollama optimization | 1 dia | **~1.5h** | -85% (speed bonus, simpler than esperado) |

Demais Phases (2-5) effort estimates revisados em [ADR-028](adr/adr-028-ollama-single-container-consolidation.md).

### Smith CONTAINED Phase 1 — 3 MEDIUMs absorbed em ADR-028

- F-S7P1-MED-01: qwen2.5:3b pre-pull em deploy script
- F-S7P1-MED-02: ADR-028 absorve Phase 1 8 OLLAMA_* env vars decisions
- F-S7P1-MED-03: SSE queue UX → Phase 4/5 (separate ADR)

7 LOWs awareness em [smith-verify-sprint-7-phase-1-2026-05-15.md](../qa/smith-verify-sprint-7-phase-1-2026-05-15.md).

*— Aria patch 2026-05-15 (D-ARIA-S07-002). Honestidade arquitetônica exige reconhecer empirical discovery de Operator + Smith adversarial findings. Visão não é dogma.*
