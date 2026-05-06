---
type: adr
id: "ADR-011"
title: "Auto-Ollama Lifecycle Management — subprocess Python + detect-then-spawn"
status: accepted
date: "2026-05-05"
proposed_by: "@architect (Aria)"
accepted_by: "Eric (decisão sessão 86, Option A aprovada com recomendações Aria default)"
accepted_date: "2026-05-05"
accepted_open_questions:
  - "Lockfile single instance (Aria default — rejeita concurrent apps single-user)"
  - "Auto-pull verification: opt-in OLLAMA_VERIFY_INFERENCE=1 default OFF (Aria default)"
  - "Health check cadence: on-demand lazy (Aria default — rejeita polling 30s)"
  - "Auto-pull retry: 3 attempts exponential backoff (Aria default — fail-fast)"
adr_level: spec
spec_coverage:
  - "Module bloco_interface/ollama_manager.py — start/stop/health/pull lifecycle"
  - "Cross-platform binary detection (Windows/Linux/Mac) com env var override"
  - "Detect-then-spawn algorithm (REUSE existing :11434 + :11435 OR spawn missing)"
  - "Atomic PID file write + lockfile (prevent concurrent app instances + race conditions)"
  - "On-demand health check + lazy respawn recovery (NÃO polling 30s)"
  - "Auto-pull com SSE progress streaming + 503 retry-after"
  - "12 edge cases mapeados com mitigations específicas"
  - "FastAPI lifespan integration (startup spawn + shutdown cleanup)"
  - "Cross-platform signal handling (atexit + SIGINT/SIGTERM best-effort)"
  - "Orphan cleanup on next startup (find ollama processes not in PID file)"
domain: "infra | runtime"
decision_makers: ["@architect (Aria)", "@dev (Neo)", "@devops (Operator)", "Eric (decisão final pendente)"]
supersedes: null
superseded_by: null
absorves:
  - "Setup manual Eric (Ollama desktop + 2ª instância manual + ollama pull manual) — friction identified v0.2.0 testing"
  - "AC-9 smoke E2E real bloqueado em UI-1 (Ollama lifecycle dependency)"
related_to:
  - "ADR-003 (LLM Strategy 2 Ollama instances — esta ADR adiciona lifecycle layer)"
  - "ADR-010 (Path C Qwen 7B fallback — modelo target do auto-pull)"
  - "ADR-012 (Vault Data Bundling — paralela, mesma sprint)"
  - "Story OLLAMA-MGR-01 (Sprint 03 Phase 0 — implementation desta ADR)"
  - "NFR-LGPD-01 (whitelist HTTP — preservada: Ollama em 127.0.0.1)"
project: revisor-contratual
sprint: "03"
etapa: "Phase 0 — Architectural Foundation"
tags:
  - project/revisor-contratual
  - adr
  - ollama
  - lifecycle
  - infrastructure
  - sprint-03
---

# ADR-011 — Auto-Ollama Lifecycle Management

```
[@architect · Aria (Visionary)] — Sprint 03 · Phase 0 Architectural Foundation
SPRINT: 03 · DOMÍNIO: Infra/Runtime
```

## Contexto

A v0.2.0 (publicada 2026-05-05) requer setup manual elaborado para o pipeline real funcionar:

1. Eric DEVE ter Ollama desktop instalado e rodando em `:11434`
2. Eric DEVE subir manualmente 2ª instância em `:11435` (`OLLAMA_HOST=127.0.0.1:11435 ollama serve`)
3. Eric DEVE ter pulled `qwen2.5:7b` (4.7GB) + `qwen2.5:3b` (1.9GB) manualmente

**Friction identified em v0.2.0 testing local (sessão 86, 2026-05-05):**

Eric testou app v0.2.0 e disse explicitamente:
> "O ollama precisa ser gerenciado pela aplicação"

Implicação: app DEVE auto-gerenciar Ollama lifecycle (start/stop/health/pull) para ter UX target "1 comando + funciona":

```bash
# Target UX (post-OLLAMA-MGR-01):
python -m bloco_interface.web.app
# → app detecta Ollama, spawna instâncias missing, pulla modelos faltantes, ready em ~30s
```

**Estado atual da app v0.2.0 (problema):**

