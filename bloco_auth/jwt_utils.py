"""JWT (HS256) encode/decode helpers — Sprint 04 multi-tenant auth (SP04-AUTH-01).

Emite tokens com claims ``{tenant_id, user_id, iat, exp}`` para autenticação
multi-tenant SaaS B2B. ``JWT_SECRET_KEY`` lido do environment com validação
eager (≥ 32 bytes) — falha cedo no startup é melhor que falha no primeiro
request prod (Story Risk #3 — JWT secret rotation).

Smith F-008 closure: ``JWT_EXPIRY_HOURS`` é env var explícita (default 24h).

Uso típico em rota de login::

    from bloco_auth.jwt_utils import encode_jwt, decode_jwt, JWTError

    token = encode_jwt(tenant_id=tenant.id, user_id=user.id)
    # ... return em response

    # Em rota autenticada:
    try:
        payload = decode_jwt(authorization_header.removeprefix("Bearer "))
    except JWTError as exc:
        raise HTTPException(401, detail=str(exc))

Cross-references:
    governance/stories/sp04-auth-01-multi-tenant-auth.md AC-05 + AC-08
    governance/architecture/adr/adr-017-multi-tenant-isolation-rls.md §4
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from uuid import UUID

import jwt as _pyjwt  # PyJWT
from pydantic import BaseModel, ConfigDict, field_validator


_DEFAULT_EXPIRY_HOURS = 24
_DEFAULT_ALGORITHM = "HS256"
_MIN_SECRET_BYTES = 32


class ConfigError(RuntimeError):
    """Configuração JWT inválida ou ausente no environment."""


class JWTError(Exception):
    """Falha ao encode/decode JWT — wrapper das ``InvalidTokenError`` de PyJWT.

    Engloba: token malformado, signature inválida, exp passado, claim missing,
    algoritmo não permitido. Mensagem detalha causa raiz para audit log
    (sem vazar SECRET_KEY).
    """


class JWTPayload(BaseModel):
    """Payload tipado de JWT decodificado (SP04-AUTH-01 schema canônico).

    Pydantic ``BaseModel`` (consistente com codebase) — runtime validation
    converte ``str`` UUIDs do JSON em ``UUID`` Python e ``int`` Unix timestamps
    em ``datetime`` timezone-aware (UTC).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: UUID
    user_id: UUID
    iat: datetime
    exp: datetime

    @field_validator("iat", "exp", mode="before")
    @classmethod
    def _coerce_unix_to_datetime(cls, value: object) -> object:
        """Converte ``int`` Unix timestamp em ``datetime`` UTC.

        PyJWT codifica ``iat`` / ``exp`` como ``int``. Pydantic não converte
        automaticamente — precisamos mapear explicitamente.
        """
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        return value


@lru_cache(maxsize=1)
def _load_secret() -> bytes:
    """Lê e valida ``JWT_SECRET_KEY`` do environment (cached).

    Validação eager (≥ 32 bytes). Tests resetam cache via
    ``_load_secret.cache_clear()`` + ``monkeypatch.setenv``.

    Raises:
        ConfigError: se ``JWT_SECRET_KEY`` ausente OR < 32 bytes.
    """
    raw = os.getenv("JWT_SECRET_KEY")
    if raw is None or raw == "":
        raise ConfigError(
            "JWT_SECRET_KEY ausente no environment. "
            "Gere via: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    secret = raw.encode("utf-8")
    if len(secret) < _MIN_SECRET_BYTES:
        raise ConfigError(
            f"JWT_SECRET_KEY tem {len(secret)} bytes — mínimo {_MIN_SECRET_BYTES} bytes "
            "(HS256 com chave fraca permite brute force). Gere via secrets.token_hex(32)."
        )
    return secret


def _get_expiry_hours() -> int:
    raw = os.getenv("JWT_EXPIRY_HOURS")
    if raw is None or raw == "":
        return _DEFAULT_EXPIRY_HOURS
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"JWT_EXPIRY_HOURS inválido: {raw!r}") from exc
    if value <= 0:
        raise ConfigError(f"JWT_EXPIRY_HOURS deve ser > 0 — recebido {value}")
    return value


def _get_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", _DEFAULT_ALGORITHM)


def encode_jwt(
    tenant_id: UUID,
    user_id: UUID,
    expiry_hours: int | None = None,
) -> str:
    """Emite JWT HS256 com claims tenant_id, user_id, iat, exp.

    Args:
        tenant_id: UUID do tenant (escritório).
        user_id: UUID do user (advogado interno).
        expiry_hours: override do default (env ``JWT_EXPIRY_HOURS`` ou 24).

    Returns:
        Token JWT serializado como string.
    """
    now = datetime.now(timezone.utc)
    hours = expiry_hours if expiry_hours is not None else _get_expiry_hours()
    payload = {
        "tenant_id": str(tenant_id),
        "user_id": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=hours)).timestamp()),
    }
    return _pyjwt.encode(payload, _load_secret(), algorithm=_get_algorithm())


def decode_jwt(token: str) -> JWTPayload:
    """Decoda + verifica JWT HS256.

    Args:
        token: JWT serializado.

    Returns:
        Payload tipado (UUIDs convertidos, timestamps em datetime UTC).

    Raises:
        JWTError: signature inválida, exp passado, claim missing, formato
            errado, algoritmo não permitido.
    """
    try:
        raw_payload = _pyjwt.decode(
            token,
            _load_secret(),
            algorithms=[_get_algorithm()],
            options={"require": ["tenant_id", "user_id", "iat", "exp"]},
        )
    except _pyjwt.ExpiredSignatureError as exc:
        raise JWTError("JWT expirado") from exc
    except _pyjwt.InvalidSignatureError as exc:
        raise JWTError("JWT signature inválida") from exc
    except _pyjwt.MissingRequiredClaimError as exc:
        raise JWTError(f"JWT claim ausente: {exc.claim}") from exc
    except _pyjwt.InvalidTokenError as exc:
        raise JWTError(f"JWT inválido: {exc}") from exc

    try:
        return JWTPayload.model_validate(raw_payload)
    except Exception as exc:
        raise JWTError(f"JWT payload inválido após decode: {exc}") from exc


def validate_config() -> None:
    """Hook de startup explícito para falha eager em produção.

    Chamar uma vez no boot do app (ex.: ``bloco_interface/web/app.py``) para
    abortar startup se ``JWT_SECRET_KEY`` ausente ou fraca. Após primeiro call,
    ``_load_secret`` cache mantém valor para reuse em encode/decode.
    """
    _load_secret()
    _get_expiry_hours()
    _get_algorithm()


__all__ = [
    "ConfigError",
    "JWTError",
    "JWTPayload",
    "encode_jwt",
    "decode_jwt",
    "validate_config",
]
