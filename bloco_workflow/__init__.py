"""bloco_workflow — Orquestração das personas + inferência sequencial + pipeline E2E.

Componentes:
  - personas/ — juiz (Python puro) + advogado/economista/redator (LLM) ✅ STORIES 3 + 7 + γ
  - orchestrator.py — run_personas_sequencial (ADR-023 D-ARIA-S06-018) ✅ STORY 7 + Sprint 6.x
  - pipeline.py — revisar_contrato (PDF → VeredictoJuiz → PecaRevisional + audit) ✅ STORY 9

ADR-023 (D-ARIA-S06-018, 2026-05-15): paralelismo asyncio.gather original (D-MOR-3.3-C)
refatorado para sequential em resposta a F-PROD-NEW-18 (VPS load 151 → 0.17). Backward-compat
alias `run_personas_paralelas` preservado para consumers existentes.
"""

from bloco_workflow.orchestrator import (
    run_personas_paralelas,  # backward-compat alias (ADR-023)
    run_personas_sequencial,
)
from bloco_workflow.pipeline import (
    PipelineError,
    VaultEmptyError,
    revisar_contrato,
)

__all__ = [
    "run_personas_sequencial",
    "run_personas_paralelas",  # backward-compat alias
    "revisar_contrato",
    "PipelineError",
    "VaultEmptyError",
]
