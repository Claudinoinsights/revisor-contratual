"""Auto-Ollama Lifecycle Management — OLLAMA-MGR-01 (ADR-011).

Implementa o gerenciamento automático do Ollama pelo Revisor Contratual:
detect-then-spawn das 2 instâncias (Sabia/Qwen em :11434 + Qwen 3B em :11435),
auto-pull de modelos faltantes, on-demand health check com lazy respawn,
e cleanup graceful de processos spawned via PID file + lockfile cross-platform.

Decisão arquitetural: ADR-011 (Accepted Eric, sessão 86). Substitui setup manual
identificado em sessão 86 v0.2.0 testing ("O ollama precisa ser gerenciado pela
aplicação"). UX target: ``python -m bloco_interface.web.app`` como único comando.

Design highlights (per ADR-011):

* **Cross-platform binary detection** — priority chain env var → platform default → PATH
* **Atomic PID file write** — temp + ``os.replace()`` POSIX atomic
* **Lockfile concurrent-app prevention** — ``fcntl`` Linux/Mac, ``msvcrt`` Windows
* **detect-then-spawn** — preserva Ollama desktop existente em :11434
* **On-demand health check** — lazy respawn em ``/revisar`` (rejeita polling 30s)
* **PID reuse race protection** — ``process_is_ours()`` verifica name + start_time
* **Auto-pull background** — ``asyncio.create_task`` não bloqueia startup
* **SSE progress streaming** — ``/ollama-status`` event stream para UI banner

Edge cases mitigados (12 catalogados em ADR-011 EC-01..EC-12) — implementação
incremental por phase per story OLLAMA-MGR-01.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Pull status state (Phase D) ──────────────────────────────────────────
# Module-level state acessível por get_pull_status / is_ready / SSE endpoint.
# Default state="ready" cobre o caso REUSE (Ollama existente já tem modelos).
# ensure_models_pulled atualiza progressivamente durante background download.

_pull_status: dict[str, object] = {
    "state": "ready",
    "model": None,
    "percent": 100,
    "eta_seconds": 0,
}
_pull_lock = asyncio.Lock()

# Regex para parse stdout do `ollama pull` (formato:
# "pulling abc123: 45% ▕████████░░░░░░░░░░░░░░ ▏ 2.0 GB/4.4 GB  3.2 MB/s   12m")
_PERCENT_RE = re.compile(r"(\d+)%")
_ETA_RE = re.compile(r"(\d+)m(?:(\d+)s)?\s*$")

# ── Constants ─────────────────────────────────────────────────────────────

DATA_DIR = Path.home() / ".local" / "share" / "revisor-contratual"
PID_FILE = DATA_DIR / ".ollama-spawned.pid"
LOCK_FILE = DATA_DIR / ".app.lock"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT_ADVOGADO = 11434
DEFAULT_PORT_ECONOMISTA = 11435

REQUIRED_MODELS = ("qwen2.5:7b", "qwen2.5:3b")
MIN_DISK_SPACE_GB = 7.0  # qwen2.5:7b 4.7GB + qwen2.5:3b 1.9GB + buffer 0.4GB

PID_FILE_SCHEMA_VERSION = "1.0"


# ── Custom Exceptions ─────────────────────────────────────────────────────


class OllamaBinaryNotFound(RuntimeError):  # noqa: N818
    """Ollama binary não foi localizado pelo priority chain. EC-01.

    Nome sem suffix ``Error`` per spec story OLLAMA-MGR-01 AC-1.
    """


class OllamaSpawnFailed(RuntimeError):  # noqa: N818
    """Subprocess Ollama spawned mas não ficou ready dentro do timeout.

    Nome sem suffix ``Error`` per spec story OLLAMA-MGR-01 AC-1.
    """


class AppAlreadyRunning(RuntimeError):  # noqa: N818
    """Outra instância do app já adquiriu o lockfile. EC-11.

    Nome sem suffix ``Error`` per spec story OLLAMA-MGR-01 AC-1.
    """


class DiskSpaceInsufficient(RuntimeError):  # noqa: N818
    """Disco com espaço insuficiente para auto-pull dos modelos. EC-04.

    Nome sem suffix ``Error`` per spec story OLLAMA-MGR-01 AC-1.
    """


# ── Phase A.2 — Cross-platform binary detection ───────────────────────────


def detect_ollama_binary() -> Path | None:
    """Detecta o binário Ollama com priority chain cross-platform.

    Priority chain (per ADR-011):

    1. Env var ``OLLAMA_BINARY_PATH`` — override explícito do operador
    2. Platform default — caminhos canônicos por OS
       - Windows: ``%LOCALAPPDATA%/Programs/Ollama/ollama.exe``
       - macOS: ``/opt/homebrew/bin/ollama`` (Apple Silicon) ou ``/usr/local/bin/ollama`` (Intel)
       - Linux: ``/usr/local/bin/ollama`` ou ``/usr/bin/ollama``
    3. ``shutil.which("ollama")`` — busca no PATH do sistema
    4. ``None`` — caller deve raise ``OllamaBinaryNotFound`` com download URL

    Returns:
        Path para o binário se encontrado, None caso contrário.
    """
    # Priority 1: env var override
    if env_path := os.environ.get("OLLAMA_BINARY_PATH"):
        candidate = Path(env_path)
        if candidate.is_file():
            logger.debug("detect_ollama_binary: env override hit -> %s", candidate)
            return candidate
        logger.warning(
            "detect_ollama_binary: OLLAMA_BINARY_PATH=%s não é arquivo válido (ignorado)",
            env_path,
        )

    # Priority 2: platform default
    candidates: list[Path] = []
    if sys.platform == "win32":
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            candidates.append(Path(local_appdata) / "Programs" / "Ollama" / "ollama.exe")
    elif sys.platform == "darwin":
        candidates.extend(
            [
                Path("/opt/homebrew/bin/ollama"),  # Apple Silicon
                Path("/usr/local/bin/ollama"),  # Intel + manual install
            ]
        )
    else:  # Linux + outros UNIX
        candidates.extend(
            [
                Path("/usr/local/bin/ollama"),
                Path("/usr/bin/ollama"),
            ]
        )

    for candidate in candidates:
        if candidate.is_file():
            logger.debug("detect_ollama_binary: platform default hit -> %s", candidate)
            return candidate

    # Priority 3: PATH search
    if found := shutil.which("ollama"):
        logger.debug("detect_ollama_binary: PATH search hit -> %s", found)
        return Path(found)

    # Priority 4: not found
    logger.warning("detect_ollama_binary: binário não encontrado em nenhuma priority")
    return None


# ── Phase A.3 — Lockfile (concurrent app prevention) ──────────────────────


def acquire_app_lock() -> int:
    """Adquire lockfile non-blocking para prevenir múltiplas instâncias do app.

    Implementa EC-11 (concurrent app instances) — usa ``fcntl.flock`` em
    Linux/Mac e ``msvcrt.locking`` em Windows. Lock é exclusivo e non-blocking;
    se outra instância já adquiriu, raise ``AppAlreadyRunning``.

    O file descriptor retornado deve ser fechado no shutdown via ``os.close(fd)``
    para liberar o lock automaticamente.

    Returns:
        File descriptor do lockfile (caller responsável por fechar).

    Raises:
        AppAlreadyRunning: se outra instância já tem o lock.
        OSError: se não foi possível abrir o lockfile (permissions, etc).
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(LOCK_FILE), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        logger.debug("acquire_app_lock: lock acquired (fd=%d, file=%s)", fd, LOCK_FILE)
        return fd
    except (BlockingIOError, OSError) as exc:
        os.close(fd)
        raise AppAlreadyRunning(
            f"App já rodando em outra instância (lockfile: {LOCK_FILE})"
        ) from exc


