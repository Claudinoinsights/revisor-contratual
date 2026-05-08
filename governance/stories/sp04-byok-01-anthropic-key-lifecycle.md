---
type: story
id: "SP04-BYOK-01"
title: "BYOK Anthropic key lifecycle — encryption + runtime injection + rotate/revoke"
status: Ready
epic: "Sprint 04 Cloud SaaS BYOK"
project: revisor-contratual
sprint: "04"
phase: 12.1
priority: P0
estimated_days: "3-5"
agent: "@dev (Neo)"
branch: "feat/sp04-byok-01 (será criada pós validate-story-draft → Ready)"
created: "2026-05-08"
created_by: "@sm River"
dependencies:
  - "SP04-AUTH-01 (Done — foundation P0 — wizard step2 OnboardingStep2Data + ping_anthropic_api validators existentes)"
  - "ADR-014 (BYOK Provider Abstraction Anthropic Only — schema tenant_api_keys + dual-key rotation 24h overlap + pgcrypto)"
  - "ADR-017 (Multi-tenant Pool+RLS BACKBONE — RLS pattern aplicado universalmente)"
  - "ADR-019 (DPA Storage Schema — pattern audit + retention reusable)"
  - "ADR-005 (Audit chain HMAC — payload tenant_id integration)"
source_frs:
  - "FR-API-KEY-01 (cadastro + validação via ping)"
  - "FR-API-KEY-02 (encryption pgcrypto.pgp_sym_encrypt)"
  - "FR-API-KEY-03 (rotação dual-key 24h overlap)"
  - "FR-API-KEY-04 (revoke self-service + suspend tenant + audit truncated)"
cross_references:
  prd: "governance/prd/prd-v2.0.0-DRAFT.md Section BYOK API Key Management (lines 89-94)"
  ux: "UX spec wizard step2 existente (SP04-AUTH-01 entregue) + panel `Configurações > BYOK` Settings novo (Sati pre-flight opcional)"
  adrs: ["adr-014", "adr-017", "adr-019", "adr-005"]
  story_predecessor: "SP04-AUTH-01"
  smith_findings_addressed: "F-014 (BYOK key encryption verification — Atlas v2 Section 1)"
tags:
  - project/revisor-contratual
  - story
  - sprint-04
  - epic-byok
  - foundation
  - p0
  - multi-tenant
  - encryption
  - anthropic
---

# SP04-BYOK-01 — BYOK Anthropic key lifecycle

```
[@sm · River (Facilitator)] — Sprint 04 · Phase 12.1 · SP04-BYOK-01 · BYOK lifecycle
SPRINT: 04 · PHASE: 12.1 · DOMÍNIO: software-dev/byok-encryption
```

> **Foundation Sprint 04 P0** — completa Cloud SaaS BYOK loop pós-SP04-AUTH-01. Wizard step2 já coleta `anthropic_api_key` validada via ping; SP04-BYOK-01 entrega encryption at rest pgcrypto + runtime injection middleware Anthropic SDK + lifecycle endpoints rotate/revoke + audit chain HMAC + LGPD compliance. Sem essa story, OCR/PARSING/EXPORT (P1+) ficam tecnicamente bloqueadas para inferência.

---

## 1. Sumário

Story foundation Sprint 04 P0 — implementa o ciclo completo de gestão BYOK (Bring Your Own Key) Anthropic conforme ADR-014 + FR-API-KEY-01..04. Foundation entregue por SP04-AUTH-01 já coleta `anthropic_api_key` no wizard step2 com validação via ping `GET https://api.anthropic.com/v1/models` (`OnboardingStep2Data` em `bloco_auth/onboarding.py`). Esta story fecha o loop entregando 5 capabilities runtime-críticas:

1. **Persistence layer** — tabela `tenant_api_keys` (ADR-014 §Decisão.Componentes 7) com `encrypted_key BYTEA` via `pgcrypto.pgp_sym_encrypt(key, master_key)`, RLS isolation tenant, dual-key state machine `current_key + pending_key` (FR-API-KEY-02 + FR-API-KEY-03)
2. **Runtime injection middleware** — FastAPI dependency `get_anthropic_client(tenant_id)` decrypta + instancia `anthropic.Anthropic(api_key=...)` SDK per-request, cache request-scoped (não cross-request por security), graceful 503 + audit em decryption failures
3. **Lifecycle endpoints** — `POST /api/tenant/byok/rotate` (state machine current→pending overlap 24h, revalida via ping antes de aceitar; FR-API-KEY-03), `POST /api/tenant/byok/revoke` (clear encrypted + tenant.status='suspended_byok' + force re-onboarding step2; FR-API-KEY-04), `GET /api/tenant/byok/status` (current key fingerprint truncated `sk-ant-...XYZ` + last_used_at)
4. **Audit chain integration** — eventos `byok_key_set`/`byok_key_rotated`/`byok_key_revoked`/`byok_key_used` em audit chain HMAC ADR-005 com payload `{tenant_id, user_id, action, key_fingerprint_truncated, timestamp}`. Chave **NUNCA** logada full (sempre truncada `sk-ant-...XYZ` per ADR-014)
5. **LGPD compliance operador** — direito ao esquecimento via `POST /api/tenant/byok/revoke` purge encrypted blob (audit retention permanent per ADR-019); ADR-017 LGPD operador posture preserved

**Foundation impact:** Desbloqueia SP04-OCR-01 (Vision Sonnet 4.6 inference), SP04-DOCTYPE-01 (Strategy doctype dispatcher LLM calls), SP04-PARSING-01 (parser Anthropic 4 personas) — 3 stories Sprint 04 P1 que dependem de inference Anthropic operacional. Sem BYOK lifecycle, todas seriam mock-only ou impossíveis.

**Branch strategy:** `feat/sp04-byok-01` base `main`. Quando SP04-AUTH-01 PR #4 merge para main, rebase trivial onto main (zero conflict expected — extends `bloco_auth`, não modifies estrutura existente).

---

## 2. As a / I want / So that

- **As a** advogado responsável de escritório de advocacia (BYOK tenant)
- **I want** cadastrar minha API key Anthropic encriptada, rotacioná-la sem downtime, e revogá-la quando necessário (suspeita compromisso, troca de conta Anthropic, ou off-boarding)
- **So that** mantenho controle exclusivo do meu billing Anthropic + segurança máxima com encryption at rest + audit completa de uso interno por advogado, sem que Eric (operador SaaS) tenha acesso à minha chave em texto claro nem sofra risco financeiro de tokens

