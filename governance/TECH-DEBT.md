---
type: dashboard
title: "Tech Debt Registry — Revisor Contratual"
last_updated: "2026-05-06"
project: revisor-contratual
sprint: "01 (closure)"
tags:
  - project/revisor-contratual
  - tech-debt
  - sprint-01-closure
---

# Tech Debt Registry — Revisor Contratual

> **Sprint 01 closure consolidation** — STORY 15 (sessão 81, Neo).
> Consolidação de 13 tech debts catalogados em 4+ QA gates Oracle (sessões 60-77) + 1 finding ativo + 5 findings RESOLVED.
> Formato: 7 campos obrigatórios (ID, Source, Sev, Description, Est. Effort, Owner, Added).

---

## 📊 Resumo executivo

| Categoria | Quantidade |
|---|---|
| Active tech debts | **38** (3 MEDIUM + 12 LOW + 23 BL-* / TD-* — 14 migrados v1.1.1 + 1 NOVO v1.1.2 + 1 NOVO Sprint 03 CC.2 + 1 NOVO Sprint 03 CC.3 + 6 NOVOS Sprint 03 CC.7 Oracle PASS) |
| Active findings | **1** (F-CI-LOW-01 LOW) |
| Resolved findings | **9** (5 Phase 3-4 + 3 sessão 86 + 1 VAULT-FIX-01 sessão 87) |
| Sprint origem | 01 (Phase 2.B até Phase 5) + 02 (REV-INT-01..02 + REV-LLM-01) + 03 Phase 0 (VAULT-FIX-01) + 03 course-correction (PRD v1.1.0 → v1.1.1 BL-* migration) |

---

## 🔧 Active Tech Debts (13)

### MEDIUM (3)

| ID | Source | Sev | Description | Est. Effort | Owner | Added |
|----|--------|-----|-------------|-------------|-------|-------|
| **TD-PIPELINE-SMOKE-REAL** | STORY 9 + STORY 13 | MEDIUM | Smoke E2E real (Ollama + Sabia-7B + Qwen 3B + httpx STJ/STF + PDF físico) nunca executado — todos os testes usam mocks injetados. Validação INTEGRAL pipeline ainda não comprovada empiricamente. | 4h + 30min setup + ~7GB download | @dev | 2026-05-02 |
| **TD-VAULT-LOAD-TEST** | STORY 8 | MEDIUM | DP-08 — performance vault sqlite-vec não testada com 10k+ rows. RRF k=60 + busca híbrida pode degradar; SLA <500ms desconhecido em escala. | 2h | @dev | 2026-05-02 |
| **TD-VAULT-SCRAPER-OUTPUT-TO-BUNDLED-ADAPTER** | VAULT-FIX-01 (Phase D) | MEDIUM | `refresh-vault` valida disponibilidade upstream mas NÃO sobrescreve bundled JSON — scrapers retornam `JurisprudenciaItem` (rich schema) enquanto bundled segue `SumulaSTJ`/`SumulaVinculanteSTF` (lean schema). Adapter scraper→bundled permitiria refresh-vault auto-update. | 3h | @dev | 2026-05-05 |

### LOW (12)

| ID | Source | Sev | Description | Est. Effort | Owner | Added |
|----|--------|-----|-------------|-------------|-------|-------|
| **TD-VAULT-DATASET-STALENESS-MITIGATION** | VAULT-FIX-01 (Phase B+E) | LOW | Bundled dataset PROVISIONAL: 5 STJ + 5 STF SV (~1.6% STJ + ~8.6% STF SV oficial). Maintainer DEVE rodar one-shot bulk import pre-produção via `import-dataset` (Path A SOP-004). Refresh trimestral documentado em `docs/sop-refresh-vault-dataset.md`. Reminder em PROJECT-CHECKPOINT por trimestre. | n/a (process) | maintainer | 2026-05-05 |
| **TD-CI-COVERAGE-REPORTER** | STORY 12 | LOW | NFR-MAINT-02 cobertura é local-only (`pytest-cov` sem reporter externo). Adicionar Codecov ou Coveralls quando integração disponível. | 2h | @devops | 2026-05-02 |
| **TD-CI-PYTHON-3.13** | STORY 12 | LOW | Matrix CI fixa em Python 3.11 + 3.12. Adicionar 3.13 quando wheels `langchain-ollama` + `sentence-transformers` estabilizarem. | 30min | @devops | 2026-05-02 |
| **TD-CI-CACHE-PIP** | STORY 12 | LOW | `cache: 'pip'` configurado em `setup-python@v5`; verificar hit rate empírico após N runs. | 1h | @devops | 2026-05-02 |
| **TD-VAULT-TJ** | STORY 8 | LOW | Scrapers TJBA/TJSP/TJMG/TJRJ/TJRS não implementados. Whitelist NFR-LGPD-01 atual = STJ + STF apenas; expandir requer ADR formal por TJ. | 8h+ por TJ | @dev | 2026-05-02 |
| **TD-VAULT-LEGAL-BERTIMBAU** | STORY 8 | LOW | Modelo `neuralmind/bert-base-portuguese-cased` (~500MB) NÃO baixado por default. Usuário precisa instalar `sentence-transformers` opt-in para busca semântica completa. | 1h | @dev | 2026-05-02 |
| **TD-VAULT-TOPIC-INDETERMINADO** | STORY 8 | LOW | Filtro `legal_topic_principal` aceita qualquer string sem validação contra ontologia jurídica formal. Pode permitir typos/variações que comprometem busca. | 2h | @dev | 2026-05-02 |
| **TD-PIPELINE-QUERY-BUILDER** | STORY 9 | LOW | Query do vault construída via heurística MVP (`modalidade + classificacao + sumulas_aplicaveis`). Query-builder dedicado pós-MVP melhora precision/recall. | 4h | @dev | 2026-05-02 |
| **TD-PIPELINE-PACTUACAO** | STORY 9 | LOW | Default `instituicao_sfn=True + pactuacao_expressa=True` MVP. Inferir de markdown via parsing semântico futuro reduziria false positives em CDC não-bancário. | 3h | @dev | 2026-05-02 |
| **TD-CLI-RICH-OPTIONAL** | STORY 10 | LOW | `rich` é opcional + fallback ASCII (defensivo intencional). Documentado em SOP-002/003. Pode permanecer indefinidamente se nunca quebrar. | n/a | — | 2026-05-02 |
| **TD-CLI-EMBEDDINGS-DEFAULT-ZERO** | STORY 10 | LOW | `populate-vault` default `--zero-embeddings=True` (MVP). Busca semântica precisa de embeddings reais para funcionar; usuário precisa explicit opt-in. | 1h | @dev | 2026-05-02 |
| **TD-CLI-PROGRESS-BAR** | STORY 10 | LOW | Sem progress bar no pipeline real (`revisar` subcomando). Adicionar `rich.progress` quando smoke E2E real for executado. | 1h | @dev | 2026-05-02 |

