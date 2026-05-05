---
type: qa-gate
title: "QA Gate STORY 9 — Integração End-to-End (Pipeline)"
project: revisor-contratual
gate_for: "STORY-9-integracao-e2e"
date: "2026-05-02"
agent: "@qa (Oracle)"
verdict: PASS
tags:
  - project/revisor-contratual
  - qa-gate
  - story-9
  - integracao-e2e
  - phase-3
---

# QA Gate STORY 9 — Integração End-to-End

> **Linhagem:** Sessão 63 (sucessor de QA Gate STORY 8 SUB-C PASS sessão 60).
> **Phase:** 3 (Integração) — primeiro story.
> **Authority:** QA quality gate formal (advisory PASS / CONCERNS / FAIL / WAIVED).

## Cabeçalho 3 linhas

[@qa · Oracle · Test Architect & Quality Advisor] — quality gate STORY 9 integração end-to-end
**VEREDICTO: PASS** (1 LOW UX/error clarity em fallback OCR + 3 tech debts Neo já registrados; 0 CRITICAL/HIGH/MEDIUM)
**Recomendação:** APROVADO — pipeline integrado funcional. Próximo: smoke E2E real (Ollama+modelos+httpx) OU bloco_interface.

---

## 1. Escopo auditado

| Artefato | Linhas | Cobertura |
|---|---|---|
| `bloco_workflow/pipeline.py` | 260 | TestPipelineHappyPath (3) + TestPipelineEdgeCases (6) + TestPipelineCalculoEdge (1) + 8 probes Oracle |
| `tests/integration/test_pipeline_e2e.py` | ~430 | self |
| `tests/integration/__init__.py` | 1 | n/a |
| `bloco_workflow/__init__.py` (delta `+revisar_contrato + PipelineError + VaultEmptyError`) | 3 linhas | n/a |

**Suite agregada:** 203 passed + 1 skipped (smoke F-MIN-02 sem Ollama), 0 failed, runtime 59.90s.
**Delta vs Phase 2.B sessão 60:** 193 → 203 (+10 integração).

---

## 2. Verificações executadas (D1-D8)

### D1 — Orquestração 7 blocos correta

| Step | Bloco | Confirmação |
|---|---|---|
| 1 | `bloco_engine.parsing.parse_contract` | Signature compatível (pdf_path + injections) ✓ |
| 2 | `bloco_engine.ferramentas_calculo.{aa_to_am, calcular_pmt_*, gerar_tabela_amortizacao, classificar_anatocismo, sumulas_aplicaveis}` | Signature corrigida pelo Neo (instituicao_sfn + pactuacao_expressa default MVP) ✓ |
| 3 | `bloco_engine.bacen.BacenClient.fetch_taxa_modalidade` | bacen_cache_dir injetável (Neo descobriu cache $HOME) ✓ |
| 4 | `bloco_vault.buscar_hibrida` | Signature compatível; query heurística MVP ✓ |
| 5 | `bloco_workflow.run_personas_paralelas` | asyncio.gather REAL (F-MIN-02 RESOLVED em STORY 7) ✓ |
| 6 | `bloco_workflow.personas.juiz_revisar` | Signature kwargs-only respeitada ✓ |
| 7 | `bloco_audit.append_audit_entry` | Audit chain HMAC preservada ✓ |

**PASS — todas as signatures compatíveis; tipos fluem corretamente entre steps.**

### D2 — Atomicidade audit ANTES do raise (probe Oracle 1)

| Verificação | Resultado |
|---|---|
| BACEN offline → `BacenFetchExhausted` raised | OK |
| `audit_path` existe ANTES do raise (file size > 0) | **PASS** ✓ |
| `verify_audit_integrity` retorna True após failure | **PASS** ✓ |
| Conteúdo registra `"status":"FAILED"` | **PASS** ✓ |
| Conteúdo registra `"error_type":"BacenFetchExhausted"` | **PASS** ✓ |

**PASS — auditabilidade total preservada mesmo em failure path.**

### D3 — Chain integrity após múltiplas falhas consecutivas (probe Oracle 2)

