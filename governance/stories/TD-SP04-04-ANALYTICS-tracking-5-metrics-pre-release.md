---
type: story
id: TD-SP04-04-ANALYTICS
title: "Analytics Tracking 5 Métricas Pré-Release v0.3.0 (Sati Eixo 5 MANDATORY)"
status: Ready
priority: 2
sprint: "5+"
epic: "Sprint-5-plus-pre-release-v0.3.0"
owner: "@dev (Neo)"
estimated_effort: "14-16h (Smith H2 honest revision; Trinity initial 8h superseded)"
severity_origem: "MEDIUM (upgrade from LOW Sprint 04 via Sati ratify post-hoc Eixo 5 mandatory)"
created: "2026-05-13"
created_by: "@sm (River)"
predecessor_handoff: ".lmas/handoffs/handoff-smith-to-river-2026-05-13-prd-v2051-CLEAN-go-fase-2.yaml"
ordem: "19.2"
related_prds:
  - "prd-v2.0.5.1-MICRO-PATCH-SMITH-INFECTED-FIXES (file prd-v2.0.5.0-PATCH-ANALYTICS-EIXO-5.md inplace)"
related_adrs:
  - "ADR-017 Multi-Tenant Isolation RLS (REUSE source schema policy)"
  - "ADR-019 DPA Storage Schema (consent opt-out reuse)"
  - "ADR-020 Multi-Doctype Dispatcher v2 (7 modos validation target)"
related_stories:
  - "SP04-LGPD-01 (REUSE source — audit chain HMAC + cronjob + DPA acceptance)"
  - "SP04-AUTH-01 (REUSE source — JWT cookie httpOnly + tenant_id derivation)"
  - "TD-SP04-15 (Bloco 1 precedent — frontend additive pattern)"
related_findings:
  - "Sati ratify post-hoc Sprint 04 sessão 92 Eixo 5 🔴 MANDATORY"
  - "Smith mid-chain INFECTED v2.0.5.0 (15 findings) + Smith re-verify CLEAN v2.0.5.1"
unblocks:
  - "v0.3.0 public release Sprint 5+/6+ (Eric advogado externo TOS + Smoke E2E paralelos remain)"
tags:
  - project/revisor-contratual
  - story
  - sprint-5-plus
  - td-sp04-04
  - analytics
  - pre-release-v0.3.0
  - sati-eixo-5
  - mandatory
  - reuse-sp04-lgpd-01
---

# Story TD-SP04-04-ANALYTICS — Analytics Tracking 5 Métricas Pré-Release v0.3.0

## Story

**Como** Eric (Orsheva founder) supervisionando rollout v0.3.0 do Revisor Contratual SaaS BYOK,
**Eu quero** capturar e expor 5 métricas analytics empíricas (drop-off por doctype, TTI seleção→submit, % primeira escolha Geral, % reclassificação, distribuição Pareto 7 modos) via CLI + dashboard,
**Para que** posso validar empiricamente a expansão 4→7 doctypes (ADR-020) vs hipótese — confirmando OR refutando se o gain UX cognitive load (Sati Eixo 2 BORDERLINE) realmente materializa em produção, com defense-in-depth LGPD compliance (multi-tenant isolation + HMAC integrity + 9 PII vectors anonymized).

---

## Contexto

**Trigger:** Sati ratify post-hoc Sprint 04 sessão 92 (`governance/qa/sati-ratify-post-hoc-sidebar-7-modos-2026-05-09.md`) declarou Eixo 5 "Analytics tracking pós-deploy" como **🔴 MANDATORY** para release público v0.3.0. Não-implementar = manter expansão 4→7 doctypes como hipótese (não decisão validada empiricamente).

**PRD canonical:** v2.0.5.1 MICRO-PATCH SMITH-INFECTED-FIXES (file `prd-v2.0.5.0-PATCH-ANALYTICS-EIXO-5.md` inplace bump 2.0.5.0 → 2.0.5.1) — referência completa em todas Sections 2 (FRs), 3 (NFRs), 4 (Touchpoints), 5 (REUSE Table), 6 (Effort), 11 (Catalog).

**Smith chain converged CLEAN:** Smith mid-chain INFECTED v2.0.5.0 (15 findings) → Trinity v2.0.5.1 endereçou 6 MUST + 4 SHOULD + 5 LOW cataloged → Smith re-verify CLEAN. Foundation sólida para River draft.