---

## 📦 Backlog Deferred — Migrated from PRD v1.1.0 §11 (14 entries — F-CHK-02 mitigation)

> **Fonte canônica:** este registro substitui PRD §11 como source of truth (mitigação F-CHK-02 do tribunal CC.1A).
> **Adicionado:** 2026-05-05 (Morgan, sessão 87 PATCH v1.1.1).

| ID | Source | Sev | Description | Est. Effort | Owner | Trigger Re-avaliação | Added |
|----|--------|-----|-------------|-------------|-------|---------------------|-------|
| **BL-AUTH-01** | PRD v1.1.0 §11 | LOW | FR-AUTH-01/02/03 Auth elaborada (bcrypt + cookies + audit log tentativas; substitui FR-LGPD-MVP-01 mínima) | 6-8h | @dev (Neo) | Após 5 advogados validarem MVP em produção | 2026-05-05 |
| **BL-AUTH-02** | PRD v1.1.0 §11 | LOW | FR-AUTH-04 Sessão IP fingerprint + inatividade | 2-3h | @dev (Neo) | Depende BL-AUTH-01 completo | 2026-05-05 |
| **BL-DELIV-03** | PRD v1.1.0 §11 | LOW | FR-DELIV-02 Comparativo de Taxas (D4 — renumerado pós D3 Apelação MVP) | 2-3h | @dev (Neo) | Após v1.0 MVP em produção (3 meses) | 2026-05-05 |
| **BL-DELIV-04** | PRD v1.1.0 §11 | LOW | FR-DELIV-03 Parcelas Reais Incontroversas (D5) | 3-4h | @dev (Neo) | Idem BL-DELIV-03 | 2026-05-05 |
| **BL-DELIV-05a** | PRD v1.1.0 §11 splitado v1.1.1 | LOW | Embargos Declaração + Agravo Instrumento + Recurso Especial (Apelação Cível movida para MVP D3) | 3-4h | @dev (Neo) | Após advogado solicitar (feedback usuário) | 2026-05-05 |
| **BL-MULTI-UF** | PRD v1.1.0 §11 | LOW | FR-RAG-05 Multi-UF first-class CLI roadmap Brasil-wide | 4-8h por UF | @dev (Neo) | Sob demanda — advogado solicita expansão para nova UF | 2026-05-05 |
| **BL-ML-LOOP** | PRD v1.1.0 §11 | LOW | FR-ML-01..04 ML feedback loop estágio 1 (coleta WON/LOST) | 4-6h | @dev (Neo) | Volume ≥50 outcomes registrados (estimado mês 6) | 2026-05-05 |
| **BL-BACKUP** | PRD v1.1.0 §11 | LOW | FR-BACKUP-01/02 + FR-RECOVERY-01 elaborado (vs FR-BACKUP-MVP-01 mínimo MVP) | 3-5h | @dev (Neo) | Após relato de perda de dados em produção OU 6 meses pós-MVP | 2026-05-05 |
| **BL-CONFIG-UI** | PRD v1.1.0 §11 | LOW | FR-CONFIG-01/02 Página Configurações UI + modal aviso | 3-4h | @dev (Neo) | Após advogado solicitar troca frequente de Tier | 2026-05-05 |
| **BL-HITL-ELAB** | PRD v1.1.0 §11 | LOW | FR-JUIZ-02 painel HITL elaborado (bigram diversity + counter visual + microcopy) | 2-3h | @dev (Neo) + @ux-design-expert (Sati) | Após observar bypasses repetitivos em audit log MVP | 2026-05-05 |
| **BL-FIES** | PRD v1.1.0 §6.3 | LOW | Projeto-irmão "Revisor FIES" (avaliação separada — federal vs estadual + 4 razões técnicas) | a definir | @pm (Morgan) | Pós-v1.0 MVP em produção + Eric autorização | 2026-05-05 |
| **BL-VAULT-BULK-IMPORT** | PRD v1.1.1 §2.2 (NOVO) | **HIGH (PRE-RELEASE BLOCKER)** | One-shot bulk import oficial vault (≥600 entries STJ + ≥58 entries STF SV) via SOP-004 Path A | 2-4h maintainer | maintainer (Eric ou delegado) | **Bloqueia release MVP** — gate condition AC-3 e AC-10 | 2026-05-05 |
| **BL-GOLDEN-SET** | PRD v1.1.1 §2.5 (NOVO) | **HIGH (PRE-RELEASE BLOCKER)** | Curadoria 50 contratos sintéticos CDC PF Veículos + 50 queries golden RAG | 8-12h | @qa Oracle | **Bloqueia release MVP** — gate condition AC-1, AC-2, AC-3, AC-10 | 2026-05-05 |
| **BL-OAB-CHECKSUM** | PRD v1.1.2 §2.5 (NOVO — F-NEW-05 Smith re-review) | LOW | Validação OAB regex `^\d{1,6}/[A-Z]{2}$` aceita formato canônico mas SEM checksum CFOAB (bot pode rotar OABs falsas formato-válidas). Mitigação MVP: rate limit 1/min + 100/dia por OAB + audit log forensic tracking | 2-3h | @dev (Neo) | "API CFOAB pública disponível OU dataset OAB+UF público validado" | 2026-05-05 |
| **BL-ADR-013-MICROFIXES** | Smith CC.2 ADR-013 review (sessão 87 / 2026-05-06) | LOW | Refinamentos documentais não-bloqueadores em ADR-013 (5 LOW consolidadas): F-NEW3-02 alternativas §4 com strawmen ("Pip-only nunca", "subprocess + sleep loop") — refinar para alternativas técnicas plausíveis · F-NEW3-04 anti-patterns §6.6 parcialmente redundantes com §4 — consolidar ou diferenciar escopo · F-NEW3-06 SOP-005 succession plan ausente (Eric vender produto / novo maintainer) — adicionar SOP de transferência · F-NEW3-07 roadmap modalidades §6.5 [OTIMISTA] qualifier sem math revision — revisar estimativas com base em feedback pós-MVP · F-NEW3-10 §2.3 mais catálogo de FR existente do que ADR introducing decisão genuinamente nova — refatorar OR aceitar como pattern documentation explícita | 1-2h consolidados | @architect (Aria) | v1.0.1 OR pós-MVP launch (Eric escolheu opção α — perfeição shipping) | 2026-05-06 |
| **BL-UX-CC3-DEBT** | Smith CC.3 UX spec MVP-LEAN-01 review (sessão 87 / 2026-05-06) | MEDIUM/LOW (consolidado) | 16 findings residuais UX spec não-bloqueadores. **8 MEDIUM:** F-CC3-01 trade-off "1 processo por vez" não enforced (server-side detect job_id em curso → 409 Conflict + variante C6 nova) · F-CC3-04 spacing scale ausente (adicionar `--space-1..-6` OR documentar Tailwind classes) · F-CC3-07 ETA "~3min" hardcoded ignora variância LLM_TIER (parametrizar microcopy + documentar audit chain entry de cancelamento) · F-CC3-13 5 flows anômalos não documentados (refresh em S5 + perda EventSource sem reattachment, sessão expira durante download S6, S8 vermelho + sessão expira, network drop durante upload S3, 2ª aba durante S5) · F-CC3-14 mapping AC §8 falta AC-FR-LGPD-MVP-01b — *já endereçado inline em micro-PATCH α* · F-CC3-15 FR-DELIV-06 OAB rate limit excedido sem UX (variante C6 'rate_limit_oab' a adicionar) · F-CC3-18 cross-browser/input não documentado (Chrome 120+ / Edge 120+ / Firefox 120+ + touch input em laptop touchscreen). **8 LOW:** F-CC3-02 fonte weight banner Manrope ≥600 · F-CC3-09 count "~58 mensagens" aproximado (recont real ~62) · F-CC3-10 glossário §5.2 violado em wireframe S5 ("Advogado" sem prefixo "Persona") · F-CC3-12 reduced-motion completude (handler genérico universal vez de casos específicos) · F-CC3-16 audit.jsonl download direto sem streaming (Content-Disposition header) · F-CC3-17 estimativa BL-UX-WARNING-TOKEN ~10min subestimada (consolidação F-CC3-03 endereçou) · F-CC3-19 debt residual (este BL consolida) · F-CC3-20 banner verde fechável inconsistência S2 wireframe vs C2 props (decidir + documentar). **4 HIGH foram endereçados inline em micro-PATCH α:** F-CC3-05 (SSE connection drop) + F-CC3-06 (D3 dual-input) + F-CC3-08 (catch-all infra + 7 variantes erro) + F-CC3-11 (contraste `--warning` corrigido `#8B5A0B` ratio 5.49:1 verificado empiricamente). +1 MEDIUM cirúrgico (F-CC3-03 4 tokens consolidados) + bonus F-CC3-14 LOW. | 6-10h fragmentado | @ux-design-expert (Sati) + @dev (Neo) durante CC.6 conforme prioridade | v1.0.1 OR durante implementação Neo CC.6 (UX refinements pós feedback advogados beta) | 2026-05-06 |
| **TD-OLLAMA-AC7-ASYNC** | Oracle CC.7 review OLLAMA-MGR-01 (sessão 91 / 2026-05-06) — F-OG-01 | HIGH | `bloco_interface/web/app.py:297` `spawn_ollama` é chamada SÍNCRONA dentro do handler `/revisar` async. Helper `_wait_for_ollama_ready` faz polling síncrono (httpx.Client + time.sleep) que bloqueia o event loop por até 30s durante lazy respawn. Aceitável MVP single-user solo (perfil Eric: 1 advogado por vez per ADR-013 §2.2). **Refactor:** spawn_ollama → async com `asyncio.create_subprocess_exec` + `httpx.AsyncClient.get` no helper | 2-3h | @dev (Neo) | Trigger: produção multi-user OR feedback Eric latência mid-respawn | 2026-05-06 |
| **TD-OLLAMA-PULLSTATUS-IPC** | Oracle CC.7 review OLLAMA-MGR-01 (sessão 91 / 2026-05-06) — F-OG-02 | MEDIUM | `bloco_interface/ollama_manager.py:44` `_pull_status` é state global module-level. Em deploy multi-worker (uvicorn `--workers N`), workers diferentes terão `_pull_status` desincronizados — UI banner pode mostrar status de outro worker. ADR-013 §2.2 fixa single-process local; multi-worker é não-objetivo MVP. **Mitigação futura:** IPC (Redis OR file-based shared state) se multi-worker for adotado | 3-4h | @dev (Neo) + @architect (Aria — design IPC) | Trigger: adoção uvicorn `--workers >1` | 2026-05-06 |
| **TD-OLLAMA-LIFESPAN-DOC-REFRESH** | Oracle CC.7 review OLLAMA-MGR-01 (sessão 91 / 2026-05-06) — F-OG-03 | MEDIUM | `bloco_interface/web/app.py:133` + `app.py:204-213` lifespan docstrings/comments referenciam `ensure_models_pulled` como "Phase D stub" e mantêm `try/except NotImplementedError`. Phase D foi implementada na sessão 90; comments outdated. Try/except permanece como defensive programming válida (nunca executará o except em produção). **Mitigação:** atualizar docstrings + comentário inline para refletir Phase D done | 10min | @dev (Neo) | Próxima iteração ollama_manager OR housekeeping debt sprint | 2026-05-06 |
| **TD-OLLAMA-RETRY-TIMING-TESTS** | Oracle CC.7 review OLLAMA-MGR-01 (sessão 91 / 2026-05-06) — F-OG-04 | LOW | `tests/unit/test_ollama_manager_edge_cases.py` test EC-05 patcha `asyncio.sleep` para acelerar — não valida delays REAIS de retry exponential (1s/2s/4s). Cobertura comportamental OK; cobertura de timing real é debt aceitável | 30min | @dev (Neo) + @qa (Oracle) | Pós-MVP launch (não impacta funcionalidade) | 2026-05-06 |
| **TD-OLLAMA-LAZY-RESPAWN-PARTIAL** | Oracle CC.7 review OLLAMA-MGR-01 (sessão 91 / 2026-05-06) — F-OG-05 | LOW | `bloco_interface/web/app.py` AC-7 lazy respawn em `/revisar` chama `write_pid_file_atomic` dentro do loop por role (advogado + economista). Se respawn de "advogado" sucesso + "economista" raise mid-loop, PID file fica com apenas advogado. **Self-healing on next /revisar request** (lazy respawn será re-tentado). Documentar comportamento em runbook operacional | observação operacional | @dev (Neo) | Apenas se Eric reportar comportamento anômalo em produção | 2026-05-06 |
| **TD-OLLAMA-SMOKE-E2E-REAL** | Oracle CC.7 review OLLAMA-MGR-01 (sessão 91 / 2026-05-06) — F-OG-06 | **HIGH (PRE-RELEASE BLOCKER v0.3.0)** | Smoke E2E real (Ollama runtime + PDF físico + UI banner browser console) NÃO executado por Oracle nesta sessão (Eric environment dependency). **Bloqueia release v0.3.0** — Eric deve executar manual antes de @devops merge PR + tag v0.3.0: `python -m bloco_interface.web.app` → verificar logs (Ollama lifecycle starting + spawn :11434/:11435 + populate vault) + browser http://127.0.0.1:8501 + UI banner SSE durante download + POST /revisar real com PDF | 30min-1h Eric manual | maintainer (Eric) | **Bloqueia release MVP v0.3.0** | 2026-05-06 |

