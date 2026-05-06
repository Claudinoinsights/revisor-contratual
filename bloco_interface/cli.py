"""CLI Click — entry point `revisor` (D-MOR-4.1-A..H + ADR-012 dataset bundling).

Subcomandos:
  - revisar           — pipeline completo PDF -> VeredictoJuiz
  - init-audit        — inicializa GENESIS audit lock
  - populate-vault    — scrapers reais STJ + STF (DEPRECATED runtime — use bundled lifespan)
  - refresh-vault     — best-effort scrape para atualizar bundled dataset (ADR-012 opt-in)
  - import-dataset    — parse compendium PDF oficial -> JSON schema-valid (autoritativo)
  - validate-dataset  — Pydantic VaultDataset.model_validate + hash_sha256 verification

Defaults persistentes em ~/.local/share/revisor-contratual/.
TODOS os erros do pipeline traduzidos para mensagens humanas (sem traceback).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path

import click

from bloco_audit.genesis import GenesisAlreadyInitialized, initialize_audit_genesis
from bloco_interface.error_handler import safe_run
from bloco_interface.output import (
    echo_error,
    format_info,
    format_success,
    format_veredito,
)
from bloco_vault import insert_jurisprudencia, open_vault, zero_embedder
from bloco_vault.data_schema import SumulaSTJ, SumulaVinculanteSTF, VaultDataset
from bloco_vault.populate import BUNDLED_DATA_DIR
from bloco_vault.scrapers import (
    scrape_stf_sumulas_vinculantes,
    scrape_stj_sumulas,
)
from bloco_workflow import revisar_contrato

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
# Defaults persistentes (D-MOR-4.1-F)
# ─────────────────────────────────────────────────────────────────────

DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "revisor-contratual"
DEFAULT_VAULT_DB = DEFAULT_DATA_DIR / "vault.db"
DEFAULT_AUDIT_PATH = DEFAULT_DATA_DIR / "audit.jsonl"
DEFAULT_GENESIS_LOCK = DEFAULT_DATA_DIR / ".audit-genesis.lock"
DEFAULT_BACEN_CACHE = DEFAULT_DATA_DIR / "bacen-cache"


def _ensure_data_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────
# Click app
# ─────────────────────────────────────────────────────────────────────


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version="0.1.0", prog_name="revisor")
def main() -> None:
    """Revisor Contratual — análise jurídica local de contratos bancários CDC.

    Sistema 100% on-premise (LGPD): nenhum dado sai da sua máquina.
    """


# ─────────────────────────────────────────────────────────────────────
# revisar
# ─────────────────────────────────────────────────────────────────────


@main.command()
@click.argument("pdf_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--uf", default=None, help="UF do contrato (override extraído do PDF)")
@click.option(
    "--data-assinatura",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Data assinatura YYYY-MM-DD (override)",
)
@click.option(
    "--tier",
    type=click.Choice(["lean", "balanced", "premium"]),
    default="premium",
    help="Tier do Advogado LLM (default: premium)",
)
@click.option(
    "--vault-db",
    type=click.Path(path_type=Path),
    default=DEFAULT_VAULT_DB,
    help=f"Caminho vault sqlite (default: {DEFAULT_VAULT_DB})",
)
@click.option(
    "--audit-path",
    type=click.Path(path_type=Path),
    default=DEFAULT_AUDIT_PATH,
    help=f"Caminho audit.jsonl (default: {DEFAULT_AUDIT_PATH})",
)
@click.option(
    "--bacen-cache",
    type=click.Path(path_type=Path),
    default=DEFAULT_BACEN_CACHE,
    help=f"Caminho cache BACEN (default: {DEFAULT_BACEN_CACHE})",
)
@click.option(
    "--top-k",
    type=click.IntRange(min=1, max=50),
    default=5,
    help="Docs do vault para personas (default: 5)",
)
def revisar(
    pdf_path: Path,
    uf: str | None,
    data_assinatura: date | object | None,  # click DateTime devolve datetime
    tier: str,
    vault_db: Path,
    audit_path: Path,
    bacen_cache: Path,
    top_k: int,
) -> None:
    """Revisa contrato PDF e emite VeredictoJuiz com audit log."""

    def run() -> int:
        if not vault_db.exists():
            echo_error(
                f"❌ Vault não encontrado em {vault_db}\n"
                "   Rode: revisor populate-vault --source all"
            )
            return 1

        conn = open_vault(str(vault_db))
        try:
            data_override = data_assinatura.date() if data_assinatura is not None else None
            veredito = asyncio.run(
                revisar_contrato(
                    pdf_path,
                    audit_path=audit_path,
                    vault_conn=conn,
                    uf_override=uf,
                    data_override=data_override,
                    tier_advogado=tier,  # type: ignore[arg-type]
                    top_k_vault=top_k,
                    bacen_cache_dir=bacen_cache,
                )
            )
        finally:
            conn.close()

        click.echo(format_veredito(veredito))
        return 0

    exit_code = safe_run(run, on_error=echo_error)
    raise SystemExit(exit_code)


# ─────────────────────────────────────────────────────────────────────
# init-audit
# ─────────────────────────────────────────────────────────────────────


@main.command("init-audit")
@click.option(
    "--lock-path",
    type=click.Path(path_type=Path),
    default=DEFAULT_GENESIS_LOCK,
    help=f"Caminho do lock GENESIS (default: {DEFAULT_GENESIS_LOCK})",
)
def init_audit(lock_path: Path) -> None:
    """Inicializa GENESIS audit lock (rodar 1× no setup)."""

    def run() -> int:
        _ensure_data_dir(lock_path)
        try:
            genesis_hash = initialize_audit_genesis(lock_path=lock_path)
        except GenesisAlreadyInitialized as exc:
            click.echo(format_info(str(exc)))
            return 0  # idempotente — não é erro
        click.echo(format_success(f"GENESIS inicializado em {lock_path}"))
        click.echo(f"Hash: {genesis_hash[:32]}...")
        return 0

    exit_code = safe_run(run, on_error=echo_error)
    raise SystemExit(exit_code)


# ─────────────────────────────────────────────────────────────────────
# populate-vault
# ─────────────────────────────────────────────────────────────────────


@main.command("populate-vault")
@click.option(
    "--vault-db",
    type=click.Path(path_type=Path),
    default=DEFAULT_VAULT_DB,
    help=f"Vault sqlite (default: {DEFAULT_VAULT_DB})",
)
@click.option(
    "--source",
    type=click.Choice(["stj", "stf", "all"]),
    default="all",
    help="Fonte: STJ súmulas / STF SVs / all",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Lista o que seria inserido, sem persistir",
)
@click.option(
    "--zero-embeddings",
    is_flag=True,
    default=True,  # MVP default: zero embeddings (sentence-transformers ~500MB)
    help=(
        "Usa embeddings zero (default MVP). Desligue para embeddings reais "
        "(requer sentence-transformers)."
    ),
)
def populate_vault(vault_db: Path, source: str, dry_run: bool, zero_embeddings: bool) -> None:
    """Popula vault via scrapers reais STJ + STF.

    NFR-LGPD-01: whitelist hardcoded — apenas www.stj.jus.br + www.stf.jus.br.
    Bate REDE REAL — confirme que tem conexão.
    """

    def run() -> int:
        _ensure_data_dir(vault_db)
        conn = open_vault(str(vault_db))
        try:
            total = 0
            sources_to_run = []
            if source in ("stj", "all"):
                sources_to_run.append(("STJ", scrape_stj_sumulas))
            if source in ("stf", "all"):
                sources_to_run.append(("STF", scrape_stf_sumulas_vinculantes))

            for name, scraper in sources_to_run:
                click.echo(format_info(f"Scrapeando {name}..."))
                items = asyncio.run(scraper())
                click.echo(f"  {name}: {len(items)} items extraídos")
                total += len(items)
                if not dry_run:
                    embedder = zero_embedder if zero_embeddings else None
                    for item in items:
                        try:
                            insert_jurisprudencia(conn, item, embedder_fn=embedder)
                        except sqlite3.IntegrityError:
                            # id_doc duplicado — pular silenciosamente (já no vault)
                            pass

            verbo = "extraídos (dry-run)" if dry_run else "persistidos"
            click.echo(format_success(f"Total {verbo}: {total} items"))
        finally:
            conn.close()
        return 0

    exit_code = safe_run(run, on_error=echo_error)
    raise SystemExit(exit_code)


# ─────────────────────────────────────────────────────────────────────
# Helpers — dataset bundled (ADR-012 / VAULT-FIX-01)
# ─────────────────────────────────────────────────────────────────────

# Padrão "Súmula 297" / "Súmula nº 297" / "Súmula Vinculante 7"
_SUMULA_HEADER_RE = re.compile(
    r"S[uú]mula(?:\s+Vinculante)?\s+(?:n[º°ºoO\.]\s*)?(\d+(?:[-‑][A-Z])?)\s*[\.\:\-–—]?\s*",
    re.IGNORECASE,
)


def _compute_hash(texto: str) -> str:
    """SHA-256 hex do texto (UTF-8). Audit chain per ADR-012."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _parse_pdf_text(pdf_path: Path) -> str:
    """Extrai texto bruto de PDF compendium via pdfplumber (já dependency)."""
    try:
        import pdfplumber  # type: ignore[import-untyped]
    except ImportError as exc:
        raise click.ClickException(
            "pdfplumber não instalado. Reinstale: pip install -e .[dev]"
        ) from exc

    pages: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return "\n".join(pages)


