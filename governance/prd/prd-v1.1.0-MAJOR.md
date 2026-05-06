---
type: prd
title: "Revisor Contratual — PRD v1.1.0 (MVP Enxuto + Roadmap 5 Modalidades)"
project: revisor-contratual
version: "1.1.0"
predecessor: "prd/prd-v1.0.3-DELTA.md"
supersedes: "prd-v1.0.2.md + prd-v1.0.3-DELTA.md"
status: active
last_updated: "2026-05-05"
owner: "@pm (Morgan)"
date: "2026-05-05"
sprint: "03 (course-correction)"
bump_basis: "Eric direção sessão 87 — caminho híbrido enxuto pós-diagnóstico Neo. Redução de escopo MVP + roadmap 5 modalidades formalizado. MAJOR bump per prd-governance.md art. MAJOR Bump Impact Protocol."
inputs:
  - ".lmas/handoffs/handoff-morpheus-to-pm-2026-05-05-cc1a-prd-v1.1.0.yaml"
  - "prd/prd-v1.0.2.md (canônico predecessor)"
  - "prd/prd-v1.0.3-DELTA.md (PATCH predecessor)"
  - "Diagnóstico Neo→Eric (3 trocas sessão 87, registradas em histórico)"
tags:
  - project/revisor-contratual
  - prd
  - prd-v1.1.0
  - mvp-lean
  - course-correction
  - sprint-03
  - cdc-veiculos
  - tjba
---

# PRD v1.1.0 — Revisor Contratual (MVP Enxuto + Roadmap 5 Modalidades)

| Campo | Valor |
|---|---|
| **Versão** | 1.1.0 (MAJOR — pivot de escopo: cortes substanciais + roadmap multi-modalidade) |
| **Status** | Active |
| **Owner** | @pm (Morgan) |
| **Data** | 2026-05-05 |
| **Diretor** | Eric Claudino |
| **Domínio** | software-dev / sub-domain: legaltech |
| **Sprint** | 03 · etapa CC.1A |
| **Predecessor** | v1.0.2 + v1.0.3-DELTA (preservados como histórico) |

---

## 1. Visão (uma frase)

**Revisor Contratual é um sistema agentic 100% local que analisa contratos de financiamento bancário CDC PF Veículos e produz, em até 3 minutos, Petição Específica revisional + Relatório Contábil fundamentados em jurisprudência STJ/STF — com roadmap modular para Imobiliária, Bancário genérico e Crédito pós-MVP, preservando LGPD on-premise como diferencial não-negociável.**

---

## 2. Objetivo

Entregar a advogados consumeristas bancários uma ferramenta MVP capaz de:

1. **Identificar** ilegalidades, excesso de cobrança, taxas abusivas e anatocismo em contratos CDC PF Veículos (modalidade única do MVP).
2. **Construir** tese jurídica + análise contábil com fundamentação rastreável a jurisprudência vinculante (peso ≥4) via 4 personas LLM internas (Advogado + Economista + Juiz + Perito).
3. **Produzir** Petição Específica revisional (Jinja2 + WeasyPrint) e Relatório Contábil estruturado (markdown), com validação semântica anti-hallucination obrigatória antes da emissão.
4. **Operar 100% local** (NFR-LGPD-01 não-negociável) no laptop do usuário (8-16GB RAM).
5. **Expansão modular pós-MVP:** cada modalidade nova (Imobiliária, Bancário genérico, Crédito) é story incremental +20-40h sem rewrite arquitetural — não é ferramenta multi-modalidade desde o MVP, é ferramenta com arquitetura modular.

---

## 3. Personas (preservadas de v1.0.2)

### 3.1 Persona Usuário (externa)

**P-USR-01 — Advogado consumerista bancário**
- Atua em ações revisionais CDC PF Veículos no MVP
- Cliente final: pessoa física com financiamento veicular cobrando taxa acima da média BACEN
- Volume típico: 1-30 contratos/mês
- Hardware típico: laptop Windows/Mac 8-16GB RAM
- Dor que pagamos: hoje gasta horas calculando Tabela Price + buscando jurisprudência manualmente + redigindo tese; quer entregar petição com base sólida em minutos

### 3.2 Personas Internas (preservadas — vontade explícita Eric, NÃO cortar)

- **P-INT-01 — Perito Contábil e Fiscal** (função Python + Decimal puro + python-bcb)
- **P-INT-02 — Advogado especialista** (LLM Tier Balanced default = Qwen 2.5 7B; Sabia-7B preserved opt-in)
- **P-INT-03 — Juiz Revisor** (função Python pura — não LLM, preserva auditabilidade)
- **P-INT-04 — Economista (entidades bancárias)** (LLM obrigatória; mitigação Tema 1378 STJ)

---

## 4. Escopo IN — MVP v1.1.0

### 4.1 Modalidade contratual (ÚNICA no MVP)

- **CDC PF Veículos APENAS** (financiamento veicular pessoa física)
- Justificativa: 80% dos financiamentos veiculares usam Tabela Price (CalculoJurídico), corpus de jurisprudência consolidado, código BACEN específico (SGS 25471 + 20749), validação rápida com 2-3 advogados antes de expandir.

### 4.2 Análises produzidas (preservadas core)

- Identificação de ilegalidades (cláusulas abusivas — CDC art. 51)
- Identificação de excesso de cobrança (taxa contratual vs taxa média BACEN para Veículos PF)
- Identificação de juros abusivos (Súmula 539 STJ + jurisprudência local)
- Detecção de anatocismo matemático (comparação Price vs juros simples)
- Classificação jurídica do anatocismo: SEM_ANATOCISMO | ANATOCISMO_LICITO | ANATOCISMO_QUESTIONAVEL | ANATOCISMO_ILICITO

