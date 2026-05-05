# SOP-003 — Revisão de Contrato (Fluxo Usuário Final)

> **Versão:** 1.0 · **Data:** 2026-05-04 · **Owner:** equipe operacional Revisor Contratual

---

## 1. Pré-requisitos

Antes de executar `revisor revisar`, confirme:

- [ ] **Audit chain inicializada:** `revisor init-audit` foi rodado uma vez (cria `.audit-genesis.lock`)
- [ ] **Vault populado:** `revisor populate-vault --source all` foi executado (sqlite com STJ + STF)
- [ ] **AUTH_COOKIE_KEY env definida:** `echo $AUTH_COOKIE_KEY` retorna 64 caracteres hex
- [ ] **Ollama rodando** (se quiser revisão real LLM): instâncias Sabia-7B em `127.0.0.1:11434` e Qwen 2.5 3B em `127.0.0.1:11435` — ver ADR-003 SUB-C
- [ ] **PDF do contrato** disponível localmente (NUNCA é enviado para a rede — LGPD)

Para setup inicial completo, ver [`README.md`](../README.md) seção Quickstart.

---

## 2. Comando

```
revisor revisar PDF_PATH [OPTIONS]
```

### Argumentos e flags

| Argumento/Flag | Default | Descrição |
|---|---|---|
| `PDF_PATH` (positional) | obrigatório | Caminho para o arquivo PDF do contrato |
| `--uf TEXTO` | extraído do PDF | UF do contrato (override extração regex) |
| `--data-assinatura YYYY-MM-DD` | extraído do PDF | Data assinatura (override) |
| `--tier {lean\|balanced\|premium}` | `premium` | Tier do Advogado LLM (FR-TESE-02) |
| `--vault-db PATH` | `~/.local/share/revisor-contratual/vault.db` | Caminho vault sqlite |
| `--audit-path PATH` | `~/.local/share/revisor-contratual/audit.jsonl` | Caminho audit log |
| `--bacen-cache PATH` | `~/.local/share/revisor-contratual/bacen-cache` | Cache de respostas BACEN SGS |
| `--top-k INT` | `5` | Docs do vault para personas (1-50) |
| `-h, --help` | — | Ajuda completa |

---

## 3. Casos de uso

### Caso 1 — PDF com camada de texto (path feliz)

**Sintoma:** PDF gerado por Word/InDesign/etc com texto extraível pelo PyMuPDF.

```bash
revisor revisar contratos/contrato_cdc_veiculos.pdf
# Se metadata estiver presente no markdown, sem overrides:
# → 📄 Parsing PDF (pymupdf4llm)...
# → 💰 Cálculo Decimal...
# → 📊 BACEN SGS modalidade=CDC_VEICULOS_PF mes=2024-03...
# → 🔍 Vault busca híbrida top-K=5...
# → 👨‍⚖️ Personas paralelas (asyncio.gather)...
# → ⚖️  Juiz Python puro...
# → 📝 Audit log persistido (entry_hash=a3f...)
# →
# → ✅ VEREDITO: APROVADO_100 (aderência 100.0%)
```

**O que esperar:** ~120-180s end-to-end (com Ollama real) ou ~60s (sem LLM real, smoke).

---

### Caso 2 — PDF imagem-only (precisa OCR)

**Sintoma:** PDF escaneado de papel; PyMuPDF retorna markdown vazio ou com fidelity baixa (<0.5).

```bash
revisor revisar contratos/contrato_escaneado.pdf
# → 📄 Parsing PDF (pymupdf4llm)... fidelity=0.12 (baixa)
# → ❌ Não foi possível extrair texto do PDF: contrato_escaneado.pdf
# →
# → 📋 Diagnóstico: PDF parece ser imagem escaneada (sem camada de texto extraível).
# → 🔍 Causa: parser primário (PyMuPDF) retornou conteúdo insuficiente; OCR é necessário mas Marker não está instalado.
# →
# → ✅ Solução: instale o suporte OCR:
# →    pip install revisor-contratual[ocr]
# →
# → 💡 Alternativa: se você tem o contrato em formato texto/Word, converta para PDF preservando a camada de texto antes de enviar.
```

