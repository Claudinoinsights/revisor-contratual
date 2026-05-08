---
type: qa-report
title: "Smith Adversarial Review — Aplicação Completa pós-CC.30..CC.36 (CC.37)"
project: revisor-contratual
sprint: "03"
session: 91
etapa: "CC.37 Smith adversarial review"
reviewer: "@qa · Oracle (Smith mode CYNICAL)"
date: "2026-05-07T08:15"
scope:
  - "11 arquivos modificados acumulados CC.30..CC.36"
  - "audit.jsonl runtime evidence"
  - "app.log runtime evidence"
  - "bloco_workflow/pipeline.py (revisar_contrato — não tocado mas crítico)"
findings_total: 16
severities:
  CRITICAL: 1
  HIGH: 5
  MEDIUM: 6
  LOW: 4
verdict: "**FAIL** — bug arquitetural CRITICAL (event loop blocking) torna inúteis TODOS os fixes CC.35 (heartbeat) + CC.36 (cache busting) + CC.30..CC.34 anteriores. 7 fix-cycles atacaram sintomas; causa raiz nunca foi tocada."
tags:
  - project/revisor-contratual
  - smith-adversarial-review
  - cc37
  - fail
---

# Smith Adversarial Review — Aplicação pós-CC.30..CC.36

> Smith mode CYNICAL ativado. Eric reportou MESMO erro 4x consecutivas apesar de 7 fix-cycles. Isso é diagnóstico: a aplicação está mentindo, e cada camada de fix adicionou outra camada de mentira. Esta review desnuda.

## Sumário Executivo

**Verdict:** **FAIL** ❌

**Findings:** 16 (1 CRITICAL · 5 HIGH · 6 MED · 4 LOW)

**Conclusão central:** O bug que Eric vem reportando NÃO É um bug específico — é o efeito visível de uma **incompatibilidade arquitetural fundamental: operações CPU/IO-bound síncronas dentro de `async revisar_contrato`** que bloqueiam o event loop do FastAPI. CC.35 (heartbeat) implementou corretamente o LOOP de heartbeat, **mas o loop nunca executa porque o event loop está bloqueado por `parse_contract(...)` síncrono que demora minutos**.

**Os 7 fix-cycles anteriores (CC.30..CC.36) não tocaram este bug.** Atacaram:
- Configuração (CC.30)
- Path mismatch (CC.31)
- Runtime version (CC.33)
- API library (CC.34/CC.35)
- Cache HTTP (CC.36)

Nenhum desses fixes faz heartbeat funcionar enquanto event loop está bloqueado por parsing síncrono.

---

## Findings

### 🔴 CRITICAL (1)

#### F-01: [CRITICAL] Event loop blocking — `revisar_contrato` chama síncronos dentro de async

- **Component:** `bloco_workflow/pipeline.py:191-280` + `bloco_interface/web/app.py:660-697`
- **Description:** `revisar_contrato` é declarado `async def` (linha 142) mas chama operações **síncronas que bloqueiam o event loop por minutos**. CC.35 implementou heartbeat via `asyncio.create_task` + `wait_for(shield(task), timeout=10)` loop **mas o loop nunca executa** porque o event loop está bloqueado.
- **Evidence:**
  ```python
  # bloco_workflow/pipeline.py:191 — SYNC dentro de async
  parsed: ParsedContract = parse_contract(pdf_path, ...)  # SEM await
  # parse_contract → parse_pdf_marker → _default_marker_parser → PdfConverter()(path)
  # PdfConverter é CPU-bound, leva minutos para PDF imagem 12 páginas

  # Linha 207: também síncrono
  calculo: ResultadoCalculo = _calcular_pipeline(parsed.metadata)

  # Linha 219: network IO síncrono (bloqueia event loop em network call)
  bacen_data = bacen_client.fetch_taxa_modalidade(...)

  # Linha 234: sqlite + embeddings síncrono
  busca_result = buscar_hibrida(vault_conn, query, ...)

  # Linha 275: síncrono
  veredito = juiz_revisar(...)
  ```
  Apenas linha 258 (`run_personas_paralelas`) tem `await`. Tudo o resto bloqueia.