---

## 3. Acceptance Criteria (8 ACs)

### AC-01 — Schema PostgreSQL `tenant_api_keys` (ADR-014 §Decisão.Componentes 7 — Tank-ratified Phase 12.3a)

Migration SQL canônica conforme ADR-014 + ADR-017 RLS pattern + Tank decisões formalizadas (CHECK refinado, partial indexes removidos, enum strict tenants.status, pg_cron rotation auto-complete):

```sql
-- ─── Extensions (Tank decision: pg_cron primary, pgcrypto reuse AUTH-01) ─────
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- já criada em AUTH-01 (idempotent)
CREATE EXTENSION IF NOT EXISTS pg_cron;   -- Tank decision Item 2 — rotation auto-complete

-- ─── Tabela: tenant_api_keys ────────────────────────────────────────────────
CREATE TABLE tenant_api_keys (
  tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  encrypted_key BYTEA,                          -- pgp_sym_encrypt(key, master_key); NULL apenas em status='revoked'
  key_fingerprint VARCHAR(20) NOT NULL,         -- 'sk-ant-...XYZ' truncated (audit/UI; NUNCA full key)
  status VARCHAR(20) NOT NULL DEFAULT 'active', -- enum: active|pending_rotation|revoked
  pending_encrypted_key BYTEA,                  -- dual-key rotation overlap 24h
  pending_fingerprint VARCHAR(20),              -- truncated novo key durante rotation
  rotation_started_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  last_used_at TIMESTAMP WITH TIME ZONE,        -- Tank decision Item 5: inline per-request UPDATE

  -- Tank decision Item 1: 2 constraints separados (clearer audit + force purge invariant)
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

ALTER TABLE tenant_api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY byok_tenant_isolation ON tenant_api_keys
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

-- Tank decision Item 3: partial indexes REMOVIDOS — cardinality 1 row/tenant;
-- PRIMARY KEY index implícito é suficiente para scale MVP (≤500 rows). Reavaliar 5K+ tenants.

-- ─── Tank decision Item 4: enum strict tenants.status (retrofit) ───────────
-- Adiciona 'suspended_byok' (FR-API-KEY-04 revoke flow) + força type safety
-- (typo prevention) com 4 valores enum. ALTER TABLE trivial em <50 rows.
ALTER TABLE tenants
  ADD CONSTRAINT tenant_status_enum CHECK (
    status IN ('active', 'suspended', 'dpa_pending', 'suspended_byok')
  );

-- ─── Rotation auto-complete cron (Tank decision Item 2: pg_cron primary) ────
CREATE OR REPLACE PROCEDURE complete_pending_rotations()
LANGUAGE plpgsql AS $$
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

SELECT cron.schedule(
  'byok-rotation-complete',
  '0 * * * *',  -- hourly
  $$CALL complete_pending_rotations()$$
);
```

**Notas:**
- `tenant_id` PK (Quota Interna pattern ADR-014 — 1 key/escritório)
- `encrypted_key` agora NULLABLE (Tank Item 1 — força revoke purge via constraint `revoked_purge_consistency`)
- 3 CHECK constraints: rotation state + revoked purge + status enum strict (defense-in-depth)
- ON DELETE CASCADE de `tenants` (LGPD purge cascade quando tenant off-boards)
- RLS USING policy idêntico padrão SP04-AUTH-01 (consistent BACKBONE)
- pg_cron job hourly verifica rotations com 24h+ overlap → auto-complete via stored procedure (multi-instance safe)
- Fallback APScheduler se pg_cron unavailable em deployment final (TD-SP04-04 Sprint 06+)

### AC-02 — Encryption at rest pgcrypto AES-256

Implementação `bloco_auth/byok_encryption.py`:

```python
def encrypt_api_key(plain_key: str, master_key: str) -> bytes:
    """pgp_sym_encrypt via PostgreSQL function call (não Python crypto direto)."""
    # SELECT pgp_sym_encrypt($1, $2) AS encrypted -- via SQLAlchemy func.pgp_sym_encrypt
    ...

def decrypt_api_key(encrypted: bytes, master_key: str) -> str:
    """pgp_sym_decrypt via PostgreSQL function call."""
    # SELECT pgp_sym_decrypt($1, $2)::text AS plain -- via SQLAlchemy func.pgp_sym_decrypt
    ...

def truncate_fingerprint(plain_key: str) -> str:
    """Format 'sk-ant-...XYZ' (first 7 + last 3 chars). Para audit/UI."""
    if len(plain_key) < 12:
        raise ValueError("API key too short to fingerprint safely")
    return f"{plain_key[:7]}...{plain_key[-3:]}"
```

**Master key:** lida de env var `MASTER_ENCRYPTION_KEY` (ADR-014 §Decisão.Componentes 3); validation eager via `@lru_cache` no module init; ConfigError eager se env ausente OR < 32 bytes (mesmo pattern SP04-AUTH-01 `bloco_auth/jwt_utils.py`). Filesystem permission 600 em `.env` (NUNCA commitada).

**Tested:** roundtrip insert encrypted via `pgp_sym_encrypt` + select decrypted via `pgp_sym_decrypt` = original plain key (integration test PostgreSQL); fingerprint formato `sk-ant-...XYZ` deterministic.

### AC-03 — Setter `set_api_key` integrado ao `complete_onboarding` (extend SP04-AUTH-01)

Modificação atomic em `bloco_auth/onboarding.py.complete_onboarding()`:

- Atualmente (SP04-AUTH-01 chunk 4): triple insert `tenant + user + dpa_acceptance` em single transaction
- SP04-BYOK-01 extends: **quadruple insert** `tenant + user + dpa_acceptance + tenant_api_keys` (encrypted + fingerprint) em single transaction
- Audit chain event `byok_key_set` com payload `{tenant_id, user_id, action: "set", key_fingerprint, timestamp}` — chave NUNCA logada full

**Tested:** integration test E2E onboarding wizard 4 steps → `tenant_api_keys` row presente com `encrypted_key` ≠ plain + `fingerprint` formato correto + audit event recorded.

### AC-04 — Runtime injection middleware Anthropic SDK

Implementação `bloco_auth/byok_middleware.py`:

