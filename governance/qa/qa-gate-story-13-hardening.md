---
type: qa-gate
title: "QA Gate STORY 13 — Hardening 3 LOWs DEFERRED"
project: revisor-contratual
story_id: STORY-13-hardening-3-lows
sprint: "01"
phase: "4"
reviewer: "@qa (Oracle)"
session: 74
date: "2026-05-04"
verdict: PASS
tags:
  - project/revisor-contratual
  - qa-gate
  - story-13
  - hardening
  - sprint-01
  - phase-4
---

# QA Gate STORY 13 — Hardening 3 LOWs DEFERRED

> **Reviewer:** Oracle (Guardian) | **Sessão:** 74 | **Data:** 2026-05-04
> **Branch:** `feature/revisor-contratual-v0.1.0` | **PR:** [#1 OPEN mergeable](https://github.com/Claudinoinsights/the-matrix/pull/1)
> **Commit sob revisão:** `3365ccd8` (apenas STORY 13 — 3 produção + 3 testes; +155/-4)

---

## 🎯 Veredito final

**PASS** — não CONCERNS, não FAIL, não WAIVED.

STORY 13 entrega exatamente o escopo cristalizado por Morpheus em D-MOR-13.x sem renegociar nenhuma decisão arquitetural. Os 3 fixes são localizados, defensivos e testados com cenários adversariais reais (não smoke). A defesa em profundidade do sistema foi reforçada em três frentes: (1) boundary LLM↔sistema com `extra='forbid'` rejeitando alucinações; (2) embedder com guard explícito contra NaN/Inf que o sqlite-vec aceitaria silenciosamente; (3) UX do `ParserOCRRequired` com mensagem PT-BR estruturada (diagnóstico → causa → solução → alternativa).

**Métricas Phase 4 #1 consolidadas:**
- Suite: 224 → 233 collected (+9 tests, exatamente o range Morpheus 6-9)
- Resultado local: 232 passed + 1 skipped + 0 failed em 62.01s (-1% vs baseline STORY 12 = 63.08s)
- 0 testes anteriores quebrados | 0 regressões
- 0 findings CRITICAL/HIGH/MEDIUM novos
- 0 findings LOW novos
- Probes Oracle adversariais: **5/5 PASS** (incluindo verificação semântica Python ao vivo)

---

## ✅ Decisões D1-D8

| # | Critério | Status | Evidência |
|---|---|---|---|
| **D1** | Pydantic strict bloqueia REALMENTE (sem fallback silencioso) | ✅ PASS | Verificação Python ao vivo: `TeseAdvogado(...campo_alucinado='nope')` levanta com `extra`/`forbidden` na mensagem |
| **D2** | Cross-cutting — schemas domain interno NÃO afetados | ✅ PASS | `grep -c "model_config\|ConfigDict"` retorna **0** em `bloco_contratos/contrato.py` e `jurisprudencia.py`. Verificação ao vivo: `ContratoMetadata(...campo_inventado='x')` aceita silenciosamente (default Pydantic `extra='ignore'`); `hasattr(m, 'campo_inventado')` é `False` (campo descartado). D-MOR-13.0-B respeitada |
| **D3** | NaN/Inf guard fail-fast (não silencia bug) | ✅ PASS | Verificação Python: `serialize_embedding([nan]*768)` levanta `ValueError` com mensagem "Embedding contém NaN ou Inf — invalido para indexação" |
| **D4** | Ordem dos checks em `serialize_embedding` (dim mismatch antes de NaN/Inf) | ✅ PASS | Verificação ao vivo: `serialize_embedding([nan]*100)` levanta **dim mismatch** primeiro (não NaN). Lógica preserva mensagem prioritária |
| **D5** | UX ParserOCRRequired compreensível para usuário não-dev | ✅ PASS | Mensagem 6/6 aspectos: nome PDF, diagnóstico, causa, solução acionável, alternativa, vocabulário PT-BR. Estrutura semântica em 4 partes (❌ Diagnóstico → 🔍 Causa → ✅ Solução → 💡 Alternativa) |
| **D6** | Regression integração — pipeline E2E + personas_llm intactos | ✅ PASS | `pytest tests/integration/test_pipeline_e2e.py tests/unit/test_personas_llm.py` → **24/24 PASS** em 16.19s |
| **D7** | Test quality — cenários adversariais reais, não smoke | ✅ PASS | Cada teste de rejeição usa payload **válido** + UM campo extra **com nome semanticamente plausível** ("hallucinated_field", "campo_alucinado", "previsao_futura", "score_misterioso", "extra_metadata") simulando alucinação LLM real |
| **D8** | 0 Pecados Capitais (No Invention + AC-traceability) | ✅ PASS | Diff cirúrgico: +155/-4 em 6 arquivos exatos. Cada fix rastreável a finding (F-LLM-MED-01, F-VAULT-LOW-01, F-PIPELINE-LOW-01). Nenhuma feature inventada |

---

## 🔬 Probes Oracle adversariais (5/5 PASS)

### Probe 1 — Cross-cutting check (D-MOR-13.0-B respeitada)

**Hipótese:** `extra='forbid'` poderia ter "vazado" para schemas domain interno por descuido.

**Verificação:**
```bash
grep -c "model_config\|ConfigDict" bloco_contratos/contrato.py bloco_contratos/jurisprudencia.py
# contrato.py: 0
# jurisprudencia.py: 0
```

**Verificação semântica Python ao vivo:**
```python
m = ContratoMetadata(contract_hash='a'*64, uf_contrato='BA', data_assinatura=date(2024,3,15), campo_inventado='deveria_ser_ignorado')
# → aceita silenciosamente (default Pydantic v2 = 'ignore')
# → hasattr(m, 'campo_inventado') == False (campo descartado)
```

**Resultado:** ✅ **PASS** — escopo isolado nos 5 LLM-facing exatamente como Morpheus decidiu.

---

### Probe 2 — Pipeline E2E real

**Hipótese:** Schemas hardenados poderiam quebrar pipeline integração se algum ponto serializa/desserializa com campos extras legítimos.

**Verificação empírica:**
```bash
pytest tests/integration/test_pipeline_e2e.py tests/unit/test_personas_llm.py -o addopts=""
# 24 passed in 16.19s
```

**Resultado:** ✅ **PASS** — pipeline integral + personas LLM operacionais sem ajuste. Hardening defensivo, não disruptivo.

---

### Probe 3 — Boundary order em serialize_embedding (6 sub-cenários)

**Hipótese:** Ordem incorreta dos checks (NaN antes de dim) confundiria diagnóstico em produção.

| Sub-probe | Input | Output esperado | Resultado |
|---|---|---|---|
| 3.1 | `[nan]*768` | `ValueError("NaN ou Inf")` | ✅ PASS |
| 3.2 | `[nan]*100` (dim ERRADO + NaN) | `ValueError("dim mismatch")` (PRIMEIRO) | ✅ PASS |
| 3.3 | `[inf] + [0]*767` | `ValueError("NaN ou Inf")` | ✅ PASS |
| 3.4 | `[-inf] + [0]*767` | `ValueError("NaN ou Inf")` | ✅ PASS |
| 3.5 | `[0]*400 + [nan] + [0]*367` (NaN no MEIO) | `ValueError("NaN ou Inf")` | ✅ PASS |
| 3.6 | `[]` (lista vazia) | `ValueError("dim mismatch")` | ✅ PASS |

**Resultado:** ✅ **PASS** 6/6 — ordem semanticamente correta (`dim_mismatch` é problema "estrutural" mais grave que NaN; faz sentido reportar primeiro). NaN detectado em qualquer posição, com qualquer sinal (+inf, -inf, nan).

---

### Probe 4 — Mensagem ParserOCRRequired completa

**Hipótese:** Mensagem poderia ter perdido aspectos durante reescrita PT-BR.

**Verificação 6 aspectos:**
| Aspecto | Conteúdo esperado | Resultado |
|---|---|---|
| Nome do PDF | `pdf_path.name` interpolado | ✅ PASS |
| Diagnóstico | "Diagnóstico:" + descrição | ✅ PASS |
| Causa | menção PyMuPDF + insuficiente | ✅ PASS |
| Solução acionável | `pip install revisor-contratual[ocr]` | ✅ PASS |
| Alternativa | "converta para PDF" + "Word" | ✅ PASS |
| Vocabulário PT-BR | "imagem"/"escaneada" | ✅ PASS |

**Resultado:** ✅ **PASS** 6/6 — mensagem completa, estruturada, acionável.

---

### Probe 5 — Regression personas_llm

**Hipótese:** `extra='forbid'` em FundamentoInvocado/TeseAdvogado/AnaliseMacroEconomica poderia quebrar fixtures de teste do pacote LLM client.

**Verificação:**
```bash
pytest tests/unit/test_personas_llm.py
# 14 passed
```

**Resultado:** ✅ **PASS** — 14/14 testes existentes do pacote `bloco_workflow/personas` continuam verdes. Fixtures pré-existentes já forneciam apenas campos válidos.

---

## 🟡 Findings novos

**0 findings CRITICAL/HIGH/MEDIUM/LOW novos.**

STORY 13 é exclusivamente defensiva — fecha findings catalogados sem introduzir novos.

---

## 🔁 Findings cross-stories (status atualizado)

| ID | Status anterior | Status atual | Notas |
|---|---|---|---|
| F-LLM-MED-01 (Pydantic permissivo) | DEFERRED | ✅ **RESOLVED** | Pydantic strict aplicado aos 5 schemas LLM-facing |
| F-VAULT-LOW-01 (NaN guard) | DEFERRED | ✅ **RESOLVED** | Guard `math.isnan/isinf` fail-fast em `serialize_embedding` |
| F-PIPELINE-LOW-01 (ParserOCRRequired UX) | DEFERRED | ✅ **RESOLVED** | Mensagem PT-BR estruturada com solução acionável + alternativa |
| F-PARSE-HIGH-01 | RESOLVED (sessão 51) | RESOLVED | — |
| F-MIN-02 | RESOLVED | RESOLVED | — |
| F-CI-LOW-01 (path-filter cross-cutting) | DEFERRED | DEFERRED | Sem mudança — escopo STORY 13 não toca CI |

**Findings ativos restantes:** apenas **F-CI-LOW-01** (LOW, hipotético até primeira dep cross-package surgir).

---

## 📋 Tech debts STORY 13 DEFERRED

**0 tech debts novos.**

Tech debts pré-existentes (Phase 3) inalterados:
- TD-CI-COVERAGE-REPORTER LOW (independente de STORY 13)
- TD-CI-PYTHON-3.13 LOW (independente)
- TD-CI-CACHE-PIP LOW (independente)
- TD-VAULT-LOAD-TEST MEDIUM, TD-VAULT-TJ LOW, TD-VAULT-LEGAL-BERTIMBAU LOW, TD-VAULT-TOPIC-INDETERMINADO LOW (vault perf — independente)
- TD-PIPELINE-QUERY-BUILDER, TD-PIPELINE-PACTUACAO, TD-PIPELINE-SMOKE-REAL (pipeline — independente)
- TD-CLI-RICH-OPTIONAL, TD-CLI-EMBEDDINGS-DEFAULT-ZERO, TD-CLI-PROGRESS-BAR (CLI — independente)

---

## 🎯 Recomendação STORY 14/15 — Oracle ranking

Com STORY 13 PASS, todos os 3 findings LOW DEFERRED da Phase 3 estão **RESOLVED**. Próximas opções (Morpheus consolidará):

### #1 — **STORY 14 — Docs README + SOPs operacionais** (RECOMENDADO Oracle)

**Razão:** Aumenta adoção/usabilidade do MVP entregue sem tocar código testado. Docs operacionais são pré-requisito para usuários não-dev experimentarem o produto.

**Escopo:**
- `packages/revisor-contratual/README.md` — quickstart 5 minutos (instalação, comandos, exemplo)
- `docs/sop-rotacao-auth-cookie-key.md` — referenciado por `genesis.py:123` mas ainda não existe (gap Smith identificável)
- `docs/sop-populate-vault.md` — comando + flags + LGPD whitelist
- `docs/sop-revisar-pdf.md` — fluxo end-to-end usuário final + casos de erro comuns

**Estimativa:** 1-2h | Risco: BAIXO (docs não tocam código) | Owner: @pm + @dev

---

### #2 — **STORY 15 — Smoke E2E real** (Ollama + modelos + httpx STJ/STF + PDF físico)

**Razão:** Valida pipeline INTEGRAL contra dependências reais. Descobriria regressões de ambiente/versão de modelos.

**Risco:** ALTO. Smoke real depende de:
- Ollama instalado + serving
- Sabia-7B + Qwen-3B baixados (~7GB)
- STJ/STF acessíveis na rede
- PDF físico de teste com camada de texto

Pode introduzir flakiness se não cuidadosamente sandboxed.

**Estimativa:** 3-5h | Owner: @devops + @dev

---

### **Recomendação Oracle final:** **#1 STORY 14 Docs primeiro**, depois #2 STORY 15 Smoke real quando ambiente Ollama disponível.

**Justificativa:** Docs aumenta valor entregue sem custo (zero risco scope creep) e cobre gap Smith de SOPs ausentes. Smoke real é o passo natural depois — ambiente pré-configurado pelos SOPs.

---

## 🔗 Handoff emitido

**ID:** H-S01-E8.0-qa2mor11
**De:** @qa (Oracle, sessão 74)
**Para:** @lmas-master (Morpheus)
**Path:** `.lmas/handoffs/handoff-qa-to-morpheus-2026-05-04-revisor-contratual-story-13-pass.yaml`
**Próxima ação Morpheus:** consolidar fechamento Phase 4 #1 STORY 13 + apresentar 2 opções a Eric (Oracle ranking acima).

---

*"Há uma diferença entre conhecer o caminho e trilhar o caminho." — Neo trilhou três caminhos com precisão; eu validei cada um, e todos levam ao mesmo destino: defesa fortalecida sem regressão. — Oracle, guardião da qualidade 🛡️*
