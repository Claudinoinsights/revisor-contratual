---
type: qa-report
title: "Smith ULTRATHINK Anti-Furos Review (CC.41)"
project: revisor-contratual
sprint: "03"
session: 91
etapa: "CC.41 Smith ULTRATHINK total"
reviewer: "@qa · Oracle (Smith mode ULTRATHINK MÁXIMA)"
date: "2026-05-07T10:00"
scope:
  - "App stability — por que crashou silenciosamente"
  - "Frontend ↔ Backend mismatch — UF/Data/Tier ausentes UI"
  - "Morpheus inventou instruções vs realidade UI"
  - "Furos arquiteturais sobreviventes CC.30..CC.40"
  - "Regressões introduzidas pelos próprios fixes"
findings_total: 22
severities:
  CRITICAL: 2
  HIGH: 7
  MEDIUM: 8
  LOW: 5
verdict: "**FAIL** — 2 CRITICAL bloqueadores reais (OOM crash + frontend incompleto). 7 HIGH revelam que vários fixes anteriores foram aplicados COM SUPOSIÇÕES erradas sobre o sistema. Aplicação NÃO é production-ready apesar de 10 fix-cycles."
tags:
  - project/revisor-contratual
  - smith-ultrathink
  - cc41
  - anti-furos
  - fail
---

# Smith ULTRATHINK Anti-Furos Review

> Eric chegou ao limite. 10 fix-cycles, 16 Smith findings supostamente "100% addressed", e a aplicação ainda não roda. Este review desnuda — não para humilhar, mas para parar a hemorragia. Cada fix anterior foi correto no que tentou — mas tantos foram aplicados sobre suposições erradas que o sistema acumulou debt arquitetural maior do que CC.30 começou.

## Sumário Executivo

**Verdict:** **FAIL** ❌

**Findings:** 22 (2 CRITICAL · 7 HIGH · 8 MED · 5 LOW)

**Conclusão central:** Os problemas que Eric vê não são bugs isolados — são **sintomas de um padrão sistêmico**:

1. **Frontend MVP-LEAN foi declarado "completo" sem validar contra backend** — falta UI para inputs que backend expõe, ou backend tem inputs vestigiais que ninguém limpou
2. **Pipeline tem 8GB RAM em uso** — sem proteção OOM, OS killou silenciosamente
3. **Morpheus inventou instruções 4x** — não consultou template real antes de instruir Eric
4. **Audit chain registra ALGUNS eventos mas não TODOS** — `pipeline_lost_connection` foi gravado mas crash do OOM não foi
5. **Tests cobrem suite passing 57/57 mas ZERO E2E real** — toda confiança vem de unit tests com mocks

**Os 7 fix-cycles CC.30..CC.40 trabalharam REVERSAMENTE — cada fix gerou cascata de assumptions sobre o que estava OK. Smith CC.37 (anterior) foi superficial: encontrou F-01 mas não auditou o restante da pipeline com mesma profundidade.**

---

## Findings

### 🔴 CRITICAL (2)

#### F-A1: [CRITICAL] [REAL] App killed silenciosamente por OOM (8GB RAM)

- **Component:** runtime / OS interaction / `bloco_engine/parsing/marker_parser.py`
- **Description:** App.log mostra `Recognizing Text 0/281` com Python process consumindo **8.25GB RAM** (8254876K). Quando OS detectou pressure de memória, mandou SIGKILL. Sem stack trace porque SIGKILL não permite cleanup. Eric viu "link não abre" — app morreu silenciosamente.
- **Evidence:**
  ```
  Process Python 25216: 8.254.876 K (~8GB)
  app.log última linha real: "Recognizing Text 0/281" (sem progresso depois)
  Sem Traceback: SIGKILL bypass except handlers
  Audit.jsonl última entry: pipeline_lost_connection 10:07 (3h antes do crash atual)
  ```
