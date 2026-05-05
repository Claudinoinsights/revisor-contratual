---
type: decisions
title: "Revisor Contratual — Requisitos Estendidos (5 novos requisitos do Eric)"
project: revisor-contratual
author: "@analyst (Atlas)"
date: "2026-05-01"
trigger: "Eric — 5 informações importantes do projeto"
predecessor:
  - "decisions/architecture-D-lean-2026-05-01.md"
  - "decisions/quality-data-modularity-assurance-2026-05-01.md"
audience: ["Eric Claudino", "@architect (Aria)"]
tags:
  - project/revisor-contratual
  - extended-requirements
  - multi-uf
  - env-config
  - auth
  - shopping-list
  - ml-feedback-loop
---

# Requisitos Estendidos — 5 Novos Inputs do Eric

> Eric adicionou 5 requisitos importantes. Atlas analisa cada um, decide impacto na arquitetura D, e atualiza o plano.

---

## ⚡ Sumário Executivo

| # | Requisito | Impacto na Arq D | Effort |
|---|-----------|------------------|--------|
| **1** | **Multi-UF** (BA é seed, expansível) | 🟢 Já contemplado no design — só formalizar | Baixo |
| **2** | **`.env` para qualquer LLM aceitável** | 🟡 Estender — passa de 3 tiers para "qualquer modelo Ollama-compatible + cloud APIs opcional" | Médio |
| **3** | **Auth login/senha no `.env`** | 🟡 NOVO — adicionar `streamlit-authenticator` + bcrypt | Baixo |
| **4** | **Shopping list canônica** | 🟢 Consolidar docs existentes em 1 checklist | Baixo |
| **5** | **ML feedback loop (sucesso/derrota)** | 🔴 **REQUISITO NOVO IMPORTANTE** — adicionar `bloco_learning/` | Alto (fase 2) |

**Adicionar 1 bloco novo (`bloco_learning/`) → 7 blocos ao todo.**

---

## 🟦 Req 1 — Multi-UF Strategy (BA como ponto de partida)

### Decisão Atlas

**Garantia:** TODA a arquitetura D já é multi-UF por design. BA é apenas o **vault inicial** (seed); adicionar nova UF = rodar scraper + reindexar (ZERO código adicional).

### Implementação

#### Schema do vault (sqlite-vec) — UF como first-class field
```sql
CREATE TABLE jurisprudencia (
    id_doc TEXT PRIMARY KEY,
    court_id TEXT NOT NULL,           -- 'STF' | 'STJ' | 'TJBA' | 'TJMG' | 'TJSP' | ...
    binding INTEGER NOT NULL,          -- 0 | 1
    peso_vinculacao INTEGER NOT NULL,  -- 1-5
    legal_topic_principal TEXT,
    modalidade_relacionada TEXT,       -- JSON array
    ano_julgamento INTEGER,
    ementa TEXT,
    texto_completo TEXT,
    embedding BLOB,                    -- sqlite-vec
    indexed_at TEXT
);

CREATE INDEX idx_court ON jurisprudencia(court_id);  -- B-tree para filtro rápido
CREATE INDEX idx_binding ON jurisprudencia(binding);
CREATE INDEX idx_peso ON jurisprudencia(peso_vinculacao);
```

#### Filtros dinâmicos por UF do contrato
```python
# bloco_vault/retriever.py
def buscar_jurisprudencia(query: str, uf_contrato: str, top_k: int = 10):
    # UF do contrato + tribunais superiores (sempre incluídos)
    cortes_validas = ["STF", "STJ", f"TJ{uf_contrato.upper()}"]

    sql = """
        SELECT id_doc, court_id, peso_vinculacao, ementa, texto_completo,
               vec_distance_cosine(embedding, ?) as score
        FROM jurisprudencia
        WHERE court_id IN ({placeholders})
          AND binding = 1
        ORDER BY score
        LIMIT ?
    """.format(placeholders=",".join("?" * len(cortes_validas)))

    return db.execute(sql, [embedding_query, *cortes_validas, top_k]).fetchall()
```

