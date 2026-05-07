---
type: prd
title: "Revisor Contratual — PRD v2.0.0 (Cloud SaaS BYOK Multi-Tenant)"
project: revisor-contratual
version: "2.0.1"
last_updated: "2026-05-07T17:15"
status: draft
patches:
  - "Phase 3.1 (2026-05-07T15:45): PDF Generation FR-OUTPUT-01..04 + FR-APPROVE-01 simplificado + FR-D3-01 PDF + NFR-PDF-01 + SP04-PDF-OUTPUT-01 story (Eric clarification — advogado revisa PDF offline)"
  - "Phase 5.2 (2026-05-07T17:15): Smith Phase 5 patches CRITICAL — FR-OUTPUT-D3-01..05 (F-003) + FR-NOTIFY-01..05 (F-007) + Delta v2.0.0 → v2.0.1 + Changelog entry. Eric ratifica Path A (Smith RECOMENDADO)"
previous_version: "1.1.2"
audience: "Eric Claudino (founder), 4 escritórios beta launchers (TBD)"
author: "@pm Trinity (Morgan)"
sprint: "04"
phase: 3
tags:
  - project/revisor-contratual
  - prd
  - sprint-04
  - cloud-pivot
  - saas-byok
  - multi-tenant
---

# PRD v2.0.0 — Revisor Contratual (Cloud SaaS BYOK Multi-Tenant)

> ⚠️ **MAJOR BUMP v1.1.2 → v2.0.0** — pivot estrutural: local single-tenant on-premise → cloud SaaS B2B BYOK multi-tenant. Esta versão SUPERSEDES PRD v1.1.2 integralmente. Stories Sprint 03 (MVP-LEAN-01) ficam como histórico Sprint 03 anchor; Sprint 04 começa novo fluxo de stories.

---

## 1. Sumário Executivo

Revisor Contratual evolui de ferramenta local single-tenant (Sprint 03 MVP-LEAN-01 — análise CDC Veicular PF on-premise) para **plataforma SaaS B2B multi-tenant** voltada a escritórios de advocacia brasileiros. O pivot foi motivado por (a) constraint estrutural de RAM em hardware solo (Smith CC.41 F-A1) e (b) ambição de modelo de negócio escalável.

**4 mudanças estruturais Sprint 04:**

1. **Cloud LLM via BYOK Anthropic** — cada escritório cliente cadastra sua própria API key Anthropic; Eric não absorve custo variável de tokens
2. **Multi-tenant PostgreSQL Pool+RLS** — milhares de escritórios isolados em mesmo schema, RLS PostgreSQL battle-tested
3. **4 doctypes simultâneos** — FIES + CDC Veicular + Bancário + Imobiliário (Sprint 03 cobria só Veicular)
4. **Per-approval billing** — Eric ganha por documentação aprovada pelo advogado (não assinatura genérica)

**Consequência LGPD crítica:** Eric vira **OPERADOR LGPD** (provê ferramenta SaaS); escritório é **CONTROLADOR** (relação direta com cliente final + responsabilidade pela base legal do tratamento).

---

## 2. Público-alvo

**Cliente direto (B2B):** Escritórios de advocacia brasileiros — solo a médio porte (1-30 advogados típico).

**Persona primária do escritório:** Advogado(a) cível ou bancário que revisa contratos de financiamento (CDC, FIES, Bancário, Imobiliário) buscando irregularidades para fundamentar ações judiciais.

**Cliente final (do escritório, NÃO do Eric):** Pessoa física que assinou contrato de financiamento e procura escritório por suspeita de cláusulas abusivas.

**Beta launchers Sprint 04:** 4 escritórios TBD (Eric identifica pré-launch).

**Out-of-target Sprint 04:** Pessoa física direta (sem escritório), advogados pro-bono em massa, departamentos jurídicos corporativos (perfil enterprise — futuro).

---

## 3. Modelo de Negócio

**BYOK + Hybrid pricing**:

- **Cliente paga sua API key Anthropic direto** (~R$ 4,18/análise CDC Veicular típica via stack Hybrid Sonnet+Haiku — ADR-014 + Atlas v2 Section 3)
- **Eric cobra**: assinatura mensal base + per-approval fee quando advogado clica "Aprovar" relatório

**Tier structure (estrutura — valores absolutos pendente Eric+Mifune):**

| Tier | Base mensal | Per-approval | Aprovações inclusas |
|---|---|---|---|
| Starter | R$ X | R$ Y | N inclusas |
| Pro | R$ X | R$ Y | N inclusas |
| Enterprise | Negociado | Negociado | Custom |

⚠️ **Cross-domain Mifune flag**: valores absolutos R$ são decisão Eric+Mifune (business). Atlas v2 Section 3 sugeriu ranges (R$ 200-500 base / R$ 30-50 per-approval) baseado em benchmark BR jurídico (Astrea/ADVBOX) e outcome-based SaaS 2026.

**Margem Eric:** ~10× custo manual de revisão (advogado faria em 2-4h × R$ 200-300/h = R$ 400-1200/análise; Eric cobra R$ 50 = sweet spot Atlas).

---

## 4. Functional Requirements (FRs)

### Authentication & Multi-Tenant

- **FR-AUTH-01** — Cadastro de escritório (tenant) com dados CNPJ, razão social, advogado responsável; emissão UUID `tenant_id` único e isolamento RLS automático em todas tabelas (ref. ADR-017)
- **FR-AUTH-02** — Gestão de usuários internos do escritório (CRUD advogados); cada usuário associado a exatamente um `tenant_id` via `users.tenant_id` FK
- **FR-AUTH-03** — Login com email + senha; session JWT com `tenant_id` claim para session context middleware (ref. ADR-017 RLS)

### BYOK API Key Management

- **FR-API-KEY-01** — Tela de Settings escritório para cadastrar Anthropic API key; validação ao submeter via ping `GET https://api.anthropic.com/v1/models` (ref. ADR-014)
- **FR-API-KEY-02** — Encryption at rest via PostgreSQL `pgcrypto.pgp_sym_encrypt(key, master_key)` (ref. ADR-014)
- **FR-API-KEY-03** — Rotação dual-key 24h overlap window (`current_key + pending_key` state machine — ref. ADR-014)
- **FR-API-KEY-04** — Revoke self-service (escritório clica "Revogar") + suspend tenant até key nova; audit log evento com timestamp + user_id; key sempre truncada em logs como `sk-ant-...XYZ`

### Vision OCR

- **FR-OCR-01** — Análise de PDFs via Claude Sonnet 4.6 vision (ref. ADR-015); image preprocessing resize 1568×1568 + JPEG quality 85
- **FR-OCR-02** — Multi-page paralelo via `asyncio.gather(timeout=120s/página)` — abort completo se ≥1 página falhar (interdependência contratual)
- **FR-OCR-03** — Cache SHA-256 de resultado OCR em `ocr_cache (pdf_hash_sha256, tenant_id, markdown_text, ...)` com TTL 90 dias (ref. ADR-015)

### Multi-Doctype

- **FR-DOCTYPE-01** — UI selector dropdown S2 obrigatório com 4 opções: FIES / CDC Veicular / Bancário / Imobiliário (advogado escolhe ao fazer upload)
- **FR-DOCTYPE-02** — Fallback LLM classifier Haiku 4.5 (~R$ 0,005/análise) se advogado pular o selector — ref. ADR-016
- **FR-DOCTYPE-03** — `DoctypeDispatcher` Strategy pattern com 4 concrete classes (FIES/Veicular/Bancário/Imobiliário); persona prompts adaptados por doctype (16 arquivos: 4 personas × 4 doctypes)
- **FR-DOCTYPE-04** — Jurisprudência SHARED com `doctype_tag VARCHAR(20)` filter por análise — ref. ADR-016

### Pipeline Análise (4 Personas + Juiz)