def release_app_lock(fd: int) -> None:
    """Libera o lockfile fechando o file descriptor.

    Idempotente — fechar fd já fechado é silenciosamente ignorado.
    """
    try:
        os.close(fd)
        logger.debug("release_app_lock: fd=%d fechado", fd)
    except OSError:
        # fd já fechado OR inválido — silenciosamente OK em shutdown
        pass


# ── Phase A.4 — Orphan cleanup (PRÓXIMA SESSÃO) ───────────────────────────


def cleanup_orphans_on_startup() -> None:
    """Limpa processos Ollama órfãos do mesmo usuário não rastreados em PID file.

    Implementa EC-06 (app crash mid-startup deixou processos pendentes).
    Estratégia: ``psutil.process_iter()`` filtra processos cujo nome é
    ``ollama``/``ollama.exe`` do usuário atual. Se PID não está no PID file
    (via ``read_pid_file_safely()``), considera órfão e termina via SIGTERM
    com timeout 5s + fallback SIGKILL.

    Idempotente — se não há órfãos, nenhuma ação é tomada (logger apenas).
    Falhas individuais (NoSuchProcess, AccessDenied) são silenciosamente
    ignoradas para tornar o startup robusto a estados parciais do sistema.
    """
    import psutil

    target_names = {"ollama", "ollama.exe"}

    try:
        current_user = psutil.Process().username()
    except psutil.Error as exc:
        logger.warning("cleanup_orphans_on_startup: não foi possível obter user atual: %s", exc)
        return

    tracked_pids = set(read_pid_file_safely().values())

    orphans_killed = 0
    for proc in psutil.process_iter(["name", "username", "pid"]):
        try:
            info = proc.info
            name = (info.get("name") or "").lower()
            if name not in target_names:
                continue
            if info.get("username") != current_user:
                continue
            if info.get("pid") in tracked_pids:
                continue  # rastreado em PID file — não é órfão

            # Processo é órfão: tenta SIGTERM, fallback SIGKILL
            pid = info["pid"]
            try:
                proc.terminate()
                proc.wait(timeout=5)
                logger.info("cleanup_orphans_on_startup: SIGTERM PID=%d", pid)
                orphans_killed += 1
            except psutil.TimeoutExpired:
                try:
                    proc.kill()
                    proc.wait(timeout=2)
                    logger.info("cleanup_orphans_on_startup: SIGKILL fallback PID=%d", pid)
                    orphans_killed += 1
                except psutil.Error as exc:
                    logger.warning(
                        "cleanup_orphans_on_startup: SIGKILL falhou PID=%d: %s", pid, exc
                    )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if orphans_killed:
        logger.info("cleanup_orphans_on_startup: %d processos órfãos terminados", orphans_killed)
    else:
        logger.debug("cleanup_orphans_on_startup: 0 órfãos encontrados")


