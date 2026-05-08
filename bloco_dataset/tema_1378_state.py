"""Tema 1378 STJ state file API — MVP-LEAN-01 Task 7.

Implementa state machine FR-MONITOR-01 (per ADR-013 §2.5 dual-layer):
- Camada 1 (auto scrape — Task 8 ownership) chama `increment_fail()` quando falha
- 2 fails consecutivas → auto-trigger CRITICAL (banner vermelho + main desabilitado)
- Maintainer chama `acknowledge()` via POST /monitor-tema/acknowledge OR CLI

State persistido em ~/.local/share/revisor-contratual/tema_1378_status.json (atomic write).
Audit trail em audit.jsonl (tipo `tema_1378_acknowledge` quando ack).

Anti-pattern proibido: write não-atomic (corrupção em crash mid-write violaria invariante).
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ── Paths e defaults ──────────────────────────────────────────────────────
DEFAULT_STATE_DIR = Path.home() / ".local" / "share" / "revisor-contratual"
STATE_FILE = DEFAULT_STATE_DIR / "tema_1378_status.json"

DEFAULT_STATE: dict[str, Any] = {
    "nivel": "verde",
    "mensagem": "✓ Tema 1378 STJ — sem alterações na última verificação automática.",
    "last_check": None,
    "fail_count": 0,
    "julgamento_data": None,
    "tese_fixada": None,
}

# Microcopy per ux-spec §4 C2 linhas 642-646
MICROCOPY: dict[str, str] = {
    "verde": "✓ Tema 1378 STJ — sem alterações na última verificação automática.",
    "amarelo_1_fail": (
        "⏳ Tema 1378 STJ — verificação automática falhou {data}. "
        "Acompanhe manualmente até a próxima execução."
    ),
    "vermelho_2_fails": (
        "⚠ ALERTA CRÍTICO — Tema 1378 STJ. A verificação automática falhou em "
        "2 execuções consecutivas. Execute SOP-005 manual."
    ),
    "amarelo_julgamento": (
        "⚠ Tema 1378 STJ — sessão de julgamento pautada para {data}. "
        "Revise teses citadas após decisão."
    ),
    "vermelho_julgamento": (
        "⚠ ALERTA CRÍTICO — Tema 1378 STJ. Estado: julgamento detectado em {data}. "
        "Tese fixada: {tese}. Novas análises pausadas até atualização do vault."
    ),
}


def _state_file_path() -> Path:
    """Lazy path resolution (suporta override via env REVISOR_DATA_DIR para testes)."""
    custom_dir = os.environ.get("REVISOR_DATA_DIR")
    if custom_dir:
        return Path(custom_dir) / "tema_1378_status.json"
    return STATE_FILE


def get_current() -> dict[str, Any]:
    """Lê state file atual; cria default se ausente OU JSON inválido (fallback robusto)."""
    path = _state_file_path()
    if not path.exists():
        return dict(DEFAULT_STATE)
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        # Sanity check — campos obrigatórios
        for key in ("nivel", "mensagem", "fail_count"):
            if key not in data:
                return dict(DEFAULT_STATE)
        return data
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_STATE)


def set_state(
    nivel: str,
    mensagem: str,
    fail_count: int | None = None,
    julgamento_data: str | None = None,
    tese_fixada: str | None = None,
) -> dict[str, Any]:
    """Atomic write JSON (temp file + os.replace) — não corrompe em crash mid-write."""
    if nivel not in ("verde", "amarelo", "vermelho"):
        raise ValueError(f"nivel inválido: {nivel} (deve ser verde|amarelo|vermelho)")

    current = get_current()
    new_state = {
        "nivel": nivel,
        "mensagem": mensagem,
        "last_check": datetime.now(UTC).isoformat(),
        "fail_count": fail_count if fail_count is not None else current.get("fail_count", 0),
        "julgamento_data": julgamento_data,
        "tese_fixada": tese_fixada,
    }

    path = _state_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: tmpfile + replace (ACID em filesystem POSIX/NTFS)
    fd, tmp_path = tempfile.mkstemp(suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(new_state, tmp, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    return new_state


def increment_fail() -> int:
    """Incrementa fail_count; auto-trigger CRITICAL (vermelho) se ≥ 2 (per ux-spec linha 645).

    Camada 1 scraper (Task 8) chama esta função quando scrape automático falha.
    Returns: novo fail_count.
    """
    current = get_current()
    new_count = current.get("fail_count", 0) + 1
    timestamp = datetime.now(UTC).isoformat()
    fmt_data = timestamp.split("T")[0]  # YYYY-MM-DD curto

    if new_count >= 2:
        # Auto-trigger CRITICAL
        set_state(
            nivel="vermelho",
            mensagem=MICROCOPY["vermelho_2_fails"],
            fail_count=new_count,
        )
    elif new_count == 1:
        set_state(
            nivel="amarelo",
            mensagem=MICROCOPY["amarelo_1_fail"].format(data=fmt_data),
            fail_count=new_count,
        )

    return new_count


def acknowledge(audit_path: Path | None = None) -> dict[str, Any]:
    """Maintainer ack — VERMELHO → AMARELO + grava entry tema_1378_acknowledge em audit.jsonl.

    Per ux-spec linha 603: "banner não-fechável até maintainer ack via CLI --acknowledge".
    Web também aceita ack via POST /monitor-tema/acknowledge (Task 7).
    """
    current = get_current()
    if current.get("nivel") != "vermelho":
        # Idempotente: ack em estado não-vermelho não muda nada
        return current

    # Downgrade VERMELHO → AMARELO (estado intermediário até próxima auto-verificação)
    new_state = set_state(
        nivel="amarelo",
        mensagem=MICROCOPY["amarelo_1_fail"].format(
            data=datetime.now(UTC).isoformat().split("T")[0],
        ),
        fail_count=current.get("fail_count", 0),
    )

    # Audit entry
    if audit_path:
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "type": "tema_1378_acknowledge",
            "timestamp": datetime.now(UTC).isoformat(),
            "previous_nivel": "vermelho",
            "new_nivel": "amarelo",
            "fail_count_at_ack": current.get("fail_count", 0),
        }
        with audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return new_state


def reset_to_verde() -> dict[str, Any]:
    """Reset para verde após auto-verificação successful (Camada 1 OK, Task 8 chama)."""
    return set_state(
        nivel="verde",
        mensagem=MICROCOPY["verde"],
        fail_count=0,
    )
