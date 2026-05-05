---
type: story
id: DOCS-02
title: "Atualização docs operacionais pós ADR-010 (README LLM Strategy + SOP-revisar-pdf cross-refs)"
status: Done
priority: alta
sprint: "02"
completed: "2026-05-05"
closed_at_sha: "8b37513"
epic: "Sprint-02-release-v0.2.0"
owner: "@dev (Neo)"
estimated_effort: "1-2h"
created: "2026-05-05"
created_by: "@sm (River)"
predecessor_handoff: ".lmas/handoffs/handoff-morpheus-to-sm-2026-05-05-docs02-create-story.yaml"
predecessor_story: "REV-LLM-01 (Done — commit 20d4459 + closure 8eea89c)"
predecessor_adr: "governance/architecture/adr/adr-010-sabia-q4-mitigation.md (Accepted Eric)"
resolves: []
unblocks:
  - "Story UI-1 production-grade (pipeline real referencia SOP atualizado)"
  - "Release v0.2.0 gate condition #7 (docs alignment com ADR-010)"
tags:
  - project/revisor-contratual
  - story
  - sprint-02
  - docs-02
  - documentation
  - adr-010
---

# Story DOCS-02 — Atualização docs operacionais pós ADR-010

## Story

**Como** novo operador (ou Eric retomando o projeto após meses) lendo o README ou SOP de revisão de PDF,
**Eu quero** que a documentação reflita o estado real pós-ADR-010 (Qwen 7B default + Sabia opt-in via `LLM_TIER=premium`),
**Para que** eu não execute o pipeline com expectativas erradas (esperando Sabia como default e tendo `citacao_textual="..."` 3 chars FAIL surpresa) e tenha caminho claro de upgrade GPU documentado.

---

## Contexto

REV-LLM-01 (Done sessão 86, commit `20d4459` + closure `8eea89c`) implementou ADR-010 Path C — fallback para Qwen 2.5 7B como default do Advogado em CPU, preservando Sabia-7B como opt-in via `LLM_TIER=premium`. Smoke INTEGRAL passou em 253.72s (citacao_textual ≥10 chars confirmado).

**Documentação atual (pré-DOCS-02) está desatualizada:**

- `README.md` linhas 142-151 (seção "LLM Strategy") cita apenas ADR-003 PATCH SUB-C + PATCH 2 — sem ADR-010
- `README.md` linha 170 ("Limitações conhecidas") lista modelos Ollama incorretamente (sem Qwen 7B)
- `docs/sop-revisar-pdf.md` em 6 pontos (linhas 14, 34, 63, 256, 342) menciona "Sabia-7B" / `default premium` / latência antiga / cross-ref ADR-003 sem ADR-010

**Outras 2 SOPs confirmadas out-of-scope** (Morpheus reality check via grep):
- `docs/sop-populate-vault.md` — zero menções LLM/Sabia/Ollama/qwen
- `docs/sop-rotacao-auth-cookie-key.md` — zero menções LLM/Sabia/Ollama/qwen

Esta story **alinha documentação com estado real do produto** sem inventar conteúdo (No Invention rule per `quality-gate-enforcement.md`).

---

## Acceptance Criteria

### Funcionalidade (3/3 MUST)

- [ ] **AC-1:** `README.md` seção "LLM Strategy" (linhas 142-151) atualizada:
  - Título inclui "ADR-010 Path C" no cross-ref
  - Bullet Advogado descreve tier configurável com default `balanced=Qwen 2.5 7B` + premium=Sabia opt-in para GPU
  - Footprint atualizado para ~10.7GB disco total (qwen2.5:3b 1.9GB + qwen2.5:7b 4.7GB + sabia-7b-instruct 4.1GB preserved)
  - Latência atualizada para ~250s INTEGRAL (smoke evidence 253.72s)
  - GPU upgrade path documentado (`LLM_TIER=premium` em .env)
  - Verificável: `grep -A12 "## LLM Strategy" README.md` mostra ADR-010 + balanced default + GPU upgrade path
- [ ] **AC-2:** `README.md` "Limitações conhecidas" (linha 170) atualizada:
  - Entry de modelos Ollama lista Qwen 7B + Qwen 3B + Sabia-7B preserved
  - Workaround inclui `ollama pull qwen2.5:3b qwen2.5:7b` + Modelfile Sabia opcional
  - Verificável: `grep -A1 "Modelos Ollama" README.md` mostra os 3 modelos
- [ ] **AC-3:** `docs/sop-revisar-pdf.md` atualizado em 6 pontos:
  - Linha 14: `Advogado :11434 (DEFAULT Qwen 2.5 7B per ADR-010; premium=Sabia opt-in)` + cross-ref `ADR-003 SUB-C + ADR-010`
  - Linha 34: `--tier` default `premium` → `balanced` (com nota ADR-010)
  - Linha 63: latência `~120-180s` → `~250-300s INTEGRAL com Qwen 7B em CPU (smoke evidence 253.72s)` + nota tier premium GPU
  - Linha 256: JSON example `tier_advogado: "premium"` → `tier_advogado: "balanced"`
  - Linha 342 (Referências técnicas): adicionar entry `ADR-010 — Path C Qwen 7B fallback`
  - Verificável: `grep -c "ADR-010" docs/sop-revisar-pdf.md` retorna ≥3; `grep "tier_advogado" docs/sop-revisar-pdf.md` retorna `balanced`