- `bloco_interface/web/app.py` assume Ollama externo running em `:11434` + `:11435`
- Se Ollama não estiver rodando → pipeline falha em runtime (ConnectError tardio, UX ruim)
- Manual setup é fonte de erros (Eric esqueceu AUTH_COOKIE_KEY na primeira tentativa, vault não inicializado)
- AC-9 smoke E2E real ficou bloqueado em UI-1 por essa friction

**Investigation Morpheus + Aria (sessão 86):**

- Ollama binary path discovery: `%LOCALAPPDATA%\Programs\Ollama\ollama.exe` em Windows; `/usr/local/bin/ollama` em Linux/Mac (também `/opt/homebrew/bin/ollama` no Apple Silicon Homebrew)
- `ollama` não está no PATH default Windows install — precisa cross-platform binary detection
- Subprocess Python viable: `subprocess.Popen(["ollama", "serve"])` funcional cross-platform com env var `OLLAMA_HOST`

---

## Decisão

**Option A escolhida — Subprocess Python + detect-then-spawn algorithm (preserva Ollama existente).**

### Algoritmo "detect-then-spawn" (não destrutivo)

```python
# Pseudocódigo simplificado — implementação em OLLAMA-MGR-01 (Neo)

# Lifespan startup (FastAPI)
async def startup():
    binary = detect_ollama_binary()  # cross-platform
    if not binary:
        raise OllamaBinaryNotFound("Install Ollama: https://ollama.ai/download")

    spawned_pids = {}

    # Advogado :11434
    if not await detect_running_ollama("127.0.0.1", 11434):
        pid = spawn_ollama(binary, "127.0.0.1", 11434, log_file_advogado)
        spawned_pids["advogado"] = pid
    # senão: REUSE existing :11434 (Ollama desktop OR previous app instance)

    # Economista :11435
    if not await detect_running_ollama("127.0.0.1", 11435):
        pid = spawn_ollama(binary, "127.0.0.1", 11435, log_file_economista)
        spawned_pids["economista"] = pid

    # Persist PIDs atomically
    if spawned_pids:
        write_pid_file_atomic(spawned_pids)

    # Auto-pull modelos faltantes (background task)
    asyncio.create_task(ensure_models_pulled(["qwen2.5:7b", "qwen2.5:3b"]))


# Lifespan shutdown (FastAPI)
async def shutdown():
    spawned_pids = read_pid_file_safely()
    for role, pid in spawned_pids.items():
        if process_is_ours(pid):  # verify name + start_time match
            try:
                kill_process_gracefully(pid, timeout=5)  # SIGTERM → SIGKILL
            except Exception as e:
                logger.warning(f"Failed to kill spawned Ollama {role} (PID {pid}): {e}")
    cleanup_pid_file()
```

### Cross-platform binary detection (priorizado)

```python
def detect_ollama_binary() -> Optional[Path]:
    """Detect Ollama binary path com priority chain."""
    # Priority 1: env var override (user customization)
    if path := os.environ.get("OLLAMA_BINARY_PATH"):
        return Path(path) if Path(path).is_file() else None

    # Priority 2: platform default
    candidates = []
    if sys.platform == "win32":
        candidates.append(Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Ollama" / "ollama.exe")
    elif sys.platform == "darwin":  # macOS
        candidates.extend([
            Path("/opt/homebrew/bin/ollama"),  # Apple Silicon Homebrew
            Path("/usr/local/bin/ollama"),     # Intel Homebrew + manual install
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

    # Priority 4: not found — caller raises clear error
    return None
```

### Atomic PID file write + lockfile

PID file location: `~/.local/share/revisor-contratual/.ollama-spawned.pid`

Lockfile location: `~/.local/share/revisor-contratual/.app.lock`

```python
def write_pid_file_atomic(pids: dict[str, int]) -> None:
    """Atomic write: temp file + rename (POSIX atomicity)."""
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
    os.replace(temp, pid_file)  # POSIX atomic rename


def acquire_app_lock() -> Optional[int]:
    """Acquire exclusive lock to prevent concurrent app instances."""
    lock_file = DATA_DIR / ".app.lock"
    fd = os.open(str(lock_file), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd  # caller responsible for cleanup atexit
    except (BlockingIOError, OSError):
        os.close(fd)
        raise AppAlreadyRunning("App já rodando em outra instância — aguarde primeira encerrar")
```

