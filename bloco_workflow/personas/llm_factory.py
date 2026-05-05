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

from typing import Any

from bloco_contratos.personas import LLMTier

# Portas distintas obrigatórias para paralelismo real (F-MIN-01)
DEFAULT_HOST_ADVOGADO = "http://127.0.0.1:11434"
DEFAULT_HOST_ECONOMISTA = "http://127.0.0.1:11435"

# Mapping tier → modelo Sabia (configurável)
TIER_TO_MODEL_ADVOGADO: dict[LLMTier, str] = {
    "lean": "sabia-3b",
    "balanced": "sabia-7b",
    "premium": "sabia-7b-instruct",
}

# Economista FIXO (ADR-003 PATCH SUB-C)
MODEL_ECONOMISTA = "qwen2.5:3b"


def get_advogado_llm(
    *,
    tier: LLMTier = "premium",
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
    )
