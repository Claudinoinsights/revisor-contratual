---
type: research
title: "Revisor Contratual — Data Sources & External Integrations"
project: revisor-contratual
author: "@analyst (Atlas)"
date: "2026-05-01"
status: draft
companion_docs:
  - "state-of-the-art-2026-04-30.md"
  - "module-by-module-deep-dive-2026-04-30.md"
tags:
  - project/revisor-contratual
  - research
  - external-integrations
  - data-sources
  - datajud
  - lexml
  - bacen
  - stj
  - jurimetria
sources_count: 8
flags:
  - "URL STJ enviada (concursos) é INCORRETA para o objetivo do projeto — sugiro URLs corretas abaixo"
  - "BACEN GitHub oficial NÃO tem repos sobre SGS — apenas Pix. python-bcb (comunidade) é a fonte real"
verification_pending:
  - "Confirmação com Eric das URLs corretas STJ (jurisprudência? súmulas? temas repetitivos?)"
  - "Solicitar API key DataJud (gratuita mas precisa de cadastro CNJ)"
  - "Verificar se projeto-v3l0z tem licença implícita ou se contato direto é necessário"
---

# Revisor Contratual — Data Sources & External Integrations

> **Missão:** Eric forneceu 6 fontes externas. Vou auditar cada uma, mapear ao projeto, e sugerir fontes complementares que faltam.
>
> **Princípio:** Fonte sem propósito específico no projeto = ruído. Cada integração precisa responder: **(a) qual bloco consome?**, **(b) que dado/serviço fornece?**, **(c) qual o risco (licença, abandono, lock-in)?**.

---

## ⚡ Sumário Executivo — Veredicto por Fonte

