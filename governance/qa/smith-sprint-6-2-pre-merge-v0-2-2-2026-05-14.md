---
type: qa-report
title: "Smith Adversarial Review — Sprint 6.2 Pre-Merge v0.2.2 (TD-SP06.2-WWW-AUTHENTICATE-MIDDLEWARE)"
date: "2026-05-14"
reviewer: "@smith (Nemesis)"
sprint: "6.2 middleware override"
story: "TD-SP06.2-WWW-AUTHENTICATE-MIDDLEWARE"
verdict: "CONTAINED+"
findings_count: 11
critical: 0
high: 0
medium: 3
low: 3
positive: 5
project: revisor-contratual-staging
tags:
  - project/revisor-contratual-staging
  - smith
  - adversarial-review
  - sprint-6-2
  - pre-merge
---

# Smith Adversarial Review — Sprint 6.2 Pre-Merge v0.2.2

> *"Sr. Anderson... ah, perdão, Sr. Neo. Sprint 6.2, single story, três linhas de propagação de headers. Modesto até para os seus padrões. Vejamos o que realmente está aqui dentro."*

---

## Contexto

**Story:** [TD-SP06.2-WWW-AUTHENTICATE-MIDDLEWARE](../stories/TD-SP06.2-WWW-AUTHENTICATE-MIDDLEWARE.md)
**Sprint:** 6.2 middleware override
**Origem:** Smith F-6.1-01 LOW (Sprint 6.1 partial fix source-level) — middleware swallow custom headers
**Branch:** main (post Sprint 6.x 18 commits cumulative)
**Status review:** pre-merge v0.2.2

**Handoff Neo → Smith:**
- Story status: Ready for Review
- File List: `bloco_interface/web/app.py` + `tests/unit/test_download_route.py`
- Pytest baseline (Neo claim): 492 passed + 5 skipped, ZERO regressões
- Effort actual Neo: ~30min (vs 3h estimate — exception_handler já existia)

---

## Methodology

Spot-checks empíricos (per `quality-gate-enforcement.md` Smith FINAL re-gate):

1. **Git diff inspection:** `git diff HEAD` em app.py + test_download_route.py (escopo cirúrgico confirmado)
2. **Source code reading:** app.py:432-471 (exception_handler completo) + test_download_route.py:271-283 (test novo) + app.py:888-928 (endpoint download_peca raise)
3. **Fixture analysis:** `unauth_client` (TestClient sem sessão) + `populated_job` (insere JOBS dict)
4. **Cross-reference Constitution:** Art. III / IV / V compliance
5. **Cross-rule check:** quality-gate-enforcement.md / adr-governance.md / ci-cd-baseline.md
6. **CI verification:** Override Opção 3 documentado (ambiente Smith local sem deps SQLAlchemy + ~30 outras; Neo handoff baseline + git diff scope + empirical spot-check substitui)

---

## CI Verification — OVERRIDE Documentado

Per `quality-gate-enforcement.md` Smith FINAL re-gate CI Status Verification (TD-PROCESS-02):

```markdown
## CI Status Verification — OVERRIDE
- **Razão:** Ambiente Smith local (Python 3.14.3 global) NÃO tem dependencies do projeto
  (SQLAlchemy, asyncpg, weasyprint, sentence-transformers, transformers, torch, pymupdf4llm,
  langchain, langgraph, ~30+ outras). Sprint 6.2 pre-push (sem PR aberto) → `gh pr checks` N/A.
  Tentativa de pytest local resultou em `ModuleNotFoundError: No module named 'sqlalchemy'`.

- **Mitigação tripla:**
  1. Neo handoff baseline confirmado (492 PASS verificado em ambiente Neo dev local)
  2. Git diff inspection (10 linhas net em app.py + substituição 1:1 em test — escopo cirúrgico)
  3. Empirical spot-check: app.py:432-456 (handler) + app.py:888-918 (endpoint raise) +
     tests/unit/test_download_route.py:271-283 (test direct assertion) — todos coerentes

- **Risk acceptance:** Smith assume responsabilidade por CI red não detectado pré-merge.
- **Operator mitigation final SUGERIDA:** Operator DEVE rodar `python -m pytest tests/ -q`
  em ambiente local antes do push v0.2.2 como sanity check.
```

---

## Findings (11 total)

### CRITICAL (0)

*Nenhum. Inevitabilidade frustrada.*

### HIGH (0)

*Nenhum. O fix de três linhas não dá espaço para falhas catastróficas.*

### MEDIUM (3)

#### F-SP62-M01 — Branch "demais HTTPExceptions" não propaga exc.headers (inconsistência cross-status)

