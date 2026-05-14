---
type: prd
id: "PRD-SP06-GAMMA"
title: "Peça Revisional AI + PDF Backend — Sprint 6 Bloco γ"
version: "0.1.0"
status: DRAFT
last_updated: "2026-05-14"
sprint: "6.x AGGRESSIVE Bloco γ"
audience:
  - "Advogados revisores (DEVEDOR final user)"
  - "Eric Claudino (Orsheva founder — supervisão release SaaS)"
  - "Advogada externa Eric (review OAB compliance — BLOQUEANTE pré-commit final)"
goal: "Resolver passos 5-6 do fluxo ideal Eric — backend gera peça revisional juridicamente válida via persona LLM Redator + PDF profissional weasyprint + download routes seguros"
mvp_scope: "CDC_VEICULOS_PF only (DP-03 — demais modalidades Sprint 6+ ADRs específicas)"
decision_makers:
  - "@pm (Trinity)"
  - "@architect (Aria)"
  - "Eric Claudino (final approval)"
  - "Advogada externa Eric (review OAB compliance)"
related_adrs:
  - "ADR-021 dual-content-type POST /revisar (Bloco β base)"
  - "ADR-022 Persona Redator Revisional (Bloco γ — PENDING Aria)"
  - "ADR-003 Implementação técnica 4 personas (precedent — Advogado, Economista, Juiz)"
  - "ADR-010 sabia-q4-mitigation (LLM tier configurable)"
related_stories:
  - "TD-SP06-REDATOR-LLM-01 (Bloco γ — pending Niobe)"
  - "TD-SP06-WEASYPRINT-PECA-01 (Bloco γ — pending Niobe)"
  - "TD-SP06-DOWNLOAD-ROUTES-01 (Bloco γ — pending Niobe)"
  - "TD-SP06-FIDELITY-01 (Bloco γ — Oracle compliance — pending Niobe)"
related_findings:
  - "Smith Fase 7-A F-D1-02 CRITICAL: index.html:2065 buildPdf JS puro (PDF horrível) — Bloco β REMOVED, Bloco γ replace com backend weasyprint"
  - "Smith Fase 7-A F-D5-26 MEDIUM: weasyprint v68.1 instalado mas nenhum código usa — Bloco γ resolve"
  - "Smith Fase 7-A backend só gera VeredictoJuiz JSON — petição revisional AI MISSING"
tags:
  - project/revisor-contratual
  - prd
  - sprint-6
  - bloco-gamma
  - peca-revisional-ai
  - pdf-backend
  - mvp-cdc-veiculos-pf
---

# PRD Sprint 6 Bloco γ — Peça Revisional AI + PDF Backend

## Visão

### Problema

Pipeline atual (Bloco α+β) processa contratos bancários CDC veículos PF e gera `VeredictoJuiz` (scores C1/C2/C3 + aderência + razões) + fragments LLM (`TeseAdvogado` + `AnaliseMacroEconomica`). Output é JSON estruturado — **insumo técnico**, não peça processual pronta.

Advogado revisor (DEVEDOR final user) ainda precisa:

1. Ler fragments JSON
2. Redigir peça inicial revisional manualmente
3. Formatar conforme OAB Provimento 209/2021 CFOAB
4. Citar jurisprudência STJ extraída do vault
5. Calcular valor da causa baseado em `diferenca_anatocismo`
6. Imprimir/exportar PDF profissional

**Gap arquitetural identificado:** Smith Fase 7-A (2026-05-14) confirmou empírico — backend **NÃO gera peça revisional formal**. Rotas `/download/d1` + `/download/d2` + `/download/d3` referenciadas em `_format_deliverables_for_c5` (linha 1037+) mas **NÃO implementadas**. `weasyprint v68.1` instalado mas zero código usa.

### Audience

| Persona | Necessidade |
|---------|-------------|
| **Advogado revisor (DEVEDOR final)** | Receber peça revisional pronta para revisão + submissão ao juízo competente |
| **Eric Claudino (Orsheva founder)** | Validar qualidade peça antes release v0.3.0 público |
| **Advogada externa Eric** | Review OAB compliance + ética profissional |

### Value Proposition

Reduzir tempo elaboração peça revisional de **~3-8 horas** (manual) para **~10-15 minutos** (review + ajustes IA-gerada). Eliminar erros recorrentes em peças genéricas (citações incorretas Súmulas, valor causa mal calculado, cabeçalho fora padrão CFOAB).

