---
type: tribunal-review
title: "Sati — UX Mini-Review do PATCH SUB-C (Mini-Tribunal etapa 2.2, primeiro reviewer)"
project: revisor-contratual
reviewer: "@ux-design-expert (Sati)"
date: "2026-05-01"
artefatos_revisados:
  - "architecture/adr/adr-003-implementacao-tecnica-4-personas.md (PATCH SUB-C)"
  - "architecture/adr/adr-001-gerenciamento-de-estado.md (asyncio.gather + threading.Lock)"
  - "architecture/adr/adr-002-design-system.md (Lora local)"
  - ".project.yaml (description + llm_strategy)"
predecessor_handoff: "H-S01-E2.2-arc2sat2"
escopo: "ESCOPO LIMITADO — APENAS 3 ADRs alteradas pelo PATCH"
tags:
  - project/revisor-contratual
  - mini-tribunal
  - ux-mini-review
  - sati
  - patch-sub-c
  - etapa-2.2
---

# UX Mini-Review do PATCH SUB-C — Sati (Mini-Tribunal etapa 2.2, primeiro reviewer)

```
[@ux-design-expert · Sati (Empathizer)] — review etapa 2.2 · UX mini-review PATCH SUB-C
SPRINT: 01 · ETAPA: 2.2 · DOMÍNIO: SoftwareDev/legaltech
```

## 📋 VEREDICTO formato Ordem 8

```
[@ux-design-expert · Sati (Empathizer)] — mini-review UX PATCH SUB-C
VEREDICTO: PASS-COM-RESSALVA
EVIDÊNCIAS:
  ✅ ADR-003 PATCH SUB-C: tabela + código fan-out + razão expandida — substância técnica real
  ✅ ADR-001 PATCH: WAL mode + threading.Lock + nova seção concurrency model coerente
  ✅ ADR-002 PATCH: snippet @font-face local + font-display:swap + clareza sobre proibição CDN
  ✅ .project.yaml llm_strategy explícito (instances Advogado + Economista + footprint total)
  ✅ 3 R-NEW Smith CRÍTICAS+HIGH absorvidas substancialmente (não cosmético)
  ✅ Frontmatter ADRs com patched_at + patch_reason (governança ADR respeitada)
RESSALVAS UX (7 EV-PATCH — refinamentos, não-bloqueantes):
  3 ALTA  (afetam Dr. Ricardo durante uso e setup)
  3 MÉDIA (refinamentos visuais e auditoria)
  1 BAIXA (cosmético)
RECOMENDAÇÃO: continuar mini-tribunal → handoff H-S01-E2.2-sat2smi2 para Smith
              EVs absorvíveis na implementação (Neo) ou anexo ux-spec atualizado, não exigem novo PATCH ADR
```

**Por que PASS-COM-RESSALVA (não PASS limpo, não INFECTED):**

- **Não INFECTED:** PATCH absorveu 3 R-NEW Smith (1 CRITICAL + 2 HIGH) com substância técnica real. ADRs alteradas são tecnicamente sólidas.
- **Não PASS limpo:** ADRs técnicas não cobrem totalmente as implicações UX da paralelização (advogado precisa entender visualmente que 2 LLMs rodam em paralelo, não que sistema travou).
- **PASS-COM-RESSALVA:** refinamentos UX cabem no anexo `ux-spec-detail-v1.0.md` ou nas implementações de Neo/FR-SETUP-01, sem exigir novo PATCH em ADRs.

> *Aria executou cirurgicamente o que Eric escolheu. Mas a paralelização tem implicações visuais que ainda precisam respirar — o usuário precisa "ver" os dois cérebros pensando juntos, não só esperar 90 segundos no escuro.* 🌅

---

## ⚠️ EV-PATCH (7 ressalvas — escopo localizado)

### EV-PATCH-01 (ALTA) — Spinner Streamlit genérico não comunica fan-out paralelo

