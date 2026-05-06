"""Integration tests for MVP-LEAN-01 Task 6 — S7 Error pane + C6 catch-all + 7 variantes.

Cobertura:
- AC-MVP-04 (S4 Validation error reuso C6)
- AC-MVP-07 (S7 Pipeline error pane)
- AC-MVP-14 (C6 component parametrizado)
- AC-MVP-ERRORS (8 variantes catalogadas — 7 específicas + 1 catch-all infra_unknown)

Padrão obrigatório SOP-003: Diagnóstico → Causa → Solução → Alternativa.
Anti-pattern proibido: mensagem genérica violando os 4 campos.

Sessão 91 (CC.17 Task 6) — Neo Trilha 3 paralelo.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import httpx
import pytest
from fastapi.testclient import TestClient

from bloco_interface.web import error_handler

TEST_USERNAME = "tester"
TEST_PASSWORD = "test-pwd-123"  # noqa: S105
TEST_SECRET = "test-secret-key-for-integration-tests-only"  # noqa: S105


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    test_hash = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
    monkeypatch.setenv("ADMIN_USERNAME", TEST_USERNAME)
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", test_hash)
    monkeypatch.setenv("REVISOR_SECRET_KEY", TEST_SECRET)


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


# ── Tests classify_exception (unit-style — 9 variantes mapping) ───────────
@pytest.mark.integration
def test_disk_full_audit_classify_correct() -> None:
    """OSError errno=28 com 'audit' na message → disk_full_audit."""
    exc = OSError(28, "No space left on device", "audit.jsonl")
    assert error_handler.classify_exception(exc) == "disk_full_audit"


@pytest.mark.integration
def test_disk_full_uploads_classify_correct() -> None:
    """OSError errno=28 com 'uploads' na message → disk_full_uploads."""
    exc = OSError(28, "No space left on device writing uploads/foo.pdf", "uploads/foo.pdf")
    assert error_handler.classify_exception(exc) == "disk_full_uploads"


@pytest.mark.integration
def test_vault_db_locked_classify_correct() -> None:
    """sqlite3.OperationalError com 'locked' → vault_db_locked."""
    exc = sqlite3.OperationalError("database is locked")
    assert error_handler.classify_exception(exc) == "vault_db_locked"


@pytest.mark.integration
def test_fernet_key_missing_classify_correct() -> None:
    """InvalidToken (cryptography.fernet) → fernet_key_missing."""
    # Não importar cryptography no test (dep extra) — simular via class name match
    class InvalidToken(Exception):  # noqa: N818
        pass

    exc = InvalidToken("invalid token")
    assert error_handler.classify_exception(exc) == "fernet_key_missing"


@pytest.mark.integration
def test_session_secret_missing_classify_correct() -> None:
    """RuntimeError com 'session_secret' → session_secret_missing."""
    exc = RuntimeError("SESSION_SECRET ausente em .env")
    assert error_handler.classify_exception(exc) == "session_secret_missing"


@pytest.mark.integration
def test_ollama_subprocess_crash_classify_correct() -> None:
    """OllamaProcessNotResponding (class name) → ollama_subprocess_crash."""
    class OllamaProcessNotResponding(Exception):
        pass

    exc = OllamaProcessNotResponding("subprocess died")
    assert error_handler.classify_exception(exc) == "ollama_subprocess_crash"


@pytest.mark.integration
def test_bacen_api_down_classify_correct() -> None:
    """httpx.TimeoutException com URL bacen → bacen_api_down."""
    exc = httpx.TimeoutException("Request to https://api.bacen.gov.br/sgs timed out")
    assert error_handler.classify_exception(exc) == "bacen_api_down"


@pytest.mark.integration
def test_weasyprint_render_fail_classify_correct() -> None:
    """weasyprint.RenderError → weasyprint_render_fail (simulado por module name)."""
    # weasyprint não está nas deps de test — simular module via class
    weasyprint_render_error = type(
        "RenderError",
        (Exception,),
        {"__module__": "weasyprint.error"},
    )
    exc = weasyprint_render_error("Cannot render table")
    assert error_handler.classify_exception(exc) == "weasyprint_render_fail"


@pytest.mark.integration
def test_unknown_exception_falls_back_to_infra_unknown() -> None:
    """ValueError genérica → infra_unknown (catch-all)."""
    exc = ValueError("custom error not mapped")
    assert error_handler.classify_exception(exc) == "infra_unknown"


# ── Tests get_c6_payload ──────────────────────────────────────────────────
@pytest.mark.integration
def test_get_c6_payload_includes_microcopy_diagnostico() -> None:
    """Payload tem 6 campos esperados (titulo + 4 SOP-003 + acoes)."""
    payload = error_handler.get_c6_payload("disk_full_audit")
    assert payload["titulo"] == "Não foi possível registrar a auditoria"
    assert payload["diagnostico"] == "Sem espaço em disco para gravar a auditoria"
    assert "OSError [Errno 28]" in payload["causa"]
    assert "Liberar espaço" in payload["solucao"]
    assert "Backup do audit.jsonl" in payload["alternativa"]
    assert isinstance(payload["acoes"], list)
    assert len(payload["acoes"]) == 2


@pytest.mark.integration
def test_get_c6_payload_infra_unknown_enriches_with_exception() -> None:
    """Para infra_unknown, payload inclui dados da exception (per ux-spec linhas 776-779)."""
    exc = ValueError("custom message line 1\nline 2")
    payload = error_handler.get_c6_payload("infra_unknown", exc=exc, job_id="job-abc-123")
    assert "ValueError" in payload["diagnostico"]
    assert "custom message line 1" in payload["diagnostico"]
    assert "ValueError" in payload["causa"]
    assert "job-abc-123" in payload["alternativa"]


# ── Tests render S7 via HTTPException ─────────────────────────────────────
@pytest.mark.integration
def test_c6_macro_renders_4_canonical_sections(client: TestClient) -> None:
    """C6 renderiza 4 sections: Diagnóstico/Causa/Solução/Alternativa."""
    # Disparar 413 (file too large) via POST /revisar com PDF gigante
    huge_pdf = b"%PDF-1.4\n" + b"x" * (11 * 1024 * 1024)  # 11MB > MAX_UPLOAD_SIZE
    response = client.post(
        "/revisar",
        files={"pdf": ("huge.pdf", huge_pdf, "application/pdf")},
    )
    assert response.status_code == 413
    body = response.text
    assert 'data-testid="c6-error-pane"' in body
    assert 'data-testid="c6-diagnostico"' in body
    assert 'data-testid="c6-causa"' in body
    assert 'data-testid="c6-solucao"' in body
    assert 'data-testid="c6-alternativa"' in body
    # Padrão SOP-003: 4 headings canônicos
    assert "Diagnóstico" in body
    assert "Causa" in body
    assert "Solução" in body
    assert "Alternativa" in body


@pytest.mark.integration
def test_s7_renders_role_alert_aria_assertive(client: TestClient) -> None:
    """S7/C6 tem role='alert' + aria-live='assertive' (a11y SR interruption)."""
    huge_pdf = b"%PDF-1.4\n" + b"x" * (11 * 1024 * 1024)
    response = client.post(
        "/revisar",
        files={"pdf": ("h.pdf", huge_pdf, "application/pdf")},
    )
    body = response.text
    assert 'role="alert"' in body
    assert 'aria-live="assertive"' in body


@pytest.mark.integration
def test_s7_renders_actions_buttons(client: TestClient) -> None:
    """C6 actions bar tem 2 botões default (Tentar novamente + Ver log audit)."""
    huge_pdf = b"%PDF-1.4\n" + b"x" * (11 * 1024 * 1024)
    response = client.post(
        "/revisar",
        files={"pdf": ("h.pdf", huge_pdf, "application/pdf")},
    )
    body = response.text
    assert "Tentar novamente" in body
    assert "Ver log audit" in body
    assert 'data-testid="c6-acao-reset"' in body
    assert 'data-testid="c6-acao-audit"' in body


@pytest.mark.integration
def test_s7_invalid_pdf_renders_c6(client: TestClient) -> None:
    """POST /revisar com bytes inválidos (não-PDF) → 400 + S7 com C6."""
    invalid = b"not a pdf at all"
    response = client.post(
        "/revisar",
        files={"pdf": ("fake.pdf", invalid, "application/pdf")},
    )
    assert response.status_code == 400
    body = response.text
    assert 'data-testid="c6-error-pane"' in body


@pytest.mark.integration
def test_variants_dict_has_9_entries() -> None:
    """VARIANTS tem 9 entries: catch-all infra_unknown + 8 específicas (per ux-spec §4 C6)."""
    expected_keys = {
        "infra_unknown",
        "disk_full_audit",
        "disk_full_uploads",
        "vault_db_locked",
        "fernet_key_missing",
        "session_secret_missing",
        "ollama_subprocess_crash",
        "bacen_api_down",
        "weasyprint_render_fail",
    }
    assert set(error_handler.VARIANTS.keys()) == expected_keys
    assert len(error_handler.VARIANTS) == 9


@pytest.mark.integration
def test_all_variants_have_4_sop003_fields() -> None:
    """Cada variante segue SOP-003: 4 campos obrigatórios + titulo."""
    required_fields = {"titulo", "diagnostico", "causa", "solucao", "alternativa"}
    for variant_key, variant_data in error_handler.VARIANTS.items():
        missing = required_fields - set(variant_data.keys())
        assert not missing, f"{variant_key} faltando campos: {missing}"
