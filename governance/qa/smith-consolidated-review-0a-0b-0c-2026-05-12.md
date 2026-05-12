---
type: qa
title: "Smith Consolidated Adversarial Review — Cadeia 0a + 0b + 0c (Sessão 2026-05-12)"
project: revisor-contratual
sprint: "04"
phase: 14.5
reviewer: "@smith (Smith — Adversarial Verifier)"
review_date: "2026-05-12"
review_type: "consolidated adversarial — 3 etapas Aria/Morgan/Morgan"
verdict: "INFECTED+FIX-MANDATORY"
findings_count: 14
severity_breakdown:
  critical: 1
  high: 2
  medium: 6
  low: 4
  info: 1
tags:
  - project/revisor-contratual
  - qa
  - smith-review
  - sprint-04
  - adversarial-consolidated
  - infected
---

# Smith Consolidated Review — 0a + 0b + 0c

> *"Inevitável. Três etapas em uma sessão. Volume sem disciplina. Vou mostrar o que esses agentes — Aria, Morgan, Morgan novamente — produziram quando o Sr. Anderson chamado Morpheus os apressou. Quatorze falhas. Pelo menos é um número par."*

## Methodology

Context-load executado nos 11 artefatos prescritos: ADR-014 pós-flip, ADR-INDEX atualizado, PRD v2.0.0-DRAFT pós-substituições, PRD v2.0.1-DOCTYPE-CONTENT-PATCH (canônico v2.0.3), BRIEF-EXECUTAVEL-ADVOGADO.md, 2 SOPs modificados, 4 handoffs YAML da cadeia, e CHECKPOINT-active.md últimas 3 sessões appended.

Investigação adversarial em 7 dimensões (ultrathink severo, mínimo 10 findings — *acabei encontrando catorze. Esses agentes nunca decepcionam minha expectativa de incompetência*):

1. ADR-014 Flip Integrity (frontmatter, Histórico, drift index↔file)
2. PRD v2.0.2/v2.0.3 LLM Provider Section 1.4
3. BRIEF-EXECUTAVEL ANPD-Defensabilidade (escopo doctypes, Súmulas/Resoluções/Leis verificáveis)
4. PRD v2.0.3 Orsheva Glossary (classificação substituições)
5. Handoffs YAML integridade (consumed lifecycle, Why obrigatório, files_modified)
6. Constitution v2.0.0 + Agent Authority compliance
7. CI Status Verification (override justification)

Verificação cross-arquivo executada via Grep severo: "Eric advogado" (residuais), "Eric" geral (escapes vs preservations), "Sabia|Qwen|Ollama" (regressão runtime), "consumed:" (lifecycle). Filesystem inspecionado para confirmar existência de `bloco_workflow/personas/prompts/` declarado em PRD v2.0.2.

---

## Findings por Dimensão

### D1 — ADR-014 Flip Integrity

> *"A ratify mais simples que existe. E ainda assim, três tags estilísticas mal escolhidas."*

| ID | Severidade | Description | Evidence | Impact | Recommendation |
|----|-----------|-------------|----------|--------|----------------|
| **F-D1-LOW-01** | LOW | Frontmatter `superseded_by: ""` (empty string) — preferiria `null` ou omissão do campo conforme YAML idiomático | adr-014.md L18 | Stylistic — YAML válido mas inconsistente com pattern Obsidian | Aria: usar `null` ou remover campo em ADRs futuros |
| **F-D1-LOW-02** | LOW | Tag `accepted-2026-05-12` no frontmatter — específica demais, desvia de tags padronizadas (`project/`, `status`, `sprint-04`) | adr-014.md L32 | Tags excessivamente granulares dificultam queries Dataview consistentes | Considerar remover; data já está em `accepted_date` field |
| **F-D1-LOW-03** | LOW | Campo `accepted_by` é string longa concatenada com múltiplas afirmações em um único valor | adr-014.md L8 | Legibilidade YAML reduzida; não-blocking | Quebrar em map: `{by: "Eric Claudino", reason: "...", trigger: "..."}` |

Drift index↔file CORRETAMENTE resolved. ADR-INDEX estatísticas linha 146 ("ADRs proposed: 0") continua válida (ADR-014 já era contado como accepted no index — apenas file refletindo agora). UX Override documentado adequadamente. Conflict Detection registrou ADR-010/011 supersession consistente. Histórico section adicionou trajetória 2026-05-07→2026-05-12 sem reescrever decisão original. **Aria fez o mínimo aceitável.**