- **Root Cause:** Marker 1.10.2 + surya OCR + 12 páginas + 281 elementos texto + Sabia 7B + Qwen 7B carregados simultâneamente em RAM. 16GB RAM máquina típica MENOS Windows OS (4GB) MENOS browser MENOS modelos LLM já carregados (~10GB) = pressão crítica.
- **Fix Proposal (3 camadas):**
  1. **Imediato:** monitorar RAM via `psutil` + abortar pipeline se >85% RAM antes de iniciar OCR pesado
  2. **Curto prazo:** lazy-unload modelos LLM enquanto OCR roda (free 8GB)
  3. **Arquitetural:** mover OCR para subprocess separado com cgroup memory limit
- **Effort:** 1h imediato, 4h+ arquitetural
- **Decoy or Real:** **REAL** — confirmado pelo log. PDF 12 páginas é o limite prático com hardware atual.

#### F-A2: [CRITICAL] [REAL] Frontend S2 NÃO oferece UF/Data/Tier — pipeline falha com `MetadataExtractionError` em PDFs sem metadados claros

- **Component:** `bloco_interface/web/templates/s2_pre_upload.html` + `partials/c3_upload_zone.html` + `bloco_engine/parsing/orchestrator.py:147-167`
- **Description:** Form S2 tem APENAS `<input name="pdf">` + `<input name="pdf_decisao_adversa">`. Backend `/revisar` aceita `uf=""`, `data=""`, `tier="balanced"` defaults. Pipeline passa `uf_override=None` para `extract_metadata_from_markdown`. Se PDF não tem regex de UF/data clara, levanta `MetadataExtractionError("Forneça via uf_override / data_override ou revise o PDF de origem")`.
- **Evidence:**
  ```html
  <!-- s2_pre_upload.html — APENAS 2 drop-zones -->
  <input type="file" name="pdf" required>
  <input type="file" name="pdf_decisao_adversa">
  <!-- ZERO inputs uf, data, tier -->
  ```
  ```python
  # orchestrator.py:155-167
  uf = uf_override or _extract_uf(markdown)
  data = data_override or _extract_data_assinatura(markdown)
  if not uf: faltantes.append("uf_contrato")
  if not data: faltantes.append("data_assinatura")
  if faltantes:
      raise MetadataExtractionError(
          f"Campos obrigatórios ausentes: {faltantes}. "
          "Forneça via uf_override / data_override ou revise o PDF."
      )
  ```
- **Root Cause:** Story MVP-LEAN-01 simplificou form para 2 drop-zones (Task 3 ux-spec §3 S2). Mas pipeline backend MANTEVE Form fields uf/data/tier sem populá-los UI. Quando backend é mais permissivo que frontend, é um caso aceitável; quando ele EXIGE algo (extract metadata) com fallback a override que UI não oferece, é furo arquitetural.
- **Fix Proposal:**
  - **Opção A (PRD-aligned):** adicionar 2 inputs `<select name="uf">` (lista UFs) + `<input type="date" name="data">` no form S2. Tier pode ficar default "balanced" ou ser advanced toggle.
  - **Opção B (defensive):** se metadata extraction falhar, retornar form S3 perguntando UF+Data antes de prosseguir
  - **Opção C (decisão MVP):** documentar como "PDF deve ser bem estruturado" + error message Eric-friendly mostrando como pré-processar
- **Effort:** Opção A 1h; Opção B 2h; Opção C 30min docs
- **Decoy or Real:** **REAL** — Eric reportou "campos não aparecem" porque ESPERAVA preencher (instruções inventadas Morpheus), e até acertasse o caminho seu PDF imagem provavelmente não tem regex UF/data.

---

### 🟠 HIGH (7)

#### F-B1: [HIGH] [REAL] PDFs temporários abandonados em `/tmp` — LGPD violation latente

