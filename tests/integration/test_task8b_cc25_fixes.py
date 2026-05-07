"""Integration tests CC.25 Trilha B+ fixes — Smith findings F-01 + F-05 + F-08.

Cobertura:
- F-01 fix: feature flag ENABLE_TEMA_1378_AUTO_CHECK condiciona registro do job 3
- F-05 fix: User-Agent + Accept-Language headers presentes em scraper httpx.Client
- F-08 fix: preserve fail_count quando estado atual é vermelho-via-fails (≥2)

Sessão 91 · CC.25 · Smith adversarial review apply-qa-fixes Trilha B+.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from bloco_backup import scheduler as scheduler_mod
from bloco_dataset import auto_trigger, scraper_tema_1378, tema_1378_state
from bloco_dataset.scraper_tema_1378 import (
    DEFAULT_HEADERS,
    ScraperError,
    scrape_tema_1378,
)


@pytest.fixture(autouse=True)
def _isolated_data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Path]:
    """Isola REVISOR_DATA_DIR + zera sleep + reseta state limpo entre tests."""
    monkeypatch.setenv("REVISOR_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(scraper_tema_1378.time, "sleep", lambda _s: None)
    yield tmp_path


# ── F-01 fix: feature flag ENABLE_TEMA_1378_AUTO_CHECK ────────────────────


@pytest.mark.integration
def test_scheduler_skips_tema_1378_when_flag_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F-01 fix: env var unset OR 'false' → tema_1378_check NÃO registrado."""
    monkeypatch.delenv("ENABLE_TEMA_1378_AUTO_CHECK", raising=False)
    sched = scheduler_mod.create_scheduler()
    job_ids = {job.id for job in sched.get_jobs()}
    assert "tema_1378_check" not in job_ids
    # Backup jobs continuam registrados independente da flag
    assert "backup_daily" in job_ids
    assert "backup_rotation" in job_ids


@pytest.mark.integration
def test_scheduler_skips_tema_1378_when_flag_explicit_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F-01 fix: env var explicit 'false' → tema_1378_check NÃO registrado."""
    monkeypatch.setenv("ENABLE_TEMA_1378_AUTO_CHECK", "false")
    sched = scheduler_mod.create_scheduler()
    job_ids = {job.id for job in sched.get_jobs()}
    assert "tema_1378_check" not in job_ids


@pytest.mark.integration
def test_scheduler_includes_tema_1378_when_flag_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F-01 fix: env var 'true' → tema_1378_check REGISTRADO."""
    monkeypatch.setenv("ENABLE_TEMA_1378_AUTO_CHECK", "true")
    sched = scheduler_mod.create_scheduler()
    job_ids = {job.id for job in sched.get_jobs()}
    assert "tema_1378_check" in job_ids


# ── F-05 fix: User-Agent + Accept-Language headers ────────────────────────


@pytest.mark.integration
def test_default_headers_constant_includes_user_agent() -> None:
    """F-05 fix: DEFAULT_HEADERS constant contém User-Agent + Accept-Language."""
    assert "User-Agent" in DEFAULT_HEADERS
    assert "Mozilla/5.0" in DEFAULT_HEADERS["User-Agent"]
    assert "revisor-contratual" in DEFAULT_HEADERS["User-Agent"]
    assert "Accept-Language" in DEFAULT_HEADERS
    assert "pt-BR" in DEFAULT_HEADERS["Accept-Language"]


@pytest.mark.integration
def test_http_get_passes_default_headers_to_client() -> None:
    """F-05 fix: httpx.Client é chamado com headers=DEFAULT_HEADERS."""
    captured_kwargs: dict = {}

    def _capturing_client(**kwargs: object) -> MagicMock:
        captured_kwargs.update(kwargs)
        client = MagicMock()
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=False)
        response = MagicMock()
        response.status_code = 200
        response.text = (
            '<html><body><div class="tema-status">Sem alterações</div></body></html>'
        )
        response.request = MagicMock()
        response.raise_for_status = MagicMock(return_value=None)
        client.get = MagicMock(return_value=response)
        return client

    with patch.object(httpx, "Client", side_effect=_capturing_client):
        scrape_tema_1378("http://test.local/tema")

    assert "headers" in captured_kwargs
    headers = captured_kwargs["headers"]
    assert "User-Agent" in headers
    assert "Mozilla/5.0" in headers["User-Agent"]
    assert "Accept-Language" in headers


