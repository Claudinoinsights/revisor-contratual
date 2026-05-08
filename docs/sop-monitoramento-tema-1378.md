# SOP-005 — Verificação Manual Semanal Tema 1378 STJ

> **Versão:** 1.0 · **Data:** 2026-05-05 · **Owner:** maintainer Revisor Contratual
> **Reference:** PRD v1.1.2 §2.2 (F-NEW-02 fallback) · FR-MONITOR-01 (PRD v1.1.1+)

---

## 1. Razão

FR-MONITOR-01 (Camada 1) é job semanal automático que faz scrape de `https://www.stj.jus.br/repetitivos/temas-repetitivos` para detectar julgamento do Tema 1378 STJ (critério de abusividade em contrato bancário).

**Limitação Camada 1:** STJ scraper já demonstrou-se frágil per ADR-012 (WAF intermitente + parser vulnerável a mudanças HTML). Job auto pode falhar 7+ dias consecutivos sem detecção, deixando hole regulatório (advogados emitindo petições com tese desatualizada após Tema 1378 julgado).

**Solução SOP-005 (Camada 2):** maintainer verifica manualmente quando trigger dispara.

---

## 2. Trigger (quando executar)

Executar verificação manual quando ocorrer **qualquer** dos seguintes:

| Trigger | Frequência | Como detectar |
|---|---|---|
| **A1** FR-MONITOR-01 falha 7+ dias consecutivos | imediato | log `audit.jsonl` com event `monitor_failed` em ≥7 dias seguidos |
| **A2** Reminder trimestral PROJECT-CHECKPOINT | trimestral | reminder em `governance/PROJECT-CHECKPOINT.md` (data próxima trimestral) |
| **A3** Notícia jurídica menciona Tema 1378 | sob demanda | maintainer ou advogado-usuário recebe notícia (Migalhas, ConJur, JusBrasil) |
| **A4** Suspeita de scraper quebrado | sob demanda | banner UI ATIVO há 7+ dias (deveria ter sido emitido ou desativado) |

---

## 3. Procedimento manual (15-30 minutos)

### Passo 1 — Acesso à fonte oficial STJ

Maintainer acessa via browser:
- **URL primária:** https://www.stj.jus.br/repetitivos/temas-repetitivos
- **URL backup:** https://processo.stj.jus.br/repetitivos/temasRepetitivos.jsp
- **URL fallback Migalhas:** https://www.migalhas.com.br/depeso/440203/repetitivo-do-stj-e-criterio-de-abusividade-em-contrato-bancario

### Passo 2 — Busca e identificação

Buscar na página por palavras-chave: `1378`, `abusividade contrato bancário`, `critério circunstancial`.

Verificar **status atual do Tema 1378:**

| Status | Como reconhecer | Ação subsequente |
|---|---|---|
| **EM JULGAMENTO** | "Em julgamento" / "Pendente julgamento" / sessão marcada para data futura | Documentar status; nenhuma ação adicional necessária |
| **JULGADO — TESE FIRMADA** | "Tese fixada em sessão de DD/MM/YYYY" + texto da tese disponível | **CRÍTICO** — executar Passo 3+4 |
| **SUSPENSO** | "Suspenso" / "Sobrestado" | Documentar status; aguardar reativação |
| **ARQUIVADO** | "Arquivado" / "Cancelado" | **CRÍTICO** — Tema desfeito; remover banner UI; atualizar audit log |

### Passo 3 — Trigger CRITICAL_ALERT manual (se julgado/arquivado)

Maintainer executa CLI:

```bash
# Tema julgado com tese firmada:
revisor monitor-tema --manual-trigger 1378 --status julgado --tese-text "{texto da tese fixada copy-paste do STJ}" --data-julgamento 2026-MM-DD

# Tema arquivado:
revisor monitor-tema --manual-trigger 1378 --status arquivado --data-arquivamento 2026-MM-DD
```

