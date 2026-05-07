"""Integration tests Task 8b — Camada 1 scraper Tema 1378 + auto-trigger.

Cobertura:
- Scraper httpx retry exponencial (5xx retry, 4xx fail-loud)
- 3 estratégias parser fallback (CSS class → semantic tag → text-pattern)
- Fail-loud em zero matches
- auto_trigger.run_camada_1_check sucesso/falha → state machine integration
- 2 fails consecutivas → state vermelho (auto-CRITICAL Task 7 integration)

Sessão 91 · CC.24 · MVP-LEAN-01 Task 8b.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from bloco_dataset import auto_trigger, scraper_tema_1378, tema_1378_state
from bloco_dataset.scraper_tema_1378 import (
    ScraperError,
    _classify_snippet,
    scrape_tema_1378,
)


@pytest.fixture(autouse=True)
def _isolated_data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Path]:
    """Isola REVISOR_DATA_DIR + zera sleep para não atrasar testes 5xx retry."""
    monkeypatch.setenv("REVISOR_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(scraper_tema_1378.time, "sleep", lambda _s: None)
    yield tmp_path


# ── HTML fixtures ────────────────────────────────────────────────────────

HTML_CSS_CLASS = """
<html><body>
  <div class="tema-status">Sem alterações relevantes</div>
</body></html>
"""

HTML_SEMANTIC_TAG = """
<html><body>
  <article data-tema="1378">
    Julgamento pautado para 15/06/2026 — Tema 1378.
  </article>
</body></html>
"""

HTML_TEXT_PATTERN_VERDE = """
<html><body>
  <p>Conforme Tema 1378 do STJ, sem novidades nesta semana.</p>
</body></html>
"""

HTML_TEXT_PATTERN_TESE = """
<html><body>
  <p>Tema 1378: Tese fixada: Não se aplica capitalização mensal de juros
  em contratos bancários celebrados antes da MP 2.170-36 sem pactuação expressa.</p>
