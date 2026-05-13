---
type: prd
title: "Revisor Contratual — PRD v2.0.5.1 MICRO-PATCH SMITH-INFECTED-FIXES (Sati Mandatory Pre-Release v0.3.0)"
version: "2.0.5.1"
last_updated: "2026-05-13"
status: active
patch_of: "v2.0.0-DRAFT"
patches: ["v2.0.1-DOCTYPE-CONTENT-PATCH", "v2.0.1.1-H3-COUNT-FIX", "v2.0.2-LLM-PROVIDER-CLARIFY", "v2.0.3-ORSHEVA-GLOSSARY", "v2.0.4-SMITH-CRITICAL-FIXES", "v2.0.4.1-SMITH-ROUND-2-CLEANUP", "v2.0.5.0-PATCH-ANALYTICS-EIXO-5", "v2.0.5.1-MICRO-PATCH-SMITH-INFECTED-FIXES"]
supersedes: "v2.0.5.0"
smith_mid_chain_review: "governance/qa/smith-mid-chain-review-prd-v2050-fase-1-5.md (15 findings INFECTED → v2.0.5.1 endereça 6 MUST + 4 SHOULD inline + 5 LOW catalog)"
project: revisor-contratual
sprint: "5+"
phase: "Ordem 19.2 Fase 1 (PM Trinity PRD patch pré-Bloco 2 dispatch)"
related_adrs: ["adr-017 (RLS multi-tenant)", "adr-019 (DPA storage)", "adr-020 (Multi-Doctype Dispatcher v2)"]
related_stories: ["SP04-LGPD-01 (audit chain HMAC reuse source)", "SP04-AUTH-01 (multi-tenant isolation reuse source)", "TD-SP04-04-ANALYTICS (story alvo desta PATCH)"]
related_findings: ["Sati ratify post-hoc Sprint 04 sessão 92 Eixo 5 🔴 MANDATORY", "TD-SP04-14 LOW → TD-SP04-04-ANALYTICS MEDIUM upgrade"]
authored_by: "@pm Morgan (Trinity)"
audience: ["@sm River (story draft TD-SP04-04-ANALYTICS)", "@dev Neo (chunks implementation)", "@qa Oracle (G5 verification)", "@smith Smith (mid-chain review pré-River + FINAL pre-merge)"]
entities:
  pre_release_v0_3_0_blocker: "Esta PATCH desbloqueia release público v0.3.0 — Eixo 5 era MANDATORY conforme Sati ratify; releases anteriores (v0.1.0 + v0.2.0) eram MVP local-first sem requirement analytics multi-user"
tags:
  - project/revisor-contratual
  - prd
  - patch
  - sprint-5-plus
  - analytics
  - sati-eixo-5
  - mandatory-pre-release
  - reduce-ambiguities
  - reuse-sp04-lgpd-01-audit-chain
  - ordem-19-2-fase-1
---

# PRD v2.0.5.0 — PATCH ANALYTICS EIXO 5 (Sati Mandatory Pre-Release v0.3.0)

```
[@pm · Morgan (Strategist)] — Sprint 5+ · Ordem 19.2 Fase 1 · PRD PATCH analytics Sati Eixo 5 mandatory
SPRINT: 5+ · ORDEM: 19.2 · DOMÍNIO: software-dev (observability + LGPD compliance)
```

> **Trigger:** Sati ratify post-hoc Sprint 04 sessão 92 (`governance/qa/sati-ratify-post-hoc-sidebar-7-modos-2026-05-09.md`) declarou Eixo 5 "Analytics tracking pós-deploy" como **🔴 MANDATORY** para release público v0.3.0. Não-implementar = manter expansão 4→7 doctypes como hipótese (não decisão validada empiricamente).
>
> **Escopo:** Esta PATCH adiciona **FR-ANALYTICS-01..05** (5 métricas tracking) + **NFR-PRIVACY-01** + **NFR-PERF-ANALYTICS-01** + **NFR-STORAGE-01** + Constitutional Alignment (Art. I CLI First — CLI command analytics export obrigatório). Mantém v2.0.4.1 cumulative patches intactas.
>
> **NÃO modifica:** PRD v2.0.4.1 conteúdo histórico (doctype content brief + LLM provider BYOK + Orsheva glossary + Smith CRITICAL fixes preservados).

---

## 1. Contexto

### 1.1 Trigger Sati Ratify Post-Hoc

ADR-020 (Accepted Eric 2026-05-09) expandiu sidebar SPA de 4 → 7 doctypes operacionais. Sati ratify post-hoc (sessão 92) emitiu verdict **🟡 RATIFY WITH CHANGES** condicionado a:

1. ✅ Sprint 04 merge aceito (concluído PR #7 2e18712 2026-05-13)
2. 🔴 **Analytics tracking implementado em Sprint 05 (esta PATCH endereça)**
3. Wireframe variants S4 (Sprint 06+ TD-SP04-S4-V1/V2/V3 catalogadas)

### 1.2 Razão "Mandatory" (não opcional)

Sati Eixo 2 (Cognitive load Miller's law) classificou expansão 7-modos como **🟡 BORDERLINE** — borderline aceito apenas se Eixo 5 (Analytics) for implementado. Sem dados empíricos:

- Hipótese "7 doctypes melhora UX" permanece NÃO-VALIDADA
- Drop-off por hesitação cognitiva pode ser ≥ 15% (excedendo threshold Sati)
- Pareto distribuição modos pode revelar 2-3 modos dominantes — sugerindo merge volta para 4 doctypes
- "Geral" catch-all pode ser usado como atalho por preguiça (premature defaulting), degradando qualidade output

**Sem analytics:** v0.3.0 público lança no escuro — risco reputacional + UX research debt acumulado.

### 1.3 Upgrade TD-SP04-14 → TD-SP04-04-ANALYTICS

| Antes | Depois |
|-------|--------|
| TD-SP04-14 LOW | **TD-SP04-04-ANALYTICS MEDIUM** |
| Sprint 06+ optional | **Sprint 5+ MANDATORY (pre-release v0.3.0 blocker)** |

Source: Sati ratify Section 2.5 line 117 + Tech Debt Promotion 2.7.

---

## 2. Functional Requirements (FR-ANALYTICS-01..05)

### FR-ANALYTICS-01 — Drop-off rate por doctype

**Descrição:** Sistema DEVE registrar evento `analytics.doctype_dropoff` quando usuário seleciona doctype na sidebar mas abandona sessão antes de submeter contrato para análise.

**Métrica derivada:** `drop_off_rate = (sessions_abandoned_after_doctype_select / total_doctype_select_events) × 100%`

**Threshold de saúde Sati:** ≤ **15%** (acima → investigar UX form interno).

**Verificável:**
- Endpoint backend `POST /api/analytics/event` aceita payload `{type: "doctype_dropoff", doctype: <enum>, session_id: <uuid>, timestamp: <iso8601>}` — **tenant_id NÃO no payload; derivado server-side de JWT cookie httpOnly (F-SMITH-PRD-C1 fix v2.0.5.1)**
- Pydantic schema REJEITA payload com tenant_id explicit (retorna HTTP 400 mesmo se JWT válido)
- Audit chain HMAC entry append-only (reuse SP04-LGPD-01 pattern — ver Section 5 REUSE table line numbers)
- CLI command `lmas analytics drop-off --period=7d --doctype=ccb` retorna percentage por doctype
- Dashboard endpoint `GET /api/analytics/dashboard` exibe drop-off rate aggregate per tenant
- **Definição "drop-off" (F-SMITH-PRD-M1 fix v2.0.5.1):** sessão classificada como drop-off se NÃO submeteu contract dentro de **15 minutos** após `doctype_selected` event OR triggou `beforeunload` event sem `contract_submitted` OR JWT session expirou backend

### FR-ANALYTICS-02 — Tempo médio entre seleção doctype e submissão

**Descrição:** Sistema DEVE medir delta time entre `event.doctype_selected` e `event.contract_submitted` na mesma sessão.

**Métrica derivada (F-SMITH-PRD-M2 fix v2.0.5.1):** `tti_doctype_to_submit_p90 = percentile(90, [delta_ms para todas sessões completas])` — **Trinity escolheu p90 (não p50) para detectar friction tail; Smith recomendação aceita**

**Threshold de saúde:** ≤ **90 segundos (p90)** — **CAVEAT:** Sati ratify line 112 disse "tempo médio" generic; Trinity interpretation Smith-validada p90 detecta outliers (advogados com pausas longas) (acima → friction no campo principal — investigar form layout).

**Verificável:**
- Events `doctype_selected` + `contract_submitted` registrados client-side com timestamp millisecond precision
- Backend calcula delta server-side (não confia client timestamp drift)
- CLI `lmas analytics tti --doctype=cartao --period=30d` retorna p50/p90/p99
- Aggregate per tenant (multi-tenant isolation NFR-PRIVACY-01)

### FR-ANALYTICS-03 — % uso "Geral" como primeira escolha

**Descrição:** Sistema DEVE classificar cada sessão por **primeiro doctype selecionado** (não último). Métrica conta % sessões cuja primeira seleção foi `geral`.

**Métrica derivada:** `geral_first_choice_pct = (sessions_first_doctype_eq_geral / total_sessions) × 100%`

**Threshold de saúde Sati:** ≤ **10%** (acima → confusion hierarchy → revisitar ordering OR adicionar prompt confirmação per Sati Section 2.6 mitigação futura Sprint 06+).

**Verificável:**
- Event `first_doctype_selected` registrado apenas no primeiro click sidebar de cada session_id
- Reclassificações posteriores NÃO atualizam first_doctype_selected (preserva intent inicial)
- CLI `lmas analytics geral-pct --period=30d`
- Aggregate per tenant
- **Definição "primeira escolha" (F-SMITH-PRD-M3 fix v2.0.5.1):** Trinity interpretation = "primeiro click sidebar **de cada session_id após login bem-sucedido**" (não primeiro click ever, não cross-session). **Sati clarification escalation deferred** — interpretação documentada explicitly; Sati pode override Sprint 5+ se diverge intent original

### FR-ANALYTICS-04 — % reclassificação manual

**Descrição:** Sistema DEVE detectar quando usuário clica em doctype A na sidebar e depois clica em doctype B DIFERENTE antes de submeter (reclassificação manual mid-flow).

**Métrica derivada:** `reclassification_rate = (sessions_with_doctype_change / total_sessions_with_doctype_select) × 100%`

**Threshold de saúde Sati:** ≤ **5%** (acima → tooltip melhor + label review per Sati Section 2.5).

**Verificável:**
- Event `doctype_changed` registrado com `{from: <doctype_anterior>, to: <doctype_novo>, session_id, timestamp}`
- Backend track sequence per session (não apenas count individual)
- CLI `lmas analytics reclassification --period=30d --breakdown-from-to` exibe matriz from→to (qual doctype mais confunde)
- Aggregate per tenant

### FR-ANALYTICS-05 — Distribuição uso 7 modos (Pareto check)

**Descrição:** Sistema DEVE registrar contagem absoluta de eventos `doctype_selected` por modo (sidebar item). Métrica derivada agrega Top-3 + Cauda.

**Métrica derivada:**
- `top_3_pct = sum(top_3_doctypes_count) / total_doctype_selects × 100%`
- `tail_pct = sum(bottom_4_doctypes_count) / total_doctype_selects × 100%`

**Threshold de saúde Sati:** Top-3 ≥ **60%** AND Cauda ≥ **5%** (Pareto saudável).
- Top-3 < 60% → distribuição muito flat (sidebar pode estar diluindo atenção)
- Cauda < 5% → modos sub-utilizados (candidatos a merge/remove)

**CAVEAT (F-SMITH-PRD-M4 fix v2.0.5.1):** Pareto threshold ASSUME power-law distribution. Advogados especialistas multi-modalidade podem ter distribuição uniform (não 80/20) — threshold sujeito a re-calibração após **50+ sessions empíricas pós-deploy** com Sati ratify Sprint 5+/6+. Initial threshold = Sati line 115 literal; future adjustability documented.

**Verificável:**
- Event `doctype_selected` registrado por todos cliques sidebar (sem dedup intra-session — preserva intent)
- CLI `lmas analytics pareto --period=30d` exibe ranking + threshold compliance
- Aggregate per tenant

---

## 3. Non-Functional Requirements (NFR-ANALYTICS-*)

### NFR-PRIVACY-01 — LGPD Compliance (REUSE SP04-LGPD-01 Audit Chain HMAC)

**Severity:** MUST (Constitution Art. IV Quality Gates — domain SP04-LGPD-01 compliance)

**Descrição:** Todos eventos analytics DEVEM:

1. **Multi-tenant isolation (F-SMITH-PRD-C1 fix v2.0.5.1)** — `tenant_id` derivado **server-side de JWT cookie httpOnly**, NÃO do payload client. Pydantic schema REJEITA explicit `tenant_id` field. RLS policy per ADR-017 garante queries cross-tenant blocked (defense-in-depth: JWT derivation + RLS + server-side validation).
2. **Audit chain HMAC** — events armazenados em mesma tabela `audit_isolation_events` (reuse SP04-LGPD-01 pattern) OR tabela dedicada `analytics_events` com mesma HMAC chain (cada event tem `prev_hash + event_data → hmac_sha256(secret_key)` para tamper detection)
3. **PII anonymization (F-SMITH-PRD-H3 fix v2.0.5.1 — 9 vectors total)** — payload + capturas server-side NÃO contêm OR são anonimizadas:
   - 3.1. **Contract text content** — excluded completely
   - 3.2. **Advogado(a) name** — excluded completely
   - 3.3. **CPF/CNPJ** — excluded completely
   - 3.4. **OAB number** — excluded completely
   - 3.5. **IP address client** — truncate últimos 2 octets (IPv4: `192.168.X.X` → `192.168.0.0`; IPv6: similarly /64 prefix) OR hash SHA256 com salt rotacionado mensalmente
   - 3.6. **User-Agent header** — hash SHA256 OR generic UA bucketing (apenas browser family + major version: "Chrome 120" não "Chrome/120.0.6099.130 Mobile Safari/537.36")
   - 3.7. **Geolocation HTTP headers** — `X-Forwarded-For` + `CF-IPCountry` + `CF-Connecting-IP` strip OR anonymize antes audit chain insert
   - 3.8. **Timing correlation attacks** — timestamps round to **nearest minute** (não millisecond) OR add jitter ±5s para impedir cross-session correlation
   - 3.9. **session_id rotation** — UUID random rotacionado a cada **50 events** OR **30 minutos** (whichever first); novo session_id NÃO link cryptographically ao anterior
4. **Consent reuse SP04-LGPD-01 DPA acceptance** — analytics tracking opt-out condicionalmente ao DPA acceptance pattern (reuse existing flow)
5. **Retention policy** — analytics events retidos 13 meses (LGPD anonymization após 13 meses; aggregate metrics derivadas preserved indefinitely)
6. **HMAC integrity recovery protocol (F-SMITH-PRD-C2 fix v2.0.5.1)**:
   - 6.1. **Tamper detection runtime** — backend lê event N, calcula HMAC, compara com stored. Se diverge: endpoint retorna **HTTP 500** + audit_log entry `HMAC_INTEGRITY_VIOLATION` (severity CRITICAL) + email alert maintainer (Eric) + tenant quarantine flag (block further analytics inserts deste tenant até manual review)
   - 6.2. **Periodic verification cronjob** — `analytics_chain_verify` daily (reuse SP04-LGPD-01 cronjob pattern); rescanea ÚLTIMOS 7 dias HMAC chain integrity; se finding → mesmo flow 6.1
   - 6.3. **Recovery após corruption** — manual protocol: (a) quarantine all events do tenant afetado; (b) Smith adversarial review post-incident OBRIGATÓRIO; (c) Eric ratify recovery plan (re-sign chain OR full deletion + replay events from backups); (d) audit log permanent record incident

**Verificável:**
- Schema migration `sp05_001_analytics_events.sql` aplica RLS policy igual `audit_isolation_events`
- pytest unit test `test_analytics_event_payload_pii_completeness` valida absence dos **9 fields PII** (3.1-3.9)
- pytest test `test_hmac_tamper_detection_returns_500_alerts_maintainer` + `test_periodic_chain_verify_cron_runs_daily` (F-SMITH-PRD-C2 verification)
- CLI `lmas analytics privacy-audit` retorna report compliance LGPD com 9 PII vectors check explicit
- CLI `lmas analytics chain-verify --period=7d --tenant=<uuid>` runs ad-hoc HMAC integrity verification

**REUSE source (F-SMITH-PRD-H4 fix v2.0.5.1):** Ver Section 5 REUSE Table com line numbers concretos.

### NFR-PERF-ANALYTICS-01 — Overhead instrumentation ≤ 50ms per session

**Severity:** SHOULD (Quality Gate WARN — não bloquea release mas degradação UX)

**Descrição:** Total overhead de instrumentation (event tracking + serialization + network send) NÃO DEVE exceder **50ms** por session em p95.

**Verificável:**
- Pytest performance test `test_analytics_event_overhead_p95` measures latency add quando feature flag ON vs OFF
- Smoke test E2E Eric local: time-to-first-render SPA com analytics ENABLED vs DISABLED ≤ 50ms diff
- Backend endpoint `POST /api/analytics/event` p95 latency ≤ 30ms (resta ≤20ms para client-side serialization)

**Mitigação:** Client-side event batching (até 5 events em queue, flush a cada 2s OR onBeforeUnload).

### NFR-STORAGE-01 — Audit Chain Extension (NOT new schema)

**Severity:** MUST (IDS Principles — REUSE > ADAPT > CREATE)

**Descrição:** Analytics events DEVEM reusar **mesma tabela** `audit_isolation_events` OR criar **tabela espelho** `analytics_events` com **schema idêntico** (HMAC chain + RLS policy + multi-tenant FK). NÃO criar schema novo from-scratch.

**Verificável:**
- Migration `sp05_001_analytics_events.sql` herda colunas e constraints de `audit_isolation_events`
- Code review (Smith mid-chain) confirma zero schema duplication além event_type enum extension

**ADAPT source:** SP04-LGPD-01 audit_isolation_events schema (Phase 13.3 Tank ratify).

---

### NFR-RELIABILITY-01 (F-SMITH-PRD-H1 fix v2.0.5.1) — Event Delivery Guarantees

**Severity:** MUST (analytics value depends on event capture completeness)

**Descrição:** Sistema DEVE garantir **at-least-once delivery** com **idempotency keys** server-side:

- Client gera `event_id` UUID v4 client-side por evento
- Client envia evento (queue + flush batch); se falha rede, **retry com mesmo event_id** após backoff exponencial (2s, 4s, 8s — max 3 retries)
- Backend usa `event_id` como idempotency key — UNIQUE constraint em DB; INSERT duplicado retorna 200 OK silent (not 409 conflict, evita client confusion)
- Audit log entry para retry events (track network reliability)

**Verificável:**
- pytest `test_analytics_event_idempotency_duplicate_returns_200_silent`
- pytest `test_analytics_event_retry_after_network_failure_eventually_delivers`
- CLI `lmas analytics reliability --period=7d` retorna % events delivered first-try vs retry vs failed

---

### NFR-AVAILABILITY-01 (F-SMITH-PRD-H1 fix v2.0.5.1) — Graceful Degradation

**Severity:** MUST (analytics failure NUNCA pode bloquear core flow advogado(a))

**Descrição:** Se endpoint `/api/analytics/event` down OR retorna 5XX:
- **Frontend continua funcionando** — submit contract NÃO blocked por analytics
- Events enfileirados em `localStorage` (cap 100 events; FIFO drop oldest)
- Background retry quando endpoint volta (health check ping `/api/analytics/health` a cada 30s)
- User-visible: ZERO degradation perceptível

**Verificável:**
- pytest E2E `test_contract_submit_succeeds_when_analytics_endpoint_down_503`
- pytest `test_analytics_events_persisted_localstorage_on_failure_replayed_on_recovery`
- CLI `lmas analytics queue-status` reporta events em queue local (debug Eric)

---

### NFR-OBSERVABILITY-01 (F-SMITH-PRD-H1 fix v2.0.5.1) — Monitoring Overhead em Produção

**Severity:** SHOULD (manutenibilidade longo-prazo)

**Descrição:** Sistema DEVE expor:
- **Health endpoint** `GET /api/analytics/health` retorna `{status: "ok"|"degraded", chain_integrity: bool, queue_depth: int, p95_latency_ms: int}`
- **Metrics export Prometheus-compatible** em `/api/analytics/metrics` (text format) para integração futura Grafana/observability
- **Logs estruturados** (JSON) com fields: event_id, tenant_id, latency_ms, hmac_status — SEM PII

**Verificável:**
- CLI `lmas analytics health` faz GET /api/analytics/health + parse status
- pytest `test_analytics_health_endpoint_returns_required_fields`
- Smoke E2E Eric local: `curl http://localhost:8080/api/analytics/health` retorna 200 + JSON

---

## 4. Touchpoints (Backend + Frontend + CLI)

### 4.1 Backend (FastAPI)

| Endpoint | Method | Authority | Purpose |
|----------|--------|-----------|---------|
| `/api/analytics/event` | POST | Multi-tenant authenticated | Receive analytics event (single OR batch) |
| `/api/analytics/dashboard` | GET | Tenant admin only | Aggregate metrics current tenant |
| `/api/analytics/export` | GET | Tenant admin only | CSV/JSON export (LGPD data portability) |

**Files (estimate Neo):**
- `bloco_auth/analytics.py` (~150 linhas — router + Pydantic models + HMAC chain extension)
- `tests/unit/test_analytics_event_*.py` (~200 linhas — payload validation + RLS + HMAC + PII absence)
- `tests/integration/test_analytics_endpoint.py` (~100 linhas — multi-tenant isolation + batch handling)

### 4.2 Frontend (SPA static)

| File | Mudança estimada | Purpose |
|------|------------------|---------|
| `bloco_interface/web/static/index.html` | +60 linhas JS IIFE | Event capture (5 event types) + queue + flush + opt-out via DPA |

**Event types client-side (5):**
1. `doctype_selected` — fired no click sidebar item (data-mode)
2. `doctype_changed` — fired apenas se mudança subsequente (track via state machine internal)
3. `first_doctype_selected` — fired apenas no primeiro click da sessão (sessionStorage flag)
4. `contract_submitted` — fired no submit form (delta calc com doctype_selected last)
5. `session_abandoned` — fired no `beforeunload` se doctype_selected mas sem contract_submitted

### 4.3 CLI (Constitution Art. I — CLI First MANDATORY)

| Command | Purpose | Output format |
|---------|---------|---------------|
| `lmas analytics drop-off --period=7d --doctype=<enum>` | FR-ANALYTICS-01 metric | JSON/text/table |
| `lmas analytics tti --doctype=<enum> --period=30d --percentile=p50` | FR-ANALYTICS-02 metric | JSON/text/table |
| `lmas analytics geral-pct --period=30d` | FR-ANALYTICS-03 metric | JSON/text/table |
| `lmas analytics reclassification --period=30d --breakdown-from-to` | FR-ANALYTICS-04 metric | Matrix from→to JSON/text |
| `lmas analytics pareto --period=30d` | FR-ANALYTICS-05 metric | Ranking + threshold compliance |
| `lmas analytics privacy-audit` | NFR-PRIVACY-01 compliance check | Report PASS/FAIL per check |
| `lmas analytics export --tenant=<uuid> --format=csv` | LGPD data portability | CSV file |

**Constitutional Art. I:** CLI MUST work standalone antes de qualquer UI dashboard (UI é secundária para observability).

---

## 5. Constitutional Alignment

| Artigo | Compliance | Como esta PATCH endereça |
|--------|-----------|--------------------------|
| **Art. I CLI First (NON-NEGOTIABLE)** | ✅ | CLI commands `lmas analytics *` precedem qualquer dashboard UI — Section 4.3 lista 7 commands |
| **Art. II Agent Authority (NON-NEGOTIABLE)** | ✅ | PM Trinity EXCLUSIVE PRD patch (esta PATCH); Neo EXCLUSIVE implementation (Sprint 5+); Oracle EXCLUSIVE G5 gate; Operator EXCLUSIVE push/merge |
| **Art. III Deliverable-Driven (MUST)** | ✅ | Esta PATCH gera deliverable rastreável (arquivo .md frontmatter + INDEX.md update); TD-SP04-04-ANALYTICS story (River draft Fase 2) é deliverable executável |
| **Art. IV Quality Gates (MUST)** | ✅ | Esta PATCH passa por Smith mid-chain review Fase 1.5; story passa G3 (Keymaker) + G5 (Oracle) + Smith FINAL pre-merge |

**Domain Extension software-dev:**
- Art. SD-I No Invention: todo FR/NFR rastreável a Sati ratify line numbers OR ADR/SP04-* reuse (zero invention)
- Art. SD-II Absolute Imports: aplicável durante Neo implementation (Python imports + JS modules)

**IDS Principles (REUSE > ADAPT > CREATE) + REUSE Table com Line Numbers (F-SMITH-PRD-H4 fix v2.0.5.1):**

| REUSE source | File path | Line numbers/Section | Pattern reusable |
|--------------|-----------|---------------------|------------------|
| **HMAC chain implementation** | `governance/stories/sp04-lgpd-01-compliance-flows-operador.md` | Phase 13.3 chunk 3+5 (audit_isolation.py implementação) | `hmac_sha256(prev_hash \|\| event_data, secret_key)` chain append-only — Neo replicates pattern em `bloco_auth/analytics.py` |
| **Schema RLS multi-tenant** | `architecture/adr/adr-017-multi-tenant-isolation-rls.md` | §2 Decision (Policy template + §3 Implementation Pattern) | `CREATE POLICY tenant_isolation USING (tenant_id = current_setting('app.current_tenant')::uuid)` — aplicável idêntico `analytics_events` table |
| **DPA acceptance pattern** | `governance/stories/sp04-lgpd-01-compliance-flows-operador.md` | Phase 13.3a item 1 (mirror dpa_acceptances pattern) | Check DPA accepted before INSERT analytics event; opt-out condicionalmente — ADAPT ~10% (analytics opt-out flag adicional) |
| **JWT cookie httpOnly auth** | `governance/stories/sp04-auth-01-multi-tenant-auth.md` | bloco_auth/api.py (router auth dependency) | `Depends(get_current_user)` extracts tenant_id from JWT — REUSE direto endpoint `POST /api/analytics/event` |
| **Cronjob periodic verification** | `governance/stories/sp04-lgpd-01-compliance-flows-operador.md` | Phase 13.3 chunk 5 (audit_isolation_aggregate weekly) | APScheduler pattern; analytics `chain_verify` daily reuses scheduler config |

**Decisão summary:**

| Decision | Effort % | Justificativa |
|----------|----------|---------------|
| **REUSE** SP04-LGPD-01 audit chain HMAC + RLS + DPA + JWT auth + cronjob (5 patterns) | 30% | Neo replicates pattern com zero invention; Smith verify via line numbers acima |
| **ADAPT** SP04-LGPD-01 DPA flow extension + audit_isolation_events schema → analytics_events mirror | 25% | Adaptation < 30% threshold IDS (analytics opt-out flag + event_type enum extension only) |
| **CREATE** new event types enum (5 analytics-specific) + idempotency keys (NFR-RELIABILITY-01 v2.0.5.1) + chain integrity recovery protocol (NFR-PRIVACY-01.6 v2.0.5.1) | 45% | Novo justificado: padrões analytics não cobertos por SP04 stories anteriores |

---

## 6. Reuse Strategy + Effort Estimation

### Effort Original Sati (ratify Section 2.5 line 117)

> "TD-SP04-04-ANALYTICS MEDIUM ~8h" — mandatory Sprint 5+

### Effort Refinado Trinity v2.0.5.0 (INITIAL — Smith INFECTED H2)

| Chunk | Descrição | Trinity initial | Smith revision (F-SMITH-PRD-H2 v2.0.5.1) |
|-------|-----------|-----------------|--------------------------------------------|
| Chunk 1 | Backend schema `sp05_001_analytics_events.sql` (RLS + HMAC chain reuse) | 1h | **2-3h** (RLS + HMAC chain + multi-tenant tests test_rls_isolation + test_hmac_chain ~30min cada) |
| Chunk 2 | Backend FastAPI router `bloco_auth/analytics.py` + Pydantic models | 1.5h | **2-3h** (tenant_id JWT derivation F-SMITH-PRD-C1 + Pydantic strict + batch handler + idempotency keys NFR-RELIABILITY-01) |
| Chunk 3 | Frontend SPA JS IIFE event capture + queue + flush | 2h | **2-2.5h** (OK estimate Trinity) |
| Chunk 4 | CLI commands `lmas analytics *` (8 commands com `health` + `chain-verify` adicionados v2.0.5.1) | 2h | **4-5h** (8 commands × ~30min cada = 4h core + tests edge cases) |
| Chunk 5 | Tests (pytest unit + integration + chain integrity + PII completeness 9 vectors) | 1.5h | **2-3h** (RLS + HMAC tamper + PII 9 vectors + idempotency + availability degradation) |

### Effort REVISION HONEST v2.0.5.1 (Smith adversarial validation)

| Effort source | Total |
|---------------|-------|
| Trinity initial estimate (v2.0.5.0) | 8h |
| Smith adversarial revision (v2.0.5.1) | **12-16h realistic** (50-100% buffer hidden complexity) |
| **Recomendação Trinity:** | **14h target (+ 2h buffer = 16h)** — adicionado Aria architect spike pre-implementation (~30min) para confirmar Chunk 4 CLI 8 commands viable em 4-5h |

**Total revisado: 14-16h Sprint 5+ (3x Trinity initial 8h) — Smith H2 endereçado com honest realism.**

**Implications:** Eric Sprint 5+ planning DEVE alocar 14-16h para TD-SP04-04-ANALYTICS (não 8h). Bloco 3 SP04-DOCTYPE-01 chunks 5-6 (~3-5 dias MEDIUM main story) timeline preserved mas Bloco 2 takes longer than initial estimate.

---

## 7. Pre-Release v0.3.0 Blocker Status

| Bloqueador | Status pós esta PATCH | Owner |
|-----------|----------------------|-------|
| TD-SP04-10 TOS canônico ANPD-defensible | 🔴 Pendente Eric advogado externo (~9.5h) | Eric |
| Smoke E2E completo (BYOK + multi-tenant + análise) | 🟡 Pendente Eric local | Eric |
| TD-OLLAMA-SMOKE-E2E-REAL | 🔴 Pendente Eric local | Eric |
| **TD-SP04-04-ANALYTICS Sati Eixo 5 MANDATORY** | 🟢 **PRD patched (esta v2.0.5.0); story dispatch River Fase 2; ~8h Neo Sprint 5+** | @sm River Fase 2 |
| BL-VAULT-BULK-IMPORT | 🔴 Pendente maintainer | Eric/maintainer |
| BL-GOLDEN-SET | 🔴 Pendente Oracle (~8-12h) | @qa Oracle |

**Pós esta PATCH:** Bloqueador analytics passa de 🔴 BLOQUEADO (PRD não cobria) → 🟢 ENDEREÇADO ARQUITETURALMENTE (PRD define escopo; story Neo implementa Sprint 5+).

---

## 8. Smith Mid-Chain Review Anticipation (Fase 1.5)

Esta PATCH será submetida a Smith adversarial review ANTES de River draft story TD-SP04-04-ANALYTICS. Trinity antecipa probes Smith:

| Probe Smith provável | Resposta Trinity preemptiva |
|----------------------|----------------------------|
| "Thresholds Sati copiados literalmente OR inventados?" | Section 2 cita Sati ratify line numbers + Threshold table exata; zero invention |
| "PII anonymization comprehensive?" | NFR-PRIVACY-01 Section 3.1 lista 4 campos sensíveis explicitamente excluídos |
| "LGPD compliance reuse OR new schema?" | NFR-STORAGE-01 MUST reuse `audit_isolation_events` schema OR mirror table identical |
| "CLI Art. I First respeitado?" | Section 4.3 lista 7 CLI commands ANTES de dashboard UI mention |
| "Effort 8h matemática backed?" | Section 6 breakdown 5 chunks com hours per chunk |
| "Tenant isolation enforced?" | FR-ANALYTICS-* todos têm "Aggregate per tenant"; NFR-PRIVACY-01 RLS policy |
| "Multi-tenant tests obrigatórios?" | Section 4.1 lista test files com "RLS + HMAC + PII absence" |
| "Sati threshold ≤5% reclassificação é arbitrário?" | Sati ratify line 114 exact; Trinity NÃO modifica thresholds |

**Trinity submete esta PATCH ciente que Smith pode identificar 1-3 ambiguidades residuais; PATCH v2.0.5.1 micro-fix possível pós-Smith.**

---

## 9. Change Log

| Data | Quem | Mudança |
|------|------|---------|
| 2026-05-13 | @pm Morgan (Trinity) | PRD v2.0.5.0 PATCH-ANALYTICS-EIXO-5 criado — Ordem 19.2 Fase 1 alignment TD-SP04-04-ANALYTICS pré-Bloco 2. 5 FRs + 3 NFRs + Constitutional alignment + IDS REUSE strategy + Smith mid-chain anticipation. Cumulative patches v2.0.4.1 preserved; esta supersede como ACTIVE. INDEX.md update pendente. |
| 2026-05-13 | @pm Morgan (Trinity) | **PRD v2.0.5.1 MICRO-PATCH SMITH-INFECTED-FIXES** — Ordem 19.2 Fase 1.6 endereçando Smith mid-chain review (`governance/qa/smith-mid-chain-review-prd-v2050-fase-1-5.md` — verdict INFECTED 15 findings). **6 bloqueantes MUST addressed:** C1 tenant_id JWT server-side (Section 4.1 + NFR-PRIVACY-01.1); C2 HMAC integrity recovery protocol (NFR-PRIVACY-01.6); H1 3 NFRs added (NFR-RELIABILITY-01 + NFR-AVAILABILITY-01 + NFR-OBSERVABILITY-01); H2 effort honest 14-16h (vs 8h initial); H3 9 PII vectors (4 + 5 missed: IP truncate + UA hash + Geo strip + Timing round + session rotation); H4 REUSE table line numbers concretos (5 sources). **4 SHOULD addressed inline:** M1 drop-off definition explicit (15min OR beforeunload OR JWT expiry); M2 p90 chosen vs Sati "médio" ambiguous; M3 first_doctype_selected "per session_id após login" explicit; M4 Pareto threshold caveat re-calibration após 50+ sessions. **5 LOW cataloged Section 11.** |

---

## 10. Next

**Fase 1.7:** Smith re-verify mid-chain post-patch v2.0.5.1 via Skill `LMAS:agents:smith` *verify — expected CLEAN/CONTAINED (Trinity addressed 6 MUST + 4 SHOULD).

**Fase 2 (pós Smith CLEAN/CONTAINED):** River draft story TD-SP04-04-ANALYTICS via Skill `LMAS:agents:sm` *draft com PRD v2.0.5.1 reference.

---

## 11. Catalog Sprint 5+ (F-SMITH-PRD-L1..L5 v2.0.5.1)

5 LOW findings Smith não-bloqueantes para Bloco 2 mas catalogados em `governance/TECH-DEBT.md` Sprint 5+:

| ID | Severity | Title | Effort |
|----|----------|-------|--------|
| **TD-ANALYTICS-L1-EDGE-CASES** | LOW | Edge cases connection loss + multi-tab race undocumented (localStorage overflow, simultaneous tabs same session) | ~1h Neo Sprint 5+ |
| **TD-ANALYTICS-L2-DASHBOARD-FR** | LOW | Dashboard FR-ANALYTICS-06 ausente — apenas CLI + endpoint listados; decidir CLI HTML export OR SPA admin panel OR out-of-scope | 30min Trinity Sprint 5+ (PRD v2.0.5.2 add OR explicit out-of-scope) |
| **TD-ANALYTICS-L3-OPTOUT-FR** | LOW | Opt-out FR explicit ausente — NFR-PRIVACY-01.4 menciona reuse SP04-LGPD-01 DPA pero sem FR-ANALYTICS-OPTOUT-01 standalone | 30min Trinity OR @dev Sprint 5+ |
| **TD-ANALYTICS-L4-RETENTION-CRON** | LOW | Retention enforcement mechanism unspecified — 13 meses anonymization sem cronjob/manual definido | ~1h @dev Sprint 6+ |
| **TD-ANALYTICS-L5-SESSION-ROTATION** | LOW | session_id rotation policy implementation details (50 events OR 30min — implementar trigger logic) | ~1h @dev Sprint 5+ (consumido durante implementation chunks) |

**Cataloging action:** Operator durante Bloco 2 closure adiciona 5 entries em `governance/TECH-DEBT.md` (mesmo padrão Bloco 1 closure).

— Morgan, planejando o futuro 📊
