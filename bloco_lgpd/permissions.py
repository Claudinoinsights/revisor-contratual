"""LGPD L5 — Permissões filesystem cross-platform (MVP-LEAN-01 Task 8).

Per ux-spec/PRD §FR-LGPD-MVP-01e + ADR-013 §2.3 camada 5:
- audit.jsonl chmod 600 (apenas owner read/write)
- uploads/ chmod 700 (apenas owner read/write/execute)

POSIX (Linux/macOS): os.chmod direto.
Windows: chmod tem semantica limitada (NT ACL avançada exige pywin32 — fora MVP).
Cross-platform: try POSIX; pass silenciosamente se OS sem suporte completo.
"""

from __future__ import annotations

import logging
import os
import platform
from pathlib import Path

logger = logging.getLogger(__name__)


def apply_audit_permissions(path: Path) -> bool:
    """chmod 0o600 em audit.jsonl (apenas owner). Retorna True se aplicado."""
    if not path.exists():
        return False
    try:
        os.chmod(path, 0o600)
    except (OSError, NotImplementedError) as exc:
        logger.warning(
            "apply_audit_permissions: chmod falhou em %s (%s — possível Windows): %s",
            path, platform.system(), exc,
        )
        return False
    return True


def apply_uploads_dir_permissions(path: Path) -> bool:
    """chmod 0o700 em uploads/ + recursivo em arquivos contidos. Retorna True se aplicado."""
    if not path.exists():
        return False
    try:
        os.chmod(path, 0o700)
        for child in path.rglob("*"):
            if child.is_file():
                try:
                    os.chmod(child, 0o600)
                except OSError:
                    continue
    except (OSError, NotImplementedError) as exc:
        logger.warning(
            "apply_uploads_dir_permissions: chmod falhou em %s (%s): %s",
            path, platform.system(), exc,
        )
        return False
    return True


def is_posix() -> bool:
    """Helper: True se POSIX (Linux/macOS), False se Windows."""
    return os.name == "posix"
