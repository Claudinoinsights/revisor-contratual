-- ════════════════════════════════════════════════════════════════════════════
-- Migration: sp04_001_auth_multitenant
-- Sprint: 04 (Cloud SaaS BYOK Pivot)
-- Story: SP04-AUTH-01 — Multi-tenant authentication + tenant onboarding
--
-- Cria fundação multi-tenant para autenticação SaaS B2B:
--   • tenants            (escritórios advocacia — ADR-017 BACKBONE pattern)
--   • users              (advogados internos — RLS scoped por tenant)
--   • dpa_acceptances    (evidence LGPD ANPD — ADR-019 spec-level)
--
-- Defense-in-depth (ADR-017):
--   1. Row-Level Security policies em todas as tabelas
--   2. UNIQUE constraints anti-collisão (cnpj, email global, email por tenant)
--   3. ON DELETE CASCADE (users) / RESTRICT (dpa_acceptances) per LGPD
--
-- Aplicação local (dev):
--   psql "$DATABASE_URL" -f bloco_database/migrations/sp04_001_auth_multitenant.sql
--
-- Cross-references:
--   governance/stories/sp04-auth-01-multi-tenant-auth.md (AC-02, AC-03, AC-06)
--   governance/architecture/adr/adr-017-multi-tenant-isolation-rls.md (BACKBONE)
--   governance/architecture/adr/adr-019-dpa-storage-schema.md (level=spec)
-- ════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ─── Extensions ─────────────────────────────────────────────────────────────
-- pgcrypto fornece gen_random_uuid() e funções HMAC/digest (audit chain SP04)
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ─── Tabela: tenants ────────────────────────────────────────────────────────
-- Cada escritório de advocacia é um tenant. CNPJ não-formatado (14 dígitos).
-- Status enumerável via VARCHAR (active|suspended|dpa_pending) — promoção para
-- tipo CHECK constraint diferida para Sprint 05+ se proliferação justificar.

CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cnpj VARCHAR(14) UNIQUE NOT NULL,
  razao_social TEXT NOT NULL,
  advogado_responsavel TEXT NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

-- Política: tenant só enxerga linha do próprio id (auto-visualização)
CREATE POLICY tenant_self_view ON tenants
  USING (id = current_setting('app.tenant_id', true)::uuid);

CREATE INDEX idx_tenants_cnpj ON tenants(cnpj);
CREATE INDEX idx_tenants_email ON tenants(email);


-- ─── Tabela: users ──────────────────────────────────────────────────────────
-- Advogados internos do escritório. Email único POR TENANT (não global) — dois
-- escritórios diferentes podem ter advogado@gmail.com sem colisão.
-- password_hash bcrypt cost factor 12 (Story AC-03 + AC-08 critical scenario #3).

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  nome TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  CONSTRAINT unique_email_per_tenant UNIQUE (tenant_id, email)
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Política: users restritos ao tenant_id da sessão atual (RLS BACKBONE)
CREATE POLICY user_tenant_isolation ON users
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

CREATE INDEX idx_users_tenant ON users(tenant_id);


-- ─── Tabela: dpa_acceptances (ADR-019 spec-level) ───────────────────────────
-- Evidence LGPD para auditoria ANPD: quando/quem/qual versão/qual hash/de qual IP.
-- Retention PERMANENT (ON DELETE RESTRICT em FKs) — apenas archive permitido,
-- nunca DELETE direto, mesmo após off-boarding tenant (Art. 52 LGPD compliance).

CREATE TABLE dpa_acceptances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
  dpa_version VARCHAR(20) NOT NULL,
  dpa_text_hash VARCHAR(64) NOT NULL,
  accepted_at TIMESTAMP WITH TIME ZONE NOT NULL,
  accepted_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  CONSTRAINT unique_tenant_version UNIQUE (tenant_id, dpa_version)
);

ALTER TABLE dpa_acceptances ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON dpa_acceptances
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

CREATE INDEX idx_dpa_acceptances_tenant ON dpa_acceptances(tenant_id);
CREATE INDEX idx_dpa_acceptances_version ON dpa_acceptances(dpa_version);


COMMIT;

-- ════════════════════════════════════════════════════════════════════════════
-- Smoke validation (post-apply):
--
--   -- Verificar extensions
--   SELECT extname FROM pg_extension WHERE extname = 'pgcrypto';
--
--   -- Verificar RLS habilitado em todas as 3 tabelas
--   SELECT relname, relrowsecurity FROM pg_class
--    WHERE relname IN ('tenants', 'users', 'dpa_acceptances');
--   -- Esperado: 3 linhas, todas com relrowsecurity = true
--
--   -- Verificar policies criadas
--   SELECT tablename, policyname FROM pg_policies
--    WHERE tablename IN ('tenants', 'users', 'dpa_acceptances')
--    ORDER BY tablename;
--   -- Esperado: tenant_self_view (tenants), user_tenant_isolation (users),
--   --          tenant_isolation (dpa_acceptances)
--
--   -- Verificar indexes
--   SELECT tablename, indexname FROM pg_indexes
--    WHERE tablename IN ('tenants', 'users', 'dpa_acceptances')
--    ORDER BY tablename, indexname;
-- ════════════════════════════════════════════════════════════════════════════
