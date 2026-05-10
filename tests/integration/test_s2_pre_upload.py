"""Integration tests for MVP-LEAN-01 Task 3 — S2 Pré-upload + C3 Upload zone dual-input.

Cobertura:
- AC-MVP-02 (S2 Pré-upload com 2 drop-zones D1+D2)
- AC-MVP-11 (C3 component parametrizado por tipo)
- AC-MVP-D3-DUAL-INPUT (per F-CC3-06: D3 só gerado quando decisão adversa enviada)
- AC-MVP-TOKENS (uso var(--opacity-disabled) + var(--cursor-disabled))

Sessão 91 (CC.12 Task 3) — Neo paralelo a Eric smoke E2E.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

# Sprint 04 chunk 1 MINIMAL (commit e7cbe7b) substituiu GET / por SPA OrSheva 7 —
# wizard S2 legacy (drop zones D1/D2, CTA disabled, microcopy UX spec, upload.js)
# não existe mais. TD-SP04-LEGACY-TESTS MEDIUM Sprint 6+ — atualizar.
pytestmark = pytest.mark.skip(
    reason="Legacy MVP-LEAN-01 S2 wizard superseded by SPA OrSheva 7 chunk 1 "
    "(commit e7cbe7b). See TD-SP04-LEGACY-TESTS in governance/TECH-DEBT.md."
)

# ── Fixtures (mesmo pattern Task 1+2) ─────────────────────────────────────
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
    """TestClient autenticado (login automático Task 2 + lifespan mockado)."""
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


# ── Tests ─────────────────────────────────────────────────────────────────
@pytest.mark.integration
def test_get_root_authenticated_renders_s2(client: TestClient) -> None:
    """AC-MVP-02: GET / autenticada renderiza S2 Pré-upload."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert 's2-container' in body
    assert "Bem-vindo" in body


@pytest.mark.integration
def test_s2_welcome_heading_includes_username(client: TestClient) -> None:
    """AC-MVP-02: heading inclui session_user."""
    response = client.get("/")
    body = response.text
    assert f"Bem-vindo, {TEST_USERNAME}" in body


@pytest.mark.integration
def test_s2_has_2_drop_zones_d1_d2(client: TestClient) -> None:
    """AC-MVP-D3-DUAL-INPUT: 2 drop-zones (contrato + decisão adversa)."""
    response = client.get("/")
    body = response.text
    assert 'data-tipo="contrato"' in body
    assert 'data-tipo="decisao_adversa"' in body
    # Verifica 2 ocorrências de upload-zone
    assert body.count('class="upload-zone upload-zone--') == 2


@pytest.mark.integration
def test_c3_contrato_zone_aria_label_obrigatorio(client: TestClient) -> None:
    """AC-MVP-11: D1 contrato com aria-label obrigatório + aria-required=true."""
    response = client.get("/")
    body = response.text
    assert 'aria-label="Upload obrigatório — contrato CDC em PDF"' in body
    assert 'aria-required="true"' in body
    assert "1. Contrato (obrigatório)" in body


@pytest.mark.integration
def test_c3_decisao_adversa_zone_aria_label_opcional(client: TestClient) -> None:
    """AC-MVP-11: D2 decisão adversa com aria-label opcional + aria-required=false."""
    response = client.get("/")
    body = response.text
    assert 'aria-label="Upload opcional — decisão adversa em PDF para gerar Apelação Cível"' in body
    assert 'aria-required="false"' in body
    assert "2. Decisão adversa (opcional)" in body


@pytest.mark.integration
def test_s2_cta_initially_disabled(client: TestClient) -> None:
    """AC-MVP-02 + AC-MVP-TOKENS: CTA Iniciar análise inicia disabled."""
    response = client.get("/")
    body = response.text
    assert 'id="upload-cta"' in body
    assert 'aria-disabled="true"' in body
    assert "disabled" in body
    assert "Iniciar análise" in body


@pytest.mark.integration
def test_s2_lgpd_reassurance_text_present(client: TestClient) -> None:
    """AC-MVP-LGPD-L1: reassurance LGPD presente em D1 (per ux-spec C3 contrato)."""
    response = client.get("/")
    body = response.text
    assert "Os dados não saem da sua máquina (LGPD)" in body


@pytest.mark.integration
def test_s2_microcopy_exact_per_uxspec(client: TestClient) -> None:
    """AC-MVP-11: microcopy exata da ux-spec §4 C3 (não inventar variações)."""
    response = client.get("/")
    body = response.text
    # Microcopy contrato
    assert "Arraste o PDF do contrato" in body
    assert "ou <strong>clique para selecionar</strong>" in body
    assert "PDF apenas · até 10MB" in body
    # Microcopy decisão adversa
    assert "Arraste a decisão adversa" in body
    assert (
        "Opcional — só envie se já houver sentença desfavorável que precise apelar. "
        "Habilita D3."
    ) in body
    # Instructions globais S2
    assert "Envie o contrato CDC PF Veículos do seu cliente" in body
    assert "gerar a peça de Apelação Cível (D3)" in body


@pytest.mark.integration
def test_s2_form_post_to_revisar(client: TestClient) -> None:
    """AC-MVP-02: form aponta para POST /revisar (pipeline existente)."""
    response = client.get("/")
    body = response.text
    assert 'id="upload-form"' in body
    assert 'action="/revisar"' in body
    assert 'enctype="multipart/form-data"' in body


@pytest.mark.integration
def test_s2_includes_upload_js_script(client: TestClient) -> None:
    """AC-MVP-02: client-side validation script incluído (vanilla JS)."""
    response = client.get("/")
    body = response.text
    assert 'src="/static/upload.js"' in body
