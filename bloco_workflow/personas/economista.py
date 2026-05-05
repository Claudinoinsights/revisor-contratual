"""Economista — gera AnaliseMacroEconomica via LLM Qwen 2.5 3B FIXO (FR-PERSONA-ECO-01).

Promovida a primeira-classe v1.0.2 (mitigação Tema 1378 STJ).

Decisão arquitetural (D-MOR-3.3-D): Qwen é FIXO (não Premium configurável como Advogado).
invoke_fn injetável → testes 100% mockados.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from bloco_contratos.contrato import BacenData, ContratoMetadata
from bloco_contratos.personas import AnaliseMacroEconomica
from bloco_workflow.personas.llm_factory import get_economista_llm

InvokeFn = Callable[[str], Awaitable[str]]


PROMPT_TEMPLATE_ECONOMISTA = """\
Você é um economista bancário. Analise o contexto macroeconômico do contrato abaixo de forma OBJETIVA e ESTRUTURADA.

CONTRATO:
- Modalidade: {modalidade}
- Data assinatura: {data_assinatura}
- Taxa contratual a.m.: {taxa_contratual_am}

DADOS BACEN (mês de referência):
- Código SGS: {codigo_sgs}
- Mês ref: {mes_ref}
- Taxa média modalidade (%): {taxa_media}
- Fonte: {fonte_url}
- Cache fallback?: {is_fallback}

TAREFA:
1. Identifique o ciclo Selic na época (alta_2022_2024 / baixa_2026 / estavel_2025 / outro_<período>).
2. Compare taxa contratual com taxa média BACEN — atípica (desvio >1.5pp) ou típica?
3. Liste comparação com 2-3 modalidades concorrentes (mesmo BACEN), com taxa_media de cada.
4. Resuma o contexto macro em 50-2000 caracteres.

Retorne APENAS JSON válido conforme schema AnaliseMacroEconomica:
{{
  "ciclo_selic_periodo": "alta_2022_2024",
  "taxa_atipica_bool": true,
  "comparacao_peer_modalities": {{"CDC_VEICULOS_PF_25471": "1,99% a.m.", "...": "..."}},
  "contexto_macro_resumido": "string entre 50 e 2000 chars"
}}
"""


def _build_prompt(contrato_meta: ContratoMetadata, bacen_data: BacenData) -> str:
    return PROMPT_TEMPLATE_ECONOMISTA.format(
        modalidade=contrato_meta.modalidade,
        data_assinatura=contrato_meta.data_assinatura.isoformat(),
        taxa_contratual_am=contrato_meta.taxa_contratual_am or "[NÃO INFORMADA]",
        codigo_sgs=bacen_data.codigo_sgs,
        mes_ref=bacen_data.mes_ref,
        taxa_media=bacen_data.taxa_media,
        fonte_url=bacen_data.fonte_url,
        is_fallback=bacen_data.is_fallback,
    )


async def _default_invoke(prompt: str) -> str:
    """Default invoke usando ChatOllama real (não chamado em testes)."""
    llm = get_economista_llm()
    response = await llm.ainvoke(prompt)
    content = response.content
    if isinstance(content, list):
        content = "".join(str(c) for c in content)
    return str(content)


async def economista_analisar_async(
    contrato_meta: ContratoMetadata,
    bacen_data: BacenData,
    *,
    invoke_fn: InvokeFn | None = None,
) -> AnaliseMacroEconomica:
    """Gera AnaliseMacroEconomica via LLM Qwen (FR-PERSONA-ECO-01).

    Args:
        contrato_meta: metadata do contrato
        bacen_data: dados BACEN para a modalidade/mes_ref
        invoke_fn: injetável para testes — recebe prompt, devolve JSON string

    Returns:
        AnaliseMacroEconomica validada por Pydantic.

    Raises:
        ValidationError se LLM devolve JSON malformado ou fora do schema.
    """
    prompt = _build_prompt(contrato_meta, bacen_data)
    if invoke_fn is None:
        json_str = await _default_invoke(prompt)
    else:
        json_str = await invoke_fn(prompt)
    return AnaliseMacroEconomica.model_validate_json(json_str)
