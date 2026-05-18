"""OCRmyPDF parser — low-memory OCR fallback (ADR-033 D-DEV-S08-008).

Substitui Marker library para PDFs scanned em produção VPS-constrained.
D-OPS-S08-016 confirmou Marker CPU layout inference OOM em VPS 7.8GB RAM.

OCRmyPDF (wrapper Python de Tesseract OCR):
- RAM peak ~600MB (vs Marker 4-6GB)
- Adiciona text layer ao PDF scanned in-place (output born-digital-like)
- Pipeline downstream PyMuPDF (ADR-027 dual-path) reusable integralmente
- LGPD-safe: 100% local processing (Tesseract Apache 2.0)
- Português brasileiro via tesseract-ocr-por language pack (já no Dockerfile)

Trade-offs vs Marker:
- Qualidade OCR: -10-15% em layouts complexos (tabelas exóticas)
- CDC veículo PDFs scanned são tipicamente textuais simples → Tesseract suficiente
- Velocidade: ~3-5x mais rápido (Tesseract C++ otimizado vs PyTorch CPU)

Fallback graceful: se ocrmypdf não instalado → ParserOCRRequired (não silent).
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Callable

from bloco_engine.parsing.marker_parser import ParserOCRRequired
from bloco_engine.parsing.pymupdf_parser import parse_pdf_pymupdf

logger = logging.getLogger(__name__)

ParserFn = Callable[[Path], tuple[str, int]]

# OCRmyPDF defaults — optimizable per workload
OCRMYPDF_LANGUAGE = "por"  # Português via tesseract-ocr-por
OCRMYPDF_OPTIMIZE = 0  # 0=fast, 3=aggressive size reduction (~10x slower)
OCRMYPDF_JOBS = 2  # Match VPS 2 CPUs


def _is_ocrmypdf_available() -> bool:
    try:
        import ocrmypdf  # noqa: F401  # type: ignore[import-not-found]

        return True
    except ImportError:
        return False


def _default_ocrmypdf_parser(pdf_path: Path) -> tuple[str, int]:
    """OCRmyPDF + PyMuPDF re-extract pipeline.

    1. OCRmyPDF adds text layer to scanned PDF (writes to tempfile)
    2. PyMuPDF extracts markdown from now born-digital-like PDF
    3. Returns (markdown, pages_count) — same signature as parse_pdf_marker

    Raises:
        ocrmypdf.exceptions.* if OCR fails (corrupt PDF, unsupported format).
        Pre-flight memory check inherited from marker_parser (psutil 2.5GB threshold).
    """
    import os as _os

    import ocrmypdf  # type: ignore[import-not-found]

    # Pre-flight memory check (defense in depth — D-DEV-S08-008 inherits from CC.42 F-A1)
    try:
        import psutil

        mem = psutil.virtual_memory()
        avail_gb = mem.available / (1024**3)
        allow_low = _os.environ.get("ALLOW_LOW_MEMORY", "").lower() in ("1", "true", "yes")
        if avail_gb < 1.0 and mem.percent > 90 and not allow_low:
            raise RuntimeError(
                f"Memória insuficiente para OCR Tesseract: {avail_gb:.1f}GB disponível "
                f"({mem.percent:.0f}% usado). Mínimo 1.0GB. "
                f"Set ALLOW_LOW_MEMORY=1 para tentar mesmo assim."
            )
        logger.info(
            "OCRmyPDF pre-flight: %.1fGB RAM disponível (%.0f%% usado)",
            avail_gb,
            mem.percent,
        )
    except ImportError:
        logger.warning("psutil não instalado — pulando RAM pre-flight check")

    # OCRmyPDF: scanned PDF → PDF com text layer (tempfile output)
    with tempfile.NamedTemporaryFile(suffix="_ocr.pdf", delete=False) as tmp_out:
        output_path = Path(tmp_out.name)

    try:
        logger.info("OCRmyPDF processing %s → %s", pdf_path.name, output_path.name)
        ocrmypdf.ocr(
            input_file=str(pdf_path),
            output_file=str(output_path),
            language=OCRMYPDF_LANGUAGE,
            optimize=OCRMYPDF_OPTIMIZE,
            jobs=OCRMYPDF_JOBS,
            # Skip pages that already have text (mixed scanned/born-digital PDFs)
            skip_text=True,
            # Don't fail on warnings (some scans are low-res)
            force_ocr=False,
            # Progress bar off (cleaner subprocess stdout — ADR-026 isolation)
            progress_bar=False,
            # Quiet mode (less log noise in subprocess)
            quiet=True,
            # D-DEV-S08-012 fix (D-OPS-S08-026 Eric empirical): output_type="pdf"
            # bypasses Ghostscript redo-ocr path. Debian bookworm ships gs 10.0.0
            # which OCRmyPDF refuses (known regression corrupts PDFs with existing
            # text when skip_text=True). output_type="pdf" uses pikepdf directly.
            output_type="pdf",
        )

        # PyMuPDF extract from now-text-enriched PDF
        markdown, pages_count = parse_pdf_pymupdf(output_path)
        logger.info(
            "OCRmyPDF + PyMuPDF success: %d pages, %d markdown chars",
            pages_count,
            len(markdown),
        )
        return markdown, pages_count
    finally:
        # Cleanup tempfile (LGPD §46 — no residual PII)
        output_path.unlink(missing_ok=True)


def parse_pdf_ocrmypdf(
    pdf_path: Path, parser_fn: ParserFn | None = None
) -> tuple[str, int]:
    """Parse PDF via OCRmyPDF (Tesseract) + PyMuPDF re-extract.

    Args:
        pdf_path: caminho para PDF (tipicamente scanned, sem text layer).
        parser_fn: injetável para testes (default: _default_ocrmypdf_parser).

    Raises:
        ParserOCRRequired se ocrmypdf não instalado (instala via [ocr] extras).
        RuntimeError se memória insuficiente (<1GB available + 90% used).
        ocrmypdf.exceptions.* em caso de OCR failure.

    Returns:
        Tuple[markdown, pages_count] — interface idêntica a parse_pdf_marker.
    """
    if parser_fn is not None:
        return parser_fn(pdf_path)
    if not _is_ocrmypdf_available():
        # F-PIPELINE-LOW-01 hardening: mensagem PT-BR estruturada
        raise ParserOCRRequired(
            f"❌ Não foi possível extrair texto do PDF: {pdf_path.name}\n\n"
            f"📋 Diagnóstico: PDF parece ser imagem escaneada (sem camada de texto).\n"
            f"🔍 Causa: OCR é necessário mas OCRmyPDF não está instalado.\n\n"
            f"✅ Solução: instale o suporte OCR:\n"
            f"   pip install revisor-contratual[ocr]\n\n"
            f"💡 Alternativa: converta para PDF preservando camada de texto antes de enviar."
        )
    return _default_ocrmypdf_parser(pdf_path)
