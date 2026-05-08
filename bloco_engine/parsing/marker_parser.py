"""Marker parser — fallback OCR OPCIONAL (FR-PARSE-01 fallback path).

Marker é dep opt-in (extras_require=["ocr"]). Se não instalado, levanta
ParserOCRRequired EXPLICITAMENTE — nunca silent fallback.

D-MOR-3.2-C: ausência de Marker NÃO degrada graciosamente em "ok parser primário só";
a ausência precisa ser visível para o orchestrator decidir (alertar usuário a instalar
ou aceitar limitação).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

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
    """Implementação real Marker — adaptado CC.34 para API marker-pdf 1.x.

    Breaking change (TD-MARKER-API-BREAKING-CHANGE):
    - marker 0.x: marker.convert.convert_single_pdf + load_all_models
    - marker 1.x: marker.converters.pdf.PdfConverter + create_model_dict

    CC.42 fix F-A1 (Smith CC.41 CRITICAL): RAM pre-flight check protege contra
    OS SIGKILL silencioso. Marker + Surya + LLMs já carregados podem totalizar
    >8GB; em hardware ~16GB com browser/IDE abertos, pressão crítica leva
    OOM kill sem stack trace. Threshold 2.5GB available + 90% used dispara
    erro estruturado em vez de OS kill (override via ALLOW_LOW_MEMORY=1).
    """
    # CC.42 fix F-A1: RAM pre-flight check antes de carregar modelos pesados.
    import os as _os
    try:
        import psutil
        mem = psutil.virtual_memory()
        avail_gb = mem.available / (1024**3)
        allow_low = _os.environ.get("ALLOW_LOW_MEMORY", "").lower() in ("1", "true", "yes")
        if avail_gb < 2.5 and mem.percent > 90 and not allow_low:
            raise RuntimeError(
                f"Memória insuficiente para OCR: {avail_gb:.1f}GB disponível "
                f"({mem.percent:.0f}% usado). Mínimo 2.5GB. Feche aplicações "
                f"OR set ALLOW_LOW_MEMORY=1 para tentar mesmo assim (risco OOM)."
            )
        logger.info(
            "OCR pre-flight: %.1fGB RAM disponível (%.0f%% usado)",
            avail_gb, mem.percent,
        )
    except ImportError:
        logger.warning("psutil não instalado — pulando RAM pre-flight check")

    # Lazy import — só importa se chamada de fato.
    from marker.converters.pdf import PdfConverter  # type: ignore[import-not-found]
    from marker.models import create_model_dict  # type: ignore[import-not-found]

    models = create_model_dict()
    converter = PdfConverter(artifact_dict=models)
    rendered = converter(str(pdf_path))
    full_text = rendered.markdown
    # CC.35 fix TD-PAGES-COUNT-LIST-VS-DICT: marker 1.x retorna page_stats como
    # list[dict] (uma entry por página); CC.34 incorretamente assumiu dict.
    page_stats = rendered.metadata.get("page_stats")
    if isinstance(page_stats, list):
        pages_count = len(page_stats)
    elif isinstance(page_stats, dict):
        pages_count = int(page_stats.get("page_count", 1))
    else:
        pages_count = int(rendered.metadata.get("pages") or 1)
    # CC.40 fix F-10: warn se schema inesperado caiu no fallback silencioso
    if pages_count == 1 and not page_stats and not rendered.metadata.get("pages"):
        logger.warning(
            "marker metadata sem 'page_stats' nem 'pages' — schema possivelmente "
            "desconhecido. pages_count=1 fallback. Metadata keys: %s",
            list(rendered.metadata.keys()) if rendered.metadata else "empty",
        )
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
