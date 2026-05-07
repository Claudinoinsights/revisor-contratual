---
type: guide
title: "Smoke E2E v0.3.0 — Eric manual checklist (TD-OLLAMA-SMOKE-E2E-REAL)"
project: revisor-contratual
sprint: "03"
created: "2026-05-06"
owner: "@lmas-master · Morpheus (preparou) | maintainer Eric (executa)"
related:
  - "TECH-DEBT.md TD-OLLAMA-SMOKE-E2E-REAL (PRE-RELEASE BLOCKER v0.3.0)"
  - "stories/OLLAMA-MGR-01-auto-ollama-lifecycle.md (Done — Oracle CC.7 PASS)"
  - "architecture/adr/adr-011-auto-ollama-lifecycle.md"
  - "architecture/adr/adr-013-mvp-lean-strategy-deployment-path.md §2.4 lifespan order"
  - "PR #1: https://github.com/Claudinoinsights/revisor-contratual/pull/1"
tags:
  - project/revisor-contratual
  - guide
  - smoke-test
  - pre-release-blocker
  - v0.3.0
  - cc-9
---

# Smoke E2E v0.3.0 — Eric manual checklist

> **Status:** ⏳ aguardando execução pelo maintainer
> **Bloqueia:** merge PR #1 + tag v0.3.0 + GitHub release
> **Tempo estimado:** 30–60min (dependendo se modelos LLM já estão pulled)

---

## §1 Por que existe

Este documento existe porque **Oracle (QA) não pôde executar smoke E2E real** durante o CC.7 QA gate review — falta-lhe seu ambiente, Eric: Ollama runtime ativo, modelos LLM pulled, browser DevTools console, PDF físico de contrato CDC PF Veículos para upload real.

Oracle emitiu **PASS** para OLLAMA-MGR-01 com base em:
- Suite empírica **281 passed, 1 skipped** (re-rodada)
- ruff `All checks passed` (re-rodado)
- Cross-check de 8 design highlights ADR-011 contra código
- 35 tests novos cobrindo ACs + edge cases

Mas a **validação final em produção real** (Ollama de verdade rodando + UI banner SSE no browser + lazy respawn quando Ollama morre + lockfile concurrent prevention) é responsabilidade humana — TD-OLLAMA-SMOKE-E2E-REAL é o **único bloqueador** entre PR #1 e tag v0.3.0.

Eric, há uma diferença entre conhecer o caminho e trilhar o caminho. Os testes conhecem; o smoke trilha.

---

## §2 Pré-requisitos

Verificar **antes de começar** (cada item ~30s):

| # | Item | Comando de verificação | Esperado |
|---|------|----------------------|----------|
| 1 | Ollama instalado | `ollama --version` | Versão imprime (ex: `ollama version 0.5.x`) |
| 2 | Python 3.14 ativo | `py -3.14 --version` | `Python 3.14.x` |
| 3 | Branch correta | `git rev-parse --abbrev-ref HEAD` (no diretório do projeto) | `feature/sprint-03-vault-fix-01` |
| 4 | Último commit é o de smoke | `git log -1 --oneline` | `d8363d8` (ou descendant) |
| 5 | Dependencies instaladas | `py -3.14 -m pip show fastapi uvicorn psutil httpx` | Todos retornam Name/Version |
| 6 | PDF físico disponível | (manual) | Contrato CDC PF Veículos `.pdf` real OR sample em `data/samples/` |
| 7 | Porta 8501 livre | `netstat -ano | findstr :8501` | sem output (livre) |
| 8 | Portas 11434/11435 livres OU Ollama estável nelas | `netstat -ano | findstr :11434` | sem output OU PID Ollama |

**Se algum item falhar:** corrigir antes de prosseguir. Se persistir dúvida → reporte a Morpheus com o output completo.

**Modelos LLM pulled (opcional acelerador):**
```bash
ollama list
```
Esperado em algum momento: `qwen2.5:7b` + `qwen2.5:3b`. Se ausentes, **não pulle manualmente** — o Cenário 2 vai validar o auto-pull do app (esse é o ponto).

