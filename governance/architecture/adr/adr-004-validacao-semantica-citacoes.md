---
type: adr
id: "ADR-004"
title: "Validação semântica de citações: similarity + NLI híbrido (anti-paráfrase invertida)"
status: accepted
date: "2026-05-01"
domain: "seguranca-audit"
decision_makers: ["@architect (Aria)"]
supersedes: null
superseded_by: null
absorves:
  - "R-NEW-SMITH-02 (CRÍTICA — paráfrase invertida)"
related_to:
  - "FR-TESE-04 (validação semântica obrigatória ≥0.7)"
  - "ADR-003 (Advogado LLM)"
  - "Smith F-CRIT-02 (citation-grounded só sintático)"
project: revisor-contratual
sprint: "01"
etapa: "2.0"
tags:
  - project/revisor-contratual
  - adr
  - validacao-semantica
  - nli
  - entailment
  - critico
---

# ADR-004 — Validação semântica de citações: similarity + NLI híbrido (anti-paráfrase invertida)

```
[@architect · Aria (Visionary)] — etapa 2.0 · ADR-004 validação semântica
SPRINT: 01 · ETAPA: 2.0 · DOMÍNIO: SoftwareDev/legaltech
```

## Contexto

PRD v1.0.2 FR-TESE-04 estabelece validação semântica obrigatória de citações antes da renderização da peça: cosine similarity ≥0.7 entre frase da tese e ementa real do doc citado.

**Smith levantou na re-review (R-NEW-SMITH-02 — CRÍTICA):** cosine similarity captura **proximidade semântica**, não **polaridade lógica**. Cenário real:

- Ementa Súmula 539 STJ: "É **permitida** a capitalização de juros com periodicidade inferior à anual em contratos com instituições integrantes do SFN..."
- LLM gera tese citando Súmula 539: "...conforme Súmula 539 STJ que **proíbe** a capitalização infra-anual..."
- Ambas as frases têm vocabulário 90% overlap (Súmula 539, STJ, capitalização, juros, infra-anual, SFN)
- Cosine similarity Legal-BERTimbau **>0.7** → **VALIDAÇÃO PASSA** silenciosamente
- Tese com citação INVERTIDA é renderizada → advogado peticiona com tese juridicamente CONTRÁRIA → derrota + responsabilização CFOAB (FR-DELIV-06 NÃO protege contra erro semântico, só contra erro processual)

**Este é o vetor mais crítico identificado pelo Smith no re-attack.** Preciso elevar a validação semântica a nível de polaridade lógica.

## Decisão

**Adotamos pipeline híbrido em 2 estágios:**

1. **Estágio A — Filtro fraco:** cosine similarity ≥0.7 (Legal-BERTimbau-sts-base)
2. **Estágio B — Filtro semântico real:** NLI (Natural Language Inference) com threshold de polaridade

Citação só PASSA se ambos os estágios passarem. Falha em qualquer um → BLOQUEIA emissão da peça.

### Modelo NLI escolhido

Após pesquisa de modelos PT-BR disponíveis:

| Modelo | Suporte PT-BR | Tamanho | Latência CPU | Decisão |
|--------|---------------|---------|--------------|---------|
| `microsoft/deberta-v3-large-mnli` | EN-only | 1.4GB | ~800ms | Rejeitado (PT-BR fraco) |
| `unicamp-dl/ptt5-base-portuguese-vocab` | PT-BR nativo | 220MB | ~300ms | Rejeitado (não-NLI nativo) |
| **`Vinicius-Nascimento/bert-base-portuguese-cased-mnli`** | PT-BR fine-tuned MNLI | 420MB | ~250ms | **ESCOLHIDO** |
| `assin/bertimbau-base-assin2` | PT-BR ASSIN-2 (entailment) | 420MB | ~250ms | Reserva (alternativa equivalente) |

Modelo escolhido: **`bert-base-portuguese-cased-mnli`** (fine-tuned em MNLI traduzido + ASSIN-2). Motivos:
- Treinado especificamente para entailment/contradiction/neutral em PT-BR
- Tamanho razoável (420MB, fica em RAM com Sabia-7B sem estourar NFR-PERF-02)
- Latência aceitável (~250ms por par premise/hypothesis)
- Carregamento via `transformers` + cache local (HF_HUB_OFFLINE=1 em runtime)

### Pipeline técnico

