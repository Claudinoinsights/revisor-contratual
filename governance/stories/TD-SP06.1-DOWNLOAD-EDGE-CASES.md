---
type: story
id: TD-SP06.1-DOWNLOAD-EDGE-CASES
title: "Download endpoint refinements — WWW-Authenticate + 404 distinct + size limit 413"
status: Ready for Review
priority: 3
sprint: "6.1 hotfix TD cleanup"
validated_by: "@po (Keymaker)"
validated_at: "2026-05-14"
validation_score: "10/10"
validation_verdict: "GO"
epic: "Sprint-6-Bloco-Gamma-Peca-Revisional-AI (post-launch hotfix)"
wave: "6.1.3 (paralelo a 6.1.1+6.1.2 — independent app.py file)"
owner: "@dev (Neo)"
estimated_effort: "1h"
severity_origem: "LOW consolidated (Smith F-γ-08 + F-γ-09 + F-γ-10)"
created: "2026-05-14"
created_by: "@sm (River)"
related_adrs:
  - "ADR-022 D7 SSE-OWNERSHIP-CHECK"
related_findings:
  - "Smith F-γ-08 LOW WWW-Authenticate (review-bloco-gamma-pos-execution-2026-05-14)"
  - "Smith F-γ-09 LOW 404 cascade distinct messages"
  - "Smith F-γ-10 LOW pdf size limit"
related_stories:
  - "TD-SP06-DOWNLOAD-ROUTES-01 (Bloco γ original — endpoint base)"
tags:
  - project/revisor-contratual
  - story
  - sprint-6-1
  - hotfix
  - download
  - edge-cases
  - lgpd
  - ready
---

# Story TD-SP06.1-DOWNLOAD-EDGE-CASES — Download endpoint refinements

## Story

**Como** advogado revisor consumindo API /download via SaaS clients (curl, Python requests, browser),
**Eu quero** error responses HTTP standard-compliant (WWW-Authenticate + 404 messages distintas + size limit 413),
**Para que** clientes possam tratar errors programaticamente sem inferir ambiguidades + segurança contra payloads maliciosos.

---

## Contexto

Smith F-γ-08 + F-γ-09 + F-γ-10 LOW (consolidated) identificaram 3 refinements para `/download/{job_id}`:

1. **F-γ-08:** 401 Response sem header `WWW-Authenticate` — clientes HTTP standard não saberão auto-prompt re-auth automatically
2. **F-γ-09:** 404 cascade collapse — 3 conditions (job ausente / PDF não gerado / file removido) em single status code; audit forense imprecisa
3. **F-γ-10:** `pdf_path.read_bytes()` sem size limit — DoS via PDF malicioso 1GB exhausting memória

Sprint 6.1 LOW consolidated em 1 story (refinements técnicos baixo risk).

---

## Acceptance Criteria

- **AC-01 (F-γ-08):** 401 Response em `/download/{job_id}` inclui header `WWW-Authenticate: Session`:
  ```python
  raise HTTPException(
      status_code=401,
      detail="Autenticação requerida",
      headers={"WWW-Authenticate": "Session"},
  )
  ```
- **AC-02 (F-γ-09):** 404 cascade distinct error codes + audit log entries:
  - Job não existe → 404 detail "job_not_found" + audit entry type "download_404_job_not_found"
  - PDF não gerado (peca_pdf_path is None) → 404 detail "pdf_not_generated_yet" + audit entry type "download_404_pdf_not_generated"
  - File removido (file não existe filesystem) → 404 detail "pdf_file_missing" + audit entry type "download_404_pdf_file_missing"
- **AC-03 (F-γ-10):** Size limit verificação ANTES de `read_bytes()`:
  ```python
  MAX_PDF_BYTES = 50 * 1024 * 1024  # 50MB sensible default SaaS
  if pdf_path.stat().st_size > MAX_PDF_BYTES:
      raise HTTPException(
          status_code=413,
          detail=f"PDF excede limite ({pdf_path.stat().st_size / 1024 / 1024:.1f}MB > 50MB)",
      )
  ```
- **AC-04:** 3 novos tests em `tests/unit/test_download_route.py`:
  - `test_401_includes_www_authenticate_header`
  - `test_404_distinct_detail_messages_per_condition`
  - `test_413_oversized_pdf_blocked`
- **AC-05:** Pytest baseline 478 PASS maintained — target 481+ com 3 novos tests
- **AC-06:** Existing tests (test_download_401_unauthenticated + test_download_404_*) backward-compat (status_code asserts continuam PASS, detail/headers podem ser refined)

---

## Tasks / Subtasks

- [ ] Task 1: F-γ-08 WWW-Authenticate header
  - [ ] 1.1 Adicionar `headers={"WWW-Authenticate": "Session"}` no HTTPException 401
- [ ] Task 2: F-γ-09 404 cascade distinct
  - [ ] 2.1 Constants para detail strings: `DOWNLOAD_404_JOB_NOT_FOUND` + `DOWNLOAD_404_PDF_NOT_GENERATED` + `DOWNLOAD_404_PDF_FILE_MISSING`
  - [ ] 2.2 Substituir detail strings genéricas pelas constants
  - [ ] 2.3 Audit log entries diferenciadas (event_type específico para cada caso)