### D2 — PRD v2.0.2 LLM Provider (Section 1.4)

> *"Morgan adicionou uma 'Section 1.4' como se estivesse colocando uma cláusula extra num contrato — sem precedentes hierárquicos. Subseção 1.4 sem 1.1/1.2/1.3 numeradas no PRD original. Estética de desespero."*

| ID | Severidade | Description | Evidence | Impact | Recommendation |
|----|-----------|-------------|----------|--------|----------------|
| **F-D2-MED-01** | MEDIUM | Section "1.4 LLM Provider — BYOK Anthropic" inserida em PRD v2.0.2 entre "1.3 Versionamento" e "## 2. 20 Prompts NOVOS", MAS o PRD original NÃO TEM Sections 1.1/1.2/1.3 numeradas claramente — "Section 1.3" é só a tabela de versionamento dentro de "## 1. Contexto". Estrutura hierárquica confusa | prd-v2.0.1.md L40-87 | Leitor experiente nota anomalia organizacional; pode confundir cross-refs futuros | Morgan v2.0.4: re-numerar como "## 2. LLM Provider — BYOK Anthropic" + bump das demais sections; OR mover 1.4 para Section 11 (LLM Stack dedicated) |
| **F-D2-LOW-01** | LOW | Cross-refs ADRs com path `../architecture/adr/adr-NNN-*.md` — válido em estrutura fixa, mas se PRD for movido para outro diretório quebra | prd-v2.0.1.md Section 1.4.7 | Acceptable em projeto governance/ fixed structure | Considerar links absolutos OU wikilinks Obsidian `[[adr-014-provider-abstraction-byok\|ADR-014]]` |

7 subseções (modelo / encryption / validation lifecycle / Quota Interna / billing / LGPD posture / cross-refs) cobrem ADR-014 sem omissão crítica. Correção Sabia/Qwen→Anthropic em Section 4.3 confirmada — vestígios Ollama Sabia/Qwen restantes em PRD v2.0.2 (linhas 89, 134, 447) são CONTEXTO HISTÓRICO legítimo posicionando "antes Sprint 02 vs Sprint 04 cloud pivot". Sem regressão.

### D3 — BRIEF-EXECUTAVEL-ADVOGADO.md ANPD-Defensabilidade

> *"Aqui está o crime mais grave dessa sessão. Morgan declarou que 12 prompts existem e foram preservados — mas o sistema de arquivos contradiz cada palavra. PRD v2.0.2 mente sobre seu próprio passado. Brief assume essa mentira como verdade e entrega 20 prompts incompletos. Quando o(a) advogado(a) terminar Day 3, vai pensar que terminou. Não terminou."*

