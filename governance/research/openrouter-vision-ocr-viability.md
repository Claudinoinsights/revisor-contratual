---
type: research
title: "OpenRouter + Vision OCR + LGPD Path A — Sprint 04 Viability"
project: revisor-contratual
sprint: 04
phase: 1
author: "@analyst (Atlas)"
date: "2026-05-07"
tags:
  - project/revisor-contratual
  - research
  - sprint-04
  - viability
  - openrouter
  - vision-ocr
  - lgpd
---

# OpenRouter + Vision OCR + LGPD Path A — Sprint 04 Viability

> **Contexto:** Pivot do hardware local (Sabia 7B + Qwen 7B/3B em 16GB com OOM bound — Smith CC.41 F-A1) para cloud via OpenRouter. Eric autorizou LGPD Path A (cloud agressivo + termo consentimento), budget R$ 1500/mês, escopo 4 doctypes (FIES + Veicular + Bancário + Imobiliário), substituição do OCR local (marker-pdf+surya) por vision LLM. Atlas mapeia viabilidade — Aria desenha (Phase 2), Trinity escreve PRD (Phase 3), Sati redesenha UI com OrSheva (Phase 4), Smith adversarial (Phase 5).
>
> **Cotação USD→BRL usada:** 5,50 (mai/2026). Atualizar antes de implementação.
> **Premissa de volume:** declarada por seção; Eric confirma teto.

---

## Seção 1 — OpenRouter Catalog & Pricing (mai/2026)

### Realidade temporal

A lista de modelos do dispatch (Claude 3.5 Sonnet, GPT-4o, Gemini 1.5) é **legacy** em mai/2026. O catalog atual tem Claude 4.x, GPT-5.x, Gemini 3.x como frontier. Mantenho cobertura legacy para comparação, mas recomendo decisão sobre os atuais.

### Top modelos por categoria (USD/1M tokens)

**Premium ($10+/1M output):**
| Modelo | Provider | Input/M | Output/M | Vision | Context | BRL Input/M |
|---|---|---|---|---|---|---|
| `openai/gpt-5.4-pro` | OpenAI | $30 | $180 | Y | 1.05M | R$ 165 |
| `anthropic/claude-opus-4.7` | Anthropic | $5 | $25 | Y | 1M | R$ 27,50 |
| `anthropic/claude-sonnet-latest` (4.6) | Anthropic | $3 | $15 | Y | 1M | R$ 16,50 |

**Mid ($1-10/1M):**
| Modelo | Provider | Input/M | Output/M | Vision | Context | BRL Input/M |
|---|---|---|---|---|---|---|
| `openai/gpt-5.4` | OpenAI | $2,50 | $15 | Y | 1.05M | R$ 13,75 |
| `google/gemini-pro-latest` (3.1) | Google | $2 | $12 | Y | 1.05M | R$ 11 |
| `mistralai/mistral-medium-3.5` | Mistral | $1,50 | $7,50 | Y | 262K | R$ 8,25 |
| `anthropic/claude-haiku-latest` (4.5) | Anthropic | $1 | $5 | Y | 200K | R$ 5,50 |

**Economy (<$1/1M):**
| Modelo | Provider | Input/M | Output/M | Vision | Context | BRL Input/M |
|---|---|---|---|---|---|---|
| `google/gemini-flash-latest` | Google | $0,50 | $3 | Y | 1.05M | R$ 2,75 |
| `deepseek/deepseek-v4-pro` | DeepSeek | $0,44 | $0,87 | Y | 1M | R$ 2,40 |
| `qwen/qwen3.5-flash` | Alibaba | $0,065 | $0,26 | Y | 1M | R$ 0,36 |
| `deepseek/deepseek-v4-flash` | DeepSeek | $0,14 | $0,28 | Y | 1M | R$ 0,77 |

### Latency P50/P95

OpenRouter não publica SLA universal — varia por provider e load momentâneo. Estimativas observadas em comunidade (verificar): Anthropic Sonnet ~3-5s P50, Claude Opus ~8-12s P50, Gemini Flash ~1-2s P50, GPT-5.4 ~4-6s P50. **Recomendação:** Aria deve validar latency real em ADR-014 com benchmark do contrato típico.

