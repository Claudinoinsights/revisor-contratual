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
| **TD-WEB-LGPD-CDN-01** | Sessão 86 (2026-05-05) | Story REV-INT-02 | Self-hosted 7 woff2 (Manrope 4w + Fraunces 1w + JetBrains 2w) em /static/fonts/ via @fontsource/jsdelivr (~117KB total); base.html removidos 3 link tags Google Fonts; tokens.css adicionados 7 @font-face declarations (font-display: swap). Validações: AC-1 zero fonts.googleapis ✅, AC-2 zero fonts.gstatic ✅, AC-4 7/7 HTTP 200 ✅, AC-8 232 passed + 1 skipped ✅, AC-9 117536 bytes ≤ 204800 ✅. |
| **TD-LLM-SABIA-Q4-OUTPUT** | Sessão 86 (2026-05-05) | Story REV-LLM-01 (ADR-010 Path C) | LLM_TIER default mudado de 'premium' (Sabia-7B Q4) para 'balanced' (Qwen 2.5 7B). 3 mudanças cirúrgicas em llm_factory.py: TIER_TO_MODEL_ADVOGADO mapping (lean/balanced=Qwen, premium=Sabia preserved); get_advogado_llm default tier='balanced'; get_economista_llm format='json'. Smoke E2E re-run com Qwen 7B+3B PASS em 253.72s (citacao_textual ≥10 chars, ratio<0.7 paralelismo). Suite 232/1 zero regressão. Sabia preservado opt-in para futuro upgrade GPU. |
| **TD-LLM-FORMAT-JSON-ECONOMISTA** | Sessão 86 (2026-05-05) | Story REV-LLM-01 (junto com TD-LLM-SABIA-Q4-OUTPUT) | `format='json'` adicionado em `get_economista_llm` (defensive consistency com get_advogado_llm). |

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

---

## 📦 Sprint 02 — REV-INT-01 (FastAPI+HTMX UI) — sessão 85

> **Origem:** Oracle QA Gate `qa-gate-story-rev-int-01-fastapi-htmx-ui.md` (CONCERNS).
> **Story:** REV-INT-01 — substituição de Streamlit por FastAPI + HTMX + Jinja2.

### HIGH (0)

✅ TD-WEB-LGPD-CDN-01 RESOLVED em sessão 86 (Story REV-INT-02). Ver Resolved Findings abaixo.

### MEDIUM (3)

| ID | Source | Sev | Description | Est. Effort | Owner | Added | Remediation by |
|----|--------|-----|-------------|-------------|-------|-------|----------------|
| **TD-WEB-VAL-MIME-01** | Oracle Probe 3 (F-VAL-01) | MEDIUM | POST /revisar aceita qualquer arquivo (HTML, vazio) como pdf. Sem validação magic bytes (`%PDF-`) ou content-type real. | 1h | @dev | 2026-05-05 | STORY UI-1 (Sprint 02) |
| **TD-WEB-LISTENER-LEAK-01** | Oracle code review (F-LEAK-01) | MEDIUM | processing.html anexa `addEventListener('htmx:sseMessage', ...)` em document.body a cada swap. Após N reset cycles, N listeners disparam paralelamente. | 30min (mover para `htmx:load` once ou usar HTMX native sse-swap) | @dev | 2026-05-05 | STORY UI-1 |
| **TD-WEB-NOMAXSIZE-01** | Oracle code review (F-NFR-01) | MEDIUM | UploadFile sem max_size — operador pode (acidentalmente ou maliciosamente) enviar 10GB consumindo RAM/disco. | 15min (Starlette `MAX_BODY_SIZE` ou middleware) | @dev | 2026-05-05 | STORY UI-1 |

### LOW (4)

| ID | Source | Sev | Description | Est. Effort | Owner | Added | Remediation by |
|----|--------|-----|-------------|-------------|-------|-------|----------------|
| **TD-WEB-SSE-NOSESSION-01** | Oracle Probe 4 (F-SSE-01) | LOW | /pipeline-stream acessível diretamente sem prévio /revisar. Quando pipeline real for conectado, precisa de session/job_id binding. | 1h | @dev | 2026-05-05 | STORY UI-1 |
| **TD-WEB-TIER-ENUM-01** | Oracle Probe 3 (F-VAL-02) | LOW | tier aceita string livre ("DROP_TABLES" passa). Substituir por Pydantic Enum. | 10min | @dev | 2026-05-05 | STORY UI-1 |
| **TD-WEB-RUFF-UP037** | Oracle Probe 6 (F-RUF-01) | LOW | bloco_interface/web/app.py:119 — type hint quoted desnecessariamente. `ruff --fix` resolve. | 1min | @dev | 2026-05-05 | Imediato (ou batch posterior) |
| **TD-WEB-CSP-INLINE-01** | Oracle code review (F-CSP-01) | LOW | processing.html tem `<script>` inline (~30 linhas). Strict CSP (`script-src 'self'`) bloquearia. Mover para arquivo externo se CSP for adotado. | 20min | @dev | 2026-05-05 | Opcional (informacional) |

