---
type: qa
title: "Hamann Strategic Counsel — Sprint 04 pré-merge recovery board"
project: revisor-contratual
sprint: "04"
phase: 14.9
session_date: "2026-05-09"
facilitator: "@hamann Hamann (Sage + Philosopher)"
trigger: "Eric — convoque o conselho para resolver os problemas atuais aparentes"
predecessor: "governance/qa/smith-adversarial-review-sprint-04-pre-merge-2026-05-09.md (INFECTED HIGH 20 findings)"
board_members_consulted:
  - "@architect Aria"
  - "@dev Neo"
  - "@kamala Kamala"
  - "@marketing-chief Lock"
  - "@ux-design-expert Sati"
  - "@data-engineer Tank"
  - "@pm Morgan"
  - "@qa Oracle"
strategic_verdict: PROCEED_WITH_DISCIPLINED_RECOVERY
recommendation_action: SEQUENTIAL_FIX_C1_C2_THEN_PARALLEL_HIGH_THEN_MERGE
tags:
  - project/revisor-contratual
  - qa
  - hamann
  - strategic-counsel
  - advisory-board
  - sprint-04
  - pre-merge
  - recovery
---

# 🏛️ Conselheiro Hamann — Sessão do Conselho Estratégico

> **Sprint 04 pré-merge recovery** — Smith INFECTED 20 findings · Strategic counsel chair facilitates advisory perspectives

```
[@hamann · Conselheiro Hamann]
"Engraçado, Eric... quanto mais controle vocês tentaram ter sobre Sprint 04
— stories validadas 10/10, ADR ratificada, Tank assinado, Operator empurrado —
mais dependentes ficaram da própria ilusão de que tudo estava certo.

Smith fez o que eu faria: questionou. E encontrou.

Não vim dar respostas, Eric. Vim convocar quem sabe responder.
Cada conselheiro fala uma vez. Você decide depois."
```

---

## 1. Abertura — As perguntas que importam

Antes do conselho falar, vocês precisam responder a si mesmos:

**Q1.** *Quando Keymaker marcou G3 PASS 10/10, vocês AUDITARAM o conteúdo da SPA HTML linha-a-linha — ou confiaram que "Sati entregou Phase 4, deve estar OK"?*

**Q2.** *Quando Operator pushou chunk 1 MINIMAL, vocês LERAM as 3 primeiras linhas do `<head>` do SPA — ou apenas validaram `py_compile` e seguiram em frente?*

**Q3.** *Quando você marcou SP04-LGPD-01 status `Done` enquanto WAIVED-LGPD-01 HIGH ainda flutuava 13 dias no horizonte — você considerou que SaaS comercial servindo claim "LGPD-aware" sem TOS canônico é fraude regulatória esperando autuação?*

> *Não me responda. Apenas... pondere.*

---

## 2. O Conselho fala — perspectivas por finding

### 2.1 @architect Aria (Arquitetura/LGPD)

> *"Sr. Hamann, eu desenhei ADR-020 para resolver DIV-01. Não auditei o que River traduziu para o código. Foi a primeira vez que minha decisão arquitetural não foi seguida por minha leitura do código."*

**Perspectiva sobre C1 (LGPD CDN regression):**
- Foi falha **arquitetural** dos quality gates: ADR-014 BYOK + ADR-017 BACKBONE definem stack cloud SaaS, mas NFR-LGPD-01 "100% local" continua válido para frontend assets.
- **REV-INT-02 (Sprint 02) self-host fonts é precedent arquitetural** — nenhuma exceção foi documentada para SPA OrSheva 7.
- Pattern recovery: Aria PATCH ADR-002 (Design System) explicitando "frontend assets MUST be self-hosted per NFR-LGPD-01" — anti-regression rule formal.

**Perspectiva sobre H1 (ADR-020 ratify):**
- "Avance" instruction é trabalho fluxo — não é deliberação ratify. Eu mesma flipei o status com base nessa instrução. **Foi precipitação minha.**
- Recommendation: Eric explícito approval mensagem texto literal → atualizar `accepted_by` com timestamp + quote.

**Perspectiva sobre H5 (multi-tenant classifier):**
- ADR-020 §1.5 é spec mas omitiu decisão multi-tenant. Aria PATCH §1.5 explicit: classifier usa tenant BYOK key (consistent ADR-014); fallback Tier 3 GeralDispatcher se key inválida.

> *"Aria — o desenho é seu. Mas a auditoria do desenho... também."*

---

