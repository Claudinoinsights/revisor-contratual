---
type: decisions
title: "Revisor Contratual — Garantias de Qualidade, Dados e Modularidade (Arquitetura D)"
project: revisor-contratual
author: "@analyst (Atlas)"
date: "2026-05-01"
trigger: "Eric: 'Em relação à qualidade, base de dados, entrega, volume e modularidade — como fica essa nova versão?'"
predecessor: "decisions/architecture-D-lean-2026-05-01.md"
audience: ["Eric Claudino", "@architect (Aria)"]
tags:
  - project/revisor-contratual
  - quality-assurance
  - data-strategy
  - modularity
---

# Garantias de Qualidade, Dados e Modularidade — Arquitetura D

> **Pergunta-chave do Eric:** A refatoração radical para D-LEAN não comprometeu a qualidade da entrega, a base de dados, o volume jurídico crítico, nem a modularidade da infra?
>
> **Resposta honesta em uma frase:** **Volume e dados intactos. Qualidade tem trade-off real e gerenciável (com escape de upgrade). Modularidade DE CÓDIGO sólida; modularidade DE INFRA reduzida intencionalmente para MVP — com caminho claro de upgrade.**

---

## ⚡ Resumo Executivo — 5 Dimensões

| Dimensão | D-LEAN compromete? | Veredicto |
|----------|:------------------:|-----------|
| **1. Qualidade do trabalho final (petição)** | 🟡 **Trade-off real** mas mitigável | LLM menor (Qwen 3B) gera tese OK; opção de upgrade para Sabia-7B sem refazer nada |
| **2. Base de dados (vault)** | 🟢 **Não compromete** | Mesmas 3.000 docs, mesmo schema enriquecido, mesma curadoria |
| **3. Entrega (deliverable)** | 🟢 **Não muda** | Petição PDF + hash + audit log idênticos |
| **4. Volume de material** | 🟢 **Capacidade SOBRA** | sqlite-vec aguenta 100k+ docs (~30× crescimento futuro) |
| **5. Modularidade infra** | 🟡 **Reduzida no MVP, recuperável** | Código é modular; processos não. Upgrade path claro |

---

## 🎯 Dimensão 1 — Qualidade do Trabalho Final

### O que mudou
| Componente | Antes (C) | Agora (D-LEAN) |
|-----------|-----------|----------------|
| LLM gerador de tese | Sabia-7B Q4 (7B params, PT-BR jurídico-treinado) | **Qwen 2.5 3B Q4** (3B params, PT-BR oficial multilíngue) |
| LLM Perito | Sabia-7B (cálculos via tools) | **Função Python pura** (sem LLM) |
| LLM Juiz | Sabia-7B (3 checagens) | **Função Python pura** (asserts + scoring) |

### Trade-off REAL e honesto

**Onde Sabia-7B é melhor que Qwen 2.5 3B:**
- Vocabulário jurídico nuançado (Sabia treinou em corpus legal BR)
- Estilo de redação forense mais natural em PT-BR
- Citações de doutrina com mais fidelidade

**Onde Qwen 2.5 3B é tão bom quanto:**
- Function calling robusto (Qwen é forte em structured output)
- Seguir instruções estritas (citation-grounded)
- Geração baseada em contexto fornecido (RAG-grounded)
- Multilíngue oficial Português

### Mitigações da queda de qualidade (já no design D)

1. **Apenas 1 tarefa LLM** — concentrar engenharia de prompt nessa única chamada
2. **Few-shot examples** — 3-5 teses exemplares no prompt (advogado-piloto curou)
3. **Citation-grounded hard-fail** — LLM NÃO PODE inventar fontes; toda citação valida contra `docs_consultados_ids`
4. **Validação determinística no Juiz Python** — independente da qualidade do LLM, o produto não emite petição com aderência <100%
5. **Vault enriquecido com metadata correto** — quanto melhor o input do RAG, melhor a tese (vale para qualquer LLM)

### 🔄 ESCAPE DE UPGRADE — Eric escolhe nível de qualidade

