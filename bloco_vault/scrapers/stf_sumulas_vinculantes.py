"""Scraper STF — Súmulas Vinculantes (FR-VAULT-03).

URL canônica: https://www.stf.jus.br/portal/cms/verTexto.asp?servico=jurisprudenciaSumulaVinculante
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

URL_STF_SV = "https://www.stf.jus.br/sumulas-vinculantes"


async def scrape_stf_sumulas_vinculantes(
    *,
    url: str = URL_STF_SV,
    httpx_fn: HttpxFn | None = None,
) -> list[JurisprudenciaItem]:
    """Scrapa Súmulas Vinculantes STF.

    Args:
        url: endpoint default STF SV.
        httpx_fn: injetável para testes.

    Returns:
        list[JurisprudenciaItem] — peso_vinculacao=5 (SV é o topo da matriz NFR-GOV-01).

    Raises:
        ScraperHostNotAllowed / ScraperParseError.
    """
    assert_host_allowed(url)
    fetch = get_httpx_fn(httpx_fn)
    html = await fetch(url)
    return _parse_stf_html(html)


def _parse_stf_html(html: str) -> list[JurisprudenciaItem]:
    soup = BeautifulSoup(html, "html.parser")
    sv_nodes = soup.find_all(class_=re.compile(r"(sumula|vinculante|sv)", re.IGNORECASE))
    if not sv_nodes:
        raise ScraperParseError(
            "Nenhum elemento STF SV encontrado. Estrutura mudou? Verificar seletor."
        )

    today = date.today()
    now = datetime.now()
    items: list[JurisprudenciaItem] = []
    seen_numeros: set[str] = set()
    for node in sv_nodes:
        text = node.get_text(separator=" ", strip=True)
        # Padrão "Súmula Vinculante NNN" ou "SV NNN"
        match = re.search(r"S[uú]mula\s+Vinculante\s+(\d+)|SV\s+(\d+)", text, re.IGNORECASE)
        if not match:
            continue
        numero = match.group(1) or match.group(2)
        if numero in seen_numeros:
            continue
        seen_numeros.add(numero)
        if len(text) < 20:
            continue
        items.append(
            JurisprudenciaItem(
                id_doc=f"STF-SV{numero}",
                court_id="STF",
                tipo_doc="SUMULA_VINCULANTE",
                numero=numero,
                binding=True,  # SV é vinculante por definição
                peso_vinculacao=5,  # topo da matriz NFR-GOV-01
                legal_topic_principal="indeterminado",
                modalidade_relacionada=[],
                ano_julgamento=today.year,
                ementa=text[:500],
                texto_completo=text,
                indexed_at=now,
                vigente_em=None,
                superseded_by=None,
                data_ultima_validacao=today,
            )
        )

    if not items:
        raise ScraperParseError("Nodes encontrados mas nenhum com formato 'Súmula Vinculante NNN'")
    return items
