---
type: adr
id: "ADR-001"
title: "Gerenciamento de estado: LangGraph + SqliteSaver com PRAGMA integrity_check + asyncio.gather paralelo"
status: accepted
date: "2026-05-01"
adr_level: spec
spec_coverage:
  - "Cobertura completa de métodos de write SqliteSaver (put + put_writes + aput + aput_writes)"
  - "threading.Lock + asyncio.Lock separados (sync vs async não compartilham primitivo)"
  - "WAL mode + PRAGMA integrity_check"
patched_at:
  - "2026-05-01 (PATCH 1 — F-CRIT-A SUB-C concurrency model)"
  - "2026-05-01 (PATCH 2 — F-MIN-03 _LockedSqliteSaver cobertura completa)"
patch_reason:
  - "PATCH 1: Concurrency model — asyncio.gather paralelo para Advogado+Economista (F-CRIT-A SUB-C ADR-003) + threading.Lock para SqliteSaver (F-HIGH-A Smith)"
  - "PATCH 2: F-MIN-03 — _LockedSqliteSaver expandido para cobrir put_writes, aput, aput_writes (Smith mini-tribunal etapa 2.2 + decisão Eric RITMO 2)"
domain: "estado-workflow"
decision_makers: ["@architect (Aria)", "@lmas-master (Morpheus consolidação)", "Eric (RITMO 2)"]
supersedes: null
superseded_by: null
absorves:
  - "R-NEW-SMITH-10 (PRAGMA integrity_check no SqliteSaver)"
  - "F-HIGH-A-2.1 (Smith — SqliteSaver lock contention) via threading.Lock"
  - "F-MIN-03-2.2 (Smith — _LockedSqliteSaver cobertura incompleta) via expansão para todos métodos de write"
related_to:
  - "FR-RECOVERY-01 (recovery mid-workflow)"
  - "FR-AUDIT-01 (audit log integrity)"
  - "ADR-003 PATCH SUB-C + PATCH 2 (fan-out paralelo Advogado + Economista; 2 servers Ollama)"
  - ".claude/rules/adr-scope.md (rule de framework — explica adr_level: spec)"
project: revisor-contratual
sprint: "01"
etapa: "2.0 (criada) → 2.2 (PATCH SUB-C concurrency) → 2.3 (PATCH-do-PATCH RITMO 2)"
tags:
  - project/revisor-contratual
  - adr
  - estado-workflow
  - langgraph
  - sqlite-saver
  - patched
  - spec
---

# ADR-001 — Gerenciamento de estado: LangGraph + SqliteSaver com PRAGMA integrity_check

```
[@architect · Aria (Visionary)] — etapa 2.0 · ADR-001 gerenciamento de estado
SPRINT: 01 · ETAPA: 2.0 · DOMÍNIO: SoftwareDev/legaltech
```

## Contexto

O Revisor Contratual orquestra um pipeline determinístico de 9 etapas (parser → BACEN → RAG → Advogado → Economista → Juiz → validação semântica → renderer → audit). O PRD v1.0.2 especifica que crashes mid-workflow devem permitir continuação sem refazer etapas concluídas (FR-RECOVERY-01).

A arquitetura D-LEAN (single-process Python, asyncio interno) precisa de um mecanismo de checkpointing leve, sem dependências distribuídas, capaz de:
1. Persistir estado entre etapas
2. Permitir recuperação após crash (mesmo upload reentra com hash sha256 igual)
3. Não bloquear o thread principal do Streamlit
4. Integrar-se naturalmente com structured output Pydantic

Smith levantou na re-review (R-NEW-SMITH-10): SQLite WAL pode deixar `state.db` em estado inconsistente após crash mid-write — checkpointer pode retornar estado corrupto silenciosamente.

## Decisão

**Adotamos LangGraph como state machine + SqliteSaver checkpointer + PRAGMA integrity_check obrigatório antes de oferecer recovery.**

### Detalhes técnicos

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict
import sqlite3

class WorkflowState(TypedDict):
    contract_hash: str
    parsed_contract: ParsedContract | None
    bacen_data: BacenData | None
    jurisprudencia: list[JurisprudenciaItem] | None
    tese: TeseAdvogado | None
    analise_macro: AnaliseMacroEconomica | None
    veredicto_juiz: VeredictoJuiz | None
    validacao_semantica: list[ValidacaoSemantica] | None

# Checkpointer com integrity_check + locks para writes
# PATCH 1 (F-HIGH-A): threading.Lock + WAL mode
# PATCH 2 (F-MIN-03): asyncio.Lock adicional para métodos async
import threading
import asyncio

_SQLITE_SYNC_LOCK = threading.Lock()  # PATCH F-HIGH-A: serializa writes sync
_SQLITE_ASYNC_LOCK = asyncio.Lock()   # PATCH F-MIN-03: serializa writes async (não usar threading.Lock em async)

