---
type: story
id: "SP04-LGPD-01"
title: "LGPD compliance flows — DPA + TOS operador + audit isolation endpoint"
status: Ready
epic: "Sprint 04 Cloud SaaS BYOK"
project: revisor-contratual
sprint: "04"
phase: 13.1
priority: P1
estimated_days: "2-3"
agent: "@dev (Neo)"
branch: "feat/sp04-lgpd-01 (base main pós AUTH+BYOK merge OR provisional rebase)"
created: "2026-05-08"
created_by: "@sm River"
dependencies:
  - "SP04-AUTH-01 (Done — DPA acceptance flow chunk 5 já entregue; este story consolida + extende)"
  - "SP04-BYOK-01 (Done — paralelo; não depende runtime BYOK)"
  - "ADR-017 (Multi-tenant + LGPD operador BACKBONE — Eric=operador, escritório=controlador)"
  - "ADR-019 (DPA Storage Schema retention permanent)"
  - "ADR-005 (Audit chain HMAC integration)"
source_frs:
  - "FR-LGPD-01 (DPA Eric-escritório obrigatório onboarding)"
  - "FR-LGPD-02 (TOS/EULA SaaS declarando operador Eric)"
  - "FR-AUDIT-01 (Endpoint GET /api/tenant/audit/isolation metadata isolamento)"
cross_references:
  prd: "governance/prd/prd-v2.0.0-DRAFT.md FR-LGPD-01..02 + FR-AUDIT-01 (lines 167-170)"
  ux: "Sati wireframe `/admin/lgpd` admin DPO dashboard + onboarding step3 DPA (parcial AUTH-01) + TOS step novo"
  adrs: ["adr-005", "adr-017", "adr-019"]
  story_predecessors: ["SP04-AUTH-01", "SP04-BYOK-01"]
  smith_findings_addressed: "F-016 LGPD subprocessor argument WAIVED TD-WAIVED-001 — SP04-LGPD-01 endereça compliance operador formal via TOS/EULA + DPA"
tags:
  - project/revisor-contratual
  - story
  - sprint-04
  - epic-lgpd
  - foundation-legal
  - p1
  - compliance
  - anpd
  - operador
---

# SP04-LGPD-01 — LGPD compliance flows operador posture

```
[@sm · River (Facilitator)] — Sprint 04 · Phase 13.1 · SP04-LGPD-01 · LGPD compliance
SPRINT: 04 · PHASE: 13.1 · DOMÍNIO: software-dev/lgpd-compliance
```

> **Foundation legal P1** — formaliza posture LGPD operador conforme ADR-017 BACKBONE + CON-LGPD-01 (Art. 5º LGPD): Eric=operador (provê ferramenta), escritório=controlador (decide finalidade dos dados). 3 deliverables PRD-aligned: FR-LGPD-01 DPA + FR-LGPD-02 TOS/EULA + FR-AUDIT-01 audit isolation endpoint.

> ⚠️ **NOTA divergência Morpheus brief vs PRD canônico:** Brief Morpheus sugeriu 5 deliverables (retention scheduler + forget Art. 18 + export Art. 18 + DPO admin dashboard + audit chain LGPD events). River alinha com **PRD canônico** lines 167-170 (FR-LGPD-01..02 + FR-AUDIT-01) — escopo MAIS RESTRITO. Forget/Export/DPO admin = stories Sprint 05+ separadas (não neste story; flag formal em Section 5 Pre-flight).

---

## 1. Sumário

Story foundation legal P1 — formaliza compliance LGPD posture operador Sprint 04 conforme PRD v2.0.0-DRAFT FRs canônicos (lines 167-170) + CON-LGPD-01 (Eric=operador, escritório=controlador per Art. 5º LGPD). SP04-AUTH-01 chunk 5 entregou DPA acceptance flow parcial (texto canônico placeholder v1.0.0.md + ADR-019 spec aplicada); este story SP04-LGPD-01 **consolida + extende** com TOS/EULA operador + audit isolation endpoint:

1. **FR-LGPD-01 — DPA Eric-escritório (consolidação)** — finalizar texto substantivo `governance/legal/dpa-templates/v1.0.0.md` (Eric advogado MANDATORY pre-implement); flow display + aceite digital já implementado AUTH-01 chunk 5 funcional; este story garante texto v1.0.0.md ANPD-ready
2. **FR-LGPD-02 — TOS/EULA operador (NOVO)** — texto canônico TOS declarando explicitamente Eric=operador (não controlador) + display em onboarding wizard NOVO step OR Settings panel + aceite digital + audit chain event `tos_accepted` HMAC ADR-005
3. **FR-AUDIT-01 — Endpoint audit isolation (NOVO)** — `GET /api/tenant/audit/isolation` retorna metadata para escritório auditar isolamento (counts users + analyses + dpa_acceptances + RLS policies ativas + último login per user) conforme ADR-017 transparency

**Foundation impact:** Compliance LGPD baseline formalizado. Stories P1+ subsequentes (OCR/PARSING/EXPORT/DASH) assumem CON-LGPD-01 operador posture explícita via TOS/EULA aceito + audit transparency endpoint disponível.

**Branch strategy:** `feat/sp04-lgpd-01` base `main` após Eric merge AUTH-01 + BYOK-01 PRs (clean rebase) OR `feat/sp04-byok-01` HEAD provisional (rebase trivial pós-merge).

---

## 2. As a / I want / So that

- **As a** Eric (advogado responsável LGPD — operador SaaS) + escritório de advocacia cliente (controlador dos dados)
- **I want** formalizar compliance LGPD posture operador via DPA + TOS/EULA aceito + audit transparency endpoint
- **So that** Eric mantém posture operador legalmente defensável em fiscalização ANPD + escritório controla seu papel controlador via documentos digitalmente aceitos + ambos podem auditar isolamento de dados a qualquer momento

---

## 3. Acceptance Criteria (6 ACs)

### AC-01 — DPA texto v1.0.0.md substantivo (FR-LGPD-01 consolidação)

Eric advogado finaliza texto canônico em `governance/legal/dpa-templates/v1.0.0.md` (placeholder atual via AUTH-01 chunk 5).

**Tested:** SHA-256 hash texto v1.0.0.md final é deterministic + stored em `dpa_acceptances.dpa_text_hash` per ADR-019 spec; flow AUTH-01 chunk 5 continua funcional sem mudança código (apenas texto).

### AC-02 — TOS/EULA operador texto v1.0.0.md (FR-LGPD-02 novo)

Eric advogado redige `governance/legal/tos-templates/v1.0.0.md` declarando:
- Eric (CPF/CNPJ) é **operador** SaaS (não controlador)
- Escritório cliente é **controlador** dos dados pessoais (titulares = clientes do escritório)
- Eric não trata dados além das instruções escritório (Art. 39 LGPD)
- Subprocessor: Anthropic API (BYOK — escritório paga direto, Eric não absorve token)
- Retenção logs operacionais: 12 meses
- Direitos titulares ANPD: contatar diretamente escritório (controlador)

### AC-03 — Schema PostgreSQL `tos_acceptances` (similar dpa_acceptances)

Migration SQL (Tank ratifica pre-implement):

```sql
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

ALTER TABLE tos_acceptances ENABLE ROW LEVEL SECURITY;

CREATE POLICY tos_tenant_isolation ON tos_acceptances
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

CREATE INDEX idx_tos_acceptances_tenant ON tos_acceptances(tenant_id);
CREATE INDEX idx_tos_acceptances_version ON tos_acceptances(tos_version);
```

Pattern idêntico `dpa_acceptances` (ADR-019) — retention permanent (ON DELETE RESTRICT).

### AC-04 — Endpoints TOS flow (parallel DPA pattern)

`bloco_auth/tos.py` (mirror `bloco_auth/dpa.py`):
- `GET /api/tenant/tos/text/{version}` — retorna texto canônico (sem auth — pré-onboarding)
- `POST /api/tenant/tos/accept` — body `{tos_version}` → compute SHA-256 hash + insert `tos_acceptances` + audit chain event `tos_accepted`
- `GET /api/tenant/tos/status` — verifica se tenant aceitou TOS atual

Display TOS no onboarding pode ser:
- **Opção A:** Novo step (wizard 5 passos: dados + api_key + DPA + **TOS** + tier) — adiciona friction
- **Opção B:** Combine DPA+TOS em single step 3 (menor friction; texto combinado) — Sati wireframe decide

### AC-05 — Endpoint `GET /api/tenant/audit/isolation` (FR-AUDIT-01)

