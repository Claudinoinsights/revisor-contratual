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
    MODEL_ECONOMISTA as MODEL_ECONOMISTA_REDATOR,
    TIER_TO_MODEL_ADVOGADO,
    TIER_TO_MODEL_REDATOR,
    get_advogado_llm,  # ADR-025 mantém import para test_no_cascade spy + future Sprint 7+
    get_economista_llm,
)

import json
import logging
import warnings

logger = logging.getLogger(__name__)

InvokeFn = Callable[[str], Awaitable[str]]

TemplateVariant = Literal["completa", "com_hitl", "inviabilidade"]

# Sprint 6.1 Story TD-SP06.1-QWEN-FALLBACK-WIRING (Smith F-γ-03):
# Fallback chain per tier — ADR-022 D1 + ADR-010 Sabia Q4 mitigation honesty.
# lean: degraded mode sem fallback (qwen2.5:3b only).
# balanced (DEFAULT): qwen2.5:7b primary → sabia-7b-instruct fallback.
# premium: sabia-7b-instruct primary → qwen2.5:7b fallback.
#
# DEPRECATED em D-DEV-S06-021 (F-PROD-NEW-19 fix):
#   `_default_invoke` agora roteia primary=qwen2.5:3b (economista host) + fallback=qwen2.5:7b
#   (advogado host) independente de tier. FALLBACK_MAP retido apenas para backward-compat de
#   imports externos + audit forense histórico. Removal scheduled via TD-SP07-FALLBACK-MAP-REMOVAL
#   (governance/TECH-DEBT.md) — depende de Sprint 7+ tier-strategy decision (Eric + Aria).
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

REGRA CRÍTICA citações vault (D-DEV-S08-011 — Layer 2 anti-hallucination):
- Cite EXCLUSIVAMENTE ids_doc presentes em JURISPRUDENCIA_VAULT acima.
- IGNORE quaisquer IDs específicos nos exemplos do Schema abaixo (são apenas FORMATO ilustrativo).
- Citacoes_jurisprudencia DEVE conter APENAS strings que existem em JURISPRUDENCIA_VAULT.
- Citar IDs fora do vault = REJEIÇÃO AUTOMÁTICA Layer 2 (FR-PECA-05).
- Se vault está vazio, deixe citacoes_jurisprudencia=[] e do_direito sem IDs específicos.

REGRA CRÍTICA min_length (D-DEV-S08-009 — Pydantic hard-fail se violar):
- cabecalho: MÍNIMO 50 caracteres — Excelentíssimo + Juízo + Comarca + Vara completos
- qualificacao_partes: MÍNIMO 100 caracteres — Autor (qualificação completa) + Ré (banco + CNPJ + endereço)
- dos_fatos: MÍNIMO 200 caracteres — Narrativa cronológica DETALHADA do contrato (data, valor, parcelas, taxa, contexto)
- do_direito: MÍNIMO 300 caracteres — Fundamentação jurídica com Súmulas vault + dispositivos legais
- do_pedido: MÍNIMO 100 caracteres — Pedidos formais enumerados (a, b, c) com requisitos específicos
- fecho: MÍNIMO 50 caracteres — Termos + cidade + data + assinatura placeholder
- disclaimer_lgpd_oab: MÍNIMO 200 caracteres — Disclaimer COMPLETO LGPD §11/§46 + OAB Provimento 209/2021
- valor_causa_extenso: MÍNIMO 10 caracteres — valor por extenso completo (ex: cinco mil reais)

