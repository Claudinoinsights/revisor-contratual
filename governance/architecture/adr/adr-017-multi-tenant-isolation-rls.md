---
type: adr
id: "ADR-017"
title: "Multi-Tenant Isolation PostgreSQL Pool+RLS + LGPD Operador"
status: proposed
date: "2026-05-07"
domain: data
adr_level: design
decision_makers:
  - "@architect (Aria) — design"
  - "@analyst (Atlas) — research v2 Section 2 + Section 4"
  - "Eric Claudino — autorização SaaS B2B BYOK"
supersedes:
  - "ADR-007"
  - "ADR-009"
superseded_by: ""
related_to:
  - "ADR-005 (audit chain HMAC — preservado, adapta tenant_id)"
  - "ADR-014 (tenant_api_keys com encryption + RLS)"
  - "ADR-015 (ocr_cache com RLS)"
  - "ADR-018 (billing_events com RLS)"
project: revisor-contratual
sprint: "04"
phase: "2.1"
tags:
  - project/revisor-contratual
  - adr
  - sprint-04
  - multi-tenant
  - postgresql
  - rls
  - lgpd
  - backbone
---

# ADR-017: Multi-Tenant Isolation + LGPD Operador (BACKBONE)

## Contexto

Sprint 04 transforma Revisor Contratual de single-tenant local (SQLite + ADR-007) em **SaaS B2B multi-tenant** para escritórios de advocacia. Atlas v2 Section 2 mapeou 3 patterns clássicos (Silo/Bridge/Pool); Pool+RLS recomendado para MVP com promotion path Silo enterprise.

**LGPD reframing crítico**: Eric vira **operador** (provê ferramenta SaaS), escritório é **controlador** (decide finalidade dos dados). ADR-009 (LGPD on-premise + pseudonimização) torna-se obsoleto — PII passa direto via API key escritório → Anthropic, com retention zero pós-resposta. Eric não retém PII; só retém logs operacionais 12 meses.

Esta ADR é **BACKBONE** porque:
- Define schema PostgreSQL base que ADRs 014/015/016/018 estendem
- Define RLS pattern aplicado universalmente
- Define LGPD operador posture que governa todas decisões compliance

## Decisão

**PostgreSQL 16 Pool + Row-Level Security + 3 camadas (RLS + encryption at rest pgcrypto + TLS 1.3) + LGPD operador posture.**

Componentes:

### 1. Migração SQLite → PostgreSQL 16

Greenfield (sem usuários produção Sprint 03), portanto sem migration tool. Sprint 04 começa do zero em PostgreSQL.

### 2. Schema multi-tenant

```sql
-- Cada tabela tem tenant_id NOT NULL
CREATE TABLE tenants (
  tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(200) NOT NULL,
  cnpj VARCHAR(18) UNIQUE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
  email VARCHAR(200) UNIQUE,
  role VARCHAR(20),
  ...
);

-- Idem para: analyses, contracts, billing_events, tenant_api_keys, ocr_cache,
-- usage_audit, billing_plans, tenant_subscription
```

### 3. RLS Policies

```sql
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON analyses
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
-- Replicado em todas tabelas
```

### 4. Session context middleware

FastAPI middleware ao autenticar request:
```python
async def set_tenant_context(request: Request, call_next):
    tenant_id = extract_tenant_from_jwt(request)
    async with db.transaction():
        await db.execute(f"SET LOCAL app.tenant_id = '{tenant_id}'")
        return await call_next(request)
```

### 5. Vault jurisprudência SHARED

Schema separado para dados públicos:
```sql
CREATE TABLE jurisprudencia_shared (
  id UUID PRIMARY KEY,
  doctype_tag VARCHAR(20),  -- veicular | fies | bancario | imobiliario | cross
  embedding VECTOR(1536),    -- pgvector extension
  content TEXT,
  source_court VARCHAR(50),
  ...
);
-- SEM tenant_id, SEM RLS — leitura aberta
```

Optional para futuro enterprise:
```sql
CREATE TABLE jurisprudencia_private (
  tenant_id UUID NOT NULL,
  ...  -- mesmas colunas + RLS
);
```

### 6. Audit chain HMAC PRESERVADO

`bloco_audit/genesis.py + chain.py` continuam — apenas adaptam payload `tenant_id`:
```python
audit_entry = {
    "tenant_id": ctx.tenant_id,
    "user_id": ctx.user_id,
    "action": "analysis.approved",
    "timestamp": now(),
    "data": {...},
}
hmac_chain.append(audit_entry)
```

### 7. Tenant isolation auditing

Endpoint `GET /api/tenant/audit/isolation` retorna metadata para escritório auditar:
```json
{
  "tenant_id": "...",
  "rls_policies_active": ["analyses", "contracts", "billing_events", ...],
  "row_counts_my_tenant": {"analyses": 142, "users": 5, ...},
  "encryption_at_rest_enabled": true,
  "tls_version": "1.3"
}
```