# ── Phase B — Spawn + PID management (PRÓXIMAS SESSÕES) ───────────────────


def _wait_for_ollama_ready(host: str, port: int, timeout: float = 30.0) -> bool:
    """Aguarda Ollama responder em ``http://{host}:{port}/api/tags`` por até ``timeout`` segundos.

    Polling síncrono (~1s entre tentativas). Usado por ``spawn_ollama()`` após
    Popen para garantir que processo ficou up antes de retornar PID.

    Args:
        host: hostname.
        port: porta TCP.
        timeout: segundos máximos de espera.

    Returns:
        True se Ollama respondeu (status < 500) dentro do timeout, False caso contrário.
    """
    import time

    import httpx

    deadline = time.monotonic() + timeout
    url = f"http://{host}:{port}/api/tags"

    while time.monotonic() < deadline:
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(url)
                if resp.status_code < 500:
                    return True
        except httpx.HTTPError:
            pass
        time.sleep(1.0)

    return False


def spawn_ollama(binary: Path, host: str, port: int, log_file: Path | None = None) -> int:
    """Spawna nova instância Ollama em (host, port) via subprocess.Popen.

    Per ADR-011: ``OLLAMA_HOST`` env var + ``creationflags`` Windows-specific
    + redirect stdout/stderr para log file + ``_wait_for_ollama_ready(timeout=30)``.

    Args:
        binary: Path para o binário Ollama (de ``detect_ollama_binary()``).
        host: hostname para bind (default ``127.0.0.1``).
        port: porta TCP para listening.
        log_file: arquivo opcional para redirecionar stdout/stderr
            (default ``DATA_DIR/.ollama-{port}.log``).

    Returns:
        PID do processo spawned.

    Raises:
        OllamaSpawnFailed: se processo spawned não ficou ready em 30s.
    """
    import subprocess  # noqa: S404 — necessário para spawn Ollama

    if log_file is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        log_file = DATA_DIR / f".ollama-{port}.log"
    else:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["OLLAMA_HOST"] = f"{host}:{port}"

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]

    log_fh = log_file.open("ab")  # append binary

    try:
        process = subprocess.Popen(  # noqa: S603 — binary path validado em detect_ollama_binary
            [str(binary), "serve"],
            env=env,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )
    except OSError as exc:
        log_fh.close()
        raise OllamaSpawnFailed(
            f"subprocess.Popen falhou para {binary} {host}:{port}: {exc}"
        ) from exc

    if not _wait_for_ollama_ready(host, port, timeout=30.0):
        try:
            process.terminate()
            process.wait(timeout=5)
        except (subprocess.TimeoutExpired, OSError):
            try:
                process.kill()
            except OSError:
                pass
        log_fh.close()
        raise OllamaSpawnFailed(
            f"Ollama spawned em {host}:{port} (PID={process.pid}) mas não ficou ready em 30s"
        )

    logger.info(
        "spawn_ollama: PID=%d ready em %s:%d (log: %s)", process.pid, host, port, log_file
    )
    return process.pid


