---
type: adr
id: "ADR-029"
title: "Backup Strategy — APScheduler Embedded + Visibility + Retention 30d"
status: accepted
date: "2026-05-16"
domain: "infra"
decision_makers: ["@architect (Aria)", "@devops (Operator)"]
supersedes: ""
superseded_by: ""
adr_level: spec
spec_coverage:
  - "APScheduler embedded jobs (backup_daily + backup_rotation)"
  - "Backup contents + location + permissions"
  - "Retention 30 days (Sprint 8 escalation from 7d)"
  - "Monitoring Prometheus metric backup_last_success_timestamp"
  - "Restore procedure (cross-reference runbook)"
  - "Encryption recommendation deferred Sprint 9+"
related:
  - "ADR-013 §2.4 (original APScheduler decision MVP-LEAN-01 Task 8)"
  - "Smith ultrathink F-CRIT-06 + F-HIGH-08 + F-HIGH-09"
  - "governance/runbook-backup-restore.md (operational procedure)"
tags:
  - project/revisor-contratual
  - adr
  - sprint-8
  - backup-strategy
  - lgpd-compliance
---

# ADR-029 — Backup Strategy: APScheduler Embedded + Visibility + Retention 30d

## Status

**Accepted** — 2026-05-16 (documents existing architecture + 3 enhancements)

## Context

Smith ultrathink (D-SMITH-S07-005) flagged **F-CRIT-06 backup automation INVISIBLE**:

```text
crontab -l grep backup        = empty (no host cron)
systemctl list-timers backup  = apenas dpkg-db-backup.timer (OS deps, NÃO revisor)
Backups DO exist em backups/2026-05-15 + 16 MAS WHERE process originating?
```

**Investigação empírica (D-ARIA-S08-001 SSH probes):**

Backups são gerados por **APScheduler embedded** dentro do FastAPI app via `bloco_backup/scheduler.py` (ADR-013 §2.4 MVP-LEAN-01 Task 8). Smith's visibility gap era **legítimo**:

- Host `cron`/`systemctl` NÃO veem APScheduler (vive dentro processo Python container)
- `docker logs` mostra mensagens APScheduler MAS não há monitoring agregado
- Runbook restore NÃO existe — operador em incident "como restore?" = NÃO TEM RESPOSTA

**Smith findings adicionais relacionados:**

- **F-HIGH-08:** Backup retention 7 days (hardcoded `RETENTION_DAYS = 7`) insuficiente para DR (target 30 days minimum)
- **F-HIGH-09:** Backups NOT encrypted at rest (plaintext em `/home/revisor/.local/share/.../backups/`)

**Constraint:** Arquitetura APScheduler embedded **já está em produção** desde MVP-LEAN-01 (Sprint 02). Migração para cron host OR systemd timer = refactor desnecessário. Mantém APScheduler + adiciona visibility/runbook.

---

## Decision

**Manter APScheduler embedded (não migrar) + 3 enhancements:**

### 1. Visibility Enhancement (NEW)

