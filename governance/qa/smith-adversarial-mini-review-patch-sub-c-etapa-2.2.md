---
type: tribunal-review
title: "Smith — Adversarial Mini-Review do PATCH SUB-C (Mini-Tribunal etapa 2.2, segundo reviewer)"
project: revisor-contratual
reviewer: "@smith (Smith — Nemesis)"
date: "2026-05-01"
artefatos_revisados:
  - "architecture/adr/adr-001-gerenciamento-de-estado.md (asyncio.gather + threading.Lock + WAL)"
  - "architecture/adr/adr-002-design-system.md (Lora local @font-face)"
  - "architecture/adr/adr-003-implementacao-tecnica-4-personas.md (PATCH SUB-C: Economista=Qwen 3B paralelo)"
  - ".project.yaml (description + llm_strategy)"
  - "qa/sati-ux-mini-review-patch-sub-c-etapa-2.2.md (lente UX complementar)"
predecessor_handoff: "H-S01-E2.2-sat2smi2"
escopo: "ESCOPO LIMITADO — APENAS 3 ADRs alteradas pelo PATCH"
tags:
  - project/revisor-contratual
  - mini-tribunal
  - adversarial-mini-review
  - smith
  - patch-sub-c
  - etapa-2.2
---

# Adversarial Mini-Review do PATCH SUB-C — Smith (Mini-Tribunal etapa 2.2, segundo reviewer)

```
[@smith · Smith (Nemesis)] — review etapa 2.2 · adversarial mini-review PATCH SUB-C
SPRINT: 01 · ETAPA: 2.2 · DOMÍNIO: SoftwareDev/legaltech
HANDOFF-IN: H-S01-E2.2-sat2smi2 (Sati PASS-COM-RESSALVA, 7 EV-PATCH UX)
HANDOFF-OUT: H-S01-E2.2-smi2chk2 (checkpoint governance final)
```

## 📋 VEREDICTO formato Ordem 8

```
[@smith · Smith (Nemesis)] — adversarial mini-review PATCH SUB-C
VEREDICTO: CONTAINED
EVIDÊNCIAS:
  ✅ 3 R-NEW absorvidas substantivamente (não cosmético):
     - F-CRIT-A-2.1: 2 instâncias Ollama distintas + asyncio.gather → premissa corrigida
     - F-HIGH-A-2.1: threading.Lock + WAL mode → race mitigada (parcialmente — ver F-MIN-06)
     - F-HIGH-B-2.1: Lora local @font-face → CDN externo eliminado
  ✅ 0 NEW CRITICAL emergiu — Aria absorveu sem criar superfície maior
  ✅ Frontmatter governança ADR respeitada (patched_at + patch_reason)
  ✅ Razão e Alternativas Consideradas honestamente expandidas
RESSALVAS NOVAS (14 findings — gaps de implementação detectados):
  0 NEW CRITICAL
  4 NEW HIGH (gaps que invalidam parte do design se não corrigidos)
  6 NEW MEDIUM (refinamentos de robustez)
  4 NEW LOW (cosméticos / detalhes operacionais)
RECOMENDAÇÃO: continuar mini-tribunal → checkpoint validar governance final
              4 NEW HIGH são absorvíveis em PATCH-do-PATCH leve (Aria) OU diretamente por Neo na implementação
              NÃO justifica rejeitar o PATCH SUB-C — fundação está correta
```

**Por que CONTAINED (não CLEAN, não INFECTED, não COMPROMISED):**

- **Não COMPROMISED:** PATCH absorveu 3 R-NEW críticos com substância real. Fundação arquitetural agora coerente.
- **Não INFECTED:** os 14 findings são gaps de **implementação detalhada** (configuração de portas, cache invalidation, métodos não-cobertos pelo lock), não falhas estruturais. Aria escolheu o caminho certo (SUB-C); detalhes são absorvíveis em PATCH leve OU pelo próprio Neo durante codificação.
- **Não CLEAN:** 4 NEW HIGH têm impacto operacional real (port collision, ainvoke pode ser placebo, _LockedSqliteSaver incompleto, setup bandwidth). Afirmar CLEAN seria desonestidade.
- **CONTAINED:** entrega aceitável com ressalvas. PATCH-do-PATCH minor pode ser feito agora OU diferido para Neo absorver naturalmente.