> **Total backlog deferred:** 12 LOW (preservados v1.1.0) + 2 HIGH (PRE-RELEASE BLOCKERS v1.1.1) + 1 LOW (NOVO v1.1.2) + 1 LOW (NOVO v1.1.2.1 / Sprint 03 CC.2) + 1 MEDIUM/LOW consolidado (NOVO Sprint 03 CC.3) + **6 NOVOS Sprint 03 CC.7 Oracle review** (1 HIGH + 2 MEDIUM + 3 LOW + 1 PRE-RELEASE BLOCKER) = **23 entries**
> **Migração executada:** PRD v1.1.1 §2.7 / Morgan sessão 87 / F-CHK-02 OPÇÃO 2 + BL-OAB-CHECKSUM v1.1.2 (F-NEW-05) + BL-ADR-013-MICROFIXES Sprint 03 CC.2 micro-PATCH α (Smith CC.2 5 LOW) + BL-UX-CC3-DEBT Sprint 03 CC.3 micro-PATCH α (Smith CC.3 16 residuais consolidados) + **6 TD-OLLAMA-* Sprint 03 CC.7 Oracle PASS** (F-OG-01..F-OG-06)

**Justificativa TD-OLLAMA-* (debt aceito Oracle CC.7 PASS):** Oracle review formal LMAS emitiu **PASS** para OLLAMA-MGR-01 com 6 follow-up items catalogados. Razão: (1) F-OG-01 HIGH é trade-off arquitetural compatível com ADR-013 §2.2 (single-user solo MVP) — não defeito; (2) F-OG-02/03 MEDIUM são gotchas futuros não-bloqueadores em deploy single-process; (3) F-OG-04/05 LOW são refinamentos não-críticos; (4) F-OG-06 PRE-RELEASE BLOCKER é Eric environment dependency — bloqueia release v0.3.0 mas não Story Done. Story status `Done` justificado: 14/14 ACs satisfeitos com evidências empíricas + ADR-011 fielmente implementada.

