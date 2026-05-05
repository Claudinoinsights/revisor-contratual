---
type: risk-analysis
title: "Revisor Contratual — Análise de Risco das 13 Decisões"
project: revisor-contratual
author: "@analyst (Atlas)"
date: "2026-05-01"
predecessor: "decisions/decisions-consolidated-2026-05-01.md"
purpose: "Para cada decisão consolidada: o que é SÓLIDO (não vai atrapalhar) vs o que é RISCO (pode atrapalhar) + mitigação"
audience: ["Eric Claudino", "@architect (Aria)", "@smith (adversarial review)"]
tags:
  - project/revisor-contratual
  - risk-analysis
  - decisions
  - phase-0
---

# Análise de Risco das 13 Decisões

> **Critério de classificação:**
> - 🟢 **Sólido** (probabilidade de quebra <20%, baixo impacto se quebrar) — não vai atrapalhar
> - 🟡 **Moderado** (probabilidade 20-50% OU médio impacto) — atrapalha se materializar mas é gerenciável
> - 🔴 **Alto** (probabilidade >50% OU alto impacto) — pode descarrilhar fase de produção
>
> **Princípio:** decisão sem risco identificado é decisão mal analisada. Se eu disser "tudo OK", desconfie.

---

## ⚡ Sumário — Mapa de Calor

| # | Decisão | Risco geral | Item mais perigoso |
|---|---------|:----------:|---------------------|
| **D-01** | Arquitetura C | 🟢 Sólido | Streamlit em multi-user (raro no MVP) |
| **D-02** | 3 blocos novos | 🟢 Sólido | Over-engineering inicial |
| **D-03** | Decimal everywhere | 🟢 Sólido | Bugs de serialização Pydantic |
| **D-04** | Eliminar Economista | 🟡 **Moderado** | Pode descobrir tarde que análise macro era útil |
| **D-05** | Vault seed manual | 🟡 **Moderado** | Trabalho de curadoria pesado, scrapers em R |
| **D-06** | 4 fontes jurisprudência | 🟡 **Moderado** | Scrapers quebram quando portal muda layout |
| **D-07** | DataJud fase 2 | 🟢 Sólido | Cliente pedir estatística no MVP |
| **D-08** | LexML pré-cache | 🟢 Sólido | Cache stale após mudança legislativa |
| **D-09** | Descartar abjur | 🟢 Sólido | Perder metodologia jurimétrica de "score de êxito" |
| **D-10** | MVP CDC Veículos | 🔴 **Alto** | Mercado saturado + Selic baixa = pouca demanda |
| **D-11** | Hardware faseado | 🟢 Sólido | Eric resistir ao R$12-15k da workstation |
| **D-12** | UF inicial MG | 🟡 **Moderado** | Eric atender outro estado primeiro |
| **D-13** | Adiar business/brand | 🟡 **Moderado** | Validação com piloto-advogados fica fraca sem marca |

**Conclusão visual:**
- **8 decisões 🟢 sólidas** (61%)
- **4 decisões 🟡 moderadas** (31%) — exigem mitigação ativa
- **1 decisão 🔴 alta** (8%) — D-10 (escopo MVP) — **pede validação de mercado antes do code**

---

## D-01 — Arquitetura C (Híbrido Pragmático) — 🟢 Sólido

### ✅ O que NÃO vai atrapalhar
- **Streamlit** existe há 5+ anos, comunidade enorme, Eric já conhece
- **FastAPI** é padrão de mercado para APIs Python async — estável
- **RQ + Redis** é stack simples e funciona — usado por milhares de projetos
- **Migração para arquitetura B** (NiceGUI, vLLM, Dramatiq) é **incremental** sem reescrever tudo
- Cada componente tem alternativas drop-in se um falhar

### ⚠️ O que PODE atrapalhar
| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-------------:|:-------:|-----------|
| Streamlit não escala se Eric quiser 5+ advogados simultâneos | Baixa (MVP é solo) | Médio | Migrar UI para NiceGUI quando precisar (1-2 sprints) |
| FastAPI + Streamlit dupla = 2 processos = dupla deploy | Média | Baixo | Docker Compose já resolve |
| RQ não tem retry sofisticado como Dramatiq | Baixa | Baixo | Migrar para Dramatiq se observar perdas |

**Quebra-galho real?** Improvável. Foundation sólida.

---

## D-02 — 3 Blocos Novos (`bloco_contratos/`, `bloco_api/`, `bloco_observability/`) — 🟢 Sólido