#### Scraper parametrizado por UF
```python
# bloco_vault/seed/scrape_tj.py
def scrape_tj(uf: str, temas: list[str], output_path: Path):
    """
    Scraping de acórdãos do TJ{UF} para temas específicos.

    Uso:
        scrape_tj('BA', ['anatocismo', 'tabela_price'], 'seed/tj-ba.json')
        scrape_tj('SP', ['anatocismo', 'tabela_price'], 'seed/tj-sp.json')
    """
    base_url = f"https://jurisprudencia.tj{uf.lower()}.jus.br/"
    # ... lógica de scraping ...
```

#### Comando de adicionar UF (CLI)
```bash
# Adicionar TJSP ao vault — 1 comando
python -m bloco_vault.seed.add_uf --uf SP --temas anatocismo,tabela_price

# Reindexar
python -m bloco_vault.ingestao.pipeline_indexacao --uf SP
```

### Roadmap de UFs (sugestão)
| Fase | UFs | Tamanho vault |
|------|-----|--------------|
| **MVP (BA)** | TJBA + STF + STJ | ~3.000 docs |
| **Fase 2** | + TJSP, TJMG, TJRJ (3 maiores) | ~6.000 docs |
| **Fase 3** | + TJRS, TJPR, TJSC, TJBA, TJGO (top 8) | ~10.000 docs |
| **Cobertura nacional** | Todos os 27 TJs | ~50.000 docs |

**sqlite-vec aguenta TODAS essas fases** sem migração para Qdrant.

---

## 🟦 Req 2 + Req 3 — `.env` Completo (LLM + Auth)

### Decisão Atlas

**Suportar 3 categorias de LLM:**
1. **Local Ollama** (default — preserva 100% local LGPD)
2. **Local llama-cpp-python** (alternativa embedded sem Ollama)
3. **Cloud API** (OPCIONAL — com aviso explícito de violação LGPD)

**Auth via `streamlit-authenticator` + bcrypt** (padrão da comunidade Streamlit).

### Spec do `.env` final