def kill_spawned_ollama() -> None:
    """Termina processos Ollama listados no PID file via SIGTERM/SIGKILL.

    Per ADR-011 EC-12: usa ``process_is_ours()`` para verificar name antes de
    matar (mitigação PID reuse race — sistema pode ter reusado o PID para outro
    processo do mesmo usuário). Cleanup PID file ao final.

    Idempotente — se PID file não existe, retorna silenciosamente.
    """
    import psutil

    pids_dict = read_pid_file_safely()
    if not pids_dict:
        logger.debug("kill_spawned_ollama: PID file vazio — nada a terminar")
        return

    for role, pid in pids_dict.items():
        if not process_is_ours(pid):
            logger.warning(
                "kill_spawned_ollama: PID=%d (%s) não é Ollama deste user "
                "— possível PID reuse, skip",
                pid,
                role,
            )
            continue

        try:
            proc = psutil.Process(pid)
            proc.terminate()
            try:
                proc.wait(timeout=5)
                logger.info("kill_spawned_ollama: SIGTERM OK PID=%d (%s)", pid, role)
            except psutil.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
                logger.info("kill_spawned_ollama: SIGKILL fallback PID=%d (%s)", pid, role)
        except psutil.NoSuchProcess:
            logger.debug("kill_spawned_ollama: PID=%d (%s) já não existe", pid, role)
        except psutil.AccessDenied as exc:
            logger.warning(
                "kill_spawned_ollama: AccessDenied PID=%d (%s): %s", pid, role, exc
            )

    # Cleanup PID file
    try:
        PID_FILE.unlink()
        logger.debug("kill_spawned_ollama: PID file %s removido", PID_FILE)
    except FileNotFoundError:
        pass
    except OSError as exc:
        logger.warning("kill_spawned_ollama: falha removendo PID file: %s", exc)


def write_pid_file_atomic(pids: dict[str, int]) -> None:
    """Escreve PID file atomicamente (temp + ``os.replace`` POSIX atomic).

    Schema JSON v1.0::

        {
          "schema_version": "1.0",
          "spawned_by_app_pid": <pid>,
          "spawned_at": "<isoformat UTC>",
          "instances": [
            {"role": "advogado", "pid": <pid>, "host": "127.0.0.1", "port": 11434},
            {"role": "economista", "pid": <pid>, "host": "127.0.0.1", "port": 11435}
          ]
        }

    Args:
        pids: mapping role → PID (ex: ``{"advogado": 12345, "economista": 12346}``).
            Roles esperados: ``advogado`` (port 11434) e ``economista`` (port 11435).
            Outros roles recebem port = ``DEFAULT_PORT_ECONOMISTA`` por convenção.
    """
    import json
    from datetime import UTC, datetime

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp = PID_FILE.with_suffix(".tmp")

    instances = []
    for role, pid in pids.items():
        port = DEFAULT_PORT_ADVOGADO if role == "advogado" else DEFAULT_PORT_ECONOMISTA
        instances.append({"role": role, "pid": pid, "host": DEFAULT_HOST, "port": port})

    payload = {
        "schema_version": PID_FILE_SCHEMA_VERSION,
        "spawned_by_app_pid": os.getpid(),
        "spawned_at": datetime.now(UTC).isoformat(),
        "instances": instances,
    }

    temp.write_text(json.dumps(payload, indent=2))
    os.replace(str(temp), str(PID_FILE))
    logger.debug("write_pid_file_atomic: %s (instances=%d)", PID_FILE, len(instances))


