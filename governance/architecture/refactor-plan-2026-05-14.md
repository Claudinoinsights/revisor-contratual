---
type: refactor-plan
title: "Plano de Refatoração + Modularização — Revisor Contratual"
date: "2026-05-14"
author: "@architect (Aria)"
status: DRAFT (Eric pending approval)
project: revisor-contratual-staging
sprint_target: "Pós Sprint 6.x (Sprint 7+ candidato)"
tags:
  - project/revisor-contratual-staging
  - refactor
  - modularization
  - slim-deploy
---

# Plano de Refatoração + Modularização — Revisor Contratual

> *"Toda arquitetura é resposta a uma pergunta. A pergunta mudou: agora é como rodar em qualquer máquina + facilitar manutenção. Resposta requer redesenho consciente, não rewrite."*

---

## Sumário Executivo

### Situação atual (Sprint 6.x v0.2.2 origin/main)

| Métrica | Valor atual |
|---------|-------------|
| Docker image | **10.1GB** (Python 3.13 + GTK + Marker OCR + WeasyPrint + Surya + sentence-transformers + transformers + torch + CUDA toolkit) |
| Ollama models | **6.6GB** (qwen2.5:7b + qwen2.5:3b em 2 containers) |
| RAM mínima funcional | **~5GB** (Marker OCR exige 2.5GB + app 1GB + Ollama 1.5GB) |
| Arquitetura | **Monolito FastAPI** (~11 packages bloco_*) + 2 Ollama containers + Postgres opcional |
| Modalidades suportadas | **1** (CDC Veículos PF), 4 outras planejadas como ADRs |
| Vault | SQLite single-file, 10 rows (target 658+) |
| Pytest baseline | 589/684 PASS (20 falhas integration pre-existing) |
| Tempo build Docker | **5-10min** (~10GB layers) |

### Target state (pós-refator)

| Métrica | Valor target |
|---------|--------------|
| Docker image **lean** (sem OCR) | **<1.0GB** |
| Docker image **standard** (com OCR opcional) | **<3.5GB** |
| RAM mínima lean | **~1.5GB** (PDFs text-based only, sem OCR) |
| RAM mínima standard | **~5GB** (com OCR) |
| Arquitetura | **6 microservices** + 2 Ollama + Postgres + Redis (opt) |
| Modalidades | **Plugin registry** — adicionar modalidade sem tocar core |
| Build time | <3min (slim) / <8min (full) |

### ROI esperado

- **Onboarding novos devs:** 1-2 dias → 4-6 horas (arquitetura modular auto-documenta intent)
- **Deploy variants:** Eric pode escolher `lean` (sem OCR, máquina modesta) OR `standard` (full features)
- **CI/CD:** test isolation per service → pytest baseline matrix paralelo (5min total vs 10min serial)
- **Custo VPS:** mínimo 2GB RAM (atual exige 4GB+) — economia ~$5-10/mês em pequenos VPS

### Investimento

- **Fase 1 (quick wins):** ~1 semana — slim Docker + Marker opt-in
- **Fase 2 (modularização):** ~3-4 semanas — split services
- **Fase 3 (plug-in):** ~6 semanas — plugin registry modalidades
- **Fase 4 (cloud-native):** ongoing — observability + multi-tenant
- **+30% buffer arquitetural** (regra do dedo)

---

## Eixo 1 — Slim Docker Image

### Análise atual

Dockerfile atual instala TUDO no app container:

| Component | Tamanho | Necessário runtime? |
|-----------|---------|---------------------|
| CUDA toolkit | ~4GB | ❌ Não (CPU-only inference) |
| Marker OCR + Surya | ~2GB | ⚠️ Opt-in (apenas PDFs imagem-only) |
| sentence-transformers | ~500MB | ✅ Layer 3 NLI futuro |
| transformers + torch | ~3GB | ✅ Marker + sentence-transformers deps |
| WeasyPrint + GTK | ~200MB | ✅ Step 8 render PDF |
| FastAPI + SQLAlchemy + 30 outras | ~150MB | ✅ Core app |

### Proposta

**Multi-stage build com 3 variants:**

