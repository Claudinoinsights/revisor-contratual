"""Smoke test obrigatório PATCH F-MIN-01 + F-MIN-02 (ADR-003 PATCH 2).

Valida que 2 instâncias Ollama distintas + asyncio.gather produzem paralelismo REAL
(não placebo). Ratio paralela/serial DEVE ser <0.7. Se falhar, paralelismo broken
(debug OLLAMA_HOST distintos OU langchain-ollama>=0.2.0).

STATUS F-MIN-02 (sessão 56 — STORY 7 SUB-D):
  - RESOLVIDO empiricamente: langchain-ollama 1.x ChatOllama.ainvoke é coroutine real
    (asyncio.iscoroutinefunction=True); ollama.AsyncClient.chat subjacente também.
  - Smoke des-xfail: agora roda DE FATO se ambiente Ollama estiver pronto, senão SKIP
    (não FAIL). Tribunal severo: skip ≠ xfail; skip diz "ambiente não suporta",
    xfail dizia "implementação não existe" (não é mais o caso).
"""

from __future__ import annotations

import asyncio
import time

import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


def _ollama_available() -> bool:
    """True se ambos os Ollama instances respondem nas portas esperadas."""
    import urllib.error
    import urllib.request

    from bloco_workflow.personas.llm_factory import (
        DEFAULT_HOST_ADVOGADO,
        DEFAULT_HOST_ECONOMISTA,
    )

    for host in (DEFAULT_HOST_ADVOGADO, DEFAULT_HOST_ECONOMISTA):
        try:
            with urllib.request.urlopen(f"{host}/api/tags", timeout=1.0) as resp:
                if resp.status != 200:
                    return False
        except (urllib.error.URLError, OSError, TimeoutError):
            return False
    return True


@pytest.mark.skipif(
    not _ollama_available(),
    reason=(
        "F-MIN-02 RESOLVIDO mas ambiente sem Ollama em portas 11434+11435 com "
        "modelos baixados (sabia + qwen2.5:3b). Ambiente CI/laptop sem download "
        "completo. Para rodar: ollama pull sabia-7b-instruct + qwen2.5:3b + "
        "subir 2ª instância em :11435 (OLLAMA_HOST=127.0.0.1:11435 ollama serve)."
    ),
)
async def test_paralelismo_llm_real() -> None:
    """PATCH F-MIN-01 + F-MIN-02 RESOLVIDO: paralelismo real verificado.

    Mede latência serial vs paralela. Ratio < 0.7 = paralelismo OK.
    Se ratio >= 0.7, F-MIN-01 reapareceu (env OLLAMA_HOST colidindo)
    OU langchain-ollama regrediu para sync wrapper (improvável após 1.x).
    """
    from datetime import date, datetime
    from decimal import Decimal

    from bloco_contratos.contrato import (
        BacenData,
        ContratoMetadata,
        LinhaAmortizacao,
        ResultadoCalculo,
    )
    from bloco_contratos.jurisprudencia import JurisprudenciaItem
    from bloco_workflow.personas.advogado import advogado_redigir_tese_async
    from bloco_workflow.personas.economista import economista_analisar_async

    contrato_meta = ContratoMetadata(
        contract_hash="0" * 64,
        uf_contrato="BA",
        data_assinatura=date(2024, 3, 15),
        modalidade="CDC_VEICULOS_PF",
        valor_financiado="50000.00",
        taxa_contratual_am="1.99",
        n_parcelas=48,
    )
    calculo = ResultadoCalculo(
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
    docs = [
        JurisprudenciaItem(
            id_doc="STJ-S539",
            tribunal="STJ",
            court_id="STJ",
            tipo_doc="SUMULA",
            ementa="É permitida a capitalização de juros em periodicidade mensal nos contratos celebrados com instituições integrantes do Sistema Financeiro Nacional a partir de 31 de março de 2000.",
            peso_vinculacao=3,
            data_publicacao=date(2010, 6, 7),
            vigente_em=None,
            superseded_by=None,
            data_ultima_validacao=date.today(),
            url_oficial="https://www.stj.jus.br/sumulas",
            topics=["anatocismo", "capitalizacao_juros"],
        )
    ]
    bacen = BacenData(
        codigo_sgs=25471,
        modalidade="CDC_VEICULOS_PF",
        mes_ref="2024-03",
        taxa_media="2.05",
        fonte_url="https://api.bcb.gov.br/dados/serie/bcdata.sgs.25471/dados/ultimos/1?formato=json",
        fetched_at=datetime.now(),
        is_fallback=False,
    )

    # Sequencial
    t0 = time.perf_counter()
    await advogado_redigir_tese_async(calculo, docs, contrato_meta, "premium")
    await economista_analisar_async(contrato_meta, bacen)
    latencia_serial = time.perf_counter() - t0

    # Paralelo
    t0 = time.perf_counter()
    await asyncio.gather(
        advogado_redigir_tese_async(calculo, docs, contrato_meta, "premium"),
        economista_analisar_async(contrato_meta, bacen),
    )
    latencia_paralela = time.perf_counter() - t0

    ratio = latencia_paralela / latencia_serial
    assert ratio < 0.7, (
        f"Paralelismo BROKEN: ratio={ratio:.2f}. "
        f"Verificar: OLLAMA_HOST distintos OU OLLAMA_NUM_PARALLEL=2 "
        f"+ langchain-ollama>=0.2.0"
    )
