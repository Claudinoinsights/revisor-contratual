---
type: adr
id: ADR-027
title: "PyMuPDF Born-Digital Fast Path — Dual-Path Pipeline Step 1 (Sprint 7 Phase 4)"
status: accepted
date: "2026-05-16"
domain: backend
adr_level: spec
spec_coverage:
  - "PDF type detection (born-digital vs scanned) via PyMuPDF text extraction heuristic"
  - "Dual-path Step 1: inline (born-digital) vs subprocess (scanned)"
  - "Smart timeout per type (30s born-digital, 180s scanned)"
  - "parser_used field in audit chain (pymupdf4llm OR marker_ocr)"
  - "Preserve Phase 3 ADR-026 subprocess isolation as fallback"
  - "10 ACs Phase 4 verification"
decision_makers:
  - "@architect (Aria)"
  - "@smith (Smith — Phase 3 verify CONTAINED + F-PROD-NEW-22 RESOLVED architecturally)"
  - "@dev (Neo — Phase 4 implementation)"
  - "Eric (owner — directive Cenário Y++ AskUserQuestion 2026-05-16)"
related_adrs:
  - "ADR-026 Marker Subprocess Isolation Parsing (preserved — scanned PDF fallback path)"
  - "ADR-023/024/025/028 (preserved — sequential LLM + tier + cascade + ollama-shared)"
related_findings:
  - "F-S7P3-MED-01 Pipeline E2E REAL 9/9 keys BLOCKED subprocess timeout 180s — RESOLVED por this ADR"
  - "F-S7P3-MED-02 Marker cache ephemeral — Phase 5 polish OR optional Phase 4 include"
tags:
  - project/revisor-contratual
  - adr
  - sprint-7
  - phase-4
  - pymupdf-fast-path
  - dual-path
  - cenario-y-plus-plus-dod-final
---

# ADR-027 — PyMuPDF Born-Digital Fast Path (Sprint 7 Phase 4)

## Context

### Phase 3 deployed Sprint 6.x F-PROD-NEW-22 fix arquitetural

Subprocess isolation (ADR-026) RESOLVED F-PROD-NEW-22 silent worker exit empirically:

- App container preserved (RestartCount=0 across pipeline crash)
- Audit chain registers `ParsingSubprocessTimeoutError` graceful
- Operator honesty Phase 3: 5/5 (best Sprint 7)

### Smith F-S7P3-MED-01 — Pipeline E2E REAL 9/9 keys BLOCKED

Empirical Phase 3 test:
- Submit Contrato Financiamento Veículo PDF (2.15MB 12 pages)
- Subprocess spawned (marker library load 3.3GB cache + OCR Tesseract)
- Timeout fired 180s ANTES Step 2 (BACEN + calculo + personas + redator + juiz)
- Pipeline 9/9 audit keys NÃO atingido — **Cenário Y++ DoD final criterion BLOCKED**

### Insight chave: 80% CDC veículo PDFs são born-digital

CDC contratos gerados por sistemas bancários (Itaú, Bradesco, etc.) são tipicamente **born-digital PDFs** (text-extractable nativamente). Apenas ~20% são scanned (image-based — copy de contratos físicos digitalizados).

**Born-digital characteristics:**
- PyMuPDF (fitz) extrai texto direto via `page.get_text()` — ~10ms per page
- Sem OCR needed (marker library 3.3GB unused)
- Fidelity score HIGH (>0.95)

**Scanned characteristics:**
- PyMuPDF `page.get_text()` retorna empty OR very low text count
- OCR mandatory (marker + Tesseract = 30-90s per page)
- Subprocess isolation essential (Phase 3 ADR-026)

### Existing orchestrator JÁ tem dual-path (fidelity-based)

`bloco_engine/parsing/orchestrator.py` linha 544-552:

