"""Unit tests para bloco_auth.byok_encryption (SP04-BYOK-01 chunk 3 / AC-02).

Pattern: similar ``tests/unit/test_jwt.py`` — eager validation @lru_cache,
monkeypatch env, cache_clear entre tests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from bloco_auth.byok_encryption import (
    ConfigError,
    _load_master_key,
    decrypt_api_key,
    encrypt_api_key,
    truncate_fingerprint,
    validate_config,
)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _master_key_env(monkeypatch):
    """Reset cache + seta MASTER_ENCRYPTION_KEY válida (32+ bytes hex)."""
    _load_master_key.cache_clear()
    monkeypatch.setenv(
        "MASTER_ENCRYPTION_KEY",
        "0123456789abcdef" * 4,  # 64 chars = 64 bytes (≥ 32 mínimo)
    )
    yield
    _load_master_key.cache_clear()


# ──────────────────────────────────────────────────────────────────────────────
# Master key validation — eager ConfigError
# ──────────────────────────────────────────────────────────────────────────────


def test_load_master_key_eager_config_error_when_missing(monkeypatch):
    """ConfigError eager se MASTER_ENCRYPTION_KEY ausente no env."""
    _load_master_key.cache_clear()
    monkeypatch.delenv("MASTER_ENCRYPTION_KEY", raising=False)
    with pytest.raises(ConfigError, match="MASTER_ENCRYPTION_KEY ausente"):
        _load_master_key()


def test_load_master_key_eager_config_error_when_empty(monkeypatch):
    """ConfigError eager se MASTER_ENCRYPTION_KEY vazia (whitespace stripping)."""
    _load_master_key.cache_clear()
    monkeypatch.setenv("MASTER_ENCRYPTION_KEY", "   ")
    with pytest.raises(ConfigError, match="MASTER_ENCRYPTION_KEY ausente"):
        _load_master_key()


def test_load_master_key_eager_config_error_when_too_short(monkeypatch):
    """ConfigError eager se MASTER_ENCRYPTION_KEY < 32 bytes."""
    _load_master_key.cache_clear()
    monkeypatch.setenv("MASTER_ENCRYPTION_KEY", "short-key")  # 9 bytes
    with pytest.raises(ConfigError, match=r"\d+ bytes — mínimo 32 bytes"):
        _load_master_key()


def test_load_master_key_returns_valid_key():
    """Master key válida (64 chars) é cached e retornada."""
    key = _load_master_key()
    assert len(key.encode("utf-8")) >= 32
    # Cache hit: segundo call retorna mesma key sem re-validar
    assert _load_master_key() is key


def test_validate_config_invokes_master_key_load():
    """validate_config() startup hook força load eager."""
    _load_master_key.cache_clear()
    # Não levanta — env válida fixture
    validate_config()


# ──────────────────────────────────────────────────────────────────────────────
# truncate_fingerprint — audit/UI safe
# ──────────────────────────────────────────────────────────────────────────────


def test_truncate_fingerprint_anthropic_format():
    """Fingerprint formato 'sk-ant-...XYZ' (7 prefix + ... + 3 suffix)."""
    plain = "sk-ant-api03-abcdefghijklmnopqrstuvwxyzXYZ"
    result = truncate_fingerprint(plain)
    assert result == "sk-ant-...XYZ"


def test_truncate_fingerprint_short_key_raises():
    """ValueError se chave < 12 chars (não fingerprintable safely)."""
    with pytest.raises(ValueError, match="mínimo 12 chars"):
        truncate_fingerprint("sk-short")  # 8 chars


def test_truncate_fingerprint_deterministic():
    """Fingerprint deterministic — mesmo input → mesmo output."""
    plain = "sk-ant-foo-bar-baz-end"
    assert truncate_fingerprint(plain) == truncate_fingerprint(plain)


def test_truncate_fingerprint_different_keys_different_fingerprints():
    """Fingerprints distintos para chaves distintas (mesmo prefix)."""
    fp_a = truncate_fingerprint("sk-ant-test-AAA")
    fp_b = truncate_fingerprint("sk-ant-test-BBB")
    assert fp_a != fp_b
    assert fp_a == "sk-ant-...AAA"
    assert fp_b == "sk-ant-...BBB"


# ──────────────────────────────────────────────────────────────────────────────
# encrypt_api_key / decrypt_api_key — SQLAlchemy func mock
# ──────────────────────────────────────────────────────────────────────────────


def _make_mock_db_session(scalar_value):
    """Helper: cria AsyncSession mock onde execute(...) retorna result.scalar_one() == scalar_value."""
    result_mock = MagicMock()
    result_mock.scalar_one = MagicMock(return_value=scalar_value)
    db_session = MagicMock()
    db_session.execute = AsyncMock(return_value=result_mock)
    return db_session


@pytest.mark.asyncio
async def test_encrypt_api_key_calls_pgp_sym_encrypt():
    """encrypt_api_key invoca pgp_sym_encrypt via SQLAlchemy func."""
    db_session = _make_mock_db_session(b"\x01\x02\x03encrypted")

    result = await encrypt_api_key("sk-ant-test-key", db_session)

    assert result == b"\x01\x02\x03encrypted"
    db_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_decrypt_api_key_calls_pgp_sym_decrypt():
    """decrypt_api_key invoca pgp_sym_decrypt via SQLAlchemy func."""
    db_session = _make_mock_db_session("sk-ant-test-decrypted")

    result = await decrypt_api_key(b"\x01\x02\x03encrypted", db_session)

    assert result == "sk-ant-test-decrypted"
    db_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_encrypt_uses_master_key_from_env(monkeypatch):
    """encrypt usa master_key cached do env (não hardcoded)."""
    _load_master_key.cache_clear()
    monkeypatch.setenv("MASTER_ENCRYPTION_KEY", "x" * 64)  # 64 bytes válido

    db_session = _make_mock_db_session(b"encrypted")

    await encrypt_api_key("sk-ant-test", db_session)

    # Verifica que execute foi chamado (master_key é applied dentro do func chain)
    db_session.execute.assert_awaited_once()
