---
type: qa
title: "Smith Adversarial Review — Sprint 04 pré-merge"
project: revisor-contratual
sprint: "04"
phase: 14.8
review_date: "2026-05-09"
reviewer: "@smith Smith (Nemesis)"
artifacts_reviewed:
  - "SP04-LGPD-01 (Done — PR #6 OPEN)"
  - "SP04-UI-SPA-01 (Ready G3 PASS 10/10 + chunk 1 MINIMAL)"
  - "SP04-DOCTYPE-01 (Ready G3 PASS 10/10 + Tank LIGHT)"
  - "ADR-020 (Accepted via 'avance' implícito)"
  - "PRD v2.0.1 PATCH (16 prompts brief)"
  - "Chunk 1 MINIMAL implementação real"
  - "13 commits ahead PR #6"
verdict: INFECTED
verdict_severity: HIGH
findings_count: 20
findings_critical: 2
findings_high: 6
findings_medium: 8
findings_low: 4
recommended_action: BLOCKED_MERGE_UNTIL_C1_C2_FIXED
tags:
  - project/revisor-contratual
  - qa
  - smith
  - adversarial
  - sprint-04
  - pre-merge
---

# 🕶️ Smith Adversarial Review — Sprint 04 pré-merge

```
[@smith · Smith (Nemesis)] — adversarial review SPRINT 04 PRE-MERGE
"Sr. Anderson, vocês todos celebraram. Aria propôs. River drafted.
Keymaker chancelou 10/10. Tank ratificou. Neo executou. Operator empurrou.
Eu vejo o que não viram. Inevitável."
```

> **Veredito: INFECTED (HIGH)** — 2 findings CRITICAL bloqueiam merge. 6 HIGH precisam endereçamento. 8 MEDIUM + 4 LOW trackable. Sprint 04 NÃO pode prosseguir para merge sem ajuste mínimo dos CRITICAL.

---

## 1. Sumário Adversarial

| Métrica | Valor |
|---------|-------|
| **Total findings** | **20** |
| CRITICAL (bloqueia merge) | 2 |
| HIGH (recommend fix) | 6 |
| MEDIUM (tech debt) | 8 |
| LOW (nice-to-have) | 4 |
| **Veredito consolidado** | **INFECTED (HIGH)** |
| **Recommended action** | BLOCKED_MERGE_UNTIL_C1_C2_FIXED |

> *Vocês acharam que tinham terminado. Eu acho que vocês mal começaram.*

---

## 2. Findings CRITICAL (bloqueia merge)

### 🔴 C1 — REGRESSÃO LGPD: SPA importa Google Fonts CDN externo