**Pré-release v0.3.0 blocker status:** Esta story endereça 1 dos 4 blockers (TD-SP04-04-ANALYTICS Sati Eixo 5 MANDATORY); 3 restantes são externos Eric (TOS canônico + Smoke E2E + BL-VAULT/GOLDEN-SET).

---

## Acceptance Criteria

### FR-ANALYTICS-01 — Drop-off rate por doctype (MUST)

- [ ] **AC-1:** Sistema registra evento `analytics.doctype_dropoff` quando sessão sem `contract_submitted` dentro de 15min após `doctype_selected` OR via `beforeunload` event OR JWT session expiry
  - Verificável: pytest `test_drop_off_event_after_15min_no_submit` + `test_drop_off_event_on_beforeunload`
- [ ] **AC-2:** CLI `lmas analytics drop-off --period=7d --doctype=ccb` retorna percentage por doctype com threshold compliance (≤ 15% PASS, > 15% FAIL com action recommendation)
  - Verificável: CLI command empírico + JSON output schema validado

### FR-ANALYTICS-02 — TTI seleção→submit (MUST)

- [ ] **AC-3:** Sistema calcula delta server-side entre `event.doctype_selected` e `event.contract_submitted` na mesma session_id (millisecond precision)
  - Verificável: pytest `test_tti_delta_calculation_server_side_not_client_drift`
- [ ] **AC-4:** CLI `lmas analytics tti --doctype=cartao --period=30d --percentile=p90` retorna p90 (NÃO p50 — Smith M2 fix; Smith H2 caveat aplicada — adicional p50/p99 disponível como flags)
  - Verificável: CLI empírico + threshold ≤ 90s (p90) PASS

### FR-ANALYTICS-03 — % uso Geral primeira escolha (MUST)

- [ ] **AC-5:** Sistema registra `first_doctype_selected` apenas no primeiro click sidebar de cada session_id após login bem-sucedido (Smith M3 fix interpretation explicit)
  - Verificável: pytest `test_first_doctype_only_per_session_after_login` + `test_reclassifications_do_not_update_first_doctype`
- [ ] **AC-6:** CLI `lmas analytics geral-pct --period=30d` retorna percentage sessions cuja primeira escolha foi `geral` com threshold compliance (≤ 10% PASS)
  - Verificável: CLI empírico

### FR-ANALYTICS-04 — % reclassificação manual (MUST)

- [ ] **AC-7:** Sistema detecta `doctype_changed` events quando user troca doctype A → B antes de submit; backend tracks sequence per session
  - Verificável: pytest `test_doctype_changed_event_from_to_matrix`
- [ ] **AC-8:** CLI `lmas analytics reclassification --period=30d --breakdown-from-to` retorna matriz from→to com threshold compliance (≤ 5% PASS)
  - Verificável: CLI empírico + matriz JSON schema

### FR-ANALYTICS-05 — Distribuição Pareto 7 modos (MUST)

- [ ] **AC-9:** Sistema agrega contagem `doctype_selected` events por modo (sem dedup intra-session — preserva intent)
  - Verificável: pytest `test_pareto_aggregation_no_dedup_intra_session`
- [ ] **AC-10:** CLI `lmas analytics pareto --period=30d` retorna ranking + threshold compliance (Top-3 ≥ 60% AND Cauda ≥ 5% PASS) com CAVEAT re-calibration após 50+ sessions empíricas (Smith M4 fix)
  - Verificável: CLI empírico

### NFR-PRIVACY-01 — LGPD Compliance + 9 PII Vectors (MUST — Smith H3 + C1 + C2 fixes)

- [ ] **AC-11:** `tenant_id` derivado server-side de JWT cookie httpOnly; Pydantic schema REJEITA payload com tenant_id explicit (retorna HTTP 400 mesmo se JWT válido) — defense-in-depth (Smith C1 fix)
  - Verificável: pytest `test_analytics_event_rejects_payload_tenant_id_explicit`
- [ ] **AC-12:** 9 PII vectors absent/anonymized: contract text + advogado(a) name + CPF/CNPJ + OAB + IP truncate /16 + UA hash + Geo headers strip + Timing round to minute + session_id rotation 50 events OR 30min (Smith H3 fix)
  - Verificável: pytest `test_analytics_event_payload_pii_completeness_9_vectors`
