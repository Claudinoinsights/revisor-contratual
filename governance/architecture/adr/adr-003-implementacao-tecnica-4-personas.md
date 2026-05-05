---
type: adr
id: "ADR-003"
title: "Implementação técnica das 4 personas internas + threshold Juiz definitivo"
status: accepted
date: "2026-05-01"
adr_level: spec
spec_coverage:
  - "Configuração Ollama (env vars OLLAMA_HOST + portas distintas; OLLAMA_NUM_PARALLEL alternativo)"
  - "Pinning langchain-ollama>=0.2.0 (mitiga sync wrapper risco)"
  - "Smoke test sugerido (medir latência asyncio.gather vs serial)"
patched_at:
  - "2026-05-01 (PATCH 1 — F-CRIT-A SUB-C)"
  - "2026-05-01 (PATCH 2 — F-MIN-01 OLLAMA_HOST + F-MIN-02 langchain pinning)"
patch_reason:
  - "PATCH 1: F-CRIT-A SUB-C — Smith adversarial review etapa 2.1 + decisão Eric (Economista em Qwen 2.5 3B paralelo)"
  - "PATCH 2: F-MIN-01 + F-MIN-02 — Smith mini-tribunal etapa 2.2 + decisão Eric RITMO 2 (Opção C — port collision Ollama + langchain pinning)"
domain: "personas-orquestracao"
decision_makers: ["@architect (Aria)", "@lmas-master Morpheus (consolidação Ordem 11)", "Eric (escolha SUB-C + RITMO 2)"]
supersedes: null
superseded_by: null
absorves:
  - "DP-04 (threshold aderência Juiz definitivo)"
  - "F-CRIT-A-2.1 (Smith — premissa instância compartilhada falsa) via PATCH SUB-C"
  - "F-MIN-01-2.2 (Smith — port collision Ollama) via PATCH-do-PATCH RITMO 2"
  - "F-MIN-02-2.2 (Smith — ainvoke sync wrapper) via pinning langchain-ollama>=0.2.0"
related_to:
  - "FR-CALC-01..03 (Perito)"
  - "FR-TESE-01..04 (Advogado)"
  - "FR-JUIZ-01..03 (Juiz)"
  - "P-INT-04 Economista promovida primeira-classe"
  - "ADR-001 (state machine LangGraph + asyncio.gather paralelo + _LockedSqliteSaver expandido)"
  - "ADR-004 (validação semântica citações)"
  - ".claude/rules/adr-scope.md (rule de framework — explica adr_level: spec)"
project: revisor-contratual
sprint: "01"
etapa: "2.0 (criada) → 2.2 (PATCH SUB-C) → 2.3 (PATCH-do-PATCH RITMO 2)"
tags:
  - project/revisor-contratual
  - adr
  - personas
  - llm
  - pydantic
  - patched
  - spec
---

# ADR-003 — Implementação técnica das 4 personas internas + threshold Juiz definitivo

```
[@architect · Aria (Visionary)] — etapa 2.0 · ADR-003 personas técnicas
SPRINT: 01 · ETAPA: 2.0 · DOMÍNIO: SoftwareDev/legaltech
```

## Contexto

PRD v1.0.2 estabelece 4 personas internas (D-04 REVOGADA):
- **P-INT-01 Perito Contábil/Fiscal:** cálculos Tabela Price + SAC + comparação BACEN
- **P-INT-02 Advogado bancário:** redige tese citation-grounded
- **P-INT-03 Juiz Revisor:** 3 checagens determinísticas (C1 cálculo, C2 jurisprudência, C3 jurisdição)
- **P-INT-04 Economista bancário:** análise macro contextual (PROMOVIDA primeira-classe v1.0.2 — mitigação Tema 1378 STJ)

Cada persona pode ser implementada como:
- **Função Python pura** (determinístico, auditável, rápido, zero alucinação)
- **Chamada LLM** (capacidade generativa, custo de latência, risco de alucinação)

Decisão arquitetural: qual persona vira função pura, qual vira LLM call, e como integrar?

DP-04 também precisa resolução: threshold de aderência do Juiz (FR-JUIZ-02) — proposta 70%/100%.

## Decisão

**Implementação técnica por persona:**

