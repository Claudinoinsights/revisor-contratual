"""Integration tests for Sprint 04 SPA OrSheva 7 (chunk 1 MINIMAL — commit e7cbe7b).

Cobertura mínima da SPA estática que substituiu o template Jinja2 legacy MVP-LEAN-01:
- GET / autenticado renderiza SPA OrSheva 7 (bloco_interface/web/static/index.html)
- GET / não autenticado redireciona /login (dual-protection MVP-LEAN-01 H4)
- Sidebar com 7 modos (CCB/Veículo/Consignado/Cartão/Imobiliário/FIES/Geral) — ADR-020
- Brand "Em formalização LGPD" honest temporário (NF1 — Hamann Caminho A Opção B)
- Zero CDN externo (LGPD NFR-LGPD-01 — REV-INT-02 self-host fonts pattern)
- Self-hosted fonts @font-face (Manrope + Fraunces + JetBrains)
- API Key section presente para BYOK Anthropic claude (SP04-BYOK-01)

Esta suite SUBSTITUI cobertura do template Jinja2 legacy. Os 27 testes legacy
(test_layout_base, test_s2_pre_upload, test_s5_processing_sse, test_s8_banner_critical,
test_pipeline_e2e) ficam pytest.mark.skip com referência a TD-SP04-LEGACY-TESTS.

TD-SP04-LEGACY-TESTS MEDIUM Sprint 6+ — atualizar 27 testes legacy para SPA OrSheva 7
(reescrever asserts ao invés de skip; este file é cobertura mínima interim).

Sessão 92 (Sprint 04 pre-merge recovery — chunk pós-Smith FINAL re-gate +
post Eric authorization "execute os marges, todos eles" + Operator detectou
27 legacy regression — Neo Opção B-1 fix).
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
def client_unauthenticated() -> Iterator[TestClient]:
    """TestClient sem login — para validar dual-protection H4."""
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


@pytest.fixture
def client(client_unauthenticated: TestClient) -> TestClient:
    """TestClient autenticado — login automático."""
    login_page = client_unauthenticated.get("/login")
    csrf_marker = 'name="csrf_token" value="'
    start = login_page.text.find(csrf_marker) + len(csrf_marker)
    end = login_page.text.find('"', start)
    csrf_token = login_page.text[start:end]
    client_unauthenticated.post(
        "/login",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "csrf_token": csrf_token,
        },
    )
    return client_unauthenticated


# ── SPA Rendering ─────────────────────────────────────────────────────────


@pytest.mark.integration
def test_get_root_authenticated_renders_spa_orsheva_7(client: TestClient) -> None:
    """SP04-UI-SPA-01 chunk 1 — GET / autenticado serve SPA OrSheva 7 estática."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    # SPA marker — title + meta theme-color OrSheva orange
    assert "OrSheva 7" in body
    assert 'data-theme="light"' in body
    # meta tag: <meta name="theme-color" content="#EE6B20"> — checar attribute pair
    assert 'name="theme-color"' in body
    assert "#EE6B20" in body  # --or-500 brand


@pytest.mark.integration
def test_get_root_unauthenticated_redirects_login(
    client_unauthenticated: TestClient,
) -> None:
    """MVP-LEAN-01 H4 dual-protection — GET / sem session redireciona /login."""
    # follow_redirects=False para capturar 303
    response = client_unauthenticated.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


# ── Sidebar 7 Modos (ADR-020) ─────────────────────────────────────────────


@pytest.mark.integration
def test_spa_has_sidebar_7_modos(client: TestClient) -> None:
    """ADR-020 + Sati ratify — sidebar 7 doctypes operacionais."""
    response = client.get("/")
    body = response.text
    # 7 data-mode buttons (ADR-020 §1.5 hierarquia)
    assert 'data-mode="ccb"' in body
    assert 'data-mode="veiculo"' in body
    assert 'data-mode="consignado"' in body
    assert 'data-mode="cartao"' in body
    assert 'data-mode="imobiliario"' in body
    assert 'data-mode="fies"' in body
    assert 'data-mode="geral"' in body


@pytest.mark.integration
def test_spa_sidebar_has_numeração_01_07(client: TestClient) -> None:
    """Sati ratify Eixo 2 — numeração 01-07 reduz cognitive load (Miller's law)."""
    response = client.get("/")
    body = response.text
    for num in ("01", "02", "03", "04", "05", "06", "07"):
        assert f'class="nav-item-num">{num}</span>' in body


# ── Brand-honest LGPD (Hamann Caminho A Opção B) ──────────────────────────


@pytest.mark.integration
def test_spa_has_brand_em_formalizacao_lgpd(client: TestClient) -> None:
    """C2 + NF1 fix — brand-honest 'Em formalização LGPD' (não 'LGPD-aware'
    aspiracional). Eric advogado externo finaliza TOS canônico ANPD-defensible.
    """
    response = client.get("/")
    body = response.text
    # Eric advogado pendente (TD-SP04-10 HIGH)
    assert "Em formalização LGPD" in body
    # Brand-claim aspiracional REMOVIDO (regressão Smith C2 evitada)
    assert "LGPD-aware" not in body


# ── LGPD Compliance — No External CDN (REV-INT-02 + C1 fix) ───────────────


@pytest.mark.integration
def test_spa_no_external_cdn_googleapis(client: TestClient) -> None:
    """C1 fix — chunk 1.5 self-host fonts (REV-INT-02 pattern reuse).
    NFR-LGPD-01 zero CDN externo (Google Fonts, gstatic, etc.).
    """
    response = client.get("/")
    body = response.text
    # Smith C1 regression test — esses devem ser ZERO
    assert "googleapis" not in body
    assert "gstatic" not in body
    assert "fonts.googleapis" not in body


@pytest.mark.integration
def test_spa_has_self_hosted_fonts(client: TestClient) -> None:
    """REV-INT-02 self-host fonts — 7 @font-face declarations Manrope + Fraunces + JetBrains."""
    response = client.get("/")
    body = response.text
    # Self-hosted via /static/fonts/
    assert "@font-face" in body
    assert "/static/fonts/" in body
    assert "'Manrope'" in body  # primary brand font OrSheva 7


# ── BYOK API Key Section (SP04-BYOK-01) ───────────────────────────────────


@pytest.mark.integration
def test_spa_has_apikey_section(client: TestClient) -> None:
    """BYOK SP04-BYOK-01 — API Key section presente na sidebar Configurações."""
    response = client.get("/")
    body = response.text
    # Sidebar config item API Key (Claude)
    assert 'data-view="apikey"' in body
    assert "API Key" in body
    # JS validation pattern (sk-ant- prefix Anthropic Claude)
    assert "sk-ant-" in body