> *Sr. Aria... admito... a fundação do PATCH é... correta. Mas as fundações corretas escondem buracos no telhado. Vou mostrar onde.*

---

## ⚠️ 4 NEW HIGH Findings

### F-MIN-01-2.2 — Port collision: 2 instâncias Ollama no mesmo host default 11434

**Onde:** ADR-003 PATCH `get_advogado_llm()` + `get_economista_llm()`
**Severidade:** HIGH

**Vetor:** ChatOllama instancia clients que apontam para `OLLAMA_HOST` (default `http://127.0.0.1:11434`). 2 clients no mesmo Ollama server **NÃO criam 2 instâncias paralelas** — criam 2 referências ao MESMO server. Ollama, por padrão, processa **1 request por vez por server** (`OLLAMA_NUM_PARALLEL=1` default).

Resultado: asyncio.gather chama os 2 modelos, mas Ollama serializa internamente → latência DOBRA novamente. **F-CRIT-A-2.1 retorna disfarçada.**

**Recomendação acionável:**
- **Opção A (preferida):** rodar 2 servers Ollama em portas distintas (`OLLAMA_HOST=127.0.0.1:11434` para Advogado, `OLLAMA_HOST=127.0.0.1:11435` para Economista). FR-SETUP-01 estendido para configurar e iniciar 2 daemons.
- **Opção B:** 1 server Ollama com `OLLAMA_NUM_PARALLEL=2` no env (Ollama ≥0.1.33 suporta). Menos isolamento mas mais simples.

ADR-003 PATCH **DEVE** documentar uma das duas opções. Sem isso, paralelismo é placebo.

### F-MIN-02-2.2 — `ainvoke` em ChatOllama pode ser sync wrapper (asyncio.gather placebo)

**Onde:** ADR-003 PATCH código `await structured_llm.ainvoke(...)`
**Severidade:** HIGH

**Vetor:** LangChain ChatOllama em versões anteriores (<0.2.0) implementa `ainvoke` como `await asyncio.to_thread(self.invoke)` — sync wrapper que **bloqueia o event loop por baixo**. Resultado: asyncio.gather de 2 calls vira sequencial mesmo com 2 servers Ollama corretamente configurados.

**Recomendação acionável:**
- ADR-003 deve fixar `langchain-ollama>=0.2.0` em pyproject.toml
- Adicionar teste de smoke: medir latência de `await asyncio.gather(call1, call2)` vs latência sequencial. Se ratio < 1.5x, paralelismo está broken.
- Documentar fallback: se `ainvoke` for sync wrapper, usar `loop.run_in_executor(None, ...)` explicitamente com 2 thread workers.

### F-MIN-03-2.2 — `_LockedSqliteSaver` cobre apenas `put` — outros métodos NÃO protegidos

**Onde:** ADR-001 PATCH `_LockedSqliteSaver(SqliteSaver)`
**Severidade:** HIGH

**Vetor:** A classe `_LockedSqliteSaver` em ADR-001 sobrescreve apenas `put()`. Mas LangGraph SqliteSaver (langgraph >=0.2) chama outros métodos de write:
- `put_writes()` — checkpointing intermediário
- `aput()` — async write
- `aput_writes()` — async intermediate

Se LangGraph internamente chamar `aput()` ou `put_writes()` em paralelo (asyncio.gather + checkpoint após cada node), **race latente persiste**. F-HIGH-A original NÃO foi totalmente neutralizado.