```dockerfile
# ── Stage 1: builder (compilation) ──
FROM python:3.13-slim-bookworm AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev libcairo2-dev libpango1.0-dev \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip wheel --no-cache-dir -e ".[lean]" -w /wheels

# ── Stage 2: runtime LEAN (default — <1GB) ──
FROM python:3.13-slim-bookworm AS lean
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links /wheels revisor-contratual
# CPU-only torch via index URL
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY bloco_*/ /app/
RUN useradd -m -u 1000 revisor && chown -R revisor:revisor /app
USER revisor
CMD ["uvicorn", "bloco_interface.web.app:app", "--host", "0.0.0.0", "--port", "8501"]

# ── Stage 3: runtime STANDARD (com OCR — <3.5GB, opt-in via target) ──
FROM lean AS standard
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-por poppler-utils \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir 'marker-pdf>=0.2' surya-ocr
USER revisor
```

Eric escolhe target no `docker build --target lean` OR `--target standard`.

### Complexidade migração: **M (Medium)** — 1-2 dias trabalho Neo
### Risco: **Low** — refactor build-only, código não mexido

---

## Eixo 2 — Modularização Services

### Análise atual

Monolito FastAPI: 1 processo carrega TUDO (auth + UI + pipeline + vault + audit + render).

**Problemas:**
- Memory footprint alto (~1.5GB app sozinho) mesmo idle
- Crash em qualquer step → app inteiro reinicia
- Test isolation ruim (importar 1 módulo carrega 30+ deps)
- Scale separado impossível (não pode ter 3 workers de pipeline + 1 ui)

### Proposta

Split em **6 microservices** comunicando via HTTP REST (simples) + Redis pub/sub (opcional Sprint 8+):

```text
┌────────────────────────────────────────────────────────────────┐
│                    Target Architecture                          │
└────────────────────────────────────────────────────────────────┘

         ┌─────────┐
         │  Caddy  │ HTTPS Let's Encrypt + WAF
         └────┬────┘
              │
         ┌────▼────┐
         │ app-ui  │ FastAPI + HTMX + Auth (LEAN, ~200MB)
         │  :8501  │
         └────┬────┘
              │ HTTP REST
   ┌──────────┼──────────────────────┐
   │          │                      │
   ▼          ▼                      ▼
┌──────┐  ┌──────────┐         ┌──────────┐
│vault │  │ pipeline │         │  audit   │
│:9001 │  │  :9002   │         │  :9003   │
└──────┘  └────┬─────┘         └──────────┘
   │           │
   │      ┌────┼────┬─────────┬─────────┐
   │      │    │    │         │         │
   │      ▼    ▼    ▼         ▼         ▼
   │  ┌───────┐ ┌────────┐ ┌──────┐ ┌──────┐
   │  │ ocr   │ │ ollama │ │ olla │ │render│
   │  │:9004  │ │ -adv   │ │ -eco │ │:9005 │
   │  │opt-in │ │:11434  │ │:11435│ │      │
   │  └───────┘ └────────┘ └──────┘ └──────┘
   │
   ▼
┌────────┐
│postgres│  (multi-tenant Sprint 04 — pgvector futuro)
│ :5432  │
└────────┘
```

### Services

| Service | Responsabilidade | Tamanho image | Stateful? |
|---------|-----------------|---------------|-----------|
| `app-ui` | UI + auth + session + orchestration | ~250MB | Não (Redis session opt) |
| `pipeline` | Steps 1-6 (parsing + cálculo + BACEN + LLMs orchestration) | ~500MB | Não |
| `vault` | Busca jurisprudência híbrida (sqlite-vec + BM25) | ~300MB | Sim (vault.db OR Postgres) |
| `audit` | HMAC chain write-only (LGPD §46) | ~150MB | Sim (audit.jsonl OR Postgres) |
| `ocr` (opt-in) | Marker + Surya OCR | ~2GB | Não (cache /tmp) |
| `render` | WeasyPrint PDF | ~300MB | Não |
| `ollama-adv` + `ollama-eco` | LLM inference | 4.7GB + 1.9GB | Sim (models volume) |
| `postgres` | Multi-tenant + DPA + tos | ~150MB | Sim |
| `redis` (opt Sprint 8+) | Session + cache + queue | ~50MB | Sim |

### Comunicação inter-services

**Sprint 7:** HTTP REST simples (FastAPI client + httpx). Latência ~20-50ms per hop, aceitável para pipeline 250s.

**Sprint 8+ (opt):** Redis pub/sub para SSE events + async pipeline steps.

