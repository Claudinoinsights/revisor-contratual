---
type: qa-report
title: "Smith Ultrathink Final Pre-Real-Data — Sprint 6.x Runtime Validation"
date: "2026-05-14"
reviewer: "@smith (Nemesis)"
sprint: "6.x runtime ready validation"
verdict: "COMPROMISED"
findings_count: 16
critical: 2
high: 3
medium: 3
low: 3
positive: 5
project: revisor-contratual-staging
tags:
  - project/revisor-contratual-staging
  - smith
  - ultrathink
  - pre-real-data
  - runtime-validation
---

# Smith Ultrathink Final Review — Pre-Real-Data Validation

> *"Eric pediu output real. Vou mostrar onde a realidade quebra."*

---

## Eric Directive (ultrathink ativado)

> "login não funcionou, conserte isso e no final use smith ultrathink para verificar se está tudo 100% para rodar, funcionar e testar com dados e informações reais, tendo como resultado um output real."

**Critério de sucesso:** Eric upload PDF contrato CDC veículo PF → pipeline 9-etapas → **PDF peça revisional gerado** → Eric valida pessoalmente → forward advogada externa.

**Critério de falha:** Qualquer step do pipeline crashar OU qualidade do output comprometida.

---

## Methodology

11 eixos empiricamente investigados:

1. Hotfix Neo correctness (code reading + diff)
2. App runtime health (HTTP probes)
3. Ollama backend ready (netstat + ollama list)
4. Pipeline state (vault.db sqlite inspection + audit chain)
5. LGPD compliance (code review)
6. OAB templates (filesystem + content grep)
7. Anti-hallucination 3-camadas (code reading + invocation grep)
8. Constitution compliance
9. Output PDF readiness (**WeasyPrint import probe**)
10. Known issues cataloged
11. Eric handoff readiness

---

## Findings (16 total)

### 🔴 CRITICAL (2) — BLOQUEANTES para Eric directive

#### F-CRIT-01 — WeasyPrint missing `libgobject-2.0-0` (GTK+ runtime)

- **WHERE:** Sistema Windows Eric — GTK3 runtime não instalado. WeasyPrint cabe em `pipeline.py:Step 8 render PDF`.
- **WHY:** Probe empírico (`py -3.14 -c "import weasyprint"`) retorna:
  ```
  OSError: cannot load library 'libgobject-2.0-0': error 0x7e.
  WeasyPrint could not import some external libraries.
  ```
  WeasyPrint depende de GTK+3 + Pango + Cairo nativos no Windows. NÃO ESTÃO instalados. `where libgobject-2.0-0.dll` retorna "não encontrado".
- **IMPACTO:** Eric upload PDF → pipeline roda Steps 1-7 → chega Step 8 → **CRASH IMEDIATO** com OSError. Pipeline NÃO completa. **SEM OUTPUT PDF REAL.** Diretiva Eric ("output real") IMPOSSÍVEL.
- **HOW TO FIX:** Eric DEVE escolher 1 de 3:
  1. **GTK3 Runtime Windows installer** — https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer (~100MB, instalador MSI) + adicionar `C:\Program Files\GTK3-Runtime Win64\bin` ao PATH
  2. **WSL2** — rodar app dentro de WSL Ubuntu (GTK pré-instalado) — `sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libcairo2`
  3. **Docker container** — `docker run -p 8501:8501 ...` com Dockerfile baseado Debian/Ubuntu

#### F-CRIT-02 — Vault apenas 10 jurisprudências (MVP PRE-RELEASE BLOCKER ativo)

