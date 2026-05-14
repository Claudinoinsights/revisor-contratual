---
type: story
id: TD-SP06.1-LAYER-3-NLI-VALIDATOR
title: "Layer 3 NLI semantic validator citações Súmulas (ADR-022 D2 patch spec)"
status: Ready
priority: 2
sprint: "6.1 hotfix TD cleanup"
validated_by: "@po (Keymaker)"
validated_at: "2026-05-14"
validation_score: "10/10"
validation_verdict: "GO"
epic: "Sprint-6-Bloco-Gamma-Peca-Revisional-AI (post-launch hotfix)"
wave: "6.1.2 (serial pós-6.1.1 — depende QWEN-FALLBACK done para evitar conflitos redator.py)"
owner: "@dev (Neo)"
estimated_effort: "4h"
severity_origem: "MEDIUM (Smith F-γ-04 + ADR-022 D2 patch — Layer 3 anti-hallucination ausente em implementação)"
created: "2026-05-14"
created_by: "@sm (River)"
related_adrs:
  - "ADR-022 D2 patch Sprint 6.1 (3-camadas distinct table)"
  - "ADR-004 NLI híbrido pattern (TeseAdvogado precedent)"
related_findings:
  - "Smith F-γ-04 MEDIUM (review-bloco-gamma-pos-execution-2026-05-14)"
related_stories:
  - "TD-SP06.1-QWEN-FALLBACK-WIRING (Wave 6.1.1 — must be done first)"
  - "TD-SP06-REDATOR-LLM-01 (Bloco γ original — 2-camadas atual)"
depends_on:
  - "TD-SP06.1-QWEN-FALLBACK-WIRING (mesma file redator.py — evita conflitos merge)"
unblocks:
  - "Defense in depth 3-camadas anti-hallucination defendida em ADR-022 D2"
tags:
  - project/revisor-contratual
  - story
  - sprint-6-1
  - hotfix
  - anti-hallucination
  - nli
  - ready
---

# Story TD-SP06.1-LAYER-3-NLI-VALIDATOR — NLI semantic validator citações

## Story

**Como** advogado revisor confiando em hardening anti-hallucination 3-camadas (ADR-022 D2),
**Eu quero** que Redator valide semanticamente cada `citacao_textual` contra a ementa REAL da Súmula no vault (Layer 3 NLI),
**Para que** peça revisional não sustente interpretação INVERTIDA de Súmula (Súmula existe no vault — Layer 2 PASS — mas peça afirma o oposto do que ela diz).

---

## Contexto

Smith F-γ-04 MEDIUM identificou que ADR-022 D2 promete 3-camadas anti-hallucination mas implementação tem apenas 2 (Pydantic + vault ID). Aria patch D2 Sprint 6.1 clarificou:

- **Layer 1** Pydantic strict (`extra="forbid"` + `min_length` + regex) ✅ implementado
- **Layer 2** Vault-restricted citation IDs (`validar_citacoes_vault`) ✅ implementado — captura "Súmula 999 não existe no vault"
- **Layer 3** NLI semantic (`validar_citacoes_nli` SPEC) 🟡 esta story — captura "Súmula 539 existe mas peça afirma o oposto"

Reuso pattern ADR-004 NLI híbrido (cosine + BERT NLI) já em uso para TeseAdvogado.

---

## Acceptance Criteria

- **AC-01:** Schema `PecaRevisional` em `bloco_contratos/personas.py` pode precisar extension:
  - Adicionar field `fundamentos_invocados: list[FundamentoInvocado] | None = None` (opt-in retrocompat com Bloco γ original que tem apenas `citacoes_jurisprudencia: list[str]`)
  - FundamentoInvocado tem `id_doc + citacao_textual + peso_vinculacao + court_id` (reuso schema existente em bloco_contratos/personas.py linhas 22-30)
  - Atualizar prompt Redator para retornar `fundamentos_invocados` quando Layer 3 ativo
- **AC-02:** Nova function `validar_citacoes_nli` em `bloco_workflow/personas/redator.py`:
  ```python
  async def validar_citacoes_nli(
      peca: PecaRevisional,
      vault_docs: list[JurisprudenciaItem],
      *,
      nli_validator_fn: NLIValidatorFn | None = None,
  ) -> list[ValidacaoSemantica]:
      """Layer 3 — NLI híbrido cosine + BERT contra ementa vault."""
  ```