def get_checkpointer(db_path: str = "bloco_workflow/state.db") -> "_LockedSqliteSaver":
    conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
    # ABSORVE R-NEW-SMITH-10: integrity_check antes de uso
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check")
    result = cursor.fetchone()[0]
    if result != "ok":
        raise RuntimeError(f"state.db corrompido: {result}. Backup necessário antes de recovery.")
    # Habilita WAL para concurrent reads + serialized writes
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")  # WAL safe + faster than FULL
    return _LockedSqliteSaver(conn, _SQLITE_SYNC_LOCK, _SQLITE_ASYNC_LOCK)

class _LockedSqliteSaver(SqliteSaver):
    """PATCH F-HIGH-A + F-MIN-03 (PATCH 2 RITMO 2):
    Cobertura COMPLETA de métodos de write SqliteSaver.

    LangGraph >=0.2 chama múltiplos métodos de write em paralelo via
    asyncio.gather (ADR-003 SUB-C fan-out). Lock apenas em put() era
    insuficiente — race latente em put_writes/aput/aput_writes.

    threading.Lock para sync (put, put_writes); asyncio.Lock para async
    (aput, aput_writes) — primitivos NÃO compartilham (threading.Lock
    bloqueia event loop)."""

    def __init__(self, conn, sync_lock: threading.Lock, async_lock: asyncio.Lock):
        super().__init__(conn)
        self._sync_lock = sync_lock
        self._async_lock = async_lock

    # SYNC writes
    def put(self, *args, **kwargs):
        with self._sync_lock:
            return super().put(*args, **kwargs)

    def put_writes(self, *args, **kwargs):
        with self._sync_lock:
            return super().put_writes(*args, **kwargs)

    # ASYNC writes — asyncio.Lock obrigatório (threading.Lock bloqueia event loop)
    async def aput(self, *args, **kwargs):
        async with self._async_lock:
            return await super().aput(*args, **kwargs)

    async def aput_writes(self, *args, **kwargs):
        async with self._async_lock:
            return await super().aput_writes(*args, **kwargs)

workflow = StateGraph(WorkflowState)
workflow.add_node("parser", parse_contract_node)
# Nodes paralelos (PATCH SUB-C — fan-out Advogado + Economista)
workflow.add_node("tese_e_macro_paralelo", tese_e_macro_node)  # asyncio.gather interno
# ... demais nodes
workflow.set_entry_point("parser")
workflow.add_edge("parser", "bacen")
workflow.add_edge("bacen", "rag")
workflow.add_edge("rag", "tese_e_macro_paralelo")  # fan-out
workflow.add_edge("tese_e_macro_paralelo", "juiz")  # fan-in
# ... demais edges
graph = workflow.compile(checkpointer=get_checkpointer())
```

### Concurrency model (PATCH SUB-C)

A partir do PATCH ADR-003 SUB-C, Advogado (Sabia-7B) e Economista (Qwen 2.5 3B) executam **em paralelo** via `asyncio.gather` usando 2 instâncias Ollama distintas. Implicações no state machine:

```python
# bloco_workflow/nodes/tese_e_macro.py
async def tese_e_macro_node(state: WorkflowState) -> dict:
    """Fan-out paralelo Advogado + Economista (PATCH SUB-C)."""
    from .personas.orchestrator import gerar_tese_e_analise_paralelo

    tese, analise = await gerar_tese_e_analise_paralelo(
        calculo=state["parsed_contract"].calculo,
        docs=state["jurisprudencia"],
        contrato_meta=state["parsed_contract"].metadata,
        bacen_data=state["bacen_data"],
        tier=state.get("llm_tier", "premium"),
    )

    # SqliteSaver write — protegido por _SQLITE_WRITE_LOCK
    return {"tese": tese, "analise_macro": analise}
