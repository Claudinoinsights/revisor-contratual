"""LLM factory — ChatOllama clients para Advogado (Sabia) + Economista (Qwen).

Decisões arquiteturais (ADR-003 PATCH 2 + D-MOR-3.3-A..D):
  - 2 instâncias Ollama em PORTAS DISTINTAS (paralelismo real, não placebo)
  - F-MIN-01 fix: base_url EXPLÍCITO (não confia no env OLLAMA_HOST default)
  - Sabia = Advogado (tier configurável: lean/balanced/premium)
  - Qwen 2.5 3B = Economista (FIXO — mitigação Tema 1378 STJ; baixo custo + determinístico)
  - F-MIN-02 RESOLVIDO empiricamente: langchain-ollama 1.x ChatOllama.ainvoke é coroutine
    real (asyncio.iscoroutinefunction=True); subjacente ollama.AsyncClient.chat também.

Uso:
    advogado_llm = get_advogado_llm(tier="premium")
    economista_llm = get_economista_llm()

NFR-LGPD-01: ambos rodam local (127.0.0.1) — nenhuma comunicação fora localhost.
"""

from __future__ import annotations

import os
from typing import Any

from bloco_contratos.personas import LLMTier


def _resolve_ollama_host(env_var: str, default: str) -> str:
    """Resolve OLLAMA host env var com fallback default.

    F-PROD-NEW-16 fix (Smith D-SMITH-S06-015 + D-DEV-S06-016 smoke E2E):
    em Docker, 127.0.0.1 = próprio container app (não Ollama hosts).
    Containers Ollama são reachable via service names da docker-compose network
    (ex: ollama-advogado:11434, ollama-economista:11434).

    Lê env var (configurada em docker-compose.prod.yml) com fallback localhost
    para dev local. Adiciona prefix http:// se ausente.
    """
    host = os.environ.get(env_var, default)
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"
    return host


# Portas distintas obrigatórias para paralelismo real (F-MIN-01)
# F-PROD-NEW-16 fix: respeitar OLLAMA_HOST_* env vars (Docker production)
DEFAULT_HOST_ADVOGADO = _resolve_ollama_host("OLLAMA_HOST_ADVOGADO", "127.0.0.1:11434")
DEFAULT_HOST_ECONOMISTA = _resolve_ollama_host("OLLAMA_HOST_ECONOMISTA", "127.0.0.1:11435")

# Mapping tier → modelo Advogado (ADR-010 Path C: Qwen 2.5 default em CPU; Sabia opt-in para GPU)
TIER_TO_MODEL_ADVOGADO: dict[LLMTier, str] = {
    "lean": "qwen2.5:3b",                # consistência família com economista
    "balanced": "qwen2.5:7b",            # NOVO DEFAULT (ADR-010 mitigation)
    "premium": "sabia-7b-instruct",      # preservado opt-in (futuro upgrade GPU)
}

# Economista FIXO (ADR-003 PATCH SUB-C)
MODEL_ECONOMISTA = "qwen2.5:3b"


def get_advogado_llm(
    *,
    tier: LLMTier = "balanced",
    host: str = DEFAULT_HOST_ADVOGADO,
    temperature: float = 0.2,
    timeout_seconds: float = 120.0,
) -> Any:
    """Cria ChatOllama para Advogado.

    Args:
        tier: lean/balanced/premium (FR-TESE-02 configurável).
        host: base_url EXPLÍCITO (F-MIN-01 — nunca confiar em env default).
        temperature: 0.2 default (criativo o suficiente para tese, conservador para citação).
        timeout_seconds: cap para evitar wait infinito.

    Returns:
        ChatOllama configurado.
    """
    from langchain_ollama import ChatOllama  # type: ignore[import-not-found]

    model = TIER_TO_MODEL_ADVOGADO[tier]
    return ChatOllama(
        model=model,
        base_url=host,
        temperature=temperature,
        timeout=timeout_seconds,
        format="json",  # FR-TESE-01: força output JSON estruturado (Pydantic-friendly)
    )


def get_economista_llm(
    *,
    host: str = DEFAULT_HOST_ECONOMISTA,
    temperature: float = 0.0,
    timeout_seconds: float = 60.0,
) -> Any:
    """Cria ChatOllama para Economista (Qwen 2.5 3B FIXO).

    Args:
        host: base_url EXPLÍCITO (porta DISTINTA do Advogado — F-MIN-01).
        temperature: 0.0 default (determinístico para análise macro reproduzível).
        timeout_seconds: cap mais agressivo (Qwen 3B é rápido).

    Returns:
        ChatOllama configurado.
    """
    from langchain_ollama import ChatOllama  # type: ignore[import-not-found]

    return ChatOllama(
        model=MODEL_ECONOMISTA,
        base_url=host,
        temperature=temperature,
        timeout=timeout_seconds,
        format="json",  # ADR-010: defensive consistency com get_advogado_llm
    )
