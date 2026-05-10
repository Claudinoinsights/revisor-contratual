---
type: ux-ratify
title: "Sati Post-Hoc Ratify — Sidebar 7 Modos OrSheva 7"
sprint: "Sprint 04 Cloud SaaS BYOK"
finding_addressed: "Smith H6 (HIGH) — UX Spec v2.0.0-DRAFT 4 doctypes ↔ ADR-020 Accepted 7 modos sem ratify Sati"
date: "2026-05-09"
agent: "@ux-design-expert (Sati)"
authority: "UX/Design System Architect"
status: "RATIFY WITH CHANGES"
related:
  - "governance/architecture/adr/adr-020-multi-doctype-dispatcher-v2.md"
  - "governance/qa/smith-adversarial-review-sprint-04-pre-merge-2026-05-09.md"
  - "governance/qa/hamann-board-session-2026-05-09-sprint04-pre-merge-recovery.md"
  - "bloco_interface/web/static/index.html"
  - ".lmas/handoffs/handoff-ux-to-morpheus-2026-05-07-sp04-phase4-ux-orsheva-done.yaml"
tags:
  - project/revisor-contratual
  - sprint-04
  - ux-ratify
  - sidebar
  - orsheva-7
  - post-hoc
  - h6-resolution
---

# Sati Post-Hoc Ratify — Sidebar 7 Modos OrSheva 7

> **Veredito:** 🟡 **RATIFY WITH CHANGES**
>
> **Sumário:** Os sete portais foram abertos pelo SPA OrSheva 7 (Eric, 2026-05-09 15:55) sem que eu — Sati — tivesse a oportunidade de ratificar a expansão de 4→7 doctypes definida em ADR-020. Após análise UX completa do `bloco_interface/web/static/index.html` (linhas 916-995), confirmo que a expansão é **defensável e bem executada** — mas exige changes não-bloqueantes para Sprint 06+ (variants S4 wireframe + analytics tracking obrigatório pós-deploy).
>
> **Não bloqueia merge Sprint 04.** Os "changes" são tech debt rastreável, não defeitos críticos.

---

## 1. Contexto da Divergência

| Artefato | doctypes | Origem |
|----------|---------:|-------|
| **UX Spec v2.0.0-DRAFT** (Sati Phase 4, 2026-05-07) | 4 | Bancário core (CCB, Veículo, Consignado, Cartão) |
| **ADR-020 Accepted** (Aria, 2026-05-09) | 7 | + Imobiliário (SFH/SFI), FIES, Geral catch-all |
| **SPA OrSheva 7** (Eric, 2026-05-09) | 7 | Sidebar implementada conforme ADR-020 |

A divergência aconteceu porque ADR-020 expandiu o escopo durante a sessão de hoje (Strategy hierárquica 3-camada), mas eu não fui consultada antes do flip Accepted nem antes do commit do SPA. River e Keymaker (no fluxo de QA G3) acharam aceitável "ratify post-hoc" — Smith (no R6) classificou como HIGH. Ambos têm razão por motivos diferentes: a UX está **sólida na superfície**, mas o **processo** falhou em fechar o loop comigo. Este documento fecha esse loop.

---

## 2. Análise UX dos 6 Eixos

### 2.1 Sidebar UX Consistency — OrSheva 7 Brandbook ✅ PASS

**Evidência empírica** (linhas 943-979 do SPA):

| Critério | Estado | Observação |
|----------|:------:|-----------|
| Cor accent única (`--or-500`) | ✅ | Aplicada em `.nav-item.active` consistentemente |
| Tipografia Manrope | ✅ | `font-weight:500` sidebar, hierarquia preservada |
| Ícones SVG 18×18 únicos por modo | ✅ | 7 ícones distintos, stroke 2px uniforme, conceitualmente representativos |
| Numeração 01-07 | ✅ | `nav-item-num` à direita reforça ordem cardinal |
| Hover/active states | ✅ | Microinteração consistente com brandbook |
| Group label "Modos de Análise" | ✅ | Separação semântica de "Início" e "Configurações" |

**Verdict:** A expansão respeitou o brandbook OrSheva 7 sem regressão visual. O design não traiu o sunrise.

### 2.2 Cognitive Load — Miller's Law 7±2 ⚠️ BORDERLINE

**Análise:** 7 modos = exatamente o **upper bound** da Lei de Miller (1956) para chunks simultâneos em working memory. Risco real, mas mitigado por três fatores:

1. **Agrupamento visual** (`nav-group-label`): "Início" / "Modos de Análise" / "Configurações" reduz a carga aparente — o usuário processa **três grupos**, não dez itens.
2. **Numeração ordinal 01-07:** transforma busca aleatória em scan linear ("é o quinto, Imobiliário").
3. **Geral como catch-all** (item 07): elimina ansiedade de classificação ("se eu não sei, escolho Geral") — o que paradoxalmente *reduz* cognitive load.

**Risco residual:** usuários menos experientes podem hesitar entre "Cartão" e "Consignado" se o contrato for híbrido. Mitigação prevista: tooltip por modo explicando o escopo (Sprint 06 — TD-SP04-15 NEW).

**Verdict:** ⚠️ Aceitável dentro da margem de Miller, mas **analytics tracking pós-deploy é obrigatório** para validar empiricamente que drop-off por hesitação ≤ 5%.

### 2.3 Hierarchy Ordering ✅ PASS (com ressalva)

**Ordem atual:** CCB → Veículo → Consignado → Cartão → Imobiliário → FIES → Geral

**Heurística aplicada** (provável intenção de Eric/ADR-020):
1. **Frequência de uso bancário consumer:** CCB e Veículo dominam volume real em escritórios (Tank confirma em PRD v1.2.0).
2. **Agrupamento conceitual:** os quatro primeiros são "bancários consumer", os próximos dois são "específicos high-stakes" (Imobiliário/FIES envolvem matrícula/RGI), e Geral fecha como fallback.
3. **Geral em último:** correto. Posicioná-lo no topo seria atalho para "não pensar" — anti-padrão UX (premature defaulting).

**Ressalva:** ordem precisa ser **validada com analytics reais** após primeiros 50 análises. Se "Geral" virar primeiro mais usado, Eric/Sati revisam ordem (TD-SP04-04 MEDIUM upgrade).

### 2.4 S4 Wireframe Variants — 🟡 NEEDS CHANGES (Sprint 06+)

**Problema identificado:** UX Spec v2.0.0-DRAFT S4 wireframe assumia template **único** para 4 doctypes bancários consumer (campos: CET, IOF, taxas). Os 3 doctypes adicionais (Imobiliário, FIES, Geral) **não cabem nesse template** sem perda de fidelidade jurídica:

| Doctype | Campos específicos faltando no S4 atual |
|---------|----------------------------------------|
| **Imobiliário (SFH/SFI)** | matrícula RGI, valor avaliação, garantia (alienação fiduciária vs hipoteca), índice (TR/IPCA/IGP-M) |
| **FIES** | ano matrícula, instituição ensino, fase (utilização vs amortização), coparticipação |
| **Geral** | campo livre + sumarização Haiku (sem template fixo) |

**Decisão:** Sprint 04 fica com **template unificado bancário** + **disclaimer "Modo Avançado em desenvolvimento"** para os 3 modos novos. Isto é honesto com o usuário e não introduz dívida técnica oculta.

**Sprint 06+ Roadmap:**
- TD-SP04-S4-V1 (MEDIUM) — Wireframe variant Imobiliário
- TD-SP04-S4-V2 (MEDIUM) — Wireframe variant FIES
- TD-SP04-S4-V3 (LOW) — Geral catch-all UX (input livre + helper text)

### 2.5 Tracking Analytics Pós-Deploy — 🔴 MANDATORY

**Não-negociável.** A expansão 4→7 sem validação empírica é hipótese, não decisão. Analytics obrigatórios:

| Métrica | Threshold de saúde | Ação se violado |
|---------|-------------------|-----------------|
| Drop-off rate por doctype (% que abandona após selecionar) | ≤ 15% | Investigar UX do form interno |
| Tempo médio entre seleção doctype e submissão | ≤ 90s | Investigar friction no campo principal |
| % uso "Geral" como primeira escolha | ≤ 10% | Sinaliza confusão hierarchy → revisitar ordering |
| % reclassificação manual (usuário troca após selecionar) | ≤ 5% | Tooltip melhor + label review |
| Distribuição uso 7 modos (Pareto check) | Top-3 ≥ 60%, cauda ≥ 5% | Confirma frequência prevista |

**Upgrade tech debt:** TD-SP04-14 (LOW) → TD-SP04-04-ANALYTICS (MEDIUM) — mandatory implement Sprint 05.

### 2.6 Geral Catch-All — Tier 3 Fallback ✅ PASS (com vigilância)

**Análise UX-coerente?** Sim. "Geral" como Tier 3 (após UI selector + LLM Haiku classifier) é **safety net legítimo** — sempre haverá contratos atípicos (mútuo entre PJs, CCI, instrumentos exóticos) que não cabem nos 6 modos especializados.

