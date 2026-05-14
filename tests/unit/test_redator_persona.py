"""Testes unit Redator Revisional — TD-SP06-REDATOR-LLM-01 Sprint 6 Bloco γ.

Estratégia: 100% offline. redator_invoke_fn dependency injection.
3-camadas anti-hallucination verificadas:
  Layer 1: Pydantic strict (extra="forbid") — JSON malformado → ValidationError
  Layer 2: validar_citacoes_vault — citação fora vault → PecaHallucinationError
  Layer 3: regex valor_causa Pydantic field_validator

AC-08 coverage:
  - test_redator_aprovado_100_returns_peca_completa
  - test_redator_aprovado_com_risco_returns_peca_com_hitl
  - test_redator_rejeitado_returns_relatorio_inviabilidade
  - test_validar_citacoes_vault_raises_on_hallucinated_sumula
"""

from __future__ import annotations

import json
from datetime import date, datetime

import pytest
from pydantic import ValidationError

from bloco_contratos.contrato import (
    ContratoMetadata,
    LinhaAmortizacao,
    ResultadoCalculo,
)
from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_contratos.personas import (
    AnaliseMacroEconomica,
    FundamentoInvocado,
    PecaRevisional,
    RelatorioInviabilidade,
    TeseAdvogado,
    VeredictoJuiz,
)
from bloco_workflow.personas.redator import (
    PecaHallucinationError,
    redator_invoke,
    validar_citacoes_vault,
)

pytestmark = [pytest.mark.unit]


# ─────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def contrato_meta() -> ContratoMetadata:
    return ContratoMetadata(
        contract_hash="b" * 64,
        uf_contrato="BA",
        data_assinatura=date(2024, 3, 15),
        modalidade="CDC_VEICULOS_PF",
        valor_financiado="50000.00",
        taxa_contratual_am="1.99",
        taxa_contratual_aa="24.5",
        n_parcelas=48,
    )


@pytest.fixture
def calculo() -> ResultadoCalculo:
    return ResultadoCalculo(
        pmt_composto="1300.40",
        pmt_simples="1100.00",
        diferenca_anatocismo="200.40",
        classificacao_anatocismo="ANATOCISMO_LICITO",
        sumulas_aplicaveis=["STJ-S539"],
        tabela_amortizacao=[
            LinhaAmortizacao(
                n_parcela=1,
                saldo_inicial="50000.00",
                juros="995.00",
                amortizacao="305.40",
                valor_parcela="1300.40",
                saldo_final="49694.60",
            )
        ],
        taxa_contratual_aa_decimal="24.5",
    )


@pytest.fixture
def docs() -> list[JurisprudenciaItem]:
    ementa_539 = (
        "É permitida a capitalização de juros com periodicidade inferior a um ano "
        "em contratos celebrados com instituições integrantes do Sistema Financeiro "
        "Nacional a partir de 31/3/2000, desde que expressamente pactuada."
    )
    ementa_472 = (
        "A cobrança de comissão de permanência cujo valor seja calculado pela maior "
        "taxa de juros praticada no mercado, e limitada à taxa do contrato, exclui a "
        "exigência dos demais encargos moratórios."
    )
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
            ementa=ementa_539,
            texto_completo=ementa_539,
            indexed_at=datetime(2024, 1, 1, 12, 0, 0),
            vigente_em=None,
            superseded_by=None,
            data_ultima_validacao=date(2024, 1, 1),
        ),
        JurisprudenciaItem(
            id_doc="STJ-S472",
            court_id="STJ",
            tipo_doc="SUMULA",
            numero="472",
            binding=False,
            peso_vinculacao=3,
            legal_topic_principal="comissao_permanencia",
            modalidade_relacionada=["CDC_VEICULOS_PF"],
            ano_julgamento=2012,
            ementa=ementa_472,
            texto_completo=ementa_472,
            indexed_at=datetime(2024, 1, 1, 12, 0, 0),
            vigente_em=None,
            superseded_by=None,
            data_ultima_validacao=date(2024, 1, 1),
        ),
    ]


@pytest.fixture
def tese() -> TeseAdvogado:
    return TeseAdvogado(
        tese_principal=(
            "Aplica-se ao contrato a Súmula 539 STJ — capitalização exige pactuação "
            "expressa. Diferença anatocismo R$ 200,40 a ser restituída em dobro nos "
            "termos do art. 42 CDC."
        ),
        fundamentos_invocados=[
            FundamentoInvocado(
                id_doc="STJ-S539",
                citacao_textual="Capitalização exige pactuação expressa",
                peso_vinculacao=3,
                court_id="STJ",
            )
        ],
        docs_consultados_ids=["STJ-S539", "STJ-S472"],
        docs_efetivamente_citados_ids=["STJ-S539"],
        confianca=0.92,
    )


