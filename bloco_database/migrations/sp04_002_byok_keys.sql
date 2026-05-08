-- ════════════════════════════════════════════════════════════════════════════
-- Migration: sp04_002_byok_keys
-- Sprint: 04 (Cloud SaaS BYOK Pivot)
-- Story: SP04-BYOK-01 — BYOK Anthropic key lifecycle
--
-- Cria persistência BYOK Anthropic key lifecycle (encryption + dual-key rotation
-- + revoke purge LGPD + pg_cron auto-complete). Schema canônico per ADR-014
-- §Decisão.Componentes 7 + Tank ratify decisions Phase 12.3a.
--
-- Tank decisions aplicadas:
--   Item 1: 3 CHECK constraints separados (rotation_state + revoked_purge + status_enum)
--   Item 2: pg_cron primary (stored procedure + cron.schedule hourly)
--   Item 3: Partial indexes DROP (cardinality 1 row/tenant; PK index suficiente)
--   Item 4: ALTER TABLE tenants enum strict (retrofit Sprint 04+)
--   Item 5: last_used_at inline per-request UPDATE (volume MVP)
--
-- Aplicação local (dev):
--   psql "$DATABASE_URL" -f bloco_database/migrations/sp04_002_byok_keys.sql
--
-- Cross-references:
--   governance/stories/sp04-byok-01-anthropic-key-lifecycle.md (AC-01..AC-08)
--   governance/architecture/adr/adr-014-provider-abstraction-byok.md
--   governance/architecture/adr/adr-017-multi-tenant-isolation-rls.md (BACKBONE)
--   .lmas/handoffs/handoff-dbe-to-dev-2026-05-08-sp04-phase12-ratify-byok-01.yaml
-- ════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ─── Extensions ─────────────────────────────────────────────────────────────
-- pgcrypto: pgp_sym_encrypt/decrypt para encrypted_key (idempotent — já em AUTH-01)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- pg_cron: rotation auto-complete 24h overlap (Tank decision Item 2 — primary)
-- Fallback APScheduler Sprint 06+ TD-SP04-04 se deployment não suportar.
CREATE EXTENSION IF NOT EXISTS pg_cron;


-- ─── Tabela: tenant_api_keys (ADR-014 §Decisão.Componentes 7 + Tank Phase 12.3a) ─
-- Quota Interna pattern: 1 key/escritório (tenant_id PK, não FK adicional).
-- encrypted_key NULLABLE — Tank Item 1 forca purge via revoked_purge_consistency.
-- Dual-key state machine 24h overlap via pending_* + rotation_started_at.

CREATE TABLE tenant_api_keys (
  tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  encrypted_key BYTEA,                          -- pgp_sym_encrypt(key, master_key); NULL apenas em status='revoked'
  key_fingerprint VARCHAR(20) NOT NULL,         -- 'sk-ant-...XYZ' truncated (audit/UI; NUNCA full key)
  status VARCHAR(20) NOT NULL DEFAULT 'active', -- enum: active|pending_rotation|revoked
  pending_encrypted_key BYTEA,                  -- dual-key rotation overlap 24h
  pending_fingerprint VARCHAR(20),              -- truncated novo key durante rotation
  rotation_started_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  last_used_at TIMESTAMP WITH TIME ZONE,        -- Tank Item 5: inline per-request UPDATE

  -- Tank Item 1: 3 CHECK constraints separados (clearer audit + force purge invariant)
  CONSTRAINT rotation_state_consistency CHECK (
    (status = 'pending_rotation'
      AND pending_encrypted_key IS NOT NULL
      AND pending_fingerprint IS NOT NULL
      AND rotation_started_at IS NOT NULL)
    OR
    (status IN ('active', 'revoked')
      AND pending_encrypted_key IS NULL
      AND pending_fingerprint IS NULL
      AND rotation_started_at IS NULL)
  ),
  CONSTRAINT revoked_purge_consistency CHECK (
    (status = 'revoked' AND encrypted_key IS NULL)
    OR
    (status != 'revoked' AND encrypted_key IS NOT NULL)
  ),
  CONSTRAINT byok_status_enum CHECK (
    status IN ('active', 'pending_rotation', 'revoked')
  )
);