```python
from anthropic import Anthropic
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from bloco_auth.byok_encryption import decrypt_api_key
from bloco_auth.middleware import get_current_user  # SP04-AUTH-01 existing
from bloco_auth.models import TenantAPIKey

async def get_anthropic_client(
    current_user: tuple[UUID, UUID] = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> Anthropic:
    """Decrypta api_key do tenant ativo + retorna SDK instance per-request.

    Cache: request-scoped via FastAPI Depends caching (não cross-request).
    Failure mode: 503 Service Unavailable + audit byok_decryption_failed se decrypt fails.
    """
    tenant_id, user_id = current_user

    # RLS aplicado automaticamente via SET LOCAL app.tenant_id (middleware AUTH-01)
    result = await db_session.execute(
        select(TenantAPIKey).where(TenantAPIKey.tenant_id == tenant_id)
    )
    key_row = result.scalar_one_or_none()

    if key_row is None or key_row.status == "revoked":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="BYOK não configurado ou revogado — re-onboarding step2 necessário",
        )

    try:
        plain_key = await decrypt_api_key_async(key_row.encrypted_key, db_session)
    except Exception as exc:
        await _audit_byok(db_session, tenant_id, user_id, "byok_decryption_failed", key_row.key_fingerprint)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BYOK decryption failure — operator alert triggered",
        ) from exc

    # Update last_used_at (background task — não bloqueia request)
    await db_session.execute(
        update(TenantAPIKey)
        .where(TenantAPIKey.tenant_id == tenant_id)
        .values(last_used_at=datetime.now(timezone.utc))
    )

    return Anthropic(api_key=plain_key)
```

**Tested:** integration test mock `anthropic.Anthropic` SDK + verify decrypted key injected matches encrypted/decrypt roundtrip; failure path 503 + audit event.

### AC-05 — Endpoint `POST /api/tenant/byok/rotate` (FR-API-KEY-03)

Dual-key rotation 24h overlap window (ADR-014 §Decisão.Componentes 5):

```
Request body: {"new_api_key": "sk-ant-..."}

Flow:
  1. Validate via ping_anthropic_api(new_api_key) (reuse SP04-AUTH-01 helper)
  2. If status == "active" (não rotation in-flight):
     a. UPDATE tenant_api_keys SET
          status = 'pending_rotation',
          pending_encrypted_key = pgp_sym_encrypt(new_api_key, master_key),
          pending_fingerprint = truncate(new_api_key),
          rotation_started_at = NOW()
     b. Audit event byok_key_rotation_started (key_fingerprint old + new)
     c. Response 202 Accepted: {"rotation_started_at": ..., "complete_at": +24h}
  3. If status == "pending_rotation" AND rotation_started_at + 24h ≤ NOW():
     a. Atomic UPDATE: encrypted_key = pending_encrypted_key, fingerprint = pending_fingerprint,
        status = 'active', pending_* = NULL, rotation_started_at = NULL
     b. Audit event byok_key_rotation_completed
     c. Response 200 OK: {"new_fingerprint": ...}
  4. If status == "pending_rotation" AND < 24h: 409 Conflict "Rotation in progress, complete_at: ..."

Background job (cron OR APScheduler):
  - Every 1h: scan tenants with status='pending_rotation' AND rotation_started_at + 24h ≤ NOW()
  - Auto-complete rotation (atomic UPDATE) + audit event
```

**Tested:** integration test rotation start (status pending) → wait 24h simulado (mock datetime) → auto-complete (status active + new fingerprint); concurrent rotation 409 conflict.

### AC-06 — Endpoint `POST /api/tenant/byok/revoke` (FR-API-KEY-04)

Self-service revocation:

```
Request body: {"reason": "suspected_compromise" | "off_boarding" | "other"}

Flow:
  1. UPDATE tenant_api_keys SET
       encrypted_key = NULL,            -- LGPD purge
       pending_encrypted_key = NULL,
       status = 'revoked',
       rotation_started_at = NULL
     WHERE tenant_id = current_user.tenant_id
  2. UPDATE tenants SET status = 'suspended_byok' (force re-onboarding step2)
  3. Audit event byok_key_revoked with payload {tenant_id, user_id, reason, timestamp, key_fingerprint_truncated}
  4. Response 204 No Content

Subsequent inference attempts:
  - get_anthropic_client → 403 Forbidden "BYOK não configurado ou revogado"
  - User must re-execute onboarding step2 (re-validar nova api_key) para reativar tenant
```

**Tested:** integration test revoke → status='revoked' + tenant.status='suspended_byok' + subsequent get_anthropic_client retorna 403 + audit event recorded.

### AC-07 — Endpoint `GET /api/tenant/byok/status` (Settings UI consumer)

Read-only status para Settings panel:

```
Response 200 OK:
{
  "status": "active" | "pending_rotation" | "revoked",
  "key_fingerprint": "sk-ant-...XYZ",
  "created_at": "2026-05-08T...",
  "last_used_at": "2026-05-08T..." | null,
  "rotation": {                            // null se não em rotation
    "pending_fingerprint": "sk-ant-...ABC",
    "started_at": "2026-05-08T...",
    "complete_at": "2026-05-09T..."
  } | null
}
```

**Tested:** integration test status active/pending/revoked + valida fingerprint truncated (NUNCA full key).

### AC-08 — Test coverage ≥ 80% + audit chain integrity

**Unit tests (Pytest):**
- `test_byok_encryption.py` — encrypt/decrypt roundtrip + fingerprint truncation + master_key validation
- `test_byok_state_machine.py` — rotation state transitions (active → pending_rotation → active) + concurrent rotation conflict

**Integration tests (Pytest + PostgreSQL `_REQUIRES_POSTGRES`):**
- `test_byok_lifecycle_e2e.py` — onboarding step2 → tenant_api_keys row present → first inference call decrypta + injeta SDK → rotate → revoke → re-onboarding cycle
- `test_byok_rls_isolation.py` — tenant A não acessa tenant_api_keys de tenant B (mesmo com BYPASSRLS misuse → policy bloqueia)
- `test_byok_audit_chain.py` — eventos set/used/rotated/revoked com tenant_id payload + integrity HMAC preservada (ADR-005) + key NUNCA full em audit log

**Coverage targets:**
- Unit `bloco_auth/byok_*.py`: 90%+ (foundation pure)
- Integration: 80%+ (RLS + state machine critical paths)
- Overall: ≥ 80% (NFR-PERF-01)

---

