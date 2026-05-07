---
type: adr
id: "ADR-012"
title: "Vault Data Bundling Strategy — bundled dataset + optional refresh scrapers"
status: accepted
date: "2026-05-05"
proposed_by: "@architect (Aria)"
accepted_by: "Eric (decisão sessão 86, Path C aprovado com recomendações Aria default)"
accepted_date: "2026-05-05"
accepted_open_questions:
  - "Initial seed source: (c) one-shot scrape working hoje + manual STF (Aria default)"
  - "Refresh cadence: trimestral (Aria default)"
  - "Dataset signing: opt-in futuro Sprint 05+ (MVP usa hash_sha256 — Aria default)"
  - "Área classification: começar com 8 valores Literal (Aria default)"
adr_level: spec
spec_coverage:
  - "Dataset structure bundled em bloco_vault/data/ (JSON + Pydantic schema)"
  - "Idempotent population strategy app startup (count == 0 OR vault.db missing)"
  - "Refresh dual-path: scraper (best effort) + manual import CLI"
  - "Audit trail: hash_sha256 per entry + commit-signed updates + CHANGELOG entry"
  - "Schema versioning (schema_version field) para forward compatibility"
domain: "data | infra"
decision_makers: ["@architect (Aria)", "@dev (Neo)", "@data-engineer (Tank)", "Eric (decisão final pendente)"]
supersedes: null
superseded_by: null
absorves:
  - "STJ scraper fragility (parser quebrado pós HTML structure change — investigation Morpheus 2026-05-05)"
  - "STF scraper fragility (SSL cert chain + anti-bot AWS ELB HTTP 403)"
  - "AC-9 smoke E2E real bloqueado em UI-1 (vault vazio → fallback mock)"
related_to:
  - "ADR-001 (Vault SQLite — esta ADR adiciona data bundling layer, não supersedes)"
  - "NFR-LGPD-01 (whitelist HTTP — preservada: scrape opcional ainda usa whitelist)"
  - "Story VAULT-FIX-01 (Sprint 03 Phase 0 — implementation desta ADR)"
  - "ADR-011 (Ollama Lifecycle — paralela, mesma sprint)"
project: revisor-contratual
sprint: "03"
etapa: "Phase 0 — Architectural Foundation"
tags:
  - project/revisor-contratual
  - adr
  - vault
  - data-bundling
  - reliability
  - sprint-03
---

# ADR-012 — Vault Data Bundling Strategy

```
[@architect · Aria (Visionary)] — Sprint 03 · Phase 0 Architectural Foundation
SPRINT: 03 · DOMÍNIO: Data/Infra
```

## Contexto

A v0.2.0 (publicada 2026-05-05) implementa scrapers STJ e STF (`bloco_vault/scrapers/stj_sumulas.py` + `stf_sumulas_vinculantes.py`) para popular `vault.db` com súmulas e súmulas vinculantes. O comando `revisor populate-vault --source all` é prerequisite obrigatório para o pipeline real funcionar — sem vault populado, persona Advogado não consegue ancorar tese em jurisprudência (FR-TESE-04).

**Descoberta empírica em sessão 86 (2026-05-05) — investigação ultrathink Morpheus:**

| Fonte | Status atual | Causa real |
|---|---|---|
| STJ `/sumulas` | HTTP 200 OK ✅ | URL **não** mudou — **HTML estrutura mudou**: `find_all(class_=re.compile('sumula'))` retorna VAZIO. Parser quebrado. |
| STF `/sumulas-vinculantes` | ConnectError SSL + HTTP 403 | **DOIS issues:** SSL cert chain (certifi 2026.02.25) + anti-bot AWS ELB (`Server: awselb/2.0`). Fix `verify=False` sozinho retorna 403 mesmo. |
| `base.py` httpx config | Sem User-Agent customizado | Default `python-httpx/X.Y.Z` provavelmente blocked por bot detection. |

**Implicações da fragility identificada:**

1. **Sites externos mudam frequentemente:** STJ trocou estrutura HTML sem deprecation notice; STF adicionou anti-bot AWS ELB (provavelmente para combater scrapers comerciais). Próximas mudanças são **inevitáveis** — questão é quando, não se.

