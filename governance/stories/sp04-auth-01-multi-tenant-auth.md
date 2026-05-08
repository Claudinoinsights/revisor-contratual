---
type: story
id: "SP04-AUTH-01"
title: "Multi-tenant authentication + tenant onboarding"
status: Ready
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

**Phase 7.2.1 — Chunk 1 (Setup environment) [2026-05-07]**
- `pyproject.toml` — modified: deps Sprint 04 (`sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.29`, `pyjwt[crypto]>=2.8`, `passlib[bcrypt]>=1.7.4`); promoted `pydantic>=2.8` → `pydantic[email]>=2.8`; included `bloco_auth*` + `bloco_database*` em packages e coverage source
- `.env.example` — modified: seção "Sprint 04 — Cloud SaaS BYOK Multi-tenant" com 5 vars (DATABASE_URL, JWT_SECRET_KEY, JWT_EXPIRY_HOURS=24, JWT_ALGORITHM=HS256, DPA_TEMPLATES_DIR)
- `bloco_auth/__init__.py` — created: package marker com docstring de escopo
- `bloco_database/__init__.py` — created: package marker para migrations PostgreSQL

**Phase 7.2.2 — Chunk 2 (Database foundation) [2026-05-07]**
- `bloco_database/migrations/sp04_001_auth_multitenant.sql` — created: DDL canônico Sprint 04 (`CREATE EXTENSION pgcrypto` + 3 tabelas + 4 RLS policies + 7 indexes + smoke validation queries no rodapé). Single source of truth para schema (story AC-02, AC-03, AC-06 + ADR-019 §2)
- `bloco_auth/models.py` — created: SQLAlchemy 2.0 async ORM (`Tenant`, `User`, `DpaAcceptance`) com `Mapped` typing, `PG_UUID(as_uuid=True)`, `INET`, `DateTime(timezone=True)`, ON DELETE rules (CASCADE users, RESTRICT dpa_acceptances), composite UniqueConstraints
- `bloco_auth/db.py` — created: async engine factory + sessionmaker singleton + `with_tenant_context(session, tenant_id)` async context manager (executa `SET LOCAL app.tenant_id` dentro de transaction — RLS ativação automática). Helper `reset_engine()` para uso em tests integration