### 4.3 Deliverables MVP — APENAS 2 (cortado de 5 para 2)

- **D1: Relatório Contábil** (markdown estruturado: dados contrato + tabela amortização Decimal + divergência matemática vs BACEN + classificação anatocismo + valores incontroversos)
- **D2: Petição Específica** (PDF Jinja2 + WeasyPrint, hash sha256 audit-tracked, com qualificação partes + fatos + fundamentos jurídicos com citações `[id_doc:X]` + pedidos)

> **3 deliverables movidos para roadmap pós-MVP:** Comparativo de Taxas (D3) + Parcelas Reais Incontroversas (D4) + Recursos Processuais (D5). Justificativa: D3 e D4 são tabelas auxiliares ao Relatório Contábil — podem ser features de v1.1+ quando D1 estiver validado em produção. D5 (recursos) requer fluxo separado pós-decisão adversa, não bloqueia MVP de petição inicial.

### 4.4 Jurisdição (preservado)

- UF inicial: **Bahia (TJBA + STJ + STF)**
- Multi-UF disponível como dado via CLI `add_uf` (FR-RAG-05 já first-class no design), mas SEM roadmap explícito Brasil-wide no MVP — expansão sob demanda.

### 4.5 Operação

- Single-user (1 advogado)
- Single-process Python local (sem containers — Docker opcional pós-v1.0)
- **SEM auth elaborada** (cortado FR-AUTH-01/02/03 — MVP local, advogado é único acesso à máquina dele)
- ML feedback loop estágio 1: **CORTADO do MVP** (v1.1+ ou Fase 2)

### 4.6 Stack técnica MVP

- **Python 3.11+** (3.12 / 3.13 no roadmap)
- **FastAPI + HTMX + Jinja2 + uvicorn** (UI Web), **CLI Click** (entry point principal — Constitution Art. I CLI First preservado)
- **Ollama local** com auto-lifecycle (OLLAMA-MGR-01) — UX "1 comando"
- **Vault sqlite-vec** (768 dims Legal-BERTimbau), bundled JSON lean (~600-700 entries via ADR-012)
- **python-bcb** para BACEN SGS (whitelist NFR-LGPD-01 preservada)
- **PyMuPDF4LLM + Marker fallback** (parsing PDF)
- **structlog → audit.jsonl** com HMAC GENESIS chain (ADR-005)

---

## 5. Escopo OUT — MVP v1.1.0 (movido para roadmap)

### 5.1 Cortes formais do MVP (7 itens) — Backlog Deferred

| # | Item cortado | Predecessor v1.0.3 | Movido para |
|---|---|---|---|
| C1 | **FR-AUTH-01/02/03** Auth elaborada (bcrypt + cookies + audit log de tentativas) | FR-AUTH-01..03 v1.0.2 | v1.1+ (após validação MVP) |
| C2 | **D3 Comparativo de Taxas** (deliverable) | FR-DELIV-02 v1.0.2 | v1.1+ |
| C3 | **D4 Parcelas Reais Incontroversas** (deliverable) | FR-DELIV-03 v1.0.2 | v1.1+ |
| C4 | **D5 Recursos Processuais** (deliverable) | FR-DELIV-05 v1.0.2 | v1.1+ |
| C5 | **FR-RAG-05** Multi-UF first-class CLI roadmap | FR-RAG-05 v1.0.2 | v1.2+ (CLI add_uf disponível como dado, sem roadmap) |
| C6 | **FR-ML-01..04** ML feedback loop estágio 1 (coleta WON/LOST) | FR-ML-01..04 v1.0.2 | Fase 2 |
| C7 | **FR-BACKUP-01/02 + FR-RECOVERY-01** Backup/recovery elaborado | FR-BACKUP-01..02 + FR-RECOVERY-01 v1.0.2 | v1.1+ (maintainer manual no MVP) |
| C8 | **FR-CONFIG-01/02** Página Configurações UI + modal aviso reinício | FR-CONFIG-01/02 v1.0.3 | v1.1+ (edit .env direto + restart manual no MVP) |
| C9 | **Painel HITL elaborado** (microcopy detalhada Sati EV-01 + EV-09 + counter visual + bigram diversity) | FR-JUIZ-02 (especificação detalhada) v1.0.2 | v1.1+ (painel mínimo 3 botões + textarea curta no MVP) |

> **Nota Morgan:** Cortes não removem CAPACIDADES — apenas movem implementação para versões posteriores. ADR-009 (LGPD on-premise) preservado intacto. Pipeline core (4 personas + Decimal + validação semântica + audit HMAC) mantido como diferencial.

### 5.2 Itens permanentemente fora do MVP (preservados de v1.0.2)

- Contratos não-bancários (locação, trabalho, civis genéricos) → Fase 4+
- Defesa de bancos (lado oposto) → NUNCA
- Multi-tenant (múltiplos escritórios isolados) → Fase 3+
- VPS multi-tenant SaaS → DESCARTADO (quebra ADR-009 NFR-LGPD-01 100% on-premise)
- Cloud LLM como default → opt-in via `LLM_ALLOW_CLOUD_PROVIDER=true` apenas

---

## 6. Roadmap 5 Modalidades (pós-MVP)

Eric explicitou visão de 5 modalidades como roadmap. **MVP v1.1.0 é monomodalidade (Veicular APENAS)** para shipping rápido. Modalidades adicionais entram como stories incrementais sem rewrite arquitetural.

### 6.1 Sequenciamento proposto (Morgan decide ROI-otimizado)

