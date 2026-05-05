---
type: decisions
title: "Revisor Contratual — Estratégia de Curadoria do Vault (D-05) + Ajuste Hardware (D-11)"
project: revisor-contratual
author: "@analyst (Atlas)"
date: "2026-05-01"
predecessor: "decisions/decisions-consolidated-2026-05-01.md"
audience: ["Eric Claudino", "@architect (Aria)"]
tags:
  - project/revisor-contratual
  - decisions
  - vault-strategy
  - hardware-strategy
---

# Estratégia de Curadoria do Vault (D-05) + Ajuste Hardware (D-11)

> **Contexto:** análise de risco identificou D-05 e D-11 como riscos moderados que precisavam de mitigação concreta. Documento resolve ambos.

---

## D-05 — Pipeline de Curadoria do Vault Inicial

### Contexto
Vault inicial precisa de **2.000-3.000 docs** curados (legislação + jurisprudência) com metadata correta (taxonomia controlada). Curadoria 100% manual = 5-10 dias de trabalho de 1 pessoa. Inviável para fase 0.

### Estratégia Atlas: **Pipeline 3-Camadas com Auto-Classificação + Validação Estratificada**

```
┌────────────────────────────────────────────────────────────────────┐
│  CAMADA 1 — INGESTÃO BRUTA (automática)                            │
│  Atlas roda scripts (Python re-implementados, não R)               │
│  ├─ STF Súmulas Vinculantes (~58 docs)         [scraping HTML]      │
│  ├─ STF Repercussão Geral (~1.300 teses)       [scraping HTML]      │
│  ├─ STJ Súmulas (~671)                         [scraping HTML]      │
│  ├─ STJ Temas Repetitivos (~1.300)             [scraping HTML]      │
│  ├─ TJMG acórdãos revisional CDC (~300)        [scraping seletivo]  │
│  └─ Legislação LexML (4 diplomas)              [API LexML]          │
│  Output: ~3.600 docs JSON brutos em seed/raw/                       │
│  Tempo estimado: 1-2 dias (Atlas + scripts)                         │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│  CAMADA 2 — AUTO-CLASSIFICAÇÃO (LLM)                                │
│  Sabia-7B (ou Qwen 2.5 7B) com few-shot + structured output         │
│  Para cada doc bruto, classificar:                                   │
│  ├─ legal_topic_principal (taxonomia controlada de ~50 tópicos)     │
│  ├─ legal_topics_secundarios                                        │
│  ├─ modalidade_relacionada (VEICULO, IMOBILIARIO, CDC_GENERICO...)  │
│  ├─ ano_julgamento (extrair de texto)                                │
│  ├─ peso_vinculacao (lookup em tabela: STF SV=5, STJ Repetitivo=4..)│
│  └─ ementa (extrair / sintetizar 200 chars)                         │
│  Output: ~3.600 docs JSON enriquecidos em seed/auto/                │
│  Tempo estimado: 4-8h em laptop (CPU-only, Sabia-7B Q3)              │
│  Custo: R$ 0 (local)                                                │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│  CAMADA 3 — VALIDAÇÃO HUMANA ESTRATIFICADA                          │
│  Eric (ou advogado-piloto) valida amostra estratificada:            │
│  ├─ 100% dos STF Súmulas Vinculantes (~58 — peso máximo)            │
│  ├─ 100% dos STJ Temas Repetitivos sobre revisional (~50-100)       │
│  ├─ Amostra 10% do restante (~330 docs randomicamente selecionados) │
│  └─ Foco: validar `legal_topic_principal` + `peso_vinculacao`       │
│  Tempo estimado: 1-2 dias de Eric (~5min/doc nos críticos, 30s nos  │
│                  amostrais)                                          │
│  Resultado: classifier accuracy medida; se <90%, re-train few-shot   │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                   Vault populado em ~4-6 dias úteis
                   (vs 5-10 dias se 100% manual)
```

### Decisão Atlas para D-05

