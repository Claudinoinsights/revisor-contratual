"""LGPD L3 — Headers HTTP defense-in-depth (MVP-LEAN-01 Task 8).

Custom Starlette middleware adiciona security headers em todos os responses.
Per ux-spec/PRD §FR-LGPD-MVP-01c + ADR-013 §2.3 camada 3.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# CSP per ux-spec: HTMX requer style 'unsafe-inline' (inline styles em base.html banner Ollama SSE).
# script-src 'self' bloqueia eval/external; frame-ancestors 'none' previne clickjacking.
CSP_VALUE = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "font-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

SECURITY_HEADERS: dict[str, str] = {
    "Content-Security-Policy": CSP_VALUE,
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


class HeadersMiddleware(BaseHTTPMiddleware):
    """Security headers: CSP + X-Frame + X-Content-Type-Options + Referrer + Permissions."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        for key, value in SECURITY_HEADERS.items():
            response.headers[key] = value
        return response