# ── F-08 fix: preserve fail_count quando vermelho-via-fails ───────────────


@pytest.mark.integration
def test_auto_trigger_preserves_fail_count_when_red_via_fails(tmp_path: Path) -> None:
    """F-08 fix: vermelho fail_count=2 + scrape amarelo → fail_count PRESERVADO.

    Invariante Task 7 SOP-005: vermelho-via-fails-consecutivas requer ack manual
    explícito. Auto-downgrade silencioso é proibido.
    """
    audit = tmp_path / "audit.jsonl"
    # Setup: simular state pós 2 fails consecutivos (vermelho com fail_count=2)
    tema_1378_state.set_state(
        nivel="vermelho",
        mensagem="2 fails consecutivos",
        fail_count=2,
    )

    # Mock scraper retorna nivel amarelo (julgamento detectado)
    fake_result = {
        "nivel": "amarelo",
        "mensagem": "Tema 1378 — julgamento pautado para 15/06/2026",
        "julgamento_data": "15/06/2026",
        "tese_fixada": None,
    }
    with patch.object(auto_trigger, "scrape_tema_1378", return_value=fake_result):
        entry = auto_trigger.run_camada_1_check(audit_path=audit)

    assert entry["status"] == "success"
    assert entry["nivel_detectado"] == "amarelo"

    # F-08 invariant: state agora é amarelo MAS fail_count=2 PRESERVADO
    state = tema_1378_state.get_current()
    assert state["nivel"] == "amarelo"
    assert state["fail_count"] == 2  # NÃO foi resetado para 0


@pytest.mark.integration
def test_auto_trigger_resets_fail_count_when_amarelo_via_scrape_no_prior_red(
    tmp_path: Path,
) -> None:
    """F-08 invariant: NÃO em vermelho-via-fails → scrape success reseta normalmente.

    Cenário: state amarelo com fail_count=1 (1 fail isolado) + scrape detecta
    julgamento (amarelo) → fail_count zerado normalmente (não preserva, pois
    não está em vermelho-via-fails-consecutivas).
    """
    audit = tmp_path / "audit.jsonl"
    # Setup: state amarelo com fail_count=1 (NÃO é vermelho-via-fails)
    tema_1378_state.set_state(
        nivel="amarelo",
        mensagem="1 fail isolado",
        fail_count=1,
    )

    fake_result = {
        "nivel": "amarelo",
        "mensagem": "julgamento detectado",
        "julgamento_data": "01/01/2027",
        "tese_fixada": None,
    }
    with patch.object(auto_trigger, "scrape_tema_1378", return_value=fake_result):
        auto_trigger.run_camada_1_check(audit_path=audit)

    state = tema_1378_state.get_current()
    assert state["nivel"] == "amarelo"
    assert state["fail_count"] == 0  # Resetado normalmente (não é vermelho-via-fails)


@pytest.mark.integration
def test_auto_trigger_preserves_fail_count_when_red_with_tese_detected(
    tmp_path: Path,
) -> None:
    """F-08 invariant edge case: vermelho-via-fails + scrape detecta vermelho-via-tese.

    Mesmo se scrape retornar vermelho (tese fixada), fail_count vermelho-via-fails
    é preservado porque ainda requer ack manual SOP-005 explícito.
    """
    audit = tmp_path / "audit.jsonl"
    tema_1378_state.set_state(
        nivel="vermelho",
        mensagem="2 fails",
        fail_count=2,
    )

    fake_result = {
        "nivel": "vermelho",
        "mensagem": "Tema 1378 — tese fixada: ...",
        "julgamento_data": "15/06/2026",
        "tese_fixada": "Tese fixada teste",
    }
    with patch.object(auto_trigger, "scrape_tema_1378", return_value=fake_result):
        auto_trigger.run_camada_1_check(audit_path=audit)

    state = tema_1378_state.get_current()
    assert state["nivel"] == "vermelho"
    assert state["fail_count"] == 2  # Preservado
    assert state.get("tese_fixada") == "Tese fixada teste"  # Tese atualizada


