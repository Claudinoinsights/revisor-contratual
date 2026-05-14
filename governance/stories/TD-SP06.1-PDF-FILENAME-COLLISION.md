---
type: story
id: TD-SP06.1-PDF-FILENAME-COLLISION
title: "pdf_filename usa job_id (multi-tenancy SaaS fix)"
status: Ready for Review
priority: 1
sprint: "6.1 hotfix TD cleanup"
validated_by: "@po (Keymaker)"
validated_at: "2026-05-14"
validation_score: "10/10"
validation_verdict: "GO"
epic: "Sprint-6-Bloco-Gamma-Peca-Revisional-AI (post-launch hotfix)"
wave: "6.1.1 (foundation paralelo)"
owner: "@dev (Neo)"
estimated_effort: "30min"
severity_origem: "MEDIUM (Smith F-γ-07 — collision risk multi-tenancy)"
created: "2026-05-14"
created_by: "@sm (River)"
related_adrs:
  - "ADR-022 D3 Pipeline Integration"
related_findings:
  - "Smith F-γ-07 MEDIUM (review-bloco-gamma-pos-execution-2026-05-14)"
related_stories:
  - "TD-SP06-WEASYPRINT-PECA-01 (Bloco γ original — pdf_filename pattern original)"
unblocks:
  - "Multi-tenancy SaaS — 2 users com mesmo PDF input recebem outputs distintos"
tags:
  - project/revisor-contratual
  - story
  - sprint-6-1
  - hotfix
  - multi-tenancy
  - ready
---

# Story TD-SP06.1-PDF-FILENAME-COLLISION — pdf_filename job_id-based

## Story

**Como** advogado revisor em escritório SaaS multi-tenant,
**Eu quero** que pdf_filename seja único por job (não por contract_hash),
**Para que** 2 advogados que sobem o mesmo PDF contratual recebam outputs distintos sem overwrite ou ownership ambiguity.

---

## Contexto

Smith F-γ-07 MEDIUM identificou que `pipeline.py:396` usa `pdf_filename = f'{contract_hash[:16]}.pdf'`. contract_hash é SHA256 determinístico do PDF content → mesmo input por users distintos produz mesmo output_path → race condition + ownership ambiguity (JOBS[job_id_A] e JOBS[job_id_B] apontam ao mesmo `peca_pdf_path` mas com owners diferentes).

Multi-tenancy SaaS rompido. Sprint 6.1 fix: job_id (UUID único por execução) em vez de contract_hash.

---

## Acceptance Criteria

- **AC-01:** `bloco_workflow/pipeline.py` linha 396 atualizada — `pdf_filename = f"{job_id[:8]}-{parsed.metadata.contract_hash[:8]}.pdf"` (preserva contract_hash audit trail + job_id uniqueness)
  - Alternativa simples: `pdf_filename = f"{job_id}.pdf"` (Neo decide qual approach — Aria handoff sugeriu ambas)
- **AC-02:** Pipeline assinatura `revisar_contrato` recebe `job_id: str | None = None` como kwarg opt-in (retrocompat — caller app.py passa, tests legacy podem omitir)
- **AC-03:** Quando `job_id is None` → fallback para current behavior (`pdf_filename = f"{contract_hash[:16]}.pdf"`)
- **AC-04:** Audit field `peca_pdf_filename` adicionado em audit_payload Step 8 (rastreabilidade)
- **AC-05:** Novo test `test_concurrent_jobs_same_pdf_no_collision`:
  - 2 chamadas `revisar_contrato` com mesmo PDF input + job_ids distintos
  - Verifica `peca_pdf_path` outputs diferentes
- **AC-06:** Pytest baseline 478 PASS maintained (target 479+ se novo test)
- **AC-07:** app.py revisar_stream passa job_id como kwarg ao revisar_contrato

---

## Tasks / Subtasks

- [ ] Task 1: Update pipeline.py
  - [ ] 1.1 Adicionar `job_id: str | None = None` na signature `revisar_contrato`
  - [ ] 1.2 Substituir linha 396 `pdf_filename` por job_id-based (Neo escolhe approach)
  - [ ] 1.3 Adicionar audit field `peca_pdf_filename`
- [ ] Task 2: Update app.py
  - [ ] 2.1 revisar_stream passa `job_id=job_id` ao revisar_contrato call (linha ~909)
- [ ] Task 3: Unit test (`tests/unit/test_pipeline_pdf_filename.py` NEW OR test_weasyprint_render.py extend)
  - [ ] 3.1 test_concurrent_jobs_same_pdf_no_collision com mock pdf_renderer_fn
- [ ] Task 4: Update File List + Change Log

---

## Dev Notes (Technical Context)

**Aria fix_approach:** `pdf_filename = f'{job_id[:8]}-{contract_hash[:8]}.pdf'` preserva ambos — job_id uniqueness + contract_hash audit trail.

**Implementation skeleton:**

```python
# bloco_workflow/pipeline.py linha 396 (revisado):
if peca_output_dir is None:
    peca_output_dir = audit_path.parent / "pecas"

if job_id is not None:
    pdf_filename = f"{job_id[:8]}-{parsed.metadata.contract_hash[:8]}.pdf"
else:
    pdf_filename = f"{parsed.metadata.contract_hash[:16]}.pdf"  # legacy fallback

pdf_output_path = peca_output_dir / pdf_filename
audit_payload["peca_pdf_filename"] = pdf_filename
```

**app.py call site (linha ~909):**

```python
pipeline_task = asyncio.create_task(
    asyncio.wait_for(
        revisar_contrato(
            Path(job["pdf_path"]),
            audit_path=DEFAULT_AUDIT_PATH,
            vault_conn=conn,
            # ... outros kwargs
            job_id=job_id,  # NEW Sprint 6.1
            result_capture=pipeline_capture,
        ),
        timeout=1800,
    )
)
```

---

## Testing

```python
async def test_concurrent_jobs_same_pdf_no_collision(tmp_path):
    """F-γ-07 Sprint 6.1: 2 users mesmo PDF → outputs distintos."""
    captured_paths = []

    def mock_renderer(template, ctx, output_path):
        captured_paths.append(str(output_path))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"%PDF-mock")
        return b"%PDF-mock"

    # Run pipeline 2x com mesmo PDF input + job_ids distintos
    # ... implementation
    assert len(set(captured_paths)) == 2  # paths diferentes
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
| 2026-05-14 | @sm (River) | Draft Sprint 6.1 Wave 6.1.1 — pdf_filename job_id-based (Smith F-γ-07 multi-tenancy fix) |
| 2026-05-14 | @po (Keymaker) | Validation GO 10/10 — flip Draft → Ready |
| 2026-05-14 | @dev (Neo) | Implementação completa Wave 6.1.1 — revisar_contrato signature `job_id: str \| None = None` (retrocompat opt-in) + pdf_filename hybrid `{job_id[:8]}-{contract_hash[:8]}.pdf` (job_id ≠ None) OR fallback legacy contract_hash[:16].pdf + audit field peca_pdf_filename + app.py revisar_stream passa job_id=job_id ao pipeline + 2 unit tests novos (uses_job_id_when_provided + legacy_fallback) — flip Ready → Ready for Review. Files: bloco_workflow/pipeline.py + bloco_interface/web/app.py + tests/unit/test_weasyprint_render.py |