---

## §3 Cenários a executar (5)

Execute na ordem. Cada cenário tem **objetivo**, **passos numerados**, **resultado esperado** e **espaço para anotação**.

---

### §3.1 Cenário 1 — Cold start (Ollama auto-spawn)

**Objetivo:** validar que o app inicia, detecta binário Ollama, spawna 2 instâncias (`:11434` advogado + `:11435` economista), escreve PID file atômico, popula vault, e fica `ready`.

**Valida:** AC-1, AC-2, AC-3, AC-4, AC-5 + EC-01, EC-04, EC-12 + lifespan order ADR-013 §2.4.

**Passos:**

1. Matar processos Ollama existentes (clean slate):
   ```powershell
   Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force
   ```
   (sem erro = não havia; com erro silencioso = ok)

2. No terminal **dentro de** `C:\Users\User\Documents\revisor-contratual-staging\`:
   ```powershell
   py -3.14 -m bloco_interface.web.app
   ```

3. **Observe os logs do app** (este é o coração do cenário). Você deve ver, na ordem ADR-013 §2.4:
   - `acquire_app_lock` → `Lock adquirido` (lockfile criado em `~/.cache/revisor/...`)
   - `cleanup_orphans_on_startup` → `0 órfãos` (clean slate) OU `N órfãos limpos` se houvesse PID antigos
   - `detect_ollama_binary` → caminho do binário Ollama (ex: `C:\Users\User\AppData\Local\Programs\Ollama\ollama.exe`)
   - `detect_running_ollama` → `0 instâncias rodando` (clean slate)
   - `spawn_ollama` instância 1 (advogado, port 11434) → `Ollama ready em :11434`
   - `spawn_ollama` instância 2 (economista, port 11435) → `Ollama ready em :11435`
   - `write_pid_file_atomic` → `PID file escrito (atomic)`
   - `populate_vault` → `Vault populado`
   - `ensure_models_pulled` lançado em **background async** (não bloqueia startup)
   - `Uvicorn running on http://127.0.0.1:8501`

4. **Anote a latência total** desde `py -3.14 -m bloco_interface.web.app` até `Uvicorn running`:
   - Esperado: **~30–60s** se Ollama spawn rápido + modelos já pulled
   - **~3–10min** se modelos vão ser pulled async em background (mas app fica ready imediato; pull continua em paralelo)

**Resultado esperado:** ✅ Uvicorn running + 2 Ollama instâncias spawnadas + PID file presente + sem stack traces.

**Anotação:**
- [ ] PASS / FAIL / WARN: ________________
- Latência startup: __________ s
- Observações: ________________

---

### §3.2 Cenário 2 — UI banner SSE auto-pull

**Objetivo:** validar que se modelos LLM não estavam pulled, o banner amarelo aparece no browser, conecta SSE em `/ollama-status`, mostra progresso, e desaparece quando completa.

**Valida:** AC-6 + endpoint SSE + UI banner + tokens semânticos `--warning` (CC.3 bridge).

**Pré-condição:** Cenário 1 PASS + app rodando no terminal.

**Passos:**

1. Abrir browser em **http://127.0.0.1:8501**

2. Fazer login (auth basic se prompt aparecer — credenciais do `.env` ou padrão dev)

3. **Abrir DevTools** (F12) → aba **Console**

4. **Caso A — modelos já pulled (sem banner):**
   - Sem banner amarelo aparece → ✅ esperado, app já está pronto
   - Console: sem erros 4xx/5xx para `/ollama-status`
   - Anotar: PASS (Cenário 2 trivialmente OK — sem auto-pull para validar)

