---
type: adr
id: "ADR-009"
title: "BACKUP_DIR external path + pseudonimização HMAC LGPD"
status: superseded
date: "2026-05-01"
superseded_date: "2026-05-07"
domain: "lgpd-backup"
decision_makers: ["@architect (Aria)"]
supersedes: null
superseded_by: "ADR-017"
absorves:
  - "R-NEW-SMITH-01 (BACKUP_DIR default mesmo disco)"
  - "R-NEW-SMITH-07 (pseudonimização determinística vulnerável a rainbow table)"
related_to:
  - "FR-BACKUP-01 (backup automático N=5 petições)"
  - "NFR-LGPD-04 (pseudonimização relator)"
  - "ADR-005 (HMAC com AUTH_COOKIE_KEY)"
project: revisor-contratual
sprint: "01"
etapa: "2.0"
tags:
  - project/revisor-contratual
  - adr
  - backup
  - lgpd
  - pseudonimizacao
  - hmac
  - superseded
---

> ⚠️ **SUPERSEDED** (2026-05-07) — Este ADR foi substituído por [ADR-017](adr-017-multi-tenant-isolation-rls.md).
> Razão: Sprint 04 pivot SaaS BYOK — Eric Claudino vira **OPERADOR LGPD** (não controlador);
> escritório cliente é o controlador e responsável pela pseudonimização com seu cliente final.
> Pseudonimização local não se aplica. PII passa direto via API key escritório → Anthropic,
> com retention zero pós-resposta. Mantido para contexto histórico do design Sprint 03
> single-tenant on-premise.

# ADR-009 — BACKUP_DIR external path + pseudonimização HMAC LGPD

```
[@architect · Aria (Visionary)] — etapa 2.0 · ADR-009 BACKUP+LGPD
SPRINT: 01 · ETAPA: 2.0 · DOMÍNIO: SoftwareDev/legaltech
```

## Contexto

PRD v1.0.2 estabelece duas políticas que Smith re-atacou no segundo tribunal:

**Backup (FR-BACKUP-01):**
- Trigger: a cada N petições (default N=5)
- BACKUP_DIR configurável; default `./backups/`

**Smith R-NEW-SMITH-01 (HIGH):** default `./backups/` é **mesmo disco** que `outcomes.db`. Cenário catastrófico:
- Advogado tem 50 outcomes em 8 meses (base ML estágio 2 prestes a iniciar)
- SSD do laptop falha (~2% AFR consumer SSDs)
- `outcomes.db` perdido + `./backups/` perdido = **perda TOTAL** do estágio 1 do ML

**Pseudonimização (NFR-LGPD-04):**
- Campo `relator` no outcomes.db pseudonimizado: `sha256(nome_relator + salt)`

**Smith R-NEW-SMITH-07 (MEDIUM):** hash determinístico com salt no código → vulnerável a rainbow table:
- Lista de juízes ativos do TJBA: ~200 nomes
- Salt no código → attacker faz rainbow table em <10s
- Pseudonimização efetiva NÃO É se conseguir reverter

Aria precisa: definir defaults seguros para backup + cryptographically secure pseudonimização.

## Decisão

**Adotamos:**
1. **BACKUP_DIR default external path** com auto-detecção e validação `f_fsid` (Linux/Mac) / volume distinto (Windows)
2. **Pseudonimização via HMAC-SHA256 com chave secreta dedicada** (`LGPD_PSEUDONIMIZATION_KEY`)
3. **Mapping table reversa** em arquivo separado read-only (acesso restrito chmod 600)

### Detalhes técnicos — Backup