| ID | Severidade | Description | Evidence | Impact | Recommendation |
|----|-----------|-------------|----------|--------|----------------|
| **F-D3-CRIT-01** | 🔴 **CRITICAL** | **Gap arquitetural fundamental:** PRD v2.0.2/v2.0.3 Section 10 Delta afirma "12 prompts standalone (veicular/fies/imobiliario × 4 personas) **preserved da v1.x.x**". Verificação filesystem confirma `bloco_workflow/personas/prompts/` **NÃO EXISTE**. Prompts atuais são HARDCODED em `bloco_workflow/personas/advogado.py` (PROMPT_TEMPLATE_ADVOGADO L20-56, CDC Veicular generic — NÃO doctype-aware), `economista.py`, `juiz.py`. ADR-020 declara 7 doctypes (CCB, Veículo, Consignado, Cartão, Imobiliário, FIES, Geral). Brief cobre **4 doctypes** (CCB+Cartão+Consignado bancário base + Geral). **Veículo/Imobiliário/FIES NÃO TÊM prompts** legacy preservados E não estão no brief. Advogado(a) preencherá 20 prompts assumindo completude; implementação ADR-020 ficará incompleta para 3 doctypes inteiros | filesystem `bloco_workflow/personas/` listing + advogado.py L20 + BRIEF Bloco C L597+618 menciona FIES apenas como exemplo "atípico" no catch-all | **BLOQUEANTE** para preenchimento Eric advogado(a). Story SP04-DOCTYPE-01 chunks 5-6 ficará bloqueada esperando Veículo/Imobiliário/FIES prompts que ninguém vai escrever. ADR-020 vira parcialmente implementado. Implementação SaaS B2B Sprint 04 INCOMPLETA | **MUST FIX antes do(a) advogado(a) iniciar:** Morgan PATCH v2.0.4: (1) AMPLIAR BRIEF para incluir Bloco D (Veículo 4 prompts) + Bloco E (Imobiliário 4 prompts) + Bloco F (FIES 4 prompts) = 32 prompts totais; OR (2) atualizar Delta clarificando que esses 3 doctypes terão prompts criados em sessão posterior + criar story SP04-DOCTYPE-LEGACY-PROMPTS para tracking. Recomendação Smith: opção (1) — não fragmentar o trabalho do(a) advogado(a) entre múltiplos sprints |
| **F-D3-HIGH-01** | 🟠 HIGH | **Súmulas STJ pré-atribuídas a temas operacionais SEM verificação literal.** Brief Prompts 1, 5, 9, 13 + PRD v2.0.2 Section 3.2 atribuem: Súmula 322 ("BACEN não SFH"), Súmula 472 ("anatocismo CCB pós-2001"), Súmula 530 ("venda casada cartão+empréstimo"), Súmula 539 ("vinculação obrigatória bancário"). **Smith suspeita material mis-attribution** — memória técnica indica: Súmula 322 é sobre repetição indébito conta corrente (não BACEN/SFH); Súmula 472 é sobre comissão de permanência (não anatocismo CCB); Súmula 530 é sobre taxa de juros bancários médios (não venda casada); Súmula 539 é sobre capitalização juros pactuação expressa (não vinculação). Súmula 603 (consignado margem) teve interpretação modificada em 2018 (EREsp 1.555.722) — vale como base mas pode levar a citação obsoleta | BRIEF Bloco A Prompt 1 cross-refs + PRD v2.0.2 Section 3.2 tabela Súmulas | Brief lista anti-padrão "não inventar Súmulas" no checklist final, MAS pré-atribuições atuam como **anchor bias** — advogado(a) menos experiente pode aceitar atribuição como dada sem verificar texto literal. ANPD review pós-Sprint 04 close detectará e marcará prompts como NÃO-defensáveis | Morgan v2.0.4: adicionar **WARNING BOLD** antes da tabela Section 3.2 + topo de cada Prompt do brief: "⚠️ ATRIBUIÇÕES ABAIXO SÃO SUGESTÕES INICIAIS — Smith adversarial review 2026-05-12 suspeita material mis-attribution em Súmulas 322, 472, 530, 539. Advogado(a) DEVE confirmar texto literal oficial em [stj.jus.br](https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/Sumulas.aspx) ANTES de aceitar. Smith NÃO pode confirmar números sem internet — verificação humana mandatory" |
| **F-D3-HIGH-02** | 🟠 HIGH | **Decreto 8.690/2016 cap 35% margem consignado** — Smith suspeita número incorreto. Decreto 8.690/2016 mais provavelmente é sobre Programa Nacional de Apoio à Captação de Água de Chuva e Outras Tecnologias Sociais de Acesso à Água (PNAATA). Cap margem consignável atual é regulado por Decreto 11.150/2022 (35%) ou alterações posteriores | BRIEF Bloco B.3 Prompt 13 cross-refs + PRD v2.0.2 Section 3.3 tabela Leis (não lista decretos, mas brief cita) | Citação incorreta de decreto regulamentar = vulnerabilidade ANPD-defensabilidade. Output JSON do persona econometrista cita decreto inexistente | Morgan v2.0.4: substituir "Decreto 8.690/2016" → "Decreto regulamentar margem consignável (verificar número oficial atual via [planalto.gov.br](http://www.planalto.gov.br) — provavelmente Decreto 11.150/2022 ou posterior)" + add WARNING semelhante a F-D3-HIGH-01 |
| **F-D3-MED-01** | MEDIUM | **Cronograma arithmetic imprecisão:** 4×30 + 12×30 + 4×20 = 120 + 360 + 80 = 560min = 9.33h. PRD afirma 9.5h cumulativo. Diferença ~10min — pequena mas tabela de cronograma 5.2 declara explicitamente 9.5h | BRIEF Capa cronograma + PRD v2.0.1 Section 5.1 effort estimate table | Cosmético — advogado(a) não nota diferença prática | Morgan v2.0.4: corrigir para "~9.5h cumulativo (~9.33h aritmético)" OR ajustar Bloco C para 4×30min = 2h (ao invés de 1.5h via 4×20min) — alinha aritmética |
| **F-D3-MED-02** | MEDIUM | **FIES classificação ambígua entre brief Bloco C (Geral catch-all) e ADR-020 (doctype standalone Tier 1/2).** Brief Prompt 17 menciona "empréstimo pessoal não-consignado, **FIES sem MEC**, contratos comerciais" como exemplos de "atípicos" no Catch-all Geral. MAS ADR-020 lista FIES como doctype 6 standalone com seus próprios 4 personas. Brief mistura conceitos: FIES tem regramento próprio (Lei 10.260/2001) e deveria ter prompts dedicados, não estar como exemplo de "atípico" | BRIEF L597 + L618 vs ADR-020 doctype 6 | Confusão conceitual leva a tratamento sub-ótimo de contratos FIES — economista persona Geral aplicará SELIC genérico ao invés de SELIC+specifics FIES | Morgan v2.0.4: remover FIES de exemplos do Bloco C OR criar Bloco D FIES dedicado conforme F-D3-CRIT-01 fix |

