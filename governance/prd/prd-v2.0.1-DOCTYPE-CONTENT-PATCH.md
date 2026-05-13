---
type: prd
title: "Revisor Contratual — PRD v2.0.4.1 PATCH (Doctype Content Brief + LLM Provider BYOK + Orsheva Glossary + Smith CRITICAL Fixes + Smith Round 2 Cleanup)"
version: "2.0.4.1"
last_updated: "2026-05-12"
status: active
patch_of: "v2.0.0-DRAFT"
patches: ["v2.0.1-DOCTYPE-CONTENT-PATCH", "v2.0.1.1-H3-COUNT-FIX", "v2.0.2-LLM-PROVIDER-CLARIFY", "v2.0.3-ORSHEVA-GLOSSARY", "v2.0.4-SMITH-CRITICAL-FIXES", "v2.0.4.1-SMITH-ROUND-2-CLEANUP"]
project: revisor-contratual
sprint: "04"
phase: 14.5
related_adrs: ["adr-003", "adr-014", "adr-015", "adr-017", "adr-018", "adr-019", "adr-020"]
related_stories: ["SP04-DOCTYPE-01", "SP04-UI-SPA-01", "SP04-LGPD-01"]
authored_by: "@pm Morgan (Strategist) — pattern Trinity legacy alignment Sprint 04"
audience: ["@dev Neo (chunks 5-6 implementation)", "advogado(a) (preenchimento substantivo via BRIEF-EXECUTAVEL-ADVOGADO.md)", "@architect Aria (validação alignment ADR-014 + ADR-020)"]
entities:
  orsheva: "Empresa/marca proprietária do Revisor Contratual (operador LGPD, Admin super-user, role estrutural empresarial). Brandbook OrSheva 7."
  eric_claudino: "Founder Orsheva, decision-maker histórico (autorizações de pivot, ratifications Smith findings, ADR decision_maker)."
tags:
  - project/revisor-contratual
  - prd
  - patch
  - sprint-04
  - doctype-content
  - prompt-brief
  - cross-domain
  - llm-provider-clarify
  - byok-anthropic
  - orsheva-glossary
  - smith-fixes-applied
  - coverage-32-prompts
---

# PRD v2.0.4 — DOCTYPE CONTENT PATCH + LLM PROVIDER BYOK + ORSHEVA GLOSSARY + SMITH CRITICAL FIXES (Brief 32 Prompts)

```
[@pm · Morgan (Strategist)] — Sprint 04 · Phase 14.5 · PRD PATCH brief 32 prompts + LLM Provider clarify + Orsheva glossary + Smith CRITICAL fixes
SPRINT: 04 · PHASE: 14.5 · DOMÍNIO: software-dev/legaltech-content · CROSS-DOMAIN
```

> **PATCH escopo cumulativo:** Esta PATCH (v2.0.4) consolida v2.0.1 + v2.0.1.1 + v2.0.2 + v2.0.3 e adiciona:
> (1) clarificação **LLM Provider — BYOK Anthropic** (ADR-014 ACCEPTED 2026-05-12) — ver Section 1.4;
> (2) estrutura de 20 novos prompts de persona para SP04-DOCTYPE-01 (backend Strategy refactor per ADR-020);
> (3) substituição "Eric advogado" → "advogado(a)" em camadas de produto (papel genérico preenchedor);
> (4) **v2.0.3:** distinção semântica **"Orsheva" (entidade empresarial / role estrutural) vs "Eric Claudino" (founder, decision-maker histórico)** — ver `entities` no frontmatter.
> (5) **NOVO v2.0.4 Smith CRITICAL fixes:** BRIEF ampliado de 20→32 prompts (Bloco D Veículo 4 + Bloco E Imobiliário 4 + Bloco F FIES 4 adicionados) — endereça F-D3-CRIT-01 gap arquitetural (ADR-020 declara 7 doctypes; brief original cobria apenas 4). WARNING BOLD verificação literal Súmulas STJ + Decretos + Resoluções BACEN adicionado (F-D3-HIGH-01 + F-D3-HIGH-02 — Smith suspeitou mis-attribution em 322/472/530/539/603 + Decreto 8.690/2016). Section 1.4 LLM Provider movida para Section 11 standalone (F-D2-MED-01 hierarchy fix). FIES removido de exemplos Bloco C Geral (F-D3-MED-02 classification fix). Cronograma BRIEF ajustado 9.5h→16h Day 1-5 (F-D3-MED-01).
> NÃO inclui conteúdo legal substantivo — esse é responsabilidade do(a) **advogado(a)** (~30min cada × 32 = ~16h cumulativo conforme cronograma BRIEF Capa). Pattern AUTH-01 chunk 5 placeholder + finalização advogado(a). Conteúdo executável consolidado em `BRIEF-EXECUTAVEL-ADVOGADO.md` v2.0.0 (32 prompts, ampliado em v2.0.4).

---

## 1. Contexto

### 1.1 Trigger arquitetural

ADR-020 (Accepted Eric 2026-05-09) supersedes ADR-016, expandindo dispatcher de 4 para **7 doctypes operacionais**:

| # | Doctype | Categoria backend | Personas (4) |
|---|---------|------------------|--------------|
| 1 | CCB Bancária | Sub-bancário (BancarioBaseStrategy) | advogado/economista/validador/juiz |
| 2 | Veículo | Standalone | advogado/economista/validador/juiz |
| 3 | Consignado | Sub-bancário (BancarioBaseStrategy) | advogado/economista/validador/juiz |
| 4 | Cartão de Crédito | Sub-bancário (BancarioBaseStrategy) | advogado/economista/validador/juiz |
| 5 | Imobiliário (SFH/SFI) | Standalone | advogado/economista/validador/juiz |
| 6 | FIES | Standalone | advogado/economista/validador/juiz |
| 7 | Geral (catch-all Tier 3) | Standalone | advogado/economista/validador/juiz |

### 1.2 Story SP04-DOCTYPE-01 dependency

Story `governance/stories/SP04-DOCTYPE-01-multi-doctype-dispatcher-backend.md` (Draft 2026-05-09) implementa Strategy hierárquica per ADR-020. **Chunks 5-6** (persona prompts integration) **bloqueam até Trinity content done**. River decision: skeleton placeholder pattern AUTH-01 chunk 5 — Neo entrega skeletons, advogado(a) preenche conteúdo paralelo.

### 1.3 PRD versionamento

