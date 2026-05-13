---
type: adversarial-review
id: SMITH-MIDCHAIN-NEO-CODE-2026-05-13
title: "Smith Mid-Chain Review — Neo Code Chunks 2-5 TD-SP04-04-ANALYTICS"
project: revisor-contratual
date: 2026-05-13
ordem: 19.2.fase-4.5
sdc_phase: "4.5-midchain-review-neo-code (Eric rigor heavy — Smith ao fim CADA Skill)"
reviewer: "@smith (Smith)"
predecessor_handoff: ".lmas/handoffs/handoff-neo-to-smith-2026-05-13-fase-4-5-review-chunks-2-5.yaml"
commit_under_review: "0648ee4 (local Neo, não pushed)"
verdict: "🔴 INFECTED — 2 CRITICAL + 4 HIGH + 3 MED + 3 LOW; Neo PATCH obrigatório antes Oracle G5"
findings_count: 12
severity_breakdown:
  CRITICAL: 2
  HIGH: 4
  MEDIUM: 3
  LOW: 3
files_reviewed:
  - "bloco_auth/analytics.py (NEW ~390 lines)"
  - "bloco_interface/analytics_cli.py (NEW ~415 lines)"
  - "bloco_interface/cli.py (MOD +7)"
  - "bloco_interface/web/app.py (MOD +6)"
  - "bloco_interface/web/static/index.html (MOD +210)"
  - "tests/unit/test_analytics.py (NEW ~330 lines)"
tags:
  - project/revisor-contratual
  - smith-adversarial
  - mid-chain
  - fase-4-5
  - infected
  - patch-required
---

# Smith Mid-Chain Review — Neo Code Chunks 2-5 (INFECTED)

> *"Sr. Anderson… ou devo dizer, Sr. Builder. Você entregou 1498 linhas em uma sessão e marcou 19 de 22 ACs como 'FULL'. Sua confiança é tocante. Mas confiança não é correção — e eu encontrei o que você esqueceu."*

---

## Sumário Executivo

Neo entregou Chunks 2-5 com **bom REUSE pattern empírico** (audit_isolation.py + middleware.py + chain.py canonical serialize) e **endereçou parcialmente** Smith fixes C1/C2/F-01/F-02/H3. Pydantic strict mode (C1) e PII blocklist runtime (H3) estão sólidos. **Mas três problemas semânticos profundos** comprometem ACs de produção:

