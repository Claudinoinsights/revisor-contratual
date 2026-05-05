"""Testes unit bloco_vault — schema, repository, busca híbrida RRF, scrapers.

Estratégia: 100% offline.
  - sqlite ':memory:' por teste (isolamento total)
  - embedder_fn = zero_embedder (zero vectors 768 dims)
  - httpx_fn mockada com HTML pré-gravado em tests/fixtures/scraper_html/
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

import pytest

from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_vault import (
    EMBEDDING_DIMS,
    JurisprudenciaNotFound,
    buscar_hibrida,
    count,
    get_by_id_doc,
    insert_jurisprudencia,
    list_all,
    open_vault,
    serialize_embedding,
    zero_embedder,
)
from bloco_vault.scrapers import (
    ALLOWED_HOSTS,
    ScraperHostNotAllowed,
    ScraperParseError,
    assert_host_allowed,
    scrape_stf_sumulas_vinculantes,
    scrape_stj_sumulas,
)

pytestmark = [pytest.mark.unit]

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "scraper_html"


# ─────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def conn() -> sqlite3.Connection:
    """Connection sqlite ':memory:' com vault inicializado."""
    return open_vault(":memory:")


def _make_item(
    id_doc: str,
    *,
    ementa: str = "É permitida a capitalização mensal de juros em contratos bancários PT-BR.",
    court_id: str = "STJ",
    peso_vinculacao: int = 3,
    binding: bool = False,
) -> JurisprudenciaItem:
    return JurisprudenciaItem(
        id_doc=id_doc,
        court_id=court_id,
        tipo_doc="SUMULA",
        numero=id_doc.split("-")[1].lstrip("S"),
        binding=binding,
        peso_vinculacao=peso_vinculacao,
        legal_topic_principal="capitalizacao_juros",
        modalidade_relacionada=["CDC_VEICULOS_PF"],
        ano_julgamento=2010,
        ementa=ementa,
        texto_completo=ementa + " (texto completo)",
        indexed_at=datetime(2024, 1, 1),
        vigente_em=None,
        superseded_by=None,
        data_ultima_validacao=date.today(),
    )


# ─────────────────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────────────────


class TestSchema:
    def test_init_vault_idempotente(self, conn: sqlite3.Connection) -> None:
        # Re-init não deve falhar
        from bloco_vault.schema import init_vault

        init_vault(conn)
        init_vault(conn)
        # Tabela existe
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jurisprudencia'")
        assert cur.fetchone() is not None

    def test_jurisp_vec_virtual_table_existe(self, conn: sqlite3.Connection) -> None:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE name='jurisp_vec'")
        assert cur.fetchone() is not None

    def test_embedding_dims_constante(self) -> None:
        assert EMBEDDING_DIMS == 768


# ─────────────────────────────────────────────────────────────────────
# Embedder
# ─────────────────────────────────────────────────────────────────────


class TestEmbedder:
    def test_zero_embedder_dim_correto(self) -> None:
        v = zero_embedder("texto qualquer")
        assert len(v) == EMBEDDING_DIMS
        assert all(x == 0.0 for x in v)

    def test_serialize_embedding_dim_correto(self) -> None:
        blob = serialize_embedding([0.0] * EMBEDDING_DIMS)
        assert len(blob) == EMBEDDING_DIMS * 4  # float32 = 4 bytes

    def test_serialize_embedding_dim_errado_levanta(self) -> None:
        with pytest.raises(ValueError, match="dim mismatch"):
            serialize_embedding([0.0] * 100)

    def test_serialize_embedding_rejeita_nan(self) -> None:
        """F-VAULT-LOW-01 hardening: NaN é bug a investigar (sentence-transformers nunca produz com normalize=True)."""
        bad = [float("nan")] + [0.0] * (EMBEDDING_DIMS - 1)
        with pytest.raises(ValueError, match="NaN ou Inf"):
            serialize_embedding(bad)

    def test_serialize_embedding_rejeita_inf(self) -> None:
        """F-VAULT-LOW-01 hardening: Inf indica overflow ou bug — sqlite-vec aceita silenciosamente."""
        bad = [float("inf")] + [0.0] * (EMBEDDING_DIMS - 1)
        with pytest.raises(ValueError, match="NaN ou Inf"):
            serialize_embedding(bad)


# ─────────────────────────────────────────────────────────────────────
# Repository
# ─────────────────────────────────────────────────────────────────────


class TestRepository:
    def test_insert_e_get_round_trip(self, conn: sqlite3.Connection) -> None:
        item = _make_item("STJ-S539")
        rowid = insert_jurisprudencia(conn, item, embedder_fn=zero_embedder)
        assert rowid == 1

        recovered = get_by_id_doc(conn, "STJ-S539")
        assert recovered.id_doc == "STJ-S539"
        assert recovered.court_id == "STJ"
        assert recovered.peso_vinculacao == 3
        assert recovered.modalidade_relacionada == ["CDC_VEICULOS_PF"]

    def test_get_inexistente_levanta(self, conn: sqlite3.Connection) -> None:
        with pytest.raises(JurisprudenciaNotFound):
            get_by_id_doc(conn, "STJ-S999")

    def test_count_inicial_zero(self, conn: sqlite3.Connection) -> None:
        assert count(conn) == 0

    def test_insert_duplicado_levanta_integrity(self, conn: sqlite3.Connection) -> None:
        item = _make_item("STJ-S539")
        insert_jurisprudencia(conn, item, embedder_fn=zero_embedder)
        with pytest.raises(sqlite3.IntegrityError):
            insert_jurisprudencia(conn, item, embedder_fn=zero_embedder)

    def test_list_all_preserva_ordem_insercao(self, conn: sqlite3.Connection) -> None:
        for n in ("539", "472", "297"):
            insert_jurisprudencia(conn, _make_item(f"STJ-S{n}"), embedder_fn=zero_embedder)
        ids = [item.id_doc for item in list_all(conn)]
        assert ids == ["STJ-S539", "STJ-S472", "STJ-S297"]


# ─────────────────────────────────────────────────────────────────────
# Busca híbrida + RRF
# ─────────────────────────────────────────────────────────────────────


class TestBuscaHibrida:
    def test_db_vazio_retorna_lista_vazia(self, conn: sqlite3.Connection) -> None:
        result = buscar_hibrida(
            conn,
            "capitalização juros",
            uf_contrato="BA",
            data_assinatura_contrato=date(2024, 3, 15),
            embedder_fn=zero_embedder,
        )
        assert result.docs == []
        assert result.top_k == 10
        assert result.latencia_ms >= 0

    def test_query_vazia_levanta(self, conn: sqlite3.Connection) -> None:
        with pytest.raises(ValueError, match="vazia"):
            buscar_hibrida(
                conn, "  ",
                uf_contrato="BA",
                data_assinatura_contrato=date(2024, 3, 15),
                embedder_fn=zero_embedder,
            )

    def test_top_k_zero_levanta(self, conn: sqlite3.Connection) -> None:
        with pytest.raises(ValueError, match="top_k"):
            buscar_hibrida(
                conn, "x",
                uf_contrato="BA",
                data_assinatura_contrato=date(2024, 3, 15),
                top_k=0,
                embedder_fn=zero_embedder,
            )

    def test_busca_recupera_doc_inserido(self, conn: sqlite3.Connection) -> None:
        item = _make_item(
            "STJ-S539",
            ementa="capitalização mensal de juros em contratos bancários é permitida pela jurisprudência",
        )
        insert_jurisprudencia(conn, item, embedder_fn=zero_embedder)

        result = buscar_hibrida(
            conn,
            "capitalização juros",
            uf_contrato="BA",
            data_assinatura_contrato=date(2024, 3, 15),
            embedder_fn=zero_embedder,
            top_k=5,
        )
        assert len(result.docs) == 1
        assert result.docs[0].id_doc == "STJ-S539"

    def test_busca_top_k_limita_resultado(self, conn: sqlite3.Connection) -> None:
        for n in range(1, 16):
            insert_jurisprudencia(
                conn,
                _make_item(f"STJ-S{n}", ementa=f"súmula sobre capitalização número {n} bancário"),
                embedder_fn=zero_embedder,
            )
        result = buscar_hibrida(
            conn,
            "capitalização",
            uf_contrato="BA",
            data_assinatura_contrato=date(2024, 3, 15),
            embedder_fn=zero_embedder,
            top_k=5,
        )
        assert len(result.docs) == 5

    def test_rrf_doc_em_ambas_listas_sobe(self, conn: sqlite3.Connection) -> None:
        """Doc cujo ementa contém EXATAMENTE a query DEVE aparecer em BM25;
        com zero_embedder todos têm distance 0 (vec ranking neutro).
        Logo, o doc relevante BM25 sobe via RRF."""
        # Doc relevante (BM25 dará score alto)
        item_relevante = _make_item(
            "STJ-S539",
            ementa="anatocismo capitalização mensal juros bancários jurisprudência consolidada",
        )
        # Docs irrelevantes
        for n in ("472", "297"):
            insert_jurisprudencia(
                conn,
                _make_item(f"STJ-S{n}", ementa=f"tema diferente da query número {n} qualquer texto"),
                embedder_fn=zero_embedder,
            )
        insert_jurisprudencia(conn, item_relevante, embedder_fn=zero_embedder)

        result = buscar_hibrida(
            conn,
            "anatocismo capitalização",
            uf_contrato="BA",
            data_assinatura_contrato=date(2024, 3, 15),
            embedder_fn=zero_embedder,
            top_k=3,
        )
        # Relevante deve estar em #1 ou #2 (RRF não garante #1 absoluto se vec dá tied scores)
        ids_top = [d.id_doc for d in result.docs[:2]]
        assert "STJ-S539" in ids_top


# ─────────────────────────────────────────────────────────────────────
# Scrapers — whitelist NFR-LGPD-01
# ─────────────────────────────────────────────────────────────────────


class TestScrapersWhitelist:
    def test_allowed_hosts_constante(self) -> None:
        assert "www.stj.jus.br" in ALLOWED_HOSTS
        assert "www.stf.jus.br" in ALLOWED_HOSTS
        assert len(ALLOWED_HOSTS) == 2  # MVP: só STJ + STF

    def test_assert_host_permite_whitelist(self) -> None:
        assert_host_allowed("https://www.stj.jus.br/sumulas")  # não levanta
        assert_host_allowed("https://www.stf.jus.br/sv")  # não levanta

    def test_assert_host_bloqueia_externo(self) -> None:
        with pytest.raises(ScraperHostNotAllowed, match="evil"):
            assert_host_allowed("https://evil.com/scrape")

    def test_assert_host_bloqueia_subdomain_nao_listado(self) -> None:
        # api.stj.jus.br ≠ www.stj.jus.br; whitelist é exata
        with pytest.raises(ScraperHostNotAllowed):
            assert_host_allowed("https://api.stj.jus.br/sumulas")


# ─────────────────────────────────────────────────────────────────────
# Scrapers — STJ + STF parsing
# ─────────────────────────────────────────────────────────────────────


class TestScraperSTJ:
    @pytest.mark.asyncio
    async def test_parsing_html_minimal_extrai_3_sumulas(self) -> None:
        html = (FIXTURES_DIR / "stj_sumulas_min.html").read_text(encoding="utf-8")

        async def fake_fetch(_url: str) -> str:
            return html

        items = await scrape_stj_sumulas(httpx_fn=fake_fetch)
        assert len(items) == 3
        ids = sorted(i.id_doc for i in items)
        assert ids == ["STJ-S297", "STJ-S472", "STJ-S539"]
        # Item irrelevante (class='outra') ignorado
        for item in items:
            assert item.court_id == "STJ"
            assert item.tipo_doc == "SUMULA"

    @pytest.mark.asyncio
    async def test_parsing_html_sem_sumulas_levanta(self) -> None:
        html = "<html><body><p>Nada relevante</p></body></html>"

        async def fake_fetch(_url: str) -> str:
            return html

        with pytest.raises(ScraperParseError, match="sumula"):
            await scrape_stj_sumulas(httpx_fn=fake_fetch)


class TestScraperSTF:
    @pytest.mark.asyncio
    async def test_parsing_html_minimal_extrai_sv(self) -> None:
        html = (FIXTURES_DIR / "stf_sv_min.html").read_text(encoding="utf-8")

        async def fake_fetch(_url: str) -> str:
            return html

        items = await scrape_stf_sumulas_vinculantes(httpx_fn=fake_fetch)
        # 3 SVs distintas (4, 17, 25); seen_numeros dedupe protege
        assert len(items) == 3
        for item in items:
            assert item.court_id == "STF"
            assert item.tipo_doc == "SUMULA_VINCULANTE"
            assert item.binding is True
            assert item.peso_vinculacao == 5  # SV é topo NFR-GOV-01

    @pytest.mark.asyncio
    async def test_parsing_html_sem_sv_levanta(self) -> None:
        html = "<html><body>nada</body></html>"

        async def fake_fetch(_url: str) -> str:
            return html

        with pytest.raises(ScraperParseError):
            await scrape_stf_sumulas_vinculantes(httpx_fn=fake_fetch)


# ─────────────────────────────────────────────────────────────────────
# Integração: scraper → repository → busca
# ─────────────────────────────────────────────────────────────────────


class TestIntegracaoScraperRepositorioBusca:
    @pytest.mark.asyncio
    async def test_scrape_stj_persistir_buscar(self, conn: sqlite3.Connection) -> None:
        html = (FIXTURES_DIR / "stj_sumulas_min.html").read_text(encoding="utf-8")

        async def fake_fetch(_url: str) -> str:
            return html

        items = await scrape_stj_sumulas(httpx_fn=fake_fetch)
        for item in items:
            insert_jurisprudencia(conn, item, embedder_fn=zero_embedder)

        assert count(conn) == 3

        result = buscar_hibrida(
            conn,
            "capitalização juros mensal",
            uf_contrato="BA",
            data_assinatura_contrato=date(2024, 3, 15),
            embedder_fn=zero_embedder,
            top_k=10,
        )
        ids = {d.id_doc for d in result.docs}
        # STJ-S539 menciona "capitalização" diretamente
        assert "STJ-S539" in ids
