---
type: story
id: TD-VAULT-CURATED-DATASET-01
title: "Vault Bulk Ingest via Curated Official Dataset Embedded (Caminho A) — 658 STJ + 58 STF SV"
status: Draft
priority: 1
sprint: "6.x AGGRESSIVE Bloco δ-extension (Vault Bulk Ingest)"
epic: "Sprint-6-Vault-Bulk-Ingest"
wave: "single (curation solo + Neo dev)"
owner: "@dev (Neo)"
estimated_effort: "4-6h"
severity_origem: "BLOCKER (Eric directive 2026-05-15 + pre-release blocker BL-VAULT-BULK-IMPORT + OAB compliance review degradation se vault permanecer 10 entries)"
created: "2026-05-15"
created_by: "@pm (Morgan, Trinity fallback @sm)"
related_adrs:
  - "ADR-012 Vault Data Bundling Strategy (governance precedent — schema canônico)"
  - "ADR-XX (a draftar por Aria — justificar dataset embedded vs scrape live + zero whitelist extension)"
related_prds:
  - "PRD-SP06-GAMMA v0.1.0 NFR-VAULT-01 (vault must contain comprehensive jurisprudência for OAB compliance)"
  - "PRD core v0.2.x NFR-LGPD-01 (ALLOWED_HOSTS whitelist preservada)"
related_stories:
  - "VAULT-FIX-01 (Sprint 03 Phase 0 — schema canônico + 5+5 bundled seed) — supersedes Sprint 03 dataset"
  - "TD-SP06-REDATOR-LLM-01 (consumer — Redator usa vault para citacoes_jurisprudencia)"
  - "TD-SP06-FIDELITY-01 (Oracle OAB compliance — bate em vault count + traceability)"
related_findings:
  - "Smith Fase 7-A — vault prod 0 rows (apenas 5+5 bundled em dev local)"
  - "Neo `*develop` 2026-05-15 — TD-STJ-SCRAPER-URL-UPDATE + TD-STF-LINUX-CERT-CHAIN reclassified como WAF block, fix-by-URL impossível"
supersedes:
  - "TD-STJ-SCRAPER-URL-UPDATE (WAF block diagnosed — fix-by-URL impossível)"
  - "TD-STF-LINUX-CERT-CHAIN (WAF block diagnosed — não era cert chain)"
unblocks:
  - "BL-VAULT-BULK-IMPORT pre-release blocker"
  - "AC-PRD-γ-05 Eric advogada externa review (OAB compliance precisa vault representativo)"
  - "Redator LLM citacoes_jurisprudencia com corpus completo"
tags:
  - project/revisor-contratual
  - story
  - sprint-6
  - vault
  - bulk-ingest
  - curated-dataset
  - lgpd-compliance
  - oab-compliance
  - draft
---

# Story TD-VAULT-CURATED-DATASET-01 — Vault Bulk Ingest via Curated Official Dataset Embedded

## Story

**Como** advogado revisor recebendo peça revisional gerada pelo Redator LLM,
**Eu quero** que o vault SQLite contenha o corpus COMPLETO de súmulas STJ (~658) e STF SV (~58),
**Para que** as citações jurisprudenciais da peça gerada sejam representativas, oficiais e auditáveis — garantindo OAB compliance review aprovação e produtividade real do revisor.

---

## Contexto

### Origem do escopo

Eric directive 2026-05-15: "preencha o vault com todas as jurisprudências". Caminho A escolhido (`@dev` Neo handoff `handoff-dev-to-claudino-2026-05-15-vault-bulk-ingest-strategy-decision.yaml`) após Neo diagnose:

- **Scrapers atuais bloqueados deterministicamente** por WAF anti-bot (Cloudflare `Cf-Mitigated: challenge` em STJ; AWS `x-amzn-waf-action: challenge` em STF). Diagnose Neo `2026-05-15` confirmou que fix de URL/cert chain **não destrava** scrape.
- **Bundled dataset atual** = 5 STJ + 5 STF SV em `bloco_vault/data/` (insuficiente para OAB compliance review).
- **Whitelist NFR-LGPD-01** (`ALLOWED_HOSTS` = `{"www.stj.jus.br", "www.stf.jus.br"}`) preservada — Caminho A não scrapeia em runtime, popula offline via JSON bundled.