### Quality (2/2 MUST)

- [ ] **AC-4:** Suite testes 232 passed + 1 skipped baseline preservado (zero regressão — docs-only changes)
  - Verificável: `python -m pytest --no-cov 2>&1 | tail -3`
- [ ] **AC-5:** Markdownlint clean OU preview visual sem broken links nos arquivos editados
  - Verificável: `python -m mdformat --check README.md docs/sop-revisar-pdf.md` (se mdformat instalado) OU revisão manual cross-refs

### Documentação (2/2 MUST)

- [ ] **AC-6:** TECH-DEBT.md verificado — DOCS-02 não introduz nem resolve tech debts (story é alignment, não mitigation)
  - Verificável: `grep -c "DOCS-02" governance/TECH-DEBT.md` retorna 0 (nenhuma menção esperada)
- [ ] **AC-7:** Conventional commit message cross-references `[Story DOCS-02]` + `ADR-010` + `REV-LLM-01`
  - Verificável: pós-push `git log -1 --pretty=%B` mostra os 3 cross-refs

---

## Tasks / Subtasks

### Phase A — README "LLM Strategy" section (10min)

- [ ] **A.1** Ler README.md linhas 140-152 (estado atual)
- [ ] **A.2** Aplicar mudança completa na seção (ver Dev Notes — bloco "D1 README LLM Strategy proposed text")
- [ ] **A.3** Verificar grep: `grep -A12 "## LLM Strategy" README.md` mostra ADR-010 + balanced default + GPU upgrade path

### Phase B — README "Limitações conhecidas" (5min)

- [ ] **B.1** Ler README.md linhas 168-174 (estado atual)
- [ ] **B.2** Atualizar entry "Modelos Ollama" (linha 170) per Dev Notes "D2 README Limitações"
- [ ] **B.3** Verificar grep: `grep -A1 "Modelos Ollama" README.md` mostra qwen2.5:3b + qwen2.5:7b + sabia-7b-instruct

### Phase C — docs/sop-revisar-pdf.md 6 pontos (15min)

- [ ] **C.1** Ler sop-revisar-pdf.md linhas 14, 34, 63, 256, 342 (5 áreas — linha 14 conta como 1 ponto + cross-ref)
- [ ] **C.2** Aplicar 6 mudanças cirúrgicas per Dev Notes "D3 SOP-revisar-pdf points"
- [ ] **C.3** Verificar greps:
  - `grep -c "ADR-010" docs/sop-revisar-pdf.md` ≥3 (linha 14 cross-ref + linha 34 nota + linha 342 entry)
  - `grep "tier_advogado" docs/sop-revisar-pdf.md` retorna `balanced`
  - `grep -c "Qwen 2.5 7B" docs/sop-revisar-pdf.md` ≥1

### Phase D — Validação + closure (10min)

- [ ] **D.1** Rodar suite regression: `python -m pytest --no-cov 2>&1 | tail -5` → esperado 232 passed + 1 skipped
- [ ] **D.2** Verificar grep cross-refs ADR-010:
  - `grep -c "ADR-010" README.md` ≥1 (seção LLM Strategy)
  - `grep -c "ADR-010" docs/sop-revisar-pdf.md` ≥3
- [ ] **D.3** Atualizar Dev Agent Record (Agent Model, File List, Completion Notes, Change Log)
- [ ] **D.4** Status story → `Ready for Review`
- [ ] **D.5** Emit handoff @dev → @qa Oracle gate

---

## Dev Notes

### D1 — README "LLM Strategy" section (proposed full text replacing lines 142-151)

**ANTES (linhas 142-151):**

```markdown
## LLM Strategy (ADR-003 PATCH SUB-C + PATCH 2)

Fan-out paralelo via `asyncio.gather` em **2 instâncias Ollama distintas**:

- **Advogado** — Sabia-7B Tier configurável (`OLLAMA_HOST_ADVOGADO=127.0.0.1:11434`)
- **Economista** — Qwen 2.5 3B FIXO (`OLLAMA_HOST_ECONOMISTA=127.0.0.1:11435`)

**Footprint:** ~7GB RAM. **Latência:** max(advogado, economista) ≈ 90s paralelo.

**Validação obrigatória pré-release:** rodar `pytest tests/smoke/test_paralelismo_llm.py` — ratio asyncio.gather vs sequencial DEVE ser <0.7. Se falhar, paralelismo é placebo (debug `OLLAMA_HOST` distintos OU `langchain-ollama>=0.2.0`).
```

