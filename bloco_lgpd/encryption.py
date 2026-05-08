"""LGPD L4 — Encryption-at-rest Fernet (MVP-LEAN-01 Task 8).

Per ux-spec/PRD §FR-LGPD-MVP-01d + ADR-013 §2.3 camada 4:
- FERNET_KEY env var (gerada via Fernet.generate_key() em produção)
- encrypt_pdf on upload + decrypt in-memory para parsing + safe_delete pós-pipeline
"""

from __future__ import annotations

import logging
import os
import secrets
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


def get_fernet_key() -> bytes:
    """Lê FERNET_KEY de env; gera key efêmera com warning se ausente (similar SECRET_KEY Task 2).

    Em produção FERNET_KEY DEVE ser persistente — sem ela, PDFs cifrados em uploads/
    não podem ser descriptografados após restart.
    """
    key_str = os.environ.get("FERNET_KEY")
    if key_str:
        key = key_str.encode("utf-8") if isinstance(key_str, str) else key_str
        # Validar formato Fernet (44 chars base64-urlsafe)
        try:
            Fernet(key)  # raise InvalidToken se formato inválido
            return key
        except (ValueError, InvalidToken) as exc:
            raise InvalidToken(
                f"FERNET_KEY com formato inválido em .env: {exc}"
            ) from exc
    logger.warning(
        "FERNET_KEY não definida em env — gerando key efêmera. "
        "PDFs cifrados não persistirão após restart. "
        "Set FERNET_KEY em produção via Fernet.generate_key()."
    )
    return Fernet.generate_key()


def encrypt_pdf(pdf_bytes: bytes) -> bytes:
    """Cifra PDF bytes via Fernet (FR-LGPD-MVP-01d encrypt-on-upload)."""
    key = get_fernet_key()
    fernet = Fernet(key)
    return fernet.encrypt(pdf_bytes)


def decrypt_pdf(encrypted_bytes: bytes) -> bytes:
    """Decifra PDF bytes via Fernet (in-memory para parsing)."""
    key = get_fernet_key()
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_bytes)


def safe_delete(path: Path) -> bool:
    """LGPD-compliant delete: overwrite com random bytes (single pass) + unlink.

    Best-effort: se write/unlink falhar, retorna False mas não levanta
    (evita bloquear pipeline mid-error em finally).

    Returns: True se deleted with success.
    """
    if not path.exists():
        return True
    try:
        size = path.stat().st_size
        # Single-pass overwrite com random bytes (LGPD compliant para storage convencional)
        with path.open("r+b") as f:
            f.write(secrets.token_bytes(size))
            f.flush()
            os.fsync(f.fileno())
        path.unlink()
        return True
    except OSError as exc:
        logger.warning("safe_delete falhou para %s: %s", path, exc)
        # Tentar unlink direto se overwrite falhou
        try:
            path.unlink(missing_ok=True)
            return True
        except OSError:
            return False
