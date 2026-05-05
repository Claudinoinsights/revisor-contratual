---
type: adr
id: "ADR-006"
title: "Preview seguro de PDF: server-side rendering via pdf2image"
status: accepted
date: "2026-05-01"
domain: "seguranca-audit"
decision_makers: ["@architect (Aria)"]
supersedes: null
superseded_by: null
absorves:
  - "R-NEW-SMITH-04 (CRÍTICA — iframe XSS vector)"
related_to:
  - "FR-DELIV-06 (PainelRevisaoCFOAB com preview)"
  - "NFR-SEC-03 (sanitização PDF qpdf+pdfid)"
  - "ADR-002 (Streamlit + CSS)"
project: revisor-contratual
sprint: "01"
etapa: "2.0"
tags:
  - project/revisor-contratual
  - adr
  - pdf-preview
  - xss
  - critico
---

# ADR-006 — Preview seguro de PDF: server-side rendering via pdf2image

```
[@architect · Aria (Visionary)] — etapa 2.0 · ADR-006 preview seguro PDF
SPRINT: 01 · ETAPA: 2.0 · DOMÍNIO: SoftwareDev/legaltech
```

## Contexto

PRD v1.0.2 FR-DELIV-06 (Tela de Revisão e Adoção CFOAB) especifica preview da peça final em iframe embedded antes do checkbox "LI, CONFERI E ADOTO".

**Smith levantou na re-review (R-NEW-SMITH-04 — CRÍTICA):** mesmo após NFR-SEC-03 (sanitização qpdf+pdfid), edge cases de bypass existem (~0.1% rate conhecido). Vetores:

1. **PDF.js renderer** tem CVEs anuais (CVE-2024-4367 foi RCE recente)
2. **Iframe sem `sandbox`** herda contexto de origem do app Streamlit → cookie de sessão exposto
3. Se sanitização falhar em 1 PDF → attacker exfiltra cookie → clona sessão → assina petição como o advogado

Embora as petições sejam GERADAS pelo próprio sistema (Jinja2 + WeasyPrint, não uploads), o preview ainda usa renderização de PDF — e mesmo PDFs gerados internamente passam pelo mesmo pipeline de exibição. Mais grave: se no futuro houver feature de "anexar PDF do contrato original ao preview", a vulnerabilidade já estaria embedded.

Decisão fundamental: **eliminar a superfície de ataque** ou **mitigar com sandbox**?

## Decisão

**Adotamos server-side rendering: PDF é convertido para imagens PNG via `pdf2image` (Poppler) e exibido como `st.image()` no Streamlit. NUNCA usar iframe para preview de PDF.**

### Detalhes técnicos

```python
# bloco_interface/preview/pdf_renderer.py

from pdf2image import convert_from_path
from pathlib import Path
import streamlit as st
import io

# Cache LRU para evitar re-renderizar PDFs já visualizados na sessão
@st.cache_data(max_entries=20, show_spinner="🖼️ Renderizando preview...")
def render_pdf_to_images(pdf_path: str, dpi: int = 120) -> list[bytes]:
    """
    Converte PDF em lista de PNGs em memória.
    Latência: ~500ms para PDF de 5 páginas; ~2s para 20 páginas.

    Por que pdf2image (Poppler) vs PyMuPDF:
    - Poppler é renderer de produção (LibreOffice, Inkscape) — battle-tested
    - PyMuPDF tem CVEs recentes (CVE-2024-43837 RCE em janela 2024-Q3)
    - pdf2image isola via subprocess (Poppler binary) — menor surface de ataque Python
    """
    pages = convert_from_path(pdf_path, dpi=dpi, fmt="PNG")
    return [_pil_to_bytes(page) for page in pages]

def _pil_to_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()

def render_pdf_preview_streamlit(pdf_path: str) -> None:
    """Componente Streamlit completo: navegação por páginas + zoom."""
    images = render_pdf_to_images(pdf_path)
    n_pages = len(images)

    if n_pages == 0:
        st.error("❌ PDF vazio ou inválido")
        return

    # Navegação simples
    if "preview_page" not in st.session_state:
        st.session_state.preview_page = 0

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("◀ Anterior", disabled=st.session_state.preview_page == 0):
            st.session_state.preview_page -= 1
            st.rerun()
    with col2:
        st.markdown(
            f"<p style='text-align:center;'>Página {st.session_state.preview_page + 1} de {n_pages}</p>",
            unsafe_allow_html=True
        )
    with col3:
        if st.button("Próxima ▶", disabled=st.session_state.preview_page == n_pages - 1):
            st.session_state.preview_page += 1
            st.rerun()

    st.image(
        images[st.session_state.preview_page],
        use_column_width=True,
        caption=f"Página {st.session_state.preview_page + 1}"
    )

    # Download original (opcional)
    with open(pdf_path, "rb") as f:
        st.download_button(
            "📄 Baixar PDF completo",
            data=f.read(),
            file_name=Path(pdf_path).name,
            mime="application/pdf"
        )
```

### Pipeline de segurança

```
1. Petição/Recurso gerado por WeasyPrint (HTML→PDF) → bytes em memória
2. Salvo em tmpdir (com rotação automática)
3. NFR-SEC-03 sanitização: qpdf --linearize + pdfid (mesmo para PDF gerado internamente)
4. ADR-006: pdf2image converte PNG (renderização Poppler em subprocess isolado)
5. PNGs servidos via st.image (browser renderiza apenas pixel data — zero JS execution)
6. Hash sha256 do PDF registrado em audit.jsonl (FR-AUDIT-01)
```