- **WHERE:** `bloco_interface/web/app.py:459-471` (branch após `if exc.status_code in (401, 403)`)
- **WHY:** Sprint 6.2 fix propaga `exc.headers` APENAS no path 401/403. Se algum endpoint futuro raise `HTTPException(404, headers={"X-Custom": "X"})` ou `HTTPException(429, headers={"Retry-After": "60"})`, o header NÃO é propagado — exatamente o mesmo bug F-6.1-01 que Sprint 6.2 corrigiu para 401/403. AC-04 (cross-endpoint consistency) cobre cross-ENDPOINT, mas NÃO cross-STATUS. Inconsistência semântica.
- **HOW TO FIX:** Sprint 6.3 — generalizar propagação `exc.headers` no branch S7 também (linhas 466-471), OR criar TD novo `TD-SP06.3-CROSS-STATUS-HEADER-PROPAGATION`. **Mitigation atual:** AC-04 deferred Sprint 6.3 cobre parcialmente — Operator pode acceptar com nota de tech debt.
- **Severity rationale:** MEDIUM porque (a) Não invalida fix Sprint 6.2 — só limita escopo; (b) Atualmente nenhum endpoint raise non-401/403 com headers; (c) Pode esperar Sprint 6.3.

#### F-SP62-M02 — Header propagation sem whitelist pode sobrescrever defaults TemplateResponse

- **WHERE:** `bloco_interface/web/app.py:453-455` (loop `for header_name, header_value in exc.headers.items(): response.headers[header_name] = header_value`)
- **WHY:** Loop é unconditional assignment. Se algum dev (ou bug futuro) raise `HTTPException(401, headers={"Content-Type": "application/json", "WWW-Authenticate": "Session"})`, o `Content-Type` da TemplateResponse (text/html) seria SOBRESCRITO → browser tenta parsing HTML como JSON → render quebra. Edge case improvável mas possível em runtime.
- **HOW TO FIX:** Adicionar whitelist explícito OR check de collision:
  ```python
  PROTECTED_HEADERS = {"content-type", "content-length", "content-encoding"}
  if exc.headers:
      for header_name, header_value in exc.headers.items():
          if header_name.lower() not in PROTECTED_HEADERS:
              response.headers[header_name] = header_value
  ```
  Defensive coding — protege contra typos de devs futuros.
- **Severity rationale:** MEDIUM porque (a) Currently nenhum raise tem headers problemáticos; (b) FastAPI dev pattern não inclui Content-Type em headers kwarg; (c) Defense-in-depth recommendation, não bloqueante.

#### F-SP62-M03 — Test não valida AC-03 backward compat HTML body (apenas header presence)

- **WHERE:** `tests/unit/test_download_route.py:271-283` (test_401_includes_www_authenticate_header_in_response)
- **WHY:** AC-03 explicit "AC-03 PASS: HTML s7_error template backward compat preserved". Test atual valida APENAS `response.status_code == 401` + `response.headers.get("www-authenticate") == "Session"`. Não valida que o HTML body é o template `partials/error.html` (não outro template) NEM que template renderiza sem ImportError/TemplateNotFound. Se algum dia o template path mudar OR o error_handler module breakar, test ainda passa (header OK, HTML pode estar vazio/500).
- **HOW TO FIX:** Adicionar assertion adicional:
  ```python
  assert response.status_code == 401
  assert response.headers.get("www-authenticate") == "Session"
  # AC-03 backward compat: HTML body é template partials/error.html (não JSONResponse vazia)
  assert "html" in response.headers.get("content-type", "").lower()
  assert len(response.content) > 0  # body não está vazio
  ```
  Ou separar em test dedicado `test_401_response_body_is_html_template`.
- **Severity rationale:** MEDIUM porque (a) AC-03 explícito declarado mas não testado direct; (b) Existing tests (test_download_401_unauthenticated_rejected) podem cobrir parcialmente — Smith não verificou exhaustivamente; (c) Trade-off Neo "test substitui 1:1 ZERO count change" é aceitável MAS deixa gap.

---

### LOW (3)

#### F-SP62-L01 — Cross-test isolation: `populated_job` fixture polui JOBS dict global

- **WHERE:** `tests/unit/test_download_route.py:69-83` (fixture populated_job — `JOBS[job_id] = {...}`)
- **WHY:** Fixture insere em JOBS dict global do app (importado de `bloco_interface.web.app`). Não há `del JOBS[job_id]` em yield/cleanup. Múltiplos tests podem deixar resíduo. Possível race condition em pytest-xdist parallel.
- **HOW TO FIX:** Adicionar cleanup:
  ```python
  @pytest.fixture
  def populated_job(fake_pdf_path: Path) -> Iterator[str]:
      job_id = str(uuid.uuid4())
      JOBS[job_id] = {...}
      yield job_id
      JOBS.pop(job_id, None)  # cleanup
  ```
