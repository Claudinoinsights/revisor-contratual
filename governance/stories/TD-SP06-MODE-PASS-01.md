---
type: story
id: TD-SP06-MODE-PASS-01
title: "Sidebar data-mode → backend modalidade override (passar seleção UI ao pipeline real)"
status: Ready for Review
priority: 2
validated_by: "@po (Keymaker)"
validated_at: "2026-05-14"
validation_score: "10/10"
implemented_by: "@dev (Neo)"
implemented_at: "2026-05-14"
implementation_evidence: "4/4 tests PASS Python 3.14 + 248 baseline maintained + audit modalidade_override_used field"
sprint: "6.x AGGRESSIVE"
epic: "Sprint-6-Bloco-Beta-Frontend-Backend-Integration"
owner: "@dev (Neo) + @architect (Aria) cross-domain (modalidade mapping)"
estimated_effort: "1-2h"
severity_origem: "MEDIUM (UX clarity + DP-03 MVP awareness; Veículo funciona sem isto via regex default)"
created: "2026-05-14"
created_by: "@sm (River)"
depends_on:
  - "TD-SP06-SPA-CONNECT-01 (FormData mechanism shared)"
related_adrs:
  - "ADR-020 Multi-Doctype Dispatcher v2 (sidebar 7 modos mapping)"
  - "DP-03 PRD v1.0.2 (MVP cobre apenas CDC_VEICULOS_PF; codigos_bacen.yaml fonte)"
  - "TD-SP06-MVP-MODALIDADES-RESTRITAS (cataloged Operator AC-05 smoke)"
related_stories:
  - "TD-SP06-SPA-CONNECT-01 (FormData mechanism precondition)"
  - "TD-SP06-PHASE-VALID-01 (S7 error 422 modalidade não-MVP)"
related_findings:
  - "Smith Fase 7-A F-D1-03 CRITICAL: SPA não passa modo ao backend"
  - "Operator AC-05 smoke attempt 1 NotImplementedError: 'CDC_BENS_PF' não suportada MVP"
unblocks:
  - "Modalidade override Eric demo clareza"
  - "Preparação Sprint 6+ expansão modalidades (cartão, consignado, imobiliário, FIES, geral)"
tags:
  - project/revisor-contratual
  - story
  - sprint-6
  - bloco-beta
  - modalidade-override
  - draft
---

# Story TD-SP06-MODE-PASS-01 — Sidebar → Backend Modalidade Override

## Story

**Como** advogado revisor escolhendo modalidade contratual na sidebar SPA (CCB / Veículo / Imobiliário / FIES / Cartão / Consignado / Geral),
**Eu quero** que minha seleção seja enviada ao backend como override explícito de `ContratoMetadata.modalidade`, com indicação visual clara de quais modalidades estão suportadas no MVP (CDC_VEICULOS_PF only),
**Para que** o pipeline real use a modalidade correta (não dependa apenas da heurística regex `_extract_modalidade` ambígua) e eu saiba antecipadamente quais modos retornam NotImplementedError (DP-03 restrição MVP).

---

## Contexto

**Trigger:** Operator AC-05 smoke attempt 1 (2026-05-14) falhou com:

```
NotImplementedError: Modalidade 'CDC_BENS_PF' não suportada no MVP — motivo: DP-03 — fora do escopo MVP
```

ContratoMetadata.modalidade enum (`bloco_contratos/contrato.py:19`):
- `CDC_VEICULOS_PF` ✅ MVP foco (codigos_bacen.yaml SGS 25471)
- `CDC_BENS_PF` ❌ DP-03 fora MVP
- `CDC_IMOBILIARIO` ❌ DP-03 (SFH/SFI regime jurídico próprio Lei 9.514)
- `CARTAO_ROTATIVO` ❌ DP-03 (Res. CMN 4.549 regulamentar)

SPA sidebar atual (Sprint 5+ Bloco 3) tem 7 modos visualmente clicáveis com `data-mode="ccb|veiculo|consignado|cartao|imobiliario|fies|geral"` mas valor **nunca enviado ao backend** (Smith Fase 7-A F-D1-03 finding).

Pipeline atual depende de regex `_extract_modalidade` heurística em `bloco_engine/parsing/orchestrator.py:89`. Pode errar em PDFs ambíguos. Override explícito UI resolve.

---

## Acceptance Criteria

