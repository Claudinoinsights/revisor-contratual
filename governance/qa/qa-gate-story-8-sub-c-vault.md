---
type: qa-gate
title: "QA Gate STORY 8 SUB-C — bloco_vault"
project: revisor-contratual
gate_for: "STORY-8-SUB-C-bloco_vault"
date: "2026-05-02"
agent: "@qa (Oracle)"
verdict: PASS
tags:
  - project/revisor-contratual
  - qa-gate
  - story-8-sub-c
  - vault
  - phase-2.B-DONE
---

# QA Gate STORY 8 SUB-C — bloco_vault

> **Linhagem:** Sessão 60 (sucessor de QA Gate STORY 7 SUB-D PASS sessão 57).
> **Domínio:** software-dev / legaltech.
> **Authority:** QA quality gate formal (advisory PASS / CONCERNS / FAIL / WAIVED).

## Cabeçalho 3 linhas

[@qa · Oracle · Test Architect & Quality Advisor] — quality gate STORY 8 SUB-C bloco_vault
**VEREDICTO: PASS** (1 LOW observation NaN no embedder + 4 tech debts Neo já documentados; 0 CRITICAL/HIGH/MEDIUM)
**Recomendação:** APROVADO — Phase 2.B FECHADA com 7/7 blocos prontos. STORY 9 = integração end-to-end.

---

## 1. Escopo auditado

| Artefato | Linhas | Cobertura |
|---|---|---|
| `bloco_vault/__init__.py` | 47 | re-export — N/A |
| `bloco_vault/schema.py` | 60 | TestSchema (3) + probe Oracle 3 |
| `bloco_vault/embedder.py` | 52 | TestEmbedder (3) + probe Oracle 3.4 (dim mismatch server) |
| `bloco_vault/repository.py` | 110 | TestRepository (5) + probe Oracle 4 (round-trip vigente_em + superseded_by) |
| `bloco_vault/busca.py` | 115 | TestBuscaHibrida (5) + probe Oracle 2 (RRF matemática) |
| `bloco_vault/scrapers/base.py` | 57 | TestScrapersWhitelist (4) + probe Oracle 1+6 (whitelist adversarial) |
| `bloco_vault/scrapers/stj_sumulas.py` | 75 | TestScraperSTJ (2) + probe Oracle 5 |
| `bloco_vault/scrapers/stf_sumulas_vinculantes.py` | 80 | TestScraperSTF (2) + probe Oracle 5.2 (dedupe) |
| `tests/unit/test_vault.py` | 290 | self |
| `tests/fixtures/scraper_html/*.html` (2 arquivos) | n/a | usados via httpx_fn fake |
| `pyproject.toml` (delta `+beautifulsoup4>=4.12`) | 1 linha | n/a |

**Suite agregada:** 193 passed + 1 skipped (smoke F-MIN-02 sem Ollama no ambiente), 0 failed, runtime 45.83s.
**Delta vs Phase 2.B sessão 57:** 167 → 193 (+26 vault).

---

## 2. Verificações executadas (D1-D7)

### D1 — FR-VAULT-01..04 cobertura

| FR | Implementação | Status |
|---|---|---|
| **FR-VAULT-01** persistência sqlite-vec 768 dims | `repository.insert_jurisprudencia` insere row + vec blob via `serialize_embedding` | PASS |
| **FR-VAULT-02** busca híbrida BM25 + vetorial + RRF | `busca.buscar_hibrida` orquestra; **probe Oracle 2 valida fórmula RRF** | PASS |
| **FR-VAULT-03** scrapers extraem JurisprudenciaItem | STJ + STF SV; **probe Oracle 5 confirma robustez (dedupe, ignorar curtos, ignorar sem número)** | PASS |
| **FR-VAULT-04** NFR-LGPD-01 whitelist scrapers | `ALLOWED_HOSTS` frozenset; **probe Oracle 1+6 validam 6 cenários adversariais** | PASS |

**PASS — 4/4 FR cobertos com probes adversariais independentes.**

### D2 — NFR-LGPD-01 whitelist adversarial (probe Oracle 1+6)

