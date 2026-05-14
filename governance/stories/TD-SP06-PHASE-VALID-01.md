---
type: story
id: TD-SP06-PHASE-VALID-01
title: "Validação UI fases pipeline + S7 error states real-time (UX robustez 3-5min LLM)"
status: Ready for Review
priority: 2
validated_by: "@po (Keymaker)"
validated_at: "2026-05-14"
validation_score: "10/10"
implemented_by: "@dev (Neo)"
implemented_at: "2026-05-14"
implementation_evidence: "PHASE_LABELS mapping + ERROR_CAUSES_PT mapping + showErrorRealS7 evoluído + 248 baseline maintained (Cancel button OPCIONAL deferred Sprint 6.1)"
sprint: "6.x AGGRESSIVE"
epic: "Sprint-6-Bloco-Beta-Frontend-Backend-Integration"
owner: "@dev (Neo)"
estimated_effort: "2h"
severity_origem: "MEDIUM (UX polish + robustez — pipeline real demora 3-5min, usuário precisa feedback claro)"
created: "2026-05-14"
created_by: "@sm (River)"
depends_on:
  - "TD-SP06-SPA-CONNECT-01 (EventSource handlers infrastructure)"
related_adrs:
  - "ADR-020 Multi-Doctype Dispatcher v2 (S7 error pane variants)"
  - "MVP-LEAN-01 Task 6 — AC-MVP-D3 + AC-MVP-MONITOR (C6 error variants)"
related_stories:
  - "TD-SP06-SPA-CONNECT-01 (precondition — SSE infrastructure)"
  - "TD-SP06-MODE-PASS-01 (complementar — 422 modalidade não-MVP → S7)"
related_findings:
  - "Smith Bloco α empirical timings: parsing ~2-5s, BACEN 16s, vault 16s, LLM 1m36s, total 3min30s"
  - "Smith Fase 7-A F-D1-08 MEDIUM: backend /pipeline-stream fallback mock graceful — perigoso prod"
unblocks:
  - "Eric demo robusta com error feedback claro"
  - "DoD Sprint 6: aplicação aceita falhas com diagnostic + cause + solution + alternative"
tags:
  - project/revisor-contratual
  - story
  - sprint-6
  - bloco-beta
  - phase-validation
  - s7-error-states
  - draft
---

# Story TD-SP06-PHASE-VALID-01 — UI Phase Validation + Error States

## Story

**Como** advogado revisor aguardando análise real (que pode demorar 3-5 minutos para inferência LLM paralela sabia-7b + qwen2.5),
**Eu quero** que cada fase do pipeline mostre status claro com timing aproximado (parsing → cálculo → BACEN → vault → personas → juiz) e que erros sejam exibidos com diagnóstico + causa + solução + alternativa em pane S7 dedicado,
**Para que** eu confie no processo (não pensar que app travou), saiba o que está acontecendo a cada momento, e possa tomar ação informada se algo falha (ex: vault vazio, modalidade não-MVP, Ollama down).

---

## Contexto

**Trigger:** Smith Bloco α 2026-05-14 evidenciou timings reais do pipeline:

| Fase | Timing empírico (Smith probe) |
|------|------------------------------|
| Parsing PyMuPDF4LLM | ~2-5s (PDF born-digital fidelity 1.0) |
| Cálculo Price + anatocismo | ~50ms (Python puro) |
| BACEN SGS fetch (live) | ~1-30s (HTTP + cache miss/hit) |
| Vault busca híbrida BM25+sqlite-vec | ~15-20s (BERT embedding query) |
| Personas LLM (sabia-7b + qwen2.5 paralelo) | ~60-180s (Ollama POST /api/chat 1m36s observed) |
| Juiz Python puro | ~10ms |
| **Total** | **~3min30s** (Smith empirical 02:04:06 → 02:07:37) |

3-5min sem feedback = usuário pensa app travou. Risco UX crítico.

Pipeline real já emite SSE events (`/revisar/stream/{job_id}` linha 771 app.py). TD-SP06-SPA-CONNECT-01 adiciona handlers básicos. Esta story polish UI + error robusto.

Backend tem `error_handler.py` C6 variants existentes (linha 424+ HTTP_STATUS_TO_C6_VARIANT). Reuso obrigatório (no invention).

---

## Acceptance Criteria