2. **Manutenção iterativa frágil:** fix scrapers requereria:
   - Update parser STJ para nova estrutura HTML
   - User-Agent rotation + cookies para contornar AWS ELB STF
   - Retry/backoff sofisticado
   - Possível Playwright (JS-rendered) se STJ migrar para SPA
   - Effort estimado: 6-10h primeira iteração + ongoing maintenance trimestral

3. **AC-9 smoke E2E real bloqueado:** UI-1 ficou com static-review-accepted porque vault populate falhou. Pipeline real (`revisar_contrato`) cai em fallback `MOCK_VERDICT` — não valida fluxo end-to-end com jurisprudência real.

4. **LGPD-positive:** scrape em runtime (mesmo whitelist STJ+STF) é overhead desnecessário — sumulas mudam raramente (poucas por trimestre). Bundled dataset é mais alinhado com NFR-LGPD-01 ("apenas STJ e STF na rede") porque **elimina** chamadas runtime à rede.

**Eric pediu (sessão 86):** "o Vault tem que funcionar". App self-contained sem dependência de scrape em runtime.

---

## Decisão

**Estratégia híbrida: bundled dataset (default) + scraper opcional (refresh manual via CLI).**

### Estrutura escolhida

```
bloco_vault/
├── data/                              ← NOVO (committed dataset)
│   ├── sumulas-stj.json               ← schema-validated
│   ├── sumulas-stf-vinculantes.json   ← schema-validated
│   └── DATASET-CHANGELOG.md           ← audit trail per refresh
├── scrapers/                          ← preservados (refresh tool opcional)
│   ├── stj_sumulas.py                 ← optional refresh (best effort)
│   ├── stf_sumulas_vinculantes.py     ← optional refresh (best effort)
│   └── base.py                        ← whitelist preservada NFR-LGPD-01
└── ...
```

### Comportamento do app startup

```python
# Pseudocódigo — implementação em VAULT-FIX-01 (Neo)
def populate_vault_if_needed(vault_db: Path) -> None:
    """Idempotent: popula apenas se vault.db missing OR vazio."""
    if not vault_db.exists():
        _populate_from_bundled_dataset(vault_db)
        return

    conn = open_vault(vault_db)
    count = conn.execute("SELECT COUNT(*) FROM sumulas").fetchone()[0]
    if count == 0:
        _populate_from_bundled_dataset(vault_db)
    # senão: noop (vault já populado, idempotent)
```

### Refresh dual-path

**Path 1 — Scraper opt-in (best effort):**

```bash
revisor refresh-vault --source stj   # tenta scrape STJ
revisor refresh-vault --source stf   # tenta scrape STF
revisor refresh-vault --source all   # tenta ambos
```

- Se scraper falhar: log warning + manter dataset atual (não corromper)
- Se scraper funcionar: gerar JSON + diff vs bundled + prompt usuário para `git add` + commit
- Audit log registra timestamp + source + diff size

**Path 2 — Manual import (autoritativo):**

```bash
revisor import-dataset --source-pdf compendium-stj-2026.pdf --output-json bloco_vault/data/sumulas-stj.json
revisor import-dataset --source-csv stf-sv-2026.csv --output-json bloco_vault/data/sumulas-stf-vinculantes.json
```

- Maintainer (Eric ou outro) baixa compendium oficial publicado pelo STJ/STF
- CLI valida schema Pydantic + gera hash_sha256 per entry + atualiza `DATASET-CHANGELOG.md`
- Maintainer commit + push (Operator standard flow)

---

## Rationale ultrathink

### Trade-offs avaliados

**Path A — Fix scrapers iterativo (REJEITADO):**

| Critério | Avaliação |
|---|---|
| Reliability | 🔴 Alta (sites externos mudam frequentemente) |
| Effort initial | 6-10h (parser STJ rewrite + STF anti-bot bypass) |
| Effort ongoing | 2-4h/trimestre (manutenção iterativa) |
| Speed populate-vault | 5-10min (network bound) |
| LGPD posture | OK (whitelist preservada) mas runtime scrape overhead |
| Audit trail | Pobre (cada scrape = state diferente, não versionado) |
| Dev experience | 🔴 Frágil — quebra silenciosamente |

