"""Tests para TD-SP06-MODE-PASS-01 — Backend modalidade_override Form param.

Cobertura:
  - AC-03: POST /revisar aceita Form parameter `modalidade_override` válido
  - AC-05: 422 com diagnostic claro para modalidades inválidas
  - Default behavior preserved: sem override → regex _extract_modalidade

Note: TD-SP06-PYTEST-DEPS-PYTHON-3-14 — rodar com Python 3.14.
"""

from __future__ import annotations

import io
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from bloco_interface.web import auth
from bloco_interface.web.app import app


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
    """Mesma fixture de test_revisar_dual_content_type.py — auth + ollama bypass."""
    def _mock_authenticate(username: str, password: str) -> bool:
        return username == "admin" and password == "admin"

    async def _mock_detect_running(host: str, port: int) -> bool:
        return True

    def _mock_is_ready() -> bool:
        return True

    monkeypatch.setattr(auth, "authenticate", _mock_authenticate)
    from bloco_interface import ollama_manager
    monkeypatch.setattr(ollama_manager, "detect_running_ollama", _mock_detect_running)
    monkeypatch.setattr(ollama_manager, "is_ready", _mock_is_ready)

    client = TestClient(app)
    csrf = client.get("/api/csrf-token").json()["csrf_token"]
    client.post(
        "/login",
        json={"username": "admin", "password": "admin", "csrf_token": csrf},
    )
    yield client


# ─────────────────────────────────────────────────────────────────────────────
# AC-03: Form parameter modalidade_override
# ─────────────────────────────────────────────────────────────────────────────


def test_post_revisar_with_valid_modalidade_veiculos(authed_client: TestClient) -> None:
    """AC-03: modalidade_override=CDC_VEICULOS_PF aceita + JSON response."""
    pdf_file = ("c.pdf", io.BytesIO(_MINIMAL_PDF), "application/pdf")
    response = authed_client.post(
        "/revisar",
        headers={"Accept": "application/json"},
        files={"pdf": pdf_file},
        data={"uf": "", "data": "", "tier": "balanced", "modalidade_override": "CDC_VEICULOS_PF"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data


def test_post_revisar_with_valid_modalidade_imobiliario(authed_client: TestClient) -> None:
    """AC-03: modalidade_override=CDC_IMOBILIARIO aceita no upload (pipeline falhará Sprint 6+)."""
    pdf_file = ("c.pdf", io.BytesIO(_MINIMAL_PDF), "application/pdf")
    response = authed_client.post(
        "/revisar",
        headers={"Accept": "application/json"},
        files={"pdf": pdf_file},
        data={"uf": "", "data": "", "tier": "balanced", "modalidade_override": "CDC_IMOBILIARIO"},
    )
    # Backend aceita (job criado) — pipeline real falhará em Step 3 BACEN com DP-03
    # Esse teste cobre apenas upload validation; pipeline error fica para PHASE-VALID
    assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# AC-05: 422 para modalidade inválida
# ─────────────────────────────────────────────────────────────────────────────


def test_post_revisar_with_invalid_modalidade_returns_422(authed_client: TestClient) -> None:
    """AC-05: modalidade_override='INVALID' → 422 + diagnostic via S7 error template OR JSON detail.

    HTTPException é convertida para template S7 (s7_error.html) pelo handler global
    (MVP-LEAN-01 Task 6). Status 422 preservado; diagnostic embedded no HTML response.
    """
    pdf_file = ("c.pdf", io.BytesIO(_MINIMAL_PDF), "application/pdf")
    response = authed_client.post(
        "/revisar",
        headers={"Accept": "application/json"},
        files={"pdf": pdf_file},
        data={"uf": "", "data": "", "tier": "balanced", "modalidade_override": "INVALID_TYPE"},
    )
    assert response.status_code == 422
    body = response.text  # S7 template HTML — não JSON parse
    # Backend HTTPException detail embedded no S7 template OR raw exception text
    assert "INVALID_TYPE" in body or "Modalidade" in body or "422" in body


# ─────────────────────────────────────────────────────────────────────────────
# Default behavior preserved: sem override → regex
# ─────────────────────────────────────────────────────────────────────────────


def test_post_revisar_without_modalidade_override_preserves_default(
    authed_client: TestClient,
) -> None:
    """Sem modalidade_override (default '') → upload OK (regex extrai do PDF)."""
    pdf_file = ("c.pdf", io.BytesIO(_MINIMAL_PDF), "application/pdf")
    response = authed_client.post(
        "/revisar",
        headers={"Accept": "application/json"},
        files={"pdf": pdf_file},
        data={"uf": "", "data": "", "tier": "balanced"},  # sem modalidade_override
    )
    assert response.status_code == 200
