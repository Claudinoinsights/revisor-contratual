---
type: brief
title: "Brief Executável — Advogado(a) preenche conteúdo legal Sprint 04 (32 prompts)"
project: revisor-contratual
version: "2.0.2"
last_updated: "2026-05-12"
status: active
fulfillment_artifact: "PREENCHIMENTO-ADVOGADO-2026-05-12-FINAL.md"
fulfillment_status:
  bloco_a: "✅ DONE 2026-05-12 (4/4 prompts Bancário Base)"
  bloco_b1: "✅ DONE 2026-05-12 (4/4 prompts CCB)"
  bloco_b2: "✅ DONE 2026-05-12 (4/4 prompts Cartão)"
  bloco_b3: "✅ DONE 2026-05-12 (4/4 prompts Consignado)"
  bloco_c: "✅ DONE 2026-05-12 (4/4 prompts Geral catch-all)"
  bloco_d_veiculo: "⏳ PENDENTE próxima wave"
  bloco_e_imobiliario: "⏳ PENDENTE próxima wave"
  bloco_f_fies: "⏳ PENDENTE próxima wave"
  total: "20/32 ARQUIVOS entregues (62.5%) — SP04-DOCTYPE-01 chunks 5-6 PARCIALMENTE DESBLOQUEADO (Bancário+Geral apenas)"
related_to:
  - "PRD v2.0.4 (canonical — `prd-v2.0.1-DOCTYPE-CONTENT-PATCH.md`)"
  - "ADR-014 Provider Abstraction Anthropic Only + BYOK (accepted 2026-05-12)"
  - "ADR-020 Multi-Doctype Dispatcher v2 (accepted — 7 doctypes)"
  - "ADR-003 Implementação Técnica 4 Personas"
  - "SP04-DOCTYPE-01 (chunks 5-6 dependem deste brief)"
  - "Smith Consolidated Review 0a+0b+0c 2026-05-12 (verdict INFECTED+FIX-MANDATORY resolved via PATCH v2.0.4)"
authored_by: "@pm Morgan (Strategist) — derivado de PRD v2.0.4 Section 2 + Smith CRITICAL fixes"
audience: "advogado(a) especializado(a) em direito bancário/consumidor/imobiliário/educacional — preenche offline"
estimated_total_hours: "~18h cumulativo (~16h prompts + 2h smoke test) Day 1-5"
distribution:
  bloco_a_bancario_base: 4 arquivos (~2h)
  bloco_b1_ccb: 4 arquivos (~2h)
  bloco_b2_cartao: 4 arquivos (~2h)
  bloco_b3_consignado: 4 arquivos (~2h)
  bloco_c_geral: 4 arquivos (~2h)
  bloco_d_veiculo: 4 arquivos (~2h)
  bloco_e_imobiliario: 4 arquivos (~2h)
  bloco_f_fies: 4 arquivos (~2h)
  total: 32 arquivos
tags:
  - project/revisor-contratual
  - brief
  - sprint-04
  - legal-content
  - executable-offline
  - coverage-32-prompts
  - smith-fixes-applied
---

# Brief Executável — Advogado(a) preenche conteúdo legal Sprint 04

> **Objetivo:** consolidar os 32 prompts brief estrutural do PRD v2.0.4 (Section 2) em formato execução **offline** para o(a) advogado(a) preencher sem precisar abrir o PRD completo. Morgan/Neo absorvem as respostas posteriormente e migram para `bloco_engine/strategies/{nome}.py` docstring + `bloco_workflow/personas/prompts/{nome}.txt` + `bloco_dataset/{nome}.json` conforme aplicável.
>
> **Premissa:** o(a) advogado(a) entende que este brief documenta a **ESTRUTURA** dos prompts; o **conteúdo legal substantivo** (fundamentação jurídica detalhada, redações finais) é responsabilidade jurídica do(a) profissional. Premissas e antinomias inevitáveis (ex: divergência STJ vs TJ regional) devem ser documentadas na resposta.
>
> **PATCH v2.0.4 — Smith CRITICAL fixes aplicados:** ampliado de 20→32 prompts (Bloco D Veículo + E Imobiliário + F FIES adicionados após Smith F-D3-CRIT-01 detectar gap arquitetural — ADR-020 declara 7 doctypes, brief original cobria apenas 4). WARNING obrigatório verificação literal Súmulas/Resoluções/Decretos adicionado (F-D3-HIGH-01 + F-D3-HIGH-02 — Smith suspeitou mis-attribution).

---

## Capa

### Sequência sugerida (cronograma Day 1-5)

| # | Bloco | Categoria | Arquivos | Estimativa | Dependência |
|---|-------|-----------|----------|------------|-------------|
| 1 | **A** | Bancário Base (compartilhado via Template Method DRY) | 4 | ~2h | Nenhuma — primeiro |
| 2 | **B.1** | CCB Bancária (specific override) | 4 | ~2h | Bloco A finalizado |
| 3 | **B.2** | Cartão de Crédito (specific override) | 4 | ~2h | Bloco A finalizado |
| 4 | **B.3** | Consignado (specific override) | 4 | ~2h | Bloco A finalizado |
| 5 | **D** | Veículo (standalone) | 4 | ~2h | Independente |
| 6 | **E** | Imobiliário SFH/SFI (standalone) | 4 | ~2h | Independente |
| 7 | **F** | FIES (standalone) | 4 | ~2h | Independente |
| 8 | **C** | Geral (catch-all Tier 3 — atualizado SEM FIES) | 4 | ~2h | Após todos os doctypes específicos |
| | | **TOTAL** | **32** | **~18h cumulativo (16h prompts + 2h smoke test Day 5)** | — |

### Cronograma sugerido

| Day | Blocos | Horas |
|-----|--------|-------|
| **Day 1** | A (Bancário Base 4) + B.1 (CCB 4) | ~4h |
| **Day 2** | B.2 (Cartão 4) + B.3 (Consignado 4) | ~4h |
| **Day 3** | D (Veículo 4) + E (Imobiliário 4) | ~4h |
| **Day 4** | F (FIES 4) + C (Geral catch-all 4) | ~4h |
| **Day 5** | Smoke test review consolidado + checklist final + verificações Súmulas/Resoluções literais oficial | ~2h |

### Como preencher

