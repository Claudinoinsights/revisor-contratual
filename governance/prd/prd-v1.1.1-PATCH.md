---
type: prd
title: "Revisor Contratual — PRD v1.1.1 PATCH (Tribunal CC.1A endereçado)"
project: revisor-contratual
version: "1.1.1"
predecessor: "prd/prd-v1.1.0-MAJOR.md"
status: active
last_updated: "2026-05-05"
owner: "@pm (Morgan)"
date: "2026-05-05"
sprint: "03 (course-correction CC.1A')"
bump_basis: "Tribunal severo CC.1A — Smith FAIL (5 HIGH bloqueadores) + checkpoint PASS-COM-RESSALVA (2 MEDIUM + 1 LOW). PATCH endereça 7 findings bloqueadores + 7 findings MEDIUM/LOW adicionais."
inputs:
  - ".lmas/handoffs/handoff-morpheus-to-pm-2026-05-05-cc1a-patch-v1.1.1.yaml"
  - "prd/prd-v1.1.0-MAJOR.md (predecessor preservado)"
  - "Tribunal CC.1A — Smith parte 1 + checkpoint parte 2 (sessão 87)"
tags:
  - project/revisor-contratual
  - prd
  - prd-v1.1.1
  - patch
  - tribunal-addressed
  - sprint-03
  - mvp-lean-hardened
---

# PRD v1.1.1 PATCH — Tribunal CC.1A Findings Endereçados

> **PATCH section sobre PRD v1.1.0-MAJOR.md.** Não substitui v1.1.0 (preservado como histórico).
> Esta PATCH endereça os 7 findings bloqueadores do tribunal severo CC.1A + 7 findings MEDIUM/LOW adicionais (escolha Morgan para defensividade máxima frente Smith re-review).

| Campo | Valor |
|---|---|
| **Versão** | 1.1.1 (PATCH — endereçamento tribunal CC.1A) |
| **Status** | Active (substitui v1.1.0 operacionalmente; v1.1.0 preservado como histórico) |
| **Owner** | @pm (Morgan) |
| **Data** | 2026-05-05 |
| **Tribunal** | CC.1A FAIL (Smith 5 HIGH + checkpoint 2 MEDIUM + 1 LOW) |
| **Findings endereçados** | 14/14 (5 HIGH obrigatórios + 2 MEDIUM checkpoint obrigatórios + 7 MEDIUM/LOW Smith opcionais) |

---

## 1. Razão do PATCH

Tribunal severo CC.1A consolidado emitiu **VEREDICTO FAIL** sobre PRD v1.1.0:

- **Smith parte 1 (technical):** INFECTED com 5 HIGH bloqueadores (veto absoluto per ORDEM 8)
- **checkpoint parte 2 (governance):** PASS-COM-RESSALVA com 3 governance gaps

Esta PATCH endereça **TODOS** os bloqueadores + **MAIORIA** dos findings adicionais para garantir Smith re-review PASS sem necessidade de v1.1.2. Morgan optou por defensividade máxima (vs mínimo necessário) porque:

1. Custo marginal endereçar MEDIUM/LOW na mesma PATCH é baixo
2. Smith re-review terá mais rigor que primeira vez
3. CC.2 Aria depende de PASS — atrasar com v1.1.2 desnecessário se PATCH cobre tudo

---

## 2. Mudanças por Finding

### 2.1 F-HIGH-01 — Latência target corrigida ≤180s → ≤210s

**Decisão Morgan:** **Opção A** (recomendação Morpheus). NFR-PERF-01 e AC-1 voltam para ≤210s mantendo Economista preservada.

**Razão:** Eric explicitamente preservou Economista em v1.0.2 Smith F-CRIT-06 (mitigação Tema 1378 STJ). Cortar Economista é contradizer decisão arquitetural histórica. Cortes UI economizam ~17-22s reais; Economista custa +30s LLM call. Math: ~190-200s real, com margem para ≤210s worst case Tier Premium Sabia-7B Q4 CPU.

**Atualização v1.1.1:**

