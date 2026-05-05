"""bloco_workflow/personas — Implementação técnica das 4 personas (ADR-003).

Componentes:
  - juiz.py — Python puro (FR-JUIZ-01..03) ✅ STORY 3
  - advogado.py — LLM Sabia tier configurável (FR-TESE-01..02) ✅ STORY 7 SUB-D
  - economista.py — LLM Qwen 2.5 3B FIXO (FR-PERSONA-ECO-01) ✅ STORY 7 SUB-D
  - llm_factory.py — get_advogado_llm/get_economista_llm com base_url EXPLÍCITO (F-MIN-01)
  - perito.py — wrapper sobre bloco_engine/ferramentas_calculo (futuro/integração STORY 8)
"""

from bloco_workflow.personas.advogado import advogado_redigir_tese_async
from bloco_workflow.personas.economista import economista_analisar_async
from bloco_workflow.personas.juiz import (
    C1_DIVERGENCIA_BACEN_PP_LIMIAR,
    C2_PESO_VINCULACAO_MIN,
    THRESHOLD_APROVADO_100,
    THRESHOLD_HITL_MIN,
    juiz_revisar,
)
from bloco_workflow.personas.llm_factory import (
    DEFAULT_HOST_ADVOGADO,
    DEFAULT_HOST_ECONOMISTA,
    MODEL_ECONOMISTA,
    TIER_TO_MODEL_ADVOGADO,
    get_advogado_llm,
    get_economista_llm,
)

__all__ = [
    # juiz (STORY 3)
    "juiz_revisar",
    "C1_DIVERGENCIA_BACEN_PP_LIMIAR",
    "C2_PESO_VINCULACAO_MIN",
    "THRESHOLD_APROVADO_100",
    "THRESHOLD_HITL_MIN",
    # personas LLM (STORY 7 SUB-D)
    "advogado_redigir_tese_async",
    "economista_analisar_async",
    # factory
    "get_advogado_llm",
    "get_economista_llm",
    "DEFAULT_HOST_ADVOGADO",
    "DEFAULT_HOST_ECONOMISTA",
    "MODEL_ECONOMISTA",
    "TIER_TO_MODEL_ADVOGADO",
]