**Path B — Playwright JS-rendered (REJEITADO):**

| Critério | Avaliação |
|---|---|
| Reliability | Média (ainda depende de HTML, mas robusto a JS-rendered SPAs) |
| Effort initial | 12-15h (Playwright setup + Chromium dep) |
| Effort ongoing | 2-3h/trimestre |
| Deps adicionadas | 🔴 Chromium ~150MB + playwright pip ~50MB |
| LGPD | OK |
| Single-user local | 🔴 Overkill — usuários instalando Chromium para jurisprudência? |
| Dev experience | Complexa |

**Path C — Bundled dataset + optional refresh (ESCOLHIDO):**

| Critério | Avaliação |
|---|---|
| Reliability | 🟢 Alta (commit-controlled, reproduzível) |
| Effort initial | 4-6h (extração inicial + schema + populate refactor) |
| Effort ongoing | 30-60min/trimestre (manual refresh) |
| Speed populate-vault | 🟢 <1s (JSON parsing local) |
| LGPD posture | 🟢 Excelente (zero runtime network calls para sumulas) |
| Audit trail | 🟢 Git-tracked, commit-signed |
| Dev experience | 🟢 Funciona out-of-the-box |
| Repo size impact | ~200-500KB JSON minified (aceitável) |
| Dataset staleness | 🟡 Risk médio (mitigation: timestamp UI warning + trimester refresh) |

### Por que Path C é o trade-off correto

1. **Reliability domina ROI:** sumulas STJ/STF mudam **lentamente** (algumas por trimestre). Bundled dataset captura esse ritmo de mudança naturalmente. Sites externos que mudam HTML/anti-bot mensalmente NÃO refletem ritmo real de mudança das sumulas.

2. **LGPD-aligned:** NFR-LGPD-01 estabeleceu whitelist mínima (STJ + STF + BACEN + 127.0.0.1). Bundled dataset reduz superfície de exposição runtime — vault populado offline.

3. **Audit-friendly:** dataset versioned no git permite forensic audit ("essa súmula é a oficial de quando?"). Cada refresh = commit com timestamp + diff + hash. Investigador jurídico pode validar autenticidade.

4. **Single-user local fits perfectly:** Revisor Contratual é app de **escritório de advocacia**, não SaaS multi-tenant. Refresh trimestral manual é razoável (advogado/admin atualiza compendium quando STJ publica nova).

5. **Out-of-the-box experience:** novo usuário roda app → funciona. Não precisa instruções "primeiro rode populate-vault e espere 10min OR fix os scrapers se quebraram".

### Trade-offs aceitos

1. **Dataset staleness risk:**
   - Mitigation 1: timestamp `last_updated` em UI ("Dataset atualizado em 2026-Q1")
   - Mitigation 2: trimester refresh process documentado em `docs/sop-refresh-vault-dataset.md`
   - Mitigation 3: warning visual se dataset > 6 meses old
   - Aceitável: súmulas STJ/STF não invalidam contratos overnight; lag de até 3 meses é razoável

2. **Repo size:**
   - STJ: ~600 súmulas × ~400 chars avg = ~240KB raw → ~200KB minified
   - STF SV: ~58 súmulas × ~700 chars avg = ~40KB raw → ~35KB minified
   - Total: ~235KB minified bundled
   - Git pack (gzip): ~80KB
   - **Aceitável** (não justifica Git LFS)

3. **Refresh process manual:**
   - Não é automatic — maintainer DEVE rodar trimestralmente
   - Mitigation: documented SOP + reminder no PROJECT-CHECKPOINT
   - Trade-off: simplicidade > automation (single-user app)

---

## Implementation Strategy

### Pydantic Schema Scaffold (para Neo implementar em VAULT-FIX-01)

