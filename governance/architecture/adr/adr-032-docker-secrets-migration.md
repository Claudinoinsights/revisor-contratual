---
type: adr
id: "ADR-032"
title: "Docker Secrets Migration — Env Vars → /run/secrets/ Pattern (Sprint 9+ Deferred)"
status: proposed
date: "2026-05-16"
domain: "infra"
decision_makers: ["@architect (Aria)", "@devops (Operator)"]
supersedes: ""
superseded_by: ""
adr_level: design
related:
  - "ADR-031 backup encryption (precedent for security hardening Sprint 8 Phase B)"
  - "Smith ultrathink F-S8PB-MV-LOW-01 (governance/qa/smith-verify-sprint-8-phase-b-mini-2026-05-16.md)"
  - "ADR-029 backup-strategy (env var pattern used: REVISOR_BACKUP_RETENTION_DAYS)"
  - "ADR-013 §2.4 APScheduler embedded (existing env-based config pattern)"
tags:
  - project/revisor-contratual
  - adr
  - sprint-9-plus
  - docker-secrets
  - security-hardening
  - defense-in-depth
  - lgpd-compliance
---

# ADR-032 — Docker Secrets Migration (Sprint 9+ Deferred)

## Status

**Proposed** — 2026-05-16 (Sprint 9+ deferred — current env-based pattern is acceptable industry practice para single-tenant deployment)

---

## Context

Smith Phase B mini-verify (D-SMITH-S08-002, 2026-05-16) identificou:

> **F-S8PB-MV-LOW-01 (LOW) — REVISOR_SECRET_KEY in env vars**
>
> Probe 4 revelou `env` command em container expõe `REVISOR_SECRET_KEY=c2c4c4531ff46c2721ac418339bc1b9b4544c42dbe5398e929d96246a37f557d` em plaintext.
>
> Single-user container faz isso aceitável industry practice MAS defense-in-depth could improve via Docker secrets (compose v3.1+ `secrets:` section, mounts secrets em /run/secrets/ com chmod 400).

### Current Pattern (Sprint 8 Phase B baseline)

Sensitive configuration values vivem em container env vars via `docker-compose.prod.yml`:

```yaml
services:
  app:
    environment:
      REVISOR_ENV: "production"
      REVISOR_HTTPS_ONLY: "1"
      REVISOR_BACKUP_RETENTION_DAYS: "30"
      RESTIC_REPOSITORY: "/home/revisor/.local/share/revisor-contratual/restic-repo"
      RESTIC_PASSWORD_FILE: "/etc/restic/password.txt"  # path only, not secret itself
    env_file:
      - .env  # contains REVISOR_SECRET_KEY, BYOK keys, etc.
```

**Attack surface (current):**

1. `docker exec app env` reveals all env vars including sensitive
2. `/proc/{pid}/environ` readable by container processes
3. Process inspection via container ps/top reveals env via OS-level interface
4. Container debug/admin sessions accidentally screenshot containing secrets

**Mitigations já em vigor:**

- Single-tenant deployment (Eric operador) — único user dentro container é `revisor` (uid 1000)
- `.env` file gitignored (no public exposure)
- HTTPS only + secure headers (no network exfiltration via app responses)
- LGPD §46 audit chain HMAC + restic encryption (ADR-031) protect data at rest

### LGPD Compliance Anchor

**Lei 13.709/2018 §46 (Segurança Técnica):** "medidas de segurança, técnicas e administrativas aptas a proteger os dados pessoais de acessos não autorizados".

REVISOR_SECRET_KEY especificamente é session signing key — compromise allows session hijacking + impersonation. While not "dados pessoais" itself, é authentication trust root para customer access.

Docker secrets pattern supporta §46 defense-in-depth requirement como controle técnico documentável em DPO/ANPD audit.

---

## Decision (PROPOSED — Sprint 9+ implementation)

**Adopt Docker Secrets pattern for sensitive configuration values** — migrate from `environment:`/`env_file:` to `secrets:` mount em /run/secrets/.

