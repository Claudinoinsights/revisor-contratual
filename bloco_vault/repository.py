"""Repository — CRUD JurisprudenciaItem ↔ sqlite (jurisprudencia + jurisp_vec).

Decisão D-MOR-3.4-E: scrapers retornam JurisprudenciaItem; persistência é
exclusiva do repository (separation of concerns).

Doc duplicado (mesmo id_doc): IntegrityError propagado — caller decide replace.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime

from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_vault.embedder import EmbedderFn, get_embedder, serialize_embedding


class JurisprudenciaNotFound(KeyError):
    """id_doc não existe no vault."""


def insert_jurisprudencia(
    conn: sqlite3.Connection,
    item: JurisprudenciaItem,
    *,
    embedder_fn: EmbedderFn | None = None,
) -> int:
    """Insere JurisprudenciaItem + embedding gerado da ementa.

    Args:
        conn: connection sqlite com vault inicializado.
        item: documento a persistir.
        embedder_fn: injetável (default lazy sentence-transformers).

    Returns:
        rowid do registro inserido.

    Raises:
        sqlite3.IntegrityError se id_doc já existe (caller decide replace).
        ValueError se embedding tem dim errado.
    """
    embedder = get_embedder(embedder_fn)
    embedding = embedder(item.ementa)
    embedding_blob = serialize_embedding(embedding)

    cur = conn.execute(
        """
        INSERT INTO jurisprudencia (
            id_doc, court_id, tipo_doc, numero, binding, peso_vinculacao,
            legal_topic_principal, modalidade_relacionada_json, ano_julgamento,
            ementa, texto_completo, indexed_at, vigente_em, superseded_by,
            data_ultima_validacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item.id_doc,
            item.court_id,
            item.tipo_doc,
            item.numero,
            int(item.binding),
            item.peso_vinculacao,
            item.legal_topic_principal,
            json.dumps(item.modalidade_relacionada),
            item.ano_julgamento,
            item.ementa,
            item.texto_completo,
            item.indexed_at.isoformat(),
            item.vigente_em.isoformat() if item.vigente_em else None,
            item.superseded_by,
            item.data_ultima_validacao.isoformat(),
        ),
    )
    rowid = cur.lastrowid
    if rowid is None:
        raise RuntimeError("INSERT não retornou lastrowid — sqlite anomalia")

    conn.execute(
        "INSERT INTO jurisp_vec(rowid, embedding) VALUES (?, ?)",
        (rowid, embedding_blob),
    )
    conn.commit()
    return rowid


def _row_to_item(row: sqlite3.Row | tuple) -> JurisprudenciaItem:
    """Converte row sqlite em JurisprudenciaItem Pydantic."""
    # Acesso por índice posicional — funciona com tuple OU Row
    (_, id_doc, court_id, tipo_doc, numero, binding, peso, topic,
     mod_json, ano, ementa, texto, indexed_at, vigente_em, superseded_by,
     data_ultima) = row

    return JurisprudenciaItem(
        id_doc=id_doc,
        court_id=court_id,
        tipo_doc=tipo_doc,
        numero=numero,
        binding=bool(binding),
        peso_vinculacao=peso,
        legal_topic_principal=topic,
        modalidade_relacionada=json.loads(mod_json),
        ano_julgamento=ano,
        ementa=ementa,
        texto_completo=texto,
        indexed_at=datetime.fromisoformat(indexed_at),
        vigente_em=date.fromisoformat(vigente_em) if vigente_em else None,
        superseded_by=superseded_by,
        data_ultima_validacao=date.fromisoformat(data_ultima),
    )


def get_by_id_doc(conn: sqlite3.Connection, id_doc: str) -> JurisprudenciaItem:
    """Busca por id_doc.

    Raises:
        JurisprudenciaNotFound se não existe.
    """
    cur = conn.execute("SELECT * FROM jurisprudencia WHERE id_doc = ?", (id_doc,))
    row = cur.fetchone()
    if row is None:
        raise JurisprudenciaNotFound(f"id_doc={id_doc!r} não encontrado no vault")
    return _row_to_item(row)


def list_all(conn: sqlite3.Connection) -> list[JurisprudenciaItem]:
    """Lista todos os documentos do vault (uso em testes / dev; cuidado em prod)."""
    cur = conn.execute("SELECT * FROM jurisprudencia ORDER BY rowid")
    return [_row_to_item(row) for row in cur.fetchall()]


def count(conn: sqlite3.Connection) -> int:
    """Total de documentos."""
    cur = conn.execute("SELECT COUNT(*) FROM jurisprudencia")
    return int(cur.fetchone()[0])
