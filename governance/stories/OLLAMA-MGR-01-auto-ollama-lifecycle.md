---
type: story
id: OLLAMA-MGR-01
title: "Auto-Ollama Lifecycle Management Implementation — subprocess + detect-then-spawn + 12 edge cases"
status: Ready
priority: alta
sprint: "03"
epic: "Sprint-03-Phase-0"
owner: "@dev (Neo)"
estimated_effort: "8-10h"
created: "2026-05-05"
created_by: "@sm (River)"
predecessor_handoff: ".lmas/handoffs/handoff-architect-to-sm-2026-05-05-sprint-03-stories.yaml"
predecessor_adr: "governance/architecture/adr/adr-011-auto-ollama-lifecycle.md (Accepted Eric)"
predecessor_stories:
  - "REV-LLM-01 (Done — commit 20d4459 + 8eea89c)"
  - "DOCS-02 (Done — commit 8b37513 + 98e5541)"
  - "UI-1 (Done — commit 110986e + 3ec01f6)"
parallel_story: "VAULT-FIX-01 (paralela, code paths independentes)"
resolves:
  - "Eric solicitação 'O ollama precisa ser gerenciado pela aplicação' (sessão 86)"
  - "Manual Ollama setup (Ollama desktop + 2ª instância manual + ollama pull manual)"
  - "EC-01..EC-12 edge cases mapeados em ADR-011"
  - "AC-9 smoke E2E real bloqueado em UI-1 (Ollama lifecycle dependency)"
unblocks:
  - "v0.3.0 release (gate condition Ollama auto-managed)"
  - "AC-9 retroativo UI-1 (smoke E2E real ponta a ponta)"
  - "UX target '1 comando + funciona' (`python -m bloco_interface.web.app`)"
  - "Smith adversarial review (após VAULT-FIX-01 + OLLAMA-MGR-01 done)"
tags:
  - project/revisor-contratual
  - story
  - sprint-03
  - ollama-mgr-01
  - lifecycle
  - infrastructure
---

# Story OLLAMA-MGR-01 — Auto-Ollama Lifecycle Management Implementation

## Story

**Como** operador rodando o Revisor Contratual local pela primeira vez,
**Eu quero** que a aplicação **auto-gerencie** o Ollama (start/stop/health/auto-pull modelos faltantes) com `python -m bloco_interface.web.app` como **único comando**,
**Para que** eu não precise instalar Ollama desktop separado, subir 2ª instância manualmente, OR rodar `ollama pull` para baixar modelos — a app cuida de tudo, preserva Ollama desktop existente se já rodando, e me mostra progresso de download dos modelos via UI.

---

## Contexto

ADR-011 (Accepted Eric, sessão 86) estabelece **Auto-Ollama Lifecycle Management** — Option A subprocess Python + detect-then-spawn algorithm com 12 edge cases mapeados. Esta story implementa ADR-011.

**Friction identificada em sessão 86 v0.2.0 testing:**

Eric testou app v0.2.0 e disse explicitamente:
> "O ollama precisa ser gerenciado pela aplicação"

Atualmente requer setup manual elaborado:
1. Eric DEVE ter Ollama desktop instalado E rodando em :11434
2. Eric DEVE subir manualmente 2ª instância em :11435 (`OLLAMA_HOST=127.0.0.1:11435 ollama serve`)
3. Eric DEVE ter pulled qwen2.5:7b (4.7GB) + qwen2.5:3b (1.9GB) manualmente

UX target pós-OLLAMA-MGR-01:

```bash
python -m bloco_interface.web.app
# → app detecta Ollama, spawna instâncias missing, pulla modelos faltantes, ready em ~30s
```

**Reference completa:** ver ADR-011 sections "Decisão" + "Implementation Strategy" + "12 Edge Cases Mapeados" para spec detalhado (algoritmos cross-platform binary detection, atomic PID write, lockfile, detect-then-spawn, on-demand health check, SSE progress, todos os 12 edge cases com mitigations).

---

## Acceptance Criteria

### Funcionalidade — Module + Detection (5/5 MUST)

- [ ] **AC-1:** `bloco_interface/ollama_manager.py` module criado com 11 funções core (per ADR-011 spec):
  - `detect_ollama_binary() -> Optional[Path]`
  - `detect_running_ollama(host, port) -> bool`
  - `spawn_ollama(binary, host, port, log_file) -> int (PID)`
  - `kill_spawned_ollama() -> None`
  - `ensure_models_pulled(required: list[str]) -> None` (background-friendly)
  - `get_pull_status() -> dict` (state/model/percent/eta)
  - `is_ready() -> bool`
  - `write_pid_file_atomic(pids: dict[str, int]) -> None`
  - `read_pid_file_safely() -> dict[str, int]`
  - `acquire_app_lock() -> int (fd)`
  - `cleanup_orphans_on_startup() -> None`
  - Verificável: `python -c "from bloco_interface.ollama_manager import detect_ollama_binary, detect_running_ollama, spawn_ollama, kill_spawned_ollama, ensure_models_pulled, get_pull_status, is_ready, write_pid_file_atomic, read_pid_file_safely, acquire_app_lock, cleanup_orphans_on_startup; print('OK 11 funcs')"` retorna OK
