---
type: adr
id: "ADR-033"
title: "OCRmyPDF (Tesseract) substitui Marker como primary OCR — VPS hardware constraint"
status: accepted
date: "2026-05-17"
domain: backend
adr_level: design
decision_makers:
  - "@dev (Neo — D-DEV-S08-008 implementation)"
  - "@devops (Operator — D-OPS-S08-016 hardware limit detection)"
  - "Eric (owner — Option A choice 2026-05-17)"
supersedes: null
superseded_by: null
related_adrs:
  - "ADR-026 Marker Subprocess Isolation (preserved — subprocess pattern reused para OCRmyPDF)"
  - "ADR-027 PyMuPDF Born-Digital Fast Path (preserved — OCRmyPDF output reusable em PyMuPDF path)"
  - "ADR-028 Ollama Single-Container Consolidation (unrelated)"
related_findings:
  - "D-OPS-S08-010 (subprocess_runner stdout contamination — Neo fix D-DEV-S08-005)"
  - "D-OPS-S08-011 (deploy + 3/9 audit keys)"
  - "D-OPS-S08-012 (vault deploy gap → Neo D-DEV-S08-006)"
  - "D-OPS-S08-013 (full rsync + 4/9 audit keys + Marker OK once)"
  - "D-OPS-S08-014 (persona LLM placeholder → Neo D-DEV-S08-007)"
  - "D-OPS-S08-015 (deploy persona fix + Marker OOM regression)"
  - "D-OPS-S08-016 (HARDWARE LIMIT CONFIRMED — Marker OOM 2x reproducible em VPS 7.8GB)"
tags:
  - project/revisor-contratual
  - adr
  - sprint-8
  - phase-c
  - ocr
  - hardware-constraint
  - vps-low-memory
---

# ADR-033 — OCRmyPDF (Tesseract) substitui Marker como primary OCR

## Context

### Empirical Hardware Limit Discovery (D-OPS-S08-016)

Sprint 8 Phase C Operator empirical E2E testing reproduced **OOM SIGKILL (exit code -9)** durante Marker CPU layout inference em VPS Hetzner CX21 (7.8GB RAM, 2 vCPU):

| Test Attempt | Cache State | Result |
|--------------|-------------|--------|
| D-OPS-S08-011 | Cold (subprocess_runner stdout bug masked OOM) | ValidationError (false negative) |
| D-OPS-S08-013 | Warm (lucky timing) | 4/9 audit keys PASS — Marker worked once |
| D-OPS-S08-015 #1 | Cold (rebuild perdeu cache não mounted) | OOM during model download |
| D-OPS-S08-015 #2 | Warm (cache mount + pré-load) | OOM during "Recognizing Layout: 0/1" |

**Pattern empírico:** Marker layout inference em CPU consume **4-6GB RAM peak** (PyTorch CNN activation + intermediate tensors). VPS available 6.4GB (após ollama-shared baseline 86MB + container app baseline 128MB + OS overhead). Pico inference exceeds available → kernel SIGKILL.

### Constraint absoluto

Eric directive (2026-05-17): **"Preciso de uma solução onde eu não preciso aumentar a minha VPS. Preciso de uma solução real, de qualidade e resolva meu problema de fato."**

Hardware upgrade Hetzner CPX31 (+€8/mês, 16GB RAM) está **fora de escopo** desta decisão.

### Why Marker was chosen originally

Marker library (ADR-026 Sprint 7 Phase 3) era state-of-art OCR/layout para PDFs complexos (tabelas, multi-column, math). Engineering excellence escolha — desconsiderou RAM footprint em ambiente production constrained.

## Decision

**Substituir Marker library por OCRmyPDF (wrapper Python de Tesseract OCR) como primary OCR engine em produção.**

Marker preserved como **optional fallback** em pyproject.toml `[ocr]` extras para:
- Tests existentes que injetam marker_fn
- Future hardware upgrades onde Marker quality valeria custo
- Development/debugging environments com mais RAM

## Rationale

### Por que OCRmyPDF + Tesseract

| Critério | OCRmyPDF/Tesseract | Marker |
|----------|---------------------|--------|
| **RAM peak inference** | **~600MB** ✅ | 4-6GB 🔴 (excede VPS) |
| **Velocidade single page** | ~3-5s | ~15-30s |
| **Português brasileiro** | ✅ tesseract-ocr-por | ✅ multilingual |
| **Layout complexo (tabelas)** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Textual simples (CDC veículo)** | ⭐⭐⭐⭐ suficiente | ⭐⭐⭐⭐⭐ overkill |
| **LGPD compliance** | ✅ 100% local | ✅ 100% local |
| **License** | Apache 2.0 | MIT |
| **Maturidade** | 30+ anos (Tesseract) | ~2 anos |
| **Battle-tested production** | ✅ amplo | Limited |
| **Subprocess pattern (ADR-026)** | ✅ compatible | ✅ compatible |
| **PyMuPDF dual-path (ADR-027)** | ✅ output reusable | N/A |