```python
markdown, pages_count = parse_pdf_pymupdf(pdf_path, parser_fn=pymupdf_fn)
parser_used: str = "pymupdf4llm"
fidelity = compute_fidelity_score(markdown)

if fidelity < fidelity_threshold:
    # Fallback Marker — pode levantar ParserOCRRequired
    markdown, pages_count = parse_pdf_marker(pdf_path, parser_fn=marker_fn)
    parser_used = "marker_ocr"
```

**Problema atual:** orchestrator INTEIRO está em subprocess (Phase 3 ADR-026). Mesmo born-digital PDFs disparam subprocess overhead (~200ms subprocess startup + marker library imports mesmo se NÃO usado).

## Decision

**Pre-detect PDF type em pipeline.py Step 1 ANTES de decidir subprocess vs inline.**

- Born-digital (~80% casos): chamar `parse_contract()` **INLINE** via `asyncio.to_thread` (PyMuPDF é fast + stable)
- Scanned (~20% casos): chamar `parse_contract()` via **subprocess** (Phase 3 ADR-026 preserved)

PDF type detection: **PyMuPDF lightweight text extraction heuristic** — read first 2 pages, count tokens, classify.

## Rationale

### Por que pre-detect (vs always subprocess)

- Subprocess overhead +200-500ms para borrn-digital PDFs (97% casos onde não precisa)
- Marker library imports (~3-5s) NÃO necessários para born-digital
- Smart timeout: born-digital 30s suficiente, scanned 180s precisa marker OCR

### Por que PyMuPDF inline para born-digital (vs subprocess)

- PyMuPDF (fitz) é C extension MAS estável (~10 anos production)
- F-PROD-NEW-22 hypothesis H1 (marker/surya os._exit) NÃO aplica para PyMuPDF nativo
- F-PROD-NEW-22 hypothesis H3 (PyMuPDF SIGABRT) é improvável em born-digital path (PyMuPDF native handling sem OCR)
- asyncio.to_thread sufficient (event loop não bloqueia — born-digital é fast)

### Por que preserve subprocess para scanned

- Marker library + torch.multiprocessing = high-risk (F-PROD-NEW-22 root cause)
- Subprocess isolation ESSENTIAL (Phase 3 ADR-026 architectural fix)
- Scanned PDFs already require marker OCR overhead → subprocess overhead trivial

### Por que NÃO sempre PyMuPDF (sem subprocess fallback)

- Scanned PDFs PyMuPDF retorna empty markdown → pipeline crash em Step 2-9
- Marker OCR mandatory para scanned (Tesseract + layout detection)
- Dual-path strategy = best of both worlds

## Alternatives Considered

### Alternative A: Always marker subprocess (current Phase 3)

**Cons:** Too slow para 80% born-digital casos (200ms overhead + 3-5s marker load + 60-90s OCR even quando PyMuPDF resolveria em 10ms-1s)
**Verdict:** Rejected — Phase 4 explicitly resolves this

### Alternative B: Always PyMuPDF (no subprocess fallback)

**Cons:** Scanned PDFs (20% casos) crashs (PyMuPDF retorna empty markdown sem OCR)
**Verdict:** Rejected — não cobre scanned scenario

### Alternative C: Always subprocess (dual orchestrator path within subprocess)

**Cons:** Overhead unnecessary para born-digital. Subprocess startup ~200ms cumulative em 100s of users = waste
**Verdict:** Rejected — overhead unjustified

### Alternative D: Dual-path pre-detect (CHOSEN — this ADR)

**Pros:** 80% cases fast inline + 20% cases safe subprocess. Best of both.
**Cons:** PDF type detection adds ~50ms (negligible)
**Verdict:** ACCEPTED

## Consequences

### Positive

| Benefit | Impact |
|---------|--------|
| Pipeline E2E REAL 9/9 keys ATINGIDO (born-digital) | Cenário Y++ DoD final criterion RESOLVED for 80% cases |
| Latency 80% cases 180s → 10s | Subprocess overhead eliminated for fast path |
| Memory savings born-digital | No marker library load (saves 3.3GB) |
| Subprocess fallback preserved | Phase 3 F-PROD-NEW-22 fix architecturally intact |
| Audit chain `parser_used` field populated | Forensic visibility |