| Persona | Implementação | Justificativa |
|---------|---------------|---------------|
| **P-INT-01 Perito** | **Função Python pura** (Decimal everywhere) | Cálculos jurídicos exigem determinismo absoluto (CI gate proíbe `float()`); zero LLM |
| **P-INT-02 Advogado** | **LLM Sabia-7B Tier Premium** + structured output Pydantic | Geração de tese é tarefa criativa-fundamentada; estrutura forçada por Pydantic; validação cruzada `citations ⊆ docs_recuperados` |
| **P-INT-03 Juiz** | **Função Python pura** (3 checagens scoring) | Auditabilidade legal: julgador deve poder reproduzir o cálculo; LLM como juiz é red flag jurídico |
| **P-INT-04 Economista** | **LLM Qwen 2.5 3B** (instância dedicada Ollama, paralela ao Advogado via asyncio.gather) | Análise contextual macro (Selic, atipicidade) é tarefa **menos exigente** que tese jurídica → tier balanced é suficiente; instância dedicada habilita paralelismo via asyncio.gather (única opção que satisfaz NFR-PERF-01 + NFR-PERF-02) |

**Threshold Juiz (DP-04 resolvido):**
- **APROVADO_100:** aderência = 100% (todos os 3 checks PASS) → segue para FR-DELIV-06 (CFOAB)
- **APROVADO_COM_RISCO_HITL:** aderência **≥70% e <100%** → painel HITL (FR-JUIZ-02)
- **REJEITADO:** aderência <70% → Relatório de Inviabilidade (NUNCA petição)

### Detalhes técnicos

```python
# bloco_contratos/personas.py — Pydantic models compartilhados

from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Literal

# P-INT-01 Perito output
class ResultadoCalculo(BaseModel):
    pmt_composto: str  # Decimal-as-string
    pmt_simples: str
    diferenca_anatocismo: str
    classificacao_anatocismo: Literal["SEM", "LICITO", "QUESTIONAVEL", "ILICITO"]
    sumulas_aplicaveis: list[str]
    tabela_amortizacao: list[dict]

# P-INT-02 Advogado output
class TeseAdvogado(BaseModel):
    tese_principal: str
    fundamentos_invocados: list[dict]  # [{id_doc, citacao_textual, peso_vinculacao}]
    docs_consultados_ids: list[str]
    docs_efetivamente_citados_ids: list[str]
    confianca: float = Field(ge=0.0, le=1.0)

# P-INT-04 Economista output (NOVO v1.0.2)
class AnaliseMacroEconomica(BaseModel):
    ciclo_selic_periodo: str
    taxa_atipica_bool: bool
    comparacao_peer_modalities: dict
    contexto_macro_resumido: str

# P-INT-03 Juiz output
class VeredictoJuiz(BaseModel):
    c1_score: float  # 0-1 baseado em divergência BACEN
    c2_score: float  # 0-1 baseado em max(peso_vinculacao)
    c3_score: float  # 0-1 binário (jurisdição)
    aderencia: float  # média * 100
    veredito: Literal["APROVADO_100", "APROVADO_COM_RISCO_HITL", "REJEITADO"]
    razoes: list[str]
```

```python
# bloco_workflow/personas/juiz.py — função Python pura

def juiz_revisar(
    calculo: ResultadoCalculo,
    tese: TeseAdvogado,
    bacen_data: BacenData,
    uf_contrato: str
) -> VeredictoJuiz:
    """3 checagens determinísticas. Reprodutível. Auditável."""
    # C1: divergência BACEN ≥0.5pp
    divergencia = abs(Decimal(calculo.taxa_contratual) - Decimal(bacen_data.taxa_media))
    c1_score = 1.0 if divergencia >= Decimal("0.5") else float(divergencia / Decimal("0.5"))

    # C2: peso_vinculacao máximo dos docs citados
    max_peso = max((d["peso_vinculacao"] for d in tese.fundamentos_invocados), default=0)
    c2_score = 1.0 if max_peso >= 4 else max_peso / 4

    # C3: pelo menos 1 doc da jurisdição
    jurisdicoes_aceitas = {f"TJ{uf_contrato}", "STJ", "STF"}
    docs_jurisdicao = [d for d in tese.fundamentos_invocados
                       if d.get("court_id") in jurisdicoes_aceitas]
    c3_score = 1.0 if len(docs_jurisdicao) >= 1 else 0.0

    aderencia = round((c1_score + c2_score + c3_score) / 3 * 100, 1)

    if aderencia == 100.0:
        veredito = "APROVADO_100"
    elif aderencia >= 70.0:
        veredito = "APROVADO_COM_RISCO_HITL"
    else:
        veredito = "REJEITADO"

    return VeredictoJuiz(
        c1_score=c1_score, c2_score=c2_score, c3_score=c3_score,
        aderencia=aderencia, veredito=veredito,
        razoes=_compor_razoes(c1_score, c2_score, c3_score)
    )
```

