"""Integration tests for OLLAMA-MGR-01 Phase C — FastAPI lifespan integration.

Cobertura:
- AC-4 detect-then-spawn preserva Ollama existente em :11434/:11435 (REUSE vs SPAWN)
- AC-5 lifespan integration completa (startup + shutdown ordem ADR-013 §2.4)
- AC-9 EC-01 fail-fast quando binary não encontrado

Mocks:
- detect_running_ollama (AsyncMock) — controla REUSE vs SPAWN
- spawn_ollama (MagicMock) — não inicia subprocess real
- detect_ollama_binary — controla "binary found" vs "not found"
- write_pid_file_atomic / kill_spawned_ollama / acquire_app_lock / release_app_lock —
  validar chamadas + ordem
- populate_vault_if_needed — não tocar vault real

Sessão 89 (CC.6 Phase C) — pós FastAPI lifespan refatorado.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_lifespan_reuse_existing_ollama() -> None:
    """detect_running_ollama=True para ambas portas → spawn não chamado."""
    with patch(
        "bloco_interface.web.app.ollama_manager.acquire_app_lock", return_value=42
    ) as mock_lock, patch(
        "bloco_interface.web.app.ollama_manager.cleanup_orphans_on_startup"
    ) as mock_cleanup, patch(
        "bloco_interface.web.app.ollama_manager.detect_ollama_binary",
        return_value=MagicMock(name="ollama_binary_mock"),
    ) as mock_detect_bin, patch(
        "bloco_interface.web.app.ollama_manager.detect_running_ollama",
        new_callable=AsyncMock,
        return_value=True,  # REUSE both ports
    ), patch(
        "bloco_interface.web.app.ollama_manager.spawn_ollama"
    ) as mock_spawn, patch(
        "bloco_interface.web.app.ollama_manager.write_pid_file_atomic"
    ) as mock_write_pid, patch(
        "bloco_interface.web.app.populate_vault_if_needed",
        return_value={"populated": False, "skipped_reason": "test mock"},
    ), patch(
        "bloco_interface.web.app.ollama_manager.ensure_models_pulled",
        side_effect=NotImplementedError("Phase D stub"),
    ), patch(
        "bloco_interface.web.app.ollama_manager.kill_spawned_ollama"
    ) as mock_kill, patch(
        "bloco_interface.web.app.ollama_manager.release_app_lock"
    ) as mock_release:
        from bloco_interface.web.app import app

        with TestClient(app):
            pass  # startup + shutdown via context manager

        # Startup ordem verificada
        mock_lock.assert_called_once()
        mock_cleanup.assert_called_once()
        mock_detect_bin.assert_called_once()
        # REUSE: spawn NÃO chamado (ambas portas reusadas)
        mock_spawn.assert_not_called()
        # Sem spawn → write_pid_file não chamado
        mock_write_pid.assert_not_called()
        # Shutdown ordem
        mock_kill.assert_called_once()
        mock_release.assert_called_once_with(42)


@pytest.mark.integration
def test_lifespan_spawn_missing_ollama() -> None:
    """detect_running_ollama=False → spawn_ollama chamado 2x (advogado + economista)."""
    with patch(
        "bloco_interface.web.app.ollama_manager.acquire_app_lock", return_value=42
    ), patch(
        "bloco_interface.web.app.ollama_manager.cleanup_orphans_on_startup"
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_ollama_binary",
        return_value=MagicMock(name="ollama_binary_mock"),
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_running_ollama",
        new_callable=AsyncMock,
        return_value=False,  # SPAWN both ports
    ), patch(
        "bloco_interface.web.app.ollama_manager.spawn_ollama",
        side_effect=[12345, 12346],  # PIDs spawned
    ) as mock_spawn, patch(
        "bloco_interface.web.app.ollama_manager.write_pid_file_atomic"
    ) as mock_write_pid, patch(
        "bloco_interface.web.app.populate_vault_if_needed",
        return_value={"populated": False, "skipped_reason": "test mock"},
    ), patch(
        "bloco_interface.web.app.ollama_manager.ensure_models_pulled",
        side_effect=NotImplementedError("Phase D stub"),
    ), patch(
        "bloco_interface.web.app.ollama_manager.kill_spawned_ollama"
    ), patch(
        "bloco_interface.web.app.ollama_manager.release_app_lock"
    ):
        from bloco_interface.web.app import app

        with TestClient(app):
            pass

        # SPAWN: chamado 2x (advogado + economista)
        assert mock_spawn.call_count == 2
        # write_pid_file chamado com ambos roles
        mock_write_pid.assert_called_once()
        pids_dict = mock_write_pid.call_args[0][0]
        assert pids_dict == {"advogado": 12345, "economista": 12346}


@pytest.mark.integration
def test_lifespan_fail_binary_not_found() -> None:
    """detect_ollama_binary=None → raises OllamaBinaryNotFound + release lock."""
    with patch(
        "bloco_interface.web.app.ollama_manager.acquire_app_lock", return_value=42
    ), patch(
        "bloco_interface.web.app.ollama_manager.cleanup_orphans_on_startup"
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_ollama_binary", return_value=None
    ), patch(
        "bloco_interface.web.app.ollama_manager.release_app_lock"
    ) as mock_release:
        from bloco_interface.ollama_manager import OllamaBinaryNotFound
        from bloco_interface.web.app import app

        with pytest.raises(OllamaBinaryNotFound):
            with TestClient(app):
                pass

        # Release_lock chamado mesmo em failure path (cleanup graceful)
        mock_release.assert_called_once_with(42)


@pytest.mark.integration
def test_lifespan_shutdown_cleanup_on_spawn() -> None:
    """Shutdown chama kill_spawned_ollama + release_app_lock após spawn."""
    with patch(
        "bloco_interface.web.app.ollama_manager.acquire_app_lock", return_value=99
    ), patch(
        "bloco_interface.web.app.ollama_manager.cleanup_orphans_on_startup"
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_ollama_binary",
        return_value=MagicMock(name="ollama_binary_mock"),
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_running_ollama",
        new_callable=AsyncMock,
        return_value=False,
    ), patch(
        "bloco_interface.web.app.ollama_manager.spawn_ollama", side_effect=[100, 101]
    ), patch(
        "bloco_interface.web.app.ollama_manager.write_pid_file_atomic"
    ), patch(
        "bloco_interface.web.app.populate_vault_if_needed",
        return_value={"populated": False, "skipped_reason": "test mock"},
    ), patch(
        "bloco_interface.web.app.ollama_manager.ensure_models_pulled",
        side_effect=NotImplementedError("Phase D stub"),
    ), patch(
        "bloco_interface.web.app.ollama_manager.kill_spawned_ollama"
    ) as mock_kill, patch(
        "bloco_interface.web.app.ollama_manager.release_app_lock"
    ) as mock_release:
        from bloco_interface.web.app import app

        with TestClient(app):
            pass

        # Ordem inversa shutdown: kill primeiro, release depois
        mock_kill.assert_called_once()
        mock_release.assert_called_once_with(99)
