---
type: adr
id: ADR-024
title: "Redator Tier Strategy — Audit-Honored Tier Parameter (Caminho C)"
status: accepted
date: "2026-05-15"
domain: backend
adr_level: design
decision_makers:
  - "@architect (Aria)"
  - "Eric (owner — directive 2026-05-15 'nível melhor que adequado')"
supersedes: null
superseded_by: null
related_adrs:
  - "ADR-022 (Persona Redator Revisional — tier param origem D1)"
  - "ADR-023 (Sequential LLM Inference — F-PROD-NEW-18 capacity)"
  - "ADR-025 (Redator Cascade Fallback Strategy — companion ADR mesma sessão)"
related_findings:
  - "Smith F-S21-03 HIGH (D-SMITH-S06-022 — tier semantic abandoned silently)"
  - "TD-SP07-TIER-SEMANTIC-DECISION (governance/TECH-DEBT.md MEDIUM)"
  - "Neo D-DEV-S06-021 (F-PROD-NEW-19 tier-down qwen2.5:7b→3b)"
  - "Neo D-DEV-S06-023 (DeprecationWarning band-aid temporário)"
tags:
  - project/revisor-contratual
  - adr
  - sprint-6
  - llm-redator
  - tier-strategy
  - audit-integrity
---

# ADR-024 — Redator Tier Strategy (Audit-Honored)

## Context

Sprint 6.x hotfix chain (F-PROD-NEW-19 Redator crash → D-DEV-S06-021 tier-down) deixou tier parameter em estado ambíguo que Smith adversarial review D-SMITH-S06-022 capturou como F-S21-03 HIGH.

