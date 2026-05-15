"""Integration tests — populate_vault_if_needed idempotency (VAULT-FIX-01 Phase E).

3 cenários: vault missing, vault empty, vault populated.
zero_embedder usado em todos para evitar download sentence-transformers (~500MB).
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_vault import insert_jurisprudencia, open_vault, zero_embedder
from bloco_vault.populate import BUNDLED_DATA_DIR, populate_vault_if_needed

pytestmark = [pytest.mark.integration]


def test_populate_when_vault_missing(tmp_path: Path) -> None:
    """Vault file não existe → populate cria e insere bundled entries."""
    vault_db = tmp_path / "vault.db"
    assert not vault_db.exists()

    result = populate_vault_if_needed(
        vault_db,
        BUNDLED_DATA_DIR,
        embedder_fn=zero_embedder,
    )

    assert result["populated"] is True
    # DATASET-CHANGELOG v1.2.0 (Story TD-VAULT-CURATED-DATASET-01):
    # STF SV expanded 5→62 (Wikipedia parse); STJ expanded 5→637 (Tesseract OCR
    # via VPS container revisor-prod-app on official STJ VerbetesSTJ.pdf)
    assert result["stj_count"] == 637
    assert result["stf_count"] == 62
    assert result["skipped_reason"] is None
    assert vault_db.exists()


def test_populate_idempotent_second_call(tmp_path: Path) -> None:
    """Segunda chamada após populate é noop (idempotency)."""
    vault_db = tmp_path / "vault.db"

    # First call — populates
    first = populate_vault_if_needed(
        vault_db,
        BUNDLED_DATA_DIR,
        embedder_fn=zero_embedder,
    )
    assert first["populated"] is True

    # Second call — skip
    second = populate_vault_if_needed(
        vault_db,
        BUNDLED_DATA_DIR,
        embedder_fn=zero_embedder,
    )
    assert second["populated"] is False
    assert second["stj_count"] == 0
    assert second["stf_count"] == 0
    assert second["skipped_reason"] is not None
    # DATASET-CHANGELOG v1.2.0 — 637 STJ + 62 STF SV = 699 entries
    assert "699 entries" in second["skipped_reason"]


def test_populate_when_vault_empty(tmp_path: Path) -> None:
    """Vault file existe mas tabela jurisprudencia vazia → populate procede."""
    vault_db = tmp_path / "vault.db"

    # Cria vault file via open_vault (schema only, zero entries)
    conn = open_vault(str(vault_db))
    conn.close()
    assert vault_db.exists()

    # populate deve detectar count==0 e popular
    result = populate_vault_if_needed(
        vault_db,
        BUNDLED_DATA_DIR,
        embedder_fn=zero_embedder,
    )
    assert result["populated"] is True
    # DATASET-CHANGELOG v1.2.0 — STJ 637 + STF SV 62
    assert result["stj_count"] == 637
    assert result["stf_count"] == 62


def test_populate_when_vault_already_populated(tmp_path: Path) -> None:
    """Vault file com entries pré-existentes → skip preserva count."""
    vault_db = tmp_path / "vault.db"

    # Insere 1 entry manual (simula vault parcialmente populado)
    conn = open_vault(str(vault_db))
    try:
        item = JurisprudenciaItem(
            id_doc="STJ-S999",
            court_id="STJ",
            tipo_doc="SUMULA",
            numero="999",
            binding=False,
            peso_vinculacao=3,
            legal_topic_principal="outras",
            modalidade_relacionada=[],
            ano_julgamento=2020,
            ementa="Súmula de teste com mais de vinte caracteres exigidos pelo schema.",
            texto_completo="Súmula de teste com mais de vinte caracteres exigidos pelo schema.",
            indexed_at=datetime.now(),
            vigente_em=None,
            superseded_by=None,
            data_ultima_validacao=date.today(),
        )
        insert_jurisprudencia(conn, item, embedder_fn=zero_embedder)
        count_before = conn.execute(
            "SELECT COUNT(*) FROM jurisprudencia"
        ).fetchone()[0]
    finally:
        conn.close()

    assert count_before == 1

    # populate deve detectar count>0 e fazer noop
    result = populate_vault_if_needed(
        vault_db,
        BUNDLED_DATA_DIR,
        embedder_fn=zero_embedder,
    )
    assert result["populated"] is False
    assert result["stj_count"] == 0
    assert result["stf_count"] == 0
    assert result["skipped_reason"] is not None
    assert "1 entries" in result["skipped_reason"]

    # Verificar zero re-insert (count preservado)
    conn = open_vault(str(vault_db))
    try:
        count_after = conn.execute(
            "SELECT COUNT(*) FROM jurisprudencia"
        ).fetchone()[0]
    finally:
        conn.close()
    assert count_after == count_before
