# SOP-002 — Populando o Vault Jurisprudencial

> **Versão:** 1.0 · **Data:** 2026-05-04 · **Owner:** equipe operacional Revisor Contratual

---

## 1. Razão

O vault jurisprudencial é o repositório local sqlite-vec que armazena súmulas, súmulas vinculantes e jurisprudência usados pela busca híbrida (BM25 lexical + vetorial). Sem o vault populado, o pipeline `revisor revisar` falha com `VaultEmptyError` quando tenta recuperar docs para as personas Advogado e Economista.

**Quando popular:**

- ✅ Primeiro setup (após `init-audit`)
- ✅ Atualização periódica (mensal recomendado — STJ publica novas súmulas)
- ✅ Após nova STORY que adiciona scrapers (TJBA, TJSP, etc — futuro)
- ❌ NÃO popular antes de cada `revisor revisar` (vault é persistente)

---

## 2. Fontes suportadas

A whitelist de hosts é **hardcoded** (`bloco_vault/scrapers/base.py:13`) e enforça NFR-LGPD-01:

```python
ALLOWED_HOSTS: frozenset[str] = frozenset({"www.stj.jus.br", "www.stf.jus.br"})
```

Qualquer tentativa de scrape fora desses hosts levanta `ScraperHostNotAllowed`. **Alterar a whitelist exige ADR formal** — não é decisão de runtime.

| Fonte | Tipo extraído | URL |
|-------|---------------|-----|
| **STJ** | Súmulas (binding=True ou False conforme tipo) | `https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/...` |
| **STF** | Súmulas Vinculantes (binding=True, peso_vinculacao=5) | `https://portal.stf.jus.br/jurisprudencia/...` |

Por que **só STJ e STF no MVP:**
- STF SVs têm o **maior peso vinculante** (matriz NFR-GOV-01)
- STJ unifica jurisprudência infra-constitucional bancária
- TJs estaduais (BA, SP, MG, RJ, RS) ficam para STORY pós-MVP — escopo limitado evita explosão de scope creep

---

## 3. Comando

```
revisor populate-vault [OPTIONS]
```

### Flags

| Flag | Default | Descrição |
|------|---------|-----------|
| `--vault-db PATH` | `~/.local/share/revisor-contratual/vault.db` | Caminho do sqlite vault |
| `--source {stj\|stf\|all}` | `all` | Quais fontes scrapear |
| `--dry-run` | `False` | Lista o que seria inserido, sem persistir |
| `--zero-embeddings` | `True` (MVP) | Usa vetores zero (sem sentence-transformers) |
| `-h, --help` | — | Mostra ajuda completa |

### Exemplos

```bash
# Setup inicial completo (STJ + STF) — MVP default
revisor populate-vault --source all
# → ℹ️  Scrapeando STJ...
# →   STJ: 64 items extraídos
# → ℹ️  Scrapeando STF...
# →   STF: 58 items extraídos
# → ✅ Total persistidos: 122 items

# Apenas STF (atualização rápida)
revisor populate-vault --source stf

# Dry-run — verificar conectividade e parsing antes de persistir
revisor populate-vault --source stj --dry-run
# → ✅ Total extraídos (dry-run): 64 items

# Embeddings reais (requer sentence-transformers instalado)
revisor populate-vault --source all --no-zero-embeddings
```

---

## 4. Cenário A — Sem sentence-transformers (MVP default)

**Estado:** `--zero-embeddings=True` (default). Todos os documentos recebem vetor `[0.0] * 768`.

**Consequências:**

| Aspecto | Comportamento |
|---------|--------------|
| Busca BM25 (lexical) | ✅ Funciona normalmente — tokeniza ementa + texto, ranqueia por TF-IDF |
| Busca vetorial (semântica) | ⚠️ Degraded — todos os docs têm distância 0.0 (zero-vector); ranking vetorial vira aleatório |
| RRF fusão (BM25 + vetorial) | ⚠️ Reduzido a BM25 puro (componente vetorial colapsa) |
| Pipeline `revisar` | ✅ Funciona — top-K ainda é retornado, apenas com qualidade reduzida em queries semanticamente sutis |

**Quando isso é aceitável:**
- Setup inicial / smoke tests
- Disco com pouco espaço (sentence-transformers + Legal-BERTimbau ~500MB)
- Ambiente offline sem possibilidade de baixar modelos

**Recomendação MVP:** comece com `--zero-embeddings`, valide o pipeline E2E, depois desligue se quiser busca semântica completa.

---

## 5. Cenário B — Com sentence-transformers (busca semântica completa)

**Pré-requisito:** `pip install sentence-transformers` (~500MB inicial; modelo Legal-BERTimbau-sts-base é baixado na primeira chamada).

```bash
# Instalar lib
pip install sentence-transformers

# Popular com embeddings reais
revisor populate-vault --source all --no-zero-embeddings
# → ℹ️  Carregando sentence-transformers neuralmind/bert-base-portuguese-cased...
# →   (primeira chamada baixa modelo ~500MB)
# → ℹ️  Scrapeando STJ...
# →   STJ: 64 items extraídos (gerando embeddings 768d)...
# → ✅ Total persistidos: 122 items
```

**Resultados:**

| Aspecto | Comportamento |
|---------|--------------|
| Busca BM25 | ✅ Igual ao Cenário A |
| Busca vetorial | ✅ Funciona — distância cosseno entre query e docs faz sentido semanticamente |
| RRF fusão | ✅ Pondera ambos — query "capitalização anual" recupera doc com "anatocismo mensal" |

