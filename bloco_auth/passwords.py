"""Bcrypt password hashing — raw ``bcrypt`` library (Sprint 04 SP04-AUTH-01).

Cost factor 12 enforced (Story Risk #4 — bcrypt cost factor degradation +
critical scenario #3 — cost mandatory ≥ 12).

**Decisão técnica @dev Neo Phase 7.2.3:** raw ``bcrypt>=4.0`` (não ``passlib``).
``passlib 1.7.4`` (latest, 2020) é incompatível com ``bcrypt>=4.0`` (2023+) —
passlib procura ``bcrypt.__about__.__version__`` que foi removido na 4.x e
falha no detect_wrap_bug com ``ValueError: password cannot be longer than
72 bytes``. Sprint 03 já tem ``bcrypt>=4.0`` raw em deps funcionando. Drop
da camada passlib elimina incompat sem perder funcionalidade — hash, verify
e cost-factor parsing são triviais com bcrypt direto.

API mantida intencionalmente igual (``hash_password``, ``verify_password``,
``verify_cost_factor``) para que chunk 4 (api.py + onboarding.py) consuma
sem mudança de contrato se passlib voltar a ser viável no futuro.

Cross-references:
    governance/stories/sp04-auth-01-multi-tenant-auth.md AC-03 + AC-08
"""

from __future__ import annotations

import re

import bcrypt as _bcrypt


_BCRYPT_DEFAULT_COST = 12
_BCRYPT_MAX_PASSWORD_BYTES = 72  # bcrypt limita 72 bytes — anti silent truncation


# Regex parser para hash bcrypt format: $2a$NN$... | $2b$NN$... | $2y$NN$...
# Bcrypt hash structure: $<variant>$<cost>$<22-char salt><31-char hash>
_BCRYPT_HASH_RE = re.compile(r"^\$2[aby]\$(\d{2})\$")


class PasswordTooLongError(ValueError):
    """Senha excede limite bcrypt 72 bytes — rejeitar em vez de truncar silently."""


def hash_password(plain: str, cost: int = _BCRYPT_DEFAULT_COST) -> str:
    """Gera hash bcrypt cost factor 12 (default) — raise se senha > 72 bytes.

    Args:
        plain: senha em texto puro.
        cost: cost factor (default 12, mínimo enforced via story AC-08 #3).

    Returns:
        Hash bcrypt no formato ``$2b$NN$<22-char-salt><31-char-hash>``.

    Raises:
        PasswordTooLongError: senha excede 72 bytes (bcrypt limit). Decisão
            arquitetural: rejeitar explicitamente em vez de truncate silent
            (anti hash-collision em senhas longas que diferem só após byte 72).
    """
    if cost < _BCRYPT_DEFAULT_COST:
        raise ValueError(
            f"Cost factor {cost} insuficiente — mínimo {_BCRYPT_DEFAULT_COST} "
            "(Story AC-08 critical scenario #3)"
        )
    encoded = plain.encode("utf-8")
    if len(encoded) > _BCRYPT_MAX_PASSWORD_BYTES:
        raise PasswordTooLongError(
            f"Senha tem {len(encoded)} bytes (max {_BCRYPT_MAX_PASSWORD_BYTES} "
            "bytes em bcrypt). Reject explícito em vez de truncate silent."
        )
    salt = _bcrypt.gensalt(rounds=cost)
    return _bcrypt.hashpw(encoded, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica senha contra hash bcrypt (constant-time compare interno).

    Args:
        plain: senha candidata em texto puro.
        hashed: hash bcrypt armazenado.

    Returns:
        ``True`` se senha bate, ``False`` caso contrário (incluindo hash
        malformado — bcrypt.checkpw retorna False sem raise).
    """
    encoded = plain.encode("utf-8")
    if len(encoded) > _BCRYPT_MAX_PASSWORD_BYTES:
        # Truncate silencioso aqui é OK — verify de senha correta nunca >72 bytes
        # (signup já rejeitou). Se chegou >72 em verify, é tentativa de bypass.
        return False
    try:
        return _bcrypt.checkpw(encoded, hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # Hash malformado (não-bcrypt) — comportamento defensivo: False, não raise
        return False


def verify_cost_factor(hashed: str, min_cost: int = _BCRYPT_DEFAULT_COST) -> bool:
    """Verifica que hash bcrypt tem cost factor >= ``min_cost``.

    Defensive check para detectar hashes legacy com cost insuficiente
    (ex.: imports de Sprint 03 que pode ter usado cost 4 em testes).

    Args:
        hashed: hash bcrypt no formato ``$2[aby]$NN$...``.
        min_cost: cost mínimo aceitável (default 12 — Story AC-08 critical
            scenario #3).

    Returns:
        ``True`` se cost factor >= min_cost.
        ``False`` se cost insuficiente OR hash não bate com regex bcrypt.
    """
    match = _BCRYPT_HASH_RE.match(hashed)
    if match is None:
        return False
    cost = int(match.group(1))
    return cost >= min_cost


__all__ = [
    "PasswordTooLongError",
    "hash_password",
    "verify_password",
    "verify_cost_factor",
]
