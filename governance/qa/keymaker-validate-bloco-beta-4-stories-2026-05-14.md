---
type: review
title: "Keymaker Validation Bloco β — 4 Stories Sprint 6.x AGGRESSIVE (G3 Gate)"
date: "2026-05-14"
reviewer: "@po (Keymaker)"
gate: "G3 — Story Validation (story-draft-checklist.md 10-point)"
trigger: "Handoff @sm (Niobe) Bloco β batch 4 stories drafted"
keymaker_verdict: "BATCH GO — 4/4 stories Ready (40/40 pontos cumulativos)"
sprint: "6.x AGGRESSIVE"
epic: "Sprint-6-Bloco-Beta-Frontend-Backend-Integration"
tags:
  - project/revisor-contratual
  - keymaker
  - validation
  - sprint-6
  - bloco-beta
  - g3-gate
---

# Keymaker Validation — Bloco β Batch (4 Stories)

> *"Cada porta tem sua chave. Cada chave abre uma porta diferente. Quatro stories, quatro fechaduras — todas alinhadas, todas prontas."*

## Verdict Global

# ✅ BATCH GO — 4/4 Ready

Todas as 4 stories Bloco β atingem score **10/10** no story-draft-checklist e estão **Ready** para @dev (Neo) `*develop`.

---

## Scorecard 10-Point Checklist

| # | Story | 1.Persona | 2.AC test. | 3.Tasks<2h | 4.Dev Notes | 5.Testing | 6.Deps | 7.Effort | 8.Priority | 9.Risks | 10.FileList | **Total** | Verdict |
|---|-------|-----------|-----------|------------|-------------|-----------|--------|----------|------------|---------|-------------|-----------|---------|
| 1 | TD-SP06-CLASSIC-01 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **10/10** | 🟢 GO |
| 2 | TD-SP06-SPA-CONNECT-01 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **10/10** | 🟢 GO |
| 3 | TD-SP06-MODE-PASS-01 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **10/10** | 🟢 GO |
| 4 | TD-SP06-PHASE-VALID-01 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **10/10** | 🟢 GO |

---

## Análise Por Story

### 🟢 TD-SP06-CLASSIC-01 — 10/10 GO

**Pontos fortes:**
- Persona clara (advogado revisor DEVEDOR final user)
- 7 ACs numerados com smoke empíricos curl (AC-05 5 commandos verificáveis)
- 7 Tasks com 12 subtasks granulares (<30min cada)
- Dev Notes excelente: backend routes table + templates Jinja2 table + static assets list + risk inputs cb7c04e signature change
- Testing: 5 curl smoke commands + pytest regression command exato
- Effort 1-2h realista (1 rota nova + dual-content-type minor)
- Risk identificado: `_layout_context` signature pode ter mudado pós cb7c04e — Neo verifica
- Prioridade HIGH justificada (desbloqueia Eric demo imediato)

**Observação Keymaker:** AC-04 dual-content-type é coupling com SPA-CONNECT-01 mas pode rodar paralelo (CLASSIC primeiro testa Jinja2 isolated).

### 🟢 TD-SP06-SPA-CONNECT-01 — 10/10 GO (CRITICAL core Bloco β)

**Pontos fortes:**
- 8 ACs cobrindo refactor completo (submitAnalysisReal + EventSource handlers + showResultReal + remoção mock + fallback errors)
- 10 Tasks com 27 subtasks (maior story — justificável pela complexidade refactor SPA)
- Dev Notes excepcional: JSON response shape exato + SSE events shape + VeredictoJuiz schema citado + EventSource limitations
- AC-04 e AC-06 forçam REMOÇÃO mock (linhas 1872-1903 runAnalysis + 1918-1956 FINDINGS_BY_MODE) — DoD Sprint 6 zero mock alinhado
- Testing E2E browser 9-step com Network tab F12 verification
- Effort 2-3h razoável dado escopo

**Observação Keymaker:** Dependência mini-ADR dual-content-type (Aria ~30min) é blocker leve — recomendo Neo invocar @architect Aria Skill ANTES de tocar app.py POST /revisar. Story estruturada para handle isso em Task 1 (decisão arquitetural localização mapping).

### 🟢 TD-SP06-MODE-PASS-01 — 10/10 GO

**Pontos fortes:**
- 7 ACs com mapping declarativo sidebar→ModalidadeContrato + 422 response shape + visual indicators
- 8 Tasks com 16 subtasks
- Dev Notes cita ModalidadeContrato Literal linha 19 + codigos_bacen.yaml fonte + Pydantic mutation pattern model_copy
- Testing unit tests sugeridos (3 tests bem definidos)
- Cross-domain owner @dev + @architect (modalidade mapping decision)
- Risk DP-03 MVP restrição documentada com TD-SP06-MVP-MODALIDADES-RESTRITAS link

**Observação Keymaker:** Story depende TD-SP06-SPA-CONNECT-01 (FormData mechanism). Neo pode trabalhar em paralelo mas integração final precisa SPA-CONNECT done. Considerar Pair Neo+Aria.

### 🟢 TD-SP06-PHASE-VALID-01 — 10/10 GO