---

## 6. Frequência recomendada

| Periodicidade | Quando aplicar |
|---------------|----------------|
| **Mensal** | STJ publica novas súmulas; advogado quer manter o vault atualizado |
| **Trimestral** | Equipes que toleram leve defasagem; STF SVs mudam pouco |
| **Sob demanda** | Após Eric/operador identificar súmula ausente que deveria estar no vault |
| **NÃO recomendado: a cada revisão** | Custo de rede desnecessário (vault é persistente sqlite) |

`populate-vault` é **idempotente por id_doc**: se um doc já existe (`STJ-S539`), o insert é pulado silenciosamente (sqlite IntegrityError capturado). Re-executar é seguro.

---

## 7. Troubleshooting

### Erro: `ScraperHostNotAllowed`

```
ScraperHostNotAllowed: Host 'evil.com' fora da whitelist NFR-LGPD-01 ['www.stf.jus.br', 'www.stj.jus.br']. Alterar whitelist requer ADR.
```

**Causa:** alguém tentou injetar URL fora da whitelist.

**Ação:** investigue origem (config, mock de teste, env var). Whitelist é frozenset constante — nunca deveria falhar em produção.

---

### Erro: `ScraperParseError`

```
ScraperParseError: STJ HTML retornou 0 items — estrutura possivelmente mudou
```

**Causa:** STJ alterou layout HTML; scraper precisa ser atualizado.

**Ação:**
1. Tente `--dry-run` para confirmar que é parsing, não rede
2. Inspecione `tests/fixtures/scraper_html/stj_sumulas_min.html` — fixture existe?
3. Abra issue no monorepo solicitando atualização do scraper
4. Workaround temporário: use vault de outro ambiente (`scp vault.db origem:dest`)

---

### Erro de rede (timeout, ConnectionError)

```
httpx.ConnectError: [Errno -3] Temporary failure in name resolution
```

**Causa:** sem conectividade a `www.stj.jus.br` ou `www.stf.jus.br`.

**Ação:**
1. Verifique conectividade básica: `curl -I https://www.stj.jus.br`
2. Verifique proxy/firewall corporativo (whitelist NFR-LGPD-01 pode requerer config infra)
3. `populate-vault` NÃO retry automático em network errors — refaça o comando após restaurar conexão
4. Se urgente: copie `vault.db` populado de outro ambiente

---

### Erro: `OperationalError: no such table jurisp_vec`

```
sqlite3.OperationalError: no such table: jurisp_vec
```

**Causa:** vault.db existe mas schema não foi criado (init_vault não rodou).

**Ação:** delete `vault.db` e re-execute `populate-vault` — o schema é criado automaticamente em `open_vault`.

---

### Vault corrompido / queries retornam 0 sempre

**Diagnóstico:**

```bash
# Inspecionar contagem
sqlite3 ~/.local/share/revisor-contratual/vault.db "SELECT COUNT(*) FROM jurisprudencia;"

# Listar primeiros 5
sqlite3 ~/.local/share/revisor-contratual/vault.db "SELECT id_doc, court_id, numero FROM jurisprudencia LIMIT 5;"
```

Se `COUNT = 0` mas `populate-vault` reportou items inseridos: provavelmente schema antigo. Recovery:

```bash
# Backup primeiro
mv vault.db vault.db.broken

# Re-popular do zero
revisor populate-vault --source all
```

---

## 8. Anti-patterns

| Anti-pattern | Por que evitar |
|--------------|---------------|
| ❌ Modificar `vault.db` manualmente via SQL | Schema sqlite-vec exige `INSERT INTO jurisp_vec` em sincronia com `jurisprudencia` row table; manual = inconsistência |
| ❌ Adicionar host à whitelist via env var | Whitelist é frozenset constante por design (NFR-LGPD-01) — alterar exige ADR |
| ❌ Rodar `populate-vault` em paralelo (múltiplos processos) | sqlite-vec não é multi-writer; locks podem causar corruption |
| ❌ Compartilhar `vault.db` entre máquinas via sync (Dropbox, OneDrive) | sqlite-vec usa virtual tables; sync incremental pode quebrar |

---

## 9. Validação pós-populate

Confirme que o vault está utilizável:

```bash
# Smoke: revisão de PDF teste
revisor revisar tests/fixtures/contrato_minimo.pdf \
  --uf BA --data-assinatura 2024-03-15

# Se retornar sem VaultEmptyError → vault OK
```

Esperado: pipeline executa todos os 7 steps (parsing → cálculo → BACEN → vault busca → personas → juiz → audit) e emite VeredictoJuiz.

---

## 10. Referências técnicas

- `bloco_vault/scrapers/base.py:13` — `ALLOWED_HOSTS` frozenset
- `bloco_vault/scrapers/stj_sumulas.py` — scraper STJ (BeautifulSoup `class~="sumula"`)
- `bloco_vault/scrapers/stf_sumulas_vinculantes.py` — scraper STF SV
- `bloco_vault/repository.py:insert_jurisprudencia` — persistência sqlite-vec
- `bloco_vault/busca.py:buscar_hibrida` — RRF k=60 (BM25 + vetorial)
- ADR-007 / ADR-008 — decisões arquiteturais sqlite-vec + scrapers

---

*SOP-002 v1.0 — Populando o Vault Jurisprudencial · STORY 14 · Sessão 76 · Neo (@dev)*
