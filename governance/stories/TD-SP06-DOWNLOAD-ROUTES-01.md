---
type: story
id: TD-SP06-DOWNLOAD-ROUTES-01
title: "GET /download/{job_id} — endpoint authenticated + ownership + audit + SPA btnDownload real"
status: Ready for Review
priority: 2
sprint: "6.x AGGRESSIVE Bloco γ"
epic: "Sprint-6-Bloco-Gamma-Peca-Revisional-AI"
wave: "γ.2 (integration — depende γ.1 done)"
owner: "@dev (Neo)"
estimated_effort: "2h"
severity_origem: "HIGH (entrega final ao usuário — peça baixável)"
created: "2026-05-14"
created_by: "@sm (River)"
validated_by: "@po (Keymaker)"
validated_at: "2026-05-14"
validation_score: "10/10"
validation_verdict: "GO"
depends_on:
  - "TD-SP06-REDATOR-LLM-01 (γ.1 done — JOBS[peca_format])"
  - "TD-SP06-WEASYPRINT-PECA-01 (γ.1 done — JOBS[peca_pdf_path])"
related_adrs:
  - "ADR-022 D6 Backward compat btnDownload + D7 SSE-OWNERSHIP-CHECK"
related_prds:
  - "PRD-SP06-GAMMA v0.1.0 FR-PECA-06 + NFR-PECA-04 + US-PECA-02 + US-PECA-05"
related_stories:
  - "TD-SP06-REDATOR-LLM-01 + TD-SP06-WEASYPRINT-PECA-01 (γ.1 precondition)"
  - "TD-SP06-FIDELITY-01 (γ.3 Oracle consume PDFs gerados via download)"
related_findings:
  - "Smith Bloco β F-D3-β-06 MEDIUM SSE-OWNERSHIP-CHECK — addressing via JOBS[owner] + authz endpoint"
  - "TD-SP06-BTN-DOWNLOAD-WEASYPRINT-BLOCO-GAMMA (Bloco β placeholder) — RESOLVED"
unblocks:
  - "Eric demo Bloco γ (download PDF revisional via SPA)"
  - "Wave γ.3 Oracle Fidelity (precisa baixar PDFs para análise)"
tags:
  - project/revisor-contratual
  - story
  - sprint-6
  - bloco-gamma
  - download-endpoint
  - authz
  - audit-chain
  - lgpd
  - ready-for-review
---

# Story TD-SP06-DOWNLOAD-ROUTES-01 — Download Endpoint Authenticated

## Story

**Como** advogado revisor com peça pronta,
**Eu quero** baixar via SPA btnDownload o PDF revisional autenticado (apenas owner do job pode baixar) com audit chain registrando download,
**Para que** eu possa salvar o arquivo localmente cumprindo LGPD + ownership integrity (Smith Bloco β F-D3-β-06 SSE-OWNERSHIP-CHECK address).

---

## Contexto

ADR-022 D6+D7 (Aria 2026-05-14) definem endpoint pattern. Smith Bloco β F-D3-β-06 MEDIUM apontou SSE sem ownership check — Bloco γ resolve adicionando `JOBS[owner]` + authz 403 em downloads. Story implementa endpoint + SPA refactor btnDownload (substitui placeholder Bloco β alert).

---

## Acceptance Criteria

- **AC-01:** Novo endpoint `GET /download/{job_id}` em `bloco_interface/web/app.py`:
  ```python
  @app.get("/download/{job_id}")
  async def download_peca(request: Request, job_id: str) -> Response:
      ...
  ```
- **AC-02:** Authz check obrigatório:
  - Session user não-vazio (raise 401 senão)
  - `request.session.get("user") == JOBS[job_id].get("owner")` (raise 403 senão — Smith F-D3-β-06 address)
- **AC-03:** 404 conditions:
  - `job_id not in JOBS` → 404 "Job não encontrado"
  - `JOBS[job_id].get("peca_pdf_path") is None` OR file não existe filesystem → 404 "Peça PDF ainda não gerada — aguarde pipeline complete"
- **AC-04:** Response 200:
  - `Content-Type: application/pdf`
  - `Content-Disposition: attachment; filename="peca-revisional-{job_id[:8]}.pdf"`
  - Body: PDF binary read from JOBS[peca_pdf_path]
- **AC-05:** JOBS dict storage extension — `JOBS[job_id]["owner"] = request.session.get("user")` adicionado na criação POST /revisar (linha 806 atual ~/JOBS dict definition)
- **AC-06:** Audit entry HMAC-chained `pdf_downloaded`:
  - `entry_type: "pdf_downloaded"`
  - `job_id`
  - `user`
  - `pdf_sha256` (SHA256 hash do PDF bytes — NÃO conteúdo NFR-PECA-04)
  - `timestamp` ISO 8601 UTC
