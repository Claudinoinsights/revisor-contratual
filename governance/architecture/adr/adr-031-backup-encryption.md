---
type: adr
id: "ADR-031"
title: "Backup Encryption — restic AES-256-CTR + Poly1305 MAC (Defense-in-Depth Layer over ADR-029)"
status: accepted
date: "2026-05-16"
domain: "infra"
decision_makers: ["@architect (Aria)", "@devops (Operator) deploy", "@dev (Neo) implementation"]
supersedes: ""
superseded_by: ""
adr_level: spec
spec_coverage:
  - "restic repository initialization (one-time Operator setup)"
  - "Encryption algorithm specification (AES-256-CTR + Poly1305 MAC + scrypt KDF)"
  - "Passphrase storage strategy (/etc/restic/password.txt root:0400)"
  - "APScheduler integration (subprocess invocation pattern)"
  - "Migration plan (legacy plaintext backups → restic repo, 30-day transition)"
  - "Key escrow procedure (Eric encrypted USB custody)"
  - "Passphrase rotation policy (annual OR post-incident)"
  - "Snapshot retention via restic forget --keep-within (replaces ADR-029 cp-based rotation)"
  - "Restore drill SOP (cross-reference runbook update)"
related:
  - "ADR-029 backup-strategy (this ADR supplements §3 Encryption Decision — promotes from 'deferred Sprint 9+' to 'implemented Sprint 8 Phase B')"
  - "ADR-013 §2.4 APScheduler embedded (preserved — restic invoked via subprocess from same APScheduler jobs)"
  - "ADR-014 audit chain HMAC (preserved — restic encrypts audit.jsonl preserving HMAC integrity inside encrypted snapshot)"
  - "Smith ultrathink F-HIGH-09 (governance/qa/smith-ultrathink-aplicacao-completa-hardware-2026-05-16.md linha 213-217)"
  - "Sprint 8 Phase B Story #11 (this ADR's implementation target — Neo handoff)"
  - "governance/runbook-backup-restore.md (operational procedure — requires update post-implementation)"
tags:
  - project/revisor-contratual
  - adr
  - sprint-8
  - phase-b
  - backup-encryption
  - lgpd-compliance
  - defense-in-depth
  - restic
---

# ADR-031 — Backup Encryption: restic AES-256-CTR + Poly1305 MAC

## Status