**Scope (incremental, opt-in):**

| Secret | Current Storage | Target Pattern | Priority |
|--------|----------------|----------------|----------|
| REVISOR_SECRET_KEY | env var em `.env` | `/run/secrets/revisor_secret_key` (chmod 400) | HIGH (auth trust root) |
| RESTIC_PASSWORD_FILE path | env var | Keep as env (already points to file mount /etc/restic/password.txt) | NO CHANGE (already secure via bind mount chmod 400) |
| Future: BYOK Anthropic API keys per-tenant | PostgreSQL row (already not env) | Keep DB pattern (RLS-protected) | NO CHANGE |
| Future: SMTP credentials se notifications added | TBD | `/run/secrets/smtp_password` direct | Design from start |
| Future: OAuth client secrets se SSO added | TBD | `/run/secrets/oauth_*_secret` | Design from start |

**Implementation pattern (target):**

```yaml
# docker-compose.prod.yml (Sprint 9+)
services:
  app:
    secrets:
      - revisor_secret_key
    environment:
      # SECRET_KEY_FILE points to mounted secret (Flask/FastAPI reads file)
      REVISOR_SECRET_KEY_FILE: /run/secrets/revisor_secret_key

secrets:
  revisor_secret_key:
    file: /etc/revisor/secret_key.txt  # host file chmod 400 root
```

**Application code change required:**

```python
# bloco_interface/web/app.py or config module
import os

def _resolve_secret_key() -> str:
    """Sprint 9+ ADR-032: Read from /run/secrets/* if SECRET_KEY_FILE set, else env fallback."""
    secret_file = os.environ.get("REVISOR_SECRET_KEY_FILE")
    if secret_file and os.path.exists(secret_file):
        with open(secret_file, "r") as f:
            return f.read().strip()
    # Fallback to legacy env var pattern (transition compatibility)
    return os.environ.get("REVISOR_SECRET_KEY", "")
```

### Why Sprint 9+ Deferred (not Sprint 8)

| Factor | Reasoning |
|--------|-----------|
| **Current pattern works** | Single-tenant Eric operador + .env gitignored + container isolation = acceptable industry standard |
| **Migration is opt-in incremental** | Each secret migrated individually — doesn't require all-at-once breaking change |
| **Compose v3.1+ requirement** | Current docker-compose.prod.yml uses v3.8 — Docker Secrets v3.1+ already supported (no compose upgrade needed) |
| **Sprint 8 focus discipline** | Sprint 8 v2.0 scope (17 stories) já expanded — Phase B momentum maintained by NOT scope-creeping |
| **Operational complexity** | Each migration requires Operator infrastructure + Neo code change — coordinated effort better planned in Sprint 9+ |
| **Risk acceptance** | Threat model (single VPS RCE + access to env) is exact same threat protected by Layer 2/3/4 mitigations ADR-031 §Total Password Loss (defense-in-depth layered, not single-point) |

---

## Alternatives Considered

### Alternative A: Status Quo — Keep env vars (Current)

**Pros:**

- Simplest operational model
- No code changes
- Familiar pattern (Twelve-Factor App)

**Cons:**

- env vars visible via `docker exec env` (single-user container mitigates)
- `/proc/{pid}/environ` readable
- Easier accidental exposure (debug screenshots, log dumps)

**Acceptance:** ✅ Acceptable single-tenant baseline (current state). Documented as risk in F-S8PB-MV-LOW-01.

### Alternative B: Docker Secrets (compose v3.1+ `secrets:` mount) — PROPOSED

**Pros:**

- Industry-standard defense-in-depth pattern
- chmod 400 enforcement on mount
- Not visible via `env` command (only via file read)
- Auditable: each secret file has timestamp + ownership
- Compatible com compose v3.8 (current)

**Cons:**

- Application code change required (`_resolve_secret_key()` helper)
- Operator host file management (`/etc/revisor/*.txt` chmod 400)
- Sprint 9+ effort (incremental per secret)