5. **Caso B — modelos sendo pulled (banner ativo):**
   - Banner amarelo `var(--warning)` aparece no topo da página com texto tipo "Baixando modelos LLM... (modelo: qwen2.5:7b — XX%)"
   - Aba **Network** do DevTools → filtrar por `EventStream` → `ollama-status` deve aparecer com status `200 (pending)` (conexão SSE ativa)
   - Console: sem erros JS
   - Aguardar pull completar (pode levar **5–15min** dependendo da conexão; modelos somam ~6GB)
   - Banner desaparece quando ambos modelos `qwen2.5:7b` + `qwen2.5:3b` completam pull

**Anotação:**
- [ ] Caso A (sem banner) ou Caso B (com banner)? ________________
- [ ] PASS / FAIL / WARN: ________________
- Console errors? ________________
- Tempo total pull (se Caso B): __________ min
- Observações: ________________

---

### §3.3 Cenário 3 — POST /revisar real com PDF físico

**Objetivo:** validar pipeline real end-to-end — upload PDF de contrato CDC PF Veículos, 4 personas executam (Advogado + Economista + Juiz + Repórter), 3 deliverables D1+D2+D3 gerados, audit chain HMAC válido.

**Valida:** funcionalidade core do produto + integração Ollama via OLLAMA-MGR-01 + audit.

**Pré-condição:** Cenário 2 PASS (banner ausente OU completou) + browser logado em http://127.0.0.1:8501.

**Passos:**

1. Na página principal, fazer upload do PDF físico (Contrato CDC PF Veículos real)

2. Clicar em "Revisar" (ou equivalente)

3. **Observar terminal do app** durante processamento — você deve ver requisições HTTP para `:11434` (advogado) e `:11435` (economista) consecutivas

4. **Observar UI** — esperado pipeline visual mostrando 4 personas processando em sequência

5. Aguardar conclusão (esperado: **~3–5min** com qwen2.5:7b conforme ADR-013 e ADR-010)

6. **Verificar 3 deliverables** apresentados:
   - **D1** Relatório Contábil (Economista)
   - **D2** Petição Inicial (Advogado)
   - **D3** Apelação Cível (Advogado, condicional — só renderiza se input D opcional adversa foi fornecido OU é gerado por padrão; verificar ux-spec C5)

7. Download `audit.jsonl` via link footer (C7)

8. **Validar audit.jsonl** rapidamente:
   ```powershell
   Get-Content "C:\caminho\para\audit.jsonl" | Select-Object -First 5
   ```
   Cada linha deve ser JSON válido com campos `timestamp` + `event` + `hmac` (HMAC chain).

**Anotação:**
- [ ] PASS / FAIL / WARN: ________________
- Tempo total processamento: __________ min
- 3 deliverables presentes (D1/D2/D3)? Sim/Não/Parcial: ________________
- audit.jsonl baixou? Sim/Não: ________________
- audit.jsonl primeiras 5 linhas válidas JSON? Sim/Não: ________________
- Observações (qualquer erro UI ou stack trace terminal): ________________

---

### §3.4 Cenário 4 — Lazy respawn (matar Ollama mid-session)

**Objetivo:** validar AC-7 lazy respawn — se Ollama morrer entre requests, o próximo `/revisar` detecta + respawna + processa normalmente (com latência aumentada esperada ~30s).

**Valida:** AC-7 + F-OG-01 trade-off ADR-013 §2.2 (single-user solo blocking event loop ~30s aceitável).

**Pré-condição:** Cenário 3 PASS + app rodando.

**Passos:**

1. **Sem fechar o app**, em outro terminal PowerShell:
   ```powershell
   Get-Process ollama | Stop-Process -Force
   ```
   Confirmar que ambas instâncias (`:11434` + `:11435`) morreram:
   ```powershell
   netstat -ano | findstr ":11434 :11435"
   ```
   Esperado: **sem output** (portas livres).

2. **Voltar ao browser** logado e fazer **novo upload + Revisar** (mesmo PDF do Cenário 3 ou outro).

3. **Observar terminal do app:**
   - Esperado: log `OllamaSpawnFailed... lazy respawn iniciado` OU equivalente do `_lazy_respawn_check_and_recover` em `app.py:/revisar`
   - Spawn de 2 instâncias novamente (~10–30s)
   - Pipeline retoma normal