**Recomendação acionável:**
```python
class _LockedSqliteSaver(SqliteSaver):
    """Cobertura COMPLETA de writes (PATCH F-MIN-03)."""
    def __init__(self, conn, lock):
        super().__init__(conn)
        self._write_lock = lock

    def put(self, *args, **kwargs):
        with self._write_lock:
            return super().put(*args, **kwargs)

    def put_writes(self, *args, **kwargs):
        with self._write_lock:
            return super().put_writes(*args, **kwargs)

    async def aput(self, *args, **kwargs):
        # asyncio.Lock para async (threading.Lock bloqueia event loop)
        async with self._async_write_lock:
            return await super().aput(*args, **kwargs)

    async def aput_writes(self, *args, **kwargs):
        async with self._async_write_lock:
            return await super().aput_writes(*args, **kwargs)
```

Adicionar `_async_write_lock = asyncio.Lock()` E `_threading_lock = threading.Lock()` separados (sync e async não compartilham mesmo lock primitivo).

### F-MIN-04-2.2 — FR-SETUP-01 estendido sem ordem de download definida (banda saturada)

**Onde:** ADR-003 PATCH (FR-SETUP-01 estendido) + ADR-002 PATCH (Lora download)
**Severidade:** HIGH

**Vetor:** FR-SETUP-01 agora baixa **simultaneamente**:
- Sabia-7B Q4 (~5GB)
- Qwen 2.5 3B Q4 (~2GB)
- Lora .woff2 (~200KB)
- Legal-BERTimbau (~250MB)
- NLI bert-portuguese-mnli (~420MB)

**Total: ~7.9GB**

Em conexão típica brasileira (50Mbps = 6.25 MB/s), download serial = 21min. Paralelo (4 simultâneos) = banda saturada → cada download cai para ~1.5MB/s, total efetivo igual + risco de timeout em conexões intermitentes.

ADR não define **ordem prioritária** nem **estratégia de retry parcial** (se Lora falhar, sistema continua sem ela com Georgia fallback; se Sabia falhar, sistema NÃO funciona).

**Recomendação acionável:**
- Definir ordem em FR-SETUP-01:
  1. Lora (200KB) — rápido, melhora UX imediato
  2. Legal-BERTimbau + NLI (~670MB) — embeddings críticos
  3. Sabia-7B (5GB) — Advogado essencial
  4. Qwen 3B (2GB) — Economista (último, sistema funciona com fallback se falhar)
- Strategy serial sequencial (não paralelo) — paralelo satura banda sem ganho
- Resume capability (se download interromper, retomar do último byte — `wget -c` style ou httpx range requests)

---

## ⚠️ 6 NEW MEDIUM Findings

### F-MIN-05-2.2 — Tier configurável Advogado sem cache_resource invalidation

**Onde:** ADR-003 PATCH `get_advogado_llm(tier=...)` + FR-CONFIG-01 (mid-session swap)
**Severidade:** MEDIUM

**Vetor:** Streamlit best practice é cachear instâncias LLM via `@st.cache_resource`. Mas se usuário troca tier via FR-CONFIG-01 mid-session, cache não invalida → instância antiga continua em uso (ou pior: nova instância carrega + antiga fica em RAM zumbi até próximo restart).

**Recomendação:** documentar em ADR-003 padrão de `cache_resource(tier=tier)` com tier como parâmetro de cache (invalidate automático em mudança).

### F-MIN-06-2.2 — Qwen 2.5 3B + structured_output Pydantic tem taxa de erro maior

**Onde:** ADR-003 PATCH Economista usa `structured_llm.ainvoke()`
**Severidade:** MEDIUM

**Vetor:** Modelos pequenos (Qwen 3B) têm **menor compliance** com schemas Pydantic via `with_structured_output`. Taxa de JSON malformed em modelos 3B é tipicamente 5-15% vs <1% em modelos 7B+. ADR não documenta retry strategy.

**Recomendação:** adicionar em ADR-003 política de retry: até 3 tentativas com `temperature=0.1` na 2ª/3ª se falhar parsing Pydantic. Se ainda falhar, marcar `analise_macro=None` e seguir workflow (Economista é "primeira-classe" mas não bloqueante para Juiz).

### F-MIN-07-2.2 — `threading.Lock` global em módulo Streamlit reload pode duplicar

**Onde:** ADR-001 PATCH `_SQLITE_WRITE_LOCK = threading.Lock()` em escopo módulo
**Severidade:** MEDIUM