1. **AC-01:** SPA SSE event handlers atualizam UI com fase-aware timing expectations:
   - Fase "parsing_pdf" → label "Lendo seu contrato..." (esperado ~5s; warning >30s)
   - Fase "calculo" → label "Calculando Tabela Price + classificando anatocismo..." (esperado <1s)
   - Fase "bacen" → label "Consultando taxa BACEN (SGS API)..." (esperado ~10s; warning >60s)
   - Fase "vault" → label "Buscando jurisprudência STJ relevante..." (esperado ~20s; warning >60s)
   - Fase "personas" → label "Personas LLM analisando (Advogado + Economista)..." (esperado ~120s; warning >300s)
   - Fase "juiz" → label "Juiz validando aderência..." (esperado <1s)
   - Phase chip text dinâmico baseado em phase event payload (não hardcoded array)

2. **AC-02:** Timeout warnings progressivos:
   - >2x esperado → cor amarela + texto "Demorando mais que esperado..."
   - >5min sem progresso (último ping) → cor vermelha + texto "Pipeline pode ter travado. Aguarde até 30min ceiling ou cancele."
   - >30min total → automatic abort UI + audit `pipeline_timeout_30min` entry

3. **AC-03:** Phase-error event handler renderiza S7 error pane:
   - `title`: "Pipeline Interrompido em [Fase X]"
   - `diagnostic`: error_msg do backend (truncado 200 chars)
   - `cause`: error_type traduzido user-friendly:
     - `VaultEmptyError` → "Banco de jurisprudência vazio — Vault SQLite não populado"
     - `ModalidadeNaoSuportada` → "Modalidade contratual fora do MVP atual"
     - `NotImplementedError` → "Funcionalidade ainda em desenvolvimento"
     - `BacenFetchExhausted` → "API BACEN temporariamente indisponível e sem cache"
     - `OllamaSpawnFailed` → "Modelo LLM falhou ao inicializar"
     - `MetadataExtractionError` → "PDF sem metadados extraíveis (forneça UF + data manualmente)"
     - `ParserOCRRequired` → "PDF imagem-only — instale Marker OCR ou use PDF born-digital"
   - `solution`: ação concreta usuário pode tomar
   - `alternative`: workaround alternativo

4. **AC-04:** Reuso obrigatório de `bloco_interface/web/error_handler.py` C6 variants (HTTP_STATUS_TO_C6_VARIANT linha 424+). **NÃO duplicar mapping** — backend emite variant_key no payload error event.

5. **AC-05:** Loading state UI durante pipeline running:
   - Spinner OrSheva 7 visual (CSS animation)
   - Texto progress: "Fase [X] de 6: [phase_label]"
   - Tempo decorrido total (atualizado a cada ping 10s)
   - btnAnalyze disabled durante running

6. **AC-06:** Empirical evidence forced VaultEmptyError:
   - Operator move temp vault.db: `mv ~/.local/share/revisor-contratual/vault.db /tmp/vault-backup.db`
   - Eric upload PDF → SPA recebe phase-error event
   - S7 pane mostra: title "Pipeline Interrompido em Vault" + cause "Banco de jurisprudência vazio" + solution "Operator: rodar populate-vault --source all" + alternative "Tente novamente após repopulação"
   - Operator restore: `mv /tmp/vault-backup.db ~/.local/share/revisor-contratual/vault.db`

7. **AC-07:** Cancel button durante pipeline running (opcional Sprint 6 AGGRESSIVE — pode defer Sprint 6.1 se trivial):
   - SPA mostra botão "Cancelar Análise" visível durante state running
   - Click → SPA chama `EventSource.close()` + opcional `POST /revisar/cancel/{job_id}` (criar endpoint backend)
   - Backend marca JOBS[job_id]["status"] = "aborted" + audit entry `pipeline_aborted_user`

---

## Tasks / Subtasks

- [ ] Task 1: SPA phase labels mapping
  - [ ] 1.1 Mapping declarativo phase_key → {label, expected_s, warning_s} em const top do SPA script
  - [ ] 1.2 Reusar para phaseChip text dinâmico
- [ ] Task 2: SPA timeout warnings progressivos
  - [ ] 2.1 setTimeout watchers por fase com thresholds 2x esperado + 5min global
  - [ ] 2.2 CSS class swap amarelo/vermelho
  - [ ] 2.3 30min auto-abort UI
- [ ] Task 3: SSE phase-error handler S7 pane
  - [ ] 3.1 `showErrorRealS7({diagnostic, cause, solution, alternative})` function
  - [ ] 3.2 HTML structure S7 pane (reuso CSS app.css existing)
  - [ ] 3.3 Hide processing UI + show S7 + Disable spinner
  - [ ] 3.4 Botão "Tentar Novamente" → reset state + permite re-upload