- [ ] **AC-2:** Cross-platform binary detection com priority chain (per ADR-011):
  - Priority 1: env var `OLLAMA_BINARY_PATH` override
  - Priority 2: platform default (Windows `%LOCALAPPDATA%\Programs\Ollama\ollama.exe`, Linux `/usr/local/bin/ollama` OR `/usr/bin/ollama`, Mac `/opt/homebrew/bin/ollama` OR `/usr/local/bin/ollama`)
  - Priority 3: `shutil.which("ollama")` PATH search
  - Priority 4: return None (caller raises clear error com download URL)
  - Verificável: tests/unit cobre 4 cenários priority chain
- [ ] **AC-3:** Atomic PID file write (temp + os.replace POSIX atomic) + lockfile fcntl/msvcrt non-blocking:
  - PID file: `~/.local/share/revisor-contratual/.ollama-spawned.pid` (JSON with schema_version 1.0)
  - Lockfile: `~/.local/share/revisor-contratual/.app.lock` (fcntl em Linux/Mac, msvcrt em Windows)
  - `acquire_app_lock()` raises `AppAlreadyRunning` se outro app instance acquired lock
  - Verificável: tests/unit (mock fcntl/msvcrt + verify atomic write)
- [ ] **AC-4:** Detect-then-spawn algorithm preserva Ollama existente:
  - Se `:11434` UP (Ollama desktop OR previous instance) → REUSE (não spawnar, não kill)
  - Se `:11434` DOWN → spawn nova instância
  - Mesma lógica para `:11435`
  - Verificável: integration test mock `detect_running_ollama` retornando True/False
- [ ] **AC-5:** FastAPI lifespan integration completa:
  - Startup: `acquire_app_lock` + `cleanup_orphans_on_startup` + `detect_ollama_binary` + spawn missing + `write_pid_file_atomic` + `asyncio.create_task(ensure_models_pulled([qwen2.5:7b, qwen2.5:3b]))`
  - Shutdown: `kill_spawned_ollama` (apenas PIDs em PID file via `process_is_ours` verification) + cleanup PID file + release lock
  - Verificável: integration test FastAPI lifespan startup/shutdown

### Funcionalidade — Auto-pull + Health (3/3 MUST)

- [ ] **AC-6:** Auto-pull background task + SSE progress streaming:
  - `asyncio.create_task(ensure_models_pulled(...))` no lifespan startup (não bloqueia startup)
  - Endpoint `/ollama-status` SSE stream: `{"state": "pulling"|"ready"|"error", "model": "...", "percent": 0-100, "eta_seconds": ...}`
  - UI banner em `index.html` com `hx-ext="sse" sse-connect="/ollama-status"` mostra progress
  - Verificável: smoke manual — primeira startup → log "Pulling qwen2.5:7b..." + UI banner ativo
- [ ] **AC-7:** On-demand health check em `/revisar` com lazy respawn (rejeita polling 30s per ADR-011):
  - Antes de aceitar `/revisar`: chamar `detect_running_ollama()` para :11434 + :11435
  - Se DOWN: tentar respawn 1 attempt + `wait_for_ollama_ready(timeout=10)`
  - Se respawn falha: HTTPException(503, retry-after 60s)
  - Verificável: integration test mock Ollama crash → retry respawn → 503 if fail
- [ ] **AC-8:** Status 503 retry-after header quando modelos pulling:
  - `is_ready()` returns False enquanto auto-pull rodando
  - `/revisar` retorna 503 + `Retry-After: 60` + JSON detail "Modelos baixando..."
  - Verificável: smoke test — startup pull rodando → POST /revisar → 503

### Funcionalidade — Edge cases + Safety (2/2 MUST)

- [ ] **AC-9:** 12 edge cases handled per ADR-011 (EC-01..EC-12) com mitigations específicas:
  - EC-01 binary não instalado → fail-fast com download URL clear
  - EC-02 :11434 ocupada por non-Ollama → port conflict detection + clear error
  - EC-03 :11435 ocupada por non-Ollama → idem
  - EC-04 disco cheio durante pull → `pre_check_disk_space(7GB)` + clear error
  - EC-05 network down → retry 3x exponential backoff
  - EC-06 app crash mid-startup → atomic PID write reduz janela; `cleanup_orphans_on_startup` pega survivor
  - EC-07 app crash mid-shutdown → kill BEFORE cleanup (ordem); orphan cleanup safety net
  - EC-08 Ollama crash mid-revisar → 500 gracioso com retry hint
  - EC-09 concurrent uploads enquanto starting → 503 retry-after
  - EC-10 antivirus blocking spawn → clear error + Windows Defender hint
  - EC-11 concurrent app instances → lockfile fcntl/msvcrt → AppAlreadyRunning error
  - EC-12 PID reuse race → `process_is_ours()` verify name + start_time match antes kill
  - Verificável: tests/unit cobre EC-01..EC-12 individualmente com mocks
