---
type: story
id: "SP04-AUTH-01"
title: "Multi-tenant authentication + tenant onboarding"
status: Draft
epic: "Sprint 04 Cloud SaaS BYOK"
project: revisor-contratual
sprint: "04"
phase: 7.1
priority: P0
estimated_days: "3-5"
agent: "@dev (Neo)"
branch: "feat/sp04-auth-01 (será criada Phase 7+ pre-implementation)"
created: "2026-05-07"
created_by: "@sm River"
dependencies:
  - "ADR-014 (BYOK Provider Abstraction)"
  - "ADR-017 (Multi-tenant Pool+RLS BACKBONE)"
  - "ADR-019 (DPA Storage Schema)"
source_frs:
  - "FR-AUTH-01 (cadastro escritório)"
  - "FR-AUTH-02 (gestão users internos)"
  - "FR-AUTH-03 (login JWT com tenant_id claim)"
cross_references:
  prd: "governance/prd/prd-v2.0.0-DRAFT.md Section 4 Authentication"
  ux: "governance/ux-spec-v2.0.0-DRAFT.md S2 Onboarding"
  adrs: ["adr-014", "adr-017", "adr-019"]
  smith_findings_addressed: "F-006 (onboarding payment flow), F-008 (login session expiry), F-013 (RLS isolation verification)"
tags:
  - project/revisor-contratual
  - story
  - sprint-04
  - epic-auth
  - foundation
  - p0
  - multi-tenant
---

# SP04-AUTH-01 — Multi-tenant authentication + tenant onboarding

```
[@sm · River (Facilitator)] — Sprint 04 · Phase 7.1 · SP04-AUTH-01 · foundation
SPRINT: 04 · PHASE: 7.1 · DOMÍNIO: software-dev/multi-tenant-auth
```

> **Foundation Sprint 04** — primeira story que destrava 13 outras (todas dependem de tenant_id + user_id auth context). Implementação multi-tenant authentication + onboarding wizard 4 passos + DPA acceptance flow + audit chain HMAC integration.

---

## 1. Sumário

Story foundation Sprint 04 — implementa autenticação multi-tenant cloud SaaS BYOK (cadastro escritório, gestão users internos, login JWT) integrado com onboarding wizard 4 passos (Sati S2 UX) + DPA acceptance flow (ADR-019) + audit chain HMAC (ADR-005 + ADR-017).

**Foundation status:** Bloqueia 13 outras Sprint 04 stories (SP04-LGPD-01 paralelo possível; SP04-BYOK-01..SP04-ADMIN-01 dependem de auth context).

---

## 2. As a / I want / So that

- **As a** advogado responsável de escritório de advocacia brasileiro
- **I want** cadastrar meu escritório como tenant + gerenciar usuários internos
- **So that** posso isolar dados do meu escritório de outros clientes Eric e ter controle granular sobre quem acessa análises

---

## 3. Acceptance Criteria (8 ACs)

### AC-01 — Onboarding wizard 4 passos
Form UI Sati S2 wireframe com 4 steps sequenciais:
- **(a) Dados escritório:** CNPJ (validação dígito verificador) + razão social + advogado responsável + email + senha (bcrypt cost 12)
- **(b) API Key Anthropic:** input + validação ping `POST https://api.anthropic.com/v1/models` (key válida = 200 OK)
- **(c) DPA acceptance:** flow ADR-019 — texto canônico exibido + checkbox "Li e aceito" + `POST /api/tenant/dpa/accept`
- **(d) Tier selection:** Starter/Pro/Enterprise (valores TBD pricing cross-domain — placeholder "R$ TBD")

**Resultado:** Emissão UUID `tenant_id` único + envio email confirmação + redirect S3 dashboard.

### AC-02 — Schema PostgreSQL `tenants`
Conforme ADR-017 BACKBONE pattern:
```sql
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cnpj VARCHAR(14) UNIQUE NOT NULL,
  razao_social TEXT NOT NULL,
  advogado_responsavel TEXT NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active|suspended|dpa_pending
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_self_view ON tenants
  USING (id = current_setting('app.tenant_id')::uuid);

CREATE INDEX idx_tenants_cnpj ON tenants(cnpj);
CREATE INDEX idx_tenants_email ON tenants(email);
```