@pytest.fixture
def analise() -> AnaliseMacroEconomica:
    return AnaliseMacroEconomica(
        ciclo_selic_periodo="alta_2022_2024",
        taxa_atipica_bool=True,
        comparacao_peer_modalities={"CDC_VEICULOS_PF": "1.85% a.m. (média BACEN 2024-03)"},
        contexto_macro_resumido=(
            "Taxa contratual 1.99% a.m. encontra-se acima da média BACEN do período "
            "(1.85% a.m.), indicando desvio relevante de mercado em ciclo de alta Selic."
        ),
    )


@pytest.fixture
def veredito_aprovado_100() -> VeredictoJuiz:
    return VeredictoJuiz(
        c1_score=1.0,
        c2_score=1.0,
        c3_score=1.0,
        aderencia=100.0,
        veredito="APROVADO_100",
        razoes=["Taxa BACEN divergente +0.14pp", "Súmula vinculante aplicável", "Doc UF jurisdição"],
    )


@pytest.fixture
def veredito_aprovado_hitl() -> VeredictoJuiz:
    return VeredictoJuiz(
        c1_score=1.0,
        c2_score=0.5,
        c3_score=1.0,
        aderencia=83.3,
        veredito="APROVADO_COM_RISCO_HITL",
        razoes=["Aderência parcial — peso vinculação 3 (não 4)", "Recomenda revisão humana"],
    )


@pytest.fixture
def veredito_rejeitado() -> VeredictoJuiz:
    return VeredictoJuiz(
        c1_score=0.0,
        c2_score=0.5,
        c3_score=1.0,
        aderencia=50.0,
        veredito="REJEITADO",
        razoes=["Taxa BACEN coerente com mercado", "Anatocismo dentro do limite SFN"],
    )


# ─────────────────────────────────────────────────────────────────────
# Mock invoke_fn factories
# ─────────────────────────────────────────────────────────────────────


def _make_peca_revisional_json(
    *, citacoes: list[str] | None = None, pontos_atencao: str | None = None
) -> str:
    """Gera JSON válido PecaRevisional para mock LLM responses."""
    citacoes = citacoes if citacoes is not None else ["STJ-S539"]
    return json.dumps({
        "cabecalho": (
            "Excelentíssimo Senhor Doutor Juiz de Direito da Vara Cível "
            "da Comarca de Salvador, Estado da Bahia."
        ),
        "qualificacao_partes": (
            "AUTOR: Fulano de Tal, brasileiro, solteiro, comerciante, inscrito no "
            "CPF sob o nº 000.000.000-00, residente e domiciliado à Rua Exemplo nº 123, "
            "Salvador/BA. RÉ: Banco Exemplo S.A., instituição financeira, CNPJ 00.000.000/0001-00."
        ),
        "dos_fatos": (
            "Em 15 de março de 2024, o autor celebrou contrato de financiamento de veículo "
            "(CDC Veículos PF) com a ré, no valor de R$ 50.000,00 (cinquenta mil reais), a ser "
            "pago em 48 parcelas mensais de R$ 1.300,40, à taxa contratual de 1,99% ao mês. "
            "Constatou-se cobrança de juros capitalizados sem pactuação expressa adequada."
        ),
        "do_direito": (
            "Aplica-se ao caso a Súmula 539 do Superior Tribunal de Justiça, segundo a qual "
            "a capitalização de juros com periodicidade inferior a um ano em contratos "
            "celebrados com instituições do SFN exige pactuação expressa. No caso concreto, "
            "a diferença identificada entre o sistema composto e o simples (R$ 200,40 mensal) "
            "configura anatocismo a ser restituído em dobro nos termos do art. 42 do CDC. "
            "A jurisprudência consolidada do STJ ampara a presente pretensão revisional."
        ),
        "do_pedido": (
            "Diante do exposto, requer-se: a) a procedência total da ação; b) a declaração "
            "de abusividade da cobrança; c) a restituição em dobro dos valores cobrados a maior; "
            "d) a condenação da ré ao pagamento de custas e honorários advocatícios."
        ),
        "valor_causa": "R$ 9.619,20",
        "valor_causa_extenso": "nove mil seiscentos e dezenove reais e vinte centavos",
        "fecho": (
            "Termos em que pede e espera deferimento. Salvador/BA, 15 de maio de 2026. "
            "Advogado Responsável OAB/BA 99999."
        ),
        "disclaimer_lgpd_oab": (
            "Este documento é insumo técnico-jurídico gerado por sistema de inteligência "
            "artificial e não substitui a responsabilidade do advogado constituído conforme "
            "OAB Provimento 209/2021. Dados pessoais tratados sob égide da LGPD (Lei 13.709/2018), "
            "art. 11 e art. 46 — proteção e confidencialidade. Revisão humana obrigatória "
            "pré-protocolo. Sistema não fornece aconselhamento jurídico autônomo."
        ),
        "citacoes_jurisprudencia": citacoes,
        "pontos_atencao": pontos_atencao,
    })


