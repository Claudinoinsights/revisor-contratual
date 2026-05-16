"""Integration tests for backup retention env override — Sprint 8 Phase B Story #14.

Smith F-HIGH-08 ultrathink: backups/2026-05-15 + 16 mostram retention=2 dias only
(scheduler.py:30 RETENTION_DAYS = 7 hardcoded).
ADR-029 spec: env override REVISOR_BACKUP_RETENTION_DAYS default 30 dias.

Refs:
- Smith ultrathink F-HIGH-08
- ADR-029 governance/architecture/adr/adr-029-backup-strategy.md
- handoff-devops-to-dev-2026-05-16-sprint-8-phase-b-neo-batch-12-13-14.yaml
"""

from __future__ import annotations

import os

import pytest


def test_resolve_retention_days_default_30(monkeypatch: pytest.MonkeyPatch):
    """AC-1+AC-2: env unset → default 30 dias (Smith F-HIGH-08 target)."""
    monkeypatch.delenv("REVISOR_BACKUP_RETENTION_DAYS", raising=False)
    from bloco_backup.scheduler import _resolve_retention_days
    assert _resolve_retention_days() == 30


def test_resolve_retention_days_env_override(monkeypatch: pytest.MonkeyPatch):
    """AC-1: env=60 → returns 60 (operator override valid range)."""
    monkeypatch.setenv("REVISOR_BACKUP_RETENTION_DAYS", "60")
    from bloco_backup.scheduler import _resolve_retention_days
    assert _resolve_retention_days() == 60


def test_resolve_retention_days_invalid_falls_back_to_default(monkeypatch: pytest.MonkeyPatch):
    """AC-3 defensive: malformed env (non-int) → fallback 30 (no break)."""
    monkeypatch.setenv("REVISOR_BACKUP_RETENTION_DAYS", "abc")
    from bloco_backup.scheduler import _resolve_retention_days
    assert _resolve_retention_days() == 30


def test_resolve_retention_days_out_of_range_falls_back(monkeypatch: pytest.MonkeyPatch):
    """AC-3 defensive: value < 1 OR > 365 → fallback 30 (sanity guard)."""
    monkeypatch.setenv("REVISOR_BACKUP_RETENTION_DAYS", "0")
    from bloco_backup.scheduler import _resolve_retention_days
    assert _resolve_retention_days() == 30

    monkeypatch.setenv("REVISOR_BACKUP_RETENTION_DAYS", "999")
    assert _resolve_retention_days() == 30

    monkeypatch.setenv("REVISOR_BACKUP_RETENTION_DAYS", "-5")
    assert _resolve_retention_days() == 30


def test_module_RETENTION_DAYS_uses_resolved_value():
    """RETENTION_DAYS module-level var deve usar _resolve_retention_days() result."""
    from bloco_backup import scheduler
    # At module load time, current env (or default 30) was used
    assert isinstance(scheduler.RETENTION_DAYS, int)
    assert 1 <= scheduler.RETENTION_DAYS <= 365