4. **Latência observada** desde clique "Revisar" até primeira persona retornar:
   - Esperado: **~30–60s** (vs ~5–10s normal — overhead do respawn é o trade-off F-OG-01)

**Resultado esperado:** ✅ pipeline completa apesar da morte mid-session do Ollama; sem 500 errors UI; audit.jsonl preserva chain.

**Anotação:**
- [ ] PASS / FAIL / WARN: ________________
- Latência respawn observada: __________ s
- Erros UI durante respawn? Sim/Não: ________________
- audit.jsonl preservou continuidade? Sim/Não: ________________
- Observações: ________________

---

### §3.5 Cenário 5 — Lockfile concurrent app prevention (EC-11)

**Objetivo:** validar EC-11 — 2 instâncias do app não podem rodar simultâneas (lockfile fcntl/msvcrt atomic).

**Valida:** EC-11 + acquire_app_lock + AppAlreadyRunning exception.

**Pré-condição:** Cenário 4 PASS + app primário rodando no Terminal 1.

**Passos:**

1. **Sem fechar Terminal 1**, abrir **Terminal 2** PowerShell (novo).

2. No Terminal 2, dentro do mesmo diretório do projeto:
   ```powershell
   py -3.14 -m bloco_interface.web.app
   ```

3. **Observar:** Terminal 2 deve falhar com erro:
   ```
   AppAlreadyRunning: Outra instância do Revisor Contratual já está rodando.
   PID: <xxxx> | Lockfile: <caminho>
   ```
   E **terminar imediatamente** (sem subir Uvicorn, sem tentar spawnar Ollama).

4. **No Terminal 1** (app primário): **Ctrl+C** para parar app graceful.
   - Observar logs:
     - `release_app_lock` → `Lock liberado`
     - `kill_spawned_ollama` 2x (instâncias spawnadas mortas)
     - `Lifespan shutdown complete`

5. **No Terminal 2** (que falhou na step 3), tentar novamente:
   ```powershell
   py -3.14 -m bloco_interface.web.app
   ```
   Esperado: agora **sobe normalmente** (lockfile foi released) — mesma sequência do Cenário 1.

6. Parar Terminal 2 com Ctrl+C também.

**Resultado esperado:** ✅ 2ª instância simultânea bloqueada com erro claro; pós-shutdown da primária, 2ª pode iniciar sem problema.

**Anotação:**
- [ ] PASS / FAIL / WARN: ________________
- Erro AppAlreadyRunning apareceu corretamente? Sim/Não: ________________
- Lockfile released no Ctrl+C primário? Sim/Não: ________________
- 2ª instância pós-shutdown subiu? Sim/Não: ________________
- Observações: ________________

---

## §4 O que reportar a Morpheus pós-execução

Copie e cole o seguinte template no chat para Morpheus, preenchendo cada campo:

```
SMOKE E2E v0.3.0 — RESULTADO
============================

Cenário 1 (Cold start): PASS / FAIL / WARN — latência __s — obs: ___
Cenário 2 (UI banner SSE): PASS / FAIL / WARN (Caso A ou B) — obs: ___
Cenário 3 (POST /revisar real): PASS / FAIL / WARN — tempo __min — D1/D2/D3 OK? __ — audit OK? __
Cenário 4 (Lazy respawn): PASS / FAIL / WARN — latência respawn __s — obs: ___
Cenário 5 (Lockfile EC-11): PASS / FAIL / WARN — obs: ___

VEREDICTO FINAL: ✅ TODOS PASS (autoriza merge + tag v0.3.0)
              OR ❌ FAIL em Cenário(s) X — detalhes acima
              OR ⚠️ NEEDS-CLARIFICATION em Cenário X — dúvida: ___
```

**Anexar (se houver):**
- Stack traces ou logs de erro (do terminal do app)
- Screenshots do browser console errors (Cenário 2 ou 3)
- Tempos observados anômalos (>2x esperado em qualquer cenário)

