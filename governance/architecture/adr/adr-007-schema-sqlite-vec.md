---
type: adr
id: "ADR-007"
title: "Schema sqlite-vec final + estratégia de índices"
status: superseded
date: "2026-05-01"
superseded_date: "2026-05-07"
domain: "vault-rag"
decision_makers: ["@architect (Aria)"]
supersedes: null
superseded_by: "ADR-017"
absorves: []
references_dp:
  - "DP-08 (load test sqlite-vec obrigatório antes de release MVP)"
related_to:
  - "FR-RAG-01..06 (vault, busca, multi-UF, benchmark)"
  - "NFR-PERF-03 (latência RAG ≤500ms p95)"
  - "NFR-GOV-01 (matriz peso_vinculacao canônica)"
project: revisor-contratual
sprint: "01"
etapa: "2.0"
tags:
  - project/revisor-contratual
  - adr
  - sqlite-vec
  - rag
  - vault
  - superseded
---

> ⚠️ **SUPERSEDED** (2026-05-07) — Este ADR foi substituído por [ADR-017](adr-017-multi-tenant-isolation-rls.md).
> Razão: Sprint 04 pivot SaaS multi-tenant exige PostgreSQL + RLS + pgvector. SQLite single-tenant
> é incompatível com isolamento entre escritórios cliente. Mantido para contexto histórico do
> design Sprint 03 single-tenant local.


# ADR-007 — Schema sqlite-vec final + estratégia de índices

```
[@architect · Aria (Visionary)] — etapa 2.0 · ADR-007 schema sqlite-vec
SPRINT: 01 · ETAPA: 2.0 · DOMÍNIO: SoftwareDev/legaltech
```

## Contexto

A arquitetura D-LEAN substituiu Qdrant por sqlite-vec (extensão SQLite) para o vault de jurisprudência. PRD v1.0.2 FR-RAG-01 enriqueceu o schema na re-revisão (Smith F-CRIT-03):

Campos: `court_id`, `binding`, `peso_vinculacao` (1-5), `legal_topic_principal`, `modalidade_relacionada` (JSON array), `ano_julgamento`, `ementa`, `texto_completo`, `embedding` (BLOB), `indexed_at`, **`vigente_em` (date|null), `superseded_by` (id_doc|null), `data_ultima_validacao` (date)**.

Vault inicial: ~3.000 docs (STF Súmulas Vinculantes ~58 + STF Repercussão Geral ~1.300 + STJ Súmulas ~671 + STJ Temas Repetitivos ~1.300 + TJBA acórdãos revisional CDC ~300).

NFR-PERF-03: latência ≤500ms p95 para query top-K=10 no laptop alvo (i5-10300H 16GB sem GPU).

DP-08 (do Smith F-HIGH-08): sqlite-vec é v0.1 — load test obrigatório antes do release MVP para validar maturidade.

Aria precisa decidir: schema final, índices SQL, estratégia de embedding, e como organizar busca híbrida BM25 + dense.

## Decisão

**Schema final em SQLite com 2 tabelas + índices estratégicos:**