- **FR-PERSONAS-01** — 4 personas paralelas via `asyncio.gather` rodando Claude Haiku 4.5 (Atlas v1+v2 stack Hybrid Anthropic)
- **FR-PERSONAS-02** — Juiz Revisor consolida outputs das 4 personas via Claude Sonnet 4.6 (premium para síntese final — ref. ADR-014 + Atlas v1)
- **FR-PERSONAS-03** — Personas adaptam prompt por doctype (`{persona}_{doctype}.txt` carregado pelo DoctypeDispatcher — ref. ADR-016)

### PDF Generation

- **FR-OUTPUT-01** — Sistema gera **PDF do relatório de análise final** após Juiz consolidação concluir; PDF inclui: identificação contrato (UF, data, doctype), resumo executivo, achados das 4 personas, parecer Juiz, jurisprudência citada
- **FR-OUTPUT-02** — PDF é gerado server-side (não LLM-generated — usa template Jinja2 → PDF via WeasyPrint OR ReportLab)
- **FR-OUTPUT-03** — PDF disponível para download no dashboard escritório via botão "Baixar PDF Análise" + audit log evento download (timestamp + user_id)
- **FR-OUTPUT-04** — PDF deve ser pesquisável (texto extraível, não imagem); inclui marca d'água sutil "Análise IA — Revisão por Advogado Obrigatória" no rodapé

### FR-OUTPUT-D3 — Petição D3 PDF (CRÍTICO Smith F-003)

| ID | Descrição | Prioridade |
|----|-----------|------------|
| FR-OUTPUT-D3-01 | Sistema gera petição em PDF separado do relatório de análise (output flow distinto, não bundled) | MUST |
| FR-OUTPUT-D3-02 | Petição usa template Jinja2 distinto em `templates_d3/{doctype}.j2` — NÃO reutiliza template do relatório de análise | MUST |
| FR-OUTPUT-D3-03 | Estrutura legal: cabeçalho identificador (Apelação Cível / Ação Revisional / etc) + fundamentação + pedidos + fecho legal | MUST |
| FR-OUTPUT-D3-04 | Watermark obrigatório: "Petição IA — Revisão por Advogado Obrigatória" (similar análise) | MUST |
| FR-OUTPUT-D3-05 | Geração D3 captura audit log (timestamp + user_id + analysis_id + tenant_id) similar FR-AUDIT-01 | MUST |

**NOTA:** Conteúdo legal específico por doctype (FIES vs CDC Veicular vs Bancário vs Imobiliário) será redigido por advogado especializado (cross-domain Eric — flag em Section 12). Esta seção define apenas o MECANISMO técnico — não o conteúdo legal substantivo. Cross-reference: FR-D3 abaixo cobre estrutura legal de alto nível; FR-OUTPUT-D3 cobre mecanismo de geração PDF.

### Petição D3 (Apelação Cível)

- **FR-D3-01** — Geração de petição Apelação Cível **em PDF** quando análise identifica irregularidades + decisão adversa anexa; mesmo flow download FR-OUTPUT-03 (advogado baixa PDF da peça pronta para uso)
- **FR-D3-02** — Templates por doctype em `bloco_workflow/templates_d3/{doctype}.txt` — **conteúdo legal pendente Eric advogado** (Trinity define ESTRUTURA, não conteúdo jurídico)

### FR-NOTIFY — Notificação Async de Análise (CRÍTICO Smith F-007)

| ID | Descrição | Prioridade |
|----|-----------|------------|
| FR-NOTIFY-01 | Email transactional disparado quando análise muda para `pending_review` (provider TBD: SendGrid / Resend / AWS SES — decisão cross-domain pricing) | MUST |
| FR-NOTIFY-02 | In-app banner persistente em S3 dashboard ao re-login: "Análise X pronta para revisão" com link direto S6 | MUST |
| FR-NOTIFY-03 | Settings preference per usuário em S7 (Tab "Notificações"): email on/off, in-app on/off, web push (future opt-in) | MUST |
| FR-NOTIFY-04 | Email content: assunto "Análise pronta para revisão — {doctype}", corpo com link direto S6 PDF Ready + CTA "Revisar análise" | MUST |
| FR-NOTIFY-05 | Notification events captured em audit chain (HMAC) para rastreabilidade compliance — quando email enviado, quando user opened (se trackeable), quando in-app banner mostrado | SHOULD |