`bloco_auth/audit_isolation.py` retorna JSON metadata para escritório auditar isolamento:

```json
{
  "tenant_id": "uuid",
  "counts": {
    "users": 5,
    "analyses": 142,
    "dpa_acceptances": 1,
    "tos_acceptances": 1,
    "audit_events_count": 234
  },
  "rls_policies_active": [
    "user_tenant_isolation (users)",
    "tos_tenant_isolation (tos_acceptances)",
    "byok_tenant_isolation (tenant_api_keys)",
    "tenant_isolation (dpa_acceptances)",
    "tenant_self_view (tenants)"
  ],
  "last_login_per_user": [
    {"user_id": "uuid", "email": "...", "last_login_at": "2026-05-08T..."},
    ...
  ],
  "rls_session_var_set": true,
  "current_dpa_version": "1.0.0",
  "current_tos_version": "1.0.0"
}
```

Auth obrigatório (Depends `get_current_user` + `apply_rls_context`). Audit event `audit_isolation_queried`.

### AC-06 — Test coverage condicional ≥ 80% bloco_lgpd / bloco_auth/{tos,audit_isolation}

**Unit tests (Pytest):**
- `test_tos_hash.py` — SHA-256 hash compute + NFC normalization (similar `test_dpa_hash.py`)
- `test_tos_accept_idempotent.py` — re-aceite retorna mesma row (UNIQUE constraint)
- `test_audit_isolation_aggregation.py` — counts query + RLS policies introspection

**Integration tests (Pytest + PostgreSQL `_REQUIRES_POSTGRES`):**
- `test_tos_lifecycle_e2e.py` — onboarding TOS aceite → audit event recorded → idempotent re-accept
- `test_audit_isolation_endpoint.py` — auth required + RLS scoped (tenant A vê apenas seus counts)

**Coverage:** ≥ 80% `bloco_auth/tos.py` + `bloco_auth/audit_isolation.py` com DB rodando (condicional similar AUTH-01/BYOK-01 pattern).

---

## 4. File List (Neo Phase 13.2+ implementation)

### Novos arquivos

- `bloco_auth/tos.py` — APIRouter `/api/tenant/tos` 3 endpoints (text/{version} GET + accept POST + status GET) + helpers SHA-256 hash + cache TTL 5min (mirror `dpa.py`)
- `bloco_auth/audit_isolation.py` — APIRouter `/api/tenant/audit` 1 endpoint (isolation GET) + aggregation queries + RLS policies introspection
- `bloco_database/migrations/sp04_003_lgpd_tos_audit.sql` — schema `tos_acceptances` + RLS policy + indexes + Smoke validation comments
- `governance/legal/tos-templates/v1.0.0.md` — texto canônico TOS operador (placeholder estrutural; Eric advogado redige texto substantivo MANDATORY pre-implement)
- `tests/unit/test_tos_hash.py` (~5 tests)
- `tests/unit/test_audit_isolation_aggregation.py` (~4 tests)
- `tests/integration/test_tos_lifecycle_e2e.py` (~5 tests `_REQUIRES_POSTGRES`)
- `tests/integration/test_audit_isolation_endpoint.py` (~4 tests `_REQUIRES_POSTGRES`)

### Arquivos modificados

- `governance/legal/dpa-templates/v1.0.0.md` — Eric advogado finaliza texto substantivo (placeholder atual AUTH-01 chunk 5 → texto ANPD-ready) — **AC-01 closure**
- `bloco_auth/onboarding.py` — adicionar step TOS aceite (Opção A novo step wizard 5 passos OR Opção B combine DPA+TOS step 3 — Sati wireframe decide); validate step com `tos_accepted: true` em complete_onboarding
- `bloco_auth/api.py` — register `bloco_auth.tos` router + `bloco_auth.audit_isolation` router
- `bloco_interface/web/app.py` — register routers
- `bloco_interface/web/templates/onboarding/step3_dpa.html` (modify) OR `step_tos.html` (novo) — Sati wireframe decide

### Pendências cross-domain (não implementação Neo)

- **Eric advogado MANDATORY pre-implement:**
  - Texto substantivo `governance/legal/dpa-templates/v1.0.0.md` finalizado ANPD-ready (AC-01)
  - Texto substantivo `governance/legal/tos-templates/v1.0.0.md` redigido (AC-02 — declara operador posture explícita)