def read_pid_file_safely() -> dict[str, int]:
    """Lê PID file retornando dict vazio se missing OR corrupto OR schema inválido.

    Não levanta exceção — defensive read para tornar ``cleanup_orphans_on_startup``
    e ``kill_spawned_ollama`` idempotentes em qualquer estado do sistema.

    Returns:
        Mapping role → PID (ex: ``{"advogado": 123, "economista": 124}``).
        Vazio se arquivo missing, JSON corrupto, schema incompatível, OR estrutura
        de ``instances`` inválida.
    """
    import json

    try:
        raw = PID_FILE.read_text()
    except FileNotFoundError:
        return {}
    except OSError as exc:
        logger.warning("read_pid_file_safely: erro leitura %s: %s", PID_FILE, exc)
        return {}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("read_pid_file_safely: JSON corrupto em %s: %s", PID_FILE, exc)
        return {}

    schema = data.get("schema_version") if isinstance(data, dict) else None
    if schema != PID_FILE_SCHEMA_VERSION:
        logger.warning(
            "read_pid_file_safely: schema_version incompatível (%s != %s) — ignorando",
            schema,
            PID_FILE_SCHEMA_VERSION,
        )
        return {}

    instances = data.get("instances", [])
    if not isinstance(instances, list):
        return {}

    result: dict[str, int] = {}
    for inst in instances:
        try:
            role = inst["role"]
            pid = int(inst["pid"])
            result[role] = pid
        except (KeyError, TypeError, ValueError):
            continue

    return result


# ── Phase C — Detection helpers (PRÓXIMA SESSÃO) ──────────────────────────


async def detect_running_ollama(host: str, port: int) -> bool:
    """Verifica se há Ollama rodando e responsivo em (host, port).

    Usa ``httpx`` async para GET ``http://{host}:{port}/api/tags`` com timeout
    curto. Status < 500 = running (incluindo 200 normal e 4xx que ainda indicam
    server alive); HTTPError ou timeout = down. Não distingue Ollama desktop de
    instância spawned pela app — ambos são REUSE candidates per ADR-011 §detect-then-spawn.

    Args:
        host: hostname (tipicamente ``127.0.0.1``).
        port: porta TCP (tipicamente 11434 ou 11435).

    Returns:
        True se Ollama responsivo (status < 500), False em qualquer falha de rede.
    """
    import httpx

    url = f"http://{host}:{port}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(url)
            return resp.status_code < 500
    except httpx.HTTPError:
        return False


# ── Phase D — Auto-pull + health (PRÓXIMAS SESSÕES) ───────────────────────


def _parse_ollama_list_output(stdout: str) -> set[str]:
    """Parse output do ``ollama list`` extraindo nomes de modelos instalados.

    Formato típico do output (header + linhas tabulares)::

        NAME                ID              SIZE      MODIFIED
        qwen2.5:7b          abc123          4.7 GB    2 days ago
        qwen2.5:3b          def456          1.9 GB    3 days ago

    Args:
        stdout: output stdout do comando ``ollama list``.

    Returns:
        Set de nomes de modelos (primeira coluna). Linhas vazias e header ignorados.
    """
    installed: set[str] = set()
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.upper().startswith("NAME"):
            continue  # skip header
        # Primeira coluna até primeiro espaço/tab
        parts = line.split()
        if parts:
            installed.add(parts[0])
    return installed