**Ação:**

```bash
# Opção A: instalar Marker OCR (~1GB modelos)
pip install revisor-contratual[ocr]
revisor revisar contratos/contrato_escaneado.pdf

# Opção B: converter o documento original para PDF preservando texto
# (Word → PDF "Salvar como" sem "Imagem" / Google Docs → Download PDF)
```

---

### Caso 3 — PDF criptografado

**Sintoma:** PDF protegido por senha (raro em contratos bancários, mas acontece).

```bash
revisor revisar contratos/contrato_protegido.pdf
# → ❌ PDFEncrypted: PDF está protegido por senha. Descriptografe antes de revisar.
```

**Ação:**

```bash
# Descriptografar com qpdf
qpdf --decrypt --password=SENHA contrato_protegido.pdf contrato_aberto.pdf
revisor revisar contrato_aberto.pdf

# Ou usando Python (pikepdf)
python -c "
import pikepdf
with pikepdf.open('contrato_protegido.pdf', password='SENHA') as pdf:
    pdf.save('contrato_aberto.pdf')
"
```

**Nota LGPD:** descriptografe **localmente**. Nunca envie PDFs com dados pessoais a serviços online de descriptografia.

---

### Caso 4 — Metadata ausente (UF / data_assinatura)

**Sintoma:** PDF sem padrões reconhecíveis para `_extract_uf` ou `_extract_data_assinatura`.

```bash
revisor revisar contratos/contrato_layout_incomum.pdf
# → ❌ MetadataExtractionError: Campos obrigatórios não extraíveis: ['uf_contrato', 'data_assinatura']. Forneça via uf_override / data_override ou revise o PDF de origem.
```

**Ação:** use os overrides explícitos:

```bash
revisor revisar contratos/contrato_layout_incomum.pdf \
  --uf BA \
  --data-assinatura 2024-03-15
```

**Quando usar overrides:**
- Você JÁ SABE a UF e a data (atendimento direto ao cliente)
- O PDF tem layout não-padrão (banco diferente, contrato antigo)
- Você quer forçar um cenário específico para análise

UFs aceitas: 27 siglas brasileiras (`AC, AL, AM, AP, BA, CE, DF, ES, GO, MA, MG, MS, MT, PA, PB, PE, PI, PR, RJ, RN, RO, RR, RS, SC, SE, SP, TO`).

---

### Caso 5 — BACEN offline (fallback automático)

**Sintoma:** rede BACEN SGS instável ou indisponível.

```bash
revisor revisar contrato.pdf
# → 📊 BACEN SGS modalidade=CDC_VEICULOS_PF mes=2024-03...
# →   ⚠️  BACEN SGS retry exhausted após 5 tentativas
# →   ℹ️  Usando última taxa conhecida do cache (is_fallback=True)
# → ... (pipeline continua)
# → ✅ VEREDITO: APROVADO_COM_RISCO_HITL (aderência 83.3%)
# →   ⚠️  Usado fallback BACEN — verificar atualidade
```

**O que acontece:** `BacenClient` faz 5 retries com backoff exponencial (1→2→4→8→16s). Se todas falharem, usa última taxa conhecida do `bacen-cache/`. O resultado é marcado `is_fallback=True` na auditoria.

**Quando isso é problema:**
- Se o cache nunca foi populado (primeiro uso): `BacenFetchExhausted` levanta (não há fallback)
- Se a divergência BACEN é o critério C1 que você precisa, considere refazer quando online

---

### Caso 6 — Vault vazio

**Sintoma:** rodou `revisor revisar` sem `populate-vault` antes.

```bash
revisor revisar contrato.pdf
# → 🔍 Vault busca híbrida top-K=5...
# → ❌ VaultEmptyError: vault sem documentos. Rode `revisor populate-vault --source all` primeiro.
```

**Ação:**