**DEPOIS:**

```markdown
## LLM Strategy (ADR-003 PATCH SUB-C + PATCH 2 + ADR-010 Path C)

Fan-out paralelo via `asyncio.gather` em **2 instâncias Ollama distintas**:

- **Advogado** — Tier configurável `lean | balanced | premium` (`OLLAMA_HOST_ADVOGADO=127.0.0.1:11434`):
  - `lean=qwen2.5:3b` (consistência família com economista)
  - `balanced=qwen2.5:7b` — **DEFAULT** (CPU-friendly per ADR-010 Path C; smoke evidence 253.72s PASS)
  - `premium=sabia-7b-instruct` (preserved opt-in para futuro upgrade GPU)
- **Economista** — Qwen 2.5 3B FIXO (`OLLAMA_HOST_ECONOMISTA=127.0.0.1:11435`)

**Footprint:** ~10.7GB disco total (qwen2.5:3b 1.9GB + qwen2.5:7b 4.7GB + sabia-7b-instruct 4.1GB preserved opt-in). **Latência:** ~250-300s INTEGRAL com Qwen 7B em CPU (~250s smoke evidence sessão 86); ~120s com tier premium quando GPU disponível.

**GPU upgrade path:** Toggle `LLM_TIER=premium` em `.env` reverte para Sabia-7B em 1 linha — sem mudança de código, sem nova ADR. Decisão de quando habilitar é operacional (deploy em hardware com GPU CUDA disponível).

**Validação obrigatória pré-release:** rodar `pytest tests/smoke/test_paralelismo_llm.py` — ratio asyncio.gather vs sequencial DEVE ser <0.7. Se falhar, paralelismo é placebo (debug `OLLAMA_HOST` distintos OU `langchain-ollama>=0.2.0`).

**Cross-refs:** ADR-003 SUB-C (paralelismo), ADR-003 PATCH 2 (instâncias distintas), [ADR-010](governance/architecture/adr/adr-010-sabia-q4-mitigation.md) (Qwen 7B fallback default — Sabia Q4 quality issue mitigation).
```

### D2 — README "Limitações conhecidas" (linha 170 update)

**ANTES (linha 170):**

```markdown
| Modelos Ollama (Sabia-7B + Qwen 3B) NÃO inclusos | Instalar Ollama externo + `ollama pull` | Setup futuro |
```

**DEPOIS:**

```markdown
| Modelos Ollama (Qwen 2.5 7B default + Qwen 2.5 3B + Sabia-7B preserved opt-in) NÃO inclusos | Instalar Ollama externo + `ollama pull qwen2.5:3b qwen2.5:7b` + Modelfile Sabia opcional | SOP sop-revisar-pdf (atualizado DOCS-02) + ADR-010 |
```

### D3 — `docs/sop-revisar-pdf.md` 6 pontos (cirurgicos)

**Ponto 1 — Linha 14 (Pré-requisitos: bullet Ollama rodando):**

```markdown
# ANTES
- [ ] **Ollama rodando** (se quiser revisão real LLM): instâncias Sabia-7B em `127.0.0.1:11434` e Qwen 2.5 3B em `127.0.0.1:11435` — ver ADR-003 SUB-C

# DEPOIS
- [ ] **Ollama rodando** (se quiser revisão real LLM): instâncias Advogado em `127.0.0.1:11434` (DEFAULT Qwen 2.5 7B per ADR-010; `LLM_TIER=premium` reverte para Sabia-7B opt-in) e Qwen 2.5 3B em `127.0.0.1:11435` — ver ADR-003 SUB-C + ADR-010 Path C
```

**Ponto 2 — Linha 34 (tabela de flags, default `--tier`):**

```markdown
# ANTES
| `--tier {lean\|balanced\|premium}` | `premium` | Tier do Advogado LLM (FR-TESE-02) |

# DEPOIS
| `--tier {lean\|balanced\|premium}` | `balanced` | Tier do Advogado LLM (FR-TESE-02; default `balanced`=Qwen 7B per ADR-010) |
```

**Ponto 3 — Linha 63 (expectativa de tempo):**

```markdown
# ANTES
**O que esperar:** ~120-180s end-to-end (com Ollama real) ou ~60s (sem LLM real, smoke).

# DEPOIS
**O que esperar:** ~250-300s INTEGRAL com Qwen 7B em CPU (smoke evidence sessão 86: 253.72s PASS); ~120-180s com tier premium quando GPU disponível; ~60s sem LLM real (smoke skipped no CI).
```

**Ponto 4 — Linha 256 (JSON example metadata):**

```markdown
# ANTES
    "tier_advogado": "premium",

# DEPOIS
    "tier_advogado": "balanced",
```

**Ponto 5 — Linha 342 (Referências técnicas, adicionar entry):**