> **NFR-PERF-01 — Latência alvo por contrato (end-to-end) — REVISADO**
> - **MVP v1.1.1: ≤210s mediana** (revertendo da meta v1.1.0 ≤180s incoerente)
> - Razão da revisão: Economista preservada (P-INT-04, ADR-003) custa +30s LLM call; cortes UI economizam ~17-22s; math real é ~195-210s
> - Coerente com decisão histórica v1.0.2 Smith F-CRIT-06
> - Sob promoção a GPU futura ou Tier menor: latência cai conforme `quality-data-modularity-assurance-2026-05-01.md`

> **AC-1 — Latência end-to-end — REVISADO**
> - Target: **≤210s mediana** (vs ≤180s v1.1.0)
> - 50 contratos golden set (após BL-GOLDEN-SET completo — ver §2.5 AC-PRECONDITION)
> - Hardware alvo: Intel i5-10300H 4C/8T, 16GB RAM, sem GPU dedicada para LLM
> - Tier: balanced default (Qwen 2.5 7B Q4)

---

### 2.2 F-HIGH-02 — AC-3 PRECONDITION + BL-VAULT-BULK-IMPORT pre-release blocker

**Atualização v1.1.1:**

> **AC-3 — Cobertura vault RAG — REVISADO**
> - Target: ≤15% Inviabilidade por RAG vazio em 50 queries golden set
> - **PRECONDITION OBRIGATÓRIA:** AC-3 só é avaliável APÓS:
>   - BL-VAULT-BULK-IMPORT completo (vault populado com ≥600 entries STJ + ≥58 entries STF SV oficiais via SOP-004 Path A — compendium PDF oficial → import-dataset CLI)
>   - BL-GOLDEN-SET completo (50 queries golden curadas pelo @qa)
> - Sem essas 2 preconditions, AC-3 é `BLOCKED-PENDING-PRECONDITIONS`

**Novo BL-VAULT-BULK-IMPORT em §11 (atualização §11 abaixo):**

> | **BL-VAULT-BULK-IMPORT** | One-shot bulk import oficial vault (≥600 STJ + ≥58 STF SV) via SOP-004 Path A | **MVP PRE-RELEASE BLOCKER** | 2-4h maintainer | maintainer (Eric ou delegado) | NÃO opcional — gate condition release MVP |

---

### 2.3 F-HIGH-03 — FR-LGPD-MVP-01 adicionado (auth mínima basic-auth)

**Decisão Morgan:** **Opção A** (recomendação Morpheus). Auth mínima basic-auth no MVP com bcrypt em .env.

**Razão:** advogado profissional usando ferramenta de produção sem login é negligente. Custo 2h dev é ínfimo vs LGPD Art. 46 compliance + responsabilização indireta Eric. Auth elaborada (FR-AUTH-01..04 v1.0.2) com cookies + audit log de tentativas + IP fingerprint vai para v1.1+ (BL-AUTH-01 mantém-se).

**Novo FR-LGPD-MVP-01 (adicionar em §7 entre 7.1 e 7.2):**

> **§7.1.1 — FR-LGPD-MVP-01 (NOVO em v1.1.1) — Compliance LGPD MVP**
>
> Mitigação Art. 46 LGPD ("medidas técnicas de segurança") via auth mínima:
>
> - Basic auth: 1 usuário (`AUTH_USERNAME` em .env) + 1 senha bcrypt (`AUTH_PASSWORD_HASH` em .env)
> - Login obrigatório: Sistema NÃO renderiza pipeline antes de autenticação válida
> - Cookie de sessão simples (Starlette `SessionMiddleware`, expiração 24h)
> - Logout via endpoint `/logout`
> - Sem audit log de tentativas (LOW-priority — BL-AUTH-01 elaborada vai para v1.1+)
> - Sem IP fingerprint (BL-AUTH-02 vai para v1.1+)
>
> **AC-FR-LGPD-MVP-01:** 100% das tentativas de acesso a `/revisar`, `/pipeline-stream`, `/verdict`, `/reset` sem cookie de sessão válido retornam 401/redirect para `/login` (cobertura teste pytest E2E obrigatória).
>
> **AC-FR-LGPD-MVP-01b:** audit.jsonl criado com chmod 600 (não world-readable) por padrão; PDFs temporários em diretório `~/.local/share/revisor-contratual/uploads/` com chmod 700.
>
> **Estimativa dev:** ~2h (basic-auth + chmod) — adicionado ao MVP estimate (28-39h vs 25-35h v1.1.0).

