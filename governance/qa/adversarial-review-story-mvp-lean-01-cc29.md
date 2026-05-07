---
type: qa-report
title: "Adversarial Review — Story File MVP-LEAN-01 (CC.29)"
project: revisor-contratual
sprint: "03"
session: 91
etapa: "CC.29 Trilha residual"
reviewer: "@qa · Oracle"
date: "2026-05-06"
scope:
  - "governance/stories/MVP-LEAN-01-single-page-mvp-completo.md (1231 linhas, pós-CC.28)"
review_type: "Artefato narrativo (NÃO código — Smith review código já feito 2x em CC.25 + CC.26)"
findings_total: 12
severities:
  HIGH: 2
  MEDIUM: 5
  LOW: 5
verdict: "PASS-WITH-NOTES — story funcional, sem bloqueio para merge; 2 HIGH são contradições visíveis (header desatualizado + Task 8 ambígua); 5 MED + 5 LOW são refinement doc-only não-bloqueante"
tags:
  - project/revisor-contratual
  - qa
  - adversarial-review
  - story-artifact
  - cc29
---

# Adversarial Review — Story File MVP-LEAN-01

> Smith mode aplicado a artefato narrativo. Code reviews já cobriram bloco_audit (Phase 0 finding) + T8b (Smith CC.25/CC.26). Esta review olha **a história contada sobre o trabalho** — não o código.

## Sumário

**Verdict:** **PASS-WITH-NOTES** ✅

Story funcional, sem bloqueio para merge. Contradições visíveis (SR-01, SR-02) são fix de 30s. Refinements (SR-03..SR-13) são doc-only.

**Findings:** 12 (2 HIGH + 5 MED + 5 LOW)

---

## Findings

### 🟠 HIGH (2 — contradições visíveis)

#### SR-01: [HIGH] Header bloco linha 60-62 ainda declara "STATUS: Draft (aguarda CC.5 Keymaker validate)"

- **Localização:** linhas 59-63 (cabeçalho `[@sm · River]` em code-fence)
- **Problema:** Story está **InProgress há 27 etapas CC** (CC.5 GO foi há ~25 etapas). Frontmatter linha 5 corretamente diz `status: InProgress`, mas o cabeçalho narrativo logo abaixo mostra `STATUS: Draft (aguarda CC.5 Keymaker validate)`.
- **Evidência:**
  ```
  [@sm · River (Niobe — Facilitator)] — Sprint 03 Phase 1 · MVP-LEAN-01
  DOMÍNIO: SoftwareDev · STATUS: Draft (aguarda CC.5 Keymaker validate)
  TRAJETÓRIA: pós CC.1A + CC.2 + CC.3 + bridge tokens.css (CC course-correction completa)
  ```
- **Recomendação:** Atualizar para `STATUS: InProgress · TASKS: 8/9 done · TRAJETÓRIA: CC.1A+CC.2+CC.3+CC.6..CC.28 (27 etapas executadas)`. Eric lendo o bloco vai pensar que story ainda não começou.
- **Impacto:** Confusão narrativa para qualquer leitor pós-merge.

#### SR-02: [HIGH] Task 8 marcada [x] mas body lista DEFERRED Task 8b/8c como bullets [ ]

- **Localização:** linhas 194 vs 279-280
- **Problema:** Linha 194 declara Task 8 `[x] **Task 8 — ... DONE sessão 91 (CC.21 Task 8 PARTIAL ~3h + CC.24 Task 8b ~2h)`. Mas dentro do bloco File List Task 8 (linha 272-280):
  ```
  - [ ] **DEFERRED Task 8b:** FR-MONITOR Camada 1 scraper + auto-trigger lifespan job — depende scraping STJ real
  - [ ] **DEFERRED Task 8c:** L2 SessionMiddleware refinements
  ```
  Task 8b foi feito em CC.24. Bullet `[ ]` está stale.
