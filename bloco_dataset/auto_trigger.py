"""Auto-trigger Camada 1 — MVP-LEAN-01 Task 8b.

Cola APScheduler (cron daily) ↔ tema_1378_state (Task 7 state machine).

Lógica:
- Try scrape_tema_1378():
    - Sucesso → reset_to_verde() (nivel=verde) OU set_state com nivel detectado
    - Failure (qualquer exception) → increment_fail() (Task 7 cuida do auto-CRITICAL
      em fail_count >= 2)
- Audit entry tipo ``tema_1378_auto_check`` em audit.jsonl (append-only).

Anti-pattern proibido: NUNCA propagar exception — é APScheduler job; falha silenciosa
do job seria perda de visibilidade total. Por isso, capturamos tudo + audit + log.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bloco_dataset import tema_1378_state
from bloco_dataset.scraper_tema_1378 import (
    DEFAULT_STJ_URL,
    ScraperError,
    scrape_tema_1378,
)

logger = logging.getLogger(__name__)

DEFAULT_AUDIT_PATH = Path.home() / ".local" / "share" / "revisor-contratual" / "audit.jsonl"


def _audit_path() -> Path:
    """Resolve audit path (env override REVISOR_DATA_DIR para testes)."""
    custom = os.environ.get("REVISOR_DATA_DIR")
    if custom:
        return Path(custom) / "audit.jsonl"
    return DEFAULT_AUDIT_PATH


def _write_audit(audit_path: Path, entry: dict[str, Any]) -> None:
    """Append audit entry; loga erro mas NÃO propaga (auto-trigger é job background)."""
    try:
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        with audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.error("auto_trigger: falha gravando audit em %s: %s", audit_path, exc)


def run_camada_1_check(
    audit_path: Path | None = None,
    url: str = DEFAULT_STJ_URL,
) -> dict[str, Any]:
    """Executa scrape Camada 1 + atualiza state Task 7. Retorna audit entry gerado.

    Robusto: NUNCA propaga exception. Em caso de erro, increment_fail() é chamado.

    F-08 invariant (Smith CC.25): se estado atual é vermelho-via-fails-consecutivas
    (≥2), fail_count é preservado mesmo quando scraper detecta julgamento real (amarelo
    ou vermelho via parser). Maintainer DEVE chamar acknowledge() (Task 7 SOP-005)
    para downgrade explícito de vermelho-via-fails. Isso preserva a invariante de que
    "vermelho-via-fails requer ack manual" — auto-downgrade silencioso é proibido.
    """
    target_audit = audit_path if audit_path is not None else _audit_path()
    timestamp = datetime.now(UTC).isoformat()

    try:
        result = scrape_tema_1378(url=url)
        if result["nivel"] == "verde":
            tema_1378_state.reset_to_verde()
        else:
            # F-08 fix: preservar fail_count se vermelho-via-fails (≥2) — invariante SOP-005
            current = tema_1378_state.get_current()
            preserve_fail_count = (
                current.get("nivel") == "vermelho"
                and current.get("fail_count", 0) >= 2
            )
            tema_1378_state.set_state(
                nivel=result["nivel"],
                mensagem=result["mensagem"],
                fail_count=current.get("fail_count", 0) if preserve_fail_count else 0,
                julgamento_data=result.get("julgamento_data"),
                tese_fixada=result.get("tese_fixada"),
            )
        entry = {
            "type": "tema_1378_auto_check",
            "timestamp": timestamp,
            "status": "success",
            "nivel_detectado": result["nivel"],
            "url": url,
        }
        logger.info("run_camada_1_check: success nivel=%s", result["nivel"])
    except ScraperError as exc:
        new_count = tema_1378_state.increment_fail()
        entry = {
            "type": "tema_1378_auto_check",
            "timestamp": timestamp,
            "status": "fail_scraper",
            "fail_count": new_count,
            "error": str(exc),
            "url": url,
        }
        logger.warning(
            "run_camada_1_check: ScraperError fail_count=%d: %s",
            new_count,
            exc,
        )
    except Exception as exc:  # noqa: BLE001 — auto-trigger job: capturar tudo
        new_count = tema_1378_state.increment_fail()
        entry = {
            "type": "tema_1378_auto_check",
            "timestamp": timestamp,
            "status": "fail_unexpected",
            "fail_count": new_count,
            "error": f"{type(exc).__name__}: {exc}",
            "url": url,
        }
        logger.error(
            "run_camada_1_check: unexpected %s fail_count=%d",
            type(exc).__name__,
            new_count,
        )

    _write_audit(target_audit, entry)
    return entry
