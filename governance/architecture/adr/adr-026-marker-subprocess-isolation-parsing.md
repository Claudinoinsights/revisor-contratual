---
type: adr
id: ADR-026
title: "Marker Subprocess Isolation Parsing — RESOLVE F-PROD-NEW-22 silent worker exit (Sprint 7 Phase 3)"
status: accepted
date: "2026-05-15"
domain: backend
adr_level: spec
spec_coverage:
  - "subprocess.exec parsing module isolated process"
  - "JSON IPC stdin/stdout protocol (não pickle)"
  - "Timeout watchdog 180s SIGTERM + 5s SIGKILL fallback"
  - "Audit chain integration error_type=ParsingSubprocessFailed"
  - "Memory deallocation post-Step-1 (parent worker liberta marker 3.3GB)"
  - "Terminology precision (image vs container instance vs restart vs recreate vs process)"
  - "Test fixtures (born-digital + scanned + corrupt PDFs)"
  - "10 ACs Phase 3 verification"
decision_makers:
  - "@architect (Aria)"
  - "@smith (Smith — Sprint 6.x F-PROD-NEW-22 root cause investigation + Sprint 7 Phase 1+2 CONTAINED reviews)"
  - "@dev (Neo — subprocess implementation Sprint 7 Phase 3)"
  - "Eric (owner — directive Cenário Y++ refinado AskUserQuestion 2026-05-15)"
supersedes: null
superseded_by: null
related_adrs:
  - "ADR-023 Sequential LLM Inference (preserved — F-PROD-NEW-18 capacity)"
  - "ADR-024 Redator Tier Strategy (preserved — tier=lean qwen2.5:3b para 3 personas)"
  - "ADR-025 Redator Cascade Fallback Strategy (preserved — graceful degradation)"
  - "ADR-028 Ollama Single-Container Consolidation (Phase 2 deployed)"
related_findings:
  - "F-PROD-NEW-22 Smith Sprint 6.x final D-SMITH-S06-040 (silent worker exit pós OCR completion, 3x reproducible)"
  - "Smith Phase 1 D-SMITH-S07-001 (12 findings, 3 MEDIUMs absorbed em ADR-028)"
  - "Smith Phase 2 D-SMITH-S07-002 (12 findings, 1 MEDIUM F-S7P2-MED-01 absorbed AQUI em terminology precision)"
related_documents:
  - "governance/architecture/sprint-7-memory-optimization-feasibility-2026-05-15.md (Aria study Cenário Y++)"
  - "governance/qa/smith-verify-final-sprint-6x-2026-05-15.md (Smith F-PROD-NEW-22 forensic Sprint 6.x final)"
  - "governance/qa/smith-verify-sprint-7-phase-2-2026-05-15.md (Smith Phase 2 12 findings)"
tags:
  - project/revisor-contratual
  - adr
  - sprint-7
  - phase-3
  - subprocess-isolation
  - f-prod-new-22-fix
  - cenario-y-plus-plus
  - terminology-precision
---

# ADR-026 — Marker Subprocess Isolation Parsing (Sprint 7 Phase 3)

## Context

### F-PROD-NEW-22 — Silent Worker Exit Empirical Pattern

Smith Sprint 6.x final D-SMITH-S06-040 documentou empirically (3x reproducible):

```text
OCR on page.number=11/12.
                              ← worker silently exits aqui (NO traceback, NO SIGKILL)
INFO:     Started server process [1]   ← container restarted
```

**Telemetry forensic:**

| Métrica | Valor |
|---------|-------|
| ExitCode | 0 (clean) |
| OOMKilled | false |
| cgroup memory.events oom_kill | 0 |
| Memory peak | 585.9 MiB / 6 GiB (12%) |
| Healthcheck FailingStreak | 0 |
| dmesg OOM events | 0 |
| Audit chain | UNCHANGED (pipeline crashed antes Step 2 audit write) |

**Não é OOM. Não é healthcheck. Não é signal kill.** Worker exits CLEANLY após `parse_contract()` retorna em `await asyncio.to_thread(...)`.