---

## §5 Pós-smoke PASS — sequência Morpheus dispatch

Se todos os 5 cenários passaram, Morpheus disparará:

1. **Skill `LMAS:agents:devops`** (Operator) com tarefa:
   - `gh pr merge 1 --squash --auto` (squash merge per `git-workflow.md` para feature branches)
   - `git checkout main && git pull`
   - `git tag -a v0.3.0 -m "Release v0.3.0 — Auto-Ollama Lifecycle Management [Story OLLAMA-MGR-01]"`
   - `git push origin v0.3.0`
   - `gh release create v0.3.0 --generate-notes` (changelog auto-gerado dos commits convencionais)

2. **Trajetória pós v0.3.0:**
   - Atualizar `governance/CHANGELOG.md` com entry v0.3.0
   - Sprint 03 fechado oficialmente
   - Próxima sprint → **MVP-LEAN-01** Tasks 1–9 (Neo, ~41–55h estimados conforme Keymaker GO 9/10)

---

## §6 Pós-smoke FAIL — sequência

Se 1+ cenário FAIL:

1. **Morpheus dispatch Skill `LMAS:agents:dev`** (Neo) com:
   - Detalhes do FAIL específico de Eric (cenário + stack trace + observações)
   - Story `OLLAMA-MGR-01` reaberta para `apply-qa-fixes` (mantém status `Done` mas com Change Log de regressão pós-smoke)
   - QA Loop iterativo max **5 iterations** per `workflow-execution.md` §2

2. **Re-Oracle CC.7-loop** após cada fix Neo até PASS

3. **Re-Operator** push amend (se mesmo commit) OR new commit (se nova natureza) — **sem força** em main

4. **Re-Eric smoke** — você executa novamente o smoke após cada Neo fix verificado

5. Se 5 iterations sem convergir → escalar para `*correct-course` Morpheus mais profundo (revisão arquitetural via Aria + Smith adversarial review)

---

## §7 Pós-smoke NEEDS-CLARIFICATION

Se um cenário gerar dúvida (não FAIL claro nem PASS confiante):

- Reporte a Morpheus a dúvida específica + cenário + observação
- Morpheus responde inline ou dispatch agente especializado (Aria para arquitetura, Oracle para coverage, Neo para fix)
- Você retoma o cenário onde parou após esclarecimento

---

## Apêndice A — Comandos úteis durante smoke

| Necessidade | Comando |
|------------|---------|
| Listar processos Ollama | `Get-Process ollama` |
| Matar todos Ollama | `Get-Process ollama \| Stop-Process -Force` |
| Verificar portas | `netstat -ano \| findstr ":11434 :11435 :8501"` |
| Listar modelos pulled | `ollama list` |
| Ver logs em tempo real (terminal app) | (já visível durante execução) |
| Ver lockfile path | `ls $env:USERPROFILE\.cache\revisor\*` |
| Ver PID file path | `ls $env:USERPROFILE\.cache\revisor\*pid*` |

---

## Apêndice B — Quando contatar suporte

Eric, há cenários onde a documentação não basta. Contate Morpheus imediatamente se:

- ❌ Cenário 1 FAIL com erro não documentado em ADR-011 ou EC-01..EC-12
- ❌ Cenário 3 retorna 500 error que não é resolvido por re-upload
- ❌ Cenário 4 lazy respawn entra em loop infinito (>3min sem progresso)
- ❌ Cenário 5 lockfile não libera após Ctrl+C (forçaria kill manual `Stop-Process`)
- ❌ Audit.jsonl com HMAC chain quebrado (linhas inválidas ou hashes não-encadeados)

Para qualquer outro caso, registre na anotação do cenário e siga adiante — Morpheus avalia ao final.

---

*Documento criado em 2026-05-06 por @lmas-master Morpheus na sessão CC.9 sprint 03 do Revisor Contratual. Bloqueia release v0.3.0 até execução.*