- **AC-03:** Para cada `fundamento.citacao_textual`, executar NLI híbrido contra `vault_doc.ementa` (vault_doc com id_doc match):
  - cosine similarity (sentence-transformers embedding)
  - BERT NLI (label: entailment | neutral | contradiction)
  - Retorna `ValidacaoSemantica` (schema já existente em `bloco_contratos/personas.py`)
- **AC-04:** Se algum `ValidacaoSemantica.nli_label == "contradiction"` → raise `PecaHallucinationError` com detail listando citações invertidas
- **AC-05:** Integração em `redator_invoke`:
  - Sequência Layer 1 (Pydantic via `model_validate_json`) → Layer 2 (`validar_citacoes_vault`) → Layer 3 (`validar_citacoes_nli`) opt-in via kwarg `enable_layer_3: bool = False` (Sprint 6.1 introduz como opt-in, Sprint 7+ pode default True após validação empírica)
- **AC-06:** Dependency injection `nli_validator_fn` para tests offline (sem load sentence-transformers + BERT NLI em CI)
- **AC-07:** 4 novos tests em `tests/unit/test_redator_persona.py`:
  - `test_layer_3_nli_passes_aligned_citation` (mock NLI retorna entailment)
  - `test_layer_3_nli_blocks_inverted_interpretation` (mock NLI retorna contradiction)
  - `test_layer_3_dep_injection_offline` (sem real sentence-transformers)
  - `test_layer_3_integration_full_chain` (Layer 1→2→3 sequência completa)
- **AC-08:** Pytest baseline 478 PASS maintained — target 482+ com 4 novos tests

---

## Tasks / Subtasks

- [ ] Task 1: Schema extension PecaRevisional (opt-in retrocompat)
  - [ ] 1.1 Adicionar `fundamentos_invocados: list[FundamentoInvocado] | None = None` field
  - [ ] 1.2 Validate FundamentoInvocado schema já existente (linhas 22-30 personas.py)
  - [ ] 1.3 Atualizar prompt Redator para incluir fundamentos_invocados quando Layer 3 enabled
- [ ] Task 2: validar_citacoes_nli function
  - [ ] 2.1 Type NLIValidatorFn (async callable signature)
  - [ ] 2.2 Function async implementation
  - [ ] 2.3 Itera fundamentos_invocados + lookup ementa vault por id_doc
  - [ ] 2.4 Chama nli_validator_fn(citacao_textual, ementa) → ValidacaoSemantica
  - [ ] 2.5 Detecta nli_label == "contradiction" → raises PecaHallucinationError
- [ ] Task 3: Integration em redator_invoke
  - [ ] 3.1 Novo kwarg `enable_layer_3: bool = False`
  - [ ] 3.2 Novo kwarg `nli_validator_fn: NLIValidatorFn | None = None`
  - [ ] 3.3 Pós validar_citacoes_vault, se enable_layer_3 → chamar validar_citacoes_nli
- [ ] Task 4: Unit tests (4 novos)
  - [ ] 4.1 test_layer_3_nli_passes_aligned_citation
  - [ ] 4.2 test_layer_3_nli_blocks_inverted_interpretation
  - [ ] 4.3 test_layer_3_dep_injection_offline
  - [ ] 4.4 test_layer_3_integration_full_chain
- [ ] Task 5: Pipeline integration kwargs forwarding
  - [ ] 5.1 pipeline.py adiciona `enable_layer_3_nli + nli_validator_fn` kwargs forwarding ao redator_invoke
- [ ] Task 6: Update File List + Change Log

---

## Dev Notes (Technical Context)

**Aria fix_approach:** Adicionar validar_citacoes_nli() em redator.py. Para cada fundamentos_invocados[].citacao_textual em PecaRevisional, executar NLI híbrido (cosine + BERT NLI) contra ementa real Súmula vault. Se label=='contradiction' raise PecaHallucinationError. Reuso pattern ADR-004 ValidacaoSemantica.

**Schema reuse (bloco_contratos/personas.py existente):**

```python
class FundamentoInvocado(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_doc: str = Field(...)
    citacao_textual: str = Field(..., min_length=10)
    peso_vinculacao: int = Field(..., ge=1, le=5)
    court_id: str = Field(...)

class ValidacaoSemantica(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_doc: str
    frase_tese: str
    ementa_real: str
    similarity_score: float
    nli_label: Literal["entailment", "neutral", "contradiction"]
    nli_confidence: float
    veredito: Literal["PASS", "FAIL_SIMILARITY", "FAIL_POLARITY"]
    razao: str
```