@pytest.mark.integration
def test_auto_trigger_resets_fail_count_when_verde_via_scrape_after_red(
    tmp_path: Path,
) -> None:
    """F-08 invariant: se scrape retorna VERDE (não amarelo), reset_to_verde é chamado.

    reset_to_verde() Task 7 zera fail_count incondicionalmente — comportamento
    correto: scraper "tudo OK" deve ser autoritativo para ambient verde.
    """
    audit = tmp_path / "audit.jsonl"
    tema_1378_state.set_state(
        nivel="vermelho",
        mensagem="2 fails",
        fail_count=2,
    )

    fake_result = {
        "nivel": "verde",
        "mensagem": "Tema 1378 — sem alterações",
        "julgamento_data": None,
        "tese_fixada": None,
    }
    with patch.object(auto_trigger, "scrape_tema_1378", return_value=fake_result):
        auto_trigger.run_camada_1_check(audit_path=audit)

    state = tema_1378_state.get_current()
    assert state["nivel"] == "verde"
    assert state["fail_count"] == 0  # reset_to_verde zera incondicionalmente


# ── Sanity: ScraperError continua funcional pós-fixes ─────────────────────


@pytest.mark.integration
def test_http_get_preserves_user_agent_through_retries() -> None:
    """RR-01 fix (Smith CC.26): headers DEFAULT_HEADERS presentes em CADA tentativa retry.

    Cenário: 503 → 503 → 200 (retry success). Valida que User-Agent é preservado
    em todas as 3 chamadas httpx.Client (não só na primeira).
    """
    captured_calls: list[dict] = []

    response_503 = MagicMock()
    response_503.status_code = 503
    response_503.text = "Service Unavailable"
    response_503.request = MagicMock()

    response_200 = MagicMock()
    response_200.status_code = 200
    response_200.text = '<html><body><div class="tema-status">OK</div></body></html>'
    response_200.request = MagicMock()
    response_200.raise_for_status = MagicMock(return_value=None)

    call_count = [0]

    def _capturing_client(**kwargs: object) -> MagicMock:
        captured_calls.append(dict(kwargs))
        client = MagicMock()
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=False)
        # 1ª e 2ª tentativa retornam 503; 3ª retorna 200
        if call_count[0] < 2:
            client.get = MagicMock(return_value=response_503)
        else:
            client.get = MagicMock(return_value=response_200)
        call_count[0] += 1
        return client

    with patch.object(httpx, "Client", side_effect=_capturing_client):
        result = scrape_tema_1378("http://test.local/tema")

    # 3 chamadas (2x 503 + 1x 200)
    assert len(captured_calls) == 3
    # User-Agent presente em TODAS
    for call_kwargs in captured_calls:
        assert "headers" in call_kwargs
        assert "User-Agent" in call_kwargs["headers"]
        assert "Mozilla/5.0" in call_kwargs["headers"]["User-Agent"]
    # Resultado correto na 3ª tentativa
    assert result["nivel"] == "verde"


@pytest.mark.integration
def test_scrape_still_raises_scraper_error_on_404() -> None:
    """Sanity: F-05 (headers) não quebra fail-loud em 4xx."""
    response = MagicMock()
    response.status_code = 404
    response.text = "Not Found"
    response.request = MagicMock()

    def _client(**_kwargs: object) -> MagicMock:
        client = MagicMock()
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=False)
        client.get = MagicMock(return_value=response)
        return client

    with patch.object(httpx, "Client", side_effect=_client):
        with pytest.raises(ScraperError) as exc_info:
            scrape_tema_1378("http://test.local/tema")
    assert "404" in str(exc_info.value)
