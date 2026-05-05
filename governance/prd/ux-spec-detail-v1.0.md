---
type: prd-annex
title: "Revisor Contratual — Anexo UX Spec Detail v1.0"
project: revisor-contratual
version: "1.0"
parent_doc: "prd/prd-v1.0.2.md"
owner: "@pm (Morgan) — com baseline de Sati EV-09 + EV-11"
date: "2026-05-01"
predecessor_review: "qa/sati-ux-review-prd-v1.0.1.md"
purpose: "Inventário Atomic Design + microcopy completo + estados de página + UX para 7 EV-IDs MÉDIA da Sati"
tags:
  - project/revisor-contratual
  - prd-annex
  - ux-spec
  - atomic-design
  - microcopy
  - accessibility
---

# Anexo UX Spec Detail v1.0 — Revisor Contratual

> **Propósito:** consolidar a baseline de Atomic Design proposta por Sati (EV-11) + tabela canônica de microcopy (EV-09) + estados detalhados de cada página + UX para as 7 EV-IDs MÉDIA da Sati que foram adiadas do PRD principal para este anexo.
>
> **Para quem:** Aria (vai criar ADR de design system referenciando este inventário) + Neo (vai implementar) + Sati (refinará detalhamento visual em fase de implementação).

---

## 1. Inventário Atomic Design (Sati EV-11)

### 1.1 Atoms (componentes base reutilizáveis)

| Componente | Propósito | Estados | A11y |
|-----------|-----------|---------|------|
| **BotaoConfirmar** | Ação primária construtiva (verde) | default, hover, active, focus, disabled, loading | aria-label, focus-visible ring 2:1, mín 44×44px touch target |
| **BotaoAlerta** | Ação destrutiva ou alta-consequência (laranja) | idem | idem + `aria-describedby` para tooltip de risco |
| **BotaoDestrutivo** | Cancelar/Abortar irreversível (vermelho) | idem | idem + confirmação obrigatória pré-execução |
| **BadgeAderencia** | Indicador visual de aderência do Juiz | verde ≥95%, amarelo 70-94%, vermelho <70% | ícone + texto além de cor (✅⚠️❌); contraste ≥4.5:1 |
| **ChipUF** | Selector de UF (27 opções) | default, selected, disabled | bandeira + sigla; teclado-navegável (←→) |
| **ChipModalidade** | Tag de modalidade contratual | VEICULO, IMOBILIARIO, CDC_GENERICO, CARTAO_ROTATIVO | ícone + texto |
| **TagPesoVinculacao** | 5 estrelas visual + valor numérico | 1★ a 5★ | aria-label "Peso de vinculação: {N} de 5" |
| **IconeFonte** | Logo/sigla + cor oficial do tribunal | STF, STJ, TJBA, TJSP, TJMG, etc. | alt-text + tooltip "Supremo Tribunal Federal" |
| **InputDecimal** | Campo monetário com formatação BR | default, focus, error, success | aria-invalid quando erro; `inputmode="decimal"`; lang="pt-BR" |
| **DatePickerBR** | Selector de data formato dd/mm/aaaa | idem | navegável por teclado; suporta `prefers-reduced-motion` |

### 1.2 Molecules (combinações simples)

| Componente | Composição | Estados |
|-----------|-----------|---------|
| **CardCitacaoJuridica** | IconeFonte + ementa truncada (max 200 chars) + link "Ver completo" + TagPesoVinculacao | default, expandido, copiado |
| **LinhaParcelaAmortizacao** | Decimal-formatado: parcela | saldo_inicial | juros | amortização | valor_parcela | saldo_final | normal, alternada (zebra), highlight ao hover |
| **AlertaLGPD** | Banner laranja com ícone + texto + botão "Saiba mais" | default, dismissed, persistente |
| **BarraProgressoEtapa** | Etapa atual/total + ETA dinâmica + spinner animado + botão Cancelar | running, paused, error, complete |
| **TextareaJustificativaHITL** | Textarea + counter visual + placeholder contextual + validação semântica anti-bypass | empty, valid (≥20 chars + diversidade ≥0.5), invalid_short, invalid_repetitive |
| **CardDeliverable** | Título + IconeFonte do tipo + preview (PDF embed) + download + hash sha256 + botão copiar hash | loading, ready, downloaded |
| **AlertaSessaoExpirando** | "Sua sessão expira em {N} dias" + botão "Estender" | normal, urgent (≤2 dias) |
| **SeletorLLMTier** (FR-CONFIG-01) | 3 cards comparativos: Lean | Balanced | Premium com Latência+RAM+Qualidade | default, current, hover |

### 1.3 Organisms (seções complexas)

