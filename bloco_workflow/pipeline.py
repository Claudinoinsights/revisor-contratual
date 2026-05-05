"""Pipeline end-to-end — revisar_contrato (PDF → VeredictoJuiz + audit) — STORY 9.

Orquestra os 7 blocos integráveis (Phase 2.B FECHADA):
  1. parsing      — bloco_engine.parsing.parse_contract
  2. cálculo      — bloco_engine.ferramentas_calculo (Price + anatocismo)
  3. BACEN        — bloco_engine.bacen.BacenClient
  4. vault        — bloco_vault.buscar_hibrida (RRF k=60)
  5. personas     — bloco_workflow.run_personas_paralelas (asyncio.gather)
  6. juiz         — bloco_workflow.personas.juiz_revisar (Python puro)
  7. audit        — bloco_audit.append_audit_entry (HMAC chain)

Decisões arquiteturais Morpheus (D-MOR-4.0-A..H):
  - Função ASYNC (precisa await em personas paralelas)
  - TODOS os IO externos via dependency injection (testes 100% offline)
  - Audit registra ENTRY mesmo em REJEITADO ou em falha (auditabilidade total)
  - Atomicidade: 1 step falha → propaga; audit registra TENTATIVA antes
  - Query do vault: heurística MVP (ementa + súmulas aplicáveis + topics)
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from bloco_audit.chain import append_audit_entry
from bloco_contratos.contrato import (
    BacenData,
    ContratoMetadata,
    LinhaAmortizacao,
    ParsedContract,
    ResultadoCalculo,
)
from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_contratos.personas import AnaliseMacroEconomica, LLMTier, TeseAdvogado, VeredictoJuiz
from bloco_engine.bacen.client import BacenClient
from bloco_engine.ferramentas_calculo.anatocismo import (
    classificar_anatocismo,
    sumulas_aplicaveis,
)
from bloco_engine.ferramentas_calculo.price import (
    aa_to_am,
    calcular_pmt_price,
    calcular_pmt_simples,
    gerar_tabela_amortizacao,
)
from bloco_engine.parsing.orchestrator import parse_contract
from bloco_vault.busca import buscar_hibrida
from bloco_workflow.orchestrator import run_personas_paralelas
from bloco_workflow.personas.juiz import juiz_revisar


class PipelineError(Exception):
    """Erro base do pipeline integrado."""


class VaultEmptyError(PipelineError):
    """Vault não tem documentos — Advogado não pode citar fundamentos."""


def _build_vault_query(
    contrato_meta: ContratoMetadata, calculo: ResultadoCalculo
) -> str:
    """Heurística MVP — query do vault baseada em modalidade + súmulas + classificação.

    TD-PIPELINE-QUERY-BUILDER LOW: substituir por query-builder dedicado
    quando vault crescer e busca ficar imprecisa.
    """
    partes = [
        contrato_meta.modalidade.replace("_", " ").lower(),
        calculo.classificacao_anatocismo.replace("_", " ").lower(),
        " ".join(calculo.sumulas_aplicaveis),
        "capitalização juros tabela price anatocismo bancário",
    ]
    return " ".join(p for p in partes if p)


def _calcular_pipeline(
    contrato_meta: ContratoMetadata,
) -> ResultadoCalculo:
    """Step 2 — calcular tabela Price + classificar anatocismo.

    Requer valor_financiado, taxa_contratual_am ou aa, n_parcelas em contrato_meta.
    """
    if contrato_meta.valor_financiado is None or contrato_meta.n_parcelas is None:
        raise PipelineError(
            "Cálculo exige valor_financiado E n_parcelas em ContratoMetadata. "
            "Forneça via parsing ou override."
        )

    # Resolver taxa em a.m. (preferido); senão converter de a.a.
    if contrato_meta.taxa_contratual_am:
        taxa_am = Decimal(contrato_meta.taxa_contratual_am) / Decimal("100")
        if contrato_meta.taxa_contratual_aa:
            taxa_aa_dec = Decimal(contrato_meta.taxa_contratual_aa) / Decimal("100")
        else:
            # Aproximação reversa: (1+i)^12 - 1
            taxa_aa_dec = (Decimal("1") + taxa_am) ** 12 - Decimal("1")
    elif contrato_meta.taxa_contratual_aa:
        taxa_aa_dec = Decimal(contrato_meta.taxa_contratual_aa) / Decimal("100")
        taxa_am = aa_to_am(taxa_aa_dec)
    else:
        raise PipelineError(
            "Cálculo exige taxa_contratual_am OU taxa_contratual_aa em ContratoMetadata."
        )

    capital = Decimal(contrato_meta.valor_financiado)
    n = contrato_meta.n_parcelas

    pmt_composto = calcular_pmt_price(capital, taxa_am, n)
    pmt_simples = calcular_pmt_simples(capital, taxa_am, n)
    diferenca = pmt_composto - pmt_simples

    # MVP: assume contrato bancário CDC com pactuação expressa (FR-CALC-03 default
    # operacional). TD-PIPELINE-PACTUACAO LOW: inferir do markdown extraído quando
    # parsing semântico estiver disponível (STORY hardening).
    classificacao = classificar_anatocismo(
        pmt_composto,
        pmt_simples,
        instituicao_sfn=True,
        pactuacao_expressa=True,
        data_assinatura=contrato_meta.data_assinatura,
    )
    sumulas = sumulas_aplicaveis(classificacao)

    tabela_dicts = gerar_tabela_amortizacao(capital, taxa_am, n)
    tabela = [LinhaAmortizacao(**linha) for linha in tabela_dicts]

    return ResultadoCalculo(
        pmt_composto=str(pmt_composto.quantize(Decimal("0.01"))),
        pmt_simples=str(pmt_simples.quantize(Decimal("0.01"))),
        diferenca_anatocismo=str(diferenca.quantize(Decimal("0.01"))),
        classificacao_anatocismo=classificacao,
        sumulas_aplicaveis=sumulas,
        tabela_amortizacao=tabela,
        taxa_contratual_aa_decimal=str(taxa_aa_dec),
    )


async def revisar_contrato(
    pdf_path: Path,
    *,
    audit_path: Path,
    vault_conn: sqlite3.Connection,
    pdf_bytes: bytes | None = None,
    uf_override: str | None = None,
    data_override: date | None = None,
    tier_advogado: LLMTier = "premium",
    top_k_vault: int = 5,
    audit_secret_key: bytes | None = None,
    genesis_lock_path: Path | None = None,
    bacen_cache_dir: Path | None = None,
    # Injections (testes offline)
    pymupdf_fn: Any = None,
    marker_fn: Any = None,
    sgs_fetcher: Any = None,
    embedder_fn: Any = None,
    advogado_invoke_fn: Any = None,
    economista_invoke_fn: Any = None,
) -> VeredictoJuiz:
    """Pipeline end-to-end: PDF → VeredictoJuiz + audit log persistido.

    Args:
        pdf_path: caminho do PDF (pode ser placeholder se pdf_bytes fornecido)
        audit_path: caminho do audit.jsonl (caller decide; testes usam tmp_path)
        vault_conn: connection sqlite com vault inicializado (open_vault)
        uf_override / data_override: overrides metadata se parsing falhar
        tier_advogado: lean/balanced/premium (FR-TESE-02)
        top_k_vault: docs do vault para personas
        audit_secret_key / genesis_lock_path: opcionais para audit (default env)
        pymupdf_fn / marker_fn / sgs_fetcher / embedder_fn / advogado_invoke_fn /
        economista_invoke_fn: dependency injection para testes offline.

    Returns:
        VeredictoJuiz com scores C1/C2/C3 + aderência + razões.

    Raises:
        Propaga exceções dos blocos (PDFEncrypted, BacenFetchExhausted,
        ValidationError, PipelineError, etc.). Audit registra TENTATIVA antes.
    """
    started_at = datetime.now()
    audit_payload: dict[str, Any] = {
        "pdf_path": str(pdf_path),
        "started_at": started_at.isoformat(),
    }

    try:
        # ─── Step 1 — parsing PDF ───────────────────────────────────────
        parsed: ParsedContract = parse_contract(
            pdf_path,
            pdf_bytes=pdf_bytes,
            uf_override=uf_override,
            data_override=data_override,
            pymupdf_fn=pymupdf_fn,
            marker_fn=marker_fn,
        )
        audit_payload["parsing"] = {
            "parser_used": parsed.parser_used,
            "pages_count": parsed.pages_count,
            "fidelity_score": parsed.fidelity_score,
            "contract_hash": parsed.metadata.contract_hash,
        }

        # ─── Step 2 — cálculo determinístico ────────────────────────────
        calculo: ResultadoCalculo = _calcular_pipeline(parsed.metadata)
        audit_payload["calculo"] = {
            "pmt_composto": calculo.pmt_composto,
            "diferenca_anatocismo": calculo.diferenca_anatocismo,
            "classificacao": calculo.classificacao_anatocismo,
            "sumulas": calculo.sumulas_aplicaveis,
        }

        # ─── Step 3 — BACEN ─────────────────────────────────────────────
        bacen_client = BacenClient(cache_dir=bacen_cache_dir, sgs_fetcher=sgs_fetcher)
        try:
            mes_ref = parsed.metadata.data_assinatura.strftime("%Y-%m")
            bacen_data: BacenData = bacen_client.fetch_taxa_modalidade(
                parsed.metadata.modalidade,
                mes_ref=mes_ref,
            )
        finally:
            bacen_client.close()
        audit_payload["bacen"] = {
            "codigo_sgs": bacen_data.codigo_sgs,
            "mes_ref": bacen_data.mes_ref,
            "taxa_media": bacen_data.taxa_media,
            "is_fallback": bacen_data.is_fallback,
        }

        # ─── Step 4 — vault busca híbrida ───────────────────────────────
        query = _build_vault_query(parsed.metadata, calculo)
        busca_result = buscar_hibrida(
            vault_conn,
            query,
            uf_contrato=parsed.metadata.uf_contrato,
            data_assinatura_contrato=parsed.metadata.data_assinatura,
            top_k=top_k_vault,
            embedder_fn=embedder_fn,
        )
        docs: list[JurisprudenciaItem] = busca_result.docs
        audit_payload["vault"] = {
            "query": query,
            "top_k": top_k_vault,
            "docs_recuperados": [d.id_doc for d in docs],
            "latencia_ms": busca_result.latencia_ms,
        }
        if not docs:
            raise VaultEmptyError(
                "Vault retornou docs=[] para a query — Advogado não pode citar fundamentos. "
                "Popule vault via scrapers ou ajuste query."
            )

        # ─── Step 5 — personas LLM paralelas ────────────────────────────
        tese: TeseAdvogado
        analise: AnaliseMacroEconomica
        tese, analise = await run_personas_paralelas(
            parsed.metadata,
            calculo,
            docs,
            bacen_data,
            tier_advogado=tier_advogado,
            advogado_invoke_fn=advogado_invoke_fn,
            economista_invoke_fn=economista_invoke_fn,
        )
        audit_payload["personas"] = {
            "tese_confianca": tese.confianca,
            "fundamentos_count": len(tese.fundamentos_invocados),
            "ciclo_selic": analise.ciclo_selic_periodo,
            "taxa_atipica": analise.taxa_atipica_bool,
        }

        # ─── Step 6 — juiz Python puro ──────────────────────────────────
        veredito: VeredictoJuiz = juiz_revisar(
            taxa_contratual_aa_decimal=Decimal(calculo.taxa_contratual_aa_decimal),
            bacen_data=bacen_data,
            tese=tese,
            uf_contrato=parsed.metadata.uf_contrato,
        )
        audit_payload["juiz"] = {
            "c1": veredito.c1_score,
            "c2": veredito.c2_score,
            "c3": veredito.c3_score,
            "aderencia": veredito.aderencia,
            "veredito": veredito.veredito,
        }
        audit_payload["status"] = "SUCCESS"
        audit_payload["completed_at"] = datetime.now().isoformat()

    except Exception as exc:
        # Audit registra TENTATIVA falha antes de propagar
        audit_payload["status"] = "FAILED"
        audit_payload["error_type"] = type(exc).__name__
        audit_payload["error_msg"] = str(exc)[:500]
        audit_payload["completed_at"] = datetime.now().isoformat()
        append_audit_entry(
            "pipeline_revisar_contrato",
            audit_payload,
            audit_path=audit_path,
            genesis_lock_path=genesis_lock_path,
            secret_key=audit_secret_key,
        )
        raise

    # ─── Step 7 — audit (sucesso) ───────────────────────────────────────
    append_audit_entry(
        "pipeline_revisar_contrato",
        audit_payload,
        audit_path=audit_path,
        genesis_lock_path=genesis_lock_path,
        secret_key=audit_secret_key,
    )

    return veredito
