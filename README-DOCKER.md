---
type: guide
title: "Docker Deploy Guide — Revisor Contratual (Caminho B)"
project: revisor-contratual
version: "1.0.0"
last_updated: "2026-05-14"
authored_by: "@devops (Operator)"
purpose: "Resolve Smith F-CRIT-01 (WeasyPrint GTK Windows) + F-CRIT-02 (vault scrapers SSL/404 Windows) via container Linux"
---

# Docker Deploy Guide — Revisor Contratual

> **Caminho B do Smith ultrathink final verdict.** Container Linux resolve:
>
> - **F-CRIT-01:** WeasyPrint GTK+ Pango Cairo nativos via `apt install` no Debian
> - **F-CRIT-02 (parcial):** SSL certificate chain Linux padrão (resolve STF SSL fail)
> - **OCR (Marker-pdf):** Linux wheels disponíveis para todas versões Python (Windows Python 3.14 bleeding edge sem wheels)

---

## Pré-requisitos

1. **Docker Desktop Windows** instalado (com WSL2 backend recomendado)
   - Download: <https://www.docker.com/products/docker-desktop>
   - Verificar: `docker --version` retorna `Docker version 20+`
2. **~15GB de espaço em disco** (imagem app ~3GB + 2 Ollama containers ~6.6GB modelos + volumes)
3. `.env` populado com secrets (já feito por Operator setup)

---

## Arquitetura Docker Stack

```text
docker-compose.app.yml (Sprint 6.x Caminho B)
├── ollama-advogado    :11434  (qwen2.5:7b — tier balanced default)
├── ollama-economista  :11435  (qwen2.5:3b)
└── app                :8501   (FastAPI + WeasyPrint + Marker OCR)
                              └── depends_on: ambos Ollama healthy
                              └── volume: revisor-data (vault + audit + lock)

docker-compose.yml (Sprint 04 SP04-AUTH-01 existing)
└── postgres           :5433   (PostgreSQL 16 multi-tenant — opt-in)
```

---

## Setup Inicial (uma vez, ~30-40min)

### Passo 1 — Build imagem app

```bash
cd c:\Users\User\Documents\the_matrix\projects\revisor-contratual-staging
docker compose -f docker-compose.app.yml build app
```

Espera ~5-10min primeira vez (download Debian base + apt deps + pip install).

### Passo 2 — Subir Ollama servers

```bash
docker compose -f docker-compose.app.yml up -d ollama-advogado ollama-economista
```

Aguardar healthcheck (~30s):

```bash
docker compose -f docker-compose.app.yml ps
# Status esperado: ambos "healthy"
```

### Passo 3 — Pull modelos Ollama dentro containers

```bash
docker exec revisor-ollama-advogado ollama pull qwen2.5:7b
docker exec revisor-ollama-economista ollama pull qwen2.5:3b
```

Tempo: ~10-30min (~6.6GB total download). Pode rodar em paralelo se bandwidth suportar.

Opcional (tier premium GPU futuro):

```bash
docker exec revisor-ollama-advogado ollama pull sabia-7b-instruct
```

### Passo 4 — Subir app

```bash
docker compose -f docker-compose.app.yml up -d app
```

Aguardar healthcheck (~2min — app boot + lifespan):

```bash
docker compose -f docker-compose.app.yml logs -f app
# Esperar "Application startup complete" + "Uvicorn running on http://0.0.0.0:8501"
```

### Passo 5 — Popular vault dentro container (scrapers funcionam Linux)

```bash
docker exec revisor-app revisor populate-vault --source all
# Esperado: ~64 STJ + ~58 STF SV = ~122 items
```

> Linux container tem certificate chain SSL completo + scrapers podem funcionar onde Windows host falha (Smith F-CRIT-02 mitigation).

### Passo 6 — Acessar UI

Abrir browser: <http://localhost:8501>

Login: `admin` / `admin` (credenciais do `.env`)

---

## Operações Diárias

### Subir tudo

```bash
docker compose -f docker-compose.app.yml up -d
```

