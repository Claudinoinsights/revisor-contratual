---
type: adr
id: ADR-023
title: "Sequential LLM Inference (Advogado → Economista) — F-PROD-NEW-18 Capacity Resolution"
status: accepted
date: "2026-05-15"
domain: backend
decision_makers:
  - "@architect (Aria)"
  - "Eric (owner)"
supersedes: null
superseded_by: null
related_adrs:
  - "ADR-003 (4 personas técnicas implementação)"
  - "ADR-010 (Sabia Q4 mitigation — qwen2.5 substituto)"
  - "ADR-011 (Auto Ollama lifecycle)"
related_findings:
  - "Smith D-SMITH-S06-015 (PROD forensics — 15 findings)"
  - "Operator D-OPS-S06-017b (F-PROD-NEW-18 capacity discovery)"
tags:
  - project/revisor-contratual
  - adr
  - sprint-6
  - llm-inference
  - performance
  - capacity
---

# ADR-023 — Sequential LLM Inference (Advogado → Economista)

## Context

Sprint 6.x post-launch hotfix loop revelou bottleneck de capacidade em produção.

**Cronologia:**

1. **ADR-003 + D-MOR-3.3-C** estabeleceram fan-out paralelo das personas LLM via `asyncio.gather(advogado, economista)`. Justificativa original: paralelismo real (2 instâncias Ollama em portas distintas) reduz latência ~2x.
2. **Sprint 6.x** deploy production: VPS 91.108.126.149 com 2 containers Ollama (qwen2.5:7b + qwen2.5:3b).
3. **Smith D-SMITH-S06-015** identificou 3 bugs CRITICAL (F-PROD-01 vault syntax, F-PROD-NEW-16 LLM host, F-PROD-NEW-17 Ollama memory 3G OOM).
4. **Neo + Operator** corrigiram em cadeia (commit `4f4d87b` + infra fix `docker-compose.prod.yml` memory 3G→6G).
5. **Smoke E2E pós-fixes** revelou F-PROD-NEW-18: VPS `load average 151.32`, HTTPS response `6.75s`, Ollama crash `unexpected EOF (status -1)` em Step 5 Personas. Memory 6G suficiente — bottleneck pivotou para **CPU saturation**.

**Diagnóstico capacity (Operator D-OPS-S06-017b):**

- VPS provavelmente 4-8 CPU cores (não confirmado, mas load 151 = saturação extrema)
- qwen2.5:7b precisa ~8 cores ideal CPU inference
- qwen2.5:3b precisa ~4 cores
- Demanda total paralelismo: ~12 cores → oversubscription 1.5-3x
- Ollama internal worker process killed (kernel-level pressure OR rate limit)

## Decision

**Adotar inference sequencial:** Advogado primeiro (qwen2.5:7b), depois Economista (qwen2.5:3b).

Mudança em `bloco_workflow/orchestrator.py:64-77` — substituir `asyncio.gather(advogado, economista)` por await sequencial.

```python
# ATUAL (paralelo — D-MOR-3.3-C original):
return await asyncio.gather(
    advogado_redigir_tese_async(...),
    economista_analisar_async(...),
)

# ALVO (sequencial — ADR-023):
tese = await advogado_redigir_tese_async(...)
analise = await economista_analisar_async(...)
return (tese, analise)
```

**Mantém:**

- `asyncio.to_thread` wrap em pipeline.py (não bloquear event loop FastAPI)
- 2 containers Ollama distintos (advogado + economista) — apenas single inferência ativa por vez
- `llm_factory.py` env vars resolution (D-DEV-S06-016) — sem mudanças
- Atomicidade: se Advogado falha, Economista nem inicia (error propagation OK)

## Consequences

### Positivas

- **Zero custo infra**: VPS atual mantida, sem scale up CPU
- **LGPD on-premise preservado**: inferência local (não delega para LLM API externa)
- **Resolve F-PROD-NEW-18 imediatamente**: single LLM por vez consome ~50% CPU vs paralelo
- **UX SSE phase-events**: emitir Step 5a "Advogado em inferência" + Step 5b "Economista em inferência" — Eric vê progresso granular
- **Mantém qualidade output**: ambos LLMs Q4_K_M quantization preservada (não cai para Q2)

### Negativas (aceitas)

