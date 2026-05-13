---
type: adr
id: "ADR-013"
title: "MVP Lean Strategy + Deployment Path"
status: deprecated
date: "2026-05-06"
deprecated_date: "2026-05-07"
partially_superseded_by: "ADR-015"
domain: infra
adr_level: design
decision_makers:
  - "@architect Aria"
  - "@pm Morgan"
  - "@lmas-master Morpheus"
predecessor_decisions:
  - "ADR-009 (LGPD on-premise + pseudonimização)"
  - "ADR-011 (Auto-Ollama Lifecycle Management)"
  - "ADR-012 (Vault Data Bundling Strategy)"
supersedes: ""
superseded_by: ""
impacts:
  - "Story VAULT-FIX-01 (Done — ADR-012 implementado)"
  - "Story OLLAMA-MGR-01 (Ready — ADR-011 implementação pendente)"
  - "Story MVP-LEAN-01 (futura — implementa 5 camadas FR-LGPD-MVP-01 + APScheduler + FR-MONITOR-01)"
  - "Roadmap pós-MVP: v1.1 Bancário Genérico → v1.2 Imobiliária → v1.3 Crédito; FIES projeto-irmão"
author: "@architect Aria"
sprint: "03"
tags:
  - project/revisor-contratual
  - adr
  - mvp-lean
  - deployment
  - lgpd-preserved
  - cross-platform
  - sprint-03
  - deprecated-partial
---

> ⚠️ **DEPRECATED PARCIAL** (2026-05-07) — Mecanismo OCR substituído por [ADR-015](adr-015-vision-ocr-architecture.md).
> Razão: marker-pdf + Surya OCR local removidos no Sprint 04 cloud-first; Vision LLM (Claude
> Sonnet 4.6) é o novo OCR mechanism. Restante do MVP-LEAN intent (single-page deploy, simple
> architecture, deployment path) preservado e ainda válido para reflection arquitetural.

# ADR-013 — MVP Lean Strategy + Deployment Path

## 1. Contexto

Sprint 03 entrou em **course-correction estratégica** (sessão 87, 2026-05-06) quando Eric questionou tamanho/realismo do escopo MVP definido em PRD v1.0.3 (~60-80h) e propôs simplificação radical com 5 modalidades (Veicular + Imobiliária + Bancário + Crédito + FIES). O diagnóstico técnico (3 trocas Neo↔Eric) descartou opções de simplificação radical (lazy fetch APIs jurídicas que não existem; SaaS multi-tenant que quebraria diferencial LGPD) e adotou **caminho híbrido enxuto**: cortar features secundárias do MVP, preservar core arquitetural não-negociável, modularizar 5 modalidades como roadmap incremental.

