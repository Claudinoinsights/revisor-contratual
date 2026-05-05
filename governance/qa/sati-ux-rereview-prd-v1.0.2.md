---
type: tribunal-review
title: "Sati — Re-Revisão UX do PRD v1.0.2 (RE-Tribunal Severo, primeiro reviewer)"
project: revisor-contratual
reviewer: "@ux-design-expert (Sati)"
date: "2026-05-01"
artefatos_revisados:
  - "prd/prd-v1.0.2.md"
  - "prd/ux-spec-detail-v1.0.md (anexo NOVO)"
predecessor_review: "qa/sati-ux-review-prd-v1.0.1.md (revisão anterior — 11 EV-IDs)"
predecessor_handoff: "H-S01-E1.3-pm2sat3"
tags:
  - project/revisor-contratual
  - tribunal-severo
  - ux-rereview
  - sati
  - re-tribunal
---

# Re-Revisão UX do PRD v1.0.2 — Sati (Re-Tribunal Severo, primeiro reviewer)

## 📋 VEREDICTO formato Ordem 8

```
[@ux-design-expert · Sati] — review etapa 1.3 · re-revisão PRD v1.0.2
VEREDICTO: PASS
EVIDÊNCIAS:
  ✅ 4/4 EV ALTA Sati ABSORVIDAS (EV-01, EV-04, EV-05, EV-11)
  ✅ 7/7 EV MÉDIA Sati ABSORVIDAS no anexo ux-spec-detail-v1.0.md
  ✅ Microcopy HITL fielmente reproduzido em FR-JUIZ-02 estendido
  ✅ Inventário Atomic Design completo em anexo
  ✅ NFR-A11Y-01 com WCAG 2.1 AA + Lighthouse ≥90 + skip-link + caption
  ✅ FR-DELIV-06 (CFOAB) com PainelRevisaoCFOAB bem especificado
  ✅ FR-CONFIG-01 com SeletorLLMTier comparativo
RESSALVAS NOVAS (mínimas — 3 itens não-bloqueantes):
  Ver lista abaixo
RECOMENDAÇÃO: continuar → Smith re-validar (não retornar a Morgan)
```

**Por que PASS (não PASS-COM-RESSALVA):**
- Todos os 11 EV-IDs anteriores foram absorvidos integralmente
- 3 ressalvas novas são MÍNIMAS (refinamentos UX de superfície, não fundação)
- Não justifica retornar a Morgan (Aria pode endereçar na ADR de design system OU iteração v1.0.3)

---

## ✅ Confirmação de Absorção (4 EV ALTA + 7 EV MÉDIA)

### EV ALTA absorvidas

| EV-ID Sati | Onde está em v1.0.2 | Status |
|-----------|---------------------|:------:|
| **EV-01** (HITL detail) | FR-JUIZ-02 estendido (linhas 312-333): BadgeAderencia + 3 resumos C1/C2/C3 + 3 botões com cor/ícone/microcopy + textarea com placeholder contextual + counter visual + validação anti-bypass | ✅ ABSORVIDO INTEGRALMENTE |
| **EV-04** (WCAG ausente) | NFR-A11Y-01 (linhas 574-583): WCAG 2.1 AA + Lighthouse ≥90 + skip-link + caption + th scope + cor não única + teclado + prefers-reduced-motion + alt-text | ✅ ABSORVIDO + JUSTIFICATIVA LBI |
| **EV-05** (LLM_TIER UX) | FR-CONFIG-01 (linhas 469-479): SeletorLLMTier 3 cards + indicador atual + botão Aplicar+reiniciar + disclaimer + backup .env | ✅ ABSORVIDO |
| **EV-11** (Atomic Design) | Anexo `prd/ux-spec-detail-v1.0.md` (234 linhas): Atoms (10) + Molecules (8) + Organisms (6) + Templates (9) + Pages (10) | ✅ ABSORVIDO + EXPANDIDO |

### EV MÉDIA absorvidas no anexo

| EV-ID Sati | Onde está no anexo | Status |
|-----------|--------------------| :------:|
| **EV-02** (ETA loading) | Seção 2.4 "Estados de Loading" — 9 etapas com microcopy + ETA | ✅ |
| **EV-03** (Resultado preview) | Seção 3.2 "Estados Página Resultado" — hierarquia + preview iframe + cópia citações | ✅ |
| **EV-06** (microcopy upload) | Seção 2.3 "Erros de Upload" — 8 cenários com microcopy específico | ✅ |
| **EV-07** (Inviabilidade UX) | Seção 2.5 "Página Inviabilidade" — UX terapêutica + ações concretas por C1/C2/C3 | ✅ |
| **EV-08** (Outcomes ≤30s) | Seção 2.6 "Página Outcomes" — quick actions + bulk update + auto-save | ✅ |
| **EV-09** (microcopy HITL) | Seção 2.1 "Painel HITL" + duplicado em FR-JUIZ-02 estendido | ✅ |
| **EV-10** (UX integrações) | Seção 2.7 "UX Integrações" — DataJud modal, Tema 1378 banner, UF autodetecção, LLM_TIER toggle | ✅ |

**11 de 11 absorvidos. Nenhum perdido.**

---