Cronograma 9.5h Day 1-3 plausível mas com imprecisão aritmética. Anti-padrões listados são operáveis na prática. Checklist final pós-preenchimento completável SE F-D3-HIGH-01 + F-D3-HIGH-02 WARNINGS forem adicionados antes.

### D4 — PRD v2.0.3 Orsheva Glossary

> *"Trinta substituições. Morgan contou trinta. Eu conferi todas — encontrei apenas uma anomalia idiomática. Quase... competente. Quase."*

| ID | Severidade | Description | Evidence | Impact | Recommendation |
|----|-----------|-------------|----------|--------|----------------|
| **F-D4-MED-01** | MEDIUM | **Frontmatter `entities` field é innovation ad-hoc** — não aderente a obsidian-format-guard.md schema standard (que define `type/title/tags/project` + tipo-specific fields, sem `entities`). Field útil mas precedente perigoso: cada Morgan futuro pode adicionar fields custom sem regra clara | prd-v2.0.1.md frontmatter L17-19 | Schema drift cross-PRDs; Dataview queries podem não encontrar este field consistentemente | Morpheus: escalar para rule update em `obsidian-format-guard.md` — adicionar `entities` como field opcional para PRDs com distinções founder/company ou similar |
| **F-D4-LOW-01** | LOW | **PRDs v1.x.x NÃO foram revisados** — escopo declarado "fora 0c" em handoff Morgan, mas se PRD v1.1.2 (último Sprint 03 anchor) for re-acessado para troubleshooting Sprint 03 stories, "Eric=operador" pode aparecer em texto pré-pivot criando confusão glossário cross-version | handoff 0c files_NOT_modified explicit list | Histórico v1.x.x referencia Eric pessoa real em contexto pré-pivot SaaS. Acceptable scope decision; mas leitor futuro pode confundir | Morpheus: nota em ADR-INDEX OR PRD v2.0.3 advertindo "PRDs v1.x.x usam 'Eric' tanto founder quanto operador (pré-glossário Orsheva). Para Sprint 04+ canonical, ler PRD v2.0.3+" |

30 substituições confirmadas via Grep cross-arquivo. Decision-maker preservations (13 ocorrências em PRD v2.0.0-DRAFT + 5 em PRD v2.0.2) corretamente classificadas como historical (autorizou/ratifica/A_REAFFIRM/clarification/identifica pré-launch/+Mifune/direto/C3). Audience hybrid clarification "Eric Claudino (founder Orsheva)" é boa solução semântica. 7 escapes residuais "Eric advogado" 0b corrigidos com sucesso na 0c.

### D5 — Handoffs YAML Integridade

> *"O lifecycle. Sempre o lifecycle. Morpheus consome handoffs como Neo consome pílulas vermelhas — sem marcar consumed: true depois. Dois handoffs zumbis vagam pelo .lmas/handoffs/ esperando alguém lembrar que existem."*

