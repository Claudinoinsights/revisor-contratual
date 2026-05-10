---
type: prd
title: "Revisor Contratual — PRD v2.0.1 PATCH (Doctype Content Brief)"
version: "2.0.1.1"
last_updated: "2026-05-10"
status: active
patch_of: "v2.0.0-DRAFT"
patches: ["v2.0.1-DOCTYPE-CONTENT-PATCH"]
project: revisor-contratual
sprint: "04"
phase: 14.5
related_adrs: ["adr-003", "adr-014", "adr-020"]
related_stories: ["SP04-DOCTYPE-01", "SP04-UI-SPA-01"]
authored_by: "@pm Morgan (Strategist) — pattern Trinity legacy alignment Sprint 04"
audience: ["@dev Neo (chunks 5-6 implementation)", "Eric advogado (preenchimento substantivo)", "@architect Aria (validação alignment ADR-020)"]
tags:
  - project/revisor-contratual
  - prd
  - patch
  - sprint-04
  - doctype-content
  - prompt-brief
  - cross-domain
---

# PRD v2.0.1.1 — DOCTYPE CONTENT PATCH (Brief 20 Prompts NOVOS)

```
[@pm · Morgan (Strategist)] — Sprint 04 · Phase 14.5 · PRD PATCH brief 20 prompts
SPRINT: 04 · PHASE: 14.5 · DOMÍNIO: software-dev/legaltech-content · CROSS-DOMAIN
```

> **PATCH escopo restrito:** Esta PATCH adiciona à PRD v2.0.0-DRAFT a **estrutura** de 20 novos prompts de persona necessários para SP04-DOCTYPE-01 (backend Strategy refactor per ADR-020). NÃO inclui conteúdo legal substantivo — esse é responsabilidade Eric advogado (~30min cada × 20 = ~9.5h cumulativo conforme cronograma section 5.1). Pattern AUTH-01 chunk 5 placeholder + finalização advogado.

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

Story `governance/stories/SP04-DOCTYPE-01-multi-doctype-dispatcher-backend.md` (Draft 2026-05-09) implementa Strategy hierárquica per ADR-020. **Chunks 5-6** (persona prompts integration) **bloqueam até Trinity content done**. River decision: skeleton placeholder pattern AUTH-01 chunk 5 — Neo entrega skeletons, Eric advogado preenche conteúdo paralelo.

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
| **v2.0.1.1** | **2026-05-10** | **Morgan** | **PATCH H3 — clarificação conta prompts: 20 NOVOS (4 base + 12 sub + 4 Geral), não 16** |

---

## 2. 20 Prompts NOVOS — Outline Estrutural

### 2.1 Categoria A — Bancário Base (4 arquivos compartilhados via Template Method DRY)

Arquivos em `bloco_workflow/personas/prompts/`:

#### 2.1.1 `advogado_bancario_base.txt`

**Propósito:** Fundamentação jurídica BASE para revisional bancária (compartilhada por CCB + Cartão + Consignado via `BancarioBaseStrategy.doctype_specific_section()`).

**Estrutura sugerida (Eric advogado preenche substantivo):**

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

## 4. Eric Advogado — Preenchimento Substantivo Guidance

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

Cada prompt finalizado por Eric advogado deve passar smoke test:
1. Carrega via `_load_prompt(filename)` sem erro
2. LLM Sabia-7B/Qwen 7B retorna JSON estruturado parseável
3. Validador NLI híbrido aceita citações em ≥80% casos test fixture
4. Juiz veredito segue thresholds ADR-003

---

## 5. Cronograma Sugerido

### 5.1 Effort estimate Eric advogado

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

Neo SP04-DOCTYPE-01 chunks 1-3 (skeleton + dispatchers + router) podem rodar **paralelos** ao Eric advogado work (2-3 days). Chunks 5-6 (prompts integration) bloqueiam até Eric advogado finaliza ≥75% prompts (Categoria A + B prioritários; C pode fechar pós-Done).

---

## 6. Smith Findings Cross-Reference

### 6.1 Findings aplicáveis (preserved)

- **F-016** (LGPD operador) — preserved via SP04-LGPD-01 audit chain integration; conteúdo prompts deve respeitar operador posture (Eric=operador, escritório=controlador)
- **F-013** (RLS isolation visível UI) — não bloqueia esta PATCH; aplicável SP04-UI-SPA-01 settings panel

### 6.2 Findings NEW potential (Smith Sprint 04 close-out)

Smith adversarial review pós-Sprint 04 close pode flag:
- Súmula STJ inexistente citada — Eric advogado verifica oficialmente cada cite
- Resolução BACEN número incorreto — Eric advogado valida via site BACEN
- Output JSON não-parseável Pydantic strict — Eric advogado valida estrutura

---

## 7. Definição de Done (PATCH v2.0.1)

### 7.1 Critérios closure PATCH

- [x] Section 1 Contexto + 1.3 Versionamento documentados
- [x] Section 2 20 prompts outline estrutural por arquivo
- [x] Section 3 Cross-references jurídicas BACEN + Súmulas + Leis
- [x] Section 4 Eric advogado guidance + anti-padrões
- [x] Section 5 Cronograma sugerido (2-3 days)
- [x] Section 6 Smith findings cross-reference

### 7.2 Pendências cross-domain (não esta PATCH)

- ⏳ **Eric advogado** preenche conteúdo substantivo 20 prompts (~9.5h cumulativo, ~2-3 days)
- ⏳ **Neo SP04-DOCTYPE-01 chunks 5-6** integrate prompts pós Eric advogado finaliza
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

## 10. Delta (v2.0.0 → v2.0.1)

### Features Adicionadas
- 20 prompts NOVOS estrutural (4 base + 12 sub + 4 Geral)
- Cross-references Resoluções BACEN + Súmulas STJ + Leis aplicáveis
- Cronograma Eric advogado work (2-3 days)

### Features Não-modificadas
- 12 prompts standalone (veicular/fies/imobiliario × 4 personas) preserved da v1.x.x

### Escopo Atual vs Original
- v2.0.0-DRAFT: 16 prompts (4 personas × 4 doctypes ADR-016 — histórico pré-PATCH)
- v2.0.1: 28 prompts total (4 personas × 7 doctypes ADR-020 — sub-bancários compartilham via Template Method DRY)
- Net incremento: +20 prompts NOVOS brief estrutural (4 base bancário compartilhado + 12 sub-bancários specific + 4 Geral standalone) + Eric advogado preenchimento substantivo paralelo
- Nota arithmetic: 4 personas × 7 doctypes = 28 prompts canônicos; section 2 detalha 20 ARQUIVOS de prompt (DRY via BancarioBaseStrategy compartilha 4 base entre 3 sub-bancários, evitando duplicação)

---

```
[@pm · Morgan (Strategist)] — drafted 2026-05-09 PATCH v2.0.1 (Trinity legacy alignment)
"O conteúdo é do advogado; a estrutura é estratégica.
 Sete portas, sete doutrinas, dezesseis textos novos.
 Eric preenche o substantivo; o sistema executa o adjetivo.
 Mapa pronto — terreno é dele."

— Morgan, planejando o futuro 📊
```