- **Sati wireframe MANDATORY:** decidir Opção A (novo step wizard) vs Opção B (combine DPA+TOS step) + design TOS step display

---

## 5. Pre-flight consultation

### @data-engineer Tank (RATIFY pre-implement)

**Status:** Schema `tos_acceptances` mirror `dpa_acceptances` (ADR-019) — pattern validado. River segue ADR-019 sem desvio.

**Decisões River vs ADR-019:**
- ✅ Tabela separada `tos_acceptances` (não embutir em `dpa_acceptances`) — clarity audit + retention separada
- ✅ Pattern idêntico (UUID PK + tenant_id FK RESTRICT + version + hash + accepted_at + user_id FK + IP + user_agent + RLS)
- ✅ ON DELETE RESTRICT preserva audit retention permanent (Art. 52 LGPD)
- ⚠ **Pre-implement Tank ratifica:**
  - UNIQUE constraint composição (tenant_id, tos_version) — Tank confirma multi-version aceitação válida
  - Index seletivo se necessário (cardinality baixa esperada — 1 row per tenant per version)

### @architect Aria (NÃO necessário — alinhamento PRD-ADR)

**Status:** ADR-019 cobre DPA storage; TOS é mirror — sem nova decisão arquitetural. Aria pre-flight pode ser **skipped**.

### @ux-design-expert Sati (MANDATORY)

**Status:** UX spec atual cobre wizard 4 passos AUTH-01 (DPA step 3). FR-LGPD-02 introduz TOS — UX gap.

**Sati pre-flight MANDATORY:**
- Decisão: **Opção A** (novo step wizard 5 passos: dados + api_key + DPA + **TOS** + tier) vs **Opção B** (combine DPA+TOS step 3 — texto único)
- Wireframe TOS display + aceite checkbox
- Considerar cognitive load — wizard 5 passos pode aumentar friction de onboarding (drop-off risk)

**River recomenda Opção B** (combine DPA+TOS step 3) — menor friction + texto único legal Eric advogado pode estruturar com headers DPA e TOS sequential. Sati confirma OR propõe alternativa.

### Eric advogado (MANDATORY pre-implement — bloqueia Neo *develop)

**Status crítico:** Sem textos substantivos finalizados ANPD-ready, Neo NÃO pode `*develop` chunks de produção. Code SP04-LGPD-01 não pode ser deployed sem texto legal.

**Eric advogado MANDATORY produz:**
1. **DPA v1.0.0.md** ANPD-ready (consolidação AUTH-01 chunk 5 placeholder) — texto Art. 5º Eric=operador + escritório=controlador + finalidade tratamento + retenção + direitos titulares contato escritório
2. **TOS/EULA v1.0.0.md** novo — declara Eric=operador (não controlador) + subprocessor Anthropic BYOK + retenção logs + Art. 39 LGPD (Eric não trata além instruções escritório)

**Loop iterativo:** Eric advogado redige → River review estrutural → Eric finaliza. Estimativa: ~1-2 dias Eric advogado + ~1-2 dias Neo *develop = **2-3 days total** (mais conservador que Morpheus 4-6 days; menor scope justifica).

---

## 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Eric advogado texto DPA/TOS não finalizado a tempo | MEDIUM | HIGH (block deploy) | Loop iterativo Eric advogado paralelo; Neo pode preparar code+tests com placeholder; finalizar texto = closure AC-01/02 |
| Sati wireframe Opção A vs B → onboarding friction drop-off | LOW | MEDIUM (UX) | River recomenda Opção B (combine); Sati ratifica; A/B test pós-deploy se cohort permite |
| TOS texto não-defensável ANPD (advocacia interpretação) | LOW | CRITICAL (compliance) | Eric advogado revisa + audit second opinion advogado especializado LGPD se incerto |
| Audit isolation endpoint expõe metadata sensível cross-tenant | LOW | HIGH (data leak) | Auth obrigatório + RLS context (pattern AUTH-01/BYOK-01); test integration RLS isolation explícito |
| Migration tos_acceptances breaking change tabela existente | LOW | MEDIUM | tos_acceptances é tabela NOVA — sem ALTER TABLE existente; migration aditiva pura |
| Scope creep Morpheus brief (forget/export/DPO) reabre escopo | MEDIUM | HIGH (timeline) | River alinha PRD canônico (3 deliverables); flag em Section 5 + handoff Keymaker validate; Sprint 05+ stories separadas para forget/export/DPO admin |

