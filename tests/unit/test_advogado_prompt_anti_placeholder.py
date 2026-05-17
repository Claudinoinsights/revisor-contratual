"""Unit tests for advogado.py prompt anti-placeholder hardening — D-DEV-S08-007 fix (D-OPS-S08-014).

Tests verify that PROMPT_TEMPLATE_ADVOGADO contains explicit instructions
against using "..." or generic placeholders in citacao_textual field.

Background:
- D-OPS-S08-014 (2026-05-17): Operator empirical E2E re-test pós deploy
  D-OPS-S08-013 (full rsync) revealed LLM advogado (qwen2.5:3b tier=lean)
  returning TeseAdvogado.fundamentos_invocados[0].citacao_textual='...'
  (3 chars violating Pydantic min_length=10).
- Root cause: prompt template line 50 used literal "..." in schema example,
  which lean LLM copied verbatim instead of generating real citation.
- Fix: replaced placeholder with real STJ-S539 citation example +
  added explicit "REGRA CRÍTICA citacao_textual" instructions.

Refs:
- D-OPS-S08-014 governance/CHECKPOINT-active.md Sessão 2026-05-17 Operator E2E
- D-DEV-S08-007 governance/CHECKPOINT-active.md Sessão 2026-05-17 Neo fix
- bloco_contratos/personas.py FundamentoInvocado.citacao_textual min_length=10
"""

from __future__ import annotations

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from bloco_contratos.contrato import (
    ContratoMetadata,
    LinhaAmortizacao,
    ResultadoCalculo,
)
from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_contratos.personas import TeseAdvogado
from bloco_workflow.personas.advogado import (
    PROMPT_TEMPLATE_ADVOGADO,
    advogado_redigir_tese_async,
)

pytestmark = [pytest.mark.unit]


# ─────────────────────────────────────────────────────────────────────
# Source-code review tests (consistent with project pattern)
# ─────────────────────────────────────────────────────────────────────


def test_prompt_template_contains_anti_placeholder_rule():
    """D-DEV-S08-007: prompt has explicit REGRA CRÍTICA section."""
    assert "REGRA CRÍTICA citacao_textual" in PROMPT_TEMPLATE_ADVOGADO, (
        "Prompt template must contain explicit anti-placeholder rule (D-OPS-S08-014 fix)"
    )
    assert "PELO MENOS 10 caracteres" in PROMPT_TEMPLATE_ADVOGADO, (
        "Prompt must explicitly state min_length=10 constraint"
    )
    assert "NUNCA use" in PROMPT_TEMPLATE_ADVOGADO, (
        "Prompt must forbid placeholder usage explicitly"
    )


def test_prompt_template_schema_example_has_real_citation():
    """D-DEV-S08-007: schema example uses real STJ-S539 citation (not '...' placeholder).

    LLM tier=lean copies whatever the example shows. If example is '...',
    LLM returns '...' literally → ValidationError.
    """
    # Real citation has substantive content, not placeholder
    assert "capitalizacao mensal de juros" in PROMPT_TEMPLATE_ADVOGADO, (
        "Schema example must contain real STJ-S539 citation, not placeholder"
    )

    # Check NO line in template has the exact pattern '"citacao_textual": "..."'
    # which would teach LLM to use placeholder
    forbidden_pattern = '"citacao_textual": "..."'
    assert forbidden_pattern not in PROMPT_TEMPLATE_ADVOGADO, (
        f"Schema example contains forbidden placeholder pattern: {forbidden_pattern} "
        "(D-OPS-S08-014 regression — LLM lean copies literal)"
    )


def test_prompt_template_schema_example_has_real_tese_principal():
    """D-DEV-S08-007: tese_principal example also uses real content."""
    # No "string >=50 chars" abstract placeholder — should be concrete example
    forbidden_pattern = '"tese_principal": "string'
    assert forbidden_pattern not in PROMPT_TEMPLATE_ADVOGADO, (
        f"tese_principal example must be concrete, not abstract '{forbidden_pattern}'"
    )


# ─────────────────────────────────────────────────────────────────────
# Runtime tests — Pydantic still hard-fails on short citation (regression guard)
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def contrato_meta() -> ContratoMetadata:
    return ContratoMetadata(
        contract_hash="a" * 64,
        uf_contrato="SP",
        data_assinatura=date(2025, 5, 15),
        modalidade="CDC_VEICULOS_PF",
        valor_financiado="35000.00",
        taxa_contratual_am="1.89",
        taxa_contratual_aa="25.36",
        n_parcelas=48,
    )


@pytest.fixture
def calculo() -> ResultadoCalculo:
    return ResultadoCalculo(
        pmt_composto="1115.67",
        pmt_simples="987.40",
        diferenca_anatocismo="-274.99",
        classificacao_anatocismo="ANATOCISMO_LICITO",
        sumulas_aplicaveis=["STF-S121", "STJ-S539", "STJ-T247"],
        tabela_amortizacao=[
            LinhaAmortizacao(
                n_parcela=1,
                saldo_inicial="35000.00",
                juros="661.50",
                amortizacao="454.17",
                valor_parcela="1115.67",
                saldo_final="34545.83",
            )
        ],
        taxa_contratual_aa_decimal="25.36",
    )


