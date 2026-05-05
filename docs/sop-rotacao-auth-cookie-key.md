# SOP-001 — Rotação de AUTH_COOKIE_KEY

> **Versão:** 1.0 · **Data:** 2026-05-04 · **Owner:** equipe operacional Revisor Contratual
> **Endereça:** referência em `bloco_audit/genesis.py:123` ("Para rotação segura: ver docs/sop-rotacao-auth-cookie-key.md")

---

## 1. Por quê rotacionar

`AUTH_COOKIE_KEY` é a chave secreta de 32 bytes (256 bits) que assina o GENESIS hash do audit chain via HMAC-SHA256. Comprometimento dessa chave permitiria a um atacante forjar entradas no audit log.

Cenários que **exigem** rotação:

| Cenário | Severidade | Prazo |
|---------|-----------|-------|
| Suspeita de vazamento da chave (logs expostos, env dump, repositório público) | CRÍTICO | imediato |
| Saída de membro com acesso à chave (encerramento de contrato, demissão) | ALTO | 24-48h |
| Política de rotação periódica (compliance) | MÉDIO | trimestral ou semestral |
| Migração entre máquinas físicas | BAIXO | janela de manutenção |

**Não rotacione preventivamente sem necessidade.** A rotação invalida o audit log antigo (que vira read-only histórico) e exige nova GENESIS chain — operação não reversível.

---

## 2. Pré-requisitos

Antes de iniciar a rotação, confirme:

- [ ] Audit log atual está **íntegro** (rodar `verify_audit_integrity` retorna chain válida)
- [ ] Backup completo de `~/.local/share/revisor-contratual/` foi feito e validado
- [ ] Janela de manutenção acordada (pipeline `revisor revisar` ficará indisponível durante a rotação)
- [ ] Acesso ao env do processo que consome `AUTH_COOKIE_KEY` (terminal, .bashrc, systemd service, etc.)
- [ ] `openssl` instalado (`openssl version` retorna sem erro)

---

## 3. Procedimento (7 passos)

### Passo 1 — Backup do estado atual

```bash
# Diretório default: ~/.local/share/revisor-contratual/
cd ~/.local/share

# Backup com timestamp
cp -r revisor-contratual revisor-contratual.backup-$(date +%Y%m%d-%H%M%S)

# Verificar tamanho do backup é coerente
du -sh revisor-contratual.backup-*
```

### Passo 2 — Verificar integridade da chain ANTES de rotacionar

A chain DEVE estar íntegra antes da rotação. Se houver tampering, **NÃO PROSSEGUIR** — investigue primeiro.

```python
# Script de verificação (até existir comando CLI dedicado)
from pathlib import Path
from bloco_audit.chain import verify_audit_integrity
from bloco_audit.genesis import get_genesis_hash

DATA_DIR = Path.home() / ".local" / "share" / "revisor-contratual"
audit_path = DATA_DIR / "audit.jsonl"
genesis_lock = DATA_DIR / ".audit-genesis.lock"

# Validar GENESIS HMAC com chave atual
genesis_hash = get_genesis_hash(lock_path=genesis_lock)
print(f"GENESIS hash: {genesis_hash[:32]}...")

# Validar chain completa
verify_audit_integrity(audit_path=audit_path, genesis_lock_path=genesis_lock)
print("✅ Chain íntegra — pode rotacionar")
```

**Se levantar `GenesisLockTampered` ou `AuditIntegrityError`:** PARE. A chain está comprometida — investigue antes de rotacionar (a rotação esconderia o tampering).

### Passo 3 — Gerar nova chave

```bash
# Linux/Mac
NEW_KEY=$(openssl rand -hex 32)
echo "Nova chave gerada (não compartilhe): ${NEW_KEY:0:8}..."

# Windows PowerShell
$NEW_KEY = -join ((1..64) | ForEach-Object { '{0:X}' -f (Get-Random -Max 16) })
Write-Host "Nova chave: $($NEW_KEY.Substring(0, 8))..."
```

