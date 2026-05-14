"""Redator Revisional — gera PecaRevisional ou RelatorioInviabilidade (FR-PECA-01).

Sprint 6 Bloco γ — Story TD-SP06-REDATOR-LLM-01.

Decisão arquitetural ADR-022:
  - D1: Tier configurável (lean=qwen | balanced=qwen+sabia fallback | premium=sabia)
  - D2: Hardening anti-hallucination 3-camadas:
      1. Pydantic strict extra="forbid" (bloco_contratos/personas.py)
      2. Vault-restricted citations (validar_citacoes_vault aqui)
      3. Validador post-LLM (regex valor_causa via Pydantic)
  - D3: Filtro FR-PECA-07:
      APROVADO_100              → PecaRevisional (completa)
      APROVADO_COM_RISCO_HITL   → PecaRevisional (com pontos_atencao)
      REJEITADO                 → RelatorioInviabilidade

Pattern mirror: bloco_workflow/personas/advogado.py (ADR-003).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Literal

from bloco_contratos.contrato import ContratoMetadata, ResultadoCalculo
from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_contratos.personas import (
    AnaliseMacroEconomica,
    LLMTier,
    PecaRevisional,
    RelatorioInviabilidade,
    TeseAdvogado,
    ValidacaoSemantica,
    VeredictoJuiz,
)
from bloco_workflow.personas.llm_factory import (
    DEFAULT_HOST_ADVOGADO,
    TIER_TO_MODEL_ADVOGADO,
    get_advogado_llm,
)

import logging

logger = logging.getLogger(__name__)

InvokeFn = Callable[[str], Awaitable[str]]

TemplateVariant = Literal["completa", "com_hitl", "inviabilidade"]

# Sprint 6.1 Story TD-SP06.1-QWEN-FALLBACK-WIRING (Smith F-γ-03):
# Fallback chain real per tier — ADR-022 D1 + ADR-010 Sabia Q4 mitigation honesty.
# lean: degraded mode sem fallback (qwen2.5:3b only).
# balanced (DEFAULT): qwen2.5:7b primary → sabia-7b-instruct fallback.
# premium: sabia-7b-instruct primary → qwen2.5:7b fallback.
FALLBACK_MAP: dict[LLMTier, str | None] = {
    "lean": None,
    "balanced": "sabia-7b-instruct",
    "premium": "qwen2.5:7b",
}


class PecaHallucinationError(Exception):
    """Raised quando peça contém citação fora do vault (Layer 2 anti-hallucination)."""


PROMPT_REDATOR_PECA = """\
Você é advogado bancarista brasileiro com 20 anos de experiência em revisional CDC veículos.

REGRAS INEGOCIÁVEIS (anti-hallucination):
1. Cite APENAS Súmulas/Temas STJ presentes em JURISPRUDENCIA_VAULT abaixo.
2. NUNCA invente Súmulas inexistentes (alucinação = rejeição automática).
3. Estruture a peça em 8 seções CFOAB (Provimento 209/2021 OAB).
4. Linguagem técnica formal brasileira (3ª pessoa).
5. Valor causa: numerado (R$ X.XXX,XX formato BR) E por extenso.
6. Disclaimer LGPD/OAB obrigatório no fecho.

CONTRATO ANALISADO:
- Modalidade: {modalidade}
- UF: {uf}
- Data assinatura: {data_assinatura}
- Valor financiado: R$ {valor_financiado}
- Taxa contratual a.m.: {taxa_am}%
- Parcelas: {n_parcelas}

CÁLCULO PERITO:
- PMT composto: R$ {pmt_composto}
- PMT simples: R$ {pmt_simples}
- Diferença anatocismo: R$ {diferenca}
- Classificação: {classificacao}

ANÁLISE MACRO ECONOMISTA:
- Ciclo Selic: {ciclo_selic}
- Taxa atípica vs pares: {taxa_atipica}
- Contexto: {contexto_macro}

