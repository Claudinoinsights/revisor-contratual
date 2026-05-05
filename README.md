# Revisor Contratual

> Sistema LEAN local de revisão jurídica de contratos bancários (CDC PF Veículos / TJBA — MVP).

## Visão (uma frase)

Sistema agentic 100% local que analisa contratos de financiamento bancário e produz, em ≤210s por contrato, teses jurídicas + contábeis + fiscais com peticionamento e recursos prontos para protocolo, fundamentados em jurisprudência vinculante do STF, STJ e TJ da jurisdição do contrato.

## Estado — v0.1.0 MVP completo

- ✅ **15 stories Done** (Sprint 01 completo) com 15/15 PASS Oracle
- ✅ **233 testes** (232 passed + 1 skipped intencional smoke sem Ollama) — local e CI verdes
- ✅ **CLI funcional** com 3 subcomandos (`revisar`, `init-audit`, `populate-vault`)
- ✅ **CI GitHub Actions** verde Python 3.11 + 3.12 ([`.github/workflows/ci.yml`](.github/workflows/ci.yml))
- 🚀 **Release:** v0.1.0
- 📦 **Governance:** PRD v1.0.2 + 9 ADRs + 16 QA gates + TECH-DEBT.md em [`governance/`](governance/)
- 🌱 **Origem:** extraído de `Claudinoinsights/the-matrix` em 2026-05-05 (Sprint 01 closure)

## Quickstart (5 minutos)

### 1. Instalação

```bash
# Clone + modo desenvolvedor
git clone https://github.com/Claudinoinsights/revisor-contratual.git
cd revisor-contratual
pip install -e ".[dev]"

# Verificar instalação
revisor --version
# → revisor, version 0.1.0
```

### 2. Configurar AUTH_COOKIE_KEY (obrigatório)

```bash
# Gerar chave de 32 bytes (hexadecimal)
export AUTH_COOKIE_KEY=$(openssl rand -hex 32)

# Persistir (Linux/Mac)
echo "export AUTH_COOKIE_KEY=$AUTH_COOKIE_KEY" >> ~/.bashrc

# Windows PowerShell
$env:AUTH_COOKIE_KEY = -join ((1..64) | ForEach-Object { '{0:X}' -f (Get-Random -Max 16) })
```

> **Importante:** `AUTH_COOKIE_KEY` assina o GENESIS audit chain (HMAC). Para rotação segura, ver [`docs/sop-rotacao-auth-cookie-key.md`](docs/sop-rotacao-auth-cookie-key.md).

### 3. Inicializar audit chain (1× no setup)

```bash
revisor init-audit
# → ✅ GENESIS inicializado em ~/.local/share/revisor-contratual/.audit-genesis.lock
# → Hash: 7f3a1b2c4d5e6f...
```

### 4. Popular vault jurisprudencial

```bash
revisor populate-vault --source all
# → ℹ️  Scrapeando STJ...
# →   STJ: 64 items extraídos
# → ℹ️  Scrapeando STF...
# →   STF: 58 items extraídos
# → ✅ Total persistidos: 122 items
```

> **Detalhes:** ver [`docs/sop-populate-vault.md`](docs/sop-populate-vault.md) para fontes, flags e troubleshooting.

### 5. Revisar contrato

```bash
revisor revisar contrato.pdf --uf BA --data-assinatura 2024-03-15
# → 📄 Parsing PDF...
# → 💰 Cálculo Decimal (Price + simples)...
# → 📊 BACEN SGS...
# → 🔍 Vault busca híbrida (BM25 + vetorial)...
# → 👨‍⚖️ Personas paralelas (Advogado Sabia-7B + Economista Qwen 3B)...
# → ⚖️  Juiz Python puro (C1/C2/C3)...
# → 📝 Audit log persistido
# →
# → ✅ VEREDITO: APROVADO_COM_RISCO_HITL (aderência 83.3%)
# →   C1 (BACEN divergência): 1.00
# →   C2 (max peso vinculação): 0.50
# →   C3 (jurisdição): 1.00
```

