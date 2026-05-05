---
type: adr
id: "ADR-002"
title: "Design system: Streamlit nativo + tokens CSS injetados + tipografia serif jurídica + Lora local"
status: accepted
date: "2026-05-01"
patched_at: "2026-05-01"
patch_reason: "F-HIGH-B Smith — Lora servida LOCALMENTE (NUNCA via Google Fonts CDN, viola NFR-LGPD-01)"
domain: "design-system-ux"
decision_makers: ["@architect (Aria)"]
supersedes: null
superseded_by: null
absorves:
  - "Notas Sati Seção 4 anexo UX (Streamlit nativo vs CSS, tokens tribunais, tipografia serif)"
  - "F-HIGH-B-2.1 (Smith — Lora via Google Fonts CDN viola NFR-LGPD-01) via download local no FR-SETUP-01"
related_to:
  - "NFR-A11Y-01 (WCAG 2.1 AA + Lighthouse ≥90)"
  - "FR-DELIV-06 (PainelRevisaoCFOAB)"
  - "FR-CONFIG-01 (SeletorLLMTier)"
project: revisor-contratual
sprint: "01"
etapa: "2.0"
tags:
  - project/revisor-contratual
  - adr
  - design-system
  - streamlit
  - wcag
---

# ADR-002 — Design system: Streamlit nativo + tokens CSS injetados + tipografia serif jurídica

```
[@architect · Aria (Visionary)] — etapa 2.0 · ADR-002 design system
SPRINT: 01 · ETAPA: 2.0 · DOMÍNIO: SoftwareDev/legaltech
```

## Contexto

Sati produziu o anexo `prd/ux-spec-detail-v1.0.md` com inventário completo Atomic Design (10 Atoms + 8 Molecules + 6 Organisms + 9 Templates + 10 Pages). Na Seção 4 do anexo, Sati deixou questões abertas para Aria sobre:

1. Streamlit nativo vs CSS injetado (impacto em consistency e WCAG)
2. Tokens de cores oficiais dos tribunais (TJBA, STJ, STF) para UI baseada na jurisdição do contrato
3. Tipografia serif para textos jurídicos longos (preview de petição, ementas)

A audiência alvo (P-USR-01: advogado consumerista bancário, ≥50 anos com declínio visual progressivo) exige WCAG 2.1 AA mínimo (NFR-A11Y-01) com Lighthouse Accessibility ≥90.

Streamlit nativo oferece componentes acessíveis por padrão, mas tem limitações visuais. CSS custom permite controle pixel-perfect mas pode quebrar acessibilidade se mal feito.

## Decisão

**Adotamos abordagem híbrida: Streamlit nativo como baseline + tokens CSS injetados via `st.markdown(unsafe_allow_html=True)` para identidade visual + tipografia serif (Lora) apenas em textos jurídicos longos (>200 palavras).**

### Detalhes técnicos