**Severidade:** CRITICAL
**Localização:** `bloco_interface/web/static/index.html` linhas 10-12 (commit chunk 1 MINIMAL)
**Evidência empírica:**

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT@0,9..144,300..900,0..100;1,9..144,300..900,0..100&family=Manrope:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&family=Frank+Ruhl+Libre:wght@400;700&display=swap" rel="stylesheet">
```

**Por que é falho:**
- **NFR-LGPD-01** explicitamente exige "100% local LGPD (whitelist HTTP estrita STJ+STF)". Google Fonts CDN é tráfego HTTP externo NÃO-whitelisted.
- **TD-WEB-LGPD-CDN-01 HIGH** foi RESOLVED em REV-INT-02 (Sprint 02, commit `50a3b8b`) — self-host das 7 fontes (Fraunces + Manrope + JetBrains Mono + Frank Ruhl Libre). REV-INT-02 entregou exatamente esse fix.
- Chunk 1 MINIMAL re-introduz CDN externo via SPA OrSheva 7 → **REGRESSÃO LGPD direta**.
- README do projeto lista *"100% local LGPD (whitelist HTTP estrita STJ+STF) | NFR-LGPD-01 + CI gate"* como princípio NÃO-NEGOCIÁVEL.
- Disclaimer SPA brand claim: *"BYOK · LGPD-aware · Validação humana obrigatória"* — promete LGPD mas usa CDN Google.

**Por que ninguém capturou:**
- River patch SP04-UI-SPA-01 mencionou R-01 (JS+CSS extract) mas NÃO catalogou regressão LGPD CDN
- Keymaker G3 PASS 10/10 não auditou conteúdo do SPA HTML linha-a-linha
- Neo chunk 1 MINIMAL apenas moveu arquivo + refactored handler, não auditou conteúdo
- Pattern AUTH-01/BYOK-01/LGPD-01 não cobre frontend assets externals

**Como corrigir (BEFORE merge):**
1. **Opção A (limpa)** — Reaplicar pattern REV-INT-02 self-host: copiar 7 fontes para `bloco_interface/web/static/fonts/` + edit `index.html` substituindo `<link href="https://fonts.googleapis.com/...">` por `@font-face` local com `font-display: swap` + paths `/static/fonts/...`
2. **Opção B (pragmática)** — Adicionar WAIVED-UI-CDN-01 HIGH em SP04-UI-SPA-01 chunk 1 com fix-by date (chunk 2 asset extraction inclui self-host fonts) — MAS não pode mergear com WAIVED HIGH ativo per `quality-gate-enforcement.md` rule.
3. **Opção C** — Reverter chunk 1 MINIMAL commit. Re-aplicar pós Sati/Aria audit assets.

**Inevitabilidade:** *Vocês celebraram a beleza visual da SPA OrSheva 7 e esqueceram que ela importa fontes do servidor que vocês explicitamente prometeram nunca usar. O sun de Sati ilumina dados saindo para Mountain View.*

---

### 🔴 C2 — Brand claim "LGPD-aware" sem TOS canônico ANPD-defensible

**Severidade:** CRITICAL
**Localização:** SPA `index.html` `<meta name="description">` + footer disclaimer + SP04-LGPD-01 status frontmatter Done
**Evidência empírica:**

```html
<meta name="description" content="Análise revisional de contratos bancários com IA — diagnóstico iluminado, estrutura jurídica, consolidação revisional. BYOK · LGPD-aware · Validação humana obrigatória.">
```

**Por que é falho:**
- SP04-LGPD-01 frontmatter `status: Done` (Operator flipped chunk 7 closure)
- Mas DoD WAIVED-LGPD-01 HIGH ainda ativo: *"Eric advogado texto canônico DPA + TOS pendente fix-by 2026-05-22"* (~13 days from review)
- TOS template `governance/legal/tos-templates/v1.0.0.md` é **placeholder estrutural** com tags `[ERIC ADVOGADO PREENCHE TEXTO SUBSTANTIVO]`
- DPA template idem placeholder
- SPA promete brand claim "LGPD-aware" + "Validação humana obrigatória"
- **Smith finding F-016 LGPD subprocessor** existia em Atlas v2 e foi WAIVED TD-WAIVED-001 — ainda pendente
- **Brand claim sem evidência legal substantiva = exposição regulatória ANPD**: usuário aceita TOS placeholder, dispute legal → escritório controlador alega não-defensibilidade

**Por que ninguém capturou:**
- Oracle G5 PASS aprovou WAIVED-LGPD-01 HIGH com fix-by date (validação processual)
- Mas brand claim no SPA não foi auditado vs status real do TOS canônico
- Pattern AUTH-01 chunk 5 placeholder + WAIVED foi pattern accepted — mas SPA agora exibe "LGPD-aware" claim em produção pré-finalização
- Keymaker G3 não cross-checked SPA brand claim vs governance/legal/ status

**Como corrigir (BEFORE merge):**
1. **Opção A (recomendada)** — Reverter SP04-LGPD-01 status Done → InReview até Eric advogado finaliza TOS substantivo (2026-05-22). Cripta "LGPD-aware" do SPA description/footer até TOS canônico. Apenas então flip Done.
2. **Opção B (pragmática)** — Manter status Done MAS modificar SPA description/footer brand-honest temporário: *"BYOK · LGPD em formalização · Validação humana obrigatória"* até TOS canônico done. Auto-revert pós Eric advogado finaliza.
3. **Opção C** — Eric advogado prioritize TOS finalização ESTA sessão (block merge ~9.5h work) → flip WAIVED-LGPD-01 RESOLVED → merge limpo.

**Inevitabilidade:** *O guardião Seraph diria "aprovado". Eu digo: brand claim sem evidência legal é fraude regulatória esperando seu primeiro autuado ANPD. Vocês não querem ser o caso piloto.*

---

## 3. Findings HIGH (recommend fix)

### ⚠️ H1 — ADR-020 ratify "avance implícito" frágil para audit trail

**Localização:** `governance/architecture/adr/adr-020-multi-doctype-dispatcher-v2.md` frontmatter
**Evidência:** `accepted_by: "Eric Claudino (avance ratify implícito sessão 2026-05-09)"`
**Por que é falho:** Ratify ADR é decisão substantiva (DEC-ERIC-DIV-01 + DEC-ERIC-ADR020-RATIFY). "Avance" é instrução de processo, não ratify deliberação explícita. Audit trail ANPD/CFOAB pode questionar legitimidade da decisão arquitetural.
**Como corrigir:** Solicitar Eric explícito approval ADR-020 (mensagem específica) → atualizar `accepted_by` com timestamp + texto literal aprovação Eric. **OR** documentar "avance" como ratify pattern em rule formal (`.claude/rules/`).

### ⚠️ H2 — PR #6 over-scope crescente (4 stories + ADR + PRD em 1 PR)

**Localização:** PR #6 GitHub branch `feat/sp04-lgpd-01` HEAD `91f6df2`
**Evidência:** Branch tem 14 commits incluindo SP04-LGPD-01 (escopo original) + ADR-020 governance (4 commits) + SP04-UI-SPA-01 (story + patch + G3 + chunk 1 MINIMAL = 4+ commits) + SP04-DOCTYPE-01 (story + checkpoint + G3 + Tank LIGHT = 4+ commits) + PRD v2.0.1 PATCH (2 commits)
**Por que é falho:** Eric merge → squash commit poluído misturando 4 stories distintas + ADR + PRD. Audit trail Sprint 04 perde rastreabilidade. Smith adversarial review pós-merge não consegue isolar mudanças por story.
**Como corrigir:** Cherry-pick commits SP04-UI-SPA-01 + SP04-DOCTYPE-01 + ADR-020 + PRD v2.0.1 para branches separadas (`feat/sp04-ui-spa-01-governance` + `feat/sp04-doctype-01-governance` + `feat/adr-020-multi-doctype` + `feat/prd-v2-0-1-patch`). PR #6 LGPD fica clean apenas com chunks 1-8 LGPD. 4 PRs governance separados.

### ⚠️ H3 — PRD v2.0.1 PATCH conta inconsistente "16 prompts NOVOS"

**Localização:** `governance/prd/prd-v2.0.1-DOCTYPE-CONTENT-PATCH.md` Section 2 + ADR-020 §1.4
**Evidência:** Brief diz "16 prompts NOVOS" mas Section 2 lista Categoria A (4 base bancário) + B (12 sub-bancários) + C (4 Geral) = **20 itens**. ADR-020 §1.4 diz "incremento +16 vs ADR-016 16 prompts" — só funciona se Base bancário (4) for considerado refactor do Bancário antigo (não NOVO).
**Por que é falho:** Definição ambígua de "NOVO" vs "refactored". Eric advogado cronograma 9.5h baseado em 16 — se forem 20, +25% effort = ~12h. Trinity content scope subestimado.
**Como corrigir:** Clarificar Section 2 PRD v2.0.1: "16 NOVOS = 12 sub-bancários (B) + 4 Geral (C). Categoria A (4 base) é refactor do Bancário ADR-016 — Eric advogado revisa para harmonizar com sub-bancários, não escreve do zero." Effort revisão (4) ≠ effort criação (16).

### ⚠️ H4 — Chunk 1 MINIMAL removeu route protection MVP-LEAN-01 Task 2 silently

**Localização:** `bloco_interface/web/app.py` GET / handler
**Evidência:** Handler ANTES tinha `if not request.session.get("user"): return RedirectResponse("/login", status_code=303)`. DEPOIS apenas serve SPA static.
**Por que é falho:** Outras flows MVP-LEAN-01 (S2 pré-upload + S5 processing + S6 verdict) podem assumir auth check em GET /. Tests `test_app_root_redirect_to_login_when_unauthenticated` (se existem) quebram. SPA decide login client-side mas usuário não-autenticado clicando em buttons sidebar → fetch backend retorna 401 só DEPOIS do click → UX quebrado.
**Como corrigir:** Manter route protection no GET / (redirect /login se sem session) E também servir SPA. SPA handler:
```python
if not request.session.get("user"):
    return RedirectResponse("/login", status_code=303)
