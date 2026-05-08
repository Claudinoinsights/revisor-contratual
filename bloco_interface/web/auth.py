"""Auth module — MVP-LEAN-01 Task 2.

Implementa auth básica defense-in-depth (FR-LGPD-MVP-01a / ADR-013 §2.3 camada 1):
- bcrypt password hashing/verify (rounds=12)
- Single-user solo via env vars ADMIN_USERNAME + ADMIN_PASSWORD_HASH (perfil Eric per ADR-013 §2.2)
- CSRF token custom (secrets.token_hex + hmac.compare_digest constant-time)
- Session secret key via env REVISOR_SECRET_KEY (gerada-on-startup com warning se ausente)

Anti-enumeration: authenticate() retorna boolean único — mesma resposta para
"usuário inexistente" vs "senha errada" (ux-spec §4 C1 linha 626).
"""

from __future__ import annotations

import hmac
import logging
import os
import secrets

import bcrypt

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────
DEFAULT_USERNAME = "admin"
# bcrypt hash de "admin" com rounds=12 (apenas dev; sobrescrito por env em prod)
DEFAULT_PASSWORD_HASH = "$2b$12$LQv3c1yqBwEHFgN0c9pBQuWlYMu7yqK1hH6S0Lxsr8VqGqJ.8PqS6"  # noqa: S105


def get_secret_key() -> str:
    """Lê REVISOR_SECRET_KEY de env; gera key efêmera com warning se ausente.

    Em produção deve ser set via env (sessões persistem entre restarts).
    Em dev sem env, gera key efêmera (sessões expiram a cada restart — aceitável).
    """
    secret = os.environ.get("REVISOR_SECRET_KEY")
    if secret:
        return secret
    logger.warning(
        "REVISOR_SECRET_KEY não definida em env — gerando key efêmera. "
        "Sessões expiram a cada restart. Set REVISOR_SECRET_KEY em produção."
    )
    return secrets.token_hex(32)


def get_admin_credentials() -> tuple[str, str]:
    """Lê ADMIN_USERNAME + ADMIN_PASSWORD_HASH de env (single-user solo MVP).

    Returns (username, password_hash). Defaults para 'admin' / hash de 'admin' em dev.
    """
    username = os.environ.get("ADMIN_USERNAME", DEFAULT_USERNAME)
    password_hash = os.environ.get("ADMIN_PASSWORD_HASH", DEFAULT_PASSWORD_HASH)
    return username, password_hash


def verify_password(plain: str, hashed: str) -> bool:
    """bcrypt.checkpw com tratamento defensivo de hash malformado."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # Hash malformado — tratado como auth failure (não levanta para evitar info leak)
        return False


def authenticate(username: str, password: str) -> bool:
    """Auth principal — anti-enumeration.

    Compara username (case-sensitive constant-time) + password (bcrypt).
    SEMPRE executa bcrypt.checkpw mesmo se username errado, para
    evitar timing-based enumeration.
    """
    admin_user, admin_hash = get_admin_credentials()
    # Constant-time compare username (mitiga timing oracle em strings curtas)
    user_match = hmac.compare_digest(username.encode("utf-8"), admin_user.encode("utf-8"))
    # SEMPRE executar bcrypt mesmo se user errado (timing constant)
    pwd_match = verify_password(password, admin_hash)
    return user_match and pwd_match


def generate_csrf_token() -> str:
    """Gera CSRF token criptograficamente seguro (32 bytes hex = 64 chars)."""
    return secrets.token_hex(32)


def verify_csrf_token(session_token: str | None, form_token: str | None) -> bool:
    """Verifica CSRF token com constant-time compare (hmac.compare_digest)."""
    if not session_token or not form_token:
        return False
    return hmac.compare_digest(session_token, form_token)
