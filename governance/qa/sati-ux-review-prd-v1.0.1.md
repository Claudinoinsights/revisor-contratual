---
type: tribunal-review
title: "Sati — Revisão UX do PRD v1.0.1 (Tribunal Severo, primeiro reviewer)"
project: revisor-contratual
reviewer: "@ux-design-expert (Sati)"
date: "2026-05-01"
artefato_revisado: "prd/prd-v1.0.1.md + prd/integrations-detail-v1.0.md"
predecessor_handoff: "H-S01-E1.1-pm2sat2"
tags:
  - project/revisor-contratual
  - tribunal-severo
  - ux-review
  - sati
---

# Revisão UX do PRD v1.0.1 — Tribunal Severo (Sati, primeiro reviewer)

## 🎭 Persona empática usada na revisão

**Dr. Ricardo** — advogado consumerista bancário em Salvador-BA, 38 anos, atende escritório com 15-30 contratos/mês, hardware: laptop Dell Inspiron 16GB. Cenário-estresse: sexta-feira 17h, cliente acabou de chegar, contrato de Honda Civic 2022, prazo de protocolo: segunda 8h. Ele tem que **confiar** no sistema para gerar petição com base sólida e protocolar sem retrabalho.

Atravessei a jornada inteira na pele dele — encontrei 11 pontos onde a UX trava ou exige esforço cognitivo desnecessário.

---

## 📋 VEREDICTO formato Ordem 8

```
[@ux-design-expert · Sati] — review etapa 1.1
VEREDICTO: PASS-COM-RESSALVA
EVIDÊNCIAS: 11 lacunas pontuais com FR-ID + linha + exemplo concreto (abaixo)
RESSALVAS / FALHAS: 11 (5 alta prioridade, 6 média)
RECOMENDAÇÃO: continuar → Smith para adversarial review;
              EM PARALELO recomendo Morgan criar adendo "UX Spec Detalhado v1.0"
              antes de Aria começar ADRs (não-bloqueante mas crítico para Aria)
```

---

## 🔍 Evidências (11 lacunas concretas)

### 🔴 ALTA prioridade (impacto direto na confiabilidade percebida do produto)

#### EV-01 — Painel HITL sem detalhamento crítico (FR-JUIZ-02 + Seção 8.2)

**Linha do PRD:** 287-291, 451-452 (FR-JUIZ-02 + Seção 8 4b)

**Problema:** O Painel HITL é o **momento mais crítico de confiança** do sistema (Juiz IA está em dúvida — humano decide), mas o PRD trata como genérico:
- "3 botões: Aprovar com Risco, Solicitar Recálculo, Abortar"
- "textarea justificativa obrigatória (≥20 chars)"

**Falta absolutamente:**
- Como visualizar **as razões C1/C2/C3 com scores** (PRD diz "razões de risco" mas não como)
- Microcopy de cada botão (texto exato, não nome interno)
- Hierarquia visual (qual botão é destrutivo? qual é seguro?)
- Placeholder do textarea (mínimo 20 chars é arbitrário sem contexto)
- O que acontece se usuário clicar Aprovar mas com justificativa "ok"? AC ≥20 chars passa mas semantically vazio
- Audit log do clique deve incluir quê? (já em FR-JUIZ-03 mas UX não articula)

**Impacto:** Dr. Ricardo, sob pressão, vai clicar "Aprovar com Risco" e digitar "ok ok ok ok ok" (passa AC ≥20 chars) — sistema emite petição com risco oculto.

**Recomendação:**
- Mostrar BadgeAderencia visível (ex: "Aderência: 78% — Risco: Médio") com tooltip explicando cada score C1/C2/C3
- Cada botão com cor + ícone + microcopy explícito (proposta abaixo em EV-09)
- Textarea com placeholder contextual: "Justifique sua escolha (ex: 'Aprovo apesar do risco porque a 3ª Câmara TJBA tem precedente favorável não indexado no vault — caso XX/2024')"
- Validação semântica: rejeitar texto repetitivo (regex ou similaridade)

---

#### EV-02 — Página Processamento sem ETA visível (Seção 8.1, FR-PARSE/CALC/RAG/TESE/JUIZ)