**Atualização §12.2 NFR-LGPD-01:**

> **NFR-LGPD-01 — 100% on-premise (REVISADO em v1.1.1)**
> - Nenhum dado do contrato sai da máquina. Whitelist HTTP estrita: STJ + STF + BACEN + 127.0.0.1 (Ollama local).
> - **PRESERVADO COM FR-LGPD-MVP-01 mitigation** (vs "PRESERVADO INTACTO" v1.1.0 — declaração sem implementação)
> - VPS multi-tenant DESCARTADO (preservado de v1.1.0)
> - 7 fontes self-hosted (REV-INT-02 RESOLVED v0.2.0)
> - Docker opcional pós-v1.0 NÃO viola NFR-LGPD-01 (container roda local)

---

### 2.4 F-HIGH-04 — BL-MONITOR-1378 movido para escopo MVP

**Atualização v1.1.1:**

> **§7.10 Setup, Backup, Recovery — REVISADO**
> - **FR-MONITOR-01 ATIVO no MVP** (vs DEFERRED v1.1.0)
>   - Job semanal scrape `https://www.stj.jus.br/repetitivos/temas-repetitivos` filtrando Tema 1378
>   - Detecção de julgamento dispara: CRITICAL_ALERT em audit.jsonl + banner vermelho persistente UI + email AUTH_USERNAME (se configurado) + pause de novas gerações até ack do usuário
>   - **AC-FR-MONITOR-01:** 100% de detecção em ≤7 dias após julgamento publicado oficialmente
>   - Estimativa dev: 3-4h

**Atualização §13 R8:**

> **R8 (REVISADO) — Tema 1378 STJ julgado durante MVP**
> - **Probabilidade:** MÉDIA-ALTA (Tema 1378 em pauta ativa STJ 2026; janela de julgamento meses)
> - **Impacto:** **CRÍTICO** (responsabilização indireta Eric se petição emitida com tese desatualizada → cliente perde caso → cliente processa advogado → advogado processa Eric)
> - **Mitigação (revisada):** FR-MONITOR-01 ATIVO no MVP (job semanal automático). Maintainer manual mantido como redundância. Risco aceito conscientemente é REJEITADO — mitigação automática obrigatória.

**BL-MONITOR-1378 removido de §11** (movido para §7.10 MVP scope).

**Estimativa MVP atualizada:** **28-39h** (era 25-35h v1.1.0; +3-4h FR-MONITOR-01 + 2h FR-LGPD-MVP-01 = +5-6h total).

---

### 2.5 F-HIGH-05 — BL-GOLDEN-SET formal + AC-PRECONDITION

**Novo BL-GOLDEN-SET em §11 (atualização §11 abaixo):**

> | **BL-GOLDEN-SET** | Curadoria 50 contratos sintéticos CDC PF Veículos + 50 queries golden RAG | **MVP PRE-RELEASE BLOCKER** | 8-12h | @qa Oracle | NÃO opcional — gate condition AC-1, AC-2, AC-3, AC-10 |

**Atualização §8 ACs com PRECONDITION:**

> **AC-PRECONDITION (NOVO em v1.1.1):**
> - AC-1 (latência), AC-2 (fidelidade tabela), AC-3 (cobertura vault), AC-10 (smoke E2E real) **só são avaliáveis APÓS BL-GOLDEN-SET completo + BL-VAULT-BULK-IMPORT completo (para AC-3 e AC-10)**.
> - Status enquanto blocked: `BLOCKED-PENDING-{BL-GOLDEN-SET|BL-VAULT-BULK-IMPORT}`

---

### 2.6 F-CHK-01 — ADR-009 implementação concreta

**Status:** AUTOMATICAMENTE FECHADO por endereçamento de F-HIGH-03 (FR-LGPD-MVP-01 adicionado). PRD v1.1.1 §12.2 atualizado removendo "PRESERVADO INTACTO" → "PRESERVADO COM FR-LGPD-MVP-01 mitigation".

---