### Negative

| Risk | Mitigation |
|------|-----------|
| PDF type detection misclassifies | Threshold calibration + fallback retry path |
| PyMuPDF inline crash em edge case | asyncio.to_thread limits damage to thread (no full process kill expected for born-digital) |
| Mixed PDFs (born-digital + scanned pages) | Primary path detection + fallback if fidelity score low |

### Neutral

| Aspecto | Detalhe |
|---------|---------|
| orchestrator.py unchanged | parse_contract() preserved (fidelity-based dual-path internal) |
| Phase 3 ADR-026 preserved | Subprocess module + exceptions reused |

## PDF Type Detection Spec

### Module: `bloco_engine/parsing/type_detector.py` (NEW)

```python
"""PDF type detection — Sprint 7 Phase 4 (ADR-027).

Detects born-digital vs scanned PDFs via PyMuPDF text extraction heuristic.

Born-digital: text-extractable (PyMuPDF returns substantial text)
Scanned: image-based (PyMuPDF returns empty or minimal text)
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import fitz  # PyMuPDF


# Empirical threshold — characters per page below which considered scanned
# Adjusted via empirical testing com CDC veículo fixtures Phase 4
DEFAULT_TEXT_THRESHOLD_PER_PAGE = 500  # chars (~100 tokens)


def detect_pdf_type(
    pdf_path: Path,
    sample_pages: int = 2,
    text_threshold_per_page: int = DEFAULT_TEXT_THRESHOLD_PER_PAGE,
) -> Literal["born_digital", "scanned"]:
    """Detects PDF type via PyMuPDF text extraction heuristic.

    Args:
        pdf_path: Path to PDF file
        sample_pages: Number of first pages to sample (default 2)
        text_threshold_per_page: Min chars per page para born-digital (default 500)

    Returns:
        "born_digital" if avg text per sampled page >= threshold
        "scanned" otherwise

    Performance: <50ms typical (PyMuPDF lightweight read)

    Edge cases:
    - Empty PDF → "scanned" (no text)
    - 1-page PDF → samples only 1 page
    - Mixed PDFs (some born + some scanned pages) → majority vote via threshold
    """
    doc = fitz.open(pdf_path)
    try:
        pages_to_sample = min(sample_pages, doc.page_count)
        if pages_to_sample == 0:
            return "scanned"

        total_chars = 0
        for page_num in range(pages_to_sample):
            page = doc[page_num]
            text = page.get_text() or ""
            total_chars += len(text)

        avg_chars_per_page = total_chars / pages_to_sample
        return "born_digital" if avg_chars_per_page >= text_threshold_per_page else "scanned"
    finally:
        doc.close()
```

## pipeline.py Step 1 Refactor

### Atual (Phase 3 — always subprocess)

```python
# bloco_workflow/pipeline.py Step 1 (Phase 3 ADR-026)
metadata_dict = {...}
with tempfile.NamedTemporaryFile(...) as metadata_file:
    metadata_path = metadata_file.name

try:
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "bloco_engine.parsing.subprocess_runner",
        str(pdf_path), metadata_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # ... timeout 180s + error handling ...
```

### Proposto Phase 4 (dual-path pre-detect)

```python
# bloco_workflow/pipeline.py Step 1 (Phase 4 ADR-027 dual-path)
from bloco_engine.parsing.type_detector import detect_pdf_type

# Detect PDF type ANTES decidir path (lightweight ~50ms)
pdf_type = await asyncio.to_thread(detect_pdf_type, pdf_path)

if pdf_type == "born_digital":
    # Fast path: PyMuPDF inline via asyncio.to_thread
    # (event loop não bloqueia — PyMuPDF é fast + stable C extension)
    try:
        parsed = await asyncio.wait_for(
            asyncio.to_thread(
                parse_contract,
                pdf_path,
                pdf_bytes=pdf_bytes,
                uf_override=uf_override,
                data_override=data_override,
                pymupdf_fn=pymupdf_fn,
                marker_fn=marker_fn,
            ),
            timeout=30.0,  # Smart timeout per type — 30s suficiente born-digital
        )
    except asyncio.TimeoutError as exc:
        raise ParsingSubprocessTimeoutError(
            f"parse_contract born-digital timeout 30s for {pdf_path}"
        ) from exc

else:
    # Scanned path: subprocess isolation (Phase 3 ADR-026 preserved)
    # ... existing subprocess code com timeout 180s ...
```