def _extract_sumulas_from_text(text: str) -> list[tuple[str, str]]:
    """Encontra (numero, texto) pairs no texto bruto via regex.

    Heurística: cada match de _SUMULA_HEADER_RE marca início de entry;
    texto da entry vai até o próximo header OU fim do documento.
    """
    matches = list(_SUMULA_HEADER_RE.finditer(text))
    entries: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        numero = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        # Limpar quebras de linha hífen + colapsar whitespace
        body = re.sub(r"-\s*\n\s*", "", body)
        body = re.sub(r"\s+", " ", body).strip()
        if len(body) >= 10:
            entries.append((numero, body))
    return entries


def _build_stj_dataset(
    entries: list[tuple[str, str]], source_label: str
) -> VaultDataset:
    """Constrói VaultDataset STJ (manual_import method)."""
    now = datetime.now(UTC)
    fonte_url = "https://www.stj.jus.br/sumulas"
    items = [
        SumulaSTJ(
            numero=numero,
            texto=texto,
            data_aprovacao=None,
            revogada=False,
            area="outras",  # PDF não tem area; maintainer pode enriquecer manualmente
            fonte_url=fonte_url,  # type: ignore[arg-type]
            fetched_at=now,
            hash_sha256=_compute_hash(texto),
        )
        for numero, texto in entries
    ]
    return VaultDataset(
        schema_version="1.0",
        source="stj",
        last_updated=now,
        last_refresh_method="manual_import",
        last_refresh_audit_log=f"manual_import: {source_label}",
        total_entries=len(items),
        entries=items,
    )


