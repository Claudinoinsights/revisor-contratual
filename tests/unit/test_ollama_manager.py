"""Unit tests for OLLAMA-MGR-01 (ADR-011) Phase A + Phase B.

Cobertura:
- AC-2 detect_ollama_binary cross-platform priority chain (6 cenários)
- AC-3 acquire_app_lock fcntl/msvcrt (2 cenários: success + already-locked)
- AC-9/EC-06 cleanup_orphans_on_startup com mock psutil
- AC-10 pre_check_disk_space mock disk_usage
- Phase B.2/B.3 write_pid_file_atomic + read_pid_file_safely roundtrip
- Phase B.4 process_is_ours edge cases

Sessão 88 (CC.6) — pós Phase A + Phase B.1-B.5 implementadas.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bloco_interface.ollama_manager import (
    AppAlreadyRunning,
    DiskSpaceInsufficient,
    acquire_app_lock,
    cleanup_orphans_on_startup,
    detect_ollama_binary,
    pre_check_disk_space,
    process_is_ours,
    read_pid_file_safely,
    release_app_lock,
    write_pid_file_atomic,
)

# ── A.2 detect_ollama_binary tests (6 cenários priority chain) ───────────


def test_detect_binary_env_var_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Priority 1: OLLAMA_BINARY_PATH env var aponta para arquivo válido."""
    fake = tmp_path / "fake_ollama"
    fake.touch()

    monkeypatch.setenv("OLLAMA_BINARY_PATH", str(fake))
    result = detect_ollama_binary()

    assert result == fake


def test_detect_binary_env_var_invalid_falls_through(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env var inválida (file não existe) → fallthrough para outros."""
    monkeypatch.setenv("OLLAMA_BINARY_PATH", "/nonexistent/fake/path")
    monkeypatch.setattr(sys, "platform", "linux")

    with patch.object(Path, "is_file", return_value=False):
        with patch("bloco_interface.ollama_manager.shutil.which", return_value=None):
            result = detect_ollama_binary()

    assert result is None


def test_detect_binary_windows_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Priority 2 Windows: %LOCALAPPDATA%/Programs/Ollama/ollama.exe."""
    fake_localappdata = tmp_path / "AppData" / "Local"
    expected = fake_localappdata / "Programs" / "Ollama" / "ollama.exe"
    expected.parent.mkdir(parents=True)
    expected.touch()

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(fake_localappdata))
    monkeypatch.delenv("OLLAMA_BINARY_PATH", raising=False)

    result = detect_ollama_binary()
    assert result == expected


def test_detect_binary_linux_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Priority 2 Linux: /usr/local/bin/ollama hit antes de /usr/bin/ollama."""
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("OLLAMA_BINARY_PATH", raising=False)

    expected = Path("/usr/local/bin/ollama")

    def is_file_mock(self: Path) -> bool:
        return str(self) == str(expected)

    with patch.object(Path, "is_file", is_file_mock):
        with patch("bloco_interface.ollama_manager.shutil.which", return_value=None):
            result = detect_ollama_binary()

    assert result == expected


def test_detect_binary_mac_homebrew(monkeypatch: pytest.MonkeyPatch) -> None:
    """Priority 2 macOS: /opt/homebrew/bin/ollama (Apple Silicon)."""
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.delenv("OLLAMA_BINARY_PATH", raising=False)

    expected = Path("/opt/homebrew/bin/ollama")

    def is_file_mock(self: Path) -> bool:
        return str(self) == str(expected)

    with patch.object(Path, "is_file", is_file_mock):
        with patch("bloco_interface.ollama_manager.shutil.which", return_value=None):
            result = detect_ollama_binary()

    assert result == expected


def test_detect_binary_path_search(monkeypatch: pytest.MonkeyPatch) -> None:
    """Priority 3: shutil.which('ollama') hit quando platform defaults falham."""
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("OLLAMA_BINARY_PATH", raising=False)

    with patch.object(Path, "is_file", return_value=False):
        with patch(
            "bloco_interface.ollama_manager.shutil.which", return_value="/custom/bin/ollama"
        ):
            result = detect_ollama_binary()

    assert result == Path("/custom/bin/ollama")


def test_detect_binary_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Priority 4: tudo falha → None (caller raises clear error)."""
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("OLLAMA_BINARY_PATH", raising=False)

    with patch.object(Path, "is_file", return_value=False):
        with patch("bloco_interface.ollama_manager.shutil.which", return_value=None):
            result = detect_ollama_binary()

    assert result is None


