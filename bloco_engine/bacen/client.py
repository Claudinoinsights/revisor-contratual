"""BACEN SGS client — wrapper sobre python-bcb com cache + retry + fallback.

Arquitetura (FR-BACEN-01..03):
  - python-bcb sgs.get(...) é a única superfície externa
  - diskcache TTL 30 dias (FR-BACEN-02)
  - tenacity retry exponencial 1→2→4→8→16s, max 5 tentativas (FR-BACEN-02)
  - Fallback "última taxa conhecida" com is_fallback=True (FR-BACEN-03)
  - NFR-LGPD-01: única origem HTTP permitida = api.bcb.gov.br (validada por whitelist no test)

Uso:
    client = BacenClient()
    data = client.fetch_taxa_modalidade("CDC_VEICULOS_PF", mes_ref="2025-12")
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from diskcache import Cache
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from bloco_contratos.contrato import BacenData, ModalidadeContrato

logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "revisor-contratual" / "bacen"
CACHE_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 dias (FR-BACEN-02)

CODIGOS_YAML = Path(__file__).parent / "codigos_bacen.yaml"

# NFR-LGPD-01: única origem HTTP permitida pelo bloco_engine
ALLOWED_HOST = "api.bcb.gov.br"
FONTE_URL_TEMPLATE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{sgs}/dados/ultimos/1?formato=json"


class BacenError(Exception):
    """Erro base BACEN client."""


class ModalidadeNaoSuportada(BacenError):
    """DP-03 — modalidade não mapeada no codigos_bacen.yaml."""


class BacenFetchExhausted(BacenError):
    """Retry esgotado E sem fallback no cache."""


def _load_codigos(path: Path = CODIGOS_YAML) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_sgs(modalidade: ModalidadeContrato) -> int:
    codigos = _load_codigos()
    taxas = codigos.get("taxas_credito_pf", {})
    if modalidade in taxas:
        return int(taxas[modalidade]["sgs_media_mensal"])
    nao_impl = codigos.get("nao_implementadas", {})
    if modalidade in nao_impl:
        raise NotImplementedError(
            f"Modalidade {modalidade!r} não suportada no MVP — "
            f"motivo: {nao_impl[modalidade]['motivo']}"
        )
    raise ModalidadeNaoSuportada(f"Modalidade {modalidade!r} não mapeada em codigos_bacen.yaml")


class BacenClient:
    """Wrapper python-bcb com cache + retry + fallback.

    Args:
        cache_dir: diretório do diskcache (default: ~/.cache/revisor-contratual/bacen)
        sgs_fetcher: callable injetável (default: python-bcb sgs.get) para teste
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        sgs_fetcher: Any = None,
    ) -> None:
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = Cache(str(self.cache_dir))
        self._sgs_fetcher = sgs_fetcher  # se None, lazy-importa python-bcb

    def _get_sgs_fetcher(self) -> Any:
        if self._sgs_fetcher is not None:
            return self._sgs_fetcher
        from bcb import sgs  # type: ignore[import-not-found]

        return sgs.get

    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _fetch_sgs_with_retry(self, sgs_code: int) -> Decimal:
        """Bate na rede com retry exponencial 1→2→4→8→16s (max 5 attempts)."""
        fetcher = self._get_sgs_fetcher()
        df = fetcher({"taxa": sgs_code}, last=1)
        # python-bcb retorna pandas DataFrame com coluna nomeada
        if df is None or len(df) == 0:
            raise BacenFetchExhausted(f"SGS {sgs_code} retornou vazio")
        valor = df.iloc[-1, 0]
        return Decimal(str(valor))

    def fetch_taxa_modalidade(
        self,
        modalidade: ModalidadeContrato,
        mes_ref: str,
    ) -> BacenData:
        """Busca taxa média BACEN para modalidade no mes_ref (formato YYYY-MM).

        Comportamento:
          1. Cache hit → retorna direto (is_fallback=False).
          2. Cache miss + rede OK → fetch + cache + retorna.
          3. Cache miss + rede falha → última taxa conhecida do cache (is_fallback=True).
          4. Sem fallback disponível → BacenFetchExhausted.

        Raises:
            ModalidadeNaoSuportada / NotImplementedError se modalidade não mapeada.
            BacenFetchExhausted se rede falhou e cache não tem fallback.
        """
        sgs_code = _resolve_sgs(modalidade)
        cache_key = f"{modalidade}:{mes_ref}"
        last_known_key = f"{modalidade}:last_known"

        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug("BACEN cache hit: %s", cache_key)
            return BacenData(**cached)

        try:
            taxa = self._fetch_sgs_with_retry(sgs_code)
        except (RetryError, ConnectionError, TimeoutError, OSError, BacenFetchExhausted) as exc:
            logger.warning("BACEN fetch falhou (%s) — tentando fallback", exc)
            fallback = self.cache.get(last_known_key)
            if fallback is None:
                raise BacenFetchExhausted(
                    f"Sem rede e sem fallback para {modalidade}/{mes_ref}"
                ) from exc
            data = BacenData(**fallback)
            return data.model_copy(update={"is_fallback": True, "fetched_at": datetime.now()})

        data = BacenData(
            codigo_sgs=sgs_code,
            modalidade=modalidade,
            mes_ref=mes_ref,
            taxa_media=str(taxa),
            fonte_url=FONTE_URL_TEMPLATE.format(sgs=sgs_code),
            fetched_at=datetime.now(),
            is_fallback=False,
        )
        payload = data.model_dump(mode="json")
        self.cache.set(cache_key, payload, expire=CACHE_TTL_SECONDS)
        self.cache.set(last_known_key, payload)  # sem expire — fallback permanente
        return data

    def close(self) -> None:
        self.cache.close()
