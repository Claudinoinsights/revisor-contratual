"""Tradução de exceções → mensagens humanas amigáveis (D-MOR-4.1-D).

Usuário final NÃO deve ver Python tracebacks. Cada exceção do pipeline tem
mensagem clara + sugestão de ação.
"""

from __future__ import annotations

from typing import Callable

from bloco_audit.genesis import GenesisAlreadyInitialized
from bloco_engine.bacen.client import BacenFetchExhausted, ModalidadeNaoSuportada
from bloco_engine.parsing.marker_parser import ParserOCRRequired
from bloco_engine.parsing.pymupdf_parser import PDFEncrypted, PDFInvalid
from bloco_engine.parsing.orchestrator import MetadataExtractionError
from bloco_workflow.pipeline import PipelineError, VaultEmptyError


def translate_exception(exc: Exception) -> str:
    """Devolve mensagem humana para exceção conhecida do pipeline.

    Returns:
        Mensagem PT-BR pronta para exibir ao usuário (sem traceback).
    """
    # Parsing
    if isinstance(exc, PDFEncrypted):
        return (
            "❌ PDF criptografado — decodifique antes de tentar novamente.\n"
            "   (Use Adobe Acrobat ou similar para remover a senha)."
        )
    if isinstance(exc, PDFInvalid):
        return (
            "❌ Arquivo não é um PDF válido — verifique se o arquivo está corrompido."
        )
    if isinstance(exc, ParserOCRRequired):
        return (
            "❌ PDF parece imagem-only (sem texto extraível).\n"
            "   Instale extras OCR: pip install revisor-contratual[ocr]"
        )
    if isinstance(exc, MetadataExtractionError):
        return (
            "❌ Não consegui extrair metadata do PDF.\n"
            "   Forneça via flags: --uf BA --data-assinatura YYYY-MM-DD"
        )

    # BACEN
    if isinstance(exc, BacenFetchExhausted):
        return (
            "❌ BACEN offline e sem cache de fallback.\n"
            "   Verifique conexão com api.bcb.gov.br ou aguarde."
        )
    if isinstance(exc, ModalidadeNaoSuportada):
        return f"❌ Modalidade não mapeada no BACEN: {exc}"

    # Vault
    if isinstance(exc, VaultEmptyError):
        return (
            "❌ Vault de jurisprudência vazio.\n"
            "   Rode: revisor populate-vault --source all"
        )

    # Audit
    if isinstance(exc, GenesisAlreadyInitialized):
        return (
            "ℹ️  GENESIS audit já inicializado.\n"
            "   Para rotação segura, ver docs/sop-rotacao-auth-cookie-key.md"
        )

    # Pipeline genérico (subclasses específicas tratadas acima)
    if isinstance(exc, PipelineError):
        return f"❌ Erro no pipeline: {exc}"

    # Fallback — exceção não-prevista
    return f"❌ Erro inesperado ({type(exc).__name__}): {exc}"


def safe_run(fn: Callable[[], int], *, on_error: Callable[[str], None]) -> int:
    """Executa fn() e captura exceções conhecidas, traduzindo para mensagem humana.

    Args:
        fn: callable que retorna exit_code (0 sucesso, !=0 erro).
        on_error: callback para imprimir mensagem traduzida.

    Returns:
        Exit code (0 ou 1).
    """
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        on_error(translate_exception(exc))
        return 1