| Cenário adversarial | Resultado | Status |
|---|---|---|
| 1.1 URL com porta `:8443` | host extraído sem porta → autorizado | PASS — comportamento esperado |
| 1.2 URL com `user:pass@host` | host extraído sem credenciais → autorizado | PASS |
| 1.3 IP raw `200.120.43.1` | bloqueado (não está na whitelist) | PASS |
| 1.4 Case-mixed `WWW.STJ.JUS.BR` | normalizado para lower → autorizado | PASS |
| **1.5 Subdomain attack `www.stj.jus.br.evil.com`** | **bloqueado (whitelist é match exato, não startswith)** | **PASS — defesa crítica** |
| 1.6 URL sem schema | hostname=`''` → bloqueado | PASS |
| **6.3 default `_default_httpx_fetch` bloqueia ANTES de importar httpx** | confirmado — `httpx` não foi importado quando host inválido | **PASS — defesa em profundidade** |

**PASS — whitelist robusta a 7 cenários adversariais, incluindo subdomain attack.**

### D3 — RRF fusion matemática (probe Oracle 2)

| Verificação | Esperado | Resultado | Status |
|---|---|---|---|
| `_rrf_fuse` aplica `1 / (k + rank)` por lista | sim | confirmado pela matemática (delta < 1e-9) | PASS |
| Doc em ambas listas (#1 BM25 + #1 vec, k=60) | `2/(60+1) = 0.032787` | `0.032787` | PASS |
| Doc só em uma lista aparece com peso menor | sim | `1/63 = 0.015873` cada | PASS |
| Doc 100 (em ambos #1) ranqueado primeiro | sim | confirmado | PASS |
| `k=0` degenerado mas não levanta | `1/1 + 1/1 = 2.0` | `2.0` | PASS |

**PASS — RRF matematicamente correto. Fórmula clássica.**

### D4 — Schema sqlite-vec idempotente + virtual table

| Aspecto | Status |
|---|---|
| `init_vault` rodável múltiplas vezes (`CREATE IF NOT EXISTS`) | PASS — `test_init_vault_idempotente` |
| `jurisp_vec` virtual table criada | PASS |
| `sqlite_vec.load(conn)` chamado dentro de init_vault | PASS — não falha em re-init |
| Indexes criados (court, topic, vigente_em) | PASS |
| `EMBEDDING_DIMS=768` constante consistente entre schema/embedder | PASS |

### D5 — Repository CRUD round-trip + IntegrityError

| Cenário | Status |
|---|---|
| Insert + get_by_id_doc round-trip preserva todos os campos | PASS — `test_insert_e_get_round_trip` |
| **Round-trip `vigente_em` (date)** | **PASS — probe Oracle 4.1** |
| **Round-trip `superseded_by` (str / None)** | **PASS — probe Oracle 4.1** |
| **Round-trip `modalidade_relacionada=[]` (lista vazia)** | **PASS — probe Oracle 4.2** (JSON serializa `[]` corretamente) |
| Doc duplicado levanta `IntegrityError` (UNIQUE id_doc) | PASS — `test_insert_duplicado_levanta_integrity` |
| `get_by_id_doc` inexistente levanta `JurisprudenciaNotFound` | PASS |
| `count` inicial = 0 | PASS |
| `list_all` preserva ordem de inserção (rowid AUTOINCREMENT) | PASS |

### D6 — Embedder dim mismatch hard-fail (defesa em 2 camadas)

| Camada | Comportamento | Status |
|---|---|---|
| **Cliente — `serialize_embedding`** | `len != 768 → ValueError("dim mismatch")` | PASS — `test_serialize_embedding_dim_errado_levanta` |
| **Servidor — sqlite-vec** | dim mismatch no INSERT → `OperationalError("Dimension mismatch")` | PASS — **probe Oracle 3.4** |

**PASS — defesa em 2 camadas; embedder mal-construído é interceptado em 2 pontos distintos.**

### D7 — Scrapers ParseError robustez (probe Oracle 5)

| Cenário | Resultado | Status |
|---|---|---|
| HTML sem elementos `class~="sumula"` | `ScraperParseError("Nenhum elemento")` | PASS |
| HTML com numeração romana (não bate regex `\d+`) | `ScraperParseError("nenhum com formato 'Súmula NNN'")` | PASS |
| HTML STJ com texto < 20 chars (Pydantic min_length) | item ignorado silenciosamente (OK) | PASS |
| HTML STJ com elementos sem número | item ignorado silenciosamente (OK) | PASS |
| **HTML STF com SV4 duplicada (formato diferente)** | **dedupe via `seen_numeros` → 1 SV4 retornado** | **PASS** |

**PASS — scrapers fail-loud quando estrutura inteira muda; fail-quiet apenas para items individuais malformados (apropriado).**

### D8 — Pecados Capitais (Ordem 10) — verificação

| Pecado | Status |
|---|---|
| Inventar dado/métrica não-mensurada | OK — RRF MEDIDO matematicamente; whitelist VERIFICADA empiricamente; latência `latencia_ms` real |
| Float em wire format monetário | n/a (vault não persiste valores monetários) |
| Silenciar erro | OK — scrapers levantam ParseError fail-loud; embedder dim mismatch hard-fail; integrity error não silenciado |
| Authority alheia | OK — Neo escreveu código; Oracle não escreve código |
| Cabeçalho ausente | OK — este documento tem cabeçalho 3 linhas |
| **Defesa em profundidade** | **OK — embedder valida 2× (cliente + servidor); httpx bloqueia ANTES de importar lib** |

**PASS — 0 violações + 1 mérito (defesa em profundidade).**

---

## 3. Findings

### CRITICAL — 0
### HIGH — 0
### MEDIUM — 0

### LOW (1 nova observação Oracle + 4 tech debts já registrados pelo Neo)

- **F-VAULT-LOW-01** — sqlite-vec aceita NaN/Inf no embedding silenciosamente (probe Oracle 3.2/3.3)
  - Comportamento: insert de vetor com NaN PASSA; query MATCH retorna `distance=None`. Vetor com `1e30` aceita; query devolve `inf` ou `0.0` (depende da posição relativa).
  - Risco: embedder defeituoso pode poluir vault sem warning. Defesa primary é arquitetural (sentence-transformers com `normalize_embeddings=True` nunca produz NaN).
  - Mitigação possível: validar `not any(math.isnan(x) or math.isinf(x) for x in embedding)` em `serialize_embedding`. Cost: O(768) por insert — desprezível.
  - **Recomendação:** acrescentar guard NaN/Inf em `serialize_embedding` quando expandir scope ou adicionar embedder customizado. Defer enquanto único embedder em uso é sentence-transformers normalize=True.

### Tech debts já registrados pelo Neo (DEFERRED)

| ID | Severidade | Status |
|---|---|---|
| TD-VAULT-LOAD-TEST | MEDIUM | DEFERRED — DP-08 sqlite-vec v0.1 load test 10k+ rows; STORY hardening pós-MVP |
| TD-VAULT-TJ | LOW | DEFERRED — scrapers TJ estaduais quando expansão multi-UF |
| TD-VAULT-LEGAL-BERTIMBAU | LOW | DEFERRED — Legal-BERTimbau-sts-base específico quando publicado |
| TD-VAULT-TOPIC-INDETERMINADO | LOW | DEFERRED — classificação automática quando vault crescer |

---

## 4. Métricas

| Métrica | Valor |
|---|---|
| Testes vault | 26 |
| Testes suite agregada | 193 + 1 skipped = 194 |
| Falhas | 0 |
| Runtime suite agregada | 45.83s |
| Linhas código produção (vault) | 596 (9 módulos) |
| Linhas código teste (test_vault.py) | 290 (0.49× ratio teste:produção — abaixo do ideal 1.0×; compensado por 6 probes Oracle adversariais externos) |
| Cobertura cenários | 26 testes Neo + 6 probes Oracle adversariais (whitelist 7 sub-cenários, RRF 5 sub-cenários, sqlite-vec 4, repository 4, scrapers 5) |
| Probes Oracle adversariais executadas | 6 |
| Probes Oracle PASS | 6/6 |
| FR cobertos | 4/4 (FR-VAULT-01..04) |
| Findings CRITICAL/HIGH/MEDIUM | 0 |
| Findings LOW (novo Oracle) | 1 |
| Tech debts (já documentados Neo) | 4 |

---

## 5. Estado consolidado Phase 2.B (FECHADA)

**7/7 blocos prontos para integração STORY 9:**

| # | Bloco | Testes | Phase | QA Gate |
|---|---|---|---|---|
| 1 | bloco_contratos | 22 | 2.A | PASS |
| 2 | bloco_engine/ferramentas_calculo | 38 | 2.A | PASS |
| 3 | bloco_workflow/personas/juiz | 23 | 2.A | PASS |
| 4 | bloco_audit | 26 | 2.A | PASS |
| 5 | bloco_engine/bacen | 16 | 2.B-S5 | PASS |
| 6 | bloco_engine/parsing | 28 | 2.B-S6 | PASS (RE-GATE pós F-PARSE-HIGH-01) |
| 7 | bloco_workflow/personas/{advogado,economista,llm_factory} | 14 | 2.B-S7 | PASS (F-MIN-02 RESOLVED) |
| 8 | **bloco_vault** | **26** | **2.B-S8** | **PASS — AGORA** |
| **Total** | **8 blocos integráveis** | **193 + 1 xfail-resolved + 1 skip** | — | **8/8 PASS** |

---

## 6. Status findings cross-stories

| Finding | Status atual |
|---|---|
| F-PARSE-HIGH-01 (STORY 6) | RESOLVED |
| F-MIN-02 (ADR-003 PATCH 2) | RESOLVED |
| F-LLM-MED-01 (Pydantic permissivo) | DEFERRED (STORY hardening pós-MVP) |
| O-08/O-09/O-10/O-11/O-12/O-13 | DEFERRED |
| F-VAULT-LOW-01 (NaN/Inf embedder — NOVO) | DEFERRED (defesa primary arquitetural via sentence-transformers normalize) |

---

## 7. Recomendação ao Morpheus

**APROVADO — Phase 2.B FECHADA com sucesso.**

### Próxima etapa: STORY 9 = integração end-to-end

**Pipeline completo a montar:**
```
PDF upload
  ↓ bloco_engine/parsing
ContratoMetadata + ParsedContract
  ↓ bloco_engine/ferramentas_calculo (Decimal puro)
ResultadoCalculo + classificação anatocismo
  ↓ bloco_engine/bacen (cache TTL + fallback)
BacenData taxa_media
  ↓ bloco_vault.buscar_hibrida (RRF k=60)
top-K JurisprudenciaItem
  ↓ bloco_workflow.run_personas_paralelas (asyncio.gather)
TeseAdvogado + AnaliseMacroEconomica
  ↓ bloco_workflow.personas.juiz_revisar (Python puro)
VeredictoJuiz (APROVADO_100 / APROVADO_COM_RISCO_HITL / REJEITADO)
  ↓ bloco_audit.append_audit_entry (HMAC GENESIS chain)
Audit log forense
  ↓ bloco_interface (CLI / Streamlit — ainda não criado, defer)
Peça final OU Relatório de Inviabilidade
```

### 3 opções para Eric escolher

1. **STORY 9 integração end-to-end** ⭐ — 7/7 blocos prontos; valida pipeline completo + smoke test workflow_test
2. **STORY hardening F-LLM-MED-01 + F-VAULT-LOW-01** — endurece schemas Pydantic com `extra="forbid"` + guard NaN antes da integração
3. **STORY bloco_interface (CLI ou Streamlit minimal)** — UI primeiro, integração depois

Recomendação Oracle: **opção 1** — integração end-to-end revela bugs de interação que hardening em isolado não pega; F-LLM-MED-01 + F-VAULT-LOW-01 podem ser endereçados em iteração subsequente sem comprometer entrega.

---

## 8. Linhagem governance

- Antecedente: `qa/qa-gate-story-7-sub-d-personas-llm.md` (PASS sessão 57)
- Handoff de entrada: H-S01-E3.4-neo2qa6
- Handoff de saída: H-S01-E3.4-qa2mor6 (Oracle→Morpheus consolida)
- Sessão checkpoint: 60

---

*Oracle, guardião da qualidade — sete blocos integráveis, uma Phase fechada, uma porta aberta para a integração.*