| Pergunta | Resposta |
|----------|----------|
| Quem roda os scrapers? | **Atlas** — re-implementa em Python (não R). Estimativa: 2-3 dias dev. Mais simples que rodar `courtsbr/*` em R. |
| Quem cura? | **3 camadas:** automação (Atlas) + LLM (Sabia) + validação humana estratificada (Eric ou advogado-piloto) |
| Onde mora a curadoria humana? | **Streamlit interface** simples: lista docs, mostra ementa + classificação proposta, Eric aprova/corrige com 1 click |
| Quando começar? | **Após Aria produzir SAD** (precisa do schema enriquecido definido) |
| Quem faz a interface de curadoria? | **@dev** em Story dedicada (Epic 2) — não precisa de Streamlit completo, pode ser script CLI mesmo |

### Riscos da estratégia
| Risco | Mitigação |
|-------|-----------|
| Scrapers Python re-implementados podem quebrar (portais STF/STJ não-versionados) | Pipeline de teste mensal + alerts |
| LLM auto-classificação pode errar peso_vinculacao em casos limítrofes | Eric valida 100% dos vinculantes (Súmulas + Repetitivos) — onde erros são caros |
| Eric não ter tempo para validar 500 docs | Reduzir amostra para top-100 críticos; deixar resto sem validação humana com flag `auto_classified=true` |

### Código Python proposto (conceitual)

```python
# bloco_vault/seed/auto_classificador.py
from langchain_ollama import OllamaLLM
from pydantic import BaseModel, Field
from typing import Literal

class ClassificacaoDoc(BaseModel):
    legal_topic_principal: Literal["ANATOCISMO", "CAPITALIZACAO_JUROS", "TABELA_PRICE",
                                    "ABUSIVIDADE_JUROS", "REVISAO_CONTRATUAL", "CDC_BANCARIO",
                                    "JUROS_REMUNERATORIOS", "TARIFAS_BANCARIAS", "OUTROS"]
    legal_topics_secundarios: list[str] = Field(max_items=3)
    modalidade_relacionada: list[Literal["VEICULO", "IMOBILIARIO", "CDC_GENERICO",
                                          "CARTAO_ROTATIVO", "GERAL"]]
    ano_julgamento: int
    peso_vinculacao: int = Field(ge=1, le=5)
    ementa_curta: str = Field(max_length=200)
    confianca_classificacao: float = Field(ge=0, le=1)

llm = OllamaLLM(model="sabia-7b:q3_k_m")  # Q3 para caber em GTX 1650 (4GB) — ver D-11

def classificar_doc(texto: str, source_meta: dict) -> ClassificacaoDoc:
    prompt = f"""Você é um classificador jurídico brasileiro. Classifique este documento:

DOCUMENTO:
{texto[:4000]}

METADADOS DA FONTE:
- Origem: {source_meta['origem']}  # ex: "STF/SumulaVinculante", "STJ/TemaRepetitivo"
- Número: {source_meta.get('numero', 'n/a')}

Retorne JSON estruturado com classificação. Se confiança < 0.7, marque para revisão humana.

{ClassificacaoDoc.model_json_schema()}
"""
    response = llm.invoke(prompt)
    return ClassificacaoDoc.model_validate_json(response)
```

---

## D-11 — Patch Hardware: GPU GTX 1650 4GB Insuficiente

### Achado
Especificações reais do laptop do Eric:
- **CPU:** Intel i5-10300H (4 cores físicos / 8 threads, 2.5 GHz, 2020)
- **GPU:** Intel UHD Graphics + **NVIDIA GeForce GTX 1650 (4GB VRAM)**
- **RAM:** 15.84 GB (4.74 GB livres no momento)
- **Disco:** 333.9 GB livres de 476 GB

### Problema
**Sabia-7B Q4 ocupa ~5GB VRAM** — não cabe na GPU.

### Opções avaliadas