**Linha do PRD:** 448 (Seção 8.1 etapa 3) + NFR-PERF-01 (linha 361-364)

**Problema:** Latência alvo é "≤180s/contrato" — mas Seção 8.1 só diz "barra de progresso + log dos passos". Sob processamento de 2-3 minutos:

- Aos **30s** Dr. Ricardo pensa: "está rodando"
- Aos **90s**: "isso travou?"
- Aos **120s**: vai abrir o terminal pra ver se Ollama morreu
- Aos **180s**: cancelou, refresh F5, perde tudo

**Falta:**
- ETA dinâmica por etapa ("Análise jurisprudencial — restam ~45s")
- Indicador visual de "vivo" (spinner animado, não barra estática)
- Botão de cancelar (com confirmação "perder progresso?")
- Log expansível mas com microcopy não-técnico (não "Ollama loading sabia-7b:q4_K_M" mas "Ativando análise inteligente")

**Impacto:** Frustração + abandono em ~30% dos casos sob latência ≥120s.

**Recomendação:** detalhar Seção 8.1 etapa 3 com ETA por etapa, spinner por subprocesso, botão Cancelar.

---

#### EV-03 — Página Resultado sem preview, sem hierarquia, sem "principal vs anexos" (FR-DELIV-01..05, Seção 8.1 etapa 4a)

**Linha do PRD:** 299-321 (FR-DELIV-01..05) + 450 (Seção 8.1 etapa 4a)

**Problema:** "download dos 5 deliverables" — mas advogado precisa **conferir antes de protocolar**. Cinco PDFs lado a lado é cognitivamente caro.

**Falta:**
- Hierarquia visual: a Petição é o deliverable principal (vai ao tribunal); Relatório/Comparativo/Parcelas são anexos técnicos; Recursos Processuais são modelos para uso futuro
- Preview inline embedded (PDF.js ou iframe) ANTES do download — Dr. Ricardo confere a tese sem baixar
- Cópia rápida das citações (`[id_doc:X]`) para usar no editor de texto local
- "Salvar todos em pasta local" (LGPD: não cloud — apenas filesystem)
- Indicação de hash da Petição visível ("Auditoria: hash sha256:abc123... [copiar]")

**Impacto:** Dr. Ricardo baixa 5 PDFs, abre cada um, descobre erro na 4ª, refaz.

**Recomendação:** mockup de Página Resultado com:
1. Card grande "Petição Inicial Revisional" (PRINCIPAL) com preview + download + hash
2. 4 cards menores (anexos)
3. Botão "Conferir Petição agora →" abre preview em modal
4. Footer: "Salvar todos os 5 documentos em [pasta]" + audit ID

---

#### EV-04 — WCAG/A11y NÃO MENCIONADO no PRD (NFR ausente — VAZIO crítico)

**Busca grep:** "wcag", "acessibil", "a11y" → **0 ocorrências no PRD principal**. Aparece apenas no handoff e na Seção 8.3 ("a11y" listado como "a detalhar com Sati").

**Problema:** Advogados como público têm percentual significativo de usuários ≥50 anos com declínio visual progressivo. Tabelas de amortização (FR-CALC-02, 360 linhas em PDF) são pesadelo para screen reader sem semântica adequada.

**Falta NFR explícito:**
- WCAG 2.1 AA mínimo (contraste 4.5:1 texto normal, 3:1 texto largo)
- Tabelas com `<th scope="row|col">` + `<caption>`
- Skip-links em tabelas longas
- Navegação completa por teclado (Tab + Enter + atalhos)
- Suporte a `prefers-reduced-motion` (transições)
- Alt-text em todos os ícones funcionais
- Cor NUNCA é única forma de comunicação (verde/amarelo/vermelho do Juiz precisa ícone + texto)

**Impacto:** Risco legal (Lei Brasileira de Inclusão exige acessibilidade em produtos de uso profissional) + exclusão de potenciais usuários.

**Recomendação:** adicionar **NFR-A11Y-01** ao PRD: "Sistema atende WCAG 2.1 AA mínimo. Lighthouse Accessibility score ≥90 em todas as páginas."