```python
# bloco_audit/backup.py

import os
from pathlib import Path
import sys

DEFAULT_PATHS = {
    "linux": [
        Path("/media/$USER"),                       # USB drives auto-mounted
        Path.home() / "Documentos" / "Revisor-Backups",
    ],
    "darwin": [
        Path("/Volumes"),                           # USB drives macOS
        Path.home() / "Documents" / "Revisor-Backups",
    ],
    "win32": [
        Path("D:/Revisor-Backups"),                 # Drive D comum (HDD secundário)
        Path("E:/Revisor-Backups"),                 # USB drive
        Path.home() / "Documents" / "Revisor-Backups",  # Fallback mesmo disco (warn)
    ],
}

def get_backup_dir() -> tuple[Path, bool]:
    """
    Retorna (path, is_external_disk).
    Prioriza disco externo. Avisa se mesmo disco que outcomes.db.
    """
    # 1. Respeitar override .env
    if "BACKUP_DIR" in os.environ:
        configured = Path(os.environ["BACKUP_DIR"])
        is_external = _check_external_volume(configured)
        return configured, is_external

    # 2. Auto-detect external
    platform = sys.platform if sys.platform in ("linux", "darwin") else "win32"
    for candidate in DEFAULT_PATHS[platform]:
        if _is_writable_external(candidate):
            return candidate, True

    # 3. Fallback: mesmo disco com WARN visível (R-NEW-SMITH-01 mitigado)
    fallback = Path.home() / "Documents" / "Revisor-Backups"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback, False

def _check_external_volume(path: Path) -> bool:
    """Compara f_fsid (Linux/Mac) ou drive letter (Windows) com outcomes.db."""
    outcomes_path = Path("bloco_learning/outcomes.db").resolve()

    if sys.platform in ("linux", "darwin"):
        try:
            outcomes_fsid = os.statvfs(outcomes_path).f_fsid
            backup_fsid = os.statvfs(path).f_fsid
            return outcomes_fsid != backup_fsid
        except (FileNotFoundError, OSError):
            return False
    else:  # Windows
        outcomes_drive = outcomes_path.anchor.upper()  # ex: "C:\"
        backup_drive = path.resolve().anchor.upper()
        return outcomes_drive != backup_drive

def show_backup_warning_if_needed():
    """No setup + no startup, mostra warning visual se backup mesmo disco."""
    _, is_external = get_backup_dir()
    if not is_external:
        st.warning(
            "⚠️ **Backup configurado no mesmo disco do banco principal**\n\n"
            "Risco: falha de SSD/HDD perde TUDO (originais + backups). "
            "Configure `BACKUP_DIR` em `.env` apontando para drive externo "
            "(USB, HDD secundário, NAS, ou cloud sync local como Dropbox/OneDrive).\n\n"
            "Documentação: docs/setup-backup-external.md"
        )
```

### Detalhes técnicos — Pseudonimização

```python
# bloco_learning/pseudonimizacao.py

import hmac
import hashlib
import os
from pathlib import Path
from datetime import datetime, timezone
import sqlite3

MAPPING_DB_PATH = Path("bloco_learning/relator_mapping.db")

def _get_pseudo_key() -> bytes:
    """Chave dedicada — NÃO reutilizar AUTH_COOKIE_KEY (separação de responsabilidade)."""
    key = os.environ.get("LGPD_PSEUDONIMIZATION_KEY")
    if not key:
        raise RuntimeError(
            "LGPD_PSEUDONIMIZATION_KEY não configurada. "
            "Gere com: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return key.encode("utf-8")

def pseudonimizar_relator(nome_relator: str) -> str:
    """
    Retorna pseudonym HMAC-SHA256.
    R-NEW-SMITH-07 mitigado: rainbow table requer LGPD_PSEUDONIMIZATION_KEY,
    que é secret no .env (não no código).
    """
    key = _get_pseudo_key()
    pseudo = hmac.new(key, nome_relator.encode("utf-8"), hashlib.sha256).hexdigest()
    _persist_mapping(nome_relator, pseudo)
    return pseudo

def _persist_mapping(nome: str, pseudo: str) -> None:
    """Mapping reverso em DB separado, chmod 600 (rw owner only)."""
    MAPPING_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    is_new = not MAPPING_DB_PATH.exists()

    conn = sqlite3.connect(MAPPING_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS relator_mapping (
            pseudo TEXT PRIMARY KEY,
            nome_real TEXT NOT NULL,
            criado_em TEXT NOT NULL,
            ultimo_uso TEXT NOT NULL,
            uso_count INTEGER NOT NULL DEFAULT 1
        )
    """)

    conn.execute("""
        INSERT INTO relator_mapping (pseudo, nome_real, criado_em, ultimo_uso, uso_count)
        VALUES (?, ?, ?, ?, 1)
        ON CONFLICT(pseudo) DO UPDATE SET
            ultimo_uso = excluded.ultimo_uso,
            uso_count = uso_count + 1
    """, [pseudo, nome, datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat()])

    conn.commit()
    conn.close()

    if is_new and os.name != "nt":
        os.chmod(MAPPING_DB_PATH, 0o600)  # rw owner only
    elif is_new:
        _windows_set_owner_only(MAPPING_DB_PATH)

def reverter_relator(pseudo: str) -> str | None:
    """
    Apenas para uso INTERNO (visualização ao próprio advogado dono dos dados).
    NUNCA exposto via API/UI pública. NUNCA em logs.
    """
    if not MAPPING_DB_PATH.exists():
        return None
    conn = sqlite3.connect(MAPPING_DB_PATH)
    row = conn.execute(
        "SELECT nome_real FROM relator_mapping WHERE pseudo = ?", [pseudo]
    ).fetchone()
    conn.close()
    return row[0] if row else None

# ML pipeline (estágio 2) usa APENAS pseudo — nunca chama reverter_relator
def get_features_for_ml(petition_id: str) -> dict:
    outcome = _load_outcome(petition_id)
    return {
        "relator_pseudo": outcome.relator_pseudo,  # HMAC, irreversível sem key
        "camara": outcome.camara,
        "valor_revisado": outcome.valor_revisado,
        # ... demais features
    }
```

