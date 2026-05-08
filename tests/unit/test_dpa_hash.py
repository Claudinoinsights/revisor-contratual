"""Unit tests DPA hash + filesystem read (SP04-AUTH-01 AC-06 + AC-08).

Cobre helpers de ``bloco_auth/dpa.py`` sem requerer DB:
- ``compute_dpa_hash`` deterministic + NFC normalization + format SHA-256
- ``get_dpa_text`` filesystem read + cache TTL + missing version error
- Path traversal mitigation (semver regex)

Tests integration de POST /accept + GET /status persistence ficam em
test_auth_rls_isolation.py (chunk 4 — deferred até PostgreSQL).
"""

from __future__ import annotations

import unicodedata

import pytest

from bloco_auth import dpa


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    """Limpa cache filesystem entre tests."""
    dpa.clear_dpa_cache()
    yield
    dpa.clear_dpa_cache()


@pytest.fixture
def _dpa_dir(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Aponta DPA_TEMPLATES_DIR para tmp_path com v1.0.0.md fixture."""
    (tmp_path / "v1.0.0.md").write_text(
        "# DPA v1.0.0\n\nTexto canônico de teste com acentuação portuguesa.\n",
        encoding="utf-8",
    )
    (tmp_path / "v1.1.0.md").write_text(
        "# DPA v1.1.0\n\nVersão atualizada.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DPA_TEMPLATES_DIR", str(tmp_path))
    return tmp_path


@pytest.mark.unit
def test_dpa_hash_deterministic() -> None:
    """compute_dpa_hash chamado 2x retorna mesmo hash."""
    text = "DPA texto de exemplo"
    assert dpa.compute_dpa_hash(text) == dpa.compute_dpa_hash(text)


@pytest.mark.unit
def test_dpa_hash_unicode_normalization() -> None:
    """Texto NFD vs NFC produz MESMO hash (NFC normalization aplicada).

    "contratação" pode ser escrito como:
    - NFC: 'c' 'o' 'n' 't' 'r' 'a' 't' 'a' 'ç' 'ã' 'o' (ç = U+00E7)
    - NFD: 'c' 'o' 'n' 't' 'r' 'a' 't' 'a' 'c' '̧' 'a' '̃' 'o'
      (ç decomposto em c + cedilha combinante)

    Mesmo texto perceptível → bytes diferentes → hashes diferentes sem NFC.
    Com NFC, hash idêntico.
    """
    text_nfc = unicodedata.normalize("NFC", "contratação digital")
    text_nfd = unicodedata.normalize("NFD", "contratação digital")
    assert text_nfc != text_nfd, "Setup do teste precisa NFC != NFD"
    assert dpa.compute_dpa_hash(text_nfc) == dpa.compute_dpa_hash(text_nfd), (
        "NFC normalization deve produzir hash idêntico cross-OS"
    )


@pytest.mark.unit
def test_dpa_hash_format() -> None:
    """Hash retornado é 64 chars hex (SHA-256)."""
    h = dpa.compute_dpa_hash("qualquer texto")
    assert len(h) == 64, f"SHA-256 hex tem 64 chars, recebido {len(h)}"
    assert all(c in "0123456789abcdef" for c in h), "Hash deve ser hex lowercase"


@pytest.mark.unit
def test_dpa_hash_different_text_different_hash() -> None:
    """Textos diferentes → hashes diferentes."""
    h_a = dpa.compute_dpa_hash("texto A")
    h_b = dpa.compute_dpa_hash("texto B")
    assert h_a != h_b


@pytest.mark.unit
def test_get_dpa_text_existing_version(_dpa_dir) -> None:
    """Lê v1.0.0.md OK retorna conteúdo."""
    text = dpa.get_dpa_text("1.0.0")
    assert "DPA v1.0.0" in text
    assert "acentuação" in text


@pytest.mark.unit
def test_get_dpa_text_missing_version(_dpa_dir) -> None:
    """Version inexistente → FileNotFoundError com mensagem informativa."""
    with pytest.raises(FileNotFoundError, match=r"versão 9\.9\.9"):
        dpa.get_dpa_text("9.9.9")


@pytest.mark.unit
def test_get_dpa_text_invalid_version_format() -> None:
    """Version com path traversal attempt → ValueError (anti-traversal)."""
    with pytest.raises(ValueError, match="path-traversal|semver"):
        dpa.get_dpa_text("../../../etc/passwd")
    with pytest.raises(ValueError):
        dpa.get_dpa_text("1.0")  # não bate semver MAJOR.MINOR.PATCH
    with pytest.raises(ValueError):
        dpa.get_dpa_text("v1.0.0")  # prefix v não permitido no helper


@pytest.mark.unit
def test_get_dpa_text_cached(_dpa_dir, monkeypatch: pytest.MonkeyPatch) -> None:
    """Duas chamadas mesma version → 1 read filesystem (cache hit)."""
    read_count = {"n": 0}
    original_read = type(_dpa_dir / "v1.0.0.md").read_text

    def counting_read(self, *args, **kwargs):
        read_count["n"] += 1
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr("pathlib.Path.read_text", counting_read)

    text1 = dpa.get_dpa_text("1.0.0")
    text2 = dpa.get_dpa_text("1.0.0")
    assert text1 == text2
    assert read_count["n"] == 1, (
        f"Cache hit esperado: read_text deve ser chamado 1x (foi {read_count['n']}x)"
    )


@pytest.mark.unit
def test_get_dpa_text_different_versions_separate_cache(_dpa_dir) -> None:
    """Cache é versionado — v1.0.0 e v1.1.0 não interferem."""
    text_v1 = dpa.get_dpa_text("1.0.0")
    text_v11 = dpa.get_dpa_text("1.1.0")
    assert "v1.0.0" in text_v1
    assert "v1.1.0" in text_v11
    assert text_v1 != text_v11


@pytest.mark.unit
def test_clear_dpa_cache(_dpa_dir, monkeypatch: pytest.MonkeyPatch) -> None:
    """clear_dpa_cache força re-read filesystem na próxima chamada."""
    read_count = {"n": 0}
    original_read = type(_dpa_dir / "v1.0.0.md").read_text

    def counting_read(self, *args, **kwargs):
        read_count["n"] += 1
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr("pathlib.Path.read_text", counting_read)

    dpa.get_dpa_text("1.0.0")
    dpa.clear_dpa_cache()
    dpa.get_dpa_text("1.0.0")
    assert read_count["n"] == 2, "Após clear_dpa_cache, read deve ser chamado novamente"
