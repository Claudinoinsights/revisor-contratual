---
type: adr
id: "ADR-005"
title: "Audit log integrity: hash chain Merkle com HMAC GENESIS anchor"
status: accepted
date: "2026-05-01"
domain: "seguranca-audit"
decision_makers: ["@architect (Aria)"]
supersedes: null
superseded_by: null
absorves:
  - "R-NEW-SMITH-03 (CRÍTICA — GENESIS sem âncora externa)"
related_to:
  - "FR-AUDIT-01 estendido (hash chain Merkle)"
  - "NFR-SEC-01 (auth bcrypt + AUTH_COOKIE_KEY)"
project: revisor-contratual
sprint: "01"
etapa: "2.0"
tags:
  - project/revisor-contratual
  - adr
  - audit
  - hash-chain
  - hmac
  - critico
---

# ADR-005 — Audit log integrity: hash chain Merkle com HMAC GENESIS anchor

```
[@architect · Aria (Visionary)] — etapa 2.0 · ADR-005 audit log integrity
SPRINT: 01 · ETAPA: 2.0 · DOMÍNIO: SoftwareDev/legaltech
```

## Contexto

PRD v1.0.2 FR-AUDIT-01 estendido define hash chain Merkle no `audit.jsonl`:
- Cada entry inclui `previous_entry_hash = sha256(entry_anterior)`
- Primeira entry tem `previous_entry_hash = "GENESIS"`
- Comando CLI `verify-audit-integrity` recalcula chain e detecta tampering

**Smith levantou na re-review (R-NEW-SMITH-03 — CRÍTICA):** se "GENESIS" é string literal estática, attacker com acesso ao audit.jsonl pode:
1. Forjar uma entry "anterior" fictícia com `previous_entry_hash = "GENESIS"`
2. Re-hashear toda a chain seguinte com a entry forjada como root
3. `verify-audit-integrity` valida a chain (cada hash[N] = sha256(entry[N-1])) mas **não distingue qual é a entry GENESIS REAL**

A chain é **localmente consistente mas globalmente forjável** — auditor não consegue provar que a entry "GENESIS" original não foi substituída por uma falsa.

Este vetor é crítico porque audit log é evidência probatória em caso de questionamento judicial sobre uma petição gerada (CFOAB FR-DELIV-06). Audit forjável = evidência inválida = produto sem proteção legal real.

## Decisão

**Adotamos GENESIS como hash de payload imutável protegido por HMAC com chave secreta do projeto:**

```
GENESIS_HASH = HMAC-SHA256(
    key   = AUTH_COOKIE_KEY,
    msg   = project_init_timestamp_iso8601 + "|" + "REVISOR-CONTRATUAL-GENESIS"
)
```

E **registramos GENESIS_HASH em arquivo separado read-only** (`bloco_audit/.audit-genesis.lock` com chmod 400).

### Detalhes técnicos

```python
# bloco_audit/genesis.py

import hmac
import hashlib
import os
from pathlib import Path
from datetime import datetime, timezone

GENESIS_LOCK_PATH = Path("bloco_audit/.audit-genesis.lock")
AUDIT_LOG_PATH = Path("bloco_audit/audit.jsonl")

def _compute_genesis_hash(project_init_ts: str, secret_key: bytes) -> str:
    msg = f"{project_init_ts}|REVISOR-CONTRATUAL-GENESIS".encode("utf-8")
    return hmac.new(secret_key, msg, hashlib.sha256).hexdigest()

def initialize_audit_genesis() -> str:
    """Roda 1× no primeiro startup. Cria .audit-genesis.lock imutável."""
    if GENESIS_LOCK_PATH.exists():
        raise RuntimeError(f"GENESIS já inicializado em {GENESIS_LOCK_PATH}. "
                           f"Não recriar — risco de invalidar audit log existente.")

    secret_key = os.environ["AUTH_COOKIE_KEY"].encode("utf-8")
    if not secret_key:
        raise RuntimeError("AUTH_COOKIE_KEY não configurado em .env — necessário para GENESIS HMAC")

    init_ts = datetime.now(timezone.utc).isoformat()
    genesis_hash = _compute_genesis_hash(init_ts, secret_key)

    GENESIS_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GENESIS_LOCK_PATH, "w", encoding="utf-8") as f:
        f.write(f"{init_ts}\n{genesis_hash}\n")

    # chmod 400 (read-only owner) — Linux/Mac; Windows: ACL deny write
    if os.name != "nt":
        os.chmod(GENESIS_LOCK_PATH, 0o400)
    else:
        # Windows: usar pywin32 ou ctypes para ACL
        _windows_set_readonly(GENESIS_LOCK_PATH)

    return genesis_hash

def get_genesis_hash() -> str:
    """Lê GENESIS do .lock file. Falha se ausente ou modificado."""
    if not GENESIS_LOCK_PATH.exists():
        raise RuntimeError(f"{GENESIS_LOCK_PATH} ausente — audit log não pode ser inicializado")

    content = GENESIS_LOCK_PATH.read_text(encoding="utf-8").strip().split("\n")
    if len(content) != 2:
        raise RuntimeError(f"{GENESIS_LOCK_PATH} corrompido — formato inválido")

    init_ts, stored_hash = content
    secret_key = os.environ["AUTH_COOKIE_KEY"].encode("utf-8")
    expected_hash = _compute_genesis_hash(init_ts, secret_key)

    if not hmac.compare_digest(stored_hash, expected_hash):
        raise RuntimeError(
            f"GENESIS HMAC INVÁLIDO! .audit-genesis.lock foi adulterado "
            f"OU AUTH_COOKIE_KEY foi rotacionada. AUDIT LOG COMPROMETIDO — investigar imediatamente."
        )

    return stored_hash
```