---

#### EV-05 — Configuração LLM_TIER apenas via .env (FR-TESE-02, sem UX)

**Linha do PRD:** 267-271 (FR-TESE-02)

**Problema:** "trocar tier requer apenas alterar `.env` e reiniciar Streamlit" — Dr. Ricardo NÃO vai abrir terminal e editar .env. Esse switch é invisível.

**Cenário real:**
- Sabia-7B Premium gera tese em 3min — Dr. Ricardo acha lento
- Não sabe que pode trocar para Qwen 7B Balanced (90s) ou Qwen 3B Lean (40s)
- Continua frustrado, talvez abandone

**Falta:**
- Página "Configurações Avançadas" com:
  - Toggle visual entre Tiers (cards comparativos: Latência/RAM/Qualidade)
  - Indicador atual ("Você está usando: Sabia-7B Premium")
  - Disclaimer: "Tier menor = mais rápido mas potencialmente menos preciso. Recomendado validar com 5 contratos antes de trocar."
- Botão "Testar este tier no próximo contrato" (sem reiniciar app)

**Impacto:** Feature poderosa fica enterrada → usuário não otimiza para seu hardware/uso.

**Recomendação:** adicionar **FR-CONFIG-01** ao PRD: "Página Configurações expõe LLM_TIER como toggle visual com comparativo de trade-offs."

---

### 🟡 MÉDIA prioridade

#### EV-06 — Microcopy de erros de upload genérico demais (FR-UPLOAD-01)

**Linha do PRD:** 176-180

**Problema:** "PDFs inválidos rejeitados em <2s com mensagem clara" — mas que mensagem?

**Casos não cobertos:**
- PDF protegido por senha → "Erro" ou "Remova a senha do PDF antes de enviar. [Como fazer no Adobe Acrobat →]"?
- >100MB → "Arquivo muito grande" ou "Limite 100MB. Seu arquivo: 247MB. [Como reduzir o tamanho do PDF? →]"?
- .DOCX por engano → "Apenas PDF aceito" ou "Você enviou .DOCX. [Converter para PDF agora? Ferramenta gratuita →]"?

**Recomendação:** definir 5-7 microcopies específicos para erros de upload comuns; PDF mostrar opção de auto-correção quando possível.

---

#### EV-07 — Página Inviabilidade sem terapia (Seção 8.1 etapa 4c)

**Linha do PRD:** 453-454

**Problema:** Quando aderência <70%, advogado fica frustrado (perdeu cliente potencial). Página atual: "relatório explicando por que aderência <70% + sugestões". Falta:

- Tom de empatia ("Não foi possível desta vez — vamos entender por quê")
- Ação concreta sugerida (não só "qual checagem falhou"):
  - "C1 falhou (taxa contratual = média BACEN)" → "Sugestão: verificar se há cláusulas abusivas além de juros (taxas, seguros, IOF)"
  - "C2 falhou (sem jurisprudência vinculante)" → "Sugestão: aguardar inclusão de novo Tema STJ ou expandir vault para outras UFs"
  - "C3 falhou (jurisdição sem precedente)" → "Sugestão: tese pode ser inovadora — considerar parecer manual"
- Opção "Salvar análise mesmo assim" (Relatório Contábil ainda é útil para acordo extrajudicial)

**Recomendação:** UX terapêutica + ações concretas + permitir export do laudo mesmo sem petição.

---

#### EV-08 — Página Outcomes pode não atingir AC ≤30s (FR-ML-01)

**Linha do PRD:** 326-328

**Problema:** "registro em ≤30s por outcome" — sem UX detalhado, isso é difícil:
- Listar petições, abrir cada uma, selecionar outcome, digitar valor, salvar = 90s+

**Falta:**
- Quick actions inline (botões WON/LOST/PENDING grandes na linha da lista)
- Bulk update (marcar 5 outcomes de uma vez se mesma decisão)
- Lembrete visual de outcomes pendentes >30 dias (notificação no header)
- Filtros (PENDING primeiro; por câmara; por relator)
- Auto-save ao mudar outcome (sem botão Salvar)

