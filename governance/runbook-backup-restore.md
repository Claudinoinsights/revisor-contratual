---
type: runbook
title: "Runbook — Backup & Restore Procedure"
project: revisor-contratual
last_updated: "2026-05-16"
owner: "@devops (Operator)"
audience: "Operator (incident response) + Eric (executive overview)"
related:
  - "ADR-029 governance/architecture/adr/adr-029-backup-strategy.md"
  - "ADR-013 §2.4 (original APScheduler decision)"
tags:
  - project/revisor-contratual
  - runbook
  - disaster-recovery
  - backup
  - sprint-8
---

# Runbook — Backup & Restore Procedure

> **Quick reference para incident response.** Use Ctrl+F para localizar cenários específicos.

## 🎯 Overview (TL;DR)

| Aspecto | Detalhe |
|---------|---------|
| **Mechanism** | APScheduler embedded em FastAPI app (cross-platform) |
| **Implementation** | `bloco_backup/scheduler.py` (ADR-013 §2.4 + ADR-029) |
| **Schedule** | Daily 02:00 UTC (cron) + rotation 24h interval |
| **Contents** | `vault.db` + `audit.jsonl` (ZERO PII — jurisprudência + HMAC hashes) |
| **Location** | `~/.local/share/revisor-contratual/backups/{YYYY-MM-DD}/` (container volume `revisor-data`) |
| **Retention** | 30 days (env `REVISOR_BACKUP_RETENTION_DAYS=30` — Sprint 8 Story #7) |
| **Encryption** | None (plaintext — deferred Sprint 9+ ADR-031, mitigated by ZERO PII) |
| **Monitoring** | Prometheus `revisor_backup_last_success_timestamp` + Alertmanager `RevisorBackupStale` (>25h) |

## 🚀 Quick Reference Commands

### Verify backup state (operacional check)

```bash
# Latest backup date
ssh eric@91.108.126.149 "sudo docker exec revisor-prod-app ls -la /home/revisor/.local/share/revisor-contratual/backups/ | tail -5"

# Verify files in latest backup
ssh eric@91.108.126.149 "sudo docker exec revisor-prod-app ls -la /home/revisor/.local/share/revisor-contratual/backups/\$(date +%Y-%m-%d)/"

# Verify APScheduler running (look for backup_daily/rotation jobs)
ssh eric@91.108.126.149 "sudo docker logs revisor-prod-app 2>&1 | grep -E 'APScheduler|backup_daily|backup_rotation' | tail -10"
```

### Verify backup age

```bash
ssh eric@91.108.126.149 "sudo docker exec revisor-prod-app find /home/revisor/.local/share/revisor-contratual/backups/ -maxdepth 1 -type d -printf '%TY-%Tm-%Td %p\n' | sort -r | head -3"
```

---

## 📋 Backup Mechanism Details

### APScheduler Embedded (não visible to host cron/systemctl)

**IMPORTANT:** Backups são gerados por **APScheduler embedded** dentro do FastAPI app. Host `crontab -l` + `systemctl list-timers` NÃO mostram esses jobs — é por design.

**Source code:** [bloco_backup/scheduler.py](../bloco_backup/scheduler.py)

**Lifespan integration:** [bloco_interface/web/app.py:362-369](../bloco_interface/web/app.py#L362) — scheduler iniciado em FastAPI startup, shutdown wait=True em shutdown.

**Jobs:**

| Job | Trigger | Function | Purpose |
|-----|---------|----------|---------|
| `backup_daily` | CronTrigger(hour=2, minute=0) | `backup_daily()` | Copy vault.db + audit.jsonl → backups/{date}/ |
| `backup_rotation` | IntervalTrigger(hours=24) | `backup_rotation()` | Delete backups/*/ com mtime > RETENTION_DAYS |

### Permissions

```text
backups/                 drwx------ revisor:revisor  (700)
backups/{YYYY-MM-DD}/    drwx------ revisor:revisor  (700)
backups/{YYYY-MM-DD}/*   -rw------- revisor:revisor  (600)
```

Apenas `revisor` user dentro container pode ler. Volume mount preserva permissions em host.

---

## 🆘 Restore Procedure (Step-by-Step DR)

### Scenario A: Audit chain corruption (HMAC integrity broken)

**Symptoms:** `validate_audit_chain.py` reports broken `previous_entry_hash` link OR app crashes appending audit entry.

**Severity:** HIGH (LGPD §46 compliance risk)

**Steps:**

1. **Identify break point:** `sudo docker exec revisor-prod-app python -c "import json; entries=[json.loads(l) for l in open('/home/revisor/.local/share/revisor-contratual/audit.jsonl')]; [print(i, entries[i].get('entry_hash')[:16]) for i in range(len(entries)) if i > 0 and entries[i-1].get('entry_hash') != entries[i].get('previous_entry_hash')]"`

2. **Stop app container (preserve ollama-shared):**
   ```bash
   ssh eric@91.108.126.149 "cd /opt/revisor-contratual && sudo docker compose -p revisor-prod stop app"
   ```

3. **Identify latest valid backup:**
   ```bash
   ssh eric@91.108.126.149 "sudo docker exec revisor-prod-app ls -la /home/revisor/.local/share/revisor-contratual/backups/ | tail -10"
   ```

4. **Mount volume directly em host (container down):**
   ```bash
   ssh eric@91.108.126.149 "sudo docker volume inspect revisor-prod_revisor-data --format '{{.Mountpoint}}'"
   # Output: /var/lib/docker/volumes/revisor-prod_revisor-data/_data
   ```

5. **Backup current corrupted audit.jsonl (forensics):**
   ```bash
   ssh eric@91.108.126.149 "sudo cp /var/lib/docker/volumes/revisor-prod_revisor-data/_data/audit.jsonl /tmp/audit-corrupted-$(date +%Y%m%dT%H%M%S).jsonl"
   ```

6. **Restore audit.jsonl from latest valid backup:**
   ```bash
   ssh eric@91.108.126.149 "sudo cp /var/lib/docker/volumes/revisor-prod_revisor-data/_data/backups/{DATE}/audit.jsonl /var/lib/docker/volumes/revisor-prod_revisor-data/_data/audit.jsonl && sudo chown 1000:1000 /var/lib/docker/volumes/revisor-prod_revisor-data/_data/audit.jsonl && sudo chmod 600 /var/lib/docker/volumes/revisor-prod_revisor-data/_data/audit.jsonl"
   ```

7. **Verify HMAC chain integrity restored:**
   ```bash
   ssh eric@91.108.126.149 "cd /opt/revisor-contratual && sudo docker compose -p revisor-prod up -d app && sleep 30 && sudo docker exec revisor-prod-app python -c 'import json; entries=[json.loads(l) for l in open(\"/home/revisor/.local/share/revisor-contratual/audit.jsonl\")]; broken=0; [broken := broken + 1 for i in range(1, len(entries)) if entries[i-1].get(\"entry_hash\") != entries[i].get(\"previous_entry_hash\")]; print(\"CHAIN STATUS:\", \"INTACT\" if broken==0 else f\"BROKEN at {broken} points\")'"
   ```

8. **Verify health:**
   ```bash
   curl -o /dev/null -w 'STATUS=%{http_code}\n' https://revisor.claudinoinsights.com/
   # Expected: STATUS=200
   ```

9. **Document incident em CHECKPOINT** com: corrupted file path forensics + restored from backup date + new chain length.

### Scenario B: vault.db corruption

**Symptoms:** App fails parsing jurisprudência queries OR SQLite errors em logs.

**Severity:** MEDIUM (degrades pipeline mas not LGPD breach)

**Steps:**

1. Stop app container (Scenario A step 2)
2. Identify latest backup com vault.db válido
3. Copy backup → live location (Scenario A step 6 adapted)
4. Restart container
5. Verify pipeline functional: submit test PDF → expect audit entry com pipeline result

### Scenario C: VPS comprometido (RCE) — disaster recovery

**Symptoms:** Suspicious processes em VPS, exfiltration logs, unauthorized container restart.

**Severity:** CRITICAL (data breach risk)

**Steps:**

1. **Isolate VPS:** Disable network egress (Cloudflare proxy block)
2. **Forensics snapshot:** `sudo docker commit revisor-prod-app revisor-contratual:forensics-$(date +%Y%m%dT%H%M%S)`
3. **Identify damage:** Audit chain HMAC integrity check (Scenario A step 7)
4. **Provision new VPS:** Fresh OS install
5. **Restore from backup:** `scp` last valid `vault.db` + `audit.jsonl` → new VPS
6. **Re-deploy stack:** `git clone` + `docker compose up -d` (per CHANGELOG-v0.2.10.0.md)
7. **Verify DNS/Traefik:** Switch DNS to new VPS IP
8. **Document:** Incident report + lessons learned em CHECKPOINT

### Scenario D: Backup stale (RevisorBackupStale alert fired)

**Symptoms:** Alertmanager fired `RevisorBackupStale` (>25h sem success). Backup not happening.

**Severity:** MEDIUM (ongoing data loss risk)

**Diagnosis:**

```bash
# Verify APScheduler running
ssh eric@91.108.126.149 "sudo docker logs revisor-prod-app 2>&1 | grep -E 'APScheduler|backup_daily' | tail -20"

# Verify container time vs UTC
ssh eric@91.108.126.149 "sudo docker exec revisor-prod-app date -u"

# Verify backups directory writable
ssh eric@91.108.126.149 "sudo docker exec revisor-prod-app sh -c 'ls -la /home/revisor/.local/share/revisor-contratual/backups/ && touch /home/revisor/.local/share/revisor-contratual/backups/.write-test && rm /home/revisor/.local/share/revisor-contratual/backups/.write-test'"

# Force manual backup
ssh eric@91.108.126.149 "sudo docker exec revisor-prod-app python -c 'from bloco_backup.scheduler import backup_daily; print(backup_daily())'"
```

**Fixes:**

- Disk full? → cleanup logs + run `docker builder prune -af` (cross-ref Sprint 8 Story #0)
- APScheduler crashed? → restart app container: `sudo docker compose -p revisor-prod restart app`
- Permissions issue? → `sudo chown -R 1000:1000 /var/lib/docker/volumes/revisor-prod_revisor-data/_data/backups/`

---

## 🔧 Monitoring & Alerts

### Prometheus Metric Setup (Operator Sprint 8 Story #7 implementation)

**Option A — Endpoint-based (Sprint 8 Phase B, requires Neo code change):**

```python
# Future: bloco_interface/web/app.py
@app.get("/metrics")
def metrics() -> Response:
    backup_dir = Path("~/.local/share/revisor-contratual/backups/").expanduser()
    latest = max(backup_dir.iterdir(), key=lambda d: d.stat().st_mtime, default=None)
    ts = int(latest.stat().st_mtime) if latest else 0
    return Response(
        content=f"revisor_backup_last_success_timestamp {ts}\n",
        media_type="text/plain"
    )
```

**Option B — Script-scraper (Sprint 8 Story #7 RECOMMENDED, Operator-only):**

```bash
# /usr/local/bin/revisor-backup-exporter.sh
#!/bin/bash
# Append to /var/lib/node_exporter/textfile_collector/revisor_backup.prom
BACKUP_DIR="/var/lib/docker/volumes/revisor-prod_revisor-data/_data/backups"
LATEST=$(ls -t "$BACKUP_DIR" | head -1)
if [ -n "$LATEST" ]; then
    TS=$(stat -c %Y "$BACKUP_DIR/$LATEST")
    echo "revisor_backup_last_success_timestamp $TS" > /var/lib/node_exporter/textfile_collector/revisor_backup.prom
fi
```

Cron entry: `*/15 * * * * root /usr/local/bin/revisor-backup-exporter.sh`

### Alertmanager Rule

```yaml
groups:
  - name: revisor-backup
    rules:
      - alert: RevisorBackupStale
        expr: time() - revisor_backup_last_success_timestamp > 90000  # 25h
        for: 15m
        labels:
          severity: critical
          component: backup
          project: revisor-contratual
        annotations:
          summary: "Revisor Contratual backup stale (>25h sem success)"
          description: "Last successful backup: {{ $value | humanizeTimestamp }}. Runbook: governance/runbook-backup-restore.md#scenario-d-backup-stale"
```

---

## 🧪 Restore Procedure Testing (Empirical Validation)

**Frequency:** Trimestral (every 90 days)

**Procedure:**

1. Create test backup snapshot
2. Stop app + corrupt audit.jsonl deliberately (test fixture)
3. Execute Scenario A restore steps
4. Verify HMAC chain integrity restored
5. Document `runbook-validation-{date}.md` em `governance/qa/`

**Success criteria:** Restore < 15min, app healthy post-restore, audit chain INTACT.

---

## 📊 Sprint 8 Story #7 Implementation Checklist (Operator)

| Step | Action | Owner | Estimate |
|------|--------|-------|----------|
| 1 | Neo: `RETENTION_DAYS = int(os.environ.get("REVISOR_BACKUP_RETENTION_DAYS", "30"))` em `bloco_backup/scheduler.py` | @dev | 10min |
| 2 | Operator: Add `REVISOR_BACKUP_RETENTION_DAYS=30` em `docker-compose.prod.yml` app env | @devops | 5min |
| 3 | Operator: Image rebuild + container recreate | @devops | 5-10min |
| 4 | Operator: Verify post-recreate: `docker logs app \| grep RETENTION_DAYS` | @devops | 2min |
| 5 | Operator: Create `/usr/local/bin/revisor-backup-exporter.sh` script (Option B above) | @devops | 30min |
| 6 | Operator: Add cron entry `*/15 * * * * root /usr/local/bin/revisor-backup-exporter.sh` | @devops | 5min |
| 7 | Operator: Add Alertmanager rule `RevisorBackupStale` | @devops | 30min |
| 8 | Operator + QA: Test restore procedure (Scenario A walkthrough) | @devops + @qa | 1h |
| 9 | Operator: Add backup_validation entry em `runbook-validation-{date}.md` | @devops | 15min |

**Total estimate:** ~3h cumulative

---

## 🔗 Cross-References

- **ADR-029:** `governance/architecture/adr/adr-029-backup-strategy.md` (architectural decision)
- **ADR-013 §2.4:** Original APScheduler decision (MVP-LEAN-01 Task 8)
- **Smith ultrathink F-CRIT-06:** `governance/qa/smith-ultrathink-aplicacao-completa-hardware-2026-05-16.md`
- **Sprint 8 scope v2.0:** `governance/sprints/sprint-8-scope.md` Story #7
- **Source code:** `bloco_backup/scheduler.py` + `bloco_interface/web/app.py:362-369`

---

*Runbook published by @architect (Aria) 2026-05-16 — Sprint 8 Phase A Story #7. Documents existing APScheduler architecture + restore procedure DR. Resolves Smith F-CRIT-06 visibility gap.*