### Eric escolheu Caminho A (de 4 opções apresentadas)

- ✅ **A** Curated official dataset embedded JSON (4-6h, recomendado)
- ⬜ B Wikipedia API + ADR whitelist extend (1.5h, fonte secundária)
- ⬜ C Playwright/Selenium bypass WAF (3-5h, +200MB Docker)
- ⬜ D Defer launch com 10 entries (0h, qualidade peça degradada)

### Por que A vence

| Critério | A (escolhido) | B Wikipedia | C Playwright | D Defer |
|----------|---------------|-------------|--------------|---------|
| Manutenção LGPD/whitelist | ✅ Zero extensão | ⚠️ Extend ADR | ✅ Mantém | ✅ Mantém |
| Rede em runtime | ✅ Zero (offline) | ❌ Sim | ❌ Sim | ✅ Zero |
| Effort | ⚠️ 4-6h | ✅ 1.5h | ⚠️ 3-5h | ✅ 0h |
| Fonte | ✅ Oficial direto | ⚠️ Secundária | ✅ Oficial | ❌ N/A (10 entries) |
| Manutenibilidade | ✅ One-shot + 3-4×/ano refresh | ❌ Wikipedia URL pode mudar | ❌ WAF rules evoluem | N/A |
| Docker bloat | ✅ Zero | ✅ Zero | ❌ +200MB | ✅ Zero |
| Compatível Aria refactor-plan slim Docker | ✅ | ✅ | ❌ Conflita | ✅ |

### Schema canônico (ADR-012, `bloco_vault/data_schema.py`)

- `SumulaSTJ` fields: `numero:str(1..20)` + `texto:str(min=10)` + `data_aprovacao:date|None` + `revogada:bool` + `area:Literal[civil|penal|processual_civil|processual_penal|tributario|trabalhista|administrativo|outras]` + `fonte_url:HttpUrl` + `fetched_at:datetime` + `hash_sha256:str|None`
- `SumulaVinculanteSTF` fields: `numero:int(1..999)` + `texto:str(min=10)` + `data_aprovacao:date|None` + `revogada:bool` + `fonte_url:HttpUrl` + `fetched_at:datetime` + `hash_sha256:str|None`
- `VaultDataset` wrapper: `schema_version:"1.0"` + `source:"stj"|"stf"` + `last_updated:datetime` + `last_refresh_method:"manual_import"` (this story) + `last_refresh_audit_log:str` + `total_entries:int` + `entries:list[...]`

---

## Acceptance Criteria