## 4. File List (Neo Phase 12.2+ implementation)

### Novos arquivos

- `bloco_auth/byok_encryption.py` — pgcrypto wrappers (encrypt/decrypt/truncate fingerprint) + master_key validation eager `@lru_cache`
- `bloco_auth/byok_middleware.py` — FastAPI Depends `get_anthropic_client` runtime injection + cache request-scoped + graceful 503
- `bloco_auth/byok_lifecycle.py` — state machine rotation (start_rotation, complete_rotation, revoke) + APScheduler/cron auto-complete 24h overlap
- `bloco_auth/byok_api.py` — APIRouter `/api/tenant/byok` 3 endpoints (rotate, revoke, status)
- `bloco_database/migrations/sp04_002_byok_keys.sql` — tabela `tenant_api_keys` + RLS policies + indexes + CHECK constraint rotation_consistency
- `tests/unit/test_byok_encryption.py` (~10 tests)
- `tests/unit/test_byok_state_machine.py` (~8 tests)
- `tests/integration/test_byok_lifecycle_e2e.py` (~6 tests `_REQUIRES_POSTGRES`)
- `tests/integration/test_byok_rls_isolation.py` (~4 tests `_REQUIRES_POSTGRES`)
- `tests/integration/test_byok_audit_chain.py` (~5 tests `_REQUIRES_POSTGRES`)

### Arquivos modificados

- `bloco_auth/onboarding.py` — extend `complete_onboarding()` para quadruple insert (tenant + user + dpa_acceptance + **tenant_api_keys encrypted**); `OnboardingStep2Data.anthropic_api_key` flow continua mas chunk 4 SP04-AUTH-01 já valida via ping
- `bloco_auth/api.py` — register byok_api router
- `bloco_auth/models.py` — adicionar `TenantAPIKey` SQLAlchemy model (mirror migration SQL)
- `bloco_interface/web/app.py` — register `bloco_auth/byok_api.py` router
- `pyproject.toml` — adicionar `anthropic>=0.40.0` (Anthropic SDK Python oficial; verify version atual no pre-implement). **Tank decision Item 2:** `apscheduler` REMOVIDO (pg_cron extension PostgreSQL é primary rotation auto-complete arch); APScheduler reservado fallback Sprint 06+ TD-SP04-04 se pg_cron unavailable em deployment final
- `.env.example` — adicionar `MASTER_ENCRYPTION_KEY=` placeholder (32+ bytes; gerar com `openssl rand -hex 32`)

### Pendências cross-domain (não implementação Neo)

- **Sati panel `Configurações > BYOK` UI** (FR-API-KEY-01 settings tela) — pre-flight Sati opcional; Neo pode prosseguir com endpoints API + Settings UI brief separado se necessário
- **Operator runbook `MASTER_ENCRYPTION_KEY` rotation** (Sprint 05+ — não bloqueia esta story; ADR-014 documenta dual-key support window pattern)

---

## 5. Pre-flight consultation

### @data-engineer Tank (schema decision — RATIFY pre-implement)

**Status:** Schema canônico já documentado em **ADR-014 §Decisão.Componentes 7** (tabela `tenant_api_keys`). River segue ADR sem desvio.

**Decisões River vs ADR-014:**
- ✅ Tabela separada `tenant_api_keys` (não coluna em `tenants`) — ADR-014 confirmado; River adiciona campos `pending_*` + `rotation_started_at` para dual-key state machine FR-API-KEY-03 (ADR-014 §Decisão.Componentes 5)
- ✅ `pgcrypto.pgp_sym_encrypt` MVP (não AWS KMS) — ADR-014 §Decisão.Componentes 2 confirmado
- ✅ ON DELETE CASCADE de `tenants` — alinhado com SP04-AUTH-01 pattern (LGPD purge cascade)
- ⚠ **Pre-implement Tank ratifica:**
  - Background job rotation auto-complete 24h: APScheduler vs pg_cron extension vs FastAPI BackgroundTasks (Tank decide arquitetura ops)
  - Index seletivo `WHERE status != 'revoked'` partial index — Tank confirma performance impact
  - CHECK constraint `rotation_consistency` (River drafted — Tank revisa para edge cases)

### @architect Aria (ADR-020 BYOK Key Lifecycle — NÃO necessário)

**Status:** ADR-014 cobre lifecycle completo (encryption + dual-key rotation + revoke + audit). River avaliou gap: NENHUM identificado. Aria pre-flight pode ser **skipped**.

**Justificativa:** ADR-014 §Decisão.Componentes 5 documenta dual-key state machine 24h overlap explicitamente; ADR-014 §Razão documenta `MASTER_ENCRYPTION_KEY` rotation como debt explícito (não bloqueia esta story). Não há nova decisão arquitetural necessária.

### @ux-design-expert Sati (panel `Configurações > BYOK` — OPCIONAL)

**Status:** UX spec atual cobre wizard step2 (SP04-AUTH-01 entregue). FR-API-KEY-01 menciona "Tela de Settings escritório" mas wireframe específico Settings panel não foi entregue UX spec v2.0.0-DRAFT.

**Sati pre-flight pode ser:**
- **OPCIONAL pre-implement:** Neo entrega endpoints API + Settings UI placeholder; Sati wireframe Configurações>BYOK em story separada (parte do SP04-DASH-01 Settings ecosystem)
- **MANDATORY se Eric prefere:** Sati brief wireframe Configurações>BYOK panel ANTES Neo `*develop`; adiciona ~1 day pre-implement

**River recomenda:** OPCIONAL — endpoints API são MVP-críticos (desbloqueia OCR/PARSING/EXPORT runtime); Settings UI pode iterar paralelo SP04-DASH-01.

---

### Tank ratify decisions (2026-05-08 — Phase 12.3a)

> **Authority:** @data-engineer Tank — schema/arquitetura DB decisões formalizadas pre-Neo chunk 2 DB foundation. Decisões abaixo são **vinculantes** para Neo durante chunks 1-8 implementation.

**Pre-leitura completa:** Tank validou story Section 1-4 + ADR-014 §Decisão.Componentes 7 + ADR-017 BACKBONE + migration AUTH-01 `sp04_001_auth_multitenant.sql` + deployment context (PostgreSQL 16 self-hosted/managed via DATABASE_URL `postgresql+asyncpg://...localhost:5432/`; sem Cloudflare D1/Workers runtime — wrangler.toml/jsonc ausente confirma).

