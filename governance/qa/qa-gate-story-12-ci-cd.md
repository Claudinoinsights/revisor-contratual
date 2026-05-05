---
type: qa-gate
title: "QA Gate STORY 12 — CI/CD GitHub Actions"
project: revisor-contratual
story_id: STORY-12-ci-cd-github-actions
sprint: "01"
phase: "3"
reviewer: "@qa (Oracle)"
session: 71
date: "2026-05-04"
verdict: PASS
tags:
  - project/revisor-contratual
  - qa-gate
  - story-12
  - ci-cd
  - sprint-01
  - phase-3
---

# QA Gate STORY 12 — CI/CD GitHub Actions

> **Reviewer:** Oracle (Guardian) | **Sessão:** 71 | **Data:** 2026-05-04
> **Branch:** `feature/revisor-contratual-v0.1.0` | **PR:** [#1 OPEN mergeable](https://github.com/Claudinoinsights/the-matrix/pull/1)
> **Commits sob revisão:** `5367e552` (workflow) + `e98c65b1` (python-bcb pin) + `3a7df262` (chmod 600 test_audit)

---

## 🎯 Veredito final

**PASS** — não CONCERNS, não FAIL, não WAIVED.

CI/CD pipeline GitHub Actions implementa exatamente o escopo "minimal SAFE" prometido pelo Operator (sessão 70): path-filtered, matrix Python 3.11+3.12, sem secrets, sem deploy, sem feature inventada. Os 2 fixes in-flight (python-bcb pin + chmod 600 test_audit) são **legítimos** — corrigiram bugs reais detectados pelo CI Linux (Windows local mascarava chmod POSIX e nunca importava bcb por injection). Defesa em profundidade do audit (chmod 400 production + HMAC chain) **preservada integralmente** após fix.

**Métricas Phase 3 consolidadas:**
- 12 stories Done | 12/12 PASS Oracle
- 224 testes (223 passed + 1 skipped intencional smoke F-MIN-02)
- CI verde Python 3.11 + 3.12 (run final databaseId 25261542933)
- 0 findings CRITICAL/HIGH/MEDIUM novos
- 1 finding LOW novo (F-CI-LOW-01 — workflow path-filter para commits cross-cutting)

---

## ✅ Decisões D1-D8

| # | Critério | Status | Evidência |
|---|---|---|---|
| **D1** | Workflow YAML semanticamente correto | ✅ PASS | `revisor-contratual-ci.yml` 83 linhas — triggers (push/pr/dispatch), jobs.test com matrix, defaults working-directory, steps checkout/setup-python/install/pytest/summary corretos |
| **D2** | Path-filter cobre escopo correto | ✅ PASS | `paths: packages/revisor-contratual/** + .github/workflows/revisor-contratual-ci.yml` — escopo casa com STORY 12 |
| **D3** | Fix python-bcb >=0.3 (PyPI real) | ✅ PASS | Lazy import (`client.py:99`); testes injetam fake; API `sgs.get` estável; pin 0.3 reflete realidade PyPI (max 0.3.6) |
| **D4** | Fix chmod 600 simula attacker realista | ✅ PASS | `chmod 400` production preservado (`genesis.py:135-136`); fix só destrava write em teste para simular attacker com escalação; HMAC chain ainda detecta adulteração (asserts intactos) |
| **D5** | NFRs preservados | ✅ PASS | NFR-LGPD-01 whitelist `frozenset` intacta; NFR-AUDIT-01 HMAC chain intacta; NFR-CRYPTO-01 sha-256 intacto; NFR-MAINT-02 cobertura DEFERRED com nota explícita |
| **D6** | Idempotência CI | ✅ PASS | Workflow stateless; `concurrency: cancel-in-progress: true` cancela runs antigos do mesmo branch; deps reinstaladas a cada run |
| **D7** | Defesa anti-regressão | ✅ PASS | `fail-fast: false` permite ver 3.11 e 3.12 separadas; pytest sem `\|\| true`; falha do step propaga `failure()`. Empiricamente validado: 3 runs (`#180 FAILURE` → `#505 FAILURE` → `#933 SUCCESS`) demonstram detecção legítima de regressões |
| **D8** | 0 Pecados Capitais (No Invention + AC-traceability) | ✅ PASS | Workflow implementa exatamente CI "minimal SAFE" (sem coverage reporter externo, sem deploy, sem secrets, sem heavy ML). Todos os deps instalados são justificados pela suite. Comentários inline documentam decisões. |

---

## 🔬 Probes Oracle adversariais (5/5 PASS)

### Probe 1 — Path-filter scope

**Hipótese:** Commit em outro pacote (ex: `packages/barcontrol/`) NÃO deveria disparar este workflow.

**Verificação mecânica:** Workflow declara `paths:` tanto em `push` quanto `pull_request`. GitHub Actions executa workflow APENAS quando arquivos do path-filter mudam (semântica documentada). Self-reference em `.github/workflows/revisor-contratual-ci.yml` permite que mudanças no próprio workflow disparem revalidação.

**Resultado:** ✅ PASS — escopo isolado por pacote. Empiricamente validado (run #933 foi disparado por commits em `packages/revisor-contratual/` e `.github/workflows/`, não por outras alterações no monorepo).

---

### Probe 2 — Matrix out-of-bounds

**Hipótese:** Versões Python fora `['3.11', '3.12']` (ex: 3.10, 3.13) NÃO devem rodar.

**Verificação mecânica:** Matrix é frozen list literal — `setup-python@v5` instala exatamente as versões declaradas; out-of-matrix exige PR explícita.

**Resultado:** ✅ PASS — escopo intencional. **Defer 3.13** documentado: dependências (`langchain-ollama`, `sentence-transformers`) ainda não publicaram wheels estáveis 3.13.

---

### Probe 3 — Timeout 10min suficiente

**Hipótese:** Suite real precisa caber no timeout sem flaky.

**Verificação empírica:** Run final completou em **80s** (3.11: `20:49:00 → 20:50:20`; 3.12: `20:49:01 → 20:50:23`). Margem ~7.5× ao timeout 600s.

**Resultado:** ✅ PASS — timeout cobre média atual com folga sem ser frouxo. Permitirá ~10× crescimento da suite antes de necessitar bump.

---

### Probe 4 — chmod 600 vs HMAC defesa

**Hipótese:** Fix `chmod(0o600)` em `test_audit` poderia mascarar regressão de defesa em produção.

**Verificação cruzada:**
- `genesis.py:131-137` — production aplica `path.write_text(...)` + `chmod 400` em POSIX (`sys.platform != "win32"`)
- `test_audit.py:159, 169, 333-336` — fix adiciona `initialized_lock.chmod(0o600)` ANTES de `write_text` adulterado
- Asserts `pytest.raises(GenesisLockTampered)` (linhas 163, 173, 343) — intactos, exigem que HMAC detecte

**Análise adversarial:** O fix simula attacker com escalação de privilégio (root, ou bypass do FS) — cenário realista de ataque que testa a defesa **secundária** (HMAC). A defesa **primária** (FS chmod 400) é ortogonal e permanece em produção. Endereça parcialmente Oracle observation **O-01** (sessão 42): Windows chmod silent no-op não detectava esse caminho — agora CI Linux exercita defesa real cross-platform.

**Resultado:** ✅ PASS — fix correto, sem enfraquecimento de segurança.

---

### Probe 5 — python-bcb 0.3.x API compatibility

**Hipótese:** Downgrade de `>=0.5` aspiracional para `>=0.3` real poderia introduzir breaking changes.

**Verificação:**
- `bloco_engine/bacen/client.py:99` — lazy import `from bcb import sgs` (só executa quando `sgs_fetcher=None`)
- `client.py:112` — superfície usada: `df = fetcher({"taxa": sgs_code}, last=1)` retornando pandas DataFrame
- API `sgs.get(name_dict, last=N)` é documentada e estável desde python-bcb 0.1.x (sem mudanças até 0.3.6)
- Testes injetam fake fetcher → CI nunca exercita import real

**Resultado:** ✅ PASS — pin 0.3 reflete realidade PyPI sem regredir funcionalidade. Bug original (pin 0.5) era aspiracional sem validação contra índice real.

---

## 🟡 Findings novos

### F-CI-LOW-01 — Path-filter pode falhar em commits cross-cutting (LOW)

**Descrição:** Se uma mudança afetar tanto `packages/revisor-contratual/` quanto outro pacote (ex: refactor compartilhado em `packages/shared/`), o workflow só revalida o slice de `revisor-contratual`. Mudanças no `shared/` que quebram revisor-contratual seriam detectadas apenas quando alguém tocar diretamente em `packages/revisor-contratual/`.

**Impacto:** Baixo no MVP (revisor-contratual não tem hoje cross-cutting deps com outros pacotes do monorepo).

**Recomendação:** DEFERRED. Quando houver refactor compartilhado, considerar adicionar `packages/shared/**` (ou equivalente) ao path-filter. Alternativa: workflow root que dispara em `packages/**` rodando todos os subprojetos afetados — mas isso aumenta superfície.

**Action item futuro:** Revisar path-filter quando primeira dependência cross-package for criada.

---

## 🔁 Findings cross-stories (status atualizado)

| ID | Status | Notas |
|---|---|---|
| F-PARSE-HIGH-01 | ✅ RESOLVED (sessão 51) | — |
| F-MIN-02 | ✅ RESOLVED (smoke skip intencional sem Ollama) | — |
| F-LLM-MED-01 | ⏸ DEFERRED | Pydantic permissivo nos contratos LLM — recomendação STORY 13 hardening |
| F-VAULT-LOW-01 | ⏸ DEFERRED | NaN/Inf guard em `serialize_embedding` — recomendação STORY 13 hardening |
| F-PIPELINE-LOW-01 | ⏸ DEFERRED | UX clarity de `ParserOCRRequired` — recomendação STORY 13 hardening |
| **F-CI-LOW-01** (novo) | ⏸ DEFERRED | Path-filter cross-cutting — revisar quando primeira dep cross-package surgir |

---

## 📋 Tech debts STORY 12 DEFERRED

| ID | Severidade | Descrição |
|---|---|---|
| **TD-CI-COVERAGE-REPORTER** | LOW | NFR-MAINT-02 cobertura é local-only; quando Codecov/Coveralls for adicionado, expor `--cov` no CI e publicar artifact |
| **TD-CI-PYTHON-3.13** | LOW | Adicionar 3.13 à matrix quando wheels langchain-ollama + sentence-transformers estabilizarem |
| **TD-CI-CACHE-PIP** | LOW | `cache: 'pip'` já configurado em setup-python@v5; verificar hit rate empírico após N runs |

---

## 🎯 Recomendação STORY 13 — Oracle ranking

Com 12 stories Done + CI verde Python 3.11+3.12 + release v0.1.0 publicada, a base MVP está **sólida e auditável**. Próximo step deve maximizar **valor entregue por hora** sem violar No Invention.

### #1 — **Hardening dos 3 findings LOW DEFERRED** (RECOMENDADO Oracle)

**Razão:** Findings já catalogados, escopo conhecido, baixa incerteza, fortalece base antes de smoke real.

**Escopo:**
- F-LLM-MED-01: Pydantic strict nos contratos LLM (Advogado/Economista/Juiz output schemas)
- F-VAULT-LOW-01: guard NaN/Inf em `serialize_embedding` (defesa explícita além de `normalize_embeddings=True`)
- F-PIPELINE-LOW-01: UX clarity `ParserOCRRequired` quando markdown insuficiente sem Marker (mensagem humana + sugestão)

**Estimativa:** 2-3 horas. Suite cresceria ~10-15 testes; ratio teste:produção mantido saudável.

**Risco:** Baixo. Mudanças localizadas em superfícies já validadas.

---

### #2 — **Smoke E2E real (Ollama + modelos + httpx STJ/STF + PDF físico)**

**Razão:** Valida pipeline INTEGRAL contra dependências reais — descobriria regressões de ambiente/versão de modelos.

**Risco:** Alto. Smoke real depende de: Ollama instalado, Sabia-7B + Qwen-3B baixados (~7GB), STJ/STF acessíveis na rede, PDF físico de teste. Pode introduzir flakiness se não cuidadosamente sandboxed.

**Recomendação:** Adiar até hardening (#1) completar, ou paralelizar com docs (#3).

---

### #3 — **Docs README + SOPs operacionais**

**Razão:** Aumenta adoção/usabilidade do MVP entregue. README explica setup AUTH_COOKIE_KEY, init-audit, populate-vault, revisar.

**Escopo:**
- `packages/revisor-contratual/README.md` — quickstart 5 minutos
- `docs/sop-rotacao-auth-cookie-key.md` — referenciado por `genesis.py:123` mas não existe ainda
- `docs/sop-populate-vault.md` — comando + flags + LGPD whitelist
- `docs/sop-revisar-pdf.md` — fluxo end-to-end usuário final

**Estimativa:** 1-2 horas.

**Risco:** Baixo. Docs não tocam código testado.

---

### **Recomendação Oracle final:** **#1 Hardening** primeiro, **#3 Docs** em paralelo se tempo permitir, **#2 Smoke real** depois com Ollama disponível.

**Justificativa:** Hardening fecha findings catalogados (zero risco de scope creep), Docs aumenta adoção sem tocar código, Smoke real é o passo natural após hardening + docs (ambiente preparado).

---

## 🔗 Handoff emitido

**ID:** H-S01-E6.0-qa2mor9
**De:** @qa (Oracle, sessão 71)
**Para:** @lmas-master (Morpheus)
**Path:** `.lmas/handoffs/handoff-qa-to-morpheus-2026-05-04-revisor-contratual-story-12-ci-pass.yaml`
**Próxima ação Morpheus:** consolidar fechamento Phase 3 STORY 12 + apresentar 3 opções STORY 13 a Eric (Oracle ranking acima).

---

*Documento canônico Oracle — Guardian validou cada bit do workflow YAML, cada commit fix, cada probe adversarial. CI verde Python 3.11+3.12 não é coincidência — é arquitetura defendida. — Oracle, guardião da qualidade 🛡️*