---

## User Stories

### US-PECA-01: Geração automática peça revisional via AI

**Como** advogado revisor recebendo análise APROVADO_100 do Juiz Python,
**Eu quero** que o backend gere automaticamente uma petição inicial revisional formal via persona LLM "Redator Revisional",
**Para que** eu tenha um documento jurídico pronto para revisão (não fragments JSON soltos), pronto para customização final + submissão judicial.

### US-PECA-02: Download PDF profissional formatado

**Como** advogado revisor após pipeline complete,
**Eu quero** baixar a peça revisional como PDF profissional formatado (cabeçalho OrSheva 7 + tipografia Lora/Outfit + estrutura CFOAB),
**Para que** eu possa imprimir, customizar ou submeter ao juízo competente sem retrabalho de formatação.

### US-PECA-03: Citações jurisprudência traceable

**Como** advogado revisor citando Súmulas STJ + Temas Repetitivos,
**Eu quero** que cada citação na peça gerada referencie diretamente os documentos do Vault (STJ-S541, STJ-S382, STF-SV7, etc) usados pelo Advogado LLM,
**Para que** eu posso validar fundamentação jurídica antes assinar peça (auditabilidade jurisprudencial).

### US-PECA-04: Filtro veredito — REJEITADO gera Relatório, não peça

**Como** advogado revisor recebendo análise REJEITADO (aderência < 70%),
**Eu quero** que o backend gere um "Relatório de Inviabilidade" (não petição),
**Para que** eu evite gastar tempo customizando peças com fundamentação fraca + proteja meu cliente de litigância de má-fé.

### US-PECA-05: Audit chain + LGPD compliance

**Como** Eric Claudino supervisionando release SaaS,
**Eu quero** que cada PDF download seja registrado em audit.jsonl HMAC chain + temp files chmod 600 + retention 90 dias,
**Para que** eu cumpra LGPD §11 + auditabilidade técnica + rastreabilidade incidentes.

---

## Functional Requirements

### FR-PECA-01 — Persona Redator LLM gera peça formato OAB

Pipeline existente termina com `VeredictoJuiz`. **NOVO Step 7:** Persona Redator (LLM) recebe `VeredictoJuiz + ContratoMetadata + ResultadoCalculo + TeseAdvogado + AnaliseMacroEconomica + jurisprudência docs` e gera peça revisional formal estruturada em **8 seções CFOAB Provimento 209/2021**:

1. **Cabeçalho** (Excelentíssimo Sr. Juiz de Direito da X Vara Cível da Comarca de [UF/Comarca])
2. **Qualificação das Partes** (Autor [DEVEDOR placeholder] vs Réu [CREDOR extraído de ContratoMetadata])
3. **Dos Fatos** (modalidade + valor + parcelas + data assinatura + contrato_hash)
4. **Do Direito** (anatocismo classificado + Súmulas aplicáveis + Tese Advogado LLM)
5. **Do Pedido** (revisão contratual + restituição valores indevidos + tutela antecipada se aderência >= 90%)
6. **Valor da Causa** (diferenca_anatocismo × n_parcelas, formatado R$ X.XXX,XX por extenso)
7. **Fecho** (cidade + UF + data atual + assinatura placeholder advogado OAB nº [TO BE FILLED])
8. **Disclaimer LGPD/OAB** (IA não substitui responsabilidade técnica do(a) advogado(a))

### FR-PECA-02 — Templates HTML peça por modalidade (MVP: CDC_VEICULOS_PF)

Template Jinja2 + HTML estruturado em `bloco_interface/web/templates/peca/inicial-revisional-veiculos.html`. Tokens design OrSheva 7 (cores + tipografia) via CSS `<style>` block ou link external `tokens.css`. Modalidades não-MVP (CDC_BENS_PF, CDC_IMOBILIARIO, CARTAO_ROTATIVO) ficam Sprint 6+ ADRs específicas.

### FR-PECA-03 — Validação OAB compliance pré-render

Antes weasyprint render, backend valida campos obrigatórios:
- UF + Comarca não-vazios
- Valor financiado > 0
- Data assinatura válida
- Pelo menos 1 jurisprudência citada
- Disclaimer LGPD/OAB embedded

Se inválido → 422 + diagnostic claro + audit entry `peca_validation_failed`.

### FR-PECA-04 — Weasyprint render OrSheva 7