```bash
revisor populate-vault --source all
# → ✅ Total persistidos: 122 items

revisor revisar contrato.pdf  # agora funciona
```

Detalhes em [SOP-002 populate-vault](sop-populate-vault.md).

---

## 4. Interpretação do veredito (ADR-003 thresholds)

O Juiz Python puro (não-LLM, reprodutível) emite um dos 3 vereditos baseado em `aderencia = (C1 + C2 + C3) / 3 * 100`:

| Aderência | Veredito | Significado | Próxima ação |
|-----------|----------|-------------|--------------|
| **= 100%** | `APROVADO_100` | Todos os 3 critérios passaram com score 1.0 — caso forte para protocolar | Tela CFOAB → emitir petição (FR-DELIV-06) |
| **70 ≤ x < 100** | `APROVADO_COM_RISCO_HITL` | Caso plausível mas com fragilidades; **revisão humana obrigatória** antes de protocolar | Painel HITL → advogado decide |
| **< 70** | `REJEITADO` | Caso fraco para protocolar — emitir Relatório de Inviabilidade ao cliente | NUNCA emitir petição automática |

### Os 3 critérios C1/C2/C3 (FR-JUIZ-01)

| Critério | O que mede | Score 1.0 quando |
|----------|-----------|------------------|
| **C1** | Divergência BACEN ≥0.5pp entre taxa contratual e taxa média BACEN | Divergência ≥ 0.5 pontos percentuais |
| **C2** | `max(peso_vinculacao)` dos fundamentos invocados ≥4 | Pelo menos 1 fundamento STJ binding (peso 4) ou STF SV (peso 5) |
| **C3** | ≥1 doc da jurisdição do contrato (matching UF) | Vault tem TJ{UF} OU TJ{UF}=∅ aceitável (graceful) |

**Reprodutibilidade:** o Juiz é Python puro com `field_validator` que rejeita `aderencia` divergente da média (`abs(declarada - esperada) > 0.1`). Se o Juiz retorna, o número é **auditável e reproduzível** — não tem aleatoriedade LLM.

### Razões emitidas

`VeredictoJuiz.razoes` é uma lista de strings explicando os scores. Exemplo:

```
razoes:
  - "C1 PASS: divergência BACEN 1.85pp > threshold 0.5pp"
  - "C2 PASS: STF-SV4 binding (peso 5) >= 4"
  - "C3 PASS: 2 docs TJBA encontrados (jurisdição match)"
```

---

## 5. Inspecionando o audit trail

Cada execução de `revisor revisar` gera uma entry no audit log forense.

### Localização default

```
~/.local/share/revisor-contratual/audit.jsonl
```

### Estrutura de cada entry

```json
{
  "ts": "2026-05-04T17:32:15.123456+00:00",
  "operation": "revisar_contrato",
  "actor": "cli:eric",
  "payload_hash": "a3f2b1c8...",
  "previous": "f9e8d7c6...",
  "entry_hash": "b4d5e6f7...",
  "metadata": {
    "contract_hash": "a1b2c3...",
    "veredito": "APROVADO_COM_RISCO_HITL",
    "aderencia": 83.3,
    "modalidade": "CDC_VEICULOS_PF",
    "uf_contrato": "BA",
    "tier_advogado": "premium",
    "duration_ms": 142531
  }
}
```

### Verificando integridade

```python
from pathlib import Path
from bloco_audit.chain import verify_audit_integrity

DATA_DIR = Path.home() / ".local" / "share" / "revisor-contratual"
verify_audit_integrity(
    audit_path=DATA_DIR / "audit.jsonl",
    genesis_lock_path=DATA_DIR / ".audit-genesis.lock",
)
print("✅ Chain íntegra")
```

Se levantar `AuditIntegrityError` ou `GenesisLockTampered`: investigação imediata. **NUNCA** rotacione AUTH_COOKIE_KEY antes de investigar (ver SOP-001 Passo 2).

### Casos de FAILED no audit

