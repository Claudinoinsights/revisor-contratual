"""Workflow orchestrator — fan-out paralelo Advogado + Economista (D-MOR-3.3-C).

asyncio.gather garante PARALELISMO REAL (verificado empiricamente F-MIN-02 RESOLVIDO):
  - langchain-ollama 1.x ChatOllama.ainvoke é coroutine real
  - ollama.AsyncClient.chat subjacente é coroutine real
  - 2 instâncias Ollama em portas distintas (F-MIN-01 fix)

Atomicidade: se UMA persona falha, asyncio.gather propaga a exceção (default behavior).
Decisão Morpheus: falha tudo → não emite peça parcial. Erro rastreável é melhor que
veredito enviesado por análise faltando.
"""

from __future__ import annotations

import asyncio

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


async def run_personas_paralelas(
    contrato_meta: ContratoMetadata,
    calculo: ResultadoCalculo,
    docs: list[JurisprudenciaItem],
    bacen_data: BacenData,
    *,
    tier_advogado: LLMTier = "premium",
    advogado_invoke_fn: InvokeFnAdvogado | None = None,
    economista_invoke_fn: InvokeFnEconomista | None = None,
) -> tuple[TeseAdvogado, AnaliseMacroEconomica]:
    """Executa Advogado + Economista EM PARALELO via asyncio.gather.

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
        propaga ValidationError ou exceção da primeira persona que falha.
    """
    return await asyncio.gather(
        advogado_redigir_tese_async(
            calculo,
            docs,
            contrato_meta,
            tier_advogado,
            invoke_fn=advogado_invoke_fn,
        ),
        economista_analisar_async(
            contrato_meta,
            bacen_data,
            invoke_fn=economista_invoke_fn,
        ),
    )