1. **Leitura prévia:** revise ADR-003 (4 personas — advogado/economista/validador/juiz) e ADR-020 (7 doctypes hierárquicos)
2. **Por prompt:** campo "**Resposta**" abaixo de cada item — escreva diretamente neste arquivo (prosa estruturada em pt-BR)
3. **Padrão `.txt`:** cada resposta vai gerar um arquivo `.txt` em `bloco_workflow/personas/prompts/` seguindo estrutura `[ROLE] / [FUNDAMENTAÇÃO|METODOLOGIA] / [CLÁUSULAS|VALIDAÇÕES|CRITÉRIOS] / [OUTPUT FORMAT JSON] / [NOTAS]` (ver PRD v2.0.2 Section 2.1.1 como exemplo canônico de `advogado_bancario_base.txt`)
4. **Anti-padrões (proibidos):**
   - ❌ Inventar Súmulas STJ não-existentes (verificar via [stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/Sumulas.aspx](https://www.stj.jus.br))
   - ❌ Citar Resolução BACEN com número errado (verificar via [bcb.gov.br](https://www.bcb.gov.br/estabilidadefinanceira/buscanormas))
   - ❌ Confundir lei federal vs estadual
   - ❌ Output não-parseável por Pydantic (extra fields, missing required, type mismatch)
   - ❌ Float em cálculos financeiros — Decimal everywhere (FR-CALC-01 violation = BLOCK)

### Provider LLM em runtime

Os prompts serão executados via **Anthropic SDK Python (Sonnet 4.6)** per ADR-014. Backend Ollama Sprint 02 (Sabia-7B/Qwen) foi substituído pelo pivot Sprint 04 cloud — escrever os prompts assumindo runtime Anthropic (BYOK por escritório, não Orsheva).

---

## ⚠️ WARNING CRÍTICO — Verificação Literal Mandatory de Súmulas + Resoluções + Decretos

**Smith adversarial review 2026-05-12 suspeita material mis-attribution** nas seguintes referências jurídicas pré-atribuídas a temas operacionais neste brief:

- **Súmula 322 STJ** atribuída a "BACEN não aplicável SFH+sistemas privados" — Smith suspeita texto literal real é sobre "repetição de indébito em conta corrente, prova de erro não exigida"
- **Súmula 472 STJ** atribuída a "anatocismo CCB pós-2001" — Smith suspeita texto literal real é sobre "comissão de permanência (limite encargos remuneratórios+moratórios)"
- **Súmula 530 STJ** atribuída a "venda casada cartão+empréstimo" — Smith suspeita texto literal real é sobre "taxa juros bancários médios BACEN" (similar Súmula 296)
- **Súmula 539 STJ** atribuída a "vinculação obrigatória bancário" — Smith suspeita texto literal real é sobre "capitalização juros pactuação expressa pós-2001 (MP 2.170-36/2001)"
- **Súmula 603 STJ** (consignado margem) — Smith nota interpretação modificada em 2018 (EREsp 1.555.722) — vale como base mas pode levar a citação obsoleta
- **Decreto 8.690/2016** atribuído a cap 35% margem consignável — Smith suspeita decreto incorreto (provavelmente PNAATA Programa Nacional Captação Água Chuva); cap consignável atual provavelmente **Decreto 11.150/2022** ou atualização posterior

**AÇÃO MANDATORY do(a) advogado(a) ANTES de aceitar qualquer atribuição:**

1. **VERIFICAR texto literal oficial de CADA Súmula** em [stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/Sumulas.aspx](https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/Sumulas.aspx)
2. Se Súmula atribuição NÃO bater com tema → substituir por Súmula correta + documentar correção no campo "Resposta" do prompt
3. **Verificar Resoluções BACEN** em [bcb.gov.br/estabilidadefinanceira/buscanormas](https://www.bcb.gov.br/estabilidadefinanceira/buscanormas)
4. **Verificar Decretos** em [planalto.gov.br](http://www.planalto.gov.br) (foco especial: cap margem consignável atual — Decreto 11.150/2022 ou alteração)
5. Smith NÃO pôde confirmar números sem internet — **verificação humana é OBRIGATÓRIA, não opcional**

**Anti-padrão Constitution v2.0.0 No Invention universal:** pré-atribuição sem verificação é forma sutil de invenção. Brief lista anti-padrão "não inventar Súmulas" no checklist final, mas pré-atribuições atuam como **anchor bias** inicial. Esta seção neutraliza o anchor bias antecipadamente.

---

# Bloco A — Bancário Base (4 prompts compartilhados via `BancarioBaseStrategy.doctype_specific_section()` DRY)

> **Pattern:** Template Method — sub-classes (CCB/Cartão/Consignado) ANEXAM `doctype_specific_section()` abaixo do base.
> **Saída por arquivo:** `bloco_workflow/personas/prompts/{persona}_bancario_base.txt`
> **Doctypes consumidores:** CCB Bancária + Cartão de Crédito + Consignado.

---

## Prompt 1 — `advogado_bancario_base.txt`

**Bloco:** A — Bancário Base
**Pattern:** BancarioBaseStrategy Template Method
**Estimativa:** ~30min

### Contexto
Fundamentação jurídica BASE para revisional bancária compartilhada por CCB + Cartão + Consignado. Define `[ROLE]`, leis fundamentais, cláusulas abusivas comuns e estrutura de output JSON Pydantic strict.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **CDC:** Lei 8.078/1990 — Art. 51 cláusulas abusivas
- **BACEN:** Resolução 4.558/2017 (capitalização juros + transparência)
- **Lei 4.595/1964** — Sistema Financeiro Nacional + competência STJ
- **Súmulas STJ:** 297 (CDC bancário), 322 (BACEN não SFH), 530 (venda casada), 539 (vinculação obrigatória), 296 (taxa acima média BACEN)

### Pergunta
Redija o conteúdo do prompt `advogado_bancario_base.txt` cobrindo:
1. `[ROLE]` Advogado revisional bancário — papel persona
2. `[FUNDAMENTAÇÃO BASE]` Leis + Resoluções + Súmulas aplicáveis a bancário em geral (não doctype-specific)
3. `[CLÁUSULAS ABUSIVAS COMUNS]` Checklist (anatocismo, capitalização não-autorizada, juros acima média, comissão permanência cumulada, venda casada)
4. `[OUTPUT FORMAT]` JSON Pydantic strict `extra='forbid'`: campos `tese_principal`, `fundamentacao_legal[]`, `clausulas_questionadas[{clausula, fundamento_juridico}]`, `citacao_textual` (≥10 chars), `veredito_preliminar` (APROVADO_COM_RISCO_HITL | REJEITADO | APROVADO_100)
5. `[NOTAS]` Sub-classes ANEXAM doctype_specific_section abaixo; output deve ser parseável Pydantic; NUNCA inventar Súmulas

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/advogado_bancario_base.txt`
- **Docstring Python:** `bloco_engine/strategies/bancario_base_strategy.py` — método `BancarioBaseStrategy.advogado_prompt_section()`

### Resposta
[ ]

---

## Prompt 2 — `economista_bancario_base.txt`

**Bloco:** A — Bancário Base
**Pattern:** BancarioBaseStrategy Template Method
**Estimativa:** ~30min

### Contexto
Cálculo financeiro BASE bancário — Decimal everywhere (FR-CALC-01 + ADR-003). Define metodologia base, BACEN SGS references, output JSON.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos / financeiros
- **FR-CALC-01:** Decimal everywhere (PROIBIDO float)
- **Tabela Price + SAC** — sistemas amortização
- **BACEN SGS:** SELIC 1178 (taxa básica), IPCA 433 (índice oficial), CDC modalidades 217 (veículos PF), 218 (outros bens PF), 419 (consignado privado), 432 (consignado público), CDI 4391 (Cartão rotativo)
- **IOF:** Lei 5.143/1966 + Decreto 6.306/2007
- **Correção monetária:** IPCA / SELIC / TR conforme contrato

### Pergunta
Redija o conteúdo do prompt `economista_bancario_base.txt` cobrindo:
1. `[ROLE]` Economista revisional bancário
2. `[METODOLOGIA BASE]` Decimal everywhere, Price/SAC, BACEN SGS, IOF, correção monetária
3. `[BACEN SGS REFERENCES]` Tabela canônica códigos por modalidade
4. `[OUTPUT FORMAT]` JSON Pydantic: campos `calculo_decimal`, `bacen_divergencia_pct` (formato "0.XX"), `modalidade_aplicada`, `encargos_revisados`, `valor_revisado` (`Decimal('...')`)
5. `[NOTAS]` Sub-classes anexam modalidade-specific; NUNCA float em finanças

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/economista_bancario_base.txt`
- **Docstring Python:** `bloco_engine/strategies/bancario_base_strategy.py` — método `economista_prompt_section()`

### Resposta
[ ]

---

## Prompt 3 — `validador_bancario_base.txt`

**Bloco:** A — Bancário Base
**Pattern:** BancarioBaseStrategy Template Method
**Estimativa:** ~30min

### Contexto
Validação semântica NLI híbrida per ADR-004 — verifica que tese gerada por advogado/economista respeita citações textuais. Threshold combinado similarity ≥0.7 AND NLI=entailment.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos / técnicos
- **ADR-004:** NLI híbrido (Sentence-BERT similarity + BART-large-mnli entailment)
- **Vault tags:** `bancario_cross` + `cdc_cross` + doctype-specific
- **Anatocismo:** pacto expresso pós-2001 (MP 1.963/2000 → MP 2.170-36/2001)
- **Citação textual:** ≥10 chars obrigatório (não permitir "..." ou abbrev)

### Pergunta
Redija o conteúdo do prompt `validador_bancario_base.txt` cobrindo:
1. `[ROLE]` Validador semântico — NLI híbrido per ADR-004
2. `[METODOLOGIA NLI HÍBRIDA]` Similarity ≥0.7 + NLI=entailment combined threshold
3. `[VALIDAÇÕES BANCÁRIAS]` Citação ≥10 chars, Súmula referida deve existir no vault, anatocismo (pacto expresso vs vedação genérica)
4. `[OUTPUT FORMAT]` JSON: `validation_passed` (bool), `similarity_score` (0.XX), `nli_label` (entailment|neutral|contradiction), `rejected_reasons[]`
5. `[NOTAS]` Sub-classes anexam validações específicas; NLI false-negative aceita tese, false-positive rejeita (conservador)

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/validador_bancario_base.txt`
- **Docstring Python:** `bloco_engine/strategies/bancario_base_strategy.py` — método `validador_prompt_section()`

### Resposta
[ ]

---

## Prompt 4 — `juiz_bancario_base.txt`

**Bloco:** A — Bancário Base
**Pattern:** BancarioBaseStrategy Template Method
**Estimativa:** ~30min

### Contexto
Decisor final C1/C2/C3 thresholds per ADR-003 adaptado BASE bancário (BACEN divergência mais severa). Veredito 3 níveis: REJEITADO / APROVADO_COM_RISCO_HITL / APROVADO_100.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **ADR-003:** Thresholds C1/C2/C3 — 4 personas pipeline
- **BACEN SGS:** divergência taxa contrato vs SGS modalidade
- **Súmula 296 STJ:** taxa acima média BACEN
- **Vinculação obrigatória:** Súmula 539 STJ

### Pergunta
Redija o conteúdo do prompt `juiz_bancario_base.txt` cobrindo:
1. `[ROLE]` Juiz revisional — thresholds C1/C2/C3 adaptados bancário
2. `[CRITÉRIOS C1/C2/C3]` BASE bancário: C1 BACEN divergência (peso 1.00 se ≥0.05; 0.50 se 0.02-0.05; 0.00 se <0.02), C2 vinculação (peso 0.50 se identificada), C3 jurisdição (1.00 TJ aplica Súmulas; 0.50 misto; 0.00 contradição STJ)
3. `[VEREDITO]` Soma C1+C2+C3 ≥2.5 → REJEITADO; 1.0-2.5 → APROVADO_COM_RISCO_HITL (revisão CFOAB); <1.0 → APROVADO_100
4. `[OUTPUT FORMAT]` JSON: `c1_score`, `c2_score`, `c3_score` (todos 0.XX), `veredito` (enum), `aderencia_pct` (0.XX)

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/juiz_bancario_base.txt`
- **Docstring Python:** `bloco_engine/strategies/bancario_base_strategy.py` — método `juiz_prompt_section()`

### Resposta
[ ]

---

# Bloco B.1 — CCB Bancária (4 prompts override doctype_specific_section)

> **Pattern:** Override — anexa após `BancarioBaseStrategy`.
> **Saída por arquivo:** `bloco_workflow/personas/prompts/{persona}_ccb_specific.txt`
> **Doctype consumidor:** CCB Bancária (Cédula de Crédito Bancário).

---

## Prompt 5 — `advogado_ccb_specific.txt`

**Bloco:** B.1 — CCB
**Pattern:** Override `doctype_specific_section()` para CCB
**Estimativa:** ~30min

### Contexto
Override jurídico específico CCB — anatocismo CCB pós-2001, capitalização juros pactuação expressa, venda casada CCB+seguro.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **Lei 10.931/2004** — CCB instrumento e execução extrajudicial
- **Resolução BACEN 4.558/2017** — capitalização CCB
- **Súmulas STJ:** 297 (CDC bancário), 472 (anatocismo CCB pós-2001), 539 (vinculação obrigatória)
- **MP 1.963/2000 → MP 2.170-36/2001** — capitalização pactuação expressa
- **Cross-tag vault:** `ccb` + `bancario_cross` + `cdc_cross`

### Pergunta
Redija o conteúdo do override `advogado_ccb_specific.txt` (anexa ao base) cobrindo:
1. Resolução BACEN 4.558/2017 aplicada CCB
2. Anatocismo CCB — Súmula 472 STJ + pactuação expressa pós-2001
3. Capitalização juros CCB — pacto expresso obrigatório
4. Vinculação CCB+seguro (CDB+Capitalização sem opção rejeição) — venda casada
5. Cross-tag jurisprudência obrigatório

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/advogado_ccb_specific.txt`
- **Strategy class:** `bloco_engine/strategies/ccb_strategy.py` — `CCBStrategy.doctype_specific_section()`

### Resposta
[ ]

---

## Prompt 6 — `economista_ccb_specific.txt`

**Bloco:** B.1 — CCB
**Pattern:** Override doctype_specific_section
**Estimativa:** ~30min

### Contexto
Cálculo específico CCB — modalidade BACEN 217 (CDC veículos PF) ou 218 (CDC outros bens PF), IOF CCB, Price/SAC.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos / financeiros
- **BACEN SGS:** 217 (CDC veículos PF) | 218 (CDC outros bens PF) — Aria valida runtime qual modalidade aplica
- **IOF CCB:** Lei 5.143/1966 + Decreto 6.306/2007 alíquota PF crédito
- **Tabela Price + amortização**

### Pergunta
Redija o conteúdo do override `economista_ccb_specific.txt` cobrindo:
1. Modalidade BACEN 217 ou 218 — critério de escolha (veículo vs outros bens)
2. IOF CCB — alíquota PF, base de cálculo, incidência
3. Cálculo Price/SAC específico CCB

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/economista_ccb_specific.txt`
- **Strategy class:** `bloco_engine/strategies/ccb_strategy.py` — `CCBStrategy.economista_specific()`

### Resposta
[ ]

---

## Prompt 7 — `validador_ccb_specific.txt`

**Bloco:** B.1 — CCB
**Pattern:** Override doctype_specific_section
**Estimativa:** ~30min

### Contexto
NLI específico CCB — validações de venda casada CCB+seguro + verificação Súmulas 297/472/539 citadas corretamente (não inventadas).

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **Súmula 297 STJ** — CDC bancário
- **Súmula 472 STJ** — anatocismo CCB pós-2001
- **Súmula 539 STJ** — vinculação obrigatória

### Pergunta
Redija o conteúdo do override `validador_ccb_specific.txt` cobrindo:
1. NLI específico CCB — venda casada CCB+seguro
2. Validar referência Súmula 297/472/539 não inventada (texto literal Súmula)
3. Outras validações específicas CCB

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/validador_ccb_specific.txt`
- **Strategy class:** `bloco_engine/strategies/ccb_strategy.py` — `CCBStrategy.validador_specific()`

### Resposta
[ ]

---

## Prompt 8 — `juiz_ccb_specific.txt`

**Bloco:** B.1 — CCB
**Pattern:** Override doctype_specific_section
**Estimativa:** ~30min

### Contexto
Juiz CCB — C1 BACEN divergência ≥0.05 stricter (taxa CDC bancário tipicamente próxima média) + C2 vinculação CCB+seguro peso 0.75.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **Súmula 296 STJ** — taxa acima média BACEN
- **Súmula 539 STJ** — vinculação

### Pergunta
Redija o conteúdo do override `juiz_ccb_specific.txt` cobrindo:
1. C1 stricter para CCB — divergência ≥0.05 peso 1.00 (CDC bancário próximo média)
2. C2 vinculação CCB+seguro peso 0.75 se obrigatório
3. C3 jurisdição CCB — manter base

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/juiz_ccb_specific.txt`
- **Strategy class:** `bloco_engine/strategies/ccb_strategy.py` — `CCBStrategy.juiz_specific()`

### Resposta
[ ]

---

# Bloco B.2 — Cartão de Crédito (4 prompts override doctype_specific_section)

> **Pattern:** Override.
> **Saída por arquivo:** `bloco_workflow/personas/prompts/{persona}_cartao_specific.txt`
> **Doctype consumidor:** Cartão de Crédito.

---

## Prompt 9 — `advogado_cartao_specific.txt`

**Bloco:** B.2 — Cartão de Crédito
**Pattern:** Override doctype_specific_section
**Estimativa:** ~30min

### Contexto
Override jurídico Cartão — Súmula 530 STJ venda casada cartão+empréstimo, Resolução BACEN 4.549/2017 rotativo+parcelado, anuidade.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **Súmula 530 STJ** — venda casada cartão+empréstimo
- **Resolução BACEN 4.549/2017** — rotativo + parcelado limite
- **Resolução BACEN 3.919/2010** — transparência tarifária (anuidade)
- **Decreto 6.306/2007** — IOF cartão crédito
- **Cross-tag vault:** `cartao` + `bancario_cross` + `cdc_cross`

### Pergunta
Redija o conteúdo do override `advogado_cartao_specific.txt` cobrindo:
1. Súmula 530 STJ aplicada — venda casada cartão+empréstimo
2. Resolução BACEN 4.549/2017 — rotativo (limite 24 meses parcelamento) + parcelado
3. IOF cartão — alíquota Decreto 6.306/2007
4. Anuidade — Resolução BACEN 3.919/2010 transparência tarifária

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/advogado_cartao_specific.txt`
- **Strategy class:** `bloco_engine/strategies/cartao_strategy.py` — `CartaoStrategy.doctype_specific_section()`

### Resposta
[ ]

---

## Prompt 10 — `economista_cartao_specific.txt`

**Bloco:** B.2 — Cartão de Crédito
**Pattern:** Override doctype_specific_section
**Estimativa:** ~30min

### Contexto
Cálculo Cartão — CDI 4391 (rotativo benchmark) + SELIC 1178 + IOF cartão + encargos rotativo (juros após atraso).

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs financeiros
- **BACEN SGS CDI 4391** — rotativo benchmark
- **SELIC 1178** + IOF cartão
- **Resolução BACEN 4.549/2017** — rotativo limite 24 meses

### Pergunta
Redija o conteúdo do override `economista_cartao_specific.txt` cobrindo:
1. CDI 4391 + SELIC 1178 + IOF cartão — composição
2. Cálculo encargos rotativo (juros após período de atraso)
3. Parcelamento sem juros (transparência fornecedor vs cartão)

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/economista_cartao_specific.txt`
- **Strategy class:** `bloco_engine/strategies/cartao_strategy.py` — `CartaoStrategy.economista_specific()`

### Resposta
[ ]

---

## Prompt 11 — `validador_cartao_specific.txt`

**Bloco:** B.2 — Cartão de Crédito
**Pattern:** Override doctype_specific_section
**Estimativa:** ~30min

### Contexto
NLI cartão — distinguir rotativo vs parcelado vs anuidade + validar Súmula 530 citada corretamente.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **Súmula 530 STJ**
- **Resolução BACEN 4.549/2017**

### Pergunta
Redija o conteúdo do override `validador_cartao_specific.txt` cobrindo:
1. NLI cartão — distinguir rotativo vs parcelado vs anuidade (semântica diferente)
2. Validar Súmula 530 STJ citada corretamente (texto literal)
3. Outras validações cartão (transparência tarifária)

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/validador_cartao_specific.txt`
- **Strategy class:** `bloco_engine/strategies/cartao_strategy.py` — `CartaoStrategy.validador_specific()`

### Resposta
[ ]

---

## Prompt 12 — `juiz_cartao_specific.txt`

**Bloco:** B.2 — Cartão de Crédito
**Pattern:** Override doctype_specific_section
**Estimativa:** ~30min

### Contexto
Juiz Cartão — C2 vinculação ≤0.4 (cartão tem vinculação alta legítima — bandeiras + emissor) + C1 divergência rotativo vs CDI threshold flexível.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **Súmula 530 STJ**
- **Resolução BACEN 4.549/2017**

### Pergunta
Redija o conteúdo do override `juiz_cartao_specific.txt` cobrindo:
1. C2 vinculação cartão peso ≤0.4 (vinculação bandeiras + emissor é legítima)
2. C1 divergência rotativo vs CDI 4391 — threshold mais flexível (rotativo é variável BACEN, não fixo)
3. C3 jurisdição cartão — manter base

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/juiz_cartao_specific.txt`
- **Strategy class:** `bloco_engine/strategies/cartao_strategy.py` — `CartaoStrategy.juiz_specific()`

### Resposta
[ ]

---

# Bloco B.3 — Consignado (4 prompts override doctype_specific_section)

> **Pattern:** Override.
> **Saída por arquivo:** `bloco_workflow/personas/prompts/{persona}_consignado_specific.txt`
> **Doctype consumidor:** Consignado (servidor público + privado + militar + INSS).

---

## Prompt 13 — `advogado_consignado_specific.txt`

**Bloco:** B.3 — Consignado
**Pattern:** Override doctype_specific_section
**Estimativa:** ~30min

### Contexto
Override jurídico Consignado — Lei 10.820/2003 servidor público + privado, cap 35% margem consignável (**Decreto 11.150/2022 ou atualização — verificar oficial**, NÃO Decreto 8.690/2016 que Smith review 2026-05-12 suspeitou incorreto), Súmula 603 STJ (verificar interpretação 2018).

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **Lei 10.820/2003** — consignado servidor público + privado
- **Decreto regulamentar cap 35% margem consignável** — verificar oficial em [planalto.gov.br](http://www.planalto.gov.br) — provavelmente **Decreto 11.150/2022** ou atualização posterior (NÃO Decreto 8.690/2016 — Smith review 2026-05-12 suspeitou número incorreto; provavelmente PNAATA Programa Nacional Captação Água Chuva)
- **Súmula 603 STJ** — consignado margem (verificar interpretação 2018 EREsp 1.555.722)
- **Lei 8.213/91** — Previdência (consignado INSS)
- **Estatutos militares** — particularidades
- **Cross-tag vault:** `consignado` + `bancario_cross` + `cdc_cross`

### Pergunta
Redija o conteúdo do override `advogado_consignado_specific.txt` cobrindo:
1. Lei 10.820/2003 — escopo (servidor público + privado + INSS + militar)
2. Cap 35% margem consignável — **Decreto 11.150/2022 ou atualização posterior** (verificar oficial em [planalto.gov.br](http://www.planalto.gov.br); NÃO Decreto 8.690/2016 que Smith review 2026-05-12 suspeitou incorreto)
3. Súmula 603 STJ — extrapolação margem
4. Distinções INSS / militar / servidor (Lei 8.213/91 + estatutos)

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/advogado_consignado_specific.txt`
- **Strategy class:** `bloco_engine/strategies/consignado_strategy.py` — `ConsignadoStrategy.doctype_specific_section()`

### Resposta
[ ]

---

## Prompt 14 — `economista_consignado_specific.txt`

**Bloco:** B.3 — Consignado
**Pattern:** Override doctype_specific_section
**Estimativa:** ~30min

### Contexto
Cálculo Consignado — modalidade BACEN 419 (privado) ou 432 (público), cálculo margem 35% líquido folha, composição taxa.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs financeiros
- **BACEN SGS 419** (consignado privado) | **432** (consignado público) — distinção relevante taxa média
- **Decreto regulamentar margem consignável** — verificar oficial (provavelmente **Decreto 11.150/2022** ou atualização posterior; NÃO Decreto 8.690/2016 que Smith review 2026-05-12 suspeitou incorreto — provavelmente PNAATA Programa Nacional Captação Água Chuva)
- **IOF consignado**

### Pergunta
Redija o conteúdo do override `economista_consignado_specific.txt` cobrindo:
1. Modalidade BACEN 419 vs 432 — critério escolha
2. Cálculo margem consignável (35% líquido folha — definição "líquido")
3. Composição taxa consignado: principal + juros + IOF

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/economista_consignado_specific.txt`
- **Strategy class:** `bloco_engine/strategies/consignado_strategy.py` — `ConsignadoStrategy.economista_specific()`

### Resposta
[ ]

---

## Prompt 15 — `validador_consignado_specific.txt`

**Bloco:** B.3 — Consignado
**Pattern:** Override doctype_specific_section
**Estimativa:** ~30min

### Contexto
NLI consignado — margem extrapolada (>35%), taxa abusiva (>3x média BACEN), validar Lei 10.820 Art. 6º cap.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **Lei 10.820/2003** — Art. 6º cap
- **Súmula 603 STJ**

### Pergunta
Redija o conteúdo do override `validador_consignado_specific.txt` cobrindo:
1. NLI consignado — margem >35% (extrapolada)
2. Taxa abusiva >3x média BACEN
3. Validar Lei 10.820 Art. 6º citado corretamente (texto literal)

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/validador_consignado_specific.txt`
- **Strategy class:** `bloco_engine/strategies/consignado_strategy.py` — `ConsignadoStrategy.validador_specific()`

### Resposta
[ ]

---

## Prompt 16 — `juiz_consignado_specific.txt`

**Bloco:** B.3 — Consignado
**Pattern:** Override doctype_specific_section
**Estimativa:** ~30min

### Contexto
Juiz Consignado — C3 jurisdição cap (Lei 10.820 federal — TR estadual menor relevância) + C2 vinculação peso menor (consignado por natureza vinculado folha).

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **Lei 10.820/2003** — federal (TR estadual menor peso C3)
- **Súmula 603 STJ**

### Pergunta
Redija o conteúdo do override `juiz_consignado_specific.txt` cobrindo:
1. C3 jurisdição consignado — Lei 10.820 federal (TJ estadual menor relevância)
2. C2 vinculação consignado peso menor (vinculação folha é natureza, não abuso isolado)
3. C1 divergência consignado — manter base

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/juiz_consignado_specific.txt`
- **Strategy class:** `bloco_engine/strategies/consignado_strategy.py` — `ConsignadoStrategy.juiz_specific()`

### Resposta
[ ]

---

# Bloco C — Geral Standalone (4 prompts catch-all Tier 3)

> **Pattern:** Catch-all Tier 3 per ADR-020 — processa contratos atípicos via prompts genéricos + cross-tag vault.
> **Saída por arquivo:** `bloco_workflow/personas/prompts/{persona}_geral.txt`
> **Doctype consumidor:** Geral (catch-all — empréstimo pessoal não-consignado, contratos comerciais atípicos, leasing financeiro fora do escopo CCB/Veículo/Imobiliário/FIES/Cartão/Consignado).
>
> **NOTA F-D3-MED-02 (Smith fix):** FIES tem doctype standalone próprio em **Bloco F** — NÃO é catch-all Geral. Smith review 2026-05-12 detectou confusão conceitual original (FIES tem regramento próprio Lei 10.260/2001).

---

## Prompt 17 — `advogado_geral.txt`

**Bloco:** C — Geral
**Pattern:** Catch-all Tier 3 (standalone, sem BancarioBaseStrategy)
**Estimativa:** ~20min (genérico, escopo menor)

### Contexto
Catch-all Tier 3 — adaptabilidade contratos atípicos via CDC base + cross-doctype principles. Sem doctype-specific scope (genérico). NOTA: FIES NÃO faz parte do Geral — tem doctype standalone próprio em Bloco F.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **CDC Lei 8.078/1990** — base (Art. 51 cláusulas abusivas, Art. 6º direitos básicos)
- **Cross-tag vault:** `geral` + `cross` (sem doctype-specific scope)

### Pergunta
Redija o conteúdo do prompt `advogado_geral.txt` cobrindo:
1. `[ROLE]` Advogado revisional generalista — contratos atípicos
2. `[FUNDAMENTAÇÃO BASE]` CDC Lei 8.078/1990 (Art. 51 + Art. 6º + Art. 39 práticas abusivas)
3. Adaptabilidade contratos atípicos (empréstimo pessoal não-consignado, contratos comerciais atípicos, leasing financeiro fora do escopo CCB/Veículo/Imobiliário/FIES/Cartão/Consignado)
4. Cross-tag jurisprudência: `geral` + `cross`
5. `[OUTPUT FORMAT]` JSON padrão (mesmo schema base)

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/advogado_geral.txt`
- **Strategy class:** `bloco_engine/strategies/geral_dispatcher.py` — `GeralDispatcher` catch-all

### Resposta
[ ]

---

## Prompt 18 — `economista_geral.txt`

**Bloco:** C — Geral
**Pattern:** Catch-all Tier 3
**Estimativa:** ~20min

### Contexto
Cálculo genérico — SELIC 1178 + IPCA 433 + cálculos universais, sem modalidade BACEN específica.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs financeiros
- **BACEN SGS SELIC 1178** + **IPCA 433** (genéricos)
- Sem modalidade CDC específica (catch-all)

### Pergunta
Redija o conteúdo do prompt `economista_geral.txt` cobrindo:
1. Cálculo financeiro genérico (Decimal everywhere mantido)
2. SELIC 1178 + IPCA 433 — referências genéricas (sem modalidade específica)
3. Adaptabilidade a contratos atípicos

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/economista_geral.txt`
- **Strategy class:** `bloco_engine/strategies/geral_dispatcher.py` — `GeralDispatcher.economista_section()`

### Resposta
[ ]

---

## Prompt 19 — `validador_geral.txt`

**Bloco:** C — Geral
**Pattern:** Catch-all Tier 3
**Estimativa:** ~20min

### Contexto
NLI híbrido genérico — sem doctype-specific cues, confia em base CDC.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **CDC Lei 8.078/1990** — base
- **ADR-004** NLI híbrido

### Pergunta
Redija o conteúdo do prompt `validador_geral.txt` cobrindo:
1. NLI híbrido genérico (sem doctype-specific)
2. Validações CDC base (citação ≥10 chars, Súmula existente)
3. Adaptabilidade contratos atípicos

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/validador_geral.txt`
- **Strategy class:** `bloco_engine/strategies/geral_dispatcher.py` — `GeralDispatcher.validador_section()`

### Resposta
[ ]

---

## Prompt 20 — `juiz_geral.txt`

**Bloco:** C — Geral
**Pattern:** Catch-all Tier 3
**Estimativa:** ~20min

### Contexto
Thresholds C1/C2/C3 medianos (sem stricter doctype-specific) — Geral cobre contratos atípicos onde benchmark BACEN específico não aplica.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **ADR-003** thresholds C1/C2/C3
- **CDC base** Lei 8.078/1990

### Pergunta
Redija o conteúdo do prompt `juiz_geral.txt` cobrindo:
1. C1 divergência genérica — threshold flexível ~0.10 (sem benchmark BACEN específico)
2. C2 vinculação genérica — peso 0.50 base
3. C3 jurisdição CDC federal — peso 1.00 base
4. Veredito padrão (REJEITADO / APROVADO_COM_RISCO_HITL / APROVADO_100)

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/juiz_geral.txt`
- **Strategy class:** `bloco_engine/strategies/geral_dispatcher.py` — `GeralDispatcher.juiz_section()`

### Resposta
[ ]

---

# Bloco D — Veículo Standalone (4 prompts)

> **Pattern:** Standalone — sem BancarioBaseStrategy. CDC Veicular tem regramento específico Decreto-Lei 911/1969 + busca apreensão.
> **Saída por arquivo:** `bloco_workflow/personas/prompts/{persona}_veiculo.txt`
> **Doctype consumidor:** Veículo (CDC Veicular financiamento PF).

---

## Prompt 21 — `advogado_veiculo.txt`

**Bloco:** D — Veículo
**Pattern:** Standalone (sem BancarioBaseStrategy)
**Estimativa:** ~30min

### Contexto
Fundamentação jurídica Veículo — CDC Veicular financiamento PF + Decreto-Lei 911/1969 (busca apreensão extrajudicial) + cláusulas abusivas comuns (vinculação seguro DPVAT vs facultativo).

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **CDC:** Lei 8.078/1990 — Art. 51 cláusulas abusivas + Art. 39 práticas abusivas
- **Decreto-Lei 911/1969** — busca e apreensão veicular (procedimento extrajudicial — alienação fiduciária)
- **Súmula 369 STJ** — verificar texto literal (provavelmente notificação extrajudicial mora veicular)
- **Lei 10.931/2004** — instrumento alienação fiduciária imóveis/veículos (verificar aplicabilidade veicular)
- **Cross-tag vault:** `veiculo` + `cdc_cross`

### Pergunta
Redija o conteúdo do prompt `advogado_veiculo.txt` cobrindo:
1. `[ROLE]` Advogado revisional Veicular
2. `[FUNDAMENTAÇÃO]` CDC Veicular + Decreto-Lei 911/1969 + Súmula 369 STJ verificada
3. `[CLÁUSULAS ABUSIVAS COMUNS VEICULAR]` Vinculação seguro DPVAT vs facultativo / busca apreensão sem notificação prévia / vendor lock-in seguradora / antecipação parcelas sem desconto
4. `[OUTPUT FORMAT]` JSON Pydantic strict (mesmo schema base personas)
5. `[NOTAS]` Cross-refs vault + anti-padrões + dont-invent

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/advogado_veiculo.txt`
- **Strategy class:** `bloco_engine/strategies/veiculo_strategy.py` — `VeiculoStrategy.advogado_prompt()`

### Resposta
[ ]

---

## Prompt 22 — `economista_veiculo.txt`

**Bloco:** D — Veículo
**Pattern:** Standalone
**Estimativa:** ~30min

### Contexto
Cálculo Veicular — Modalidade BACEN 217 (CDC veículos PF) + IOF veicular + IPVA encargos accessórios.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs financeiros
- **BACEN SGS Modalidade 217** — CDC veículos PF (verificar código atualizado em [bcb.gov.br/sgspub](https://www.bcb.gov.br/sgspub))
- **IOF veicular:** Lei 5.143/1966 + Decreto 6.306/2007 alíquota PF crédito veicular
- **IPVA encargos accessórios** — verificar legislação estadual aplicável
- **Tabela Price + amortização veicular** com prazos típicos 36-60 meses

### Pergunta
Redija o conteúdo do prompt `economista_veiculo.txt` cobrindo:
1. `[ROLE]` Economista revisional Veicular
2. `[METODOLOGIA]` Decimal everywhere + Modalidade 217 + IOF + IPVA accessório
3. Cálculo Price/SAC Veicular típico (36-60 meses, PF crédito direto consumidor)
4. `[OUTPUT FORMAT]` JSON Pydantic: `bacen_217_divergencia_pct`, `iof_veicular_decimal`, `valor_revisado` Decimal
5. `[NOTAS]` NUNCA float em finanças (FR-CALC-01)

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/economista_veiculo.txt`
- **Strategy class:** `bloco_engine/strategies/veiculo_strategy.py` — `VeiculoStrategy.economista_prompt()`

### Resposta
[ ]

---

## Prompt 23 — `validador_veiculo.txt`

**Bloco:** D — Veículo
**Pattern:** Standalone
**Estimativa:** ~30min

### Contexto
NLI veicular específico — busca apreensão extrajudicial sem notificação válida, repactuação automática sem opt-in, depósito judicial valor controverso.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **Decreto-Lei 911/1969** — notificação extrajudicial mora veicular
- **Súmula 369 STJ** (verificar texto literal)
- **ADR-004** NLI híbrido (similarity ≥0.7 + entailment)

### Pergunta
Redija o conteúdo do prompt `validador_veiculo.txt` cobrindo:
1. `[ROLE]` Validador semântico Veicular
2. NLI veicular — busca apreensão sem notificação prévia (Súmula 369 STJ pacto expresso vs presunção)
3. Validar repactuação opt-in vs cobrança automática
4. Validar depósito judicial valor controverso
5. `[OUTPUT FORMAT]` JSON: `validation_passed`, `similarity_score`, `nli_label`, `rejected_reasons[]`

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/validador_veiculo.txt`
- **Strategy class:** `bloco_engine/strategies/veiculo_strategy.py` — `VeiculoStrategy.validador_prompt()`

### Resposta
[ ]

---

## Prompt 24 — `juiz_veiculo.txt`

**Bloco:** D — Veículo
**Pattern:** Standalone
**Estimativa:** ~30min

### Contexto
Juiz Veicular — C1 BACEN 217 divergência + C2 vinculação seguro DPVAT obrigatório (peso 0.0) vs facultativo (peso 0.75) + C3 jurisdição TJ veicular.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **ADR-003** thresholds C1/C2/C3
- **Súmula 369 STJ** (notificação mora veicular)
- **Decreto-Lei 911/1969**

### Pergunta
Redija o conteúdo do prompt `juiz_veiculo.txt` cobrindo:
1. `[ROLE]` Juiz revisional Veicular — thresholds C1/C2/C3
2. C1 BACEN 217 divergência (peso 1.00 se ≥0.05; 0.50 se 0.02-0.05; 0.00 se <0.02)
3. C2 vinculação seguro Veicular — DPVAT obrigatório peso 0.0 (legal); facultativo peso 0.75 se vinculado financiamento
4. C3 jurisdição TJ veicular (1.00 se TJ aplica Súmula 369 STJ; 0.50 se misto)
5. `[OUTPUT FORMAT]` JSON: `c1_score`, `c2_score`, `c3_score`, `veredito`, `aderencia_pct`

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/juiz_veiculo.txt`
- **Strategy class:** `bloco_engine/strategies/veiculo_strategy.py` — `VeiculoStrategy.juiz_prompt()`

### Resposta
[ ]

---

# Bloco E — Imobiliário SFH/SFI Standalone (4 prompts)

> **Pattern:** Standalone — Sistema Hipotecário SFH (Sistema Financeiro Habitação) + SFI (Sistema Financeiro Imobiliário).
> **Saída por arquivo:** `bloco_workflow/personas/prompts/{persona}_imobiliario.txt`
> **Doctype consumidor:** Imobiliário (SFH + SFI + Minha Casa Minha Vida).

---

## Prompt 25 — `advogado_imobiliario.txt`

**Bloco:** E — Imobiliário SFH/SFI
**Pattern:** Standalone
**Estimativa:** ~30min

### Contexto
Fundamentação Imobiliário — Lei 11.977/2009 (Minha Casa Minha Vida) + Súmula 322 STJ (BACEN não aplicável SFH + sistemas privados — verificar texto literal) + Sistema Hipotecário SFH vs SFI distinção.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **CDC:** Lei 8.078/1990 — Art. 51 cláusulas abusivas
- **Lei 11.977/2009** — Programa Minha Casa Minha Vida
- **Lei 4.380/1964** — SFH Sistema Financeiro Habitação
- **Lei 9.514/1997** — SFI Sistema Financeiro Imobiliário (alienação fiduciária imóvel)
- **Súmula 322 STJ** — atribuição "BACEN não aplicável SFH" SUSPECT (Smith review) — verificar texto literal oficial
- **Cross-tag vault:** `imobiliario` + `cdc_cross` + `cdc_imovel`

### Pergunta
Redija o conteúdo do prompt `advogado_imobiliario.txt` cobrindo:
1. `[ROLE]` Advogado revisional Imobiliário SFH/SFI
2. `[FUNDAMENTAÇÃO]` Lei 4.380/1964 SFH + Lei 9.514/1997 SFI + Lei 11.977/2009 MCMV + CDC + Súmula 322 STJ (verificar)
3. `[CLÁUSULAS ABUSIVAS COMUNS IMOBILIÁRIO]` Atualização TR vs IPCA contra contrato / cláusula crédito rotativo embutida / fiança bancária obrigatória / vinculação seguro MIP+DFI / amortização Price contra SAC quando contratado SAC
4. Distinção SFH (regulamentado BACEN/governo) vs SFI (privado liberdade contratual)
5. `[OUTPUT FORMAT]` JSON Pydantic strict

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/advogado_imobiliario.txt`
- **Strategy class:** `bloco_engine/strategies/imobiliario_strategy.py` — `ImobiliarioStrategy.advogado_prompt()`

### Resposta
[ ]

---

## Prompt 26 — `economista_imobiliario.txt`

**Bloco:** E — Imobiliário SFH/SFI
**Pattern:** Standalone
**Estimativa:** ~30min

### Contexto
Cálculo Imobiliário — Resolução BACEN regulamentar SFH/SFI (verificar número atual; provavelmente 4.196/2013 ou atualização) + TR/IPCA/INCC correção + sistema Price/SAC Imobiliário.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs financeiros
- **Resolução BACEN regulamentar SFH/SFI** — verificar número oficial atual em [bcb.gov.br/estabilidadefinanceira/buscanormas](https://www.bcb.gov.br/estabilidadefinanceira/buscanormas) (provavelmente 4.196/2013 ou atualização posterior)
- **TR** (Taxa Referencial) BACEN — atualização SFH típica
- **IPCA** (Índice Preços Consumidor Amplo) — alternativa SFI
- **INCC** (Índice Nacional Construção Civil) — pré-chaves
- **Tabela Price + SAC** — distinção crítica Imobiliário (prazo 240-420 meses)

### Pergunta
Redija o conteúdo do prompt `economista_imobiliario.txt` cobrindo:
1. `[ROLE]` Economista revisional Imobiliário
2. `[METODOLOGIA]` Decimal everywhere + Price/SAC + TR/IPCA/INCC correção
3. Cálculo Imobiliário SFH (prazo 240-360 meses Price) vs SFI (240-420 meses, flexível)
4. Verificar correção TR vs IPCA conforme contrato (INDEXAÇÃO STAGE-DEPENDENTE: INCC pré-chaves, IPCA/TR pós-chaves)
5. `[OUTPUT FORMAT]` JSON Pydantic com `bacen_imob_divergencia_pct`, `correcao_aplicada` enum, `valor_revisado` Decimal

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/economista_imobiliario.txt`
- **Strategy class:** `bloco_engine/strategies/imobiliario_strategy.py` — `ImobiliarioStrategy.economista_prompt()`

### Resposta
[ ]

---

## Prompt 27 — `validador_imobiliario.txt`

**Bloco:** E — Imobiliário SFH/SFI
**Pattern:** Standalone
**Estimativa:** ~30min

### Contexto
NLI imobiliário específico — atualização TR vs IPCA contra contrato, cláusula crédito rotativo embutida, fiança bancária obrigatória.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **ADR-004** NLI híbrido
- **Súmula 322 STJ** (verificar texto literal)
- **Lei 9.514/1997** SFI

### Pergunta
Redija o conteúdo do prompt `validador_imobiliario.txt` cobrindo:
1. `[ROLE]` Validador semântico Imobiliário
2. NLI imobiliário — TR vs IPCA correção (verificar contrato literal vs aplicado), cláusula crédito rotativo embutida em parcelas, fiança bancária obrigatória
3. Validar Súmula 322 STJ citada corretamente texto literal
4. `[OUTPUT FORMAT]` JSON: `validation_passed`, `similarity_score`, `nli_label`, `rejected_reasons[]`

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/validador_imobiliario.txt`
- **Strategy class:** `bloco_engine/strategies/imobiliario_strategy.py` — `ImobiliarioStrategy.validador_prompt()`

### Resposta
[ ]

---

## Prompt 28 — `juiz_imobiliario.txt`

**Bloco:** E — Imobiliário SFH/SFI
**Pattern:** Standalone
**Estimativa:** ~30min

### Contexto
Juiz Imobiliário — C1 BACEN regulamentar SFH/SFI divergência + C2 vinculação seguro habitacional (MIP+DFI obrigatórios SFH peso 0.0; vinculação seguradora específica peso 0.75) + C3 jurisdição SFH federal vs SFI estadual.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **ADR-003** thresholds C1/C2/C3
- **Súmula 322 STJ** (verificar)
- **Lei 4.380/1964 SFH** + **Lei 9.514/1997 SFI**

### Pergunta
Redija o conteúdo do prompt `juiz_imobiliario.txt` cobrindo:
1. `[ROLE]` Juiz revisional Imobiliário — thresholds C1/C2/C3
2. C1 BACEN regulamentar SFH/SFI divergência (peso 1.00 se ≥0.05; 0.50 se 0.02-0.05)
3. C2 vinculação seguro MIP+DFI obrigatório peso 0.0; seguradora específica peso 0.75
4. C3 jurisdição SFH (federal) vs SFI (estadual) — peso 1.00 se TJ aplica Súmula 322 STJ
5. `[OUTPUT FORMAT]` JSON Pydantic

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/juiz_imobiliario.txt`
- **Strategy class:** `bloco_engine/strategies/imobiliario_strategy.py` — `ImobiliarioStrategy.juiz_prompt()`

### Resposta
[ ]

---

# Bloco F — FIES Standalone (4 prompts)

> **Pattern:** Standalone — Lei 10.260/2001 + Lei 12.202/2010 (alterações Pronatec) + Lei 12.087/2009 (FGEDUC fundo garantidor educacional) + MEC normativos.
> **Saída por arquivo:** `bloco_workflow/personas/prompts/{persona}_fies.txt`
> **Doctype consumidor:** FIES (Fundo Financiamento Estudantil) — incluindo PMF (Programa de Financiamento Estudantil).

---

## Prompt 29 — `advogado_fies.txt`

**Bloco:** F — FIES
**Pattern:** Standalone
**Estimativa:** ~30min

### Contexto
Fundamentação FIES — Lei 10.260/2001 (FIES original) + Lei 12.202/2010 (alterações Pronatec) + Lei 12.087/2009 (FGEDUC fundo garantidor) + MEC normativos vigentes.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **CDC:** Lei 8.078/1990 (aplicabilidade contratos educacionais — verificar jurisprudência)
- **Lei 10.260/2001** — FIES original
- **Lei 12.202/2010** — alterações FIES Pronatec
- **Lei 12.087/2009** — FGEDUC Fundo Garantidor Educacional
- **MEC Portarias normativas vigentes** — taxa de juros subsidiada + critérios elegibilidade — verificar mais recentes em [mec.gov.br](https://www.mec.gov.br)
- **Cross-tag vault:** `fies` + `cdc_educacional`

### Pergunta
Redija o conteúdo do prompt `advogado_fies.txt` cobrindo:
1. `[ROLE]` Advogado revisional FIES
2. `[FUNDAMENTAÇÃO]` Lei 10.260/2001 + 12.202/2010 + 12.087/2009 + MEC normativos
3. `[CLÁUSULAS ABUSIVAS COMUNS FIES]` Fiador solidário vs FGEDUC (não-vinculação obrigatória) / cobertura inadimplência insuficiente / vinculação curso autorizado MEC / juros pós-fase amortização acima taxa MEC oficial
4. CDC aplicável FIES (verificar jurisprudência STJ — relação consumidor vs financiamento público federal)
5. `[OUTPUT FORMAT]` JSON Pydantic strict

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/advogado_fies.txt`
- **Strategy class:** `bloco_engine/strategies/fies_strategy.py` — `FIESStrategy.advogado_prompt()`

### Resposta
[ ]

---

## Prompt 30 — `economista_fies.txt`

**Bloco:** F — FIES
**Pattern:** Standalone
**Estimativa:** ~30min

### Contexto
Cálculo FIES — Taxa juros subsidiada MEC (verificar Portaria MEC vigente — historicamente 3,4% a.a., pode ter sido reduzida ou indexada) + correção SEM TR/IPCA durante carência + fase amortização própria.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs financeiros
- **Taxa de juros FIES** — verificar Portaria MEC vigente (taxa subsidiada historicamente 3,4% a.a.; verificar atualizações)
- **Carência:** 18 meses pós-conclusão curso (verificar Lei 10.260/2001 + MEC)
- **Fase amortização:** própria (sem TR/IPCA durante grade period)
- **FGEDUC** — Lei 12.087/2009 alíquota retenção sobre desembolso
- **IOF FIES** — verificar se aplicável (financiamento público pode ter isenção)

### Pergunta
Redija o conteúdo do prompt `economista_fies.txt` cobrindo:
1. `[ROLE]` Economista revisional FIES
2. `[METODOLOGIA]` Decimal everywhere + taxa subsidiada MEC + carência 18 meses + amortização própria
3. Cálculo FIES por fase: (a) curso (apenas FGEDUC) / (b) carência 18 meses (juros sem amortização) / (c) amortização (parcelas)
4. Verificar taxa contratada vs taxa MEC oficial — divergência sinaliza cobrança indevida
5. `[OUTPUT FORMAT]` JSON: `taxa_mec_oficial_pct`, `taxa_contratada_pct`, `divergencia_pct`, `fase_calculo` enum, `valor_revisado` Decimal

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/economista_fies.txt`
- **Strategy class:** `bloco_engine/strategies/fies_strategy.py` — `FIESStrategy.economista_prompt()`

### Resposta
[ ]

---

## Prompt 31 — `validador_fies.txt`

**Bloco:** F — FIES
**Pattern:** Standalone
**Estimativa:** ~30min

### Contexto
NLI FIES — fiador solidário vs FGEDUC (não-cumulável), vinculação curso autorizado MEC, cobertura inadimplência FGEDUC vs cobrança particular.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **ADR-004** NLI híbrido
- **Lei 12.087/2009** FGEDUC
- **Lei 10.260/2001** FIES + Lei 12.202/2010

### Pergunta
Redija o conteúdo do prompt `validador_fies.txt` cobrindo:
1. `[ROLE]` Validador semântico FIES
2. NLI FIES — fiador solidário vs FGEDUC (não pode ser cumulado), vinculação curso autorizado MEC, cobertura inadimplência FGEDUC vs cobrança particular
3. Validar Portaria MEC citada corretamente (verificar vigência)
4. `[OUTPUT FORMAT]` JSON: `validation_passed`, `similarity_score`, `nli_label`, `rejected_reasons[]`

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/validador_fies.txt`
- **Strategy class:** `bloco_engine/strategies/fies_strategy.py` — `FIESStrategy.validador_prompt()`

### Resposta
[ ]

---

## Prompt 32 — `juiz_fies.txt`

**Bloco:** F — FIES
**Pattern:** Standalone
**Estimativa:** ~30min

### Contexto
Juiz FIES — C1 taxa contratada vs taxa MEC oficial divergência + C2 vinculação fiador/FGEDUC peso 0.50 (FGEDUC é fundo público garantidor, fiador cumulado é abusivo) + C3 jurisdição educacional federal.

> ⚠️ **Verifique cada Súmula/Resolução/Decreto citado abaixo em fonte oficial ANTES de aceitar atribuição.** Smith review 2026-05-12 detectou suspeita de mis-attribution — atribuições são SUGESTÕES INICIAIS, não verdades canônicas (ver WARNING CRÍTICO no topo do brief).

### Cross-refs jurídicos
- **ADR-003** thresholds C1/C2/C3
- **Lei 10.260/2001** FIES
- **Lei 12.087/2009** FGEDUC
- **MEC Portarias** taxa oficial

### Pergunta
Redija o conteúdo do prompt `juiz_fies.txt` cobrindo:
1. `[ROLE]` Juiz revisional FIES — thresholds C1/C2/C3
2. C1 taxa contratada vs taxa MEC oficial (peso 1.00 se divergência ≥0.005 absolute pct points — taxa subsidiada baixa torna divergência relativamente alta)
3. C2 vinculação fiador/FGEDUC — peso 0.50 se cumulado (FGEDUC + fiador particular é abusivo); peso 0.0 se apenas FGEDUC; peso 0.75 se apenas fiador (sem oferta FGEDUC mesmo elegível)
4. C3 jurisdição educacional federal — peso 1.00 se TRF aplica Lei 10.260/2001 + MEC; 0.50 se misto estadual
5. `[OUTPUT FORMAT]` JSON Pydantic

### Onde será inserido
- **Arquivo `.txt`:** `bloco_workflow/personas/prompts/juiz_fies.txt`
- **Strategy class:** `bloco_engine/strategies/fies_strategy.py` — `FIESStrategy.juiz_prompt()`

### Resposta
[ ]

---

# Pós-preenchimento — Checklist final

Após preencher as 32 respostas, antes de devolver a Morgan/Neo:

- [ ] **Súmulas verificadas** em [stj.jus.br](https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/Sumulas.aspx) (não inventadas)
- [ ] **Resoluções BACEN verificadas** em [bcb.gov.br/estabilidadefinanceira](https://www.bcb.gov.br/estabilidadefinanceira/buscanormas) (números corretos)
- [ ] **Leis citadas com data + alteração mais recente** (ex: Lei 10.820/2003 atualizada por **Decreto 11.150/2022** ou atualização posterior — verificar oficial)
- [ ] **Cross-tag vault** consistente entre Blocos (`bancario_cross`, `cdc_cross`, doctype-specific)
- [ ] **Output format JSON** mantém schema Pydantic strict `extra='forbid'` (mesma estrutura entre personas)
- [ ] **Anti-padrões evitados:** zero invenções, zero float financeiro, zero confusão lei federal vs estadual

# Próximo passo após Done

1. Devolver este arquivo preenchido a Morgan (via commit em `governance/prd/BRIEF-EXECUTAVEL-ADVOGADO.md`)
2. Morgan absorve respostas, gera 20 `.txt` em `bloco_workflow/personas/prompts/`
3. Neo SP04-DOCTYPE-01 chunks 5-6 integra prompts ao backend Strategy
4. Smith Sprint 04 close-out review ANPD-defensável dos prompts finalizados

---

*Brief executável criado por Morgan 2026-05-12 derivado de PRD v2.0.4 Section 2 + Smith CRITICAL fixes + Smith Round 2 cleanup. Pattern AUTH-01 chunk 5 placeholder + finalização advogado(a). 32 prompts (4 base bancário DRY + 12 sub-bancários + 4 Geral catch-all + 4 Veículo + 4 Imobiliário + 4 FIES = full coverage ADR-020 7 doctypes). ~18h cumulativo (16h prompts + 2h smoke test) Day 1-5.*

— Morgan, planejando o futuro 📊
