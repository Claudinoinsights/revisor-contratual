---
type: research
title: "BYOK SaaS Multi-Tenant + Per-Approval Pricing — Sprint 04 Phase 1.8 Supplement"
project: revisor-contratual
sprint: 04
phase: 1.8
author: "@analyst (Atlas)"
date: "2026-05-07"
supersedes_partial: "openrouter-vision-ocr-viability.md (premissa Eric=paga-API)"
preserves: "openrouter-vision-ocr-viability.md (OCR landscape, model benchmarks, LGPD framework genérico)"
tags:
  - project/revisor-contratual
  - research
  - sprint-04
  - byok
  - multi-tenant
  - per-approval-pricing
  - saas-juridico
---

# BYOK SaaS Multi-Tenant + Per-Approval Pricing

> **Contexto:** Eric confirmou (Sprint 04 Phase 1.7-1.7.1) que Revisor Contratual é SaaS B2B para escritórios de advocacia, BYOK (cada escritório paga sua própria API key Anthropic), Eric=operador LGPD, billing per-approval (advogado clica "Aprovar" no UI). Stack: Anthropic Hybrid (Sonnet 4.6 OCR+Juiz, Haiku 4.5 4 personas) — R$ 4,18/análise pago direto pelo escritório.
>
> **Este supplement complementa** `openrouter-vision-ocr-viability.md` v1 (preserva OCR landscape, benchmarks, framework LGPD geral). Reframa a partes que assumiam Eric pagando a API.

---

## Seção 1 — BYOK API Key Security & Storage

### Princípios OWASP (não-negociável)

[OWASP Multi-Tenant Security](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html) define 3 invariantes para BYOK em SaaS:

1. **Per-tenant key isolation** — escritório A nunca decifra dado de escritório B (hardware-level se possível, software-level mínimo)
2. **Sharing API keys across tenants é proibido** — se a sua app usa "default key Anthropic do Eric" como fallback, isso é vazamento arquitetural
3. **Manage secrets via vault** — nunca em env-vars compartilhadas ou logs

### Pontos no código onde key passa (auditoria mandatória Aria)

A key Anthropic do escritório transita por:
- Form de cadastro (input)
- API endpoint `POST /tenant/api-key` (validação)
- Storage de persistência (encryption at rest)
- Cada request à pipeline (inject runtime)
- Cada exception handler (NUNCA logar mesmo em erro)
- Cada audit trail entry (substituir por hash truncado: `sk-...XYZ`)

**Aria deve garantir** que cada um desses pontos tem teste explícito provando que key não vaza em logs/console/audit.

### Storage options ranking (MVP → produção)

| Solução | MVP-fit | Produção-fit | Custo | Notas |
|---|---|---|---|---|
| **PostgreSQL + pgcrypto** | ✅ Excelente | ⚠️ Adequado | Zero | Encryption at rest via `pgp_sym_encrypt()` com key master Eric. Simples mas key master também precisa proteção |
| **HashiCorp Vault** | ❌ Overkill | ✅ Ideal | $$$  | Self-hosted complexity grande para MVP solo dev |
| **AWS Secrets Manager** | ⚠️ Vendor lock | ✅ Ideal | $0,40/secret/mês × N tenants | Cloud-native; integra com KMS para BYOK customer-key |
| **Azure Key Vault** | ⚠️ Vendor lock | ✅ Ideal | Similar AWS | Igual AWS, escolher pelo cloud já usado |
| **Encrypted env per tenant** | ❌ Não escala | ❌ Anti-pattern | Zero | Pre-MVP only, cada novo tenant requer redeploy |

### Recomendação Atlas

**MVP (1-50 escritórios):** PostgreSQL + pgcrypto + key master via env var (`MASTER_ENCRYPTION_KEY`) protegido por filesystem permissions. Simples, zero custo, escalável para dezenas de tenants.

