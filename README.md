# Revisor Contratual

> Sistema SaaS B2B BYOK de revisão jurídica de contratos bancários — production deployed em [revisor.claudinoinsights.com](https://revisor.claudinoinsights.com).

## 🎯 Visão

**Revisor Contratual** é um sistema agentic deployed em produção que analisa contratos de financiamento bancário (CDC PF Veículos prioritário, com roadmap para Bens/Imobiliário/Cartão) e produz veredito jurídico + contábil + fiscal fundamentado em jurisprudência vinculante STF + STJ.

**Target audience:** Escritórios de advocacia + Departamentos jurídicos B2B que necessitam revisão escalável de contratos bancários com compliance LGPD on-premise.

**Modelo:** SaaS B2B BYOK (Bring Your Own Key) — escritório paga API LLM direto (Anthropic/OpenAI/local Ollama), nós entregamos plataforma + pipeline + audit chain LGPD §46.

**Performance empirical (Sprint 7 Phase 4):**

- Born-digital PDF: **~985ms** (PyMuPDF fast path) — 180x speedup vs subprocess
- Scanned PDF: ~120s (marker OCR subprocess isolation)
- LGPD §46 HMAC chain integrity: 100% preserved (11/11 entries empirical Sprint 7)

## 📊 Estado — v0.2.10.0 (Sprint 7 Closed)

> **🚧 OPERATOR COLLABORATIVE FINISH PENDENTE** (Sprint 8 Story #2.5 — atualizar versions + git tags + production URL + ongoing Sprint 8 cleanup checkboxes)

**Production:**

- 🚀 **Release:** [v0.2.10.0](https://github.com/Claudinoinsights/revisor-contratual/releases/tag/v0.2.10.0) (2026-05-16)
- 🌐 **Production URL:** [https://revisor.claudinoinsights.com](https://revisor.claudinoinsights.com)
- 🏗️ **Image:** `revisor-contratual:prod` sha256:c93e9853d50a (Sprint 8 Stories #1.5+#1.6 hardened)
- 🛡️ **Smith verdict (Sprint 7 Phase 4):** CONTAINED + GREENLIGHT — Cenário Y++ DoD architectural 100% atingido empirically
- 📋 **Sprint status:** Sprint 7 Closed (Cenário Y++ DoD architectural) + Sprint 8 Phase A em progresso (production readiness 56→target 95+/100)

**Architectural Milestones:**

- ✅ **Cenário Y++ DoD architectural:** parser_used=pymupdf4llm + audit 9 keys + Step 2 reached + container preserved + HMAC chain INTACT
- ✅ **F-PROD-NEW-22 RESOLVED:** subprocess isolation Phase 3 (ADR-026) + dual-path Phase 4 (ADR-027)
- ✅ **Memory consolidation:** 22GB+ → 10GB total (~55% reduction via Ollama single-container ADR-028)
- ✅ **Production hardening Sprint 8:** /docs disabled em produção (REVISOR_ENV=production) + LGPD §16 tempfile cleanup 3-layer defense

**Cumulative Stats:**

- 🌱 **Origem:** extraído de `Claudinoinsights/the-matrix` em 2026-05-05 (Sprint 01 closure)
- 📦 **Governance:** PRD v1.0.x + ~50 stories cumulative + ADRs 001-029 + 7 Sprints closed + ongoing Sprint 8
- 🧪 **Tests:** ~233 cumulative (smoke pipeline real Sprint 02 + integration tests Sprint 7+8)
- 🔄 **CI GitHub Actions:** verde Python 3.11 + 3.12 ([`.github/workflows/ci.yml`](.github/workflows/ci.yml))

## 🏛️ Arquitetura

**Stack production:**

- **Backend:** FastAPI + HTMX + Jinja2 + uvicorn (Python 3.13)
- **LLM:** Ollama embedded (qwen2.5:3b + qwen2.5:7b) via ADR-028 single-container consolidation
- **Parsing dual-path (ADR-027):**
  - Born-digital → PyMuPDF inline (`asyncio.to_thread`, ~985ms latency)
  - Scanned → marker OCR subprocess isolation (`asyncio.create_subprocess_exec`, ~120s)
- **Subprocess isolation (ADR-026):** F-PROD-NEW-22 silent worker exit RESOLVED via process-level isolation
- **Audit chain:** HMAC LGPD §46 (`bloco_audit/chain.py`) — entry_hash + previous_entry_hash links
- **Backup:** APScheduler embedded (ADR-013 §2.4 + ADR-029 enhancements)
- **Deploy:** Docker Compose + Traefik reverse proxy + Cloudflare DNS (HTTPS + HSTS preload)

**Key Architectural Decisions (ADRs):**

| ADR | Title | Sprint |
|-----|-------|--------|
| [ADR-010](governance/architecture/adr/) | Path C — Qwen 7B fallback default + format=json economista | Sprint 02 |
| [ADR-013](governance/architecture/adr/) | APScheduler embedded backup + lifespan integration | Sprint 02 |
| [ADR-014](governance/architecture/adr/) | Audit chain HMAC LGPD §46 | Sprint 01 |
| [ADR-026](governance/architecture/adr/adr-026-marker-subprocess-isolation-parsing.md) | Marker subprocess isolation parsing | Sprint 7 Phase 3 |
| [ADR-027](governance/architecture/adr/adr-027-pymupdf-born-digital-fast-path.md) | PyMuPDF born-digital fast path (dual-path) | Sprint 7 Phase 4 |
| [ADR-028](governance/architecture/adr/adr-028-ollama-single-container-consolidation.md) | Ollama single container consolidation | Sprint 7 Phase 2 |
| [ADR-029](governance/architecture/adr/adr-029-backup-strategy.md) | Backup strategy — APScheduler + visibility + retention 30d | Sprint 8 |

**Index completo:** [`governance/architecture/ADR-INDEX.md`](governance/architecture/ADR-INDEX.md)

## 🚀 Production Status

**Deployment:**

- **Region:** Hetzner VPS Germany (eric@91.108.126.149)
- **Reverse proxy:** Traefik v2.11 (Let's Encrypt cert + HSTS preload + CSP headers)
- **Container orchestration:** Docker Compose v2 (`docker-compose.prod.yml`)
- **DNS:** Cloudflare (proxied — DDoS protection + caching layer)

**Resource limits:**

- App container: 6GB memory limit (~50 MiB idle baseline, ~700 MiB pipeline run)
- Ollama-shared container: 4GB memory limit (consolidated qwen2.5:3b + 7b via ADR-028)
- Total VPS budget: ~10GB application stack (de 7.8GB system RAM) — efficient

**Monitoring stack:**

- Prometheus + Grafana 11.1 + Alertmanager + Loki 3.0
- Uptime-Kuma probes (revisor.claudinoinsights.com health)
- Cockpit web UI (system management)

**Ongoing Sprint 8 cleanup (production readiness 56→95+/100):**

| Item | Status |
|------|--------|
| Disk cleanup ≥80% buffer | ✅ DONE (Story #0) |
| Marker cache volume mount | ✅ DONE (Story #2) |
| Tempfile LGPD §16 3-layer defense | ✅ DONE (Story #1.5) |
| /docs production hardening | ✅ DONE (Story #1.6) |
| README architectural refresh | 🚧 EM PROGRESSO (Story #2.5 — THIS document) |
| Backup automation visibility + retention 30d | 🚧 EM PROGRESSO (Story #7 — ADR-029 + runbook) |
| DNS subdomains uptime+cockpit | ⏳ Phase B (Story #8) |
| Backup encryption Sprint 9+ | ⏳ Future (ADR-031) |

> Para acompanhar Sprint 8 detalhado: [`governance/sprints/sprint-8-scope.md`](governance/sprints/sprint-8-scope.md)

## 🔐 LGPD Compliance

**Princípios implementados:**

- **§16 Minimização:** Tempfile PDF cleanup 3-layer defense (background safety task + lifespan shutdown + cron daily) — Sprint 8 Story #1.5
- **§46 Audit chain HMAC:** entry_hash + previous_entry_hash cryptographic chain (`bloco_audit/chain.py`) — integrity preserved 100% empirical Sprint 7
- **§11 On-premise:** Fontes self-hosted (Manrope + Fraunces + JetBrains Mono), ZERO CDN externo (REV-INT-02 Sprint 02)
- **Backup retention 30d:** ADR-029 + APScheduler embedded (`bloco_backup/scheduler.py`)
- **Zero PII em backups:** vault.db (jurisprudência pública) + audit.jsonl (HMAC hashes apenas — no CPF/nome/valor financeiro)

**Production hardening:**

- HTTPS-only (HTTP→HTTPS 308 permanent redirect)
- HSTS preload + CSP + X-Frame-Options + X-Content-Type-Options + Permissions-Policy
- `/docs` + `/openapi.json` + `/redoc` disabled em produção (REVISOR_ENV=production guard — Sprint 8 Story #1.6)
- File upload validation (MIME magic bytes %PDF- + max 10MB)
- Non-root container user (revisor uid 1000)
- Cookie session HttpOnly + SameSite=Lax + 24h max-age

**Audit verification empirical (Sprint 7 Phase 4):**

```text
audit.jsonl: 11 entries
HMAC chain integrity: 10/10 valid links (CHAIN INTACT)
parser_used distribution: pymupdf4llm=7 (born-digital) | None=4 (subprocess timeouts)
```

## 📋 Governance & Documentation

> **🚧 OPERATOR COLLABORATIVE FINISH PENDENTE** (Sprint 8 Story #2.5 — atualizar links CHECKPOINT + CHANGELOG cross-refs)

- **PRD:** [`governance/prd/`](governance/prd/) (v1.0.x cumulative)
- **CHECKPOINTS:**
  - [`governance/CHECKPOINT-active.md`](governance/CHECKPOINT-active.md) (current sprint activity)
  - [`governance/PROJECT-CHECKPOINT.md`](governance/PROJECT-CHECKPOINT.md) (executive summary)
- **CHANGELOG:** [`governance/CHANGELOG-v0.2.10.0.md`](governance/CHANGELOG-v0.2.10.0.md) (Sprint 7 closure release notes)
- **Sprints:**
  - [`governance/retrospectives/sprint-7-retrospective.md`](governance/retrospectives/sprint-7-retrospective.md)
  - [`governance/sprints/sprint-8-scope.md`](governance/sprints/sprint-8-scope.md) (current)
- **Smith adversarial verifies:** [`governance/qa/smith-verify-*.md`](governance/qa/)
- **Tech Debt:** [`governance/TECH-DEBT.md`](governance/TECH-DEBT.md)
- **Architecture decisions:** [`governance/architecture/`](governance/architecture/)
- **Runbooks:**
  - [`governance/runbook-backup-restore.md`](governance/runbook-backup-restore.md) (DR procedure)
  - [`governance/sop-revisar-pdf.md`](governance/sop-revisar-pdf.md) (CLI usage)
  - [`governance/sop-populate-vault.md`](governance/sop-populate-vault.md) (vault management)

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

### 6. (Opcional) UI Web local — FastAPI + HTMX

```bash
revisor-web
# OU diretamente:
uvicorn bloco_interface.web.app:app --port 8501 --reload
# Abre: http://127.0.0.1:8501
# Design system orsheva (laranja accent + Manrope/Fraunces) aplicado via tokens CSS
```

> 🚧 **UI Web v0.1.0 é workspace minimal** — só ações do operador (upload, configurar, revisar, ver veredito). Invocação real do pipeline será implementada na STORY UI-1 do Sprint 02. Por agora roda em modo demo (mock SSE 7 steps + mock veredito HITL 78%). CLI é canônica para uso real.
>
> **Stack:** FastAPI + HTMX 2.0 + Jinja2 + uvicorn. HTMX local em `bloco_interface/web/static/htmx.min.js` (sem CDN runtime).
> **Migração de Streamlit:** REV-INT-01 (2026-05-05) — Streamlit removido por limitar controle CSS profundo. Filosofia LEAN preservada.

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

## LLM Strategy (ADR-003 PATCH SUB-C + PATCH 2 + ADR-010 Path C)

Fan-out paralelo via `asyncio.gather` em **2 instâncias Ollama distintas**:

- **Advogado** — Tier configurável `lean | balanced | premium` (`OLLAMA_HOST_ADVOGADO=127.0.0.1:11434`):
  - `lean=qwen2.5:3b` (consistência família com economista)
  - `balanced=qwen2.5:7b` — **DEFAULT** (CPU-friendly per ADR-010 Path C; smoke evidence 253.72s PASS)
  - `premium=sabia-7b-instruct` (preserved opt-in para futuro upgrade GPU)
- **Economista** — Qwen 2.5 3B FIXO (`OLLAMA_HOST_ECONOMISTA=127.0.0.1:11435`)

**Footprint:** ~10.7GB disco total (qwen2.5:3b 1.9GB + qwen2.5:7b 4.7GB + sabia-7b-instruct 4.1GB preserved opt-in). **Latência:** ~250-300s INTEGRAL com Qwen 7B em CPU (~250s smoke evidence sessão 86); ~120s com tier premium quando GPU disponível.

**GPU upgrade path:** Toggle `LLM_TIER=premium` em `.env` reverte para Sabia-7B em 1 linha — sem mudança de código, sem nova ADR. Decisão de quando habilitar é operacional (deploy em hardware com GPU CUDA disponível).

**Validação obrigatória pré-release:** rodar `pytest tests/smoke/test_paralelismo_llm.py` — ratio asyncio.gather vs sequencial DEVE ser <0.7. Se falhar, paralelismo é placebo (debug `OLLAMA_HOST` distintos OU `langchain-ollama>=0.2.0`).

**Cross-refs:** ADR-003 SUB-C (paralelismo), ADR-003 PATCH 2 (instâncias distintas), [ADR-010](governance/architecture/adr/adr-010-sabia-q4-mitigation.md) (Qwen 7B fallback default — Sabia Q4 quality issue mitigation).

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
| Modelos Ollama (Qwen 2.5 7B + Qwen 2.5 3B; Sabia-7B preserved opt-in) NÃO inclusos | App auto-pulla via OLLAMA-MGR-01 (ADR-011) — basta Ollama instalado + 7GB livres | SOP sop-revisar-pdf + ADR-010 + ADR-011 |
| sentence-transformers (~500MB) é opt-in | populate-vault default `--zero-embeddings=True` (busca lexical funciona; vetorial degraded) | SOP-002 |
| BACEN python-bcb >=0.3 (PyPI max real) | Pin aspiracional >=0.5 corrigido em STORY 12 | CI Linux validou |
| UI Streamlit ainda não implementada (CLI MVP only) | Use `revisor revisar` direto na CLI | Roadmap pós-MVP |

## Como rodar (1 comando — pós OLLAMA-MGR-01 / ADR-011)

```bash
python -m bloco_interface.web.app
# → app auto-detecta Ollama, spawna instâncias missing em :11434+:11435,
#   baixa modelos faltantes (qwen2.5:7b + qwen2.5:3b), ready em ~30s
# → primeira vez pode levar 10-30min para download de modelos (~6.6GB total)
# → UI banner mostra progresso de download em tempo real (SSE em /ollama-status)
```

**Pré-requisitos:**
- Python 3.11+ + `pip install -e .`
- [Ollama instalado](https://ollama.ai/download) (binary detectado automaticamente)
- 7GB+ disco livre para modelos LLM (uma única vez)

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
