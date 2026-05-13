-- ════════════════════════════════════════════════════════════════════════════
-- Sprint 5+ · Story TD-SP04-04-ANALYTICS · Chunk 1 (Path B)
-- Migration: analytics_events + RLS + HMAC chain + idempotency
--
-- Tabela criada:
--   • analytics_events   (Sati Eixo 5 MANDATORY pre-release v0.3.0)
--
-- REUSE source (PRD v2.0.5.1 Section 5 REUSE Table):
--   • bloco_database/migrations/sp04_003_lgpd_tos_audit.sql (mirror tos_acceptances pattern)
--   • architecture/adr/adr-017-multi-tenant-isolation-rls.md §2-§3 (RLS policy template)
--   • bloco_audit/chain.py (HMAC chain append_audit_entry — server-side derivation)
--
-- Decisões aplicadas (Trinity v2.0.5.1 + Smith F-SMITH-PRD-C1/C2 fixes):
--   1. tenant_id derivado server-side (NÃO no payload) — RLS enforces
--   2. UNIQUE (event_id) para idempotency NFR-RELIABILITY-01 (Smith H1 fix)
--   3. HMAC chain via prev_hash → integrity tamper detection (Smith C2 fix)
--   4. ON DELETE RESTRICT em FK — retention 13 meses LGPD (NFR-PRIVACY-01.5)
--   5. event_type enum constrained — 5 metrics + meta-event types
--
-- Pré-requisitos:
--   • sp04_001_auth_multitenant.sql aplicada (tenants table + RLS infrastructure)
--   • sp04_003_lgpd_tos_audit.sql aplicada (audit governance LGPD foundation)
--   • Extensões: pgcrypto (gen_random_uuid)
--
-- ADR alignment:
--   • ADR-017 §2 — Pool+RLS multi-tenant isolation (CREATE POLICY using tenant_id)
--   • ADR-019 — Audit storage pattern reuse (mirror dpa_acceptances/tos_acceptances)
--   • ADR-020 — Multi-doctype dispatcher (7 modos sidebar — analytics target validation)
-- ════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ─── Tabela: analytics_events (Sati Eixo 5 MANDATORY pre-release v0.3.0) ─────
-- Eventos analytics captured client-side, server-validated, HMAC-chained.
-- Multi-tenant isolation via RLS (ADR-017). Idempotency via UNIQUE event_id
-- (NFR-RELIABILITY-01). PII-free per NFR-PRIVACY-01.3 (9 vectors anonymized).
-- HMAC chain tamper detection per NFR-PRIVACY-01.6 (Smith C2 recovery protocol).

CREATE TABLE analytics_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID NOT NULL,  -- Client-side UUID v4 idempotency key (Smith F-01 fix)
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
  session_id UUID NOT NULL,  -- Random UUID rotated per NFR-PRIVACY-01.3.9 (50 events OR 30min)
  event_type VARCHAR(40) NOT NULL,  -- Constrained enum (CHECK below)
  doctype VARCHAR(20),  -- ccb|veiculo|consignado|cartao|imobiliario|fies|geral|NULL
  occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,  -- Rounded to nearest minute (PII timing fix)
  payload_json JSONB,  -- Event-specific data (PII-stripped); see NFR-PRIVACY-01.3 for 9 excluded vectors
  prev_hash VARCHAR(64),  -- Previous HMAC for chain integrity (Smith C2 fix)
  hmac VARCHAR(64) NOT NULL,  -- hmac_sha256(prev_hash || event_data, secret_key)
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  -- Smith F-SMITH-PRD-C1 fix: UNIQUE event_id ensures idempotency
  -- Backend catches psycopg.errors.UniqueViolation → returns HTTP 200 silent
  -- (NUNCA 409 Conflict default) — Smith F-01 contract gap addressed
  CONSTRAINT unique_event_id UNIQUE (event_id),

  -- Event types constrained — 5 FR-ANALYTICS metrics + 2 meta events
  -- Aligned with PRD v2.0.5.1 Section 2 + Section 4.2 frontend event types
  CONSTRAINT valid_event_type CHECK (event_type IN (
    'doctype_selected',         -- FR-ANALYTICS-05 Pareto + FR-ANALYTICS-02 TTI base
    'first_doctype_selected',   -- FR-ANALYTICS-03 Geral % first choice (after-login scope per Smith M3)
    'doctype_changed',          -- FR-ANALYTICS-04 reclassification matrix from→to
    'doctype_dropoff',          -- FR-ANALYTICS-01 drop-off rate per doctype
    'contract_submitted'        -- FR-ANALYTICS-02 TTI delta calc termination
  )),

  -- Doctype constrained (NULL allowed for non-doctype-bound events futuros)
  CONSTRAINT valid_doctype CHECK (
    doctype IS NULL OR doctype IN (
      'ccb', 'veiculo', 'consignado', 'cartao', 'imobiliario', 'fies', 'geral'
    )
  )
);