### Rate limits

OpenRouter padrão: 200 req/min com $10 saldo, escala com saldo (1000 req/min com $100+). Free tier limitado a poucos req/dia. **Para Sprint 04 com 4 doctypes simultâneos rodando 4 personas paralelas: precisa saldo ≥$50** para evitar throttling.

**Sources:**
- [OpenRouter Models API — JSON catalog](https://openrouter.ai/api/v1/models)
- [OpenRouter Models page](https://openrouter.ai/models)
- [OpenRouter FAQ](https://openrouter.ai/docs/faq)

---

## Seção 2 — Vision OCR Landscape (substitui marker-pdf+surya)

### Benchmarks publicados (2026)

| Modelo | Char Accuracy (scanned) | Field Extract (complex) | Hallucination |
|---|---|---|---|
| **Claude Sonnet 4.6** | ~95% | **97,6%** ⭐ | **0,09%** ⭐ |
| GPT-5.4 (vision) | **97,3%** ⭐ | ~95% | 0,15% |
| Gemini 2.5 Pro / 3.1 Pro | ~93% | ~91% | 0,2% |
| Gemini Flash latest | ~88% | ~85% | 0,3% |
| Llama 3.2 90B Vision | ~85% | ~80% | 0,4% |

**Para CDC PF brasileiro (jurídico/financeiro):** Claude Sonnet 4.6 vence porque (a) **0,09% hallucination** — invenção de cláusula em contrato é catastrófica, (b) campos extraídos com 97,6% precisão em layouts complexos (CET, planilhas amortização, cláusulas multi-coluna), (c) Anthropic API comercial não treina no input.

**Para PDF escaneado puro (não jurídico complexo):** GPT-5.4 vision é marginalmente melhor (97,3% char) — irrelevante para Eric que tem layouts estruturados.

### Tokenização de imagem

- **Gemini (Flash + Pro):** ~258 tokens/imagem padrão, regardless da resolução até 3072×3072
- **Claude Sonnet 4.6:** ~1500-1800 tokens/imagem média (1568×1568); high-detail >2k
- **GPT-5.4 vision:** tile system 512×512 (~85 tokens/tile + base 85; varia high/low detail)

### Trade-off vs marker-pdf local

| Dimensão | marker+surya local | Vision LLM cloud |
|---|---|---|
| Custo $ | Zero | $0,02-0,06 / 12 págs (provider) |
| Custo recurso | 2-3GB RAM + 30-60s/PDF | Latency rede 3-15s |
| Precisão jurídico | ~90% (perdas em tabela) | 97,6% (Claude) |
| Manutenção | Updates marker = breaking | Provider mantém |
| LGPD | Local = sem transferência | Cloud = Art. 33 |

**Recomendação OCR Atlas:** **Claude Sonnet 4.6** primário, **Gemini Flash** fallback para volumes altos.

**Sources:**
- [TokenMix Best AI Document Processing 2026](https://tokenmix.ai/blog/best-ai-for-document-processing)
- [CodeSOTA Best OCR Models 2026](https://www.codesota.com/ocr)
- [Vellum LLMs vs OCRs 2026](https://www.vellum.ai/blog/document-data-extraction-llms-vs-ocrs)
- [OmniAI OCR Benchmark](https://getomni.ai/blog/ocr-benchmark)

---

## Seção 3 — LGPD Compliance Path A (Eric escolheu agressivo)

### a) Base legal Art. 7º — recomendação Atlas

| Inciso | Aplicabilidade | Solidez |
|---|---|---|
| **I — Consentimento** ⭐ | Cliente do advogado consente uso de IA cloud para análise | **MAIS SÓLIDO** |
| V — Execução de contrato | Se contrato cliente-advogado prevê uso de IA | OK se contrato atualizado |
| IX — Legítimo interesse | Análise jurídica do contrato | **FRÁGIL** para PII financeiro (CPF, valor financiado) |

**Atlas recomenda:** **Art. 7º I (consentimento explícito)** combinado com **execução de contrato (V)** como base secundária. Consentimento porque PII é sensível (CPF + dados financeiros) e Art. 33 transferência internacional exige base robusta.

### b) Termo de consentimento — pontos obrigatórios (Art. 8º)

Atlas NÃO redige termo (escopo Eric advogado). Lista mínima a constar:

1. Identificação do controlador (Eric / razão social)
2. Finalidade específica: "análise de contrato bancário via IA cloud para identificar irregularidades"
3. Forma e duração do tratamento (máx 30 dias para análise + retenção zero pós-resposta via ZDR)
4. **Compartilhamento com terceiros: OpenRouter + provider downstream (Anthropic/Google/OpenAI)**
5. **Transferência internacional Art. 33: servidores US/EU**
6. Direitos do titular (Art. 18: confirmação, acesso, eliminação, portabilidade)
7. Possibilidade de revogação (com consequência: análise não pode ser reprocessada)

### c) Disclaimer no produto

**Atlas sugere:**
- **S2 pré-upload:** checkbox obrigatório "Concordo com o uso de IA cloud para análise — [link termo]" (BLOQUEIA upload se não marcado)
- **Footer:** texto passive "Análises processadas via IA cloud LGPD-compliant"
- **Modal informativo** quando user clica "Concordo": mostra resumo dos riscos (transferência US, providers, retenção)

### d) Riscos não-mitigados pelo Path A (Eric assumiu)

| Risco | Severidade | Mitigação possível (não obrigatória Path A) |
|---|---|---|
| **Art. 33 transferência internacional** | ALTA | Path C usaria providers BR-residence (não disponível em OpenRouter). Path A: consentimento explícito + termo |
| **Retenção 30 dias OpenAI default** | MÉDIA | Usar Anthropic-only OU `zdr=true` per-request OpenRouter |
| **Provider retreina prompts em consumer tier** | ALTA | API commercial NÃO retreina (Anthropic confirma; OpenAI ZDR via aprovação) |
| **Subprocessors do OpenRouter** | MÉDIA | Verificar lista pública (Anthropic é cliente direto, sem subproc oculto) |
| **Logs OpenRouter padrão** | BAIXA | OpenRouter ZDR default — só loga metadata (não prompt) salvo se user opt-in logging |

### e) Provider policies (mai/2026 — verificar atual antes implementar)

| Provider | Default training? | Default retention | ZDR available? |
|---|---|---|---|
| **OpenRouter** | Não retém prompts | Apenas metadata (billing) | ✅ Per-request `zdr=true` param |
| **Anthropic API comercial** | **NÃO treina** ✅ | Standard (não especifica tempo) | ✅ Via enterprise agreement |
| **OpenAI API** | NÃO treina (since 2023) | **30 dias para abuse monitoring** | ⚠️ Via aprovação enterprise — NÃO default |
| **Google Gemini API** | Free tier: SIM treina | Pago: NÃO treina | Via Vertex AI enterprise |

**CRÍTICO Eric:** OpenRouter por si só NÃO faz transferência adicional (intermediário). Mas ele ROTEIA para o provider que processa sob política DELE. Para LGPD posture mínima: **forçar provider Anthropic** + `zdr=true` em todas chamadas + evitar Gemini free tier.

**Sources:**
- [OpenRouter Privacy Policy](https://openrouter.ai/privacy)
- [OpenRouter ZDR docs](https://openrouter.ai/docs/guides/features/zdr)
- [OpenRouter Provider Logging](https://openrouter.ai/docs/guides/privacy/provider-logging)
- [Anthropic Claude API Data Retention](https://platform.claude.com/docs/en/build-with-claude/api-and-data-retention)
- [Anthropic ZDR enterprise](https://privacy.claude.com/en/articles/8956058-i-have-a-zero-data-retention-agreement-with-anthropic-what-products-does-it-apply-to)
- [OpenAI Enterprise Privacy](https://openai.com/enterprise-privacy/)
- [Lei Geral de Proteção de Dados (LGPD)](https://www.gov.br/anpd/pt-br)

---

## Seção 4 — Custo estimado por análise × 4 doctypes

### Premissas declaradas

Por análise contrato CDC PF (Veicular baseline):
- OCR vision: 12 págs (varia 5-25)
- Markdown extraído: ~30k tokens
- 4 personas: cada 42k input + 5k output = 47k → 188k total
- Juiz revisor: 50k input + 3k output = 53k
- **TOTAL não-OCR: ~241k tokens; com OCR varia conforme provider**

**Variação por doctype (estimativa Atlas):**
| Doctype | Páginas | Tokens markdown | Multiplicador vs Veicular |
|---|---|---|---|
| FIES | 10 | ~25k | 0,9× |
| **Veicular** ⭐ | **12** | **~30k** | **1,0× (baseline)** |
| Bancário | 6 | ~15k | 0,55× |
| Imobiliário | 25 | ~62k | 2,1× |

### Tabela A — Custo por análise (Veicular baseline 12 págs)

| Cenário | OCR ($) | 4 Personas ($) | Juiz ($) | Total $/análise | **R$/análise** |
|---|---|---|---|---|---|
| **Economy** (Gemini Flash) | 0,002 | 0,19 | 0,05 | **$0,24** | **R$ 1,32** |
| **Mid** (Claude Haiku 4.5) | 0,020 | 0,38 | 0,10 | **$0,50** | **R$ 2,75** |
| **Premium** (Claude Sonnet 4.6) | 0,060 | 1,13 | 0,32 | **$1,51** | **R$ 8,30** |
| **Hybrid** ⭐ (Gemini Flash personas + Claude Sonnet 4.6 OCR+Juiz) | 0,060 | 0,19 | 0,32 | **$0,57** | **R$ 3,15** |

### Tabela B — Análises cabíveis em R$ 1500/mês (Veicular)

| Cenário | R$/análise | Análises/mês cabíveis | Por doctype (÷4) |
|---|---|---|---|
| Economy | R$ 1,32 | **~1135** | ~280/doctype/mês |
| Mid | R$ 2,75 | **~545** | ~135/doctype/mês |
| Premium | R$ 8,30 | **~180** | ~45/doctype/mês |
| **Hybrid** ⭐ | **R$ 3,15** | **~475** | **~120/doctype/mês** |

### Tabela C — Crossover analysis (impacto Imobiliário 2,1×)

| Cenário | Veicular R$ | Imobiliário R$ (2,1×) | Imobiliários/mês cabíveis |
|---|---|---|---|
| Economy | 1,32 | 2,77 | ~540 |
| Mid | 2,75 | 5,77 | ~260 |
| Premium | 8,30 | 17,43 | **~86** ⚠️ |
| **Hybrid** ⭐ | 3,15 | 6,61 | ~227 |

**Crossover real:** Premium puro queima budget se >180 análises Veicular OU >86 Imobiliário/mês. **Hybrid** é o sweet spot — preserva qualidade no OCR + Juiz (onde precisão importa) e economia nas 4 personas (onde paralelismo dilui erros individuais).

---

## Seção 5 — Recomendação Atlas (top picks acionáveis)

### a) OCR Vision recomendado: **`anthropic/claude-sonnet-latest`** (Claude Sonnet 4.6)

**Por quê:** 97,6% extração em layouts complexos jurídicos + 0,09% hallucination (decisivo para legal — invenção de cláusula é catastrófica) + Anthropic API comercial não treina + ZDR enterprise opcional.

**Custo:** ~$0,06/análise OCR (12 págs). Para 4 doctypes simultâneos, OCR é gargalo de qualidade — vale o premium aqui.

### b) Persona texto recomendado (4 personas paralelas): **`google/gemini-flash-latest`**

**Por quê:** $0,5/M input + $3/M output é o melhor preço entre vision-capable mainstream + 1M context (cabe contrato + 5 jurisprudências sem chunking) + qualidade suficiente para análise persona individual (4 personas redundantes diluem erro individual via Juiz consolidação).

**Custo:** ~$0,19/análise para 4 personas combinadas.

⚠️ **Atenção LGPD:** Gemini API pago NÃO treina, mas free tier SIM. Aria deve garantir billing pago em ADR-014.

### c) Juiz revisor (consolidação final): **`anthropic/claude-sonnet-latest`** (Claude Sonnet 4.6)

**Por quê:** Síntese das 4 personas + decisão final exige raciocínio jurídico premium. 0,09% hallucination crítico aqui — Juiz é a saída final ao cliente.

### d) Stack ideal Hybrid (R$ 1500/mês, 4 doctypes simultâneos)

```
S2 Upload PDF → S3 OCR Vision (Claude Sonnet 4.6, ~$0,06)
              → S4 4 Personas paralelas (Gemini Flash, ~$0,19)
              → S5 Juiz consolida (Claude Sonnet 4.6, ~$0,32)
              → S6 Output ao cliente

Custo médio: $0,57/análise (R$ 3,15)
Capacidade R$ 1500/mês: ~475 análises (~120/doctype)
```

### e) Backup / fallback strategy

1. **Claude Sonnet rate limited** → fallback `anthropic/claude-haiku-latest` (Haiku 4.5, $1/$5)
2. **Anthropic provider down** → fallback `openai/gpt-5.4` (similar quality, $2,50/$15)
3. **Custo excedendo budget** → modo "degraded": Gemini Flash em TUDO ($0,30/análise R$ 1,65), aceita -2pp accuracy

### f) Riscos pendentes para Aria (Phase 2 — ADRs)

1. **ADR-014 OpenRouter integration:**
   - SDK oficial OpenRouter vs HTTP direto via `httpx`?
   - Per-request `zdr=true` enforcement?
   - Retry strategy (exponential backoff, circuit breaker)?
   - Cost tracking middleware (decremento budget mensal)?

2. **ADR-015 Vision OCR architecture:**
   - Image preprocessing antes do envio (resize? OCR-pre fallback)?
   - Caching de OCR (mesmo PDF re-analisado evita re-OCR)?
   - Multi-page handling (envio paginado vs único)?
   - Fallback se vision LLM falhar (marker-pdf local como degraded mode)?

3. **ADR-016 Multi-doctype dispatcher:**
   - Registry pattern (lookup table doctype → personas) vs Strategy pattern (4 classes Persona)?
   - Como detectar doctype automaticamente (LLM classifier vs UI selector vs ambos)?
   - Jurisprudência por doctype (vault separado ou tags)?
   - Templates de petição diferenciados (D3 output formats)?

4. **ADR-017 LGPD compliance flow:**
   - Onde armazenar consent record (cookie, sessão, audit trail)?
   - Anonimização opcional pré-envio (CPF → hash) como Path B latente?
   - Audit log inclui consent timestamp + termo version?
   - Revogação consent: como invalida análise já feita?

---

## Sumário executivo a Eric

✅ **VIABILIDADE: GO** com stack Hybrid recomendado (Claude Sonnet 4.6 OCR+Juiz + Gemini Flash 4 personas).

📊 **Custo:** ~R$ 3,15/análise → **475 análises/mês cabem em R$ 1500** (média ~120/doctype/mês).

🛡️ **LGPD:** Path A viável com consentimento Art. 7º I + termo + disclaimer S2. Riscos não-mitigados explícitos. ZDR per-request OpenRouter + Anthropic API comercial = posture mais sólida possível em Path A.

⏭️ **Próximos passos:**
1. Aria desenha ADR-014/015/016/017 (Phase 2 Sprint 04)
2. Trinity escreve PRD v2.0.0 com 4 doctypes (Phase 3)
3. Sati redesenha UI com OrSheva brandbook (Phase 4)
4. Smith adversarial review do pivot completo (Phase 5)
5. Morpheus consolidação ORDEM 11 (Phase 6) — GO/NO-GO/PIVOT-PARCIAL

⚠️ **Pendências para Eric decidir antes de Aria começar:**
- Confirmar provider primário: Claude (recomendação) OR misto?
- Confirmar volume estimado mensal (475 capacity ≥ demanda real?)
- Autorizar billing OpenRouter (precisa $50+ saldo inicial)
- Termo de consentimento: Eric redige em paralelo a Phase 2-4

— Atlas, investigando a verdade 🔎
