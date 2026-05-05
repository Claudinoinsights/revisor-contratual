---
type: story
id: REV-INT-02
title: "Self-host Google Fonts (LGPD on-premise)"
status: Ready for Review
priority: 2
sprint: "02"
epic: "Sprint-02-release-v0.2.0"
owner: "@dev (Neo)"
estimated_effort: "30min"
created: "2026-05-05"
created_by: "@sm (River)"
predecessor_handoff: ".lmas/handoffs/handoff-morpheus-to-sm-2026-05-05-revint02-create-story.yaml"
resolves:
  - TD-WEB-LGPD-CDN-01 (HIGH)
unblocks:
  - "Release v0.2.0 gate condition #1 (zero CDN externos em base.html)"
tags:
  - project/revisor-contratual
  - story
  - sprint-02
  - rev-int-02
  - lgpd
  - frontend
---

# Story REV-INT-02 — Self-host Google Fonts (LGPD on-premise)

## Story

**Como** operador da ferramenta Revisor Contratual instalada localmente,
**Eu quero** que a UI Web (FastAPI + HTMX) NÃO faça requisições HTTP para CDNs externos (Google Fonts),
**Para que** o princípio "100% on-premise LGPD" do PRD seja respeitado e meu IP não seja vazado para terceiros (Google) a cada page load.

---

## Contexto

Oracle QA Gate REV-INT-01 (sessão 85) identificou via Probe 5 que `bloco_interface/web/templates/base.html` carrega Google Fonts via:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,500&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

Embora o produto declare em `landing/index.html` linha 7-8 que **"PDFs e dados do contrato nunca saem da máquina"**, o **IP do operador é exposto a Google** a cada page load via Google Fonts CDN. Isso é inconsistência reputacional para um produto que vende "100% local" como diferencial.

Esta story resolve o único HIGH ativo do projeto (TD-WEB-LGPD-CDN-01) — gate condition mandatório para release v0.2.0 público.

---

## Acceptance Criteria

### Funcionalidade (MUST)

- [ ] **AC-1:** Zero requisições HTTP para `fonts.googleapis.com` em qualquer carregamento de página da UI Web
  - Verificável: `curl -s http://127.0.0.1:8501/ | grep -c 'fonts.googleapis'` → retorna `0`
- [ ] **AC-2:** Zero requisições HTTP para `fonts.gstatic.com` em qualquer carregamento
  - Verificável: `curl -s http://127.0.0.1:8501/ | grep -c 'fonts.gstatic'` → retorna `0`
- [ ] **AC-3:** Tipografia Manrope, Fraunces e JetBrains Mono preservadas visualmente (mesma identidade Orsheva)
  - Verificável: smoke browser test Eric — comparação visual antes/depois deve ser visualmente idêntica em estado idle (form upload), processing (pipeline steps) e result (verdict 78%)
- [ ] **AC-4:** Fontes self-hosted servidas via `/static/fonts/`
  - Verificável: `curl -I http://127.0.0.1:8501/static/fonts/manrope-400.woff2` → HTTP 200

### Visual (MUST)

- [ ] **AC-5:** Manrope em corpo da UI (topbar brand, sidebar histórico, form labels, botões)
- [ ] **AC-6:** Fraunces APENAS em verdict (status 24px + número 44px + criterio-score 24px)
- [ ] **AC-7:** JetBrains Mono em código inline (`<code>`), badges de veredito, criterio-tag, hist-meta

### Quality (MUST)

- [ ] **AC-8:** Suite testes mantém **232 passed + 1 skipped** (baseline pós-DEVOPS-01) — zero regressão
  - Verificável: `python -m pytest --no-cov 2>&1 | tail -3`
- [ ] **AC-9:** Tamanho total de fontes ≤ 200KB (preserva LEAN philosophy do PRD)
  - Verificável: `ls -lh bloco_interface/web/static/fonts/ | awk '{sum+=$5} END {print sum}'`
- [ ] **AC-10:** Formato woff2 para todas as fontes (suporte universal navegadores modernos, melhor compressão)

### Documentação (SHOULD)

