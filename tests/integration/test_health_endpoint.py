"""Integration tests for /health endpoint + HEAD / method — Sprint 8 Phase B Story #13.

Smith F-HIGH-04 ultrathink: /health, /api/health, /healthz all 404 (no dedicated endpoint).
Smith F-HIGH-05 ultrathink: HEAD / returns 405 Method Not Allowed (Uptime-Kuma + load balancer unfriendly).

Fix: @app.get('/health') returns JSON system health snapshot (no auth).
Fix: @app.head('/') returns 200 OK headers only (mirror GET).

Refs:
- Smith ultrathink F-HIGH-04 + F-HIGH-05
- handoff-devops-to-dev-2026-05-16-sprint-8-phase-b-neo-batch-12-13-14.yaml
"""

from __future__ import annotations


def test_health_endpoint_route_registered():
    """AC-1: /health endpoint registrado em FastAPI app."""
    from bloco_interface.web.app import app
    paths_methods = [
        (getattr(r, "path", None), sorted(getattr(r, "methods", []) or []))
        for r in app.routes
        if hasattr(r, "methods")
    ]
    assert ("/health", ["GET"]) in paths_methods, "GET /health route MUST be registered"


def test_head_root_route_registered():
    """AC-2: HEAD / endpoint registrado em FastAPI app."""
    from bloco_interface.web.app import app
    paths_methods = [
        (getattr(r, "path", None), sorted(getattr(r, "methods", []) or []))
        for r in app.routes
        if hasattr(r, "methods")
    ]
    assert ("/", ["HEAD"]) in paths_methods, "HEAD / route MUST be registered (Smith F-HIGH-05)"


def test_health_endpoint_callable():
    """AC-1: health_endpoint function callable."""
    from bloco_interface.web.app import health_endpoint
    assert callable(health_endpoint), "health_endpoint MUST be callable"


def test_head_root_callable():
    """AC-2: head_root function callable."""
    from bloco_interface.web.app import head_root
    assert callable(head_root), "head_root MUST be callable"


def test_get_root_still_registered_post_head_addition():
    """AC-2: HEAD / addition NÃO removeu GET / (mirror behavior preserved)."""
    from bloco_interface.web.app import app
    paths_methods = [
        (getattr(r, "path", None), sorted(getattr(r, "methods", []) or []))
        for r in app.routes
        if hasattr(r, "methods")
    ]
    assert ("/", ["GET"]) in paths_methods, "GET / route MUST be preserved after HEAD addition"
