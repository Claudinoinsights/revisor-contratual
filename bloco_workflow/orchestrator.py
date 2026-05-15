"""Workflow orchestrator — inferência sequencial Advogado → Economista (ADR-023).

ADR-023 (D-ARIA-S06-018, 2026-05-15) refatorou paralelismo asyncio.gather original
(D-MOR-3.3-C) para sequential em resposta a F-PROD-NEW-18 (Smith D-SMITH-S06-015 +
Operator D-OPS-S06-017b):

  - VPS load average 151.32 durante inferência paralela qwen2.5:7b + qwen2.5:3b
  - Ollama internal process killed via `unexpected EOF (status -1)` por CPU saturation
  - Memory fix (3G→6G) resolveu OOM mas CPU bottleneck pivotou

ATOMICIDADE PRESERVADA: se Advogado raise, Economista nem inicia (mesmo comportamento
que asyncio.gather default — first exception propaga).

TRADE-OFF: latência ~2x maior (~30-60s vs ~15-30s paralelo) — aceitável para MVP
CDC Veículos PF. Reconsideration triggers Sprint 7+ documentados em ADR-023.

Mantém:
  - 2 instâncias Ollama em portas/hosts distintos (F-MIN-01 fix + D-DEV-S06-016 env vars)
  - asyncio.to_thread wrap em pipeline.py (não bloquear FastAPI event loop)
  - Backward-compat alias `run_personas_paralelas` (consumers existentes preservados)
"""

from __future__ import annotations

from bloco_contratos.contrato import (
    BacenData,
    ContratoMetadata,
    ResultadoCalculo,
)
from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_contratos.personas import AnaliseMacroEconomica, LLMTier, TeseAdvogado
from bloco_workflow.personas.advogado import (
    InvokeFn as InvokeFnAdvogado,
)
from bloco_workflow.personas.advogado import (
    advogado_redigir_tese_async,
)
from bloco_workflow.personas.economista import (
    InvokeFn as InvokeFnEconomista,
)
from bloco_workflow.personas.economista import (
    economista_analisar_async,
)


async def run_personas_sequencial(
    contrato_meta: ContratoMetadata,
    calculo: ResultadoCalculo,
    docs: list[JurisprudenciaItem],
    bacen_data: BacenData,
    *,
    tier_advogado: LLMTier = "premium",
    advogado_invoke_fn: InvokeFnAdvogado | None = None,
    economista_invoke_fn: InvokeFnEconomista | None = None,
) -> tuple[TeseAdvogado, AnaliseMacroEconomica]:
    """Executa Advogado primeiro, depois Economista — SEQUENCIAL (ADR-023).

    F-PROD-NEW-18 resolution: paralelismo asyncio.gather original (D-MOR-3.3-C)
    saturava CPU VPS (load 151) durante inferência simultânea qwen2.5:7b +
    qwen2.5:3b. Single LLM por vez reduz pressure ~50% e evita OOM-like kills.

    Args:
        contrato_meta: metadata do contrato (compartilhado)
        calculo: output Perito (consumido só pelo Advogado)
        docs: jurisprudência top-K (consumido só pelo Advogado)
        bacen_data: dados BACEN (consumido só pelo Economista)
        tier_advogado: lean/balanced/premium (FR-TESE-02)
        advogado_invoke_fn / economista_invoke_fn: injetáveis para testes

    Returns:
        (TeseAdvogado, AnaliseMacroEconomica)

    Raises:
        Propaga exceção do Advogado (se raise) ANTES de iniciar Economista.
        Comportamento de atomicidade equivalente ao asyncio.gather default.

    Trade-off (ADR-023):
        Latência ~2x maior (sequencial) vs paralelismo original. Aceitável para
        MVP CDC Veículos PF em VPS atual. Reconsiderar quando VPS escalada para
        ≥16 CPU cores OR migration LLM API externa (Sprint 7+).
    """
    # Step 5a: Advogado primeiro (qwen2.5:7b — modelo maior, mais lento)
    tese = await advogado_redigir_tese_async(
        calculo,
        docs,
        contrato_meta,
        tier_advogado,
        invoke_fn=advogado_invoke_fn,
    )

    # Step 5b: Economista depois (qwen2.5:3b — modelo menor, mais rápido)
    # Single LLM ativo por vez evita CPU saturation que crashou produção 2026-05-15
    analise = await economista_analisar_async(
        contrato_meta,
        bacen_data,
        invoke_fn=economista_invoke_fn,
    )

    return (tese, analise)


# Backward-compat alias — preserva imports existentes (pipeline.py + tests)
# ADR-023 renomeou função paralelo→sequencial; API consumers não precisam migrar.
# DEPRECATED: prefira `run_personas_sequencial` em novo código.
run_personas_paralelas = run_personas_sequencial