Comportamento esperado do CLI:
1. Append CRITICAL_JURIS_CHANGE em `audit.jsonl` com payload `{"tema": "1378", "tribunal": "STJ", "status": "...", "detected_at": "...", "manual_trigger": true, "operator": "maintainer", "source_url": "..."}`
2. Setar flag persistente em `~/.local/share/revisor-contratual/.tema-1378-status.json` (lido pela UI no próximo login)
3. Banner vermelho persistente no UI startup do app: "ATENÇÃO: Tema 1378 STJ julgado em DD/MM/YYYY — pause de novas gerações até maintainer atualizar vault"
4. Email para `AUTH_USERNAME` se SMTP configurado

### Passo 4 — Atualizar vault com nova jurisprudência (se julgado)

Maintainer copia texto da tese fixada do STJ → cria entry JSON manual:

```bash
# Editar bloco_vault/data/sumulas-stj.json adicionando entry Tema 1378:
{
  "numero": "Tema-1378",
  "texto": "{texto exato da tese fixada do STJ}",
  "data_aprovacao": "YYYY-MM-DD",
  "revogada": false,
  "area": "civil",
  "fonte_url": "https://www.stj.jus.br/repetitivos/temas-repetitivos",
  "fetched_at": "2026-MM-DDTHH:MM:SSZ",
  "hash_sha256": "{computed via hashlib.sha256(texto)}"
}

# Validar:
revisor validate-dataset bloco_vault/data/sumulas-stj.json

# Re-popular vault (force):
revisor populate-vault --vault-db ~/.local/share/revisor-contratual/vault.db --source stj --force
```

### Passo 5 — Reativar pipeline + ack banner

Após vault atualizado + validação OK:

```bash
# Reset banner UI (acknowledge maintainer endereçou):
revisor monitor-tema --acknowledge 1378
```

Banner vermelho desaparece; pipeline volta ao normal.

---

## 4. Audit trail (registro obrigatório)

Cada execução SOP-005 DEVE produzir:

1. Entry `audit.jsonl` com `event_type: "manual_monitor_check"`, payload incluindo: tema_id, status detectado, data verificação, operator, source_url, action_taken
2. Atualização `governance/PROJECT-CHECKPOINT.md` na seção "Decisoes Tomadas" + data próxima verificação trimestral

**Exemplo entry audit:**

```json
{
  "ts": "2026-08-15T14:30:00Z",
  "event_type": "manual_monitor_check",
  "tema_id": "1378",
  "tribunal": "STJ",
  "status_detectado": "em_julgamento",
  "data_verificacao": "2026-08-15",
  "operator": "maintainer (Eric)",
  "source_url": "https://www.stj.jus.br/repetitivos/temas-repetitivos",
  "trigger_motivo": "reminder_trimestral",
  "action_taken": "documentar status; nenhuma acao adicional",
  "next_check_due": "2026-11-15"
}
```

---

## 5. Cross-references

- **PRD v1.1.2 §2.2:** F-NEW-02 fallback maintainer manual
- **FR-MONITOR-01** (PRD v1.1.1 §7.10): Camada 1 automática
- **R-NEW-OAB-CHECKSUM** (PRD v1.1.2 §13): risco aceito MVP
- **PROJECT-CHECKPOINT.md:** trimestral reminder
- **ADR-012:** Vault Data Bundling (motivação da fragilidade do scraper STJ)
- **bloco_vault/data/sumulas-stj.json:** vault bundled (entry Tema-1378 a adicionar manualmente após julgamento)

---

## 6. Trigger reminder PROJECT-CHECKPOINT

Adicionar em `governance/PROJECT-CHECKPOINT.md` na seção "Próximos Passos":

```markdown
- [ ] **SOP-005 trimestral:** Verificação manual Tema 1378 STJ — próxima data: {YYYY-MM-DD trimestral}
```

Incrementar trimestre a cada execução (após Tema julgado/arquivado, remover reminder).

---

*SOP-005 — Maintainer documentation per PRD v1.1.2 + FR-MONITOR-01 fallback (Sprint 03 course-correction CC.1A'')*
