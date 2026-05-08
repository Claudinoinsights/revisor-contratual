"""Integration tests for MVP-LEAN-01 Task 7 — S8 Banner CRITICAL + state file + ack endpoint.

Cobertura:
- AC-MVP-08 (S8 Banner CRITICAL Tema 1378 com main desabilitado)
- AC-MVP-10 (state file persiste estado tema_1378)
- AC-MVP-MONITOR (auto-trigger 2 fails consecutivas → CRITICAL + ack downgrade)

Sessão 91 (CC.18 Task 7) — Neo Trilha 3 paralelo.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

from bloco_dataset import tema_1378_state

TEST_USERNAME = "tester"
TEST_PASSWORD = "test-pwd-123"  # noqa: S105
TEST_SECRET = "test-secret-key-for-integration-tests-only"  # noqa: S105


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    test_hash = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
    monkeypatch.setenv("ADMIN_USERNAME", TEST_USERNAME)
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", test_hash)
    monkeypatch.setenv("REVISOR_SECRET_KEY", TEST_SECRET)
    # State file isolado em tmp_path (não tocar real do user)
    monkeypatch.setenv("REVISOR_DATA_DIR", str(tmp_path))
    # Audit também isolado
    audit_file = tmp_path / "audit.jsonl"
    monkeypatch.setattr(
        "bloco_interface.web.app.DEFAULT_AUDIT_PATH",
        audit_file,
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    """TestClient autenticado + lifespan mockado."""
    with patch(
        "bloco_interface.web.app.ollama_manager.acquire_app_lock", return_value=42
    ), patch(
        "bloco_interface.web.app.ollama_manager.cleanup_orphans_on_startup"
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_ollama_binary",
        return_value=MagicMock(),
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_running_ollama",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "bloco_interface.web.app.ollama_manager.spawn_ollama"
    ), patch(
        "bloco_interface.web.app.ollama_manager.write_pid_file_atomic"
    ), patch(
        "bloco_interface.web.app.ollama_manager.kill_spawned_ollama"
    ), patch(
        "bloco_interface.web.app.ollama_manager.release_app_lock"
    ), patch(
        "bloco_interface.web.app.ollama_manager.is_ready",
        return_value=True,
    ), patch(
        "bloco_interface.web.app.populate_vault_if_needed"
    ), patch(
        "bloco_interface.web.app.ollama_manager.ensure_models_pulled",
        new_callable=AsyncMock,
    ):
        from bloco_interface.web.app import app

        with TestClient(app) as tc:
            login_page = tc.get("/login")
            csrf_marker = 'name="csrf_token" value="'
            start = login_page.text.find(csrf_marker) + len(csrf_marker)
            end = login_page.text.find('"', start)
            csrf_token = login_page.text[start:end]
            tc.post(
                "/login",
                data={
                    "username": TEST_USERNAME,
                    "password": TEST_PASSWORD,
                    "csrf_token": csrf_token,
                },
            )
            yield tc


# ── Tests state file API ──────────────────────────────────────────────────
@pytest.mark.integration
def test_state_file_default_verde() -> None:
    """get_current sem file → DEFAULT_STATE (verde)."""
    state = tema_1378_state.get_current()
    assert state["nivel"] == "verde"
    assert state["fail_count"] == 0


@pytest.mark.integration
def test_increment_fail_once_amarelo() -> None:
    """1 fail → state amarelo + fail_count=1."""
    count = tema_1378_state.increment_fail()
    assert count == 1
    state = tema_1378_state.get_current()
    assert state["nivel"] == "amarelo"
    assert state["fail_count"] == 1
    assert "verificação automática falhou" in state["mensagem"]


@pytest.mark.integration
def test_increment_fail_twice_critical() -> None:
    """2 fails consecutivas → auto-trigger vermelho (CRITICAL)."""
    tema_1378_state.increment_fail()  # fail #1 → amarelo
    count = tema_1378_state.increment_fail()  # fail #2 → vermelho
    assert count == 2
    state = tema_1378_state.get_current()
    assert state["nivel"] == "vermelho"
    assert state["fail_count"] == 2
    assert "ALERTA CRÍTICO" in state["mensagem"]
    assert "2 execuções consecutivas" in state["mensagem"]


@pytest.mark.integration
def test_set_state_atomic_write(tmp_path: Path) -> None:
    """Atomic write: tmp file + os.replace (não corrompe em crash mid-write)."""
    new_state = tema_1378_state.set_state(
        nivel="verde",
        mensagem="test message",
    )
    assert new_state["nivel"] == "verde"
    assert new_state["mensagem"] == "test message"

    # Verificar que arquivo existe e é JSON válido
    state_path = tmp_path / "tema_1378_status.json"
    assert state_path.exists()
    loaded = json.loads(state_path.read_text(encoding="utf-8"))
    assert loaded["nivel"] == "verde"


@pytest.mark.integration
def test_set_state_invalid_nivel_raises() -> None:
    """nivel inválido → ValueError."""
    with pytest.raises(ValueError, match="nivel inválido"):
        tema_1378_state.set_state(nivel="laranja", mensagem="x")


@pytest.mark.integration
def test_acknowledge_idempotent_when_not_red() -> None:
    """Ack em estado não-vermelho é no-op (idempotente)."""
    state_before = tema_1378_state.get_current()
    assert state_before["nivel"] == "verde"
    state_after = tema_1378_state.acknowledge()
    assert state_after["nivel"] == "verde"  # não muda


@pytest.mark.integration
def test_acknowledge_downgrades_red_to_yellow(tmp_path: Path) -> None:
    """Ack em VERMELHO → AMARELO + audit entry tema_1378_acknowledge."""
    # Trigger CRITICAL
    tema_1378_state.increment_fail()
    tema_1378_state.increment_fail()
    assert tema_1378_state.get_current()["nivel"] == "vermelho"

    # Ack
    audit_path = tmp_path / "audit.jsonl"
    new_state = tema_1378_state.acknowledge(audit_path=audit_path)
    assert new_state["nivel"] == "amarelo"

    # Verifica audit entry
    assert audit_path.exists()
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    entry = json.loads(lines[-1])
    assert entry["type"] == "tema_1378_acknowledge"
    assert entry["previous_nivel"] == "vermelho"
    assert entry["new_nivel"] == "amarelo"


# ── Tests render banner + main_disabled ───────────────────────────────────
@pytest.mark.integration
def test_main_funcional_quando_verde(client: TestClient) -> None:
    """Verde default: main NÃO tem class .main-disabled."""
    response = client.get("/")
    body = response.text
    assert 'class="container"' in body
    assert "main-disabled" not in body
    # Banner verde renderizado
    assert "banner-tema-1378--verde" in body


@pytest.mark.integration
def test_main_disabled_when_vermelho(client: TestClient) -> None:
    """Banner vermelho → main com class .main-disabled + aria-disabled."""
    # Trigger CRITICAL via state file
    tema_1378_state.increment_fail()
    tema_1378_state.increment_fail()

    response = client.get("/")
    body = response.text
    assert "main-disabled" in body
    assert 'aria-disabled="true"' in body
    assert 'data-testid="main-disabled"' in body
    assert "banner-tema-1378--vermelho" in body
    assert "ALERTA CRÍTICO" in body


@pytest.mark.integration
def test_main_funcional_quando_amarelo(client: TestClient) -> None:
    """Banner amarelo (1 fail): main NÃO disabled (apenas warning visível)."""
    tema_1378_state.increment_fail()  # fail #1 → amarelo

    response = client.get("/")
    body = response.text
    assert "main-disabled" not in body
    assert "banner-tema-1378--amarelo" in body


# ── Tests POST /monitor-tema/acknowledge endpoint ─────────────────────────
@pytest.mark.integration
def test_post_acknowledge_downgrades_to_amarelo(
    client: TestClient,
    tmp_path: Path,
) -> None:
    """POST /monitor-tema/acknowledge → state vermelho → amarelo + HX-Redirect."""
    # Trigger CRITICAL
    tema_1378_state.increment_fail()
    tema_1378_state.increment_fail()

    response = client.post("/monitor-tema/acknowledge")
    assert response.status_code == 200
    assert response.headers.get("hx-redirect") == "/"
    assert response.headers.get("x-tema-1378-nivel") == "amarelo"

    # Verifica state file mudou
    state = tema_1378_state.get_current()
    assert state["nivel"] == "amarelo"

    # Verifica audit entry
    audit_path = tmp_path / "audit.jsonl"
    assert audit_path.exists()
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    assert any('"type": "tema_1378_acknowledge"' in line for line in lines)


@pytest.mark.integration
def test_post_acknowledge_requires_auth() -> None:
    """POST /monitor-tema/acknowledge sem session → 401."""
    with patch(
        "bloco_interface.web.app.ollama_manager.acquire_app_lock", return_value=42
    ), patch(
        "bloco_interface.web.app.ollama_manager.cleanup_orphans_on_startup"
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_ollama_binary",
        return_value=MagicMock(),
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_running_ollama",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "bloco_interface.web.app.ollama_manager.spawn_ollama"
    ), patch(
        "bloco_interface.web.app.ollama_manager.write_pid_file_atomic"
    ), patch(
        "bloco_interface.web.app.ollama_manager.kill_spawned_ollama"
    ), patch(
        "bloco_interface.web.app.ollama_manager.release_app_lock"
    ), patch(
        "bloco_interface.web.app.populate_vault_if_needed"
    ), patch(
        "bloco_interface.web.app.ollama_manager.ensure_models_pulled",
        new_callable=AsyncMock,
    ):
        from bloco_interface.web.app import app

        with TestClient(app) as tc:
            response = tc.post("/monitor-tema/acknowledge")
            assert response.status_code == 401


@pytest.mark.integration
def test_reset_to_verde_zera_fail_count() -> None:
    """reset_to_verde: nivel=verde + fail_count=0 (Camada 1 OK Task 8)."""
    tema_1378_state.increment_fail()
    tema_1378_state.increment_fail()
    state = tema_1378_state.get_current()
    assert state["nivel"] == "vermelho"

    new_state = tema_1378_state.reset_to_verde()
    assert new_state["nivel"] == "verde"
    assert new_state["fail_count"] == 0
