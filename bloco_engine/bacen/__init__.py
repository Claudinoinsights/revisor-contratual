"""bloco_engine/bacen — wrapper python-bcb com cache + retry + fallback.

API pública (FR-BACEN-01..03):
  - BacenClient.fetch_taxa_modalidade(modalidade, mes_ref) -> BacenData
  - Exceções: BacenError, ModalidadeNaoSuportada, BacenFetchExhausted

Cache: diskcache TTL 30 dias + fallback "última taxa conhecida".
NFR-LGPD-01: única origem HTTP = api.bcb.gov.br.
"""

from bloco_engine.bacen.client import (
    ALLOWED_HOST,
    CACHE_TTL_SECONDS,
    DEFAULT_CACHE_DIR,
    FONTE_URL_TEMPLATE,
    BacenClient,
    BacenError,
    BacenFetchExhausted,
    ModalidadeNaoSuportada,
)

__all__ = [
    "BacenClient",
    "BacenError",
    "BacenFetchExhausted",
    "ModalidadeNaoSuportada",
    "ALLOWED_HOST",
    "CACHE_TTL_SECONDS",
    "DEFAULT_CACHE_DIR",
    "FONTE_URL_TEMPLATE",
]
