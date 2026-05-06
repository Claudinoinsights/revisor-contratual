"""Integration tests for MVP-LEAN-01 Task 5 — S6 Resultado + C5 + D3 condicional.

Cobertura:
- AC-MVP-06 (S6 Resultado consolidado com 3 deliverables + Veredicto Juiz)
- AC-MVP-13 (C5 component parametrizado por deliverables[].disponivel)
- AC-MVP-D3-DUAL-INPUT (D3 disponível só com decisão adversa enviada em S2)
- AC-MVP-AUDIT (hash truncado 4+4 chars + audit chain entry id)

Sessão 91 (CC.14 Task 5) — Neo paralelo a Eric smoke E2E.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

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


# ── Tests S6 render ───────────────────────────────────────────────────────
@pytest.mark.integration
def test_get_verdict_renders_s6_with_3_cards(client: TestClient) -> None:
    """AC-MVP-06: GET /verdict renderiza S6 com 3 articles deliverables."""
    response = client.get("/verdict")
    assert response.status_code == 200
    body = response.text
    assert 'class="s6-container"' in body
    assert "Análise concluída" in body
    # 3 cards (article role=article)
    assert body.count('data-testid="c5-card-d') == 3


@pytest.mark.integration
def test_s6_default_d3_indisponivel_no_job_id(client: TestClient) -> None:
    """AC-MVP-D3-DUAL-INPUT: GET /verdict sem job_id usa MOCK + D3 indisponível default."""
    response = client.get("/verdict")
    body = response.text
    # MOCK_VERDICT não tem decisão adversa → D3 indisponível
    assert 'data-testid="c5-card-d3"' in body
    assert 'data-disponivel="false"' in body
    # CTA Enviar decisão presente
    assert "Enviar decisão" in body
    assert 'data-testid="c5-cta-enviar-decisao"' in body


@pytest.mark.integration
def test_s6a_d3_disponivel_renders_baixar_button(client: TestClient) -> None:
    """AC-MVP-13: has_decisao_adversa=True → 3 botões Baixar."""
    # Inject job com has_decisao_adversa=True diretamente em JOBS dict
    from bloco_interface.web.app import JOBS

    job_id = "test-job-d3-available"
    JOBS[job_id] = {
        "status": "done",
        "pdf_path": "/tmp/fake.pdf",  # noqa: S108
        "tier": "balanced",
        "uf": "SP",
        "data": "2024-01-01",
        "filename": "contrato.pdf",
        "verdict": {"audit_hash": "abc12345-xyz98765"},
        "error": None,
        "has_decisao_adversa": True,
    }
    try:
        response = client.get(f"/verdict?job_id={job_id}")
        body = response.text
        assert 'data-disponivel="true"' in body
        # 3 botões Baixar (D1+D2+D3)
        assert body.count("Baixar") >= 3
        # Botão Enviar decisão NÃO renderizado (string aparece 1x no JS querySelector;
        # quando D3 indisponível seria 2x = 1 JS + 1 botão real)
        assert body.count('data-testid="c5-cta-enviar-decisao"') == 1
    finally:
        del JOBS[job_id]


@pytest.mark.integration
def test_s6b_d3_indisponivel_renders_enviar_decisao_cta(client: TestClient) -> None:
    """AC-MVP-D3-DUAL-INPUT: has_decisao_adversa=False → 2 Baixar + CTA Enviar decisão."""
    from bloco_interface.web.app import JOBS

    job_id = "test-job-d3-unavailable"
    JOBS[job_id] = {
        "status": "done",
        "pdf_path": "/tmp/fake.pdf",  # noqa: S108
        "tier": "balanced",
        "uf": "SP",
        "data": "2024-01-01",
        "filename": "contrato.pdf",
        "verdict": {"audit_hash": "abc12345-xyz98765"},
        "error": None,
        "has_decisao_adversa": False,
    }
    try:
        response = client.get(f"/verdict?job_id={job_id}")
        body = response.text
        # D3 indisponível
        assert "(indisponível)" in body
        assert "D3 só é gerada com decisão adversa enviada" in body
        # CTA Enviar decisão presente
        assert "Enviar decisão" in body
    finally:
        del JOBS[job_id]


@pytest.mark.integration
def test_s6_hash_truncado_4_plus_4_chars(client: TestClient) -> None:
    """AC-MVP-AUDIT: hash exibido como XXXX…YYYY (4+4 chars + ellipsis)."""
    from bloco_interface.web.app import JOBS

    job_id = "test-job-hash"
    JOBS[job_id] = {
        "status": "done",
        "pdf_path": "/tmp/fake.pdf",  # noqa: S108
        "tier": "balanced",
        "uf": "SP",
        "data": "2024-01-01",
        "filename": "contrato.pdf",
        "verdict": {"audit_hash": "7a3fb91c4d5e6f7a8b9c0d1e2f3a4b5c"},
        "error": None,
        "has_decisao_adversa": False,
    }
    try:
        response = client.get(f"/verdict?job_id={job_id}")
        body = response.text
        # Hash truncado: 7a3f…4b5c
        assert "7a3f…4b5c" in body
    finally:
        del JOBS[job_id]


@pytest.mark.integration
def test_s6_sumario_juiz_uses_fraunces_class(client: TestClient) -> None:
    """AC-MVP-06: heading Veredicto Juiz tem class .s6-veredicto-heading (Fraunces)."""
    response = client.get("/verdict")
    body = response.text
    assert 'class="s6-veredicto-heading"' in body
    assert "Veredicto Juiz" in body


@pytest.mark.integration
def test_s6_audit_link_present(client: TestClient) -> None:
    """AC-MVP-06: link 'Ver entrada audit' presente."""
    response = client.get("/verdict")
    body = response.text
    assert "Ver entrada audit" in body
    assert 'data-testid="s6-link-audit"' in body


@pytest.mark.integration
def test_s6_a11y_articles_aria_labels(client: TestClient) -> None:
    """AC-MVP-13: cards usam <article role="article"> + aria-label descritivo nos botões."""
    response = client.get("/verdict")
    body = response.text
    assert 'role="article"' in body
    # aria-label descritivo em botão Baixar (formato + páginas)
    assert "aria-label=\"Baixar Relatório Contábil PDF (12 páginas)\"" in body


@pytest.mark.integration
def test_s6_microcopy_exact_per_uxspec(client: TestClient) -> None:
    """AC-MVP-13: microcopy exata da ux-spec §4 C5 linhas 725-737."""
    response = client.get("/verdict")
    body = response.text
    # D1
    assert "Relatório Contábil" in body
    assert "Tabela Price + cálculos abusivos" in body
    # D2
    assert "Petição Inicial" in body
    assert "Fundamentos + jurisprudência + pedidos" in body
    # D3 indisponível (default mock)
    assert "Apelação Cível" in body
    # Botão final
    assert "Analisar outro contrato" in body


@pytest.mark.integration
def test_post_revisar_d3_stub_redirects_to_verdict(client: TestClient) -> None:
    """AC-MVP-D3-DUAL-INPUT: POST /revisar/d3 stub aceita job_id + redirect."""
    from bloco_interface.web.app import JOBS

    job_id = "test-job-d3-rerun"
    JOBS[job_id] = {
        "status": "done",
        "pdf_path": "/tmp/fake.pdf",  # noqa: S108
        "tier": "balanced",
        "uf": "SP",
        "data": "2024-01-01",
        "filename": "contrato.pdf",
        "verdict": {},
        "error": None,
        "has_decisao_adversa": False,
    }
    try:
        decisao_pdf = b"%PDF-1.4\n%fake decisao adversa"
        response = client.post(
            "/revisar/d3",
            data={"job_id": job_id},
            files={
                "pdf_decisao_adversa": (
                    "decisao.pdf",
                    decisao_pdf,
                    "application/pdf",
                ),
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert f"/verdict?job_id={job_id}" in response.headers.get("location", "")
        # Job marcado has_decisao_adversa=True
        assert JOBS[job_id]["has_decisao_adversa"] is True
    finally:
        del JOBS[job_id]


@pytest.mark.integration
def test_post_revisar_d3_requires_auth() -> None:
    """AC-MVP-LGPD-L1: POST /revisar/d3 requer session válida."""
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
                "/revisar/d3",
                data={"job_id": "x"},
                files={"pdf_decisao_adversa": ("d.pdf", b"%PDF-1.4", "application/pdf")},
                follow_redirects=False,
            )
            assert response.status_code == 303
            assert response.headers.get("location") == "/login"
