# DATASET-CHANGELOG — Vault Bundled Data

> **Per ADR-012 (Vault Data Bundling Strategy)** — audit trail per refresh manual OR scrape.
> Schema canônico: `bloco_vault/data_schema.py` (`SumulaSTJ`, `SumulaVinculanteSTF`, `VaultDataset` `schema_version: "1.0"`).

---

## ⚠️ INITIAL SEED PROVISIONAL — 2026-05-05 (Sprint 03 Phase 0 / Story VAULT-FIX-01)

**Status:** ⚠️ **PROVISIONAL — NÃO USAR EM PRODUÇÃO REAL SEM ONE-TIME BULK IMPORT**

### Conteúdo

- **STJ:** 5 sumulas representativas de domínio público (numero 297, 380, 381, 382, 541) — relevantes para CDC PF Veículos (target use case do produto)
- **STF SV:** 5 súmulas vinculantes representativas de domínio público (numero 7, 25, 27, 28, 32)

### Por que é provisional

Esta seed é **demonstrativa** do pattern arquitetural ADR-012 (bundled dataset + schema-validated + hash audit). Não substitui o compendium oficial completo:

- STJ tem ~600 sumulas oficiais ativas
- STF SV tem ~58 súmulas vinculantes oficiais

A seed atual cobre apenas **~1.6% do STJ + ~8.6% do STF SV**.

### Por que não foi feito scrape completo

Investigação Sprint 03 Phase 0 (sessão 86, 2026-05-05):

- **STJ `/sumulas`** — anti-bot WAF intermitente: rejeita requests com `Mozilla/5.0 (RevisorContratual/0.3)`, `Mozilla/5.0 Chrome/120...`, requests sem User-Agent (HTTP 404 OR 200 inconsistente). Apenas `Mozilla/5.0` simples passa, mas Request Rejected via WAF retorna ainda assim. HTML mudou estrutura (`class="sumula"` não existe mais).
- **STF `/sumulas-vinculantes`** — anti-bot AWS ELB (`Server: awselb/2.0`) + SSL cert chain issue: HTTP 403 mesmo com `verify=False` + custom User-Agent.

ADR-012 escolheu **Path C — bundled dataset híbrido** justamente por essa fragility. Scrapers ficam como ferramenta opt-in `revisor refresh-vault` (best-effort, falha graciosa).

### Maintainer action required (Eric) PRE-PRODUÇÃO

Antes de uso real em escritório, **maintainer DEVE fazer one-time bulk import** seguindo SOP:

```bash
# 1. Download compendium oficial STJ (mais recente)
# Link: https://www.stj.jus.br/publicacaoinstitucional/index.php/sumstj
# Format: PDF compendium das sumulas

# 2. Manual import via CLI (Phase D entrega)
python -m bloco_interface.cli import-dataset \
  --source-pdf path/to/compendium-stj-2026.pdf \
  --output-json bloco_vault/data/sumulas-stj.json

# 3. Validate
python -m bloco_interface.cli validate-dataset bloco_vault/data/sumulas-stj.json

# 4. Repeat para STF SV
# Link STF: https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp

# 5. Commit + tag
git add bloco_vault/data/sumulas-*.json
git commit -m "chore(vault): bulk import sumulas STJ + STF SV oficial 2026-05-XX [maintainer]"
```

**SOP completo:** `docs/sop-refresh-vault-dataset.md` (Phase E entrega VAULT-FIX-01).

### Audit details

| Field | Valor |
|---|---|
| Method | seed (one-time bootstrap, MARKED PROVISIONAL) |
| Source | Domínio público (jurisprudência STJ/STF é livre uso conforme Lei 9.610/98 art. 8º IV) |
| Operator | @dev (Neo) via Story VAULT-FIX-01 (Sprint 03 Phase 0) |
| Schema version | 1.0 |
| Hash verification | sha256 per entry, validado via Pydantic |
| ADR predecessor | ADR-012 (Accepted Eric 2026-05-05) |

### Garantias

- ✅ Schema-valid (Pydantic `VaultDataset.model_validate()` PASS)
- ✅ Hashes sha256 corretos (computed via hashlib.sha256 from texto)
- ✅ Pattern arquitetural ADR-012 demonstrado end-to-end
- ⚠️ NÃO é coverage exhaustive — maintainer DEVE bulk import oficial pre-produção
- ⚠️ Sumulas selecionadas refletem subset CDC PF Veículos (não representam sumulas STJ/STF em geral)

---

## Histórico de refresh

> Próximas entries documentarão refresh manual (scraper opt-in OR import-dataset CLI) por trimestre OR sob demanda STJ/STF publica nova súmula.

*Nenhum refresh manual ainda realizado.*

---

## Schema migration history

> Schema_version `"1.0"` em uso desde initial seed. Migrations futuras documentadas aqui (Sprint 04+).

*Schema 1.0 stable.*

---

*DATASET-CHANGELOG — Story VAULT-FIX-01 (Sprint 03 Phase 0) — Neo @dev sessão 86 2026-05-05*