- [ ] **AC-10:** `pre_check_disk_space(min_gb=7.0)` antes de pull:
  - `shutil.disk_usage(DATA_DIR).free < 7GB` → raise `DiskSpaceInsufficient` com mensagem clara
  - 7GB margin: qwen2.5:7b 4.7GB + qwen2.5:3b 1.9GB = 6.6GB + buffer 0.4GB
  - Verificável: test/unit mock `shutil.disk_usage` insufficient → exception

### Quality (2/2 MUST)

- [ ] **AC-11:** Tests criados:
  - `tests/unit/test_ollama_manager.py` (12+ tests cobrindo EC-01..EC-12 + 11 funcs com mocks)
  - `tests/integration/test_lifespan_ollama.py` (mock detect_running_ollama + verify lifespan flow)
  - Verificável: `pytest tests/unit/test_ollama_manager.py tests/integration/test_lifespan_ollama.py -v` PASS
- [ ] **AC-12:** README + SOP-revisar-pdf updated (remove manual Ollama setup steps):
  - README: substituir seção "Pré-requisitos Ollama" por "1 comando" UX
  - SOP-revisar-pdf: remover bullet "Ollama rodando" pre-requisite (auto-managed)
  - Verificável: `grep -c "ollama serve" README.md docs/sop-revisar-pdf.md` deve ser 0 OR só em refresh CLI context

### Quality (2/2 MUST adicional)

- [ ] **AC-13:** Suite testes 232+1+N baseline preservado (zero regressão + novos tests N adicionados)
  - Verificável: `python -m pytest --no-cov 2>&1 | tail -3` retorna 232+N passed
- [ ] **AC-14:** ruff All checks passed em arquivos modificados:
  - `bloco_interface/ollama_manager.py` (NEW) + `bloco_interface/web/app.py` + `bloco_interface/cli.py` (se modificado)
  - Verificável: `python -m ruff check bloco_interface/ollama_manager.py bloco_interface/web/app.py` All checks passed

---

## Tasks / Subtasks

### Phase A — Binary detection + lockfile (1.5h)

- [ ] **A.1** Criar `bloco_interface/ollama_manager.py` skeleton com 11 funções (signatures + docstrings)
- [ ] **A.2** Implementar `detect_ollama_binary()` cross-platform (copy-paste from ADR-011)
- [ ] **A.3** Implementar `acquire_app_lock()` com fcntl (Linux/Mac) + msvcrt (Windows) try-except
- [ ] **A.4** Implementar `cleanup_orphans_on_startup()` com `psutil.process_iter()` filtrando ollama do current user NOT em PID file
- [ ] **A.5** Tests unit `test_ollama_manager.py`:
  - `test_detect_binary_env_var_override` (mock OLLAMA_BINARY_PATH)
  - `test_detect_binary_windows_default` (mock sys.platform + Path.is_file)
  - `test_detect_binary_linux_default`
  - `test_detect_binary_mac_homebrew`
  - `test_detect_binary_path_search` (mock shutil.which)
  - `test_detect_binary_not_found` (returns None)
  - `test_acquire_lock_success`
  - `test_acquire_lock_already_locked` (raises AppAlreadyRunning)
  - `test_cleanup_orphans` (mock psutil + verify kill orphans)

### Phase B — Spawn + PID management (2h)

- [ ] **B.1** Implementar `spawn_ollama(binary, host, port)`:
  - subprocess.Popen com env OLLAMA_HOST + redirect stdout/stderr to log file
  - `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP` em Windows
  - `wait_for_ollama_ready(host, port, timeout=30)` after spawn
  - Raises `OllamaSpawnFailed` se não ficar ready
- [ ] **B.2** Implementar `write_pid_file_atomic(pids: dict)`:
  - JSON com schema_version + spawned_by_app_pid + spawned_at + instances list
  - Write to `.tmp` + `os.replace()` POSIX atomic
- [ ] **B.3** Implementar `read_pid_file_safely() -> dict`:
  - Try-except FileNotFoundError + JSONDecodeError
  - Returns empty dict se arquivo missing/corrupto
- [ ] **B.4** Implementar `process_is_ours(pid) -> bool`:
  - psutil.Process(pid).name() == "ollama" + username() == current_user
  - Try-except NoSuchProcess + AccessDenied
- [ ] **B.5** Implementar `kill_spawned_ollama()`:
  - Read PID file + `process_is_ours` verify + SIGTERM (timeout 5s) → SIGKILL fallback
  - Cleanup PID file at end
- [ ] **B.6** Tests unit:
  - `test_spawn_ollama_success` (mock subprocess.Popen + wait_for_ready)
  - `test_spawn_ollama_timeout` (raises OllamaSpawnFailed)
  - `test_write_pid_file_atomic` (verify temp + replace)
  - `test_read_pid_file_missing` (returns empty)
  - `test_read_pid_file_corrupt` (returns empty)
  - `test_process_is_ours_match`
  - `test_process_is_ours_pid_reuse` (mock Process com name diferente)
  - `test_kill_spawned_ollama` (mock psutil)