```markdown
# ANTES (linha 342)
- ADR-003 PATCH SUB-C — LLM Strategy (Sabia-7B + Qwen 3B paralelo)
- ADR-005 — HMAC GENESIS audit chain

# DEPOIS (insere ADR-010 entre as duas)
- ADR-003 PATCH SUB-C — LLM Strategy (Sabia-7B + Qwen 3B paralelo)
- ADR-010 — Path C Qwen 7B fallback (Sabia Q4 output 3 chars FAIL mitigation; preserva Sabia opt-in para GPU futuro)
- ADR-005 — HMAC GENESIS audit chain
```

**Ponto 6 — Verificação cumulativa (greps esperados pós-edit):**

```bash
grep -c "ADR-010" docs/sop-revisar-pdf.md          # esperado: ≥3 (linha 14 + linha 34 + linha 342)
grep "tier_advogado" docs/sop-revisar-pdf.md       # esperado: "balanced" (não mais "premium")
grep -c "Qwen 2.5 7B" docs/sop-revisar-pdf.md      # esperado: ≥1 (linha 14 cross-ref)
```

### Anti-patterns a evitar

- ❌ NÃO editar `docs/sop-populate-vault.md` (zero menções LLM — out-of-scope per Morpheus reality check)
- ❌ NÃO editar `docs/sop-rotacao-auth-cookie-key.md` (zero menções LLM — out-of-scope)
- ❌ NÃO editar arquivos `.py` (DOCS-02 é docs-only — zero code changes)
- ❌ NÃO renomear `LLMTier` types em código (mantém `lean | balanced | premium`)
- ❌ NÃO inventar nova "v0.2.0" se ainda não foi tagged (use `governance/architecture/adr/adr-010` apenas para cross-ref)
- ❌ NÃO atualizar tests pytest (DOCS-02 é docs-only — suite continua 232+1 baseline)

### Estratégia anti-regressão

- Suite testes deve continuar **232 passed + 1 skipped** após edits (docs-only não toca código)
- Se algum teste quebrar: investigar (provavelmente edit acidental de `.py` — reverter)
- Se markdownlint quebrar (se config existir): ajustar formatação inline sem mudar conteúdo

---

## Files to Modify

- `README.md` (2 seções: linhas 142-151 LLM Strategy + linha 170 Limitações conhecidas)
- `docs/sop-revisar-pdf.md` (6 pontos cirurgicos: linhas 14, 34, 63, 256, 342)

## Files NOT to Modify

- `docs/sop-populate-vault.md` (zero menções LLM — out-of-scope)
- `docs/sop-rotacao-auth-cookie-key.md` (zero menções LLM — out-of-scope)
- Qualquer `.py` (DOCS-02 é docs-only — zero code changes)
- `tests/**/*.py` (suite continua 232+1 baseline)
- `bloco_workflow/personas/llm_factory.py` (REV-LLM-01 já fechado — não tocar)
- `governance/architecture/adr/adr-010-sabia-q4-mitigation.md` (ADR Accepted — não modificar)

---

## Tests Required

### Regressão (pytest mocked)

```bash
python -m pytest --no-cov 2>&1 | tail -3
# Esperado: 232 passed + 1 skipped (zero regressão)
```

### Cross-ref verification (grep)

```bash
# README.md
grep -c "ADR-010" README.md                                # esperado: ≥1
grep -A12 "## LLM Strategy" README.md | grep -c "balanced" # esperado: ≥1 (default)

# sop-revisar-pdf.md
grep -c "ADR-010" docs/sop-revisar-pdf.md                  # esperado: ≥3
grep "tier_advogado" docs/sop-revisar-pdf.md               # esperado: "balanced"
grep -c "Qwen 2.5 7B" docs/sop-revisar-pdf.md              # esperado: ≥1
```

### Markdownlint (se aplicável)

```bash
python -m mdformat --check README.md docs/sop-revisar-pdf.md
# Esperado: clean OU diff-only-formatting (não conteúdo)
```

---

## Dependencies

### Upstream (this story depends on)

- ✅ ADR-010 accepted (Eric, sessão 86, governance/architecture/adr/adr-010-sabia-q4-mitigation.md)
- ✅ REV-LLM-01 Done (commit 20d4459 + closure 8eea89c — sessão 86)
- ✅ Estado atual README + sop-revisar-pdf identificado (Morpheus mapeou linhas exatas)

### Downstream (this story unblocks)

- 🔓 Story UI-1 production-grade — pipeline real pode referenciar SOP atualizado sem aviso de divergência
- 🔓 Release v0.2.0 gate condition #7 — docs alignment com ADR-010
- 🔓 Onboarding novo operador (ou Eric retomando após meses) tem doc consistente com produto real

---

## Definition of Done

Story está Done quando:

1. ✅ Todos os 7 ACs passam
2. ✅ @qa (Oracle) PASS gate
3. ✅ Conventional commit pushed em main com cross-reference [Story DOCS-02] + ADR-010 + REV-LLM-01
4. ✅ CI verde
5. ✅ Suite 232 passed + 1 skipped preservado
6. ✅ Story status `Done`
7. ✅ Checkpoint sessão atualizado com SHA do commit

