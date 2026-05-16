---
type: runbook
title: "Runbook — Backup & Restore Procedure"
project: revisor-contratual
last_updated: "2026-05-16"
owner: "@devops (Operator)"
audience: "Operator (incident response) + Eric (executive overview)"
related:
  - "ADR-029 governance/architecture/adr/adr-029-backup-strategy.md"
  - "ADR-031 governance/architecture/adr/adr-031-backup-encryption.md (Sprint 8 Phase B Story #11 — restic encryption layer)"
  - "ADR-013 §2.4 (original APScheduler decision)"
tags:
  - project/revisor-contratual
  - runbook
  - disaster-recovery
  - backup
  - sprint-8
  - encryption
  - lgpd-compliance
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

## 🔐 Encrypted Backup Layer (ADR-031 — Sprint 8 Phase B Story #11)

> **Sprint 8 Phase B addition:** Sobre o backup mecânico legacy (cp-based), uma camada de **encryption at-rest** foi adicionada via **restic** (AES-256-CTR + Poly1305 MAC + scrypt KDF). Resolve Smith F-HIGH-09 e implementa LGPD §46/§11 defense-in-depth.

### Co-existence Architecture (D+0 → D+30 Migration Window)

Durante 30-day transition (deploy D-OPS-S08-005 em 2026-05-16):

| Job | Schedule | Type | Status |
|-----|----------|------|--------|
| `backup_daily` | 02:00 UTC daily | Legacy cp-based (plaintext) | Active during transition |
| `backup_rotation` | 24h interval | Legacy rotation | Active during transition |
| `backup_daily_encrypted` | **02:05 UTC daily** (+5min I/O offset) | **NEW restic AES-256-CTR** | Active primary |
| `cleanup_old_snapshots_encrypted` | 24h interval | NEW restic forget+prune | Active primary |

**Após D+30 (cerca de 2026-06-15):** Operator follow-up deploy removerá legacy jobs (`backup_daily` + `backup_rotation`) — restic vira única source of truth.

### Cryptographic Guarantees

| Property | Algorithm | Bits |
|----------|-----------|------|
| Symmetric encryption | AES-256-CTR | 256 |
| Authenticated encryption (MAC) | Poly1305 | 128 (one-time auth) |
| Key derivation | scrypt | N=2^17, r=8, p=1 (~1s CPU) |
| Content hashing | SHA-256 (dedup) | 256 |
| Per-snapshot encryption | Yes (master key derivation per repo password) | — |

**Audited externally:** Filippo Valsorda (Apple/Cloudflare cryptography reviewer) — 2018 audit.

### Verify Encrypted Backup State

```bash
# Container interactive
docker exec -it revisor-prod-app sh

# Dentro container — list snapshots
restic -r $RESTIC_REPOSITORY -p $RESTIC_PASSWORD_FILE snapshots

# Esperado:
# ID        Time                 Host          Tags          Paths
# --------------------------------------------------------------------
# a9e45e53  2026-05-16 14:58:55  revisor-prod  manual-smoke  /home/revisor/.local/share/.../audit.jsonl
#                                                            /home/revisor/.local/share/.../vault.db
```

### Verify Cryptographic Opacity (anti-leak proof)

```bash
# Plaintext vault.db (legacy backup OR active runtime) shows SQLite magic bytes
docker exec revisor-prod-app head -c 16 /home/revisor/.local/share/revisor-contratual/vault.db | od -c | head -2
# Expected: SQLite format 3\0

# Encrypted restic pack file shows OPAQUE BINARY (zero plaintext signature)
docker exec revisor-prod-app sh -c 'find /home/revisor/.local/share/revisor-contratual/restic-repo/data -type f | head -1 | xargs head -c 16 | od -c | head -2'
# Expected: opaque bytes like '033 v 023 223 214 375...'  (NOT SQLite, NOT readable)
```

### Verify Integrity (weekly health check recommended)

```bash
docker exec revisor-prod-app restic -r $RESTIC_REPOSITORY -p $RESTIC_PASSWORD_FILE check --read-data-subset 5%

# Expected: "no errors were found"
# Sprint 9+ TD: Automate as cron weekly + alert on errors
```

### Storage Architecture

```text
/home/revisor/.local/share/revisor-contratual/
├── vault.db                      (plaintext active DB — runtime)
├── audit.jsonl                   (plaintext active audit — runtime)
├── restic-repo/                  (encrypted backup repository)
│   ├── config                    (encrypted repo metadata, 155 bytes)
│   ├── keys/{key-id}             (encrypted master keys — scrypt KDF)
│   ├── snapshots/{snapshot-id}   (encrypted snapshot manifests)
│   ├── data/{prefix}/{pack-id}   (encrypted content-addressable packs ~MiB each)
│   ├── index/{index-id}          (pack index for fast restore)
│   └── locks/                    (active operation locks)
└── backups/                      (LEGACY plaintext — 30d transition only)
    └── YYYY-MM-DD/
```

