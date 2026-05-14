"""Tests para TD-SP06-SPA-CONNECT-01 — Backend POST /revisar dual-content-type (ADR-021).

Cobertura:
  - AC backend: POST /revisar com Accept: application/json → JSONResponse com job_id + stream_url
  - AC backend: POST /revisar sem Accept (default) → HTMLResponse template legacy preserved
  - Schema JSON contract conforme ADR-021

Note: TD-SP06-PYTEST-DEPS-PYTHON-3-14 — rodar com Python 3.14 (env Python 3.13 não tem sqlalchemy
via bloco_auth import chain). Mock auth.authenticate via monkeypatch para bypass env var hash.
Mock ollama_manager + revisar_contrato via monkeypatch para evitar real LLM inference (smoke test
real fica para Operator pós-Neo).
"""

from __future__ import annotations

import io
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from bloco_interface.web import auth
from bloco_interface.web.app import app


# Minimal valid PDF bytes (magic %PDF- + minimal structure) — passa magic bytes validation
_MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n"
    b"xref\n0 3\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000054 00000 n \n"
    b"trailer<</Size 3/Root 1 0 R>>\n"
    b"startxref\n95\n%%EOF\n"
)


@pytest.fixture
def authed_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Client com auth + ollama_manager + revisar_contrato mockados.

    auth.authenticate bypass env var ADMIN_PASSWORD_HASH (mesmo padrão test_classic_route.py).
    ollama_manager.is_ready + detect_running_ollama mock → 503 evita pipeline real iniciar.
    revisar_contrato NÃO precisa mock — POST /revisar apenas valida + cria job;
    pipeline real só roda em GET /revisar/stream (não testado aqui).
    """
    def _mock_authenticate(username: str, password: str) -> bool:
        return username == "admin" and password == "admin"

    async def _mock_detect_running(host: str, port: int) -> bool:
        return True  # bypass lazy respawn

    def _mock_is_ready() -> bool:
        return True  # bypass 503 modelos baixando

    monkeypatch.setattr(auth, "authenticate", _mock_authenticate)

    from bloco_interface import ollama_manager
    monkeypatch.setattr(ollama_manager, "detect_running_ollama", _mock_detect_running)
    monkeypatch.setattr(ollama_manager, "is_ready", _mock_is_ready)

    client = TestClient(app)
    # Login para session ativa
    csrf = client.get("/api/csrf-token").json()["csrf_token"]
    resp = client.post(
        "/login",
        json={"username": "admin", "password": "admin", "csrf_token": csrf},
    )
    assert resp.status_code == 200
    yield client


# ─────────────────────────────────────────────────────────────────────────────
# ADR-021 dual-content-type branches
# ─────────────────────────────────────────────────────────────────────────────


def test_post_revisar_with_accept_json_returns_json_response(
    authed_client: TestClient,
) -> None:
    """ADR-021 JSON branch: POST /revisar Accept: application/json → JSON com job_id."""
    pdf_file = ("contrato.pdf", io.BytesIO(_MINIMAL_PDF), "application/pdf")
    response = authed_client.post(
        "/revisar",
        headers={"Accept": "application/json"},
        files={"pdf": pdf_file},
        data={"uf": "", "data": "", "tier": "balanced"},
    )
    assert response.status_code == 200
    # Content-Type JSON (não text/html)
    content_type = response.headers.get("content-type", "")
    assert "application/json" in content_type.lower()

    # Schema ADR-021
    data = response.json()
    assert "job_id" in data
    assert "status" in data
    assert "filename" in data
    assert "stream_url" in data
    assert "verdict_url" in data
    assert "has_decisao_adversa" in data

    # Valores expected
    assert data["status"] == "queued"
    assert data["filename"] == "contrato.pdf"
    assert data["stream_url"] == f"/revisar/stream/{data['job_id']}"
    assert data["verdict_url"] == f"/verdict?job_id={data['job_id']}"
    assert data["has_decisao_adversa"] is False  # D2 não enviado


def test_post_revisar_without_accept_returns_html_legacy(
    authed_client: TestClient,
) -> None:
    """ADR-021 fall-through: POST /revisar sem Accept JSON → HTMLResponse legacy preserved."""
    pdf_file = ("contrato.pdf", io.BytesIO(_MINIMAL_PDF), "application/pdf")
    response = authed_client.post(
        "/revisar",
        # Sem Accept: application/json header
        files={"pdf": pdf_file},
        data={"uf": "", "data": "", "tier": "balanced"},
    )
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "text/html" in content_type.lower()
    # HTML response contém s5_processing template signatures
    body = response.text
    assert "job_id" in body or "processing" in body.lower()


def test_post_revisar_invalid_pdf_returns_400(authed_client: TestClient) -> None:
    """Magic bytes validation rejeita não-PDF (preserved AC-1)."""
    fake_file = ("fake.pdf", io.BytesIO(b"NOTAPDF"), "application/pdf")
    response = authed_client.post(
        "/revisar",
        headers={"Accept": "application/json"},
        files={"pdf": fake_file},
        data={"uf": "", "data": "", "tier": "balanced"},
    )
    assert response.status_code == 400
