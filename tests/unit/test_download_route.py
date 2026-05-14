"""Tests para TD-SP06-DOWNLOAD-ROUTES-01 — Sprint 6 Bloco γ Wave γ.2.

Endpoint GET /download/{job_id} authenticated + ownership check + audit chain.

AC-08 coverage (5 tests core):
  - test_download_200_owner_receives_pdf
  - test_download_401_unauthenticated_rejected
  - test_download_403_non_owner_forbidden
  - test_download_404_job_not_found
  - test_download_404_pdf_not_generated_yet

Bonus:
  - test_download_audit_entry_created_pdf_downloaded
  - test_download_content_disposition_attachment_filename
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bloco_interface.web import auth
from bloco_interface.web.app import JOBS, app

pytestmark = [pytest.mark.unit]


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures — auth bypass via monkeypatch (mirror test_classic_route.py)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def authed_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """TestClient com auth.authenticate mockado + session admin populada."""
    def _mock_authenticate(username: str, password: str) -> bool:
        return username == "admin" and password == "admin"

    monkeypatch.setattr(auth, "authenticate", _mock_authenticate)
    client = TestClient(app)
    # Estabelece sessão admin via login JSON SPA flow
    csrf_resp = client.get("/api/csrf-token")
    csrf = csrf_resp.json()["csrf_token"]
    login = client.post(
        "/login",
        json={"username": "admin", "password": "admin", "csrf_token": csrf},
    )
    assert login.status_code == 200
    yield client


@pytest.fixture
def unauth_client() -> Iterator[TestClient]:
    """TestClient sem sessão (zero auth)."""
    yield TestClient(app)


@pytest.fixture
def fake_pdf_path(tmp_path: Path) -> Path:
    """Cria PDF fake no filesystem para servir via /download."""
    pdf = tmp_path / "fake-peca.pdf"
    pdf.write_bytes(b"%PDF-1.7\n%mock test pdf content\n0123456789\n%%EOF")
    return pdf


@pytest.fixture
def populated_job(fake_pdf_path: Path) -> Iterator[str]:
    """Insere JOBS[job_id] com owner=admin + peca_pdf_path=fake_pdf."""
    import uuid
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "status": "done",
        "owner": "admin",
        "peca_pdf_path": str(fake_pdf_path),
        "peca_pdf_hash": "fake-hash",
        "peca_format": "PecaRevisional",
        "verdict": {"veredito": "APROVADO_100"},
        "filename": "test.pdf",
    }
    yield job_id
    JOBS.pop(job_id, None)


# ─────────────────────────────────────────────────────────────────────────────
# AC-08 Test 1: 200 owner receives PDF
# ─────────────────────────────────────────────────────────────────────────────


def test_download_200_owner_receives_pdf(authed_client: TestClient, populated_job: str) -> None:
    """AC-02 + AC-04: owner autenticado recebe PDF 200 com Content-Type pdf."""
    response = authed_client.get(f"/download/{populated_job}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")
    # AC-04 Content-Disposition attachment com filename derivado de job_id[:8]
    cd = response.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert f"peca-revisional-{populated_job[:8]}" in cd


# ─────────────────────────────────────────────────────────────────────────────
# AC-08 Test 2: 401 unauthenticated rejected
# ─────────────────────────────────────────────────────────────────────────────


def test_download_401_unauthenticated_rejected(
    unauth_client: TestClient, populated_job: str
) -> None:
    """AC-02: sem sessão → 401 Autenticação requerida (HTML error_handler middleware)."""
    response = unauth_client.get(f"/download/{populated_job}")
    assert response.status_code == 401
    # Project error_handler middleware renderiza HTML s7_error em vez de JSON default.
    # Verifica que NÃO retornou o PDF (status_code é o gate semântico).
    assert not response.content.startswith(b"%PDF-")


# ─────────────────────────────────────────────────────────────────────────────
# AC-08 Test 3: 403 non-owner forbidden
# ─────────────────────────────────────────────────────────────────────────────


def test_download_403_non_owner_forbidden(
    authed_client: TestClient, fake_pdf_path: Path
) -> None:
    """AC-02 Smith β F-D3-β-06 address: user != owner → 403."""
    import uuid
    other_owner_job = str(uuid.uuid4())
    JOBS[other_owner_job] = {
        "status": "done",
        "owner": "outro_advogado",  # NOT admin
        "peca_pdf_path": str(fake_pdf_path),
        "peca_pdf_hash": "hash-x",
        "peca_format": "PecaRevisional",
        "verdict": {},
        "filename": "other.pdf",
    }
    try:
        response = authed_client.get(f"/download/{other_owner_job}")
        assert response.status_code == 403
        assert not response.content.startswith(b"%PDF-")  # NÃO entrega PDF
    finally:
        JOBS.pop(other_owner_job, None)


# ─────────────────────────────────────────────────────────────────────────────
# AC-08 Test 4: 404 job not found
# ─────────────────────────────────────────────────────────────────────────────


def test_download_404_job_not_found(authed_client: TestClient) -> None:
    """AC-03: job_id inexistente → 404 (HTML error_handler middleware)."""
    response = authed_client.get("/download/job-que-nao-existe-12345")
    assert response.status_code == 404
    assert not response.content.startswith(b"%PDF-")


# ─────────────────────────────────────────────────────────────────────────────
# AC-08 Test 5: 404 PDF not generated yet
# ─────────────────────────────────────────────────────────────────────────────


def test_download_404_pdf_not_generated_yet(authed_client: TestClient) -> None:
    """AC-03: job existe mas peca_pdf_path=None → 404 aguarde pipeline."""
    import uuid
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "status": "running",
        "owner": "admin",
        "peca_pdf_path": None,  # ainda não gerado
        "verdict": None,
        "filename": "pending.pdf",
    }
    try:
        response = authed_client.get(f"/download/{job_id}")
        assert response.status_code == 404
        assert not response.content.startswith(b"%PDF-")
    finally:
        JOBS.pop(job_id, None)


# ─────────────────────────────────────────────────────────────────────────────
# Bonus: audit chain entry pdf_downloaded
# ─────────────────────────────────────────────────────────────────────────────


def test_download_audit_entry_created_pdf_downloaded(
    authed_client: TestClient,
    populated_job: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-06: download bem-sucedido escreve entry HMAC-chained pdf_downloaded."""
    # Capturar chamadas append_audit_entry via monkeypatch
    captured = []

    def _spy_append(event_type, payload, **kwargs):
        captured.append((event_type, dict(payload), kwargs))

    # Patch no escopo do módulo app.py onde está importado
    from bloco_interface.web import app as web_app
    monkeypatch.setattr(web_app, "append_audit_entry", _spy_append)

    response = authed_client.get(f"/download/{populated_job}")
    assert response.status_code == 200

    # Pelo menos 1 entry pdf_downloaded
    pdf_entries = [(t, p) for (t, p, _) in captured if t == "pdf_downloaded"]
    assert len(pdf_entries) == 1
    event_type, payload = pdf_entries[0]
    assert payload["job_id"] == populated_job
    assert payload["user"] == "admin"
    assert "pdf_sha256" in payload
    assert len(payload["pdf_sha256"]) == 64  # SHA256 hex
    assert payload["pdf_size_bytes"] > 0
    assert "timestamp" in payload


