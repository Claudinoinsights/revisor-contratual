"""SQLAlchemy 2.0 async ORM models para Sprint 04 multi-tenant auth (SP04-AUTH-01).

Espelha o schema canônico definido em
``bloco_database/migrations/sp04_001_auth_multitenant.sql`` (single source of
truth para DDL, RLS policies, indexes). Os modelos abaixo são apenas a
representação Python — RLS é aplicada exclusivamente em nível PostgreSQL via
``current_setting('app.tenant_id')`` setado pelo middleware (chunk 3+).

Cross-references:
    governance/stories/sp04-auth-01-multi-tenant-auth.md (AC-02, AC-03)
    governance/architecture/adr/adr-017-multi-tenant-isolation-rls.md
    governance/architecture/adr/adr-019-dpa-storage-schema.md
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import INET, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base do bloco_auth (schema multi-tenant Sprint 04)."""


class Tenant(Base):
    """Escritório de advocacia — entidade raiz do isolamento multi-tenant.

    Status enumerável (texto livre por enquanto): ``active``, ``suspended``,
    ``dpa_pending`` (transição quando DPA MAJOR exige re-aceite — ADR-019 §5).
    """

    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    razao_social: Mapped[str] = mapped_column(Text, nullable=False)
    advogado_responsavel: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    users: Mapped[list[User]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    dpa_acceptances: Mapped[list[DpaAcceptance]] = relationship(
        back_populates="tenant",
        cascade="save-update",
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} cnpj={self.cnpj} status={self.status}>"


class User(Base):
    """Advogado interno do escritório — escopo de acesso definido pelo ``tenant_id``.

    O password_hash é bcrypt cost factor 12 (Story SP04-AUTH-01 AC-03 + crítico
    cenário #3 — cost < 12 deve falhar test em chunk 3).
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="unique_email_per_tenant"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    tenant: Mapped[Tenant] = relationship(back_populates="users")

    def __repr__(self) -> str:
        return f"<User id={self.id} tenant_id={self.tenant_id} email={self.email}>"


class DpaAcceptance(Base):
    """Evidence LGPD ANPD da aceitação do DPA por um user de um tenant (ADR-019).

    Retention PERMANENT — FKs em ``ON DELETE RESTRICT`` impedem DELETE direto
    mesmo após off-boarding do tenant. Strategy de archive (cold storage) cabe
    a story posterior — esta tabela é write-once, audit-ready.
    """

    __tablename__ = "dpa_acceptances"
    __table_args__ = (
        UniqueConstraint("tenant_id", "dpa_version", name="unique_tenant_version"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    dpa_version: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    dpa_text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    accepted_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    tenant: Mapped[Tenant] = relationship(back_populates="dpa_acceptances")

    def __repr__(self) -> str:
        return (
            f"<DpaAcceptance id={self.id} tenant_id={self.tenant_id} "
            f"version={self.dpa_version}>"
        )


__all__ = ["Base", "Tenant", "User", "DpaAcceptance"]
