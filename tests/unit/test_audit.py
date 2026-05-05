"""Testes unitários do bloco_audit (HMAC GENESIS + chain Merkle).

Cobertura: ADR-005 R-NEW-SMITH-03 absorvida + FR-AUDIT-01 estendido.
Testes adversariais: tentativas de forge GENESIS, tampering de chain, edge cases.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from bloco_audit import (
    AuditIntegrityError,
    AuthCookieKeyMissing,
    GenesisAlreadyInitialized,
    GenesisLockCorrupt,
    GenesisLockMissing,
    GenesisLockTampered,
    append_audit_entry,
    compute_genesis_hash,
    get_genesis_hash,
    initialize_audit_genesis,
    verify_audit_integrity,
)

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures — isolamento por teste via tmp_path
# ──────────────────────────────────────────────────────────────────────────────

SECRET_TEST = b"test-secret-key-deadbeef-0123456789abcdef" * 2  # 80 bytes
SECRET_OUTRO = b"outro-secret-key-feedface-fedcba9876543210" * 2  # 80 bytes


@pytest.fixture()
def lock_path(tmp_path: Path) -> Path:
    return tmp_path / ".audit-genesis.lock"


@pytest.fixture()
def audit_path(tmp_path: Path) -> Path:
    return tmp_path / "audit.jsonl"


@pytest.fixture()
def initialized_lock(lock_path: Path) -> Path:
    """Lock inicializado com SECRET_TEST."""
    initialize_audit_genesis(
        lock_path=lock_path, secret_key=SECRET_TEST, init_ts="2026-05-01T00:00:00+00:00"
    )
    return lock_path


# ──────────────────────────────────────────────────────────────────────────────
# compute_genesis_hash — propriedades criptográficas
# ──────────────────────────────────────────────────────────────────────────────


def test_compute_genesis_hash_deterministico():
    """Mesma entrada → mesmo hash sempre."""
    h1 = compute_genesis_hash("2026-05-01T00:00:00+00:00", SECRET_TEST)
    h2 = compute_genesis_hash("2026-05-01T00:00:00+00:00", SECRET_TEST)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_compute_genesis_hash_secret_diferente_resultado_diferente():
    """Chaves diferentes produzem hashes diferentes (HMAC depende da chave)."""
    h1 = compute_genesis_hash("2026-05-01T00:00:00+00:00", SECRET_TEST)
    h2 = compute_genesis_hash("2026-05-01T00:00:00+00:00", SECRET_OUTRO)
    assert h1 != h2


def test_compute_genesis_hash_ts_diferente_resultado_diferente():
    h1 = compute_genesis_hash("2026-05-01T00:00:00+00:00", SECRET_TEST)
    h2 = compute_genesis_hash("2026-05-02T00:00:00+00:00", SECRET_TEST)
    assert h1 != h2


def test_compute_genesis_hash_secret_vazio_falha():
    with pytest.raises(ValueError, match="secret_key vazia"):
        compute_genesis_hash("2026-05-01T00:00:00+00:00", b"")


def test_compute_genesis_hash_ts_vazio_falha():
    with pytest.raises(ValueError, match="project_init_ts vazio"):
        compute_genesis_hash("", SECRET_TEST)


# ──────────────────────────────────────────────────────────────────────────────
# initialize_audit_genesis
# ──────────────────────────────────────────────────────────────────────────────


def test_initialize_cria_lock_com_2_linhas(lock_path: Path):
    h = initialize_audit_genesis(
        lock_path=lock_path, secret_key=SECRET_TEST, init_ts="2026-05-01T00:00:00+00:00"
    )
    assert lock_path.exists()
    lines = lock_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert lines[0] == "2026-05-01T00:00:00+00:00"
    assert lines[1] == h


def test_initialize_falha_se_lock_ja_existe(initialized_lock: Path):
    with pytest.raises(GenesisAlreadyInitialized, match="invalidaria audit log"):
        initialize_audit_genesis(
            lock_path=initialized_lock, secret_key=SECRET_TEST,
            init_ts="2026-06-01T00:00:00+00:00",
        )


def test_initialize_sem_auth_cookie_key_no_env_falha(lock_path: Path, monkeypatch):
    """Se AUTH_COOKIE_KEY não está no env e secret_key não foi passado → falha."""
    monkeypatch.delenv("AUTH_COOKIE_KEY", raising=False)
    with pytest.raises(AuthCookieKeyMissing, match="AUTH_COOKIE_KEY não configurada"):
        initialize_audit_genesis(lock_path=lock_path)


def test_initialize_usa_now_como_default_ts(lock_path: Path):
    """Sem init_ts explícito, usa datetime.now() UTC ISO 8601."""
    initialize_audit_genesis(lock_path=lock_path, secret_key=SECRET_TEST)
    ts_line = lock_path.read_text(encoding="utf-8").strip().split("\n")[0]
    # Deve parsear como ISO 8601
    parsed = datetime.fromisoformat(ts_line)
    assert parsed.tzinfo is not None  # tem timezone


# ──────────────────────────────────────────────────────────────────────────────
# get_genesis_hash — validação HMAC contra adulteração
# ──────────────────────────────────────────────────────────────────────────────


def test_get_genesis_hash_lock_ausente_falha(lock_path: Path):
    with pytest.raises(GenesisLockMissing, match="initialize_audit_genesis"):
        get_genesis_hash(lock_path=lock_path, secret_key=SECRET_TEST)


def test_get_genesis_hash_lock_corrompido_1_linha_falha(lock_path: Path):
    lock_path.write_text("apenas_uma_linha\n", encoding="utf-8")
    with pytest.raises(GenesisLockCorrupt, match="2 linhas"):
        get_genesis_hash(lock_path=lock_path, secret_key=SECRET_TEST)


def test_get_genesis_hash_secret_rotacionada_falha(initialized_lock: Path):
    """ADR-005 ataque cenário: AUTH_COOKIE_KEY foi rotacionada → HMAC inválido."""
    with pytest.raises(GenesisLockTampered, match="AUDIT LOG COMPROMETIDO"):
        get_genesis_hash(lock_path=initialized_lock, secret_key=SECRET_OUTRO)


def test_get_genesis_hash_lock_adulterado_hash_falha(initialized_lock: Path):
    """Attacker substitui hash no lock por valor inventado → detectado."""
    # initialize_audit_genesis aplica chmod 400 (read-only owner POSIX); attacker
    # precisa restaurar write antes de adulterar. Em Windows chmod é no-op.
    initialized_lock.chmod(0o600)
    lines = initialized_lock.read_text(encoding="utf-8").strip().split("\n")
    fake_hash = "f" * 64  # hash forjado
    initialized_lock.write_text(f"{lines[0]}\n{fake_hash}\n", encoding="utf-8")
    with pytest.raises(GenesisLockTampered):
        get_genesis_hash(lock_path=initialized_lock, secret_key=SECRET_TEST)


def test_get_genesis_hash_lock_adulterado_ts_falha(initialized_lock: Path):
    """Attacker muda init_ts (mantém hash original) → HMAC recalculado diverge → detectado."""
    initialized_lock.chmod(0o600)  # destrava write (chmod 400 default em POSIX)
    lines = initialized_lock.read_text(encoding="utf-8").strip().split("\n")
    fake_ts = "1970-01-01T00:00:00+00:00"
    initialized_lock.write_text(f"{fake_ts}\n{lines[1]}\n", encoding="utf-8")
    with pytest.raises(GenesisLockTampered):
        get_genesis_hash(lock_path=initialized_lock, secret_key=SECRET_TEST)


def test_get_genesis_hash_round_trip_correto(initialized_lock: Path):
    """Init + get com mesma chave/ts → mesmo hash."""
    h = get_genesis_hash(lock_path=initialized_lock, secret_key=SECRET_TEST)
    expected = compute_genesis_hash("2026-05-01T00:00:00+00:00", SECRET_TEST)
    assert h == expected


# ──────────────────────────────────────────────────────────────────────────────
# append_audit_entry — chain integrity
# ──────────────────────────────────────────────────────────────────────────────


def test_append_primeira_entry_referencia_genesis(initialized_lock: Path, audit_path: Path):
    """Primeira entry: previous_entry_hash = GENESIS hash."""
    h_genesis = get_genesis_hash(lock_path=initialized_lock, secret_key=SECRET_TEST)
    append_audit_entry(
        "login",
        {"user": "advogado_x", "ip": "192.168.0.1"},
        audit_path=audit_path,
        genesis_lock_path=initialized_lock,
        secret_key=SECRET_TEST,
        timestamp=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    line = audit_path.read_text(encoding="utf-8").strip()
    entry = json.loads(line)
    assert entry["previous_entry_hash"] == h_genesis
    assert entry["event_type"] == "login"
    assert entry["payload"]["user"] == "advogado_x"


def test_append_segunda_entry_referencia_primeira(initialized_lock: Path, audit_path: Path):
    h1 = append_audit_entry(
        "login", {"user": "x"},
        audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
        timestamp=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    h2 = append_audit_entry(
        "tese_gerada", {"hash_peca": "abc123"},
        audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
        timestamp=datetime(2026, 5, 1, 12, 5, 0, tzinfo=timezone.utc),
    )
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    entry1 = json.loads(lines[0])
    entry2 = json.loads(lines[1])
    assert entry1["entry_hash"] == h1
    assert entry2["previous_entry_hash"] == h1
    assert entry2["entry_hash"] == h2
    assert h1 != h2


def test_append_acentos_pt_br_preservados(initialized_lock: Path, audit_path: Path):
    """ensure_ascii=False mantém acentos sem escape."""
    append_audit_entry(
        "decisao_hitl",
        {"justificativa": "Aprovo apesar do risco — precedente análogo no TJBA"},
        audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
    )
    raw = audit_path.read_text(encoding="utf-8")
    assert "análogo" in raw  # não escapado para "análogo"


# ──────────────────────────────────────────────────────────────────────────────
# verify_audit_integrity — happy path + adversarial
# ──────────────────────────────────────────────────────────────────────────────


def test_verify_audit_vazio_eh_integro(initialized_lock: Path, audit_path: Path):
    """Audit vazio com GENESIS válido → íntegro."""
    assert verify_audit_integrity(
        audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
    ) is True


def test_verify_audit_chain_correta_eh_integro(initialized_lock: Path, audit_path: Path):
    for i in range(5):
        append_audit_entry(
            f"event_{i}", {"i": i},
            audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
        )
    assert verify_audit_integrity(
        audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
    ) is True


def test_verify_detecta_linha_alterada(initialized_lock: Path, audit_path: Path):
    """Tampering: attacker altera payload de uma linha → entry_hash não bate."""
    for i in range(3):
        append_audit_entry(
            "event", {"i": i},
            audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
        )
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    entry = json.loads(lines[1])
    entry["payload"]["i"] = 999  # adulteração
    lines[1] = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    audit_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(AuditIntegrityError, match="entry_hash adulterado"):
        verify_audit_integrity(
            audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
        )


def test_verify_detecta_linha_removida(initialized_lock: Path, audit_path: Path):
    """Attacker remove a linha 2 → linha 3 fica órfã (previous_entry_hash não bate)."""
    for i in range(3):
        append_audit_entry(
            "event", {"i": i},
            audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
        )
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    audit_path.write_text(lines[0] + "\n" + lines[2] + "\n", encoding="utf-8")  # pula linha 1

    with pytest.raises(AuditIntegrityError, match="previous_entry_hash divergente"):
        verify_audit_integrity(
            audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
        )


def test_verify_detecta_genesis_forge_attempt(initialized_lock: Path, audit_path: Path):
    """ATAQUE CENÁRIO Smith F-CRIT-A original (resolvido em ADR-005):

    Attacker:
    1. Cria entry forjada com previous_entry_hash="GENESIS" string literal
    2. Re-hashera as entries seguintes com a forjada como root

    Defesa: get_genesis_hash() valida HMAC do .audit-genesis.lock; previous_entry_hash
    real esperado é o HMAC, NÃO a string literal "GENESIS".
    """
    # Forja: cria audit.jsonl com primeira entry referenciando "GENESIS" literal
    fake_entry = {
        "ts": "2026-05-01T12:00:00+00:00",
        "event_type": "FORJADO",
        "payload": {"x": 1},
        "previous_entry_hash": "GENESIS",  # ← string literal forjada
    }
    fake_entry_serial = json.dumps(fake_entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    import hashlib as _h
    fake_entry["entry_hash"] = _h.sha256(fake_entry_serial.encode("utf-8")).hexdigest()
    audit_path.write_text(
        json.dumps(fake_entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Defesa funciona: previous_entry_hash esperado é HMAC, não "GENESIS"
    with pytest.raises(AuditIntegrityError, match="previous_entry_hash divergente"):
        verify_audit_integrity(
            audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
        )


def test_verify_falha_se_genesis_lock_adulterado(initialized_lock: Path, audit_path: Path):
    """Adulteração do .audit-genesis.lock → verify falha em get_genesis_hash()."""
    append_audit_entry(
        "x", {},
        audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
    )
    # Adultera o lock (chmod 600 destrava write — em Windows é no-op; em POSIX
    # initialize_audit_genesis aplica chmod 400 read-only owner)
    initialized_lock.chmod(0o600)
    lines = initialized_lock.read_text(encoding="utf-8").strip().split("\n")
    initialized_lock.write_text(f"1970-01-01T00:00:00+00:00\n{lines[1]}\n", encoding="utf-8")

    with pytest.raises(GenesisLockTampered):
        verify_audit_integrity(
            audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
        )


def test_verify_falha_se_json_invalido_em_alguma_linha(initialized_lock: Path, audit_path: Path):
    append_audit_entry(
        "x", {},
        audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
    )
    audit_path.write_text(audit_path.read_text(encoding="utf-8") + "isso_nao_eh_json\n", encoding="utf-8")
    with pytest.raises(AuditIntegrityError, match="JSON inválido"):
        verify_audit_integrity(
            audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Performance — chain de 1000 entries em <1s (FR-AUDIT-01 promete <5s para 10k)
# ──────────────────────────────────────────────────────────────────────────────


def test_verify_chain_1000_entries_rapido(initialized_lock: Path, audit_path: Path):
    """Sanity check de O(N): 1000 entries devem verificar em <2s em CI lento."""
    import time

    for i in range(1000):
        append_audit_entry(
            "x", {"i": i},
            audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
        )

    t0 = time.perf_counter()
    assert verify_audit_integrity(
        audit_path=audit_path, genesis_lock_path=initialized_lock, secret_key=SECRET_TEST,
    ) is True
    elapsed = time.perf_counter() - t0
    assert elapsed < 2.0, f"verify levou {elapsed:.2f}s para 1k entries (esperado <2s)"