---

## Risk + Mitigation

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Scope creep para SOPs sem LLM mention (sop-populate-vault/sop-rotacao) | BAIXA | Files NOT to Modify violados | "Files NOT to Modify" explícito + Morpheus reality check documentado |
| Regression suite quebra inesperadamente em docs-only | MUITO BAIXA | Bloqueia push | Edits são .md only; rodar pytest pré/pós (paranoia) |
| Link/cross-ref inconsistente após edits (ex: ADR-010 path errado) | BAIXA | Doc visualmente OK mas link broken | @qa Oracle gate verifica via grep ADR-010 em README + sop-revisar-pdf |
| Edit acidental em arquivo `.py` confundindo com `.md` | MUITO BAIXA | Suite quebra | Diff review pré-commit; @dev usa git diff antes de stage |
| Markdownlint config inexistente — AC-5 vacuo | BAIXA | AC-5 não verificável mecanicamente | AC-5 aceita "preview visual sem broken links" como alternativa |

---

## Change Log

| Data | Sessão | Quem | Ação |
|---|---|---|---|
| 2026-05-05 | 86 | @sm (River) | Story criada (status Ready) — escopo Morpheus mapeou exato (README 2 seções + sop-revisar-pdf 6 pontos); 7 ACs + 4 phases + Dev Notes copy-paste-ready |
| 2026-05-05 | 86 | @po (Keymaker) | PO Gate APROVADO 10/10 (GO) — story exemplar com reality check Morpheus + Dev Notes copy-paste-ready + Files NOT to Modify defensive |
| 2026-05-05 | 86 | @dev (Neo) | Implementação completa: Phase A README LLM Strategy substituição completa + Phase B Limitações entry update + Phase C sop-revisar-pdf 6 pontos cirúrgicos + Phase D regression suite 232+1 baseline preservado; status → Ready for Review |
| 2026-05-05 | 86 | @qa (Oracle) | Gate PASS — 5/5 adversarial probes (README LLM Strategy + Limitações + sop-revisar-pdf 6 pontos + boundary respect + AC-5 PRAGMATIC); QA Results preenchido; gate file criado |
| 2026-05-05 | 86 | @devops (Operator) | Commit `8b37513` (5 files +1006/-8) pushed to origin/main; status → Done; **DOCS-02 CLOSED — Sprint 02 5/5 priority alta done — UI-1 priority 4 restante (3-5h)** |

---

## Validation Notes (@po Keymaker)

### 10-Point Checklist

| # | Critério | Status | Evidência |
|---|---|---|---|
| 1 | Story title clear/específico | ✅ PASS | "Atualização docs operacionais pós ADR-010 (README LLM Strategy + SOP-revisar-pdf cross-refs)" — explicito sobre escopo (2 arquivos) + ADR origem |
| 2 | User story format completo (As/I want/so that) | ✅ PASS | Linhas 33-35 com persona específica (operador novo OU Eric retomando após meses), motivação técnica e benefício mensurável (evita `citacao_textual="..."` FAIL surpresa) |
| 3 | ACs ≥5 testáveis com critérios numéricos | ✅ PASS | 7 ACs (3 Func + 2 Quality + 2 Docs), todos com critério verificável (grep regex / file diff stat / pytest count) |
| 4 | Tasks/Subtasks granulares com checkbox | ✅ PASS | 4 phases (A-D), 11 subtasks total, todos com `[ ]` checkbox e tempo estimado (10+5+15+10min) |
| 5 | Dependencies explícitas (upstream/downstream) | ✅ PASS | Upstream: ADR-010 ✅ + REV-LLM-01 ✅ + Morpheus reality check ✅. Downstream: UI-1 + Release v0.2.0 gate condition #7 + onboarding |
| 6 | Files to modify/NOT-modify listados | ✅ PASS | 2 modify (README + sop-revisar-pdf) + 6 NOT-modify defensive (2 SOPs out-of-scope + .py + tests + llm_factory.py + ADR-010 file) |
| 7 | Tests required cobrem ACs | ✅ PASS | Regression suite (AC-4) + grep cross-refs ADR-010 (AC-1/2/3) + Markdownlint fallback (AC-5) — 100% Quality ACs cobertos |
| 8 | Risk + Mitigation documentado | ✅ PASS | 5 riscos com Probabilidade/Impacto/Mitigação (scope creep, regression docs-only, link inconsistente, edit acidental .py, markdownlint config) |
| 9 | Effort estimado realista | ✅ PASS | 1-2h com phase breakdown (10+5+15+10min ≈ 40min ativos + buffer para validação/closure) — realista para docs-only |
| 10 | Status correto (Ready) | ✅ PASS | `status: Ready` no frontmatter; Morpheus mapeou linhas exatas (README 142-151 + 170; sop-revisar-pdf 14, 34, 63, 256, 342) → zero ambiguidade técnica |

**Score: 10/10 — GO**

### Decisão