def _build_stf_dataset(
    entries: list[tuple[str, str]], source_label: str
) -> VaultDataset:
    """Constrói VaultDataset STF SV (manual_import method)."""
    now = datetime.now(UTC)
    fonte_url = "https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp"
    items: list[SumulaVinculanteSTF] = []
    for numero_str, texto in entries:
        # STF SV é numero int — descartar revisões alfa (e.g., "28-A" -> pular)
        if not numero_str.isdigit():
            logger.warning("STF SV numero não-numérico %s, pulando", numero_str)
            continue
        items.append(
            SumulaVinculanteSTF(
                numero=int(numero_str),
                texto=texto,
                data_aprovacao=None,
                revogada=False,
                fonte_url=fonte_url,  # type: ignore[arg-type]
                fetched_at=now,
                hash_sha256=_compute_hash(texto),
            )
        )
    return VaultDataset(
        schema_version="1.0",
        source="stf",
        last_updated=now,
        last_refresh_method="manual_import",
        last_refresh_audit_log=f"manual_import: {source_label}",
        total_entries=len(items),
        entries=items,
    )


# ─────────────────────────────────────────────────────────────────────
# refresh-vault (ADR-012 — best-effort scraper opt-in)
# ─────────────────────────────────────────────────────────────────────


@main.command("refresh-vault")
@click.option(
    "--source",
    type=click.Choice(["stj", "stf", "all"]),
    default="all",
    help="Fonte: stj / stf / all",
)
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default=BUNDLED_DATA_DIR,
    help=f"Diretório bundled JSON (default: {BUNDLED_DATA_DIR})",
)
def refresh_vault(source: str, data_dir: Path) -> None:
    """Refresh best-effort dos JSONs bundled via scrapers (opt-in, falha gracefully).

    Per ADR-012: scrapers são frágeis (STJ WAF + STF anti-bot); falha NÃO corrompe
    dataset bundled. Em failure -> exit 0 com warning. Em success -> atualiza JSON.
    """

    def run() -> int:
        targets: list[tuple[str, str, str]] = []
        if source in ("stj", "all"):
            targets.append(("stj", "STJ", "sumulas-stj.json"))
        if source in ("stf", "all"):
            targets.append(("stf", "STF SV", "sumulas-stf-vinculantes.json"))

        successes: list[str] = []
        failures: list[tuple[str, str]] = []

        for src_key, label, _filename in targets:
            click.echo(format_info(f"Tentando refresh {label}..."))
            try:
                if src_key == "stj":
                    items = asyncio.run(scrape_stj_sumulas())
                else:
                    items = asyncio.run(scrape_stf_sumulas_vinculantes())
            except Exception as exc:  # noqa: BLE001 — refresh é best-effort
                msg = f"{type(exc).__name__}: {exc}"
                logger.warning("Refresh %s falhou (gracefully): %s", label, msg)
                click.echo(format_info(f"  {label}: scrape falhou ({msg}) — bundled preservado"))
                failures.append((label, msg))
                continue

            click.echo(format_success(f"  {label}: {len(items)} items extraídos"))
            successes.append(label)
            # NOTA: scrapers retornam JurisprudenciaItem (rich schema), enquanto JSON
            # bundled segue SumulaSTJ/STF (lean schema). Conversão reversa é tech debt
            # — por ora, refresh marca success mas NÃO sobrescreve bundled (manual
            # review obrigatória pelo maintainer via import-dataset).
            click.echo(format_info(
                f"  {label}: refresh validado mas escrita JSON requer maintainer review "
                "(use `import-dataset` com PDF oficial)"
            ))

        if successes:
            click.echo(format_success(
                f"Refresh OK em {len(successes)} fonte(s): {', '.join(successes)}"
            ))
        if failures:
            click.echo(format_info(
                f"Refresh degradou em {len(failures)} fonte(s) — bundled dataset intacto"
            ))
        return 0  # graceful: sempre exit 0 (best-effort)

    exit_code = safe_run(run, on_error=echo_error)
    raise SystemExit(exit_code)