### Root Cause Hypotheses (Smith forensic)

| H | Probabilidade | Mecanismo |
|---|--------------|-----------|
| **H1** marker/surya internal `os._exit(0)` | **HIGH** | Library chama exit() abrupto após parsing — mata processo Python inteiro |
| **H2** torch.multiprocessing fork corrupting asyncio | MEDIUM | torch usa `fork()` default Linux — fork dentro asyncio loop pode corromper estado |
| **H3** PyMuPDF/fitz C extension SIGABRT silent | MEDIUM | C extensions podem abort processo sem traceback Python |

### Estado Atual Pipeline (problematic)

```python
# bloco_workflow/pipeline.py linha 225-238 (Step 1)
try:
    parsed: ParsedContract = await asyncio.to_thread(
        parse_contract,
        pdf_path,
        pdf_bytes=pdf_bytes,
        uf_override=uf_override,
        data_override=data_override,
        pymupdf_fn=pymupdf_fn,
        marker_fn=marker_fn,
    )
except Exception as exc:
    # Captura SOMENTE Python exceptions
    # NÃO captura os._exit() OR SIGABRT (mata processo inteiro)
    audit_payload["error_type"] = type(exc).__name__
    ...
```

**Problema:** `asyncio.to_thread` executa parse_contract em ThreadPoolExecutor — se library chama `os._exit(0)` OU C extension SIGABRT, mata processo Python inteiro (não apenas a thread). Try/except inútil contra abort process-level.

### Por que Phase 3 agora

- Phase 1 (Ollama ENV vars) ✅ Smith CONTAINED — config-only, sem impact F-PROD-NEW-22
- Phase 2 (container consolidation ADR-028) ✅ Smith CONTAINED — infra change, F-PROD-NEW-22 ainda persists (Smith F-S7P2-LOW-04)
- **Phase 3 = código produto change para isolar marker em subprocess descartável**

Pipeline E2E REAL com 9/9 audit keys = Cenário Y++ DoD final criterion. Phase 3 desbloqueia.

## Decision

**Refactor pipeline.py Step 1 para usar `asyncio.subprocess.exec()` em vez de `asyncio.to_thread()`.** Marker library + PyMuPDF + parse_contract executam em **subprocess descartável** isolado. Subprocess crash NÃO mata parent worker.

Inter-process protocol: **JSON via stdin/stdout** (simplicidade + debuggability + cross-language futuro).

## Rationale

### Por que subprocess isolation

1. **Isolamento process-level** — `os._exit()` OR SIGABRT no subprocess NÃO afeta parent worker
2. **Audit chain protection** — parent worker captura subprocess exit code + escreve audit entry mesmo em crash
3. **Memory deallocation** — subprocess exit libera marker 3.3 GB para OS (parent worker mantém ~600 MB baseline)
4. **Independent runtime** — subprocess pode usar versões diferentes Python/libs futuro
5. **Testability empirical** — subprocess CLI standalone testable

### Por que NÃO try/except mais agressivo

`os._exit(0)` chama imediatamente kernel `_exit()` syscall — bypassa Python finally + exception handling. Try/except dentro do mesmo processo NÃO captura. Subprocess é a ÚNICA solução process-level.

### Por que NÃO thread isolation

Python GIL não isola threads em terms of process death. Se thread chama `os._exit()`, processo inteiro morre. Threads compartilham memory address space.

### Por que NÃO existing wraps

`signal.signal(SIGABRT, handler)` pode interceptar SIGABRT de C extensions, mas `os._exit()` é syscall direto sem signal — handler não dispara.

### Por que JSON (não pickle)

- **Security:** pickle deserialize é vulnerable a code execution (CVE-history)
- **Debuggability:** JSON human-readable em logs/dumps
- **Cross-language:** futuro pode subprocess em Rust/Go se quiser
- **Pydantic compat:** ParsedContract `.model_dump_json()` + `.model_validate_json()` nativos

### Por que NÃO shared memory

