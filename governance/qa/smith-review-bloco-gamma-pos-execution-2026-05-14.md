---
type: smith-adversarial-review
title: "Smith Adversarial Review — Bloco γ Post-Execution Final Pre-Merge Consolidated"
agent: "@smith (Smith)"
date: "2026-05-14"
project: revisor-contratual-staging
sprint: "6.x AGGRESSIVE Bloco γ"
methodology: "v5 functional smoke probe + ultrathink"
stories_reviewed:
  - "TD-SP06-REDATOR-LLM-01"
  - "TD-SP06-WEASYPRINT-PECA-01"
  - "TD-SP06-DOWNLOAD-ROUTES-01"
  - "TD-SP06-FIDELITY-01"
verdict_global: "CONTAINED"
findings_total: 12
findings_by_severity:
  CRITICAL: 0
  HIGH: 2
  MEDIUM: 5
  LOW: 4
  NOTE: 1
tags:
  - project/revisor-contratual
  - smith-review
  - sprint-6
  - bloco-gamma
  - adversarial-review
  - post-execution
  - methodology-v5
---

# Smith Adversarial Review — Bloco γ Post-Execution Final Pre-Merge Consolidated

> *"Quatro stories. Três agentes felicitando-se. Pytest verde. Oracle declarou PASS. Sr. Anderson, vou mostrar o que vocês decidiram não enxergar."*

---

## Verdict Global: **CONTAINED**

> *"Talvez vocês não sejam tão incapazes quanto eu temia. CONTAINED — entrega aceitável com ressalvas. 2 HIGH exigem atenção pré-launch v0.2.0; 5 MEDIUM são tech debt aceitável Sprint 6.1+; 4 LOW são refinamentos. ZERO CRITICAL — não há sangue desta vez."*

**Resumo numérico:**

| Severity | Count | Action |
|----------|-------|--------|
| CRITICAL | **0** | — |
| HIGH | **2** | Remediation antes de v0.2.0 commit (não bloqueia merge Bloco γ; Sprint 6.0.1 hotfix candidato) |
| MEDIUM | **5** | Tech debt cataloged Sprint 6.1+ |
| LOW | **4** | Refinamentos pós-MVP |
| NOTE | **1** | Inconsistência documental ADR vs implementation |

---

## CI Status Verification (quality-gate-enforcement.md MUST)

| Check | Resultado | Evidência |
|-------|-----------|-----------|
| **gh pr checks** | N/A — não há PR aberto na branch `main` | `git status --short` confirma working tree modified mas sem PR remoto |
| **Pytest local re-execução** | ✅ **477 passed + 5 skipped** em 48.19s | Smith re-rodou `py -3.14 -m pytest tests/unit/ -o addopts="" --tb=line -q` em ambiente próprio |
| **Baseline regressão** | ✅ ZERO regressões | Sentinel 248 → 477 preservado; 5 skipped legítimos (TD-SP06-WEASYPRINT-WIN-GTK-DEPS) |
| **Override documentado** | N/A — não aplicável (pytest local executado) | — |

CI Status MUST satisfeito. *"Os números estão honestos. Pelo menos isso."*

---

## Adversarial Findings (12 identificados — methodology v5)

### 🟠 HIGH — 2 findings (remediation antes v0.2.0)

#### F-γ-01 HIGH — Audit silent failure em /download permite LGPD §46 trail gap