```python
# bloco_vault/data_schema.py (NOVO)

from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class SumulaSTJ(BaseModel):
    """Súmula STJ — schema canônico per ADR-012.

    Numero pode incluir revisão: '1', '28-A', '342-revogada'
    """

    numero: str = Field(..., min_length=1, max_length=20)
    texto: str = Field(..., min_length=10)
    data_aprovacao: Optional[date] = None  # Some old súmulas sem data
    revogada: bool = False
    area: Literal[
        "civil", "penal", "processual_civil", "processual_penal",
        "tributario", "trabalhista", "administrativo", "outras",
    ] = "outras"
    fonte_url: HttpUrl
    fetched_at: datetime  # Timestamp do dataset capture
    hash_sha256: Optional[str] = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @field_validator("texto")
    @classmethod
    def texto_must_have_content(cls, v: str) -> str:
        if v.strip() == "" or v.strip() == "...":
            raise ValueError("Texto não pode ser vazio ou placeholder")
        return v


class SumulaVinculanteSTF(BaseModel):
    """Súmula Vinculante STF — schema canônico per ADR-012.

    SVs têm numeração simples 1-N (não revisões na mesma forma do STJ).
    """

    numero: int = Field(..., ge=1, le=999)
    texto: str = Field(..., min_length=10)
    data_aprovacao: Optional[date] = None
    revogada: bool = False
    fonte_url: HttpUrl
    fetched_at: datetime
    hash_sha256: Optional[str] = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @field_validator("texto")
    @classmethod
    def texto_must_have_content(cls, v: str) -> str:
        if v.strip() == "" or v.strip() == "...":
            raise ValueError("Texto não pode ser vazio ou placeholder")
        return v


class VaultDataset(BaseModel):
    """Top-level dataset wrapper — schema versioning + audit fields."""

    schema_version: Literal["1.0"] = "1.0"
    source: Literal["stj", "stf"]
    last_updated: datetime
    last_refresh_method: Literal["manual_import", "scraper", "seed"] = "seed"
    last_refresh_audit_log: Optional[str] = None  # Caminho relativo para audit entry
    total_entries: int = Field(..., ge=0)
    entries: list[SumulaSTJ] | list[SumulaVinculanteSTF]

    @field_validator("total_entries")
    @classmethod
    def total_must_match_entries(cls, v: int, info) -> int:
        if "entries" in info.data and len(info.data["entries"]) != v:
            raise ValueError(
                f"total_entries ({v}) deve ser igual a len(entries) ({len(info.data['entries'])})"
            )
        return v
```

### Population Strategy (idempotent)

```python
# bloco_vault/populate.py — refactor (não new file)

def populate_vault_if_needed(vault_db: Path, data_dir: Path) -> None:
    """Idempotent population — popula apenas se vault missing OR vazio.

    Args:
        vault_db: Path to vault.db (SQLite)
        data_dir: Path to bloco_vault/data/ (bundled JSON)
    """
    needs_populate = False

    if not vault_db.exists():
        needs_populate = True
    else:
        conn = open_vault(vault_db)
        try:
            count = conn.execute("SELECT COUNT(*) FROM sumulas").fetchone()[0]
            if count == 0:
                needs_populate = True
        finally:
            conn.close()

    if not needs_populate:
        return  # Idempotent: vault já populado

    # Load bundled datasets
    stj_dataset = VaultDataset.model_validate_json(
        (data_dir / "sumulas-stj.json").read_text(encoding="utf-8")
    )
    stf_dataset = VaultDataset.model_validate_json(
        (data_dir / "sumulas-stf-vinculantes.json").read_text(encoding="utf-8")
    )

    # Insert into vault.db (existing insert_jurisprudencia API)
    conn = open_vault(vault_db)
    try:
        for entry in stj_dataset.entries:
            insert_jurisprudencia(conn, source="stj", entry=entry.model_dump())
        for entry in stf_dataset.entries:
            insert_jurisprudencia(conn, source="stf", entry=entry.model_dump())
        conn.commit()
    finally:
        conn.close()

    logger.info(
        f"Vault populated: {len(stj_dataset.entries)} STJ + {len(stf_dataset.entries)} STF "
        f"(dataset last_updated: {stj_dataset.last_updated})"
    )
```

### Refresh CLI (opt-in, audit-logged)

