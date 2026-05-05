---
type: decisions
title: "Revisor Contratual — Arquitetura D (LEAN) — Refatoração Radical"
project: revisor-contratual
author: "@analyst (Atlas)"
date: "2026-05-01"
trigger: "Eric: 'Essa estrutura está muito pesada — 16RAM é extremamente alta para uma aplicação tão simples.'"
supersedes_partially:
  - "decisions/decisions-consolidated-2026-05-01.md (D-01, D-02, D-04, D-11, D-12)"
  - "decisions/vault-curation-and-hardware-strategy-2026-05-01.md (D-11 patch)"
audience: ["Eric Claudino", "@architect (Aria)"]
tags:
  - project/revisor-contratual
  - architecture-refactoring
  - lean
  - lightweight
---

# Arquitetura D (LEAN) — Refatoração Radical

> **Auto-crítica:** A arquitetura C que propus tinha **80% de gordura** para o caso real. Pensei como engenheiro paranoico (escala, multi-tenant, observability industrial) — não como Decoder do que de fato a aplicação faz: **1 advogado processa 1 contrato por vez**.
>
> **Princípio de refatoração:** _"Onde realmente precisa de LLM? Onde matemática pura basta? Onde infra resolve sem container?"_

---

## ⚡ TL;DR

| Métrica | Arquitetura C (proposta anterior) | Arquitetura D (LEAN — nova) | Redução |
|---------|----------------------------------|----------------------------|---------|
| **RAM em uso** | ~12-15 GB | **~3-4 GB** | **-75%** |
| **Containers Docker** | 5 (Streamlit, FastAPI, Redis, Ollama, Qdrant) | **0** | **-100%** |
| **Processos Python** | 3+ (Streamlit, FastAPI, workers Dramatiq) | **1** | **-66%** |
| **Chamadas LLM por contrato** | 4 (Perito, Economista, Advogado, Juiz) | **1** (apenas Advogado) | **-75%** |
| **Latência por contrato** | 5-8 min (Sabia-7B Q4 CPU) | **30s-2min** (Qwen 2.5 3B) | **-75%** |
| **Hardware mínimo** | RTX 4070 Ti 16GB OU CPU lento | **Qualquer laptop 8GB OU VPS R$ 30/mês** | -90% custo |
| **Setup time** | ~1 dia (5 containers + config) | **~1h** (pip install + 1 modelo) | -90% |

**Mensagem:** Eric pode rodar a aplicação inteira no laptop dele com folga, em Raspberry Pi 5, ou em VPS de R$ 30/mês.

---

## 🔬 Análise: Onde realmente precisa de LLM?

Re-pensei cada persona honestamente:

| Persona original | Função real | Precisa LLM? | Justificativa |
|------------------|-------------|:------------:|---------------|
| **Perito Contábil** | Cálculo Tabela Price + comparação BACEN | ❌ **NÃO** | Matemática Decimal pura. Tools determinísticas. LLM só atrasaria. |
| **Economista** | (já eliminado em D-04) | n/a | Removido; pode voltar como tool se Tema 1378 STJ exigir |
| **Advogado** | Redigir tese fundamentada citando jurisprudência | ✅ **SIM** | Texto persuasivo + citation-grounded — único lugar onde LLM agrega valor real |
| **Juiz Revisor** | 3 checagens (taxa BACEN inferior? juris vinculante? jurisdição correta?) | ❌ **NÃO** | Lógica determinística pura. Função Python com asserts e scoring. |

### Conclusão crítica
**Apenas 1 chamada LLM por contrato é necessária** — para o Advogado. Tudo o mais é matemática + lookup + lógica.

Isso muda TUDO.

---

## 🏗️ Arquitetura D — Pipeline Ultra-Lean