### ✅ O que NÃO vai atrapalhar
- Cada bloco cura **uma fragilidade transversal documentada** (não é especulação)
- `bloco_contratos/` é só Pydantic — **trivial de implementar**
- `bloco_api/` reaproveita FastAPI (sem novo stack)
- `bloco_observability/` pode começar minimalista (só audit-log) e crescer

### ⚠️ O que PODE atrapalhar
| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-------------:|:-------:|-----------|
| **Over-engineering** — equipe gasta tempo em observability antes do MVP funcionar | Média | Médio | Implementar em ordem: contratos → api → observability (último) |
| Eric ver complexidade e desistir do scope | Baixa | Alto | Demonstrar valor de cada bloco com 1 exemplo de bug que ele evita |
| OpenTelemetry tem curva de aprendizado | Média | Baixo | Começar com `structlog` (90% do valor, 10% do esforço) |

**Quebra-galho real?** Não — risco principal é **pseudo-progresso** (gastar tempo em infra antes de função). Mitigação: priorizar.

---

## D-03 — Decimal Everywhere — 🟢 Sólido

### ✅ O que NÃO vai atrapalhar
- `decimal.Decimal` é stdlib Python — sem dependência externa
- Performance OK para nosso uso (~50-100ms para 360 parcelas — irrelevante)
- Resolve **vulnerabilidade legal definitiva** (perícia aceita o cálculo)

### ⚠️ O que PODE atrapalhar
| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-------------:|:-------:|-----------|
| **Bugs de serialização Pydantic** — converter Decimal ↔ str em fronteiras pode dar bug sutil | **Alta** | Médio | Centralizar conversão em helpers `bloco_contratos/decimal_helpers.py`; testes unitários obrigatórios |
| Devs novos esquecem regra e usam float em algum cálculo | Média | **Alto** (legal) | Linter custom (ruff rule) + code review obrigatório em qualquer arquivo `bloco_engine/ferramentas_calculo/` |
| Bibliotecas externas retornam float (`pandas`, `numpy`) | Alta | Baixo | Wrapper que converte na borda + Pydantic validator |

**Quebra-galho real?** Bugs sutis de serialização são prováveis mas detectáveis em CI. **Risco gerenciável**.

---

## D-04 — Eliminar Economista (3 Personas) — 🟡 Moderado

### ✅ O que NÃO vai atrapalhar
- Reduz latência total (-1 chamada LLM = -30 a -90s)
- Simplifica grafo LangGraph (menos arestas condicionais)
- 3 personas é o **mínimo viável** para o conceito state-machine + HITL

### ⚠️ O que PODE atrapalhar
| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-------------:|:-------:|-----------|
| **Descobrir tarde que análise macro contextual era importante** (ex: "essa taxa BACEN era atípica devido a ciclo de Selic em 2024") | **Média (40%)** | Médio | Voltar = adicionar **tool** chamada pelo Perito (não persona separada) — mais barato |
| Juiz Revisor pode rejeitar tese por falta de "porquê macroeconômico" — alguns juízes pedem | Média | Médio | A/B test: 30 contratos com e sem análise macro → medir score do Juiz |
| Crítica em adversarial review (`@smith` pode questionar) | Alta | Baixo | Justificativa documentada nesta análise; aceitável defender |

**Quebra-galho real?** **Reversível mas custosa** se descoberta no meio do dev. Smith pode atacar — defesa é "MVP first, otimizar com dado real". **Esta é uma das decisões mais frágeis.**

---

## D-05 — Vault Seed Manual com courtsbr/* — 🟡 Moderado

### ✅ O que NÃO vai atrapalhar
- **Garante qualidade** do corpus inicial (pior que vault vazio é vault com lixo)
- 2.000-3.000 docs cabem confortavelmente em Qdrant embedded
- One-shot: depois funciona

### ⚠️ O que PODE atrapalhar
| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-------------:|:-------:|-----------|
| **Scrapers `courtsbr/*` são em R** — Eric ou eu rodamos? Stack mismatch | Alta | Médio | Opção 1: Atlas roda R uma vez localmente. Opção 2: re-implementar scraping em Python (~3-5 dias dev). Opção 3: usar HuggingFace dataset como base + completar |
| **Trabalho de curadoria manual** dos 2-3k docs — taggar metadata correto é repetitivo | Alta | Médio | Curar amostra 200 docs manualmente → treinar classificador zero-shot (Sabia-7B + few-shot) → aplicar no resto |
| Scrapers do `courtsbr` podem estar desatualizados (último commit varia) | Média | Médio | Verificar se ainda funcionam; se não, fork + fix ou usar alternativas Python |
| Output do `courtsbr` pode não casar com nosso schema enriquecido | Alta | Baixo | Criar layer de transformação `seed/transformers/` |