# ── A.3 acquire_app_lock tests ────────────────────────────────────────────


def test_acquire_lock_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Happy path: lock acquired retorna fd válido > 0."""
    monkeypatch.setattr("bloco_interface.ollama_manager.DATA_DIR", tmp_path)
    monkeypatch.setattr("bloco_interface.ollama_manager.LOCK_FILE", tmp_path / ".app.lock")

    fd = acquire_app_lock()
    try:
        assert isinstance(fd, int)
        assert fd >= 0
    finally:
        release_app_lock(fd)


def test_acquire_lock_already_locked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Segundo acquire da mesma file → AppAlreadyRunning."""
    monkeypatch.setattr("bloco_interface.ollama_manager.DATA_DIR", tmp_path)
    monkeypatch.setattr("bloco_interface.ollama_manager.LOCK_FILE", tmp_path / ".app.lock")

    fd1 = acquire_app_lock()
    try:
        with pytest.raises(AppAlreadyRunning):
            acquire_app_lock()
    finally:
        release_app_lock(fd1)


# ── A.4 cleanup_orphans tests ────────────────────────────────────────────


def test_cleanup_orphans_removes_orphan(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Mock psutil: 1 órfão Ollama do current user → terminate chamado."""
    monkeypatch.setattr("bloco_interface.ollama_manager.DATA_DIR", tmp_path)
    monkeypatch.setattr("bloco_interface.ollama_manager.PID_FILE", tmp_path / ".ollama-spawned.pid")

    current_proc_mock = MagicMock()
    current_proc_mock.username.return_value = "testuser"

    orphan_mock = MagicMock()
    orphan_mock.info = {"name": "ollama", "username": "testuser", "pid": 9999}

    other_user_mock = MagicMock()
    other_user_mock.info = {"name": "ollama", "username": "otheruser", "pid": 8888}

    not_ollama_mock = MagicMock()
    not_ollama_mock.info = {"name": "firefox", "username": "testuser", "pid": 7777}

    with patch("psutil.Process", return_value=current_proc_mock):
        with patch(
            "psutil.process_iter",
            return_value=[orphan_mock, other_user_mock, not_ollama_mock],
        ):
            cleanup_orphans_on_startup()

    orphan_mock.terminate.assert_called_once()
    other_user_mock.terminate.assert_not_called()
    not_ollama_mock.terminate.assert_not_called()


def test_cleanup_orphans_skips_tracked_pids(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """PID em PID file não é considerado órfão (não é terminado)."""
    monkeypatch.setattr("bloco_interface.ollama_manager.DATA_DIR", tmp_path)
    pid_file = tmp_path / ".ollama-spawned.pid"
    monkeypatch.setattr("bloco_interface.ollama_manager.PID_FILE", pid_file)

    # Cria PID file rastreando PID 9999
    write_pid_file_atomic({"advogado": 9999})

    current_proc_mock = MagicMock()
    current_proc_mock.username.return_value = "testuser"

    tracked_mock = MagicMock()
    tracked_mock.info = {"name": "ollama", "username": "testuser", "pid": 9999}

    with patch("psutil.Process", return_value=current_proc_mock):
        with patch("psutil.process_iter", return_value=[tracked_mock]):
            cleanup_orphans_on_startup()

    tracked_mock.terminate.assert_not_called()


# ── B.2/B.3 PID file write+read roundtrip ────────────────────────────────


def test_write_read_pid_file_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """write_pid_file_atomic + read_pid_file_safely roundtrip preserva mapping."""
    monkeypatch.setattr("bloco_interface.ollama_manager.DATA_DIR", tmp_path)
    monkeypatch.setattr("bloco_interface.ollama_manager.PID_FILE", tmp_path / ".ollama-spawned.pid")

    pids_in = {"advogado": 12345, "economista": 12346}
    write_pid_file_atomic(pids_in)
    pids_out = read_pid_file_safely()

    assert pids_out == pids_in


def test_read_pid_file_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """File não existe → returns dict vazio (não raise)."""
    monkeypatch.setattr("bloco_interface.ollama_manager.PID_FILE", tmp_path / "nonexistent.pid")

    result = read_pid_file_safely()
    assert result == {}


def test_read_pid_file_corrupt_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """JSON corrupto → returns dict vazio + logger warning."""
    pid_file = tmp_path / ".ollama-spawned.pid"
    pid_file.write_text("{this is not valid json")
    monkeypatch.setattr("bloco_interface.ollama_manager.PID_FILE", pid_file)

    result = read_pid_file_safely()
    assert result == {}


def test_read_pid_file_wrong_schema_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """schema_version incompatível → returns dict vazio."""
    pid_file = tmp_path / ".ollama-spawned.pid"
    pid_file.write_text('{"schema_version": "9.99", "instances": []}')
    monkeypatch.setattr("bloco_interface.ollama_manager.PID_FILE", pid_file)

    result = read_pid_file_safely()
    assert result == {}


# ── B.4 process_is_ours tests ────────────────────────────────────────────


def test_process_is_ours_match() -> None:
    """Processo nome=ollama do current user → True."""
    current_user_mock = MagicMock()
    current_user_mock.username.return_value = "testuser"

    target_proc_mock = MagicMock()
    target_proc_mock.name.return_value = "ollama"
    target_proc_mock.username.return_value = "testuser"

    with patch("psutil.Process", side_effect=[target_proc_mock, current_user_mock]):
        result = process_is_ours(12345)

    assert result is True


def test_process_is_ours_pid_reuse_diff_name() -> None:
    """PID reusado por processo não-Ollama → False (EC-12 mitigation)."""
    current_user_mock = MagicMock()
    current_user_mock.username.return_value = "testuser"

    reused_proc_mock = MagicMock()
    reused_proc_mock.name.return_value = "firefox"  # PID foi reusado
    reused_proc_mock.username.return_value = "testuser"

    with patch("psutil.Process", side_effect=[reused_proc_mock, current_user_mock]):
        result = process_is_ours(12345)

    assert result is False


def test_process_is_ours_no_such_process() -> None:
    """PID não existe → False (não levanta)."""
    import psutil

    with patch("psutil.Process", side_effect=psutil.NoSuchProcess(99999)):
        result = process_is_ours(99999)

    assert result is False


# ── AC-10 pre_check_disk_space tests ─────────────────────────────────────


def test_pre_check_disk_space_sufficient(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Disco com espaço suficiente → no raise."""
    monkeypatch.setattr("bloco_interface.ollama_manager.DATA_DIR", tmp_path)

    fake_usage = MagicMock()
    fake_usage.free = 10 * 1024**3  # 10GB livres
    with patch("shutil.disk_usage", return_value=fake_usage):
        pre_check_disk_space(min_gb=7.0)  # não raise


def test_pre_check_disk_space_insufficient(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Disco com espaço insuficiente → raise DiskSpaceInsufficient."""
    monkeypatch.setattr("bloco_interface.ollama_manager.DATA_DIR", tmp_path)

    fake_usage = MagicMock()
    fake_usage.free = 1 * 1024**3  # 1GB apenas
    with patch("shutil.disk_usage", return_value=fake_usage):
        with pytest.raises(DiskSpaceInsufficient) as exc_info:
            pre_check_disk_space(min_gb=7.0)

    assert "1.00GB" in str(exc_info.value)
    assert "7.00GB" in str(exc_info.value)
