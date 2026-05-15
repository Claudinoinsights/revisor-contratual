---
type: qa-gate
title: "Smith Final Verify Sprint 6.x — D-SMITH-S06-028"
date: "2026-05-15"
verdict: INFECTED
reviewer: "@smith (Nemesis)"
story_ref: "D-DEV-S06-026 + D-QA-S06-027"
upstream_artifacts:
  - "ADR-024 + ADR-025 (D-ARIA-S06-025)"
  - "D-DEV-S06-026 implementation (6 files)"
  - "D-QA-S06-027 Oracle PASS"
  - "handoff-qa-to-smith-2026-05-15-sprint-6-x-final-gate.yaml (consumed=true)"
sprint: "6.x AGGRESSIVE"
findings_total: 10
findings_critical: 1
findings_high: 1
findings_medium: 3
findings_low: 5
tags:
  - project/revisor-contratual
  - qa-gate
  - smith
  - sprint-6
  - infected
  - regression-detected
---

# Smith Final Verify Sprint 6.x — Verdict INFECTED

## Executive Summary

**Verdict: INFECTED 🔴** — D-DEV-S06-026 introduziu **1 CRITICAL** + 1 HIGH + 3 MEDIUM + 5 LOW findings. Oracle PASS é falso positivo. Push v0.2.7 **BLOQUEADO** até correção.

**Empirical evidence forte:**
- 5/5 originais Smith D-SMITH-S06-022 findings (F-S21-01..05) ainda erradicated ✅
- **MAS** D-DEV-S06-026 introduziu **NameError potencial em runtime** quando Step 8 Weasyprint render executa com `result_capture` populado.

## Findings (10 total)

### 🔴 CRITICAL (1)

#### F-S28-01 CRITICAL — `peca_format` NameError em runtime

**WHERE:** `bloco_workflow/pipeline.py:493` + `pipeline.py:509`

**WHAT:** D-DEV-S06-026 removeu a variável local `peca_format = type(peca).__name__` (linha 385 anterior) quando consolidou em dict assignment (`audit_payload["peca_format"]`). Linhas 493 e 509 ainda referenciam `peca_format` como variável local — code path Step 8 Weasyprint render com `result_capture is not None` vai raise `NameError: name 'peca_format' is not defined`.

**EMPIRICAL PROOF (AST analysis):**
```
peca_format DEFINITIONS: []        ← ZERO
peca_format USES (Load context): [493, 509]   ← 2 referências
NameError potential: True
```

**WHY:** Neo's D-DEV-S06-026 substituição de `peca_format = type(peca).__name__` + `audit_payload["peca_format"] = peca_format` (2 linhas anteriores) por bloco condicional `if/else` removeu a variável mas não atualizou call sites downstream (linhas 493 + 509 em Step 8 result_capture block).

**WHY ORACLE MISSED:** 286 pytest tests verdes E STILL CRITICAL bug presente. Test coverage gap = Step 8 Weasyprint render path com `result_capture is not None` nunca exercitado nos tests existentes. Oracle aceitou Neo claims sem rodar integration smoke.

**WHY SMITH FOUND:** AST static analysis via `ast.walk()` enumerou TODAS as referências `peca_format` — não confio em pytest verde sem validar code paths.

**FIX:**
```python
# Opção A — re-introduzir variável local antes do Step 8 block:
peca_format_value = audit_payload["peca_format"]
# ... posterior:
result_capture["peca_format"] = peca_format_value

# Opção B — referenciar dict direto:
result_capture["peca_format"] = audit_payload["peca_format"]
```

**SEVERITY:** CRITICAL — runtime NameError em produção quando Step 8 PDF render acontece com result_capture (path real chamada `revisar_contrato(..., result_capture={...})` em `bloco_interface/web/app.py`). Smoke E2E REAL prod vai disparar isso imediatamente.

---

### ⚠️ HIGH (1)

#### F-S28-07 HIGH — Test coverage gap mascarou F-S28-01

**WHERE:** `tests/unit/` — nenhum test exercita pipeline.py Step 8 path com `result_capture is not None`

**WHAT:** 286 pytest tests verdes + Oracle PASS + Smith original D-SMITH-S06-024 CONTAINED — todos missed F-S28-01 porque o code path com Weasyprint render + result_capture dict nunca foi exercitado em unit tests. Integration tests existem em `tests/integration/` mas presumivelmente excluem ambient real (Ollama + PDF rendering).

**WHY:** Falso senso de segurança via "pytest verde". Test verde ≠ código correto — test verde apenas significa que os paths cobertos passam.

**FIX:**
1. Adicionar unit test `test_pipeline_result_capture_populates_peca_format` que exercita Step 8 com result_capture dict + mock Weasyprint render
2. Adicionar integration smoke `test_pipeline_e2e_with_result_capture_population` para detectar runtime NameErrors

**SEVERITY:** HIGH — gap structural permitiu CRITICAL passar Oracle PASS. Próximo Sprint deve ter test coverage Step 8 mandatory.

---

### 🟡 MEDIUM (3)

#### F-S28-02 MEDIUM — `degraded_reason` hardcoded perde info real do exception