@pytest.fixture
def docs() -> list[JurisprudenciaItem]:
    return [
        JurisprudenciaItem(
            id_doc="STJ-S539",
            court_id="STJ",
            tipo_doc="SUMULA",
            numero="539",
            binding=False,
            peso_vinculacao=3,
            legal_topic_principal="capitalizacao_juros",
            modalidade_relacionada=["CDC_VEICULOS_PF"],
            ano_julgamento=2010,
            ementa="É lícita a capitalização mensal de juros nos contratos bancários celebrados após 31/03/2000.",
            texto_completo="Súmula 539 STJ — capitalização mensal lícita desde que expressamente pactuada.",
            indexed_at=datetime(2024, 1, 1),
            data_ultima_validacao=date.today(),
        ),
    ]


async def test_short_citation_still_rejected_by_pydantic(
    contrato_meta: ContratoMetadata,
    calculo: ResultadoCalculo,
    docs: list[JurisprudenciaItem],
):
    """D-DEV-S08-007 regression guard: even with prompt hardening, Pydantic
    still rejects citations < 10 chars (defense in depth).

    If LLM somehow ignores prompt and returns '...', Pydantic must still
    fail-hard. This guards against false-positive "fix worked" scenarios.
    """
    bad_llm_response = """{
        "tese_principal": "Cabe revisional do contrato CDC veículo para apurar capitalização indevida e abusiva.",
        "fundamentos_invocados": [
            {"id_doc": "STJ-S539", "citacao_textual": "...", "peso_vinculacao": 4, "court_id": "STJ"}
        ],
        "docs_consultados_ids": ["STJ-S539"],
        "docs_efetivamente_citados_ids": ["STJ-S539"],
        "confianca": 0.85
    }"""

    async def _bad_invoke(prompt: str) -> str:
        return bad_llm_response

    with pytest.raises(ValidationError) as exc_info:
        await advogado_redigir_tese_async(
            calculo=calculo,
            docs=docs,
            contrato_meta=contrato_meta,
            invoke_fn=_bad_invoke,
        )

    error_str = str(exc_info.value)
    assert "citacao_textual" in error_str, (
        "ValidationError must mention citacao_textual field"
    )
    assert "at least 10 characters" in error_str, (
        "Error must reference min_length=10 constraint"
    )


async def test_valid_citation_accepted(
    contrato_meta: ContratoMetadata,
    calculo: ResultadoCalculo,
    docs: list[JurisprudenciaItem],
):
    """D-DEV-S08-007: well-formed citation (>=10 chars) passes validation."""
    good_llm_response = """{
        "tese_principal": "Cabe revisional do contrato CDC veículo para apurar capitalização indevida.",
        "fundamentos_invocados": [
            {
                "id_doc": "STJ-S539",
                "citacao_textual": "E licita a capitalizacao mensal de juros nos contratos bancarios celebrados apos 31/03/2000.",
                "peso_vinculacao": 4,
                "court_id": "STJ"
            }
        ],
        "docs_consultados_ids": ["STJ-S539"],
        "docs_efetivamente_citados_ids": ["STJ-S539"],
        "confianca": 0.85
    }"""

    async def _good_invoke(prompt: str) -> str:
        return good_llm_response

    tese = await advogado_redigir_tese_async(
        calculo=calculo,
        docs=docs,
        contrato_meta=contrato_meta,
        invoke_fn=_good_invoke,
    )

    assert isinstance(tese, TeseAdvogado)
    assert len(tese.fundamentos_invocados) == 1
    assert len(tese.fundamentos_invocados[0].citacao_textual) >= 10
    assert tese.confianca == 0.85


async def test_prompt_includes_anti_placeholder_text_in_actual_invocation(
    contrato_meta: ContratoMetadata,
    calculo: ResultadoCalculo,
    docs: list[JurisprudenciaItem],
):
    """D-DEV-S08-007: prompt actually sent to LLM contains anti-placeholder rule.

    Spy invoke_fn captures the rendered prompt and verifies the critical
    instructions are present (not lost in template formatting).
    """
    captured_prompt: list[str] = []

    async def _spy_invoke(prompt: str) -> str:
        captured_prompt.append(prompt)
        return """{
            "tese_principal": "Cabe revisional do contrato CDC veículo conforme jurisprudência consolidada.",
            "fundamentos_invocados": [
                {
                    "id_doc": "STJ-S539",
                    "citacao_textual": "E licita a capitalizacao mensal de juros nos contratos bancarios.",
                    "peso_vinculacao": 4,
                    "court_id": "STJ"
                }
            ],
            "docs_consultados_ids": ["STJ-S539"],
            "docs_efetivamente_citados_ids": ["STJ-S539"],
            "confianca": 0.85
        }"""

    await advogado_redigir_tese_async(
        calculo=calculo,
        docs=docs,
        contrato_meta=contrato_meta,
        invoke_fn=_spy_invoke,
    )

    assert len(captured_prompt) == 1
    prompt_sent = captured_prompt[0]
    assert "REGRA CRÍTICA citacao_textual" in prompt_sent, (
        "Anti-placeholder rule must be in actual rendered prompt sent to LLM"
    )
    assert "PELO MENOS 10 caracteres" in prompt_sent, (
        "Min-length constraint must be in actual prompt"
    )
    assert "NUNCA use" in prompt_sent, (
        "Forbidden placeholder warning must be in actual prompt"
    )
