"""Marker parser — fallback OCR OPCIONAL (FR-PARSE-01 fallback path).

Marker é dep opt-in (extras_require=["ocr"]). Se não instalado, levanta
ParserOCRRequired EXPLICITAMENTE — nunca silent fallback.

D-MOR-3.2-C: ausência de Marker NÃO degrada graciosamente em "ok parser primário só";
a ausência precisa ser visível para o orchestrator decidir (alertar usuário a instalar
ou aceitar limitação).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from bloco_engine.parsing.pymupdf_parser import ParserError

ParserFn = Callable[[Path], tuple[str, int]]


class ParserOCRRequired(ParserError):
    """PyMuPDF não conseguiu extrair texto (PDF imagem-only) e Marker não está instalado."""


def _is_marker_available() -> bool:
    try:
        import marker  # noqa: F401  # type: ignore[import-not-found]
        return True
    except ImportError:
        return False


def _default_marker_parser(pdf_path: Path) -> tuple[str, int]:
    """Implementação real Marker (só chamada se Marker instalado)."""
    # Lazy import — só importa se chamada de fato.
    from marker.convert import convert_single_pdf  # type: ignore[import-not-found]
    from marker.models import load_all_models  # type: ignore[import-not-found]

    models = load_all_models()
    full_text, _images, out_meta = convert_single_pdf(str(pdf_path), models)
    pages_count = int(out_meta.get("pages", 1))
    return full_text, pages_count


def parse_pdf_marker(pdf_path: Path, parser_fn: ParserFn | None = None) -> tuple[str, int]:
    """Parse PDF via OCR Marker.

    Se parser_fn=None E Marker não instalado → levanta ParserOCRRequired.
    """
    if parser_fn is not None:
        return parser_fn(pdf_path)
    if not _is_marker_available():
        # F-PIPELINE-LOW-01 hardening: mensagem PT-BR estruturada (diagnóstico → causa → solução → alternativa)
        raise ParserOCRRequired(
            f"❌ Não foi possível extrair texto do PDF: {pdf_path.name}\n\n"
            f"📋 Diagnóstico: PDF parece ser imagem escaneada (sem camada de texto extraível).\n"
            f"🔍 Causa: parser primário (PyMuPDF) retornou conteúdo insuficiente; "
            f"OCR é necessário mas Marker não está instalado.\n\n"
            f"✅ Solução: instale o suporte OCR:\n"
            f"   pip install revisor-contratual[ocr]\n\n"
            f"💡 Alternativa: se você tem o contrato em formato texto/Word, "
            f"converta para PDF preservando a camada de texto antes de enviar."
        )
    return _default_marker_parser(pdf_path)