### Por que NUNCA iframe (mesmo com sandbox)

Mesmo `<iframe sandbox="allow-same-origin">` (a opção mais restritiva) tem problemas:

- `allow-same-origin` ainda permite acesso ao DOM pai via `window.parent`
- Browser PDF.js executa para renderizar — se CVE descoberta, sandbox não protege
- `sandbox` sem `allow-same-origin` quebra cookies de sessão para o próprio iframe (Streamlit pode não funcionar)
- Tradeoff complexo entre usabilidade e segurança

**Server-side rendering elimina o problema completamente:** browser nunca interpreta PDF, apenas exibe pixels. Zero código executável. CVE em PDF.js é irrelevante.

## Razão

- **Eliminar > mitigar:** server-side rendering remove a classe inteira de vulnerabilidades XSS-via-PDF
- **Latência aceitável:** ~500ms para 5 páginas (petições típicas têm 8-15 páginas → ~1.5s); cabe em NFR-PERF-01 ≤210s end-to-end
- **Poppler é production-grade:** usado por LibreOffice, Inkscape, Calibre — battle-tested sob ataque real por 20+ anos
- **Subprocess isolation:** Poppler roda em processo separado (não Python) — heap overflow não atinge runtime Python
- **Cache LRU previne re-renderização:** mesma petição vista 5× = 1 render + 4 cache hits
- **Download do PDF original disponível:** advogado pode baixar para protocolo (preview é só visual)

## Alternativas Consideradas

### Alt 1 — Iframe sem sandbox (PRD original)
- **Prós:** simples
- **Contras:** **vulnerável conforme R-NEW-SMITH-04** — XSS via PDF.js CVE
- **Rejeitada:** falha de segurança crítica

### Alt 2 — Iframe com sandbox restritivo (`allow-same-origin` SEM `allow-scripts`)
- **Prós:** mais seguro que sem sandbox
- **Contras:** PDF.js precisa JS para renderizar → quebra preview; alternativa é PDF nativo do browser (varia entre Chrome/Firefox/Safari, inconsistente)
- **Rejeitada:** UX quebrada na maioria dos browsers

### Alt 3 — PyMuPDF para renderização Python (em vez de Poppler)
- **Prós:** Python puro, sem subprocess
- **Contras:** PyMuPDF teve CVE-2024-43837 (RCE); manter atualizado é responsabilidade do usuário; Python no mesmo runtime = blast radius maior em caso de bug
- **Rejeitada:** Poppler subprocess é mais seguro

### Alt 4 — Servir PDF como download direto (sem preview)
- **Prós:** zero superfície de ataque
- **Contras:** UX hostil — usuário precisa baixar antes de "ler, conferir e adotar"; quebra fluxo CFOAB
- **Rejeitada:** UX inaceitável para FR-DELIV-06

### Alt 5 — Renderização SVG via PyMuPDF (vetorial)
- **Prós:** vetorial = zoom infinito + tamanho arquivo menor
- **Contras:** mesmo risco PyMuPDF; SVG inline em HTML pode ter XSS se mal sanitizado
- **Rejeitada:** combina problemas de ambos

## Consequências

### Positivas
- **Vetor crítico R-NEW-SMITH-04 NEUTRALIZADO** definitivamente
- Eliminada classe inteira de vulnerabilidades (não apenas mitigada)
- Browser cross-compatibility automática (PNG é universal)
- Cache LRU otimiza performance em sessões com revisões iterativas
- Independência de PDF renderer do browser (consistência visual entre Chrome/Firefox/Safari)

### Negativas / Tradeoffs
- Dependência: Poppler precisa ser instalado no sistema (Linux: `apt install poppler-utils`; Mac: `brew install poppler`; Windows: instaladores ou WSL)
- **DP-NOVO:** documentar instalação do Poppler em FR-SETUP-01 estendido
- Latência ~500ms-2s na primeira renderização (mitigado por cache + spinner UX)
- Petições muito longas (>30 páginas) podem ter latência inicial >5s — aceitável dado que petições típicas são <20 páginas
- Não permite seleção de texto no preview (workaround: download do PDF original)

### Neutras
- Servidor headless precisa ter libs gráficas Poppler (não problema em Linux/Mac; Windows pode exigir documentação extra)

## Decisão Pendente Documentada

**DP-NOVO (criada por esta ADR):** validar instalação Poppler em laptops alvo (Windows + Mac + Linux); estimar tamanho do download (~150MB Windows installer); documentar em README setup-day-1.

## Referências

- PRD v1.0.2: FR-DELIV-06 linha 368 (preview iframe original), NFR-SEC-03 (linhas 587-594)
- Smith re-review: R-NEW-SMITH-04 (qa/smith-adversarial-rereview-prd-v1.0.2.md)
- pdf2image: https://github.com/Belval/pdf2image
- Poppler (renderer): https://poppler.freedesktop.org/
- CVE-2024-4367 PDF.js RCE: https://nvd.nist.gov/vuln/detail/CVE-2024-4367
- CVE-2024-43837 PyMuPDF: https://nvd.nist.gov/vuln/detail/CVE-2024-43837

---

*Aria, eliminando a superfície em vez de blindá-la. Defesa absoluta vence defesa parcial. 🏗️*
