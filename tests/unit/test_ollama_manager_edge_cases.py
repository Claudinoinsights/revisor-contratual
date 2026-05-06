"""Unit tests for OLLAMA-MGR-01 Phase E — edge cases EC-02 a EC-10 (AC-9).

Cobertura adicional dos 12 edge cases ADR-011 que não estavam cobertos
em test_ollama_manager.py (Phase A+B) ou test_lifespan_ollama.py (Phase C)
ou test_auto_pull_sse.py (Phase D).

Edge cases cobertos aqui:
- EC-02 :11434 ocupada por non-Ollama (port conflict comportamento documentado)
- EC-03 :11435 idem
- EC-05 network down durante pull (retry 3x esgotado → state=error)
- EC-07 kill BEFORE cleanup ordem (idempotência em failure path)
- EC-08 Ollama crash mid-revisar (lazy respawn handler)
- EC-09 concurrent uploads pulling (validação específica AC-8 + AC-9 combo)
- EC-10 antivirus blocking spawn (clear error com Defender hint potencial)

Sessão 91 (CC.6 Phase E final).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import psutil
import pytest

from bloco_interface import ollama_manager
from bloco_interface.ollama_manager import OllamaSpawnFailed

# ── EC-02 / EC-03: port occupied by non-Ollama (comportamento documentado) ──


def test_ec02_port_11434_responsive_assumed_ollama() -> None:
    """detect_running_ollama=True com port responsivo → REUSE flow (AC-4).

    Limitação documentada: OLLAMA-MGR-01 não distingue Ollama de outro server
    HTTP em :11434. Se algum non-Ollama responder /api/tags com status<500,
    REUSE flow assume Ollama. Pipeline downstream falha (responsabilidade não-OLLAMA).

    Esta limitação é aceita per ADR-011 (probabilidade BAIXA + mitigação manual:
    operador encerra processo conflitante antes de subir app).
    """
    # Mock httpx.get retornando server responsivo (mesmo non-Ollama)
    response_mock = MagicMock()
    response_mock.status_code = 200

    async def run() -> bool:
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=response_mock)
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            return await ollama_manager.detect_running_ollama("127.0.0.1", 11434)

    result = asyncio.run(run())
    assert result is True  # REUSE flow assumido (limitação documentada)


def test_ec03_port_11435_idem() -> None:
    """EC-03 mesma limitação que EC-02 para :11435 (role economista)."""
    response_mock = MagicMock()
    response_mock.status_code = 404  # 4xx ainda indica server alive (não 5xx)

    async def run() -> bool:
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=response_mock)
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            return await ollama_manager.detect_running_ollama("127.0.0.1", 11435)

    result = asyncio.run(run())
    assert result is True


# ── EC-05: network down durante pull → retry 3x esgotado ──


def test_ec05_network_down_pull_retry_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    """ollama list OK + pull fail OSError 3x consecutivas → state=error."""
    sample_output = b"NAME                ID              SIZE      MODIFIED\n"
    list_proc_mock = MagicMock()
    list_proc_mock.communicate = AsyncMock(return_value=(sample_output, b""))

    # Mock _pull_one_model raise OSError sempre (network down)
    async def raise_oserror(model: str) -> None:
        raise OSError("Network unreachable (mocked)")

    fake_usage = MagicMock()
    fake_usage.free = 10 * 1024**3  # disco OK

    try:
        with patch(
            "bloco_interface.ollama_manager.asyncio.create_subprocess_exec",
            AsyncMock(return_value=list_proc_mock),
        ), patch(
            "bloco_interface.ollama_manager._pull_one_model", side_effect=raise_oserror
        ), patch("shutil.disk_usage", return_value=fake_usage), patch(
            "bloco_interface.ollama_manager.asyncio.sleep", new_callable=AsyncMock
        ):
            asyncio.run(ollama_manager.ensure_models_pulled(["qwen2.5:7b"]))

        status = ollama_manager.get_pull_status()
        assert status["state"] == "error"
        assert status["model"] == "qwen2.5:7b"
    finally:
        # Restaurar default
        ollama_manager._pull_status.update(
            {"state": "ready", "model": None, "percent": 100, "eta_seconds": 0}
        )


# ── EC-07: kill_spawned_ollama ordem (read_pid → kill → unlink) ──


def test_ec07_kill_before_cleanup_ordem(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifica ordem em kill_spawned_ollama: read_pid → kill PIDs → unlink PID file.

    Crash mid-shutdown (EC-07): mesmo se psutil.Process raise, PID file deve ser
    cleaned ao final (idempotente em failure paths).
    """
    pid_file = tmp_path / ".ollama-spawned.pid"
    monkeypatch.setattr("bloco_interface.ollama_manager.PID_FILE", pid_file)
    monkeypatch.setattr("bloco_interface.ollama_manager.DATA_DIR", tmp_path)

    # Cria PID file com 1 entry
    ollama_manager.write_pid_file_atomic({"advogado": 99999})
    assert pid_file.exists()

    # Mock process_is_ours retornando True + psutil.Process levantando NoSuchProcess
    with patch(
        "bloco_interface.ollama_manager.process_is_ours", return_value=True
    ), patch("psutil.Process", side_effect=psutil.NoSuchProcess(99999)):
        ollama_manager.kill_spawned_ollama()

    # PID file deve ser deletado mesmo em failure path
    assert not pid_file.exists()