**Skeleton implementation:**

```python
# bloco_workflow/personas/redator.py
from typing import Awaitable, Callable
from bloco_contratos.personas import FundamentoInvocado, ValidacaoSemantica

NLIValidatorFn = Callable[[str, str], Awaitable[ValidacaoSemantica]]

async def validar_citacoes_nli(
    peca: PecaRevisional,
    vault_docs: list[JurisprudenciaItem],
    *,
    nli_validator_fn: NLIValidatorFn | None = None,
) -> list[ValidacaoSemantica]:
    """Layer 3 anti-hallucination — NLI semantic validation citações textuais.

    Para cada fundamento citado, NLI híbrido contra ementa real vault.
    Raises PecaHallucinationError se label=contradiction.
    """
    if peca.fundamentos_invocados is None:
        # Layer 3 opt-in — peças sem fundamentos_invocados schema (Bloco γ original) skipped
        return []

    if nli_validator_fn is None:
        # Default: real NLI híbrido (sentence-transformers + BERT)
        # Implementation Sprint 6.1: pode importar de bloco_workflow.nli.hybrid_validator
        raise NotImplementedError(
            "Sprint 6.1: default NLI validator não implementado; passe nli_validator_fn explicit."
        )

    validations: list[ValidacaoSemantica] = []
    vault_lookup = {d.id_doc: d for d in vault_docs}

    for fundamento in peca.fundamentos_invocados:
        vault_doc = vault_lookup.get(fundamento.id_doc)
        if vault_doc is None:
            # Layer 2 já capturaria — Layer 3 defensive
            continue
        validacao = await nli_validator_fn(fundamento.citacao_textual, vault_doc.ementa)
        validations.append(validacao)
        if validacao.nli_label == "contradiction":
            raise PecaHallucinationError(
                f"Layer 3 NLI bloqueou citação invertida: id_doc={fundamento.id_doc} "
                f"citacao='{fundamento.citacao_textual[:80]}...' "
                f"reason='{validacao.razao}'"
            )

    return validations
```

**Sprint 6.1 scope MVP:** real NLI híbrido (sentence-transformers + BERT) NÃO instalado em Sprint 6.1 — Neo cria interface + tests offline + default real implementation fica TD-SP07-NLI-HYBRID-REAL (Sprint 7+). Layer 3 fica opt-in até real validator implementado.

---

## Testing

```python
@pytest.mark.asyncio
async def test_layer_3_nli_blocks_inverted_interpretation():
    """F-γ-04 Sprint 6.1: NLI label=contradiction → PecaHallucinationError."""
    async def mock_nli_contradiction(citacao_textual, ementa):
        return ValidacaoSemantica(
            id_doc="STJ-S539",
            frase_tese=citacao_textual,
            ementa_real=ementa,
            similarity_score=0.85,
            nli_label="contradiction",
            nli_confidence=0.92,
            veredito="FAIL_POLARITY",
            razao="Citação afirma o oposto do que a Súmula 539 STJ diz",
        )

    peca_with_inverted_citation = PecaRevisional(
        # ... fields normais
        fundamentos_invocados=[FundamentoInvocado(
            id_doc="STJ-S539",
            citacao_textual="Súmula 539 PROÍBE capitalização de juros em qualquer hipótese",  # FALSO — S539 PERMITE com pactuação
            peso_vinculacao=3,
            court_id="STJ",
        )],
    )

    with pytest.raises(PecaHallucinationError, match="Layer 3 NLI bloqueou"):
        await validar_citacoes_nli(
            peca_with_inverted_citation,
            vault_docs=[mock_vault_doc_s539],
            nli_validator_fn=mock_nli_contradiction,
        )
```

---

## Dev Agent Record

**Agent Model Used:** (vazio)
**Debug Log References:** (vazio)
**Completion Notes List:** (vazio)
**File List:** (vazio)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-05-14 | @sm (River) | Draft Sprint 6.1 Wave 6.1.2 — Layer 3 NLI semantic validator spec ADR-022 D2 patch (Smith F-γ-04 + reuso ADR-004 pattern) |
