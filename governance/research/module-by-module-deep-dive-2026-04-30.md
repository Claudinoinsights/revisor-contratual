---
type: research
title: "Revisor Contratual — Module-by-Module Deep Dive"
project: revisor-contratual
author: "@analyst (Atlas)"
date: "2026-04-30"
status: draft
companion_doc: "state-of-the-art-2026-04-30.md"
tags:
  - project/revisor-contratual
  - research
  - architecture-review
  - module-analysis
  - blocos
  - solidity-audit
related:
  - ".project.yaml"
  - "research/state-of-the-art-2026-04-30.md"
sources_count: 25
verification_pending:
  - "Cardinalidade real do vault de jurisprudência (STJ/STF/TJ-MG iniciais)"
  - "Comportamento Streamlit + LangGraph astream sob HITL com interrupt() na prática"
  - "Performance numpy_financial vs Decimal em loop de 360 parcelas"
---

# Revisor Contratual — Module-by-Module Deep Dive

> **Missão:** Eric não sentiu solidez na estrutura proposta. Vou dissecar **arquivo por arquivo** dos 4 blocos, identificar fragilidades pontuais, pesquisar alternativas, e propor patches concretos. Esse documento complementa o `state-of-the-art-2026-04-30.md` (que cobriu camadas tecnológicas) com análise **estrutural** dos módulos.
>
> **Princípio de Solidez (definição operacional):**
> Um módulo é sólido quando: (a) tem **um único motivo para falhar**, (b) **falha rápido e barulhento** (não silenciosamente), (c) é **testável em isolamento**, (d) tem **contratos explícitos** com módulos vizinhos, e (e) seu estado é **observável** em runtime.

---

## ⚠️ Diagnóstico geral antes da dissecação

Sua estrutura tem **3 fragilidades estruturais transversais** que se manifestam em todos os 4 blocos:

### Fragilidade #1 — Acoplamento implícito não-documentado
Os blocos passam dados via **strings e dicts soltos** (ex: `texto_contrato_estruturado: String`, `metadados_contrato: Dicionário`). Não há **contratos formais** (Pydantic models compartilhados) entre blocos. Resultado: mudança no Bloco 4 quebra Bloco 2 sem aviso de tipo.

> **Impacto:** Refactors viram caça-bug; debugging entre blocos vira tentativa-e-erro.
> **Patch:** Criar `bloco_contratos/` com Pydantic models partilhados (`ContratoExtraido`, `ResultadoCalculo`, `JurisprudenciaItem`).

### Fragilidade #2 — Falta de "fail loud" em validações jurídicas
Nada na estrutura define **o que acontece se um cálculo retornar NaN, ou se o BACEN retornar lixo, ou se o vault não tiver nenhum doc para a UF**. Cada arquivo precisa decidir. Resultado: silent failures se acumulam até o Juiz Revisor.

> **Impacto:** Petição gerada com dados zerados sem alarme; advogado descobre só revisando manualmente.
> **Patch:** Cada `@tool` LangChain DEVE retornar `Result[T, Erro]` (Rust-style) ou levantar exceção tipada. Nó intermediário valida antes de prosseguir.

### Fragilidade #3 — Observabilidade ausente
Não há tracing entre nós LangGraph, latência de cada tool, ou audit-log do que cada agente "viu" antes de decidir. Quando algo der errado em produção, **só Deus sabe** qual foi a causa.

> **Impacto:** Bug em campo = reproduzir manualmente o caso; sem replay.
> **Patch:** Logs estruturados (structlog) + LangSmith local OU OpenTelemetry + Jaeger + LangGraph checkpointer com state snapshots.

---

# 🟦 BLOCO 1 — Front-end e Intervenção Humana (UI)

## Estrutura proposta (sua)
```text
bloco_interface/
├── app.py
├── componentes/
│   ├── uploader.py
│   ├── visualizador_chat.py
│   └── painel_intervencao.py
└── utils/
    └── formatador_pdf.py
```

## Análise pontual arquivo-por-arquivo

### `app.py` — Entrypoint Streamlit

**Fragilidades identificadas:**
1. **Single-file entrypoint sem state isolation**: Streamlit executa `app.py` inteiro a cada interação. Toda lógica de roteamento de páginas, sessão, e callbacks fica num só arquivo → bug de scope.
2. **Sem separação UI ↔ workflow**: Implícito que app.py vai chamar LangGraph diretamente — mas o spec diz que o Bloco 2 é o "cérebro". Onde está o cliente HTTP do app.py para o backend?
3. **Nenhuma menção a `st.session_state` para HITL**: como você vai persistir o estado de "aguardando aprovação" entre reruns?

