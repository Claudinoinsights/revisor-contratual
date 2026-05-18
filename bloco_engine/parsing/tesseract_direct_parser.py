"""Tesseract Direct parser — pdf2image + pytesseract sem dependência Ghostscript (ADR-034).

D-DEV-S08-013 (D-OPS-S08-028 fix definitivo): elimina OCRmyPDF + Ghostscript
da pipeline. ULTRATHINK analysis revelou OCRmyPDF depende fundamentalmente de
Ghostscript em múltiplos paths internos (image rendering, PDF validation,
color space management). Cada workaround (D-DEV-S08-012 output_type='pdf')
adiava o problema para próximo path.

Solução DEFINITIVA: pipeline direto sem wrappers:

  PDF → pdf2image (poppler-utils) → PIL Images → pytesseract → markdown

Vantagens vs OCRmyPDF:
- 0 dependência Ghostscript (Debian bookworm 10.0.0 regressão irrelevante)
- 2 ferramentas vs 5 — menos failure surfaces
- poppler-utils + tesseract-ocr-por JÁ no Dockerfile
- Tesseract português mantém qualidade
- Memory similar (~500-800MB)
- Não construímos PDF saída (só markdown — é o que pipeline precisa)

Trade-offs aceitos:
- Tabelas complexas: -10% qualidade vs OCRmyPDF (CDC veículo é textual simples)
- Sem output PDF (apenas markdown extraído — suficiente para pipeline downstream)

Inherits patterns:
- ADR-026 subprocess isolation (executa em subprocess_runner)
- D-DEV-S08-005 stdout silence (pytesseract retorna direto, não imprime)
- Pre-flight memory check (CC.42 F-A1 pattern de marker_parser.py)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from bloco_engine.parsing.marker_parser import ParserOCRRequired

logger = logging.getLogger(__name__)

ParserFn = Callable[[Path], tuple[str, int]]

# Tesseract configuration — sweet spots para texto jurídico CDC veículo
TESSERACT_LANGUAGE = "por"  # Português brasileiro via tesseract-ocr-por
TESSERACT_DPI = 100  # D-DEV-S08-014: 100dpi (era 150) — ~2x mais rápido CPU, qualidade OCR ainda aceitável CDC
TESSERACT_PSM = 3  # Page Segmentation Mode 3 = auto (default, robusto)


def _is_tesseract_direct_available() -> bool:
    """Verifica se pdf2image + pytesseract estão importáveis."""
    try:
        import pdf2image  # noqa: F401  # type: ignore[import-not-found]
        import pytesseract  # noqa: F401  # type: ignore[import-not-found]

        return True
    except ImportError:
        return False


def _default_tesseract_direct_parser(pdf_path: Path) -> tuple[str, int]:
    """Pipeline OCR direto: pdf2image + pytesseract.

    1. pdf2image renderiza cada page do PDF para PIL Image (poppler-utils, sem Ghostscript)
    2. pytesseract aplica OCR em cada image (lang=por)
    3. Concatena texto de todas pages em markdown único

    Raises:
        RuntimeError se memória insuficiente (pre-flight check).
        pdf2image.exceptions.* se PDF corrupt/unsupported.
        pytesseract.TesseractNotFoundError se tesseract binary missing.

    Returns:
        Tuple[markdown_text, pages_count] — mesma assinatura que parse_pdf_marker.
    """
    import os as _os

    from pdf2image import convert_from_path  # type: ignore[import-not-found]
    import pytesseract  # type: ignore[import-not-found]

    # Pre-flight memory check (D-DEV-S08-013 inherits CC.42 F-A1 pattern)
    try:
        import psutil

        mem = psutil.virtual_memory()
        avail_gb = mem.available / (1024**3)
        allow_low = _os.environ.get("ALLOW_LOW_MEMORY", "").lower() in ("1", "true", "yes")
        if avail_gb < 1.0 and mem.percent > 90 and not allow_low:
            raise RuntimeError(
                f"Memória insuficiente para OCR Tesseract direto: {avail_gb:.1f}GB disponível "
                f"({mem.percent:.0f}% usado). Mínimo 1.0GB. "
                f"Set ALLOW_LOW_MEMORY=1 para tentar mesmo assim."
            )
        logger.info(
            "Tesseract direct pre-flight: %.1fGB RAM disponível (%.0f%% usado)",
            avail_gb,
            mem.percent,
        )
    except ImportError:
        logger.warning("psutil não instalado — pulando RAM pre-flight check")

    # 1. PDF → PIL Images via poppler-utils (ZERO Ghostscript dependency)
    logger.info("Tesseract direct: rendering %s pages via pdf2image (poppler)", pdf_path.name)
    try:
        images = convert_from_path(
            pdf_path,
            dpi=TESSERACT_DPI,
            fmt="png",
        )
    except Exception as exc:
        logger.error("pdf2image falhou: %s", exc)
        raise

    pages_count = len(images)
    if pages_count == 0:
        raise RuntimeError(f"PDF sem pages renderizáveis: {pdf_path.name}")

    logger.info("Tesseract direct: %d pages renderizadas, iniciando OCR", pages_count)

    # 2. Tesseract OCR cada page (lang português brasileiro)
    pages_text: list[str] = []
    for i, img in enumerate(images, start=1):
        try:
            text = pytesseract.image_to_string(
                img,
                lang=TESSERACT_LANGUAGE,
                config=f"--psm {TESSERACT_PSM}",
            )
            pages_text.append(text.strip())
            logger.debug(
                "Tesseract page %d/%d: %d chars extracted", i, pages_count, len(text)
            )
        except Exception as exc:
            logger.warning("Tesseract OCR falhou em page %d/%d: %s", i, pages_count, exc)
            pages_text.append(f"[OCR FAILED page {i}: {exc}]")

    # 3. Concatenate pages com separator markdown
    markdown = "\n\n---\n\n".join(pages_text)
    logger.info(
        "Tesseract direct success: %d pages, %d total markdown chars",
        pages_count,
        len(markdown),
    )
    return markdown, pages_count


def parse_pdf_tesseract_direct(
    pdf_path: Path, parser_fn: ParserFn | None = None
) -> tuple[str, int]:
    """Parse PDF via Tesseract direct (pdf2image + pytesseract).

    Substitui parse_pdf_ocrmypdf — elimina dependência Ghostscript que
    bloqueava pipeline em Debian bookworm (gs 10.0.0 regression).

    Args:
        pdf_path: PDF scanned (sem text layer).
        parser_fn: injetável para testes (default: _default_tesseract_direct_parser).

    Raises:
        ParserOCRRequired se pdf2image OU pytesseract não instalados.
        RuntimeError se memória insuficiente.
        pdf2image/pytesseract exceptions em falhas runtime.

    Returns:
        Tuple[markdown, pages_count] — interface idêntica a parse_pdf_marker.
    """
    if parser_fn is not None:
        return parser_fn(pdf_path)
    if not _is_tesseract_direct_available():
        raise ParserOCRRequired(
            f"❌ Não foi possível extrair texto do PDF: {pdf_path.name}\n\n"
            f"📋 Diagnóstico: PDF parece ser imagem escaneada (sem camada de texto).\n"
            f"🔍 Causa: OCR é necessário mas pdf2image OU pytesseract não estão instalados.\n\n"
            f"✅ Solução: instale o suporte OCR:\n"
            f"   pip install revisor-contratual[ocr]\n\n"
            f"💡 Alternativa: converta para PDF preservando camada de texto antes de enviar."
        )
    return _default_tesseract_direct_parser(pdf_path)