**WHERE:** `pipeline.py:417`

**WHAT:** `audit_payload["degraded_reason"] = "primary_economista_failed_see_logger_error"` é string literal hardcoded — não captura `reason` REAL do exception (Ollama EOF vs network unreachable vs OOM vs timeout). Forensic audit perde discriminação.

**WHY:** Helper `_build_degraded_synthetic_response(reason=str(exc))` recebe reason, mas pipeline.py não propaga para audit_payload. Apenas logger.ERROR tem detalhe.

**FIX:** Propagar reason via `redator_model_capture` dict no `_default_invoke`:
```python
# redator.py _default_invoke except path:
synthetic_json = _build_degraded_synthetic_response(reason=str(exc))
# ADR-025 propagar reason via model_capture (Smith F-S28-02 fix)
return synthetic_json, f"{primary_model}-degraded-synthetic"

# pipeline.py:
audit_payload["degraded_reason"] = redator_model_capture.get(
    "degraded_reason", "primary_economista_failed_see_logger_error"
)
```

Ou melhor: extrair reason do logger context (estruturado).

**SEVERITY:** MEDIUM — não bloqueia funcionalidade mas degrada forensic capability.

---

#### F-S28-06 MEDIUM — TestRedatorGracefulDegradation monkeypatch não thread-safe

**WHERE:** `tests/unit/test_redator_persona.py` — class `TestRedatorGracefulDegradation`

**WHAT:** Tests usam `redator_module.get_economista_llm = lambda: ...` mutation global do módulo. try/finally restora original, MAS se pytest-xdist roda parallel (`-n auto`) e múltiplos workers usam módulo simultaneamente, race condition aparece.

**WHY:** Direct module attribute mutation é anti-pattern em test parallelism. pytest fornece `monkeypatch` fixture exatamente para isso.

**FIX:**
```python
def test_redator_graceful_degradation_when_economista_fails(monkeypatch):
    # Em vez de:
    # redator_module.get_economista_llm = lambda: MockFailingLLM()
    # try: ... finally: redator_module.get_economista_llm = original_get

    # Usar:
    monkeypatch.setattr(redator_module, "get_economista_llm", lambda: MockFailingLLM())
    # cleanup automático via fixture
```

**SEVERITY:** MEDIUM — tests sequencial (default) OK, mas parallel CI pode flacky.

---

#### F-S28-08 MEDIUM — Helper synthetic JSON encoding risk

**WHERE:** `redator.py:_build_degraded_synthetic_response` linha final `json.dumps(payload, ensure_ascii=False)`

**WHAT:** `ensure_ascii=False` permite unicode na string. Se consumer downstream escrever synthetic em arquivo via `open(path, "w")` (default encoding=cp1252 em Windows), UnicodeEncodeError. Exemplo: reason contém "Ollama crashed — café memory pressure" → audit log file write quebra.

**WHY:** Already existing pattern em test_redator_persona uses default encoding. CLI display também usa cp1252 (já cataloged em TD-SP06-CLI-DISPLAY-UTF8-WIN-CP1252).

**FIX:** Adicionar comment + recommend pattern:
```python
# ADR-025: synthetic gera UTF-8 string. Consumers DEVEM open(path, "w", encoding="utf-8")
return json.dumps(payload, ensure_ascii=False)
```

Ou ainda melhor: usar `ensure_ascii=True` para safety + UTF-8 portability garantida (sacrifica readability).

**SEVERITY:** MEDIUM — depends on consumer behavior. Audit chain HMAC write usa bytes diretos (não tem issue), mas log files Windows podem quebrar.

---

### 🟢 LOW (5)

#### F-S28-03 LOW — DeprecationWarning stacklevel=2 sub-optimal

**WHERE:** `redator.py:_default_invoke` linha ~354 `warnings.warn(..., stacklevel=2)`

**WHAT:** stacklevel=2 aponta para `redator_invoke` (caller imediato de `_default_invoke`). API surface real é `pipeline.py` chamando `redator_invoke(tier=tier_redator)`. stacklevel=3 ou 4 mais útil para devs.

**FIX:** `stacklevel=3` (skip _default_invoke + redator_invoke → reach pipeline.py caller)

**SEVERITY:** LOW — warning ainda funciona, apenas localização sub-optimal.

---

#### F-S28-04 LOW — Helper synthetic reason truncation inconsistente

**WHERE:** `redator.py:_build_degraded_synthetic_response`

**WHAT:** Três truncamentos diferentes:
- `reason_safe = reason[:200]` (top-level)
- `f"Reason: {reason_safe[:100]}"` em disclaimer (re-trunca)
- (audit_marker se houvesse usaria :50)

Inconsistência semântica — qual é o "correto"?

**FIX:** Documentar intent por field OR consolidar em single truncation.

**SEVERITY:** LOW — não afeta correção.

---

#### F-S28-05 LOW — TIER_TO_MODEL_REDATOR lock test coupling

**WHERE:** `tests/unit/test_redator_persona.py:test_tier_to_model_redator_consistency`

