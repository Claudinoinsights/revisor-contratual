"""Parsing subprocess exceptions — Sprint 7 Phase 3 (ADR-026).

F-PROD-NEW-22 fix: marker library + PyMuPDF C extensions isolated em subprocess
descartável. Subprocess crash NÃO mata parent worker — exceptions abaixo capturadas
em pipeline.py Step 1 e registradas em audit chain.

Refs:
- ADR-026 governance/architecture/adr/adr-026-marker-subprocess-isolation-parsing.md
"""

from __future__ import annotations


class ParsingSubprocessFailedError(Exception):
    """Subprocess parse_contract failed (non-zero exit code).

    Captura subprocess crash via os._exit() OR SIGABRT OR Python exception.
    error_type pode ser de stderr JSON parsed OR fallback "ParsingSubprocessFailed".
    """

    def __init__(self, error_type: str, error_msg: str) -> None:
        self.error_type = error_type
        self.error_msg = error_msg
        super().__init__(f"{error_type}: {error_msg}")


class ParsingSubprocessTimeoutError(Exception):
    """Subprocess parse_contract excedeu timeout 180s + 5s SIGKILL fallback.

    Subprocess hang OR runaway loop OR very large PDF (>20 pages) podem disparar.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