| Versão | Modalidade | Estimativa | Razão sequência |
|---|---|---|---|
| **v1.0 MVP** | CDC PF Veículos | 25-35h (já em curso) | Eric MVP target; jurisprudência consolidada; BACEN SGS específico mapeado |
| **v1.1** | **Bancário Genérico** (CDC não-veicular não-imobiliário) | +20-30h | **Maior reuso código (~80%)** — mantém Tabela Price + anatocismo + 4 personas + audit chain. Apenas: novos códigos BACEN SGS + jurisprudência expandida + parser PDF flexível. **Fastest-to-market.** |
| **v1.2** | **Imobiliária** (CDC SFH/SFI) | +30-40h | **Maior volume mercado** mas requer refator BACEN (SGS imobiliário diferente) + jurisprudência específica (Tema 922 STJ + ADC Caixa) + parser PDF (contratos imobiliários estrutura mais complexa). |
| **v1.3** | **Crédito Bancário** (cartão rotativo + cheque especial) | +25-35h | Público diferente (não-financiamento, é crédito direto). Jurisprudência específica (Tema 27 STJ rotativo). Reuso código ~70%. |

**Razão Morgan para sequenciar Bancário Genérico ANTES de Imobiliária** (mesmo Imobiliária ter maior volume): ROI de tempo dev é maior se a próxima modalidade reaproveitar 80% código. Bancário genérico = quick win → valida arquitetura modular → Imobiliária ganha confiança técnica antes de investir +30-40h.

### 6.2 Multi-UF (Brasil-wide) — dado, não rewrite

- CLI `add_uf` já first-class no design FR-RAG-05 (preservado de v1.0.2)
- Adicionar UF ao vault: rodar scraper OR import-dataset oficial + reindexar (~4-8h por UF)
- **NÃO é rewrite** — é manutenção operacional pós-MVP
- Whitelist NFR-LGPD-01 expandida exige ADR formal por TJ (ADR-008 pipeline scraping multi-UF preservado)

### 6.3 FIES — Decisão arquitetural Morgan

**Decisão:** **FIES vira projeto-irmão "Revisor FIES" (NÃO entra no roadmap Revisor Contratual).**

**Justificativa técnica (5 razões):**

1. **Jurisdição federal vs estadual:** FIES é regulado por FNDE (Fundo Nacional Desenvolvimento Educação) com jurisdição federal (TRFs + STJ). Revisor Contratual atual é estadual (TJ + STJ + STF). Stack vault e jurisprudência são fundamentalmente diferentes.
2. **Procedimento administrativo vs revisional:** FIES contestação é via **suspensão administrativa** (Caixa banco gestor + Procuradoria-Geral Federal/AGU) — NÃO revisional contratual bancária pura. Workflow do produto é distinto.
3. **Regulamento FNDE específico:** FIES não usa BACEN SGS (taxa de juros é FIXA por contrato + fundo público). Stack `python-bcb` e `FR-BACEN-01..03` não se aplicam.
4. **ICP diferente:** Advogado especializado em educação superior + FIES + FNDE ≠ advogado consumerista bancário. Marketing, copy, posicionamento divergem.
5. **Modelo de negócio diferente:** Revisor Contratual cliente final é PF com superendividamento bancário privado. Revisor FIES cliente final é estudante/ex-estudante com dívida pública subsidiada. Operações de cobrança e tese jurídica seguem caminhos distintos.

**Recomendação Morgan:** criar projeto-irmão `revisor-fies` em repositório separado quando MVP Revisor Contratual estiver shipping (post v1.0). Reuso possível: framework LMAS, agentes, audit HMAC, validação semântica citações — backend modular. Mas pipeline + vault + parser são novos.

**Backlog item formal:** Projeto-irmão "Revisor FIES" — avaliação Sprint 04+ ou Fase 2.

---

## 7. Functional Requirements MVP v1.1.0 (LEAN)

> **Nota:** FRs preservados de v1.0.2 com numeração mantida para rastreabilidade. ACs ajustados para refletir cortes do MVP. FRs cortados (ver §5.1) NÃO aparecem aqui — registrados em §11 Backlog Deferred.

### 7.1 Auth & Sessão (CORTADO no MVP)

- **FR-AUTH-01/02/03/04** → DEFERRED para v1.1+ (após validação MVP)
- MVP single-user local: aplicação roda sem login. Acesso à máquina = acesso ao app.

### 7.2 Upload e Parsing de Contrato (preservado)

- **FR-UPLOAD-01** Upload PDF até 100MB com validação magic bytes (`%PDF-`) + metadados UF/data/valor
- **FR-PARSE-01** Extração Markdown via PyMuPDF4LLM (default) + Marker (OCR fallback)
- **FR-PARSE-02** Extração regex/heurística de campos contratuais (taxa, prazo, valor financiado, modalidade)

### 7.3 Cálculo Determinístico (Decimal everywhere — preservado, NÃO cortar)

- **FR-CALC-01** Tabela Price com Decimal (precisão ≥28 dígitos, `getcontext().prec=28`)
- **FR-CALC-02** Tabela amortização (saldo, juros, amortização, valor parcela, saldo final — todos Decimal-as-string)
- **FR-CALC-03** Detecção e classificação de anatocismo (4 vereditos)

### 7.4 Integração BACEN (preservado)

- **FR-BACEN-01** Fetch BACEN python-bcb + mapping `codigos_bacen.yaml` (Veículos PF SGS 25471 + 20749 confirmados)
- **FR-BACEN-02** Cache diskcache TTL 30 dias + retry tenacity backoff exponencial
- **FR-BACEN-03** Fallback "última taxa conhecida" com alerta visível