Backend renderiza PDF via `weasyprint.HTML(template_rendered).write_pdf()` com:
- Fontes self-hosted Lora + Outfit (REV-INT-02 LGPD §46)
- A4 portrait, margins 25mm
- Header + footer com numeração pages
- Quebra automática páginas longas
- Tipografia OrSheva 7 (tokens.css)

### FR-PECA-05 — Citações jurisprudência traceable

Cada Súmula/Tema STJ citado na peça gerada vincula a `audit_payload["vault"]["docs_recuperados"]` (lista IDs). Backend cross-reference `bloco_vault.busca_hibrida` retorno + `TeseAdvogado.fundamentos_invocados` → embutir citações ABNT na seção "Do Direito".

### FR-PECA-06 — Download endpoint authenticated + audit + chmod 600

**NOVO endpoint:** `GET /download/{job_id}` retorna PDF binary:
- Auth required (session cookie httpOnly + verificação `JOBS[job_id]["owner"]` — addressing TD-SP06-SSE-OWNERSHIP-CHECK Smith finding)
- Content-Type: application/pdf
- Content-Disposition: attachment; filename=peca-revisional-{job_id}.pdf
- File temp chmod 0o600 (LGPD §46) + auto-delete pós-download
- Audit entry `pdf_downloaded` HMAC-chained

### FR-PECA-07 — Filtro veredito (Aprovado vs Rejeitado)

Backend filtra por `VeredictoJuiz.veredito`:
- `APROVADO_100` → peça revisional completa (8 seções FR-PECA-01)
- `APROVADO_COM_RISCO_HITL` → peça revisional + seção adicional "Pontos de Atenção" listando riscos
- `REJEITADO` → "Relatório de Inviabilidade" (template separado — NÃO petição) com análise técnica + recomendação não-protocolar

---

## Non-Functional Requirements

### NFR-PECA-01 — LLM Redator tier

Aria ADR-022 decide entre:
- Opção A: sabia-7b-instruct (Português-trained — natural language jurídico)
- Opção B: qwen2.5:7b (genérico mas estável)
- Opção C: dual-tier (sabia + qwen consistency check — análogo ADR-003 Advogado+Economista paralelo)

NFR mínimo: tier MVP support latency <60s per generation (single peça ~3-5 minutos LLM inference acceptable).

### NFR-PECA-02 — Render PDF latency

Weasyprint render single-page peça revisional típica <30s. Multi-page (>5 páginas — peças longas com extensive jurisprudence) <60s. Total Step 7 + Step 8: <90s adicionais ao pipeline existente (total Bloco α+β+γ: <5min).

### NFR-PECA-03 — PDF size

Output PDF <2MB (fontes referenciadas externally OR embedded subset). Sem imagens raster (apenas SVG OrSheva 7 logo header).

### NFR-PECA-04 — LGPD §11 compliance

- Dados cliente (devedor nome + CPF + endereço) tratados como PII
- Temp files chmod 0o600 + auto-delete pós-download (não persistir > 90 dias)
- Audit chain HMAC registra **hash SHA256 do PDF gerado** (não conteúdo cleartext)
- Retention policy documentada em LGPD §46 disclaimer

### NFR-PECA-05 — OAB ethics

Disclaimer obrigatório embedded toda peça:

> "Este documento é insumo técnico-jurídico gerado por inteligência artificial via Revisor Contratual SaaS BYOK. A IA NÃO substitui a responsabilidade técnica do(a) advogado(a) habilitado(a) que assinará e protocolará a peça. Revisão jurídica humana é obrigatória antes de qualquer submissão judicial. Conformidade: OAB Provimento 209/2021 + Resolução CFOAB ética IA jurídica."

---

## Acceptance Criteria Globais

### AC-PRD-γ-01 — Pipeline end-to-end com Step 7+8

Eric upload PDF veículo synthetic → SPA → POST /revisar Accept JSON → audit entry SUCCESS com novas keys:
- `peca_generated: true`
- `peca_format: "inicial_revisional_veiculos"`
- `peca_pdf_hash: "<sha256>"`
- `redator_persona_used: "<sabia-7b OR qwen2.5 conforme ADR-022>"`

### AC-PRD-γ-02 — Download endpoint funcional

GET /download/{job_id} authenticated → 200 + Content-Type application/pdf + Content-Disposition attachment + arquivo válido weasyprint-generated.

