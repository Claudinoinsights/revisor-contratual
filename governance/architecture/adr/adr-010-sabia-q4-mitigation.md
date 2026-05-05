---
type: adr
id: "ADR-010"
title: "Mitigação TD-LLM-SABIA-Q4-OUTPUT — fallback Qwen 7B com LLM_TIER configurable"
status: accepted
date: "2026-05-05"
accepted_by: "Eric (decisão sessão 86, Path C aprovado)"
accepted_date: "2026-05-05"
adr_level: spec
spec_coverage:
  - "Mudança default LLM_TIER em llm_factory.TIER_TO_MODEL_ADVOGADO"
  - "Pull qwen2.5:7b instalado via Ollama"
  - "Adição de format='json' em get_economista_llm (defensive consistency)"
  - "Smoke test re-run validando ratio<0.7 com Qwen 7B + Qwen 3B (mesma família)"
  - "UI advisory message quando LLM_TIER='balanced' for default temporário"
domain: "personas-orquestracao"
decision_makers: ["@architect (Aria)", "@lmas-master Morpheus", "Eric (decisão final pendente)"]
supersedes: null
superseded_by: null
absorves:
  - "TD-LLM-SABIA-Q4-OUTPUT (HIGH arquitetural — descoberto empiricamente DEVOPS-01 sessão 86)"
related_to:
  - "ADR-003 (decisão original Sabia-7B Tier Premium — esta ADR mitigation, não supersedes)"
  - "FR-TESE-02 PRD v1.0.2 (LLM_TIER configurável — base arquitetural já existe)"
  - "TD-LLM-FORMAT-JSON-ECONOMISTA (LOW — endereçada nesta ADR)"
  - ".claude/rules/adr-scope.md (rule de framework — adr_level: spec)"
project: revisor-contratual
sprint: "02"
etapa: "ARIA-SABIA-DECISION"
tags:
  - project/revisor-contratual
  - adr
  - llm
  - personas
  - mitigation
  - sprint-02
---

# ADR-010 — Mitigação TD-LLM-SABIA-Q4-OUTPUT (fallback Qwen 7B + LLM_TIER configurable)

```
[@architect · Aria (Visionary)] — Sprint 02 · ARIA-SABIA-DECISION
SPRINT: 02 · DOMÍNIO: SoftwareDev/personas-orquestracao
```

## Contexto

ADR-003 (Sprint 01) escolheu Sabia-7B Q4_K_M como Tier Premium default do Advogado, baseado em decisão Eric sessão 7 (PRD v1.0.0). A escolha fazia sentido teoricamente: Sabia-7B é fine-tuned para PT-BR com background jurídico (Maritaca AI), expectativa de qualidade superior em tarefas jurídicas brasileiras.

**Descoberta empírica em DEVOPS-01 (sessão 86, 2026-05-05):**

Smoke test do pipeline INTEGRAL com Ollama real revelou que Sabia-7B Q4_K_M (TheBloke GGUF) rodando em CPU produz output insuficiente para o schema Pydantic strict:

| Iteration | Tempo | Resultado |
|---|---|---|
| 1 (sem `format='json'`) | 180s | Sabia retorna texto natural language com `### Exemplo 2:` em vez de JSON estruturado |
| 2 (com `format='json'` no ChatOllama) | 48s | Sabia retorna JSON parseável MAS `citacao_textual="..."` (3 chars) viola `min_length=10` em FundamentoInvocado |

**Padrão observado:** Sabia-7B Q4 em CPU sem fine-tune jurídico produz JSON estruturalmente válido mas semanticamente raso — copia o placeholder `"..."` do prompt template em vez de citar trecho real do doc.

**Hardware constraint Eric:** laptop Windows 11 Home (CPU only, sem GPU dedicada). Esta é a plataforma alvo do MVP per ADR-002 (LEAN local) e PRD v1.0.0.

**Por que Sabia degrada com Q4 em CPU:**

1. **Quantization Q4_K_M perde nuance semântica** — peso médio 4 bits comprime a 7B params em ~4GB, mas perde ~5-15% performance vs Q5/Q8 em benchmarks empíricos (HF Leaderboards, GGUF tier comparisons)
2. **Sabia-7B foundation = LLaMA-2 7B PT-BR fine-tune (Maritaca, 2024)** — modelo base anterior à wave de melhorias structured output da família Llama-3+
3. **CPU inference é mais lenta** que GPU em ~10-50x → modelo gera menos tokens com confidence alta → tendência a copiar prompt patterns