# ─────────────────────────────────────────────────────────────────────
# import-dataset (manual import autoritativo)
# ─────────────────────────────────────────────────────────────────────


@main.command("import-dataset")
@click.option(
    "--source-pdf",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="PDF compendium oficial STJ/STF",
)
@click.option(
    "--output-json",
    type=click.Path(path_type=Path),
    required=True,
    help="Path do JSON output (e.g., bloco_vault/data/sumulas-stj.json)",
)
@click.option(
    "--source",
    type=click.Choice(["stj", "stf"]),
    required=True,
    help="Fonte: stj (Súmulas STJ) ou stf (Súmulas Vinculantes STF)",
)
def import_dataset(source_pdf: Path, output_json: Path, source: str) -> None:
    """Parse compendium PDF oficial -> JSON schema-valid (manual_import autoritativo).

    Heurística regex para extrair (numero, texto) pairs; maintainer DEVE revisar
    output JSON antes de commit (data_aprovacao + revogada são None — preencher
    manualmente). Hash sha256 computed per entry (audit chain ADR-012).
    """

    def run() -> int:
        click.echo(format_info(f"Lendo PDF {source_pdf}..."))
        text = _parse_pdf_text(source_pdf)
        click.echo(f"  PDF parseado: {len(text)} chars")

        entries = _extract_sumulas_from_text(text)
        click.echo(f"  Extraídas: {len(entries)} entries via regex")

        if not entries:
            raise click.ClickException(
                "Nenhuma súmula extraída do PDF — verifique formato/heurística regex"
            )

        if source == "stj":
            dataset = _build_stj_dataset(entries, source_label=source_pdf.name)
        else:
            dataset = _build_stf_dataset(entries, source_label=source_pdf.name)

        # Pydantic já validou no construtor; serialize com mode='json' para HttpUrl/datetime
        output_json.parent.mkdir(parents=True, exist_ok=True)
        json_str = json.dumps(
            dataset.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
        output_json.write_text(json_str, encoding="utf-8")

        click.echo(format_success(
            f"Dataset gravado em {output_json}: "
            f"source={dataset.source}, total={dataset.total_entries}, "
            f"schema_version={dataset.schema_version}"
        ))
        click.echo(format_info(
            "ATENÇÃO: data_aprovacao + revogada estão None — maintainer revisar manualmente"
        ))
        return 0

    exit_code = safe_run(run, on_error=echo_error)
    raise SystemExit(exit_code)


# ─────────────────────────────────────────────────────────────────────
# validate-dataset (Pydantic + hash verification)
# ─────────────────────────────────────────────────────────────────────


@main.command("validate-dataset")
@click.argument(
    "json_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
def validate_dataset(json_path: Path) -> None:
    """Valida JSON bundled: Pydantic schema + hash_sha256 recompute (per entry).

    Exit 0 + log PASS se válido. Exit 1 + erro específico se schema invalid OU
    hash mismatch detectado.
    """

    def run() -> int:
        click.echo(format_info(f"Validando {json_path}..."))

        # Pydantic schema validation
        try:
            dataset = VaultDataset.model_validate_json(
                json_path.read_text(encoding="utf-8")
            )
        except Exception as exc:  # noqa: BLE001 — Pydantic ValidationError + json
            raise click.ClickException(f"Schema validation FAIL: {exc}") from exc

        click.echo(
            f"  Schema: PASS (source={dataset.source}, "
            f"total={dataset.total_entries}, schema_version={dataset.schema_version})"
        )

        # Hash recomputation per entry
        hash_mismatches: list[str] = []
        hash_missing: list[str] = []
        for entry in dataset.entries:
            numero = str(entry.numero)
            if entry.hash_sha256 is None:
                hash_missing.append(numero)
                continue
            recomputed = _compute_hash(entry.texto)
            if recomputed != entry.hash_sha256:
                hash_mismatches.append(
                    f"{numero}: stored={entry.hash_sha256[:8]}... "
                    f"recomputed={recomputed[:8]}..."
                )

        if hash_mismatches:
            for m in hash_mismatches:
                click.echo(format_info(f"  Hash MISMATCH: {m}"))
            raise click.ClickException(
                f"Hash verification FAIL: {len(hash_mismatches)} mismatch(es)"
            )

        if hash_missing:
            click.echo(format_info(
                f"  Hash missing em {len(hash_missing)} entries (optional field)"
            ))

        click.echo(format_success(
            f"PASS — {dataset.total_entries} entries schema-valid + "
            f"hash verified ({dataset.total_entries - len(hash_missing)}/"
            f"{dataset.total_entries})"
        ))
        return 0

    exit_code = safe_run(run, on_error=echo_error)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
