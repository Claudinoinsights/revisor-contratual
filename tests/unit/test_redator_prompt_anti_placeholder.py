"""Unit tests for redator.py prompt anti-placeholder hardening — D-DEV-S08-009 fix (D-OPS-S08-018).

Tests verify PROMPT_REDATOR_PECA + SCHEMA_SKELETON_PECA/INVIABILIDADE contain
explicit min_length instructions and concrete examples (no abstract placeholders).

Background:
- D-OPS-S08-018 (2026-05-17): Operator empirical E2E test (pipeline 7/9 audit keys)
  revealed LLM redator (qwen2.5:3b tier=lean) returning PecaRevisional with
  dos_fatos < 200 chars and disclaimer_lgpd_oab < 200 chars, violating Pydantic.
- Root cause: SCHEMA_SKELETON_PECA used abstract placeholders like
  "(min 200 chars)" which lean LLM copied literally.
- Fix: replaced placeholders with REAL concrete examples that satisfy min_length
  + added "REGRA CRÍTICA min_length" section with explicit field rules.
- Pattern reused from D-DEV-S08-007 (advogado.py fix proven functional).

Refs:
- D-OPS-S08-018 governance/CHECKPOINT-active.md Sessão 2026-05-17 Operator E2E 7/9
- D-DEV-S08-009 governance/CHECKPOINT-active.md Sessão 2026-05-17 Neo redator fix
- D-DEV-S08-007 governance/CHECKPOINT-active.md (advogado pattern this reuses)
- bloco_contratos/personas.py PecaRevisional/RelatorioInviabilidade min_length constraints
"""

from __future__ import annotations

import pytest

from bloco_workflow.personas.redator import (
    PROMPT_REDATOR_PECA,
    SCHEMA_SKELETON_PECA,
    SCHEMA_SKELETON_INVIABILIDADE,
)

pytestmark = [pytest.mark.unit]


# ─────────────────────────────────────────────────────────────────────
# Source-code review tests
# ─────────────────────────────────────────────────────────────────────


def test_prompt_contains_regra_critica_min_length():
    """D-DEV-S08-009: prompt has explicit REGRA CRÍTICA min_length section."""
    assert "REGRA CRÍTICA min_length" in PROMPT_REDATOR_PECA, (
        "Prompt must contain explicit min_length rule section (D-OPS-S08-018 fix)"
    )
    assert "MÍNIMO 200 caracteres" in PROMPT_REDATOR_PECA, (
        "Prompt must explicitly state 200 chars min for dos_fatos/disclaimer"
    )
    assert "NUNCA use placeholders" in PROMPT_REDATOR_PECA, (
        "Prompt must explicitly forbid placeholder usage"
    )


def test_schema_skeleton_peca_has_real_examples_not_placeholders():
    """D-DEV-S08-009: SCHEMA_SKELETON_PECA uses real content, not abstract placeholders.

    LLM tier=lean copies whatever the example shows. If example is "(min X chars)",
    LLM returns short text + the placeholder literally → ValidationError.
    """
    # Forbidden abstract patterns
    forbidden_patterns = [
        "(min 50 chars)",
        "(min 100 chars)",
        "(min 200 chars)",
        "(min 300 chars)",
    ]
    for pattern in forbidden_patterns:
        assert pattern not in SCHEMA_SKELETON_PECA, (
            f"SCHEMA_SKELETON_PECA contains forbidden abstract placeholder: {pattern!r} "
            "— LLM lean copies literal (D-OPS-S08-018 root cause)"
        )

    # Required real content markers (proves schema has substantive examples)
    assert "Excelentíssimo Senhor Doutor Juiz" in SCHEMA_SKELETON_PECA, (
        "cabecalho example must be concrete (not placeholder)"
    )
    assert "Banco Exemplo S.A." in SCHEMA_SKELETON_PECA, (
        "qualificacao_partes example must be concrete"
    )
    assert "Em 15 de maio de 2025" in SCHEMA_SKELETON_PECA, (
        "dos_fatos example must be concrete narrative"
    )
    # D-DEV-S08-011: do_direito uses placeholder reference to vault (not literal IDs)
    # — prevents auto-induced hallucination (D-OPS-S08-022)
    assert "JURISPRUDENCIA_VAULT" in SCHEMA_SKELETON_PECA, (
        "do_direito example must reference JURISPRUDENCIA_VAULT (placeholder, not literal)"
    )
    assert "Provimento 209/2021 da OAB" in SCHEMA_SKELETON_PECA, (
        "disclaimer_lgpd_oab example must reference OAB Provimento"
    )


def test_schema_skeleton_peca_meets_min_length_constraints():
    """D-DEV-S08-009: examples in SCHEMA_SKELETON_PECA satisfy Pydantic min_length.

    Parses the JSON-like skeleton and verifies key fields meet their Pydantic
    constraints. If examples violate min_length, LLM follows broken example.
    """
    import json

    # SCHEMA_SKELETON_PECA is multi-line — strip trailing whitespace, parse JSON
    parsed = json.loads(SCHEMA_SKELETON_PECA.strip())

    # Match constraints from bloco_contratos/personas.py PecaRevisional
    constraints = {
        "cabecalho": 50,
        "qualificacao_partes": 100,
        "dos_fatos": 200,
        "do_direito": 300,
        "do_pedido": 100,
        "fecho": 50,
        "disclaimer_lgpd_oab": 200,
        "valor_causa_extenso": 10,
    }

    for field, min_len in constraints.items():
        actual = len(parsed[field])
        assert actual >= min_len, (
            f"SCHEMA_SKELETON_PECA.{field} example has {actual} chars, "
            f"violates Pydantic min_length={min_len} (D-OPS-S08-018 regression)"
        )