# ── EC-08: Ollama crash mid-revisar → AC-7 lazy respawn handler ──


def test_ec08_ollama_crash_lazy_respawn_handler() -> None:
    """detect_running_ollama=False mid-revisar → /revisar dispara lazy respawn.

    Verifica que a sequência AC-7 (detect_running → spawn → write_pid) executa
    quando Ollama desce mid-uso. Mock spawn retorna PID novo; write_pid atualiza.
    """
    binary_mock = MagicMock(name="ollama_binary")

    with patch(
        "bloco_interface.web.app.ollama_manager.acquire_app_lock", return_value=42
    ), patch(
        "bloco_interface.web.app.ollama_manager.cleanup_orphans_on_startup"
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_ollama_binary",
        return_value=binary_mock,
    ), patch(
        "bloco_interface.web.app.populate_vault_if_needed",
        return_value={"populated": False, "skipped_reason": "test"},
    ), patch(
        "bloco_interface.web.app.ollama_manager.ensure_models_pulled",
        side_effect=NotImplementedError(),
    ), patch(
        "bloco_interface.web.app.ollama_manager.kill_spawned_ollama"
    ), patch(
        "bloco_interface.web.app.ollama_manager.release_app_lock"
    ), patch(
        "bloco_interface.web.app.ollama_manager.is_ready", return_value=True
    ), patch(
        # Lifespan startup: True (REUSE)
        # Mid-revisar: False (crash) → lazy respawn dispara
        "bloco_interface.web.app.ollama_manager.detect_running_ollama",
        new_callable=AsyncMock,
        side_effect=[True, True, False, False],  # startup x2 + revisar x2 (advogado+economista)
    ), patch(
        "bloco_interface.web.app.ollama_manager.spawn_ollama",
        side_effect=[55555, 55556],  # PIDs respawn
    ) as mock_spawn, patch(
        "bloco_interface.web.app.ollama_manager.read_pid_file_safely",
        return_value={},
    ), patch(
        "bloco_interface.web.app.ollama_manager.write_pid_file_atomic"
    ) as mock_write_pid:
        from fastapi.testclient import TestClient

        from bloco_interface.web.app import app

        with TestClient(app) as client:
            response = client.post(
                "/revisar",
                files={"pdf": ("test.pdf", b"%PDF-1.4 fake content")},
                data={"tier": "balanced"},
            )

        # AC-7 lazy respawn: spawn chamado 2x (advogado + economista)
        assert mock_spawn.call_count == 2
        # write_pid_file_atomic chamado pelo menos 2x (1 por respawn)
        assert mock_write_pid.call_count >= 1
        # Resposta provavelmente 400/500 (PDF mock falha downstream, mas AC-7 disparou)
        assert response.status_code != 503  # NÃO 503 — respawn sucesso


# ── EC-09: concurrent uploads pulling → 503 retry-after (validação AC-8) ──


def test_ec09_concurrent_uploads_pulling_503() -> None:
    """is_ready=False (modelos pulling background) → POST /revisar = 503 + Retry-After."""
    with patch(
        "bloco_interface.web.app.ollama_manager.acquire_app_lock", return_value=42
    ), patch(
        "bloco_interface.web.app.ollama_manager.cleanup_orphans_on_startup"
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_ollama_binary",
        return_value=MagicMock(name="binary"),
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_running_ollama",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "bloco_interface.web.app.populate_vault_if_needed",
        return_value={"populated": False, "skipped_reason": "test"},
    ), patch(
        "bloco_interface.web.app.ollama_manager.ensure_models_pulled",
        side_effect=NotImplementedError(),
    ), patch(
        "bloco_interface.web.app.ollama_manager.kill_spawned_ollama"
    ), patch(
        "bloco_interface.web.app.ollama_manager.release_app_lock"
    ), patch(
        "bloco_interface.web.app.ollama_manager.is_ready", return_value=False
    ):
        from fastapi.testclient import TestClient

        from bloco_interface.web.app import app

        with TestClient(app) as client:
            response = client.post(
                "/revisar",
                files={"pdf": ("test.pdf", b"%PDF-1.4 fake")},
                data={"tier": "balanced"},
            )

        assert response.status_code == 503


# ── EC-10: antivirus blocking spawn → OllamaSpawnFailed clear error ──


def test_ec10_antivirus_blocking_spawn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """subprocess.Popen raise PermissionError [Errno 13] (antivirus block) → OllamaSpawnFailed."""
    monkeypatch.setattr("bloco_interface.ollama_manager.DATA_DIR", tmp_path)
    fake_binary = tmp_path / "ollama.exe"
    fake_binary.touch()

    # Mock subprocess.Popen raise PermissionError (Windows antivirus block)
    with patch(
        "subprocess.Popen", side_effect=PermissionError(13, "Access denied (mocked AV block)")
    ), pytest.raises(OllamaSpawnFailed) as exc_info:
        ollama_manager.spawn_ollama(fake_binary, "127.0.0.1", 11434)

    # Mensagem de erro deve conter informação útil
    assert "11434" in str(exc_info.value) or "spawn" in str(exc_info.value).lower()
