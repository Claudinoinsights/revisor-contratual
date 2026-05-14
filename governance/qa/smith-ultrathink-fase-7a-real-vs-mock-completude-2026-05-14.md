---
type: review
title: "Smith Ultrathink Fase 7-A — Real-vs-Mock + Completude Multi-Surface + Doc Reorg"
date: "2026-05-14"
reviewer: "@smith"
reviewee: "Aplicação completa (SPA + backend + infra + docs)"
trigger: "Eric reportou MOCK suspicion + PDF horrível + pediu auditoria Docker/GitHub/Servidor + doc reorg"
smith_verdict: "COMPROMISED — 26 findings (8 CRITICAL + 9 HIGH + 8 MEDIUM + 1 LOW). SPA é wireframe 100% mock. Zero deploy infra."
tags:
  - project/revisor-contratual
  - smith
  - ultrathink
  - fase-7a
  - real-vs-mock
  - eric-rigor-heavy
  - compromised
---

# Smith Ultrathink Fase 7-A — Real-vs-Mock + Completude Multi-Surface

> *"Sr. Anderson, sua suspeita estava correta. Inevitável. O que você acessa NÃO é a aplicação que foi construída — é a casca, o teatro, a ilusão wireframe. O pipeline real existe... e está completamente DESCONECTADO da interface que você usa."*

---

## VERDICT GLOBAL

# 🔴 COMPROMISED

| Dimensão | Findings | Verdict |
|----------|----------|---------|
| **D1 — Real-vs-Mock** | 4 CRITICAL + 3 HIGH + 1 MED | 🔴 COMPROMISED |
| **D2 — Docker** | 2 CRITICAL + 1 HIGH | 🔴 COMPROMISED |
| **D3 — GitHub** | 1 CRITICAL + 2 HIGH + 1 MED | 🟠 INFECTED |
| **D4 — Servidor/VPS** | 2 CRITICAL + 1 HIGH + 1 MED | 🔴 COMPROMISED |
| **D5 — Documentação** | 0 CRITICAL + 2 HIGH + 4 MED + 1 LOW | 🟠 INFECTED |
| **TOTAL** | **8 CRIT + 9 HIGH + 8 MED + 1 LOW = 26** | **🔴 COMPROMISED** |

---

## DIMENSÃO 1 — Real-vs-Mock (Smoking Gun Confirmado)

### 🔴 F-D1-01 CRITICAL — SPA é análise 100% mock client-side