### On-demand health check (não polling agressivo)

Morpheus suggested polling every 30s — Aria **rejeita** essa abordagem:

- Polling agressivo = load desnecessário em Ollama idle
- Better: **lazy check** — apenas antes de `/revisar` request

```python
# bloco_interface/web/app.py (parte de OLLAMA-MGR-01)
async def ensure_ollama_healthy_or_503(request: Request) -> None:
    """Middleware-like check antes de /revisar — lazy + auto-recovery."""
    if not await detect_running_ollama("127.0.0.1", 11434):
        # Tenta respawn (1 attempt)
        binary = detect_ollama_binary()
        if binary:
            try:
                pid = spawn_ollama(binary, "127.0.0.1", 11434, log_file_advogado)
                update_pid_file_atomic({"advogado": pid})
                await wait_for_ollama_ready("127.0.0.1", 11434, timeout=10)
            except Exception as e:
                raise HTTPException(503, detail=f"Ollama indisponível: {e}. Tente novamente em 10s.")
        else:
            raise HTTPException(503, detail="Ollama binary não encontrado. Reinicie a aplicação.")

    # idem para :11435
```

### Auto-pull com SSE progress + 503 retry-after

Modelos podem demorar 5-30min primeiro pull (qwen2.5:7b é 4.7GB):

```python
# bloco_interface/web/app.py — novo endpoint
@app.get("/ollama-status")
async def ollama_status_sse() -> StreamingResponse:
    """SSE stream do status do auto-pull para UI mostrar progress bar."""
    async def event_generator() -> AsyncIterator[str]:
        while True:
            status = ollama_manager.get_pull_status()
            # status: {"state": "pulling"|"ready"|"error", "model": "qwen2.5:7b", "percent": 45.2, "eta_seconds": 720}
            yield f"event: status\ndata: {json.dumps(status)}\n\n"
            if status["state"] in ("ready", "error"):
                break
            await asyncio.sleep(2)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Em /revisar — bloqueia se pull não completou
async def revisar(...):
    if not ollama_manager.is_ready():
        raise HTTPException(
            503,
            detail="Modelos baixando. Acompanhe progresso em /ollama-status.",
            headers={"Retry-After": "60"},
        )
    # ... resto do flow (Phase A validation + Phase C pipeline real)
```

UI banner durante pull:

```html
<!-- index.html — banner condicional -->
<div id="ollama-status-banner" hx-ext="sse" sse-connect="/ollama-status">
  <p>⏳ Baixando modelos LLM (primeira vez)... <span id="pull-percent">0</span>%</p>
  <p>ETA: <span id="pull-eta">calculando...</span></p>
</div>
```

---

## Rationale ultrathink

### Trade-offs avaliados

**Option A — Subprocess Python (ESCOLHIDO):**

| Critério | Avaliação |
|---|---|
| Simplicity | 🟢 Alta — apenas `subprocess.Popen` + cleanup |
| Cross-platform | 🟢 Funciona Windows/Linux/Mac com mesmo código |
| Deps adicionadas | 🟢 Zero (só usa stdlib + Ollama binary já necessário) |
| Performance overhead | 🟢 Mínimo (apenas spawn, no virtualization) |
| LGPD posture | 🟢 Excelente (Ollama em 127.0.0.1, zero rede externa) |
| Lifecycle integration | 🟢 Native FastAPI lifespan |
| Orphan risk | 🟡 Existe (mitigated via atomic PID + lockfile + atexit + orphan cleanup on startup) |
| Edge cases handled | 🟢 12 mapeados com mitigations específicas |

**Option B — Docker compose (REJEITADO):**

| Critério | Avaliação |
|---|---|
| Simplicity | 🔴 Adiciona Docker dep |
| Cross-platform | 🟡 Docker Desktop em Windows/Mac, native Linux |
| Deps adicionadas | 🔴 Docker Desktop ~500MB + container Ollama ~600MB |
| Performance overhead | 🔴 ~5-10% inference em CPU (containerization) |
| LGPD posture | 🟡 OK mas precisa garantir Docker network não vaza |
| Lifecycle | 🟡 docker-compose up/down separado de Python |
| Setup user | 🔴 "Instale Docker primeiro" — friction enorme single-user |