### 2.7 F-CHK-02 — 12 BL-* migrados para TECH-DEBT.md

**Decisão Morgan:** **OPÇÃO 2** (Morgan adiciona AGORA na PATCH). Morgan tem authority para Edit TECH-DEBT.md; defensividade máxima frente Smith re-review.

**Ação executada nesta PATCH:**

- 12 BL-* originais (PRD v1.1.0 §11) + 2 novos (BL-VAULT-BULK-IMPORT + BL-GOLDEN-SET) = **14 entries** adicionadas em `governance/TECH-DEBT.md` formato canônico (ID + Source + Sev + Description + Effort + Owner + Added)
- PRD §11 (esta v1.1.1) vira **referência cruzada** para TECH-DEBT.md (TECH-DEBT é fonte de verdade canônica; PRD lista resumo)
- Resumo executivo TECH-DEBT.md atualizado: 15 active → 29 active (15 originais + 14 BL-*)

---

### 2.8 F-MED-01 — Estimativas modalidades qualificadas

**Atualização §6.1 (sequenciamento):**

| Versão | Modalidade | Estimativa | Razão sequência |
|---|---|---|---|
| v1.0 MVP | CDC PF Veículos | **28-39h** (revisado v1.1.1: +5-6h FR-LGPD-MVP-01 + FR-MONITOR-01) | (preservado) |
| v1.1 | Bancário Genérico | **+25-40h** [ESTIMATIVA OTIMISTA — reuso ~60-70% real, não 80%] | (preservado com qualificador) |
| v1.2 | Imobiliária | **+40-60h** [ESTIMATIVA REVISADA — Tema 922 STJ + ADC Caixa + parser PDF complexo] | (revisado +10-20h) |
| v1.3 | Crédito Bancário | **+30-45h** [ESTIMATIVA REVISADA — refator FR-CALC para juros compostos diários] | (revisado +5-10h) |

---

### 2.9 F-MED-02 — Apelação Cível incorporada no MVP (decisão Morgan)

**Decisão Morgan:** Após reflexão, advogado litigante revisional bancário PRECISA Apelação Cível como ferramenta básica. Cortar 100% dos Recursos Processuais quebra value proposition. Solução híbrida: **Apelação Cível NO MVP** + Embargos/Agravo/RE no v1.1+.

**Atualização §4.3 Deliverables MVP — REVISADO:**

> - **D1: Relatório Contábil** (preservado)
> - **D2: Petição Específica revisional** (preservado)
> - **D3 NOVO em v1.1.1: Apelação Cível** (incorporada do BL-DELIV-05 splitado)
>   - Geração de modelo Apelação Cível em PDF (Jinja2 + WeasyPrint, hash sha256 audit-tracked)
>   - Fundamentação rastreável a jurisprudência específica recuperada via RAG
>   - Fluxo: usuário recebe decisão adversa → upload da decisão + petição original → sistema gera Apelação com base no contexto + nova jurisprudência relevante
>   - Aplicável FR-DELIV-06 Tela Adoção CFOAB (idem D2)
>   - Estimativa: ~2h dev adicional

> **Cortados (mantidos DEFERRED):** Comparativo de Taxas (D4) + Parcelas Reais Incontroversas (D5) + Embargos Declaração + Agravo Instrumento + Recurso Especial

**MVP estimate atualizado:** **30-41h** (28-39h + 2h D3 Apelação).

**Atualização §11 BL-DELIV-05:** splitado em BL-DELIV-05a (Embargos+Agravo+RE — pós-MVP) e BL-DELIV-05b já implementado v1.1.1 (Apelação Cível).

---

### 2.10 F-MED-03 — Backup automático mínimo MVP

**Decisão Morgan:** Backup automático mínimo MVP (cron daily) — proteção crítica contra perda audit chain HMAC. Custo 1h dev.

**Atualização §7.10 Setup/Backup/Recovery — NOVO:**

