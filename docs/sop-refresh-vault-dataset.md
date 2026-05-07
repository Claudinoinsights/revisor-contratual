# SOP-004 — Refresh do Bundled Dataset (Vault Súmulas STJ + STF SV)

> **Versão:** 1.0 · **Data:** 2026-05-05 · **Owner:** maintainer Revisor Contratual
> **Reference:** ADR-012 (Vault Data Bundling Strategy) · Story VAULT-FIX-01

---

## 1. Razão

Per ADR-012, a fonte canônica de jurisprudência runtime é o **bundled dataset** committed em `bloco_vault/data/`:

- `sumulas-stj.json` — Súmulas STJ schema-validated
- `sumulas-stf-vinculantes.json` — Súmulas Vinculantes STF
- `DATASET-CHANGELOG.md` — audit trail per refresh

Esses JSONs são populados em `vault.db` automaticamente via FastAPI lifespan (idempotent — `bloco_vault/populate.py::populate_vault_if_needed`). Scrapers (`bloco_vault/scrapers/*`) são preservados como **ferramenta opt-in** mas não rodam em runtime (frágeis: STJ WAF + STF AWS ELB anti-bot).

**Quando refresh é necessário:**

- ✅ **Trimestral** (recomendado): STJ/STF publicam novas súmulas e revogações periodicamente
- ✅ **Sob demanda**: STJ/STF emitiu nova súmula relevante para CDC PF Veículos (target use case)
- ✅ **Pré-produção**: maintainer DEVE fazer one-shot bulk import oficial antes de uso real (seed atual cobre apenas ~1.6% STJ + ~8.6% STF SV — PROVISIONAL)

---

## 2. Caminhos de refresh (3 opções, em ordem de preferência)

### Path A — `import-dataset` via PDF compendium oficial (autoritativo, recomendado)

Maintainer baixa compendium oficial, parseia, valida, commita. Mais robusto contra anti-bot.

**Links oficiais:**

- STJ: https://www.stj.jus.br/publicacaoinstitucional/index.php/sumstj
- STF SV: https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp

```bash
# 1. Download compendium PDF oficial (manual via browser)
#    Salvar em ~/Downloads/compendium-stj-2026.pdf

# 2. Import via CLI (parser regex + Pydantic schema validation + hash sha256)
python -m bloco_interface.cli import-dataset \
    --source-pdf ~/Downloads/compendium-stj-2026.pdf \
    --output-json bloco_vault/data/sumulas-stj.json \
    --source stj

# 3. Repetir para STF SV
python -m bloco_interface.cli import-dataset \
    --source-pdf ~/Downloads/compendium-stf-sv-2026.pdf \
    --output-json bloco_vault/data/sumulas-stf-vinculantes.json \
    --source stf

# 4. ATENÇÃO: campos data_aprovacao + revogada ficam None — maintainer preenche manualmente
#    Editar JSONs em editor para incluir essas datas (consultar PDF original)
```

### Path B — `refresh-vault` via scraper best-effort (opt-in)

Tenta scraping via `bloco_vault/scrapers/*`. Falha graciosamente se WAF/anti-bot bloqueia (exit 0, bundled preservado).

```bash
# Tenta refresh via scrapers — log warning se falhar
python -m bloco_interface.cli refresh-vault --source all
# Output: graceful HTTP 4xx/5xx → "bundled preservado", exit_code=0

# NOTA: refresh-vault NÃO sobrescreve bundled JSON em success — scrapers retornam
# JurisprudenciaItem (rich schema) enquanto bundled segue SumulaSTJ/STF (lean schema).
# Adapter scraper→bundled é tech debt MEDIUM (TD-VAULT-SCRAPER-OUTPUT-TO-BUNDLED-ADAPTER).
# Por ora, refresh-vault apenas valida disponibilidade upstream — review manual segue Path A.
```

### Path C — Dataset 3rd-party open-source (fallback emergencial)

Se Path A indisponível (PDF download bloqueado) e Path B inviável (scrapers broken):

1. Buscar repositórios GitHub com datasets jurídicos (e.g., "stf sumulas vinculantes brasileiro json")
2. Verificar license compatível (MIT/Apache/CC-BY-SA)
3. Validar via `validate-dataset` CLI antes de commit
4. **OBRIGATÓRIO:** documentar attribution em `DATASET-CHANGELOG.md` entry

---

## 3. Validation (sempre antes de commit)

```bash
python -m bloco_interface.cli validate-dataset bloco_vault/data/sumulas-stj.json
# Expected: PASS — N entries schema-valid + hash verified (N/N)

python -m bloco_interface.cli validate-dataset bloco_vault/data/sumulas-stf-vinculantes.json
# Expected: PASS

# Se FAIL → corrigir JSON manualmente; NÃO commitar dataset broken
```

---

## 4. Audit (DATASET-CHANGELOG.md entry)

Adicionar entry no topo de `bloco_vault/data/DATASET-CHANGELOG.md`:

```markdown
## YYYY-MM-DD — Refresh trimestral (Sprint XX / [maintainer])

### Conteúdo
- **STJ:** N súmulas (delta vs anterior: +X / -Y revogadas)
- **STF SV:** N súmulas vinculantes (delta vs anterior: +X / -Y)

### Method
- Path: A (PDF oficial) / B (scraper opt-in) / C (3rd-party com attribution)
- Source: [link PDF OR repo URL com hash commit]
- Operator: [maintainer name + role]

### Hash verification
- ✅ validate-dataset PASS em ambos JSONs
```

---

## 5. Commit + tag (opcional)

```bash
git add bloco_vault/data/sumulas-*.json bloco_vault/data/DATASET-CHANGELOG.md

git commit -m "chore(vault): refresh trimestral STJ + STF SV YYYY-MM-XX [maintainer]

- STJ: N súmulas (delta +X/-Y)
- STF SV: N súmulas vinculantes (delta +X/-Y)
- Method: Path A (PDF oficial) [or whichever path used]
- validate-dataset: PASS

Cross-ref: ADR-012 (Vault Data Bundling Strategy)"

# Opcional — tag para marcar marco trimestral
git tag -a vault-refresh-YYYY-Q1 -m "Vault dataset refresh Q1 YYYY"
```

---

## 6. Trimester reminder (operacional)

Para evitar dataset staleness, maintainer DEVE checar:

- [ ] Trimestralmente: rodar Path A para STJ + STF SV
- [ ] Trimestralmente: validar com `validate-dataset` ambos JSONs
- [ ] Documentar entry em `DATASET-CHANGELOG.md`
- [ ] Atualizar `last_updated` no frontmatter do CHANGELOG

> **Lembrete em `governance/PROJECT-CHECKPOINT.md`:** próximo refresh agendado para `[YYYY-Q+1]`.

---

## 7. Cross-references

- **ADR-012:** `governance/architecture/adr/adr-012-vault-data-bundling.md` — decisão arquitetural
- **DATASET-CHANGELOG:** `bloco_vault/data/DATASET-CHANGELOG.md` — audit trail histórico
- **Pydantic schemas:** `bloco_vault/data_schema.py` — `SumulaSTJ` + `SumulaVinculanteSTF` + `VaultDataset`
- **Populate logic:** `bloco_vault/populate.py` — idempotent `populate_vault_if_needed`
- **CLI commands:** `bloco_interface/cli.py` — `refresh-vault`, `import-dataset`, `validate-dataset`
- **Story:** `governance/stories/VAULT-FIX-01-vault-data-bundling.md`

---

*SOP-004 — Maintainer documentation per ADR-012 + Story VAULT-FIX-01 (Sprint 03 Phase 0)*