### 7.5 RAG Jurisprudência (preservado, vault lean)

- **FR-RAG-01** Indexação bundled JSON ~600-700 entries (STJ + STF SV) via ADR-012 — VAULT-FIX-01 implementou. Schema enriquecido v1.0.2 (vigente_em + superseded_by + data_ultima_validacao) preservado.
- **FR-RAG-02** Busca híbrida BM25 + vetorial RRF k=60, filtros UF + binding + vigência (peso ≥3 default)
- **FR-RAG-03** Fallback "relaxar binding" → Relatório de Inviabilidade se RAG vazio
- **FR-RAG-04** Cache queries diskcache TTL 24h
- **FR-RAG-05** ~~CLI multi-UF first-class~~ → DEFERRED v1.2+ (CLI add_uf existe como dado, sem roadmap explícito Brasil-wide no MVP)
- **FR-RAG-06** Benchmark cobertura vault (≤15% Inviabilidade no golden set) — preservado, executado pelo @qa antes do release MVP

### 7.6 Geração de Tese (Advogado LLM — preservado, NÃO cortar)

- **FR-TESE-01** Citation-grounded com validação cruzada `docs_citados ⊆ docs_consultados`
- **FR-TESE-02** Fallback Tier (lean / balanced default Qwen 2.5 7B / premium Sabia-7B opt-in) — alinhado ADR-010
- **FR-TESE-03** Provider abstrato (ollama default, llamacpp embedded, openai_compatible cloud opt-in com aviso)
- **FR-TESE-04** **Validação semântica de citações (NÃO cortar — Smith F-CRIT-02 mitigação fundamental)** — cosine similarity ≥0.7 obrigatório, hard-fail bloqueia emissão sem reading

### 7.7 Validação do Juiz Revisor (preservado, painel HITL simplificado)

- **FR-JUIZ-01** 3 checagens determinísticas (C1 BACEN + C2 vinculação + C3 jurisdição) com scoring
- **FR-JUIZ-02** 3 vereditos (APROVADO_100 / APROVADO_COM_RISCO_HITL / REJEITADO) — **painel HITL MVP simplificado:** 3 botões (Aprovar / Solicitar novo cálculo / Abortar) + textarea justificativa obrigatória ≥20 chars (sem bigram diversity check, sem validação semântica anti-bypass elaborada). Validação anti-bypass complexa → DEFERRED v1.1+.
- **FR-JUIZ-03** Audit log da decisão (preservado)

### 7.8 Deliverables MVP — 2 (cortado de 5 para 2)

- **FR-DELIV-01 D1: Relatório Contábil** (markdown estruturado, sempre gerado mesmo em REJEITADO)
- **FR-DELIV-04 D2: Peticionamento Específico** (PDF Jinja2 + WeasyPrint, hash sha256 audit-tracked)
- **FR-DELIV-06 Tela Revisão e Adoção (CFOAB) NÃO cortar** — checkbox "LI, CONFERI E ADOTO" + OAB+UF+nome obrigatórios + audit log adoção. Aplicável SOMENTE a D2 no MVP (D1 não é peça jurídica). Provimento CFOAB 205/2021 + Estatuto OAB Lei 8.906/94 art. 32.

> **Cortados:** FR-DELIV-02 (Comparativo Taxas D3) + FR-DELIV-03 (Parcelas Reais D4) + FR-DELIV-05 (Recursos Processuais D5) → todos DEFERRED v1.1+.

### 7.9 Audit Log (preservado, NÃO cortar — diferencial LGPD)

- **FR-AUDIT-01** structlog → audit.jsonl append-only com HMAC GENESIS chain (ADR-005)
- **FR-AUDIT-02** Tema 1378 STJ trigger CRITICAL_JURIS_CHANGE
- **FR-AUDIT-01 hash chain anti-tamper** (Smith F-HIGH-04) — preservado, comando `verify-audit-integrity` detecta tampering em <5s

### 7.10 Setup, Backup, Recovery (PARCIAL no MVP)

- **FR-SETUP-01** Bootstrap único (preservado, simplificado): `python -m bloco_interface.web.app` → auto-Ollama (OLLAMA-MGR-01) + auto-vault populate (VAULT-FIX-01) + ready em ~30s
- **FR-SETUP-02** Mensagens 4-bloco PT-BR estruturadas (preservado de v1.0.3)
- ~~**FR-BACKUP-01/02** Backup automático e manual~~ → DEFERRED v1.1+ (maintainer manual no MVP via cp vault.db + audit.jsonl)
- ~~**FR-RECOVERY-01** Recovery mid-workflow LangGraph checkpointer~~ → DEFERRED v1.1+ (re-upload contrato no MVP em caso de crash)
- **FR-MONITOR-01** Monitoramento Tema 1378 STJ — DEFERRED v1.1+ (alerta manual via maintainer no MVP)

### 7.11 Configurações Avançadas (CORTADO no MVP)

- ~~**FR-CONFIG-01** Página Configurações Avançadas com toggle visual~~ → DEFERRED v1.1+ (edit .env + restart manual no MVP)
- ~~**FR-CONFIG-02** Modal aviso perda de sessão~~ → DEFERRED v1.1+ (depende de FR-CONFIG-01)
- ~~**FR-AUTH-04** Sessão IP fingerprint~~ → DEFERRED v1.1+ (depende de FR-AUTH-01..03)

---

## 8. Critérios de Aceite Numéricos (MVP v1.1.0)

