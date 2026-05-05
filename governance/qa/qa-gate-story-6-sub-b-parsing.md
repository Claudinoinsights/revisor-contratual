---
type: qa-gate
title: "QA Gate STORY 6 SUB-B — bloco_engine/parsing"
project: revisor-contratual
gate_for: "STORY-6-SUB-B-bloco_engine-parsing"
date: "2026-05-01"
agent: "@qa (Oracle)"
verdict: PASS
verdict_history:
  - date: "2026-05-01"
    verdict: CONCERNS
    sessao: 50
    motivo: "F-PARSE-HIGH-01 detectado por probe Oracle 7.5b"
  - date: "2026-05-01"
    verdict: PASS
    sessao: 53
    motivo: "Fix loop aplicado por Neo (D-MOR-3.2-FIX); probe re-executada 5/5 corretos; 2 testes regression bloqueando reaparecimento"
tags:
  - project/revisor-contratual
  - qa-gate
  - story-6-sub-b
  - parsing
  - phase-2.B
  - concerns
---

# QA Gate STORY 6 SUB-B — bloco_engine/parsing

> **Linhagem:** Sessão 50 (sucessor de QA Gate STORY 5 SUB-A PASS sessão 46).
> **Domínio:** software-dev / legaltech.
> **Authority:** QA quality gate formal (advisory PASS / CONCERNS / FAIL / WAIVED).

## Cabeçalho 3 linhas — RE-GATE PASS (sessão 53)

[@qa · Oracle · Test Architect & Quality Advisor] — RE-GATE STORY 6 SUB-B pós fix loop F-PARSE-HIGH-01
**VEREDICTO ATUAL: PASS** (CONCERNS → PASS após fix Neo; 3 LOW remanescentes documentados como tech debt rastreável NÃO bloqueante)
**Recomendação:** APROVADO para STORY 7 — fix de 1 linha + 2 testes regression resolveram F-PARSE-HIGH-01

---

### Re-gate evidências (sessão 53)

| Verificação | Resultado |
|---|---|
| Fix em `orchestrator.py:89-95` | ✅ Parênteses corretos: `if "rotativo" in text and ("cartão" in text or "cartao" in text):` |
| Comentário rastreável adicionado | ✅ Cita F-PARSE-HIGH-01 + explica precedência Python |
| Probe Oracle 7.5b re-executada (5 cenários) | ✅ 5/5 corretos: "cartao" isolado=CDC_VEICULOS_PF; "cartao débito automático"=CDC_VEICULOS_PF; "cartao+rotativo"=CARTAO_ROTATIVO; "cartão+rotativo"=CARTAO_ROTATIVO; "rotativo" sozinho sem cartao=CDC_VEICULOS_PF |
| `test_modalidade_cartao_rotativo_detectada` (happy path) | ✅ PASS — sem regressão |
| `test_modalidade_cartao_isolado_nao_dispara_rotativo` (regression) | ✅ PASS |
| `test_modalidade_cartao_sem_til_isolado_nao_dispara_rotativo` (regression) | ✅ PASS |
| Suite TestMetadataExtraction completa | ✅ 12/12 PASS |
| Suite agregada | ✅ 153 passed + 1 xfailed, 62.31s |
| Mensagens assert dos testes regression | ✅ Citam "bug F-PARSE-HIGH-01 reapareceu" — rastreabilidade futura |

### Status observations remanescentes (3 LOW — inalteradas, NÃO bloqueiam)

- O-11 LOW (Marker default não testado) — defer
- O-12 LOW (PyMuPDF default não testado) — defer
- O-13 LOW (valor sem centavos) — zero impacto CDC veículos atual

---

### Veredito anterior (sessão 50 — preservado para auditoria)

[@qa · Oracle · Test Architect & Quality Advisor] — quality gate STORY 6 SUB-B bloco_engine/parsing
**VEREDICTO: CONCERNS** (1 HIGH bug lógica + 3 LOW observations + 1 gap cobertura testes)
**Recomendação:** APROVADO COM RESSALVA — Neo DEVE corrigir F-PARSE-HIGH-01 antes da STORY 7 OU registrar WAIVED formal com remediation_date

---

## 1. Escopo auditado

| Artefato | Linhas | Cobertura testes |
|---|---|---|
| `bloco_engine/parsing/__init__.py` | 47 | re-export — N/A |
| `bloco_engine/parsing/pymupdf_parser.py` | 53 | mocked via parser_fn |
| `bloco_engine/parsing/marker_parser.py` | 60 | path indisponível confirmado real |
| `bloco_engine/parsing/fidelity.py` | 60 | 4 testes diretos + probes Oracle |
| `bloco_engine/parsing/orchestrator.py` | 200 | 17 testes diretos + probes Oracle |
| `tests/unit/test_parsing.py` | 277 | self |
| `bloco_engine/__init__.py` (delta `+parsing`) | 2 linhas | n/a |