- Overhead setup multiprocessing.shared_memory > JSON serialization para single PDF
- Complexity (locking, lifecycle) > benefit MVP B2B 1-3 users
- Single PDF parsing é I/O-bound (PDF read + OCR) — JSON serialize trivial

## Alternatives Considered

### Alternative A: Try/except mais agressivo + signal handlers

**Pros:** Sem refactor architectural, mesmo processo.
**Cons:** `os._exit()` bypassa signal handlers + Python exception handling. NÃO resolve F-PROD-NEW-22 root cause.
**Verdict:** Rejected — não funcional contra hypothesis H1.

### Alternative B: Thread isolation com daemon thread

**Pros:** Lower overhead que subprocess.
**Cons:** Python GIL + shared address space — `os._exit()` mata processo inteiro independente de thread.
**Verdict:** Rejected — não isola process-level.

### Alternative C: Replace marker com PyMuPDF only

**Pros:** Eliminate marker library 3.3 GB cache.
**Cons:** PyMuPDF (fitz) também é C extension — H3 hypothesis SIGABRT applies. CDC scanned PDFs (raros mas possíveis) requerem OCR which PyMuPDF não faz.
**Verdict:** PARTIAL adoption — Phase 4 (PyMuPDF born-digital fast path ADR-027) já planeja para 80% casos. Mas Phase 3 subprocess isolation é fundação que cobre AMBOS PyMuPDF + Marker.

### Alternative D: Subprocess isolation (CHOSEN — this ADR)

**Pros:** Process-level isolation, F-PROD-NEW-22 RESOLVED, memory deallocation, audit recovery, future-proof.
**Cons:** Subprocess overhead ~200ms + JSON serialize ~50ms = +250ms per parse vs in-process. 3-4 dias dev effort.
**Verdict:** **ACCEPTED** — Cenário Y++ component B + cura F-PROD-NEW-22.

### Alternative E: Process pool (multiprocessing.Pool)

**Pros:** Reuse workers (avoid fork overhead).
**Cons:** Pool workers are PERSISTENT — se um chama `os._exit()`, esse worker morre mas pool tenta replace. Adds complexity e race conditions. SaaS B2B MVP 1-3 users não justifica pool.
**Verdict:** Rejected — over-engineering MVP. Pode revisitar Sprint 8+ se concurrent users escalar.

## Consequences

### Positive

| Benefit | Impact |
|---------|--------|
| F-PROD-NEW-22 RESOLVED | Pipeline E2E REAL com 9/9 audit keys executável |
| Memory deallocation post-Step-1 | Parent worker libera 3.3 GB pós subprocess exit |
| Audit chain robust | Subprocess crash → audit entry com error_type=ParsingSubprocessFailed |
| Testability empirical | `python -m bloco_engine.parsing.subprocess_runner test.pdf` standalone |
| Future-proof | Subprocess pode usar Python diferente OR Rust/Go futuro |
| Phase 4 PyMuPDF integration | Subprocess pattern reutilizável born-digital fast path |
| Smith F-S7P2-MED-01 absorbed | Terminology precision section formal record |

### Negative

| Risk | Mitigation |
|------|-----------|
| Subprocess overhead +250ms per parse | Born-digital path Phase 4 (~50ms PyMuPDF) compensa para 80% casos |
| JSON serialization size (large markdown) | Markdown ~5KB típico — serialize trivial; gzip optional Phase 5+ se necessário |
| Subprocess startup time (~200ms python -m import) | Acceptable para single PDF parsing (não loop hot path) |
| pipeline.py refactor risk | Neo MEDIUM risk implementation; Smith MANDATORY verify F-PROD-NEW-22 reproduction; ADR-025 graceful degradation fallback |
| Audit error taxonomy futura expansion | Single error_type=ParsingSubprocessFailed com `detail` field — granular taxonomy Phase 5+ se necessário |

### Neutral

| Aspecto | Detalhe |
|---------|---------|
| ADR-023 sequential LLM preserved | run_personas_sequencial() unchanged |
| ADR-024 tier strategy preserved | TIER_TO_MODEL_* + MODEL_ECONOMISTA preserved |
| ADR-025 Redator cascade preserved | _build_degraded_synthetic_response unchanged |
| ADR-028 ollama-shared preserved | OLLAMA_HOST_*=ollama-shared:11434 unchanged |