def _make_relatorio_inviabilidade_json() -> str:
    return json.dumps({
        "cabecalho": "Relatório de Inviabilidade Revisional — Contrato bbbb…",
        "sintese_analise": (
            "A análise técnica do contrato CDC Veículos PF concluiu pela inviabilidade "
            "da ação revisional. Não foram identificados fundamentos consistentes para "
            "questionamento da taxa praticada ou da capitalização de juros."
        ),
        "diagnostico_tecnico": (
            "Scores apurados: C1=0.00 (taxa BACEN coerente com mercado, divergência <0.5pp); "
            "C2=0.50 (peso vinculação Súmulas baixo, máximo 3); C3=1.00 (doc da jurisdição BA presente). "
            "Aderência consolidada: 50.0% — abaixo do threshold mínimo de 70% para emissão de peça revisional."
        ),
        "motivos_rejeicao": [
            "Taxa contratual 1.99% a.m. dentro da média BACEN do período",
            "Ausência de Súmulas Vinculantes ou Repercussão Geral aplicáveis",
            "Cálculo de anatocismo não evidencia abusividade material",
        ],
        "recomendacao": (
            "Recomenda-se NÃO protocolar ação revisional com base na presente análise. "
            "Sugere-se buscar outros fundamentos ou aguardar evolução jurisprudencial. "
            "Cliente deve ser informado sobre a viabilidade técnica antes de qualquer decisão."
        ),
        "disclaimer_lgpd_oab": (
            "Este documento é insumo técnico-jurídico gerado por sistema de IA e não substitui "
            "a responsabilidade do advogado constituído conforme OAB Provimento 209/2021. "
            "Dados pessoais tratados sob égide da LGPD (Lei 13.709/2018), art. 11 e art. 46. "
            "Revisão humana obrigatória pré-decisão. Sistema não fornece aconselhamento autônomo."
        ),
    })


# ─────────────────────────────────────────────────────────────────────
# AC-08 Test 1: APROVADO_100 → PecaRevisional completa
# ─────────────────────────────────────────────────────────────────────


async def test_redator_aprovado_100_returns_peca_completa(
    contrato_meta, calculo, tese, analise, docs, veredito_aprovado_100
):
    """AC-06 + AC-08: veredito APROVADO_100 → PecaRevisional sem pontos_atencao."""
    async def mock_invoke(prompt: str) -> str:
        # ASCII-safe assertions (cp1252 console compat)
        assert "COMPLETA" in prompt
        assert "APROVADO_100" in prompt
        return _make_peca_revisional_json(citacoes=["STJ-S539", "STJ-S472"])

    result = await redator_invoke(
        veredito=veredito_aprovado_100,
        contrato_meta=contrato_meta,
        calculo=calculo,
        tese=tese,
        analise=analise,
        docs=docs,
        invoke_fn=mock_invoke,
    )

    assert isinstance(result, PecaRevisional)
    assert result.pontos_atencao is None
    assert result.valor_causa == "R$ 9.619,20"
    assert "STJ-S539" in result.citacoes_jurisprudencia
    assert len(result.do_direito) >= 300  # min_length compliance
    assert "OAB Provimento 209/2021" in result.disclaimer_lgpd_oab


# ─────────────────────────────────────────────────────────────────────
# AC-08 Test 2: APROVADO_COM_RISCO_HITL → PecaRevisional com pontos_atencao
# ─────────────────────────────────────────────────────────────────────