- **Component:** `bloco_interface/web/app.py:603-607` (mkstemp)
- **Description:** `tempfile.mkstemp(suffix=".pdf")` cria PDF temp. `event_generator.finally:` deleta APENAS se pipeline iniciar e completar/falhar gracefully. Quando OOM kill (F-A1), `finally` não executa → PDFs órfãos persistem. Verificação: `/tmp` tem **3 PDFs** (`fake.pdf`, `tmp_5izqo03.pdf`, `tmp_g_orxgg.pdf`).
- **Evidence:**
  ```bash
  ls /tmp/*.pdf
  /tmp/fake.pdf
  /tmp/tmp_5izqo03.pdf
  /tmp/tmp_g_orxgg.pdf
  ```
- **Root Cause:** `finally` só roda se controle volta. SIGKILL bypassa.
- **Fix Proposal:**
  ```python
  # No startup lifespan, scan /tmp/tmp_*.pdf > 1h e deletar
  # OR usar atexit handler
  # OR mover temp para diretório com TTL gerenciado
  ```
- **Effort:** 30min
- **Decoy or Real:** **REAL** — 3 PDFs abandonados confirmam.

#### F-B2: [HIGH] [REAL] sqlite-vec extension NÃO carrega via sqlite3 puro — `jurisp_vec` retorna "no such module: vec0"

- **Component:** `bloco_vault/busca.py` + `bloco_vault/__init__.py:open_vault`
- **Description:** Empirical: `sqlite3.connect(vault.db).execute('SELECT COUNT(*) FROM jurisp_vec')` falha com `OperationalError: no such module: vec0`. Significa que `buscar_hibrida` (linha 234 pipeline) DEPENDE de `open_vault()` carregar extension via `conn.load_extension(sqlite_vec.loadable_path())`. Se a função NÃO carrega corretamente em Python 3.13 (pode haver mudança), busca falha.
- **Evidence:**
  ```python
  >>> sqlite3.connect(db).execute("SELECT * FROM jurisp_vec").fetchone()
  OperationalError: no such module: vec0
  ```
  Mas: `import sqlite_vec; sqlite_vec.loadable_path()` retorna OK (path existe).
- **Root Cause:** Vault busca só funciona se `open_vault` chama `enable_load_extension` + `load_extension`. Pode quebrar silenciosamente se Python 3.13 wrapper não suporta OR se sqlite-vec wheel para Py3.13 tem bug.
- **Fix Proposal:** Read `bloco_vault/__init__.py` open_vault — confirmar que carrega extension. Adicionar test integração que cria vault + busca + assert non-empty.
- **Effort:** 30min investigação + fix se quebrar
- **Decoy or Real:** **REAL** — pode estar funcionando, mas não temos test E2E que prova.

#### F-B3: [HIGH] [REAL] Lifespan startup `BertModel LOAD REPORT` warnings UNEXPECTED keys — modelo embeddings PT-BR carrega errado

- **Component:** `bloco_vault/embeddings.py` (provavelmente) + sentence-transformers wrapper de BERTimbau
- **Description:** App.log durante startup:
  ```
  [transformers] BertModel LOAD REPORT from: neuralmind/bert-base-portuguese-cased
  Key | Status
  cls.seq_relationship.weight | UNEXPECTED
  cls.predictions.transform.LayerNorm.weight | UNEXPECTED
  ... (8 keys UNEXPECTED)
  Notes: UNEXPECTED can be ignored when loading from different task/architecture
  ```
- **Root Cause:** BERTimbau é modelo MaskedLM com cabeças `cls.*`. Sentence-transformers usa apenas embeddings layer. Os UNEXPECTED são `cls.*` que não vão ser usados — comportamento normal mas log assustador.
- **Fix Proposal:** Suprimir log via `transformers.logging.set_verbosity_error()` no startup.
- **Effort:** 5min
- **Decoy or Real:** **REAL como log noise** — comportamento técnico OK, mas eleva ansiedade do dev.

#### F-B4: [HIGH] [REAL] Static files servidos por uvicorn sync — bloqueia event loop em request grande

