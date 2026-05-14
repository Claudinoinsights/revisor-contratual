---
type: story
id: TD-SP06.1-PIPELINE-STEP-8-GRACEFUL
title: "Pipeline Step 8 graceful degradation — preserva peça LLM se weasyprint falha"
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
estimated_effort: "1h"
severity_origem: "MEDIUM (Smith F-γ-06 — Step 8 falha derruba peça LLM real Step 7)"
created: "2026-05-14"
created_by: "@sm (River)"
related_adrs:
  - "ADR-022 D3 Pipeline Integration"
  - "ADR-022 D5 Weasyprint config"
related_findings:
  - "Smith F-γ-06 MEDIUM (review-bloco-gamma-pos-execution-2026-05-14)"
related_stories:
  - "TD-SP06-WEASYPRINT-PECA-01 (Bloco γ original — Step 8 sem try/except)"
unblocks:
  - "UX: usuário não perde peça LLM gerada (Step 7) se PDF render falha (Step 8)"
  - "Sprint 7+: novo endpoint /regenerar-pdf/{job_id} retry rendering"
tags:
  - project/revisor-contratual
  - story
  - sprint-6-1
  - hotfix
  - graceful-degradation
  - ready
---

# Story TD-SP06.1-PIPELINE-STEP-8-GRACEFUL — Step 8 try/except weasyprint failure

## Story

**Como** advogado revisor após pipeline complete,
**Eu quero** receber a peça LLM gerada (Step 7) mesmo se weasyprint PDF render (Step 8) falhar (ex: GTK libs missing, filesystem permission),
**Para que** ~90s-2min de inferência LLM real não sejam perdidos por falha em render PDF (refinement).

---

## Contexto

Smith F-γ-06 MEDIUM identificou que `pipeline.py` Step 8 weasyprint NÃO tem try/except específico. Se `render_peca_pdf()` falhar (template not found, GTK runtime ausente VPS, filesystem permission revoked, malformed HTML), exceção propaga ao `except Exception` global linha 331+ → Pipeline INTEIRO falha com status FAILED — incluindo a peça LLM REAL gerada com sucesso no Step 7.

UX rough: usuário espera 2min LLM inference + ao final recebe erro genérico por falha render PDF. Sprint 6.1 corrige com graceful degradation.

---

## Acceptance Criteria

- **AC-01:** `bloco_workflow/pipeline.py` Step 8 (linhas 384-438) wrap weasyprint render call em try/except específico (catch `weasyprint.WeasyprintError` + `OSError` + `FileNotFoundError` — NÃO bare Exception)
- **AC-02:** Quando Step 8 fails:
  - `audit_payload["peca_pdf_generated"] = False`
  - `audit_payload["peca_pdf_render_error"] = type(exc).__name__ + ": " + str(exc)[:300]`
  - `peca_pdf_path` NÃO populated (None)
  - `peca_pdf_hash` NÃO populated (None)
- **AC-03:** Pipeline status SUCCESS (não FAILED) quando peca LLM OK mas PDF falhou — Step 7 success preservado
- **AC-04:** `result_capture` preserva peca_format e peca_template mesmo sem peca_pdf_path:
  ```python
  if result_capture is not None:
      result_capture["peca_format"] = peca_format
      result_capture["peca_template"] = template_name
      result_capture["peca_pdf_path"] = None  # explicit None se falhou
  ```
- **AC-05:** logger.warning emitido com contexto (template_name + exception detail)
- **AC-06:** Novo test `test_step_8_weasyprint_failure_does_not_fail_pipeline`:
  - Mock `pdf_renderer_fn` raises `OSError("simulated GTK libs missing")`
  - Verifica pipeline retorna VeredictoJuiz (não levanta PipelineError)
  - Verifica audit_payload tem peca_pdf_generated=False
- **AC-07:** Pytest baseline 478 PASS maintained (target 479+ com novo test)

---

## Tasks / Subtasks

- [ ] Task 1: Wrap Step 8 try/except
  - [ ] 1.1 Identificar exceptions específicas weasyprint (importar `weasyprint.WeasyprintError`)
  - [ ] 1.2 Try block envolve render_peca_pdf call + compute_pdf_hash + chmod
  - [ ] 1.3 Except block popula audit fields graceful failure
- [ ] Task 2: result_capture graceful failure path
  - [ ] 2.1 Preserva peca_format + peca_template
  - [ ] 2.2 peca_pdf_path = None explicit
- [ ] Task 3: Logger contextual warning
  - [ ] 3.1 logger.warning com template_name + exception type + message[:300]
