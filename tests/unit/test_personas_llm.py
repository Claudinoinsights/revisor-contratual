"""Testes unit bloco_workflow/personas LLM — advogado, economista, orchestrator paralelo.

Estratégia: 100% offline. invoke_fn injetável devolve JSON pré-fabricado.
Paralelismo medido via asyncio.sleep — não bate Ollama real.

Cenários cobertos:
  - Happy path: ambas personas geram output válido
  - Anti-fantasma sintático (TeseAdvogado.field_validator)
  - JSON malformado → ValidationError propagado
  - asyncio.gather paralelismo real (latência total ≈ max, não soma)
  - Atomicidade orchestrator: 1 falha = tudo levanta
  - llm_factory: portas distintas obrigatórias (F-MIN-01)
"""

from __future__ import annotations

import asyncio
import time
from datetime import date, datetime

import pytest
from pydantic import ValidationError

from bloco_contratos.contrato import (
    BacenData,
    ContratoMetadata,
    LinhaAmortizacao,
    ResultadoCalculo,
)
from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_contratos.personas import AnaliseMacroEconomica, TeseAdvogado
from bloco_workflow import run_personas_paralelas
from bloco_workflow.personas import (
    DEFAULT_HOST_ADVOGADO,
    DEFAULT_HOST_ECONOMISTA,
    MODEL_ECONOMISTA,
    TIER_TO_MODEL_ADVOGADO,
    advogado_redigir_tese_async,
    economista_analisar_async,
)

pytestmark = [pytest.mark.unit]
# asyncio mark aplicado via asyncio_mode=auto no pyproject.toml — só roda para async fns


# ─────────────────────────────────────────────────────────────────────
# Fixtures comuns
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def contrato_meta() -> ContratoMetadata:
    return ContratoMetadata(
        contract_hash="a" * 64,
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
            ementa=(
                "É permitida a capitalização de juros em periodicidade mensal nos contratos "
                "celebrados com instituições integrantes do Sistema Financeiro Nacional a "
                "partir de 31 de março de 2000."
            ),
            texto_completo=(
                "Súmula 539 do STJ: É permitida a capitalização de juros em "
                "periodicidade mensal nos contratos celebrados com instituições "
                "integrantes do Sistema Financeiro Nacional a partir de 31 de março de 2000."
            ),
            indexed_at=datetime(2024, 1, 1),
            data_ultima_validacao=date.today(),
        ),
        JurisprudenciaItem(
            id_doc="STF-S121",
            court_id="STF",
            tipo_doc="SUMULA",
            numero="121",
            binding=False,
            peso_vinculacao=4,
            legal_topic_principal="anatocismo",
            modalidade_relacionada=["CDC_VEICULOS_PF"],
            ano_julgamento=1963,
            ementa="É vedada a capitalização de juros, ainda que expressamente convencionada.",
            texto_completo=(
                "Súmula 121 do STF: É vedada a capitalização de juros, ainda que "
                "expressamente convencionada — vigente para contratos pré MP-2170."
            ),
            indexed_at=datetime(2024, 1, 1),
            data_ultima_validacao=date.today(),
        ),
    ]


@pytest.fixture
def bacen() -> BacenData:
    return BacenData(
        codigo_sgs=25471,
        modalidade="CDC_VEICULOS_PF",
        mes_ref="2024-03",
        taxa_media="2.05",
        fonte_url="https://api.bcb.gov.br/dados/serie/bcdata.sgs.25471/dados/ultimos/1?formato=json",
        fetched_at=datetime.now(),
        is_fallback=False,
    )


# ─────────────────────────────────────────────────────────────────────
# JSONs pré-fabricados (resposta LLM mockada)
# ─────────────────────────────────────────────────────────────────────


JSON_TESE_VALIDA = """\
{
  "tese_principal": "O contrato apresenta capitalização mensal lícita conforme STJ-S539, mas a taxa contratual destoa da média de mercado BACEN, configurando indício de onerosidade excessiva a ser apreciado pelo juízo.",
  "fundamentos_invocados": [
    {
      "id_doc": "STJ-S539",
      "citacao_textual": "É permitida a capitalização de juros em periodicidade mensal",
      "peso_vinculacao": 3,
      "court_id": "STJ"
    }
  ],
  "docs_consultados_ids": ["STJ-S539", "STF-S121"],
  "docs_efetivamente_citados_ids": ["STJ-S539"],
  "confianca": 0.85
}
"""

JSON_TESE_FANTASMA = """\
{
  "tese_principal": "Tese citando jurisprudência inventada que não está no top-K do RAG, configurando alucinação clássica de LLM em domínio jurídico.",
  "fundamentos_invocados": [
    {
      "id_doc": "STJ-S999",
      "citacao_textual": "súmula inexistente que LLM inventou",
      "peso_vinculacao": 4,
      "court_id": "STJ"
    }
  ],
  "docs_consultados_ids": ["STJ-S539", "STF-S121"],
  "docs_efetivamente_citados_ids": ["STJ-S999"],
  "confianca": 0.99
}
"""

