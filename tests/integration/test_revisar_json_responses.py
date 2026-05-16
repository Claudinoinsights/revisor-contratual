"""Integration tests for JSON validation responses — Sprint 8 Phase B Story #12.

Smith F-HIGH-07 ultrathink: POST /revisar com bad PDF retorna 400 + HTML page (5574 bytes)
em vez JSON. API consumers (curl, Python clients) can't parse HTML response.

Fix: _wants_json_response(request) helper checks Accept: application/json header OR /api/* path.
http_exception_handler + global_exception_handler return JSONResponse quando API client.
Browser users (Accept: text/html default) → HTML preserved (UX).

Refs:
- Smith ultrathink F-HIGH-07
- handoff-devops-to-dev-2026-05-16-sprint-8-phase-b-neo-batch-12-13-14.yaml
"""

from __future__ import annotations

from unittest.mock import MagicMock


def test_wants_json_response_accept_header_application_json():
    """AC-1: Accept: application/json header → True."""
    from bloco_interface.web.app import _wants_json_response
    request = MagicMock()
    request.headers = {"accept": "application/json"}
    request.url.path = "/revisar"
    assert _wants_json_response(request) is True


def test_wants_json_response_accept_header_mixed():
    """AC-1: Accept: application/json, text/html → True (json em qualquer parte)."""
    from bloco_interface.web.app import _wants_json_response
    request = MagicMock()
    request.headers = {"accept": "text/html, application/json"}
    request.url.path = "/revisar"
    assert _wants_json_response(request) is True


def test_wants_json_response_api_path():
    """AC-1: /api/* path → True (sem Accept header)."""
    from bloco_interface.web.app import _wants_json_response
    request = MagicMock()
    request.headers = {}
    request.url.path = "/api/analytics/health"
    assert _wants_json_response(request) is True


def test_wants_json_response_browser_default():
    """AC-3: browser default (Accept: text/html) → False (HTML preserved)."""
    from bloco_interface.web.app import _wants_json_response
    request = MagicMock()
    request.headers = {"accept": "text/html, application/xhtml+xml"}
    request.url.path = "/revisar"
    assert _wants_json_response(request) is False


def test_wants_json_response_no_accept_header():
    """AC-3: missing Accept header + non-API path → False (default HTML)."""
    from bloco_interface.web.app import _wants_json_response
    request = MagicMock()
    request.headers = {}
    request.url.path = "/revisar"
    assert _wants_json_response(request) is False
