"""Testes unit bloco_engine/parsing — pipeline PDF → ParsedContract.

Estratégia: 100% offline.
  - parser_fn injetável evita dependência hard de PyMuPDF/Marker em CI
  - hash do PDF é calculado a partir de bytes literais inline (não precisa fixture física)

NOTA: 1 fixture pdf_path retorna `tmp_path / "fake.pdf"` (arquivo VAZIO ou bytes literais
mínimos) — é apenas placeholder para signatures que exigem `Path`. O parser_fn
injetável devolve o markdown que QUEREMOS testar, ignorando o conteúdo do arquivo.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from bloco_contratos.contrato import ContratoMetadata, ParsedContract
from bloco_engine.parsing import (
    FIDELITY_THRESHOLD_DEFAULT,
    MetadataExtractionError,
    ParserOCRRequired,
    compute_contract_hash,
    compute_fidelity_score,
    extract_metadata_from_markdown,
    parse_contract,
)
from bloco_engine.parsing.pymupdf_parser import PDFEncrypted, PDFInvalid


# ─────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def pdf_path(tmp_path: Path) -> Path:
    """Path placeholder — bytes do arquivo são irrelevantes (parser_fn substitui)."""
    p = tmp_path / "contrato.pdf"
    p.write_bytes(b"%PDF-1.4\n%placeholder\n")
    return p


MARKDOWN_CONTRATO_VEICULOS_RICO = """
# Contrato de Financiamento — CDC Veículos PF

**UF:** BA
**Data de assinatura:** 15/03/2024
**Valor financiado:** R$ 50.000,00
**Taxa contratual:** 1,99% a.m. (24,5% a.a.)
**Número de parcelas:** 48 parcelas

## Tabela de amortização