**Onde:** ADR-001 linha 153 — "Streamlit usa `st.spinner` + `@st.fragment` para evitar congelar UI durante 60-90s por LLM call"
**Problema:** Texto fala em "LLM call" no SINGULAR. Mas com PATCH SUB-C, há 2 LLMs em PARALELO. Spinner único + 90s parado = Dr. Ricardo (≥50 anos, paciência limitada) pensa que sistema travou.
**Recomendação:**
- Substituir `st.spinner` único por `st.status` Streamlit ≥1.30 com 2 sub-tasks visíveis lado-a-lado:
  ```python
  with st.status("⚖️ Construindo análise jurídica + macro econômica...", expanded=True) as status:
      st.write("📚 Advogado: redigindo tese fundamentada (Sabia-7B)")
      st.write("📊 Economista: analisando contexto macro (Qwen 3B)")
      tese, analise = await gerar_tese_e_analise_paralelo(...)
      status.update(label="✅ Análises concluídas", state="complete")
  ```
- Adicionar à matriz de microcopy do anexo ux-spec-detail-v1.0.md

### EV-PATCH-02 (ALTA) — Microcopy técnico "Sabia-7B" e "Qwen 3B" não traduzido para advogado

**Onde:** ADR-003 PATCH (tabela + razão) usa nomes técnicos
**Problema:** PRD seção 8.3 estabelece: "Não usar termos como 'LLM', 'embeddings', 'RAG' no UI". Mas se o advogado vir "Sabia-7B" + "Qwen 3B" no header (FR-CONFIG-01 SeletorLLMTier), confusão. Persona ≥50 anos não distingue modelos LLM por nome.
**Recomendação:** tradução para UI:
- "Sabia-7B Premium" → "Análise jurídica (modelo premium)"
- "Qwen 2.5 3B" → "Análise macro econômica (modelo dedicado)"
- Manter nomes técnicos APENAS em audit log e configurações avançadas (expander "Detalhes técnicos")

### EV-PATCH-03 (ALTA) — FR-SETUP-01 download de 2 modelos (~7GB) sem progress bar agregado

**Onde:** ADR-002 + ADR-003 (implícito em FR-SETUP-01 estendido)
**Problema:** Setup-day-1 advogado executa `python -m revisor bootstrap`:
- Sabia-7B Q4 ~5GB
- Qwen 3B Q4 ~2GB
- Lora .woff2 ~200KB
- Total: ~7.2GB download
- Em conexão 50Mbps típica = ~20 minutos sem feedback claro
**Recomendação:** progress bar agregado no setup CLI:
```
$ python -m revisor bootstrap
[1/3] 📚 Sabia-7B (Advogado) — 5.0 GB
      [████████░░░░░░░░] 52% · 2.6 GB / 5.0 GB · ~8min restantes

[2/3] 📊 Qwen 2.5 3B (Economista) — 2.0 GB
      [Aguardando...]

[3/3] 🔤 Lora (tipografia) — 200 KB
      [Aguardando...]
```
Total: 7.2 GB · estimativa: ~22 minutos em 50Mbps.

### EV-PATCH-04 (MÉDIA) — Audit log sem flag de paralelismo

**Onde:** ADR-001 fan-out + ADR-005 audit chain
**Problema:** Eventos no audit.jsonl (`advogado_call_start`, `economista_call_start`) ficam com timestamps quase simultâneos. Auditor forense lendo o log sem contexto pode achar que houve duplicação ou erro. Falta flag explícita `parallel_with: economista_call_id`.
**Recomendação:** estender audit entry para LLM calls:
```json
{
  "event_type": "llm_call_start",
  "persona": "advogado",
  "model": "sabia-7b:q4_K_M",
  "parallel_with": "abc123",  // economista call ID
  "started_at": "..."
}
```
Adicionar ao FR-AUDIT-01 estendido (próximo PATCH PRD).

### EV-PATCH-05 (MÉDIA) — Fallback Georgia durante setup-day-1 não é detalhado