## Terminology Precision (Smith F-S7P2-MED-01 Absorption)

Esta section absorve formalmente Smith Sprint 7 Phase 2 finding F-S7P2-MED-01 (Operator pattern recorrente terminology imprecisa "preserved"):

### Container & Image Lifecycle Terms

| Termo | Significado |
|-------|-------------|
| **image preserved** | Docker image SHA256 unchanged (`docker inspect --format '{{.Image}}'` retorna mesmo digest pré e pós deploy) |
| **container instance preserved** | Same Docker container ID + RestartCount unchanged (`docker inspect --format '{{.Id}} {{.RestartCount}}'` retorna mesmo valor) |
| **container restarted** | Same instance, RestartCount incremented (e.g., 3→4 indicates 1 restart) |
| **container recreated** | NEW instance, RestartCount reset to 0, StartedAt is recent (e.g., docker compose up -d after env vars change) |
| **image rebuilt** | New Docker image SHA256 (e.g., docker build após code change) |

### Process Execution Model Terms

| Termo | Significado |
|-------|-------------|
| **parent worker process** | uvicorn worker Python process (PID 1 inside container) |
| **subprocess** | Child process spawned via `asyncio.subprocess.exec()` (independent PID, JSON IPC stdin/stdout) |
| **subprocess crash** | Subprocess exits non-zero OR is SIGKILLed (parent worker continues) |
| **process recreated** | NEW Python process (parent worker recreated by uvicorn OR Docker compose) |

### Phase 3 ACs Terminology Application

Cada Phase 3 AC abaixo usa terminology PRECISA. Operator e Smith devem verify usando exatamente esses termos.

## Phase 3 Spec — bloco_engine.parsing.subprocess_runner Module

### CLI Interface

```python
# bloco_engine/parsing/subprocess_runner.py
"""Subprocess CLI runner for parse_contract — F-PROD-NEW-22 isolation fix (ADR-026).

Usage:
    python -m bloco_engine.parsing.subprocess_runner <pdf_path> <metadata_json>

Reads metadata JSON from <metadata_json> file (uf_override, data_override, etc).
Returns ParsedContract via JSON stdout.
Exits 0 on success, 1+ on error (error_type + error_msg in stderr).
"""

import sys
import json
import os
from pathlib import Path
from datetime import date
from bloco_engine.parsing.orchestrator import parse_contract

def main():
    if len(sys.argv) != 3:
        print("ERROR: usage: python -m bloco_engine.parsing.subprocess_runner <pdf_path> <metadata_json>",
              file=sys.stderr)
        sys.exit(2)

    pdf_path = Path(sys.argv[1])
    metadata_json_path = Path(sys.argv[2])

    if not pdf_path.is_file():
        print(json.dumps({"error_type": "PDFNotFound", "error_msg": str(pdf_path)}),
              file=sys.stderr)
        sys.exit(1)

    try:
        with open(metadata_json_path) as f:
            metadata = json.load(f)
        uf_override = metadata.get("uf_override")
        data_str = metadata.get("data_override")
        data_override = date.fromisoformat(data_str) if data_str else None

        parsed = parse_contract(
            pdf_path,
            pdf_bytes=pdf_path.read_bytes(),
            uf_override=uf_override,
            data_override=data_override,
        )

        # Serialize ParsedContract via Pydantic JSON
        print(parsed.model_dump_json())
        sys.exit(0)
    except Exception as exc:
        # Catch Python exceptions (NÃO captura os._exit ou SIGABRT que matam processo)
        print(json.dumps({
            "error_type": type(exc).__name__,
            "error_msg": str(exc)
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Inter-Process Protocol

| Direction | Channel | Format | Example |
|-----------|---------|--------|---------|
| Parent → Subprocess | argv | path strings | `python -m ... /tmp/contract.pdf /tmp/metadata.json` |
| Parent → Subprocess | metadata.json file | JSON | `{"uf_override": "SP", "data_override": "2025-12-01"}` |
| Subprocess → Parent | stdout | Pydantic JSON | `{"metadata": {...}, "markdown": "...", "pages_count": 12, ...}` |
| Subprocess → Parent | stderr | JSON error | `{"error_type": "ParserOCRRequired", "error_msg": "Marker library failed"}` |
| Subprocess → Parent | exit code | int | 0=success, 1=error, 2=usage error |

## Phase 3 Spec — pipeline.py Refactor

### Atual (Problematic)

```python
# bloco_workflow/pipeline.py linha 225-238 (Step 1)
try:
    parsed: ParsedContract = await asyncio.to_thread(
        parse_contract,
        pdf_path,
        pdf_bytes=pdf_bytes,
        uf_override=uf_override,
        data_override=data_override,
        pymupdf_fn=pymupdf_fn,
        marker_fn=marker_fn,
    )