- **AC-07:** SPA Bloco β btnDownload refactor (`static/index.html` linha ~2105 atual placeholder alert):
  - Substituir alert por `fetch('/download/' + jobId, {credentials: 'same-origin'})`
  - Blob URL + anchor click → browser save PDF
  - jobId extraído de `lastResult.verdictUrl` query param OR `lastResult.deliverables` field
  - Error handling 401 → redirect /classic; 403 → alert "Acesso negado"; 404 → alert "Peça ainda não disponível"
- **AC-08:** Unit tests `tests/unit/test_download_route.py` — 4 tests:
  - test_download_200_owner_receives_pdf
  - test_download_403_non_owner_forbidden
  - test_download_404_job_not_found
  - test_download_404_pdf_not_generated_yet
  - test_audit_entry_pdf_downloaded_created
- **AC-09:** Pytest baseline 248 passed maintained

---

## Tasks / Subtasks

- [ ] Task 1: JOBS dict extension owner field
  - [ ] 1.1 POST /revisar handler (app.py linha 806) — add `"owner": request.session.get("user")` no JOBS[job_id] dict
- [ ] Task 2: Download endpoint
  - [ ] 2.1 Adicionar `@app.get("/download/{job_id}")` em app.py (após POST /revisar)
  - [ ] 2.2 Authz check session + owner match
  - [ ] 2.3 404 logic (job não existe OR pdf não gerado)
  - [ ] 2.4 Read PDF bytes from JOBS[peca_pdf_path]
  - [ ] 2.5 Response com Content-Type + Content-Disposition
- [ ] Task 3: Audit entry pdf_downloaded
  - [ ] 3.1 `append_audit_entry("pdf_downloaded", entry_data, audit_path=DEFAULT_AUDIT_PATH)` chamada
  - [ ] 3.2 entry_data inclui user + job_id + pdf_sha256 + timestamp
- [ ] Task 4: SPA btnDownload refactor (`static/index.html`)
  - [ ] 4.1 Localizar btnDownload click handler atual (~linha 2105 placeholder alert Bloco β)
  - [ ] 4.2 Substituir alert por async fetch /download/{jobId}
  - [ ] 4.3 Blob → URL.createObjectURL → anchor.download → click → URL.revokeObjectURL (cleanup setTimeout 800ms)
  - [ ] 4.4 Error handling 401/403/404 com mensagens UI claras
  - [ ] 4.5 jobId extraction logic from lastResult
- [ ] Task 5: Unit tests (`tests/unit/test_download_route.py`)
  - [ ] 5.1 Fixture JOBS dict com peca_pdf_path real (temp PDF file)
  - [ ] 5.2 5 tests AC-08
- [ ] Task 6: Update File List + Change Log
- [ ] Task 7: Self-critique
- [ ] Task 8: Handoff Neo → Oracle (Wave γ.3 Fidelity)

---

## Dev Notes (Technical Context)

**ADR-022 D6 — SPA btnDownload skeleton:**

```javascript
document.getElementById('btnDownload').addEventListener('click', async () => {
  if (!lastResult || !lastResult.verdictUrl) return;
  const jobId = new URL(lastResult.verdictUrl, location.origin).searchParams.get('job_id');
  try {
    const resp = await fetch(`/download/${jobId}`, { credentials: 'same-origin' });
    if (!resp.ok) {
      if (resp.status === 401) { location.href = '/classic'; return; }
      if (resp.status === 403) { alert('Acesso negado'); return; }
      throw new Error(`HTTP ${resp.status}`);
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `peca-revisional-${jobId.slice(0, 8)}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 800);
  } catch(err) {
    alert(`Erro download: ${err.message}`);
  }
});
```

**ADR-022 D7 — Endpoint skeleton:**

```python
@app.get("/download/{job_id}")
async def download_peca(request: Request, job_id: str) -> Response:
    user = request.session.get("user")
    if not user:
        raise HTTPException(401, "Autenticação requerida")
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado")
    if user != job.get("owner"):
        raise HTTPException(403, "Acesso negado")
    pdf_path_str = job.get("peca_pdf_path")
    if not pdf_path_str or not Path(pdf_path_str).exists():
        raise HTTPException(404, "Peça PDF ainda não gerada — aguarde pipeline complete")
    pdf_path = Path(pdf_path_str)
    pdf_bytes = pdf_path.read_bytes()
    audit_entry = {
        "type": "pdf_downloaded",
        "job_id": job_id,
        "user": user,
        "pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    append_audit_entry("pdf_downloaded", audit_entry, audit_path=DEFAULT_AUDIT_PATH)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="peca-revisional-{job_id[:8]}.pdf"'},
    )