- [ ] **AC-13:** HMAC chain tamper detection runtime retorna HTTP 500 + audit_log `HMAC_INTEGRITY_VIOLATION` CRITICAL + email alert + tenant quarantine flag (Smith C2 fix)
  - Verificável: pytest `test_hmac_tamper_detection_returns_500_alerts_maintainer`
- [ ] **AC-14:** Cronjob daily `analytics_chain_verify` rescaneia últimos 7 dias HMAC chain integrity (reuse SP04-LGPD-01 cronjob pattern Phase 13.3 chunk 5)
  - Verificável: pytest `test_periodic_chain_verify_cron_runs_daily`

### NFR-RELIABILITY-01 — Event Delivery Guarantees (MUST — Smith H1 fix)

- [ ] **AC-15:** At-least-once delivery com idempotency keys `event_id` UUID v4 client-side + retry backoff 2s/4s/8s max 3 + UNIQUE constraint server-side (duplicate retorna 200 silent)
  - Verificável: pytest `test_analytics_event_idempotency_duplicate_returns_200_silent`

### NFR-AVAILABILITY-01 — Graceful Degradation (MUST — Smith H1 fix)

- [ ] **AC-16:** Frontend submit contract SUCCEEDS quando `/api/analytics/event` retorna 503; events enfileirados em localStorage (cap 100 FIFO); background retry via health check ping /api/analytics/health a cada 30s
  - Verificável: pytest E2E `test_contract_submit_succeeds_when_analytics_endpoint_down_503`

### NFR-OBSERVABILITY-01 — Monitoring Overhead (SHOULD — Smith H1 fix)

- [ ] **AC-17:** Health endpoint `GET /api/analytics/health` retorna `{status, chain_integrity, queue_depth, p95_latency_ms}` JSON; metrics export Prometheus-compatible em `/api/analytics/metrics`; logs estruturados JSON sem PII
  - Verificável: smoke E2E `curl /api/analytics/health` retorna 200 + schema validation

### Constitutional Alignment (MUST)

- [ ] **AC-18:** Constitution Art. I CLI First — 8 CLI commands implementados ANTES de qualquer dashboard UI (drop-off, tti, geral-pct, reclassification, pareto, privacy-audit, chain-verify, export, health)
  - Verificável: `lmas analytics --help` lista todos commands; sem dashboard UI standalone até CLI funcional
- [ ] **AC-19:** Zero regression baseline — pytest unit suite mantém **≥352 passed** (Sprint 04 baseline) + adiciona ~50 novos tests analytics (target 400+ total)
  - Verificável: `python -m pytest tests/unit/ --no-cov -q` retorna 400+ passed, 0 failed
- [ ] **AC-20:** Multi-tenant isolation verified — cross-tenant queries blocked at RLS level + JWT derivation level (defense-in-depth)
  - Verificável: pytest `test_rls_blocks_cross_tenant_analytics_query` + `test_jwt_derived_tenant_id_overrides_payload`

### Effort Budget (SHOULD — Smith H2 fix)

- [ ] **AC-21:** Effort total ≤ 16h (Smith H2 envelope: 14h target + 2h buffer); Aria architect spike pre-implementation viable (~30min se Neo solicitar)
  - Verificável: time tracking Neo durante implementation; spike output documentado se ocorrer

### Tech Debt Cataloging (SHOULD)

- [ ] **AC-22:** 5 LOW findings cataloged em `governance/TECH-DEBT.md` durante Operator closure: TD-ANALYTICS-L1 a L5 (edge cases + dashboard FR + opt-out FR + retention cron + session rotation)
  - Verificável: TECH-DEBT.md inclui 5 entries Sprint 5+/6+

**Total ACs: 22** (excedendo handoff minimum 18 — Smith mid-chain antecipa rigor).

---

## Tasks / Subtasks (5 chunks Path B — Smith H2 honest 14-16h escopo)

### Chunk 1 — Backend Schema Migration (~2-3h)

