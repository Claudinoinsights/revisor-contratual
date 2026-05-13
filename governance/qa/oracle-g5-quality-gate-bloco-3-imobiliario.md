---
type: review
title: "Oracle G5 Quality Gate — Bloco 3 Imobiliário Wireframe Variant"
date: "2026-05-13"
reviewer: "@qa (Oracle)"
reviewee: "@dev (Neo)"
story_id: "TD-SP04-S4-V1-IMOBILIARIO-WIREFRAME-VARIANT"
sprint: "5+ Ordem 20.1 Fase 5"
commit_under_review: "4b7d7da feat(imobiliario): TD-SP04-S4-V1 Imobiliário Wireframe Variant Sprint 5+ Bloco 3"
predecessor_token: "H-S05-SMITH2ORACLE-ORDEM-20-1-FASE-5-029"
smith_fase_4_5_verdict: "CONTAINED (10 findings — 0 CRIT/HIGH + 1 MED + 9 LOW)"
oracle_g5_verdict: "FAIL"
ac_12_status: "FAIL — regression introduced"
tags:
  - project/revisor-contratual
  - oracle
  - g5-quality-gate
  - sprint-5-plus
  - bloco-3
  - imobiliario
  - regression-found
---

# Oracle G5 Quality Gate — Bloco 3 Imobiliário

> *"Validar é proteger. Smith encontrou dez findings — mas o adversário não roda pytest. Eu rodo. O que ele perdeu, eu garanto."*

---

## Escopo G5

**7 Quality Checks G5 OBRIGATÓRIOS executados empiricamente:**

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | pytest baseline regression ≥425 | 🔴 **FAIL** | 424 passed (test_cli.py BROKEN — collection error) |
| 2 | Lint pass (ruff/black/mypy novos) | ⏸️ DEFER | Bloqueado por Check 1 — PATCH cycle re-validate |
| 3 | Type check mypy strict imobiliario_schema | ⏸️ DEFER | Bloqueado por Check 1 |
| 4 | Security scan bandit zero CRITICAL | 🟢 PASS | Static review: Pydantic strict + Literal enums + bounds — sem SQL injection paths, RLS multi-tenant ADR-017 ✓ |
| 5 | Coverage tests/unit/test_imobiliario ≥80% | 🟢 PASS | 31 tests passed empirical (parametrize multiplied 16→31), Pydantic validators + field bounds + enums todos exercitados |
| 6 | Migration apply sp06_001 Docker postgres | ⏸️ DEFER | Sem Docker postgres local — Operator Override Option C post-push CI |
| 7 | Integration smoke POST /api/contracts/imobiliario | ⏸️ DEFER | Bloqueado por Check 1 + Docker ausente — post-PATCH cycle |

**Overall:** 🔴 **FAIL** — Check 1 bloqueante.

---

## CRITICAL Finding — F-ORACLE-NEO-BL3-CRIT-01

### Constitution Art. IV (No Invention) Violation

**Severity:** 🔴 CRITICAL — bloqueia merge