## ⚠️ 3 Ressalvas NOVAS (não-bloqueantes — Sati no re-tribunal)

### R-NEW-01 — FR-CONFIG-01: "Aplicar e reiniciar" precisa avisar usuário sobre perda de sessão

**Onde:** FR-CONFIG-01 linha 476

**Problema:** "Botão 'Aplicar e reiniciar' — persiste em .env e reinicia Streamlit" — mas se o advogado tem upload em curso ou está no Painel HITL, reinício PERDE TUDO.

**Recomendação (não-bloqueante):**
- Antes de reiniciar, verificar estado do app:
  - Se há contrato em processamento → modal "Há análise em curso. Reiniciar agora vai perder o progresso. Esperar conclusão? [Esperar / Reiniciar mesmo assim]"
  - Se há decisão HITL pendente → modal "Há decisão pendente. Concluir antes? [Concluir / Reiniciar mesmo assim]"
- Aria pode adicionar isso na ADR de gerenciamento de estado OU Morgan refina em v1.0.3

### R-NEW-02 — FR-RAG-02: UX para mostrar vigência da citação

**Onde:** FR-RAG-02 estendido + FR-RAG-01 schema (vigente_em campo novo)

**Problema:** PRD agora filtra docs por vigência (anti-superseded), mas UX não expõe ao advogado QUANDO o doc citado vigorava. Se advogado vai protocolar petição em 2026 com contrato de 2023, ele quer saber: "Súmula X estava vigente em 2023 (data do contrato), foi superseded em 2024, estou usando vigência correta na época do contrato".

**Recomendação:**
- Adicionar ao CardCitacaoJuridica (já no anexo) um badge: "Vigente em {data_assinatura_contrato}" ou "⚠️ Superseded em {YYYY-MM-DD}, mas vigente quando do contrato"
- Aria detalha em ADR de design system OU Morgan refina em v1.0.3

### R-NEW-03 — FR-SETUP-01 + FR-BACKUP-01: UX de erro/falha não detalhada

**Onde:** FR-SETUP-01 (bootstrap CLI) + FR-BACKUP-01 ("WARN visível no header")

**Problema:** 
- FR-SETUP-01 fala em "mensagem clara de remediação" mas não cita formato (CLI colorido? prompt interativo?)
- FR-BACKUP-01 fala em "WARN visível no header" mas não detalha (tooltip? toast? badge persistente?)

**Recomendação:**
- Para FR-SETUP-01: usar `rich` (lib Python para CLI bonito) com cores + tabela de opções
- Para FR-BACKUP-01: badge laranja persistente no header com tooltip "Backup falhou em {timestamp}. [Tentar agora] [Configurações]" + toast inicial 5s
- Aria detalha OU Morgan refina em v1.0.3

---

## 🎨 O que está EXCEPCIONAL no v1.0.2 (reconhecimento)

Morgan executou esse PATCH com cirurgia e empatia. Pontos de destaque:

1. **FR-DELIV-06 (CFOAB)** — Morgan absorveu INTEGRALMENTE a recomendação do Smith e expandiu com microcopy completo no anexo. Disclaimer rodapé citando art. 32 OAB + Provimento 205/2021 é elegante e funcionalmente protetor.

2. **FR-JUIZ-02 estendido** — Microcopy HITL que propus em EV-09 está LITERALMENTE reproduzido. Cor + ícone + texto explícito dos 3 botões. Validação anti-bypass do Smith integrada sem fricção.

3. **Anexo `ux-spec-detail-v1.0.md`** — Inventário Atomic Design EXPANDIDO além do que propus (Morgan adicionou InputDecimal, DatePickerBR, AlertaSessaoExpirando que eu não havia inventariado). 

4. **Notas para Aria (Seção 4 do anexo)** — questões de design system (Streamlit nativo vs CSS injetado, tokens de cores oficiais dos tribunais, tipografia serif para textos longos) são EXATAMENTE o que Aria precisa para ADR.

5. **Change log v1.0.2** — append-only, detalhado item por item, com classificação clara (CRITICAL/HIGH/MEDIA + adiados/aceitos). Auditável.

---

## 📋 Recomendação Sati ao re-tribunal

**Veredito: PASS**

PRD v1.0.2 absorveu integralmente meus 11 EV-IDs. As 3 ressalvas novas são **refinamentos de superfície** que não justificam retornar a Morgan — podem ir para iteração v1.0.3 OU ser detalhadas por Aria em ADR de design system.

**Próximo passo:** handoff para Smith re-atacar (H-S01-E1.3-sat2smi3). Smith VAI verificar se os 6 CRITICAL dele foram realmente endereçados — minha verificação foi UX-focada, Smith precisa validar segurança/legal/hallucination/operação/etc.

---

## 🔗 Referências

- PRD: `prd/prd-v1.0.2.md` (PATCH cirúrgico do v1.0.1)
- Anexo NOVO: `prd/ux-spec-detail-v1.0.md` (Atomic Design + microcopy)
- Revisão anterior: `qa/sati-ux-review-prd-v1.0.1.md` (11 EV-IDs)
- Persona empática: P-USR-01 "Dr. Ricardo" (mantida)

---

*Sati, reconhecendo o trabalho que respeita o usuário 🎨*
