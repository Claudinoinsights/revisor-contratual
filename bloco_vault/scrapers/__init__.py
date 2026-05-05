"""bloco_vault/scrapers — coletores HTML jurisprudência (FR-VAULT-03 + NFR-LGPD-01).

MVP: STJ súmulas + STF SV. Scrapers TJ deferred para STORY futura.
"""

from bloco_vault.scrapers.base import (
    ALLOWED_HOSTS,
    HttpxFn,
    ScraperError,
    ScraperHostNotAllowed,
    ScraperParseError,
    assert_host_allowed,
)
from bloco_vault.scrapers.stf_sumulas_vinculantes import (
    URL_STF_SV,
    scrape_stf_sumulas_vinculantes,
)
from bloco_vault.scrapers.stj_sumulas import (
    URL_STJ_SUMULAS,
    scrape_stj_sumulas,
)

__all__ = [
    "scrape_stj_sumulas",
    "scrape_stf_sumulas_vinculantes",
    "URL_STJ_SUMULAS",
    "URL_STF_SV",
    "ALLOWED_HOSTS",
    "assert_host_allowed",
    "ScraperError",
    "ScraperHostNotAllowed",
    "ScraperParseError",
    "HttpxFn",
]