NUNCA use placeholders genéricos como "(min X chars)", "..." OR "[texto]" — sempre escreva texto LITERAL completo.

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
  "cabecalho": "Excelentíssimo Senhor Doutor Juiz de Direito da Vara Cível da Comarca de São Paulo/SP",
  "qualificacao_partes": "AUTOR: João da Silva, brasileiro, casado, portador do RG nº 12.345.678-9 SSP/SP, inscrito no CPF nº 123.456.789-00, residente e domiciliado na Rua Exemplo, nº 100, São Paulo/SP. RÉ: Banco Exemplo S.A., pessoa jurídica de direito privado, CNPJ nº 12.345.678/0001-90, com sede na Av. Paulista, 1000, São Paulo/SP.",
  "dos_fatos": "Em 15 de maio de 2025, o autor celebrou com a ré contrato de financiamento de veículo (CDC) no valor de R$ 35.000,00, parcelado em 48 prestações mensais consecutivas, com taxa de juros declarada de 1,89% ao mês. O contrato apresenta cláusulas que ensejam revisão judicial, notadamente quanto à capitalização mensal de juros, comissão de permanência e tarifas administrativas cobradas sem previsão legal expressa, conforme entendimento pacificado pelo Superior Tribunal de Justiça.",
  "do_direito": "Aplicam-se ao caso as Súmulas e Temas Repetitivos indicados em JURISPRUDENCIA_VAULT acima, que disciplinam a capitalização mensal de juros nos contratos bancários celebrados após 31/03/2000 (MP 1.963-17), exigindo pactuação expressa. O Código de Defesa do Consumidor (Lei 8.078/90) incide na relação contratual, impondo nulidade às cláusulas abusivas (art. 51, IV). A jurisprudência consolidada do STJ veda a cobrança cumulativa de comissão de permanência com outros encargos moratórios, conforme entendimento sedimentado em sede de recursos repetitivos disponíveis no vault.",
  "do_pedido": "Diante do exposto, requer-se: a) a citação da ré para responder aos termos da presente ação; b) a inversão do ônus da prova com fundamento no art. 6º, VIII, do CDC; c) ao final, a procedência total da demanda para revisar o contrato em comento, declarando-se a nulidade das cláusulas abusivas identificadas e condenando-se a ré à restituição em dobro dos valores cobrados indevidamente (art. 42, parágrafo único, CDC).",
  "valor_causa": "R$ 5.107,00",
  "valor_causa_extenso": "cinco mil cento e sete reais",
  "fecho": "Termos em que pede deferimento. São Paulo, 15 de maio de 2025. Advogado Exemplo OAB/SP nº 000.000",
  "disclaimer_lgpd_oab": "Este documento constitui insumo técnico-jurídico gerado por sistema de apoio à decisão jurídica, em conformidade com a Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018, art. 11 §1º e art. 46) e o Provimento 209/2021 da OAB que regulamenta o uso de inteligência artificial na advocacia. O conteúdo aqui apresentado NÃO substitui o juízo crítico, a análise técnica e a responsabilidade profissional do advogado subscritor.",
  "citacoes_jurisprudencia": ["<copie ids_doc do JURISPRUDENCIA_VAULT acima>"],
  "pontos_atencao": null
}
"""

SCHEMA_SKELETON_INVIABILIDADE = """\
{
  "cabecalho": "Relatório de Inviabilidade Revisional — Contrato CDC Veículos 991fd186 — Análise Técnica",
  "sintese_analise": "A análise técnica do contrato em comento concluiu pela INVIABILIDADE da propositura de ação revisional, em razão da ausência de fundamentos jurídicos suficientes para sustentar a tese de abusividade, conforme detalhamento técnico apresentado nas seções subsequentes.",
  "diagnostico_tecnico": "Os scores objetivos calculados pelo Juiz Revisor indicam: C1 (divergência BACEN) = 0.30 (taxa contratual dentro da banda de mercado), C2 (peso vinculação jurisprudencial) = 0.50 (Súmulas aplicáveis com peso médio), C3 (aderência jurisdicional) = 0.40 (jurisprudência local não favorável), resultando em aderência consolidada de 40%, abaixo do threshold de 70% exigido para viabilidade da ação revisional conforme protocolo interno.",
  "motivos_rejeicao": ["Taxa contratual BACEN compatível com a média de mercado vigente à época da contratação", "Súmulas STJ aplicáveis possuem peso vinculação insuficiente para o caso concreto", "Jurisprudência da jurisdição de domicílio do autor não é majoritariamente favorável à tese revisional"],
  "recomendacao": "Recomenda-se ENFATICAMENTE a NÃO propositura da presente ação revisional, sob risco de improcedência e eventual condenação em honorários de sucumbência. Sugere-se ao patrono buscar outros fundamentos jurídicos ou orientar o cliente quanto à inviabilidade técnica da pretensão.",
  "disclaimer_lgpd_oab": "Este documento constitui insumo técnico-jurídico gerado por sistema de apoio à decisão jurídica, em conformidade com a Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018, art. 11 §1º e art. 46) e o Provimento 209/2021 da OAB que regulamenta o uso de inteligência artificial na advocacia. O conteúdo aqui apresentado NÃO substitui o juízo crítico, a análise técnica e a responsabilidade profissional do advogado subscritor."
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


def _build_degraded_synthetic_response(reason: str) -> str:
    """Constrói RelatorioInviabilidade synthetic Pydantic-valid (ADR-025 graceful degradation).

    Sprint 6.x ADR-025 (D-ARIA-S06-025 + D-DEV-S06-026): quando primary economista do
    Redator falhar em `_default_invoke`, retornar este synthetic JSON em vez de retry
    com qwen2.5:7b (F-PROD-NEW-19 cascade source). Pipeline atomicity preserved + UX
    honest + LGPD audit trail completo via `audit_marker` rastreável.

    Args:
        reason: motivo da degradação (string da exception). Truncado para 200 chars
                em fields visíveis para evitar audit chain bloat — full reason em logger.

    Returns:
        JSON string Pydantic-valid contra RelatorioInviabilidade schema (extra="forbid").
        Todos fields obedecem min_length constraints + model_validate_json passa sem erro.
    """
    reason_safe = reason[:200] if reason else "unknown"
    payload = {
        "cabecalho": (
            "Relatório de Degradação Operacional — Sistema temporariamente "
            "indisponível para geração de peça revisional formal"
        ),
        "sintese_analise": (
            "Sistema temporariamente indisponível para gerar peça revisional formal. "
            "Análise técnica completa (parsing + cálculo + BACEN + jurisprudência + "
            "tese Advogado + análise Economista + veredito Juiz) foi PRESERVADA em "
            "audit chain. Apenas a geração de peça revisional formal foi adiada por "
            "falha transitiva no LLM Redator (ADR-025 graceful degradation)."
        ),
        "diagnostico_tecnico": (
            f"Falha transitiva no LLM Redator (motivo registrado: {reason_safe}). "
            "ADR-025 graceful degradation: pipeline NÃO falha cataclismicamente, "
            "preserva atomicidade Steps 1-6 e retorna este relatório honesto em vez "
            "de tentar fallback com qwen2.5:7b (modelo que crashou produção 2026-05-15 "
            "F-PROD-NEW-19). Análise jurídica + econômica + veredito Juiz disponíveis "
            "em audit chain para investigação manual ou re-submissão. Audit marker: "
            "ADR-025-degraded-synthetic. Probabilidade falha transitiva (network blip "
            "/ memory pressure intra-container): alta. Probabilidade falha estrutural "
            "(OOM persistente / cascade Steps 5-6): baixa — Steps anteriores passaram."
        ),
        "motivos_rejeicao": [
            f"Redator LLM economista (qwen2.5:3b) indisponível: {reason_safe}",
            (
                "Cascade fallback eliminado (ADR-025) — evita re-invocação qwen2.5:7b "
                "problemático que crashou produção em F-PROD-NEW-19"
            ),
            (
                "Pipeline atomicity preserved — Steps 1-6 audit registrados normalmente; "
                "apenas Step 7 (Redator) entrou em modo degraded synthetic"
            ),
        ],
        "recomendacao": (
            "Re-submeter PDF após 2-5 minutos (provável falha transitiva, ADR-025 "
            "assume blip). Se persistir após 3 tentativas, contatar suporte informando "
            "job_id do sistema para investigação. Alternativa: solicitar análise manual "
            "baseada no veredito Juiz + tese Advogado disponíveis em audit chain — "
            "análise técnica completa preservada, apenas peça revisional formal adiada."
        ),
        "disclaimer_lgpd_oab": (
            "Este relatório é insumo técnico-operacional gerado automaticamente em modo "
            "de degradação graciosa (ADR-025 Caminho A — Graceful Degradation Synthetic). "
            "LGPD §11 §46 — dados pessoais processados localmente sem retenção indevida; "
            "audit chain registra evento completo via marker 'ADR-025-degraded-synthetic'. "
            "OAB Provimento 209/2021 — não substitui responsabilidade profissional do "
            "advogado. Conforme arquitetura ADR-025, o sistema escolhe honestamente "
            "informar indisponibilidade transitiva em vez de gerar peça sob memory "
            f"pressure que poderia comprometer qualidade jurídica. Reason: {reason_safe[:100]}."
        ),
    }
    # Smith F-S28-08 MEDIUM fix (D-DEV-S06-029): synthetic gera UTF-8 string (ensure_ascii=False
    # preserva caracteres unicode em reason). Consumers DEVEM `open(path, "w", encoding="utf-8")`
    # se escreverem em arquivo — Windows cp1252 default raise UnicodeEncodeError. Audit chain
    # HMAC write usa bytes diretos via json.dumps(...).encode("utf-8") — sem issue. Log files
    # Windows: usar encoding explicit OU substituir caracteres unicode antes do write.
    return json.dumps(payload, ensure_ascii=False)


async def _default_invoke(prompt: str, tier: LLMTier) -> tuple[str, str]:
    """Default invoke — tier audit-honored + graceful degradation (ADR-024 + ADR-025).

    Sprint 6.x evolution chain:
      D-DEV-S06-021 (F-PROD-NEW-19): tier-down qwen2.5:7b → qwen2.5:3b primary
      D-DEV-S06-023 (S21 fixes): DeprecationWarning band-aid + audit integrity
      D-ARIA-S06-025 (ADRs): formalização band-aids em decisões arquiteturais
      D-DEV-S06-026 (THIS): implementação ADR-024 + ADR-025

    ADR-024 Audit-Honored Tier (Caminho C):
        Parâmetro `tier` preservado para backward-compat E como AUDIT INTENT capture.
        Selection logic usa `TIER_TO_MODEL_REDATOR[tier]` (currently all-3b mapping —
        Sprint 7+ pode promover via map mutation sem refactor). DeprecationWarning
        runtime sinaliza API surface ambiguity para tier != "balanced".

    ADR-025 Graceful Degradation Synthetic (Caminho A):
        Se primary economista falhar, retornar `RelatorioInviabilidade` synthetic
        Pydantic-valid via `_build_degraded_synthetic_response(reason)` em vez de
        cascade fallback qwen2.5:7b (F-PROD-NEW-19 root cause eliminado).
        Pipeline atomicity preserved + UX honest + LGPD audit trail completo.

    Trade-off: Redator tier nominal "balanced" agora roda em qwen2.5:3b. Qualidade
    peça revisional pode degradar marginalmente vs 7b — mas pipeline COMPLETO funcional
    > peça premium teórica nunca entregue. Sprint 7+ reconsiderar quando VPS escalada.

    Args:
        prompt: prompt completo (PROMPT_REDATOR_PECA ou PROMPT_INVIABILIDADE).
        tier: AUDIT-HONORED — registra intent original do caller em audit chain
              (`audit_payload[redator_tier_consumed]`). Model selection via
              TIER_TO_MODEL_REDATOR[tier] (currently all-3b — ADR-024).
              Audit chain registra `actual_model_used` (real model) + `tier_consumed`
              (intent) separadamente para forense post-incident.

    Returns:
        (content_str, actual_model_used) — actual_model_used = "qwen2.5:3b" em sucesso,
        OR f"{primary_model}-degraded-synthetic" em ADR-025 graceful degradation mode.
        Synthetic mode preserva pipeline atomicity — pipeline.py detecta via suffix
        e registra `peca_format="degraded_synthetic"` + `degraded_reason` em audit.

    Raises:
        NUNCA raise em produção normal — ADR-025 graceful degradation captura
        qualquer Exception do primary economista e retorna synthetic JSON.
    """
    # ADR-024 Audit-Honored Tier (D-DEV-S06-026): tier é IGNORED para model selection
    # desde D-DEV-S06-021 F-PROD-NEW-19, mas registrado em audit_payload[redator_tier_consumed]
    # via pipeline.py. DeprecationWarning runtime alerta API consumers que tier != "balanced"
    # ainda passa silently para qwen2.5:3b. Sprint 7+ pode promover tier semantic real
    # via TIER_TO_MODEL_REDATOR map mutation (ver ADR-024 Reconsideration Triggers).
    if tier != "balanced":
        warnings.warn(
            f"Redator `tier={tier!r}` é AUDIT-HONORED desde ADR-024 (D-DEV-S06-026) — "
            f"todas as invocações usam {TIER_TO_MODEL_REDATOR[tier]} (ADR-024 audit-honored-v1). "
            f"Tier registrado em audit_payload[redator_tier_consumed] para análise forense.",
            DeprecationWarning,
            stacklevel=2,
        )

    # ADR-024 tier mapping — TIER_TO_MODEL_REDATOR documenta reality all-3b pós F-PROD-NEW-19
    primary_model = TIER_TO_MODEL_REDATOR[tier]  # qwen2.5:3b (todos tiers atualmente)

    try:
        llm = get_economista_llm()
        response = await llm.ainvoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join(str(c) for c in content)
        return str(content), primary_model
    except Exception as exc:  # noqa: BLE001 — graceful degradation é por design (ADR-025)
        # ADR-025 Caminho A — Graceful Degradation Synthetic (D-DEV-S06-026):
        # NÃO retry com qwen2.5:7b (cascade risk F-PROD-NEW-19 root cause). Retornar
        # RelatorioInviabilidade synthetic Pydantic-valid via helper module-level.
        # Pipeline atomicity preserved + UX honest + LGPD audit trail completo.
        # Logger.ERROR (não WARNING) — degraded mode é evento operacional para alerting.
        logger.error(
            "Redator ADR-025 graceful degradation — primary economista (%s) falhou: %s. "
            "Retornando synthetic RelatorioInviabilidade (degraded mode). "
            "Audit marker: ADR-025-degraded-synthetic. NÃO acionando fallback qwen2.5:7b "
            "(cascade risk F-PROD-NEW-19 eliminado).",
            primary_model, exc,
        )
        # Smith F-S28-02 MEDIUM fix (D-DEV-S06-029): propagar reason real via suffix do
        # actual_model_used para audit chain forensic distinguish (Ollama EOF vs OOM vs
        # network blip vs timeout). Reason truncado a 100 chars no suffix para evitar
        # audit chain bloat — full reason permanece em logger.ERROR acima.
        reason_safe = str(exc).replace("\n", " ").replace(":", "_")[:100]
        synthetic_json = _build_degraded_synthetic_response(reason=str(exc))
        return synthetic_json, f"{primary_model}-degraded-synthetic:{reason_safe}"


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
        # ADR-024 Audit-Honored Tier (D-DEV-S06-026): invoke_fn é mock/test injection,
        # mas o actual_model_used DEVE refletir TIER_TO_MODEL_REDATOR[tier] (mesmo mapping
        # que `_default_invoke` real usa internamente). Mantém audit chain consistente
        # entre production path (real _default_invoke) e test paths (mock injection).
        # Sprint 7+ pode promover TIER_TO_MODEL_REDATOR["premium"] = qwen2.5:7b sem
        # quebrar este test path — tier mapping fica em single source of truth.
        actual_model_used = TIER_TO_MODEL_REDATOR[tier]

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