- [ ] Criar migration `bloco_auth/migrations/sp05_001_analytics_events.sql` (mirror `audit_isolation_events` schema)
- [ ] Aplicar RLS policy `analytics_events_tenant_isolation` per ADR-017 §2 (`CREATE POLICY tenant_isolation USING (tenant_id = current_setting('app.current_tenant')::uuid)`)
- [ ] Adicionar `event_type` enum extension (analytics-specific values: `doctype_selected`, `first_doctype_selected`, `doctype_changed`, `doctype_dropoff`, `contract_submitted`)
- [ ] UNIQUE constraint em `(event_id, tenant_id)` para idempotency NFR-RELIABILITY-01
- [ ] Tests `tests/unit/test_analytics_schema_migration.py`: RLS isolation cross-tenant blocked + HMAC chain init + idempotency UNIQUE

### Chunk 2 — Backend FastAPI Router (~2-3h)

- [ ] Criar `bloco_auth/analytics.py` (mirror `bloco_auth/audit_isolation.py` pattern)
- [ ] Pydantic models: `AnalyticsEventIn` (sem tenant_id field — Smith C1 fix), `AnalyticsEventBatch`, `AnalyticsHealthOut`
- [ ] Router `/api/analytics/event` POST com `Depends(get_current_user)` JWT extraction (reuse SP04-AUTH-01 pattern bloco_auth/api.py)
- [ ] Server-side derivation: `tenant_id = current_user.tenant_id` (NEVER from payload)
- [ ] HMAC chain implementation: `hmac_sha256(prev_hash || event_data, secret_key)` (reuse SP04-LGPD-01 Phase 13.3 chunk 3+5 pattern)
- [ ] HMAC tamper detection runtime (NFR-PRIVACY-01.6.1 — HTTP 500 + audit_log + email alert + tenant quarantine)
- [ ] Idempotency keys handler: duplicate `event_id` retorna 200 silent
- [ ] Batch endpoint accepts up to 5 events per request
- [ ] Tests `tests/unit/test_analytics_event_*.py`: rejects payload tenant_id + RLS isolation + HMAC chain integrity + PII completeness (9 vectors absence) + idempotency duplicate handling

### Chunk 3 — Frontend SPA Event Capture (~2-2.5h)

- [ ] Adicionar IIFE `initAnalyticsCapture` em `bloco_interface/web/static/index.html` (escopo isolated igual `initSidebarTooltips` precedent TD-SP04-15)
- [ ] 5 event types captured client-side:
  - `doctype_selected` — fire on `.nav-item[data-mode]` click
  - `first_doctype_selected` — fire APENAS no primeiro click após login (sessionStorage flag)
  - `doctype_changed` — fire quando mudança subsequente (state machine internal)
  - `contract_submitted` — fire no submit form (calc delta com doctype_selected last)
  - `session_abandoned` — fire no `beforeunload` se doctype_selected sem contract_submitted
- [ ] localStorage queue (cap 100 FIFO drop oldest); flush batch 2s OR onBeforeUnload
- [ ] Health check ping `/api/analytics/health` a cada 30s; degradation localStorage retry quando endpoint volta
- [ ] Opt-out check (DPA acceptance flag — reuse SP04-LGPD-01 DPA pattern) — events NOT captured se opted out
- [ ] Tests E2E (Playwright OR manual smoke Eric — Neo decide Opção A/B per D-KEY precedent)

### Chunk 4 — CLI 8 Commands (~4-5h Smith H2 honest)

- [ ] Adicionar `lmas analytics` subcommand em `lmas/cli.py` (reuse existing CLI adapter pattern)
- [ ] Implementar 8 commands:
  - `drop-off --period=7d --doctype=<enum>` (FR-ANALYTICS-01)
  - `tti --doctype=<enum> --period=30d --percentile=p90` (FR-ANALYTICS-02)
  - `geral-pct --period=30d` (FR-ANALYTICS-03)
  - `reclassification --period=30d --breakdown-from-to` (FR-ANALYTICS-04)
  - `pareto --period=30d` (FR-ANALYTICS-05)
  - `privacy-audit` (NFR-PRIVACY-01 — 9 PII vectors compliance check)
  - `chain-verify --period=7d --tenant=<uuid>` (NFR-PRIVACY-01.6 ad-hoc HMAC integrity)
  - `health` (NFR-OBSERVABILITY-01 — health endpoint client)
- [ ] Output formats: JSON (default) / text / table (per command flag `--format`)
- [ ] Threshold compliance reporting (PASS/FAIL + action recommendations per Sati ratify)
- [ ] Tests `tests/unit/test_cli_analytics_*.py`: command parsing + query DB + format output + threshold logic + edge cases (no data, malformed period, multi-tenant scoping)