**Schema canônico ADR-014 §Decisão.Componentes 7:** ✅ Tank ratifica River alignment sem desvio (tabela `tenant_api_keys` com `tenant_id PK`, encryption pgcrypto MVP, ON DELETE CASCADE LGPD).

**5 itens MANDATORY ratificados:**

#### Item 1 — CHECK constraint refinement

**Decisão Tank:** **Refinar 2 constraints separados** (em vez de single combined River draft):

```sql
CONSTRAINT rotation_state_consistency CHECK (
  (status = 'pending_rotation'
    AND pending_encrypted_key IS NOT NULL
    AND pending_fingerprint IS NOT NULL  -- Tank addition (River omitiu)
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
```

**Justificativa:**
- 2 invariantes separados (rotation state + revoked purge) são mais auditáveis que combined boolean
- `pending_fingerprint NOT NULL` durante rotation força UI/audit consistency (River draft omitiu)
- `revoked_purge_consistency` força LGPD purge invariante (encrypted_key=NULL apenas em revoked)
- `byok_status_enum` é defense-in-depth (mesmo padrão Item 4 tenants.status)
- Clock skew em `rotation_started_at` futuro é tolerado (DBA monitora separado — não é responsabilidade da CHECK)
- `encrypted_key` agora NULLABLE (era NOT NULL River draft) — força purge via constraint, não NOT NULL violation

**Impacto AC-01 SQL migration:** atualizado em Section 3 acima.

#### Item 2 — Rotation auto-complete arquitetura

**Decisão Tank:** **pg_cron primary** + APScheduler fallback Sprint 06+ TD-SP04-04.

**Justificativa:**
- Deployment context é PostgreSQL 16 self-hosted/managed (não Cloudflare D1) — `pg_cron` IS supported (mesmo princípio que pgcrypto AUTH-01)
- pg_cron é multi-instance safe (DB-side execution; reliable mesmo com Python down)
- Stored procedure SQL nativo elimina deps Python adicional (`apscheduler` removido pyproject.toml)
- Pattern alinhado com pgcrypto AUTH-01 (extensions PostgreSQL como first-class)
- Job hourly (`'0 * * * *'`) verifica rotations com 24h+ overlap → auto-complete atomic UPDATE

**Stored procedure + cron schedule:**

```sql
CREATE OR REPLACE PROCEDURE complete_pending_rotations()
LANGUAGE plpgsql AS $$
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

SELECT cron.schedule('byok-rotation-complete', '0 * * * *', $$CALL complete_pending_rotations()$$);
```

**Fallback APScheduler:** Se deployment final (managed Postgres provider) NÃO suportar pg_cron, Operator runbook ops Sprint 06+ adiciona APScheduler async via FastAPI lifespan (TD-SP04-04). Por padrão Sprint 04 = pg_cron; mudança requer ADR-020 BYOK Lifecycle update.

**Impacto:**
- `pyproject.toml`: REMOVER `apscheduler>=3.10.0` (não-necessário)
- Migration `sp04_002_byok_keys.sql`: ADICIONAR `CREATE EXTENSION IF NOT EXISTS pg_cron` + procedure + cron.schedule (atualizado AC-01 SQL acima)
- Audit chain integration (chunk 7): event `byok_key_rotation_completed` precisa ser emitido pela stored procedure (Tank decide se trigger ON UPDATE OR audit dentro proc)

#### Item 3 — Partial indexes performance

**Decisão Tank:** **DROP ambos partial indexes** (manter apenas implicit PRIMARY KEY index em `tenant_id`).

**Justificativa:**
- Cardinality MVP: 1 row per tenant (Quota Interna pattern) → 50-500 rows total (Sprint 04 scale)
- Sequential scan + filter em <500 rows é microseconds (PostgreSQL planner choosing seq scan over index é correto em low cardinality)
- Partial indexes adicionam write overhead sem read benefit em scale MVP
- PRIMARY KEY index implícito (`tenant_id`) já cobre lookups primary
- Background job `complete_pending_rotations()` faz table scan trivial em <500 rows

**Roadmap:** Quando MVP escalar para 5K+ tenants (Sprint 07+ estimativa), reavaliar com EXPLAIN ANALYZE. Tracked como **TD-SP04-04** TECH-DEBT.md.

**Impacto migration:**
- REMOVER `CREATE INDEX idx_byok_status WHERE status != 'revoked';`
- REMOVER `CREATE INDEX idx_byok_rotation WHERE status = 'pending_rotation';`
- (atualizado AC-01 SQL acima — indexes não-presentes)

#### Item 4 — `tenants.status` enum strict

**Decisão Tank:** **Opção B — adicionar CHECK constraint enum strict** em chunk 2 migration.

**Justificativa:**
- 4 valores distintos (`active`, `suspended`, `dpa_pending`, `suspended_byok`) é ponto inflexão typo (3 era tolerável; 4+ valoriza-se type safety)
- ALTER TABLE ADD CONSTRAINT é trivial em <50 rows (~10ms execution)
- Captura typos imediato em testes (`'suspendend'` rejeita migration time)
- Migration AUTH-01 linha 35 explicitamente deferiu para "Sprint 05+ se proliferação justificar" — Sprint 04 BYOK é o trigger
- Future-proof: futuras stories adicionam status via ALTER TABLE DROP CONSTRAINT + ADD CONSTRAINT (audit explícito)

**ALTER TABLE snippet** (incluído em migration `sp04_002_byok_keys.sql`):

```sql
ALTER TABLE tenants
  ADD CONSTRAINT tenant_status_enum CHECK (
    status IN ('active', 'suspended', 'dpa_pending', 'suspended_byok')
  );
```

**Impacto:** Zero migration risk (tabela com poucos rows). Retrofit alinha governance enum strict para todas as stories Sprint 04+.

#### Item 5 — `last_used_at` update strategy

**Decisão Tank:** **Opção A — Inline per-request UPDATE** (River draft atual).

**Justificativa:**
- Volume MVP (Sprint 04): 50 tenants × 10 análises/dia = 500 inference calls/day = **0.005 writes/sec average**
- PostgreSQL row-level locking nativo handle write contention trivialmente neste volume
- Eventual consistency (Opção B background batch) introduz complexidade sem benefit em scale MVP
- Promoção para Opção B é trivial pós-Sprint quando scale exceed 5K writes/day (= 500 tenants × 100 análises/dia escala 10x)