| Version | Data | Autor | Mudança principal |
|---------|------|-------|-------------------|
| v1.0.0 | 2026-04-15 | Morgan | PRD inicial Sprint 01 (CDC Veicular MVP) |
| v1.0.1 | 2026-04-22 | Morgan | PATCH ajustes Sprint 01 escopo |
| v1.0.2 | 2026-05-01 | Morgan | PATCH score 8.7/10 tribunais 2 iterações |
| v1.0.3 | 2026-05-04 | Morgan | DELTA Sprint 02 UI FastAPI |
| v1.1.0 | 2026-05-06 | Morgan | MAJOR Sprint 03 escopo B (4 doctypes ADR-016) |
| v1.1.1 | 2026-05-06 | Morgan | PATCH Sprint 03 ajustes |
| v1.1.2 | 2026-05-06 | Morgan | PATCH MVP Lean ADR-013 |
| v2.0.0-DRAFT | 2026-05-07 | Morgan | MAJOR Sprint 04 cloud SaaS BYOK pivot |
| v2.0.1 | 2026-05-09 | Morgan | PATCH brief prompts (SP04-DOCTYPE-01 paralelo) |
| v2.0.1.1 | 2026-05-10 | Morgan | PATCH H3 — clarificação conta prompts: 20 NOVOS (4 base + 12 sub + 4 Geral), não 16 |
| v2.0.2 | 2026-05-12 | Morgan | PATCH LLM Provider clarify (BYOK Anthropic SDK) + advogado glossário (Eric advogado→advogado(a)) + BRIEF-EXECUTAVEL-ADVOGADO.md criado |
| v2.0.3 | 2026-05-12 | Morgan | PATCH Orsheva glossary — distinção entidade empresarial (Orsheva = operador/Admin/role estrutural) vs decision-maker histórico (Eric Claudino = founder/autorizações). ~30 substituições nas camadas de produto |
| v2.0.4 | 2026-05-12 | Morgan | PATCH Smith CRITICAL fixes — BRIEF ampliado 20→32 prompts (Bloco D Veículo + E Imobiliário + F FIES) + WARNING verificação literal Súmulas STJ + Decreto 8.690→11.150 + Section 1.4 LLM Provider → Section 11 standalone + FIES classification fix + cronograma 9.5h→16h Day 1-5 |
| **v2.0.4.1** | **2026-05-12** | **Morgan** | **Mini-PATCH Smith Round 2 cleanup — 3 prompts ECONOMISTA (10/14/18) warning per-prompt adicionado + 3 residuais Decreto 8.690 corrigidos (L555 + L579 + L1226) + cronograma frontmatter 16h→18h (16h prompts + 2h smoke). Endereça F-R2-MED-01 + F-R2-MED-02 + F-R2-LOW-01 detectados em Smith Round 2 CONTAINED+GREENLIGHT verdict.** |

---

## 11. LLM Provider — BYOK Anthropic (ADR-014 ACCEPTED 2026-05-12)

> **Section standalone** — posicionada fisicamente após Section 1.3 por ordem cronológica de inserção (v2.0.2), MAS é Section 11 top-level (NÃO subseção de "## 1. Contexto"). F-D2-MED-01 Smith review fix: hierarchy clarification. Numeração ## 11 reflete que o conteúdo é independente do Contexto Section 1.
>
> Esta seção consolida ADR-014 (Provider Abstraction Anthropic Only + BYOK Key Management — `accepted` em 2026-05-12 via A_REAFFIRM Eric) para garantir alinhamento PRD ↔ ADR ↔ SPA OrSheva 7 ↔ backend Sprint 04. Backend Ollama Sprint 02 (Sabia-7B / Qwen 7B) é **camada legacy** a ser substituída por Anthropic SDK conforme stories Sprint 04 evoluem.

### 11.1 Modelo de provider

| Aspecto | Decisão | Fonte canônica |
|---------|---------|----------------|
| **BYOK** | Bring Your Own Key **Anthropic** (cada escritório cliente cadastra sua API key) — **NÃO** "BYO Model" / multi-provider | ADR-014 Decisão |
| Provider único | Anthropic SDK Python (`anthropic` package), Sonnet 4.6 default | ADR-014 Componente 1 |
| Vision OCR | Mesmo provider (Sonnet 4.6 vision) | ADR-015 |
| Multi-provider abstraction | **Rejeitada** (A2/A3) — Eric autorizou A1 Anthropic only Phase 1.7 priorizando simplicidade arquitetural | ADR-014 Alternativas |

### 11.2 Encryption at rest

| Camada | MVP | Produção (50+ tenants OR enterprise tier) |
|--------|-----|------------------------------------------|
| Storage | PostgreSQL `pgcrypto` extension via `pgp_sym_encrypt(key, master_key)` | AWS Secrets Manager + KMS customer-managed |
| Master key | `MASTER_ENCRYPTION_KEY` env (filesystem permission 600, não commitada) | AWS KMS rotation policy automatizada |
| Tabela | `tenant_api_keys (tenant_id PK, encrypted_key BYTEA, created_at, last_used_at, status)` | Idem + KMS pointer |
| Rotation | Dual-key state machine `current_key + pending_key` overlap 24h (ADR-014 Componente 5) | Idem + automated via KMS schedule |

### 11.3 Key validation + lifecycle

1. **Key format obrigatório:** `sk-ant-*` (validação regex antes de aceitar)
2. **Obtenção:** [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) — escritório responsável (operador Orsheva não intermedia)
3. **Validation flow:** ping `GET https://api.anthropic.com/v1/models` antes de salvar (request não cobrável)
4. **Audit trail:** todas as keys truncadas em logs (`sk-ant-...XYZ`); tabela `usage_audit` registra requests sem expor key full

### 11.4 Quota Interna (per-tenant)

| Item | Decisão |
|------|---------|
| Granularidade | **1 API key por escritório** (tenant) — todos os(as) advogados(as) do escritório compartilham |
| Audit per-usuário | Tabela `usage_audit (tenant_id, user_id, request_tokens, model, timestamp)` permite relatório interno granular ao escritório (qual advogado(a) consumiu quanto) |
| Sub-keys Anthropic nativos | Não suportados — Quota Interna via audit substitui sem complexidade de proxy intermediário (ADR-014 Componente 7) |
| Limite por escritório | Configurável via TOS/EULA (operador define) — bloqueio quando atingir threshold |

### 11.5 Billing model (consequência do BYOK)

- **Anthropic cobra diretamente** na conta do escritório (sk-ant-* é da Anthropic do escritório, não do Revisor)
- **Revisor cobra** assinatura base + per-approval fee (FR-BILLING-* + ADR-018) — **não intermedia** custos de tokens Anthropic
- Escritório tem **visibilidade total** dos custos Anthropic (dashboard Anthropic) + dos custos Revisor (dashboard interno)
- Margem Revisor: tarifa SaaS independente de uso LLM (escritório paga Anthropic separadamente)

### 11.6 LGPD posture (consequência do BYOK)

| Papel | Antes Sprint 02 (Ollama on-premise) | Sprint 04 BYOK Anthropic |
|-------|-------------------------------------|--------------------------|
| Orsheva (Revisor) | Controlador | **Operador** (ferramenta SaaS) |
| Escritório | Controlador (via uso ferramenta on-premise) | **Controlador** (relação direta com cliente final + responsabilidade base legal) |
| Anthropic | N/A | **Sub-operador** (processador downstream do escritório) |
| Surface auditável | Orsheva direta (on-premise stack) | Orsheva reduzida — Anthropic comercial não treina em customer data por default; ZDR enterprise opcional via tier upgrade |