**Vantagem da arquitetura D:** trocar de modelo é **1 linha de configuração**, sem refazer infra.

| Tier | Modelo | RAM | Latência (CPU) | Qualidade jurídica |
|------|--------|-----|----------------|---------------------|
| **Tier S — Lean** | **Qwen 2.5 3B Q4** ⭐ default | 2 GB | 20-60s | OK (defensável) |
| **Tier M — Balanceado** | **Qwen 2.5 7B Q4** | 4.5 GB | 60-180s | Boa |
| **Tier L — Premium** | **Sabia-7B Q4** | 5 GB | 60-200s | Melhor PT-BR jurídico |
| **Tier XL — Top** | **Llama 3.1 70B Q4** | 22 GB | (precisa GPU) | Top open-source |

**Eric pode começar Tier S e migrar para M/L em 1 minuto** se sentir que a qualidade não está suficiente.

### 🎓 Recomendação Atlas

**MVP: começar com Qwen 2.5 3B (Tier S)** — testar com 10-20 contratos reais. Se Eric ou advogados-piloto sentirem qualidade fraca, **upgrade imediato para Qwen 2.5 7B (Tier M)** — ainda cabe nos 16GB RAM dele.

**Configuração proposta:**
```python
# bloco_workflow/config.py
LLM_MODELS = {
    "lean":     "qwen2.5:3b-instruct-q4_K_M",      # ~2GB
    "balanced": "qwen2.5:7b-instruct-q4_K_M",      # ~4.5GB
    "premium":  "sabia-7b:q4_K_M",                  # ~5GB
}
LLM_TIER = os.getenv("LLM_TIER", "lean")  # default lean, override via env
```

**Trocar tier = restart do Streamlit. Zero refactor.**

---

## 🎯 Dimensão 2 — Base de Dados (Vault de Jurisprudência)

### O que NÃO mudou
✅ **Mesmas 4 fontes de jurisprudência (D-06):**
- STF Súmulas Vinculantes (~58 docs — peso 5/5)
- STF Repercussão Geral (~1.300 teses — peso 5/5)
- STJ Súmulas (~671 — peso 3/5)
- STJ Temas Repetitivos (~1.300 — peso 4/5)
- TJBA acórdãos revisional CDC (~300 — peso 1/5)

✅ **Mesmo schema enriquecido:**
- `legal_topic_principal` (taxonomia controlada)
- `legal_topics_secundarios`
- `modalidade_relacionada` (VEICULO, IMOBILIARIO, etc.)
- `peso_vinculacao` (1-5)
- `ano_julgamento`
- `binding` (bool)

✅ **Mesma estratégia de chunking jurídico:**
- Recursive splitter com separadores legais (`Art.`, `§`, `Súmula`, `TEMA`)
- Summary-based context enrichment (combate cross-document confusion)
- Deduplication via hash canônico

✅ **Mesmas 4 leis pré-cacheadas (D-08):**
- CDC (Lei 8.078/90)
- Código Civil (Lei 10.406/02)
- Lei SFN (Lei 4.595/64)
- MP 2.170-36/2001 (capitalização)

### O que mudou (apenas a tecnologia de armazenamento)

| Componente | Antes (Qdrant) | Agora (sqlite-vec) |
|-----------|---------------|---------------------|
| **Volume de docs suportado** | Milhões | **100k-500k confortável (brute-force)** |
| **Filtros payload** | 1.1× overhead, recursivo | **SQL WHERE clauses (índices B-tree)** |
| **Hybrid search (sparse+dense)** | Native v1.9+ | **Implementar BM25 manual com `rank_bm25`** (~1 dia dev) |
| **Latência típica (3.000 docs)** | ~30-60ms | **~10-50ms** (brute-force é rápido em volumes pequenos) |
| **Setup** | Docker container | **`pip install sqlite-vec`** |

### Veredicto sobre dados

**Capacidade da infra >> volume real:**
- **Vault inicial:** 3.000 docs
- **Crescimento previsto:** 500-1000 docs/ano (vinculantes + relevantes)
- **Em 5 anos:** ~8.000 docs
- **Capacidade sqlite-vec:** **100.000-500.000 docs** com latência <500ms
- **Folga:** **30-100×** o necessário em 5 anos