| AC | Métrica | Target | Como verificar |
|---|---|---|---|
| **AC-1** Latência end-to-end | ≤180s mediana | 50 contratos golden set | Benchmark @qa |
| **AC-2** Taxa de extração tabela amortização | ≥95% fidelidade | 50 contratos golden set | Validação aritmética juros + amortização == valor parcela ±R$ 0.01 |
| **AC-3** Cobertura vault RAG | ≤15% Inviabilidade por RAG vazio | 50 queries golden set | FR-RAG-06 — benchmark @qa pré-release |
| **AC-4** Hard-fail citações fantasmas | 0% emissões | Suite testes | `docs_citados ⊆ docs_consultados` validação cruzada |
| **AC-5** Validação semântica cosine | 0% emissões com similarity <0.7 | Suite testes | FR-TESE-04 hard-fail |
| **AC-6** Audit log integridade HMAC | 100% events rastreáveis | Comando `verify-audit-integrity` | <5s detecção tampering |
| **AC-7** Adoção CFOAB obrigatória | 0% PDFs emitidos sem checkbox+OAB | UI + audit log | `revisar` route teste E2E |
| **AC-8** Suite testes regressão | ≥246 passed + 1 skipped | `pytest --no-cov` | Baseline atual VAULT-FIX-01 Phase E |
| **AC-9** ruff lint | All checks passed | Arquivos modificados | CI pipeline + dev pre-commit |
| **AC-10** Smoke E2E real (TD-PIPELINE-SMOKE-REAL) | PASS pipeline integral | Ollama + Qwen 7B + Sabia-7B + PDF físico + httpx STJ/STF | @devops + @dev pré-release |

---

## 9. UX Spec — Placeholder (Sati CC.3)

> **Owner:** @ux-design-expert (Sati). Especificação detalhada em CC.3 do fluxo course-correction.

**Princípios MVP enxuto (briefing inicial Sati):**

- **Site single-page:** drop PDF → SSE pipeline progress → resultado (sem painel histórico, sem login)
- **3-4 estados visuais:** idle (drop zone) / processing (SSE progress 7 steps) / result (verdict + 2 deliverables download links) / error (4 templates UI-1 já implementadas)
- **HITL simplificado** (FR-JUIZ-02 LEAN): 3 botões (Aprovar / Solicitar novo cálculo / Abortar) + textarea justificativa ≥20 chars (sem bigram diversity check elaborado)
- **Microcopy enxuta:** sem placeholder contextual rico (Sati v1.0.2 EV-01 era para painel elaborado — DEFERRED)
- **Sem painel Configurações UI:** cortado FR-CONFIG-01/02
- **Sem página outcomes/feedback ML:** cortado FR-ML-01

Sati produzirá `governance/ux-spec-v1.1.0-MVP-LEAN.md` em CC.3 com:
- Wireframes 3-4 estados (low-fi)
- Microcopy estados error (preservar 4 templates UI-1)
- A11y baseline WCAG AA
- Tokens design system preservados (REV-INT-02 self-host fonts)

---

## 10. Dependências

### 10.1 ADRs (preservados)

| ADR | Status | Impacto MVP v1.1.0 |
|---|---|---|
| ADR-001 Gerenciamento estado | accepted | Preservado |
| ADR-002 Design system | accepted | Preservado (tokens self-hosted REV-INT-02) |
| ADR-003 4 personas implementação | accepted | Preservado (Economista mantida) |
| ADR-004 Validação semântica citações | accepted | **CRÍTICO — não cortar (FR-TESE-04)** |
| ADR-005 Audit log HMAC | accepted | **CRÍTICO — diferencial LGPD** |
| ADR-006 Preview seguro PDF | accepted | Preservado (FR-DELIV-06 Tela Adoção) |
| ADR-007 Schema sqlite-vec | accepted | Preservado |
| ADR-008 Pipeline scraping multi-UF | accepted | Preservado (CLI add_uf como dado) |
| ADR-009 Backup/LGPD pseudonimização | accepted | **CRÍTICO — NFR-LGPD-01 preservado, VPS descartado** |
| ADR-010 Sabia Q4 mitigation (Path C Qwen 7B fallback) | accepted | Preservado (LLM_TIER=balanced default) |
| ADR-011 Auto-Ollama lifecycle | accepted | Preservado — story OLLAMA-MGR-01 mantida MVP |
| ADR-012 Vault data bundling | accepted, implementado | Preservado — story VAULT-FIX-01 Ready for Review |

### 10.2 Stories existentes — Impact Protocol

Per `prd-governance.md` art. **MAJOR Bump Impact Protocol**:

| Story | Status pré-PRD v1.1.0 | Tratamento | Razão |
|---|---|---|---|
| **VAULT-FIX-01** | Ready for Review | **Preservada sem alterações de AC** — Keymaker fará delta-revalidation pós-publish (~10-15 min) | ADR-012 permanece accepted. Bundled vault lean ~600-700 entries é a solução técnica do caminho híbrido. Implementação Phase A+B+C+D+E (246 tests, ruff clean) é compatível com MVP enxuto. |
| **OLLAMA-MGR-01** | Ready (não iniciada) | **Preservada sem alterações** — Keymaker reconfirma | ADR-011 permanece accepted. UX "1 comando" (auto-Ollama lifecycle) é mantida pelo caminho híbrido. Story 14 ACs continuam válidos. |

> **NOTA importante:** stories cortadas (auth, 3 deliverables, multi-UF first-class, ML loop, backup elaborado, config UI, painel HITL elaborado) **NÃO existem como stories formais ainda** — são entries de **Backlog Deferred** (§11), não retrabalho.

### 10.3 Stories MVP futuras (River CC.4 criará)

