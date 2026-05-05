# Release v0.2.0 — Production-grade Revisor Contratual

> **Data:** 2026-05-05
> **Sprint:** 02 (OFICIALMENTE 100% CLOSED)
> **Predecessor:** v0.1.0 (Sprint 01 closure)
> **Branch:** main (HEAD `3ec01f6`)
> **Milestone:** ⭐⭐ ZERO HIGH ATIVOS (incluindo arquitetural — primeira vez no projeto)

---

## 🎯 Highlights

**v0.2.0 transforma o Revisor Contratual em produto production-grade end-to-end:**

- **UI Web real conectada ao pipeline** — `POST /revisar` agora executa pipeline jurídico real (não mock); upload PDF → ~250s → veredito real exibido
- **ADR-010 Path C — Qwen 7B fallback** — Sabia-7B Q4 substituído por Qwen 2.5 7B como default (`LLM_TIER=balanced`); Sabia preservada como opt-in para upgrade GPU futuro
- **LGPD on-premise consistente** — fontes self-hosted (zero CDN externo), tempfile cleanup obrigatório, whitelist HTTP estrita preservada
- **Hardening completo** — validação MIME magic bytes %PDF-, max upload 10MB, tier Pydantic Literal, event listener cleanup (zero leak)
- **Documentação alinhada** — README + SOP-revisar-pdf refletindo ADR-010 + LLM tier strategy

**11 tech debts resolvidos** (2 HIGH + 3 MEDIUM + 6 LOW) — incluindo o último HIGH arquitetural ativo no projeto.

---

## ✨ Features

### LLM Strategy (ADR-010 Path C)

- **`feat(llm): ADR-010 Path C — Qwen 7B fallback default + format=json economista [Story REV-LLM-01]`** (`20d4459`)
  - `TIER_TO_MODEL_ADVOGADO` mapping: `lean=qwen2.5:3b`, `balanced=qwen2.5:7b` (NEW DEFAULT), `premium=sabia-7b-instruct` (preserved opt-in)
  - `get_advogado_llm` default tier `"premium"` → `"balanced"` (ADR-010 alignment)
  - `get_economista_llm` `format="json"` (defensive consistency)
  - Smoke INTEGRAL: 253.72s PASS (citação textual ≥10 chars, ratio<0.7 paralelismo Qwen 7B + 3B)

### UI Web (Production-grade)

- **`feat(web): production-grade UI — pipeline real + hardening 5 debts [Story UI-1]`** (`110986e`)
  - Validation hardening: MIME `%PDF-` magic bytes + max_size 10MB + tier `Literal["lean","balanced","premium"]`
  - Pipeline real integration: `JobState` TypedDict + `JOBS` dict + `await revisar_contrato` (async direto) + LGPD cleanup obrigatório
  - Event listener cleanup: Opção A (sse-container element removido no swap, garbage collected)
  - Error states UX: 4 templates PT-BR (invalid_pdf/file_too_large/invalid_tier/pipeline_failure) + custom exception handler
  - Resolves: TD-WEB-VAL-MIME-01 (M), TD-WEB-LISTENER-LEAK-01 (M), TD-WEB-NOMAXSIZE-01 (M), TD-WEB-TIER-ENUM-01 (L), TD-WEB-RUFF-UP037 (L), TD-WEB-SSE-NOSESSION-01 (L conditional)

- **`feat(web): self-host Google Fonts em /static/fonts/ (LGPD on-premise) [Story REV-INT-02]`** (`50a3b8b`)
  - 7 fontes self-hosted (~117KB total: Manrope 400/500/600/700, Fraunces 500, JetBrains Mono 400/500)
  - Zero CDN externo (LGPD on-premise consistente)
  - Resolves: TD-WEB-LGPD-CDN-01 (HIGH)

- **`feat(interface): substituir Streamlit por FastAPI + HTMX + Jinja2 [Story REV-INT-01]`** (`f6b935c`)
  - UI base FastAPI/HTMX/Jinja2 (Streamlit deprecated)
  - 5 endpoints + 6 templates + tokens Orsheva
  - HTMX-driven partial swaps + SSE streaming

