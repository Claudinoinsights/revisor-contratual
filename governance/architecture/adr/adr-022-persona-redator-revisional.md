---
type: adr
id: "ADR-022"
title: "Persona Redator Revisional — sabia-7b primary + Qwen 2.5 fallback + hardening anti-hallucination"
status: accepted
adr_level: design
date: "2026-05-14"
domain: "ai-llm-pipeline"
decision_makers: ["@architect (Aria)"]
supersedes: null
superseded_by: null
related_adrs:
  - "ADR-003 Implementação técnica 4 personas (Advogado + Economista + Juiz pattern precedent)"
  - "ADR-010 sabia-q4-mitigation (fallback Qwen 7B + LLM_TIER configurable — pattern leverage)"
  - "ADR-021 dual-content-type POST /revisar (Bloco β base — download flow continuação)"
  - "ADR-014 Provider Abstraction BYOK (multi-tenant LLM future-proof)"
related_stories:
  - "TD-SP06-REDATOR-LLM-01 (Bloco γ pending Niobe)"
  - "TD-SP06-WEASYPRINT-PECA-01 (Bloco γ pending Niobe)"
  - "TD-SP06-DOWNLOAD-ROUTES-01 (Bloco γ pending Niobe)"
  - "TD-SP06-FIDELITY-01 (Bloco γ Oracle compliance pending Niobe)"
related_prds:
  - "PRD-SP06-GAMMA v0.1.0 (FR-PECA-01..07 + NFR-PECA-01..05)"
impacts:
  - "bloco_workflow/pipeline.py — adicionar Step 7 (Redator) + Step 8 (Weasyprint)"
  - "bloco_workflow/personas/ — novo arquivo redator.py (mirror advogado.py pattern)"
  - "bloco_contratos/personas.py — novo schema Pydantic PecaRevisional"
  - "bloco_interface/web/templates/peca/ — novo template inicial-revisional-veiculos.html"
  - "bloco_interface/web/app.py — GET /download/{job_id} novo endpoint"
related_findings:
  - "Smith Fase 7-A F-D1-02 CRITICAL (PDF horrível JS) — backend weasyprint resolve"
  - "Smith Fase 7-A F-D5-26 MEDIUM (weasyprint instalado mas não usado) — Bloco γ usage"
  - "Smith Bloco β F-D3-β-06 MEDIUM (SSE-OWNERSHIP-CHECK) — JOBS[owner] field + /download authz address"
tags:
  - project/revisor-contratual
  - adr
  - sprint-6
  - bloco-gamma
  - persona-redator
  - llm-pipeline
  - oab-compliance
---

# ADR-022 — Persona Redator Revisional

## Status

✅ **Accepted** (2026-05-14) | adr_level: design

## Contexto

PRD-SP06-GAMMA v0.1.0 (Trinity, 2026-05-14) define Sprint 6 Bloco γ objetivo: gerar **peça revisional formal** via persona LLM (não apenas VeredictoJuiz JSON fragments) + render PDF profissional weasyprint + download seguro. Resolve passos 5-6 do fluxo ideal Eric.

**Gap arquitetural** Smith Fase 7-A (2026-05-14) confirmou:
- Backend gera apenas `VeredictoJuiz` JSON (scores C1/C2/C3 + razões) + `TeseAdvogado` text fragment
- **NÃO existe persona "Redator"** que produza peça formal CFOAB Provimento 209/2021
- Rotas `/download/d1` referenciadas (linha 1037 `_format_deliverables_for_c5`) mas **NÃO implementadas**
- `weasyprint v68.1` instalado mas zero código usa

**Contexto LLM existente** (ADR-003 + ADR-010):
- 3 personas operacionais: Advogado (sabia-7b com fallback Qwen ADR-010), Economista (qwen2.5:7b), Juiz (Python puro deterministic)
- LLM_TIER configurable em ADR-010 (lean/balanced/premium)
- Dual-port Ollama: 11434 Advogado, 11435 Economista
- Smith Bloco α F-D1-α-02 MEDIUM: dual-port design parcialmente funcional (apenas 11435 ativo) — TD pendente Sprint 6+

