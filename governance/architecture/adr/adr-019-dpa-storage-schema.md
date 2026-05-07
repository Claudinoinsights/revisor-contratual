---
type: adr
id: "ADR-019"
title: "DPA Storage Schema — Multi-Tenant Acceptance Tracking with Audit Evidence"
project: revisor-contratual
status: accepted
date: "2026-05-07"
domain: "legal-compliance"
decision_makers: ["@architect Aria", "@lmas-master Morpheus", "@pm Trinity"]
adr_level: spec
spec_coverage:
  - "Schema SQL completo dpa_acceptances com FKs e constraints"
  - "RLS policies multi-tenant"
  - "Retention policy permanent (legal evidence)"
  - "DPA versioning protocol semantic"
  - "Storage canônico texto DPA (filesystem versionado git)"
  - "Audit chain HMAC integration"
  - "API endpoints GET/POST /api/tenant/dpa"
supersedes: ""
superseded_by: ""
impacts: ["ADR-017", "FR-LGPD-01", "FR-NOTIFY"]
sprint: "04"
phase: "5.3"
tags:
  - project/revisor-contratual
  - adr
  - sprint-04
  - lgpd
  - dpa
  - multi-tenant
  - spec
---

# ADR-019 — DPA Storage Schema (Multi-Tenant Acceptance Tracking with Audit Evidence)

```
[@architect · Aria (Visionary)] — Sprint 04 · Phase 5.3 · ADR-019 · Smith F-012 CRITICAL
SPRINT: 04 · PHASE: 5.3 · DOMÍNIO: legal-compliance + data + multi-tenant
```

> **Smith F-012 driven (CRITICAL):** PRD FR-LGPD-01 conceitualizou DPA mas não detalhou storage/versioning/hash/timestamp/IP origin. Sem chassis técnico, ANPD audit Eric=operador é indefensável. ADR-019 desenha o esqueleto que sobrevive a uma multa Art. 52 LGPD (R$ 50M cap).

---

## 1. Contexto

**Smith Phase 5 ULTRATHINK adversarial review** (commit `4519ef1`) identificou F-012 como CRITICAL:

> "DPA acceptance storage/versioning não definido. ANPD audit Eric=operador → multa Art. 52 LGPD até R$ 50M sem evidence rastreável."

**Estado pré-ADR-019:**
- PRD v2.0.0 FR-LGPD-01: "DPA Eric-escritório obrigatório no onboarding" — afirmação sem chassis
- ADR-017 BACKBONE: posture operador LGPD definida, mas DPA acceptance específica não desenhada
- Trinity Phase 5.2 (PRD v2.0.1): formalizou conceito, deixou implementação para Aria

**Risco material concreto:**
- LGPD Art. 5º VIII define operador como "pessoa que realiza tratamento em nome do controlador"
- Art. 52 LGPD: multa até **2% faturamento** ou **R$ 50M cap por infração** se operador não comprovar base legal e consentimento documentado
- ANPD pode auditar retroativamente — sem schema explícito de DPA acceptance, Eric não consegue provar **quando/como/qual versão** foi aceita por escritório X

**Constraint multi-tenant:** Cada escritório (`tenant_id`) aceita sua própria versão de DPA. Sistema precisa suportar:
- Múltiplas versões DPA coexistindo (escritório A aceitou v1.0.0, escritório B aceitou v1.1.0)
- Re-aceite forçado em mudança material (MAJOR bump)
- Evidence rastreável por aceitação individual (não por tenant agregado)

---

## 2. Decisão (Schema Canônico SQL)

```sql
-- Tabela dedicated para evidence de aceitação DPA
CREATE TABLE dpa_acceptances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
  dpa_version VARCHAR(20) NOT NULL,                  -- semver: "1.0.0", "1.1.0", "2.0.0"
  dpa_text_hash VARCHAR(64) NOT NULL,                -- SHA-256 hex do texto canônico
  accepted_at TIMESTAMP WITH TIME ZONE NOT NULL,     -- UTC com timezone (ANPD audit-friendly)
  accepted_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  ip_address INET,                                    -- IPv4/IPv6 origin do aceite
  user_agent TEXT,                                    -- navegador/dispositivo origin
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  CONSTRAINT unique_tenant_version UNIQUE(tenant_id, dpa_version)
);

-- RLS multi-tenant (consistente ADR-017 BACKBONE pattern)
ALTER TABLE dpa_acceptances ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON dpa_acceptances
  USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- Indexes para queries comuns (lookup por tenant + versão)
CREATE INDEX idx_dpa_acceptances_tenant ON dpa_acceptances(tenant_id);
CREATE INDEX idx_dpa_acceptances_version ON dpa_acceptances(dpa_version);
```

---

## 3. Razão (por que cada elemento)