**Produção (50+ escritórios ou enterprise tier):** migration para AWS Secrets Manager + KMS, com path explícito para "customer-managed key" (escritório enterprise pode fornecer SUA própria KMS key, atingindo BYOK true).

### Multi-user dentro do escritório (decisão de design)

3 patterns possíveis (Aria decide ADR-014):

- **Pattern Single Key:** uma key Anthropic por escritório. Todos advogados compartilham. Simples mas billing Anthropic não distingue qual advogado consumiu mais.
- **Pattern Sub-Key:** cada advogado cadastra sub-key própria. Anthropic não tem nativo, mas escritório pode criar projects separados no Anthropic Console. Mais granular mas mais setup.
- **Pattern Quota Interna:** uma key escritório + Revisor rastreia consumo per-advogado em audit log. Bill Anthropic agrega; relatório interno separa. **Recomendação Atlas para MVP.**

### Validação ao cadastrar

Quando escritório submete key:
```
POST /tenant/api-key { key: "sk-ant-..." }
  → Atlas backend pings: GET https://api.anthropic.com/v1/models (Authorization: Bearer key)
  → Se 200 OK → encrypt + store
  → Se 401/403 → reject "Key inválida"
  → Se outros erros → retry 3× com backoff, depois reject "Provider unavailable"
```

### Rotação sem downtime

Padrão: dual-key window. Escritório cadastra key NOVA; sistema mantém key VELHA por 24h; após confirmação, key velha apagada. Aria desenha state machine.

### Compromised key handling

- Self-service revoke (escritório clica "Revogar key" no Settings)
- Suspend tenant até key nova cadastrada
- Audit log evento de revogação com timestamp + user_id
- Notificar todos advogados do tenant via email