### Bootstrap LGPD_PSEUDONIMIZATION_KEY

```bash
# FR-SETUP-01 estendido — gerar chave LGPD no setup
$ python -m revisor bootstrap
> ✅ AUTH_COOKIE_KEY gerada (sessão + audit)
> ✅ LGPD_PSEUDONIMIZATION_KEY gerada (relator)
> ⚠️  Faça backup das chaves em local SEPARADO do laptop:
>    - AUTH_COOKIE_KEY: necessária para sessão + audit log integrity
>    - LGPD_PSEUDONIMIZATION_KEY: necessária para reverter pseudonyms
>    Perda da chave = audit log inválido OU pseudonyms irreversíveis.
```

## Razão

### Backup
- **Auto-detecção de external volume:** maioria dos usuários sabe ligar USB; sistema escolhe automaticamente
- **`f_fsid`/drive letter check:** verificação programática objetiva (não palpite)
- **Warning visual quando fallback mesmo disco:** explicitar risco em vez de silenciar
- **Fallback NÃO bloqueia uso:** advogado pode prosseguir com risco assumido (não-bloqueante)
- **Documentação dedicada:** `docs/setup-backup-external.md` com instruções multi-SO

### Pseudonimização
- **HMAC > SHA256+salt determinístico:** secret protege contra rainbow table mesmo com lista de nomes conhecidos
- **Chave dedicada (não reutilizar AUTH_COOKIE_KEY):** separação de responsabilidades — perda de uma chave não compromete outra
- **Mapping table separado em DB:** consultas SQL flexíveis, transações atômicas, chmod 600
- **ML pipeline usa apenas pseudo:** garantia operacional de não-vazamento (LGPD Art. 7 inciso V)
- **`reverter_relator` apenas uso interno do dono:** advogado pode ver seus próprios dados, ML/API não pode

## Alternativas Consideradas

### Backup

#### Alt 1 — Manter `./backups/` default sem warning (PRD original)
- **Prós:** simples
- **Contras:** risco silencioso de perda total; R-NEW-SMITH-01 não-mitigado
- **Rejeitada:** absorver R-NEW-SMITH-01 é alvo da ADR

#### Alt 2 — Forçar BACKUP_DIR external (bloqueante se falhar)
- **Prós:** segurança máxima
- **Contras:** UX hostil — usuário sem USB/HDD secundário não consegue usar produto
- **Rejeitada:** warn é suficiente; user agency preservada