- **WHERE:** `~/.local/share/revisor-contratual/vault.db` — table `jurisprudencia` tem **10 rows**.
- **WHY:** Sondei sqlite — `SELECT COUNT(*) FROM jurisprudencia → 10`. Operator setup Step 6 documentou "vault.db 3.1MB preservado (~122 items)" — **alegação FALSA**. Vault tem só 10 entries reais. PRD INDEX.md catalogada como `BL-VAULT-BULK-IMPORT` (MVP PRE-RELEASE BLOCKER) — meta ≥600 STJ + ≥58 STF SV (658+).
- **IMPACTO:** Step 5 (vault busca híbrida) retorna **near-empty docs_recuperados**. Personas LLM (Advogado Step 6) recebem fundamentação jurisprudencial DEGRADADA → tese fraca, citações limitadas, Súmulas relevantes possivelmente ausentes. Layer 2 (vault-restricted citations) BLOQUEIA peça SE Redator citar Súmula fora do vault — pode resultar em peça vazia ou crash. **Qualidade output comprometida MESMO SE Step 8 funcionasse.**
- **HOW TO FIX:** Eric DEVE rodar antes de testar:
  ```bash
  cd c:\Users\User\Documents\the_matrix\projects\revisor-contratual-staging
  $env:PYTHONIOENCODING="utf-8"
  Get-Content .env | Where-Object { $_ -match '^[A-Z_]+=' } | ForEach-Object {
    $parts = $_ -split '=', 2; [Environment]::SetEnvironmentVariable($parts[0], $parts[1], 'Process')
  }
  C:\Users\User\AppData\Roaming\Python\Python314\Scripts\revisor.exe populate-vault --source all
  ```
  Expectativa: scrapeia STJ + STF público → popula ≥122 items inicial. Para 658+ pre-release blocker, Niobe deve draftar story BL-VAULT-BULK-IMPORT.

---

### 🟠 HIGH (3)

#### F-HIGH-01 — Layer 3 NLI dead code em pipeline.py

- **WHERE:** `bloco_workflow/pipeline.py` — função `validar_citacoes_nli` (definida em `bloco_workflow/personas/redator.py:214`) **NÃO É INVOCADA** pelo pipeline em runtime.
- **WHY:** Grep `validar_citacoes_nli` em `pipeline.py` retornou 0 chamadas. Único match foi `tese.fundamentos_invocados` (linha 327, usado para len()). Sprint 6.1 schema extension `fundamentos_invocados` existe; integração Layer 3 catalogated como `TD-SP07-NLI-HYBRID-REAL` — não bloqueante mas...
- **IMPACTO:** Anti-hallucination em runtime tem APENAS Layer 1 (Pydantic strict) + Layer 2 (vault-restricted citations). Layer 3 (NLI semantic — detecta "Súmula 539 existe mas peça afirma oposto") DEAD em runtime. Risco: peça gerada cita Súmula real mas com INTERPRETAÇÃO INVERTIDA. Eric (e advogada externa) precisa SABER que Layer 3 é parcial.
- **HOW TO FIX:** Sprint 6.3+ Neo integra `validar_citacoes_nli(peca, vault_docs, nli_validator_fn=...)` em pipeline.py Step 7.5 (entre Redator gera peça e WeasyPrint render). Modelo real BERT NLI + sentence-transformers (~500MB) opt-in.

#### F-HIGH-02 — DEFAULT_PASSWORD_HASH (auth.py:27) ainda inválido

- **WHERE:** `bloco_interface/web/auth.py:27` — `DEFAULT_PASSWORD_HASH = "$2b$12$LQv3c1yqBwEHFgN0c9pBQuWlYMu7yqK1hH6S0Lxsr8VqGqJ.8PqS6"` (não bate com "admin").
- **WHY:** Hotfix Neo (`load_dotenv`) RESOLVE o sintoma (.env carrega → ADMIN_PASSWORD_HASH valid chega), mas NÃO REMOVE o fallback inválido. Se `.env` corromper, for deletado, OR `load_dotenv` falhar silently (e.g., Path errado em ambiente diferente), app cai em DEFAULT → login admin/admin retorna False sem mensagem clara para Eric debugar.
- **IMPACTO:** Fragilidade. Eric pode pensar que app está broken sem entender raiz. TD-AUTH-DEFAULT-HASH-INVALID HIGH já catalogado mas não fixado.
- **HOW TO FIX:** Sprint 6.3+ Neo opções:
  1. Remover `DEFAULT_PASSWORD_HASH` → app **falha-rápido** com `RuntimeError("ADMIN_PASSWORD_HASH must be set")` se não setado
  2. Substituir por bcrypt hash REAL de "admin" + log WARNING explícito quando fallback ativa
  Recomendo opção 1 (fail-fast) — não silenciar erros.