| Parcela | Saldo Inicial | Juros | Amortização | Valor | Saldo Final |
|---------|--------------|-------|-------------|-------|-------------|
| 1 | 50.000,00 | 995,00 | 305,40 | 1.300,40 | 49.694,60 |
| 2 | 49.694,60 | 988,92 | 311,48 | 1.300,40 | 49.383,12 |
"""

MARKDOWN_VAZIO = ""

MARKDOWN_LIXO_OCR = "asdf qwer zxcv 1234 ###"


def _fake_parser(markdown: str, pages: int = 3) -> Any:
    """Fábrica de parser_fn que retorna (markdown, pages)."""

    def _fn(_path: Path) -> tuple[str, int]:
        return markdown, pages

    return _fn


# ─────────────────────────────────────────────────────────────────────
# Hash do PDF
# ─────────────────────────────────────────────────────────────────────


class TestContractHash:
    def test_hash_deterministico(self) -> None:
        h1 = compute_contract_hash(b"abc")
        h2 = compute_contract_hash(b"abc")
        assert h1 == h2
        assert len(h1) == 64  # SHA256 hex

    def test_hash_diferente_para_bytes_diferentes(self) -> None:
        assert compute_contract_hash(b"abc") != compute_contract_hash(b"abd")

    def test_hash_aceita_bytes_vazios(self) -> None:
        h = compute_contract_hash(b"")
        assert len(h) == 64


# ─────────────────────────────────────────────────────────────────────
# Fidelity score
# ─────────────────────────────────────────────────────────────────────


class TestFidelityScore:
    def test_markdown_vazio_retorna_zero(self) -> None:
        assert compute_fidelity_score("") == 0.0
        assert compute_fidelity_score("   \n\t  ") == 0.0

    def test_markdown_rico_retorna_score_alto(self) -> None:
        score = compute_fidelity_score(MARKDOWN_CONTRATO_VEICULOS_RICO)
        assert score >= 0.9, f"esperado >=0.9, veio {score}"
        assert score <= 1.0

    def test_markdown_lixo_retorna_score_baixo(self) -> None:
        score = compute_fidelity_score(MARKDOWN_LIXO_OCR)
        assert score < FIDELITY_THRESHOLD_DEFAULT, (
            f"esperado <{FIDELITY_THRESHOLD_DEFAULT}, veio {score}"
        )

    def test_so_keywords_sem_tabela_sem_monetario(self) -> None:
        # 6 keywords → score_keywords=0.5; sem tabela=0; sem monetário=0
        md = "Contrato de financiamento CDC. Parcela, juros, taxa, saldo, prestação."
        score = compute_fidelity_score(md)
        assert score == pytest.approx(0.5, abs=0.01)


# ─────────────────────────────────────────────────────────────────────
# Extração de metadata (FR-PARSE-02)
# ─────────────────────────────────────────────────────────────────────


class TestMetadataExtraction:
    def test_markdown_rico_extrai_todos_campos(self) -> None:
        meta = extract_metadata_from_markdown(
            MARKDOWN_CONTRATO_VEICULOS_RICO,
            contract_hash="a" * 64,
        )
        assert meta.uf_contrato == "BA"
        assert meta.data_assinatura == date(2024, 3, 15)
        assert meta.modalidade == "CDC_VEICULOS_PF"
        assert Decimal(meta.valor_financiado or "") == Decimal("50000.00")
        assert Decimal(meta.taxa_contratual_aa or "") == Decimal("24.5")
        assert Decimal(meta.taxa_contratual_am or "") == Decimal("1.99")
        assert meta.n_parcelas == 48

    def test_data_iso_funciona(self) -> None:
        md = "Estado: SP. Data: 2023-08-22. Veículo."
        meta = extract_metadata_from_markdown(md, contract_hash="b" * 64)
        assert meta.data_assinatura == date(2023, 8, 22)
        assert meta.uf_contrato == "SP"

    def test_modalidade_cartao_rotativo_detectada(self) -> None:
        md = "BA 01/01/2023. Cartão de crédito modalidade rotativo."
        meta = extract_metadata_from_markdown(md, contract_hash="c" * 64)
        assert meta.modalidade == "CARTAO_ROTATIVO"

    def test_modalidade_cartao_isolado_nao_dispara_rotativo(self) -> None:
        """F-PARSE-HIGH-01 regression — "cartão de débito automático" em CDC veicular
        NÃO deve ser classificado como CARTAO_ROTATIVO (sem palavra 'rotativo')."""
        md = (
            "BA 15/03/2024. Contrato CDC veículo Honda Civic. "
            "Pagamento das parcelas via cartão de débito automático."
        )
        meta = extract_metadata_from_markdown(md, contract_hash="k" * 64)
        assert meta.modalidade == "CDC_VEICULOS_PF", (
            f"esperado CDC_VEICULOS_PF, veio {meta.modalidade} — bug F-PARSE-HIGH-01 reapareceu"
        )

    def test_modalidade_cartao_sem_til_isolado_nao_dispara_rotativo(self) -> None:
        """F-PARSE-HIGH-01 regression — "cartao" sem til, sem 'rotativo' em CDC
        veicular NÃO deve ser classificado como CARTAO_ROTATIVO."""
        md = (
            "SP 20/06/2024. CDC veiculo. "
            "Debito em cartao do banco para quitar parcelas mensais."
        )
        meta = extract_metadata_from_markdown(md, contract_hash="l" * 64)
        assert meta.modalidade == "CDC_VEICULOS_PF", (
            f"esperado CDC_VEICULOS_PF, veio {meta.modalidade} — bug F-PARSE-HIGH-01 reapareceu"
        )

    def test_modalidade_imobiliario_detectada(self) -> None:
        md = "RJ 02/02/2023. Financiamento imobiliário SFH."
        meta = extract_metadata_from_markdown(md, contract_hash="d" * 64)
        assert meta.modalidade == "CDC_IMOBILIARIO"

    def test_uf_ausente_levanta(self) -> None:
        md = "Sem estado aqui. Data 01/01/2024. Veículo."
        with pytest.raises(MetadataExtractionError, match="uf_contrato"):
            extract_metadata_from_markdown(md, contract_hash="e" * 64)

    def test_data_ausente_levanta(self) -> None:
        md = "BA. Veículo financiado sem data nenhuma."
        with pytest.raises(MetadataExtractionError, match="data_assinatura"):
            extract_metadata_from_markdown(md, contract_hash="f" * 64)

    def test_overrides_substituem_extracao(self) -> None:
        md = "Sem nada útil aqui."
        meta = extract_metadata_from_markdown(
            md,
            contract_hash="g" * 64,
            uf_override="BA",
            data_override=date(2024, 1, 1),
        )
        assert meta.uf_contrato == "BA"
        assert meta.data_assinatura == date(2024, 1, 1)

    def test_data_pre_1986_rejeitada_por_pydantic(self) -> None:
        md = "BA Data: 01/01/1980. Veículo."
        # Pydantic field_validator rejeita pré-1986
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="1986"):
            extract_metadata_from_markdown(md, contract_hash="h" * 64)

    def test_n_parcelas_fora_da_faixa_retorna_none(self) -> None:
        md = "BA 01/01/2024. Veículo. 999 parcelas (acima do limite 480)."
        meta = extract_metadata_from_markdown(md, contract_hash="i" * 64)
        assert meta.n_parcelas is None

    def test_campos_opcionais_ausentes_ficam_none(self) -> None:
        md = "BA Data: 01/01/2024. Veículo financiado."
        meta = extract_metadata_from_markdown(md, contract_hash="j" * 64)
        assert meta.valor_financiado is None
        assert meta.taxa_contratual_aa is None
        assert meta.n_parcelas is None


# ─────────────────────────────────────────────────────────────────────
# Orquestrador parse_contract — happy path + fallback
# ─────────────────────────────────────────────────────────────────────


class TestParseContract:
    def test_happy_path_pymupdf_suficiente(self, pdf_path: Path) -> None:
        result = parse_contract(
            pdf_path,
            pymupdf_fn=_fake_parser(MARKDOWN_CONTRATO_VEICULOS_RICO, pages=3),
        )
        assert isinstance(result, ParsedContract)
        assert isinstance(result.metadata, ContratoMetadata)
        assert result.parser_used == "pymupdf4llm"
        assert result.pages_count == 3
        assert result.fidelity_score is not None
        assert result.fidelity_score >= 0.9

    def test_pdf_bytes_override_evita_leitura_disco(self, tmp_path: Path) -> None:
        # Path inexistente — só funciona porque pdf_bytes é fornecido
        ghost_path = tmp_path / "nao_existe.pdf"
        result = parse_contract(
            ghost_path,
            pdf_bytes=b"conteudo arbitrario",
            pymupdf_fn=_fake_parser(MARKDOWN_CONTRATO_VEICULOS_RICO),
        )
        # Hash bate com o que esperamos do override
        assert result.metadata.contract_hash == compute_contract_hash(b"conteudo arbitrario")

    def test_fidelity_baixo_aciona_fallback_marker(self, pdf_path: Path) -> None:
        result = parse_contract(
            pdf_path,
            pymupdf_fn=_fake_parser(MARKDOWN_VAZIO),  # primary falha
            marker_fn=_fake_parser(MARKDOWN_CONTRATO_VEICULOS_RICO),  # fallback resolve
        )
        assert result.parser_used == "marker_ocr"
        assert result.fidelity_score is not None and result.fidelity_score >= 0.9

    def test_marker_indisponivel_levanta_ocr_required(self, pdf_path: Path) -> None:
        # primary devolve markdown insuficiente E marker_fn=None com Marker não instalado
        # Em CI marker NÃO está instalado → levanta ParserOCRRequired
        with pytest.raises(ParserOCRRequired):
            parse_contract(
                pdf_path,
                pymupdf_fn=_fake_parser(MARKDOWN_VAZIO),
                marker_fn=None,  # força default — Marker indisponível em CI
            )

    def test_parser_ocr_required_message_contem_solucao_acionavel(self, pdf_path: Path) -> None:
        """F-PIPELINE-LOW-01 hardening UX: mensagem PT-BR contém comando pip install acionável."""
        with pytest.raises(ParserOCRRequired) as exc_info:
            parse_contract(
                pdf_path,
                pymupdf_fn=_fake_parser(MARKDOWN_VAZIO),
                marker_fn=None,
            )
        msg = str(exc_info.value)
        assert "pip install revisor-contratual[ocr]" in msg
        assert "Solução" in msg or "Solucao" in msg

    def test_parser_ocr_required_message_contem_alternativa(self, pdf_path: Path) -> None:
        """F-PIPELINE-LOW-01 hardening UX: mensagem oferece alternativa para usuário sem OCR."""
        with pytest.raises(ParserOCRRequired) as exc_info:
            parse_contract(
                pdf_path,
                pymupdf_fn=_fake_parser(MARKDOWN_VAZIO),
                marker_fn=None,
            )
        msg = str(exc_info.value)
        assert "converta para PDF" in msg or "preservando a camada de texto" in msg
        assert "Alternativa" in msg

    def test_metadata_extraction_falha_com_overrides_ausentes(self, pdf_path: Path) -> None:
        # markdown rico em palavras mas sem UF/data
        md = "Contrato CDC veículo. Valor R$ 10.000,00. 24 parcelas. Juros 2,5% a.m."
        with pytest.raises(MetadataExtractionError):
            parse_contract(pdf_path, pymupdf_fn=_fake_parser(md))


# ─────────────────────────────────────────────────────────────────────
# Erros propagados de parsers low-level
# ─────────────────────────────────────────────────────────────────────


class TestParserLowLevelErrors:
    def test_pdf_encrypted_propaga(self, pdf_path: Path) -> None:
        def bombs_encrypted(_p: Path) -> tuple[str, int]:
            raise PDFEncrypted("teste cripto")

        with pytest.raises(PDFEncrypted):
            parse_contract(pdf_path, pymupdf_fn=bombs_encrypted)

    def test_pdf_invalid_propaga(self, pdf_path: Path) -> None:
        def bombs_invalid(_p: Path) -> tuple[str, int]:
            raise PDFInvalid("bytes não são PDF")

        with pytest.raises(PDFInvalid):
            parse_contract(pdf_path, pymupdf_fn=bombs_invalid)


# ─────────────────────────────────────────────────────────────────────
# Threshold de fidelity custom
# ─────────────────────────────────────────────────────────────────────


class TestFidelityThreshold:
    def test_threshold_zero_nunca_aciona_fallback(self, pdf_path: Path) -> None:
        # threshold=0.0 → mesmo markdown vazio (score=0) NÃO aciona fallback
        # Mas MetadataExtraction vai falhar porque markdown vazio não tem UF/data.
        with pytest.raises(MetadataExtractionError):
            parse_contract(
                pdf_path,
                pymupdf_fn=_fake_parser(MARKDOWN_VAZIO),
                fidelity_threshold=0.0,
            )

    def test_threshold_alto_sempre_aciona_fallback(self, pdf_path: Path) -> None:
        # threshold=1.5 (impossível) → SEMPRE aciona fallback
        result = parse_contract(
            pdf_path,
            pymupdf_fn=_fake_parser(MARKDOWN_CONTRATO_VEICULOS_RICO),
            marker_fn=_fake_parser(MARKDOWN_CONTRATO_VEICULOS_RICO),
            fidelity_threshold=1.5,
        )
        assert result.parser_used == "marker_ocr"