| Componente | Composição | Notas A11y |
|-----------|-----------|------------|
| **TabelaAmortizacaoCompleta** | LinhaParcelaAmortizacao × N (até 360) | `<caption>` "Tabela de N parcelas, total R$ X" + `<th scope="col">` + skip-link "Pular tabela →" + summary no topo |
| **PainelHITL** | BadgeAderencia + 3 resumos C1/C2/C3 + 3 botões hierarquizados + TextareaJustificativaHITL + alerta de risco | hierarquia visual clara; botão Aprovar à direita (positivo); botão Abortar destacado em vermelho |
| **ListaOutcomesPendentes** | Filtros (status, câmara, data) + linhas com quick actions WON/LOST/PARTIAL inline + bulk update | virtualizar render se >100 linhas; teclado-navegável |
| **DownloadsDeliverables** | 1 CardDeliverable PRINCIPAL (Petição) + 4 secundários (Relatório/Comparativo/Parcelas/Recursos) + botão "Salvar todos em pasta local" + audit ID copiável | hierarquia: Petição em destaque (card grande) |
| **HeaderApp** | Logo + status auth (nome usuário) + AlertaSessaoExpirando + notificações (sino) + atalhos teclado | sticky no topo; `role="banner"` |
| **PainelRevisaoCFOAB** (FR-DELIV-06) | Preview embedded + checkbox "LI, CONFERI E ADOTO" + campos OAB+UF + botão "Gerar PDF" desabilitado até preencher | checkbox `aria-required="true"`; campos `aria-invalid` quando vazios |

### 1.4 Templates (layouts de página)

- **TemplateLogin** — formulário centralizado, footer "100% local · LGPD"
- **TemplateUpload** — área drag-and-drop + form com UF + data + valor (campos validados) + AlertaLGPD
- **TemplateProcessamento** — BarraProgressoEtapa fullscreen + log expansível + botão Cancelar
- **TemplateResultado** — header com aderência + DownloadsDeliverables + botão "Iniciar nova análise"
- **TemplateHITL** — PainelHITL fullscreen + botão "Voltar ao processamento"
- **TemplateInviabilidade** — Relatório explicativo + sugestões de ação + botão "Salvar laudo mesmo assim"
- **TemplateOutcomes** — ListaOutcomesPendentes + filtros + bulk update
- **TemplateConfiguracoes** — sidebar com seções (LLM/Backup/Auth/A11y) + SeletorLLMTier
- **TemplateRevisaoCFOAB** (FR-DELIV-06) — PainelRevisaoCFOAB fullscreen pré-emissão de qualquer peça

### 1.5 Pages (instâncias)

- `/` Login (TemplateLogin)
- `/dashboard` Home pós-login (cards de petições recentes + atalhos)
- `/upload` Upload (TemplateUpload)
- `/processamento` Processamento (TemplateProcessamento)
- `/resultado/{petition_hash}` Resultado (TemplateResultado)
- `/hitl/{petition_hash}` HITL (TemplateHITL)
- `/inviabilidade/{petition_hash}` Inviabilidade (TemplateInviabilidade)
- `/outcomes` Outcomes (TemplateOutcomes)
- `/configuracoes` Configurações Avançadas (TemplateConfiguracoes)
- `/revisao-cfoab/{petition_hash}` Revisão CFOAB (TemplateRevisaoCFOAB) — gate obrigatório antes de gerar PDF

---

## 2. Tabela Canônica de Microcopy (Sati EV-09)

### 2.1 Painel HITL (referência canônica para FR-JUIZ-02)

| Elemento | Microcopy |
|----------|-----------|
| Cabeçalho | "⚠️ Análise concluída com **{X}% de aderência**. Há ressalvas — sua decisão é necessária." |
| Resumo C1 (cálculo) | "📊 Cálculo matemático: divergência {Y}% vs taxa BACEN ({passa/falha})" |
| Resumo C2 (jurisprudência) | "⚖️ Jurisprudência vinculante: peso máximo {Z}/5 ({passa/falha})" |
| Resumo C3 (jurisdição) | "🏛️ Jurisdição: {N} doc(s) de TJ{UF}/STJ/STF citado(s) ({passa/falha})" |
| Botão Aprovar | 🟧 "**Aprovar mesmo assim** — assumo o risco de {X}%" |
| Botão Recálculo | 🟦 "**Solicitar novo cálculo** — vou ajustar parâmetros" |
| Botão Abortar | 🟥 "**Abortar** — gerar Relatório de Inviabilidade" |
| Textarea label | "Justificativa da sua escolha (auditoria) *" |
| Textarea placeholder | "Ex: 'Aprovo apesar do risco porque a 3ª Câmara do TJBA tem precedente favorável (caso 0801234-XX.2024) ainda não indexado no sistema.'" |
| Counter visual | "{N}/20 caracteres (mínimo)" — vermelho se <20, verde se ≥20 |
| Erro repetição | "Justificativa muito repetitiva ou genérica. Por favor, descreva o motivo concreto da decisão." |

