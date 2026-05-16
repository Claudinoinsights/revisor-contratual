"""Integration tests for restic backup encryption — Sprint 8 Phase B Story #11.

ADR-031 spec: restic AES-256-CTR + Poly1305 MAC + scrypt KDF.
Smith F-HIGH-09: backups plaintext readable em filesystem-level (resolves architecturally).
LGPD §46 (segurança técnica) + §11 (prevenção) defense-in-depth baseline.

Pattern: pytest.MonkeyPatch (env vars) + unittest.mock.MagicMock (subprocess.run mock).
TD-SP06-PYTEST-DEPS preserved — runs em container post-Operator deploy (host sqlalchemy ausente).

Refs:
- ADR-031 §APScheduler Integration + §Spec Coverage
- ADR-029 §Backup Mechanism (preserved BackgroundScheduler + CronTrigger)
- Smith ultrathink F-HIGH-09 (governance/qa/smith-ultrathink-aplicacao-completa-hardware-2026-05-16.md:213-217)
- handoff-architect-to-dev-2026-05-16-sprint-8-phase-b-story-11-restic-impl.yaml
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def test_backup_daily_encrypted_invokes_restic_with_correct_args(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """AC_NEO_2: backup_daily_encrypted() invokes restic with ADR-031 spec args.

    Verifica:
    - subprocess.run invocado com ['restic', '-r', REPO, '-p', PW, 'backup', ...targets, '--tag', 'daily', '--host', 'revisor-prod']
    - Targets incluem vault.db + audit.jsonl (apenas os que existem)
    - timeout=300s + capture_output=True + text=True
    """
    # Setup tmp data dir com vault.db + audit.jsonl
    monkeypatch.setenv("REVISOR_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("RESTIC_REPOSITORY", "/test/repo")
    monkeypatch.setenv("RESTIC_PASSWORD_FILE", "/test/pw.txt")
    (tmp_path / "vault.db").write_bytes(b"sqlite-mock")
    (tmp_path / "audit.jsonl").write_text('{"entry": 1}\n')

    # Mock subprocess.run para capturar invocation
    mock_run = MagicMock()
    mock_run.return_value = MagicMock(returncode=0, stdout="snapshot abc123 saved\n", stderr="")
    monkeypatch.setattr("bloco_backup.scheduler.subprocess.run", mock_run)

    from bloco_backup.scheduler import backup_daily_encrypted
    backup_daily_encrypted()

    assert mock_run.call_count == 1, "subprocess.run deve ser invocado exatamente 1x"
    args, kwargs = mock_run.call_args
    cmd = args[0]

    # Verifica estrutura do cmd
    assert cmd[0] == "restic", "primeiro arg deve ser restic"
    assert "-r" in cmd and "/test/repo" in cmd, "repo flag + path"
    assert "-p" in cmd and "/test/pw.txt" in cmd, "password file flag + path"
    assert "backup" in cmd, "subcommand backup"
    assert str(tmp_path / "vault.db") in cmd, "vault.db target presente"
    assert str(tmp_path / "audit.jsonl") in cmd, "audit.jsonl target presente"
    assert "--tag" in cmd and "daily" in cmd, "tag daily presente"
    assert "--host" in cmd and "revisor-prod" in cmd, "host revisor-prod presente"

    # Verifica kwargs (subprocess hygiene)
    assert kwargs.get("capture_output") is True
    assert kwargs.get("text") is True
    assert kwargs.get("timeout") == 300


def test_backup_daily_encrypted_raises_runtimeerror_on_nonzero_returncode(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """AC_NEO_4: subprocess returncode != 0 → RuntimeError com stderr embedded."""
    monkeypatch.setenv("REVISOR_DATA_DIR", str(tmp_path))
    (tmp_path / "vault.db").write_bytes(b"sqlite-mock")

    mock_run = MagicMock()
    mock_run.return_value = MagicMock(
        returncode=1,
        stdout="",
        stderr="restic: unable to open config file: stat /repo/config: no such file",
    )
    monkeypatch.setattr("bloco_backup.scheduler.subprocess.run", mock_run)

    from bloco_backup.scheduler import backup_daily_encrypted
    with pytest.raises(RuntimeError, match="rc=1"):
        backup_daily_encrypted()


def test_cleanup_old_snapshots_encrypted_uses_retention_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC_NEO_3: cleanup_old_snapshots_encrypted() respeita REVISOR_BACKUP_RETENTION_DAYS (Story #14 integration).

    Verifica que retention env=60 produz --keep-within 60d (não default 30).
    """
    monkeypatch.setenv("REVISOR_BACKUP_RETENTION_DAYS", "60")
    monkeypatch.setenv("RESTIC_REPOSITORY", "/test/repo")
    monkeypatch.setenv("RESTIC_PASSWORD_FILE", "/test/pw.txt")

    mock_run = MagicMock()
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="remove 2 snapshots:\nID 1\nID 2\n",
        stderr="",
    )
    monkeypatch.setattr("bloco_backup.scheduler.subprocess.run", mock_run)

    from bloco_backup.scheduler import cleanup_old_snapshots_encrypted
    deleted = cleanup_old_snapshots_encrypted()

    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert "forget" in cmd
    assert "--keep-within" in cmd
    assert "60d" in cmd, "retention env=60 deve produzir --keep-within 60d"
    assert "--prune" in cmd
    assert kwargs.get("timeout") == 600
    # Best-effort parse de "remove 2 snapshots" deve retornar 2
    assert deleted == 2, "parse de 'remove N snapshots' deve retornar N"


