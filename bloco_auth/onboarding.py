"""Onboarding wizard 4 passos (SP04-AUTH-01 AC-01).

State machine in-memory por session_id. Sprint 05+ promove para Redis ou
PostgreSQL. Sequência:

    Step 1 — Dados escritório (CNPJ + razão social + advogado responsável + email + senha)
    Step 2 — Anthropic API key (validada via ping HTTP)
    Step 3 — DPA acceptance (chunk 5 implementa hash flow completo)
    Step 4 — Tier selection (Starter/Pro/Enterprise)

``complete_onboarding`` finaliza wizard atomicamente: persiste tenant + first
user (advogado responsável) em transaction, audita evento ``tenant_signup``.

Cross-references:
    governance/stories/sp04-auth-01-multi-tenant-auth.md AC-01, AC-02
    governance/architecture/adr/adr-019-dpa-storage-schema.md (chunk 5)
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Literal

import httpx
from fastapi import Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from bloco_auth.byok_encryption import encrypt_api_key, truncate_fingerprint
from bloco_auth.models import Tenant, TenantAPIKey, User
from bloco_auth.passwords import hash_password


_ANTHROPIC_PING_URL = "https://api.anthropic.com/v1/models"
_ANTHROPIC_PING_TIMEOUT_S = 10.0
_CNPJ_DIGITS_RE = re.compile(r"^\d{14}$")


class OnboardingError(RuntimeError):
    """Erro genérico do fluxo de onboarding."""


class OnboardingStep1Data(BaseModel):
    """Step 1 — Dados do escritório de advocacia."""

    model_config = ConfigDict(extra="forbid")

    cnpj: str = Field(..., min_length=14, max_length=14, description="CNPJ unformatted (14 dígitos)")
    razao_social: str = Field(..., min_length=3, max_length=500)
    advogado_responsavel: str = Field(..., min_length=3, max_length=200)
    email: EmailStr
    senha: str = Field(..., min_length=8, max_length=72)

    @field_validator("cnpj", mode="before")
    @classmethod
    def _strip_cnpj(cls, value: object) -> object:
        """Remove formatação ``00.000.000/0000-00`` antes de validar 14 dígitos."""
        if isinstance(value, str):
            return re.sub(r"\D", "", value)
        return value

    @field_validator("cnpj")
    @classmethod
    def _validate_cnpj_digits(cls, value: str) -> str:
        if not _CNPJ_DIGITS_RE.match(value):
            raise ValueError("CNPJ deve ter 14 dígitos")
        if not validate_cnpj(value):
            raise ValueError("CNPJ inválido (dígito verificador)")
        return value


class OnboardingStep2Data(BaseModel):
    """Step 2 — API key Anthropic (validada via ping HTTP)."""

    model_config = ConfigDict(extra="forbid")

    anthropic_api_key: str = Field(..., min_length=10, max_length=200)


class OnboardingStep3Data(BaseModel):
    """Step 3 — DPA acceptance (chunk 5 implementa flow completo)."""

    model_config = ConfigDict(extra="forbid")

    dpa_version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semver da DPA aceita")
    accepted: bool


class OnboardingStep4Data(BaseModel):
    """Step 4 — Tier selection (pricing TBD cross-domain Mifune business)."""

    model_config = ConfigDict(extra="forbid")

    tier: Literal["Starter", "Pro", "Enterprise"]


# ──────────────────────────────────────────────────────────────────────────────
# CNPJ validator — algoritmo dígito verificador BR módulo 11
# ──────────────────────────────────────────────────────────────────────────────


def validate_cnpj(cnpj: str) -> bool:
    """Valida CNPJ brasileiro via algoritmo dígito verificador módulo 11.

    Args:
        cnpj: 14 dígitos sem formatação.

    Returns:
        ``True`` se dígitos verificadores conferem.
    """
    if len(cnpj) != 14 or not cnpj.isdigit():
        return False
    # Rejeita CNPJs com todos dígitos iguais (ex.: 00000000000000)
    if cnpj == cnpj[0] * 14:
        return False

    def _digit(base: list[int], weights: list[int]) -> int:
        soma = sum(b * w for b, w in zip(base, weights))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    base = [int(d) for d in cnpj[:12]]
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    d1 = _digit(base, weights1)
    if d1 != int(cnpj[12]):
        return False
    d2 = _digit(base + [d1], weights2)
    return d2 == int(cnpj[13])


# ──────────────────────────────────────────────────────────────────────────────
# Anthropic API key ping (SP04-AUTH-01 AC-01b)
# ──────────────────────────────────────────────────────────────────────────────


async def ping_anthropic_api(api_key: str) -> bool:
    """Valida Anthropic API key via GET ``/v1/models``.

    Args:
        api_key: chave Anthropic do escritório.

    Returns:
        ``True`` se 200 OK; ``False`` se 401/403 (chave inválida) ou erro de
        rede (mantém sinal binário — Sprint 05+ pode introduzir status codes
        mais ricos para UX explicar "Anthropic indisponível" vs "chave ruim").
    """
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    try:
        async with httpx.AsyncClient(timeout=_ANTHROPIC_PING_TIMEOUT_S) as client:
            response = await client.get(_ANTHROPIC_PING_URL, headers=headers)
            return response.status_code == 200
    except httpx.HTTPError:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# State machine in-memory (Sprint 05+ promove Redis/PostgreSQL)
# ──────────────────────────────────────────────────────────────────────────────


_SESSIONS: dict[str, dict[str, Any]] = {}


def start_session(step1: OnboardingStep1Data) -> str:
    """Cria sessão de onboarding e armazena step1.

    Returns:
        ``session_id`` UUID4 para continuação do wizard.
    """
    session_id = str(uuid.uuid4())
    _SESSIONS[session_id] = {"step1": step1, "step2": None, "step3": None, "step4": None}
    return session_id


def store_step(session_id: str, step_n: int, data: BaseModel) -> None:
    """Armazena dado do step N na sessão.

    Raises:
        OnboardingError: session_id desconhecida OR step anterior não preenchido.
    """
    session = _SESSIONS.get(session_id)
    if session is None:
        raise OnboardingError(f"Sessão {session_id} não encontrada (expirada ou inválida)")
    if step_n not in (2, 3, 4):
        raise OnboardingError(f"Step {step_n} inválido (1 inicia via start_session)")
    prev_key = f"step{step_n - 1}"
    if session.get(prev_key) is None:
        raise OnboardingError(
            f"Step {step_n - 1} não completado — ordem sequencial obrigatória"
        )
    session[f"step{step_n}"] = data


def get_session(session_id: str) -> dict[str, Any]:
    """Retorna sessão raw (testing/inspection helper)."""
    session = _SESSIONS.get(session_id)
    if session is None:
        raise OnboardingError(f"Sessão {session_id} não encontrada")
    return session


def reset_sessions() -> None:
    """Limpa todas as sessões (uso em tests integration)."""
    _SESSIONS.clear()


# ──────────────────────────────────────────────────────────────────────────────
# complete_onboarding — finaliza wizard atomicamente
# ──────────────────────────────────────────────────────────────────────────────


async def complete_onboarding(
    session_id: str,
    db_session: AsyncSession,
    request: Request | None = None,
) -> tuple[Tenant, User]:
    """Persiste tenant + first user + dpa_acceptance atomicamente (triple insert).

    Pre-requisitos: todos 4 steps completos no state machine. Caller é
    responsável por verificar antes de chamar (rota POST /api/onboarding/step4
    valida).

    Triple insert em single transaction (chunk 5 — fecha AC-06):
      1. Tenant
      2. User (advogado responsável)
      3. DpaAcceptance (via dpa.accept_dpa) com IP + user_agent capture

    Falha em qualquer passo rollback completo — tenant órfão sem user OR
    sem DPA acceptance é estado inválido (compliance LGPD).

    Args:
        session_id: UUID da sessão de onboarding.
        db_session: AsyncSession SQLAlchemy (sem RLS context — tenant ainda
            não existe; criação inicial usa role com BYPASSRLS OR superuser).
        request: FastAPI Request (opcional — capture IP/user_agent no DPA
            acceptance). Quando ``None``, campos ficam null no audit DPA.

    Returns:
        ``(tenant, user)`` recém-criados.

    Raises:
        OnboardingError: sessão incompleta OR violação UNIQUE (CNPJ/email já
            cadastrados) OR DPA texto canônico ausente.
    """
    # Import lazy para evitar ciclo (dpa.py importa onboarding indiretamente
    # via api.py routing? não — mas mantemos defensive). Função interna.
    from bloco_auth import dpa as _dpa

    session = _SESSIONS.get(session_id)
    if session is None:
        raise OnboardingError(f"Sessão {session_id} não encontrada")

    step1: OnboardingStep1Data | None = session.get("step1")
    step2: OnboardingStep2Data | None = session.get("step2")
    step3: OnboardingStep3Data | None = session.get("step3")
    step4: OnboardingStep4Data | None = session.get("step4")
    if step1 is None or step2 is None or step3 is None or step4 is None:
        raise OnboardingError("Wizard incompleto — todos 4 steps devem ser preenchidos")
    if not step3.accepted:
        raise OnboardingError("DPA não aceita — onboarding bloqueado")

    # Quadruple insert atomic — single transaction (SP04-BYOK-01 chunk 4 extension)
    # Sequência: tenant → user → dpa_acceptance → tenant_api_keys (encrypted)
    async with db_session.begin():
        tenant = Tenant(
            cnpj=step1.cnpj,
            razao_social=step1.razao_social,
            advogado_responsavel=step1.advogado_responsavel,
            email=step1.email,
            status="active",
        )
        db_session.add(tenant)
        await db_session.flush()  # gera tenant.id sem commit

        user = User(
            tenant_id=tenant.id,
            email=step1.email,
            password_hash=hash_password(step1.senha),
            nome=step1.advogado_responsavel,
            status="active",
        )
        db_session.add(user)
        await db_session.flush()  # gera user.id sem commit

        # Triple insert step 3 — DPA acceptance (AUTH-01 chunk 5 / AC-06)
        # Falha aqui (texto inexistente, hash compute error) rollback completo.
        try:
            await _dpa.accept_dpa(
                tenant_id=tenant.id,
                user_id=user.id,
                version=step3.dpa_version,
                request=request,
                db_session=db_session,
            )
        except FileNotFoundError as exc:
            raise OnboardingError(
                f"DPA texto canônico v{step3.dpa_version} não encontrado — "
                f"onboarding bloqueado. Detalhe: {exc}"
            ) from exc

        # Quadruple insert step 4 — BYOK encrypted api_key (SP04-BYOK-01 chunk 4 / AC-03)
        # Tank Phase 12.3a — quadruple insert atomic (rollback completo se encrypt falha).
        # Audit chain event byok_key_set é emitido em chunk 7 via byok_lifecycle helper
        # (separação de concern — lifecycle audit centralizado em byok_lifecycle.py).
        plain_api_key = step2.anthropic_api_key
        encrypted = await encrypt_api_key(plain_api_key, db_session)
        fingerprint = truncate_fingerprint(plain_api_key)

        db_session.add(TenantAPIKey(
            tenant_id=tenant.id,
            encrypted_key=encrypted,
            key_fingerprint=fingerprint,
            status="active",
        ))
        await db_session.flush()

    # Sessão finalizada — limpa
    _SESSIONS.pop(session_id, None)
    return tenant, user


__all__ = [
    "OnboardingError",
    "OnboardingStep1Data",
    "OnboardingStep2Data",
    "OnboardingStep3Data",
    "OnboardingStep4Data",
    "validate_cnpj",
    "ping_anthropic_api",
    "start_session",
    "store_step",
    "get_session",
    "reset_sessions",
    "complete_onboarding",
]