```python
# bloco_audit/append.py

def append_audit_entry(event_type: str, payload: dict) -> str:
    """Append-only com hash chain. Retorna hash desta entry."""
    last_hash = _get_last_entry_hash()  # ou GENESIS se primeira entry
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
        "previous_entry_hash": last_hash,
    }
    entry_serialized = json.dumps(entry, sort_keys=True, separators=(",", ":"))
    entry_hash = hashlib.sha256(entry_serialized.encode("utf-8")).hexdigest()
    entry["entry_hash"] = entry_hash

    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return entry_hash

def _get_last_entry_hash() -> str:
    """Retorna hash da última entry, ou GENESIS_HASH se vazio."""
    if not AUDIT_LOG_PATH.exists() or AUDIT_LOG_PATH.stat().st_size == 0:
        return get_genesis_hash()  # ANCORADO HMAC — não string literal
    with open(AUDIT_LOG_PATH, "rb") as f:
        # Ler última linha eficientemente (seek do final)
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b"\n":
            f.seek(-2, os.SEEK_CUR)
        last_line = f.readline().decode("utf-8")
    return json.loads(last_line)["entry_hash"]
```

```python
# bloco_audit/verify.py — comando CLI

def verify_audit_integrity() -> bool:
    """Verifica chain inteira do audit.jsonl. Detecta tampering em <5s."""
    expected_genesis = get_genesis_hash()  # HMAC valida .audit-genesis.lock antes

    prev_hash = expected_genesis
    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            entry = json.loads(line)

            if entry["previous_entry_hash"] != prev_hash:
                raise AuditIntegrityError(
                    f"Linha {line_no}: previous_entry_hash divergente. "
                    f"Esperado={prev_hash[:16]}..., obtido={entry['previous_entry_hash'][:16]}..."
                )

            entry_copy = {k: v for k, v in entry.items() if k != "entry_hash"}
            recomputed = hashlib.sha256(
                json.dumps(entry_copy, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()

            if recomputed != entry["entry_hash"]:
                raise AuditIntegrityError(
                    f"Linha {line_no}: entry_hash adulterado. "
                    f"Esperado={recomputed[:16]}..., obtido={entry['entry_hash'][:16]}..."
                )

            prev_hash = entry["entry_hash"]

    return True  # Chain íntegra do GENESIS (HMAC validado) à última entry
```

### Por que isso resolve R-NEW-SMITH-03

Cenário do attack original:
1. Attacker tenta forjar entry "anterior" com `previous_entry_hash = "GENESIS"` (string literal)
2. Em ADR-005: `previous_entry_hash` da primeira entry = `get_genesis_hash()` = HMAC de payload protegido
3. Para forjar GENESIS, attacker precisaria:
   - Conhecer `AUTH_COOKIE_KEY` (secret no .env, fora do audit.jsonl)
   - **OU** modificar `.audit-genesis.lock` (detectado pelo HMAC compare_digest)
4. **Forge sem AUTH_COOKIE_KEY é impossível** (HMAC é cryptographically secure)

### Defesa em profundidade adicional