| Cenário | Resultado |
|---|---|
| Run 1 (PDFEncrypted) + Run 2 (BacenFetchExhausted) consecutivos | 2 entries no audit ✓ |
| `verify_audit_integrity` após 2 falhas | **PASS** ✓ |
| `entry2.previous_entry_hash == entry1.entry_hash` (encadeamento real) | **PASS** ✓ |
| entry1 registra `error_type=PDFEncrypted` | **PASS** ✓ |
| entry2 registra `error_type=BacenFetchExhausted` | **PASS** ✓ |

**PASS — falhas consecutivas mantêm chain válida (HMAC GENESIS robusto).**

### D4 — Resource cleanup BacenClient (probe Oracle 3)

| Verificação | Resultado |
|---|---|
| `BacenClient` instanciado dentro de try | OK |
| `try/finally: bacen_client.close()` presente | **PASS** ✓ |
| Pattern regex `try.*?finally.*?bacen_client\.close\(\)` match | **PASS** ✓ |

**PASS — diskcache.Cache fechado mesmo em exception (sem leak de file descriptors).**

### D5 — DI completa (probe Oracle 4)

| Parâmetro | Presente |
|---|---|
| pymupdf_fn | ✓ |
| marker_fn | ✓ |
| sgs_fetcher | ✓ |
| embedder_fn | ✓ |
| advogado_invoke_fn | ✓ |
| economista_invoke_fn | ✓ |
| audit_path | ✓ |
| vault_conn | ✓ |
| audit_secret_key | ✓ |
| genesis_lock_path | ✓ |
| bacen_cache_dir | ✓ |

**PASS — 11/11 parâmetros injetáveis confirmados na signature. Testes 100% offline reais.**

### D6 — Vault connection lifecycle (probe Oracle 5)

| Verificação | Resultado |
|---|---|
| Pipeline NÃO fecha vault_conn | **PASS** ✓ (caller responsabilidade — permite reuso entre calls) |

**PASS — separation of concerns correta. Pipeline não assume ownership da conexão.**

### D7 — Audit single-write em sucesso (probe Oracle 6)

| Verificação | Resultado |
|---|---|
| `append_audit_entry` chamado 2× no source | OK (1 em except + 1 em sucesso) |
| Sucesso path APÓS except (fora do try) | **PASS** ✓ — não há audit duplicado em sucesso |

**PASS — sucesso registra UMA entry; failure registra UMA entry. Sem dupla escrita.**

### D8 — Pecados Capitais (Ordem 10) — verificação

| Pecado | Status |
|---|---|
| Inventar dado/métrica não-mensurada | OK — `latencia_ms` da busca real; audit timestamp real; nada fabricado |
| Float em wire format monetário | OK — todas conversões via `Decimal` no `_calcular_pipeline` |
| Silenciar erro | OK — try/except tem `raise` no final; audit registra ANTES; sem swallow |
| Authority alheia | OK — Neo escreveu código; Oracle não escreve código |
| Cabeçalho ausente | OK — este documento tem cabeçalho 3 linhas |
| **Defesa em profundidade** | **OK** — auditabilidade em sucesso E falha; resource cleanup em finally; DI permite testes 100% offline |

**PASS — 0 violações + 1 mérito (defesa em profundidade auditável).**

---

## 3. Findings

### CRITICAL — 0
### HIGH — 0
### MEDIUM — 0

### LOW (1 nova observação Oracle + 3 tech debts já registrados pelo Neo)

- **F-PIPELINE-LOW-01** — Mensagem `ParserOCRRequired` confusa quando markdown insuficiente sem Marker disponível
  - **Cenário descoberto durante probe Oracle 2 (versão inicial):** se PyMuPDF retorna markdown curto demais (fidelity < 0.5) E `marker_fn` não foi injetado E ambiente não tem Marker instalado, o pipeline propaga `ParserOCRRequired` sem contexto adicional do que o usuário deve fazer.
  - **Impacto:** UX/error clarity. Usuário vê "Marker OCR não está instalado (extras=ocr)" mas talvez o problema real seja que o PDF é muito curto / não tem texto útil, não que precisa OCR.
  - **Mitigação possível:** envolver `parse_contract` no pipeline com try/except específico que ressanaliza o erro e fornece mensagem mais rica (ex: "PDF não tem texto suficiente — verifique se é digital ou escaneado; se escaneado, instale extras=ocr").
  - **Recomendação:** defer para STORY de UX/CLI — quando bloco_interface for criado, melhorar tratamento de error messages para humanos.