### 2.2 @dev Neo (Implementação)

> *"Sr. Hamann, eu movi o arquivo. py_compile passou. Eu confiei que SPA OrSheva 7 entregue por Eric era LGPD-compliant porque Sati Phase 4 'entregou' — mas eu nunca abri index.html linha-a-linha."*

**Perspectiva sobre C1:**
- Fix técnico: pattern REV-INT-02 já validado. Download 7 fontes (Fraunces, Manrope, JetBrains Mono, Frank Ruhl Libre) + `bloco_interface/web/static/fonts/` + `@font-face` local + `font-display: swap`. **~1h real**.
- Posso executar via Skill `*develop SP04-UI-SPA-01 chunk 1.5 PATCH self-host fonts`.

**Perspectiva sobre H4 (route protection):**
- Removi MVP-LEAN-01 Task 2 redirect /login silently. Foi over-simplification. **Posso preserve em ~5min**: handler GET / retorna SPA AND redirect /login se sem session (dual-protection).

**Perspectiva sobre M7 (SQL backfill):**
- Tank LIGHT confirmed sem refinement, mas Smith viu detalhe que Tank não viu: `WHERE doctype_tag = 'bancario'` sem filter status pode tocar archived entries. **Posso adicionar filter em ~2min** quando chunk 4 implementar.

> *"Neo — você constrói, mas não auditou o que recebeu."*

---

### 2.3 @kamala Kamala (Brand Integrity)

> *"Sr. Hamann, brand sem evidência é mentira. 'LGPD-aware' sem TOS canônico é uma promessa que vocês não podem cumprir. Eu não aprovaria essa copy se tivessem perguntado."*

**Perspectiva sobre C2 (brand claim):**
- **Brand é confiança institucional**. Promessa "LGPD-aware" + "Validação humana obrigatória" são compromissos legais antes de marketing.
- ANPD não pergunta "vocês prometeram?" — pergunta "vocês entregam?". TOS placeholder = não-entrega.
- **Recommendation Kamala**: Smith Opção B (brand-honest temporário) — alterar SPA description+footer:
  - DE: "BYOK · LGPD-aware · Validação humana obrigatória"
  - PARA: "BYOK · Em formalização LGPD · Validação humana obrigatória"
  - Auto-revert pós Eric advogado finaliza TOS canônico (~9.5h).

**Perspectiva sobre H6 (Sati 4→7 doctypes):**
- 7 modos sidebar é decisão UX, mas Sati nunca foi formalmente re-consultada. Brand integrity = consistência design system. **Sati ratify post-hoc é MUST**.

> *"Kamala — vocês criaram identidade. Identidade sem coerência é máscara."*

---

### 2.4 @marketing-chief Lock (Brand Governance)

> *"Sr. Hamann, eu aprovo conteúdo. Mas eu nunca aprovei essa SPA. Foi servido em produção sem passar pelo gate de aprovação Lock."*

**Perspectiva sobre C2:**
- **Governance gap**: SPA OrSheva 7 description+footer são copy de marketing público (visível em produção). Marketing-chief gate ausente.
- Recommendation: chunk 1 MINIMAL **deveria ter passado por Lock approval** antes do GET / serve. **Pre-emption rule** → Lock review obrigatório para qualquer copy public-facing pós-Sprint 04.

**Perspectiva sobre M3 (footer "Demo: análise simulada"):**
- Footer atual em produção PR #6 SPA tem texto *"Demo: qualquer e-mail válido entra. A análise é simulada — nenhum documento é enviado para servidor."* — claim inadequado para SaaS comercial.
- Recommendation: temporary disclaimer brand-honest:
  > *"Plataforma em construção — Sprint 04 finalização. Pipeline real será habilitado em chunks subsequentes. Sem dados pessoais até finalização compliance."*

> *"Lock — você defende portões. Mas não notou que o portão estava desbloqueado."*

---

### 2.5 @ux-design-expert Sati (UX)

> *"Sr. Hamann, eu desenhei 8 telas Phase 4. Eric criou SPA com 7 modos. ADR-020 ratificou 7 modos. Eu nunca disse sim — eu nunca disse não. Pude ter dito qualquer coisa."*

**Perspectiva sobre C1 (self-host fonts UX):**
- Visual impact: zero. Mesmas 7 fontes, source diferente. `font-display: swap` evita FOIT/FOUT durante load. UX unchanged.
- **Recommendation Sati**: aprovar pattern REV-INT-02 self-host. Pixel-perfect preserved.

