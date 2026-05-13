---
type: orchestration-route
id: MORPHEUS-ROUTE-SPRINT-5-REMAINING-2026-05-13
title: "Morpheus Route — Sprint 5+ Remaining Priority Synthesis"
project: revisor-contratual
date: 2026-05-13
ordem: 20.1
sdc_phase: "route-priority-synthesis"
orchestrator: "@claudino (Morpheus)"
predecessor_closure: "TD-SP04-04-ANALYTICS DONE Ordem 19.2 Fase 8"
verdict: "Trinity @pm spec pipeline recommended — synthesize v0.3.0 remaining + identify next attackable story candidate"
tags:
  - project/revisor-contratual
  - orchestration
  - sprint-5-plus
  - priority-synthesis
  - morpheus-route
---

# Morpheus Route — Sprint 5+ Remaining Priority Synthesis

> *"A porta fechou — Ordem 19.2 está consumida. Outras portas aguardam. Mas não toda porta merece ser aberta agora. Vamos discernir."*

---

## Synapse + Constitution Loaded

**Synapse v2.1.0:** PRD location `docs/prd.md` (sharded `docs/prd/`); Stories `docs/stories`; QA `docs/qa`; User profile **advanced**.

**Constitution v2.0.0:**
- Art. I — CLI First (NON-NEGOTIABLE)
- Art. II — Agent Authority (NON-NEGOTIABLE)
- Art. III — Deliverable-Driven
- Art. IV — Quality Gates

**Project state Sprint 5+:**
- Bloco 1 TD-SP04-15 tooltips sidebar DONE (precedent additive frontend)
- Bloco 2 TD-SP04-04-ANALYTICS DONE (5 métricas Sati Eixo 5 MANDATORY)
- 1/4 v0.3.0 blockers UNBLOCKED
- 3 remaining external blockers + plus opção Bloco 3 TBD

---

## 5 Candidates Analysis Matrix

| # | Candidate | Domain | Skill route | Bloqueador | Attackable now? |
|---|-----------|--------|-------------|------------|-----------------|
| 1 | TD-SP04-10 TOS advogado ANPD (~9.5h) | software-dev/legal | Trinity @pm + Eric externo | Advogado externo Eric | ❌ External — code não desbloqueia |
| 2 | Smoke E2E completo (BYOK+multi-tenant+LGPD) | software-dev | Oracle @qa + Neo @dev | Test infra setup local (.venv/Docker) | ⚠️ Attackable mas requires Eric env setup primeiro (TD-L7 catalog) |
| 3 | BL-VAULT-BULK-IMPORT + BL-GOLDEN-SET (Sprint 6+ Oracle 8-12h) | software-dev | Atlas @analyst + Tank @data-engineer + Neo @dev | Vault jurisprudência válida + métodos | ⚠️ Sprint 6+ scope; defer |
| 4 | Advogada Blocos D/E/F microcopy (~6h) | marketing/legal | @copywriter Mouse OR Sati + advogada externa | Advogada externa | ❌ External |
| 5 | **Bloco 3 nova story TBD** | software-dev | Trinity @pm spec pipeline | TBD identify gap real | ✅ **Most attackable** |

---

## Decision Tree

```
Eric directive "continue desenvolvimento" + rigor heavy
    ↓
Need: feature code work (não governance/external/setup)
    ↓
Candidates attackable agora?
  ✅ #5 Bloco 3 nova story (Trinity identify gap)
  ⚠️ #2 Smoke E2E (Eric env setup primeiro)
  ⚠️ #3 BL-VAULT (Sprint 6+ scope)
  ❌ #1 #4 (external Eric/advogados)
    ↓
Best route: Trinity @pm *status synthesize remaining v0.3.0 +
            identify Bloco 3 candidate gap real
            (PRD authority + epic orchestrator)
```

---

## Recommendation: Trinity @pm Synthesize + Identify Bloco 3

