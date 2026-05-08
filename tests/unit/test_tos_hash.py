"""Unit tests TOS hash + filesystem read (SP04-LGPD-01 AC-04 + AC-06).

Cobre helpers de ``bloco_auth/tos.py`` sem requerer DB:
- ``compute_tos_hash`` deterministic + NFC normalization + format SHA-256
- ``get_tos_text`` filesystem read + cache TTL + missing version error
- Path traversal mitigation (semver regex)

Tests integration de POST /accept + GET /status persistence ficam em
``tests/integration/test_tos_lifecycle_e2e.py`` (chunk 6 — _REQUIRES_POSTGRES).

Mirror estrutural ``tests/unit/test_dpa_hash.py`` (paridade ADR-019 pattern).
"""

from __future__ import annotations

import unicodedata

import pytest

from bloco_auth import tos


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    """Limpa cache filesystem entre tests."""
    tos.clear_tos_cache()
    yield
    tos.clear_tos_cache()


@pytest.fixture
def _tos_dir(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Aponta TOS_TEMPLATES_DIR para tmp_path com v1.0.0.md fixture."""
    (tmp_path / "v1.0.0.md").write_text(
        "# TOS v1.0.0\n\nTermos de uso operador SaaS com acentuação portuguesa.\n",
        encoding="utf-8",
    )
    (tmp_path / "v1.1.0.md").write_text(
        "# TOS v1.1.0\n\nVersão atualizada minor bump.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TOS_TEMPLATES_DIR", str(tmp_path))
    return tmp_path


@pytest.mark.unit
def test_tos_hash_deterministic() -> None:
    """compute_tos_hash chamado 2x retorna mesmo hash."""
    text = "TOS texto de exemplo operador"
    assert tos.compute_tos_hash(text) == tos.compute_tos_hash(text)


@pytest.mark.unit
def test_tos_hash_unicode_normalization() -> None:
    """Texto NFD vs NFC produz MESMO hash (NFC normalization aplicada).

    Mirror test_dpa_hash test pattern — TOS hash usa mesma NFC normalization
    para defesa cross-OS (Mac NFD vs Linux NFC).
    """
    text_nfc = unicodedata.normalize("NFC", "operação operador")
    text_nfd = unicodedata.normalize("NFD", "operação operador")
    assert text_nfc != text_nfd, "Setup do teste precisa NFC != NFD"
    assert tos.compute_tos_hash(text_nfc) == tos.compute_tos_hash(text_nfd), (
        "NFC normalization deve produzir hash idêntico cross-OS"
    )


@pytest.mark.unit
def test_tos_hash_format() -> None:
    """Hash retornado é 64 chars hex (SHA-256)."""
    h = tos.compute_tos_hash("qualquer texto TOS")
    assert len(h) == 64, f"SHA-256 hex tem 64 chars, recebido {len(h)}"
    assert all(c in "0123456789abcdef" for c in h), "Hash deve ser hex lowercase"


@pytest.mark.unit
def test_tos_hash_different_text_different_hash() -> None:
    """Textos diferentes → hashes diferentes."""
    h_a = tos.compute_tos_hash("texto TOS A")
    h_b = tos.compute_tos_hash("texto TOS B")
    assert h_a != h_b


@pytest.mark.unit
def test_tos_dpa_hash_distinct_for_same_text() -> None:
    """compute_tos_hash e compute_dpa_hash usam mesmo SHA-256 algoritmo —
    para o MESMO texto retornam mesmo hash. Isso é correto: o hash é função
    do texto (não do tipo de documento). A distinção entre TOS/DPA acontece
    em metadata (table separada + version field separado), não no hash.
    """
    from bloco_auth import dpa

    text = "Texto idêntico submetido aos dois helpers"
    assert tos.compute_tos_hash(text) == dpa.compute_dpa_hash(text), (
        "Mesmo SHA-256 algoritmo; distinção é via tabela + version field"
    )


@pytest.mark.unit
def test_get_tos_text_existing_version(_tos_dir) -> None:
    """Lê v1.0.0.md OK retorna conteúdo."""
    text = tos.get_tos_text("1.0.0")
    assert "TOS v1.0.0" in text
    assert "acentuação" in text


@pytest.mark.unit
def test_get_tos_text_missing_version(_tos_dir) -> None:
    """Version inexistente → FileNotFoundError com mensagem informativa."""
    with pytest.raises(FileNotFoundError, match=r"versão 9\.9\.9"):
        tos.get_tos_text("9.9.9")


@pytest.mark.unit
def test_get_tos_text_invalid_version_format() -> None:
    """Version com path traversal attempt → ValueError (anti-traversal)."""
    with pytest.raises(ValueError, match="path-traversal|semver"):
        tos.get_tos_text("../../../etc/passwd")
    with pytest.raises(ValueError):
        tos.get_tos_text("1.0")  # não bate semver MAJOR.MINOR.PATCH
    with pytest.raises(ValueError):
        tos.get_tos_text("v1.0.0")  # prefix v não permitido no helper


@pytest.mark.unit
def test_get_tos_text_cached(_tos_dir, monkeypatch: pytest.MonkeyPatch) -> None:
    """Duas chamadas mesma version → 1 read filesystem (cache hit)."""
    read_count = {"n": 0}
    original_read = type(_tos_dir / "v1.0.0.md").read_text

    def counting_read(self, *args, **kwargs):
        read_count["n"] += 1
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr("pathlib.Path.read_text", counting_read)

    text1 = tos.get_tos_text("1.0.0")
    text2 = tos.get_tos_text("1.0.0")
    assert text1 == text2
    assert read_count["n"] == 1, (
        f"Cache hit esperado: read_text deve ser chamado 1x (foi {read_count['n']}x)"
    )


@pytest.mark.unit
def test_get_tos_text_different_versions_separate_cache(_tos_dir) -> None:
    """Cache é versionado — v1.0.0 e v1.1.0 não interferem."""
    text_v1 = tos.get_tos_text("1.0.0")
    text_v11 = tos.get_tos_text("1.1.0")
    assert "v1.0.0" in text_v1
    assert "v1.1.0" in text_v11
    assert text_v1 != text_v11


@pytest.mark.unit
def test_clear_tos_cache(_tos_dir, monkeypatch: pytest.MonkeyPatch) -> None:
    """clear_tos_cache força re-read filesystem na próxima chamada."""
    read_count = {"n": 0}
    original_read = type(_tos_dir / "v1.0.0.md").read_text

    def counting_read(self, *args, **kwargs):
        read_count["n"] += 1
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr("pathlib.Path.read_text", counting_read)

    tos.get_tos_text("1.0.0")
    tos.clear_tos_cache()
    tos.get_tos_text("1.0.0")
    assert read_count["n"] == 2, "Após clear_tos_cache, read deve ser chamado novamente"