```

**Latência:** max(advogado, economista) ≈ 90s (vs. soma serial 150-180s).
**Footprint:** Sabia-7B 5GB + Qwen 3B 2GB = ~7GB (cabe em NFR-PERF-02 ≤8GB).

### Recovery flow

1. Usuário faz upload de contrato → calcular `sha256(pdf_bytes)`
2. Consultar SqliteSaver: existe checkpoint com `thread_id = sha256`?
3. Se SIM:
   - Executar PRAGMA integrity_check no `state.db`
   - Se OK: oferecer "Continuar de onde parou (etapa X)" + "Reiniciar do zero"
   - Se NÃO OK: descartar checkpoint, alertar usuário, oferecer apenas "Reiniciar do zero"
4. Se NÃO: pipeline novo

### Threading com Streamlit

LangGraph roda **dentro** do Streamlit (single-process). Etapas LLM (Advogado + Economista) são bloqueantes — Streamlit usa `st.spinner` + `@st.fragment` (Streamlit ≥1.40) para evitar congelar UI durante 60-90s por LLM call.

## Razão

- **LangGraph é a escolha pragmática:** state machine declarativa + checkpointer plugável + serialização Pydantic nativa. Já listado em `.project.yaml` como stack aprovada.
- **SqliteSaver é coerente com LEAN:** nenhuma dependência externa (Redis, PostgreSQL); arquivo local; suporta concurrent reads + serialized writes (WAL mode).
- **PRAGMA integrity_check é barato (<100ms para state.db de ≤10MB):** custo desprezível comparado ao risco de recovery silenciosamente errado.
- **`threading.Lock` para writes sync (PATCH F-HIGH-A):** com `check_same_thread=False` + `asyncio.gather` paralelo (PATCH SUB-C), múltiplas coroutines podem escrever no SqliteSaver. Lock serializa writes sync, mantendo atomicidade SQLite.
- **`asyncio.Lock` para writes async (PATCH 2 F-MIN-03):** Smith mini-tribunal etapa 2.2 expôs que LangGraph >=0.2 chama `aput`/`aput_writes` em paralelo via asyncio.gather. `threading.Lock` BLOQUEARIA o event loop nessas chamadas → deadlock. Locks separados (sync vs async) é obrigatório.
- **Cobertura completa de métodos de write (PATCH 2 F-MIN-03):** wrapper original cobria apenas `put()`. Versão expandida cobre `put`, `put_writes`, `aput`, `aput_writes` — toda a superfície de escrita do SqliteSaver.
- **WAL mode + synchronous=NORMAL:** balance entre durability e performance — concurrent reads funcionam sem bloquear writers.
- **asyncio.gather para fan-out (PATCH SUB-C):** Advogado + Economista usam 2 instâncias Ollama distintas em portas separadas (PATCH 2 ADR-003 — base_url explícito), não há contenção no provider LLM.

## Alternativas Consideradas

### Alt 1 — Asyncio + dict puro (sem LangGraph)
- **Prós:** zero dependências; código mais simples
- **Contras:** sem persistência nativa; recovery exigiria implementação manual de serialização Pydantic + roteamento de retomada; reinventa a roda
- **Rejeitada:** custo de implementação não compensa o ganho de simplicidade; LangGraph já oferece recovery built-in

### Alt 2 — Celery + Redis broker
- **Prós:** task queue robusta; retry automático
- **Contras:** viola arquitetura D-LEAN (introduce Redis como dependência); orquestração distribuída excessiva para single-user
- **Rejeitada:** Eric explicitamente sinalizou "Essa estrutura está muito pesada — 16RAM é extremamente alta" antes da refatoração D-LEAN

### Alt 3 — Prefect / Dagster
- **Prós:** workflow engines maduros
- **Contras:** dependência pesada (servidor próprio); overhead enorme para pipeline single-user
- **Rejeitada:** mesma razão da Alt 2

## Consequências

### Positivas
- Recovery mid-workflow funciona out-of-the-box (FR-RECOVERY-01 ✅)
- Detecção de corrupção do state.db antes de propagar erro silencioso (R-NEW-SMITH-10 ✅)
- **Cobertura completa de race conditions (PATCH 2 F-MIN-03):** todos os 4 métodos de write do SqliteSaver protegidos; sync vs async com primitivos corretos
- **Sem deadlock async (PATCH 2):** asyncio.Lock dedicado para aput/aput_writes evita bloqueio do event loop que `threading.Lock` causaria
- Padrão de checkpointing reaproveitável quando ML estágio 2 entrar (Mês 6+)
- Streamlit + LangGraph é stack documentada com exemplos públicos

### Negativas / Tradeoffs
- LangGraph adiciona ~30MB ao footprint (aceitável dentro de NFR-PERF-02 ≤8GB)
- PRAGMA integrity_check adiciona ~50-100ms ao recovery (imperceptível ao usuário)
- Curva de aprendizado para devs não-familiarizados com state machines
- **2 locks em vez de 1 (PATCH 2):** complexidade pequena adicional; documentado claramente no snippet de `_LockedSqliteSaver`

### Neutras
- Substituir LangGraph por outra state machine no futuro requer refactor isolado em `bloco_workflow/` (NFR-MAINT-01 preservada)

## Referências

- PRD v1.0.2: FR-RECOVERY-01 (linhas 452-456)
- Smith re-review: R-NEW-SMITH-10 (qa/smith-adversarial-rereview-prd-v1.0.2.md)
- Smith mini-review etapa 2.2: F-HIGH-A + F-MIN-03 (qa/smith-adversarial-mini-review-patch-sub-c-etapa-2.2.md)
- LangGraph docs: https://langchain-ai.github.io/langgraph/
- LangGraph SqliteSaver source: https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-sqlite
- SQLite PRAGMA integrity_check: https://www.sqlite.org/pragma.html#pragma_integrity_check
- Python asyncio.Lock vs threading.Lock: https://docs.python.org/3/library/asyncio-sync.html#asyncio.Lock
- `.project.yaml` campo `bloco_workflow.stack`
- Rule de framework: `.claude/rules/adr-scope.md` (formaliza adr_level: spec)

---

*Aria, definindo a fundação que sobrevive ao crash. 🏗️*