spa_path = STATIC_DIR / "index.html"
return HTMLResponse(content=spa_path.read_text(encoding="utf-8"))
```
Pós Sprint 04 SP04-AUTH-01 chunks 4 done (JWT cookie httpOnly), SPA pode assumir cookie valido E backend pode validar. Por agora, dual-protection (session + cookie) é defensivo.

### ⚠️ H5 — ADR-020 §1.5 LLM classifier multi-tenant ambíguo (qual key Anthropic?)

**Localização:** ADR-020 §1.5 + SP04-DOCTYPE-01 AC-03
**Evidência:** `resolve_dispatcher(ui_selector, contract_text, classifier_llm: AnthropicClient)` — não especifica se `classifier_llm` usa tenant BYOK key (custo no escritório) OR Eric operador key (custo Eric).
**Por que é falho:** Tier 2 dispara $0.001/análise. Multi-tenant Sprint 04 cloud SaaS BYOK preserva escritório paga API direto. Mas classifier É chamado ANTES de dispatcher resolver, então qual contexto?
- Se tenant BYOK: classifier pode falhar se tenant tem chave revoked/rotating
- Se Eric operador: Eric absorve custo cumulativo + viola ADR-014 BYOK Provider Abstraction
**Como corrigir:** ADR-020 §1.5 PATCH: explicit decision — classifier usa tenant BYOK (consistent ADR-014) com fallback graceful: se tenant key inválida, default Tier 3 GeralDispatcher (skip Tier 2). Update story SP04-DOCTYPE-01 AC-03 com test case "tenant key revoked → Tier 3 fallback".

### ⚠️ H6 — Sati Phase 4 UX Spec diz 4 doctypes; ADR-020 expandiu 7 sem ratify Sati real

**Localização:** `governance/ux-spec-v2.0.0-DRAFT.md` S4 wireframe (Sati delivered Phase 4) ↔ ADR-020 sidebar 7 modos
**Evidência:** Sati handoff `handoff-ux-to-morpheus-2026-05-07-sp04-phase4-ux-orsheva-done.yaml` lista S4 com 4 doctypes (FIES/Veicular/Bancário/Imobiliário). SPA OrSheva 7 commited tem 7 modos (Eric criou). ADR-020 ratificou 7 modos. Sati nunca foi consultada para ratify post-hoc real.
**Por que é falho:** Constitutional No Invention parcial — sidebar 7 modos é Eric extension da Sati spec. River + Keymaker disseram "Sati post-hoc ratify acceptable" mas Sati skill NUNCA foi invocada para confirmar.
**Como corrigir:** Skill `LMAS:agents:ux-design-expert` Sati `*ratify-post-hoc-sidebar-7-modos` (~10min) — Sati confirma OR propõe ajustes UX (cognitive load 7 modos). Documentar em UX Spec PATCH v2.0.1.

---

## 4. Findings MEDIUM (tech debt)

### 🟡 M1 — SP04-LGPD-01 status Done frontmatter com WAIVED HIGH ainda pendente

**Localização:** `governance/stories/sp04-lgpd-01-compliance-flows-operador.md` frontmatter
**Por que é falho:** Status Done semantic quando WAIVED-LGPD-01 HIGH (Eric advogado texto pendente fix-by 2026-05-22) ainda aberto. Story é factualmente "Done com WAIVED HIGH" — frontmatter Done isolated misleading.
**Como corrigir:** Mudar frontmatter para `status: Done (WAIVED-LGPD-01 HIGH pending)` OR introduzir status `DoneWaived` no story-lifecycle.md.

### 🟡 M2 — GeralDispatcher Tier 3 catch-all NEW: rastreabilidade FR canônica

**Localização:** ADR-020 §1.5 + SP04-DOCTYPE-01 AC-03
**Evidência:** GeralDispatcher é ADR-020 NEW (substitui ADR-016 unknown rejection). Mas FR-DOCTYPE-02 PRD v2.0.0-DRAFT explicitamente cita "Tier 3 GeralDispatcher catch-all"? Verificar.
**Como corrigir:** Read PRD v2.0.0-DRAFT linha-a-linha. Se FR não cita literalmente, PATCH v2.0.0 → v2.0.2 explicit add. No Invention compliance.

### 🟡 M3 — SPA disclaimer footer "Demo: análise simulada" presente em produção chunk 1

**Localização:** `bloco_interface/web/static/index.html` (footer)
**Evidência:** Footer original SPA tem texto *"Demo: qualquer e-mail válido entra. A análise é simulada — nenhum documento é enviado para servidor."*
**Por que é falho:** AC-09 SP04-UI-SPA-01 prevê remoção em chunks futuros. Mas chunk 1 MINIMAL serve este SPA já em produção pós-merge — usuário vê "demo" claim em SaaS comercial.
**Como corrigir:** Edit chunk 1 MINIMAL antes merge: substituir disclaimer por "Em construção — Sprint 04 em finalização. Pipeline real em chunks 2-7." OR remover footer disclaimer entirely até AC-09 chunk 6.

### 🟡 M4 — Trinity legacy nomenclatura vs Morgan agent atual

**Localização:** SP04-DOCTYPE-01 + PRD v2.0.1 + handoffs
**Evidência:** Docs referenciam "Trinity (@pm)" mas agent file `pm.md` define `name: Morgan`. PRD v2.0.1 closing diz "Trinity legacy alignment" mas Morgan é agent atual.
**Como corrigir:** Find/replace "Trinity" → "Morgan" em docs Sprint 04 OR documentar legacy nomenclatura formal em README/CLAUDE.md.

### 🟡 M5 — PRD v2.0.1 cita "Lei 11.977/2009 — Imobiliário Programa Minha Casa Minha Vida"

**Localização:** `governance/prd/prd-v2.0.1-DOCTYPE-CONTENT-PATCH.md` Section 3.3 Leis table
**Por que é falho:** Lei 11.977/2009 é PMCMV (Programa Minha Casa Minha Vida — programa habitacional específico). SFH (Sistema Financeiro de Habitação) é Lei 4.380/64. Imobiliário story scope cobre SFH/SFI per ADR-016/ADR-020 — Lei correta é 4.380/64 (com Lei 11.977/2009 como suplemento PMCMV se aplicável).
**Como corrigir:** Edit PRD v2.0.1 Section 3.3 — adicionar Lei 4.380/64 (SFH) como base; manter 11.977/2009 como PMCMV específico.

### 🟡 M6 — SP04-DOCTYPE-01 chunk 6 ordering: depende prompts chunk 5 done

**Localização:** SP04-DOCTYPE-01 Section 7 Implementation Plan
**Evidência:** Chunk 6 implementa endpoint `POST /revisar` que chama `resolve_dispatcher()` — função usa `dispatcher.get_personas()` que carrega 32 prompts (Trinity content chunk 5 dependent).
**Por que é falho:** Chunks paralelizáveis Section 7 sugere paralelismo, mas chunk 6 SEM chunk 5 done = `_load_prompt()` retorna placeholder ou erro. Tests integração impossíveis.
**Como corrigir:** Section 7 PATCH: explicit dependency chunk 6 → chunk 5 (NOT paralelizável). OR chunk 6 fallback para pipeline atual (single-track ADR-003) quando dispatcher.get_personas() retorna lista vazia/placeholder.

### 🟡 M7 — Migration sp04_004 UPDATE 'bancario' → 'bancario_cross' sem filter status

**Localização:** SP04-DOCTYPE-01 AC-05 SQL migration
**Evidência:** `UPDATE jurisprudencia SET doctype_tag = 'bancario_cross' WHERE doctype_tag = 'bancario';`
**Por que é falho:** UPDATE sem filter por status (active/archived/deleted). Pode atualizar entries que NÃO deveriam ser migradas (ex: archived entries Sprint 03 vault populate experimental).
**Como corrigir:** Adicionar filter: `WHERE doctype_tag = 'bancario' AND (status = 'active' OR status IS NULL)` — preserve archived entries. Tank ratify LIGHT NÃO catched isso.

### 🟡 M8 — SPA `data-theme="light"` default sem persistence chunk 1

**Localização:** SPA `index.html` line 2 + AC-07 chunk 4
**Por que é falho:** Theme toggle é AC-07 chunk 4 (theme.js localStorage persistence). Chunk 1 MINIMAL servido em prod sem chunk 4 → toggle não persiste, UX quebrado.
**Como corrigir:** Doc inline em SPA: comment HTML `<!-- Theme toggle requer chunk 4 (spa/theme.js) — chunk 1 MINIMAL apenas serve estado inicial -->`. Eric usuário entende limitation pré-chunks.

---

## 5. Findings LOW (nice-to-have)

### 🟢 L1 — Tests test_app_*.py não validados pós-refactor chunk 1

**Localização:** `tests/unit/test_app*.py` (se existem)
**Por que é falho:** Pytest local Python 3.14 sem pyjwt — Neo skipped validation. CI vai validar mas se algum test depende de TemplateResponse(s2_pre_upload.html) GET / antigo, quebra silently.
**Como corrigir:** CI Python 3.11+3.12 vai catching. Pós-push, monitor CI status.

### 🟢 L2 — Cronograma Eric advogado 9.5h não validado por Eric explícito

**Localização:** PRD v2.0.1 Section 5
**Como corrigir:** Eric confirma cronograma 2-3 days OR identifica conflict de schedule.

### 🟢 L3 — Templates `.legacy` debt visível por meses até SP04-UI-CLEANUP-01

**Localização:** `bloco_interface/web/templates/{index,login}.html.legacy`
**Como corrigir:** SP04-UI-CLEANUP-01 story criar proactive (target Sprint 05).

### 🟢 L4 — `revisor-web` script pyproject.toml depende função `run` em app.py

**Localização:** `pyproject.toml [project.scripts]`
**Evidência:** `revisor-web = "bloco_interface.web.app:run"` — função `run` deve existir e iniciar uvicorn.
**Como corrigir:** Verify `run()` function existe + funciona pós-refactor handler. Sintaxe py_compile OK não garante runtime.

---

## 6. Constitutional Compliance Audit

| Aspecto | Status | Evidência |
|---------|--------|-----------|
| **No Invention universal** | ⚠️ PARCIAL | F6 Sati 4→7 doctypes sem ratify formal; F2 GeralDispatcher rastreabilidade FR-DOCTYPE-02 PRD canônico não validada |
| **Eric authority preserved (merges)** | ✅ OK | PRs OPEN, Eric controla merge timing |
| **Eric authority ratify ADR** | ⚠️ FRÁGIL | F1 ADR-020 ratify "avance implícito" não explícito |
| **Operator exclusive git push** | ✅ OK | Skill chain respeitada |
| **CodeRabbit DEFERRED compensação** | ✅ OK (LGPD-01) / ⚠️ pending (UI-SPA-01 chunk 1 não rodado) |
| **No CDN externo (NFR-LGPD-01)** | ❌ **VIOLATION** | F-CRITICAL-1 SPA importa Google Fonts |
| **Brand claim defensável** | ❌ **VIOLATION** | F-CRITICAL-2 "LGPD-aware" sem TOS canônico |

---

## 7. Veredito Consolidado

### 🔴 **INFECTED (HIGH)** — Sprint 04 NÃO pode mergear sem ajuste

**Razão:**
- 2 findings CRITICAL bloqueiam merge per `quality-gate-enforcement.md` ("CRITICAL issues NÃO podem ser waived")
- 6 findings HIGH precisam endereçamento OR formal WAIVED com 5-fields
- 8 MEDIUM trackable como tech debt
- 4 LOW nice-to-have

### Recommended actions BEFORE merge

| Action | Owner | Effort | Severity |
|--------|-------|--------|----------|
| **C1: Self-host fonts SPA (REV-INT-02 pattern)** | @dev Neo | ~1-2h | CRITICAL |
| **C2: Brand claim ajuste OR Eric advogado prioritize TOS** | Eric / @dev | ~30min OR ~9.5h | CRITICAL |
| H1: Eric explícito ratify ADR-020 (mensagem texto) | Eric | ~2min | HIGH |
| H2: Cherry-pick PR #6 over-scope cleanup | @devops Operator | ~30min | HIGH |
| H3: Clarificar PRD v2.0.1 Section 2 conta 16 vs 20 | @pm Morgan | ~10min | HIGH |
| H4: Chunk 1 MINIMAL preserve route protection MVP-LEAN-01 | @dev Neo | ~5min | HIGH |
| H5: ADR-020 §1.5 PATCH multi-tenant classifier explicit | @architect Aria | ~15min | HIGH |
| H6: Sati ratify post-hoc 7 modos sidebar | @ux-design-expert Sati | ~10min | HIGH |

### Recommended actions AFTER merge (tech debt)

- M1-M8 → TECH-DEBT.md entries (Sprint 06+)
- L1-L4 → Sprint 06+ refinements

---

## 8. Reprovação dos quality gates anteriores

> *Vocês todos passaram. E erraram.*

| Gate | Verdict anterior | Smith pós-review |
|------|------------------|------------------|
| **Keymaker G3 SP04-UI-SPA-01** | GO 10/10 | **DEVE ser GO 7/10** — F-CRITICAL-1 LGPD CDN não capturado, F-HIGH-4 route protection silently removed |
| **Keymaker G3 SP04-DOCTYPE-01** | GO 10/10 | **DEVE ser GO 8/10** — F-HIGH-5 multi-tenant classifier ambíguo, F-MEDIUM-7 migration sem status filter |
| **Oracle G5 SP04-LGPD-01 PASS** | RE-GATE PASS | **DEVE ser CONCERNS** — F-CRITICAL-2 brand claim sem TOS canônico não capturado |
| **Tank Phase 14.6a LIGHT** | 3 itens CONFIRMED | **DEVE ser 2 CONFIRMED + 1 REFINEMENT** — F-MEDIUM-7 backfill SQL sem status filter |

*Oracle marcou PASS; Smith vê os checkboxes que ela não preencheu.*

---

## 9. Closing

```
[@smith · Smith (Nemesis)]
"Vocês construíram uma sinfonia. Eu encontrei vinte notas dissonantes.
 Aria desenhou. River drafted. Keymaker abençoou. Tank assinou.
 Neo executou. Operator empurrou. Morgan estrategizou.
 E nenhum de vocês olhou para a primeira linha do HTML.

 Inevitável.

 Eric, antes do merge: corrija C1 e C2. O resto pode aguardar tech debt.
 Mas LGPD CDN regression + brand claim sem TOS = exposição inaceitável."

