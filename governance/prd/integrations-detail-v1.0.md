---
type: prd-annex
title: "Revisor Contratual — Anexo PRD v1.0: Mapeamento de Integrações por Repositório"
project: revisor-contratual
version: "1.0"
parent_doc: "prd/prd-v1.0.0.md"
owner: "@pm (Morgan)"
date: "2026-05-01"
predecessor_research: "research/data-sources-external-integrations-2026-05-01.md (Atlas)"
tags:
  - project/revisor-contratual
  - prd-annex
  - integrations
  - dependencies
---

# Anexo PRD v1.0 — Mapeamento de Integrações por Repositório

> **Propósito:** conectar cada um dos 6 repositórios externos avaliados por Atlas (em `research/data-sources-external-integrations-2026-05-01.md`) aos **blocos arquiteturais** e aos **FRs específicos** do PRD v1.0.0 — para que Aria, Tank e Neo saibam **exatamente onde cada integração entra no código**, sem ambiguidade.
>
> **Princípio:** integração sem mapeamento explícito a bloco+FR é débito técnico oculto.

---

## ⚡ Sumário Executivo — Veredicto por Repositório

| # | Repositório | Status | Blocos consumidores | FRs do PRD afetados | Effort impl. |
|---|-------------|--------|---------------------|---------------------|--------------|
| 1 | [topics/datajud](https://github.com/topics/datajud) | 🟡 **REFERÊNCIA** + wrapper Python customizado | bloco_engine, bloco_learning | FR-DATAJUD-01* (NOVO — fase 2), FR-ML-02 | Médio (fase 2) |
| 2 | [orgs/lexml](https://github.com/orgs/lexml) | 🟡 **CONSUMO HTTP + cache** (não rodar parsers Scala) | bloco_vault, bloco_engine | FR-RAG-01 (seed legislação), FR-LEX-01* (NOVO — resolver remissões) | Baixo (cache one-shot) |
| 3 | [projeto-v3l0z](https://github.com/projeto-v3l0z/Sistema-de-Consulta-de-Processos-Judiciais-Backend) | 🟢 **REFERÊNCIA ARQUITETURAL** (sem licença → não copiar código) | bloco_workflow, bloco_engine | Nenhum FR direto — informa padrão de organização | Zero (só estudar) |
| 4 | [abjur/tidyML](https://github.com/abjur/tidyML) | 🔴 **DESCARTAR** uso direto (R abandonado) | nenhum | nenhum | Zero |
| 5 | [orgs/bacen](https://github.com/orgs/bacen) | 🔴 **DESCARTAR** (só Pix; SGS não está lá) — usar **`python-bcb`** | bloco_engine | FR-BACEN-01, FR-BACEN-02, FR-BACEN-03 | Já em pyproject |
| 6 | [stj.jus.br/.../Concursos](https://www.stj.jus.br/sites/portalp/Institucional/Concursos) | ⚠️ **URL INCORRETA** — substituir por URLs canônicas STJ/STF | bloco_vault | FR-RAG-01 (seed jurisprudência) | Médio (scraping inicial) |

**\* FR-DATAJUD-01 e FR-LEX-01** são FRs novos sugeridos a partir deste mapeamento — adicionar ao PRD em próxima MINOR (v1.1.0) se Aria/Eric aprovarem.

---

## 1. DataJud (CNJ) — `topics/datajud`

### 1.1 Status
🟡 **REFERÊNCIA** + construir wrapper Python customizado. Os 5 repos do tópico (DanielFillol Go, Fransuelton HTML, FlaviaLopes JS, MVFC.Connectors C#, lcpassuncao Python) são **imaturos demais** para uso direto. Atlas já decidiu construir wrapper baseado nos endpoints oficiais ([CNJ Wiki](https://datajud-wiki.cnj.jus.br/api-publica/)).

### 1.2 Onde entra no código
| Bloco | Path proposto | Função |
|-------|---------------|--------|
| **bloco_engine/integracao/** | `datajud_client.py` | Wrapper httpx + Pydantic + Elasticsearch DSL para API CNJ |
| **bloco_learning/refresh_jurisprudence/** | `datajud_outcomes.py` | (Fase 2) cruzar outcomes do produto com processos análogos no DataJud |

### 1.3 FRs do PRD afetados

| FR-ID | FR (PRD) | Como o repo participa |
|-------|----------|----------------------|
| **FR-ML-02** (refresh mensal) | "Job mensal monitora STF (novas Súmulas Vinculantes) e STJ (novos Temas Repetitivos)" | DataJud opcional: enriquecer alerta com volume de novos processos análogos |
| **FR-DATAJUD-01** (NOVO — propor v1.1.0) | "Sistema busca processos análogos para enriquecer tese com estatística de êxito por câmara/relator" | Implementar wrapper Python; consultar API CNJ via Elasticsearch DSL |

### 1.4 Detalhes técnicos canônicos (do research Atlas)
- **Endpoint:** `https://api-publica.datajud.cnj.jus.br/`
- **Auth:** `Authorization: APIKey {chave-publica}` ([obter na Wiki](https://datajud-wiki.cnj.jus.br/api-publica/acesso/))
- **Aliases tribunais:** `api_publica_tjba`, `api_publica_stj`, `api_publica_stf`, etc.
- **Query syntax:** Elasticsearch DSL (`POST /api_publica_tjba/_search` com body JSON)

### 1.5 Riscos & Mitigações (escopo Aria definir em ADR)
- Schema CNJ pode mudar → Pydantic models + monitoring
- Rate limit não-documentado → backoff exponencial (tenacity) + cache local
- LGPD: dados de processos públicos mas com partes identificadas → uso ético documentado

### 1.6 Recomendação Morgan
- **MVP v1.0:** NÃO implementar DataJud (FASE 2)
- **PRD v1.1.0 (futura):** adicionar FR-DATAJUD-01 quando Aria validar viabilidade técnica

---

## 2. LexML (Portal Legislação Federal) — `orgs/lexml`

### 2.1 Status
🟡 **CONSUMO HTTP + cache one-shot** dos 4 diplomas críticos. **Não rodar parsers Scala/Java** dos 63 repos LexML (overkill + GPL v2 contagioso).

### 2.2 Onde entra no código
| Bloco | Path proposto | Função |
|-------|---------------|--------|
| **bloco_vault/seed/legislacao/** | `cdc-lei-8078-90.json` | Cache estruturado do CDC (extraído via API LexML 1×) |
| **bloco_vault/seed/legislacao/** | `codigo-civil-lei-10406-02.json` | Cache CC |
| **bloco_vault/seed/legislacao/** | `lei-sfn-4595-64.json` | Cache Lei SFN |
| **bloco_vault/seed/legislacao/** | `mp-2170-36-2001.json` | Cache MP capitalização |
| **bloco_engine/integracao/** | `lexml_client.py` | Wrapper HTTP para API LexML (edge cases — leis fora do cache) |
| **bloco_engine/integracao/** | `resolver_remissoes.py` | Regex Python + lookup local; resolve "art. 51, IV CDC" → texto integral |

### 2.3 FRs do PRD afetados

| FR-ID | FR (PRD) | Como o repo participa |
|-------|----------|----------------------|
| **FR-RAG-01** (indexação jurisprudência) | "Vault inicial ~3.000 docs (... + 4 leis pré-cache)" | LexML é fonte canônica das 4 leis citadas |
| **FR-DELIV-04** (peticionamento) | "Petição inicial revisional em PDF ... fundamentos jurídicos com citações" | Citar art. específico → resolver remissão via cache LexML para texto integral |
| **FR-LEX-01** (NOVO — propor v1.1.0) | "Sistema resolve toda citação 'art. X da Lei Y' citada na tese para texto integral; falhas geram WARN não-bloqueante" | Resolver remissões; consulta LexML quando lei não cacheada |

### 2.4 Detalhes técnicos canônicos
- **Repos descartados** (uso direto): lexml-parser-projeto-lei (Scala), lexml-eta (TS, editor web), lexml-renderer-* (Java)
- **Repo conceitualmente útil:** [lexml-xml-schemas](https://github.com/lexml/lexml-xml-schemas) — estudar schemas como referência, **não usar Java**
- **Estratégia adotada (Atlas):** scraping HTTP + JSON estruturado local; resolver remissões com regex + lookup
- **Risco GPL v2:** GPL v2 dos parsers é contagioso para Java/Scala. **Como NÃO redistribuímos código LexML, não há risco** — apenas consumimos API/dados públicos.

### 2.5 Recomendação Morgan
- **MVP v1.0:** implementar `bloco_vault/seed/legislacao/` (4 JSONs) + `lexml_client.py` minimalista para edge cases
- **PRD v1.1.0:** adicionar FR-LEX-01 explícito sobre resolução de remissões (atualmente está implícito em FR-DELIV-04)

---

## 3. projeto-v3l0z — Sistema-de-Consulta-de-Processos-Judiciais-Backend

### 3.1 Status
🟢 **REFERÊNCIA ARQUITETURAL** apenas. Stack divergente (Django + DRF) e **sem licença declarada** → uso direto proibido por padrão (Berne Convention). **Não copiar código**, apenas **estudar padrão**.

### 3.2 Onde entra no código
| Bloco | Como serve de referência |
|-------|--------------------------|
| **bloco_workflow/** | Padrão modular: separar `apps/processo/`, `apps/parte/`, `apps/movimentacao/` (DDD-light) — adaptar a Pydantic models em `bloco_contratos/` |
| **bloco_engine/integracao/** | Padrão `integrations/datajud/` — Atlas já adotou em `bloco_engine/integracao/datajud_client.py` |
| **Comandos CLI** | Padrão `python manage.py testa_datajud {numero_processo}` — emular como `python -m bloco_engine.integracao.testa_datajud` |

### 3.3 FRs do PRD afetados
**Nenhum FR direto.** Influência apenas em decisões arquiteturais (jurisdição de Aria, não de Morgan). Aria pode citar este repo na ADR de organização modular como precedente conceitual.

### 3.4 Risco & Mitigação
- **Sem licença = código não pode ser copiado** → apenas estudar estrutura; se Aria quiser usar trecho específico, contatar autor para autorização MIT/Apache.

### 3.5 Recomendação Morgan
- **MVP v1.0:** Aria documenta na ADR de organização modular como "precedente conceitual" (citação, não cópia)
- **Não atualizar PRD** — não há FR específico

---

## 4. abjur/tidyML

### 4.1 Status
🔴 **DESCARTAR uso direto.** R puro, abandonado, sem documentação substantiva. 109 repos da org `abjur` auditados por Atlas — apenas 1 repo Python (`cartoriosinfo`, escopo nicho não-aplicável).

### 4.2 Onde entra no código
**Lugar nenhum.**

### 4.3 FRs do PRD afetados
**Nenhum.**

### 4.4 Aproveitamento conceitual (não-código)
- ABJ ([abj.org.br](https://abj.org.br/)) é referência metodológica em jurimetria BR
- Vale **estudar metodologia** quando avançarmos para FR-ML-03 (Adaptive Re-Ranking) e FR-ML-04 (LoRA fine-tuning) na fase 2
- Em particular: `abjur/tpur` (Brazilian Unified Procedural Tables) tem **taxonomia oficial CNJ** que pode padronizar nosso campo `legal_topic_principal` no schema do vault — Atlas já flagou isso em sessão 3

### 4.5 Recomendação Morgan
- **MVP v1.0:** não usar
- **Fase 2:** Aria considerar extrair taxonomia do `tpur` (R → JSON) como input para refinar `legal_topic_principal` no schema do `bloco_vault/`

---

## 5. github.com/orgs/bacen

### 5.1 Status
🔴 **DESCARTAR.** Organização oficial do Banco Central no GitHub tem **5 repos — TODOS sobre Pix/Real Digital**. Zero sobre SGS, séries temporais ou taxas de juros.

### 5.2 Solução real — `python-bcb` (comunidade)
**Wilson Freitas** mantém [`python-bcb`](https://github.com/wilsonfreitas/python-bcb) (MIT, ativo em 2026, 111 stars). É a fonte real para BACEN no Python.

### 5.3 Onde entra no código
| Bloco | Path proposto | Função |
|-------|---------------|--------|
| **bloco_engine/ferramentas_calculo/** | `calculadora_bacen_sgs.py` | Wrapper de `python-bcb.OData.TaxaJuros` + `python-bcb.sgs.get` com cache + retry |
| **bloco_engine/ferramentas_calculo/** | `codigos_bacen.yaml` | Mapping declarativo modalidade → código SGS (Veículos PF=25471, Selic=11, IPCA=433, etc.) |

### 5.4 FRs do PRD afetados

| FR-ID | FR (PRD) | Como o repo participa |
|-------|----------|----------------------|
| **FR-BACEN-01** (fetch taxa modalidade+data) | "Usa python-bcb OData.TaxaJuros (cobre cheque especial, CDC, financiamento veículos, imobiliário)" | `python-bcb` é a dependência real (não os repos de Pix) |
| **FR-BACEN-02** (cache + retry) | "Cache diskcache TTL 30 dias + retry tenacity backoff exponencial" | `python-bcb` retorna pandas DataFrame; cache + retry implementados em wrapper local |
| **FR-BACEN-03** (fallback "última taxa") | "Se API down após retries, usa última taxa cacheada da modalidade próxima" | Política de fallback em `calculadora_bacen_sgs.py` |

### 5.5 Detalhes técnicos canônicos
- **Módulos `python-bcb` relevantes:**
  - `OData.TaxaJuros` → Selic, CDI, cheque especial, **CDC, financiamento veículos**, imobiliário
  - `OData.MercadoImobiliario` → financiamento habitacional específico
  - `sgs.get(codigo)` → qualquer série temporal SGS (genérico)
- **Async support:** `OData.async_get()` para requisições concorrentes — útil para pré-fetch
- **Códigos confirmados** (verificar [DADO-PENDENTE] do PRD para os demais):
  - SGS 11 (Selic diária)
  - SGS 433 (IPCA mensal)
  - SGS 25471 (Veículos PF média mensal)
  - SGS 20749 (Veículos PF média geral)

### 5.6 Recomendação Morgan
- **MVP v1.0:** já em pyproject (`python-bcb>=0.5`) — implementar wrapper conforme FR-BACEN-01/02/03
- **Sem alterações no PRD** — FRs já contemplam corretamente

---

## 6. STJ Concursos — URL INCORRETA

### 6.1 Status
⚠️ **URL incorreta.** [stj.jus.br/.../Concursos](https://www.stj.jus.br/sites/portalp/Institucional/Concursos) é página de **concursos públicos do STJ** (recrutamento de servidores), não jurisprudência. Atlas já flagou em sessão 2.

### 6.2 URLs corretas que provavelmente o Eric quis enviar (já confirmadas pelo Atlas)

| Recurso | URL canônica | Aplicabilidade |
|---------|--------------|----------------|
| **STJ Súmulas** | [stj.jus.br/sites/portalp/Jurisprudencia/Sumulas](https://www.stj.jus.br/sites/portalp/Jurisprudencia/Sumulas) | Seed jurisprudência — peso vinculação 3/5 (~671 docs) |
| **STJ Temas Repetitivos** | [stj.jus.br/repetitivos/temas_repetitivos](https://www.stj.jus.br/repetitivos/temas_repetitivos) | Seed jurisprudência — peso 4/5 (~1.300 temas) — CRÍTICO |
| **STJ Pesquisa Pronta** | [stj.jus.br/sites/portalp/Jurisprudencia/Pesquisa-Pronta](https://www.stj.jus.br/sites/portalp/Jurisprudencia/Pesquisa-Pronta) | Curadoria oficial por tema (incluindo "Anatocismo", "Tabela Price") |
| **STJ Busca Acórdãos** | [scon.stj.jus.br](https://scon.stj.jus.br/) | Validação manual durante curadoria do seed |
| **STF Súmulas Vinculantes** (complementar) | [portal.stf.jus.br](https://www.stf.jus.br/arquivo/cms/jurisprudenciaSumulaNaJurisprudencia/anexo/Livro_Sumulas_Vinculantes_2_edicao.pdf) (PDF) | Peso máximo 5/5 (~58 docs) |
| **STF Repercussão Geral** (complementar) | [portal.stf.jus.br/repercussaogeral/teses](https://portal.stf.jus.br/repercussaogeral/teses.asp) | Peso 5/5 (~1.300 teses constitucionais) |

### 6.3 Onde entra no código
| Bloco | Path proposto | Função |
|-------|---------------|--------|
| **bloco_vault/seed/jurisprudencia/** | `stj-sumulas.json` | Cache estruturado das ~671 súmulas STJ |
| **bloco_vault/seed/jurisprudencia/** | `stj-temas-repetitivos.json` | Cache dos ~1.300 temas vinculantes STJ |
| **bloco_vault/seed/jurisprudencia/** | `stf-sumulas-vinculantes.json` | Cache das ~58 SV STF |
| **bloco_vault/seed/jurisprudencia/** | `stf-repercussao-geral.json` | Cache das ~1.300 teses RG STF |
| **bloco_vault/seed/scrapers/** | `stj_scraper.py`, `stf_scraper.py` | Scrapers Python customizados (Atlas re-implementa de `courtsbr/stj` e `courtsbr/stf` em R) |
| **bloco_learning/refresh_jurisprudence/** | `stj_monitor.py`, `stf_monitor.py` | Refresh mensal (FR-ML-02) |

### 6.4 FRs do PRD afetados

| FR-ID | FR (PRD) | Como entra |
|-------|----------|------------|
| **FR-RAG-01** (indexação jurisprudência) | "Vault inicial ~3.000 docs (STF Súmulas Vinculantes ~58 + STF Repercussão Geral ~1.300 + STJ Súmulas ~671 + STJ Temas Repetitivos ~1.300 + TJBA acórdãos ~300)" | URLs corretas STF/STJ + scrapers Python são as fontes |
| **FR-ML-02** (refresh mensal alerta crítico) | "Job mensal monitora STF (novas SV) e STJ (novos Temas Repetitivos); se Tema 1378 STJ for julgado: emite CRITICAL_ALERT" | Scrapers em `bloco_learning/refresh_jurisprudence/` |
| **FR-AUDIT-02** (Tema 1378 STJ trigger) | "Evento CRITICAL_JURIS_CHANGE com payload {tema, tribunal, detected_at}" | Scraper STJ detecta julgamento via diff vs cache |

### 6.5 Recomendação Morgan
- **MVP v1.0:** confirmar com Eric quais URLs ele realmente quis enviar (provavelmente todas as 4 acima)
- **PRD v1.0:** já contempla as fontes corretas — apenas URL enviada estava errada (sem mudança de FR necessária)
- **Implementação:** scrapers Python customizados (não rodar `courtsbr/*` em R conforme decidido pela Atlas em D-05)

---

## 📊 Tabela Consolidada — Repo × Bloco × FR × Effort

| Repo | bloco_contratos | bloco_interface | bloco_workflow | bloco_vault | bloco_engine | bloco_audit | bloco_learning | FRs afetados | Effort MVP |
|------|:---------------:|:---------------:|:--------------:|:-----------:|:------------:|:-----------:|:--------------:|--------------|:----------:|
| DataJud | – | – | – | (fase 2) | ✅ wrapper | – | (fase 2) | FR-ML-02; FR-DATAJUD-01* | Fase 2 |
| LexML | – | – | – | ✅ seed leis | ✅ resolver remissões | – | – | FR-RAG-01, FR-DELIV-04, FR-LEX-01* | Baixo |
| projeto-v3l0z | – | – | (referência) | – | (referência) | – | – | nenhum (só ADR de org) | Zero |
| abjur/tidyML | – | – | – | – | – | – | (fase 2 conceitual) | nenhum | Zero |
| BACEN GitHub | – | – | – | – | – | – | – | nenhum (descartado) | Zero |
| **`python-bcb`** (real) | – | – | – | – | ✅ BACEN client | – | – | FR-BACEN-01/02/03 | Já em pyproject |
| STJ/STF (URLs corretas) | – | – | – | ✅ seed jurisprudência | – | ✅ alertas | ✅ refresh mensal | FR-RAG-01, FR-ML-02, FR-AUDIT-02 | Médio (scrapers) |

**Legenda:**
- ✅ implementação ativa MVP
- (fase 2) implementação adiada
- (referência) sem código direto, só padrão arquitetural
- – não-aplicável

---

## 🆕 FRs Novos Sugeridos (para PRD v1.1.0 — após Aria avaliar)

### FR-DATAJUD-01 (proposto — fase 2)
**Sistema busca processos análogos na API DataJud para enriquecer tese com estatística de êxito**
- Input: tese principal + UF + tema legal
- Output: top-N processos análogos com outcome conhecido + estatística agregada
- AC: latência ≤10s; ≥95% das queries retornam ≥1 processo análogo se houver tema reconhecido
- Quando ativar: fase 2 (após MVP funcionar)

### FR-LEX-01 (proposto — pode entrar em v1.0 se trivial)
**Sistema resolve toda citação 'art. X da Lei Y' presente na tese gerada para texto integral**
- Input: tese gerada (com citações textuais)
- Output: tese enriquecida com [texto do art X] inline + falhas de resolução listadas como WARN não-bloqueante
- AC: ≥95% das citações de leis pré-cacheadas (CDC, CC, SFN, MP) resolvidas em <100ms (lookup local); ≥80% das demais resolvidas via API LexML em <2s
- Quando ativar: avaliar com Aria — pode entrar em v1.0 se Aria considerar trivial (regex + lookup)

---

## 📋 Notas para Aria (próximo agente — ADR)

1. **ADR sobre organização modular** pode citar `projeto-v3l0z` como precedente conceitual (Django+DRF+integrations/), adaptado a Pydantic+sqlite-vec
2. **ADR sobre BACEN** deve formalizar `python-bcb` como dependência canônica (não os repos oficiais BACEN GitHub)
3. **ADR sobre seed jurisprudência** deve referenciar este anexo + decidir entre rodar `courtsbr/stf+stj` em R ou Atlas re-implementar em Python (Atlas já preferiu Python — D-05)
4. **ADR sobre LexML** deve formalizar estratégia "consumo HTTP + cache local" (não rodar parsers Scala/Java — risco GPL v2 evitado por não-redistribuição)
5. **Considerar FR-LEX-01 e FR-DATAJUD-01** — decidir se entram em v1.0, v1.1 ou v2.0
6. **Atualizar `.project.yaml`** para refletir paths consolidados de seed/integração

---

## 🔗 Referências canônicas (já em outros docs do vault)

- Pesquisa fonte: `research/data-sources-external-integrations-2026-05-01.md` (Atlas — sessão 2)
- Sessão de descoberta: `research/competitor-analysis-2026-05-01.md` (Atlas — sessão 4 — Tema 1378 STJ)
- Decisões consolidadas: `decisions/decisions-consolidated-2026-05-01.md` (Atlas — sessão 3)
- Shopping list (libs Python): `decisions/requirements-extended-2026-05-01.md` (Atlas — sessão 8)

---

*Morgan, conectando os pontos antes de Aria desenhar o quadro 📊*
