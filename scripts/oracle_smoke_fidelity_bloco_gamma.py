"""Oracle Wave γ.3 — Smoke Fidelity Bloco γ (TD-SP06-FIDELITY-01).

Gera 3 outputs (1 per veredito) e verifica OAB CFOAB compliance + LGPD disclaimer
+ valor causa BR + citações vault traceability + metadata.

Approach (Oracle decisão 2026-05-14):
  - Opção A + C combinadas: Jinja2 HTML standalone render (offline, sem GTK deps)
    + Pydantic strict validation + cross-reference vault simulation.
  - Opção B veredictos: 3 fixtures controlados (PecaRevisional APROVADO_100 + COM_HITL,
    RelatorioInviabilidade REJEITADO) — determinísticos, repetíveis.
  - Weasyprint render real DIFERIDO para VPS Linux deploy (TD-SP06-WEASYPRINT-WIN-GTK-DEPS).

Outputs:
  - data/test-fixtures/synthetic/peca-output-aprovado-100.html
  - data/test-fixtures/synthetic/peca-output-com-hitl.html
  - data/test-fixtures/synthetic/peca-output-rejeitado.html
  - data/test-fixtures/synthetic/peca-output-{...}.pdf (apenas se weasyprint GTK OK)
  - Scorecard impresso stdout + JSON em data/test-fixtures/synthetic/oracle-scorecard.json
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

# Force UTF-8 stdout/stderr para evitar cp1252 issues no Windows console.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bloco_contratos.contrato import ContratoMetadata  # noqa: E402
from bloco_contratos.personas import (  # noqa: E402
    PecaRevisional,
    RelatorioInviabilidade,
    VeredictoJuiz,
)
from bloco_engine.pdf.render import _build_jinja_env  # noqa: E402
from bloco_workflow.personas.redator import (  # noqa: E402
    PecaHallucinationError,
    validar_citacoes_vault,
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "test-fixtures" / "synthetic"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VAULT_DOCS_AVAILABLE = ["STJ-S539", "STJ-S472", "STJ-S297", "STF-SV4", "STJ-S381"]


def make_contrato_meta() -> ContratoMetadata:
    return ContratoMetadata(
        contract_hash="oracle" + "f" * 58,
        uf_contrato="BA",
        data_assinatura=date(2024, 3, 15),
        modalidade="CDC_VEICULOS_PF",
        valor_financiado="50000.00",
        taxa_contratual_am="1.99",
        taxa_contratual_aa="24.5",
        n_parcelas=48,
    )


def make_peca_aprovado_100() -> PecaRevisional:
    return PecaRevisional(
        cabecalho=(
            "Excelentíssimo Senhor Doutor Juiz de Direito da Vara Cível "
            "da Comarca de Salvador, Estado da Bahia."
        ),
        qualificacao_partes=(
            "AUTOR: Fulano de Tal, brasileiro, solteiro, comerciante, inscrito no CPF "
            "000.000.000-00, residente à Rua Exemplo nº 123, Salvador/BA. "
            "RÉ: Banco Exemplo S.A., instituição financeira, CNPJ 00.000.000/0001-00, "
            "com sede à Avenida Paulista nº 1000, São Paulo/SP."
        ),
        dos_fatos=(
            "Em 15 de março de 2024, o autor celebrou contrato de financiamento de "
            "veículo (CDC Veículos PF) com a ré, no valor de R$ 50.000,00, a ser pago "
            "em 48 parcelas mensais de R$ 1.300,40, à taxa contratual de 1,99% ao mês "
            "(24,5% ao ano). Constatou-se cobrança de juros capitalizados mensalmente "
            "sem pactuação expressa adequada, gerando anatocismo no valor mensal de "
            "R$ 200,40 entre o sistema composto (Tabela Price) e o sistema simples."
        ),
        do_direito=(
            "Aplica-se ao caso concreto a Súmula 539 do Superior Tribunal de Justiça, "
            "segundo a qual a capitalização de juros com periodicidade inferior a um "
            "ano em contratos celebrados com instituições integrantes do Sistema "
            "Financeiro Nacional exige pactuação expressa válida. A diferença mensal "
            "identificada de R$ 200,40 entre o sistema composto e simples configura "
            "anatocismo a ser restituído em dobro nos termos do art. 42, parágrafo "
            "único, do Código de Defesa do Consumidor. A jurisprudência consolidada "
            "do STJ ampara a presente pretensão revisional, conforme também a "
            "Súmula 472 STJ acerca da comissão de permanência limitada."
        ),
        do_pedido=(
            "Diante do exposto, requer-se a Vossa Excelência: a) a procedência "
            "total da presente ação revisional; b) a declaração de abusividade da "
            "cobrança de juros capitalizados sem pactuação expressa; c) a "
            "restituição em dobro dos valores cobrados a maior; d) a condenação da "
            "ré ao pagamento de custas processuais e honorários advocatícios em 20%."
        ),
        valor_causa="R$ 9.619,20",
        valor_causa_extenso="nove mil seiscentos e dezenove reais e vinte centavos",
        fecho=(
            "Termos em que pede e espera deferimento. Salvador/BA, 15 de maio de "
            "2026. Advogado Responsável, OAB/BA 99999."
        ),
        disclaimer_lgpd_oab=(
            "Este documento é insumo técnico-jurídico gerado por sistema de "
            "inteligência artificial e não substitui a responsabilidade do advogado "
            "constituído conforme OAB Provimento 209/2021. Dados pessoais tratados "
            "sob égide da LGPD (Lei 13.709/2018), art. 11 e art. 46 — proteção e "
            "confidencialidade de dados sensíveis. Revisão humana obrigatória "
            "pré-protocolo. Sistema não fornece aconselhamento jurídico autônomo."
        ),
        citacoes_jurisprudencia=["STJ-S539", "STJ-S472"],
        pontos_atencao=None,
    )


def make_peca_com_hitl() -> PecaRevisional:
    base = make_peca_aprovado_100()
    return base.model_copy(
        update={
            "pontos_atencao": (
                "Veredito do Juiz APROVADO_COM_RISCO_HITL — aderência 83.3%. "
                "Riscos identificados: (1) peso vinculação Súmulas no nível 3 (não 4 "
                "Tema Repetitivo); (2) divergência BACEN limítrofe; (3) jurisprudência "
                "TJBA específica não localizada no vault. Recomenda-se revisão humana "
                "pelo advogado responsável antes do protocolo, com possível "
                "complementação de fundamentos doutrinários ou aguardar superveniência "
                "de Tema Repetitivo STJ favorável."
            ),
        }
    )


def make_relatorio_rejeitado() -> RelatorioInviabilidade:
    return RelatorioInviabilidade(
        cabecalho=(
            "Relatório de Inviabilidade Revisional — Contrato CDC Veículos "
            "PF / Hash oracle...0000"
        ),
        sintese_analise=(
            "A análise técnica do contrato concluiu pela inviabilidade da ação "
            "revisional. Não foram identificados fundamentos consistentes para "
            "questionamento judicial da taxa praticada ou da capitalização dos juros."
        ),
        diagnostico_tecnico=(
            "Scores apurados pelo Juiz Revisor (sistema Python puro auditável): "
            "C1=0.00 (divergência BACEN abaixo de 0,5 pontos percentuais — taxa "
            "contratual coerente com média de mercado para o período de assinatura); "
            "C2=0.50 (peso vinculação Súmulas insuficiente — máximo 3, sem Súmula "
            "Vinculante STF ou Tema Repetitivo STJ aplicável); C3=1.00 (doc da "
            "jurisdição BA presente no vault). Aderência consolidada: 50.0% — abaixo "
            "do threshold mínimo de 70% definido pela metodologia FR-JUIZ-01 para "
            "emissão de peça revisional formal."
        ),
        motivos_rejeicao=[
            "Taxa contratual 1,99% a.m. coerente com média BACEN do período (1,85% a.m.)",
            "Ausência de Súmulas Vinculantes ou Repercussão Geral aplicáveis ao caso",
            "Cálculo de anatocismo não evidencia abusividade material relevante",
            "Diferença entre PMT composto e simples dentro do esperado SFN",
        ],
        recomendacao=(
            "Recomenda-se NÃO protocolar ação revisional com base na presente análise "
            "técnica. Sugere-se buscar outros fundamentos jurídicos ou aguardar "
            "evolução jurisprudencial favorável. O cliente deve ser informado sobre a "
            "viabilidade técnica antes de qualquer decisão judicial. A presente "
            "análise não vincula o advogado constituído."
        ),
        disclaimer_lgpd_oab=(
            "Este documento é insumo técnico-jurídico gerado por sistema de "
            "inteligência artificial e não substitui a responsabilidade do advogado "
            "constituído conforme OAB Provimento 209/2021. Dados pessoais tratados "
            "sob égide da LGPD (Lei 13.709/2018), art. 11 e art. 46 — proteção e "
            "confidencialidade. Revisão humana obrigatória pré-decisão. Sistema não "
            "fornece aconselhamento jurídico autônomo."
        ),
    )


def make_veredito(tipo: str) -> VeredictoJuiz:
    if tipo == "APROVADO_100":
        return VeredictoJuiz(c1_score=1.0, c2_score=1.0, c3_score=1.0, aderencia=100.0,
                             veredito="APROVADO_100", razoes=["Taxa BACEN divergente +0.14pp", "Súmula 539 aplicável"])
    if tipo == "APROVADO_COM_RISCO_HITL":
        return VeredictoJuiz(c1_score=1.0, c2_score=0.5, c3_score=1.0, aderencia=83.3,
                             veredito="APROVADO_COM_RISCO_HITL", razoes=["Aderência parcial"])
    return VeredictoJuiz(c1_score=0.0, c2_score=0.5, c3_score=1.0, aderencia=50.0,
                         veredito="REJEITADO", razoes=["Taxa BACEN coerente com mercado"])


# AC verification functions

def check_ac_02_cfoab_8_secoes(html: str, peca_type: str) -> dict:
    """AC-02: 8 seções CFOAB embedded (apenas para PecaRevisional)."""
    if peca_type == "RelatorioInviabilidade":
        return {"applicable": False, "reason": "Relatório inviabilidade tem estrutura distinta (NÃO petição)"}

    checks = {
        "cabecalho": "Excelent" in html and "Juiz" in html,
        "qualificacao_partes": ("Qualifica" in html) and ("das Partes" in html),
        "dos_fatos": "Dos Fatos" in html,
        "do_direito": "Do Direito" in html,
        "do_pedido": "Do Pedido" in html,
        "do_valor_causa": "Do Valor da Causa" in html,
        "fecho": "secao fecho" in html or "fecho" in html.lower(),
        "disclaimer_lgpd_oab": "peca-disclaimer" in html or "disclaimer" in html.lower(),
    }
    return {
        "applicable": True,
        "passed": all(checks.values()),
        "details": checks,
        "count": sum(checks.values()),
        "of": len(checks),
    }


def check_ac_03_disclaimer_lgpd_oab(html: str) -> dict:
    """AC-03: Disclaimer LGPD/OAB embedded."""
    checks = {
        "insumo_tecnico_juridico": ("Insumo t" in html or "insumo t" in html) and "dico" in html,
        "nao_substitui_responsabilidade": ("o substitui" in html) and ("responsabilidade" in html),
        "oab_provimento_209_2021": "OAB Provimento 209/2021" in html,
        "lgpd_mention": "LGPD" in html or "Lei 13.709" in html,
    }
    return {
        "passed": all(checks.values()),
        "details": checks,
        "count": sum(checks.values()),
        "of": len(checks),
    }


def check_ac_04_valor_causa_br(html: str, peca_type: str) -> dict:
    """AC-04: Valor causa formato BR (regex)."""
    if peca_type == "RelatorioInviabilidade":
        return {"applicable": False, "reason": "Relatório inviabilidade não tem valor causa (não é petição)"}

    pattern = r"R\$\s*[\d\.]+,\d{2}"
    matches = re.findall(pattern, html)
    has_extenso = "reais" in html.lower()
    return {
        "applicable": True,
        "passed": len(matches) > 0 and has_extenso,
        "matches": matches[:3],
        "has_extenso": has_extenso,
    }


def check_ac_05_citacoes_vault(peca, peca_type: str, vault_docs: list[str]) -> dict:
    """AC-05: Cross-reference citações Súmulas STJ com vault — FR-PECA-05 traceability."""
    if peca_type == "RelatorioInviabilidade":
        return {"applicable": False, "reason": "Relatório inviabilidade não cita Súmulas"}

    cited = list(peca.citacoes_jurisprudencia)
    fantasmas = [c for c in cited if c not in vault_docs]
    try:
        validar_citacoes_vault(peca, vault_docs)
        validation_passed = True
        validation_error = None
    except PecaHallucinationError as exc:
        validation_passed = False
        validation_error = str(exc)

    return {
        "applicable": True,
        "passed": validation_passed and len(fantasmas) == 0,
        "cited": cited,
        "fantasmas_detected": fantasmas,
        "vault_available_subset": [c for c in cited if c in vault_docs],
        "validation_passed": validation_passed,
        "validation_error": validation_error,
    }


def check_ac_06_metadata(html: str, pdf_bytes: bytes | None) -> dict:
    """AC-06: PDF metadata (verificação parcial via HTML <title> + brand strings)."""
    title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else None
    has_brand = "Revisor Contratual" in html
    has_subject_hint = "Peça Revisional" in html or "Relat" in html

    result = {
        "html_title_populated": bool(title and len(title) > 5),
        "html_title_value": title,
        "html_brand_revisor_contratual": has_brand,
        "html_subject_hint_peca_revisional": has_subject_hint,
    }
    if pdf_bytes:
        result["pdf_starts_with_magic"] = pdf_bytes.startswith(b"%PDF-")
        result["pdf_size_bytes"] = len(pdf_bytes)
    else:
        result["pdf_render_skipped"] = "TD-SP06-WEASYPRINT-WIN-GTK-DEPS — GTK libs ausentes"
    result["passed"] = result["html_title_populated"] and has_brand and has_subject_hint
    return result


def try_weasyprint_render(html: str, output_pdf: Path) -> bytes | None:
    """Tenta renderizar PDF via weasyprint. Retorna None se GTK ausente."""
    try:
        from weasyprint import HTML  # type: ignore
        pdf_bytes = HTML(string=html, base_url=str(PROJECT_ROOT / "bloco_interface" / "web" / "static")).write_pdf()
        output_pdf.write_bytes(pdf_bytes)
        try:
            output_pdf.chmod(0o600)
        except (OSError, NotImplementedError):
            pass
        return pdf_bytes
    except Exception as exc:
        print(f"  [weasyprint] SKIP — {type(exc).__name__}: {str(exc)[:80]}")
        return None


def main() -> int:
    print("=" * 70)
    print("Oracle Wave γ.3 — Smoke Fidelity Bloco γ (TD-SP06-FIDELITY-01)")
    print("=" * 70)
    print(f"Approach: Opção A+C (Jinja2 HTML standalone + Pydantic + vault cross-ref)")
    print(f"Vault docs disponíveis: {VAULT_DOCS_AVAILABLE}")
    print()

    contrato_meta = make_contrato_meta()
    env = _build_jinja_env()

    scenarios = [
        ("APROVADO_100", "peca/inicial-revisional-veiculos.html", make_peca_aprovado_100(), "PecaRevisional", "aprovado-100"),
        ("APROVADO_COM_RISCO_HITL", "peca/inicial-revisional-com-hitl.html", make_peca_com_hitl(), "PecaRevisional", "com-hitl"),
        ("REJEITADO", "peca/relatorio-inviabilidade.html", make_relatorio_rejeitado(), "RelatorioInviabilidade", "rejeitado"),
    ]

    scorecard = {
        "agent": "Oracle (Guardian)",
        "story_id": "TD-SP06-FIDELITY-01",
        "wave": "γ.3 (Bloco γ quality gate)",
        "date": "2026-05-14",
        "approach": "Opção A+C — Jinja2 HTML standalone + Pydantic strict + vault cross-ref",
        "vault_docs_available": VAULT_DOCS_AVAILABLE,
        "scenarios": [],
    }

    overall_pass = True

    for veredito_tipo, template_name, peca, peca_type, slug in scenarios:
        print(f"━━━ Cenário: {veredito_tipo} ━━━")
        print(f"  Template: {template_name}")
        print(f"  Peça type: {peca_type}")

        veredito = make_veredito(veredito_tipo)
        context = {
            "peca": peca,
            "contrato": contrato_meta,
            "veredito": veredito,
            "gerado_em": datetime.now().isoformat(),
        }

        # Render HTML
        start = time.time()
        template = env.get_template(template_name)
        html = template.render(**context)
        html_elapsed = round((time.time() - start) * 1000, 2)
        print(f"  HTML rendered: {len(html)} chars in {html_elapsed}ms")

        html_path = OUTPUT_DIR / f"peca-output-{slug}.html"
        html_path.write_text(html, encoding="utf-8")
        print(f"  → {html_path}")

        # Try weasyprint render real
        pdf_path = OUTPUT_DIR / f"peca-output-{slug}.pdf"
        pdf_bytes = try_weasyprint_render(html, pdf_path)
        if pdf_bytes:
            print(f"  PDF rendered: {len(pdf_bytes)} bytes → {pdf_path}")

        # AC verification
        ac_02 = check_ac_02_cfoab_8_secoes(html, peca_type)
        ac_03 = check_ac_03_disclaimer_lgpd_oab(html)
        ac_04 = check_ac_04_valor_causa_br(html, peca_type)
        ac_05 = check_ac_05_citacoes_vault(peca, peca_type, VAULT_DOCS_AVAILABLE)
        ac_06 = check_ac_06_metadata(html, pdf_bytes)

        # Pass/Fail logic — applicable ACs must pass
        applicable_passes = []
        for label, ac in [("AC-02", ac_02), ("AC-04", ac_04), ("AC-05", ac_05)]:
            if ac.get("applicable") is False:
                print(f"  {label} N/A — {ac.get('reason', '')}")
            else:
                p = ac.get("passed", False)
                applicable_passes.append(p)
                emoji = "✓" if p else "✗"
                print(f"  {label} {emoji} {p}")
        for label, ac in [("AC-03", ac_03), ("AC-06", ac_06)]:
            p = ac.get("passed", False)
            applicable_passes.append(p)
            emoji = "✓" if p else "✗"
            print(f"  {label} {emoji} {p}")

        scenario_pass = all(applicable_passes)
        overall_pass = overall_pass and scenario_pass

        scorecard["scenarios"].append({
            "veredito_tipo": veredito_tipo,
            "template_name": template_name,
            "peca_type": peca_type,
            "html_output": str(html_path.relative_to(PROJECT_ROOT)),
            "pdf_output": str(pdf_path.relative_to(PROJECT_ROOT)) if pdf_bytes else None,
            "html_size_chars": len(html),
            "pdf_size_bytes": len(pdf_bytes) if pdf_bytes else None,
            "render_latency_ms": html_elapsed,
            "scenario_verdict": "PASS" if scenario_pass else "FAIL",
            "ac_02_cfoab": ac_02,
            "ac_03_disclaimer": ac_03,
            "ac_04_valor_causa": ac_04,
            "ac_05_citacoes_vault": ac_05,
            "ac_06_metadata": ac_06,
        })
        print(f"  Verdict cenário: {'PASS' if scenario_pass else 'FAIL'}")
        print()

    # Cross-cenário hallucination probe — testar PecaRevisional COM citação fora vault
    print("━━━ Bonus: Layer 2 anti-hallucination probe ━━━")
    peca_hallucinated = make_peca_aprovado_100().model_copy(
        update={"citacoes_jurisprudencia": ["STJ-S539", "STJ-S999-FANTASMA"]}
    )
    try:
        validar_citacoes_vault(peca_hallucinated, VAULT_DOCS_AVAILABLE)
        hallucination_guard_works = False
        print("  ✗ Layer 2 NÃO bloqueou citação fora vault — FAIL")
    except PecaHallucinationError as exc:
        hallucination_guard_works = True
        print(f"  ✓ Layer 2 bloqueou citação fantasma (PecaHallucinationError raised)")
        print(f"     Reason: {str(exc)[:100]}")

    scorecard["layer_2_hallucination_guard"] = {
        "passed": hallucination_guard_works,
        "test_citations": ["STJ-S539", "STJ-S999-FANTASMA"],
    }

    overall_pass = overall_pass and hallucination_guard_works

    # Final scorecard
    print()
    print("=" * 70)
    print(f"VERDICT GLOBAL: {'PASS' if overall_pass else 'FAIL OR CONCERNS'}")
    print("=" * 70)

    scorecard["verdict_global"] = "PASS" if overall_pass else "CONCERNS"
    scorecard["weasyprint_pdf_render_status"] = (
        "available" if any(s.get("pdf_output") for s in scorecard["scenarios"])
        else "skipped_windows_gtk_deps_missing"
    )

    scorecard_path = OUTPUT_DIR / "oracle-scorecard.json"
    scorecard_path.write_text(json.dumps(scorecard, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Scorecard JSON: {scorecard_path}")

    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