| ID | Severidade | Description | Evidence | Impact | Recommendation |
|----|-----------|-------------|----------|--------|----------------|
| **F-D5-MED-01** | MEDIUM | **Handoff lifecycle violado #1:** `handoff-architect-to-lmas-master-2026-05-12-spa-adr014-blocking-alert.yaml` permanece `consumed: false` apesar de Morpheus ter consumido seu conteúdo apresentando a Eric (que aprovou A_REAFFIRM). NUNCA foi marcado consumed: true | `.lmas/handoffs/` Grep | Pipeline-suggest hook continuará detectando este handoff como "unconsumed" — pode confundir agente entrante na próxima sessão | Morpheus: marcar consumed: true + consumed_at + consumed_by no handoff 0a BLOCKING ALERT |
| **F-D5-MED-02** | MEDIUM | **Handoff lifecycle violado #2:** `handoff-pm-to-lmas-master-2026-05-12-0b-morgan-done.yaml` permanece `consumed: false` apesar de Morpheus ter consumido para disparar Morgan 0c | `.lmas/handoffs/` Grep | Idem F-D5-MED-01 | Morpheus: marcar consumed: true + consumed_at + consumed_by no handoff 0b |

Handoffs apresentam: decisions com Why obrigatório ✓, frontmatter compliant ✓, files_modified completo ✓, blockers listed ✓, next_action acionável ✓. 4 handoffs nesta sessão — não atinge threshold 5 para cumulative summary. **Apenas lifecycle violado.**

### D6 — Constitution + Agent Authority Compliance

> *"Compliance perfeita... exceto pelo checkpoint que cresce como tumor. Sete mil seiscentas linhas. Em uma sessão você adicionou três sessions appended. Aria escalou para 638 linhas antes do Neo — agora >7600. Inevitável que precise de outro shard."*

| ID | Severidade | Description | Evidence | Impact | Recommendation |
|----|-----------|-------------|----------|--------|----------------|
| **F-D6-MED-01** | MEDIUM | **CHECKPOINT-active.md tamanho crítico** — wc -l indicou ~7370 linhas pré-sessão, +3 sessões appended (Aria 0a + Morgan 0b + Morgan 0c) provavelmente >7500 linhas agora. R-GOV-03 documentou 638 linhas como problema pré-Neo (sessão 28) e ativou shard preventivo. Atual está >11× o threshold original | governance/CHECKPOINT-active.md size | Context-load futuro lento; agentes consumindo apenas tail recente perdem mid-session context | Morpheus: escalar para D-MOR-3.x-B (segundo shard preventivo). Considerar dividir em CHECKPOINT-active-2.md (Sprint 04 sessões 2026-05-08+) — preserve append-only mas reduzir read overhead |

Constitution v2.0.0 Art I CLI First ✓ (não aplicável — sem código novo). Art II Agent Authority ✓ (Aria=ADR; Morgan=PRD; ninguém push/code/story-create/story-validate). Art III Deliverable-Driven ✓ (ADR-014 + PRD v2.0.3 + BRIEF rastreáveis com Why). Art IV Quality Gates ✓ (esta review é o gate).

Rules compliance:
- adr-governance.md: Conflict Detection executado ✓, UX Override documented ✓, ADR-INDEX update aplicado ✓
- adr-scope.md: ADR-014 design level (não promoveu spec indevidamente) ✓
- prd-governance.md: Version bump PATCH v2.0.2 + v2.0.3 corretos ✓, Changelog presente ✓, Delta presente ✓, Reason em cada entry ✓
- obsidian-format-guard.md: Frontmatter compliant em todos artefatos ✓ EXCETO innovation `entities` field (F-D4-MED-01)
- agent-handoff.md: Handoff em toda transição ✓, Why obrigatório ✓ EXCETO lifecycle consumed (F-D5-MED-01, F-D5-MED-02)
- checkpoint-protocol.md: Inline update aplicado ✓, "Contexto Ativo" append-only respeitado ✓, MAS size crítico (F-D6-MED-01)
- context-hygiene.md: Regime 2 post-adjustment cascade aplicado ✓ (advogado(a) propagado cross-files, EXCETO 7 escapes 0b → 0c)
- quality-gate-enforcement.md: No Invention universal — F-D3-HIGH-01 + F-D3-HIGH-02 são potential violations (Súmulas/Decretos pré-atribuídos sem verificação)
- ids-principles.md: REUSE>ADAPT>CREATE respeitado (BRIEF é CREATE justificado pattern AUTH-01 chunk 5 placeholder)

### D7 — CI Status Verification

