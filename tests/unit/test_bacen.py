"""Testes unit bloco_engine/bacen — cache, retry, fallback, modalidades.

Estratégia: 100% offline. python-bcb sgs.get é injetado via construtor (sgs_fetcher).
Nenhum teste deve bater api.bcb.gov.br — CI roda sem rede.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from bloco_engine.bacen import (
    ALLOWED_HOST,
    FONTE_URL_TEMPLATE,
    BacenClient,
    BacenFetchExhausted,
    ModalidadeNaoSuportada,
)


# ─────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────


class _FakeDataFrame:
    """Mock minimal pandas-like — só implementa len() + iloc[-1, 0]."""

    def __init__(self, value: float | str) -> None:
        self._value = value

    def __len__(self) -> int:
        return 1

    @property
    def iloc(self) -> Any:
        outer = self

        class _ILoc:
            def __getitem__(self, _key: tuple[int, int]) -> float | str:
                return outer._value

        return _ILoc()


def _make_fetcher(value: float | str | None, *, raises: type[Exception] | None = None) -> Any:
    """Retorna callable que mimica python-bcb sgs.get."""
    mock = MagicMock()
    if raises is not None:
        mock.side_effect = raises("simulado")
    elif value is None:
        mock.return_value = _FakeDataFrame(0.0)
        mock.return_value.__class__.__len__ = lambda self: 0
    else:
        mock.return_value = _FakeDataFrame(value)
    return mock


@pytest.fixture
def tmp_cache(tmp_path: Path) -> Path:
    return tmp_path / "bacen_cache"


@pytest.fixture
def client_ok(tmp_cache: Path) -> BacenClient:
    fetcher = _make_fetcher(2.15)  # taxa fictícia 2.15% a.m.
    return BacenClient(cache_dir=tmp_cache, sgs_fetcher=fetcher)


# ─────────────────────────────────────────────────────────────────────
# Happy path
# ─────────────────────────────────────────────────────────────────────


class TestHappyPath:
    def test_fetch_veiculos_pf_retorna_bacen_data(self, client_ok: BacenClient) -> None:
        data = client_ok.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-12")

        assert data.codigo_sgs == 25471
        assert data.modalidade == "CDC_VEICULOS_PF"
        assert data.mes_ref == "2025-12"
        assert Decimal(data.taxa_media) == Decimal("2.15")
        assert data.is_fallback is False
        assert isinstance(data.fetched_at, datetime)
        client_ok.close()

    def test_fonte_url_aponta_para_api_bcb(self, client_ok: BacenClient) -> None:
        data = client_ok.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-11")
        assert ALLOWED_HOST in data.fonte_url
        assert data.fonte_url == FONTE_URL_TEMPLATE.format(sgs=25471)
        client_ok.close()

    def test_taxa_media_sempre_string_decimal_safe(self, client_ok: BacenClient) -> None:
        data = client_ok.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-10")
        # FR-CALC-01 — taxa_media é string parseável como Decimal
        Decimal(data.taxa_media)  # não levanta
        assert isinstance(data.taxa_media, str)
        client_ok.close()


# ─────────────────────────────────────────────────────────────────────
# Cache (FR-BACEN-02)
# ─────────────────────────────────────────────────────────────────────


class TestCache:
    def test_cache_hit_nao_chama_fetcher_segunda_vez(self, tmp_cache: Path) -> None:
        fetcher = _make_fetcher(1.99)
        client = BacenClient(cache_dir=tmp_cache, sgs_fetcher=fetcher)

        client.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-09")
        client.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-09")

        assert fetcher.call_count == 1  # segundo veio do cache
        client.close()

    def test_cache_miss_em_mes_diferente_chama_fetcher(self, tmp_cache: Path) -> None:
        fetcher = _make_fetcher(1.50)
        client = BacenClient(cache_dir=tmp_cache, sgs_fetcher=fetcher)

        client.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-08")
        client.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-07")

        assert fetcher.call_count == 2
        client.close()

    def test_cache_persiste_entre_clientes(self, tmp_cache: Path) -> None:
        fetcher_a = _make_fetcher(1.80)
        client_a = BacenClient(cache_dir=tmp_cache, sgs_fetcher=fetcher_a)
        client_a.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-06")
        client_a.close()

        # Segundo cliente apontando ao mesmo cache
        fetcher_b = _make_fetcher(99.99)  # nunca deve ser chamado
        client_b = BacenClient(cache_dir=tmp_cache, sgs_fetcher=fetcher_b)
        data = client_b.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-06")

        assert Decimal(data.taxa_media) == Decimal("1.80")
        assert fetcher_b.call_count == 0
        client_b.close()


# ─────────────────────────────────────────────────────────────────────
# Retry + Fallback (FR-BACEN-02 + FR-BACEN-03)
# ─────────────────────────────────────────────────────────────────────


class TestRetryAndFallback:
    def test_retry_recupera_apos_2_falhas(self, tmp_cache: Path) -> None:
        attempts = {"n": 0}

        def flaky_fetcher(_query: dict, last: int) -> _FakeDataFrame:  # noqa: ARG001
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise ConnectionError("rede oscilando")
            return _FakeDataFrame(2.50)

        client = BacenClient(cache_dir=tmp_cache, sgs_fetcher=flaky_fetcher)
        data = client.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-05")

        assert attempts["n"] == 3
        assert Decimal(data.taxa_media) == Decimal("2.50")
        assert data.is_fallback is False
        client.close()

    def test_fallback_ativa_quando_rede_falha_e_cache_tem_last_known(
        self, tmp_cache: Path
    ) -> None:
        # Sessão 1 — cache populado com sucesso
        ok_fetcher = _make_fetcher(2.00)
        client_a = BacenClient(cache_dir=tmp_cache, sgs_fetcher=ok_fetcher)
        client_a.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-04")
        client_a.close()

        # Sessão 2 — rede falha, mas last_known existe
        broken_fetcher = MagicMock(side_effect=ConnectionError("offline"))
        client_b = BacenClient(cache_dir=tmp_cache, sgs_fetcher=broken_fetcher)
        data = client_b.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-03")  # mês NOVO

        assert data.is_fallback is True
        assert Decimal(data.taxa_media) == Decimal("2.00")
        # Mes_ref do fallback é do registro anterior (não o solicitado) — esperado
        client_b.close()

    def test_retry_esgotado_sem_fallback_levanta(self, tmp_cache: Path) -> None:
        broken_fetcher = MagicMock(side_effect=ConnectionError("offline"))
        client = BacenClient(cache_dir=tmp_cache, sgs_fetcher=broken_fetcher)

        with pytest.raises(BacenFetchExhausted):
            client.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-02")

        # Tenacity já tentou 5 vezes
        assert broken_fetcher.call_count == 5
        client.close()


# ─────────────────────────────────────────────────────────────────────
# Modalidades não suportadas (DP-03)
# ─────────────────────────────────────────────────────────────────────


class TestModalidadesNaoSuportadas:
    @pytest.mark.parametrize(
        "modalidade",
        ["CDC_BENS_PF", "CDC_IMOBILIARIO", "CARTAO_ROTATIVO"],
    )
    def test_modalidade_nao_implementada_levanta(
        self, modalidade: str, tmp_cache: Path
    ) -> None:
        fetcher = _make_fetcher(1.00)  # nunca deve ser chamado
        client = BacenClient(cache_dir=tmp_cache, sgs_fetcher=fetcher)

        with pytest.raises(NotImplementedError, match="DP-03|não suportada"):
            client.fetch_taxa_modalidade(modalidade, "2025-12")  # type: ignore[arg-type]

        assert fetcher.call_count == 0
        client.close()


# ─────────────────────────────────────────────────────────────────────
# NFR-LGPD-01 — única origem HTTP permitida = api.bcb.gov.br
# ─────────────────────────────────────────────────────────────────────


class TestLGPDWhitelist:
    def test_fonte_url_template_aponta_apenas_para_api_bcb(self) -> None:
        url = FONTE_URL_TEMPLATE.format(sgs=12345)
        assert url.startswith("https://api.bcb.gov.br/")
        # Garantia defensiva: nenhuma outra origem permitida no template
        assert "://" + ALLOWED_HOST + "/" in url

    def test_allowed_host_constante_imutavel(self) -> None:
        # Whitelist é código, não config — alterar requer ADR.
        assert ALLOWED_HOST == "api.bcb.gov.br"


# ─────────────────────────────────────────────────────────────────────
# Edge cases — formato mês_ref + Decimal precision
# ─────────────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_mes_ref_formato_invalido_levanta_pydantic(
        self, client_ok: BacenClient
    ) -> None:
        from pydantic import ValidationError

        # client_ok injeta resposta válida; mes_ref formato errado falha no Pydantic
        with pytest.raises(ValidationError):
            client_ok.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025/12")
        client_ok.close()

    def test_taxa_decimal_preserva_precisao(self, tmp_cache: Path) -> None:
        # python-bcb tipicamente retorna float; convertemos via str(float)
        # garantindo que serializamos como string.
        fetcher = _make_fetcher(1.789012)
        client = BacenClient(cache_dir=tmp_cache, sgs_fetcher=fetcher)

        data = client.fetch_taxa_modalidade("CDC_VEICULOS_PF", "2025-01")
        # str(float) preserva representação curta determinística
        assert "1.789012" in data.taxa_media
        Decimal(data.taxa_media)  # parseável
        client.close()
