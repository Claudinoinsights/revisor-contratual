---
type: external-handoff-document
title: "Handoff Document — Revisor Contratual IA: review OAB compliance pré-launch v0.2.0"
project: revisor-contratual
version: "1.0.0"
last_updated: "2026-05-14"
authored_by: "@pm Morgan (Trinity)"
audience: "Advogada externa Eric (review OAB compliance — AC-PRD-γ-05 BLOQUEANTE)"
status: ready-to-send
related_to:
  - "email-advogada-externa-template-2026-05-14.md"
  - "PRD-SP06-GAMMA v0.1.0 (Sprint 6 Bloco γ COMPLETE)"
  - "Versão técnica em produção: v0.2.2 origin/main"
tags:
  - project/revisor-contratual
  - external-handoff
  - advogada-review
  - oab-compliance
---

# Revisor Contratual — Handoff para Review Jurídico Externo

> **Documento anexo ao email enviado por Eric Claudino (Orsheva) em {{DATA_ENVIO}}.**
> Versão técnica do produto em review: **v0.2.2** (Sprint 6 Bloco γ + δ + 6.1 hotfix + 6.2 middleware — todos publicados em origin/main).

---

## 1. Sumário Executivo

**Produto:** Revisor Contratual — SaaS B2B para escritórios de advocacia que atuam em revisional bancária.

**Propósito:** Reduzir o tempo de elaboração de peça revisional inicial de 3-8 horas (manual) para 10-15 minutos (review + ajustes da peça gerada por IA). Eliminar erros recorrentes em peças genéricas: citações incorretas de Súmulas, valor da causa mal calculado, cabeçalho fora do padrão CFOAB.

**Público-alvo:** Advogados(as) revisores(as) bancários — pessoa-DEVEDOR final user. Escritórios de advocacia pequenos e médios (B2B).

**Status técnico (2026-05-14):** Sprint 6 Bloco γ tecnicamente COMPLETE. Pipeline 9-etapas operacional. Peça revisional gerada via persona LLM Redator. PDF profissional rendered via WeasyPrint. Endpoints download autenticados. Auditoria LGPD §11 + §46 compliant. Versão v0.2.2 publicada em repositório `origin/main` aguardando aprovação OAB compliance externa **antes** de deploy em produção real.

**MVP scope:** Exclusivamente contratos **CDC Veículos Pessoa Física** (Credit Direct Consumer — financiamento de veículos para PF). Demais modalidades (CDC bens não-veiculares, CDC imobiliário, Cartão rotativo, Consignado, FIES) catalogadas como roadmap pós-MVP.

**Compliance declarada:**
- LGPD §11 (tratamento de dados pessoais) + §46 (segurança técnica)
- OAB Provimento 209/2021 CFOAB (uso ético de IA em peças)
- Decreto 6.306/2007 (IOF) + Lei 5.143/1966
- Súmulas STJ aplicáveis (297, 322, 530, 539, 296, 541, 382 — vault jurisprudencial estruturado)

---

## 2. Pipeline Técnico — 9 Etapas (descrição funcional)

| Etapa | Função | Output |
|-------|--------|--------|
| **1. Parsing PDF** | Extrai texto + estrutura do contrato PDF do banco (PyMuPDF4LLM + OCR fallback) | Texto estruturado + metadados |
| **2. Análise de Cláusulas** | Identifica cláusulas-chave (juros, capitalização, IOF, comissão de permanência, seguros adicionais) | Cláusulas mapeadas |
| **3. Cálculo Financeiro** | Recalcula evolução da dívida em Decimal (zero float), aplica Tabela Price ou SAC, identifica anatocismo | Valor diferença anatocismo + saldo recalculado |
| **4. Consulta BACEN** | Busca taxa média BACEN (SGS) na data de assinatura do contrato — comparativo Súmula 296 | Taxa BACEN histórica + comparação |
| **5. Vault Jurisprudencial** | Busca híbrida (vec + BM25) em base STJ/STF jurisprudência (Súmulas, Temas Repetitivos) | Documentos jurídicos recuperados + IDs traceable |
| **6. Personas LLM (3 paralelas)** | Advogado LLM (tese jurídica) + Economista LLM (análise financeira) + Juiz LLM (verdict final APROVADO/RISCO/REJEITADO) | Fragments JSON estruturados |
| **7. Persona Redator Revisional (Sprint 6 Bloco γ)** | LLM redige peça revisional formal em 8 seções CFOAB Provimento 209/2021 | Peça revisional estruturada |
| **8. Render PDF WeasyPrint** | Render template HTML+CSS (tokens OrSheva 7, tipografia Manrope sans + Fraunces serif, fontes self-hosted LGPD §46) | PDF profissional A4 |
| **9. Audit Chain HMAC** | Registro estruturado de cada evento em audit.jsonl com hash encadeado (entry_hash + previous_entry_hash) | Trilha auditável imutável |

