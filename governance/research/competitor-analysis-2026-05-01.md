---
type: research
title: "Revisor Contratual — Análise de Concorrentes + Tema 1378 STJ"
project: revisor-contratual
author: "@analyst (Atlas)"
date: "2026-05-01"
purpose: "Resolver risco D-10 (escopo MVP) — validar mercado + identificar gap"
predecessor: "decisions/risk-analysis-13-decisions-2026-05-01.md"
tags:
  - project/revisor-contratual
  - research
  - competitor-analysis
  - market-validation
  - tema-1378-stj
sources_count: 18
---

# Análise de Concorrentes + Tema 1378 STJ

> **Missão:** validar D-10 (MVP CDC PF Veículos) com pesquisa de mercado real. Decidir: **manter, pivotar ou ajustar**.
>
> **Spoiler:** mercado existe, há gap real, mas há um divisor de águas: **Tema 1378 STJ** (afetado em 09/09/2025, ainda não julgado).

---

## ⚡ Veredicto Executivo

**Decisão sobre D-10: MANTER com PIVÔ ESTRATÉGICO de POSICIONAMENTO** + monitorar Tema 1378.

| Aspecto | Achado |
|---------|--------|
| Mercado existe? | ✅ **SIM** — JusCalc, CalculoJuridico têm 2.000+ advogados pagantes |
| Há concorrência direta? | 🟡 **Calculadoras tradicionais sim, IA-completas não** |
| Existe gap real? | ✅ **SIM** — ninguém faz "calc + RAG jurisprudencial + tese AI" integrado |
| Tema 1378 STJ é risco ou oportunidade? | ⚠️ **AMBOS** — depende do julgamento (pendente) |
| Posicionamento original (revisor IA) é defensável? | 🔄 **PRECISA AJUSTE** — não é "calculadora", é "revisor com IA fundamentada" |

---

## 🚨 Achado #1 — Tema 1378 STJ (CRÍTICO)

### O que é
**STJ afetou em 09/09/2025** (pendente de julgamento) recursos especiais paradigmas que vão definir:

> **(I)** Suficiência ou não da adoção das **taxas médias de mercado divulgadas pelo BACEN** ou de outros critérios previamente definidos como **fundamento exclusivo** para aferição da abusividade dos juros remuneratórios em contratos bancários.
>
> **(II)** (In)admissibilidade dos recursos especiais para rediscussão das conclusões dos acórdãos recorridos quanto à abusividade ou não das taxas, quando baseadas em **aspectos fáticos** da contratação.

### Por que é crítico para o Revisor Contratual

| Cenário do julgamento | Impacto no produto |
|----------------------|-------------------|
| **STJ decide: "BACEN é suficiente"** | 🟢 **OURO** — produto vira automatizado puro: comparar contrato vs BACEN → tese pronta. Demanda explode (advogados massificam revisional). |
| **STJ decide: "precisa análise circunstancial"** | 🔴 **REVERTE D-04** — Economista volta como persona obrigatória (análise macro contextual: ciclo Selic, atipicidade da taxa). Produto fica mais complexo. |
| **STJ decide caso a caso (modulação)** | 🟡 Produto precisa **ambos os caminhos** — feature flag entre "modo BACEN-only" e "modo análise circunstancial" |

### Quando será julgado?
**Indeterminado** — temas repetitivos costumam levar 1-3 anos do afetamento ao julgamento. Pode ser 2026, 2027 ou depois.

### Decisão Atlas
- **Construir produto inicialmente em "modo BACEN-only"** (D-04 mantido — 3 personas)
- **Arquitetar de forma que Economista possa ser adicionado como tool ou persona** se Tema 1378 exigir análise circunstancial
- **Adicionar entry no `bloco_observability/audit_log/`** para rastrear "mudanças jurisprudenciais críticas" (Tema 1378 entre elas)