- **MVP-LEAN-01** (Sprint 03+ pós CC.4) — Implementação pipeline lean com 2 deliverables (D1 + D2), UI single-page, HITL simplificado, sem auth elaborada. Estimativa: 15-22h pós-VAULT-FIX-01 + OLLAMA-MGR-01.

---

## 11. Backlog Deferred (cortes formais com tracking)

> Estes 9 itens cortados do MVP NÃO foram cancelados — apenas movidos para versões posteriores. Cada item será criado como story formal quando atingir prioridade.

| ID Backlog | Descrição | Versão alvo | Estimativa | Razão corte MVP |
|---|---|---|---|---|
| **BL-AUTH-01** | FR-AUTH-01/02/03 Auth elaborada (bcrypt + cookies + audit log tentativas) | v1.1+ | 6-8h | App local single-user; advogado é único acesso à máquina dele |
| **BL-AUTH-02** | FR-AUTH-04 Sessão IP fingerprint + inatividade | v1.1+ | 2-3h | Depende BL-AUTH-01 |
| **BL-DELIV-03** | FR-DELIV-02 Comparativo de Taxas (D3) | v1.1+ | 2-3h | Tabela auxiliar ao Relatório Contábil; v1.0 valida D1+D2 antes |
| **BL-DELIV-04** | FR-DELIV-03 Parcelas Reais Incontroversas (D4) | v1.1+ | 3-4h | Mesma justificativa BL-DELIV-03 |
| **BL-DELIV-05** | FR-DELIV-05 Recursos Processuais (D5) | v1.1+ | 4-6h | Fluxo separado pós-decisão adversa; não bloqueia MVP de petição inicial |
| **BL-MULTI-UF** | FR-RAG-05 Multi-UF first-class CLI roadmap Brasil-wide | v1.2+ | 4-8h por UF | CLI add_uf existe como dado; expansão sob demanda |
| **BL-ML-LOOP** | FR-ML-01..04 ML feedback loop estágio 1 (coleta WON/LOST) | Fase 2 | 4-6h | Requer volume ≥50 outcomes (estimado mês 6); v1.0 prepara schema apenas |
| **BL-BACKUP** | FR-BACKUP-01/02 + FR-RECOVERY-01 elaborado | v1.1+ | 3-5h | Maintainer manual no MVP via `cp vault.db + audit.jsonl` |
| **BL-CONFIG-UI** | FR-CONFIG-01/02 Página Configurações UI + modal aviso | v1.1+ | 3-4h | Edit .env + restart manual no MVP |
| **BL-HITL-ELAB** | FR-JUIZ-02 painel HITL elaborado (microcopy detalhada Sati EV-01 + bigram diversity + counter visual) | v1.1+ | 2-3h | MVP usa painel mínimo 3 botões + textarea ≥20 chars |
| **BL-MONITOR-1378** | FR-MONITOR-01 Monitoramento ATIVO Tema 1378 STJ | v1.1+ | 3-4h | Maintainer manual no MVP (verifica STJ semanal) |
| **BL-FIES** | Projeto-irmão "Revisor FIES" (avaliação separada) | Fase 2+ | a definir | Federal vs estadual + procedimento administrativo + regramento FNDE distinto (§6.3) |

**Total estimado backlog deferred:** ~36-58h (cortes economizam exatamente esta janela do MVP).

---

## 12. NFRs (preservados, ajustados)

### 12.1 NFR-PERF-01 — Latência (ajustado)

- **MVP v1.1.0:** ≤180s mediana (vs 210s v1.0.2)
- Razão da redução: cortes de painel HITL elaborado (-5s render), 3 deliverables extras (-10-15s), auth (-2s). Pipeline 4 personas LLM mantido (Economista preservada).
- Worst case ainda aceitável: ≤210s com Tier Premium Sabia-7B Q4 CPU.

### 12.2 NFR-LGPD-01 — 100% on-premise (PRESERVADO INTACTO)

- Nenhum dado do contrato sai da máquina. Whitelist HTTP estrita: STJ + STF + BACEN + 127.0.0.1 (Ollama local).
- **VPS multi-tenant DESCARTADO** — quebra deste princípio. Reafirmado.
- 7 fontes Google Fonts self-hosted (REV-INT-02 RESOLVED v0.2.0).
- Docker opcional pós-v1.0 NÃO viola NFR-LGPD-01 (container roda local).

### 12.3 NFR-MAINT-02 — Cobertura testes

- ≥246 passed + 1 skipped baseline (atualizado pós VAULT-FIX-01 Phase E)
- Suite continua subindo a cada story (MVP-LEAN-01 add ~10-15 tests)

### 12.4 Demais NFRs (preservados de v1.0.2)

NFR-PERF-02, NFR-PERF-03, NFR-LGPD-02..05, NFR-MAINT-01, NFR-GOV-01, NFR-RELIAB-01..02 — todos preservados intactos.

---