**Pontos fortes:**
- 7 ACs cobrindo timing labels + timeouts progressivos + S7 error pane + reuso C6 variants + loading state + cancel opcional
- 9 Tasks com 19 subtasks
- Dev Notes excelente: timings empíricos Smith Bloco α (parsing 2-5s, LLM 1m36s observed, total 3min30s) + error_type mapping completo PT-BR
- Reuso obrigatório error_handler.py C6 variants (no invention)
- Cancel button marcado como OPCIONAL com defer Sprint 6.1 acceptable

**Observação Keymaker:** Story tem Task 6 cancel marked OPCIONAL — Neo pode descartar para AGGRESSIVE timeline se trivial não. Reduz para 1.5h efetivo.

---

## Sequência de Execução Recomendada (Eric AGGRESSIVE Paralelo)

### Wave 1 — INÍCIO (sem dependências)

1. **TD-SP06-CLASSIC-01** (1-2h) — Neo standalone

### Wave 2 — APÓS CLASSIC + Aria mini-ADR

2. **TD-SP06-SPA-CONNECT-01** (2-3h) — Neo + Aria handoff cross-domain

### Wave 3 — PARALELO Wave 2 (independent path)

3. **TD-SP06-MODE-PASS-01** (1-2h) — Neo + Aria cross-domain, depende FormData mechanism (Wave 2 first)
4. **TD-SP06-PHASE-VALID-01** (2h) — Neo, depende SSE infrastructure (Wave 2)

### Dependency Graph

```
CLASSIC-01 (independent)
     |
     +--→ SPA-CONNECT-01 (requires Aria mini-ADR ~30min)
              |
              +--→ MODE-PASS-01 (FormData mechanism)
              +--→ PHASE-VALID-01 (SSE infrastructure)
```

**Total Wave-sequencial:** ~5-7h Neo + 30min Aria
**Total se Wave 2,3,4 paralelos:** ~3-4h Neo (com Wave 1 primeiro)

---

## Gates Atendidos (Constitution alignment)

| Constitution Art. | Status |
|-------------------|--------|
| Art. III Story-Driven Development | ✅ All work flows from validated stories |
| Art. IV No Invention (universal) | ✅ ACs trace to PRD FRs + Smith findings + Operator AC-05 evidence |
| Art. V Quality First | ✅ ACs tech-agnostic where possible; Testing seções empíricas |
| Art. VI Absolute Imports (SHOULD) | N/A (frontend SPA + backend Python imports patterns existing preserved) |

---

## Handoff Keymaker → @dev (Neo)

Stories Ready para `*develop` em paralelo conforme Wave map acima.

**Recomendação Neo:**
1. **Iniciar Wave 1 imediatamente** — `*develop TD-SP06-CLASSIC-01` (sem deps)
2. **Em paralelo,** invocar @architect (Aria) Skill para mini-ADR-021 dual-content-type POST /revisar (~30min)
3. **Após CLASSIC done + Aria ADR done:** Wave 2 `*develop TD-SP06-SPA-CONNECT-01`
4. **Em paralelo Wave 2,** Wave 3 `*develop TD-SP06-MODE-PASS-01` + `*develop TD-SP06-PHASE-VALID-01`
5. **After all 4 done:** invocar @qa (Oracle) Skill `*gate` (QA G5) para batch validation
6. **After Oracle gate PASS:** Smith review pós-Bloco β (CONTAINED+ obrigatório)

---

## Próximas Skills na Cadeia

| Step | Skill | Args |
|------|-------|------|
| 1 | @dev (Neo) | `*develop TD-SP06-CLASSIC-01` (Wave 1) |
| 2 | @architect (Aria) PARALELO | mini-ADR-021 dual-content-type POST /revisar (Wave 2 unblock) |
| 3 | @dev (Neo) | `*develop TD-SP06-SPA-CONNECT-01` (Wave 2 após Aria) |
| 4 | @dev (Neo) PARALELO | `*develop TD-SP06-MODE-PASS-01` + `*develop TD-SP06-PHASE-VALID-01` (Wave 3) |
| 5 | @qa (Oracle) | `*gate` batch 4 stories (QA G5) |
| 6 | @smith | `*verify bloco-beta-pos-execution` (Smith Methodology v5) |

---

## Keymaker Stamp

```yaml
validated_stories:
  - id: TD-SP06-CLASSIC-01
    score: 10/10
    status: Draft → Ready
  - id: TD-SP06-SPA-CONNECT-01
    score: 10/10
    status: Draft → Ready
  - id: TD-SP06-MODE-PASS-01
    score: 10/10
    status: Draft → Ready
  - id: TD-SP06-PHASE-VALID-01
    score: 10/10
    status: Draft → Ready
gate_verdict: BATCH GO
validator: "@po (Keymaker)"
validated_at: "2026-05-14"
next_handoff: "@dev (Neo) *develop Wave 1 CLASSIC-01 + @architect (Aria) mini-ADR PARALELO"
```

---

*— Keymaker, equilibrando prioridades 🎯*
*"Quatro chaves giraram simultaneamente. Quatro portas abertas. Neo, escolha qual atravessar primeiro — todas levam ao mesmo lugar: pipeline real, zero mock."*