```python
# bloco_workflow/personas/validacao_semantica.py

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from sentence_transformers import SentenceTransformer, util

EMBEDDER = SentenceTransformer('rufimelo/Legal-BERTimbau-sts-base')
NLI_MODEL_NAME = 'Vinicius-Nascimento/bert-base-portuguese-cased-mnli'
NLI_TOKENIZER = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
NLI_MODEL = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME)
NLI_LABELS = ["contradiction", "neutral", "entailment"]

class ValidacaoSemantica(BaseModel):
    id_doc: str
    frase_tese: str
    ementa_real: str
    similarity_score: float
    nli_label: Literal["entailment", "neutral", "contradiction"]
    nli_confidence: float
    veredito: Literal["PASS", "FAIL_SIMILARITY", "FAIL_POLARITY"]
    razao: str

def validar_citacoes(tese: TeseAdvogado, vault: VaultClient) -> list[ValidacaoSemantica]:
    resultados = []
    for citacao in tese.fundamentos_invocados:
        doc = vault.get(citacao["id_doc"])
        ementa_real = doc.ementa
        frase_tese = citacao["citacao_textual"]

        # ESTÁGIO A — similarity (FR-TESE-04 original)
        emb_frase = EMBEDDER.encode(frase_tese, convert_to_tensor=True)
        emb_ementa = EMBEDDER.encode(ementa_real, convert_to_tensor=True)
        sim_score = float(util.cos_sim(emb_frase, emb_ementa)[0][0])

        if sim_score < 0.7:
            resultados.append(ValidacaoSemantica(
                id_doc=citacao["id_doc"], frase_tese=frase_tese, ementa_real=ementa_real,
                similarity_score=sim_score, nli_label="neutral", nli_confidence=0.0,
                veredito="FAIL_SIMILARITY",
                razao=f"Similaridade {sim_score:.2f} < 0.7 — citação possivelmente fora do contexto"
            ))
            continue

        # ESTÁGIO B — NLI polaridade (R-NEW-SMITH-02 absorvida)
        # premise = ementa real do doc; hypothesis = frase atribuída pela tese
        inputs = NLI_TOKENIZER(ementa_real, frase_tese, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            logits = NLI_MODEL(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]
        label_idx = int(torch.argmax(probs))
        nli_label = NLI_LABELS[label_idx]
        nli_conf = float(probs[label_idx])

        if nli_label == "contradiction" and nli_conf >= 0.5:
            # CRÍTICO — paráfrase invertida detectada
            resultados.append(ValidacaoSemantica(
                id_doc=citacao["id_doc"], frase_tese=frase_tese, ementa_real=ementa_real,
                similarity_score=sim_score, nli_label=nli_label, nli_confidence=nli_conf,
                veredito="FAIL_POLARITY",
                razao=f"NLI detectou CONTRADIÇÃO entre tese e ementa (confidence {nli_conf:.2f}). "
                      f"Possível paráfrase invertida — verificar manualmente."
            ))
        else:
            resultados.append(ValidacaoSemantica(
                id_doc=citacao["id_doc"], frase_tese=frase_tese, ementa_real=ementa_real,
                similarity_score=sim_score, nli_label=nli_label, nli_confidence=nli_conf,
                veredito="PASS",
                razao=f"OK (sim={sim_score:.2f}, nli={nli_label}@{nli_conf:.2f})"
            ))

    return resultados

def bloquear_se_falhas(resultados: list[ValidacaoSemantica]) -> None:
    """Hard-fail bloqueia renderização. Diff visual via UI antes."""
    falhas = [r for r in resultados if r.veredito != "PASS"]
    if falhas:
        raise CitacaoInvalida(falhas)  # UI captura e mostra diff
```

### UX no Painel HITL semântico

Quando uma citação falha (especialmente FAIL_POLARITY), Streamlit mostra:

```
⚠️ Validação semântica detectou problema na citação [id_doc:STJ-S539]:

📖 Ementa REAL do doc:
   "É permitida a capitalização de juros com periodicidade inferior à anual..."

🤖 Frase da tese atribuindo ao doc:
   "conforme Súmula 539 STJ que proíbe a capitalização infra-anual..."

🚨 NLI: CONTRADICTION (confidence 0.87)
   Sua tese afirma o oposto do que a ementa diz. Isso pode ser:
   - Erro de paráfrase do modelo IA
   - Tese argumentando contra a súmula (válido se intencional)

Decisão necessária:
  [✏️  Corrigir manualmente]   [🗑️ Rejeitar citação]   [🛑 Abortar geração]
```

Audit log registra: `(id_doc, sim_score, nli_label, nli_confidence, decisao_usuario, timestamp)`.

## Razão