## 13. Riscos com Mitigação

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| **R1:** Modalidade-única no MVP reduz TAM (target addressable market) | MÉDIA | MÉDIO | Validação rápida com 2-3 advogados Veicular antes de investir +20-30h em Bancário Genérico v1.1 |
| **R2:** Vault provisional ~10 entries hoje (PROVISIONAL — VAULT-FIX-01 Phase B) | ALTA | ALTO em produção | Maintainer DEVE fazer one-shot bulk import oficial pré-produção (SOP-004 documenta Path A/B/C). Reminder em PROJECT-CHECKPOINT trimestral |
| **R3:** Shipping atrasar com cortes incompletos (escopo creep) | MÉDIA | MÉDIO | Keymaker valida MVP-LEAN-01 story com timeboxing rigoroso (15-22h máximo). Smith adversarial review pré-Operator push |
| **R4:** Cortar auth pode comprometer LGPD se laptop roubado | BAIXA (single-user MVP) | MÉDIO | MVP é single-user single-machine; advogado responsável pela segurança física da máquina. v1.1+ adiciona FR-AUTH (BL-AUTH-01) |
| **R5:** Cortar painel HITL elaborado pode comprometer FR-DELIV-06 (CFOAB) | BAIXA | ALTO | Painel HITL minimal MANTÉM checkbox CFOAB obrigatório + OAB+UF+nome (Provimento CFOAB 205/2021). Apenas microcopy elaborada (placeholder rico, bigram diversity) é DEFERRED |
| **R6:** Roadmap 5 modalidades pode confundir investidores/advogados sobre foco MVP | MÉDIA | MÉDIO | Marketing/Brand pós-MVP comunicar claramente "v1.0 = Veicular; outras vêm depois" — não vender capacidades futuras como presentes |
| **R7:** FIES como projeto-irmão pode duplicar esforço de framework | BAIXA | BAIXO | Framework LMAS + agentes + validação semântica + audit HMAC são reutilizáveis. Apenas pipeline + vault + parser são novos. Estimativa Fase 2+ |
| **R8:** Tema 1378 STJ julgado durante MVP development sem monitor ativo | BAIXA (jurisprudencial timing) | ALTO se ocorrer | Maintainer verifica STJ semanal manualmente até BL-MONITOR-1378 (v1.1+). Risco aceito conscientemente |

---

## 14. Decisão FIES — Documentação isolada (referência §6.3)

**Pergunta original Eric (sessão 87):** "Esse projeto está sendo criado para executar nas seguintes dívidas: Veicular, Imobiliária, Contrato Bancário, Crédito Bancária, Contrato FIES."

**Decisão Morgan:** **FIES vira projeto-irmão "Revisor FIES" — NÃO entra no roadmap Revisor Contratual.**

**Evidências técnicas (5 razões):**

1. **Jurisdição:** FIES é federal (FNDE + TRFs + AGU). Revisor Contratual é estadual (TJ + STJ + STF).
2. **Procedimento:** FIES é contestação **administrativa** via Caixa banco gestor + PGF. Revisor Contratual é **revisional contratual judicial**.
3. **Regramento:** FNDE (não BACEN). `python-bcb` + FR-BACEN-01..03 não se aplicam a FIES.
4. **Vault e jurisprudência:** AGU portarias + jurisprudência TRFs federal ≠ STJ/STF/TJ estadual.
5. **ICP e modelo de negócio:** advogado FNDE/educação ≠ advogado consumerista bancário. Marketing, copy, posicionamento divergem.

**Plano:**

- Backlog item **BL-FIES** registrado em §11.
- Sprint 04+: avaliação se vale criar projeto-irmão `revisor-fies` (em repo separado) reutilizando framework LMAS + agentes + audit + validação semântica.
- Decisão final será de Eric pós-MVP Revisor Contratual em produção.

---

## 15. Delta Section v1.0.3 → v1.1.0 (per `prd-governance.md` MAJOR bump)

### 15.1 Features Adicionadas

- **Roadmap 5 modalidades estruturado** — sequenciamento ROI-otimizado documentado (§6.1)
- **Decisão FIES isolada** — projeto-irmão justificado tecnicamente (§6.3 + §14)
- **Backlog Deferred formal** — 12 itens com tracking ID, versão alvo, estimativa, razão (§11)

### 15.2 Features Modificadas

- **Visão** — reescrita refletindo MVP modalidade-única + roadmap multi-modalidade (§1)
- **Escopo IN MVP** — restrito a CDC PF Veículos (era multi-modalidade implícita) (§4.1)
- **Deliverables MVP** — cortado de 5 para 2 (D1 Relatório Contábil + D2 Petição) (§4.3)
- **NFR-PERF-01** — latência target ≤180s (vs ≤210s v1.0.2) refletindo cortes (§12.1)

### 15.3 Features Removidas (movidas para roadmap pós-MVP)

| Item | Versão alvo | ID Backlog |
|---|---|---|
| FR-AUTH-01/02/03/04 | v1.1+ | BL-AUTH-01/02 |
| FR-DELIV-02 (D3 Comparativo Taxas) | v1.1+ | BL-DELIV-03 |
| FR-DELIV-03 (D4 Parcelas Reais) | v1.1+ | BL-DELIV-04 |
| FR-DELIV-05 (D5 Recursos Processuais) | v1.1+ | BL-DELIV-05 |
| FR-RAG-05 multi-UF first-class roadmap | v1.2+ | BL-MULTI-UF |
| FR-ML-01..04 ML feedback loop estágio 1 | Fase 2 | BL-ML-LOOP |
| FR-BACKUP-01/02 + FR-RECOVERY-01 | v1.1+ | BL-BACKUP |
| FR-CONFIG-01/02 + FR-AUTH-04 | v1.1+ | BL-CONFIG-UI |
| FR-JUIZ-02 painel HITL elaborado | v1.1+ | BL-HITL-ELAB |
| FR-MONITOR-01 Tema 1378 ATIVO | v1.1+ | BL-MONITOR-1378 |

### 15.4 Escopo Atual vs Original

