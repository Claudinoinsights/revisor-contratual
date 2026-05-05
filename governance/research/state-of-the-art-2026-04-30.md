---
type: research
title: "Revisor Contratual — State-of-the-Art Validation (2026-04-30)"
project: revisor-contratual
author: "@analyst (Atlas)"
date: "2026-04-30"
status: draft
tags:
  - project/revisor-contratual
  - research
  - state-of-the-art
  - legaltech
  - local-llm
  - rag
  - pdf-parsing
  - validation
related:
  - ".project.yaml"
sources_count: 35
verification_pending:
  - "Códigos BACEN SGS específicos por modalidade (verificar em https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do)"
  - "Benchmark direto Sabia-7B vs Qwen 2.5 7B em jurídico PT-BR"
  - "Performance Legal-BERTimbau-large com filtros pesados de payload"
---

# Revisor Contratual — State-of-the-Art Validation

> **Missão:** Validar a stack proposta no `.project.yaml` cruzando com pesquisa imparcial. Foco em **mais barato, mais robusto, e que NÃO TRAVE**. Cada componente recebe TOP 1 (recomendado), TOP 2 (alternativa) e descartar.
>
> **Princípio inegociável:** 100% local (LGPD + custo zero API).

---

## ⚡ Sumário Executivo — 5 Decisões Críticas

