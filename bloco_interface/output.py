"""Formatação humana — rich opcional + fallback ASCII puro (D-MOR-4.1-B).

`rich` é dep declarada mas detecta runtime: se ausente, fallback ASCII garante
que CLI nunca quebra por falta de lib visual.
"""

from __future__ import annotations

import sys
from typing import Any

from bloco_contratos.personas import VeredictoJuiz

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False


_VEREDITO_ICONS = {
    "APROVADO_100": "✅",
    "APROVADO_COM_RISCO_HITL": "⚠️ ",
    "REJEITADO": "❌",
}


def format_veredito(veredito: VeredictoJuiz, audit_hash: str | None = None) -> str:
    """Formata VeredictoJuiz para CLI (rich se disponível, ASCII fallback)."""
    if _RICH_AVAILABLE:
        return _format_veredito_rich(veredito, audit_hash)
    return _format_veredito_ascii(veredito, audit_hash)


def _format_veredito_ascii(veredito: VeredictoJuiz, audit_hash: str | None) -> str:
    icon = _VEREDITO_ICONS.get(veredito.veredito, "?")
    lines = [
        "",
        f"{icon} Veredito: {veredito.veredito} (aderência: {veredito.aderencia:.1f}%)",
        "",
        "Scores:",
        f"  C1 (divergência BACEN):   {veredito.c1_score:.2f}",
        f"  C2 (peso vinculação):     {veredito.c2_score:.2f}",
        f"  C3 (jurisdição):          {veredito.c3_score:.2f}",
        "",
        "Razões:",
    ]
    for r in veredito.razoes:
        lines.append(f"  • {r}")
    if audit_hash:
        lines.extend(["", f"Audit entry: {audit_hash[:16]}..."])
    return "\n".join(lines)


def _format_veredito_rich(veredito: VeredictoJuiz, audit_hash: str | None) -> str:
    from io import StringIO

    buf = StringIO()
    console = Console(file=buf, force_terminal=False, width=80)

    icon = _VEREDITO_ICONS.get(veredito.veredito, "?")
    title = f"{icon} {veredito.veredito} — aderência {veredito.aderencia:.1f}%"

    table = Table(show_header=True, header_style="bold", title=title, title_style="bold")
    table.add_column("Critério", style="cyan", no_wrap=True)
    table.add_column("Score", justify="right")
    table.add_row("C1 — Divergência BACEN", f"{veredito.c1_score:.2f}")
    table.add_row("C2 — Peso Vinculação", f"{veredito.c2_score:.2f}")
    table.add_row("C3 — Jurisdição", f"{veredito.c3_score:.2f}")
    console.print(table)

    razoes_text = "\n".join(f"• {r}" for r in veredito.razoes)
    console.print(Panel(razoes_text, title="Razões", border_style="dim"))

    if audit_hash:
        console.print(f"\n[dim]Audit entry: {audit_hash[:16]}...[/dim]")

    return buf.getvalue()


def format_info(message: str) -> str:
    """Mensagem informativa (rich panel se disponível, prefixo ℹ️ caso contrário)."""
    return f"ℹ️  {message}"


def format_success(message: str) -> str:
    return f"✅ {message}"


def echo_error(message: str) -> None:
    """Imprime erro para stderr (não polui stdout que pode ser pipeable)."""
    print(message, file=sys.stderr)


def is_rich_available() -> bool:
    """Helper para testes."""
    return _RICH_AVAILABLE