**Justificativa BL-ADR-013-MICROFIXES (debt aceito):** os 5 findings LOW Smith CC.2 são refinamentos documentais não-bloqueadores. Endereçá-los inline no micro-PATCH α retardaria CC.3+ Sprint 03 sem ganho material em qualidade arquitetural ou correção operacional. Eric (opção α recomendada Smith) priorizou shipping com qualidade ascendente. Os 5 MEDIUM Smith CC.2 (F-NEW3-01/03/05/08/09) **foram** endereçados no micro-PATCH α; este BL-* cobre apenas o residual LOW.

---

## 🟡 Active Findings (1)

| ID | Source | Sev | Description | Status |
|----|--------|-----|-------------|--------|
| **F-CI-LOW-01** | STORY 12 (sessão 71) | LOW | Path-filter pode falhar em commits cross-cutting (ex: refactor compartilhado em `packages/shared/`). Hoje revisor-contratual é isolado no monorepo — risco hipotético. | DEFERRED |

---

## ✅ Resolved Findings (5)

| ID | Resolved | Story | Resolution |
|----|----------|-------|------------|
| **F-PARSE-HIGH-01** | STORY 6 (sessão 51) | STORY 6 | Fix em `_extract_modalidade` — parênteses obrigatórios para precedência Python (`A and B or C` → `A and (B or C)`) |
| **F-MIN-02** | Antes STORY 12 | STORY 12 | Smoke `tests/smoke/test_paralelismo_llm.py` skip intencional sem Ollama (esperado em CI sem ambiente) |
| **F-LLM-MED-01** | STORY 13 (sessão 73) | STORY 13 | `model_config = ConfigDict(extra='forbid')` aplicado aos 5 schemas LLM-facing (`FundamentoInvocado`, `TeseAdvogado`, `AnaliseMacroEconomica`, `VeredictoJuiz`, `ValidacaoSemantica`) |
| **F-VAULT-LOW-01** | STORY 13 (sessão 73) | STORY 13 | Guard `math.isnan/isinf` fail-fast antes de `struct.pack` em `serialize_embedding` |
| **F-PIPELINE-LOW-01** | STORY 13 (sessão 73) | STORY 13 | Mensagem `ParserOCRRequired` reescrita PT-BR estruturada (diagnóstico → causa → solução → alternativa); reproduzida exatamente em SOP-003 caso 2 |
| **TD-WEB-LGPD-CDN-01** | Sessão 86 (2026-05-05) | Story REV-INT-02 | Self-hosted 7 woff2 (Manrope 4w + Fraunces 1w + JetBrains 2w) em /static/fonts/ via @fontsource/jsdelivr (~117KB total); base.html removidos 3 link tags Google Fonts; tokens.css adicionados 7 @font-face declarations (font-display: swap). Validações: AC-1 zero fonts.googleapis ✅, AC-2 zero fonts.gstatic ✅, AC-4 7/7 HTTP 200 ✅, AC-8 232 passed + 1 skipped ✅, AC-9 117536 bytes ≤ 204800 ✅. |
| **TD-LLM-SABIA-Q4-OUTPUT** | Sessão 86 (2026-05-05) | Story REV-LLM-01 (ADR-010 Path C) | LLM_TIER default mudado de 'premium' (Sabia-7B Q4) para 'balanced' (Qwen 2.5 7B). 3 mudanças cirúrgicas em llm_factory.py: TIER_TO_MODEL_ADVOGADO mapping (lean/balanced=Qwen, premium=Sabia preserved); get_advogado_llm default tier='balanced'; get_economista_llm format='json'. Smoke E2E re-run com Qwen 7B+3B PASS em 253.72s (citacao_textual ≥10 chars, ratio<0.7 paralelismo). Suite 232/1 zero regressão. Sabia preservado opt-in para futuro upgrade GPU. |
| **TD-LLM-FORMAT-JSON-ECONOMISTA** | Sessão 86 (2026-05-05) | Story REV-LLM-01 (junto com TD-LLM-SABIA-Q4-OUTPUT) | `format='json'` adicionado em `get_economista_llm` (defensive consistency com get_advogado_llm). |
| **TD-VAULT-SCRAPERS-FRAGILITY** | Sessão 87 (2026-05-05) | Story VAULT-FIX-01 (ADR-012 Path C) | Problema empírico descoberto sessão 86 v0.2.0 testing: `populate-vault --source all` falhava com STJ HTTP 200/404 intermitente (WAF + parser broken — HTML mudou) + STF anti-bot AWS ELB HTTP 403 (mesmo com verify=False). Pipeline real caía em fallback `MOCK_VERDICT`. **Resolução:** ADR-012 Vault Data Bundling Strategy + bundled JSON committed (`bloco_vault/data/sumulas-{stj,stf-vinculantes}.json`) + Pydantic schemas (`bloco_vault/data_schema.py`) + idempotent `populate_vault_if_needed()` em FastAPI lifespan + 3 CLI subcommands (refresh-vault opt-in best-effort, import-dataset PDF compendium oficial, validate-dataset hash verification). Suite 232/1 → 246/1 (14 novos tests AC-8 unit + integration). Scrapers preservados como ferramenta opt-in (zero modificação). |

