---
type: decisions
title: "Revisor Contratual — Decisões Consolidadas (Atlas → Aria handoff)"
project: revisor-contratual
author: "@analyst (Atlas)"
delegated_by: "Eric Claudino"
date: "2026-05-01"
status: approved-by-delegation
predecessor_docs:
  - "research/state-of-the-art-2026-04-30.md"
  - "research/module-by-module-deep-dive-2026-04-30.md"
  - "research/data-sources-external-integrations-2026-05-01.md"
next_skill: "LMAS:agents:architect (Aria)"
tags:
  - project/revisor-contratual
  - decisions
  - architecture-input
  - phase-0-closure
---

# Revisor Contratual — Decisões Consolidadas

> **Origem:** Eric Claudino delegou explicitamente as 13 decisões pendentes a Atlas (@analyst), com mandato: *"você sabe o que faz diferença para esse projeto, os dados necessários e mais importantes."*
>
> **Mandato exercido:** decidir cada uma com **justificativa rastreável** baseada em research das 3 sessões anteriores. Documento serve de **input formal** para a próxima Skill (`@architect` Aria) produzir SAD.
>
> **Escopo desta decisão:** decisões técnicas + estratégicas que destravam Phase 1 (implementação). Decisões posteriores (refinamentos arquiteturais, ADRs específicos, scope de stories) ficam com Aria + Keymaker.

---

## ⚡ Sumário Executivo — 13 Decisões + 4 Repos Adicionais

| # | Decisão | Escolha | Confiança |
|---|---------|---------|-----------|
| **D-01** | Arquitetura | **C — Híbrido Pragmático** | 🟢 Alta |
| **D-02** | Estrutura nova (3 blocos extra) | **SIM — adotar** | 🟢 Alta |
| **D-03** | Decimal everywhere | **SIM — não-negociável** | 🟢 Alta |
| **D-04** | 5 personas ou eliminar Economista | **ELIMINAR Economista — restam 3 personas** | 🟡 Média |
| **D-05** | Vault inicial: seed manual ou pipeline | **SEED MANUAL primeiro** com courtsbr/stf+stj | 🟢 Alta |
| **D-06** | URL STJ correta | **3 URLs adotadas** + STF Súmulas Vinculantes | 🟢 Alta |
| **D-07** | DataJud fase 1 ou 2 | **FASE 2 — não-crítico para MVP** | 🟢 Alta |
| **D-08** | LexML API ou pré-cache | **PRÉ-CACHE de 4 diplomas** (CDC, CC, SFN, MP) | 🟢 Alta |
| **D-09** | Auditar abjur (109 repos) | **FEITO — descartado uso direto** (R-dominado) | 🟢 Alta |
| **D-10** | Tipo contrato MVP | **CDC PF — Aquisição de Veículos** | 🟢 Alta |
| **D-11** | Hardware target | **Cenário A (laptop) → C (workstation) em prod** | 🟢 Alta |
| **D-12** | UF inicial vault | **MG (TJMG)** | 🟡 Média |
| **D-13** | Domínio LMAS secundário | **Adiar para fase 2** | 🟢 Alta |