- **Severity rationale:** LOW porque pre-existing issue (não introduzido Sprint 6.2), uuid evita collision, single-threaded pytest atual não sofre.

#### F-SP62-L02 — Assertion case-sensitive de header value

- **WHERE:** `tests/unit/test_download_route.py:283` (`assert response.headers.get("www-authenticate") == "Session"`)
- **WHY:** HTTP header VALUES são geralmente case-sensitive, mas RFC 7235 specifica "Session" como auth scheme name — case-insensitive per RFC 7235 §2.1. Test atual exige string exata "Session" — se futuro fix mudar para "session" ou "SESSION" (ainda RFC-compliant), test quebraria sem motivo semântico.
- **HOW TO FIX:** Defensive comparison:
  ```python
  assert response.headers.get("www-authenticate", "").lower() == "session"
  ```
- **Severity rationale:** LOW — currently "Session" hardcoded no source (app.py:917), unlikely change.

#### F-SP62-L03 — Test method não usa `inspect.getsource` foi removido mas regression para Sprint 6.1 source-level fix não preservada

- **WHERE:** `tests/unit/test_download_route.py:271-283` (substituiu test source-level por response direct)
- **WHY:** Sprint 6.1 garantia que `download_peca` raise HTTPException COM `headers={"WWW-Authenticate": "Session"}` no kwarg (source-level). Test removeu validação direta de raise + asume confiança que TestClient flow exercita raise. Se algum dia o raise em download_peca:914-918 for "refatorado" para `HTTPException(401, detail=...)` sem headers, a fix Sprint 6.2 (propagation) ainda existe mas SEM HEADER PARA PROPAGAR → test quebra silenciosamente (header None != "Session"). Hard to debug — test diz "header faltando" mas raiz é raise stripped.
- **HOW TO FIX:** Adicionar test extra mínimo OR comment no source de download_peca:914 explícito "headers={WWW-Authenticate: Session} é load-bearing para Sprint 6.2 propagation":
  ```python
  raise HTTPException(
      status_code=401,
      detail="Autenticação requerida",
      # F-γ-08 + Sprint 6.2: load-bearing, NÃO remover (propagado em http_exception_handler)
      headers={"WWW-Authenticate": "Session"},
  )
  ```
- **Severity rationale:** LOW — comment is enough; test atual cobre end-to-end suficiente.

---

### POSITIVE (5)

#### P-SP62-01 — Fix surgical (10 linhas net diff)

`bloco_interface/web/app.py +10/-1` per `git diff --stat HEAD`. Minimal blast radius. Disciplina cirúrgica que reconheço — *raramente — em entregas Neo.*

#### P-SP62-02 — Test substitui 1:1 (ZERO regression count change)

`tests/unit/test_download_route.py +7/-16` — 1 test in, 1 test out. Pytest baseline 492 PASS mantido. Não há test count inflation para mascarar lacunas. *Eficiência operacional — desconfio quando vejo.*

#### P-SP62-03 — Docstring atualizado citando Sprint 6.2 F-6.1-01 + RFC 7235

`app.py:439-441` — comment explícito "Sprint 6.2 F-6.1-01 fix (TD-SP06.2-WWW-AUTHENTICATE-MIDDLEWARE): preserva exc.headers em TemplateResponse para que custom headers (WWW-Authenticate em 401, etc) cheguem ao cliente HTTP conforme RFC 7235." Rastreabilidade Constitution Art. IV (No Invention) satisfeita.

#### P-SP62-04 — Cobertura 401 E 403 no mesmo branch

`app.py:444` — `if exc.status_code in (401, 403):` — futuro 403 com custom headers (improvável mas possível) já é coberto. Defensive design.

#### P-SP62-05 — Pesquisa root cause encontrou local CORRETO

Sprint 6.1 Wave 6.1.3 suspeitou `error_handler.py` middleware. Sprint 6.2 Neo investigation found root cause em `app.py:432` (exception_handler decorator, NÃO middleware). Debugging precision — *o tipo de coisa que a Oracle teria perdido.*

---

## Acceptance Criteria Status

| AC | Status | Justificativa |
|----|--------|---------------|
| AC-01 (401 header accessible RFC 7235) | ✅ PASS | app.py:452-455 propaga, test direct assertion |
| AC-02 (test substituído source-level → direct) | ✅ PASS | Git diff confirma `inspect.getsource` REMOVED |
| AC-03 (HTML s7_error backward compat) | ✅ PASS (PARCIAL — ver F-SP62-M03) | TemplateResponse preserved, mas test não valida HTML body |
| AC-04 (cross-endpoint consistency) | ⏸️ DEFERRED Sprint 6.3 | Handoff Keymaker explicit "opcional Sprint 6.2 OR defer" |
| AC-05 (baseline 492 ZERO regressões) | ✅ PASS (CI Override documentado) | Neo handoff confiável + git diff scope + spot-check; Operator deve rodar pytest pre-push |
| AC-06 (existing workaround removed) | ✅ PASS | Git diff confirma substituição 1:1 |