**Recomendação:** detalhar Seção 8 com UI de outcomes que cumpra AC ≤30s.

---

#### EV-09 — Microcopy do Painel HITL — proposta concreta (complementa EV-01)

**Tabela canônica de microcopy** (proposta para Morgan adicionar à Seção 8.3):

| Elemento | Microcopy proposto |
|----------|-------------------|
| Cabeçalho painel | "⚠️ Análise concluída com **{X}% de aderência**. Há ressalvas — sua decisão é necessária." |
| Resumo C1 | "📊 Cálculo matemático: divergência {Y}% vs taxa BACEN ({passa/falha})" |
| Resumo C2 | "⚖️ Jurisprudência vinculante: peso máximo {Z}/5 ({passa/falha})" |
| Resumo C3 | "🏛️ Jurisdição: {N} doc(s) de TJ{UF}/STJ/STF citado(s) ({passa/falha})" |
| Botão Aprovar | 🟧 "**Aprovar mesmo assim** — assumo o risco de {X}%" |
| Botão Recálculo | 🟦 "**Solicitar novo cálculo** — vou ajustar parâmetros" |
| Botão Abortar | 🟥 "**Abortar** — gerar Relatório de Inviabilidade" |
| Textarea label | "Justificativa da sua escolha (auditoria) *" |
| Textarea placeholder | "Ex: 'Aprovo apesar do risco porque a 3ª Câmara do TJBA tem precedente favorável (caso 0801234-XX.2024) ainda não indexado no sistema.'" |
| Counter | "{N}/20 caracteres (mínimo)" — vermelho se <20, verde se ≥20 |

---

#### EV-10 — Seção 9.6 NOVA: integrações sem UX correspondente

**Linha do PRD:** 510-525 (Seção 9.6 + integrations-detail-v1.0.md)

