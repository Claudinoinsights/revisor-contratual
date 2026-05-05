"""bloco_engine — Parsing PDF + Cálculo Decimal + Integração BACEN.

Componentes (a implementar em stories sucessivas):
  - parsing/         — PyMuPDF4LLM + Marker (FR-PARSE-01..02)
  - ferramentas_calculo/  — Decimal puro (FR-CALC-01..03) ✅ STORY 2
  - bacen/           — python-bcb wrapper + cache + retry (FR-BACEN-01..03)
"""

from bloco_engine import bacen, ferramentas_calculo, parsing

__all__ = ["ferramentas_calculo", "bacen", "parsing"]