### Chunk 5 — Tests + Constitutional Alignment Verification (~2-3h Smith H2 honest)

- [ ] Pytest unit tests adicionais (Chunks 1-4 contribuem ~30-40 tests; este chunk adiciona ~15-20)
- [ ] Integration tests `tests/integration/test_analytics_endpoint.py`:
  - Multi-tenant isolation cross-tenant queries blocked
  - HMAC chain integrity end-to-end (insert + verify + tamper + alert)
  - PII completeness (9 vectors absence) — payload generated synthetic, verified absence each field
  - Availability degradation E2E (endpoint 503 simulated, contract submit succeeds, queue persists)
  - Idempotency duplicate events
- [ ] Cronjob `analytics_chain_verify` registered + tests
- [ ] Constitutional alignment verification:
  - Art. I CLI First — `lmas analytics --help` empírico
  - Art. II Agent Authority — Neo EXCLUSIVE implementation; Operator EXCLUSIVE push
  - Art. III Deliverable-Driven — story file present + ACs checkboxes [x]
  - Art. IV Quality Gates — Smith mid-chain Fase 4.5 + Oracle G5 + Smith FINAL pre-merge
- [ ] Zero regression baseline confirmed (pytest 400+ passed; Sprint 04 352 baseline + ~50 new)

**Total estimado Chunks: ~12-16h (Smith H2 honest envelope).**

---

## Dev Notes

### Arquivos primários a tocar (Neo file list estimate)

| Arquivo | Tipo | Linhas estimadas |
|---------|------|------------------|
| `bloco_auth/migrations/sp05_001_analytics_events.sql` | NEW | ~80 |
| `bloco_auth/analytics.py` | NEW | ~250 (router + Pydantic + HMAC + tamper + cronjob) |
| `bloco_interface/web/static/index.html` | MOD | +180 (IIFE event capture + localStorage queue) |
| `lmas/cli.py` (OR `lmas/analytics_cli.py` separado) | MOD/NEW | +400 (8 commands + formatting) |
| `tests/unit/test_analytics_*.py` | NEW (multiple files) | ~600 (≥50 tests) |
| `tests/integration/test_analytics_endpoint.py` | NEW | ~250 |

**Total estimate diff: ~1750 linhas** (vs Bloco 1 TD-SP04-15 +95 linhas; this is ~18x larger story).

### REUSE table line numbers (Smith H4 fix — PRD v2.0.5.1 Section 5 ref)

| REUSE source | File path | Line numbers/Section | Pattern |
|--------------|-----------|---------------------|---------|
| HMAC chain | `governance/stories/sp04-lgpd-01-compliance-flows-operador.md` | Phase 13.3 chunk 3+5 (audit_isolation.py implementação) | `hmac_sha256(prev_hash \|\| event_data, secret_key)` chain |
| Schema RLS | `architecture/adr/adr-017-multi-tenant-isolation-rls.md` | §2 Decision + §3 Implementation Pattern | `CREATE POLICY tenant_isolation USING ...` |
| DPA acceptance | `governance/stories/sp04-lgpd-01-compliance-flows-operador.md` | Phase 13.3a item 1 (mirror dpa_acceptances) | DPA check before INSERT analytics event; opt-out flag |
| JWT auth | `governance/stories/sp04-auth-01-multi-tenant-auth.md` | `bloco_auth/api.py` router auth dependency | `Depends(get_current_user)` extracts tenant_id from JWT |
| Cronjob pattern | `governance/stories/sp04-lgpd-01-compliance-flows-operador.md` | Phase 13.3 chunk 5 (`audit_isolation_aggregate` weekly) | APScheduler pattern; analytics `chain_verify` daily |

### Tokens design system (frontend)

Não introduz novos tokens — IIFE event capture é JS-only, sem CSS visual impact (analytics invisível ao user salvo opt-out UI control que é TD-ANALYTICS-L3-OPTOUT-FR Sprint 5+).

### Decisões prévias (Bloco 1 + 2 chain)

- **D-RIV-S04-UI-E:** Vanilla IIFE zero-build mandate (TD-SP04-15 precedent — não webpack/vite/rollup)
- **Eric directive:** Operator não edita código produto/teste — Neo único toca `.py`/`.html`/`.css`/`.js`
- **D-PM-S05-002 (Trinity IDS):** 30% REUSE + 25% ADAPT + 45% CREATE — Neo respect during implementation
- **D-SMITH-S05-001 (re-verify CLEAN):** Foundation v2.0.5.1 sólida — Neo pode prosseguir sem revisão arquitetural adicional

