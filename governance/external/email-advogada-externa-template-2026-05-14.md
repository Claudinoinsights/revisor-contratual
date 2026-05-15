---
type: external-handoff-email
title: "Email template — Advogada externa OAB review pré-launch v0.2.0 (AC-PRD-γ-05)"
project: revisor-contratual
version: "1.0.0"
last_updated: "2026-05-14"
authored_by: "@pm Morgan (Trinity)"
audience: "Eric Claudino (envia) → Advogada externa (recebe)"
status: ready-to-send
related_to:
  - "PRD-SP06-GAMMA v0.1.0 (AC-PRD-γ-05 BLOQUEANTE)"
  - "handoff-advogada-externa-2026-05-14.md (documento anexo)"
  - "Sprint 6 Bloco γ COMPLETE (v0.2.0 + v0.2.1 + v0.2.2 origin/main)"
tags:
  - project/revisor-contratual
  - external-handoff
  - advogada-review
  - oab-compliance
  - pre-launch
---

# Email Template — Advogada Externa OAB Review

> **Owner Eric:** preencha campos `{{...}}` antes de enviar. Checklist pre-send no final.

---

## Subject

```
Review OAB compliance — Sistema Revisor Contratual IA (CDC veículos PF) — pré-launch v0.2.0
```

---

## Corpo do email

```
Prezada Dra. {{NOME_ADVOGADA}},

Espero que esta mensagem a encontre bem. Escrevo para solicitar sua expertise em
direito bancário e ética profissional OAB para um review jurídico específico de
um sistema que estou prestes a lançar em produção.

═══════════════════════════════════════════════════════════════════════
SOBRE O PRODUTO
═══════════════════════════════════════════════════════════════════════

Sou Eric Claudino, fundador da Orsheva. Desenvolvi o Revisor Contratual, um SaaS
B2B destinado a escritórios de advocacia que atuam em revisional bancária. O
sistema automatiza a análise de contratos CDC veículos pessoa física (escopo MVP)
e gera uma peça revisional inicial em PDF profissional pronta para revisão
humana e protocolo judicial.

O fluxo técnico é um pipeline de 9 etapas: parsing do PDF do contrato → análise
das cláusulas → cálculo financeiro Decimal (anatocismo, IOF, capitalização) →
consulta BACEN SGS (taxas históricas) → vault de jurisprudência STJ/STF →
personas LLM (Advogado + Economista + Juiz) → persona Redator Revisional → render
PDF via WeasyPrint → entry de auditoria HMAC. A peça final segue estrutura OAB
Provimento 209/2021 CFOAB em 8 seções (Cabeçalho, Qualificação, Fatos, Direito,
Pedido, Valor da Causa, Fecho, Disclaimer LGPD/OAB).

Operacionalmente: o sistema roda 100% on-premise (LGPD §11 + §46 compliance), o
escritório-cliente fornece suas próprias API keys de LLM (modelo BYOK — Bring
Your Own Key), e eu (Eric) sou o operador de tratamento de dados nos termos
LGPD. O sistema NÃO substitui o(a) advogado(a) responsável — toda peça gerada
tem disclaimer explícito de que é insumo técnico-jurídico assistivo e exige
revisão profissional antes do protocolo.

═══════════════════════════════════════════════════════════════════════
O QUE PRECISO DE VOCÊ
═══════════════════════════════════════════════════════════════════════

Estou em momento pré-launch da versão 0.2.0 em produção. Antes de liberar para
escritórios reais, preciso de um parecer técnico-jurídico seu cobrindo
especificamente quatro pontos:

1) BOAS PRÁTICAS OAB
   A peça revisional gerada respeita as boas práticas da OAB em termos de
   fundamentação jurídica, citação de Súmulas STJ, linguagem técnica adequada e
   estrutura processual? Em particular, é coerente com Provimento 209/2021 CFOAB
   sobre uso de IA em peças.

2) ANÁLISE DE EXEMPLOS REAIS
   Anexei {{N_PECAS_ANEXADAS}} peças revisionais reais geradas pelo sistema
   (anonimizadas — sem CPF, nome de cliente ou dados específicos de contrato
   identificáveis). Solicito análise crítica: a qualidade jurídica está
   aceitável? Há riscos de fundamentação fraca, citações incorretas ou estrutura
   processual deficiente?

3) DISCLOSURES NECESSÁRIOS AO USUÁRIO FINAL
   Quais avisos legais o sistema DEVE exibir ao advogado(a) revisor(a) antes de
   ele(a) utilizar a peça gerada? (Ex: limitação de responsabilidade do
   fornecedor, obrigatoriedade de revisão humana, ressalvas sobre AI-generated
   content, etc.) O disclaimer atual está nos anexos.

4) ENQUADRAMENTO "ASSISTIVE AI" UX
   O sistema está corretamente posicionado como assistivo (não substitutivo do
   advogado)? Há melhorias específicas que você recomendaria na comunicação ou
   na interface para reforçar esse enquadramento ético?

═══════════════════════════════════════════════════════════════════════
ANEXOS
═══════════════════════════════════════════════════════════════════════

- {{N_PECAS_ANEXADAS}} peças revisionais anonimizadas (PDF)
- Handoff Document — descrição técnica detalhada do produto (Markdown/PDF)
- Brandbook OrSheva 7 (HTML) — identidade visual e tokens de design
- Disclaimer LGPD/OAB atualmente embutido (excerpt)

═══════════════════════════════════════════════════════════════════════
PRAZO E COMPENSAÇÃO
═══════════════════════════════════════════════════════════════════════

Prazo sugerido: {{PRAZO_DIAS}} dias úteis (não bloqueante para desenvolvimento
técnico, mas bloqueante para deploy em produção real).

Compensação: {{VALOR_COMPENSACAO}} (sujeito a negociação caso o escopo se mostre
maior do que o previsto).

Formato de entrega esperado: parecer escrito (.md, .pdf ou .docx) com veredito
APROVADO / APROVADO COM RESSALVAS / NEEDS CHANGES, lista de findings (se
houver), e recomendações específicas.

═══════════════════════════════════════════════════════════════════════
PRÓXIMO PASSO
═══════════════════════════════════════════════════════════════════════

Posso agendar uma call de 30 minutos para apresentar o produto em demo ao vivo
e esclarecer dúvidas técnicas antes de você iniciar o review formal. Tenho
disponibilidade {{DISPONIBILIDADE_ERIC}}.

Fico à disposição para qualquer esclarecimento prévio. Agradeço imensamente a
atenção e aguardo seu retorno.

Cordialmente,

Eric Claudino
Fundador — Orsheva
{{EMAIL_ERIC}}
{{TELEFONE_ERIC}}
```

