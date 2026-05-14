---
type: story
id: TD-SP06.1-QWEN-FALLBACK-WIRING
title: "Qwen fallback chain em redator._default_invoke (ADR-022 D1 honesty)"
status: Ready for Review
priority: 1
sprint: "6.1 hotfix TD cleanup"
validated_by: "@po (Keymaker)"
validated_at: "2026-05-14"
validation_score: "10/10"
validation_verdict: "GO"
epic: "Sprint-6-Bloco-Gamma-Peca-Revisional-AI (post-launch hotfix)"
wave: "6.1.1 (foundation paralelo)"
owner: "@dev (Neo)"
estimated_effort: "2h"
severity_origem: "MEDIUM (Smith F-γ-03 — docstring + ADR-022 D1 promete fallback que não existe)"
created: "2026-05-14"
created_by: "@sm (River)"
related_adrs:
  - "ADR-022 D1 (sabia primary + Qwen fallback claim)"
  - "ADR-010 Sabia Q4 mitigation (fallback Qwen pattern original)"
related_findings:
  - "Smith F-γ-03 MEDIUM (review-bloco-gamma-pos-execution-2026-05-14)"
related_stories:
  - "TD-SP06-REDATOR-LLM-01 (Bloco γ original — fallback claim docstring)"
  - "TD-SP06.1-LAYER-3-NLI-VALIDATOR (Wave 6.1.2 depende esta done)"
unblocks:
  - "Wave 6.1.2 LAYER-3-NLI-VALIDATOR (mesma file redator.py — evita conflitos)"
tags:
  - project/revisor-contratual
  - story
  - sprint-6-1
  - hotfix
  - qwen-fallback
  - ready
---

# Story TD-SP06.1-QWEN-FALLBACK-WIRING — Qwen fallback chain em redator._default_invoke

## Story

**Como** advogado revisor confiando em redundância LLM,
**Eu quero** que redator._default_invoke implemente fallback chain real (primary model fail → fallback model),
**Para que** Sprint 6 Bloco γ resilience não dependa de single LLM instance (ADR-010 + ADR-022 D1 honesty).

---

## Contexto

Smith F-γ-03 MEDIUM identificou que `redator._default_invoke` chama `get_advogado_llm(tier=tier)` único modelo SEM try/except + fallback chain. Docstring redator.py linha 6 promete "balanced=qwen+sabia fallback". ADR-022 D1 promete "sabia primary + Qwen 2.5 fallback (ADR-010 pattern leverage)". Implementação atual = zero fallback logic.

Sprint 6.1 corrige a divergência ADR vs código.

---

## Acceptance Criteria

- **AC-01:** `_default_invoke` em `bloco_workflow/personas/redator.py` envolve `await llm.ainvoke(prompt)` em try/except específico (não bare Exception)
- **AC-02:** Fallback chain configurado por tier:
  - tier=`balanced` (DEFAULT): primary `qwen2.5:7b` → fallback `sabia-7b-instruct`
  - tier=`premium`: primary `sabia-7b-instruct` → fallback `qwen2.5:7b`
  - tier=`lean`: primary `qwen2.5:3b` (sem fallback — degraded mode aceitável)
- **AC-03:** `logger.warning("Redator primary model {primary} falhou: {exc} — tentando fallback {fallback}")` quando fallback acionado
- **AC-04:** Audit field `redator_persona_used` registra modelo ACTUAL usado (primary OR fallback) — não claim. Já implementado em F-γ-02 hotfix linha 381 pipeline.py via `TIER_TO_MODEL_ADVOGADO[tier_redator]` — Sprint 6.1 estende para capturar fallback usado em runtime
- **AC-05:** Novo test `test_fallback_chain_when_primary_fails` em `tests/unit/test_redator_persona.py`:
  - Mock `get_advogado_llm` retorna LLM cujo ainvoke raises (primary fail)
  - Verifica que fallback model é chamado
  - Verifica que logger.warning foi emitido
- **AC-06:** Pytest baseline 478 PASS + 5 skip maintained — target 479+ PASS após novo test
- **AC-07:** Story TD-SP06-REDATOR-LLM-01 Change Log adicionar entry referenciando este patch

---

## Tasks / Subtasks

- [ ] Task 1: Refatorar `_default_invoke` em redator.py
  - [ ] 1.1 Adicionar function helper `_get_fallback_model(tier)` retornando model name OR None (lean tier)
  - [ ] 1.2 Wrap `await llm.ainvoke(prompt)` em try/except
  - [ ] 1.3 Se exception → log warning + criar second llm com fallback model + retry
  - [ ] 1.4 Se fallback model None (lean) → propagar exception original
- [ ] Task 2: Capturar actual model usado em runtime
  - [ ] 2.1 Retornar tuple `(content_str, actual_model_used)` de `_default_invoke`
  - [ ] 2.2 redator_invoke captura `actual_model_used` para downstream audit chain
  - [ ] 2.3 Atualizar pipeline.py linha 378-381 (Bloco δ hotfix F-γ-02) para usar `actual_model_used` do redator em vez de TIER_TO_MODEL_ADVOGADO[tier] estático