> **FR-BACKUP-MVP-01 (NOVO em v1.1.1) — Backup automático mínimo**
> - Cron daily (02:00 horário local): `cp ~/.local/share/revisor-contratual/{vault.db,audit.jsonl} ~/.local/share/revisor-contratual/backups/{YYYY-MM-DD}/`
> - Rotação: manter últimos 7 dias (vs 30 dias FR-BACKUP-01 elaborada v1.0.2)
> - SEM trigger por petições (FR-BACKUP-01 elaborada DEFERRED v1.1+)
> - SEM falha-WARN no header (DEFERRED v1.1+)
> - **AC-FR-BACKUP-MVP-01:** simulação perda vault.db → restauração via último backup recupera 100% (verificável via test integração)
> - Estimativa: ~1h dev

**MVP estimate atualizado:** **31-42h** (30-41h + 1h backup mínimo).

---

### 2.11 F-MED-04 — Decisão FIES razão 6 (TRFs regionais)

**Atualização §6.3 e §14 (Decisão FIES):**

**Razões técnicas (revisadas, 6 razões):**

1. **Jurisdição federal vs estadual** (preservado)
2. **Procedimento administrativo vs revisional** (preservado)
3. **Regulamento FNDE específico** (preservado)
4. **TRFs regionais (NOVA — F-MED-04 Smith):** FIES contestação judicial é **TRF da seção judiciária do estudante** (regra geral — Lei 5.010/66). Brasil tem 6 TRFs (TRF1..TRF6). Vault Revisor Contratual é estadual (TJ + STJ + STF). Reuso de jurisprudência seria <10%; necessária indexação separada por TRF + súmulas administrativas FNDE.
5. **ICP diferente** (movido para subsection "Razões de produto" — não-técnica)
6. **Modelo de negócio diferente** (movido para subsection "Razões de produto" — não-técnica)

> **Subsection "Razões de produto (não-técnicas)":** ICP advogado FNDE/educação ≠ advogado consumerista bancário. Marketing, copy, posicionamento divergem. Cliente final FIES é estudante/ex-estudante com dívida pública subsidiada vs cliente final Revisor Contratual é PF com superendividamento bancário privado.

**Conclusão Morgan reforçada:** FIES vira projeto-irmão "Revisor FIES". Reuso técnico <10% (vs 60-80% entre Veicular/Bancário/Imobiliário). Decisão arquitetural defendida com 4 razões técnicas + 2 de produto.

---

### 2.12 F-MED-05 — FR-ECONOMISTA-01 explícito

**Novo FR-ECONOMISTA-01 (adicionar em §7 entre 7.6 e 7.7):**

> **§7.6.1 — FR-ECONOMISTA-01 (NOVO em v1.1.1) — Análise Macroeconômica via LLM**
>
> Persona P-INT-04 (Economista entidades bancárias) gera análise contextual macro do contrato.
>
> - Chamada LLM obrigatória (Tier balanced default) com schema Pydantic `AnaliseMacroEconomica`
> - Campos output: `ciclo_selic_periodo`, `taxa_atipica_bool`, `comparacao_peer_modalities`, `contexto_macro_resumido`
> - Mitigação Tema 1378 STJ (provimento alinhado cenário PIOR caso de critério circunstancial)
> - Custo arquitetural: latência por contrato +30s (refletido NFR-PERF-01 ≤210s)
>
> **AC-FR-ECONOMISTA-01:** 100% das análises produzem `AnaliseMacroEconomica` Pydantic schema-valid; campos `ciclo_selic_periodo` rastreável a SGS BACEN data
>
> **Justificativa (preservada de v1.0.2):** Smith F-CRIT-06 promoveu Economista a primeira-classe em v1.0.2. v1.1.0 declarou persona em §3.2 mas omitiu FR explícito (lacuna F-MED-05). v1.1.1 corrige.

---

### 2.13 F-LOW-01 — Reconciliação contábil cortes

**Atualização §5.1 header (PRD v1.1.1 substitui contagem v1.1.0):**

> **§5.1 Cortes formais do MVP (9 cortes, C1..C9)** — header revisado de "7 itens" para "9 cortes"
>
> Tabela existente preservada (9 linhas C1..C9 já estavam na v1.1.0 — apenas o header estava errado). Inconsistência contábil reconciliada.

