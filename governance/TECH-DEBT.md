---
type: dashboard
title: "Tech Debt Registry — Revisor Contratual"
last_updated: "2026-05-05"
project: revisor-contratual
sprint: "01 (closure)"
tags:
  - project/revisor-contratual
  - tech-debt
  - sprint-01-closure
---

# Tech Debt Registry — Revisor Contratual

> **Sprint 01 closure consolidation** — STORY 15 (sessão 81, Neo).
> Consolidação de 13 tech debts catalogados em 4+ QA gates Oracle (sessões 60-77) + 1 finding ativo + 5 findings RESOLVED.
> Formato: 7 campos obrigatórios (ID, Source, Sev, Description, Est. Effort, Owner, Added).

---

## 📊 Resumo executivo

| Categoria | Quantidade |
|---|---|
| Active tech debts | **13** (2 MEDIUM + 11 LOW) |
| Active findings | **1** (F-CI-LOW-01 LOW) |
| Resolved findings | **5** (Phase 3-4) |
| Sprint origem | 01 (Phase 2.B até Phase 5) |

---

## 🔧 Active Tech Debts (13)

### MEDIUM (2)

| ID | Source | Sev | Description | Est. Effort | Owner | Added |
|----|--------|-----|-------------|-------------|-------|-------|
| **TD-PIPELINE-SMOKE-REAL** | STORY 9 + STORY 13 | MEDIUM | Smoke E2E real (Ollama + Sabia-7B + Qwen 3B + httpx STJ/STF + PDF físico) nunca executado — todos os testes usam mocks injetados. Validação INTEGRAL pipeline ainda não comprovada empiricamente. | 4h + 30min setup + ~7GB download | @dev | 2026-05-02 |
| **TD-VAULT-LOAD-TEST** | STORY 8 | MEDIUM | DP-08 — performance vault sqlite-vec não testada com 10k+ rows. RRF k=60 + busca híbrida pode degradar; SLA <500ms desconhecido em escala. | 2h | @dev | 2026-05-02 |

### LOW (11)

| ID | Source | Sev | Description | Est. Effort | Owner | Added |
|----|--------|-----|-------------|-------------|-------|-------|
| **TD-CI-COVERAGE-REPORTER** | STORY 12 | LOW | NFR-MAINT-02 cobertura é local-only (`pytest-cov` sem reporter externo). Adicionar Codecov ou Coveralls quando integração disponível. | 2h | @devops | 2026-05-02 |
| **TD-CI-PYTHON-3.13** | STORY 12 | LOW | Matrix CI fixa em Python 3.11 + 3.12. Adicionar 3.13 quando wheels `langchain-ollama` + `sentence-transformers` estabilizarem. | 30min | @devops | 2026-05-02 |
| **TD-CI-CACHE-PIP** | STORY 12 | LOW | `cache: 'pip'` configurado em `setup-python@v5`; verificar hit rate empírico após N runs. | 1h | @devops | 2026-05-02 |
| **TD-VAULT-TJ** | STORY 8 | LOW | Scrapers TJBA/TJSP/TJMG/TJRJ/TJRS não implementados. Whitelist NFR-LGPD-01 atual = STJ + STF apenas; expandir requer ADR formal por TJ. | 8h+ por TJ | @dev | 2026-05-02 |
| **TD-VAULT-LEGAL-BERTIMBAU** | STORY 8 | LOW | Modelo `neuralmind/bert-base-portuguese-cased` (~500MB) NÃO baixado por default. Usuário precisa instalar `sentence-transformers` opt-in para busca semântica completa. | 1h | @dev | 2026-05-02 |
| **TD-VAULT-TOPIC-INDETERMINADO** | STORY 8 | LOW | Filtro `legal_topic_principal` aceita qualquer string sem validação contra ontologia jurídica formal. Pode permitir typos/variações que comprometem busca. | 2h | @dev | 2026-05-02 |
| **TD-PIPELINE-QUERY-BUILDER** | STORY 9 | LOW | Query do vault construída via heurística MVP (`modalidade + classificacao + sumulas_aplicaveis`). Query-builder dedicado pós-MVP melhora precision/recall. | 4h | @dev | 2026-05-02 |
| **TD-PIPELINE-PACTUACAO** | STORY 9 | LOW | Default `instituicao_sfn=True + pactuacao_expressa=True` MVP. Inferir de markdown via parsing semântico futuro reduziria false positives em CDC não-bancário. | 3h | @dev | 2026-05-02 |
| **TD-CLI-RICH-OPTIONAL** | STORY 10 | LOW | `rich` é opcional + fallback ASCII (defensivo intencional). Documentado em SOP-002/003. Pode permanecer indefinidamente se nunca quebrar. | n/a | — | 2026-05-02 |
| **TD-CLI-EMBEDDINGS-DEFAULT-ZERO** | STORY 10 | LOW | `populate-vault` default `--zero-embeddings=True` (MVP). Busca semântica precisa de embeddings reais para funcionar; usuário precisa explicit opt-in. | 1h | @dev | 2026-05-02 |
| **TD-CLI-PROGRESS-BAR** | STORY 10 | LOW | Sem progress bar no pipeline real (`revisar` subcomando). Adicionar `rich.progress` quando smoke E2E real for executado. | 1h | @dev | 2026-05-02 |

