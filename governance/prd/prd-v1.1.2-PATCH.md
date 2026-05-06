---
type: prd
title: "Revisor Contratual — PRD v1.1.2 PATCH (Smith re-review CC.1A' endereçado — perfeição Eric)"
project: revisor-contratual
version: "1.1.2.1"
predecessor: "prd/prd-v1.1.1-PATCH.md"
status: active
last_updated: "2026-05-06"
inline_micro_patch: "v1.1.2.1 endereçando F-NEW2-01/02/03 Smith re-review #2 (Eric opção α; sem ciclo formal separado)"
owner: "@pm (Morgan)"
date: "2026-05-05"
sprint: "03 (course-correction CC.1A'')"
bump_basis: "Smith re-review CC.1A' PASS-COM-RESSALVA — 4 MEDIUM + 2 LOW novos findings endereçados (Eric escolheu opção B perfeição). Defense-in-depth + cross-platform completos."
inputs:
  - ".lmas/handoffs/handoff-morpheus-to-pm-2026-05-05-cc1a-patch-v1.1.2.yaml"
  - ".lmas/handoffs/handoff-smith-to-morpheus-2026-05-05-cc1a-prime-consolidation.yaml"
  - "prd/prd-v1.1.1-PATCH.md (predecessor preservado)"
tags:
  - project/revisor-contratual
  - prd
  - prd-v1.1.2
  - patch
  - perfection
  - defense-in-depth
  - cross-platform
  - sprint-03
---

# PRD v1.1.2 PATCH — Smith Re-Review CC.1A' Findings Endereçados (Perfeição Eric)

> **PATCH section sobre PRD v1.1.1-PATCH.md.** Não substitui v1.1.1 (preservado como histórico).
> Esta PATCH endereça os **6 NOVOS findings** descobertos no Smith re-review CC.1A' (4 MEDIUM + 2 LOW), por escolha estratégica Eric (opção B = perfeição).

