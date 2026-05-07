---
type: adr
id: "ADR-014"
title: "Provider Abstraction Anthropic Only + BYOK Key Management"
status: proposed
date: "2026-05-07"
domain: infra
adr_level: design
decision_makers:
  - "@architect (Aria) — design"
  - "@analyst (Atlas) — research v2 Section 1"
  - "Eric Claudino — autorização A1 + LGPD Path A"
supersedes:
  - "ADR-010"
  - "ADR-011"
superseded_by: ""
related_to:
  - "ADR-017 (multi-tenant isolation — RLS para tenant_api_keys)"
  - "ADR-015 (vision OCR — usa mesmo provider)"
project: revisor-contratual
sprint: "04"
phase: "2.1"
tags:
  - project/revisor-contratual
  - adr
  - sprint-04
  - byok
  - anthropic
  - multi-tenant
---

# ADR-014: Provider Abstraction Anthropic Only + BYOK Key Management

## Contexto

Sprint 04 marca pivot de LLM local (Sabia 7B + Qwen 7B/3B via Ollama, ADR-010 + ADR-011) para SaaS B2B BYOK (Bring Your Own Key) onde cada escritório de advocacia cliente fornece sua própria API key. Eric escolheu **provider abstraction A1** (Anthropic only hardcoded) — não suporta OpenRouter ou OpenAI nesta versão.

Motivações:
- Smith CC.41 F-A1 demonstrou hardware Eric (16GB RAM) inviável para LLMs locais simultâneos
- Atlas v2 Section 4 mapeou Anthropic API comercial como provider com melhor LGPD posture (não treina em customer data por default)
- LGPD Path A com BYOK move Eric de controlador para operador (Atlas v2 Section 4 — surface massivamente reduzida)

## Decisão

**Anthropic API only via SDK oficial Python (`anthropic` package), sem abstração multi-provider.** Cada escritório cadastra sua API key Anthropic individual; BYOK pattern com Quota Interna (1 key por escritório, audit per-advogado).

Componentes:
1. **Anthropic SDK** (não HTTP direto): type safety, retry built-in, streaming nativo
2. **Encryption at rest**: PostgreSQL `pgcrypto` extension via `pgp_sym_encrypt(key, master_key)` MVP; AWS Secrets Manager + KMS produção
3. **Master env key** `MASTER_ENCRYPTION_KEY` filesystem permission 600 (não commitada)
4. **Key validation flow**: ping `GET https://api.anthropic.com/v1/models` antes de aceitar (não cobra)
5. **Dual-key rotation**: state machine `current_key + pending_key` overlap 24h
6. **Audit trail**: tabela `usage_audit (tenant_id, user_id, request_tokens, model, timestamp)` — keys sempre truncadas em logs (`sk-ant-...XYZ`)
7. **Pattern Quota Interna**: tabela `tenant_api_keys (tenant_id PK, encrypted_key BYTEA, created_at, last_used_at, status)` — 1 key/escritório, todos advogados compartilham; audit separa por user_id

## Razão

- **Type safety SDK vs HTTP direto**: SDK Anthropic oficial valida tipos request/response em compile-time, reduz bugs de integração; HTTP direto exigiria reimplementar retry exponencial + streaming parser
- **Anthropic only vs multi-provider**: Atlas v1 Section 1 mostrou Claude Sonnet 4.6 vence em legal accuracy (97,6% extraction + 0,09% hallucination) — único provider necessário para qualidade required. Multi-provider abstraction (A2/A3) aumenta surface de bugs sem ganho proporcional
- **pgcrypto MVP vs Vault produção**: Atlas v2 Section 1 — pgcrypto zero custo, escala 50+ tenants; Vault/Secrets Manager justifica-se em scale enterprise (50+ tenants OR enterprise tier com customer-managed KMS)
- **Quota Interna vs sub-keys**: Anthropic não suporta sub-keys nativos; Quota Interna via audit per-advogado dá granularidade necessária sem complexidade de proxy intermediário

## Alternativas Consideradas

### A2 — Multi-provider abstraction (Anthropic + OpenRouter + OpenAI)

**Rejeitada.** Atlas v2 Section 1 documentou que adapter pattern para 3 providers triplica surface de testes + manutenção (cada provider com retry/streaming/error handling diferente). Eric explicitamente escolheu A1 priorizando simplicidade arquitetural sobre flexibilidade de cliente.

### A3 — OpenRouter como gateway único

**Rejeitada.** OpenRouter intermedia mas adiciona hop adicional na cadeia de logging (Atlas v2 Section 4 — surface auditável aumenta). Eric escolheu LGPD posture máxima Path A → Anthropic direto reduz subprocessors a 1.

### Vault HashiCorp + KMS customer-managed para MVP

**Rejeitada.** Atlas v2 Section 1 — overkill setup para Eric solo dev. Migration para Secrets Manager faz sentido em produção (50+ tenants OR enterprise tier).

### Cada advogado cadastra key própria

**Rejeitada.** Anthropic billing não distingue por sub-organização nativamente. Quota Interna via audit per-advogado oferece mesma granularidade interna para escritório, sem complicar relacionamento com Anthropic.

## Consequências

### Positivas
- Stack simples: 1 provider, 1 SDK, 1 encryption strategy
- LGPD posture máxima Path A: Anthropic API comercial não treina + ZDR enterprise opcional
- BYOK protege Eric de risco financeiro API (escritório paga sua conta)
- Audit per-advogado dá relatório interno granular ao escritório

### Negativas
- Vendor lock-in Anthropic: se Anthropic deprecar Sonnet 4.6 OR aumentar preços, projeto exposto
- Sem fallback automático para outro provider (Eric assume risco)
- pgcrypto requer master env key gestão cuidadosa (rotation manual)

### Neutras
- Sub-keys não suportados — escritórios com >10 advogados podem querer no futuro (debt CC.43+)
- AWS Secrets Manager migration é debt explícito, não bloqueante

## Cross-references

- **Atlas v2 Section 1** (BYOK API Key Security & Storage) — base research
- **Atlas v1 Section 1** (OpenRouter catalog) — provider comparison context
- **Smith CC.41 F-A1** — motivação RAM constraint que justifica cloud
- **ADR-010 (superseded)** — Sabia Q4 + Qwen mitigation local
- **ADR-011 (superseded)** — Auto-Ollama Lifecycle local
- **ADR-017 (related)** — Multi-tenant isolation cobre RLS para `tenant_api_keys`
- **ADR-015 (related)** — Vision OCR usa mesmo provider Anthropic