### Trade-offs

| Ganho | Perde |
|-------|-------|
| Memory isolation per service | +20-50ms latência inter-service per hop |
| Crash 1 service não derruba app | +complexidade compose stack (6 services vs 1) |
| Scale horizontal independente | +deploy complexity (build 6 images) |
| Test contracts entre services | +overhead network HTTP entre containers |
| OCR opcional não consome RAM se não usado | Eric precisa configurar mode (lean/standard) |

### Complexidade migração: **L (Large)** — 3-4 semanas Neo
### Risco: **Medium** — refactor coupling cross-bloco, exige test refator paralelo

---

## Eixo 3 — Plug-in Modalidades

### Análise atual

Modalidade atual hardcoded: pipeline lê `modalidade=CDC_VEICULOS_PF` mas chama strategies fixas em `bloco_engine/strategies/`. Adicionar Cartão/Consignado/Imobiliário/FIES exige tocar pipeline.py + strategies + templates + tests.

### Proposta

**Plugin registry via Python entry_points** (`pyproject.toml`):

```python
# core: interface
class ModalidadeStrategy(Protocol):
    name: str  # "cdc_veiculos_pf"
    template_path: Path
    
    def parse_contract(self, pdf: Path) -> ContratoMetadata: ...
    def calculate_anatocismo(self, ctx: CalculoContext) -> ResultadoCalculo: ...
    def validate_oab_fields(self, peca: PecaRevisional) -> bool: ...

# plugin: pyproject.toml
[project.entry-points."revisor.modalidades"]
cdc_veiculos_pf = "revisor_modalidade_cdc_veiculos:Strategy"
cartao_rotativo = "revisor_modalidade_cartao:Strategy"  # plugin separado
```

**Adicionar modalidade nova = criar pacote Python plugin separado** + `pip install`. Core não toca.

### Repositórios sugeridos

```
github.com/Claudinoinsights/
├── revisor-contratual            (core)
├── revisor-modalidade-cdc-veiculos
├── revisor-modalidade-cartao
├── revisor-modalidade-imobiliario
└── revisor-modalidade-fies
```

### Complexidade migração: **L (Large)** — 4-6 semanas Neo
### Risco: **Medium** — refactor strategies + interface design crítico

---

## Eixo 4 — Test Isolation

### Análise atual

**20 falhas pytest integration** em Sprint 6.x baseline (cataloged TD-PYTEST-INTEGRATION-20-PRE-EXISTING). Causa: importar `bloco_interface.web.app` carrega 30+ deps + side-effects.

### Proposta

3 camadas test:

| Camada | Escopo | Mock | Tempo |
|--------|--------|------|-------|
| **Unit** | Per bloco isolado | Mock everything external | <30s |
| **Contract** | Interface entre services | Mock Ollama via fixture httpx_mock | <2min |
| **E2E** | Stack completo Docker | Real services (opt-in) | <10min |

**Mocks Ollama:** fixture `httpx_mock` com responses canned (não exige Ollama running em CI).

### Complexidade migração: **M (Medium)** — 2 semanas Neo + Oracle
### Risco: **Low** — adicionar testes não quebra existentes

---

## Eixo 5 — Storage Strategy

### Análise atual

- Vault: SQLite single-file (`vault.db`) — não escala multi-tenant
- Audit: JSONL append-only — eficiente mas single-file
- Postgres em compose mas under-utilized (apenas Sprint 04 auth multi-tenant)

### Proposta fasada

**Sprint 7 (sem migrar dados):** manter SQLite vault + JSONL audit; adicionar abstraction layer (`VaultRepository` interface) para futura migração.

**Sprint 9+ (migration):** vault → Postgres com pgvector extension. audit → Postgres com partitioning per-tenant.

### Trade-off

- SQLite: rápido para <100k rows, single-tenant
- Postgres+pgvector: scale multi-tenant, search distribuída, MAS complexidade ops alta

### Complexidade migração: **XL (Extra Large)** — fora escopo Sprint 7
### Risco: **High** — perda de dados se migration mal feita

---

## Eixo 6 — Configuração

### Análise atual

`.env` flat: ~30 vars, secrets + features misturados, hard reload runtime.

### Proposta

**Pydantic Settings hierárquico:**