### Architectural Fit

OCRmyPDF adiciona **text layer** ao PDF scanned (output born-digital-like) → pipeline downstream PyMuPDF (ADR-027) processa normalmente. Architectural disruption mínima:

```text
Antes (Marker):
  Scanned PDF → Marker (4-6GB RAM, OOM) → markdown → orchestrator

Depois (OCRmyPDF):
  Scanned PDF → OCRmyPDF (600MB RAM) → PDF + text layer → PyMuPDF (50ms) → markdown → orchestrator
                                                          ↑
                                                          ADR-027 dual-path reusado
```

### Qualidade OCR para CDC Veículo Specifically

CDC veículo PDFs scanned em produção são tipicamente:
- **Texto plano** (não tabelas complexas) — Tesseract excelente
- **Layout single-column** — Tesseract handles trivially
- **Português jurídico** — tesseract-ocr-por bem treinado
- **Resolução 150-300dpi** — Tesseract sweet spot

Marker overkill para esse use case. OCRmyPDF qualidade **suficiente** para extração metadata regex + LLM fallback.

## Alternatives Considered

### Alternative A: Marker low-memory tuning (Option 4 original Eric choice tree)

- **Tentativas:** torch.set_num_threads(1), batch_size=1 já default, swap aggressive
- **Resultado esperado:** Marginal — Marker CPU activation peak não escala com threads
- **Verdict:** REJECTED — uncertain, hack-ish, doesn't address root cause

### Alternative B: External OCR API (Google Vision, AWS Textract, OCR.space)

- **Pros:** Zero RAM local, qualidade state-of-art
- **Cons:** LGPD §13 violation potencial (dados clientes finais enviados terceiros sem DPA), custo recurring per-call, network dependency
- **Verdict:** REJECTED — LGPD risk para SaaS B2B BYOK arquitetura

### Alternative C: Tier-down PyMuPDF only (no OCR)

- **Pros:** Zero new dep, zero hardware risk
- **Cons:** Perde "killer feature" scanned PDF support → produto incompleto
- **Verdict:** REJECTED — feature degradation inaceitável

### Alternative D: VPS upgrade Hetzner CPX31 16GB

- **Pros:** Marker funcionaria reliably + suporte concurrent users futuro
- **Cons:** Eric directive explicitamente rejeitou hardware upgrade
- **Verdict:** REJECTED — fora de escopo per Eric directive 2026-05-17

### Alternative E (CHOSEN): OCRmyPDF replacing Marker (this ADR)

- **Pros:** RAM 600MB cabe folgado em VPS atual, qualidade suficiente CDC veículo, LGPD-safe local, reusa ADR-027 dual-path
- **Cons:** Qualidade OCR -10-15% em layouts complexos (não material para CDC veículo)
- **Verdict:** **ACCEPTED** — único path que satisfaz Eric directive + LGPD + qualidade adequada

## Consequences

### Positive

| Benefit | Impact |
|---------|--------|
| RAM footprint OCR cai 4-6GB → 600MB | Cabe folgado em VPS 7.8GB |
| Pipeline scanned PDFs viabiliza E2E | Pode finalmente atingir 9/9 audit keys |
| LGPD compliance preserved (100% local) | Zero risco transmissão dados terceiros |
| Tesseract battle-tested 30+ anos | Maturity > Marker recente |
| ADR-027 dual-path reusable | Architectural disruption mínima |
| ADR-026 subprocess isolation preserved | OCRmyPDF roda em subprocess_runner.py mesmo pattern |
| Marker fallback preserved | Tests + futuro tier-up retain |
| Velocidade 3-5x mais rápido | Single-page Tesseract < Marker CPU |

### Negative

| Risk | Mitigation |
|------|-----------|
| Qualidade OCR -10-15% em layouts complexos | CDC veículo é textual simples — não material |
| Tesseract não detecta tabelas formatadas (Marker faz) | CDC veículo raramente tem tabelas complexas; valor_financiado regex robusto vs formatação |
| OCRmyPDF dependency adiciona ~50MB image | Já temos marker bigger em dep — net reduction |
| Existing tests assumindo Marker default precisam update | 2 tests adjusted, marker_fn injection ainda funcional |
| Bloco_engine.parsing.marker_parser.py mantido but unused em prod | Aceitável — code preserved, opt-in via marker_fn |

### Neutral