**Trade-off de transparência:** etapas 6 e 7 envolvem LLMs (modelos de linguagem de grande porte). Por isso o sistema implementa 3 camadas de defesa contra hallucination (próxima seção).

---

## 3. Três Camadas Anti-Hallucination

Reconhecemos que LLMs podem inventar citações ou fabricar Súmulas. O sistema implementa três camadas de defesa:

### Camada 1 — Pydantic strict schema (forbid extra fields)

Toda saída de LLM é validada contra um schema Pydantic com `extra='forbid'`. Se o modelo retornar campo inventado, a validação falha e o sistema rejeita o output. Citações textuais do contrato exigem mínimo de 10 caracteres literais para aceitar.

### Camada 2 — Vault-restricted citation IDs

A peça revisional só pode citar Súmulas e Temas Repetitivos cujos IDs estejam presentes no vault de jurisprudência do projeto (atualmente ~600 STJ + ~58 STF SV pré-curados). Citações fora do vault são rejeitadas em validação cross-reference contra `audit_payload["vault"]["docs_recuperados"]`.

### Camada 3 — NLI semantic validator (em hardening)

Validador semântico Natural Language Inference (NLI) que verifica se a fundamentação invocada pela tese realmente é entailment dos documentos recuperados do vault. Esta camada está **parcialmente implementada** — atualmente como hook estrutural, com integração real do modelo NLI catalogada como tech debt (TD-SP07-NLI-HYBRID-REAL para próxima sprint).

**Risco residual:** Mesmo com 3 camadas, não há garantia 100% contra hallucination. Por isso o disclaimer obrigatório embute orientação de revisão humana antes de protocolo (Seção 6).

---

## 4. Exemplos de Output (anexos)

{{N_PECAS_ANEXADAS}} peças revisionais reais geradas pelo sistema acompanham este handoff:

| Anexo | Caso | Veredito Juiz | Observação |
|-------|------|---------------|------------|
| {{ANEXO_1}} | Contrato CDC veículo PF — anatocismo claro | APROVADO_100 | Peça revisional completa (8 seções) |
| {{ANEXO_2}} | Contrato CDC veículo PF — borderline | APROVADO_COM_RISCO_HITL | Peça com seção adicional "Pontos de Atenção" |

**Anonimização aplicada:** nome do cliente, CPF, endereço, hash do contrato e quaisquer dados identificáveis foram substituídos por placeholders `[ANONIMIZADO]`. Manteve-se intacta a estrutura, fundamentação jurídica, cálculos financeiros e citações.

---

## 5. Limitações Conhecidas

Para transparência total no review:

- **MVP exclusivo CDC Veículos PF.** Outras modalidades não cobertas nesta versão (catalogadas como roadmap).
- **Peça é "first draft".** Não substitui revisão de advogado(a) humano(a). Todo PDF gerado contém disclaimer explícito (Seção 6).
- **LLM inference variability.** Mesmo input pode gerar outputs ligeiramente diferentes em runs distintas (temperatura > 0). Por isso o pipeline é determinístico até a etapa 6, e o Juiz LLM serve como filtro final.
- **Dependência de API externa LLM.** Modelo BYOK (escritório fornece sua própria chave). Sistema não armazena dados do cliente fora do ambiente local.
- **Camada 3 NLI semantic validator parcialmente implementada.** Em hardening, catalogada como TD-SP07.
- **Cross-endpoint header consistency Sprint 6.3 backlog.** Não afeta peças geradas — apenas comportamento HTTP de erro.

---

## 6. LGPD + Disclaimer OAB embutido

### LGPD §11 + §46 compliance

- Execução 100% on-premise (zero cloud para dados de contrato)
- Operador LGPD: Eric Claudino (Orsheva)
- Cliente-escritório: agente de tratamento (LGPD Art. 5º)
- Audit chain HMAC: registro estruturado de cada evento, hash encadeado, payload com SHA256 do PDF (não conteúdo cleartext)
- Retention temp files: chmod 0o600 + auto-delete pós-download
- Retention audit: 90 dias documentado

### Disclaimer obrigatório embutido em toda peça gerada

```
Este documento é insumo técnico-jurídico gerado por inteligência artificial
via Revisor Contratual SaaS BYOK. A IA NÃO substitui a responsabilidade
técnica do(a) advogado(a) habilitado(a) que assinará e protocolará a peça.
Revisão jurídica humana é obrigatória antes de qualquer submissão judicial.
Conformidade: OAB Provimento 209/2021 + Resolução CFOAB ética IA jurídica.
```