**NOTA:** Provider de email transactional (SendGrid vs Resend vs AWS SES) será decidido em pricing analysis cross-domain (Mifune business OR Eric direto — flag em Section 12). Implementação @dev usa interface abstrata `EmailProvider` para permitir swap entre providers sem refactor de código de negócio.

### Workflow Aprovação (Billing Trigger)

- **FR-APPROVE-01** — UI simples no dashboard: análise listada com 3 ações — **[Baixar PDF]** + **[Aprovar]** + **[Desaprovar]**. Aprovar/Desaprovar são clicks instantâneos (sem necessidade de UI de revisão completa do relatório dentro do app — advogado revisa o PDF baixado offline em sua ferramenta preferida)
- **FR-APPROVE-02** — State machine análise: `created → ocr_processing → personas_running → judge_consolidating → pending_review → approved | rejected | expired` (ref. ADR-018)
- **FR-APPROVE-03** — Rejection requer modal com `rejection_reason` enum (`pii_incorrect | analysis_inadequate | doctype_wrong | other` + free text); advogado pode reabrir (`rejected → pending_review`) sem cobrança duplicada
- **FR-APPROVE-04** — Análise sem ação após 30 dias `pending_review` vira `expired` (não cobra)

### Billing

- **FR-BILLING-01** — Approval click emite `billing_event` async com webhook Stripe — cria invoice line item (ref. ADR-018)
- **FR-BILLING-02** — Mensal Stripe agrega + emite fatura recorrente para escritório; pagamento via cartão de crédito ou PIX boleto (depende capacidade Stripe Brasil)
- **FR-BILLING-03** — Tier enforcement: tabela `tenant_subscription` controla `monthly_quota_approvals` + `monthly_used` + `reset_date`; status `quota_exceeded` bloqueia novas análises com mensagem PT-BR
- **FR-BILLING-04** — ⚠️ Valores absolutos R$ pricing (base + per-approval) **pendente Eric+Mifune cross-domain** (Atlas v2 Section 3 ranges sugeridos)

### Auditoria & LGPD

- **FR-AUDIT-01** — Endpoint `GET /api/tenant/audit/isolation` retorna metadata para escritório auditar isolamento (counts, RLS policies ativas, último login per user) — ref. ADR-017
- **FR-AUDIT-02** — Audit chain HMAC PRESERVADO Sprint 03 (`bloco_audit/genesis.py + chain.py`) adapta `tenant_id` no payload — ref. ADR-005 + ADR-017
- **FR-LGPD-01** — DPA Eric-escritório obrigatório no onboarding (Eric advogado redige texto, sistema apresenta + escritório aceita digitalmente)
- **FR-LGPD-02** — TOS/EULA do SaaS declarando explicitamente papel **operador** Eric (não controlador)

### Dashboard & Admin

- **FR-DASH-01** — Dashboard escritório (advogado): listagem de análises com filtros (status/doctype/data), histórico billing, gestão de usuários, settings API key
- **FR-DASH-02** — Métricas escritório: total análises mês, taxa de aprovação, taxa de rejeição, custo agregado API + Eric fees
- **FR-ADMIN-01** — Admin Eric (super-user): listar tenants, ver billing agregado por tenant, suspend/reactivate tenant, ver audit logs cross-tenant (read-only para troubleshooting)

---

## 5. Non-Functional Requirements (NFRs)