**Repos adicionais identificados nesta sessão (essenciais):**
- 🟢 [`courtsbr/stf`](https://github.com/courtsbr/stf) — scraper STF (vault seed)
- 🟢 [`courtsbr/stj`](https://github.com/courtsbr/stj) — scraper STJ (vault seed)
- 🟢 [HuggingFace `joelniklaus/brazilian_court_decisions`](https://huggingface.co/datasets/joelniklaus/brazilian_court_decisions) — STF + STJ + TJ-SP + TJ-RJ + TSE
- 🟡 [`JurisTCU`](https://arxiv.org/html/2503.08379) — benchmark RAG legal PT-BR (16k docs + 150 queries com relevance judgments) — usar como **test set** para validar Bloco 3

---

## D-01 — Arquitetura: C (Híbrido Pragmático)

### Escolha
**Arquitetura C** (do `state-of-the-art-2026-04-30.md`):
- Streamlit (UI familiar) + FastAPI+RQ atrás (não trava)
- Sabia-7B (PT-BR) + Legal-BERTimbau (jurídico)
- Qdrant embedded (filtros 1.1× overhead)
- Docling/Marker/PyMuPDF4LLM (parsing inteligente híbrido)
- LangGraph + SqliteSaver (resume após crash)
- python-bcb + diskcache + tenacity
- NumPy Financial → **substituído por Decimal puro** (ver D-03)

### Razão
- **Mantém familiaridade** Streamlit (curva mínima vs B com NiceGUI)
- **Cura os 3 furos críticos** da arquitetura A: trava, qualidade PT-BR, filtros vector
- **Permite migração incremental** para B sob demanda quando MVP escalar
- **Menor risco** que B (NiceGUI + vLLM + Dramatiq seria mudança grande de uma vez)

### Tradeoff aceito
- Performance ligeiramente inferior a B (vLLM > Ollama em concorrência)
- Mais setup que A (precisa FastAPI + RQ + Redis local)

### Dependências (próxima Skill)
Aria deve produzir **ADR-001** formalizando essa decisão com tabela de tradeoffs A vs B vs C.

---

## D-02 — Adotar Estrutura Nova (bloco_contratos/, bloco_api/, bloco_observability/)

### Escolha
**SIM — adotar** os 3 blocos novos propostos no `module-by-module-deep-dive`.

### Razão
Cada bloco novo cura uma **fragilidade transversal documentada**:

| Bloco novo | Fragilidade que cura |
|-----------|---------------------|
| `bloco_contratos/` | #1 Acoplamento implícito (Pydantic models partilhados) |
| `bloco_api/` | Síncrono que trava (FastAPI bridge + workers Dramatiq/RQ) |
| `bloco_observability/` | #3 Observabilidade ausente (OpenTelemetry + audit-log) |

Sem eles, o produto vai pra produção e quebra na primeira semana.

### Dependências
Aria deve documentar em **ADR-002** o pattern arquitetural de 7 blocos (4 originais + 3 novos) e os contratos Pydantic entre eles.

---

## D-03 — Decimal Everywhere (NÃO-NEGOCIÁVEL)

### Escolha
**SIM — Decimal em TODO cálculo financeiro**. Float é PROIBIDO em campos monetários.

### Razão
Critério legal: perícia judicial não aceita imprecisão de centavos. Para 360 parcelas (imobiliário 30 anos), float acumula erros que invalidam o cálculo.
- `numpy_financial.pmt` retorna float — **NÃO USAR**
- Implementar Tabela Price + SAC + juros simples manualmente com `decimal.Decimal` + `getcontext().prec = 28`
- Schema Pydantic: campos monetários como `str` (Decimal serializado) → re-converter ao usar

### Tradeoff aceito
- ~10-30% mais lento que float (irrelevante para 360 iterações: ~50-100ms vs 5-10ms)
- Código mais verboso

### Dependências
Aria documenta em **ADR-003** o padrão "Decimal-as-string" em todo o EstadoRevisor TypedDict.

---

## D-04 — Eliminar Persona Economista (3 personas, não 5)

### Escolha
**Eliminar Economista.** Restam 3 personas:
1. **Perito Contábil** (cálculo via tools)
2. **Advogado** (RAG + tese)
3. **Juiz Revisor** (validação 100% aderência)

### Razão
- **Sem responsabilidade EXCLUSIVA**: o Perito já consulta BACEN; "análise contextual macro" do Economista é cosmética e duplica latência LLM.
- **Cada nó adicional = +30-90s** (chamada LLM + processamento) sem agregar para o veredicto do Juiz.
- **3 personas é o mínimo viável** para o conceito state-machine + HITL.

### Tradeoff aceito
- Perde-se eventual análise macro-econômica (ex: "essa taxa BACEN é atípica devido a ciclo de Selic"). Se necessário no futuro, virar **tool** chamada pelo Perito, não persona separada.

### Confiança: 🟡 Média
Reversível em fase 2 se prova de campo mostrar que análise contextual agrega valor.

### Dependências
Aria atualiza diagrama do grafo LangGraph com 3 nós + Juiz + HITL.

---

## D-05 — Vault Inicial: Seed Manual (depois pipeline)

### Escolha
**Seed manual primeiro** rodando uma vez:
1. **`courtsbr/stf`** → STF Súmulas + Súmulas Vinculantes + acórdãos relevantes (peso 5/5)
2. **`courtsbr/stj`** → STJ Súmulas + Temas Repetitivos + acórdãos PF veículos (peso 4-3/5)
3. **HuggingFace `joelniklaus/brazilian_court_decisions`** → enriquecimento (TJ-SP/TJ-RJ por similaridade)
4. **TJMG**: scraping ad-hoc 100-300 acórdãos sobre "revisão CDC veículos" (peso 1/5 mas crítico para UF)

**Pipeline mensal de re-indexação** entra em fase 2.

### Razão
- **Crítico para MVP**: sem vault populado, o Bloco 3 sempre retorna RAG vazio → todo workflow vai para Relatório de Inviabilidade
- **Estimativa de volume**: ~2.000-3.000 docs (cabe em Qdrant embedded sem problema)
- **Curadoria humana inicial** garante qualidade do seed (filtrar lixo, taggar metadata correto)
- **Pipeline automático mais tarde** quando processo de seed estiver maduro

### Dependências
- @sm: criar Story "Seed inicial vault de jurisprudência" como primeira story do Epic 2 (Bloco 3).
- Atlas: pode rodar os scrapers `courtsbr/*` (R) localmente OU buscar wrappers Python equivalentes em fase 1.

---

## D-06 — URLs STJ Adotadas (+ STF)

### Escolha
**4 URLs canônicas para o vault de jurisprudência:**

| Fonte | URL | Tipo | Peso vinculação | Volume estimado |
|-------|-----|------|----------------|-----------------|
| **STF Súmulas Vinculantes** | [stf.jus.br/.../Sumulas_Vinculantes](https://www.stf.jus.br/arquivo/cms/jurisprudenciaSumulaNaJurisprudencia/anexo/Livro_Sumulas_Vinculantes_2_edicao.pdf) | PDF + scraping HTML | **5/5** | ~58 súmulas |
| **STF Repercussão Geral** | [portal.stf.jus.br/repercussaogeral/teses](https://portal.stf.jus.br/repercussaogeral/teses.asp) | HTML estruturado | 5/5 (constitucional) | ~1.300 teses |
| **STJ Súmulas** | [stj.jus.br/.../Sumulas](https://www.stj.jus.br/sites/portalp/Jurisprudencia/Sumulas) | HTML | 3/5 | ~671 súmulas |
| **STJ Temas Repetitivos** | [stj.jus.br/repetitivos/temas_repetitivos](https://www.stj.jus.br/repetitivos/temas_repetitivos) | HTML | **4/5 — CRÍTICO** | ~1.300 temas |

**+ ferramenta de validação manual:** [scon.stj.jus.br](https://scon.stj.jus.br/) (busca interativa para curar seed).

### Razão
- **STF Súmulas Vinculantes** = peso máximo. Súmula 121/STF (anatocismo) é central para o produto.
- **STJ Temas Repetitivos** = vinculantes para todos os tribunais inferiores. Tema 247 (Tabela Price) é central.
- **STJ Súmulas** = referenciais frequentes (Súmula 539 — capitalização infra-anual no SFN).

### Filtros priorizados para seed inicial (v1)
- Temas legais: `ANATOCISMO`, `CAPITALIZACAO_JUROS`, `TABELA_PRICE`, `JUROS_REMUNERATORIOS`, `REVISAO_CONTRATUAL`, `ABUSIVIDADE_JUROS`, `CDC_BANCARIO`
- Modalidades: `VEICULO` (foco MVP), `CDC_GENERICO`, `IMOBILIARIO`

---

## D-07 — DataJud na Fase 2 (não-crítico MVP)

### Escolha
**Adiar DataJud para Fase 2.**

### Razão
- DataJud retorna **metadados de processos individuais**, não jurisprudência consolidada
- O produto MVP analisa **contrato + jurisprudência** — DataJud é **enriquecimento estatístico** ("70% dos casos no TJMG ganham revisão")
- **Bloqueador atual:** seed do vault (D-05). Sem vault, DataJud não agrega.
- **Fase 2 valor:** após MVP funcionar, DataJud permite "score de probabilidade de êxito" baseado em casos análogos

### Dependências
Aria documenta em **ADR-004**: DataJud é dependência opcional do Bloco 4, ativada via feature flag.

---

## D-08 — LexML: Pré-cache de 4 Diplomas Críticos

### Escolha
**Pré-cachear 4 diplomas legais em `bloco_vault/seed/legislacao/`:**

| Lei | Por quê é crítico | Tamanho aprox. |
|-----|-------------------|----------------|
| **CDC — Lei 8.078/90** | Base de toda revisão consumerista (arts. 39, 51 — cláusulas abusivas) | ~80 páginas |
| **Código Civil — Lei 10.406/02** | Contratos em geral (arts. 421-480), mútuo (591) | ~600 páginas (extrair só Livro I Títulos V-VI) |
| **Lei do SFN — Lei 4.595/64** | Caracteriza "instituição financeira" (Súmula 539 STJ) | ~30 páginas |
| **MP 2.170-36/2001** | Capitalização infra-anual no SFN | ~5 páginas |

**API LexML** só usar para edge cases (norma não cacheada citada por algum acórdão).

### Razão
- **4 diplomas cobrem >95% das citações** em revisão contratual bancária PF
- **Cache local elimina latência** + dependência de SLA externo
- **Versionamento por git** dos JSONs cacheados garante reprodutibilidade

### Dependências
- @sm: criar Story "Seed legislação no vault" — fetch via LexML API uma vez, salvar JSON estruturado.
- Aria documenta em **ADR-005**: estratégia de cache local + invalidação manual (leis raramente mudam).

---

## D-09 — abjur Auditado (109 Repos R-dominados — Descartar)

### Escolha
**Descartar uso direto** dos repos `abjur/*`. **Aproveitar conhecimento conceitual** apenas (taxonomia jurimétrica BR).

### Razão (auditoria desta sessão)
A org [github.com/abjur](https://github.com/orgs/abjur/repositories) tem **109 repositórios** (não 18 como estimado anteriormente). Destaques:

| Repo | Linguagem | Aplicabilidade |
|------|-----------|---------------|
| `cartoriosinfo` | Python | Único Python — escopo nicho (cartórios) |
| `tpur` | R | Brazilian Unified Procedural Tables — referência conceitual |
| `datajudScraper` | R | Stack incompatível |
| `cnc` | R | Scraper CNC-CNJ |
| `abjData` | R | Datasets gerais R |
| ~104 outros | majoritariamente R | Não auditados — estatística inferior a 1% Python |

**Conclusão:** ABJ é **referência metodológica em jurimetria BR** mas não fornece código diretamente reutilizável em Python para nosso caso.

### Aproveitamento
Estudar metodologia ABJ ([abj.org.br](https://abj.org.br/)) para inspiração em métricas/avaliação do produto, **NÃO depender de código deles**.

---

## D-10 — Tipo de Contrato MVP: CDC PF — Aquisição de Veículos

### Escolha
**MVP foca em CDC Pessoa Física para aquisição de veículos.**

### Razão
- **Modalidade mais comum** em revisional bancária BR
- **BACEN tem código SGS específico** (25471 mensal, 20749 média) — Bloco 4 já tem dado pronto
- **Anatocismo + Tabela Price** são temas clássicos com vasta jurisprudência consolidada
- **Volume processual**: TJMG/TJSP/TJRS têm milhares de casos = bom corpus de treinamento e validação
- **Contrato típico curto** (10-30 páginas) — bom para iteração rápida no parsing
- **Tabela de amortização presente** — testa a stack Docling/Marker em PDFs financeiros reais

### Modalidades posteriores (fase 2+)
- CDC genérico (bens de consumo não-veículos)
- Cartão de crédito rotativo
- Imobiliário (mais complexo: SAC + Price + cláusulas específicas SFH)

### Dependências
- @pm: PRD v1.0 escopa explicitamente "MVP = CDC PF Veículos"
- Atlas: seed inicial do vault prioriza jurisprudência sobre CDC veículos

---

## D-11 — Hardware: Laptop Dev → Workstation Prod

### Escolha
**Cenário A (laptop dev) para Phase 1-2** → **Cenário C (workstation RTX 4070 Ti)** quando MVP for para produção real.

### Razão
- **Não comprar hardware antes de MVP funcionar** — princípio lean.
- Laptop atual já roda Sabia-7B Q4 (~5GB VRAM) + Qdrant embedded + Streamlit + FastAPI.
- Latência aceitável para 1 contrato/vez em dev (3-8 min — não importa).
- **Workstation entra quando**: Eric tiver 1º cliente real OU quando latência > 10min começar a incomodar.

### Tradeoff aceito
- Em dev, processar contrato leva ~5-8 min (vs 1-2 min em workstation)
- Aceitável para iteração

### Dependências
Aria documenta em **ADR-006**: targets de hardware por fase (dev/staging/prod).

---

## D-12 — UF Inicial Vault: MG (TJMG)

### Escolha
**Minas Gerais (TJMG)** como UF inicial do vault.

### Razão
- **TJMG tem corpus consolidado** de revisional bancária (Súmula 30 TJMG sobre limitação de juros é referência nacional)
- **Câmaras especializadas** em Direito do Consumidor produzem acórdãos coerentes
- **Volume processual** alto = bom para testar filtros estritos `WHERE court_id = "TJMG"`
- **Acessibilidade dos dados**: TJMG tem portal com busca pública

### Confiança: 🟡 Média
Alternativas válidas:
- **TJSP**: maior volume, mas câmaras divergem mais entre si (heterogeneidade)
- **TJRS**: jurisprudência consumerista forte (defensoria robusta)

**Decisão final pode ser revisada** em Phase 2 quando Eric escolher mercado-alvo geográfico (escritório local).

### Dependências
- @sm: 1ª story do Epic 2 = "Seed jurisprudência TJMG sobre revisional CDC veículos"
- Atlas: scraping inicial focado em TJMG via `courtsbr/stj` (que tem extensão para TJ).

---

## D-13 — Domínio LMAS Secundário: Adiar para Fase 2

### Escolha
**Manter `software-dev` como único domínio para Phase 1.** Fase 2 considera `business` (oferta para advogados) e `brand` (naming/posicionamento).

### Razão
- **MVP precisa funcionar primeiro** antes de pensar em pricing/marca
- **Skills `business/brand` consomem contexto** sem agregar para a entrega técnica
- **Validação técnica** (MVP processando contrato real) é **pré-requisito** para validação de mercado

### Quando ativar
- **`@kamala`** (brand): quando Eric for definir nome comercial + posicionamento (o "Revisor Contratual" é codinome interno)
- **`@mifune`** (business): quando MVP estiver rodando e for definir oferta (R$/contrato? R$/mês? freemium?)
- **`@traffic-manager`** (business): quando houver landing page para captar advogados-piloto

---

## 🆕 Repositórios Adicionais Descobertos (essenciais)

### `courtsbr/stf` + `courtsbr/stj` (R) — VAULT SEED

| Atributo | Valor |
|----------|-------|
| Repo | [github.com/courtsbr](https://github.com/courtsbr) |
| Linguagem | R |
| Propósito | Scraping STF e STJ |
| Aplicabilidade | **Crítica** — popular vault inicial |
| Estratégia | Rodar 1× para coletar dados → exportar JSON → indexar no Qdrant |
| Stack divergente | Aceitável para script one-shot; output JSON é stack-agnóstico |

**Alternativa Python:** se Atlas/Aria não quiserem rodar R, buscar wrappers Python equivalentes em fase 1 ou re-implementar scraping (não complexo — endpoints HTML públicos).

### HuggingFace `joelniklaus/brazilian_court_decisions` — ENRIQUECIMENTO

| Atributo | Valor |
|----------|-------|
| URL | [huggingface.co/datasets/joelniklaus/brazilian_court_decisions](https://huggingface.co/datasets/joelniklaus/brazilian_court_decisions) |
| Cobertura | STF + STJ + TJ-SP + TJ-RJ + TSE |
| Formato | Parquet (HuggingFace datasets lib) |
| Licença | Verificar na página HF |
| Aplicabilidade | Enriquecer vault inicial com TJ-SP/TJ-RJ (após MG) |

### `JurisTCU` — BENCHMARK RAG (test set)

| Atributo | Valor |
|----------|-------|
| URL | [arXiv 2503.08379](https://arxiv.org/html/2503.08379) |
| Conteúdo | 16.045 docs jurisprudenciais TCU + **150 queries com relevance judgments** |
| Aplicabilidade | **Test set para validar Bloco 3** — medir precisão@k do retriever Legal-BERTimbau + Qdrant |
| Uso | Pipeline de avaliação automatizada do RAG |

### `tiagocupertino/tjrj-datajud-api-scraping` — EXEMPLO DataJud Python

| Atributo | Valor |
|----------|-------|
| URL | [github.com/tiagocupertino/tjrj-datajud-api-scraping...](https://github.com/tiagocupertino/tjrj-datajud-api-scraping-analise-de-dados-python) |
| Linguagem | Python (pandas + matplotlib + plotly + folium) |
| Aplicabilidade | **Exemplo concreto** de consumo DataJud em Python — referência para `datajud_client.py` da Fase 2 |

---

## 📋 Stack Final Consolidada (Phase 1)

### Estrutura de diretórios (Eric pode revisar antes de @architect formalizar)

```text
revisor_contratual/
├── bloco_contratos/                  # Pydantic models compartilhados (D-02)
│   ├── contrato.py                   # ContratoExtraido, MetadadosContrato, UF enum
│   ├── calculo.py                    # ResultadoCalculo, OutputPerito (Decimal-as-string D-03)
│   ├── jurisprudencia.py             # JurisprudenciaItem com peso_vinculacao
│   ├── debate.py                     # TurnoDebate, DivergenciaJuiz
│   └── decisao.py                    # DecisaoHumana, OutputJuiz
│
├── bloco_interface/                  # Streamlit (D-01)
│   ├── pages/
│   ├── api_client.py
│   ├── session.py
│   ├── componentes/
│   │   ├── uploader.py               # Pydantic + magic bytes
│   │   ├── visualizador_chat.py      # SSE-aware
│   │   └── painel_intervencao.py     # payload tipado + justificativa
│   └── utils/formatador_pdf.py       # Jinja2 + WeasyPrint + hash
│
├── bloco_api/                        # FastAPI bridge (D-02)
│   ├── main.py
│   ├── endpoints/
│   │   ├── upload.py
│   │   ├── stream.py                 # SSE
│   │   └── decisao.py
│   ├── workers/dramatiq_actors.py    # ou RQ — Aria decide
│   └── observability/
│       ├── tracing.py
│       └── audit_log.py
│
├── bloco_agentes/                    # 3 personas (D-04)
│   ├── orquestrador/
│   │   ├── grafo_estado.py           # TypedDict + Annotated reducers + Decimal-as-string
│   │   ├── definicao_nos_arestas.py  # RetryPolicy + recursion_limit + 3-vias Juiz
│   │   └── checkpointer.py           # SqliteSaver
│   ├── personas/
│   │   ├── _base.py
│   │   ├── agente_perito.py          # structured output + tool history validation
│   │   ├── agente_advogado.py        # citation-grounded + RAG fallback
│   │   └── agente_juiz_revisor.py    # score quantificado + 3-vias
│   └── prompts/                      # versionados por persona
│       ├── _base/
│       ├── perito/
│       ├── advogado/
│       └── juiz/
│
├── bloco_vault/                      # Qdrant + Legal-BERTimbau
│   ├── motor_busca/
│   │   ├── retriever.py              # RRF + cache + fallback
│   │   ├── gerador_embeddings.py     # rufimelo/Legal-BERTimbau-sts-large
│   │   └── reranker.py
│   ├── ingestao/
│   │   ├── pipeline_indexacao.py     # legal splitter + summary enrichment + dedup
│   │   ├── classificador_metadados.py
│   │   └── refresh_scheduler.py      # mensal (fase 2)
│   ├── seed/                         # D-05 + D-06 + D-08
│   │   ├── legislacao/               # 4 diplomas pré-cacheados
│   │   │   ├── cdc-lei-8078-90.json
│   │   │   ├── codigo-civil-lei-10406-02.json
│   │   │   ├── lei-sfn-4595-64.json
│   │   │   └── mp-2170-36-2001.json
│   │   └── jurisprudencia/
│   │       ├── stf-sumulas-vinculantes.json
│   │       ├── stf-repercussao-geral.json
│   │       ├── stj-sumulas.json
│   │       ├── stj-temas-repetitivos.json
│   │       └── tj-mg-acordaos-piloto.json     # D-12
│   ├── schemas/
│   │   ├── jurisprudencia_schema.yaml
│   │   └── legal_topics_taxonomia.yaml
│   └── database/qdrant_data/
│
├── bloco_engine/
│   ├── extratores/
│   │   ├── pdf_parser.py             # router Docling/Marker/PyMuPDF4LLM
│   │   ├── limpador_tabelas.py       # validação aritmética
│   │   └── detector_tipo_pdf.py
│   ├── ferramentas_calculo/          # D-03 Decimal everywhere
│   │   ├── calculadora_bacen_sgs.py  # python-bcb wrapper
│   │   ├── motor_tabela_price.py     # Decimal + simples + compostos + SAC
│   │   ├── analisador_anatocismo.py  # quantitativo + jurisprudencial
│   │   └── codigos_bacen.yaml        # mapping modalidade → código (foco VEICULO em MVP D-10)
│   ├── integracao/
│   │   ├── bacen_client.py           # python-bcb (D-09 substitui BACEN GitHub)
│   │   ├── lexml_client.py           # API edge cases (D-08)
│   │   └── stj_client.py             # acessórios para refresh
│   │   # NOTA: datajud_client.py vai para fase 2 (D-07)
│   └── tests/
│
├── bloco_observability/              # D-02
│   ├── tracing.py                    # OpenTelemetry
│   ├── metrics.py                    # Prometheus
│   └── audit_log.py                  # decisões humanas append-only
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── benchmark_rag/                # usar JurisTCU como test set
│   └── fixtures/
│       ├── contratos_sinteticos/
│       └── jurisprudencia_seed/
│
├── docker-compose.yml                # Streamlit + FastAPI + Qdrant + Redis + Ollama
├── pyproject.toml
└── README.md
```

---

## 🔄 Próximas Skills (handoff)

### Imediato
**`LMAS:agents:architect` (Aria)** com input completo:
- Spec original (`.project.yaml`)
- 3 docs de research (state-of-the-art, deep-dive, data-sources)
- Este documento de decisões
- Mandato: produzir SAD formal + 6 ADRs (D-01 a D-06 + D-11) + diagramas C4 + sequência do workflow.

### Em seguida
**`LMAS:agents:smith`** — adversarial review da arquitetura final.
- Mandato: atacar tudo que Atlas/Aria possam ter perdido. Especial atenção: segurança LGPD, edge cases jurídicos, vetores de travamento, fragilidades de seed manual.

### Depois
- **`LMAS:agents:pm` (Morgan)** — formaliza PRD v1.0 escopando "MVP = CDC PF Veículos / TJMG / 3 personas / Decimal" (D-10, D-12, D-04, D-03).
- **`LMAS:agents:po` (Keymaker)** — valida PRD (G1).
- **`LMAS:agents:sm` (River)** — Epic 1: Bloco Engine + Bloco Contratos. Epic 2: Bloco Vault + Seed. Epic 3: Bloco Agentes. Epic 4: Bloco API + Bloco Interface + Bloco Observability.

---

## ⚠️ Itens que continuam abertos (não decididos)

Não me senti confortável decidindo unilateralmente:

1. **Nome comercial** do produto ("Revisor Contratual" é codinome interno) → @kamala em fase 2
2. **Modelo de negócio** (R$/contrato? subscription? freemium?) → @mifune em fase 2
3. **Mercado-alvo geográfico** (escritório local em qual cidade?) → impacta D-12 (UF inicial)
4. **Política de retenção de dados** dos contratos analisados (LGPD: deletar imediatamente? armazenar criptografado?) → @architect deve propor; humano decide

---

## 🔗 Fontes Consultadas (esta sessão)

### Repos descobertos hoje
- [github.com/courtsbr/stf](https://github.com/courtsbr/stf)
- [github.com/courtsbr/stj](https://github.com/courtsbr/stj)
- [github.com/jjesusfilho/stj](https://github.com/jjesusfilho/stj)
- [github.com/lucianlorens/stj](https://github.com/lucianlorens/stj)
- [github.com/tiagocupertino/tjrj-datajud-api-scraping...](https://github.com/tiagocupertino/tjrj-datajud-api-scraping-analise-de-dados-python)

### Datasets
- [HuggingFace joelniklaus/brazilian_court_decisions](https://huggingface.co/datasets/joelniklaus/brazilian_court_decisions)
- [JurisTCU — arXiv 2503.08379](https://arxiv.org/html/2503.08379)

### ABJ (auditoria completa)
- [github.com/orgs/abjur/repositories](https://github.com/orgs/abjur/repositories) — 109 repos
- [abj.org.br](https://abj.org.br/) — site institucional

### Empirical legal research
- [Empirical analysis binding precedent STF — Springer 2025](https://link.springer.com/article/10.1007/s10506-025-09458-6)
- [LegalAnalytics STF appeals — Springer 2025](https://link.springer.com/article/10.1007/s10506-025-09446-w)

---

*Atlas, decifrando até a última escolha — agora a vez é da Arquiteta. 🔎*
