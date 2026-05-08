"""Hash chain Merkle do audit.jsonl (FR-AUDIT-01 estendido — ADR-005).

Append-only: cada entry tem `previous_entry_hash` apontando para entry[N-1].
Primeira entry: previous_entry_hash = GENESIS_HASH (HMAC ancorado em ADR-005).

Comando CLI verify_audit_integrity recalcula chain inteira em O(N).
Tampering manual (editar/inserir/remover linha) → detectável em <5s para 10k entries.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bloco_audit.genesis import get_genesis_hash

# CC.31 fix TD-AUDIT-PATH-MISMATCH: alinhado com cli.py + scheduler.py +
# auto_trigger.py. Antes era Path("bloco_audit/audit.jsonl") relativo.
# CC.40 fix F-12: respeita XDG_DATA_HOME para containers/serverless.
_XDG_DATA_HOME = Path(
    os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
)
DEFAULT_AUDIT_LOG = _XDG_DATA_HOME / "revisor-contratual" / "audit.jsonl"


# ──────────────────────────────────────────────────────────────────────────────
# Exceções
# ──────────────────────────────────────────────────────────────────────────────


class AuditChainError(RuntimeError):
    """Erro genérico de operações com audit.jsonl."""


class AuditIntegrityError(AuditChainError):
    """Cadeia hash quebrada — adulteração detectada."""


# ──────────────────────────────────────────────────────────────────────────────
# Serialização canônica (essencial para hash determinístico)
# ──────────────────────────────────────────────────────────────────────────────


def _canonical_serialize(entry: dict[str, Any]) -> str:
    """Serialização determinística para hashing.

    sort_keys=True (ordem estável)
    separators=(',', ':') (sem espaços extras)
    ensure_ascii=False (preserva acentos PT-BR sem escape)
    """
    return json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash_entry(entry: dict[str, Any]) -> str:
    """SHA-256 hex do entry serializado canonicamente (sem campo entry_hash)."""
    payload = {k: v for k, v in entry.items() if k != "entry_hash"}
    return hashlib.sha256(_canonical_serialize(payload).encode("utf-8")).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Leitura eficiente da última linha (sem ler arquivo inteiro)
# ──────────────────────────────────────────────────────────────────────────────


def _last_entry_hash(audit_path: Path) -> str | None:
    """Retorna entry_hash da última linha. None se arquivo vazio/inexistente."""
    if not audit_path.exists() or audit_path.stat().st_size == 0:
        return None

    # Lê última linha eficientemente via seek do final
    with open(audit_path, "rb") as f:
        try:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b"\n":
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            # Arquivo com 1 linha sem newline final → ler tudo
            f.seek(0)
        last_line_bytes = f.readline()

    last_line = last_line_bytes.decode("utf-8").strip()
    if not last_line:
        return None
    try:
        entry = json.loads(last_line)
    except json.JSONDecodeError as e:
        raise AuditChainError(f"Última linha de {audit_path} não é JSON válido: {e}") from e
    return entry.get("entry_hash")


# ──────────────────────────────────────────────────────────────────────────────
# Append (FR-AUDIT-01 — append-only)
# ──────────────────────────────────────────────────────────────────────────────


def append_audit_entry(
    event_type: str,
    payload: dict[str, Any],
    *,
    audit_path: Path | None = None,
    genesis_lock_path: Path | None = None,
    secret_key: bytes | None = None,
    timestamp: datetime | None = None,
) -> str:
    """Adiciona entry ao audit.jsonl com hash chain.

    Args:
        event_type: tipo do evento (ex: 'login', 'tese_gerada', 'CRITICAL_ALERT')
        payload: dados estruturados do evento
        audit_path: arquivo audit.jsonl (default DEFAULT_AUDIT_LOG)
        genesis_lock_path: caminho .audit-genesis.lock (default DEFAULT_GENESIS_LOCK)
        secret_key: AUTH_COOKIE_KEY (default do env)
        timestamp: datetime do evento (default now() UTC)

    Returns:
        entry_hash hex da entry recém-adicionada.
    """
    path = audit_path if audit_path is not None else DEFAULT_AUDIT_LOG

    last_hash = _last_entry_hash(path)
    if last_hash is None:
        last_hash = get_genesis_hash(lock_path=genesis_lock_path, secret_key=secret_key)

    ts = timestamp if timestamp is not None else datetime.now(timezone.utc)

    entry: dict[str, Any] = {
        "ts": ts.isoformat(),
        "event_type": event_type,
        "payload": payload,
        "previous_entry_hash": last_hash,
    }
    entry["entry_hash"] = _hash_entry(entry)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(_canonical_serialize(entry) + "\n")

    return entry["entry_hash"]


# ──────────────────────────────────────────────────────────────────────────────
# Verificação de integridade (CLI verify-audit-integrity)
# ──────────────────────────────────────────────────────────────────────────────


def verify_audit_integrity(
    *,
    audit_path: Path | None = None,
    genesis_lock_path: Path | None = None,
    secret_key: bytes | None = None,
) -> bool:
    """Verifica chain inteira do audit.jsonl. O(N) — <5s para 10k entries.

    Detecta:
      - GENESIS lock adulterado/ausente (delegado a get_genesis_hash)
      - previous_entry_hash divergente (linha inserida/removida/reordenada)
      - entry_hash adulterado (campo dentro da entry alterado manualmente)

    Returns:
        True se chain íntegra do GENESIS à última entry.

    Raises:
        AuditIntegrityError: detalhada (linha, hash esperado vs obtido).
    """
    path = audit_path if audit_path is not None else DEFAULT_AUDIT_LOG
    expected_genesis = get_genesis_hash(
        lock_path=genesis_lock_path, secret_key=secret_key
    )

    if not path.exists() or path.stat().st_size == 0:
        # Audit vazio é ok desde que GENESIS esteja válido
        return True

    prev_hash = expected_genesis
    with open(path, encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                raise AuditIntegrityError(
                    f"Linha {line_no}: JSON inválido — {e}"
                ) from e

            stored_prev = entry.get("previous_entry_hash")
            if stored_prev != prev_hash:
                raise AuditIntegrityError(
                    f"Linha {line_no}: previous_entry_hash divergente. "
                    f"Esperado={prev_hash[:16]}..., obtido={(stored_prev or '<missing>')[:16]}..."
                )

            stored_hash = entry.get("entry_hash")
            recomputed = _hash_entry(entry)
            if stored_hash != recomputed:
                raise AuditIntegrityError(
                    f"Linha {line_no}: entry_hash adulterado. "
                    f"Esperado={recomputed[:16]}..., obtido={(stored_hash or '<missing>')[:16]}..."
                )

            prev_hash = stored_hash  # avança chain

    return True
