"""FastAPI routers — Auth + Onboarding + Users CRUD (SP04-AUTH-01 AC-01/04/05/07).

Endpoints sob ``/api`` prefix (registrado em ``bloco_interface/web/app.py``):

    Auth:
      POST /auth/signup          — inicia onboarding (step 1)
      POST /auth/login           — emite JWT
      POST /auth/logout          — JWT stateless, audit only

    Onboarding (sequencial, requer session_id de signup):
      POST /onboarding/step2     — Anthropic API key
      POST /onboarding/step3     — DPA acceptance (chunk 5 hash flow completo)
      POST /onboarding/step4     — Tier selection + finaliza (auto-login)

    Users CRUD (RLS scoped, requer JWT):
      POST /tenant/users         — criar
      GET  /tenant/users         — listar (RLS auto-filtra)
      PATCH /tenant/users/{id}   — update
      DELETE /tenant/users/{id}  — soft-delete

Audit chain integration: cada endpoint registra event via
``bloco_audit.chain.append_audit_entry`` com payload contendo ``tenant_id``
e ``user_id`` (ADR-005 + ADR-017 §6 preservado).

Cross-references:
    governance/stories/sp04-auth-01-multi-tenant-auth.md AC-01/04/05/07
    governance/architecture/adr/adr-017-multi-tenant-isolation-rls.md §4-6
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bloco_audit.chain import append_audit_entry
from bloco_auth.db import get_sessionmaker, with_tenant_context
from bloco_auth.jwt_utils import encode_jwt
from bloco_auth.middleware import get_current_user
from bloco_auth.models import Tenant, User
from bloco_auth.onboarding import (
    OnboardingError,
    OnboardingStep1Data,
    OnboardingStep2Data,
    OnboardingStep3Data,
    OnboardingStep4Data,
    complete_onboarding,
    ping_anthropic_api,
    start_session,
    store_step,
)
from bloco_auth.passwords import hash_password, verify_password


router = APIRouter(prefix="/api", tags=["auth"])


# ──────────────────────────────────────────────────────────────────────────────
# Response models (Pydantic)
# ──────────────────────────────────────────────────────────────────────────────


class SignupResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    next_url: str = "/api/onboarding/step2"


class StepResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    next_url: str | None
    step_completed: int


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    senha: str = Field(..., min_length=1, max_length=72)


class LoginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str
    token_type: Literal["Bearer"] = "Bearer"
    tenant_id: UUID
    user_id: UUID


class CompleteOnboardingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: UUID
    user_id: UUID
    token: str  # auto-login post-onboarding (UX friendly)


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    senha: str = Field(..., min_length=8, max_length=72)
    nome: str = Field(..., min_length=1, max_length=200)


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nome: str | None = Field(default=None, max_length=200)
    email: EmailStr | None = None
    status: Literal["active", "suspended"] | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    tenant_id: UUID
    email: str
    nome: str
    status: str


# ──────────────────────────────────────────────────────────────────────────────
# Helper — audit chain wrapper (Sprint 04 multi-tenant payload)
# ──────────────────────────────────────────────────────────────────────────────


def _audit(
    event_type: str,
    tenant_id: UUID | None,
    user_id: UUID | None,
    request: Request | None = None,
    extra: dict | None = None,
) -> None:
    """Append audit chain entry com payload multi-tenant (ADR-017 §6)."""
    payload: dict = {}
    if tenant_id is not None:
        payload["tenant_id"] = str(tenant_id)
    if user_id is not None:
        payload["user_id"] = str(user_id)
    if request is not None:
        payload["ip_address"] = request.client.host if request.client else None
        payload["user_agent"] = request.headers.get("user-agent")
    if extra:
        payload.update(extra)
    try:
        append_audit_entry(event_type, payload)
    except Exception:  # noqa: BLE001 — audit best-effort: nunca derruba request
        # CC.39 hardening pattern Sprint 03: audit errors NÃO bloqueiam funcionalidade
        # core. Logar via structlog seria ideal mas evita coupling neste módulo.
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Auth — signup, login, logout
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/auth/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(data: OnboardingStep1Data, request: Request) -> SignupResponse:
    """Inicia onboarding wizard — armazena step 1 in-memory + retorna session_id."""
    session_id = start_session(data)
    _audit("tenant_signup_started", tenant_id=None, user_id=None, request=request,
           extra={"cnpj": data.cnpj, "session_id": session_id})
    return SignupResponse(session_id=session_id)


@router.post("/auth/login", response_model=LoginResponse)
async def login(data: LoginRequest, request: Request) -> LoginResponse:
    """Login cross-tenant — lookup user por email global + bcrypt verify + JWT 24h."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        # Cross-tenant lookup — sem RLS context (tenant ainda não autenticado).
        # users.email é UNIQUE per-tenant; tenants.email é UNIQUE GLOBAL —
        # combinação previne ambiguidade na prática (advogado responsável de
        # tenant é também user com mesma email; fallback de busca em users).
        # Nota: chamada SEM with_tenant_context — RLS bloqueia se policy ativa.
        # Para login funcionar, role do app deve ter BYPASSRLS OU policy
        # condicional `current_setting('app.tenant_id', true) IS NULL`.
        # Migration usa current_setting(..., true) (missing_ok) — quando var
        # ausente retorna NULL e USING fica `tenant_id = NULL::uuid` que é
        # FALSE para todas as rows. CONCLUSÃO: login precisa de role BYPASSRLS
        # OU SET app.tenant_id = '<query-time>' para liberar lookup.
        # MITIGAÇÃO PRAGMÁTICA: usar SET LOCAL com tenant_id=NULL não funciona;
        # usar role com BYPASSRLS é setup ops. Sprint 04 chunk 4 documenta isso
        # como TECH-DEBT — ver Risk Assessment seção #1 mitigation deferred.
        # Para tests integration: usar superuser ou role BYPASSRLS no DATABASE_URL.
        result = await session.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

    if user is None or not verify_password(data.senha, user.password_hash):
        # Mensagem genérica anti enumeration (Story Risk #5)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
        )
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Conta suspensa"
        )

    token = encode_jwt(tenant_id=user.tenant_id, user_id=user.id)
    _audit("user_login", user.tenant_id, user.id, request)
    return LoginResponse(token=token, tenant_id=user.tenant_id, user_id=user.id)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> Response:
    """JWT stateless logout — client-side token discard. Audit only."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        # Best-effort: tenta extrair tenant/user para audit; ignora erro
        try:
            from bloco_auth.jwt_utils import decode_jwt

            payload = decode_jwt(auth_header[len("Bearer ") :].strip())
            _audit("user_logout", payload.tenant_id, payload.user_id, request)
        except Exception:  # noqa: BLE001
            _audit("user_logout_unauthenticated", None, None, request)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


# ──────────────────────────────────────────────────────────────────────────────
# Onboarding — sequential steps 2-4
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/onboarding/step2", response_model=StepResponse)
async def onboarding_step2(
    data: OnboardingStep2Data, session_id: str, request: Request
) -> StepResponse:
    """Step 2 — Anthropic API key + ping HTTP validation."""
    is_valid = await ping_anthropic_api(data.anthropic_api_key)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anthropic API key inválida ou serviço indisponível",
        )
    try:
        store_step(session_id, 2, data)
    except OnboardingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    _audit("onboarding_step2_completed", None, None, request,
           extra={"session_id": session_id})
    return StepResponse(session_id=session_id, next_url="/api/onboarding/step3", step_completed=2)


@router.post("/onboarding/step3", response_model=StepResponse)
async def onboarding_step3(
    data: OnboardingStep3Data, session_id: str, request: Request
) -> StepResponse:
    """Step 3 — DPA + TOS acceptance combined (Sati Opção B antecipada — SP04-LGPD-01 AC-04).

    Originalmente apenas DPA (AUTH-01 chunk 5). LGPD-01 chunk 4 adiciona TOS/EULA
    no mesmo step (menor friction onboarding; texto único legal Eric advogado
    pode estruturar com headers DPA e TOS sequential).
    """
    if not data.accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DPA deve ser aceita para prosseguir",
        )
    if not data.tos_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOS/EULA deve ser aceito para prosseguir",
        )
    try:
        store_step(session_id, 3, data)
    except OnboardingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    _audit("onboarding_step3_completed", None, None, request,
           extra={
               "session_id": session_id,
               "dpa_version": data.dpa_version,
               "tos_version": data.tos_version,
           })
    return StepResponse(session_id=session_id, next_url="/api/onboarding/step4", step_completed=3)


@router.post("/onboarding/step4", response_model=CompleteOnboardingResponse)
async def onboarding_step4(
    data: OnboardingStep4Data, session_id: str, request: Request
) -> CompleteOnboardingResponse:
    """Step 4 — Tier + finaliza wizard atomicamente + auto-login."""
    try:
        store_step(session_id, 4, data)
    except OnboardingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db_session:
        try:
            # Chunk 5: triple insert atomic (tenant + user + dpa_acceptance)
            # — request passado para capture IP + user_agent no DPA accept
            tenant, user = await complete_onboarding(
                session_id, db_session, request=request
            )
        except OnboardingError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc
        except IntegrityError as exc:
            await db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="CNPJ ou email já cadastrados",
            ) from exc

    token = encode_jwt(tenant_id=tenant.id, user_id=user.id)
    _audit("tenant_signup", tenant.id, user.id, request,
           extra={"cnpj": tenant.cnpj, "tier": data.tier})
    return CompleteOnboardingResponse(tenant_id=tenant.id, user_id=user.id, token=token)


# ──────────────────────────────────────────────────────────────────────────────
# Tenant Users CRUD (RLS scoped via Depends + apply_rls_context)
# ──────────────────────────────────────────────────────────────────────────────


@router.post(
    "/tenant/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    data: UserCreateRequest,
    request: Request,
    current: tuple[UUID, UUID] = Depends(get_current_user),
) -> UserResponse:
    """Criar user dentro do tenant atual (RLS auto-aplica via apply_rls_context)."""
    tenant_id, _ = current
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session, with_tenant_context(session, tenant_id):
        new_user = User(
            tenant_id=tenant_id,
            email=data.email,
            password_hash=hash_password(data.senha),
            nome=data.nome,
            status="active",
        )
        session.add(new_user)
        try:
            await session.flush()
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email já cadastrado neste escritório",
            ) from exc
        await session.refresh(new_user)
        _audit("user_created", tenant_id, new_user.id, request)
        return UserResponse.model_validate(new_user)


@router.get("/tenant/users", response_model=list[UserResponse])
async def list_users(
    current: tuple[UUID, UUID] = Depends(get_current_user),
) -> list[UserResponse]:
    """Listar users do tenant atual (RLS filtra automaticamente)."""
    tenant_id, _ = current
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session, with_tenant_context(session, tenant_id):
        result = await session.execute(select(User))
        users = result.scalars().all()
        return [UserResponse.model_validate(u) for u in users]


@router.patch("/tenant/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdateRequest,
    request: Request,
    current: tuple[UUID, UUID] = Depends(get_current_user),
) -> UserResponse:
    """Update user — RLS impede tocar user de outro tenant (404 ao invés de 403)."""
    tenant_id, _ = current
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session, with_tenant_context(session, tenant_id):
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User não encontrado")
        if data.nome is not None:
            user.nome = data.nome
        if data.email is not None:
            user.email = data.email
        if data.status is not None:
            user.status = data.status
        try:
            await session.flush()
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado"
            ) from exc
        await session.refresh(user)
        _audit("user_updated", tenant_id, user.id, request)
        return UserResponse.model_validate(user)


@router.delete("/tenant/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    request: Request,
    current: tuple[UUID, UUID] = Depends(get_current_user),
) -> Response:
    """Soft-delete user (status='suspended') — preserva audit history."""
    tenant_id, _ = current
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session, with_tenant_context(session, tenant_id):
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User não encontrado")
        user.status = "suspended"
        await session.flush()
        _audit("user_suspended", tenant_id, user.id, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router"]