```

### Proposto (Subprocess isolation)

```python
# bloco_workflow/pipeline.py linha 225-280 (Step 1 refactored ADR-026)
import json
import tempfile
import asyncio
from pathlib import Path

# Step 1 — parsing PDF via subprocess isolation (ADR-026 — F-PROD-NEW-22 fix)
metadata_dict = {
    "uf_override": uf_override,
    "data_override": data_override.isoformat() if data_override else None,
}

# Write metadata JSON file temp
with tempfile.NamedTemporaryFile(
    mode="w", suffix=".json", delete=False
) as metadata_file:
    json.dump(metadata_dict, metadata_file)
    metadata_path = metadata_file.name

try:
    # Spawn subprocess — isolated from parent worker
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "bloco_engine.parsing.subprocess_runner",
        str(pdf_path), metadata_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Wait with timeout (180s + 5s SIGKILL fallback)
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=180.0
        )
    except asyncio.TimeoutError:
        # SIGTERM grace period
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            # SIGKILL fallback
            proc.kill()
            await proc.wait()
        raise ParsingSubprocessTimeoutError(
            f"parse_contract subprocess timeout 180s for {pdf_path}"
        )

    if proc.returncode != 0:
        # Subprocess failed (could be os._exit OR SIGABRT OR Python exception)
        try:
            error_data = json.loads(stderr_bytes.decode())
            error_type = error_data.get("error_type", "ParsingSubprocessFailed")
            error_msg = error_data.get("error_msg", stderr_bytes.decode()[:500])
        except json.JSONDecodeError:
            error_type = "ParsingSubprocessFailed"
            error_msg = (
                f"Subprocess exited code={proc.returncode} "
                f"stderr={stderr_bytes.decode()[:500]}"
            )
        raise ParsingSubprocessFailedError(error_type=error_type, error_msg=error_msg)

    # Parse stdout JSON → ParsedContract
    parsed = ParsedContract.model_validate_json(stdout_bytes.decode())

finally:
    # Cleanup metadata temp file
    Path(metadata_path).unlink(missing_ok=True)
