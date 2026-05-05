"""Scraper STJ — extrai súmulas do site oficial (FR-VAULT-03).

URL canônica: https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/Sumulas-do-STJ.aspx
(o link real exato é fora do escopo deste MVP — usamos parsing genérico de HTML).

Parsing minimal: extrai elementos com classe "sumula" ou estrutura similar.
HTML real evolui — robustez via fallback patterns.
"""

from __future__ import annotations

import re
from datetime import date, datetime

from bs4 import BeautifulSoup

from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_vault.scrapers.base import (
    HttpxFn,
    ScraperParseError,
    assert_host_allowed,
    get_httpx_fn,
)

URL_STJ_SUMULAS = "https://www.stj.jus.br/sumulas"


async def scrape_stj_sumulas(
    *,
    url: str = URL_STJ_SUMULAS,
    httpx_fn: HttpxFn | None = None,
) -> list[JurisprudenciaItem]:
    """Scrapa súmulas STJ e retorna lista de JurisprudenciaItem.

    Args:
        url: endpoint (default URL canônica STJ).
        httpx_fn: injetável para testes.

    Returns:
        list[JurisprudenciaItem] — não persiste no DB; caller chama repository.

    Raises:
        ScraperHostNotAllowed se host fora whitelist.
        ScraperParseError se HTML não tem súmulas reconhecíveis.
    """
    assert_host_allowed(url)
    fetch = get_httpx_fn(httpx_fn)
    html = await fetch(url)
    return _parse_stj_html(html)


def _parse_stj_html(html: str) -> list[JurisprudenciaItem]:
    """Parsing minimal — busca <li class="sumula"> ou <div class="sumula">."""
    soup = BeautifulSoup(html, "html.parser")
    sumula_nodes = soup.find_all(class_=re.compile(r"sumula", re.IGNORECASE))
    if not sumula_nodes:
        raise ScraperParseError(
            "Nenhum elemento class='sumula' encontrado no HTML STJ. "
            "Estrutura mudou? Verificar seletor."
        )

    today = date.today()
    now = datetime.now()
    items: list[JurisprudenciaItem] = []
    for node in sumula_nodes:
        numero_match = re.search(r"S[uú]mula\s+(\d+)", node.get_text(), re.IGNORECASE)
        if not numero_match:
            continue
        numero = numero_match.group(1)
        ementa_text = node.get_text(separator=" ", strip=True)
        if len(ementa_text) < 20:
            continue
        items.append(
            JurisprudenciaItem(
                id_doc=f"STJ-S{numero}",
                court_id="STJ",
                tipo_doc="SUMULA",
                numero=numero,
                binding=False,
                peso_vinculacao=3,
                legal_topic_principal="indeterminado",
                modalidade_relacionada=[],
                ano_julgamento=today.year,  # heurística — ano do scraping (sem info real)
                ementa=ementa_text[:500],
                texto_completo=ementa_text,
                indexed_at=now,
                vigente_em=None,
                superseded_by=None,
                data_ultima_validacao=today,
            )
        )

    if not items:
        raise ScraperParseError("Nodes encontrados mas nenhum com formato 'Súmula NNN'")
    return items
