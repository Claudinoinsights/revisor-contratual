"""bloco_contratos — Pydantic models compartilhados entre TODOS os blocos do Revisor Contratual.

Princípios (decisão arquitetural Atlas + Aria):
  - Contratos formais previnem acoplamento implícito entre blocos
  - Substituir 1 bloco (ex: sqlite-vec → Qdrant) NÃO exige tocar nos demais
  - NFR-MAINT-01: modularidade preservada via interfaces Pydantic
  - Decimal everywhere (Decimal-as-string em wire format) — FR-CALC-01

ADRs relacionadas:
  - ADR-003 (4 personas + Pydantic structured output)
  - ADR-007 (schema sqlite-vec + JurisprudenciaItem)
"""

from bloco_contratos.contrato import (
    BacenData,
    ContratoMetadata,
    LinhaAmortizacao,
    ParsedContract,
    ResultadoCalculo,
)
from bloco_contratos.jurisprudencia import (
    CourtId,
    JurisprudenciaItem,
    PesoVinculacao,
    TipoDoc,
)
from bloco_contratos.personas import (
    AnaliseMacroEconomica,
    LLMTier,
    TeseAdvogado,
    ValidacaoSemantica,
    VeredictoJuiz,
)

__all__ = [
    # Personas (ADR-003)
    "TeseAdvogado",
    "AnaliseMacroEconomica",
    "VeredictoJuiz",
    "ValidacaoSemantica",
    "LLMTier",
    # Contrato + cálculo (FR-CALC-01..03, FR-PARSE-01..02)
    "ContratoMetadata",
    "ParsedContract",
    "ResultadoCalculo",
    "LinhaAmortizacao",
    "BacenData",
    # Jurisprudência (ADR-007 schema)
    "JurisprudenciaItem",
    "CourtId",
    "TipoDoc",
    "PesoVinculacao",
]
