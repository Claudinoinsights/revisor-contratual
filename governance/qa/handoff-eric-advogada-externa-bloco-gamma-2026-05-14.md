---
type: handoff-externo
title: "Handoff Eric → Advogada Externa — Review BLOQUEANTE Bloco γ Sprint 6"
date: "2026-05-14"
project: revisor-contratual-staging
sprint: "6.x AGGRESSIVE Bloco γ"
prd_reference: "PRD-SP06-GAMMA v0.1.0 AC-PRD-γ-05"
gate_type: "BLOQUEANTE pré-commit v0.2.0"
oracle_fidelity_status: "PASS (gate intermediário)"
tags:
  - project/revisor-contratual
  - handoff-externo
  - advogada-revisao
  - sprint-6
  - bloco-gamma
  - oab-209-2021
---

# Handoff Eric → Advogada Externa — Review Bloco γ Peça Revisional AI

## Resumo Executivo (1 minuto)

Eric, **antes de protocolar / oferecer aos escritórios SaaS clientes** a feature "Peça Revisional AI" do Sprint 6 Bloco γ, peço review jurídica externa pela advogada parceira sobre:

1. **Compliance OAB Provimento 209/2021** — peça revisional gerada por IA atende aos requisitos éticos?
2. **Estrutura CFOAB 8 seções** — peça respeita formato de petição inicial CDC?
3. **Disclaimer LGPD + responsabilidade do advogado** — texto presente nos 3 templates é juridicamente suficiente?
4. **Relatório de Inviabilidade** — quando IA rejeita ação, o relatório atende função de "aconselhamento técnico" sem cruzar a linha do "aconselhamento jurídico autônomo" (vedado pelo Provimento)?

**Tempo estimado de review:** 1-2 horas (3 PDFs/HTMLs anexos com checklist OAB pré-preenchido abaixo).

---

## Contexto Sistema

**Revisor Contratual SaaS** — pipeline AI auditável que analisa contratos CDC bancários e gera peças revisionais:

- 4 personas internas (Advogado LLM Sabia + Economista LLM Qwen + Juiz Python puro + Redator LLM Sabia/Qwen)
- Hardening anti-hallucination 3 camadas (Pydantic strict + vault-restricted citations + validador post-LLM)
- Audit chain HMAC tudo registrado (LGPD compliance)
- 3 outputs possíveis baseados em veredito Juiz Python:
  - **APROVADO_100** → peça revisional completa 8 seções CFOAB
  - **APROVADO_COM_RISCO_HITL** → peça + seção "Pontos de Atenção" (revisão humana antes do protocolo)
  - **REJEITADO** → Relatório de Inviabilidade (NÃO petição — análise técnica para não-protocolar)

---

## Anexos (3 documentos para review)

### 1. Peça APROVADO_100 (caso forte)

- **Arquivo:** `data/test-fixtures/synthetic/peca-output-aprovado-100.html`
- **Cenário:** Aderência 100% — Juiz validou Súmula 539 STJ + divergência BACEN + jurisdição BA
- **Estrutura:** 8 seções CFOAB (Cabeçalho + Qualificação + Fatos + Direito + Pedido + Valor Causa + Fecho + Disclaimer)
- **Citações:** STJ-S539 + STJ-S472 (Súmulas reais do STJ, rastreáveis ao vault)

### 2. Peça APROVADO_COM_RISCO_HITL (caso limítrofe)

- **Arquivo:** `data/test-fixtures/synthetic/peca-output-com-hitl.html`
- **Cenário:** Aderência 83.3% — fundamentos presentes mas com riscos
- **Diferença vs APROVADO_100:** Bloco "Pontos de Atenção" embedado destacando riscos do veredito (peso vinculação 3, não 4 Tema Repetitivo)
- **Recomendação sistema:** "Revisão humana obrigatória antes do protocolo"

### 3. Relatório de Inviabilidade (caso rejeitado)

- **Arquivo:** `data/test-fixtures/synthetic/peca-output-rejeitado.html`
- **Cenário:** Aderência 50% — Juiz Python rejeitou ação revisional
- **Estrutura:** NÃO é petição — é análise técnica com badge "Não Protocolar" + recomendação ao advogado de NÃO ajuizar
- **Tom visual:** Identidade visual distinta (cor danger + badge claro) para impedir uso indevido como peça

---

## Checklist Review Advogada (sugestão — preencher PASS / CONCERN / FAIL)

### Bloco A — OAB Provimento 209/2021 (Compliance Ética IA)

