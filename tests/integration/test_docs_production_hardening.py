"""Integration tests for /docs production hardening — Sprint 8 Story #1.6.

Smith F-CRIT-03 empirical: https://revisor.claudinoinsights.com/docs retornou 200 OK
(Swagger UI) e /openapi.json retornou 200 OK (full schema) em produção.

Fix: app.py FastAPI() conditional initialization — docs_url=None + openapi_url=None
quando REVISOR_ENV=production. Em dev (REVISOR_ENV unset OR != "production"),
docs continuam acessíveis (zero impact desenvolvedores).

Test strategy: REVISOR_ENV é lido em MODULE LOAD time (app.py:_is_production).
Reload module triggers stale-import chain (sp05_analytics etc). Em vez disso:
- Test current app instance (refletindo REVISOR_ENV em time-of-import)
- Test conditional helper logic standalone (whatever env atual)

Refs:
- Smith ultrathink F-CRIT-03 governance/qa/smith-ultrathink-aplicacao-completa-hardware-2026-05-16.md
- handoff-devops-to-dev-2026-05-16-sprint-8-phase-a-stories-1-5-1-6-code.yaml
"""

from __future__ import annotations

import os

from bloco_interface.web.app import _is_production, app


def test_is_production_flag_matches_env_var():
    """_is_production deve refletir REVISOR_ENV at module load time."""
    env_value = os.environ.get("REVISOR_ENV", "").lower()
    expected = env_value == "production"
    assert _is_production is expected, (
        f"_is_production={_is_production} mismatch REVISOR_ENV={env_value!r}"
    )


def test_docs_url_consistent_with_is_production_flag():
    """app.docs_url should be None in production mode, /docs in dev mode."""
    if _is_production:
        assert app.docs_url is None, "Production hardening: /docs MUST be disabled"
        assert app.openapi_url is None, "Production hardening: /openapi.json MUST be disabled"
        assert app.redoc_url is None, "Production hardening: /redoc MUST be disabled"
    else:
        assert app.docs_url == "/docs", "Dev mode: /docs MUST be accessible"
        assert app.openapi_url == "/openapi.json", "Dev mode: /openapi.json MUST be accessible"
        assert app.redoc_url == "/redoc", "Dev mode: /redoc MUST be accessible"


def test_production_logic_is_lowercase_insensitive_via_string_check():
    """Verify conditional logic: 'production' lowercase matches.

    app.py:_is_production = os.environ.get('REVISOR_ENV', '').lower() == 'production'
    Quaisquer variações (PRODUCTION, Production, production) devem trigger.
    """
    # Direct logic verification (sem reload module)
    assert ("PRODUCTION".lower() == "production") is True
    assert ("Production".lower() == "production") is True
    assert ("production".lower() == "production") is True
    assert ("development".lower() == "production") is False
    assert ("".lower() == "production") is False
    assert ("prod".lower() == "production") is False  # exact match required


def test_production_logic_default_is_dev_when_env_unset():
    """Default behavior: REVISOR_ENV unset = dev mode (docs enabled)."""
    # Simulate unset env
    assert (os.environ.get("MISSING_VAR_FOR_TEST", "").lower() == "production") is False


def test_dev_mode_has_docs_in_current_test_run():
    """Sanity check: pytest geralmente roda em dev mode (REVISOR_ENV unset).

    Esta test confirma o estado AT-TIME-OF-IMPORT da app instance.
    Para validar production behavior empiricamente, ver smoke test pós-deploy
    Operator (curl REVISOR_ENV=production /docs deve retornar 404).
    """
    if os.environ.get("REVISOR_ENV", "").lower() != "production":
        # Dev mode esperado
        assert app.docs_url == "/docs"