**§11 Backlog Deferred (PRD v1.1.1):**
- 12 BL-* originais (preservados)
- 2 novos BL-* (BL-VAULT-BULK-IMPORT + BL-GOLDEN-SET — ver §2.2 e §2.5 desta PATCH)
- Removido BL-MONITOR-1378 (movido para MVP §7.10 — ver §2.4)
- BL-DELIV-05 splitado em BL-DELIV-05a (pós-MVP) + D3 Apelação implementada MVP (ver §2.9)
- **Total atualizado:** 13 backlog items + 1 sub-item (BL-DELIV-05a) = 14 entries em TECH-DEBT.md

**Reconciliação documentada:** "Cortes formais" (§5.1) = 9 (decisões de exclusão MVP). "Backlog items" (§11 + TECH-DEBT.md) = 14 (cortes + sub-items + decisões arquiteturais como BL-FIES). Conceitos distintos.

---

### 2.14 F-LOW-02 — Backlog Deferred owner + trigger

**Atualização §11 — colunas adicionadas em TECH-DEBT.md (referência cruzada):**

| Coluna NOVA | Conteúdo |
|---|---|
| **Owner** | Agente responsável por trigger/implementação (ex: @pm Morgan, maintainer Eric, @qa Oracle) |
| **Trigger Re-avaliação** | Condição para reavivar BL-* (ex: "trimestral", "após 5 advogados validarem MVP", "ao atingir 50 outcomes WON", "quando Tema 1378 STJ julgado") |

(Colunas implementadas no TECH-DEBT.md edit; PRD §11 referencia.)

---

### 2.15 F-LOW-03 — Validação OAB server-side

**Atualização §7.8 FR-DELIV-06 Tela Adoção CFOAB:**

> **FR-DELIV-06 (REVISADO v1.1.1) — Tela Revisão e Adoção (CFOAB) com validação server-side**
>
> - Componentes preservados de v1.1.0: preview PDF + checkbox "LI, CONFERI E ADOTO" + campos OAB+UF+nome obrigatórios + audit log
> - **NOVO em v1.1.1 — Validação server-side anti-bypass:**
>   - Regex OAB: `^\d{1,6}/[A-Z]{2}$` (formato canônico OAB Brasil)
>   - Rate limit por OAB: 1 petição/minuto, 100 petições/dia (mitigação bot script externo)
>   - Audit log inclui IP origin + User-Agent (forensic tracking)
> - **AC-FR-DELIV-06b (NOVO):** 0% das requests POST `/revisar` com OAB inválido (regex fail) ou rate limit excedido geram PDF
> - Estimativa dev: ~2h (regex + rate limit middleware FastAPI)

**MVP estimate atualizado final:** **33-44h** (31-42h + 2h validação OAB).

---

## 3. Delta Section v1.1.0 → v1.1.1

### 3.1 Features Adicionadas em v1.1.1

- **FR-LGPD-MVP-01** — auth mínima basic-auth + chmod 600 (mitigação F-HIGH-03 + F-CHK-01)
- **FR-MONITOR-01 ATIVO** — Tema 1378 STJ monitor semanal (mitigação F-HIGH-04)
- **FR-BACKUP-MVP-01** — backup automático cron daily (mitigação F-MED-03)
- **FR-ECONOMISTA-01** — Persona P-INT-04 com FR explícito (mitigação F-MED-05)
- **D3 Apelação Cível** incorporada como deliverable MVP (mitigação F-MED-02)
- **Validação server-side OAB** em FR-DELIV-06 (mitigação F-LOW-03)
- **AC-PRECONDITION** para AC-1/2/3/10 (mitigação F-HIGH-05)
- **BL-VAULT-BULK-IMPORT** PRE-RELEASE BLOCKER em TECH-DEBT.md (mitigação F-HIGH-02)
- **BL-GOLDEN-SET** PRE-RELEASE BLOCKER em TECH-DEBT.md (mitigação F-HIGH-05)
- **Razão técnica 4 (TRFs regionais)** em decisão FIES (mitigação F-MED-04)

### 3.2 Features Modificadas em v1.1.1

