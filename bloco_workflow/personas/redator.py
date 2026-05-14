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
    VeredictoJuiz,
)
from bloco_workflow.personas.llm_factory import get_advogado_llm

InvokeFn = Callable[[str], Awaitable[str]]

TemplateVariant = Literal["completa", "com_hitl", "inviabilidade"]


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


async def _default_invoke(prompt: str, tier: LLMTier) -> str:
    """Default invoke via ChatOllama (não chamado em testes)."""
    llm = get_advogado_llm(tier=tier)
    response = await llm.ainvoke(prompt)
    content = response.content
    if isinstance(content, list):
        content = "".join(str(c) for c in content)
    return str(content)


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
        json_str = await _default_invoke(prompt, tier)
    else:
        json_str = await invoke_fn(prompt)

    # Layer 1 anti-hallucination — Pydantic strict validation
    if template_variant == "inviabilidade":
        return RelatorioInviabilidade.model_validate_json(json_str)
    else:
        peca = PecaRevisional.model_validate_json(json_str)
        # Layer 2 anti-hallucination — vault-restricted citations
        validar_citacoes_vault(peca, [d.id_doc for d in docs])
        return peca