## Phase 4 Acceptance Criteria

| AC | Description | Verification |
|----|-------------|--------------|
| **AC-1** | PDF type detector works (born-digital + scanned fixtures) | Unit tests fixtures `cdc-veiculo-born-digital.pdf` + `cdc-veiculo-scanned.pdf` |
| **AC-2** | Born-digital path uses PyMuPDF inline (NO subprocess) | Integration test verifies asyncio.to_thread call (not create_subprocess_exec) |
| **AC-3** | Scanned path uses subprocess marker (Phase 3 ADR-026 preserved) | Integration test verifies create_subprocess_exec call |
| **AC-4** | **Pipeline E2E REAL 9/9 keys ATINGIDO** com born-digital fixture | E2E test submit + tail audit.jsonl mostra status=success + 9+ keys |
| **AC-5** | Smart timeout per type (born-digital 30s, scanned 180s) | Code review verification + timeout edge case test |
| **AC-6** | audit_payload.parser_used="pymupdf4llm" OR "marker_ocr" per type | E2E test inspect audit payload |
| **AC-7** | Memory baseline born-digital path < 500 MB | docker stats during born-digital pipeline (parent NÃO loads marker 3.3GB) |
| **AC-8** | Phase 3 F-PROD-NEW-22 fix PRESERVED (subprocess fallback funcional) | Test subprocess path com scanned fixture → RestartCount=0 + audit registered |
| **AC-9** | Container lifecycle DECLARED (per ADR-026 terminology precisa) | Operator deploy report compliance |
| **AC-10** | Latency 80% cases < 30s (vs Phase 3 180s timeout) | Empirical benchmark born-digital fixture |

## Phase 4 Operator Deploy Steps

```bash
# 1. Backup pre-Phase-4 image
sudo docker tag revisor-contratual:prod revisor-contratual:bak-pre-phase-4

# 2. scp Neo files → VPS (3 files modified)
scp bloco_engine/parsing/type_detector.py + orchestrator.py? + bloco_workflow/pipeline.py
# (Plus updated subprocess_runner.py if Neo refactored)

# 3. Image rebuild
cd /opt/revisor-contratual && sudo docker build -t revisor-contratual:prod .

# 4. Container recreate (terminology precisa per ADR-026)
sudo docker compose -p revisor-prod up -d app

# 5. Smoke test BOTH paths:
#    - Born-digital fixture submit → expect ~10s + 9/9 audit keys
#    - Scanned fixture submit → expect ~120s subprocess + 9/9 OR graceful error
```

## Tests Strategy (Neo Deliverable)

### Unit Tests

```python
# tests/unit/test_pdf_type_detector.py
def test_detect_born_digital_pdf():
    """AC-1: Born-digital PDF returns 'born_digital'"""
    assert detect_pdf_type(Path("tests/fixtures/cdc-veiculo-born-digital.pdf")) == "born_digital"

def test_detect_scanned_pdf():
    """AC-1: Scanned PDF returns 'scanned'"""
    assert detect_pdf_type(Path("tests/fixtures/cdc-veiculo-scanned.pdf")) == "scanned"

def test_detect_empty_pdf():
    """Edge case: empty PDF returns 'scanned'"""
    # ...
```

### Integration Tests