```text
/etc/restic/
└── password.txt    (mode 0400, owner uid=1000 deploy↔revisor, contents: 32-byte base64)
```

### Password Rotation Procedure

**Annual baseline OR post-incident (suspected breach, personnel change):**

```bash
# 1. Generate new password
sudo sh -c 'openssl rand -base64 32 > /etc/restic/password.txt.new'
sudo chmod 400 /etc/restic/password.txt.new
sudo chown 1000:1000 /etc/restic/password.txt.new

# 2. Add new key to repo (restic supports multiple keys)
sudo docker exec revisor-prod-app \
  restic -r /home/revisor/.local/share/revisor-contratual/restic-repo \
         -p /etc/restic/password.txt \
         key add --new-password-file /etc/restic/password.txt.new

# 3. Verify new key works
sudo docker exec revisor-prod-app \
  restic -r /home/revisor/.local/share/revisor-contratual/restic-repo \
         -p /etc/restic/password.txt.new \
         snapshots

# 4. Remove old key (LIST first to get ID)
sudo docker exec revisor-prod-app \
  restic -r /home/revisor/.local/share/revisor-contratual/restic-repo \
         -p /etc/restic/password.txt.new \
         key list
# Then remove the old key ID:
sudo docker exec revisor-prod-app \
  restic -r /home/revisor/.local/share/revisor-contratual/restic-repo \
         -p /etc/restic/password.txt.new \
         key remove <old-key-id>

# 5. Atomic swap on host
sudo mv /etc/restic/password.txt.new /etc/restic/password.txt

# 6. Update key escrow USB (Eric — physical action) — see Key Escrow section

# 7. Document rotation em governance/CHECKPOINT-active.md com data
```

### 🔑 Key Escrow Procedure (Eric — Manual Physical Action)

**Critical:** Loss of `/etc/restic/password.txt` = LOSS of ALL encrypted backups irreversibly. Key escrow é mandatory para LGPD §46 defensibility + business continuity.

**Procedimento Eric retrieval:**

```bash
# 1. Eric SSH retrieval
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149

# 2. Read password (sudo required - file root-permissioned)
sudo cat /etc/restic/password.txt
# OR copy to temp staging:
sudo cp /etc/restic/password.txt /tmp/restic-pw-YYYY-MM-DD.txt

# 3. scp para máquina Eric (Windows local)
scp eric@91.108.126.149:/tmp/restic-pw-YYYY-MM-DD.txt ~/

# 4. Encrypt USB com BitLocker (Windows native) OU VeraCrypt
#    - Create encrypted USB volume
#    - Copy password file dentro
#    - Note physical location

# 5. Cleanup staging (CRITICAL — não deixar temp file)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 "sudo shred -u /tmp/restic-pw-YYYY-MM-DD.txt"

# 6. Document em PASSWORD-RECOVERY-PLAN.md (LOCAL ONLY — NÃO commit git):
#    - USB physical location
#    - Decryption procedure (BitLocker/VeraCrypt steps)
#    - Last rotation date
#    - Recovery contact (Eric primary)
```

**Recovery workflow se VPS unrecoverable:**

```bash
# Eric retrieve USB → decrypt → cat password.txt → on new VPS:
sudo mkdir -p /etc/restic
sudo sh -c 'echo "<password>" > /etc/restic/password.txt'
sudo chmod 400 /etc/restic/password.txt
sudo chown 1000:1000 /etc/restic/password.txt
# Then restore restic-repo via offsite backup (Sprint 9+ ADR-030)
```

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

### Scenario E: Restore from Encrypted Backup (ADR-031 restic)

**When to use:**

- Legacy plaintext backup ausente OR corrupted (D+30 transition cleanup completed)
- Encrypted snapshot é primary recovery source (Sprint 8 Phase C+ post-transition)
- Granular restore needed (specific snapshot by ID)

**Severity:** Variable (depends on incident scope)

**Pre-requirement:** `/etc/restic/password.txt` available em VPS OR Eric key escrow USB recovered.

**Steps:**