**Suite agregada:** 151 passed + 1 xfailed (intencional smoke F-MIN-02), 0 failed, runtime 45.68s.
**Delta vs Phase 2.B sessão 46:** 125 → 151 (+26 testes parsing).

---

## 2. Verificações executadas (D1-D7)

### D1 — Conformidade FR-PARSE-01..02

| Requisito | Implementação | Status |
|---|---|---|
| **FR-PARSE-01** PyMuPDF4LLM primário + Marker fallback OCR | `parse_contract` orquestra ambos; fidelity_threshold decide escalar | PASS |
| **FR-PARSE-01 AC** fidelity ≥0.95 para tabela amortização | heurística 3-dim + threshold default 0.5 (conservador) | PASS — heurística operacional, não validada contra ground truth |
| **FR-PARSE-02** ContratoMetadata extraída via regex PT-BR | UF, data, modalidade, valor_financiado, taxas aa/am, n_parcelas | **PARCIAL** — modalidade tem bug F-PARSE-HIGH-01 |

**PARCIAL — FR-PARSE-02 modalidade comprometida pelo bug HIGH.**

### D2 — Conformidade D-MOR-3.2-A..D arquiteturais

| Decisão | Implementação | Status |
|---|---|---|
| D-MOR-3.2-A PyMuPDF primário sempre | `parse_contract` chama PyMuPDF antes do fallback | PASS |
| D-MOR-3.2-B Marker fallback APENAS se fidelity baixo OU vazio | `if fidelity < fidelity_threshold:` aciona fallback | PASS |
| D-MOR-3.2-C Marker indisponível levanta ParserOCRRequired (não silent) | `_is_marker_available()` + raise explícito | PASS — confirmado real (probe Oracle: Marker NÃO instalado no ambiente atual) |
| D-MOR-3.2-D parser_used registra parser efetivo | string atribuída em `parse_contract`, persiste em ParsedContract | PASS — confirmado probe 5.A/5.B |

**PASS — 4/4 decisões arquiteturais respeitadas.**

### D3 — Validação cruzada independente Oracle (8 probes adversariais)

| # | Probe | Resultado | Status |
|---|---|---|---|
| 1.1-1.5 | Regex UF — siglas inválidas, palavras com 4 letras (BATOM, TJBA), minúsculas, "CE/SP" | None corretos / SP correto / boundary funciona | PASS |
| 2.1-2.6 | Regex data — 31/02 inválido, ISO mês/dia inválidos, 2-dígitos, ano futuro 2099, ISO+BR conflito, "12345-67-89" | Defesa em 2 camadas (regex + Pydantic field_validator) | PASS — TD-PARSE-02 (Neo) confirmado |
| 3.1-3.6 | Fidelity — só tabela, só monetário, gaming repetição, contrato curto, vazio whitespace, None | Heurística robusta a gaming (keywords distintas, não contagem); defesa None | PASS |
| 4.1-4.2 | Marker indisponível REAL no ambiente | `_is_marker_available()=False`, ParserOCRRequired levantado com mensagem clara | PASS |
| 5.A-5.C | parse_contract end-to-end — parser_used auditável + fallback + hash determinístico | Todos comportamentos esperados confirmados (parser_used="pymupdf4llm"→"marker_ocr"; hash bate) | PASS |
| 6.1-6.5 | Decimal precision — 1.234.567,89 / 0,01 / sem centavos / múltiplos / negativo | Funciona para milhares; **não captura "R$ 100" sem centavos** (regex exige `,\d{2}`) | OBSERVATION O-13 |
| 7.1-7.4 | n_parcelas — "1000 parcelas" (1-3 dígitos), 480 limite, "1 parcela" singular, "00 parcelas" | Robusto por design (regex \s* + parcelas? exige whitespace+palavra; range check 1-480) | PASS |
| **7.5b** | **Modalidade — APENAS "cartao" sem "rotativo" sem "cartão"** | **BUG: retorna CARTAO_ROTATIVO indevidamente** | **F-PARSE-HIGH-01** |

### D4 — Cobertura cenários (test_parsing.py)

