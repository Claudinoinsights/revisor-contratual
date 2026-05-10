"""Unit tests JWT encode/decode (SP04-AUTH-01 AC-05 + AC-08).

Cobre:
- Encode/decode roundtrip — claims preservados (tenant_id, user_id UUIDs)
- Expiry default 24h (Smith F-008 closure)
- Expired token rejection
- Tampered signature rejection
- Missing claim rejection
- SECRET_KEY < 32 bytes → ConfigError no startup

Cada teste roda com env JWT_SECRET_KEY válido injetado via fixture autouse.
``_load_secret.cache_clear()`` entre testes para evitar cache leakage.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt as _pyjwt
import pytest

from bloco_auth import jwt_utils
from bloco_auth.jwt_utils import (
    ConfigError,
    JWTError,
    JWTPayload,
    _load_secret,
    decode_jwt,
    encode_jwt,
)


_TEST_SECRET = "0123456789abcdef" * 4  # 64 chars utf-8 = 64 bytes (>= 32 mín.)


@pytest.fixture(autouse=True)
def _jwt_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setup env vars JWT válidas + reset cache antes de cada teste."""
    monkeypatch.setenv("JWT_SECRET_KEY", _TEST_SECRET)
    monkeypatch.setenv("JWT_EXPIRY_HOURS", "24")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    _load_secret.cache_clear()
    yield
    _load_secret.cache_clear()


@pytest.mark.unit
def test_encode_decode_roundtrip() -> None:
    """encode + decode → claims tenant_id, user_id preservados."""
    tid = uuid4()
    uid = uuid4()
    token = encode_jwt(tenant_id=tid, user_id=uid)
    payload = decode_jwt(token)
    assert isinstance(payload, JWTPayload)
    assert payload.tenant_id == tid
    assert payload.user_id == uid


@pytest.mark.unit
def test_jwt_expiry_24h_default() -> None:
    """exp = iat + 24h por default (Smith F-008 explicit).

    Margem de ±5s para clock drift entre encode e decode.
    """
    token = encode_jwt(tenant_id=uuid4(), user_id=uuid4())
    payload = decode_jwt(token)
    delta = payload.exp - payload.iat
    expected = timedelta(hours=24)
    assert abs(delta - expected) < timedelta(seconds=5), (
        f"exp - iat = {delta} (esperado ~{expected})"
    )


@pytest.mark.unit
def test_jwt_expired_rejection() -> None:
    """Token com exp no passado → JWTError 'JWT expirado'."""
    token = encode_jwt(tenant_id=uuid4(), user_id=uuid4(), expiry_hours=-1)
    with pytest.raises(JWTError, match="expirado"):
        decode_jwt(token)


@pytest.mark.unit
def test_jwt_tampered_signature_rejection() -> None:
    """Modificar payload do token → JWTError signature inválida.

    Tamperizamos um char no meio da seção payload (entre os dois pontos),
    o que muda o conteúdo decodificado e portanto invalida a HMAC. Modificar
    o último char do JWT pode não alterar bytes da signature em base64url
    porque os 2 bits finais são padding (43 chars × 6 bits = 258 bits, mas
    HMAC-SHA256 produz só 256 bits — 2 bits ignorados).
    """
    token = encode_jwt(tenant_id=uuid4(), user_id=uuid4())
    parts = token.split(".")
    assert len(parts) == 3, "JWT deve ter formato header.payload.signature"
    payload_part = parts[1]
    # Flip um char no meio do payload — base64url alphabet [A-Za-z0-9_-]
    middle = len(payload_part) // 2
    original_char = payload_part[middle]
    flipped_char = "Z" if original_char != "Z" else "Y"
    tampered_payload = payload_part[:middle] + flipped_char + payload_part[middle + 1 :]
    tampered = f"{parts[0]}.{tampered_payload}.{parts[2]}"
    with pytest.raises(JWTError):
        decode_jwt(tampered)


@pytest.mark.unit
def test_jwt_missing_claim_rejection() -> None:
    """Forge JWT manualmente sem ``tenant_id`` → JWTError claim ausente."""
    now = datetime.now(timezone.utc)
    forged_payload = {
        # tenant_id propositalmente ausente
        "user_id": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    forged_token = _pyjwt.encode(forged_payload, _TEST_SECRET, algorithm="HS256")
    with pytest.raises(JWTError, match="claim ausente|tenant_id"):
        decode_jwt(forged_token)


@pytest.mark.unit
def test_jwt_secret_key_too_short(monkeypatch: pytest.MonkeyPatch) -> None:
    """SECRET_KEY < 32 bytes → ConfigError no _load_secret."""
    monkeypatch.setenv("JWT_SECRET_KEY", "short")  # 5 bytes
    _load_secret.cache_clear()
    with pytest.raises(ConfigError, match=r"32 bytes|mínimo"):
        _load_secret()


@pytest.mark.unit
def test_jwt_secret_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """SECRET_KEY ausente → ConfigError no _load_secret."""
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    _load_secret.cache_clear()
    with pytest.raises(ConfigError, match=r"ausente|JWT_SECRET_KEY"):
        _load_secret()


@pytest.mark.unit
def test_jwt_validate_config_eager() -> None:
    """validate_config() executa _load_secret + checks (startup hook)."""
    # Deve completar sem raise quando env válido
    jwt_utils.validate_config()