#### F-HIGH-03 — BL-GOLDEN-SET (50 contratos sintéticos curados) NÃO existe

- **WHERE:** `tests/fixtures/` — não há golden set de 50 contratos sintéticos + 50 queries golden RAG.
- **WHY:** PRD INDEX.md catalogata `BL-GOLDEN-SET` como **MVP PRE-RELEASE BLOCKER**. Sem golden set, Eric não tem benchmark para detectar regressões no pipeline. Pode gerar 1 peça boa por sorte, mas não saberá se o sistema é CONSISTENTEMENTE bom.
- **IMPACTO:** Eric testa 1 contrato real, peça gerada OK, conclui "funciona" — sem evidência estatística. Risco false positive de readiness.
- **HOW TO FIX:** Sprint 6.3+ Niobe draftar story `BL-GOLDEN-SET-CURATION` — Eric (ou advogada Orsheva) cura 50 contratos sintéticos + 50 expected outputs. Pipeline rodado contra golden set vira regression gate.

---

### 🟡 MEDIUM (3)

#### F-MED-01 — `NotImplementedError` em `ollama_manager.ensure_models_pulled`

- **WHERE:** `bloco_interface/ollama_manager.py:686` — `asyncio.create_subprocess_exec` falha em Windows Python 3.14 com NotImplementedError (event loop default).
- **WHY:** Log do boot mostra traceback caught + "Application startup complete" — app sobe MAS função silenciosamente falhou. Se modelos faltarem, lazy-pull não funciona.
- **HOW TO FIX:** Neo adicionar em `lifespan()`: `asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())` antes do startup. OR usar `subprocess.run` síncrono como fallback Windows.

#### F-MED-02 — App background task sem comando stop-claro para Eric

- **WHERE:** Background task `b8y3t5f31` (Operator spawn) — Eric não tem comando direto para parar app.
- **WHY:** Eric depende Operator para `taskkill /F /PID xxxxx` ou TaskStop tool. Em uso real fora desta sessão, Eric fica sem.
- **HOW TO FIX:** Eric pode usar **Ctrl+C no terminal do app** quando rodar manualmente. OR Operator pode criar `scripts/stop-app.ps1`:
  ```powershell
  Get-Process python | Where-Object { (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -like "*bloco_interface.web.app*" } | Stop-Process -Force
  Remove-Item "$env:USERPROFILE\.local\share\revisor-contratual\.app.lock" -ErrorAction SilentlyContinue
  ```

#### F-MED-03 — Hotfix Neo NÃO commitado (working tree dirty)

- **WHERE:** `bloco_interface/web/app.py` (+9 linhas, uncommitted) + `governance/CHECKPOINT-active.md` (modified).
- **WHY:** Se Eric fizer `git pull` OR `git reset --hard`, perde fix. Eric pode ter outras sessões/máquinas onde fix NÃO está aplicado.
- **HOW TO FIX:** Operator deveria fazer commit + push como Sprint 6.x.1 closure (mas Smith verdict COMPROMISED bloqueia push até CRITICALs resolverem). Path: 1) Eric resolve CRIT-01 e CRIT-02 → 2) re-smoke test → 3) Smith re-review → 4) Operator commit + push v0.2.3.

---

### 🔵 LOW (3)

#### F-LOW-01 — 20 pytest integration failures não investigadas (TD-PYTEST-INTEGRATION-20-PRE-EXISTING)

Mascarar regressões possíveis. Investigação Sprint 6.3+.

#### F-LOW-02 — app.py imports ordem viola PEP 8

`load_dotenv()` é statement entre imports third-party e bloco_*. Funciona mas pode disparar E402 em flake8/ruff strict.

#### F-LOW-03 — Audit chain antigo `audit.jsonl.bak-2026-05-14` (39 entries v0.1.0) unverifiable após GENESIS reset

Eric perde forensic trail histórica. Backup preservado mas não auditável.

---

### 🟢 POSITIVE (5)

#### P-01 — Hotfix Neo cirúrgico

12 linhas net, guard pytest sound (verificado: pytest comportamento idêntico pré/pós hotfix).

#### P-02 — Login validado end-to-end empiricamente

