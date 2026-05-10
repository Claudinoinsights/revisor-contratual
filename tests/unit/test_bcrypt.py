"""Unit tests bcrypt password hashing (SP04-AUTH-01 AC-03 + AC-08).

Cobre:
- hash + verify roundtrip (raw bcrypt — passlib droppado por incompat 1.7.4 ↔ bcrypt 4.x)
- Wrong password rejection
- Cost factor 12 enforcement (Story Risk #4 + critical scenario #3)
- Cost < 12 detection via verify_cost_factor helper
- Salt único (anti rainbow table) — mesma senha 2x → hashes diferentes
- Password > 72 bytes → PasswordTooLongError (anti silent truncation)

Sem env vars necessárias — bcrypt config é em código (não env).
"""

from __future__ import annotations

import bcrypt as _bcrypt_raw
import pytest

from bloco_auth.passwords import (
    PasswordTooLongError,
    hash_password,
    verify_cost_factor,
    verify_password,
)


@pytest.mark.unit
def test_bcrypt_hash_verify_roundtrip() -> None:
    """hash + verify mesma senha → True."""
    plain = "minhasenh@SuperSecreta2026"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


@pytest.mark.unit
def test_bcrypt_wrong_password_rejection() -> None:
    """verify com senha errada → False."""
    hashed = hash_password("certa")
    assert verify_password("errada", hashed) is False


@pytest.mark.unit
def test_bcrypt_cost_factor_12() -> None:
    """Hash gerado por hash_password tem cost 12 enforced ($2b$12$ prefix)."""
    hashed = hash_password("qualquersenha")
    assert hashed.startswith("$2b$12$"), (
        f"Esperado prefix '$2b$12$' (cost factor 12), recebido: {hashed[:7]}"
    )


@pytest.mark.unit
def test_bcrypt_cost_too_low_rejection() -> None:
    """Hash com cost < 12 detectado por verify_cost_factor.

    Forge um hash com cost 4 usando bcrypt raw + assert helper retorna False.
    """
    weak_hash = _bcrypt_raw.hashpw(b"x", _bcrypt_raw.gensalt(rounds=4)).decode("utf-8")
    assert weak_hash.startswith("$2b$04$"), f"Forge hash failed: {weak_hash[:7]}"
    assert verify_cost_factor(weak_hash) is False, (
        "verify_cost_factor deveria rejeitar cost < 12"
    )


@pytest.mark.unit
def test_bcrypt_cost_strong_acceptance() -> None:
    """verify_cost_factor aceita cost >= 12 (default min)."""
    strong_hash = hash_password("teste")
    assert verify_cost_factor(strong_hash) is True


@pytest.mark.unit
def test_bcrypt_unique_salt() -> None:
    """Mesma senha em 2 hashes → salts diferentes → hashes diferentes.

    Anti rainbow table: salt único garante que 2 users com mesma senha não
    têm hashes idênticos no DB (não revela "fulano usa 123456").
    """
    password = "mesma_senha"
    hash_a = hash_password(password)
    hash_b = hash_password(password)
    assert hash_a != hash_b, "Salt único quebrado — hashes idênticos!"
    # Mas ambos verificam OK
    assert verify_password(password, hash_a) is True
    assert verify_password(password, hash_b) is True


@pytest.mark.unit
def test_bcrypt_password_too_long_rejection() -> None:
    """Senha > 72 bytes → PasswordTooLongError (anti silent truncation)."""
    long_password = "a" * 73
    with pytest.raises(PasswordTooLongError, match="73 bytes|max 72"):
        hash_password(long_password)


@pytest.mark.unit
def test_bcrypt_cost_below_minimum_rejected_by_hash() -> None:
    """hash_password rejeita cost < 12 explicitamente (defense-in-depth)."""
    with pytest.raises(ValueError, match="insuficiente|mínimo"):
        hash_password("teste", cost=4)


@pytest.mark.unit
def test_bcrypt_verify_cost_factor_invalid_format() -> None:
    """verify_cost_factor com string não-bcrypt → False (não raise)."""
    assert verify_cost_factor("not-a-hash") is False
    assert verify_cost_factor("") is False
    assert verify_cost_factor("$1$md5$something") is False  # md5crypt format


@pytest.mark.unit
def test_bcrypt_verify_password_malformed_hash() -> None:
    """verify_password com hash malformado → False (defensive, não raise)."""
    assert verify_password("anything", "not-a-bcrypt-hash") is False
    assert verify_password("anything", "") is False