```python
# bloco_workflow/personas/llm_factory.py — 2 instâncias Ollama (PATCH SUB-C)

from langchain_ollama import ChatOllama
from typing import Literal

# PATCH F-CRIT-A SUB-C: modelos diferenciados por persona
ADVOGADO_MODELS = {
    "premium":  "sabia-7b:q4_K_M",       # ~5GB — default (jurídico-crítico)
    "balanced": "qwen2.5:7b-instruct-q4_K_M",  # ~4.5GB
    "lean":     "qwen2.5:3b-instruct-q4_K_M",  # ~2GB
}

ECONOMISTA_MODEL = "qwen2.5:3b-instruct-q4_K_M"  # ~2GB — fixo (análise macro)

def get_advogado_llm(tier: Literal["lean", "balanced", "premium"] = "premium"):
    """Instância Ollama dedicada do Advogado (Sabia-7B no tier premium)."""
    return ChatOllama(model=ADVOGADO_MODELS[tier], temperature=0.2)

def get_economista_llm():
    """Instância Ollama dedicada do Economista (sempre Qwen 2.5 3B)."""
    return ChatOllama(model=ECONOMISTA_MODEL, temperature=0.3)
```

```python
# bloco_workflow/personas/advogado.py — LLM call estruturado (paralelizável)

from langchain_core.prompts import ChatPromptTemplate
import asyncio

async def advogado_redigir_tese_async(
    calculo: ResultadoCalculo,
    docs: list[JurisprudenciaItem],
    contrato_meta: ContratoMetadata,
    tier: Literal["lean", "balanced", "premium"] = "premium"
) -> TeseAdvogado:
    model = get_advogado_llm(tier)
    structured_llm = model.with_structured_output(TeseAdvogado)

    prompt = ChatPromptTemplate.from_messages([
        ("system", PROMPT_ADVOGADO_SYSTEM),
        ("user", PROMPT_ADVOGADO_USER.format(
            calculo=calculo.model_dump_json(),
            docs_disponiveis=[d.model_dump() for d in docs],
            contrato=contrato_meta.model_dump_json()
        ))
    ])

    tese = await structured_llm.ainvoke(prompt.format_messages())

    # Hard-fail: citações ⊆ docs_recuperados (anti-fantasma)
    docs_ids = {d.id_doc for d in docs}
    citados_ids = set(tese.docs_efetivamente_citados_ids)
    if not citados_ids.issubset(docs_ids):
        raise CitationFantasma(f"LLM citou docs fora do RAG: {citados_ids - docs_ids}")

    return tese


# bloco_workflow/personas/economista.py — Análise macro (Qwen 3B fixo)
async def economista_analisar_async(
    contrato_meta: ContratoMetadata,
    bacen_data: BacenData
) -> AnaliseMacroEconomica:
    model = get_economista_llm()
    structured_llm = model.with_structured_output(AnaliseMacroEconomica)
    # ... prompt + invoke async
    return await structured_llm.ainvoke(...)


# bloco_workflow/orchestrator.py — fan-out paralelo (PATCH SUB-C)
async def gerar_tese_e_analise_paralelo(
    calculo, docs, contrato_meta, bacen_data, tier="premium"
) -> tuple[TeseAdvogado, AnaliseMacroEconomica]:
    """
    PATCH SUB-C: 2 LLM calls executam EM PARALELO (asyncio.gather)
    via 2 instâncias Ollama distintas.

    Latência: max(advogado, economista) ≈ 90s (vs. soma serial 150s)
    Footprint: Sabia-7B 5GB + Qwen 3B 2GB = ~7GB (cabe em NFR-PERF-02 ≤8GB)
    """
    tese, analise = await asyncio.gather(
        advogado_redigir_tese_async(calculo, docs, contrato_meta, tier),
        economista_analisar_async(contrato_meta, bacen_data),
    )
    return tese, analise
```

### Threshold Juiz — justificativa numérica

- **100% como APROVADO_100:** mantém rigor absoluto; petição emite sem fricção apenas se TODAS as 3 checagens passam
- **70-99% como HITL:** zona de risco com decisão humana — advogado avalia se conhece precedente local não-indexado, se aceita risco etc.
- **<70% como REJEITADO:** falha em ≥2 das 3 checagens (ou 1 catastrófica) → não há fundamento jurídico mínimo para petição

