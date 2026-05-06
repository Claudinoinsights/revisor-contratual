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
| Active tech debts | **30** (3 MEDIUM + 12 LOW + 15 BL-* — 14 migrados v1.1.1 + 1 NOVO v1.1.2) |
| Active findings | **1** (F-CI-LOW-01 LOW) |
| Resolved findings | **9** (5 Phase 3-4 + 3 sessão 86 + 1 VAULT-FIX-01 sessão 87) |
| Sprint origem | 01 (Phase 2.B até Phase 5) + 02 (REV-INT-01..02 + REV-LLM-01) + 03 Phase 0 (VAULT-FIX-01) + 03 course-correction (PRD v1.1.0 → v1.1.1 BL-* migration) |

---

## 🔧 Active Tech Debts (13)

### MEDIUM (3)

| ID | Source | Sev | Description | Est. Effort | Owner | Added |
|----|--------|-----|-------------|-------------|-------|-------|
| **TD-PIPELINE-SMOKE-REAL** | STORY 9 + STORY 13 | MEDIUM | Smoke E2E real (Ollama + Sabia-7B + Qwen 3B + httpx STJ/STF + PDF físico) nunca executado — todos os testes usam mocks injetados. Validação INTEGRAL pipeline ainda não comprovada empiricamente. | 4h + 30min setup + ~7GB download | @dev | 2026-05-02 |
| **TD-VAULT-LOAD-TEST** | STORY 8 | MEDIUM | DP-08 — performance vault sqlite-vec não testada com 10k+ rows. RRF k=60 + busca híbrida pode degradar; SLA <500ms desconhecido em escala. | 2h | @dev | 2026-05-02 |
| **TD-VAULT-SCRAPER-OUTPUT-TO-BUNDLED-ADAPTER** | VAULT-FIX-01 (Phase D) | MEDIUM | `refresh-vault` valida disponibilidade upstream mas NÃO sobrescreve bundled JSON — scrapers retornam `JurisprudenciaItem` (rich schema) enquanto bundled segue `SumulaSTJ`/`SumulaVinculanteSTF` (lean schema). Adapter scraper→bundled permitiria refresh-vault auto-update. | 3h | @dev | 2026-05-05 |

### LOW (12)

| ID | Source | Sev | Description | Est. Effort | Owner | Added |
|----|--------|-----|-------------|-------------|-------|-------|
| **TD-VAULT-DATASET-STALENESS-MITIGATION** | VAULT-FIX-01 (Phase B+E) | LOW | Bundled dataset PROVISIONAL: 5 STJ + 5 STF SV (~1.6% STJ + ~8.6% STF SV oficial). Maintainer DEVE rodar one-shot bulk import pre-produção via `import-dataset` (Path A SOP-004). Refresh trimestral documentado em `docs/sop-refresh-vault-dataset.md`. Reminder em PROJECT-CHECKPOINT por trimestre. | n/a (process) | maintainer | 2026-05-05 |
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

## 📦 Backlog Deferred — Migrated from PRD v1.1.0 §11 (14 entries — F-CHK-02 mitigation)

> **Fonte canônica:** este registro substitui PRD §11 como source of truth (mitigação F-CHK-02 do tribunal CC.1A).
> **Adicionado:** 2026-05-05 (Morgan, sessão 87 PATCH v1.1.1).

