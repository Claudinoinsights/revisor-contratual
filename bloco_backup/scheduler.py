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
RETENTION_DAYS = 7


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
    # Job 1: backup_daily 02:00 UTC
    scheduler.add_job(
        backup_daily,
        trigger=CronTrigger(hour=2, minute=0),
        id="backup_daily",
        name="Daily backup vault + audit",
        replace_existing=True,
    )
    # Job 2: backup_rotation a cada 24h (start em 1min após startup)
    scheduler.add_job(
        backup_rotation,
        trigger=IntervalTrigger(days=1),
        id="backup_rotation",
        name="Rotation backups >7 dias",
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
