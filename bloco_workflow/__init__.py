"""bloco_workflow — Orquestração das personas + fan-out paralelo + pipeline E2E.

Componentes:
  - personas/ — juiz (Python puro) + advogado/economista (LLM) ✅ STORIES 3 + 7
  - orchestrator.py — run_personas_paralelas (asyncio.gather D-MOR-3.3-C) ✅ STORY 7
  - pipeline.py — revisar_contrato (PDF → VeredictoJuiz + audit) ✅ STORY 9
"""

from bloco_workflow.orchestrator import run_personas_paralelas
from bloco_workflow.pipeline import (
    PipelineError,
    VaultEmptyError,
    revisar_contrato,
)

__all__ = [
    "run_personas_paralelas",
    "revisar_contrato",
    "PipelineError",
    "VaultEmptyError",
]