JSON_ANALISE_VALIDA = """\
{
  "ciclo_selic_periodo": "alta_2022_2024",
  "taxa_atipica_bool": false,
  "comparacao_peer_modalities": {
    "CDC_VEICULOS_PF_25471_media_BACEN": "2,05% a.m.",
    "CARTAO_ROTATIVO_BACEN": "12,5% a.m."
  },
  "contexto_macro_resumido": "Em março/2024 a Selic estava em ciclo de alta encerrando-se. A taxa contratual de 1,99% a.m. está coerente com a média BACEN de 2,05% a.m. para CDC veículos PF, sem desvio relevante."
}
"""

JSON_MALFORMADO = """{ "tese_principal": "incompleto"  """  # JSON invalido


# ─────────────────────────────────────────────────────────────────────
# llm_factory — F-MIN-01 fix verification
# ─────────────────────────────────────────────────────────────────────


class TestLLMFactoryConfig:
    def test_hosts_default_distintos_obrigatorio(self) -> None:
        """F-MIN-01: paralelismo real exige portas distintas."""
        assert DEFAULT_HOST_ADVOGADO != DEFAULT_HOST_ECONOMISTA
        assert "11434" in DEFAULT_HOST_ADVOGADO
        assert "11435" in DEFAULT_HOST_ECONOMISTA

    def test_economista_modelo_fixo(self) -> None:
        """ADR-003 PATCH SUB-C: Economista é Qwen 2.5 3B FIXO (não configurável)."""
        assert MODEL_ECONOMISTA.startswith("qwen")
        assert "3b" in MODEL_ECONOMISTA.lower()

    def test_advogado_tiers_mapeados(self) -> None:
        """FR-TESE-02: 3 tiers configuráveis."""
        assert set(TIER_TO_MODEL_ADVOGADO.keys()) == {"lean", "balanced", "premium"}
        assert all("sabia" in m.lower() for m in TIER_TO_MODEL_ADVOGADO.values())


# ─────────────────────────────────────────────────────────────────────
# Advogado — happy path + anti-fantasma + erro JSON
# ─────────────────────────────────────────────────────────────────────


class TestAdvogadoLLM:
    async def test_happy_path_gera_tese_valida(
        self,
        calculo: ResultadoCalculo,
        docs: list[JurisprudenciaItem],
        contrato_meta: ContratoMetadata,
    ) -> None:
        async def fake_invoke(_prompt: str) -> str:
            return JSON_TESE_VALIDA

        tese = await advogado_redigir_tese_async(
            calculo, docs, contrato_meta, "premium", invoke_fn=fake_invoke
        )
        assert isinstance(tese, TeseAdvogado)
        assert tese.confianca == 0.85
        assert "STJ-S539" in tese.docs_efetivamente_citados_ids

    async def test_anti_fantasma_sintatico_rejeita_doc_fora_top_k(
        self,
        calculo: ResultadoCalculo,
        docs: list[JurisprudenciaItem],
        contrato_meta: ContratoMetadata,
    ) -> None:
        """LLM 'inventa' STJ-S999 fora do top-K → ValidationError CitationFantasma."""

        async def fake_invoke(_prompt: str) -> str:
            return JSON_TESE_FANTASMA

        with pytest.raises(ValidationError, match="CitationFantasma"):
            await advogado_redigir_tese_async(
                calculo, docs, contrato_meta, "premium", invoke_fn=fake_invoke
            )

    async def test_json_malformado_levanta(
        self,
        calculo: ResultadoCalculo,
        docs: list[JurisprudenciaItem],
        contrato_meta: ContratoMetadata,
    ) -> None:
        async def fake_invoke(_prompt: str) -> str:
            return JSON_MALFORMADO

        with pytest.raises(ValidationError):
            await advogado_redigir_tese_async(
                calculo, docs, contrato_meta, "premium", invoke_fn=fake_invoke
            )

    async def test_prompt_inclui_dados_contrato(
        self,
        calculo: ResultadoCalculo,
        docs: list[JurisprudenciaItem],
        contrato_meta: ContratoMetadata,
    ) -> None:
        captured = {}

        async def fake_invoke(prompt: str) -> str:
            captured["prompt"] = prompt
            return JSON_TESE_VALIDA

        await advogado_redigir_tese_async(
            calculo, docs, contrato_meta, "premium", invoke_fn=fake_invoke
        )
        prompt = captured["prompt"]
        assert "BA" in prompt
        assert "2024-03-15" in prompt
        assert "CDC_VEICULOS_PF" in prompt
        assert "STJ-S539" in prompt  # docs disponíveis foram listados


# ─────────────────────────────────────────────────────────────────────
# Economista — happy path + erro JSON
# ─────────────────────────────────────────────────────────────────────