---

## 🟡 Active Findings (1)

| ID | Source | Sev | Description | Status |
|----|--------|-----|-------------|--------|
| **F-CI-LOW-01** | STORY 12 (sessão 71) | LOW | Path-filter pode falhar em commits cross-cutting (ex: refactor compartilhado em `packages/shared/`). Hoje revisor-contratual é isolado no monorepo — risco hipotético. | DEFERRED |

---

## ✅ Resolved Findings (5)

| ID | Resolved | Story | Resolution |
|----|----------|-------|------------|
| **F-PARSE-HIGH-01** | STORY 6 (sessão 51) | STORY 6 | Fix em `_extract_modalidade` — parênteses obrigatórios para precedência Python (`A and B or C` → `A and (B or C)`) |
| **F-MIN-02** | Antes STORY 12 | STORY 12 | Smoke `tests/smoke/test_paralelismo_llm.py` skip intencional sem Ollama (esperado em CI sem ambiente) |
| **F-LLM-MED-01** | STORY 13 (sessão 73) | STORY 13 | `model_config = ConfigDict(extra='forbid')` aplicado aos 5 schemas LLM-facing (`FundamentoInvocado`, `TeseAdvogado`, `AnaliseMacroEconomica`, `VeredictoJuiz`, `ValidacaoSemantica`) |
| **F-VAULT-LOW-01** | STORY 13 (sessão 73) | STORY 13 | Guard `math.isnan/isinf` fail-fast antes de `struct.pack` em `serialize_embedding` |
| **F-PIPELINE-LOW-01** | STORY 13 (sessão 73) | STORY 13 | Mensagem `ParserOCRRequired` reescrita PT-BR estruturada (diagnóstico → causa → solução → alternativa); reproduzida exatamente em SOP-003 caso 2 |

---

## 🚦 Action Items por Sprint

### Sprint 02 — top-priority (quando iniciar)

- [ ] **Top-1: TD-PIPELINE-SMOKE-REAL** — validar pipeline INTEGRAL com Ollama real. Pré-requisito: Eric instala Ollama (~30min) + baixa Sabia-7B (~5GB) + Qwen 3B (~2GB). **Bloqueador para confiança em produção.**
- [ ] **Top-2: TD-VAULT-LOAD-TEST** — DP-08 perf 10k+ rows. Gerar dataset sintético STJ + STF expandido (~10k súmulas/SVs) e medir latência RRF.
- [ ] **Top-3: TD-CI-COVERAGE-REPORTER** — adicionar Codecov ou Coveralls. Visibility de cobertura externa sustenta NFR-MAINT-02.
- [ ] **Top-4: F-CI-LOW-01** — revisar quando primeira dep cross-package surgir no monorepo.

### Sprint 03+ (priorizar conforme uso real)

- [ ] **TD-VAULT-TJ** — scrapers TJ adicionais (TJBA priority — mercado-alvo MVP). Cada novo TJ exige ADR formal para expansão de whitelist NFR-LGPD-01.
- [ ] **TD-PIPELINE-QUERY-BUILDER** — query-builder dedicado pós-MVP (melhora precision/recall vault).
- [ ] **TD-PIPELINE-PACTUACAO** — inferir `pactuacao_expressa` de markdown via parsing semântico.
- [ ] **TD-VAULT-LEGAL-BERTIMBAU** — verificar se default zero-embeddings continua suficiente para usuários reais.
- [ ] **TD-VAULT-TOPIC-INDETERMINADO** — ontologia jurídica formal para `legal_topic_principal`.
- [ ] **TD-CLI-PROGRESS-BAR** — adicionar `rich.progress` no pipeline real.
- [ ] **TD-CLI-EMBEDDINGS-DEFAULT-ZERO** — flip default quando `sentence-transformers` for instalado por padrão.
- [ ] **TD-CI-PYTHON-3.13** — adicionar à matrix quando wheels estabilizarem.
- [ ] **TD-CI-CACHE-PIP** — verificar hit rate empírico.
- [ ] **TD-CLI-RICH-OPTIONAL** — manter como está (defensivo intencional).