✅ **GO (APROVADA)** — Story DOCS-02 está pronta para development. @dev (Neo) pode prosseguir com `*develop-yolo`.

### Forças destacadas (story exemplar)

- **Reality check Morpheus documentado** — Contexto (linhas 49-51) explica que 3 SOPs originalmente mencionadas viraram 1 SOP relevante após grep; No Invention rule respeitada
- **Dev Notes copy-paste-ready** — D1 (README LLM Strategy ANTES/DEPOIS full text) + D2 (Limitações entry update) + D3 (6 pontos cirurgicos sop-revisar-pdf com ANTES/DEPOIS por linha) eliminam ambiguidade total para Neo
- **Files NOT to Modify defensive (6 itens)** — Inclui `.py`, `tests/**/*.py`, `llm_factory.py` (REV-LLM-01 closed), `ADR-010 file` (Accepted) — protege contra scope creep direto e indireto
- **AC-5 fallback pragmatic** — Markdownlint OU preview visual sem broken links — não bloqueia em ambientes sem mdformat config; risk mitigation explícita também (linha 351)
- **Anti-pattern "edit acidental .py confundindo com .md"** — risco MUITO BAIXA mas registrado com mitigação (git diff pré-commit) — defensive thinking de River

### Observações non-bloqueantes (advisory)

1. **AC-3 contagem "6 pontos / 5 áreas"** — Linha 14 conta como 1 ponto principal + 1 cross-ref ajuste no mesmo bullet (2 mudanças). Story documenta isso em Phase C.1 ("linha 14 conta como 1 ponto + cross-ref"). **Aceitável** — pequena nota Para Neo não confundir.
2. **AC-5 verificabilidade vacuosa** — Se `mdformat` não estiver instalado no projeto, AC-5 cai para "preview visual sem broken links" qualitativo. Risk #5 já registra. **Sugestão para @qa Oracle:** ao verificar AC-5, se mdformat ausente → grep ADR-010 + verificação visual de cross-refs é suficiente.
3. **DoD #6 PROJECT-CHECKPOINT update** — Não é AC explícito mas DoD lista "Checkpoint sessão atualizado com SHA do commit". @dev/Operator devem lembrar (já é prática estabelecida REV-LLM-01).

### Próximo handoff

**H-S02-DOCS02-po2dev** → @dev (Neo) `*develop-yolo DOCS-02` — Workflow estrito, status Ready aprovado.

— Keymaker, balanceando precisão e velocidade 🎯

---

## Dev Agent Record

### Agent Model Used

claude-opus-4-7[1m] via Skill `LMAS:agents:dev` (Neo persona, sessão 86, 2026-05-05).

### Debug Log References

- Phase A: README.md linhas 142-151 substituídas em 1 Edit operation (block replacement). Resultado grep `grep -A12 "## LLM Strategy" README.md` mostra ADR-010 + balanced default + GPU upgrade path ✓
- Phase B: README.md linha 170 substituição inline em 1 Edit. Resultado grep `grep -A1 "Modelos Ollama" README.md` mostra qwen2.5:3b + qwen2.5:7b + sabia-7b-instruct ✓
- Phase C: 6 Edit operations cirúrgicas em sop-revisar-pdf.md (linhas 14, 34, 63, 256, 342). Greps cumulativos: `ADR-010=3` ✓, `tier_advogado=balanced` ✓, `Qwen 2.5 7B=1` ✓
- Phase D iter 1: regression suite **232 passed + 1 skipped em 61.12s** — zero regressão ✓
- Diff scope check: `git diff --stat HEAD` mostra apenas README.md + sop-revisar-pdf.md + CHECKPOINT-active.md (acumulado sessões anteriores Sm/Po) — zero `.py` edits, zero tests, boundary respected

### Completion Notes List

**Implementação direta sem desvios — story exemplar Morpheus → River → Keymaker → Neo chain executou per spec:**

1. **Reality check Morpheus respeitado** — Story listava 2 SOPs out-of-scope (sop-populate-vault.md + sop-rotacao-auth-cookie-key.md) em Files NOT to Modify; nenhuma editada. Único SOP relevante (sop-revisar-pdf.md) com 6 pontos cirúrgicos exatos.

2. **Dev Notes copy-paste-ready validados** — D1 (README LLM Strategy ANTES/DEPOIS) + D2 (Limitações entry) + D3 (6 pontos sop-revisar-pdf) executados sem ambiguidade. Zero iterações de fix necessárias.

3. **Suite preservada** — 232 passed + 1 skipped baseline mantido em 61.12s (paridade com tempos anteriores REV-LLM-01 closure).

**Validações passadas:**