- **Latência ~2x maior**: estimado ~30-60s sequential vs ~15-30s paralelo (CPU-bound qwen2.5:7b)
- **Tier `balanced` MVP**: aceitável para CDC Veículos PF (~30s analysis end-to-end é razoável para advogado)
- **Sprint 7+ reconsideração**: se VPS escalado para 16+ cores OR migrarmos para LLM API, paralelismo pode voltar

### Neutras

- Atomicidade preservada: comportamento de erro idêntico (`asyncio.gather` propaga primeira exceção; sequential propaga Advogado primeiro)
- Tests devem continuar passando: `advogado_invoke_fn` + `economista_invoke_fn` injection iguais

## Alternatives Considered

| Alternativa | Pros | Cons | Rejeitada porque |
|-------------|------|------|------------------|
| **B. External LLM API** (OpenAI/Anthropic) | Zero CPU local + qualidade premium | Custo $ recorrente + viola LGPD on-premise | Cancela MVP positioning "advocacia BR LGPD-compliant" |
| **C. VPS scale up CPU** (4→16 cores) | Mantém arquitetura paralela | Custo infra recorrente + migration | Eric directive "zero custo infra agora" |
| **D. Tier reduction** (só qwen2.5:3b para ambos) | Menos CPU | Qualidade Advogado degradada (3B vs 7B) | Tese jurídica precisa raciocínio Advogado superior |
| **E. Quantization Q2_K** (qwen2.5:7b → Q2) | Mantém paralelismo + menos memory | Qualidade output piora ~20% | Trade-off não justificável para tese jurídica |

## Implementation Guidance (handoff @dev Neo)

### Arquivo a modificar

`bloco_workflow/orchestrator.py:38-77` — função `run_personas_paralelas`.

### Mudanças específicas

1. **Renomear função:** `run_personas_paralelas` → `run_personas_sequencial` (truthfulness em naming)
2. **Manter import path:** `bloco_workflow.__init__.py` exporta alias `run_personas_paralelas = run_personas_sequencial` (backward compat tests existentes)
3. **Refactor body:** await sequencial em vez de `asyncio.gather`
4. **Atualizar docstring:** referencia ADR-023 + justificativa F-PROD-NEW-18

### Tests required (Neo scope)

1. **Unit test existente** `tests/unit/test_orchestrator.py` (se existir): adapter para sequential — `advogado_invoke_fn` MUST be called BEFORE `economista_invoke_fn` (ordering assertion)
2. **Integration test NEW** `tests/integration/test_personas_sequential.py`: smoke contra Ollama real (se ambiente permitir) OR mock com sleep para verificar single-inflight
3. **Pytest 0 regressões** baseline: 36/36 parsing + 42/42 vault + 2/2 integration

### SSE phase-events (opcional UX improvement)

Considerar emitir 2 phase-start events distintos em `bloco_interface/web/app.py` (Step 5 atual → Step 5a Advogado + Step 5b Economista). Não é blocking — pode ser tech debt futura.

### Constraints

- **Manter atomicidade:** se Advogado falha, propagate exception (Economista não inicia)
- **Zero deps novas:** apenas refactor `asyncio.gather` → sequential await
- **Mantain tier_advogado kwarg:** `lean | balanced | premium` ainda configurável

## Sprint 7+ Reconsideration Triggers

Reabrir esta decisão se:

1. VPS escalada para ≥16 CPU cores (paralelismo passa a ser viável)
2. Migration para LLM API externa (B path) — Sprint 8+
3. Tier `premium` requer otimização latência crítica
4. Feature requer >2 personas simultâneas (atualmente apenas Advogado + Economista)

## References

- ADR-003 — Implementação técnica 4 personas (precedent paralelismo original D-MOR-3.3-C)
- ADR-010 — Sabia Q4 mitigation (qwen2.5 substitute)
- ADR-011 — Auto Ollama lifecycle
- Smith D-SMITH-S06-015 — PROD forensics 2026-05-15 (15 findings)
- Operator D-OPS-S06-017b — F-PROD-NEW-18 capacity discovery
- Audit entry 2026-05-15T15:18:39 UTC — `ResponseError: unexpected EOF (status -1)` em Step 5

---

*Sequential é honestidade técnica — admitir o que o hardware oferece sem teatro de paralelismo.* — Aria, 2026-05-15