### AC-PRD-γ-03 — Validação OAB compliance pré-render

PDF gerado contém todas 8 seções FR-PECA-01 + disclaimer LGPD/OAB embedded + valor causa formatado correto + UF + comarca corretos + jurisprudência citada inline.

### AC-PRD-γ-04 — Filtro veredito funcional

3 smoke tests:
- Veredito APROVADO_100 → peça revisional completa gerada
- Veredito APROVADO_COM_RISCO_HITL → peça com seção "Pontos de Atenção"
- Veredito REJEITADO → "Relatório de Inviabilidade" (NÃO petição)

### AC-PRD-γ-05 — Eric advogada externa review BLOQUEANTE

Antes commit final Sprint 6 v0.2.0 — Eric advogada externa lê 3 peças geradas (3 PDFs reais smoke) + valida OAB compliance + qualidade jurídica + ética IA → review documento `governance/legal/advogada-review-peca-revisional-2026-05-XX.md` com verdict APROVADO/NEEDS-CHANGES.

### AC-PRD-γ-06 — Audit chain HMAC preservado

`peca_generated` event + `pdf_downloaded` event registrados em audit.jsonl com:
- entry_hash + previous_entry_hash linkage
- timestamp ISO 8601 + tz
- payload hashed (PDF SHA256, não conteúdo)

### AC-PRD-γ-07 — Smith Methodology v5 functional smoke probe

Pós-implementação Neo + Oracle gate G5 → Smith executa functional smoke probe v5 verificando:
- audit.jsonl com `peca_generated` entry real
- PDF abrível em viewer (não corrompido)
- Render weasyprint sem warnings críticos
- LLM Redator inference real (Ollama logs evidência)
- OAB compliance fields populated

---

## Out of Scope (Sprint 6 Bloco γ)

| Item | Razão | Sprint Target |
|------|-------|---------------|
| Modalidades CDC_BENS_PF, CDC_IMOBILIARIO, CARTAO_ROTATIVO | DP-03 MVP restrição (codigos_bacen.yaml) | Sprint 6+ ADRs específicas por modalidade |
| Peça D2 (Decisão Adversa parsing) | MVP-LEAN-01 Task 3+5 partial — REVIEW Sprint 6+ se Eric demo precisa | Sprint 6.1 |
| Peça D3 (Apelação Cível condicional) | Depende D2 — Sprint 6+ | Sprint 6.1+ |
| Multi-tenant peça storage S3-compatible | LGPD retention >90d cloud — Sprint 7+ (release v0.4.0) | Sprint 7+ |
| Eric advogada externa review workflow (ClickUp/Linear ticket) | Process eric-side — review manual Sprint 6 closure | Sprint 7+ tooling |
| Peça ANBIMA bonds modalities | Fora MVP CDC consumer | Sprint 8+ |
| Multilingual support (peça em inglês) | Não MVP brasileiro | Out of roadmap atual |

---

## Risks + Mitigations

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **R-01** LLM Redator gera peça com hallucinated Súmulas (Súmula inexistente) | 🟠 MEDIUM | 🔴 HIGH | FR-PECA-05 traceability (citações vinculadas ao Vault docs reais); Aria ADR-022 hardening prompt + Pydantic schema strict; Smith probe |
| **R-02** Weasyprint render falha PDF inválido (corrupted bytes) | 🟡 LOW | 🟠 MEDIUM | Try/except + fallback "render error" PDF + audit entry; FR-PECA-04 latency NFR; unit tests render |
| **R-03** OAB compliance — peça gerada falha validação ética CFOAB | 🟠 MEDIUM | 🔴 HIGH | Advogada externa review BLOQUEANTE AC-PRD-γ-05; disclaimer NFR-PECA-05 obrigatório |
| **R-04** LGPD breach — temp PDF persistido fora retention 90d | 🟡 LOW | 🔴 HIGH | chmod 0o600 + auto-delete pós-download FR-PECA-06; audit hash-only (não conteúdo) NFR-PECA-04 |
| **R-05** Citação jurisprudência divergente do TeseAdvogado original | 🟠 MEDIUM | 🟠 MEDIUM | FR-PECA-05 cross-reference vault.docs_recuperados; Smith probe traceability |
| **R-06** Eric advogada review demora >7d → bloqueia commit final Sprint 6 | 🔴 HIGH | 🟠 MEDIUM | AC-PRD-γ-05 documenta dependência external; Eric pre-alinha advogada agenda |
| **R-07** Sabia-7b mais lento que estimativa (>120s per peça) | 🟠 MEDIUM | 🟡 LOW | Aria ADR-022 fallback qwen2.5:7b; SSE phase-start informa timing real |
| **R-08** Backward compat — Bloco β btnDownload placeholder quebra ao apontar /download/{job_id} novo | 🟡 LOW | 🟡 LOW | Smith review confirmar SPA Bloco β btnDownload-handler aceita endpoint backend novo seamlessly |