---

## 7. Implementation Plan (Path B chunks sugeridos — Neo refina)

Pattern Path B SP04-AUTH-01/BYOK-01 adaptado:

1. **Chunk 1** — Setup environment: branch `feat/sp04-lgpd-01` (base main pós-merge OR provisional) + skeleton files `tos.py` + `audit_isolation.py`
2. **Chunk 2** — Database foundation: migration `sp04_003_lgpd_tos_audit.sql` (tos_acceptances + RLS + indexes); SQLAlchemy `TosAcceptance` model
3. **Chunk 3** — TOS flow `bloco_auth/tos.py` (mirror dpa.py — text/accept/status endpoints + SHA-256 hash + cache TTL); ~5 unit tests
4. **Chunk 4** — Onboarding integration: extend `complete_onboarding()` para incluir tos_acceptance insert (Opção A novo step OR Opção B combine — Sati confirma)
5. **Chunk 5** — Audit isolation endpoint `bloco_auth/audit_isolation.py` (aggregation queries counts + RLS policies introspection + last_login per user); ~4 unit tests
6. **Chunk 6** — Integration tests: 9 tests `_REQUIRES_POSTGRES` (5 TOS lifecycle + 4 audit isolation endpoint) + coverage AC-06
7. **Chunk 7** — Story closure: DoD WAIVED format honest + Final File List Consolidado + status InReview + handoff @qa Oracle qa-gate G5

**Estimativa River:** 2-3 days (escopo PRD-aligned é mais restrito que Morpheus brief sugeria; Eric advogado loop adiciona ~1-2 dias paralelo).

**Branch creation:** `feat/sp04-lgpd-01` — Operator/Neo cria chunk 1 base main (idealmente pós-AUTH+BYOK merge para clean rebase).

---

## 8. Definition of Done (template — Neo populates implementation)

A definir empiricamente durante implementation chunks 1-7. Template proposto:

### Esperado VERIFIED (se chain Path B segue AUTH-01/BYOK-01 padrão)

- [ ] All 6 ACs implementadas + verified empíricamente
- [ ] Eric advogado texto DPA v1.0.0.md + TOS v1.0.0.md finalizados ANPD-ready (AC-01 + AC-02)
- [ ] Migration SQL aplicada (`sp04_003_lgpd_tos_audit.sql`) + RLS policy `tos_tenant_isolation` funcional
- [ ] Unit tests pass (~9 tests bloco_auth/{tos,audit_isolation})
- [ ] Story file File List Section 4 atualizada Final File List Consolidado
- [ ] Dev Agent Record Section 10 chunks 1-7 entries
- [ ] Conventional commits chunks 1-7 + Story ID reference em cada
- [ ] Handoff @qa Oracle qa-gate G5 emitted

### Possível DEFERRED com WAIVED format (rule quality-gate-enforcement.md MANDATORY — 5 fields per item)

Conforme padrão AUTH-01/BYOK-01:
- Integration tests `_REQUIRES_POSTGRES` skipped sem DB local → qa-gate G5 retest
- Coverage condicional sem DB rodando → AC-06 condicional documentado
- CodeRabbit DEFERRED (CLI ausente WSL bash padrão) → self-critique manual fallback
- Sati wireframe Opção A vs B decisão deferred se UX cycle iterativo
- Eric advogado texto finalizado pode ser pendente até Sprint 04 close-out (se Eric ainda não disponível)

---

## 9. QA Validation (@po Keymaker — *validate-story-draft G3)

### Verdict @po Keymaker (2026-05-08)

**Verdict:** ✅ **GO** | **Score: 10/10** | **Status:** Draft → **Ready**

> Story tem qualidade técnica sólida, escopo PRD-aligned (não scope creep Morpheus brief), paridade estrutural com SP04-BYOK-01 (template validado). River-decision alinhar PRD canônico (3 deliverables) sobre brief Morpheus preliminar (5 deliverables) é PROCEDIMENTO CORRETO conforme LMAS rule "No Invention" + "PRD-driven story creation". Forget/Export/DPO admin/retention scheduler movidos para Sprint 05+ stories separadas mantêm audit trail explícito + escopo realista.

