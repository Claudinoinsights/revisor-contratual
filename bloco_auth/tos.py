"""TOS/EULA (Terms of Service) flow — Sprint 04 SP04-LGPD-01 AC-02/AC-04.

Mirror estrutural de ``bloco_auth/dpa.py`` (ADR-019 padrão validado).
Diferença material: TOS declara **operador posture** Eric=operador,
escritório=controlador (Art. 5º LGPD); DPA descreve **tratamento** dos
dados pessoais. Schema ``tos_acceptances`` espelha ``dpa_acceptances``
sem desvio (Tank Phase 13.3a Item 1).

Skeleton — implementação completa em chunk 3 do Path B.
"""

from __future__ import annotations