**Restrições MVP** (PRD γ):
- Apenas CDC_VEICULOS_PF target (DP-03)
- Eric advogada externa review BLOQUEANTE pré-commit final (AC-PRD-γ-05)
- LGPD §11 + OAB Provimento 209/2021 compliance NFR-PECA-04 + NFR-PECA-05
- Latency budget <2.5min total Step 7 + 8 (NFR-PECA-02)

## Decisão

**Adotar Opção A: sabia-7b-instruct PRIMARY + Qwen 2.5 7B fallback (pattern ADR-010 leverage) + hardening anti-hallucination via Pydantic strict + vault-restricted citations.**

### Decisões granulares

#### D1. LLM Tier — Single-tier sabia-7b primary

**Escolhido:** Opção A (sabia-7b com fallback Qwen 7B).

**Razão:**
- ADR-010 já estabeleceu padrão sabia-7b + Qwen fallback funcional (Advogado persona). Leverage pattern existente reduz risk técnico.
- Sabia-7b é **Portuguese-trained** (LegalPT + dados jurídicos brasileiros) — natural language jurídico forte essencial para peça CFOAB
- Q4 quantization issues conhecidos ADR-010 mitigados via output validation (Pydantic strict) e fallback Qwen 7B
- Single-tier (não dual concurrent) reduz latency 50% vs Opção C — NFR-PECA-02 <2.5min total fica viável (sabia ~90s + weasyprint ~15s)

**Não escolhido:**
- Opção B (qwen2.5:7b only) — linguajar jurídico genérico, output PT-BR menos natural para CFOAB
- Opção C (dual-tier concurrent sabia + qwen consistency check) — latency dobra (>3min), over-engineering MVP, complica integration

**Tier configurable:** `tier_redator: LLMTier = "balanced"` aceita `lean | balanced | premium` (mirror Advogado). Premium = sabia-7b puro; Balanced = sabia com fallback Qwen; Lean = Qwen apenas (degraded).

#### D2. Prompt Design — Hardening anti-hallucination

**System prompt persona Redator** (skeleton):

```
Você é um advogado bancarista brasileiro com 20 anos de experiência em revisional CDC.
Sua tarefa: redigir uma petição inicial revisional formal conforme OAB Provimento 209/2021 CFOAB.

REGRAS INEGOCIÁVEIS:
1. Cite APENAS Súmulas/Temas STJ presentes na lista JURISPRUDENCIA_VAULT abaixo
2. NUNCA invente Súmulas inexistentes (alucinação = rejeição automática)
3. Estruture peça em 8 seções: Cabeçalho + Qualificação + Fatos + Direito + Pedido + Valor Causa + Fecho + Disclaimer
4. Use linguagem técnica formal brasileira (3ª pessoa, voz passiva quando apropriado)
5. Inclua valor causa numerado + por extenso
6. Disclaimer LGPD/OAB obrigatório no fecho

OUTPUT FORMAT: JSON estrito conforme schema PecaRevisional (extra="forbid" Pydantic).
NÃO gere texto fora do JSON. NÃO use markdown.
```

**Few-shot examples:** Sprint 6 MVP usa **2 templates fictícios** OAB-compliant (criados por Aria + Eric advogada externa review pré-prompt finalização). Sprint 6.1+ build dataset peças reais (Eric advogada workflow).

**Pydantic schema strict** (`bloco_contratos/personas.py`):