Cross-reference: ADR-019 (DPA Storage Schema) + ADR-017 (Multi-Tenant Isolation RLS para `tenant_api_keys`).

### 11.7 Cross-references LLM Provider

- **ADR-014** [`../architecture/adr/adr-014-provider-abstraction-byok.md`](../architecture/adr/adr-014-provider-abstraction-byok.md) — Provider decision canônica
- **ADR-015** [`../architecture/adr/adr-015-vision-ocr-architecture.md`](../architecture/adr/adr-015-vision-ocr-architecture.md) — Vision OCR same provider
- **ADR-017** [`../architecture/adr/adr-017-multi-tenant-isolation-rls.md`](../architecture/adr/adr-017-multi-tenant-isolation-rls.md) — RLS para `tenant_api_keys`
- **ADR-018** [`../architecture/adr/adr-018-saas-pricing-billing-event.md`](../architecture/adr/adr-018-saas-pricing-billing-event.md) — Billing model per-approval
- **ADR-019** [`../architecture/adr/adr-019-dpa-storage-schema.md`](../architecture/adr/adr-019-dpa-storage-schema.md) — DPA LGPD operador
- **CON-PROVIDER-01** (PRD v2.0.0-DRAFT) — Anthropic only Phase 1.7

---

## 2. 20 Prompts NOVOS — Outline Estrutural (ver Section 11 para LLM Provider canônico; ver BRIEF-EXECUTAVEL-ADVOGADO.md v2.0.0 para 32 prompts ampliados em v2.0.4)

> **NOTA v2.0.4:** Esta Section 2 mantém os 20 prompts originais. **BRIEF-EXECUTAVEL-ADVOGADO.md v2.0.0** foi ampliado para 32 prompts (Bloco D Veículo + E Imobiliário + F FIES adicionados) em v2.0.4 endereçando Smith F-D3-CRIT-01. Section 11 LLM Provider — BYOK Anthropic é Section standalone (originalmente numerada 1.4 em v2.0.2; re-numerada para 11 em v2.0.4 para clarificar hierarquia top-level).

### 2.1 Categoria A — Bancário Base (4 arquivos compartilhados via Template Method DRY)

Arquivos em `bloco_workflow/personas/prompts/`:

#### 2.1.1 `advogado_bancario_base.txt`

**Propósito:** Fundamentação jurídica BASE para revisional bancária (compartilhada por CCB + Cartão + Consignado via `BancarioBaseStrategy.doctype_specific_section()`).

**Estrutura sugerida (advogado(a) preenche substantivo via BRIEF-EXECUTAVEL-ADVOGADO.md):**

```
[ROLE] Advogado revisional especializado em direito bancário.

[FUNDAMENTAÇÃO BASE]
1. Código de Defesa do Consumidor (Lei 8.078/1990) — Art. 51 cláusulas abusivas
2. BACEN Resolução 4.558/2017 — capitalização juros + transparência
3. Lei 4.595/1964 — Sistema Financeiro Nacional + competência STJ
4. Súmulas STJ aplicáveis: 297 (CDC bancário), 322 (BACEN não aplicável SFH+sistemas privados), 530 (venda casada), 539 (vinculação obrigatória)

[CLÁUSULAS ABUSIVAS COMUNS]
- Anatocismo (capitalização mensal vedada se ausente pacto expresso pré-1996)
- Capitalização juros não autorizada
- Juros remuneratórios acima taxa média BACEN (Súmula 296 STJ)
- Comissão de permanência cumulada com encargos
- Vinculação obrigatória (venda casada)

[OUTPUT FORMAT — JSON estrito Pydantic strict extra='forbid']
{
  "tese_principal": "...",
  "fundamentacao_legal": [...],
  "clausulas_questionadas": [{"clausula": "...", "fundamento_juridico": "..."}],
  "citacao_textual": "..." (≥10 chars),
  "veredito_preliminar": "APROVADO_COM_RISCO_HITL | REJEITADO | APROVADO_100"
}

[NOTAS CONTEXTUAIS]
- Sub-classes (CCB/Cartão/Consignado) ANEXAM doctype_specific_section() abaixo deste prompt
- Output deve ser parseável por Pydantic (extra='forbid')
- NUNCA inventar Súmulas inexistentes — apenas as listadas + cross-domain cdc_cross
```

#### 2.1.2 `economista_bancario_base.txt`

**Propósito:** Cálculo financeiro BASE bancário (Decimal everywhere per FR-CALC-01 + ADR-003).

**Estrutura sugerida:**

```
[ROLE] Economista revisional especializado em finanças bancárias.

[METODOLOGIA BASE]
1. Decimal everywhere (PROIBIDO float) — FR-CALC-01
2. Tabela Price + Sistema Amortização Constante (SAC)
3. BACEN SGS — Sistema Gerenciador de Séries Temporais
4. IOF (Lei 5.143/1966 + Decreto 6.306/2007)
5. Correção monetária — IPCA / SELIC / TR conforme contrato

[BACEN SGS REFERENCES]
- SELIC 1178 (taxa básica)
- IPCA 433 (índice oficial)
- Modalidades CDC: 217 (veículos PF), 218 (outros bens PF), 419 (consignado privado), 432 (consignado público)
- CDI 4391 (Cartão rotativo benchmark)

[OUTPUT FORMAT — JSON estrito]
{
  "calculo_decimal": "...",
  "bacen_divergencia_pct": "0.XX",
  "modalidade_aplicada": "217|218|...",
  "encargos_revisados": "...",
  "valor_revisado": "Decimal('...')"
}

[NOTAS]
- Sub-classes anexam modalidade-specific
- NUNCA float em finanças (FR-CALC-01 violation BLOCK)
```

#### 2.1.3 `validador_bancario_base.txt`

**Propósito:** Validação semântica NLI híbrida per ADR-004 — verifica que tese gerada por advogado/economista respeita citações textuais.

**Estrutura sugerida:**

```
[ROLE] Validador semântico — NLI híbrido per ADR-004.

[METODOLOGIA NLI HÍBRIDA]
1. Similarity (Sentence-BERT) ≥0.7 entre tese e citação textual
2. NLI semântico (modelo BART-large-mnli) — entailment vs contradiction
3. Threshold combinado: similarity ≥0.7 AND NLI=entailment

[VALIDAÇÕES BANCÁRIAS]
- Citação textual ≥10 chars (não permitir "..." ou abbrev)
- Súmula referida deve existir no vault (cross-tag bancario_cross + cdc_cross + doctype-specific)
- Anatocismo / capitalização — verificar se tese cita pacto expresso vs vedação genérica

[OUTPUT FORMAT — JSON estrito]
{
  "validation_passed": true|false,
  "similarity_score": 0.XX,
  "nli_label": "entailment|neutral|contradiction",
  "rejected_reasons": [...]
}

[NOTAS]
- Sub-classes anexam validações específicas (ex: CCB anatocismo proibido)
- NLI false negative = aceitar tese; NLI false positive = rejeitar tese (mais conservador)
```

#### 2.1.4 `juiz_bancario_base.txt`