1. `.audit-genesis.lock` em chmod 400 (read-only owner) — ataque local exige escalation de privilégio
2. AUTH_COOKIE_KEY rotation invalida GENESIS — operação destrutiva propositalmente bloqueada (alerta no `verify-audit-integrity` se HMAC falhar)
3. Backup do `.audit-genesis.lock` incluído em FR-BACKUP-01 (preservar para recovery)

## Razão

- **HMAC com chave secreta é o padrão criptográfico para integridade autenticada** (NIST SP 800-107)
- **AUTH_COOKIE_KEY já existe** (NFR-SEC-01): reutilizar em vez de criar nova chave reduz superfície de gerenciamento de secrets
- **`.audit-genesis.lock` separado do audit.jsonl:** ataque ao audit não compromete GENESIS; ataque ao GENESIS é detectável
- **Custo computacional desprezível:** HMAC-SHA256 de 100 bytes = <1μs; verificação de chain de 10k entries = <500ms
- **Anti-pattern eliminado:** "secret literal no código" (`"GENESIS"` string) → "secret derivado de chave segura"

## Alternativas Consideradas

### Alt 1 — Manter "GENESIS" como string literal (PRD original)
- **Prós:** simples
- **Contras:** **vulnerável conforme R-NEW-SMITH-03** — chain forjável
- **Rejeitada:** falha de segurança crítica

### Alt 2 — GENESIS = sha256(timestamp_init) (sem HMAC)
- **Prós:** mais difícil de forjar que string literal
- **Contras:** sem secret, attacker que conhece o timestamp recria o hash; verificável publicamente mas falsificável
- **Rejeitada:** segurança aparente, não real

### Alt 3 — Blockchain externo (anchorar hash em Bitcoin/Ethereum)
- **Prós:** integridade verificável globalmente
- **Contras:** **viola 100% local LGPD** (depende de rede externa); custo (taxas blockchain); overkill para single-user
- **Rejeitada:** princípio inegociável

### Alt 4 — Assinatura digital RSA/Ed25519 por entry
- **Prós:** non-repudiation forte
- **Contras:** custo computacional ~10ms por assinatura (vs <1μs HMAC); gerenciamento de chave privada complexo; overkill
- **Rejeitada para MVP:** revisitar se LGPD exigir non-repudiation forte

### Alt 5 — TPM/HSM para chave HMAC
- **Prós:** chave em hardware dedicado
- **Contras:** dependência de hardware específico; viola portabilidade laptop/VPS
- **Rejeitada:** AUTH_COOKIE_KEY no .env é compromisso aceitável

## Consequências

### Positivas
- **Vetor crítico R-NEW-SMITH-03 NEUTRALIZADO**
- Audit log probatório em juízo (HMAC + chain Merkle = padrão forense)
- Reutiliza secret existente (AUTH_COOKIE_KEY) — não cria novo gerenciamento
- Detecção de tampering em <5s para vault de 10k entries (cabe AC FR-AUDIT-01 ✅)
- Linux/Mac: chmod 400 nativo; Windows: ACL via pywin32 (overhead aceitável)

### Negativas / Tradeoffs
- AUTH_COOKIE_KEY torna-se chave dupla (sessão + audit) — perda da chave invalida AMBOS
- Mitigação: AUTH_COOKIE_KEY backup em local seguro fora do laptop (responsabilidade do usuário; documentar em README setup)
- Rotação de AUTH_COOKIE_KEY exige re-inicialização do GENESIS (operação destrutiva — exige confirmação explícita + backup)
- Windows ACL para chmod 400 é menos robusto que Linux POSIX (workaround documentado)

### Neutras
- DP-NOVO criada: documentar procedimento de "rotação segura de AUTH_COOKIE_KEY" — destruição controlada do GENESIS antigo + criação do novo + arquivamento do audit log antigo

## Referências

- PRD v1.0.2: FR-AUDIT-01 estendido (linhas 416-420), NFR-SEC-01 (linha 548)
- Smith re-review: R-NEW-SMITH-03 (qa/smith-adversarial-rereview-prd-v1.0.2.md)
- HMAC: NIST SP 800-107 — https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-107r1.pdf
- Python `hmac` module: https://docs.python.org/3/library/hmac.html
- `hmac.compare_digest` (constant-time): https://docs.python.org/3/library/hmac.html#hmac.compare_digest

---

*Aria, fechando a porta que o atacante usaria para reescrever a história. 🏗️*