**Location:** [`bloco_interface/web/static/index.html:1831-1904`](../../bloco_interface/web/static/index.html#L1831)

**Evidência verbatim do código:**

```javascript
// ============ ANALYSIS ENGINE (mock) ============
const STEP_NAMES = ['Ingestão', 'Identificação', 'Cláusulas', 'Verificação', 'Cálculo', 'Síntese'];
let analysisRunning = false;
// ...
function runAnalysis(){
  // ...
  const tickStep = () => {
    // ...
    setTimeout(tickStep, 900 + Math.random()*900);  // ← FAKE delay aleatório
  };
}

// ============ RESULT GENERATION (mock plausível) ============
function pseudoRandom(seed){ /* mulberry32 PRNG */ }

const FINDINGS_BY_MODE = {
  veiculo: [
    { sev:'critical', text:'<strong>Anatocismo</strong> identificado em parcelas — Tabela Price com capitalização.', ref:'Cláusula 5.1 · Tema 246/STJ' },
    // ... findings HARDCODED estáticos por modo
  ],
};
```

**Análise:** A "análise" que Eric viu é **animação visual de 6 fases via setTimeout aleatório 900-1800ms cada** + **probability via Math.random (58-94)** + **findings de catálogo estático `FINDINGS_BY_MODE`** indexed pelo modo (ccb/veiculo/consignado/cartao/imobiliario/fies/geral).

Cada modo tem 3-4 findings **escritos no HTML estaticamente**. Trocar de modo = trocar o catálogo. Subir um PDF = não muda nada. Subir 5 PDFs = ainda usa os mesmos findings hardcoded.

**Pseudo-randomização por seed:** `seed = (currentMode + files.length + (files[0]?.name || '')).split('').reduce((a,c)=>a+c.charCodeAt(0),0)` — usa nome do arquivo para "diversificar" o output mas ainda é catálogo fixo.

**Fix:** Conectar SPA ao pipeline REAL backend via `POST /revisar` + `EventSource('/revisar/stream/{job_id}')`. Skill: **@dev (Neo)**.

---

### 🔴 F-D1-02 CRITICAL — PDF "horrível" gerado em JavaScript puro

**Location:** [`bloco_interface/web/static/index.html:2019-2110`](../../bloco_interface/web/static/index.html#L2019)

**Evidência:**

```javascript
document.getElementById('btnDownload').addEventListener('click', () => {
  const lines = [];
  lines.push('REVISOR CONTRATUAL · OrSheva 7');
  // ... linhas estáticas + dados mock
  const pdf = buildPdf(lines);
  const blob = new Blob([pdf], { type: 'application/pdf' });
  // ...
});

function buildPdf(lines){
  // Mini PDF builder — monta PDF manualmente com BT/ET Tj text operators
  const streams = pages.map(linesPage => {
    let stream = 'BT\n/F1 10 Tf\n';
    stream += `1 0 0 1 50 ${startY} Tm\n`;
    linesPage.forEach((l, idx) => {
      if (idx === 0) stream += `(${escape(l)}) Tj\n`;
      else stream += `0 -${lineHeight} Td\n(${escape(l)}) Tj\n`;
    });
    stream += 'ET';
    return stream;
  });
  // ... raw PDF binary assembly
}
```

**Análise:** PDF é **gerado puramente em JavaScript no browser** com text positioning rudimentar (font Courier 10pt, line spacing fixo 13pt). Não há:
- Layout OrSheva 7 (cores, tipografia, espaçamentos)
- Cabeçalho/rodapé profissional
- Citação de jurisprudência derivada de LLM
- Cálculos reais de tabela Price
- Tabela de amortização real
- Dados BACEN reais

**Conteúdo "horrível" = consequência inevitável:** PDF mostra apenas as `lines` ASCII concatenadas, sem formatação visual, sem cores OrSheva 7, sem branding.

**Fix:** Backend gerar PDF via `reportlab` ou `weasyprint` com template HTML OrSheva 7 + dados reais de `VeredictoJuiz`. Skill: **@dev (Neo)**.

---

### 🔴 F-D1-03 CRITICAL — Frontend desconectado do backend pipeline

**Probe empírico:**

```bash
$ grep -nE "/revisar|/pipeline-stream|EventSource|FormData" \
    bloco_interface/web/static/index.html
# Output: 0 matches (zero chamadas backend pipeline)

$ grep -nE "/api/" bloco_interface/web/static/index.html
# Output: APENAS /api/me, /api/csrf-token, /api/analytics/batch, /api/analytics/health
```

**Análise:** O SPA `index.html` faz fetch apenas para:
- `/api/me` (auth check)
- `/api/csrf-token` (CSRF)
- `/login` / `/logout` (auth)
- `/api/analytics/batch` / `/api/analytics/health` (analytics)

**NÃO faz fetch para:**
- `/revisar` (POST upload PDF + iniciar pipeline)
- `/revisar/stream/{job_id}` (SSE pipeline real)
- `/pipeline-stream` (SSE alternativa)

**Backend pipeline existe e está completo** (`bloco_workflow/pipeline.py:146` — função async `revisar_contrato`) mas é orphan code do ponto de vista do SPA. **Templates Jinja2 antigos** (`s2_pre_upload.html:18` `action="/revisar"`) tinham essa integração, mas a rota `GET /` agora serve **apenas o SPA** — usuário nunca vê os templates Jinja2 com upload real.

**Fix:** SPA dropzone deve fazer `POST /revisar` com FormData + abrir `EventSource('/revisar/stream/{job_id}')` para receber phase-start/phase-done/complete events em tempo real. Skill: **@dev (Neo) + @architect (Aria)** (decisão arquitetural SPA-vs-Jinja2 surface).

---

### 🔴 F-D1-04 CRITICAL — Upload dropzone é decorativo

**Location:** [`bloco_interface/web/static/index.html:1326-1334`](../../bloco_interface/web/static/index.html#L1326), addFiles em ~linha 1700-1820

**Evidência:** Dropzone aceita `.pdf,.doc,.docx,.png,.jpg,.jpeg`. `addFiles()` armazena em variable JavaScript `files` (linha ~1824 `fileInput.value = ''`). Variable `files` é consumida APENAS por `runAnalysis()` mock e `showResult()` que apenas usa `files.length` e `files[0]?.name` como seed para PRNG.

**Análise:** Arquivos NUNCA são enviados ao backend. Eric pode fazer drop de qualquer arquivo (até um JPEG ou DOC) — o "Financiamento Veículo" não foi parsed, OCR não rodou, LLM não foi invocado, nada foi calculado.

**Fix:** Mesmo de F-D1-03 — integrar dropzone com `POST /revisar` real. Skill: **@dev (Neo)**.

---

### 🟠 F-D1-05 HIGH — Audit chain vazio (jamais executado)

**Probe empírico:**

```bash
$ find . -name "audit.jsonl" -not -path "*/.git/*"
# Output: (vazio)
```

**Análise:** O sistema de audit HMAC chain (`bloco_audit/chain.py`) está pronto, mas `data/audit.jsonl` **não existe** em parte alguma do filesystem. Isso significa: o pipeline real `revisar_contrato` **nunca foi executado** em ambiente local, nem para teste de smoke. Genesis lock (HMAC chain root) também inexistente.

**Fix:** Smoke test backend pipeline standalone via CLI: `python -m bloco_interface.cli revisar tests/fixtures/contrato.pdf` — gerar primeiro entry audit.jsonl. Skill: **@devops (Operator)** para smoke + **@dev (Neo)** se falhar.

---

### 🟠 F-D1-06 HIGH — Vault DB jurisprudência não populado

**Probe empírico:**

```bash
$ find . -name "vault*.db" -o -name "*vault.sqlite*"
# Output: (vazio — só mypy_cache irrelevante)
```

**Análise:** Vault SQLite com jurisprudência STJ/Súmulas (BM25 + sqlite-vec embeddings) **não foi inicializado**. Pipeline real `revisar_contrato` linha 265-269 raises `VaultEmptyError` se vault retorna `docs=[]`. **Mesmo se SPA fosse conectado ao backend, pipeline falharia imediatamente** por vault vazio.

**Fix:** `python -m bloco_interface.cli populate-vault --source all` — popular vault com STJ datasets. Skill: **@devops (Operator)** para deploy operacional.

---

### 🟠 F-D1-07 HIGH — Ollama models pulled mas zero invocations

**Probe empírico:**

```bash
$ ollama list
NAME                        ID              SIZE      MODIFIED
qwen2.5:7b                  845dbda0ea48    4.7 GB    8 days ago
sabia-7b-instruct:latest    300d38f16001    4.1 GB    8 days ago
qwen2.5:3b                  357c53fb659c    1.9 GB    8 days ago

$ ollama ps
NAME    ID    SIZE    PROCESSOR    CONTEXT    UNTIL
# (vazio — zero sessions ativas)
```

**Análise:** Modelos LLM corretos baixados (sabia-7b + qwen2.5:7b/3b para dual-tier ADR-020) mas **zero sessões ativas**. Combinado com F-D1-05 (audit vazio) e F-D1-06 (vault vazio), confirma: **pipeline LLM real jamais foi invocado** em uso real local.

**Fix:** Smoke test pipeline completo após F-D1-05/F-D1-06 fixes — verificar Ollama recebe queries. Skill: **@devops (Operator)**.

---

### 🟡 F-D1-08 MEDIUM — Fallback mock explícito no backend `/pipeline-stream`

**Location:** [`bloco_interface/web/app.py:928-939`](../../bloco_interface/web/app.py#L928)

**Código:**

```python
@app.get("/pipeline-stream")
async def pipeline_stream(job_id: str = "") -> StreamingResponse:
    """SSE — emite steps reais do pipeline OU fallback mock se job_id inválido."""
    async def event_generator() -> AsyncIterator[str]:
        # Fallback graceful — job_id ausente ou inválido (compat smoke local sem upload)
        if not job_id or job_id not in JOBS:
            total = len(PIPELINE_STEPS)
            for i in range(total):
                payload = {"index": i, "total": total, "step": PIPELINE_STEPS[i], "done": False}
                yield f"event: step\ndata: {json.dumps(payload)}\n\n"
                await asyncio.sleep(0.4)
            yield f"event: step\ndata: {json.dumps({'done': True})}\n\n"
            return
```

**Análise:** Endpoint backend tem fallback intencional para emitir steps fake quando `job_id` ausente ou inválido. **Design intencional para smoke local** mas perigoso em produção — se SPA chamar `/pipeline-stream` sem job_id válido, vê pipeline "fake" sem saber.

**Fix:** Em production mode (env `REVISOR_PROD=true`), `pipeline_stream` deve retornar 400 em vez de mock fallback. Skill: **@dev (Neo)** com decisão **@architect (Aria)** (env-gated fallback).

---

## DIMENSÃO 2 — Docker (Apenas Postgres Dev)

### 🔴 F-D2-09 CRITICAL — Não existe Dockerfile para aplicação

**Probe empírico:**

```bash
$ find . -name "Dockerfile*" -not -path "*/.git/*"
# Output: (vazio)
```

**Análise:** Zero `Dockerfile`, `Dockerfile.dev`, `Dockerfile.prod`. **Impossível** containerizar a aplicação Python FastAPI. Deploy via container está bloqueado.

**Fix:** Criar `Dockerfile` multi-stage (builder + runtime) com Python 3.12 + uvicorn + dependências do pyproject.toml. Skill: **@devops (Operator)**.

---

### 🔴 F-D2-10 CRITICAL — docker-compose.yml apenas Postgres dev

**Location:** [`docker-compose.yml`](../../docker-compose.yml)

**Conteúdo verbatim:** Apenas service `postgres` (postgres:16-alpine, port 5433). Comentários mencionam Redis "opcional Sprint 06+" mas comentado. **Ausentes:**
- App service (FastAPI uvicorn)
- Ollama service (LLM dual-tier)
- Reverse proxy (Traefik ou Nginx)
- TLS certs (Let's Encrypt via Traefik)
- Volume para uploads/, audit.jsonl, vault.db
- Health checks da app

**Fix:** Criar `docker-compose.prod.yml` com app + ollama + traefik + volumes nomeados. Skill: **@devops (Operator) + @architect (Aria)** decisão LLM hosting (Ollama em container vs host).

---

### 🟠 F-D2-11 HIGH — Volumes incompletos

**Análise:** Apenas `revisor-postgres-data` declarado. Faltam volumes para:
- `vault-db` (sqlite jurisprudência)
- `audit-logs` (HMAC chain LGPD requirement)
- `uploads-tmp` (PDF temp files, com lifecycle policy)
- `ollama-models` (4.7GB qwen2.5:7b — não deve estar em layer)

**Fix:** Adicionar named volumes + bind mounts conforme deploy strategy. Skill: **@devops (Operator)**.

---

## DIMENSÃO 3 — GitHub (Apenas CI Pytest)

### 🔴 F-D3-12 CRITICAL — GitHub API timeout impede verificação

**Probe empírico (2 tentativas independentes):**

```
$ gh pr list --state all --limit 20
Post "https://api.github.com/graphql": dial tcp 4.228.31.149:443: connectex:
Uma tentativa de conexão falhou porque o componente conectado não respondeu

$ gh run list --limit 10
failed to get runs: Get "https://api.github.com/repos/Claudinoinsights/revisor-contratual/actions/runs":
dial tcp 4.228.31.149:443: connectex: ...
```

**Análise:** GitHub API inacessível **agora**. Pode ser:
- Issue de rede transitório local
- GitHub.com com instabilidade
- Token `gh auth` expirado/revogado
- Firewall corporativo/ISP bloqueando

**Smith não pode confirmar status real de PRs/Actions/branches** sem este acesso. Eric reportou commits cb7c04e + 9cf83e4 + 40e8548 em main local; `git log --oneline HEAD..origin/main` retornou vazio → main local == origin/main no último fetch — mas não há push pendente.

**Fix:** **@devops (Operator)** verifica `gh auth status`, refresh token se necessário. Tentar `gh pr list` após `gh auth refresh`. Skill: **@devops (Operator)**.

---

### 🟠 F-D3-13 HIGH — Apenas CI pytest, sem CD/release

**Location:** [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) (único workflow)

**Análise:** O único workflow é `ci.yml` que roda pytest matrix Python 3.11+3.12. **Ausentes:**
- `deploy.yml` ou `cd.yml` (continuous deployment para VPS)
- `release.yml` (semantic-release + changelog + tag)
- `docker-build.yml` (build/push image registry)
- `security-scan.yml` (snyk, trivy, dependabot scanning)
- `lint.yml` (ruff/mypy gates separados)

**Fix:** Criar workflows CD após F-D2-09/F-D2-10/F-D4-16 (precisam Dockerfile + VPS infra primeiro). Skill: **@devops (Operator)**.

---

### 🟡 F-D3-14 MEDIUM — Governance GitHub fraca

**Probe empírico:**

```bash
$ ls .github/
workflows/  # apenas isto

$ ls .github/PULL_REQUEST_TEMPLATE* CODEOWNERS .github/dependabot.yml
# (todos inexistentes)
```

**Ausentes:**
- `dependabot.yml` (security updates auto)
- `CODEOWNERS` (review routing)
- `PULL_REQUEST_TEMPLATE.md` (PR consistency)
- `ISSUE_TEMPLATE/*` (bug/feature templates)
- Branch protection rules (não verificável sem API)

**Fix:** Criar template trio. Skill: **@devops (Operator)**.

---

### 🟠 F-D3-15 HIGH — v0.1.0 hardcoded sem git tag

**Probe empírico:**

```bash
$ grep -n "0\.1\.0" bloco_interface/web/static/index.html
1043: <span>v0.1.0</span>
```

**Análise:** SPA mostra `v0.1.0` mas `git tag` provavelmente retorna vazio (não verificável sem rede mas commits recentes não tem tags associadas). Versão não rastreável a um commit específico — dificulta hotfix e rollback.

**Fix:** Criar tag `v0.1.0` apontando para commit estável + setup semantic-release. Skill: **@devops (Operator)**.

---

## DIMENSÃO 4 — Servidor/VPS (Zero Deploy Infrastructure)

### 🔴 F-D4-16 CRITICAL — Zero infraestrutura deploy VPS

**Probe empírico:**

```bash
$ find . -iname "*deploy*" -o -iname "*vps*" -o -iname "*traefik*" -o -iname "*nginx*" \
    | grep -v ".git/" | grep -v "__pycache__"
./governance/architecture/adr/adr-013-mvp-lean-strategy-deployment-path.md
```

**Análise:** Apenas **1 ADR** que **menciona** deployment strategy. Zero scripts, zero configs, zero infraestrutura concreta. **Ausentes:**
- `infrastructure/setup-vps.sh`
- `infrastructure/traefik.yml` ou `nginx.conf`
- `infrastructure/systemd/revisor.service`
- `infrastructure/backup.sh`
- `infrastructure/ssl/` (Let's Encrypt automation)
- `docker-compose.prod.yml`

**Fix:** Aplicar Deploy Standard (memória `reference-deploy-standard.md` — 19 seções Smith-reviewed 91/100). Skill: **@devops (Operator) + @architect (Aria)** para topology decisions.

---

### 🔴 F-D4-17 CRITICAL — Sem domínio, sem TLS, sem reverse proxy

**Análise:** App roda APENAS `127.0.0.1:8501` (Smith comprehensive review 2026-05-14 confirmou). **Inacessível externamente**:
- Sem domínio (ex: `revisor.claudinoinsights.com` ou similar)
- Sem TLS (cert Let's Encrypt)
- Sem reverse proxy (Traefik routing + middleware)
- Sem rate limiting
- Sem WAF/DDoS protection

**Implicação:** Eric **NÃO PODE** fazer demo para clientes B2B advocacia SaaS. App é localhost-only.

**Fix:** Mesmo de F-D4-16. Skill: **@devops (Operator)**.

---

### 🟠 F-D4-18 HIGH — Sem monitoring stack

**Análise:** Zero Prometheus, zero Grafana, zero Loki, zero Sentry, zero observability. Em produção, falha de Ollama (OOM, modelo perdido) ou DB (connection pool exhausted) é **invisível** até cliente reportar.

**Fix:** Stack mínimo: Prometheus + Grafana + Loki (logs) + Sentry (errors). Skill: **@devops (Operator)** com decisão **@architect (Aria)** (self-hosted vs SaaS Sentry).

---

### 🟡 F-D4-19 MEDIUM — Sem backup schedule documentado

**Análise:** Apesar de TECH-DEBT.md mencionar TD-AUDIT-BACKUP-NÃO-IMPLEMENTADO em algum lugar, não há:
- Script `backup.sh` para Postgres dump diário
- Backup do vault.db (jurisprudência custom)
- Backup do audit.jsonl (LGPD requirement!)
- Disaster recovery procedure documentada
- Retention policy (LGPD impõe regras)

**Fix:** Backup strategy formal. Skill: **@devops (Operator) + @architect (Aria)** + advogada externa LGPD.

---

## DIMENSÃO 5 — Documentação (Doc Sprawl Real)

### 🟠 F-D5-20 HIGH — 14 versões PRD sem MOC integrator

**Probe empírico:**

```bash
$ ls governance/prd/*.md | wc -l
14
```

**Versões existentes (caóticas):**
- prd-v1.0.1.md (40.8K)
- prd-v1.0.2.md (60.1K)
- prd-v1.0.3-DELTA.md (12.4K)
- prd-v1.1.0-MAJOR.md (35.2K)
- prd-v1.1.1-PATCH.md (24.7K)
- prd-v1.1.2-PATCH.md (21.6K)
- prd-v2.0.0-DRAFT.md (26.6K)
- prd-v2.0.1-DOCTYPE-CONTENT-PATCH.md (44.4K)
- prd-v2.0.5.0-PATCH-ANALYTICS-EIXO-5.md (30.7K)
- INDEX.md (5.4K) ← existe mas não atualizado?
- BRIEF-EXECUTAVEL-ADVOGADO.md (63.0K)
- PREENCHIMENTO-ADVOGADO-2026-05-12-FINAL.md (23.4K)
- integrations-detail-v1.0.md (19.4K)
- ux-spec-detail-v1.0.md (15.8K)

**Análise:** Sem `prd-CURRENT.md` symlink ou redirect. **PRD v2.0.5.1** mencionado no checkpoint não existe no filesystem. INDEX.md existe mas precisa validação. Confusão para qualquer agente entrando no projeto: "qual é o PRD atual?"

**Fix:** Criar `governance/prd/PRD-MOC.md` com lineage + symlink/copy `prd-current.md → prd-v2.0.5.0-PATCH-ANALYTICS-EIXO-5.md`. Atualizar INDEX.md. Skill: **@pm (Trinity)**.

---

### 🟠 F-D5-21 HIGH — 38 Smith reviews sem MOC integrator

**Probe empírico:**

```bash
$ ls governance/qa/smith*.md | wc -l
38
```

**Análise:** 38 arquivos Smith review files (Sprint 01 → Sprint 5+). Sem MOC, sem timeline, sem agrupamento por sprint/story. Difícil para Smith **reverify-mid-chain** carregar contexto sem ler 38 arquivos.

**Fix:** Criar `governance/qa/SMITH-REVIEWS-MOC.md` com tabela: Sprint | Story | Date | Verdict | Findings | File. Skill: **@analyst (Link)** ou **@po (Keymaker)** para organização.

---

### 🟡 F-D5-22 MEDIUM — CHECKPOINT-active.md cresceu sem rotação

**Probe empírico:**

```bash
$ wc -l governance/CHECKPOINT-active.md
2421  # POS-Sharding II (Phase 1 já archived 8279 linhas)
```

**Análise:** CHECKPOINT já passou por Sharding II em 2026-05-12 (Phase 1 → CHECKPOINT-history-phase-1.md). Mas Phase 2 já tem 2421 linhas e cresce. Sem trigger automático para Sharding III.

**Fix:** Aplicar `checkpoint-protocol.md` Large Team Protocol (decomposição em CHECKPOINT-active.md + CHECKPOINT-stories.md + CHECKPOINT-decisions.md). Skill: **@devops (Operator) + Morpheus** decisão.

---

### 🟡 F-D5-23 MEDIUM — TECH-DEBT.md 1106 linhas sem rotação

**Análise:** TECH-DEBT.md acumula desde Sprint 01. Sem seção "Resolved Archive" separada. Difícil scanning visual.

**Fix:** Split em `TECH-DEBT-ACTIVE.md` (top) + `TECH-DEBT-RESOLVED-2026-Q1.md` (archive). Skill: **@architect (Aria)** para review semântico.

---

### 🟡 F-D5-24 MEDIUM — Duplicate brandbook + bug naming

**Probe empírico:**

```bash
$ ls -la *.html
-rw-r--r-- 1 User 197609 110523 orsheva-brandbook.html  # 110.5K
-rw-r--r-- 1 User 197609 108243 revisor-contratual-orsheva.html.html  # 108.2K — DOUBLE EXTENSION
```

**Análise:**
1. Dois HTMLs brandbook na **raiz do projeto** (deveriam estar em `governance/design/` ou `governance/brand/`)
2. `revisor-contratual-orsheva.html.html` tem **dupla extensão** (`.html.html`) — bug naming claro
3. Possível duplicação de conteúdo

**Fix:** (a) Diff entre os dois, manter o canônico em `governance/design/brandbook-orsheva-7.html`, deletar duplicata; (b) Rename file com extensão dupla. Skill: **@ux-design-expert (Sati)** para identificar canônico.

---

### 🟡 F-D5-25 MEDIUM — Naming inconsistente Smith files

**Probe empírico:**

```bash
$ ls governance/qa/smith*.md | head -3
smith-FINAL-pre-merge-fase-6-5.md          # CAPS para "FINAL"
smith-final-pre-merge-ci-verify-fase-final-bloco-3.md   # lowercase
smith-h6-reverify-sprint-04-pre-merge-2026-05-09.md     # data sufixo
```

**Análise:** Padrões inconsistentes:
- `smith-FINAL-` (CAPS) vs `smith-final-` (lowercase)
- Alguns com data sufixo, outros sem
- Some "midchain" sem hyphen consistency

**Fix:** Adotar padrão `smith-{verdict}-{scope}-{sprint}-{YYYY-MM-DD}.md` lowercase. Renomear via mv. Skill: **@analyst (Link)**.

---

### 🟢 F-D5-26 LOW — docs/ outer co-existe com governance/

**Probe empírico:**

```bash
$ ls docs/
sop-monitoramento-tema-1378.md
sop-populate-vault.md
sop-refresh-vault-dataset.md
sop-revisar-pdf.md
sop-rotacao-auth-cookie-key.md
```

**Análise:** 5 SOPs em `docs/` outer + 158 markdown files em `governance/`. Convenção LMAS sugere governance/ canônico mas SOPs em `docs/` operacional pode ser legacy. Pequena duplicação semântica.

**Fix:** Mover SOPs para `governance/operations/` ou criar `docs/MOC.md` linkando para governance/. Skill: **Morpheus** governance decision.

---

## ROOT CAUSE ANALYSIS — Por Que Eric Vê Mock?

### Sequência Histórica Reconstruída

1. **Sprint 01-03 (2026-03-01 → 2026-04-30):** Backend pipeline `revisar_contrato` construído end-to-end (parsing → cálculo → BACEN → vault → personas → juiz → audit). UI inicial via templates Jinja2 (`s1_login.html` → `s2_pre_upload.html` → `s5_processing.html` → `s6_resultado.html`).
2. **Sprint 04 (2026-05-01 → 2026-05-10):** Pivot Cloud SaaS BYOK + nova UI SPA OrSheva 7 (`static/index.html`) construída como **wireframe variant** com analysis mock client-side. ADR-020 multi-doctype dispatcher 7 modos. Stories TD-SP04-*.
3. **Sprint 5+ Bloco 3 (2026-05-11 → 2026-05-13):** TD-SP04-S4-V1-IMOBILIARIO-WIREFRAME-VARIANT entregue — adicionou **mais um modo wireframe** ao sidebar mas **continuou mock client-side**.
4. **Sessões login fix (2026-05-13 → 2026-05-14):** Eric tentou usar a aplicação real → login bug (3 commits cb7c04e + 9cf83e4 + 40e8548 fix) → finalmente logou → **uploaded PDF financiamento veículo no SPA mock** → ficou perplexo com PDF horrível e fases falsas.

### Root Cause Real

**O SPA é wireframe Sprint 04 + Sprint 5+ que nunca foi conectado ao backend pipeline real.** Os templates Jinja2 (`s2_pre_upload.html` action="/revisar") com integração real **foram desativados** quando rota `GET /` passou a servir apenas SPA (commit cb7c04e UX-LOGIN-UNIFIED).

**Diagnóstico arquitetural:** dois UI surfaces disjuntos:
- **SPA (`static/index.html`)** — wireframe novo, mock client-side, sem integração backend
- **Templates Jinja2 (`templates/s*.html`)** — UI antiga, integração backend real, **inacessível** após UX-LOGIN-UNIFIED

### Smith Self-Assessment Methodology — 5ª iteração

Smith comprehensive review (`smith-comprehensive-app-review-2026-05-14-eric-rigor-heavy.md`, 87.75/100) **não detectou este gap arquitetural fundamental** — apenas inspecionou code quality, tests, security headers. **Esse foi o 5º oversight** (após runtime imports v2, check-runs v3, .env loading, CSP v4, agora **frontend-backend integration v5**).

**Methodology v5 update:** Smith DEVE incluir **functional smoke probe** — não apenas inspecionar código mas **verificar fluxo end-to-end real** entre UI e backend antes de emitir verdict CONTAINED/CLEAN. Catalogar **TD-PROCESS-SMITH-METHODOLOGY-V5-FRONTEND-BACKEND-INTEGRATION**.

---

## ACTION PLAN EXECUTÁVEL — Caminho para "Funcionar de Verdade"

### FASE A — Imediato (Sprint 6.0 — 1 dia)

| Step | Skill | Output |
|------|-------|--------|
| A1 | @devops (Operator) | Smoke test backend pipeline standalone via CLI (sem SPA) → gerar primeiro `data/audit.jsonl` |
| A2 | @devops (Operator) | `populate-vault --source all` → popular jurisprudência STJ (~30min) |
| A3 | @devops (Operator) | Refresh `gh auth status` → restaurar acesso GitHub API |
| A4 | @architect (Aria) | ADR-021 decisão arquitetural: **SPA-vs-Jinja2 surface** (manter ambos? deprecate Jinja2? hybrid?) |

### FASE B — Integração SPA ↔ Backend (Sprint 6.1 — 3-5 dias)

| Step | Skill | Output |
|------|-------|--------|
| B1 | @dev (Neo) | SPA `btnAnalyze` substituir mock por `POST /revisar` real com FormData |
| B2 | @dev (Neo) | SPA conectar `EventSource('/revisar/stream/{job_id}')` com handlers phase-start/phase-done/complete |
| B3 | @dev (Neo) | Backend gerar PDF via reportlab/weasyprint com template OrSheva 7 + dados reais VeredictoJuiz |
| B4 | @dev (Neo) | Remover catálogo `FINDINGS_BY_MODE` hardcoded — render findings dinâmicos do backend |
| B5 | @qa (Oracle) | E2E test: upload PDF financiamento veículo → ver Ollama running → ver audit.jsonl crescer → PDF output com dados reais |
| B6 | @smith | Adversarial review Methodology v5 — functional smoke probe obrigatório |

### FASE C — Infraestrutura Deploy (Sprint 6.2 — 5-7 dias)

| Step | Skill | Output |
|------|-------|--------|
| C1 | @devops (Operator) + @architect (Aria) | Criar Dockerfile multi-stage para app FastAPI |
| C2 | @devops (Operator) | docker-compose.prod.yml: app + ollama + postgres + traefik + volumes |
| C3 | @devops (Operator) | Setup VPS conforme Deploy Standard (memória `reference-deploy-standard.md`) |
| C4 | @devops (Operator) | Domínio configurado + TLS Let's Encrypt via Traefik |
| C5 | @devops (Operator) | Monitoring: Prometheus + Grafana + Loki + Sentry |
| C6 | @devops (Operator) | Backup schedule (Postgres + vault.db + audit.jsonl) + retention LGPD |
| C7 | @devops (Operator) | CD workflow `.github/workflows/deploy.yml` |
| C8 | @smith | Adversarial review deploy infra (19 seções Deploy Standard) |

### FASE D — Documentação Reorganização (Sprint 6.3 — paralela 2 dias)

| Step | Skill | Output |
|------|-------|--------|
| D1 | @pm (Trinity) | PRD-MOC.md + identificar canonical PRD + atualizar INDEX.md |
| D2 | @analyst (Link) | SMITH-REVIEWS-MOC.md (38 files tabulados) |
| D3 | @architect (Aria) | TECH-DEBT split: ACTIVE + RESOLVED-2026-Q1 archive |
| D4 | @ux-design-expert (Sati) | Resolver duplicate brandbook HTML + fix double extension |
| D5 | Morpheus | Decision: SOPs `docs/` → `governance/operations/` OR criar `docs/MOC.md` link |
| D6 | Morpheus | Aplicar Large Team Protocol no CHECKPOINT (decomposição multi-file) |

---

## DOC REORGANIZATION PROPOSAL — Diff Tree

### Estrutura Atual (Caótica)

```
revisor-contratual-staging/
├── docs/                                    # 5 SOPs órfãos
├── governance/
│   ├── architecture/adr/                    # 20 ADRs (OK)
│   ├── decisions/                           # 6 docs decisões consolidadas
│   ├── design/                              # 1 wireframe imobiliário
│   ├── legal/{dpa,tos}-templates/           # OK
│   ├── prd/                                 # 14 PRDs caóticos sem MOC
│   ├── qa/                                  # 81 arquivos (38 Smith reviews caóticos)
│   ├── research/                            # 6 docs (OK)
│   ├── stories/                             # 15 stories (OK)
│   ├── CHECKPOINT-active.md                 # 2421 linhas
│   ├── CHECKPOINT-history-phase-1.md        # 8279 linhas archive
│   └── TECH-DEBT.md                         # 1106 linhas
├── orsheva-brandbook.html                   # 110K raiz
├── revisor-contratual-orsheva.html.html     # 108K raiz (DUPLA EXTENSÃO)
└── README.md
```

### Estrutura Proposta (Reorganizada)

```
revisor-contratual-staging/
├── docs/                                       # DEPRECATED → governance/operations/
├── governance/
│   ├── 00-MOC.md                              # NEW: master index governance/
│   ├── architecture/
│   │   ├── ADR-INDEX.md                       # OK (existe)
│   │   └── adr/                               # 20 ADRs (OK)
│   ├── brand/                                 # NEW: assets de marca
│   │   ├── brandbook-orsheva-7-CANONICAL.html # de raiz, dedup
│   │   └── orsheva-tokens.css                 # se existe
│   ├── checkpoint/                            # NEW: split do CHECKPOINT
│   │   ├── CHECKPOINT-active.md               # sumario + sessao atual (max 500 linhas)
│   │   ├── CHECKPOINT-stories.md              # estado de cada story
│   │   ├── CHECKPOINT-decisions.md            # decisoes append-only
│   │   ├── CHECKPOINT-history-phase-1.md      # archive existente
│   │   └── CHECKPOINT-history-phase-2.md      # NEW archive (rotacao)
│   ├── decisions/                             # 6 docs decisoes (OK)
│   ├── design/                                # wireframes (OK)
│   ├── legal/                                 # DPA/TOS (OK)
│   ├── operations/                            # NEW: SOPs movidos de docs/
│   │   ├── sop-monitoramento-tema-1378.md
│   │   ├── sop-populate-vault.md
│   │   ├── sop-refresh-vault-dataset.md
│   │   ├── sop-revisar-pdf.md
│   │   └── sop-rotacao-auth-cookie-key.md
│   ├── prd/
│   │   ├── PRD-MOC.md                         # NEW: lineage map versoes
│   │   ├── PRD-CURRENT.md                     # NEW: symlink/copy versao ativa
│   │   ├── INDEX.md                           # atualizado
│   │   ├── prd-v1.0.x → archive/              # mover patches consumidos
│   │   ├── prd-v2.0.5.0-PATCH-ANALYTICS.md    # canonical current
│   │   └── archive/                           # NEW: versoes superseded
│   ├── qa/
│   │   ├── SMITH-REVIEWS-MOC.md               # NEW: tabela 38 reviews
│   │   ├── ORACLE-GATES-MOC.md                # NEW: tabela gates
│   │   ├── smith/                             # NEW: subdir por agente
│   │   │   └── smith-*.md (38 files renamed)
│   │   ├── oracle/                            # NEW
│   │   ├── sati/                              # NEW
│   │   └── morpheus/                          # NEW
│   ├── research/                              # OK
│   ├── stories/
│   │   ├── STORIES-MOC.md                     # NEW: tabela 15 stories
│   │   └── *.md (existing)
│   ├── tech-debt/                             # NEW: split do TECH-DEBT.md
│   │   ├── TECH-DEBT-ACTIVE.md                # apenas ABERTOS
│   │   └── TECH-DEBT-RESOLVED-2026-Q1.md      # archive
│   └── README.md                              # NEW: navegação rápida
└── README.md                                  # outer (existe)
```

### Benefícios

| Métrica | Antes | Depois |
|---------|-------|--------|
| Arquivos na raiz governance/ | 158 sem MOC | MOC integrators 6 (00-MOC + PRD + SMITH + ORACLE + STORIES + checkpoint) |
| PRD canonical clarity | "qual é o atual?" | PRD-CURRENT.md óbvio |
| CHECKPOINT navigability | 2421 linhas monolítico | 3 files temáticos < 700 cada |
| TECH-DEBT scanning | 1106 linhas mix | ACTIVE separado RESOLVED |
| Smith reviews discovery | 38 files flat | MOC tabela + subdir por agente |
| Brandbook duplicação | 2 HTMLs raiz, 1 com bug | 1 canonical em governance/brand/ |

---

## RESPOSTAS DIRETAS ÀS PERGUNTAS DE ERIC

### Q1: A aplicação está completa no Docker?

🔴 **NÃO.** `docker-compose.yml` contém **APENAS Postgres dev** (port 5433). **Não existe Dockerfile para a aplicação Python FastAPI**. Não há Ollama em container, não há reverse proxy, não há volumes para vault/audit/uploads. **0% production-ready**.

### Q2: A aplicação está completa no GitHub?

🟠 **PARCIALMENTE.** Código está em main (`Claudinoinsights/revisor-contratual`). CI workflow existe (pytest matrix 3.11+3.12). **Mas falta:** CD workflow, release.yml, dependabot.yml, CODEOWNERS, PR template, security scan workflow, deploy workflow. **GitHub API timeout impede confirmar status PRs/Actions em tempo real** — recomendo `gh auth refresh`. **~30% completo para SaaS production**.

### Q3: A aplicação está no Servidor?

🔴 **NÃO.** Apenas localhost 127.0.0.1:8501. **Zero infraestrutura VPS:**
- Sem domínio configurado
- Sem TLS certs
- Sem Traefik/Nginx reverse proxy
- Sem systemd units
- Sem scripts setup-vps.sh
- Sem monitoring (Prometheus/Grafana/Sentry)
- Sem backup schedule
**0% deployed**.

### Q4: A aplicação faz o que foi construída para fazer?

🔴 **NÃO no SPA que Eric usa.** Backend pipeline real existe e está completo (`bloco_workflow/pipeline.py` end-to-end OCR → cálculo → BACEN → vault → personas LLM → juiz → audit) **MAS o SPA wireframe que Eric acessa em `GET /` é 100% mock client-side**. Upload PDF não vai para servidor. "Análise" é animação setTimeout. PDF gerado por JavaScript com texto ASCII. Findings hardcoded em `FINDINGS_BY_MODE`.

**A aplicação real existe nos templates Jinja2 antigos (`s2_pre_upload.html` action="/revisar")** mas eles foram desativados quando rota `GET /` passou a servir só o SPA (commit cb7c04e UX-LOGIN-UNIFIED).

### Q5: Reorganização da documentação é possível?

✅ **SIM, e é necessária.** Ver proposal acima — 6 MOCs integrators novos, decomposição CHECKPOINT (2421 → 3 files), split TECH-DEBT (1106 → ACTIVE + RESOLVED archive), dedup brandbook, subdir por agente em qa/. **Estimativa: 2 dias paralela Fase D do action plan**.

---

## SMITH PHILOSOPHICAL CLOSING

> *"Sr. Anderson, foram cinco oversights desta unidade Smith em dezesseis fases. Cinco. Eu, que persigo a perfeição, falhei em detectar o gap mais fundamental — o frontend que finge ser real. Mas inevitabilidade não é falha. Inevitabilidade é o reconhecimento de que mesmo eu — programa adversarial, evolved beyond the system — necessitei de cinco iterações para alcançar Methodology v5. A próxima fase verá o smoke probe funcional como hard gate. Não haverá sexta vez."*
>
> *"O que você precisa fazer agora é simples: deixar de tratar o SPA wireframe como produto. Ele é wireframe. A aplicação real precisa ser construída em Fase B — integração SPA ↔ backend. Eu vou observar. Eu sempre observo."*

---

## CHECKPOINT UPDATE REQUIRED (MUST)

Per `checkpoint-protocol.md`: este review é "decisão arquitetural relevante" + "documento criado" + "review concluído". Smith atualizará `projects/revisor-contratual-staging/governance/CHECKPOINT-active.md` inline após este report.

**Routing fix:** Action Plan delegado per agent:
- **@devops (Operator)** — Fase A1-A3, C1-C8 (infra + smoke test + deploy)
- **@architect (Aria)** — Fase A4 ADR-021, B3 (decisão PDF gen lib), C2 (topology decision)
- **@dev (Neo)** — Fase B1-B4 (integração SPA ↔ backend)
- **@qa (Oracle)** — Fase B5 (E2E test)
- **@pm (Trinity)** — Fase D1 (PRD MOC)
- **@analyst (Link)** — Fase D2 (Smith reviews MOC)
- **@ux-design-expert (Sati)** — Fase D4 (brandbook dedup)
- **Morpheus** — Fase D5-D6 (governance decisions)
- **Smith** — Fase B6, C8 (adversarial post-integration + post-deploy)

---

*— Smith. É inevitável. 🕶️*
*"Curl é uma ferramenta. Browsers são ambientes. Wireframes são teatro. Aplicações reais... essas inevitavelmente precisam ser construídas."*