async def test_redator_aprovado_com_risco_returns_peca_com_hitl(
    contrato_meta, calculo, tese, analise, docs, veredito_aprovado_hitl
):
    """AC-06 + AC-08: veredito APROVADO_COM_RISCO_HITL → peça + pontos_atencao."""
    async def mock_invoke(prompt: str) -> str:
        # ASCII-safe substring para evitar cp1252 console issues em Windows test runner
        assert "Pontos de Aten" in prompt
        assert "APROVADO_COM_RISCO_HITL" in prompt
        return _make_peca_revisional_json(
            citacoes=["STJ-S539"],
            pontos_atencao=(
                "Aderência parcial 83.3% — peso vinculação Súmulas no nível 3 (não 4). "
                "Recomenda-se revisão humana antes do protocolo conforme veredito HITL do Juiz."
            ),
        )

    result = await redator_invoke(
        veredito=veredito_aprovado_hitl,
        contrato_meta=contrato_meta,
        calculo=calculo,
        tese=tese,
        analise=analise,
        docs=docs,
        invoke_fn=mock_invoke,
    )

    assert isinstance(result, PecaRevisional)
    assert result.pontos_atencao is not None
    assert "revisão humana" in result.pontos_atencao.lower()
    assert result.citacoes_jurisprudencia == ["STJ-S539"]


# ─────────────────────────────────────────────────────────────────────
# AC-08 Test 3: REJEITADO → RelatorioInviabilidade (template separate)
# ─────────────────────────────────────────────────────────────────────


async def test_redator_rejeitado_returns_relatorio_inviabilidade(
    contrato_meta, calculo, tese, analise, docs, veredito_rejeitado
):
    """AC-06 + AC-08: veredito REJEITADO → RelatorioInviabilidade (NÃO petição)."""
    async def mock_invoke(prompt: str) -> str:
        # ASCII-safe (cp1252 console compat)
        assert "RELAT" in prompt and "INVIABILIDADE" in prompt
        assert "REJEITADO" in prompt
        return _make_relatorio_inviabilidade_json()

    result = await redator_invoke(
        veredito=veredito_rejeitado,
        contrato_meta=contrato_meta,
        calculo=calculo,
        tese=tese,
        analise=analise,
        docs=docs,
        invoke_fn=mock_invoke,
    )

    assert isinstance(result, RelatorioInviabilidade)
    assert not isinstance(result, PecaRevisional)
    assert len(result.motivos_rejeicao) >= 1
    assert "não protocolar" in result.recomendacao.lower()


# ─────────────────────────────────────────────────────────────────────
# AC-08 Test 4: Layer 2 anti-hallucination — citação fora do vault
# ─────────────────────────────────────────────────────────────────────


async def test_validar_citacoes_vault_raises_on_hallucinated_sumula(
    contrato_meta, calculo, tese, analise, docs, veredito_aprovado_100
):
    """AC-04 + AC-08 Layer 2: citação fora do vault → PecaHallucinationError raised."""
    # Mock LLM retorna peça com Súmula INVENTADA (STJ-S999 não existe no vault)
    async def mock_invoke_hallucinated(prompt: str) -> str:
        return _make_peca_revisional_json(citacoes=["STJ-S539", "STJ-S999-FANTASMA"])

    with pytest.raises(PecaHallucinationError) as exc_info:
        await redator_invoke(
            veredito=veredito_aprovado_100,
            contrato_meta=contrato_meta,
            calculo=calculo,
            tese=tese,
            analise=analise,
            docs=docs,
            invoke_fn=mock_invoke_hallucinated,
        )

    assert "STJ-S999-FANTASMA" in str(exc_info.value)
    assert "fora do vault" in str(exc_info.value).lower()
    assert "FR-PECA-05" in str(exc_info.value)


# ─────────────────────────────────────────────────────────────────────
# Bonus: Layer 1 Pydantic strict — JSON malformado → ValidationError
# ─────────────────────────────────────────────────────────────────────


async def test_redator_layer1_pydantic_strict_rejects_extra_fields(
    contrato_meta, calculo, tese, analise, docs, veredito_aprovado_100
):
    """Layer 1 anti-hallucination: extra fields no JSON → ValidationError (extra='forbid')."""
    async def mock_invoke_with_extra(prompt: str) -> str:
        data = json.loads(_make_peca_revisional_json())
        data["campo_inventado_pelo_llm"] = "alucinação estrutural"
        return json.dumps(data)

    with pytest.raises(ValidationError):
        await redator_invoke(
            veredito=veredito_aprovado_100,
            contrato_meta=contrato_meta,
            calculo=calculo,
            tese=tese,
            analise=analise,
            docs=docs,
            invoke_fn=mock_invoke_with_extra,
        )