| Cenário | Coberto? | Teste |
|---|---|---|
| SHA256 hash determinístico | ✅ | TestContractHash (3 testes) |
| Fidelity vazio/rico/lixo/só-keywords | ✅ | TestFidelityScore (4 testes) |
| Metadata extração rica + ISO + 3 modalidades + UF/data ausentes + overrides + pré-1986 + n_parcelas fora faixa + opcionais None | ✅ | TestMetadataExtraction (10 testes) |
| Happy path PyMuPDF + bytes override + fallback Marker + Marker indisponível ParserOCRRequired + falha overrides ausentes | ✅ | TestParseContract (5 testes) |
| Propagação PDFEncrypted/PDFInvalid | ✅ | TestParserLowLevelErrors (2 testes) |
| Threshold custom (0/alto) | ✅ | TestFidelityThreshold (2 testes) |
| **Bug precedência operadores em modalidade ("cartao" sem rotativo)** | **❌** | **GAP — não coberto** |
| **Decimal sem centavos "R$ 100"** | **❌** | **GAP — não coberto (cosmético)** |
| **Múltiplas UFs no contrato (comprador + vendedor)** | **❌** | **GAP TD-PARSE-01 documentado pelo Neo** |
| **Múltiplas datas (assinatura + nascimento)** | **❌** | **GAP TD-PARSE-02 documentado pelo Neo** |

**PASS PARCIAL — 26 cenários cobertos; 4 gaps (1 HIGH + 3 LOW/cosmético/já-documentados).**

### D5 — Cobertura código (estimada)

| Módulo | Estimativa | Limites NFR-MAINT-02 |
|---|---|---|
| `parsing/__init__.py` | n/a (re-export puro) | — |
| `parsing/pymupdf_parser.py` | ≥80% (paths mockados; `_default_pymupdf_parser` real não testado mas isolado em lazy import) | ≥80% bloco_engine ✅ |
| `parsing/marker_parser.py` | ≥75% (`_is_marker_available` testado real; `_default_marker_parser` lazy não chamado) | ≥80% bloco_engine — borderline OBSERVATION |
| `parsing/fidelity.py` | ≥90% (4 testes + 6 probes) | ≥80% bloco_engine ✅ |
| `parsing/orchestrator.py` | ≥85% (17 testes diretos cobrem maior parte; bug em `_extract_modalidade` revela path não-coberto) | ≥80% bloco_engine ✅ |

**PASS PARCIAL — média ≥85% mas marker_parser borderline e bug modalidade indica gap parcial.**

### D6 — Conformidade transversal

| Aspecto | Status | Evidência |
|---|---|---|
| Tipo seguro (mypy strict compatible) | OK | `from __future__ import annotations`, anotações completas, `Any` apenas em parser_fn (DI legítimo) |
| Decimal everywhere (FR-CALC-01) | OK | `valor_financiado` e taxas como string Decimal-safe |
| NFR-LGPD-01 (parsing 100% local) | OK | nenhum import HTTP; PyMuPDF + Marker são bibliotecas locais |
| Erro rastreável (exceções customizadas com hierarquia) | OK | ParserError → {PDFEncrypted, PDFInvalid, ParserOCRRequired, MetadataExtractionError} |
| Lazy import (não trava startup) | OK | PyMuPDF + Marker importados dentro de funções `_default_*` |
| ADR-scope cumprida (ADR-design vs ADR-spec) | OK — implementação de design |
| Bug fix in-flight documentado | OK — comentário no código sobre `periodo[1]` |

**PASS — limpo transversalmente.**

### D7 — Pecados Capitais (Ordem 10) — verificação

| Pecado | Verificado | Status |
|---|---|---|
| Inventar dado/métrica não-mensurada | fidelity_score é HEURÍSTICO documentado como tal — não inventa precisão | OK |
| Float em wire format monetário | valor/taxas são string Decimal-safe | OK |
| Silenciar erro (except: pass) | `try: import marker except ImportError:` é padrão Python idiomático para deps opcionais | OK |
| Authority alheia | Neo escreveu código (legítimo); QA não escreve código | OK |
| Cabeçalho ausente | Este documento tem cabeçalho 3 linhas | OK |

**PASS — 0 violações.**

---

## 3. Findings

### HIGH (1 — bloqueia se não corrigida ou WAIVED)

- **F-PARSE-HIGH-01** — Bug precedência operadores em `_extract_modalidade`
  - **Localização:** `bloco_engine/parsing/orchestrator.py:80-88`
  - **Código atual:**
    ```python
    if "rotativo" in text and "cartão" in text or "cartao" in text:
        return "CARTAO_ROTATIVO"
    ```
  - **Bug:** precedência Python avalia como `(rotativo AND cartão) OR cartao`. Se APENAS "cartao" (sem til, sem "rotativo") aparece no markdown, retorna CARTAO_ROTATIVO **indevidamente**.
  - **Impacto material:** contratos CDC veículos PF frequentemente mencionam "cartão de débito automático" para débito de parcelas — toda modalidade seria classificada erradamente como CARTAO_ROTATIVO, levando o juiz para checagens C2/C3 com mapping de súmulas erradas.
  - **Confirmação:** probe Oracle 7.5b — `_extract_modalidade('contrato CDC veiculo com pagamento cartao')` retornou `CARTAO_ROTATIVO`.
  - **Fix recomendado:**
    ```python
    if "rotativo" in text and ("cartão" in text or "cartao" in text):
        return "CARTAO_ROTATIVO"
    ```
  - **Teste a adicionar:** `test_modalidade_cartao_isolado_nao_dispara_rotativo` cobrindo casos com "cartão de débito" em contrato veicular.