A chave DEVE ter 64 caracteres hexadecimais (32 bytes). **Nunca** reutilize uma chave anterior.

### Passo 4 — Rotação atômica (NOVO audit dir, NÃO sobrescrever antigo)

Crie um diretório separado para o NOVO audit chain. **Nunca** sobrescreva o lock antigo.

```bash
# Criar novo dir com timestamp
NEW_DIR=~/.local/share/revisor-contratual-rotacao-$(date +%Y%m%d)
mkdir -p $NEW_DIR

# Inicializar GENESIS no novo dir com a nova chave
AUTH_COOKIE_KEY=$NEW_KEY revisor init-audit --lock-path $NEW_DIR/.audit-genesis.lock
# → ✅ GENESIS inicializado em <NEW_DIR>/.audit-genesis.lock
# → Hash: <novo-hash>...
```

### Passo 5 — NUNCA sobrescrever lock antigo

O audit log antigo (`audit.jsonl` + `.audit-genesis.lock` originais) torna-se **read-only por design**. Eles permanecem como **registro forense histórico** assinado pela chave anterior.

```bash
# Marcar como read-only explicitamente (POSIX)
chmod 400 ~/.local/share/revisor-contratual/.audit-genesis.lock
chmod 400 ~/.local/share/revisor-contratual/audit.jsonl

# Documentar a rotação em README inline
cat > ~/.local/share/revisor-contratual/ROTATED-$(date +%Y%m%d).txt <<EOF
Audit chain rotacionada em $(date -Iseconds).
Motivo: <preencher: compromise / política / saída-membro>
Chain antiga (este dir) é read-only histórica.
Chain nova: $NEW_DIR
Operador: $(whoami)
EOF
```

### Passo 6 — Atualizar AUTH_COOKIE_KEY env + restart

Atualize o env do processo e o vault/path para apontar para o novo dir.

```bash
# Linux/Mac — atualizar .bashrc / .zshrc
sed -i.bak "s/^export AUTH_COOKIE_KEY=.*/export AUTH_COOKIE_KEY=$NEW_KEY/" ~/.bashrc
sed -i.bak "s|XDG_DATA_HOME.*revisor-contratual|XDG_DATA_HOME=$NEW_DIR|" ~/.bashrc 2>/dev/null || true

# Recarregar
source ~/.bashrc

# Verificar
echo $AUTH_COOKIE_KEY | head -c 8 && echo "..."

# Systemd service (se aplicável)
sudo systemctl daemon-reload
sudo systemctl restart revisor-contratual
```

### Passo 7 — Validar nova chain com primeiro append teste

Confirme que a nova chain aceita appends antes de declarar a rotação concluída.

```bash
# Comando smoke (assumindo vault já populado no novo dir, OU populate primeiro)
revisor populate-vault --vault-db $NEW_DIR/vault.db --source stj --dry-run

# Revisão smoke com PDF de teste (se disponível)
revisor revisar tests/fixtures/contrato_minimo.pdf \
  --audit-path $NEW_DIR/audit.jsonl \
  --vault-db $NEW_DIR/vault.db \
  --uf BA --data-assinatura 2024-03-15

# Verificar que audit.jsonl novo tem entrada
tail -1 $NEW_DIR/audit.jsonl
```

Se o append falhar com `GenesisLockMissing` ou `GenesisLockTampered`, a rotação **não foi concluída** — siga o Recovery Checklist abaixo.

---

## 4. Recovery Checklist (se rotação interromper)

Se algo der errado durante a rotação:

| Sintoma | Ação |
|---------|------|
| Passo 4 falha (`GenesisAlreadyInitialized` no NEW_DIR) | Limpe `$NEW_DIR/.audit-genesis.lock` e refaça (NEW_DIR deve estar limpo) |
| Passo 6 — env não atualizou | `echo $AUTH_COOKIE_KEY` deve retornar nova chave; se não, reabra terminal ou `exec $SHELL` |
| Passo 7 falha com `GenesisLockTampered` | A chain nova foi assinada com chave diferente da que está no env. Verifique que `AUTH_COOKIE_KEY` no env = chave usada no Passo 4 |
| Processo em produção continua usando chave antiga | Confirme restart de TODOS os processos (systemd, supervisor, container) |
| Backup do Passo 1 perdido | A chain antiga ainda está no dir original (você NÃO sobrescreveu, conforme Passo 5). Recovery: restaurar `AUTH_COOKIE_KEY=<chave-antiga>` no env. NÃO continue com a nova chain até que backup seja refeito |