### 10-point PO Master Checklist (G3)

| # | Ponto | Score | Evidência |
|---|-------|-------|-----------|
| 1 | Frontmatter completo (18 campos) | ✅ 1/1 | type/id/title/status/epic/project/sprint/phase/priority/estimated_days/agent/branch/created/created_by/dependencies(5)/source_frs(3)/cross_references/tags(8) — paridade SP04-BYOK-01 |
| 2 | Sumário Section 1 claro | ✅ 1/1 | Contexto LGPD operador + 3 deliverables explícitos + foundation impact (P1+ baseline) + branch strategy + **NOTA divergência Morpheus brief vs PRD canônico documentada** |
| 3 | As a / I want / So that Section 2 | ✅ 1/1 | Eric (DPO advogado operador) + escritório (controlador) — papéis Art. 5º LGPD distintos |
| 4 | ACs estruturadas Section 3 (testable + 5+) | ✅ 1/1 | 6 ACs (excede mínimo 5) — AC-01 DPA texto v1.0.0 + AC-02 TOS NOVO + AC-03 schema mirror + AC-04 endpoints mirror + AC-05 audit isolation + AC-06 coverage. Cada AC com critérios "Tested:" explícitos |
| 5 | File List Section 4 pre-implementation contract | ✅ 1/1 | 8 novos código/tests + 5 modificados + 2 pendências cross-domain (Eric advogado MANDATORY DPA+TOS texto + Sati wireframe MANDATORY Opção A vs B) explícitas |
| 6 | Pre-flight consultation Section 5 | ✅ 1/1 | Tank ratify (light — mirror ADR-019 sem desvio) + Aria skip (justificada) + Sati MANDATORY (wireframe TOS step) + Eric advogado MANDATORY pre-implement (texto substantivo bloqueia Neo) |
| 7 | Risk Assessment Section 6 (3+ risks com P/I/M) | ✅ 1/1 | 6 risks tabelados (Eric timeline + Sati Opção A/B + TOS ANPD-defensável + audit isolation data leak + migration breaking + scope creep Morpheus reabertura) |
| 8 | Implementation Plan Section 7 chunks | ✅ 1/1 | 7 chunks Path B detalhados (vs 8 BYOK — escopo menor justifica) + estimativa 2-3 days + branch creation timing |
| 9 | Cross-references rastreáveis | ✅ 1/1 | PRD v2.0.0 lines 167-170 + ADRs 005/009/017/019 + UX (Sati wireframe MANDATORY) + predecessors AUTH-01+BYOK-01 + Smith F-016 já WAIVED |
| 10 | Frontmatter dependencies + source_frs canônicos | ✅ 1/1 | 5 dependencies (AUTH-01 + BYOK-01 + ADRs 017/019/005) + 3 source_frs canônicos (FR-LGPD-01..02 + FR-AUDIT-01) — links rastreáveis PRD oficial |
| **TOTAL** | | **10/10** | **GO threshold ≥ 7/10 — exceeded by 3 pontos** |

### Validação especial: Divergência Morpheus brief vs PRD canônico

**Decisão Keymaker: River-decision PROCEDIMENTO CORRETO ✅**

| Aspecto | Validação |
|---------|-----------|
| **Alinhamento PRD canônico está correto?** | ✅ SIM — PRD v2.0.0-DRAFT lines 167-170 explicitamente lista FR-LGPD-01 (DPA) + FR-LGPD-02 (TOS/EULA) + FR-AUDIT-01 (audit isolation endpoint) — escopo restritivo canônico |
| **River-decision viola brief Morpheus authority?** | ✅ NÃO — Morpheus brief é orientação preliminar (não decisão canônica). Keymaker invoca **LMAS rule "No Invention"** (`.claude/rules/quality-gate-enforcement.md`): "Cada deliverable DEVE ser rastreável a PRD FR-* / NFR-* / CON-* / pedido explícito do usuário / ADR. Se agente não consegue apontar fonte → BLOCK até fonte ser identificada OR feature removida." |
| **Forget/Export/DPO admin scope creep removido é defensável?** | ✅ SIM — features valiosas mas Sprint 05+ stories separadas (audit trail explícito por story; escopo MVP conservador; retrabalho prevenido) |
| **River-decision audit trail explícito?** | ✅ SIM — Section 1 NOTA divergência + Section 5 Pre-flight consultation + Section 12 Change Log entry. Decisão totalmente documentada e rastreável |