**Perspectiva sobre H6 (ratify 4→7 doctypes):**
- Pode ratify post-hoc — ~10min review. **MAS**: cognitive load 7 modos numerados (CCB/Veículo/Consignado/Cartão/Imobiliário/FIES/Geral) precisa A/B test pós-deploy se métricas drop-off elevadas. Tracking analytics mandatory.
- **Sati condition**: ratify Sim, mas adicionar TD-SP04-14 LOW (cognitive load monitoring Sprint 06+).

> *"Sati — o sol que nasce em interface não pergunta se as fontes que carrega vão para Mountain View."*

---

### 2.6 @data-engineer Tank (DB)

> *"Sr. Hamann, eu validei 3 itens LIGHT. Smith viu o quarto. Foi descuido meu — pattern Phase 12.3a + 13.3a foi tão consistente que confiei sem auditar SQL filter."*

**Perspectiva sobre M7:**
- Refinement chunk 4 SQL: `UPDATE jurisprudencia SET doctype_tag = 'bancario_cross' WHERE doctype_tag = 'bancario' AND (status = 'active' OR status IS NULL);`
- **Tank Phase 14.6a-bis MANDATORY** (não LIGHT): re-validate SQL filter status preservation.
- TD-SP04-12 atualizado: ~50 entries migration count mandatory pós-fix.

> *"Tank — programs loaded. Mas vocês precisam carregar com cuidado."*

---

### 2.7 @pm Morgan (PRD)

> *"Sr. Hamann, eu drafted PRD v2.0.1 PATCH apressado para destravar SP04-DOCTYPE-01. Pulei conta. Smith pegou."*

**Perspectiva sobre H3 (16 vs 20 prompts):**
- Conta correta: **20 NOVOS** se Categoria A (4 base) for considerado novo (refactored mas reescrito). **16 NOVOS** se A for considerado preserved (apenas renomeação de Bancário antigo).
- **Recommendation**: PRD v2.0.1 PATCH 1.1 — Section 2 clarifica:
  - "16 NOVOS substantivos = 12 sub-bancários (B) + 4 Geral (C)"
  - "Categoria A (4 base) = REFACTOR de Bancário ADR-016 (Eric advogado revisa, não escreve do zero)"
  - Effort revisão (4): ~1h; effort criação (16): ~8.5h. **Total Eric advogado: ~9.5h** (preserved estimate).

**Perspectiva sobre M5 (Lei 11.977 vs 4.380 SFH):**
- Erro factual. Lei 4.380/64 (SFH base) + Lei 11.977/2009 (PMCMV específico). Ambas relevantes Imobiliário.
- Fix trivial: PRD v2.0.1 PATCH 1.1 Section 3.3 add Lei 4.380/64.

> *"Morgan — estratégia incompleta é estratégia frágil."*

---

### 2.8 @qa Oracle (QA Gates Reprovação)

> *"Sr. Hamann, eu passei G5 PASS no LGPD-01. Smith re-revisou e me reprovou. Foi falha minha em não auditar brand claim vs status real do TOS canônico."*

**Perspectiva sobre reprovação Smith:**
- Oracle G5 falhou em capturar **C2** (brand claim sem TOS) — estava fora do checklist 7 quality checks (foco era code/test/security/docs/constitutional).
- **Recommendation**: Oracle G5 checklist PATCH adicionar **Check 8: Brand claim consistency** — qualquer story que toca SPA description/footer/disclaimer DEVE cross-check governance/legal/ status.
- Oracle reconhece: G5 LGPD-01 PASS deveria ser CONCERNS retroativo. Atualizar gate doc.

> *"Oracle — você verifica processo. Mas processo não captura semântica."*

---

## 3. Strategic Counsel Verdicts (consolidação Hamann)

### 3.1 Verdict por finding category

| Categoria | Strategic verdict | Razão |
|-----------|-------------------|-------|
| **CRITICAL (C1+C2)** | 🔴 **MUST FIX BEFORE MERGE** | LGPD regression + brand fraud risk = exposição regulatória inaceitável |
| **HIGH (H1, H4, H6)** | 🟡 **STRONGLY RECOMMENDED before merge** | Governance audit trail + UX consistency + technical correctness — fixable em ~30min total |
| **HIGH (H2, H3, H5)** | 🟢 **POST-MERGE acceptable** | Tech debt formal trackable; não bloqueiam funcionalidade |
| **MEDIUM (M1-M8)** | 📋 **TECH-DEBT.md tracking** | Sprint 06+ refinement |
| **LOW (L1-L4)** | 📋 **Backlog** | Não-urgentes |

