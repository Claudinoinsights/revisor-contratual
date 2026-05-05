---
type: qa-gate
title: "QA Gate STORY 7 SUB-D — bloco_workflow/personas LLM"
project: revisor-contratual
gate_for: "STORY-7-SUB-D-bloco_workflow-personas-LLM"
date: "2026-05-02"
agent: "@qa (Oracle)"
verdict: PASS
tags:
  - project/revisor-contratual
  - qa-gate
  - story-7-sub-d
  - personas-llm
  - phase-2.B
---

# QA Gate STORY 7 SUB-D — bloco_workflow/personas LLM

> **Linhagem:** Sessão 57 (sucessor de RE-GATE STORY 6 SUB-B PASS sessão 53).
> **Domínio:** software-dev / legaltech.
> **Authority:** QA quality gate formal (advisory PASS / CONCERNS / FAIL / WAIVED).

## Cabeçalho 3 linhas

[@qa · Oracle · Test Architect & Quality Advisor] — quality gate STORY 7 SUB-D bloco_workflow/personas LLM
**VEREDICTO: PASS** (1 MEDIUM observation Pydantic permissivo + 4 LOW tech debt rastreável; 0 CRITICAL/HIGH)
**Recomendação:** APROVADO para STORY 8 (próxima/última sub-fronteira: SUB-C vault sqlite-vec)

---

## 1. Escopo auditado

| Artefato | Linhas | Cobertura testes |
|---|---|---|
| `bloco_workflow/personas/llm_factory.py` | 76 | TestLLMFactoryConfig (3 testes) + probe Oracle 1 |
| `bloco_workflow/personas/advogado.py` | 115 | TestAdvogadoLLM (4 testes) + probe Oracle 2 |
| `bloco_workflow/personas/economista.py` | 95 | TestEconomistaLLM (3 testes) + probe Oracle 6 |
| `bloco_workflow/orchestrator.py` | 75 | TestOrchestradorParalelo (4 testes) + probes Oracle 3+5 |
| `tests/unit/test_personas_llm.py` | 330 | self |
| `tests/smoke/test_paralelismo_llm.py` | atualizado (des-xfail + skipif) | manual via probe 5 Oracle |
| `bloco_workflow/personas/__init__.py` (delta re-exports) | 2 linhas | n/a |
| `bloco_workflow/__init__.py` (delta re-export) | 1 linha | n/a |

**Suite agregada:** 167 passed + 1 skipped (smoke F-MIN-02 sem Ollama no ambiente), 0 failed, runtime 43.92s.
**Delta vs Phase 2.B sessão 53:** 153 → 167 (+14 personas LLM); 1 xfailed → 0 (F-MIN-02 saiu da xfail).

---

## 2. Verificações executadas (D1-D7)

### D1 — F-MIN-02 fix correto + evidência empírica

| Aspecto | Status | Evidência |
|---|---|---|
| langchain-ollama versão | PASS | 1.1.0 instalado (>=0.2.0 ADR-003 PATCH 2 requirement) |
| `ChatOllama.ainvoke` é coroutine | PASS | `inspect.iscoroutinefunction(ChatOllama.ainvoke) = True` (probe Oracle 1.1) |
| `BaseChatModel.ainvoke` (parent) é coroutine | PASS | confirmado herança correta (probe 1.2) |
| `ollama.AsyncClient.chat` (subjacente) é coroutine | PASS | confirmado (probe 1.3) |
| Smoke des-xfail | PASS | `pytest.mark.xfail` removido; agora `skipif` ambiente sem Ollama (semântica correta) |
| Status comentário fala "RESOLVIDO" | PASS | smoke + checkpoint sessão 56 documentam |

**PASS — F-MIN-02 era pendência desde Phase 1; resolvido empiricamente; 3 camadas auditadas.**

### D2 — Anti-fantasma sintático funciona

| Cenário | Resultado | Evidência |
|---|---|---|
| Doc 100% real (STJ-S539 in top-K) | aceito | `test_happy_path_gera_tese_valida` |
| Doc 100% fantasma (STJ-S999 fora top-K) | **rejeitado ValidationError** | `test_anti_fantasma_sintatico_rejeita_doc_fora_top_k` |
| **Mistura real+fantasma (1 OK, 1 inventado)** | **rejeitado ValidationError** | **probe Oracle 2** — STJ-S539 + STF-INVENTADO juntos → CitationFantasma com lista do fantasma exato |

**PASS — anti-fantasma robusto a mistura. Pydantic field_validator em bloco_contratos.TeseAdvogado faz hard-fail.**

### D3 — Paralelismo asyncio.gather REAL (não placebo)

| Probe | Setup | Resultado | Status |
|---|---|---|---|
| Test interno (`test_paralelismo_real_via_asyncio_gather`) | 2x `asyncio.sleep(0.3)` paralelas | latência <0.5s | PASS |
| **Probe Oracle 5** independente | 2x `asyncio.sleep(1.0)` paralelas via `run_personas_paralelas` | **1.007s medido (sequencial seria ~2.0s)** | PASS — overhead asyncio <1% |
| Ratio paralelo/sequencial ideal | — | **0.503** (ideal teórico 0.5) | PASS — paralelismo 99%+ eficiente |