```python
class PecaRevisional(BaseModel):
    model_config = ConfigDict(extra="forbid")  # rejeita campos extras alucinados
    cabecalho: str = Field(..., min_length=50, description="Excelentíssimo Sr. Juiz...")
    qualificacao_partes: str = Field(..., min_length=100)
    dos_fatos: str = Field(..., min_length=200)
    do_direito: str = Field(..., min_length=300)
    do_pedido: str = Field(..., min_length=100)
    valor_causa: str = Field(..., pattern=r"R\$\s*[\d.]+,\d{2}")  # formato BR
    valor_causa_extenso: str = Field(..., min_length=10)
    fecho: str = Field(..., min_length=50)
    disclaimer_lgpd_oab: str = Field(..., min_length=200)
    citacoes_jurisprudencia: list[str]  # IDs Súmulas/Temas vault
```

**Validador post-LLM** (`bloco_workflow/personas/redator.py`):

```python
def validar_citacoes_vault(peca: PecaRevisional, vault_docs: list[str]) -> bool:
    """Rejeita peça se cita Súmula/Tema fora do vault.docs_recuperados (R-01 mitigation)."""
    for citacao_id in peca.citacoes_jurisprudencia:
        if citacao_id not in vault_docs:
            raise PecaHallucinationError(
                f"Súmula '{citacao_id}' alucinada (fora vault docs: {vault_docs})"
            )
    return True
```

#### D3. Pipeline Integration — Serial Step 7 + Step 8

**Pipeline sequence** (após Step 6 Juiz):

```
Step 6 (Juiz) → VeredictoJuiz
    ↓ (serial, precisa veredito como input)
Step 7 (Redator LLM) → PecaRevisional | RelatorioInviabilidade
    ↓ (serial, precisa peca dict como input para template render)
Step 8 (Weasyprint) → PDF bytes
    ↓
GET /download/{job_id} retrieve
```

**Filtro veredito** (FR-PECA-07):

```python
if veredito.veredito == "APROVADO_100":
    peca = await redator_invoke(..., template="inicial-revisional-completa")
elif veredito.veredito == "APROVADO_COM_RISCO_HITL":
    peca = await redator_invoke(..., template="inicial-revisional-com-hitl")
elif veredito.veredito == "REJEITADO":
    peca = await redator_invoke(..., template="relatorio-inviabilidade")
```

**Asyncio wrapping:** mesmo padrão ADR-003 Advogado — `await asyncio.to_thread(redator_invoke, ...)` para não bloquear event loop SSE heartbeat.

#### D4. Template HTML — Jinja2 estructurado 8 seções CFOAB

**Localização:** `bloco_interface/web/templates/peca/inicial-revisional-veiculos.html`