</body></html>
"""

HTML_GENERIC = "<html><body><p>Página irrelevante sem nenhum tema.</p></body></html>"


def _mock_client_factory(response: MagicMock) -> MagicMock:
    """Cria mock httpx.Client retornando ``response`` em .get()."""
    client = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    client.get = MagicMock(return_value=response)
    return client


def _make_response(status: int, text: str = "") -> MagicMock:
    response = MagicMock()
    response.status_code = status
    response.text = text
    response.request = MagicMock()
    if 400 <= status:
        response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                f"HTTP {status}",
                request=response.request,
                response=response,
            )
        )
    else:
        response.raise_for_status = MagicMock(return_value=None)
    return response


# ── 1. Scrape success ────────────────────────────────────────────────────


@pytest.mark.integration
def test_scrape_success_returns_state_dict() -> None:
    """Scrape OK + HTML válido → retorna dict com keys obrigatórias."""
    response = _make_response(200, HTML_CSS_CLASS)
    with patch.object(httpx, "Client", return_value=_mock_client_factory(response)):
        result = scrape_tema_1378("http://test.local/tema")
    assert "nivel" in result
    assert "mensagem" in result
    assert result["nivel"] in ("verde", "amarelo", "vermelho")


# ── 2. Retry 5xx → eventual fail ─────────────────────────────────────────


@pytest.mark.integration
def test_scrape_5xx_retry_then_fail() -> None:
    """3x 5xx → retry exponencial esgota → ScraperError."""
    response = _make_response(503, "Service Unavailable")
    with patch.object(httpx, "Client", return_value=_mock_client_factory(response)):
        with pytest.raises(ScraperError) as exc_info:
            scrape_tema_1378("http://test.local/tema")
    assert "Esgotadas" in str(exc_info.value) or "tentativas" in str(exc_info.value)


# ── 3. 4xx fail-loud (sem retry) ─────────────────────────────────────────


@pytest.mark.integration
def test_scrape_4xx_fail_loud() -> None:
    """404 → ScraperError imediato (não-retentável)."""
    response = _make_response(404, "Not Found")
    with patch.object(httpx, "Client", return_value=_mock_client_factory(response)):
        with pytest.raises(ScraperError) as exc_info:
            scrape_tema_1378("http://test.local/tema")
    assert "404" in str(exc_info.value)
    assert "não-retentável" in str(exc_info.value).lower() or "nao-retentavel" in str(
        exc_info.value
    ).lower()


# ── 4. Estratégia 1: CSS class match ─────────────────────────────────────


@pytest.mark.integration
def test_parser_strategy_1_css_class_match() -> None:
    """HTML com class CSS específica STJ → estratégia 1 detecta."""
    response = _make_response(200, HTML_CSS_CLASS)
    with patch.object(httpx, "Client", return_value=_mock_client_factory(response)):
        result = scrape_tema_1378("http://test.local/tema")
    assert result["nivel"] == "verde"  # snippet sem julgamento/tese


# ── 5. Estratégia 2: semantic tag match ──────────────────────────────────


@pytest.mark.integration
def test_parser_strategy_2_semantic_tag_match() -> None:
    """HTML sem CSS class mas com data-tema="1378" → estratégia 2 detecta julgamento."""
    response = _make_response(200, HTML_SEMANTIC_TAG)
    with patch.object(httpx, "Client", return_value=_mock_client_factory(response)):
        result = scrape_tema_1378("http://test.local/tema")
    assert result["nivel"] == "amarelo"
    assert result["julgamento_data"] == "15/06/2026"


# ── 6. Estratégia 3: text-pattern fallback ───────────────────────────────


@pytest.mark.integration
def test_parser_strategy_3_text_pattern_fallback() -> None:
    """HTML sem estrutura formal, apenas referência textual a Tema 1378 → estratégia 3."""
    response = _make_response(200, HTML_TEXT_PATTERN_VERDE)
    with patch.object(httpx, "Client", return_value=_mock_client_factory(response)):
        result = scrape_tema_1378("http://test.local/tema")
    assert result["nivel"] == "verde"


@pytest.mark.integration
def test_parser_strategy_3_detects_tese_fixada() -> None:
    """text-pattern detecta tese fixada → vermelho."""
    response = _make_response(200, HTML_TEXT_PATTERN_TESE)
    with patch.object(httpx, "Client", return_value=_mock_client_factory(response)):
        result = scrape_tema_1378("http://test.local/tema")
    assert result["nivel"] == "vermelho"
    assert result["tese_fixada"] is not None
    assert "capitalização mensal" in result["tese_fixada"].lower()


# ── 7. Zero matches → fail-loud ──────────────────────────────────────────


@pytest.mark.integration
def test_parser_zero_match_raises_scraper_error() -> None:
    """HTML genérico sem qualquer referência a Tema 1378 → ScraperError fail-loud."""
    response = _make_response(200, HTML_GENERIC)
    with patch.object(httpx, "Client", return_value=_mock_client_factory(response)):
        with pytest.raises(ScraperError) as exc_info:
            scrape_tema_1378("http://test.local/tema")
    assert "estratégias" in str(exc_info.value) or "estrategias" in str(exc_info.value)


# ── 8. auto_trigger sucesso → reset_to_verde ─────────────────────────────


@pytest.mark.integration
def test_auto_trigger_success_resets_state_to_verde(tmp_path: Path) -> None:
    """Scrape OK nivel verde → state.reset_to_verde + audit success."""
    audit = tmp_path / "audit.jsonl"
    # state inicial: amarelo (ex: previous fail) — verifica que reset_to_verde é chamado
    tema_1378_state.set_state(nivel="amarelo", mensagem="prev fail", fail_count=1)

    fake_result = {
        "nivel": "verde",
        "mensagem": "ok",
        "julgamento_data": None,
        "tese_fixada": None,
    }
    with patch.object(auto_trigger, "scrape_tema_1378", return_value=fake_result):
        entry = auto_trigger.run_camada_1_check(audit_path=audit)

    assert entry["status"] == "success"
    assert entry["nivel_detectado"] == "verde"
    state = tema_1378_state.get_current()
    assert state["nivel"] == "verde"
    assert state["fail_count"] == 0

    # Audit entry escrito
    assert audit.exists()
    lines = audit.read_text(encoding="utf-8").strip().splitlines()
    last = json.loads(lines[-1])
    assert last["type"] == "tema_1378_auto_check"
    assert last["status"] == "success"


# ── 9. auto_trigger ScraperError → increment_fail ────────────────────────


@pytest.mark.integration
def test_auto_trigger_failure_increments_fail_count(tmp_path: Path) -> None:
    """Scrape ScraperError → increment_fail (count 0 → 1, nivel amarelo)."""
    audit = tmp_path / "audit.jsonl"
    # Estado inicial verde com fail_count 0
    tema_1378_state.reset_to_verde()

    with patch.object(
        auto_trigger,
        "scrape_tema_1378",
        side_effect=ScraperError("Network down"),
    ):
        entry = auto_trigger.run_camada_1_check(audit_path=audit)

    assert entry["status"] == "fail_scraper"
    assert entry["fail_count"] == 1
    state = tema_1378_state.get_current()
    assert state["nivel"] == "amarelo"
    assert state["fail_count"] == 1


# ── 10. 2 fails consecutivos → state vermelho (auto-CRITICAL) ────────────


@pytest.mark.integration
def test_auto_trigger_2_failures_critical(tmp_path: Path) -> None:
    """2 ScraperError consecutivas → state vermelho (auto-trigger Task 7 integration)."""
    audit = tmp_path / "audit.jsonl"
    tema_1378_state.reset_to_verde()

    with patch.object(
        auto_trigger,
        "scrape_tema_1378",
        side_effect=ScraperError("STJ unreachable"),
    ):
        # Fail 1
        entry1 = auto_trigger.run_camada_1_check(audit_path=audit)
        # Fail 2 → escala vermelho
        entry2 = auto_trigger.run_camada_1_check(audit_path=audit)

    assert entry1["fail_count"] == 1
    assert entry2["fail_count"] == 2
    state = tema_1378_state.get_current()
    assert state["nivel"] == "vermelho"
    assert state["fail_count"] == 2


# ── 11. auto_trigger Exception genérico → fail_unexpected ────────────────


@pytest.mark.integration
def test_auto_trigger_unexpected_exception_caught(tmp_path: Path) -> None:
    """Exception não-ScraperError ainda é capturada (job NUNCA propaga)."""
    audit = tmp_path / "audit.jsonl"
    tema_1378_state.reset_to_verde()

    with patch.object(
        auto_trigger,
        "scrape_tema_1378",
        side_effect=RuntimeError("unexpected"),
    ):
        entry = auto_trigger.run_camada_1_check(audit_path=audit)

    assert entry["status"] == "fail_unexpected"
    assert entry["fail_count"] == 1
    assert "RuntimeError" in entry["error"]


# ── 12. _classify_snippet unit tests (rápido) ────────────────────────────


@pytest.mark.integration
def test_classify_snippet_julgamento_only_returns_amarelo() -> None:
    """Snippet com julgamento_data mas sem tese → amarelo."""
    result = _classify_snippet(
        "julgamento pautado para 01/01/2027",
        "<html>julgamento pautado para 01/01/2027</html>",
    )
    assert result["nivel"] == "amarelo"
    assert result["julgamento_data"] == "01/01/2027"
    assert result["tese_fixada"] is None