- [ ] Task 4: error_type tradução PT-BR friendly
  - [ ] 4.1 Mapping client-side error_type → user-friendly cause
  - [ ] 4.2 Fallback genérico "Erro inesperado: {error_type}" para casos não-mapeados
- [ ] Task 5: Loading state polish OrSheva 7
  - [ ] 5.1 Spinner CSS animation (tokens.css var --accent)
  - [ ] 5.2 Tempo decorrido formatted "0:34" / "2:15" etc
  - [ ] 5.3 btnAnalyze disabled state visual
- [ ] Task 6: Cancel button (OPCIONAL — defer se trivial)
  - [ ] 6.1 Backend POST /revisar/cancel/{job_id} (atualiza JOBS dict + audit)
  - [ ] 6.2 SPA click handler com confirmation
  - [ ] 6.3 AbortController EventSource cleanup
- [ ] Task 7: Tests
  - [ ] 7.1 Manual smoke: forced VaultEmptyError → S7 pane visible com texto correto
  - [ ] 7.2 Pytest baseline 248 passed maintained
- [ ] Task 8: Update File List + Change Log
- [ ] Task 9: Self-critique

---

## Dev Notes (Technical Context)

**SSE events shape backend (existente):**

```
event: phase-error
data: {
  "phase": "vault",
  "diagnostic": "Vault retornou docs=[] para query — Advogado não pode citar fundamentos.",
  "cause": "Vault vazio",
  "solution": "Rode: revisor populate-vault --source all",
  "alternative": "Verifique se DEFAULT_VAULT_DB path está correto"
}
```

Backend já emite `diagnostic / cause / solution / alternative` (Smith Bloco α probe confirmou).

**MVP-LEAN-01 Task 6 C6 variants** (`bloco_interface/web/error_handler.py`):

```python
HTTP_STATUS_TO_C6_VARIANT = {
    413: "disk_full_uploads",
    503: "ollama_unavailable",
    422: "modalidade_unsupported",
    # ...
}
```

Reusar payloads C6 — backend `error_handler.get_c6_payload(variant_key)` retorna dict completo.

**error_type → cause user-friendly mapping** (client-side traduzido):

```javascript
const ERROR_CAUSES_PT = {
  VaultEmptyError: "Banco de jurisprudência vazio — Vault SQLite não populado",
  ModalidadeNaoSuportada: "Modalidade contratual fora do MVP atual",
  NotImplementedError: "Funcionalidade ainda em desenvolvimento",
  BacenFetchExhausted: "API BACEN temporariamente indisponível e sem cache",
  OllamaSpawnFailed: "Modelo LLM falhou ao inicializar",
  MetadataExtractionError: "PDF sem metadados extraíveis (forneça UF + data manualmente)",
  ParserOCRRequired: "PDF imagem-only — instale Marker OCR ou use PDF born-digital",
};
```

**Locations relevantes** SPA `static/index.html`:
- linha 1832 `STEP_NAMES` array — substituir por mapping phase_key
- linha 1841 `phaseChip.textContent` — dynamic
- linha 1843 `progressMeta.textContent` — dynamic
- linhas pré-screen-app onde S7 error pane HTML deve ser added (ou já existe — Neo verifica)

**TDs catalogados pendentes Sprint 6+** (não bloqueadores):
- TD-SP06-CLI-DISPLAY-UTF8-WIN-CP1252 (CLI only, não SPA)
- TD-SP06-OLLAMA-DUAL-PORT-VERIFICATION (irrelevante UX)

---

## Testing

**Manual smoke E2E (Operator pós-implementação Neo):**

```bash
# 1. Baseline - pipeline real funciona
# Eric upload veiculo synthetic → veredito APROVADO_100

# 2. Forced VaultEmptyError
mv ~/.local/share/revisor-contratual/vault.db /tmp/vault-backup.db
# Eric upload → SPA mostra S7 pane "Pipeline Interrompido em Vault"
mv /tmp/vault-backup.db ~/.local/share/revisor-contratual/vault.db

# 3. Forced ModalidadeNaoSuportada (depende TD-SP06-MODE-PASS-01)
# Eric clica "Imobiliário" → upload → SPA bloqueia OR S7 "Pipeline Interrompido em BACEN"

# 4. Timeout warning (mocked slow LLM)
# Operator pode forçar Ollama overload OR mock long sleep — opcional
```

**Pytest baseline:** mesmo comando TD-SP06-CLASSIC-01.

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
| 2026-05-14 | @sm (River) | Draft inicial Bloco β Sprint 6 AGGRESSIVE — UX robustez 3-5min |