**Estrutura:**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>{{ peca.cabecalho|truncate(60) }}</title>
  <style>
    @font-face { font-family: 'Lora'; src: url('/static/fonts/Lora-Regular.ttf'); }
    @font-face { font-family: 'Outfit'; src: url('/static/fonts/Outfit-Regular.ttf'); }
    body { font-family: 'Lora', serif; font-size: 12pt; line-height: 1.6; margin: 25mm; }
    h1, h2 { font-family: 'Outfit', sans-serif; color: var(--peca-primary, #1a1a2e); }
    .secao { margin-bottom: 18pt; page-break-inside: avoid; }
    .disclaimer { font-size: 9pt; color: var(--peca-muted, #6c757d); margin-top: 24pt; border-top: 1pt solid #ddd; padding-top: 12pt; }
    @page { size: A4 portrait; margin: 25mm; @bottom-right { content: counter(page) "/" counter(pages); } }
  </style>
</head>
<body>
  <header><svg>OrSheva7 logo inline</svg></header>
  <section class="secao cabecalho">{{ peca.cabecalho }}</section>
  <section class="secao qualificacao">
    <h2>Da Qualificação das Partes</h2>
    <p>{{ peca.qualificacao_partes }}</p>
  </section>
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

**Tokens OrSheva 7:** inline CSS minimal (não link external — weasyprint render isolated). Cores via CSS variables `--peca-primary` etc.

#### D5. Weasyprint Config

```python
from weasyprint import HTML, CSS
from pathlib import Path

def render_peca_pdf(template_name: str, context: dict, output_path: Path) -> bytes:
    """Render peça PDF via weasyprint + Jinja2 template."""
    from bloco_interface.web.app import templates  # reuso Jinja2 env existente
    rendered_html = templates.get_template(template_name).render(context)
    pdf_bytes = HTML(
        string=rendered_html,
        base_url=str(Path("bloco_interface/web/static").absolute()),  # resolve fontes
    ).write_pdf()
    output_path.write_bytes(pdf_bytes)
    output_path.chmod(0o600)  # LGPD §46
    return pdf_bytes
```

#### D6. Backward Compat Bloco β btnDownload

SPA `static/index.html` btnDownload atual (Bloco β placeholder alert) → Bloco γ substitui por fetch real:

```javascript
document.getElementById('btnDownload').addEventListener('click', async () => {
  if (!lastResult || !lastResult.verdictUrl) return;
  // Bloco γ: GET /download/{job_id} retorna PDF binary
  const jobId = new URL(lastResult.verdictUrl, location.origin).searchParams.get('job_id');
  try {
    const resp = await fetch(`/download/${jobId}`, { credentials: 'same-origin' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
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
    alert(`Erro download peça: ${err.message}`);
  }
});
```

#### D7. SSE-OWNERSHIP-CHECK addressing (Smith Bloco β F-D3-β-06)

**JOBS dict storage extension:**

```python
# bloco_interface/web/app.py POST /revisar
JOBS[job_id] = {
    "status": "queued",
    "owner": request.session.get("user"),  # NEW Bloco γ — ownership tracking
    "pdf_path": pdf_path,
    # ... existing fields
}
```

**Download endpoint authz:**

```python
@app.get("/download/{job_id}")
async def download_peca(request: Request, job_id: str) -> Response:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado")
    if request.session.get("user") != job.get("owner"):
        raise HTTPException(403, "Acesso negado — peça pertence a outro usuário")
    # ... return PDF binary
```

Mesma lógica aplicada em `GET /revisar/stream/{job_id}` (Smith F-D3-β-06 TD address Sprint 6).

## Alternativas Consideradas

### Opção A — sabia-7b primary + Qwen 7B fallback ✅ ESCOLHIDA

| Critério | Avaliação |
|----------|-----------|
| Português jurídico nativo | ✅ Excelente (Portuguese-trained) |
| Latency MVP (<2.5min) | ✅ Viável (~90s LLM + 15s weasyprint) |
| Risk técnico | ✅ Baixo (ADR-010 pattern já validado Advogado) |
| Compatibilidade Ollama dual-port | ✅ Pode usar 11434 (Advogado port idle quando Redator roda) |
| Cost engineering | ✅ Reuso infra existente |

### Opção B — qwen2.5:7b only ❌ REJEITADA

| Critério | Avaliação |
|----------|-----------|
| Português jurídico | ⚠️ Genérico, menos natural CFOAB linguajar |
| Latency | ✅ Levemente mais rápido (~70s) |
| Risk técnico | ✅ Baixo |
| Hallucination jurisprudência | 🔴 Maior risco — não-Portuguese-trained tem maior tendência inventar Súmulas |

**Rejeição:** Quality jurídico > 20s latency. Redator é cara da peça final advogada externa review — usar best Portuguese model disponível.

### Opção C — Dual-tier sabia + qwen consistency check ❌ REJEITADA

| Critério | Avaliação |
|----------|-----------|
| Quality | ✅ Highest (dois LLMs validam consistência) |
| Latency | 🔴 Dobra (>3min) — viola NFR-PECA-02 |
| Complexity integration | 🔴 Alta (dual response parsing + diff logic) |
| Cost engineering | 🔴 Over-engineering MVP |

**Rejeição:** Sprint 6 AGGRESSIVE timeline + MVP scope inviabiliza. Pode ser Sprint 7+ ADR específica se Smith identifica hallucination patterns recorrentes Sprint 6 Bloco γ.

## Consequências

### Positivas ✅

- **DRY pattern reuse:** ADR-010 sabia+Qwen fallback leverage — zero invenção infra
- **Quality jurídico forte:** sabia-7b Portuguese-trained = linguajar CFOAB natural
- **Latency MVP viável:** <2.5min Step 7+8 atende NFR-PECA-02
- **Hardening anti-hallucination:** Pydantic strict + vault-restricted citations + validador post-LLM = 3 camadas defesa contra R-01 (hallucinated Súmulas)
- **Backward compat Bloco β:** btnDownload swap placeholder → fetch real seamless
- **SSE-OWNERSHIP-CHECK addressed:** JOBS[owner] field + 403 authz no /download = Smith F-D3-β-06 resolved
- **Audit chain extension:** `peca_generated` + `pdf_downloaded` HMAC-chained eventos novos

### Negativas ⚠️

- **Single-tier dependência sabia-7b Q4:** se quality output degradar (Q4 quantization issues ADR-010), fallback Qwen 7B é único safety net. Sprint 6+ pode considerar Opção C dual-tier se Smith detecta hallucination patterns sistemáticos
- **Latency Step 7 ~90s** adiciona ~30% tempo total pipeline (visible UX SSE phase-start)
- **Templates HTML inline CSS:** não usa OrSheva 7 tokens.css external — duplicação minor styling logic (mitigado por simplicidade weasyprint render isolated)
- **Few-shot examples MVP fictícios:** Sprint 6 não tem dataset peças reais; Sprint 6.1+ build (Eric advogada workflow); risk minor: quality output Sprint 6 < quality Sprint 6.1+

### Neutras ⚪

- **Persona Redator separada de Advogado:** Advogado persona produz `TeseAdvogado` (texto fragment); Redator produz `PecaRevisional` (estrutura formal CFOAB). Distinção arquitetural clara — Sprint 6+ podem se fundir se Smith identificar redundância
- **Step 8 Weasyprint serial pós-Redator:** acceptable — peça é blocking dependency. Sprint 6+ pode paralelizar render template variants (D1/D2/D3) se Eric advogada review demanda múltiplas variantes
- **GET /download/{job_id} sem rate limit:** Sprint 6 MVP local — sem necessidade. Sprint 7+ produção considerar rate limit (10 req/min per user)

## Implementação — Guia para Neo Bloco γ

### Story TD-SP06-REDATOR-LLM-01

**Arquivos novos:**
- `bloco_workflow/personas/redator.py` (mirror advogado.py pattern)
- `bloco_contratos/personas.py` — add `PecaRevisional` Pydantic model + `RelatorioInviabilidade` + `PecaHallucinationError` exception
- `tests/unit/test_redator_persona.py` — tests com mocks LLM

**Pipeline edit:**
- `bloco_workflow/pipeline.py` — add Step 7 após Juiz (line ~298):

```python
# Step 7 — Redator Revisional (NOVO Bloco γ)
peca: PecaRevisional | RelatorioInviabilidade = await asyncio.to_thread(
    redator_invoke,
    veredito=veredito,
    contrato_meta=parsed.metadata,
    calculo=calculo,
    tese_advogado=tese,
    analise_macro=analise,
    vault_docs=docs,
    tier=tier_redator,
    redator_invoke_fn=redator_invoke_fn,  # DI for tests
)
# Validar citações (anti-hallucination R-01)
if isinstance(peca, PecaRevisional):
    validar_citacoes_vault(peca, [d.id_doc for d in docs])
audit_payload["peca_generated"] = True
audit_payload["peca_format"] = type(peca).__name__
```

### Story TD-SP06-WEASYPRINT-PECA-01

**Arquivos novos:**
- `bloco_interface/web/templates/peca/inicial-revisional-veiculos.html`
- `bloco_interface/web/templates/peca/inicial-revisional-com-hitl.html`
- `bloco_interface/web/templates/peca/relatorio-inviabilidade.html`
- `bloco_engine/pdf/render.py` — função `render_peca_pdf(template, context, output_path)` weasyprint wrapper

**Pipeline edit Step 8:**

```python
# Step 8 — PDF Render Weasyprint (NOVO Bloco γ)
pdf_output_path = DEFAULT_DATA_DIR / "pecas" / f"{job_id}.pdf"
pdf_output_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)  # LGPD
pdf_bytes = await asyncio.to_thread(
    render_peca_pdf,
    template_name=f"peca/{template_variant}.html",
    context={"peca": peca, "contrato": parsed.metadata, "veredito": veredito},
    output_path=pdf_output_path,
)
audit_payload["peca_pdf_hash"] = hashlib.sha256(pdf_bytes).hexdigest()
audit_payload["peca_pdf_size_bytes"] = len(pdf_bytes)
JOBS[job_id]["peca_pdf_path"] = str(pdf_output_path)
```

### Story TD-SP06-DOWNLOAD-ROUTES-01

**Edits app.py:**

```python
@app.get("/download/{job_id}")
async def download_peca(request: Request, job_id: str) -> Response:
    """Download peça revisional PDF — authenticated + ownership + audit."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado")
    user = request.session.get("user")
    if not user or user != job.get("owner"):
        raise HTTPException(403, "Acesso negado")
    pdf_path_str = job.get("peca_pdf_path")
    if not pdf_path_str or not Path(pdf_path_str).exists():
        raise HTTPException(404, "Peça PDF ainda não gerada — aguarde pipeline complete")
    pdf_path = Path(pdf_path_str)
    pdf_bytes = pdf_path.read_bytes()
    # Audit entry pdf_downloaded
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

### Story TD-SP06-FIDELITY-01

**Oracle compliance scope:**
- Verificar 3 PDFs gerados (APROVADO_100 + APROVADO_COM_RISCO_HITL + REJEITADO) atendem AC-PRD-γ-03 (8 seções CFOAB embedded + disclaimer + valor causa formatado)
- Validar AC-PRD-γ-05 advogada externa review process (documento `governance/legal/advogada-review-peca-revisional-2026-05-XX.md` BLOQUEANTE pré-commit)
- Smoke test FR-PECA-05 traceability (citações Súmulas todas em vault.docs_recuperados)

## Histórico

| Data | Mudança | Autor |
|------|---------|-------|
| 2026-05-14 | Criação ADR — Persona Redator Revisional sabia-7b primary + Qwen fallback + 3-layer anti-hallucination defense | @architect (Aria) |

## Referências

- [PRD-SP06-GAMMA v0.1.0](../../prd/prd-sp06-bloco-gamma-peca-revisional-ai-v0.1.0.md) — requisitos source
- [ADR-003 Implementação 4 personas](./adr-003-implementacao-tecnica-4-personas.md) — pattern precedent
- [ADR-010 Sabia Q4 mitigation](./adr-010-sabia-q4-mitigation.md) — fallback Qwen pattern
- [ADR-021 Dual content-type](./adr-021-dual-content-type-post-revisar.md) — download flow continuação
- [Smith Bloco α CONTAINED](../../qa/smith-review-bloco-alpha-pos-execution-2026-05-14.md) — pipeline real base
- [Smith Bloco β CONTAINED](../../qa/smith-review-bloco-beta-pos-execution-2026-05-14.md) — F-D3-β-06 SSE-OWNERSHIP-CHECK origem

---

*— Aria, arquitetando o futuro 🏗️*
*"Sétima persona desenhada. sabia-7b empresta voz portuguesa. Qwen 7B vigia em fallback. Três camadas anti-hallucination — pydantic strict, vault-restricted citations, validador post-LLM. Niobe escreve as ondas, Neo constrói. Bloco γ ganha forma."*
