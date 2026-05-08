---
type: adr
id: "ADR-018"
title: "SaaS Pricing Hybrid + Billing Event State Machine"
status: proposed
date: "2026-05-07"
domain: business
adr_level: design
decision_makers:
  - "@architect (Aria) — design estrutura"
  - "@analyst (Atlas) — research v2 Section 3"
  - "Eric Claudino — autorização D-c per-approval billing"
  - "@mifune (cross-domain) — valores absolutos pendente"
supersedes: ""
superseded_by: ""
related_to:
  - "ADR-014 (BYOK key — escritório paga API direto)"
  - "ADR-017 (billing_events RLS multi-tenant)"
project: revisor-contratual
sprint: "04"
phase: "2.1"
tags:
  - project/revisor-contratual
  - adr
  - sprint-04
  - pricing
  - billing
  - stripe
  - per-approval
  - cross-domain-business
---

# ADR-018: SaaS Pricing Hybrid + Billing Event State Machine

## Contexto

BYOK arquitetura (ADR-014) significa que escritório paga API Anthropic direto — Eric não captura value via tokens. Sua receita SaaS vem de outra fonte. Eric escolheu D-c na elicitation Phase 1.7.1: **billing per-approval** (advogado clica "Aprovar" no UI após revisar relatório).

Atlas v2 Section 3 mapeou per-approval puro como modelo incomum (~17% enterprise SaaS implementaram até 2022) com riscos de receita imprevisível. Recomendou **Hybrid** (base mensal + per-approval) como mitigação — também dominante 2026 enterprise AI.

Esta ADR define **estrutura técnica** do billing system. **Valores absolutos** (R$ X base, R$ Y per-approval, quotas) são DECISÃO Eric+Mifune (cross-domain business), não arquitetural.

## Decisão

**Hybrid pricing**: assinatura base mensal (cobre infrastructure SaaS) + per-approval fee (success-based, alinha incentivos qualidade).

**State machine de billing event** triggera fatura quando advogado aprova análise. Stripe MVP (Asaas BR-native como alternativa pós-MVP).

Componentes:

### 1. State machine `analysis.status`

```
created
   ↓
ocr_processing  ← ADR-015 vision OCR roda aqui
   ↓
personas_running  ← 4 personas paralelas (ADR-016)
   ↓
judge_consolidating  ← Juiz Sonnet revisor (ADR-014 stack B)
   ↓
pending_review  ← Advogado revisa relatório no UI
   ↓
   ├─→ approved  ← BILLING EVENT ⚡
   ├─→ rejected  ← Não fatura, registra rejection_reason
   └─→ expired   ← Após 30 dias pending = auto-rejected (não fatura)

# Reabertura possível: rejected → pending_review (advogado pode reabrir)
```

### 2. Tabela `billing_events`

