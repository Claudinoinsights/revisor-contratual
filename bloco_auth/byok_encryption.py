"""BYOK encryption wrappers via PostgreSQL pgcrypto (SP04-BYOK-01 / ADR-014 + Tank Phase 12.3a).

Encrypt/decrypt API keys via ``pgp_sym_encrypt``/``pgp_sym_decrypt`` PostgreSQL
functions (não Python crypto direto) — consistency com extension first-class
pattern AUTH-01 pgcrypto. Master key ``MASTER_ENCRYPTION_KEY`` env var (≥32
bytes; ConfigError eager via ``@lru_cache`` similar ``jwt_utils.py`` template).

Audit trail: ``truncate_fingerprint`` retorna formato ``sk-ant-...XYZ`` para
audit/UI — chave NUNCA logada full (ADR-014 §Decisão.Componentes 6).

Cross-references:
    governance/stories/sp04-byok-01-anthropic-key-lifecycle.md AC-02
    governance/architecture/adr/adr-014-provider-abstraction-byok.md
    bloco_auth/jwt_utils.py (template eager validation @lru_cache)
"""

from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


_MIN_KEY_BYTES = 32
_FINGERPRINT_PREFIX_LEN = 7  # 'sk-ant-' = 7 chars
_FINGERPRINT_SUFFIX_LEN = 3  # last 3 chars
_MIN_FINGERPRINTABLE_LEN = _FINGERPRINT_PREFIX_LEN + _FINGERPRINT_SUFFIX_LEN + 2  # min 12 chars total


class ConfigError(RuntimeError):
    """``MASTER_ENCRYPTION_KEY`` ausente ou inválida no environment.

    Lançada eager no startup via ``validate_config()`` OR primeiro chamado
    de ``encrypt_api_key`` / ``decrypt_api_key``. Falha cedo é melhor que
    falha no primeiro request prod.
    """


@lru_cache(maxsize=1)
def _load_master_key() -> str:
    """Lê e valida ``MASTER_ENCRYPTION_KEY`` do environment (cached).

    Validação eager (≥ 32 bytes). Tests resetam cache via
    ``_load_master_key.cache_clear()`` + ``monkeypatch.setenv``.

    Raises:
        ConfigError: se ``MASTER_ENCRYPTION_KEY`` ausente OR < 32 bytes.
    """
    raw = os.getenv("MASTER_ENCRYPTION_KEY")
    if raw is None or raw.strip() == "":
        raise ConfigError(
            "MASTER_ENCRYPTION_KEY ausente no environment. "
            "Gere via: openssl rand -hex 32 (output ≥ 64 hex chars = 32 bytes)"
        )
    key = raw.strip()
    if len(key.encode("utf-8")) < _MIN_KEY_BYTES:
        raise ConfigError(
            f"MASTER_ENCRYPTION_KEY tem {len(key.encode('utf-8'))} bytes — "
            f"mínimo {_MIN_KEY_BYTES} bytes (chave fraca permite brute force "
            "do encrypted_key). Gere via: openssl rand -hex 32"
        )
    return key


async def encrypt_api_key(plain_key: str, db_session: AsyncSession) -> bytes:
    """Encripta API key via PostgreSQL ``pgp_sym_encrypt(key, master_key)``.

    Usa SQLAlchemy ``func.pgp_sym_encrypt`` — não Python crypto direto. Consistency
    com extension first-class pattern AUTH-01 pgcrypto. ``MASTER_ENCRYPTION_KEY``
    é validada eager via ``_load_master_key`` (cached).

    Args:
        plain_key: API key Anthropic em texto claro (ex: ``sk-ant-...``).
        db_session: AsyncSession SQLAlchemy ativa.

    Returns:
        ``encrypted_key`` BYTEA pronto para insert em ``tenant_api_keys.encrypted_key``.

    Raises:
        ConfigError: ``MASTER_ENCRYPTION_KEY`` ausente OR < 32 bytes.
    """
    master_key = _load_master_key()
    result = await db_session.execute(
        select(func.pgp_sym_encrypt(plain_key, master_key))
    )
    return result.scalar_one()


async def decrypt_api_key(encrypted: bytes, db_session: AsyncSession) -> str:
    """Decripta API key via PostgreSQL ``pgp_sym_decrypt(encrypted, master_key)``.

    Args:
        encrypted: ``encrypted_key`` BYTEA do banco (de ``tenant_api_keys``).
        db_session: AsyncSession SQLAlchemy ativa.

    Returns:
        API key Anthropic em texto claro — pronta para inject em ``Anthropic(api_key=...)``.

    Raises:
        ConfigError: ``MASTER_ENCRYPTION_KEY`` ausente OR < 32 bytes.
        Exception: PostgreSQL ``decryption failed`` (master_key mismatch, blob corrompido)
            — caller (middleware) deve catchar e retornar HTTP 503 + audit
            ``byok_decryption_failed``.
    """
    master_key = _load_master_key()
    result = await db_session.execute(
        select(func.pgp_sym_decrypt(encrypted, master_key))
    )
    return result.scalar_one()


def truncate_fingerprint(plain_key: str) -> str:
    """Retorna formato ``sk-ant-...XYZ`` para audit/UI (NUNCA chave full).

    Format: primeiros 7 chars (``sk-ant-`` prefix Anthropic) + ``...`` + últimos 3.
    Chave Anthropic real tem ~108 chars (`sk-ant-api03-...`); fingerprint expõe
    apenas prefixo público + 3 chars de entropia para identificação humana.

    Args:
        plain_key: API key Anthropic em texto claro.

    Returns:
        Fingerprint truncated para audit log e Settings UI.

    Raises:
        ValueError: se ``plain_key`` < 12 chars (não fingerprintable safely).

    Examples:
        >>> truncate_fingerprint("sk-ant-api03-abcdefghij...XYZ")
        'sk-ant-...XYZ'
    """
    if len(plain_key) < _MIN_FINGERPRINTABLE_LEN:
        raise ValueError(
            f"API key '{plain_key[:3]}...' tem {len(plain_key)} chars — "
            f"mínimo {_MIN_FINGERPRINTABLE_LEN} chars para fingerprint safely "
            "(evita expor chave fraca completa)"
        )
    return f"{plain_key[:_FINGERPRINT_PREFIX_LEN]}...{plain_key[-_FINGERPRINT_SUFFIX_LEN:]}"


def validate_config() -> None:
    """Hook de startup explícito para falha eager em produção.

    Chamar uma vez no boot do app (ex.: ``bloco_interface/web/app.py`` lifespan)
    para abortar startup se ``MASTER_ENCRYPTION_KEY`` ausente ou fraca. Após
    primeiro call, ``_load_master_key`` cache mantém valor para reuse em
    encrypt/decrypt.
    """
    _load_master_key()


__all__ = [
    "ConfigError",
    "encrypt_api_key",
    "decrypt_api_key",
    "truncate_fingerprint",
    "validate_config",
]