---

## Tech Debt Prevention Checklist

- [ ] FR-PECA-01..07 todos rastreáveis a User Stories US-PECA-01..05 (No Invention Art. IV)
- [ ] ACs tech-agnostic onde possível (não mencionar tecnologias específicas exceto onde requisito é a tech — weasyprint, Ollama)
- [ ] Risks R-01..R-08 todos com mitigation documented
- [ ] Smith Methodology v5 functional smoke probe pré-commit final (AC-PRD-γ-07)
- [ ] Advogada externa review BLOQUEANTE (AC-PRD-γ-05) — Sprint 6+ se atraso → catalogar TD-SP06-ADVOGADA-REVIEW-PENDING + flag commit
- [ ] LGPD §11 + §46 compliance fields populated (NFR-PECA-04)
- [ ] OAB Provimento 209/2021 CFOAB compliance fields populated (FR-PECA-01)
- [ ] Audit chain HMAC integrity preserved (AC-PRD-γ-06)

---

## Out-of-Scope Anti-Padrões (Evitar Invention)

❌ **NÃO criar:**
- Templates peça para 6+ modalidades simultaneamente (escopo MVP CDC_VEICULOS_PF)
- API REST external para advogada review submission (manual via .md file Sprint 6)
- Real-time collaborative editing peça (single-shot generation Sprint 6)
- AI re-writing iterative loop (single-shot Redator persona Sprint 6 — Sprint 6+ pode evoluir)

---

## Changelog

### v0.1.0 (2026-05-14)

- **Added:** PRD inicial Sprint 6 Bloco γ — peça revisional AI + PDF backend
- **FRs:** FR-PECA-01..07 (Redator LLM + Templates + Validação OAB + Weasyprint + Citações + Download endpoint + Filtro veredito)
- **NFRs:** NFR-PECA-01..05 (LLM tier + render latency + PDF size + LGPD compliance + OAB ethics)
- **ACs globais:** AC-PRD-γ-01..07 (incluindo advogada externa review BLOQUEANTE)
- **Risks identified:** R-01..R-08 com mitigações
- **Reason:** Resolver passos 5-6 fluxo ideal Eric — Smith Fase 7-A confirmou gap arquitetural (backend só gera VeredictoJuiz JSON, não peça revisional formal). DoD Sprint 6 zero mock SPA achieved Bloco β, agora gerar deliverable real Bloco γ.

---

## Handoff Trinity → @architect (Aria)

**Mandato Aria ADR-022:**

Decisão arquitetural Persona Redator Revisional:
1. **LLM tier** — sabia-7b vs qwen2.5:7b vs dual-tier (NFR-PECA-01 opções A/B/C)
2. **Prompt design** — system prompt + few-shot examples + Pydantic schema strict
3. **Hardening anti-hallucination** — citações Súmulas vinculadas Vault docs FR-PECA-05
4. **Integration pipeline** — Step 7 paralelo ou serial após Juiz Step 6
5. **Template HTML** — Jinja2 templates structure + variables exposed
6. **Weasyprint config** — fontes self-hosted + tokens.css load strategy
7. **Backward compat** — Bloco β btnDownload placeholder → /download/{job_id} novo (R-08)

ADR-022 espera-se ~30-45min Aria session decision + documentação.

Após Aria ADR-022 → Niobe Skill draft 4 stories Bloco γ (REDATOR-LLM + WEASYPRINT-PECA + DOWNLOAD-ROUTES + FIDELITY) → Keymaker validate batch → Neo implement (~3-5 dias) → Oracle G5 batch → Smith review v5.

---

*— Morgan (Trinity), planejando o futuro 📊*
*"PRD enxuto, escopo claro, MVP focused. Aria escolhe a arquitetura, Niobe escreve as ondas, Neo constrói, Oracle valida, Smith examina. Sprint 6 Bloco γ — onde o pipeline ganha voz jurídica."*