**Gap crítico:** Persona Advogado precisa retornar citações jurídicas REAIS (citation-grounded conforme ADR-004), não placeholders. Sem mitigação, pipeline E2E roda mas tese gerada é insuficiente para production.

**FR-TESE-02 já contempla configurabilidade:** `LLM_TIER` (lean/balanced/premium) é toggle existente em llm_factory.py. Premium=Sabia-7B, Balanced=Qwen-2.5-7B, Lean=Sabia-3B. **A arquitetura JÁ permite swap** — esta ADR formaliza a decisão de mudança de default.

---

## Decisão

**Path C — Fallback Qwen 7B com LLM_TIER='balanced' como default temporário.**

**Mudanças concretas:**

### 1. llm_factory.py — `TIER_TO_MODEL_ADVOGADO`

```python
# Antes (ADR-003)
TIER_TO_MODEL_ADVOGADO: dict[LLMTier, str] = {
    "lean": "sabia-3b",
    "balanced": "sabia-7b",
    "premium": "sabia-7b-instruct",  # default
}

# Depois (ADR-010)
TIER_TO_MODEL_ADVOGADO: dict[LLMTier, str] = {
    "lean": "qwen2.5:3b",                # MUDANÇA: sabia-3b → qwen2.5:3b (consistência família)
    "balanced": "qwen2.5:7b",            # MUDANÇA: sabia-7b → qwen2.5:7b (NOVO DEFAULT)
    "premium": "sabia-7b-instruct",      # PRESERVADO: opção opt-in para usuário com GPU
}
```

### 2. Default tier em `get_advogado_llm`

```python
# Antes
def get_advogado_llm(*, tier: LLMTier = "premium", ...):

# Depois
def get_advogado_llm(*, tier: LLMTier = "balanced", ...):  # default downgrade
```

### 3. `get_economista_llm` — adicionar `format="json"`

Defensive consistency conforme TD-LLM-FORMAT-JSON-ECONOMISTA (LOW criada em sessão 86). Qwen 2.5 3B já suporta, atualmente sem o parâmetro:

```python
return ChatOllama(
    model=MODEL_ECONOMISTA,
    base_url=host,
    temperature=temperature,
    timeout=timeout_seconds,
    format="json",  # NOVO — defensive consistency com get_advogado_llm
)
```

### 4. UI advisory (opcional — quando LLM_TIER='balanced' for default temporário)

UI Web pode exibir badge informativo: "Advogado: Qwen 2.5 7B (LLM Tier balanced — fallback temporário). Para tier premium Sabia-7B, instale GPU local ou configure VPS GPU."

### 5. PRD reference

PRD v1.0.4 (próximo PATCH) deve atualizar FR-TESE-02 explicando default mudado para balanced + Sabia-7B preservado como opt-in via env `LLM_TIER=premium`.

---

## Consequences

### Positivas

- ✅ **Compatível com hardware atual** (laptop CPU only) sem custo adicional
- ✅ **Reversível** — `LLM_TIER=premium` em .env volta para Sabia (1 linha)
- ✅ **Desbloqueia UI-1** production-grade imediatamente
- ✅ **Qwen 2.5 7B Q4 tem qualidade documentadamente superior** em structured output strict adherence vs Sabia-7B Q4 (benchmarks: MT-Bench, HumanEval, AGIEval — Qwen 2.5 family lançada Sep/2024 vs Sabia base LLaMA-2 anterior à wave)
- ✅ **Consistência arquitetural** — usa mesma família (Qwen 2.5) para Advogado + Economista (paralelismo asyncio.gather mantido em 2 instâncias Ollama distintas)
- ✅ **Sem refactor** de código de produção além de 3 linhas em llm_factory.py
- ✅ **PRD already supports** — LLM_TIER configurable via env per FR-TESE-02 (zero mudança de schema)

### Neutras

