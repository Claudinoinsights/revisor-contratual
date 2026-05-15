"""Scraper STF — Súmulas Vinculantes (FR-VAULT-03).

⚠️ ORFÃO — NÃO USADO EM RUNTIME (preservado para futuro)
─────────────────────────────────────────────────────────
Diagnose Neo 2026-05-15 (Story TD-VAULT-CURATED-DATASET-01): WAF anti-bot AWS
(`Server: awselb/2.0` + `x-amzn-waf-action: challenge` em jurisprudencia.stf.jus.br)
bloqueia deterministicamente scrape direto STF.

Endpoints testados:
- `www.stf.jus.br/sumulas-vinculantes` → 403 (awselb)
- `www.stf.jus.br/portal/cms/verTexto.asp?servico=...` → 403
- `portal.stf.jus.br/sumulasVinculantes/` → 200 mas SPA "erro-404"
- `jurisprudencia.stf.jus.br/` → 202 WAF challenge

Fonte alternativa adotada (offline curation): Wikipedia `Lista_de_súmulas_vinculantes`
(estruturado wikitable, comunidade jurídica curada) parsed via BeautifulSoup →
`bloco_vault/data/sumulas-stf-vinculantes.json` (62 SVs bundled, não scrape live).

Este módulo é preservado para uso futuro caso STF disponibilize API oficial OR
WAF rules sejam relaxadas. Para popular vault, usar `bloco_vault.populate.populate_vault_if_needed()`.

Ver: governance/stories/TD-VAULT-CURATED-DATASET-01.md +
     bloco_vault/data/DATASET-CHANGELOG.md (v1.1.0 entry)
─────────────────────────────────────────────────────────

URL canônica histórica: https://www.stf.jus.br/sumulas-vinculantes (Sprint 03 — agora 403)
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