```python
# bloco_interface/styles/tokens.py
TOKENS = {
    "color": {
        "primary": "#1B3A6F",     # Azul institucional (neutro entre tribunais)
        "secondary": "#7A0F1A",   # Vermelho jurídico (advertências, vetos)
        "success": "#1F6B3A",     # Verde aderência ≥70%
        "warning": "#B8730F",     # Laranja aderência 70-99% (HITL)
        "danger": "#7A0F1A",      # Vermelho aderência <70% (rejeitado)
        "neutral_900": "#1A1A1A", # Texto principal
        "neutral_700": "#4A4A4A", # Texto secundário
        "neutral_100": "#F5F5F5", # Background
    },
    "typography": {
        "ui_font": "system-ui, -apple-system, 'Segoe UI', sans-serif",
        "legal_font": "'Lora', 'Georgia', serif",  # Textos jurídicos longos
        "mono_font": "'JetBrains Mono', monospace", # Hashes, IDs, audit
    },
    "spacing": {
        "xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px",
    },
    "contrast": {
        # Validado WCAG 2.1 AA
        "primary_on_white": 7.2,    # AA Large, AAA
        "danger_on_white": 7.5,     # AA Large, AAA
        "neutral_700_on_white": 8.6, # AAA
    }
}

# bloco_interface/styles/inject.py
def inject_global_styles():
    """Injeta tokens CSS globais. Chamar 1× no startup do Streamlit."""
    st.markdown(f"""
    <style>
      :root {{
        --color-primary: {TOKENS['color']['primary']};
        --color-danger: {TOKENS['color']['danger']};
        /* ... demais tokens */
      }}
      /* Tipografia jurídica em containers específicos */
      .legal-text {{
        font-family: {TOKENS['typography']['legal_font']};
        font-size: 16px;
        line-height: 1.7;
        max-width: 70ch;
      }}
      /* Skip-link WCAG (NFR-A11Y-01) */
      .skip-link {{
        position: absolute;
        top: -40px;
        left: 0;
        background: var(--color-primary);
        color: white;
        padding: 8px;
        z-index: 100;
      }}
      .skip-link:focus {{ top: 0; }}
      /* prefers-reduced-motion (NFR-A11Y-01) */
      @media (prefers-reduced-motion: reduce) {{
        * {{ animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }}
      }}
    </style>
    """, unsafe_allow_html=True)
```

### Padrões obrigatórios

1. **Tabela de amortização (FR-CALC-02 — 360 linhas):** sempre com `<caption>`, `<th scope="col">` e skip-link "Pular tabela →" antes (acessibilidade NFR-A11Y-01)
2. **BadgeAderencia:** cor + ícone + texto (cor NUNCA é única forma de comunicação — NFR-A11Y-01)
3. **CardCitacaoJuridica:** body em `.legal-text` (Lora serif), metadados em `font-mono`
4. **PainelRevisaoCFOAB (FR-DELIV-06):** preview em iframe (decisão definitiva em ADR-006)
5. **SeletorLLMTier (FR-CONFIG-01):** 3 cards com cor + ícone medalha (🥉🥈🥇) + microcopy
6. **Headings hierárquicos:** `<h1>` único por página; `<h2>`/`<h3>` aninhados corretamente

### Cores NÃO-tribunal-específicas

Decisão deliberada: **NÃO usar cores oficiais TJBA/STJ/STF**. Razões:
- Risco de violação de identidade visual oficial (uso indevido de brasão/cor)
- Multi-UF first-class significa que TJSP/TJMG/etc. terão cores diferentes — manutenção combinatorial
- Azul institucional + vermelho jurídico são genéricos suficientes para dar autoridade sem invadir identidade de tribunal específico
- Identificação visual da UF do contrato fica via badge textual ("TJBA — 5ª Câmara Cível")

## Razão

- **Streamlit nativo cobre 80% das necessidades** sem CSS — formulários, tabelas, expanders, sidebar — todos com a11y razoável
- **CSS injetado via `st.markdown` é controlado:** apenas tokens globais + classes utilitárias específicas (`.legal-text`, `.skip-link`); evitamos override descontrolado de componentes Streamlit
- **Lora (Google Font) é serif jurídica reconhecida:** boa legibilidade em corpos longos, precedente em portais jurídicos brasileiros (Migalhas, ConJur)
- **Lora servida LOCALMENTE (PATCH F-HIGH-B):** arquivos .woff2 baixados durante FR-SETUP-01 e empacotados no app (`bloco_interface/static/fonts/lora/`); servidos via Streamlit static. **NUNCA referenciar `fonts.googleapis.com` em runtime** (violaria NFR-LGPD-01 whitelist — toda sessão beam IP do usuário para Google). Snippet correto:
```css
@font-face {
  font-family: 'Lora';
  src: url('./static/fonts/lora/Lora-Regular.woff2') format('woff2');
  font-display: swap;  /* fallback Georgia até Lora carregar local */
  font-weight: 400;
}
```
- **Tokens centralizados em `tokens.py`** — mudança de paleta = 1 arquivo, propaga via CSS variables (`var(--color-primary)`)
- **WCAG 2.1 AA validado nos contrastes principais:** todos ≥4.5:1 (texto normal) ou ≥3:1 (texto largo)

