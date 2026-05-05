---
type: prd
title: "Revisor Contratual — PRD v1.0.0 (MVP CDC PF Veículos / TJBA)"
project: revisor-contratual
version: "1.0.1"
status: draft
owner: "@pm (Morgan)"
date: "2026-05-01"
predecessor_handoff: "H-S01-E1.0-mor2pm1"
annexes:
  - "prd/integrations-detail-v1.0.md (mapeamento detalhado repo→bloco→FR — etapa 1.1)"
inputs:
  - ".project.yaml"
  - "decisions/architecture-D-lean-2026-05-01.md"
  - "decisions/requirements-extended-2026-05-01.md"
  - "decisions/quality-data-modularity-assurance-2026-05-01.md"
  - "research/competitor-analysis-2026-05-01.md"
  - "research/state-of-the-art-2026-04-30.md"
  - "research/data-sources-external-integrations-2026-05-01.md"
tags:
  - project/revisor-contratual
  - prd
  - mvp
  - legaltech
  - cdc-veiculos
  - tjba
---

# PRD v1.0.0 — Revisor Contratual

| Campo | Valor |
|---|---|
| **Versão** | 1.0.1 (PATCH — anexo de integrações adicionado em 2026-05-01) |
| **Status** | Draft (aguardando tribunal severo: Sati → Smith → checkpoint) |
| **Owner** | @pm (Morgan) |
| **Data** | 2026-05-01 |
| **Diretor** | Eric Claudino |
| **Domínio** | software-dev / sub-domain: legaltech |
| **Sprint** | 01 · Etapa 1.0 |
| **Próximo handoff (após tribunal PASS)** | @architect (Aria) — criar ADRs |

---

## 1. Visão (uma frase)

**Revisor Contratual é um sistema agentic local que analisa contratos de financiamento bancário e produz, em até 3 minutos por contrato, teses jurídicas, contábeis e fiscais com peticionamento e recursos prontos para protocolo, fundamentados em jurisprudência vinculante do STF, STJ e TJ da jurisdição do contrato.**

---

## 2. Objetivo

Entregar a advogados especializados em direito do consumidor bancário uma ferramenta capaz de:

1. **Identificar** ilegalidades, excesso de cobrança, taxas exorbitantes, juros abusivos e enriquecimento ilícito em contratos bancários (foco MVP: CDC PF Veículos).
2. **Construir** teses jurídicas + contábeis + fiscais com fundamentação rastreável a jurisprudência vinculante (peso ≥4) e legislação brasileira vigente (CDC, CC, Lei SFN, MP capitalização).
3. **Produzir** Petição Específica para a demanda judicial cabível e os Recursos Processuais previsíveis, com validação determinística antes da emissão.
4. **Aprender** com outcomes reais (WON/LOST) para reforçar teses vencedoras e descartar abordagens fracas (ML feedback loop em 3 estágios — fase 2+).
5. **Operar 100% local** (LGPD não-negociável) no laptop do usuário ou VPS de baixo custo (R$ 50-150/mês).

---

## 3. Personas

### 3.1 Persona Usuário (externa — quem usa o produto)

**P-USR-01 — Advogado consumerista bancário**
- Atua em ações revisionais de contratos bancários (foco CDC PF Veículos no MVP)
- Cliente final: pessoa física com financiamento veicular cobrando taxa acima da média BACEN
- Volume típico: 1-30 contratos/mês para revisar
- Hardware típico: laptop Windows/Mac de 8-16GB RAM
- Dor que pagamos para resolver: hoje gasta horas calculando Tabela Price + buscando jurisprudência manualmente + redigindo tese; quer entregar petição com base sólida em minutos

### 3.2 Personas Internas (agentes do produto — vontade explícita do Eric, D-04 REVOGADA)

**P-INT-01 — Perito Contábil e Fiscal**
- Expertise: contratos bancários e financiamentos
- Responsabilidade exclusiva: cálculo Tabela Price + SAC + análise de anatocismo + comparação com taxa BACEN da modalidade+data
- Implementação técnica recomendada (Aria decide): função Python + tools deterministícas (Decimal puro, python-bcb)
- Output: ResultadoCalculo Pydantic (Decimal-as-string)

**P-INT-02 — Advogado especialista em direito bancário e contratual**
- Expertise: direito bancário, CDC, jurisprudência STF/STJ/TJ
- Responsabilidade exclusiva: redigir tese fundamentada citando jurisprudência específica recuperada via RAG (citation-grounded — não inventa fontes)
- Implementação técnica recomendada (Aria decide): chamada LLM (Sabia-7B Tier Premium default) com structured output Pydantic + validação cruzada `citations ⊆ docs_recuperados_ids`
- Output: TeseAdvogado Pydantic (com fundamentos invocados, docs citados, confiança 0-1)

**P-INT-03 — Juiz Revisor com vasta experiência em demandas financeiras**
- Expertise: validação de aderência matemática + jurisprudencial
- Responsabilidade exclusiva: 3 checagens determinísticas e quantificadas:
  - C1: divergência entre taxa do contrato e taxa BACEN é estatisticamente material (≥0.5pp ou critério configurável)
  - C2: jurisprudência recuperada tem peso de vinculação ≥4 (Súmula Vinculante, Tema Repetitivo STJ ou Súmula STJ relevante)
  - C3: pelo menos 1 jurisprudência da jurisdição do contrato (UF) ou de tribunal superior (STJ/STF)
- Output: VeredictoJuiz Pydantic com aderência (0-100%) + 3 vereditos: APROVADO_100 | APROVADO_COM_RISCO_HITL | REJEITADO
- Implementação técnica recomendada (Aria decide): função Python pura (não LLM — preserva auditabilidade legal)