**Solicitação de review:** este disclaimer está adequado? Há ajustes que você recomendaria à luz do Provimento 209/2021 CFOAB?

---

## 7. Questões para Review (5 perguntas estruturadas)

Para facilitar a entrega do parecer, segue lista estruturada das questões centrais:

### Q1 — Boas práticas OAB na peça gerada

A peça revisional gerada (anexos) respeita as boas práticas OAB em termos de fundamentação jurídica, citação de Súmulas STJ, linguagem técnica processual adequada e estrutura formal CFOAB? Há deficiências graves?

### Q2 — Qualidade jurídica substantiva

Analisando os 2 exemplos anexados, a tese jurídica (Camara 1 — Pydantic) é coerente? As citações de Súmulas (Camada 2 — vault) são corretamente aplicadas ao caso? O valor da causa está calculado dentro do que se espera tecnicamente?

### Q3 — Disclosures necessários ao usuário final

Quais avisos legais o sistema DEVE exibir ao advogado(a) revisor(a) antes de ele(a) utilizar a peça? O disclaimer embutido (Seção 6) é suficiente? Há cláusulas adicionais que você recomendaria (limitação de responsabilidade do fornecedor, ressalvas sobre AI-generated content, declarações específicas Provimento 209/2021, etc.)?

### Q4 — Enquadramento "assistive AI" — está claro?

O sistema está corretamente posicionado como assistivo (não substitutivo)? Há melhorias específicas que você recomendaria na comunicação ou na interface (UX) para reforçar esse enquadramento ético? O texto do disclaimer atual transmite essa mensagem com força suficiente?

### Q5 — Riscos éticos não-cobertos

Há riscos éticos OAB que o sistema atualmente NÃO endereça e que você recomendaria endereçar pré-launch? (Ex: captação de clientela, mercantilização da advocacia, sigilo profissional, conflito de interesses, publicidade vedada, etc.)

---

## 8. Formato esperado do parecer

Sugestão de estrutura para a entrega:

```markdown
# Parecer — Revisor Contratual IA OAB Compliance Review (v0.2.0)

## Veredito Final
[ ] APROVADO — sistema pode prosseguir para launch sem modificações
[ ] APROVADO COM RESSALVAS — listar ressalvas que devem ser endereçadas no roadmap
[ ] NEEDS CHANGES — listar findings bloqueantes que devem ser endereçados pré-launch

## Findings (se houver)
- Finding 1: [descrição] — Severidade: [CRÍTICO/ALTO/MÉDIO/BAIXO] — Recomendação: [...]
- Finding 2: [...]

## Respostas Q1..Q5
[Respostas estruturadas à Seção 7]

## Recomendações adicionais
[Pontos não cobertos pelas Q1..Q5 que você considera relevantes]

## Disclaimer profissional
[Sua ressalva como advogada — escopo do parecer, dados analisados, limitações]
```

Formato: `.md`, `.pdf` ou `.docx` — qualquer um serve. Eric arquivará em `governance/legal/advogada-review-peca-revisional-{{DATA_REVIEW}}.md` (caminho referenciado em AC-PRD-γ-05 do PRD).

---

## 9. Próximos passos após seu parecer

| Veredito seu | Ação Eric |
|--------------|-----------|
| APROVADO | Deploy v0.2.0 em produção real + comunicação aos escritórios-cliente piloto |
| APROVADO COM RESSALVAS | Implementar ressalvas como Sprint 6.3 backlog + deploy condicional |
| NEEDS CHANGES | Bloquear deploy, abrir tickets de correção, re-review pós-fix |

Em qualquer cenário, seu parecer será arquivado como parte da governança LGPD/OAB do projeto e referenciado em audit trail.

---

## 10. Contato técnico

- **Eric Claudino** (fundador Orsheva, operador LGPD): `{{EMAIL_ERIC}}` / `{{TELEFONE_ERIC}}`
- **Repositório técnico** (privado — acesso sob NDA se desejado): disponível mediante solicitação
- **Documentação PRD completa** (Sprint 6 Bloco γ): disponível mediante solicitação
- **Auditoria de código** (Smith adversarial reviews Sprints 6.x): disponível mediante solicitação

---

*Documento gerado em 2026-05-14 por @pm Morgan (Trinity) — Revisor Contratual SaaS Orsheva.*
*Baseado integralmente em PRD-SP06-GAMMA v0.1.0 + Sprint 6.x COMPLETE origin/main. No Invention (Constitution Art. IV LMAS framework).*