Threshold 70% é defensável porque:
- C1 + C2 falhando = sem divergência BACEN material + sem jurisprudência vinculante → tese sem base
- C1 + C3 falhando = sem divergência + sem jurisdição = tese sem mérito + sem foro
- C2 + C3 falhando = sem precedente vinculante + sem jurisdição = tese inviável

Calibração futura: após 50 outcomes (Mês 6+), validar correlação `juiz_score ↔ outcome` (KPI mín ≥0.5 Pearson). Se <0.3, recalibrar.

## Razão

- **Determinismo onde a lei exige determinismo:** Perito (Decimal jurídico) e Juiz (auditabilidade) NÃO podem ser LLM
- **LLM onde criatividade fundamentada agrega:** Advogado (redação) e Economista (análise contextual) ganham com generative AI
- **Modelos LLM diferenciados por criticidade jurídica (PATCH SUB-C):**
  - Advogado precisa **Sabia-7B Premium** — tese citation-grounded fundamentada em jurisprudência brasileira é a tarefa jurídico-crítica do produto. Tier menor degradaria qualidade da peça, não aceitável.
  - Economista usa **Qwen 2.5 3B** — análise macro contextual (ciclo Selic, atipicidade de taxa, peer modalities) é raciocínio sobre dados estruturados, não geração jurídica criativa. Tier balanced é suficiente.
- **Paralelismo via asyncio.gather + 2 instâncias Ollama distintas (PATCH SUB-C):**
  - Única opção que satisfaz simultaneamente NFR-PERF-01 (≤210s) E NFR-PERF-02 (≤8GB). Footprint Sabia-7B (~5GB) + Qwen 3B (~2GB) = ~7GB total.
  - Latência max(advogado, economista) ≈ 90s vs soma serial 150-180s. Preserva SLA.
  - Smith adversarial review F-CRIT-A-2.1 expôs que premissa anterior ("1 instância serve 2 personas sem custo") era falsa: Ollama serializa requests por modelo. SUB-C é correção arquitetural validada por Eric.
- **Pydantic structured output bloqueia drift:** LLM não pode retornar texto livre; campos obrigatórios + validators
- **Hard-fail anti-fantasma já no Advogado:** validação `citations ⊆ docs` acontece ANTES do Juiz e ANTES da validação semântica (ADR-004) — defesa em profundidade

## Alternativas Consideradas

### Alt 1 — Todas as 4 personas como LLM (Multi-Agent puro)
- **Prós:** flexibilidade máxima
- **Contras:** **Juiz LLM é juridicamente inaceitável** (não-reproducible, alucinação); Perito LLM viola "Decimal everywhere"; latência 4× maior
- **Rejeitada:** viola princípios não-negociáveis

### Alt 2 — Todas as 4 personas como funções Python (zero LLM)
- **Prós:** 100% determinístico, latência mínima, sem alucinação
- **Contras:** Advogado precisa LLM (geração de texto fundamentado); Economista precisa LLM (raciocínio contextual macro)
- **Rejeitada:** perde-se a vantagem do produto

### Alt 3 — 2 LLMs distintos cloud (Sabia para Advogado, GPT-4o-mini para Economista)
- **Prós:** especialização por tarefa
- **Contras:** viola NFR-LGPD-01 (cloud)
- **Rejeitada:** LGPD não-negociável

### Alt 3-PATCH-SUB-A — Sequencial documentado (rejeitada por F-CRIT-A)
- **Prós:** simples; sem refactor de paralelismo
- **Contras:** 2 LLM calls em série em 1 instância Sabia-7B = ~150-180s só LLMs → estoura NFR-PERF-01 ≤210s; UX degradada (5min/contrato)
- **Rejeitada por Eric:** competitividade e UX inaceitáveis vs JusCalc/CalculoJurídico

### Alt 3-PATCH-SUB-B — 2 instâncias Sabia-7B paralelas (rejeitada por F-CRIT-A)
- **Prós:** preserva qualidade Sabia-7B em ambas personas
- **Contras:** 2× 5GB = ~10GB RAM → **estoura NFR-PERF-02 ≤8GB**; produto inviável em laptops 8-16GB típicos
- **Rejeitada por Eric:** RAM excessiva limita base instalada

### Alt 3-PATCH-SUB-C ✅ **ESCOLHIDA por Eric** — Economista em Qwen 2.5 3B paralelo
- **Prós:** satisfaz TODOS os NFRs (PERF-01 + PERF-02); paralelismo real; Advogado preserva qualidade Sabia-7B Premium
- **Contras:** 2 modelos para baixar/manter; Economista tier balanced em vez de premium
- **Adotada via PATCH 2026-05-01** — único caminho viável após F-CRIT-A