**Recommendation:** ✅ **SELECTED para Sprint 9+ implementation** (when implemented). Aligns com ADR-031 precedent (`/etc/restic/password.txt` pattern already proven).

### Alternative C: HashiCorp Vault

**Pros:**

- Industry-standard secrets management
- Dynamic secrets + rotation + audit logging
- Multi-cloud + Kubernetes native

**Cons:**

- Overkill para single-VPS deployment Eric operador
- Additional infrastructure (Vault server + storage backend)
- Operational complexity (Vault unsealing + token management)
- Network dependency (app → Vault HTTP calls)

**Rejected:** Single-VPS architecture doesn't justify Vault complexity. Revisit se multi-tenant expansion OR Kubernetes migration future.

### Alternative D: Encrypted .env Files (sops / age / git-crypt)

**Pros:**

- Git-friendly (encrypted .env can be committed)
- KMS-integrated rotation possible
- Audit trail via git history

**Cons:**

- CI/CD complexity (decryption step in pipeline)
- Local dev experience requires age/sops install + key distribution
- Doesn't solve runtime exposure (still env vars at runtime)
- Adds tooling burden vs simple file-mount pattern

**Rejected:** Solves git-storage problem (not current pain point — `.env` gitignored), doesn't solve runtime env exposure (which IS the F-S8PB-MV-LOW-01 concern).

---

## Consequences (if Accepted Sprint 9+)

### Positive

- **Defense-in-depth:** chmod 400 enforcement at OS-level
- **No env exposure:** `docker exec env` doesn't reveal secret values
- **Audit trail:** Each `/run/secrets/*` file has filesystem timestamp + ownership
- **ADR-031 pattern consistency:** Aligns com restic password.txt mount pattern já proven
- **LGPD §46 hardening:** Documentable security control improvement
- **Incremental migration:** Per-secret rollout reduces risk
- **Forward-compatible:** Multi-tenant SaaS evolution preserves pattern (per-tenant secrets via Docker compose templates)

### Negative