**Quebra-galho real?** Stack mismatch é **chato mas resolvível**. Curadoria de 2-3k docs é trabalho real (~5-10 dias se 1 pessoa, ~2-3 dias com auto-classificação).

---

## D-06 — 4 Fontes Jurisprudência (STF + STJ) — 🟡 Moderado

### ✅ O que NÃO vai atrapalhar
- Cobertura de pesos vinculação 5/5 (STF) + 4/5 (STJ) — **base canônica**
- Volume manejável (~3.000 docs no total)
- Fontes oficiais — autoridade jurídica máxima

### ⚠️ O que PODE atrapalhar
| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-------------:|:-------:|-----------|
| **Portais STF/STJ mudam layout HTML** sem aviso → scrapers quebram | **Alta** (típico em portais governamentais — 2-3× por ano) | Alto (vault não atualiza) | (a) Testes E2E mensais que validam scraping; (b) Alerta automatizado + manual fix; (c) backup de schema XPath versionado |
| Schema STJ Temas Repetitivos pode variar entre eras (temas antigos vs novos) | Média | Médio | Pydantic com campos opcionais + tolerância a missing fields |
| Súmulas STF Vinculantes têm só ~58 itens — corpus pequeno demais para alguns nichos | Alta | Baixo | Compensar com Repercussão Geral (~1300) e STJ Súmulas (671) |
| Acórdãos podem ter encoding quebrado, latin-1 vs utf-8 | Média | Baixo | Normalização Unicode na ingestão |

**Quebra-galho real?** Scrapers vão quebrar — é **questão de quando, não se**. Mitigação: pipeline mensal com testes + alertas. **Risco operacional contínuo, não bloqueador**.

---

## D-07 — DataJud na Fase 2 — 🟢 Sólido

### ✅ O que NÃO vai atrapalhar
- MVP funciona sem DataJud (vault + cálculo + jurisprudência consolidada bastam)
- API DataJud é gratuita e estável quando precisar
- Implementação fase 2 é trabalho conhecido (~1-2 sprints)

### ⚠️ O que PODE atrapalhar
| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-------------:|:-------:|-----------|
| **Cliente piloto pedir "estatística de êxito"** desde MVP — diferencial competitivo | Média | Médio | Backlog visível + roadmap mostra fase 2; se virar bloqueador, antecipar (1-2 sprints custo) |
| Dependência de chave API CNJ (cadastro burocrático) | Baixa | Baixo | Solicitar chave logo no início para não atrasar quando precisar |

**Quebra-galho real?** Improvável. DataJud é "nice-to-have", não "must-have" para revisão contratual.

---

## D-08 — LexML Pré-cache de 4 Diplomas — 🟢 Sólido

### ✅ O que NÃO vai atrapalhar
- 4 leis cobrem **>95% das citações** em revisão bancária PF
- Cache local elimina dependência de SLA externo
- Versionamento via git garante reprodutibilidade

### ⚠️ O que PODE atrapalhar
| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-------------:|:-------:|-----------|
| **Acórdãos citarem leis fora dos 4** (ex: Lei 14.181/2021 — superendividamento — entra muito hoje) | Média | Médio | Logging das remissões não-resolvidas + alerta para incluir nova lei no cache |
| **Mudanças legislativas** (emendas, alterações no CDC) deixam cache stale | Baixa-Média (CDC tem alterações esporádicas) | Médio | Refresh trimestral via API LexML + diff vs cached |
| API LexML pode estar lenta/indisponível para edge cases | Média | Baixo | Fallback "lei não disponível, citação não resolvida" + log para refresh manual |

**Quebra-galho real?** Lei nova frequentemente citada (Lei 14.181/2021) é o risco mais provável. **Mitigação: monitorar logs de remissões não-resolvidas** e adicionar leis ao cache reativamente.

---

## D-09 — Descartar abjur (uso direto) — 🟢 Sólido

### ✅ O que NÃO vai atrapalhar
- Stack incompatível confirmada (R) — não há código a perder
- 109 repos auditados, 99% R
- Conceitos jurimétricos podem ser estudados independentemente

### ⚠️ O que PODE atrapalhar
| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-------------:|:-------:|-----------|
| Perder **metodologia "score de probabilidade de êxito"** — diferencial em fase 2 | Média | Médio (em fase 2, não MVP) | Estudar livro `abjur/livro` (Metodologia de Pesquisa Jurimétrica) quando DataJud entrar |
| `tpur` (Brazilian Unified Procedural Tables) tem **taxonomia oficial** que poderia padronizar `legal_topic_principal` | Média | Médio | Extrair taxonomia do tpur (R → JSON) — trabalho de 1-2 horas |