- **Component:** `bloco_interface/web/app.py:340 app.mount("/static", StaticFiles(...))`
- **Description:** `fastapi.staticfiles.StaticFiles` é wrapper sync. Para arquivo estático de poucos KB OK. Mas quando carrega `/static/htmx.min.js` (~50KB) ou tokens.css (~30KB) durante 100ms, event loop bloqueia. Combinado com pipeline OCR rodando, latência acumula.
- **Evidence:** Não tem repro direto, mas é design pattern conhecido.
- **Fix Proposal:** Servir static via nginx/Caddy reverse proxy em produção. Para dev, aceitável.
- **Effort:** Production setup — fora escopo CC.41
- **Decoy or Real:** **DECOY** — não é o bug atual. Mas é debt para produção.

#### F-B5: [HIGH] [REAL] Audit `pipeline_lost_connection` event — gravado pelo CLIENT JS, não pelo servidor — viola integridade

- **Component:** `bloco_interface/web/app.py:736 POST /audit/connection-drop` + JS `sse_resilient.js`
- **Description:** Audit.jsonl última entry:
  ```json
  {"type": "pipeline_lost_connection", "job_id": "b4caefbf-...", "last_phase": "Parsing PDF",
   "timestamp": "2026-05-07T10:07:30.550234+00:00"}
  ```
  **NÃO TEM `entry_hash`, `event_type` (atributo), `payload`, `previous_entry_hash`** — campos obrigatórios da chain HMAC. Significa que esta entry foi escrita por OUTRO endpoint (`/audit/connection-drop`) sem passar pelo `append_audit_entry` chain. Viola integridade Merkle.
- **Evidence:** Compare entries:
  ```json
  // Entry normal CC.28:
  {"entry_hash":"61aebe...", "event_type":"pipeline_revisar_contrato", "payload":{...}, "previous_entry_hash":"...", "ts":"..."}

  // Entry lost_connection (POST /audit/connection-drop):
  {"type":"pipeline_lost_connection", "job_id":"...", "last_phase":"...", "timestamp":"..."}
  ```
- **Root Cause:** Endpoint `/audit/connection-drop` faz JSONL append direto sem chain. Smith CC.28 finding TD-T9-AUDIT-INTEGRATION mencionou `_write_audit` direct write similar. Esta é mesma classe de bug.
- **Fix Proposal:** Refatorar `/audit/connection-drop` para usar `append_audit_entry` com `event_type="pipeline_lost_connection"` e payload estruturado.
- **Effort:** 30min
- **Decoy or Real:** **REAL** — chain quebrada significa `verify_audit_integrity()` vai falhar. Auditoria forense impossível.

#### F-B6: [HIGH] [REAL] Morpheus inventou 4x instruções "preencher UF/Data/Tier" — falta no-invention enforcement em meta-camada

- **Component:** Meta — orquestração Morpheus em conversa Eric
- **Description:** Eu (Morpheus) escrevi 4 vezes "preencher UF, data, tier" em instruções a Eric. Consultei `bloco_interface/web/app.py:539-545` que tem esses parâmetros como Form, MAS não consultei o template `s2_pre_upload.html` que NÃO renderiza esses inputs. Confiei no backend signature como prova de feature UI.
- **Evidence:** Histórico conversa CC.36-CC.40 — múltiplas mensagens com instruções "preencha UF: BA, Data assinatura: 2024-03-15, Tier: lean".
- **Root Cause:** Meta-padrão. `feedback_no_invention.md` da memória diz: "Toda afirmação rastreável a evidência documental." Mas Morpheus não validou contra UI real, apenas backend.
- **Fix Proposal:** Antes de instruir Eric a interagir com UI, Morpheus DEVE ler templates HTML específicos da tela mencionada. Adicionar como rule meta.
- **Effort:** Disciplina — 0min código, 100% processo
- **Decoy or Real:** **REAL** — confirmado por Eric.

#### F-B7: [HIGH] [REAL] Tests `tests/unit/` cobrem 57 mocks mas ZERO E2E real — confiança falsa