**Threshold promotion:** **50K writes/day** = trigger Opção B (background batch APScheduler async OR pg_cron dedicated procedure). Tracked como **TD-SP04-05** TECH-DEBT.md Sprint 06+ se scale exceed.

**Implementação refinement (Neo aplicar chunk 5):**
- AC-04 código `byok_middleware.py.get_anthropic_client()`: REMOVER comentário "background task — não bloqueia request" (inconsistência draft) — substituir por `# inline UPDATE per request (Tank decision Phase 12.3a Item 5; volume MVP 0.005 writes/sec justifica simplicidade)`
- Implementação inline `await db_session.execute(update(...))` mantida (River draft já correto)

---

### Tank close-out

✅ **5 itens ratificados:** CHECK refinado (3 constraints) + pg_cron primary + indexes drop + enum strict + last_used_at inline
✅ **Schema ADR-014 alignment** confirmado sem desvio
✅ **Decisões vinculantes** para Neo chunks 1-8 implementation
✅ **TECH-DEBT.md Sprint 06+** flagged: TD-SP04-04 (partial indexes reavaliar 5K+ tenants), TD-SP04-05 (last_used_at promotion 50K writes/day), TD-SP04-06 (APScheduler fallback se pg_cron unavailable)
⏳ **Próximo:** Neo *develop chunks 1-8 com Tank decisions aplicadas

— Tank, carregando os dados 🗄️

---

## 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Decryption failure middleware → tenant sem inferência funcional | LOW | HIGH (tenant blocked) | Graceful 503 + audit `byok_decryption_failed` + alert operacional + revoke flow available |
| `MASTER_ENCRYPTION_KEY` rotation breaking change todos encrypted blobs | LOW | CRITICAL | Dual-key support window (decrypt com old_key fallback + re-encrypt com new_key migration script) — ADR-014 documenta debt; Sprint 05+ runbook |
| Anthropic API deprecation Sonnet 4.6 / Haiku 4.5 / API v1/models endpoint | LOW | HIGH (all tenants) | Ping validation periódico (cron daily) + alert tenants se ping fails + dashboard health check (Sprint 05+) |
| Race condition rotation start vs concurrent set | LOW | MEDIUM (data inconsistency) | CHECK constraint `rotation_consistency` enforces atomic state; integration test concurrent 409 |
| Audit chain swallow exceptions silencia BYOK events (CC.39 hardening pattern) | MEDIUM | MEDIUM (LGPD audit gap) | Pattern alinhado SP04-AUTH-01 TD-SP04-03 — adicionar structlog logger Sprint 05+ TECH-DEBT |
| Anthropic SDK version drift breaking changes | LOW | MEDIUM (runtime fail) | Pin SDK version em pyproject.toml + Dependabot Sprint 05+ |
| LGPD operador posture — Eric acessa key plain via decryption se compromised | LOW | HIGH (compliance) | `MASTER_ENCRYPTION_KEY` em filesystem permission 600 + Eric não logged em servidor produção rotineiro; ADR-017 LGPD operador documentado |

---

## 7. Implementation Plan (Path B chunks sugeridos — Neo refina)

Pattern Path B SP04-AUTH-01 adaptado:

1. **Chunk 1** — Setup environment: `pyproject.toml` deps (`anthropic>=0.40.0`, `apscheduler>=3.10.0`); `.env.example` `MASTER_ENCRYPTION_KEY`; verificar `bloco_auth/byok_*.py` package skeleton
2. **Chunk 2** — Database foundation: migration `sp04_002_byok_keys.sql` (tabela + RLS + indexes + CHECK constraint); SQLAlchemy `TenantAPIKey` model
3. **Chunk 3** — Encryption foundation: `byok_encryption.py` (encrypt/decrypt wrappers via pgcrypto + master_key eager validation + fingerprint truncate); 10 unit tests
4. **Chunk 4** — Onboarding integration: extend `complete_onboarding()` para quadruple insert atomic; audit event `byok_key_set`; integration test E2E onboarding chunk 4 SP04-AUTH-01 + tenant_api_keys row
5. **Chunk 5** — Runtime injection: `byok_middleware.py` FastAPI Depends `get_anthropic_client` + cache request-scoped + graceful 503; integration test mock SDK
6. **Chunk 6** — Lifecycle endpoints: `byok_api.py` 3 endpoints (rotate state machine + revoke + status) + APScheduler/pg_cron rotation auto-complete 24h
7. **Chunk 7** — RLS isolation + audit chain: integration tests RLS cross-tenant + audit chain HMAC eventos completos (set/used/rotated/revoked); coverage AC-08 verify
8. **Chunk 8** — Story closure: DoD WAIVED format honest (similar AUTH-01) + Final File List Consolidado + status InReview + handoff @qa Oracle qa-gate G5

**Estimativa River:** 3-5 days similar SP04-AUTH-01 — complexity equivalente (8 chunks Path B). Neo ajusta conforme pre-implement consultation Tank/Sati.

**Branch creation:** `feat/sp04-byok-01` base `main` — criada por Operator OR Neo no início chunk 1. Quando SP04-AUTH-01 PR #4 merge, rebase trivial.

---

## 8. Definition of Done (template — Neo populates implementation)

A definir empiricamente durante implementation Phase 12.2+ chunks 1-8. Template proposto:

### Esperado VERIFIED (se chain Path B segue SP04-AUTH-01 padrão)

- [ ] All 8 ACs implementadas + verified empíricamente
- [ ] Migration SQL aplicada (PostgreSQL `sp04_002_byok_keys.sql`) + RLS policies funcionais
- [ ] Unit tests pass (~18 tests bloco_auth/byok_*: encryption + state machine)
- [ ] Story file File List Section 4 atualizada Neo Final File List Consolidado
- [ ] Dev Agent Record Section 10 chunks 1-8 entries
- [ ] Conventional commits chunks 1-8 + Story ID reference em cada
- [ ] Handoff @qa Oracle qa-gate G5 emitted

### Possível DEFERRED com WAIVED format (rule quality-gate-enforcement.md MANDATORY — 5 fields per item)

