"""Scrapers base — whitelist NFR-LGPD-01 + httpx_fn injetável.

D-MOR-3.4-D: scrapers SOMENTE batem em hosts da whitelist constante (não config).
Alterar requer ADR. NFR-LGPD-01 enforced em código.
"""

from __future__ import annotations

from typing import Awaitable, Callable
from urllib.parse import urlparse

# Whitelist EXPLÍCITA — alterar requer ADR (NFR-LGPD-01)
ALLOWED_HOSTS: frozenset[str] = frozenset({"www.stj.jus.br", "www.stf.jus.br"})

# httpx_fn(url) -> str (HTML body)
HttpxFn = Callable[[str], Awaitable[str]]


class ScraperError(Exception):
    """Erro base de scraper."""


class ScraperHostNotAllowed(ScraperError):
    """Tentativa de bater em host fora da whitelist NFR-LGPD-01."""


class ScraperParseError(ScraperError):
    """HTML malformado ou estrutura inesperada (anti-padrão silent fail)."""


def assert_host_allowed(url: str) -> None:
    """Bloqueia URLs fora da whitelist. Levanta ScraperHostNotAllowed caso contrário."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host not in ALLOWED_HOSTS:
        raise ScraperHostNotAllowed(
            f"Host {host!r} fora da whitelist NFR-LGPD-01 {sorted(ALLOWED_HOSTS)}. "
            "Alterar whitelist requer ADR."
        )


async def _default_httpx_fetch(url: str) -> str:
    """Fetch HTTP real via httpx (lazy import). Bloqueado se host fora whitelist."""
    assert_host_allowed(url)
    import httpx  # type: ignore[import-not-found]

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


def get_httpx_fn(httpx_fn: HttpxFn | None = None) -> HttpxFn:
    """Resolve httpx_fn: injetável OU default lazy."""
    return httpx_fn if httpx_fn is not None else _default_httpx_fetch