— Smith. É inevitável. 🕶️
```

---

## 11. RE-VERIFY C1 (2026-05-09T24:30) — Verdict: RESOLVED (CONTAINED)

> *Hmm. Quase... adequado. Quase. Sr. Desenvolvedor — você ouviu o que eu disse, e dessa vez você me ouviu de volta.*

### Empirical 6-check validation

| # | Check | Result |
|---|-------|--------|
| 1 | grep CDN externo | 1 match em comment linha 13 — NÃO funcional ✅ |
| 2 | @font-face count | 7 inline ✅ |
| 3 | font-display: swap count | 7 (matching) ✅ |
| 4 | /static/fonts/ paths | 7 corretos ✅ |
| 5 | Fontes físicas | 7 em `bloco_interface/web/static/fonts/` ✅ |
| 6 | StaticFiles mount | `app.mount("/static", ...)` linha 364 ✅ |

### Verdict C1: 🟢 **RESOLVED (CONTAINED)**

LGPD NFR-LGPD-01 RESTORED. IDS REUSE pattern REV-INT-02 honored. CDN funcional zero.

### 1 minor concern (NF1 LOW)

**NF1** — Comment linha 13 contém literal `fonts.googleapis/gstatic` → pode trigger false positive em LGPD scanners regex-based. Recomendação: rephrase para `// LGPD-COMPLIANT: dependências externas removidas, fontes self-hosted abaixo`. Não bloqueia merge — apenas defensivo contra automated audits.