Pipeline que levanta exceção registra entry `status=FAILED` ANTES de propagar (atomicidade D-NEO-4.0-D). Útil para debugar em produção sem rodar de novo.

---

## 6. Privacidade LGPD

### Promessas do sistema

| Aspecto | Garantia | Onde enforçada |
|---------|----------|----------------|
| **PDF nunca sai da máquina** | Parsing 100% local (PyMuPDF + Marker opcional) | Não há upload — código não tem chamada HTTP de PDF |
| **Dados extraídos do PDF nunca saem** | Markdown, metadata, valores ficam locais | Cálculo Decimal local; LLM bate Ollama em `127.0.0.1` (loopback) |
| **Apenas STJ e STF são consultados na rede** | Whitelist hardcoded `frozenset({"www.stj.jus.br", "www.stf.jus.br"})` | `bloco_vault/scrapers/base.py:13` + `assert_host_allowed` antes de cada request |
| **BACEN consulta apenas taxas agregadas** | API SGS retorna estatística pública (taxa média mensal); **NÃO envia dados do contrato** | `bloco_engine/bacen/client.py` — fetcher só passa `sgs_code` (número público) |
| **Audit log fica local** | `audit.jsonl` em `~/.local/share/...` — nenhuma sincronização externa | Sem código de upload/sync |

### Confirmação por usuário

Se você quiser verificar empiricamente:

```bash
# Monitorar conexões durante revisão
sudo netstat -tnp | grep python
# Esperado: SOMENTE conexões a www.stj.jus.br, www.stf.jus.br, api.bcb.gov.br, 127.0.0.1 (Ollama)
```

Qualquer conexão a outro host **viola NFR-LGPD-01** e é bug crítico.

---

## 7. Anti-patterns

| Anti-pattern | Por que evitar |
|--------------|---------------|
| ❌ Enviar PDF para serviço online de OCR (Adobe, ilovepdf) | Vaza dados do cliente — viola LGPD |
| ❌ Compartilhar `audit.jsonl` por Slack/email sem redação | Pode conter contract_hash + metadata sensível |
| ❌ Usar Ollama hospedado em nuvem pública | Quebra promessa "PDF/dados nunca saem" — mantenha Ollama local |
| ❌ Modificar `audit.jsonl` manualmente | HMAC chain quebra — auditoria forense invalidada |
| ❌ Rodar `revisar` sem `init-audit` | Pipeline levanta `GenesisLockMissing` — sempre rode `init-audit` no setup |
| ❌ Confiar em `APROVADO_100` sem revisão humana em casos de alto valor | O sistema é **assistente**, não substituto da OAB; tela CFOAB existe por isso |

---

## 8. Roadmap pós-MVP (referência)

Funcionalidades planejadas mas NÃO no v0.1.0:

- UI Streamlit (CLI MVP only)
- Smoke E2E real automatizado (STORY 15)
- Scrapers TJBA / TJSP / TJMG / TJRJ / TJRS (whitelist requer ADR)
- Modalidades além de CDC_VEICULOS_PF (CDC_BENS_PF, CDC_IMOBILIARIO, CARTAO_ROTATIVO já modelados; lógica de cálculo em STORIES futuras)
- Bloco_learning ativo (outcomes.db + ML feedback loop)

---

## 9. Referências técnicas

- `bloco_interface/cli.py:71-152` — comando `revisar` (Click)
- `bloco_workflow/pipeline.py:revisar_contrato` — orquestração 7 steps
- `bloco_engine/parsing/orchestrator.py:parse_contract` — PyMuPDF → Marker fallback
- `bloco_workflow/personas/juiz.py` — Juiz Python puro (FR-JUIZ-01..03)
- `bloco_audit/chain.py:append_audit_entry` — HMAC chain forense
- ADR-003 PATCH SUB-C — LLM Strategy (Sabia-7B + Qwen 3B paralelo)
- ADR-005 — HMAC GENESIS audit chain

---

*SOP-003 v1.0 — Revisão de Contrato (Fluxo Usuário Final) · STORY 14 · Sessão 76 · Neo (@dev)*