-- RLS pattern AUTH-01 BACKBONE
ALTER TABLE tenant_api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY byok_tenant_isolation ON tenant_api_keys
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

-- Tank Item 3: Partial indexes REMOVIDOS — cardinality 1 row/tenant + scale MVP <500 rows
-- justifica seq scan trivial. PRIMARY KEY index implícito suficiente.
-- Reavaliar 5K+ tenants — TD-SP04-04 EXPLAIN ANALYZE Sprint 07+.


-- ─── Retrofit: tenants.status enum strict (Tank Item 4) ─────────────────────
-- Migration AUTH-01 deferiu para "Sprint 05+ se proliferação justificar".
-- SP04-BYOK-01 introduz 'suspended_byok' (FR-API-KEY-04 revoke flow) → 4 valores
-- = ponto inflexão typo prevention. ALTER TABLE trivial em <50 rows.
ALTER TABLE tenants
  ADD CONSTRAINT tenant_status_enum CHECK (
    status IN ('active', 'suspended', 'dpa_pending', 'suspended_byok')
  );


-- ─── Rotation auto-complete cron (Tank Item 2 — pg_cron primary) ────────────
-- Stored procedure executa atomic UPDATE quando rotation_started_at + 24h ≤ NOW().
-- Multi-instance safe (DB-side execution); reliable mesmo com Python down.

CREATE OR REPLACE PROCEDURE complete_pending_rotations()
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE tenant_api_keys
     SET encrypted_key = pending_encrypted_key,
         key_fingerprint = pending_fingerprint,
         status = 'active',
         pending_encrypted_key = NULL,
         pending_fingerprint = NULL,
         rotation_started_at = NULL
   WHERE status = 'pending_rotation'
     AND rotation_started_at + INTERVAL '24 hours' <= NOW();
END;
$$;

-- Schedule hourly job (cron syntax: minute hour day month weekday)
-- '0 * * * *' = top of every hour
SELECT cron.schedule(
  'byok-rotation-complete',
  '0 * * * *',
  $$CALL complete_pending_rotations()$$
);


COMMIT;

-- ════════════════════════════════════════════════════════════════════════════
-- Smoke validation (post-apply):
--
--   -- Verificar extensions
--   SELECT extname FROM pg_extension WHERE extname IN ('pgcrypto', 'pg_cron');
--   -- Esperado: 2 linhas
--
--   -- Verificar tabela criada
--   SELECT relname, relrowsecurity FROM pg_class WHERE relname = 'tenant_api_keys';
--   -- Esperado: 1 linha com relrowsecurity=true
--
--   -- Verificar 3 CHECK constraints
--   SELECT conname FROM pg_constraint
--    WHERE conrelid = 'tenant_api_keys'::regclass AND contype = 'c'
--    ORDER BY conname;
--   -- Esperado: byok_status_enum, revoked_purge_consistency, rotation_state_consistency
--
--   -- Verificar tenants.status CHECK retrofit
--   SELECT conname FROM pg_constraint
--    WHERE conrelid = 'tenants'::regclass AND contype = 'c' AND conname = 'tenant_status_enum';
--   -- Esperado: 1 linha
--
--   -- Verificar policy criada
--   SELECT policyname FROM pg_policies WHERE tablename = 'tenant_api_keys';
--   -- Esperado: byok_tenant_isolation
--
--   -- Verificar pg_cron job
--   SELECT jobname, schedule, command FROM cron.job WHERE jobname = 'byok-rotation-complete';
--   -- Esperado: 1 linha com schedule='0 * * * *' command='CALL complete_pending_rotations()'
--
--   -- Smoke encrypt/decrypt roundtrip (test data — não em produção)
--   -- SELECT pgp_sym_decrypt(pgp_sym_encrypt('sk-ant-test', 'master-key-32-bytes-min-here-ok!!'), 'master-key-32-bytes-min-here-ok!!');
-- ════════════════════════════════════════════════════════════════════════════