1. **AC-01:** Mapping declarativo SPA mode → backend ModalidadeContrato (constante exportada de módulo Python ou inline em handler):
   - `"ccb"` → `"CDC_BENS_PF"` (warning UI: não-MVP)
   - `"veiculo"` → `"CDC_VEICULOS_PF"` (verde MVP-supported)
   - `"consignado"` → `"CDC_BENS_PF"` (warning não-MVP)
   - `"cartao"` → `"CARTAO_ROTATIVO"` (warning não-MVP)
   - `"imobiliario"` → `"CDC_IMOBILIARIO"` (warning não-MVP)
   - `"fies"` → `"CDC_BENS_PF"` (warning não-MVP)
   - `"geral"` → `"CDC_BENS_PF"` (warning não-MVP — catch-all)
   - `"welcome"` / `"apikey"` → null (não-análise, não envia)

2. **AC-02:** SPA `submitAnalysisReal()` (de TD-SP06-SPA-CONNECT-01) inclui campo FormData `modalidade_override`:
   - Valor = mapping[currentMode] OR null se welcome/apikey
   - SPA blocking pré-submit: se mode não-MVP → modal warning "Modalidade X em desenvolvimento Sprint 6+. Use Veículo para teste real. Continuar mesmo assim? (sim/não)"

3. **AC-03:** Backend `POST /revisar` aceita novo Form parameter:
   ```python
   modalidade_override: str | None = Form(default=None)
   ```
   - Se fornecido e valor em `ModalidadeContrato` enum válido → passa para `revisar_contrato(modalidade_override=...)`
   - Se inválido → 422 Unprocessable Entity com diagnostic claro
   - Se None → preserva behavior atual (regex `_extract_modalidade`)

4. **AC-04:** `bloco_workflow/pipeline.py revisar_contrato()` aceita novo kwarg `modalidade_override: ModalidadeContrato | None = None`:
   - Após Step 1 parsing (linha ~199), antes Step 2 cálculo
   - Se `modalidade_override` not None → `parsed.metadata.modalidade = modalidade_override` (mutação controlada Pydantic via .model_copy(update={...}))
   - Senão → preserva regex extracted

5. **AC-05:** Se modalidade não-MVP escolhida → backend retorna 422:
   ```json
   {
     "detail": "Modalidade 'CDC_IMOBILIARIO' ainda não suportada no MVP (DP-03). Use 'CDC_VEICULOS_PF' para teste real. Sprint 6+ ADR específica expandirá suporte.",
     "modalidade_solicitada": "CDC_IMOBILIARIO",
     "modalidades_mvp_suportadas": ["CDC_VEICULOS_PF"],
     "tech_debt_ref": "TD-SP06-MVP-MODALIDADES-RESTRITAS"
   }
   ```
   - SPA captura 422 → renderiza S7 error pane com mensagem user-friendly

6. **AC-06:** Sidebar SPA visual indicators:
   - Modos MVP-suportados (`veiculo`): icon checkmark verde OR badge "Real"
   - Modos não-MVP (CCB, Imobiliário, FIES, Cartão, Consignado, Geral): icon warning amarelo OR badge "Sprint 6+"
   - Tooltip data-tooltip atual expandido com status MVP

7. **AC-07:** Empirical evidence:
   - Eric clica "Veículo" → upload contrato_veiculo_synthetic.pdf → audit.jsonl entry com `modalidade: "CDC_VEICULOS_PF"` (explicit override, não inferido regex)
   - Eric clica "Imobiliário" → upload qualquer PDF → SPA bloqueia OR backend 422 → S7 pane mostrado

---

## Tasks / Subtasks

- [ ] Task 1: Decisão arquitetural mapping localização
  - [ ] 1.1 Opção A: constante Python `bloco_contratos/modalidade_mapping.py` exportada
  - [ ] 1.2 Opção B: inline em `app.py` handler `POST /revisar`
  - [ ] 1.3 Recomendado Opção A (reuso CLI standalone + tests + SPA JSON config endpoint)
- [ ] Task 2: Backend handler update
  - [ ] 2.1 `POST /revisar` linha 650: adicionar `modalidade_override: str | None = Form(default=None)`
  - [ ] 2.2 Validar valor contra `ModalidadeContrato` Literal — invalid → HTTPException 422
  - [ ] 2.3 Passar para `revisar_contrato(...modalidade_override=modalidade_override...)`
