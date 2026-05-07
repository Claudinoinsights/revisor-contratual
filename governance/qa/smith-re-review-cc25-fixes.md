---
type: qa-report
title: "Smith Adversarial Re-Review — CC.25 Fixes"
project: revisor-contratual
sprint: "03"
session: 91
etapa: "CC.26 Trilha 2.5 re-review"
reviewer: "@qa · Oracle (Smith adversarial mode)"
date: "2026-05-06"
scope:
  - "F-01 fix em bloco_backup/scheduler.py (feature flag)"
  - "F-05 fix em bloco_dataset/scraper_tema_1378.py (DEFAULT_HEADERS)"
  - "F-08 fix em bloco_dataset/auto_trigger.py:run_camada_1_check (invariant)"
  - "tests/integration/test_task8b_cc25_fixes.py (10 tests)"
  - "tests/integration/test_task8_lgpd_backup.py:test_create_scheduler_has_3_jobs (update)"
commits_revisados:
  - "6c5afaf fix(monitor): MVP-LEAN-01 Task 8b CC.25 — feature flag + User-Agent + F-08 invariant"
findings_total: 6
severities:
  CRITICAL: 0
  HIGH: 0
  MEDIUM: 2
  LOW: 4
verdict: "PASS-WITH-NOTES — 3 fixes corretamente implementados, 0 regressões funcionais, 0 issues HIGH/CRITICAL. 6 notas LOW/MED para refinamento futuro (não-bloqueantes para merge)."
tags:
  - project/revisor-contratual
  - qa
  - adversarial-review
  - cc25-re-review
  - sprint-03
---

# Smith Adversarial Re-Review — CC.25 Fixes

> Cynical mindset preservado. Pressuponho que fixes podem ter introduzido novos bugs ou ser parciais — preciso provar o contrário ou expor a verdade.
> 6 findings em 3 fixes (6c5afaf). 0 CRITICAL, 0 HIGH, 2 MEDIUM, 4 LOW.

---

## Sumário executivo

**O que foi verificado:**
- F-01 (feature flag) — lógica condicional, parsing env, logger, docstring
- F-05 (DEFAULT_HEADERS) — User-Agent RFC compliance, Accept-Language, retry preservation
- F-08 (invariant) — condição preserva fail_count, race conditions, edge cases
- 10 tests novos + 1 test legacy atualizado
- Side effects + integração com módulos não-touched

**O que funcionou (raramente Smith reconhece, mas aqui sim):**
- ✅ F-01: `os.environ.get(..., "false").lower() == "true"` é parsing correto e case-insensitive
- ✅ F-05: `DEFAULT_HEADERS` definido como constant module-level garante consistência em retries
- ✅ F-08: condição AND `nivel == "vermelho" AND fail_count >= 2` é precisa e defensive (`.get()` com defaults)
- ✅ Tests cobrem happy paths + 1 edge case (vermelho-via-tese)
- ✅ Suite 397+3 zero regressão

**O que merece nota (mas não bloqueia merge):**
- 2 MED: F-05 retry headers não-testado explicitamente; F-08 race condition concurrent
- 4 LOW: F-01 env parsing rígido + runtime stale; F-05 URL UA stale-prone; F-08 docstring incompleta

**Verdict:** **PASS-WITH-NOTES**. Merge defensável; tech debts LOW/MED rastreados para refinamento iterativo.

---

## Findings por severidade

### 🟡 MEDIUM (2)

#### RR-01-CC25: [MED] F-05 retry preserva headers mas não há test explícito que valida nas tentativas 5xx
- **Localização:** `bloco_dataset/scraper_tema_1378.py:152-158` + `tests/integration/test_task8b_cc25_fixes.py:test_http_get_passes_default_headers_to_client`
- **Problema:** Test atual verifica que headers são passados na **primeira chamada** httpx.Client. Mas o retry loop cria **novo client em cada attempt** (L154-158 dentro do for loop). Se houver bug futuro onde headers fossem aplicados condicionalmente (ex: só primeira tentativa), test não detectaria. Também não há test de "503 → 503 → 200" (retry success com headers preservados).
- **Evidência:** L152: `for attempt, backoff in enumerate(RETRY_BACKOFF_SECONDS, start=1):` cria contexto novo a cada iteration. Test mock usa `side_effect=_capturing_client` que captura **última** kwargs (o lambda sobrescreve dict a cada call); test passa porque httpx é mockado uma vez.
- **Recomendação:** Adicionar test específico:
  ```python
  def test_http_get_preserves_user_agent_through_retries():
      """F-05: headers presentes em CADA tentativa do retry loop."""
      captured_calls = []
      def _capturing_client(**kwargs):
          captured_calls.append(kwargs)
          # mock que falha 2x com 503 e sucesso na 3ª
          ...
      # assert len(captured_calls) == 3
      # assert all("User-Agent" in c["headers"] for c in captured_calls)
  ```