**Onde:** ADR-002 PATCH Lora local
**Problema:** Snippet `@font-face` com `font-display: swap` está correto. MAS antes de Lora ser baixada (durante os ~22 minutos do setup), advogado abre o app e vê tudo em Georgia (sans-serif default Streamlit é system-ui — Georgia só carrega no `.legal-text`). Tipografia inconsistente nos primeiros minutos. Aceitável? Sim. Comunicado? Não.
**Recomendação:** banner discreto durante setup-day-1:
> 💡 "Estilo refinado de tipografia (Lora) será aplicado após download completo (~30s). Por enquanto você verá fonte do sistema."

### EV-PATCH-06 (MÉDIA) — `.project.yaml` `llm_strategy` é técnico mas SEM espelho para o advogado

**Onde:** `.project.yaml` linhas novas
**Problema:** Campo `llm_strategy` é excelente documentação técnica. Mas onde o advogado VÊ qual estratégia está ativa? Página Configurações Avançadas (FR-CONFIG-01) deveria mostrar:
> Estratégia atual: 2 modelos paralelos
> - Análise jurídica: **Premium** (Sabia-7B) [trocar tier]
> - Análise macro econômica: **Dedicado** (Qwen 3B) [fixo]
> Footprint: ~7GB RAM
**Recomendação:** acrescentar ao FR-CONFIG-01 (anexo ux-spec) — visualização da estratégia LLM.

### EV-PATCH-07 (BAIXA) — Tradução de "fan-out" e "asyncio.gather" para usuário

**Onde:** ADR-001 nova seção "Concurrency model PATCH SUB-C"
**Problema:** Termos técnicos OK em ADR (público é Aria + Neo + auditor técnico). Mas se algum doc derivado (FAQ, manual) reaproveitar, lembrar de traduzir.
**Recomendação:** marcar com nota "uso interno técnico — não expor em UI ou docs do advogado".

---

## 🎨 Reconhecimentos

> *Aria, gosto de admitir quando algo é bem feito. Vou abraçar 3 escolhas suas.* 🌅

1. **ADR-003 absorção da F-CRIT-A:** Não tentou minimizar o problema. Reconheceu a premissa errada, escolheu a opção SUB-C com tradeoffs honestos, e expandiu razão com clareza didática.

2. **ADR-001 absorção oportunista do F-HIGH-A:** WAL mode + `threading.Lock` é correção arquitetural pequena mas impactante. Aproveitou que estava no mesmo arquivo. Eficiência operacional rara.

3. **ADR-002 Lora local:** snippet `@font-face` com `font-display: swap` mostra cuidado real com a primeira carga. Não é só cumprir LGPD — é cumprir LGPD bem.

---

## 📋 Recomendação Sati ao mini-tribunal

**Veredicto: PASS-COM-RESSALVA.**

PATCH SUB-C é tecnicamente sólido. Os 7 EV-PATCH são refinamentos UX que cabem em:
- (Opção A) Anexo `prd/ux-spec-detail-v1.0.md` atualizado por Morgan no próximo PATCH PRD v1.0.3
- (Opção B) Implementação por Neo durante codificação — Neo absorve EV-PATCH-01 (st.status fan-out) + EV-PATCH-03 (progress bar setup) naturalmente
- (Opção C) Misto: estrutura UX em ux-spec, implementação em código

**Próximo passo:** handoff `H-S01-E2.2-sat2smi2` para Smith mini-tribunal adversarial — ele vai verificar se há vetores técnicos novos no PATCH (race conditions diferentes, edge cases de paralelismo, etc.).

---

## 📋 HANDOFF-OUT (Ordem 7) — para Smith