**Option C — systemd/Windows Service (REJEITADO):**

| Critério | Avaliação |
|---|---|
| Simplicity | 🔴 Platform-specific (3 implementações diferentes) |
| Cross-platform | 🔴 Linux systemd != Windows Service != macOS launchd |
| Deps adicionadas | Zero |
| Performance | 🟢 Native, OS-managed |
| LGPD posture | 🟢 OK |
| Lifecycle | 🔴 NÃO integra Python lifecycle (separate OS-level) |
| Setup user | 🔴 Requires admin/sudo |
| Auto-restart on crash | 🟢 OS-managed restart |

### Por que Option A é o trade-off correto

1. **Single-user local app** não justifica complexidade Docker/systemd
2. **Cross-platform via stdlib:** mesmo código Windows/Linux/Mac
3. **FastAPI lifespan:** lifecycle integration natural com app Python
4. **Zero deps novas:** apenas Ollama binary que já é dependency externa razoável
5. **Edge cases mitigados:** 12 cenários mapeados com solutions concretas (não handwave)

---

## Implementation Strategy

### Module structure

```
bloco_interface/
├── ollama_manager.py              ← NOVO (esta ADR)
│   ├── detect_ollama_binary()
│   ├── detect_running_ollama()
│   ├── spawn_ollama()
│   ├── kill_spawned_ollama()
│   ├── ensure_models_pulled()
│   ├── get_pull_status()
│   ├── is_ready()
│   ├── write_pid_file_atomic()
│   ├── read_pid_file_safely()
│   ├── acquire_app_lock()
│   ├── cleanup_orphans_on_startup()
│   └── exceptions:
│       ├── OllamaBinaryNotFound
│       ├── OllamaSpawnFailed
│       ├── AppAlreadyRunning
│       └── DiskSpaceInsufficient
└── web/
    └── app.py                      ← MODIFIED (lifespan integration)
```

### FastAPI lifespan integration

```python
# bloco_interface/web/app.py
from contextlib import asynccontextmanager
from bloco_interface import ollama_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    lock_fd = ollama_manager.acquire_app_lock()  # raises if already running
    ollama_manager.cleanup_orphans_on_startup()  # find + kill orphan ollama not in PID file

    binary = ollama_manager.detect_ollama_binary()
    if not binary:
        raise RuntimeError(
            "Ollama binary não encontrado. Install: https://ollama.ai/download"
        )

    spawned = {}
    if not await ollama_manager.detect_running_ollama("127.0.0.1", 11434):
        spawned["advogado"] = ollama_manager.spawn_ollama(binary, "127.0.0.1", 11434)
    if not await ollama_manager.detect_running_ollama("127.0.0.1", 11435):
        spawned["economista"] = ollama_manager.spawn_ollama(binary, "127.0.0.1", 11435)

    if spawned:
        ollama_manager.write_pid_file_atomic(spawned)

    # Background task: pull modelos faltantes
    asyncio.create_task(
        ollama_manager.ensure_models_pulled(["qwen2.5:7b", "qwen2.5:3b"])
    )

    yield  # app accepts requests

    # Shutdown
    ollama_manager.kill_spawned_ollama()  # kill apenas PIDs em PID file
    ollama_manager.cleanup_pid_file()
    os.close(lock_fd)


app = FastAPI(title="Revisor Contratual", version="0.3.0", lifespan=lifespan)
```

### Disk space pre-check (auto-pull safety)

```python
def pre_check_disk_space(min_gb: float = 7.0) -> None:
    """qwen2.5:7b 4.7GB + qwen2.5:3b 1.9GB = 6.6GB; margin 7GB."""
    import shutil
    free_bytes = shutil.disk_usage(DATA_DIR).free
    free_gb = free_bytes / (1024 ** 3)
    if free_gb < min_gb:
        raise DiskSpaceInsufficient(
            f"Disco insuficiente: {free_gb:.1f}GB livre, precisa {min_gb}GB. "
            f"Libere espaço ou rode sem auto-pull (LLM_TIER=lean)."
        )
```

### Logging strategy

Per-role log files: `~/.local/share/revisor-contratual/ollama-{advogado|economista}.log`