```
┌──────────────────────────────────────────────────────────────────┐
│  Streamlit (single process, asyncio interno)                     │
│  ↓                                                                │
│  1. PDF → PyMuPDF4LLM → Markdown                  [Python puro]  │
│  ↓                                                                │
│  2. Regex/heurísticas → extrai taxa, prazo, valor [Python puro]  │
│  ↓                                                                │
│  3. python-bcb → fetch taxa BACEN modalidade+data [Python puro]  │
│  ↓                                                                │
│  4. Decimal → calcular Price + comparar BACEN     [Python puro]  │
│  ↓                                                                │
│  5. sqlite-vec → top-10 jurisprudência filtrada   [SQLite]       │
│     WHERE court_id IN ('STJ','STF','TJBA') AND binding=1          │
│  ↓                                                                │
│  6. **Qwen 2.5 3B → gera tese fundamentada**      [LLM ÚNICA]    │
│     citation-grounded com [id_doc:N]                              │
│  ↓                                                                │
│  7. Função Python → 3 checagens do Juiz           [Python puro]  │
│     score quantificado + 3 vereditos                              │
│  ↓                                                                │
│  8. Jinja2 + WeasyPrint → petição PDF + hash      [Python puro]  │
└──────────────────────────────────────────────────────────────────┘

Footprint runtime:
  - Streamlit + Python: ~500 MB
  - Qwen 2.5 3B Q4: ~2 GB
  - Legal-BERTimbau-base: ~250 MB (vs large 330MB)
  - SQLite + sqlite-vec: ~100 MB
  - PyMuPDF + libs: ~150 MB
  TOTAL: ~3 GB RAM em uso (pico ~4 GB)

Disco:
  - Modelos LLM + embeddings: ~3 GB
  - Vault SQLite (3000 docs): ~500 MB
  - Cache BACEN + Lex: ~50 MB
  TOTAL: ~3.5 GB
```

---

## 📋 Decisões Atualizadas (substituem partes anteriores)

### **D-01 → REVISADO: Arquitetura D (LEAN), não C**