```sql
-- bloco_vault/database/schema.sql

-- Tabela principal: metadados + texto + filtros
CREATE TABLE IF NOT EXISTS jurisprudencia (
    id_doc                  TEXT PRIMARY KEY,                    -- ex: "STJ-S539" ou "STF-SV4"
    court_id                TEXT NOT NULL CHECK(court_id IN
                              ('STF', 'STJ', 'TST',
                               'TJAC','TJAL','TJAP','TJAM','TJBA','TJCE','TJDF','TJES','TJGO',
                               'TJMA','TJMT','TJMS','TJMG','TJPA','TJPB','TJPR','TJPE','TJPI',
                               'TJRJ','TJRN','TJRS','TJRO','TJRR','TJSC','TJSP','TJSE','TJTO')),
    tipo_doc                TEXT NOT NULL CHECK(tipo_doc IN
                              ('SUMULA_VINCULANTE','SUMULA','REPERCUSSAO_GERAL',
                               'TEMA_REPETITIVO','ACORDAO','LEI','MEDIDA_PROVISORIA','DECRETO')),
    numero                  TEXT NOT NULL,                       -- ex: "539" ou "247"
    binding                 INTEGER NOT NULL CHECK(binding IN (0, 1)),
    peso_vinculacao         INTEGER NOT NULL CHECK(peso_vinculacao BETWEEN 1 AND 5),
    legal_topic_principal   TEXT NOT NULL,                       -- taxonomia controlada
    modalidade_relacionada  TEXT NOT NULL,                       -- JSON array
    ano_julgamento          INTEGER NOT NULL,
    ementa                  TEXT NOT NULL,
    texto_completo          TEXT NOT NULL,
    indexed_at              TEXT NOT NULL,                       -- ISO 8601
    -- v1.0.2 — vigência temporal (Smith F-CRIT-03)
    vigente_em              TEXT,                                -- ISO date | null=vigente
    superseded_by           TEXT REFERENCES jurisprudencia(id_doc),
    data_ultima_validacao   TEXT NOT NULL                        -- ISO date
);

-- Índices estratégicos (decididos via análise de queries reais)
CREATE INDEX IF NOT EXISTS idx_juris_court_binding
  ON jurisprudencia(court_id, binding);              -- filtro principal FR-RAG-02
CREATE INDEX IF NOT EXISTS idx_juris_vigencia
  ON jurisprudencia(vigente_em);                     -- filtro temporal FR-RAG-02
CREATE INDEX IF NOT EXISTS idx_juris_topic
  ON jurisprudencia(legal_topic_principal);          -- filtro por tema
CREATE INDEX IF NOT EXISTS idx_juris_peso
  ON jurisprudencia(peso_vinculacao DESC);           -- sort por relevância vinculante

-- Full-text search BM25 (FTS5 nativo SQLite)
CREATE VIRTUAL TABLE IF NOT EXISTS jurisprudencia_fts USING fts5(
    id_doc UNINDEXED,
    ementa,
    texto_completo,
    tokenize = 'unicode61 remove_diacritics 2'  -- normaliza acentos PT-BR
);

-- Tabela de embeddings (sqlite-vec)
CREATE VIRTUAL TABLE IF NOT EXISTS jurisprudencia_vec USING vec0(
    id_doc TEXT PRIMARY KEY,
    embedding FLOAT[768]                          -- Legal-BERTimbau-sts-base = 768 dims
);

-- Trigger: manter FTS sincronizado com tabela principal
CREATE TRIGGER IF NOT EXISTS juris_ai AFTER INSERT ON jurisprudencia BEGIN
    INSERT INTO jurisprudencia_fts(id_doc, ementa, texto_completo)
    VALUES (new.id_doc, new.ementa, new.texto_completo);
END;
CREATE TRIGGER IF NOT EXISTS juris_au AFTER UPDATE ON jurisprudencia BEGIN
    UPDATE jurisprudencia_fts SET ementa=new.ementa, texto_completo=new.texto_completo
    WHERE id_doc=new.id_doc;
END;
CREATE TRIGGER IF NOT EXISTS juris_ad AFTER DELETE ON jurisprudencia BEGIN
    DELETE FROM jurisprudencia_fts WHERE id_doc=old.id_doc;
END;
```

### Pipeline de busca híbrida (FR-RAG-02)

```python
# bloco_vault/busca.py

def buscar_hibrida(
    query: str,
    uf_contrato: str,
    data_assinatura_contrato: str,  # ISO date
    top_k: int = 10,
    binding_relax: bool = False
) -> list[JurisprudenciaItem]:
    """
    Pipeline híbrido BM25 + dense embedding com fusion RRF.
    Filtros estritos: court_id, binding, vigência temporal.
    """
    # 1. Embedding da query
    query_emb = EMBEDDER.encode(query, convert_to_tensor=False).tolist()

    # 2. Filtros WHERE construídos dinamicamente
    courts = ('STF', 'STJ', f'TJ{uf_contrato}')
    binding_filter = "binding = 1" if not binding_relax else "binding IN (0, 1)"
    vigencia_filter = f"(vigente_em IS NULL OR vigente_em > '{data_assinatura_contrato}')"

    # 3. Busca dense (sqlite-vec)
    dense_results = conn.execute(f"""
        SELECT j.id_doc, vec_distance_cosine(v.embedding, ?) AS dist
        FROM jurisprudencia_vec v
        JOIN jurisprudencia j ON j.id_doc = v.id_doc
        WHERE j.court_id IN ({','.join(['?']*len(courts))})
          AND {binding_filter}
          AND {vigencia_filter}
        ORDER BY dist ASC
        LIMIT ?
    """, [query_emb, *courts, top_k * 2]).fetchall()

    # 4. Busca sparse (BM25 via FTS5)
    sparse_results = conn.execute(f"""
        SELECT j.id_doc, bm25(jurisprudencia_fts) AS rank
        FROM jurisprudencia_fts
        JOIN jurisprudencia j ON j.id_doc = jurisprudencia_fts.id_doc
        WHERE jurisprudencia_fts MATCH ?
          AND j.court_id IN ({','.join(['?']*len(courts))})
          AND {binding_filter}
          AND {vigencia_filter}
        ORDER BY rank
        LIMIT ?
    """, [query, *courts, top_k * 2]).fetchall()

    # 5. Fusion via Reciprocal Rank Fusion (RRF)
    fused_ids = _rrf_fusion(dense_results, sparse_results, k=60)[:top_k]

    # 6. Hidratar metadados completos
    return [_get_doc(id_doc) for id_doc in fused_ids]
```

### Estratégia de DPI/embedding