- **NFR-PERF-01** — Latência OCR ~5s para PDF 12 páginas via paralelismo `asyncio.gather` (Sonnet 4.6 vision); persona análise total ≤30s (4 personas paralelas + Juiz consolidação)
- **NFR-PDF-01** — Geração PDF ≤3s para relatório típico (12 págs análise + 5 jurisprudências); failover graceful se template render falhar (mensagem PT-BR "PDF temporariamente indisponível, tente novamente")
- **NFR-COST-01** — Custo escritório < R$ 5/análise CDC Veicular típico (12 págs); Imobiliário (25 págs) pode escalar até R$ 7-10/análise (Atlas v2 Section 3 multiplier 2,1×)
- **NFR-LGPD-01** — 100% RLS coverage em tabelas com `tenant_id` (validado por test integração); encryption at rest pgcrypto em `tenant_api_keys`; TLS 1.3 everywhere — ref. ADR-017 3 camadas
- **NFR-SCALE-01** — Suportar 100+ escritórios concurrent sem degradação RLS (overhead 1-5% per Atlas v2 benchmark)
- **NFR-AUDIT-01** — Audit chain HMAC PRESERVADO de Sprint 03 — invariante: cada entry tem hash do anterior + payload com `tenant_id`; chain quebrada = alerta crítico
- **NFR-AVAILABILITY-01** — Uptime objetivo 99.5% (admite Anthropic downstream + manutenções planejadas); status page para escritórios
- **NFR-SUPPORT-01** — Onboarding self-service (escritório consegue cadastrar API key + fazer 1ª análise sem ajuda Eric); suporte email/chat para edge cases

---

## 6. Constraints (CON)

- **CON-LGPD-01** — Eric=operador, escritório=controlador (DPA mandatory) — não negociável; ref. Art. 5º LGPD
- **CON-PROVIDER-01** — Anthropic only (A1 Eric autorização Phase 1.7) — Sprint 04 não suporta multi-provider
- **CON-BUDGET-01** — Per-approval pricing alinha incentivo qualidade Eric; rejection rate alta (>30%) sinaliza quality issue, não meta de receita
- **CON-VOLUME-01** — Volume aspiracional não definido (Eric C3); arquitetura suporta escala variável (Pool+RLS)
- **CON-STACK-01** — Anthropic Hybrid (Sonnet OCR+Juiz, Haiku 4 personas) — ref. ADR-014 + Atlas judgment B
- **CON-OFFLINE-01** — App requer internet (vision LLM cloud); sem internet = sem análise nova (cache OCR ainda servível para re-views)

---

## 7. Out of Scope (OOS)

- **OOS-01** — Multi-provider abstraction (OpenRouter, OpenAI, Gemini) — Sprint 05+ se demanda emerge
- **OOS-02** — Customer-managed KMS key (BYOK true with own KMS) — enterprise tier futuro (50+ tenants OR demanda explícita)
- **OOS-03** — Doctypes além dos 4 (Trabalhista, Empresarial, Penal, ...) — backlog se Sprint 04 prove-out tracion
- **OOS-04** — Mobile app nativo (iOS/Android) — apenas web responsive Sprint 04; PWA opcional Sprint 05+
- **OOS-05** — Sub-keys per advogado dentro do escritório (Anthropic não suporta nativo) — Quota Interna via audit é workaround Sprint 04
- **OOS-06** — Funcionalidade offline / on-premise — cloud-first definitivo Sprint 04
- **OOS-07** — Integração com sistemas jurídicos externos (Astrea, ADVBOX, CPJ) — possível Sprint 05+ via API
- **OOS-08** — Relatório PDF customizado per escritório (white-label) — backlog
- **OOS-09** — Notificações push / email automáticas avançadas — Sprint 04 entrega básico (status updates)
- **OOS-10** — Compliance frameworks além LGPD (HIPAA, SOC 2 Type II) — futuro enterprise

---

## 8. Delta History (OBRIGATÓRIO per `prd-governance.md`)

### Delta v2.0.0 → v2.0.1 (current — Smith Phase 5 patches CRITICAL)

**Patches motivados por Smith adversarial review (commit 4519ef1) — verdict CONCERNS + 4 CRITICAL findings.**

#### F-003 — FR-OUTPUT-D3 adicionado (5 FRs)
- Spec mecanismo PDF petição D3 separado da análise (gap identificado: UX S6 expõe "Baixar Petição D3" sem FR específico)
- Template Jinja2 dedicado, estrutura legal, watermark, audit log
- Conteúdo legal templates: cross-domain Eric advogado especializado (mantém Section 12 pendência)