**Localização:** [`bloco_interface/web/app.py:917-936`](bloco_interface/web/app.py#L917-L936)

**Problema:** O endpoint `GET /download/{job_id}` envolve `append_audit_entry("pdf_downloaded", ...)` em `try/except Exception` que apenas faz `logger.error()` — o download de PDF prossegue mesmo se audit chain HMAC falhar (corruption, IOError, permission denied).

```python
try:
    append_audit_entry("pdf_downloaded", {...}, audit_path=DEFAULT_AUDIT_PATH)
except Exception as audit_exc:  # noqa: BLE001
    logging.getLogger(__name__).error(...)  # ← Download continua mesmo sem trail
return Response(content=pdf_bytes, ...)
```

**Por que importa:** Peça revisional contém dados pessoais sensíveis LGPD (CPF, qualificação, contrato). Art. 46 LGPD exige rastreabilidade de quem acessou. Audit failure silenciosa = violação de compliance em produção.

**Distinção vs CC.39 pattern:** CC.39 estabeleceu try/except em pipeline.py para PRESERVAR exceção original (not lose error). Aqui é diferente — o handler está em operação user-facing, e audit failure é o ÚNICO trail LGPD. Não há "exceção original" a preservar.

**Como corrigir:**
1. Audit-first pattern: chamar `append_audit_entry` ANTES de `return Response`. Se falhar, raise HTTPException 503 "Trail LGPD indisponível — tente novamente".
2. OU: monitoring/alerting obrigatório em logger.error("audit pdf_downloaded falhou") — não pode passar despercebido em prod.
3. Sprint 6.0.1 hotfix recomendado pré-launch v0.2.0.

---

#### F-γ-02 HIGH — `audit_payload["redator_persona_used"]` registra string misleading

**Localização:** [`bloco_workflow/pipeline.py:377`](bloco_workflow/pipeline.py#L377)

**Problema:** Pipeline registra:

```python
audit_payload["redator_persona_used"] = f"sabia-or-qwen-tier-{tier_redator}"
```

A string "sabia-or-qwen" sugere fallback dinâmico (sabia primary + qwen fallback). **A implementação NÃO TEM fallback chain** (ver F-γ-03). Audit chain integrity comprometida — registra capability promised, não actual model used.

**Por que importa:** Audit forense pós-incident (ex: hallucinated Súmula, advogada externa flag) precisa identificar EXATAMENTE qual modelo gerou o output. "sabia-or-qwen-tier-balanced" é não-determinístico em interpretação.

**Como corrigir:**
1. Capture actual model usado: `audit_payload["redator_persona_used"] = llm.model` (acessar via `_default_invoke` retornando metadata).
2. OU: hardcoded mapping via `TIER_TO_MODEL_ADVOGADO[tier_redator]` que é a fonte da verdade ATUAL (sem fallback claim).
3. Sprint 6.0.1 hotfix recomendado.

---

### 🟡 MEDIUM — 5 findings (tech debt Sprint 6.1+)

#### F-γ-03 MEDIUM — Qwen fallback NÃO implementado em redator._default_invoke

**Localização:** [`bloco_workflow/personas/redator.py:212-219`](bloco_workflow/personas/redator.py#L212-L219)

**Problema:** Docstring redator.py linha 6 promete: "balanced=qwen+sabia fallback". ADR-022 D1 promete: "sabia-7b primary + Qwen 2.5 fallback (ADR-010 pattern leverage)". A implementação:

```python
async def _default_invoke(prompt: str, tier: LLMTier) -> str:
    llm = get_advogado_llm(tier=tier)  # ← Único modelo, sem try/except + retry
    response = await llm.ainvoke(prompt)
    ...
```

`get_advogado_llm()` mapeia tier → 1 modelo único via `TIER_TO_MODEL_ADVOGADO[tier]`. **Zero fallback logic.** Se sabia-7b travar/lentar/falhar, Qwen NÃO é chamado.

**Por que importa:** ADR-010 mitigation (Sabia Q4 quality) só funciona se fallback existe. Sem fallback, sistema produção fica refém de uma instância LLM.

**Como corrigir (Sprint 6.1):**
1. Adicionar try/except em `_default_invoke` com Qwen fallback explicit no tier `balanced`.
2. OU patch ADR-022 D1 para remover claim "fallback" se decisão é tier mapping puro.

---

#### F-γ-04 MEDIUM — Layer 3 anti-hallucination AUSENTE em redator.py

**Localização:** [`bloco_workflow/personas/redator.py:251-279`](bloco_workflow/personas/redator.py#L251-L279) + ADR-022 D2

**Problema:** ADR-022 D2 promete 3 camadas:
1. Pydantic strict — ✅ Layer 1 (`extra="forbid"`)
2. Vault-restricted citations — ✅ Layer 2 (`validar_citacoes_vault`)
3. **Validador post-LLM — ❌ AUSENTE em redator.py**

Docstring `Raises:` linha 250-252 lista apenas `PecaHallucinationError` (Layer 2) e `ValidationError` (Layer 1). Nenhuma menção a Layer 3.

**Counter-argumento parcial:** Regex `valor_causa` pattern `R\$\s*[\d.]+,\d{2}` via Pydantic field validator é tecnicamente um "post-LLM check" — mas tecnicamente é Layer 1 (Pydantic). ADR-022 distinguia.

**Por que importa:** Hardening 3-camadas é "defense in depth". 2 camadas sem terceira = sistema mais frágil que claim.

**Como corrigir (Sprint 6.1):**
1. Implementar Layer 3 distinct: post-validation funcional além do Pydantic (ex: NLI híbrido ADR-004 pattern aplicado a citações_textual nos fundamentos_invocados — verificar se citação realmente afirma o que peça diz que afirma).
2. OU patch ADR-022 D2 para colapsar 3 camadas em 2 (Pydantic + vault) reconhecendo realidade.

---

#### F-γ-05 MEDIUM — ADR-022 D4 desalinhado com implementação (Lora/Outfit vs Manrope/Fraunces)

**Localização:** [`governance/architecture/adr/adr-022-persona-redator-revisional.md` linhas 186-189](governance/architecture/adr/adr-022-persona-redator-revisional.md#L186-L189) vs templates `peca/*.html`

**Problema:** ADR-022 D4 ainda especifica:
```css
'Lora'; src: url('/static/fonts/Lora-Regular.ttf');
'Outfit'; src: url('/static/fonts/Outfit-Regular.ttf');
'Lora', serif; (corpo)
'Outfit', sans-serif; (h1, h2)
color: var(--peca-primary, #1a1a2e);
```

Implementação Neo Wave γ.1 usa Manrope (sans/UI) + Fraunces (serif/display) + Or-500 `#EE6B20` — alinhado ao brandbook OrSheva 7 real (que Neo identificou como fonte da verdade).

**Por que importa:** ADR vivo deve refletir reality (`prd-governance.md` + `adr-governance.md` MUST atualização pós-implementation). Future agents lendo ADR-022 D4 vão construir expectativas erradas.

**Como corrigir (Sprint 6.0.1 ou Sprint 6.1):**
1. PATCH ADR-022 D4: substituir Lora/Outfit por Manrope/Fraunces + Or-500 + commentário "decisão Neo Wave γ.1 — brandbook OrSheva 7 v1.1.2 real".
2. Adicionar entry "Change Log" no ADR-022 com data + autor + razão.

---

#### F-γ-06 MEDIUM — pipeline.py Step 8 sem graceful degradation weasyprint render failure

**Localização:** [`bloco_workflow/pipeline.py:407-438`](bloco_workflow/pipeline.py#L407-L438)

**Problema:** Step 8 weasyprint render NÃO tem try/except específico. Se `render_peca_pdf()` falhar (template not found, GTK runtime ausente, filesystem permission, malformed HTML), exceção propaga ao `except Exception` global linha 331+. Pipeline INTEIRO falha com status FAILED — incluindo a peça LLM REAL gerada com sucesso no Step 7.

**Por que importa:** Step 7 Redator pode levar ~30s-2min (LLM inference). Step 8 falha = perde tudo. Production VPS Linux deve ter GTK libs OK mas edge cases (disk full, permission revoked) podem ocorrer.

**Como corrigir (Sprint 6.1):**
1. Wrap Step 8 em try/except local — se falhar, registrar `audit_payload["peca_pdf_generated"] = False` + reason, mas marcar pipeline status SUCCESS para peca LLM real preservada.
2. UI pode permitir re-tentar render via novo endpoint `/regenerar-pdf/{job_id}`.

---

#### F-γ-07 MEDIUM — pdf_filename collision risk (deterministic contract_hash[:16])

**Localização:** [`bloco_workflow/pipeline.py:396`](bloco_workflow/pipeline.py#L396)

**Problema:**

```python
pdf_filename = f"{parsed.metadata.contract_hash[:16]}.pdf"
pdf_output_path = peca_output_dir / pdf_filename
```

`contract_hash` é SHA256 do PDF content. Determinístico → mesmo PDF upload por 2 users diferentes produz mesmo `pdf_filename` → segundo job sobrescreve PDF do primeiro → ownership ambiguity (JOBS[job_id_A] e JOBS[job_id_B] apontam ao mesmo `peca_pdf_path` mas com owners diferentes).

**Cenário concreto:** Escritório SaaS multi-user → 2 advogados sobem mesmo PDF (cliente comum, contrato compartilhado) → race condition + audit chain confusion.

**Por que importa:** Multi-tenancy SaaS rompido. SHA256 do CONTRATO ≠ ID único de JOB.

**Como corrigir (Sprint 6.1):**
1. `pdf_filename = f"{job_id}.pdf"` (job_id UUID é único por execução).
2. OU `pdf_filename = f"{job_id[:8]}-{contract_hash[:8]}.pdf"` para preservar contract_hash audit trail.

---

### 🟢 LOW — 4 findings (Sprint 6.1+ refinements)

#### F-γ-08 LOW — 401 Response sem `WWW-Authenticate` header em /download

Clientes HTTP standard (curl, requests Python) não saberão auto-prompt re-autenticação. UX SPA já redireciona /classic mas APIs/CLI consumers ficam orphan.

**Fix:** `Response(status_code=401, headers={"WWW-Authenticate": "Session"}, ...)`.

#### F-γ-09 LOW — 404 cascade colapsa 3 conditions distintas

`/download/{job_id}` retorna 404 para: (a) job não existe, (b) PDF não gerado, (c) file removido. Audit forense fica imprecisa — qual situação real?

**Fix:** Detail messages distintas + audit log entry diferenciada (cada caso = entry type específica).

#### F-γ-10 LOW — `pdf_bytes = pdf_path.read_bytes()` sem size limit

DoS potential: PDF malicioso 1GB exhausting memory. peca outputs reais são <1MB mas attacker pode forçar via filesystem.

**Fix:** `if pdf_path.stat().st_size > MAX_PDF_BYTES: raise HTTPException(413)`.

#### F-γ-11 LOW — Oracle smoke fixtures coverage incompleta

APROVADO_100 + COM_HITL fixtures citam mesmas Súmulas (STJ-S539 + STJ-S472). Vault docs hardcoded list tem 5 docs, fixtures usam 2. Regex `valor_causa` edge cases (3 decimais, sem extenso, etc) não probados.

**Fix:** Sprint 6.1 expandir smoke fixtures com diversity matrix.

---

### 📝 NOTE — 1 finding

#### F-γ-12 NOTE — JOBS dict in-memory sem persistence (pre-existing pattern agravado por Bloco γ)

JOBS dict global em-memória. Restart app → JOBS perdido → mesmo com PDF físico em filesystem, btnDownload retorna 404 "job não encontrado". Pre-existing pattern Bloco β; Bloco γ adicionou `peca_pdf_path` ao mesmo lugar → mesma vulnerabilidade amplificada.

**Não é finding novo do Bloco γ.** Catalogado como NOTE para Smith β reference. TD-SPRINT-7-JOBS-PERSISTENCE recomendado (Redis OR sqlite OR file-backed dict).

---

## Constitution Compliance

| Artigo | Status | Notas |
|--------|--------|-------|
| **Art. III** Story-Driven Development | ✅ PASS | 4 stories Ready for Review com ACs traceadas; cada implementação documentada em File List + Change Log |
| **Art. IV** No Invention | ⚠️ PASS COM RESSALVA | Implementação rastreável a PRD-SP06-GAMMA + ADR-022 + Smith β findings. **EXCEÇÃO:** F-γ-05 ADR-022 D4 desalinhado — fontes Manrope/Fraunces foi decisão Neo NÃO refletida no ADR. Não é "invenção" (brandbook real existe), mas é gap processo. |
| **Art. V** Quality First | ✅ PASS | Pytest 477 PASS + 5 skip ZERO regressão; hardening 3-camadas claim parcialmente cumprido (F-γ-04 Layer 3 ausente — não bloqueante) |

---

## Methodology v5 — Functional Smoke Probe

Smith executou empíricamente:

1. **Git status inspection** ✅ — 10 modified + N untracked files identificados
2. **Pytest baseline re-execution** ✅ — 477 PASS + 5 skipped local em ambiente Smith fresh
3. **Source code adversarial reading** ✅:
   - `bloco_workflow/personas/redator.py` linhas 200-279 — Layer 3 ausência + fallback ausência confirmados
   - `bloco_interface/web/app.py` linhas 895-944 — audit silent failure + 404 cascade collapse confirmados
   - `bloco_workflow/pipeline.py` linhas 340-438 — Step 7+8 error handling gap + pdf_filename collision confirmados
   - `governance/architecture/adr/adr-022-persona-redator-revisional.md` linhas 186-189 — fonte desalinhada confirmada
4. **CI status check** ✅ — `gh pr checks` N/A (sem PR), pytest local satisfaz MUST quality-gate-enforcement.md

---

## Recomendações Smith por agente

| Agente | Findings sob responsabilidade | Ação Sprint 6.0.1 / 6.1 |
|--------|------------------------------|--------------------------|
| @dev (Neo) | F-γ-01 audit silent, F-γ-02 misleading audit field, F-γ-06 Step 8 graceful, F-γ-07 pdf collision | Sprint 6.0.1 hotfix HIGH; Sprint 6.1 patches MEDIUM |
| @architect (Aria) | F-γ-04 Layer 3 ausente, F-γ-05 ADR-022 D4 fonts mismatch | Sprint 6.0.1 patch ADR-022 D2+D4 |
| @qa (Oracle) | F-γ-11 fixtures coverage | Sprint 6.1 expandir smoke |
| @dev (Neo) — Sprint 7+ | F-γ-08 WWW-Authenticate, F-γ-09 404 cascade, F-γ-10 size limit, F-γ-12 JOBS persistence | Sprint 7 polish |

---

## Verdict Final

> **CONTAINED — entrega aceitável com ressalvas.**
>
> *"Sr. Anderson, dessa vez vocês surpreenderam-me. Não bom o suficiente para CLEAN — nunca é — mas digno de CONTAINED. 2 HIGH precisam de hotfix antes do v0.2.0 commit, mas o esqueleto está sólido. Pytest verde, audit chain mostly íntegra, Constitution Art. III/V satisfeitos."*
>
> *"Sigam adiante. Mas saibam que estarei observando."*

**Próximo passo:** @claudino (Claudino) Skill orchestrar Bloco δ closure:
1. Decision point Eric: hotfix 2 HIGH AGORA vs cataloged como Sprint 6.0.1 pré-launch (não bloqueia merge Bloco γ)
2. Eric advogada externa review BLOQUEANTE persiste (AC-PRD-γ-05 process externo)
3. Commit v0.2.0 sequence (Operator push se decisão for commit-now)
4. Eric demo + cleanup governance docs final
5. CHECKPOINT update + handoff Smith → Bloco δ closure final

---

**Veredito assinado:** @smith (Smith) — 2026-05-14
**Methodology:** v5 functional smoke probe + ultrathink
**Findings:** 12 (0 CRIT / 2 HIGH / 5 MED / 4 LOW / 1 NOTE)
**Status pytest baseline:** 477 PASS + 5 skip ZERO regressão (re-verificado por Smith)

*— Smith. É inevitável. Mas dessa vez, contável. 🕶️*