**Rollback (se rotação foi prematura):**

1. Restaure `AUTH_COOKIE_KEY` para a chave antiga no env
2. Aponte vault/audit paths de volta para o dir original
3. Restart processos
4. Verifique chain antiga com `verify_audit_integrity` — deve estar íntegra
5. Documente o rollback (motivo) e marque o NEW_DIR como `ABORTED-<timestamp>`

---

## 5. Anti-patterns (NÃO fazer)

| Anti-pattern | Por que é perigoso |
|--------------|-------------------|
| ❌ Renomear `.audit-genesis.lock` antigo | Quebra rastreabilidade forense; o lock antigo deve permanecer no lugar como histórico |
| ❌ Concatenar audit.jsonl novo com antigo | Chain HMAC quebra (entry.previous referencia hash com chave diferente); auditoria invalidada |
| ❌ `init-audit` no MESMO dir do antigo (sobrescrever) | `GenesisAlreadyInitialized` por design; tentativa de bypass = comprometimento da auditabilidade |
| ❌ Usar a mesma chave antiga "rotacionada" | Não é rotação, é não-operação; risco original permanece |
| ❌ Rotacionar sem backup do Passo 1 | Se algo falhar, recovery é impossível |
| ❌ Compartilhar AUTH_COOKIE_KEY em plain text (Slack, email, ticket) | Vazamento imediato — gera necessidade de nova rotação |
| ❌ Pular Passo 2 (verificação de integridade ANTES) | Pode estar rotacionando uma chain já tampered, escondendo o ataque |

---

## 6. Frequência recomendada

| Contexto | Frequência sugerida |
|----------|---------------------|
| Solo dev / desenvolvimento | Apenas em compromise; sem rotação periódica |
| Equipe pequena (2-5 pessoas) | Trimestral OU em cada saída de membro |
| Compliance LGPD / SOC2 | Conforme política da organização (tipicamente trimestral) |
| Pós-incidente de segurança | Imediato + revisão de toda a infraestrutura |

---

## 7. Rastreabilidade da rotação

Toda rotação DEVE ser registrada em log fora do audit chain (porque o audit chain antigo não pode ser modificado e o novo ainda não tem essa entrada). Sugestão: `~/.local/share/revisor-contratual/ROTATIONS.md`.

```markdown
# Histórico de Rotações AUTH_COOKIE_KEY

## 2026-05-04 14:32 UTC
- **Motivo:** política trimestral
- **Operador:** eric@claudinoinsights.com
- **Chain antiga:** `~/.local/share/revisor-contratual/` (read-only)
- **Chain nova:** `~/.local/share/revisor-contratual-rotacao-20260504/`
- **Verificação pré-rotação:** PASS (chain íntegra)
- **Smoke pós-rotação:** PASS (1 entry teste)

## 2026-02-01 09:15 UTC
...
```

---

## 8. Referências técnicas

- `bloco_audit/genesis.py:99-139` — `initialize_audit_genesis()` (cria GENESIS lock + chmod 400 POSIX)
- `bloco_audit/genesis.py:147-191` — `get_genesis_hash()` (valida HMAC com `AUTH_COOKIE_KEY`)
- `bloco_audit/chain.py:33` — `AuditIntegrityError` (levantada se chain quebrada)
- ADR-005 — decisão arquitetural sobre HMAC GENESIS chain ([governance/architecture/adr/](../governance/architecture/adr/))

---

*SOP-001 v1.0 — Rotação de AUTH_COOKIE_KEY · STORY 14 · Sessão 76 · Neo (@dev)*
