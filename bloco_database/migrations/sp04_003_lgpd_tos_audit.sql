-- ════════════════════════════════════════════════════════════════════════════
-- Sprint 04 · Story SP04-LGPD-01 · Chunk 2 (Path B)
-- Migration: tos_acceptances + RLS + indexes
--
-- Tabela criada:
--   • tos_acceptances    (evidence LGPD ANPD — mirror dpa_acceptances ADR-019)
--
-- Decisões aplicadas (Tank Phase 13.3a — ratify LIGHT):
--   1. Item 1 — Mirror sem desvio do schema dpa_acceptances (ADR-019 §2)
--   2. Item 2 — UNIQUE composite (tenant_id, tos_version) + COMMENT ON
--               CONSTRAINT inline documentando multi-version audit semantic
--   3. Item 3 — 2 indexes seletivos (tenant_id alta + tos_version alta)
--               TD-SP04-08 reavaliar 5K+ tenants em Sprint 06+
--
-- Pré-requisitos:
--   • sp04_001_auth_multitenant.sql aplicada (tenants + users + dpa_acceptances)
--   • Extensões: pgcrypto (gen_random_uuid)
--
-- ADR-019 alignment: tabela tos_acceptances é mirror estrutural de
-- dpa_acceptances. Pattern audit governance LGPD validado em SP04-AUTH-01
-- chunk 5 + Oracle qa-gate G5. Reuse pattern reduz surface bugs + consistency
-- BACKBONE multi-tenant Pool+RLS (ADR-017).
-- ════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ─── Tabela: tos_acceptances (mirror dpa_acceptances ADR-019) ────────────────
-- Evidence LGPD para auditoria ANPD: aceite TOS/EULA declara explicitamente
-- Eric=operador (não controlador) per Art. 5º LGPD. Retention PERMANENT
-- (ON DELETE RESTRICT em FKs) — apenas archive permitido, nunca DELETE direto,
-- mesmo após off-boarding tenant (Art. 52 LGPD compliance — multa R$ 50M cap).

CREATE TABLE tos_acceptances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
  tos_version VARCHAR(20) NOT NULL,
  tos_text_hash VARCHAR(64) NOT NULL,
  accepted_at TIMESTAMP WITH TIME ZONE NOT NULL,
  accepted_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  CONSTRAINT unique_tenant_tos_version UNIQUE (tenant_id, tos_version)
);

-- Tank Phase 13.3a Item 2: documenta semantic multi-version em pg_constraint
-- metadata (queryable via `\d+ tos_acceptances` psql).
COMMENT ON CONSTRAINT unique_tenant_tos_version ON tos_acceptances IS
  'Multi-version audit trail: cada (tenant, version) gera 1 row distinct. '
  'TOS major bump força re-aceite (ADR-019 §5 pattern); minor bumps (typo/clarification) '
  'NÃO requerem re-aceite. Re-aceite mesma version retorna 409 Conflict (idempotent).';

ALTER TABLE tos_acceptances ENABLE ROW LEVEL SECURITY;

CREATE POLICY tos_tenant_isolation ON tos_acceptances
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

CREATE INDEX idx_tos_acceptances_tenant ON tos_acceptances(tenant_id);
CREATE INDEX idx_tos_acceptances_version ON tos_acceptances(tos_version);


COMMIT;

-- ════════════════════════════════════════════════════════════════════════════
-- Smoke validation (post-apply):
--
--   -- Verificar RLS habilitado
--   SELECT relname, relrowsecurity FROM pg_class
--    WHERE relname = 'tos_acceptances';
--   -- Esperado: 1 linha, relrowsecurity = true
--
--   -- Verificar policy criada
--   SELECT tablename, policyname FROM pg_policies
--    WHERE tablename = 'tos_acceptances';
--   -- Esperado: tos_tenant_isolation
--
--   -- Verificar indexes
--   SELECT tablename, indexname FROM pg_indexes
--    WHERE tablename = 'tos_acceptances'
--    ORDER BY indexname;
--   -- Esperado: idx_tos_acceptances_tenant, idx_tos_acceptances_version,
--   --          tos_acceptances_pkey, unique_tenant_tos_version (UNIQUE index)
--
--   -- Verificar comment inline na constraint
--   SELECT conname, obj_description(oid, 'pg_constraint')
--     FROM pg_constraint
--    WHERE conname = 'unique_tenant_tos_version';
--   -- Esperado: 1 linha com comment Multi-version audit trail...
--
-- Rollback (se necessário antes de produção):
--   BEGIN;
--   DROP TABLE IF EXISTS tos_acceptances CASCADE;
--   COMMIT;
-- ════════════════════════════════════════════════════════════════════════════