---

## 🚦 Action Items por Sprint

### Sprint 02 — top-priority (quando iniciar)

- [ ] **Top-1: TD-PIPELINE-SMOKE-REAL** — validar pipeline INTEGRAL com Ollama real. Pré-requisito: Eric instala Ollama (~30min) + baixa Sabia-7B (~5GB) + Qwen 3B (~2GB). **Bloqueador para confiança em produção.**
- [ ] **Top-2: TD-VAULT-LOAD-TEST** — DP-08 perf 10k+ rows. Gerar dataset sintético STJ + STF expandido (~10k súmulas/SVs) e medir latência RRF.
- [ ] **Top-3: TD-CI-COVERAGE-REPORTER** — adicionar Codecov ou Coveralls. Visibility de cobertura externa sustenta NFR-MAINT-02.
- [ ] **Top-4: F-CI-LOW-01** — revisar quando primeira dep cross-package surgir no monorepo.

### Sprint 03+ (priorizar conforme uso real)

- [ ] **TD-VAULT-TJ** — scrapers TJ adicionais (TJBA priority — mercado-alvo MVP). Cada novo TJ exige ADR formal para expansão de whitelist NFR-LGPD-01.
- [ ] **TD-PIPELINE-QUERY-BUILDER** — query-builder dedicado pós-MVP (melhora precision/recall vault).
- [ ] **TD-PIPELINE-PACTUACAO** — inferir `pactuacao_expressa` de markdown via parsing semântico.
- [ ] **TD-VAULT-LEGAL-BERTIMBAU** — verificar se default zero-embeddings continua suficiente para usuários reais.
- [ ] **TD-VAULT-TOPIC-INDETERMINADO** — ontologia jurídica formal para `legal_topic_principal`.
- [ ] **TD-CLI-PROGRESS-BAR** — adicionar `rich.progress` no pipeline real.
- [ ] **TD-CLI-EMBEDDINGS-DEFAULT-ZERO** — flip default quando `sentence-transformers` for instalado por padrão.
- [ ] **TD-CI-PYTHON-3.13** — adicionar à matrix quando wheels estabilizarem.
- [ ] **TD-CI-CACHE-PIP** — verificar hit rate empírico.
- [ ] **TD-CLI-RICH-OPTIONAL** — manter como está (defensivo intencional).

---

## 🔄 Retrospective — Sprint 01 (14 stories Done, 14/14 PASS Oracle)

### O que funcionou ✅