#### Alt 3 — Cloud backup automático (S3/Backblaze)
- **Prós:** redundância geográfica
- **Contras:** **viola 100% local LGPD**; custo recorrente; complexidade
- **Rejeitada:** princípio inegociável

#### Alt 4 — rsync incremental para drive externo
- **Prós:** eficiente espaço/tempo
- **Contras:** dependência externa (rsync); Windows precisa Cygwin/WSL; complexidade
- **Rejeitada para MVP:** revisitar se backups crescerem >1GB

### Pseudonimização

#### Alt 1 — Manter SHA256 + salt no código (PRD original)
- **Prós:** simples
- **Contras:** **vulnerável conforme R-NEW-SMITH-07** — rainbow table em ~10s
- **Rejeitada:** absorver é alvo da ADR

#### Alt 2 — UUIDv4 random + mapping table (sem hash)
- **Prós:** completamente irreversível sem mapping
- **Contras:** mapping table vira ponto único de falha; sem mapping, dados são lixo (não há derivação)
- **Rejeitada:** HMAC dá flexibilidade similar com vantagem de derivação

#### Alt 3 — Reutilizar AUTH_COOKIE_KEY para HMAC pseudo
- **Prós:** menos chaves para gerenciar
- **Contras:** acoplamento — comprometer 1 secret afeta auth + audit + LGPD
- **Rejeitada:** princípio de separação de responsabilidades

#### Alt 4 — Encryption simétrica (AES-GCM) em vez de HMAC
- **Prós:** reversível com chave (não precisa mapping table)
- **Contras:** mais complexo; HMAC + mapping table é equivalente em segurança e mais simples
- **Rejeitada:** complexidade desnecessária

## Consequências

### Positivas
- **R-NEW-SMITH-01 e R-NEW-SMITH-07 NEUTRALIZADOS**
- Default seguro para backup (auto-detect external)
- User agency preservada (warn vs block)
- Pseudonimização cryptographically secure
- Separação de chaves (AUTH_COOKIE_KEY vs LGPD_PSEUDONIMIZATION_KEY)
- ML pipeline operacional sem nomes em claro (LGPD Art. 7 V atendido)

### Negativas / Tradeoffs
- 1 chave secreta a mais para usuário gerenciar (LGPD_PSEUDONIMIZATION_KEY)
- Mapping table cria responsabilidade adicional (proteger acesso, backup separado)
- Auto-detect de external volume pode falhar em ambientes não-padrão (servidor headless sem USB) — mitigado pelo fallback documentado
- Windows ACL para chmod 600 menos robusto que POSIX (workaround documentado)

### Neutras
- Documentação multi-SO de setup external backup (`docs/setup-backup-external.md`) — esforço one-time
- Política de retenção do mapping_db: indefinida (DP-NOVO)

## Decisão Pendente Documentada

**DP-NOVO (criada por esta ADR):** definir política de retenção e expurgo do `relator_mapping.db`. Opções:
- (A) Indefinida (preservar para revisões históricas)
- (B) Expurgo automático após N anos (LGPD princípio da minimização)
- (C) Configurável via .env

Owner: Eric (humano) em coordenação com @lmas-master Morpheus. Bloqueia apenas auditoria LGPD final, não MVP.

## Referências

- PRD v1.0.2: FR-BACKUP-01/02 (linhas 437-450), NFR-LGPD-04 (linhas 608-614), FR-SETUP-01 (linhas 424-435)
- Smith re-review: R-NEW-SMITH-01 + R-NEW-SMITH-07 (qa/smith-adversarial-rereview-prd-v1.0.2.md)
- LGPD Lei 13.709/2018 Art. 7 inciso V (interesse legítimo agregado)
- HMAC NIST SP 800-107 (referenciado em ADR-005)
- Python `os.statvfs`: https://docs.python.org/3/library/os.html#os.statvfs
- ADR-005 (HMAC pattern compartilhado para audit log)

---

*Aria, defendendo a perda total e a reversibilidade indevida — duas faces do mesmo princípio: segurança não é configurável por padrão. 🏗️*
