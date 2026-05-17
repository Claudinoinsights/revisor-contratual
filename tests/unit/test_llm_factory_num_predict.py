"""Unit tests for llm_factory num_predict configuration — D-DEV-S08-010 (D-OPS-S08-020 fix).

Tests verify get_advogado_llm + get_economista_llm pass num_predict to ChatOllama
preventing Ollama default (128 tokens) truncation of LLM output.

Background:
- D-OPS-S08-020 (2026-05-17): Operator empirical E2E test (audit chain 019453af...)
  revealed PecaRevisional output TRUNCATED mid-word (dos_fatos="Em 15 de maio...mento",
  disclaimer="Insumo técnico-jurídic...nstituição") despite D-DEV-S08-009 prompt
  strengthening + D-DEV-S08-007 advogado prompt fix.
- Root cause: llm_factory.py had ZERO num_predict config — Ollama default=128 tokens
  insufficient for PecaRevisional 8 fields ~1500 tokens output.
- Fix: configure num_predict=2048 + num_ctx=4096 in both factory functions.

Refs:
- D-OPS-S08-020 governance/CHECKPOINT-active.md (root cause real)
- D-DEV-S08-010 governance/CHECKPOINT-active.md (this fix)
- D-DEV-S08-007 (advogado prompt — necessary but insufficient alone)
- D-DEV-S08-009 (redator prompt — necessary but insufficient alone)
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]


# ─────────────────────────────────────────────────────────────────────
# Source-code review tests
# ─────────────────────────────────────────────────────────────────────


def test_llm_factory_imports_correctly():
    """D-DEV-S08-010: llm_factory.py source contains num_predict config."""
    from bloco_workflow.personas import llm_factory

    source = Path(llm_factory.__file__).read_text(encoding="utf-8")
    assert "num_predict" in source, (
        "llm_factory.py must configure num_predict (D-OPS-S08-020 fix)"
    )
    assert "num_ctx" in source, (
        "llm_factory.py must configure num_ctx (fits prompt + output)"
    )


def test_get_advogado_llm_has_num_predict_param():
    """D-DEV-S08-010: get_advogado_llm signature includes num_predict."""
    from bloco_workflow.personas.llm_factory import get_advogado_llm

    sig = inspect.signature(get_advogado_llm)
    assert "num_predict" in sig.parameters, (
        "get_advogado_llm must accept num_predict param"
    )
    assert "num_ctx" in sig.parameters, (
        "get_advogado_llm must accept num_ctx param"
    )

    # Default value sanity check
    default_num_predict = sig.parameters["num_predict"].default
    assert default_num_predict >= 1024, (
        f"num_predict default should be >=1024 (fits PecaRevisional ~1500 tokens), "
        f"got {default_num_predict}"
    )


def test_get_economista_llm_has_num_predict_param():
    """D-DEV-S08-010: get_economista_llm signature includes num_predict.

    Redator usa get_economista_llm (ADR-024 audit-honored tier mapping —
    all tiers resolve to qwen2.5:3b on economista host). Fix here propagates
    to redator pipeline.
    """
    from bloco_workflow.personas.llm_factory import get_economista_llm

    sig = inspect.signature(get_economista_llm)
    assert "num_predict" in sig.parameters, (
        "get_economista_llm must accept num_predict param (Redator uses this LLM)"
    )
    assert "num_ctx" in sig.parameters, (
        "get_economista_llm must accept num_ctx param"
    )

    # Default fits PecaRevisional output
    default_num_predict = sig.parameters["num_predict"].default
    assert default_num_predict >= 1024, (
        f"num_predict default should fit PecaRevisional ~1500 tokens, got {default_num_predict}"
    )


def test_llm_factory_documents_root_cause_in_source():
    """D-DEV-S08-010: source documents D-OPS-S08-020 + D-DEV-S08-010 for traceability."""
    from bloco_workflow.personas import llm_factory

    source = Path(llm_factory.__file__).read_text(encoding="utf-8")
    assert "D-DEV-S08-010" in source, (
        "Source must reference D-DEV-S08-010 for traceability"
    )
    assert "D-OPS-S08-020" in source or "Ollama default" in source, (
        "Source must explain why num_predict was added"
    )


# ─────────────────────────────────────────────────────────────────────
# Runtime tests — ChatOllama receives num_predict
# ─────────────────────────────────────────────────────────────────────


def test_get_advogado_llm_passes_num_predict_to_chat_ollama(monkeypatch):
    """D-DEV-S08-010 runtime: ChatOllama instantiated with num_predict kwarg."""
    captured_kwargs: dict = {}

    class _MockChatOllama:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    # Patch langchain_ollama.ChatOllama where it's imported
    import langchain_ollama

    monkeypatch.setattr(langchain_ollama, "ChatOllama", _MockChatOllama)

    from bloco_workflow.personas.llm_factory import get_advogado_llm

    get_advogado_llm(tier="lean", num_predict=2048, num_ctx=4096)

    assert captured_kwargs.get("num_predict") == 2048, (
        f"ChatOllama should receive num_predict=2048, got: {captured_kwargs.get('num_predict')}"
    )
    assert captured_kwargs.get("num_ctx") == 4096, (
        f"ChatOllama should receive num_ctx=4096, got: {captured_kwargs.get('num_ctx')}"
    )


def test_get_economista_llm_passes_num_predict_to_chat_ollama(monkeypatch):
    """D-DEV-S08-010 runtime: ChatOllama economista instantiated with num_predict."""
    captured_kwargs: dict = {}

    class _MockChatOllama:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    import langchain_ollama

    monkeypatch.setattr(langchain_ollama, "ChatOllama", _MockChatOllama)

    from bloco_workflow.personas.llm_factory import get_economista_llm

    get_economista_llm(num_predict=2048, num_ctx=4096)

    assert captured_kwargs.get("num_predict") == 2048, (
        f"ChatOllama should receive num_predict=2048, got: {captured_kwargs.get('num_predict')}"
    )
    assert captured_kwargs.get("num_ctx") == 4096, (
        f"ChatOllama should receive num_ctx=4096, got: {captured_kwargs.get('num_ctx')}"
    )