- **Application code change:** `_resolve_*_secret()` helper per secret (small surface, low risk)
- **Operator host file management:** `/etc/revisor/*.txt` requires careful chmod + chown (same pattern restic — Eric already familiar)
- **Compose template complexity:** `secrets:` declaration + service mount + env file path indirection
- **Sprint 9+ effort:** Estimate ~2-3h per secret migrated (code helper + compose update + deploy + verify)
- **Backwards compatibility transitional:** During migration, app code reads from file OR fallback env (similar dual-mode pattern Story #14 retention env)

### Neutral

- **Performance:** Negligible (file read once at startup)
- **Image size:** Zero impact (no new dependencies)
- **Multi-tenant scaling:** Compatible com per-tenant Docker compose templates Sprint 9+
- **Single-tenant Eric operacional:** Current pattern continues to work — no breaking change

---

## Spec Coverage (Implementation Outline para future Sprint 9+ Neo + Operator)

### Phase 1: Application Code (~1h Neo)

```python
# bloco_interface/web/app.py OR new bloco_config/secrets.py
def resolve_secret_from_file_or_env(secret_name: str, fallback_env: str = None) -> str:
    """ADR-032: Read secret from /run/secrets/* if FILE env set, else env fallback.

    Pattern: REVISOR_{SECRET}_FILE env var points to mounted secret file.
    Backwards compat: falls back to direct env var if file path not set.
    """
    file_env = f"REVISOR_{secret_name.upper()}_FILE"
    file_path = os.environ.get(file_env)
    if file_path and os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    legacy_env = fallback_env or f"REVISOR_{secret_name.upper()}"
    return os.environ.get(legacy_env, "")

# Usage:
REVISOR_SECRET_KEY = resolve_secret_from_file_or_env("secret_key")
```

### Phase 2: Tests (~30min Neo)

- 4 unit tests via pytest.MonkeyPatch + tmp_path:
  - test_resolve_secret_from_file_when_file_exists
  - test_resolve_secret_falls_back_to_env_when_file_missing
  - test_resolve_secret_falls_back_to_env_when_file_path_unset
  - test_resolve_secret_handles_missing_secret_gracefully

### Phase 3: Operator Host Setup (~30min Operator)

```bash
sudo mkdir -p /etc/revisor
sudo sh -c 'openssl rand -hex 32 > /etc/revisor/secret_key.txt'
sudo chmod 400 /etc/revisor/secret_key.txt
sudo chown 1000:1000 /etc/revisor/secret_key.txt  # uid-matching container per ADR-031 pattern
```

### Phase 4: Compose Update (~15min Operator)

```yaml
services:
  app:
    secrets:
      - revisor_secret_key
    environment:
      REVISOR_SECRET_KEY_FILE: /run/secrets/revisor_secret_key

secrets:
  revisor_secret_key:
    file: /etc/revisor/secret_key.txt
```

### Phase 5: Migration Plan (~30min Operator transitional)

- D+0: Deploy code + secret file + new env (legacy REVISOR_SECRET_KEY still present)
- D+0 → D+7: Verify Flask/FastAPI sessions still valid (no breakage)
- D+7: Remove legacy REVISOR_SECRET_KEY from `.env` (force file path resolution)
- D+7+: Monitor session integrity, document in checkpoint

### Phase 6: Key Escrow (~15min Eric)

- Eric copies `/etc/revisor/secret_key.txt` to encrypted USB (same procedure ADR-031 §Key Escrow)
- Document em PASSWORD-RECOVERY-PLAN.md (local, NÃO git)

---

## Future ADRs Cross-Reference

| Topic | ADR # | Status | Dependency |
|-------|-------|--------|------------|
| Offsite backup S3/B2 (separate encryption key) | ADR-030 | reserved | Leverages ADR-031 restic foundation |
| **Docker Secrets Migration** | **ADR-032** | **proposed (this)** | **Standalone — can implement independently** |
| Backup integrity validation cron | ADR-033 | future | Sprint 9+ scope |
| Multi-tenant secrets per-customer | ADR-034 | future | Requires multi-tenant architecture decision first |

---

## Cross-References

- **Smith Phase B mini-verify D-SMITH-S08-002:** `governance/qa/smith-verify-sprint-8-phase-b-mini-2026-05-16.md` (F-S8PB-MV-LOW-01 source)
- **ADR-031 backup encryption:** Pattern precedent — `/etc/restic/password.txt` chmod 400 uid 1000 bind mount (this ADR follows same pattern for other secrets)
- **ADR-029 backup-strategy:** Existing env var pattern for non-sensitive config (REVISOR_BACKUP_RETENTION_DAYS — stays env, not migrating)
- **ADR-013 §2.4 APScheduler embedded:** Existing config resolution via env helper (`_resolve_retention_days`) — same pattern reused for secrets
- **LGPD Lei 13.709/2018 §46:** Compliance anchor (segurança técnica documentável)
- **Runbook §Total Password Loss (Smith F-LOW-05):** Multi-layer mitigation philosophy aplica também a este ADR (defense-in-depth)

---

## Sprint Planning Triggers (when to promote proposed → accepted)

ADR-032 should be promoted from `proposed` → `accepted` quando ANY trigger fires:

1. **Multi-tenant SaaS architecture decision approved** (per-customer secrets become mandatory)
2. **External security audit recommends secrets migration** (DPO/ANPD audit, SOC2 path, etc.)
3. **Sprint 9+ planning capacity allows** (low priority — wait for trigger 1 or 2)
4. **Operator detects env exposure incident** (e.g., screenshot leaked, log dump containing secrets)
5. **Eric pivot adds high-value secrets** (OAuth client secrets, SMTP credentials, third-party API tokens)

---

*ADR-032 published em proposed status por @architect (Aria) 2026-05-16 — Sprint 8 Phase B post-Smith governance D-ARIA-S08-003. Defers implementation to Sprint 9+. Documents migration path proactively to enable rapid execution quando trigger fires. Pattern aligns com ADR-031 restic precedent.*