**Quando precisaria migrar para Qdrant:**
- Vault >100k docs (Eric expande para todos os 27 TJs + câmaras)
- Filtros de cardinalidade muito alta (>50 valores distintos)
- Multi-tenant com isolamento por cliente
- → Migração: 1-2 sprints, **interfaces estáveis (`bloco_vault/retriever.py` API)**

### 🔍 Honestidade técnica
**A única perda real:** hybrid search nativo do Qdrant. Mas:
- Para 3.000 docs jurídicos, dense search com Legal-BERTimbau já é 90% do valor
- BM25 manual (lib `rank_bm25`) cobre os outros 10% sem dor

---

## 🎯 Dimensão 3 — Entrega (Deliverable)

### O que NÃO mudou
**O produto final é IDÊNTICO:**

| Output | Antes (C) | Agora (D-LEAN) |
|--------|-----------|----------------|
| **Petição revisional PDF** | Jinja2 + WeasyPrint | ✅ Idêntico |
| **Citações rastreáveis** `[id_doc:N]` | Citation-grounded | ✅ Idêntico |
| **Hash sha256 da petição** | Para auditoria | ✅ Idêntico |
| **Comparativo BACEN vs contrato** | Tabela com Decimal | ✅ Idêntico |
| **Relatório contábil** | Markdown estruturado | ✅ Idêntico |
| **Audit log de decisões humanas** | structlog → arquivo | ✅ Idêntico |
| **Score quantificado do Juiz** | 0-100 com 3 vereditos | ✅ Idêntico |
| **Relatório de Inviabilidade** | Quando aderência <70% | ✅ Idêntico |

**Conclusão:** o que o cliente recebe não mudou. **Só a forma como produzimos.**

---

## 🎯 Dimensão 4 — Volume de Material

### Análise quantitativa

| Aspecto | Quantidade | Capacidade D | Folga |
|---------|-----------|--------------|-------|
| Docs de jurisprudência (vault inicial) | 3.000 | 100.000+ | **33×** |
| Docs de legislação pré-cacheados | 4 | ilimitado | n/a |
| Contratos processados/dia (single user) | 1-5 | 50+ | **10×** |
| Tamanho médio de contrato | 10-30 pgs | 200+ pgs | **10×** |
| Citações por petição | 5-15 | 50+ | **3×** |
| Tamanho audit log (1 ano de uso intenso) | ~100 MB | ilimitado | n/a |
| RAM em uso | 3-4 GB | 16 GB (laptop Eric) | **4×** |

**Não há gargalo de volume em nenhuma dimensão.**

### Crescimento futuro suportado sem refactor

| Cenário | Volume | D-LEAN aguenta? |
|---------|--------|:---------------:|
| Solo MVP — TJBA | 3k docs | ✅ folga total |
| Expansão para 3 UFs | ~6k docs | ✅ folga total |
| Expansão para 5 UFs + acórdãos | ~15k docs | ✅ folga total |
| Cobertura nacional (todos 27 TJs vinculantes) | ~50k docs | ✅ ainda folgado |
| Cobertura nacional + acórdãos relevantes | ~150k docs | 🟡 brute-force começa a custar (~1s/query) — hora de migrar para Qdrant |
| Multi-tenant 100 escritórios | n/a | 🔴 Postgres + Qdrant + multi-process — fase 3 |

**Para os primeiros 2-3 anos do produto, D-LEAN aguenta confortável.**

---

## 🎯 Dimensão 5 — Modularidade da Infraestrutura

**Esta é a pergunta mais importante.** Vou ser brutalmente honesto.

### Modularidade tem 6 dimensões — análise por uma