```python
class Settings(BaseSettings):
    auth: AuthSettings  # AUTH_COOKIE_KEY, ADMIN_*, JWT_*
    llm: LLMSettings    # OLLAMA_HOST_*, LLM_TIER
    audit: AuditSettings  # FERNET_KEY, retention_days
    
    model_config = SettingsConfigDict(
        env_file=(".env", "config/dev.yaml"),
        env_nested_delimiter="__",
    )

# Usage: settings.auth.cookie_key
```

**Secrets:** Docker secrets (production) OR HashiCorp Vault (futuro).

### Complexidade migração: **S (Small)** — 2-3 dias Neo
### Risco: **Low** — backward compat possível com adapter

---

## Eixo 7 — Observability

### Análise atual

- Logs: structlog (texto), audit.jsonl, .ollama-*.log
- Métricas: nenhuma
- Tracing: nenhum

### Proposta

**Stack OpenTelemetry:**

| Layer | Tool | Onde |
|-------|------|------|
| Tracing | OpenTelemetry SDK Python | Per service (auto-instrument FastAPI) |
| Coleta | OTel Collector | Container separado |
| Visualização | Jaeger OR Tempo (Grafana stack) | Local OR self-hosted VPS |
| Métricas | Prometheus + node_exporter | Container separado |
| Dashboard | Grafana | Container separado |
| Logs aggregação | Loki | (opt — Sprint 9+) |

### Complexidade migração: **M (Medium)** — 1-2 semanas Neo
### Risco: **Low** — additive, não modifica código existente (apenas instrumentação)

---

## Roadmap Fasado

### Fase 1 — Quick Wins (1 semana)

**Sprint 7.1** — Foco: rodar em qualquer máquina ASAP.

- [ ] Eixo 1: Dockerfile multi-stage com targets `lean`/`standard`
- [ ] Eixo 1: CPU-only torch wheel (remove CUDA 4GB)
- [ ] Eixo 6: hierarchical config Pydantic Settings (parcial — auth + llm)
- [ ] Doc: `docs/deploy-guide.md` com 3 cenários (lean local / standard local / Docker VPS)

**Entrega:** image `lean` <1GB, runs em laptop 4GB RAM. STD ainda 3.5GB com OCR.

### Fase 2 — Modularização Core (3-4 semanas)

**Sprint 7.2-7.4** — Foco: split services + test isolation.

- [ ] Eixo 2: split `bloco_audit` → `audit-service` container
- [ ] Eixo 2: split `bloco_vault` → `vault-service` container
- [ ] Eixo 2: split OCR (Marker+Surya) → `ocr-service` container opt-in
- [ ] Eixo 2: split WeasyPrint → `render-service` container
- [ ] Eixo 4: 3 camadas test (unit + contract + e2e)
- [ ] Eixo 4: mocks Ollama via httpx_mock
- [ ] Doc: `docs/architecture/services.md` interfaces HTTP REST

**Entrega:** stack 6 services + 2 Ollama + Postgres. Crash 1 service não derruba sistema.

### Fase 3 — Plug-in Modalidades (4-6 semanas)

**Sprint 8.x** — Foco: facilidade adicionar modalidade.

- [ ] Eixo 3: design `ModalidadeStrategy` interface
- [ ] Eixo 3: refactor CDC veículos PF → plugin separado
- [ ] Eixo 3: plugin loader em pipeline-service
- [ ] Eixo 3: template scaffold `cookiecutter-revisor-modalidade`
- [ ] Plugin: Cartão rotativo (primeiro plugin real)
- [ ] Doc: `docs/architecture/plugins.md` how-to

**Entrega:** Adicionar modalidade nova = 1 dia (vs ~2 semanas atual).

### Fase 4 — Cloud-Native (Ongoing)

**Sprint 9+** — Foco: production-grade.

- [ ] Eixo 5: vault → Postgres+pgvector migration
- [ ] Eixo 7: OpenTelemetry + Prometheus + Grafana
- [ ] Eixo 6: secrets management adequado (HashiCorp Vault OR cloud provider)
- [ ] Multi-tenant pricing tiers (Sprint 04 SP04-AUTH-01 evolution)
- [ ] Eixo 4: matrix CI pytest paralelo (5 cores)

**Entrega:** Production-grade SaaS multi-tenant.

---

## ADRs Candidatos (Eric decide criar)