### Phase C — FastAPI lifespan integration (1.5h)

- [ ] **C.1** Refactor `bloco_interface/web/app.py` para usar `@asynccontextmanager` lifespan:
  - Substituir `app = FastAPI(...)` direto por `app = FastAPI(..., lifespan=lifespan)`
  - Lifespan startup chama: acquire_app_lock + cleanup_orphans + detect_ollama_binary + detect+spawn :11434 + :11435 + write_pid_file_atomic + asyncio.create_task ensure_models_pulled
  - Lifespan shutdown chama: kill_spawned_ollama + cleanup_pid_file + release lock_fd
- [ ] **C.2** Tratamento de erros lifespan startup:
  - `OllamaBinaryNotFound` → app fail-to-start com clear message
  - `AppAlreadyRunning` → exit code 1 + clear message
  - `DiskSpaceInsufficient` → fail com clear message
- [ ] **C.3** Tests integration `test_lifespan_ollama.py`:
  - Mock detect_running_ollama returning True (REUSE) → no spawn
  - Mock detect_running_ollama returning False → spawn called
  - Mock startup raise OllamaBinaryNotFound → app fail-to-start
- [ ] **C.4** Smoke local: `python -m bloco_interface.web.app` → log "Ollama lifecycle starting..." → spawn ollama → ready

### Phase D — Auto-pull + SSE progress (2h)

- [ ] **D.1** Implementar `ensure_models_pulled(required: list[str])`:
  - Chama `ollama list` parsing → identifica missing
  - `pre_check_disk_space(7.0)` antes de pull
  - For each missing: `subprocess.Popen(["ollama", "pull", model])` + parse stdout para progress
  - Update internal state via `_pull_status` global
  - Retry 3x exponential backoff em network errors
- [ ] **D.2** Implementar `get_pull_status() -> dict` + `is_ready() -> bool`:
  - Returns current state (`pulling`/`ready`/`error`) + model + percent + eta_seconds
  - is_ready() = state == "ready" AND all models present
- [ ] **D.3** Endpoint SSE `/ollama-status` em `bloco_interface/web/app.py`:
  ```python
  @app.get("/ollama-status")
  async def ollama_status_sse() -> StreamingResponse:
      async def event_generator() -> AsyncIterator[str]:
          while True:
              status = ollama_manager.get_pull_status()
              yield f"event: status\ndata: {json.dumps(status)}\n\n"
              if status["state"] in ("ready", "error"):
                  break
              await asyncio.sleep(2)
      return StreamingResponse(event_generator(), media_type="text/event-stream")
  ```
- [ ] **D.4** Update `index.html` com banner condicional:
  ```html
  <div id="ollama-status-banner" hx-ext="sse" sse-connect="/ollama-status" class="hidden">
    <p>⏳ Baixando modelos LLM... <span id="pull-percent">0</span>%</p>
    <p>ETA: <span id="pull-eta">calculando...</span></p>
  </div>
  ```
- [ ] **D.5** `/revisar` 503 quando `not is_ready()`:
  ```python
  if not ollama_manager.is_ready():
      raise HTTPException(503, detail="Modelos baixando...", headers={"Retry-After": "60"})
  ```

### Phase E — On-demand health check + 12 edge cases + tests + docs + closure (2-3h)

- [ ] **E.1** On-demand health check em `/revisar`:
  - Call `detect_running_ollama` para :11434 + :11435
  - If DOWN: lazy respawn 1 attempt + wait_for_ready
  - If respawn fails: HTTPException(503)
- [ ] **E.2** Tests específicos para cada edge case (EC-01..EC-12):
  - 12 test cases com mocks específicos validando mitigation funciona
- [ ] **E.3** Atualizar README:
  - Substituir seção "Pré-requisitos Ollama (manual)" por:
    ```markdown
    ## Como rodar (1 comando)

    ```bash
    python -m bloco_interface.web.app
    # → app auto-detecta Ollama, spawna instâncias missing, baixa modelos faltantes
    # → ready em ~30s (primeira vez pode levar 10-30min para download de modelos)
    ```
    ```
- [ ] **E.4** Atualizar `docs/sop-revisar-pdf.md`:
  - Remover bullet "Ollama rodando em :11434 + :11435" (auto-managed)
  - Adicionar nota: "App auto-gerencia Ollama lifecycle (ADR-011 — sessão 86)"
- [ ] **E.5** Rodar suite regression: `python -m pytest --no-cov 2>&1 | tail -5` → 232+N passed
- [ ] **E.6** Rodar ruff: `python -m ruff check bloco_interface/ollama_manager.py bloco_interface/web/app.py` → All checks passed
- [ ] **E.7** Atualizar Dev Agent Record + status story → Ready for Review
- [ ] **E.8** Emit handoff @dev → @qa Oracle gate

---

## Dev Notes