**Estado atual `_default_invoke(prompt, tier: LLMTier)` em [redator.py:315-365](../../../bloco_workflow/personas/redator.py#L315-L365):**

- `tier: LLMTier = "balanced"` mantém na assinatura (backward-compat) mas é **IGNORADO** pelo model selection logic desde D-DEV-S06-021
- Production path real usa SEMPRE `MODEL_ECONOMISTA_REDATOR` (qwen2.5:3b) como primary independente de `tier`
- Caller `redator_invoke(tier=tier_redator)` em [pipeline.py:370](../../../bloco_workflow/pipeline.py#L370) passa tier mas modelo escolhido não respeita
- D-DEV-S06-023 fix temporário: emite DeprecationWarning runtime se tier != "balanced" — **band-aid** que sinaliza problema sem resolver

**Tensão semântica:**

| Aspecto | TIER_TO_MODEL_ADVOGADO (Advogado) | Redator pós F-PROD-NEW-19 |
|---------|----------------------------------|---------------------------|
| `lean` | qwen2.5:3b | (ignorado) → qwen2.5:3b |
| `balanced` | qwen2.5:7b | (ignorado) → qwen2.5:3b |
| `premium` | sabia-7b-instruct | (ignorado) → qwen2.5:3b |

API consumer invocando `tier_redator="premium"` espera modelo premium (sabia-7b-instruct) — recebe qwen2.5:3b silently. **Forensic audit chain** registra `redator_persona_used="qwen2.5:3b"` corretamente (Smith F-S21-02 fix) mas **intent vs reality** continua divergente.

## Decision

**Adotar Caminho C: Audit-Honored Tier — preserve API surface, registre intent em audit chain, sem mudança de model selection.**

### Mudanças específicas

1. **Manter assinatura existente:** `_default_invoke(prompt, tier: LLMTier = "balanced")` — backward compat 100%
2. **Manter DeprecationWarning runtime** (D-DEV-S06-023): se tier != "balanced", warning informativo
3. **Adicionar audit field NEW** `tier_consumed`: registrar intent original do caller para análise forense post-incident
4. **Atualizar docstring** com bloco "INTENT vs REALITY" explicando trade-off honestamente
5. **Atualizar TIER_TO_MODEL_REDATOR constant** em llm_factory.py mapping documentando reality: `{lean: 3b, balanced: 3b, premium: 3b}` — espelhando comportamento atual, removendo ambiguity

```python
# llm_factory.py — NEW constant (ADR-024)
TIER_TO_MODEL_REDATOR: dict[LLMTier, str] = {
    "lean": "qwen2.5:3b",      # consistente F-PROD-NEW-19
    "balanced": "qwen2.5:3b",  # default — pós tier-down
    "premium": "qwen2.5:3b",   # ADR-024 trade-off — Sprint 7+ pode promover para 7b
}
```

6. **Pipeline.py audit chain enrichment** linha ~389: além de `redator_persona_used` (modelo REAL), adicionar `redator_tier_consumed` (intent original):

```python
audit_payload["redator_persona_used"] = redator_model_capture.get(
    "actual_model_used", MODEL_ECONOMISTA  # F-PROD-NEW-19 reality
)
audit_payload["redator_tier_consumed"] = tier_redator  # ADR-024 intent capture
```

## Consequences

### Positivas

- **Audit chain forense honesto**: `redator_tier_consumed` separado de `redator_persona_used` permite post-incident analysis distinguir intent vs reality
- **Zero breaking change**: API consumers existentes (pipeline.py + tests) funcionam sem migration
- **LGPD compliance preservada**: audit trail completo do que foi solicitado E entregue
- **DeprecationWarning + docstring DEPRECATED bloco** sinalizam ambiguity sem quebrar
- **TIER_TO_MODEL_REDATOR constant** documenta reality explicitamente — eliminar mistério para futuros devs
- **Sprint 7+ escalada simples**: quando VPS escalada para 16+ cores, basta atualizar `TIER_TO_MODEL_REDATOR["premium"] = "qwen2.5:7b"` (1 linha)

### Negativas (aceitas)

- **Tier semantic still ambígua até Sprint 7+**: 3 tiers diferentes resultam em mesmo modelo — não há tier "real" agora
- **Audit field NEW (`redator_tier_consumed`)**: requer migration audit schema (additive, retrocompatível — entries antigas não têm field, novas têm)
- **TIER_TO_MODEL_REDATOR duplicação parcial**: tier mapping para Redator coexiste com TIER_TO_MODEL_ADVOGADO — clareza vs duplicação trade-off (escolhemos clareza)

### Neutras

- **Backward-compat alias preservado**: tests existentes (`tests/unit/test_redator_persona.py`) continuam passando sem mudança
- **TD-SP07-FALLBACK-MAP-REMOVAL** continua escopo Sprint 7+ (independente desta ADR)

## Alternatives Considered

| Caminho | Pros | Cons | Rejeitada porque |
|---------|------|------|------------------|
| **A. Restore tier semantic** ({lean: 3b, balanced: 3b, premium: 7b}) | API meaningful + permite escalada manual | Premium = qwen2.5:7b reativa F-PROD-NEW-19 cascade risk + complexidade adicional `_default_invoke` (branch logic) | VPS atual não suporta 7b sustentável para Redator pós Step 6 Juiz. ADR-025 cascade fallback strategy depende de NÃO usar 7b. |
| **B. Remover tier param totalmente** | Sem ambiguity + API limpa | Breaking change — pipeline.py linha 370 + tests injection + caller signature change | Eric directive "concerte tudo" não inclui breaking changes API surface. Trade-off complexidade fix vs benefit não vale. |
| **C. Audit-Honored Tier (RECOMENDADA)** | Backward compat + audit forensic + zero breaking + DeprecationWarning sinaliza | Tier ainda ambíguo até Sprint 7+ | Adotada — trade-off ideal para Sprint 6.x scope. |

## Implementation Guidance (handoff @dev Neo)

### Arquivos a modificar

1. **`bloco_workflow/personas/llm_factory.py`** — adicionar constant `TIER_TO_MODEL_REDATOR` (~5 linhas)
2. **`bloco_workflow/personas/redator.py`** — `_default_invoke` body: substituir hardcoded `MODEL_ECONOMISTA_REDATOR` por `TIER_TO_MODEL_REDATOR[tier]` (linha ~362)
3. **`bloco_workflow/pipeline.py`** — audit chain enrichment: adicionar `audit_payload["redator_tier_consumed"] = tier_redator` após linha 401
4. **`tests/unit/test_redator_persona.py`** — adicionar test `test_audit_chain_records_tier_consumed_intent` validando audit field

### Mudanças específicas redator.py

```python
# ANTES (D-DEV-S06-023):
primary_model = MODEL_ECONOMISTA_REDATOR  # qwen2.5:3b — economista host

# DEPOIS (ADR-024):
primary_model = TIER_TO_MODEL_REDATOR[tier]  # ADR-024 audit-honored
                                              # Sprint 7+ pode diferenciar tiers
```

### Mudanças específicas pipeline.py

```python
# ADR-024 audit chain enrichment (após linha 401):
audit_payload["redator_tier_consumed"] = tier_redator  # intent capture
audit_payload["redator_tier_strategy"] = "audit-honored-v1"  # ADR-024 marker
```

### Tests required (Neo scope)

1. **NEW** `test_audit_chain_records_tier_consumed_intent` — assert audit payload contém `redator_tier_consumed` == tier passed
2. **NEW** `test_tier_to_model_redator_consistency` — todos 3 tiers → "qwen2.5:3b" (lock contra accidental escalada premature)
3. **Update** `test_model_capture_records_tier_when_invoke_fn_provided` — verificar tanto `actual_model_used` (reality) quanto `tier_consumed` (intent)
4. **DeprecationWarning** silenciado em tests via `pytest.warns(DeprecationWarning)` context se tier != "balanced"

### Constraints

- **NÃO remover** `tier` parameter — backward compat MUST
- **NÃO mudar** TIER_TO_MODEL_ADVOGADO (Advogado mantém tier semantic real)
- **Manter** DeprecationWarning runtime de D-DEV-S06-023 (sinalização API surface)
- **Manter** TIER_TO_MODEL_REDATOR all-3b mapping até Sprint 7+ reconsideração

## Sprint 7+ Reconsideration Triggers

Reabrir esta decisão se:

1. VPS escalada para ≥16 CPU cores E memória ≥32GB (permite qwen2.5:7b sustentável Redator pós Steps 5-6)
2. Provision 3rd Ollama container dedicado Redator (ver ADR-025 Sprint 7+ Caminho C alternativa)
3. Migration para LLM API externa (Anthropic/OpenAI) — tier real volta a fazer sentido (claude-haiku/sonnet/opus map)
4. Eric directive negocia trade-off qualidade vs latência para tier="premium" reactivation

## References

- ADR-022 — Persona Redator Revisional (D1 tier configurável origem)
- ADR-023 — Sequential LLM Inference (F-PROD-NEW-18 capacity fix)
- ADR-025 — Redator Cascade Fallback Strategy (companion ADR — cascade depende de all-3b assumption desta ADR)
- Smith D-SMITH-S06-022 — F-S21-03 HIGH tier semantic abandoned
- Neo D-DEV-S06-023 — DeprecationWarning band-aid temporário (esta ADR formaliza pattern)
- TD-SP07-TIER-SEMANTIC-DECISION — tech debt rastreável agora RESOLVED via ADR-024

---

*Tier é intent. Modelo é reality. Audit chain registra ambos honestamente — e admite quando divergem. Honestidade arquitetural vence ilusão de configurabilidade.* — Aria, 2026-05-15