| AC | Resultado | Evidência |
|---|---|---|
| AC-1 README LLM Strategy section | ✅ PASS | grep mostra ADR-010 Path C + balanced DEFAULT + Footprint 10.7GB + Latência 250s + GPU upgrade path |
| AC-2 README Limitações conhecidas | ✅ PASS | grep mostra qwen2.5:3b + qwen2.5:7b + sabia-7b-instruct preserved + workaround correto |
| AC-3 sop-revisar-pdf.md 6 pontos | ✅ PASS | grep ADR-010=3 + tier_advogado=balanced + Qwen 2.5 7B=1 |
| AC-4 Suite 232+1 baseline | ✅ PASS | 232 passed + 1 skipped em 61.12s — zero regressão |
| AC-5 Markdownlint clean OU preview visual | ⚠️ PRAGMATIC | mdformat não instalado no projeto (verificável via `python -m mdformat --check` retornaria error); fallback aceito per AC-5 advisory PO — visual review confirma cross-refs ADR-010 íntegros |
| AC-6 TECH-DEBT.md verificado | ✅ PASS | `grep -c "DOCS-02" governance/TECH-DEBT.md` = 0 (esperado — alignment story não introduz/resolve debts) |
| AC-7 Conventional commit cross-refs | ⏳ PENDING | Operator Phase F (esperado — fora do escopo Neo) |

**Total: 6/7 firmes + 1 partial-aceitável (AC-5 mdformat ausente — fallback visual per PO advisory) + 1 pending (AC-7 commit Operator).**

**Ambiente final:**
- README.md atualizado (15 lines diff: +13/-2 net per `git diff --stat`)
- docs/sop-revisar-pdf.md atualizado (9 lines diff: 6 cirurgical points)
- Suite 232+1 baseline preservado
- Zero `.py` modificados (boundary respect rigoroso)
- Zero scope creep (2 SOPs out-of-scope intactas; llm_factory.py intacto; ADR-010 file intacto)

### File List

**Files modified (2):**

- `README.md` — Phase A: substituição completa seção "LLM Strategy" (linhas 142-151 → expandida com 3 tiers + Footprint 10.7GB + Latência 250s + GPU upgrade path + cross-refs); Phase B: entry "Modelos Ollama" linha 170 atualizada (modelos list correto + workaround correto)
- `docs/sop-revisar-pdf.md` — Phase C: 6 pontos cirúrgicos (linhas 14 cross-ref + 14 descrição Advogado tier + 34 default tier + 63 latência + 256 JSON tier_advogado + 342 entry ADR-010)

**Files modified (governance):**

- `governance/stories/DOCS-02-readme-sops-adr-010-updates.md` — Dev Agent Record + Change Log + status → Ready for Review

**Files NOT modified (boundary respect):**

- `docs/sop-populate-vault.md` (out-of-scope — zero LLM mentions)
- `docs/sop-rotacao-auth-cookie-key.md` (out-of-scope — zero LLM mentions)
- Qualquer `.py` (DOCS-02 docs-only)
- `tests/**/*.py` (suite 232+1 preservado)
- `bloco_workflow/personas/llm_factory.py` (REV-LLM-01 closed)
- `governance/architecture/adr/adr-010-sabia-q4-mitigation.md` (Accepted — não modificar)

**Files added:** none

---

## QA Results

### Gate Decision: ✅ **PASS**

**Reviewer:** Oracle (@qa) | **Date:** 2026-05-05 | **Session:** 86 | **Gate file:** `governance/qa/qa-gate-story-docs-02-readme-sops-adr-010.md`

### Adversarial Probes (5/5)

| Probe | Result | Evidência |
|---|---|---|
| **P1** README LLM Strategy section | ✅ PASS | `grep -A18 "## LLM Strategy" README.md` mostra ADR-010 Path C + 3 tiers + DEFAULT marked + Footprint 10.7GB + Latência 250s + GPU upgrade path + cross-refs íntegros |
| **P2** README Limitações | ✅ PASS | `grep -A1 "Modelos Ollama" README.md` mostra qwen2.5:3b + qwen2.5:7b + sabia-7b-instruct preserved + workaround `ollama pull qwen2.5:3b qwen2.5:7b` + endereçada em SOP atualizado + ADR-010 |
| **P3** sop-revisar-pdf 6 pontos | ✅ PASS | greps cumulativos: ADR-010=3 (linhas 14, 34, 343 — entry inserida entre ADR-003 e ADR-005); tier_advogado=balanced; Qwen 2.5 7B=1 |
| **P4** Boundary respect | ✅ PASS | `git diff --stat HEAD`: APENAS 3 .md files (README +13/-2, sop-revisar-pdf +9 cirurgicos, CHECKPOINT-active +103 acumulado sessões anteriores); ZERO `.py`, ZERO `tests/**/*.py` modificados |
| **P5** AC-5 self-critique + link integrity | ✅ PASS | mdformat **genuinamente não instalado** (ImportError confirmado) → fallback visual per PO advisory aceito; ADR-010 file existe (13693 bytes) com status `accepted`; README cross-ref `[ADR-010](governance/architecture/adr/adr-010-sabia-q4-mitigation.md)` aponta path correto |

### AC Compliance Matrix