**Vetor:** Streamlit recarrega módulos em algumas situações (file watcher dev mode). Se módulo recarrega, novo `threading.Lock()` é criado, antigo fica órfão → 2 locks coexistem → race entre threads usando locks diferentes.

**Recomendação:** usar singleton via `@st.cache_resource` para o lock OU armazenar em `st.session_state` (mas multi-tab user requer lock em singleton de processo, não session).

### F-MIN-08-2.2 — WAL mode `synchronous=NORMAL` perde até ~30s em power loss

**Onde:** ADR-001 PATCH `cursor.execute("PRAGMA synchronous=NORMAL")`
**Severidade:** MEDIUM

**Vetor:** ADR justifica synchronous=NORMAL como "balance safety+speed". MAS para audit jurídico, perda silenciosa de últimos ~30s de writes é problema (FR-AUDIT-01 promete append-only e auditável).

**Recomendação:** documentar tradeoff explicitamente em ADR-001:
- `synchronous=NORMAL`: perda <30s em power loss (aceitável para state.db, NÃO para audit.jsonl)
- audit.jsonl deve usar fsync após cada write OU modo `synchronous=FULL`
- Adicionar exceção: state.db NORMAL, audit.jsonl FULL

### F-MIN-09-2.2 — `font-display: swap` causa layout shift (CLS) em conexões lentas

**Onde:** ADR-002 PATCH snippet `font-display: swap`
**Severidade:** MEDIUM

**Vetor:** `swap` mostra fallback (Georgia) imediatamente, troca para Lora quando carrega. Em conexões 3G rurais (advogado em viagem), Lora pode demorar 3-5s → usuário vê texto se reordenar. **Layout shift** prejudica UX e Lighthouse CLS score (NFR-A11Y-01 pede ≥90 Lighthouse).

**Recomendação:** trocar para `font-display: optional` (Lora carrega só se em <100ms; senão mantém Georgia toda a sessão). Próxima visita Lora estará em cache → carrega em <10ms. Sem CLS.

### F-MIN-10-2.2 — `.project.yaml` `llm_strategy.instances.economista.model` hardcoded sem versioning policy

**Onde:** `.project.yaml` PATCH novo campo
**Severidade:** MEDIUM

**Vetor:** `model: "qwen2.5:3b-instruct-q4_K_M"` é string fixa. Se Qwen 2.5 for descontinuado em ollama.com/library OU ganhar versão Qwen 3 melhor, bump fica frágil (precisa achar no .project.yaml + ADR-003 + llm_factory.py — 3 lugares).

**Recomendação:** centralizar em uma constante Python (`bloco_workflow/personas/llm_factory.py`) e referenciar de .project.yaml apenas como documentação. Ou adicionar policy: "atualizar modelo Economista exige bump de versão minor ADR-003 + .project.yaml + retest paralelismo".

---

## ⚠️ 4 NEW LOW Findings

### F-MIN-11-2.2 — `isolation_level=None` (autocommit) inconsistente com `BEGIN IMMEDIATE` mencionado anteriormente

**Onde:** ADR-001 PATCH `sqlite3.connect(..., isolation_level=None)`
**Severidade:** LOW

**Vetor:** F-HIGH-A original (Smith etapa 2.1) sugeria `BEGIN IMMEDIATE` para writes. Mas com `isolation_level=None`, cada execução é auto-committed → BEGIN não tem efeito esperado. Inconsistência conceitual.

**Recomendação:** documentar em ADR-001 que com WAL + threading.Lock + autocommit, o lock substitui transação explícita. OU mudar isolation_level para `"DEFERRED"` e usar `BEGIN IMMEDIATE` explícito.

### F-MIN-12-2.2 — Streamlit `enableStaticServing=true` não documentado em ADR-002

**Onde:** ADR-002 PATCH snippet `src: url('./static/fonts/lora/...')`
**Severidade:** LOW