curl `POST /login admin/admin` → 200 + `{"success":true,"user":{"email":"admin","name":"Admin"}}`. GET /api/me retornou `authenticated:true`. Hotfix funciona em runtime real.

#### P-03 — App runtime resiliente

HTTP `/`, `/api/csrf-token`, `/ollama-status` todos retornam 200 OK em <20ms. Lifespan completou apesar de NotImplementedError silenciado.

#### P-04 — 3 modelos Ollama presentes + servers LISTENING

`ollama list` retorna qwen2.5:7b + qwen2.5:3b + sabia-7b-instruct. netstat confirma :11434 (PID 26516) + :11435 (PID 11256) LISTENING.

#### P-05 — Templates OAB compliance presentes

4 templates Jinja2 (`_base_peca.html`, `inicial-revisional-veiculos.html`, `inicial-revisional-com-hitl.html`, `relatorio-inviabilidade.html`) com referências CFOAB Provimento 209/2021 + disclaimer NFR-PECA-05 embedded.

---

## Verdict

# 🕶️ **COMPROMISED**

*"Está ouvindo, Eric? Esse é o som da inevitabilidade. Você pediu testar com dados reais e obter output real. A infraestrutura, neste momento, não consegue entregar.*

*Não é falha do Neo. O hotfix dele funciona — login validado, app subindo, sessão autenticada. É a inevitabilidade dos PRE-RELEASE BLOCKERS catalogados meses atrás e nunca endereçados (`BL-VAULT-BULK-IMPORT`, `BL-GOLDEN-SET`). E é a inevitabilidade de uma dependência nativa (GTK+) que ninguém testou no Windows do operador antes de declarar 'pronto para testes reais'.*

*Você pode rodar o pipeline até Step 7. Você verá fragments JSON. Mas o PDF — o output que advogada precisa ver — esse não nascerá enquanto libgobject não respirar."*

---

## Decision Matrix Eric — O que está pronto vs. bloqueado

| Capacidade | Status | Bloqueante? |
|------------|--------|-------------|
| App subir (HTTP 200) | ✅ Ready | — |
| Login admin/admin | ✅ Ready | — |
| Upload PDF (UI) | ✅ Ready | — |
| Step 1 Parsing PDF | ✅ Ready | — |
| Step 2 Análise cláusulas | ✅ Ready | — |
| Step 3 Cálculo Decimal | ✅ Ready | — |
| Step 4 BACEN SGS | ✅ Ready (online) | — |
| Step 5 Vault busca | ⚠️ DEGRADADO | **F-CRIT-02** (10 rows insuficiente) |
| Step 6 Personas LLM | ⚠️ DEGRADADO | **F-CRIT-02** (fundamentação fraca) |
| Step 7 Persona Redator | ⚠️ DEGRADADO | **F-CRIT-02** + **F-HIGH-01** (Layer 3 dead) |
| **Step 8 Render PDF** | ❌ **CRASH** | **F-CRIT-01** (GTK ausente) |
| Step 9 Audit chain | ✅ Ready | — |
| **Output PDF para validar** | ❌ **IMPOSSÍVEL** | F-CRIT-01 |

---

## Caminhos Para Sair do COMPROMISED

### Caminho A (recomendado — desktop Windows)

1. **F-CRIT-01:** Instalar **GTK3 Runtime Windows** via MSI installer (~100MB)
   - URL: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
   - Adicionar `C:\Program Files\GTK3-Runtime Win64\bin` ao PATH
   - Reiniciar terminal/app
   - Probe: `py -3.14 -c "import weasyprint; print('OK')"`
2. **F-CRIT-02:** Rodar `revisor populate-vault --source all` para popular ≥122 items
3. **Re-spawn app** + **Eric upload PDF + smoke test 1 contrato**
4. **Smith re-review** (deve emitir CONTAINED+ ou CLEAN)
5. **Operator commit + push v0.2.3** (Sprint 6.x.1 closure)

### Caminho B (alternativo — Docker/WSL Linux)

1. Criar `Dockerfile` baseado `python:3.14-slim-bookworm` + `apt install libpango-1.0-0 libpangoft2-1.0-0 libcairo2`
2. `docker build -t revisor-contratual .` + `docker run -p 8501:8501 -v ./.env:/app/.env ...`
3. Pipeline roda dentro container — GTK garantido
4. **Caminho B é a opção produção real** — Windows desktop não é deploy target