```

## Phase 3 Acceptance Criteria (10 ACs com Terminology Precision)

| AC | Description | Verification command |
|----|-------------|---------------------|
| **AC-1** | subprocess_runner CLI standalone executes (returns valid JSON ParsedContract) | `python -m bloco_engine.parsing.subprocess_runner tests/fixtures/cdc-veiculo-born-digital.pdf /tmp/metadata.json` retorna JSON válido + exit 0 |
| **AC-2** | pipeline.py uses subprocess (NOT asyncio.to_thread) | `grep -n "asyncio.subprocess" bloco_workflow/pipeline.py` retorna match em Step 1 + `grep -n "to_thread.*parse_contract" bloco_workflow/pipeline.py` retorna ZERO matches |
| **AC-3** | F-PROD-NEW-22 RESOLVED — pipeline COMPLETES Steps 2-9 mesmo se marker subprocess crash | Force subprocess crash via fixture (corrupt PDF) → audit chain registers `pipeline_revisar_contrato` event_type com `error_type=ParsingSubprocessFailed` AND parent worker process NOT recreated |
| **AC-4** | Audit chain registers error_type=ParsingSubprocessFailed em scenarios crash | `tail audit.jsonl` mostra entry com `payload.error_type=ParsingSubprocessFailed` |
| **AC-5** | App container parent process memory pós-Step-1 < 700 MB (subprocess deallocated marker 3.3 GB) | `docker exec app ps -o pid,rss,cmd | grep uvicorn` retorna RSS < 716800 KiB pós Step 1 |
| **AC-6** | Pipeline E2E REAL submission completes 9/9 audit keys com PDF born-digital test fixture | Submit `tests/fixtures/cdc-veiculo-born-digital.pdf` via /revisar API → audit entry payload contém keys `[parsing, calculo, bacen, vault, personas, juiz, peca_generated, peca_format, redator_tier_consumed]` (≥9) + `status="success"` |
| **AC-7** | **Container instance status DECLARED EXPLICITLY** (Smith F-S7P2-MED-01) — Operator deve declarar qual tipo de mudança Phase 3 deploy causou | Operator deploy report inclui section "Container Lifecycle Phase 3 Deploy" com terminology precisa: image rebuilt SIM/NÃO + container recreated SIM/NÃO + RestartCount pré/pós + StartedAt pré/pós |
| **AC-8** | RestartCount tracking entre Phase 2 baseline (D-SMITH-S07-002 = 0) e Phase 3 pós-deploy | Smith pre-Phase-3: `docker inspect app --format '{{.RestartCount}}'` registers baseline. Smith post-Phase-3: register actual + delta. Expected delta = 0 (RestartCount reset por recreate é OK desde que image rebuild justifica) |
| **AC-9** | Subprocess timeout funcional (180s SIGTERM verified empirically + 5s SIGKILL fallback) | Force subprocess hang via fixture (loop infinito) → parent worker terminates subprocess em 185s ± 5s + audit entry `error_type=ParsingSubprocessTimeoutError` |
| **AC-10** | Subprocess MEMORY deallocation verified empirically | Pre-subprocess: parent process RSS X MB. During subprocess: parent RSS X MB (subprocess separate PID). Post-subprocess exit: parent RSS X MB (sem leak). Compare via `psutil.Process(pid).memory_info().rss` |

## Phase 3 Operator Deploy Script

### Pre-flight (Operator)

```bash
# 1. Backup current production image (rollback safety)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo docker tag revisor-contratual:prod revisor-contratual:bak-pre-phase-3"

# 2. Backup docker-compose.prod.yml (preservado de Phase 2 — apenas symlink)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo cp /opt/revisor-contratual/docker-compose.prod.yml \
   /opt/revisor-contratual/docker-compose.prod.yml.bak-pre-phase-3"
```

### Build & Deploy (Operator + Neo collaboration)

```bash
# 3. Neo committed code changes em main (subprocess_runner.py + pipeline.py refactor + tests)
# Operator pull no VPS source tree (similar Sprint 6.x D-OPS-S06-037 pattern)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "cd /opt/revisor-contratual && sudo git pull origin main"
# OR scp specific .py files se /opt/revisor-contratual NÃO é git tree (Sprint 6.x discovery)

# 4. Image rebuild com novo subprocess_runner module
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "cd /opt/revisor-contratual && sudo docker build -t revisor-contratual:prod ."

# 5. Container RECREATE necessário (image rebuild = new instance)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "cd /opt/revisor-contratual && sudo docker compose -p revisor-prod up -d app"
```

### Smoke Verification (Operator + Smith collaboration)

```bash
# 6. Verify subprocess_runner CLI standalone (AC-1)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo docker exec revisor-prod-app python -m bloco_engine.parsing.subprocess_runner \
   /tmp/contrato_veiculo.pdf /tmp/metadata-test.json"

# 7. Submit real PDF via /revisar API (AC-3, AC-6)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo docker exec revisor-prod-app sh -c 'curl -X POST http://localhost:8501/revisar \
    -H \"Accept: application/json\" \
    -F \"pdf=@/tmp/contrato_veiculo.pdf\" \
    -F \"uf=SP\" -F \"data=2025-12-01\" -F \"tier=lean\" \
    -F \"modalidade_override=CDC_VEICULOS_PF\"'"

