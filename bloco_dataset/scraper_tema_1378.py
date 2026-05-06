"""Tema 1378 STJ scraper — Camada 1 (auto monitoring).

MVP-LEAN-01 Task 8b — implementação FR-MONITOR Camada 1.

Per ADR-013 §2.5 dual-layer monitoring:
- Camada 1 (este módulo): scrape periódico do site STJ via cron daily 02:30 UTC.
  Sucesso → reset_to_verde() OU set_state(nivel detectado).
  Falha → increment_fail() (Task 7 state machine cuida do auto-CRITICAL em 2 fails).
- Camada 2 (SOP-005 manual): maintainer ack via CLI --acknowledge.

Resilient parser: 3 estratégias fallback (CSS class → semantic tag → text-pattern).
Fail-loud em zero matches (anti-pattern proibido: silent fail mascara real-world drift).

Tech debt:
- TD-MVP-LEAN-08B-URL-VERIFY — DEFAULT_STJ_URL é placeholder; maintainer confirma
  URL real do STJ pré-deploy. Patterns de parser também precisam tuning empírico.

Decisão autônoma Neo (CC.24):
- httpx.Client sync (não AsyncClient) — APScheduler executa jobs em thread pool sync;
  asyncio.run() dentro do job adicionaria overhead sem benefício real (1 GET daily).
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# TD-MVP-LEAN-08B-URL-VERIFY: placeholder URL — confirmar com maintainer pré-deploy
DEFAULT_STJ_URL = "https://www.stj.jus.br/repetitivos/temas_repetitivos/"
DEFAULT_TIMEOUT_SECONDS = 30.0
RETRY_BACKOFF_SECONDS: tuple[int, ...] = (2, 4, 8)  # 3 retries exponencial

# Patterns text-extraction (case-insensitive)
RE_JULGAMENTO_DATE = re.compile(
    r"julgamento\s+(?:pautado|marcado|previsto)\s+para\s+(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)
RE_TESE_FIXADA = re.compile(
    r"tese\s+fixada[\s:]*([^\n<]{20,300})",
    re.IGNORECASE,
)


class ScraperError(Exception):
    """Raised quando scrape falha — HTTP non-recoverable OU zero matches."""


# ── Estratégias parser (fallback chain) ──────────────────────────────────


def _try_strategy_css_class(html: str) -> dict[str, Any] | None:
    """Estratégia 1: elementos com CSS class específica STJ.

    Patterns: ``class="tema-status"`` | ``class="tema-1378-info"`` | etc.
    """
    pattern = re.compile(
        r'<[^>]+class=["\'][^"\']*tema[-_](?:status|1378|repetitivo)[^"\']*["\'][^>]*>'
        r"([^<]+)<",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(html)
    if not match:
        return None
    snippet = match.group(1).strip()
    return _classify_snippet(snippet, html)


def _try_strategy_semantic_tag(html: str) -> dict[str, Any] | None:
    """Estratégia 2: tag semantic com data-attribute.

    Pattern: ``<article data-tema="1378">`` | ``<section data-tema="1378">``.
    """
    pattern = re.compile(
        r'<(?:article|section|div)[^>]+data-tema=["\']1378["\'][^>]*>'
        r"(.*?)</(?:article|section|div)>",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(html)
    if not match:
        return None
    snippet = match.group(1).strip()
    return _classify_snippet(snippet, html)


def _try_strategy_text_pattern(html: str) -> dict[str, Any] | None:
    """Estratégia 3 (fallback): text-pattern regex no body raw.

    Procura referência a "Tema 1378" no HTML; se encontra, classifica via patterns.
    Último recurso — menos preciso que estratégias 1 e 2.
    """
    if "tema 1378" not in html.lower() and "1378" not in html:
        return None
    return _classify_snippet(html, html)


def _classify_snippet(snippet: str, full_html: str) -> dict[str, Any]:
    """Classifica snippet → state dict (nivel, mensagem, dados auxiliares)."""
    julgamento_match = RE_JULGAMENTO_DATE.search(snippet) or RE_JULGAMENTO_DATE.search(full_html)
    tese_match = RE_TESE_FIXADA.search(snippet) or RE_TESE_FIXADA.search(full_html)

    if tese_match:
        tese_text = tese_match.group(1).strip()[:200]
        return {
            "nivel": "vermelho",
            "mensagem": f"Tema 1378 — tese fixada: {tese_text[:150]}",
            "julgamento_data": julgamento_match.group(1) if julgamento_match else None,
            "tese_fixada": tese_text,
        }
    if julgamento_match:
        return {
            "nivel": "amarelo",
            "mensagem": f"Tema 1378 — julgamento pautado para {julgamento_match.group(1)}",
            "julgamento_data": julgamento_match.group(1),
            "tese_fixada": None,
        }
    return {
        "nivel": "verde",
        "mensagem": "Tema 1378 — sem alterações detectadas no scrape automático.",
        "julgamento_data": None,
        "tese_fixada": None,
    }


# ── HTTP layer (retry exponencial) ───────────────────────────────────────


def _http_get_with_retry(
    url: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """GET com retry exponencial 2s/4s/8s em 5xx ou connection error.

    4xx → fail-loud imediato (não-retentável, ex: 404 URL errada).
    """
    last_exc: Exception | None = None
    for attempt, backoff in enumerate(RETRY_BACKOFF_SECONDS, start=1):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.get(url)
                if 400 <= response.status_code < 500:
                    raise ScraperError(
                        f"HTTP {response.status_code} (não-retentável) em {url}"
                    )
                if 500 <= response.status_code < 600:
                    raise httpx.HTTPStatusError(
                        f"5xx tentativa {attempt}: {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                return response.text
        except ScraperError:
            raise
        except (
            httpx.HTTPStatusError,
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.NetworkError,
        ) as exc:
            last_exc = exc
            if attempt < len(RETRY_BACKOFF_SECONDS):
                time.sleep(backoff)
                continue
    raise ScraperError(
        f"Esgotadas {len(RETRY_BACKOFF_SECONDS)} tentativas para {url}: {last_exc}"
    ) from last_exc


# ── Public API ───────────────────────────────────────────────────────────


def scrape_tema_1378(url: str = DEFAULT_STJ_URL) -> dict[str, Any]:
    """Scrape Tema 1378 STJ — 3 estratégias parser fallback chain.

    Raises:
        ScraperError: HTTP 4xx, 5xx persistente, network error persistente,
            OU zero matches em todas as 3 estratégias.

    Returns:
        dict com chaves:
        - ``nivel``: "verde" | "amarelo" | "vermelho"
        - ``mensagem``: str descrição estado
        - ``julgamento_data``: str (DD/MM/YYYY) ou None
        - ``tese_fixada``: str ou None
    """
    html = _http_get_with_retry(url)

    result = _try_strategy_css_class(html)
    if result is not None:
        logger.info("scrape_tema_1378: estratégia 1 (CSS class) match nivel=%s", result["nivel"])
        return result

    result = _try_strategy_semantic_tag(html)
    if result is not None:
        logger.info(
            "scrape_tema_1378: estratégia 2 (semantic tag) match nivel=%s",
            result["nivel"],
        )
        return result

    result = _try_strategy_text_pattern(html)
    if result is not None:
        logger.info(
            "scrape_tema_1378: estratégia 3 (text-pattern) match nivel=%s",
            result["nivel"],
        )
        return result

    raise ScraperError(
        "scrape_tema_1378: 3 estratégias falharam. HTML sem padrões reconhecíveis "
        "(possível mudança no site STJ — revisar patterns ou URL)."
    )