- **Root Cause:** Pipeline foi escrito assumindo execução em script CLI síncrono (`revisar` CLI). Quando portado para FastAPI async (UI Web), foi marcado `async def` por convenção mas internamente nunca foi adaptado. CC.35 heartbeat assume cooperação do event loop — não há.
- **Fix Proposal:**
  ```python
  # OPÇÃO A (mínima): envolver parse_contract em to_thread
  parsed = await asyncio.to_thread(
      parse_contract,
      pdf_path,
      pdf_bytes=pdf_bytes,
      uf_override=uf_override,
      data_override=data_override,
      pymupdf_fn=pymupdf_fn,
      marker_fn=marker_fn,
  )

  # Repetir para _calcular_pipeline, bacen_client.fetch, buscar_hibrida, juiz_revisar.
  # Steps async (run_personas_paralelas) já estão OK.

  # OPÇÃO B (idiomática): expor revisar_contrato como sync,
  # e wrappar inteiro com asyncio.to_thread no event_generator do app.py
  veredito = await asyncio.to_thread(
      revisar_contrato_sync,  # versão sync do pipeline
      pdf_path, ...
  )
  ```
  **Opção B é mais segura** — preserva semântica original do pipeline (foi escrito sync) + delega async para a borda HTTP.
- **Effort:** 1-2h (Opção A: ~5 mudanças `to_thread`; Opção B: criar wrapper sync + chamar `to_thread` 1x)

---

### 🟠 HIGH (5)

#### F-02: [HIGH] CC.35 heartbeat loop tem `await asyncio.wait_for(asyncio.shield(task), timeout=10)` — semântica é CORRETA mas CONDICIONALMENTE inútil

- **Component:** `bloco_interface/web/app.py:687-694`
- **Description:** A construção `asyncio.wait_for(asyncio.shield(task), timeout=10)` é semanticamente correta para heartbeat (timeout faz wait_for cancelar o aguardo, mas shield previne propagação ao task). PORÉM, **só funciona se o event loop conseguir AGENDAR o callback de timeout**. Como F-01 mostra, event loop está bloqueado durante steps síncronos → wait_for nunca completa nem timeouta dentro de 10s. Pode timeoutar muito mais tarde (depois de step síncrono terminar) ou nunca.
- **Evidence:**
  ```python
  while not pipeline_task.done():
      try:
          await asyncio.wait_for(asyncio.shield(pipeline_task), timeout=10)
      except asyncio.TimeoutError:
          yield ping
  ```
  Em isolation parece correto. Em context com event loop bloqueado: inútil.
- **Root Cause:** CC.35 fix endereçou ARQUITETURA DE SINALIZAÇÃO mas não a CAUSA do bloqueio. Bonito, mas não funcional contra F-01.
- **Fix Proposal:** Auto-resolvido se F-01 for corrigido (event loop livre → wait_for timeout 10s funciona normalmente).
- **Effort:** 0 (depende de F-01)

#### F-03: [HIGH] `revisar_contrato` chama `append_audit_entry` em path FAILED — pode levantar exceção e perder o erro original

- **Component:** `bloco_workflow/pipeline.py:291-300`
- **Description:** No `except Exception as exc:` o código tenta gravar audit FAILED com `append_audit_entry(...)`. Se `append_audit_entry` em si falhar (HMAC error, IO error, audit chain corrupted) — **a exceção original é PERDIDA** e Eric vê só o erro secundário. Audit é exatamente onde você quer redundância máxima.
- **Evidence:**
  ```python
  except Exception as exc:
      audit_payload["status"] = "FAILED"
      ...
      append_audit_entry(...)  # se isso falhar, exc original some
      raise
  ```
- **Fix Proposal:**
  ```python
  except Exception as exc:
      audit_payload["status"] = "FAILED"
      audit_payload["error_type"] = type(exc).__name__
      audit_payload["error_msg"] = str(exc)[:500]
      try:
          append_audit_entry(...)
      except Exception as audit_exc:
          logger.error("audit FAILED entry write failed: %s (original: %s)", audit_exc, exc)
      raise exc from None
  ```
- **Effort:** 15min

#### F-04: [HIGH] CC.34/CC.35 `_default_marker_parser` não tem timeout — pode rodar indefinidamente

- **Component:** `bloco_engine/parsing/marker_parser.py:33-58`
- **Description:** `PdfConverter(artifact_dict=models)(str(pdf_path))` (linha 47) **não tem timeout configurado**. Se Surya OCR travar em "Recognizing Text 0/281" (sintoma exato Eric reportou), pipeline trava INFINITAMENTE. Audit nunca grava SUCCESS nem FAILED. UI mostra "lost connection" eternamente.
- **Evidence:** app.log mostra `Recognizing Text: 0/281 [00:00<?, ?it/s]` sem progresso há tempo. Pipeline não tem watchdog.
- **Fix Proposal:**
  ```python
  # Wrap com timeout via asyncio.to_thread + wait_for
  veredito = await asyncio.wait_for(
      asyncio.to_thread(revisar_contrato_sync, ...),
      timeout=1800,  # 30min hard ceiling
  )
  ```
  Plus: em `_default_marker_parser`, monitorar progresso via callback (marker 1.x suporta?) e abortar se nenhum progresso > 5min.