Conforme padrão SP04-AUTH-01:
- Integration tests `_REQUIRES_POSTGRES` skipped sem DB local (Docker daemon offline padrão sessão) → qa-gate G5 retest
- Coverage condicional sem DB rodando → AC-08 condicional documentado em pyproject.toml comment
- CodeRabbit DEFERRED (CLI ausente WSL bash padrão) → self-critique manual fallback
- Sati panel `Configurações > BYOK` UI deferred → SP04-DASH-01 Settings ecosystem
- `MASTER_ENCRYPTION_KEY` rotation runbook → Sprint 05+ TECH-DEBT
- `last_used_at` background update strategy (per-request OR batch) → Tank pre-implement decide

---

## 9. QA Validation (@po Keymaker — *validate-story-draft G3)

### Verdict @po Keymaker (2026-05-08)

**Verdict:** ✅ **GO** | **Score: 10/10** | **Status:** Draft → **Ready**

> Story tem qualidade técnica sólida, paridade estrutural completa com SP04-AUTH-01 (template validado), frontmatter completo, ACs testáveis com critérios "Tested:" explícitos por AC, pre-flight consultation com justificativas explícitas, risk assessment denso (7 risks > mínimo 3), implementation plan 8 chunks Path B alinhado com padrão validado AUTH-01. Concerns River flagged são todos aceitáveis pós-Ready (deferred para fase pre-implementation OR durante chunks).

### 10-point PO Master Checklist (G3)

| # | Ponto | Score | Evidência |
|---|-------|-------|-----------|
| 1 | Frontmatter completo (16+ campos) | ✅ 1/1 | type/id/title/status/epic/project/sprint/phase/priority/estimated_days/agent/branch/dependencies(5)/source_frs(4)/cross_references(5)/tags(9) — paridade SP04-AUTH-01 |
| 2 | Sumário Section 1 claro | ✅ 1/1 | Contexto Cloud SaaS BYOK + 5 deliverables numerados explícitos + foundation impact (3 stories desbloqueadas: OCR/DOCTYPE/PARSING) + branch strategy paralelo |
| 3 | As a / I want / So that Section 2 | ✅ 1/1 | Formato correto (advogado responsável / cadastrar+rotacionar+revogar / controle billing + segurança + audit) |
| 4 | ACs estruturadas Section 3 (testable + 5+) | ✅ 1/1 | 8 ACs (excede mínimo 5) — cada uma com sub-section "Tested:" explícita + SQL/code blocks específicos por AC |
| 5 | File List Section 4 pre-implementation contract | ✅ 1/1 | 5 novos código + 5 test files + 5 modificados + `.env.example` + 2 pendências cross-domain (Sati UI + Operator runbook) explícitas |
| 6 | Pre-flight consultation Section 5 | ✅ 1/1 | Tank ratify (3 itens específicos: rotation arch + index + CHECK edges) + Aria skip (ADR-020 redundante justificado) + Sati OPCIONAL (endpoint-first justificado) |
| 7 | Risk Assessment Section 6 (3+ risks com P/I/M) | ✅ 1/1 | 7 risks tabelados (decryption + master_key rotation + Anthropic deprecation + race rotation + audit swallow + SDK drift + LGPD operador) com Probability/Impact/Mitigation completos |
| 8 | Implementation Plan Section 7 chunks | ✅ 1/1 | 8 chunks Path B detalhados (similar AUTH-01 pattern validado) + estimativa 3-5 days + branch creation timing |
| 9 | Cross-references rastreáveis | ✅ 1/1 | PRD lines 89-94 + 4 ADRs (014/017/019/005) + UX spec + story predecessor SP04-AUTH-01 + Smith F-014 |
| 10 | Frontmatter dependencies + source_frs canônicos | ✅ 1/1 | 5 dependencies (SP04-AUTH-01 + 4 ADRs) + 4 source_frs (FR-API-KEY-01..04) — links rastreáveis PRD canônico |
| **TOTAL** | | **10/10** | **GO threshold ≥ 7/10 — exceeded by 3 pontos** |

### Concerns River flagged — Keymaker decisão

| Concern River | Decisão Keymaker | Justificativa |
|---|---|---|
| **DoD Section 8 template-only (Neo populates)** | ✅ ACEITÁVEL | Padrão SP04-AUTH-01 validado (DoD populated durante chunks 1-8 implementation com WAIVED format honest); template explícito Section 8 + lista de DEFERRED candidates já documentada antecipa quality gate Oracle G5 |
| **AC-01 CHECK constraint complexo — Tank ratify deferred** | ✅ ACEITÁVEL | River documentou alignment ADR-014 + 3 pontos específicos Tank ratifica pre-implement (rotation arquitetura + partial index + CHECK edge cases); consultation deferred move para fase pre-Neo *develop não bloqueia Ready transition; Tank Skill consultation é MANDATORY antes Neo chunk 2 (DB foundation) — handoff Keymaker → Neo deve incluir esse requirement |
| **Branch strategy paralelo (feat/sp04-byok-01 base main)** | ✅ ACEITÁVEL | Eric autorização explícita Opção 3 (Sprint 04 paralelo) via "Avance pelo recomendado"; branches isolados são pattern padrão git-workflow.md feature; rebase trivial pós AUTH-01 merge |

### Concerns adicionais Keymaker (não-bloqueantes — flagged para Neo/Tank)

| # | Concern | Severidade | Recomendação |
|---|---------|-----------|--------------|
| K-01 | **AC-04 `last_used_at` update strategy** | LOW | Section 8 DoD lista `last_used_at` background update strategy como Tank pre-implement decision. Keymaker confirma: comentário código AC-04 diz "background task" mas implementação inline (await db_session.execute). Tank decide per-request inline OR background batch (APScheduler) pre-implement. NÃO bloqueia Ready |
| K-02 | **AC-06 revoke: tenant.status='suspended_byok' novo enum** | LOW | Migration SP04-AUTH-01 chunk 2 definiu `tenants.status VARCHAR(20) DEFAULT 'active'` sem CHECK constraint enum strict. Adicionar 'suspended_byok' é sem-migration (nullable VARCHAR aceita). Neo/Tank ratifica pre-implement se vale CHECK constraint enum strict para prevenir typo OR mantém VARCHAR free para flexibility |
| K-03 | **AC-08 Coverage AC-08 condicional** | LOW | Padrão SP04-AUTH-01 já aceito (52% sem DB; 90%+ módulos puros). DoD Section 8 lista DEFERRED candidates explicitamente — Oracle qa-gate G5 endereça com BYPASSRLS role + DB rodando. Não-bloqueante Ready |

### Próximo step

