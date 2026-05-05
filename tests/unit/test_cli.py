"""Testes CLI Click — 100% offline via CliRunner + monkeypatch.

Estratégia: monkeypatch substitui pipeline.revisar_contrato e scrapers por mocks.
Cada subcomando (revisar, init-audit, populate-vault) tem testes happy + erros.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from bloco_audit.genesis import initialize_audit_genesis
from bloco_contratos.jurisprudencia import JurisprudenciaItem
from bloco_contratos.personas import VeredictoJuiz
from bloco_engine.bacen.client import BacenFetchExhausted
from bloco_engine.parsing.pymupdf_parser import PDFEncrypted
from bloco_interface import cli as cli_module
from bloco_interface.error_handler import translate_exception
from bloco_interface.output import format_veredito, is_rich_available
from bloco_workflow.pipeline import VaultEmptyError

pytestmark = [pytest.mark.unit]


# ─────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def runner() -> CliRunner:
    # Click 8.3+ removeu mix_stderr; stderr e stdout sempre separados via .stderr/.stdout
    return CliRunner()


@pytest.fixture
def fake_veredito() -> VeredictoJuiz:
    return VeredictoJuiz(
        c1_score=1.0,
        c2_score=0.85,
        c3_score=0.7,
        aderencia=85.0,
        veredito="APROVADO_COM_RISCO_HITL",
        razoes=[
            "C1: divergência BACEN dentro do limiar",
            "C2: peso máximo 4 (Tema Repetitivo)",
            "C3: 1 doc STJ aplicável",
            "Aderência total: 85.0% → APROVADO_COM_RISCO_HITL",
        ],
    )


@pytest.fixture
def pdf_placeholder(tmp_path: Path) -> Path:
    p = tmp_path / "contrato.pdf"
    p.write_bytes(b"%PDF-1.4\nplaceholder\n")
    return p


# ─────────────────────────────────────────────────────────────────────
# Smoke — entry point
# ─────────────────────────────────────────────────────────────────────


class TestCLIEntry:
    def test_main_help(self, runner: CliRunner) -> None:
        r = runner.invoke(cli_module.main, ["--help"])
        assert r.exit_code == 0
        assert "revisar" in r.stdout
        assert "init-audit" in r.stdout
        assert "populate-vault" in r.stdout
        assert "100% on-premise" in r.stdout  # tagline LGPD

    def test_main_version(self, runner: CliRunner) -> None:
        r = runner.invoke(cli_module.main, ["--version"])
        assert r.exit_code == 0
        assert "0.1.0" in r.stdout


# ─────────────────────────────────────────────────────────────────────
# revisar
# ─────────────────────────────────────────────────────────────────────


class TestRevisar:
    def test_revisar_vault_inexistente_falha_amigavel(
        self, runner: CliRunner, pdf_placeholder: Path, tmp_path: Path
    ) -> None:
        r = runner.invoke(cli_module.main, [
            "revisar", str(pdf_placeholder),
            "--vault-db", str(tmp_path / "naoexiste.db"),
        ])
        assert r.exit_code == 1
        assert "Vault não encontrado" in r.stderr or "Vault" in r.stderr
        assert "populate-vault" in r.stderr  # sugere ação

    def test_revisar_happy_path_via_monkeypatch(
        self,
        runner: CliRunner,
        pdf_placeholder: Path,
        tmp_path: Path,
        fake_veredito: VeredictoJuiz,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Cria vault vazio existente
        vault_db = tmp_path / "vault.db"
        from bloco_vault import open_vault
        open_vault(str(vault_db)).close()

        # Monkeypatch revisar_contrato para retornar veredito direto
        async def fake_pipeline(*args: object, **kwargs: object) -> VeredictoJuiz:
            return fake_veredito

        monkeypatch.setattr(cli_module, "revisar_contrato", fake_pipeline)

        r = runner.invoke(cli_module.main, [
            "revisar", str(pdf_placeholder),
            "--vault-db", str(vault_db),
            "--audit-path", str(tmp_path / "audit.jsonl"),
            "--bacen-cache", str(tmp_path / "bacen"),
        ])
        assert r.exit_code == 0
        assert "APROVADO_COM_RISCO_HITL" in r.stdout
        assert "85" in r.stdout  # aderência

    def test_revisar_pdf_criptografado_traduzido(
        self,
        runner: CliRunner,
        pdf_placeholder: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        vault_db = tmp_path / "vault.db"
        from bloco_vault import open_vault
        open_vault(str(vault_db)).close()

        async def cripto_pipeline(*args: object, **kwargs: object) -> VeredictoJuiz:
            raise PDFEncrypted("teste")

        monkeypatch.setattr(cli_module, "revisar_contrato", cripto_pipeline)

        r = runner.invoke(cli_module.main, [
            "revisar", str(pdf_placeholder),
            "--vault-db", str(vault_db),
            "--audit-path", str(tmp_path / "audit.jsonl"),
            "--bacen-cache", str(tmp_path / "bacen"),
        ])
        assert r.exit_code == 1
        assert "criptografado" in r.stderr
        assert "Traceback" not in r.stderr  # erro AMIGÁVEL, sem traceback

    def test_revisar_bacen_offline_traduzido(
        self,
        runner: CliRunner,
        pdf_placeholder: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        vault_db = tmp_path / "vault.db"
        from bloco_vault import open_vault
        open_vault(str(vault_db)).close()

        async def offline_pipeline(*args: object, **kwargs: object) -> VeredictoJuiz:
            raise BacenFetchExhausted("offline")

        monkeypatch.setattr(cli_module, "revisar_contrato", offline_pipeline)

        r = runner.invoke(cli_module.main, [
            "revisar", str(pdf_placeholder),
            "--vault-db", str(vault_db),
            "--audit-path", str(tmp_path / "audit.jsonl"),
            "--bacen-cache", str(tmp_path / "bacen"),
        ])
        assert r.exit_code == 1
        assert "BACEN offline" in r.stderr
        assert "api.bcb.gov.br" in r.stderr

    def test_revisar_vault_vazio_traduzido(
        self,
        runner: CliRunner,
        pdf_placeholder: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        vault_db = tmp_path / "vault.db"
        from bloco_vault import open_vault
        open_vault(str(vault_db)).close()

        async def empty_pipeline(*args: object, **kwargs: object) -> VeredictoJuiz:
            raise VaultEmptyError("vault vazio")

        monkeypatch.setattr(cli_module, "revisar_contrato", empty_pipeline)

        r = runner.invoke(cli_module.main, [
            "revisar", str(pdf_placeholder),
            "--vault-db", str(vault_db),
            "--audit-path", str(tmp_path / "audit.jsonl"),
            "--bacen-cache", str(tmp_path / "bacen"),
        ])
        assert r.exit_code == 1
        assert "Vault" in r.stderr
        assert "populate-vault" in r.stderr

    def test_revisar_pdf_inexistente_click_valida(
        self, runner: CliRunner
    ) -> None:
        r = runner.invoke(cli_module.main, ["revisar", "/nao/existe.pdf"])
        assert r.exit_code != 0
        assert "does not exist" in r.stderr.lower() or "não existe" in r.stderr.lower()


# ─────────────────────────────────────────────────────────────────────
# init-audit
# ─────────────────────────────────────────────────────────────────────


class TestInitAudit:
    def test_init_audit_cria_lock(
        self,
        runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("AUTH_COOKIE_KEY", "test-secret-32-bytes-padding-ok-x")
        lock = tmp_path / ".audit-genesis.lock"
        r = runner.invoke(cli_module.main, [
            "init-audit", "--lock-path", str(lock),
        ])
        assert r.exit_code == 0
        assert lock.exists()
        assert "GENESIS inicializado" in r.stdout

    def test_init_audit_idempotente(
        self,
        runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("AUTH_COOKIE_KEY", "test-secret-32-bytes-padding-ok-x")
        lock = tmp_path / ".audit-genesis.lock"
        # 1ª init
        runner.invoke(cli_module.main, ["init-audit", "--lock-path", str(lock)])
        # 2ª init — deve devolver mensagem amigável (não erro)
        r = runner.invoke(cli_module.main, ["init-audit", "--lock-path", str(lock)])
        assert r.exit_code == 0
        assert "já inicializado" in r.stdout.lower() or "rotação" in r.stdout.lower()


# ─────────────────────────────────────────────────────────────────────
# populate-vault
# ─────────────────────────────────────────────────────────────────────


class TestPopulateVault:
    def test_populate_vault_dry_run_via_monkeypatch(
        self,
        runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Mock scrapers
        fake_item = JurisprudenciaItem(
            id_doc="STJ-S539", court_id="STJ", tipo_doc="SUMULA", numero="539",
            binding=False, peso_vinculacao=3, legal_topic_principal="x",
            modalidade_relacionada=["CDC_VEICULOS_PF"], ano_julgamento=2010,
            ementa="capitalização mensal autorizada",
            texto_completo="Súmula 539 STJ texto longo qualquer aqui ok",
            indexed_at=datetime(2024, 1, 1), vigente_em=None, superseded_by=None,
            data_ultima_validacao=date.today(),
        )

        async def fake_stj() -> list[JurisprudenciaItem]:
            return [fake_item]

        async def fake_stf() -> list[JurisprudenciaItem]:
            return []

        monkeypatch.setattr(cli_module, "scrape_stj_sumulas", fake_stj)
        monkeypatch.setattr(cli_module, "scrape_stf_sumulas_vinculantes", fake_stf)

        vault_db = tmp_path / "vault.db"
        r = runner.invoke(cli_module.main, [
            "populate-vault", "--vault-db", str(vault_db), "--dry-run",
        ])
        assert r.exit_code == 0
        assert "1 items" in r.stdout
        assert "dry-run" in r.stdout

    def test_populate_vault_persiste_quando_nao_dry_run(
        self,
        runner: CliRunner,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        fake_item = JurisprudenciaItem(
            id_doc="STJ-S472", court_id="STJ", tipo_doc="SUMULA", numero="472",
            binding=False, peso_vinculacao=3, legal_topic_principal="x",
            modalidade_relacionada=["CDC_VEICULOS_PF"], ano_julgamento=2012,
            ementa="comissão de permanência texto longo qualquer aqui ok ok",
            texto_completo="Súmula 472 texto completo longo aqui ok ok ok",
            indexed_at=datetime(2024, 1, 1), vigente_em=None, superseded_by=None,
            data_ultima_validacao=date.today(),
        )

        async def fake_stj() -> list[JurisprudenciaItem]:
            return [fake_item]

        monkeypatch.setattr(cli_module, "scrape_stj_sumulas", fake_stj)

        vault_db = tmp_path / "vault.db"
        r = runner.invoke(cli_module.main, [
            "populate-vault", "--vault-db", str(vault_db), "--source", "stj",
        ])
        assert r.exit_code == 0
        assert "persistidos" in r.stdout

        # Confirma que persistiu de fato
        from bloco_vault import count, open_vault
        conn = open_vault(str(vault_db))
        assert count(conn) == 1
        conn.close()

    def test_populate_vault_source_invalido_click_valida(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        r = runner.invoke(cli_module.main, [
            "populate-vault", "--source", "tjba",  # inválido
        ])
        assert r.exit_code != 0


# ─────────────────────────────────────────────────────────────────────
# Tradução de exceções (error_handler)
# ─────────────────────────────────────────────────────────────────────


class TestErrorTranslation:
    def test_translate_pdf_encrypted(self) -> None:
        msg = translate_exception(PDFEncrypted("x"))
        assert "criptografado" in msg
        assert "Traceback" not in msg

    def test_translate_bacen_exhausted(self) -> None:
        msg = translate_exception(BacenFetchExhausted("x"))
        assert "BACEN" in msg
        assert "api.bcb.gov.br" in msg

    def test_translate_vault_empty(self) -> None:
        msg = translate_exception(VaultEmptyError("x"))
        assert "Vault" in msg
        assert "populate-vault" in msg

    def test_translate_unknown_exception_fallback(self) -> None:
        msg = translate_exception(RuntimeError("algo inesperado"))
        assert "RuntimeError" in msg
        assert "inesperado" in msg


# ─────────────────────────────────────────────────────────────────────
# Output formatting
# ─────────────────────────────────────────────────────────────────────


class TestOutput:
    def test_format_veredito_aprovado_100(self, fake_veredito: VeredictoJuiz) -> None:
        out = format_veredito(fake_veredito)
        # Funciona com rich OU ASCII
        assert "APROVADO_COM_RISCO_HITL" in out
        assert "85" in out

    def test_format_veredito_inclui_audit_hash_quando_fornecido(
        self, fake_veredito: VeredictoJuiz
    ) -> None:
        out = format_veredito(fake_veredito, audit_hash="a" * 64)
        assert "aaaaaaa" in out  # primeiros chars do hash

    def test_rich_disponivel_no_ambiente(self) -> None:
        # Verifica que rich foi instalado conforme deps; testes funcionam mesmo sem
        assert is_rich_available() is True