| Dimensão da modularidade | Antes (C) | Agora (D-LEAN) | Comentário |
|--------------------------|:---------:|:--------------:|------------|
| **1. Separation of concerns (código)** | 🟢 | 🟢 | 6 blocos com responsabilidades claras |
| **2. Pluggable components** | 🟢 | 🟢 | Cada bloco substituível via interfaces Pydantic |
| **3. Process isolation** | 🟢 | 🟡 | Antes 3+ processos, agora 1 |
| **4. Container isolation** | 🟢 | 🔴 | Antes Docker Compose, agora monolito Python |
| **5. Independent deployment** | 🟢 | 🔴 | Antes deploy por serviço, agora deploy único |
| **6. Independent scaling** | 🟢 | 🔴 | Antes escalar workers, agora escala tudo junto |

**3 das 6 reduzidas (4, 5, 6)** — todas ligadas a infra operacional, não a código.

### Por que essa redução é ACEITÁVEL no MVP

**Princípio:** modularidade tem custo. Você paga em complexidade. Vale o custo apenas quando o benefício existe.

| Benefício | Faz sentido em MVP single-user? |
|-----------|:-------------------------------:|
| Deploy independente de cada serviço | ❌ Não — 1 dev, 1 user |
| Escalar workers separadamente | ❌ Não — 1 contrato/vez |
| Isolar falhas por container | ❌ Não — falha do LLM = falha do produto inteiro |
| Equipes independentes mexendo em serviços diferentes | ❌ Não — equipe = Eric |
| Múltiplas linguagens (Java backend + Python ML) | ❌ Não — só Python |

**Conclusão:** os 3 tipos de modularidade reduzidos não traziam valor real para o caso. Reduzir = remover gordura.

### Modularidade que IMPORTA continua intacta — 3 garantias

#### Garantia #1 — Estrutura de código modular (preservada 100%)
```
revisor_contratual/
├── bloco_contratos/      # Pydantic models — INTERFACES ESTÁVEIS
├── bloco_interface/      # Streamlit  — pode virar React + API depois
├── bloco_workflow/       # State machine — pode virar Dramatiq workers
├── bloco_vault/          # sqlite-vec — pode virar Qdrant
├── bloco_engine/         # Python puro — não muda nunca
└── bloco_audit/          # structlog — pode virar OpenTelemetry
```

**Cada bloco TEM uma interface bem definida via `bloco_contratos/`.** Substituir um bloco NÃO QUEBRA os outros.

#### Garantia #2 — Caminho de upgrade modular (claro)

Para CADA tipo de crescimento, há **upgrade path conhecido sem reescrita**:

| Necessidade futura | Upgrade necessário | Effort | Outros blocos afetados? |
|-------------------|-------------------|--------|-------------------------|
| Multi-cliente (>1 user simultâneo) | Adicionar FastAPI camada + Dramatiq workers | 2 sprints | NÃO — Streamlit vira mais um cliente da API |
| Vault >100k docs | Migrar `bloco_vault/` para Qdrant | 1-2 sprints | NÃO — interface `retriever.py` igual |
| LLM melhor (mais contratos/dia) | vLLM + GPU dedicada | 1 sprint | NÃO — `bloco_workflow/` chama via mesma API Ollama-compat |
| Tracing pesado | Adicionar OpenTelemetry no `bloco_audit/` | 1 sprint | NÃO — Apenas mais um exporter |
| Multi-tenant | Postgres + isolation por org_id | 3-4 sprints | Schema migration + auth — mas blocos preservam |

**Cada upgrade é localizado em 1-2 blocos.** Os demais continuam funcionando.

#### Garantia #3 — Contratos Pydantic estáveis

```python
# bloco_contratos/jurisprudencia.py — INTERFACE QUE NÃO MUDA
class JurisprudenciaItem(BaseModel):
    id_doc: str
    court_id: str
    binding: bool
    peso_vinculacao: int
    legal_topic_principal: str
    modalidade_relacionada: list[str]
    ementa: str
    texto_relevante: str
    score_relevancia: float
```

**Independente se atrás está sqlite-vec, Qdrant, Pinecone ou Weaviate** — o `bloco_workflow/` recebe o mesmo `JurisprudenciaItem`. Trocar implementação não muda consumidores.

### Diagrama: Módulos com interfaces estáveis (Hexagonal-like)