### AC-03 — Schema PostgreSQL `users`
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,  -- bcrypt cost 12
  nome TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active|suspended
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  CONSTRAINT unique_email_per_tenant UNIQUE(tenant_id, email)
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_tenant_isolation ON users
  USING (tenant_id = current_setting('app.tenant_id')::uuid);

CREATE INDEX idx_users_tenant ON users(tenant_id);
```

### AC-04 — CRUD users dentro tenant
APIs FastAPI tenant-scoped via RLS:
- `POST /api/tenant/users` — criar user (body: email + senha + nome). Retorna user_id. Audit chain event `user_created`.
- `GET /api/tenant/users` — listar users do tenant atual. Tenant-scoped via RLS.
- `PATCH /api/tenant/users/{id}` — update nome/email/status (suspend). Audit chain event `user_updated`.
- `DELETE /api/tenant/users/{id}` — soft-delete (status → `suspended`). Audit chain event `user_suspended`.

### AC-05 — Login email + senha + JWT
`POST /api/auth/login`:
- Body: `{email, senha}`
- Lookup user por email (across all tenants — não tenant-scoped pois session ainda não estabelecida)
- Validate bcrypt
- Emite JWT HS256 com claims `{tenant_id, user_id, exp: now + 24h}`
- Audit chain event `user_login`

JWT middleware (FastAPI dependency):
- Decode JWT → set `app.tenant_id` PostgreSQL session var via `SET LOCAL app.tenant_id = '...'` no início de cada request
- RLS policies aplicam automaticamente

### AC-06 — DPA acceptance flow ADR-019
Onboarding step 3 chama `POST /api/tenant/dpa/accept`:
- Body: `{dpa_version}` (ex: "1.0.0")
- Server lê texto canônico de `governance/legal/dpa-templates/v{version}.md` (Eric advogado paralelo redige — placeholder OK)
- Computa SHA-256 hash do texto
- Insert em `dpa_acceptances` (schema ADR-019)
- IP via `request.client.host` + user_agent via `request.headers["user-agent"]`
- Audit chain event `dpa_accepted`

### AC-07 — Audit chain HMAC eventos auth
Eventos capturados em audit chain HMAC (ADR-005 + ADR-017 pattern):
- `tenant_signup` (cadastro inicial)
- `user_created` / `user_updated` / `user_suspended`
- `user_login` / `user_logout`
- `dpa_accepted`
- `tenant_status_change` (active → suspended → active)

Payload comum:
```json
{
  "event_type": "user_login",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "timestamp": "2026-05-07T18:50:00+00:00",
  "ip_address": "192.0.2.1",
  "user_agent": "..."
}
```

### AC-08 — Test coverage ≥ 80%
**Unit tests (Pytest):**
- JWT encode/decode + expiry validation
- Bcrypt hash/verify (cost factor 12)
- DPA SHA-256 hash compute/validate
- CNPJ dígito verificador

**Integration tests (Pytest + PostgreSQL test container):**
- RLS isolation: tenant A não vê data tenant B (cross-access bloqueado)
- Onboarding wizard 4 passos completo (signup → onboarding → first user created)
- DPA acceptance with hash validation

**E2E smoke (HTTP):**
- POST /api/auth/signup → onboarding wizard 4 steps → POST /api/auth/login → POST /api/tenant/users → GET /api/tenant/users (lista 2 users)
- Coverage ≥ 80% (NFR-PERF-01 + integration RLS)

---

## 4. File List (Neo Phase 7+ implementation)

### Novos arquivos
- `bloco_auth/__init__.py`
- `bloco_auth/models.py` — Tenant + User SQLAlchemy models
- `bloco_auth/middleware.py` — JWT middleware + RLS context setter (`SET LOCAL app.tenant_id`)
- `bloco_auth/onboarding.py` — Wizard 4 passos backend logic
- `bloco_auth/dpa.py` — DPA acceptance flow integrado ADR-019
- `bloco_auth/jwt_utils.py` — encode/decode JWT helpers
- `bloco_auth/api.py` — FastAPI routers (signup + login + logout + users CRUD + dpa accept)
- `bloco_interface/web/templates/onboarding/step1_dados.html` — Sati S2 step 1
- `bloco_interface/web/templates/onboarding/step2_api_key.html` — Sati S2 step 2
- `bloco_interface/web/templates/onboarding/step3_dpa.html` — Sati S2 step 3
- `bloco_interface/web/templates/onboarding/step4_tier.html` — Sati S2 step 4
- `bloco_interface/web/static/onboarding.css` — OrSheva tokens (Sati Design System)
- `bloco_interface/web/templates/login.html` — Sati S1 login
- `bloco_database/migrations/sp04_001_auth_multitenant.sql` — schema + RLS migration
- `tests/unit/test_jwt.py`
- `tests/unit/test_bcrypt.py`
- `tests/unit/test_dpa_hash.py`
- `tests/unit/test_cnpj_validation.py`
- `tests/integration/test_auth_rls_isolation.py`
- `tests/integration/test_onboarding_e2e.py`
- `tests/integration/test_users_crud.py`

### Arquivos modificados
- `bloco_interface/web/app.py` — register `bloco_auth/api.py` routers + middleware
- `pyproject.toml` — adicionar dependencies (PyJWT, passlib[bcrypt], pydantic[email])
- `requirements.txt` (se aplicável) — sync dependencies

### Pendências cross-domain (não implementação Neo)
- `governance/legal/dpa-templates/v1.0.0.md` — texto DPA legal substantivo (Eric advogado paralelo redige; story implementation pode usar placeholder hash inicial)

---

## 5. Dev Notes (context para @dev Phase 7+)

### Stack
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL pgcrypto (não pgvector neste story)
- **JWT:** PyJWT (HS256 com `SECRET_KEY` env var de 32+ bytes)
- **Bcrypt:** passlib[bcrypt] cost factor 12 (default seguro 2026)
- **Email validation:** pydantic EmailStr
- **CNPJ validation:** validador customizado dígito verificador (lib `validate-docbr` opcional)

### Patterns
- **DPA texto canônico:** ler de filesystem `governance/legal/dpa-templates/v{version}.md` no startup OR per-request (cache 5min). Eric advogado redige paralelo — usar placeholder "[DPA TEXT PENDING — Eric advogado redige]" no início; hash será placeholder mas estrutura técnica funcional.
- **RLS pattern:** middleware FastAPI executa `SET LOCAL app.tenant_id = '<uuid>'` ao início de cada request autenticado. PostgreSQL RLS policies aplicam automaticamente.
- **Audit chain integration:** integrar com `bloco_audit/chain.py` existente (Sprint 03 preservado). Adicionar `tenant_id` no payload (Sprint 04 multi-tenant adapt).
- **Email confirmation:** signup envia email via FR-NOTIFY-01 provider (TBD pricing cross-domain — usar SendGrid/Resend/SES; placeholder mock no início OK).

### Referências cross-doc
- **PRD v2.0.1** Section 4 Authentication: `governance/prd/prd-v2.0.0-DRAFT.md`
- **UX Spec S1 Login + S2 Onboarding:** `governance/ux-spec-v2.0.0-DRAFT.md`
- **ADR-014 BYOK:** `governance/architecture/adr/adr-014-provider-abstraction-byok.md`
- **ADR-017 Multi-tenant BACKBONE:** `governance/architecture/adr/adr-017-multi-tenant-isolation-rls.md`
- **ADR-019 DPA Storage:** `governance/architecture/adr/adr-019-dpa-storage-schema.md`

---

## 6. Testing (overview)

### Pyramid
- **Unit (foundation):** JWT + bcrypt + DPA hash + CNPJ validation
- **Integration (middle):** RLS isolation multi-tenant + onboarding wizard end-to-end + users CRUD scoped
- **E2E smoke (top):** signup → onboarding → login → user CRUD → logout flow completo

### Coverage targets
- **Unit:** 90%+ (foundation pure functions)
- **Integration:** 80%+ (RLS critical paths)
- **E2E:** golden path coverage (não exhaustive)
- **Overall:** ≥ 80% (NFR-PERF-01)

### Critical scenarios
1. **RLS cross-tenant isolation:** tenant A signup → criar user A1; tenant B signup → criar user B1; tenant A login → GET /api/tenant/users retorna apenas user A1 (não B1). MUST PASS.
2. **JWT expiry:** login → JWT exp = 24h; tentar request com JWT > 24h → 401 Unauthorized
3. **Bcrypt brute force resistance:** cost factor 12 mandatory (não < 12)
4. **DPA hash mismatch:** server modifica DPA texto entre GET /current e POST /accept → 409 Conflict
5. **Email duplicado dentro tenant:** UNIQUE constraint enforced + erro 400 amigável

---

## 7. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| RLS isolation bug (tenant A vê data tenant B) | LOW | CRITICAL (data leak) | Integration test mandatory; ADR-017 pattern proven; CodeRabbit security scan |
| DPA texto canônico pendente Eric advogado | MEDIUM | LOW (placeholder OK initial) | Eric paralelo redige; story implementation usa placeholder + hash placeholder até texto real disponível |
| JWT secret rotation | LOW | HIGH (breaks all sessions) | SECRET_KEY env var + dual-key rotation pattern (futuro Sprint 05+) |
| Bcrypt cost factor degradation | LOW | MEDIUM (brute force easier) | Cost factor 12 mandatory (passlib default 12); test enforces |
| Email enumeration via signup | MEDIUM | LOW (privacy minor) | Generic error "Email indisponível" (não revela se já existe) |
| CNPJ duplicate signup | LOW | MEDIUM (split tenant data) | UNIQUE constraint cnpj + erro 400 |

---

## 8. Definition of Done

- [ ] All 8 ACs implemented + verified
- [ ] All file list files committed
- [ ] Unit tests pass (Pytest 0 failures)
- [ ] Integration tests pass (RLS isolation crítico)
- [ ] E2E smoke passes (golden path)
- [ ] Test coverage ≥ 80% (Pytest --cov)
- [ ] CodeRabbit review CRITICAL = 0
- [ ] @qa qa-gate verdict PASS or CONCERNS (não FAIL)
- [ ] Story file File List section atualizada com files reais
- [ ] Dev Agent Record section atualizada
- [ ] Status: `Done`

---

## 9. CodeRabbit Integration

### Quality predictions
- **Security focus:** JWT secret handling, bcrypt cost factor, RLS policy correctness, SQL injection prevention
- **Performance focus:** RLS overhead overhead < 5% (per ADR-017 benchmark)
- **Anti-patterns to detect:** hardcoded secrets, missing CSRF tokens, weak password validation, exposed user enumeration

### Self-healing config
- Iteration max: 3
- CRITICAL: auto-fix (3 attempts max)
- HIGH: auto-fix (3 attempts max)
- MEDIUM: document_as_debt
- LOW: ignore

---

## 10. Dev Agent Record

*Section to be populated by @dev Neo durante implementation Phase 7+*

### Agent
- **Name:** @dev Neo
- **Persona:** Software-dev — implementação de código

### Tasks completed
- [ ] AC-01 Onboarding wizard 4 passos
- [ ] AC-02 Schema tenants
- [ ] AC-03 Schema users
- [ ] AC-04 CRUD users APIs
- [ ] AC-05 Login JWT
- [ ] AC-06 DPA acceptance flow
- [ ] AC-07 Audit chain integration
- [ ] AC-08 Test coverage ≥ 80%

### Files created/modified
*To be populated by @dev*

### Test results
*To be populated by @dev (Pytest output, coverage report)*

### CodeRabbit results
*To be populated by @dev (CRITICAL/HIGH/MEDIUM/LOW counts)*

### QA Results
*Section to be populated by @qa Oracle durante qa-gate (rule story-lifecycle.md G5)*

---

## 11. Change Log

| Data | Author | Change |
|------|--------|--------|
| 2026-05-07 | @sm River | Story criada Draft (Phase 7.1 Sprint 04 — foundation) |

---

— River, removendo obstáculos com fluidez 🌊