**Quebra-galho real?** Não. Mas **vale extrair `tpur` taxonomy** para alinhar com padrão CNJ.

---

## D-10 — MVP CDC PF Veículos — 🔴 **ALTO RISCO**

### ✅ O que NÃO vai atrapalhar (tecnicamente)
- BACEN tem código SGS específico (25471) — dado pronto
- Jurisprudência abundante (anatocismo + Tabela Price = temas clássicos)
- Contrato curto (10-30 páginas) — bom para iteração

### ⚠️ O que PODE atrapalhar — **AQUI MORA O DRAGÃO**
| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-------------:|:-------:|-----------|
| 🔴 **Mercado saturado** — possíveis competidores: Linte, Verum, Verbalize, Justto, Jusbrasil + escritórios já fazem revisão manualmente | **Alta (não pesquisado)** | **CRÍTICO** | **Análise de concorrentes ANTES de escrever código** — Atlas pode rodar `*perform-market-research` ou `*create-competitor-analysis` |
| 🔴 **Selic baixa atual** (2026: ~10-12%) reduz divergência matemática vs taxas contratuais — **menos "ganhos" de revisão** | Alta | Alto | Ampliar foco: Selic alta de 2022-2024 ainda gera contratos vigentes "revisáveis"; pode focar em contratos antigos |
| 🔴 **Súmula 539 STJ** legalizou capitalização infra-anual no SFN com pactuação — torna anatocismo mais difícil de provar | Alta (já é realidade) | Alto | Foco da tese muda: **abusividade absoluta** (taxa muito acima de mercado) > anatocismo puro |
| Demanda real de advogados por "revisor IA" pode ser baixa — preferem fazer manual | Média | Alto | **Validação com 5-10 advogados-piloto antes do MVP**: pesquisa qualitativa |
| Concorrente diferenciado pode ter funcionalidades que não cobrimos | Alta | Médio | Análise de concorrentes informa backlog |

**Quebra-galho real?** **SIM. Esta é a decisão mais arriscada das 13.** Tecnicamente sólido, mas **mercado pode rejeitar**.

### 🚨 Mitigação CRÍTICA recomendada por Atlas
**ANTES de invocar `@architect` (Aria) e começar SAD/implementação:**
1. **Análise de concorrentes** (15-30 min de pesquisa) — identificar 5 SaaS LegalTech BR de revisional
2. **Validação qualitativa** — Eric conversar com 3-5 advogados sobre a dor real (eles fariam? pagariam quanto?)
3. **Decidir se mantém D-10 ou pivota** (ex: revisional cartão rotativo, onde anatocismo ainda é mais agressivo)

**Eric: posso rodar análise de concorrentes agora se você quiser. Comando: `*create-competitor-analysis`.**

---

## D-11 — Hardware Faseado (Laptop → Workstation) — 🟢 Sólido

### ✅ O que NÃO vai atrapalhar
- Sabia-7B Q4 (~5GB) roda em laptop comum
- Latência aceitável em dev (3-8 min/contrato)
- Não bloqueia desenvolvimento

### ⚠️ O que PODE atrapalhar
| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-------------:|:-------:|-----------|
| Eric resistir ao gasto de R$12-15k da workstation quando precisar | Média | Médio | VPS com GPU spot (ex: RunPod) é alternativa intermediária ~R$500/mês |
| Laptop de Eric pode não ter RAM suficiente (precisa 16GB mínimo) | Baixa-Média (verificar) | Alto | Confirmar specs do laptop ANTES de começar dev |

**Quebra-galho real?** Não. Decisão financeira pode adiar mas não bloqueia.

---

## D-12 — UF Inicial MG (TJMG) — 🟡 Moderado

### ✅ O que NÃO vai atrapalhar
- TJMG tem corpus consolidado de revisional
- Estrutura permite multi-UF — só re-rodar scraper para nova UF
- Súmula 30 TJMG é referência nacional

### ⚠️ O que PODE atrapalhar
| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-------------:|:-------:|-----------|
| **Eric atender clientes de outro estado primeiro** (ex: SP, RJ) — vault MG vira inútil | Média | Médio | Reversível em ~1-2 dias (re-rodar scraper + reindexar) |
| TJMG mudou tese sobre revisional recentemente (sem verificar) | Baixa | Médio | Verificar com advogado-piloto MG |
| Câmara dividida no TJMG — jurisprudência conflitante interna | Média | Baixo | Indexar com peso por câmara + permitir filtro fino |