**PASS — paralelismo MEDIDO empiricamente. NÃO é placebo (não roda sequencial debaixo dos panos).**

### D4 — Atomicidade orchestrator (1 falha = tudo levanta)

| Tipo de exceção | Cenário | Propagação | Status |
|---|---|---|---|
| `ValidationError` (Pydantic) | JSON malformado economista | propagada | PASS — `test_atomicidade_falha_propaga` |
| **`asyncio.TimeoutError`** | timeout advogado | **propagada** | PASS probe Oracle 3.1 |
| **`ConnectionError`** | Ollama down (economista) | **propagada** | PASS probe Oracle 3.2 |

**PASS — `asyncio.gather` propaga primeira exceção independente do tipo. Sem retorno parcial.**

### D5 — Configurações arquiteturais (F-MIN-01 + ADR-003 PATCH 2)

| Aspecto | Status | Evidência |
|---|---|---|
| 2 portas distintas obrigatórias | PASS | `DEFAULT_HOST_ADVOGADO` (11434) ≠ `DEFAULT_HOST_ECONOMISTA` (11435); `test_hosts_default_distintos_obrigatorio` |
| Economista FIXO (Qwen 3B) | PASS | `MODEL_ECONOMISTA = "qwen2.5:3b"`; `test_economista_modelo_fixo` |
| Advogado tier-configurável (Sabia) | PASS | 3 tiers mapeados (lean/balanced/premium); `test_advogado_tiers_mapeados` |
| `base_url` EXPLÍCITO (F-MIN-01) | PASS | factory força host como argumento; nunca confia em env default |
| Lazy import langchain_ollama | PASS | `from langchain_ollama import ChatOllama` dentro de função (não top-level) |

**PASS — configuração alinhada ADR-003 PATCH 2 + F-MIN-01.**

### D6 — Prompts incluem dados certos

| Probe | Resultado |
|---|---|
| Prompt advogado contém UF, data ISO, modalidade, docs disponíveis | PASS — `test_prompt_inclui_dados_contrato` |
| Prompt economista contém SGS, mes_ref, taxa_media | PASS — `test_prompt_inclui_dados_bacen` |
| **Probe Oracle 4 — campos opcionais None** | PASS — fallbacks "[NÃO INFORMADO]" / "[NÃO INFORMADA]" / "[nenhum]" funcionam graciosamente |
| **Probe Oracle 4.2 — `is_fallback=True` BACEN visível no prompt** | PASS — Economista vê quando dados são fallback (Oracle observation O-10 STORY 5 SUB-A endereçada parcialmente — Economista pode ALERTAR sobre fallback) |

**PASS — prompts robustos a campos faltantes.**

### D7 — Pecados Capitais (Ordem 10) — verificação

| Pecado | Status |
|---|---|
| Inventar dado/métrica não-mensurada | OK — paralelismo MEDIDO (1.007s real); F-MIN-02 verificado empiricamente; sem afirmação de latência sem prova |
| Float em wire format monetário | OK — taxas/valores são string Decimal-safe (delegado para bloco_contratos.BacenData/ContratoMetadata) |
| Silenciar erro | OK — atomicidade orchestrator propaga; ParserOCRRequired não-silent (legacy STORY 6); ValidationError hard-fail |
| Authority alheia | OK — Neo escreveu código; Oracle não escreve código |
| Cabeçalho ausente | OK — este documento tem cabeçalho 3 linhas |

**PASS — 0 violações.**

---

## 3. Findings

### CRITICAL — 0
### HIGH — 0

### MEDIUM (1 — observação importante mas NÃO bloqueia)

- **F-LLM-MED-01** — Pydantic permissivo aceita campos extras LLM-hallucinated silenciosamente
  - **Probe Oracle 6.1:** `AnaliseMacroEconomica.model_validate_json(...)` com JSON contendo `"campo_extra_inventado": "hallucination"` E `"recomendacao_acao": "abrir processo"` → **PASSOU validação**, campos extras IGNORADOS sem warning.
  - **Comportamento Pydantic v2 default:** `extra="ignore"`. Schema só valida o que conhece.
  - **Risco:** se LLM hallucinar uma "recomendacao_acao" ou "alerta_compliance" extra, será silenciosamente descartado — perde-se sinal de comportamento anômalo.
  - **No DOMÍNIO JURÍDICO:** anti-fantasma (sintático) protege contra citação inventada, mas NÃO protege contra "raciocínio extra" que LLM tenta exportar via campos não-modelados.
  - **Recomendação:** considerar `model_config = ConfigDict(extra="forbid")` em TeseAdvogado e AnaliseMacroEconomica. Quando LLM enviar campo extra → ValidationError → log + retry com prompt mais estrito. Decisão Eric/Morpheus arquitetural — pode ser STORY de hardening pós-MVP.

### LOW (4 — tech debt rastreável NÃO bloqueia)

