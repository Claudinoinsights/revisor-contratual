"""Advogado — gera TeseAdvogado via LLM Sabia (FR-TESE-01).

Decisão arquitetural (D-MOR-3.3-B): invoke_fn injetável → testes 100% mockados.
Anti-fantasma sintático já validado em bloco_contratos.TeseAdvogado.field_validator.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from bloco_contratos.contrato import ContratoMetadata, ResultadoCalculo
from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_contratos.personas import LLMTier, TeseAdvogado
from bloco_workflow.personas.llm_factory import get_advogado_llm

# invoke_fn(prompt) -> JSON string (resposta do LLM)
InvokeFn = Callable[[str], Awaitable[str]]


PROMPT_TEMPLATE_ADVOGADO = """\
Você é um advogado especialista em direito bancário brasileiro. Gere uma tese revisional para o contrato abaixo.

CONTRATO:
- UF: {uf}
- Data assinatura: {data_assinatura}
- Modalidade: {modalidade}
- Valor financiado: {valor}
- Taxa contratual a.m.: {taxa_am}
- Parcelas: {n_parcelas}

CÁLCULO PERITO:
- PMT composto: R$ {pmt_composto}
- PMT simples: R$ {pmt_simples}
- Diferença anatocismo: R$ {diferenca}
- Classificação: {classificacao}
- Súmulas aplicáveis: {sumulas}

DOCUMENTOS DISPONÍVEIS NO VAULT (top-K):
{docs_disponiveis}

INSTRUÇÕES OBRIGATÓRIAS:
1. Cite APENAS docs da lista acima (anti-fantasma — qualquer citação fora será REJEITADA).
2. Atribua peso_vinculacao 1-5 conforme jurisprudência (5=súmula vinculante STF, 4=súmula STJ, 3=tema repetitivo, 2=jurisprudência dominante, 1=acórdão isolado).
3. Retorne APENAS JSON válido conforme schema TeseAdvogado.

Schema esperado:
{{
  "tese_principal": "string >=50 chars",
  "fundamentos_invocados": [
    {{"id_doc": "STJ-S539", "citacao_textual": "...", "peso_vinculacao": 4, "court_id": "STJ"}}
  ],
  "docs_consultados_ids": ["STJ-S539", ...],
  "docs_efetivamente_citados_ids": ["STJ-S539", ...],
  "confianca": 0.0-1.0
}}
"""


def _build_prompt(
    calculo: ResultadoCalculo,
    docs: list[JurisprudenciaItem],
    contrato_meta: ContratoMetadata,
) -> str:
    docs_disponiveis = "\n".join(
        f"- {d.id_doc} ({d.court_id}): {d.ementa[:120]}..." for d in docs
    )
    return PROMPT_TEMPLATE_ADVOGADO.format(
        uf=contrato_meta.uf_contrato,
        data_assinatura=contrato_meta.data_assinatura.isoformat(),
        modalidade=contrato_meta.modalidade,
        valor=contrato_meta.valor_financiado or "[NÃO INFORMADO]",
        taxa_am=contrato_meta.taxa_contratual_am or "[NÃO INFORMADA]",
        n_parcelas=contrato_meta.n_parcelas or "[NÃO INFORMADO]",
        pmt_composto=calculo.pmt_composto,
        pmt_simples=calculo.pmt_simples,
        diferenca=calculo.diferenca_anatocismo,
        classificacao=calculo.classificacao_anatocismo,
        sumulas=", ".join(calculo.sumulas_aplicaveis) or "[nenhuma]",
        docs_disponiveis=docs_disponiveis or "[nenhum]",
    )


async def _default_invoke(prompt: str, tier: LLMTier) -> str:
    """Default invoke usando ChatOllama real (não chamado em testes)."""
    llm = get_advogado_llm(tier=tier)
    response = await llm.ainvoke(prompt)
    # ChatOllama retorna AIMessage; .content pode ser str ou list
    content = response.content
    if isinstance(content, list):
        content = "".join(str(c) for c in content)
    return str(content)


async def advogado_redigir_tese_async(
    calculo: ResultadoCalculo,
    docs: list[JurisprudenciaItem],
    contrato_meta: ContratoMetadata,
    tier: LLMTier = "premium",
    *,
    invoke_fn: InvokeFn | None = None,
) -> TeseAdvogado:
    """Gera TeseAdvogado via LLM Sabia (FR-TESE-01).

    Args:
        calculo: output Perito (R$ + classificação anatocismo)
        docs: jurisprudência top-K do vault (anti-fantasma — LLM só pode citar destes)
        contrato_meta: metadata do contrato
        tier: lean/balanced/premium (FR-TESE-02)
        invoke_fn: injetável para testes — recebe prompt, devolve JSON string

    Returns:
        TeseAdvogado validado por Pydantic (anti-fantasma sintático hard-fail).

    Raises:
        ValidationError se LLM cita doc fora do top-K ou JSON malformado.
    """
    prompt = _build_prompt(calculo, docs, contrato_meta)
    if invoke_fn is None:
        json_str = await _default_invoke(prompt, tier)
    else:
        json_str = await invoke_fn(prompt)
    return TeseAdvogado.model_validate_json(json_str)