```

**Sprint 6+ Sprint nota:** Mesmo padrão authz pode ser aplicado a `GET /revisar/stream/{job_id}` (Smith F-D3-β-06 full address). Bloco γ scope MVP = apenas /download; SSE auth fica Sprint 6+ se Smith review γ flag novamente.

---

## Testing

**Pytest unit:** 5 tests AC-08 com monkeypatch fixture `authed_client` (mirror test_classic_route.py).

**Empirical smoke** (Operator + Eric):
- Eric upload PDF veículo synthetic → SPA → backend Step 7+8 → audit `peca_generated`
- SPA btnDownload click → fetch /download/{jobId} → browser save peca-revisional-{prefix}.pdf
- Verificar audit.jsonl entry `pdf_downloaded`

---

## Dev Agent Record

**Agent Model Used:** Neo (claude-opus-4-7 — Skill LMAS:agents:dev Wave γ.2 self-continuation)
**Debug Log References:** Wave γ.2 (após Wave γ.1 REDATOR + WEASYPRINT done)
**Completion Notes List:**
- Endpoint `GET /download/{job_id}` implementado em `bloco_interface/web/app.py` (linhas ~854-933) com:
  - AC-02 ownership check `session.user == JOBS[job_id]["owner"]` (Smith β F-D3-β-06 partial address)
  - AC-03 cascata 401 (sem session) → 404 (job ausente) → 403 (non-owner) → 404 (PDF não gerado) → 404 (file não existe)
  - AC-04 Response 200 com Content-Type `application/pdf` + Content-Disposition `attachment` + `X-Peca-Format` header
  - AC-06 audit chain `pdf_downloaded` HMAC-chained (user + pdf_sha256 + pdf_size_bytes + peca_format + timestamp UTC ISO)
- JOBS dict extension AC-05: adicionado `owner: request.session.get("user")` + `peca_pdf_path` + `peca_pdf_hash` + `peca_format` no POST /revisar (linha ~806). `peca_pdf_path` populado via `pipeline_capture` dict (Wave γ.1 result_capture pattern) após Step 8 Weasyprint complete.
- AC-07 SPA btnDownload refactor (`static/index.html` linhas ~2117 + ~2166-2210):
  - Removido placeholder alert "Sprint 6 Bloco γ shipped"
  - Added `_extractJobIdFromVerdictUrl()` helper para extrair job_id de `lastResult.verdictUrl`
  - Fetch /download/{jobId} com credentials=same-origin + error handling 401 (redirect /classic) + 403 (alert "Acesso negado") + 404 (alert "Peça ainda não disponível")
  - Blob URL → anchor.download → click → cleanup setTimeout 1000ms
- AC-08 7/7 unit tests PASS em `tests/unit/test_download_route.py`:
  - test_download_200_owner_receives_pdf
  - test_download_401_unauthenticated_rejected
  - test_download_403_non_owner_forbidden
  - test_download_404_job_not_found
  - test_download_404_pdf_not_generated_yet
  - test_download_audit_entry_created_pdf_downloaded
  - test_download_content_disposition_attachment_filename
- AC-09 Pytest baseline expandido: 470 → **477 passed + 5 skipped** · ZERO regressões.
- Decisão técnica Neo: tests validam status_code (gate semântico) sem `.json()` parse — error_handler middleware do projeto renderiza HTML s7_error em vez de JSON default. Backward-compat preservado (não alterar middleware).

**File List:**
- `bloco_interface/web/app.py` (MODIFIED) — import Response + append_audit_entry + JOBS dict 4 novos fields + pipeline_capture wiring + GET /download/{job_id} endpoint
- `bloco_interface/web/static/index.html` (MODIFIED) — btnDownload click handler refatorado (fetch real + blob + error handling)
- `tests/unit/test_download_route.py` (NEW) — 7 tests, 7 PASS

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-05-14 | @sm (River) | Draft inicial Bloco γ Wave γ.2 — download endpoint + SPA refactor |
| 2026-05-14 | @po (Keymaker) | Validation GO 10/10 — flip Draft → Ready |
| 2026-05-14 | @dev (Neo) | Implementação completa Wave γ.2 — endpoint GET /download/{job_id} + authz JOBS[owner] + audit pdf_downloaded + SPA btnDownload fetch real + 7/7 unit tests PASS + 477 baseline ZERO regressão — flip Ready → Ready for Review |
| 2026-05-14 | @dev (Neo) | **Hotfix Smith F-γ-01 HIGH** — audit-first pattern em /download endpoint (LGPD §46 compliance). `append_audit_entry` failure agora raises HTTPException 503 em vez de silent log.error+continue. Novo test `test_download_503_when_audit_fails` (mock raises) PASS. Baseline 477 → 478 PASS ZERO regressões. Arquivos: bloco_interface/web/app.py + tests/unit/test_download_route.py |