- **Verdict:** Fix correto, mas cobertura de teste **incompleta** — adicionar tech debt LOW.
- **Impacto:** Bug latente em retry path não detectado por test atual; aceitável porque arquitetura módulo-level constant garante. Defesa-em-profundidade pediria test explícito.

#### RR-02-CC25: [MED] F-08 race condition entre get_current() e set_state() em scenario concurrent
- **Localização:** `bloco_dataset/auto_trigger.py:77-89`
- **Problema:** Lógica F-08 lê state via `get_current()` (L78), avalia condição (L79-82), depois chama `set_state()` (L83-89). Entre os dois calls, **outro thread/processo pode modificar o state**. Cenário real:
  1. Scheduler thread chama `auto_trigger.run_camada_1_check`
  2. `get_current()` lê: nivel=vermelho, fail_count=2 (vermelho-via-fails)
  3. Maintainer faz POST `/monitor-tema/acknowledge` → `tema_1378_state.acknowledge()` muda state para amarelo (fail_count=2)
  4. `set_state()` em auto_trigger executa com `preserve_fail_count=True` (avaliado com state stale) e marca state como vermelho-via-tese mas com fail_count=2 → confusão
- **Evidência:** L78 (`current = tema_1378_state.get_current()`) e L83 (`tema_1378_state.set_state(...)`) não são atomic juntos. tema_1378_state usa atomic write para `set_state()` mas read+modify+write são separados aqui.
- **Recomendação:** 
  - **Curto prazo:** Adicionar nota em docstring "F-08 fix assume scheduler é único modificador entre acknowledge() events; race condition mínima na prática (cron daily 02:30 + acknowledge raro)"
  - **Longo prazo:** state machine deveria ter operação atomic `compare_and_swap` ou file lock — registrar como TD-T8B-F08-RACE-CONDITION (MED)
- **Verdict:** Fix correto **na maioria dos cenários**; race condition é edge case real mas baixa probabilidade (cron scheduler + acknowledge web são eventos esparsos).
- **Impacto:** Em caso muito raro, state pode ficar inconsistente (1 ciclo) até próxima auto-verificação corrigir. Não-bloqueante mas merece doc.

---

### 🟢 LOW (4)

#### RR-03-CC25: [LOW] F-01 env var parsing rígido — só aceita literal "true"
- **Localização:** `bloco_backup/scheduler.py:131-133`
- **Problema:** `os.environ.get("ENABLE_TEMA_1378_AUTO_CHECK", "false").lower() == "true"` aceita: `true`, `True`, `TRUE`, `tRuE`, `TRue`. Mas **NÃO aceita**: `"1"`, `"yes"`, `"on"`, `"enabled"` (convenções comuns em env vars). Também não trim whitespace: `" true "` (com espaço acidental) → `" true "` ≠ `"true"`.
- **Evidência:** L132: `.lower() == "true"` — match exato após lowercasing.
- **Recomendação:** Tolerar formato comum:
  ```python
  enable_tema_check = os.environ.get(
      "ENABLE_TEMA_1378_AUTO_CHECK", "false"
  ).strip().lower() in {"true", "1", "yes", "on", "enabled"}
  ```
  OU manter rígido + documentar em README/docs/.env.example o formato exato esperado (`"true"` literal).
- **Verdict:** Fix funciona; rigidez é **design choice defensável** (explicit é melhor que implicit). Eric pode preferir manter rígido para evitar `"true"` vs `"True"` ambiguity em scripts.
- **Impacto:** Eric coloca `ENABLE_TEMA_1378_AUTO_CHECK=1` em `.env` esperando habilitar → scheduler não registra job → debugar perde tempo. Mitigação: documentar formato.