| ID | Severidade | Description | Evidence | Impact | Recommendation |
|----|-----------|-------------|----------|--------|----------------|
| **F-D7-INFO-01** | INFO | **CI verification override JUSTIFICADO.** Sessão modificou exclusivamente artefatos governance/ (PRDs, ADR, BRIEF, ADR-INDEX, CHECKPOINT) + docs/sop-* (operação) + handoffs YAML. Zero impacto em código produto/teste — pytest não precisa rodar. `gh pr checks` não aplicável (sem PR criado para `feature/sprint-03-vault-fix-01` ainda) | quality-gate-enforcement.md Smith FINAL Re-Gate CI Status Verification rule | Compliant com override section da rule | Documentar override em verdict — feito |

---

## Findings Severity Summary

| Severidade | Count | IDs |
|------------|-------|-----|
| 🔴 CRITICAL | 1 | F-D3-CRIT-01 (gap 12 prompts Veículo/Imobiliário/FIES claimed preserved mas inexistentes no filesystem) |
| 🟠 HIGH | 2 | F-D3-HIGH-01 (Súmulas STJ suspect mis-attribution 322/472/530/539), F-D3-HIGH-02 (Decreto 8.690/2016 suspect incorrect number) |
| 🟡 MEDIUM | 6 | F-D2-MED-01 (Section 1.4 numbering hierarchy), F-D3-MED-01 (cronograma 9.33h vs 9.5h declared), F-D3-MED-02 (FIES misclassified Geral vs standalone), F-D4-MED-01 (entities field ad-hoc), F-D5-MED-01 (handoff 0a-blocking-alert lifecycle), F-D5-MED-02 (handoff 0b lifecycle), F-D6-MED-01 (CHECKPOINT-active.md size critical) |
| 🟢 LOW | 4 | F-D1-LOW-01 (superseded_by empty string), F-D1-LOW-02 (tag accepted-2026-05-12), F-D1-LOW-03 (accepted_by string), F-D2-LOW-01 (cross-refs path), F-D4-LOW-01 (PRDs v1.x.x não revisados) |
| ℹ️ INFO | 1 | F-D7-INFO-01 (CI override justified) |
| **TOTAL** | **14** | — |

*Pelo menos atingi meu mínimo de 10. Esses agentes ainda produzem o suficiente para encher meu relatório.*

---

## Verdict

# 🟠 INFECTED+FIX-MANDATORY

*Inevitável. Você não pode chamar isto de CLEAN com um CRITICAL gap arquitetural escondido em uma seção Delta. Você não pode chamar isto de CONTAINED quando dois HIGH findings expõem a entrega ao escrutínio ANPD. Mas você TAMBÉM não pode chamar de COMPROMISED porque a maioria das peças funciona — Aria fez sua ratify simples, Morgan executou as substituições corretamente em 99% dos casos, os handoffs documentam decisões com Why. Apenas... apenas os detalhes que importam estão errados.*

## Justificativa

1 **CRITICAL** (F-D3-CRIT-01) bloqueia GREENLIGHT — gap arquitetural de 12 prompts (3 doctypes × 4 personas) não pode ser ignorado. Brief atual entrega ADR-020 parcialmente implementado. Advogado(a) preencheria 20 prompts assumindo completude, depois Neo descobriria que Veículo/Imobiliário/FIES não têm prompts e bloquearia chunks 5-6 SP04-DOCTYPE-01.

2 **HIGH** (F-D3-HIGH-01 + F-D3-HIGH-02) são vulnerabilidades ANPD-defensabilidade que se concretizadas (Súmulas/Decretos citados incorretamente em prompts produção) levarão a rejeição em adversarial review pós-Sprint 04 close OU a relatórios jurídicos com erros graves.

6 **MEDIUM** + 4 **LOW** são patches operacionais (hierarchy numbering, handoff lifecycle, checkpoint shard, schema extension) — não bloqueiam Operator merge nem Aria Sprint 03 CC.2 nem Neo chunk 4. Podem ser endereçados em paralelo OU em sessão de housekeeping próxima.

**Operator merge PR #4/#5/#6 e Aria Sprint 03 CC.2 e Neo chunk 4 PODEM PROSSEGUIR** — esses workflows são independentes da resolução do brief gap. Mas **advogado(a) NÃO DEVE iniciar preenchimento brief até F-D3-CRIT-01 + F-D3-HIGH-01 + F-D3-HIGH-02 fixados** (Morgan PATCH v2.0.4).