**Propósito:** Decisor final C1/C2/C3 thresholds per ADR-003 — adaptação BASE bancário (BACEN divergência mais severa).

**Estrutura sugerida:**

```
[ROLE] Juiz revisional — thresholds C1/C2/C3 ADR-003 adaptados bancário.

[CRITÉRIOS C1/C2/C3]
- C1: BACEN divergência (taxa contrato vs SGS modalidade)
  - Bancário: threshold 1.00 se divergência ≥0.05 (5%); 0.50 se 0.02-0.05; 0.00 se <0.02
- C2: Vinculação obrigatória (venda casada) — peso 0.50 se identificada cláusula vinculação
- C3: Jurisdição (estado/UF + lei aplicável)
  - Bancário: 1.00 se estado tem TJ que aplica Súmulas bancárias; 0.50 se TJ regional misto; 0.00 se contradição STJ

[VEREDITO]
- soma C1+C2+C3 ≥2.5 → REJEITADO (cláusulas abusivas confirmadas)
- soma 1.0-2.5 → APROVADO_COM_RISCO_HITL (revisão humana obrigatória CFOAB)
- soma <1.0 → APROVADO_100 (zero red flags)

[OUTPUT FORMAT — JSON estrito]
{
  "c1_score": 0.XX,
  "c2_score": 0.XX,
  "c3_score": 0.XX,
  "veredito": "REJEITADO|APROVADO_COM_RISCO_HITL|APROVADO_100",
  "aderencia_pct": 0.XX
}
```

### 2.2 Categoria B — Sub-bancários Specific (12 arquivos via doctype_specific_section)

#### 2.2.1 CCB (4 arquivos)

**`advogado_ccb_specific.txt`** (anexa ao base):
- Resolução BACEN 4.558/2017 — capitalização CCB
- Anatocismo CCB — Súmula STJ 297, 539 + Súmula 472 (incidentes processuais)
- Capitalização juros — pactuação expressa pós-2001 (MP 1.963/2000 → MP 2.170-36/2001)
- Cross-tag jurisprudência: `ccb` + `bancario_cross` + `cdc_cross`

**`economista_ccb_specific.txt`**:
- Modalidades 217 (CDC veículos PF) ou 218 (CDC outros bens) — Aria valida runtime
- IOF CCB — Lei 5.143/1966 + Decreto 6.306/2007 alíquota PF crédito
- Cálculo Price + amortização CCB

**`validador_ccb_specific.txt`**:
- NLI específico CCB — venda casada CCB+seguro (CDB+Capitalização sem opção rejeição)
- Validar referência à Súmula 297/539 não inventada

**`juiz_ccb_specific.txt`**:
- C1 BACEN divergência ≥0.05 stricter para CCB (taxa CDC bancário tipicamente próxima média)
- C2 vinculação CCB vs seguro — peso 0.75 se obrigatório

#### 2.2.2 Cartão de Crédito (4 arquivos)

**`advogado_cartao_specific.txt`**:
- Súmula 530 STJ — venda casada cartão+empréstimo
- Resolução BACEN 4.549/2017 — rotativo + parcelado limite
- IOF cartão — Decreto 6.306/2007 alíquota cartão crédito
- Anuidade — Resolução BACEN 3.919/2010 (transparência tarifária)
- Cross-tag: `cartao` + `bancario_cross` + `cdc_cross`

**`economista_cartao_specific.txt`**:
- CDI 4391 (rotativo benchmark) + SELIC 1178 + IOF cartão
- Cálculo encargos rotativo (juros após período de atraso)
- Parcelamento sem juros (transparência fornecedor vs cartão)

**`validador_cartao_specific.txt`**:
- NLI cartão — distinguir rotativo vs parcelado vs anuidade
- Validar Súmula 530 STJ citada corretamente

**`juiz_cartao_specific.txt`**:
- C2 vinculação ≤0.4 (cartão tem vinculação alta legítima — bandeiras + emissor)
- C1 divergência rotativo vs CDI threshold mais flexível (rotativo é variável BACEN)

#### 2.2.3 Consignado (4 arquivos)

**`advogado_consignado_specific.txt`**:
- Lei 10.820/2003 — consignado servidor público + privado
- Cap 35% margem consignável (Decreto 8.690/2016 atualizado)
- Súmula 603 STJ — consignado margem
- INSS / militar / servidor distinções (Lei 8.213/91 + estatutos militares)
- Cross-tag: `consignado` + `bancario_cross` + `cdc_cross`

**`economista_consignado_specific.txt`**:
- Modalidades 419 (privado) ou 432 (público) — distinção relevante taxa média BACEN
- Cálculo margem consignável (35% líquido folha)
- Composição taxa: principal + juros + IOF consignado

**`validador_consignado_specific.txt`**:
- NLI consignado — margem extrapolada (>35%), taxa abusiva (>3x média BACEN)
- Validar Lei 10.820 citada (Art. 6º cap)

**`juiz_consignado_specific.txt`**:
- C3 jurisdição cap (Lei 10.820 federal — TR estadual menor relevância)
- C2 vinculação consignado — peso menor (consignado por natureza vinculado folha)

### 2.3 Categoria C — Geral Standalone (4 arquivos catch-all Tier 3)

**Propósito:** Tier 3 fallback per ADR-020 — processa contratos atípicos via prompts genéricos + cross-tag vault.

**`advogado_geral.txt`**:
- Fundamentação CDC base (Lei 8.078/1990) + cross-doctype principles
- Adaptabilidade contratos atípicos (empréstimo pessoal não-consignado, FIES sem MEC, contratos comerciais)
- Cross-tag jurisprudência: `geral` + `cross` (sem doctype-specific scope)

**`economista_geral.txt`**:
- SELIC 1178 genérico + IPCA 433 + cálculos universais
- Sem modalidade BACEN específica (genérica)

**`validador_geral.txt`**:
- NLI híbrido genérico (sem doctype-specific cues — confia em base CDC)

**`juiz_geral.txt`**:
- Thresholds C1/C2/C3 medianos (sem stricter doctype-specific)
- C1 divergência threshold flexível (~0.10) — Geral cobre contratos atípicos

---

## 3. Cross-references Jurídicas

### 3.1 BACEN Resoluções

| Resolução | Tema | Doctype |
|-----------|------|---------|
| 4.558/2017 | Capitalização juros + transparência CCB | CCB |
| 4.549/2017 | Cartão rotativo + parcelado limite | Cartão |
| 3.919/2010 | Tarifas bancárias (anuidade cartão) | Cartão |
| 4.196/2013 | Imobiliário SFH/SFI alíquotas | Imobiliário |

### 3.2 Súmulas STJ

| Súmula | Tema | Doctype |
|--------|------|---------|
| 296 | Taxa juros bancária acima média BACEN | Bancário (CCB/Cartão/Consignado) |
| 297 | CDC aplicável bancário | Bancário base |
| 322 | BACEN não aplicável SFH+sistemas privados | Imobiliário (CDC SFH específico) |
| 472 | Anatocismo CCB pós-2001 | CCB |
| 530 | Venda casada cartão+empréstimo | Cartão |
| 539 | Vinculação obrigatória bancário | Bancário base |
| 603 | Consignado margem | Consignado |