def test_download_content_disposition_attachment_filename(
    authed_client: TestClient, populated_job: str
) -> None:
    """AC-04: Content-Disposition attachment + filename derivado de job_id[:8]."""
    response = authed_client.get(f"/download/{populated_job}")
    assert response.status_code == 200

    cd = response.headers["content-disposition"]
    assert cd.startswith("attachment;")
    assert f'filename="peca-revisional-{populated_job[:8]}.pdf"' in cd
    # X-Peca-Format header informativo
    assert response.headers.get("x-peca-format") == "PecaRevisional"


# ─────────────────────────────────────────────────────────────────────────────
# Smith F-γ-01 hotfix: audit-first pattern — audit failure bloqueia download
# ─────────────────────────────────────────────────────────────────────────────


def test_download_503_when_audit_fails(
    authed_client: TestClient,
    populated_job: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F-γ-01 HOTFIX: se append_audit_entry raises, /download → 503 LGPD §46.

    LGPD compliance: peça revisional tem dados pessoais sensíveis; download SEM
    trail HMAC é violação Art. 46. Hotfix Smith F-γ-01 substitui silent failure
    por HTTPException 503 + logger.error preserved.
    """
    def _raise_on_audit(event_type, payload, **kwargs):
        raise RuntimeError(
            f"audit chain HMAC corrupted (probe): event={event_type} payload_keys={sorted(payload.keys())}"
        )

    from bloco_interface.web import app as web_app
    monkeypatch.setattr(web_app, "append_audit_entry", _raise_on_audit)

    response = authed_client.get(f"/download/{populated_job}")
    assert response.status_code == 503
    # NÃO entregou PDF (LGPD §46 compliance preserved)
    assert not response.content.startswith(b"%PDF-")

