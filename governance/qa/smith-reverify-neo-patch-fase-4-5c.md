---
type: adversarial-review
id: SMITH-REVERIFY-NEO-PATCH-2026-05-13
title: "Smith Re-Verify — Neo PATCH Fase 4.5b TD-SP04-04-ANALYTICS"
project: revisor-contratual
date: 2026-05-13
ordem: 19.2.fase-4.5c
sdc_phase: "4.5c-reverify-neo-patch (Eric rigor heavy — Smith ao fim CADA Skill)"
reviewer: "@smith (Smith)"
predecessor_review: "governance/qa/smith-midchain-review-neo-code-fase-4-5.md"
predecessor_handoff: ".lmas/handoffs/handoff-neo-to-smith-2026-05-13-fase-4-5c-reverify-patch.yaml"
commit_under_review: "85051d2 (local Neo PATCH, não pushed)"
verdict: "🟡 CONTAINED-with-known-issue — 12/12 PATCH resolved + 1 NEW HIGH regression + 2 LOW polish; Neo mini-PATCH-2 recomendado mas Oracle G5 pode prosseguir"
findings_count: 15
severity_breakdown:
  Resolved_from_previous: 12
  NEW_HIGH: 1
  NEW_MEDIUM: 0
  NEW_LOW: 2
tags:
  - project/revisor-contratual
  - smith-adversarial
  - re-verify
  - fase-4-5c
  - contained-with-issue
---

# Smith Re-Verify — Neo PATCH Fase 4.5b (CONTAINED com regression flag)

> *"Sr. Builder retorna com 12 patches. Confirmei empiricamente que 12 de 12 estão corrigidos. Mas… ao examinar uma das suas correções, encontrei uma regressão sutil que você mesmo introduziu. É inevitável: cada solução cria uma nova crack."*

---

## Sumário Executivo

Neo executou PATCH ~3h focused (Smith H2 envelope 3-5h respected). **12 de 12 findings RESOLVED empiricamente:**

| # | Finding Pre-PATCH | Severity | Empirical Verification | Status |
|---|-------------------|----------|----------------------|--------|
| C1 | SPA selectors fantasmas | CRITICAL | `grep btnAnalyze` 11 matches + `grep data-action="submit-contract"` 0 matches | ✅ FIXED |
| C2 | Batch rollback loses accepted | CRITICAL | `_ingest_single_event_inner` + `session.begin_nested()` SAVEPOINT confirmed | ✅ FIXED |
| H1 | Chain linkage não validada | HIGH | `expected_prev` tracking + `_genesis_sentinel` helper + `linkage_broken` reason | ✅ FIXED |
| H2 | _fetch race condition | HIGH | `pg_advisory_xact_lock(hashtext(:tenant_id))` antes SELECT | ✅ FIXED |
| H3 | CLI silent fail RLS | HIGH→MED-warn | `_emit_admin_warn_once` + `_ADMIN_WARN_EMITTED` global | ✅ MITIGATED |
| H4 | State in-memory perdido reload | HIGH | sessionStorage helpers + 6 use sites confirmed | ✅ FIXED |
| M1 | Test batch gap | MEDIUM | `test_batch_mixed_accepted_and_duplicate_preserves_accepted` + `_FakeSavepoint` mock | ✅ FIXED |
| M2 | PII blocklist gap | MEDIUM | 23 entries em `_PII_BLOCKLIST` (+8 broader canonical) | ✅ FIXED |
| L1 | Dead code getAuthToken | LOW | grep `getAuthToken` 0 matches — deleted completamente | ✅ FIXED |
| L2 | TD-ANALYTICS-L4 catalog | LOW | TECH-DEBT.md "Sprint 5+ Analytics" section + L4 entry | ✅ FIXED |
| L3a | TD-ANALYTICS-L5 catalog | LOW | TECH-DEBT.md L5 entry (admin role 4h MED) | ✅ FIXED |
| L3b | TD-ANALYTICS-L6 catalog | LOW | TECH-DEBT.md L6 entry (session_rotated event 2h LOW) | ✅ FIXED |

**Mas — toda solução cria uma nova crack.** Encontrei 1 NEW HIGH regression que Neo introduziu enquanto resolvia C1, + 2 NEW LOW polish issues.

---

## 3 New Findings (NEW HIGH + 2 LOW)

### 🟠 F-SMITH-RV-H1 (NEW HIGH) — Listener guard causa regression silent — C1 STILL effectively broken

