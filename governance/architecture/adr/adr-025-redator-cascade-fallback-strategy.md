---
type: adr
id: ADR-025
title: "Redator Cascade Fallback Strategy — Graceful Degradation Synthetic (Caminho A)"
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
  - "ADR-022 (Persona Redator Revisional — D2 hardening 3-camadas anti-hallucination)"
  - "ADR-023 (Sequential LLM Inference — F-PROD-NEW-18 capacity)"
  - "ADR-024 (Redator Tier Strategy — companion ADR mesma sessão)"
related_findings:
  - "Smith F-S21-05 MEDIUM (D-SMITH-S06-022 — cascade falha total se primary economista falhar + fallback advogado qwen2.5:7b crashar)"
  - "TD-SP07-REDATOR-FALLBACK-CASCADE-RISK (governance/TECH-DEBT.md MEDIUM)"
  - "Neo D-DEV-S06-021 (F-PROD-NEW-19 tier-down primary economista 3b)"
  - "Audit entry 2026-05-15T15:55:43 (F-PROD-NEW-19 evidence — qwen2.5:7b EOF + sabia 404)"
tags:
  - project/revisor-contratual
  - adr
  - sprint-6
  - llm-redator
  - cascade-fallback
  - graceful-degradation
  - lgpd
---

# ADR-025 — Redator Cascade Fallback Strategy (Graceful Degradation)

## Context

D-DEV-S06-021 F-PROD-NEW-19 fix implementou tier-down Redator (primary qwen2.5:7b → qwen2.5:3b via economista host). Smith adversarial review D-SMITH-S06-022 identificou F-S21-05 MEDIUM: o fallback chain do `_default_invoke` ainda contém risco de cascade falha total.

