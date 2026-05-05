"""DDL sqlite-vec — schema do vault de jurisprudência (ADR-007).

Layout:
  - jurisprudencia (rowid, id_doc UNIQUE, court_id, tipo_doc, ementa, texto_completo,
                    peso_vinculacao, ano_julgamento, vigente_em, superseded_by,
                    data_ultima_validacao, indexed_at, modalidade_relacionada_json,
                    legal_topic_principal, numero, binding)
  - jurisp_vec  (vec0 virtual table, embedding float[768] indexada por rowid)

Embedding: 768 dims (Legal-BERTimbau-sts-base default; configurável).
sqlite-vec v0.1.x — API estável. Usamos `embedding MATCH ?` para busca KNN.
"""

from __future__ import annotations

import sqlite3
from typing import Final

import sqlite_vec

EMBEDDING_DIMS: Final = 768

DDL_JURISPRUDENCIA: Final = """
CREATE TABLE IF NOT EXISTS jurisprudencia (
    rowid                       INTEGER PRIMARY KEY AUTOINCREMENT,
    id_doc                      TEXT UNIQUE NOT NULL,
    court_id                    TEXT NOT NULL,
    tipo_doc                    TEXT NOT NULL,
    numero                      TEXT NOT NULL,
    binding                     INTEGER NOT NULL,
    peso_vinculacao             INTEGER NOT NULL,
    legal_topic_principal       TEXT NOT NULL,
    modalidade_relacionada_json TEXT NOT NULL DEFAULT '[]',
    ano_julgamento              INTEGER NOT NULL,
    ementa                      TEXT NOT NULL,
    texto_completo              TEXT NOT NULL,
    indexed_at                  TEXT NOT NULL,
    vigente_em                  TEXT,
    superseded_by               TEXT,
    data_ultima_validacao       TEXT NOT NULL
);
"""

DDL_VEC: Final = f"""
CREATE VIRTUAL TABLE IF NOT EXISTS jurisp_vec USING vec0(
    embedding float[{EMBEDDING_DIMS}]
);
"""

DDL_INDEXES: Final = (
    "CREATE INDEX IF NOT EXISTS idx_jurisp_court ON jurisprudencia(court_id);",
    "CREATE INDEX IF NOT EXISTS idx_jurisp_topic ON jurisprudencia(legal_topic_principal);",
    "CREATE INDEX IF NOT EXISTS idx_jurisp_vigente ON jurisprudencia(vigente_em);",
)


def init_vault(conn: sqlite3.Connection) -> None:
    """Inicializa schema completo (tabelas + virtual vec + indexes).

    Args:
        conn: conexão sqlite com `enable_load_extension(True)` chamado antes.

    Idempotente: pode rodar múltiplas vezes (uses IF NOT EXISTS).
    """
    sqlite_vec.load(conn)
    conn.execute(DDL_JURISPRUDENCIA)
    conn.execute(DDL_VEC)
    for ddl in DDL_INDEXES:
        conn.execute(ddl)
    conn.commit()


def open_vault(db_path: str = ":memory:") -> sqlite3.Connection:
    """Abre conexão sqlite + carrega sqlite-vec extension + inicializa schema.

    Helper conveniente para testes e produção.
    """
    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    init_vault(conn)
    return conn