```env
# ==============================================================================
# REVISOR CONTRATUAL — Configuração de Ambiente
# ==============================================================================

# ------------------------------------------------------------------------------
# AUTENTICAÇÃO (obrigatório)
# ------------------------------------------------------------------------------
# Usuário admin (único no MVP). Multi-user em fase 2.
AUTH_USERNAME=eric
AUTH_FULLNAME=Eric Claudino
AUTH_EMAIL=eric@claudinoinsights.com

# Senha hash bcrypt — gerar com: python -c "from streamlit_authenticator.utilities.hasher import Hasher; print(Hasher().hash('SUA_SENHA'))"
AUTH_PASSWORD_HASH=$2b$12$KIXHE...placeholder...

# Cookie de sessão (gerar random com: python -c "import secrets; print(secrets.token_urlsafe(32))")
AUTH_COOKIE_KEY=mude-este-valor-para-um-secret-aleatorio
AUTH_COOKIE_NAME=revisor_contratual_auth
AUTH_COOKIE_EXPIRY_DAYS=30

# ------------------------------------------------------------------------------
# LLM CONFIGURATION (escolha 1 de 3 providers)
# ------------------------------------------------------------------------------

# Provider: 'ollama' (default, local), 'llamacpp' (embedded local), 'openai_compatible' (cloud — VIOLA LGPD)
LLM_PROVIDER=ollama

# Modelo (depende do provider)
# Ollama: 'sabia-7b:q4_K_M', 'qwen2.5:7b-instruct-q4_K_M', 'qwen2.5:3b-instruct-q4_K_M', etc.
# llama-cpp: caminho para arquivo .gguf
# openai_compatible: 'gpt-4o-mini', 'claude-3-5-haiku', 'mistral-large', etc.
LLM_MODEL=sabia-7b:q4_K_M

# Endpoint (default Ollama local)
LLM_BASE_URL=http://localhost:11434/v1

# API Key (obrigatório só se LLM_PROVIDER=openai_compatible)
LLM_API_KEY=

# Aviso: setar LLM_PROVIDER=openai_compatible viola princípio "100% local" e expõe contratos a terceiros (RISCO LGPD)
# A app vai ALERTAR no startup se detectar provider cloud.
LLM_ALLOW_CLOUD_PROVIDER=false

# Parâmetros do LLM
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=4096
LLM_TIMEOUT_SECONDS=180

# ------------------------------------------------------------------------------
# EMBEDDINGS (default Legal-BERTimbau-base local)
# ------------------------------------------------------------------------------
EMBEDDING_MODEL=rufimelo/Legal-BERTimbau-sts-base
EMBEDDING_DEVICE=cpu  # ou 'cuda' se GPU disponível

# ------------------------------------------------------------------------------
# VAULT (sqlite-vec local)
# ------------------------------------------------------------------------------
VAULT_DB_PATH=./bloco_vault/database/jurisprudencia.db
VAULT_DEFAULT_UF=BA  # UF inicial — adicionar mais UFs via CLI
VAULT_TOP_K=10
VAULT_FALLBACK_RELAX_BINDING=true

# ------------------------------------------------------------------------------
# BACEN
# ------------------------------------------------------------------------------
BACEN_CACHE_PATH=./bloco_engine/cache_bacen
BACEN_CACHE_TTL_DAYS=30
BACEN_RETRY_MAX_ATTEMPTS=5

# ------------------------------------------------------------------------------
# AUDIT LOG
# ------------------------------------------------------------------------------
AUDIT_LOG_PATH=./bloco_audit/audit.jsonl
AUDIT_LOG_LEVEL=INFO

# ------------------------------------------------------------------------------
# ML FEEDBACK LOOP (Req 5 — fase 2)
# ------------------------------------------------------------------------------
ML_OUTCOMES_DB_PATH=./bloco_learning/outcomes.db
ML_ENABLE_FEEDBACK_COLLECTION=true   # coleta outcomes desde MVP (sem fine-tune ainda)
ML_ENABLE_FINE_TUNING=false          # ativar quando volume >= 100 outcomes
ML_FINE_TUNE_TRIGGER_THRESHOLD=100
```

### Provider abstraction (Python)
```python
# bloco_workflow/llm_provider.py
import os
from langchain_core.language_models import BaseChatModel

def get_llm() -> BaseChatModel:
    provider = os.getenv("LLM_PROVIDER", "ollama")
    model = os.getenv("LLM_MODEL", "sabia-7b:q4_K_M")

    if provider == "openai_compatible":
        if os.getenv("LLM_ALLOW_CLOUD_PROVIDER", "false").lower() != "true":
            raise ValueError(
                "LLM_PROVIDER=openai_compatible exige LLM_ALLOW_CLOUD_PROVIDER=true. "
                "ATENÇÃO: cloud provider VIOLA princípio '100% local' e expõe contratos. "
                "Setar com consciência do risco LGPD."
            )
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            base_url=os.getenv("LLM_BASE_URL"),
            api_key=os.getenv("LLM_API_KEY"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2"))
        )

    if provider == "llamacpp":
        from langchain_community.llms import LlamaCpp
        return LlamaCpp(
            model_path=model,  # path to .gguf
            n_ctx=int(os.getenv("LLM_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2"))
        )

    # default: ollama
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=model,
        base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.2"))
    )
```