- **Effort:** 1h

#### F-05: [HIGH] Audit chain HMAC depende de bytes encoding ambíguo (descoberto CC.30 mas não documentado)

- **Component:** `bloco_audit/genesis.py:85-94` `_get_secret_key`
- **Description:** CC.30 descobriu que `AUTH_COOKIE_KEY` no `.env` é um **string hex** (64 chars), e `_get_secret_key` faz `key.encode("utf-8")` (não `bytes.fromhex(key)`). Resultado: HMAC usa 64 bytes ASCII em vez dos 32 bytes binários reais. Funciona porque é determinístico, mas **viola convenção criptográfica** (chave hex deveria ser decoded).
- **Evidence:**
  ```python
  return key.encode("utf-8")  # 64 bytes ASCII '3', '1', 'f'...
  # Convenção esperada: bytes.fromhex(key)  # 32 bytes binários
  ```
- **Root Cause:** Convenção implícita inconsistente; documentação ADR-005 não especifica encoding.
- **Fix Proposal:** OU (a) deixar como está + documentar explicitamente; OU (b) migrar para `bytes.fromhex` com migration script para audit chains existentes (DESTRUTIVO).
- **Effort:** 30min docs / 4h se migrar

#### F-06: [HIGH] CC.36 cache busting `?v=cc36` é manual — desenvolvedor vai esquecer de bumpar em release futura

- **Component:** `bloco_interface/web/templates/{base.html, s5_processing.html, s2_pre_upload.html}`
- **Description:** `?v=cc36` é hardcoded. Próxima mudança de JS sem bumpar para `?v=cc37` reintroduz o bug. Cache busting deveria ser automático (timestamp do arquivo OR git SHA OR build hash).
- **Evidence:** Comentário em `base.html:8` diz "bump versão a cada release" — depende de disciplina humana.
- **Fix Proposal:**
  ```python
  # bloco_interface/web/app.py — adicionar context processor
  import os, hashlib
  STATIC_VERSION = hashlib.sha256(
      str(os.path.getmtime("bloco_interface/web/static")).encode()
  ).hexdigest()[:8]

  # OR via Jinja env
  env.globals["static_version"] = STATIC_VERSION

  # Templates: <script src="/static/sse_resilient.js?v={{ static_version }}">
  ```
- **Effort:** 30min

---

### 🟡 MEDIUM (6)

#### F-07: [MED] Heartbeat ping em `app.py:669` envia 1x ANTES do task começar — desnecessário e confuso

- **Component:** `bloco_interface/web/app.py:669`
- **Description:** Linha 669 emite `event: ping` ANTES do `asyncio.create_task` (linha 676). Isso é redundante porque o loop heartbeat já cobre desde o primeiro timeout. Confuso para debug — duplicação de ping inicial.
- **Fix Proposal:** Remover linha 669; loop CC.35 (linha 687) já cobre heartbeat desde início.
- **Effort:** 2min

#### F-08: [MED] Pipeline não tem fase intermediária visível — UI fica em "phase-start parsing" o tempo todo

- **Component:** `bloco_interface/web/app.py:706-701` (loop emit phase-done para todas fases SEQUENCIAL após pipeline real terminar)
- **Description:** Servidor só emite `phase-done` para todas as 5 fases NO FINAL (sequencial linha 706-701), depois que pipeline real completou. Durante 10-30min de execução, UI mostra apenas "Parsing PDF" como phase ativa. Estado real (Cálculo, BACEN, Vault, Personas, Juiz) é desconhecido pelo UI durante runtime.
- **Evidence:**
  ```python
  veredito = await pipeline_task  # bloqueia até FIM
  # depois disso, loop emit phase-done para fases 1-4 sequencialmente
  ```
- **Fix Proposal:** `revisar_contrato` deveria aceitar callback `on_phase_complete(phase_name)` que UI streamea em tempo real. OU pipeline emite eventos via fila/queue compartilhada com `event_generator`.
- **Effort:** 2-4h (refactor incremental)