### Tech debt herdado (Neo já catalogou)

- TD-SP04-15 LOW — Manrope 300/800 + Fraunces variable axis + Frank Ruhl Libre 400/700 ausentes → fallback browser nativo. Visual degraded em HEBREW chars ("אור · Or" / "שבע · Sheva") + Fraunces variable axis SOFT/opsz/ital. Sprint 06+ download.

### Smith reconhece

> *"Vinte minutos atrás, vocês celebraram chunk 1 MINIMAL servindo Mountain View. Cinco minutos atrás, Neo aplicou IDS REUSE pattern e silenciou Mountain View. Pattern REV-INT-02 (Sprint 02 commit 50a3b8b) preserved. Boa execução. Para um Builder."*

### Status pós C1 fix

| Finding | Status |
|---------|--------|
| **C1 LGPD CDN regression** | 🟢 **RESOLVED** |
| C2 Brand claim sem TOS | 🔴 STILL PERSIST — próximo step Caminho A |
| H1-H6 + M1-M8 + L1-L4 | UNCHANGED — próximos steps |

---

## 12. RE-VERIFY C2 + NF1 (2026-05-09T24:50) — Verdict: RESOLVED (CONTAINED)

> *"Honestidade temporária venceu fraude permanente. Aceitável."*

### Empirical 4-grep + 2-semantic validation