def test_schema_skeleton_inviabilidade_has_real_examples():
    """D-DEV-S08-009: SCHEMA_SKELETON_INVIABILIDADE also uses real content."""
    forbidden_patterns = [
        "(min 30 chars)",
        "(min 100 chars)",
        "(min 200 chars)",
    ]
    for pattern in forbidden_patterns:
        assert pattern not in SCHEMA_SKELETON_INVIABILIDADE, (
            f"SCHEMA_SKELETON_INVIABILIDADE contains forbidden placeholder: {pattern!r}"
        )

    assert "Relatório de Inviabilidade Revisional" in SCHEMA_SKELETON_INVIABILIDADE, (
        "cabecalho example must be concrete title"
    )
    assert "NÃO propositura" in SCHEMA_SKELETON_INVIABILIDADE, (
        "recomendacao example must be concrete (recomendar não protocolar)"
    )


def test_schema_skeleton_peca_has_no_literal_sumula_ids_in_citacoes():
    """D-DEV-S08-011: SCHEMA_SKELETON_PECA.citacoes_jurisprudencia uses placeholders.

    Prevents auto-induced hallucination (D-OPS-S08-022) where LLM copies
    literal Súmula IDs from examples instead of using JURISPRUDENCIA_VAULT
    dynamic IDs → Layer 2 anti-hallucination rejection.
    """
    # Specific Súmula IDs that previously caused hallucination
    forbidden_literal_ids = ['"STJ-S539"', '"STJ-S541"', '"STJ-T247"', '"STJ-S539", "STJ-S541"']
    for forbidden in forbidden_literal_ids:
        assert forbidden not in SCHEMA_SKELETON_PECA, (
            f"SCHEMA_SKELETON_PECA must NOT contain literal Súmula ID {forbidden} — "
            "LLM copies literally (D-OPS-S08-022 root cause)"
        )

    # Placeholder pattern should be present
    assert "JURISPRUDENCIA_VAULT" in SCHEMA_SKELETON_PECA, (
        "Example should reference JURISPRUDENCIA_VAULT (placeholder, not literal IDs)"
    )


def test_prompt_contains_anti_vault_hallucination_rule():
    """D-DEV-S08-011: prompt has explicit REGRA CRÍTICA citações vault section."""
    from bloco_workflow.personas.redator import PROMPT_REDATOR_PECA

    assert "REGRA CRÍTICA citações vault" in PROMPT_REDATOR_PECA, (
        "Prompt must contain explicit anti-vault-hallucination rule (D-OPS-S08-022 fix)"
    )
    assert "IGNORE quaisquer IDs específicos" in PROMPT_REDATOR_PECA, (
        "Prompt must explicitly tell LLM to ignore literal IDs in schema examples"
    )
    assert "REJEIÇÃO AUTOMÁTICA Layer 2" in PROMPT_REDATOR_PECA, (
        "Prompt must warn about Layer 2 automatic rejection"
    )


def test_schema_skeleton_inviabilidade_meets_min_length_constraints():
    """D-DEV-S08-009: examples in SCHEMA_SKELETON_INVIABILIDADE satisfy Pydantic."""
    import json

    parsed = json.loads(SCHEMA_SKELETON_INVIABILIDADE.strip())

    # Match constraints from bloco_contratos/personas.py RelatorioInviabilidade
    constraints = {
        "cabecalho": 30,
        "sintese_analise": 100,
        "diagnostico_tecnico": 200,
        "recomendacao": 100,
        "disclaimer_lgpd_oab": 200,
    }

    for field, min_len in constraints.items():
        actual = len(parsed[field])
        assert actual >= min_len, (
            f"SCHEMA_SKELETON_INVIABILIDADE.{field} example has {actual} chars, "
            f"violates Pydantic min_length={min_len}"
        )


# ─────────────────────────────────────────────────────────────────────
# Runtime tests — Pydantic still hard-fails on short fields (regression guard)
# ─────────────────────────────────────────────────────────────────────


def test_pydantic_still_rejects_short_dos_fatos():
    """D-DEV-S08-009 regression guard: even with prompt hardening, Pydantic
    still rejects PecaRevisional with dos_fatos < 200 chars (defense in depth).
    """
    from pydantic import ValidationError
    from bloco_contratos.personas import PecaRevisional

    # Build PecaRevisional with intentionally short dos_fatos
    with pytest.raises(ValidationError) as exc_info:
        PecaRevisional(
            cabecalho="Excelentíssimo Senhor Juiz de Direito da Vara Cível " * 2,
            qualificacao_partes="Autor: João + Ré: Banco" * 10,
            dos_fatos="Curto demais",  # < 200 chars → should fail
            do_direito="Aplicam-se as Súmulas STJ aplicáveis ao caso concreto " * 10,
            do_pedido="Diante do exposto, requer-se a procedência da ação " * 5,
            valor_causa="R$ 5.107,00",
            valor_causa_extenso="cinco mil cento e sete reais",
            fecho="Termos em que pede deferimento, São Paulo 2025",
            disclaimer_lgpd_oab="Insumo técnico-jurídico LGPD §11 §46 OAB Provimento 209/2021 não substitui responsabilidade profissional do advogado " * 2,
        )
    error_str = str(exc_info.value)
    assert "dos_fatos" in error_str, "ValidationError must mention dos_fatos"
    assert "at least 200 characters" in error_str, (
        "Error must reference min_length=200 constraint"
    )