### MEDIUM — 0

### LOW (3 — tech debt rastreável NÃO bloqueante)

- **O-11 LOW** — Marker `_default_marker_parser` não tem testes (só lazy path)
  - **Justificativa:** Marker é dep opcional; CI roda sem ele instalado. Quando STORY de teste integration com PDFs imagem-only chegar, instalar Marker e cobrir.
  - **Recomendação:** adicionar marker no `dev` extras temporariamente quando STORY apropriada chegar OU manter como tech debt explícito.

- **O-12 LOW** — `_default_pymupdf_parser` real não testado
  - **Justificativa:** parser_fn injection cobre lógica do orchestrator; a integração com PyMuPDF real fica para teste integration com PDF físico.
  - **Recomendação:** 1 teste integration com PDF sintético gerado in-memory via `pymupdf` low-level API quando STORY apropriada chegar.

- **O-13 LOW** — Regex valor_financiado exige centavos obrigatórios `,\d{2}`
  - **Localização:** `orchestrator.py` `_extract_valor_financiado`
  - **Confirmação:** probe Oracle 6.3 — "R$ 100" (sem centavos) retorna None.
  - **Impacto:** zero atual (CDC veículos PF sempre tem centavos). Risco se outras modalidades forem suportadas com valores arredondados.
  - **Recomendação:** quando CDC_BENS_PF / CDC_IMOBILIARIO forem implementadas, tornar centavos opcionais `(?:,\d{2})?`.

### CRITICAL — 0

### Gap de cobertura testes (correlacionado a F-PARSE-HIGH-01)

O bug F-PARSE-HIGH-01 NÃO foi capturado porque os testes só cobriam casos "felizes" (cartão + rotativo juntos) — faltou caso adversarial "cartão sem rotativo" e "cartao sem til sem rotativo". Lição: testes Neo precisam casos adversariais explícitos quando há keyword logic com OR.

---

## 4. Métricas

| Métrica | Valor |
|---|---|
| Testes parsing | 26 |
| Testes suite agregada | 151 + 1 xfailed = 152 |
| Falhas | 0 |
| Runtime suite agregada | 45.68s |
| Linhas código produção (parsing/*.py exclui __init__) | 373 |
| Linhas código teste (test_parsing.py) | 277 (0.74× ratio teste:produção — borderline; ideal ≥1.0) |
| Cobertura cenários distintos | 26 |
| Probes Oracle adversariais | 8 |
| FR cobertos (com ressalva) | 2/2 (FR-PARSE-01 PASS, FR-PARSE-02 PARCIAL — modalidade comprometida) |
| D-MOR cobertos | 4/4 (D-MOR-3.2-A..D PASS) |
| Findings HIGH | 1 (F-PARSE-HIGH-01) |
| Findings LOW | 3 |
| Bug fix in-flight detectado por testes | 1 (`periodo[0]→[1]`) |
| Bug HIGH não capturado por testes Neo (gap) | 1 (F-PARSE-HIGH-01) |

---

## 5. Recomendação ao Morpheus

**APROVADO COM RESSALVA** — caminho recomendado:

### Opção A (preferencial): Fix loop antes de STORY 7
1. Neo aplica fix de 1 linha em `orchestrator.py` (parênteses corrigem precedência)
2. Neo adiciona 2 testes adversariais (`cartao` isolado em contrato CDC veículos / `cartão de débito automático` em contrato veicular)
3. Re-rodar pytest → suite verde
4. Oracle re-gate rápido → PASS
5. STORY 7 destravada

### Opção B (se urgência): WAIVED formal
1. Neo registra WAIVED em formato simplificado (projeto solo — `quality-gate-enforcement.md` permite)
2. Remediation_date obrigatório (sugestão: antes da STORY de integração workflow_test que efetivamente USE modalidade)
3. STORY 7 prossegue, mas com débito formal

### Próxima sub-fronteira pós-fix:
Mantém recomendação ordinal de risco crescente: **SUB-D LLM → SUB-C vault** (sqlite-vec ainda jovem; adiar).

---

## 6. Linhagem governance

- Antecedente: `qa/qa-gate-story-5-sub-a-bacen.md` (PASS sessão 46)
- Handoff de entrada: H-S01-E3.2-neo2qa3 (Neo→Oracle)
- Handoff de saída: H-S01-E3.2-qa2mor3 (Oracle→Morpheus consolida)
- Sessão checkpoint: 50

---

*Oracle, guardião da qualidade — uma única letra de precedência separa decisão correta de classificação fantasma.*
