# ════════════════════════════════════════════════════════════════════════════
# Revisor Contratual — Dockerfile (Sprint 6.x Caminho B Docker/Linux deploy)
#
# Resolve Smith F-CRIT-01: WeasyPrint missing libgobject-2.0-0 no Windows.
# Linux container tem GTK + Pango + Cairo nativamente via apt.
#
# Build:    docker build -t revisor-contratual:latest .
# Run:      docker compose -f docker-compose.app.yml up -d
# ════════════════════════════════════════════════════════════════════════════

FROM python:3.13-slim-bookworm

# Native deps: WeasyPrint (GTK+ Pango Cairo) + OCR (tesseract poppler) + build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint Linux native deps
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    # OCR deps (Marker + pdf2image + tesseract português)
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    # HTTP healthcheck
    curl \
    # Build deps (compile native wheels)
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pyproject + install deps first (layer cache friendly)
COPY pyproject.toml README.md ./
COPY bloco_audit/ ./bloco_audit/
COPY bloco_auth/ ./bloco_auth/
COPY bloco_backup/ ./bloco_backup/
COPY bloco_contratos/ ./bloco_contratos/
COPY bloco_dataset/ ./bloco_dataset/
COPY bloco_engine/ ./bloco_engine/
COPY bloco_interface/ ./bloco_interface/
COPY bloco_learning/ ./bloco_learning/
COPY bloco_lgpd/ ./bloco_lgpd/
COPY bloco_vault/ ./bloco_vault/
COPY bloco_workflow/ ./bloco_workflow/

RUN pip install --no-cache-dir -e ".[dev,ocr]"

# Copy remaining project files
COPY scripts/ ./scripts/

# Non-root user (LGPD §46 — chmod sensível garantido por uid não-root)
RUN useradd -m -u 1000 revisor && \
    mkdir -p /home/revisor/.local/share/revisor-contratual && \
    chown -R revisor:revisor /app /home/revisor

# F-PROD-NEW-21 Option D fix (Smith D-SMITH-S06-038 root cause):
# surya-ocr (dep marker-pdf 1.10.2) settings.py:31 tenta mkdir/write em
# /usr/local/lib/python3.13/site-packages/static/fonts mas dir não existe
# e container roda como user revisor (non-root). Pre-create + chown resolve.
RUN mkdir -p /usr/local/lib/python3.13/site-packages/static/fonts && \
    chown -R revisor:revisor /usr/local/lib/python3.13/site-packages/static

USER revisor

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8501/ || exit 1

# Docker bind 0.0.0.0 (não 127.0.0.1 hardcoded em app.py:1459)
# Operator workaround Sprint 6.x — uvicorn CLI direto aceita --host override.
# TD-UVICORN-DOCKER-HOST (Sprint 6.3+ Neo refator app.py run() lê UVICORN_HOST env var).
CMD ["uvicorn", "bloco_interface.web.app:app", "--host", "0.0.0.0", "--port", "8501"]