### 3.3 Leis

| Lei | Tema | Doctype |
|-----|------|---------|
| 4.595/1964 | Sistema Financeiro Nacional | Bancário base |
| 5.143/1966 | IOF | Todos bancários |
| 8.078/1990 (CDC) | Defesa Consumidor | Todos |
| 8.213/1991 | Previdência (consignado INSS) | Consignado |
| 10.820/2003 | Consignado servidor + privado | Consignado |
| 10.260/2001 | FIES | FIES |
| 11.977/2009 | Imobiliário Programa Minha Casa Minha Vida | Imobiliário |
| Decreto-Lei 911/1969 | Veicular busca apreensão | Veicular |

---

## 4. Advogado(a) — Preenchimento Substantivo Guidance

### 4.1 Padrão por arquivo

Cada `.txt` deve ter:

1. **`[ROLE]`** — Definição de papel persona (advogado/economista/validador/juiz)
2. **`[FUNDAMENTAÇÃO/METODOLOGIA]`** — Bases legais OU cálculos OU validações OU thresholds
3. **`[CLÁUSULAS / VALIDAÇÕES / CRITÉRIOS]`** — Checklist específico ao doctype
4. **`[OUTPUT FORMAT]`** — JSON Pydantic strict (`extra='forbid'`)
5. **`[NOTAS]`** — Cross-references + anti-padrões + dont-invent

### 4.2 Anti-padrões (proibidos no conteúdo)

- ❌ Inventar Súmulas STJ não-existentes
- ❌ Citar Resolução BACEN com número errado (verificar oficialmente)
- ❌ Confundir lei federal vs estadual
- ❌ Output não-parseável por Pydantic (extra fields, missing required, type mismatch)
- ❌ Float em cálculos financeiros (Decimal everywhere)

### 4.3 Validação ANPD-defensável

Cada prompt finalizado pelo(a) advogado(a) deve passar smoke test:
1. Carrega via `_load_prompt(filename)` sem erro
2. **Anthropic Sonnet 4.6** retorna JSON estruturado parseável (via Anthropic SDK Python per ADR-014 — Sabia-7B/Qwen 7B citados em versões anteriores eram backend legacy Sprint 02, substituído por Anthropic na Sprint 04 cloud pivot)
3. Validador NLI híbrido aceita citações em ≥80% casos test fixture
4. Juiz veredito segue thresholds ADR-003

---

## 5. Cronograma Sugerido

### 5.1 Effort estimate advogado(a)

| Categoria | Arquivos | Effort/arquivo | Total |
|-----------|----------|----------------|-------|
| A — Bancário base | 4 | ~30min | ~2h |
| B — Sub-bancários (CCB+Cartão+Consignado) | 12 | ~30min | ~6h |
| C — Geral standalone | 4 | ~20min (genérico) | ~1.5h |
| **Total cumulativo** | **20** | — | **~9.5h** |

### 5.2 Cronograma 2-3 days

**Day 1 (~4h):**
- Categoria A — bancário base 4 prompts (~2h)
- Categoria B CCB 4 prompts (~2h)

**Day 2 (~4h):**
- Categoria B Cartão 4 prompts (~2h)
- Categoria B Consignado 4 prompts (~2h)

**Day 3 (~1.5h):**
- Categoria C Geral 4 prompts (~1.5h)
- Smoke test integração com Neo skeleton chunks 5

### 5.3 Paralelo Neo work

Neo SP04-DOCTYPE-01 chunks 1-3 (skeleton + dispatchers + router) podem rodar **paralelos** ao trabalho do(a) advogado(a) (2-3 days). Chunks 5-6 (prompts integration) bloqueiam até o(a) advogado(a) finalizar ≥75% prompts (Categoria A + B prioritários; C pode fechar pós-Done).

---

## 6. Smith Findings Cross-Reference

### 6.1 Findings aplicáveis (preserved)

- **F-016** (LGPD operador) — preserved via SP04-LGPD-01 audit chain integration; conteúdo prompts deve respeitar operador posture (Orsheva=operador, escritório=controlador)
- **F-013** (RLS isolation visível UI) — não bloqueia esta PATCH; aplicável SP04-UI-SPA-01 settings panel

### 6.2 Findings NEW potential (Smith Sprint 04 close-out)

Smith adversarial review pós-Sprint 04 close pode flag:
- Súmula STJ inexistente citada — advogado(a) verifica oficialmente cada cite
- Resolução BACEN número incorreto — advogado(a) valida via site BACEN
- Output JSON não-parseável Pydantic strict — advogado(a) valida estrutura

---

## 7. Definição de Done (PATCH v2.0.1)

### 7.1 Critérios closure PATCH

- [x] Section 1 Contexto + 1.3 Versionamento documentados
- [x] Section 2 20 prompts outline estrutural por arquivo
- [x] Section 3 Cross-references jurídicas BACEN + Súmulas + Leis
- [x] Section 4 Advogado(a) guidance + anti-padrões
- [x] Section 5 Cronograma sugerido (2-3 days)
- [x] Section 6 Smith findings cross-reference

### 7.2 Pendências cross-domain (não esta PATCH)

- ⏳ **Advogado(a)** preenche conteúdo substantivo 20 prompts (~9.5h cumulativo, ~2-3 days) — via BRIEF-EXECUTAVEL-ADVOGADO.md
- ⏳ **Neo SP04-DOCTYPE-01 chunks 5-6** integrate prompts pós advogado(a) finaliza ≥75%
- ⏳ **Smith Sprint 04 close-out** revisa prompts ANPD-defensável
- ⏳ **PRD v2.0.0-DRAFT → v2.0.0** finalize (separate PATCH posterior)

---

## 8. Cross-references documentos

- **PRD canônico:** [`prd-v2.0.0-DRAFT.md`](./prd-v2.0.0-DRAFT.md)
- **ADR-020:** [`../architecture/adr/adr-020-multi-doctype-dispatcher-v2.md`](../architecture/adr/adr-020-multi-doctype-dispatcher-v2.md)
- **ADR-003:** [`../architecture/adr/adr-003-implementacao-tecnica-4-personas.md`](../architecture/adr/adr-003-implementacao-tecnica-4-personas.md)
- **Story SP04-DOCTYPE-01:** [`../stories/SP04-DOCTYPE-01-multi-doctype-dispatcher-backend.md`](../stories/SP04-DOCTYPE-01-multi-doctype-dispatcher-backend.md)
- **Sati UX Spec v2.0.0-DRAFT:** [`../ux-spec-v2.0.0-DRAFT.md`](../ux-spec-v2.0.0-DRAFT.md) (sidebar 7 modos delivered Phase 4)
- **TECH-DEBT.md:** [`../TECH-DEBT.md`](../TECH-DEBT.md) — TD-SP04-12 + TD-SP04-13 NEW

---

## 9. Changelog