**Rationale Constitution Art. II Agent Authority:**
- Trinity @pm owns PRD orchestration + epic creation
- Trinity has visibility cross-Sprint backlog (Sprint 5+/6+ context)
- Trinity decides: continue Bloco 3 OR escalate Sprint 6+ start OR defer

**Skill chain proposta (rigor heavy):**

```
Morpheus *route (THIS)
    ↓ handoff
Trinity @pm *status
    ↓ analyze remaining + identify Bloco 3 candidate
    ↓ create PRD update OR spec stub
    ↓ handoff Smith Fase Trinity.5 (mid-chain review PRD synthesis)
Smith *verify Trinity synthesis
    ↓ CLEAN/CONTAINED → River @sm *draft Bloco 3 story
    ↓ INFECTED → Trinity PATCH
River @sm *draft Bloco 3 story
    ↓ Smith Fase River.5
Keymaker @po *validate-story-draft G3 10-point
    ↓ Smith Fase Keymaker.5
Neo @dev *develop
    ↓ Smith Fase Neo.5
Oracle @qa *qa-gate G5
    ↓ Smith Fase Oracle.5
Operator @devops *push
    ↓ Smith FINAL pre-merge CI verification
Eric merge Fase 7
    ↓ Morpheus closure FINAL
```

**Estimate cycle:** ~3-5 sessões Skill cumulativas (replicate Bloco 2 pattern).

---

## Alternative Routes (se Eric prefere)

### Alternative A: Smoke E2E Sprint 5+ Bloco 3

**Path:** Eric setup local primeiro (`.venv` + WSL Ubuntu install OR Docker test container TD-L7 fix) → Oracle @qa *qa-loop Sprint 04 stories integration tests `_REQUIRES_POSTGRES` retest. Heavy infra work.

### Alternative B: Eric externo loops parallel

**Path:** Eric inicia TOS advogado conversation + Advogada Blocos D/E/F microcopy review parallelo enquanto LMAS aguarda. NÃO requer LMAS Skills agora.

### Alternative C: BL-VAULT Sprint 6+ early start

**Path:** Atlas @analyst pesquisa jurisprudência methodology + vault bulk import design. Anticipa Sprint 6+ work. Trade-off: defer v0.3.0 release foco.

---

## Next Action

**Recommended Skill handoff:** `LMAS:agents:pm` (Trinity) com prompt:

```
*status — Sprint 5+ remaining synthesis:
1. Analise TECH-DEBT.md TD-SP04 + TD-ANALYTICS-L1..L7 acumulado
2. Analise Sati ratify post-hoc Sprint 04 sessão 92 — Eixo 5 era único MANDATORY
   ou outros Eixos também?
3. Identifique Bloco 3 candidate gap real (não governance, não external Eric)
4. Recommend PRD update OR spec creation OR story stub
5. Emit handoff próxima Skill (River @sm *draft se Bloco 3 ready, OR Atlas
   @analyst *research se gap unclear)
```

Trinity executar com Eric rigor heavy: PRD guardado + ambiguidade reduzida + handoff artifact CADA Skill. Smith Fase Trinity.5 review mid-chain ao fim.

---

## Decisões Morpheus (D-MOR-S05-Route-001..003)

- **D-MOR-S05-Route-001:** Trinity @pm é next Skill correta — PRD authority + epic orchestration per Agent Authority Art. II.
- **D-MOR-S05-Route-002:** Bloco 3 candidate identification é PRD work — Trinity owns synthesis cross-Sprint backlog.
- **D-MOR-S05-Route-003:** Eric rigor heavy directive: Trinity *status NÃO bypass Smith — mid-chain Fase Trinity.5 review obrigatório CADA Skill troca.

---

## Files modified Morpheus Ordem 20.1 route

- `governance/qa/morpheus-route-sprint-5-remaining-2026-05-13.md` (NEW — este)
- `.lmas/handoffs/handoff-morpheus-to-trinity-2026-05-13-sprint-5-remaining-synthesis.yaml` (NEW — próximo)

— Morpheus 🎯