### D1 — Cross-platform binary detection (copy-paste from ADR-011)

**Reference completa:** `governance/architecture/adr/adr-011-auto-ollama-lifecycle.md` section "Cross-platform binary detection (priorizado)" (linhas ~120-160)

```python
def detect_ollama_binary() -> Optional[Path]:
    """Detect Ollama binary path com priority chain."""
    # Priority 1: env var override
    if path := os.environ.get("OLLAMA_BINARY_PATH"):
        return Path(path) if Path(path).is_file() else None

    # Priority 2: platform default
    candidates = []
    if sys.platform == "win32":
        candidates.append(Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Ollama" / "ollama.exe")
    elif sys.platform == "darwin":
        candidates.extend([
            Path("/opt/homebrew/bin/ollama"),  # Apple Silicon Homebrew
            Path("/usr/local/bin/ollama"),     # Intel Homebrew + manual
        ])
    else:  # Linux
        candidates.extend([
            Path("/usr/local/bin/ollama"),
            Path("/usr/bin/ollama"),
        ])

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    # Priority 3: PATH search
    if found := shutil.which("ollama"):
        return Path(found)

    return None  # Priority 4: caller raises clear error
```

### D2 — Atomic PID + Lockfile (copy-paste from ADR-011)

**Reference completa:** ADR-011 section "Atomic PID file write + lockfile" (linhas ~165-220)

```python
def write_pid_file_atomic(pids: dict[str, int]) -> None:
    pid_file = DATA_DIR / ".ollama-spawned.pid"
    temp = pid_file.with_suffix(".tmp")

    payload = {
        "schema_version": "1.0",
        "spawned_by_app_pid": os.getpid(),
        "spawned_at": datetime.utcnow().isoformat(),
        "instances": [
            {"role": role, "pid": pid, "host": "127.0.0.1", "port": 11434 if role == "advogado" else 11435}
            for role, pid in pids.items()
        ],
    }
    temp.write_text(json.dumps(payload, indent=2))
    os.replace(temp, pid_file)  # POSIX atomic


def acquire_app_lock() -> int:
    lock_file = DATA_DIR / ".app.lock"
    fd = os.open(str(lock_file), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except (BlockingIOError, OSError):
        os.close(fd)
        raise AppAlreadyRunning("App já rodando em outra instância")
```

### D3 — FastAPI Lifespan Integration (copy-paste from ADR-011)

**Reference completa:** ADR-011 section "FastAPI lifespan integration" (linhas ~310-345)

```python
from contextlib import asynccontextmanager
from bloco_interface import ollama_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    lock_fd = ollama_manager.acquire_app_lock()
    ollama_manager.cleanup_orphans_on_startup()

    binary = ollama_manager.detect_ollama_binary()
    if not binary:
        raise RuntimeError("Ollama binary não encontrado. Install: https://ollama.ai/download")

    spawned = {}
    if not await ollama_manager.detect_running_ollama("127.0.0.1", 11434):
        spawned["advogado"] = ollama_manager.spawn_ollama(binary, "127.0.0.1", 11434)
    if not await ollama_manager.detect_running_ollama("127.0.0.1", 11435):
        spawned["economista"] = ollama_manager.spawn_ollama(binary, "127.0.0.1", 11435)

    if spawned:
        ollama_manager.write_pid_file_atomic(spawned)

    asyncio.create_task(
        ollama_manager.ensure_models_pulled(["qwen2.5:7b", "qwen2.5:3b"])
    )

    yield

    # Shutdown
    ollama_manager.kill_spawned_ollama()
    ollama_manager.cleanup_pid_file()
    os.close(lock_fd)


app = FastAPI(title="Revisor Contratual", version="0.3.0", lifespan=lifespan)
```

### D4 — 12 Edge Cases reference

**Reference completa:** ADR-011 section "12 Edge Cases Mapeados" (linhas ~400-540) — cada EC tem detection + mitigation + user experience documented.

Resumo:

| EC | Cenário | Mitigation |
|---|---|---|
| EC-01 | Binary não instalado | Fail-fast com download URL |
| EC-02 | :11434 ocupada non-Ollama | Port conflict detection + clear error |
| EC-03 | :11435 ocupada non-Ollama | Idem EC-02 |
| EC-04 | Disco cheio durante pull | `pre_check_disk_space(7GB)` |
| EC-05 | Network down | Retry 3x exponential |
| EC-06 | App crash mid-startup | Atomic PID + cleanup_orphans next start |
| EC-07 | App crash mid-shutdown | Kill before cleanup ordem |
| EC-08 | Ollama crash mid-revisar | Retry once + 500 gracioso |
| EC-09 | Concurrent uploads pulling | 503 retry-after |
| EC-10 | Antivirus blocking | Clear error + Defender hint |
| EC-11 | Concurrent app instances | Lockfile fcntl/msvcrt |
| EC-12 | PID reuse race | process_is_ours verify name+start_time |

### Anti-patterns a evitar