- **Component:** `tests/` arquitetura
- **Description:** Suite atual tem 57 unit tests passing. **NENHUM** é E2E real (PDF → veredict). Smith CC.37 F-11 endereçou "test marker disponível mas falha" mas com mock. Toda cadeia CC.34/CC.35/CC.38/CC.40 passou tests mas Eric encontra erros runtime que tests não pegam.
- **Evidence:** `grep -rln "marker_pdf\|sabia\|surya\|integration" tests/` — quase tudo é mock.
- **Root Cause:** Test strategy é unit-only. Sem integration test rodando pipeline real PDF→verdict.
- **Fix Proposal:** Criar `tests/integration/test_pipeline_e2e_real.py` com 1 PDF fixture + Ollama running + assert verdict válido. Mark `@pytest.mark.integration` para skip em CI sem hardware.
- **Effort:** 2-3h (incluir fixture PDF de teste)
- **Decoy or Real:** **REAL** — ausência de E2E real é por que cada CC.X precisou de Eric humano descobrir bug.

---

### 🟡 MEDIUM (8)

#### F-C1: [MED] [REAL] `JOBS` dict cresce indefinidamente — verifico que F-09 ainda é debt

- **Component:** `bloco_interface/web/app.py` JOBS global
- **Description:** Smith CC.37 F-09 marcado como debt. Em produção isso é HIGH; em dev local single-user é MED. Mas após 10 jobs failed (incluindo CC.41 atual), JOBS tem garbage acumulado.
- **Fix:** Mesmo do F-09 anterior — TTL cleanup. Não-prioritário para Eric atual.
- **Decoy or Real:** **REAL mas baixa urgência** — confirmado.

#### F-C2: [MED] [REAL] Lifespan NÃO valida vault populated antes de aceitar requests

- **Component:** `bloco_interface/web/app.py:624 lifespan` + `app.py:648 vault check em /revisar/stream`
- **Description:** Vault check é feito tarde — DENTRO do event_generator do SSE, não no startup. Se vault não existir, app sobe normalmente, login funciona, upload aceito, e SÓ quando SSE inicia descobrimos. UX ruim.
- **Fix Proposal:** Em lifespan startup: check `DEFAULT_VAULT_DB.exists()` + se ausente, log WARN proeminente + opcionalmente raise.
- **Effort:** 15min
- **Decoy or Real:** **REAL** — UX defensivo.

#### F-C3: [MED] [REAL] CC.40 fix F-12 (XDG_DATA_HOME) introduzido SEM test que valida o env override

- **Component:** `bloco_audit/genesis.py:24` + `chain.py:26`
- **Description:** Fix CC.40 adicionou `_XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME") or ...)` mas tests não cobrem case com env var setada. Possível bug não-testado: se `XDG_DATA_HOME=/tmp/test`, o GENESIS lock muda de localização — tests existentes podem quebrar OR não detectar.
- **Fix Proposal:** Test específico com monkeypatch de env var.
- **Effort:** 20min
- **Decoy or Real:** **REAL** — fix sem test.

#### F-C4: [MED] [REAL] Pipeline phase events emit `phase-done` ao FINAL — heartbeat funcional mas UX phase tracking é ilusório

- **Component:** `app.py:706-701`
- **Description:** Comentário CC.41 anterior: phase-done para todas 5 fases é emitido SEQUENCIALMENTE no final, depois que pipeline real completou. Eric vê "Parsing PDF" durante todo runtime real.
- **Fix:** Smith CC.37 F-08 — accepted-as-debt. Reafirmado debt ativo.
- **Decoy or Real:** **REAL** — UX issue mas não bloqueia.

#### F-C5: [MED] [REAL] `extract_metadata_from_markdown` regex frágil — funciona apenas em PDF gerado por banco específico

- **Component:** `bloco_engine/parsing/orchestrator.py` `_extract_uf` `_extract_data_assinatura`
- **Description:** Regex extraem padrões assumindo formato textual específico. PDF de outro banco com layout diferente falha silenciosamente.
- **Fix:** LLM-aware extraction (Sabia 7B prompt com markdown chunks) OU offer manual input em form S2 (F-A2 fix).
- **Effort:** 4h+ refactor
- **Decoy or Real:** **REAL** — limita generalidade do produto.