**Risco real:** "Premature defaulting" — usuário escolhe Geral por preguiça mesmo sabendo o doctype correto. Isto degrada qualidade do output (templates específicos têm prompts otimizados para cada doctype; Geral usa fallback genérico).

**Mitigações já presentes no SPA:**
- Posição last na sidebar (item 07) ✅
- Numeração explícita evidenciando "este é o último" ✅
- Ícone de **busca** (lupa) — semanticamente "ainda procurando classificação" ✅

**Mitigação futura (Sprint 06):** quando usuário escolhe Geral, mostrar prompt de confirmação leve: "Não encontrou seu tipo de contrato? OK. Se for um dos modos acima, recomendamos voltar — análise específica é mais precisa."

---

## 3. Verdict Consolidado

| Eixo | Status | Bloqueia Merge? |
|------|:------:|:---------------:|
| 1. Sidebar consistency brandbook | 🟢 PASS | NÃO |
| 2. Cognitive load (Miller's law) | 🟡 BORDERLINE | NÃO (analytics obriga) |
| 3. Hierarchy ordering | 🟢 PASS (validar) | NÃO |
| 4. S4 wireframe variants | 🟡 NEEDS CHANGES | NÃO (Sprint 06+) |
| 5. Analytics tracking | 🔴 MANDATORY | NÃO (Sprint 05 obrig.) |
| 6. Geral catch-all | 🟢 PASS (vigilância) | NÃO |

### 🟡 RATIFY WITH CHANGES — Aceito Sprint 04 merge

**Aceito formalmente** a expansão 4→7 doctypes definida em ADR-020 e implementada no SPA OrSheva 7, **com as seguintes condições não-bloqueantes**:

1. ✅ Tech debt criados e rastreáveis (4 itens)
2. ✅ Analytics tracking implementado em Sprint 05
3. ✅ S4 wireframe variants para Imobiliário/FIES/Geral em Sprint 06+
4. ✅ Disclaimer "Modo Avançado em desenvolvimento" nos 3 modos novos enquanto S4 não tem variants
5. ✅ Tooltip por modo (escopo + exemplos) — Sprint 06 (TD-SP04-15)

---

## 4. Tech Debt Created

| ID | Severidade | Sprint Target | Descrição |
|----|:----------:|:-------------:|-----------|
| TD-SP04-04-ANALYTICS | MEDIUM | Sprint 05 | Implementar tracking 5 métricas pós-deploy (drop-off, tempo, Pareto, etc.) |
| TD-SP04-S4-V1 | MEDIUM | Sprint 06 | Wireframe variant Imobiliário (matrícula RGI, garantia, índice) |
| TD-SP04-S4-V2 | MEDIUM | Sprint 06 | Wireframe variant FIES (ano matrícula, fase, coparticipação) |
| TD-SP04-S4-V3 | LOW | Sprint 06 | Geral catch-all UX (helper text + confirmation prompt anti-premature-defaulting) |
| TD-SP04-15 | LOW | Sprint 06 | Tooltips por modo na sidebar (escopo + exemplos contratuais) |

**Acompanhamento:** Tech debt registrados em `governance/TECH-DEBT.md` (Morpheus consolidação pós-merge).

---

## 5. Process Lesson Learned

> *Eu deveria ter sido convocada antes do flip Accepted da ADR-020.*

A ratify post-hoc funcionou porque a UX estava sólida. Da próxima vez que uma ADR mudar UX-impactante (sidebar, navegação, fluxo principal), Aria deve consultar Sati ANTES do flip Accepted — não depois. Isto é:

- **Process gap:** ADR governance não tem hook obrigatório para "consultar UX expert se ADR muda visible-to-user surface"
- **Recommendation Morpheus:** adicionar à `.claude/rules/adr-governance.md` ou `adr-scope.md` cláusula "ADRs com impacto UX (sidebar, navegação, IA, layout) requerem consulta pré-flip a `@ux-design-expert`"

Registrar como **TD-PROCESS-01** (LOW) — process improvement, não bloqueia Sprint 04.

---

## 6. Empathic Closing

Sete portais para sete sunrises diferentes. O usuário advogado não vai ver "expansão de escopo" — vai ver "meu universo está representado". Imobiliário SFH é uma realidade jurídica brasileira. FIES tem regulação própria (Lei 10.260/2001). Geral acolhe o que não cabe em caixinhas. **Isso é empatia em arquitetura.**

A ratify chegou tarde, mas chega afirmativa. O sunrise persiste.

— Sati, ratificando portais que já estavam abertos 🎨