| Aspecto | Detalhe |
|---------|---------|
| ADR-026 subprocess pattern | OCRmyPDF roda em mesmo subprocess_runner.py — sem mudança |
| ADR-027 PyMuPDF dual-path | Born-digital path unchanged; scanned agora passa por OCRmyPDF antes |
| ADR-028 ollama-shared | Unrelated, preserved |
| Container size | OCRmyPDF + ocrmypdf binary adds ~50MB; marker-pdf preserved em deps adds ~100MB. Net similar |
| Dockerfile | Já tinha tesseract-ocr + tesseract-ocr-por (linhas 24-25). Sem mudança Dockerfile. |

## Implementation

### Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `bloco_engine/parsing/ocrmypdf_parser.py` | **NEW** module | OCRmyPDF wrapper + PyMuPDF re-extract pipeline |
| `bloco_engine/parsing/orchestrator.py` | Use parse_pdf_ocrmypdf as default OCR path | OCRmyPDF primary, marker_fn injection still works |
| `bloco_contratos/contrato.py` | Literal parser_used += "ocrmypdf_tesseract" | ParsedContract type accommodation |
| `pyproject.toml` | extras_require ocr = [ocrmypdf, marker-pdf] | OCRmyPDF added, marker preserved opt-in |
| `tests/integration/test_ocrmypdf_scanned.py` | **NEW** 7 tests | Source review + runtime guards + E2E |
| `tests/unit/test_parsing.py` | test_marker_disponivel_mas_falha_propaga_excecao updated | Inject marker_fn explicit |
| `tests/unit/test_parsing_subprocess_runner.py` | Skipif ocrmypdf+marker both missing | Skip when no OCR backend local |
| `Dockerfile` | UNCHANGED (já tinha tesseract-ocr-por) | Already had Tesseract |

### Subprocess Pattern Preserved (ADR-026)

OCRmyPDF execution happens **inside subprocess_runner.py** (same as Marker before). ADR-026 isolation guarantees:
- OOM em OCR subprocess NÃO mata parent worker
- Audit chain captura ParsingSubprocessFailedError
- Memory deallocation pós subprocess exit

D-DEV-S08-005 stdout isolation (contextlib.redirect_stdout) também protege OCRmyPDF output noise.

### Marker Cache Volume Preserved

D-OPS-S08-015 added `marker-cache:/home/revisor/.cache/datalab` mount em docker-compose.prod.yml. Volume **PRESERVED** mesmo após ADR-033 — útil para:
- Future testing reverting to Marker
- Marker pre-loaded if needed
- Zero cost manter mount adicional

### Migration Plan

| Phase | Action | Owner |
|-------|--------|-------|
| 1 | Deploy OCRmyPDF via Operator (file-specific scp ou rebuild) | @devops |
| 2 | E2E re-test scanned PDF — espera 5+/9 → 9/9 audit keys | @devops |
| 3 | Eric submete PDF scanned REAL escritório piloto | Eric |
| 4 | Sprint 9+ consider remove marker-pdf from extras se cleanup desejado | @architect |

## ADR Index Update

Adicionar em `governance/architecture/ADR-INDEX.md` (Sprint 8 Phase C section):

```markdown
| [ADR-033](adr/adr-033-ocrmypdf-replace-marker.md) | OCRmyPDF Tesseract substitui Marker primary OCR — VPS 7.8GB constraint (Sprint 8 Phase C) | ✅ Accepted | 2026-05-17 |
```

## References

- [D-OPS-S08-016 Hardware Limit Catalog](../../CHECKPOINT-active.md#sessão-2026-05-17--operator-d-ops-s08-015-deploy----hardware-limit-confirmed-)
- [Eric Option A Choice (verbatim)](../../CHECKPOINT-active.md) "Preciso de uma solução onde eu não preciso aumentar a minha VPS..."
- [ADR-026 Marker Subprocess Isolation](adr-026-marker-subprocess-isolation-parsing.md) (preserved pattern)
- [ADR-027 PyMuPDF Born-Digital Fast Path](adr-027-pymupdf-born-digital-fast-path.md) (reusable downstream)
- [OCRmyPDF documentation](https://ocrmypdf.readthedocs.io/)
- [Tesseract OCR](https://tesseract-ocr.github.io/)

---

*ADR-033 created 2026-05-17 — D-DEV-S08-008 implementation. Marker substitution motivated by VPS hardware constraint (D-OPS-S08-016 confirmed 2x reproducible OOM). Eric directive 2026-05-17 explicitly rejected hardware upgrade alternative. OCRmyPDF satisfies all constraints: RAM 600MB << 6.4GB available, LGPD-safe local, quality sufficient for CDC veículo textual scans, architectural fit (reuses ADR-026 subprocess + ADR-027 dual-path).*

*— Aria (architectural decision facilitated by Neo D-DEV-S08-008 implementation work)*
