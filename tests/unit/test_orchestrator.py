"""Unit tests — bloco_workflow.orchestrator (run_personas_sequencial).

ADR-023 (D-ARIA-S06-018) refatorou paralelismo → sequential. Estes tests garantem:
- Advogado SEMPRE invocado ANTES de Economista (ordering crítico para F-PROD-NEW-18)
- Backward-compat alias `run_personas_paralelas` continua funcional
- Atomicidade preservada: Advogado raise → Economista nem inicia
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pytest

from bloco_contratos.contrato import (
    BacenData,
    ContratoMetadata,
    ResultadoCalculo,
)
from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_workflow.orchestrator import (
    run_personas_paralelas,  # backward-compat alias
    run_personas_sequencial,
)


# ─────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────


@pytest.fixture
def contrato_meta() -> ContratoMetadata:
    return ContratoMetadata(
        contract_hash="a" * 64,
        uf_contrato="SP",
        data_assinatura=date(2024, 1, 1),
        modalidade="CDC_VEICULOS_PF",
        valor_financiado="45000.00",
        taxa_contratual_aa="23.88",
        taxa_contratual_am="1.99",
        n_parcelas=60,
    )


@pytest.fixture
def calculo() -> ResultadoCalculo:
    return ResultadoCalculo(
        pmt_composto="1291.43",
        pmt_simples="1291.43",
        diferenca_anatocismo="0.00",
        classificacao_anatocismo="ANATOCISMO_LICITO",
        sumulas_aplicaveis=["STF-S121", "STJ-S539"],
        tabela_amortizacao=[],  # vazia OK para tests orchestrator
        taxa_contratual_aa_decimal="0.2388",
    )


@pytest.fixture
def bacen_data() -> BacenData:
    return BacenData(
        codigo_sgs=25471,
        modalidade="CDC_VEICULOS_PF",
        mes_ref="2024-12",
        taxa_media="1.99",
        fonte_url="https://api.bcb.gov.br/dados/serie/bcdata.sgs.25471/dados/ultimos/1?formato=json",
        fetched_at=datetime(2024, 12, 31, 23, 59, 59),
        is_fallback=False,
    )


@pytest.fixture
def docs() -> list[JurisprudenciaItem]:
    return []  # vazio é OK para testes orchestrator


# ─────────────────────────────────────────────────────────────────
# Helpers — mock invoke fns que retornam JSON Pydantic-válido
# ─────────────────────────────────────────────────────────────────


def _make_advogado_invoke_with_tracking(call_log: list[tuple[str, float]]) -> Any:
    """Mock advogado invoke que registra timestamp + retorna JSON TeseAdvogado válida."""

    async def _invoke(prompt: str) -> str:
        call_log.append(("advogado", time.perf_counter()))
        return json.dumps({
            "tese_principal": (
                "Anatocismo lícito conforme STF-S121 e STJ-S539 — capitalização "
                "em CDC veículos com taxa contratada compatível com média BACEN."
            ),
            "fundamentos_invocados": [
                {
                    "id_doc": "STF-S121",
                    "citacao_textual": "A capitalização de juros é permitida na forma da Súmula 121 do STF.",
                    "peso_vinculacao": 4,
                    "court_id": "STF",
                }
            ],
            "docs_consultados_ids": ["STF-S121", "STJ-S539"],
            "docs_efetivamente_citados_ids": ["STF-S121"],
            "confianca": 0.85,
        })

    return _invoke


def _make_economista_invoke_with_tracking(call_log: list[tuple[str, float]]) -> Any:
    """Mock economista invoke que registra timestamp + retorna JSON AnaliseMacroEconomica válida."""

    async def _invoke(prompt: str) -> str:
        call_log.append(("economista", time.perf_counter()))
        return json.dumps({
            "ciclo_selic_periodo": "estavel_2024",
            "taxa_atipica_bool": False,
            "comparacao_peer_modalities": {"CDC_VEICULOS_PF": "1.99"},
            "contexto_macro_resumido": (
                "Taxa contratada (1.99% a.m.) coincide com média BACEN para CDC "
                "Veículos PF no período — operação dentro do padrão de mercado, "
                "sem indícios de abusividade econômica em ciclo Selic estável."
            ),
        })

    return _invoke


# ─────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────


class TestSequentialOrdering:
    """ADR-023 AC-FIX-04: Advogado SEMPRE invocado ANTES de Economista."""

    @pytest.mark.asyncio
    async def test_advogado_called_before_economista(
        self,
        contrato_meta: ContratoMetadata,
        calculo: ResultadoCalculo,
        docs: list[JurisprudenciaItem],
        bacen_data: BacenData,
    ) -> None:
        """Ordering crítico — F-PROD-NEW-18 resolution depende de single-flight inference."""
        call_log: list[tuple[str, float]] = []

        await run_personas_sequencial(
            contrato_meta,
            calculo,
            docs,
            bacen_data,
            tier_advogado="balanced",
            advogado_invoke_fn=_make_advogado_invoke_with_tracking(call_log),
            economista_invoke_fn=_make_economista_invoke_with_tracking(call_log),
        )

        assert len(call_log) == 2, f"Esperado 2 calls, got {len(call_log)}"
        assert call_log[0][0] == "advogado", (
            f"AC-FIX-04: Advogado deveria ser PRIMEIRO, "
            f"got call_log[0]={call_log[0][0]!r}"
        )
        assert call_log[1][0] == "economista", (
            f"AC-FIX-04: Economista deveria ser SEGUNDO, "
            f"got call_log[1]={call_log[1][0]!r}"
        )
        # Ordem temporal estrita: economista t > advogado t (sequential)
        assert call_log[1][1] > call_log[0][1], (
            "Sequential ordering: economista timestamp deve ser > advogado timestamp"
        )


class TestBackwardCompatAlias:
    """ADR-023 AC-FIX-02: alias `run_personas_paralelas` continua funcional."""

    def test_alias_points_to_sequencial(self) -> None:
        assert run_personas_paralelas is run_personas_sequencial, (
            "Backward-compat alias `run_personas_paralelas` deve apontar para "
            "`run_personas_sequencial` (ADR-023)"
        )

    @pytest.mark.asyncio
    async def test_alias_executes_sequentially(
        self,
        contrato_meta: ContratoMetadata,
        calculo: ResultadoCalculo,
        docs: list[JurisprudenciaItem],
        bacen_data: BacenData,
    ) -> None:
        """Consumers usando o alias antigo recebem behavior sequential."""
        call_log: list[tuple[str, float]] = []

        result = await run_personas_paralelas(
            contrato_meta,
            calculo,
            docs,
            bacen_data,
            tier_advogado="balanced",
            advogado_invoke_fn=_make_advogado_invoke_with_tracking(call_log),
            economista_invoke_fn=_make_economista_invoke_with_tracking(call_log),
        )

        # Returns tuple (TeseAdvogado, AnaliseMacroEconomica)
        assert isinstance(result, tuple)
        assert len(result) == 2
        # Ordem sequential mantida via alias
        assert call_log[0][0] == "advogado"
        assert call_log[1][0] == "economista"


class TestAtomicidade:
    """ADR-023: Advogado raise → Economista nem inicia."""

    @pytest.mark.asyncio
    async def test_advogado_falha_economista_nao_executa(
        self,
        contrato_meta: ContratoMetadata,
        calculo: ResultadoCalculo,
        docs: list[JurisprudenciaItem],
        bacen_data: BacenData,
    ) -> None:
        """Atomicidade: se Advogado raise, Economista nem é chamado."""
        economista_called = False

        async def advogado_que_falha(prompt: str) -> str:
            raise RuntimeError("Advogado simulated failure")

        async def economista_tracker(prompt: str) -> str:
            nonlocal economista_called
            economista_called = True
            return "{}"  # nunca chega aqui

        with pytest.raises(RuntimeError, match="Advogado simulated failure"):
            await run_personas_sequencial(
                contrato_meta,
                calculo,
                docs,
                bacen_data,
                tier_advogado="balanced",
                advogado_invoke_fn=advogado_que_falha,
                economista_invoke_fn=economista_tracker,
            )

        assert economista_called is False, (
            "Atomicidade ADR-023: Advogado raise deveria abortar Economista. "
            "Got economista_called=True (BUG)."
        )