---

## Checklist Eric pre-send (OBRIGATÓRIO antes de enviar)

- [ ] **Anexar {{N_PECAS_ANEXADAS}} PDFs peças revisionais anonimizadas** (Eric remove PII: nome cliente, CPF, endereço, dados identificáveis do contrato). Sugestão: 2 peças — 1 caso APROVADO_100 + 1 caso APROVADO_COM_RISCO_HITL.
- [ ] **Confirmar destinatária** — `{{NOME_ADVOGADA}}` + email + OAB nº (Eric tem ou precisa pesquisar). Se mesma advogada do Sprint 04 (Orsheva): considerar histórico positivo.
- [ ] **Definir compensação** — `{{VALOR_COMPENSACAO}}` (Eric decide; não cabe Trinity especular valor de mercado).
- [ ] **Definir prazo** — `{{PRAZO_DIAS}}` (sugestão: 5 dias úteis; ajuste conforme urgência deploy).
- [ ] **Definir disponibilidade call** — `{{DISPONIBILIDADE_ERIC}}` (ex: "qualquer terça/quinta entre 14h-17h").
- [ ] **Anexar Handoff Document** (`governance/external/handoff-advogada-externa-2026-05-14.md`) — converter para PDF se preferir, ou enviar Markdown direto.
- [ ] **Anexar Brandbook OrSheva 7** (`orsheva-brandbook.html` — Eric tem local) — opcional mas reforça profissionalismo.
- [ ] **Cc próprio** — para arquivar resposta no inbox e ter trilha de e-mail.
- [ ] **Anotar deadline em calendar** — `{{PRAZO_DIAS}}` dias úteis para follow-up se sem resposta.
- [ ] **Revisar Handoff Document tecnicamente** — Eric valida exatidão (não há features inventadas; tudo bate com PRD Bloco γ + Sprint 6.x COMPLETE em origin/main).

---

## Notas para Eric

- **Tom:** Formal mas pragmático. Você é o fundador, não o subordinado — fala de igual para igual com a advogada como profissional contratante.
- **Privacidade:** As peças anonimizadas DEVEM passar por checklist LGPD antes de sair (remover CPF, nome, endereço, hash do contrato, qualquer dado identificável). Em caso de dúvida, use placeholders explícitos: `[NOME ANONIMIZADO]`, `[CPF ANONIMIZADO]`.
- **Histórico Orsheva:** Se for a mesma advogada da entrega 2026-05-12 (20/32 prompts), você pode iniciar o email com "Dando continuidade ao trabalho que iniciamos em maio..." — economiza contexto.
- **Risco R-06 PRD Bloco γ:** Advogada review pode demorar >7 dias. Tenha plano B (advogada backup ou ajuste prazo).

---

*— Morgan (Trinity), planejando o futuro 📊*
*"Email enxuto, escopo claro, sem inventar features. Aguarda seu envio, Eric."*
