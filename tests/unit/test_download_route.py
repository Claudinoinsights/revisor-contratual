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


# ─────────────────────────────────────────────────────────────────────
# Sprint 6.1 Wave 6.1.3 — F-γ-08+09+10 LOW consolidated remediation
# ─────────────────────────────────────────────────────────────────────


def test_401_endpoint_specifies_www_authenticate_in_exception(
    unauth_client: TestClient, populated_job: str
) -> None:
    """F-γ-08 Sprint 6.1: HTTPException 401 declarada com headers WWW-Authenticate=Session.

    Note: o `error_handler` middleware do projeto reescreve responses 401 para HTML
    s7_error e pode swallow custom headers. O fix Sprint 6.1 ESTÁ aplicado no source
    (raise HTTPException com headers={"WWW-Authenticate": "Session"}); a entrega
    efetiva ao cliente depende do middleware. TD-SP06.2-WWW-AUTHENTICATE-MIDDLEWARE
    catalogado para Sprint 6.2 (middleware override preservar custom headers).

    Esta verifica via source inspection que a constante está corretamente declarada.
    """
    import inspect
    from bloco_interface.web import app as web_app
    source = inspect.getsource(web_app.download_peca)
    # Source contém o header WWW-Authenticate (verifica fix aplicado no código)
    assert '"WWW-Authenticate": "Session"' in source

    # Comportamento user-facing: status_code 401 garantido (middleware preserva)
    response = unauth_client.get(f"/download/{populated_job}")
    assert response.status_code == 401


def test_download_constants_exposed():
    """F-γ-09 Sprint 6.1: 404 distinct detail constants expostos para audit forense."""
    from bloco_interface.web.app import (
        DOWNLOAD_404_JOB_NOT_FOUND,
        DOWNLOAD_404_PDF_FILE_MISSING,
        DOWNLOAD_404_PDF_NOT_GENERATED,
    )

    assert DOWNLOAD_404_JOB_NOT_FOUND == "job_not_found"
    assert DOWNLOAD_404_PDF_NOT_GENERATED == "pdf_not_generated_yet"
    assert DOWNLOAD_404_PDF_FILE_MISSING == "pdf_file_missing"
    # All distinct (no collision)
    assert len({
        DOWNLOAD_404_JOB_NOT_FOUND,
        DOWNLOAD_404_PDF_NOT_GENERATED,
        DOWNLOAD_404_PDF_FILE_MISSING,
    }) == 3


def test_max_pdf_bytes_50mb_constant():
    """F-γ-10 Sprint 6.1: MAX_PDF_BYTES = 50MB sensible default SaaS."""
    from bloco_interface.web.app import MAX_PDF_BYTES

    assert MAX_PDF_BYTES == 50 * 1024 * 1024  # 50MB
    assert MAX_PDF_BYTES > 1024 * 1024  # > 1MB (peças reais ~500KB-2MB)


def test_413_oversized_pdf_blocked(
    authed_client: TestClient,
    fake_pdf_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F-γ-10 Sprint 6.1: PDF >50MB → 413 Payload Too Large.

    DoS protection — pdf_path.stat().st_size verificado ANTES de read_bytes()
    para avoid memory exhaustion via payload malicioso 1GB+.
    """
    import uuid
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "status": "done",
        "owner": "admin",
        "peca_pdf_path": str(fake_pdf_path),
        "peca_pdf_hash": "fake-hash-large",
        "peca_format": "PecaRevisional",
        "verdict": {"veredito": "APROVADO_100"},
        "filename": "huge.pdf",
    }
    try:
        # Mock pdf_path.stat() para retornar size > 50MB
        from pathlib import Path as _Path
        original_stat = _Path.stat

        def mock_stat(self, *args, **kwargs):
            real_stat = original_stat(self, *args, **kwargs)
            if str(self) == str(fake_pdf_path):
                # Spoofar size = 51MB
                class _FakeStat:
                    st_size = 51 * 1024 * 1024
                    st_mode = real_stat.st_mode
                    st_mtime = real_stat.st_mtime
                return _FakeStat()
            return real_stat

        monkeypatch.setattr(_Path, "stat", mock_stat)

        response = authed_client.get(f"/download/{job_id}")
        assert response.status_code == 413
        assert not response.content.startswith(b"%PDF-")
    finally:
        JOBS.pop(job_id, None)