- **v1.0.3:** 14 FRs + 9 NFRs + 9 DPs + 7 web debts incorporados
- **v1.1.0:** ~8 FRs ativos MVP (FR-UPLOAD-01 + FR-PARSE-01/02 + FR-CALC-01..03 + FR-BACEN-01..03 + FR-RAG-01..04+06 + FR-TESE-01..04 + FR-JUIZ-01..03 + FR-DELIV-01+04+06 + FR-AUDIT-01/02 + FR-SETUP-01/02) + 9 NFRs preservados + 9 DPs + 12 backlog items (cortes) + Roadmap 4 modalidades pós-MVP + 1 projeto-irmão (Revisor FIES)
- **Motivo principal:** Eric direção sessão 87 — caminho híbrido enxuto pós-diagnóstico Neo. MVP shipping em ~25-35h vs ~60-80h cenário B, preservando diferenciais não-negociáveis (LGPD on-premise + 4 personas LLM + validação semântica + audit HMAC)

---

## 16. Action Items v1.1.0 — Próximas Etapas Course-Correction

- [ ] **CC.1B (paralelo)** — @qa Oracle gate VAULT-FIX-01 (handoff já enfileirado por Morpheus)
- [ ] **CC.2** — @architect Aria — ADR-013 "MVP Lean Strategy + Deployment Path"
- [ ] **CC.3** — @ux-design-expert Sati — UX spec MVP single-page (`governance/ux-spec-v1.1.0-MVP-LEAN.md`)
- [ ] **CC.4** — @sm River — rebase stories: VAULT-FIX-01 + OLLAMA-MGR-01 mantidas + criar MVP-LEAN-01 + arquivar/postergar cortes (Backlog Deferred)
- [ ] **CC.5** — @po Keymaker — validar todas stories rebaseadas (delta-revalidation VAULT-FIX-01 + OLLAMA-MGR-01 + validation MVP-LEAN-01)
- [ ] **CC.6+** — @dev Neo — implementar (Oracle gate VAULT-FIX-01 → OLLAMA-MGR-01 → MVP-LEAN-01) — estimativa total 25-35h
- [ ] **Tribunal severo** a cada CC.x: Smith + checkpoint sempre; Sati em CC.3; Oracle em CC.6+
- [ ] **Operator push** (CC.final) APÓS todos os PASS (Oracle + Smith + checkpoint)

---

## 17. Histórico Append-Only

### v1.1.0 — 2026-05-05 (Morgan, Sprint 03 course-correction CC.1A)

**MAJOR bump.** Razão: Eric direção sessão 87 — caminho híbrido enxuto pós-diagnóstico Neo (3 trocas registradas em histórico). Cortes substanciais MVP + roadmap 5 modalidades formalizado + decisão FIES projeto-irmão.

**Mudanças estruturais:**
- ADDED Roadmap 5 modalidades estruturado (Veicular MVP + Bancário Genérico v1.1 + Imobiliária v1.2 + Crédito v1.3) com sequenciamento ROI-otimizado
- ADDED Decisão FIES isolada — projeto-irmão "Revisor FIES" pós-MVP (5 razões técnicas)
- ADDED Backlog Deferred formal — 12 itens com IDs (BL-AUTH-01/02, BL-DELIV-03/04/05, BL-MULTI-UF, BL-ML-LOOP, BL-BACKUP, BL-CONFIG-UI, BL-HITL-ELAB, BL-MONITOR-1378, BL-FIES)
- REMOVED FR-AUTH-01/02/03/04 do MVP → v1.1+
- REMOVED FR-DELIV-02/03/05 do MVP (3 dos 5 deliverables) → v1.1+
- REMOVED FR-RAG-05 multi-UF roadmap explícito → v1.2+ (CLI add_uf como dado)
- REMOVED FR-ML-01..04 → Fase 2
- REMOVED FR-BACKUP-01/02 + FR-RECOVERY-01 → v1.1+
- REMOVED FR-CONFIG-01/02 → v1.1+
- REMOVED FR-MONITOR-01 → v1.1+
- MODIFIED FR-JUIZ-02 painel HITL elaborado → minimal MVP (3 botões + textarea ≥20 chars; bigram diversity DEFERRED)
- MODIFIED Visão (modalidade-única + roadmap)
- MODIFIED NFR-PERF-01 latência ≤180s (vs ≤210s v1.0.2)
- PRESERVED ADR-009 LGPD on-premise (VPS DESCARTADO)
- PRESERVED 4 personas LLM + Decimal-only + FR-TESE-04 validação semântica + ADR-005 HMAC + ADR-006 Tela Adoção CFOAB

**Stories impactadas:**
- VAULT-FIX-01 (Ready for Review) — preservada sem alterações; Keymaker delta-revalidation pós-publish
- OLLAMA-MGR-01 (Ready não iniciada) — preservada sem alterações; Keymaker reconfirma

**Decisões pendentes Eric (não endereçadas nesta versão):**
- Confirmação roadmap sequenciamento (Bancário Genérico v1.1 antes de Imobiliária v1.2 — Morgan optou por ROI-otimizado, Eric pode ajustar)
- Confirmação FIES como projeto-irmão (Morgan recomendou; Eric pode discordar)

---

### v1.0.3 — 2026-05-05 (Morgan, Sprint 02 planning) [PATCH — predecessor preservado]

(Conteúdo preservado em `prd/prd-v1.0.3-DELTA.md` — não duplicar aqui)

### v1.0.2 — 2026-05-01 (Morgan, Sprint 01 etapa 1.0) [PATCH — predecessor preservado]

(Conteúdo preservado em `prd/prd-v1.0.2.md` — não duplicar aqui)

---

*PRD v1.1.0 — Morgan (sessão 87, 2026-05-05) · Sprint 03 course-correction CC.1A · MVP enxuto + Roadmap 5 modalidades · Caminho híbrido pós-diagnóstico Neo · MAJOR bump per prd-governance.md*

— Morgan, planejando o futuro 📊