### 8. LGPD Operador posture (Eric responsabilidade)

- **DPA Eric-escritório obrigatório** (Atlas v2 Section 4 — 9 pontos estruturais; Eric advogado redige texto)
- **Subprocessor único declarado**: Anthropic API (via key escritório)
- **Retention logs operacionais**: 12 meses
- **Retention PII contratos**: ZERO pós-resposta API (passa direto, não armazena)
- **Notification incidente**: 24-72h via email DPO escritório
- **TOS / EULA SaaS**: declara papel operador explicitamente

### 9. Promotion path Silo enterprise

Schema separado `tenant_{uuid}` para clientes premium quando volume justifica (TBD threshold). Migration tool não desenhada aqui — debt CC.43+ quando primeiro enterprise client surgir.

## Razão

- **Pool+RLS vs Silo**: Atlas v2 Section 2 — Silo escala limitado (~100 tenants), backup/restore pesado, custo alto. Pool+RLS battle-tested em SaaS jurídico AWS, overhead 1-5% queries simples, escala milhares de tenants
- **PostgreSQL 16 vs MySQL/MariaDB**: pgvector extension nativo (ADR-007 superseded), pgcrypto built-in (ADR-014), JSONB suporte robusto, RLS battle-tested
- **3 camadas defense-in-depth**: bug em RLS = encryption at rest protege; bug em encryption = TLS protege; bug em TLS = ainda RLS lógica. Atlas v2 Section 2 — 2026 best practice
- **SHARED jurisprudência**: dado público, curadoria centralizada beneficia todos. Atlas v2 D-ATLAS-SP04-P1.8-C
- **Audit HMAC preservado**: já implementado Sprint 03, battle-tested em CC.39 (try/except hardening). Adaptar tenant_id é refactor menor

## Alternativas Consideradas

### Silo (database-per-tenant)

**Rejeitada para MVP.** Atlas v2 Section 2 — escala ~100 tenants ceiling, backup/restore pesado, custo operacional alto. Promotion path mantido para enterprise tier futuro.

### Bridge (schema-per-tenant)

**Rejeitada.** Middle ground sem ganho claro vs Pool+RLS. Cada novo tenant requer DDL (CREATE SCHEMA) — operação privilegiada toda vez.

### Manter SQLite com tenant_id discriminator

**Rejeitada.** SQLite não tem RLS nativo (precisaria RLS em código aplicação = error-prone). Multi-writer concurrency limitada. Escala fraca.

### Vault jurisprudência per-tenant

**Rejeitada.** Atlas v2 Section 2 — waste storage + maintenance hell para dado público. Override path mantido (`jurisprudencia_private`) para enterprise customizada.

### Pseudonimização local (preservar ADR-009)

**Rejeitada.** Eric vira operador LGPD; escritório é controlador. Pseudonimização cabe ao controlador (escritório) com seu cliente final, não ao operador. Path A Eric autorizou cloud agressivo — pseudonimização inline contradiz.

## Consequências

### Positivas
- Compliance LGPD posture máxima Path A (Atlas v2 Section 4)
- Escala milhares de tenants sem refactor estrutural
- 3 camadas defense-in-depth = surface auditável robusta
- Promotion path Silo enterprise mantém otionality
- Audit chain HMAC continua dando integridade temporal

### Negativas
- Migração SQLite → PostgreSQL exige refactor `bloco_vault` significativo (ADR-007 código superseded)
- RLS overhead 1-5% queries simples (mensurável mas aceitável)
- Eric responsabilidade DPA + TOS legal (advogado, mas time investment)
- Master key encryption (ADR-014) precisa proteção filesystem rigorosa

### Neutras
- pgvector vs sqlite-vec: API similar, migration cost = único
- Silo migration tool é debt explícito CC.43+ — não bloqueia MVP
- Vault SHARED + private split adiciona complexity menor

## Cross-references

- **Atlas v2 Section 2** (Multi-tenant Pool+RLS) — base research
- **Atlas v2 Section 4** (LGPD operador) — compliance posture
- **Smith CC.41** — motivação cloud que justifica pivot multi-tenant
- **ADR-007 (superseded)** — Schema sqlite-vec → PostgreSQL pgvector
- **ADR-009 (superseded)** — LGPD on-premise → LGPD operador SaaS
- **ADR-005 (preserved)** — audit chain HMAC adapta tenant_id no payload
- **ADR-014 (related)** — `tenant_api_keys` com pgcrypto encryption + RLS
- **ADR-015 (related)** — `ocr_cache` com tenant_id + RLS
- **ADR-018 (related)** — `billing_events` com tenant_id + RLS