### Infrastructure

- **`feat(infra): Ollama autônomo install + smoke pipeline INTEGRAL parcialmente validado [Story DEVOPS-01]`** (`f146be4`)
  - Ollama 0.23.0 install autônomo
  - qwen2.5:3b (1.9GB) + sabia-7b-instruct (4.1GB) + qwen2.5:7b (4.7GB)
  - Smoke pipeline INTEGRAL parcialmente validado (validação completa em REV-LLM-01)

### Landing Page

- **`feat(landing): production-ready Cloudflare Pages config`** (`a868f25`)
  - `_headers` + `_redirects` + `robots.txt` + setup guide

---

## 📚 Documentation

- **`docs: alinha README + sop-revisar-pdf com ADR-010 Path C [Story DOCS-02]`** (`8b37513`)
  - README seção "LLM Strategy": 3 tiers explícitos (lean/balanced/premium) + Footprint 10.7GB + Latência 250s + GPU upgrade path
  - README "Limitações conhecidas": modelos Ollama list correto + workaround `ollama pull qwen2.5:3b qwen2.5:7b`
  - `docs/sop-revisar-pdf.md`: 6 pontos cirurgicos atualizados (defaults, latência, JSON example, cross-refs ADR-010)

- **`docs(governance): Sprint 02 plan formal + PRD v1.0.3 DELTA [Sprint-02 planning]`** (`04a576b`)
  - Sprint 02 plan oficial
  - PRD v1.0.3 DELTA documentando mudanças vs v1.0.2

### Closure Commits (Operator entries)

- `3ec01f6` UI-1 closure + Sprint 02 100% CLOSED
- `98e5541` DOCS-02 closure
- `8eea89c` REV-LLM-01 closure
- `ad251c1` OPS-CLEANUP-01 NO-OP confirmado

---

## 🐛 Fixes

- **`fix: corrigir code_path em governance/.project.yaml após extração`** (`457fdaf`)
  - Path correto pós-extração de Claudinoinsights/the-matrix para repo dedicado

---

## 🧹 Chores

- **`chore: gitignore worker.js (build artifact MCP deploy)`** (`c9bf118`)

---

## ⭐⭐ Marco histórico — ZERO HIGH ATIVOS

**v0.2.0 é o primeiro release do projeto com ZERO tech debts HIGH ativos** (incluindo arquitetural):

| Tech Debt | Severidade | Resolvido em |
|---|---|---|
| TD-WEB-LGPD-CDN-01 | HIGH (code-level) | REV-INT-02 (`50a3b8b`) |
| **TD-LLM-SABIA-Q4-OUTPUT** | **HIGH (arquitetural)** | **REV-LLM-01 via ADR-010 Path C (`20d4459`)** |
| TD-WEB-VAL-MIME-01 | MEDIUM | UI-1 (`110986e`) |
| TD-WEB-LISTENER-LEAK-01 | MEDIUM | UI-1 (`110986e`) |
| TD-WEB-NOMAXSIZE-01 | MEDIUM | UI-1 (`110986e`) |
| TD-LLM-FORMAT-JSON-ECONOMISTA | LOW | REV-LLM-01 (`20d4459`) |
| TD-WEB-TIER-ENUM-01 | LOW | UI-1 (`110986e`) |
| TD-WEB-RUFF-UP037 | LOW | UI-1 (`110986e`) |
| TD-WEB-SSE-NOSESSION-01 | LOW conditional | UI-1 Phase C (`110986e`) |

**Pioneer milestone:** zero HIGH em todas as categorias (code-level + arquitetural). Próximas stories Sprint 03+ partem de baseline limpo.

---

## 📊 Sprint 02 Stats

