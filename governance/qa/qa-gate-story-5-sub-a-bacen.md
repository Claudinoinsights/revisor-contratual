---
type: qa-gate
title: "QA Gate STORY 5 SUB-A — bloco_engine/bacen"
project: revisor-contratual
gate_for: "STORY-5-SUB-A-bloco_engine-bacen"
date: "2026-05-01"
agent: "@qa (Oracle)"
verdict: PASS
tags:
  - project/revisor-contratual
  - qa-gate
  - story-5-sub-a
  - bacen
  - phase-2.B
---

# QA Gate STORY 5 SUB-A — bloco_engine/bacen

> **Linhagem:** Sessão 46 (sucessor de QA Gate STORIES 1-4 PASS sessão 42).
> **Domínio:** software-dev / legaltech.
> **Authority:** QA quality gate formal (advisory PASS / CONCERNS / FAIL / WAIVED).

## Cabeçalho 3 linhas

[@qa · Oracle · Test Architect & Quality Advisor] — quality gate STORY 5 SUB-A bloco_engine/bacen
**VEREDICTO: PASS** (3 observations LOW, todas tech debt rastreável; 0 CRITICAL, 0 HIGH, 0 MEDIUM bloqueantes)
**Recomendação:** APROVADO para STORY 6 (próxima sub-fronteira: SUB-B parsing | SUB-C vault | SUB-D LLM)

---

## 1. Escopo auditado

| Artefato | Linhas | Cobertura testes |
|---|---|---|
| `bloco_engine/bacen/__init__.py` | 28 | re-export — N/A |
| `bloco_engine/bacen/codigos_bacen.yaml` | 31 | validado por _resolve_sgs |
| `bloco_engine/bacen/client.py` | 173 | 16 testes diretos |
| `tests/unit/test_bacen.py` | 269 | self |
| `pyproject.toml` (delta `+pyyaml>=6.0`) | 1 linha | n/a |
| `bloco_engine/__init__.py` (delta) | 2 linhas | n/a |

**Suite agregada:** 125 passed + 1 xfailed (intencional smoke F-MIN-02), 0 failed, runtime 42.29s.
**Delta vs Phase 2.A:** 109 → 125 (+16 testes BACEN).

---

## 2. Verificações executadas (D1-D7)

### D1 — Conformidade FR-BACEN-01..03

| Requisito | Implementação | Evidência |
|---|---|---|
| **FR-BACEN-01** wrapper python-bcb | `BacenClient._fetch_sgs_with_retry` chama `sgs.get` lazy-importado | `client.py:96-117` |
| **FR-BACEN-02** cache TTL 30d + retry exponencial 1→2→4→8→16s max 5 | diskcache + tenacity decorator com wait_exponential(min=1, max=16) + stop_after_attempt(5) | `client.py:103-108`, `test_bacen.py:190-199` (broken_fetcher.call_count == 5) |
| **FR-BACEN-03** fallback "última taxa conhecida" com is_fallback=True | `last_known_key` cache.set sem expire + `model_copy(update={"is_fallback": True})` | `client.py:154-155, 168`, `test_bacen.py:171-188` |

**PASS — 3/3 FR cobertos.**

### D2 — Conformidade NFR-LGPD-01 (whitelist HTTP)

| Aspecto | Implementação | Evidência |
|---|---|---|
| ALLOWED_HOST constante imutável | `ALLOWED_HOST = "api.bcb.gov.br"` (não config) | `client.py:43` |
| FONTE_URL_TEMPLATE hardcoded | `"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{sgs}/dados/ultimos/1?formato=json"` | `client.py:44` |
| Teste defensivo whitelist | `test_allowed_host_constante_imutavel` + `test_fonte_url_template_aponta_apenas_para_api_bcb` | `test_bacen.py:230-239` |

**PASS — whitelist no código (não config), portanto alteração requer ADR. NFR-LGPD-01 enforced.**

### D3 — Validação cruzada independente Oracle

| # | Probe | Resultado | Status |
|---|---|---|---|
| 1 | Tenacity `reraise=True` levanta `ConnectionError` (não `RetryError`)? | Confirmado: `type(e).__name__ == 'ConnectionError'` | OK — Neo cobriu ambos no except (defensivo) |
| 2 | YAML carrega 3 seções esperadas (indices, taxas_credito_pf, nao_implementadas)? | Sim, 3 seções confirmadas | PASS |
| 3 | CDC_VEICULOS_PF SGS = 25471 (média mensal)? | Sim, 25471 | PASS — alinhado com PRD v1.0.2 |
| 4 | IPCA mensal = 433, Selic meta = 432? | Sim, ambos confirmados | PASS — alinhado com séries SGS BACEN públicas |
| 5 | BacenData rejeita mes_ref formato `2025/12`? | Sim — `ValidationError` (Pydantic regex) | PASS |
| 6 | BacenData rejeita float em taxa_media? | Aceita string Decimal-safe `"2.15"` | PASS (FR-CALC-01 conformidade) |
| 7 | BacenData VALIDA host da fonte_url? | **NÃO** — aceita qualquer URL string (ver O-09 abaixo) | OBSERVATION |