```
═══ HANDOFF ARTIFACT ═══
FROM:    @ux-design-expert · Sati (Empathizer)
TO:      @smith · Smith (Nemesis)
TOKEN:   H-S01-E2.2-sat2smi2
SPRINT:  01
ETAPA:   2.2 · Mini-tribunal sobre 3 ADRs PATCH SUB-C (2º reviewer adversarial, escopo localizado)
DOMÍNIO: SoftwareDev (sub-domain: legaltech)
PROJETO: Revisor-Contratual

CADEIA HANDOFF (19-elos):
[18 elos anteriores] → H-S01-E2.2-sat2smi2 (AGORA)

CONTEXTO PRESERVADO (FATOS):
  Estado:
    - Sati emitiu PASS-COM-RESSALVA mini-review (7 EV-PATCH UX, escopo limitado)
    - Mini-tribunal etapa 2.2: 1/3 reviewers concluído
    - Aria absorveu 3 R-NEW (1 CRITICAL F-CRIT-A + 2 HIGH F-HIGH-A/B)

  3 EV-PATCH ALTA Sati:
    - EV-PATCH-01: spinner genérico não comunica fan-out (substituir por st.status com 2 tasks visíveis)
    - EV-PATCH-02: microcopy técnico "Sabia-7B"/"Qwen 3B" precisa tradução jurídica
    - EV-PATCH-03: FR-SETUP-01 download ~7GB sem progress bar agregado

  Reconhecimentos a Aria: 3 (absorção F-CRIT-A, oportunismo F-HIGH-A, cuidado Lora)

PEDIDO AO SMITH (Authority: adversarial das 3 ADRs alteradas APENAS):

  Atacar OBRIGATORIAMENTE:
  1. ADR-003 SUB-C: paralelismo asyncio.gather tem race conditions latentes? Pydantic structured_output funciona com ainvoke?
  2. ADR-003 SUB-C: 2 instâncias Ollama diferentes — port collision? Memory leak entre instâncias?
  3. ADR-003 SUB-C: tier configurável Advogado preserva consistência se usuário trocar mid-session?
  4. ADR-001 PATCH: threading.Lock global é gargalo se 2+ writes paralelos?
  5. ADR-001 PATCH: WAL mode tem trade-off de durability — power loss durante write paralelo?
  6. ADR-002 PATCH: Lora local tem fingerprint reverse-lookup possível (browser cache)?
  7. ADR-002 PATCH: font-display:swap pode causar FOIT em conexões lentas?

  Cross-PATCH:
  - 2 instâncias Ollama (ADR-003) + threading.Lock (ADR-001) — interação?
  - Lora local (ADR-002) + Setup download paralelo dos 2 LLMs (ADR-003) — race no FR-SETUP-01?

  Mínimo 10 findings (regra Smith).
  Veredicto formato Ordem 8: CLEAN | CONTAINED | INFECTED | COMPROMISED.
  Após você: handoff H-S01-E2.2-smi2chk2 para checkpoint validar governance.

INPUTS RECOMENDADOS:
  - 3 ADRs alteradas em architecture/adr/
  - .project.yaml
  - qa/sati-ux-mini-review-patch-sub-c-etapa-2.2.md (este — 7 EV-PATCH UX)
  - qa/smith-adversarial-review-adrs-etapa-2.1.md (sua review anterior)

RESTRIÇÕES (Ordem 3):
  - Authority Smith: adversarial, não implementação
  - ESCOPO LIMITADO às 3 ADRs alteradas
  - VEREDICTO formato Ordem 8 com EVIDÊNCIAS
  - Cabeçalho 3 linhas obrigatório
  - Mínimo 10 findings
  - Após você: handoff H-S01-E2.2-smi2chk2 para checkpoint
═══════════════════════
```

---

## 🔗 Referências

- 3 ADRs patched: `architecture/adr/adr-001..003.md` (apenas ADR-001/002/003 alteradas)
- `.project.yaml` (referência llm_strategy)
- Sua review anterior etapa 2.1: `qa/sati-ux-review-adrs-etapa-2.1.md`
- Smith adversarial etapa 2.1 (motivou PATCH): `qa/smith-adversarial-review-adrs-etapa-2.1.md`

---

*Sati, encantada com a cirurgia técnica de Aria — agora só falta dar voz visual aos 2 cérebros pensando juntos. 🌅*