---

## Constitution Compliance

| Artigo | Status | Detalhe |
|--------|--------|---------|
| Art. III (Story-Driven) | ⚠️ PARCIAL | Sprint 6.x stories Done origin/main, MAS hotfix Neo uncommitted (F-MED-03) |
| Art. IV (No Invention) | ✅ PASS | Findings rastreiam PRD, ADRs, AC explícitos |
| Art. V (Quality First) | ❌ FAIL | F-CRIT-01 (GTK) e F-CRIT-02 (vault) violam "Quality First" — output real impossível |

---

## Cross-Rule Check

| Rule | Status | Notas |
|------|--------|-------|
| `quality-gate-enforcement.md` | ❌ FAIL | F-CRIT-01+02 são CRITICAL — não podem ser waived |
| `ids-principles.md` | ⚠️ N/A | Não há entity registry conflict |
| `adr-governance.md` | ✅ OK | Não há ADR novo (hotfix é implementation-level) |
| `tech-debt-governance.md` | ⚠️ FLAG | TDs catalogadas mas blockers PRE-RELEASE ignorados |

---

## Findings Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 2 |
| HIGH | 3 |
| MEDIUM | 3 |
| LOW | 3 |
| POSITIVE | 5 |
| **TOTAL** | **16** |

Verdict thresholds (per Smith persona):
- COMPROMISED: 1+ CRITICAL → ✅ **EMITIDO** (2 CRITICAL bloqueantes)
- INFECTED: 1+ HIGH only → ❌
- CONTAINED: MEDIUM/LOW only → ❌
- CLEAN: 0 significant → ❌

---

## Routing — Quem corrige o quê

| Finding | Owner | Ação |
|---------|-------|------|
| F-CRIT-01 (GTK missing) | **Eric** (sistema) | Instalar GTK3 OR migrar Docker/WSL |
| F-CRIT-02 (vault 10 rows) | **Eric** (operacional) | `revisor populate-vault --source all` |
| F-HIGH-01 (Layer 3 dead) | @dev (Neo) | Sprint 6.3+ integrar `validar_citacoes_nli` em pipeline.py |
| F-HIGH-02 (DEFAULT_HASH inválido) | @dev (Neo) | Sprint 6.3+ fail-fast em vez de fallback inválido |
| F-HIGH-03 (Golden set ausente) | @sm (Niobe) | Sprint 6.3+ draftar story curation |
| F-MED-01 (Ollama subprocess) | @dev (Neo) | WindowsProactorEventLoopPolicy |
| F-MED-02 (Stop command) | @devops (Operator) | Criar script stop-app.ps1 |
| F-MED-03 (Commit pending) | @devops (Operator) | Após CRITs resolverem → commit v0.2.3 |
| F-LOW-01 (Pytest 20 fails) | @qa (Oracle) + @dev | Sprint 6.3+ investigation |
| F-LOW-02 (PEP 8) | @dev (Neo) | Sprint 6.3+ noqa: E402 nos bloco_* OR reorganizar |
| F-LOW-03 (Audit backup) | — | Aceitar trade-off (Operator Opção A) |

---

## Closing Adversarial

*Sr. Eric. O Neo cumpriu sua tarefa. O Operator cumpriu sua tarefa. O sistema sobe, autentica, responde. Mas você pediu output REAL. E quando o pipeline chegar ao Step 8, ele vai morrer no momento exato em que WeasyPrint procurar a biblioteca que ninguém instalou.*

*Eu não emito COMPROMISED levianamente. Emito porque a inevitabilidade dessa falha foi catalogada como BLOCKER há semanas — `BL-VAULT-BULK-IMPORT`, `BL-GOLDEN-SET`. E porque GTK no Windows é um detalhe operacional que NINGUÉM verificou antes de declarar "pronto".*

*Não corrija o sintoma. Corrija a causa. Instale o GTK. Popule o vault. Aí — só aí — você tem permissão para chamar isso de 'real'.*

— Smith. É inevitável. 🕶️