#### F-09: [MED] `JOBS` global dict — não thread-safe + memory leak

- **Component:** `bloco_interface/web/app.py` (variável `JOBS`)
- **Description:** `JOBS[job_id]` é dict global mutável. Sem lock para concurrent access. Sem cleanup — entries acumulam até memory full. Se 100 jobs/dia × 30 dias = 3000 entries × veredito ~50KB cada = ~150MB de RAM permanente.
- **Fix Proposal:**
  - `threading.Lock()` para writes OU `asyncio.Lock`
  - TTL cleanup (background task remove entries > 1h)
  - OR usar Redis/sqlite para job state
- **Effort:** 1-2h

#### F-10: [MED] `marker_parser.py:48-55` pages_count fallback chain pode dar 1 silenciosamente em caso de schema futuro

- **Component:** `bloco_engine/parsing/marker_parser.py:48-55`
- **Description:** Fallback chain `len(list) → dict.get("page_count") → metadata.get("pages") → 1` cobre 3 schemas mas se marker 2.x mudar de novo, retorna `1` silenciosamente. **Não levanta warning/log.**
- **Fix Proposal:**
  ```python
  if pages_count == 1 and not page_stats:
      logger.warning(
          "marker metadata sem 'page_stats' nem 'pages' — schema desconhecido. "
          "Returning pages_count=1 fallback. Metadata keys: %s",
          list(rendered.metadata.keys()),
      )
  ```
- **Effort:** 5min

#### F-11: [MED] Tests adaptados CC.34 não cobrem path "marker disponível mas falha"

- **Component:** `tests/unit/test_parsing.py:269-298`
- **Description:** 3 tests CC.34 mockam `_is_marker_available=False`. Não há test para path inverso: marker instalado + `_default_marker_parser` levanta exception (TimeoutError, ValueError, RuntimeError). Esse path é EXATAMENTE o que Eric está vivendo agora.
- **Fix Proposal:** Adicionar test:
  ```python
  def test_marker_disponivel_mas_falha_propaga_excecao(self, pdf_path, monkeypatch):
      def mock_marker_fail(*args, **kwargs):
          raise RuntimeError("Surya OCR timeout")
      monkeypatch.setattr(
          "bloco_engine.parsing.marker_parser._default_marker_parser",
          mock_marker_fail,
      )
      with pytest.raises(RuntimeError):
          parse_contract(pdf_path, pymupdf_fn=_fake_parser(MARKDOWN_VAZIO), marker_fn=None)
  ```
- **Effort:** 30min

#### F-12: [MED] CC.31 fix `bloco_audit/{genesis,chain}.py` paths agora dependem de `Path.home()` — não funciona em containers/serverless onde `$HOME` é diferente

- **Component:** `bloco_audit/genesis.py:23-24` + `bloco_audit/chain.py:23-25`
- **Description:** `Path.home() / ".local" / "share" / "revisor-contratual"` assume convenção XDG-like em ambiente desktop. Em containers Docker (`HOME=/`), CI sandboxes (`HOME=/root`), ou serverless (sem HOME) o caminho fica errado/inacessível.
- **Fix Proposal:** Respeitar `XDG_DATA_HOME` env var se setado:
  ```python
  XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
  DEFAULT_AUDIT_DIR = XDG_DATA_HOME / "revisor-contratual"
  ```
- **Effort:** 15min

---

### 🟢 LOW (4)

#### F-13: [LOW] UnicodeDecodeError em subprocess Ollama threads — log noise, não bloqueante

- **Component:** Ollama Manager `subprocess._readerthread`
- **Description:** `app.log` mostra `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc6` em threads de leitura de subprocess Ollama. Confirma cosmético (subprocess output em encoding errado) — não afeta funcionalidade. Mas polui logs.
- **Fix Proposal:** Quando spawn ollama, passar `encoding="utf-8", errors="replace"` para subprocess.Popen.
- **Effort:** 10min

#### F-14: [LOW] `.env` mistura segredos com config not-secret (REVISOR_HTTPS_ONLY=0)

- **Component:** `.env`
- **Description:** Mistura `AUTH_COOKIE_KEY` (segredo crítico) com `REVISOR_HTTPS_ONLY=0` (config trivial). Boas práticas separam: `.env` (segredos) + `config.toml` (config não-secret).
- **Fix Proposal:** Mover REVISOR_HTTPS_ONLY + ENABLE_TEMA_1378_AUTO_CHECK para `pyproject.toml [tool.revisor]` ou separar config.
- **Effort:** 30min (refactor)