- **Embeddings:** Legal-BERTimbau-sts-base (768 dims, ~250MB) — pré-treinado em corpus jurídico português
- **Chunking:** documento INTEIRO embedded (não chunk) — súmulas/temas são curtos (50-500 palavras); acórdãos longos usam summary-based context enrichment (arXiv 2510.06999)
- **Normalização:** L2 normalize antes de armazenar para usar cosine distance eficientemente
- **Storage:** FLOAT[768] = 3KB por embedding × 3000 docs = ~9MB (cabe em RAM facilmente)

## Razão

- **SQLite + FTS5 + sqlite-vec é stack coerente:** zero processos adicionais, transações atômicas
- **Índices compostos (court_id, binding):** filtro principal de FR-RAG-02 fica O(log n) — testado conceitualmente
- **FTS5 com `unicode61 remove_diacritics 2`:** "veículo" matches "veiculo"; importante para PT-BR
- **vec0 (sqlite-vec) suporta cosine distance nativa:** sem necessidade de cálculo Python
- **RRF fusion é simples e robusto:** padrão industry para hybrid search; k=60 é hiperparâmetro consagrado
- **Triggers garantem consistência:** FTS sempre em sync com tabela principal
- **Documento inteiro embedded (não chunks):** súmulas/temas são curtos por natureza; acórdãos longos usam summary
- **Foreign key `superseded_by`:** integridade referencial validada por SQLite (FR-RAG-01 AC v1.0.2)

## Alternativas Consideradas

### Alt 1 — Manter Qdrant
- **Prós:** mais maduro que sqlite-vec
- **Contras:** **viola D-LEAN** (processo separado, +500MB RAM)
- **Rejeitada:** decisão arquitetural já tomada na refatoração D-LEAN

### Alt 2 — Chroma (embeddings DB lightweight)
- **Prós:** Python-nativo
- **Contras:** ainda exige processo separado em produção; menos controle SQL; menos maduro que SQLite
- **Rejeitada:** sqlite-vec dá controle SQL nativo

### Alt 3 — FAISS (Facebook AI Similarity Search)
- **Prós:** muito rápido para vetores
- **Contras:** apenas similarity (sem metadados); precisaria sincronizar com SQLite separado; complexidade
- **Rejeitada:** sqlite-vec integra naturalmente

### Alt 4 — Chunking de acórdãos longos
- **Prós:** melhor recall em docs >2000 palavras
- **Contras:** complexidade de re-ranking + duplicação de doc IDs; pequena fração do vault são docs longos
- **Rejeitada para MVP:** revisitar se DP-09 benchmark mostrar problema de recall

### Alt 5 — Embedding por chunk + pooling
- **Prós:** semantic richness
- **Contras:** complexidade alta para ganho marginal em corpus de súmulas/temas
- **Rejeitada para MVP:** simplicidade vence

## Consequências

### Positivas
- Zero processos adicionais (alinhado D-LEAN)
- Filtros temporal + jurisdição + binding em índice composto eficiente
- BM25 nativo SQLite (FTS5) — sem dependência externa
- Hybrid search com RRF — estado da arte
- Migração futura é fácil (CSV → import via INSERT) se decidirmos mudar engine
- Foreign key garante integridade `superseded_by`

### Negativas / Tradeoffs
- **sqlite-vec é v0.1** — DP-08 mantém-se ativa: load test obrigatório com 3000 docs + 1000 queries simultâneas
- BM25 do FTS5 é menos sofisticado que Elasticsearch (sem stemming PT-BR avançado) — mitigado por hybrid search
- Sem fallback automático para outro engine se sqlite-vec falhar — DP-NOVO: documentar plano B (FAISS + SQLite metadata)
- Vault de 3000 docs cabe na RAM, mas se crescer >100k pode exigir mudança de estratégia (out of scope MVP)

### Neutras
- Schema versionado em `bloco_vault/database/schema.sql` — migrations futuras via `alembic` ou scripts SQL idempotentes
- Reindex completo leva ~15min para 3k docs (Legal-BERTimbau encoding) — aceitável durante setup

## Decisão Pendente Reforçada

**DP-08 (existente):** load test sqlite-vec antes do release MVP — 3000 docs + 1000 queries simultâneas + medir p50/p95/p99 de latência. Meta: p95 ≤500ms.

**DP-NOVO criada:** documentar fallback para FAISS+SQLite caso sqlite-vec apresente problemas no load test. Documentar em `decisions/risk-mitigation-sqlite-vec.md`.

## Referências

- PRD v1.0.2: FR-RAG-01..06 (linhas 233-268), NFR-PERF-03 (linha 506)
- DP-08 origem: Smith F-HIGH-08
- sqlite-vec: https://github.com/asg017/sqlite-vec
- SQLite FTS5: https://www.sqlite.org/fts5.html
- Reciprocal Rank Fusion paper: https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
- Legal-BERTimbau: https://huggingface.co/rufimelo/Legal-BERTimbau-base
- Summary-based context enrichment: arXiv 2510.06999

---

*Aria, projetando o cérebro jurídico que cabe num arquivo único. 🏗️*