**P-INT-04 — Economista (entidades bancárias)** — RESTAURADA por Morpheus em sessão 10
- Expertise: ciclos macroeconômicos, atipicidade de taxas, análise contextual de mercado bancário
- Responsabilidade exclusiva: análise contextual macro do contrato (ex: "taxa do contrato em 03/2024 era 2× a média histórica devido a ciclo de alta da Selic") — útil quando Tema 1378 STJ exigir análise circunstancial
- Implementação técnica recomendada (Aria decide): pode ser tool latente (chamada condicional do Advogado) OU persona LLM separada
- Output: AnaliseMacroEconomica Pydantic
- Justificativa da inclusão: vontade explícita do Eric + alinhamento com cenário de julgamento Tema 1378 STJ que exige análise circunstancial ([Migalhas — Tema 1378 STJ](https://www.migalhas.com.br/depeso/440203/repetitivo-do-stj-e-criterio-de-abusividade-em-contrato-bancario))

> **NOTA para Aria (próxima etapa — ADR):** `.project.yaml` campo `agentes_internos` precisa ser atualizado de 3 para 4 personas refletindo a revogação de D-04. Decidir na ADR a estratégia de implementação técnica de cada persona (LLM vs função Python).

---

## 4. Escopo IN (MVP v1.0)

### 4.1 Modalidade contratual
- Contratos de financiamento de aquisição de veículos para pessoa física (CDC PF Veículos)
- Justificativa: 80% dos financiamentos veiculares usam Tabela Price ([CalculoJurídico](https://calculojuridico.com.br/calculos-bancarios/)), corpus de jurisprudência consolidado, código BACEN específico (SGS 25471 e 20749)

### 4.2 Análises produzidas
- Identificação de ilegalidades (cláusulas abusivas — CDC art. 51)
- Identificação de excesso de cobrança (taxa contratual vs taxa média BACEN para a modalidade+mês)
- Identificação de juros abusivos (alinhado com critério da Súmula 539 STJ + jurisprudência pertinente do tribunal local)
- Detecção de anatocismo matemático (comparação Price vs juros simples)
- Classificação jurídica do anatocismo: SEM_ANATOCISMO | ANATOCISMO_LICITO | ANATOCISMO_QUESTIONAVEL | ANATOCISMO_ILICITO (referência: STF Súmula 121 + STJ Súmula 539 + STJ Tema 247)

### 4.3 Deliverables nomeados (5 — confirmados pelo Eric)
- Relatório Contábil
- Comparativo de Taxas (contrato vs BACEN)
- Parcelas Reais Incontroversas
- Peticionamento Específico (petição inicial revisional)
- Recursos Processuais (NOVO — apelação, embargos declaratórios, agravos cabíveis)

### 4.4 Jurisdição
- UF inicial: Bahia (TJBA + STJ + STF)
- Multi-UF first-class: adicionar nova UF = rodar scraper + reindexar (CLI `add_uf`)

### 4.5 Operação
- Single-user (1 advogado)
- Single-process Python local (sem containers, sem servidores)
- Auth obrigatório (streamlit-authenticator + bcrypt)
- ML feedback loop estágio 1 ativo desde MVP (coleta outcomes — sem fine-tune ainda)

---

## 5. Escopo OUT (NÃO faz parte do MVP v1.0)

| Item | Razão | Quando entra |
|------|-------|--------------|
| Contratos não-bancários (locação, trabalho, civis genéricos) | Foco em revisional bancária | Fase 4+ |
| Modalidades bancárias além de CDC veículos (CDC genérico, imobiliário, cartão rotativo) | Foco MVP | Fase 2 (CDC genérico), Fase 3 (imobiliário, rotativo) |
| Defesa de bancos (lado oposto) | Conflito de propósito; concorrentes (Enter LegalTech) já cobrem | NUNCA |
| Multi-tenant (múltiplos escritórios isolados) | Complexidade desproporcional ao MVP single-user | Fase 3+ |
| Integração com sistemas de gestão jurídica externos (Astrea, ADVbox, Themis) | Validar produto antes | Fase 3 |
| Cobertura nacional automática (todos 27 TJs) | Vault inicial é BA — outros via CLI sob demanda | Fase 2 (top 4 TJs) → Fase 3 (top 8) → Fase 4 (nacional) |
| DataJud (estatística de processos análogos) | Não-crítico para gerar petição | Fase 2 (enriquecimento) |
| ML estágio 2/3 (re-ranking adaptativo + LoRA fine-tune Sabia-7B) | Requer volume de outcomes (≥50 / ≥100) | Fase 2 (estágio 2 ~mês 6-18), Fase 2-3 (estágio 3 ~mês 12+) |
| Geração de pareceres extra-petição (consultivos) | Fora do escopo "ferramenta de revisão para litígio" | Avaliar fase 3 |
| Suporte a cloud LLM como default | Viola princípio 100% local (LGPD) | Apenas opt-in via `LLM_ALLOW_CLOUD_PROVIDER=true` com aviso |

---

## 6. Functional Requirements (FRs)

### 6.1 Auth & Sessão

**FR-AUTH-01 — Autenticação obrigatória por bcrypt**
- Sistema NÃO renderiza nenhuma funcionalidade antes de login bem-sucedido
- Credenciais armazenadas como hash bcrypt em variáveis de ambiente (`AUTH_PASSWORD_HASH`)
- Cookie de sessão com expiração configurável (default 30 dias)
- AC numérico: 100% das tentativas de acesso a páginas internas sem `authentication_status=True` resultam em redirect para tela de login (cobertura de teste obrigatória — pytest)

**FR-AUTH-02 — Logout explícito**
- Botão de logout visível na sidebar; ao clicar, sessão é invalidada e cookie limpo
- AC: clicar logout → próxima requisição exige novo login (verificável por teste E2E)

**FR-AUTH-03 — Audit log de tentativas**
- Toda tentativa de login (sucesso ou falha) registrada em `audit.jsonl` com timestamp, IP, username
- AC: 100% das tentativas registradas, sem perda (verificável por inspeção do JSONL após teste de carga 100 logins)

### 6.2 Upload e Parsing de Contrato

**FR-UPLOAD-01 — Upload de contrato PDF com validação**
- Aceita PDF até 100MB
- Valida magic bytes (`%PDF-`)
- Coleta metadados obrigatórios do usuário: UF do contrato (enum 27 UFs), data de assinatura (ISO 8601, faixa 1986-presente), valor financiado (Decimal opcional)
- AC: PDFs inválidos (não-PDF, criptografados, >100MB, dados de UF/data inválidos) são rejeitados com mensagem clara em <2s

**FR-PARSE-01 — Extração de Markdown do PDF**
- Roteia entre PyMuPDF4LLM (default), Marker (OCR fallback se PDF escaneado), com heurística de detecção de tabelas financeiras
- AC: contratos do golden set (50 contratos sintéticos curados — [DADO-PENDENTE: golden set será produzido pelo @qa em fase de teste]) extraídos com taxa de fidelidade da tabela de amortização ≥95% (validação aritmética: juros + amortização == valor parcela com tolerância R$ 0.01)

**FR-PARSE-02 — Extração de campos contratuais**
- Regex/heurísticas extraem: taxa de juros contratual (% a.m. e % a.a.), prazo (n parcelas), valor financiado, modalidade (VEICULO inferido)
- AC: extração correta em ≥90% dos contratos do golden set (medida em teste); falhas geram pedido de input manual ao usuário

### 6.3 Cálculo Determinístico (Decimal everywhere)

**FR-CALC-01 — Cálculo Tabela Price com Decimal**
- Recebe (capital, taxa_aa, n_parcelas, regime: JUROS_COMPOSTOS|JUROS_SIMPLES)
- Retorna PMT com precisão ≥28 dígitos decimais (`getcontext().prec=28`)
- AC: float é PROIBIDO em qualquer cálculo monetário (CI gate verifica via grep + linter custom — sem `float(...)` em `bloco_engine/ferramentas_calculo/`); 100% bloqueio em violação

**FR-CALC-02 — Geração de tabela de amortização**
- Para cada parcela: saldo_inicial, juros, amortização, valor_parcela, saldo_final (todos Decimal-as-string)
- AC: integridade aritmética em todas as linhas (saldo[n] - amortização[n] = saldo[n+1] com tolerância R$ 0.01)

**FR-CALC-03 — Detecção e classificação de anatocismo**
- Compara PMT regime composto (Tabela Price) vs PMT regime simples para mesmos parâmetros
- Classifica em 4 vereditos com base em STF Súmula 121 + STJ Súmula 539 + STJ Tema 247:
  - SEM_ANATOCISMO (diferença < R$ 0.01)
  - ANATOCISMO_LICITO (SFN + pactuação expressa)
  - ANATOCISMO_QUESTIONAVEL (SFN sem pactuação clara — flagar para HITL)
  - ANATOCISMO_ILICITO (fora SFN)
- AC: classificação rastreável a artigo de súmula/tema citado (campo `sumulas_aplicaveis` no output)

### 6.4 Integração BACEN

**FR-BACEN-01 — Fetch da taxa BACEN para modalidade+data**
- Usa `python-bcb` OData.TaxaJuros (cobre cheque especial, CDC, financiamento veículos, imobiliário)
- Mapping declarativo modalidade → código SGS em `bloco_engine/ferramentas_calculo/codigos_bacen.yaml`
- Códigos confirmados: Selic diária 11, IPCA mensal 433, Veículos PF média mensal SGS 25471 ([BACEN dados abertos](https://dadosabertos.bcb.gov.br/dataset/25471-taxa-media-mensal-de-juros-das-operacoes-de-credito-com-recursos-livres---pessoas-fisicas---a/)), Veículos PF média geral SGS 20749
- Códigos a confirmar pré-implementação: CDC bens não-veículo, imobiliário, cartão rotativo (marcado [DADO-PENDENTE — verificar em https://www3.bcb.gov.br/sgspub/])
- AC: ≥99% das chamadas BACEN com modalidade+data válidas retornam taxa correta em ≤3s (latência 95p)

**FR-BACEN-02 — Cache local + retry**
- Cache `diskcache` com TTL 30 dias (taxas históricas não mudam)
- Retry com tenacity: backoff exponencial 1s→2s→4s→8s→16s, máx 5 tentativas
- AC: 100% de cache hit para mesma (modalidade, mês_ref) na 2ª chamada (verificável por teste); resiliente a 4 falhas consecutivas da API

**FR-BACEN-03 — Fallback "última taxa conhecida"**
- Se API BACEN indisponível após retries esgotados, usa última taxa cacheada da modalidade próxima do mês_ref + alerta visível no Relatório
- AC: petição NÃO é emitida silenciosamente com taxa fallback — sempre alertar o usuário

### 6.5 RAG Jurisprudência (sqlite-vec multi-UF)

**FR-RAG-01 — Indexação de jurisprudência seed**
- Vault inicial: ~3.000 docs (STF Súmulas Vinculantes ~58 + STF Repercussão Geral ~1.300 + STJ Súmulas ~671 + STJ Temas Repetitivos ~1.300 + TJBA acórdãos revisional CDC ~300)
- Schema enriquecido: court_id, binding (bool), peso_vinculacao (1-5), legal_topic_principal (taxonomia controlada), modalidade_relacionada (JSON array), ano_julgamento, ementa, texto_completo, embedding (sqlite-vec BLOB), indexed_at
- Chunking jurídico: recursive splitter com separadores `Art.`, `§`, `Súmula`, `TEMA` + summary-based context enrichment ([arXiv 2510.06999](https://arxiv.org/html/2510.06999v1))
- Deduplication: hash sha256 do texto canonicalizado
- AC: vault populado com ≥2.500 docs antes do MVP ir para usuário (90% do alvo de 3k); cobertura ≥1 doc por UF/STF/STJ + cada legal_topic_principal listado

**FR-RAG-02 — Busca híbrida filtrada por UF**
- Query do Advogado → embedding Legal-BERTimbau-sts-base + BM25 sparse → fusion (RRF)
- Filtro estrito: `WHERE court_id IN ('STF', 'STJ', 'TJ{UF_contrato}') AND binding = 1`
- Top-K configurável (default 10)
- AC: latência ≤500ms por query no vault de 3k docs em laptop alvo (Intel i5-10300H, 16GB RAM)
- AC: ≥95% das queries do golden set RAG (50 queries com gabarito — [DADO-PENDENTE: produzir junto com golden set de contratos]) retornam ≥1 doc relevante (peso_vinculacao ≥3) no top-10

**FR-RAG-03 — Fallback "relaxar binding"**
- Se filtro estrito retorna 0 docs → relaxar para `binding=0 OR 1` e re-buscar
- Se ainda 0 → emitir Relatório de Inviabilidade (não tentar gerar tese sem fundamento)
- AC: 100% dos casos de RAG vazio resultam em Relatório de Inviabilidade (não em tese inventada)

**FR-RAG-04 — Cache de queries frequentes**
- Hash da (query, UF, binding_relax) → resultado cacheado com TTL 24h via diskcache
- AC: economia de ≥80% de embeddings recomputados em queries repetidas (verificável por contagem de calls a `embedder.encode`)

**FR-RAG-05 — CLI multi-UF**
- Comando `python -m bloco_vault.seed.add_uf --uf SP --temas anatocismo,tabela_price` adiciona TJSP ao vault em ≤1h (depende do scraping)
- Comando `python -m bloco_vault.ingestao.pipeline_indexacao --uf SP` reindexa após scrape
- AC: adição de UF não exige mudança de código — apenas execução de CLI

### 6.6 Geração de Tese (Advogado — LLM)

**FR-TESE-01 — Geração citation-grounded**
- LLM (Sabia-7B Tier Premium default; configurável via `LLM_TIER` env: lean | balanced | premium) recebe: ResultadoCalculo + JurisprudenciaItems (top-N do RAG) + few-shot examples de teses vencedoras (curadas)
- Output: TeseAdvogado Pydantic com campos: tese_principal, fundamentos_invocados (lista com id_doc), docs_consultados_ids, docs_efetivamente_citados_ids, confianca (0-1)
- Validação cruzada: `docs_efetivamente_citados_ids ⊆ docs_consultados_ids` (hard-fail se LLM citar fonte fantasma)
- AC: 100% das teses geradas têm ≥3 citações `[id_doc:X]` rastreáveis ao vault; 0% de citações fantasmas (hard-fail blocks)
- AC: latência geração tese ≤180s no laptop alvo com Tier Premium (Sabia-7B Q4 CPU)

**FR-TESE-02 — Fallback Tier configurável**
- `LLM_TIER=premium` (Sabia-7B Q4 ~5GB, ⭐ default escolha do Eric)
- `LLM_TIER=balanced` (Qwen 2.5 7B Q4 ~4.5GB)
- `LLM_TIER=lean` (Qwen 2.5 3B Q4 ~2GB)
- AC: trocar tier requer apenas alterar `.env` e reiniciar Streamlit (zero refactor)

**FR-TESE-03 — Provider abstrato (LLM_PROVIDER)**
- Suporta: `ollama` (default, local), `llamacpp` (embedded local), `openai_compatible` (cloud — opt-in)
- Cloud provider exige `LLM_ALLOW_CLOUD_PROVIDER=true` E gera aviso visível no startup ("ATENÇÃO: provider cloud viola princípio 100% local")
- AC: tentativa de usar cloud sem flag = exceção bloqueante na inicialização

### 6.7 Validação do Juiz Revisor

**FR-JUIZ-01 — 3 checagens determinísticas com scoring**
- C1 (taxa BACEN inferior?): score baseado em divergência percentual; passa se divergência ≥0.5pp
- C2 (jurisprudência vinculante?): score baseado em max(peso_vinculacao) dos docs citados; passa se ≥4
- C3 (jurisdição correta?): score binário; passa se ≥1 doc citado pertence a `{STF, STJ, TJ{UF}}`
- Aderência total = média dos 3 scores * 100
- AC: cálculo de aderência é determinístico e reproduzível (mesma entrada → mesma saída — verificável por teste)

**FR-JUIZ-02 — 3 vereditos**
- Aderência = 100% → APROVADO_100 → emite Petição
- Aderência 70-99% → APROVADO_COM_RISCO_HITL → pausa workflow para decisão humana
- Aderência <70% → REJEITADO → emite Relatório de Inviabilidade (não Petição)
- AC: 0% das petições emitidas com aderência <70% (hard-fail bloqueia emissão)

**FR-JUIZ-03 — Audit log da decisão**
- Cada veredito (incluindo razões C1/C2/C3 + scores + decisão humana se HITL) registrado em `audit.jsonl`
- AC: 100% dos vereditos rastreáveis no audit log (verificável por correlação petition_hash ↔ entry no JSONL)

### 6.8 Deliverables (5 outputs nomeados)

**FR-DELIV-01 — Relatório Contábil**
- Markdown estruturado com: dados do contrato, tabela de amortização gerada (Decimal), divergência matemática vs BACEN, classificação anatocismo, valores incontroversos
- AC: gerado para 100% dos contratos processados (mesmo casos REJEITADO)

**FR-DELIV-02 — Comparativo de Taxas**
- Tabela comparando: taxa contratual (a.a. e a.m.), taxa média BACEN da modalidade no mês de assinatura, divergência absoluta e percentual, série histórica BACEN ±6 meses
- AC: 100% das taxas com fonte explícita (código SGS + URL + data de fetch)

**FR-DELIV-03 — Parcelas Reais Incontroversas**
- Tabela de amortização recalculada com a taxa BACEN do mês como cap (versão "incontroversa" para acordo)
- Diferença total a recompor (R$) entre o pago/cobrado e o incontroverso
- AC: integridade aritmética 100% (validação cruzada saldo/juros/amortização)

**FR-DELIV-04 — Peticionamento Específico**
- Petição inicial revisional em PDF (Jinja2 + WeasyPrint), com hash sha256 para auditoria
- Inclui: qualificação das partes (placeholder configurável), fatos, fundamentos jurídicos com citações `[id_doc:X]`, pedidos, valor da causa
- AC: hash sha256 da petição registrado no audit log; template versionado por git

**FR-DELIV-05 — Recursos Processuais (NOVO)**
- Geração de modelos de recursos cabíveis previsíveis: Apelação Cível, Embargos de Declaração, Agravo de Instrumento, Recurso Especial (quando aplicável)
- Cada recurso com fundamentação rastreável a jurisprudência específica
- Fluxo: usuário seleciona qual recurso após receber decisão adversa → sistema gera com base no contexto da petição original + nova jurisprudência relevante
- AC: cada recurso gerado tem hash próprio + referência ao petition_hash original

### 6.9 ML Feedback Loop (estágio 1 ativo no MVP)

**FR-ML-01 — Outcomes registry (estágio 1 — Cold Start)**
- Cada petição gerada cria entry em `outcomes.db` (SQLite separado em `bloco_learning/outcomes.db`) com status inicial PENDING
- UI Streamlit (página dedicada) permite usuário marcar outcome (WON | LOST | PARTIAL | UNKNOWN | PENDING) + valor revisado + câmara + relator + sentença (opcional)
- AC: 100% das petições geradas têm entry no outcomes.db; UI permite registro em ≤30s por outcome

**FR-ML-02 — Refresh de jurisprudência mensal (alerta crítico)**
- Job mensal monitora STF (novas Súmulas Vinculantes) e STJ (novos Temas Repetitivos)
- Se Tema 1378 STJ for julgado: emite CRITICAL_ALERT no audit log + notifica usuário
- AC: 100% de detecção de novos temas vinculantes (verificável por diff vs cache)

**FR-ML-03 — Adaptive Re-Ranking (estágio 2) — fora do MVP, mas preparar schema**
- Schema do outcomes.db já contempla campos para análise (docs_jurisprudencia_citados, tese_principal, juiz_score)
- Implementação ativa apenas quando volume ≥50 outcomes (estimado ~mês 6)
- AC v1.0: schema preparado; código não-implementado mas referenciado no NOTE para Aria

**FR-ML-04 — LoRA Fine-Tuning (estágio 3) — fora do MVP**
- Quando volume ≥100 outcomes WON: pipeline Unsloth gera Sabia-7B-Revisor-v1
- AC v1.0: pipeline documentado mas não-implementado

### 6.10 Audit Log

**FR-AUDIT-01 — structlog → audit.jsonl append-only**
- Cada evento crítico registrado: login, upload contrato, fetch BACEN, query RAG, geração tese, decisão Juiz, decisão humana HITL, emissão petição
- Formato JSONL com timestamp ISO 8601, evento_tipo, payload estruturado
- AC: arquivo nunca regravado (apenas append); 100% dos eventos críticos com entrada (verificável por correlação ID)

**FR-AUDIT-02 — Audit log inclui Tema 1378 STJ trigger**
- Evento `CRITICAL_JURIS_CHANGE` com payload `{"tema": "1378", "tribunal": "STJ", "detected_at": "..."}` quando refresh detectar julgamento
- AC: este evento dispara também notificação visual no Streamlit no próximo login do usuário

---

## 7. Non-Functional Requirements (NFRs)

### 7.1 Performance

**NFR-PERF-01 — Latência alvo por contrato (end-to-end)**
- ≤180s (3 min) para contrato de até 50 páginas no laptop alvo (Intel i5-10300H 4C/8T, 16GB RAM, sem GPU dedicada para LLM)
- Medido como mediana sobre 20 execuções do golden set
- Fonte do alvo: spec da arquitetura D-LEAN (latência observada Sabia-7B Q4 CPU 60s-3min, conforme `quality-data-modularity-assurance-2026-05-01.md`)

**NFR-PERF-02 — Footprint RAM em uso**
- ≤8GB RAM em uso com Tier Premium (Sabia-7B Q4)
- Medido com `resource.getrusage` em pico de processamento
- Fonte: `.project.yaml` `footprint_alvo.ram_em_uso = "~6 GB (com Sabia-7B Tier L)"`

**NFR-PERF-03 — Latência RAG**
- Query no vault de 3k docs ≤500ms (95p) no laptop alvo
- Medida com test de carga 100 queries simultâneas

### 7.2 LGPD / Compliance

**NFR-LGPD-01 — Zero requisições HTTP a domínios externos não-autorizados**
- Whitelist explícita: `api.bcb.gov.br`, `lexml.gov.br`, `localhost:11434` (Ollama), HuggingFace Hub apenas para download inicial de modelos (não em runtime)
- CI gate verifica via análise estática de imports + scan de URLs hard-coded
- AC: 100% bloqueio em CI se código tentar contactar domínio fora da whitelist

**NFR-LGPD-02 — Retenção de dados de contratos (proposta — humano decide)**
- Contratos uploadados são processados em memória; PDF original é deletado em ≤24h após geração da petição (configurável via `CONTRACT_RETENTION_HOURS`)
- Hash sha256 do contrato é mantido em outcomes.db para referência (não o conteúdo)
- AC v1.0: política implementada com default 24h; usuário pode estender via env var
- > **NOTA para humano (Eric):** confirmar política de retenção. Sugestão Morgan: 24h padrão; se contestado em juízo, advogado deve manter cópia do PDF separadamente.

**NFR-LGPD-03 — Cloud LLM exige opt-in explícito**
- `LLM_PROVIDER=openai_compatible` exige `LLM_ALLOW_CLOUD_PROVIDER=true`
- App emite aviso visual no startup quando cloud provider detectado
- AC: 100% impossível usar cloud por engano (gate na inicialização)

### 7.3 Confiabilidade

**NFR-REL-01 — Resiliência a falhas de BACEN**
- Cache local + retry + fallback "última taxa conhecida" garantem operação mesmo com API down por até 30 dias
- AC: simular API BACEN down e verificar geração de petição com alerta visível

**NFR-REL-02 — Hard-fail em condições inválidas**
- RAG vazio (após relaxamento) → Relatório de Inviabilidade, NUNCA tese inventada
- Citações fantasmas → bloqueio antes da geração da petição
- Aderência <70% → REJEITADO, NUNCA petição emitida
- AC: 0% de petições emitidas em condições inválidas (verificável por testes de borda)

### 7.4 Disponibilidade

**NFR-DISP-01 — Single-user MVP**
- Sistema projetado para 1 usuário concorrente (suficiente para advogado solo)
- Multi-user em fase 3+ (requer FastAPI + Dramatiq — patches localizados em `bloco_workflow/` e novo `bloco_api/`)

### 7.5 Segurança

**NFR-SEC-01 — Auth bcrypt + cookie HMAC**
- Senha em hash bcrypt (cost factor padrão da lib streamlit-authenticator)
- Cookie de sessão assinado com `AUTH_COOKIE_KEY` random
- AC: 100% das tentativas de login com hash incorreto bloqueadas (cobertura de teste)

**NFR-SEC-02 — Sanitização de inputs PDF**
- Magic bytes obrigatório (`%PDF-`)
- Tamanho máx 100MB
- PDFs com macros/JS são processados em sandbox (PyMuPDF nativamente seguro contra exec de macros)
- AC: 100% de PDFs maliciosos detectáveis bloqueados (test set de PDFs com payloads OWASP)

### 7.6 Manutenibilidade

**NFR-MAINT-01 — Modularidade preservada via interfaces Pydantic**
- Todo dado entre blocos transita via Pydantic models em `bloco_contratos/`
- Substituir 1 bloco (ex: sqlite-vec → Qdrant) NÃO exige tocar nos demais
- AC: refactor isolado de `bloco_vault/` em PR separado mantém testes dos demais blocos verdes

**NFR-MAINT-02 — Cobertura de testes mínima**
- ≥80% cobertura em `bloco_engine/ferramentas_calculo/` (cálculos críticos legais)
- ≥70% cobertura em `bloco_workflow/` e `bloco_vault/`
- ≥60% cobertura geral
- AC: CI bloqueia merge abaixo dos thresholds

---

## 8. UX Spec (alto nível — DELEGAR a Sati para detalhamento)

### 8.1 Fluxo principal (1 contrato)

```
1. Login (auth bcrypt)
   ↓
2. Página Upload: usuário escolhe PDF + UF + data de assinatura (form Pydantic-validado)
   ↓
3. Página Processamento: barra de progresso + log dos passos (parsing → BACEN → RAG → tese → juiz)
   ↓ [se Juiz APROVADO_100]
4a. Página Resultado: download dos 5 deliverables (Relatório Contábil, Comparativo, Parcelas Incontroversas, Petição PDF, Recursos modelos)
   ↓ [se Juiz APROVADO_COM_RISCO_HITL]
4b. Página HITL: mostra aderência calculada + razões de risco + 3 botões (Aprovar com Risco, Solicitar Recálculo, Abortar e Gerar Inviabilidade) + textarea justificativa obrigatória (≥20 chars)
   ↓ [se Juiz REJEITADO]
4c. Página Inviabilidade: relatório explicando por que aderência <70% (qual checagem falhou) + sugestões
   ↓
5. Página Outcomes (acessível sempre): lista petições já geradas, marcar WON/LOST/etc + dados processuais
```

### 8.2 Estados de cada página (a detalhar com Sati)

- Vazio: "Nenhum contrato processado ainda. Faça upload."
- Loading: barra de progresso com nome da etapa atual (ex: "Consultando BACEN — taxa veículos PF mar/2024...")
- Erro: mensagem amigável + opção de tentar novamente + log completo expansível
- Sucesso: download buttons + audit ID copiável

### 8.3 Microcopy (a detalhar com Sati)

- Tom: profissional jurídico, direto, sem jargão técnico de ML/IA
- Não usar termos como "LLM", "embeddings", "RAG" no UI — substituir por "análise inteligente", "busca jurisprudencial", etc.
- Erros técnicos traduzidos: "Não foi possível consultar a taxa BACEN do mês solicitado. Tente novamente em alguns minutos."

> **HANDOFF NOTA para Sati (na próxima etapa do tribunal severo):** UX spec aqui é alto nível. Refinar: estados de cada página com transições, microcopy completo (especialmente Painel HITL — payload tipado de divergência), a11y (contraste, navegação por teclado, screen reader nas tabelas de amortização), consistência visual.

---

## 9. Dependências

### 9.1 Bibliotecas Python
Conforme shopping list canônica em `decisions/requirements-extended-2026-05-01.md` seção "📦 Bibliotecas Python (`pyproject.toml`)" — referência completa lá. Resumo das críticas:
- streamlit ≥1.40, streamlit-authenticator ≥0.3.3
- langchain ≥0.3, langgraph ≥0.2, langchain-ollama ≥0.2
- sqlite-vec ≥0.1, sentence-transformers ≥3.0, rank_bm25 ≥0.2
- pymupdf4llm ≥0.0.12, marker-pdf ≥0.2 (opcional)
- python-bcb ≥0.5
- pydantic ≥2.8, tenacity ≥9.0, diskcache ≥5.6, structlog ≥24.4
- jinja2 ≥3.1, weasyprint ≥63.0

### 9.2 Modelos
- LLM default (Tier Premium): **Sabia-7B Q4** ([TheBloke/sabia-7B-GGUF](https://huggingface.co/TheBloke/sabia-7B-GGUF))
- Embeddings: **rufimelo/Legal-BERTimbau-sts-base** ([HF](https://huggingface.co/rufimelo/Legal-BERTimbau-base))

### 9.3 APIs externas (whitelist LGPD)
- BACEN OData/SGS — `https://api.bcb.gov.br/dados/serie/...` (sem auth)
- LexML — `https://www.lexml.gov.br/` (edge cases, sem auth)
- HuggingFace Hub — APENAS download inicial de modelos (não runtime)

### 9.4 Vault seed (rodar 1× pré-MVP)
- STF Súmulas Vinculantes (~58 docs)
- STF Repercussão Geral (~1.300 teses) — [portal.stf.jus.br/repercussaogeral/teses](https://portal.stf.jus.br/repercussaogeral/teses.asp)
- STJ Súmulas (~671) — [stj.jus.br/sites/portalp/Jurisprudencia/Sumulas](https://www.stj.jus.br/sites/portalp/Jurisprudencia/Sumulas)
- STJ Temas Repetitivos (~1.300) — [stj.jus.br/repetitivos/temas_repetitivos](https://www.stj.jus.br/repetitivos/temas_repetitivos)
- TJBA acórdãos revisional CDC (~300 — scraping + curadoria amostral pelo usuário)

### 9.5 Legislação pré-cache (4 leis em JSON estruturado)
- CDC — Lei 8.078/90
- Código Civil — Lei 10.406/02
- Lei do SFN — Lei 4.595/64
- MP 2.170-36/2001 (capitalização infra-anual)

### 9.6 Mapeamento Detalhado de Integrações por Repositório

Ver anexo canônico: **`prd/integrations-detail-v1.0.md`**

Sumário rápido (referência ao anexo para detalhes):

| Repositório | Status | Blocos consumidores | FRs afetados |
|-------------|--------|---------------------|--------------|
| topics/datajud (CNJ) | 🟡 referência + wrapper Python (fase 2) | bloco_engine, bloco_learning | FR-ML-02, FR-DATAJUD-01* |
| orgs/lexml (federal) | 🟡 consumo HTTP + cache one-shot | bloco_vault, bloco_engine | FR-RAG-01, FR-DELIV-04, FR-LEX-01* |
| projeto-v3l0z | 🟢 referência arquitetural (sem licença → não copiar) | bloco_workflow, bloco_engine | nenhum FR direto |
| abjur/tidyML | 🔴 descartar (R abandonado); aproveitar conceito ABJ em fase 2 | nenhum | nenhum |
| orgs/bacen | 🔴 descartar (só Pix) — usar `python-bcb` (real) | bloco_engine | FR-BACEN-01/02/03 |
| STJ Concursos | ⚠️ URL incorreta — substituir por STJ Súmulas + Temas Repetitivos + STF SV + STF Repercussão Geral | bloco_vault, bloco_audit, bloco_learning | FR-RAG-01, FR-ML-02, FR-AUDIT-02 |

**\* FR-DATAJUD-01 e FR-LEX-01** são FRs novos sugeridos para PRD v1.1.0 (após Aria avaliar viabilidade).

---

## 10. Riscos e Mitigações

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| **R-01** | Tema 1378 STJ é julgado durante o MVP exigindo "análise circunstancial" como critério único | Média (julgamento pendente desde 09/09/2025) | **CRÍTICO** — pode reverter design | Persona Economista já restaurada (P-INT-04); FR-AUDIT-02 monitora julgamento; estrutura pronta para Economista virar persona ativa em ≤1 sprint |
| **R-02** | Selic atual baixa (~10-12% em 2026) reduz divergência matemática vs taxas contratuais → menos teses de revisão viáveis | Alta | Médio | Foco em contratos antigos (Selic alta 2022-2024 ainda gerando contratos vigentes); ampliar escopo para "abusividade absoluta" alinhada com Súmula 539 STJ |
| **R-03** | Portais STF/STJ mudam layout HTML → scrapers quebram | Alta (típico 2-3×/ano) | Alto (vault não atualiza) | Pipeline mensal de teste de scraping + alerta automatizado; backup de schema XPath versionado em git; fallback manual via script ad-hoc |
| **R-04** | Volume de outcomes (registro humano) abaixo do necessário (<50 em 12 meses) → ML estágio 2 não inicia | Média | Médio (estágio 2 atrasa) | UI fluida em ≤30s/outcome; lembrete visual de outcomes pendentes; integração futura com sistemas de gestão jurídica |
| **R-05** | Sabia-7B Q4 latência CPU (60s-3min) frustra usuário em uso intensivo | Média | Médio | Tiers configuráveis (M/S como fallback); upgrade para GPU local ou cloud GPU on-demand documentado |
| **R-06** | LGPD violation se algum modelo/embedding cair em cloud por engano | Baixa | **CRÍTICO** | NFR-LGPD-01 + CI gate de whitelist; opt-in explícito para cloud LLM; auditoria recorrente de imports |
| **R-07** | Citações fantasmas do LLM (alucinação) escapam validação cruzada | Baixa | Alto | FR-TESE-01 hard-fail em `citations ⊄ docs_recuperados`; teste de regressão contínuo |
| **R-08** | Vault de jurisprudência envelhece sem refresh → tese cita súmula superseded | Média | Alto | FR-ML-02 refresh mensal automatizado; campo `superseded_by` no schema permite flagar |
| **R-09** | Concorrente (CJ, JusCalc) lança feature de IA generativa antes do MVP | Média | Médio | Diferencial defensável: integração end-to-end + auditabilidade Juiz IA + 100% local LGPD; ainda assim — acelerar MVP |
| **R-10** | Mercado real de revisional veículos em queda (Selic baixa + Súmula 539 reduzem demanda) | Média (sinalizada no competitor-analysis) | Alto | Validação qualitativa com 3-5 advogados-piloto antes de Phase 2; pivô para CDC genérico ou imobiliário se confirmado |

---

## 11. Métricas de Sucesso (KPIs)

Conforme `decisions/requirements-extended-2026-05-01.md` seção "ML feedback loop" — adotados como metas oficiais do produto:

| KPI | Meta MVP | Alerta |
|-----|----------|--------|
| Win rate (WON / WON+LOST) | ≥60% após mês 6 | <40% em 3 meses → revisar tese padrão |
| Correlação juiz_score ↔ outcome | ≥0.5 (Pearson) | <0.3 → recalibrar Juiz |
| Tempo até outcome registrado | mediana ≤120 dias | >180 dias → ajustar reminders |
| Volume de outcomes registrados | ≥80% das petições marcadas em 90 dias | <50% → revisar UX da página de outcomes |
| Latência por contrato | mediana ≤180s | >300s consistente → considerar upgrade tier ou hardware |
| Cobertura de citações vinculantes | ≥3 citações peso ≥4 por petição | <2 → ampliar vault |

---

## 12. Roadmap (referência — escopo formal apenas v1.0)

| Fase | Conteúdo | Estimativa |
|------|----------|------------|
| **Phase 0** | Research + decisões + PRD (esta etapa) | ✅ Concluída |
| **Phase 1 (MVP)** | Implementação dos 7 blocos + vault TJBA + 5 deliverables + auth + audit | 6-10 semanas |
| **Phase 2** | DataJud (estatística), CDC genérico, ML estágio 2 (adaptive ranking), TJSP/TJMG/TJRJ | 3-6 meses pós-MVP |
| **Phase 3** | LoRA fine-tune Sabia (estágio 3), multi-tenant, integração sistemas externos | 6-12 meses pós-MVP |
| **Phase 4** | Cobertura nacional, modalidade imobiliário, internacionalização Mercosul | 12+ meses |

---

## 13. Notas Críticas para Aria (próximo agente — ADR)

1. **Atualizar `.project.yaml`** campo `agentes_internos`: lista deve refletir 4 personas (não 3). D-04 foi REVOGADA por Morpheus na sessão 10.
2. **Atualizar `.project.yaml`** campo `description`: corrigir "Qwen 2.5 3B" para "Sabia-7B Tier Premium configurável".
3. **Decidir na ADR a estratégia técnica de cada persona** — quais viram função Python pura (determinístico) vs chamada LLM. Recomendação Morgan: Juiz 100% Python; Perito majoritariamente Python com LLM opcional para análise complexa; Advogado LLM obrigatório; Economista LLM condicional (ativada por flag/feature ou pelo Tema 1378 STJ).
4. **Decidir threshold de aderência** (FR-JUIZ-02): 70%/100% é proposta inicial — pode ser refinado via dados reais.
5. **Decidir golden set obrigatório** (referenciado em FRs como [DADO-PENDENTE]): @qa deve produzir golden set de ≥50 contratos sintéticos curados antes do MVP fechar — talvez seja epic separado.
6. **Decidir códigos BACEN específicos** (FR-BACEN-01): confirmar códigos para CDC bens não-veículo, imobiliário, cartão rotativo no portal SGS antes da implementação.
7. **Política de retenção LGPD** (NFR-LGPD-02): 24h é proposta — precisa confirmação humana.

---

## 14. Itens [DADO-PENDENTE] (não inventados — exigem confirmação antes de implementação)

| ID | Item | Quem resolve | Quando |
|----|------|--------------|--------|
| DP-01 | Golden set de ≥50 contratos sintéticos para validação | @qa | Antes de fechamento MVP |
| DP-02 | Golden set de ≥50 queries RAG com gabarito | @qa | Antes de fechamento MVP |
| DP-03 | Códigos SGS BACEN para CDC bens não-veículo, imobiliário, cartão rotativo | @dev (consulta SGS portal) | Implementação FR-BACEN-01 |
| DP-04 | Threshold final de aderência do Juiz (70/100%) | @architect (Aria) na ADR | Próxima etapa |
| DP-05 | Política de retenção de PDFs de contratos (24h proposta) | Humano (Eric) | Antes de produção |
| DP-06 | Métricas baseline para KPIs (win rate inicial) | @qa após mês 3 de uso | Iterativo |

---

## 15. Change Log (append-only)

### v1.0.1 — 2026-05-01 (Morgan) — PATCH
- **ADDED:** Seção 9.6 — Mapeamento Detalhado de Integrações por Repositório (sumário; detalhes em anexo)
- **ADDED:** Anexo `prd/integrations-detail-v1.0.md` — mapeamento completo dos 6 repos do Eric → blocos → FRs específicos do PRD
- **ADDED:** `research/data-sources-external-integrations-2026-05-01.md` na lista de inputs (era source implícito)
- **PROPOSED:** 2 FRs novos para PRD v1.1.0 — FR-DATAJUD-01 (busca processos análogos via DataJud) e FR-LEX-01 (resolução automática de remissões legais via LexML cache)
- **CLARIFIED:** Repos `abjur/tidyML`, `orgs/bacen` e `projeto-v3l0z` formalmente classificados como "descartar uso direto" / "referência conceitual" sem impacto em FRs do v1.0
- **CONFIRMED:** URL STJ Concursos foi enviada por engano — URLs corretas (STJ Súmulas, Temas Repetitivos, Pesquisa Pronta, scon.stj.jus.br + STF SV + STF Repercussão Geral) são as fontes reais já contempladas em FR-RAG-01

### v1.0.0 — 2026-05-01 (Morgan)
- **CREATED:** PRD inicial baseado em handoff H-S01-E1.0-mor2pm1 do Morpheus
- **CONFIRMED:** 4 personas internas (D-04 revogada por Morpheus na sessão 10)
- **ADDED:** FR-DELIV-05 (Recursos Processuais — escopo NOVO confirmado por Eric)
- **CONFIRMED:** Tier Premium Sabia-7B Q4 como LLM default (escolha Eric sessão 7)
- **CONFIRMED:** UF inicial = BA (escolha Eric sessão 5/8)
- **ADOPTED:** Multi-UF first-class via CLI `add_uf`
- **ADOPTED:** Auth obrigatório via streamlit-authenticator + bcrypt
- **ADOPTED:** ML feedback loop estágio 1 ativo desde MVP (estágios 2/3 documentados mas não implementados)
- **REFERENCED:** Shopping list canônica em decisions/requirements-extended-2026-05-01.md
- **MARKED:** 6 itens [DADO-PENDENTE] para resolução antes de implementação

---

*Morgan, planejando o futuro com critérios numéricos rastreáveis 📊*