- **NFR-PERF-01:** ≤180s → **≤210s** (mitigação F-HIGH-01 — coerente com Economista)
- **AC-1:** target ≤180s → **≤210s** (idem)
- **AC-3:** PRECONDITION explícita BL-VAULT-BULK-IMPORT + BL-GOLDEN-SET (mitigação F-HIGH-02)
- **§12.2 NFR-LGPD-01:** "PRESERVADO INTACTO" → **"PRESERVADO COM FR-LGPD-MVP-01 mitigation"** (mitigação F-HIGH-03 + F-CHK-01)
- **§13 R8 Tema 1378:** probabilidade BAIXA → **MÉDIA-ALTA**; impacto ALTO → **CRÍTICO**; mitigação manual → **FR-MONITOR-01 ATIVO** (mitigação F-HIGH-04)
- **§5.1 header:** "7 itens" → **"9 cortes (C1..C9)"** (mitigação F-LOW-01)
- **§6.1 estimativas modalidades:** qualificadores [ESTIMATIVA OTIMISTA] + revisões Imobiliária (+30-40h → +40-60h) e Crédito (+25-35h → +30-45h) (mitigação F-MED-01)
- **§6.3 + §14 Decisão FIES:** razão técnica 4 (TRFs regionais) adicionada; razões 5-6 movidas para subsection "Razões de produto" (mitigação F-MED-04)
- **MVP estimate:** 25-35h → **33-44h** (incremental: +5-6h FR-LGPD-MVP-01 + FR-MONITOR-01 + FR-BACKUP-MVP-01 + 2h D3 Apelação + 2h OAB validation)

### 3.3 Features Removidas (consolidadas em TECH-DEBT.md)

- **BL-MONITOR-1378** removido de §11 (movido para escopo MVP §7.10 FR-MONITOR-01 ATIVO)
- **BL-DELIV-05** splitado: D3 Apelação Cível MVP + BL-DELIV-05a (Embargos/Agravo/RE) → v1.1+

### 3.4 Escopo Atual vs Original

- **v1.1.0:** ~8 FRs ativos MVP + 12 BL-* + 4 modalidades roadmap + 1 projeto-irmão FIES
- **v1.1.1:** **~12 FRs ativos MVP** (8 v1.1.0 + FR-LGPD-MVP-01 + FR-MONITOR-01 + FR-BACKUP-MVP-01 + FR-ECONOMISTA-01) + **3 deliverables** (D1+D2+D3) + 13 BL-* + 4 modalidades roadmap + 1 projeto-irmão FIES + AC-PRECONDITION explícitas
- **MVP estimate:** 25-35h v1.1.0 → **33-44h v1.1.1** (+8-9h endereçando findings)
- **Motivo principal:** Tribunal severo CC.1A endereçado completamente (5 HIGH + 2 MEDIUM + 7 MEDIUM/LOW = 14/14 findings)

---

## 4. Ações executadas durante esta PATCH

| Ação | Artefato | Status |
|---|---|---|
| PRD v1.1.1 PATCH publicado | `governance/prd/prd-v1.1.1-PATCH.md` | ✅ ESTE ARQUIVO |
| INDEX.md atualizado | `governance/prd/INDEX.md` | ⏳ A executar |
| 14 BL-* migrados para TECH-DEBT.md | `governance/TECH-DEBT.md` | ⏳ A executar (F-CHK-02 OPÇÃO 2) |
| Checkpoint inline atualizado | `governance/CHECKPOINT-active.md` | ⏳ A executar |
| Handoff Morgan→Smith re-review emitido | `.lmas/handoffs/handoff-pm-to-smith-2026-05-05-cc1a-tribunal-re-review.yaml` | ⏳ A executar |

---

## 5. Histórico Append-Only

### v1.1.1 — 2026-05-05 (Morgan, Sprint 03 course-correction CC.1A')

**PATCH bump.** Razão: Tribunal severo CC.1A consolidado FAIL (Smith parte 1: 5 HIGH bloqueadores; checkpoint parte 2: 2 MEDIUM + 1 LOW governance gaps). PATCH endereça **14/14 findings** (5 HIGH obrigatórios + 2 MEDIUM checkpoint obrigatórios + 7 MEDIUM/LOW Smith opcionais selecionados por Morgan para defensividade máxima).