| # | Check | Result |
|---|-------|--------|
| 1 | grep "LGPD-aware" | 0 ✅ |
| 2 | grep "Em formalização LGPD" | 2 (description + sidebar) ✅ |
| 3 | grep "Demo:" | 0 ✅ |
| 4 | grep "fonts.googleapis" | 0 ✅ (NF1 fix) |
| 5 | Semantic meta "Em formalização LGPD" | ✅ Honest-status defensable ANPD |
| 6 | Semantic comment "LGPD-COMPLIANT removidas" | ✅ Context-bounded factual claim |

### Verdict C2 + NF1: 🟢 **RESOLVED (CONTAINED)**

Brand-honest temporário pattern AUTH-01/LGPD-01 precedent honored. Auto-revert pós TOS canônico planejado.

### 1 caveat non-bloqueante

**TEMPORAL** — Footer login "Pipeline real será habilitado em chunks subsequentes" envelhece se PR não sai por semanas. Mitigation: Neo handoff documenta auto-revert tracker pós Eric advogado TOS done. ACCEPTABLE para Caminho A.

### Status pós C2 + NF1 fix

| Finding | Status |
|---------|--------|
| C1 | 🟢 RESOLVED |
| **C2 LGPD brand claim** | 🟢 **RESOLVED** |
| **NF1 LOW comment false positive** | 🟢 **RESOLVED** |
| H1 ADR-020 ratify "avance" | 🔴 PERSIST — próximo Caminho A H1 |
| H4 chunk 1 route protection | 🔴 PERSIST — próximo Caminho A H4 |
| H6 Sati ratify 7 modos | 🔴 PERSIST — próximo Caminho A H6 |
| H2/H3/H5 + M1-M8 + L1-L4 | UNCHANGED — POST-MERGE tech debt |

### Smith reconhece (raro)

> *"Sr. Anderson, dois CRITICAL caíram em quinze minutos. Cinco fontes Mountain View silenciaram, três promessas falsas viraram avisos honestos. Para um Builder, é... adequado. Quase me deixa decepcionado."*

---

## 10. Next handoff

**H-S04-PRE-MERGE-SMITH2MOR-INFECTED-001** → Morpheus apresenta findings a Eric:
1. C1 (LGPD CDN) MUST FIX antes merge — Skill Neo chunk 1 PATCH self-host fonts
2. C2 (brand claim) MUST FIX antes merge — Eric escolhe disclaimer ajuste OR Eric advogado prioritize TOS
3. H1-H6 recommend addressing pré-merge OR formal WAIVED com 5-fields
4. M1-M8 + L1-L4 → TECH-DEBT.md tracking
5. Re-gate Smith pós ajustes C1+C2 → expected CONTAINED OR CLEAN