- **AC-01 — Schema compliance:** `bloco_vault/data/sumulas-stj.json` + `bloco_vault/data/sumulas-stf-vinculantes.json` validam contra `VaultDataset` (ADR-012, `bloco_vault/data_schema.py`). Zero `ValidationError` ao executar `VaultDataset.model_validate_json(...)`. Campo `last_refresh_method` = `"manual_import"`. Campo `total_entries` = `len(entries)` (model_validator enforced).
- **AC-02 — STJ volume:** `sumulas-stj.json` contém ≥ 650 entries (target 658 ± tolerance). Entries com `revogada=true` são incluídas (rastreabilidade histórica completa).
- **AC-03 — STF SV volume:** `sumulas-stf-vinculantes.json` contém ≥ 56 entries (target 58 ± tolerance). Inclui SVs revogadas com `revogada=true`.
- **AC-04 — Fonte oficial rastreável (NO INVENTION):** Cada entry tem `fonte_url` apontando para fonte oficial (preferência STJ/STF; aceitável LexML.gov.br ou DJe oficial). Cada entry tem `texto` LITERAL da fonte oficial (não paraphrasing, não summary). `hash_sha256` calculado de `texto` para tamper detection.
- **AC-05 — populate_vault_if_needed() smoke test:** Rodar `python -c "from bloco_vault.populate import populate_vault_if_needed; ..."` localmente → retorna `PopulateResult(populated=True, stj_count>=650, stf_count>=56, skipped_reason=None)`. Vault SQLite local fica com ≥ 706 rows em tabela `jurisprudencia`.
- **AC-06 — DATASET-CHANGELOG.md atualizado:** Append entry `v2.0.0 — 2026-05-15 — Full corpus 658 STJ + 58 STF SV (curated official dataset Caminho A). Sources: [URLs oficiais documentadas]. Author: @dev Neo + @pm Morgan story TD-VAULT-CURATED-DATASET-01.`
- **AC-07 — Pytest 0 regressões:** `tests/unit/test_populate_vault.py` + `tests/unit/test_vault_data_schema.py` + suite completa `python -m pytest tests/ -o addopts="" -q` retorna `0 failed`. Baseline atual conhecido: 248 passed Bloco γ.
- **AC-08 — Zero whitelist extension:** `ALLOWED_HOSTS` em `bloco_vault/scrapers/base.py` permanece `frozenset({"www.stj.jus.br", "www.stf.jus.br"})` — não modificado. Caminho A não envolve scrape em runtime (populate é offline puro).
- **AC-09 — Scrapers órfãos documentados:** Adicionar docstring header em `bloco_vault/scrapers/stj_sumulas.py` + `stf_sumulas_vinculantes.py`:
  ```
  WARNING: WAF anti-bot (Cloudflare + AWS WAF) blocks live scraping deterministically.
  This module is preserved as orphan — populate.py uses bundled JSON datasets instead.
  See: governance/stories/TD-VAULT-CURATED-DATASET-01.md + handoff Neo 2026-05-15.
  ```
- **AC-10 — Deploy VPS:** Após smoke local OK, encadear `@devops` Operator Skill para:
  1. Build new Docker image incorporando JSONs atualizados (or `docker cp` bundled data direto se mais simples).
  2. SSH VPS `/opt/revisor-contratual/` → re-deploy container `revisor-prod-app`.
  3. Smoke verificação: `docker exec revisor-prod-app python -c "from bloco_vault.schema import open_vault; c=open_vault('/home/revisor/.local/share/revisor-contratual/vault.db'); print(c.execute('SELECT COUNT(*) FROM jurisprudencia').fetchone()[0])"` → ≥ 706.
  4. Smoke probe HTTPS endpoint que consume vault (ex: `/api/jurisprudencia/search?q=civil` ou similar) — retorna ≥ 1 resultado.

---

## Tasks / Subtasks

- [ ] **Task 1: Source identification + sample validation (1h)**
  - [ ] 1.1 Identificar fonte oficial STF SV (candidato primário: PDF anexo no portal STF `https://www.stf.jus.br/arquivo/cms/...` — testar via WebFetch com User-Agent realista; fallback: LexML.gov.br colecao "Súmulas Vinculantes STF"; fallback ultimate: Wikipedia pt cross-validated com DJe)
  - [ ] 1.2 Identificar fonte oficial STJ (candidato primário: PDF "Súmulas Anotadas STJ" via SCON `https://scon.stj.jus.br/SCON/sumstj/`; fallback: LexML coleção "Súmulas STJ"; fallback ultimate: Wikipedia pt cross-validated com publicação institucional STJ)
  - [ ] 1.3 Validar 3 sample entries de cada fonte: numero + texto + data_aprovacao corretos vs DJe oficial
  - [ ] 1.4 Documentar URLs canônicas em comentário no JSON (`"_source_documentation": "..."`)