> **Casos de uso completos:** ver [`docs/sop-revisar-pdf.md`](docs/sop-revisar-pdf.md) para PDFs criptografados, OCR, metadata ausente, BACEN offline, etc.

### 6. (Opcional) UI Streamlit local

```bash
streamlit run bloco_interface/streamlit_app.py
# Abre: http://localhost:8501
# Design system orsheva-brandbook aplicado via tokens CSS
```

> 🚧 **Streamlit UI v0.1.0 é skeleton** — invocação real do pipeline será implementada na STORY UI-1 do Sprint 02. Por agora roda em modo demo (mock veredito). CLI é canônica para uso real.

## Landing institucional

`landing/` contém página estática para deploy em `claudinoinsights.com/revisor-contratual`. NÃO processa dados — apenas marketing + download. Preserva NFR-LGPD-01.

```bash
# Preview local
cd landing && python -m http.server 8080
# Abrir: http://localhost:8080
```

Deploy via Cloudflare Pages — ver [`landing/README.md`](landing/README.md).

## Arquitetura D-LEAN

```
revisor-contratual/
├── pyproject.toml
├── README.md (este)
├── docs/                    ← SOPs operacionais
│   ├── sop-rotacao-auth-cookie-key.md
│   ├── sop-populate-vault.md
│   └── sop-revisar-pdf.md
├── bloco_contratos/         ← Pydantic models compartilhados (extra='forbid' nos schemas LLM-facing)
├── bloco_interface/         ← CLI Click (3 subcomandos)
├── bloco_workflow/          ← Pipeline async + personas/
│   └── personas/            ← Advogado/Economista/Juiz (ADR-003 SUB-C)
├── bloco_vault/             ← sqlite-vec + scrapers STJ/STF (NFR-LGPD-01)
├── bloco_engine/            ← parsing + cálculo + BACEN
│   └── ferramentas_calculo/ ← Decimal everywhere (FR-CALC-01)
├── bloco_audit/             ← audit.jsonl + HMAC GENESIS chain (ADR-005)
├── bloco_learning/          ← outcomes.db + ML feedback loop (futuro)
└── tests/
    ├── unit/                ← testes unitários
    ├── integration/         ← pipeline E2E (10 testes)
    └── smoke/               ← validações operacionais (paralelismo LLM)
```

## LLM Strategy (ADR-003 PATCH SUB-C + PATCH 2)

Fan-out paralelo via `asyncio.gather` em **2 instâncias Ollama distintas**:

- **Advogado** — Sabia-7B Tier configurável (`OLLAMA_HOST_ADVOGADO=127.0.0.1:11434`)
- **Economista** — Qwen 2.5 3B FIXO (`OLLAMA_HOST_ECONOMISTA=127.0.0.1:11435`)

**Footprint:** ~7GB RAM. **Latência:** max(advogado, economista) ≈ 90s paralelo.

**Validação obrigatória pré-release:** rodar `pytest tests/smoke/test_paralelismo_llm.py` — ratio asyncio.gather vs sequencial DEVE ser <0.7. Se falhar, paralelismo é placebo (debug `OLLAMA_HOST` distintos OU `langchain-ollama>=0.2.0`).

## Princípios não-negociáveis

