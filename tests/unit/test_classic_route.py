"""Tests para TD-SP06-CLASSIC-01 — Rota GET /classic Jinja2 bypass do SPA mock.

Cobertura:
  - AC-01: GET /classic sem session → s1_login.html
  - AC-01: GET /classic com session → s2_pre_upload.html
  - AC-04: POST /login Form-encoded → HX-Redirect /classic (não /)
  - AC-04: POST /login JSON → preserva response JSON SPA
  - POST /logout → HX-Redirect /classic (não /login inexistente)
  - AC-06: CSP headers preservados em /classic

Note: TD-SP06-PYTEST-DEPS-PYTHON-3-14 — alguns testes auth-dependent precisam de
Python 3.14 (env atual env Python 3.13 não tem sqlalchemy via bloco_auth import
chain). Roda com: py -3.14 -m pytest tests/unit/test_classic_route.py
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from bloco_interface.web import auth
from bloco_interface.web.app import app

client = TestClient(app)


@pytest.fixture
def authed_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Client com auth.authenticate mockado retornando True (bypass env var hash).

    Necessário porque test runner não carrega .env com ADMIN_PASSWORD_HASH;
    auth real falha 401 sem env. Mock é safe — preserva fluxo POST /login dual-content-type
    (CSRF check + session creation) inalterados.
    """
    def _mock_authenticate(username: str, password: str) -> bool:
        return username == "admin" and password == "admin"

    monkeypatch.setattr(auth, "authenticate", _mock_authenticate)
    yield TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# AC-01: GET /classic dual-state (auth vs unauth)
# ─────────────────────────────────────────────────────────────────────────────


def test_get_classic_without_session_renders_s1_login() -> None:
    """AC-01: GET /classic sem session → 200 + s1_login.html template."""
    response = client.get("/classic")
    assert response.status_code == 200
    body = response.text
    # s1_login.html tem form action="/login" + htmx attributes
    assert 'action="/login"' in body
    assert 'hx-post="/login"' in body
    # NÃO contém SPA index.html signature (screen-app)
    assert 'id="screen-app"' not in body


def test_get_classic_with_session_renders_s2_pre_upload(
    authed_client: TestClient,
) -> None:
    """AC-01: GET /classic autenticado → 200 + s2_pre_upload.html template."""
    # Login via JSON SPA flow (mais simples para test)
    csrf_resp = authed_client.get("/api/csrf-token")
    csrf = csrf_resp.json()["csrf_token"]
    login = authed_client.post(
        "/login",
        json={"username": "admin", "password": "admin", "csrf_token": csrf},
    )
    assert login.status_code == 200
    assert login.json()["success"] is True

    # GET /classic com session ativa
    response = authed_client.get("/classic")
    assert response.status_code == 200
    body = response.text
    # s2_pre_upload.html tem form action="/revisar" + multipart
    assert 'action="/revisar"' in body
    assert 'enctype="multipart/form-data"' in body


# ─────────────────────────────────────────────────────────────────────────────
# AC-06: Cache-Control headers preservados
# ─────────────────────────────────────────────────────────────────────────────


def test_get_classic_cache_control_no_cache() -> None:
    """AC-06: /classic Cache-Control no-cache (evita stale Jinja2)."""
    response = client.get("/classic")
    cache_control = response.headers.get("cache-control", "")
    assert "no-cache" in cache_control
    assert "no-store" in cache_control
    assert "must-revalidate" in cache_control


# ─────────────────────────────────────────────────────────────────────────────
# AC-04: POST /login dual-content-type
# ─────────────────────────────────────────────────────────────────────────────


def test_post_login_json_preserves_spa_response(authed_client: TestClient) -> None:
    """AC-04: POST /login Content-Type JSON → response JSON SPA atual (não muda)."""
    csrf_resp = authed_client.get("/api/csrf-token")
    csrf = csrf_resp.json()["csrf_token"]

    response = authed_client.post(
        "/login",
        json={"username": "admin", "password": "admin", "csrf_token": csrf},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["email"] == "admin"
    assert "csrf_token" in data
    # JSON flow NÃO deve setar HX-Redirect (esse é só legacy htmx)
    assert "hx-redirect" not in {k.lower() for k in response.headers}


def test_post_login_form_encoded_hx_redirect_to_classic(
    authed_client: TestClient,
) -> None:
    """AC-04: POST /login Form-encoded → HX-Redirect /classic (não /)."""
    csrf_resp = authed_client.get("/api/csrf-token")
    csrf = csrf_resp.json()["csrf_token"]

    response = authed_client.post(
        "/login",
        data={"username": "admin", "password": "admin", "csrf_token": csrf},
    )
    assert response.status_code == 200
    # Legacy htmx: HX-Redirect header presente apontando para /classic
    hx_redirect = response.headers.get("hx-redirect")
    assert hx_redirect == "/classic"


# ─────────────────────────────────────────────────────────────────────────────
# POST /logout HX-Redirect updated
# ─────────────────────────────────────────────────────────────────────────────


def test_post_logout_hx_redirect_to_classic(authed_client: TestClient) -> None:
    """POST /logout → HX-Redirect /classic (não /login inexistente)."""
    # Login primeiro
    csrf = authed_client.get("/api/csrf-token").json()["csrf_token"]
    authed_client.post(
        "/login",
        json={"username": "admin", "password": "admin", "csrf_token": csrf},
    )

    # Logout
    response = authed_client.post("/logout")
    assert response.status_code == 200
    assert response.headers.get("hx-redirect") == "/classic"


# ─────────────────────────────────────────────────────────────────────────────
# AC-03: SPA preservado em GET / (additive, não-quebra Sprint 5+ Bloco 3)
# ─────────────────────────────────────────────────────────────────────────────


def test_get_root_still_serves_spa() -> None:
    """AC-03: GET / continua servindo SPA index.html (não /classic Jinja2)."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    # SPA index.html signature
    assert 'id="screen-app"' in body or 'class="app-shell"' in body
    # NÃO deve ser Jinja2 s1_login
    assert 'hx-post="/login"' not in body