#### RR-04-CC25: [LOW] F-01 env var não re-lida em runtime — toggle requer restart
- **Localização:** `bloco_backup/scheduler.py:131` + lifespan FastAPI
- **Problema:** `enable_tema_check` é avaliado **uma vez** quando `create_scheduler()` é chamado (lifespan startup). Se Eric toggle env var depois (via `.env` reload, container restart sem rebuild), scheduler já carregado mantém comportamento anterior. Comportamento esperado para feature flags simples, mas merece nota.
- **Evidência:** L131-133 — sem mecanismo de re-leitura periódica.
- **Recomendação:** Documentar em docstring: "Mudança em ENABLE_TEMA_1378_AUTO_CHECK requer reinicio do app para ter efeito (toggle não é hot-reload)."
- **Verdict:** Comportamento padrão Python env handling. Não é bug, é spec.
- **Impacto:** Eric muda env, espera efeito imediato, fica confuso. Fix: nota em docs/.env.example.

#### RR-05-CC25: [LOW] F-05 User-Agent URL pode ficar stale se repo renomeado
- **Localização:** `bloco_dataset/scraper_tema_1378.py:42-43`
- **Problema:** `"+https://github.com/Claudinoinsights/revisor-contratual"` é hardcoded no User-Agent. Se Eric renomear o repo (ex: `revisor-contratual` → `revisor-juridico`), ou mover org, UA aponta para 404. Não bloqueia funcionamento — UA é só metadata identificação — mas perde valor RFC bot identification (ponto inteiro era admin contactar via repo).
- **Evidência:** L43: URL literal no string concatenation.
- **Recomendação:** OU manter (aceitável; convenção comum) OU usar variável de pacote:
  ```python
  from importlib.metadata import metadata
  _repo_url = metadata("revisor-contratual").get("Home-page", "")
  ```
  Decisão Eric — prefiro hardcoded por simplicidade.
- **Verdict:** Aceitável. Não-bloqueante.
- **Impacto:** Se URL ficar stale, STJ admin que quiser identificar bot vai encontrar 404. Probabilidade baixa (repos raramente renomeados).

#### RR-06-CC25: [LOW] F-08 docstring não menciona caso vermelho-via-tese (fail_count=0) explicitamente
- **Localização:** `bloco_dataset/auto_trigger.py:63-67`
- **Problema:** Docstring diz "vermelho-via-fails-consecutivas (≥2)" mas NÃO menciona que vermelho-via-tese-detected (fail_count=0) tem comportamento diferente — esse caso, condição F-08 NÃO preserva (fail_count permanece 0, mas state vai para vermelho com tese atualizada). Test cobre (`test_auto_trigger_preserves_fail_count_when_red_with_tese_detected`), mas docstring é incompleta para reader que tente entender invariant sem ler tests.
- **Evidência:** L63-67 docstring; L82 condição.
- **Recomendação:** Adicionar à docstring:
  ```
  Nota: este invariant aplica-se SOMENTE a vermelho-via-fails-consecutivas
  (fail_count >= 2). Para vermelho-via-tese-detected (fail_count == 0), o
  set_state procede normalmente — tese atualizada substituiu state anterior.
  ```
- **Verdict:** Doc gap; código correto.
- **Impacto:** Mantenedor futuro debugando comportamento pode ficar confuso. Fix: 3 linhas docstring.

---

## Verificações empíricas adicionais

### Suite tests pós-CC.25 (re-validação)

- ✅ Suite 397 passed + 3 skipped preservada (zero regressão)
- ✅ 10 tests novos cobrem 3 fixes em paths principais
- ⚠️ Lacunas (registradas como RR-01, RR-06): retry headers explícito + race condition + docstring vermelho-via-tese

### Side effects scan

- ✅ `auto_trigger.run_camada_1_check` é chamado **apenas** por scheduler.add_job — nenhum outro caller espera comportamento antigo
- ✅ `DEFAULT_HEADERS` import — não há colisão com outros módulos (verificado via grep)
- ✅ `ENABLE_TEMA_1378_AUTO_CHECK` env var — não é referenciada em outro lugar do código (só `scheduler.py:131`)

### Tests legacy não-touched

- ✅ `test_create_scheduler_has_2_jobs` foi renomeado e atualizado — passa com flag=true
- ✅ Outros tests scheduler-related (`test_backup_daily_creates_dated_dir`, `test_backup_rotation_*`) não dependem de job 3 — passam sem env var