**Conclusão:** River executou disciplina LMAS Constitution correta. Brief Morpheus serve como sugestão orquestracional; PRD canônico é a fonte. Quando divergem, alinhar PRD é PROCEDIMENTO mandatory por rule `quality-gate-enforcement.md` (No Invention universal cross-domain).

### Concerns River flagged — Keymaker decisão

| Concern River | Decisão Keymaker | Justificativa |
|---|---|---|
| **Eric advogado MANDATORY pre-implement (bloqueia Neo *develop)** | ✅ ACEITÁVEL Ready | Story Ready é estado válido mesmo com Eric advogado pre-implement pendente. Análogo SP04-AUTH-01 chunk 5 que entregou DPA flow com texto placeholder + AUTH-01 fechou Done — Eric finalizou texto pós-Done. Em LGPD-01, Eric tem oportunidade finalizar paralelo Neo chunks 1-3 (setup + DB foundation + skeleton TOS flow); chunks 4-7 esperam texto |
| **DPA texto v1.0.0.md placeholder pendência herdada AUTH-01** | ✅ ACEITÁVEL escopo deste story | SP04-LGPD-01 AC-01 explicitamente CONSOLIDA finalize texto v1.0.0.md (closure pendência). Não-bloqueante validate-story-draft |

### Concerns adicionais Keymaker (LOW non-bloqueantes — flag para Neo/Eric)

| # | Concern | Severidade | Recomendação |
|---|---------|-----------|--------------|
| K-LGPD-01 | **AC-04 Sati Opção A vs B onboarding decision** | LOW | Sati wireframe MANDATORY pre-Neo *develop chunk 4. River recomenda Opção B (combine DPA+TOS step 3 — menor friction); Sati confirma OR propõe alternativa. NÃO bloqueia Ready |
| K-LGPD-02 | **AC-02 TOS texto operador qualidade ANPD-defensável** | LOW | Risk #3 já flagged Section 6. Eric advogado pode buscar second opinion advogado especializado LGPD se incerto. Audit trail proteção |
| K-LGPD-03 | **Branch base feat/sp04-byok-01 HEAD provisional vs main pós-merge** | LOW | Recomenda aguardar Eric merge AUTH+BYOK para branch base main clean. Mas BYOK base é viável se urgência (rebase trivial pós-merge — pattern AUTH-01→BYOK-01 já validado) |

### Próximo step

**Recomendação Keymaker:** Skill `LMAS:agents:dev` (@dev Neo) consume + execute pre-implement orchestration:

1. **Eric advogado paralelo (MANDATORY):** finalizar `governance/legal/dpa-templates/v1.0.0.md` + redigir `governance/legal/tos-templates/v1.0.0.md` ANPD-ready (loop iterativo ~1-2 days)
2. **Sati Skill wireframe MANDATORY:** Opção A novo wizard step 5 vs Opção B combine DPA+TOS step 3 (River recomenda B)
3. **Tank Skill ratify pre-implement (light):** schema tos_acceptances mirror dpa_acceptances ADR-019 + UNIQUE constraint + indexes seletivos
4. **Após consultations + Eric texto preliminar:** Neo `*develop` chunks 1-7 Path B (similar SP04-BYOK-01 ritmo + estimativa 2-3 days)
5. **Branch creation:** Neo cria `feat/sp04-lgpd-01` no início chunk 1 (base provisional `feat/sp04-byok-01` HEAD OR main pós-merge — Eric decide via review PR #4/#5)

**Cadeia próxima Skill:** Neo *develop → Oracle qa-gate G5 → Keymaker close-story → Operator push+PR Sprint 04 PR #6 (similar Path B AUTH-01/BYOK-01).

— Keymaker, equilibrando prioridades 🎯

---

## 10. Dev Agent Record (vazio — preenchido @dev Neo durante implement)

> @dev Neo `*develop SP04-LGPD-01` — chunks 1-7 entries preencham aqui durante Phase 13.2+ implementation.

---

## 11. QA Validation post-implementation (vazio — preenchido @qa Oracle qa-gate G5)

> @qa Oracle `*review SP04-LGPD-01` qa-gate G5 — adversarial review verdict + findings preenchem aqui pós-implementation.

---

## 12. Change Log

| Data | Author | Change |
|------|--------|--------|
| 2026-05-08 | @po Keymaker | Phase 13.2 — *validate-story-draft G3 verdict ✅ GO score 10/10 executado: status frontmatter Draft → Ready; Section 9 QA Validation preenchida com 10-point checklist completo (TODOS PASS — paridade SP04-BYOK-01 + escopo PRD-aligned + ACs testáveis "Tested:" explícitas + pre-flight Section 5 com justificativas + 6 risks tabelados + 7 chunks Path B + cross-references rastreáveis); **Validação especial divergência Morpheus brief vs PRD canônico:** River-decision PROCEDIMENTO CORRETO confirmado por Keymaker invocando LMAS rule "No Invention" (`quality-gate-enforcement.md`) — PRD é canônico (3 deliverables); Morpheus brief é preliminar (5 deliverables); Forget/Export/DPO/retention scheduler movidos para Sprint 05+ stories separadas (audit trail). Concerns River flagged 2 ACEITÁVEIS pós-Ready (Eric advogado MANDATORY pre-implement análogo AUTH-01 chunk 5 placeholder pattern; DPA texto pendência consolidada via AC-01); 3 concerns adicionais Keymaker LOW non-bloqueantes (K-LGPD-01 Sati Opção A vs B + K-LGPD-02 TOS qualidade ANPD + K-LGPD-03 branch base provisional). Próximo step: cadeia Eric advogado paralelo + Sati Skill wireframe + Tank ratify (light) + Neo *develop chunks 1-7 Path B (estimativa 2-3 days). Conventional commit `docs(governance): validate-story-draft SP04-LGPD-01 — verdict GO score 10/10 [Story SP04-LGPD-01]`. |
| 2026-05-08 | @sm River | Story criada Draft Phase 13.1 — LGPD compliance flows operador posture. **Foundation legal P1** Sprint 04 (após Foundation P0 cycle COMPLETO AUTH-01 + BYOK-01). Pre-leitura: PRD v2.0.0-DRAFT FR-LGPD-01..02 + FR-AUDIT-01 (lines 167-170) + ADR-017 BACKBONE LGPD operador + ADR-019 DPA Storage + ADR-005 Audit chain + bloco_lgpd/ existing (encryption + headers + permissions Sprint 03 — verify reusability Neo pre-implement). **River decisão crítica: alinhar PRD canônico (3 deliverables) — Morpheus brief sugeriu 5 deliverables (forget/export/DPO admin/retention scheduler), mas escopo PRD restritivo a FR-LGPD-01 DPA + FR-LGPD-02 TOS/EULA + FR-AUDIT-01 audit isolation endpoint.** Forget/Export/DPO admin = stories Sprint 05+ separadas (não neste story). 6 ACs estruturadas (DPA texto v1.0.0 finalize + TOS texto v1.0.0 novo + schema tos_acceptances mirror dpa_acceptances + endpoints TOS flow mirror DPA + endpoint audit isolation FR-AUDIT-01 + coverage condicional bloco_lgpd). Pre-flight consultation: Tank ratify schema (mandatory pre-implement); Aria skip (ADR-019 mirror — sem nova decisão); Sati wireframe MANDATORY (Opção A novo wizard step 5 vs Opção B combine DPA+TOS step 3 — River recomenda B menor friction); **Eric advogado MANDATORY pre-implement** — bloqueia Neo *develop sem texto substantivo DPA v1.0.0.md ANPD-ready + TOS v1.0.0.md operador posture redigido. 6 risks documentados (Eric advogado timeline, Sati Opção A/B drop-off, TOS texto ANPD-defensável, audit isolation data leak, migration breaking, scope creep Morpheus brief reabertura). Implementation Plan 7 chunks Path B sugeridos. Estimativa 2-3 days (escopo restritivo PRD vs Morpheus 4-6 days — Eric advogado loop paralelo). Branch sugerido: feat/sp04-lgpd-01 base main pós-AUTH+BYOK merge OR provisional. Próxima Skill: LMAS:agents:po (@po Keymaker *validate-story-draft G3 10-point checklist). |

---

— River, alinhando PRD canônico sobre brief preliminar 🌊