| Elemento | Justificativa |
|----------|--------------|
| **Schema dedicated table** | > coluna em `tenants` — escala, versioning, audit history nativos |
| **`dpa_version VARCHAR(20)` semver** | Permite query history + protocolo de versioning explícito (Seção 5) |
| **`dpa_text_hash VARCHAR(64)` SHA-256** | Prova imutabilidade da versão aceita — previne disputa "aceitei texto diferente" |
| **`INET` type para IP** | PostgreSQL nativo IPv4/IPv6 — type-safe sobre VARCHAR genérico |
| **`TIMESTAMP WITH TIME ZONE`** | ANPD pode pedir evidence em horário local BR — timezone preservado |
| **`UNIQUE(tenant_id, dpa_version)`** | Previne aceitação duplicada da mesma versão pelo mesmo tenant (idempotência) |
| **RLS `tenant_isolation`** | Multi-tenant isolation consistente ADR-017 BACKBONE — defense-in-depth |
| **`ON DELETE RESTRICT` em FKs** | Evidence preservada mesmo se user/tenant deletado (apenas archive permitido — ver Seção 6) |
| **`created_at` separado de `accepted_at`** | `accepted_at` = ato declarado pelo cliente; `created_at` = timestamp server-side imutável (defense contra clock skew client) |

---

## 4. Alternativas Consideradas

| # | Alternativa | Veredicto | Razão |
|---|-------------|-----------|-------|
| 1 | Coluna boolean em `tenants.dpa_accepted` | ❌ REJEITADA | Sem versioning, sem audit history, sem hash imutável, sem IP/timestamp evidence |
| 2 | PDF stored como BLOB em column | ❌ REJEITADA | Storage caro (~100KB+/PDF), search-unfriendly, hash texto canônico cobre imutabilidade sem custo |
| 3 | External audit service (DocuSign/Adobe Sign/ClickSign) | ❌ REJEITADA | Vendor lock-in + custo R$ 5-20/aceitação (escala mata) + complexidade integração + dependência externa para evidence ANPD |
| 4 | JSONB column em `tenants.dpa_history` array | ❌ REJEITADA | Difícil query histórica (`WHERE dpa_history @> ...`), perde benefits SQL native (JOINs, indexes), CASE bloqueado em queries complexas |
| 5 | **Schema dedicated `dpa_acceptances`** | ✅ **CHOSEN** | Table dedicated, SQL native, escalável, audit-friendly, ANPD-defensible, RLS pattern consistente |

---

## 5. DPA Versioning Protocol (Semantic Versioning)

| Bump Type | Exemplo | Mudança | Re-aceite |
|-----------|---------|---------|-----------|
| **MAJOR** | v1.0.0 → v2.0.0 | Mudança material legal (escopo de tratamento, base legal, sub-processadores) | **OBRIGATÓRIO TODOS tenants** |
| **MINOR** | v1.0.0 → v1.1.0 | Clarificação de redação, adição de detalhes não-materiais | **Opcional** (notificação tenant) |
| **PATCH** | v1.0.0 → v1.0.1 | Typos, correções gramáticas, formatação | **Sem re-aceite** |

### Política de notificação MAJOR

- Email tenant **30 dias antes** da entrada em vigor (usa FR-NOTIFY infrastructure Trinity Phase 5.2)
- Bloqueio uso pós-prazo se não re-aceito (status tenant → `dpa_pending`)
- **Grace period 7 dias** após bloqueio para re-aceite sem dataloss

### Storage do texto DPA canônico

- **Path:** `governance/legal/dpa-templates/{version}.md` versionado em git
- **Imutabilidade:** git log preserva history + hash SHA-256 stored em `dpa_acceptances.dpa_text_hash` valida integridade no momento de aceite
- **Naming:** semver folder structure (`v1.0.0.md`, `v2.0.0.md`) — clareza de qual texto exato corresponde a qual hash
- **Cross-domain:** Eric advogado (F-016) redige conteúdo legal substantivo; Aria/Operator versionam estrutura

---

## 6. Retention Policy

### PERMANENT — registros nunca deletados (evidência legal LGPD)

### Distinção LGPD Art. 18 (direito à eliminação):

| Item | Tratamento |
|------|-----------|
| PII tratada (nome, CPF, contratos analisados) | Eliminável a pedido tenant (Art. 18) |
| **PROOF de consent (DPA acceptance)** | **PERMANENT** — necessário defender Eric=operador em ANPD audit retroativa |

**Argumento legal:** tenant pode pedir anonymization de seus DADOS, mas EVIDENCE de aceite legal mantida. Operador precisa provar tratamento foi consentido **na época do tratamento** — sem isso, presunção legal inverte.

### Backup tier
- Weekly snapshots independent do retention principal (defense-in-depth)
- Replicação cross-region opcional Sprint 06+ (Eric decide custo/benefício)

### Anonymization possível (LGPD Art. 18 compliance)
Se tenant cancela SaaS + invoca Art. 18:
- `accepted_by_user_id` → pode ser anonimizado para UUID null sentinel
- `tenant_id`, `dpa_version`, `dpa_text_hash`, `accepted_at`, `ip_address`, `user_agent` → **PRESERVADOS** (evidence aceite legal preservada)