async def _pull_one_model(model: str) -> None:
    """Executa ``ollama pull <model>`` e atualiza ``_pull_status`` durante o download.

    Lê stdout linha por linha, regex extrai percent + eta, atualiza state global
    via ``_pull_lock``. Wait final do subprocess; raise OSError se exit code ≠ 0.

    Args:
        model: nome do modelo (ex: ``"qwen2.5:7b"``).

    Raises:
        OSError: se subprocess fail (exit code ≠ 0 OR não pode iniciar).
    """
    proc = await asyncio.create_subprocess_exec(
        "ollama",
        "pull",
        model,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    last_percent = -1
    if proc.stdout is None:
        await proc.wait()
        if proc.returncode != 0:
            raise OSError(f"ollama pull {model} exit={proc.returncode}")
        return

    while True:
        line_bytes = await proc.stdout.readline()
        if not line_bytes:
            break
        line = line_bytes.decode(errors="replace")

        # Parse percent
        m_pct = _PERCENT_RE.search(line)
        if m_pct:
            percent = int(m_pct.group(1))
            # Update apenas se mudou ≥5% (evita spam de updates)
            if percent - last_percent >= 5 or percent == 100:
                last_percent = percent
                eta_sec: int | None = None
                m_eta = _ETA_RE.search(line)
                if m_eta:
                    minutes = int(m_eta.group(1))
                    seconds = int(m_eta.group(2)) if m_eta.group(2) else 0
                    eta_sec = minutes * 60 + seconds
                async with _pull_lock:
                    _pull_status.update(
                        {
                            "state": "pulling",
                            "model": model,
                            "percent": percent,
                            "eta_seconds": eta_sec,
                        }
                    )

    await proc.wait()
    if proc.returncode != 0:
        raise OSError(f"ollama pull {model} exit={proc.returncode}")


async def ensure_models_pulled(required: list[str]) -> None:
    """Verifica e baixa modelos Ollama faltantes (background-friendly).

    Per ADR-011: chama ``ollama list`` parsing → identifica missing →
    ``pre_check_disk_space(MIN_DISK_SPACE_GB)`` → ``ollama pull`` async com parse
    de stdout para progresso → atualiza ``_pull_status`` global thread-safe.
    Retry 3x exponential backoff (1s/2s/4s) em network errors (EC-05).

    Projetada para rodar em ``asyncio.create_task()`` no lifespan startup —
    não bloqueia a app subir; UI banner + endpoint SSE mostram progresso.

    Args:
        required: lista de modelos esperados (ex: ``["qwen2.5:7b", "qwen2.5:3b"]``).

    Note:
        Não levanta exceções para o caller — falhas são registradas em
        ``_pull_status["state"] = "error"`` para serem visíveis via SSE/banner.
    """
    # Identifica missing via `ollama list`
    try:
        list_proc = await asyncio.create_subprocess_exec(
            "ollama",
            "list",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, _stderr = await list_proc.communicate()
    except OSError as exc:
        logger.exception("ensure_models_pulled: ollama list failed: %s", exc)
        async with _pull_lock:
            _pull_status.update(
                {
                    "state": "error",
                    "model": None,
                    "percent": 0,
                    "eta_seconds": 0,
                    "error": f"ollama list falhou: {exc}",
                }
            )
        return

    installed = _parse_ollama_list_output(stdout_bytes.decode(errors="replace"))
    missing = [m for m in required if m not in installed]

    if not missing:
        async with _pull_lock:
            _pull_status.update(
                {"state": "ready", "model": None, "percent": 100, "eta_seconds": 0}
            )
        logger.info("ensure_models_pulled: all required já instalados (%s)", required)
        return

    # Pre-check disk space ANTES de iniciar pulls (EC-04)
    try:
        pre_check_disk_space(MIN_DISK_SPACE_GB)
    except DiskSpaceInsufficient as exc:
        async with _pull_lock:
            _pull_status.update(
                {
                    "state": "error",
                    "model": None,
                    "percent": 0,
                    "eta_seconds": 0,
                    "error": str(exc),
                }
            )
        logger.exception("ensure_models_pulled: disk space insufficient")
        return

    # Pull cada missing com retry 3x exponential backoff (EC-05)
    for model in missing:
        async with _pull_lock:
            _pull_status.update(
                {"state": "pulling", "model": model, "percent": 0, "eta_seconds": None}
            )
        success = False
        for attempt in range(3):
            try:
                await _pull_one_model(model)
                success = True
                break
            except OSError as exc:
                wait = 2**attempt  # 1, 2, 4 segundos
                logger.warning(
                    "ensure_models_pulled: pull %s falhou (attempt %d/3): %s — retry em %ds",
                    model,
                    attempt + 1,
                    exc,
                    wait,
                )
                await asyncio.sleep(wait)
        if not success:
            async with _pull_lock:
                _pull_status.update(
                    {
                        "state": "error",
                        "model": model,
                        "percent": 0,
                        "eta_seconds": 0,
                        "error": f"pull {model} falhou após 3 tentativas",
                    }
                )
            logger.error("ensure_models_pulled: %s falhou 3 attempts — abort", model)
            return

    # Todos pulled com sucesso
    async with _pull_lock:
        _pull_status.update(
            {"state": "ready", "model": None, "percent": 100, "eta_seconds": 0}
        )
    logger.info("ensure_models_pulled: complete — %d modelos baixados", len(missing))


def get_pull_status() -> dict[str, object]:
    """Retorna snapshot do ``_pull_status`` global para SSE endpoint /ollama-status.

    Schema::

        {
          "state": "pulling" | "ready" | "error",
          "model": str | None,        # modelo atual sendo baixado
          "percent": int (0-100),     # progresso atual
          "eta_seconds": int | None,  # estimado tempo restante
          "error": str (opcional, apenas se state="error")
        }

    Returns:
        Cópia defensiva do estado (Lock não necessário em read).
    """
    return dict(_pull_status)


def is_ready() -> bool:
    """True se ``_pull_status.state == "ready"``.

    Usado em ``/revisar`` para retornar 503 retry-after enquanto auto-pull rodando.
    """
    return _pull_status.get("state") == "ready"


# ── Phase E — On-demand health check (PRÓXIMAS SESSÕES) ───────────────────


def process_is_ours(pid: int) -> bool:
    """Verifica se PID corresponde a processo Ollama do usuário atual.

    Mitigação EC-12 (PID reuse race) — antes de matar processo via PID,
    confirma que ainda é o processo Ollama que spawnamos (sistema reusa PIDs
    rapidamente em Linux/Mac). Cross-platform (aceita ``ollama`` e ``ollama.exe``).

    Args:
        pid: PID a verificar.

    Returns:
        True se ``psutil.Process(pid)`` reporta name=ollama|ollama.exe E
        username igual ao usuário atual; False se processo não existe,
        foi reusado para outro programa, ou AccessDenied.
    """
    import psutil

    target_names = {"ollama", "ollama.exe"}

    try:
        proc = psutil.Process(pid)
        name = proc.name().lower()
        if name not in target_names:
            return False
        if proc.username() != psutil.Process().username():
            return False
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def pre_check_disk_space(min_gb: float = MIN_DISK_SPACE_GB) -> None:
    """Verifica espaço em disco suficiente antes de auto-pull de modelos.

    Mitigação EC-04 (disco cheio durante pull). Usa ``shutil.disk_usage``
    no DATA_DIR e raise ``DiskSpaceInsufficient`` se livre < ``min_gb``.

    Args:
        min_gb: mínimo de GB livres exigido (default 7.0 = qwen 7b 4.7GB
            + qwen 3b 1.9GB + buffer 0.4GB).

    Raises:
        DiskSpaceInsufficient: se livre < min_gb.

    TODO Phase D.1:
        - shutil.disk_usage(DATA_DIR).free / 1024**3 < min_gb → raise
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(DATA_DIR)
    free_gb = usage.free / (1024**3)
    if free_gb < min_gb:
        raise DiskSpaceInsufficient(
            f"Espaço em disco insuficiente para baixar modelos: "
            f"{free_gb:.2f}GB livres em {DATA_DIR}, mínimo exigido {min_gb:.2f}GB. "
            f"Libere espaço em ~/.local/share/revisor-contratual/ e re-execute."
        )


# ── Public API ────────────────────────────────────────────────────────────


__all__ = [
    # Constants
    "DATA_DIR",
    "PID_FILE",
    "LOCK_FILE",
    "DEFAULT_HOST",
    "DEFAULT_PORT_ADVOGADO",
    "DEFAULT_PORT_ECONOMISTA",
    "REQUIRED_MODELS",
    "MIN_DISK_SPACE_GB",
    # Exceptions
    "OllamaBinaryNotFound",
    "OllamaSpawnFailed",
    "AppAlreadyRunning",
    "DiskSpaceInsufficient",
    # Phase A — implementadas
    "detect_ollama_binary",
    "acquire_app_lock",
    "release_app_lock",
    "cleanup_orphans_on_startup",  # stub Phase A.4
    "pre_check_disk_space",
    # Phase B — stubs
    "spawn_ollama",
    "kill_spawned_ollama",
    "write_pid_file_atomic",
    "read_pid_file_safely",
    "process_is_ours",
    # Phase C — stubs
    "detect_running_ollama",
    # Phase D — stubs
    "ensure_models_pulled",
    "get_pull_status",
    "is_ready",
]