#### F-007 — FR-NOTIFY adicionado (5 FRs)
- Notificação async de análise pronta (gap identificado: UX S5 promete "você será notificado" mas PRD não tinha FR mecanismo)
- Email transactional + in-app banner + settings preference + future web push
- Provider email TBD pricing cross-domain (interface `EmailProvider` permite swap)
- Audit chain integrado para compliance LGPD

#### Não modificado nesta versão (CRITICAL pendentes)
- **F-012** (DPA storage schema) → endereçado por **Aria Phase 5.3 ADR-019** (próximo Skill na cadeia Path A)
- **F-016** (LGPD subprocessor argument) → cross-domain Eric advogado especializado paralelo (5-15 dias)

#### Não modificado nesta versão (debt aceitável)
- 19 HIGH + 13 MEDIUM + 2 LOW Smith findings → TECH-DEBT.md CC.43+ (defer post Phase 6 PR creation)

#### Escopo Atual vs v2.0.0

| Métrica | v2.0.0 | v2.0.1 | Delta |
|---|---|---|---|
| FRs totais | ~25 | ~35 | +10 (5 D3 + 5 NOTIFY) |
| Seções FR | 13 | 15 | +2 (FR-OUTPUT-D3 + FR-NOTIFY) |
| Smith CRITICAL fechados via PRD | 0/4 | 2/4 | F-003 + F-007 |

---

### Delta v1.1.2 → v2.0.0 (MAJOR pivot — preserved histórico)

### Features Adicionadas

- **Multi-tenant SaaS** (todas FR-AUTH-* + FR-API-KEY-* + FR-AUDIT-*)
- **BYOK API key management** (FR-API-KEY-01..04)
- **Vision OCR cloud** (FR-OCR-01..03 substituindo marker-pdf+Surya local)
- **Multi-doctype dispatcher** (FR-DOCTYPE-01..04) — escopo expandido de 1 doctype (Veicular) para 4 (FIES + Veicular + Bancário + Imobiliário)
- **PDF Generation server-side** (FR-OUTPUT-01..04) — relatório análise + petição D3 ambos em PDF para download offline; workflow advogado revisa PDF na sua ferramenta preferida (Adobe/Foxit), retorna ao app apenas para Aprovar/Desaprovar
- **Workflow simplificado approval** (FR-APPROVE-01 simplificado) — sem UI de revisão complexa dentro do app; click instantâneo Aprovar/Desaprovar após review offline do PDF
- **Per-approval billing** (FR-APPROVE-01..04 + FR-BILLING-01..04) — modelo de receita novo
- **Dashboard escritório + Admin Eric** (FR-DASH-* + FR-ADMIN-01)
- **DPA + TOS operador** (FR-LGPD-01..02) — formaliza papel operador

### Features Modificadas

- **OCR mechanism**: marker-pdf + Surya local → Claude Sonnet 4.6 vision cloud (mantém função, muda implementação completa)
- **LLM stack**: Sabia 7B + Qwen 7B/3B Ollama local → Anthropic API cloud (Sonnet 4.6 + Haiku 4.5)
- **Pipeline 4 personas**: lógica preservada, mas adapta-se por doctype via Strategy pattern
- **Audit chain HMAC**: preservado, adapta `tenant_id` no payload

### Features Removidas

- **OCR local marker-pdf + Surya** — substituído por Vision LLM (sem fallback local)
- **Auto-Ollama lifecycle management** — sem Ollama no cloud (ADR-011 superseded)
- **Mitigação Sabia Q4 Qwen fallback** — sem LLM local (ADR-010 superseded)
- **BACKUP_DIR + pseudonimização HMAC LGPD on-premise** — Eric vira operador; escritório controla pseudonimização (ADR-009 superseded)
- **SQLite vector store** — substituído por PostgreSQL pgvector multi-tenant (ADR-007 superseded)

### Escopo Atual vs Original