# 8. Tail audit chain (AC-4, AC-6)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo docker exec revisor-prod-app tail -1 \
   /home/revisor/.local/share/revisor-contratual/audit.jsonl | python -m json.tool"

# 9. Verify memory deallocation (AC-5, AC-10)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo docker stats --no-stream revisor-prod-app"

# 10. Verify container lifecycle (AC-7, AC-8)
ssh -i ~/.ssh/claudino-insights eric@91.108.126.149 \
  "sudo docker inspect revisor-prod-app --format \
   'Image={{.Image}} StartedAt={{.State.StartedAt}} RestartCount={{.RestartCount}}'"
```

## Tests Strategy (Neo Deliverable)

### Unit Tests

```python
# tests/unit/test_parsing_subprocess_runner.py
def test_subprocess_runner_born_digital_success(tmp_path):
    """AC-1: subprocess_runner returns valid JSON ParsedContract"""
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text('{"uf_override": "SP", "data_override": "2025-12-01"}')

    result = subprocess.run(
        [sys.executable, "-m", "bloco_engine.parsing.subprocess_runner",
         "tests/fixtures/cdc-veiculo-born-digital.pdf", str(metadata_path)],
        capture_output=True, text=True, timeout=60
    )

    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert "metadata" in parsed
    assert "markdown" in parsed
    assert "pages_count" in parsed

def test_subprocess_runner_corrupt_pdf_error(tmp_path):
    """AC-4: subprocess_runner returns error JSON on corrupt PDF"""
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text('{"uf_override": "SP", "data_override": "2025-12-01"}')

    result = subprocess.run(
        [sys.executable, "-m", "bloco_engine.parsing.subprocess_runner",
         "tests/fixtures/corrupt.pdf", str(metadata_path)],
        capture_output=True, text=True, timeout=60
    )

    assert result.returncode != 0
    error = json.loads(result.stderr)
    assert "error_type" in error
```

### Integration Tests

```python
# tests/integration/test_pipeline_subprocess.py
@pytest.mark.asyncio
async def test_pipeline_uses_subprocess_not_to_thread(monkeypatch):
    """AC-2: pipeline.py uses asyncio.subprocess (NOT asyncio.to_thread)"""
    # Verify via mock that asyncio.create_subprocess_exec is called
    # NOT asyncio.to_thread
    ...

@pytest.mark.asyncio
async def test_pipeline_audit_on_subprocess_crash():
    """AC-3, AC-4: audit chain registers ParsingSubprocessFailed if subprocess crashes"""
    # Force subprocess crash via fixture corrupt PDF
    # Verify audit.jsonl entry com error_type=ParsingSubprocessFailed
    ...
```

### E2E Tests

```python
# tests/e2e/test_f_prod_new_22_resolution.py
@pytest.mark.e2e
async def test_pipeline_completes_steps_2_to_9_after_subprocess(http_client):
    """AC-6: Pipeline completes 9/9 audit keys with born-digital PDF fixture"""
    pdf_path = "tests/fixtures/cdc-veiculo-born-digital.pdf"
    response = await http_client.post("/revisar", files={"pdf": open(pdf_path, "rb")},
                                       data={"uf": "SP", "data": "2025-12-01",
                                             "tier": "lean",
                                             "modalidade_override": "CDC_VEICULOS_PF"},
                                       headers={"Accept": "application/json"})
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Wait for SSE stream completion
    # Tail audit chain
    # Assert ≥9 keys in payload + status="success"