**Pesquisa:**
- Padrão consagrado 2026: **agent-service-toolkit** (JoshuaC215) usa **FastAPI como camada intermediária** entre Streamlit e LangGraph. Streamlit faz HTTP calls. Razão: Streamlit não consegue manter websocket persistente nem rodar background tasks confiáveis ([GitHub agent-service-toolkit](https://github.com/JoshuaC215/agent-service-toolkit)).
- LangGraph v1.0 expõe `interrupt()` (HITL nativo) e `Command` (resume com input do usuário) que NÃO funcionam direto em Streamlit sync — precisa de bridge async.

**Patch concreto:**
```text
bloco_interface/
├── api_client.py          # ← NOVO: HTTP client tipado para FastAPI backend
├── session.py             # ← NOVO: gestão isolada de st.session_state
├── pages/                 # ← NOVO: multi-page Streamlit
│   ├── 1_upload.py
│   ├── 2_processamento.py
│   └── 3_resultado.py
├── componentes/
│   ├── uploader.py
│   ├── visualizador_chat.py
│   └── painel_intervencao.py
└── utils/
    └── formatador_pdf.py
```

**Veredicto:** `app.py` precisa virar **shell de roteamento**, NÃO o monólito. Lógica de chamada ao workflow vai para `api_client.py`.

---

### `componentes/uploader.py` — Upload PDF + metadados

**Fragilidades identificadas:**
1. **Sem validação de tamanho/formato**: PDF de 100MB? PDF criptografado? PDF com macros maliciosas?
2. **"Estado de jurisdição" como input livre**: usuário pode digitar "MG", "Minas Gerais", "Minas", "minas gerais", "M.G." — vai quebrar filtro do Bloco 3.
3. **"Data de assinatura" sem validação**: data futura? data anterior à existência do BACEN SGS (1986)? formato livre?
4. **Sem quarantine pre-parse**: PDF entra direto no parser. Se for malicioso, parser ataca o sistema.

**Pesquisa:**
- OWASP File Upload guideline: validar magic bytes (`%PDF-`), max size, scan AV (ClamAV opcional), processar em sandbox.
- Streamlit `st.file_uploader` retorna `BytesIO`, não persiste em disco — bom para isolamento mas precisa de validação proativa.

**Patch concreto:**
```python
# uploader.py
from pydantic import BaseModel, Field, field_validator
from datetime import date
from enum import Enum

class UF(str, Enum):
    AC = "AC"; AL = "AL"; AP = "AP"; AM = "AM"; BA = "BA"
    CE = "CE"; DF = "DF"; ES = "ES"; GO = "GO"; MA = "MA"
    MT = "MT"; MS = "MS"; MG = "MG"; PA = "PA"; PB = "PB"
    PR = "PR"; PE = "PE"; PI = "PI"; RJ = "RJ"; RN = "RN"
    RS = "RS"; RO = "RO"; RR = "RR"; SC = "SC"; SP = "SP"
    SE = "SE"; TO = "TO"

class UploadContrato(BaseModel):
    uf: UF                             # enum força validação
    data_assinatura: date              # ISO format obrigatório
    valor_financiado: Decimal | None   # opcional, mas se vier, é Decimal

    @field_validator("data_assinatura")
    @classmethod
    def data_no_futuro(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Data de assinatura não pode ser futura")
        if v < date(1986, 1, 1):
            raise ValueError("BACEN SGS não cobre antes de 1986")
        return v

def validar_pdf(file_bytes: bytes) -> None:
    if not file_bytes.startswith(b"%PDF-"):
        raise ValueError("Arquivo não é PDF válido (magic bytes)")
    if len(file_bytes) > 100 * 1024 * 1024:
        raise ValueError("PDF acima de 100MB")
    # opcional: ClamAV scan
```

**Veredicto:** Adicionar **Pydantic + UF enum + validação magic bytes** elimina toda uma classe de bugs.

---

### `componentes/visualizador_chat.py` — Stream do debate de agentes

**Fragilidades identificadas:**
1. **"Consumir o stream do LangGraph"**: como? `astream`, `astream_events`, ou polling do checkpointer? Cada um tem semântica diferente.
2. **Streamlit não tem container que recebe stream nativo**: você precisa de loop manual com `placeholder.markdown()` — se rodar via FastAPI, precisa SSE client em Python ou JS.
3. **Sem reconexão**: se WebSocket cair em meio ao workflow de 5min, usuário perde o painel.
4. **Sem timestamps nem IDs por mensagem**: impossível auditar depois.

**Pesquisa:**
- LangGraph 2026 expõe `astream` com `stream_mode="messages" | "values" | "updates" | "custom"` ([LangChain docs](https://docs.langchain.com/oss/python/langgraph/streaming)).
- Para custom data por nó (ex: "Perito está calculando..."), usar `get_stream_writer` dentro do nó + `stream_mode="custom"`.
- Padrão SSE LangGraph→FastAPI→cliente: encoder JSON line-delimited, com tipo de evento (`token`, `tool_call`, `interrupt`, `error`).

**Patch concreto:**
```python
# visualizador_chat.py — versão SSE-aware
import streamlit as st
from sseclient import SSEClient   # pip install sseclient-py
import json
import time

def renderizar_stream(task_id: str, api_url: str):
    placeholder = st.empty()
    mensagens = []

    try:
        url = f"{api_url}/stream/{task_id}"
        for event in SSEClient(url):
            evt = json.loads(event.data)

            mensagens.append({
                "id": evt.get("id"),
                "timestamp": evt.get("ts", time.time()),
                "agente": evt.get("agent"),
                "tipo": evt.get("type"),       # token | tool_call | interrupt | done | error
                "conteudo": evt.get("content")
            })

            # Re-renderiza painel inteiro a cada evento (Streamlit pattern)
            with placeholder.container():
                for msg in mensagens:
                    render_mensagem(msg)

            if evt.get("type") == "interrupt":
                # Sinaliza para painel_intervencao.py renderizar botões
                st.session_state["aguardando_aprovacao"] = True
                st.session_state["interrupt_payload"] = evt
                break  # Para o loop até usuário decidir
    except Exception as e:
        st.error(f"Conexão SSE perdida: {e}. Tentando reconectar...")
        # Implementar exponential backoff
```

**Veredicto:** Stream sem **tipo de evento + timestamps** + **handling de interrupt** = caixa preta. Precisa de protocolo SSE explícito.

---

### `componentes/painel_intervencao.py` — HITL approve/reject/abort

**Fragilidades identificadas:**
1. **3 botões mas SEM contexto sobre o que está sendo aprovado**: "Aprovar Tese com Risco" — qual risco? quanto risco? em qual dimensão (matemática? jurisprudência?)
2. **"Solicitar Recálculo"** — recálculo do quê? de toda a thread ou só do nó do Perito?
3. **Sem audit-trail da decisão humana**: quem aprovou, em qual horário, vendo qual estado do grafo?
4. **Sem timeout**: usuário some, workflow fica órfão para sempre.

**Pesquisa:**
- LangGraph `interrupt(value)` permite passar dados arbitrários ao usuário; `Command(resume=user_input)` retorna decisão tipada para o grafo ([LangChain docs](https://docs.langchain.com/oss/python/langgraph/streaming)).
- Padrão recomendado: serializar **estado relevante** + **opções tipadas** no payload do interrupt.

**Patch concreto:**
```python
# painel_intervencao.py
import streamlit as st
from pydantic import BaseModel
from enum import Enum
from typing import Literal

class DivergenciaJuiz(BaseModel):
    aderencia_pct: float                    # 0-100
    razoes: list[str]                       # ["taxa não exatamente igual BACEN", "súmula é STF mas não vinculante"]
    risco_classificado: Literal["BAIXO", "MEDIO", "ALTO"]
    impacto_se_aprovar: str
    sugestao_juiz: str

class DecisaoHumana(BaseModel):
    acao: Literal["APROVAR_COM_RISCO", "RECALCULAR_NO", "ABORTAR_INVIABILIDADE"]
    no_para_recalcular: str | None = None   # se RECALCULAR
    justificativa: str                      # OBRIGATÓRIO — vai para audit-log
    timestamp: datetime
    user_id: str

def renderizar_painel(payload: DivergenciaJuiz, task_id: str) -> DecisaoHumana | None:
    st.warning(f"⚠️ Aderência: {payload.aderencia_pct:.1f}% — Risco: {payload.risco_classificado}")
    st.write("**Razões da divergência:**")
    for r in payload.razoes:
        st.write(f"- {r}")
    st.info(f"**Sugestão do Juiz Revisor:** {payload.sugestao_juiz}")

    justificativa = st.text_area(
        "Justificativa da sua decisão (obrigatório p/ audit-log):",
        max_chars=500,
        key=f"just_{task_id}"
    )
    if not justificativa or len(justificativa) < 20:
        st.warning("Justificativa muito curta (min 20 chars).")
        return None

    col1, col2, col3 = st.columns(3)
    if col1.button("✅ Aprovar com Risco", key=f"apr_{task_id}"):
        return DecisaoHumana(acao="APROVAR_COM_RISCO", justificativa=justificativa, ...)
    if col2.button("🔄 Recálculo (Perito)", key=f"rec_{task_id}"):
        return DecisaoHumana(acao="RECALCULAR_NO", no_para_recalcular="agente_perito", ...)
    if col3.button("🛑 Abortar (Inviabilidade)", key=f"abt_{task_id}"):
        return DecisaoHumana(acao="ABORTAR_INVIABILIDADE", justificativa=justificativa, ...)
    return None
```

**Veredicto:** Painel sem **payload tipado da divergência** + **justificativa obrigatória** = decisão jurídica não-rastreável → invalida o produto judicialmente.

---

### `utils/formatador_pdf.py` — Geração da petição final

**Fragilidades identificadas:**
1. **Sem template estruturado**: vai gerar PDF como? texto puro? com formatação ABNT? com cabeçalho de petição?
2. **Sem versionamento do template**: petição do mês passado tem mesmo layout da deste mês?
3. **Sem assinatura digital ou hash**: como garantir que o PDF entregue é o que o sistema gerou?

**Pesquisa:**
- Bibliotecas: **`fpdf2`** (simples, controle baixo) | **`weasyprint`** (HTML/CSS → PDF, mais flexível) | **`reportlab`** (industrial, complexo) | **`docxtpl` + LibreOffice headless** (template Word → PDF, ideal para advogados).
- Padrão recomendado: HTML/CSS template (Jinja2) → WeasyPrint → PDF. Permite versionamento por git.

**Patch concreto:**
```python
# formatador_pdf.py
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import hashlib
from pathlib import Path

class GeradorPeticao:
    def __init__(self, templates_dir: Path):
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def gerar_peticao_revisional(self, contexto: dict, output_path: Path) -> dict:
        template = self.env.get_template("peticao_revisional_v1.html.j2")
        html_content = template.render(**contexto)
        HTML(string=html_content).write_pdf(output_path)

        # Hash para auditoria
        with open(output_path, "rb") as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()

        return {"path": str(output_path), "sha256": sha256, "template_version": "v1"}
```

**Veredicto:** Petição é o **deliverable jurídico** — não pode ser gerada com `fpdf("Olá mundo")`. Precisa template versionado + hash de auditoria.

---

## 🟦 Veredicto Bloco 1

**Solidez atual:** 🔴 Baixa — entrega o conceito mas falha em todos os 5 critérios de solidez.

**Patches críticos (em ordem de impacto):**
1. **Adicionar `api_client.py`** + arquitetura Streamlit → FastAPI → LangGraph (não acoplar diretamente)
2. **Pydantic em todo input** — UploadContrato, DivergenciaJuiz, DecisaoHumana
3. **Protocolo SSE explícito** com tipos de evento + timestamps
4. **Painel HITL com payload tipado + justificativa obrigatória**
5. **Petição via Jinja2 + WeasyPrint + hash auditoria**

---

# 🟦 BLOCO 2 — Orquestração, Estado e Agentes (Cérebro)

## Estrutura proposta (sua)
```text
bloco_agentes/
├── orquestrador/
│   ├── grafo_estado.py
│   └── definicao_nos_arestas.py
├── personas/
│   ├── agente_perito.py
│   ├── agente_economista.py
│   ├── agente_advogado.py
│   └── agente_juiz_revisor.py
└── prompts/
    └── instrucoes_base.md
```

## Análise pontual arquivo-por-arquivo

### `orquestrador/grafo_estado.py` — TypedDict do estado global

**Fragilidades identificadas:**
1. **TypedDict puro sem reducers**: ao atualizar `jurisprudencia_recuperada` (lista) em paralelo a partir de múltiplos nós, o último escreve por cima — perde resultados. Mesmo problema com `motivo_rejeicao` se o Juiz adicionar múltiplos motivos.
2. **Tipos primitivos em campos críticos**: `taxa_contrato: float`. Float é PROIBIDO em finanças (perda de precisão). Mesmo problema em `valor_incontestado`.
3. **Nada captura história intermediária** (turnos do debate). Como você reconstrói o que o Perito disse na 2ª iteração se o Juiz pedir recálculo?
4. **Sem versão do schema**: refactor do estado quebra checkpointer existente sem aviso.

**Pesquisa:**
- LangGraph state DEVE usar `Annotated[list, operator.add]` ou `add_messages` para campos que acumulam ([LangChain docs](https://docs.langchain.com/oss/python/langgraph/use-graph-api), [Shaza Ali Substack](https://shazaali.substack.com/p/type-safety-in-langgraph-when-to)).
- TypedDict é o padrão recomendado pelo time LangGraph (não Pydantic) — mas com validação manual nos nós críticos.
- Pydantic BaseModel só valida no PRIMEIRO nó — não em nós subsequentes (limitação documentada).
- Para precisão financeira: `decimal.Decimal` ou `Money` (lib money-math).

**Patch concreto:**
```python
# grafo_estado.py
from typing import TypedDict, Annotated, Literal
from operator import add
from decimal import Decimal
from datetime import datetime
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# Schema versioning (CRÍTICO para checkpointer compatibility)
SCHEMA_VERSION = "1.0.0"

class MetadadosContrato(TypedDict):
    uf: str
    data_assinatura: str               # ISO 8601
    valor_financiado: str              # Decimal serializado como string
    modalidade: Literal["VEICULO", "IMOBILIARIO", "CDC", "CARTAO"]

class ResultadoCalculo(TypedDict):
    taxa_contrato_aa: str              # Decimal string
    taxa_bacen_aa: str                 # Decimal string
    valor_incontestado: str            # Decimal string
    divergencia_pct: str               # Decimal string
    metodo_calculo: str                # ex: "tabela_price_juros_compostos"
    timestamp_calculo: datetime
    fonte_taxa_bacen: str              # ex: "SGS_25471_2024-03"

class JurisprudenciaItem(TypedDict):
    id_doc: str                        # ID único no vault
    court_id: str                      # TJMG, STJ, STF
    binding: bool                      # vinculante?
    tipo: Literal["SUMULA", "TEMA_REPETITIVO", "ACORDAO", "PRECEDENTE"]
    numero: str                        # ex: "Tema 247/STJ"
    ementa: str
    texto_relevante: str
    score_relevancia: float

class TurnoDebate(TypedDict):
    iteracao: int
    agente: Literal["PERITO", "ECONOMISTA", "ADVOGADO", "JUIZ"]
    output: str
    timestamp: datetime

class EstadoRevisor(TypedDict):
    schema_version: str
    texto_contrato_estruturado: str
    metadados_contrato: MetadadosContrato

    # Reducers para campos que acumulam ao longo do debate
    resultados_calculo: Annotated[list[ResultadoCalculo], add]    # múltiplas iterações
    jurisprudencia_recuperada: Annotated[list[JurisprudenciaItem], add]
    historico_debate: Annotated[list[TurnoDebate], add]
    motivos_rejeicao_juiz: Annotated[list[str], add]

    # Campos finais
    status_aprovacao_juiz: bool | None
    decisao_humana: dict | None        # quando HITL ativado
    iteracoes_realizadas: int
```

**Veredicto:** TypedDict atual é **frágil** para multi-nó concorrente e **proibitivo** para finanças (float). Reducers + Decimal-as-string são obrigatórios.

---

### `orquestrador/definicao_nos_arestas.py` — Grafo + edges

**Fragilidades identificadas:**
1. **Aresta condicional única (Juiz aprova/rejeita)**: e se o Juiz aprovar com risco médio? não há terceira via.
2. **Sem retry policy**: nó do Economista falhou ao chamar BACEN — qual a política? abortar? retry quantas vezes?
3. **Sem timeout por nó**: nó do Advogado pode ficar 10min consultando RAG sem limite.
4. **Loops permitidos sem guard**: se Juiz pedir recálculo, e o recálculo gerar nova divergência, e o Juiz pedir de novo... infinito.

**Pesquisa:**
- LangGraph suporta `RetryPolicy` por nó com `retry_on`, `max_attempts`, `backoff_factor`.
- `recursion_limit` previne loops infinitos (default 25).
- Conditional edges podem retornar múltiplas chaves (não apenas binário).

**Patch concreto:**
```python
# definicao_nos_arestas.py
from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy, interrupt, Command

workflow = StateGraph(EstadoRevisor)

# Retry policies por tipo de falha
RETRY_BACEN = RetryPolicy(
    max_attempts=5,
    initial_interval=1.0,
    backoff_factor=2.0,
    retry_on=[TimeoutError, ConnectionError]
)

RETRY_LLM = RetryPolicy(
    max_attempts=3,
    retry_on=[Exception]  # mais conservador
)

workflow.add_node("agente_perito", node_perito, retry=RETRY_LLM)
workflow.add_node("agente_economista", node_economista, retry=RETRY_BACEN)
workflow.add_node("agente_advogado", node_advogado, retry=RETRY_LLM)
workflow.add_node("agente_juiz", node_juiz)
workflow.add_node("hitl_pause", node_hitl)
workflow.add_node("relatorio_inviabilidade", node_inviabilidade)
workflow.add_node("peticao_final", node_peticao)

# Aresta condicional com 3 saídas, não 2
def roteador_juiz(state: EstadoRevisor) -> Literal["peticao_final", "hitl_pause", "relatorio_inviabilidade"]:
    if state["iteracoes_realizadas"] >= 3:  # ← Guard contra loop infinito
        return "relatorio_inviabilidade"

    aderencia = calcular_aderencia(state)
    if aderencia >= 100:
        return "peticao_final"
    elif 70 <= aderencia < 100:
        return "hitl_pause"      # ← humano decide
    else:
        return "relatorio_inviabilidade"

workflow.add_conditional_edges("agente_juiz", roteador_juiz)

# Compile com checkpointer + interrupt antes de HITL
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("./bloco_agentes/state.db")

graph = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["hitl_pause"]   # nativo HITL
)
```

**Veredicto:** Aresta condicional binária + sem retry/timeout/guard = workflow morre de fome em produção.

---

### `personas/agente_perito.py` — Cálculos via tools

**Fragilidades identificadas:**
1. **"Proibido fazer contas usando o LLM"** — como ENFORÇAR? prompt promete, mas LLM pode "inventar" um número se a tool falhar.
2. **Sem fallback se a tool de BACEN falhar**: Perito tenta tool, tool falha (404, timeout) — Perito alucina taxa? aborta? entra em loop?
3. **Output do Perito é texto livre + chave `resultados_calculo`** — quem garante que o texto reflete os números?

**Pesquisa:**
- Padrão LangChain "structured output": forçar Perito a retornar **Pydantic model** validado, não texto livre.
- Function calling robusto: Llama 3.1+ e Sabia-7B suportam — mas Sabia-7B é geração antiga, function calling pode ser limitado. Validar.
- "Tool failure as state" — em vez de exception, retornar `Result.fail(reason)` e deixar o nó decidir.

**Patch concreto:**
```python
# agente_perito.py
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

class OutputPerito(BaseModel):
    metodologia_aplicada: str = Field(description="Ex: Tabela Price com juros compostos mensais")
    taxa_contrato_aa: str = Field(description="Decimal string, ex: '0.245' = 24.5% a.a.")
    taxa_bacen_aa: str
    valor_incontestado: str
    divergencia_pct: str
    raciocinio: str = Field(description="Justifica a metodologia e cita os números das tools")
    fontes_chamadas: list[str] = Field(description="Lista de tools chamadas, ex: ['get_taxa_bacen(25471, 2024-03)']")

def node_perito(state: EstadoRevisor) -> dict:
    parser = PydanticOutputParser(pydantic_object=OutputPerito)

    # Sistema do Perito FORÇA structured output e proíbe inventar números
    system = """Você é o Perito Contábil. REGRAS ABSOLUTAS:
1. NUNCA calcule mentalmente — chame a tool `motor_tabela_price` ou `calculadora_bacen_sgs`.
2. Se uma tool falhar 3x, retorne `divergencia_pct = "ERRO_TOOL"` e raciocínio explicando.
3. Cite EXATAMENTE qual tool chamou em `fontes_chamadas`.

Schema obrigatório de saída:
{parser.get_format_instructions()}
"""
    # ... LLM call com tools bound ...

    output_struct = parser.parse(llm_response)

    # Validação cruzada: o output do LLM bate com as tool calls reais?
    if output_struct.fontes_chamadas == []:
        raise PeritoSemFontesError("Perito não chamou nenhuma tool — saída suspeita")

    if output_struct.taxa_bacen_aa not in [str(t.result) for t in tool_history]:
        raise PeritoInventouNumeroError(f"Taxa BACEN no output ({output_struct.taxa_bacen_aa}) não bate com tool history")

    return {
        "resultados_calculo": [output_struct.dict()],
        "historico_debate": [{"iteracao": ..., "agente": "PERITO", ...}]
    }
```

**Veredicto:** Texto livre + promessa-no-prompt = Perito vai mentir. **Pydantic structured output + validação cruzada com tool history** é a única blindagem real.

---

### `personas/agente_economista.py` — Análise BACEN

**Fragilidades identificadas:**
1. **Função do Economista vs Perito**: ambos chamam BACEN? Quem tem responsabilidade canônica?
2. **Não está claro qual valor agregado o Economista traz**: o Perito já consulta BACEN. O que o Economista faz diferente?
3. **Possível duplicação ou nó morto**: se o Perito já tem todos os dados, o Economista é overhead.

**Pesquisa:**
- Em multi-agent systems, **separation of concerns** evita "double work" e ambiguidade.
- Padrão recomendado: Economista = **contextualização macro** (ex: "a taxa BACEN nesse mês foi atípica devido a ciclo de alta da Selic em XX/2024") enquanto Perito = **cálculo cru**.

**Patch concreto:**
Definir claramente o **escopo** de cada um:

| Persona | Responsabilidade EXCLUSIVA | NÃO faz |
|---------|--------------------------|---------|
| **Perito** | Cálculo numérico via tools (Price, ipmt, BACEN spot rate) | Análise contextual; redação jurídica |
| **Economista** | Análise contextual da taxa (era atípica? ciclo monetário? comparação com peer modalities) | Cálculo numérico |
| **Advogado** | RAG jurisprudência + redação tese | Cálculo; análise macro econômica |
| **Juiz** | Validação 100% aderência | Geração — só decide |

**OU eliminar Economista** se você não consegue justificar uma responsabilidade exclusiva. **Princípio:** persona sem escopo único é um nó morto que aumenta latência sem agregar.

**Veredicto:** Reavaliar se o Economista é um nó real ou se é uma extensão do Perito. Se manter, dar **escopo cirúrgico** (análise macro contextual, NÃO cálculo).

---

### `personas/agente_advogado.py` — Tese via RAG

**Fragilidades identificadas:**
1. **"Proibido citar leis de memória"** — como enforçar? mesma fragilidade do Perito.
2. **"Redige tese com base exclusiva nos documentos retornados"** — e se o RAG retornar 0 docs? alucina? aborta?
3. **Sem ranking de fonte** no output: tese cita Súmula 539 STJ + acórdão TJ-MG — mas qual peso cada um tem?
4. **Sem validação de pertinência da tese ao contrato analisado**: tese pode ser sobre "abusividade de juros" quando o contrato é "anatocismo" (temas relacionados mas distintos).

**Pesquisa:**
- Padrão "Citation-grounded generation": cada parágrafo da tese DEVE referenciar `[id_doc:N]`. LLM com structured output pode forçar isso.
- Re-ranking pós-retrieval: usar cross-encoder Legal-BERTimbau para ordenar top-20 → top-5 antes de passar ao LLM.

**Patch concreto:**
```python
# agente_advogado.py
class OutputAdvogado(BaseModel):
    tese_principal: str = Field(description="2-3 parágrafos com [id_doc:N] em cada citação")
    fundamentos_invocados: list[dict]  # [{"id_doc": "...", "tipo": "SUMULA", "tese_aplicavel": "..."}]
    docs_consultados_ids: list[str]
    docs_efetivamente_citados_ids: list[str]
    confianca: float                   # 0-1, baseado em score do RAG + numero de fontes vinculantes

def node_advogado(state: EstadoRevisor) -> dict:
    metadados = state["metadados_contrato"]

    # 1. RAG com filtro estrito
    docs = retriever.search(
        query=construir_query_jurisprudencia(state),
        filtro={
            "court_id": ["STJ", "STF", f"TJ{metadados['uf']}"],
            "binding": True,
            "modalidade_relacionada": metadados["modalidade"]
        },
        top_k=20
    )

    # 2. Re-rank com cross-encoder Legal-BERTimbau
    docs_reranked = cross_encoder.rerank(query, docs, top_n=5)

    # 3. Hard-fail se zero docs
    if len(docs_reranked) == 0:
        return {
            "motivos_rejeicao_juiz": ["RAG_VAZIO: Nenhuma jurisprudência aplicável encontrada"],
            "status_aprovacao_juiz": False
        }

    # 4. LLM com prompt que FORÇA citation-grounded
    output = llm_advogado.invoke([...])

    # 5. Validação: docs citados ⊆ docs consultados?
    if not set(output.docs_efetivamente_citados_ids).issubset(set(output.docs_consultados_ids)):
        raise AdvogadoCitouDocFantasmaError(...)

    return {"tese": output.dict(), "jurisprudencia_recuperada": docs_reranked}
```

**Veredicto:** Sem **citation-grounded + RAG filter strict + hard-fail em RAG vazio**, o Advogado vai gerar petição com fundamentos fabricados — risco judicial enorme.

---

### `personas/agente_juiz_revisor.py` — Validação 100%

**Fragilidades identificadas:**
1. **3 checagens "sistêmicas" mas não definidas como assertions matemáticas**: "A taxa do BACEN é inferior à cobrada?" — quanto inferior? 0.01%? 1%? 10%? Sem threshold formal.
2. **"Jurisprudência retornada é vinculante?"** — binário sim/não, mas vinculação tem gradação (Súmula Vinculante > Tema Repetitivo > Acórdão STJ > Acórdão TJ).
3. **"Tribunal pesquisado é o mesmo da jurisdição informada?"** — STJ é nacional, então essa checagem precisa de exceção.
4. **Sem score de aderência granular**: 100% ou aborta. Mas vida real é cinza — daí o HITL fazer sentido. Mas o Juiz precisa retornar % aderência, não só bool.

**Pesquisa:**
- STF Súmula 121: anatocismo proibido em casos não-SFN.
- STJ Súmula 539: capitalização infra-anual permitida no SFN com pactuação expressa ([Migalhas](https://www.migalhas.com.br/depeso/317971/sumula-121-do-stf-e-anatocismo-na-tabela-price)).
- Hierarquia de vinculação: Súmula Vinculante (peso 5) > Repetitivo STJ (peso 4) > Súmula STJ (peso 3) > Acórdão STJ (peso 2) > TJ vinculante (peso 1).

**Patch concreto:**
```python
# agente_juiz_revisor.py
class ChecagemJuiz(BaseModel):
    nome: str
    passou: bool
    score: float             # 0-1
    razao: str
    threshold_aplicado: str

class OutputJuiz(BaseModel):
    checagens: list[ChecagemJuiz]
    aderencia_total: float   # 0-100
    veredicto: Literal["APROVADO_100", "APROVADO_COM_RISCO_HITL", "REJEITADO"]
    racional: str

THRESHOLDS = {
    "divergencia_minima_taxa": 0.005,   # 0.5% — abaixo disso é "ruído matemático"
    "score_juris_minimo": 0.7,
    "peso_minimo_vinculacao": 3         # exige ao menos Súmula STJ
}

def checar_taxa_inferior(state) -> ChecagemJuiz:
    div = float(state["resultados_calculo"][-1]["divergencia_pct"])
    passou = div >= THRESHOLDS["divergencia_minima_taxa"]
    return ChecagemJuiz(
        nome="taxa_bacen_inferior",
        passou=passou,
        score=min(div / 0.05, 1.0),  # até 5% acima é nota cheia
        razao=f"Divergência de {div:.4%} entre contrato e BACEN",
        threshold_aplicado=f">= {THRESHOLDS['divergencia_minima_taxa']:.4%}"
    )

def checar_jurisprudencia_vinculante(state) -> ChecagemJuiz:
    docs = state["jurisprudencia_recuperada"]
    pesos = [peso_vinculacao(d) for d in docs]
    peso_max = max(pesos) if pesos else 0
    passou = peso_max >= THRESHOLDS["peso_minimo_vinculacao"]
    return ChecagemJuiz(...)

def checar_jurisdicao(state) -> ChecagemJuiz:
    uf = state["metadados_contrato"]["uf"]
    cortes_validas = {"STJ", "STF", f"TJ{uf}"}
    docs = state["jurisprudencia_recuperada"]
    docs_validos = [d for d in docs if d["court_id"] in cortes_validas]
    passou = len(docs_validos) > 0
    return ChecagemJuiz(...)

def node_juiz(state) -> dict:
    checagens = [checar_taxa_inferior(state), checar_jurisprudencia_vinculante(state), checar_jurisdicao(state)]
    aderencia = sum(c.score for c in checagens) / len(checagens) * 100

    if aderencia == 100:
        veredicto = "APROVADO_100"
    elif aderencia >= 70:
        veredicto = "APROVADO_COM_RISCO_HITL"   # ← dispara interrupt
    else:
        veredicto = "REJEITADO"

    return {"juiz_output": OutputJuiz(...).dict()}
```

**Veredicto:** Juiz binário com checagens não-quantificadas é caixa preta. **Score por checagem + thresholds explícitos + 3-vias** dá auditabilidade jurídica.

---

### `prompts/instrucoes_base.md` — Prompts compartilhados

**Fragilidades identificadas:**
1. **Único arquivo .md** para todos os agentes? prompts compartilhados é anti-pattern (cada persona tem necessidades distintas).
2. **Sem versionamento**: prompts evoluem; mudanças invalidam testes.
3. **Sem testes de prompt**: como saber que o prompt do Perito ainda funciona com Sabia-7B após upgrade?

**Pesquisa:**
- Padrão moderno: **Prompt como código** — versionado em git, com testes (DeepEval, promptfoo).
- Estrutura: 1 arquivo por persona + 1 arquivo de "base persona" + 1 arquivo de "regras universais".

**Patch concreto:**
```text
prompts/
├── _base/
│   ├── regras_universais.md         # No Invention, formato output, etc.
│   └── persona_juridico_brasileiro.md
├── perito/
│   ├── system_v1.md
│   ├── few_shot_examples.json
│   └── tests.yaml                   # promptfoo config
├── economista/...
├── advogado/...
└── juiz/
    ├── system_v1.md
    └── tests.yaml
```

**Veredicto:** Único arquivo é dívida técnica que vira inferno na primeira mudança de modelo.

---

## 🟦 Veredicto Bloco 2

**Solidez atual:** 🟡 Média — conceito bom (state-machine + persona separation + Juiz validador) mas execução frágil em 5 dimensões: state shape, retry/timeout, structured output, citation grounding, e quantificação de checagens.

**Patches críticos (em ordem de impacto):**
1. **Reducers + Decimal-as-string** no EstadoRevisor (reescrever schema)
2. **Pydantic structured output em todas as personas** + validação cruzada com tool history
3. **RetryPolicy + recursion_limit + timeout por nó**
4. **Citation-grounded generation no Advogado** + hard-fail em RAG vazio
5. **Score quantificado + 3-vias do Juiz** (não binário)
6. **Prompts versionados por persona em arquivos separados**

---

# 🟦 BLOCO 3 — Vault de Jurisprudência (Memória RAG)

## Estrutura proposta (sua)
```text
bloco_vault/
├── motor_busca/
│   ├── retriever.py
│   └── gerador_embeddings.py
├── ingestao/
│   ├── pipeline_indexacao.py
│   └── classificador_metadados.py
└── database/
    └── (arquivos locais do ChromaDB)
```

## Análise pontual arquivo-por-arquivo

### `motor_busca/retriever.py` — Busca híbrida filtrada

**Fragilidades identificadas:**
1. **"Busca Híbrida Filtrada" sem detalhe**: BM25 + dense? Como combina scores (RRF, weighted average)?
2. **Filtro `WHERE court_id IN [...] AND binding == True` é INSUFICIENTE**: e se eu quiser "Súmula vinculante 121" especificamente? Filtro por `numero_sumula`?
3. **Sem caching de queries frequentes**: mesma query "anatocismo Tabela Price MG" será re-embedded a cada chamada do Advogado.
4. **Sem fallback se filtro retornar 0 docs**: deveria relaxar (remover binding=True) ou aborta?

**Pesquisa:**
- Reciprocal Rank Fusion (RRF) é o padrão para combinar BM25 + dense scores ([Lettria](https://www.lettria.com/blogpost/5-rag-chunking-strategies-for-better-retrieval-augmented-generation)).
- Cardinalidade STJ: ~1500 súmulas + ~1300 temas repetitivos (números aproximados de 2026) → filtro por `numero` é viável.
- Cache de embeddings via Redis com TTL — economia de 90%+ em queries repetidas.

**Patch concreto:**
```python
# retriever.py
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue
import hashlib
import diskcache

cache_query = diskcache.Cache("./bloco_vault/cache_queries")

def busca_hibrida(
    query: str,
    uf: str,
    apenas_vinculantes: bool = True,
    relax_se_vazio: bool = True,
    top_k: int = 20
) -> list[JurisprudenciaItem]:
    cache_key = hashlib.sha256(f"{query}|{uf}|{apenas_vinculantes}".encode()).hexdigest()
    if cache_key in cache_query:
        return cache_query[cache_key]

    cortes_validas = ["STJ", "STF", f"TJ{uf}"]

    filtros = [FieldCondition(key="court_id", match=MatchAny(any=cortes_validas))]
    if apenas_vinculantes:
        filtros.append(FieldCondition(key="binding", match=MatchValue(value=True)))

    # Dense
    embedding_query = legal_bertimbau.encode(query)
    resultados_dense = qdrant.query_points(
        collection_name="jurisprudencia",
        query=embedding_query,
        query_filter=Filter(must=filtros),
        limit=top_k
    )

    # Sparse (BM25 via Qdrant named vectors v1.9+)
    resultados_sparse = qdrant.query_points(
        collection_name="jurisprudencia",
        query=bm25_encode(query),
        using="sparse_vector",
        query_filter=Filter(must=filtros),
        limit=top_k
    )

    # RRF fusion
    fundidos = reciprocal_rank_fusion([resultados_dense, resultados_sparse], k=60)

    # Fallback: se zero, relaxar binding
    if len(fundidos) == 0 and relax_se_vazio and apenas_vinculantes:
        return busca_hibrida(query, uf, apenas_vinculantes=False, relax_se_vazio=False, top_k=top_k)

    cache_query.set(cache_key, fundidos, expire=24*3600)
    return fundidos
```

**Veredicto:** Busca híbrida sem **RRF + fallback + cache** vai degradar latência e qualidade.

---

### `motor_busca/gerador_embeddings.py` — Embeddings

**Fragilidades identificadas:**
1. **HuggingFace Sentence-Transformers genérico**: já discutido — Legal-BERTimbau é superior.
2. **Sem batching configurável**: indexar 10k docs um-por-um leva horas.
3. **Sem versionamento do modelo**: trocar embedder no meio do projeto invalida vault inteiro.

**Patch concreto:**
```python
# gerador_embeddings.py
from sentence_transformers import SentenceTransformer
from typing import Iterable

EMBEDDING_MODEL_VERSION = "rufimelo/Legal-BERTimbau-sts-large@v1.0"

class GeradorEmbeddings:
    def __init__(self):
        self.model = SentenceTransformer("rufimelo/Legal-BERTimbau-sts-large")
        self.versao = EMBEDDING_MODEL_VERSION

    def encode_batch(self, textos: Iterable[str], batch_size: int = 32) -> list[list[float]]:
        return self.model.encode(
            list(textos),
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True   # cosine distance fica eficiente
        ).tolist()

    def get_versao(self) -> str:
        # Vault DEVE ter metadado embedding_version — re-indexar quando trocar
        return self.versao
```

---

### `ingestao/pipeline_indexacao.py` — Pipeline de ingestão

**Fragilidades identificadas:**
1. **Sem chunking strategy explícita**: documento jurídico de 50 páginas vai entrar como 1 chunk? bobagem. Como é a estratégia?
2. **Sem deduplication**: mesma súmula indexada 3x (de fontes diferentes) infla vault.
3. **Sem incremental update**: indexação é full-rebuild ou append? como atualizar quando STJ publica novo tema?

**Pesquisa:**
- Para legal: **Recursive Text Splitter com regex de cabeçalhos** ("Art. X", "§ Y", "Súmula Z") → preserva estrutura ([Lettria](https://www.lettria.com/blogpost/5-rag-chunking-strategies-for-better-retrieval-augmented-generation), [Procycons](https://procycons.com/en/blogs/pdf-data-extraction-benchmark/)).
- **Summary-based context enrichment**: prepend resumo de 1 parágrafo do doc inteiro a cada chunk — combate "cross-document confusion" típica de corpora jurídicos ([arXiv 2510.06999](https://arxiv.org/html/2510.06999v1)).
- Deduplication: hash do texto canonicalizado (strip whitespace, normalize unicode).

**Patch concreto:**
```python
# pipeline_indexacao.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
import hashlib
import unicodedata

LEGAL_SEPARATORS = [
    "\n\nArt. ",         # artigo
    "\n\n§ ",            # parágrafo
    "\n\nINCISO ",
    "\n\nSúmula ",
    "\n\nTEMA ",
    "\n\n",              # parágrafo branco
    "\n",
    ". ",
    " "
]

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
    separators=LEGAL_SEPARATORS,
    length_function=len
)

def texto_canonico(s: str) -> str:
    return unicodedata.normalize("NFKC", s).strip().lower()

def hash_doc(s: str) -> str:
    return hashlib.sha256(texto_canonico(s).encode()).hexdigest()

def indexar_doc(doc: dict) -> int:
    h = hash_doc(doc["texto"])
    if qdrant.exists(filter={"hash_doc": h}):
        return 0  # dedup

    # Resumo do doc inteiro (1 parágrafo)
    resumo = gerar_resumo_doc(doc["texto"])  # via LLM ou extractive

    chunks = splitter.split_text(doc["texto"])
    points = []
    for i, chunk in enumerate(chunks):
        chunk_enriquecido = f"[Resumo do doc: {resumo}]\n\n{chunk}"   # ← context enrichment
        points.append({
            "id": f"{doc['id']}_{i}",
            "vector": embedder.encode(chunk_enriquecido),
            "sparse_vector": bm25.encode(chunk_enriquecido),
            "payload": {
                "doc_id": doc["id"],
                "court_id": doc["court_id"],
                "binding": doc["binding"],
                "tipo": doc["tipo"],
                "numero": doc["numero"],
                "modalidade_relacionada": doc.get("modalidade", []),  # ["VEICULO", "IMOBILIARIO"]
                "ano_julgamento": doc["ano"],
                "hash_doc": h,
                "embedding_version": embedder.get_versao(),
                "indexed_at": datetime.now().isoformat()
            }
        })
    qdrant.upsert(collection_name="jurisprudencia", points=points)
    return len(points)
```

**Veredicto:** Sem **chunking jurídico-aware + summary enrichment + dedup + versioning**, vault degrada e retorna lixo.

---

### `ingestao/classificador_metadados.py` — Esquema de metadados

**Fragilidades identificadas:**
1. **Schema proposto incompleto**: `court_id`, `binding`, `legal_topic` não cobre o que é necessário para filtros jurídicos reais.
2. **`legal_topic` é genérico**: "anatocismo" vs "abusividade de juros" vs "capitalização" — categorias não definidas.
3. **Sem ano de julgamento**: jurisprudência de 1995 vs 2024 tem peso diferente.
4. **Sem `modalidade_relacionada`**: súmula sobre "veículos" sendo retornada para contrato imobiliário = erro.

**Patch concreto — Schema enriquecido:**
```yaml
# Schema obrigatório por documento
id: "stj-tema-247"                    # único
court_id: "STJ"                       # ENUM: STF | STJ | TJ{UF}
tipo: "TEMA_REPETITIVO"               # ENUM: SUMULA_VINCULANTE | TEMA_REPETITIVO | SUMULA | ACORDAO | RECURSO_REPETITIVO
numero: "247"
ano_julgamento: 2018
binding: true
peso_vinculacao: 4                    # 1-5: TJ < STJ-acórdão < STJ-súmula < STJ-repetitivo < STF-vinculante
legal_topic_principal: "ANATOCISMO"   # ENUM controlado
legal_topics_secundarios: ["CAPITALIZACAO_JUROS", "TABELA_PRICE"]
modalidade_relacionada: ["VEICULO", "IMOBILIARIO"]   # cross-cutting
relator: "Min. Luis Felipe Salomão"
data_publicacao: "2018-04-15"
fonte_url: "https://www.stj.jus.br/..."
ementa: "..."
texto_completo: "..."
hash_doc: "sha256:abc..."
embedding_version: "rufimelo/Legal-BERTimbau-sts-large@v1.0"
indexed_at: "2026-04-30T10:00:00"
```

**Cardinalidade esperada para filtros (ajuda Qdrant otimizar):**

| Campo | Cardinalidade | Indexar como |
|-------|--------------|-------------|
| `court_id` | ~30 (27 TJ + STJ + STF + TST) | keyword |
| `tipo` | 5 | keyword |
| `binding` | 2 | bool |
| `legal_topic_principal` | ~50 (taxonomia controlada) | keyword |
| `modalidade_relacionada` | ~10 | keyword (array) |
| `ano_julgamento` | ~30 anos | integer (range index) |
| `peso_vinculacao` | 5 | integer |

**Veredicto:** Schema atual é placeholder. **Taxonomia controlada de legal_topic + modalidade_relacionada + peso_vinculacao + ano** são essenciais para retrieval correto.

---

## 🟦 Veredicto Bloco 3

**Solidez atual:** 🔴 Baixa — conceito de "filtro estrito por jurisdição" está certo, mas implementação proposta é frágil em chunking, dedup, schema, fallback, cache.

**Patches críticos (em ordem de impacto):**
1. **Schema enriquecido** com `legal_topic_principal` (taxonomia controlada), `modalidade_relacionada`, `ano`, `peso_vinculacao`
2. **Recursive splitter com separadores jurídicos** (Art./§/Súmula)
3. **Summary-based context enrichment** (combate cross-document confusion)
4. **Deduplication via hash canônico**
5. **RRF para busca híbrida** + cache de queries
6. **Fallback "relaxar binding"** se filtro retorna 0 docs

---

# 🟦 BLOCO 4 — Engine de Parsing e Ferramentas Matemáticas

## Estrutura proposta (sua)
```text
bloco_engine/
├── extratores/
│   ├── pdf_parser_marker.py
│   └── limpador_tabelas.py
├── ferramentas_calculo/
│   ├── calculadora_bacen_sgs.py
│   ├── motor_tabela_price.py
│   └── analisador_anatocismo.py
└── integracao/
    └── definicao_tools_langchain.py
```

## Análise pontual arquivo-por-arquivo

### `extratores/pdf_parser_marker.py` — Parsing PDF

**Fragilidades identificadas:**
1. **Hardcoded em Marker**: e se o PDF for escaneado e Marker OCR não pegar? E se for nativo com tabela Price (onde Docling é melhor)?
2. **Sem fallback**: parser falhou → exceção → workflow morre. Deveria tentar fallback (PyMuPDF4LLM se Marker travar).
3. **Sem validação do output**: como saber se o Markdown gerado é fiel ao PDF? metric de qualidade?

**Pesquisa:**
- Já coberto no doc anterior: estratégia híbrida Docling/Marker/PyMuPDF4LLM por heurística.
- Validação fiel: comparar # de páginas, # de tabelas detectadas, % de texto extraído vs OCR sample.

**Patch concreto:**
```python
# pdf_parser.py (renomear de pdf_parser_marker.py)
from enum import Enum
from pydantic import BaseModel

class TipoPDF(str, Enum):
    NATIVO_COM_TABELA_PRICE = "nativo_price"
    NATIVO_TEXTO_PURO = "nativo_texto"
    ESCANEADO = "escaneado"

class ResultadoParse(BaseModel):
    markdown: str
    tipo_detectado: TipoPDF
    parser_usado: str
    qualidade_score: float          # 0-1 — heurística
    tabelas_detectadas: int
    paginas: int

def detectar_tipo_pdf(pdf_path: Path) -> TipoPDF:
    # heurísticas:
    # - PDF nativo se tem texto extraível (PyMuPDF.get_text())
    # - tabela Price se contém >5 linhas com R$ + % juntos
    # - escaneado se images > text e texto < 100 chars
    ...

def parsear_pdf(pdf_path: Path) -> ResultadoParse:
    tipo = detectar_tipo_pdf(pdf_path)

    parsers_em_ordem = {
        TipoPDF.NATIVO_COM_TABELA_PRICE: [docling_parse, marker_parse, pymupdf_parse],
        TipoPDF.NATIVO_TEXTO_PURO: [pymupdf4llm_parse, marker_parse],
        TipoPDF.ESCANEADO: [marker_parse, docling_parse]
    }

    erros = []
    for parser in parsers_em_ordem[tipo]:
        try:
            md = parser(pdf_path)
            qualidade = avaliar_qualidade_parse(md, pdf_path)
            if qualidade > 0.7:
                return ResultadoParse(markdown=md, tipo_detectado=tipo, parser_usado=parser.__name__, qualidade_score=qualidade, ...)
        except Exception as e:
            erros.append((parser.__name__, str(e)))

    raise PDFParseFailedError(f"Todos os parsers falharam: {erros}")
```

**Veredicto:** Hardcoded + sem fallback + sem qualidade = parser frágil que vai derrubar produção.

---

### `extratores/limpador_tabelas.py` — Limpeza de tabelas

**Fragilidades identificadas:**
1. **Não está claro o que "limpa"**: se Docling/Marker já extraem tabela Markdown, o que esse módulo faz?
2. **Tabelas Price podem ter quebras visuais**: linhas de borda em PDFs viram lixo no Markdown.

**Patch concreto:**
```python
# limpador_tabelas.py
import pandas as pd
from io import StringIO

def markdown_table_to_df(md_table: str) -> pd.DataFrame:
    # Converte tabela markdown para DataFrame
    return pd.read_csv(StringIO(md_table.replace("|", ",")))

def limpar_tabela_amortizacao(df: pd.DataFrame) -> pd.DataFrame:
    # Heurísticas:
    # 1. Detectar colunas: "Parcela", "Saldo Devedor", "Juros", "Amortização", "Valor da Parcela"
    # 2. Converter R$ "1.234,56" → Decimal("1234.56")
    # 3. Validar: saldo[n] - amortizacao[n] = saldo[n+1] (auto-checa integridade)
    # 4. Detectar linhas de quebra/borda e remover
    ...

def validar_integridade_amortizacao(df: pd.DataFrame) -> bool:
    # Cross-check: para cada linha, juros + amortização == valor parcela?
    for _, row in df.iterrows():
        if abs((row["Juros"] + row["Amortização"]) - row["Valor Parcela"]) > Decimal("0.01"):
            return False
    return True
```

**Veredicto:** Limpador SEM **validação de integridade aritmética** da tabela é inútil — é exatamente onde Marker/Docling falham (split de cells).

---

### `ferramentas_calculo/calculadora_bacen_sgs.py` — BACEN

**Fragilidades identificadas:**
1. **Já coberto:** sem cache, sem retry. Patch já no doc anterior.
2. **Adicional:** sem mapping `modalidade_contrato → codigo_bacen`. Como o Perito decide qual código BACEN buscar?

**Patch concreto:**
```python
# codigos_bacen.yaml — taxonomia projeto
modalidades:
  VEICULO:
    codigo_sgs: 25471
    descricao: "Taxa média mensal de juros - PF - Aquisição de veículos"
    periodicidade: mensal
  VEICULO_LIVRES:
    codigo_sgs: 20749
    descricao: "Taxa média - PF - Veículos (recursos livres)"
  CDC_NAO_CONSIGNADO:
    codigo_sgs: 20748   # [verificar]
    descricao: "Taxa média - PF - Crédito pessoal não consignado"
  CARTAO_ROTATIVO:
    codigo_sgs: 20741   # [verificar]
    descricao: "Taxa média - PF - Cartão de crédito rotativo"
  IMOBILIARIO:
    codigo_sgs: null    # [verificar — múltiplos códigos]
    descricao: "Taxa - PF - Financiamento imobiliário"

selic:
  diaria: 11
  mensal: 4189

ipca: 433

# calculadora_bacen_sgs.py
import yaml
codigos = yaml.safe_load(open("codigos_bacen.yaml"))

def get_taxa_modalidade(modalidade: str, data: date) -> Decimal:
    if modalidade not in codigos["modalidades"]:
        raise ModalidadeDesconhecidaError(modalidade)
    codigo = codigos["modalidades"][modalidade]["codigo_sgs"]
    if codigo is None:
        raise ModalidadeSemCodigoBacenError(modalidade)

    return get_taxa_bacen(codigo, data)  # com cache + retry
```

**Veredicto:** Faltava **mapping declarativo modalidade → código BACEN**. Sem isso, Perito chuta código.

---

### `ferramentas_calculo/motor_tabela_price.py` — Cálculo Price

**Fragilidades identificadas:**
1. **CRÍTICO: usar `numpy_financial.pmt` direto**: retorna **float** ([numpy-financial docs](https://numpy.org/numpy-financial/latest/pmt.html)). Float perde precisão em loops longos (360 parcelas imobiliário). Para uso JURÍDICO, isso é inaceitável — diferença de centavos pode invalidar perícia.
2. **Sem suporte a juros simples**: STJ exige perícia para diferenciar juros simples vs compostos em Tabela Price. Motor só suporta compostos? Anatocismo nunca será detectado.
3. **Sem amortização constante (SAC) como alternativa**: para imobiliário, SAC é comum.

**Pesquisa:**
- Decimal Python: precisão arbitrária, mas mais lento. Para 360 parcelas, latência é OK (< 100ms).
- Anatocismo: STF Súmula 121 proíbe em casos não-SFN; STJ Súmula 539 permite no SFN com pactuação ([Migalhas](https://www.migalhas.com.br/depeso/317971/sumula-121-do-stf-e-anatocismo-na-tabela-price)).
- Discussão acadêmica: "Tabela Price é juros compostos" — tese clássica de revisão.

**Patch concreto:**
```python
# motor_tabela_price.py
from decimal import Decimal, getcontext
from typing import Literal
from langchain_core.tools import tool

getcontext().prec = 28   # precisão extra para finanças

@tool
def calcular_parcela_price(
    capital: Decimal,
    taxa_aa: Decimal,        # ex: Decimal("0.245") para 24.5% a.a.
    n_parcelas: int,
    regime: Literal["JUROS_COMPOSTOS", "JUROS_SIMPLES"] = "JUROS_COMPOSTOS"
) -> dict:
    """
    Calcula valor da parcela pela Tabela Price (capital, taxa a.a., n parcelas).

    REGIME:
    - JUROS_COMPOSTOS: fórmula clássica Price (anatocismo se não-SFN)
    - JUROS_SIMPLES: para comparação revisional
    """
    taxa_am = (1 + taxa_aa) ** (Decimal("1")/Decimal("12")) - 1   # taxa equivalente mensal

    if regime == "JUROS_COMPOSTOS":
        # PMT = PV * (i * (1+i)^n) / ((1+i)^n - 1)
        fator = (1 + taxa_am) ** n_parcelas
        pmt = capital * (taxa_am * fator) / (fator - 1)
    else:
        # JUROS SIMPLES (linear)
        juros_total = capital * taxa_am * n_parcelas
        pmt = (capital + juros_total) / n_parcelas

    return {
        "pmt": str(pmt.quantize(Decimal("0.01"))),
        "regime_aplicado": regime,
        "taxa_am_efetiva": str(taxa_am.quantize(Decimal("0.000001"))),
        "total_pago": str((pmt * n_parcelas).quantize(Decimal("0.01"))),
        "juros_totais": str((pmt * n_parcelas - capital).quantize(Decimal("0.01")))
    }

@tool
def gerar_tabela_amortizacao(capital: Decimal, taxa_aa: Decimal, n_parcelas: int, regime: str) -> list[dict]:
    """Retorna linha-a-linha da amortização para comparar com tabela do contrato."""
    saldo = capital
    pmt_dict = calcular_parcela_price(capital, taxa_aa, n_parcelas, regime)
    pmt = Decimal(pmt_dict["pmt"])
    taxa_am = Decimal(pmt_dict["taxa_am_efetiva"])

    tabela = []
    for i in range(1, n_parcelas + 1):
        juros = saldo * taxa_am
        amortizacao = pmt - juros
        saldo -= amortizacao
        tabela.append({
            "parcela": i,
            "saldo_devedor_inicial": str(saldo + amortizacao),
            "juros": str(juros.quantize(Decimal("0.01"))),
            "amortizacao": str(amortizacao.quantize(Decimal("0.01"))),
            "valor_parcela": str(pmt.quantize(Decimal("0.01"))),
            "saldo_devedor_final": str(saldo.quantize(Decimal("0.01")))
        })
    return tabela
```

**Veredicto:** Float em finanças jurídicas = vulnerabilidade legal. **Decimal + suporte a regime juros simples/compostos** é obrigatório para o produto ter validade pericial.

---

### `ferramentas_calculo/analisador_anatocismo.py` — Análise anatocismo

**Fragilidades identificadas:**
1. **Definição não clara**: anatocismo = "juros sobre juros". Como o módulo DETECTA matematicamente?
2. **Sem critério jurisprudencial**: STJ Súmula 539 permite no SFN com pactuação. O módulo verifica isso?
3. **Sem comparação Price vs Simples**: detecção clássica de anatocismo é ver se PMT pelo Price é maior que PMT pelo Simples.

**Pesquisa:**
- Definição operacional anatocismo: "incorporação de juros vencidos ao capital para nova incidência de juros".
- Em Price, a parcela inicial é majoritariamente juros — quando o saldo amortiza pouco e juros incidem sobre saldo "engordado" pelos juros não pagos.
- Detecção numérica: comparar tabela Price vs SAC vs Simples; se Price tem juros totais > Simples por mesma taxa, há anatocismo matemático.

**Patch concreto:**
```python
# analisador_anatocismo.py
from langchain_core.tools import tool
from decimal import Decimal

@tool
def analisar_anatocismo(
    capital: Decimal,
    taxa_aa_contrato: Decimal,
    n_parcelas: int,
    pertence_sfn: bool,
    pactuacao_capitalizacao_explicita: bool
) -> dict:
    """
    Detecta anatocismo matemático e classifica licitude jurídica.

    REFERÊNCIAS:
    - STF Súmula 121: proíbe capitalização de juros (não-SFN)
    - STJ Súmula 539: permite capitalização infra-anual em SFN com pactuação expressa
    - STJ Tema 247: Tabela Price não enseja anatocismo POR SI SÓ
    """
    # 1. Detecção matemática
    pmt_price = calcular_parcela_price(capital, taxa_aa_contrato, n_parcelas, "JUROS_COMPOSTOS")
    pmt_simples = calcular_parcela_price(capital, taxa_aa_contrato, n_parcelas, "JUROS_SIMPLES")

    diferenca_juros = Decimal(pmt_price["juros_totais"]) - Decimal(pmt_simples["juros_totais"])
    anatocismo_matematico = diferenca_juros > Decimal("0.01")

    # 2. Classificação jurídica
    if not anatocismo_matematico:
        verdicto = "SEM_ANATOCISMO"
        razao = "Diferença Price vs Simples desprezível"
    elif pertence_sfn and pactuacao_capitalizacao_explicita:
        verdicto = "ANATOCISMO_LICITO"
        razao = "STJ Súmula 539 — SFN com pactuação expressa permite capitalização"
    elif pertence_sfn and not pactuacao_capitalizacao_explicita:
        verdicto = "ANATOCISMO_QUESTIONAVEL"
        razao = "STJ Súmula 539 exige pactuação expressa — verificar contrato"
    else:
        verdicto = "ANATOCISMO_ILICITO"
        razao = "STF Súmula 121 — fora do SFN, capitalização proibida"

    return {
        "anatocismo_matematico_detectado": anatocismo_matematico,
        "diferenca_juros_brl": str(diferenca_juros.quantize(Decimal("0.01"))),
        "verdicto_juridico": verdicto,
        "razao": razao,
        "sumulas_aplicaveis": ["STF-Súmula-121", "STJ-Súmula-539", "STJ-Tema-247"]
    }
```

**Veredicto:** Análise jurídica QUANTITATIVA + jurisprudencial integrada. Esse módulo é coração do produto — não pode ser superficial.

---

### `integracao/definicao_tools_langchain.py` — Tools registry

**Fragilidades identificadas:**
1. **Sem schema explícito de tools**: cada @tool deveria ter docstring com input/output Pydantic.
2. **Sem testes unitários por tool**: como garantir que `calcular_parcela_price` continua certo após refactor?

**Patch:** padrão Pydantic + testes pytest.

---

## 🟦 Veredicto Bloco 4

**Solidez atual:** 🟡 Conceito sólido (BACEN como ferramenta + matemática determinística) MAS execução proposta tem 3 furos críticos: float em finanças, falta regime juros simples, anatocismo superficial.

**Patches críticos (em ordem de impacto):**
1. **Decimal em tudo** que toca dinheiro (não float)
2. **Suporte regime juros simples** vs compostos no motor Price
3. **Análise anatocismo integrando jurisprudência** (Súmulas 121/539, Tema 247)
4. **Mapping `modalidade → codigo_bacen`** declarativo
5. **Pipeline parsing com fallback** + validação de qualidade
6. **Validação aritmética de tabela** extraída (juros + amort = parcela)

---

# 🎯 Síntese — Nova Arquitetura "Sólida"

## Estrutura proposta enriquecida (recomendação Atlas)

```text
revisor_contratual/
├── bloco_contratos/                      # ← NOVO: Pydantic models compartilhados
│   ├── __init__.py
│   ├── contrato.py                       # ContratoExtraido, MetadadosContrato, UF enum
│   ├── calculo.py                        # ResultadoCalculo, OutputPerito
│   ├── jurisprudencia.py                 # JurisprudenciaItem
│   ├── debate.py                         # TurnoDebate, DivergenciaJuiz
│   └── decisao.py                        # DecisaoHumana, OutputJuiz
│
├── bloco_interface/
│   ├── pages/
│   │   ├── 1_upload.py
│   │   ├── 2_processamento.py
│   │   └── 3_resultado.py
│   ├── api_client.py                     # ← cliente HTTP tipado p/ FastAPI
│   ├── session.py                        # gestão st.session_state
│   ├── componentes/
│   │   ├── uploader.py                   # com Pydantic + magic bytes
│   │   ├── visualizador_chat.py          # SSE-aware com tipos de evento
│   │   └── painel_intervencao.py         # payload tipado + justificativa
│   └── utils/
│       └── formatador_pdf.py             # Jinja2 + WeasyPrint + hash
│
├── bloco_api/                            # ← NOVO: FastAPI bridge
│   ├── main.py
│   ├── endpoints/
│   │   ├── upload.py                     # POST /processar
│   │   ├── stream.py                     # SSE GET /stream/{task_id}
│   │   └── decisao.py                    # POST /decisao/{task_id}
│   ├── workers/
│   │   └── dramatiq_actors.py
│   └── observability/
│       ├── tracing.py                    # OpenTelemetry
│       └── audit_log.py                  # structlog + arquivo append-only
│
├── bloco_agentes/
│   ├── orquestrador/
│   │   ├── grafo_estado.py               # TypedDict + Annotated reducers + Decimal-as-string
│   │   ├── definicao_nos_arestas.py      # RetryPolicy, recursion_limit, 3-vias condicional
│   │   └── checkpointer.py               # SqliteSaver config
│   ├── personas/
│   │   ├── _base.py                      # Persona base class
│   │   ├── agente_perito.py              # Pydantic structured output + tool history validation
│   │   ├── agente_economista.py          # ESCOPO CIRÚRGICO: análise macro contextual
│   │   ├── agente_advogado.py            # citation-grounded + RAG fallback
│   │   └── agente_juiz_revisor.py        # score quantificado + 3-vias
│   └── prompts/
│       ├── _base/
│       │   ├── regras_universais.md
│       │   └── persona_juridico_brasileiro.md
│       ├── perito/
│       │   ├── system_v1.md
│       │   ├── few_shot.json
│       │   └── tests.yaml                # promptfoo
│       ├── economista/...
│       ├── advogado/...
│       └── juiz/...
│
├── bloco_vault/
│   ├── motor_busca/
│   │   ├── retriever.py                  # RRF + cache + fallback
│   │   ├── gerador_embeddings.py         # Legal-BERTimbau-sts-large + versioning
│   │   └── reranker.py                   # ← NOVO: cross-encoder rerank
│   ├── ingestao/
│   │   ├── pipeline_indexacao.py         # legal splitter + summary enrichment + dedup
│   │   ├── classificador_metadados.py    # taxonomia controlada
│   │   ├── seed_jurisprudencia/          # ← NOVO: jurisprudência inicial seed
│   │   │   ├── stf_sumulas_vinculantes.json
│   │   │   ├── stj_temas_repetitivos.json
│   │   │   └── tj_mg_acordaos.json
│   │   └── refresh_scheduler.py          # ← NOVO: re-indexação mensal
│   ├── schemas/
│   │   ├── jurisprudencia_schema.yaml    # validação YAML
│   │   └── legal_topics_taxonomia.yaml   # taxonomia controlada
│   └── database/
│       └── qdrant_data/                  # binários Qdrant
│
├── bloco_engine/
│   ├── extratores/
│   │   ├── pdf_parser.py                 # router Docling/Marker/PyMuPDF4LLM
│   │   ├── limpador_tabelas.py           # validação aritmética
│   │   └── detector_tipo_pdf.py          # heurísticas
│   ├── ferramentas_calculo/
│   │   ├── calculadora_bacen_sgs.py      # cache + retry + mapping modalidade
│   │   ├── motor_tabela_price.py         # Decimal + juros simples/compostos + SAC
│   │   ├── analisador_anatocismo.py      # quantitativo + jurisprudencial
│   │   └── codigos_bacen.yaml            # mapping declarativo
│   ├── integracao/
│   │   └── definicao_tools_langchain.py  # tools registry com Pydantic schemas
│   └── tests/
│       ├── test_motor_price.py           # casos canônicos
│       ├── test_anatocismo.py
│       └── test_bacen_cache.py
│
├── bloco_observability/                  # ← NOVO
│   ├── tracing.py                        # OpenTelemetry exporter
│   ├── metrics.py                        # Prometheus
│   └── audit_log.py                      # decisões humanas append-only
│
├── tests/
│   ├── unit/                             # por módulo
│   ├── integration/                      # por bloco
│   ├── e2e/                              # workflow completo com PDFs sintéticos
│   └── fixtures/
│       ├── contratos_sinteticos/
│       └── jurisprudencia_seed/
│
├── docker-compose.yml                    # Streamlit + FastAPI + Qdrant + Redis + Ollama
├── pyproject.toml
└── README.md
```

## Princípio de Solidez aplicado — antes vs depois

| Critério | Sua proposta | Recomendação Atlas |
|----------|--------------|---------------------|
| **Único motivo para falhar** | Cada bloco tem 3-5 motivos | Cada módulo tem 1 motivo (testável) |
| **Falha rápido e barulhento** | Silent failures (LLM alucina, RAG retorna lixo) | Hard-fail tipado (`PeritoSemFontesError`, `RAGVazioError`) |
| **Testável em isolamento** | Tools acopladas, schemas implícitos | Pydantic models partilhados + tests/ por módulo |
| **Contratos explícitos** | Strings e dicts soltos | `bloco_contratos/` com Pydantic |
| **Estado observável em runtime** | Logs ad-hoc | OpenTelemetry + audit-log + LangGraph checkpointer |

---

## 📋 Checklist de Solidez para Implementação

### Por bloco — gates antes de avançar

**Bloco 1 (UI):**
- [ ] Toda input do usuário valida via Pydantic
- [ ] Streamlit não chama LangGraph diretamente — usa `api_client.py`
- [ ] Stream SSE com tipos de evento explícitos
- [ ] HITL com payload tipado + justificativa obrigatória
- [ ] Petição com hash sha256 + template versionado

**Bloco 2 (Agentes):**
- [ ] EstadoRevisor com `Annotated[..., add]` em todos os campos lista
- [ ] Decimal-as-string em todos os campos monetários
- [ ] Schema versioning + checkpointer compatível
- [ ] RetryPolicy + recursion_limit configurados
- [ ] Cada persona retorna Pydantic structured output
- [ ] Validação cruzada Perito vs tool history
- [ ] Citation-grounded no Advogado
- [ ] Score 3-vias no Juiz

**Bloco 3 (Vault):**
- [ ] Schema metadados com taxonomia controlada
- [ ] Recursive splitter com separadores jurídicos
- [ ] Summary-based context enrichment
- [ ] Deduplication via hash canônico
- [ ] RRF para hybrid search
- [ ] Cache de queries com TTL
- [ ] Fallback "relaxar binding" se RAG vazio
- [ ] Embedding version no payload

**Bloco 4 (Engine):**
- [ ] Decimal em todos os cálculos financeiros
- [ ] Suporte regime juros simples + compostos + SAC
- [ ] Análise anatocismo integrando Súmulas 121/539 + Tema 247
- [ ] Mapping `modalidade → codigo_bacen` declarativo
- [ ] BACEN com cache + retry + tenacity
- [ ] Pipeline parsing com fallback de 3 parsers
- [ ] Validação aritmética da tabela extraída
- [ ] Tests unitários por tool

**Cross-cutting:**
- [ ] `bloco_contratos/` Pydantic models compartilhados
- [ ] OpenTelemetry tracing
- [ ] Audit-log append-only para decisões humanas
- [ ] Docker compose com todos os serviços
- [ ] CI rodando tests por bloco antes de merge

---

## 🔗 Fontes Adicionais (deste estudo)

### Frontend / Streaming
- [agent-service-toolkit (JoshuaC215)](https://github.com/JoshuaC215/agent-service-toolkit)
- [Streaming AI Agent FastAPI LangGraph 2025-26 — Dev.to](https://dev.to/kasi_viswanath/streaming-ai-agent-with-fastapi-langgraph-2025-26-guide-1nkn)
- [Bridging LangGraph and Streamlit — Medium Yiğit Bekir Kaya](https://medium.com/@yigitbekir/bridging-langgraph-and-streamlit-a-practical-approach-to-streaming-graph-state-13db0999c80d)
- [Real-Time AI Apps LangGraph FastAPI Streamlit — Dharmendra Singh](https://medium.com/@dharamai2024/building-real-time-ai-apps-with-langgraph-fastapi-streamlit-streaming-llm-responses-like-04d252d4d763)
- [LangGraph Streaming Docs](https://docs.langchain.com/oss/python/langgraph/streaming)

### LangGraph State
- [Type Safety in LangGraph TypedDict vs Pydantic — Shaza Ali Substack](https://shazaali.substack.com/p/type-safety-in-langgraph-when-to)
- [LangGraph State Management — CallSphere](https://callsphere.ai/blog/langgraph-state-management-typeddict-reducers-state-channels)
- [LangGraph Best Practices — Swarnendu De](https://www.swarnendu.de/blog/langgraph-best-practices/)
- [LangGraph Use Graph API Docs](https://docs.langchain.com/oss/python/langgraph/use-graph-api)

### Legal RAG Chunking
- [Towards Reliable Retrieval RAG Legal Datasets — arXiv 2510.06999](https://arxiv.org/html/2510.06999v1)
- [5 RAG Chunking Strategies — Lettria](https://www.lettria.com/blogpost/5-rag-chunking-strategies-for-better-retrieval-augmented-generation)
- [Legal Chunking Evaluating Methods — ResearchGate](https://www.researchgate.net/publication/386472016_Legal_Chunking_Evaluating_Methods_for_Effective_Legal_Text_Retrieval)
- [Optimizing Legal Text Summarization Dynamic RAG — MDPI](https://www.mdpi.com/2073-8994/17/5/633)
- [Mastering Document Chunking Strategies RAG — Medium Sahin Ahmed](https://medium.com/@sahin.samia/mastering-document-chunking-strategies-for-retrieval-augmented-generation-rag-c9c16785efc7)

### Financial Calculations / Anatocismo
- [numpy_financial pmt docs](https://numpy.org/numpy-financial/latest/pmt.html)
- [numpy_financial ipmt docs](https://numpy.org/numpy-financial/latest/ipmt.html)
- [STF Súmula 121 anatocismo Tabela Price — Migalhas](https://www.migalhas.com.br/depeso/317971/sumula-121-do-stf-e-anatocismo-na-tabela-price)
- [STJ Tabela Price não enseja anatocismo — Bocater](https://www.bocater.com.br/en_us/publicacoes/stj-entende-que-uso-da-tabela-price-nao-enseja-anatocismo-em-contrato-de-financiamento-imobiliario/)
- [Anatocismo no SFN — Código Alpha](https://codigoalpha.blog/anatocismo-conceito-e-proibicao-no-ordenamento-juridico/)
- [Tabela Price sem anatocismo para magistrados — Migalhas](https://www.migalhas.com.br/depeso/315562/tabela-price-sem-anatocismo-para-magistrados-e-advogados)
- [Jurisprudência STJ Capitalização Juros — AnyCalc](https://anycalc.com.br/blog/jurisprudencia-atualizada-do-stj-sobre-capitalizacao-de-juros-anatocismo/)

### Brazilian Legal Schema
- [STJ Temas Repetitivos 1º semestre 2025](https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2025/29072025-Tribunal-julgou-37-temas-repetitivos-no-primeiro-semestre-de-2025--confira-todas-as-teses.aspx)
- [STJ Temas Repetitivos 2º semestre 2025](https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2026/28012026-STJ-julgou-42-temas-repetitivos-no-segundo-semestre-de-2025--veja-as-teses-fixadas.aspx)
- [STF Súmulas Vinculantes — DireitoHD](https://www.direitohd.com/sumulasvinculantesstf)
- [STJ Recursos Repetitivos info](https://www.stj.jus.br/sites/portalp/Precedentes/informacoes-gerais/recursos-repetitivos)
- [STF Repercussão Geral Teses](https://portal.stf.jus.br/repercussaogeral/teses.asp)

---

## 📌 Handoff para próximas Skills

**Pronto para:**
- `LMAS:agents:architect` (Aria) — receber este deep-dive + spec original + research anterior, produzir SAD formal + ADRs por decisão crítica.
- `LMAS:agents:smith` — adversarial review desta nova estrutura proposta. Atacar vetores que Atlas pode ter perdido (especialmente segurança, compliance, edge cases jurídicos).

**Decisões pendentes para Eric:**
1. Adotar nova estrutura proposta (com `bloco_contratos/`, `bloco_api/`, `bloco_observability/`)?
2. Adotar Decimal everywhere ou aceitar float com warning?
3. Implementar todas as 5 personas ou eliminar Economista (escopo redundante)?
4. Vault de jurisprudência: começar com seed manual (STF + STJ + 1 TJ) ou pipeline de scraping desde já?

---

*Atlas, dissecando até onde a luz alcança — 🔎*
