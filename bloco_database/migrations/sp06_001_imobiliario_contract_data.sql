-- ════════════════════════════════════════════════════════════════════════════
-- Sprint 5+ · Story TD-SP04-S4-V1-IMOBILIARIO-WIREFRAME-VARIANT · Chunk 1
-- Migration: imobiliario_contract_data + RLS + CHECK constraints
--
-- Tabela criada:
--   • imobiliario_contract_data  (Sati Eixo 4 NEEDS CHANGES pull-forward Sprint 5+)
--
-- REUSE source (Sati ratify Eixo 4 + TECH-DEBT TD-SP04-S4-V1 linha 929):
--   • bloco_database/migrations/sp05_001_analytics_events.sql (Bloco 2 pattern)
--   • architecture/adr/adr-017-multi-tenant-isolation-rls.md §2-§3 (RLS template)
--
-- 4 campos específicos Imobiliário SFH/SFI:
--   1. matricula_rgi  — formato cartório.livro.folha.X.Y (regex regional Sprint 6+)
--   2. valor_avaliacao — Decimal R$ ≥0 ≤R$ 100M sanity bound
--   3. tipo_garantia  — enum alienacao_fiduciaria | hipoteca (Lei 9.514/97 + CC Art. 1.473)
--   4. indice_correcao — enum TR | IPCA | IGP-M | PRE (SFH TR + SFI livre)
--
-- Pré-requisitos:
--   • sp04_001_auth_multitenant.sql aplicada (tenants table + RLS infrastructure)
--   • Extensões: pgcrypto (gen_random_uuid)
-- ════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ─── Tabela: imobiliario_contract_data ──────────────────────────────────────
CREATE TABLE imobiliario_contract_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
  analysis_id UUID,  -- FK contracts/analyses table (Sprint 06+ when migrated)

  -- 4 fields Imobiliário-specific (TECH-DEBT TD-SP04-S4-V1 cataloged)
  matricula_rgi VARCHAR(40) NOT NULL,  -- formato X.XXX.XXX.XX.XXXX (regional variance R-06 LOW Sprint 6+)
  valor_avaliacao NUMERIC(14, 2) NOT NULL,  -- R$ 0,00 a R$ 100.000.000,00
  tipo_garantia VARCHAR(30) NOT NULL,  -- enum CHECK constraint below
  indice_correcao VARCHAR(10) NOT NULL,  -- enum CHECK constraint below

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  -- Garantia constrained — 2 modalidades legais
  -- Lei 9.514/97 (alienação fiduciária) + CC Art. 1.473 (hipoteca)
  CONSTRAINT valid_tipo_garantia CHECK (tipo_garantia IN (
    'alienacao_fiduciaria',  -- Lei 9.514/97 — modalidade SFI predominante + SFH
    'hipoteca'               -- CC Art. 1.473 — modalidade legacy + commercial
  )),

  -- Índice correção constrained — 4 modalidades
  -- TR padrão SFH; IPCA/IGP-M livres SFI; PRE fixo
  CONSTRAINT valid_indice_correcao CHECK (indice_correcao IN (
    'tr',     -- Taxa Referencial — SFH padrão
    'ipca',   -- IPCA — SFI livre indexado
    'igpm',   -- IGP-M — legacy contracts pré-2022
    'pre'     -- Pré-fixado — taxa fixa contratual
  )),

  -- Valor avaliação bounds sanity (R-07 LOW catalogged: commercial SFI may exceed)
  CONSTRAINT valid_valor_avaliacao CHECK (
    valor_avaliacao >= 0 AND valor_avaliacao <= 100000000.00
  ),

  -- Matrícula RGI not empty (regex validation backend Pydantic Chunk 2)
  CONSTRAINT valid_matricula_rgi CHECK (
    LENGTH(TRIM(matricula_rgi)) > 0
  )
);

COMMENT ON TABLE imobiliario_contract_data IS
  'Sprint 5+ Bloco 3 (Sati Eixo 4 NEEDS CHANGES pull-forward Sprint 06+→5+). '
  'Wireframe variant Imobiliário SFH/SFI com 4 campos específicos (matrícula RGI + '
  'valor + garantia + índice). Template unificado bancário não cabe — esta tabela '
  'estende para 1 de 3 doctypes novos. V2 FIES + V3 Geral catch-all Sprint 6+ next.';

COMMENT ON COLUMN imobiliario_contract_data.matricula_rgi IS
  'Matrícula do Registro Geral de Imóveis (RGI) — formato X.XXX.XXX.XX.XXXX. '
  'Regional variance (R-06 LOW Sprint 6+ TODO regex adaptive SP/RJ/MG/BA). '
  'Backend Pydantic Chunk 2 valida format via regex (frontend pattern attribute).';

COMMENT ON COLUMN imobiliario_contract_data.tipo_garantia IS
  'Lei 9.514/97 (alienação fiduciária) — modalidade SFI predominante + SFH atual; '
  'CC Art. 1.473 (hipoteca) — modalidade legacy + commercial real estate.';

COMMENT ON COLUMN imobiliario_contract_data.indice_correcao IS
  'TR (SFH padrão Caixa) + IPCA (SFI livre) + IGP-M (legacy pre-2022) + PRE (fixo). '
  'CET calculation backend considera índice variable vs fixo Chunk 2.';

-- ─── RLS habilitar + policy (ADR-017 §2 reuse direto Bloco 2 pattern) ──────
ALTER TABLE imobiliario_contract_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY imobiliario_tenant_isolation ON imobiliario_contract_data
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

-- ─── Indexes seletivos ─────────────────────────────────────────────────────
-- Query patterns esperados:
--   1. Lookup by tenant + analysis_id (1:1 contract data)
--   2. Aggregate per tenant + indice (analytics future Sprint 6+)
--   3. Aggregate per tenant + garantia (legal portfolio analytics)

CREATE INDEX idx_imobiliario_tenant_analysis
  ON imobiliario_contract_data(tenant_id, analysis_id)
  WHERE analysis_id IS NOT NULL;

CREATE INDEX idx_imobiliario_tenant_indice
  ON imobiliario_contract_data(tenant_id, indice_correcao);

CREATE INDEX idx_imobiliario_tenant_garantia
  ON imobiliario_contract_data(tenant_id, tipo_garantia);

COMMIT;

-- ════════════════════════════════════════════════════════════════════════════
-- Smoke validation (post-apply):
--
--   -- RLS habilitado
--   SELECT relname, relrowsecurity FROM pg_class
--    WHERE relname = 'imobiliario_contract_data';
--   -- Esperado: relrowsecurity = true
--
--   -- Policy
--   SELECT tablename, policyname FROM pg_policies
--    WHERE tablename = 'imobiliario_contract_data';
--   -- Esperado: imobiliario_tenant_isolation
--
--   -- CHECK constraints (4 total: garantia + indice + valor + matricula)
--   SELECT conname FROM pg_constraint
--    WHERE conrelid = 'imobiliario_contract_data'::regclass
--      AND contype = 'c'
--    ORDER BY conname;
--
--   -- Indexes (4 total: PRIMARY KEY + 3 seletivos)
--   SELECT indexname FROM pg_indexes
--    WHERE tablename = 'imobiliario_contract_data'
--    ORDER BY indexname;
--
-- Rollback:
--   BEGIN; DROP TABLE IF EXISTS imobiliario_contract_data CASCADE; COMMIT;
-- ════════════════════════════════════════════════════════════════════════════