- [ ] Task 4: Unit test
  - [ ] 4.1 test_step_8_weasyprint_failure_does_not_fail_pipeline em test_weasyprint_render.py
  - [ ] 4.2 Mock pdf_renderer_fn raises OSError simulando GTK ausente
  - [ ] 4.3 Verifica pipeline retorna VeredictoJuiz + audit graceful fields
- [ ] Task 5: Update File List + Change Log
- [ ] Task 6: Self-critique + handoff Oracle Sprint 6.1.3 smoke

---

## Dev Notes (Technical Context)

**Aria fix_approach:** Wrap Step 8 em try/except local. Se weasyprint falhar, registrar `audit_payload[peca_pdf_generated]=False` + reason mas marcar pipeline status SUCCESS para peca LLM real preservada. UI pode permitir re-tentar render via novo endpoint `/regenerar-pdf/{job_id}` (Sprint 7+).

**Skeleton implementation:**

```python
# bloco_workflow/pipeline.py Step 8 (Sprint 6.1 graceful):
try:
    if pdf_renderer_fn is None:
        from bloco_engine.pdf.render import compute_pdf_hash, render_peca_pdf
        pdf_bytes = await asyncio.to_thread(
            render_peca_pdf, template_name, render_context, pdf_output_path,
        )
        pdf_hash = compute_pdf_hash(pdf_bytes)
    else:
        pdf_bytes = await asyncio.to_thread(
            pdf_renderer_fn, template_name, render_context, pdf_output_path,
        )
        import hashlib as _hl
        pdf_hash = _hl.sha256(pdf_bytes).hexdigest()

    audit_payload["peca_pdf_path"] = str(pdf_output_path)
    audit_payload["peca_pdf_hash"] = pdf_hash
    audit_payload["peca_pdf_size_bytes"] = len(pdf_bytes)
    audit_payload["peca_template"] = template_name
    audit_payload["peca_pdf_generated"] = True

    if result_capture is not None:
        result_capture["peca_pdf_path"] = str(pdf_output_path)
        result_capture["peca_pdf_hash"] = pdf_hash
        result_capture["peca_format"] = peca_format
        result_capture["peca_template"] = template_name

except (OSError, FileNotFoundError) as render_exc:
    # F-γ-06 graceful degradation: preserva peca LLM Step 7 mesmo se PDF render falha
    logger.warning(
        "Step 8 weasyprint render falhou (template=%s): %s — peça LLM preserved",
        template_name, render_exc,
    )
    audit_payload["peca_pdf_generated"] = False
    audit_payload["peca_pdf_render_error"] = (
        f"{type(render_exc).__name__}: {str(render_exc)[:300]}"
    )
    audit_payload["peca_template"] = template_name

    if result_capture is not None:
        result_capture["peca_format"] = peca_format
        result_capture["peca_template"] = template_name
        result_capture["peca_pdf_path"] = None
```

**Weasyprint exceptions:** principal é `WeasyprintError` (catch-all weasyprint runtime issues). OSError catches GTK libs missing (libgobject-2.0-0 absent). FileNotFoundError catches template missing OR base_url path issues.

---

## Testing

```python
@pytest.mark.asyncio
async def test_step_8_weasyprint_failure_does_not_fail_pipeline(tmp_path, monkeypatch):
    """F-γ-06 Sprint 6.1: Step 8 render fail preserves peca LLM Step 7."""
    def mock_renderer_fails(template, ctx, output_path):
        raise OSError("simulated libgobject-2.0-0 missing (GTK ausente)")

    # Mock dependencies + run revisar_contrato com pdf_renderer_fn=mock_renderer_fails
    # ... implementation Neo
    veredito = await revisar_contrato(..., pdf_renderer_fn=mock_renderer_fails)

    assert veredito.veredito in {"APROVADO_100", "APROVADO_COM_RISCO_HITL", "REJEITADO"}
    # audit.jsonl última entry tem peca_pdf_generated=False + peca_pdf_render_error
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
| 2026-05-14 | @sm (River) | Draft Sprint 6.1 Wave 6.1.1 — Step 8 graceful degradation weasyprint (Smith F-γ-06 remediation) |
| 2026-05-14 | @po (Keymaker) | Validation GO 10/10 — flip Draft → Ready |
| 2026-05-14 | @dev (Neo) | Implementação completa Wave 6.1.1 — pipeline.py Step 8 wrap try/except específico (OSError + FileNotFoundError + RuntimeError, não bare Exception) + audit_payload[peca_pdf_generated]=True/False + peca_pdf_render_error registrado em falha + result_capture preserva peca_format/template/render_error/pdf_path=None graceful + logger.warning template + exception detail + 1 unit test novo (graceful_degradation_dict_keys) — flip Ready → Ready for Review. Files: bloco_workflow/pipeline.py + tests/unit/test_weasyprint_render.py |
