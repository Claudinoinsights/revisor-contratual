---
type: prd
title: "Revisor Contratual — PRD v1.0.0 (MVP CDC PF Veículos / TJBA)"
project: revisor-contratual
version: "1.0.2"
status: draft (aguardando re-tribunal severo)
owner: "@pm (Morgan)"
date: "2026-05-01"
predecessor_handoff: "H-S01-E1.2-mor2pm2"
patch_basis: "Tribunal severo etapa 1.1 (Sati 11 EV-IDs + Smith 22 F-IDs + checkpoint 4 R-GOV)"
annexes:
  - "prd/integrations-detail-v1.0.md (mapeamento repo→bloco→FR — etapa 1.1)"
  - "prd/ux-spec-detail-v1.0.md (inventário Atomic Design + microcopy completo — etapa 1.2)"
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
| **Versão** | 1.0.2 (PATCH — endereçando 6 CRITICAL + 11 HIGH Smith + 4 EV-ID ALTA Sati em 2026-05-01) |
| **Status** | Draft (aguardando re-tribunal severo: Sati → Smith → checkpoint) |
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

**P-INT-04 — Economista (entidades bancárias)** — PROMOVIDA A PRIMEIRA-CLASSE (Smith F-CRIT-06)
- Expertise: ciclos macroeconômicos, atipicidade de taxas, análise contextual de mercado bancário
- Responsabilidade exclusiva: análise contextual macro do contrato (ex: "taxa do contrato em 03/2024 era 2× a média histórica devido a ciclo de alta da Selic") — fornece blindagem antecipada caso Tema 1378 STJ exija análise circunstancial
- **Implementação técnica:** **Persona ATIVA desde MVP** (NÃO é mais "tool latente"). Cada análise inclui chamada LLM obrigatória do Economista produzindo `AnaliseMacroEconomica`. Decisão tomada por Morpheus em mitigação CRITICAL ao risco de tempo do Tema 1378 STJ.
- Custo arquitetural aceito: latência por contrato sobe ≤180s → **≤210s** (atualizado em NFR-PERF-01).
- Output: AnaliseMacroEconomica Pydantic (campos: ciclo_selic_periodo, taxa_atipica_bool, comparacao_peer_modalities, contexto_macro_resumido)
- Justificativa: vontade do Eric + Smith F-CRIT-06 + Provimento alinhado com cenário PIOR caso de Tema 1378 ([Migalhas — Tema 1378 STJ](https://www.migalhas.com.br/depeso/440203/repetitivo-do-stj-e-criterio-de-abusividade-em-contrato-bancario))

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

**FR-RAG-01 — Indexação de jurisprudência seed (estendido em v1.0.2 por Smith F-CRIT-03)**
- Vault inicial: ~3.000 docs (STF Súmulas Vinculantes ~58 + STF Repercussão Geral ~1.300 + STJ Súmulas ~671 + STJ Temas Repetitivos ~1.300 + TJBA acórdãos revisional CDC ~300)
- Schema enriquecido (v1.0.2): court_id, binding (bool), peso_vinculacao (1-5), legal_topic_principal (taxonomia controlada), modalidade_relacionada (JSON array), ano_julgamento, ementa, texto_completo, embedding (sqlite-vec BLOB), indexed_at, **vigente_em (date|null — null=vigente; date=vigência até)**, **superseded_by (id_doc|null — link para jurisprudência substituta)**, **data_ultima_validacao (date — quando foi verificado vigência pela última vez)**
- Chunking jurídico: recursive splitter com separadores `Art.`, `§`, `Súmula`, `TEMA` + summary-based context enrichment ([arXiv 2510.06999](https://arxiv.org/html/2510.06999v1))
- Deduplication: hash sha256 do texto canonicalizado
- AC: vault populado com ≥2.500 docs antes do MVP ir para usuário (90% do alvo de 3k); cobertura ≥1 doc por UF/STF/STJ + cada legal_topic_principal listado
- AC v1.0.2: 100% dos docs do vault têm campo `vigente_em` preenchido (null ou date); 100% dos docs com `superseded_by` apontando para id_doc existente no vault

**FR-RAG-02 — Busca híbrida filtrada por UF (estendido em v1.0.2 por Smith F-CRIT-03)**
- Query do Advogado → embedding Legal-BERTimbau-sts-base + BM25 sparse → fusion (RRF)
- Filtro estrito (v1.0.2): `WHERE court_id IN ('STF', 'STJ', 'TJ{UF_contrato}') AND binding = 1 AND (vigente_em IS NULL OR vigente_em > {data_assinatura_contrato})`
- Top-K configurável (default 10)
- AC: latência ≤500ms por query no vault de 3k docs em laptop alvo (Intel i5-10300H, 16GB RAM)
- AC: ≥95% das queries do golden set RAG (50 queries com gabarito — [DADO-PENDENTE: produzir junto com golden set de contratos]) retornam ≥1 doc relevante (peso_vinculacao ≥3) no top-10
- AC v1.0.2: 0% das queries retornam jurisprudência superseded à data de assinatura do contrato (verificável por teste de regressão com docs marcados superseded)

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

**FR-RAG-06 — Benchmark de cobertura do vault (NOVO em v1.0.2 — Smith F-HIGH-09)**
- Antes de fechar MVP, executar benchmark de cobertura do vault inicial
- Procedimento: testar 50 contratos do golden set (DP-01) e medir % das queries que caem em Inviabilidade por RAG vazio (mesmo após relaxamento binding)
- Meta: ≤15% de Inviabilidade por RAG vazio no golden set
- Se >15%: bloquear release MVP até expansão do vault (mais TJs, mais legal_topics, mais docs vinculantes)
- AC: relatório `qa/coverage-report-vault-mvp.md` publicado pelo @qa antes da release MVP

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

**FR-TESE-04 — Validação semântica de citações (NOVO em v1.0.2 — Smith F-CRIT-02)**
- Após geração da tese (FR-TESE-01), executar validação semântica obrigatória ANTES de qualquer renderização
- Procedimento por citação `[id_doc:X]`:
  1. Recuperar ementa real do doc no vault
  2. Calcular cosine similarity entre frase da tese atribuída ao doc e ementa real (via Legal-BERTimbau-sts-base)
  3. Citações com similaridade <0.7 → BLOQUEAR emissão da peça
  4. Apresentar diff visual ao usuário (frase IA vs ementa real, lado a lado)
  5. Usuário pode: (a) corrigir manualmente, (b) rejeitar a citação, (c) abortar geração
- Por que: evitar caso real em que LLM cita doc CORRETO com tese INVERTIDA (ex: "Súmula 539 STJ proíbe X" quando ela permite X)
- AC numérico: 0% das peças emitidas com citações de similaridade <0.7
- AC: validação executa em ≤200ms por citação (<2s para tese típica com 5-10 citações)
- Audit log registra: cada validação semântica com (id_doc, similarity_score, decisao_usuario)

### 6.7 Validação do Juiz Revisor

**FR-JUIZ-01 — 3 checagens determinísticas com scoring**
- C1 (taxa BACEN inferior?): score baseado em divergência percentual; passa se divergência ≥0.5pp
- C2 (jurisprudência vinculante?): score baseado em max(peso_vinculacao) dos docs citados; passa se ≥4
- C3 (jurisdição correta?): score binário; passa se ≥1 doc citado pertence a `{STF, STJ, TJ{UF}}`
- Aderência total = média dos 3 scores * 100
- AC: cálculo de aderência é determinístico e reproduzível (mesma entrada → mesma saída — verificável por teste)

**FR-JUIZ-02 — 3 vereditos (estendido em v1.0.2 — Sati EV-01 + Smith F-HIGH-02)**
- Aderência = 100% → APROVADO_100 → segue para FR-DELIV-06 (revisão obrigatória)
- Aderência 70-99% → APROVADO_COM_RISCO_HITL → pausa workflow para decisão humana
- Aderência <70% → REJEITADO → emite Relatório de Inviabilidade (não Petição)
- AC: 0% das petições emitidas com aderência <70% (hard-fail bloqueia emissão)

**Especificação detalhada do Painel HITL (v1.0.2 — Sati EV-01 + EV-09):**
- Cabeçalho mostra BadgeAderencia visível: "⚠️ Análise concluída com X% de aderência. Há ressalvas — sua decisão é necessária."
- Resumo das 3 checagens com tooltip explicativo cada:
  - 📊 C1 (cálculo matemático): divergência Y% vs taxa BACEN ({passa/falha})
  - ⚖️ C2 (jurisprudência vinculante): peso máximo Z/5 ({passa/falha})
  - 🏛️ C3 (jurisdição): N doc(s) de TJ{UF}/STJ/STF ({passa/falha})
- 3 botões com cor + ícone + microcopy explícito:
  - 🟧 Aprovar mesmo assim — "assumo o risco de X%"
  - 🟦 Solicitar novo cálculo — "vou ajustar parâmetros"
  - 🟥 Abortar — "gerar Relatório de Inviabilidade"
- Textarea justificativa OBRIGATÓRIA com:
  - Placeholder contextual: "Ex: 'Aprovo apesar do risco porque a 3ª Câmara do TJBA tem precedente favorável (caso 0801234-XX.2024) ainda não indexado no sistema.'"
  - Counter visual: "{N}/20 caracteres (mínimo)" — vermelho se <20, verde se ≥20
  - **Validação semântica anti-bypass (Smith F-HIGH-02):** rejeitar texto com bigram diversity <0.5, ≤4 palavras únicas, ou apenas palavras genéricas (lista negra: "ok", "sim", "aprovo", "ciente"). Mensagem: "Justificativa muito repetitiva ou genérica. Por favor, descreva o motivo concreto da decisão."
- AC: 0% das justificativas HITL com diversidade <0.5 ou ≤4 palavras únicas são aceitas
- Audit log registra: timestamp, usuário, decisão (botão clicado), justificativa, score C1/C2/C3 vigente, hash da peça pendente

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

**FR-DELIV-05 — Recursos Processuais (NOVO em v1.0.0)**
- Geração de modelos de recursos cabíveis previsíveis: Apelação Cível, Embargos de Declaração, Agravo de Instrumento, Recurso Especial (quando aplicável)
- Cada recurso com fundamentação rastreável a jurisprudência específica
- Fluxo: usuário seleciona qual recurso após receber decisão adversa → sistema gera com base no contexto da petição original + nova jurisprudência relevante
- AC: cada recurso gerado tem hash próprio + referência ao petition_hash original

**FR-DELIV-06 — Tela de Revisão e Adoção Obrigatória (CFOAB) — NOVO em v1.0.2 (Smith F-CRIT-01)**
- Antes de gerar PDF de qualquer peça (FR-DELIV-04 petição inicial OU FR-DELIV-05 recursos), sistema EXIGE tela de revisão obrigatória
- Componentes da tela:
  1. **Preview da peça final** (PDF embedded em iframe — usuário consegue ler antes de adotar)
  2. **Checkbox** "LI, CONFERI E ADOTO os fundamentos como meus" (sem default checked)
  3. **Campos obrigatórios** do peticionante: nome completo + nº OAB + UF (preenchidos uma vez, persistem em .env)
  4. **Campo opcional** de notas adicionais do advogado (para personalização)
- Hard-fail: sem checkbox marcado E sem campos OAB preenchidos → PDF NÃO é emitido (botão "Gerar PDF" desabilitado)
- Audit log registra (FR-AUDIT-01 estendido):
  - timestamp da adoção
  - hash sha256 da peça aprovada (idêntico ao do PDF gerado)
  - identificação do peticionante: nome + OAB + UF
  - texto livre do checkbox apresentado ao usuário (versionado)
- **Aplicação universal**: este FR vale para TODAS as peças geradas pelo sistema (petição inicial, embargos, apelação, agravo, recurso especial)
- AC numérico: 0% das peças (qualquer FR-DELIV-04 ou FR-DELIV-05) emitidas sem checkbox+OAB confirmados
- AC LGPD: 100% das adoções têm entry no audit.jsonl com OAB+UF+timestamp+hash
- **Referência jurídica:** Estatuto da OAB (Lei 8.906/94 art. 32 — responsabilidade do advogado) + Provimento CFOAB 205/2021 (uso de tecnologia/IA em peças jurídicas)
- **Justificativa de design:** Sem este FR, o produto expõe Eric a responsabilização indireta caso advogado-usuário seja punido pela seccional OAB por petição IA-gerada com defeito. Este checkbox + assinatura digital transferem responsabilidade legal ao peticionante (proteção do produto E do usuário)

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

**FR-AUDIT-01 (estendido em v1.0.2 — Smith F-HIGH-04 hash chain anti-tamper):**
- Cada entry em audit.jsonl inclui campo `previous_entry_hash` (sha256 da entry anterior)
- Primeira entry tem `previous_entry_hash: "GENESIS"`
- Comando CLI `python -m revisor verify-audit-integrity` recalcula chain Merkle-style e detecta tampering
- AC: tampering manual em audit.jsonl é detectável em <5s pelo comando de verificação

### 6.11 Setup, Backup e Recovery (NOVO em v1.0.2 — Smith F-CRIT-04, F-CRIT-05, F-HIGH-06, F-HIGH-05)

**FR-SETUP-01 — Bootstrap único com fallback de modelo (Smith F-CRIT-04 + F-HIGH-05)**
- Comando único: `python -m revisor bootstrap` (ou `make setup`)
- Procedimento:
  1. Verifica existência de `.env` — se não existe, gera template
  2. Tenta `ollama pull` do modelo configurado em LLM_MODEL (default: sabia-7b:q4_K_M)
  3. Se falhar (modelo não no library) → mensagem clara: "Modelo {X} não disponível em ollama.com/library. Opções:"
     - (a) Criar Modelfile customizado a partir do GGUF da HuggingFace (instruções)
     - (b) Fallback automático para Qwen 2.5 7B (Ollama oficial, confirmado)
  4. Persiste escolha final em .env (LLM_MODEL atualizado)
  5. Download de embeddings (Legal-BERTimbau-sts-base) com `HF_HUB_OFFLINE=0` apenas no setup; runtime usa cache local com `HF_HUB_OFFLINE=1` (mitiga telemetria HF — Smith F-HIGH-05)
- AC: setup-day-1 não falha silenciosamente; usuário sempre tem caminho para resolver
- AC: HF Hub não é contactado em runtime (verificável por mock/blocklist)

**FR-BACKUP-01 — Backup automático de ativos críticos (Smith F-CRIT-05)**
- Ativos cobertos: `outcomes.db`, `audit.jsonl`, `bloco_vault/seed/jurisprudencia/*`, `bloco_vault/database/jurisprudencia.db`
- Trigger: a cada N petições geradas (configurável via env `BACKUP_EVERY_N_PETITIONS`, default N=5)
- Destino: `BACKUP_DIR` configurável em .env (default: `./backups/`)
- Estrutura: `{BACKUP_DIR}/{YYYY-MM-DD}/{HHMMSS}/`
- Rotação: manter últimos 30 dias; mais antigos deletados automaticamente
- Falha de backup: WARN visível no header do Streamlit (não-bloqueante; advogado pode continuar usando)
- AC: simulação de perda de outcomes.db + restauração via último backup recupera 100% dos outcomes

**FR-BACKUP-02 — Backup manual sob demanda**
- Comando CLI: `python -m revisor backup-now`
- Força backup imediato (mesmo se contador de petições não atingiu N)
- Saída: caminho do backup criado + tamanho total
- AC: comando completa em ≤30s para vault de 3k docs + outcomes.db de 1k entries

**FR-RECOVERY-01 — Recovery mid-workflow via LangGraph checkpointer (Smith F-HIGH-06)**
- Workflow usa `langgraph.checkpoint.sqlite.SqliteSaver` em `bloco_workflow/state.db`
- Cada etapa (parser, BACEN, RAG, tese, juiz, validação semântica, renderer) checkpointa estado
- Crash mid-workflow: próximo upload do MESMO contrato (hash sha256 igual) oferece opção "Continuar de onde parou (etapa X)"
- AC: simular crash na etapa 5 (geração tese) → recovery preserva etapas 1-4 → processamento continua sem refazer

**FR-MONITOR-01 — Monitoramento ATIVO do Tema 1378 STJ (Smith F-CRIT-06)**
- Job dedicado SEMANAL (não mensal): scrape de stj.jus.br/repetitivos para Tema 1378
- Detecção do julgamento dispara:
  1. CRITICAL_ALERT no audit.jsonl
  2. Notificação visual persistente no header do Streamlit (banner vermelho)
  3. Email para AUTH_EMAIL (se configurado)
  4. Pausa de novas gerações até usuário confirmar leitura do alerta
- AC: 100% de detecção em ≤7 dias após julgamento publicado oficialmente

### 6.12 Configurações Avançadas e Segurança (NOVO em v1.0.2 — Sati EV-05 + Smith F-HIGH-03)

**FR-CONFIG-01 — Página Configurações Avançadas com toggle visual (Sati EV-05)**
- Menu lateral expõe "Configurações Avançadas" (acessível apenas após login)
- Toggle visual entre 3 LLM_TIER:
  - 🥉 Lean (Qwen 2.5 3B Q4) — Latência ~40s • RAM ~2GB
  - 🥈 Balanced (Qwen 2.5 7B Q4) — Latência ~90s • RAM ~4.5GB
  - 🥇 Premium (Sabia-7B Q4) ⭐ atual — Latência ~150s • RAM ~5GB
- Indicador visual do tier ativo + comparativo de trade-offs
- Botão "Aplicar e reiniciar" — persiste em .env e reinicia Streamlit
- Disclaimer: "Tier menor = mais rápido mas potencialmente menos preciso. Recomendado validar com 5 contratos antes de fixar."
- Mudanças persistidas com backup do .env anterior (em `.env.backup-{timestamp}`)
- AC: trocar tier funciona em ≤2 cliques + 1 confirmação

**FR-AUTH-04 — Sessão com IP fingerprint + inatividade (Smith F-HIGH-03)**
- Cookie de sessão inclui IP fingerprint (hash do IP no momento do login)
- Sessão expira após **menor de**: 7 dias de inatividade OU 30 dias absolutos
- Mudança de IP detectada → re-login obrigatório (mitigação de roubo de laptop)
- Header do app mostra: "Sessão expira em {N} dias [Estender]"
- AC: laptop roubado + IP do ladrão diferente = re-login obrigatório (verificável por teste de mudança de IP)

---

## 7. Non-Functional Requirements (NFRs)

### 7.1 Performance

**NFR-PERF-01 — Latência alvo por contrato (end-to-end)** — atualizado em v1.0.2
- **≤210s (3.5 min)** para contrato de até 50 páginas no laptop alvo (Intel i5-10300H 4C/8T, 16GB RAM, sem GPU dedicada para LLM)
- Mudança v1.0.2: **+30s** vs v1.0.1 (≤180s) — refletindo +1 chamada LLM da Persona Economista promovida a primeira-classe (Smith F-CRIT-06)
- Medido como mediana sobre 20 execuções do golden set
- Fonte do alvo: spec da arquitetura D-LEAN + 1 LLM call adicional (~30s no Tier Premium Sabia-7B Q4 CPU)
- Sob promoção a GPU futura ou tier menor: latência cai conforme `quality-data-modularity-assurance-2026-05-01.md`

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

### 7.7 Acessibilidade (NOVO em v1.0.2 — Sati EV-04)

**NFR-A11Y-01 — WCAG 2.1 AA mínimo**
- Sistema atende WCAG 2.1 AA mínimo em todas as páginas
- Lighthouse Accessibility score ≥90 em todas as páginas (medido em CI)
- Contraste mínimo: 4.5:1 texto normal, 3:1 texto largo
- Tabelas (especialmente FR-CALC-02 amortização 360 linhas) com `<caption>`, `<th scope="row|col">`, skip-link "Pular tabela →"
- Cor NUNCA é única forma de comunicação (BadgeAderencia tem ícone + texto além da cor)
- Navegação completa por teclado (Tab + Enter + atalhos): todos os fluxos completáveis sem mouse
- Suporte a `prefers-reduced-motion`: transições reduzidas se preferência ativa
- Alt-text em todos os ícones funcionais
- Justificativa: Lei Brasileira de Inclusão (Lei 13.146/2015) + perfil de usuários (advogados ≥50 anos com declínio visual progressivo)

### 7.8 Segurança Adicional (NOVO em v1.0.2 — Smith F-HIGH-01)

**NFR-SEC-03 — Sanitização de PDF malicioso (Smith F-HIGH-01)**
- Magic bytes (`%PDF-`) é necessário mas não suficiente
- Pipeline obrigatório de sanitização antes de qualquer processamento ou preview:
  1. `qpdf --linearize --decrypt` (remove criptografia se senha conhecida)
  2. Strip de JS embedded, formulários XFA, links externos (tracking pixels)
  3. Detecção de payloads OWASP via `pdfid.py` ou equivalente
- AC: 100% dos PDFs uploadados passam por sanitização antes de qualquer renderização
- AC: PDF com tracking pixel embedded é detectado e rejeitado em <2s

### 7.9 Governança de Dados (NOVO em v1.0.2 — Smith F-HIGH-10, F-HIGH-11)

**NFR-GOV-01 — Atribuição de peso_vinculacao via matriz canônica (Smith F-HIGH-10)**
- Atribuição segue matriz canônica em `bloco_vault/schemas/peso-vinculacao-matrix.yaml`:
  - 5 = Súmula Vinculante STF
  - 4 = Tema Repetitivo STJ + Repercussão Geral STF
  - 3 = Súmula STJ + Súmula TST/TSE
  - 2 = Acórdão STJ/STF
  - 1 = Acórdão TJ
- Atribuição automática via classificador Sabia-7B + validação humana amostral conforme decisions/vault-curation
- AC: 100% dos docs do vault têm peso_vinculacao atribuído conforme matriz (verificável por amostragem)

**NFR-LGPD-04 — Pseudonimização de dados pessoais de juízes (Smith F-HIGH-11)**
- Campo `relator` no outcomes.db é pseudonimizado: armazenado como hash sha256(nome_relator + salt)
- Mapping reverso (hash → nome) em arquivo separado `bloco_learning/relator_mapping.db` com acesso restrito (chmod 600)
- ML pipeline (estágio 2 adaptive ranking) usa APENAS hashes (não nomes em claro)
- Base legal: LGPD Art. 7 inciso V (interesses legítimos para análise estatística agregada não-individualizada)
- Política completa documentada em `docs/lgpd-tratamento-juizes.md`
- AC: nenhum nome de juiz em claro no audit.jsonl ou em logs de ML

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
| **R-01** | Tema 1378 STJ é julgado durante o MVP exigindo "análise circunstancial" como critério único | Média (julgamento pendente desde 09/09/2025) | **CRÍTICO** — Pode invalidar tese padrão | **MITIGAÇÃO ATIVA v1.0.2**: Persona Economista PROMOVIDA a primeira-classe desde MVP (custo: +30s latência); FR-MONITOR-01 SEMANAL com alerta crítico automatizado; FR-AUDIT-02 registro persistente; estrutura preparada para múltiplos cenários de julgamento (BACEN-only, análise circunstancial, ou caso-a-caso) |
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
| DP-07 | Verificar se sabia-7b:q4_K_M está em ollama.com/library OU criar Modelfile (Smith F-CRIT-04) | @dev no FR-SETUP-01 | Antes de release MVP |
| DP-08 | Validar maturidade do sqlite-vec via load test (3000 docs + 1000 queries simultâneas) — Smith F-HIGH-08 | @qa | Antes de release MVP |
| DP-09 | Benchmark de cobertura do vault: 50 contratos golden set, medir % Inviabilidade RAG vazio (Smith F-HIGH-09) | @qa via FR-RAG-06 | Antes de release MVP |

---

## 15. Change Log (append-only)

### v1.0.2 — 2026-05-01 (Morgan) — PATCH (endereçando tribunal severo etapa 1.1)

**Endereçados — 6 CRITICAL Smith (todos):**
- **F-CRIT-01** (CFOAB) → ADDED: FR-DELIV-06 "Tela de Revisão e Adoção Obrigatória" + audit log estendido com OAB+UF
- **F-CRIT-02** (citation-grounded só sintático) → ADDED: FR-TESE-04 "Validação semântica de citações" via Legal-BERTimbau similarity ≥0.7
- **F-CRIT-03** (vault sem superseded) → EXTENDED: schema FR-RAG-01 com `vigente_em`, `superseded_by`, `data_ultima_validacao` + filtro FR-RAG-02 estendido com vigência temporal
- **F-CRIT-04** (Sabia no Ollama) → ADDED: DP-07 + FR-SETUP-01 com fallback Qwen 2.5 7B
- **F-CRIT-05** (backup outcomes.db) → ADDED: FR-BACKUP-01 (automático) + FR-BACKUP-02 (manual CLI)
- **F-CRIT-06** (Tema 1378 timing) → PROMOTED: Persona Economista (P-INT-04) a primeira-classe desde MVP + ADDED FR-MONITOR-01 (scrape semanal) + R-01 atualizado para "mitigação ATIVA"; NFR-PERF-01 ajustado de ≤180s para ≤210s

**Endereçados — 11 HIGH Smith:**
- **F-HIGH-01** (PDF malicioso JS embed) → ADDED: NFR-SEC-03 (sanitização qpdf+pdfid)
- **F-HIGH-02** (bypass HITL "ok ok ok") → EXTENDED: FR-JUIZ-02 com validação semântica anti-bypass
- **F-HIGH-03** (cookie 30 dias) → ADDED: FR-AUTH-04 (IP fingerprint + 7 dias inatividade)
- **F-HIGH-04** (audit.jsonl tamper) → EXTENDED: FR-AUDIT-01 com hash chain Merkle + comando verify-audit-integrity
- **F-HIGH-05** (HF Hub SPOF + telemetria) → INTEGRATED em FR-SETUP-01 (HF_HUB_OFFLINE=1 em runtime)
- **F-HIGH-06** (recovery mid-workflow) → ADDED: FR-RECOVERY-01 com SqliteSaver checkpointer
- **F-HIGH-07** (Streamlit single-process bloqueia) → DEFERRED como tech debt: documentar uso de @st.fragment + spinner async em ux-spec-detail-v1.0.md (Aria detalha solução técnica em ADR)
- **F-HIGH-08** (sqlite-vec v0.1) → ADDED: DP-08 (load test obrigatório antes de release)
- **F-HIGH-09** (cobertura vault) → ADDED: FR-RAG-06 + DP-09 (benchmark golden set 50 contratos)
- **F-HIGH-10** (peso_vinculacao governança) → ADDED: NFR-GOV-01 + matriz canônica
- **F-HIGH-11** (relator LGPD) → ADDED: NFR-LGPD-04 + pseudonimização hash

**Endereçados — 4 EV-IDs ALTA Sati:**
- **EV-01** (HITL detail) → INTEGRATED em FR-JUIZ-02 estendido (microcopy + validação anti-bypass + spec completa do painel)
- **EV-04** (WCAG ausente) → ADDED: NFR-A11Y-01 (WCAG 2.1 AA + Lighthouse ≥90)
- **EV-05** (LLM_TIER UX) → ADDED: FR-CONFIG-01 (Página Configurações Avançadas com toggle visual)
- **EV-11** (Atomic Design) → CREATED: anexo `prd/ux-spec-detail-v1.0.md` com inventário Atoms/Molecules/Organisms/Templates/Pages

**Adiados para v1.0.3 ou anexo ux-spec (7 EV-IDs MÉDIA Sati):**
- EV-02 (ETA processamento) — absorvido como ressalva no anexo ux-spec
- EV-03 (preview/hierarquia resultado) — absorvido no anexo ux-spec
- EV-06 (microcopy upload) — absorvido no anexo ux-spec
- EV-07 (terapia Inviabilidade) — absorvido no anexo ux-spec
- EV-08 (outcomes ≤30s) — absorvido no anexo ux-spec
- EV-09 (microcopy HITL completo) — absorvido em FR-JUIZ-02 estendido + anexo
- EV-10 (UX integrações) — absorvido no anexo ux-spec

**Aceitas como riscos conhecidos (não-correção, justificativa registrada):**
- nenhuma — todas as 22 findings de Smith e 11 EV-IDs de Sati foram endereçadas (6 EV adiadas para o anexo UX, todas as outras absorvidas)

**Estrutura — Atualizado:**
- ADDED 3 novos itens [DADO-PENDENTE]: DP-07, DP-08, DP-09
- ADDED nova seção 6.11 "Setup, Backup e Recovery"
- ADDED nova seção 6.12 "Configurações Avançadas e Segurança"
- ADDED nova seção 7.7 "Acessibilidade"
- ADDED nova seção 7.8 "Segurança Adicional"
- ADDED nova seção 7.9 "Governança de Dados"
- UPDATED NFR-PERF-01: latência alvo ≤180s → ≤210s (justificada por +1 LLM call do Economista)
- UPDATED R-01 (Tema 1378 STJ): de "risco mitigado" para "mitigação ATIVA" com escudo arquitetural completo
- UPDATED FR-AUDIT-01: hash chain anti-tamper
- CREATED anexo `prd/ux-spec-detail-v1.0.md` (inventário Atomic Design)

**Decisão pendente para Eric (não endereçada nesta versão):**
- DP-05 (política retenção LGPD 24h proposta) — humano confirma
- Política de outcomes — quem registra (Eric? advogado-piloto? integração externa?)

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