| # | Tema | Proposta original | Recomendação Atlas | Razão |
|---|------|-------------------|-------------------|-------|
| 1 | **Frontend** | Streamlit | **NiceGUI** ou **FastAPI+SSE+Streamlit como cliente fino** | Streamlit *full script rerun* trava em workflows de 5-30min ([fonte](https://medium.com/@manikolbe/streamlit-gradio-nicegui-and-mesop-building-data-apps-without-web-devs-4474106778f5)) |
| 2 | **LLM Serving** | Ollama | **Ollama (dev) + vLLM (prod)** — dual-mode | vLLM 16.6× mais throughput; quebra Ollama a 128 reqs concorrentes ([Red Hat 2025](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking)) |
| 3 | **Modelo PT-BR Jurídico** | Llama 3 / Mistral 7B | **Sabia-7B-GGUF** (gen) + **Legal-BERTimbau-large** (embeddings) | Sabia-3/4 são API-only (descartado por LGPD); Sabia-7B + LegalBERTimbau são open + jurídico-específico |
| 4 | **Vector Store** | ChromaDB ou Qdrant | **Qdrant** (prod) ou **LanceDB** (dev embed) | Qdrant 1.1× overhead com filtros vs Chroma 3-8× — crítico para WHERE court_id IN ("TJMG", "STJ") |
| 5 | **Padrão "não trava"** | Síncrono | **FastAPI + Dramatiq + Redis + SSE** | Streamlit sync trava no PDF de 50+ pgs; Dramatiq é 10× mais rápido que RQ e ack-on-completion |

**Veredicto geral:** sua arquitetura está conceitualmente sólida, mas tem **3 fragilidades operacionais** que vão causar travamentos em produção:
1. Streamlit single-thread + workflow longo
2. Ollama em concorrência (mesmo com 1 usuário, queue de tools paralelos quebra)
3. Falta de fila assíncrona — qualquer PDF grande ou Ollama lento congela a UX

---

## 1. Frontend para Agentic Workflows Long-Running

### O problema
Sua arquitetura prevê *streaming* do debate Perito ↔ Advogado ↔ Juiz em tempo real, com **pausa para Human-in-the-Loop** (botões Aprovar/Recálculo/Abortar). O fluxo total pode levar 5-30 min (Ollama + RAG + BACEN + parsing). O frontend NÃO PODE travar nem perder estado.

### Comparativo

| Opção | Pros | Contras | Custo (R$/mês local) | Maturidade | Risco de travar | Veredicto |
|-------|------|---------|---------------------|-----------|----------------|-----------|
| **Streamlit** (proposta) | Setup mínimo, comunidade enorme, Python puro | Full script rerun a cada interação, off-load obrigatório para FastAPI em workflows longos, websocket frágil ([Medium 2024](https://medium.com/@manikolbe/streamlit-gradio-nicegui-and-mesop-building-data-apps-without-web-devs-4474106778f5)) | R$ 0 | Alta | **🔴 Alto** | Aceitável só com queue externa |
| **Gradio** | Simples, integração HF, `live=True` para updates | Submit explícito, multi-user limitado, design inflexível | R$ 0 | Alta | 🟡 Médio | Bom para POC |
| **NiceGUI** | Event-driven, websocket nativo, real-time sem hack ([Bitdoze](https://www.bitdoze.com/streamlit-vs-nicegui/)) | Comunidade menor, menos pronto p/ multi-user pesado | R$ 0 | Média-Alta | **🟢 Baixo** | **TOP 1 — fit ideal** |
| **Mesop** (Google) | Streaming/large data nativo, hot reload com state preservado ([GitHub](https://github.com/mesop-dev/mesop)) | Lock-in Google, ecossistema novo, docs limitadas | R$ 0 | Média | 🟢 Baixo | TOP 2 |
| **FastAPI + SSE + HTMX** | Controle total, async nativo, debugável | Mais código, requer skills frontend | R$ 0 | Alta | 🟢 Baixo | Para equipe sênior |
| **Chainlit** | Especializado em chat-AI, debugger embutido | Menos flexível p/ painéis customizados | R$ 0 | Média | 🟡 Médio | Descartar (foco chat-only) |

**Veredicto Atlas:**
- **TOP 1: NiceGUI** — websocket nativo + event-driven resolve o problema de "trava no rerun" do Streamlit. Permite painéis Aprovar/Reprovar reagindo em tempo real ao stream de agentes.
- **TOP 2: Streamlit + FastAPI separados** — manter Streamlit (UI rica de chat) MAS off-loadar todo workflow LangGraph para FastAPI atrás de fila. Streamlit só renderiza progresso via polling/SSE. Reaproveita arquitetura proposta com mínima mudança.
- **Descartar puro Streamlit síncrono** — *vai* travar quando PDF tiver 80 páginas + Ollama estiver sob carga.

### Sinais clínicos de travamento Streamlit (a evitar)
- `st.rerun()` perdendo estado de chat
- WebSocket dropped após 5min idle
- "App is sleeping" em workflows longos
- Multi-user → sessions colidindo

---

## 2. Orquestração de Agentes

### O problema
Você precisa de: state machine **persistente** (não pode perder o trabalho do Perito se cair), **conditional edges** (Juiz aprova/rejeita), **human-in-the-loop nativo** (pausa real), e **debugability** (auditoria visual do debate).

### Comparativo

| Opção | State persistence | Conditional edges | HITL nativo | Debug UI | Lock-in | Veredicto |
|-------|------------------|------------------|------------|---------|---------|-----------|
| **LangGraph** (proposta) | ✅ Checkpointer (SQLite/PG/Redis) | ✅ First-class | ✅ Pause/resume nativo | LangSmith (cloud) ou local | LangChain ecosystem | **TOP 1** ([DataCamp](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen)) |
| **CrewAI** | Limitado | Custom wrappers | ❌ Requer hack | Web UI nascente | Médio | Descartar p/ HITL crítico |
| **AutoGen** (MS) | Limitado | Conversational only | Human-proxy pattern | AutoGen Studio | MS lock-in | TOP 2 |
| **Burr** (DAGWorks) | ✅ Pluggable persisters | ✅ State machine pura | ✅ HITL específico ([Burr blog](https://blog.dagworks.io/p/building-interactive-agents-with)) | UI embutida real-time | Mínimo | **TOP 2 — alternativa enxuta** |
| **LlamaIndex Workflows** | Em evolução | Sim | Sim | Limitado | LlamaIndex | Descartar (jovem) |
| **Custom (Python + Redis)** | Total controle | Total | Implementar | Construir | Zero | Para equipe muito sênior |

**Veredicto Atlas:**
- **TOP 1: LangGraph (manter sua escolha)** — venceu CrewAI em GitHub stars no início de 2026 ([fonte](https://www.intuz.com/blog/top-5-ai-agent-frameworks-2025)), HITL é first-class, checkpointer permite resumir após queda. Sua arquitetura de Aresta Condicional → Relatório de Inviabilidade é canônica em LangGraph.
- **TOP 2: Burr** — alternativa lightweight da DAGWorks com HITL e UI de tracing embutidas. Menor lock-in que LangChain. Considerar se quiser fugir do ecossistema LangChain.
- **Mantém**: LangGraph é a escolha certa. **Adicionar**: usar `SqliteSaver` ou `PostgresSaver` como checkpointer (não MemorySaver) para permitir resume após crash.

### Patch crítico para sua proposta
```python
# Adicionar ao grafo_estado.py
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("./bloco_agentes/state.db")
graph = workflow.compile(checkpointer=checkpointer, interrupt_before=["agente_juiz_revisor"])
```

---

## 3. Local LLM Serving

### O problema
Você roda **2 LLMs em paralelo** potencialmente (Perito chamando tool BACEN enquanto Advogado consulta RAG). Ollama é confortável mas degrada catastroficamente em concorrência.

### Comparativo

| Opção | Throughput (peak) | 50 reqs concorrentes | GPU/CPU | Modelo loading | Setup | Veredicto |
|-------|------------------|---------------------|---------|---------------|-------|-----------|
| **Ollama** (proposta) | 41 TPS ([Red Hat](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking)) | Plateau 155 tok/s, degrada | Híbrido CPU/GPU offload | GGUF instant | 1 comando | TOP 1 dev / TOP 3 prod |
| **vLLM** | 793 TPS (peak) — 8.033 TPS em Blackwell ([SitePoint 2026](https://www.sitepoint.com/ollama-vs-vllm-performance-benchmark-2026/)) | 920 tok/s, 100% success @ 128 reqs | GPU only (CUDA/ROCm) | Continuous batching + PagedAttention | Mais complexo | **TOP 1 prod** |
| **llama.cpp server** | 132 tok/s ([TechPlained](https://www.techplained.com/ollama-vs-vllm-vs-llamacpp)) | Médio | CPU/GPU/Apple MLX | GGUF | Compile/build | TOP 2 — controle fino |
| **LM Studio** | Similar Ollama | Limitado | GUI | GGUF | GUI desktop | Descartar (não-server) |
| **TGI (HuggingFace)** | Alto | Alto | GPU | Carregamento longo | Docker | Descartar (overkill) |
| **MLC-LLM** | Alto em dispositivos edge | Variável | Multiplataforma | Compilar modelo | Complexo | Descartar (nicho) |

**Veredicto Atlas:**
- **Estratégia DUAL: Ollama em dev, vLLM em prod**
  - **Dev local (single user):** Ollama (proposta original) — confortável, 1 comando.
  - **Produção (1+ usuários ou múltiplos agentes paralelos):** vLLM — `vllm serve maritaca-ai/sabia-7b --quantization awq` e a degradação some.
- **Trade-off:** vLLM exige GPU NVIDIA com CUDA. Em CPU-only, manter Ollama + paralelizar agentes via fila (não simultaneamente no mesmo processo Python).
- **Sinal vermelho na sua proposta:** se o Perito e o Advogado puderem chamar Ollama **simultaneamente**, você vai ver `model loading` repetido + queue → tempo total dobra. Solução: **um único worker LLM** servindo todos os agentes via fila.

---

## 4. Modelos LLM para Jurídico PT-BR

### O problema
Llama 3 e Mistral 7B (sua escolha) são genéricos e fluentes em PT-BR de forma OK — mas para análise jurídica + compliance com pedidos estruturados (function calling para tool BACEN), o ganho de modelos especializados é significativo.

### Comparativo

| Modelo | Tamanho | PT-BR | Jurídico | Function Calling | Open + Local | OAB Performance | Veredicto |
|--------|---------|-------|----------|------------------|-------------|-----------------|-----------|
| **Llama 3 / 3.1 8B** (proposta) | 8B | OK genérico | Fraco — "closer to lawyers, not GPT-4o level" ([LegalBench.PT](https://arxiv.org/html/2502.16357v1)) | Sim (3.1+) | ✅ | Mediano | TOP 3 |
| **Mistral 7B** (proposta) | 7B | OK | Fraco | Sim | ✅ | Mediano | TOP 3 |
| **Sabia-7B** (Maritaca) | 7B | **Excelente — treino PT-BR específico** | Razoável (não-jurídico-específico) | Limitado | ✅ GGUF disponível ([HuggingFace](https://huggingface.co/maritaca-ai/sabia-7b), [TheBloke GGUF](https://huggingface.co/TheBloke/sabia-7B-GGUF)) | Bom | **TOP 1 — gen** |
| **Sabia-3 / Sabia-4** | API only | Top — comparável GPT-4o em 64 exames brasileiros ([Maritaca](https://x.com/MaritacaAI/status/1809212778957164970)) | **Top** — Sabiazinho-3 supera gpt-4o-mini em essays jurídicos ([Rabula](https://ceur-ws.org/Vol-4089/paper6.pdf)) | Sim | ❌ **API paga — viola LGPD/local** | Top | **❌ DESCARTAR — viola princípio** |
| **Qwen 2.5 7B** | 7B | **Supera Llama 3.1 8B em ~10pts em PT** ([PoETa v2](https://arxiv.org/html/2511.17808)) | Genérico bom | Sim, robusto | ✅ | Bom | **TOP 2** |
| **Llama 3.1 70B Q4** | 70B (Q4 ~22GB VRAM) | Bom | Bom | Sim | ✅ | Muito bom | TOP se houver GPU 24GB+ |
| **Phi-3 (mini/medium)** | 3.8B / 14B | Razoável | Fraco | Sim | ✅ | Mediano | Descartar (PT-BR limitado) |
| **DeepSeek R1 distilled** | 7-32B | OK | Excelente reasoning | Sim | ✅ | [verificar OAB] | **TOP 2 reasoning** — para o Juiz Revisor |
| **Bode-7B** | 7B (LoRA Llama 2) | OK | Fraco | Limitado | ✅ | Mediano | Descartar (geração antiga) |
| **Cabrita** | 3B (Apache 2.0) | OK | Fraco | Limitado | ✅ | Inferior | Descartar (geração antiga) |
| **JurisBERT / Legal-BERTimbau** | Encoder | n/a (encoder) | **TOP — treinado em jurídico BR** ([HuggingFace](https://huggingface.co/rufimelo/Legal-BERTimbau-sts-large)) | n/a | ✅ | n/a | **TOP 1 — embeddings** (não generativo) |

**Veredicto Atlas — arquitetura híbrida de modelos:**

| Função | Modelo recomendado | Tamanho | Razão |
|--------|-------------------|--------|-------|
| **Generativo geral** (Perito conversa, Advogado redige tese) | **Sabia-7B-GGUF** ou **Qwen 2.5 7B** | 7B Q4 (~5GB) | PT-BR superior |
| **Reasoning** (Juiz Revisor 3 checagens) | **DeepSeek R1 7B distilled** | 7B Q4 | Reasoning forte; verificar OAB |
| **Embeddings RAG** (Bloco 3) | **Legal-BERTimbau-large** (rufimelo) | encoder ~330MB | Único PT-BR jurídico open |
| **Fallback/genérico** | **Llama 3.1 8B Instruct** | 8B Q4 | Function calling robusto, baseline |

**Patch crítico:** descartar **Llama 3 / Mistral genéricos como única opção**. Usar **Sabia-7B** ou **Qwen 2.5 7B** como backbone gerador. Isso é gratuito, melhora qualidade mensurável em PT-BR jurídico, sem violar princípio local.

---

## 5. Vector Store para RAG Jurídico com Metadados Estritos

### O problema
Sua *Regra de Consulta* é o coração do RAG: `WHERE court_id IN ["TJMG", "STJ", "STF"] AND binding == True`. Esses filtros precisam ser **rápidos e exatos**. Vector DB lento em filter = LLM recebendo lixo de outros estados.

### Comparativo

| Opção | Filtros payload | Hybrid search (BM25+dense) | Persistência local | Setup | Filter overhead | Veredicto |
|-------|----------------|---------------------------|-------------------|-------|----------------|-----------|
| **ChromaDB** (proposta) | Sim, mas **3-8× overhead** ([CallSphere 2026](https://callsphere.ai/blog/vector-database-benchmarks-2026-pgvector-qdrant-weaviate-milvus-lancedb)) | ❌ Não nativo | Sim (sqlite) | Trivial | 🔴 Alto | TOP 3 — só p/ POC |
| **Qdrant** (proposta) | **Boolean nesting recursivo, exact match em keyword/int/bool** ([Qdrant docs](https://qdrant.tech/documentation/search/filtering/)), **1.1× overhead** | ✅ Native v1.9+ (sparse + dense) | Sim (file-based) | Docker ou embedded | 🟢 Baixo | **TOP 1 — fit perfeito** |
| **LanceDB** | Sim, eficiente | ✅ Native | Sim (Lance file format) | Embedded (sem server) | 🟢 Baixo | **TOP 2 — embedded** |
| **PgVector** | Sim, mas 2.3× overhead text | ❌ Plain (extensão pg_search) | Sim (Postgres) | Postgres já existir | 🟡 Médio | TOP se Postgres já é stack |
| **Weaviate** | Sim | ✅ Native | Sim | Mais pesado | 🟢 Baixo | Overkill |
| **Milvus 2.5+** | Sim | ✅ Native | Sim | Complexo | 🟢 Baixo | Overkill |

**Veredicto Atlas:**
- **TOP 1: Qdrant** — **ideal para seu caso**:
  - Filter cardinality estimation (escolhe HNSW vs payload-index automático)
  - Boolean nesting recursivo permite `WHERE (court_id IN [...]) AND binding == True AND year >= 2020`
  - Sparse + dense vectors em **named vectors** (mesmo collection) — busca híbrida nativa
  - Embedded mode (sem servidor) ou via Docker
  - **CRÍTICO:** Criar payload index em `court_id`, `binding`, `legal_topic` para filtros rápidos
- **TOP 2: LanceDB** — embedded puro (zero infra), bom para single-user.
- **Descartar ChromaDB para produção** — overhead de filtro 3-8× é incompatível com a Regra de Consulta crítica do Bloco 3. Usar só em prototipagem.

### Patch crítico
```python
# bloco_vault/motor_busca/retriever.py
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue

# Indexar metadados ANTES de qualquer ingestão volume
client.create_payload_index(collection_name="jurisprudencia", field_name="court_id", field_schema="keyword")
client.create_payload_index(collection_name="jurisprudencia", field_name="binding", field_schema="bool")

filtro = Filter(
    must=[
        FieldCondition(key="court_id", match=MatchAny(any=["TJMG", "STJ", "STF"])),
        FieldCondition(key="binding", match=MatchValue(value=True))
    ]
)
```

---

## 6. Embeddings PT-BR

### O problema
"HuggingFace Sentence-Transformers genérico" (sua proposta) é multilíngue mas não jurídico-específico. Em domínio legal, embeddings genéricos retornam falsos positivos por similaridade superficial ("contrato de aluguel" ≈ "contrato de trabalho").

### Comparativo

| Opção | PT-BR | Jurídico | Dimensões | Hybrid (sparse) | Velocidade local | Veredicto |
|-------|-------|----------|----------|-----------------|------------------|-----------|
| **Sentence-Transformers genérico** (proposta — ex: paraphrase-multilingual-MiniLM) | OK multilíngue | ❌ Não-jurídico | 384 | ❌ | Rápido | TOP 3 |
| **BGE-M3** (BAAI) | Excelente em 100+ línguas ([HuggingFace](https://huggingface.co/BAAI/bge-m3)) | Genérico forte | 1024, contexto 8192 | ✅ Dense + sparse + multi-vector | Médio | **TOP 1 — fallback geral** |
| **E5-large-multilingual** | Bom | Genérico | 1024 | ❌ | Médio | TOP 3 |
| **Legal-BERTimbau-large** ([rufimelo](https://huggingface.co/rufimelo/Legal-BERTimbau-large)) | **Pré-treinado em 30k docs jurídicos PT** | **TOP — única opção PT-BR jurídico open** | 1024 | ❌ | Rápido (BERT-base size) | **TOP 1 — para jurídico** |
| **Legal-BERTimbau-sts-large** | Mesmo + fine-tuned STS (similaridade) | TOP | 1024 | ❌ | Rápido | **TOP 1 alternativa** — uso direto STS |
| **JurisBERT** | OK | F1 79.61% (vs Legal-BERTimbau 83.78%) | 768 | ❌ | Rápido | TOP 2 |
| **Jina v3** | Excelente | Genérico | 1024, modular | ✅ | Médio | TOP 2 fallback |
| **OpenAI text-embedding-3** | Excelente | Genérico | 3072 | ❌ | API cloud | **❌ Descartar — viola LGPD** |

**Veredicto Atlas — pipeline híbrido de embeddings:**
1. **Embedding primário:** `rufimelo/Legal-BERTimbau-sts-large` — único modelo PT-BR especializado em jurídico, com STS fine-tune ideal para retrieval por similaridade.
2. **Embedding sparse complementar:** BM25 (Okapi) implementado em Python (não precisa de modelo) — captura termos exatos jurídicos (números de leis, súmulas).
3. **Re-ranking:** BGE-M3 multi-vector ou cross-encoder Legal-BERTimbau para top-20 → top-5.
4. **Descartar:** Sentence-Transformers genérico como única opção (qualidade muito inferior em domínio).

### Custos
- Legal-BERTimbau-large: ~330MB no disco, roda em CPU (sem GPU) com latência ~10-50ms/query.
- BGE-M3: ~2.2GB, roda em CPU mas mais lento (~100-300ms/query). GPU recomendada.
- Total custo: **R$ 0** (Apache 2.0 / MIT licenses).

---

## 7. Parsing PDF Jurídico/Contratual

### O problema
Contratos bancários têm **tabelas de amortização** (centenas de linhas Price), cláusulas em colunas, OCR ruim em PDFs escaneados, e numeração quebrada. Marker (sua proposta) é bom mas não o melhor para tabelas complexas.

### Comparativo

| Opção | Tabelas complexas | OCR | Velocidade | Layout fidelity | Memory footprint | Veredicto |
|-------|------------------|-----|-----------|-----------------|-----------------|-----------|
| **Marker** (proposta) | Bom — Surya OCR 90+ línguas, mas split de merged cells ([CodeCut](https://codecut.ai/docling-vs-marker-vs-llamaparse/)) | Sim | ~2× Docling speed | Bom | Médio | **TOP 1 — balanceado** |
| **Docling** (IBM) | **97.9% accuracy, TableFormer model preserva merged cells** ([CodeCut](https://codecut.ai/docling-vs-marker-vs-llamaparse/)) | Sim | ~4s/página (lento) | **TOP — DoclingDocument com semântica** | Alto (modelos maiores) | **TOP 1 — para contratos com Price** |
| **MarkItDown** (MS) | ❌ Fraco — "basic text scraper" ([Systenics](https://systenics.ai/blog/2025-07-28-pdf-to-markdown-conversion-tools/)) | Limitado | Rápido | Baixo | Baixo | Descartar p/ tabelas |
| **PyMuPDF4LLM** | ❌ Tabelas distorcidas | Não nativo | **0.12s/pg — ultra rápido** | Bom texto | Baixo | TOP 2 — fallback texto |
| **Unstructured.io** | Bom | Sim | Médio | Bom | Médio | TOP 3 |
| **LlamaParse** | TOP, mas **API cloud** | Sim | API | TOP | API | **❌ Descartar — viola LGPD** |
| **MinerU** | Excelente para científico | Sim | Médio | Bom | Médio | TOP 2 alternativa |

**Veredicto Atlas — pipeline híbrido de parsing:**

| Cenário | Tool | Razão |
|---------|------|-------|
| **PDF nativo (digital) com tabela Price** | **Docling** | Único com 97.9% accuracy em tabelas; preserva merged cells (crítico para colunas "Saldo Devedor", "Juros", "Amortização") |
| **PDF escaneado (precisa OCR)** | **Marker** (Surya OCR) | Suporta PT-BR robustamente |
| **Texto puro rápido (não-financeiro)** | **PyMuPDF4LLM** | 30× mais rápido que Docling, ideal p/ cláusulas textuais |
| **Fallback** | Unstructured.io | Se outros falharem |

**Patch arquitetural:**
```python
# bloco_engine/extratores/pdf_parser_marker.py → renomear para pdf_parser.py
def extrair_contrato(pdf_path):
    # 1. Detectar se tem tabela financeira (heurística: > 5 linhas com R$, %, juros)
    if detectar_tabela_amortizacao(pdf_path):
        return docling_parse(pdf_path)  # accuracy crítica
    elif detectar_pdf_escaneado(pdf_path):
        return marker_parse(pdf_path)   # OCR
    else:
        return pymupdf4llm_parse(pdf_path)  # rápido
```

---

## 8. Integração BACEN SGS

### O problema
Sua arquitetura prevê chamada à API SGS por contrato. Sem caching e retry, isso vai falhar em produção (rate limit, API down, latência).

### Best Practices

#### Bibliotecas Python recomendadas
| Lib | Pros | Contras | Recomendação |
|-----|------|---------|--------------|
| **`python-bcb`** ([wilsonfreitas](https://wilsonfreitas.github.io/python-bcb/sgs.html)) | Maior cobertura, retorna pandas DataFrame, ativa | Sintaxe própria | **TOP 1** |
| **`sgs`** ([PyPI](https://pypi.org/project/sgs/)) | Wrapper minimalista | Menos features | TOP 2 |
| HTTP raw (`requests` + URL `/dados/serie/bcdata.sgs.{codigo}/dados`) | Total controle | Requer parsing | TOP 3 (controle máximo) |

#### Códigos BACEN SGS úteis (verificar oficial em [SGS](https://www3.bcb.gov.br/sgspub/))

| Indicador | Código SGS | Periodicidade | Status |
|-----------|------------|--------------|--------|
| Selic diária | 11 | diária | Confirmado ([dados abertos](https://dadosabertos.bcb.gov.br/dataset/11-taxa-de-juros---selic/)) |
| IPCA mensal | 433 | mensal | Confirmado |
| Taxa juros PF — Aquisição veículos (média mensal) | **25471** | mensal | Confirmado ([dados abertos](https://dadosabertos.bcb.gov.br/dataset/25471-taxa-media-mensal-de-juros-das-operacoes-de-credito-com-recursos-livres---pessoas-fisicas---a/)) |
| Taxa juros PF — Aquisição veículos (média geral) | 20749 | mensal | Confirmado |
| Taxa juros PF — Crédito pessoal não-consignado | 20748 | mensal | [verificar] |
| Taxa juros PF — Cartão de crédito rotativo | 20741 | mensal | [verificar] |
| Taxa juros PF — Financiamento imobiliário | [verificar] | mensal | Consultar SGS |
| Taxa juros PF — CDC bens não-veículo | [verificar] | mensal | Consultar SGS |

> ⚠️ **Verificação obrigatória:** códigos podem mudar. Consultar [SGS Search Portal](https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do) na implementação. Caching dos códigos em `bloco_engine/ferramentas_calculo/codigos_bacen.yaml`.

#### Padrão "não trava" para BACEN

| Risco | Mitigação |
|-------|-----------|
| API BACEN down | Cache local (Redis ou SQLite) com TTL 30 dias para taxas históricas (não mudam) |
| Rate limit não-documentado | Backoff exponencial: 1s, 2s, 4s, 8s, 16s |
| Latência alta (5-10s) | Pre-fetch das taxas no upload do contrato (paralelo ao parsing) |
| Resposta inválida | Validação Pydantic do schema retornado |

```python
# bloco_engine/ferramentas_calculo/calculadora_bacen_sgs.py
import diskcache
from tenacity import retry, stop_after_attempt, wait_exponential

cache = diskcache.Cache("./bloco_engine/cache_bacen")

@retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=16))
def get_taxa_bacen(codigo_serie: int, data: str) -> float:
    cache_key = f"{codigo_serie}:{data}"
    if cache_key in cache:
        return cache[cache_key]
    # ... chamada bcb.sgs.get(codigo_serie) ...
    cache.set(cache_key, valor, expire=30*24*3600)  # 30 dias
    return valor
```

---

## 9. Padrão "Não Trava" — Async + Queue

### O problema
Sua arquitetura é **síncrona implícita** (Streamlit chama LangGraph chama Ollama chama RAG chama BACEN). Qualquer um dos 5 lentifica → toda a UI congela. Em produção real (mesmo single-user), isso quebra.

### Comparativo

| Padrão | Latência percebida | Complexidade | Reliability | Veredicto |
|--------|-------------------|--------------|------------|-----------|
| **Síncrono Streamlit direto** (proposta implícita) | 🔴 Trava UI | Baixa | Frágil | **❌ Não usar em prod** |
| **Streamlit + thread async (`asyncio`)** | 🟡 OK | Média | Médio (GIL issues) | TOP 3 |
| **FastAPI backend + Celery + Redis broker** | 🟢 Robusto | Alta | TOP — ack-late, retry, monitoring (Flower) | TOP 2 |
| **FastAPI + Dramatiq + Redis** | 🟢 Robusto | **Média** | **TOP — ack-on-completion (default), 10× mais rápido que RQ** ([Dramatiq motivation](https://dramatiq.io/motivation.html)) | **TOP 1** |
| **FastAPI + RQ + Redis** | 🟡 OK | Baixa | Baixo (sem retry built-in robusto) | TOP 3 simplicidade |
| **Redis Streams puro** | 🟢 OK | Alta | Alto, exige código próprio | Só p/ caso muito custom |
| **Temporal** | 🟢 TOP | Muito alta | TOP enterprise | Overkill |

**Veredicto Atlas — arquitetura assíncrona recomendada:**

```
┌─────────────────────────────────────────────────────────────┐
│  NiceGUI (Frontend) — websocket nativo                      │
│  ├─ Upload PDF + UF → POST /processar                       │
│  └─ SSE stream do status → render Painel Intervenção        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI (API Layer)                                         │
│  ├─ Recebe upload, valida, salva PDF                        │
│  ├─ Enqueue task Dramatiq                                   │
│  └─ Retorna task_id → cliente faz long-poll/SSE             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Dramatiq Workers (background — N processos)                │
│  ├─ Worker 1: Parsing PDF (Docling/Marker)                  │
│  ├─ Worker 2: Workflow LangGraph (com checkpointer)         │
│  ├─ Worker 3: BACEN fetch (com cache)                       │
│  └─ Publish progresso → Redis pub/sub                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Redis (broker + cache + pub/sub)                            │
│  ├─ Queue Dramatiq                                          │
│  ├─ Cache BACEN (diskcache pode substituir p/ single-host)  │
│  └─ Pub/sub para SSE → frontend                             │
└─────────────────────────────────────────────────────────────┘
```

#### Sinais clínicos de travamento (a evitar)
| Cenário | Sintoma | Mitigação |
|---------|---------|----------|
| PDF 80+ pgs | Streamlit "Running..." infinito | Workers Dramatiq + parsing async |
| Ollama lento (cold start) | Toda UI parada | Worker dedicado LLM, limit `concurrency=1` |
| API BACEN timeout | Travamento sequencial | Cache + retry + fallback "última taxa conhecida" |
| RAG miss (zero docs) | Espera infinita | Timeout 5s, fallback para Relatório de Inviabilidade |
| Crash mid-workflow | Perde tudo | LangGraph `SqliteSaver` permite resume |

---

## 10. TCO — Hardware Mínimo & Custos

### Cenários

#### Cenário A — Solo dev (sua máquina) — **R$ 0/mês**
| Componente | Recomendação |
|-----------|--------------|
| CPU | Ryzen 7 / i7 (8+ cores) |
| RAM | 32GB (16GB mínimo p/ Sabia-7B Q4 + Qdrant + workers) |
| GPU | **Opcional** RTX 3060 12GB — acelera Ollama mas não obrigatório |
| Disco | SSD 256GB (modelos: ~10-20GB; vault Qdrant: 5-50GB conforme jurisprudência) |
| Custo recorrente | **R$ 0** (eletricidade marginal) |

#### Cenário B — VPS produção single-tenant — **R$ 200-600/mês**
| Componente | Recomendação |
|-----------|--------------|
| VPS | Hetzner CCX33 (8 vCPU, 32GB RAM) ou similar | R$ ~250/mês |
| GPU | **Não viável em VPS comum** — usar Ollama CPU-mode ou serverless GPU on-demand |
| Storage | +100GB SSD | R$ ~50/mês |
| Total | **R$ 200-600/mês** | depende do provider |

#### Cenário C — Workstation dedicada (recomendado) — **R$ 8-15k upfront, R$ 30-50/mês**
| Componente | Recomendação |
|-----------|--------------|
| CPU | Ryzen 9 7900X / i9-13900K |
| RAM | 64GB DDR5 |
| GPU | **RTX 4070 Ti Super 16GB** (R$ ~7.000) — roda Sabia-7B Q4 + Legal-BERTimbau + vLLM com folga |
| GPU alternativa | RTX 3090 24GB usada (R$ ~5.000) — permite Llama 3.1 70B Q4 |
| Disco | NVMe 2TB |
| Total upfront | R$ 12-15k |
| Recorrente | R$ 30-50/mês (eletricidade ~200W médio) |

### Comparação com SaaS LegalTech (referência)
- Linte / Contraktor / Docket: R$ 200-800/usuário/mês para revisão de contratos.
- **Break-even** workstation Cenário C vs SaaS @ R$ 500/mês: **24-30 meses** se uso solo. Para escritório com 3+ usuários, payback é < 12 meses.

---

## 🎯 Stack Recomendada Final (vs Stack Proposta)

### Comparação lado-a-lado

| Camada | **Sua proposta** | **Recomendação Atlas** | Razão da mudança |
|--------|-----------------|-----------------------|------------------|
| **Frontend** | Streamlit | **NiceGUI** OU **Streamlit + FastAPI separados** | Streamlit single-thread trava em workflow longo |
| **Orquestração** | LangGraph | **LangGraph + SqliteSaver** | Adicionar checkpointer para resume após crash |
| **LLM Serving (dev)** | Ollama | **Ollama** (manter) | OK para dev solo |
| **LLM Serving (prod)** | (não definido) | **vLLM** | 16.6× throughput, não quebra em concorrência |
| **Modelo gerador** | Llama 3 / Mistral 7B | **Sabia-7B-GGUF** ou **Qwen 2.5 7B** | PT-BR especializado, mesmo footprint |
| **Modelo reasoning (Juiz)** | (mesmo gerador) | **DeepSeek R1 7B distilled** (opcional) | Reasoning superior para validação 100% aderência |
| **Vector Store** | ChromaDB ou Qdrant | **Qdrant** (com payload index) | 1.1× overhead vs Chroma 3-8× |
| **Embeddings** | Sentence-Transformers genérico | **Legal-BERTimbau-sts-large** (rufimelo) + BM25 sparse | Único PT-BR jurídico open |
| **PDF parsing primário** | Marker | **Docling** para tabelas de amortização | 97.9% accuracy em tabelas complexas |
| **PDF parsing OCR** | Marker | **Marker** (manter) | OCR Surya excelente |
| **Math** | NumPy Financial | **NumPy Financial** (manter) | TOP — não inventar |
| **BACEN** | API direta | **`python-bcb`** + `diskcache` + `tenacity` | Caching + retry obrigatórios |
| **Pattern execução** | Síncrono (Streamlit → LangGraph) | **FastAPI + Dramatiq + Redis** | Não trava + retry + reliability |

---

## 🧬 3 Arquiteturas Sintetizadas (para escolha do PO/Eric)

### Arquitetura A — Sua Proposta (mantida)
**Stack:** Streamlit + LangGraph + Ollama + ChromaDB + Sentence-Transformers + Marker + NumPy + BACEN sync.

**Pros:** Setup mais rápido, menos componentes, comunidade enorme.
**Contras:** Trava em produção real, embeddings/Chroma fracos para filtro jurídico, modelo genérico.
**Quando usar:** POC inicial / prova de conceito de 1 contrato.

### Arquitetura B — Recomendação Atlas (aggressive upgrade)
**Stack:** NiceGUI + FastAPI + Dramatiq + Redis + LangGraph(SqliteSaver) + Ollama(dev)/vLLM(prod) + Sabia-7B + Qdrant + Legal-BERTimbau + Docling/Marker/PyMuPDF4LLM + python-bcb+cache.

**Pros:** Não trava, qualidade jurídica superior, escala para multi-tenant, audit trail via LangGraph state.
**Contras:** Mais peças (curva de setup), exige aprender NiceGUI + Dramatiq.
**Quando usar:** Produção real desde o MVP — fundação que escala.

### Arquitetura C — Híbrido Pragmático (sugestão de equilíbrio)
**Stack mínimo viável robusto:**
- **UI:** Streamlit (mantém — é o que você sabe), MAS **off-loadar workflow para FastAPI atrás de fila**
- **Orquestração:** LangGraph + SqliteSaver (patch crítico — adicionar checkpointer)
- **LLM:** Ollama com **Sabia-7B-GGUF** (substitui Llama 3) — mesma infra, melhor PT-BR
- **Vector:** Qdrant embedded (sem servidor) — substitui ChromaDB direto, mantém simplicidade
- **Embeddings:** Legal-BERTimbau-sts-large (single model upgrade)
- **PDF:** Docling **se** tabela financeira detectada, senão Marker (heurística simples)
- **BACEN:** python-bcb + diskcache local + tenacity retry
- **Async:** FastAPI + RQ (mais simples que Dramatiq) + Redis local
- **Math:** NumPy Financial (mantém)

**Pros:** Mantém familiaridade Streamlit + faz upgrades cirúrgicos onde dói (modelo PT-BR, vector filter, parsing tabelas, async). Mínima mudança conceitual.
**Contras:** Pesa um pouco mais que A; menos performant que B em escala.
**Quando usar:** **Recomendação default** — best balance esforço × qualidade.

---

## 📋 Recomendação Final (do Atlas)

> **Adotar Arquitetura C (Híbrido Pragmático)** como ponto de partida. Migrar componentes para Arquitetura B sob demanda quando sentir os limites:
>
> - Quando UI travar em multi-user → migrar Streamlit → NiceGUI
> - Quando RQ não der vazão → migrar para Dramatiq
> - Quando Ollama queue degradar → migrar para vLLM
>
> **Decisões inegociáveis** (independente da arquitetura escolhida):
> 1. **Trocar modelo gerador** Llama 3 → Sabia-7B (qualidade PT-BR mensurável)
> 2. **Trocar embeddings** Sentence-Transformers → Legal-BERTimbau (jurídico-específico)
> 3. **Trocar vector store** ChromaDB → Qdrant (filtros 3-8× mais rápidos)
> 4. **Adicionar SqliteSaver** ao LangGraph (resume após crash)
> 5. **Adicionar caching BACEN** com diskcache + retry
> 6. **PDF: usar Docling** se detectar tabela financeira

---

## 🔗 Fontes Consultadas

### LLMs & Modelos PT-BR
- [Maritaca AI — Pesquisa em LLM Português](https://www.maritaca.ai/en/pesquisa)
- [Sabiá-4 Technical Report (arXiv 2603.10213)](https://arxiv.org/html/2603.10213v1)
- [Sabiá-3 Technical Report (arXiv 2410.12049)](https://arxiv.org/abs/2410.12049)
- [Sabiá-2 Technical Report (arXiv 2403.09887)](https://arxiv.org/html/2403.09887)
- [Maritaca Sabia-7B HuggingFace](https://huggingface.co/maritaca-ai/sabia-7b)
- [TheBloke Sabia-7B-GGUF](https://huggingface.co/TheBloke/sabia-7B-GGUF)
- [Juru: Legal Brazilian LLM (arXiv 2403.18140)](https://arxiv.org/html/2403.18140v1)
- [Rabula: Brazilian Legal Benchmark (CEUR-WS Vol-4089)](https://ceur-ws.org/Vol-4089/paper6.pdf)
- [LegalBench.PT (arXiv 2502.16357)](https://arxiv.org/html/2502.16357v1)
- [PoETa v2 — Robust PT Evaluation (arXiv 2511.17808)](https://arxiv.org/html/2511.17808)
- [TeenyTinyLlama (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S2666827024000343)
- [Bode-7B-alpaca-pt-br (HF)](https://huggingface.co/recogna-nlp/bode-7b-alpaca-pt-br)
- [Portuguese-NLP curated list](https://github.com/ajdavidl/Portuguese-NLP)

### LLM Serving
- [Ollama vs vLLM Performance Benchmark — Red Hat 2025](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking)
- [Ollama vs vLLM Performance Benchmark 2026 — SitePoint](https://www.sitepoint.com/ollama-vs-vllm-performance-benchmark-2026/)
- [Ollama vs vLLM vs llama.cpp — TechPlained](https://www.techplained.com/ollama-vs-vllm-vs-llamacpp)
- [vLLM vs Ollama — Northflank](https://northflank.com/blog/vllm-vs-ollama-and-how-to-run-them)

### Orquestração de Agentes
- [LangGraph vs CrewAI vs AutoGen — DataCamp](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen)
- [Top 5 AI Agent Frameworks 2026 — Intuz](https://www.intuz.com/blog/top-5-ai-agent-frameworks-2025)
- [Burr (DAGWorks) PyPI](https://pypi.org/project/burr/)
- [Burr — Building Interactive Agents (DAGWorks blog)](https://blog.dagworks.io/p/building-interactive-agents-with)

### Vector Stores
- [Vector Database Benchmarks 2026 — CallSphere](https://callsphere.ai/blog/vector-database-benchmarks-2026-pgvector-qdrant-weaviate-milvus-lancedb)
- [Vector Database Comparison 2026 — 4xxi](https://4xxi.com/articles/vector-database-comparison/)
- [Qdrant Filtering Documentation](https://qdrant.tech/documentation/search/filtering/)
- [Qdrant Hybrid Search Article](https://qdrant.tech/articles/vector-search-filtering/)
- [Best Vector Databases — Encore](https://encore.dev/articles/best-vector-databases)

### Embeddings PT-BR
- [Legal-BERTimbau-large (rufimelo)](https://huggingface.co/rufimelo/Legal-BERTimbau-large)
- [Legal-BERTimbau-sts-large](https://huggingface.co/rufimelo/Legal-BERTimbau-sts-large)
- [Legal-bert-base-cased-ptbr (dominguesm)](https://huggingface.co/dominguesm/legal-bert-base-cased-ptbr)
- [BAAI/bge-m3 HuggingFace](https://huggingface.co/BAAI/bge-m3)
- [BGE-M3 Documentation](https://bge-model.com/bge/bge_m3.html)
- [RoBERTaLexPT (PROPOR 2024)](https://aclanthology.org/2024.propor-1.38.pdf)

### PDF Parsing
- [Docling vs Marker vs LlamaParse — CodeCut](https://codecut.ai/docling-vs-marker-vs-llamaparse/)
- [Best Open Source PDF-to-Markdown — Jimmy Song](https://jimmysong.io/blog/pdf-to-markdown-open-source-deep-dive/)
- [PDF to Markdown Comparison — Systenics](https://systenics.ai/blog/2025-07-28-pdf-to-markdown-conversion-tools/)
- [PyMuPDF4LLM Documentation](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/)
- [Marker GitHub (datalab-to)](https://github.com/datalab-to/marker)
- [PDF Data Extraction Benchmark — Procycons](https://procycons.com/en/blogs/pdf-data-extraction-benchmark/)

### BACEN SGS
- [python-bcb Documentation](https://wilsonfreitas.github.io/python-bcb/)
- [SGS Module — python-bcb](https://wilsonfreitas.github.io/python-bcb/sgs.html)
- [sgs PyPI Package](https://pypi.org/project/sgs/)
- [BACEN Dados Abertos — Selic 11](https://dadosabertos.bcb.gov.br/dataset/11-taxa-de-juros---selic/)
- [BACEN Dados Abertos — Veículos PF 25471](https://dadosabertos.bcb.gov.br/dataset/25471-taxa-media-mensal-de-juros-das-operacoes-de-credito-com-recursos-livres---pessoas-fisicas---a/)
- [SGS Search Portal (oficial)](https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do)
- [Coletando Dados BC com Python — Análise Macro](https://analisemacro.com.br/economia/indicadores/coletando-dados-do-banco-central-com-python/)

### Async / Task Queues
- [Celery vs Dramatiq vs RQ — Judoscale](https://judoscale.com/blog/choose-python-task-queue)
- [Python Task Queue Load Test — Steven Yue](https://stevenyue.com/blogs/exploring-python-task-queue-libraries-with-load-test)
- [Dramatiq Motivation](https://dramatiq.io/motivation.html)
- [Async Task Patterns Django — Hash Block](https://medium.com/@connect.hashblock/async-task-patterns-in-django-choosing-between-celery-dramatiq-and-rq-bb14339291fc)

### Frontend
- [Streamlit vs Gradio vs NiceGUI vs Mesop — Mani Kolbe Medium](https://medium.com/@manikolbe/streamlit-gradio-nicegui-and-mesop-building-data-apps-without-web-devs-4474106778f5)
- [Streamlit vs NiceGUI — Bitdoze](https://www.bitdoze.com/streamlit-vs-nicegui/)
- [Streamlit vs Gradio vs Chainlit (2026)](https://medium.com/@atnoforgenai/streamlit-vs-gradio-vs-chainlit-building-quick-uis-for-your-ai-applications-138e3baa5317)
- [Mesop GitHub (Google)](https://github.com/mesop-dev/mesop)

### Hardware / TCO
- [Ollama VRAM Requirements 2026 — LocalLLM.in](https://localllm.in/blog/ollama-vram-requirements-for-local-llms)
- [GPU Requirement Guide Llama 3 — apxml](https://apxml.com/posts/ultimate-system-requirements-llama-3-models)
- [Mistral 7B System Requirements](https://www.oneclickitsolution.com/centerofexcellence/aiml/run-mistral-7b-locally-hardware-software-specs)
- [Local LLM Hardware Guide 2026 — Apatero](https://apatero.com/blog/running-open-source-llms-locally-hardware-guide-2026)

---

## ⚠️ Itens Marcados [verificar]

Dados que requerem confirmação antes de virar decisão arquitetural:

1. **Códigos BACEN específicos** para CDC bens não-veículo, financiamento imobiliário PF, cartão rotativo — confirmar em [SGS Search](https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do) durante implementação.
2. **Benchmark direto Sabia-7B vs Qwen 2.5 7B em jurídico PT-BR** — não encontrado benchmark público específico; rodar piloto interno com 50 contratos antes de fixar modelo.
3. **DeepSeek R1 distilled em OAB** — não há benchmark público; testar antes de adotar para Juiz Revisor.
4. **Performance Legal-BERTimbau-large com filtros pesados de payload Qdrant** — testar localmente com vault de 10k+ docs sintéticos.
5. **Latência real do pipeline end-to-end** — só medível após implementação. Meta: contrato de 30 páginas processado em < 5 min em workstation Cenário C.

---

## 📌 Handoff para Próximas Skills

**Próxima Skill recomendada:** `LMAS:agents:architect` (Aria)
**Missão para Aria:** Receber este research + spec original do `.project.yaml` e produzir **arquitetura B (Atlas)** vs **arquitetura A (proposta)** vs **arquitetura C (híbrida)** como **SAD formal** com ADRs por decisão crítica + tradeoff matrix.

**Em seguida:** `LMAS:agents:smith` para adversarial review das 3 arquiteturas — atacar pontos cegos, fragilidades, e vetores de travamento que Atlas/Aria possam ter perdido.

---

*Atlas, decifrando os caminhos antes que sejam trilhados — 🔎*