| Métrica | v1.1.2 (Sprint 03) | v2.0.0 (Sprint 04) | Delta |
|---|---|---|---|
| Doctypes suportados | 1 (CDC Veicular) | 4 (FIES + Veicular + Bancário + Imobiliário) | +3 |
| Modelo de deploy | Local on-premise (1 user) | Cloud SaaS multi-tenant (N escritórios) | Estrutural |
| LLM stack | Local Ollama (Sabia + Qwen) | Cloud Anthropic (Sonnet + Haiku) | Estrutural |
| Modelo de negócio | N/A (uso interno Eric) | Hybrid base + per-approval | Novo |
| Papel LGPD Eric | Controlador | Operador | Estrutural |
| FRs totais | ~13 (PRD v1.1.2) | ~25 (PRD v2.0.0) | +12 |

---

## 9. Changelog

### v2.0.1 (2026-05-07) — Smith Phase 5 patches CRITICAL

- **Added:** FR-OUTPUT-D3-01..05 (petição D3 PDF dedicated flow) — addresses Smith F-003
- **Added:** FR-NOTIFY-01..05 (notification mechanism async) — addresses Smith F-007
- **Section Delta:** v2.0.0 → v2.0.1 com escopo +10 FRs e 2/4 CRITICAL fechados via PRD
- **Reason:** Smith adversarial review (commit 4519ef1) verdict CONCERNS + 4 CRITICAL findings — patches mandatory antes Phase 7 implementation. Eric ratifica Path A (Smith RECOMENDADO).
- **Refs:** governance/qa/smith-sp04-pivot-adversarial.md (commit 4519ef1)
- **Pending CRITICAL:** F-012 (Aria Phase 5.3 ADR-019 DPA storage schema) + F-016 (cross-domain Eric advogado LGPD subprocessor argument)
- **Path A chain progress:** step 2/6 done (Trinity Phase 5.2)

### v2.0.0 (2026-05-07) — MAJOR BUMP — Cloud SaaS BYOK Pivot

- **Added:** 12+ FRs novos (multi-tenant, BYOK, vision OCR, 4 doctypes, billing, dashboard, LGPD operador)
- **Changed:** OCR mechanism, LLM stack, pipeline doctype-aware
- **Removed:** OCR local, Ollama lifecycle, LGPD on-premise pseudonimização
- **Reason:** Smith CC.41 F-A1 demonstrou hardware solo inviável + ambição modelo SaaS B2B escalável. Eric autorizou pivot Phase 1.7-1.7.1 (A1 Anthropic only / B Hybrid stack / C3 volume aspiracional / D-c per-approval billing).
- **References:** Atlas v1+v2 research, 5 ADRs Sprint 04 Phase 2.1 (014/015/016/017/018), 5 ADRs superseded (007/009/010/011/013)

### v1.1.2 (anterior — preserved Sprint 03 anchor)

PRD on-premise local single-tenant CDC Veicular PF — preservado em branch `feat/mvp-lean-01-task1-layout-base @ d53011e` para histórico Sprint 03.

---

## 10. Stories Impact

### Sprint 03 stories — status update

- **MVP-LEAN-01** (Sprint 03 Phase 0 implementação local) — **deprecated** parcial: arquitetura local substituída, mas story permanece como histórico documentado. Não é "rolled into" Sprint 04 (paradigma diferente).

### Sprint 04 stories sugeridas (Trinity sugere — @sm cria depois)

Sequência recomendada (dependências):