### Alt 4 — Threshold Juiz 80% (em vez de 70%)
- **Prós:** mais conservador
- **Contras:** REJEITA casos viáveis com 1 fraqueza compensada por 2 fortes; UX hostil (mais Inviabilidade)
- **Rejeitada:** 70% é ponto de equilíbrio entre rigor e viabilidade comercial

### Alt 5 — Threshold Juiz dinâmico (calibrado por ML estágio 1)
- **Prós:** adapta-se ao histórico
- **Contras:** estágio 2 só inicia após 50 outcomes (Mês 6+); não disponível no MVP
- **Rejeitada para MVP:** revisitar em ADR futura quando outcomes ≥50

## Consequências

### Positivas
- Auditabilidade absoluta de Perito + Juiz (juridicamente defensável)
- LLM concentrado em tarefas onde agrega valor (Advogado + Economista)
- **2 instâncias Ollama paralelas com modelos diferenciados (PATCH SUB-C):** preserva qualidade Sabia-7B no Advogado + paralelismo real via asyncio.gather + cabe em ≤8GB RAM
- **Latência máxima preservada (PATCH SUB-C):** max(advogado, economista) ≈ 90s em paralelo vs 150-180s serializado
- Threshold Juiz definitivo e justificado (DP-04 ✅ resolvido)
- Anti-fantasma já no Advogado (defesa em profundidade)
- F-CRIT-A-2.1 (Smith) NEUTRALIZADO via PATCH SUB-C — premissa arquitetural corrigida sem comprometer NFRs

### Negativas / Tradeoffs
- **2 modelos LLM para baixar e manter (PATCH SUB-C):** Sabia-7B Q4 (~5GB) + Qwen 2.5 3B Q4 (~2GB); FR-SETUP-01 estendido para baixar ambos
- **Economista tier balanced (Qwen 3B) em vez de premium (PATCH SUB-C):** tradeoff aceitável dado que análise macro contextual é menos exigente que tese jurídica
- Manter 2 prompts (Advogado + Economista) em sincronia com schema Pydantic exige disciplina
- Threshold 70% é "regra de ouro" não-empírica para MVP — depende de calibração estágio 2

### Neutras
- Migração para GPU (RTX 4070 Ti em produção) reduziria latência LLM para ~30-60s — documentado em `decisions/quality-data-modularity-assurance-2026-05-01.md`

## Configuração Ollama (PATCH 2 — F-MIN-01 RITMO 2)

> **PATCH-do-PATCH RITMO 2:** Smith F-MIN-01 expôs que ChatOllama default em 2 instâncias NÃO produz paralelismo real — Ollama serializa requests por modelo (`OLLAMA_NUM_PARALLEL=1` default). 2 clients no mesmo server compartilham fila → asyncio.gather vira placebo, F-CRIT-A retorna disfarçada.

Esta seção promove ADR-003 a `adr_level: spec` (conforme `.claude/rules/adr-scope.md`) com cobertura operacional obrigatória.

### Opção preferida: 2 servers Ollama em portas distintas

```bash
# .env
OLLAMA_HOST_ADVOGADO=http://127.0.0.1:11434
OLLAMA_HOST_ECONOMISTA=http://127.0.0.1:11435
```

```bash
# FR-SETUP-01 estendido — iniciar 2 daemons Ollama
# Daemon 1 (default port 11434) — Advogado
ollama serve &  # background

# Daemon 2 (port 11435) — Economista
OLLAMA_HOST=127.0.0.1:11435 ollama serve &  # background

# Verificação
curl http://127.0.0.1:11434/api/tags  # Advogado
curl http://127.0.0.1:11435/api/tags  # Economista
```

```python
# bloco_workflow/personas/llm_factory.py — base_url EXPLÍCITO (PATCH 2)
import os
from langchain_ollama import ChatOllama

def get_advogado_llm(tier: Literal["lean", "balanced", "premium"] = "premium"):
    return ChatOllama(
        model=ADVOGADO_MODELS[tier],
        base_url=os.environ["OLLAMA_HOST_ADVOGADO"],  # NÃO default
        temperature=0.2,
    )

def get_economista_llm():
    return ChatOllama(
        model=ECONOMISTA_MODEL,
        base_url=os.environ["OLLAMA_HOST_ECONOMISTA"],  # NÃO default
        temperature=0.3,
    )
```

