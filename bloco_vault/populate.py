"""Idempotent vault population from bundled JSON datasets (ADR-012).

Per ADR-012 (Vault Data Bundling Strategy) — populates `vault.db` from
bundled `bloco_vault/data/sumulas-stj.json` + `sumulas-stf-vinculantes.json`
on app startup, but only if the vault is missing or empty (idempotent).

Conversion mapping (`SumulaSTJ` / `SumulaVinculanteSTF` → `JurisprudenciaItem`):
- STJ Súmula → tipo_doc=SUMULA, peso_vinculacao=3, binding=False (persuasiva)
- STF SV    → tipo_doc=SUMULA_VINCULANTE, peso_vinculacao=5, binding=True

Story: VAULT-FIX-01 (Sprint 03 Phase 0).
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path
from typing import TypedDict

from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_vault.data_schema import SumulaSTJ, SumulaVinculanteSTF, VaultDataset
from bloco_vault.embedder import EmbedderFn
from bloco_vault.repository import insert_jurisprudencia
from bloco_vault.schema import open_vault

logger = logging.getLogger(__name__)

# Bundled data dir (next to this module). Production override via parameter.
BUNDLED_DATA_DIR = Path(__file__).parent / "data"

# STJ area → legal_topic_principal (placeholder taxonomy until ML enrichment Sprint 04+)
_STJ_AREA_TO_TOPIC: dict[str, str] = {
    "civil": "civil_geral",
    "penal": "penal_geral",
    "processual_civil": "processual_civil_geral",
    "processual_penal": "processual_penal_geral",
    "tributario": "tributario_geral",
    "trabalhista": "trabalhista_geral",
    "administrativo": "administrativo_geral",
    "outras": "outras",
}

# Fallback ano_julgamento quando data_aprovacao=None (algumas súmulas antigas sem data documented)
_FALLBACK_ANO_JULGAMENTO = 2000


class PopulateResult(TypedDict):
    """Resultado de `populate_vault_if_needed()`.

    populated: True se inseriu entries; False se idempotent skip.
    stj_count/stf_count: contagem de itens inseridos (0 se skip).
    skipped_reason: motivo do skip (None se populated=True).
    """

    populated: bool
    stj_count: int
    stf_count: int
    skipped_reason: str | None


def _stj_to_jurisprudencia(
    item: SumulaSTJ, *, today: date, now: datetime
) -> JurisprudenciaItem:
    """Map SumulaSTJ → JurisprudenciaItem (peso=3, binding=False)."""
    return JurisprudenciaItem(
        id_doc=f"STJ-S{item.numero}",
        court_id="STJ",
        tipo_doc="SUMULA",
        numero=str(item.numero),
        binding=False,
        peso_vinculacao=3,
        legal_topic_principal=_STJ_AREA_TO_TOPIC.get(item.area, "outras"),
        modalidade_relacionada=[],
        ano_julgamento=(
            item.data_aprovacao.year if item.data_aprovacao else _FALLBACK_ANO_JULGAMENTO
        ),
        ementa=item.texto,
        texto_completo=item.texto,
        indexed_at=now,
        vigente_em=today if item.revogada else None,
        superseded_by=None,
        data_ultima_validacao=today,
    )


def _stf_to_jurisprudencia(
    item: SumulaVinculanteSTF, *, today: date, now: datetime
) -> JurisprudenciaItem:
    """Map SumulaVinculanteSTF → JurisprudenciaItem (peso=5, binding=True)."""
    return JurisprudenciaItem(
        id_doc=f"STF-SV{item.numero}",
        court_id="STF",
        tipo_doc="SUMULA_VINCULANTE",
        numero=str(item.numero),
        binding=True,
        peso_vinculacao=5,
        legal_topic_principal="constitucional_geral",
        modalidade_relacionada=[],
        ano_julgamento=(
            item.data_aprovacao.year if item.data_aprovacao else _FALLBACK_ANO_JULGAMENTO
        ),
        ementa=item.texto,
        texto_completo=item.texto,
        indexed_at=now,
        vigente_em=today if item.revogada else None,
        superseded_by=None,
        data_ultima_validacao=today,
    )


def populate_vault_if_needed(
    vault_db: Path,
    data_dir: Path,
    *,
    embedder_fn: EmbedderFn | None = None,
) -> PopulateResult:
    """Popula vault.db a partir de bundled JSON datasets (idempotent).

    Detection rule:
      - vault.db missing OR jurisprudencia table vazia → POPULATE
      - jurisprudencia table com count > 0 → SKIP (idempotent)

    Args:
        vault_db: path para sqlite vault.db (criado se missing).
        data_dir: dir contendo `sumulas-stj.json` + `sumulas-stf-vinculantes.json`.
        embedder_fn: embedder injetável (default lazy sentence-transformers
            ~500MB). Use `zero_embedder` em testes/smoke para velocidade.

    Returns:
        PopulateResult com populated flag, counts e skipped_reason.
    """
    # Garantir parent dir do vault existe (Path.home() / .local / share / ...)
    vault_db.parent.mkdir(parents=True, exist_ok=True)

    # open_vault é idempotent (CREATE TABLE IF NOT EXISTS) — abre OU cria schema
    conn = open_vault(str(vault_db))
    try:
        existing = conn.execute("SELECT COUNT(*) FROM jurisprudencia").fetchone()[0]
    finally:
        conn.close()

    if existing > 0:
        reason = f"vault already has {existing} entries"
        logger.info("Vault already populated — skipping (%s)", reason)
        return PopulateResult(
            populated=False,
            stj_count=0,
            stf_count=0,
            skipped_reason=reason,
        )

    # Verificar bundled datasets disponíveis
    stj_path = data_dir / "sumulas-stj.json"
    stf_path = data_dir / "sumulas-stf-vinculantes.json"
    missing = [p.name for p in (stj_path, stf_path) if not p.exists()]
    if missing:
        reason = f"bundled datasets missing in {data_dir}: {missing}"
        logger.warning("Cannot populate vault — %s", reason)
        return PopulateResult(
            populated=False,
            stj_count=0,
            stf_count=0,
            skipped_reason=reason,
        )

    # Load + Pydantic validate (forward-compat schema_version "1.0")
    stj_dataset = VaultDataset.model_validate_json(stj_path.read_text(encoding="utf-8"))
    stf_dataset = VaultDataset.model_validate_json(stf_path.read_text(encoding="utf-8"))

    today = date.today()
    now = datetime.now()

    conn = open_vault(str(vault_db))
    stj_inserted = 0
    stf_inserted = 0
    try:
        for stj_item in stj_dataset.entries:
            if not isinstance(stj_item, SumulaSTJ):
                # Pydantic union pode resolver para STF se schema ambíguo — guard defensivo
                logger.warning("Entry STJ inesperado tipo %s, pulando", type(stj_item).__name__)
                continue
            juris = _stj_to_jurisprudencia(stj_item, today=today, now=now)
            insert_jurisprudencia(conn, juris, embedder_fn=embedder_fn)
            stj_inserted += 1

        for stf_item in stf_dataset.entries:
            if not isinstance(stf_item, SumulaVinculanteSTF):
                logger.warning("Entry STF inesperado tipo %s, pulando", type(stf_item).__name__)
                continue
            juris = _stf_to_jurisprudencia(stf_item, today=today, now=now)
            insert_jurisprudencia(conn, juris, embedder_fn=embedder_fn)
            stf_inserted += 1
    finally:
        conn.close()

    logger.info(
        "Vault populated from bundled — %d STJ + %d STF SV (last_updated STJ=%s, STF=%s)",
        stj_inserted,
        stf_inserted,
        stj_dataset.last_updated.isoformat(),
        stf_dataset.last_updated.isoformat(),
    )

    return PopulateResult(
        populated=True,
        stj_count=stj_inserted,
        stf_count=stf_inserted,
        skipped_reason=None,
    )


__all__ = ["BUNDLED_DATA_DIR", "PopulateResult", "populate_vault_if_needed"]