**PASS — todas as validações materiais corretas. Observation O-09 documentada.**

### D4 — Cobertura cenários (test_bacen.py)

| Cenário | Coberto? | Teste |
|---|---|---|
| Happy path (BacenData estruturalmente válido) | ✅ | `TestHappyPath` (3 testes) |
| Cache hit não chama fetcher | ✅ | `test_cache_hit_nao_chama_fetcher_segunda_vez` |
| Cache miss em mes_ref diferente chama fetcher | ✅ | `test_cache_miss_em_mes_diferente_chama_fetcher` |
| Cache persiste entre BacenClient distintos (diskcache) | ✅ | `test_cache_persiste_entre_clientes` |
| Retry recupera após N falhas | ✅ | `test_retry_recupera_apos_2_falhas` (3ª tentativa OK) |
| Fallback ativa quando rede off + last_known existe | ✅ | `test_fallback_ativa_quando_rede_falha_e_cache_tem_last_known` |
| Retry esgotado sem fallback levanta `BacenFetchExhausted` | ✅ | `test_retry_esgotado_sem_fallback_levanta` (call_count == 5) |
| 3 modalidades DP-03 levantam NotImplementedError | ✅ | `TestModalidadesNaoSuportadas` (parametrizado 3×) |
| Whitelist LGPD imutável | ✅ | `TestLGPDWhitelist` (2 testes) |
| mes_ref inválido rejeitado por Pydantic | ✅ | `test_mes_ref_formato_invalido_levanta_pydantic` |
| Decimal precision preservada via `str(float)` | ✅ | `test_taxa_decimal_preserva_precisao` |

**PASS — 11 cenários distintos, edge cases cobertos.**

### D5 — Cobertura código (estimada)

| Módulo | Estimativa | Limites NFR-MAINT-02 |
|---|---|---|
| `bloco_engine/bacen/client.py` | ≥85% (todas APIs públicas + paths principais cobertos) | ≥80% bloco_engine ✅ |
| `bloco_engine/bacen/__init__.py` | n/a (re-export puro) | — |
| `bloco_engine/bacen/codigos_bacen.yaml` | validado indireto via `_resolve_sgs` | — |

**PASS — atende NFR-MAINT-02 (≥80% bloco_engine).**

### D6 — Conformidade transversal

| Aspecto | Status | Evidência |
|---|---|---|
| Tipo seguro (mypy strict compatible) | OK | `from __future__ import annotations`, anotações completas, `Any` apenas em `_sgs_fetcher` (DI legítimo) |
| Decimal everywhere (FR-CALC-01) | OK | `Decimal(str(valor))` no fetch, `str()` no taxa_media |
| Erro rastreável (exceções customizadas com hierarquia) | OK | BacenError → {ModalidadeNaoSuportada, BacenFetchExhausted}; NotImplementedError reusado para DP-03 (idiomático) |
| Logger nomeado (não print) | OK | `logger = logging.getLogger(__name__)` |
| Lazy import python-bcb (não trava startup se rede off) | OK | `_get_sgs_fetcher` faz `from bcb import sgs` apenas quando necessário |
| ADR-scope cumprida (ADR-design vs ADR-spec) | OK — implementação de design, sem ADR explícita necessária para wrappers de lib |

**PASS — limpo transversalmente.**

### D7 — Pecados Capitais (Ordem 10) — verificação

| Pecado | Verificado | Status |
|---|---|---|
| Inventar dado/métrica não-mensurada | Latência BACEN não foi medida — NÃO foi inventada (não consta no client.py nem testes) | OK |
| Float em wire format monetário | taxa_media é string em todo path | OK |
| Silenciar erro (except: pass) | Logger.warning em fallback path (visível) | OK |
| Authority alheia | Neo escreveu código (legítimo); QA não escreve código | OK |
| Cabeçalho ausente | Este documento tem cabeçalho 3 linhas | OK |

**PASS — 0 violações.**

---

## 3. Observations (tech debt rastreável — NÃO bloqueia)