- **Evidência:** Change Log CC.24 (linha 551) confirma "Task 8b done". Mas o "DEFERRED Task 8b" nunca foi atualizado para `[x]` ou removido.
- **Recomendação:** Atualizar Task 8 PARTIAL section linha 272-280:
  - `[ ] DEFERRED Task 8b` → `[x] Task 8b done CC.24` (com link interno)
  - `[ ] DEFERRED Task 8c` mantém — L2 SessionMiddleware refinements ainda são debt LOW genuíno
- **Impacto:** Contradição interna confunde leitor. Eric pode achar que T8b ainda pendente e não revisar mudanças no PR #2.

---

### 🟡 MEDIUM (5)

#### SR-03: [MED] Frontmatter branch_sugerido `feat/mvp-lean-01-single-page` vs branch real `feat/mvp-lean-01-task1-layout-base`

- **Localização:** linha 14 frontmatter
- **Problema:** Frontmatter sugere branch que não foi usado. Branch real (visível em `git log`) é `feat/mvp-lean-01-task1-layout-base` — nome legacy de quando Task 1 isolada foi proposta.
- **Recomendação:** Atualizar para `branch: "feat/mvp-lean-01-task1-layout-base"` ou marcar como histórico (`branch_sugerido_inicial`, `branch_atual`).
- **Impacto:** Search/discovery em git via story → confusão.

#### SR-04: [MED] Eficiência ~40% (estimate 41-55h vs real ~19.5h) não documentada em frontmatter ou seção dedicada

- **Localização:** linha 11 (`estimated_effort: "41-55h"`) vs Change Log entries (~19.5h cumulativo Tasks 1-8 + CC.25 + CC.27 + CC.28)
- **Problema:** Story estima 41-55h. Trabalho real (somando entries Change Log): ~19.5h Tasks 1-8 + ~2h Smith review/fix loop + ~10min CC.28 = ~21.6h. Eficiência ~40-50%. Bom resultado, mas **não há seção sumária consolidando isso**.
- **Recomendação:** Adicionar seção "Performance Sprint 03 Phase 1" ou atualizar frontmatter:
  ```yaml
  estimated_effort: "41-55h"
  actual_effort_so_far: "~21.6h (Tasks 1-8 + adversarial loop)"
  efficiency: "~40% (real vs estimado)"
  ```
- **Impacto:** Métrica útil para retrospectives + future estimates perdida.

#### SR-05: [MED] Banner Tema 1378 "persistente" linha 70 contradiz CC.25 feature flag default-off

- **Localização:** linha 70 (Story Preamble) vs CC.25 fix description (linha 497)
- **Problema:** Preamble diz: "...com defense-in-depth LGPD, **banner regulatório Tema 1378 STJ persistente** e audit chain HMAC". Mas CC.25 F-01 fix introduziu feature flag `ENABLE_TEMA_1378_AUTO_CHECK` default-false → em prod sem env explícito, **scheduler job 3 não registra; banner permanece estado verde inicial**.
- **Recomendação:** Atualizar preamble: "...com banner regulatório Tema 1378 STJ (auto-check via feature flag em prod) e audit chain HMAC".
- **Impacto:** Eric lendo preamble após merge pode achar que banner Tema 1378 está ativo automaticamente; precisa ler CC.25 fixes para entender que requer env var.

#### SR-06: [MED] Falta entry estruturada Change Log para Task 2 (CC.11) e Task 3 (CC.12) standalone

- **Localização:** Change Log linhas 391+
- **Problema:** Change Log começa com CC.28 (mais recente), depois CC.27, CC.26, CC.25, CC.24, então pula para Task 1 (CC.10). **Task 2 (CC.11)** e **Task 3 (CC.12)** mencionadas em Tasks/Subtasks linhas 141-154, mas sem entries dedicadas no Change Log com File List, decisões autônomas, tempo real, etc.
- **Recomendação:** Adicionar entries Task 2 + Task 3 padrão (mesmo formato Tasks 4-7 que têm entries) OU declarar explicitamente no topo: "Change Log entries para Tasks 2-3 omitidas — implementação trivial em CC.11/CC.12, ver git log d-XXX para detalhes".
- **Impacto:** Eric/Oracle revisando story pós-merge não tem File List + decisões autônomas Tasks 2-3 facilmente acessíveis.