- ❌ NÃO modificar `bloco_workflow/*` (orchestrator + personas REV-LLM-01 closed preserved)
- ❌ NÃO modificar `governance/architecture/adr/adr-011-*.md` (Accepted)
- ❌ NÃO modificar `governance/architecture/adr/adr-012-*.md` (paralela VAULT-FIX-01)
- ❌ NÃO modificar `bloco_vault/*` (VAULT-FIX-01 escopo)
- ❌ NÃO usar Docker/systemd (Options B/C rejeitadas no ADR-011)
- ❌ NÃO implementar polling 30s health check (rejeitado em ADR-011 — overkill)
- ❌ NÃO matar Ollama desktop existente em :11434 (detect-then-spawn preserva)

### Estratégia anti-regressão

- Suite testes deve continuar **232+1+N** após edits (N = novos tests AC-11)
- Cross-platform tests: rodar local Windows + adicionar comments para Linux/Mac expectations
- Phase C lifespan refactor pode quebrar testes integration existentes — verificar mocks
- Phase D auto-pull background task: garantir não bloqueia startup (asyncio.create_task)

### Phase D nuance importante

Auto-pull `ollama pull qwen2.5:7b` pode demorar **10-30 minutos** primeira vez (4.7GB download). Implementação:

- `subprocess.Popen` com `stdout=subprocess.PIPE` + parse stdout linha por linha
- Stdout format Ollama: `pulling abc123: 45% ▕████████░░░░░░░░░░░░░░░░░ ▏ 2.0 GB/4.4 GB  3.2 MB/s   12m`
- Regex parse `(\d+)%` para percent + `(\d+m)` para eta
- Update `_pull_status` global thread-safe (asyncio.Lock se necessário)

UI banner deve esconder após `state == "ready"`:
```javascript
container.addEventListener('htmx:sseMessage', function (e) {
  const data = JSON.parse(e.detail.data);
  if (data.state === "ready") {
    document.getElementById('ollama-status-banner').style.display = 'none';
  } else {
    document.getElementById('pull-percent').textContent = data.percent;
    document.getElementById('pull-eta').textContent = `${Math.floor(data.eta_seconds/60)} min`;
  }
});
```

---

## Files to Modify

- `bloco_interface/ollama_manager.py` (NEW ~400-500 LOC com 11 funções + custom exceptions: OllamaBinaryNotFound, OllamaSpawnFailed, AppAlreadyRunning, DiskSpaceInsufficient)
- `bloco_interface/web/app.py` (lifespan integration + endpoint /ollama-status SSE + 503 retry-after em /revisar)
- `bloco_interface/web/templates/index.html` (banner /ollama-status condicional)
- `README.md` (remove manual Ollama setup, adicionar "1 comando")
- `docs/sop-revisar-pdf.md` (remove pre-requisites Ollama manual)
- `tests/unit/test_ollama_manager.py` (NEW — 12+ tests)
- `tests/integration/test_lifespan_ollama.py` (NEW)
- `governance/TECH-DEBT.md` (Eric friction "Ollama gerenciado pela aplicação" → resolved + EC-XX edge cases tracking se aparecerem em produção)

## Files NOT to Modify

- `bloco_workflow/*` (orchestrator + personas + llm_factory.py preservados — REV-LLM-01 closed)
- `governance/architecture/adr/adr-011-*.md` (Accepted, não modificar)
- `governance/architecture/adr/adr-012-*.md` (paralela VAULT-FIX-01)
- `bloco_vault/*` (VAULT-FIX-01 escopo — NÃO tocar)
- Tests existentes (suite 232+1 baseline preservado)

---

## Tests Required

### Regressão + new (pytest)

```bash
python -m pytest --no-cov 2>&1 | tail -5
# Esperado: 232+N passed + 1 skipped (N = novos tests AC-11, ~20 tests)
```

### ollama_manager unit tests (mocks)

```bash
pytest tests/unit/test_ollama_manager.py -v --no-cov
# Esperado: 20+ PASS (binary detection × 6 + lockfile × 2 + spawn × 2 + PID × 4 + edge cases × 12)
```

### Lifespan integration tests

```bash
pytest tests/integration/test_lifespan_ollama.py -v --no-cov
# Esperado: ~6 PASS (REUSE existing, spawn missing, fail-to-start, shutdown cleanup)
```

### Smoke E2E manual (opcional, primeira vez)

```bash
# Mata todos backgrounds anteriores
taskkill /F /IM ollama.exe (Windows) ou pkill ollama (Linux/Mac)

# Roda app limpo
python -m bloco_interface.web.app

# Verifica logs:
# 1. "Ollama lifecycle starting..."
# 2. "Detect binary: <path>"
# 3. "Cleanup orphans: 0 found"
# 4. "Spawning advogado :11434 (PID X)"
# 5. "Spawning economista :11435 (PID Y)"
# 6. "Pulling qwen2.5:7b..." (se primeira vez, 10-30min)
# 7. "Server ready at http://127.0.0.1:8501"

# Browser http://127.0.0.1:8501
# - Banner ⏳ "Baixando modelos LLM..." se pulling
# - POST /revisar enquanto pulling → 503 retry-after
# - POST /revisar após pulling done → pipeline real funciona
```

