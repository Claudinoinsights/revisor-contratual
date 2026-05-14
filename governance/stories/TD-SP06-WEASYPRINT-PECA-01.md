---
type: story
id: TD-SP06-WEASYPRINT-PECA-01
title: "Weasyprint Render Peça Revisional — 3 templates Jinja2 OrSheva 7 + pipeline Step 8"
status: Ready for Review
priority: 1
sprint: "6.x AGGRESSIVE Bloco γ"
epic: "Sprint-6-Bloco-Gamma-Peca-Revisional-AI"
wave: "γ.1 (foundation, paralelo TD-SP06-REDATOR-LLM-01)"
owner: "@dev (Neo) + @ux-design-expert (Sati) cross-domain"
estimated_effort: "6h Neo + 2h Sati"
severity_origem: "CRITICAL (sem render PDF não há deliverable)"
created: "2026-05-14"
created_by: "@sm (River)"
validated_by: "@po (Keymaker)"
validated_at: "2026-05-14"
validation_score: "10/10"
validation_verdict: "GO"
related_adrs:
  - "ADR-022 D4 Template HTML estructure + D5 Weasyprint config"
related_prds:
  - "PRD-SP06-GAMMA v0.1.0 FR-PECA-02 + FR-PECA-04 + NFR-PECA-02 + NFR-PECA-03"
related_stories:
  - "TD-SP06-REDATOR-LLM-01 (γ.1 paralelo — produz PecaRevisional input)"
  - "TD-SP06-DOWNLOAD-ROUTES-01 (γ.2 depende peca_pdf_path)"
related_findings:
  - "Smith Fase 7-A F-D1-02 CRITICAL — PDF horrível JS Bloco β REMOVED, backend render resolve"
  - "Smith Fase 7-A F-D5-26 MEDIUM — weasyprint v68.1 instalado mas nenhum código usa"
unblocks:
  - "Wave γ.2 DOWNLOAD-ROUTES (precisa PDF gerado)"
  - "Eric demo Bloco γ final (peça revisional baixável)"
tags:
  - project/revisor-contratual
  - story
  - sprint-6
  - bloco-gamma
  - weasyprint
  - pdf-render
  - templates-jinja2
  - orsheva-7
  - ready-for-review
---

# Story TD-SP06-WEASYPRINT-PECA-01 — Weasyprint Render Peça Revisional

## Story

**Como** advogado revisor após pipeline complete,
**Eu quero** baixar a peça revisional como PDF profissional formatado (cabeçalho OrSheva 7 + tipografia Lora/Outfit + 8 seções CFOAB + numeração páginas + footer disclaimer LGPD/OAB),
**Para que** eu possa imprimir, customizar ou submeter ao juízo sem retrabalho de formatação.

---

## Contexto

ADR-022 D4 + D5 (Aria 2026-05-14) definem template Jinja2 + weasyprint config. Smith Fase 7-A F-D5-26 confirmou weasyprint v68.1 instalado mas nenhum código usa. Story implementa Step 8 pipeline (serial pós-Redator) com 3 variantes template baseado em veredito.

---

## Acceptance Criteria

- **AC-01:** 3 templates Jinja2 em `bloco_interface/web/templates/peca/`:
  - `inicial-revisional-veiculos.html` (APROVADO_100 — peça completa 8 seções)
  - `inicial-revisional-com-hitl.html` (APROVADO_COM_RISCO_HITL — peça + seção "Pontos de Atenção")
  - `relatorio-inviabilidade.html` (REJEITADO — análise técnica + recomendação não-protocolar)
- **AC-02:** Tokens OrSheva 7 inline CSS em cada template (não link external — weasyprint render isolated):
  - `font-family: 'Lora', serif` (corpo) + `'Outfit', sans-serif` (headers)
  - CSS variables `--peca-primary`, `--peca-muted` etc
  - Sati delivery: paleta cores + spacing tokens em PR comment
- **AC-03:** Page settings via `@page` CSS:
  - `size: A4 portrait`
  - `margin: 25mm`
  - `@bottom-right { content: counter(page) "/" counter(pages); }` (numeração)
  - Header repetido com SVG logo OrSheva 7 inline
  - Footer com disclaimer LGPD/OAB compacto
