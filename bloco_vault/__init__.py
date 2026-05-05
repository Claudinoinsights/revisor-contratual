"""bloco_vault — Vault de jurisprudência (sqlite-vec + busca híbrida + scrapers).

Componentes (FR-VAULT-01..04 + ADR-007):
  - schema.py — DDL sqlite-vec (vec0 768 dims) + jurisprudencia row table
  - repository.py — CRUD JurisprudenciaItem ↔ sqlite
  - busca.py — busca híbrida BM25 + vetorial + RRF k=60
  - embedder.py — wrapper sentence-transformers + injection
  - scrapers/ — STJ súmulas + STF SV (whitelist NFR-LGPD-01)

Tech debt aberta: TD-VAULT-LOAD-TEST (DP-08 sqlite-vec v0.1 load test 10k+ rows).
"""

from bloco_vault.busca import RRF_K_DEFAULT, TOP_K_DEFAULT, buscar_hibrida
from bloco_vault.embedder import (
    DEFAULT_MODEL_NAME,
    EMBEDDING_DIMS,
    EmbedderFn,
    serialize_embedding,
    zero_embedder,
)
from bloco_vault.repository import (
    JurisprudenciaNotFound,
    count,
    get_by_id_doc,
    insert_jurisprudencia,
    list_all,
)
from bloco_vault.schema import init_vault, open_vault

__all__ = [
    # schema
    "init_vault",
    "open_vault",
    "EMBEDDING_DIMS",
    # repository
    "insert_jurisprudencia",
    "get_by_id_doc",
    "list_all",
    "count",
    "JurisprudenciaNotFound",
    # busca
    "buscar_hibrida",
    "RRF_K_DEFAULT",
    "TOP_K_DEFAULT",
    # embedder
    "EmbedderFn",
    "DEFAULT_MODEL_NAME",
    "serialize_embedding",
    "zero_embedder",
]