```bash
# Refresh via scraper (best effort)
revisor refresh-vault --source stj   # tenta scrape, se falhar mantém dataset atual
revisor refresh-vault --source stf
revisor refresh-vault --source all

# Manual import (autoritativo — após download oficial)
revisor import-dataset --source-pdf compendium-stj-2026.pdf --output-json bloco_vault/data/sumulas-stj.json
revisor import-dataset --source-csv stf-sv-2026.csv --output-json bloco_vault/data/sumulas-stf-vinculantes.json

# Validate dataset integrity
revisor validate-dataset bloco_vault/data/sumulas-stj.json
# → schema validation + hash verification + entry count check
```

Refresh process auto-updates `bloco_vault/data/DATASET-CHANGELOG.md`:

```markdown
## 2026-05-05 — Initial seed (Sprint 03 Phase 0)
- Source: manual extraction from STJ compendium 2026 + STF SV listing 2026
- STJ: 612 súmulas (números 1 a 643, with gaps for revogadas)
- STF SV: 58 súmulas vinculantes
- Method: seed (one-time bootstrap)
- Operator: @architect (Aria) via VAULT-FIX-01

## 2026-08-XX — Trimester refresh Q3 (placeholder)
- Source: STJ scraper (refresh-vault --source stj)
- Diff: +3 novas súmulas (644, 645, 646), 0 revogadas
- ...
```

---

## Consequences

### Positivos

- ✅ **Reliability:** app funciona out-of-the-box, zero dependency em scrapers que quebram
- ✅ **Speed:** vault populate em <1s (vs 5-10min de scrape)
- ✅ **LGPD:** zero runtime network calls para jurisprudência (preserva NFR-LGPD-01 mais estritamente)
- ✅ **Audit:** dataset versionado no git, commit-controlled, hash-verified
- ✅ **Reproducibility:** mesma versão do app = mesmo vault = mesmos vereditos (importante para audit jurídico)
- ✅ **Onboarding:** novo usuário não precisa "fix scraper if broken" como pre-requisite
- ✅ **Removes external sites dependency:** STJ/STF anti-bot, SSL cert chains, HTML structure changes — todos ficam fora do critical path

### Negativos

- ⚠️ **Dataset staleness risk:**
  - Mitigation 1: `last_updated` field exposto em UI ("Dataset atualizado em 2026-Q2")
  - Mitigation 2: trimester refresh SOP documented (`docs/sop-refresh-vault-dataset.md` — VAULT-FIX-01 entrega)
  - Mitigation 3: warning visual se dataset > 6 meses
- ⚠️ **Repo size aumenta:** ~200-500KB JSON minified
  - Mitigation: minified + Git pack (gzip) = ~80KB pack overhead. Aceitável.
- ⚠️ **Refresh manual:** não é automatic
  - Mitigation: SOP documentado + reminder em PROJECT-CHECKPOINT trimestral

### Neutros

- 🔵 **Initial seed effort:** maintainer (Eric) precisa one-time download + import inicial
  - Estimate: 1-2h primeira vez (depois trimester é 30-60min)
- 🔵 **Scrapers preservados:** ainda funcionam quando sites cooperarem; código mantido
- 🔵 **Schema evolution:** `schema_version: "1.0"` permite migração futura (Sprint 04+)

---

## Alternatives Considered

### Path A — Fix scrapers iterativo

**Estratégia:** Update parser STJ + bypass STF anti-bot + ongoing maintenance.

**Por que rejeitado:**
1. Sites externos mudam mais frequentemente que sumulas STJ/STF
2. AWS ELB anti-bot (STF) pode bloquear permanentemente — ELB lê padrões de requests
3. Effort ongoing alto (2-4h/trimestre = 8-16h/ano) sem agregar valor proporcional
4. App reliability dependente de fatores externos não controláveis
5. Smoke E2E test E AC-9 ficam frágeis — passam local mas falham em CI sem internet

### Path B — Playwright JS-rendered scraping

**Estratégia:** Headless Chromium browser para resolver JS-rendered SPAs + anti-bot.

**Por que rejeitado:**
1. Chromium dep ~150MB + playwright pip ~50MB → 200MB extra para single-user local app
2. Setup cumbersome (`playwright install chromium` requer admin/root em alguns OS)
3. Performance overhead (browser startup ~3s + page load + parsing)
4. STJ pode adicionar Cloudflare anti-bot que detecta Playwright também
5. Overkill: single-user local app não precisa scraping enterprise-grade