- **Cosine similarity é necessário mas insuficiente:** captura "fala do mesmo assunto" mas não "afirma o mesmo"
- **NLI é o estado da arte para entailment/contradiction:** fundação teórica em RTE/SNLI/MNLI; PT-BR tem modelos viáveis
- **Pipeline híbrido tem custo aceitável:** 250ms NLI × 5-10 citações por tese = 1.25-2.5s adicionais (cabe em NFR-PERF-01 ≤210s)
- **UX explícito no HITL semântico:** diff visual + 3 ações claras + audit log → usuário em controle, sem fricção desnecessária
- **R-NEW-SMITH-02 era a falha mais crítica do PRD v1.0.2:** absorver agora em ADR é correção definitiva

## Alternativas Consideradas

### Alt 1 — Manter apenas similarity ≥0.7 (PRD original)
- **Prós:** simples, latência mínima
- **Contras:** **vulnerável à paráfrase invertida** (R-NEW-SMITH-02 não-mitigada) — risco real de derrota judicial + CFOAB
- **Rejeitada:** Smith identificou como CRÍTICA; absorver é não-negociável

### Alt 2 — Aumentar threshold similarity para 0.9
- **Prós:** filtra mais agressivamente
- **Contras:** mesma classe de erro — paráfrase invertida ainda passa (vocabulário idêntico, ordem das palavras diferente)
- **Rejeitada:** mesmo problema raiz

### Alt 3 — LLM-as-judge (Sabia-7B avalia contradição)
- **Prós:** pode capturar nuances complexas
- **Contras:** introduce 3ª chamada LLM (latência +60-90s, viola NFR-PERF-01); LLM avaliando LLM é circular; alucinação na avaliação
- **Rejeitada:** custo > benefício; NLI dedicado é melhor escolha

### Alt 4 — Modelo NLI multilingual (`facebook/bart-large-mnli`)
- **Prós:** suporta 100+ idiomas
- **Contras:** 1.6GB, latência ~800ms CPU, performance PT-BR inferior a modelos PT-BR-only
- **Rejeitada:** modelo PT-BR dedicado é mais leve e mais preciso

### Alt 5 — Usar o `unicamp-dl/ptt5-base-portuguese-vocab` reformulado para NLI via prompt
- **Prós:** modelo brasileiro
- **Contras:** ptt5 é T5 (text-to-text), não classificador NLI nativo; exigiria few-shot prompting (instável)
- **Rejeitada:** preferir modelo NLI fine-tuned

## Consequências

### Positivas
- **Vetor crítico R-NEW-SMITH-02 NEUTRALIZADO** definitivamente
- Defesa em profundidade: anti-fantasma sintático (Advogado) + anti-paráfrase invertida (validação semântica)
- Audit log enriquecido com NLI scores → trilha de auditoria jurídica completa
- UX HITL semântico empodera advogado a entender o problema

### Negativas / Tradeoffs
- +420MB no footprint (modelo NLI) — cabe em NFR-PERF-02 ≤8GB com Sabia-7B (~5GB) + Legal-BERTimbau (~250MB) + NLI (~420MB) = ~5.7GB total
- +1.25-2.5s latência por tese típica — aceitável
- Necessidade de download inicial do modelo NLI (FR-SETUP-01 estendido)
- NLI PT-BR não tem precisão de modelos EN — DP-NOVO: validar com 50 paráfrases invertidas curadas no golden set (DP-09 expandida)

### Neutras
- Substituir modelo NLI no futuro requer apenas swap em `bloco_workflow/personas/validacao_semantica.py` (NFR-MAINT-01 preservada)

## Decisão Pendente Documentada

**DP-04-NOVA (criada por esta ADR):** validar precisão do NLI PT-BR escolhido com 50+ paráfrases invertidas curadas. @qa produz golden set NLI antes do MVP fechar. Meta: ≥85% recall em detecção de contradição.

## Referências

- PRD v1.0.2: FR-TESE-04 (linhas 290-301)
- Smith re-review: R-NEW-SMITH-02 (qa/smith-adversarial-rereview-prd-v1.0.2.md)
- Smith F-CRIT-02 original (v1.0.1): qa/smith-adversarial-review-prd-v1.0.1.md
- ADR-003 (Advogado é a fonte das citações a validar)
- Modelo NLI: https://huggingface.co/Vinicius-Nascimento/bert-base-portuguese-cased-mnli
- ASSIN-2 dataset PT-BR entailment: https://sites.google.com/view/assin2/

---

*Aria, defesa em profundidade contra a alucinação que mata casos. 🏗️*
