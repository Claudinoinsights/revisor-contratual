---
type: adr
id: "ADR-015"
title: "Vision OCR Architecture — Claude Sonnet 4.6 + caching + multi-page paralelo"
status: proposed
date: "2026-05-07"
domain: infra
adr_level: design
decision_makers:
  - "@architect (Aria) — design"
  - "@analyst (Atlas) — research v1 Section 2"
  - "Eric Claudino — autorização B (Atlas judgment)"
supersedes: ""
superseded_by: ""
partially_supersedes: "ADR-013 (mecanismo OCR — preserva intent geral MVP-LEAN)"
related_to:
  - "ADR-014 (provider abstraction — usa mesmo Anthropic SDK)"
  - "ADR-017 (multi-tenant — ocr_cache table com RLS)"
project: revisor-contratual
sprint: "04"
phase: "2.1"
tags:
  - project/revisor-contratual
  - adr
  - sprint-04
  - vision-ocr
  - anthropic
  - caching
---

# ADR-015: Vision OCR Architecture

## Contexto

Sprint 03 usava marker-pdf 1.x + Surya OCR local (ADR-013). Smith CC.41 F-A1 demonstrou hardware ~16GB RAM insuficiente para stack OCR + LLMs simultâneos (OOM kill silencioso). Sprint 04 cloud-first elimina OCR local; Atlas v1 Section 2 mapeou Claude Sonnet 4.6 vision como melhor opção legal (97,6% field extraction complex layouts + 0,09% hallucination — decisivo para contratos jurídicos).

Eric escolheu B (Atlas judgment) Anthropic Hybrid: Sonnet 4.6 OCR+Juiz, Haiku 4.5 4 personas. OCR é etapa crítica de qualidade — premium model justifica-se aqui.

## Decisão

**Claude Sonnet 4.6 vision para OCR + caching SHA-256 + multi-page paralelo.** PDF é particionado por página, cada página enviada como image input ao Sonnet, paralelismo via `asyncio.gather`. Resultado markdown unificado é cacheado por hash do PDF original (TTL 90 dias).

Componentes:

1. **Image preprocessing** (per page):
   - Resize máx 1568×1568 (Sonnet sweet spot ~1700 tokens/imagem)
   - Normalize contrast (PIL ImageEnhance)
   - JPEG quality 85 (compromise quality/size)
   - Detail level: `high` para todas páginas (legal accuracy mandatory)

2. **Multi-page handling**:
   - Páginas paralelas via `asyncio.gather(*[ocr_page(p) for p in pages], return_exceptions=False)`
   - Timeout 120s por página
   - Page-level error: se 1 de N págs falhar → abort análise inteira (não tenta processar parcial — risco análise incorreta)

3. **Custo per analysis** (cliente paga via BYOK):
   - ~1700 input tokens × 12 págs típicas ≈ 20.400 tokens
   - × Sonnet 4.6 $3/M input = **$0,061/análise** (R$ 0,34 cotação 5,5)
   - Imobiliário 25 págs ≈ R$ 0,71/análise

4. **Cache** SHA-256:
   - Tabela `ocr_cache (pdf_hash_sha256 PK, tenant_id NOT NULL, markdown_text TEXT, tokens_used INT, model VARCHAR(50), created_at TIMESTAMP, accessed_at TIMESTAMP)`
   - RLS policy `tenant_isolation` (ADR-017)
   - TTL 90 dias via cron job semanal `DELETE FROM ocr_cache WHERE accessed_at < NOW() - INTERVAL '90 days'`
   - Hit rate esperado: ~5-15% (mesmos contratos re-analisados)

5. **Fallback se vision LLM falhar**:
   - 3 retries exponential backoff (1s, 4s, 16s)
   - Após 3 falhas → erro estruturado PT-BR ao usuário ("OCR temporariamente indisponível, tente novamente em alguns minutos")
   - **NÃO há fallback marker-pdf** — local removido nesta arquitetura cloud-first
   - Análise marca status `failed` + log incidente para audit

## Razão

- **Sonnet 4.6 vs alternativas**: Atlas v1 Section 2 — Sonnet 4.6 lidera 97,6% field extraction + 0,09% hallucination. GPT-5.4 ligeiramente melhor em scanned char (97,3% vs 95%) mas hallucination 0,15% derruba para legal. Gemini Flash mais barato mas accuracy 88% inadequada
- **Caching SHA-256 vs LRU memory**: PDF é input determinístico, cache disk PostgreSQL persiste entre restarts; LRU memory perde ao reiniciar app
- **Paralelismo asyncio.gather vs serial**: 12 págs serial = ~60s; paralelo = ~5s. Latência crítica para UX. Custo igual (mesmas N requests)
- **Page-level abort vs partial processing**: contratos jurídicos têm interdependências entre páginas (cláusulas referenciam-se); processar parcial = análise incorreta = risco legal escritório

## Alternativas Consideradas

### Manter marker-pdf + Surya local

**Rejeitada.** Smith CC.41 F-A1 demonstrou inviabilidade RAM. Cloud pivot resolve estruturalmente.

### Gemini Flash Vision (economy)

**Rejeitada.** Atlas v1 Section 2 — accuracy 88% char + 0,3% hallucination inaceitável para legal (cláusula inventada = catástrofe). Economia de ~$0,06/análise não compensa risco.

### GPT-5.4 Vision

**Rejeitada.** Atlas v1 Section 2 — accuracy comparable mas hallucination 0,15% (1,7× pior que Sonnet). Decisivo para legal.

### Cache em Redis (vs PostgreSQL)

**Rejeitada.** Adiciona dependência infraestrutural sem ganho — markdown texts ~30KB/análise não justifica memory cache; PostgreSQL aproveita storage existente + RLS.

### Processamento serial (sem paralelismo)

**Rejeitada.** UX degradada (60s vs 5s). Sem ganho de custo (mesmas requests).

## Consequências

### Positivas
- Eliminação de RAM bottleneck (Smith CC.41 F-A1 fechado estruturalmente)
- Accuracy legal best-in-class (97,6% extraction)
- Cache reduz custo escritório em casos de re-análise (~5-15% hit rate)
- Paralelismo dá UX rápida

### Negativas
- Custo per-page novo (escritório paga $0,06/análise mínimo)
- Dependência rede: sem internet = sem OCR (offline-first impossível)
- Vendor lock-in Anthropic Sonnet específico

### Neutras
- 90-day TTL cache: trade-off storage vs hit rate; ajustável via config
- Page-level abort pode frustrar usuário em PDFs grandes com 1 falha — UX trade-off aceitável vs risco análise incorreta

## Cross-references

- **Atlas v1 Section 2** (Vision OCR Landscape) — benchmark base
- **Atlas v1 Section 1** (OpenRouter catalog) — pricing Sonnet 4.6
- **Smith CC.41 F-A1** — motivação RAM constraint
- **ADR-013 (deprecated parcial)** — MVP-LEAN OCR mechanism substituído; restante intent preservado
- **ADR-014 (related)** — usa mesmo Anthropic SDK + BYOK key
- **ADR-017 (related)** — `ocr_cache` table com RLS multi-tenant