### 2.2 PainelRevisaoCFOAB (referência canônica para FR-DELIV-06)

| Elemento | Microcopy |
|----------|-----------|
| Título | "Revisão e adoção da peça — última etapa antes do PDF" |
| Subtítulo | "A peça abaixo será assinada por você. Confira os fundamentos antes de adotar." |
| Checkbox label | "**LI, CONFERI E ADOTO** os fundamentos como meus, na qualidade de advogado responsável pela peça." |
| Campo nome | "Nome completo do advogado responsável *" |
| Campo OAB | "Número OAB (somente dígitos) *" |
| Campo UF | "UF da OAB *" (selector dos 27 estados) |
| Notas opcionais | "Notas adicionais ao texto (opcional, máx 500 chars)" |
| Botão | "Gerar PDF e finalizar" (desabilitado até checkbox + campos preenchidos) |
| Tooltip botão desabilitado | "Marque o checkbox e preencha sua OAB+UF para gerar a peça final." |
| Disclaimer footer | "Ao adotar esta peça, você assume responsabilidade profissional integral nos termos do art. 32 do Estatuto da OAB e Provimento CFOAB 205/2021." |

### 2.3 Erros de Upload (Sati EV-06 — adiada do PRD principal)

| Cenário | Microcopy |
|---------|-----------|
| PDF protegido por senha | "Este PDF está protegido por senha. Remova a senha no leitor de PDF e tente novamente. [Como fazer no Adobe Reader →]" |
| Arquivo > 100MB | "Arquivo muito grande ({X} MB). Limite: 100 MB. [Como reduzir o tamanho do PDF? →]" |
| Não é PDF (.docx, .jpg) | "Apenas arquivos PDF aceitos. Você enviou .{EXT}. [Converter para PDF agora? Ferramenta gratuita →]" |
| PDF corrompido | "Não conseguimos abrir este PDF. Talvez esteja corrompido — tente reabrir e salvar novamente no leitor de PDF." |
| PDF malicioso (JS embed) | "Este PDF contém scripts ou conteúdo executável que removemos por segurança. Versão sanitizada salva. Continuar?" |
| UF inválida | "Selecione uma UF válida (lista de 27 estados)." |
| Data fora da faixa | "Data fora da faixa permitida (1986–hoje). BACEN SGS não cobre datas anteriores." |
| Data futura | "Data de assinatura não pode ser futura. Verifique e tente novamente." |

### 2.4 Estados de Loading (Sati EV-02 — adiada do PRD principal)

| Etapa | Microcopy + ETA visível |
|-------|-------------------------|
| Parsing PDF | "Lendo o contrato... ~10 segundos" + spinner |
| Fetch BACEN | "Consultando taxa BACEN para {modalidade}, {mês}/{ano}... ~3 segundos" + spinner |
| RAG jurisprudência | "Buscando jurisprudência aplicável no STF, STJ e TJ{UF}... ~5 segundos" + spinner |
| Análise Economista | "Analisando contexto macroeconômico do contrato... ~30 segundos" + spinner |
| Geração tese (Advogado LLM) | "Redigindo a tese fundamentada... esta é a parte mais demorada (até 3 min)" + spinner + ETA dinâmica |
| Validação semântica | "Validando que cada citação reflete a tese real do precedente... ~10 segundos" + spinner |
| Validação Juiz | "Validando aderência matemática + jurisprudencial..." + spinner (rápido <1s) |
| Renderização PDF | "Gerando PDF final..." + spinner (rápido) |
| **Botão Cancelar visível em todas** | "Cancelar análise (perde progresso)" |

### 2.5 Página Inviabilidade — UX terapêutica (Sati EV-07 — adiada do PRD principal)

| Elemento | Microcopy |
|----------|-----------|
| Header | "Não foi possível desta vez — vamos entender por quê" |
| Razão C1 falhou | "📊 **Cálculo:** a taxa do contrato está alinhada com a média BACEN. Sem divergência matemática, não há base para revisão por juros abusivos. **Sugestão:** verificar se há outras cláusulas abusivas (taxas extras, seguros casados, IOF cumulativo)." |
| Razão C2 falhou | "⚖️ **Jurisprudência:** não encontramos precedente vinculante (peso ≥4) para este caso no vault atual. **Sugestão:** aguardar inclusão de novo Tema STJ ou expandir vault para outras UFs (CLI add_uf)." |
| Razão C3 falhou | "🏛️ **Jurisdição:** seu caso é em {UF} mas não temos precedente do TJ{UF} no vault. **Sugestão:** tese pode ser inovadora — considerar parecer manual para teste do mercado." |
| Botão | "Salvar Relatório Contábil mesmo assim (útil para acordo extrajudicial)" |
| Botão secundário | "Iniciar nova análise" |

