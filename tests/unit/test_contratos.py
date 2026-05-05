"""Testes unitários dos Pydantic models compartilhados (bloco_contratos).

Cobertura: validações cruzadas, hard-fails, regras de negócio (NFR-MAINT-02 ≥60%).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from bloco_contratos import (
    AnaliseMacroEconomica,
    BacenData,
    ContratoMetadata,
    JurisprudenciaItem,
    LinhaAmortizacao,
    ParsedContract,
    ResultadoCalculo,
    TeseAdvogado,
    ValidacaoSemantica,
    VeredictoJuiz,
)
from bloco_contratos.contrato import LinhaAmortizacao as _LA  # type: ignore[attr-defined]
from bloco_contratos.personas import FundamentoInvocado


# ──────────────────────────────────────────────────────────────────────────────
# TeseAdvogado — validação cruzada citações ⊆ docs_recuperados (FR-TESE-01)
# ──────────────────────────────────────────────────────────────────────────────


def _fundamento(id_doc: str = "STJ-S539", peso: int = 4) -> FundamentoInvocado:
    return FundamentoInvocado(
        id_doc=id_doc,
        citacao_textual="É permitida a capitalização de juros com periodicidade inferior à anual...",
        peso_vinculacao=peso,
        court_id="STJ",
    )


def test_tese_advogado_valida_aceita_citacoes_subset():
    tese = TeseAdvogado(
        tese_principal=("Argumento de excesso de cobrança fundamentado em " * 3).strip(),
        fundamentos_invocados=[_fundamento("STJ-S539")],
        docs_consultados_ids=["STJ-S539", "STF-SV4", "TJBA-A100"],
        docs_efetivamente_citados_ids=["STJ-S539"],
        confianca=0.85,
    )
    assert tese.confianca == 0.85
    assert len(tese.fundamentos_invocados) == 1


def test_tese_advogado_hard_fail_citacao_fantasma():
    """LLM citou doc fora do RAG — DEVE explodir (anti-fantasma sintático)."""
    with pytest.raises(ValidationError) as exc_info:
        TeseAdvogado(
            tese_principal="X" * 60,
            fundamentos_invocados=[_fundamento("STJ-S999")],
            docs_consultados_ids=["STJ-S539"],
            docs_efetivamente_citados_ids=["STJ-S999"],  # NÃO está em consultados
            confianca=0.9,
        )
    assert "CitationFantasma" in str(exc_info.value)
    assert "STJ-S999" in str(exc_info.value)


def test_tese_advogado_confianca_fora_do_intervalo_falha():
    with pytest.raises(ValidationError):
        TeseAdvogado(
            tese_principal="X" * 60,
            fundamentos_invocados=[_fundamento()],
            docs_consultados_ids=["STJ-S539"],
            docs_efetivamente_citados_ids=["STJ-S539"],
            confianca=1.5,  # > 1.0
        )


# ──────────────────────────────────────────────────────────────────────────────
# VeredictoJuiz — aderência consistente com scores (FR-JUIZ-01 reprodutível)
# ──────────────────────────────────────────────────────────────────────────────


def test_veredicto_juiz_aderencia_100_aprovado_100():
    v = VeredictoJuiz(
        c1_score=1.0,
        c2_score=1.0,
        c3_score=1.0,
        aderencia=100.0,
        veredito="APROVADO_100",
        razoes=["Todos os 3 checks PASS"],
    )
    assert v.veredito == "APROVADO_100"


def test_veredicto_juiz_aderencia_inconsistente_falha():
    """Aderência declarada DEVE bater com média(c1+c2+c3)*100 (FR-JUIZ-01 reprodutibilidade)."""
    with pytest.raises(ValidationError) as exc_info:
        VeredictoJuiz(
            c1_score=1.0,
            c2_score=1.0,
            c3_score=1.0,
            aderencia=80.0,  # esperado=100
            veredito="APROVADO_COM_RISCO_HITL",
        )
    assert "inconsistente" in str(exc_info.value).lower()


def test_veredicto_juiz_threshold_70_hitl():
    """70 ≤ aderência < 100 → APROVADO_COM_RISCO_HITL (DP-04 resolvido)."""
    # c1=1, c2=0.5, c3=1 → média=0.833... → aderência ≈ 83.3
    v = VeredictoJuiz(
        c1_score=1.0,
        c2_score=0.5,
        c3_score=1.0,
        aderencia=83.3,
        veredito="APROVADO_COM_RISCO_HITL",
    )
    assert 70 <= v.aderencia < 100


# ──────────────────────────────────────────────────────────────────────────────
# AnaliseMacroEconomica — Economista (PATCH SUB-C ADR-003)
# ──────────────────────────────────────────────────────────────────────────────


def test_analise_macro_economica_minimo_valido():
    a = AnaliseMacroEconomica(
        ciclo_selic_periodo="alta_2022_2024",
        taxa_atipica_bool=True,
        comparacao_peer_modalities={"CDC_VEICULOS_PF": "1.85", "CDC_BENS_PF": "2.10"},
        contexto_macro_resumido=(
            "Ciclo de alta da Selic 2022-2024 levou taxas de financiamento "
            "veicular acima da média histórica em 30%. Contrato avaliado dentro "
            "da banda esperada para o período."
        ),
    )
    assert a.taxa_atipica_bool is True


# ──────────────────────────────────────────────────────────────────────────────
# ValidacaoSemantica — pipeline NLI híbrido (ADR-004)
# ──────────────────────────────────────────────────────────────────────────────


def test_validacao_semantica_pass():
    v = ValidacaoSemantica(
        id_doc="STJ-S539",
        frase_tese="A capitalização de juros é permitida em SFN com pactuação expressa",
        ementa_real="É permitida a capitalização de juros com periodicidade inferior à anual",
        similarity_score=0.82,
        nli_label="entailment",
        nli_confidence=0.91,
        veredito="PASS",
        razao="OK (sim=0.82, nli=entailment@0.91)",
    )
    assert v.veredito == "PASS"


def test_validacao_semantica_fail_polarity():
    """Paráfrase invertida — cosine alto + NLI=contradiction. Bloqueia emissão."""
    v = ValidacaoSemantica(
        id_doc="STJ-S539",
        frase_tese="A Súmula 539 STJ proíbe a capitalização infra-anual",  # OPOSTO
        ementa_real="É permitida a capitalização de juros com periodicidade inferior à anual",
        similarity_score=0.78,
        nli_label="contradiction",
        nli_confidence=0.87,
        veredito="FAIL_POLARITY",
        razao=(
            "NLI detectou CONTRADIÇÃO entre tese e ementa (confidence 0.87). "
            "Possível paráfrase invertida — verificar manualmente."
        ),
    )
    assert v.veredito == "FAIL_POLARITY"


# ──────────────────────────────────────────────────────────────────────────────
# ResultadoCalculo + LinhaAmortizacao — Decimal-as-string (FR-CALC-01)
# ──────────────────────────────────────────────────────────────────────────────


def test_linha_amortizacao_decimal_valido():
    linha = LinhaAmortizacao(
        n_parcela=1,
        saldo_inicial="50000.00",
        juros="125.50",
        amortizacao="800.00",
        valor_parcela="925.50",
        saldo_final="49200.00",
    )
    assert linha.juros == "125.50"


def test_linha_amortizacao_float_serializado_falha():
    """Decimal-as-string OBRIGATÓRIO — '0.1+0.2' não pode virar 0.30000000000000004."""
    with pytest.raises(ValidationError):
        LinhaAmortizacao(
            n_parcela=1,
            saldo_inicial="not_a_number",  # parser falha
            juros="0.0",
            amortizacao="0.0",
            valor_parcela="0.0",
            saldo_final="0.0",
        )


def test_resultado_calculo_classificacao_anatocismo_taxonomia():
    rc = ResultadoCalculo(
        pmt_composto="985.43",
        pmt_simples="950.00",
        diferenca_anatocismo="35.43",
        classificacao_anatocismo="ANATOCISMO_QUESTIONAVEL",
        sumulas_aplicaveis=["STF-S121", "STJ-S539"],
        tabela_amortizacao=[],
        taxa_contratual_aa_decimal="24.5",
    )
    assert rc.classificacao_anatocismo == "ANATOCISMO_QUESTIONAVEL"


# ──────────────────────────────────────────────────────────────────────────────
# ContratoMetadata — janela de datas (1986-presente)
# ──────────────────────────────────────────────────────────────────────────────


def test_contrato_metadata_data_pre_1986_falha():
    """Pré-Plano Cruzado fora do escopo (alta inflação)."""
    with pytest.raises(ValidationError):
        ContratoMetadata(
            contract_hash="a" * 64,
            uf_contrato="BA",
            data_assinatura=date(1985, 12, 31),
        )


def test_contrato_metadata_data_futura_falha():
    with pytest.raises(ValidationError):
        ContratoMetadata(
            contract_hash="a" * 64,
            uf_contrato="BA",
            data_assinatura=date(2099, 1, 1),
        )


def test_contrato_metadata_minimo_valido():
    m = ContratoMetadata(
        contract_hash="a" * 64,
        uf_contrato="BA",
        data_assinatura=date(2024, 3, 15),
    )
    assert m.modalidade == "CDC_VEICULOS_PF"  # default MVP


# ──────────────────────────────────────────────────────────────────────────────
# BacenData — formato mês_ref + flag fallback (FR-BACEN-03)
# ──────────────────────────────────────────────────────────────────────────────


def test_bacen_data_mes_ref_formato_iso_yyyy_mm():
    b = BacenData(
        codigo_sgs=25471,
        modalidade="CDC_VEICULOS_PF",
        mes_ref="2024-03",
        taxa_media="2.15",
        fonte_url="https://api.bcb.gov.br/dados/serie/bcdata.sgs.25471/dados",
        fetched_at=datetime.now(timezone.utc),
    )
    assert b.is_fallback is False  # default


def test_bacen_data_mes_ref_invalido_falha():
    with pytest.raises(ValidationError):
        BacenData(
            codigo_sgs=25471,
            modalidade="CDC_VEICULOS_PF",
            mes_ref="03/2024",  # formato BR — esperado ISO
            taxa_media="2.15",
            fonte_url="https://api.bcb.gov.br/dados/serie/bcdata.sgs.25471/dados",
            fetched_at=datetime.now(timezone.utc),
        )


def test_bacen_data_fallback_flag():
    b = BacenData(
        codigo_sgs=25471,
        modalidade="CDC_VEICULOS_PF",
        mes_ref="2024-03",
        taxa_media="2.10",  # última conhecida
        fonte_url="cache://diskcache",
        fetched_at=datetime.now(timezone.utc),
        is_fallback=True,
    )
    assert b.is_fallback is True


# ──────────────────────────────────────────────────────────────────────────────
# JurisprudenciaItem — schema enriquecido v1.0.2 (vigente_em + superseded_by)
# ──────────────────────────────────────────────────────────────────────────────


def test_jurisprudencia_vigente_em_none_significa_vigente():
    j = JurisprudenciaItem(
        id_doc="STJ-S539",
        court_id="STJ",
        tipo_doc="SUMULA",
        numero="539",
        binding=True,
        peso_vinculacao=3,
        legal_topic_principal="capitalizacao_juros",
        ano_julgamento=2015,
        ementa="É permitida a capitalização de juros com periodicidade inferior à anual...",
        texto_completo="Texto integral da súmula 539...",
        indexed_at=datetime.now(timezone.utc),
        vigente_em=None,  # vigente
        superseded_by=None,
        data_ultima_validacao=date.today(),
    )
    assert j.vigente_em is None
    assert j.superseded_by is None


def test_jurisprudencia_superseded_referencia_outro_doc():
    j_antiga = JurisprudenciaItem(
        id_doc="STJ-S100",
        court_id="STJ",
        tipo_doc="SUMULA",
        numero="100",
        binding=False,
        peso_vinculacao=2,
        legal_topic_principal="anatocismo",
        ano_julgamento=2000,
        ementa="Ementa antiga superseded em 2024",
        texto_completo="Texto integral histórico da súmula 100 (já não vigente em 2024).",
        indexed_at=datetime.now(timezone.utc),
        vigente_em=date(2024, 6, 30),  # vigente ATÉ 2024-06-30
        superseded_by="STJ-S539",  # FK lógica
        data_ultima_validacao=date.today(),
    )
    assert j_antiga.vigente_em == date(2024, 6, 30)
    assert j_antiga.superseded_by == "STJ-S539"


def test_jurisprudencia_id_doc_pattern():
    """ID deve seguir pattern AAA-NNN ou similar."""
    with pytest.raises(ValidationError):
        JurisprudenciaItem(
            id_doc="invalid id with spaces",
            court_id="STJ",
            tipo_doc="SUMULA",
            numero="1",
            binding=True,
            peso_vinculacao=3,
            legal_topic_principal="x",
            ano_julgamento=2020,
            ementa="X" * 30,
            texto_completo="Y" * 30,
            indexed_at=datetime.now(timezone.utc),
            data_ultima_validacao=date.today(),
        )


# ──────────────────────────────────────────────────────────────────────────────
# ParsedContract — fidelity_score opcional para FR-PARSE-01 AC
# ──────────────────────────────────────────────────────────────────────────────


def test_parsed_contract_fidelity_score_opcional():
    pc = ParsedContract(
        metadata=ContratoMetadata(
            contract_hash="a" * 64,
            uf_contrato="BA",
            data_assinatura=date(2024, 3, 15),
        ),
        markdown_extracted="# Contrato CDC...",
        parser_used="pymupdf4llm",
        parsed_at=datetime.now(timezone.utc),
        pages_count=12,
        fidelity_score=0.97,
    )
    assert pc.fidelity_score is not None and pc.fidelity_score >= 0.95


# ──────────────────────────────────────────────────────────────────────────────
# F-LLM-MED-01 hardening — Pydantic strict (extra='forbid') nos 5 schemas LLM-facing
# STORY 13 — defesa contra campos alucinados pelo LLM (boundary LLM↔sistema).
# ──────────────────────────────────────────────────────────────────────────────


def test_fundamento_invocado_rejeita_campos_extras():
    """F-LLM-MED-01: LLM pode alucinar campos extras — DEVE explodir."""
    with pytest.raises(ValidationError) as exc_info:
        FundamentoInvocado(
            id_doc="STJ-S539",
            citacao_textual="É permitida a capitalização de juros com periodicidade inferior à anual",
            peso_vinculacao=4,
            court_id="STJ",
            hallucinated_field="x",  # alucinação LLM
        )
    assert "extra" in str(exc_info.value).lower() or "forbidden" in str(exc_info.value).lower()


def test_tese_advogado_rejeita_campos_extras():
    """F-LLM-MED-01: TeseAdvogado é o output principal LLM — defesa crítica."""
    with pytest.raises(ValidationError) as exc_info:
        TeseAdvogado(
            tese_principal=("Argumento de excesso de cobrança fundamentado em " * 3).strip(),
            fundamentos_invocados=[_fundamento("STJ-S539")],
            docs_consultados_ids=["STJ-S539"],
            docs_efetivamente_citados_ids=["STJ-S539"],
            confianca=0.85,
            campo_inventado_pelo_llm="lorem",  # alucinação LLM
        )
    assert "extra" in str(exc_info.value).lower() or "forbidden" in str(exc_info.value).lower()


def test_analise_macro_rejeita_campos_extras():
    """F-LLM-MED-01: AnaliseMacroEconomica (Economista Qwen 3B) — defesa contra alucinação."""
    with pytest.raises(ValidationError) as exc_info:
        AnaliseMacroEconomica(
            ciclo_selic_periodo="alta_2022_2024",
            taxa_atipica_bool=True,
            comparacao_peer_modalities={"CDC_VEICULOS_PF": "1.85"},
            contexto_macro_resumido=(
                "Ciclo de alta da Selic 2022-2024 levou taxas de financiamento "
                "veicular acima da média histórica em 30%."
            ),
            previsao_futura="bull market",  # alucinação fora do schema
        )
    assert "extra" in str(exc_info.value).lower() or "forbidden" in str(exc_info.value).lower()


def test_veredicto_juiz_rejeita_campos_extras():
    """F-LLM-MED-01: VeredictoJuiz é Python puro mas schema é serializado/desserializado.

    Mesmo VeredictoJuiz não vindo do LLM diretamente, ele atravessa boundaries
    (audit log, API, etc) — extra='forbid' protege contra payload corrompido.
    """
    with pytest.raises(ValidationError) as exc_info:
        VeredictoJuiz(
            c1_score=1.0,
            c2_score=1.0,
            c3_score=1.0,
            aderencia=100.0,
            veredito="APROVADO_100",
            razoes=["Todos os 3 checks PASS"],
            score_misterioso=42,  # campo extra (alucinação ou bug serializer)
        )
    assert "extra" in str(exc_info.value).lower() or "forbidden" in str(exc_info.value).lower()


def test_validacao_semantica_rejeita_campos_extras():
    """F-LLM-MED-01: ValidacaoSemantica (NLI híbrido) — defesa contra alucinação."""
    with pytest.raises(ValidationError) as exc_info:
        ValidacaoSemantica(
            id_doc="STJ-S539",
            frase_tese="A capitalização de juros é permitida em SFN com pactuação expressa",
            ementa_real="É permitida a capitalização de juros com periodicidade inferior à anual",
            similarity_score=0.82,
            nli_label="entailment",
            nli_confidence=0.91,
            veredito="PASS",
            razao="OK (sim=0.82, nli=entailment@0.91)",
            extra_metadata={"foo": "bar"},  # alucinação fora do schema
        )
    assert "extra" in str(exc_info.value).lower() or "forbidden" in str(exc_info.value).lower()