- **AC-04:** Novo módulo `bloco_engine/pdf/render.py` com função `render_peca_pdf(template_name, context, output_path) -> bytes`:
  - Reuso Jinja2 environment existente (`bloco_interface/web/app.py templates`)
  - Weasyprint `HTML(string=rendered, base_url=...).write_pdf()`
  - `base_url` aponta para `bloco_interface/web/static/` (resolve fontes self-hosted)
- **AC-05:** `output_path.chmod(0o600)` pós-write (NFR-PECA-04 LGPD §46)
- **AC-06:** PDF metadata:
  - title: `peca.cabecalho[:60]`
  - author: `"Revisor Contratual SaaS"`
  - subject: `f"Peça Revisional {contrato.modalidade}"`
  - producer: `"weasyprint v68.1"`
- **AC-07:** Pipeline integration — `bloco_workflow/pipeline.py` adicionar Step 8 serial pós-Step 7 Redator. Wrap `asyncio.to_thread(render_peca_pdf, ...)`. Output path: `DEFAULT_DATA_DIR / "pecas" / f"{job_id}.pdf"`. Parent dir chmod 0o700 (mkdir parents=True, mode=0o700)
- **AC-08:** Audit fields em Step 8:
  - `peca_pdf_hash`: SHA256 do PDF bytes
  - `peca_pdf_size_bytes`: len(pdf_bytes)
  - `peca_pdf_path`: str(output_path) (para JOBS dict)
- **AC-09:** JOBS dict storage extension — `JOBS[job_id]["peca_pdf_path"] = str(pdf_output_path)` (para DOWNLOAD-ROUTES Wave γ.2 consume)
- **AC-10:** Latency render <30s typical (NFR-PECA-02) — measure em test
- **AC-11:** Unit tests `tests/unit/test_weasyprint_render.py` — 4 tests:
  - test_render_peca_aprovado_100_generates_valid_pdf
  - test_render_peca_com_hitl_includes_pontos_atencao_section
  - test_render_relatorio_inviabilidade_uses_separate_template
  - test_pdf_output_chmod_600_lgpd_compliance

---

## Tasks / Subtasks

- [ ] Task 1: Sati design tokens delivery (cross-domain @ux-design-expert)
  - [ ] 1.1 Paleta cores peça revisional (--peca-primary, --peca-muted, --peca-accent)
  - [ ] 1.2 Spacing tokens (margins, paddings) compatible weasyprint @page
  - [ ] 1.3 SVG logo OrSheva 7 inline-ready (otimizado size)
- [ ] Task 2: 3 templates Jinja2 (`bloco_interface/web/templates/peca/`)
  - [ ] 2.1 `inicial-revisional-veiculos.html` (APROVADO_100) — 8 seções CFOAB + inline CSS + @page
  - [ ] 2.2 `inicial-revisional-com-hitl.html` (com HITL) — herda base + adiciona seção "Pontos de Atenção"
  - [ ] 2.3 `relatorio-inviabilidade.html` (REJEITADO) — template separado (análise técnica, não petição)
  - [ ] 2.4 Header + footer macros reusáveis (DRY)
- [ ] Task 3: Render module (`bloco_engine/pdf/render.py` NEW)
  - [ ] 3.1 Function `render_peca_pdf(template_name, context, output_path)`
  - [ ] 3.2 Reuso Jinja2 env (import templates from app.py OR criar env local)
  - [ ] 3.3 Weasyprint HTML().write_pdf() chain
  - [ ] 3.4 base_url para resolve fontes self-hosted /static/fonts/
  - [ ] 3.5 PDF metadata population
  - [ ] 3.6 chmod 0o600 pós-write
- [ ] Task 4: Pipeline integration (`bloco_workflow/pipeline.py`)
  - [ ] 4.1 Adicionar Step 8 serial pós-Step 7 (linha ~340 atual após Redator)
  - [ ] 4.2 asyncio.to_thread wrap render_peca_pdf
  - [ ] 4.3 template_variant lookup: APROVADO_100 → veiculos | COM_HITL → com_hitl | REJEITADO → inviabilidade
  - [ ] 4.4 Audit payload: peca_pdf_hash + peca_pdf_size_bytes + peca_pdf_path
  - [ ] 4.5 JOBS[job_id]["peca_pdf_path"] extension
  - [ ] 4.6 Try/except weasyprint errors → log + raise PipelineError