- **Runbook explícito** documentando APScheduler architecture (cross-ref `runbook-backup-restore.md`)
- **Prometheus metric** `revisor_backup_last_success_timestamp` exposto via app endpoint OR script-scraper (Operator implementation Sprint 8 Story #7 deploy)
- **Alertmanager rule** `BackupStale` quando `time() - revisor_backup_last_success_timestamp > 25h` (1h grace além cron daily 02:00)
- **Health check inclusion** `/health` endpoint (futura Story #13 Phase B) expõe `backup_last_success_age_hours` field

### 2. Retention Escalation 7d → 30d (Smith F-HIGH-08)

- `RETENTION_DAYS` hardcoded 7 → variável `REVISOR_BACKUP_RETENTION_DAYS` env (default 30)
- Migration: Neo code change em `bloco_backup/scheduler.py` (small refactor)
- Backwards compatible: env unset → default 30d (no break existing deploys)

### 3. Encryption Decision (Smith F-HIGH-09 — Sprint 9+ scope)

**Decision: Backup encryption recomendada MAS NÃO obrigatória Sprint 8.**

**Rationale empirical:**

| Backup file | PII content | LGPD risk |
|-------------|-------------|-----------|
| `vault.db` | Jurisprudência STJ/STF (dados PÚBLICOS) | ZERO |
| `audit.jsonl` | `entry_hash`, `previous_entry_hash` (HMAC chain), `parser_used`, `error_msg`, `contract_hash` | LOW (no CPF, no nome, no valor financeiro) |

**Backups contêm ZERO dados pessoais** — encryption é "defense in depth" não LGPD §46 obrigatório.

**Sprint 9+ scope (separate ADR):** GPG file-level encryption OR LUKS volume mount, decidir conforme threat model evolution (e.g., offsite backup S3).

### 4. Offsite Backup Recommendation (Sprint 9+ scope)

- **Current:** Local backups apenas (`/home/revisor/.local/share/.../backups/`) → SINGLE POINT OF FAILURE se VPS comprometido
- **Sprint 9+:** rsync nightly → encrypted offsite (S3/B2/Backblaze) OR Hetzner Storage Box
- **Cost:** ~$1-3/month (S3 IA tier) OR free (Hetzner included em VPS plan)

---

## Spec Coverage

### Backup Mechanism

```python
# bloco_backup/scheduler.py — APScheduler BackgroundScheduler
# Jobs:
# 1. backup_daily: CronTrigger(hour=2, minute=0)  # daily 02:00 UTC
#    Copy: vault.db + audit.jsonl → backups/{YYYY-MM-DD}/
#    Permissions: dir 700, files 600 (revisor user)
# 2. backup_rotation: IntervalTrigger(hours=24)
#    Delete: backups/*/ com mtime > REVISOR_BACKUP_RETENTION_DAYS (default 30)
```

### Backup Contents

| File | Source | Format | Size estimate |
|------|--------|--------|---------------|
| `vault.db` | `~/.local/share/revisor-contratual/vault.db` | SQLite | ~3.5MB (10 jurisprudências bundled) |
| `audit.jsonl` | `~/.local/share/revisor-contratual/audit.jsonl` | JSONL | ~9KB/100 entries (grows linearly) |

### Backup Location

```text
/home/revisor/.local/share/revisor-contratual/backups/
├── 2026-05-15/
│   ├── vault.db
│   └── audit.jsonl
├── 2026-05-16/
│   ├── vault.db
│   └── audit.jsonl
└── ...
```

Container volume mount `revisor-data:/home/revisor/.local/share/revisor-contratual` preserva backups entre container recreates.

### Monitoring (Sprint 8 Story #7 deploy implementation)

**Prometheus metric:**

```text
# HELP revisor_backup_last_success_timestamp Unix timestamp of last successful backup_daily run
# TYPE revisor_backup_last_success_timestamp gauge
revisor_backup_last_success_timestamp 1715833200
```

**Implementation options (Operator decision):**

1. **Endpoint-based:** Add `/metrics` endpoint em FastAPI app (requires Neo code change Sprint 8 Phase B)
2. **Script-scraper:** Operator script (`scripts/backup_metric_exporter.sh`) reads `backups/*/` mtime + writes prometheus-textfile format → node_exporter collector
3. **Hybrid:** Backup_daily job appends to `/var/log/revisor-backup.log` + journald parser

**Alertmanager rule:**

```yaml
- alert: RevisorBackupStale
  expr: time() - revisor_backup_last_success_timestamp > 90000  # 25h (24h cron + 1h grace)
  for: 15m
  labels:
    severity: critical
    component: backup
  annotations:
    summary: "Revisor Contratual backup stale (>25h sem success)"
    runbook: "governance/runbook-backup-restore.md#backup-stale"
```

### Retention Policy

```python
# bloco_backup/scheduler.py — Sprint 8 Story #7 patch (Neo code change)
RETENTION_DAYS = int(os.environ.get("REVISOR_BACKUP_RETENTION_DAYS", "30"))
```

**Deploy:** Add `REVISOR_BACKUP_RETENTION_DAYS=30` em `docker-compose.prod.yml` app environment.

### Restore Procedure

Cross-reference: `governance/runbook-backup-restore.md` (step-by-step DR procedure)

**Summary:**

1. Stop app container: `sudo docker compose stop app`
2. Copy backup files from `backups/{DATE}/` → `~/.local/share/revisor-contratual/`
3. Verify HMAC chain integrity: `python -c "validate_audit_chain(...)"` (Sprint 9+ tool)
4. Restart container: `sudo docker compose up -d app`
5. Verify health: `curl GET /` → 200 OK + audit chain consistent

---

## Alternatives Considered

### Alternative A: Migrate to cron host

**Rejected.** Requires:
- Cross-platform script (bash + PowerShell duplicate)
- Container-host coupling (cron reads volume mount path)
- Permissions complexity (root cron + revisor user files)
- Loses APScheduler's logging integration

**Trade-off:** Cron host = visible MAS overhead refactor + duplicated code.

### Alternative B: Migrate to systemd timer

**Rejected.** Similar issues to cron host PLUS:
- systemd timer não cross-platform (Linux-only, no Docker Desktop/Windows dev)
- Requires `revisor-backup.service` + `revisor-backup.timer` unit files
- Requires `WorkingDirectory` + `User=revisor` + `EnvironmentFile=` setup

### Alternative C: Docker container internal cron

**Rejected.** Anti-pattern:
- Container should NÃO have cron daemon (separation of concerns)
- APScheduler embedded já resolve o problema cross-platform

### Alternative D: External backup service (rclone, restic)

**Considered for Sprint 9+ offsite.** Requires:
- Additional service (rclone) install em container OR host
- Encryption keys management
- Offsite credentials (S3/B2)

**Decision:** Sprint 9+ scope, separate ADR.

---

## Consequences

### Positive

- **Zero refactor:** APScheduler embedded já produção desde Sprint 02
- **Visibility added:** Runbook + Prometheus metric + Alertmanager rule = host ops tools agora veem backup state
- **Retention 30d:** Smith F-HIGH-08 RESOLVED
- **Cross-platform preserved:** Dev local Windows + production Linux mesma codebase
- **LGPD §46 audit chain preserved:** Backup integrity via HMAC chain validation (cross-ref ADR-014 audit chain)

### Negative

- **Single point of failure:** Local backups only. Se VPS comprometido (RCE), backups perdidos junto.
- **No encryption at rest:** Plaintext backups (mitigated by ZERO PII content; deferred Sprint 9+)
- **Container restart = backup paused:** APScheduler vive dentro container; if container down 24h+, backup_daily skipped
- **No backup-of-backup:** Se backup_rotation bug deleta wrong items, no recovery

### Neutral

- **Retention 30d means more disk usage:** ~4MB/day × 30 days = ~120MB total (negligible vs 27GB free)
- **Sprint 9+ offsite migration:** Decoupled, can be added without breaking ADR-029

---

## Operator Action Items (Sprint 8 Story #7 deploy)

| Action | Owner | Estimate |
|--------|-------|----------|
| Add `REVISOR_BACKUP_RETENTION_DAYS=30` em `docker-compose.prod.yml` app env | @devops | 5min |
| Neo code change `RETENTION_DAYS = int(os.environ.get(...))` em `bloco_backup/scheduler.py` | @dev (Sprint 8 sub-action) | 10min |
| Image rebuild + container recreate | @devops | 5-10min |
| Verify post-recreate: `docker logs app \| grep RETENTION_DAYS` | @devops | 2min |
| Implement Prometheus exporter (script-scraper option 2 recommended) | @devops | 1-2h |
| Configure Alertmanager rule `RevisorBackupStale` | @devops | 30min |
| Test restore procedure empirically (runbook walkthrough) | @devops + @qa | 1h |

**Total Operator estimate:** ~3-4h cumulative

---

## Sprint 9+ Future Work (Separate ADRs)

| Topic | ADR # | Rationale |
|-------|-------|-----------|
| Offsite backup (S3/B2/Hetzner Storage Box) | ADR-030 (future) | Mitigate single point of failure |
| Backup encryption GPG/LUKS | ADR-031 (future) | Defense in depth quando PII content adicionado (futuro feature) |
| Backup integrity validation tool | ADR-032 (future) | Validate HMAC chain consistency em backup |

---

## Cross-References

- **Original ADR-013 §2.4:** APScheduler embedded decision (MVP-LEAN-01 Task 8)
- **Smith ultrathink F-CRIT-06 + F-HIGH-08 + F-HIGH-09:** `governance/qa/smith-ultrathink-aplicacao-completa-hardware-2026-05-16.md`
- **Runbook:** `governance/runbook-backup-restore.md` (operational procedure)
- **Sprint 8 scope v2.0:** `governance/sprints/sprint-8-scope.md` Story #7

---

*ADR-029 published by @architect (Aria) 2026-05-16 — Sprint 8 Phase A Story #7. Documents existing APScheduler architecture + 3 enhancements (visibility + retention + encryption deferred). Resolves Smith F-CRIT-06 (visibility) + F-HIGH-08 (retention 30d). F-HIGH-09 (encryption) deferred Sprint 9+ ADR-031 com rationale (ZERO PII content).*
