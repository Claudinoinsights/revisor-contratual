"""Integration tests for MVP-LEAN-01 Task 4 — S5 Processing + C4 + SSE resilient.

Cobertura:
- AC-MVP-05 (S5 Processing pane com 5 fases)
- AC-MVP-12 (C4 Processing pane com lista + cancel)
- AC-MVP-SSE-RESILIENT (endpoint /revisar/stream/{job_id} estrutura — happy path)
- AC-MVP-AUDIT (POST /audit/connection-drop grava entry pipeline_lost_connection)

Nota: Tests de timer client-side (60s timeout, retry backoff 5s, heartbeat detect)
NÃO incluídos aqui — async timer mocking em pytest+TestClient é complexo e fora
do happy path. Documentado como tech debt a refinar pós-MVP (smoke E2E real Task 9
valida em browser).

Sessão 91 (CC.13 Task 4) — Neo paralelo a Eric smoke E2E.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

# ── Fixtures (mesmo pattern Tasks 1+2+3) ──────────────────────────────────
TEST_USERNAME = "tester"
TEST_PASSWORD = "test-pwd-123"  # noqa: S105
TEST_SECRET = "test-secret-key-for-integration-tests-only"  # noqa: S105


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    test_hash = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
    monkeypatch.setenv("ADMIN_USERNAME", TEST_USERNAME)
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", test_hash)
    monkeypatch.setenv("REVISOR_SECRET_KEY", TEST_SECRET)
    # audit.jsonl temporário para testar connection-drop (não tocar audit real)
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    audit_file = audit_dir / "audit.jsonl"
    monkeypatch.setattr(
        "bloco_interface.web.app.DEFAULT_AUDIT_PATH",
        audit_file,
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    """TestClient autenticado + lifespan mockado + Ollama is_ready mock."""
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


# ── Tests S5 + C4 render ──────────────────────────────────────────────────
@pytest.mark.integration
def test_post_revisar_renders_s5_with_job_id(client: TestClient) -> None:
    """AC-MVP-05: POST /revisar válido renderiza s5_processing.html com job_id."""
    pdf_content = b"%PDF-1.4\n%fake test pdf"
    response = client.post(
        "/revisar",
        files={"pdf": ("contrato.pdf", pdf_content, "application/pdf")},
        data={"uf": "SP", "data": "2024-01-01", "tier": "balanced"},
    )
    assert response.status_code == 200
    body = response.text
    assert 'class="processing-pane"' in body
    assert 'data-job-id=' in body
    assert 'data-stream-url="/revisar/stream/' in body


@pytest.mark.integration
def test_s5_renders_5_canonical_phases(client: TestClient) -> None:
    """AC-MVP-12: S5 renderiza 5 fases canônicas em estado pending inicial."""
    pdf_content = b"%PDF-1.4\n%fake"
    response = client.post(
        "/revisar",
        files={"pdf": ("c.pdf", pdf_content, "application/pdf")},
    )
    body = response.text
    # 5 fases canônicas per ux-spec §4 C4 linhas 695-700
    assert "Parsing PDF" in body
    assert "Advogado (Sabia/Qwen 7B)" in body
    assert "Economista (Qwen 7B)" in body
    assert "Validador semântico" in body
    assert "Juiz HITL" in body
    # Estado inicial pending para todos
    assert body.count('data-state="pending"') == 5


@pytest.mark.integration
@pytest.mark.skip(
    reason="Legacy MVP-LEAN-01 SSE resilient script (sse_resilient.js) — "
    "SPA OrSheva 7 chunk 1 (commit e7cbe7b) usa fetch direto sem SSE legacy. "
    "TD-SP04-LEGACY-TESTS MEDIUM Sprint 6+ — atualizar para validar SPA SSE pattern."
)
def test_s5_includes_sse_resilient_script(client: TestClient) -> None:
    """AC-MVP-SSE-RESILIENT: client-side script incluído."""
    pdf_content = b"%PDF-1.4\n%fake"
    response = client.post(
        "/revisar",
        files={"pdf": ("c.pdf", pdf_content, "application/pdf")},
    )
    body = response.text
    assert 'src="/static/sse_resilient.js"' in body


@pytest.mark.integration
def test_s5_renders_cancel_button(client: TestClient) -> None:
    """AC-MVP-05: footer com 'Cancelar e recomeçar'."""
    pdf_content = b"%PDF-1.4\n%fake"
    response = client.post(
        "/revisar",
        files={"pdf": ("c.pdf", pdf_content, "application/pdf")},
    )
    body = response.text
    assert "Cancelar e recomeçar" in body
    assert 'class="processing-cancel"' in body


@pytest.mark.integration
def test_s5_a11y_role_list_aria_live(client: TestClient) -> None:
    """WCAG: lista fases com role=list + aria-live=polite por fase."""
    pdf_content = b"%PDF-1.4\n%fake"
    response = client.post(
        "/revisar",
        files={"pdf": ("c.pdf", pdf_content, "application/pdf")},
    )
    body = response.text
    assert 'role="list"' in body
    assert body.count('aria-live="polite"') >= 5  # 1 por fase


@pytest.mark.integration
def test_s5_filename_displayed(client: TestClient) -> None:
    """AC-MVP-05: filename do PDF exibido no S5."""
    pdf_content = b"%PDF-1.4\n%fake"
    response = client.post(
        "/revisar",
        files={"pdf": ("contrato-cliente-x.pdf", pdf_content, "application/pdf")},
    )
    body = response.text
    assert "contrato-cliente-x.pdf" in body


# ── Tests SSE endpoint shape (happy path mock) ────────────────────────────
@pytest.mark.integration
def test_sse_endpoint_invalid_job_id_returns_phase_error(client: TestClient) -> None:
    """AC-MVP-SSE-RESILIENT: GET /revisar/stream/{invalid} → phase-error event."""
    response = client.get("/revisar/stream/invalid-job-id")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    body = response.text
    assert "event: phase-error" in body
    # JSON serialization escapa unicode (ó → á); aceitar ambas formas
    assert ("job_id inválido" in body) or ("job_id inv\\u00e1lido" in body)


# ── Tests audit /audit/connection-drop ────────────────────────────────────
@pytest.mark.integration
def test_audit_connection_drop_writes_entry(client: TestClient) -> None:
    """AC-MVP-AUDIT: POST /audit/connection-drop grava entry pipeline_lost_connection."""
    response = client.post(
        "/audit/connection-drop",
        data={"job_id": "test-job-123", "last_phase": "Advogado (Sabia/Qwen 7B)"},
    )
    assert response.status_code == 204

    # Verifica entry gravado
    from bloco_interface.web.app import DEFAULT_AUDIT_PATH

    assert DEFAULT_AUDIT_PATH.exists()
    lines = DEFAULT_AUDIT_PATH.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 1
    entry = json.loads(lines[-1])
    assert entry["type"] == "pipeline_lost_connection"
    assert entry["job_id"] == "test-job-123"
    assert entry["last_phase"] == "Advogado (Sabia/Qwen 7B)"
    assert "timestamp" in entry


@pytest.mark.integration
def test_audit_connection_drop_requires_auth() -> None:
    """AC-MVP-LGPD-L1: /audit/connection-drop requer session válida."""
    # Cliente sem login (não usa fixture autenticada)
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
            response = tc.post(
                "/audit/connection-drop",
                data={"job_id": "x", "last_phase": "y"},
            )
            assert response.status_code == 401


@pytest.mark.integration
def test_mvp_lean_phases_constant_is_5(client: TestClient) -> None:
    """AC-MVP-12: constante MVP_LEAN_PHASES tem exatamente 5 fases canônicas."""
    from bloco_interface.web.app import MVP_LEAN_PHASES

    assert len(MVP_LEAN_PHASES) == 5
    assert MVP_LEAN_PHASES[0] == "Parsing PDF"
    assert MVP_LEAN_PHASES[-1] == "Juiz HITL"