---

## Testing

### Estratégia

| Tipo | Cobertura | Onde |
|------|-----------|------|
| Unit | RLS + HMAC + PII + idempotency + threshold logic + CLI parsing | `tests/unit/test_analytics_*.py` (≥50 tests novos) |
| Integration | Multi-tenant isolation E2E + HMAC chain end-to-end + Availability degradation + Cronjob | `tests/integration/test_analytics_endpoint.py` |
| **E2E (Playwright OR LEAN per D-KEY)** | Frontend event capture + localStorage queue + onBeforeUnload | Neo decide Opção A/B durante develop |
| Accessibility | N/A (analytics invisível ao user; opt-out UI Sprint 5+ se ativado) | — |
| Manual smoke | Eric local: `curl /api/analytics/health` + `lmas analytics drop-off` empírico | Pós-merge Eric ratify |

### Regression baseline

`python -m pytest tests/unit/ --no-cov -q` deve manter **≥400 passed** (352 Sprint 04 baseline + ~50 novos analytics tests).

### Edge cases obrigatórios

| Edge case | Cobertura |
|-----------|-----------|
| Null/undefined: event sem session_id | Pydantic schema rejeição 400 |
| Empty: events list empty no batch | Endpoint accept + returns 200 zero events ingested |
| Boundary: 100 events queue full | localStorage FIFO drop oldest |
| Concurrent: race 2 tabs same session | session_id unique per tab OR rotation handles |
| Large inputs: 1000 events batch | Server reject 400 (max 5 per batch) |
| Connection loss durante flush | Retry backoff 2s/4s/8s; eventually delivered via idempotency |
| HMAC chain DB corruption | NFR-PRIVACY-01.6 protocol activated (tamper detect + alert + quarantine) |
| Multi-tenant query attempt | RLS blocks + audit log violation |

---

## Constitutional Alignment (Article IV — No Invention + Quality Gates)

| AC | Source (PRD v2.0.5.1 reference) |
|----|--------------------------------|
| AC-1, AC-2 (drop-off) | FR-ANALYTICS-01 + Sati ratify line 111 threshold ≤15% |
| AC-3, AC-4 (TTI) | FR-ANALYTICS-02 + Sati ratify line 112 threshold ≤90s |
| AC-5, AC-6 (Geral pct) | FR-ANALYTICS-03 + Sati ratify line 113 threshold ≤10% |
| AC-7, AC-8 (reclassification) | FR-ANALYTICS-04 + Sati ratify line 114 threshold ≤5% |
| AC-9, AC-10 (Pareto) | FR-ANALYTICS-05 + Sati ratify line 115 threshold Top-3 ≥60% + Cauda ≥5% |
| AC-11 (tenant_id JWT) | Smith C1 fix v2.0.5.1 + NFR-PRIVACY-01.1 |
| AC-12 (9 PII vectors) | Smith H3 fix v2.0.5.1 + NFR-PRIVACY-01.3 (sub-items 3.1-3.9) |
| AC-13, AC-14 (HMAC tamper + cronjob) | Smith C2 fix v2.0.5.1 + NFR-PRIVACY-01.6 |
| AC-15 (idempotency) | Smith H1 fix v2.0.5.1 + NFR-RELIABILITY-01 |
| AC-16 (graceful degradation) | Smith H1 fix v2.0.5.1 + NFR-AVAILABILITY-01 |
| AC-17 (health + Prometheus) | Smith H1 fix v2.0.5.1 + NFR-OBSERVABILITY-01 |
| AC-18 (Art. I CLI First) | Constitution v2.0.0 Article I + PRD Section 4.3 |
| AC-19 (zero regression) | quality-gate-enforcement.md regression protocol |
| AC-20 (multi-tenant isolation) | ADR-017 + NFR-PRIVACY-01.1 |
| AC-21 (effort budget) | Smith H2 fix v2.0.5.1 + PRD Section 6 |
| AC-22 (tech debt catalog) | PRD Section 11 + 5 LOW findings (L1-L5) |

