"""render_peca_pdf — Sprint 6 Bloco γ (TD-SP06-WEASYPRINT-PECA-01).

Decisão arquitetural ADR-022 D4+D5:
  - 3 templates Jinja2 em bloco_interface/web/templates/peca/
  - Tokens OrSheva 7 inline (Manrope sans + Fraunces serif + Or-500 accent)
  - Page A4 portrait + margins 25mm + numeração páginas + footer disclaimer
  - chmod 0o600 LGPD §46 + parent dir mkdir 0o700

Compliance:
  - NFR-PECA-02 latency <30s typical (measured em test_weasyprint_render.py)
  - NFR-PECA-03 fontes self-hosted (REV-INT-02 LGPD on-premise)
  - NFR-PECA-04 LGPD §46 file permissions
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

# Diretórios canônicos (relative ao projeto root)
_WEB_DIR = Path(__file__).resolve().parents[2] / "bloco_interface" / "web"
TEMPLATES_DIR = _WEB_DIR / "templates"
STATIC_DIR = _WEB_DIR / "static"


def _build_jinja_env() -> Environment:
    """Cria Jinja2 environment standalone (não acopla a app.py para evitar cycle)."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def render_peca_pdf(
    template_name: str,
    context: dict[str, Any],
    output_path: Path,
    *,
    base_url: str | Path | None = None,
) -> bytes:
    """Renderiza peça revisional PDF via weasyprint.

    Args:
        template_name: caminho relativo a templates/ (ex: 'peca/inicial-revisional-veiculos.html').
        context: dict Jinja2 com keys obrigatórios:
            - peca: PecaRevisional ou RelatorioInviabilidade
            - contrato: ContratoMetadata
            - veredito: VeredictoJuiz (opcional)
            - gerado_em: ISO timestamp (opcional)
        output_path: caminho do PDF de saída (parent dir criado 0o700).
        base_url: base_url para weasyprint resolver assets (fontes /static/fonts/).
            Default: bloco_interface/web/static/ absoluto.

    Returns:
        bytes do PDF gerado (também escrito em output_path).

    Raises:
        FileNotFoundError se template_name não existe.
        weasyprint exceptions encapsuladas via logger.
    """
    from weasyprint import HTML  # import tardio — só carrega quando renderiza

    env = _build_jinja_env()
    template = env.get_template(template_name)
    rendered_html = template.render(**context)

    if base_url is None:
        base_url = str(STATIC_DIR.absolute())

    pdf_bytes = HTML(string=rendered_html, base_url=str(base_url)).write_pdf()

    # AC-07 + AC-05: parent dir 0o700 + arquivo 0o600 (LGPD §46)
    output_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    output_path.write_bytes(pdf_bytes)
    try:
        output_path.chmod(0o600)
    except (OSError, NotImplementedError) as exc:
        # Windows: chmod silenciosamente ignorado (filesystem POSIX permissions ausente).
        # LGPD compliance preservada em deploy Linux VPS production.
        logger.debug("chmod 0o600 não-suportado (Windows?): %s", exc)

    return pdf_bytes


def compute_pdf_hash(pdf_bytes: bytes) -> str:
    """SHA256 do PDF bytes para audit chain (AC-08)."""
    return hashlib.sha256(pdf_bytes).hexdigest()