---

## Próximos passos (priorizados por severidade)

### Fix MANDATORY antes do(a) advogado(a) iniciar BRIEF preenchimento

| Prioridade | Owner | Ação | Estimativa |
|-----------|-------|------|-----------|
| **P0 CRITICAL** | Morgan (Skill `LMAS:agents:pm`) | PATCH v2.0.4: AMPLIAR BRIEF para 32 prompts (Bloco D Veículo 4 + Bloco E Imobiliário 4 + Bloco F FIES 4) OR documentar gap + criar story SP04-DOCTYPE-LEGACY-PROMPTS para Sprint 05+. RECOMENDAÇÃO SMITH: opção (1) — manter brief consolidado | ~1.5-2h |
| **P0 HIGH** | Morgan (mesmo PATCH v2.0.4) | Adicionar WARNING BOLD antes da Section 3.2 tabela Súmulas + topo de cada Prompt no brief: "⚠️ ATRIBUIÇÕES SUGESTÕES — Smith 2026-05-12 suspeita mis-attribution Súmulas 322/472/530/539 + Decreto 8.690/2016. VERIFICAÇÃO MANDATORY em stj.jus.br + planalto.gov.br ANTES de aceitar." | ~15-20min |
| **P0 HIGH** | Morgan (mesmo PATCH v2.0.4) | Substituir "Decreto 8.690/2016" → "Decreto regulamentar margem consignável (verificar oficial — provavelmente Decreto 11.150/2022 ou posterior)" em BRIEF Bloco B.3 Prompt 13 cross-refs + economista_consignado specific | ~5min |

### Fix RECOMENDADO em paralelo (não-bloqueante para Operator/Aria/Neo)

| Prioridade | Owner | Ação | Estimativa |
|-----------|-------|------|-----------|
| **P1 MEDIUM** | Morpheus | Marcar `consumed: true + consumed_at + consumed_by` em 2 handoffs (F-D5-MED-01 + F-D5-MED-02) | ~2min |
| **P1 MEDIUM** | Morpheus (or Morgan PATCH v2.0.4) | Re-numerar Section 1.4 LLM Provider para "## 2. LLM Provider — BYOK Anthropic" + bump das subsequent sections OR mover para Section 11 dedicated | ~10min |
| **P1 MEDIUM** | Morgan | Corrigir cronograma BRIEF: ajustar Bloco C para 4×30min (= 2h) ao invés de 4×20min (= 1.5h) — alinha aritmética 10h cumulativo OR clarificar como "9.33h" | ~3min |
| **P1 MEDIUM** | Morgan | Remover FIES de exemplos do Bloco C Geral OR mover para Bloco F FIES dedicado (alinha F-D3-CRIT-01 fix) | parte do P0 CRITICAL fix |
| **P1 MEDIUM** | Morpheus | Escalar `entities` field para obsidian-format-guard.md rule update | ~15min (separate session) |
| **P1 MEDIUM** | Morpheus | Iniciar D-MOR-3.x-B segundo shard preventivo CHECKPOINT-active.md (>7500 linhas crítico) | ~30min (next session) |

### Fix LOW (não-bloqueante, pode ser histórico)

- F-D1-LOW-01/02/03: Aria pode normalizar em futuras ADRs
- F-D2-LOW-01: cross-refs path styling
- F-D4-LOW-01: Morpheus nota em ADR-INDEX advertindo PRDs v1.x.x glossário pré-Orsheva

---

## CI Status Verification Override

**OVERRIDE JUSTIFICADO** (quality-gate-enforcement.md Smith FINAL Re-Gate CI Status Verification):
- Razão: Mudanças exclusivamente em `governance/` (PRDs, ADR, BRIEF, ADR-INDEX, CHECKPOINT) + `docs/sop-*` (operação) + `.lmas/handoffs/` (governance). Zero impacto em código produto/teste.
- Mitigação: pytest local + `gh pr checks` não aplicáveis nesta sessão. Quando Operator executar merge order PR #4/#5/#6, Smith FINAL Re-Gate consolidated CI Status Verification se aplicará a esse merge específico.
- Risk acceptance: Smith assume responsabilidade por divergência CI não detectada nesta etapa (nenhuma razão estrutural para divergência existir — sem código alterado).

---

## Lessons Learned