```bash
# 1. SSH to VPS
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149

# 2. List available snapshots — identify target
sudo docker exec revisor-prod-app \
  restic -r /home/revisor/.local/share/revisor-contratual/restic-repo \
         -p /etc/restic/password.txt \
         snapshots

# Output:
# ID        Time                 Host          Tags     Paths
# --------------------------------------------------------------
# a9e45e53  2026-05-16 14:58:55  revisor-prod  daily    /home/revisor/.local/share/.../vault.db
#                                                       /home/revisor/.local/share/.../audit.jsonl
# b3f72c91  2026-05-17 02:05:12  revisor-prod  daily    /home/revisor/.local/share/.../vault.db
#                                                       /home/revisor/.local/share/.../audit.jsonl
# ...

# 3. Stop app container (preserve running ollama-shared per ADR-026)
sudo docker compose -p revisor-prod -f docker-compose.prod.yml stop app

# 4. Restore specific snapshot to /tmp staging (NÃO direto live location)
sudo docker run --rm \
  -v revisor-prod_revisor-data:/data \
  -v /etc/restic:/etc/restic:ro \
  -e RESTIC_PASSWORD_FILE=/etc/restic/password.txt \
  revisor-contratual:prod \
  restic -r /data/restic-repo restore <SNAPSHOT_ID> --target /tmp/restore

# Note: --target /tmp/restore creates /tmp/restore/home/revisor/.local/share/revisor-contratual/{vault.db, audit.jsonl}
# (restic preserves full path structure)

# 5. Inspect restored files (sanity check sizes + magic bytes)
sudo docker run --rm \
  -v revisor-prod_revisor-data:/data \
  alpine sh -c 'ls -la /tmp/restore/home/revisor/.local/share/revisor-contratual/ && head -c 16 /tmp/restore/home/revisor/.local/share/revisor-contratual/vault.db | od -c | head -1'
# Expected: SQLite format 3\0 (plaintext restored from encrypted backup)

# 6. Copy restored files → live location (replacing corrupted/lost)
sudo docker run --rm \
  -v revisor-prod_revisor-data:/data \
  alpine sh -c 'cp /tmp/restore/home/revisor/.local/share/revisor-contratual/vault.db /data/vault.db && cp /tmp/restore/home/revisor/.local/share/revisor-contratual/audit.jsonl /data/audit.jsonl && chown 1000:1000 /data/vault.db /data/audit.jsonl && chmod 600 /data/vault.db /data/audit.jsonl'

# 7. Restart app container
sudo docker compose -p revisor-prod -f docker-compose.prod.yml up -d app

# 8. Verify pipeline + health
curl https://revisor.claudinoinsights.com/health
# Esperado: {"status":"ok","version":"0.2.10.0",...}

# 9. Verify audit chain integrity (HMAC chain — ADR-014)
sudo docker exec revisor-prod-app python -c "
from bloco_audit.chain import validate_audit_chain
result = validate_audit_chain()
print('Chain valid:', result.valid, '| Entries:', result.entry_count)
"
# Esperado: Chain valid: True | Entries: <N>
```

**Restore latest snapshot (shortcut):**

```bash
# Substitute step 4 com:
sudo docker exec revisor-prod-app \
  restic -r /home/revisor/.local/share/revisor-contratual/restic-repo \
         -p /etc/restic/password.txt \
         restore latest --target /tmp/restore
```

**Partial restore (single file):**

```bash
# Restore only vault.db (skip audit.jsonl)
sudo docker exec revisor-prod-app \
  restic -r /home/revisor/.local/share/revisor-contratual/restic-repo \
         -p /etc/restic/password.txt \
         restore <SNAPSHOT_ID> --target /tmp/restore \
         --include /home/revisor/.local/share/revisor-contratual/vault.db
```

**Verify post-restore:**

- ✅ `/health` returns 200 com version + ollama configured
- ✅ Audit chain HMAC integrity preserved (ADR-014)
- ✅ Vault DB queryable: `docker exec app python -c 'from bloco_vault.repo import VaultRepo; print(VaultRepo().count_documents())'`
- ✅ APScheduler jobs still 4 registered (post-restart)

---

## 🔧 Monitoring & Alerts

### ⚡ Sprint 8 Story #7 Deployed: journald + Loki (node_exporter ausente VPS)

**Deployed approach (Sprint 8 D-OPS-S08-002):**

- **Script:** `/usr/local/bin/revisor-backup-check.sh` (chmod 755, root:root)
- **Cron:** `/etc/cron.d/revisor-backup-monitor` → `*/15 * * * * root /usr/local/bin/revisor-backup-check.sh`
- **Output:** journald via `logger -t revisor-backup-check` (auto-collected by Alloy → Loki)
- **Log levels:** INFO (backup_ok) | WARN (backup_incomplete) | ERROR (backup_stale)

**Loki query for alerting (manual setup Sprint 9+ TD):**

```logql
{tag="revisor-backup-check"} |~ "ERROR backup_stale"
```

**Grafana alert configuration (Sprint 9+ TD):**

- Datasource: Loki
- Query: above LogQL
- Condition: count > 0 over last 1h
- Notification: email via Alertmanager smtp config

**Verify deployment:**

```bash
ssh eric@91.108.126.149 "
sudo journalctl -t revisor-backup-check --since '1 hour ago' --no-pager | head -5
sudo cat /etc/cron.d/revisor-backup-monitor
sudo /usr/local/bin/revisor-backup-check.sh; echo exit=\$?
"
```

---

### Sprint 9+ TD: Prometheus Metric Setup (Option A original, deferred)

**TD-S8P7-MED-03:** Prometheus textfile-collector integration deferred — VPS NÃO tem node_exporter installed (apenas prometheus + postgres-exporter containers). Sprint 9+ install node_exporter container com `--collector.textfile.directory` + migrate `revisor-backup-check.sh` to write `.prom` format.

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