#### F-15: [LOW] CC.36 `?v=cc36` aplicado SOMENTE a 6 assets — não cobre fonts em /static/fonts/

- **Component:** Templates não cobertos
- **Description:** CSS importa fonts em `/static/fonts/` via `@font-face`. Browser pode cachear fonts. Se atualizar font, tem mesmo problema.
- **Fix Proposal:** Adicionar `?v=cc36` em URLs de fontes dentro de `tokens.css` OU servidor headers Cache-Control para fonts.
- **Effort:** 10min

#### F-16: [LOW] CC.30 `.env.example` template não usa `secrets.token_hex(32)` para defaults — desenvolvedor pode achar que é OK rodar com placeholders

- **Component:** `.env.example`
- **Description:** Placeholders são strings descritivas (`<32-bytes-hex-gerados...>`). Desenvolvedor distraído pode literalmente usar a string como valor.
- **Fix Proposal:** Adicionar header `# CRITICAL: NUNCA usar placeholders como valores reais. Gerar via comandos abaixo de cada var.`
- **Effort:** 5min

---

## Recommendations Consolidadas (Priorizadas)

### 🚨 Imediato (BLOQUEIA Eric continuar smoke):

1. **F-01 fix** — `await asyncio.to_thread(parse_contract, ...)` em `pipeline.py:191` (Opção A) OR wrappear `revisar_contrato` inteiro com `to_thread` no `app.py:676` (Opção B). **Sem isso, heartbeat CC.35 nunca vai funcionar.**
2. **F-04 fix** — adicionar timeout 30min hard ceiling no `await asyncio.wait_for(...)` que envolve o pipeline.
3. **Restart app** — após fixes acima.

### 🔥 Curto prazo (1 sessão):

4. **F-03** — proteger `append_audit_entry` em except block.
5. **F-06** — cache busting automático via mtime hash.
6. **F-08** — phase-done streaming durante runtime real (UI feedback).

### 📋 Médio prazo (registrar como debt):

7. **F-09** — JOBS dict thread-safety + cleanup TTL.
8. **F-11** — test "marker falha" path.
9. **F-12** — XDG_DATA_HOME respect.

### 📌 Aceitar como debt:

10. **F-02** (auto-resolvido por F-01)
11. **F-05** (encoding doc only)
12. **F-07** (cosmético)
13. **F-10** (warning fallback)
14. **F-13, F-14, F-15, F-16** (LOW polish)

---

## Análise Cynical: Por Que 7 Fix-Cycles Não Resolveram

| CC | Fix | Atacou Causa Raiz? |
|---|---|---|
| CC.30 | .env + AUTH | Não — config secundária |
| CC.31 | bloco_audit path | Não — path é relevante mas não bug atual |
| CC.33 | Python 3.13 | Não — Python version era pré-condição não causa |
| CC.34 | marker API | Não — API estava errada mas isso é sintoma de bug não validado pré-instalação |
| CC.35 | pages_count + SSE heartbeat | **PARCIALMENTE** — fix arquitetural correto MAS inútil pelo F-01 |
| CC.36 | Cache busting | Não — sintoma cache, fix não chega ao backend |

**A causa raiz F-01 (event loop blocking) está no `bloco_workflow/pipeline.py`, que NÃO foi tocado em nenhuma das 7 CCs.** Cada CC pegou um sintoma adjacente e corrigiu, mas o pipeline real continuou bloqueando event loop.

**Por que escapou às reviews:** Smith reviews CC.25/CC.26/CC.29 focaram em `bloco_dataset` (Tema 1378) + story file. `pipeline.py` revisar_contrato signatures não foram revisadas no contexto FastAPI async UI.

**Lesson:** Um pipeline pode ser corretamente síncrono em CLI script mas profundamente errado em FastAPI async route. **Marca `async def` ≠ código async.** Verificar cada chamada interna por `to_thread` discipline.

---

## Verdict Final

**FAIL** — Aplicação não pode ser usada para PDFs imagem até F-01 ser corrigido. Todos os fixes anteriores foram corretos no que tentaram resolver, mas atacaram sintomas. **F-01 é o fix mínimo viável para desbloquear Eric.**

Recomendação: **dispatch Neo via Skill imediatamente para F-01 fix (1-2h)** + F-04 timeout (incluído mesmo escopo).

---

— Oracle (Smith mode), guardião que reconhece quando 7 fixes não bastam 🛡️