**Accepted** — 2026-05-16 (Sprint 8 Phase B Story #11 architectural decision, implementation pending Neo)

---

## Context

Smith ultrathink 2026-05-16 (F-HIGH-09) identificou:

> **F-HIGH-09 — Backups NOT Encrypted At Rest**
> **Empirical:** `backups/2026-05-16/audit.jsonl` + `vault.db` plaintext (`-rw------- revisor:revisor`).
> **Impact:** Filesystem-level backup readable. Compromise VPS access = compromise audit trail + jurisprudence vault. LGPD §46 audit data sensibility consideration.
> **Fix:** GPG encrypt backups OR LUKS volume mount for backup directory. Sprint 8 architectural decision.
>
> *(governance/qa/smith-ultrathink-aplicacao-completa-hardware-2026-05-16.md:213-217)*

### Relação com ADR-029 (cross-reference)

ADR-029 §3 (`accepted 2026-05-16`) decidiu **deferir** encryption Sprint 9+ com rationale:

> "Backups contêm ZERO dados pessoais — encryption é 'defense in depth' não LGPD §46 obrigatório."

**ADR-031 NÃO contradiz ADR-029.** ADR-029 permanece Accepted para strategy/visibility/retention. ADR-031 **promove o §3 Encryption Decision** de "deferred Sprint 9+" para "implemented Sprint 8 Phase B" por 4 razões emergentes durante Sprint 8 Phase B:

1. **Eric directive Sprint 8 scope v2.0 expansion:** 17 stories absorber 6 CRITICAL + 11 HIGH (Smith preference). F-HIGH-09 entrou no escopo Sprint 8 #11.
2. **Phase B parallel pattern (A3 hybrid):** Architect ADR-031 paralelo enquanto Operator deploya Neo batch (#12+#13+#14).
3. **Future-proofing:** Se PII content evoluir backups (e.g., sprint Sprint 9+ adds peças jurídicas generation com customer name), encryption baked NOW evita retrofit posterior.
4. **LGPD §46 best practice:** Mesmo sem obrigatoriedade strict (ZERO PII atual), §46 "medidas de segurança técnicas e administrativas" recomenda encryption-at-rest como baseline defensible. Auditoria LGPD futura aceita "encryption deployed" mais facilmente que "encryption deferred com rationale".

### Threat Model

Backup encryption protege contra **3 vetores específicos:**

| Vetor de ataque | Mitigação restic encryption |
|----------------|------------------------------|
| **VPS comprometido (RCE)** | Attacker obtém shell root → lê `/restic-repo/` mas conteúdo cifrado AES-256-CTR. Repositório opaque sem password. |
| **Sysadmin malicioso (insider)** | Sysadmin com acesso filesystem mas SEM password file (`/etc/restic/password.txt` chmod 400 root) não pode ler snapshots. Audit trail Operator access. |
| **Disk physical theft / disposal** | VPS provider Hetzner faz wipe oficial MAS encryption layer adicional protege contra negligence em disposal. |

### LGPD Compliance Anchors

**Lei 13.709/2018 (LGPD) artigos relevantes:**

- **§46 (Segurança técnica):** "Os agentes de tratamento devem adotar medidas de segurança, técnicas e administrativas aptas a proteger os dados pessoais de acessos não autorizados e de situações acidentais ou ilícitas de destruição, perda, alteração, comunicação ou qualquer forma de tratamento inadequado ou ilícito."
- **§11 (Tratamento on-premise):** "O tratamento de dados pessoais deve observar a boa-fé e os princípios de finalidade, adequação, necessidade, livre acesso, qualidade dos dados, transparência, segurança, prevenção, não discriminação, responsabilização e prestação de contas."

restic encryption supporta **§46 ("segurança técnica") + §11 ("prevenção")** como controles técnicos defensáveis em audit DPO/ANPD.

---

## Decision

**Adotar restic como mecanismo de backup encryption substituindo cp-based plaintext backup atual.**

### Especificação Cryptográfica

| Componente | Algoritmo |
|-----------|-----------|
| **Symmetric encryption** | AES-256-CTR |
| **Message authentication** | Poly1305 (HMAC-equivalent — fast streaming MAC) |
| **Key derivation function (KDF)** | scrypt (N=2^17, r=8, p=1 — restic default, ~1s on modern CPU) |
| **Per-snapshot encryption** | Yes — cada snapshot tem master key derivada via repository password |
| **Content addressable storage** | SHA-256 chunked content (dedup window 512KB-8MB) |
| **Audit trail** | Snapshot manifest assinado + per-chunk Poly1305 MAC |

**Audit by cryptography expert:** restic foi auditado por Filippo Valsorda (cryptography reviewer Apple/Cloudflare) em 2018. Source: https://restic.net/blog/2018-09-02/audit-completed/ (referência apenas — verificar antes implementation).

### Storage Architecture

```text
/home/revisor/.local/share/revisor-contratual/
├── vault.db                       (plaintext active DB — runtime)
├── audit.jsonl                    (plaintext active audit — runtime)
├── restic-repo/                   (NEW — encrypted backup repository)
│   ├── config                     (encrypted repo metadata)
│   ├── keys/{key-id}              (encrypted master keys)
│   ├── snapshots/{snapshot-id}    (encrypted snapshot manifests)
│   └── data/{prefix}/{pack-id}    (encrypted content-addressable packs)
└── backups/                       (LEGACY plaintext — 30-day transition, then DELETE)
    └── YYYY-MM-DD/
```

```text
/etc/restic/
└── password.txt    (mode 0400, owner root:root, contents: openssl rand -base64 32)
```

### APScheduler Integration

`bloco_backup/scheduler.py` substitui current cp-based backup com restic invocation via subprocess. Preserva APScheduler embedded (ADR-013 §2.4) — apenas troca payload do job.

```python
import subprocess
from pathlib import Path

RESTIC_REPO = os.environ.get(
    "RESTIC_REPOSITORY",
    "/home/revisor/.local/share/revisor-contratual/restic-repo"
)
RESTIC_PASSWORD_FILE = os.environ.get(
    "RESTIC_PASSWORD_FILE",
    "/etc/restic/password.txt"
)

def backup_daily_encrypted() -> None:
    """Sprint 8 Story #11 (ADR-031): encrypted backup via restic."""
    targets = [VAULT_DB_PATH, AUDIT_JSONL_PATH]
    cmd = [
        "restic", "-r", RESTIC_REPO, "-p", RESTIC_PASSWORD_FILE,
        "backup", *map(str, targets),
        "--tag", "daily",
        "--host", "revisor-prod",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        logger.error("restic backup failed: %s", result.stderr)
        raise RuntimeError(f"backup_daily_encrypted failed: {result.stderr}")
    logger.info("restic backup OK: %s", result.stdout.strip().split("\n")[-1])

def cleanup_old_snapshots_encrypted() -> None:
    """Replaces ADR-029 cp-based rotation — uses restic forget + prune."""
    retention_days = _resolve_retention_days()  # existing helper (Story #14)
    cmd = [
        "restic", "-r", RESTIC_REPO, "-p", RESTIC_PASSWORD_FILE,
        "forget",
        "--keep-within", f"{retention_days}d",
        "--prune",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        logger.error("restic forget+prune failed: %s", result.stderr)
        raise RuntimeError(f"cleanup_old_snapshots_encrypted failed: {result.stderr}")
    logger.info("restic forget+prune OK (retention=%dd)", retention_days)
```

### Dockerfile Changes

Adicionar restic install ao container:

```dockerfile
# ADR-031: restic for encrypted backups
RUN apt-get update && apt-get install -y --no-install-recommends \
    restic \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

Tamanho adicional image: ~25MB (restic binary + deps Go runtime).

### docker-compose.prod.yml Changes

```yaml
services:
  app:
    environment:
      # ... existing env ...
      RESTIC_REPOSITORY: "/home/revisor/.local/share/revisor-contratual/restic-repo"
      RESTIC_PASSWORD_FILE: "/etc/restic/password.txt"
    volumes:
      # ... existing volumes ...
      - /etc/restic:/etc/restic:ro    # read-only mount password file
```

### Passphrase Generation (Operator one-time)

```bash
sudo mkdir -p /etc/restic
sudo sh -c 'openssl rand -base64 32 > /etc/restic/password.txt'
sudo chmod 400 /etc/restic/password.txt
sudo chown root:root /etc/restic/password.txt
```

### Repository Initialization (Operator one-time)

```bash
sudo docker exec revisor-prod-app \
  restic -r /home/revisor/.local/share/revisor-contratual/restic-repo \
         -p /etc/restic/password.txt \
         init
# Output esperado:
#   created restic repository <repo-id> at <path>
#   Please note that knowledge of your password is required to access
#   the repository. Losing your password means that your data is irrecoverably lost.
```

### Key Escrow Procedure (LGPD §46 defensibility)

**Eric custody backup:**

1. Operator copia password file para encrypted USB:
   ```bash
   sudo cp /etc/restic/password.txt /tmp/restic-pw-2026-05-16.txt
   # Eric encrypts USB com BitLocker/VeraCrypt + stores fisicamente separado VPS
   sudo shred -u /tmp/restic-pw-2026-05-16.txt
   ```
2. Eric documenta em **PASSWORD-RECOVERY-PLAN.md** (local custody, NÃO commitado git):
   - USB location (physical)
   - Decryption procedure
   - Last rotation date
   - Recovery contact
3. **Audit trail:** Operator log em `governance/CHECKPOINT-active.md` data de generation + key escrow confirmation (sem expor password).

### Passphrase Rotation Policy

| Trigger | Rotation Required? |
|---------|--------------------|
| Annual baseline (every 12 months) | YES — best practice cryptographic hygiene |
| Operator personnel change | YES — within 30 days |
| VPS security incident (suspected breach) | YES — IMMEDIATE |
| Password file compromised filesystem (e.g., backup leak) | YES — IMMEDIATE |
| Major restic version upgrade (e.g., v0.x → v1.0) | OPTIONAL — verify upgrade notes |

**Rotation procedure (Operator):**

```bash
# 1. Generate new password
sudo sh -c 'openssl rand -base64 32 > /etc/restic/password.txt.new'
sudo chmod 400 /etc/restic/password.txt.new

# 2. Add new key to repo (restic supports multiple keys)
sudo docker exec revisor-prod-app \
  restic -r /restic-repo -p /etc/restic/password.txt \
         key add --new-password-file /etc/restic/password.txt.new

# 3. Verify new key works
sudo docker exec revisor-prod-app \
  restic -r /restic-repo -p /etc/restic/password.txt.new snapshots

# 4. Remove old key
sudo docker exec revisor-prod-app \
  restic -r /restic-repo -p /etc/restic/password.txt.new \
         key remove <old-key-id>

# 5. Atomic swap
sudo mv /etc/restic/password.txt.new /etc/restic/password.txt

# 6. Update key escrow USB (Eric)

# 7. Document rotation em governance/CHECKPOINT-active.md
```

### Migration Plan (30-day transition)

| Day | Action | Owner |
|-----|--------|-------|
| **D+0** | Story #11 deploy (restic install + APScheduler patches + init repo + first encrypted backup) | Neo + Operator |
| **D+0 → D+30** | Both backups co-exist: NEW `restic-repo/` encrypted + LEGACY `backups/YYYY-MM-DD/` plaintext | Operator monitoring |
| **D+30** | Verify ≥30 encrypted snapshots accumulated successfully | Operator |
| **D+31** | DELETE legacy `backups/YYYY-MM-DD/*` plaintext directories (irreversible) | Operator |
| **D+31+** | restic-repo único source of truth | — |

Migration transitional minimiza risk: se restic implementation tem bug, legacy plaintext backup ainda available D+0 to D+30.

---

## Alternatives Considered

### Alternative A: GPG `--symmetric --cipher-algo AES256` per-file

**Rejected.** Análise:

| Critério | Resultado |
|----------|-----------|
| Implementation effort | 3h (Neo bash subprocess + tarball+gpg pipe) |
| Ops overhead | **HIGH** — passphrase rotation = re-encrypt ALL historical backups OR maintain multi-version keys |
| LGPD §46 defensibility | Medium — per-file proof mas no audit trail unificado |
| RTO incremental | **POOR** — vault.db (3.5MB) full re-encrypt every night (wasteful, no dedup) |
| Future S3 scalability | **POOR** — `rsync GPG files → S3` é hand-rolled, sem dedup |
| Cross-platform dev | OK (gnupg disponível Windows/Linux/Mac) |
| Defense-in-depth | OK |

**Trade-off:** GPG é familiar mas designed para file-at-a-time encryption (email, signed releases), NÃO para backup workloads (incremental, dedup, retention). Usar GPG aqui = forçar martelo em parafuso.

### Alternative B: LUKS partition-level encryption

**Rejected.** Análise:

| Critério | Resultado |
|----------|-----------|
| Implementation effort | **HIGH** — 4-6h, intrusivo (requer VPS partition reformat OR new mount + data migration) |
| Ops overhead | Medium — keyfile-on-disk required (interactive unlock impossível em VPS sem console) |
| LGPD §46 defensibility | Medium — volume-level encryption, MAS keyfile-on-disk reduz defensibility |
| RTO transparent | **HIGH** — kernel-level transparent, near-zero overhead |
| Future S3 scalability | **IMPOSSIBLE** — LUKS volume é local block device, NÃO replicável para object storage |
| Cross-platform dev | **POOR** — Linux-only (Windows dev Docker Desktop sem LUKS) |
| Defense-in-depth | Good (whole-volume) |

**Trade-off bloqueador:** LUKS requires keyfile-on-disk para auto-mount em VPS reboot, mas se attacker tem root acesso VPS, attacker lê keyfile + monta LUKS volume = encryption defeated. LUKS protege contra **physical theft** (cenário negligível em datacenter Hetzner), NÃO contra **VPS RCE** (cenário real F-HIGH-09).

### Alternative C: restic AES-256-CTR + Poly1305 MAC ✅ SELECTED

(Especificação acima — Decision section)

### Alternative D: Borg (BorgBackup) — also encrypted backup tool

**Considered briefly.** Borg é alternativa válida (similar features: AES-256-CTR + dedup + incremental). Razões para preferir restic:

- restic tem multi-backend nativo (S3/B2/Azure/GCS) — Borg requer borg-storage-box ou rsync.net
- restic Go single-binary (sem dependências Python) — Borg requer Python install
- restic actively maintained 2026 — Borg maintenance velocity menor
- restic auditado externamente (Filippo Valsorda 2018) — Borg sem audit comparable publicada

Trade-off pequeno: ambos serviriam, restic é preferência técnica marginal mas significativa em multi-backend roadmap futuro.

---

## Consequences

### Positive

- **F-HIGH-09 RESOLVED EMPIRICALLY** post-deploy (encryption-at-rest provável via `file restic-repo/data/*` mostrando binary content, NÃO `sqlite3` magic bytes)
- **Defense-in-depth completa:** Combina com LGPD §16 tempfile cleanup (Sprint 8 Phase A) + audit chain HMAC (ADR-014) = 3 camadas proteção PII workflow
- **Future-proof PII evolution:** Quando peças jurídicas generation adicionar customer name/CPF aos backups, encryption já ativa (zero retrofit)
- **LGPD §46 audit defensible:** "Encryption-at-rest via restic AES-256-CTR + Poly1305 MAC" é controle técnico documentável em DPO report
- **Retention preserved:** restic `forget --keep-within Nd` integra com Story #14 `REVISOR_BACKUP_RETENTION_DAYS=30` env
- **S3 backend ready:** Sprint 9+ offsite migration trivial (`restic -r s3:s3.amazonaws.com/bucket backup ...`)
- **Snapshot atomic restore:** `restic restore <snapshot-id> --target /tmp/restore` substitui current cp procedure (mais confiável)
- **Deduplication economy:** vault.db rarely changes between nights → restic detecta chunks idênticos → snapshots incrementais ~kilobytes vs full ~3.5MB

### Negative

- **Additional dependency:** restic install Dockerfile (+25MB image)
- **Operational learning curve:** Operator team precisa aprender restic CLI (restore = `restic restore`, list = `restic snapshots`, integrity = `restic check`)
- **Password management responsibility:** Loss of /etc/restic/password.txt = LOSS of all encrypted backups irreversibly (mitigado por key escrow procedure)
- **Migration window risk:** 30-day transitional period mantém legacy plaintext backups (technically expanded attack surface durante migration)
- **Restore complexity slight increase:** Cross-reference runbook atualização obrigatória pré-deploy

### Neutral

- **Image size +25MB:** Negligible (image já 10.2GB)
- **Backup runtime slight increase:** restic add overhead ~1-2s para encryption + MAC computation (vs cp instantâneo). Total backup_daily ainda < 10s.
- **No PII content currently:** Encryption é defense-in-depth + future-proofing, NÃO immediate LGPD §46 obrigatório (alinha ADR-029 §3 original rationale)

---

## Spec Coverage — Implementation Outline para Neo (Story #11)

### Phase 1: Dockerfile (~15min)

- File: `Dockerfile`
- Change: Add `restic` apt-get install layer
- Test: `docker build` succeeds + `docker run --rm image which restic` returns `/usr/bin/restic`

### Phase 2: bloco_backup/scheduler.py refactor (~1h)

- Replace `backup_daily()` cp-based logic with `backup_daily_encrypted()` restic subprocess
- Replace `cleanup_old_snapshots()` rotation logic with `cleanup_old_snapshots_encrypted()` restic forget+prune
- Preserve APScheduler job registration (BackgroundScheduler + CronTrigger hour=2 minute=0)
- Preserve env var resolution (`REVISOR_BACKUP_RETENTION_DAYS` from Story #14 — `_resolve_retention_days()` helper)
- Add error handling: subprocess timeout + non-zero returncode → RuntimeError + logger.error

### Phase 3: Tests (~45min)

- File: `tests/integration/test_backup_encryption_restic.py` (NEW)
- 5 tests minimum:
  1. `test_backup_daily_encrypted_invokes_restic_with_correct_args` (mock subprocess)
  2. `test_backup_daily_encrypted_raises_on_nonzero_returncode`
  3. `test_cleanup_old_snapshots_encrypted_uses_retention_env`
  4. `test_restic_repository_env_default_path`
  5. `test_restic_password_file_env_default_path`

### Phase 4: docker-compose.prod.yml (deploy — Operator domain)

- Per feedback_operator_no_code_edits: Neo NÃO edita docker-compose. Operator deploy adiciona:
  - `RESTIC_REPOSITORY` env
  - `RESTIC_PASSWORD_FILE` env
  - `/etc/restic:/etc/restic:ro` volume mount

### Phase 5: One-time Setup (Operator deploy)

- Per feedback_operator_no_code_edits: Operator domain, NÃO Neo:
  - Generate password file
  - Init restic repo dentro container
  - Key escrow Eric USB
  - First backup verify

### Phase 6: Migration (Operator deploy)

- Day 0-30: Co-existence monitoring
- Day 31: Delete legacy plaintext backups

### Phase 7: Runbook Update (Architect collaboration with Operator)

- Update `governance/runbook-backup-restore.md`:
  - Section "Restore Procedure" → restic-based steps
  - Section "Backup Integrity Check" → `restic check --read-data-subset 5%` weekly
  - Section "Password Rotation" → procedure acima

---

## ADR-029 Cross-Reference Amendment

ADR-029 §3 "Encryption Decision" texto original:

> "Sprint 9+ scope (separate ADR): GPG file-level encryption OR LUKS volume mount, decidir conforme threat model evolution (e.g., offsite backup S3)."

**ADR-031 amendment:** ADR-029 §3 é **superseded em parte** por esta decisão. ADR-029 §3 deferral rationale (ZERO PII content) permanece **válido para audit defense LGPD §46 obrigatório**, MAS ADR-031 promove de "deferred" para "implemented" por 4 razões (Sprint 8 v2.0 scope expansion, Phase B parallel pattern, future-proofing, LGPD §46 best practice baseline).

ADR-029 mantém status `accepted` (não superseded inteiramente — §1 visibility, §2 retention 30d, §4 offsite Sprint 9+ permanecem válidos).

ADR-029 será atualizada com adendo apontando para ADR-031 (cross-reference apenas, status preserved).

---

## Operator Action Items (One-time setup, post-Neo Story #11 code merge)

| Action | Owner | Estimate |
|--------|-------|----------|
| Generate `/etc/restic/password.txt` (openssl rand) | @devops | 5min |
| Set permissions chmod 400 root:root | @devops | 1min |
| Add env vars + volume mount em docker-compose.prod.yml | @devops | 10min |
| Image rebuild com Dockerfile restic install | @devops | 5-10min |
| Container recreate (ollama-shared preserved per ADR-026) | @devops | 2min |
| `restic init` dentro container | @devops | 1min |
| First `restic backup` manual smoke test | @devops | 5min |
| Verify snapshot list: `restic snapshots` returns 1 entry | @devops | 1min |
| `restic check` integrity verify | @devops | 2min |
| Document key escrow USB procedure executed (Eric custody) | @devops + Eric | 30min (USB encrypt + physical store) |
| Update runbook restore section restic-based | @devops + @architect | 1h |
| Operator restore drill empirical (test restore latest snapshot to /tmp) | @devops + @qa | 30min |

**Total Operator estimate post-Neo:** ~3h cumulative (em janela única deploy)

---

## Smith Verification Targets Post-Implementation

Smith Phase B mini-verify (futura) DEVE validar empiricamente:

1. **F-HIGH-09 RESOLVED:** `file /home/revisor/.local/share/revisor-contratual/restic-repo/data/00/*` retorna `data` (binary opaque), NÃO `SQLite 3.x database` (plaintext detectable).
2. **Restore drill PASS:** Operator demonstra `restic restore latest --target /tmp/test-restore` produzindo vault.db readable.
3. **Integrity check PASS:** `restic check --read-data-subset 10%` retorna `no errors were found`.
4. **Retention env integration:** `restic forget --keep-within 30d` respects Story #14 `REVISOR_BACKUP_RETENTION_DAYS`.
5. **APScheduler logs:** `docker logs revisor-prod-app | grep "restic backup OK"` mostra job daily 02:00 success.
6. **Password file permissions:** `ls -la /etc/restic/password.txt` mostra `-r-------- 1 root root`.
7. **No plaintext leak migration period:** Legacy `backups/YYYY-MM-DD/` files também ainda chmod 600 revisor:revisor (no regression).

---

## Sprint 9+ Future Work (Separate ADRs)

| Topic | ADR # | Status |
|-------|-------|--------|
| Offsite backup S3/B2/Hetzner Storage Box (with restic native backend) | ADR-032 (future) | Pending — leverages ADR-031 restic foundation |
| Backup integrity validation tool (cron weekly `restic check` + alerting) | ADR-033 (future) | Pending |
| Backup encryption key escrow formalization (SOC2 alignment se needed) | ADR-034 (future) | Pending — only if SOC2 path adopted |

---

## Cross-References

- **Smith ultrathink F-HIGH-09:** `governance/qa/smith-ultrathink-aplicacao-completa-hardware-2026-05-16.md:213-217`
- **Related ADR-029 backup-strategy:** `governance/architecture/adr/adr-029-backup-strategy.md` (this ADR supplements §3 Encryption Decision)
- **Related ADR-013 §2.4 APScheduler:** preserved — restic invoked via subprocess from same APScheduler jobs
- **Related ADR-014 audit chain HMAC:** preserved — restic encrypts audit.jsonl preserving HMAC integrity inside encrypted snapshot
- **LGPD Lei 13.709/2018:** §11 (princípios) + §46 (segurança técnica)
- **Sprint 8 Phase B Story #11:** implementation target (Neo handoff in `.lmas/handoffs/handoff-architect-to-dev-2026-05-16-sprint-8-phase-b-story-11-restic-impl.yaml`)
- **Runbook:** `governance/runbook-backup-restore.md` (requires Operator+Architect update post-implementation)

---

*ADR-031 published by @architect (Aria) 2026-05-16 — Sprint 8 Phase B Story #11. Supplements ADR-029 §3 Encryption Decision (promotes deferred → implemented). Resolves Smith F-HIGH-09 architecturally. Implementation handoff Architect→Neo created.*