---

## 7. Audit Chain HMAC Integration

DPA acceptance event capturado em audit chain HMAC (pattern ADR-005 + ADR-017).

### Payload structure
```json
{
  "event_type": "dpa_accepted",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "dpa_version": "1.0.0",
  "dpa_text_hash": "sha256_hex",
  "ip_address": "192.0.2.1",
  "accepted_at": "2026-05-07T17:30:00+00:00"
}
```

### Defense-in-depth
- DB row `dpa_acceptances` (primary evidence)
- Chain HMAC entry (secondary evidence — chain link previne tampering)
- Mismatch entre DB e chain → alerta crítico (operacional integrity check)

### Audit query path
- `GET /api/tenant/audit/chain?event_type=dpa_accepted` (admin only — admin role bypass RLS conforme ADR-017 admin pattern)

---

## 8. API Endpoints

### `GET /api/tenant/dpa/current` — DPA atual + status user
```json
Response: {
  "current_version": "1.0.0",
  "current_text": "<markdown texto DPA canônico>",
  "current_hash": "sha256_hex",
  "user_acceptance": {
    "accepted": true,
    "accepted_version": "1.0.0",
    "accepted_at": "2026-05-07T15:00:00-03:00"
  } | null
}
```

### `POST /api/tenant/dpa/accept` — registra aceite

- **Body:** `{"dpa_version": "1.0.0"}`
- **Server-side capture obrigatório:**
  - `ip_address` via `request.client.host`
  - `user_agent` via `request.headers["user-agent"]`
- **Server-side validation:**
  - Hash recomputed do texto canônico atual e validado contra hash stored
  - Se mismatch (DPA atualizada entre `GET /current` e `POST /accept`) → retorna **409 Conflict** com nova versão
- **Atomic transaction:**
  - INSERT `dpa_acceptances` + audit chain event em **single transaction**
  - Falha de chain → rollback DB (consistência absoluta)

### `GET /api/tenant/dpa/history` — admin only, audit purpose
```json
Response: [
  {
    "dpa_version": "1.0.0",
    "accepted_at": "2026-05-07T17:30:00+00:00",
    "accepted_by": "user_uuid",
    "ip_address": "192.0.2.1",
    "user_agent": "Mozilla/5.0 ..."
  },
  ...
]
```

---

## 9. Consequências

### Positivas

- ✅ **ANPD audit defensible** — evidence completa por aceitação (versão + hash + timestamp + IP + user_agent)
- ✅ **Multi-version support** — escala para evolução DPA legal sem retrabalho schema
- ✅ **Hash imutável** previne dispute legal "eu aceitei texto diferente"
- ✅ **RLS multi-tenant** consistente com ADR-017 BACKBONE pattern (manutenibilidade)
- ✅ **Audit chain HMAC dupla** — defense-in-depth contra DB tampering

### Negativas

- ⚠️ **Storage permanent cresce indefinidamente** — mitigável via partitioning por ano em `dpa_acceptances` (Sprint 06+ se volume justificar)
- ⚠️ **Re-aceite forçado em MAJOR** pode causar friction — mitigável via 30 dias notice + grace period 7 dias
- ⚠️ **Texto canônico em git requer disciplina** — Eric advogado redige; Aria/Operator versionam; Operator commit (cross-domain coordenação)
- ⚠️ **API endpoints adicionam complexidade backend** Phase 7+ (3 endpoints novos)

### Neutras

- ℹ️ DPA texto legal substantivo permanece responsabilidade Eric advogado especializado (cross-domain F-016)
- ℹ️ Provider de notificação re-aceite usa FR-NOTIFY infrastructure (Trinity Phase 5.2 — sem decisão duplicada)
- ℹ️ Backup permanent infra usa mesma estratégia geral PostgreSQL Pool (ADR-017 — sem custo arquitetural marginal)

---

## 10. Cross-references

- **ADR-017** (BACKBONE multi-tenant Pool+RLS) — RLS policies pattern aplicado nesta ADR
- **ADR-005** (Audit chain HMAC) — integration pattern preservado
- **ADR-014** (BYOK provider abstraction) — `tenant_api_keys` pattern paralelo (table dedicated + RLS)
- **PRD v2.0.1 FR-LGPD-01** — formaliza mecanismo conceitualmente (Trinity Phase 5.2)
- **PRD v2.0.1 FR-NOTIFY-01..05** — notificação re-aceite MAJOR DPA versioning (Trinity Phase 5.2)
- **Smith F-012** — driver da decisão (`governance/qa/smith-sp04-pivot-adversarial.md` commit `4519ef1`)
- **Smith F-016** — cross-domain Eric advogado redige texto legal substantivo (paralelo, fora escopo Aria)

---

— Aria, arquitetando o futuro 🏗️