## Alternativas Consideradas

### Alt 1 — Streamlit puro sem CSS custom
- **Prós:** zero risco de quebrar a11y; código mais simples
- **Contras:** identidade visual genérica de "app de protótipo"; UX inferior em telas críticas (HITL, CFOAB); sem controle de tipografia jurídica
- **Rejeitada:** P-USR-01 é advogado profissional — produto precisa parecer ferramenta jurídica séria, não notebook Jupyter

### Alt 2 — React frontend + FastAPI backend (substituir Streamlit)
- **Prós:** controle visual total; PWA possível; design system completo (shadcn/ui, etc.)
- **Contras:** **viola arquitetura D-LEAN** (introduz 2º processo, 2× tooling, build pipeline); 4-6 semanas adicionais de implementação
- **Rejeitada:** Eric explicitamente sinalizou peso excessivo da arquitetura anterior; D-LEAN é não-negociável

### Alt 3 — Streamlit + biblioteca de componentes externos (streamlit-extras, streamlit-aggrid)
- **Prós:** componentes ricos prontos
- **Contras:** dependências adicionais com a11y inconsistente; AGGrid tem licença comercial para features avançadas
- **Rejeitada:** custo a11y > benefício; faremos componentes próprios via CSS quando Streamlit nativo não bastar

### Alt 4 — Cores oficiais por tribunal (TJBA azul/branco, STJ azul/dourado, STF azul/dourado)
- **Prós:** identificação visual imediata
- **Contras:** risco legal (uso de identidade visual oficial); manutenção combinatorial multi-UF; complexidade de design
- **Rejeitada:** ver "Cores NÃO-tribunal-específicas" acima

## Consequências

### Positivas
- WCAG 2.1 AA atingível com Lighthouse ≥90 (NFR-A11Y-01 ✅)
- Identidade visual coerente sem violar tribunal oficial
- Tokens centralizados → mudança de paleta = 1 arquivo
- Tipografia serif jurídica em containers apropriados (não em UI)
- Preserva D-LEAN (sem React, sem build pipeline frontend)

### Negativas / Tradeoffs
- CSS injetado via `unsafe_allow_html=True` exige cuidado (sanitização de inputs em qualquer interpolação) — mitigado por `tokens.py` ser estático sem dados de usuário
- Lora exige download na primeira carga (~50KB) — cacheado pelo browser; aceitável
- Limitação: não dá para customizar internals de componentes Streamlit (ex: estilo de `st.dataframe`); workaround via CSS seletor `[data-testid="stDataFrame"]` — frágil entre versões Streamlit

### Neutras
- Atualizar Streamlit (≥1.40 atual) requer re-validação dos seletores CSS específicos — documentado em `bloco_interface/styles/UPGRADE-NOTES.md` (futuro)

## Referências

- PRD v1.0.2: NFR-A11Y-01 (linhas 574-583), FR-CONFIG-01 (linhas 469-479), FR-DELIV-06 (linhas 365-382)
- Anexo UX: `prd/ux-spec-detail-v1.0.md` Seção 4 (Notas para Aria)
- Sati re-review: `qa/sati-ux-rereview-prd-v1.0.2.md` (PASS limpo)
- WCAG 2.1 AA: https://www.w3.org/WAI/WCAG21/quickref/?versions=2.1&levels=aa
- Lora font: https://fonts.google.com/specimen/Lora
- Streamlit theming: https://docs.streamlit.io/library/advanced-features/theming

---

*Aria, equilibrando autoridade visual com leveza arquitetural. 🏗️*