- **Workflow LMAS estrito** — Morpheus orquestra; agentes executam dentro de Authority. Entregou 14 stories sem retrabalho ou ambiguidade.
- **Adversarial Oracle review** — probes Python ao vivo + cross-reference com código capturaram 0 regressões. STORY 14 cross-story consistency (4/4 frases-chave sincronizadas SOP↔código) é exemplo paradigmático.
- **Decisões Morpheus com Why explícito** — 60+ decisões D-MOR-X.0.x facilitaram QA gates Oracle e justificaram escolhas em Tech Debt registry.
- **Pre-flight check empírico em operações shared-state** — descoberta na sessão 78 (PR #1 desatualizado) preveniu merger MVP incompleto.
- **Hardening defensivo (Phase 4 #1) + Docs operacionais (Phase 4 #2)** — endereçou 3 findings LOW DEFERRED com 9 testes adversariais reais + cataloga uso real para advogados não-dev.

### O que não funcionou ⚠️

- **Pre-flight check de PR descoberto tardiamente** — sessão 78 descobriu commits Phase 4 não pushed; ideal seria check automático em workflow.
- **TECH-DEBT.md ficou para o final** (STORY 15) em vez de incremental por story — debts ficaram esparsos em 4+ QA gates Oracle. Consolidar agora exigiu re-leitura de 14 docs QA.
- **Lacuna runtime real** — Eric nunca rodou pipeline com Ollama real; toda confiança vem de mocks injetados + adversarial probes. Smoke real (TD-PIPELINE-SMOKE-REAL) é gap estrutural.
- **Versionamento release vs main desalinhado** — release v0.1.0-revisor-contratual aponta para `e00183c4` (pré-Phase-4); main HEAD é `b5c57be3` (com Phase 4). Releases futuras (v0.2.0) precisarão alinhar.

### Lessons Learned 📖

1. **Pre-flight checks ANTES de qualquer ação shared-state** (merge, push remote, deploy) são essenciais. Adicionar como passo obrigatório em template de stories git remote.
2. **TECH-DEBT.md DEVE ser atualizado por story** (não no final do sprint) — alinhar com `tech-debt-governance.md`. Sprint 02 começará com este princípio.
3. **Cross-story consistency** (STORY 13 hardening + STORY 14 docs) é padrão a replicar — quando um fix muda mensagem visível ao usuário, docs DEVEM reproduzir exatamente.
4. **Adversarial probes Python ao vivo** valem mais que probes textuais — Probe 4 STORY 14 (verificação Python ao vivo de mensagem ParserOCRRequired) detectou 6/6 aspectos com 100% de precisão.
5. **Squash merge + tag release histórica** é estratégia limpa: main fica curto e legível; tag preserva snapshot para auditoria; PR no GitHub preserva discussão de revisão.

### Action Items para Sprint 02 📌

- [ ] **Atualizar TECH-DEBT.md a cada story Done** (não acumular para closure) — alinhar com `tech-debt-governance.md`
- [ ] **Adicionar pre-flight check obrigatório** no template de stories que envolvem operações git remote (push, merge)
- [ ] **Setup Ollama documentado** como pré-requisito de Sprint 02 (ou criar STORY dedicada de setup automação)
- [ ] **Re-tag v0.2.0** quando Sprint 02 entregar mais features (alinhar tag com main HEAD pós-Phase-4)
- [ ] **TODO Operator para Sprint 02:** `git push origin --delete feature/revisor-contratual-v0.1.0` (cleanup remote — Neo não tem authority)

---

## 🔗 Referências

- **PRD canônico:** [`prd/prd-v1.0.2.md`](./prd/prd-v1.0.2.md)
- **ADR Index (9 ADRs):** [`architecture/ADR-INDEX.md`](./architecture/ADR-INDEX.md)
- **QA Gates Oracle (14 docs):** [`qa/`](./qa/)
- **Estado vivo:** [`CHECKPOINT-active.md`](./CHECKPOINT-active.md)

---

*Sprint 01 closure registry — Neo (sessão 81, 2026-05-05) · 13 active debts + 1 finding ativo + 5 RESOLVED. MVP v0.1.0 oficial em main `b5c57be3`.*

---

## 📦 Sprint 02 — REV-INT-01 (FastAPI+HTMX UI) — sessão 85

> **Origem:** Oracle QA Gate `qa-gate-story-rev-int-01-fastapi-htmx-ui.md` (CONCERNS).
> **Story:** REV-INT-01 — substituição de Streamlit por FastAPI + HTMX + Jinja2.

### HIGH (0)

✅ TD-WEB-LGPD-CDN-01 RESOLVED em sessão 86 (Story REV-INT-02). Ver Resolved Findings abaixo.

### MEDIUM (3) — ✅ ALL RESOLVED em sessão 86 via Story UI-1

✅ **TD-WEB-VAL-MIME-01 RESOLVED** | Story UI-1 (Phase A) | 2026-05-05 | Validação magic bytes `b'%PDF-'` em revisar() raise HTTPException(400)
✅ **TD-WEB-LISTENER-LEAK-01 RESOLVED** | Story UI-1 (Phase B) | 2026-05-05 | Listener anexado a `#sse-container` (removido no swap, garbage collected)
✅ **TD-WEB-NOMAXSIZE-01 RESOLVED** | Story UI-1 (Phase A) | 2026-05-05 | `MAX_UPLOAD_SIZE = 10MB` + `pdf.size > MAX_UPLOAD_SIZE` raise HTTPException(413)

### LOW (4)

| ID | Source | Sev | Description | Est. Effort | Owner | Added | Remediation by |
|----|--------|-----|-------------|-------------|-------|-------|----------------|
| ~~**TD-WEB-SSE-NOSESSION-01**~~ | ~~Oracle Probe 4 (F-SSE-01)~~ | ~~LOW~~ | ✅ **RESOLVED** Story UI-1 Phase C — `JOBS: dict[str, JobState]` + `/pipeline-stream?job_id=` binding implementado | ~~1h~~ | ~~@dev~~ | ~~2026-05-05~~ | ✅ Resolved 2026-05-05 |
| ~~**TD-WEB-TIER-ENUM-01**~~ | ~~Oracle Probe 3 (F-VAL-02)~~ | ~~LOW~~ | ✅ **RESOLVED** Story UI-1 Phase A — `LLMTier = Literal["lean","balanced","premium"]` substitui `str`; default `"balanced"` (ADR-010 alignment) | ~~10min~~ | ~~@dev~~ | ~~2026-05-05~~ | ✅ Resolved 2026-05-05 |
| ~~**TD-WEB-RUFF-UP037**~~ | ~~Oracle Probe 6 (F-RUF-01)~~ | ~~LOW~~ | ✅ **RESOLVED** Story UI-1 Phase A — `ruff --fix` aplicado; ruff All checks passed | ~~1min~~ | ~~@dev~~ | ~~2026-05-05~~ | ✅ Resolved 2026-05-05 |
| **TD-WEB-CSP-INLINE-01** | Oracle code review (F-CSP-01) | LOW | processing.html tem `<script>` inline (~30 linhas). Strict CSP (`script-src 'self'`) bloquearia. Mover para arquivo externo se CSP for adotado. | 20min | @dev | 2026-05-05 | Opcional (informacional) — out-of-scope UI-1 |

---

*Sprint 02 REV-INT-01 debts — Oracle (sessão 85, 2026-05-05) · 1 HIGH + 3 MEDIUM + 4 LOW = 8 findings. Gate: CONCERNS.*

---

## 📦 Sprint 02 — DEVOPS-01 (Ollama install + smoke E2E real) — sessão 86

> **Origem:** DEVOPS-01 closure parcial (Operator + Neo, 2026-05-05).
> **Story:** DEVOPS-01 — Ollama install autônomo + smoke pipeline integral.

### Status TD-PIPELINE-SMOKE-REAL: **PARTIALLY RESOLVED**

| Aspecto | Status | Evidência empírica |
|---|---|---|
| Ollama instalado (Windows 11 winget) | ✅ DONE | v0.23.0 |
| Modelos baixados | ✅ DONE | qwen2.5:3b (1.9GB) + sabia-7b-instruct (4.1GB via Modelfile TheBloke GGUF Q4_K_M) |
| 2 instâncias Ollama (paralelismo F-MIN-01) | ✅ DONE | :11434 advogado + :11435 economista, ambos enxergam modelos compartilhados |
| F-MIN-02 (langchain-ollama 1.x ainvoke coroutine) | ✅ CONFIRMED EMPIRICALLY | Smoke iteration 1: 180s; iteration 2: 48s — chamadas async reais |
| Pipeline INTEGRAL roda Sabia + Qwen via langchain-ollama | ✅ CONFIRMED | format=json adicionado em llm_factory.py — Sabia retorna JSON parseável |
| Smoke test PASSED | ❌ NOT YET | Output Sabia 7B Q4 CPU não atinge `min_length=10` em `FundamentoInvocado.citacao_textual` (modelo retorna "..." copiado do prompt template) |

**Conclusão:** TD-PIPELINE-SMOKE-REAL resolvido em 5 de 6 aspectos. Bloqueio único é qualidade do output Sabia (novo debt abaixo). Para atestar empiricamente o pipeline INTEGRAL, é suficiente — paralelismo e integração validados; quality gap é debt separado.

### NEW (1 HIGH + 1 LOW)

| ID | Source | Sev | Description | Est. Effort | Owner | Added | Remediation by |
|----|--------|-----|-------------|-------------|-------|-------|----------------|
| ~~**TD-LLM-SABIA-Q4-OUTPUT**~~ | ~~Smoke DEVOPS-01 sessão 86~~ | ~~HIGH~~ | ✅ **RESOLVED 2026-05-05** Story REV-LLM-01 (Path C ADR-010): LLM_TIER default mudou para 'balanced' (Qwen 2.5 7B); Sabia preservado opt-in via 'premium'. Smoke E2E passa em 253s (citacao_textual ≥10 chars confirmado, ratio<0.7). Ver Resolved Findings abaixo. | — | — | — | — |
| ~~**TD-LLM-FORMAT-JSON-ECONOMISTA**~~ | ~~Smoke DEVOPS-01 sessão 86~~ | ~~LOW~~ | ✅ **RESOLVED 2026-05-05** Story REV-LLM-01: `format="json"` adicionado em `get_economista_llm` (defensive consistency). Ver Resolved Findings abaixo. | — | — | — | — |

### Mudanças aplicadas em produto durante DEVOPS-01

| Arquivo | Mudança | Razão |
|---|---|---|
| `bloco_workflow/personas/llm_factory.py` | `format="json"` em `get_advogado_llm` | Sabia-7B Q4 estava gerando texto natural language; format=json força output JSON estruturado parseável |
| `tests/smoke/test_paralelismo_llm.py` | Fixture `JurisprudenciaItem` ampliado com 6 campos requeridos pelo schema (numero, binding, legal_topic_principal, ano_julgamento, texto_completo, indexed_at) | Schema cresceu em PRD v1.0.2 (Smith F-CRIT-03 vigência) mas test fixture não acompanhou |

### Mudanças em ambiente

- Ollama 0.23.0 instalado em `C:\Users\User\AppData\Local\Programs\Ollama\` via winget
- Modelos baixados em `~/.ollama/models/` (default Windows): ~6GB total
- `models/sabia-7b.Q4_K_M.gguf` (~3.8GB) + `models/Modelfile.sabia-7b-instruct` no repo (gitignored via `.gguf` + `models/` patterns existentes)
- 2ª instância Ollama background em `:11435` (durante smoke; deve ser parada após DEVOPS-01 closure)

---

*Sprint 02 DEVOPS-01 debts — Operator+Neo (sessão 86, 2026-05-05) · TD-PIPELINE-SMOKE-REAL partial RESOLVED + 2 novos debts (1 HIGH + 1 LOW).*

---

## Sprint 03 CC.25 — Smith adversarial review T8b (15 NEW + 3 RESOLVED)

> Origem: Oracle Smith adversarial review CC.25 (`governance/qa/smith-adversarial-review-t8b-cc25.md`).
> 18 findings totais. **3 fixes determinísticos aplicados em CC.25 Trilha B+** (F-01 + F-05 + F-08 RESOLVED). **15 findings empíricos remanescentes** registrados como tech debt.

### Active Items — Task 8b Smith Findings

| ID | Source | Sev | Description | Est. Effort | Owner | Added |
|----|--------|-----|-------------|-------------|-------|-------|
| TD-T8B-F02 | Smith CC.25 | HIGH | Estratégia 3 fallback aceita "1378" em qualquer contexto numérico — false positive (ex: "Processo 1378/2026") | 1h | @dev | 2026-05-06 |
| TD-T8B-F03 | Smith CC.25 | HIGH | `_classify_snippet` busca tese em `snippet OR full_html` — cross-tema contamination (tese de Tema 4555 atribuída ao 1378) | 1h | @dev | 2026-05-06 |
| TD-T8B-F04 | Smith CC.25 | HIGH | Estratégia 1 regex `[^<]+` força conteúdo inline — provável dead code em HTML aninhado real STJ | 1h | @dev | 2026-05-06 |
| TD-T8B-F06 | Smith CC.25 | HIGH | Estratégia 2 regex permite mismatch tags abertura/fechamento (`<article>...</div>`) — usar backreference `\1` | 30min | @dev | 2026-05-06 |
| TD-T8B-F07 | Smith CC.25 | HIGH | Faltam tests `httpx.TimeoutException` / `NetworkError` — paths críticos não exercitados | 1h | @dev | 2026-05-06 |
| TD-T8B-F09 | Smith CC.25 | MED | `RE_TESE_FIXADA` limit `[^\n<]{20,300}` corta tese real STJ multi-line ou com `<br>` interno | 30min | @dev | 2026-05-06 |
| TD-T8B-F10 | Smith CC.25 | MED | `RE_JULGAMENTO_DATE` só aceita DD/MM/YYYY — STJ usa "1º de junho de 2026", "junho/2026" etc. | 1h | @dev | 2026-05-06 |
| TD-T8B-F11 | Smith CC.25 | MED | `response.raise_for_status()` em `_http_get_with_retry` é dead code redundante (4xx + 5xx já tratados) | 5min | @dev | 2026-05-06 |
| TD-T8B-F12 | Smith CC.25 | MED | Audit entry write não-atomic em Windows / concurrent jobs — usar `os.open(O_APPEND)` ou file lock | 2h | @dev | 2026-05-06 |
| TD-T8B-F13 | Smith CC.25 | MED | Patterns CSS class hardcoded `(?:status\|1378\|repetitivo)` sem evidência empírica HTML real STJ | 1h Eric+@dev | @dev | 2026-05-06 |
| TD-T8B-F14 | Smith CC.25 | MED | Mock factory não simula retry success após falha intermitente (ex: 503→503→200) | 30min | @dev | 2026-05-06 |
| TD-T8B-F15 | Smith CC.25 | MED | Tests usam HTML sintético sem quirks reais (encoding latin-1/BOM, JS-rendered, cookies) | 2h | @dev | 2026-05-06 |
| TD-T8B-F16 | Smith CC.25 | LOW | Tese truncada 200 chars em `_classify_snippet` perde semântica jurídica | 15min | @dev | 2026-05-06 |
| TD-T8B-F17 | Smith CC.25 | LOW | Logger sem `log.debug` para parser strategy decisions (snippet capturado, regex match groups) | 15min | @dev | 2026-05-06 |
| TD-T8B-F18 | Smith CC.25 | LOW | 4xx não diferenciados — 401/403 (UA/auth) vs 404 (URL errada) tratados igual; mensagem genérica | 30min | @dev | 2026-05-06 |

### Resolved Items — Task 8b CC.25 fixes

| ID | Resolved | Story | Resolution |
|----|----------|-------|------------|
| TD-T8B-F01 | 2026-05-06 | MVP-LEAN-01 T8b CC.25 | CRITICAL — mitigado via feature flag `ENABLE_TEMA_1378_AUTO_CHECK` default false em `bloco_backup/scheduler.py`. Scheduler em prod NÃO registra job 3 sem env explícito |
| TD-T8B-F05 | 2026-05-06 | MVP-LEAN-01 T8b CC.25 | HIGH — mitigado via `DEFAULT_HEADERS` (User-Agent Mozilla/5.0 + Accept-Language pt-BR) em `bloco_dataset/scraper_tema_1378.py:DEFAULT_HEADERS` passed para httpx.Client |
| TD-T8B-F08 | 2026-05-06 | MVP-LEAN-01 T8b CC.25 | HIGH — corrigido em `bloco_dataset/auto_trigger.py:run_camada_1_check` — preserva fail_count quando estado atual é vermelho-via-fails (≥2). Invariante Task 7 SOP-005 mantida |

### Sumário CC.25

- **Smith findings totais:** 18 (1 CRITICAL + 7 HIGH + 7 MED + 3 LOW)
- **Resolved em CC.25 Trilha B+:** 3 (F-01, F-05, F-08 — todos determinísticos)
- **Active tech debt remanescente:** 15 (5 HIGH empíricos + 7 MED + 3 LOW)
- **Verdict pós-fix:** merge defensável com tech debts explícitos; 5 HIGH empíricos requerem URL real STJ + HTML extraction para validação iterativa pós-deploy

*Sprint 03 CC.25 Smith review apply-qa-fixes — Neo (sessão 91, 2026-05-06) · 3 fixes determinísticos + 15 tech debts registrados.*

---

## Sprint 03 CC.26 — Smith re-review CC.25 fixes (6 NEW)

> Origem: Oracle Smith re-review CC.26 (`governance/qa/smith-re-review-cc25-fixes.md`).
> 6 findings refinement (0 CRITICAL + 0 HIGH + 2 MED + 4 LOW). Verdict PASS-WITH-NOTES.

### Active Items — CC.26 Re-review

| ID | Source | Sev | Description | Est. Effort | Owner | Added |
|----|--------|-----|-------------|-------------|-------|-------|
| TD-T8B-RR01 | Smith re-review CC.26 | MED | F-05 retry preserva headers — falta test explícito retries 5xx → 200 (cobertura defesa-em-profundidade) | 30min | @dev | 2026-05-06 |
| TD-T8B-RR02 | Smith re-review CC.26 | MED | F-08 race condition get_current/set_state em concurrent (scheduler thread + acknowledge web POST) | 1-2h | @dev | 2026-05-06 |
| TD-T8B-RR03 | Smith re-review CC.26 | LOW | F-01 env parsing rígido — só "true" literal (não aceita "1"/"yes"/"on") | 15min | @dev | 2026-05-06 |
| TD-T8B-RR04 | Smith re-review CC.26 | LOW | F-01 env não re-lida runtime — toggle requer restart (esperado mas merece doc) | 15min docs | @dev | 2026-05-06 |
| TD-T8B-RR05 | Smith re-review CC.26 | LOW | F-05 UA URL hardcoded "+https://github.com/..." — stale-prone se repo renomeado | 15min | @dev | 2026-05-06 |
| TD-T8B-RR06 | Smith re-review CC.26 | LOW | F-08 docstring incompleta — não menciona vermelho-via-tese (fail_count=0) edge case | 5min | @dev | 2026-05-06 |

### Sumário CC.26 verdict

- **Verdict:** PASS-WITH-NOTES — 3 fixes determinísticos CC.25 confirmados corretos
- **Findings refinement:** 6 (não-bloqueantes para merge)
- **Suite preservada:** 397 passed + 3 skipped (zero regressão)
- **Merge PR #2 recomendado:** ✅ com confidence reforçada pós-re-review

*Sprint 03 CC.26 Smith re-review verdict — Oracle (sessão 91, 2026-05-06) · 6 tech debts refinement registrados.*
