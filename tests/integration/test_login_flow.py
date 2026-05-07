"""Integration tests for MVP-LEAN-01 Task 2 — S1 Login + C1 Login form.

Cobertura:
- AC-MVP-01 (S1 Login): GET /login renderiza form + CSRF; rota / protegida
- AC-MVP-09 (C1 component): form fields + autofocus + aria-live error
- AC-MVP-LGPD-L1 (auth defense-in-depth): bcrypt verify + anti-enumeration + CSRF custom

Sessão 91 (CC.11 Task 2) — Neo paralelo a Eric smoke E2E.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

# ── Fixtures ──────────────────────────────────────────────────────────────
TEST_USERNAME = "tester"
TEST_PASSWORD = "test-pwd-123"  # noqa: S105
TEST_SECRET = "test-secret-key-for-integration-tests-only"  # noqa: S105


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set env vars de auth para testes (bcrypt hash gerado runtime)."""
    test_hash = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
    monkeypatch.setenv("ADMIN_USERNAME", TEST_USERNAME)
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", test_hash)
    monkeypatch.setenv("REVISOR_SECRET_KEY", TEST_SECRET)


@pytest.fixture
def client() -> Iterator[TestClient]:
    """TestClient com lifespan mockado (não spawna Ollama real)."""
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
            yield tc


# ── Tests ─────────────────────────────────────────────────────────────────
@pytest.mark.integration
def test_get_login_renders_s1_form(client: TestClient) -> None:
    """AC-MVP-01: GET /login renderiza form + CSRF hidden + heading Fraunces."""
    response = client.get("/login")
    assert response.status_code == 200
    body = response.text
    assert 'name="csrf_token"' in body
    assert 'name="username"' in body
    assert 'name="password"' in body
    assert "Revisor Contratual" in body
    assert 'autofocus' in body  # AC-MVP-01: autofocus em Usuário
    assert "Entrar" in body  # PT-BR (não "Login")


@pytest.mark.integration
def test_get_login_omits_banner_tema_1378_pre_auth(client: TestClient) -> None:
    """ux-spec §3 S1: banner Tema 1378 NÃO renderiza pré-auth (LGPD coerência)."""
    response = client.get("/login")
    body = response.text
    # Banner suprimido via tema_1378.nivel="oculto" no context
    assert "banner-tema-1378" not in body


@pytest.mark.integration
def test_get_login_omits_topbar_user_pre_auth(client: TestClient) -> None:
    """ux-spec §3 S1: topbar SEM nome usuário pré-auth."""
    response = client.get("/login")
    body = response.text
    assert "topbar-user" not in body
    assert "topbar-logout" not in body


@pytest.mark.integration
def test_post_login_success_returns_hx_redirect(client: TestClient) -> None:
    """AC-MVP-01: credenciais válidas → 200 + HX-Redirect=/"""
    csrf_response = client.get("/login")
    csrf_token = _extract_csrf(csrf_response.text)
    response = client.post(
        "/login",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "csrf_token": csrf_token,
        },
    )
    assert response.status_code == 200
    assert response.headers.get("hx-redirect") == "/"


@pytest.mark.integration
def test_post_login_wrong_password_generic_error(client: TestClient) -> None:
    """AC-MVP-LGPD-L1: senha errada → 401 + mensagem genérica."""
    csrf_response = client.get("/login")
    csrf_token = _extract_csrf(csrf_response.text)
    response = client.post(
        "/login",
        data={
            "username": TEST_USERNAME,
            "password": "senha-errada",
            "csrf_token": csrf_token,
        },
    )
    assert response.status_code == 401
    assert "Usuário ou senha inválidos" in response.text


@pytest.mark.integration
def test_post_login_wrong_username_same_generic_error(client: TestClient) -> None:
    """AC-MVP-LGPD-L1 anti-enumeration: username errado → MESMA mensagem genérica."""
    csrf_response = client.get("/login")
    csrf_token = _extract_csrf(csrf_response.text)
    response = client.post(
        "/login",
        data={
            "username": "nao-existe",
            "password": TEST_PASSWORD,
            "csrf_token": csrf_token,
        },
    )
    assert response.status_code == 401
    assert "Usuário ou senha inválidos" in response.text


@pytest.mark.integration
def test_post_login_invalid_csrf_returns_403(client: TestClient) -> None:
    """AC-MVP-LGPD-L1: CSRF mismatch → 403 'Sessão expirada'."""
    client.get("/login")  # gera CSRF na session
    response = client.post(
        "/login",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "csrf_token": "csrf-token-invalido",
        },
    )
    assert response.status_code == 403
    assert "Sessão expirada" in response.text


@pytest.mark.integration
def test_get_root_redirects_to_login_if_unauthenticated(client: TestClient) -> None:
    """AC-MVP-01: GET / sem session → 303 redirect /login."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers.get("location") == "/login"


@pytest.mark.integration
def test_post_logout_clears_session_then_root_redirects(client: TestClient) -> None:
    """Integração Task 1+2: logout limpa session, GET / volta a redirecionar."""
    # 1) Login
    csrf_response = client.get("/login")
    csrf_token = _extract_csrf(csrf_response.text)
    login_response = client.post(
        "/login",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "csrf_token": csrf_token,
        },
    )
    assert login_response.status_code == 200

    # 2) GET / agora autenticado renderiza index
    root_response = client.get("/", follow_redirects=False)
    assert root_response.status_code == 200

    # 3) Logout limpa session
    logout_response = client.post("/logout")
    assert logout_response.status_code == 200
    assert logout_response.headers.get("hx-redirect") == "/login"

    # 4) GET / pós-logout → 303 /login novamente
    final_response = client.get("/", follow_redirects=False)
    assert final_response.status_code == 303
    assert final_response.headers.get("location") == "/login"


# ── Helpers ───────────────────────────────────────────────────────────────
def _extract_csrf(html: str) -> str:
    """Extrai CSRF token do hidden input no form."""
    marker = 'name="csrf_token" value="'
    start = html.find(marker)
    assert start >= 0, "CSRF token não encontrado no form"
    start += len(marker)
    end = html.find('"', start)
    return html[start:end]