| Campo | Valor |
|---|---|
| **Versão** | 1.1.2 (PATCH — endereçamento Smith re-review CC.1A') |
| **Status** | Active (substitui v1.1.1 operacionalmente; v1.1.1 preservado como histórico) |
| **Owner** | @pm (Morgan) |
| **Data** | 2026-05-05 |
| **Decisão Eric** | Opção B (perfeição) — zero ressalvas residuais antes de Aria começar arquitetura |
| **Findings endereçados** | 6/6 (4 MEDIUM obrigatórios + 2 LOW completos) |

---

## 1. Razão do PATCH

Smith re-review CC.1A' emitiu **VEREDICTO PASS-COM-RESSALVA** sobre PRD v1.1.1, identificando 6 novos findings residuais (4 MEDIUM + 2 LOW). Eric foi apresentado a 3 opções e escolheu **opção B (perfeição)**:

> "+3-5h Morgan PATCH + 1h Smith re-review #2 = ~4-6h adicional antes CC.2 — em troca, PRD v1.1.2 sem ressalvas pendentes; Aria recebe escopo definitivo."

Custo aceito: CC.1B Oracle gate VAULT-FIX-01 em HOLD (pipeline serial limpo, não paralelo).
Ganho: defesa em profundidade LGPD + cross-platform real + estimativas honestas.

---

## 2. Mudanças por Finding

### 2.1 F-NEW-01 — FR-LGPD-MVP-01 expandido com defesa em profundidade

**Atualização v1.1.2:**

> **§7.1.1 — FR-LGPD-MVP-01 (EXPANDIDO em v1.1.2) — Compliance LGPD MVP com defesa em profundidade**
>
> Mitigação Art. 46 LGPD ("medidas técnicas de segurança") via 4 camadas:
>
> **Camada 1 — Autenticação (preservada de v1.1.1):**
> - Basic auth: 1 usuário (`AUTH_USERNAME` em .env) + 1 senha bcrypt (`AUTH_PASSWORD_HASH` em .env)
> - Login obrigatório: Sistema NÃO renderiza pipeline antes de autenticação válida
> - Logout via endpoint `/logout`
>
> **Camada 2 — Sessão segura (NOVO em v1.1.2):**
> - Starlette `SessionMiddleware(https_only=True, samesite="strict")` previne cookie roubo via XSS/CSRF
> - Cookie de sessão com `secure=True` (HTTPS only) + `samesite=strict` + expiração 24h
> - **SessionMiddleware secret_key (NOVO em v1.1.2.1):** gerada via `python -c "import secrets; print(secrets.token_urlsafe(32))"` no setup inicial e persistida em `.env` (variável `SESSION_SECRET`, mínimo 32 bytes). FastAPI carrega via `os.getenv('SESSION_SECRET')` em startup. **NUNCA hardcoded em código** (vulnerabilidade git histórico). **NUNCA commitada** (`.env` já gitignored). Re-geração invalida sessões existentes (todos usuários re-login). Setup script `scripts/init-session-secret.sh` documentado em SOP-001 (a criar como follow-up trivial).
> - CSRF token automático para form POST `/revisar`, `/reset` (FastAPI middleware integrado)
>
> **Camada 3 — Headers HTTP de segurança (NOVO em v1.1.2):**
> - Content-Security-Policy header restrita: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'`
> - X-Frame-Options: `DENY` (anti-clickjacking)
> - X-Content-Type-Options: `nosniff`
> - Strict-Transport-Security (apenas se HTTPS configurado): `max-age=31536000; includeSubDomains`
>
> **Camada 4 — Encryption-at-rest (NOVO em v1.1.2):**
> - PDFs uploads/ encriptados via Python `cryptography.fernet` lib
> - Chave em .env (`FERNET_KEY` — 32 bytes base64-encoded)
> - Encrypt on upload (POST `/revisar`) → decrypt para parsing in-memory → delete após pipeline (LGPD cleanup)
> - Audit log inclui hash do PDF original (para correlação) sem expor conteúdo
>
> **Camada 5 — Permissões filesystem (preservada de v1.1.1):**
> - audit.jsonl criado com chmod 600 (rw owner only, não world-readable)
> - PDFs temporários em `~/.local/share/revisor-contratual/uploads/` com chmod 700
>
> **Estimativa dev expandida:** ~3h45min (era ~2h v1.1.1)
>   - Layer 1 (preservada): 0h
>   - Layer 2 CSRF/sessão: ~30min
>   - Layer 3 CSP+headers: ~15min
>   - Layer 4 encryption-at-rest: ~1h (cryptography.fernet + chave + encrypt/decrypt flow)
>   - Layer 5 (preservada): 0h
>   - Subtotal: ~1h45min ADICIONAL sobre v1.1.1
>
> **AC-FR-LGPD-MVP-01a (preservado):** 100% das tentativas sem cookie sessão válido retornam 401/redirect
>
> **AC-FR-LGPD-MVP-01b EXPANDIDO (NOVO):**
> - chmod 600 em audit.jsonl ✅
> - chmod 700 em uploads/ ✅
> - **0% dos PDFs em uploads/ permanecem em plain text após upload** (verificável via `file uploads/*.bin` retornando "data" not "PDF document"; descriptografia exige FERNET_KEY)
>
> **AC-FR-LGPD-MVP-01c (NOVO):** CSP header presente em 100% das responses HTTP (verificável via `curl -I` ou test E2E)
>
> **AC-FR-LGPD-MVP-01d (NOVO):** CSRF token validado em 100% das form POSTs (verificável via test E2E POST sem token → 403 Forbidden)
>
> **AC-FR-LGPD-MVP-01e (NOVO em v1.1.2.1):** SESSION_SECRET presente em .env com ≥32 bytes (verificável via `grep -E 'SESSION_SECRET=.{32,}' .env`); ZERO occurrences de string hardcoded `secret_key="..."` no código (verificável via `grep -r 'secret_key=' bloco_interface/web/ | wc -l` retornando 0 OR apenas leitura via os.getenv).

**Atualização §12.2 NFR-LGPD-01:**

> **NFR-LGPD-01 — 100% on-premise (REVISADO em v1.1.2)**
> - Nenhum dado do contrato sai da máquina. Whitelist HTTP estrita: STJ + STF + BACEN + 127.0.0.1 (Ollama local).
> - **PRESERVADO COM FR-LGPD-MVP-01 mitigation defense-in-depth (5 camadas):** auth + sessão segura + headers HTTP + encryption-at-rest + permissões filesystem
> - VPS multi-tenant DESCARTADO (preservado)
> - Docker opcional pós-v1.0 NÃO viola NFR-LGPD-01

---

### 2.2 F-NEW-02 — FR-MONITOR-01 com fallback SOP-005

**Atualização v1.1.2 §7.10:**

> **FR-MONITOR-01 (REVISADO em v1.1.2) — Monitoramento ATIVO Tema 1378 STJ com fallback**
>
> **Camada 1 — Monitoramento automático (preservada de v1.1.1):**
> - Job semanal scrape `https://www.stj.jus.br/repetitivos/temas-repetitivos` filtrando Tema 1378
> - Detecção dispara: CRITICAL_ALERT em audit.jsonl + banner vermelho persistente UI + email AUTH_USERNAME + pause de novas gerações até ack
>
> **Camada 2 — Fallback maintainer manual (NOVO em v1.1.2 — F-NEW-02):**
> - **SOP-005:** `docs/sop-monitoramento-tema-1378.md`
> - **Trigger:** "Se FR-MONITOR-01 falhar 7+ dias consecutivos OR maintainer notifica via PROJECT-CHECKPOINT trimestral"
> - **Procedimento:** maintainer acessa stj.jus.br/repetitivos manualmente → busca "1378" → verifica status → se julgado → trigger CRITICAL_ALERT manual via CLI `revisor monitor-tema --manual-trigger 1378 --status julgado` (NOVO subcomando)
> - **Cross-reference:** PROJECT-CHECKPOINT.md trimestral reminder
>
> **Estimativa dev expandida:** ~3h30min (era 3-4h v1.1.1)
>   - Camada 1 scraper + alerta + UI banner: ~3h (preservado)
>   - Camada 2 SOP-005 + CLI subcommand `monitor-tema --manual-trigger`: ~30min adicional
>
> **AC-FR-MONITOR-01a (preservado):** 100% de detecção em ≤7 dias após julgamento publicado oficialmente
>
> **AC-FR-MONITOR-01b (NOVO):** SOP-005 documentado em docs/sop-monitoramento-tema-1378.md + cross-reference PROJECT-CHECKPOINT.md (verificável via grep)
>
> **AC-FR-MONITOR-01c (REVISADO em v1.1.2.1):** CLI subcommand `revisor monitor-tema` aceita 6 flags completos: `--manual-trigger {tema_id}` + `--status {julgado|suspenso|em_julgamento|arquivado}` + `--tese-text {string}` (se julgado) + `--data-julgamento {YYYY-MM-DD}` (se julgado) + `--data-arquivamento {YYYY-MM-DD}` (se arquivado) + `--acknowledge {tema_id}` (reset banner pós-vault update). Verificável via `revisor monitor-tema --help` retornando todos os 6 flags + test E2E cada signature.

---

### 2.3 F-NEW-03 — D3 Apelação Cível reestimado para 6-8h

**Atualização v1.1.2 §4.3 Deliverables MVP:**

> **D3 — Apelação Cível (REESTIMADO em v1.1.2)**
>
> Geração de modelo Apelação Cível em PDF (Jinja2 + WeasyPrint, hash sha256 audit-tracked) com fundamentação rastreável a jurisprudência específica recuperada via RAG.
>
> **Fluxo de implementação detalhado (estimativa realista):**
>
> 1. **Parser decisão adversa PDF** (~30min — reuso PyMuPDF4LLM existente) — extrai dispositivo + fundamentos + data
> 2. **Recuperação contexto petição original** (~1h) — load `veredicto.json` + `tese.json` do audit log via hash da petição original
> 3. **Nova jurisprudência relevante** (~30min — reuso FR-RAG existente) — query filtrada com `tipo=apelacao` + `decisao_adversa_dispositivo`
> 4. **Template Jinja2 Apelação + WeasyPrint** (~3-4h NOVO) — template específico Apelação (estrutura: tempestividade + admissibilidade + mérito com citações + pedido)
> 5. **Validação semântica citações** (~30min — reuso FR-TESE-04) — cosine similarity ≥0.7
> 6. **Tela Adoção CFOAB** (~30min — reuso FR-DELIV-06) — checkbox + OAB + audit log
>
> **Estimativa total:** **6-8h dev** (corrigido de 2h v1.1.1 — F-NEW-03 mitigado)
>
> **Justificativa Morgan:** Smith identificou underestimate 3x. Reestimativa honesta evita debt de cronograma + frustração @dev Neo durante implementação.
>
> **AC-FR-DELIV-D3 (preservado):** PDF Apelação gerado para 100% dos casos onde usuário fez upload de decisão adversa + petição original; hash sha256 registrado em audit log; FR-DELIV-06 CFOAB aplicado.

**Atualização §11 / TECH-DEBT.md:** BL-DELIV-05a (Embargos+Agravo+RE) preservado para v1.1+ (não afetado por reestimativa D3).

---

### 2.4 F-NEW-04 — FR-BACKUP-MVP-01 cross-platform via APScheduler

**Atualização v1.1.2 §7.10:**

> **FR-BACKUP-MVP-01 (REVISADO em v1.1.2) — Backup automático cross-platform**
>
> **Implementação cross-platform via APScheduler (NOVO em v1.1.2):**
>
> - Dependency: `apscheduler>=3.10` adicionada em pyproject.toml
> - **Footprint (NOVO em v1.1.2.1):** ~150KB compressed (negligível vs alternativas cron OS-específico não-portátil OR Python pure threading.Timer não-persistente). Production-grade (PyPI maintained, Linux+Mac+Windows nativo).
> - APScheduler `BackgroundScheduler` instanciado em FastAPI lifespan startup (`bloco_interface/web/app.py`)
> - Job `backup_daily` com trigger `cron(hour=2, minute=0)` (executa 02:00 horário local)
>   - Procedimento: `shutil.copy2()` de `~/.local/share/revisor-contratual/{vault.db, audit.jsonl}` → `~/.local/share/revisor-contratual/backups/{YYYY-MM-DD}/`
> - Job `backup_rotation` com trigger `interval(days=1)` (executa 1×/dia)
>   - Procedimento: deletar backups com `mtime < now() - 7 days`
> - Cross-platform: APScheduler funciona Linux + Mac + Windows nativamente (não requer cron nem Task Scheduler)
> - Falha graceful: try/except em job; log WARNING se backup falhar; NÃO bloqueia pipeline
>
> **Estimativa dev expandida:** **1.5-2h** (era 1h v1.1.1 — F-NEW-04 mitigado)
>
> **AC-FR-BACKUP-MVP-01a (preservado):** simulação perda vault.db → restauração via último backup recupera 100%
>
> **AC-FR-BACKUP-MVP-01b EXPANDIDO (NOVO):**
> - Backup automático funciona em **Linux + Mac + Windows** (verificável via test integração mock APScheduler)
> - APScheduler dependency adicionada em pyproject.toml (verificável via `pip show apscheduler`)

---

### 2.5 F-NEW-05 — Validação OAB sem checksum (aceito como MVP debt)

**Atualização v1.1.2 §13 Riscos:**

> **R-NEW-OAB-CHECKSUM (NOVO em v1.1.2) — Validação OAB regex sem checksum CFOAB**
> - **Probabilidade:** BAIXA (advogado profissional não tem incentivo para fakeout próprio número OAB)
> - **Impacto:** BAIXO (audit log forensic tracking permite detecção pós-fato; rate limit por OAB+IP previne abuse em massa)
> - **Mitigação MVP:** rate limit 1/min + 100/dia por OAB + audit log forensic tracking (FR-DELIV-06 v1.1.1)
> - **Mitigação completa (deferred):** API CFOAB pública integration OR dataset OAB+UF público validado — `BL-OAB-CHECKSUM` em TECH-DEBT.md
> - **Trigger re-avaliação:** "API CFOAB pública disponível OU dataset OAB+UF público validado"
> - **Owner:** @dev (Neo) sob direção @pm Morgan

**Atualização TECH-DEBT.md (a executar):** adicionar BL-OAB-CHECKSUM como entry LOW.

---

### 2.6 F-NEW-06 — MVP estimate atualizado refletindo math real

**Atualização v1.1.2 §3.4 Escopo Atual vs Original:**

> **v1.1.2:** ~13 FRs ativos MVP + 3 deliverables + 14 BL-* + 4 modalidades roadmap + 1 projeto-irmão + AC-PRECONDITION explícitas + defense-in-depth LGPD + APScheduler cross-platform
>
> **MVP estimate REVISADO (math real refletindo todas correções):**
>
> | Componente | v1.1.0 | v1.1.1 | **v1.1.2** |
> |---|---|---|---|
> | Baseline (FR-CALC + FR-BACEN + FR-RAG + FR-TESE + FR-JUIZ + FR-DELIV-01/04 + FR-DELIV-06 + FR-AUDIT + FR-PARSE + FR-UPLOAD) | 25-35h | 25-35h | 25-35h |
> | FR-LGPD-MVP-01 (auth+chmod) | n/a | +2h | n/a (parte de defense-in-depth abaixo) |
> | FR-LGPD-MVP-01 expanded (5 camadas: auth + sessão + CSP + encryption + permissões) | n/a | n/a | **+3h45min** |
> | FR-MONITOR-01 ATIVO (scrape STJ + alerta + UI banner + email + pause) | n/a | +3-4h | n/a (parte de scraper+fallback) |
> | FR-MONITOR-01 (scrape + SOP-005 + CLI manual-trigger) | n/a | n/a | **+3h30min** |
> | FR-BACKUP-MVP-01 (cron daily Linux/Mac OR APScheduler cross-platform) | n/a | +1h | **+1.5-2h** (APScheduler cross-platform) |
> | FR-ECONOMISTA-01 explicit | n/a | 0h (já em ADR-003) | 0h (já em ADR-003) |
> | D3 Apelação Cível | n/a | +2h (underestimate) | **+6-8h** (realista) |
> | FR-DELIV-06 validação OAB server-side | n/a | +2h | +2h (preservado) |
> | **TOTAL MVP ESTIMATE** | **25-35h** | **33-44h** | **41-55h** |
>
> **Motivo principal v1.1.2:** Smith re-review identificou 4 MEDIUM + 2 LOW residuais. Eric escolheu opção B (perfeição) — endereçamento completo via defense-in-depth LGPD + cross-platform backup + reestimativa honesta D3.

---

## 3. Delta Section v1.1.1 → v1.1.2

### 3.1 Features Adicionadas em v1.1.2

- **FR-LGPD-MVP-01 Camadas 2-4:** Sessão segura (CSRF + samesite=strict) + Headers HTTP (CSP + X-Frame-Options + X-Content-Type-Options) + Encryption-at-rest (Fernet) — defense-in-depth LGPD MVP
- **SOP-005:** docs/sop-monitoramento-tema-1378.md (fallback maintainer manual semanal)
- **CLI subcommand `revisor monitor-tema --manual-trigger`** (manual trigger CRITICAL_ALERT Tema 1378)
- **APScheduler dependency** (cross-platform backup automático Linux+Mac+Windows)
- **R-NEW-OAB-CHECKSUM** documentado em §13 com mitigação aceita
- **3 ACs novos:** AC-FR-LGPD-MVP-01b expandido, AC-FR-LGPD-MVP-01c (CSP), AC-FR-LGPD-MVP-01d (CSRF), AC-FR-MONITOR-01b (SOP-005), AC-FR-MONITOR-01c (CLI manual-trigger), AC-FR-BACKUP-MVP-01b expandido (cross-platform)

### 3.2 Features Modificadas em v1.1.2

- **FR-LGPD-MVP-01:** auth básica → defense-in-depth 5 camadas (~2h dev v1.1.1 → ~3h45min v1.1.2)
- **FR-MONITOR-01:** auto only → auto + fallback manual (~3-4h v1.1.1 → ~3h30min v1.1.2)
- **FR-BACKUP-MVP-01:** cron OS-específico → APScheduler cross-platform (~1h v1.1.1 → ~1.5-2h v1.1.2)
- **D3 Apelação Cível:** estimativa 2h underestimate → 6-8h realista (correção F-NEW-03)
- **MVP estimate:** 33-44h v1.1.1 → **41-55h v1.1.2** (+8-11h refletindo defense-in-depth + reestimativas honestas)

### 3.3 Features Removidas

Nenhuma. Todas as features v1.1.1 preservadas; apenas expandidas para defense-in-depth + cross-platform.

### 3.4 Escopo Atual vs Original (linha-final)

- **v1.1.0:** ~8 FRs MVP + 12 BL-* + 4 modalidades + FIES projeto-irmão | **MVP 25-35h**
- **v1.1.1:** ~12 FRs + 3 deliverables + 14 BL-* + 2 PRE-RELEASE BLOCKERS | **MVP 33-44h**
- **v1.1.2:** ~13 FRs + 3 deliverables + 15 BL-* (BL-OAB-CHECKSUM novo) + 2 PRE-RELEASE BLOCKERS + defense-in-depth LGPD + cross-platform backup + SOP-005 fallback | **MVP 41-55h**

**Net trade-off Eric (opção B perfeição vs opção A aceitar v1.1.1 ressalvas):**
- Custo: +8-11h dev MVP + ~5h Morgan/Smith course-correction (PATCH v1.1.2 + re-review)
- Ganho: defense-in-depth LGPD real (CSRF/CSP/encryption-at-rest) + cross-platform backup + fallback manual Tema 1378 + estimativa MVP honesta

---

## 4. Ações executadas durante esta PATCH

| Ação | Artefato | Status |
|---|---|---|
| PRD v1.1.2 PATCH publicado | `governance/prd/prd-v1.1.2-PATCH.md` | ✅ ESTE ARQUIVO |
| INDEX.md atualizado (v1.1.2 ACTIVE; v1.1.1 superseded) | `governance/prd/INDEX.md` | ⏳ A executar |
| BL-OAB-CHECKSUM adicionado em TECH-DEBT.md | `governance/TECH-DEBT.md` | ⏳ A executar |
| SOP-005 criado | `docs/sop-monitoramento-tema-1378.md` | ⏳ A executar |
| Checkpoint inline atualizado | `governance/CHECKPOINT-active.md` | ⏳ A executar |
| Handoff Morgan→Smith re-review #2 emitido | `.lmas/handoffs/handoff-pm-to-smith-2026-05-05-cc1a-tribunal-re-review-2.yaml` | ⏳ A executar |

---

## 5. Histórico Append-Only

### v1.1.2.1 — 2026-05-06 (Morgan, sessão 87 micro-PATCH inline α)

**Micro-PATCH inline.** Razão: Smith re-review #2 PASS-COM-RESSALVA com 3 micro-fixes documentais (F-NEW2-01/02/03). Eric escolheu opção α recomendada Smith — Edit direto em v1.1.2 sem ciclo formal v1.1.2.1 separado.

**Mudanças (3 inline edits):**
- EXPANDED AC-FR-MONITOR-01c (signature CLI completa 6 flags: `--manual-trigger` + `--status` + `--tese-text` + `--data-julgamento` + `--data-arquivamento` + `--acknowledge`) — F-NEW2-01 LOW endereçado
- DOCUMENTED SessionMiddleware secret_key em FR-LGPD-MVP-01 Camada 2 (gerada via secrets.token_urlsafe(32) em .env SESSION_SECRET, nunca hardcoded) + AC-FR-LGPD-MVP-01e novo — F-NEW2-02 MEDIUM endereçado
- DOCUMENTED apscheduler dependency footprint (~150KB compressed) em FR-BACKUP-MVP-01 — F-NEW2-03 LOW endereçado

**Estimativa:** ~20min Morgan Edit (sem dev time impact — mudanças documentais)

**Próximo:** Morpheus consolida CC.1A'' final + dispara CC.2 Aria + CC.1B Oracle paralelo

---

### v1.1.2 — 2026-05-05 (Morgan, Sprint 03 course-correction CC.1A'')

**PATCH bump.** Razão: Smith re-review CC.1A' PASS-COM-RESSALVA com 6 novos findings residuais. Eric escolheu opção B (perfeição) — endereçar todos antes de Aria começar.

**Mudanças estruturais:**
- EXPANDED FR-LGPD-MVP-01 para 5 camadas defense-in-depth (auth + sessão CSRF/samesite + headers CSP/X-Frame/X-Content + encryption-at-rest Fernet + permissões filesystem)
- EXPANDED FR-MONITOR-01 com fallback SOP-005 + CLI manual-trigger
- EXPANDED FR-BACKUP-MVP-01 cross-platform via APScheduler
- REVISED D3 Apelação Cível estimativa 2h → 6-8h (correção F-NEW-03 underestimate 3x)
- ADDED 3 novos ACs: AC-FR-LGPD-MVP-01c (CSP), AC-FR-LGPD-MVP-01d (CSRF), AC-FR-MONITOR-01c (CLI manual-trigger)
- ADDED dependency apscheduler>=3.10
- ADDED R-NEW-OAB-CHECKSUM em §13 + BL-OAB-CHECKSUM em TECH-DEBT.md
- REVISED MVP estimate 33-44h → 41-55h (refletindo defense-in-depth + reestimativas honestas)

**Stories impactadas:**
- VAULT-FIX-01 (Ready for Review) — sem alterações; CC.1B Oracle gate em HOLD aguardando perfeição PATCH v1.1.2 PASS
- OLLAMA-MGR-01 (Ready não iniciada) — sem alterações
- MVP-LEAN-01 (futura, River CC.4) — escopo expandido com defense-in-depth + APScheduler + SOP-005

**Decisões pendentes Eric:**
- Confirmação MVP estimate 41-55h é aceitável (vs 33-44h v1.1.1; vs 25-35h v1.1.0 original) — perfeição custa 16-20h additional vs caminho híbrido inicial
- Confirmação dependency apscheduler é OK adicionar (mais 1 dependency Python; alternativa cron OS-específico foi rejeitada)

**Próximo step:** Smith re-review #2 focado em verificar CSRF/CSP/encryption REAIS + APScheduler cross-platform + SOP-005 completo + ACs expandidos mensuráveis.

---

### v1.1.1 — 2026-05-05 (Morgan, Sprint 03 course-correction CC.1A') [PATCH — predecessor preservado]

(Conteúdo preservado em `prd/prd-v1.1.1-PATCH.md` — não duplicar aqui)

### v1.1.0 — 2026-05-05 (Morgan, Sprint 03 course-correction CC.1A) [MAJOR — predecessor preservado]

(Conteúdo preservado em `prd/prd-v1.1.0-MAJOR.md` — não duplicar aqui)

### v1.0.3 — 2026-05-05 (Morgan, Sprint 02 planning) [PATCH — predecessor preservado]

(Conteúdo preservado em `prd/prd-v1.0.3-DELTA.md` — não duplicar aqui)

### v1.0.2 — 2026-05-01 (Morgan, Sprint 01 etapa 1.0) [PATCH — predecessor preservado]

(Conteúdo preservado em `prd/prd-v1.0.2.md` — não duplicar aqui)

---

*PRD v1.1.2 PATCH — Morgan (sessão 87, 2026-05-05) · Sprint 03 course-correction CC.1A'' · Smith re-review CC.1A' endereçado (6/6 findings) · Eric opção B perfeição · Defense-in-depth LGPD + cross-platform backup + fallback manual Tema 1378*

— Morgan, planejando o futuro 📊