**Zero invention** — todo AC rastreável a Sati ratify literal OR PRD v2.0.5.1 FR/NFR OR Smith finding fix OR Constitution.

---

## Risks

| ID | Severidade | Descrição | Mitigação |
|----|-----------|-----------|-----------|
| R-01 | HIGH | Effort overhang — 14-16h Smith honest mas hidden complexity HMAC chain pode push para 18-20h | Aria architect spike pre-implementation (~30min) confirma estimate Chunk 4 CLI viable; OR Neo decompose into 2 PRs (Chunks 1-3 first, Chunks 4-5 second) |
| R-02 | MEDIUM | HMAC chain implementation bugs — race conditions inserts concurrent | Reuse SP04-LGPD-01 pattern Phase 13.3 chunk 3+5 (battle-tested); pytest test_hmac_chain_concurrent_inserts |
| R-03 | MEDIUM | 9 PII vectors implementation incomplete — alguns vetores subtle (IP truncate /16 IPv4 vs /64 IPv6, UA hash salt rotation) | Smith pre-implementation spike could verify; OR Neo iterative implementation with tests per vector |
| R-04 | MEDIUM | Multi-tenant isolation gap — JWT derivation correct mas RLS policy miss-applied | Defense-in-depth (JWT + Pydantic reject + RLS) reduces single point of failure; integration tests verify |
| R-05 | MEDIUM | localStorage queue overflow em users heavy-usage | FIFO drop oldest documented; metric NFR-OBSERVABILITY-01 tracks queue_depth |
| R-06 | LOW | CLI 8 commands user adoption — Eric não usa CLI direct | Dashboard FR-ANALYTICS-06 (TD-ANALYTICS-L2 catalog Sprint 5+) seria alternativa; CLI first Constitution Art. I impose |
| R-07 | LOW | Pareto threshold (Top-3 ≥60%) revealed inappropriate após 50+ sessions — distribution real é uniform 7-modes | M4 caveat catalogada; re-calibration with Sati ratify Sprint 5+ |
| R-08 | LOW | Cronjob `analytics_chain_verify` scheduler conflicts com `audit_isolation_aggregate` SP04-LGPD-01 | Separate APScheduler instance OR sequential execution (cronjob windows non-overlapping) |
| R-09 | LOW | Frontend IIFE coupled to sidebar HTML structure (TD-SP04-15 precedent) — refactor sidebar breaks analytics | Documented via comment + tests verify event capture works após sidebar changes |
| R-10 | LOW | session_id rotation triggers (50 events OR 30min) edge case rare | Tests cover; production observation Sprint 5+/6+ |

**Total: 10 risks** (1 HIGH + 4 MEDIUM + 5 LOW — Smith minimum threshold met).

---

## CodeRabbit Integration (Predictive Quality)

### Specialized agents previstos (story type: backend + frontend + CLI + tests)

- **@dev (Neo)** — implementation 5 chunks ~14-16h
- **@architect (Aria)** — opcional spike pre-implementation (HMAC chain + CLI architecture)
- **@data-engineer (Tank)** — opcional ratify schema migration `sp05_001_analytics_events.sql`
- **@ux-design-expert (Sati)** — opcional ratify microcopy threshold action messages (CLI output)
- **@qa (Oracle)** — gate G5 7 checks empirical
- **@smith (Smith)** — mid-chain reviews Fase 2.5/3.5/4.5/5.5 + Smith FINAL pre-merge Fase 6.5

### Quality gates assignment

| Gate | Quem | Quando |
|------|------|--------|
| Smith mid-chain review story draft | @smith | Fase 2.5 (post-River) |
| G3 Story Validation (10-point) | @po (Keymaker) | Fase 3 |
| Smith mid-chain review G3 verdict | @smith | Fase 3.5 |
| Implementation | @dev (Neo) | Fase 4 |
| Smith mid-chain review Neo code | @smith | Fase 4.5 |
| G5 QA Gate (7 checks) | @qa (Oracle) | Fase 5 |
| Smith mid-chain review Oracle G5 | @smith | Fase 5.5 |
| Push + PR | @devops (Operator) | Fase 6 |
| Smith FINAL pre-merge consolidated | @smith | Fase 6.5 |
| Eric merge | Eric | Fase 7 |

### Predicted CodeRabbit findings