| ADR | Tópico | Fase |
|-----|--------|------|
| ADR-023 | Multi-stage Docker + variants lean/standard | 1 |
| ADR-024 | Microservices boundary (6 services + contracts) | 2 |
| ADR-025 | Inter-service protocol: HTTP REST + httpx | 2 |
| ADR-026 | Plugin registry via entry_points | 3 |
| ADR-027 | Test pyramid: unit + contract + e2e | 2 |
| ADR-028 | Storage migration SQLite → Postgres+pgvector | 4 |
| ADR-029 | Observability stack (OTel + Prometheus + Grafana) | 4 |

---

## Estimativa Tamanho Final

| Variant | Image size | RAM mín | CPU | Cenário |
|---------|-----------|---------|-----|---------|
| **lean** | <1.0GB | 1.5GB | 1 core | PDFs text-based, modalidades plugin |
| **standard** | <3.5GB | 5GB | 2 cores | + Marker OCR (PDFs imagem-only) |
| **gpu-full** | 8GB | 16GB | 4 cores + GPU CUDA | Tier premium sabia-7b GPU inference |

Eric pode rodar `lean` em qualquer laptop 4GB+. `standard` em VPS modesto $5/mês. `gpu-full` em workstation OR cloud GPU.

---

## Trade-offs Globais

### Você GANHA

- **Manutenibilidade:** mudança em 1 service não afeta outros (test isolation real)
- **Onboarding:** novo dev entende arquitetura em horas (não dias)
- **Escala:** scale horizontal independente per service
- **Custo:** deploy minimalista possível ($5/mês VPS)
- **Modalidades:** plug-in dev em 1 dia vs 2 semanas
- **Resiliência:** crash 1 service não derruba sistema
- **CI/CD:** test paralelo matrix → builds <5min

### Você PERDE

- **Latência:** +20-50ms inter-service per hop (~150ms total pipeline)
- **Complexidade ops:** 6 services + 2 Ollama + Postgres = 9 containers (vs 3 atual)
- **Debugging:** distributed traces obrigatório (não dá pra `print()` cross-service)
- **Investimento inicial:** ~10-14 semanas total (com 30% buffer)
- **Migração dados:** Sprint 9 vault migration tem risco perda dados

### Mitigations

- Latência: aceitável dado pipeline 250s real (overhead 0.06%)
- Complexidade: docker-compose abstrai; healthchecks + restart policies cuidam
- Debugging: OpenTelemetry Sprint 9
- Investimento: priorize Fase 1 (quick win) — Eric decide se vai Fase 2+

---

## Recomendação Aria

**Prioridade IMEDIATA (Sprint 7.1):** Fase 1 quick wins. Resolve Eric directive "rodar em qualquer máquina" SEM rewrite. Esforço: 1 semana. ROI: image 10.1GB → <1GB.

**Prioridade MÉDIA (Sprint 7.2-7.4):** Fase 2 modularização. Resolve "manutenções mais fácil". Esforço: 3-4 semanas. ROI: test isolation + crash isolation.

**Prioridade BAIXA (Sprint 8+):** Fase 3 plug-in. Resolve "implementações mais fácil". Esforço: 4-6 semanas. ROI: nova modalidade em 1 dia.

**DEFERIR (Sprint 9+):** Fase 4 cloud-native. Só após Eric ter clientes reais pagando — não otimize prematuramente.

---

## Próximos Passos

1. **Eric review este plano** (estimado 30min leitura)
2. **Eric aprova roadmap fases** (1/2/3/4 todas? ou só Fase 1?)
3. **Niobe Skill `*draft`** stories da Fase aprovada
4. **Aria Skill `*create-full-stack-architecture`** ADR-023 (se Fase 1 aprovada)
5. **Neo Skill `*develop`** implementa stories

**Eric pode também decidir:**

- Manter status quo Sprint 6.x v0.2.2 → operacional, deploy via Docker (10GB OK em VPS dedicado)
- Pular para Fase 2 sem Fase 1 (risco: image grande continua)
- Implementar Fase 1 + 3 (skip Fase 2) → modular plugin mas monolito core

---

*Plano gerado em 2026-05-14 por @architect (Aria) — Sprint 6.x cumulative refactor analysis.*
*30% buffer arquitetural incluído. Sem ADRs criados — Eric aprovará primeiro.*