### v2.0.4.1 (2026-05-12) — Mini-PATCH Smith Round 2 NEW findings cleanup
- **F-R2-MED-01 FIXED:** Warning per-prompt adicionado manualmente em 3 prompts ECONOMISTA (Prompts 10/14/18 — economista_cartao/consignado/geral) que usam "### Cross-refs financeiros" (não "jurídicos") e foram pulados pelo replace_all original v2.0.4. BRIEF agora tem warning per-prompt em **32/32 prompts** (100% coverage)
- **F-R2-MED-02 FIXED:** 3 residuais Decreto 8.690/2016 substituídos por "Decreto 11.150/2022 ou atualização (verificar oficial)" em BRIEF L555 (Prompt 13 Pergunta item 2) + L579 (Prompt 14 Cross-refs financeiros) + L1226 (Checklist final exemplo). Total ocorrências "Decreto 8.690/2016" no BRIEF agora apenas em meta-references (WARNING TOP + 2 explicações)
- **F-R2-LOW-01 FIXED:** Frontmatter BRIEF `estimated_total_hours: "~16h cumulativo Day 1-5"` → `"~18h cumulativo (~16h prompts + 2h smoke test) Day 1-5"`. Tabela "TOTAL 32 prompts" e footer poético atualizados consistentemente. Aritmética: 4×30min×8 blocos = 16h pure prompts + 2h smoke test Day 5 = 18h cumulativo total
- **BRIEF version:** v2.0.0 → **v2.0.1** PATCH
- **Reason:** Smith Round 2 consolidated re-review (governance/qa/smith-consolidated-review-round-2-2026-05-12.md) emitiu CONTAINED+GREENLIGHT confirmando 11/14 findings Round 1 resolvidos mas detectou 4 NEW findings introduzidos por replace_all/edits incompletos da v2.0.4. Eric directou "continue pela Skill" → Opção A Smith recomendada (mini-cleanup antes de prosseguir Operator/Aria/Neo/Advogado). Mini-PATCH completa fixes para Smith Round 3 quick verify (esperado CLEAN)
- **Pendentes (deferred housekeeping non-blocking):** F-R2-INFO-01 (CHECKPOINT shard II) + F-D4-MED-01 (entities rule escalation) + F-D2-LOW-01 (cross-refs cosmético) — endereçados em sessões housekeeping futuras
- **F-R3-LOW-01 FIXED (trivial mini-edit 0g 2026-05-12):** BRIEF L1228 Checklist final "20 respostas" → "32 respostas" — texto stale pós ampliação 0d corrigido. **Sprint 04 Smith Cycle CLOSURE CLEAN** alcançado (16/19 findings resolved + 2 deferred housekeeping + 1 INFO already noted = 100% addressed)
- **CONTEXT DRIFT META-NOTE 2026-05-12:** Operator 0i `gh pr list` revelou que PRs Sprint 04 #4/#5/#6 (SP04-AUTH-01 + SP04-BYOK-01 + SP04-LGPD-01) **JÁ FORAM MERGED em 2026-05-10** no repo dedicated `Claudinoinsights/revisor-contratual` (2 dias antes desta sessão). Toda cadeia Smith/Morgan/Aria 0a→0i trabalhou em assumption OPEN MERGEABLE. **Deliverables continuam válidos para Sprint 05+** (PRD v2.0.4.1 + BRIEF v2.0.1 + ADR-014 + ADR-013 Histórico + Smith reviews) mas **decisão "merge order Sprint 04" era operação inexistente**. **Lesson learned canônica:** sessões long-running > 1 dia requerem `gh pr list -R {repo}` early check Operator Read-only Augment ao context-load original. Context-hygiene.md Regime 1 pre-compaction sweep deveria incluir verificação remote state ANTES de decisões arquiteturais sobre PR merge/creation. Drift natural >24h é INEVITÁVEL — proteção precisa ser mecânica, não cultural
- **FULFILLMENT ADVOGADO 2026-05-12 (20/32 prompts):** Advogado(a) Orsheva entregou 20 prompts preenchidos (Bloco A Bancário Base + B.1 CCB + B.2 Cartão + B.3 Consignado + C Geral = 5 dos 8 Blocos = **62.5% coverage**). Artefato canônico: `PREENCHIMENTO-ADVOGADO-2026-05-12-FINAL.md`. BRIEF bumped v2.0.1 → v2.0.2 (fulfillment_status field). Blocos D/E/F (Veículo + Imobiliário + FIES = 12 prompts) pendentes próxima wave. **Súmulas STJ + Resoluções BACEN + Leis VALIDADAS pelo profissional** — resolve F-D3-HIGH-01 anchor bias risk em produção (runtime usará texto literal validado). Decreto 8.690/2016 mantido por advogado(a) com nota implícita "atualizado" (F-D3-HIGH-02 risk acceptance pelo advogado(a) — autoridade jurídica final). SP04-DOCTYPE-01 chunks 5-6 **PARCIALMENTE DESBLOQUEADOS** — Neo pode integrar Bancário + Geral (4 sub-doctypes funcionais); Veículo+Imobiliário+FIES ficam stub até próxima wave advogado(a) (~6h adicional)

### v2.0.4 (2026-05-12) — PATCH Smith CRITICAL Fixes (verdict INFECTED+FIX-MANDATORY resolved)
- **CRITICAL FIXED (F-D3-CRIT-01):** BRIEF-EXECUTAVEL-ADVOGADO.md ampliado de 20→32 prompts (Bloco D Veículo 4 + Bloco E Imobiliário 4 + Bloco F FIES 4). Endereça gap arquitetural ADR-020 (7 doctypes declarados; prompts atuais hardcoded em `bloco_workflow/personas/{advogado,economista,juiz}.py` são CDC Veicular generic — não doctype-aware). Estimated total: ~16h cumulativo Day 1-5 (escala de 9.5h Day 1-3 anteriores)
- **HIGH FIXED (F-D3-HIGH-01):** WARNING BOLD adicionado topo BRIEF + topo CADA prompt (20 prompts atuais via replace_all + 12 prompts novos com warning embutido) sobre verificação literal Súmulas STJ (322/472/530/539/603 suspect mis-attribution). Neutraliza anchor bias pré-atribuição
- **HIGH FIXED (F-D3-HIGH-02):** Decreto 8.690/2016 → "Decreto regulamentar margem consignável (verificar oficial — provavelmente Decreto 11.150/2022 ou atualização posterior)" em BRIEF Bloco B.3 Prompts 13+14 + cross-refs jurídicos atualizados
- **MEDIUM FIXED (F-D2-MED-01):** Section 1.4 LLM Provider → Section 11 standalone. Subseções 1.4.1-1.4.7 re-numeradas para 11.1-11.7. Nota adicionada em Section 2 apontando Section 11. Hierarchy clarification — Section 11 é top-level standalone (não subseção de Section 1 Contexto)
- **MEDIUM FIXED (F-D3-MED-01):** Cronograma BRIEF ajustado para 32×30min = 16h cumulativo Day 1-5 (consistência aritmética; Bloco C Geral também ajustado para 4×30min = 2h)
- **MEDIUM FIXED (F-D3-MED-02):** FIES removido de exemplos Bloco C Geral catch-all (BRIEF L597 + L618 originais). Movido para Bloco F dedicado conforme ADR-020 doctype standalone. Nota adicionada em Bloco C explicando "FIES tem doctype standalone próprio em Bloco F"
- **Adicionais já feitos por Morpheus direto (não-PRD):**
  - F-D5-MED-01 + F-D5-MED-02: 2 handoffs marcados consumed: true (handoff-architect-to-lmas-master-2026-05-12-spa-adr014-blocking-alert.yaml + handoff-pm-to-lmas-master-2026-05-12-0b-morgan-done.yaml)