1. **SP04-AUTH-01** — Multi-tenant authentication + tenant onboarding (FR-AUTH-01..03)
2. **SP04-LGPD-01** — DPA + TOS operador + audit isolation endpoint (FR-LGPD-01..02 + FR-AUDIT-01) — paralelo a SP04-AUTH-01 pois Eric advogado redige DPA
3. **SP04-BYOK-01** — API key management (cadastro/validação/rotation/revocation) (FR-API-KEY-01..04)
4. **SP04-OCR-01** — Vision OCR Sonnet 4.6 + cache (FR-OCR-01..03)
5. **SP04-DOCTYPE-DISPATCHER-01** — Strategy pattern infrastructure (FR-DOCTYPE-01..04) — sem prompts ainda
6. **SP04-DOCTYPE-VEICULAR-01** — Adaptação personas + jurisprudência + D3 template Veicular (validar pipeline com tipo conhecido)
7. **SP04-DOCTYPE-FIES-01** — Adaptação FIES
8. **SP04-DOCTYPE-BANCARIO-01** — Adaptação Bancário
9. **SP04-DOCTYPE-IMOBILIARIO-01** — Adaptação Imobiliário
10. **SP04-PDF-OUTPUT-01** — Geração PDF relatório (template Jinja2 + WeasyPrint/ReportLab) + petição D3 PDF (FR-OUTPUT-01..04 + FR-D3-01) — depende SP04-DOCTYPE-DISPATCHER-01
11. **SP04-APPROVE-01** — Workflow aprovação + state machine (FR-APPROVE-01..04) — depende SP04-PDF-OUTPUT-01
12. **SP04-BILLING-01** — Stripe integration + billing event webhook (FR-BILLING-01..04) — depende SP04-APPROVE-01
13. **SP04-DASH-01** — Dashboard escritório: listagem análises + filtros + botões [Baixar PDF] + [Aprovar] + [Desaprovar] (FR-DASH-01..02)
14. **SP04-ADMIN-01** — Admin Eric super-user (FR-ADMIN-01)

Total estimativa stories: **~14**. SM (River) refina granularidade + estimativas em Phase 6+ (story creation).

---

## 11. Cross-references

### Atlas Research

- **Atlas v1** (`governance/research/openrouter-vision-ocr-viability.md`) — OCR landscape + LGPD framework + model benchmarks
- **Atlas v2** (`governance/research/byok-saas-multitenant-pricing-v2.md`) — BYOK security + multi-tenant Pool+RLS + Hybrid pricing + LGPD operador

### ADRs Sprint 04 Phase 2.1 (Aria)

- **ADR-014** Provider Abstraction Anthropic + BYOK — supersedes ADR-010 + ADR-011
- **ADR-015** Vision OCR Architecture — partial supersede ADR-013
- **ADR-016** Multi-Doctype Dispatcher Strategy
- **ADR-017** Multi-Tenant Pool+RLS + LGPD Operador (BACKBONE) — supersedes ADR-007 + ADR-009
- **ADR-018** SaaS Pricing Hybrid + Billing State Machine

### Predecessor

- **PRD v1.1.2** (`governance/prd/prd-v1.1.2-PATCH.md`) — Sprint 03 on-premise CDC Veicular único (superseded)

### Decisões Eric

- **Phase 1.7 elicitation** (2026-05-07): SaaS B2B BYOK confirmado
- **Phase 1.7.1 elicitation** (2026-05-07): A1 Anthropic only / B Atlas judgment Hybrid / C3 volume aspiracional / D-c per-approval
- **Phase 2.3 ratificação implícita** (2026-05-07): "execute o recomendado" = aprovação Phase 2.1 + DPA paralelo

### Smith adversarial review

- **Smith CC.41 F-A1** — motivação RAM constraint que justifica cloud pivot
- **Smith Phase 5** (Sprint 04) — adversarial review de PRD v2.0.0 + ADRs 014-018 + Sati UX OrSheva (TBD após Sati Phase 4)

---

## 12. Pendências cross-domain (Trinity flagga, não decide)

| Pendência | Owner | Quando |
|---|---|---|
| Valores absolutos R$ pricing tier (FR-BILLING-04) | @mifune (Mifune business) cross-domain OR Eric direto | Antes de SP04-BILLING-01 implementação |
| Conteúdo legal templates D3 (FR-D3-02) | Eric advogado | Antes de SP04-DOCTYPE-{FIES/VEICULAR/BANCARIO/IMOBILIARIO}-01 |
| Texto DPA + TOS operador (FR-LGPD-01..02) | Eric advogado paralelo Phase 3 | Antes de SP04-LGPD-01 release |
| UX redesign aplicar OrSheva brandbook | @ux-design-expert Sati Phase 4 | Após Phase 3 |
| Adversarial review pivot completo | @qa Smith Phase 5 | Após Phase 4 |

---

— Morgan, planejando o futuro 📊