### Path C — Bundled dataset + optional refresh híbrido (ESCOLHIDO)

**Estratégia:** dataset commit-controlled + scrapers como ferramenta opt-in.

**Por que escolhido:** ver "Rationale ultrathink" acima.

---

## Migration Path from v0.2.0

1. **VAULT-FIX-01 implementation (Neo):**
   - Criar `bloco_vault/data_schema.py` (Pydantic models)
   - Criar `bloco_vault/data/sumulas-stj.json` + `sumulas-stf-vinculantes.json` (initial seed)
   - Refactor `bloco_vault/populate.py` para idempotent population from bundled
   - Adicionar CLI commands `refresh-vault` + `import-dataset` + `validate-dataset`
   - Update `bloco_interface/cli.py` para wire CLI subcommands
   - Tests: unit (schema validation, idempotent population) + integration (E2E populate)

2. **App startup change (parte de VAULT-FIX-01):**
   - FastAPI lifespan: `populate_vault_if_needed()` em startup (antes de aceitar requests)
   - Logging: `Vault populated from bundled (last_updated: X)` OR `Vault already populated, skipping`

3. **Smoke E2E real validation:**
   - Pós-VAULT-FIX-01 push: vault populated automaticamente
   - AC-9 retroativo UI-1: smoke browser real funcionará (não fallback mock)
   - Validates `await revisar_contrato(...)` end-to-end com jurisprudência real

4. **Backward compat v0.2.0 → v0.3.0:**
   - Existing vault.db com 0 entries: detectado, re-populated from bundled
   - Existing vault.db com entries scraped (caso raro de quem teve scrape funcionando): NÃO sobrescrever (idempotent count > 0)
   - Reset path: `revisor reset-vault` deletes vault.db → próxima startup repopula bundled

---

## Open Questions (resolver no review Eric)

1. **Initial seed source:** Eric quer extrair de:
   - (a) Compendium PDF oficial STJ (manual extraction, ~2h)
   - (b) Dataset 3rd-party reusable (e.g., projetos open-source jurídicos brasileiros) com attribution
   - (c) One-shot scrape working hoje (STJ HTTP 200) + manual STF (anti-bot block)
   - **Aria recomenda:** (c) — usar momento que STJ está acessível para grab inicial + manual STF; depois bundled fica como autoridade.

2. **Refresh cadence:** trimestral é OK ou Eric prefere outro? (mensal/semestral)
   - **Aria recomenda:** trimestral — alinha com publicação típica STJ/STF + balance overhead vs staleness.

3. **Dataset signing:** GPG-signed commits para refresh updates?
   - **Aria recomenda:** opt-in para futuro (Sprint 05+). MVP usa hash_sha256 no schema + commit message audit.

4. **CSP para área da súmula (campo `area`):**
   - Atualmente Literal de 8 valores. STJ classifica de forma mais granular?
   - **Aria recomenda:** começar com 8 valores; expandir se classificação real STJ for mais granular (Sprint 04+).

---

## Decision Status

**Status: ✅ ACCEPTED — Eric sessão 86, 2026-05-05.**

Eric aceitou Path C com recomendações Aria default (4 open questions resolvidas):
1. Initial seed: (c) one-shot scrape working hoje + manual STF
2. Refresh cadence: trimestral
3. Dataset signing: opt-in futuro Sprint 05+ (MVP usa hash_sha256)
4. Área classification: 8 valores Literal MVP

**Próximos passos pós-accept:**
1. ✅ ADR-012 status accepted (este commit)
2. ⏳ Aria escreve ADR-011 (Auto-Ollama Lifecycle) — em progresso
3. ⏳ Após ADR-011 accepted: Aria atualiza ADR-INDEX + emit handoff @sm
4. ⏳ @sm draft VAULT-FIX-01 + OLLAMA-MGR-01 stories (paralelas)

---

*ADR-012 — Aria @architect (sessão 86, 2026-05-05) · Sprint 03 Phase 0 · Vault Data Bundling Strategy · Path C bundled + optional refresh híbrido · resolves STJ/STF scrapers fragility · unblocks AC-9 smoke E2E real*

— Aria, arquitetando o futuro com dados que não dependem do humor dos sites externos 🏗️
