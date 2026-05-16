"""Pipeline end-to-end — revisar_contrato (PDF → VeredictoJuiz + audit) — STORY 9.

Orquestra os 7 blocos integráveis (Phase 2.B FECHADA):
  1. parsing      — bloco_engine.parsing.parse_contract
  2. cálculo      — bloco_engine.ferramentas_calculo (Price + anatocismo)
  3. BACEN        — bloco_engine.bacen.BacenClient
  4. vault        — bloco_vault.buscar_hibrida (RRF k=60)
  5. personas     — bloco_workflow.run_personas_sequencial (ADR-023 sequential)
  6. juiz         — bloco_workflow.personas.juiz_revisar (Python puro)
  7. audit        — bloco_audit.append_audit_entry (HMAC chain)

Decisões arquiteturais Morpheus (D-MOR-4.0-A..H) + ADR-023 (D-ARIA-S06-018):
  - Função ASYNC (precisa await em personas sequenciais)
  - TODOS os IO externos via dependency injection (testes 100% offline)
  - Audit registra ENTRY mesmo em REJEITADO ou em falha (auditabilidade total)
  - Atomicidade: 1 step falha → propaga; audit registra TENTATIVA antes
  - Query do vault: heurística MVP (ementa + súmulas aplicáveis + topics)
  - Personas sequencial (NÃO asyncio.gather): F-PROD-NEW-18 mitigation — VPS load 151
    em paralelismo qwen2.5:7b+3b → 0.17 em sequential. Atomicidade preservada.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import sys
import tempfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from bloco_audit.chain import append_audit_entry

logger = logging.getLogger(__name__)
from bloco_contratos.contrato import (
    BacenData,
    ContratoMetadata,
    LinhaAmortizacao,
    ParsedContract,
    ResultadoCalculo,
)
from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_contratos.personas import (
    AnaliseMacroEconomica,
    LLMTier,
    PecaRevisional,
    RelatorioInviabilidade,
    TeseAdvogado,
    VeredictoJuiz,
)
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
from bloco_engine.parsing.exceptions import (
    ParsingSubprocessFailedError,
    ParsingSubprocessTimeoutError,
)
from bloco_engine.parsing.orchestrator import parse_contract
from bloco_engine.parsing.type_detector import detect_pdf_type
from bloco_vault.busca import buscar_hibrida
from bloco_workflow.orchestrator import run_personas_sequencial
from bloco_workflow.personas.juiz import juiz_revisar
from bloco_workflow.personas.llm_factory import (
    MODEL_ECONOMISTA,
    TIER_TO_MODEL_ADVOGADO,
)
from bloco_workflow.personas.redator import (
    PecaHallucinationError,
    redator_invoke,
)


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
    modalidade_override: str | None = None,  # TD-SP06-MODE-PASS-01 Sprint 6 Bloco β Wave 3
    job_id: str | None = None,  # Sprint 6.1 F-γ-07 — pdf_filename multi-tenancy
    tier_advogado: LLMTier = "premium",
    tier_redator: LLMTier = "balanced",  # Sprint 6 Bloco γ — ADR-022 D1
    top_k_vault: int = 5,
    audit_secret_key: bytes | None = None,
    genesis_lock_path: Path | None = None,
    bacen_cache_dir: Path | None = None,
    # Sprint 6 Bloco γ — Step 7+8 (Redator + Weasyprint)
    peca_output_dir: Path | None = None,
    skip_peca_generation: bool = False,
    result_capture: dict[str, Any] | None = None,
    # Injections (testes offline)
    pymupdf_fn: Any = None,
    marker_fn: Any = None,
    sgs_fetcher: Any = None,
    embedder_fn: Any = None,
    advogado_invoke_fn: Any = None,
    economista_invoke_fn: Any = None,
    redator_invoke_fn: Any = None,
    pdf_renderer_fn: Any = None,
) -> VeredictoJuiz:
    """Pipeline end-to-end: PDF → VeredictoJuiz + audit log persistido.

    Args:
        pdf_path: caminho do PDF (pode ser placeholder se pdf_bytes fornecido)
        audit_path: caminho do audit.jsonl (caller decide; testes usam tmp_path)
        vault_conn: connection sqlite com vault inicializado (open_vault)
        uf_override / data_override: overrides metadata se parsing falhar
        modalidade_override: TD-SP06-MODE-PASS-01 — override explícito de
            ContratoMetadata.modalidade após parsing (substitui heurística regex
            _extract_modalidade). Valor deve ser literal válido ModalidadeContrato
            (CDC_VEICULOS_PF, CDC_BENS_PF, CDC_IMOBILIARIO, CARTAO_ROTATIVO).
            None preserva extração via regex parser.
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
        # ─── Step 1 — parsing PDF dual-path (Phase 4 ADR-027) ───────────
        # Sprint 7 Phase 4 (D-DEV-S07-002): PyMuPDF born-digital fast path.
        # Pre-detect PDF type ANTES decidir subprocess vs inline:
        # - born-digital (~80% CDC veículo): PyMuPDF inline ~10s (asyncio.to_thread)
        # - scanned (~20%): subprocess marker (Phase 3 ADR-026 preserved como fallback)
        #
        # Phase 3 ADR-026 subprocess isolation cura F-PROD-NEW-22 silent worker exit
        # (marker/surya/torch C extension os._exit() OR SIGABRT). Phase 4 evita
        # subprocess overhead unnecessary para born-digital PDFs (PyMuPDF stable).

        pdf_type = await asyncio.to_thread(detect_pdf_type, pdf_path)

        if pdf_type == "born_digital":
            # Fast path: PyMuPDF inline via asyncio.to_thread (~10s)
            # PyMuPDF nativo NÃO tem F-PROD-NEW-22 risk (não usa marker/surya/torch).
            try:
                parsed: ParsedContract = await asyncio.wait_for(
                    asyncio.to_thread(
                        parse_contract,
                        pdf_path,
                        pdf_bytes=pdf_bytes,
                        uf_override=uf_override,
                        data_override=data_override,
                        pymupdf_fn=pymupdf_fn,
                        marker_fn=marker_fn,
                    ),
                    timeout=30.0,  # Smart timeout born-digital: 30s suficiente
                )
            except asyncio.TimeoutError as timeout_exc:
                raise ParsingSubprocessTimeoutError(
                    f"parse_contract born-digital timeout 30s for {pdf_path}"
                ) from timeout_exc
        else:
            # Scanned path: subprocess marker isolation (Phase 3 ADR-026 preserved)
            # F-PROD-NEW-22 silent exit risk em scanned (marker library load) → subprocess
            metadata_dict = {
                "uf_override": uf_override,
                "data_override": data_override.isoformat() if data_override else None,
            }
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as metadata_file:
                json.dump(metadata_dict, metadata_file)
                metadata_path = metadata_file.name

            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-m",
                    "bloco_engine.parsing.subprocess_runner",
                    str(pdf_path),
                    metadata_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(), timeout=180.0
                    )
                except asyncio.TimeoutError as timeout_exc:
                    proc.terminate()
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        proc.kill()
                        await proc.wait()
                    raise ParsingSubprocessTimeoutError(
                        f"parse_contract subprocess timeout 180s for {pdf_path}"
                    ) from timeout_exc

                if proc.returncode != 0:
                    try:
                        error_data = json.loads(stderr_bytes.decode())
                        error_type = error_data.get(
                            "error_type", "ParsingSubprocessFailed"
                        )
                        error_msg = error_data.get(
                            "error_msg", stderr_bytes.decode()[:500]
                        )
                    except json.JSONDecodeError:
                        error_type = "ParsingSubprocessFailed"
                        error_msg = (
                            f"Subprocess exited code={proc.returncode} "
                            f"stderr={stderr_bytes.decode()[:500]}"
                        )
                    raise ParsingSubprocessFailedError(
                        error_type=error_type, error_msg=error_msg
                    )

                parsed = ParsedContract.model_validate_json(stdout_bytes.decode())
            finally:
                # LGPD §46: cleanup tempfile metadata
                Path(metadata_path).unlink(missing_ok=True)

        # TD-SP06-MODE-PASS-01 Sprint 6 Bloco β Wave 3:
        # Override modalidade explícito SPA sidebar → backend (substitui regex
        # _extract_modalidade que pode errar em PDFs ambíguos). Mutation via
        # Pydantic model_copy para preservar imutabilidade contract.
        if modalidade_override is not None:
            parsed = parsed.model_copy(
                update={
                    "metadata": parsed.metadata.model_copy(
                        update={"modalidade": modalidade_override}
                    )
                }
            )
            audit_payload["modalidade_override_used"] = True
            audit_payload["modalidade_override_value"] = modalidade_override

        audit_payload["parsing"] = {
            "parser_used": parsed.parser_used,
            "pages_count": parsed.pages_count,
            "fidelity_score": parsed.fidelity_score,
            "contract_hash": parsed.metadata.contract_hash,
        }

        # ─── Step 2 — cálculo determinístico ────────────────────────────
        # CC.38 fix F-01: wrap sync para não bloquear event loop.
        calculo: ResultadoCalculo = await asyncio.to_thread(
            _calcular_pipeline, parsed.metadata
        )
        audit_payload["calculo"] = {
            "pmt_composto": calculo.pmt_composto,
            "diferenca_anatocismo": calculo.diferenca_anatocismo,
            "classificacao": calculo.classificacao_anatocismo,
            "sumulas": calculo.sumulas_aplicaveis,
        }

        # ─── Step 3 — BACEN ─────────────────────────────────────────────
        # CC.38 fix F-01: wrap sync network IO BACEN com asyncio.to_thread.
        bacen_client = BacenClient(cache_dir=bacen_cache_dir, sgs_fetcher=sgs_fetcher)
        try:
            mes_ref = parsed.metadata.data_assinatura.strftime("%Y-%m")
            bacen_data: BacenData = await asyncio.to_thread(
                bacen_client.fetch_taxa_modalidade,
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
        # CC.38 fix F-01: wrap sync sqlite + embeddings com asyncio.to_thread.
        query = _build_vault_query(parsed.metadata, calculo)
        busca_result = await asyncio.to_thread(
            buscar_hibrida,
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

        # ─── Step 5 — personas LLM sequencial (ADR-023 F-PROD-NEW-18) ───
        tese: TeseAdvogado
        analise: AnaliseMacroEconomica
        tese, analise = await run_personas_sequencial(
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
        # CC.38 fix F-01: wrap sync com asyncio.to_thread (consistência).
        veredito: VeredictoJuiz = await asyncio.to_thread(
            juiz_revisar,
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

        # ─── Step 7 — Redator LLM (Sprint 6 Bloco γ — ADR-022 D1+D2) ────
        # FR-PECA-01: gera peça revisional formal CFOAB 8 seções OU
        # relatório de inviabilidade conforme veredito (FR-PECA-07 filter).
        # Hardening 3-camadas anti-hallucination embutido em redator_invoke.
        if skip_peca_generation:
            audit_payload["peca_generated"] = False
            audit_payload["peca_skipped_reason"] = "skip_peca_generation=True"
        else:
            # Sprint 6.1 F-γ-03 + F-γ-02 honesty: model_capture dict colhe actual_model_used
            # do redator_invoke (primary OR fallback quando fallback chain acionada).
            redator_model_capture: dict[str, Any] = {}
            try:
                peca: PecaRevisional | RelatorioInviabilidade = await redator_invoke(
                    veredito=veredito,
                    contrato_meta=parsed.metadata,
                    calculo=calculo,
                    tese=tese,
                    analise=analise,
                    docs=docs,
                    tier=tier_redator,
                    invoke_fn=redator_invoke_fn,
                    model_capture=redator_model_capture,
                )
            except PecaHallucinationError as exc:
                # Layer 2 anti-hallucination triggered — propagar como PipelineError
                # mas preservar contexto para audit/diagnose downstream.
                logger.warning("Redator hallucination detectada: %s", exc)
                raise PipelineError(
                    f"Redator produziu peça com citações fora do vault: {exc}"
                ) from exc

            audit_payload["peca_generated"] = True
            # Sprint 6.1 F-γ-03 + F-γ-02 honesty: registrar modelo ACTUAL usado em runtime
            # (primary OR fallback). Substituiu TIER_TO_MODEL_ADVOGADO[tier] estático que NÃO
            # refletia fallback chain dinâmica. Audit forense pós-incident agora pode
            # identificar exatamente qual LLM gerou a peça.
            #
            # Smith F-S21-02 fix (D-DEV-S06-023): fallback alinhado com D-DEV-S06-021 tier-down.
            # `MODEL_ECONOMISTA` (qwen2.5:3b) é o primary REAL do Redator desde F-PROD-NEW-19.
            #
            # ADR-024 Audit-Honored Tier (D-DEV-S06-026): adiciona `redator_tier_consumed`
            # (intent capture do caller) + `redator_tier_strategy` (marker estratégia ativa)
            # ao audit chain. Permite forense distinguir intent (tier="premium") vs reality
            # (modelo qwen2.5:3b currently — Sprint 7+ pode promover via TIER_TO_MODEL_REDATOR).
            #
            # ADR-025 Graceful Degradation (D-DEV-S06-026): detectar suffix
            # "-degraded-synthetic" em actual_model_used → registrar peca_format=degraded
            # + degraded_reason. Pipeline atomicity preservada (Steps 1-6 audit normais).
            actual_model = redator_model_capture.get(
                "actual_model_used",
                MODEL_ECONOMISTA,  # F-PROD-NEW-19 primary tier-down — audit honesto
            )
            audit_payload["redator_persona_used"] = actual_model
            audit_payload["redator_tier_consumed"] = tier_redator  # ADR-024 intent
            audit_payload["redator_tier_strategy"] = "audit-honored-v1"  # ADR-024 marker

            # ADR-025 graceful degradation detection — suffix marker do _default_invoke
            # Smith F-S28-02 MEDIUM fix (D-DEV-S06-029): suffix agora carrega reason real
            # do exception (truncado :100 chars). Format: "qwen2.5:3b-degraded-synthetic:REASON"
            if isinstance(actual_model, str) and "-degraded-synthetic" in actual_model:
                # Synthetic RelatorioInviabilidade retornada (ADR-025 Caminho A) — pipeline
                # NÃO falhou, mas peça é degraded. Forense pode investigar `degraded_reason`.
                audit_payload["peca_format"] = "degraded_synthetic"
                # Extrair reason após "-degraded-synthetic:" se presente (Smith F-S28-02 fix)
                marker = "-degraded-synthetic:"
                if marker in actual_model:
                    audit_payload["degraded_reason"] = actual_model.split(marker, 1)[1]
                else:
                    # Backward-compat: marker antigo sem reason suffix
                    audit_payload["degraded_reason"] = "primary_economista_failed_see_logger_error"
            else:
                audit_payload["peca_format"] = type(peca).__name__

            audit_payload["peca_citacoes_count"] = (
                len(peca.citacoes_jurisprudencia)
                if isinstance(peca, PecaRevisional)
                else 0
            )

            # ─── Step 8 — Weasyprint render PDF (ADR-022 D4+D5) ─────────
            # FR-PECA-02: render 3 templates Jinja2 OrSheva 7 + chmod LGPD §46
            if veredito.veredito == "APROVADO_100":
                template_name = "peca/inicial-revisional-veiculos.html"
            elif veredito.veredito == "APROVADO_COM_RISCO_HITL":
                template_name = "peca/inicial-revisional-com-hitl.html"
            else:  # REJEITADO
                template_name = "peca/relatorio-inviabilidade.html"

            # Output path: peca_output_dir / pdf_filename
            # Sprint 6.1 F-γ-07: pdf_filename hybrid job_id + contract_hash (multi-tenancy safe).
            # Preserva contract_hash audit trail + job_id uniqueness (2 users mesmo PDF input
            # produzem outputs distintos sem overwrite).
            if peca_output_dir is None:
                peca_output_dir = audit_path.parent / "pecas"
            if job_id is not None:
                pdf_filename = f"{job_id[:8]}-{parsed.metadata.contract_hash[:8]}.pdf"
            else:
                # Legacy fallback (tests/callers sem job_id) — contract_hash determinístico
                pdf_filename = f"{parsed.metadata.contract_hash[:16]}.pdf"
            pdf_output_path = peca_output_dir / pdf_filename
            audit_payload["peca_pdf_filename"] = pdf_filename

            render_context = {
                "peca": peca,
                "contrato": parsed.metadata,
                "veredito": veredito,
                "calculo": calculo,
                "gerado_em": datetime.now().isoformat(),
            }

            # Sprint 6.1 F-γ-06 graceful degradation: weasyprint render failure
            # NÃO derruba pipeline inteiro. Peça LLM Step 7 preserved + audit
            # registra peca_pdf_generated=False + reason. UI pode re-tentar Sprint 7+.
            try:
                # DI for tests: pdf_renderer_fn permite mock weasyprint offline
                if pdf_renderer_fn is None:
                    from bloco_engine.pdf.render import compute_pdf_hash, render_peca_pdf
                    pdf_bytes = await asyncio.to_thread(
                        render_peca_pdf,
                        template_name,
                        render_context,
                        pdf_output_path,
                    )
                    pdf_hash = compute_pdf_hash(pdf_bytes)
                else:
                    pdf_bytes = await asyncio.to_thread(
                        pdf_renderer_fn,
                        template_name,
                        render_context,
                        pdf_output_path,
                    )
                    import hashlib as _hl
                    pdf_hash = _hl.sha256(pdf_bytes).hexdigest()

                audit_payload["peca_pdf_path"] = str(pdf_output_path)
                audit_payload["peca_pdf_hash"] = pdf_hash
                audit_payload["peca_pdf_size_bytes"] = len(pdf_bytes)
                audit_payload["peca_template"] = template_name
                audit_payload["peca_pdf_generated"] = True

                # Expor peca_pdf_path para app.py popular JOBS[peca_pdf_path]
                # (AC-09 WEASYPRINT — opt-in via result_capture dict, retrocompat)
                if result_capture is not None:
                    result_capture["peca_pdf_path"] = str(pdf_output_path)
                    result_capture["peca_pdf_hash"] = pdf_hash
                    # Smith F-S28-01 CRITICAL fix (D-DEV-S06-029): ler de audit_payload
                    # (single source of truth) em vez de variável local `peca_format` que
                    # foi removida em D-DEV-S06-026 quando consolidamos em dict assignment.
                    result_capture["peca_format"] = audit_payload["peca_format"]
                    result_capture["peca_template"] = template_name
            except (OSError, FileNotFoundError, RuntimeError) as render_exc:
                # F-γ-06 fix: preserva peca LLM (Step 7) mesmo se PDF render (Step 8) falha.
                # Pipeline status SUCCESS — peca_pdf_generated=False sinaliza ausência PDF.
                logger.warning(
                    "Step 8 weasyprint render falhou (template=%s): %s — peca LLM preserved",
                    template_name, render_exc,
                )
                audit_payload["peca_pdf_generated"] = False
                audit_payload["peca_pdf_render_error"] = (
                    f"{type(render_exc).__name__}: {str(render_exc)[:300]}"
                )
                audit_payload["peca_template"] = template_name

                if result_capture is not None:
                    # Smith F-S28-01 CRITICAL fix (D-DEV-S06-029): single source of truth
                    result_capture["peca_format"] = audit_payload["peca_format"]
                    result_capture["peca_template"] = template_name
                    result_capture["peca_pdf_path"] = None
                    result_capture["peca_pdf_render_error"] = (
                        f"{type(render_exc).__name__}: {str(render_exc)[:300]}"
                    )

        audit_payload["status"] = "SUCCESS"
        audit_payload["completed_at"] = datetime.now().isoformat()

    except Exception as exc:
        # Audit registra TENTATIVA falha antes de propagar.
        # CC.39 fix F-03: protege append_audit_entry para não perder exc original
        # caso write do audit falhe (HMAC, IO, chain corrupted).
        audit_payload["status"] = "FAILED"
        audit_payload["error_type"] = type(exc).__name__
        audit_payload["error_msg"] = str(exc)[:500]
        audit_payload["completed_at"] = datetime.now().isoformat()
        try:
            append_audit_entry(
                "pipeline_revisar_contrato",
                audit_payload,
                audit_path=audit_path,
                genesis_lock_path=genesis_lock_path,
                secret_key=audit_secret_key,
            )
        except Exception as audit_exc:  # noqa: BLE001
            logger.error(
                "audit FAILED entry write failed: %s (original error: %s)",
                audit_exc, exc,
            )
        raise

    # ─── Step 9 — audit (sucesso) ───────────────────────────────────────
    # (Sprint 6 Bloco γ renumeração: Steps 7+8 são Redator+Weasyprint;
    # audit final é Step 9 — preserva ordering temporal post-emission.)
    append_audit_entry(
        "pipeline_revisar_contrato",
        audit_payload,
        audit_path=audit_path,
        genesis_lock_path=genesis_lock_path,
        secret_key=audit_secret_key,
    )

    return veredito