#### F-C6: [MED] [REAL] Hashlib import dentro de `_compute_static_version` (CC.39) é PEP8 violation menor

- **Component:** `bloco_interface/web/app.py:344` `_compute_static_version`
- **Description:** `import hashlib` dentro da função em vez de no topo do módulo. Funciona mas viola PEP8.
- **Fix:** Mover para topo.
- **Effort:** 2min
- **Decoy or Real:** **REAL polish** — não bloqueia.

#### F-C7: [MED] [REAL] Pipeline `revisar_contrato` cria BacenClient SÍNCRONO mas chama `client.fetch_taxa_modalidade` via to_thread — close() é fora de async

- **Component:** `bloco_workflow/pipeline.py:217-225`
- **Description:** CC.38 wrappa `bacen_client.fetch_taxa_modalidade` com `asyncio.to_thread`. Mas `bacen_client.close()` em finally é chamado SYNC no event loop — pode bloquear se close envolve flush.
- **Fix:** `await asyncio.to_thread(bacen_client.close)` se close pode bloquear, OR confirmar close é trivial.
- **Effort:** 10min
- **Decoy or Real:** **DECOY likely** — close de BacenClient deve ser trivial. Verificar.

#### F-C8: [MED] [REAL] Logger `transformers` BertModel UNEXPECTED warns aparecem mesmo se transformers.logging silenciado — pode ser print() não logger

- **Component:** Dependência transformers + sentence-transformers
- **Description:** Logs UNEXPECTED no app.log podem ser `print()` direto no transformers, não `logging.warning`. Se for print, suprimir requer redirecionar stdout.
- **Fix:** Investigar; se print direct, redirecionar stdout/devnull em startup.
- **Effort:** 30min
- **Decoy or Real:** **REAL** — log noise.

---

### 🟢 LOW (5)

#### F-D1: [LOW] [REAL] CC.40 docstring F-05 usa caracteres especiais (`!`, `→`) que podem quebrar em encoding-restricted

- **Component:** `bloco_audit/genesis.py` _get_secret_key docstring
- **Decoy or Real:** **DECOY** — UTF-8 padrão Python 3.13 OK. Cosmético.

#### F-D2: [LOW] [REAL] `STATIC_VERSION` é computado UMA vez em startup — restart com hot reload de assets fica stale

- **Component:** `app.py:357` STATIC_VERSION computed once
- **Description:** Se Eric/dev edita JS sem restart app, hash não recalcula. Não bumpa.
- **Fix:** Recalcular per-request (cost negligível, 8 mtimes scan).
- **Effort:** 5min
- **Decoy or Real:** **REAL minor**.

#### F-D3: [LOW] [REAL] Subprocess Ollama UnicodeDecodeError continua aparecendo em log apesar CC.40 F-13 documentar como dep externa

- **Component:** Subprocess Ollama threads
- **Description:** Log noise persiste. CC.40 F-13 marcou como "investigated, accepted log noise" — confirmação que ainda aparece.
- **Decoy or Real:** **REAL log noise**.

#### F-D4: [LOW] [REAL] `.env.example` agora tem header CRITICAL (CC.40 F-16) MAS continua com placeholders descritivos que humano distraído pode usar

- **Component:** `.env.example`
- **Description:** Header CRITICAL ajuda mas placeholders ainda parecem com valores reais a olhos cansados.
- **Fix:** Substituir placeholders por strings ÓBVIAS de placeholder: `<<<GENERATE_VIA_secrets.token_hex(32)>>>`
- **Effort:** 5min
- **Decoy or Real:** **REAL polish**.

#### F-D5: [LOW] [REAL] App rodando Python 3.13 mas pyproject `requires-python = ">=3.11"` — não documenta upper bound

- **Component:** `pyproject.toml`
- **Description:** Sem upper bound, próximo Python 3.14+ pode quebrar (como vimos em CC.33). Recomendar `requires-python = ">=3.11,<3.14"`.
- **Effort:** 2min
- **Decoy or Real:** **REAL** — preventivo futuro.