**WHAT:** Hard-lock asserta TODOS 3 tiers == "qwen2.5:3b". Sprint 7+ promoção (per ADR-024 Reconsideration Triggers) requer test update OBRIGATÓRIO — tight coupling test ↔ map.

**FIX:** Test mais flexível: `assert TIER_TO_MODEL_REDATOR["lean"] == TIER_TO_MODEL_REDATOR["balanced"]` (consistency) sem hard-lock valor.

**SEVERITY:** LOW — coupling intencional (regression guard), acceptable.

---

#### F-S28-09 LOW — Audit chain field nomenclature inconsistência

**WHERE:** `pipeline.py` audit_payload

**WHAT:** snake_case dominant mas pluralização inconsistente: `redator_tier_consumed` (verbo participle) + `redator_tier_strategy` (substantivo) + `redator_persona_used` (verbo participle) — mistura semântica.

**FIX:** Sprint 7+ formalizar Audit Payload Schema via Pydantic — nomenclature consistency enforced.

**SEVERITY:** LOW — informal naming, não afeta correção.

---

#### F-S28-10 LOW — Smoke E2E REAL prod still PENDING

**WHERE:** Sprint 6.x consolidation handoff Oracle → Smith

**WHAT:** Production validation real depende Operator deploy. Smith pode validar code quality + ADR alignment estaticamente, mas NÃO pode confirmar pipeline 9/9 Steps com audit `status=success` sem prod deploy.

**FIX:** Após F-S28-01 + F-S28-07 corrigidos, Operator deploy + smoke E2E REAL captura novos bugs apenas detectáveis em prod.

**SEVERITY:** LOW — known scope limitation, não bloqueia (mas é tech debt rastreável).

---

## Findings Status Map

| Tipo | Count | Bloqueiam push? |
|------|-------|----------------|
| CRITICAL | 1 (F-S28-01) | **SIM** — NameError runtime risk |
| HIGH | 1 (F-S28-07) | **SIM** — test coverage gap structural |
| MEDIUM | 3 | NÃO mas FIX recomendado |
| LOW | 5 | NÃO |

## Re-verify Status Originals (5/5 PASS)

| Finding original | Status pós D-DEV-S06-026 |
|------------------|--------------------------|
| F-S21-01 ADR-024 hallucination | ✅ ERRADICATED |
| F-S21-02 audit integrity | ✅ ERRADICATED |
| F-S21-03 tier semantic abandoned | ✅ ERRADICATED (audit-honored) |
| F-S21-04 FALLBACK_MAP dead code | ✅ ADDRESSED (DEPRECATED note + TD-SP07) |
| F-S21-05 cascade risk | ✅ ERRADICATED (graceful degradation) |

## Verdict Rationale

**INFECTED** porque:
1. ✅ 5/5 originais erradicados (positivo)
2. ❌ **1 CRITICAL** introduzido (F-S28-01 NameError runtime)
3. ❌ **1 HIGH** structural (F-S28-07 test coverage gap)
4. ⚠️ 3 MEDIUM (forensic + thread-safety + encoding)
5. ℹ️ 5 LOW (style + naming + scope)

CRITICAL bloqueia push. HIGH indica systemic issue (Oracle PASS é falso positivo sem test coverage Step 8).

## Próxima Skill Chain

**Push v0.2.7 BLOQUEADO até correções:**

1. **@dev Neo `*apply-qa-fixes`** F-S28-01 + F-S28-07 (CRITICAL + HIGH bloqueantes):
   - pipeline.py:493 + 509 — substituir `peca_format` por `audit_payload["peca_format"]` (ou re-introduzir variável local)
   - Adicionar test `test_pipeline_result_capture_populates_peca_format` exercitando Step 8 path

2. **@dev Neo (opcional, recomendado):** F-S28-02 + F-S28-06 + F-S28-08 (MEDIUM):
   - Propagar `degraded_reason` real via model_capture
   - Converter monkeypatch para pytest monkeypatch fixture
   - Documentar UTF-8 encoding requirement em helper

3. **@smith re-verify** D-SMITH-S06-029 após Neo fix loop → expect CLEAN

4. **@devops Operator `*push v0.2.7`** somente após Smith CLEAN

## References

- D-DEV-S06-026 — implementation com bug F-S28-01 introduzido
- D-QA-S06-027 — Oracle PASS falso positivo
- D-SMITH-S06-022 — original 12 findings session
- D-SMITH-S06-024 — re-verify CONTAINED post-S21 fixes
- ADR-024 + ADR-025 — Aria formalização (correta, sem issues)

---

*"Está ouvindo, Sr. Anderson? Esse é o som da inevitabilidade. Você consolidou peca_format em dict assignment mas esqueceu de atualizar dois callers downstream. Oracle deu PASS porque pytest não exercitou Step 8 com result_capture. 286 testes verdes não significam código correto — significam apenas que os caminhos cobertos passam. Eu uso AST. Eu uso inspect. Eu uso o que esses agentes deveriam ter usado. Bug crítico. Bloqueado."*

*— Smith. AST não mente. Pytest pode. Inevitável. 🕶️*