| ID | Source | Sev | Description | Est. Effort | Owner | Trigger Re-avaliação | Added |
|----|--------|-----|-------------|-------------|-------|---------------------|-------|
| **BL-AUTH-01** | PRD v1.1.0 §11 | LOW | FR-AUTH-01/02/03 Auth elaborada (bcrypt + cookies + audit log tentativas; substitui FR-LGPD-MVP-01 mínima) | 6-8h | @dev (Neo) | Após 5 advogados validarem MVP em produção | 2026-05-05 |
| **BL-AUTH-02** | PRD v1.1.0 §11 | LOW | FR-AUTH-04 Sessão IP fingerprint + inatividade | 2-3h | @dev (Neo) | Depende BL-AUTH-01 completo | 2026-05-05 |
| **BL-DELIV-03** | PRD v1.1.0 §11 | LOW | FR-DELIV-02 Comparativo de Taxas (D4 — renumerado pós D3 Apelação MVP) | 2-3h | @dev (Neo) | Após v1.0 MVP em produção (3 meses) | 2026-05-05 |
| **BL-DELIV-04** | PRD v1.1.0 §11 | LOW | FR-DELIV-03 Parcelas Reais Incontroversas (D5) | 3-4h | @dev (Neo) | Idem BL-DELIV-03 | 2026-05-05 |
| **BL-DELIV-05a** | PRD v1.1.0 §11 splitado v1.1.1 | LOW | Embargos Declaração + Agravo Instrumento + Recurso Especial (Apelação Cível movida para MVP D3) | 3-4h | @dev (Neo) | Após advogado solicitar (feedback usuário) | 2026-05-05 |
| **BL-MULTI-UF** | PRD v1.1.0 §11 | LOW | FR-RAG-05 Multi-UF first-class CLI roadmap Brasil-wide | 4-8h por UF | @dev (Neo) | Sob demanda — advogado solicita expansão para nova UF | 2026-05-05 |
| **BL-ML-LOOP** | PRD v1.1.0 §11 | LOW | FR-ML-01..04 ML feedback loop estágio 1 (coleta WON/LOST) | 4-6h | @dev (Neo) | Volume ≥50 outcomes registrados (estimado mês 6) | 2026-05-05 |
| **BL-BACKUP** | PRD v1.1.0 §11 | LOW | FR-BACKUP-01/02 + FR-RECOVERY-01 elaborado (vs FR-BACKUP-MVP-01 mínimo MVP) | 3-5h | @dev (Neo) | Após relato de perda de dados em produção OU 6 meses pós-MVP | 2026-05-05 |
| **BL-CONFIG-UI** | PRD v1.1.0 §11 | LOW | FR-CONFIG-01/02 Página Configurações UI + modal aviso | 3-4h | @dev (Neo) | Após advogado solicitar troca frequente de Tier | 2026-05-05 |
| **BL-HITL-ELAB** | PRD v1.1.0 §11 | LOW | FR-JUIZ-02 painel HITL elaborado (bigram diversity + counter visual + microcopy) | 2-3h | @dev (Neo) + @ux-design-expert (Sati) | Após observar bypasses repetitivos em audit log MVP | 2026-05-05 |
| **BL-FIES** | PRD v1.1.0 §6.3 | LOW | Projeto-irmão "Revisor FIES" (avaliação separada — federal vs estadual + 4 razões técnicas) | a definir | @pm (Morgan) | Pós-v1.0 MVP em produção + Eric autorização | 2026-05-05 |
| **BL-VAULT-BULK-IMPORT** | PRD v1.1.1 §2.2 (NOVO) | **HIGH (PRE-RELEASE BLOCKER)** | One-shot bulk import oficial vault (≥600 entries STJ + ≥58 entries STF SV) via SOP-004 Path A | 2-4h maintainer | maintainer (Eric ou delegado) | **Bloqueia release MVP** — gate condition AC-3 e AC-10 | 2026-05-05 |
| **BL-GOLDEN-SET** | PRD v1.1.1 §2.5 (NOVO) | **HIGH (PRE-RELEASE BLOCKER)** | Curadoria 50 contratos sintéticos CDC PF Veículos + 50 queries golden RAG | 8-12h | @qa Oracle | **Bloqueia release MVP** — gate condition AC-1, AC-2, AC-3, AC-10 | 2026-05-05 |
| **BL-OAB-CHECKSUM** | PRD v1.1.2 §2.5 (NOVO — F-NEW-05 Smith re-review) | LOW | Validação OAB regex `^\d{1,6}/[A-Z]{2}$` aceita formato canônico mas SEM checksum CFOAB (bot pode rotar OABs falsas formato-válidas). Mitigação MVP: rate limit 1/min + 100/dia por OAB + audit log forensic tracking | 2-3h | @dev (Neo) | "API CFOAB pública disponível OU dataset OAB+UF público validado" | 2026-05-05 |

