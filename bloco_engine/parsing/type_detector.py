"""PDF type detection — Sprint 7 Phase 4 (ADR-027).

Detects born-digital vs scanned PDFs via PyMuPDF (fitz) text extraction heuristic.
Used by pipeline.py Step 1 to decide between PyMuPDF inline (born-digital ~10s) vs
subprocess marker fallback (scanned ~120s, Phase 3 ADR-026 preserved).

Refs:
- ADR-027 governance/architecture/adr/adr-027-pymupdf-born-digital-fast-path.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import fitz  # PyMuPDF — already installed via marker-pdf dependency


# Empirical threshold: chars per page below which considered scanned.
# Born-digital CDC veículo PDFs typically extract 1500-3000 chars/page.
# Scanned PDFs return 0 chars (no text layer) OR <100 chars (sparse fallback text).
DEFAULT_TEXT_THRESHOLD_PER_PAGE = 500

PdfType = Literal["born_digital", "scanned"]


def detect_pdf_type(
    pdf_path: Path,
    sample_pages: int = 2,
    text_threshold_per_page: int = DEFAULT_TEXT_THRESHOLD_PER_PAGE,
) -> PdfType:
    """Detect PDF type via PyMuPDF text extraction heuristic.

    Args:
        pdf_path: Path to PDF file.
        sample_pages: Number of first pages to sample (default 2).
        text_threshold_per_page: Min chars per page para born-digital (default 500).

    Returns:
        "born_digital" if avg text per sampled page >= threshold.
        "scanned" otherwise (also returned for empty/unreadable PDFs).

    Performance: <50ms typical (PyMuPDF lightweight read sem OCR).

    Edge cases:
    - Empty PDF (0 pages) → "scanned"
    - Single page PDF → samples only that page
    - Mixed PDFs (some born-digital + some scanned pages) → majority via threshold
    - Corrupt PDF → "scanned" (fitz raises, caught here OR upstream)
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        # Corrupt/unreadable PDF — defer to subprocess marker fallback (scanned path)
        return "scanned"

    try:
        pages_to_sample = min(sample_pages, doc.page_count)
        if pages_to_sample == 0:
            return "scanned"

        total_chars = 0
        for page_num in range(pages_to_sample):
            page = doc[page_num]
            text = page.get_text() or ""
            total_chars += len(text)

        avg_chars_per_page = total_chars / pages_to_sample
        return "born_digital" if avg_chars_per_page >= text_threshold_per_page else "scanned"
    finally:
        doc.close()