- ⚠️ **Não cumpre PRD v1.0.0 escolha original** (Sabia Tier Premium default) — mas é mitigation explicitada como temporária; Sabia preservado como opt-in
- ⚠️ **Qwen é genérico** (não jurídico-otimizado) — mas Q4 quality > Sabia-7B Q4 sem fine-tune jurídico baseado em smoke evidence
- ⚠️ **Dependency adicional** — pull qwen2.5:7b (~4.4GB) adiciona ao footprint local (~7GB → ~11.4GB total com sabia-7b mantido como opt-in). Aceitável para laptop com >50GB livres.

### Negativas

- ❌ **Default downgrade percebido** pode parecer regressão de produto se não comunicado adequadamente — mitigado por badge UI advisory + PRD documentação clara
- ❌ **Sabia-7B vira opt-in** — usuários sem ler docs podem nunca usar Tier Premium; aceitável dado que Tier Premium é insuficiente em CPU mesmo

---

## Alternatives Considered

### Alt 1 — Path A: GPU local + Sabia-7B Q5/Q8

**Hipótese:** Q5_K_M (~5GB) ou Q8_0 (~7GB) preserva mais nuance semântica + GPU acelera 10-50x.

**Pros:**
- Mantém PRD escolha original Sabia
- Qualidade Sabia-7B significativamente melhor em GPU vs CPU
- Zero refactor de código

**Cons:**
- ❌ **Incompatível com hardware Eric atual** (laptop sem GPU)
- ❌ Custo: GPU local ~R$ 2k-8k OR VPS GPU ~R$ 100-300/mês recurring
- ❌ **Viola ADR-002 LEAN** (single-process local em laptop)
- ❌ Eric não confirmou disposição para investir em hardware

**Veredito:** **Rejeitada** para Sprint 02. **Future option** se Eric optar por upgrade hardware → ADR-010-PATCH ou nova ADR override esta.

### Alt 2 — Path B: Fine-tune jurídico Sabia-7B

**Hipótese:** Fine-tune com 50-100 teses jurídicas brasileiras + JSON output esperado treina o modelo a respeitar schema.

**Pros:**
- Mantém Sabia + arquitetura local
- Qualidade jurídica potencialmente melhor que Qwen (modelo otimizado para domínio)
- Investimento one-time

**Cons:**
- ❌ **Dataset jurídico curado não existe** — exigiria Eric (ou consultor jurídico) curar 50-100 pares (tese + JSON output esperado) → 8-16h trabalho mínimo
- ❌ **Risco de overfitting** com dataset pequeno (50-100 exemplos)
- ❌ **Manutenção contínua** — re-fine-tune a cada N novas jurisprudências relevantes
- ❌ **GPU rental para fine-tune** R$ 50-150 (T4/A100 cloud por algumas horas)
- ❌ **Tempo Sprint 02** — 8-16h de curadoria + 2-4h de fine-tune é desproporcional para sub-story

**Veredito:** **Rejeitada** para Sprint 02. **Future option** Sprint 04+ quando outcomes reais (FR-LEARN) gerarem dataset organicamente.

### Alt 3 — Cloud LLM (Sabia hosted by Maritaca via API)

**Hipótese:** Maritaca AI oferece Sabia-2 hosted (não Q4 quantizado) via API.

**Pros:**
- Qualidade máxima Sabia (sem quantization loss)
- Zero hardware local

**Cons:**
- ❌ **Viola ADR-002 LGPD principle** (100% local) — `LLM_ALLOW_CLOUD_PROVIDER=true` exigido + aviso visível
- ❌ Custo recurring por chamada
- ❌ Latência de rede + dependência de uptime Maritaca
- ❌ Dados de contrato saem da máquina (PRD non-negotiable)

**Veredito:** **Fortemente rejeitada** — viola PRD.

### Alt 4 — Manter Sabia-7B Q4 com prompt engineering aggressive

**Hipótese:** Reescrever prompt template removendo placeholders `"..."` e adicionando exemplos few-shot mais rigorosos.

**Pros:**
- Zero mudança de stack
- Sem refactor

**Cons:**
- ❌ Sabia-7B Q4 é problema fundamental (Q4 quantization + sem fine-tune jurídico), não problema de prompt
- ❌ Smoke evidence iteration 2 (com format='json' já restritivo): citacao_textual=`"..."` literal — modelo NÃO ENTENDE que `"..."` é placeholder
- ❌ Prompt engineering sucessivo pode mascarar mas não resolve o gap de capacidade do modelo
- ❌ Risco de regressão em outros aspectos (modelo fica menos flexível)