- [ ] Task 3: F-γ-10 size limit 413
  - [ ] 3.1 Constant `MAX_PDF_BYTES = 50 * 1024 * 1024` em app.py (ou bloco_lgpd/limits.py se aplicável)
  - [ ] 3.2 Check `pdf_path.stat().st_size > MAX_PDF_BYTES` ANTES de `read_bytes()` (avoid memory exhaustion)
  - [ ] 3.3 HTTPException 413 com size details
- [ ] Task 4: Unit tests (3 novos)
  - [ ] 4.1 test_401_includes_www_authenticate_header
  - [ ] 4.2 test_404_distinct_detail_messages_per_condition (3 sub-cases)
  - [ ] 4.3 test_413_oversized_pdf_blocked (mock pdf_path stat retorna >50MB)
- [ ] Task 5: Update File List + Change Log
- [ ] Task 6: Self-critique

---

## Dev Notes (Technical Context)

**Aria fix_approach:**

```
F-γ-08: Response(status_code=401, headers={"WWW-Authenticate": "Session"})
F-γ-09: detail messages distintas + audit log entries diferenciadas (job_not_found vs pdf_not_generated vs pdf_file_missing)
F-γ-10: if pdf_path.stat().st_size > MAX_PDF_BYTES: raise HTTPException(413). MAX_PDF_BYTES = 50MB sensible default.
```

**Skeleton implementation:**

```python
# bloco_interface/web/app.py /download endpoint refined:
MAX_PDF_BYTES = 50 * 1024 * 1024  # 50MB sensible default SaaS
DOWNLOAD_404_JOB_NOT_FOUND = "job_not_found"
DOWNLOAD_404_PDF_NOT_GENERATED = "pdf_not_generated_yet"
DOWNLOAD_404_PDF_FILE_MISSING = "pdf_file_missing"

@app.get("/download/{job_id}")
async def download_peca(request: Request, job_id: str) -> Response:
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Autenticação requerida",
            headers={"WWW-Authenticate": "Session"},  # F-γ-08
        )

    job = JOBS.get(job_id)
    if not job:
        # F-γ-09: distinct audit + detail
        try:
            append_audit_entry("download_404_job_not_found", {"job_id": job_id, "user": user}, ...)
        except Exception:
            pass
        raise HTTPException(status_code=404, detail=DOWNLOAD_404_JOB_NOT_FOUND)

    # ... authz check (preserved)

    pdf_path_str = job.get("peca_pdf_path")
    if not pdf_path_str:
        try:
            append_audit_entry("download_404_pdf_not_generated", {"job_id": job_id, "user": user}, ...)
        except Exception:
            pass
        raise HTTPException(status_code=404, detail=DOWNLOAD_404_PDF_NOT_GENERATED)

    pdf_path = Path(pdf_path_str)
    if not pdf_path.exists():
        try:
            append_audit_entry("download_404_pdf_file_missing", {"job_id": job_id, "user": user, "expected_path": pdf_path_str}, ...)
        except Exception:
            pass
        raise HTTPException(status_code=404, detail=DOWNLOAD_404_PDF_FILE_MISSING)

    # F-γ-10: size limit ANTES de read_bytes
    pdf_size = pdf_path.stat().st_size
    if pdf_size > MAX_PDF_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"PDF excede limite ({pdf_size / 1024 / 1024:.1f}MB > 50MB)",
        )

    pdf_bytes = pdf_path.read_bytes()
    # ... audit-first pattern (F-γ-01 hotfix preserved)
    # ... return Response (preserved)
```

---

## Testing

```python
def test_401_includes_www_authenticate_header(unauth_client, populated_job):
    """F-γ-08 Sprint 6.1: 401 Response inclui WWW-Authenticate header."""
    response = unauth_client.get(f"/download/{populated_job}")
    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Session"


def test_404_distinct_detail_messages_per_condition(authed_client, fake_pdf_path):
    """F-γ-09 Sprint 6.1: 404 cascade distinct messages."""
    # Caso A: job não existe
    resp_a = authed_client.get("/download/nonexistent-job-123")
    assert resp_a.status_code == 404
    # detail validation via response.text (HTML error_handler middleware) OR response.json() depending env

    # Caso B: job existe mas pdf_path=None
    # Caso C: job existe + pdf_path set mas file removido
    # ... 3 sub-asserts


def test_413_oversized_pdf_blocked(authed_client, monkeypatch):
    """F-γ-10 Sprint 6.1: PDF >50MB blocked."""
    # Mock Path.stat() retorna size > 50MB
    # ... assert response.status_code == 413
```

---

## Dev Agent Record

**Agent Model Used:** (vazio)
**Debug Log References:** (vazio)
**Completion Notes List:** (vazio)
**File List:** (vazio)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-05-14 | @sm (River) | Draft Sprint 6.1 Wave 6.1.3 — Download endpoint refinements (Smith F-γ-08+09+10 LOW consolidated) |
| 2026-05-14 | @po (Keymaker) | Validation GO 10/10 — flip Draft → Ready |
| 2026-05-14 | @dev (Neo) | Implementação completa Wave 6.1.3 — F-γ-08 WWW-Authenticate header em 401 (HTTPException kwarg headers, middleware swallow TD-SP06.2 catalogado) + F-γ-09 constants DOWNLOAD_404_JOB_NOT_FOUND/PDF_NOT_GENERATED/PDF_FILE_MISSING distinct + F-γ-10 MAX_PDF_BYTES=50MB size limit antes read_bytes() + 4 novos unit tests — pytest 484 → 488 PASS ZERO regressão — flip Ready → Ready for Review. Files: bloco_interface/web/app.py + tests/unit/test_download_route.py |