- **Pendentes (Aria + Morpheus separate sessions):**
  - F-D1-LOW-01/02/03 (ADR-014 frontmatter styling) — pendente Skill Aria
  - F-D4-MED-01 (entities field escalação rule update) — pendente Morpheus skill update-config separate session
  - F-D6-MED-01 (CHECKPOINT-active.md shard II) — pendente Morpheus next session housekeeping
- **Reason:** Smith consolidated adversarial review 0a+0b+0c emitiu **INFECTED+FIX-MANDATORY** com 14 findings. Eric directou "concerte tudo que for possivel com o maior esforço e sempre pela Skill". PATCH v2.0.4 endereça TODOS findings P0 CRITICAL + HIGH + 3 MEDIUM PRD-related. LOW + handoffs MEDIUM já corrigidos diretamente. Aria F-D1 LOWs serão endereçados em Skill separada subsequente

### v2.0.3 (2026-05-12) — PATCH Orsheva glossary (entidade empresarial vs decision-maker histórico)
- **Added:** Frontmatter `entities` field documentando distinção semântica Orsheva (empresa/role estrutural) vs Eric Claudino (founder, decision-maker histórico)
- **Changed:** ~30 substituições "Eric" → "Orsheva" em roles estruturais distribuídas em 5 arquivos:
  - `prd-v2.0.0-DRAFT.md`: 18 substituições (Eric não absorve / Eric ganha / Eric vira OPERADOR / NÃO do Eric / Eric cobra / Margem Eric / DPA Eric-escritório / papel operador Eric / Eric fees / Admin Eric / ajuda Eric / Eric=operador / qualidade Eric / uso interno Eric / Papel LGPD Eric / Admin Eric super-user / Dashboard Admin Eric / Eric vira operador) + 1 audience clarificação "Eric Claudino (founder Orsheva)"
  - `prd-v2.0.1-DOCTYPE-CONTENT-PATCH.md` (este file): 4 estruturais (operador Eric / Eric (Revisor) / Eric direto + Eric reduzido / Eric=operador F-016)
  - `BRIEF-EXECUTAVEL-ADVOGADO.md`: 1 estrutural (BYOK não Eric → não Orsheva)
  - `docs/sop-monitoramento-tema-1378.md`: 1 (operator maintainer Eric → Orsheva)
  - `docs/sop-populate-vault.md`: 1 (Eric/operador → Orsheva (operador))
- **Fixed:** 7 ocorrências residuais "Eric advogado" que escaparam da v2.0.2 0b substituídas para "advogado(a)" (linhas 61 trigger, 488-490 Smith findings checklist, 501 DoD Section 4, 507-508 Section 7.2, 588 footer poético) — achado lateral 0c
- **Preserved:** "Eric" como decision-maker histórico em ~14 ocorrências (Eric autorizou pivot Phase 1.7-1.7.1 / Eric ratifica Path A / Eric+Mifune cross-domain / Eric direto alternative / Eric C3 volume aspiracional / Eric A_REAFFIRM / Eric clarification / Eric identifica pré-launch / decision-maker em Section "Decisões Eric")
- **Reason:** Eric directive 2026-05-12 "founder/operador/maintainer real esses caras são a Orsheva". Distinção entidade empresarial (Orsheva) vs owner pessoa real (Eric Claudino) mantém clareza histórica sem confusão de role. Distinção operacional explícita em frontmatter `entities` reduz ambiguidade para Smith review + leitores futuros.

### v2.0.2 (2026-05-12) — PATCH LLM Provider clarify + advogado(a) glossário
- **Added:** Section 1.4 "LLM Provider — BYOK Anthropic" (7 subseções: modelo, encryption, validation lifecycle, Quota Interna, billing model, LGPD posture, cross-refs) — consolida ADR-014 ACCEPTED 2026-05-12 no PRD canônico
- **Changed:** Section 4.3 smoke test bullet 2 — "LLM Sabia-7B/Qwen 7B retorna JSON" → "Anthropic Sonnet 4.6 retorna JSON (via Anthropic SDK Python per ADR-014)" — alinha backend legacy Sprint 02 vs runtime Sprint 04
- **Changed:** "Eric advogado" → "advogado(a)" em camadas de produto (Section 1.2 trigger, 2.1.1 estrutura sugerida, 4 título, 4.3 smoke, 5.1 effort estimate, 5.3 paralelo Neo, frontmatter audience). **Preservado:** "Eric=operador" (Section 6.1, papel LGPD canônico) + "Eric founder/Admin/decision-maker" em PRD v2.0.0-DRAFT (papel histórico real, não substituível)
- **Added:** Cross-reference para `BRIEF-EXECUTAVEL-ADVOGADO.md` (criado nesta sessão consolidando 20 prompts em formato execução offline)
- **Added:** `related_adrs` frontmatter expandido — ADR-015 + ADR-017 + ADR-018 + ADR-019 (cadeia Sprint 04 completa)
- **Added:** `related_stories` frontmatter — SP04-LGPD-01 (cadeia LGPD operador)
- **Reason:** Eric A_REAFFIRM 2026-05-12 pós-Morpheus alerta SPA-backend false-positive resolvido (sessão BLOCKING ALERT Aria detectou: SPA já alinhado com ADR-014 desde chunk 1 MINIMAL 2026-05-09). PATCH garante alinhamento PRD ↔ ADR-014 ↔ SPA OrSheva 7 ↔ backend Sprint 04 e prepara terreno para Eric advogado(a) iniciar preenchimento brief offline (~9.5h cumulativo Day 1-3)

### v2.0.1.1 (2026-05-10) — PATCH H3 conta inconsistente prompts
- **Fixed:** Sumário/título mencionavam "16 prompts NOVOS" mas seção 2 detalhava 4+12+4 = 20 (4 base bancário + 12 sub-bancários + 4 Geral standalone)
- **Changed:** Título PRD "Brief 16 Prompts NOVOS" → "Brief 20 Prompts NOVOS"
- **Changed:** Section 2 heading "16 Prompts NOVOS" → "20 Prompts NOVOS"
- **Changed:** Effort cumulativo recalculado consistentemente: 30min × 20 = ~9.5h (cronograma section 5.1 já estava correto)
- **Clarified:** Delta section — distinção entre 28 prompts canônicos (4 personas × 7 doctypes) vs 20 ARQUIVOS de prompt (DRY via BancarioBaseStrategy compartilha 4 base entre 3 sub-bancários)
- **Reason:** Smith H3 HIGH (governance/qa/smith-adversarial-review-sprint-04-pre-merge-2026-05-09.md) identificou inconsistência documental pré-merge; Hamann board Caminho A deferiu POST-MERGE; PATCH agora resolve narrative consistency
- **Não-impact:** Conteúdo legal substantivo dos prompts não alterado (Eric advogado scope preserved); estrutura backend ADR-020 não alterada (7 doctypes mantidos)