**Por que preferida:** isolamento total (crash em 1 server não derruba o outro); throughput máximo (cada server tem seu próprio thread pool); auditoria clara (logs separados por persona).

### Opção alternativa: 1 server com OLLAMA_NUM_PARALLEL

```bash
# .env
OLLAMA_NUM_PARALLEL=2  # Ollama ≥0.1.33

# 1 daemon
ollama serve &
```

```python
# llm_factory.py com base_url default
def get_advogado_llm(tier="premium"):
    return ChatOllama(model=ADVOGADO_MODELS[tier], temperature=0.2)
    # base_url default = http://127.0.0.1:11434

def get_economista_llm():
    return ChatOllama(model=ECONOMISTA_MODEL, temperature=0.3)
```

**Trade-off:** mais simples (1 daemon), menos isolamento (crash do server derruba ambas personas). Aceitável para MVP single-user.

### Pinning obrigatório — `pyproject.toml` (PATCH 2 — F-MIN-02)

```toml
[project]
dependencies = [
  "langchain-ollama>=0.2.0",  # ainvoke async nativo (mitiga F-MIN-02 sync wrapper)
  # ... outras
]
```

Versões `<0.2.0` implementam `ainvoke` como `asyncio.to_thread(self.invoke)` — sync wrapper que **bloqueia o event loop**. `asyncio.gather` vira sequencial mesmo com 2 servers Ollama corretamente configurados.

### Smoke test obrigatório (Neo executa antes de release)

```python
# tests/smoke/test_paralelismo_llm.py
import asyncio
import time
import pytest
from bloco_workflow.personas.advogado import advogado_redigir_tese_async
from bloco_workflow.personas.economista import economista_analisar_async

@pytest.mark.asyncio
async def test_paralelismo_llm_real():
    """PATCH F-MIN-01 + F-MIN-02: validar que paralelismo NÃO é placebo.

    Latência paralela DEVE ser ~50-60% da latência sequencial.
    Ratio ≥0.7 → paralelismo broken (debug OLLAMA_HOST ou langchain-ollama versão).
    """
    # Inputs mínimos para LLM calls
    calculo, docs, contrato_meta, bacen_data = _fixtures()

    # Sequencial
    t0 = time.perf_counter()
    tese_seq = await advogado_redigir_tese_async(calculo, docs, contrato_meta, "premium")
    analise_seq = await economista_analisar_async(contrato_meta, bacen_data)
    latencia_serial = time.perf_counter() - t0

    # Paralelo
    t0 = time.perf_counter()
    tese_par, analise_par = await asyncio.gather(
        advogado_redigir_tese_async(calculo, docs, contrato_meta, "premium"),
        economista_analisar_async(contrato_meta, bacen_data),
    )
    latencia_paralela = time.perf_counter() - t0

    ratio = latencia_paralela / latencia_serial
    assert ratio < 0.7, (
        f"Paralelismo BROKEN: ratio={ratio:.2f} (esperado <0.7). "
        f"Verificar: OLLAMA_HOST distintos OU OLLAMA_NUM_PARALLEL=2 + langchain-ollama>=0.2.0"
    )
```

## Referências

- PRD v1.0.2: P-INT-01..04 (linhas 77-104), FR-CALC-01..03 (linhas 195-211), FR-TESE-01..04 (linhas 270-301), FR-JUIZ-01..03 (linhas 305-337)
- Resolve DP-04 (PRD linha 771): threshold definitivo 70%/100%
- ADR-001 (state machine + _LockedSqliteSaver expandido em PATCH 2)
- ADR-004 (validação semântica complementar — defesa em profundidade pós-Advogado)
- Sabia-7B GGUF: https://huggingface.co/TheBloke/sabia-7B-GGUF
- Pydantic structured output LangChain: https://python.langchain.com/docs/how_to/structured_output/
- Ollama OLLAMA_NUM_PARALLEL: https://github.com/ollama/ollama/blob/main/docs/faq.md#how-can-i-allow-additional-web-origins-to-access-ollama
- langchain-ollama 0.2.0 changelog: https://github.com/langchain-ai/langchain/releases/tag/langchain-ollama%3D%3D0.2.0
- Rule de framework: `.claude/rules/adr-scope.md` (formaliza adr_level: spec)

---

*Aria, separando o que precisa ser determinístico do que pode ser criativo. PATCH-do-PATCH RITMO 2 fecha o último gap arquitetural antes de Neo começar. 🏗️*
