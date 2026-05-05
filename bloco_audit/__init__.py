"""bloco_audit — Audit log forense-grade (FR-AUDIT-01 + ADR-005).

Componentes:
  - genesis.py — HMAC GENESIS anchor com AUTH_COOKIE_KEY (R-NEW-SMITH-03 absorvido)
  - chain.py — Hash chain Merkle do audit.jsonl (append-only)

Excepções importantes:
  - GenesisLockTampered → adulteração ou rotação AUTH_COOKIE_KEY
  - AuditIntegrityError → cadeia hash quebrada
"""

from bloco_audit.chain import (
    DEFAULT_AUDIT_LOG,
    AuditChainError,
    AuditIntegrityError,
    append_audit_entry,
    verify_audit_integrity,
)
from bloco_audit.genesis import (
    DEFAULT_GENESIS_LOCK,
    AuthCookieKeyMissing,
    GenesisAlreadyInitialized,
    GenesisError,
    GenesisLockCorrupt,
    GenesisLockMissing,
    GenesisLockTampered,
    compute_genesis_hash,
    get_genesis_hash,
    initialize_audit_genesis,
)

__all__ = [
    # genesis
    "compute_genesis_hash",
    "initialize_audit_genesis",
    "get_genesis_hash",
    "DEFAULT_GENESIS_LOCK",
    # chain
    "append_audit_entry",
    "verify_audit_integrity",
    "DEFAULT_AUDIT_LOG",
    # exceções
    "GenesisError",
    "GenesisAlreadyInitialized",
    "GenesisLockMissing",
    "GenesisLockTampered",
    "GenesisLockCorrupt",
    "AuthCookieKeyMissing",
    "AuditChainError",
    "AuditIntegrityError",
]