```python
# tests/integration/test_pipeline_dual_path.py
async def test_pipeline_born_digital_uses_inline():
    """AC-2: Born-digital path uses asyncio.to_thread (not subprocess)"""
    # Mock asyncio.create_subprocess_exec and asyncio.to_thread
    # Submit born-digital fixture
    # Assert create_subprocess_exec NOT called for parse_contract
    # Assert to_thread called for parse_contract

async def test_pipeline_scanned_uses_subprocess():
    """AC-3: Scanned path uses subprocess marker (Phase 3 ADR-026)"""
    # Submit scanned fixture
    # Assert create_subprocess_exec called
```

### E2E Tests

```python
# tests/e2e/test_pipeline_e2e_9_keys.py
@pytest.mark.e2e
async def test_pipeline_9_keys_born_digital():
    """AC-4: Pipeline E2E REAL 9/9 keys atingido born-digital"""
    response = await http_client.post("/revisar", files={"pdf": born_digital_fixture}, ...)
    # ... wait SSE complete
    audit_entry = read_audit_chain_latest()
    payload = audit_entry["payload"]
    assert payload["status"] == "success"
    assert len(payload.keys()) >= 9
    assert payload["parser_used"] == "pymupdf4llm"
```

## Test Fixtures (Neo Deliverable)

| Fixture | Path | Generation |
|---------|------|-----------|
| born-digital | `tests/fixtures/cdc-veiculo-born-digital.pdf` | fpdf2 Python — CDC contrato veículo template ~2 pages text-extractable |
| scanned | `tests/fixtures/cdc-veiculo-scanned.pdf` | fpdf2 render → fitz convert to image → embed image em new PDF |

**Dependencies NEW Phase 4:**
- `fpdf2` (pip install fpdf2) — fixture generation
- PyMuPDF (fitz) — already installed

## Rollback Procedure

Se Phase 4 deploy falha:

```bash
# 1. Stop app container
sudo docker compose -p revisor-prod stop app

# 2. Restore Phase 3 image
sudo docker tag revisor-contratual:bak-pre-phase-4 revisor-contratual:prod

# 3. Recreate app com Phase 3 image
sudo docker compose -p revisor-prod up -d app
```

## Follow-ups (Phase 5)

| Finding | Phase 5 Action |
|---------|----------------|
| F-S7P3-MED-02 Marker cache ephemeral | Volume mount /home/revisor/.cache/datalab/models |
| F-S7P3-LOW-01 Smart timeout per PDF size/pages | Enhancement Sprint 7+ |
| F-S7P3-LOW-02 psutil empirical AC-5 + AC-10 | Sprint 7+ test enhancement |
| F-S7P3-LOW-04 E2E test test_f_prod_new_22_resolution | Add em Phase 5 polish |
| F-S7P3-LOW-05 Subprocess SIGKILL empirical | Stress test Phase 5 |
| F-S7P3-LOW-06 Tier-up swap test | Phase 5 stress test |

## ADR Index Update

```markdown
| [ADR-027](adr/adr-027-pymupdf-born-digital-fast-path.md) | PyMuPDF Born-Digital Fast Path — Dual-Path Pipeline Step 1 (Sprint 7 Phase 4) — RESOLVE F-S7P3-MED-01 pipeline E2E REAL 9/9 keys | ✅ Accepted | 2026-05-16 |
```

## References

- [Smith Verify Sprint 7 Phase 3 CONTAINED](../../qa/smith-verify-sprint-7-phase-3-2026-05-15.md)
- [ADR-026 Marker Subprocess Isolation](adr-026-marker-subprocess-isolation-parsing.md) (preserved fallback)
- [Sprint 7 Feasibility Study](../sprint-7-memory-optimization-feasibility-2026-05-15.md)
- ADR-023/024/025/028 (preserved)

---

*— Aria, Visionary. Phase 4 é o último passo antes do Cenário Y++ DoD final. Subprocess isolation cura crashes catastróficos (Phase 3). PyMuPDF fast path cura latência inaceitável para born-digital (80% casos). Juntos: pipeline E2E REAL 9/9 audit keys finalmente atingível. Neo, sua hora de construir o detector. 🏗️*