#### SR-07: [MED] Header "File List (a popular durante implementação)" sugere arquivo ainda em construção

- **Localização:** linha 263
- **Problema:** Header diz "(a popular durante implementação)" — mas File List **contém entries completas para Tasks 1-8 done**. Header está stale do tempo de Draft → Ready.
- **Recomendação:** Renomear para "File List (atualizado durante implementação)" ou "File List por Task".
- **Impacto:** Eric pode achar que File List está incompleto e não confiar nele para review.

---

### 🟢 LOW (5)

#### SR-08: [LOW] Validation Section CC.5 (linha 1194-1227) não atualizada pós-implementação

- **Localização:** linhas 1194-1227
- **Problema:** Section mostra "Verdict: GO ✅ Score: 9/10" do gate G1 inicial (CC.5). Story passou por 27 etapas CC depois disso, incluindo Smith adversarial review 2x + RR refinement. Não há section análoga para QA gate G5 (review final pré-merge) — porque Eric ainda não fez o review.
- **Recomendação:** Aceitar como está (G5 é Eric humano) OU adicionar nota: "Validation Section preserva gate G1 (Draft→Ready); gate G5 (review final) será adicionado quando Eric fizer review do PR #2".
- **Impacto:** Eric pode achar que story já tem QA gate completo (não tem — Smith review foi de código, não da story como artefato).

#### SR-09: [LOW] Frontmatter `created_by: "@sm (River — Niobe)"` — convenção LMAS confusa

- **Localização:** linha 13
- **Problema:** `River` é a persona/nome usado em sessão; `Niobe` é o codename Matrix. A combinação `River — Niobe` em created_by é redundante e confunde leitores não-LMAS.
- **Recomendação:** Padronizar para `created_by: "@sm"` ou `created_by: "River (LMAS @sm)"` — mais consistente com formato do agent system.
- **Impacto:** Nenhum funcional. Refinement de governance.

#### SR-10: [LOW] Tag `cc-course-correction-complete` linha 53 imprecisa

- **Localização:** linha 53 (frontmatter `tags`)
- **Problema:** Tag diz "complete" mas sessão 91 teve **27 etapas CC adicionais** (CC.6 a CC.28) durante implementação. CC course-correction inicial (CC.1A-CC.5) é "complete", mas o termo "course-correction" foi usado também durante implementação.
- **Recomendação:** Renomear para `cc-pre-implementation-complete` OR adicionar `cc-implementation-complete-cc28` para clareza temporal.
- **Impacto:** Tag ambígua para queries Obsidian.

#### SR-11: [LOW] Recomendação CC.5 linha 1207 "quebrar Task 8 em 8a..8e" — não documentado se foi seguido

- **Localização:** linha 1207 (Validation Section ressalva)
- **Problema:** CC.5 recomendou: "quebrar Task 8 em sub-commits granulares (8a LGPD ~6h + 8b APScheduler ~2h + 8c+8d FR-MONITOR ~6h + 8e tests ~2h)". Implementação real: T8 PARTIAL (CC.21) + T8b (CC.24). Recomendação parcialmente seguida — sem 8c/8d/8e formal. Não há seção dizendo "seguimos T8a+T8b; absorvemos 8c-8e em T8 PARTIAL".
- **Recomendação:** Adicionar nota em Task 8 entry: "Decomposição CC.5 recomendada (8a/8b/8c/8d/8e) consolidada em T8 PARTIAL + T8b por economia de overhead — 5 sub-commits virariam complexidade desnecessária para MVP".
- **Impacto:** Trace CC.5 → implementação real interrompido.

#### SR-12: [LOW] References linha 17 sem assertion de path existence