TESE ADVOGADO LLM:
{tese_principal}

VEREDITO JUIZ:
- Aderência: {aderencia}%
- Veredito: {veredito_tipo}
- Razões: {razoes}

JURISPRUDENCIA_VAULT (cite APENAS estas — id_doc obrigatório):
{docs_disponiveis}

INSTRUÇÕES FINAIS:
{instrucoes_variante}

OUTPUT: JSON estrito conforme schema {schema_name} (extra="forbid").
Schema esperado:
{schema_skeleton}
"""

SCHEMA_SKELETON_PECA = """\
{
  "cabecalho": "Excelentíssimo Senhor Juiz de Direito da... (min 50 chars)",
  "qualificacao_partes": "Autor: {nome}, brasileiro... Ré: Banco X... (min 100 chars)",
  "dos_fatos": "Em {data}, o autor celebrou contrato... (min 200 chars)",
  "do_direito": "Aplicam-se ao caso as Súmulas STJ X, Y... (min 300 chars com citações vault)",
  "do_pedido": "Diante do exposto, requer-se: a) ... b) ... (min 100 chars)",
  "valor_causa": "R$ 5.107,00",
  "valor_causa_extenso": "cinco mil cento e sete reais",
  "fecho": "Termos em que pede deferimento. {cidade}, {data}. {advogado} OAB/XX 00000 (min 50 chars)",
  "disclaimer_lgpd_oab": "Insumo técnico-jurídico... LGPD §11 §46... OAB Provimento 209/2021... não substitui responsabilidade (min 200 chars)",
  "citacoes_jurisprudencia": ["STJ-S539", "STJ-S472"],
  "pontos_atencao": null
}
"""

SCHEMA_SKELETON_INVIABILIDADE = """\
{
  "cabecalho": "Relatório de Inviabilidade Revisional — Contrato {hash} (min 30 chars)",
  "sintese_analise": "A análise concluiu pela inviabilidade da ação revisional... (min 100 chars)",
  "diagnostico_tecnico": "Scores C1={c1}, C2={c2}, C3={c3}, aderência={ad}%... (min 200 chars)",
  "motivos_rejeicao": ["Taxa BACEN coerente com mercado", "Ausência de Súmulas aplicáveis", ...],
  "recomendacao": "Recomenda-se NÃO protocolar a presente ação... (min 100 chars)",
  "disclaimer_lgpd_oab": "Insumo técnico-jurídico... LGPD §11... OAB 209/2021 (min 200 chars)"
}
"""

INSTRUCOES_COMPLETA = (
    "Gere peça revisional COMPLETA. Veredito APROVADO_100 indica fortes fundamentos. "
    "Estruture com fundamentação robusta em todas as 8 seções CFOAB."
)
INSTRUCOES_COM_HITL = (
    "Gere peça revisional COM seção 'Pontos de Atenção' embedada. Veredito APROVADO_COM_RISCO_HITL "
    "indica fundamentos presentes mas com riscos (aderência 70-99%). Liste no campo 'pontos_atencao' "
    "os riscos do veredito.razoes para revisão humana pré-protocolo."
)
INSTRUCOES_INVIABILIDADE = (
    "Gere RELATÓRIO DE INVIABILIDADE (NÃO petição). Veredito REJEITADO indica aderência <70%. "
    "Estruture como análise técnica explicando objetivamente por que a ação revisional NÃO deve "
    "ser protocolada. Recomendação: não protocolar / buscar outros fundamentos."
)


def _build_prompt(
    veredito: VeredictoJuiz,
    contrato_meta: ContratoMetadata,
    calculo: ResultadoCalculo,
    tese: TeseAdvogado,
    analise: AnaliseMacroEconomica,
    docs: list[JurisprudenciaItem],
    template_variant: TemplateVariant,
) -> str:
    """Build prompt Redator com contexto completo do pipeline."""
    docs_disponiveis = "\n".join(
        f"- {d.id_doc} ({d.court_id}): {d.ementa[:120]}..." for d in docs
    ) or "[nenhum]"

    if template_variant == "inviabilidade":
        schema_name = "RelatorioInviabilidade"
        schema_skeleton = SCHEMA_SKELETON_INVIABILIDADE
        instrucoes_variante = INSTRUCOES_INVIABILIDADE
    elif template_variant == "com_hitl":
        schema_name = "PecaRevisional"
        schema_skeleton = SCHEMA_SKELETON_PECA
        instrucoes_variante = INSTRUCOES_COM_HITL
    else:
        schema_name = "PecaRevisional"
        schema_skeleton = SCHEMA_SKELETON_PECA
        instrucoes_variante = INSTRUCOES_COMPLETA

    return PROMPT_REDATOR_PECA.format(
        modalidade=contrato_meta.modalidade,
        uf=contrato_meta.uf_contrato,
        data_assinatura=contrato_meta.data_assinatura.isoformat(),
        valor_financiado=contrato_meta.valor_financiado or "[NÃO INFORMADO]",
        taxa_am=contrato_meta.taxa_contratual_am or "[NÃO INFORMADA]",
        n_parcelas=contrato_meta.n_parcelas or "[NÃO INFORMADO]",
        pmt_composto=calculo.pmt_composto,
        pmt_simples=calculo.pmt_simples,
        diferenca=calculo.diferenca_anatocismo,
        classificacao=calculo.classificacao_anatocismo,
        ciclo_selic=analise.ciclo_selic_periodo,
        taxa_atipica=analise.taxa_atipica_bool,
        contexto_macro=analise.contexto_macro_resumido[:300],
        tese_principal=tese.tese_principal[:500],
        aderencia=veredito.aderencia,
        veredito_tipo=veredito.veredito,
        razoes=" | ".join(veredito.razoes) or "[não detalhadas]",
        docs_disponiveis=docs_disponiveis,
        instrucoes_variante=instrucoes_variante,
        schema_name=schema_name,
        schema_skeleton=schema_skeleton,
    )


# Sprint 6.1 TD-SP06.1-LAYER-3-NLI-VALIDATOR (Smith F-γ-04 + ADR-022 D2 patch):
# NLIValidatorFn signature — recebe (citacao_textual, ementa_real) retorna ValidacaoSemantica.
# Default real implementation (sentence-transformers + BERT NLI) fica Sprint 7+ TD-SP07-NLI-HYBRID-REAL.
NLIValidatorFn = Callable[[str, str], Awaitable[ValidacaoSemantica]]


async def validar_citacoes_nli(
    peca: PecaRevisional,
    vault_docs: list[JurisprudenciaItem],
    *,
    nli_validator_fn: NLIValidatorFn | None = None,
) -> list[ValidacaoSemantica]:
    """Layer 3 anti-hallucination — NLI semantic validation citações textuais.

    Para cada fundamentos_invocados[].citacao_textual em PecaRevisional, executa
    NLI híbrido (cosine + BERT NLI) contra ementa real Súmula vault para detectar
    interpretação invertida.

    Distinção vs Layer 2:
    - Layer 2 (validar_citacoes_vault) captura "Súmula 999 não existe no vault" (ID fantasma)
    - Layer 3 (this function) captura "Súmula 539 existe mas peça afirma o oposto" (semantic)

    Args:
        peca: PecaRevisional com fundamentos_invocados (opt-in Bloco γ schema extension Sprint 6.1).
        vault_docs: jurisprudência do vault para lookup ementa real por id_doc.
        nli_validator_fn: dependency injection. None default raises NotImplementedError
            (real implementation cabe Sprint 7+ TD-SP07-NLI-HYBRID-REAL).

    Returns:
        list[ValidacaoSemantica] com NLI label para cada citação.
        Empty list se peca.fundamentos_invocados is None (Layer 3 skipped — Bloco γ retrocompat).

    Raises:
        PecaHallucinationError se algum nli_label == "contradiction" (interpretação invertida).
        NotImplementedError se nli_validator_fn is None (Sprint 7+ TD).
    """
    if peca.fundamentos_invocados is None:
        # Layer 3 opt-in — Bloco γ originals (sem fundamentos_invocados field) skipped
        return []

    if nli_validator_fn is None:
        raise NotImplementedError(
            "Sprint 6.1 MVP scope: real NLI validator (sentence-transformers + BERT) fica "
            "TD-SP07-NLI-HYBRID-REAL Sprint 7+. Pass nli_validator_fn explicit (mock OR real)."
        )

    vault_lookup = {d.id_doc: d for d in vault_docs}
    validations: list[ValidacaoSemantica] = []
    fantasmas_semanticos: list[str] = []

    for fundamento in peca.fundamentos_invocados:
        vault_doc = vault_lookup.get(fundamento.id_doc)
        if vault_doc is None:
            # Layer 2 já captura este caso — Layer 3 defensive skip
            continue
        validacao = await nli_validator_fn(
            fundamento.citacao_textual,
            vault_doc.ementa,
        )
        validations.append(validacao)
        if validacao.nli_label == "contradiction":
            fantasmas_semanticos.append(
                f"id_doc={fundamento.id_doc} citacao='{fundamento.citacao_textual[:80]}...' "
                f"reason='{validacao.razao}'"
            )

    if fantasmas_semanticos:
        raise PecaHallucinationError(
            f"Layer 3 NLI bloqueou interpretação invertida: {'; '.join(fantasmas_semanticos)}. "
            f"FR-PECA-05 traceability semantic — peça REJEITADA."
        )

    return validations


def validar_citacoes_vault(
    peca: PecaRevisional,
    vault_doc_ids: list[str],
) -> None:
    """Layer 2 anti-hallucination — bloqueia citações fora do vault.

    Args:
        peca: PecaRevisional gerada pelo LLM (com citacoes_jurisprudencia).
        vault_doc_ids: lista de IDs disponíveis no vault da execução.

    Raises:
        PecaHallucinationError se alguma citação não está no vault.
    """
    cited = set(peca.citacoes_jurisprudencia)
    available = set(vault_doc_ids)
    fantasmas = cited - available
    if fantasmas:
        raise PecaHallucinationError(
            f"Citações fora do vault detectadas: {sorted(fantasmas)}. "
            f"Vault disponível: {sorted(available)}. "
            f"FR-PECA-05 traceability — peça REJEITADA."
        )


async def _default_invoke(prompt: str, tier: LLMTier) -> tuple[str, str]:
    """Default invoke via ChatOllama com fallback chain (Sprint 6.1 F-γ-03 fix).

    Returns:
        (content_str, actual_model_used) — actual_model_used captura primary OR fallback model name.
        Forense pós-incident pode identificar modelo ACTUAL via audit chain.

    Raises:
        Exception original do primary se fallback_model is None (lean degraded mode)
        OR se fallback_model também falha (cascading failure).
    """
    primary_model = TIER_TO_MODEL_ADVOGADO[tier]
    fallback_model = FALLBACK_MAP.get(tier)

    try:
        llm = get_advogado_llm(tier=tier)
        response = await llm.ainvoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join(str(c) for c in content)
        return str(content), primary_model
    except Exception as exc:  # noqa: BLE001 — fallback é por design
        if fallback_model is None:
            # lean degraded mode — sem fallback configurado
            logger.warning(
                "Redator tier=%s primary %s falhou: %s — sem fallback (lean degraded)",
                tier, primary_model, exc,
            )
            raise

        logger.warning(
            "Redator tier=%s primary %s falhou: %s — tentando fallback %s",
            tier, primary_model, exc, fallback_model,
        )
        from langchain_ollama import ChatOllama  # type: ignore[import-not-found]
        fallback_llm = ChatOllama(
            model=fallback_model,
            base_url=DEFAULT_HOST_ADVOGADO,
            temperature=0.2,
            timeout=120.0,
            format="json",
        )
        response = await fallback_llm.ainvoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join(str(c) for c in content)
        return str(content), fallback_model


async def redator_invoke(
    veredito: VeredictoJuiz,
    contrato_meta: ContratoMetadata,
    calculo: ResultadoCalculo,
    tese: TeseAdvogado,
    analise: AnaliseMacroEconomica,
    docs: list[JurisprudenciaItem],
    *,
    tier: LLMTier = "balanced",
    template_variant: TemplateVariant | None = None,
    invoke_fn: InvokeFn | None = None,
    model_capture: dict[str, Any] | None = None,
    enable_layer_3: bool = False,
    nli_validator_fn: NLIValidatorFn | None = None,
) -> PecaRevisional | RelatorioInviabilidade:
    """Invoca Redator LLM — gera peça revisional ou relatório de inviabilidade.

    Args:
        veredito: output do Juiz Python (FR-PECA-07 filter).
        contrato_meta: metadata do contrato analisado.
        calculo: output do Perito (PMT composto + diferença).
        tese: output do Advogado LLM (já validada Pydantic).
        analise: output do Economista LLM (contexto macro).
        docs: jurisprudência do vault (anti-hallucination ground truth).
        tier: lean/balanced/premium (ADR-022 D1).
        template_variant: completa/com_hitl/inviabilidade. Se None, derivado do veredito.
        invoke_fn: dependency injection para testes (recebe prompt, retorna JSON str).
        model_capture: dict opt-in (Sprint 6.1 F-γ-03) — preenchido com `actual_model_used`
            para audit chain forense post-incident saber qual LLM gerou a peça (primary OR fallback).
            Default `tier` mapped quando invoke_fn provided OR primary used.

    Returns:
        PecaRevisional para veredictos APROVADO_*, RelatorioInviabilidade para REJEITADO.

    Raises:
        PecaHallucinationError se peça cita Súmulas fora do vault (Layer 2).
        ValidationError se LLM retorna JSON malformado (Layer 1 Pydantic).
    """
    # FR-PECA-07 filter: veredito → template_variant
    if template_variant is None:
        if veredito.veredito == "APROVADO_100":
            template_variant = "completa"
        elif veredito.veredito == "APROVADO_COM_RISCO_HITL":
            template_variant = "com_hitl"
        else:  # REJEITADO
            template_variant = "inviabilidade"

    prompt = _build_prompt(
        veredito, contrato_meta, calculo, tese, analise, docs, template_variant
    )

    if invoke_fn is None:
        json_str, actual_model_used = await _default_invoke(prompt, tier)
    else:
        json_str = await invoke_fn(prompt)
        # invoke_fn é mock/test injection — actual_model é o primary tier mapped
        actual_model_used = TIER_TO_MODEL_ADVOGADO[tier]

    # Propagar actual_model_used para audit chain (F-γ-03 + F-γ-02 honesty)
    if model_capture is not None:
        model_capture["actual_model_used"] = actual_model_used

    # Layer 1 anti-hallucination — Pydantic strict validation
    if template_variant == "inviabilidade":
        return RelatorioInviabilidade.model_validate_json(json_str)
    else:
        peca = PecaRevisional.model_validate_json(json_str)
        # Layer 2 anti-hallucination — vault-restricted citations (id_doc)
        validar_citacoes_vault(peca, [d.id_doc for d in docs])
        # Layer 3 anti-hallucination — NLI semantic validation (Sprint 6.1 opt-in)
        if enable_layer_3:
            await validar_citacoes_nli(peca, docs, nli_validator_fn=nli_validator_fn)
        return peca