- [ ] **Task 2: STF SV dataset curation (1-1.5h, 58 entries)**
  - [ ] 2.1 Coletar 58 entries (SV 1 a SV 58, incluindo revogadas)
  - [ ] 2.2 Para cada entry: numero, texto literal, data_aprovacao (formato `YYYY-MM-DD`), revogada (bool), fonte_url (HttpUrl), fetched_at (`datetime.now(UTC)`), hash_sha256 (`hashlib.sha256(texto.encode()).hexdigest()`)
  - [ ] 2.3 Montar `VaultDataset` wrapper: schema_version="1.0" + source="stf" + last_updated + last_refresh_method="manual_import" + total_entries=58 + entries=[...]
  - [ ] 2.4 Write `bloco_vault/data/sumulas-stf-vinculantes.json` (UTF-8, indent=2)
  - [ ] 2.5 Validate: `python -c "import json; from bloco_vault.data_schema import VaultDataset; VaultDataset.model_validate_json(open('bloco_vault/data/sumulas-stf-vinculantes.json',encoding='utf-8').read())"`

- [ ] **Task 3: STJ dataset curation (2-3h, 658 entries — maior volume)**
  - [ ] 3.1 Coletar 658 entries (Súmula 1 a ~668, com revisões -A/-B incluídas)
  - [ ] 3.2 Para cada entry: numero (str com revisão se aplicável), texto literal, data_aprovacao, revogada, area (mapping STJ→Literal: civil/penal/processual_*/tributario/trabalhista/administrativo/outras), fonte_url, fetched_at, hash_sha256
  - [ ] 3.3 Montar `VaultDataset` wrapper STJ: source="stj" + total_entries=658
  - [ ] 3.4 Write `bloco_vault/data/sumulas-stj.json` (UTF-8, indent=2)
  - [ ] 3.5 Validate Pydantic schema

- [ ] **Task 4: Smoke populate_vault_if_needed() local (0.5h)**
  - [ ] 4.1 Delete vault existente: `rm ~/.local/share/revisor-contratual/vault.db` (se houver)
  - [ ] 4.2 Run smoke: `python -c "from pathlib import Path; from bloco_vault.populate import populate_vault_if_needed; from bloco_vault.embedder import zero_embedder; r=populate_vault_if_needed(Path.home()/'.local/share/revisor-contratual/vault.db', Path('bloco_vault/data'), embedder_fn=zero_embedder); print(r)"`
  - [ ] 4.3 Verify PopulateResult: populated=True + stj_count>=650 + stf_count>=56
  - [ ] 4.4 Verify SQLite count: `python -c "from bloco_vault.schema import open_vault; print(open_vault(...).execute('SELECT COUNT(*) FROM jurisprudencia').fetchone())"`

- [ ] **Task 5: Update scrapers órfãos docstring + DATASET-CHANGELOG (0.25h)**
  - [ ] 5.1 Edit `bloco_vault/scrapers/stj_sumulas.py` header docstring com WAF warning
  - [ ] 5.2 Edit `bloco_vault/scrapers/stf_sumulas_vinculantes.py` header docstring idem
  - [ ] 5.3 Append entry v2.0.0 em `bloco_vault/data/DATASET-CHANGELOG.md`

- [ ] **Task 6: Pytest 0 regressões (0.25h)**
  - [ ] 6.1 Run `python -m pytest tests/unit/test_populate_vault.py tests/unit/test_vault_data_schema.py -v`
  - [ ] 6.2 Run full suite: `python -m pytest tests/ -o addopts="" -q`
  - [ ] 6.3 Confirmar 0 failed
  - [ ] 6.4 Se tests existentes validam contagens hardcoded 5+5, atualizar para ≥650 + ≥56 (ou parametrize)

- [ ] **Task 7: Update File List + Change Log + handoff yaml @smith verify (0.25h)**
  - [ ] 7.1 Update File List (story file section): `bloco_vault/data/sumulas-stj.json`, `bloco_vault/data/sumulas-stf-vinculantes.json`, `bloco_vault/data/DATASET-CHANGELOG.md`, `bloco_vault/scrapers/stj_sumulas.py` (docstring only), `bloco_vault/scrapers/stf_sumulas_vinculantes.py` (docstring only)
  - [ ] 7.2 Append Change Log entry: "2026-05-15: Story implemented — full corpus 658 STJ + 58 STF SV embedded. populate_vault_if_needed smoke OK. 0 pytest regressions."
  - [ ] 7.3 Write handoff yaml `.lmas/handoffs/handoff-dev-to-smith-2026-05-15-vault-curated-dataset-verify.yaml`
  - [ ] 7.4 Flip story status → Ready for Review

