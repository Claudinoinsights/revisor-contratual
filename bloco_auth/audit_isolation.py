"""Audit isolation endpoint — Sprint 04 SP04-LGPD-01 AC-05 (FR-AUDIT-01).

``GET /api/tenant/audit/isolation`` retorna metadata transparente para
escritório auditar isolamento de dados conforme ADR-017 BACKBONE
(multi-tenant Pool+RLS). Resposta inclui:

- Counts (users, analyses, dpa_acceptances, tos_acceptances, audit events)
- RLS policies ativas (introspection PostgreSQL pg_policies)
- Last login per user (audit access pattern)
- ``rls_session_var_set`` boolean (verifica ``app.tenant_id`` setado)

Auth obrigatório (Depends ``get_current_user`` + RLS context aplicado).
Audit chain HMAC event ``audit_isolation_queried`` (ADR-005 pattern).

Skeleton — implementação completa em chunk 5 do Path B.
"""

from __future__ import annotations