> **Total backlog deferred:** 12 LOW (preservados v1.1.0) + 2 HIGH (PRE-RELEASE BLOCKERS v1.1.1) + 1 LOW (NOVO v1.1.2) = **15 entries**
> **Migração executada:** PRD v1.1.1 §2.7 / Morgan sessão 87 / F-CHK-02 OPÇÃO 2 + BL-OAB-CHECKSUM v1.1.2 (F-NEW-05)

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
| **TD-VAULT-SCRAPERS-FRAGILITY** | Sessão 87 (2026-05-05) | Story VAULT-FIX-01 (ADR-012 Path C) | Problema empírico descoberto sessão 86 v0.2.0 testing: `populate-vault --source all` falhava com STJ HTTP 200/404 intermitente (WAF + parser broken — HTML mudou) + STF anti-bot AWS ELB HTTP 403 (mesmo com verify=False). Pipeline real caía em fallback `MOCK_VERDICT`. **Resolução:** ADR-012 Vault Data Bundling Strategy + bundled JSON committed (`bloco_vault/data/sumulas-{stj,stf-vinculantes}.json`) + Pydantic schemas (`bloco_vault/data_schema.py`) + idempotent `populate_vault_if_needed()` em FastAPI lifespan + 3 CLI subcommands (refresh-vault opt-in best-effort, import-dataset PDF compendium oficial, validate-dataset hash verification). Suite 232/1 → 246/1 (14 novos tests AC-8 unit + integration). Scrapers preservados como ferramenta opt-in (zero modificação). |

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

### MEDIUM (3) — ✅ ALL RESOLVED em sessão 86 via Story UI-1

✅ **TD-WEB-VAL-MIME-01 RESOLVED** | Story UI-1 (Phase A) | 2026-05-05 | Validação magic bytes `b'%PDF-'` em revisar() raise HTTPException(400)
✅ **TD-WEB-LISTENER-LEAK-01 RESOLVED** | Story UI-1 (Phase B) | 2026-05-05 | Listener anexado a `#sse-container` (removido no swap, garbage collected)
✅ **TD-WEB-NOMAXSIZE-01 RESOLVED** | Story UI-1 (Phase A) | 2026-05-05 | `MAX_UPLOAD_SIZE = 10MB` + `pdf.size > MAX_UPLOAD_SIZE` raise HTTPException(413)

### LOW (4)

| ID | Source | Sev | Description | Est. Effort | Owner | Added | Remediation by |
|----|--------|-----|-------------|-------------|-------|-------|----------------|
| ~~**TD-WEB-SSE-NOSESSION-01**~~ | ~~Oracle Probe 4 (F-SSE-01)~~ | ~~LOW~~ | ✅ **RESOLVED** Story UI-1 Phase C — `JOBS: dict[str, JobState]` + `/pipeline-stream?job_id=` binding implementado | ~~1h~~ | ~~@dev~~ | ~~2026-05-05~~ | ✅ Resolved 2026-05-05 |
| ~~**TD-WEB-TIER-ENUM-01**~~ | ~~Oracle Probe 3 (F-VAL-02)~~ | ~~LOW~~ | ✅ **RESOLVED** Story UI-1 Phase A — `LLMTier = Literal["lean","balanced","premium"]` substitui `str`; default `"balanced"` (ADR-010 alignment) | ~~10min~~ | ~~@dev~~ | ~~2026-05-05~~ | ✅ Resolved 2026-05-05 |
| ~~**TD-WEB-RUFF-UP037**~~ | ~~Oracle Probe 6 (F-RUF-01)~~ | ~~LOW~~ | ✅ **RESOLVED** Story UI-1 Phase A — `ruff --fix` aplicado; ruff All checks passed | ~~1min~~ | ~~@dev~~ | ~~2026-05-05~~ | ✅ Resolved 2026-05-05 |
| **TD-WEB-CSP-INLINE-01** | Oracle code review (F-CSP-01) | LOW | processing.html tem `<script>` inline (~30 linhas). Strict CSP (`script-src 'self'`) bloquearia. Mover para arquivo externo se CSP for adotado. | 20min | @dev | 2026-05-05 | Opcional (informacional) — out-of-scope UI-1 |

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