| # | Fonte fornecida | Veredicto | Bloco consumidor | Risco |
|---|----------------|-----------|------------------|-------|
| 1 | [github.com/topics/datajud](https://github.com/topics/datajud) | 🟡 **Útil como referência** — 5 repos pequenos, nenhum maduro. Construir wrapper customizado. | Bloco 3 (Vault) — opcional para enriquecer com dados de processos | Baixo (API CNJ é gratuita) |
| 2 | [github.com/orgs/lexml](https://github.com/orgs/lexml) | 🟡 **Útil indiretamente** — stack Scala/Java pesada. Consumir API do Portal LexML diretamente, não rodar parsers. | Bloco 3 (Vault) — citar legislação (CDC, Código Civil) | Médio (GPL v2 — copyleft contagioso para Java/Scala) |
| 3 | [projeto-v3l0z/Sistema-de-Consulta-de-Processos-Judiciais-Backend](https://github.com/projeto-v3l0z/Sistema-de-Consulta-de-Processos-Judiciais-Backend) | 🟢 **Referência arquitetural** — padrão Django+DRF+DataJud. Não copiar código (sem licença), aprender estrutura. | Bloco 2/4 — referência de modelagem | Médio (sem licença = uso direto proibido por padrão) |
| 4 | [abjur/tidyML](https://github.com/abjur/tidyML) | 🔴 **Descartar uso direto** — R puro, abandonado, sem doc. | n/a — só inspiração conceitual | Alto (abandono) |
| 5 | [github.com/orgs/bacen](https://github.com/orgs/bacen) | 🔴 **Decepção** — só repos de Pix. **ZERO sobre SGS/séries temporais/taxas**. Para BACEN usar **python-bcb** (comunidade). | Bloco 4 — usar `python-bcb` em vez | Baixo |
| 6 | [stj.jus.br/.../Concursos](https://www.stj.jus.br/sites/portalp/Institucional/Concursos) | ⚠️ **URL INCORRETA** — é página de concursos públicos, não jurisprudência. Sugerir URLs corretas abaixo. | n/a — pedir URL correta | n/a |

**Achado adicional:**
- A biblioteca **`python-bcb`** (Wilson Freitas, MIT, ativa em 2026, 111 stars) cobre o que BACEN GitHub NÃO oferece: módulo `OData.TaxaJuros`, `OData.MercadoImobiliario`, `SGS`, `Currency`. **Esta é a integração real para BACEN — não os repos oficiais.**

---

## 🟦 Fonte 1 — DataJud (CNJ)

### O que é
**DataJud** é a base de dados oficial do **Conselho Nacional de Justiça (CNJ)** para metadados de processos judiciais de **todos os tribunais brasileiros**. Usa **Elasticsearch** como engine. API pública gratuita com autenticação por API Key.

### Repositórios analisados (`github.com/topics/datajud`)

| Repo | Linguagem | Stars | Aplicabilidade |
|------|-----------|-------|---------------|
| [DanielFillol/DataJUD_API_CALLER](https://github.com/DanielFillol/DataJUD_API_CALLER) | Go | 8 | Wrapper Go (ignorar — projeto é Python) |
| [Fransuelton/teste-incaas](https://github.com/Fransuelton/teste-incaas) | HTML/Angular | 2 | Frontend — não aplicável |
| [FlaviaLopes/CNJINOVA-DESAFIO2](https://github.com/FlaviaLopes/CNJINOVA-DESAFIO2) | JavaScript | 2 | Hackathon CNJ Inova 2020 — exemplo |
| [Marcus-V-Freitas/MVFC.Connectors](https://github.com/Marcus-V-Freitas/MVFC.Connectors) | C# | 1 | .NET conectores genéricos |
| [lcpassuncao/cleanjud](https://github.com/lcpassuncao/cleanjud) | **Python** | 0 | Único Python — sanitização de dados DataJud |

### API Pública oficial — informações canônicas

| Parâmetro | Valor |
|-----------|-------|
| **Endpoint base** | `https://api-publica.datajud.cnj.jus.br/` ([CNJ Wiki](https://datajud-wiki.cnj.jus.br/api-publica/)) |
| **Autenticação** | `Authorization: APIKey {chave-publica}` no header |
| **Chave** | Pública, gratuita, [obtida na Wiki CNJ](https://datajud-wiki.cnj.jus.br/api-publica/acesso/) |
| **Query syntax** | Elasticsearch DSL ([Endpoints docs](https://datajud-wiki.cnj.jus.br/api-publica/endpoints/)) |
| **Tribunais** | Aliases por tribunal: `api_publica_tjsp`, `api_publica_tjmg`, `api_publica_stj`, `api_publica_trf1`, etc. |
| **Documentação** | [Tutorial PDF CNJ 2023](https://www.cnj.jus.br/wp-content/uploads/2023/05/tutorial-api-publica-datajud-beta.pdf) |
| **Tutorial Python** | [Medium José Eduardo Pimentel](https://medium.com/@pimentel.jes/consulta-com-python-%C3%A0-api-p%C3%BAblica-do-datajud-base-de-dados-do-poder-judici%C3%A1rio-do-cnj-670157a392ae) |

### Aplicabilidade ao Revisor Contratual

**Casos de uso:**
1. **Buscar processos análogos** — dado um contrato bancário em UF X, buscar processos com mesmo CNJ-tema em DataJud para reforçar tese ("70% dos casos similares no TJMG resultaram em revisão").
2. **Validar status de jurisprudência citada** — confirmar se um acórdão referenciado pelo Advogado ainda é válido (não foi reformado).
3. **Enriquecimento estatístico opcional** — em fase posterior, gerar relatório "tese revisional tem 65% de êxito no TJMG, 41% no TJSP".

**NÃO é o foco principal:** o Revisor-Contratual analisa **contrato + jurisprudência consolidada**, não processos individuais. DataJud é **opcional** e enriquece, não substitui RAG no Bloco 3.

### Recomendação de implementação

**NÃO usar repos do tópico (todos imaturos).** **Construir wrapper customizado** baseado nos padrões oficiais:

```python
# bloco_engine/integracao/datajud_client.py
import httpx
from pydantic import BaseModel
from datetime import date
from typing import Literal

DATAJUD_BASE = "https://api-publica.datajud.cnj.jus.br"
DATAJUD_API_KEY = "..."  # obter em datajud-wiki.cnj.jus.br/api-publica/acesso/

TRIBUNAIS = Literal[
    "tjsp", "tjmg", "tjrj", "tjrs", "tjpr", "tjsc", "tjba", "tjgo",
    "stj", "stf", "trf1", "trf2", "trf3", "trf4", "trf5", "trf6"
]

class ProcessoDataJud(BaseModel):
    numero_cnj: str
    tribunal: str
    classe: str
    assunto: list[str]
    data_ajuizamento: date
    movimentacoes: list[dict]

async def buscar_processos_por_tema(
    tribunal: TRIBUNAIS,
    tema_assunto: str,         # ex: "anatocismo", "revisão contratual"
    valor_min: float | None = None,
    limit: int = 100
) -> list[ProcessoDataJud]:
    """Query Elasticsearch DSL contra DataJud."""
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"assuntos.nome": tema_assunto}}
                ]
            }
        },
        "size": limit
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{DATAJUD_BASE}/api_publica_{tribunal}/_search",
            headers={"Authorization": f"APIKey {DATAJUD_API_KEY}"},
            json=query,
            timeout=30
        )
        response.raise_for_status()
        return [ProcessoDataJud(**hit["_source"]) for hit in response.json()["hits"]["hits"]]
```

### Riscos

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| API CNJ pode mudar schema | Médio | Pydantic models permitem detecção precoce |
| Rate limit não-documentado | Médio | Backoff exponencial + cache local |
| Quebra de SLA da CNJ (instabilidade) | Médio | Fallback "DataJud indisponível — análise sem enriquecimento estatístico" |
| LGPD — dados de processos públicos mas com partes identificadas | Baixo | DataJud já é público; documentar uso ético |

---

## 🟦 Fonte 2 — LexML (Portal de Legislação Federal)

### O que é
**LexML** é o portal oficial do governo federal para **legislação brasileira padronizada em XML**. A organização GitHub mantém **63 repositórios** (30 visíveis na primeira página) com parsers, schemas, editores e renderizadores em **Scala, Java, TypeScript** principalmente.

### Repositórios mais relevantes para o Revisor

| Repo | Linguagem | Stars | Aplicabilidade ao projeto |
|------|-----------|-------|--------------------------|
| **[lexml-parser-projeto-lei](https://github.com/lexml/lexml-parser-projeto-lei)** | Scala | 15 | Parser de leis em XML — overkill para nosso uso |
| **[lexml-xml-schemas](https://github.com/lexml/lexml-xml-schemas)** | Java | 7 | **Schemas XML oficiais** — útil como referência conceitual |
| **[lexml-eta](https://github.com/lexml/lexml-eta)** | TypeScript | 23 | Editor web de textos articulados — descartar |
| **[lexml-linker](https://github.com/lexml/lexml-linker)** | **Haskell** | 12 | **Parser de remissões entre normas** — excelente para resolver "Art. 4º da Lei 8.078/90" → texto integral. Mas Haskell. |
| **[lexml-toolkit](https://github.com/lexml/lexml-toolkit)** | Java | 2 | Ferramenta de integração com Portal LexML |

**Total: 63 repos**, dominados por stack Scala/Java/TypeScript. Para Python, **rodar via subprocess** (Java disponível, Scala compilado para JVM) ou **consumir API web** do Portal LexML diretamente.

### O que falta no GitHub LexML

- **NÃO há cliente Python oficial** para a API do Portal LexML
- **NÃO há scrapers prontos** para CDC, Código Civil, leis bancárias específicas
- O foco é **infraestrutura de padronização**, não consumo

### Aplicabilidade ao Revisor Contratual

**Casos de uso:**
1. **Enriquecimento de citações legais** — quando o Advogado cita "art. 51, IV CDC", resolver a remissão para texto integral via API LexML (ou cache local).
2. **Vault de legislação** — popular `bloco_vault` com CDC, Código Civil, Lei 4.595/64 (SFN), Lei 10.931/04 (Patrimônio de Afetação) usando os XMLs LexML como fonte canônica.
3. **Validação de citação** — confirmar que o número do artigo citado existe e está vigente.

### Recomendação de implementação

**Estratégia híbrida:**

| Componente | Estratégia |
|-----------|-----------|
| Schemas XML LexML | Estudar como referência conceitual, **não usar parsers Scala** |
| Acesso ao corpus de leis | **Scrap inicial uma vez** (CDC, CC, leis bancárias) → salvar como JSON local versionado em `bloco_vault/seed_legislacao/` |
| Resolução de remissões | Construir resolver Python simples (regex + lookup local) — não precisa de Haskell |
| API LexML | Consumir via HTTP quando precisar de norma não cacheada |

```python
# bloco_vault/seed_legislacao/resolver_remissoes.py
import re
from pathlib import Path
import json

CITATION_PATTERN = re.compile(
    r"(?P<artigo>art(?:igo)?\.?\s*\d+(?:[º°])?)"
    r"(?:,\s*(?P<inciso>[IVXLCDM]+))?"
    r"\s+(?:da\s+)?(?P<lei>Lei\s+(?:Complementar\s+)?n[º°]?\s*[\d.]+(?:/\d{2,4})?|CDC|CC|CF)",
    re.IGNORECASE
)

def resolver_citacao(texto: str, vault_legislacao: Path) -> list[dict]:
    """Encontra citações legais e devolve texto do artigo."""
    citacoes = []
    for match in CITATION_PATTERN.finditer(texto):
        lei_nome = normalizar_lei(match.group("lei"))
        artigo_num = extrair_numero_artigo(match.group("artigo"))
        artigo_texto = buscar_artigo(vault_legislacao, lei_nome, artigo_num)
        citacoes.append({
            "match": match.group(0),
            "lei": lei_nome,
            "artigo": artigo_num,
            "texto_resolvido": artigo_texto
        })
    return citacoes
```

### Riscos

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| GPL v2 nos parsers — copyleft viral se distribuir | Alto se usar | Não distribuir os parsers; consumir só XML/API |
| API LexML pode mudar | Baixo | Cache local + versão dos schemas |
| Schemas XML são complexos | Médio | Não tentar parser completo — extrair só artigo+texto |

---

## 🟦 Fonte 3 — projeto-v3l0z/Sistema-de-Consulta-de-Processos-Judiciais-Backend

### O que é
Backend Django em desenvolvimento ativo (82 commits). Expõe API REST para consulta de processos judiciais brasileiros via integração DataJud. **Sem licença declarada**, **sem stars**, projeto de aprendizado/portfólio.

### Análise técnica

| Aspecto | Avaliação |
|---------|-----------|
| **Stack** | Django 5.2.1 + DRF + PostgreSQL 15 + drf-yasg (Swagger) + Docker Compose |
| **Estrutura** | Modular bem organizada: `apps/`, `processo/`, `parte/`, `movimentacao/`, `tribunais/`, `integrations/` |
| **Integração DataJud** | Suporta múltiplos tribunais via env var `DATAJUD_DEFAULT_TRIBUNAIS=api_publica_tjsp,api_publica_tjrj,api_publica_trf1` |
| **Comando útil** | `python manage.py testa_datajud {numero_processo}` |
| **Licença** | **NENHUMA declarada** — uso direto proibido por padrão (Berne Convention) |

### Aplicabilidade ao Revisor Contratual

**Stack divergente:**
- Revisor-Contratual usa **Streamlit + FastAPI + LangGraph**
- projeto-v3l0z usa **Django + DRF**

**Não há reaproveitamento direto de código** (stacks incompatíveis + sem licença).

**Mas é **referência arquitetural valiosa** para:
1. Modelagem de domínio (Processo, Parte, Movimentação, Tribunal) — adaptar ao Pydantic
2. Padrão de integrações em `integrations/` separado
3. Comando de teste `testa_datajud` — emular pattern em script Python
4. Estrutura modular por entidade (DDD-light)

### Recomendação

**Aprender a estrutura, não copiar código.** Solicitar ao autor licença MIT/Apache se quiser usar trechos específicos.

```text
# Adotar pattern de organização em bloco_engine/integracao/
bloco_engine/integracao/
├── __init__.py
├── datajud_client.py        # similar ao integrations/datajud do v3l0z
├── lexml_client.py
├── bacen_client.py
└── tests/
    ├── test_datajud.py      # similar ao testa_datajud command
    └── fixtures/
```

### Riscos

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| Sem licença = código não pode ser copiado | **Alto** | Apenas estudar; não copiar trechos sem contato com autor |
| Projeto pode ser abandonado | Médio | Não depender — usar como referência one-shot |

---

## 🟦 Fonte 4 — abjur/tidyML

### O que é
Repositório da **Associação Brasileira de Jurimetria (ABJ)** com **funções R** para organizar dados de tribunais brasileiros, no contexto do projeto CNJ "Maiores Litigantes".

### Análise técnica

| Aspecto | Avaliação |
|---------|-----------|
| **Linguagem** | R 100% |
| **Licença** | MIT |
| **Stars / Forks** | 2 / 0 |
| **Status** | **Aparentemente abandonado** (sem releases recentes) |
| **Documentação** | Ausente (sem README detalhado) |
| **Funcionalidade** | Estrutura de pacote R (R/, data-raw/, data/, vignettes/) sem detalhe acessível |

### Aplicabilidade ao Revisor Contratual

**Direta: NENHUMA** — stack Python, este é R.

**Indireta: conceitual** — a ABJ é referência em jurimetria brasileira. Vale conhecer o ecossistema:
- **[ABJ — Associação Brasileira de Jurimetria](https://abj.org.br/)** — eventos, papers, datasets
- **Outros repos da abjur** ([github.com/abjur](https://github.com/abjur)) — vale fazer um sweep separado

### Recomendação

**Descartar uso técnico direto.** Verificar outros repos da org abjur para ver se há algo Python utilizável (não foi auditado nesta sessão — solicitar nova pesquisa se Eric quiser).

### Riscos

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| Stack incompatível (R vs Python) | Alto | Não usar |
| Abandono | Alto | Não usar |

---

## 🟦 Fonte 5 — github.com/orgs/bacen (DECEPÇÃO)

### Achado crítico
A **organização oficial do Banco Central no GitHub** tem apenas **5 repositórios — TODOS sobre Pix e Real Digital**:

| Repo | Foco | Stars |
|------|------|-------|
| pix-api | API Pix | 2.8k |
| pilotord-kit-onboarding | Real Digital piloto (Solidity) | 953 |
| pix-dict-api | API DICT (chaves Pix) | 427 |
| pix-dict-quickstart | Quickstart DICT (Java) | 461 |
| pix-api-recebimentos | (Arquivado) | 130 |

**ZERO repositórios oficiais sobre:**
- ❌ SGS (Sistema Gerenciador de Séries Temporais) — nossa principal necessidade
- ❌ Open Banking
- ❌ Dados abertos
- ❌ Validadores de dados financeiros
- ❌ Taxas de juros

### Solução real — biblioteca comunitária

**`python-bcb`** (Wilson Freitas) — licença MIT, mantida ativamente em 2026:

| Atributo | Valor |
|----------|-------|
| **Repo** | [github.com/wilsonfreitas/python-bcb](https://github.com/wilsonfreitas/python-bcb) |
| **Licença** | **MIT** (compatível com qualquer uso) |
| **Status** | **Ativo** — último commit fevereiro 2026 |
| **Stars** | 111 |
| **Linguagem** | Python (8.3%) + Jupyter (91.7%) |
| **Módulos** | `sgs`, `currency`, `OData (PTAX, Expectativas, **TaxaJuros**, **MercadoImobiliario**, IFDATA)` |
| **Async** | Suporta `async_get()` para requisições concorrentes |

**Funcionalidades específicas para Revisor Contratual:**
- `OData.TaxaJuros` — Selic, CDI, **cheque especial, CDC, financiamento veículos, imobiliário**
- `OData.MercadoImobiliario` — dados específicos habitacional
- `sgs.get(codigo)` — qualquer série temporal SGS

### Aplicabilidade ao Revisor Contratual

**Bloco 4 (Engine)**, fundamental:
1. `calculadora_bacen_sgs.py` consome **`python-bcb` OData.TaxaJuros** em vez de `sgs.get()` direto.
2. Cobertura mais granular: TaxaJuros já organiza modalidades por categoria.
3. Async permite paralelizar busca de Selic + taxa CDC + taxa imobiliário.

### Recomendação

**Substituir** "API direta BACEN" da especificação por `python-bcb.OData`:

```python
# bloco_engine/ferramentas_calculo/calculadora_bacen_sgs.py
from bcb import sgs, OData
from datetime import date
from decimal import Decimal

class TaxaJurosBACEN:
    def __init__(self):
        self.taxa_juros_api = OData.TaxaJuros()

    async def get_taxa_modalidade(self, modalidade: str, mes_ref: date) -> Decimal:
        """Retorna taxa BACEN OData para a modalidade no mês de referência."""
        df = await self.taxa_juros_api.async_get(...)  # filtros específicos
        # df é pandas DataFrame
        return Decimal(str(df.loc[mes_ref, "taxa_juros_aa"]))

    async def get_selic_mes(self, mes_ref: date) -> Decimal:
        df = sgs.get({"selic": 4189}, start=mes_ref.replace(day=1))
        return Decimal(str(df.iloc[0, 0]))
```

### Riscos

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| `python-bcb` é mantido por 1 pessoa | Médio | Fork interno se necessário; código MIT permite |
| BACEN OData pode mudar schema | Médio | Cache local + Pydantic validation |
| Dependência indireta de pandas (peso) | Baixo | Aceitável — pandas já é dependência implícita |

---

## ⚠️ Fonte 6 — STJ Concursos (URL INCORRETA)

### Achado
A URL [stj.jus.br/sites/portalp/Institucional/Concursos](https://www.stj.jus.br/sites/portalp/Institucional/Concursos) é a **página de concursos públicos do STJ** — para contratação de servidores. Conteúdo:
- Editais de concurso (32 documentos PDF)
- Convocações de candidatos
- Históricos de concursos (2024, 2018, 2015, 2012, 2008, 2004, 1999)
- **Nenhum dataset de jurisprudência, súmulas, ou temas repetitivos**

### Provável intenção do Eric

Para o Revisor Contratual, as URLs do STJ que fazem sentido são:

| Recurso | URL | Conteúdo |
|---------|-----|----------|
| **Busca de jurisprudência** | [scon.stj.jus.br](https://scon.stj.jus.br/) | Sistema de busca de acórdãos, decisões monocráticas |
| **Súmulas STJ** | [stj.jus.br/sites/portalp/Jurisprudencia/Sumulas](https://www.stj.jus.br/sites/portalp/Jurisprudencia/Sumulas) | 671+ súmulas oficiais |
| **Temas Repetitivos** | [stj.jus.br/repetitivos/temas_repetitivos](https://www.stj.jus.br/repetitivos/temas_repetitivos) | 1300+ temas vinculantes |
| **Pesquisa Pronta** | [stj.jus.br/sites/portalp/Jurisprudencia/Pesquisa-Pronta](https://www.stj.jus.br/sites/portalp/Jurisprudencia/Pesquisa-Pronta) | Pesquisas pré-curadas por tema |
| **Dados Abertos** | [stj.jus.br/sites/portalp/Servicos/Dados-abertos](https://www.stj.jus.br/sites/portalp/Servicos/Dados-abertos) | Catálogo oficial (URL retornou 404 na verificação — pode ter mudado) |

### Recomendação para Eric

❓ **Confirmar qual recurso STJ você queria referenciar.** Sugestões:
1. Se é **jurisprudência** → usar `scon.stj.jus.br` (busca)
2. Se são **súmulas oficiais** → seed inicial via scraping de `Jurisprudencia/Sumulas`
3. Se são **temas repetitivos** (mais críticos para Bloco 3 — Juiz Revisor exige vinculantes) → `repetitivos/temas_repetitivos`
4. Se eram **datasets estatísticos** → tentar `Servicos/Dados-abertos` (URL pode ter mudado)

**Provavelmente tudo isso é o que faltava para popular o vault de jurisprudência.**

### Risco identificado
Sem fonte estruturada, o vault começa vazio → Bloco 3 retorna sempre RAG vazio → workflow vai sempre para Relatório de Inviabilidade. **Definir as fontes seed do vault é blocker** para fase 2.

---

## 🎯 Mapeamento Consolidado — Fontes → Blocos

| Fonte | Bloco 1 (UI) | Bloco 2 (Agentes) | Bloco 3 (Vault) | Bloco 4 (Engine) |
|-------|:-----------:|:-----------------:|:--------------:|:----------------:|
| **DataJud (CNJ)** | – | – | 🟡 Opcional (enriquecimento estatístico) | 🟢 `datajud_client.py` |
| **LexML (legislação)** | – | – | 🟢 Seed CDC + CC + Leis bancárias | 🟡 Resolver remissões (regex local) |
| **projeto-v3l0z** | – | – | – | 🟡 Padrão arquitetural (sem cópia) |
| **abjur/tidyML** | – | – | – | – (descartar) |
| **BACEN GitHub oficial** | – | – | – | 🔴 (descartar — usar `python-bcb`) |
| **`python-bcb` (real BACEN)** | – | – | – | 🟢 `calculadora_bacen_sgs.py` |
| **STJ (URL correta)** | – | – | 🟢 Súmulas + Temas Repetitivos (seed crítico) | – |

---

## 🧩 Fontes Complementares Recomendadas (que faltam na sua lista)

### Críticas para o vault inicial

| Fonte | Tipo | Uso |
|-------|------|-----|
| **STF — Súmulas Vinculantes** ([portal.stf.jus.br/jurisprudenciaSumulaNaJurisprudencia](https://www.stf.jus.br/arquivo/cms/jurisprudenciaSumulaNaJurisprudencia/anexo/Livro_Sumulas_Vinculantes_2_edicao.pdf)) | PDF + JSON | Maior peso de vinculação (5/5) |
| **STF — Repercussão Geral** ([portal.stf.jus.br/repercussaogeral/teses](https://portal.stf.jus.br/repercussaogeral/teses.asp)) | HTML estruturado | Teses vinculantes constitucionais |
| **STJ — Pesquisa Pronta** | HTML | Curadoria oficial por tema (incluindo "Anatocismo", "Tabela Price", "Revisão Contratual") |
| **CDC — Lei 8.078/90** | Texto integral via LexML | Base do Bloco 3 para arts. 39, 51 (cláusulas abusivas) |
| **Código Civil — Lei 10.406/02** | Texto integral via LexML | Arts. 421-480 (contratos em geral), 591 (mútuo) |
| **Lei do SFN — Lei 4.595/64** | Texto integral via LexML | Caracteriza "instituição financeira" (Súmula 539 STJ) |
| **MP 2.170-36/2001** | Texto integral via LexML | Capitalização infra-anual em SFN |

### Úteis para enriquecimento

| Fonte | Tipo | Uso |
|-------|------|-----|
| **TJ-MG / TJ-SP / TJ-RJ** | APIs/scraping | Acórdãos por UF inicial do MVP |
| **OAB — Provas + gabaritos** | PDF / OAB-Bench dataset | Validar qualidade do Advogado em queries jurídicas |
| **Maritaca AI Sabia avaliações** | HuggingFace datasets | Benchmark PT-BR jurídico |
| **JusBrasil** | Web scraping (atenção ToS) | Maior corpus de jurisprudência consolidada (mas ToS restritivo — verificar) |

### Outros repos da ABJ (vale auditar)

A organização [github.com/abjur](https://github.com/abjur) tem **18 repositórios** (não auditado nesta sessão). Vale outra pesquisa para identificar:
- Datasets jurimétricos brasileiros
- Ferramentas Python (se houver — abj usa principalmente R)
- Análises consolidadas que o Advogado/Juiz pode citar

---

## 📋 Stack Final de Integrações Externas (consolidada)

### Camada Bloco 4 (Engine — integrações de dados)

```text
bloco_engine/integracao/
├── __init__.py
├── datajud_client.py           # API CNJ — opcional, enriquecimento estatístico
├── lexml_client.py             # Resolução de remissões legais (regex + cache)
├── bacen_client.py             # python-bcb wrapper com cache + retry
├── stj_client.py               # Scraping/API de súmulas e temas repetitivos
├── cache.py                    # diskcache compartilhado
└── tests/
    ├── test_datajud.py
    ├── test_lexml.py
    ├── test_bacen.py
    └── test_stj.py
```

### Camada Bloco 3 (Vault — seed de dados)

```text
bloco_vault/seed/
├── legislacao/
│   ├── cdc-lei-8078-90.json           # via LexML
│   ├── codigo-civil-lei-10406-02.json
│   ├── lei-sfn-4595-64.json
│   └── mp-2170-36-2001.json
├── jurisprudencia/
│   ├── stf-sumulas-vinculantes.json
│   ├── stf-repercussao-geral.json
│   ├── stj-sumulas.json
│   ├── stj-temas-repetitivos.json
│   └── tj-{uf}-acordaos-piloto.json   # MVP: TJMG
└── README.md                           # como atualizar seed
```

### Pipeline de re-indexação

```text
bloco_vault/ingestao/refresh_scheduler.py
└─ Roda mensalmente:
   1. Re-fetch STF Súmulas Vinculantes → diff vs cache
   2. Re-fetch STJ Temas Repetitivos → adicionar novos
   3. Notificar mudanças no checkpoint do projeto
```

---

## ⚠️ Decisões críticas pendentes

1. **STJ — confirmar URL correta** (jurisprudência? súmulas? temas repetitivos? dados abertos?). A URL enviada é de concursos.
2. **Vault inicial — fonte seed:** começar com **scraping manual de STF Súmulas Vinculantes + STJ Temas Repetitivos + STJ Súmulas** (~2000 documentos) ou aguardar pipeline automático?
3. **DataJud é prioridade fase 1 ou fase 2?** Não é crítico para o MVP (que analisa contrato + jurisprudência consolidada). Adiar para fase 2 (enriquecimento estatístico).
4. **LexML — adotar consumo via API ou pré-cachear** os 4-5 diplomas legais relevantes (CDC, CC, SFN, MP capitalização)?
5. **Outros repos da ABJ — auditar?** ([github.com/abjur](https://github.com/abjur) tem 18 repos não auditados)

---

## 🔗 Fontes Consultadas (este estudo)

### URLs fornecidas por Eric
- [github.com/topics/datajud](https://github.com/topics/datajud)
- [github.com/orgs/lexml/repositories](https://github.com/orgs/lexml/repositories)
- [projeto-v3l0z/Sistema-de-Consulta-de-Processos-Judiciais-Backend](https://github.com/projeto-v3l0z/Sistema-de-Consulta-de-Processos-Judiciais-Backend)
- [abjur/tidyML](https://github.com/abjur/tidyML)
- [github.com/orgs/bacen/repositories](https://github.com/orgs/bacen/repositories)
- [stj.jus.br/sites/portalp/Institucional/Concursos](https://www.stj.jus.br/sites/portalp/Institucional/Concursos) ⚠️

### URLs adicionais consultadas
- [github.com/wilsonfreitas/python-bcb](https://github.com/wilsonfreitas/python-bcb)
- [datajud-wiki.cnj.jus.br/api-publica/](https://datajud-wiki.cnj.jus.br/api-publica/)
- [datajud-wiki.cnj.jus.br/api-publica/acesso/](https://datajud-wiki.cnj.jus.br/api-publica/acesso/)
- [datajud-wiki.cnj.jus.br/api-publica/endpoints/](https://datajud-wiki.cnj.jus.br/api-publica/endpoints/)
- [Tutorial CNJ DataJud PDF 2023](https://www.cnj.jus.br/wp-content/uploads/2023/05/tutorial-api-publica-datajud-beta.pdf)
- [LegalSuite — DataJud guia](https://legalsuite.com.br/blog/datajud-api-cnj)
- [Medium José Pimentel — DataJud Python](https://medium.com/@pimentel.jes/consulta-com-python-%C3%A0-api-p%C3%BAblica-do-datajud-base-de-dados-do-poder-judici%C3%A1rio-do-cnj-670157a392ae)

### URLs sugeridas para STJ (perguntar a Eric)
- [scon.stj.jus.br](https://scon.stj.jus.br/) — busca de jurisprudência
- [stj.jus.br/sites/portalp/Jurisprudencia/Sumulas](https://www.stj.jus.br/sites/portalp/Jurisprudencia/Sumulas)
- [stj.jus.br/repetitivos/temas_repetitivos](https://www.stj.jus.br/repetitivos/temas_repetitivos)
- [stj.jus.br/sites/portalp/Jurisprudencia/Pesquisa-Pronta](https://www.stj.jus.br/sites/portalp/Jurisprudencia/Pesquisa-Pronta)

---

*Atlas, mapeando os pontos de entrada para a Matriz dos dados — 🔎*