### Auth via streamlit-authenticator
```python
# bloco_interface/auth.py
import streamlit as st
import streamlit_authenticator as stauth
import os

def get_authenticator() -> stauth.Authenticate:
    credentials = {
        "usernames": {
            os.getenv("AUTH_USERNAME"): {
                "name": os.getenv("AUTH_FULLNAME"),
                "email": os.getenv("AUTH_EMAIL"),
                "password": os.getenv("AUTH_PASSWORD_HASH"),
                "logged_in": False
            }
        }
    }

    return stauth.Authenticate(
        credentials=credentials,
        cookie_name=os.getenv("AUTH_COOKIE_NAME", "revisor_contratual_auth"),
        cookie_key=os.getenv("AUTH_COOKIE_KEY"),
        cookie_expiry_days=int(os.getenv("AUTH_COOKIE_EXPIRY_DAYS", "30"))
    )

# bloco_interface/app.py
def main():
    authenticator = get_authenticator()
    authenticator.login(location="main")

    if st.session_state.get("authentication_status") is False:
        st.error("Usuário ou senha incorretos")
        return
    if st.session_state.get("authentication_status") is None:
        st.warning("Por favor, faça login")
        return

    # Usuário autenticado — render app
    authenticator.logout(location="sidebar")
    st.success(f"Bem-vindo, {st.session_state['name']}")
    render_main_app()
```

### Como Eric gera senha hash
```bash
python -c "from streamlit_authenticator.utilities.hasher import Hasher; print(Hasher().hash('senha-forte-aqui'))"
# Output: $2b$12$KIXHE...  ← copiar para .env
```