### Lint

```bash
python -m ruff check bloco_interface/ollama_manager.py bloco_interface/web/app.py
# Esperado: All checks passed
```

---

## Dependencies

### Upstream

- ✅ ADR-011 accepted (Eric, sessão 86)
- ✅ REV-LLM-01 + DOCS-02 + UI-1 closed (Sprint 02 100% closed)
- ✅ psutil disponível (verificar pyproject.toml; se não, adicionar dep)
- ✅ Ollama binary instalado (Eric já tem em `%LOCALAPPDATA%\Programs\Ollama\ollama.exe`)

### Downstream

- 🔓 v0.3.0 release gate condition (Ollama auto-managed)
- 🔓 AC-9 retroativo UI-1 (smoke E2E real ponta a ponta)
- 🔓 UX target "1 comando" cumprido
- 🔓 Smith adversarial review (após VAULT-FIX-01 + OLLAMA-MGR-01 done)

---

## Definition of Done

1. ✅ Todos os 14 ACs passam
2. ✅ @qa (Oracle) PASS gate
3. ✅ Conventional commit pushed em main com cross-reference [Story OLLAMA-MGR-01] + ADR-011
4. ✅ CI verde
5. ✅ Suite 232+1+N baseline preservado
6. ✅ TECH-DEBT.md atualizado (Eric friction resolved)
7. ✅ README + SOP-revisar-pdf updated (manual setup removido)
8. ✅ Story status `Done`
9. ✅ Checkpoint sessão atualizado com SHA do commit

---

## Risk + Mitigation

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| 12 edge cases implementação tediosa | ALTA | Phase E estende > 3h | Phase E dedicada; tests por edge case validam mitigation |
| Cross-platform testing (só rodamos Windows) | MÉDIA | Linux/Mac bugs em produção | Docs com Linux/Mac expectations + opt-in CI matrix Sprint 04+ |
| Lockfile fcntl/msvcrt diff Windows/Unix | MÉDIA | Lockfile fail em platform específico | Try-except + fallback OS detection (sys.platform) |
| atexit + signal handlers cross-platform incomplete | MÉDIA | Orphan processes ocasionais | `cleanup_orphans_on_startup` safety net |
| Ollama binary não no PATH (Windows comum) | ALTA | Detection falha | Env var OLLAMA_BINARY_PATH override + clear error |
| Phase D auto-pull demora 10-30min primeira vez | ALTA | UX preocupante | SSE progress + 503 retry-after + UI banner |
| subprocess stdout/stderr OS differences | MÉDIA | Logging quebra | Open file handle approach + creationflags Windows-specific |
| 14 ACs > 8-10h effort estimate | MÉDIA | Story estende | Priorizar AC-1..AC-9 firme; AC-10..AC-14 closure se time |

---

## Change Log

| Data | Sessão | Quem | Ação |
|---|---|---|---|
| 2026-05-05 | 86 | @sm (River) | Story criada (status Ready) — escopo Aria mapeou (14 ACs, 5 phases, 12 edge cases ADR-011); paralela com VAULT-FIX-01 |

---

## Validation Notes (@po Keymaker)

### 10-Point Checklist

