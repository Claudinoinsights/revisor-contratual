"""Embedder — wrapper sentence-transformers Legal-BERTimbau-sts-base (768 dims).

D-MOR-3.4-B: embedder_fn injetável → testes mockam com zero vectors.
Lazy import sentence-transformers (modelo ~500MB; só carrega quando produção).

Output: numpy.ndarray shape=(768,) float32 OU list[float] de 768 elementos.
"""

from __future__ import annotations

import math
import struct
from typing import Callable

from bloco_vault.schema import EMBEDDING_DIMS

# Modelo default — Legal-BERTimbau (PT-BR jurídico) ou multilingual fallback
DEFAULT_MODEL_NAME = "neuralmind/bert-base-portuguese-cased"

# Tipo de uma função embedder: recebe texto, devolve list[float] 768 dims
EmbedderFn = Callable[[str], list[float]]


def _default_embedder(text: str) -> list[float]:
    """Embedder padrão usando sentence-transformers (lazy import).

    Em produção: baixa modelo na primeira chamada (~500MB).
    Em testes: substitua por mock via injection.
    """
    from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]

    if not hasattr(_default_embedder, "_model"):
        _default_embedder._model = SentenceTransformer(DEFAULT_MODEL_NAME)  # type: ignore[attr-defined]
    embedding = _default_embedder._model.encode(text, normalize_embeddings=True)  # type: ignore[attr-defined]
    return [float(x) for x in embedding]


def zero_embedder(_text: str) -> list[float]:
    """Embedder mock — retorna vetor zero. Usado em testes para isolar BM25."""
    return [0.0] * EMBEDDING_DIMS


def serialize_embedding(embedding: list[float]) -> bytes:
    """Converte lista de floats em formato binário sqlite-vec (float[N] little-endian).

    Raises:
        ValueError: dim mismatch OU NaN/Inf detectado. sentence-transformers com
                    normalize_embeddings=True nunca produz NaN — qualquer NaN/Inf é bug
                    a investigar (sqlite-vec aceita silenciosamente, daí o guard explícito).
    """
    if len(embedding) != EMBEDDING_DIMS:
        raise ValueError(
            f"Embedding dim mismatch: esperado {EMBEDDING_DIMS}, recebido {len(embedding)}"
        )
    # F-VAULT-LOW-01 hardening: fail-fast se NaN/Inf — sqlite-vec aceita silenciosamente.
    if any(math.isnan(x) or math.isinf(x) for x in embedding):
        raise ValueError(
            "Embedding contém NaN ou Inf — invalido para indexação. "
            "Verificar se embedder está produzindo vetores normalizados."
        )
    return struct.pack(f"{EMBEDDING_DIMS}f", *embedding)


def get_embedder(embedder_fn: EmbedderFn | None = None) -> EmbedderFn:
    """Resolve embedder: injetável OU default lazy."""
    return embedder_fn if embedder_fn is not None else _default_embedder