# ─────────────────────────────────────────────────────────────────────
# validar_citacoes_vault — unit isolated
# ─────────────────────────────────────────────────────────────────────


def test_validar_citacoes_vault_passes_when_all_cited_in_vault():
    """Happy path: todas as citações estão no vault → silenciosamente OK."""
    peca = PecaRevisional.model_validate_json(
        _make_peca_revisional_json(citacoes=["STJ-S539", "STJ-S472"])
    )
    # Não raises
    validar_citacoes_vault(peca, vault_doc_ids=["STJ-S539", "STJ-S472", "STJ-S297"])


def test_validar_citacoes_vault_passes_when_no_citations():
    """Edge case: peca.citacoes_jurisprudencia=[] → silenciosamente OK."""
    peca = PecaRevisional.model_validate_json(_make_peca_revisional_json(citacoes=[]))
    validar_citacoes_vault(peca, vault_doc_ids=["STJ-S539"])


# ─────────────────────────────────────────────────────────────────────
# Sprint 6.1 F-γ-03: model_capture dict propagation (actual_model_used)
# ─────────────────────────────────────────────────────────────────────


async def test_model_capture_records_tier_when_invoke_fn_provided(
    contrato_meta, calculo, tese, analise, docs, veredito_aprovado_100
):
    """F-γ-03 Sprint 6.1: model_capture dict propaga actual_model_used quando invoke_fn provided.

    Em tests offline (invoke_fn mock injection), redator_invoke registra
    actual_model_used = TIER_TO_MODEL_ADVOGADO[tier] (primary mapping).
    """
    from bloco_workflow.personas.llm_factory import TIER_TO_MODEL_ADVOGADO

    async def mock_invoke(prompt: str) -> str:
        return _make_peca_revisional_json(citacoes=["STJ-S539"])

    model_capture: dict = {}
    await redator_invoke(
        veredito=veredito_aprovado_100,
        contrato_meta=contrato_meta,
        calculo=calculo,
        tese=tese,
        analise=analise,
        docs=docs,
        tier="balanced",
        invoke_fn=mock_invoke,
        model_capture=model_capture,
    )

    assert "actual_model_used" in model_capture
    assert model_capture["actual_model_used"] == TIER_TO_MODEL_ADVOGADO["balanced"]
    assert model_capture["actual_model_used"] == "qwen2.5:7b"


async def test_model_capture_none_does_not_crash(
    contrato_meta, calculo, tese, analise, docs, veredito_aprovado_100
):
    """F-γ-03 Sprint 6.1: model_capture=None (default) não causa AttributeError."""
    async def mock_invoke(prompt: str) -> str:
        return _make_peca_revisional_json(citacoes=["STJ-S539"])

    # Retrocompat — chamada sem model_capture (Bloco γ callers existentes)
    result = await redator_invoke(
        veredito=veredito_aprovado_100,
        contrato_meta=contrato_meta,
        calculo=calculo,
        tese=tese,
        analise=analise,
        docs=docs,
        tier="balanced",
        invoke_fn=mock_invoke,
        # model_capture=None default
    )
    assert isinstance(result, PecaRevisional)


def test_fallback_map_configured_per_tier():
    """F-γ-03 Sprint 6.1: FALLBACK_MAP exposed + configured per tier (ADR-022 D1).

    - lean: None (degraded mode sem fallback)
    - balanced (DEFAULT): qwen2.5:7b primary → sabia-7b-instruct fallback
    - premium: sabia-7b-instruct primary → qwen2.5:7b fallback
    """
    from bloco_workflow.personas.redator import FALLBACK_MAP

    assert FALLBACK_MAP["lean"] is None
    assert FALLBACK_MAP["balanced"] == "sabia-7b-instruct"
    assert FALLBACK_MAP["premium"] == "qwen2.5:7b"


# ─────────────────────────────────────────────────────────────────────
# Sprint 6.1 Wave 6.1.2 — F-γ-04 Layer 3 NLI semantic validator (ADR-022 D2 patch)
# ─────────────────────────────────────────────────────────────────────