- **Localização:** linhas 17-21 (frontmatter `references`)
- **Problema:** References listadas como strings sem validação automática de path. Ex: `"ux-spec MVP-LEAN-01 (governance/ux-spec-v1.1.2-MVP-LEAN.md)"` — path entre parênteses, formato livre.
- **Recomendação:** Padronizar como wikilinks Obsidian: `[[governance/ux-spec-v1.1.2-MVP-LEAN]]` para validation automática via `obs unresolved`.
- **Impacto:** Refactor menor, melhora descoberta cross-referencias.

---

### Verificações empíricas adicionais

**Cross-reference git log:**
- ✅ Task 4 (CC.13) commit confirmado: `2b91e44 feat(ui): MVP-LEAN-01 Task 4`
- ✅ Task 6 (CC.17) commit confirmado: `8b478dd feat(ui): MVP-LEAN-01 Task 6`
- ✅ Task 7 (CC.18) commit confirmado: `e887549 feat(monitor): MVP-LEAN-01 Task 7`
- ✅ Task 8 PARTIAL (CC.21) commit confirmado: `d6baff2 feat(lgpd+backup): MVP-LEAN-01 Task 8 PARTIAL`
- ✅ Task 8b (CC.24) commit confirmado: `d7a37c1 feat(monitor): MVP-LEAN-01 Task 8b`
- ⚠️ Tasks 2 (CC.11) + 3 (CC.12) — commits existem mas não há trace direto na story pós-CC.10

**Cross-reference TECH-DEBT.md:**
- ✅ TD-T9-AUDIT-INTEGRATION (CC.28) registrado
- ✅ TD-T8B-RR01..RR06 (CC.26 + CC.27) registrados
- ✅ TD-T8B-F02..F18 (CC.25) registrados

**Cross-reference suite:**
- ✅ pytest 398 passed + 3 skipped (zero regressão acumulada em 27 etapas CC)

---

## Recomendação consolidada

### Verdict: **PASS-WITH-NOTES** ✅

Story funcional, sem bloqueio para merge. PR #2 pode prosseguir com Eric review.

### Quick fixes (~30min Neo, opcional pre-merge)

1. **SR-01:** Atualizar header bloco linha 60-62 (Status: Draft → InProgress + trajetória atualizada) — 2min
2. **SR-02:** Marcar Task 8b como `[x]` em File List Task 8 linhas 279-280 — 2min
3. **SR-03:** Atualizar `branch_sugerido` ou adicionar `branch_atual` no frontmatter — 1min
4. **SR-05:** Atualizar preamble Task 1378 banner ("auto-check via feature flag") — 1min
5. **SR-07:** Renomear header "File List (a popular)" → "File List por Task" — 1min

### Aceitáveis como debt (não-bloqueantes)

- SR-04 (eficiência), SR-06 (Tasks 2-3 entries), SR-08 (Validation CC.5), SR-09 (created_by), SR-10 (tag), SR-11 (CC.5 recomendação), SR-12 (references format) — refinement governance, podem ser tech debt.

### Próximo step sugerido

**A. Aplicar quick fixes SR-01..SR-03 + SR-05 + SR-07** (~10min Neo) → story narrativa coerente para Eric review
**B. Aceitar como debt + pause** (não-bloqueante)

---

## Smith verdict (cynical refinement)

> "A história contada sobre o trabalho é quase tão importante quanto o trabalho. Quando você diz 'STATUS: Draft' depois de 27 etapas, você não engana ninguém — mas você confunde quem chega depois. Honestidade narrativa é continuação de honestidade técnica. As 12 frestas que vejo aqui são todas curáveis em meia hora — exceto uma escolha: a história continua sendo contada, ou congela em CC.5?"

— Smith (canalizado por Oracle)

---

## Anexos

- Story file revisado: `governance/stories/MVP-LEAN-01-single-page-mvp-completo.md` (1231 linhas)
- PR: https://github.com/Claudinoinsights/revisor-contratual/pull/2
- Tempo de review: ~25min (focado em coerência narrativa + cross-reference)