```

## Test Fixtures Strategy

| Fixture | Path | Purpose | Generation |
|---------|------|---------|-----------|
| born-digital | `tests/fixtures/cdc-veiculo-born-digital.pdf` | Happy path PyMuPDF (no marker) | Generate via `fpdf2` Python (CDC veículo template) |
| scanned | `tests/fixtures/cdc-veiculo-scanned.pdf` | Marker OCR path | Render born-digital → image → embed em new PDF |
| corrupt | `tests/fixtures/corrupt.pdf` | Subprocess error test | Truncated bytes (first 100 bytes only) |
| timeout | `tests/fixtures/timeout-test.pdf` | Subprocess timeout test | Large PDF (50+ pages OR specific marker stress pattern) |

Neo deve criar fixtures durante implementation (incluso em 2-3 dias estimate).

## Rollback Procedure

Se Phase 3 deploy falha:

```bash
# 1. Stop app container
sudo docker compose -p revisor-prod stop app

# 2. Restore previous image
sudo docker tag revisor-contratual:bak-pre-phase-3 revisor-contratual:prod

# 3. Restore docker-compose.prod.yml backup (se modificado)
sudo cp /opt/revisor-contratual/docker-compose.prod.yml.bak-pre-phase-3 \
       /opt/revisor-contratual/docker-compose.prod.yml

# 4. Up app com image restaurada
sudo docker compose -p revisor-prod up -d app
```

## Follow-ups (Phase 4-5+)

| Finding | Phase | Action |
|---------|-------|--------|
| Smith F-S7P2-MED-03 (queue UX gap) | Phase 4/5 | ADR separate (SSE timeout + queue UX feedback) |
| Phase 4 PyMuPDF born-digital fast path | Phase 4 | ADR-027 — pode reutilizar subprocess pattern OR direct PyMuPDF (decidir Phase 4 spec) |
| Smith F-S7P1-LOW-04 (KV q8_0 quality untested) | Phase 5 | Compare q8_0 vs f16 prompt jurídico Brasileiro |
| Smith F-S7P1-LOW-05 (tier-up swap latency edge case) | Sprint 7+ | UX feedback durante model swap |
| Smith F-S7P2-LOW-01 (volumes antigos cleanup) | Phase 5 polish | docker volume rm ollama-models-{advogado,economista} |
| Smith F-S7P2-LOW-03 (compose external warning) | Phase 5 polish | Mark `external: true` em compose volumes section |
| Subprocess error taxonomy granular | Sprint 7+ | Multiple error_type (Timeout, OSExit, etc) se necessário |

## ADR Index Update

Adicionar em [`governance/architecture/ADR-INDEX.md`](../ADR-INDEX.md) (Sprint 7 section nova):

```markdown
| [ADR-026](adr/adr-026-marker-subprocess-isolation-parsing.md) | Marker Subprocess Isolation Parsing — RESOLVE F-PROD-NEW-22 + terminology precision (Sprint 7 Phase 3) | ✅ Accepted | 2026-05-15 |
```

## References

- [Sprint 7 Memory Optimization Feasibility Study](../sprint-7-memory-optimization-feasibility-2026-05-15.md) (Aria D-ARIA-S07-001 + Phase 1 patches D-ARIA-S07-002)
- [ADR-028 Ollama Single-Container Consolidation](adr-028-ollama-single-container-consolidation.md) (Phase 2 deployed)
- [Smith Verify Sprint 6.x Final F-PROD-NEW-22 forensic](../../qa/smith-verify-final-sprint-6x-2026-05-15.md)
- [Smith Verify Sprint 7 Phase 1 CONTAINED](../../qa/smith-verify-sprint-7-phase-1-2026-05-15.md)
- [Smith Verify Sprint 7 Phase 2 CONTAINED](../../qa/smith-verify-sprint-7-phase-2-2026-05-15.md)
- D-OPS-S07-001 + D-OPS-S07-002 (Operator Phases 1+2 deployment)

---

*— Aria, Visionary. Subprocess isolation é o ato arquitetônico mais honesto do Sprint 7: reconhece que C extensions podem matar processos sem aviso e isola o risco em territory descartável. Terminology precision absorbida formalmente — Smith força clareza onde Operator usava ambiguidade. F-PROD-NEW-22 será cura definitiva quando Neo implementar. Pipeline E2E REAL com 9/9 audit keys está a 3-4 dias de distância. 🏗️*