| Princípio | Onde se aplica |
|-----------|---------------|
| 100% local LGPD (whitelist HTTP estrita STJ+STF) | NFR-LGPD-01 + CI gate |
| Decimal everywhere — float PROIBIDO em finanças jurídicas | FR-CALC-01 + CI lint |
| Citation-grounded com validação semântica NLI híbrida | FR-TESE-04 + ADR-004 |
| Audit log forense-grade (HMAC GENESIS chain) | FR-AUDIT-01 + ADR-005 |
| Pydantic strict (`extra='forbid'`) nos schemas LLM-facing | F-LLM-MED-01 hardening (Phase 4 #1) |
| WCAG 2.1 AA + Lighthouse ≥90 | NFR-A11Y-01 (futuro UI) |
| Tela CFOAB obrigatória antes de PDF (Estatuto OAB art. 32) | FR-DELIV-06 |

## Limitações conhecidas (v0.1.0)

| Limitação | Workaround | Endereçada em |
|-----------|------------|---------------|
| Marker OCR é opt-in (não vem instalado) | `pip install revisor-contratual[ocr]` para PDFs imagem-only | SOP-003 caso 2 |
| Modelos Ollama (Sabia-7B + Qwen 3B) NÃO inclusos | Instalar Ollama externo + `ollama pull` | Setup futuro |
| sentence-transformers (~500MB) é opt-in | populate-vault default `--zero-embeddings=True` (busca lexical funciona; vetorial degraded) | SOP-002 |
| BACEN python-bcb >=0.3 (PyPI max real) | Pin aspiracional >=0.5 corrigido em STORY 12 | CI Linux validou |
| UI Streamlit ainda não implementada (CLI MVP only) | Use `revisor revisar` direto na CLI | Roadmap pós-MVP |

## Comandos CLI

```bash
revisor --help                              # ajuda geral
revisor revisar --help                      # ajuda do subcomando
revisor revisar contrato.pdf [--uf BA --data-assinatura 2024-03-15 --tier {lean|balanced|premium} --top-k 5]
revisor init-audit [--lock-path ~/.local/share/revisor-contratual/.audit-genesis.lock]
revisor populate-vault [--source {stj|stf|all} --dry-run --zero-embeddings]
```

Defaults persistentes em `~/.local/share/revisor-contratual/`:
- `vault.db` — sqlite-vec database
- `audit.jsonl` — audit log forense
- `.audit-genesis.lock` — GENESIS hash HMAC
- `bacen-cache/` — diskcache de respostas BACEN SGS

## Testes

```bash
# Suite completa (local — sem Ollama)
python -m pytest tests/ -o addopts="" --tb=short
# → 232 passed, 1 skipped, 0 failed em ~62s

# Subset rápido (apenas unit)
python -m pytest tests/unit/ -o addopts="" -v

# Smoke paralelismo (requer Ollama+modelos rodando)
python -m pytest tests/smoke/ -o addopts="" -v
```

CI GitHub Actions roda Python 3.11 + 3.12 em push/PR para main:
[`.github/workflows/ci.yml`](.github/workflows/ci.yml)

## Decisões Eric pendentes (paralelas, não bloqueiam código)

- **DP-05** — política retenção LGPD (24h proposta)
- **Política outcomes** — quem registra (Eric / advogado-piloto / integração)

## Referências de governance

- **PRD canônico:** [`governance/prd/prd-v1.0.2.md`](governance/prd/prd-v1.0.2.md)
- **ADR Index (9 ADRs):** [`governance/architecture/ADR-INDEX.md`](governance/architecture/ADR-INDEX.md)
- **QA Gates (16 docs):** [`governance/qa/`](governance/qa/)
- **TECH-DEBT.md:** [`governance/TECH-DEBT.md`](governance/TECH-DEBT.md)
- **Estado vivo:** [`governance/CHECKPOINT-active.md`](governance/CHECKPOINT-active.md)

## SOPs operacionais

| SOP | Tópico | Quando usar |
|-----|--------|-------------|
| [SOP-001](docs/sop-rotacao-auth-cookie-key.md) | Rotação de AUTH_COOKIE_KEY | Compromise de chave, política periódica de rotação |
| [SOP-002](docs/sop-populate-vault.md) | Populando o Vault Jurisprudencial | Setup inicial, atualização mensal de súmulas |
| [SOP-003](docs/sop-revisar-pdf.md) | Revisão de Contrato (Fluxo Usuário) | Cada contrato a ser analisado |

## Licença

Ver `LICENSE` na raiz do repositório.