```
              ┌─────────────────────┐
              │  bloco_interface    │  ← Streamlit (substituível)
              │  (Streamlit)        │
              └─────────┬───────────┘
                        │
                        ▼
            ┌──────────────────────────┐
            │  bloco_workflow          │  ← LangGraph minimal
            │  (state machine)         │
            └──────────┬───────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
┌───────────┐  ┌─────────────┐  ┌──────────────┐
│ bloco_    │  │ bloco_      │  │ bloco_       │
│ engine    │  │ vault       │  │ audit        │
│ (puro Py) │  │ (sqlite-vec)│  │ (structlog)  │
└───────────┘  └─────────────┘  └──────────────┘
       ▲               ▲               ▲
       │               │               │
       └───────────────┴───────────────┘
                       │
              ┌────────┴─────────┐
              │ bloco_contratos  │  ← Pydantic models compartilhados
              │ (INTERFACES)     │     ESTÁVEIS — não mudam
              └──────────────────┘
```

**Setas para `bloco_contratos/` indicam dependência de interface, não implementação.**

---

## 🎯 Decisão Atualizada — Eric Escolhe Tier de Qualidade

Para resolver a tensão "qualidade vs leveza", proponho **decisão paramétrica**:

### Opção 1 (recomendada para começar) — **Tier S Lean**
- Qwen 2.5 3B Q4 (~2GB)
- Latência 20-60s/contrato CPU
- Qualidade OK para MVP
- **Custo: zero (laptop atual)**

### Opção 2 — **Tier M Balanceado**
- Qwen 2.5 7B Q4 (~4.5GB)
- Latência 60-180s/contrato CPU
- Qualidade boa, ainda cabe no laptop
- **Custo: zero**

### Opção 3 — **Tier L Premium (qualidade máxima local)**
- Sabia-7B Q4 (~5GB)
- Latência 60-200s/contrato CPU
- Melhor PT-BR jurídico open-source
- **Custo: zero**

**Decisão recomendada Atlas:**
> Começar **Tier S** com **escape configurado** para promover a Tier M imediatamente se Eric ou advogados-piloto sentirem qualidade fraca. Sem refactor — só mudar variável de ambiente.

**TODOS os 3 tiers preservam:**
- Footprint da arquitetura D (3-4 GB RAM mesmo no Tier L, pois Sabia ~5GB cabe nos 16 do Eric)
- Modularidade de código
- Caminho de upgrade
- Capacidade de vault

---

## 📋 Resumo Final — Tabela Verdade

| Pergunta de Eric | Resposta honesta |
|------------------|------------------|
| Qualidade do trabalho a ser executado? | 🟡 **Trade-off real (3B vs 7B) MAS gerenciável + escape de upgrade configurado** |
| A base de dados? | 🟢 **Intacta** — mesmo schema, fontes, curadoria |
| A entrega (deliverable)? | 🟢 **Idêntica** — petição PDF + hash + audit log iguais |
| O volume necessário de material? | 🟢 **Capacidade sobra 30-100×** o necessário em 5 anos |
| A infraestrutura continua modular? | 🟡 **Código sim, infra reduzida intencionalmente — caminho de upgrade modular claro** |

---

## 🚦 Recomendação final do Atlas

**Manter arquitetura D-LEAN com 1 ajuste:**

1. **Configurar 3 tiers de LLM desde o setup inicial** (variável de ambiente `LLM_TIER=lean|balanced|premium`)
2. **Default Tier S (Qwen 2.5 3B)** para começar leve
3. **Promoção imediata para Tier M (Qwen 2.5 7B) ou Tier L (Sabia-7B)** se qualidade for sentida como fraca em piloto
4. **Manter `bloco_contratos/` Pydantic models** como contratos estáveis — qualquer upgrade futuro localizado em 1-2 blocos

**Eric ganha:**
- Leveza desde MVP
- Opção de qualidade premium em 1 minuto (mudar env var, restart)
- Modularidade de código preservada
- Upgrade path para multi-tenant / Qdrant / vLLM claro e localizado

---

*Atlas, mantendo as ferramentas afiadas mas sem peso desnecessário — 🔎*
