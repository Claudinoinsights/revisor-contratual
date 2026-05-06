"""Integration tests for MVP-LEAN-01 Task 8 PARTIAL — LGPD L3+L4+L5 + APScheduler backup.

Cobertura:
- L3 Headers HTTP: CSP + X-Frame + X-Content-Type-Options + Referrer-Policy + Permissions-Policy
- L4 Encryption-at-rest: Fernet encrypt/decrypt + safe_delete LGPD compliant
- L5 Permissões filesystem: chmod cross-platform (POSIX 600/700; Windows skip)
- APScheduler: backup_daily + backup_rotation + scheduler create

Sessão 91 (CC.21 Task 8 PARTIAL).
"""

from __future__ import annotations

import os
import platform
import time
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import pytest
from cryptography.fernet import Fernet, InvalidToken
from fastapi.testclient import TestClient

from bloco_backup import scheduler as scheduler_mod
from bloco_lgpd import encryption, permissions
from bloco_lgpd.headers import CSP_VALUE, SECURITY_HEADERS

TEST_USERNAME = "tester"
TEST_PASSWORD = "test-pwd-123"  # noqa: S105
TEST_SECRET = "test-secret-key-for-integration-tests-only"  # noqa: S105


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    test_hash = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
    monkeypatch.setenv("ADMIN_USERNAME", TEST_USERNAME)
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", test_hash)
    monkeypatch.setenv("REVISOR_SECRET_KEY", TEST_SECRET)
    monkeypatch.setenv("REVISOR_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode("utf-8"))


@pytest.fixture
def client() -> Iterator[TestClient]:
    """TestClient autenticado + lifespan mockado."""
    with patch(
        "bloco_interface.web.app.ollama_manager.acquire_app_lock", return_value=42
    ), patch(
        "bloco_interface.web.app.ollama_manager.cleanup_orphans_on_startup"
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_ollama_binary",
        return_value=MagicMock(),
    ), patch(
        "bloco_interface.web.app.ollama_manager.detect_running_ollama",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "bloco_interface.web.app.ollama_manager.spawn_ollama"
    ), patch(
        "bloco_interface.web.app.ollama_manager.write_pid_file_atomic"
    ), patch(
        "bloco_interface.web.app.ollama_manager.kill_spawned_ollama"
    ), patch(
        "bloco_interface.web.app.ollama_manager.release_app_lock"
    ), patch(
        "bloco_interface.web.app.ollama_manager.is_ready",
        return_value=True,
    ), patch(
        "bloco_interface.web.app.populate_vault_if_needed"
    ), patch(
        "bloco_interface.web.app.ollama_manager.ensure_models_pulled",
        new_callable=AsyncMock,
    ):
        from bloco_interface.web.app import app

        with TestClient(app) as tc:
            login_page = tc.get("/login")
            csrf_marker = 'name="csrf_token" value="'
            start = login_page.text.find(csrf_marker) + len(csrf_marker)
            end = login_page.text.find('"', start)
            csrf_token = login_page.text[start:end]
            tc.post(
                "/login",
                data={
                    "username": TEST_USERNAME,
                    "password": TEST_PASSWORD,
                    "csrf_token": csrf_token,
                },
            )
            yield tc


# ── L3 Headers HTTP CSP ───────────────────────────────────────────────────
@pytest.mark.integration
def test_csp_header_present_in_response(client: TestClient) -> None:
    """L3: CSP header presente em todos os responses."""
    response = client.get("/")
    assert "content-security-policy" in {h.lower() for h in response.headers}
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


@pytest.mark.integration
def test_security_headers_complete(client: TestClient) -> None:
    """L3: 5 headers de segurança presentes."""
    response = client.get("/")
    expected_headers = {
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "Content-Security-Policy",
    }
    response_headers_lower = {h.lower() for h in response.headers}
    for expected in expected_headers:
        assert expected.lower() in response_headers_lower, f"Missing: {expected}"


@pytest.mark.integration
def test_csp_allows_htmx_inline_styles() -> None:
    """L3: CSP permite style 'unsafe-inline' (HTMX requirement)."""
    assert "style-src 'self' 'unsafe-inline'" in CSP_VALUE


@pytest.mark.integration
def test_x_frame_options_deny() -> None:
    """L3: X-Frame-Options DENY (anti-clickjacking)."""
    assert SECURITY_HEADERS["X-Frame-Options"] == "DENY"


# ── L4 Encryption-at-rest Fernet ──────────────────────────────────────────
@pytest.mark.integration
def test_fernet_encrypt_decrypt_roundtrip() -> None:
    """L4: bytes → encrypt → decrypt = bytes original."""
    pdf_bytes = b"%PDF-1.4\nfake pdf content " * 100
    encrypted = encryption.encrypt_pdf(pdf_bytes)
    assert encrypted != pdf_bytes  # genuinamente cifrado
    decrypted = encryption.decrypt_pdf(encrypted)
    assert decrypted == pdf_bytes


@pytest.mark.integration
def test_fernet_key_invalid_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """L4: FERNET_KEY com formato inválido → InvalidToken."""
    monkeypatch.setenv("FERNET_KEY", "this-is-not-a-valid-fernet-key")
    with pytest.raises(InvalidToken):
        encryption.get_fernet_key()


@pytest.mark.integration
def test_fernet_key_missing_generates_ephemeral(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """L4: FERNET_KEY ausente → key efêmera com warning (similar SECRET_KEY pattern)."""
    monkeypatch.delenv("FERNET_KEY", raising=False)
    key = encryption.get_fernet_key()
    assert key is not None
    # Key efêmera deve ser válida Fernet
    Fernet(key)


@pytest.mark.integration
def test_safe_delete_overwrites_then_unlinks(tmp_path: Path) -> None:
    """L4: safe_delete overwrite + unlink (LGPD compliant)."""
    test_file = tmp_path / "secret.pdf"
    test_file.write_bytes(b"%PDF-1.4\nsensitive data" * 100)
    assert test_file.exists()
    result = encryption.safe_delete(test_file)
    assert result is True
    assert not test_file.exists()


@pytest.mark.integration
def test_safe_delete_idempotent_for_missing_file(tmp_path: Path) -> None:
    """L4: safe_delete em arquivo já ausente retorna True (idempotente)."""
    nonexistent = tmp_path / "never-existed.pdf"
    result = encryption.safe_delete(nonexistent)
    assert result is True


# ── L5 Permissões filesystem ──────────────────────────────────────────────
@pytest.mark.integration
@pytest.mark.skipif(platform.system() == "Windows", reason="POSIX chmod limitado em Windows")
def test_apply_audit_permissions_posix_600(tmp_path: Path) -> None:
    """L5: audit.jsonl chmod 600 em POSIX."""
    audit = tmp_path / "audit.jsonl"
    audit.write_text("{}\n")
    result = permissions.apply_audit_permissions(audit)
    assert result is True
    mode = audit.stat().st_mode & 0o777
    assert mode == 0o600


@pytest.mark.integration
@pytest.mark.skipif(platform.system() == "Windows", reason="POSIX chmod limitado em Windows")
def test_apply_uploads_dir_permissions_700(tmp_path: Path) -> None:
    """L5: uploads/ chmod 700 em POSIX."""
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    (uploads / "file.pdf").write_text("x")
    result = permissions.apply_uploads_dir_permissions(uploads)
    assert result is True
    mode = uploads.stat().st_mode & 0o777
    assert mode == 0o700


@pytest.mark.integration
def test_apply_audit_permissions_missing_path_returns_false(tmp_path: Path) -> None:
    """L5: path ausente → False (graceful)."""
    nonexistent = tmp_path / "no-audit.jsonl"
    assert permissions.apply_audit_permissions(nonexistent) is False


@pytest.mark.integration
def test_is_posix_returns_correct_value() -> None:
    """L5: is_posix() retorna True/False conforme OS."""
    expected = os.name == "posix"
    assert permissions.is_posix() == expected


# ── APScheduler backup ────────────────────────────────────────────────────
@pytest.mark.integration
def test_create_scheduler_has_3_jobs() -> None:
    """APScheduler: scheduler tem 3 jobs (backup_daily + backup_rotation + tema_1378_check Task 8b)."""
    sched = scheduler_mod.create_scheduler()
    job_ids = {job.id for job in sched.get_jobs()}
    assert "backup_daily" in job_ids
    assert "backup_rotation" in job_ids
    assert "tema_1378_check" in job_ids


@pytest.mark.integration
def test_backup_daily_creates_dated_dir(tmp_path: Path) -> None:
    """APScheduler: backup_daily copia vault.db + audit.jsonl para backups/{YYYY-MM-DD}/."""
    # Setup files
    (tmp_path / "vault.db").write_bytes(b"fake sqlite db content")
    (tmp_path / "audit.jsonl").write_text('{"type":"test"}\n')

    # Trigger
    target = scheduler_mod.backup_daily()
    assert target is not None
    assert target.exists()
    assert (target / "vault.db").exists()
    assert (target / "audit.jsonl").exists()


@pytest.mark.integration
def test_backup_rotation_deletes_old(tmp_path: Path) -> None:
    """APScheduler: backup_rotation deleta backups com mtime > 7 dias."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    # Backup recente (não deve ser deletado)
    recent = backup_dir / "2026-05-06"
    recent.mkdir()
    (recent / "vault.db").write_text("recent")

    # Backup antigo (mtime > 7 dias atrás)
    old = backup_dir / "2026-04-01"
    old.mkdir()
    (old / "vault.db").write_text("old")
    old_mtime = time.time() - (10 * 24 * 60 * 60)  # 10 dias atrás
    os.utime(old, (old_mtime, old_mtime))

    deleted_count = scheduler_mod.backup_rotation()
    assert deleted_count >= 1
    assert recent.exists()  # backup recente preservado
    assert not old.exists()  # backup antigo deletado


@pytest.mark.integration
def test_backup_rotation_no_dir_returns_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """APScheduler: backup_rotation sem diretório existente retorna 0 (graceful)."""
    # tmp_path/backups não existe
    monkeypatch.setenv("REVISOR_DATA_DIR", str(tmp_path / "nonexistent"))
    deleted = scheduler_mod.backup_rotation()
    assert deleted == 0