### 2.6 Página Outcomes — UX para AC ≤30s (Sati EV-08 — adiada do PRD principal)

| Elemento | Microcopy |
|----------|-----------|
| Header | "Petições aguardando registro de outcome ({N} pendentes há >30 dias)" |
| Filtros | Status (PENDING / WON / LOST / PARTIAL / UNKNOWN) | UF | Câmara | Data |
| Quick action WON | 🟢 "Ganho" (botão grande inline) |
| Quick action LOST | 🟥 "Perdido" |
| Quick action PARTIAL | 🟧 "Parcial" |
| Quick action UNKNOWN | ⚪ "Sem info" |
| Bulk select | "Selecionar todas as {N} petições visíveis" |
| Bulk action | "Marcar selecionadas como [WON/LOST/PARTIAL/UNKNOWN]" |
| Auto-save indicator | "✅ Salvo automaticamente há {N}s" |

### 2.7 UX Integrações (Sati EV-10 — adiada do PRD principal)

| Integração | UX |
|-----------|-----|
| **DataJud config (fase 2)** | Modal "Adicionar chave API CNJ" com link para [datajud-wiki.cnj.jus.br/api-publica/acesso/](https://datajud-wiki.cnj.jus.br/api-publica/acesso/) + instruções passo-a-passo |
| **Tema 1378 STJ alerta (FR-MONITOR-01)** | Banner persistente vermelho no header até dismissed manualmente + modal explicativo ao clicar "Saiba mais" + sugestão de ações |
| **UF do contrato** | Form upload tenta autodetecção via regex no PDF (busca "Tribunal de Justiça do Estado de {X}") — selector manual como fallback |
| **LLM_TIER toggle** (FR-CONFIG-01) | Página Configurações Avançadas → seção LLM com SeletorLLMTier (3 cards comparativos) |

---

## 3. Estados de cada página (detalhamento Sati EV-02 expandido)

### 3.1 Estados padrão para todas as páginas

- **Empty state**: ícone grande + texto explicativo + CTA primário
- **Loading state**: skeleton placeholders (não spinner full-page) para listas; spinner inline para ações pontuais
- **Error state**: ícone erro + mensagem amigável + botão "Tentar novamente" + log expansível "Detalhes técnicos"
- **Success state**: feedback visual (toast 3s ou inline check) + próximo passo claro

### 3.2 Estados específicos da Página Resultado (Sati EV-03 detalhada)

- **Hierarquia visual**: Petição em card grande no topo (1 col); 4 anexos em cards menores em grid 2×2 abaixo
- **Preview inline**: Petição renderizada em iframe expansível (botão "Maximizar")
- **Cópia rápida**: cada citação `[id_doc:X]` na petição tem botão "Copiar citação" inline
- **Salvar todos**: botão fixo no footer "💾 Salvar 5 documentos em [pasta local]" + selector de pasta nativo do OS
- **Audit ID**: badge no footer "Audit: sha256:abc123... [copiar]"

---

## 4. Notas para Aria (próxima etapa — ADR de design system)

1. **Adotar Streamlit nativo** OU avaliar customização leve via CSS injetado (`st.markdown` com `<style>`)?
2. **Tokens de design**: cores oficiais dos tribunais (STF azul, STJ verde, TJBA dourado) + paleta de aderência (verde/amarelo/vermelho com WCAG 4.5:1)
3. **Tipografia**: serif para textos longos (Crimson Text, EB Garamond) + sans-serif para UI (Inter, Roboto)
4. **Espaçamento**: grid 8px base
5. **Ícones**: Lucide React via streamlit-lucide OU emojis nativos (mais leve)
6. **A11y framework**: validar Lighthouse ≥90 em CI (axe-core)

---

## 5. Referências

- Persona empática usada: P-USR-01 (linha 66-71 do PRD v1.0.2) — "Dr. Ricardo"
- Smith F-CRIT-01 → FR-DELIV-06 (PainelRevisaoCFOAB)
- Sati EV-01 → FR-JUIZ-02 estendido (PainelHITL com microcopy)
- Sati EV-04 → NFR-A11Y-01 (WCAG 2.1 AA + Lighthouse ≥90)
- Sati EV-05 → FR-CONFIG-01 (TemplateConfiguracoes)
- Sati EV-11 → este anexo (inventário completo)

---

*Morgan, descendo do estratégico ao detalhe que Aria vai precisar 📊*