### Fontes
- [Jusbrasil — Tema 1378 e Crefisa](https://www.jusbrasil.com.br/artigos/a-afetacao-do-tema-1378-no-superior-tribunal-de-justica-e-os-juros-da-crefisa/5395137808)
- [Migalhas — Repetitivo STJ critério abusividade](https://www.migalhas.com.br/depeso/440203/repetitivo-do-stj-e-criterio-de-abusividade-em-contrato-bancario)
- [TJMG — detalhes Tema 1378](https://www.tjmg.jus.br/portal-tjmg/jurisprudencia/recurso-repetitivo-e-repercussao-geral/detalhes-de-recurso-repetitivo-8ACC808B992B7C5E01992FDF9A4E4866-00.htm)

---

## 🏪 Achado #2 — Concorrentes Identificados (categorizados)

### Categoria A — Calculadoras Especializadas (concorrência direta no Bloco 4)

| Player | Foco | Diferencial | Pricing |
|--------|------|-------------|---------|
| **[CálculoJurídico (CJ)](https://calculojuridico.com.br/)** | Calculadora bancária + modelos editáveis | "3 modelos de revisional" + cálculo de débitos | Não revelado publicamente — assinatura |
| **[JusCálculos / JC Calc](https://www.jccalculos.com/)** | "2.000+ advogados pagantes" | Sistema completo de cálculos judiciais editáveis | Assinatura |
| **[JusCalc (Jusfy)](https://jusfy.com.br/juscalc/)** | Calculadora geral | Versões para aluguel, FGTS, alimentos, revisional | Assinatura |
| **[DRCalc](https://drcalc.net/juridico.asp)** | Cálculo de débitos | Simples, foco em correção monetária | Single purchase |
| **[SOS Cálculos](https://www.soscalculos.com.br/)** | Plataforma cálculos jurídicos e financeiros | Módulos especializados | Assinatura |

**Análise:** **Mercado consolidado** para a parte de **CÁLCULO**. CJ e JusCalc dominam.

### Categoria B — Plataformas Jurídicas com Modelos (concorrência parcial)

| Player | Foco | Diferencial | Pricing |
|--------|------|-------------|---------|
| **[EasyJur](https://easyjur.com/)** | Modelos de petição + blog | Modelos editáveis, focado em automação documental | Não revelado |
| **[ADVbox](https://blog.advbox.com.br/)** | Modelos + gestão escritório | Software de gestão jurídica completo | Assinatura |

**Análise:** **Modelos templated** — não geram tese personalizada baseada em jurisprudência específica do caso.

### Categoria C — IA Jurídica AI-First (concorrência futurista)

| Player | Foco | Diferencial | Pricing |
|--------|------|-------------|---------|
| **[Enter](https://www.getenter.ai/)** | **Defesa de bancos** (lado contrário!) | IA Agents para contencioso de massa, R$2bi valuation, US$5,5M Sequoia | Enterprise B2B |
| **[Jusbrasil](https://www.jusbrasil.com.br/)** | Pesquisa + IA em todos os planos (2026) | Maior LegalTech LatAm, base massiva de jurisprudência | R$ 39-499/mês |
| **[Linte](https://linte.com/)** | Gestão processos + contratos com IA | Documentos, contratos, automação | Não revelado |

**Análise CRÍTICA:**
- **Enter está do LADO OPOSTO** — defende bancos (Nubank, BMG, C6, Inter). **NÃO é concorrente direto** — é "inimigo" estratégico que advogados de consumidor querem combater.
- **Jusbrasil é busca + IA generalista**, não revisor especializado.
- **Linte é gestão**, não revisor.

### Categoria D — Modelos Templates + Blog (não-software)

| Player | Foco | Diferencial |
|--------|------|-------------|
| [Modelo Inicial](https://modeloinicial.com.br/) | Banco de petições | Templates por tema |
| [SEDEP](https://www.sedep.com.br/) | Modelos de petições | Repositório clássico |

**Análise:** Concorrência baixa — vende template, não solução.

---

## 🎯 Achado #3 — GAP DE MERCADO IDENTIFICADO

### O que existe hoje
```
Advogado precisa fazer revisional bancária:
1. Vai no CJ/JusCalc → faz cálculo Price vs BACEN     [resolvido por concorrentes]
2. Pesquisa jurisprudência manualmente → STJ, TJ-MG    [trabalho manual]
3. Escreve tese + petição                              [usa modelo do EasyJur/ADVbox]
4. Revisa, ajusta, protocola                           [trabalho manual]
```

### O que NINGUÉM faz hoje
```
Sistema integrado:
1. Upload contrato PDF
2. Cálculo automático Price vs BACEN (via tool determinística)
3. RAG jurisprudência STJ/TJ-{UF} filtrado por jurisdição → top docs vinculantes
4. LLM gera tese fundamentada em jurisprudência específica recuperada
5. Juiz Revisor IA valida 100% aderência matemática + jurisprudencial
6. Petição final pronta com [Súmula 539 STJ], [Tema 247 STJ], [TJMG ementa Y]
```

**Esse é o produto Revisor Contratual.** Ninguém tem hoje.

### Posicionamento defensável
- **NÃO é calculadora** (CJ ganha esse jogo — 2.000+ usuários)
- **NÃO é repositório de modelos** (EasyJur/ADVbox dominam)
- **NÃO é busca de jurisprudência** (Jusbrasil domina)
- **É: revisor end-to-end com IA fundamentada em jurisprudência local + cálculo determinístico**

---

## 💰 Achado #4 — Pricing de Mercado (referência)

### Custo de uma ação revisional (lado advogado/cliente)
**R$ 1.500 a R$ 10.000** por ação (depende complexidade, valor envolvido, perícia) — fonte: [calculojuridico.com.br](https://calculojuridico.com.br/como-calcular-emprestimos-financiamentos/)

### Pricing de SaaS jurídico BR (referência geral)
- **Jusbrasil:** R$ 39-499/mês (planos basic → enterprise)
- **CJ / JusCalc / EasyJur:** R$ 100-400/mês (estimativa não-confirmada)
- **Linte / Enter:** Enterprise (não revelam — provavelmente R$ 2k-20k+/mês)

### Estimativa de pricing viável para Revisor Contratual
- **Solo advogado (foco MVP):** R$ 200-500/mês
- **Pequeno escritório (3-10 advogados):** R$ 800-2.000/mês
- **Por ação (modelo alternativo):** R$ 50-150 por revisional gerada (cliente paga R$ 1.500-10k para cliente final → margem confortável)

> ⚠️ Pricing definitivo deve vir de `@mifune` em fase 2. Esses são chutes de Atlas baseados em referencial.

---

## 🟢 Demanda real comprovada

### Sinais positivos
1. **80% dos financiamentos veículos usam Tabela Price** ([CalculoJuridico](https://calculojuridico.com.br/calculos-bancarios/)) → corpus enorme de contratos revisáveis
2. **CJ tem 2.000+ advogados pagantes** → mercado validado
3. **Súmula 539 STJ + Tema 247 + STF Súmula 121** → jurisprudência rica e estável
4. **Tribunais têm milhares de ações revisionais ativas** → demanda contínua
5. **Tema 1378 STJ** vai re-aquecer o mercado independente do resultado

### Sinais negativos
1. **Selic em queda** (~10-12% em 2026) reduz divergência matemática vs taxas BACEN → menos "ganhos" cristalinos
2. **STJ Súmula 539 + Tema 247** já reduziram facilidade de provar anatocismo
3. **Calculadoras maduras** (CJ, JusCalc) já capturam parte do valor

### Balanço
**🟢 Demanda existe e é estável.** Risco de saturação está MITIGADO pela diferenciação proposta (RAG + tese AI fundamentada, não só cálculo).

---

## 📋 Recomendação Atlas Final para D-10

### MANTER MVP CDC PF Veículos COM ajustes:

1. **Posicionamento:** "Revisor de contrato com IA fundamentada em jurisprudência local" — **não competir com calculadoras**.

2. **Diferencial competitivo claro:**
   - Cálculo determinístico (já fazem)
   - **+ RAG STJ/TJ-{UF} filtrado por jurisdição (NOVIDADE)**
   - **+ LLM PT-BR jurídico (Sabia/Qwen) gerando tese fundamentada (NOVIDADE)**
   - **+ Validação Juiz IA com 100% aderência ou aborta (NOVIDADE — auditabilidade)**
   - + Petição pronta com citações rastreáveis

3. **Monitorar Tema 1378 STJ:**
   - Adicionar tarefa em backlog: "Acompanhar julgamento Tema 1378 STJ" (Atlas pode rodar `*loop` mensal)
   - Arquitetar produto preparado para ambos os cenários (manter Economista como tool latente, não persona)

4. **Validação humana ainda recomendada (Eric):**
   - Conversar com 3-5 advogados-piloto (sugestão: rede do Eric + advogados especializados em DIREITO DO CONSUMIDOR BANCÁRIO MG)
   - Perguntas-chave: (a) Hoje, quanto tempo gasta numa revisional? (b) Pagaria R$300-500/mês por automação? (c) Qual a maior dor: cálculo, jurisprudência, ou redação?

---

## 🎯 Conclusão sobre D-10

| Aspecto | Veredicto |
|---------|-----------|
| **Risco "mercado saturado"** | 🟢 MITIGADO — gap real existe na integração calc+RAG+IA |
| **Risco "Selic baixa reduz demanda"** | 🟡 PARCIAL — contratos antigos com Selic alta ainda revisáveis; Tema 1378 pode reverter |
| **Risco "Súmula 539 dificulta anatocismo"** | 🟡 PARCIAL — abusividade absoluta substitui anatocismo como tese principal |
| **Risco "demanda baixa"** | 🟢 MITIGADO — 2.000+ advogados em CJ + 80% contratos veículos usam Price |
| **Risco "Tema 1378 STJ"** | ⚠️ MONITORAR — pode reverter D-04 ou validar produto |

**D-10 promovida de 🔴 ALTA para 🟡 MODERADA** com mitigações arquiteturais.

---

## 🔗 Fontes Consultadas

### Tema 1378 STJ
- [Jusbrasil — Tema 1378 STJ Crefisa](https://www.jusbrasil.com.br/artigos/a-afetacao-do-tema-1378-no-superior-tribunal-de-justica-e-os-juros-da-crefisa/5395137808)
- [Migalhas — Repetitivo STJ abusividade](https://www.migalhas.com.br/depeso/440203/repetitivo-do-stj-e-criterio-de-abusividade-em-contrato-bancario)
- [TJMG — Detalhes Tema 1378](https://www.tjmg.jus.br/portal-tjmg/jurisprudencia/recurso-repetitivo-e-repercussao-geral/detalhes-de-recurso-repetitivo-8ACC808B992B7C5E01992FDF9A4E4866-00.htm)
- [Marques Silva — Revisão Bancária 2026](https://msadv.adv.br/revisao-de-contrato-bancario/)
- [Barbieri Advogados — Ação Revisional](https://www.barbieriadvogados.com/acao-revisional-de-contratos-bancarios-aspectos-juridicos-e-praticos/)

### Concorrentes — Calculadoras
- [Cálculo Jurídico (CJ)](https://calculojuridico.com.br/)
- [JC Cálculos / JusCalculos](https://www.jccalculos.com/)
- [Jusfy JusCalc](https://jusfy.com.br/juscalc/)
- [DR Calc](https://drcalc.net/juridico.asp)
- [SOS Cálculos](https://www.soscalculos.com.br/)

### Concorrentes — Modelos
- [EasyJur](https://easyjur.com/)
- [ADVbox](https://blog.advbox.com.br/)
- [Modelo Inicial](https://modeloinicial.com.br/)
- [SEDEP](https://www.sedep.com.br/)

### Concorrentes — IA Jurídica
- [Enter LegalTech](https://www.getenter.ai/)
- [Linte — Melhor IA contratos 2026](https://linte.com/qual-e-a-melhor-ia-para-contratos-juridicos-em-2026)
- [Jusbrasil — Conjur 2026 IA em todos planos](https://www.conjur.com.br/2026-abr-13/ferramenta-de-ia-passa-a-integrar-todos-os-planos-do-jusbrasil/)
- [Tecnovix — Enter Review 2026](https://tecnovix.com.br/startups/enter)
- [Brazil Journal — Enter Sequoia](https://braziljournal.com/enter-usa-ai-para-desafogar-acoes-trabalhistas-e-de-consumidores-e-ja-atraiu-o-sequoia/)

### Mercado e Pricing
- [Startups.com.br — 13 LegalTechs BR](https://startups.com.br/negocios/dia-do-advogado-13-legaltechs-brasileiras-que-estao-transformando-o-setor-juridico/)
- [ABES — Tendências Jurídicas 2026](https://abes.org.br/en/integracao-tecnologica-no-setor-juridico-5-tendencias-para-2026/)

---

*Atlas, mapeando o terreno antes da batalha — 🔎*