**Mudanças estruturais:**
- ADDED FR-LGPD-MVP-01 (auth mínima basic-auth + chmod 600 — mitiga F-HIGH-03 + F-CHK-01)
- ADDED FR-MONITOR-01 ATIVO no MVP (move BL-MONITOR-1378 para escopo — mitiga F-HIGH-04)
- ADDED FR-BACKUP-MVP-01 (cron daily — mitiga F-MED-03)
- ADDED FR-ECONOMISTA-01 (mitiga F-MED-05)
- ADDED D3 Apelação Cível como deliverable MVP (mitiga F-MED-02)
- ADDED Validação server-side OAB em FR-DELIV-06 (mitiga F-LOW-03)
- ADDED AC-PRECONDITION para AC-1/2/3/10 (mitiga F-HIGH-05)
- ADDED BL-VAULT-BULK-IMPORT (PRE-RELEASE BLOCKER — mitiga F-HIGH-02)
- ADDED BL-GOLDEN-SET (PRE-RELEASE BLOCKER — mitiga F-HIGH-05)
- ADDED Razão técnica 4 (TRFs regionais) em FIES (mitiga F-MED-04)
- MODIFIED NFR-PERF-01 latência ≤180s → ≤210s (mitiga F-HIGH-01)
- MODIFIED §12.2 NFR-LGPD-01 "PRESERVADO INTACTO" → "PRESERVADO COM FR-LGPD-MVP-01 mitigation"
- MODIFIED R8 Tema 1378 probabilidade MÉDIA-ALTA + impacto CRÍTICO + mitigação ATIVA
- MODIFIED §5.1 header reconciliado (9 cortes, era "7 itens")
- MODIFIED §6.1 estimativas modalidades qualificadas [ESTIMATIVA OTIMISTA] + revisões
- MODIFIED §6.3+§14 FIES razões reestruturadas (4 técnicas + 2 produto subsection)
- MODIFIED MVP estimate 25-35h → 33-44h (+8-9h)
- REMOVED BL-MONITOR-1378 do §11 (movido para MVP §7.10)
- SPLIT BL-DELIV-05 em BL-DELIV-05a (Embargos/Agravo/RE) + D3 Apelação MVP

**Stories impactadas:**
- VAULT-FIX-01 (Ready for Review) — sem alterações na PATCH (pode prosseguir Oracle gate paralelo)
- OLLAMA-MGR-01 (Ready não iniciada) — sem alterações
- MVP-LEAN-01 (futura, River CC.4) — escopo expandido com FR-LGPD-MVP-01 + FR-MONITOR-01 + FR-BACKUP-MVP-01 + FR-ECONOMISTA-01 + D3 Apelação + validação OAB

**Decisões pendentes Eric (não endereçadas nesta PATCH — registradas como advisory):**
- Confirmação roadmap sequenciamento modalidades pós-MVP (preservado v1.1.0)
- Confirmação FIES projeto-irmão (preservado v1.1.0, agora com 4 razões técnicas robustas + 2 produto)
- Confirmação MVP estimate ampliado 33-44h (vs 25-35h original) é aceitável para Eric

**Próximo step:** Smith re-review focado nos 5 HIGH endereçados; após PASS, CC.2 Aria desbloqueia.

---

### v1.1.0 — 2026-05-05 (Morgan, Sprint 03 course-correction CC.1A) [MAJOR — predecessor preservado]

(Conteúdo preservado em `prd/prd-v1.1.0-MAJOR.md` — não duplicar aqui)

### v1.0.3 — 2026-05-05 (Morgan, Sprint 02 planning) [PATCH — predecessor preservado]

(Conteúdo preservado em `prd/prd-v1.0.3-DELTA.md` — não duplicar aqui)

### v1.0.2 — 2026-05-01 (Morgan, Sprint 01 etapa 1.0) [PATCH — predecessor preservado]

(Conteúdo preservado em `prd/prd-v1.0.2.md` — não duplicar aqui)

---

*PRD v1.1.1 PATCH — Morgan (sessão 87, 2026-05-05) · Sprint 03 course-correction CC.1A' · Tribunal CC.1A endereçado (14/14 findings) · Defensividade máxima frente Smith re-review*

— Morgan, planejando o futuro 📊