**Sources:**
- [OWASP Multi-Tenant Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [AWS BYOK + KMS](https://aws.amazon.com/blogs/security/demystifying-kms-keys-operations-bring-your-own-key-byok-custom-key-store-and-ciphertext-portability/)
- [IBM What is BYOK](https://www.ibm.com/think/topics/byok)
- [PostgreSQL pgcrypto docs](https://www.postgresql.org/docs/current/pgcrypto.html)

---

## Seção 2 — Multi-Tenant Architecture Patterns

### 3 Patterns Clássicos

| Pattern | Isolamento | Custo Op | Escala | Compliance LGPD |
|---|---|---|---|---|
| **Silo** (DB-per-tenant) | Total | Alto | Limitada (~100 tenants) | Máxima — backup/restore por tenant trivial |
| **Bridge** (schema-per-tenant) | Alto | Médio | ~500 tenants | Alta — schemas isolados PostgreSQL |
| **Pool** (shared schema + RLS) | Médio (lógico) | Baixo | Milhares | OK — RLS PostgreSQL é battle-tested |

### Recomendação Atlas para SaaS jurídico

**MVP: Pool com PostgreSQL Row-Level Security (RLS).**

**Por quê:**
- RLS é battle-tested em SaaS jurídico ([AWS RLS multi-tenant](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/))
- Overhead 1-5% para queries simples — desprezível
- Cada row tem `tenant_id`; policy força filter automaticamente — mesmo com bug na app, dados não vazam
- Backup/restore por tenant via `pg_dump --where`
- Promoção para Silo possível depois para enterprise tier sem rewrite massivo

**3 camadas de segurança obrigatórias** ([2026 best practice](https://hiveforge.dev/guides/multi-tenant-saas)):
1. RLS — cada row taggeada com `tenant_id`, policy garantida
2. Encryption at rest — disco PostgreSQL + storage backups + logs
3. Encryption in transit — TLS 1.3 everywhere

### Vault jurisprudência: SHARED ou per-tenant?

**Recomendação Atlas: SHARED entre tenants.**

**Por quê:**
- Jurisprudência STJ/TJ é dado público (não há PII)
- Curadoria centralizada Eric beneficia TODOS escritórios
- Redundância per-tenant = waste storage + maintenance hell
- Custo: ~3MB hoje, escalará para ~50MB em produção (10k jurisprudências). Trivial.

Único contraindicador: se escritório enterprise quer **adicionar SUA própria jurisprudência customizada** (precedentes internos, vitorias específicas). Aria pode prever extensão "tenant-private vault" como override da SHARED.

### Tenant isolation auditing (prova para escritório)

Eric deve oferecer mecanismo para escritório auditar isolamento:
- Endpoint `GET /tenant/audit/isolation` que retorna metadata sem dados (counts, last_activity, RLS policies ativas)
- Penetration test report anual (Smith adversarial review pode simular)
- SOC 2 Type II eventualmente (enterprise tier)

**Sources:**
- [AWS PostgreSQL RLS Multi-Tenant](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/)
- [Multi-tenancy with PostgreSQL — Logto](https://blog.logto.io/implement-multi-tenancy)
- [Building Multi-Tenant SaaS 2026 — HiveForge](https://hiveforge.dev/guides/multi-tenant-saas)
- [Shipping multi-tenant SaaS using Postgres RLS — Nile](https://www.thenile.dev/blog/multi-tenant-rls)

---

## Seção 3 — Per-Approval Pricing Benchmark

### Mercado SaaS Jurídico Brasil (baseline)

[Comparáveis BR 2026](https://www.aurum.com.br/astrea/planos-e-precos/):

| Software | Modelo | Tier inicial | Tier médio | Notas |
|---|---|---|---|---|
| **Astrea (Aurum)** | Assinatura mensal | R$ 50-200/advogado | R$ 200-600 | Most popular small/medium firms |
| **ADVBOX** | Assinatura tier | "Multiplos planos" | n/a (não-público) | AI integration em todos planos |
| **CPJ-3C** | Assinatura mensal | n/a | R$ 200-500 | Médias firmas |
| **Projuris** | Tier por features | n/a | R$ 300-800 | Médias-grandes firmas |
| **Easyjur** | Assinatura simples | R$ 50-150 | n/a | Solo/iniciantes |
| **Themis (Aurum)** | IA jurídica | Premium | Não-público | Foco AI |

**Range geral:** **R$ 50 a R$ 1500+/mês** dependendo tier e número de advogados. Modelos predominantes: assinatura fixa OR per-usuário ativo.

### Per-Approval / Outcome-Based em SaaS Geral

**Reality check ([Monetizely 2026 guide](https://www.getmonetizely.com/blogs/the-2026-guide-to-saas-ai-and-agentic-pricing-models)):**
- Apenas **~17% dos enterprise SaaS** implementaram outcome-based até 2022
- Crescendo em AI agentic (chatbots resolvem ticket → cobra por resolução)
- Difícil de medir outcomes consistentemente
- Requer **baseline studies + legal safeguards** (Eric tem skill jurídica para isso)
- **Hybrid (base subscription + per-outcome)** é dominante 2026 enterprise

### Custo ESCRITÓRIO end-to-end

Por análise (estimativa baseline Veicular 12 págs):

| Componente | Custo escritório |
|---|---|
| Anthropic API (Hybrid stack) | **R$ 4,18** |
| Eric per-approval fee (TBD) | **R$ X** |
| Total | R$ 4,18 + X |

**Comparação modo tradicional (sem IA):**
- Advogado revisa contrato CDC PF manualmente: 2-4h × R$ 200-300/h = **R$ 400 a R$ 1.200/análise**
- Eric SaaS deve ficar 5-15× mais barato para gerar ROI claro

### Sweet spot Eric per-approval

**Range Atlas recomenda:** **R$ 30 a R$ 80 por aprovação.**

**Lógica:**
- R$ 30: 5% do custo manual → ROI muito claro, mas pode ser percebido como "barato demais" (concorrência free tier OR DIY rebate)
- R$ 50: ~10% do custo manual → sweet spot (ROI claro + receita decente Eric)
- R$ 80: 15% custo manual → ainda barato vs manual, gera receita ~R$ 80k/mês com 1000 aprovações

**Comparação com baseline mercado BR:**
- Astrea: R$ 200/advogado/mês → escritório com 5 advogados paga R$ 1000/mês fixo
- Eric per-approval R$ 50: escritório com 100 análises/mês paga R$ 5000/mês — só faz sentido se SUBSTITUI o trabalho manual (ROI vs R$ 40-120k manual)

**Insight crítico:** Per-approval só compete contra **manual labor**, não contra Astrea/ADVBOX (que NÃO substituem análise jurídica — só gestão de processos). Posicionamento Eric: **"automatiza o que Astrea não automatiza"**.

### Hybrid recomendado (mitigation risco Eric)

**Base mensal R$ 200-500/escritório + per-approval R$ 30-50.**

Razão: outcome-based puro carrega risco (rejection rate desconhecida + churn baixo volume = receita zero). Base mensal cobre infrastructure (multi-tenant, encryption, support). Per-approval captura value real entregue.

| Tier | Base mensal | Per-approval | Análises/mês incluso |
|---|---|---|---|
| Starter | R$ 200 | R$ 50 | 5 (depois pay-as-you-go) |
| Pro | R$ 500 | R$ 30 | 30 inclusas |
| Enterprise | Negociado | Negociado | Custom |

### Billing engine

[BR-friendly options 2026](https://flexprice.io/blog/best-enterprise-billing-software-for-ai-and-saas):

- **Stripe** — mais maduro, suporta usage-based, BR via Stripe Brasil
- **Iugu** — BR-native, boa integração PIX/boleto
- **Asaas** — BR-native, foco PME/jurídico (alguns escritórios já usam para receber clientes)
- **Pagar.me** — BR, robusto

**Recomendação Atlas:** Stripe para MVP (developer experience superior + docs pt-BR), Asaas se Eric quer "ferramenta brasileira" como diferencial.

### Implementação técnica billing event

```
Advogado clica "Aprovar" no UI
  → POST /api/analysis/{id}/approve
  → Insert row em billing_events { tenant_id, analysis_id, timestamp, user_id }
  → Webhook async para Stripe (cria invoice line item)
  → Mensal: Stripe agrega + emite fatura escritório
  → Charge automático cartão / PIX boleto vencimento
```

Aria desenha ADR-018 com state machine: `pending_review → approved (billing event) → completed | rejected (no billing)`.

### Rejection rate típica IA jurídica

**Unknown explícito:** dados de rejection rate em IA jurídica BR ainda escassos publicamente. Eric deve **assumir conservador 15-25% rejection** no primeiro ano e ajustar com dados reais. Se rate alto (>30%) → produto precisa quality improvement; se baixo (<10%) → bem alinhado.

**Sources:**
- [Monetizely 2026 SaaS AI Pricing Guide](https://www.getmonetizely.com/blogs/the-2026-guide-to-saas-ai-and-agentic-pricing-models)
- [PYMNTS AI Pricing Disrupting SaaS](https://www.pymnts.com/artificial-intelligence-2/2026/cfos-scramble-as-ai-pricing-breaks-traditional-saas-billing-model/)
- [Astrea Planos e Preços](https://www.aurum.com.br/astrea/planos-e-precos/)
- [ADVBOX Planos](https://advbox.com.br/planos)
- [Capterra Astrea](https://www.capterra.com/p/217058/Astrea/)
- [SaaS Billing Models Guide 2026](https://fungies.io/saas-billing-models-guide-2026/)
- [Harvey AI Legal](https://www.harvey.ai/)

---

## Seção 4 — LGPD Operador vs Controlador (reframe)

### Diferença Art. 5º LGPD ([fundamental](https://prodest.es.gov.br/saiba-quem-sao-os-agentes-previstos-na-lgpd))

| Papel | LGPD Art. 5º | Decide | Eric? Escritório? |
|---|---|---|---|
| **Controlador** | Inciso VI | Finalidade + meios do tratamento | **Escritório** (decide analisar contrato CDC do cliente) |
| **Operador** | Inciso VII | Executa tratamento em nome do controlador | **Eric** (provê ferramenta SaaS) |
| Encarregado (DPO) | Inciso VIII | Ponto de contato com ANPD | Eventualmente Eric (depende escala) |

**Primacy of reality** ([Jusbrasil](https://www.jusbrasil.com.br/doutrina/secao/30-compartilhamento-de-dados-pessoais-e-a-figura-do-controlador-compliance-e-politicas-de-protecao-de-dados/1506551419)): cláusula contratual chamando alguém de "operador" não basta — a EXECUÇÃO concreta é que define. Se Eric começar a decidir finalidade dos dados (ex: usar dados para treinar modelo próprio), vira controlador automaticamente, mesmo com contrato dizendo o contrário.

### Eric responsabilidades como operador

1. **DPA (Data Processing Agreement)** com cada escritório — não obrigatório por lei BR, mas prática de mercado e Eric **DEVE** ter (Astrea/Aurum já oferecem)
2. **TOS / EULA do SaaS** declarando explicitamente papel operador
3. **Documentar isolamento técnico multi-tenant** — provar que escritório A não vê dado B (relatório técnico anexo ao DPA)
4. **Política de retenção de logs operacionais** — distinguir logs (Eric pode reter) de PII (não retém pós-resposta da API)
5. **Notificar ANPD** em incidente de segurança Art. 48 LGPD (prazo: razoável, sugerido 72h GDPR-style)
6. **Encarregado (DPO)** — para SaaS pequeno Eric pode acumular função; ao crescer, contratar dedicado

### Riscos Eric mesmo como operador

| Risco | Severidade | Mitigação |
|---|---|---|
| **Falha de isolamento multi-tenant** | CRITICAL | RLS PostgreSQL + auditoria periódica + Smith adversarial pen-test |
| **Vazamento API key escritório** | HIGH | Encryption at rest + nunca logar + rotation flow |
| **Audit trail incompleto** | HIGH | HMAC chain (já existe no projeto via bloco_audit) — preservar Sprint 04 |
| **Multa ANPD Art. 52** | até 2% faturamento R$ 50M cap | DPA + isolamento técnico + audit |
| **Outage durante análise (PII pendente)** | MEDIUM | Retry + idempotência + delete imediato após resposta |

### DPA template structure (Atlas lista — Eric advogado redige)

Pontos obrigatórios per [Mercado/Hyperflow modelo](https://hyperflow.global/acordo-de-processamento-de-dados-pessoais-entre-hyperflow-e-cliente/):

1. **Identificação das partes** — Eric (operador) + escritório (controlador) com CNPJ
2. **Finalidade do tratamento** — análise jurídica de contratos CDC PF para identificação de irregularidades
3. **Tipos de dados processados** — PII contrato (CPF, nome, endereço), valores financeiros, dados do agente financeiro
4. **Subprocessors autorizados** — Anthropic Inc. (via API key fornecida pelo controlador)
5. **Medidas técnicas e organizacionais** — encryption at rest, encryption in transit, RLS multi-tenant, audit chain HMAC, key encryption
6. **Notificação de incidentes** — prazo (recomendação: 24-72h), canal (email DPO escritório), template
7. **Retenção e eliminação** — logs operacionais 12 meses, PII contrato zero retention pós-resposta API, dados conta escritório até término contrato + 6 meses
8. **Direitos do controlador (escritório)** — auditoria do operador (Eric), portabilidade, eliminação
9. **Foro e legislação** — Brasil, LGPD aplicável

### Termo de consentimento (cliente final do escritório)

**NÃO é responsabilidade Eric.** Escritório (controlador) que firma com cliente final. Eric pode:
- Oferecer **template OPCIONAL** como diferencial competitivo ("seu cliente assina termo de uso de IA com 1 clique")
- NÃO se responsabilizar pelo conteúdo
- Documentar no DPA que escritório se responsabiliza por base legal Art. 7º com cliente final

### Surface LGPD reduzida (vantagem BYOK + operador)

Comparado ao cenário Eric=controlador discutido em research v1:

| Surface LGPD | Eric=Controlador (v1) | Eric=Operador BYOK (v2) |
|---|---|---|
| Eric processa PII cliente final | SIM | NÃO (passa direto via key escritório) |
| Eric responsável Art. 33 transferência | SIM | NÃO (escritório autoriza) |
| Termo consentimento Eric redige | SIM | NÃO (escritório responsabilidade) |
| DPA com cliente final | SIM | NÃO (escritório-cliente direto) |
| DPA Eric necessário | NÃO | **SIM** (escritório-Eric) |
| Multa potencial Art. 52 | Direta | Subsidiária (operador divide com controlador) |

**BYOK + operador é massivamente mais leve LGPD-wise.** Sprint 04 simplificado vs research v1.

**Sources:**
- [LGPD Lei 13.709/2018](http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- [ANPD orientações](https://www.gov.br/anpd/pt-br)
- [Operador ou Controlador LGPD — MacherTecnologia](https://www.machertecnologia.com.br/operador-ou-controlador-lgpd/)
- [Compartilhamento de Dados — Jusbrasil](https://www.jusbrasil.com.br/doutrina/secao/30-compartilhamento-de-dados-pessoais-e-a-figura-do-controlador-compliance-e-politicas-de-protecao-de-dados/1506551419)
- [DPA Template Modelo Hyperflow](https://hyperflow.global/acordo-de-processamento-de-dados-pessoais-entre-hyperflow-e-cliente/)
- [Cláusulas-Padrão Contratuais Brasileiras (Oracle)](https://www.oracle.com/contracts/docs/brazil-scc-portuguese-081825.pdf)

---

## Sumário executivo Atlas v2

✅ **BYOK security** → MVP: PostgreSQL pgcrypto + master key env. Produção: AWS Secrets Manager + KMS. Per-tenant isolation absoluta.

✅ **Multi-tenant pattern** → MVP: PostgreSQL Pool + RLS (3 camadas: RLS + encryption at rest + TLS). Promotion path para Silo enterprise. Vault jurisprudência SHARED.

✅ **Per-approval pricing** → Hybrid recomendado: base R$ 200-500/escritório + per-approval R$ 30-50. Sweet spot R$ 50 (10% custo manual = ROI 10×). Stripe ou Asaas para billing engine.

✅ **LGPD operador** → Surface massivamente reduzida vs controlador. DPA Eric-escritório obrigatório. 9 pontos estruturais; Eric (advogado) redige texto final. Termo consentimento cliente final = responsabilidade escritório.

⏭️ **Inputs para Aria Phase 2 (5 ADRs):**

- **ADR-014:** Provider abstraction (A1 Anthropic only) + BYOK key management (Pattern Quota Interna multi-user)
- **ADR-015:** Vision OCR architecture (preserva v1 — Sonnet 4.6 OCR + caching)
- **ADR-016:** Multi-doctype dispatcher (independente)
- **ADR-017:** Multi-tenant isolation (Pool + RLS + 3 camadas) + audit trail multi-tenant
- **ADR-018:** SaaS pricing & billing event (Hybrid base+per-approval, state machine pending_review→approved)

⚠️ **Pendências Eric continuam paralelas:**

- Redigir DPA template (Eric advogado)
- Definir números absolutos pricing (base R$ X + per-approval R$ Y) — Mifune cross-domain pode ajudar com benchmark mais profundo
- Decidir billing engine (Stripe vs Asaas vs outro)
- Definir tier structure final (Starter/Pro/Enterprise)

— Atlas, investigando a verdade 🔎