**Recomendação Keymaker:** Skill `LMAS:agents:dev` (@dev Neo) consume + execute pre-implement Tank Skill consultation MANDATORY (`LMAS:agents:data-engineer`) antes chunk 2 DB foundation → Neo `*develop` chunks 1-8 Path B (similar SP04-AUTH-01 ritmo + estimativa 3-5 days).

**Branch creation:** Neo (OR Operator) cria `feat/sp04-byok-01` base `main` no início chunk 1. Eric autorização paralelo explícita.

**Cadeia próxima Skill:** Neo *develop → Oracle qa-gate G5 → Keymaker close-story → Operator push+PR Sprint 04 PR #5 (similar Path B AUTH-01).

— Keymaker, equilibrando prioridades 🎯

---

## 10. Dev Agent Record (vazio — preenchido @dev Neo durante implement)

> @dev Neo `*develop SP04-BYOK-01` — chunks 1-8 entries preencham aqui durante Phase 12.2+ implementation.

---

## 11. QA Validation post-implementation (vazio — preenchido @qa Oracle qa-gate G5)

> @qa Oracle `*review SP04-BYOK-01` qa-gate G5 — adversarial review verdict + findings preenchem aqui pós-implementation.

---

## 12. Change Log

| Data | Author | Change |
|------|--------|--------|
| 2026-05-08 | @sm River | Story criada Draft Phase 12.1 — BYOK Anthropic key lifecycle. Foundation Sprint 04 P0 segunda story (após SP04-AUTH-01 done). Pre-leitura completa: PRD v2.0.0-DRAFT FR-API-KEY-01..04 + ADR-014 schema canônico + ADR-017 RLS BACKBONE + ADR-019 DPA pattern + bloco_auth/onboarding.py existente. 8 ACs estruturadas (schema migration + encryption + onboarding integration + runtime injection middleware + rotate dual-key 24h + revoke purge + status read-only + tests coverage). Schema decision Tank ratify pre-implement: River segue ADR-014 §Decisão.Componentes 7 sem desvio. Aria ADR-020 NÃO necessário (ADR-014 cobre lifecycle). Sati panel OPCIONAL pre-implement (endpoints API são MVP-críticos; Settings UI pode iterar paralelo SP04-DASH-01). Risk assessment 7 risks documentados. Implementation Plan 8 chunks Path B sugeridos (similar SP04-AUTH-01 estrutura). Branch sugerido feat/sp04-byok-01 base main (rebase trivial pós SP04-AUTH-01 merge). Estimativa 3-5 days. Cross-references: PRD Section BYOK lines 89-94 + ADRs 014/017/019/005 + smith-finding F-014 endereçado. Próxima Skill: LMAS:agents:po (@po Keymaker *validate-story-draft G3 10-point checklist). |
| 2026-05-08 | @po Keymaker | Phase 12.2 — *validate-story-draft G3 verdict ✅ GO score 10/10 executado: status frontmatter Draft → Ready; Section 9 QA Validation preenchida com 10-point checklist completo (todos PASS — paridade SP04-AUTH-01 + frontmatter completo + ACs testáveis com critérios "Tested:" explícitos + pre-flight Section 5 com justificativas + 7 risks tabelados + 8 chunks Path B + cross-references rastreáveis); concerns River flagged 3 itens TODOS aceitáveis pós-Ready (DoD template Neo populates é padrão validado AUTH-01; Tank ratify deferred move para pre-Neo *develop chunk 2 mas é MANDATORY no handoff Neo; branch paralelo Eric autorizou Opção 3); 3 concerns adicionais Keymaker LOW non-bloqueantes flagged Neo/Tank pre-implement (K-01 last_used_at strategy, K-02 tenant.status enum suspended_byok, K-03 coverage AC-08 condicional). Próximo step: Skill LMAS:agents:dev (@dev Neo) consume + Tank Skill consultation MANDATORY antes chunk 2 → Neo *develop chunks 1-8 Path B (3-5 days similar AUTH-01). Conventional commit `docs(governance): validate-story-draft SP04-BYOK-01 — verdict GO score 10/10 [Story SP04-BYOK-01]`. |
| 2026-05-08 | @data-engineer Tank | Phase 12.3a — pre-implement ratify 5 itens schema/arquitetura executado. Pre-leitura: story Section 1-4 + ADR-014 §Decisão.Componentes 7 + ADR-017 BACKBONE + migration sp04_001_auth_multitenant.sql + deployment context (PostgreSQL 16 self-hosted/managed; sem Cloudflare D1/Workers — wrangler.toml/jsonc ausente confirma). 5 decisões formalizadas: (1) CHECK refinado em 3 constraints separados — `rotation_state_consistency` com `pending_fingerprint NOT NULL` exigido (River omitiu) + `revoked_purge_consistency` força LGPD purge invariante + `byok_status_enum` strict; encrypted_key agora NULLABLE (forçado purge via constraint, não NOT NULL); (2) Rotation auto-complete = pg_cron primary com stored procedure `complete_pending_rotations()` + cron.schedule hourly; APScheduler removido pyproject.toml (fallback Sprint 06+ TD-SP04-04 se pg_cron unavailable); (3) Partial indexes DROP ambos — cardinality 1 row/tenant + scale MVP <500 rows justifica seq scan; PRIMARY KEY index implícito suficiente; reavaliar 5K+ tenants TD-SP04-04; (4) tenants.status enum strict ADD CONSTRAINT CHECK (active|suspended|dpa_pending|suspended_byok) — 4 valores é ponto inflexão typo prevention; ALTER TABLE trivial <50 rows; (5) last_used_at = inline per-request UPDATE — volume MVP 0.005 writes/sec justifica simplicidade; promotion threshold 50K writes/day TD-SP04-05. Decisões vinculantes Neo chunks 1-8. Schema ADR-014 alignment confirmado sem desvio. Section 5 nova subsection "Tank ratify decisions" + AC-01 SQL refinado (3 CHECK constraints + ALTER TABLE tenants enum + pg_cron procedure + indexes removidos). Section 4 File List atualizada (apscheduler removido). Próximo step Skill `LMAS:agents:dev` (@dev Neo) consume + chunks 1-8 Path B com decisões aplicadas. Conventional commit `docs(governance): Tank ratify pre-implement SP04-BYOK-01 — 5 itens decisões [Story SP04-BYOK-01]`. |

---

— Tank, carregando os dados 🗄️