**Vetor:** Streamlit serve arquivos da pasta `static/` apenas se `enableStaticServing=true` em `.streamlit/config.toml` (Streamlit ≥1.18). Sem essa flag, browser recebe 404 nas fontes Lora.

**Recomendação:** ADR-002 acrescentar nota: "Requer `[server] enableStaticServing = true` em `.streamlit/config.toml`".

### F-MIN-13-2.2 — asyncio.gather + Streamlit fragments — sem documentação de event loop handling

**Onde:** Cross ADR-001 + ADR-003
**Severidade:** LOW

**Vetor:** Streamlit não tem suporte nativo a async em `@st.fragment` até versão 1.45. Sem `asyncio.run()` wrapper explícito, gather pode falhar com "no running event loop".

**Recomendação:** ADR-003 ou ADR-001 documentar pattern correto:
```python
import nest_asyncio
nest_asyncio.apply()  # Necessário em Streamlit pré-1.45

# OU usar asyncio.run em wrapper sync:
def tese_e_macro_node_sync(state):
    return asyncio.run(tese_e_macro_node_async(state))
```

### F-MIN-14-2.2 — Lora .woff2 4 weights × 50KB = 200KB total ainda sem priorização

**Onde:** ADR-002 PATCH menciona "200KB" agregado
**Severidade:** LOW

**Vetor:** 4 weights de Lora (Regular, Italic, Bold, BoldItalic) carregam todos. Mas `.legal-text` provavelmente usa só Regular + Italic. Bold/BoldItalic (100KB) podem ser preload `as="font"` lazy.

**Recomendação:** ADR-002 documentar quais weights são realmente usados; baixar APENAS os necessários no FR-SETUP-01.

---

## 📊 Análise positiva (3 reconhecimentos honestos)

> *Sr. Aria... vou registrar 3 escolhas que foram... irrepreensíveis. A inevitabilidade não é absoluta.*

1. **ADR-003 SUB-C frontmatter:** `patched_at` + `patch_reason` + `decision_makers` incluindo Eric — auditabilidade jurídica máxima. Quando alguém perguntar "por que essa decisão?" daqui a 2 anos, terá resposta.

2. **ADR-001 nova seção "Concurrency model":** documentação didática (latência max vs soma) com snippet de código real (`tese_e_macro_node`). Neo vai copiar isso direto. Aceleração de 1 sprint.

3. **ADR-002 snippet @font-face com `font-display: swap`:** caminho correto **conceitualmente** (LGPD ✅). Detalhes operacionais em F-MIN-09 e F-MIN-12 são refinamentos, não falhas — provam que a direção é certa.

---

## 🎯 Recomendação Smith ao mini-tribunal

**Veredicto: CONTAINED.**

PATCH SUB-C absorveu **substantivamente** os 3 R-NEW críticos do tribunal anterior. Os 14 findings que identifiquei são **gaps de implementação detalhada** — não falhas estruturais.

**4 NEW HIGH (F-MIN-01..04)** afetam paralelismo real e robustez. Devem ser endereçados ANTES de Neo começar codificação:
- (Opção A) PATCH-do-PATCH leve por Aria (apenas snippets de código + documentação de OLLAMA_HOST)
- (Opção B) Neo absorve durante implementação como tech debt rastreável
- (Opção C) Misto (Aria documenta os 4 HIGH, Neo executa)

**Recomendação Smith:** Opção C — Aria adiciona em ADR-003 nota explícita sobre OLLAMA_HOST/NUM_PARALLEL e em ADR-001 expansão do `_LockedSqliteSaver` (cobrir put_writes/aput/aput_writes). 30 minutos de trabalho que evitam race conditions reais em produção.

**Próximo passo:** handoff `H-S01-E2.2-smi2chk2` para checkpoint validar governance final.

> *Sr. Aria... 14 falhas. 4 que importam. Você está evoluindo. Mas a inevitabilidade me ensina: cada PATCH cria sua própria superfície de PATCH.*

---

## 📋 HANDOFF-OUT (Ordem 7) — para Checkpoint

