"""bloco_database — Sprint 04 PostgreSQL foundation (multi-tenant Pool+RLS).

Container das migrations SQL executadas em ordem sequencial contra o
PostgreSQL 16 do tenant pool. Cada migration é versionada
(``sp04_NNN_descricao.sql``) e aplicada via ``psql`` ou ferramenta de runner
escolhida por @devops em fase posterior.

Sprint 04 introduz PostgreSQL ao lado do SQLite Sprint 03 (ADR-007 superseded
por ADR-017 mas código ainda usa SQLite para vault/audit — refactor pendente
Sprint 05+).

Migration files:
    migrations/sp04_001_auth_multitenant.sql — tenants + users + RLS (SP04-AUTH-01)

Aplicação local (dev):
    psql "$DATABASE_URL" -f bloco_database/migrations/sp04_001_auth_multitenant.sql
"""

__all__: list[str] = []