- [ ] **AC-11:** Atualizar `governance/TECH-DEBT.md` marcando TD-WEB-LGPD-CDN-01 como **RESOLVED** com data e commit hash
- [ ] **AC-12:** Atualizar `bloco_interface/web/templates/base.html` com comentário curto explicando self-host (se necessário para futura referência)

---

## Tasks / Subtasks

### Phase A — Research & Download (10min)

- [ ] **A.1** Identificar fonte de download woff2 confiável para Manrope/Fraunces/JetBrains Mono
  - Opção primária: [google-webfonts-helper](https://gwfh.mranftl.com/fonts) (interface fácil, gera @font-face + zip)
  - Opção alternativa: GitHub repos oficiais ([Manrope](https://github.com/sharanda/manrope), [Fraunces](https://github.com/undercasetype/Fraunces), [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono))
- [ ] **A.2** Baixar Manrope weights 400/500/600/700 em woff2 (subset latin)
- [ ] **A.3** Baixar Fraunces weight 500 em woff2 (estático ou variable opsz axis)
- [ ] **A.4** Baixar JetBrains Mono weights 400/500 em woff2 (subset latin)

### Phase B — Estrutura de arquivos (5min)

- [ ] **B.1** Criar diretório `bloco_interface/web/static/fonts/`
- [ ] **B.2** Mover/copiar arquivos woff2 para o diretório
- [ ] **B.3** Verificar tamanho total ≤ 200KB

### Phase C — Edição de templates + CSS (10min)

- [ ] **C.1** Editar `bloco_interface/web/templates/base.html`:
  - Remover 3 link tags (preconnect googleapis, preconnect gstatic, stylesheet googleapis)
  - Manter apenas `<link rel="stylesheet" href="/static/tokens.css">` e `<link rel="stylesheet" href="/static/app.css">`
- [ ] **C.2** Editar `bloco_interface/web/static/tokens.css` — adicionar `@font-face` declarations no topo:
  ```css
  @font-face {
    font-family: 'Manrope';
    font-style: normal;
    font-weight: 400;
    font-display: swap;
    src: url('/static/fonts/manrope-400.woff2') format('woff2');
  }
  /* ... outros weights ... */
  ```
- [ ] **C.3** Manter as variáveis `--f-ui`, `--f-display`, `--f-mono` em `:root` (já apontam para nomes corretos)

### Phase D — Validação (5min)

- [ ] **D.1** Subir uvicorn: `python -m uvicorn bloco_interface.web.app:app --port 8501 --reload`
- [ ] **D.2** Verificar AC-1 e AC-2 via curl (zero requisições para fonts.googleapis OR fonts.gstatic)
- [ ] **D.3** Verificar AC-4 via curl (HTTP 200 nos arquivos /static/fonts/*.woff2)
- [ ] **D.4** Smoke browser test Eric: abrir `http://127.0.0.1:8501` em browser e comparar visualmente com versão anterior
- [ ] **D.5** Rodar suite testes: `python -m pytest --no-cov` → 232 passed + 1 skipped

### Phase E — Documentação (3min)

- [ ] **E.1** Atualizar `governance/TECH-DEBT.md`:
  - Mover TD-WEB-LGPD-CDN-01 da seção "HIGH (1)" para "Resolved Findings"
  - Adicionar entry: `Resolved: 2026-05-05 | Story REV-INT-02 | Resolution: Self-hosted fonts em /static/fonts/, 0 CDN external requests`
- [ ] **E.2** Adicionar entry no Change Log da story (Dev Agent Record section)

### Phase F — Handoff próximo agente (2min — owner @dev sinaliza completion)

- [ ] **F.1** Status: `Ready for Review`
- [ ] **F.2** Notificar @qa (Oracle) para gate
- [ ] **F.3** Após Oracle PASS, notificar @devops (Operator) para commit + push

---

## Dev Notes

### Especificação técnica de fontes

| Família | Pesos | Formato | Tamanho estimado | Uso |
|---|---|---|---|---|
| Manrope | 400, 500, 600, 700 | woff2 (subset latin) | ~30-50KB total | UI body (`--f-ui`) |
| Fraunces | 500 | woff2 (estático OR variable opsz 9-144) | ~30-80KB | Display verdict (`--f-display`) |
| JetBrains Mono | 400, 500 | woff2 (subset latin) | ~40KB total | Mono code/badges (`--f-mono`) |
| **Total target** | — | — | **≤ 200KB** | — |

### Recomendação de fonte oficial

[google-webfonts-helper](https://gwfh.mranftl.com/fonts) é a forma mais rápida — interface gera zip + CSS @font-face pronto. Alternativa: download direto dos repos GitHub oficiais.

### Estratégia @font-face

Adicionar declarações no **topo de `tokens.css`** (mantém tudo em 1 arquivo, simplifica). Alternativa: criar `fonts.css` separado e importar no base.html — só recomendado se ficar > 50 linhas de @font-face.

### font-display strategy

- `font-display: swap` — fallback imediato com fonte de sistema, troca para Manrope/Fraunces quando carrega. Preserva FCP (First Contentful Paint).

### CSP futuro (out of scope desta story)

Esta story NÃO endereça CSP (`Content-Security-Policy`). TD-WEB-CSP-INLINE-01 (LOW) é story separada. Mas após self-host fontes, CSP `default-src 'self'` fica viável.

### Anti-pattern a evitar

❌ NÃO usar `@import url('/static/fonts/...')` em CSS — bloqueia render-blocking. Use `@font-face` declarations diretamente.
❌ NÃO baixar TTF/OTF — woff2 é universal e ~30% menor.
❌ NÃO baixar TODOS os weights de Fraunces — 500 é suficiente conforme `tokens.css`.

---

## Files to Modify

- `bloco_interface/web/templates/base.html` (remover 3 link tags Google Fonts)
- `bloco_interface/web/static/tokens.css` (adicionar @font-face declarations)
- `governance/TECH-DEBT.md` (mover TD-WEB-LGPD-CDN-01 para Resolved)

## Files to Add

- `bloco_interface/web/static/fonts/manrope-400.woff2`
- `bloco_interface/web/static/fonts/manrope-500.woff2`
- `bloco_interface/web/static/fonts/manrope-600.woff2`
- `bloco_interface/web/static/fonts/manrope-700.woff2`
- `bloco_interface/web/static/fonts/fraunces-500.woff2` (ou variable)
- `bloco_interface/web/static/fonts/jetbrains-mono-400.woff2`
- `bloco_interface/web/static/fonts/jetbrains-mono-500.woff2`

## Files NOT to Modify

- `bloco_interface/web/static/app.css` — não toca em estilos
- `bloco_interface/web/templates/index.html`, `partials/*.html` — não tocam em fontes
- `bloco_interface/web/app.py` — backend não muda

---

## Tests Required

### Smoke (curl)

```bash
# AC-1
test "$(curl -s http://127.0.0.1:8501/ | grep -c 'fonts.googleapis')" -eq 0
# AC-2
test "$(curl -s http://127.0.0.1:8501/ | grep -c 'fonts.gstatic')" -eq 0
# AC-4
curl -sI http://127.0.0.1:8501/static/fonts/manrope-400.woff2 | head -1
# Esperado: HTTP/1.1 200 OK
```

### Regressão (pytest)

```bash
python -m pytest --no-cov
# Esperado: 232 passed, 1 skipped
```

### Browser test (Eric manual)

1. `python -m uvicorn bloco_interface.web.app:app --port 8501 --reload`
2. Abrir `http://127.0.0.1:8501`
3. DevTools > Network tab > recarregar
4. Verificar: zero requisições para `googleapis.com` ou `gstatic.com`
5. Verificar visualmente: tipografia Manrope/Fraunces idêntica à versão anterior

---

## Dependencies

### Upstream (this story depends on)

- ✅ REV-INT-01 (FastAPI + HTMX UI base) — DONE em commit `f6b935c`
- ✅ DEVOPS-01 partial (não bloqueia) — main HEAD `f146be4`

### Downstream (this story unblocks)

- 🔓 Release v0.2.0 gate condition #1 (zero CDN externos)
- 🔓 CSP strict policy (TD-WEB-CSP-INLINE-01) torna-se viável em story separada futura

---

## Definition of Done

Story está Done quando:

1. ✅ Todos os 12 ACs passam
2. ✅ @qa (Oracle) PASS gate (sem CRITICAL/HIGH novos)
3. ✅ Conventional commit pushed em main
4. ✅ CI verde
5. ✅ TECH-DEBT.md atualizado (TD-WEB-LGPD-CDN-01 → Resolved)
6. ✅ Story status atualizado para `Done`
7. ✅ Checkpoint sessão atualizado com SHA do commit

---

## Risk + Mitigation

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Visual regression sutil (kerning/leading diferente) | BAIXA | Visual identity | Smoke browser test Eric obrigatório; rollback rápido (revert link tags) |
| woff2 não suporta browser legacy | MUITO BAIXA | Compatibilidade | Eric usa Chrome/Firefox modernos; woff2 universal desde 2018+ |
| Tamanho total > 200KB | MÉDIA | LEAN philosophy | Subset latin only; remover weights não usados; medir final size |
| @font-face syntax error | BAIXA | Render quebra | Validar via DevTools > Console (zero erros) |

---

## Change Log

| Data | Sessão | Quem | Ação |
|---|---|---|---|
| 2026-05-05 | 86 | @sm (River) | Story criada (status Ready) — Sprint 02 priority 2 |
| 2026-05-05 | 86 | @po (Keymaker) | Validate-story-draft: GO (10/10) — story aprovada para development |
| 2026-05-05 | 86 | @dev (Neo) | Implementação completa: 7 fontes self-hosted, base.html + tokens.css + TECH-DEBT atualizados; 11/12 ACs PASS (AC-3 visual pendente Oracle/Eric); status → Ready for Review |

---

## Validation Notes (@po Keymaker)

### 10-Point Checklist

| # | Critério | Status | Evidência |
|---|---|---|---|
| 1 | Story title clear/específico | ✅ PASS | "Self-host Google Fonts (LGPD on-premise)" — preciso e contextual |
| 2 | User story format completo (As/I want/so that) | ✅ PASS | Linhas 31-33 presentes com persona, motivação e benefício explícitos |
| 3 | ACs ≥5 testáveis com critérios numéricos | ✅ PASS | 12 ACs (4 Func + 3 Visual + 3 Quality + 2 Docs), todos com critério de verificação (curl returns 0, HTTP 200, file size ≤200KB, suite 232/1) |
| 4 | Tasks/Subtasks granulares com checkbox | ✅ PASS | 6 phases (A-F), ~20 subtasks, todos com `[ ]` checkbox e effort estimado |
| 5 | Dependencies explícitas (upstream/downstream) | ✅ PASS | Upstream (REV-INT-01 ✅, DEVOPS-01 partial não bloqueia), Downstream (release v0.2.0 gate #1, CSP strict policy futuro) |
| 6 | Files to modify/add listados | ✅ PASS | 3 modify (base.html, tokens.css, TECH-DEBT.md) + 7 add (4 Manrope + 1-2 Fraunces + 2 JetBrains) + Files NOT to Modify (defensive) |
| 7 | Tests required cobrem ACs | ✅ PASS | Smoke curl (AC-1, AC-2, AC-4) + pytest (AC-8) + browser test (AC-3, AC-5, AC-6, AC-7) |
| 8 | Risk + Mitigation documentado | ✅ PASS | 4 riscos com Probabilidade/Impacto/Mitigação (visual regression, woff2 legacy, tamanho >200KB, syntax error) |
| 9 | Effort estimado realista | ✅ PASS | 30min total com phase breakdown (10+5+10+5+3+2 = 35min — alinhado com estimate macro) |
| 10 | Status correto (Ready) | ✅ PASS | `status: Ready` no frontmatter; `created_by: @sm (River)` rastreável |

**Score: 10/10 — GO**

### Decisão

✅ **GO (APROVADA)** — Story REV-INT-02 está pronta para development. @dev (Neo) pode prosseguir com `*develop`.

### Observações não-bloqueantes (advisory)

1. **AC-9 verificação de tamanho** — comando `awk '{sum+=$5}'` retorna bytes; @dev deve adicionar assertion explícita `[ $size -le 204800 ]` (200KB) ou usar `du -sh`. Sugestão para Dev Notes adicional, não bloqueia.
2. **Phase F.1 vs DoD #6** — Phase F diz "Status: Ready for Review" (handoff Neo→Oracle), DoD diz status final `Done` (após push). Semantica clara: Ready for Review é estado intermediário; Done é após Oracle PASS + push. Aceitável.
3. **AC-12 é SHOULD** — comentário em base.html explicando self-host é nice-to-have. OK manter como SHOULD.

### Forças destacadas (vale propagar a outras stories Sprint 02+)

- **Anti-patterns explícitos** ("NÃO usar @import", "NÃO TTF/OTF", "NÃO todos os weights Fraunces") — preventivo de erros @dev
- **Rollback path explícito** ("revert link tags") na coluna Mitigação — operacionalmente útil
- **Cross-reference completo** com PRD v1.0.3 DELTA + TECH-DEBT + handoffs — rastreabilidade total
- **Files NOT to Modify** — escopo defensivo evita scope creep

### Próximo handoff

**H-S02-INT02-po2dev** → @dev (Neo) `*develop REV-INT-02` — Workflow estrito, status Ready aprovado.

— Keymaker, equilibrando prioridades 🎯

## Dev Agent Record

### Agent Model Used

claude-opus-4-7[1m] via Skill `LMAS:agents:dev` (Neo persona, sessão 86, 2026-05-05).

### Debug Log References

- Phase A: Download via @fontsource/jsdelivr CDN (`https://cdn.jsdelivr.net/npm/@fontsource/{family}/files/{family}-latin-{weight}-normal.woff2`) — 7 fontes em batch, ~117KB total.
- Phase B+C: base.html removidas 3 link tags + comentário explicativo; tokens.css adicionado bloco `@font-face` (7 declarations) no topo, antes de `:root`.
- Phase D smoke: uvicorn :8501 → curl validations AC-1/AC-2/AC-4 passaram; pytest 232/1 passou.

### Completion Notes List

**Implementação direta sem desvios:**

- Decisão técnica: usar `@fontsource/*` via jsdelivr CDN para download (mais confiável que google-webfonts-helper que requer interface). Apenas para download — fontes ficam self-hosted após.
- Decisão técnica: Fraunces 500 estático (não variable opsz) — single weight conforme spec section 6 da spec design + estático é mais simples.
- AC-9 strictness aplicada conforme advisory Keymaker: `[ "$total_bytes" -le 204800 ]` → 117536 bytes ≤ 204800 (57% do limite).
- Anti-patterns respeitados: woff2 only, weights exatos da spec, `font-display: swap` em todas declarations.
- @font-face declarations adicionadas no topo de tokens.css (não em arquivo separado) — escolha por simplicidade dado o tamanho total (~50 linhas, abaixo do threshold de "criar fonts.css separado").
- Variáveis `--f-ui`, `--f-display`, `--f-mono` em `:root` mantidas inalteradas (já apontavam para 'Manrope', 'Fraunces', 'JetBrains Mono').
- AC-12 (comentário em base.html): adicionado comentário curto explicando self-host + referência REV-INT-02.

**Validations passadas:**

| AC | Resultado | Evidência |
|---|---|---|
| AC-1 zero fonts.googleapis | ✅ PASS | curl ... \| grep -c 'fonts.googleapis' = 0 |
| AC-2 zero fonts.gstatic | ✅ PASS | curl ... \| grep -c 'fonts.gstatic' = 0 |
| AC-3 visual preservation | ⏳ PENDING | smoke browser test Eric (Oracle gate) |
| AC-4 fontes /static/fonts/ HTTP 200 | ✅ PASS | 7/7 fontes retornam HTTP 200 |
| AC-5 Manrope em UI body | ✅ PASS | --f-ui → 'Manrope' (inalterado) |
| AC-6 Fraunces APENAS verdict | ✅ PASS | --f-display → 'Fraunces' apenas em .verdict-status, .verdict-num, .criterio-score |
| AC-7 JetBrains Mono code/badges | ✅ PASS | --f-mono → 'JetBrains Mono' inalterado |
| AC-8 suite 232+1 zero regressão | ✅ PASS | pytest --no-cov: 232 passed, 1 skipped, 64.88s |
| AC-9 ≤ 200KB (assertion strict) | ✅ PASS | 117536 bytes ≤ 204800 (Keymaker advisory aplicada) |
| AC-10 woff2 universal | ✅ PASS | 7/7 arquivos .woff2 |
| AC-11 TECH-DEBT.md atualizado | ✅ PASS | TD-WEB-LGPD-CDN-01 movido para Resolved Findings |
| AC-12 comentário base.html | ✅ PASS | Comentário curto adicionado |

**Total: 11/12 PASS (AC-3 pending Eric browser test no Oracle gate).**

### File List

**Files added (8):**

- `bloco_interface/web/static/fonts/manrope-400.woff2` (14108 bytes)
- `bloco_interface/web/static/fonts/manrope-500.woff2` (14044 bytes)
- `bloco_interface/web/static/fonts/manrope-600.woff2` (14172 bytes)
- `bloco_interface/web/static/fonts/manrope-700.woff2` (14212 bytes)
- `bloco_interface/web/static/fonts/fraunces-500.woff2` (18000 bytes)
- `bloco_interface/web/static/fonts/jetbrains-mono-400.woff2` (21168 bytes)
- `bloco_interface/web/static/fonts/jetbrains-mono-500.woff2` (21832 bytes)
- (governance/stories/REV-INT-02-self-host-fonts.md já existia — Validation Notes + Dev Agent Record adicionadas)

**Files modified (3):**

- `bloco_interface/web/templates/base.html` (removidas 3 link tags Google Fonts + comentário REV-INT-02)
- `bloco_interface/web/static/tokens.css` (adicionados bloco @font-face com 7 declarations no topo)
- `governance/TECH-DEBT.md` (TD-WEB-LGPD-CDN-01 HIGH (1) → HIGH (0) + entry em Resolved Findings)

---

## QA Results

### Gate: **PASS** ✅ (Oracle, sessão 86, 2026-05-05)

**Verdict resumo:** Implementação resolve TD-WEB-LGPD-CDN-01 HIGH com elegância arquitetural. 11/12 ACs PASS firmes + AC-3 condicional (visual preservation pendente smoke browser Eric durante deploy). Zero findings adversariais.

### Probes adversariais (5/5 PASS)

| # | Probe | Resultado |
|---|---|---|
| 1 | Grep recursivo zero CDN externo em `bloco_interface/web/` | ✅ Única match é comentário documentando ausência |
| 2 | @font-face URLs corretos em tokens.css | ✅ 7 declarations, todas /static/fonts/ + woff2 |
| 3 | File size strict assertion ≤ 204800 | ✅ 117536 bytes (57% do limite) |
| 4 | Uvicorn smoke + endpoints adicionais (/reset, /verdict) | ✅ Defense-in-depth — todos endpoints limpos |
| 5 | Smoke visual (Eric browser test) | ⏳ Condicional — Operator solicita pré-push |

### Self-critique adversarial

- ✅ Grep amplo `https?://[a-z]` em todo `bloco_interface/web/` → 0 matches
- ✅ htmx.min.js sem URLs externos
- ✅ font-display: swap mitiga FOIT
- ✅ @fontsource latin subset cobre PT-BR (ç, ã, õ)

### Forças destacadas

- **Defense-in-depth:** comentário em tokens.css cria rastreabilidade textual além do código
- **AC-9 strict assertion** aplicada exatamente conforme advisory Keymaker (não watered-down)
- **Endpoints adicionais auditados** (/reset, /verdict) sem ter sido solicitado — Neo foi além do mínimo
- **Substituição cirúrgica** — zero churn (3 link tags removidos + 7 @font-face adicionados)

### Decisão

✅ **PASS** — Story tecnicamente aprovada para deploy. Operator deve solicitar Eric smoke browser ANTES de push final para validar AC-3 visual preservation.

### Gate document

Detalhes completos em `governance/qa/qa-gate-story-rev-int-02-self-host-fonts.md`

— Oracle, guardião da qualidade 🛡️

---

*Story REV-INT-02 — River (sessão 86, 2026-05-05) · Sprint 02 priority 2 · Resolve TD-WEB-LGPD-CDN-01 HIGH · 30min effort estimado.*

— River, removendo obstáculos 🌊
