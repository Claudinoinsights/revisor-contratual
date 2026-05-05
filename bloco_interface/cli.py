"""CLI Click — entry point `revisor` (D-MOR-4.1-A..H).

3 subcomandos MVP:
  - revisar       — pipeline completo PDF → VeredictoJuiz
  - init-audit    — inicializa GENESIS audit lock
  - populate-vault — scrapers reais STJ + STF (NFR-LGPD-01 whitelist)

Defaults persistentes em ~/.local/share/revisor-contratual/.
TODOS os erros do pipeline traduzidos para mensagens humanas (sem traceback).
"""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional

import click

from bloco_audit.genesis import GenesisAlreadyInitialized, initialize_audit_genesis
from bloco_interface.error_handler import safe_run, translate_exception
from bloco_interface.output import (
    echo_error,
    format_info,
    format_success,
    format_veredito,
)
from bloco_vault import insert_jurisprudencia, open_vault, zero_embedder
from bloco_vault.scrapers import (
    scrape_stf_sumulas_vinculantes,
    scrape_stj_sumulas,
)
from bloco_workflow import revisar_contrato

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
    uf: Optional[str],
    data_assinatura: Optional["date | object"],  # click DateTime devolve datetime
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
    help="Usa embeddings zero (default MVP). Desligue para embeddings reais (requer sentence-transformers).",
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


if __name__ == "__main__":
    main()