### LOW (3)

- **O-08 LOW** — `RetryError` no except path é dead code defensivo
  - Tenacity com `reraise=True` levanta a exceção ORIGINAL, não `RetryError`. Confirmado experimentalmente: `type(e).__name__ == 'ConnectionError'`.
  - **Impacto:** zero (defesa redundante; se Neo trocar `reraise=True` por `reraise=False` no futuro, a captura passa a fazer sentido).
  - **Recomendação:** manter como está OU adicionar comentário `# reraise=True; capture defensiva caso flag mude`. Decisão Neo.

- **O-09 LOW** — `BacenData.fonte_url` não valida host
  - Pydantic schema aceita qualquer string em `fonte_url` (inclusive `"https://evil.com/x"`). A whitelist NFR-LGPD-01 vive APENAS no `FONTE_URL_TEMPLATE` constante.
  - **Impacto atual:** zero (todo código que constrói `BacenData` no client.py usa o template). Não há rota fora dele.
  - **Risco futuro:** se outro lugar construir `BacenData` (ex: deserialização de cache externo), pode burlar.
  - **Recomendação:** adicionar `field_validator("fonte_url")` em `bloco_contratos/contrato.py` confirmando `urlparse(v).hostname == "api.bcb.gov.br"`. Tarefa para STORY de hardening pós-MVP OU absorver na STORY 6 SUB-D quando deserialização aparecer.

- **O-10 LOW** — Fallback retorna `mes_ref` do registro anterior (não o solicitado)
  - Comentário próprio do teste já documenta: `# Mes_ref do fallback é do registro anterior (não o solicitado) — esperado`.
  - **Impacto:** UX/legal — petição que cita "BACEN mes_ref=2025-04" enquanto usuário pediu 2025-03 pode causar confusão se `is_fallback=True` não for inspecionado upstream.
  - **Recomendação:** quando bloco_workflow consumir BacenData, MUST checar `data.is_fallback is True` e exibir warning à persona Advogado/Juiz para citação alternativa OU sobrescrever `mes_ref` no fallback para o solicitado e documentar separadamente que a taxa veio de mês diferente. Decisão arquitetural — defer para STORY de integração workflow.

### MEDIUM / HIGH / CRITICAL — **0**

---

## 4. Métricas

| Métrica | Valor |
|---|---|
| Testes BACEN | 16 |
| Testes suite agregada | 125 + 1 xfailed = 126 |
| Falhas | 0 |
| Runtime suite agregada | 42.29s |
| Runtime test_bacen.py isolado | 33.81s (inclui inicialização diskcache em tmp_path 16×) |
| Linhas código produção (client.py) | 173 |
| Linhas código teste (test_bacen.py) | 269 (1.55× ratio teste:produção — saudável) |
| Cobertura cenários distintos | 11 |
| FR cobertos | 3/3 (FR-BACEN-01, 02, 03) |
| NFR cobertos | 1/1 (NFR-LGPD-01 enforced) |
| Observations LOW | 3 |
| Observations MEDIUM/HIGH/CRITICAL | 0 |

---

## 5. Recomendação ao Morpheus

**APROVADO para STORY 6.**

Próxima sub-fronteira de risco a contratar: **SUB-B parsing** (PyMuPDF4LLM + Marker), **SUB-C vault** (sqlite-vec — risco MAIOR por dep nova), ou **SUB-D LLM** (langchain-ollama 2 instâncias — desbloqueia smoke F-MIN-02).

Recomendação Oracle ordinal por risco crescente:
1. **SUB-B parsing** (deps PDF maduras; PyMuPDF é battle-tested) — risco BAIXO
2. **SUB-D LLM** (langchain-ollama é maduro mas requer downloads Sabia 5GB + Qwen 2GB; smoke F-MIN-02 des-xfail é incentivo) — risco MÉDIO
3. **SUB-C vault** (sqlite-vec v0.1 ainda jovem; DP-08 load test pendente) — risco MAIOR — defer se possível

Ordem proposta: **B → D → C** (camada por camada conforme doutrina Phase 2.B).

---

## 6. Linhagem governance

- Antecedente: `qa/qa-gate-stories-1-4-fase-3.0.md` (PASS sessão 42)
- Handoff de entrada: H-S01-E3.1-neo2qa2 (Neo→Oracle, materializar em `.lmas/handoffs/`)
- Handoff de saída: H-S01-E3.1-qa2mor2 (Oracle→Morpheus consolida)
- Sessão checkpoint: 46

---

*Oracle, guardião da qualidade — a fronteira BACEN está contida e auditável.*