- [ ] Task 3: Pipeline kwarg
  - [ ] 3.1 `bloco_workflow/pipeline.py revisar_contrato` signature add kwarg
  - [ ] 3.2 Mutação `parsed.metadata` via `.model_copy(update={"modalidade": modalidade_override})`
  - [ ] 3.3 Audit payload registra `modalidade_override_used: bool` para rastreabilidade
- [ ] Task 4: SPA submitAnalysisReal update
  - [ ] 4.1 FormData add field `modalidade_override` baseado em mapping
  - [ ] 4.2 Pre-submit warning modal se mode não-MVP
- [ ] Task 5: SPA sidebar visual
  - [ ] 5.1 CSS class `.nav-item--mvp-supported` (verde) + `.nav-item--mvp-pending` (amarelo)
  - [ ] 5.2 Aplicar dinamicamente baseado em mapping
- [ ] Task 6: Tests
  - [ ] 6.1 Unit test backend: POST /revisar com modalidade_override válido + inválido + null
  - [ ] 6.2 Unit test pipeline: revisar_contrato com modalidade_override mutation
  - [ ] 6.3 Pytest baseline 248 passed maintained
- [ ] Task 7: Update File List + Change Log
- [ ] Task 8: Self-critique

---

## Dev Notes (Technical Context)

**ModalidadeContrato Literal** (`bloco_contratos/contrato.py:19`):

```python
ModalidadeContrato = Literal[
    "CDC_VEICULOS_PF",  # MVP foco
    "CDC_BENS_PF",
    "CDC_IMOBILIARIO",
    "CARTAO_ROTATIVO",
]
```

**codigos_bacen.yaml** (`bloco_engine/bacen/codigos_bacen.yaml`):

```yaml
taxas_credito_pf:
  CDC_VEICULOS_PF:
    sgs_media_mensal: 25471

nao_implementadas:
  CDC_BENS_PF: motivo: "DP-03 — fora do escopo MVP"
  CDC_IMOBILIARIO: motivo: "DP-03 — taxa SFH/SFI Lei 9.514"
  CARTAO_ROTATIVO: motivo: "DP-03 — Res. CMN 4.549"
```

**Pydantic mutation** (FR-CALC-01 Decimal everywhere + extra="forbid"):

```python
# Após Step 1 parsing
if modalidade_override is not None:
    parsed = parsed.model_copy(
        update={"metadata": parsed.metadata.model_copy(
            update={"modalidade": modalidade_override}
        )}
    )
```

**Sidebar HTML atual** (`static/index.html:995-1029`): 7 nav-items com `data-mode="ccb|veiculo|...|geral"` + `data-crumb` + `data-tooltip`.

**Tooltip expansion** (UX patrocinada Sati Eixo 2 TD-SP04-15): expandir tooltip atual com status MVP suffix:

```
"Cédula de Crédito Bancário (empréstimo/giro). Súmula 472 STJ + MP 2.170-36 + Res. BACEN 4.558/2017.
⚠️ Modalidade em desenvolvimento Sprint 6+ — use Veículo para teste real."
```

---

## Testing

**Unit tests sugeridos:**

```python
# tests/unit/test_modalidade_override.py
def test_post_revisar_with_valid_modalidade_override():
    """POST /revisar com modalidade_override=CDC_VEICULOS_PF → pipeline usa override."""
    ...

def test_post_revisar_with_invalid_modalidade_override():
    """POST /revisar com modalidade_override='INVALID' → 422."""
    ...

def test_pipeline_revisar_contrato_modalidade_override_kwarg():
    """revisar_contrato(modalidade_override=...) overrides parsed.metadata.modalidade."""
    ...
```

**E2E empirical:**

1. Eric clica "Veículo" no sidebar → upload synthetic PDF → audit entry contém `"modalidade": "CDC_VEICULOS_PF"` (explicit)
2. Eric clica "Imobiliário" → upload → SPA bloqueia OR backend 422 → S7 pane

---

## Dev Agent Record

**Agent Model Used:** (vazio — Neo + Aria preenchem)
**Debug Log References:** (vazio)
**Completion Notes List:** (vazio)
**File List:** (vazio)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-05-14 | @sm (River) | Draft inicial Bloco β Sprint 6 AGGRESSIVE |