**Problemas:**
- **DataJud (fase 2):** quando entrar, precisa modal "Adicionar chave API CNJ" com link para [datajud-wiki.cnj.jus.br/api-publica/acesso/](https://datajud-wiki.cnj.jus.br/api-publica/acesso/) e instruções
- **Tema 1378 STJ alerta (FR-AUDIT-02):** PRD diz "notificação visual no Streamlit no próximo login" — mas COMO? Banner persistente top? Modal bloqueante? Card no dashboard?
- **UF do contrato:** form de upload pede UF — autodetecção via regex no PDF deveria ser tentada primeiro (Dr. Ricardo já está cansado, evitar input manual)
- **LLM_TIER toggle (já em EV-05)** — UX necessária

**Recomendação:** adicionar Seção 8.4 ao PRD: "UX de Integrações e Configurações" cobrindo cada integração ativa.

---

#### EV-11 — Componentes Atomic Design não identificados (Aria precisa para ADR de design system)

**Problema:** Aria vai criar ADR sobre design system na próxima etapa. Sem inventário Atomic Design pré-feito, ela vai improvisar. Eu (Sati) deveria fornecer baseline:

**Atoms identificados (mínimo viável):**
- BotaoConfirmar / BotaoAlerta / BotaoDestrutivo (variantes Streamlit)
- BadgeAderencia (verde ≥95% / amarelo 70-94% / vermelho <70%)
- ChipUF (selector visual com bandeira + sigla)
- ChipModalidade (VEICULO, IMOBILIARIO etc.)
- TagPesoVinculacao (5 estrelas visual)
- IconeFonte (STF, STJ, TJBA com cores oficiais)

**Molecules:**
- CardCitacaoJuridica (id_doc + ementa truncada + link "Ver completo")
- LinhaParcelaAmortizacao (Decimal-formatted, screen-reader friendly)
- AlertaLGPD (banner para configurações que tocariam cloud)
- BarraProgressoEtapa (atual/total + ETA dinâmica + spinner)
- TextareaJustificativaHITL (counter + placeholder contextual + validação semântica)
- CardDeliverable (título + preview + download + hash)

**Organisms:**
- TabelaAmortizacaoCompleta (com `<caption>` + `<th scope>` + skip-link)
- PainelHITL (3 botões + textarea + summary C1/C2/C3 + alerta de risco)
- ListaOutcomesPendentes (filtro + bulk update + quick actions)
- DownloadsDeliverables (1 principal + 4 anexos + copy citações)
- HeaderApp (logo + auth status + notificações + atalhos teclado)

**Templates:**
- TemplateUpload, TemplateProcessamento, TemplateResultado, TemplateHITL, TemplateInviabilidade, TemplateOutcomes, TemplateConfiguracoes

**Pages:** as 5 + 1 página de Configurações Avançadas (EV-05) + 1 Dashboard (home pós-login com cards de petições recentes)

**Recomendação:** adicionar Seção 8.5 ao PRD ou criar `prd/ux-spec-detail-v1.0.md` com este inventário.

---

## 🎨 Lacunas adicionais médias (não-bloqueantes — para futura iteração)

| Item | Onde |
|------|------|
| Sistema de notificações (toast?) não definido | Seção 8 |
| Empty state da Dashboard pós-login | Seção 8 |
| Loading skeleton (vs spinner) para tabelas | Seção 8 |
| Onboarding (primeira execução) — wizard | Seção 8 |
| Atalhos de teclado (Ctrl+U upload, Ctrl+L logout) | NFR-SEC + a11y |
| Tema escuro vs claro (preferencias OS) | Seção 8 |

---

## 📋 Recomendação Sati ao tribunal severo

**Veredito: PASS-COM-RESSALVA**

O PRD v1.0.1 tem fundação sólida e ACs numéricos rastreáveis — não é FAIL. Mas tem **11 lacunas concretas** onde a UX precisa de detalhamento ANTES da implementação. Não posso aprovar como PASS limpo porque dois pontos (EV-01 Painel HITL + EV-04 WCAG ausente) são **risco direto à confiabilidade legal e à inclusão do produto**.

**Caminho recomendado:**

1. ✅ **Continuar tribunal** — handoff para Smith fazer adversarial review (Smith pode confirmar/contestar minhas ressalvas + atacar outros vetores)
2. ⏸️ **EM PARALELO**, Morgan abre **PATCH v1.0.2** ou **anexo `prd/ux-spec-detail-v1.0.md`** endereçando:
   - EV-01 (Painel HITL detalhado com microcopy EV-09)
   - EV-04 (NFR-A11Y-01 — WCAG 2.1 AA mínimo)
   - EV-05 (FR-CONFIG-01 — Configurações Avançadas com toggle LLM_TIER)
   - EV-11 (Inventário Atomic Design para Aria poder ADR de design system)
3. 🔄 **Antes de Aria começar ADRs**, garantir que esses 4 pontos críticos estão resolvidos (os outros 7 podem ir para iteração v1.0.3 ou stories específicas)

---

## ✅ O que está BOM no PRD (reconhecimento)

Não posso ser só corretiva — Morgan fez trabalho sólido. O que está bem:

- **Visão em uma frase** (linha 46) está cristalina e cabe em uma respiração
- **Personas internas (3.2)** — Economista restaurado conforme vontade do owner; descrições com responsabilidade exclusiva clara
- **5 deliverables nomeados** (4.3) com FR específico para cada um (FR-DELIV-01..05)
- **ACs numéricos** em quase todos os FRs — Dr. Ricardo pode cobrar implementação
- **Itens [DADO-PENDENTE]** explicitamente flagados (sem invenção) — integridade preservada
- **Anexo de integrações (Seção 9.6)** mapeia cada repo a bloco+FR — Aria vai amar
- **Hard-fails bem definidos** (NFR-REL-02, FR-RAG-03, FR-TESE-01) — citação fantasma bloqueada, RAG vazio gera Inviabilidade não tese inventada

---

## 🔗 Referências usadas

- PRD: `prd/prd-v1.0.1.md` (623 linhas lidas inteiras)
- Anexo: `prd/integrations-detail-v1.0.md` (mapeamento integrações)
- Persona empática: P-USR-01 (linha 66-71 do PRD) extrapolada como "Dr. Ricardo"

---

*Sati, criando experiências que não traem o usuário sob pressão 🎨*