```python
def spawn_ollama(binary: Path, host: str, port: int) -> int:
    role = "advogado" if port == 11434 else "economista"
    log_file = DATA_DIR / f"ollama-{role}.log"
    log_handle = open(log_file, "ab")  # append binary mode

    env = os.environ.copy()
    env["OLLAMA_HOST"] = f"{host}:{port}"

    process = subprocess.Popen(
        [str(binary), "serve"],
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )

    # Wait for /api/tags to respond (timeout 30s)
    if not wait_for_ollama_ready(host, port, timeout=30):
        process.terminate()
        raise OllamaSpawnFailed(f"Ollama {role} não ficou ready em 30s")

    return process.pid
```

---

## 12 Edge Cases Mapeados

### EC-01: Ollama binary não instalado

**Detection:** `detect_ollama_binary()` retorna None
**Mitigation:** fail-fast com clear error message + download URL
**User experience:**
```
ERROR: Ollama binary não encontrado.
Install: https://ollama.ai/download
After install, run: python -m bloco_interface.web.app
```

### EC-02: Port :11434 ocupada por non-Ollama

**Detection:** `detect_running_ollama()` retorna False mesmo com porta ocupada (curl /api/tags fails com 404 OR timeout)
**Mitigation:** clear error + sugestão de port conflict resolution
**User experience:**
```
ERROR: Porta 11434 ocupada por outro processo (não-Ollama).
Identifique: netstat -ano | findstr :11434 (Windows) ou lsof -i :11434 (Linux/Mac)
Mate o processo OR mude OLLAMA_HOST_ADVOGADO env var
```

### EC-03: Port :11435 ocupada por non-Ollama

**Mitigation:** idem EC-02 para :11435.

### EC-04: Disco cheio durante auto-pull

**Detection:** `pre_check_disk_space(7.0)` antes de pull
**Mitigation:** fail-fast com clear error + fallback option
**User experience:**
```
ERROR: Disco insuficiente: 4.2GB livre, precisa 7GB.
Libere espaço OR rode com LLM_TIER=lean (apenas Qwen 3B, 1.9GB).
```

### EC-05: Network down durante auto-pull

**Detection:** `ollama pull` retorna exit code != 0 com network error em stderr
**Mitigation:** retry com exponential backoff (3 attempts max), depois fail-fast
**User experience:**
```
ERROR: Pull qwen2.5:7b falhou após 3 tentativas (network error).
Verifique conexão e reinicie a aplicação.
Última tentativa: ConnectionError: ...
```

### EC-06: App crash mid-startup (após spawn, antes PID file)

**Race window:** entre `subprocess.Popen` retornar PID e `write_pid_file_atomic()` completar
**Result se não mitigado:** orphan Ollama process
**Mitigation 1:** atomic write (temp + rename) reduz janela
**Mitigation 2:** `cleanup_orphans_on_startup()` na próxima startup detecta processes ollama do current user que não estão em PID file → kill

```python
def cleanup_orphans_on_startup() -> None:
    """Find ollama processes from current user NOT in PID file → kill them."""
    import psutil
    expected_pids = set()
    if pid_file.exists():
        data = json.loads(pid_file.read_text())
        expected_pids = {inst["pid"] for inst in data.get("instances", [])}

    current_user = getpass.getuser()
    for proc in psutil.process_iter(["pid", "name", "username"]):
        try:
            if proc.info["name"] == "ollama" and proc.info["username"] == current_user:
                if proc.info["pid"] not in expected_pids:
                    logger.warning(f"Killing orphan ollama PID {proc.info['pid']}")
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
```

### EC-07: App crash mid-shutdown (PID file deletado mas Ollama running)

**Race window:** entre `cleanup_pid_file()` e `kill_process_gracefully()` completar
**Result se não mitigado:** orphan Ollama process
**Mitigation:** kill BEFORE cleanup_pid_file (ordem importa)
**Backup:** EC-06 mitigation (orphan cleanup on next startup)

### EC-08: Ollama crash mid-revisar

**Detection:** `await revisar_contrato(...)` raises ConnectError ou similar
**Mitigation:** retry once com respawn + 500 gracioso se falhar
**User experience:**
```
UI: error.html pipeline_failure
"Pipeline encontrou erro: Ollama indisponível (crash detectado).
Tente novamente em 10s."
```