- **TD-LLM-01 LOW** — `_default_invoke` em advogado.py + economista.py não testados (lazy paths)
  - Justificativa: precisam Ollama real; CI sem Ollama; smoke F-MIN-02 cobre quando ambiente pronto.
  - Recomendação: rodar smoke após Eric baixar modelos pela primeira vez; documentar evidência da execução real no checkpoint.

- **TD-LLM-02 LOW** — Prompts são strings hardcoded em `advogado.py` e `economista.py`
  - Recomendação: STORY de prompt-engineering futura → mover para Jinja2 templates versionados em `bloco_workflow/personas/prompts/`. Permite A/B testing de prompts sem deploy.

- **TD-LLM-03 LOW** — Modelo Sabia tier "lean" assume `sabia-3b` mas nome exato pode variar
  - Recomendação: verificar com `ollama list` no deploy real. Se modelo não existir com esse nome, atualizar `TIER_TO_MODEL_ADVOGADO` em llm_factory.py.

- **TD-LLM-04 LOW** — Pydantic coerção bool: string `"true"` (probe 6.2) vira `True` automaticamente
  - Comportamento esperado mas worth knowing: LLM que escreve `"taxa_atipica_bool": "true"` (string) em vez de `true` (bool) NÃO falhará. Se quiser strict, `Field(...)` com `strict=True`.

---

## 4. Métricas

| Métrica | Valor |
|---|---|
| Testes personas LLM | 14 |
| Testes suite agregada | 167 + 1 skipped (smoke) = 168 |
| Falhas | 0 |
| Runtime suite agregada | 43.92s |
| Linhas código produção (parsing) | 361 (4 módulos) |
| Linhas código teste (test_personas_llm) | 330 (0.91× ratio teste:produção — saudável) |
| Cobertura cenários distintos | 14 testes Neo + 6 probes Oracle adversariais |
| Probes Oracle adversariais executadas | 6 (F-MIN-02, anti-fantasma mistura, atomicidade Timeout+Connection, edge None, paralelismo 1s, Pydantic permissivo) |
| Probes Oracle PASS | 6/6 |
| FR cobertos | 3/3 (FR-TESE-01 anti-fantasma + FR-TESE-02 tier + FR-PERSONA-ECO-01 economista) |
| F-MIN-02 status | **RESOLVIDO** (era pendência desde Phase 1) |
| Findings CRITICAL/HIGH | 0 |
| Findings MEDIUM | 1 (Pydantic permissivo extra fields) |
| Findings LOW | 4 |

---

## 5. Status findings anteriores (rastreabilidade cross-stories)

| Finding | Status atual |
|---|---|
| F-PARSE-HIGH-01 (STORY 6 SUB-B) | **RESOLVED** sessão 53 |
| O-08 LOW (BACEN — RetryError dead path) | DEFERRED |
| O-09 LOW (BACEN — fonte_url sem field_validator host) | DEFERRED |
| O-10 LOW (BACEN — fallback mes_ref divergente) | **PARCIALMENTE ENDEREÇADA** — Economista agora vê `is_fallback=True` no prompt (probe Oracle 4.2); pode alertar |
| O-11 LOW (PARSE — Marker default não testado) | DEFERRED |
| O-12 LOW (PARSE — PyMuPDF default não testado) | DEFERRED |
| O-13 LOW (PARSE — valor sem centavos) | DEFERRED |
| F-MIN-02 (ADR-003 PATCH 2 — async real) | **RESOLVED** sessão 56 |

---

## 6. Recomendação ao Morpheus

**APROVADO para STORY 8.**

### Próxima sub-fronteira (única remanescente)
- **SUB-C vault** — sqlite-vec v0.1 + scrapers HTML jurisprudência (ADR-007)
- Risco: sqlite-vec v0.1 ainda jovem; DP-08 load test pendente desde Phase 1
- Após SUB-C: 7/7 blocos prontos → STORY 9 = **integração end-to-end** (PDF → parsing → cálculo Decimal → BACEN → personas LLM paralelas → juiz → audit → peça final)

### Decisão estratégica para Eric
1. **Avançar SUB-C agora** — completa todos os 7 blocos antes da integração
2. **Pular SUB-C, ir direto para STORY 9 integração** — usar mocks de vault até stabilizar sqlite-vec
3. **Hardening primeiro** — endereçar F-LLM-MED-01 (Pydantic strict) + tech debts antes de adicionar complexidade

Recomendação Oracle: **opção 1** (SUB-C) — mantém doutrina Phase 2.B "camada por camada"; F-LLM-MED-01 é observation arquitetural que pode ser endereçada em STORY de hardening pós-integração.

---

## 7. Linhagem governance

- Antecedente: `qa/qa-gate-story-6-sub-b-parsing.md` (RE-GATE PASS sessão 53)
- Handoff de entrada: H-S01-E3.3-neo2qa5
- Handoff de saída: H-S01-E3.3-qa2mor5 (Oracle→Morpheus consolida)
- Sessão checkpoint: 57

---

*Oracle, guardião da qualidade — paralelismo medido, alucinação contida, atomicidade preservada.*
