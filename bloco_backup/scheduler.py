"""APScheduler embedded backup — MVP-LEAN-01 Task 8.

Per FR-BACKUP-MVP-01a/b + ADR-013 §2.4:
- backup_daily: cron 02:00 → copia vault.db + audit.jsonl para backups/{YYYY-MM-DD}/
- backup_rotation: interval 24h → deleta backups/*/ com mtime > 7 dias

Cross-platform via APScheduler BackgroundScheduler (non-blocking, daemon thread).
Lifespan FastAPI: scheduler.start() em startup, scheduler.shutdown(wait=True) em shutdown.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bloco_dataset.auto_trigger import run_camada_1_check

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "revisor-contratual"
DEFAULT_BACKUP_DIR = DEFAULT_DATA_DIR / "backups"

# ADR-031 Sprint 8 Phase B Story #11 — restic encryption (Smith F-HIGH-09)
# LGPD §46 (segurança técnica) + §11 (prevenção) defense-in-depth layer.
# Repository default lives in same data dir as legacy backups (volume mount preserved).
DEFAULT_RESTIC_REPO = DEFAULT_DATA_DIR / "restic-repo"
DEFAULT_RESTIC_PASSWORD_FILE = "/etc/restic/password.txt"


def _resolve_retention_days() -> int:
    """Sprint 8 Story #14 (Smith F-HIGH-08 + ADR-029): retention configurable via env.

    Smith ultrathink F-HIGH-08: backups retention 7 dias insuficiente para DR.
    ADR-029 spec: REVISOR_BACKUP_RETENTION_DAYS env override, default 30 dias.

    Defensive: env unset OR malformed (non-int) OR < 1 OR > 365 → default 30.
    """
    raw = os.environ.get("REVISOR_BACKUP_RETENTION_DAYS", "30")
    try:
        value = int(raw)
    except ValueError:
        logger.warning(
            "REVISOR_BACKUP_RETENTION_DAYS=%r invalid (not int) — using default 30", raw
        )
        return 30
    if value < 1 or value > 365:
        logger.warning(
            "REVISOR_BACKUP_RETENTION_DAYS=%d out of range [1,365] — using default 30", value
        )
        return 30
    return value


RETENTION_DAYS = _resolve_retention_days()


def _data_dir() -> Path:
    """Resolve data dir (env override REVISOR_DATA_DIR para testes)."""
    custom = os.environ.get("REVISOR_DATA_DIR")
    if custom:
        return Path(custom)
    return DEFAULT_DATA_DIR


def _backup_dir() -> Path:
    return _data_dir() / "backups"


def backup_daily() -> Path | None:
    """Job: copia vault.db + audit.jsonl para backups/{YYYY-MM-DD}/."""
    data_dir = _data_dir()
    backup_dir = _backup_dir()
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    target = backup_dir / today
    try:
        target.mkdir(parents=True, exist_ok=True)
        # chmod 700 em todo o backup tree (segurança)
        try:
            os.chmod(backup_dir, 0o700)
            os.chmod(target, 0o700)
        except OSError:
            pass

        copied: list[str] = []
        for fname in ("vault.db", "audit.jsonl"):
            src = data_dir / fname
            if src.exists():
                dst = target / fname
                shutil.copy2(src, dst)
                try:
                    os.chmod(dst, 0o600)
                except OSError:
                    pass
                copied.append(fname)
        logger.info("backup_daily: %s files copied to %s", copied, target)
    except OSError as exc:
        logger.error("backup_daily falhou: %s", exc)
        return None
    return target


def _restic_repo() -> str:
    """Resolve restic repository path (env override RESTIC_REPOSITORY)."""
    return os.environ.get("RESTIC_REPOSITORY", str(DEFAULT_RESTIC_REPO))


def _restic_password_file() -> str:
    """Resolve restic password file path (env override RESTIC_PASSWORD_FILE)."""
    return os.environ.get("RESTIC_PASSWORD_FILE", DEFAULT_RESTIC_PASSWORD_FILE)


def backup_daily_encrypted() -> None:
    """Job: encrypted backup via restic — ADR-031 Sprint 8 Phase B Story #11.

    Smith F-HIGH-09: backups plaintext readable em filesystem-level → defense-in-depth gap.
    ADR-031 §APScheduler Integration: restic AES-256-CTR + Poly1305 MAC + scrypt KDF.
    LGPD §46 (segurança técnica) + §11 (prevenção) compliance baseline.

    Preserves ADR-013 §2.4 APScheduler embedded architecture (subprocess invocation
    from BackgroundScheduler, NÃO migrate to host cron).

    Co-existence: roda em paralelo com legacy backup_daily() durante 30-day migration
    window (ADR-031 §Migration Plan D+0 → D+30). Operator removes legacy job em
    follow-up deploy após D+30.

    Targets: vault.db + audit.jsonl (mesmos arquivos legacy — content-addressable
    storage do restic deduplica conteúdo idêntico).
    """
    data_dir = _data_dir()
    repo = _restic_repo()
    pw_file = _restic_password_file()
    targets = [str(data_dir / "vault.db"), str(data_dir / "audit.jsonl")]
    # Filtra apenas arquivos existentes (restic não falha em missing mas log fica claro).
    existing_targets = [t for t in targets if Path(t).exists()]
    if not existing_targets:
        logger.warning("backup_daily_encrypted: nenhum target existe em %s, skip", data_dir)
        return

    cmd = [
        "restic",
        "-r", repo,
        "-p", pw_file,
        "backup",
        *existing_targets,
        "--tag", "daily",
        "--host", "revisor-prod",
    ]
    try:
        result = subprocess.run(  # noqa: S603 — fixed args, no user input
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        logger.error("backup_daily_encrypted: restic timeout (%ss)", exc.timeout)
        raise RuntimeError(f"backup_daily_encrypted timeout after {exc.timeout}s") from exc
    except FileNotFoundError as exc:
        # restic binary missing — Dockerfile install layer ausente OR host run sem restic
        logger.error("backup_daily_encrypted: restic binary not found (%s)", exc)
        raise RuntimeError("backup_daily_encrypted: restic binary missing — verify Dockerfile") from exc

    if result.returncode != 0:
        logger.error(
            "backup_daily_encrypted: restic backup failed (rc=%d) stderr=%s",
            result.returncode, result.stderr.strip(),
        )
        raise RuntimeError(f"backup_daily_encrypted failed (rc={result.returncode}): {result.stderr.strip()}")

    # Success — log last line of restic output (snapshot ID summary).
    last_line = result.stdout.strip().split("\n")[-1] if result.stdout else ""
    logger.info("backup_daily_encrypted: restic OK — %s", last_line)


def cleanup_old_snapshots_encrypted() -> int:
    """Job: restic forget + prune para retention via REVISOR_BACKUP_RETENTION_DAYS.

    Replaces ADR-029 cp-based rotation com restic native retention (snapshot-aware).
    Retorna count snapshots removidos (parsed from restic output OR 0 se parse fail).

    Story #14 integration: _resolve_retention_days() helper preserved — mesmo env var
    REVISOR_BACKUP_RETENTION_DAYS controla legacy rotation E encrypted rotation.

    --keep-within Nd: mantém snapshots dentro janela N dias, deleta restante.
    --prune: physically remove orphaned packs (recupera disk space).
    """
    repo = _restic_repo()
    pw_file = _restic_password_file()
    retention_days = _resolve_retention_days()

    cmd = [
        "restic",
        "-r", repo,
        "-p", pw_file,
        "forget",
        "--keep-within", f"{retention_days}d",
        "--prune",
    ]
    try:
        result = subprocess.run(  # noqa: S603 — fixed args, no user input
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        logger.error("cleanup_old_snapshots_encrypted: restic forget timeout (%ss)", exc.timeout)
        raise RuntimeError(f"cleanup_old_snapshots_encrypted timeout after {exc.timeout}s") from exc
    except FileNotFoundError as exc:
        logger.error("cleanup_old_snapshots_encrypted: restic binary not found (%s)", exc)
        raise RuntimeError("cleanup_old_snapshots_encrypted: restic binary missing") from exc

    if result.returncode != 0:
        logger.error(
            "cleanup_old_snapshots_encrypted: restic forget failed (rc=%d) stderr=%s",
            result.returncode, result.stderr.strip(),
        )
        raise RuntimeError(
            f"cleanup_old_snapshots_encrypted failed (rc={result.returncode}): {result.stderr.strip()}"
        )

    # Best-effort parse: restic forget output inclui "remove N snapshots".
    # Failure to parse → return 0 (not error — operation succeeded).
    deleted = 0
    for line in result.stdout.split("\n"):
        if "remove" in line.lower() and "snapshot" in line.lower():
            for token in line.split():
                if token.isdigit():
                    deleted = int(token)
                    break
            break
    logger.info(
        "cleanup_old_snapshots_encrypted: restic forget+prune OK (retention=%dd, ~%d removed)",
        retention_days, deleted,
    )
    return deleted


def backup_rotation() -> int:
    """Job: deleta backups/*/ com mtime > RETENTION_DAYS dias. Retorna count deletados."""
    backup_dir = _backup_dir()
    if not backup_dir.exists():
        return 0
    deleted = 0
    cutoff_seconds = time.time() - (RETENTION_DAYS * 24 * 60 * 60)
    for child in backup_dir.iterdir():
        if not child.is_dir():
            continue
        try:
            mtime = child.stat().st_mtime
            if mtime < cutoff_seconds:
                shutil.rmtree(child, ignore_errors=True)
                deleted += 1
        except OSError as exc:
            logger.warning("backup_rotation: erro processando %s: %s", child, exc)
    if deleted > 0:
        logger.info("backup_rotation: %d backups antigos deletados (>%dd)", deleted, RETENTION_DAYS)
    return deleted


def create_scheduler() -> BackgroundScheduler:
    """Cria BackgroundScheduler com jobs registrados (não-iniciado).

    Jobs sempre registrados:
    - backup_daily: 02:00 UTC (Task 8 PARTIAL)
    - backup_rotation: 24h interval (Task 8 PARTIAL)

    Jobs condicionais (env var):
    - tema_1378_check: 02:30 UTC (Task 8b Camada 1 STJ scraper) — só registrado
      se ENABLE_TEMA_1378_AUTO_CHECK=true (default false). Per Smith review
      CC.25 F-01: DEFAULT_STJ_URL é placeholder; ativar em prod só após Eric
      confirmar URL real STJ + tuning empírico patterns parser.

    Nota RR-04 (Smith CC.26): ENABLE_TEMA_1378_AUTO_CHECK é avaliado UMA VEZ na
    criação do scheduler (lifespan startup). Mudanças em runtime (toggle env var
    pós-startup) requerem reinicio do app — não é hot-reload por design (feature
    flag simples). Documentar em .env.example o formato exato esperado.

    Nota RR-03 (Smith CC.26): env parsing aceita "true", "1", "yes", "on", "enabled"
    (case-insensitive, com strip de whitespace). Outros valores → flag false.
    """
    scheduler = BackgroundScheduler(daemon=True, timezone="UTC")
    # Job 1 (LEGACY): backup_daily 02:00 UTC — co-existência 30-day migration window
    # ADR-031 §Migration Plan: legacy plaintext + restic encrypted co-existem D+0 → D+30,
    # após D+30 Operator remove via follow-up deploy.
    scheduler.add_job(
        backup_daily,
        trigger=CronTrigger(hour=2, minute=0),
        id="backup_daily",
        name="Daily backup vault + audit (legacy plaintext — 30d migration)",
        replace_existing=True,
    )
    # Job 2 (LEGACY): backup_rotation a cada 24h
    scheduler.add_job(
        backup_rotation,
        trigger=IntervalTrigger(days=1),
        id="backup_rotation",
        name=f"Rotation legacy backups >{RETENTION_DAYS}d",
        replace_existing=True,
    )
    # Job 3 (NEW ADR-031): backup_daily_encrypted 02:05 UTC — restic AES-256-CTR
    # Smith F-HIGH-09 RESOLVED. Offset +5min para evitar contenção I/O com legacy.
    scheduler.add_job(
        backup_daily_encrypted,
        trigger=CronTrigger(hour=2, minute=5),
        id="backup_daily_encrypted",
        name="Daily encrypted backup (restic ADR-031)",
        replace_existing=True,
    )
    # Job 4 (NEW ADR-031): cleanup_old_snapshots_encrypted a cada 24h (offset +1h legacy)
    scheduler.add_job(
        cleanup_old_snapshots_encrypted,
        trigger=IntervalTrigger(days=1),
        id="cleanup_old_snapshots_encrypted",
        name=f"Rotation encrypted snapshots >{RETENTION_DAYS}d (restic forget+prune)",
        replace_existing=True,
    )
    # Job 3 condicional: tema_1378_check 02:30 UTC (per Smith CC.25 F-01)
    # RR-03 fix (Smith CC.26): tolerar formatos comuns ("true"/"1"/"yes"/"on"/"enabled")
    enable_tema_check = (
        os.environ.get("ENABLE_TEMA_1378_AUTO_CHECK", "false")
        .strip()
        .lower()
        in {"true", "1", "yes", "on", "enabled"}
    )
    if enable_tema_check:
        scheduler.add_job(
            run_camada_1_check,
            trigger=CronTrigger(hour=2, minute=30),
            id="tema_1378_check",
            name="Tema 1378 STJ scraper Camada 1",
            replace_existing=True,
        )
        logger.info(
            "create_scheduler: tema_1378_check job registered "
            "(ENABLE_TEMA_1378_AUTO_CHECK=true)"
        )
    else:
        logger.info(
            "create_scheduler: tema_1378_check SKIPPED "
            "(ENABLE_TEMA_1378_AUTO_CHECK=false — set env var to enable in prod)"
        )
    return scheduler


def get_jobs_diagnostic() -> list[dict]:
    """Diagnostic-safe job introspection — Sprint 8 Phase B Smith F-S8PB-MV-MED-02.

    Smith mini-verify finding: `j.next_run_time` raises AttributeError when
    scheduler is NOT started (APScheduler API — computed only after start()).
    This degrades Operator post-deploy diagnostic capability — cannot easily
    verify scheduled job timing via simple Python query.

    This helper returns job metadata WITHOUT requiring scheduler.start(), using
    the trigger object's string representation for human-readable schedule.

    Use case: Operator post-deploy verification via:
        docker exec app python -c "from bloco_backup.scheduler import get_jobs_diagnostic; import json; print(json.dumps(get_jobs_diagnostic(), indent=2))"

    Preserves ADR-013 §2.4 APScheduler embedded architecture — no state change,
    pure read of trigger configuration.

    Returns:
        List of dicts com {id, name, trigger_str, trigger_type} para cada job
        registrado em create_scheduler() (legacy backup_daily + backup_rotation +
        new backup_daily_encrypted + cleanup_old_snapshots_encrypted = 4 jobs
        during co-existence window per ADR-031 §Migration Plan).
    """
    scheduler = create_scheduler()
    return [
        {
            "id": j.id,
            "name": j.name,
            "trigger_str": str(j.trigger),
            "trigger_type": type(j.trigger).__name__,
        }
        for j in scheduler.get_jobs()
    ]