```sql
CREATE TABLE billing_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
  analysis_id UUID NOT NULL REFERENCES analyses(id),
  user_id UUID NOT NULL REFERENCES users(user_id),
  approved_at TIMESTAMP NOT NULL DEFAULT NOW(),
  stripe_invoice_line_id VARCHAR(100),
  amount_brl DECIMAL(10,2) NOT NULL,  -- valor congelado no momento approval
  webhook_status VARCHAR(20) DEFAULT 'pending'  -- pending | sent | failed
);

ALTER TABLE billing_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON billing_events
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

### 3. Stripe webhook async

- Quando `pending_review → approved`: insert em `billing_events` + dispatch Celery/asyncio task para Stripe API
- Stripe `invoice_items.create()` com customer_id (escritório), amount, description (analysis_id)
- Mensal Stripe agrega + emite fatura recorrente (configurada via Stripe dashboard pelo Eric)
- Webhook NÃO bloqueia UI — usuário vê success imediato; Stripe é eventual consistency

### 4. Tier enforcement

```sql
CREATE TABLE tenant_subscription (
  tenant_id UUID PRIMARY KEY REFERENCES tenants(tenant_id),
  tier_name VARCHAR(50) NOT NULL,  -- 'starter' | 'pro' | 'enterprise'
  monthly_quota_approvals INT NOT NULL,
  monthly_used INT DEFAULT 0,
  reset_date DATE NOT NULL,
  base_fee_brl DECIMAL(10,2),
  per_approval_fee_brl DECIMAL(10,2),
  approvals_included INT DEFAULT 0,
  ...
);
```

Quando `monthly_used >= monthly_quota_approvals + approvals_included` → status análise nova vira `quota_exceeded` com mensagem PT-BR ao usuário ("Cota mensal atingida — entre em contato administrativo do escritório").

### 5. Cross-domain Mifune flag

**Aria define ESTRUTURA tabelas** acima. **Mifune (business domain) define VALORES**:
- `base_fee_brl` — quanto cobrar base mensal por tier
- `per_approval_fee_brl` — quanto cobrar por aprovação
- `approvals_included` — quantas inclusas no base
- `monthly_quota_approvals` — teto antes de bloquear

Atlas v2 Section 3 sugeriu tier estrutura como ponto de partida (Starter/Pro/Enterprise), mas valores absolutos requerem benchmark Mifune cross-domain.

### 6. Pré-pago alternativo (POST-MVP)

```sql
CREATE TABLE tenant_credits (
  tenant_id UUID PRIMARY KEY,
  credits_remaining DECIMAL(10,2),
  last_topup_at TIMESTAMP
);
```

Cada approval decrementa `credits_remaining`; bloqueia novas análises quando = 0. Estrutura desenhada mas marcada **POST-MVP** — adoção depende de feedback escritórios.

### 7. Rejection flow

- `pending_review → rejected` NÃO emite billing event
- Audit trail registra `rejection_reason` (advogado preenche em modal obrigatório)
- Rejection reasons enum: `pii_incorrect | analysis_inadequate | doctype_wrong | other` + free text
- Advogado pode reabrir: `rejected → pending_review` (não cobra denovo)

## Razão

- **Hybrid vs per-approval puro**: Atlas v2 Section 3 — outcome puro implementado por ~17% enterprise (rejection rate desconhecida + churn baixo volume = receita zero). Hybrid mitiga: base cobre infrastructure, per-approval captura value entregue
- **Stripe MVP vs Asaas**: Stripe DX superior + docs pt-BR melhores; Asaas BR-native para boletos/PIX direto pode ser melhor a longo prazo. Decisão final pós-validação MVP
- **Approval click vs auto-aprovação após N dias**: success-based pricing exige human-in-the-loop explícito (Eric escolheu D-c). Auto-approval rompe alinhamento incentivos
- **Webhook async vs sync**: UI não pode esperar Stripe API (latência variable + falhas Stripe não devem cortar UX)
- **Aria não precifica absoluto**: pricing benchmark BR jurídico (Astrea R$ 50-200/advogado, ADVBOX) requer Mifune cross-domain — Aria define estrutura tabelas, valores ficam configuráveis

## Alternativas Consideradas

### Per-approval puro sem base mensal

**Rejeitada.** Atlas v2 Section 3 — receita imprevisível, churn baixo volume = zero receita. Hybrid mitiga sem sacrificar alinhamento.

### Subscription apenas (sem per-approval)

**Rejeitada.** Quebra promessa Eric "ganho por documentação aprovada". Não alinha incentivo qualidade.

### Markup escondido em API tokens (não-BYOK)

**Rejeitada.** Quebra BYOK pattern (ADR-014). Eric escolheu A1 BYOK + D-c per-approval — mark-up token contradiz.

### Asaas como billing engine MVP

**Rejeitada (para MVP).** Stripe maior maturidade docs + community para questões técnicas; Asaas reserva-se para pós-MVP quando boleto/PIX direto for prioridade.

### Auto-aprovação após 7 dias pending

**Rejeitada.** Quebra success-based — escritórios poderiam ignorar review e ainda receber bill. Manter human-in-the-loop até timeout maior (30 dias = expired sem cobrança).

## Consequências

### Positivas
- Receita previsível (base) + alinhada qualidade (per-approval)
- BYOK + per-approval = LGPD posture mínima (ADR-017)
- State machine clara facilita debug + audit
- Tier enforcement protege contra abuso (quota exceeded)
- Cross-domain Mifune flag explícito = sem invenção valores

### Negativas
- Stripe vendor dependency (debt: explorar Asaas pós-MVP)
- Rejection flow cria fricção UX (modal reason obrigatório)
- Webhook async: Stripe failures requerem retry/recovery (não trivial)
- Eric+Mifune precisam definir números absolutos antes de Aria lançar — bloqueio sequencial

### Neutras
- Pré-pago credits POST-MVP — opcionalidade preservada
- 30-day expiration: trade-off entre não pressionar advogado e não acumular pendings infinitos
- `webhook_status` field permite retry manual via admin tool (debt CC.50+)

## Cross-references

- **Atlas v2 Section 3** (Pricing benchmark SaaS jurídico Brasil + per-approval) — base research
- **ADR-014 (related)** — BYOK key, escritório paga API direto
- **ADR-017 (related)** — `billing_events` table multi-tenant com RLS
- **Mifune (cross-domain pendente)** — valores absolutos R$ pricing
- **Trinity Phase 3 PRD** — definirá UX do approval flow + tier descriptions
- **Eric Claudino autorização D-c** — Phase 1.7.1 elicitation per-approval billing