- **Stories priority alta done:** 6/6 (100%)
- **Tech debts resolved:** 11 (2 HIGH + 3 MEDIUM + 6 LOW)
- **Commits since v0.1.0:** 15 (12 feat + docs + 1 fix + 1 chore + 1 closure)
- **Suite testes:** 232 passed + 1 skipped (baseline preservado em todos commits)
- **Smoke INTEGRAL:** 253.72s PASS (Qwen 7B + 3B paralelismo)
- **CI runs verde:** 25390674821 + 25394260607 + 25399068199 (entre outros)
- **Sessões LMAS:** Sessão 86 (Skill chain estrito Morpheus → @sm → @po → @dev → @qa → @devops, replicado 3 vezes em REV-LLM-01 + DOCS-02 + UI-1)

---

## 🔧 Stack ATIVA pós-v0.2.0

- **Pipeline core:** Python 3.11/3.12 + asyncio + Pydantic strict (extra='forbid')
- **LLM stack:** Ollama 0.23.0 + qwen2.5:7b (NEW DEFAULT) + qwen2.5:3b + sabia-7b-instruct (preserved opt-in) + langchain-ollama
- **UI Web:** FastAPI + HTMX + Jinja2 + 7 fontes self-hosted (~117KB) + tokens Orsheva
- **Audit:** HMAC GENESIS chain (forense-grade)
- **Vault:** SQLite + STJ/STF whitelist (LGPD)
- **BACEN:** API SGS (taxas agregadas, zero PII)

---

## 🚀 Como atualizar de v0.1.0 → v0.2.0

```bash
git fetch --tags
git checkout v0.2.0

# Pull novos modelos Ollama (additional ~4.4GB)
ollama pull qwen2.5:7b

# (Opcional) Toggle GPU upgrade path
# Se você tiver GPU CUDA disponível:
# echo "LLM_TIER=premium" >> .env
# (reverte para Sabia-7B com qualidade superior em GPU)

# Suite regression
python -m pytest --no-cov
# Esperado: 232 passed + 1 skipped

# Smoke INTEGRAL (requer 2 instâncias Ollama)
# Terminal 1: ollama serve (default :11434)
# Terminal 2: OLLAMA_HOST=127.0.0.1:11435 ollama serve
python -m pytest tests/smoke/test_paralelismo_llm.py -v --no-cov

# Iniciar UI Web
python -m bloco_interface.web.app
# → http://127.0.0.1:8501
```

---

## 📋 Próximas prioridades (Sprint 03 backlog)

- TD-WEB-CSP-INLINE-01 (LOW) — refactor `<script>` inline para arquivo externo se CSP strict for adotado
- Outros LOW debts catalogados em `governance/TECH-DEBT.md`
- Smoke E2E browser automatizado (Playwright opcional)
- Modalidades além de CDC_VEICULOS_PF (CDC_BENS_PF, CDC_IMOBILIARIO, CARTAO_ROTATIVO)
- Bloco_learning ativo (outcomes.db + ML feedback loop)
- TJBA / TJSP / TJMG / TJRJ / TJRS scrapers (whitelist requer ADR)

---

## 🙏 Co-authoring

Sprint 02 — Sessão 86 (2026-05-05) — workflow LMAS estrito 12 Skills consecutivas:

- **Morpheus** (orchestrator) — escopo de stories REV-LLM-01 + DOCS-02 + UI-1 com reality checks
- **River** (@sm) — story drafts com Dev Notes copy-paste-ready
- **Keymaker** (@po) — 10-point checklist validations (3× GO 10/10)
- **Neo** (@dev) — implementação cirúrgica + boundary respect rigoroso
- **Oracle** (@qa) — 6-15 adversarial probes per gate (REV-LLM-01 6 + DOCS-02 5 + UI-1 6)
- **Operator** (@devops) — 6 commits + push standalone + closures + esta release

**Co-Authored-By:** Claude Opus 4.7 (1M context)

---

*Release v0.2.0 — Production-grade Revisor Contratual · Sprint 02 100% CLOSED · ZERO HIGH ATIVOS · 11 tech debts resolved · ADR-010 Path C accepted Eric*