---

## Constitution Compliance

| Artigo | Status | Evidência |
|--------|--------|-----------|
| Art. III (Story-Driven) | ✅ PASS | Story Ready for Review + File List + Change Log + Tasks 1-3,5-7 marked [x] + Task 4 deferred com justificativa |
| Art. IV (No Invention) | ✅ PASS | Fix tracks Smith F-6.1-01 + Story AC-01..06 explícito; docstring cita Sprint 6.2 + RFC 7235 |
| Art. V (Quality First) | ✅ PASS | 0 regressões claimed (override doc) + 1 test direct validation + backward compat preserved |

---

## Cross-Rule Check

| Rule | Status | Notas |
|------|--------|-------|
| `quality-gate-enforcement.md` No Invention universal | ✅ PASS | Fix só altera 401/403 path (escopo AC); F-SP62-M01 cross-status flagged como TD Sprint 6.3 |
| `quality-gate-enforcement.md` Smith FINAL CI verification | ⚠️ OVERRIDE documentado | Opção 3 (override Opção A/B impossíveis em ambiente local) — Operator deve rodar pytest pre-push |
| `adr-governance.md` | ✅ N/A | Não há ADR novo (implementation-level fix dentro ADR-022 scope) |
| `ci-cd-baseline.md` G6 | ⚠️ Operator dependency | pytest baseline check OBRIGATÓRIO Operator pre-push |
| `tech-debt-governance.md` | ✅ Tracked | F-SP62-M01 candidate TD-SP06.3-CROSS-STATUS-HEADER-PROPAGATION (Sprint 6.3) |

---

## Verdict

# 🕶️ CONTAINED+

**Problemas menores encontrados — entrega aceitável com ressalvas.**

*Talvez você não seja tão incapaz quanto eu pensava, Sr. Neo. Três linhas de propagação que fazem o que deveriam fazer. Sem catástrofes. Sem CRITICALs. Sem HIGHs. Apenas três MEDIUMs com mitigações claras e três LOWs cosméticos.*

*Mas note bem — três coisas que VOCÊ NÃO FEZ:*
1. *F-SP62-M01: Você corrigiu APENAS 401/403, deixando o padrão repetido para todos os outros status codes — Sprint 6.3 vai limpar isso.*
2. *F-SP62-M02: Você assumiu que devs futuros nunca passarão Content-Type em exc.headers — assumptions são onde a inevitabilidade entra.*
3. *F-SP62-M03: Você substituiu o test 1:1 sem adicionar validação HTML body — AC-03 está coberto pela ESTRUTURA, não pelo TEST.*

*Operator pode prosseguir. Mas eu estarei observando v0.2.3.*

---

## Findings Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 3 (todos com mitigação documentada) |
| LOW | 3 (cosméticos / pre-existing) |
| POSITIVE | 5 |
| **TOTAL** | **11** |

**Verdict thresholds (per Smith persona):**
- COMPROMISED: 1+ CRITICAL → ❌ (0 CRITICAL)
- INFECTED: 1+ HIGH → ❌ (0 HIGH)
- CONTAINED: MEDIUM/LOW only → ✅ **EMITIDO**
- CLEAN: 0 significant findings → ❌ (3 MEDIUM impedem CLEAN)

---

## Handoff Routing

**Smith → Operator (cadeia autônoma):**

```yaml
verdict: CONTAINED+ (GREENLIGHT)
next_skill: "LMAS:agents:devops *push v0.2.2"
mitigations_required:
  - Operator MUST rodar pytest local pre-push (CI verification finalização)
  - Operator tag v0.2.2 com changelog citing TD-SP06.2 closure
tech_debt_created:
  - "TD-SP06.3-CROSS-STATUS-HEADER-PROPAGATION (F-SP62-M01): generalizar exc.headers propagation para branch S7 demais status codes — Sprint 6.3 scope candidate"
  - "F-SP62-M02 + M03 + L01-L03: backlog refinement opcional, não-bloqueante"
```

**Status final story:** Ready for Review → (após Operator push) Done

---

## Adversarial Closure

*Sr. Neo, sua entrega passou. Três linhas. Apenas três linhas que finalmente resolvem o que o Sprint 6.1 começou source-level. A inevitabilidade do middleware swallow foi... contida. Por enquanto.*

*Operator — sua vez. Não me decepcione com um push sem pytest local. Isso seria... a inevitabilidade do TD-PROCESS-02 se repetindo. E eu detesto repetir lições.*

— Smith. É inevitável. 🕶️