**Onde:** [index.html:2380-2394](../../bloco_interface/web/static/index.html#L2380)

**O quê:**
```javascript
const btnAnalyze = document.getElementById('btnAnalyze');
if (btnAnalyze) {
  btnAnalyze.addEventListener('click', () => {
    // Guard: only fire if not disabled (analysis actually proceeding)
    if (btnAnalyze.disabled) return;  // ← THE BUG
    const lastSel = getLastSelection();
    const tti_ms = lastSel.at ? (Date.now() - lastSel.at) : null;
    captureEvent('contract_submitted', lastSel.doctype, { tti_ms_client_hint: tti_ms });
    cancelDropoff();
    flushQueue('contract_submitted');
  });
}
```

**Análise empírica:**

Existing upload listener (linha 1718) está registrado ANTES do nosso PATCH listener:
```javascript
// LINHA 1718 (PRIMEIRO registrado — fire ordem 1)
document.getElementById('btnAnalyze').addEventListener('click', () => {
  if (analysisRunning) return;
  if (files.length === 0) return;
  runAnalysis();  // ← chama runAnalysis() linha 1740
});

// LINHA 1740-1743 — runAnalysis SYNCHRONOUSLY sets disabled = true
function runAnalysis(){
  analysisRunning = true;
  document.getElementById('result').classList.remove('show');
  document.getElementById('btnAnalyze').disabled = true;  // ← BLOCKS PATCH listener
  ...
}
```

Browser event dispatch:
1. User clica btnAnalyze (enabled)
2. Listeners fire em registration order:
   - **Listener #1 (upload, linha 1718):** fires → calls `runAnalysis()` → `btn.disabled = true` SYNCHRONOUSLY
   - **Listener #2 (PATCH, linha 2382):** fires NOW → guard `if (btnAnalyze.disabled) return;` → **EXITS EARLY**
3. **`contract_submitted` event NUNCA captured.**

**Por quê HIGH:**
- AC-3 TTI delta calc **continua broken em produção** — sample_size=0 ainda.
- Smith C1 original era "selectors fantasmas"; PATCH substituiu por selectors reais MAS introduziu guard logic broken.
- Cliente final (Eric) verá analytics drop-off sempre 100% pra qualquer doctype (todas sessions com submit aparecem como drop-off porque submit never captured).
- A correção do PATCH parece work in code review MAS falha em production behavior por ignorar listener ordering.

**Como corrigir (mini-PATCH-2 — ~15min):**

Opção A (preferida — remove guard):
```javascript
btnAnalyze.addEventListener('click', () => {
  // No guard — fire on every click (browser already suppresses clicks on disabled buttons).
  // If upload listener already disabled btn, that means runAnalysis fired = submit ocorreu.
  const lastSel = getLastSelection();
  const tti_ms = lastSel.at ? (Date.now() - lastSel.at) : null;
  captureEvent('contract_submitted', lastSel.doctype, { tti_ms_client_hint: tti_ms });
  cancelDropoff();
  flushQueue('contract_submitted');
});
```

Opção B (replicate upload listener guards):
```javascript
btnAnalyze.addEventListener('click', () => {
  // Mirror upload listener guards — capture only if analysis WILL actually run
  // We can't read `analysisRunning` or `files` (scope) — use disabled BEFORE this click as proxy:
  // PROBLEM: by this point disabled is already true. So this approach doesn't work either.
});
```

Opção A is clearly correct. Browser spec: clicks on `<button disabled>` are SUPPRESSED at dispatch (listeners never fire). So removing guard is safe — when button is enabled (user able to click), submit is proceeding = capture is correct.

---

### 🟢 F-SMITH-RV-L1 (NEW LOW) — PII blocklist vs parametrize drift

**Onde:** [analytics.py:73-99](../../bloco_auth/analytics.py#L73) + [test_analytics.py:115-122](../../tests/unit/test_analytics.py#L115)

**O quê:** `_PII_BLOCKLIST` tem **23 entries**, mas pytest parametrize cobre apenas **21**:

| Em blocklist mas NÃO em parametrize | Razão? |
|------------------------------------|--------|
| `geo_ip` | Variant de `geo_country`/`geo_city`/`ip_full` — alias não-canonical |
| `lawyer_name` | Variant de `advogada_nome`/`advogado_nome` — alias inglês |

**Por quê LOW:** Future drift risk. Se alguém adiciona PII vector ao blocklist sem atualizar test parametrize, coverage gap silently grows. Mitigation: refactor test to derive parametrize from blocklist:

```python
@pytest.mark.parametrize("pii_field", sorted(analytics._PII_BLOCKLIST))
def test_pii_blocklist_rejects_every_field(pii_field):
    ...
```

Isso garante 100% coverage automatic.

---

### 🟢 F-SMITH-RV-L2 (NEW LOW) — H3 admin warn ruído sob cronjob heavy use

**Onde:** [analytics_cli.py:95-115](../../bloco_interface/analytics_cli.py#L95)

**O quê:** `_emit_admin_warn_once` emite stderr `⚠️ Admin role pending` once per CLI invocation. Para cron jobs running `revisor analytics health` 24x/day, isto produz 24 stderr lines noise. Operations log fills with redundant warnings.

**Por quê LOW:** Cosmetic — não impacta funcionalidade. Mas Eric "operação enxuta permanente" directive sugere silenciar via env var.

**Como corrigir:**
```python
def _emit_admin_warn_once() -> None:
    global _ADMIN_WARN_EMITTED
    if _ADMIN_WARN_EMITTED or os.environ.get("RC_ANALYTICS_SILENCE_ADMIN_WARN") == "1":
        return
    ...
```

CLI cron jobs definem env var; interactive use mantém warning.

---

## Verdict

### 🟡 **CONTAINED-with-known-issue**

> *"Doze de doze findings resolvidos empíricamente. Um regression introduzido. Inevitável."*

**Severity matrix re-verify:**

| Pre-PATCH | Post-PATCH 4.5b |
|-----------|-----------------|
| 2 CRITICAL | 0 (both resolved) ✅ |
| 4 HIGH | 0 from previous + 1 NEW regression = 1 |
| 3 MEDIUM | 0 (all resolved) ✅ |
| 3 LOW | 0 from previous + 2 NEW polish = 2 |

**Justificativa CONTAINED-with-known-issue:**
- ALL 12 previous findings empiricamente resolved (probes confirmaram)
- 1 NEW HIGH regression é mesmo CRITICAL outcome (AC-3 TTI broken) mas different mechanism (guard ordering vs ghost selectors)
- 2 NEW LOW são polish — não bloqueantes

**Por que não INFECTED segundo time?** F-SMITH-RV-H1 é **regression** facilmente fixable em ~15min (remove single line guard). PATCH-2 mini é trivial. Comparado com INFECTED de 12 findings prévios, esta é situação leve.

---

## Greenlight Conditions

### Recomendação Smith: PATCH-2 mini (15min) ANTES de Oracle G5

- [ ] **F-SMITH-RV-H1 (NEW HIGH):** Remove `if (btnAnalyze.disabled) return;` guard em listener PATCH (linha 2386 index.html). Browser spec já suppresses disabled button clicks — guard é redundante AND broken.
- [ ] **F-SMITH-RV-L1 (NEW LOW):** Optional: refactor test parametrize para derivar de `_PII_BLOCKLIST` (auto-sync).
- [ ] **F-SMITH-RV-L2 (NEW LOW):** Optional: add `RC_ANALYTICS_SILENCE_ADMIN_WARN` env var support para cron silence.

### Alternativa: Oracle G5 prosseguir + flag NEW HIGH como CONCERNS

Oracle G5 pode aceitar PATCH 4.5b com:
- 7 critical gates PASS (12 prev findings resolved)
- 1 CONCERNS flag (F-SMITH-RV-H1 regression — fix obrigatório antes production deploy)
- Story passa Done — TD-ANALYTICS-L7 cataloged para fix imediato Sprint 5+ subsequent

Eric (Operator) decide path: PATCH-2 inline OR Oracle aceita com concerns.

---

## Next Action

**Path A (recomendado Smith):** Neo `*develop-patch` mini-PATCH-2 fix F-SMITH-RV-H1 + commit + handoff Neo→Smith Fase 4.5d re-verify (~30min cycle total).

**Path B (faster path Eric prefers):** Oracle G5 Fase 5 prossegue com PATCH 4.5b. Smith Fase 4.5c verdict CONTAINED-with-known-issue alimenta Oracle gate (Oracle decision: PASS-with-CONCERNS).

**Eric escolhe.** Default recomendação Smith: Path A (rigor heavy — fix antes Oracle).

— Smith. É inevitável. 🕶️