**Quebra-galho real?** **Decisão sensível ao mercado-alvo do Eric.** Se MVP for SP, mudar para TJSP. Re-trabalho de 2 dias.

---

## D-13 — Adiar business/brand — 🟡 Moderado

### ✅ O que NÃO vai atrapalhar
- Foco técnico no MVP é correto
- Sem distração com pricing/marca durante engineering

### ⚠️ O que PODE atrapalhar
| Risco | Probabilidade | Impacto | Mitigação |
|-------|:-------------:|:-------:|-----------|
| **Validação com piloto-advogados** fica fraca sem nome + posicionamento — "o que é isso?" | **Alta** | Médio | Codinome interno funciona para POC técnica; quando piloto formal, ativar `@kamala` (~1 sprint para naming + posicionamento básico) |
| Eric demorar para definir modelo de negócio → MVP funciona mas não vira produto | Média | Alto | Trigger: ao concluir MVP, automaticamente acionar `@mifune` |
| Concorrente lançar com nome/branding fortes enquanto desenvolvemos | Baixa-Média | Médio | Análise de concorrentes (já mencionada em D-10) cobre isto |

**Quebra-galho real?** Decisão **estratégica**, não técnica. Se Eric estiver focado em provar tecnologia primeiro, OK. Se quiser também validar mercado, brand vem mais cedo.

---

## 🎯 Top 5 Riscos a Mitigar AGORA (antes de chamar Aria)

| Prioridade | Risco | Decisão afetada | Ação imediata |
|:---------:|-------|-----------------|---------------|
| **1** | Mercado saturado / Selic baixa / Súmula 539 reduz demanda | D-10 | **Análise de concorrentes + validação com 3-5 advogados** |
| 2 | Scrapers courtsbr são R + curadoria pesada | D-05 | Decidir: rodar R ou reescrever Python? Quem cura? |
| 3 | Scrapers STF/STJ quebram quando portal muda | D-06 | Estabelecer pipeline de monitoramento desde o início |
| 4 | Eliminar Economista pode ser revertido tarde | D-04 | A/B test em 30 contratos no piloto |
| 5 | Validação fraca sem marca | D-13 | Definir cronograma: quando ativar @kamala |

---

## 🟢 Top 5 Decisões Mais Sólidas (sem preocupação)

| # | Decisão | Por que é sólida |
|---|---------|------------------|
| **D-01** | Arquitetura C | Componentes maduros + migração drop-in possível |
| **D-02** | 3 blocos novos | Cura fragilidades documentadas + implementação simples |
| **D-03** | Decimal | Stdlib Python + resolve vulnerabilidade legal |
| **D-07** | DataJud fase 2 | Não bloqueia MVP + fácil adicionar depois |
| **D-08** | LexML pré-cache 4 leis | Cobertura >95% + cache versionado |

---

## 📋 Recomendação de Atlas

**3 ações antes de chamar `@architect` (Aria):**

1. ✅ **Resolver D-10** — análise de concorrentes (posso rodar agora) + validação com advogados (Eric)
2. ✅ **Resolver D-05 quem cura** — Eric, Atlas, ou auto-classificação Sabia-7B?
3. ✅ **Confirmar laptop tem 16GB+ RAM** — D-11 trivial mas blocker se não tiver

**Se essas 3 ações NÃO forem feitas e formos direto para Aria:**
- D-10: SAD pode estar errado (escopo MVP que ninguém compra)
- D-05: Aria não sabe estimar effort do vault seed
- D-11: Dev pode ficar inviável no laptop atual

**Se essas 3 ações FOREM feitas:**
- Confiança no plano salta de 75% → 95%
- Smith terá menos munição para atacar no adversarial review

---

## ⚖️ Veredicto Honesto

| Categoria | Quantidade |
|-----------|:---------:|
| Decisões sem risco material | 8 (61%) |
| Decisões com risco gerenciável | 4 (31%) |
| Decisões com risco alto / não-mitigado | 1 (8%) — **D-10** |

**Phase 0 está fechada do ponto de vista TÉCNICO** — todas as decisões técnicas (D-01 a D-09 + D-11 + D-12 + D-13) estão defensáveis com mitigações.

**Phase 0 NÃO está fechada do ponto de vista de PRODUTO** — D-10 (escopo MVP) precisa de validação de mercado antes da implementação começar. **Esse é o único risco que pode descarrilhar o projeto inteiro.**

---

*Atlas, mostrando onde a casca pode rachar — 🔎*