| Opção | Modelo | VRAM/RAM | Velocidade | Qualidade PT-BR jurídico |
|-------|--------|----------|-----------|---------------------------|
| **A — Sabia-7B Q3 GPU** | sabia-7b Q3_K_M (~3GB) | 3GB GPU | Rápido | Levemente reduzida vs Q4 |
| **B — Sabia-7B Q4 CPU** | sabia-7b Q4 (~5GB) | 5GB RAM | 3-5× mais lento | Original |
| **C — Modelo menor GPU** | Phi-3 mini Q4 (~3GB) ou Llama 3.2 3B Q4 (~2GB) | 2-3GB GPU | Rápido | INFERIOR (não-PT-BR-específico) |
| **D — Cloud GPU temporária** | Sabia-7B Q4 ou maior | n/a (RunPod RTX 4090) | Rápido | Original ou superior |

### Decisão Atlas para D-11 (Phase 1)

**Estratégia híbrida em 3 fases:**

| Fase | Setup | Razão |
|------|-------|-------|
| **Phase 1 (dev local)** | **Opção B — Sabia-7B Q4 em CPU** com Ollama `--num-gpu-layers 0` | Mantém qualidade original; latência de 10-30s/resposta é aceitável em dev solo |
| **Phase 2 (validação MVP)** | Manter laptop OU **cloud GPU on-demand** (RunPod ~R$2-4/hora, ~R$50-100 para 30h dev) | Se latência travar produtividade, usar cloud temporariamente |
| **Phase 3 (produção)** | **Workstation Cenário C** (RTX 4070 Ti 16GB ~R$7k) OU **VPS GPU** (~R$500-1500/mês) | Quando primeiro cliente real chegar |

### Por que NÃO Opção A (Sabia Q3 GPU)
- Q3 perde precisão suficiente para alterar saída em prompts longos jurídicos
- Risco no Juiz Revisor (que precisa de aderência 100%)

### Por que NÃO Opção C (modelo menor)
- Phi-3, Llama 3.2 não são PT-BR específicos — qualidade jurídica cai significativamente
- Defeats the purpose de D-04 (escolha de Sabia-7B)

### Por que NÃO Opção D direto
- Custo recorrente desnecessário em fase 0
- Dependência de internet em dev = atrito

### Implicação para arquitetura
Adicionar configuração de **modo deployment** no LangGraph:
```python
# bloco_agentes/orquestrador/configuracao.py
from enum import Enum

class ModoDeployment(str, Enum):
    DEV_LAPTOP_CPU = "dev_laptop_cpu"        # Sabia-7B Q4 CPU, latência 10-30s
    DEV_CLOUD_GPU = "dev_cloud_gpu"          # Sabia-7B Q4 GPU cloud, latência 1-3s
    PROD_WORKSTATION = "prod_workstation"    # Sabia-7B FP16 GPU local, latência <1s
    PROD_VLLM = "prod_vllm"                  # vLLM com batching, latência variável
```

### Custo total D-11 (revisado)
- Phase 1: **R$ 0** (laptop atual)
- Phase 2: **R$ 50-100 one-shot** (cloud GPU se necessário)
- Phase 3: **R$ 7-15k upfront** OU **R$ 500-1.500/mês** (decidir quando chegar)

---

## 📋 Resumo das Decisões Tomadas

| Decisão | Status | Mudança |
|---------|--------|---------|
| **D-05** | ✅ Resolvida | Pipeline 3-camadas: Atlas scrapers Python → Sabia auto-classifica → Eric valida estratificado |
| **D-11** | ✅ Resolvida com patch | Phase 1: Sabia-7B Q4 em CPU (não GPU). Cloud GPU é fallback. Workstation só em produção. |
| **D-10** | ✅ Resolvida (ver competitor-analysis) | MANTER + pivô posicionamento. Promovida 🔴→🟡. |
| **NOVO** | ⚠️ Adicionar ao backlog | Monitorar Tema 1378 STJ (`*loop` mensal sugerido) |

---

## 🔗 Referências

- D-05/D-11 originais: [`decisions/decisions-consolidated-2026-05-01.md`](./decisions-consolidated-2026-05-01.md)
- Análise de risco: [`decisions/risk-analysis-13-decisions-2026-05-01.md`](./risk-analysis-13-decisions-2026-05-01.md)
- Análise de concorrentes: [`research/competitor-analysis-2026-05-01.md`](../research/competitor-analysis-2026-05-01.md)

---

*Atlas, fechando os últimos cabos antes do voo — 🔎*