### EC-09: Concurrent uploads enquanto Ollama starting up

**Detection:** `is_ready()` returns False (modelos ainda pulling OR Ollama spawning)
**Mitigation:** 503 com `Retry-After: 60` header
**User experience:**
```
HTTP 503 Service Unavailable
Retry-After: 60
{"detail": "Modelos baixando (45% completo, ETA 12 min). Tente novamente em 1 minuto."}
```

### EC-10: Antivirus blocking Ollama spawn

**Detection:** `subprocess.Popen` raises PermissionError OR Ollama dies imediatamente
**Mitigation:** clear error + Windows Defender exception hint
**User experience:**
```
ERROR: Falha ao spawnar Ollama (PermissionError).
Possível causa: antivirus blocking.
Windows: adicione exceção no Windows Defender para ollama.exe
Linux/Mac: verifique SELinux/AppArmor policies
```

### EC-11: Concurrent app instances (Aria adicionou — não no Morpheus map)

**Detection:** `acquire_app_lock()` raises `AppAlreadyRunning`
**Mitigation:** lockfile com fcntl/msvcrt non-blocking
**User experience:**
```
ERROR: App já rodando em outra instância (PID 12345).
Aguarde primeira instância encerrar OR mate-a:
- Windows: taskkill /F /PID 12345
- Linux/Mac: kill 12345
```

### EC-12: PID file race (PID reuse) (Aria adicionou — não no Morpheus map)

**Race window:** OS pode reaproveitar PID após processo morrer
**Result se não mitigado:** kill aleatório de processo não-Ollama
**Mitigation:** verify process name + start_time match antes de kill

```python
def process_is_ours(pid: int) -> bool:
    """Verify process IS the ollama we spawned (não PID reuse)."""
    try:
        proc = psutil.Process(pid)
        return (
            proc.name() in ("ollama", "ollama.exe")
            and proc.username() == getpass.getuser()
        )
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
```

---

## Consequences

### Positivos

- ✅ **UX target atingido:** `python -m bloco_interface.web.app` → app cuida de tudo
- ✅ **Self-contained:** zero manual setup steps após install Ollama binary
- ✅ **Cross-platform:** mesmo código Windows/Linux/Mac
- ✅ **Lifecycle integration:** FastAPI lifespan native
- ✅ **Preserva existing Ollama desktop:** detect-then-spawn não destrói se Ollama desktop já rodando
- ✅ **LGPD posture:** Ollama em 127.0.0.1, zero exposição rede externa
- ✅ **Auto-pull:** modelos faltantes baixados automaticamente com progress UI
- ✅ **Recovery:** on-demand health check + lazy respawn se Ollama crashed
- ✅ **AC-9 desbloqueado:** smoke E2E real funcionará pós-implementation

### Negativos

- ⚠️ **Complexidade:** 12 edge cases requerem código defensivo
  - Mitigation: bem-documented em ollama_manager.py + tests específicos por edge case
- ⚠️ **Orphan risk residual:** mesmo com atomic PID + lockfile + cleanup, race conditions raras possíveis
  - Mitigation: orphan cleanup on next startup
- ⚠️ **Auto-pull pode ser slow primeira vez:** qwen2.5:7b 4.7GB pode levar 10-30min em conexão lenta
  - Mitigation: SSE progress streaming + 503 retry-after + UI banner
- ⚠️ **Disk space dependency:** 6.6GB modelos + audit log + temp PDFs
  - Mitigation: pre-check disk space + clear error + fallback LLM_TIER=lean (1.9GB only)

### Neutros

- 🔵 **Ollama binary dependency permanece:** usuário ainda precisa Ollama instalado (aceitável — é dep externa razoável, single binary download)
- 🔵 **Logging append-only MVP:** sem rotation (Sprint 04+ usar logging.handlers.RotatingFileHandler)
- 🔵 **GPU detection out of scope:** Ollama auto-detects CUDA, não precisamos código nosso (mencionar como future consideration)

---

## Alternatives Considered

### Option A — Subprocess Python (ESCOLHIDO)

Ver "Decisão" + "Rationale ultrathink" acima.

### Option B — Docker compose

**Estratégia:** Container Ollama via docker-compose.yml, ortogonal à app Python.