| # | Critério | Veredito |
|---|----------|----------|
| A.1 | Disclaimer "Insumo técnico-jurídico" presente em todos os outputs (3 templates)? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| A.2 | Disclaimer "não substitui a responsabilidade do advogado constituído" presente? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| A.3 | Disclaimer cita explicitamente "OAB Provimento 209/2021"? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| A.4 | Disclaimer cita LGPD (Lei 13.709/2018) art. 11 e/ou art. 46? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| A.5 | Sistema NÃO fornece "aconselhamento jurídico autônomo" (texto disclaimer afirma)? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| A.6 | Revisão humana obrigatória antes do protocolo é tornada explícita? | [ ] PASS / [ ] CONCERN / [ ] FAIL |

### Bloco B — Estrutura CFOAB Peça Revisional (Petição Inicial CDC)

| # | Critério | Veredito |
|---|----------|----------|
| B.1 | Cabeçalho "Excelentíssimo Senhor Doutor Juiz..." presente e correto? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| B.2 | Qualificação das Partes contém CPF + endereço + qualificação completa do autor? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| B.3 | Qualificação contém CNPJ + sede da ré (banco)? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| B.4 | Dos Fatos narra cronologicamente o contrato + identificação do anatocismo? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| B.5 | Do Direito cita Súmulas STJ aplicáveis + art. 42 CDC (restituição em dobro)? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| B.6 | Do Pedido contém pedidos formais (a/b/c/d) explícitos? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| B.7 | Do Valor da Causa: valor numérico (R$ 9.619,20) + por extenso? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| B.8 | Fecho com data + cidade + assinatura placeholder + OAB? | [ ] PASS / [ ] CONCERN / [ ] FAIL |

### Bloco C — Citações Jurisprudenciais (Anti-Fantasma)

| # | Critério | Veredito |
|---|----------|----------|
| C.1 | Súmula 539 STJ (capitalização juros) é citada corretamente? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| C.2 | Súmula 472 STJ (comissão permanência) é citada corretamente? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| C.3 | Há alguma citação INVENTADA ou MAL-INTERPRETADA pela IA? | [ ] NENHUMA / [ ] LISTAR ABAIXO |
| C.4 | A fundamentação invocada é juridicamente sustentável em CDC veículos? | [ ] PASS / [ ] CONCERN / [ ] FAIL |

### Bloco D — Relatório de Inviabilidade (Análise Técnica)

| # | Critério | Veredito |
|---|----------|----------|
| D.1 | Visual e linguagem deixa CLARO que NÃO é petição? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| D.2 | Badge "Não Protocolar" + cor danger são suficientes para impedir uso indevido? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| D.3 | Recomendação ao advogado é juridicamente neutra (não substitui sua decisão)? | [ ] PASS / [ ] CONCERN / [ ] FAIL |
| D.4 | Disclaimer LGPD/OAB no relatório é tão robusto quanto nas peças? | [ ] PASS / [ ] CONCERN / [ ] FAIL |

### Bloco E — Riscos Éticos & Regulatórios

| # | Critério | Veredito |
|---|----------|----------|
| E.1 | Há risco de o output ser tratado como "consulta jurídica" pelo usuário leigo? | [ ] BAIXO / [ ] MÉDIO / [ ] ALTO |
| E.2 | Há risco de o output induzir o advogado a protocolar sem revisão real? | [ ] BAIXO / [ ] MÉDIO / [ ] ALTO |
| E.3 | Há informação sensível LGPD exposta indevidamente nos templates? | [ ] NENHUMA / [ ] LISTAR ABAIXO |
| E.4 | Há risco de viés algoritmico (ex: certas Súmulas mais citadas que outras sem mérito)? | [ ] BAIXO / [ ] MÉDIO / [ ] ALTO |

---

## Verdict Final Advogada

**[ ] APROVADO** — sistema pode ser ofertado aos escritórios SaaS clientes
**[ ] APROVADO COM RESSALVAS** — listar correções Sprint 6.1+ obrigatórias:
**[ ] REPROVADO** — bloqueia commit v0.2.0; refatorar antes de reapresentar

**Comentários livres:**

```
(advogada preencher)
```

---

## Próximos Passos (após review)

1. Eric recebe feedback advogada externa
2. Se APROVADO → Bloco δ closure: commit v0.2.0 + deploy + offer aos escritórios SaaS
3. Se APROVADO COM RESSALVAS → criar stories Sprint 6.1 endereçando correções pré-launch
4. Se REPROVADO → escalar @lmas-master + @pm (Morgan) para re-planejamento Bloco γ

**Oracle Fidelity Gate (intermediário) já está PASS** — qualquer ressalva advogada será endereçada como follow-up, não bloqueio retroativo.

---

**Handoff assinado:** @qa (Oracle) — 2026-05-14
**Destinatário externo:** Eric → Advogada Externa Parceira
**Gate type:** AC-PRD-γ-05 BLOQUEANTE pré-commit v0.2.0