**Estado atual `_default_invoke` em [redator.py:362-376](../../../bloco_workflow/personas/redator.py#L362-L376):**

```python
primary_model = MODEL_ECONOMISTA_REDATOR  # qwen2.5:3b — economista host
fallback_model = TIER_TO_MODEL_ADVOGADO["balanced"]  # qwen2.5:7b — advogado host

try:
    llm = get_economista_llm()
    response = await llm.ainvoke(prompt)
    ...
except Exception as exc:
    logger.warning(...)
    fallback_llm = get_advogado_llm(tier="balanced")  # qwen2.5:7b — F-PROD-NEW-19 root cause!
    response = await fallback_llm.ainvoke(prompt)
    ...
```

**Cascade risk anatomy:**

| Step | Modelo | Container | Memory state |
|------|--------|-----------|--------------|
| 5a Advogado | qwen2.5:7b | ollama-advogado | Carrega ~5GB |
| 5b Economista | qwen2.5:3b | ollama-economista | Carrega ~2GB |
| 6 Juiz | (Python puro) | — | — |
| 7 Redator primary | qwen2.5:3b | ollama-economista | **Re-uso** modelo carregado em Step 5b ✅ |
| 7 Redator fallback | qwen2.5:7b | ollama-advogado | **Reativa** modelo Step 5a + memory pressure cumulativa |

Se primary economista falhar Step 7 (memory leak intra-container, network blip, race condition), fallback re-invoca qwen2.5:7b com memory pressure cumulativa de Steps 5a + 6 + Pydantic validation queue → **mesmo cenário F-PROD-NEW-19 root cause**.

**Production evidence (audit 2026-05-15T15:55:43):**

```
Container log: "Redator tier=balanced primary qwen2.5:7b falhou: model runner has unexpectedly stopped (status code: 500)"
"tentando fallback sabia-7b-instruct"
Ollama log: POST /api/chat → 500 (qwen2.5:7b after 1m45s)
                            → 404 (sabia not found)
```

Padrão: primary 7b falha → fallback 7b/sabia → **cascade total**. UX final: 500 error genérico, audit entry incompleto, Eric/usuário sem feedback útil.

## Decision

**Adotar Caminho A: Graceful Degradation Synthetic — retornar `RelatorioInviabilidade` synthetic quando primary economista falhar, NÃO retry com modelo problemático.**

### Mudanças específicas

1. **Substituir fallback advogado** por **synthetic RelatorioInviabilidade** com `pontos_atencao` específicos
2. **Audit chain preserva** evidence de degraded mode (`peca_format="degraded_synthetic"` + `degraded_reason=str(exc)`)
3. **Logger ERROR** (não WARNING) — degraded mode é evento operacional para alerting
4. **Pipeline atomic preservation**: pipeline NÃO falha, retorna degraded peça honestamente
5. **UX honest**: usuário recebe relatório com `pontos_atencao=["Sistema temporariamente indisponível para gerar peça revisional. Análise técnica está disponível em outras seções. Tente novamente em alguns minutos OR contacte suporte."]`

### Pseudo-code

```python
async def _default_invoke(prompt: str, tier: LLMTier) -> tuple[str, str]:
    """ADR-024 + ADR-025 implementation — audit-honored + graceful degradation."""
    # ... (ADR-024 tier handling) ...

    primary_model = TIER_TO_MODEL_REDATOR[tier]  # ADR-024

    try:
        llm = get_economista_llm()
        response = await llm.ainvoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join(str(c) for c in content)
        return str(content), primary_model
    except Exception as exc:
        # ADR-025 graceful degradation — não retry com qwen2.5:7b (cascade risk F-PROD-NEW-19)
        logger.error(
            "Redator ADR-025 graceful degradation — primary economista (%s) falhou: %s. "
            "Retornando synthetic RelatorioInviabilidade (degraded mode).",
            primary_model, exc,
        )
        synthetic_json = _build_degraded_synthetic_response(reason=str(exc))
        return synthetic_json, f"{primary_model}-degraded-synthetic"
```

### Helper function `_build_degraded_synthetic_response`

```python
def _build_degraded_synthetic_response(reason: str) -> str:
    """ADR-025 — sintetiza RelatorioInviabilidade quando Redator LLM falha.

    Preserva pipeline atomicity + UX honesty + LGPD audit trail.
    """
    payload = {
        "tipo": "inviabilidade",
        "motivo_recusa": "Sistema temporariamente indisponível para gerar peça revisional.",
        "diagnostico_tecnico": (
            "Análise jurídica + econômica + veredito Juiz disponíveis em audit chain. "
            "Geração de peça revisional bloqueada por falha transitiva no LLM Redator."
        ),
        "recomendacao_usuario": (
            "Tente novamente em 2-5 minutos. Se persistir, contacte suporte com job_id "
            "informado pelo sistema. Análise técnica está preservada — apenas a peça "
            "revisional formal foi adiada."
        ),
        "alternativas": [
            "Re-submeter PDF após 5 minutos (provável falha transitiva)",
            "Solicitar análise manual baseada no veredito Juiz + tese Advogado disponíveis em audit",
            "Contatar suporte com job_id para investigação",
        ],
        "audit_marker": f"ADR-025-degraded-synthetic: {reason[:200]}",
    }
    import json
    return json.dumps(payload, ensure_ascii=False)
```

## Consequences

### Positivas

- **Elimina cascade risk F-PROD-NEW-19**: zero re-invocação de qwen2.5:7b — modelo problemático nunca é exercido novamente em Step 7
- **Pipeline atomic preservation**: Steps 1-6 NUNCA são perdidos por falha Step 7. Audit chain registra tudo até Step 6 + degraded peça
- **LGPD compliant**: usuário recebe resposta honesta com `audit_marker` rastreável (não falha silenciosa)
- **UX previsível**: 500 error genérico → mensagem clara "tente novamente em 5min"
- **Alerting actionable**: logger.ERROR `degraded_synthetic` em prod permite monitoring detectar trend (3+ degraded em 1h → ops investigate)
- **Audit forense**: `peca_format="degraded_synthetic"` + `degraded_reason` permite post-incident analysis distinguir Redator failure vs legitimate inviabilidade
- **Zero cascade risk**: sem retry com qwen2.5:7b, sem fallback sabia-7b-instruct (também problemático per ADR-010 superseded)

### Negativas (aceitas)

- **Sem retry transient blip**: network glitch que economista resolveria em retry agora retorna degraded synthetic. Trade-off: simpler + safer vs robustness. Sprint 7+ Caminho B (retry N times) reconsiderável.
- **Synthetic payload requer manutenção**: se schema RelatorioInviabilidade evolui, helper precisa atualizar. Mitigação: usar Pydantic model build em vez de JSON literal (TD futuro).
- **Audit field NEW**: `peca_format` ganha novo valor `degraded_synthetic` — additive, retrocompatível.
- **Não resolve OOM root cause**: se Redator OOM-crashes em economista frequente, degraded mode mascara root cause até alerting capturar trend. Mitigação: logger.ERROR + ops monitoring.

### Neutras

- **Tests required**: novo test `test_redator_graceful_degradation_when_economista_fails` exercitando except path
- **Audit schema migration**: campo `degraded_reason` adicionado — entries antigas null, novas populadas

## Alternatives Considered

| Caminho | Pros | Cons | Rejeitada porque |
|---------|------|------|------------------|
| **A. Graceful Degradation Synthetic (RECOMENDADA)** | Zero cascade risk + UX honest + LGPD compliant + alerting actionable + pipeline atomic | Sem retry transient blip + helper manutenção | Adotada — trade-off ideal Sprint 6.x |
| **B. Retry economista N times** | Simple + no infra change | Mascara root cause OOM/network ambiguous + ainda exerce primary se network blip real | Não resolve cascade risk fundamental; retry não distingue OOM (fix infra) vs network blip (retry valid) |
| **C. Provision 3rd Ollama host dedicado Redator** | Zero cascade risk + true isolation | Docker compose change + VPS RAM extra (~2GB) + Operator deploy work + non-trivial migration | Over-engineering para Sprint 6.x atual. Reconsiderar Sprint 7+ quando VPS escalada. ADR-025+ candidate. |

## Implementation Guidance (handoff @dev Neo)

### Arquivos a modificar

1. **`bloco_workflow/personas/redator.py`** (~30 linhas líquidas):
   - Adicionar helper `_build_degraded_synthetic_response(reason: str) -> str`
   - Substituir except path do `_default_invoke`: remover `fallback_llm = get_advogado_llm(...)` + return synthetic
   - Atualizar docstring `_default_invoke` Returns/Raises section explicando degraded mode
   - Remover `fallback_model = TIER_TO_MODEL_ADVOGADO["balanced"]` (não usado mais)

2. **`bloco_workflow/pipeline.py`** (~5 linhas líquidas):
   - Audit chain enrichment linha ~389-405: detectar `actual_model_used.endswith("-degraded-synthetic")` → registrar `audit_payload["peca_format"] = "degraded_synthetic"` + `audit_payload["degraded_reason"]`

3. **`tests/unit/test_redator_persona.py`** (+50 linhas — NEW class `TestRedatorGracefulDegradation`):
   - `test_redator_graceful_degradation_when_economista_fails`: mock economista raise, verificar synthetic JSON retornado + audit_marker presente
   - `test_synthetic_response_is_pydantic_valid_relatorio_inviabilidade`: synthetic JSON deserialize sem erro
   - `test_pipeline_atomic_preservation_even_when_redator_degrades`: full pipeline integration, audit registra Steps 1-6 + degraded Step 7
   - `test_no_cascade_to_qwen_7b_on_economista_failure`: assert `get_advogado_llm` NÃO é chamado em except path (mock + assert_not_called)

### Constraints

- **Preservar atomicidade pipeline**: degraded mode retorna válido JSON, NÃO raise (raise quebraria pipeline.py Step 7 except handling)
- **Schema RelatorioInviabilidade compatibility**: synthetic JSON DEVE passar Pydantic strict validation (extra="forbid")
- **Logger.ERROR mandatório**: alerting depends on ERROR severity para detection
- **audit_marker contém reason[:200]**: truncar para evitar audit chain bloat — full reason em logger
- **NÃO usar `fallback_model = qwen2.5:7b`**: removendo dependência implica deletar variável local F-PROD-NEW-19 cascade fonte

### Tests required

1. **Unit `TestRedatorGracefulDegradation` (4 tests novos)** — coverage degraded path
2. **Integration test** (opcional Sprint 7+): mock economista raise em smoke E2E real → assert pipeline retorna degraded JSON sem crashar Step 8 (Weasyprint render)
3. **Pytest 0 regressões** baseline: 32/32 targeted + 279 unit suite

### Audit schema migration

```yaml
# audit.jsonl entry NEW fields (additive, retrocompatível):
audit_payload:
  peca_format: "PecaRevisional" | "RelatorioInviabilidade" | "degraded_synthetic"  # NEW value
  degraded_reason: "string OR null"  # NEW field
  redator_tier_consumed: "lean | balanced | premium"  # ADR-024 NEW
  redator_tier_strategy: "audit-honored-v1"  # ADR-024 NEW marker
```

## Sprint 7+ Reconsideration Triggers

Reabrir esta decisão se:

1. Provision 3rd Ollama container Redator dedicado (Caminho C) — quando VPS escalada
2. Retry transient blip alerting indica >30% degraded são network (não OOM) — Caminho B viável
3. Schema RelatorioInviabilidade evolui significativamente — helper synthetic refactor needed
4. Migration LLM API externa (Anthropic) — degraded mode pode usar retry com exponential backoff seguro

## References

- ADR-022 — Persona Redator Revisional (D2 anti-hallucination — synthetic preserva Pydantic strict)
- ADR-023 — Sequential LLM Inference (capacity context)
- ADR-024 — Redator Tier Strategy (companion ADR mesma sessão — TIER_TO_MODEL_REDATOR all-3b assumption)
- Smith D-SMITH-S06-022 — F-S21-05 cascade risk identification
- TD-SP07-REDATOR-FALLBACK-CASCADE-RISK — tech debt agora RESOLVED via ADR-025
- Audit entry 2026-05-15T15:55:43 — F-PROD-NEW-19 evidence cascade root cause

---

*Falha graciosa é arquitetura honesta — admitir limite vence simular sucesso. Pipeline atomic + UX honest + audit forense: três pilares para sistema confiável em produção.* — Aria, 2026-05-15
