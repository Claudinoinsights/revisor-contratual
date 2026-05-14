"""Born-digital synthetic PDFs (TD-SP06-MARKER-DEFERRED fallback Sprint 6 Bloco α).

Gera 4 PDFs born-digital sintéticos com texto contratual realista para validar
o pipeline end-to-end SEM Marker OCR (que falha em Python 3.14 Windows sem
Visual Studio Build Tools — ver TD-SP06-MARKER-DEFERRED).

Cada PDF é gerado via fpdf2 (puro Python, sem C extension) e atende:
  - Texto extraível por pymupdf4llm.to_markdown (>2000 chars markdown)
  - Metadata extraível por regex de bloco_engine/parsing/orchestrator.py
  - Fidelity score >= 0.5 (6+ keywords + tabela + valores R$)
  - Cláusulas com potencial revisional (anatocismo, comissão permanência, seguros)

Modalidades cobertas (match ModalidadeContrato Literal de bloco_contratos/contrato.py):
  - ccb        → CDC_BENS_PF (Cédula de Crédito Bancário)
  - veiculo    → CDC_VEICULOS_PF
  - imobiliario→ CDC_IMOBILIARIO
  - fies       → CDC_BENS_PF (FIES não tem enum dedicado; default match)

Uso:
  python scripts/generate_test_pdfs.py                    # gera todos os 4
  python scripts/generate_test_pdfs.py --modalidade ccb   # gera específico
  python scripts/generate_test_pdfs.py --output-dir /tmp  # custom output

Compliance: 100% texto fictício, partes fictícias, valores ilustrativos. Sem
dados reais de pessoas físicas/jurídicas (LGPD §11 § 5º — fixture de teste).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import click
from fpdf import FPDF

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_OUTPUT_DIR = Path("data/test-fixtures/synthetic")

Modalidade = Literal["ccb", "veiculo", "imobiliario", "fies"]

ALL_MODALIDADES: tuple[Modalidade, ...] = ("ccb", "veiculo", "imobiliario", "fies")


# ─────────────────────────────────────────────────────────────────────────────
# Spec declarativa de contrato sintético
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ContratoSpec:
    """Spec imutável de contrato sintético — single source of truth por modalidade.

    Atributos:
        modalidade: Chave curta (ccb/veiculo/imobiliario/fies).
        titulo: Cabeçalho do PDF (ex: "CÉDULA DE CRÉDITO BANCÁRIO").
        uf: Sigla UF brasileira (2 letras maiúsculas) que aparece no contrato.
        data_assinatura: Data DD/MM/YYYY (formato BR — regex orchestrator suporta).
        valor: Valor financiado formato BR (ex: "R$ 25.000,00").
        parcelas: Número de parcelas (1..480).
        taxa_am: Taxa mensal formato BR (ex: "1,99% a.m.").
        taxa_aa: Taxa anual formato BR (ex: "26,67% a.a.").
        cet_aa: Custo Efetivo Total anual.
        devedor_nome: Nome fictício pessoa física.
        devedor_cpf: CPF fictício (formato XXX.XXX.XXX-XX, sem validação algorítmica).
        credor_nome: Razão social fictícia banco/instituição.
        credor_cnpj: CNPJ fictício formato XX.XXX.XXX/XXXX-XX.
        clausulas: Lista de (titulo, texto) para renderização sequencial.
        modalidade_keyword: Palavra-chave para heurística _extract_modalidade
            do orchestrator (ex: "veículo", "imobiliário", "bem").
    """

    modalidade: Modalidade
    titulo: str
    uf: str
    data_assinatura: str
    valor: str
    parcelas: int
    taxa_am: str
    taxa_aa: str
    cet_aa: str
    devedor_nome: str
    devedor_cpf: str
    credor_nome: str
    credor_cnpj: str
    clausulas: tuple[tuple[str, str], ...]
    modalidade_keyword: str


# ─────────────────────────────────────────────────────────────────────────────
# Specs por modalidade — texto contratual realista PT-BR
# ─────────────────────────────────────────────────────────────────────────────

_CLAUSULAS_CCB: tuple[tuple[str, str], ...] = (
    (
        "CLÁUSULA 1 — IDENTIFICAÇÃO DAS PARTES",
        "Pelo presente instrumento particular de Cédula de Crédito Bancário, "
        "regida pela Lei nº 10.931/2004, as partes acima qualificadas firmam o "
        "presente contrato de financiamento, sendo o CREDOR a instituição "
        "financeira identificada no preâmbulo e o DEVEDOR a pessoa física "
        "qualificada, ambos com plena capacidade jurídica.",
    ),
    (
        "CLÁUSULA 2 — OBJETO DO CONTRATO",
        "Constitui objeto deste contrato a concessão de financiamento bancário "
        "(modalidade CDC bens) ao DEVEDOR, no valor total de R$ 35.000,00 "
        "(trinta e cinco mil reais), destinado ao capital de giro e aquisição "
        "de bens. O DEVEDOR confessa-se devedor da quantia ora financiada.",
    ),
    (
        "CLÁUSULA 3 — PRAZO E PARCELAS",
        "O presente contrato terá vigência de 36 (trinta e seis) meses, com "
        "início em 15/04/2023 e término previsto em 15/04/2026. O DEVEDOR pagará "
        "o valor financiado em 36 parcelas mensais e sucessivas, com primeiro "
        "vencimento em 15/05/2023, no valor estimado de cada prestação conforme "
        "tabela de amortização anexa.",
    ),
    (
        "CLÁUSULA 4 — TAXA DE JUROS E CET",
        "Sobre o valor financiado incidirão juros remuneratórios à taxa nominal "
        "de 2,15% a.m., equivalente a 29,11% a.a., capitalizados mensalmente. "
        "O Custo Efetivo Total (CET) é de 33,42% a.a., conforme Resolução CMN "
        "nº 3.517/2007 e Resolução BCB nº 4.881/2020.",
    ),
    (
        "CLÁUSULA 5 — SISTEMA DE AMORTIZAÇÃO (TABELA PRICE)",
        "O sistema de amortização adotado é o Sistema Francês (Tabela Price), "
        "que prevê prestações fixas com juros decrescentes e amortização "
        "crescente ao longo do prazo. A capitalização dos juros se dará de "
        "forma mensal, independentemente de pactuação expressa adicional, "
        "incidindo sobre o saldo devedor remanescente após cada prestação.",
    ),
    (
        "CLÁUSULA 6 — ENCARGOS POR INADIMPLÊNCIA",
        "Em caso de inadimplência, sobre o saldo devedor incidirão "
        "cumulativamente: (a) juros moratórios de 1% a.m.; (b) multa moratória "
        "de 2% sobre o valor da parcela vencida; (c) correção monetária pelo "
        "IGP-M/FGV; e (d) comissão de permanência calculada pela taxa de "
        "mercado vigente, cumuláveis entre si — Cláusula reconhecida.",
    ),
    (
        "CLÁUSULA 7 — GARANTIAS E SEGUROS",
        "Como condição de outorga do crédito, o DEVEDOR aderiu obrigatoriamente "
        "ao seguro prestamista oferecido pelo CREDOR, com prêmio incluso nas "
        "parcelas, sem opção de contratar com seguradora de livre escolha. "
        "Garantia adicional: alienação fiduciária de bem indicado em aditivo.",
    ),
    (
        "CLÁUSULA 8 — FORO E DISPOSIÇÕES FINAIS",
        "Fica eleito o foro da Comarca de Campinas/SP para dirimir quaisquer "
        "controvérsias oriundas deste contrato, com renúncia expressa a qualquer "
        "outro, por mais privilegiado que seja. O presente contrato é firmado "
        "em duas vias de igual teor.",
    ),
)


_CLAUSULAS_VEICULO: tuple[tuple[str, str], ...] = (
    (
        "CLÁUSULA 1 — IDENTIFICAÇÃO DAS PARTES",
        "Pelo presente Contrato de Financiamento de Veículo (modalidade CDC PF "
        "veículos), regido pela Resolução BCB nº 4.881/2020 e CDC (Lei "
        "8.078/1990), as partes acima qualificadas pactuam financiamento de "
        "automóvel mediante alienação fiduciária do bem.",
    ),
    (
        "CLÁUSULA 2 — OBJETO E BEM FINANCIADO",
        "Constitui objeto deste contrato o financiamento, pelo CREDOR, da "
        "aquisição pelo DEVEDOR de veículo automotor (automóvel) marca Honda, "
        "modelo Civic LX, ano/modelo 2024/2024, no valor de R$ 95.000,00 "
        "(noventa e cinco mil reais), sendo R$ 65.000,00 (sessenta e cinco mil "
        "reais) o valor financiado e R$ 30.000,00 dados a título de entrada.",
    ),
    (
        "CLÁUSULA 3 — PRAZO E PARCELAS",
        "O presente contrato terá prazo de 48 (quarenta e oito) meses para "
        "amortização integral. O DEVEDOR pagará o valor financiado em 48 "
        "parcelas mensais consecutivas, com primeiro vencimento em 10/02/2023 "
        "e último em 10/01/2027, no valor de prestação calculado conforme "
        "Tabela Price anexa.",
    ),
    (
        "CLÁUSULA 4 — TAXA DE JUROS, IOF E CET",
        "Sobre o saldo devedor incidirão juros remuneratórios à taxa de "
        "1,89% a.m., equivalente a 25,28% a.a., capitalizados mensalmente "
        "sem pactuação expressa específica. Incidirá IOF na forma da legislação "
        "vigente. O Custo Efetivo Total (CET) divulgado é de 30,15% a.a.",
    ),
    (
        "CLÁUSULA 5 — SISTEMA DE AMORTIZAÇÃO",
        "O sistema de amortização adotado é o Sistema Francês (Tabela Price). "
        "A capitalização mensal dos juros sobre o saldo devedor é inerente ao "
        "sistema escolhido, gerando incidência de juros sobre juros ao longo "
        "do prazo, conforme metodologia consagrada pelo mercado financeiro.",
    ),
    (
        "CLÁUSULA 6 — TARIFAS, SEGUROS E SERVIÇOS",
        "O DEVEDOR pagará: (a) Tarifa de Cadastro no valor de R$ 850,00, "
        "cobrada em renovação contratual; (b) Tarifa de Avaliação do Bem no "
        "valor de R$ 450,00 sem comprovação efetiva da prestação; (c) Seguro "
        "de Proteção Financeira (prestamista) com prêmio incluso nas parcelas, "
        "sem opção de não-contratação ou escolha de seguradora.",
    ),
    (
        "CLÁUSULA 7 — ENCARGOS POR INADIMPLÊNCIA",
        "Na hipótese de inadimplemento, incidirão sobre o saldo devedor "
        "cumulativamente: juros remuneratórios contratuais, juros moratórios "
        "de 1% a.m., multa moratória de 2%, correção monetária pelo INPC, e "
        "comissão de permanência pela taxa média de mercado, cumuláveis com "
        "multa e correção monetária.",
    ),
    (
        "CLÁUSULA 8 — GARANTIAS",
        "Para garantia do fiel cumprimento das obrigações pactuadas, o "
        "DEVEDOR transfere ao CREDOR a propriedade fiduciária do veículo "
        "objeto deste contrato, nos termos do Decreto-Lei 911/1969 e Lei "
        "9.514/1997, mantendo a posse direta na qualidade de fiel depositário.",
    ),
    (
        "CLÁUSULA 9 — FORO",
        "As partes elegem o foro da Comarca do Rio de Janeiro/RJ para "
        "dirimir quaisquer controvérsias decorrentes deste contrato, com "
        "renúncia expressa a qualquer outro foro, por mais privilegiado que "
        "venha a ser.",
    ),
)


_CLAUSULAS_IMOBILIARIO: tuple[tuple[str, str], ...] = (
    (
        "CLÁUSULA 1 — IDENTIFICAÇÃO DAS PARTES",
        "Pelo presente Contrato de Financiamento Imobiliário (Sistema "
        "Financeiro de Habitação — SFH), nos termos da Lei 4.380/1964 e "
        "alterações posteriores, as partes pactuam financiamento habitacional "
        "para aquisição de imóvel residencial urbano.",
    ),
    (
        "CLÁUSULA 2 — OBJETO E IMÓVEL FINANCIADO",
        "Constitui objeto a concessão de crédito imobiliário ao DEVEDOR no "
        "valor de R$ 320.000,00 (trezentos e vinte mil reais) destinado à "
        "aquisição de imóvel residencial situado em Belo Horizonte/MG, "
        "matrícula nº 12.345 do 5º Ofício do Registro de Imóveis, conforme "
        "memorial descritivo anexo.",
    ),
    (
        "CLÁUSULA 3 — PRAZO E PARCELAS",
        "O presente contrato será amortizado em 360 (trezentos e sessenta) "
        "parcelas mensais consecutivas, com primeiro vencimento em 20/03/2024 "
        "e último previsto para 20/02/2054. Cada prestação será composta de "
        "amortização, juros, seguro MIP, seguro DFI e taxa de administração.",
    ),
    (
        "CLÁUSULA 4 — TAXA DE JUROS, CES E CET",
        "Os juros remuneratórios serão de 0,75% a.m., equivalente a 9,38% "
        "a.a., calculados sobre o saldo devedor mensalmente atualizado. "
        "Aplica-se a Cota de Equilíbrio Securitário (CES) na forma "
        "regulamentar. O Custo Efetivo Total (CET) é de 11,42% a.a.",
    ),
    (
        "CLÁUSULA 5 — SISTEMA DE AMORTIZAÇÃO E CORREÇÃO",
        "O sistema de amortização adotado é o Sistema Francês (Tabela Price), "
        "com capitalização mensal dos juros sobre o saldo devedor. A correção "
        "monetária do saldo devedor seguirá o IPCA/IBGE (índice mais oneroso "
        "ao mutuário na faixa contratada). Aplica-se a Taxa Referencial (TR) "
        "como pós-fixação adicional.",
    ),
    (
        "CLÁUSULA 6 — SEGUROS HABITACIONAIS (MIP E DFI)",
        "O DEVEDOR contratará obrigatoriamente: (a) Seguro de Morte e "
        "Invalidez Permanente (MIP), com prêmio incluso nas parcelas; "
        "(b) Seguro de Danos Físicos do Imóvel (DFI), também incluso. Ambos "
        "os seguros serão contratados exclusivamente com seguradora vinculada "
        "ao CREDOR, sem opção de livre escolha pelo DEVEDOR.",
    ),
    (
        "CLÁUSULA 7 — GARANTIAS",
        "Como garantia da operação, o DEVEDOR institui ALIENAÇÃO FIDUCIÁRIA "
        "do imóvel objeto do financiamento em favor do CREDOR, nos termos da "
        "Lei 9.514/1997, mantendo a posse direta na qualidade de fiel "
        "depositário até a quitação integral do contrato.",
    ),
    (
        "CLÁUSULA 8 — ENCARGOS POR INADIMPLÊNCIA",
        "Em caso de inadimplência, incidirão sobre o saldo devedor: juros "
        "moratórios de 1% a.m., multa moratória de 2%, correção monetária "
        "pelo INPC e comissão de permanência pela taxa de mercado, todos "
        "cumuláveis entre si.",
    ),
    (
        "CLÁUSULA 9 — FORO",
        "As partes elegem o foro da Comarca de Belo Horizonte/MG para dirimir "
        "controvérsias deste contrato.",
    ),
)


_CLAUSULAS_FIES: tuple[tuple[str, str], ...] = (
    (
        "CLÁUSULA 1 — IDENTIFICAÇÃO DAS PARTES E PROGRAMA",
        "Pelo presente Contrato de Financiamento Estudantil — FIES "
        "(modalidade CDC bens educacionais), regido pela Lei 10.260/2001, "
        "Lei 11.552/2007, Lei 13.530/2017 e Manual Operacional FNDE vigente, "
        "as partes pactuam financiamento de despesas com curso superior.",
    ),
    (
        "CLÁUSULA 2 — OBJETO E VALOR",
        "Constitui objeto deste contrato a concessão de financiamento ao "
        "ESTUDANTE no valor total de R$ 48.000,00 (quarenta e oito mil reais), "
        "destinado ao custeio de mensalidades de curso superior em "
        "Instituição de Ensino Superior credenciada ao FIES (curso de "
        "Engenharia Civil, 5 anos de duração).",
    ),
    (
        "CLÁUSULA 3 — PERÍODO DE CARÊNCIA",
        "Durante o período de carência (cursando + 18 meses pós-formatura), "
        "o ESTUDANTE pagará trimestralmente o valor de R$ 50,00 por trimestre, "
        "a título de juros amortizáveis. A capitalização mensal de juros "
        "sobre o saldo devedor durante o período de carência ocorrerá de "
        "forma automática, independente de pactuação expressa adicional, "
        "amplificando o débito final acumulado.",
    ),
    (
        "CLÁUSULA 4 — TAXA DE JUROS",
        "Os juros aplicáveis ao saldo devedor são equivalentes à Taxa CESH "
        "(Custo Efetivo de Saldo Habilitado) divulgada pelo FNDE, fixada em "
        "0,55% a.m., equivalente a 6,80% a.a., capitalizados mensalmente. "
        "O Custo Efetivo Total (CET) é de 8,15% a.a.",
    ),
    (
        "CLÁUSULA 5 — FUNDO GARANTIDOR (FGEDUC)",
        "O ESTUDANTE pagará contribuição ao Fundo Garantidor da Educação "
        "Superior (FGEDUC) na alíquota de 5,63% sobre o valor financiado, "
        "sem demonstração da prestação proporcional do fundo garantidor, "
        "constituindo onerosidade adicional sem contrapartida verificada.",
    ),
    (
        "CLÁUSULA 6 — AMORTIZAÇÃO E PRAZO",
        "Após o período de carência, o saldo devedor será amortizado em "
        "162 (cento e sessenta e duas) parcelas mensais consecutivas, "
        "calculadas pelo Sistema Francês (Tabela Price). A primeira parcela "
        "vencerá em 15/01/2023 e a última em 15/06/2036.",
    ),
    (
        "CLÁUSULA 7 — GARANTIAS",
        "Como condição de outorga, o ESTUDANTE apresentará FIADOR PESSOA "
        "FÍSICA com renda comprovada equivalente a no mínimo 2 (duas) vezes "
        "o valor da parcela mensal, em contrato firmado anteriormente à "
        "vigência da Lei 13.530/2017, configurando desproporcionalidade da "
        "garantia para o curso de adesão estudantil.",
    ),
    (
        "CLÁUSULA 8 — ENCARGOS POR INADIMPLÊNCIA",
        "Em caso de inadimplência das parcelas pós-carência, incidirão "
        "cumulativamente sobre o saldo devedor: juros moratórios de 1% a.m., "
        "multa de 2% sobre cada prestação vencida, correção monetária pelo "
        "IPCA e comissão de permanência, podendo o débito ser inscrito em "
        "dívida ativa da União pela Procuradoria-Geral da Fazenda Nacional.",
    ),
    (
        "CLÁUSULA 9 — FORO",
        "Fica eleito o foro da Comarca de São Paulo/SP, sede do FNDE — "
        "Fundo Nacional de Desenvolvimento da Educação, para dirimir "
        "controvérsias decorrentes deste contrato.",
    ),
)


SPECS: dict[Modalidade, ContratoSpec] = {
    "ccb": ContratoSpec(
        modalidade="ccb",
        titulo="CÉDULA DE CRÉDITO BANCÁRIO — CDC BENS",
        uf="SP",
        data_assinatura="15/04/2023",
        valor="R$ 35.000,00",
        parcelas=36,
        taxa_am="2,15% a.m.",
        taxa_aa="29,11% a.a.",
        cet_aa="33,42% a.a.",
        devedor_nome="JOÃO DA SILVA SANTOS",
        devedor_cpf="111.222.333-44",
        credor_nome="BANCO SINTÉTICO S.A.",
        credor_cnpj="11.222.333/0001-44",
        clausulas=_CLAUSULAS_CCB,
        modalidade_keyword="bens",
    ),
    "veiculo": ContratoSpec(
        modalidade="veiculo",
        titulo="CONTRATO DE FINANCIAMENTO DE VEÍCULO (CDC PF)",
        uf="RJ",
        data_assinatura="10/02/2023",
        valor="R$ 65.000,00",
        parcelas=48,
        taxa_am="1,89% a.m.",
        taxa_aa="25,28% a.a.",
        cet_aa="30,15% a.a.",
        devedor_nome="MARIA OLIVEIRA COSTA",
        devedor_cpf="222.333.444-55",
        credor_nome="FINANCEIRA AUTO SINTÉTICA S.A.",
        credor_cnpj="22.333.444/0001-55",
        clausulas=_CLAUSULAS_VEICULO,
        modalidade_keyword="veículo",
    ),
    "imobiliario": ContratoSpec(
        modalidade="imobiliario",
        titulo="CONTRATO DE FINANCIAMENTO IMOBILIÁRIO (SFH)",
        uf="MG",
        data_assinatura="20/03/2024",
        valor="R$ 320.000,00",
        parcelas=360,
        taxa_am="0,75% a.m.",
        taxa_aa="9,38% a.a.",
        cet_aa="11,42% a.a.",
        devedor_nome="CARLOS ALBERTO PEREIRA",
        devedor_cpf="333.444.555-66",
        credor_nome="BANCO IMOBILIÁRIO SINTÉTICO S.A.",
        credor_cnpj="33.444.555/0001-66",
        clausulas=_CLAUSULAS_IMOBILIARIO,
        modalidade_keyword="imobiliário",
    ),
    "fies": ContratoSpec(
        modalidade="fies",
        titulo="CONTRATO DE FINANCIAMENTO ESTUDANTIL — FIES",
        uf="SP",
        data_assinatura="15/01/2023",
        valor="R$ 48.000,00",
        parcelas=162,
        taxa_am="0,55% a.m.",
        taxa_aa="6,80% a.a.",
        cet_aa="8,15% a.a.",
        devedor_nome="ANA PAULA RODRIGUES",
        devedor_cpf="444.555.666-77",
        credor_nome="FNDE — FUNDO NACIONAL DESENV. EDUCAÇÃO",
        credor_cnpj="00.378.257/0001-81",
        clausulas=_CLAUSULAS_FIES,
        modalidade_keyword="bens educacionais",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Renderização PDF via fpdf2
# ─────────────────────────────────────────────────────────────────────────────


class ContratoPDF(FPDF):
    """fpdf2 subclass com header/footer brand-neutro para fixtures sintéticos."""

    def __init__(self, spec: ContratoSpec) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self._spec = spec
        self.set_margins(left=20, top=20, right=20)
        self.set_auto_page_break(auto=True, margin=20)
        # PDF metadata (NFR-07) — sanitizados para latin-1 (fpdf2 core fonts)
        self.set_title(_safe_latin1(spec.titulo))
        self.set_author("Revisor Contratual Synthetic Fixtures")
        self.set_subject("TD-SP06-MARKER-DEFERRED fallback")
        self.set_creator("scripts/generate_test_pdfs.py")
        self.set_keywords(f"sintetico fixture {spec.modalidade}")

    def header(self) -> None:
        """Cabeçalho repetido em cada página: título + UF."""
        self.set_font("Helvetica", style="B", size=10)
        self.cell(
            0,
            6,
            _safe_latin1(self._spec.titulo),
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.set_font("Helvetica", style="I", size=8)
        self.cell(
            0,
            5,
            _safe_latin1(
                f"Foro: Comarca em {self._spec.uf} — "
                f"Documento sintético para teste técnico"
            ),
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.ln(4)

    def footer(self) -> None:
        """Rodapé com nº de página e marker de fixture sintético."""
        self.set_y(-15)
        self.set_font("Helvetica", style="I", size=7)
        self.cell(
            0,
            5,
            _safe_latin1(
                f"Página {self.page_no()}/{{nb}} — "
                f"Fixture sintético TD-SP06 — sem efeito jurídico real"
            ),
            align="C",
        )

    def render_preambulo(self) -> None:
        """Renderiza preâmbulo identificando partes + valores principais."""
        spec = self._spec
        self.set_font("Helvetica", style="B", size=11)
        self.cell(0, 8, "PREÂMBULO", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        self.set_font("Helvetica", size=10)

        # Linha CREDOR
        self.set_font("Helvetica", style="B", size=10)
        self.cell(30, 6, "CREDOR:", new_x="RIGHT", new_y="TOP")
        self.set_font("Helvetica", size=10)
        self.multi_cell(
            0,
            6,
            _safe_latin1(f"{spec.credor_nome}, CNPJ {spec.credor_cnpj}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )

        # Linha DEVEDOR
        self.set_font("Helvetica", style="B", size=10)
        self.cell(30, 6, "DEVEDOR:", new_x="RIGHT", new_y="TOP")
        self.set_font("Helvetica", size=10)
        self.multi_cell(
            0,
            6,
            _safe_latin1(f"{spec.devedor_nome}, CPF {spec.devedor_cpf}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )

        self.ln(2)

        # Bloco de dados resumidos
        self.set_font("Helvetica", style="B", size=10)
        self.cell(0, 6, "DADOS DO FINANCIAMENTO:", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", size=10)
        dados = [
            f"Modalidade: financiamento de {spec.modalidade_keyword}",
            f"Valor financiado: {spec.valor}",
            f"Número de parcelas: {spec.parcelas} parcelas",
            f"Taxa contratual: {spec.taxa_am} ({spec.taxa_aa})",
            f"Custo Efetivo Total: {spec.cet_aa}",
            f"Data de assinatura: {spec.data_assinatura}",
            f"Foro: Comarca em {spec.uf}",
        ]
        for linha in dados:
            # Sanitizar para latin-1 (fpdf2 core fonts limitation)
            self.multi_cell(
                0, 5, _safe_latin1(linha), new_x="LMARGIN", new_y="NEXT"
            )
        self.ln(4)

    def render_clausula(self, titulo: str, texto: str) -> None:
        """Renderiza uma cláusula com título em negrito + texto justificado."""
        self.set_font("Helvetica", style="B", size=10)
        self.multi_cell(0, 6, _safe_latin1(titulo), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)
        self.set_font("Helvetica", size=10)
        self.multi_cell(0, 5, _safe_latin1(texto), new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def render_tabela_amortizacao_resumida(self) -> None:
        """Renderiza tabela resumida (cabeçalho + 5 parcelas) para fidelity score.

        bloco_engine/parsing/fidelity.py exige tabela markdown (|...|...|) ou
        valores R$ para score >= 0.5. Renderizamos tabela visível em texto +
        valores monetários — pymupdf4llm.to_markdown converte para markdown.
        """
        self.set_font("Helvetica", style="B", size=10)
        self.cell(0, 6, "TABELA DE AMORTIZAÇÃO (RESUMO)", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

        self.set_font("Courier", size=8)
        # Cabeçalho separado por pipes (pymupdf4llm reconhece tabela)
        header = "| Parcela | Saldo Inicial | Juros | Amortização | Valor Parcela | Saldo Final |"
        self.cell(0, 5, header, new_x="LMARGIN", new_y="NEXT")
        self.cell(
            0,
            5,
            "|---------|---------------|-------|-------------|---------------|-------------|",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        # 5 linhas de exemplo (não cálculo real — fixture sintético)
        sample_rows = [
            "|    1    | R$ 35.000,00  | R$ 752 | R$ 743     | R$ 1.495,00  | R$ 34.257   |",
            "|    2    | R$ 34.257,00  | R$ 736 | R$ 759     | R$ 1.495,00  | R$ 33.498   |",
            "|    3    | R$ 33.498,00  | R$ 720 | R$ 775     | R$ 1.495,00  | R$ 32.723   |",
            "|   ...   | ...           | ...   | ...         | ...           | ...         |",
            "|   36    | R$ 1.475,00   | R$ 32  | R$ 1.463    | R$ 1.495,00  | R$    0,00  |",
        ]
        for row in sample_rows:
            self.cell(0, 5, row, new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def render_assinatura(self) -> None:
        """Renderiza bloco de assinaturas no final do contrato."""
        self.set_font("Helvetica", size=10)
        spec = self._spec
        self.ln(8)
        self.cell(
            0,
            6,
            _safe_latin1(
                f"Por estarem assim justos e contratados, firmam o presente em duas vias, "
                f"na cidade do foro acima eleito, em {spec.data_assinatura}."
            ),
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.ln(10)
        self.cell(80, 6, "_" * 30, align="C", new_x="RIGHT", new_y="TOP")
        self.cell(80, 6, "_" * 30, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", size=9)
        self.cell(80, 5, _safe_latin1(spec.credor_nome), align="C", new_x="RIGHT", new_y="TOP")
        self.cell(80, 5, _safe_latin1(spec.devedor_nome), align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(80, 5, "CREDOR", align="C", new_x="RIGHT", new_y="TOP")
        self.cell(80, 5, "DEVEDOR", align="C", new_x="LMARGIN", new_y="NEXT")


def _safe_latin1(text: str) -> str:
    """Sanitiza texto para encoding latin-1 (fpdf2 core fonts limitation).

    Substitui caracteres unicode comuns (—, "", ', etc) por equivalentes ASCII.
    Caracteres acentuados PT-BR (á, é, ç, ã, õ, etc) são preservados — latin-1
    suporta. Apenas pontuação tipográfica unicode (em dashes, smart quotes) é
    convertida para ASCII puro.
    """
    replacements = {
        "—": "-",  # em dash
        "–": "-",  # en dash
        "“": '"',  # left double quote
        "”": '"',  # right double quote
        "‘": "'",  # left single quote
        "’": "'",  # right single quote (apostrofe)
        "…": "...",
        "•": "-",
        "º": "o",  # ordinal masculino (alguns parsers core fpdf não suportam)
        "ª": "a",  # ordinal feminino
    }
    out = text
    for src, dst in replacements.items():
        out = out.replace(src, dst)
    return out


def generate_pdf(spec: ContratoSpec, output_path: Path) -> None:
    """Gera 1 PDF born-digital sintético a partir de ContratoSpec.

    Args:
        spec: Specificação do contrato (modalidade, partes, valores, cláusulas).
        output_path: Caminho de saída do PDF.

    Side effects:
        Cria diretório pai se não existir.
        Sobrescreve PDF existente sem warning (idempotência reproducibility).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = ContratoPDF(spec)
    pdf.alias_nb_pages()  # {nb} no footer
    pdf.add_page()

    pdf.render_preambulo()
    for titulo, texto in spec.clausulas:
        pdf.render_clausula(titulo, texto)
    pdf.render_tabela_amortizacao_resumida()
    pdf.render_assinatura()

    pdf.output(str(output_path))


# ─────────────────────────────────────────────────────────────────────────────
# CLI Click
# ─────────────────────────────────────────────────────────────────────────────


@click.command()
@click.option(
    "--modalidade",
    type=click.Choice(["ccb", "veiculo", "imobiliario", "fies", "all"]),
    default="all",
    help="Modalidade a gerar (default: all = gera os 4).",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=DEFAULT_OUTPUT_DIR,
    show_default=True,
    help="Diretório de saída dos PDFs.",
)
def main(modalidade: str, output_dir: Path) -> None:
    """Gera PDFs born-digital sintéticos para teste pipeline sem Marker OCR.

    Saída em {output_dir}/contrato_{modalidade}_synthetic.pdf.

    Examples:
        python scripts/generate_test_pdfs.py
        python scripts/generate_test_pdfs.py --modalidade veiculo
        python scripts/generate_test_pdfs.py --output-dir /tmp/fixtures
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if modalidade == "all":
        targets: tuple[Modalidade, ...] = ALL_MODALIDADES
    else:
        targets = (modalidade,)  # type: ignore[assignment]

    click.echo(f"Gerando {len(targets)} PDF(s) sintético(s) em {output_dir}/")

    for mod in targets:
        spec = SPECS[mod]
        output_path = output_dir / f"contrato_{mod}_synthetic.pdf"
        try:
            generate_pdf(spec, output_path)
            size_kb = output_path.stat().st_size / 1024
            click.echo(f"  [OK] {output_path.name} ({size_kb:.1f} KB)")
        except Exception as exc:  # noqa: BLE001
            click.echo(f"  [FAIL] {output_path.name}: {exc}", err=True)
            sys.exit(1)

    click.echo("\nPDFs sintéticos gerados com sucesso.")
    click.echo(
        "Próximo passo: python -m bloco_interface.cli revisar "
        f"{output_dir}/contrato_ccb_synthetic.pdf --tier balanced"
    )


if __name__ == "__main__":
    main()