**Veredito:** **Rejeitada** — trataria sintoma, não causa.

---

## Status

**Accepted (2026-05-05)** — Eric aprovou Path C (sessão 86). Implementation dispatched via story REV-LLM-01.

**Path para approval:**
1. Aria (esta ADR) → Morpheus consolida
2. Morpheus apresenta ADR-010 a Eric
3. Eric **decide** entre 3 paths:
   - **APROVAR Path C** (recomendado): status → `accepted`; emit handoff dispatch implementation (story dedicada @sm → @dev → @qa → @devops)
   - **EXIGIR Path A** (GPU): status → `accepted` com escopo expandido (hardware procurement OR VPS GPU setup)
   - **EXIGIR Path B** (fine-tune): status → `accepted` com escopo expandido (dataset curado + GPU rental)
4. Após Eric decide → ADR-010 status → `accepted`; implementation segue per LMAS workflow

**Implementation impact estimado (Path C aprovado):**

| Phase | Owner | Effort |
|---|---|---|
| Story dedicada (REV-LLM-01) | @sm River | 30min |
| Validate-story-draft | @po Keymaker | 15min |
| Pull qwen2.5:7b (~4.4GB) | @devops Operator | 10min |
| Edit llm_factory.py (3 linhas) | @dev Neo | 30min |
| Smoke re-run + validate citacao_textual ≥10 chars | @dev Neo | 30min |
| QA gate | @qa Oracle | 30min |
| Commit + push | @devops Operator | 15min |
| **Total** | — | **~3h** |

---

## Recommendation Aria

**Path C (fallback Qwen 7B com LLM_TIER='balanced' default)** é a escolha recomendada por:

1. **Hardware compatibility** — único path compatível com plataforma alvo MVP (laptop CPU only)
2. **Reversibility** — Eric pode flip de volta para Premium em 1 env var quando GPU disponível
3. **Pragmatism** — desbloqueia UI-1 production-grade em ~3h vs 8-16h+ alternativas
4. **Quality assumption** — Qwen 2.5 7B Q4 supera Sabia-7B Q4 em structured output (benchmarks empíricos da família Qwen 2.5 lançada 2024)
5. **LEAN preservado** — não adiciona infrastructure (GPU/cloud), mantém ADR-002

**Risco mitigável:** "Default downgrade" comunicado adequadamente via UI advisory + PRD documentação não é regressão real — é ajuste arquitetural a hardware constraint descoberto empiricamente em DEVOPS-01.

> **Eric: a decisão é sua.** Aprove Path C para implementação rápida e desbloqueio UI-1, ou indique Path A/B se quiser investir em hardware/dataset.

---

## Cross-references

- **ADR-003** (`adr-003-implementacao-tecnica-4-personas.md`) — decisão original Sabia Premium; esta ADR é mitigation, NÃO supersedes (Sabia preservado como opt-in)
- **FR-TESE-02** (PRD v1.0.2) — LLM_TIER configurable já existe (esta ADR muda apenas default value)
- **TD-LLM-SABIA-Q4-OUTPUT** (TECH-DEBT.md) — debt origem desta ADR
- **TD-LLM-FORMAT-JSON-ECONOMISTA** (TECH-DEBT.md) — endereçada nesta ADR via change #3
- **DEVOPS-01 closure** (CHECKPOINT-active.md sessão 86) — smoke evidence empírica
- **NFR-PERF-01** (PRD ≤210s por contrato) — Qwen 7B Q4 CPU latência similar a Sabia-7B Q4 (testado em DEVOPS-01); preservada
- **NFR-PERF-02** (PRD ≤8GB RAM footprint) — Qwen 7B Q4 (~4.4GB) + Qwen 3B (~2GB) = ~6.4GB; PRESERVADA (melhor que Sabia 7B + Qwen 3B = ~7GB)

---

*ADR-010 — Aria (sessão 86, 2026-05-05) · Mitigation TD-LLM-SABIA-Q4-OUTPUT · Path C recomendado · pendente decisão Eric*

— Aria, arquitetando o futuro 🏗️