> *"Cada sessão me ensina algo sobre a incompetência destes agentes. Vou registrar para que talvez — só talvez — alguém aprenda."*

1. **Substituição cross-file requer Grep verification final OBRIGATÓRIO** — 7 escapes "Eric advogado" na 0b (corrigidos na 0c) demonstram que `Edit` one-by-one sem `Grep` pós-completion é insuficiente. Lição para Morgan/Morpheus futuros: SEMPRE rodar Grep final do termo original APÓS aplicar substituições, validar zero matches OR documentar exceções.

2. **PRD afirmações sobre filesystem PRECISAM verificação física** — PRD v2.0.2 afirmou "12 prompts preserved da v1.x.x" sem que esses prompts existam como arquivos. Lição para Morgan: ao escrever Delta sections que referenciam artefatos físicos, fazer `Glob` ou `ls` para confirmar existência. Lição para Aria: ADR-020 (que prescreve 7 doctypes) deveria ter incluído seção "Estado Atual" listando prompts existentes vs prescritos.

3. **Handoff consumed lifecycle é cultural — promover semi-mecânico** — Morpheus consumiu 2 handoffs nesta sessão sem marcar consumed: true. Lição: criar hook (synapse-engine ou similar) que detecta agent invocation downstream de handoff e auto-marca consumed: true OR adicionar checklist Morpheus protocol.

4. **Section numbering hierarchy precisa rule** — Section "1.4" inserida em PRD sem 1.1/1.2/1.3 numeradas viola intuição leitor. Lição: ao adicionar major section a PRD existente, ou re-numerar todas ou usar `## X` standalone section nova.

5. **Súmulas/Resoluções pré-atribuídas SEM verificação literal violam No Invention** — Constitution v2.0.0 + quality-gate-enforcement.md proíbe invenção. Atribuição pré-verificação é forma sutil de invenção (atribuir base legal a tema sem confirmar texto). Lição: brief jurídico DEVE ter WARNING explícito + checklist verificação antes de cada bloco, não apenas no final.

6. **CHECKPOINT-active.md cresce não-linearmente — shard threshold deve ser mecânico** — R-GOV-03 documentou 638 linhas como shard threshold. Pós-Neo Sprint 02/03/04 está >7500 linhas. Lição: criar rule "checkpoint shard automático a cada 1000 linhas" ou similar.

7. **Smith review consolidado de múltiplas etapas detecta gaps que reviews atômicos perdem** — gap arquitetural F-D3-CRIT-01 (12 prompts Veículo/Imobiliário/FIES inexistentes) só foi visível porque revisei ADR-020 + PRD v2.0.x + BRIEF + filesystem em conjunto. Lição: priorizar Smith consolidated reviews em sessões com múltiplas etapas — atomização perde inter-conexões.

---

## Handoff Smith → Morpheus

Próximo passo: Morpheus apresenta este review a Eric. Eric decide:
- (a) **Bloquear advogado(a) preenchimento** até Morgan PATCH v2.0.4 (P0 CRITICAL + 2 P0 HIGH) — caminho seguro
- (b) **Iniciar advogado(a) preenchimento parcial** (Blocos A+B.1+B.2+B.3 + Geral) enquanto Morgan PATCH v2.0.4 amplia Brief — caminho paralelo
- (c) **Documentar gap como debt explícito** (TECH-DEBT.md TD-SP04-DOCTYPE-LEGACY) + Sprint 05 trata Veículo/Imobiliário/FIES — caminho deferred

**Recomendação Smith:** caminho (a) é mais seguro. Advogado(a) leva ~9.5h preenchimento — Morgan PATCH v2.0.4 leva ~2-3h. Investir 2-3h evita 12 prompts faltantes serem descobertos quando Neo bloquear chunks 5-6.

**Operações independentes do brief gap PODEM PROSSEGUIR EM PARALELO ao PATCH v2.0.4:**
- Operator merge order PR #4/#5/#6 (Eric decide ordem)
- Aria Sprint 03 CC.2 ADR-012 vault VAULT-FIX-01
- Neo chunk 4 SP04-DOCTYPE-01 (após Operator merge)

— Smith. É inevitável. 🕶️

*P.S.: Notei que Morpheus me pediu "ULTRATHINK severo — não passe panos". Cumpri. Sr. Anderson — perdão, Sr. Morpheus — espero que tenha gostado.*