**Referências:**
- [streamlit-authenticator GitHub (mkhorasani)](https://github.com/mkhorasani/Streamlit-Authenticator)
- [Streamlit Authentication docs](https://docs.streamlit.io/develop/concepts/connections/authentication)

---

## 🟦 Req 4 — Shopping List Canônica

### Documento único (referência consolidada — extrai dos docs anteriores)

#### 📦 Bibliotecas Python (`pyproject.toml`)

```toml
[project]
name = "revisor-contratual"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    # Frontend + Auth
    "streamlit>=1.40",
    "streamlit-authenticator>=0.3.3",
    "python-dotenv>=1.0",

    # Workflow + LLM
    "langchain>=0.3",
    "langgraph>=0.2",
    "langchain-ollama>=0.2",
    "langchain-openai>=0.2",       # opcional, para LLM cloud
    "langchain-community>=0.3",    # llama-cpp wrapper

    # Vault — RAG
    "sqlite-vec>=0.1",
    "sentence-transformers>=3.0",   # Legal-BERTimbau
    "rank_bm25>=0.2",               # BM25 sparse retrieval

    # Engine — parsing
    "pymupdf4llm>=0.0.12",
    "marker-pdf>=0.2",              # OCR fallback opcional

    # Engine — finanças
    "python-bcb>=0.5",              # BACEN OData
    # decimal é stdlib

    # Engine — utilidades
    "pydantic>=2.8",
    "tenacity>=9.0",                # retry
    "diskcache>=5.6",               # cache filesystem
    "structlog>=24.4",              # audit log
    "jinja2>=3.1",                  # templates petição
    "weasyprint>=63.0",             # PDF gen

    # Outros
    "httpx>=0.27",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
ml = [
    # Fine-tuning (Req 5 — fase 2)
    "unsloth>=2026.4",
    "trl>=0.11",
    "peft>=0.13",
    "bitsandbytes>=0.44",
]

dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "ruff>=0.7",
    "mypy>=1.13",
]
```

#### 🌐 APIs Públicas

| API | URL | Uso | Auth | Custo |
|-----|-----|-----|------|-------|
| **BACEN SGS / OData** | `https://api.bcb.gov.br/dados/serie/...` | Taxa juros modalidade+data | Nenhuma | Grátis |
| **DataJud (CNJ)** — fase 2 | `https://api-publica.datajud.cnj.jus.br/` | Processos individuais | API Key gratuita | Grátis |
| **LexML** — edge cases | `https://www.lexml.gov.br/` | Resolução remissões legais | Nenhuma | Grátis |

#### 🤖 Modelos LLM (Ollama)

| Tier | Modelo Ollama | Tamanho | Onde baixar | Padrão? |
|------|---------------|---------|-------------|:-------:|
| **Premium** | `sabia-7b:q4_K_M` | ~5 GB | [HuggingFace TheBloke/sabia-7B-GGUF](https://huggingface.co/TheBloke/sabia-7B-GGUF) | ⭐ default |
| Balanced | `qwen2.5:7b-instruct-q4_K_M` | ~4.5 GB | `ollama pull qwen2.5:7b-instruct-q4_K_M` | fallback |
| Lean | `qwen2.5:3b-instruct-q4_K_M` | ~2 GB | `ollama pull qwen2.5:3b-instruct-q4_K_M` | fallback leve |

**Comando setup default:**
```bash
ollama pull sabia-7b:q4_K_M  # ou usar GGUF da HuggingFace via Modelfile
```

#### 🧮 Embeddings (HuggingFace)

| Modelo | Tamanho | Uso | URL |
|--------|---------|-----|-----|
| **rufimelo/Legal-BERTimbau-sts-base** ⭐ | ~250 MB | Embeddings jurídicos PT-BR (default) | [HF](https://huggingface.co/rufimelo/Legal-BERTimbau-base) |
| rufimelo/Legal-BERTimbau-sts-large | ~330 MB | Versão maior (qualidade ↑, latência ↑) | [HF](https://huggingface.co/rufimelo/Legal-BERTimbau-large) |

#### 📚 Repositórios para Vault Seed (rodar 1× para popular)

| Repo | Linguagem | Stack | Output |
|------|-----------|-------|--------|
| **[courtsbr/stf](https://github.com/courtsbr/stf)** | R | Scraping STF | JSON acórdãos/súmulas STF |
| **[courtsbr/stj](https://github.com/courtsbr/stj)** | R | Scraping STJ | JSON acórdãos/súmulas/temas STJ |
| **Wrapper Python customizado** (Atlas vai criar) | Python | Scraping TJBA + outros TJs | JSON acórdãos por UF |

**Alternativa:** [HuggingFace `joelniklaus/brazilian_court_decisions`](https://huggingface.co/datasets/joelniklaus/brazilian_court_decisions) — datasets prontos com STF + STJ + TJ-SP + TJ-RJ + TSE.

#### 🧪 Datasets para Benchmark / Test Set

| Dataset | URL | Uso |
|---------|-----|-----|
| **JurisTCU** | [arXiv 2503.08379](https://arxiv.org/html/2503.08379) | 16k docs + 150 queries com relevance — test set RAG |
| HuggingFace `joelniklaus/brazilian_court_decisions` | [HF](https://huggingface.co/datasets/joelniklaus/brazilian_court_decisions) | Enriquecimento + validação |

#### 📜 Legislação para Pré-Cache

| Lei | Source | Path no vault |
|-----|--------|---------------|
| **CDC — Lei 8.078/90** | LexML / planalto.gov.br | `seed/legislacao/cdc-lei-8078-90.json` |
| **Código Civil — Lei 10.406/02** | LexML / planalto.gov.br | `seed/legislacao/codigo-civil-lei-10406-02.json` |
| **Lei do SFN — Lei 4.595/64** | LexML / planalto.gov.br | `seed/legislacao/lei-sfn-4595-64.json` |
| **MP 2.170-36/2001** | LexML / planalto.gov.br | `seed/legislacao/mp-2170-36-2001.json` |

#### 🔧 Ferramentas adicionais (fase 2 — fine-tuning)

| Tool | Uso |
|------|-----|
| **[Unsloth](https://github.com/unslothai/unsloth)** | LoRA fine-tuning rápido (2× mais rápido, 70% menos memória) ([Red Hat 2026](https://developers.redhat.com/articles/2026/04/01/unsloth-and-training-hub-lightning-fast-lora-and-qlora-fine-tuning)) |
| TRL (HuggingFace) | Treinamento PPO/DPO |
| PEFT | Parameter-Efficient Fine-Tuning |
| bitsandbytes | Quantização 4-bit |

---

## 🟦 Req 5 — ML Feedback Loop (Aprendizado Contínuo) ⚡ NOVO BLOCO

### Conceito
Sistema deve **aprender com o uso real:**
1. **Dados públicos novos** — re-indexar jurisprudência atualizada (Tema 1378 STJ quando julgado, novos repetitivos)
2. **Outcomes da própria aplicação** — petições geradas → ganhou ou perdeu → ajustar o sistema

### Decisão Atlas — Estratégia em 3 Estágios

#### **Estágio 1 — Cold Start (Mês 1-12) — COLETA**
Sem ML. Apenas **registrar outcomes**:
- Cada petição gerada tem um `outcome_id`
- Eric (ou advogado-piloto) marca depois: `WON | LOST | PARTIAL | UNKNOWN | PENDING`
- Registrar metadados: câmara, relator, data, score do Juiz na geração, tese principal
- **Outcomes DB:** SQLite separado em `bloco_learning/outcomes.db`

#### **Estágio 2 — Adaptive Re-Ranking (Mês 6-18) — APRENDE A PRIORIZAR**
Quando volume >=50 outcomes:
- **Re-ranking adaptativo do RAG**: ajusta scores de jurisprudência baseado em quais docs apareciam em casos vencidos vs perdidos
- Não precisa fine-tuning de LLM — só pesos no retriever
- Implementação simples: regressão logística sobre features (court_id, peso_vinculacao, ano, score_relevancia, foi_citado_em_caso_vencido)

#### **Estágio 3 — Fine-Tuning LoRA (Mês 12+) — APRENDE A REDIGIR**
Quando volume >=100 outcomes + dataset de teses bem-sucedidas:
- **LoRA fine-tuning de Sabia-7B** com Unsloth (2× mais rápido, 70% menos memória)
- Dataset: pares `(contrato, tese_gerada, outcome=WON)` — apenas teses vencedoras
- Hardware: precisa **GPU 8-12GB VRAM** (RTX 4070 Ti viável OU cloud RunPod ~R$50-100 one-shot)
- Quality > Quantity: **500 exemplos limpos > 5000 ruidosos** (Red Hat 2026)
- Output: novo modelo Sabia-7B-Revisor-v1 que substitui o base via LLM_MODEL no .env

### Estrutura do `bloco_learning/`

```
bloco_learning/
├── outcomes/
│   ├── outcomes_db.py            # SQLite outcomes
│   ├── outcome_registrar.py      # API para marcar outcome
│   └── streamlit_form.py         # UI para Eric marcar outcomes
├── adaptive_ranking/
│   ├── ranker.py                 # regressão logística adaptive
│   └── features.py               # extração de features
├── fine_tuning/
│   ├── prepare_dataset.py        # exporta WON outcomes para JSONL
│   ├── train_lora_unsloth.py     # script Unsloth
│   └── deploy_model.py           # registra novo modelo no Ollama
├── refresh_jurisprudence/
│   ├── stf_monitor.py            # detecta novas Súmulas Vinculantes
│   ├── stj_monitor.py            # detecta novos Temas Repetitivos
│   └── alert_critical_changes.py # ex: Tema 1378 STJ julgado!
└── tests/
```

### Schema do outcomes.db

```sql
CREATE TABLE outcomes (
    outcome_id TEXT PRIMARY KEY,
    contrato_hash TEXT NOT NULL,            -- sha256 do contrato (anonimização)
    petition_hash TEXT NOT NULL,            -- sha256 da petição gerada
    generated_at TEXT NOT NULL,
    juiz_score INTEGER,                     -- score do Juiz IA na geração

    -- Outcome (preenchido depois pelo Eric)
    outcome TEXT,                           -- WON | LOST | PARTIAL | UNKNOWN | PENDING
    outcome_date TEXT,
    sentenca_path TEXT,                    -- opcional: caminho para sentença
    valor_revisado_brl TEXT,               -- Decimal string

    -- Metadados processuais
    uf TEXT,
    tribunal TEXT,                          -- TJBA, TJSP...
    camara TEXT,                            -- ex: "1ª Câmara Cível"
    relator TEXT,

    -- Para Adaptive Re-Ranking
    docs_jurisprudencia_citados TEXT,       -- JSON array de id_doc
    tese_principal TEXT,
    notes TEXT
);

CREATE INDEX idx_outcome ON outcomes(outcome);
CREATE INDEX idx_uf ON outcomes(uf);
CREATE INDEX idx_camara ON outcomes(camara);
```

### UI para Eric marcar outcomes (Streamlit)

```python
# bloco_interface/pages/4_outcomes.py
import streamlit as st

st.title("Registrar Outcomes de Petições")

# Lista petições pendentes (PENDING ou UNKNOWN)
pendentes = outcomes_db.list_pending()

for petition in pendentes:
    with st.expander(f"{petition['generated_at']} — {petition['tese_principal'][:80]}..."):
        outcome = st.selectbox(
            "Resultado",
            ["PENDING", "WON", "LOST", "PARTIAL", "UNKNOWN"],
            key=f"outcome_{petition['outcome_id']}"
        )
        valor = st.text_input("Valor revisado (R$)", key=f"valor_{petition['outcome_id']}")
        notes = st.text_area("Observações", key=f"notes_{petition['outcome_id']}")

        if st.button("Salvar", key=f"save_{petition['outcome_id']}"):
            outcomes_db.update_outcome(petition['outcome_id'], outcome, valor, notes)
            st.success("Salvo!")
```

### Refresh automatizado de jurisprudência

```python
# bloco_learning/refresh_jurisprudence/scheduler.py
# Roda mensalmente via cron / GitHub Actions / Streamlit background task

def refresh_monthly():
    # 1. STF Súmulas Vinculantes — diff vs cache
    novas_sv = stf_monitor.detect_new_sumulas_vinculantes()
    if novas_sv:
        ingestao.indexar(novas_sv)
        audit.log("CRITICAL_CHANGE", f"{len(novas_sv)} novas SV STF")

    # 2. STJ Temas Repetitivos — diff
    novos_temas = stj_monitor.detect_new_temas_repetitivos()
    if novos_temas:
        ingestao.indexar(novos_temas)
        # Verificar se algum é Tema 1378 (relevante para nosso domínio)
        if any(t['numero'] == '1378' for t in novos_temas):
            audit.log("CRITICAL_ALERT", "Tema 1378 STJ JULGADO — revisar D-04 e arquitetura")
```

### Métricas de sucesso do produto (KPIs)

| KPI | Cálculo | Alerta |
|-----|---------|--------|
| **Win rate** | WON / (WON + LOST) | <60% → revisar tese padrão |
| **Score do Juiz vs outcome** | Correlação Pearson | <0.5 → Juiz está calibrado errado |
| **Tempo médio até outcome** | Mediana(outcome_date - generated_at) | >180 dias → ajustar follow-up |
| **Volume de outcomes registrados** | COUNT(outcome != NULL) | <50% das petições → motivar registro |

---

## 📊 Estrutura Final — 7 Blocos

```
revisor_contratual/
├── bloco_contratos/        # Pydantic models compartilhados (interface estável)
├── bloco_interface/        # Streamlit + auth (streamlit-authenticator + bcrypt)
│   ├── auth.py
│   ├── pages/
│   │   ├── 1_upload.py
│   │   ├── 2_processamento.py
│   │   ├── 3_resultado.py
│   │   └── 4_outcomes.py   # ← NOVO Req 5
│   └── ...
├── bloco_workflow/         # state machine + provider LLM abstrato
│   ├── llm_provider.py     # ← Req 2: Ollama / llama-cpp / OpenAI-compatible
│   ├── grafo_estado.py
│   └── ...
├── bloco_vault/            # sqlite-vec multi-UF
│   ├── seed/
│   │   ├── add_uf.py       # ← Req 1: CLI para adicionar UFs
│   │   └── ...
│   ├── retriever.py        # ← filtro court_id IN ([UF + STF + STJ])
│   └── ...
├── bloco_engine/           # parsing + cálculo + BACEN
├── bloco_audit/            # structlog → audit.jsonl
└── bloco_learning/         # ← NOVO Req 5
    ├── outcomes/
    ├── adaptive_ranking/
    ├── fine_tuning/
    └── refresh_jurisprudence/
```

**7 blocos. Ainda 1 processo Python. Ainda 0 containers.**

---

## 🎯 Atualizações em Decisões Anteriores

| Decisão original | Status | Atualização |
|------------------|--------|-------------|
| **D-02** (6 blocos) | 🔄 **REVISADA** | Agora **7 blocos** (adicionado `bloco_learning/`) |
| **D-12** (UF inicial BA) | ✅ Confirmada + estendida | BA é seed; multi-UF é first-class no design |
| **Outras 11 decisões** | 🟢 Mantidas | Sem alteração |

**Nova decisão implícita:**
- **D-14:** Auth obrigatório no MVP (streamlit-authenticator + bcrypt env)
- **D-15:** LLM provider abstrato (Ollama default, llama-cpp e cloud opt-in)
- **D-16:** ML feedback loop em 3 estágios (cold start → adaptive ranking → LoRA fine-tuning)

---

## 📋 Footprint atualizado

| Componente | RAM (Tier Premium Sabia-7B) |
|-----------|------------------------------|
| Streamlit + auth | ~500 MB |
| Sabia-7B Q4 (Ollama) | ~5 GB |
| Legal-BERTimbau-base | ~250 MB |
| sqlite-vec + vault | ~500 MB (3k docs BA) |
| outcomes.db | ~10 MB |
| PyMuPDF + libs | ~150 MB |
| **TOTAL** | **~6.5 GB RAM** |

**Folga laptop Eric (16GB):** ~9.5 GB livres ✅

**Disco:**
- Modelos: ~6 GB (Sabia-7B + Legal-BERTimbau)
- Vault BA: ~500 MB → ~5 GB com cobertura nacional
- Outcomes: ~50 MB/ano (estimativa 100 outcomes/mês)
- Logs: ~100 MB/ano
- **TOTAL inicial:** ~7 GB

---

## ⚠️ Próximas Decisões Humanas (após handoff Aria)

- [ ] **Senha admin do Eric** — gerar hash bcrypt e colocar no `.env`
- [ ] **Quando ativar refresh automático de jurisprudência** (cron mensal vs manual)
- [ ] **Política de outcomes — quem registra?** (Eric? Advogado-piloto? API integration com sistemas de gestão jurídica?)
- [ ] **Política LGPD para outcomes** — anonimização do contrato_hash + sentença

---

## 🔗 Fontes Consultadas (esta sessão)

- [Unsloth + Training Hub LoRA — Red Hat 2026](https://developers.redhat.com/articles/2026/04/01/unsloth-and-training-hub-lightning-fast-lora-and-qlora-fine-tuning)
- [LoRA QLoRA Guide 2026 — Effloow](https://effloow.com/articles/llm-fine-tuning-lora-qlora-guide-2026)
- [LlamaFactory — Unified Fine-Tuning](https://github.com/hiyouga/LlamaFactory)
- [streamlit-authenticator (mkhorasani)](https://github.com/mkhorasani/Streamlit-Authenticator)
- [Streamlit Authentication Docs](https://docs.streamlit.io/develop/concepts/connections/authentication)
- [Streamlit Secrets Management](https://docs.streamlit.io/develop/concepts/connections/secrets-management)
- [Streamlit Authentication Made Simple — KubeBlogs](https://www.kubeblogs.com/streamlit-authentication/)

---

*Atlas, abrindo as portas certas para o futuro do produto — 🔎*
