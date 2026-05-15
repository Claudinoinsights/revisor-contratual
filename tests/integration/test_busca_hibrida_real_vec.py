"""Integration test — buscar_hibrida com sqlite-vec REAL (não zero_embedder mock).

Smith F-PROD-08 fix (D-DEV-S06-016): cobre gap de cobertura pytest que escapou
F-PROD-01 CRITICAL em produção. Tests existentes usam zero_embedder mock + injected
vec_rank fn, mascarando bug de sintaxe sqlite-vec em runtime real.

Este test EXIGE:
- sqlite-vec extension carregável (`pip install sqlite-vec`)
- sentence-transformers OU embedder real (fallback hash-based se ST indisponível)
- vault populated com sample mínimo (5+5 entries)
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from bloco_vault.busca import buscar_hibrida
from bloco_vault.embedder import EmbedderFn
from bloco_vault.populate import populate_vault_if_needed
from bloco_vault.schema import open_vault

pytestmark = [pytest.mark.integration]


def _hash_embedder_768() -> EmbedderFn:
    """Embedder determinístico 768d para tests (sem dep sentence-transformers).

    Não é semanticamente útil, mas EXERCITA o caminho real sqlite-vec MATCH +
    knn query syntax — que é o que F-PROD-01 falhava em produção.
    """
    import hashlib

    def _embed(text: str) -> list[float]:
        # 768 floats determinísticos derivados de hash do texto
        h = hashlib.sha256(text.encode("utf-8")).digest()
        # Expandir 32 bytes → 768 floats via repetição + variação
        floats: list[float] = []
        for i in range(768):
            byte_idx = i % 32
            shift = (i // 32) % 8
            val = ((h[byte_idx] >> shift) & 1) * 2.0 - 1.0  # ±1.0
            # Adicionar ruído baseado em posição
            val += (i * 0.001) % 0.1
            floats.append(val)
        return floats

    return _embed


def test_buscar_hibrida_sqlite_vec_real_syntax(tmp_path: Path) -> None:
    """F-PROD-01 regression: buscar_hibrida com sqlite-vec REAL não falha.

    Reproduz o caminho que crashava em produção com:
    "A LIMIT or 'k = ?' constraint is required on vec0 knn queries."

    Após D-DEV-S06-016 fix em busca.py:_vec_rank, query usa `AND k = ?` syntax.
    """
    vault_db = tmp_path / "vault_real.db"
    data_dir = Path("bloco_vault/data")

    # Pré-condição: data dir contém bundled JSONs (sumulas-stj.json + sumulas-stf-vinculantes.json)
    if not (data_dir / "sumulas-stj.json").exists():
        pytest.skip(f"Bundled data missing in {data_dir}")

    embedder = _hash_embedder_768()
    result = populate_vault_if_needed(vault_db, data_dir, embedder_fn=embedder)
    assert result["populated"] is True
    assert (result["stj_count"] + result["stf_count"]) > 0

    # Smoke real query — exercita sqlite-vec extension load + vec0 MATCH + k = ? syntax
    conn = open_vault(str(vault_db))
    try:
        busca_result = buscar_hibrida(
            conn,
            query="contrato de adesão consumidor",
            uf_contrato="SP",
            data_assinatura_contrato=date(2024, 1, 1),
            top_k=5,
            embedder_fn=embedder,
        )
    finally:
        conn.close()

    # Asserts: query executou sem exception SQL + retornou estrutura válida
    assert busca_result.query == "contrato de adesão consumidor"
    assert busca_result.uf_contrato == "SP"
    assert busca_result.top_k == 5
    assert isinstance(busca_result.docs, list)
    assert len(busca_result.docs) <= 5
    assert busca_result.latencia_ms >= 0
    # Sanity bound: deve completar em < 5s mesmo em hardware fraco
    assert busca_result.latencia_ms < 5000, (
        f"buscar_hibrida latency {busca_result.latencia_ms}ms excede sanity bound 5s"
    )


def test_buscar_hibrida_top_k_respected(tmp_path: Path) -> None:
    """top_k constraint passa corretamente para vec0 k = ? syntax."""
    vault_db = tmp_path / "vault_topk.db"
    data_dir = Path("bloco_vault/data")
    if not (data_dir / "sumulas-stj.json").exists():
        pytest.skip(f"Bundled data missing in {data_dir}")

    embedder = _hash_embedder_768()
    populate_vault_if_needed(vault_db, data_dir, embedder_fn=embedder)

    conn = open_vault(str(vault_db))
    try:
        for k in (1, 3, 10):
            r = buscar_hibrida(
                conn,
                query="súmula tributária",
                uf_contrato="SP",
                data_assinatura_contrato=date(2024, 1, 1),
                top_k=k,
                embedder_fn=embedder,
            )
            assert len(r.docs) <= k, f"top_k={k} excedido: {len(r.docs)} docs"
    finally:
        conn.close()