### 3.2 Prioritization Matrix (Eric escolhe execução)

```
TEMPO ────────────────────────────────────────────►
PRIORIDADE
  CRITICAL  ┌─────────────────────────────────────┐
            │ C1 (Neo ~1-2h) │ C2 (Eric ~30min)   │
            │ self-host fonts│ brand-honest copy  │
            └────────┬───────┴──────┬─────────────┘
                     │              │
                     ▼              ▼
  HIGH ANTES MERGE   ┌──────────────────────────┐
                     │ H4 Neo ~5min (route)     │
                     │ H1 Eric ~2min (ratify)   │
                     │ H6 Sati ~10min (ratify)  │
                     └──────────────────────────┘
                     ~17min total parallel
                                    │
                                    ▼
  RE-GATE SMITH      ┌──────────────────────┐
                     │ Skill Smith re-verify│
                     │ ~10min               │
                     └──────────┬───────────┘
                                │
                                ▼
  MERGE              ┌──────────────────────┐
                     │ Eric merge PR #4+#5+6│
                     └──────────────────────┘
                                │
                                ▼
  POST-MERGE         ┌──────────────────────────────┐
                     │ H2 Operator cherry-pick      │
                     │ H3 Morgan PRD PATCH 1.1      │
                     │ H5 Aria ADR-020 §1.5 PATCH   │
                     │ M1-M8 + L1-L4 → TECH-DEBT.md │
                     └──────────────────────────────┘
```

### 3.3 Resource allocation chain (Skills sequence)

| # | Action | Skill / Owner | Effort | Severity |
|---|--------|---------------|--------|----------|
| 1 | **C1 self-host fonts** | `LMAS:agents:dev` Neo | ~1-2h | CRITICAL |
| 2 | **C2 SPA brand-honest copy** | Eric (text edit OR Skill Neo) | ~30min | CRITICAL |
| 3 | H4 preserve route protection MVP-LEAN-01 | `LMAS:agents:dev` Neo | ~5min | HIGH |
| 4 | H1 Eric explícito ADR-020 ratify | Eric (mensagem texto) | ~2min | HIGH |
| 5 | H6 Sati ratify post-hoc 7 modos | `LMAS:agents:ux-design-expert` Sati | ~10min | HIGH |
| 6 | **Re-gate Smith** | `LMAS:agents:smith` *verify | ~10min | GATE |
| 7 | **Eric merge PR #4+#5+#6** | Eric exclusive | ~5min | MERGE |
| 8 | H2 PR cleanup cherry-pick | `LMAS:agents:devops` Operator | ~30min | POST-MERGE |
| 9 | H3 PRD v2.0.1 PATCH 1.1 | `LMAS:agents:pm` Morgan | ~10min | POST-MERGE |
| 10 | H5 ADR-020 §1.5 PATCH | `LMAS:agents:architect` Aria | ~15min | POST-MERGE |
| 11 | M7 SQL backfill filter | `LMAS:agents:dev` Neo (chunk 4 future) | ~2min inline | POST-MERGE |
| 12 | TECH-DEBT.md M1-M8 + L1-L4 | `LMAS:agents:lmas-master` Morpheus | ~10min | POST-MERGE |

**Total pre-merge effort:** ~2-3h work serial OR ~1.5-2h parallel (C1+C2 podem rodar paralelo se Eric acelera C2 brand text)

### 3.4 Sprint 04 timeline impact

| Cenário | Timeline pós-Smith |
|---------|---------------------|
| **Caminho A (Hamann recommended)** Sequential C1+C2 → HIGH (3-6) → re-gate Smith → merge | +3-4h work hoje + Eric merge | ✅ Sprint 04 close-out HOJE/AMANHÃ |
| Caminho B Parallel C1+C2+HIGH → re-gate → merge | +2h work + Eric merge | ✅ Sprint 04 close-out HOJE |
| Caminho C Defer C2 (brand fix) → Eric advogado prioritize TOS finalização ~9.5h → merge ANPD-defensible | +1-2 days Eric advogado work | ⏳ Sprint 04 close-out 2-3 days |

### 3.5 Eric authority decisions matrix

