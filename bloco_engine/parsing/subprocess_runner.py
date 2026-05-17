"""Subprocess CLI runner for parse_contract — Sprint 7 Phase 3 (ADR-026).

F-PROD-NEW-22 fix: marker library + PyMuPDF C extensions executam em subprocess
descartável isolado. Subprocess crash (os._exit() OR SIGABRT OR Python exception)
NÃO mata parent worker — pipeline.py Step 1 captures via asyncio.subprocess.

Usage:
    python -m bloco_engine.parsing.subprocess_runner <pdf_path> <metadata_json_path>

Reads metadata JSON from <metadata_json_path> file:
    {
        "uf_override": "SP",  # str | None
        "data_override": "2025-12-01"  # ISO date str | None
    }

Returns ParsedContract via stdout (Pydantic JSON).
Exits 0 on success, 1 on Python exception (error JSON em stderr), 2 on usage error.

Refs:
- ADR-026 governance/architecture/adr/adr-026-marker-subprocess-isolation-parsing.md
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from datetime import date
from pathlib import Path

from bloco_engine.parsing.orchestrator import parse_contract


def main() -> int:
    """CLI entry point. Returns exit code (0=success, 1=error, 2=usage)."""
    if len(sys.argv) != 3:
        print(
            "ERROR: usage: python -m bloco_engine.parsing.subprocess_runner "
            "<pdf_path> <metadata_json_path>",
            file=sys.stderr,
        )
        return 2

    pdf_path = Path(sys.argv[1])
    metadata_json_path = Path(sys.argv[2])

    if not pdf_path.is_file():
        print(
            json.dumps(
                {
                    "error_type": "PDFNotFound",
                    "error_msg": f"PDF file not found: {pdf_path}",
                }
            ),
            file=sys.stderr,
        )
        return 1

    if not metadata_json_path.is_file():
        print(
            json.dumps(
                {
                    "error_type": "MetadataFileNotFound",
                    "error_msg": f"Metadata JSON file not found: {metadata_json_path}",
                }
            ),
            file=sys.stderr,
        )
        return 1

    try:
        with open(metadata_json_path, encoding="utf-8") as f:
            metadata = json.load(f)
        uf_override = metadata.get("uf_override")
        data_str = metadata.get("data_override")
        data_override = date.fromisoformat(data_str) if data_str else None

        # parse_contract() chamado dentro do subprocess — marker library +
        # PyMuPDF + surya carregados aqui. Se chamarem os._exit() OR SIGABRT,
        # apenas o subprocess morre. Parent worker continua via asyncio.subprocess.
        #
        # D-DEV-S08-005 fix (D-OPS-S08-010 empirical): marker library imprime
        # diagnostic messages em stdout ("=== Document parser messages ===",
        # progress bars surya). Estas contaminam JSON output → Pydantic
        # ValidationError no parent. Redireciona stdout durante parse_contract
        # para io.StringIO descartável — apenas o JSON final vai para stdout.
        with contextlib.redirect_stdout(io.StringIO()):
            parsed = parse_contract(
                pdf_path,
                pdf_bytes=pdf_path.read_bytes(),
                uf_override=uf_override,
                data_override=data_override,
            )

        # Pydantic native JSON serialization — ÚNICO output em stdout (limpo)
        print(parsed.model_dump_json())
        return 0

    except Exception as exc:
        # Captura Python exceptions — NÃO captura os._exit() OR SIGABRT
        # (que matam processo subprocess inteiro, parent detecta via returncode != 0).
        print(
            json.dumps(
                {
                    "error_type": type(exc).__name__,
                    "error_msg": str(exc),
                }
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