def test_restic_repository_env_default_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC_NEO_5a: _restic_repo() retorna DEFAULT_RESTIC_REPO quando RESTIC_REPOSITORY unset."""
    monkeypatch.delenv("RESTIC_REPOSITORY", raising=False)
    from bloco_backup.scheduler import DEFAULT_RESTIC_REPO, _restic_repo
    assert _restic_repo() == str(DEFAULT_RESTIC_REPO)
    # Default path termina em restic-repo
    assert _restic_repo().endswith("restic-repo")


def test_restic_password_file_env_default_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC_NEO_5b: _restic_password_file() retorna /etc/restic/password.txt quando env unset."""
    monkeypatch.delenv("RESTIC_PASSWORD_FILE", raising=False)
    from bloco_backup.scheduler import _restic_password_file
    assert _restic_password_file() == "/etc/restic/password.txt"


def test_get_jobs_diagnostic_returns_all_4_jobs() -> None:
    """AC_F_MED_02: get_jobs_diagnostic() returns 4 jobs without scheduler.start().

    Smith F-S8PB-MV-MED-02 fix: scheduler introspection via job.next_run_time
    raises AttributeError when scheduler is NOT started. get_jobs_diagnostic()
    helper avoids that — returns metadata via trigger string representation.

    Verifies all 4 ADR-031 §Migration Plan co-existence jobs registered:
    - backup_daily (legacy plaintext)
    - backup_rotation (legacy rotation)
    - backup_daily_encrypted (NEW restic AES-256-CTR)
    - cleanup_old_snapshots_encrypted (NEW restic forget+prune)
    """
    from bloco_backup.scheduler import get_jobs_diagnostic
    jobs = get_jobs_diagnostic()
    assert len(jobs) == 4, f"Expected 4 jobs, got {len(jobs)}"
    ids = {j["id"] for j in jobs}
    expected = {
        "backup_daily",
        "backup_rotation",
        "backup_daily_encrypted",
        "cleanup_old_snapshots_encrypted",
    }
    assert ids == expected, f"Job IDs mismatch — expected {expected}, got {ids}"
    # Verify all 4 fields present in each dict
    for j in jobs:
        assert "id" in j, f"job missing 'id' field: {j}"
        assert "name" in j, f"job missing 'name' field: {j}"
        assert "trigger_str" in j, f"job missing 'trigger_str' field: {j}"
        assert "trigger_type" in j, f"job missing 'trigger_type' field: {j}"
        # trigger_type should be CronTrigger or IntervalTrigger
        assert j["trigger_type"] in {"CronTrigger", "IntervalTrigger"}, (
            f"unexpected trigger_type: {j['trigger_type']}"
        )