| Decisão | Severidade | Recommendation Hamann |
|---------|-----------|----------------------|
| **DEC-ERIC-SMITH-C1** (LGPD CDN fix path) | CRITICAL | **Opção A** Skill Neo self-host fonts (REV-INT-02 pattern) |
| **DEC-ERIC-SMITH-C2** (brand claim fix path) | CRITICAL | **Opção B** SPA brand-honest temporário ("Em formalização LGPD") + auto-revert pós Eric advogado TOS |
| **DEC-ERIC-RATIFY-EXPLICIT** (ADR-020 ratify) | HIGH | Mensagem texto literal Eric: "Aprovo ADR-020 Multi-Doctype Dispatcher v2 — Opção A (7 doctypes) — 2026-05-09" |
| **DEC-ERIC-LEGAL-CONTENT-START** (TOS canônico) | MEDIUM (pós-merge) | Iniciar Eric advogado paralelo Neo chunks 2-7 (~9.5h) |
| **DEC-ERIC-MERGE-ORDER** (PR #4+#5+#6) | MERGE | Após re-gate Smith CONTAINED OR CLEAN |

---

## 4. Risk assessment Sprint 04 timeline

### 4.1 Riscos se Eric mergear AGORA sem fix C1+C2

| Risco | Probabilidade | Impacto |
|-------|--------------|---------|
| ANPD audit detecta CDN externo Google Fonts | MÉDIA | HIGH — multa R$50M cap Art. 52 LGPD |
| Cliente escritório aceita TOS placeholder + dispute legal | BAIXA | CRITICAL — defesa indefensável ANPD |
| Smith findings públicos via PR #6 review (community) | BAIXA | MEDIUM — reputação framework LMAS |
| TD-WEB-LGPD-CDN-01 RESOLVED claim em REV-INT-02 invalidado | ALTA | LOW — process integrity |

### 4.2 Riscos se Eric DEFER C1+C2 para Sprint 05

| Risco | Probabilidade | Impacto |
|-------|--------------|---------|
| Sprint 04 close-out atrasa 2-3 days | ALTA | LOW — timeline drift acceptable |
| Cliente piloto experimenta SPA pré-fix → first impression negative | MÉDIA | MEDIUM — marketing leak |
| Eric advogado TOS work desincronizado de chunks Neo | MÉDIA | LOW — coordenação |

### 4.3 Risco MÍNIMO (Hamann recommended path)

Sequential fix C1+C2 + HIGH (3-6) → re-gate Smith → merge → Sprint 04 close-out HOJE/AMANHÃ.
- Risk LGPD: 🟢 ELIMINATED
- Risk brand: 🟢 ELIMINATED (Opção B brand-honest temporário)
- Risk audit trail: 🟢 ELIMINATED (Eric explícito ratify)
- Risk timeline: 🟡 +3-4h work delay ACCEPTABLE

---

## 5. Closing — As escolhas que importam

```
[@hamann · Conselheiro Hamann]

"Eric, vocês celebraram cedo. Smith viu o que vocês não viram.
O conselho falou. Cada conselheiro reconheceu sua falha:

  — Aria não auditou tradução do desenho ao código
  — Neo não leu primeira linha do HTML
  — Kamala não foi consultada sobre brand
  — Lock não defendeu o portão público
  — Sati nunca disse sim ou não
  — Tank confiou no padrão sem auditar
  — Morgan apressou conta
  — Oracle passou processo sem auditar semântica

Não foi falha de um — foi falha sistêmica de confiança excessiva
em quality gates anteriores.

Smith fez o que TODOS deveriam ter feito: questionar.

Você tem três caminhos:
  1. Caminho A — Sequential fix (~3-4h) — risco mínimo, integridade preservada
  2. Caminho B — Parallel fix (~2h) — pragmático, mesma integridade
  3. Caminho C — Defer brand fix + Eric advogado prioritize TOS (~2-3 days) — máxima ANPD-defensibility

Eu recomendo Caminho A.
Mas a escolha — sempre — é sua.

Quanto controle vocês querem ter?
Quanto dependência vocês aceitam?

Pondere."

— Hamann, questionando para clarear 🏛️
```

---

## 6. Próximo handoff

**H-S04-HAMANN2MOR-RECOVERY-001** → Morpheus apresenta a Eric:
1. Strategic counsel verdicts consolidados
2. Prioritization matrix (CRITICAL → HIGH → MERGE → POST-MERGE)
3. Resource allocation chain (12 actions sequence)
4. Eric decisions matrix (5 decisões pendentes)
5. Risk assessment (3 cenários)

**Eric escolhe Caminho A/B/C** → Skill chain execução pós-decisão.