| # | Critério | Status | Evidência |
|---|---|---|---|
| 1 | Story title clear/específico | ✅ PASS | "Auto-Ollama Lifecycle Management Implementation — subprocess + detect-then-spawn + 12 edge cases" — escopo + decisão arquitetural + edge cases count + cita ADR-011 predecessor |
| 2 | User story format completo (As/I want/so that) | ✅ PASS | Linhas 33-36 com persona específica (operador first time local), motivação técnica (auto-gerencia Ollama lifecycle), benefício multi-dimensional (1 comando + preserva existing + UI progress) |
| 3 | ACs ≥5 testáveis com critérios numéricos | ✅ PASS | 14 ACs (5 Module+Detection + 3 Auto-pull+Health + 2 Edge cases+Safety + 2 Quality + 2 Docs) todos com critério verificável (grep, pytest, log message, HTTP status code) |
| 4 | Tasks/Subtasks granulares com checkbox | ✅ PASS | 5 phases (A:5 + B:6 + C:4 + D:5 + E:8 = 28 subtasks total) com `[ ]` checkbox e tempo estimado (1.5h + 2h + 1.5h + 2h + 2-3h ≈ 9h) |
| 5 | Dependencies explícitas (upstream/downstream) | ✅ PASS | Upstream: ADR-011 ✅ + REV-LLM-01/DOCS-02/UI-1 closed + psutil dep (verificar pyproject.toml) + Ollama binary instalado (Eric tem). Downstream: v0.3.0 gate + AC-9 retroativo + UX target "1 comando" + Smith review |
| 6 | Files to modify/NOT-modify listados | ✅ PASS | 8 modify (ollama_manager.py NEW ~400-500 LOC + app.py lifespan + index.html banner + README + SOP-revisar-pdf + 2 tests + TECH-DEBT) + 5 NOT-modify defensive (workflow/* + ADRs + bloco_vault paralela + tests existentes) |
| 7 | Tests required cobrem ACs | ✅ PASS | Regression (AC-13) + ruff (AC-14) + unit test_ollama_manager 12+ tests cobrindo EC-01..EC-12 + 11 funcs (AC-11a) + integration test_lifespan_ollama (AC-11b) + smoke E2E manual primeira vez (opcional) |
| 8 | Risk + Mitigation documentado | ✅ PASS | 8 riscos com Probabilidade/Impacto/Mitigação: 12 edge cases tediosos (Phase E dedicada), cross-platform Windows-only (CI matrix Sprint 04+), lockfile diff (try-except), signal handlers cross-platform (orphan cleanup safety net), binary PATH (env var override), auto-pull demora (SSE progress), subprocess OS diff (creationflags Windows), 14 ACs > effort (priorizar AC-1..AC-9) |
| 9 | Effort estimado realista | ✅ PASS | 8-10h com phase breakdown (1.5h + 2h + 1.5h + 2h + 2-3h ≈ 9h média) — alinhado com complexity 11 funcs + 12 edge cases + lifespan refactor + SSE endpoint + UI banner + cross-platform |
| 10 | Status correto (Ready) | ✅ PASS | frontmatter `status: Ready`; ADR-011 accepted Eric; Dev Notes citam ADR sections D1 binary detection + D2 atomic PID/lockfile + D3 lifespan + D4 12 edge cases — copy-paste-able; zero ambiguidade técnica |

**Score: 10/10 — GO**

### Decisão

✅ **GO (APROVADA)** — Story OLLAMA-MGR-01 está pronta para development. @dev (Neo) pode prosseguir com `*develop-yolo`.

### Forças destacadas (story exemplar)

- **Pattern eficiente Dev Notes** — D1-D4 citam ADR-011 sections específicas (linhas ~120-540) em vez de duplicar; Neo tem reference direta para algoritmos detect-then-spawn + 12 edge cases mitigations
- **12 edge cases mapeados estruturalmente** — Aria adicionou EC-11 (lockfile concurrent app) + EC-12 (PID reuse race) além dos 10 Morpheus; cada EC tem detection + mitigation + UX clara
- **Maior story Sprint 03 Phase 0** — proporcional à complexity (subprocess + lifecycle + 12 edge cases + SSE + cross-platform)
- **Defensive scope guards (5 NOT-modify)** — preservam workflow + ADRs + paralela story
- **Pre-check disk space (AC-10)** — `pre_check_disk_space(7GB)` antes de pull evita disco cheio mid-pull
- **On-demand health check (AC-7)** — rejeita polling 30s (Aria decision em ADR-011); lazy + auto-recovery 1 attempt
- **Cross-platform binary detection priority chain (AC-2)** — env var override → platform default → PATH search → fail-fast clear error

### Observações non-bloqueantes (advisory)

1. **Phase E auto-pull demora primeira vez** — `qwen2.5:7b` é 4.7GB, pode levar 10-30min em conexão lenta. SSE progress + UI banner mitigates UX. **Sugestão Oracle:** ao testar AC-9 EC-09 (concurrent uploads pulling), pode usar mock pra acelerar test (não rodar pull real)

2. **psutil dependency** — Story usa `psutil` para `process_is_ours` (EC-12) + `cleanup_orphans_on_startup` (EC-06). Verificar se já em pyproject.toml; se não, Phase A.4 deve adicionar dep + commit

3. **Cross-platform testing limited Windows** — Linux/Mac code paths são teóricos (não testados em runtime). **Sugestão futura (não blocker):** CI matrix Sprint 04+ rodar tests em Ubuntu + macOS runners

4. **AC-12 README + SOP update** — pode esquecer mid-implementation. Phase E.3 + E.4 explicitam isso, mas vale flag para Oracle gate verificar grep "ollama serve" zero em README/SOP pós-update

### Próximo handoff

**H-S03-OMG01-po2dev** → @dev (Neo) `*develop-yolo OLLAMA-MGR-01` (paralelo OR sequential com VAULT-FIX-01 — Eric decide).

— Keymaker, validando o canal Ollama lifecycle com 12 edge cases sob controle 🎯

---

## Dev Agent Record

> **A preencher pelo @dev (Neo) durante implementação.**

_(a preencher)_

---

## QA Results

> **A preencher pelo @qa (Oracle) durante gate.**

_(a preencher)_

---

*Story OLLAMA-MGR-01 — River (sessão 86, 2026-05-05) · Sprint 03 Phase 0 priority alta · Auto-Ollama Lifecycle Management · 8-10h effort estimado · resolves Eric friction "Ollama gerenciado pela aplicação" + 12 edge cases ADR-011 · paralela VAULT-FIX-01 · unblocks v0.3.0 + AC-9 retroativo UI-1*

— River, traduzindo arquitetura Aria em mapa Neo-readable cross-platform 🌊