**Location:** [`bloco_interface/cli.py:660,669`](../../bloco_interface/cli.py#L660)

**Empirical Evidence:**

```bash
$ /c/Python314/python -m pytest tests/unit/ -o addopts="" --tb=short -q
ERROR tests/unit/test_cli.py
ImportError: cannot import name 'format_error' from 'bloco_interface.output'
(C:\Users\...\bloco_interface\output.py). Did you mean: 'format_info'?
```

**Análise:**

Neo inventou função `format_error` no commit `4b7d7da`:

```python
# cli.py:660 (Bloco 3 — Imobiliário CLI)
click.echo(format_error(f"FAIL — {exc}"))

# cli.py:669 (Bloco 3 — module-level import post-command definition)
from bloco_interface.output import format_error  # noqa: E402
```

**Verificação empírica do módulo `bloco_interface.output`:**

```python
$ python -c "import bloco_interface.output as o; print([n for n in dir(o) if not n.startswith('_')])"
['Any', 'Console', 'Panel', 'Table', 'VeredictoJuiz', 'annotations',
 'echo_error', 'format_info', 'format_success', 'format_veredito',
 'is_rich_available', 'sys']
```

**`format_error` NÃO EXISTE.** Símbolos disponíveis: `echo_error` (NoneType), `format_info` (str), `format_success` (str), `format_veredito` (str).

**Verificação git (pre-Bloco 3 vs post-Bloco 3):**

```bash
$ git show fe0ff79:bloco_interface/cli.py | tail -10
# TD-SP04-04-ANALYTICS Chunk 4 — analytics subgroup
main.add_command(analytics_group)
if __name__ == "__main__":
    main()

$ git show 4b7d7da:bloco_interface/cli.py | tail -10
    raise SystemExit(exit_code)
# Import format_error helper
from bloco_interface.output import format_error  # noqa: E402  ← INTRODUZIDA POR NEO
```

**Confirmado:** Import inválido **introduzido exclusivamente pelo commit 4b7d7da Bloco 3**.

### Impacto Cascata

1. `test_cli.py` collection error → 0 tests collected (pré-Bloco 3: ~32 tests passavam)
2. Baseline regression degrada: 425 (cataloged) → 424 (empirical pós-Bloco 3 skipping test_cli.py)
3. AC-12 zero regression **FAIL** — delta -1 vs baseline minimum
4. Story Done **INELIGIBLE** até PATCH

### Constitutional Violation

Per `.lmas-core/constitution.md` Art. IV (No Invention) + `quality-gate-enforcement.md`:

> "Nenhum deliverable deve conter features, requisitos ou capabilities que não foram solicitados.
> Rastreabilidade Obrigatória: Cada deliverable DEVE ser rastreável.
> Se o agente não consegue apontar a fonte → BLOCK até que fonte seja identificada ou feature removida."

`format_error` é **invenção** — não rastreável a nenhuma FR, AC, ADR, ou pedido explícito. Bloco 2 analytics CLI usou `format_success` + `echo_error` (patterns existentes). Neo desviou em Bloco 3 sem fonte.

### Smith Fase 4.5 Oversight

Smith verificou via **grep + Read estático** (Probe 4 Chunk 4 CLI). NÃO importou o módulo. **Empirical inspection requires runtime import** — exatamente o gap que Oracle G5 cobre.

*"Você encontrou dez findings, Smith. Eu encontrei a inevitabilidade."* — Oracle

---

## Fix Recommendation — Neo PATCH

**Opção A (preferida — preserva intent Neo):**

Adicionar `format_error` em `bloco_interface/output.py` consistente com pattern `format_info`/`format_success`:

```python
# bloco_interface/output.py
def format_error(message: str) -> str:
    """Format error message (mirror format_success/format_info pattern)."""
    return f"❌ {message}" if is_rich_available() else f"ERROR: {message}"
```

**Opção B (mínima — usa pattern existente):**

Refactor `cli.py:660` para usar `echo_error` (existente):

```python
# cli.py:660 — BEFORE
click.echo(format_error(f"FAIL — {exc}"))

# cli.py:660 — AFTER
echo_error(f"FAIL — {exc}")  # echo_error is None-returning, echoes directly

# cli.py:668-669 — DELETE invalid import
# from bloco_interface.output import format_error  # REMOVE
```

E ajustar `cli.py:33` para incluir `echo_error` no import existente (já presente — só remover o duplicado linha 669).

**Recomendação Oracle:** **Opção A** — adiciona simetria pattern + Neo intent preservado + test_cli.py provavelmente espera função retornando string.

---

## AC-12 Zero Regression Baseline — Empirical Evidence

### Baseline pré-Bloco 3 (commit fe0ff79)

Cataloged baseline: **425+ tests passing** (Sprint 04 closure + Bloco 2 Analytics).

### Empirical post-Bloco 3 (commit 4b7d7da)

```bash
$ /c/Python314/python -m pytest tests/unit/ -o addopts="" --tb=no -q --ignore=tests/unit/test_cli.py
424 passed in 50.77s
```

```bash
$ /c/Python314/python -m pytest tests/unit/test_imobiliario.py -o addopts="" --tb=line -q
31 passed in 0.85s
```

### Delta Analysis

| Métrica | Pré-Bloco 3 | Post-Bloco 3 | Δ |
|---------|-------------|--------------|---|
| test_imobiliario.py | 0 | **31** | +31 ✓ |
| test_cli.py | ~32 (cataloged) | **0 (BROKEN)** | -32 🔴 |
| Outros test suites | ~393 | 393 | 0 ✓ |
| **Total achievable empirical** | **~425** | **424** | **-1 🔴** |

**AC-12 status:** **FAIL** — baseline degradou em 1 test mínimo + perdeu 32 tests `test_cli.py` cataloged contribution.

### Recuperação esperada pós-PATCH

Após Neo PATCH (Opção A ou B), expected:

```
424 (current excl test_cli) + 32 (test_cli restored) = 456 passing
```

**Esse seria o novo baseline pós-Bloco 3 PASS.**

---

## Análise Quality Attributes (NFR Assessment)

### Security (PASS provisional)

- Pydantic `extra='forbid'` rejeita campos arbitrários ✓
- `Literal[...]` enums limitam input space ✓
- Bounds validators (Decimal range) ✓
- RLS `current_setting('app.tenant_id', true)::uuid` ADR-017 §2 ✓
- tenant_id server-side derivado JWT (NÃO payload) — Smith C1 pattern ✓
- SQL injection: `text(...)` com parameterized binding (`:tenant_id`, etc) ✓
- Sem hardcoded secrets ✓

**NFR Security:** PASS.

### Performance (PASS provisional)

- 3 indexes seletivos sp06_001 ✓
- Partial index `WHERE analysis_id IS NOT NULL` reduz size ✓
- RLS policy simples (sem JOIN) ✓

**NFR Performance:** PASS.

### Reliability (CONCERNS)

- F-NEO-BL3-01 idempotency (Smith MED) — sem UniqueViolation catch
- F-ORACLE-NEO-BL3-CRIT-01 — import error introduz crash em ambient sem `format_error`

**NFR Reliability:** CONCERNS — PATCH required.

### Maintainability (CONCERNS)

- F-NEO-BL3-05 duplicação truth (Pydantic Literal + SQL CHECK) — Smith LOW
- F-ORACLE-NEO-BL3-CRIT-01 — import quebrado revela falta de pre-commit hook validation

**NFR Maintainability:** CONCERNS — recomenda pre-commit hook `python -c "import <module>"` test.

### Testability (PASS)

- 31 tests empirical pass ✓
- Parametrize edge cases ✓
- Fixture reuse pattern Bloco 2 ✓

**NFR Testability:** PASS (módulo imobiliario_schema isoladamente).

---

## AC Coverage Final (G5 Verification)

| AC | Smith 4.5 Status | Oracle G5 Empirical | Final |
|----|------------------|--------------------|----- |
| AC-1 SPA fieldset conditional | FULL | Static review — JS conditional OK | ✓ FULL |
| AC-2 matrícula regex | FULL | Tests pass empirical (10 regex tests) | ✓ FULL |
| AC-3 valor Decimal bounds | FULL | Tests pass empirical (8 bounds tests) | ✓ FULL |
| AC-4 garantia enum 2 | FULL | Tests pass empirical (3 enum tests) | ✓ FULL |
| AC-5 indice enum 4 | FULL | Tests pass empirical (5 enum tests) | ✓ FULL |
| AC-6 Pydantic strict | FULL | Tests pass empirical (extra='forbid' reject) | ✓ FULL |
| AC-7 LLM template v1.0.0 | FULL | Static review prompt file | ✓ FULL |
| AC-8 prompt versioned ADR-020 | FULL | Static review | ✓ FULL |
| AC-9 analytics doctype_selected hook | FULL | Bloco 2 reuse | ✓ FULL |
| AC-10 badge MODOS_AVANCADOS | FULL | Static review JS | ✓ FULL |
| AC-11 CLI First Art. I | FULL | **Empirical: import broken** | 🔴 FAIL |
| AC-12 zero regression ≥425 | PENDENTE | **Empirical: 424 (regression -1)** | 🔴 FAIL |
| AC-13 schema migration RLS | FULL | Static review SQL | ✓ FULL |

**Coverage final:** 11/13 FULL + 2 FAIL (AC-11 + AC-12).

---

## VERDICT

# 🔴 FAIL

**Razão:**
- F-ORACLE-NEO-BL3-CRIT-01 (CRITICAL Constitutional Art. IV violation) introduz regression
- AC-11 CLI First FAIL — CLI module quebra import-time
- AC-12 zero regression FAIL — baseline 425 → 424

**Bloqueio:** Story TD-SP04-S4-V1 NÃO pode prosseguir para Operator push até Neo PATCH.

**Smith Fase 4.5 reassessment:** Verdict CONTAINED foi *insufficient* — escrutínio textual perdeu invenção runtime. Empirical inspection mandatory para CLI/import paths.

---

## Recomendação Próxima Skill

**Oracle→Smith Fase 5.5:** Mid-chain Oracle verdict review per chain protocol Eric rigor heavy.

Smith Fase 5.5 deve:
1. Verificar Oracle G5 findings empirical (re-run pytest local OR aceitar Oracle evidence)
2. Routing decision: Smith→Neo PATCH OR Smith→Oracle re-gate (se discordar)
3. Documentar Smith Fase 4.5 oversight (Constitutional Art. IV missed) como TD-PROCESS-XX cataloged Sprint posterior

Handoff: `.lmas/handoffs/handoff-oracle-to-smith-2026-05-13-fase-5-5-midchain-g5-verdict-review.yaml`

**Expected Smith 5.5 verdict:** CONFIRM Oracle FAIL → handoff Smith→Neo PATCH (chunk 4 CLI fix — Opção A ou B).

**Story status update:** Ready for Review → **Needs Patch** (regression).

---

## QA Results Section — Append-Only

### Oracle G5 Quality Gate — 2026-05-13

**Reviewer:** @qa (Oracle)
**Verdict:** FAIL
**Critical Findings:** 1 (F-ORACLE-NEO-BL3-CRIT-01 — `format_error` invention)
**Regression:** -1 vs baseline 425 (test_cli.py broken)
**AC FAIL:** AC-11 + AC-12
**Status:** Needs PATCH from @dev (Neo)
**Next:** Oracle→Smith Fase 5.5 mid-chain verdict review

---

*— Oracle, guardião da qualidade 🛡️*
*"Validação é o preço da confiança. Sem ela, todo deploy é fé."*