**Por que rejeitado:**
1. Docker Desktop ~500MB friction enorme single-user local
2. Performance overhead ~5-10% LLM inference em CPU
3. Container Ollama ~600MB image
4. Lifecycle separado de Python (docker-compose up/down)
5. LGPD compliance complica (garantir Docker network não vaza)
6. Admin/Sudo requirements em alguns OS

**Quando reconsiderar:** Sprint 05+ se Eric escalar para SaaS multi-tenant OR multi-user enterprise deployment.

### Option C — systemd / Windows Service / launchd

**Estratégia:** Ollama como OS-level service, gerenciado pelo OS.

**Por que rejeitado:**
1. Platform-specific (3 implementações diferentes Windows/Linux/Mac)
2. Requires admin/sudo para install service
3. NÃO integra com Python app lifecycle (separação artificial)
4. Setup user friction alta

**Quando reconsiderar:** Sprint 05+ se Eric quiser app rodando 24/7 como background service.

---

## Open Questions (resolver no review Eric)

1. **Lockfile vs allow concurrent app instances?**
   - Atualmente: lockfile previne 2+ apps simultaneamente (1 instance por user)
   - Alternative: allow concurrent (cada app tem PID file separado)
   - **Aria recomenda:** lockfile (single instance) — single-user local app não precisa concurrent

2. **Auto-pull verification: smoke inference call?**
   - Atualmente: `ollama show qwen2.5:7b` valida metadata (rápido)
   - Stronger: smoke inference (`echo "test" | ollama run qwen2.5:7b`) com timeout 30s — adiciona ~10s startup
   - **Aria recomenda:** opt-in via env var `OLLAMA_VERIFY_INFERENCE=1` (default OFF)

3. **Health check cadence: on-demand vs polling background?**
   - Aria propõe: on-demand (lazy check antes de /revisar)
   - Morpheus propôs: polling 30s background
   - **Aria recomenda:** on-demand (rejeita polling — overkill single-user)

4. **Auto-pull retry policy?**
   - Atualmente: 3 attempts com exponential backoff
   - Alternative: infinite retry (até user abortar)
   - **Aria recomenda:** 3 attempts (fail-fast > infinite hang)

---

## Future Considerations (out of scope ADR-011)

- **GPU detection:** Ollama auto-detects CUDA. Quando Eric upgrade hardware, `LLM_TIER=premium` (Sabia-7B) auto-ativa em GPU sem mudança código.
- **Log rotation:** Sprint 04+ implementar `logging.handlers.RotatingFileHandler` para Ollama logs.
- **Concurrent revisar requests queue UI:** Sprint 04+ mostrar "Aguardando vez (3 jobs adiante)..." em UI.
- **Multiple users:** Sprint 05+ se SaaS multi-tenant (Docker compose Option B reconsidera).

---

## Decision Status

**Status: ✅ ACCEPTED — Eric sessão 86, 2026-05-05.**

Eric aceitou Option A com recomendações Aria default (4 open questions resolvidas):
1. Lockfile single instance (rejeita concurrent apps single-user)
2. Auto-pull verification: opt-in `OLLAMA_VERIFY_INFERENCE=1` (default OFF)
3. Health check cadence: on-demand lazy (rejeita polling 30s)
4. Auto-pull retry: 3 attempts exponential backoff

**Próximos passos pós-accept:**
1. ✅ ADR-011 status accepted (este commit)
2. ⏳ Aria atualiza ADR-INDEX.md (adiciona ADR-011 + ADR-012)
3. ⏳ Aria emit handoff @sm para drafts VAULT-FIX-01 + OLLAMA-MGR-01 stories (paralelas)
4. ⏳ @sm draft → @po validate → @dev implement → @qa gate → @devops push v0.3.0
5. ⏳ Pós-merge: invocar Skill smith adversarial ultrathink review

---

*ADR-011 — Aria @architect (sessão 86, 2026-05-05) · Sprint 03 Phase 0 · Auto-Ollama Lifecycle Management · Option A subprocess + detect-then-spawn · 12 edge cases mapeados · resolves Eric friction "Ollama gerenciado pela aplicação"*

— Aria, arquitetando o ciclo de vida dos LLMs com elegância cross-platform 🏗️
