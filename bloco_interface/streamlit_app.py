"""Streamlit UI — Revisor Contratual (frontend local com tokens orsheva).

Aplicação 100% local que envolve a CLI existente (revisar/init-audit/populate-vault).
NFR-LGPD-01 preservado: roda em localhost, PDFs nunca saem da máquina.

Decisões de design:
  - D-UI-1.0-A: Streamlit single-page (sem multi-page) — single-process simplifica
  - D-UI-1.0-B: Tokens orsheva-brandbook via CSS injetado (st.markdown unsafe_allow_html)
  - D-UI-1.0-C: Wrapper sobre revisar_contrato (mesma lógica da CLI)
  - D-UI-1.0-D: Lora local font NÃO incluída no skeleton — serve via Google Fonts CDN no MVP UI

Para rodar:
  streamlit run bloco_interface/streamlit_app.py

Ainda em SKELETON — STORY UI-1 do Sprint 02 polirá interações (progress bar, audit viewer, etc).
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime
from pathlib import Path

import streamlit as st


# ─────────────────────────────────────────────────────────────────────
# Defaults persistentes (replica da CLI — D-MOR-4.1-F)
# ─────────────────────────────────────────────────────────────────────

DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "revisor-contratual"
DEFAULT_VAULT_DB = DEFAULT_DATA_DIR / "vault.db"
DEFAULT_AUDIT_PATH = DEFAULT_DATA_DIR / "audit.jsonl"
DEFAULT_GENESIS_LOCK = DEFAULT_DATA_DIR / ".audit-genesis.lock"
DEFAULT_BACEN_CACHE = DEFAULT_DATA_DIR / "bacen-cache"


# ─────────────────────────────────────────────────────────────────────
# Page config + tokens orsheva
# ─────────────────────────────────────────────────────────────────────


def inject_brand_tokens() -> None:
    """Injeta tokens orsheva via CSS (Google Fonts + custom tokens)."""
    fonts_link = (
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?'
        'family=Fraunces:opsz,wght@9..144,300..900&'
        'family=Manrope:wght@300;400;500;600;700;800&'
        'family=JetBrains+Mono:wght@400;500&'
        'display=swap" rel="stylesheet">'
    )

    tokens_css = (Path(__file__).parent / "streamlit_tokens.css").read_text(encoding="utf-8")

    st.markdown(
        f'{fonts_link}<style>{tokens_css}</style>',
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Header com identidade orsheva."""
    st.markdown(
        """
        <div style="margin-bottom: 32px;">
          <div class="brand-eyebrow">Revisor Contratual · v0.1.0 MVP</div>
          <h1 class="brand-display" style="font-size: 3rem; margin: 0;">
            Análise jurídica local<br>
            de contratos bancários
          </h1>
          <p style="font-family: var(--f-body); color: var(--fg-muted); font-size: 1.125rem; max-width: 580px; margin-top: 16px; line-height: 1.5;">
            Sistema 100% on-premise (LGPD): seu PDF nunca sai da máquina.
            Análise em ≤210s com tese jurídica + fundamentação BACEN/STJ/STF.
          </p>
          <div class="brand-divider"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_veredict_badge(veredito: str) -> str:
    """HTML de badge para o veredito."""
    classes = {
        "APROVADO_100": "verdict-aprovado-100",
        "APROVADO_COM_RISCO_HITL": "verdict-aprovado-hitl",
        "REJEITADO": "verdict-rejeitado",
    }
    css_class = classes.get(veredito, "verdict-aprovado-hitl")
    return f'<div class="verdict-badge {css_class}">{veredito}</div>'


# ─────────────────────────────────────────────────────────────────────
# Sidebar — config + actions
# ─────────────────────────────────────────────────────────────────────


def render_sidebar() -> dict:
    """Sidebar com configurações + retorna dict de overrides."""
    with st.sidebar:
        st.markdown(
            '<div class="brand-eyebrow">Configurações</div>',
            unsafe_allow_html=True,
        )

        st.markdown("### Overrides do contrato")
        uf = st.text_input("UF (sigla)", value="", placeholder="BA, SP, RJ...", max_chars=2)
        data_assinatura = st.date_input(
            "Data assinatura",
            value=None,
            format="DD/MM/YYYY",
        )

        st.markdown("### LLM")
        tier = st.selectbox(
            "Tier do Advogado",
            options=["premium", "balanced", "lean"],
            index=0,
            help="premium=Sabia-7B (5GB) | balanced=Qwen 7B (4.5GB) | lean=Qwen 3B (2GB)",
        )
        top_k = st.slider("Top-K vault", min_value=1, max_value=20, value=5)

        st.markdown("### Setup")
        if st.button("🔧 Init audit (1× setup)", type="secondary"):
            st.info("Use a CLI: `revisor init-audit` (veja docs/sop-rotacao-auth-cookie-key.md)")

        if st.button("📚 Populate vault", type="secondary"):
            st.info("Use a CLI: `revisor populate-vault --source all`")

        st.markdown("---")
        st.caption("Streamlit UI v0.1.0 · skeleton")
        st.caption("[Repositório](https://github.com/Claudinoinsights/revisor-contratual)")

    return {
        "uf": uf if uf else None,
        "data_assinatura": data_assinatura,
        "tier": tier,
        "top_k": top_k,
    }


# ─────────────────────────────────────────────────────────────────────
# Main flow — upload PDF + revisar
# ─────────────────────────────────────────────────────────────────────


def render_main(overrides: dict) -> None:
    """Fluxo principal de revisão."""
    st.markdown("## Revisão de contrato")

    uploaded = st.file_uploader(
        "Selecione o PDF do contrato",
        type=["pdf"],
        accept_multiple_files=False,
        help="O arquivo NUNCA é enviado para servidor — processado 100% localmente.",
    )

    if uploaded is None:
        st.markdown(
            """
            <div style="padding: 32px; background: var(--bg-elev); border: 1px solid var(--line); border-radius: 12px; margin-top: 24px;">
              <div class="brand-eyebrow">Como funciona</div>
              <ol style="font-family: var(--f-body); color: var(--fg); padding-left: 20px;">
                <li>Faça upload do PDF do contrato (CDC PF Veículos suportado em v0.1.0)</li>
                <li>Override UF/data se metadata não detectada automaticamente</li>
                <li>Aguarde análise (~120-180s com Ollama local)</li>
                <li>Receba veredito (APROVADO_100 / APROVADO_COM_RISCO_HITL / REJEITADO)</li>
                <li>Inspecione audit trail forense (HMAC chain)</li>
              </ol>
              <p style="color: var(--fg-muted); font-size: 0.875rem; margin-bottom: 0;">
                Pré-requisitos: <code>revisor init-audit</code> + <code>revisor populate-vault</code> rodados.
                Detalhes em <a href="https://github.com/Claudinoinsights/revisor-contratual/blob/main/docs/sop-revisar-pdf.md" target="_blank">SOP-003</a>.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Upload realizado
    st.success(f"📄 Carregado: **{uploaded.name}** ({len(uploaded.getvalue())/1024:.1f} KB)")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(
            f"Tier: **{overrides['tier']}** · Top-K vault: **{overrides['top_k']}** · "
            f"UF override: **{overrides['uf'] or 'auto'}** · "
            f"Data override: **{overrides['data_assinatura'] or 'auto'}**"
        )
    with col2:
        run = st.button("⚡ Revisar contrato", type="primary", use_container_width=True)

    if run:
        st.markdown("### Pipeline em execução")

        # SKELETON: indicar passos do pipeline (sem invocar LLM real)
        # STORY UI-1 do Sprint 02 implementará invocação real com asyncio + progress

        steps = [
            ("📄 Parsing PDF (PyMuPDF)", 0.1),
            ("💰 Cálculo Decimal (Price + simples)", 0.1),
            ("📊 BACEN SGS (taxa média modalidade)", 0.1),
            ("🔍 Vault busca híbrida (BM25 + vetorial)", 0.1),
            ("👨‍⚖️ Personas paralelas (Advogado + Economista)", 0.1),
            ("⚖️ Juiz Python puro (C1/C2/C3)", 0.1),
            ("📝 Audit log (HMAC chain)", 0.1),
        ]

        progress = st.progress(0)
        status = st.empty()
        for i, (step, _delay) in enumerate(steps):
            status.write(f"**Passo {i+1}/7:** {step}")
            progress.progress((i + 1) / len(steps))
            # Em produção: await pipeline real

        status.empty()
        progress.empty()

        st.warning(
            "🚧 **Skeleton UI** — invocação real do pipeline será implementada na STORY UI-1 do Sprint 02. "
            "Por agora, use a CLI: `revisor revisar contrato.pdf --uf BA --data-assinatura 2024-03-15`"
        )

        # Demo de veredito (mock)
        st.markdown("### Resultado (mock para demonstração de design)")
        st.markdown(
            render_veredict_badge("APROVADO_COM_RISCO_HITL"),
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div style="margin-top: 24px; padding: 24px; background: var(--bg-elev); border: 1px solid var(--line); border-radius: 12px;">
              <div class="brand-eyebrow">Aderência</div>
              <div class="brand-display" style="font-size: 4rem; color: var(--accent);">83.3%</div>
              <div style="font-family: var(--f-body); color: var(--fg-muted); margin-top: 16px;">
                <p><strong>C1</strong> (BACEN divergência): 1.00 · 1.85pp acima da média</p>
                <p><strong>C2</strong> (max peso vinculação): 0.50 · STJ-S539 (peso 4)</p>
                <p><strong>C3</strong> (jurisdição): 1.00 · 2 docs TJBA encontrados</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────


def render_footer() -> None:
    st.markdown(
        """
        <div style="margin-top: 64px; padding-top: 32px; border-top: 1px solid var(--line); color: var(--fg-muted); font-family: var(--f-body); font-size: 0.875rem; text-align: center;">
          <p>
            <strong>Revisor Contratual</strong> · v0.1.0 MVP ·
            <a href="https://github.com/Claudinoinsights/revisor-contratual" target="_blank" style="color: var(--accent);">github.com/Claudinoinsights/revisor-contratual</a>
          </p>
          <p style="margin-top: 8px;">
            Design system: <strong>Orsheva 7</strong> · Iluminar · Estruturar · Consolidar
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────


def main() -> None:
    st.set_page_config(
        page_title="Revisor Contratual",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_brand_tokens()
    render_header()

    overrides = render_sidebar()
    render_main(overrides)

    render_footer()


if __name__ == "__main__":
    main()