**Phase 7.2.3 — Chunk 3 (JWT + bcrypt foundation) [2026-05-07]**
- `bloco_auth/jwt_utils.py` — created: JWT HS256 encode/decode + `JWTPayload` pydantic BaseModel + `JWTError` + `ConfigError`. `_load_secret()` com `@lru_cache` valida `JWT_SECRET_KEY` ≥ 32 bytes eager. PyJWT 2.12.1 com `options={"require": [...]}` detecta missing claims. `validate_config()` hook explícito para startup (Story Risk #3 secret rotation)
- `bloco_auth/passwords.py` — created: raw bcrypt (não passlib — incompat passlib 1.7.4 ↔ bcrypt 4.x via `__about__` removido). `hash_password` cost 12 + `verify_password` constant-time + `verify_cost_factor` defensive parser + `PasswordTooLongError` anti silent truncation
- `bloco_auth/middleware.py` — created: FastAPI `Depends(get_current_user)` extrai `Bearer <token>`, decoda JWT, retorna `(tenant_id, user_id)`. HTTPException 401 com `WWW-Authenticate: Bearer` (RFC 6750). Re-export semântico `apply_rls_context = with_tenant_context` (db.py)
- `tests/unit/test_jwt.py` — created: 8 tests (encode/decode roundtrip, expiry 24h Smith F-008, expired rejection, tampered payload, missing claim, secret < 32 bytes, secret missing, validate_config eager)
- `tests/unit/test_bcrypt.py` — created: 10 tests (hash/verify roundtrip, wrong password, cost 12 prefix `$2b$12$`, cost < 12 rejection via raw bcrypt forge, salt único, password too long, cost insuficiente em hash_password, invalid format, malformed hash defensive False)
- `pyproject.toml` — modified: removido `passlib[bcrypt]` (incompat documentada inline), comentário de razão técnica preservado

**Decisões Neo autônomas (Eric mandate):**
- Removido passlib em runtime (incompat passlib 1.7.4 ↔ bcrypt>=4.0). Raw bcrypt já presente em deps Sprint 03. API mantida (`hash_password`, `verify_password`, `verify_cost_factor`) — chunk 4 consome sem mudança
- `_load_secret` via `@lru_cache(maxsize=1)` em vez de eager module-level `_SECRET = _load_secret()`. Permite tests resetarem cache + lazy boot sem ConfigError em import
- `validate_config()` exposto como hook explícito para startup app (`bloco_interface/web/app.py` chamará no boot — chunk subsequente)
- Adicionado `bloco_auth/passwords.py` como 5º file novo (brief mencionou 4) — bcrypt logic precisa de home; chunk 4 consumirá igual

### Test results

**Chunks 1-2 (foundation):** sem testes — chunks são SETUP + DDL + ORM models.

**Chunk 3 — pytest 18/18 PASSING ✅:**
```
tests/unit/test_jwt.py ........        8 passed
tests/unit/test_bcrypt.py ..........  10 passed
======== 18 passed in 2.31s ========
```
Coverage chunk 3 modules: `bloco_auth/jwt_utils.py` 87%, `bloco_auth/passwords.py` 97%. `bloco_auth/middleware.py`, `models.py`, `db.py` 0% (esperado — tests entram chunks 4+ via integration). Coverage global 44% (gate ≥ 80% é em chunk 8 closure conforme Story AC-08).

**Deferred validations (Chunk 2 → chunk 4 OR Operator local env):**
- `psql "$DATABASE_URL" -f bloco_database/migrations/sp04_001_auth_multitenant.sql` para aplicar migration localmente (chunk 4 RLS isolation E2E test #1 BLOCKING precisa DB rodando)
- Smoke queries no rodapé do SQL (verificar `pg_extension`, `pg_class.relrowsecurity`, `pg_policies`, `pg_indexes`)

**Resolved:** `pip install -e ".[dev]"` ✅ executado em chunk 3 — pyjwt 2.12.1 + email-validator 2.3.0 + dnspython 2.8.0 instalados; sqlalchemy 2.0.48, passlib 1.7.4, pydantic 2.12.5 already-satisfied.

### CodeRabbit results

**Chunks 1-2:** deferido para chunk com business logic.

**Chunk 3 — DEFERRED (CodeRabbit CLI não instalado no ambiente):**
- WSL bash: `bash: not found` (WSL distro não configurada para esta tool)
- Windows direct: `coderabbit not in PATH`, `~/.local/bin/coderabbit` ausente
- Self-critique manual @dev Neo (substituto fallback per dev agent definition):
  - **0 CRITICAL detectados** — secrets via env (`JWT_SECRET_KEY` validado eager), bcrypt `checkpw` constant-time interno, sem hardcoded values, sem eval/exec dynamic, RFC 6750 `WWW-Authenticate: Bearer` em 401 responses
  - **0 HIGH detectados** — `JWTError` wrapping não vaza `SECRET_KEY` em mensagens, `PasswordTooLongError` anti silent truncation, `verify_password` defensive `False` em hash malformado, `verify_cost_factor` regex parser não-throws
  - **MEDIUM observations (registrar TECH-DEBT.md candidate):**
    - Rate limiting em endpoints auth deferido para chunk 4 (api.py)
    - JWT secret rotation strategy (dual-key pattern) deferido para Sprint 05+
    - `_get_algorithm()` lê `JWT_ALGORITHM` env sem whitelist explícito; PyJWT default rejeita `"none"` algorithm — defesa adequada via biblioteca, mas explícito seria mais robusto
- **Action item:** Operator/CC.43 follow-up para instalar CodeRabbit CLI (TECH-DEBT.md entry) + re-run full review em chunk 8 story closure

### Chunks remaining (sequência recomendada Morpheus)

- [x] **Chunk 3:** JWT + bcrypt foundation — `bloco_auth/jwt_utils.py` + `bloco_auth/passwords.py` + `bloco_auth/middleware.py` + `tests/unit/test_jwt.py` + `tests/unit/test_bcrypt.py` ✅ DONE 18/18 tests passing
- [ ] **Chunk 4:** Auth API — `bloco_auth/api.py` + `bloco_auth/onboarding.py` + `tests/integration/test_auth_rls_isolation.py` (RLS isolation #1 BLOCKING). Pre-req: PostgreSQL local rodando + migration aplicada
- [ ] **Chunk 5:** DPA flow — `bloco_auth/dpa.py` + 3 endpoints + `governance/legal/dpa-templates/v1.0.0.md` placeholder + tests
- [ ] **Chunk 6:** UI templates — 4 onboarding steps + login.html + onboarding.css OrSheva (Sati S2/S1 wireframes)
- [ ] **Chunk 7:** Integration + E2E — `test_onboarding_e2e.py` + `test_users_crud.py` + `test_login_jwt.py` + coverage ≥ 80%
- [ ] **Chunk 8:** Story closure — DoD checkboxes 10/10 + Change Log + status Ready → InReview

### QA Results
*Section to be populated by @qa Oracle durante qa-gate (rule story-lifecycle.md G5)*

---

## 11. QA Validation (rule story-lifecycle.md G3)

### Validated by: @po Keymaker
### Date: 2026-05-07
### Verdict: ✅ GO
### Score: 10/10

| # | Checklist Item | Pass/Fail | Notes |
|---|---------------|-----------|-------|
| 1 | Story title clear and descriptive? | ✅ PASS | "Multi-tenant authentication + tenant onboarding" — purpose + scope + workflow explícitos |
| 2 | Story description complete (As a / I want / So that)? | ✅ PASS | Persona específica (advogado escritório brasileiro), need claro (cadastrar tenant + gerenciar users), value mensurável (data isolation + control granular) |
| 3 | Acceptance Criteria clear and testable? | ✅ PASS | 8 ACs com SQL schema inline + JWT claims explícitos + behavior endpoints — zero ambiguidade. Implementação imediata Neo Phase 7+ |
| 4 | Tasks/Subtasks defined? | ✅ PASS | File List (~20 files) + Testing pyramid funcionam como decomposição implementação. Sem Tasks section formal mas File List + ACs combinados servem como guidance suficiente |
| 5 | File List documented? | ✅ PASS | Exhaustivo: 7 bloco_auth/* + 5 templates + 1 CSS + 1 SQL migration + 7 test files + 3 modified + pendência cross-domain explícita |
| 6 | Dev Notes provide sufficient context? | ✅ PASS | Stack (FastAPI/SQLAlchemy/PostgreSQL pgcrypto/JWT/bcrypt) + Patterns (DPA read + RLS pattern + Audit chain + Email confirmation) + Cross-doc refs (PRD v2.0.1 Section 4 + UX S1+S2 + ADR-014/017/019) |
| 7 | Testing approach described? | ✅ PASS | Pyramid Unit/Integration/E2E + Coverage targets (90% Unit, 80% Integration, golden path E2E, ≥ 80% overall) + 5 critical scenarios prioritized (RLS isolation #1 CRITICAL) |
| 8 | Dependencies identified? | ✅ PASS | 3 ADRs (014/017/019) + 3 FRs (FR-AUTH-01..03) + Smith findings addressed (F-006/F-008/F-013) — triangulação forte em frontmatter + Dev Notes + Risk Assessment |
| 9 | Story sized appropriately (3-5 dias estimated)? | ✅ PASS | Realista para foundation auth solo dev. RLS testing pode estender ao topo do range mas P0 justifica investment time |
| 10 | Risk Assessment + Definition of Done defined? | ✅ PASS | 6 risks com Probability + Impact + Mitigation (RLS isolation #1 LOW/CRITICAL com defense-in-depth 3 layers) + 10 DoD checkboxes mandatory |

### Result

**Story aprovada para @dev implementation post-merge PR #3. Status Draft → Ready.**

Foundation P0 SP04-AUTH-01 está pronta para ativação. Quality gates Phase 7+ completos:
- AC-08 garante test coverage ≥ 80% (NFR-PERF-01 compliance)
- Risk #1 RLS isolation defended via 3 layers (ADR-017 pattern + integration test mandatory + CodeRabbit security scan)
- Cross-domain pendências documentadas (DPA texto Eric advogado + Notification provider TBD pricing)

### Recomendação @po Keymaker

Após Eric merge PR #3 → @dev Neo pode iniciar implementation imediatamente (sem wait blockers). Branch sugerida: `feat/sp04-auth-01` baseada em main pós-merge.

13 stories Sprint 04 dependentes desbloquadas pela foundation.

---

## 12. Change Log

| Data | Author | Change |
|------|--------|--------|
| 2026-05-07 | @sm River | Story criada Draft (Phase 7.1 Sprint 04 — foundation) |
| 2026-05-07 | @po Keymaker | QA Validation G3 — Verdict: ✅ GO (Score: 10/10) — Status Draft → Ready |
| 2026-05-07 | @dev Neo | Phase 7.2.1-2 — Chunks 1-2 implementados (setup environment + DB foundation): pyproject.toml deps, bloco_auth + bloco_database packages, migration SQL canônica (3 tabelas + 4 RLS policies + 7 indexes), SQLAlchemy 2.0 async models, async engine + RLS context helper. 6 files novos + 2 modified. Chunks 3-8 pendentes. |
| 2026-05-07 | @dev Neo | Phase 7.2.3 — Chunk 3 (JWT + bcrypt foundation) implementado: jwt_utils.py (PyJWT HS256 + JWTPayload pydantic + ConfigError eager validation), passwords.py (raw bcrypt 4.x — passlib droppado por incompat), middleware.py (FastAPI Depends 401 RFC 6750), test_jwt.py 8 tests + test_bcrypt.py 10 tests = 18/18 passing. Coverage local jwt_utils 87% + passwords 97%. CodeRabbit deferred (CLI não instalado) — self-critique manual: 0 CRITICAL/0 HIGH. 5 files novos + 1 modified (pyproject.toml). |

---

— Keymaker, equilibrando prioridades 🎯
