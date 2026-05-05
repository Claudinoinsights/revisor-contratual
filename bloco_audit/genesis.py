"""HMAC GENESIS anchor para audit chain (ADR-005 PATCH F-MIN-03 RITMO 2).

Smith F-CRIT-A → R-NEW-SMITH-03: "GENESIS" como string literal era forjável.
Solução ADR-005: GENESIS = HMAC-SHA256(AUTH_COOKIE_KEY, init_ts || "REVISOR-CONTRATUAL-GENESIS")

`.audit-genesis.lock` armazena (init_ts, hmac_hash) em arquivo separado read-only.
get_genesis_hash() valida o lock via compare_digest constant-time antes de retornar.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Default paths (parametrizáveis em chamador para testes)
DEFAULT_AUDIT_DIR = Path("bloco_audit")
DEFAULT_GENESIS_LOCK = DEFAULT_AUDIT_DIR / ".audit-genesis.lock"

GENESIS_PAYLOAD_SUFFIX = "REVISOR-CONTRATUAL-GENESIS"
"""Sufixo imutável do payload HMAC. Se mudar, invalida TODOS os audits anteriores."""


# ──────────────────────────────────────────────────────────────────────────────
# Exceções
# ──────────────────────────────────────────────────────────────────────────────


class GenesisError(RuntimeError):
    """Erro genérico de operações com .audit-genesis.lock."""


class GenesisAlreadyInitialized(GenesisError):
    """Tentativa de re-inicializar .audit-genesis.lock existente — operação destrutiva."""


class GenesisLockMissing(GenesisError):
    """Tentativa de uso sem .audit-genesis.lock inicializado."""


class GenesisLockTampered(GenesisError):
    """HMAC do .audit-genesis.lock inválido — adulteração detectada OU AUTH_COOKIE_KEY rotacionada."""


class GenesisLockCorrupt(GenesisError):
    """Formato de .audit-genesis.lock inválido (não 2 linhas)."""


class AuthCookieKeyMissing(GenesisError):
    """AUTH_COOKIE_KEY não configurada no env."""


# ──────────────────────────────────────────────────────────────────────────────
# Cálculo HMAC
# ──────────────────────────────────────────────────────────────────────────────


def compute_genesis_hash(project_init_ts: str, secret_key: bytes) -> str:
    """HMAC-SHA256(secret_key, init_ts || '|' || GENESIS_SUFFIX) em hex.

    Args:
        project_init_ts: timestamp ISO 8601 da inicialização do projeto
        secret_key: AUTH_COOKIE_KEY em bytes (não vazio)

    Returns:
        Hash hex (64 chars).

    Raises:
        ValueError se secret_key vazio ou init_ts vazio.
    """
    if not secret_key:
        raise ValueError("secret_key vazia — AUTH_COOKIE_KEY ausente")
    if not project_init_ts:
        raise ValueError("project_init_ts vazio")
    msg = f"{project_init_ts}|{GENESIS_PAYLOAD_SUFFIX}".encode("utf-8")
    return hmac.new(secret_key, msg, hashlib.sha256).hexdigest()


def _get_secret_key() -> bytes:
    """Lê AUTH_COOKIE_KEY do env. Levanta AuthCookieKeyMissing se ausente."""
    key = os.environ.get("AUTH_COOKIE_KEY", "")
    if not key:
        raise AuthCookieKeyMissing(
            "AUTH_COOKIE_KEY não configurada no .env. "
            "Necessária para HMAC GENESIS (ADR-005). "
            "Gerar com: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return key.encode("utf-8")


# ──────────────────────────────────────────────────────────────────────────────
# Inicialização (rodar 1× no setup)
# ──────────────────────────────────────────────────────────────────────────────


def initialize_audit_genesis(
    *,
    lock_path: Path | None = None,
    secret_key: bytes | None = None,
    init_ts: str | None = None,
) -> str:
    """Inicializa .audit-genesis.lock UMA vez no setup do projeto.

    Args:
        lock_path: caminho do arquivo lock (default DEFAULT_GENESIS_LOCK).
        secret_key: AUTH_COOKIE_KEY em bytes (default do env).
        init_ts: timestamp de inicialização (default now() UTC ISO 8601).

    Returns:
        Hash GENESIS calculado (hex).

    Raises:
        GenesisAlreadyInitialized: se lock já existe.
        AuthCookieKeyMissing: se AUTH_COOKIE_KEY ausente no env (e secret_key não fornecido).
    """
    path = lock_path if lock_path is not None else DEFAULT_GENESIS_LOCK
    if path.exists():
        raise GenesisAlreadyInitialized(
            f"GENESIS já inicializado em {path}. NÃO recriar — invalidaria audit log existente. "
            "Para rotação segura: ver docs/sop-rotacao-auth-cookie-key.md (DP-NOVO ADR-005)."
        )

    key = secret_key if secret_key is not None else _get_secret_key()
    ts = init_ts if init_ts is not None else datetime.now(timezone.utc).isoformat()

    genesis_hash = compute_genesis_hash(ts, key)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{ts}\n{genesis_hash}\n", encoding="utf-8")

    # chmod 400 (read-only owner) — Linux/Mac POSIX
    if sys.platform != "win32":
        os.chmod(path, 0o400)
    # Windows: ACL via icacls é responsabilidade do FR-SETUP-01 wizard (DP-NOVO)

    return genesis_hash


# ──────────────────────────────────────────────────────────────────────────────
# Leitura validada (cada append/verify chama esta fn)
# ──────────────────────────────────────────────────────────────────────────────


def get_genesis_hash(
    *,
    lock_path: Path | None = None,
    secret_key: bytes | None = None,
) -> str:
    """Lê .audit-genesis.lock E VALIDA HMAC antes de retornar.

    Adulteração do lock OU rotação de AUTH_COOKIE_KEY → GenesisLockTampered.
    Comparação constant-time via hmac.compare_digest.

    Returns:
        Hash GENESIS hex (validado).

    Raises:
        GenesisLockMissing: arquivo ausente.
        GenesisLockCorrupt: formato inválido.
        GenesisLockTampered: HMAC inválido.
    """
    path = lock_path if lock_path is not None else DEFAULT_GENESIS_LOCK

    if not path.exists():
        raise GenesisLockMissing(
            f"{path} ausente. Rodar initialize_audit_genesis() no setup."
        )

    content = path.read_text(encoding="utf-8").strip().split("\n")
    if len(content) != 2:
        raise GenesisLockCorrupt(
            f"{path} corrompido — formato esperado: 2 linhas (init_ts, hmac). "
            f"Encontrado: {len(content)} linhas."
        )

    init_ts, stored_hash = content
    key = secret_key if secret_key is not None else _get_secret_key()
    expected_hash = compute_genesis_hash(init_ts, key)

    if not hmac.compare_digest(stored_hash, expected_hash):
        raise GenesisLockTampered(
            f"GENESIS HMAC INVÁLIDO em {path}. "
            f"Adulteração detectada OU AUTH_COOKIE_KEY rotacionada. "
            f"AUDIT LOG COMPROMETIDO — investigar imediatamente."
        )

    return stored_hash