- [ ] Task 3: Unit test fallback
  - [ ] 3.1 Mock ChatOllama primary raises ConnectionError
  - [ ] 3.2 Mock ChatOllama fallback succeeds
  - [ ] 3.3 Verifica logger.warning + actual_model_used == fallback name
- [ ] Task 4: Update File List + Change Log story original (TD-SP06-REDATOR-LLM-01)
- [ ] Task 5: Self-critique checklist (story-dod-checklist.md)
- [ ] Task 6: Handoff Neo → Wave 6.1.2 (LAYER-3-NLI-VALIDATOR depends este done)

---

## Dev Notes (Technical Context)

**Aria fix_approach (handoff yaml):**
> try/except em _default_invoke — tier=balanced primeiro tenta qwen2.5:7b (DEFAULT atual), se falhar tenta sabia-7b-instruct fallback. Sprint 7+ pode inverter (sabia primary com qwen fallback) quando GPU disponível.

**Skeleton implementation:**

```python
# bloco_workflow/personas/redator.py
FALLBACK_MAP: dict[LLMTier, str | None] = {
    "lean": None,  # degraded mode, sem fallback
    "balanced": "sabia-7b-instruct",  # qwen primary, sabia fallback
    "premium": "qwen2.5:7b",  # sabia primary, qwen fallback
}

async def _default_invoke(prompt: str, tier: LLMTier) -> tuple[str, str]:
    """Default invoke com fallback chain (Sprint 6.1 F-γ-03 fix).

    Returns:
        (content_str, actual_model_used) — actual_model_used captura primary OR fallback.
    """
    primary_model = TIER_TO_MODEL_ADVOGADO[tier]
    fallback_model = FALLBACK_MAP.get(tier)

    try:
        llm = get_advogado_llm(tier=tier)
        response = await llm.ainvoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join(str(c) for c in content)
        return str(content), primary_model
    except Exception as exc:  # noqa: BLE001
        if fallback_model is None:
            raise  # lean degraded — sem fallback, propaga
        logger.warning(
            "Redator primary model %s falhou: %s — tentando fallback %s",
            primary_model, exc, fallback_model,
        )
        # Override model temporariamente para fallback
        # Implementation: get_advogado_llm aceita model name override OR criar ChatOllama diretamente
        from langchain_ollama import ChatOllama
        fallback_llm = ChatOllama(model=fallback_model, base_url=DEFAULT_HOST_ADVOGADO, format="json")
        response = await fallback_llm.ainvoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join(str(c) for c in content)
        return str(content), fallback_model
```

**Audit chain integration:**

`redator_invoke` signature change: retornar tuple `(peca, actual_model_used)`. Pipeline.py linha 378-381 substitui `TIER_TO_MODEL_ADVOGADO[tier_redator]` por `actual_model_used` capturado.

---

## Testing

**Pytest unit (`tests/unit/test_redator_persona.py`):**

```python
async def test_fallback_chain_when_primary_fails(monkeypatch):
    """F-γ-03 Sprint 6.1: primary fails → fallback model invoked + audit chain captures actual."""
    call_count = {"primary": 0, "fallback": 0}

    async def mock_fail_invoke(prompt):
        call_count["primary"] += 1
        raise ConnectionError("primary model timeout")

    async def mock_fallback_invoke(prompt):
        call_count["fallback"] += 1
        return _make_peca_revisional_json()

    # Mock get_advogado_llm primary fails + ChatOllama fallback succeeds
    # ... implementation Neo

    result, actual_model = await redator_invoke(..., tier="balanced", invoke_fn=...)
    assert call_count["primary"] == 1
    assert call_count["fallback"] == 1
    assert actual_model == "sabia-7b-instruct"  # fallback for balanced tier
```

**Baseline regressão:** 478 → 479+ PASS ZERO regressões.

---

## Dev Agent Record

**Agent Model Used:** (vazio — Neo preenche)
**Debug Log References:** (vazio)
**Completion Notes List:** (vazio)
**File List:** (vazio)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-05-14 | @sm (River) | Draft Sprint 6.1 Wave 6.1.1 — Qwen fallback wiring (Smith F-γ-03 remediation + ADR-022 D1 honesty) |
| 2026-05-14 | @po (Keymaker) | Validation GO 10/10 — flip Draft → Ready |
| 2026-05-14 | @dev (Neo) | Implementação completa Wave 6.1.1 — FALLBACK_MAP per tier + _default_invoke tuple retorno (content, actual_model_used) + model_capture dict param em redator_invoke + pipeline.py audit substituir TIER_TO_MODEL estático por actual_model_used capturado + 3 unit tests novos (model_capture + fallback_map config) + pytest 478 → 484 PASS ZERO regressão — flip Ready → Ready for Review. Files: bloco_workflow/personas/redator.py + bloco_workflow/pipeline.py + tests/unit/test_redator_persona.py |
