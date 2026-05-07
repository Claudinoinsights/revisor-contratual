"""Integration tests for MVP-LEAN-01 Task 1 — Layout-base + estrutura HTMX swap.

Cobertura:
- AC-MVP-09 (estrutura layout): topbar + banner Tema 1378 + main + footer renderizam
- AC-MVP-15 (footer C7): versão + audit.jsonl link + LGPD disclaimer
- AC-MVP-LGPD-L1 (banner Tema 1378 persistente): 3 níveis renderizam corretamente
- POST /logout retorna HX-Redirect para /login
- main tem id="app-main" + aria-live="polite" para HTMX swap

Sessão 91 (CC.10 Task 1) — Neo paralelo a Eric smoke E2E.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

# Task 2 instalou auth — tests de layout_base agora precisam autenticar antes de GET /
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
    """TestClient com lifespan mockado + login automático (Task 2 protege GET /)."""
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
        "bloco_interface.web.app.populate_vault_if_needed"
    ), patch(
        "bloco_interface.web.app.ollama_manager.ensure_models_pulled",
        new_callable=AsyncMock,
    ):
        from bloco_interface.web.app import app

        with TestClient(app) as tc:
            # Login automático (Task 2 protege GET /)
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


@pytest.mark.integration
def test_get_root_renders_topbar(client: TestClient) -> None:
    """AC-MVP-09: topbar renderiza com mark + brand."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert '<header class="topbar"' in body
    assert "Revisor Contratual" in body
    assert 'aria-label="Barra de navegação principal"' in body


@pytest.mark.integration
def test_get_root_renders_main_with_app_main_id(client: TestClient) -> None:
    """AC-MVP-09: <main id='app-main' aria-live='polite'> para HTMX swap."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert 'id="app-main"' in body
    assert 'aria-live="polite"' in body


@pytest.mark.integration
def test_get_root_renders_banner_tema_1378_default_verde(client: TestClient) -> None:
    """AC-MVP-LGPD-L1: banner Tema 1378 nível verde (default) renderiza."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert "banner-tema-1378" in body
    assert "banner-tema-1378--verde" in body
    assert "Tema 1378 STJ" in body
    assert 'role="status"' in body  # verde/amarelo = status


@pytest.mark.integration
def test_get_root_renders_footer_c7(client: TestClient) -> None:
    """AC-MVP-15: footer C7 com versão + audit.jsonl + LGPD disclaimer."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert 'class="footer-c7"' in body
    assert "audit.jsonl" in body
    assert "/audit.jsonl" in body
    assert "100% local" in body
    assert "LGPD" in body


@pytest.mark.integration
def test_get_root_footer_has_app_version(client: TestClient) -> None:
    """AC-MVP-15: footer mostra versão dinâmica (lida de pyproject.toml)."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    # APP_VERSION começa com "v" + semver OR fallback
    assert "Revisor Contratual v" in body


@pytest.mark.integration
def test_post_logout_returns_hx_redirect(client: TestClient) -> None:
    """AC-MVP-LGPD-L1: POST /logout retorna 200 + header HX-Redirect=/login."""
    response = client.post("/logout")
    assert response.status_code == 200
    assert response.headers.get("hx-redirect") == "/login"


@pytest.mark.integration
def test_main_aria_label_present(client: TestClient) -> None:
    """WCAG AA: main tem aria-label semântico."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert 'aria-label="Área principal de conteúdo"' in body


@pytest.mark.integration
def test_footer_aria_label_present(client: TestClient) -> None:
    """WCAG AA: footer tem aria-label semântico."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert 'aria-label="Rodapé com versão e disclaimers"' in body