- ✅ AC-1, AC-2, AC-3 (Funcionalidade): todas PASS
- ✅ AC-4 (suite 232+1): PASS (61.12s)
- ⚠️ AC-5 (markdownlint): PRAGMATIC ACCEPTED — mdformat genuinamente ausente; fallback visual via grep ADR-010 íntegros é evidência suficiente per PO advisory linha 351 risk #5
- ✅ AC-6 (TECH-DEBT verificado): PASS (grep DOCS-02=0 conforme esperado para alignment story)
- ⏳ AC-7 (Conventional commit): PENDING Operator (esperado — fora do escopo Neo)

**Final score: 6 firmes + 1 partial-aceitável + 1 pending-operator = PASS**

### Risk Assessment (post-implementation)

| Risco | Status final |
|---|---|
| Scope creep para SOPs sem LLM | ✅ Mitigado: 2 SOPs out-of-scope intactas, diff scope confirmou |
| Regression suite quebra docs-only | ✅ Validado: 232 passed + 1 skipped em 61.12s (paridade baseline) |
| Link/cross-ref inconsistente | ✅ Validado: ADR-010 file existe + path README correto |
| Edit acidental .py | ✅ Mitigado: zero .py modificados (Probe 4 confirmou) |
| Markdownlint config inexistente | ⚠️ Materializado: mdformat genuinamente ausente → fallback visual aceito |

**Riscos materializados:** 1 de 5 (AC-5 mdformat ausente — PRAGMATIC fallback). Restantes 4 não materializaram.

### Observações Non-Blocking (advisory)

1. **AC-5 mdformat instalação opcional** — Sugerir adicionar `mdformat` em pyproject.toml dev dependencies para futuro: permite verificação mecânica em vez de visual. **Não blocker** para esta story (escopo docs-only) — mais um nice-to-have de DX. Se Eric quiser, story dedicada futura `INFRA-XX install mdformat` em backlog LOW.

2. **ADR-010 entry em sop-revisar-pdf linha 343 (não 342)** — Story spec dizia "linha 342" mas Neo inseriu na linha 343 (entre ADR-003 SUB-C linha 342 e ADR-005 linha 344). Diferença de 1 linha decorre do entry novo deslocando linhas — semantically correto, posição na lista preserva ordem por número ADR. **Aceitável.**

3. **Latência atualizada usando smoke evidence sessão 86** — README e sop-revisar-pdf cita `253.72s` como evidência empírica concreta. Se Eric rodar smoke novamente em hardware diferente, o número pode variar. **Aceitável** — número documentado como evidência sessão específica, não como SLA.

### Smoke Pipeline INTEGRAL não re-rodado

DOCS-02 é docs-only — **não re-roda smoke INTEGRAL** (não toca código LLM nem schemas). Smoke baseline 253.72s permanece válido (REV-LLM-01 sessão 86 evidence). Suite regression mocked (232 passed + 1 skipped em 61.12s) é suficiente.

### Próximo handoff

✅ **PASS gate emitido.** Próximo step: `@devops` (Operator) para commit + push **STANDALONE** (não há governance batch pendente — REV-LLM-01 já fechou ADR-010 batch unificado anteriormente):

**Batch standalone:**
1. `README.md` (Phase A + B)
2. `docs/sop-revisar-pdf.md` (Phase C 6 pontos)
3. `governance/CHECKPOINT-active.md` (acumulado sessões anteriores Sm/Po/Dev/Oracle)
4. `governance/stories/DOCS-02-readme-sops-adr-010-updates.md` (closure — Dev Agent Record + QA Results + Change Log)
5. `governance/qa/qa-gate-story-docs-02-readme-sops-adr-010.md` (NEW gate file)

**Conventional commit message sugerido:**
```
docs: alinha README + sop-revisar-pdf com ADR-010 Path C [Story DOCS-02]

- README LLM Strategy: 3 tiers explícitos (lean/balanced/premium) + Footprint 10.7GB + Latência 250s + GPU upgrade path
- README Limitações: modelos Ollama list correto + workaround `ollama pull qwen2.5:3b qwen2.5:7b`
- docs/sop-revisar-pdf: 6 pontos cirurgicos atualizados (defaults, latência, JSON example, cross-refs ADR-010)
- Suite 232 passed + 1 skipped baseline preservado (zero regressão)

Refs: governance/architecture/adr/adr-010-sabia-q4-mitigation.md (Accepted Eric, REV-LLM-01 closed 20d4459)
QA Gate: governance/qa/qa-gate-story-docs-02-readme-sops-adr-010.md (PASS Oracle)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

— Oracle, conferindo cada cross-ref antes de aprovar a verdade compartilhada 🛡️

---

*Story DOCS-02 — River (sessão 86, 2026-05-05) · Sprint 02 priority alta · Documentation alignment pós ADR-010 · 1-2h effort estimado · zero tech-debts resolved (alignment story) · unblocks UI-1 + Release v0.2.0 gate*

— River, conectando documento à realidade 🌊