| Camada | Arquitetura C (descartada) | Arquitetura D (NOVA) |
|--------|---------------------------|----------------------|
| **UI** | Streamlit + FastAPI separado | **Streamlit ONLY** (sem FastAPI) |
| **Async** | FastAPI + Dramatiq + Redis | **asyncio puro** (Python stdlib) |
| **Orquestração** | LangGraph + SqliteSaver completo | **LangGraph mínimo** (3 nós) OU state machine puro |
| **LLM serving** | Ollama (Sabia-7B) | **Ollama (Qwen 2.5 3B Q4)** ou llama-cpp-python embedded |
| **Modelo** | Sabia-7B Q4 (5GB) | **Qwen 2.5 3B Q4 (2GB)** — PT-BR oficial Llama 3.2 fallback |
| **Vector store** | Qdrant + Docker | **sqlite-vec extension** (zero infra) ([asg017/sqlite-vec](https://github.com/asg017/sqlite-vec)) |
| **Embeddings** | Legal-BERTimbau-large (330MB) | **Legal-BERTimbau-base** (~250MB) — mesma qualidade jurídica, menor footprint |
| **Parsing** | Marker + Docling + PyMuPDF4LLM | **PyMuPDF4LLM** primário (rápido) + Marker apenas para OCR |
| **BACEN** | python-bcb + diskcache | **Manter** (já leve) |
| **Cache** | Redis | **diskcache** (filesystem, zero infra) |
| **Observability** | OpenTelemetry + Prometheus + audit | **structlog → audit.jsonl** apenas |

### **D-02 → REVISADO: 6 blocos (não 7)**

| Bloco | Status | Mudança |
|-------|--------|---------|
| `bloco_contratos/` | ✅ Manter | Pydantic models — leve e útil |
| `bloco_interface/` | ✅ Manter | Streamlit ONLY (sem FastAPI separado) |
| `bloco_workflow/` | 🆕 Renomeado | LangGraph mínimo OU state machine — substitui `bloco_agentes/` + `bloco_api/` |
| `bloco_vault/` | ✅ Manter | sqlite-vec em vez de Qdrant |
| `bloco_engine/` | ✅ Manter | parsing + cálculo + BACEN |
| `bloco_audit/` | 🆕 Simplificado | structlog → audit.jsonl (substitui `bloco_observability/` complexo) |
| ~~`bloco_api/`~~ | ❌ ELIMINADO | Streamlit chama workflow inline via asyncio |
| ~~`bloco_observability/`~~ | ❌ Reduzido | Vira `bloco_audit/` minimalista |

**Estrutura final:**
```
revisor_contratual/
├── bloco_contratos/      # Pydantic shared models
├── bloco_interface/      # Streamlit (single process)
├── bloco_workflow/       # state machine (LangGraph minimal ou puro Python)
├── bloco_vault/          # sqlite-vec + Legal-BERTimbau-base
├── bloco_engine/         # parsing + cálculo + BACEN
├── bloco_audit/          # structlog → audit.jsonl
├── tests/
├── pyproject.toml
└── README.md
```

**6 blocos. Sem Docker. Sem containers. 1 processo Python.**

### **D-04 → REVISADO: 1 chamada LLM (não 3)**

| Antes | Agora |
|-------|-------|
| 3 personas LLM (Perito, Advogado, Juiz) | **Apenas Advogado é LLM** |
| Perito chamava LLM + tools | **Perito vira função Python** que chama tools direto |
| Juiz LLM com 3 checagens | **Juiz vira função Python** com asserts + scoring |

**Implicação:** workflow LangGraph simplifica para 4 nós (parser → calculator → retriever → llm_advogado → judge_function → renderer). Última iteração: Tema 1378 STJ pode reverter — adicionar Economista como **tool latente** chamado pelo Advogado se análise circunstancial for exigida.

### **D-11 → REVISADO: Hardware atual de Eric SOBRA**

| Recurso | Necessário (D) | Eric tem | Status |
|---------|---------------|----------|--------|
| RAM | 4 GB em uso | 16 GB | ✅ **Sobra 12 GB** |
| GPU VRAM | Opcional (CPU OK) | 4 GB | ✅ Pode rodar Qwen 3B em GPU |
| CPU | 4 cores | 4C/8T | ✅ OK |
| Disk | 5 GB | 333 GB livres | ✅ OK |

**Sem necessidade de cloud, sem necessidade de workstation, sem necessidade de Docker.**

Para produção real (multi-cliente), VPS de R$ 30-100/mês resolve.

### **D-12 → ATUALIZADO: UF inicial = BA (Bahia)**

**Bahia (TJBA)** confirmada como UF inicial. Achados que reforçam:

| Aspecto | Status |
|---------|--------|
| TJBA tem jurisprudência consumerista bancária ativa | ✅ Confirmado |
| Câmaras Recursais com decisões sobre revisional CDC veículos | ✅ Confirmado |
| Alinhado com Tema 1378 STJ ("abusividade só se taxa discrepa SUBSTANCIALMENTE da média") | ✅ |
| Vedação de venda casada (CDC) reforçada | ✅ |
| Acessibilidade dos dados via portal TJBA + Jusbrasil | ✅ |

**Filtro principal do RAG:** `WHERE court_id IN ('STJ', 'STF', 'TJBA')`

**Vault inicial:** ~3.000 docs (STF Súmulas Vinculantes + STJ Temas Repetitivos + STJ Súmulas + TJBA acórdãos revisional ~300).

---

## 🎯 Implicações Práticas para Eric

### Você pode começar AMANHÃ:
```bash
# Setup completo
pip install streamlit langchain langgraph sqlite-vec sentence-transformers \
            ollama python-bcb pymupdf4llm pydantic structlog jinja2 weasyprint

# Modelos (one-time download)
ollama pull qwen2.5:3b-instruct-q4_K_M

# Rodar
streamlit run app.py
```

**Setup: ~1 hora. Sem Docker. Sem Redis. Sem nada além de Python.**

### Custo operacional
| Cenário | Custo |
|---------|-------|
| Dev no seu laptop | **R$ 0/mês** |
| VPS produção single-tenant | **R$ 30-50/mês** (Hetzner CX22, 4GB RAM) |
| VPS prod multi-cliente leve | **R$ 100-200/mês** (Hetzner CX42, 16GB RAM) |
| Cloud GPU para piloto avançado | **R$ 200-500/mês** (RunPod RTX 4090 sob demanda) |

### Latência esperada
| Operação | Tempo |
|----------|-------|
| Upload + parsing PDF (50 pgs) | 5-15s |
| Cálculo Decimal Price + BACEN | <1s |
| RAG sqlite-vec (3000 docs) | ~100ms |
| **Geração tese (Qwen 2.5 3B Q4)** | **20-60s** (CPU) ou 5-15s (GPU) |
| Validação Juiz (Python) | <100ms |
| Renderização petição | 1-3s |
| **TOTAL por contrato** | **30s-2min** |

vs. ~5-8 min na arquitetura C. **3-10× mais rápido.**

---

## 🧪 Trade-offs Aceitos da Arquitetura D

| Trade-off | Por que aceitamos |
|-----------|-------------------|
| Qwen 2.5 3B é menor que Sabia-7B | PT-BR oficial Qwen + foco em geração de tese (não-conversação) — qualidade suficiente para MVP |
| sqlite-vec é brute-force (não HNSW) | Para 3.000 docs é IRRELEVANTE (busca em <100ms) |
| Sem queue de workers | 1 advogado, 1 contrato por vez — desnecessário em MVP |
| Sem tracing OpenTelemetry | structlog + audit.jsonl é o suficiente para auditoria solo |
| Sem retry policy sofisticado | tenacity dentro das tools resolve casos críticos (BACEN, RAG) |
| Sem multi-tenant | MVP é single-user. Multi-tenant entra em fase 2 com migration plan |

### Caminho de upgrade quando crescer
- **Multi-cliente** → adicionar FastAPI + Dramatiq sem mexer no core (Streamlit vira mais um cliente)
- **>10k jurisprudências** → migrar sqlite-vec para Qdrant (1 sprint)
- **LLM melhor** → trocar Qwen 2.5 3B por Sabia-7B ou Qwen 2.5 14B (1 linha de config)
- **Tracing pesado** → adicionar OpenTelemetry (1 sprint)

**Migrações são incrementais — não exigem reescrita.**

---

## 📊 Comparação Final — Arquiteturas A vs B vs C vs D

| Aspecto | A (sua original) | B (Atlas aggressive) | C (Híbrido — descartado) | **D (LEAN — nova)** |
|---------|------------------|---------------------|--------------------------|---------------------|
| Containers | 0 | 4-5 | 4-5 | **0** |
| Processos | 1-2 | 3+ | 3+ | **1** |
| RAM uso | ~6 GB | ~12 GB | ~12 GB | **~3-4 GB** |
| Latência | 5-10 min (trava) | 1-3 min (vLLM GPU) | 5-8 min | **30s-2min** |
| Curva | Baixa | Alta | Média | **Baixíssima** |
| Trava? | 🔴 Sim | 🟢 Não | 🟢 Não | 🟢 **Não** |
| LGPD | ⚠️ se mal arquitetado | ✅ | ✅ | ✅ |
| Custo VPS | n/a | R$ 500-1500/mês | R$ 200-500/mês | **R$ 30-100/mês** |

**D vence em: simplicidade, custo, latência, hardware-friendliness.**
**D perde em: throughput multi-tenant pesado (mas isso é fase 2+).**

---

## ⚠️ O que continua igual (decisões anteriores mantidas)

- **D-03**: Decimal everywhere (não-negociável — vale para qualquer arquitetura)
- **D-05**: Pipeline 3-camadas para vault (Atlas roda scrapers Python → Qwen auto-classifica → Eric valida estratificado)
- **D-06**: 4 fontes jurisprudência (STF Súmulas Vinculantes + Repercussão Geral + STJ Súmulas + Temas Repetitivos)
- **D-07**: DataJud fase 2
- **D-08**: LexML pré-cache 4 diplomas (CDC, CC, SFN, MP capitalização)
- **D-09**: Descartar abjur (R)
- **D-10**: MVP CDC PF Veículos com posicionamento ajustado (gap RAG+IA, não calculadora)
- **D-13**: Adiar business/brand para fase 2

---

## 🔄 Próxima Skill (handoff atualizado)

**`LMAS:agents:architect` (Aria)** com pacote ATUALIZADO:
- `.project.yaml` (atualizar para refletir D)
- 4 docs research (state-of-the-art, deep-dive, data-sources, competitor-analysis)
- 4 docs decisions (consolidated, risk-analysis, vault-curation-hardware, **architecture-D-lean** ⭐)
- **Mandato Aria atualizado:** SAD formal v1.0 baseado em arquitetura D (LEAN), 4-5 ADRs (não 6-7), diagramas C4 simplificados, política LGPD para single-process Streamlit + sqlite-vec local.

---

## 📌 Resposta direta ao Eric

> **"Essa estrutura está muito pesada — 16RAM é extremamente alta para uma aplicação tão simples."**

**Você tinha razão.** Refatorei. Resultado:

- **3-4 GB RAM** em vez de 12-15 GB
- **Zero containers Docker** em vez de 5
- **1 processo Python** em vez de 3
- **1 chamada LLM por contrato** (Advogado) em vez de 4
- **30s-2min** por contrato em vez de 5-8 min
- **R$ 30-50/mês** em produção em vez de R$ 500-1500
- **Setup em 1h** em vez de 1 dia

A aplicação é **simples sim** — e a stack agora reflete isso. Foi minha falha pensar em "produção massiva" quando o caso real é "1 advogado, 1 contrato por vez". Decoder estava paranoico, não analítico.

---

*Atlas, devolvendo o peso da realidade ao projeto — 🔎*