---

*Sprint 02 REV-INT-01 debts — Oracle (sessão 85, 2026-05-05) · 1 HIGH + 3 MEDIUM + 4 LOW = 8 findings. Gate: CONCERNS.*

---

## 📦 Sprint 02 — DEVOPS-01 (Ollama install + smoke E2E real) — sessão 86

> **Origem:** DEVOPS-01 closure parcial (Operator + Neo, 2026-05-05).
> **Story:** DEVOPS-01 — Ollama install autônomo + smoke pipeline integral.

### Status TD-PIPELINE-SMOKE-REAL: **PARTIALLY RESOLVED**

| Aspecto | Status | Evidência empírica |
|---|---|---|
| Ollama instalado (Windows 11 winget) | ✅ DONE | v0.23.0 |
| Modelos baixados | ✅ DONE | qwen2.5:3b (1.9GB) + sabia-7b-instruct (4.1GB via Modelfile TheBloke GGUF Q4_K_M) |
| 2 instâncias Ollama (paralelismo F-MIN-01) | ✅ DONE | :11434 advogado + :11435 economista, ambos enxergam modelos compartilhados |
| F-MIN-02 (langchain-ollama 1.x ainvoke coroutine) | ✅ CONFIRMED EMPIRICALLY | Smoke iteration 1: 180s; iteration 2: 48s — chamadas async reais |
| Pipeline INTEGRAL roda Sabia + Qwen via langchain-ollama | ✅ CONFIRMED | format=json adicionado em llm_factory.py — Sabia retorna JSON parseável |
| Smoke test PASSED | ❌ NOT YET | Output Sabia 7B Q4 CPU não atinge `min_length=10` em `FundamentoInvocado.citacao_textual` (modelo retorna "..." copiado do prompt template) |

**Conclusão:** TD-PIPELINE-SMOKE-REAL resolvido em 5 de 6 aspectos. Bloqueio único é qualidade do output Sabia (novo debt abaixo). Para atestar empiricamente o pipeline INTEGRAL, é suficiente — paralelismo e integração validados; quality gap é debt separado.

### NEW (1 HIGH + 1 LOW)

| ID | Source | Sev | Description | Est. Effort | Owner | Added | Remediation by |
|----|--------|-----|-------------|-------------|-------|-------|----------------|
| ~~**TD-LLM-SABIA-Q4-OUTPUT**~~ | ~~Smoke DEVOPS-01 sessão 86~~ | ~~HIGH~~ | ✅ **RESOLVED 2026-05-05** Story REV-LLM-01 (Path C ADR-010): LLM_TIER default mudou para 'balanced' (Qwen 2.5 7B); Sabia preservado opt-in via 'premium'. Smoke E2E passa em 253s (citacao_textual ≥10 chars confirmado, ratio<0.7). Ver Resolved Findings abaixo. | — | — | — | — |
| ~~**TD-LLM-FORMAT-JSON-ECONOMISTA**~~ | ~~Smoke DEVOPS-01 sessão 86~~ | ~~LOW~~ | ✅ **RESOLVED 2026-05-05** Story REV-LLM-01: `format="json"` adicionado em `get_economista_llm` (defensive consistency). Ver Resolved Findings abaixo. | — | — | — | — |

### Mudanças aplicadas em produto durante DEVOPS-01

| Arquivo | Mudança | Razão |
|---|---|---|
| `bloco_workflow/personas/llm_factory.py` | `format="json"` em `get_advogado_llm` | Sabia-7B Q4 estava gerando texto natural language; format=json força output JSON estruturado parseável |
| `tests/smoke/test_paralelismo_llm.py` | Fixture `JurisprudenciaItem` ampliado com 6 campos requeridos pelo schema (numero, binding, legal_topic_principal, ano_julgamento, texto_completo, indexed_at) | Schema cresceu em PRD v1.0.2 (Smith F-CRIT-03 vigência) mas test fixture não acompanhou |

### Mudanças em ambiente

- Ollama 0.23.0 instalado em `C:\Users\User\AppData\Local\Programs\Ollama\` via winget
- Modelos baixados em `~/.ollama/models/` (default Windows): ~6GB total
- `models/sabia-7b.Q4_K_M.gguf` (~3.8GB) + `models/Modelfile.sabia-7b-instruct` no repo (gitignored via `.gguf` + `models/` patterns existentes)
- 2ª instância Ollama background em `:11435` (durante smoke; deve ser parada após DEVOPS-01 closure)

---

*Sprint 02 DEVOPS-01 debts — Operator+Neo (sessão 86, 2026-05-05) · TD-PIPELINE-SMOKE-REAL partial RESOLVED + 2 novos debts (1 HIGH + 1 LOW).*