### Tech debts Neo já registrados — DEFERRED

| ID | Severidade | Status |
|---|---|---|
| TD-PIPELINE-QUERY-BUILDER | LOW | DEFERRED — query vault heurística MVP; query-builder dedicado pós-MVP |
| TD-PIPELINE-PACTUACAO | LOW | DEFERRED — `instituicao_sfn=True + pactuacao_expressa=True` default MVP; inferir de markdown via parsing semântico futuro |
| TD-PIPELINE-SMOKE-REAL | LOW | DEFERRED — smoke E2E real (Ollama+modelos+httpx STJ/STF+PDF físico) defer para STORY pós-integração |

---

## 4. Métricas

| Métrica | Valor |
|---|---|
| Testes integração | 10 |
| Testes suite agregada | 203 + 1 skipped = 204 |
| Falhas | 0 |
| Runtime suite agregada | 59.90s |
| Linhas código produção (pipeline.py) | 260 |
| Linhas código teste (test_pipeline_e2e.py) | ~430 (1.65× ratio teste:produção — saudável) |
| Probes Oracle adversariais executadas | 8 |
| Probes Oracle PASS | 8/8 |
| Bugs in-flight Neo (corrigidos antes do gate) | 3 |
| Findings CRITICAL/HIGH/MEDIUM | 0 |
| Findings LOW (novo Oracle) | 1 |
| Tech debts Neo (DEFERRED) | 3 |

---

## 5. Status findings cross-stories

| Finding | Status atual |
|---|---|
| F-PARSE-HIGH-01 | RESOLVED |
| F-MIN-02 (async paralelismo) | RESOLVED |
| F-LLM-MED-01 (Pydantic permissivo) | DEFERRED |
| F-VAULT-LOW-01 (NaN/Inf embedder) | DEFERRED |
| F-PIPELINE-LOW-01 (ParserOCRRequired UX — NOVO) | DEFERRED (STORY UX/CLI) |
| O-08 a O-13, TD-VAULT-* | DEFERRED |

---

## 6. Estado consolidado Phase 3 (#1 completo)

**8 blocos integráveis + 1 pipeline orquestrador:**

| # | Componente | Testes | QA Gate |
|---|---|---|---|
| 1-8 | bloco_contratos / engine / workflow / audit / vault | 193 | 8/8 PASS |
| 9 | **bloco_workflow.pipeline (revisar_contrato)** | **10** | **PASS — AGORA** |
| **Total** | — | **203 + 1 skip = 204** | **9/9 PASS** |

---

## 7. Recomendação ao Morpheus

**APROVADO — Phase 3 #1 completo.**

### Próximas opções para Eric

1. **STORY 10 — Smoke E2E real (TD-PIPELINE-SMOKE-REAL)** — Ollama+modelos baixados + httpx scrapers reais STJ/STF + PDF físico real; valida pipeline com IO completo
2. **STORY 10 — bloco_interface (CLI minimal)** — `revisor revisar <pdf>` CLI usando Click/Typer para usuário final
3. **STORY 10 — Hardening F-LLM-MED-01 + F-VAULT-LOW-01 + F-PIPELINE-LOW-01** — endurece schemas + UX error clarity

Recomendação Oracle: **opção 2 (CLI)** — pipeline funcional sem CLI é demonstrável apenas em testes; CLI minimal permite que Eric rode o pipeline manualmente com PDF próprio (mesmo com mocks de LLM). Smoke E2E real (opção 1) e hardening (opção 3) podem vir depois — CLI é o que falta para "produto utilizável end-to-end".

---

## 8. Linhagem governance

- Antecedente: `qa/qa-gate-story-8-sub-c-vault.md` (PASS sessão 60)
- Handoff de entrada: H-S01-E4.0-neo2qa7
- Handoff de saída: H-S01-E4.0-qa2mor7 (Oracle→Morpheus consolida)
- Sessão checkpoint: 63

---

*Oracle, guardião da qualidade — sete blocos integrados num único pipeline auditável; primeira completude do sistema.*
