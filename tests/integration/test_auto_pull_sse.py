"""Integration tests for OLLAMA-MGR-01 Phase D — auto-pull SSE + 503 retry-after.

Cobertura:
- AC-6 ensure_models_pulled (no-op + disk insufficient)
- AC-6 endpoint SSE /ollama-status (events stream correctos)
- AC-8 503 retry-after em /revisar quando is_ready=False

Sessão 90 (CC.6 Phase D).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_ensure_models_pulled_no_op() -> None:
    """ollama list retorna required → state=ready imediato sem pull."""
    from bloco_interface import ollama_manager

    sample_output = (
        b"NAME                ID              SIZE      MODIFIED\n"
        b"qwen2.5:7b          abc123          4.7 GB    2 days ago\n"
        b"qwen2.5:3b          def456          1.9 GB    3 days ago\n"
    )
    proc_mock = MagicMock()
    proc_mock.communicate = AsyncMock(return_value=(sample_output, b""))

    with patch(
        "bloco_interface.ollama_manager.asyncio.create_subprocess_exec",
        AsyncMock(return_value=proc_mock),
    ):
        asyncio.run(ollama_manager.ensure_models_pulled(["qwen2.5:7b", "qwen2.5:3b"]))

    assert ollama_manager.is_ready() is True


@pytest.mark.integration
def test_ensure_models_pulled_disk_insufficient(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Disk usage low + missing models → state=error sem iniciar pull."""
    from bloco_interface import ollama_manager

    monkeypatch.setattr("bloco_interface.ollama_manager.DATA_DIR", tmp_path)

    # Mock ollama list retornando vazio (todos missing)
    sample_output = b"NAME                ID              SIZE      MODIFIED\n"
    proc_mock = MagicMock()
    proc_mock.communicate = AsyncMock(return_value=(sample_output, b""))

    fake_usage = MagicMock()
    fake_usage.free = 1 * 1024**3  # 1GB livre (< 7GB threshold)

    try:
        with patch(
            "bloco_interface.ollama_manager.asyncio.create_subprocess_exec",
            AsyncMock(return_value=proc_mock),
        ), patch("shutil.disk_usage", return_value=fake_usage):
            asyncio.run(ollama_manager.ensure_models_pulled(["qwen2.5:7b"]))

        status = ollama_manager.get_pull_status()
        assert status["state"] == "error"
    finally:
        # Restaurar state default para não afetar outros tests
        ollama_manager._pull_status.update(
            {"state": "ready", "model": None, "percent": 100, "eta_seconds": 0}
        )


def _common_lifespan_mocks() -> dict[str, object]:
    """Helper: dict de patches comuns para mockar lifespan startup completo."""
    return {
        "bloco_interface.web.app.ollama_manager.acquire_app_lock": 42,
        "bloco_interface.web.app.ollama_manager.cleanup_orphans_on_startup": None,
        "bloco_interface.web.app.ollama_manager.detect_ollama_binary": MagicMock(name="binary"),
        "bloco_interface.web.app.populate_vault_if_needed": {
            "populated": False,
            "skipped_reason": "test",
        },
    }


@pytest.mark.integration
def test_ollama_status_sse_endpoint() -> None:
    """GET /ollama-status retorna SSE stream com event 'status' contendo state=ready."""
    fake_status = {"state": "ready", "model": None, "percent": 100, "eta_seconds": 0}

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
        "bloco_interface.web.app.ollama_manager.get_pull_status",
        return_value=fake_status,
    ):
        from bloco_interface.web.app import app

        with TestClient(app) as client:
            response = client.get("/ollama-status")
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            # Primeiro event "status" emitido + state=ready → loop break
            assert "event: status" in response.text
            assert '"state": "ready"' in response.text


@pytest.mark.integration
def test_revisar_503_when_not_ready() -> None:
    """POST /revisar retorna 503 quando is_ready=False (modelos baixando)."""
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
        "bloco_interface.web.app.ollama_manager.is_ready",
        return_value=False,  # AC-8: 503 quando não ready
    ):
        from bloco_interface.web.app import app

        with TestClient(app) as client:
            # POST com PDF dummy — early 503 check dispara antes da validação MIME
            response = client.post(
                "/revisar",
                files={"pdf": ("test.pdf", b"%PDF-1.4 fake content")},
                data={"tier": "balanced"},
            )
            # Espera 503 (HTTPException → custom handler renderiza error.html)
            assert response.status_code == 503