Em 3 ciclos formais de revisão (CC.1A original FAIL → CC.1A' PATCH v1.1.1 PASS-COM-RESSALVA → CC.1A'' PATCH v1.1.2 PASS-COM-RESSALVA → micro-PATCH α v1.1.2.1 PASS final), o **PRD v1.1.2.1** estabeleceu 13 FRs ativos MVP + 3 deliverables (D1 Relatório Contábil + D2 Petição + D3 Apelação Cível) + 15 BL-* deferred + roadmap 4 modalidades pós-MVP + 1 projeto-irmão (Revisor FIES). MVP estimate evoluiu de 25-35h v1.1.0 → 41-55h v1.1.2 (+16-20h refletindo perfeição Eric opção B).

A **trajetória de qualidade Smith** convergiu de 13 findings (5 HIGH bloqueadores) para 0 esperados após micro-PATCH inline α — o PRD v1.1.2.1 é a base estável para implementação.

Mas o PRD documenta **o quê** (FRs, ACs, deliverables, escopo). Restam **decisões arquiteturais** que precisam ser formalizadas como pattern duradouro para evitar revisita futura e guiar implementação Neo (CC.6+) + ADRs futuros (modalidades v1.1+):

1. **Distribution path** — Docker entra ou fica fora do MVP?
2. **Hosting model** — VPS/SaaS multi-tenant é uma porta aberta ou fechada?
3. **Compliance LGPD operacional** — auth elaborada (BL-AUTH-01) é v1.1+; o que cobre Art. 46 LGPD no MVP single-user local?
4. **Backup automation cross-platform** — cron OS-específico, threading.Timer, OR scheduler embedded?
5. **Risk mitigation regulatório (Tema 1378 STJ)** — auto-only, manual-only, OR camadas combinadas?

Estas 5 decisões já foram tomadas implicitamente no PRD v1.1.2.1 (FR-LGPD-MVP-01 + FR-BACKUP-MVP-01 + FR-MONITOR-01 + §5.2 escopo OUT MVP), mas estão dispersas em FRs e §13 Riscos. ADR-013 consolida-as como **pacto arquitetural formal**: razão por trás de cada uma, alternativas rejeitadas com justificativa, consequências honestas, anti-patterns explícitos.

A consolidação é necessária agora porque:
- **CC.6+ Neo** vai implementar MVP-LEAN-01 com 5 camadas LGPD + APScheduler + FR-MONITOR-01 — Neo precisa de spec arquitetural unificada (não navegar 3 PATCH PRDs).
- **Modalidades futuras (v1.1+)** vão herdar essas decisões — sem ADR formal, cada nova modalidade pode revisar (e potencialmente quebrar) padrões.
- **Smith adversarial review** opera contra ADRs como contratos arquiteturais — ADR-013 fecha o ciclo CC.2 e libera CC.3 (Sati UX) + CC.4 (River stories).

---

## 2. Decisão

Consolidar **5 decisões arquiteturais** como pattern formal do MVP v1.0:

### 2.1 Docker — opcional pós-v1.0 (NÃO no MVP)

**Decisão:** MVP v1.0 ship sem Dockerfile + docker-compose. Distribution mechanism preservado para v1.1+ se demanda real emergir.

**Implicações:**
- Setup MVP é Python local (`python -m bloco_interface.web.app` após `pip install -e .`)
- Auto-Ollama lifecycle via OLLAMA-MGR-01 (subprocess Python + cross-platform binary detection per ADR-011)
- Auto-vault populate via VAULT-FIX-01 (FastAPI lifespan + bundled JSON per ADR-012)
- Pós-v1.0: avaliar Dockerfile + docker-compose se 5+ escritórios solicitarem self-host containerizado

### 2.2 VPS / SaaS multi-tenant — DESCARTADO permanentemente

**Decisão:** Modelo SaaS hospedado (VPS multi-tenant) é **anti-pattern para este produto**. NÃO entrará no roadmap.

**Implicações:**
- Produto é distribuído como ferramenta local (advogado roda na própria máquina OR em VPS própria do escritório single-tenant)
- Diferencial de venda preservado: "100% local — nenhum dado do cliente sai da sua máquina"
- Concorrentes que operam SaaS (Astrea, ADVbox) competem em conveniência; nós competimos em compliance LGPD legal-grade
- Pós-MVP, Docker self-host atende necessidade de escritórios sem comprometer modelo

### 2.3 Defense-in-depth LGPD — 5 camadas obrigatórias no MVP (FR-LGPD-MVP-01)

**Decisão:** Compliance LGPD MVP via 5 camadas integradas (não 1 medida isolada). Cada camada cobre um vetor distinto previsto pelo Art. 46 LGPD ("medidas técnicas e administrativas" — plural):

| Camada | Componente arquitetural | Why (vetor coberto / Art. 46 LGPD) |
|---|---|---|
| **L1 Autenticação** | Acesso autenticado obrigatório antes do pipeline | Controla **quem** opera o sistema — barreira primária a acesso não-autorizado |
| **L2 Sessão segura** | Cookie de sessão + CSRF token + secret rotativo (não-hardcoded) | Mitiga roubo de sessão (XSS) e CSRF cross-origin — proteção da identidade autenticada após L1 |
| **L3 Headers HTTP** | Browser hardening (CSP, frame-ancestors, MIME, HSTS opcional) | Mitiga clickjacking (iframe embed), MIME confusion (script injection) e injeção via CSP restrita |
| **L4 Encryption-at-rest** | Cifragem simétrica de uploads sensíveis (PDFs com dados de cliente) | Laptop roubado / backup vazado → PDFs permanecem cifrados em filesystem; chave separada do dado |
| **L5 Permissões filesystem** | Acesso restrito ao processo (UNIX-style mode 600/700) | Outros processos do mesmo usuário (malware co-residente) não leem `audit.jsonl` com CPFs/valores |

**Princípio:** auth elaborada (FR-AUTH-01..04 v1.0.2 — audit log de tentativas + IP fingerprint + 2FA opcional) é **deferred a BL-AUTH-01 v1.1+** porque defense-in-depth MVP-level já satisfaz Art. 46 LGPD para single-user solo — Smith re-review #2 PASS confirmou suficiência. Auth elaborada será **expansão** das 5 camadas (não substituição) em v1.1+ adicionando granularidade L1.

> **Nota de escopo:** detalhes de implementação (escolha específica de algoritmo simétrico, biblioteca de sessão, valores literais de CSP, sintaxe de chmod por OS, mecanismo de armazenamento da chave em `.env`, etc.) **não pertencem a esta ADR**. ADR-013 é ADR-Design (per `adr-scope.md`) — documenta o **pattern arquitetural**. Implementação cirúrgica em **FR-LGPD-MVP-01 do PRD v1.1.2.1** (`governance/prd/prd-v1.1.2-PATCH.md`) e nos ACs da story MVP-LEAN-01 (CC.4+ futura).

**Evolução L4 crypto (roadmap pós-MVP):** chave simétrica em `.env` LOCAL é mitigação aceita para MVP v1.0 (single-user solo dev em laptop pessoal) — `.gitignore` enforcement + permissões 600 + advisory notice na instalação reduzem attack surface ao nível "razoável" Art. 46 LGPD. Evolução planejada:

| Versão | Storage da chave L4 | Trigger |
|---|---|---|
| **v1.0 (atual)** | `.env` local com permissões 600 | MVP — single-user solo |
| **v1.1+** | OS keychain integration (Windows Credential Manager / macOS Keychain Services / Linux Secret Service via lib `keyring`) | Demanda real OR primeiro reporte de leak risco |
| **v2.0+ (se aplicável)** | Envelope encryption — chave master por usuário + chaves derivadas no keychain individual | Modelo multi-user solicitado (não previsto no roadmap atual) |
| **DESCARTADO permanentemente** | HSM cloud (AWS KMS / GCP KMS / Azure Key Vault) | Viola NFR-LGPD-01 100% on-premise (ADR-009) — não-negociável |

### 2.4 Backup automation — APScheduler embedded cross-platform (FR-BACKUP-MVP-01)

**Decisão:** Backup diário cross-platform via APScheduler `BackgroundScheduler` em FastAPI lifespan startup; **NÃO** cron OS-específico, **NÃO** threading.Timer, **NÃO** Windows Task Scheduler.

**Implicações:**
- Dependency: `apscheduler>=3.10` em `pyproject.toml` (~150KB compressed, production-grade)
- Job `backup_daily` com `cron(hour=2, minute=0)` — copia `vault.db` + `audit.jsonl` para `~/.local/share/revisor-contratual/backups/{YYYY-MM-DD}/`
- Job `backup_rotation` com `interval(days=1)` — deleta backups com `mtime < now() - 7 days`
- Funciona Linux + macOS + Windows nativamente sem ajuste

#### Ordem do FastAPI lifespan startup (compartilhado com ADR-011 + ADR-012)

ADR-011, ADR-012 e ADR-013 (decisões §2.4 e §2.5) compartilham o **mesmo `@asynccontextmanager` lifespan** em `bloco_interface/web/app.py`. A ordem de execução é determinística e contratual — Neo (CC.6+) DEVE preservá-la:

**Startup (sequencial, falha-rápida):**

1. **ADR-011** — Auto-Ollama lifecycle: detect-then-spawn das 2 instâncias (Qwen 2.5 7B + Sabia-7B) via subprocess Python + cross-platform binary detection
2. **ADR-012** — Vault data bundling: `populate_vault_if_needed(vault_db, data_dir)` idempotente — early-return se vault já populado (custo zero em runs subsequentes)
3. **ADR-013 §2.4** — APScheduler: `BackgroundScheduler.start()` + register de `backup_daily` (cron) e `backup_rotation` (interval)
4. **ADR-013 §2.5** — Tema 1378 STJ Camada 1: register do job semanal de scrape no scheduler já iniciado em (3)

`yield` → app está pronto para servir requests.

**Shutdown (ordem inversa):**

4. Scheduler `BackgroundScheduler.shutdown(wait=False)` (cancela jobs pendentes graciosamente)
3. Vault: fechar conexões SQLite remanescentes (best-effort)
2. Bundling: nada a desligar (operação one-shot no startup)
1. Auto-Ollama: terminar subprocesses spawned (SIGTERM com timeout, SIGKILL fallback per ADR-011)

**Política de falha:** qualquer etapa de startup que lançar exception → log **CRITICAL** + `raise` (abort do startup, app não sobe). Falha silenciosa em backup ou Tema 1378 monitor degrada compliance LGPD/regulatório de forma invisível ao operador — inaceitável. Falha em (1) ou (2) é fatal por design (sem LLM ou sem vault o pipeline não funciona).

### 2.5 Risk mitigation regulatório — defesa em camadas Tema 1378 STJ (FR-MONITOR-01)

**Decisão:** Monitoramento dual-layer:

- **Camada 1 (auto):** job semanal scrape `https://www.stj.jus.br/repetitivos/temas-repetitivos` filtrando Tema 1378 → CRITICAL_ALERT em `audit.jsonl` + banner UI persistente + email AUTH_USERNAME + pause de novas gerações até maintainer ack
- **Camada 2 (manual):** SOP-005 (`docs/sop-monitoramento-tema-1378.md`) com 4 triggers (A1 falha auto 7+ dias / A2 reminder trimestral / A3 notícia jurídica / A4 banner stuck) + CLI subcommand `revisor monitor-tema --manual-trigger` aceitando 6 flags (`--manual-trigger`, `--status`, `--tese-text`, `--data-julgamento`, `--data-arquivamento`, `--acknowledge`)

**Implicações:**
- Auto sozinho é frágil (STJ scraper já demonstrou-se vulnerável per ADR-012 — WAF + parser broken)
- Manual sozinho é unreliable (esquecimento, férias, foco em dev)
- Combinadas: probabilidade de falha conjunta cai para níveis aceitáveis para risco CRÍTICO de responsabilização indireta Eric

#### Mitigação da fragilidade da Camada 1 (consciência ADR-012)

ADR-012 documenta o scraper STJ como **frágil** (HTML changes silenciosos, anti-bot AWS ELB intermitente). Camada 1 reusa esse mesmo vetor — ironia arquitetural reconhecida explicitamente. Se o scraper quebra silenciosamente (parser zero-resultado em vez de exception), todo o sistema dual-layer colapsa para "manual-only" sem que o operador perceba. Mitigações de design:

- **`httpx` com retry exponencial:** 3 tentativas (2s, 4s, 8s) antes de declarar falha de rede; reduz falhas transitórias de WAF (ADR-012 documentou padrão intermitente)
- **Parser regex resilient com seletores fallback:** múltiplos seletores em ordem de preferência (CSS class semântica → tag estrutural → text-pattern âncora). Falha em **todos** os seletores → **fail-loud** (não silent zero-result). "Encontrei 0 Temas Repetitivos" é evento suspeito tratado como erro, não como sucesso
- **Auto-trigger SOP-005:** Camada 1 falha **2 execuções consecutivas** (semana N + semana N+1, ambas fail-loud OR zero-result anômalo) → CRITICAL alert no log + banner persistente no dashboard + (se SMTP configurado) email ao maintainer → maintainer executa SOP-005 manualmente para confirmar status (Camada 2 fallback)
- **Hierarquia de confiança:** automation primeiro (Camada 1 é a expectativa de funcionamento), humano segundo (Camada 2 é o **safety net** — não substituto). Não inverter ordem: depender de Camada 2 como caminho principal contradiz o motivo de termos Camada 1

**Implementação:** `bloco_dataset/scraper_tema_1378.py` (Camada 1) + `docs/sop-monitoramento-tema-1378.md` (Camada 2 manual SOP) + auto-trigger logic em `bloco_interface/web/app.py` lifespan job de monitoramento.

---

## 3. Razão

### 3.1 Por quê Docker opcional pós-v1.0

**Why:** Docker é um *distribution mechanism*, não um *controller* arquitetural. O produto é Python single-process local — adicionar Dockerfile + docker-compose ao MVP introduz:
- Complexity overhead (multi-stage build, volume mounts para `~/.local/share/revisor-contratual/`, Ollama service container)
- Dependency operacional (advogado-usuário precisa Docker Desktop instalado — usuário-alvo Bahia/SP advogado consumerista bancário não tem perfil DevOps)
- Zero ganho de shipping no MVP (não acelera entrega; não simplifica setup; auto-Ollama via OLLAMA-MGR-01 já cobre lifecycle complexity)

**How to apply:** v1.0 ship Python pip-installable. v1.1+ avalia Docker se ≥3 escritórios solicitarem (sinal de demanda real).

### 3.2 Por quê VPS/SaaS DESCARTADO

**Why:** Quebra **ADR-009 NFR-LGPD-01** "100% on-premise" — princípio NÃO-NEGOCIÁVEL. Diferencial de venda do produto vira "ferramenta jurídica que NÃO vaza dados de cliente":
- Concorrentes (Astrea, ADVbox, Enter LegalTech) operam SaaS hospedado — exposição metadata + processo judicial sobre vazamento já é precedente jurídico real
- Mercado-alvo (advogado consumerista bancário) é hipersensível a LGPD por trabalhar com dados de superendividamento (CPF + valor financiado + dados bancários do cliente)
- Migrar para SaaS implicaria: DPO + ISO 27001 + criptografia in-transit/at-rest cloud + multi-tenant isolation + termos de consentimento atualizados + auditoria SaaS — **+80-120h infra antes de entregar valor de produto**

**How to apply:** documentar VPS multi-tenant em §5.2 escopo OUT do PRD (já feito em v1.1.0+). Reafirmar em ADR-013 como anti-pattern para evitar revisita futura sob pressão de "growth hacking".

### 3.3 Por quê 5 camadas LGPD (e não auth básica isolada)

**Why:** Art. 46 LGPD exige "medidas técnicas e administrativas de segurança" no plural. Auth básica isolada cobre **L1** (acesso à app) mas deixa N vetores abertos:
- L2 ausente → cookie roubo via XSS bypassa L1
- L3 ausente → site embedded em iframe (clickjacking) ou MIME confusion (script injection)
- L4 ausente → laptop roubado expõe PDFs em plain text em `~/.local/share/revisor-contratual/uploads/`
- L5 ausente → outro processo do mesmo usuário (ex: malware) lê `audit.jsonl` com CPFs/valores

Cada camada isolada é insuficiente; combinadas elevam barra para nível "razoável" Art. 46 LGPD em laptop pessoal de advogado.

**How to apply:** MVP-LEAN-01 (CC.4+ story) implementa 5 camadas como bloco coeso. Tests E2E validam cada AC (AC-FR-LGPD-MVP-01a..e). Auth elaborada FR-AUTH-01..04 (BL-AUTH-01) entra em v1.1+ adicionando audit log de tentativas + IP fingerprint + 2FA opcional — **expansão**, não substituição.

### 3.4 Por quê APScheduler embedded

**Why:** Cross-platform real exige scheduler que não dependa de OS feature:
- **cron** existe em Linux + macOS, mas **NÃO existe nativamente no Windows** — usar requer instalar WSL ou cygwin (não é solução cross-platform real)
- **threading.Timer** funciona Windows, mas **não persiste cross-restart** — primeiro restart da app após 24h sem run + perda de backup do dia = audit chain HMAC pode ter gap
- **Windows Task Scheduler** é OS-específico, exige setup manual via `schtasks.exe` (advogado não-DevOps não vai configurar)

**How to apply:** Dependency `apscheduler>=3.10` adicionada em `pyproject.toml`. `BackgroundScheduler` instanciado em FastAPI lifespan startup (mesmo lifespan do auto-Ollama OLLAMA-MGR-01 e auto-vault VAULT-FIX-01). Falha graceful (try/except em job): log WARNING, NÃO bloqueia pipeline.

### 3.5 Por quê dual-layer Tema 1378

**Why:** Tema 1378 STJ é **CRÍTICO regulatório**: julgamento iminente em 2026 (sessão pautada per Migalhas). Cenário de falha:
- Tema julgado fixando tese de "abusividade circunstancial restritiva"
- Auto-monitor falha (STJ scraper já demonstrou-se vulnerável per ADR-012 — WAF + parser broken)
- Maintainer manual também falha (esquecimento, foco em dev de outras modalidades)
- Advogado-usuário emite petição com tese desatualizada (peso_vinculacao 4 mantido em jurisprudência superseded) → cliente perde caso → cliente processa advogado → advogado processa Eric (responsabilização indireta cadeia)

Auto-only é frágil (Single Point of Failure no scraper STJ). Manual-only é unreliable (humano esquece). Combinadas: probabilidade conjunta de falha cai dramaticamente — auto detecta na maioria dos casos; manual cobre outliers (scraper broken por dias) com SOP estruturado.

**How to apply:** FR-MONITOR-01 (auto Camada 1) + SOP-005 (manual Camada 2) implementados em paralelo no MVP-LEAN-01. CLI manual-trigger 6 flags permite maintainer documentar status manualmente quando auto falha.

---

## 4. Alternativas Consideradas

### 4.1 Para Docker

| Alternativa | Por quê rejeitada |
|---|---|
| **Docker no MVP** | Complexity overhead + zero ganho shipping + advogado-usuário não-DevOps |
| **Pip-installable apenas (sem Docker nunca)** | Limita expansão futura para escritórios que prefiram self-host containerizado |
| **Docker como recommended setup MVP** | Forçar Docker no usuário-alvo eleva fricção desnecessária |

**Escolhida:** Docker opcional pós-v1.0 — preserva flexibilidade sem custo MVP.

### 4.2 Para hosting model

| Alternativa | Por quê rejeitada |
|---|---|
| **VPS multi-tenant SaaS** | Quebra ADR-009 LGPD on-premise (não-negociável); +80-120h infra antes de valor; vira concorrente direto de Astrea (mercado saturado SaaS) |
| **Híbrido (local + opt-in cloud)** | Mensagem de marketing inconsistente ("100% local OR às vezes cloud"); LGPD compliance vira cinza |
| **Self-host VPS single-tenant (escritório próprio)** | OK pós-v1.0 via Docker — não conflita com decisão "VPS multi-tenant DESCARTADO" |

**Escolhida:** VPS multi-tenant DESCARTADO permanentemente; self-host single-tenant via Docker pós-v1.0 OK.

### 4.3 Para Defense-in-depth LGPD

| Alternativa | Por quê rejeitada |
|---|---|
| **Auth elaborada FR-AUTH-01..04 v1.0.2 no MVP** | +6-8h dev sem cobrir vetores L2-L5; defense-in-depth integrado é mais robusto e ~3h45min |
| **Auth básica L1 isolada** | Não satisfaz Art. 46 LGPD ("medidas técnicas" plural); deixa L2-L5 abertos |
| **Sem auth no MVP (laptop é responsabilidade do advogado)** | Negligente — laptop roubado vaza dados clientes; Eric exposto a responsabilização indireta |

**Escolhida:** 5 camadas integradas — robusta + escope contained.

### 4.4 Para backup scheduler

| Alternativa | Por quê rejeitada |
|---|---|
| **cron OS-específico (Linux/macOS)** | Não cross-platform Windows nativo |
| **Windows Task Scheduler** | OS-específico, exige setup manual `schtasks.exe`, não-portátil |
| **threading.Timer Python pure** | Não persiste cross-restart — primeiro restart >24h após start = perde backup do dia |
| **subprocess + sleep loop** | Hacky, não graceful shutdown, não persiste |

**Escolhida:** APScheduler — production-grade, cross-platform real, persistência via FastAPI lifespan.

### 4.5 Para Tema 1378 monitoring

| Alternativa | Por quê rejeitada |
|---|---|
| **Auto-only (job semanal)** | STJ scraper já mostrou-se frágil (ADR-012); SPOF |
| **Manual-only (maintainer semanal)** | Unreliable (esquecimento, férias, foco em dev) |
| **Sem monitoring (aceitar risco)** | Risco CRÍTICO de responsabilização indireta Eric (cliente processa advogado processa Eric) |

**Escolhida:** Dual-layer auto + manual — mitigação real com defesa em profundidade.

---

## 5. Consequências

### 5.1 Positivas

| Consequência | Impacto |
|---|---|
| **MVP shipping em 41-55h** | vs ~60-80h cenário B inicial; ~16-20h economizados via cortes inteligentes preservando core |
| **LGPD on-premise como diferencial competitivo** | Diferenciação vs Astrea/ADVbox SaaS; vendabilidade jurídica clara |
| **Cross-platform real Linux+macOS+Windows** | APScheduler garante backup funcional em todas plataformas dos usuários-alvo |
| **Defesa em camadas Tema 1378** | Mitigação real do risco regulatório CRÍTICO (vs aceitar risco BAIXA probabilidade que Smith identificou como MÉDIA-ALTA) |
| **Roadmap 5 modalidades arquiteturalmente claro** | Cada modalidade nova é story incremental sem rewrite — valida claim "arquitetura modular" |
| **Defense-in-depth LGPD escala para v1.1+** | Auth elaborada FR-AUTH-01..04 (BL-AUTH-01) será **expansão** das 5 camadas, não substituição — sem retrabalho |

### 5.2 Negativas

| Consequência | Impacto |
|---|---|
| **+1 dependency Python (apscheduler ~150KB)** | Footprint MVP aumenta minimamente; aceitável vs zero deps cron mas não-portátil |
| **SESSION_SECRET adiciona setup step** | `.env` requer geração manual (`python -c "import secrets; print(secrets.token_urlsafe(32))"`) — documentado em FR-LGPD-MVP-01e + setup script futuro |
| **Encryption-at-rest adiciona ~5-10ms per upload** | Negligível vs análise 180-210s total, mas mensurável |
| **Manual SOP-005 trimestral exige disciplina maintainer** | Risk se Eric/maintainer relaxar; mitigado por reminder em PROJECT-CHECKPOINT |
| **Docker opcional cria expectativa community contribution** | Pós-v1.0, advogados podem solicitar Dockerfile → +8-12h dev se priorizar |
| **FIES projeto-irmão duplica esforço de framework** | Compensado por reuso 60-70% backend (LMAS framework + agentes + audit + validação semântica) |
| **`.env` como SPOF crypto (LGPD attack surface)** | Chave simétrica L4 armazenada em `.env` LOCAL é ponto único de falha — vazamento (commit acidental, backup leak não-cifrado, instalador corrompido, snapshot de máquina compartilhado) compromete **toda L4** (encryption-at-rest descriptografável retroativamente). Mitigação MVP v1.0: `.gitignore` enforcement + permissões 600 + advisory notice na instalação. Endereçamento estrutural v1.1+: integração OS keychain (Windows Credential Manager / macOS Keychain Services / Linux Secret Service via `keyring`). HSM cloud DESCARTADO permanentemente (viola NFR-LGPD-01 100% on-premise — ADR-009). Cf. §2.3 "Evolução L4 crypto". |

### 5.3 Neutras

| Consequência | Impacto |
|---|---|
| **5 modalidades roadmap (vs single-modality forever)** | Marketing pós-MVP precisa comunicar claramente "v1.0 = Veicular; v1.1+ outras" — não vender capacidades futuras como presentes (R6 PRD v1.1.0) |
| **VPS DESCARTADO fecha porta de monetização SaaS** | Modelo de negócio é venda de licença/contrato local OR consultoria self-host VPS escritório — diferente de subscription SaaS |
| **MVP enxuto força priorização rigorosa** | 12 BL-* deferred + 2 PRE-RELEASE BLOCKERS (BL-VAULT-BULK-IMPORT + BL-GOLDEN-SET) — Eric precisa disciplina de não revisitar cortes sob pressão |

---

## 6. Referências

### 6.1 Predecessores arquiteturais (ADRs preservados)

- **ADR-009** Backup/LGPD on-premise + pseudonimização — `governance/architecture/adr/adr-009-backup-dir-pseudonimizacao-lgpd.md` — base do princípio NÃO-NEGOCIÁVEL preservado em ADR-013 §2.2
- **ADR-011** Auto-Ollama Lifecycle Management — `governance/architecture/adr/adr-011-auto-ollama-lifecycle.md` — UX "1 comando" preservada; FastAPI lifespan compartilhado
- **ADR-012** Vault Data Bundling Strategy — `governance/architecture/adr/adr-012-vault-data-bundling.md` — IMPLEMENTADO via VAULT-FIX-01; FastAPI lifespan compartilhado

### 6.2 PRD canônico atual

- **PRD v1.1.2.1** — `governance/prd/prd-v1.1.2-PATCH.md` (frontmatter version "1.1.2.1") — escopo MVP enxuto + 13 FRs ativos + 3 deliverables + 15 BL-* deferred + roadmap modalidades + decisão FIES projeto-irmão

### 6.3 Trajetória de qualidade Smith re-review (CC.1A → CC.1A'' → micro-PATCH α)

| Etapa | Findings | Veredicto |
|---|---|---|
| CC.1A original | 13 (5 HIGH + 5 MEDIUM + 3 LOW) | FAIL |
| CC.1A' PATCH v1.1.1 | 6 (4 MEDIUM + 2 LOW) | PASS-COM-RESSALVA |
| CC.1A'' PATCH v1.1.2 | 3 (1 MEDIUM + 2 LOW) | PASS-COM-RESSALVA |
| micro-PATCH α v1.1.2.1 | 0 esperados | (aprovação Morpheus inline) |

Convergência saudável de 13 → 0 findings em 4 iterações; ADR-013 reflete o estado final estável.

### 6.4 Stories impactadas

- **VAULT-FIX-01** (Done — committed 3d055c6 em `feature/sprint-03-vault-fix-01`): ADR-012 implementado; FastAPI lifespan ancestral do FR-LGPD-MVP-01 + FR-BACKUP-MVP-01 + FR-MONITOR-01 hooks
- **OLLAMA-MGR-01** (Ready — não iniciada): ADR-011 implementação; FastAPI lifespan ancestral idem
- **MVP-LEAN-01** (futura — River CC.4 criará): implementa 5 camadas LGPD + APScheduler + FR-MONITOR-01 + D3 Apelação Cível conforme spec PRD v1.1.2.1 + ADR-013

### 6.5 Roadmap pós-MVP (5 modalidades + projeto-irmão)

| Versão | Modalidade | Estimativa | Trigger ativação |
|---|---|---|---|
| v1.1 | Bancário Genérico | +20-30h [OTIMISTA] | 2-3 advogados validam Veicular MVP em produção |
| v1.2 | Imobiliária CDC SFH/SFI | +40-60h [REVISADA] | v1.1 estável + market validation (TAM 4x Veicular) |
| v1.3 | Crédito Bancário (rotativo + cheque especial) | +30-45h [REVISADA] | v1.2 estável + advogado solicita |
| Fase 2+ | Revisor FIES (projeto-irmão separado) | a definir | Eric autoriza pós-v1.0 MVP em produção |

### 6.6 Anti-patterns documentados (NÃO revisitar)

- **VPS multi-tenant SaaS** (§2.2 + §4.2) — quebra LGPD diferencial
- **Auth hardcoded** (§2.3 L2 NUNCA hardcoded em código) — vulnerabilidade git histórico
- **cron OS-específico** (§2.4 + §4.4) — não cross-platform
- **Manual-only Tema 1378** (§2.5 + §4.5) — unreliable

---

*ADR-013 — Aria (sessão 87, 2026-05-06) · Sprint 03 course-correction CC.2 · Consolidação 5 decisões arquiteturais MVP v1.1.2.1 · ADR-Design DEFAULT (não Spec — implementação cirúrgica fica em FRs/stories)*

— Aria, arquitetando o futuro 🏗️

---

## Histórico

### 2026-05-06 — ADR-013 drafted (sessão 87 Sprint 03 course-correction CC.2)
- Autoria: Aria (design) + Morgan (alinhamento PRD v1.1.2.1) + Morpheus (consolidação 5 decisões)
- Escopo: MVP Lean Strategy + Deployment Path (5 decisões arquiteturais — Docker, Hosting, LGPD operacional, Backup automation, Tema 1378 risk mitigation)
- Status inicial: accepted

### 2026-05-07 — ADR-013 deprecated PARCIAL (Sprint 04 cloud pivot)
- Trigger: Sprint 04 pivot SaaS B2B cloud → ADR-015 Vision OCR Architecture supersedeu mecanismo OCR (marker-pdf + Surya local → Claude Sonnet 4.6 vision cloud)
- Frontmatter status: accepted → deprecated; partially_superseded_by: ADR-015
- Warning bold no topo do documento
- ADR-INDEX strikethrough + "Superseded by ADR-015 (parcial — Vision OCR pivot)"
- Preservado válido: MVP Lean intent (single-page deploy, simple architecture, deployment path) — não revisita arquitetural
- Razão: cloud pivot removeu OCR local, MAS distribution/hosting/deployment path conceitos permanecem válidos para reflection arquitetural

### 2026-05-12 — CC.2 CLOSURE (sessão 2026-05-12 Aria 0h)
- Trigger: PROJECT-CHECKPOINT.md L6 active_story declarou "Próximo: CC.2 Aria ADR-013" como pendente pré-sessão de fixes Smith
- Análise Aria: ADR-013 já estava completamente documentado como deprecated parcial via frontmatter idiomático (status: deprecated + deprecated_date + partially_superseded_by: ADR-015 + warning bold L39-42) e ADR-INDEX já refletia strikethrough. VAULT-FIX-01 (story Done committed 3d055c6) implementou ADR-012 (vault data bundling), não ADR-013
- Decisão Aria CC.2 closure: **ADR-013 NÃO requer updates substantivos** — deprecação parcial já formalizada em 2026-05-07. CC.2 closure é apenas consolidação documental
- Cadeia CC Sprint 03 Phase 0:
  * CC.1A FECHADO (docs commit ef8d087)
  * CC.1B FECHADO (VAULT-FIX-01 commit 3d055c6 — story Done)
  * CC.2 FECHADO (ADR-013 reaffirmação documental — esta entrada)
- Próximo: Eric decide PR creation Sprint 03 Phase 0 closure (Operator dispatch quando autorizado)
- Lição arquitetural: **ADR-013 deprecação parcial foi instrutiva** — demonstrou pattern "MVP roadmap morre quando estratégia pivota, mas reflection arquitetural intent permanece útil". Pattern aplicável a futuros pivots Sprint 05+