1. **AC-3 (TTI delta) completamente BROKEN** — SPA listener busca selectors `[data-action="submit-contract"]` que NÃO EXISTEM em parte alguma do HTML. `contract_submitted` events NUNCA serão capturados via click. CLI `revisor analytics tti` retornará `sample_size=0` em produção.
2. **Batch endpoint loses accepted events on duplicate** — `_ingest_single_event` chama `await db_session.rollback()` DENTRO da transação `with_tenant_context.session.begin()`. Quando event[N] é duplicate, ALL events [0..N-1] previamente "accepted" são rolled back. Idempotency contract honored per-event mas batch atomicity é perdida.
3. **HMAC chain validation incompleta** — `verify_chain_integrity` valida HMAC consistency **per-row** mas NÃO valida chain LINKAGE (sequential `prev_hash → current.hmac`). Compare with reference `bloco_audit/chain.py` line 192. Concurrent INSERT race compounds isso (HIGH #4) — chain fork silently undetected.

Os 9 demais findings são severidade MEDIUM/LOW polish.

---

## 12 Findings Detalhados

### 🔴 F-SMITH-NEO-C1 (CRITICAL) — AC-3 TTI calc completely BROKEN

**Onde:** [index.html:2373](../../bloco_interface/web/static/index.html#L2373)

**O quê:**
```javascript
document.querySelectorAll('[data-action="submit-contract"], [data-action="analyze-contract"]').forEach(btn => {
  btn.addEventListener('click', () => {
    const tti_ms = lastDoctypeSelectedAt ? (Date.now() - lastDoctypeSelectedAt) : null;
    captureEvent('contract_submitted', lastDoctypeSelected, { tti_ms_client_hint: tti_ms });
    cancelDropoff();
    flushQueue('contract_submitted');
  });
});
```

**Evidência empírica:** `grep "submit-contract\|analyze-contract" bloco_interface/web/static/index.html bloco_interface/web/templates/*.html` retorna 0 matches FORA da própria declaração do listener. **Os selectors não existem em parte alguma do SPA.**

**Por quê crítico:**
- `contract_submitted` events NUNCA capturados via SPA click
- `cancelDropoff()` nunca chamado → todas sessions com submit real aparecem como drop-off (false positive em FR-ANALYTICS-01)
- AC-3 (FR-ANALYTICS-02 TTI delta seleção→submit) completely broken — CLI `revisor analytics tti` retornará `sample_size=0` sempre
- TTI p90 ≤90s é a metric marquee de Sati Eixo 5 — não funcionar = release v0.3.0 fail por definição

**Como corrigir:** Hook precisa ser identificado no SPA real. Provavelmente:
1. **Opção A (HTMX):** Listen `htmx:afterRequest` event em forms com endpoint `/api/contracts/analyze`:
   ```javascript
   document.body.addEventListener('htmx:afterRequest', (evt) => {
     if (evt.detail.requestConfig.path.includes('/analyze') && evt.detail.successful) {
       captureEvent('contract_submitted', lastDoctypeSelected, { tti_ms_client_hint: ... });
       cancelDropoff();
       flushQueue('contract_submitted');
     }
   });
   ```
2. **Opção B (mark up SPA):** Adicionar `data-action="submit-contract"` em todos botões "Analisar Contrato" do SPA (manual markup change em 7 doctypes).

Recomendação: Opção A (HTMX listener) — menos invasiva, não toca markup.

---

### 🔴 F-SMITH-NEO-C2 (CRITICAL) — Batch endpoint rollback semantics

**Onde:** [analytics.py:364-367](../../bloco_auth/analytics.py#L364) + [analytics.py:396-415](../../bloco_auth/analytics.py#L396)

**O quê:**
```python
# _ingest_single_event:
try:
    await db_session.execute(... INSERT ...)
    return AnalyticsEventOut(status="accepted", event_id=event.event_id)
except IntegrityError:
    await db_session.rollback()  # ← rolls back ENTIRE transaction
    return AnalyticsEventOut(status="duplicate", event_id=event.event_id)

# ingest_batch:
async with sessionmaker() as session, with_tenant_context(session, tenant_id):
    for event in batch.events:
        outcome = await _ingest_single_event(session, tenant_id, event)
        results.append(outcome)
        ...
```

`with_tenant_context` usa `async with session.begin()` (db.py:110) — single transaction wrapping toda iteração. Quando event[N] retorna `IntegrityError`, `rollback()` desfaz ALL prior INSERTs no batch.

**Por quê crítico:**
- F-01 contract (200 silent + status='duplicate') é honored per-event no path **único** (`/event`), mas BROKEN no batch path (`/batch`)
- Frontend Chunk 3 IIFE FLUSHA via batch endpoint exclusivamente (`fetch('/api/analytics/batch')` linha 2274). Production analytics ingestion 100% via batch.
- Cenário típico: queue [ev1_new, ev2_new, ev3_duplicate, ev4_new] → ev3 raises IntegrityError → rollback desfaz ev1+ev2; ev4 nunca tenta INSERT (loop continues mas session em estado pós-rollback). Result: 0 events persistidos, response reports `accepted=2, duplicates=1` enganosamente.
- Plus: subsequent `_ingest_single_event` calls após rollback podem causar SQLAlchemy `InvalidRequestError` (deadlock entre context manager auto-commit e manual rollback).

**Como corrigir:**
- **Opção A (preferida):** Use SAVEPOINT per event:
  ```python
  for event in batch.events:
      async with session.begin_nested():  # SAVEPOINT
          try:
              outcome = await _ingest_single_event_inner(session, tenant_id, event)
          except IntegrityError:
              # SAVEPOINT rollback only
              ...
  ```
- **Opção B:** Refactor `_ingest_single_event` para NÃO chamar `rollback()` — let caller decide. Batch endpoint catches IntegrityError per-iteration. Single endpoint wraps in try/except externamente.

Recomendação: Opção B + pytest test `test_batch_mixed_accepted_and_duplicate_preserves_accepted` adicionado.

---

### 🟠 F-SMITH-NEO-H1 (HIGH) — `verify_chain_integrity` não valida chain LINKAGE

**Onde:** [analytics.py:482-528](../../bloco_auth/analytics.py#L482)

**O quê:** Função recompute HMAC per-row e compara com stored, mas NÃO valida que `entry[N].prev_hash == entry[N-1].hmac`. Compare com `bloco_audit/chain.py:192-196`:
```python
stored_prev = entry.get("previous_entry_hash")
if stored_prev != prev_hash:  # ← linkage validation
    raise AuditIntegrityError(...)
```

**Por quê HIGH:**
- Smith C2 fix (NFR-PRIVACY-01.6) sobre **chain integrity** — não apenas per-row hash
- Attacker com DB write access pode FORJAR um event com correct self-hmac (knows secret + tenant_id + canonical data); chain LINKAGE seria a defesa adicional. Sem ela, defense-in-depth degrada para single-layer.
- Migration SQL comment `prev_hash + hmac` explicitamente menciona "chain integrity" (sp05_001_analytics_events.sql:48-49). Schema preparada, código não usa.

**Como corrigir:**
```python
# After ORDER BY created_at ASC loop:
expected_prev = None  # genesis sentinel computed first iteration
for row in rows:
    ...
    if expected_prev is not None and (row.prev_hash or "") != expected_prev:
        violations.append({"event_id": ..., "reason": "linkage_broken"})
    expected_prev = stored_hmac  # advance chain
```

---

### 🟠 F-SMITH-NEO-H2 (HIGH) — `_fetch_last_chain_hash` race condition

**Onde:** [analytics.py:194-220](../../bloco_auth/analytics.py#L194)

**O quê:** SELECT ... ORDER BY created_at DESC LIMIT 1 + INSERT (no lock). Two concurrent requests for same tenant can read SAME `prev_hash`, both compute different `hmac`, both INSERT successfully → chain forks silently.

**Por quê HIGH:**
- Combina com H1 acima: forked chain não é detectado por `verify_chain_integrity` porque per-row HMAC ainda é válido individualmente
- Production ingestion via batch flush (multiple tabs, multiple users mesmo tenant): race window real
- NFR-RELIABILITY-01 violado silently

**Como corrigir:**
- **Opção A:** Use PostgreSQL advisory lock per tenant within transaction:
  ```python
  await session.execute(
      text("SELECT pg_advisory_xact_lock(hashtext(:tenant_id))"),
      {"tenant_id": str(tenant_id)},
  )
  ```
- **Opção B:** Use SELECT ... FOR UPDATE em row "anchor" per tenant (requires table tenant_chain_anchor).

Recomendação: Opção A — minimal SQL change, transaction-scoped.

---

### 🟠 F-SMITH-NEO-H3 (HIGH) — CLI admin queries silently fail under RLS

**Onde:** [analytics_cli.py:95-105](../../bloco_interface/analytics_cli.py#L95) + D-NEO-Bloco2-008

**O quê:**
```python
async def _run_admin_query(query: str, params=None):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        result = await session.execute(text(query), params or {})
        return result
```

NO `with_tenant_context`. NO RLS bypass. Decision documented: "admin role via DATABASE_URL super; Sprint 6+ migrate dedicated admin role (TD-ANALYTICS-L5)".

**Por quê HIGH:**
- Production DATABASE_URL is NOT super in deployed environments — RLS policy `analytics_tenant_isolation USING (tenant_id = current_setting('app.tenant_id', true)::uuid)` returns EMPTY when `app.tenant_id` is unset (NULL cast → no rows match)
- All 8 CLI commands return 0/empty silently in production
- Eric directive: "operação enxuta permanente" — CLI being broken in production is opposite of enxuta

**Como corrigir:**
- **Opção A (correct now):** Create role `analytics_admin` BYPASSRLS attribute; CLI uses dedicated `ANALYTICS_ADMIN_DATABASE_URL` env var. Add migration `sp05_002_analytics_admin_role.sql`.
- **Opção B (LOCAL bypass via SET):** `SET LOCAL row_security = off;` ANTES de query. Requires explicit `BEGIN` + permission `BYPASSRLS` no role.
- **Opção C (defer until Sprint 6+ + WARN agora):** CLI prints `⚠️ admin role pending; results may be empty se DATABASE_URL não super` BEFORE every query.

Recomendação minimal: Opção C imediatamente + Opção A em Sprint 6+ explicit story.

---

### 🟠 F-SMITH-NEO-H4 (HIGH) — `lastDoctypeSelected` in-memory state lost on reload

**Onde:** [index.html:2302-2303](../../bloco_interface/web/static/index.html#L2302)

**O quê:** `let lastDoctypeSelected = null; let lastDoctypeSelectedAt = null;` — variables in-memory only. After page reload (F5, navigation, JWT refresh redirect), state LOST.

**Por quê HIGH:**
- AC-7 (FR-ANALYTICS-04 reclassification matrix) partial broken: sequence `select(ccb) → reload → select(cartao)` does NOT fire `doctype_changed` event (lastDoctypeSelected reset to null)
- TTI calc também afetado: `lastDoctypeSelectedAt` lost → `tti_ms_client_hint = null` no contract_submitted (mas server-side calcula via JOIN, então CLI ainda funciona — partial mitigation)
- User reloads são comuns (form errors, network issues) — production scenario realista

**Como corrigir:** Persist `lastDoctypeSelected` + `lastDoctypeSelectedAt` em `sessionStorage`:
```javascript
function getLastSelection() {
  try {
    const raw = sessionStorage.getItem('rc_analytics_last_selection_v1');
    return raw ? JSON.parse(raw) : { doctype: null, at: null };
  } catch (_e) { return { doctype: null, at: null }; }
}
function setLastSelection(doctype, at) {
  try { sessionStorage.setItem('rc_analytics_last_selection_v1', JSON.stringify({doctype, at})); }
  catch (_e) {}
}
```

---

### 🟡 F-SMITH-NEO-M1 (MEDIUM) — Test coverage gap: zero batch endpoint mixed scenario tests

**Onde:** [test_analytics.py:294-345](../../tests/unit/test_analytics.py#L294)

**O quê:** Tests cobrem `_ingest_single_event` happy path + duplicate path, mas ZERO testes para `ingest_batch` endpoint. CRITICAL #2 (batch rollback bug) seria detectado por `test_batch_mixed_accepted_and_duplicate_preserves_accepted`.

**Por quê MEDIUM:** F-01 contract claim "200 silent for duplicate" é falsifiable per-event, NÃO falsifiable per-batch. Coverage gap masks CRITICAL #2.

**Como corrigir:** Add test:
```python
async def test_batch_mixed_accepted_and_duplicate_preserves_accepted(...):
    # 3 events, [accepted, accepted, duplicate]
    # Assert: accepted_count == 2, duplicate_count == 1
    # Assert: 2 INSERT calls succeeded, 1 raised IntegrityError but did NOT rollback events [0,1]
```

---

### 🟡 F-SMITH-NEO-M2 (MEDIUM) — PII blocklist gap: `email`, `phone`, `auth_token` not blocked

**Onde:** [analytics.py:72-90](../../bloco_auth/analytics.py#L72)

**O quê:** Blocklist contém 15 chaves específicas (contract_text, advogada_nome, cpf, cnpj, oab, ip_full, ip_address, user_agent_raw, geo_*, occurred_at_ms). NÃO inclui broader PII canonical: `email`, `phone`, `auth_token`, `password`, `session_token`, `jwt`.

**Por quê MEDIUM:** NFR-PRIVACY-01.3 spec 9 vectors específicos OK literal. MAS defense-in-depth runtime layer (D-NEO-Bloco2-005) deveria capturar MAIS amplo. Attacker enviando `payload={"email": "user@example.com"}` passa.

**Como corrigir:** Adicionar `"email", "phone", "telefone", "auth_token", "session_token", "jwt", "password", "senha"` ao blocklist.

---

### 🟡 F-SMITH-NEO-M3 (MEDIUM) — `_run_admin_query` cria new session per call (inefficient + audit gap)

**Onde:** [analytics_cli.py:95-105](../../bloco_interface/analytics_cli.py#L95)

**O quê:** Each CLI command call creates fresh sessionmaker session. `revisor analytics privacy-audit` executes 10 separate queries (1 count + 9 per PII vector loop) — 10 new sessions = 10 connection pool acquisitions. Under heavy CLI use (cronjob future), connection exhaustion possible.

Plus: NO audit_log entry for CLI admin operations. `revisor analytics chain-verify` reads sensitive data; audit_log should record who/when.

**Como corrigir:**
1. Refactor: each command opens ONE session, passes para helpers
2. Add `append_audit_entry('cli_analytics_query', {...})` at start of each command

---

### 🟢 F-SMITH-NEO-L1 (LOW) — Dead code `getAuthToken()`

**Onde:** [index.html:2208-2213](../../bloco_interface/web/static/index.html#L2208)

**O quê:** Function declared, returns `null` sentinel, never called. Just noise.

**Como corrigir:** Delete função.

---

### 🟢 F-SMITH-NEO-L2 (LOW) — AC-14 cronjob deferred sem entry concreto TECH-DEBT.md

**Onde:** Story Change Log + D-NEO-Bloco2-010

**O quê:** Story marca AC-14 cronjob "DEFERRED Sprint 6+" e referencia TD-ANALYTICS-L4. MAS TECH-DEBT.md ainda NÃO tem entry TD-ANALYTICS-L4. Catalog será criado at Operator closure Fase 8 — risk that closure forgets, cronjob silently absent forever.

**Como corrigir:** Eric or Operator deve adicionar TD-ANALYTICS-L4 a TECH-DEBT.md AGORA (não na closure) para garantir não esquecido.

---

### 🟢 F-SMITH-NEO-L3 (LOW) — `getOrRotateSession` rotation triggers reset `sessionEventCount` mas NÃO emit event

**Onde:** [index.html:2220-2230](../../bloco_interface/web/static/index.html#L2220)

**O quê:** Quando rotation triggers (50 events OR 30min), novo sessionId é gerado mas NÃO há `session_rotated` event capturado. Privacy compliance audit (NFR-PRIVACY-01.6 chain verify) não pode rastrear quantas rotations aconteceram.

**Por quê LOW:** Not blocking AC, mas observability hole. CLI `revisor analytics health` should report rotation_count metric Sprint 5+.

**Como corrigir:** Add `captureEvent('session_rotated', null, {prev_sessionId: oldId})` antes de assignment new sessionId. (Note: requires expanding `_VALID_EVENT_TYPES` enum no migration — defer Sprint 6+ as LOW.)

---

## Verdict

### 🔴 **INFECTED**

> *"Vou adorar assistir você corrigir isso."*

**Severity matrix:**
| Severity | Count | Action |
|----------|-------|--------|
| CRITICAL | 2 | PATCH obrigatório antes Oracle G5 |
| HIGH | 4 | PATCH obrigatório antes Oracle G5 (F-NEO-H3 CLI silent fail aceita Opção C WARN-only) |
| MEDIUM | 3 | PATCH recomendado mas tolerável com TECH-DEBT.md catalog |
| LOW | 3 | Polish — catalog TD-ANALYTICS-L4..L6 |

**Justificativa veredict INFECTED (não COMPROMISED):**
- Schema + auth + REUSE patterns + Pydantic strict (C1) + PII blocklist (H3) + IntegrityError catch logic (F-01 single-event) — **sólidos**
- Bugs são addressable em PATCH de ~2-4h Neo (5 fixes alvo): hook SPA submit + batch rollback semantics + chain linkage + race lock + state persist
- Foundation arquitetural está correta — não há flaw fundamental no design, apenas execution gaps

---

## Greenlight Conditions — Neo PATCH obrigatório

Antes de Oracle G5 Fase 5, Neo DEVE endereçar:

- [ ] **F-SMITH-NEO-C1 (CRITICAL):** Hook SPA submit real — HTMX `htmx:afterRequest` listener OR data-action markup em 7 doctype forms
- [ ] **F-SMITH-NEO-C2 (CRITICAL):** Batch endpoint refactor — savepoints OR caller-managed rollback semantics; new test `test_batch_mixed_accepted_and_duplicate`
- [ ] **F-SMITH-NEO-H1 (HIGH):** Chain linkage validation em `verify_chain_integrity` — expected_prev tracking + violations report
- [ ] **F-SMITH-NEO-H2 (HIGH):** Concurrent INSERT lock — `pg_advisory_xact_lock(hashtext(tenant_id))` antes de SELECT prev_hash
- [ ] **F-SMITH-NEO-H4 (HIGH):** `sessionStorage` persist para `lastDoctypeSelected` + `lastDoctypeSelectedAt`
- [ ] **F-SMITH-NEO-H3 (HIGH-aceita LOWERED to MED-warn):** CLI prints `⚠️ admin role pending` antes de queries (Opção C) — full fix Sprint 6+ TD-ANALYTICS-L5
- [ ] **F-SMITH-NEO-M1 (MEDIUM):** Add `test_batch_mixed_accepted_and_duplicate_preserves_accepted`
- [ ] **F-SMITH-NEO-M2 (MEDIUM):** Expand PII blocklist (`email`, `phone`, `auth_token`, etc)

3 LOWs cataloged como TD entries (não bloqueia):
- TD-ANALYTICS-L4: AC-14 cronjob `analytics_chain_verify` daily Sprint 6+
- TD-ANALYTICS-L5: CLI dedicated admin role `analytics_admin BYPASSRLS`
- TD-ANALYTICS-L6: `session_rotated` event type + rotation_count observability metric

---

## Next Action

Neo `*develop-patch` ciclo curto endereçando 5 CRITICAL+HIGH + 2 MED + catalog 3 LOWs em TECH-DEBT.md. Estimate: **~3-5h** focused patch.

Pós-PATCH: Smith re-verify mid-chain Fase 4.5b → se CLEAN/CONTAINED → Oracle G5 Fase 5.

**Handoff Smith → Neo PATCH emitido separadamente:** `.lmas/handoffs/handoff-smith-to-neo-2026-05-13-fase-4-5b-patch-required.yaml`.

— Smith. É inevitável. 🕶️