async def test_layer_3_skipped_when_fundamentos_invocados_none(docs):
    """F-γ-04 Sprint 6.1: Layer 3 opt-in retrocompat — peça sem fundamentos_invocados skip."""
    from bloco_workflow.personas.redator import validar_citacoes_nli

    peca = PecaRevisional.model_validate_json(_make_peca_revisional_json())
    # peca.fundamentos_invocados is None (default)

    result = await validar_citacoes_nli(peca, docs, nli_validator_fn=None)
    # NÃO raises NotImplementedError porque fundamentos_invocados=None → early return
    assert result == []


async def test_layer_3_raises_notimplementederror_when_default(docs):
    """F-γ-04 Sprint 6.1: nli_validator_fn=None + fundamentos_invocados populated → NotImplementedError.

    Real implementation (sentence-transformers + BERT) é Sprint 7+ TD-SP07-NLI-HYBRID-REAL.
    """
    from bloco_workflow.personas.redator import validar_citacoes_nli
    from bloco_contratos.personas import FundamentoInvocado

    peca = PecaRevisional.model_validate_json(_make_peca_revisional_json())
    # Forçar fundamentos_invocados populated via model_copy
    peca_with_fundamentos = peca.model_copy(update={
        "fundamentos_invocados": [
            FundamentoInvocado(
                id_doc="STJ-S539",
                citacao_textual="Capitalização juros exige pactuação expressa",
                peso_vinculacao=3,
                court_id="STJ",
            )
        ]
    })

    with pytest.raises(NotImplementedError, match="TD-SP07-NLI-HYBRID-REAL"):
        await validar_citacoes_nli(peca_with_fundamentos, docs, nli_validator_fn=None)


async def test_layer_3_passes_aligned_citation(docs):
    """F-γ-04 Sprint 6.1: NLI label=entailment → validations retornadas sem raise."""
    from bloco_workflow.personas.redator import validar_citacoes_nli
    from bloco_contratos.personas import FundamentoInvocado, ValidacaoSemantica

    async def mock_nli_entailment(citacao_textual: str, ementa: str) -> ValidacaoSemantica:
        return ValidacaoSemantica(
            id_doc="STJ-S539",
            frase_tese=citacao_textual,
            ementa_real=ementa,
            similarity_score=0.92,
            nli_label="entailment",
            nli_confidence=0.95,
            veredito="PASS",
            razao="Citação alinhada com ementa real",
        )

    peca = PecaRevisional.model_validate_json(_make_peca_revisional_json())
    peca_with_fundamentos = peca.model_copy(update={
        "fundamentos_invocados": [
            FundamentoInvocado(
                id_doc="STJ-S539",
                citacao_textual="Capitalização juros exige pactuação expressa",
                peso_vinculacao=3,
                court_id="STJ",
            )
        ]
    })

    validations = await validar_citacoes_nli(
        peca_with_fundamentos, docs, nli_validator_fn=mock_nli_entailment
    )

    assert len(validations) == 1
    assert validations[0].nli_label == "entailment"
    assert validations[0].veredito == "PASS"


async def test_layer_3_blocks_inverted_interpretation(docs):
    """F-γ-04 Sprint 6.1: NLI label=contradiction → PecaHallucinationError raised.

    Cenário: peça afirma o OPOSTO do que a Súmula real diz.
    Layer 2 (vault id check) passa porque STJ-S539 existe no vault.
    Layer 3 (semantic NLI) detecta interpretação invertida e bloqueia.
    """
    from bloco_workflow.personas.redator import validar_citacoes_nli
    from bloco_contratos.personas import FundamentoInvocado, ValidacaoSemantica

    async def mock_nli_contradiction(citacao_textual: str, ementa: str) -> ValidacaoSemantica:
        return ValidacaoSemantica(
            id_doc="STJ-S539",
            frase_tese=citacao_textual,
            ementa_real=ementa,
            similarity_score=0.85,
            nli_label="contradiction",
            nli_confidence=0.93,
            veredito="FAIL_POLARITY",
            razao="Citação afirma o oposto do que a Súmula 539 STJ diz",
        )

    peca = PecaRevisional.model_validate_json(_make_peca_revisional_json())
    peca_inverted = peca.model_copy(update={
        "fundamentos_invocados": [
            FundamentoInvocado(
                id_doc="STJ-S539",
                citacao_textual="Súmula 539 PROÍBE capitalização em qualquer hipótese",  # FALSO
                peso_vinculacao=3,
                court_id="STJ",
            )
        ]
    })

    with pytest.raises(PecaHallucinationError, match="Layer 3 NLI bloqueou"):
        await validar_citacoes_nli(
            peca_inverted, docs, nli_validator_fn=mock_nli_contradiction
        )