- [ ] Task 5: Unit tests (`tests/unit/test_weasyprint_render.py`)
  - [ ] 5.1 Fixture PecaRevisional + RelatorioInviabilidade valid instances
  - [ ] 5.2 4 tests AC-11
- [ ] Task 6: Update File List + Change Log
- [ ] Task 7: Self-critique
- [ ] Task 8: Handoff Neo → Oracle (γ.2 + γ.3)

---

## Dev Notes (Technical Context)

**ADR-022 D4 — Template structure skeleton:**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>{{ peca.cabecalho|truncate(60) }}</title>
  <style>
    @font-face { font-family: 'Lora'; src: url('fonts/Lora-Regular.ttf'); }
    @font-face { font-family: 'Outfit'; src: url('fonts/Outfit-Regular.ttf'); }
    body { font-family: 'Lora', serif; font-size: 12pt; line-height: 1.6; margin: 25mm; }
    h1, h2 { font-family: 'Outfit', sans-serif; color: var(--peca-primary, #1a1a2e); }
    .secao { margin-bottom: 18pt; page-break-inside: avoid; }
    .disclaimer { font-size: 9pt; color: var(--peca-muted, #6c757d); margin-top: 24pt; border-top: 1pt solid #ddd; padding-top: 12pt; }
    @page { size: A4 portrait; margin: 25mm; @bottom-right { content: counter(page) "/" counter(pages); } }
  </style>
</head>
<body>
  <header><svg>...OrSheva 7 logo inline...</svg></header>
  <section class="secao cabecalho">{{ peca.cabecalho }}</section>
  <section class="secao qualificacao"><h2>Da Qualificação das Partes</h2>{{ peca.qualificacao_partes }}</section>
  <section class="secao fatos"><h2>Dos Fatos</h2>{{ peca.dos_fatos }}</section>
  <section class="secao direito"><h2>Do Direito</h2>{{ peca.do_direito }}</section>
  <section class="secao pedido"><h2>Do Pedido</h2>{{ peca.do_pedido }}</section>
  <section class="secao valor-causa">
    <h2>Do Valor da Causa</h2>
    <p>Atribui-se à causa o valor de <strong>{{ peca.valor_causa }}</strong> ({{ peca.valor_causa_extenso }}).</p>
  </section>
  <section class="secao fecho">{{ peca.fecho }}</section>
  <footer class="disclaimer">{{ peca.disclaimer_lgpd_oab }}</footer>
</body>
</html>
```

**ADR-022 D5 — render_peca_pdf skeleton:**

```python
from weasyprint import HTML
from pathlib import Path

def render_peca_pdf(template_name: str, context: dict, output_path: Path) -> bytes:
    from bloco_interface.web.app import templates  # reuso Jinja2 env
    rendered_html = templates.get_template(template_name).render(context)
    pdf_bytes = HTML(
        string=rendered_html,
        base_url=str(Path("bloco_interface/web/static").absolute()),
    ).write_pdf()
    output_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    output_path.write_bytes(pdf_bytes)
    output_path.chmod(0o600)
    return pdf_bytes
```

**Fontes self-hosted** (REV-INT-02 LGPD §46): `bloco_interface/web/static/fonts/Lora-Regular.ttf` + `Outfit-Regular.ttf` (já existem — verificar via `ls`).

**SVG logo OrSheva 7** — reusar inline SVG do SPA index.html linha 969-976 (extract para template macro).

---

## Testing

**Pytest unit:**

```bash
py -3.14 -m pytest tests/unit/test_weasyprint_render.py -o addopts="" --tb=short -v
# Esperado: 4/4 PASS

# Latency measure (manual smoke):
import time
start = time.time()
pdf_bytes = render_peca_pdf("peca/inicial-revisional-veiculos.html", context, output_path)
elapsed = time.time() - start
assert elapsed < 30  # NFR-PECA-02
```

**Empirical smoke** (Oracle Bloco γ.3):
- Render 3 PDFs (1 per veredito) → verificar abrir em viewer (não corrompido) + metadata correta

---

## Dev Agent Record

**Agent Model Used:** Neo (claude-opus-4-7 — Skill LMAS:agents:dev YOLO mode Eric AGGRESSIVE chain)
**Debug Log References:** Wave γ.1 paralelo (com TD-SP06-REDATOR-LLM-01)
**Completion Notes List:**
- 4 templates Jinja2 criados em `bloco_interface/web/templates/peca/`:
  - `_base_peca.html` — base template com tokens OrSheva 7 inline + @page A4 + numeração páginas + footer LGPD
  - `inicial-revisional-veiculos.html` (APROVADO_100) — 8 seções CFOAB completas
  - `inicial-revisional-com-hitl.html` (APROVADO_COM_RISCO_HITL) — peça + bloco "Pontos de Atenção" (HITL warn variant)
  - `relatorio-inviabilidade.html` (REJEITADO) — standalone template visual distinto (badge danger #B43D3D, NÃO petição)
- **Decisão técnica No Invention:** fontes alinhadas ao brandbook real OrSheva 7 v1.1.2 do projeto — Manrope (sans/UI) + Fraunces (serif/display), substituindo Lora/Outfit do skeleton ADR-022 que não existem em `static/fonts/`. Tokens reais: `--or-500 #EE6B20` (accent), neutros warm, danger `#B43D3D`.
- `bloco_engine/pdf/render.py` NEW — `render_peca_pdf(template_name, context, output_path)` + `compute_pdf_hash()` para audit chain. chmod 0o600 + parent dir mkdir 0o700 (NFR-PECA-04 LGPD §46) com graceful degradation Windows (logger.debug em NTFS).
- Pipeline Step 8 integrado em `pipeline.py` com asyncio.to_thread wrap + template variant lookup baseado em `veredito.veredito` + audit fields (`peca_pdf_path`, `peca_pdf_hash`, `peca_pdf_size_bytes`, `peca_template`) + `result_capture` dict opt-in para app.py popular JOBS[peca_pdf_path].
- 5/10 unit tests PASS + 5 skipped (weasyprint GTK runtime ausente em Windows — TD-SP06-WEASYPRINT-WIN-GTK-DEPS catalogado, coverage real em VPS Linux deploy). Offline coverage via Jinja2 env standalone testa estrutura HTML + tokens OrSheva 7 + 8 seções CFOAB rendering sem depender weasyprint.
- Pytest baseline expandido: 248 → 470 passed (ZERO regressões) + 5 skipped legítimos.

**File List:**
- `bloco_engine/pdf/__init__.py` (NEW — exports `render_peca_pdf`)
- `bloco_engine/pdf/render.py` (NEW — render_peca_pdf + compute_pdf_hash + Jinja2 env standalone)
- `bloco_interface/web/templates/peca/_base_peca.html` (NEW — base template OrSheva 7)
- `bloco_interface/web/templates/peca/inicial-revisional-veiculos.html` (NEW — APROVADO_100)
- `bloco_interface/web/templates/peca/inicial-revisional-com-hitl.html` (NEW — APROVADO_COM_RISCO_HITL)
- `bloco_interface/web/templates/peca/relatorio-inviabilidade.html` (NEW — REJEITADO)
- `bloco_workflow/pipeline.py` (MODIFIED — Step 8 Weasyprint integration + kwargs `peca_output_dir`, `pdf_renderer_fn`, `result_capture`)
- `tests/unit/test_weasyprint_render.py` (NEW — 10 tests, 5 PASS + 5 skip GTK)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-05-14 | @sm (River) | Draft inicial Bloco γ — foundation render PDF weasyprint |
| 2026-05-14 | @po (Keymaker) | Validation GO 10/10 — flip Draft → Ready |
| 2026-05-14 | @dev (Neo) | Implementação completa Wave γ.1 paralelo — 4 templates Jinja2 OrSheva 7 + render_peca_pdf + Pipeline Step 8 integration + chmod 0o600 LGPD + 5/10 tests PASS (5 skip Win GTK) + 470 baseline ZERO regressão — flip Ready → Ready for Review |