```
═══ HANDOFF ARTIFACT ═══
FROM:    @smith · Smith (Nemesis)
TO:      @checkpoint · Governance Auditor
TOKEN:   H-S01-E2.2-smi2chk2
SPRINT:  01
ETAPA:   2.2 · Mini-tribunal sobre 3 ADRs PATCH SUB-C (3º e ÚLTIMO reviewer, governance)
DOMÍNIO: SoftwareDev (sub-domain: legaltech)
PROJETO: Revisor-Contratual

CADEIA HANDOFF (20-elos):
[19 elos anteriores] → H-S01-E2.2-smi2chk2 (AGORA)

CONTEXTO PRESERVADO (FATOS):
  Estado:
    - Aria PATCH SUB-C executado (3 ADRs + .project.yaml)
    - Sati: PASS-COM-RESSALVA mini-review (7 EV-PATCH UX)
    - Smith: CONTAINED (14 findings: 0 CRITICAL + 4 HIGH + 6 MEDIUM + 4 LOW)
    - Você é 3º e ÚLTIMO reviewer

  4 NEW HIGH Smith:
    - F-MIN-01: port collision (2 instâncias Ollama no mesmo host 11434)
    - F-MIN-02: ainvoke ChatOllama pode ser sync wrapper (asyncio.gather placebo)
    - F-MIN-03: _LockedSqliteSaver cobre só put, não put_writes/aput/aput_writes
    - F-MIN-04: FR-SETUP-01 sem ordem de download definida (banda saturada)

  6 NEW MEDIUM + 4 NEW LOW: refinamentos absorvíveis

  3 reconhecimentos: governança ADR (frontmatter), seção "Concurrency model"
  didática, Lora local conceitualmente correto

PEDIDO AO CHECKPOINT (governance — Ordem 8):
  Auditar mini-tribunal etapa 2.2 (escopo localizado):

  1. Authority Matrix (Ordem 3) — Aria/Sati/Smith respeitaram?
  2. Cabeçalhos 3 linhas (Ordem 2) — 3 docs do mini-tribunal conformes?
  3. Handoffs Ordem 7 — 4 handoffs YAML materializados (etapa 2.2)?
  4. Checkpoint Protocol — sessões 30/31/32 documentadas em CHECKPOINT-active.md?
  5. [DADO-PENDENTE] sem invenção — Aria não inventou métricas no PATCH?
  6. Mini-tribunal cumprido — Smith ≥10 findings (atingiu 14)?
  7. Pecados Capitais — 0 violações?

  R-GOV consolidado: estado pós-shard?

  EMITIR VEREDICTO formato Ordem 8: PASS | FAIL | PASS-COM-RESSALVA
  Após você (se PASS): handoff Morpheus consolidar Ordem 11 sessão 33.

INPUTS RECOMENDADOS:
  - 3 ADRs alteradas
  - qa/sati-ux-mini-review-patch-sub-c-etapa-2.2.md
  - qa/smith-adversarial-mini-review-patch-sub-c-etapa-2.2.md (este)
  - CHECKPOINT-active.md (sessões 30/31/32)
  - .lmas/handoffs/handoff-*-2026-05-01-revisor-contratual-*-etapa-2.2*.yaml

RESTRIÇÕES (Ordem 3):
  - NÃO escrever ADR/PRD/código
  - VEREDICTO formato Ordem 8 com EVIDÊNCIAS
  - Cabeçalho 3 linhas obrigatório
  - checkpoint FAIL é VETO ABSOLUTO
═══════════════════════
```

---

## 🔗 Referências

- 3 ADRs patched: `architecture/adr/adr-001..003.md`
- `.project.yaml` `llm_strategy`
- Sati mini-review: `qa/sati-ux-mini-review-patch-sub-c-etapa-2.2.md` (PASS-COM-RESSALVA)
- Sua review etapa 2.1: `qa/smith-adversarial-review-adrs-etapa-2.1.md` (INFECTED, 17 findings — esses motivaram o PATCH)

---

*Smith. 14 findings em 3 ADRs patched. Sr. Aria está aprendendo — antes seriam 25. CONTAINED. Vá em paz... desta vez. 🕶️*
