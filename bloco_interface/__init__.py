"""bloco_interface — CLI Click entry point + output formatting + error handler.

STORY 10 ✅ — `revisor` comando exposto via pyproject scripts entry-point.
"""

from bloco_interface.error_handler import safe_run, translate_exception
from bloco_interface.output import (
    echo_error,
    format_info,
    format_success,
    format_veredito,
)

__all__ = [
    "safe_run",
    "translate_exception",
    "format_veredito",
    "format_info",
    "format_success",
    "echo_error",
]