COMMENT ON CONSTRAINT unique_event_id ON analytics_events IS
  'Idempotency key (Smith F-SMITH-PRD-C1 fix v2.0.5.1): client UUID v4. '
  'Duplicate INSERT raises psycopg.errors.UniqueViolation; backend catches and returns '
  'HTTP 200 com body {status: "duplicate", event_id} — NUNCA 409 Conflict default. '
  'Pytest test_idempotency_returns_200_not_409 obrigatório (Smith G3 D-KEY-S05-002).';

COMMENT ON COLUMN analytics_events.hmac IS
  'HMAC chain integrity per NFR-PRIVACY-01.6 (Smith F-SMITH-PRD-C2 fix v2.0.5.1). '
  'Tamper detection runtime: bloco_auth/analytics.py compara hmac stored vs recomputed. '
  'Divergência → HTTP 500 + audit_log HMAC_INTEGRITY_VIOLATION CRITICAL + tenant quarantine. '
  'Cronjob analytics_chain_verify daily rescaneia últimos 7 dias chain integrity.';

COMMENT ON COLUMN analytics_events.occurred_at IS
  'Timestamp rounded to nearest minute (NFR-PRIVACY-01.3.8 — timing correlation attack mitigation). '
  'Original millisecond precision available client-side mas server-side stores rounded. '
  'Aggregate analytics (drop-off rate, TTI p90, Pareto) preserved precision; correlation cross-session blocked.';

-- ─── RLS habilitar + policy (ADR-017 §2 reuse direto) ──────────────────────
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY analytics_tenant_isolation ON analytics_events
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

-- ─── Indexes seletivos (Tank pattern Phase 13.3a Item 3) ──────────────────
-- Query patterns esperados (PRD v2.0.5.1 Section 4.3 CLI commands):
--   1. Aggregate per tenant + period (drop-off, TTI, Pareto, reclassification)
--   2. HMAC chain verification (sequential by created_at within tenant)
--   3. Idempotency lookup (event_id direct)

CREATE INDEX idx_analytics_events_tenant_occurred
  ON analytics_events(tenant_id, occurred_at);

CREATE INDEX idx_analytics_events_tenant_session
  ON analytics_events(tenant_id, session_id);

CREATE INDEX idx_analytics_events_tenant_event_type
  ON analytics_events(tenant_id, event_type);

CREATE INDEX idx_analytics_events_tenant_doctype
  ON analytics_events(tenant_id, doctype) WHERE doctype IS NOT NULL;

-- event_id UNIQUE constraint auto-creates index — não duplicar

-- ─── Cronjob registration (NFR-PRIVACY-01.6.2 — Smith C2 fix) ─────────────
-- Daily HMAC chain verification reuse SP04-LGPD-01 APScheduler pattern.
-- Implementation: bloco_auth/analytics.py register cronjob `analytics_chain_verify`
-- runs at 03:00 UTC daily, rescaneia últimos 7 dias HMAC chain integrity.
-- Implementação Python (NÃO SQL) — schedule documented aqui para handoff Neo.

COMMIT;

-- ════════════════════════════════════════════════════════════════════════════
-- Smoke validation (post-apply):
--
--   -- Verificar RLS habilitado
--   SELECT relname, relrowsecurity FROM pg_class
--    WHERE relname = 'analytics_events';
--   -- Esperado: 1 linha, relrowsecurity = true
--
--   -- Verificar policy
--   SELECT tablename, policyname FROM pg_policies
--    WHERE tablename = 'analytics_events';
--   -- Esperado: analytics_tenant_isolation
--
--   -- Verificar indexes (5 total: 4 created + 1 from UNIQUE event_id + 1 PRIMARY KEY)
--   SELECT tablename, indexname FROM pg_indexes
--    WHERE tablename = 'analytics_events'
--    ORDER BY indexname;
--   -- Esperado: analytics_events_pkey, idx_analytics_events_tenant_doctype,
--   --          idx_analytics_events_tenant_event_type, idx_analytics_events_tenant_occurred,
--   --          idx_analytics_events_tenant_session, unique_event_id
--
--   -- Verificar CHECK constraints
--   SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint
--    WHERE conrelid = 'analytics_events'::regclass
--      AND contype = 'c'
--    ORDER BY conname;
--   -- Esperado: valid_doctype, valid_event_type
--
-- Rollback (se necessário antes de produção):
--   BEGIN;
--   DROP TABLE IF EXISTS analytics_events CASCADE;
--   COMMIT;
-- ════════════════════════════════════════════════════════════════════════════