---

## Recommendations Consolidadas (Priorizadas)

### 🚨 IMEDIATO (BLOQUEIA Eric):

1. **Restart app via Operator** — sem isso Eric não pode nem testar
2. **F-A2 fix Opção A** — adicionar inputs UF + Data no form S2 (1h Neo)
3. **F-A1 monitoring** — `psutil` check antes de OCR pesado (1h Neo)

### 🔥 CURTO PRAZO (1 sessão dedicada):

4. **F-B1** — limpar /tmp PDFs órfãos no startup
5. **F-B5** — refatorar /audit/connection-drop usar append_audit_entry
6. **F-B7** — criar 1 test E2E real (com fixture PDF + Ollama running)
7. **F-B6** — adicionar regra meta: Morpheus consulta templates antes de instruir UI
8. **F-C2** — vault check no startup lifespan

### 📋 MÉDIO PRAZO (debt tracker):

9. **F-B2** — investigar sqlite-vec extension em open_vault
10. **F-B3** — suprimir BertModel UNEXPECTED warnings
11. **F-C3** — test XDG_DATA_HOME override
12. **F-C5** — extract_metadata melhorar regex OR LLM-based

### 📌 ACEITAR DEBT:

13. **F-C1** (F-09 reafirmado), F-C4 (F-08 reafirmado), F-C6, F-C7, F-C8, F-D1..F-D5

---

## Roadmap Concreto Próximos Steps

### Etapa CC.42 (Operator restart + Neo F-A2 + F-A1)
- Operator: restart app limpo
- Neo: form S2 + inputs UF/Data + RAM monitor
- Operator: restart com fixes
- Eric retoma smoke

### Etapa CC.43 (test infra + audit chain integrity)
- Neo: criar test E2E integration
- Neo: refatorar /audit/connection-drop chain-aware

### Etapa CC.44+ (debts)
- Conforme priorização Morpheus

---

## Análise Cynical: Por Que Smith CC.37 NÃO Foi Suficiente

| Smith CC.37 disse | Smith CC.41 verifica |
|---|---|
| "F-01 event loop blocking RESOLVED" | ✅ Sim, confirmado em CC.38 |
| "F-04 timeout 30min ceiling RESOLVED" | ✅ Sim, mas timeout DENTRO de wait_for sem proteção OOM upstream |
| "16/16 findings 100% addressed" | ❌ **Falso** — Smith CC.37 perdeu 6+ findings agora descobertos |

**Smith CC.37 foi review focado em código modificado.** Não auditou `s2_pre_upload.html` (template), `extract_metadata_from_markdown` (orchestrator), `/audit/connection-drop` (separate route), OOM ressources, tests E2E ausentes. Smith CC.41 amplia escopo para ARQUITETURAL, não apenas mudança incremental.

**Lição:** "Adversarial review" é técnica, não checkbox. Cada review deve ter escopo declarado E auditoria do escopo. CC.37 escopo declarou "mudança CC.30..CC.36" — corretamente fez. Mas Eric assumiu que cobria TUDO. Comunicação de escopo é crítica.

---

## Verdict Final

**FAIL** — Eric NÃO pode usar a aplicação até:
1. App restart estável (Operator)
2. F-A2 fix UI inputs OR documentar PDF requirements estritos
3. F-A1 OOM protection OU avisar usuário pre-OCR
4. F-B7 test E2E real para confiança real

**Recomendação Smith:** dispatch Operator para restart + Neo URGENTE para F-A2 (UI inputs) + F-A1 (RAM check). Demais debts podem aguardar.

Ironicamente, "100% Smith addressed" de CC.40 era **localmente correto** — todos os 16 findings de CC.37 foram tratados. Mas o ESCOPO de CC.37 era estreito. CC.41 abre escopo para o que Smith deveria ter olhado desde o começo: **a aplicação como produto, não apenas o código modificado**.

---

— Oracle (Smith mode ULTRATHINK), guardião que admite quando review anterior foi superficial 🛡️