class TestEconomistaLLM:
    async def test_happy_path_gera_analise_valida(
        self, contrato_meta: ContratoMetadata, bacen: BacenData
    ) -> None:
        async def fake_invoke(_prompt: str) -> str:
            return JSON_ANALISE_VALIDA

        analise = await economista_analisar_async(
            contrato_meta, bacen, invoke_fn=fake_invoke
        )
        assert isinstance(analise, AnaliseMacroEconomica)
        assert analise.ciclo_selic_periodo == "alta_2022_2024"
        assert analise.taxa_atipica_bool is False

    async def test_json_malformado_levanta(
        self, contrato_meta: ContratoMetadata, bacen: BacenData
    ) -> None:
        async def fake_invoke(_prompt: str) -> str:
            return JSON_MALFORMADO

        with pytest.raises(ValidationError):
            await economista_analisar_async(
                contrato_meta, bacen, invoke_fn=fake_invoke
            )

    async def test_prompt_inclui_dados_bacen(
        self, contrato_meta: ContratoMetadata, bacen: BacenData
    ) -> None:
        captured = {}

        async def fake_invoke(prompt: str) -> str:
            captured["prompt"] = prompt
            return JSON_ANALISE_VALIDA

        await economista_analisar_async(contrato_meta, bacen, invoke_fn=fake_invoke)
        prompt = captured["prompt"]
        assert "25471" in prompt  # SGS
        assert "2024-03" in prompt  # mes_ref
        assert "2.05" in prompt  # taxa_media


# ─────────────────────────────────────────────────────────────────────
# Orchestrator — paralelismo real + atomicidade
# ─────────────────────────────────────────────────────────────────────


class TestOrchestradorParalelo:
    async def test_run_paralelas_retorna_ambos_outputs(
        self,
        contrato_meta: ContratoMetadata,
        calculo: ResultadoCalculo,
        docs: list[JurisprudenciaItem],
        bacen: BacenData,
    ) -> None:
        async def fake_adv(_p: str) -> str:
            return JSON_TESE_VALIDA

        async def fake_eco(_p: str) -> str:
            return JSON_ANALISE_VALIDA

        tese, analise = await run_personas_paralelas(
            contrato_meta,
            calculo,
            docs,
            bacen,
            advogado_invoke_fn=fake_adv,
            economista_invoke_fn=fake_eco,
        )
        assert isinstance(tese, TeseAdvogado)
        assert isinstance(analise, AnaliseMacroEconomica)

    async def test_paralelismo_real_via_asyncio_gather(
        self,
        contrato_meta: ContratoMetadata,
        calculo: ResultadoCalculo,
        docs: list[JurisprudenciaItem],
        bacen: BacenData,
    ) -> None:
        """asyncio.gather DEVE rodar em paralelo: latência total ≈ max, não soma.

        Mock cada invoke com asyncio.sleep(0.3). Sequencial seria ~0.6s, paralelo ~0.3s.
        Ratio total/0.6 < 0.7 prova que asyncio.gather é REAL (não sync por baixo).
        """

        async def slow_adv(_p: str) -> str:
            await asyncio.sleep(0.3)
            return JSON_TESE_VALIDA

        async def slow_eco(_p: str) -> str:
            await asyncio.sleep(0.3)
            return JSON_ANALISE_VALIDA

        t0 = time.perf_counter()
        await run_personas_paralelas(
            contrato_meta,
            calculo,
            docs,
            bacen,
            advogado_invoke_fn=slow_adv,
            economista_invoke_fn=slow_eco,
        )
        latencia_total = time.perf_counter() - t0

        # Soma serial seria 0.6s; paralelo deve ser ~0.3s (max + overhead asyncio)
        assert latencia_total < 0.5, (
            f"Paralelismo BROKEN: latencia={latencia_total:.2f}s "
            f"(esperado <0.5s para asyncio.gather de 2x sleep(0.3)). "
            f"asyncio.gather pode estar rodando sequencialmente."
        )

    async def test_atomicidade_falha_propaga(
        self,
        contrato_meta: ContratoMetadata,
        calculo: ResultadoCalculo,
        docs: list[JurisprudenciaItem],
        bacen: BacenData,
    ) -> None:
        """Se UMA persona falha, gather propaga exceção — não retorna parcial."""

        async def fake_adv_ok(_p: str) -> str:
            return JSON_TESE_VALIDA

        async def fake_eco_broken(_p: str) -> str:
            return JSON_MALFORMADO

        with pytest.raises(ValidationError):
            await run_personas_paralelas(
                contrato_meta,
                calculo,
                docs,
                bacen,
                advogado_invoke_fn=fake_adv_ok,
                economista_invoke_fn=fake_eco_broken,
            )

    async def test_invoke_fns_sao_chamadas_uma_vez_cada(
        self,
        contrato_meta: ContratoMetadata,
        calculo: ResultadoCalculo,
        docs: list[JurisprudenciaItem],
        bacen: BacenData,
    ) -> None:
        adv_calls = {"n": 0}
        eco_calls = {"n": 0}

        async def fake_adv(_p: str) -> str:
            adv_calls["n"] += 1
            return JSON_TESE_VALIDA

        async def fake_eco(_p: str) -> str:
            eco_calls["n"] += 1
            return JSON_ANALISE_VALIDA

        await run_personas_paralelas(
            contrato_meta,
            calculo,
            docs,
            bacen,
            advogado_invoke_fn=fake_adv,
            economista_invoke_fn=fake_eco,
        )
        assert adv_calls["n"] == 1
        assert eco_calls["n"] == 1