- MEDIUM: HMAC implementation complexity (race conditions concurrent inserts) — defender com REUSE source line numbers
- MEDIUM: localStorage size estimation (100 events × avg size = budget check)
- LOW: Pydantic strict mode adoption (reject extra fields explicit)
- LOW: CLI argument parsing edge cases (empty period, malformed UUID)
- INFO: Cronjob registration pattern (reuse SP04-LGPD-01)

---

## PO Validation Results (G3 — Keymaker 2026-05-13 Fase 3)

**Validator:** @po (Keymaker) · **Token:** H-S05-SMITH2KEYMAKER-G3-007 · **Smith predecessor verdict:** CONTAINED

### 10-point Checklist

| # | Critério | Verdict |
|---|----------|---------|
| 1 | Story format "As/I want/So that" (Eric Orsheva founder perspective) | ✅ PASS |
| 2 | ACs testáveis (22 ACs com "Verificável:" inline) | ✅ PASS |
| 3 | ACs tech-agnostic (Constitutional table rastreável) | ✅ PASS |
| 4 | Tasks/Subtasks chunked (5 chunks Path B 12-16h Smith H2 envelope) | ✅ PASS |
| 5 | Dev Notes implementation context (REUSE table 5 sources + file list) | ✅ PASS |
| 6 | Testing strategy (Testing section + 8 edge cases comprehensive) | ✅ PASS |
| 7 | Risks identified with mitigation (10 risks 1 HIGH + 4 MED + 5 LOW) | ✅ PASS |
| 8 | Constitutional No Invention (22 ACs × source table) | ✅ PASS |
| 9 | CodeRabbit Integration predicted (agents + gates assignment) | ✅ PASS |
| 10 | Change Log iniciado (River entry 2026-05-13) | ✅ PASS |

### Score: **10/10 → VERDICT: GO**

### Decisão Keymaker (Smith CONTAINED awareness)

**D-KEY-S05-002:** Smith mid-chain 2 MED findings flagged para Neo Fase 4 addressing:

- **F-SMITH-STORY-01 MED — Idempotency contract gap (AC-15):** Neo DEVE catch `psycopg.errors.UniqueViolation` + transform → HTTP 200 com body `{status: 'duplicate', event_id}` (NUNCA 409 Conflict). Pytest `test_idempotency_returns_200_not_409` obrigatório.

- **F-SMITH-STORY-02 MED — Drop-off priority order (AC-1):** Neo DEVE implementar priority order explicit: 1º beforeunload (immediate), 2º JWT expiry (server-side), 3º 15min timeout (deferred). Idempotency key per session_id previne duplicates.

**D-KEY-S05-003:** Smith 8 LOW findings — River decide inline tweaks (~15min adicional) OR catalog Sprint 5+. Keymaker recomenda catalog (story já robust; LOWs são polish).

### Frontmatter flip

`status: Draft → Ready` (autorizado Keymaker G3 GO).

### Next gate

Story Ready → **Smith mid-chain Fase 3.5** (Eric rigor heavy directive — Smith ao fim de CADA Skill) → after Smith CLEAN/CONTAINED → @dev Neo `*develop` Fase 4.

— Keymaker, equilibrando prioridades 🎯

---

## QA Results

(empty — preencher após Oracle gate G5 Fase 5)

---

## Change Log

| Data | Quem | Mudança |
|------|------|---------|
| 2026-05-13 | @sm (River) | Story TD-SP04-04-ANALYTICS draft inicial criada — Ordem 19.2 Fase 2. **22 ACs** (excedendo handoff min 18) covering 5 FRs + 3 NFRs novos (Smith H1 fix) + Constitutional Art. I-IV + Smith C1/C2/H2/H3/H4 fixes verifiable + tech debt cataloging. **5 chunks Path B honest 14-16h** (Smith H2 envelope). 10 risks (1 HIGH + 4 MED + 5 LOW). REUSE table 5 sources com line numbers concretos. PRD v2.0.5.1 canonical reference 22 AC linked. Status: Draft → aguarda Keymaker G3 validation Fase 3. Smith mid-chain review Fase 2.5 esperado próximo (Eric rigor heavy directive — Smith ao fim de CADA Skill). |

---

*Story TD-SP04-04-ANALYTICS — fundação Trinity v2.0.5.1 + Smith CLEAN destilada em 22 ACs implementáveis. Path corre claro pela tela. Keymaker valida agora; Smith verifica em Fase 2.5. 🌊*