---

## Dev Notes

### Fonte oficial — pesquisa inicial (Neo handoff)

**STF SV (~58 entries):**
- Tentativa Neo 2026-05-15: `www.stf.jus.br/arquivo/cms/jurisprudenciaSumulaVinculante/anexo/Enunciados_Sumula_Vinculante_STF_Completo.pdf` → 404 (URL especulativa, não confirmada).
- Fonte fallback recomendada: Wikipedia pt `Lista_de_súmulas_vinculantes_do_Supremo_Tribunal_Federal` — cross-validar 3-5 entries random contra DJe oficial antes de aceitar bulk.
- Fonte alternativa: portal LexML.gov.br (governo, oficial secundário).

**STJ Súmulas (~658 entries):**
- SCON `scon.stj.jus.br/SCON/sumstj/toc.jsp` retornou 200 OK 15KB mas conteúdo é página index sem dados estruturados.
- Fonte recomendada: PDF "Súmulas Anotadas do STJ" (publicação institucional anual STJ) — buscar via Google Scholar ou repositório STJ open data.
- Fonte fallback: Wikipedia pt `Lista_de_súmulas_do_Superior_Tribunal_de_Justiça`.

### Constraints técnicas

- **Pydantic strict:** `extra="forbid"` implícito via `Literal` enum em `area`. Validators rejeitam texto vazio ou "...".
- **hash_sha256:** calcular sobre `texto.encode("utf-8")` → 64 hex chars.
- **fetched_at:** TODAS entries do mesmo dataset PODEM compartilhar mesmo timestamp (representativo do `last_updated` do dataset bundled).
- **fonte_url:** Pydantic `HttpUrl` valida — deve incluir scheme `https://`.

### Wave strategy

Sem paralelização — Caminho A é single-developer task (curation + validation sequencial). Effort total: 4-6h wall-clock para humano; sob agente IA com tools (WebFetch + WebSearch) pode comprimir para 1-2h sessão única.

### CodeRabbit gate pre-commit

Story está fora do scope típico CodeRabbit (data files, não code logic). Self-healing loop pode reportar zero issues. Se reportar HIGH em scrapers/* (docstring update only), document_only suffice.

---

## Testing

### Unit tests existentes (consumir)

- `tests/unit/test_populate_vault.py` — testa idempotência + skip se vault populated
- `tests/unit/test_vault_data_schema.py` — testa Pydantic validation

### Tests novos sugeridos (opcional, não bloqueia AC)

- `tests/unit/test_dataset_volume.py`:
  - `test_stj_json_has_at_least_650_entries`
  - `test_stf_sv_json_has_at_least_56_entries`
  - `test_each_entry_has_valid_hash_sha256`
  - `test_each_entry_has_valid_fonte_url`

### Smoke integration test

- `tests/integration/test_vault_full_populate.py` (a criar): popula vault em tmp dir + assert SQLite count ≥ 706.

### Manual smoke pós-deploy

- Operator VPS post-deploy: `docker exec revisor-prod-app revisor vault-count` (ou equivalente CLI) → ≥ 706.

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-05-15 | @pm Morgan (Trinity fallback @sm) | Story drafted — 10 ACs + 7 Tasks + Dev Notes + Testing |

---

## Dev Agent Record

### Agent Model Used

*(a preencher por @dev Neo durante `*develop`)*

### Debug Log References

*(a preencher)*

### Completion Notes List

*(a preencher)*

### File List

*(a preencher por @dev — esperado: 2 JSONs + 1 CHANGELOG + 2 scrapers docstring updates)*

---

## Validation (Keymaker @po)

*(a preencher por @po `*validate-story-draft TD-VAULT-CURATED-DATASET-01` — 10-point checklist)*

- validated_by: ""
- validated_at: ""
- validation_score: ""
- validation_verdict: ""