### Smoke test mental do código produção

Cenário 1: prod sem env var → `enable_tema_check = False` → scheduler 2 jobs (backup_daily + backup_rotation) → ✅ Esperado
Cenário 2: prod com `ENABLE_TEMA_1378_AUTO_CHECK=true` → scheduler 3 jobs → cron 02:30 dispara `run_camada_1_check` → httpx.Client com Mozilla UA → STJ retorna HTML → parser tenta 3 estratégias → state atualiza → ✅ Esperado
Cenário 3: prod com flag true mas STJ 403 (UA bloqueado mesmo com Mozilla) → ScraperError → `increment_fail()` → fail_count=1 amarelo → repete dia seguinte → fail_count=2 vermelho → maintainer ack → ✅ Esperado

---

## Verdict consolidado

**PASS-WITH-NOTES** ✅

### Resumo

| Aspecto | Avaliação |
|---|---|
| **Fix-correctness F-01 feature flag** | ✅ Correto |
| **Fix-correctness F-05 User-Agent** | ✅ Correto |
| **Fix-correctness F-08 invariant** | ✅ Correto |
| **Regressões funcionais** | ❌ Zero |
| **Cobertura de tests** | ⚠️ Boa, com lacunas LOW/MED |
| **Race conditions** | ⚠️ 1 MED edge case (não-bloqueante) |
| **Docstrings** | ⚠️ 1 LOW gap em F-08 |
| **Production readiness** | ✅ Defensável (com feature flag default-off) |

### Tech debts adicionais para `governance/TECH-DEBT.md`

| ID | SEV | Fonte | Descrição |
|----|-----|-------|-----------|
| TD-T8B-RR01 | MED | Smith re-review CC.26 | F-05 retry preserva headers — falta test explícito retries 5xx → 200 |
| TD-T8B-RR02 | MED | Smith re-review CC.26 | F-08 race condition get_current/set_state em concurrent (scheduler+acknowledge) |
| TD-T8B-RR03 | LOW | Smith re-review CC.26 | F-01 env parsing rígido — só "true" literal (não "1"/"yes"/"on") |
| TD-T8B-RR04 | LOW | Smith re-review CC.26 | F-01 env não re-lida runtime — toggle requer restart |
| TD-T8B-RR05 | LOW | Smith re-review CC.26 | F-05 UA URL hardcoded — stale-prone se repo renomeado |
| TD-T8B-RR06 | LOW | Smith re-review CC.26 | F-08 docstring incompleta — não menciona vermelho-via-tese (fail_count=0) |

**Recomendação merge:** ✅ **Merge OK** — 3 fixes determinísticos corretos, zero regressão, 0 HIGH/CRITICAL. Tech debts LOW/MED registrados para refinamento futuro.

### Próximo step sugerido

**A. Merge PR #2 com confidence reforçada** (RECOMENDADO):
- Smith re-review pós-fixes confirma fixes corretos
- 6 findings rastreados como tech debt
- Suite 397+3 estável

**B. Apply fix-of-fix mínimo (~30min Neo opcional):**
- Adicionar 3 docstring lines em `auto_trigger.py` (RR-06)
- Adicionar test explícito retry headers (RR-01)
- Não-bloqueante, mas zero-debt approach

---

## Smith verdict (cynical refinement)

> "Você queria saber se Neo fechou as portas ou só pintou as paredes. Resposta: as portas estão trancadas. As fechaduras são reais. Mas há frestas — uma corrente de ar entre as tábuas (race condition F-08), um marcador no chão que pode apagar (User-Agent URL hardcoded), um aviso na porta que diz 'true literal' mas não 'sim/yes/1' (env parsing rígido). Frestas não derrubam paredes — apenas convidam revisões futuras. Merge com olhos abertos."

— Smith (re-review canalizado por Oracle)

---

## Anexos

- Commit revisado: `6c5afaf`
- PR: https://github.com/Claudinoinsights/revisor-contratual/pull/2
- Smith review original: `governance/qa/smith-adversarial-review-t8b-cc25.md` (18 findings)
- Suite baseline pós-CC.25: 397 passed + 3 skipped
- Tempo de re-review: ~25min (focado em fix-correctness + regressões)
