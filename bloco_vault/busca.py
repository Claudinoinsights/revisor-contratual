"""Busca híbrida — BM25 + vetorial sqlite-vec + RRF fusion (FR-VAULT-02 + ADR-007).

RRF (Reciprocal Rank Fusion):
    score(d) = Σ_listas 1 / (k + rank_lista(d))

Default k=60 (literatura padrão). Documentos em ambas as listas (BM25 + vetorial)
sobem; documentos em só uma aparecem mas com menor peso.
"""

from __future__ import annotations

import re
import sqlite3
import time
from collections.abc import Sequence
from datetime import date

from rank_bm25 import BM25Okapi  # type: ignore[import-not-found]

from bloco_contratos.jurisprudencia import BuscaHibridaResult, JurisprudenciaItem
from bloco_vault.embedder import EmbedderFn, get_embedder, serialize_embedding
from bloco_vault.repository import _row_to_item

RRF_K_DEFAULT = 60
TOP_K_DEFAULT = 10


def _tokenize_pt(text: str) -> list[str]:
    """Tokenizer simples PT-BR — minúsculo + split por não-alfa."""
    return [t for t in re.split(r"\W+", text.lower()) if t]


def _bm25_rank(
    conn: sqlite3.Connection, query: str, top_k: int
) -> list[tuple[int, float]]:
    """Ranking BM25 sobre ementa+texto_completo. Retorna (rowid, score)."""
    cur = conn.execute("SELECT rowid, ementa || ' ' || texto_completo FROM jurisprudencia")
    rows = cur.fetchall()
    if not rows:
        return []
    rowids = [r[0] for r in rows]
    corpus = [_tokenize_pt(r[1]) for r in rows]
    bm25 = BM25Okapi(corpus)
    query_tokens = _tokenize_pt(query)
    if not query_tokens:
        return []
    scores = bm25.get_scores(query_tokens)
    paired = sorted(zip(rowids, scores), key=lambda x: x[1], reverse=True)
    return paired[:top_k]


def _vec_rank(
    conn: sqlite3.Connection, query_embedding: list[float], top_k: int
) -> list[tuple[int, float]]:
    """Ranking vetorial via sqlite-vec MATCH. Retorna (rowid, distance)."""
    blob = serialize_embedding(query_embedding)
    cur = conn.execute(
        "SELECT rowid, distance FROM jurisp_vec "
        "WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
        (blob, top_k),
    )
    return [(int(r[0]), float(r[1])) for r in cur.fetchall()]


def _rrf_fuse(
    bm25_results: Sequence[tuple[int, float]],
    vec_results: Sequence[tuple[int, float]],
    *,
    k: int = RRF_K_DEFAULT,
) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion. Retorna (rowid, rrf_score) ordenado desc."""
    rrf_scores: dict[int, float] = {}
    for rank, (rowid, _) in enumerate(bm25_results, start=1):
        rrf_scores[rowid] = rrf_scores.get(rowid, 0.0) + 1.0 / (k + rank)
    for rank, (rowid, _) in enumerate(vec_results, start=1):
        rrf_scores[rowid] = rrf_scores.get(rowid, 0.0) + 1.0 / (k + rank)
    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)


def _fetch_items_by_rowids(
    conn: sqlite3.Connection, rowids: Sequence[int]
) -> list[JurisprudenciaItem]:
    """Busca JurisprudenciaItem por lista de rowids preservando a ordem."""
    if not rowids:
        return []
    placeholders = ",".join("?" * len(rowids))
    cur = conn.execute(
        f"SELECT * FROM jurisprudencia WHERE rowid IN ({placeholders})",
        tuple(rowids),
    )
    by_rowid = {row[0]: _row_to_item(row) for row in cur.fetchall()}
    return [by_rowid[rid] for rid in rowids if rid in by_rowid]


def buscar_hibrida(
    conn: sqlite3.Connection,
    query: str,
    *,
    uf_contrato: str,
    data_assinatura_contrato: date,
    top_k: int = TOP_K_DEFAULT,
    binding_relax: bool = False,
    embedder_fn: EmbedderFn | None = None,
    rrf_k: int = RRF_K_DEFAULT,
) -> BuscaHibridaResult:
    """Busca híbrida BM25 + vetorial fundida por RRF.

    Args:
        conn: connection sqlite com vault inicializado.
        query: texto da busca (PT-BR).
        uf_contrato: UF do contrato (para BuscaHibridaResult; filtragem em STORY futura).
        data_assinatura_contrato: data do contrato (para resultado; vigência em STORY futura).
        top_k: número de resultados.
        binding_relax: relax requirement de binding (para resultado; lógica em STORY futura).
        embedder_fn: injetável (default lazy sentence-transformers).
        rrf_k: parâmetro RRF (60 default).

    Returns:
        BuscaHibridaResult com docs ordenados por RRF score desc.

    Raises:
        ValueError se query vazia ou top_k <= 0.
    """
    if not query or not query.strip():
        raise ValueError("query não pode ser vazia")
    if top_k <= 0:
        raise ValueError(f"top_k deve ser >= 1, recebido {top_k}")

    t0 = time.perf_counter()

    embedder = get_embedder(embedder_fn)
    query_embedding = embedder(query)

    # Buscamos um pouco mais em cada lista (3×top_k) para RRF ter material
    extended_k = top_k * 3
    bm25 = _bm25_rank(conn, query, extended_k)
    vec = _vec_rank(conn, query_embedding, extended_k)

    fused = _rrf_fuse(bm25, vec, k=rrf_k)[:top_k]
    fused_rowids = [rowid for rowid, _ in fused]
    docs = _fetch_items_by_rowids(conn, fused_rowids)

    latencia_ms = int((time.perf_counter() - t0) * 1000)

    return BuscaHibridaResult(
        query=query,
        uf_contrato=uf_contrato,
        data_assinatura_contrato=data_assinatura_contrato,
        binding_relax=binding_relax,
        top_k=top_k,
        docs=docs,
        latencia_ms=latencia_ms,
    )