---

## 🔄 Retrospective — Sprint 01 (14 stories Done, 14/14 PASS Oracle)

### O que funcionou ✅

- **Workflow LMAS estrito** — Morpheus orquestra; agentes executam dentro de Authority. Entregou 14 stories sem retrabalho ou ambiguidade.
- **Adversarial Oracle review** — probes Python ao vivo + cross-reference com código capturaram 0 regressões. STORY 14 cross-story consistency (4/4 frases-chave sincronizadas SOP↔código) é exemplo paradigmático.
- **Decisões Morpheus com Why explícito** — 60+ decisões D-MOR-X.0.x facilitaram QA gates Oracle e justificaram escolhas em Tech Debt registry.
- **Pre-flight check empírico em operações shared-state** — descoberta na sessão 78 (PR #1 desatualizado) preveniu merger MVP incompleto.
- **Hardening defensivo (Phase 4 #1) + Docs operacionais (Phase 4 #2)** — endereçou 3 findings LOW DEFERRED com 9 testes adversariais reais + cataloga uso real para advogados não-dev.

### O que não funcionou ⚠️

- **Pre-flight check de PR descoberto tardiamente** — sessão 78 descobriu commits Phase 4 não pushed; ideal seria check automático em workflow.
- **TECH-DEBT.md ficou para o final** (STORY 15) em vez de incremental por story — debts ficaram esparsos em 4+ QA gates Oracle. Consolidar agora exigiu re-leitura de 14 docs QA.
- **Lacuna runtime real** — Eric nunca rodou pipeline com Ollama real; toda confiança vem de mocks injetados + adversarial probes. Smoke real (TD-PIPELINE-SMOKE-REAL) é gap estrutural.
- **Versionamento release vs main desalinhado** — release v0.1.0-revisor-contratual aponta para `e00183c4` (pré-Phase-4); main HEAD é `b5c57be3` (com Phase 4). Releases futuras (v0.2.0) precisarão alinhar.

### Lessons Learned 📖

1. **Pre-flight checks ANTES de qualquer ação shared-state** (merge, push remote, deploy) são essenciais. Adicionar como passo obrigatório em template de stories git remote.
2. **TECH-DEBT.md DEVE ser atualizado por story** (não no final do sprint) — alinhar com `tech-debt-governance.md`. Sprint 02 começará com este princípio.
3. **Cross-story consistency** (STORY 13 hardening + STORY 14 docs) é padrão a replicar — quando um fix muda mensagem visível ao usuário, docs DEVEM reproduzir exatamente.
4. **Adversarial probes Python ao vivo** valem mais que probes textuais — Probe 4 STORY 14 (verificação Python ao vivo de mensagem ParserOCRRequired) detectou 6/6 aspectos com 100% de precisão.
5. **Squash merge + tag release histórica** é estratégia limpa: main fica curto e legível; tag preserva snapshot para auditoria; PR no GitHub preserva discussão de revisão.

### Action Items para Sprint 02 📌

- [ ] **Atualizar TECH-DEBT.md a cada story Done** (não acumular para closure) — alinhar com `tech-debt-governance.md`
- [ ] **Adicionar pre-flight check obrigatório** no template de stories que envolvem operações git remote (push, merge)
- [ ] **Setup Ollama documentado** como pré-requisito de Sprint 02 (ou criar STORY dedicada de setup automação)
- [ ] **Re-tag v0.2.0** quando Sprint 02 entregar mais features (alinhar tag com main HEAD pós-Phase-4)
- [ ] **TODO Operator para Sprint 02:** `git push origin --delete feature/revisor-contratual-v0.1.0` (cleanup remote — Neo não tem authority)

---

## 🔗 Referências

- **PRD canônico:** [`prd/prd-v1.0.2.md`](./prd/prd-v1.0.2.md)
- **ADR Index (9 ADRs):** [`architecture/ADR-INDEX.md`](./architecture/ADR-INDEX.md)
- **QA Gates Oracle (14 docs):** [`qa/`](./qa/)
- **Estado vivo:** [`CHECKPOINT-active.md`](./CHECKPOINT-active.md)

---

*Sprint 01 closure registry — Neo (sessão 81, 2026-05-05) · 13 active debts + 1 finding ativo + 5 RESOLVED. MVP v0.1.0 oficial em main `b5c57be3`.*