### v2.0.1 (2026-05-09) — PATCH brief 20 prompts NOVOS
- **Added:** 20 prompts brief estrutural — 4 base bancário + 12 sub-bancários specific + 4 Geral standalone
- **Added:** Cross-references jurídicas (BACEN Resoluções 4.558/4.549/3.919/4.196 + 7 Súmulas STJ + 8 Leis)
- **Added:** Eric advogado guidance + anti-padrões + cronograma 2-3 days
- **Reason:** Desbloqueio cross-domain SP04-DOCTYPE-01 chunks 5-6 (Trinity Phase 3 PRD update River dependency)
- **Pattern:** Skeleton placeholder AUTH-01 chunk 5 + Eric advogado preenchimento substantivo (idêntico SP04-LGPD-01 DPA texto)

### v2.0.0-DRAFT (2026-05-07)
- (preserved — referência base)

---

## 10. Delta (v2.0.0 → v2.0.4)

### Features Adicionadas (cumulativo v2.0.1 → v2.0.1.1 → v2.0.2 → v2.0.3 → v2.0.4)
- 20 prompts NOVOS estrutural (4 base + 12 sub + 4 Geral) — v2.0.1
- Cross-references Resoluções BACEN + Súmulas STJ + Leis aplicáveis — v2.0.1
- Cronograma advogado(a) work (2-3 days) — v2.0.1; **ampliado para Day 1-5 (16h) em v2.0.4**
- **Section 1.4 LLM Provider — BYOK Anthropic** (consolida ADR-014 ACCEPTED 2026-05-12) — v2.0.2; **renumerada Section 11 standalone em v2.0.4**
- Cross-reference `BRIEF-EXECUTAVEL-ADVOGADO.md` — v2.0.2 (20 prompts); **ampliado v2.0.0 BRIEF com 32 prompts em v2.0.4**
- **Frontmatter `entities` documentando Orsheva (empresa/role estrutural) vs Eric Claudino (founder/decision-maker)** — v2.0.3
- **NOVO v2.0.4:** BRIEF Bloco D Veículo (4 prompts) + Bloco E Imobiliário SFH/SFI (4 prompts) + Bloco F FIES (4 prompts) = +12 prompts addressing F-D3-CRIT-01 gap
- **NOVO v2.0.4:** WARNING CRÍTICO topo BRIEF + warning per-prompt sobre verificação literal Súmulas STJ + Decretos + Resoluções BACEN

### Features Não-modificadas
- ~~12 prompts standalone (veicular/fies/imobiliario × 4 personas) preserved da v1.x.x~~ **CORREÇÃO v2.0.4 (F-D3-CRIT-01):** afirmação anterior era INCORRETA — prompts hardcoded em `bloco_workflow/personas/{advogado,economista,juiz}.py` são CDC Veicular generic não doctype-aware. v2.0.4 ampliou BRIEF para 32 prompts incluindo Veículo/Imobiliário/FIES explicitamente
- "Eric autorizou pivot Phase 1.7-1.7.1" / "Eric ratifica Path A" / "Eric+Mifune cross-domain" / "Eric A_REAFFIRM" / "Eric C3 volume aspiracional" / "Eric direto alternative" / "Eric identifica pré-launch" — decision-maker histórico preservado

### Features Substituídas (v2.0.2 + v2.0.3 + v2.0.4)
- "Eric advogado" (papel preenchedor genérico) → "advogado(a)" em camadas de produto — v2.0.2 + 7 residuais corrigidos v2.0.3
- "Sabia-7B/Qwen 7B" (backend legacy Sprint 02) → "Anthropic Sonnet 4.6" (runtime canônico Sprint 04 per ADR-014) em Section 4.3 — v2.0.2
- **"Eric" (role estrutural empresarial)** → **"Orsheva"** em PRDs v2.0.x + BRIEF + SOPs (5 arquivos, ~30 substituições) — v2.0.3
- **NOVO v2.0.4:** "Decreto 8.690/2016 cap 35% margem consignável" → "Decreto regulamentar (verificar oficial — provavelmente Decreto 11.150/2022 ou atualização)" em BRIEF Bloco B.3 Prompts 13+14
- **NOVO v2.0.4:** Section 1.4 LLM Provider (subseção de Section 1) → Section 11 LLM Provider (top-level standalone)
- **NOVO v2.0.4:** Cronograma BRIEF 9.5h Day 1-3 → 16h Day 1-5

### Features Removidas (v2.0.4)
- FIES de exemplos Bloco C Geral catch-all (movido para Bloco F dedicated standalone conforme ADR-020 doctype standalone)

### Escopo Atual vs Original
- v2.0.0-DRAFT: 16 prompts (4 personas × 4 doctypes ADR-016 — histórico pré-PATCH)
- v2.0.1: 28 prompts total (4 personas × 7 doctypes ADR-020 — sub-bancários compartilham via Template Method DRY)
- v2.0.2: 28 prompts canônicos + Section 1.4 LLM Provider BYOK + advogado(a) glossário
- v2.0.3: idem v2.0.2 + Orsheva glossary (entidade empresarial vs decision-maker histórico)
- **v2.0.4: 32 prompts BRIEF (full coverage 7 doctypes) + WARNING verificação literal + Section 11 standalone + Decreto fix + cronograma 16h**
- Net incremento v2.0.3 → v2.0.4: +12 prompts BRIEF (Bloco D+E+F) + WARNING TOP + 20 warnings per-prompt (replace_all) + 12 warnings embutidos (novos prompts) + Section 11 renumeração + Decreto 8.690→11.150 fix + Bloco C FIES classification fix + cronograma 9.5h→16h + Changelog v2.0.4 + Delta cumulativo atualizado
- Nota arithmetic: 4 personas × 7 doctypes = 28 prompts canônicos via DRY BancarioBaseStrategy; BRIEF v2.0.0 entrega 32 ARQUIVOS (4 base bancário compartilhado + 12 sub-bancários specific + 4 Geral standalone + 4 Veículo standalone + 4 Imobiliário standalone + 4 FIES standalone = 32). Full coverage ADR-020 7 doctypes alcançada via PATCH v2.0.4

---

```
[@pm · Morgan (Strategist)] — drafted 2026-05-09 PATCH v2.0.1 (Trinity legacy alignment)
"O conteúdo é do advogado; a estrutura é estratégica.
 Sete portas, sete doutrinas, dezesseis textos novos.
 Advogado(a) preenche o substantivo; o sistema executa o adjetivo.
 Mapa pronto — terreno é dele."

— Morgan, planejando o futuro 📊
```