### Logs em tempo real

```bash
docker compose -f docker-compose.app.yml logs -f app
```

### Parar tudo (preserva volumes)

```bash
docker compose -f docker-compose.app.yml down
```

### Reset completo (apaga vault + audit + Ollama models)

```bash
docker compose -f docker-compose.app.yml down -v
```

> ⚠️ **Reset apaga DADOS PERMANENTEMENTE.** Confirme com Eric antes.

### Acessar shell do container app

```bash
docker exec -it revisor-app bash
```

### Verificar vault count

```bash
docker exec revisor-app python -c "
import sqlite3
conn = sqlite3.connect('/home/revisor/.local/share/revisor-contratual/vault.db')
print('Jurisprudência rows:', conn.execute('SELECT COUNT(*) FROM jurisprudencia').fetchone()[0])
"
```

---

## Combinar com Postgres SP04 (opcional)

Se Eric quiser stack completa (app + Ollama + Postgres Sprint 04):

```bash
docker compose -f docker-compose.yml -f docker-compose.app.yml up -d
```

`docker-compose.yml` existing prove `revisor-postgres` em :5433 — `.env` precisa apontar `DATABASE_URL` para `revisor-postgres:5432` (internal network).

---

## Troubleshooting

### Build falha em apt-get

- Verificar conexão internet do Docker daemon
- Tentar `docker system prune` antes (limpa cache antigo)

### App container restart loop

```bash
docker compose -f docker-compose.app.yml logs app --tail 50
```

- Se `AUTH_COOKIE_KEY missing`: verificar `.env` no host está completo
- Se `audit chain hash mismatch`: volume `revisor-data` tem GENESIS antigo — `docker compose down -v` + re-popular

### Ollama models corrupt

```bash
docker compose -f docker-compose.app.yml down -v
docker compose -f docker-compose.app.yml up -d ollama-advogado ollama-economista
docker exec revisor-ollama-advogado ollama pull qwen2.5:7b
```

### Vault populate falha SSL no container

- Pode happen se certificado raiz custom corporativo. Solução: `docker exec revisor-app bash -c "apt update && apt install -y ca-certificates && update-ca-certificates"` (mas requer root, não user revisor).

---

## Smith F-CRIT Resolution Status

| Finding | Status no Docker |
|---------|------------------|
| F-CRIT-01 (WeasyPrint GTK) | ✅ RESOLVED — `libpango libcairo libgdk-pixbuf` instalados via apt |
| F-CRIT-02 (Vault populate fail) | ⚠️ PARCIAL — STF SSL Linux deve funcionar; STJ scraper 404 ainda pode persistir (URL desatualizada Sprint 6.3 fix candidate) |
| F-HIGH-01 (Layer 3 NLI dead) | ❌ NÃO RESOLVED — Docker não fixa código; Sprint 6.3+ Neo |
| F-HIGH-02 (DEFAULT_HASH fallback inválido) | ❌ NÃO RESOLVED — mesmo issue; mas .env carrega via load_dotenv → não atinge fallback |
| F-MED-01 (Ollama subprocess NotImplementedError) | ✅ RESOLVED — Linux asyncio funciona sem WindowsProactor |

---

## Próximos Passos pós-Docker-Setup

1. Eric upload PDF contrato real CDC veículo PF via <http://localhost:8501>
2. Pipeline 9-etapas roda end-to-end (Steps 1-7 + Step 8 WeasyPrint render PDF agora funciona)
3. Download PDF gerado via `/download/{job_id}`
4. Eric valida qualidade peça
5. Se OK → anonimizar PDFs + forward advogada externa (Trinity email template em `governance/external/`)
6. Smith re-review com output PDF real → CLEAN verdict → Operator commit + push v0.2.3

---

*Documento criado em 2026-05-14 por @devops (Operator) — Sprint 6.x Caminho B Docker deploy*
*Resolve Smith F-CRIT-01 + F-CRIT-02 (parcial) per ultrathink final verdict.*
