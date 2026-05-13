"""CLI subgroup ``revisor analytics`` — TD-SP04-04-ANALYTICS Chunk 4.

8 commands per Sati Eixo 5 + Constitution Art. I CLI First:

  drop-off          FR-ANALYTICS-01 — drop-off rate per doctype
  tti               FR-ANALYTICS-02 — TTI percentile (p50/p90/p99)
  geral-pct         FR-ANALYTICS-03 — % first-selection Geral
  reclassification  FR-ANALYTICS-04 — from→to matrix
  pareto            FR-ANALYTICS-05 — distribution Top-3 + Tail
  privacy-audit     NFR-PRIVACY-01 — 9 PII vectors compliance check
  chain-verify      NFR-PRIVACY-01.6 — HMAC chain integrity
  health            NFR-OBSERVABILITY-01 — operational metadata

Output formats: ``--format=json|text|table`` (default JSON).
Threshold compliance: PASS/FAIL com action recommendation (Sati ratify).

REUSE pattern: bloco_interface/cli.py async via asyncio.run; queries SQL diretas
via bloco_auth.db.get_engine() (psycopg async driver). RLS aplicado via
``with_tenant_context`` quando tenant_id known; admin queries cross-tenant
(privacy-audit, chain-verify) operam SEM RLS context (require AUTH_COOKIE_KEY).
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import click
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from bloco_auth.analytics import verify_chain_integrity
from bloco_auth.db import get_sessionmaker, with_tenant_context


# ──────────────────────────────────────────────────────────────────────────────
# Thresholds — PRD v2.0.5.1 §2 FRs + Sati ratify post-hoc Eixo 5
# ──────────────────────────────────────────────────────────────────────────────

_THRESHOLD_DROPOFF_MAX = 0.15        # AC-2: ≤15% PASS
_THRESHOLD_TTI_P90_MAX_SEC = 90      # AC-4: ≤90s PASS (p90)
_THRESHOLD_GERAL_MAX = 0.10          # AC-6: ≤10% PASS
_THRESHOLD_RECLASS_MAX = 0.05        # AC-8: ≤5% PASS
_THRESHOLD_PARETO_TOP3_MIN = 0.60    # AC-10: Top-3 ≥60% PASS
_THRESHOLD_PARETO_TAIL_MIN = 0.05    # AC-10: Cauda ≥5% PASS

_VALID_DOCTYPES = ("ccb", "veiculo", "consignado", "cartao", "imobiliario", "fies", "geral")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers — period parsing + output formatting
# ──────────────────────────────────────────────────────────────────────────────


def _parse_period(period: str) -> int:
    """Parse ``7d``, ``30d``, ``90d`` → days int. Sentinel for SQL interval."""
    m = re.fullmatch(r"(\d+)d", period.strip().lower())
    if not m:
        raise click.BadParameter(f"period inválido: '{period}'. Use formato Nd (ex: 7d, 30d).")
    days = int(m.group(1))
    if days <= 0 or days > 365:
        raise click.BadParameter(f"period fora do range 1d-365d: '{period}'")
    return days


def _emit(payload: dict, fmt: str) -> None:
    """Emit payload no formato escolhido (json/text/table)."""
    if fmt == "json":
        click.echo(json.dumps(payload, indent=2, default=str, ensure_ascii=False))
    elif fmt == "text":
        for k, v in payload.items():
            click.echo(f"{k}: {v}")
    elif fmt == "table":
        # Simple 2-col table — keys + values left-aligned
        max_k = max((len(str(k)) for k in payload.keys()), default=0)
        for k, v in payload.items():
            click.echo(f"{str(k).ljust(max_k)}  {v}")
    else:
        raise click.BadParameter(f"format inválido: '{fmt}'")


def _verdict(passed: bool, action_if_fail: str) -> dict[str, str]:
    """Threshold verdict + action recommendation (Sati ratify)."""
    return {
        "verdict": "PASS" if passed else "FAIL",
        "action_recommendation": "" if passed else action_if_fail,
    }


_ADMIN_WARN_EMITTED = False


def _emit_admin_warn_once() -> None:
    """Smith H3 fix Fase 4.5b — warn admin role pending (lowered to MED-warn-only).

    Print stderr WARNING once per CLI invocation antes de queries cross-tenant.
    Full fix Sprint 6+: TD-ANALYTICS-L5 (`analytics_admin BYPASSRLS` role).
    """
    global _ADMIN_WARN_EMITTED
    if _ADMIN_WARN_EMITTED:
        return
    click.echo(
        "⚠️  Admin role pending (TD-ANALYTICS-L5 Sprint 6+). "
        "Results may be empty se DATABASE_URL não é super OR sem BYPASSRLS attribute.",
        err=True,
    )
    _ADMIN_WARN_EMITTED = True


async def _run_admin_query(query: str, params: dict[str, Any] | None = None) -> Any:
    """Execute admin query — cross-tenant analytics queries usadas por CLI.

    RLS bypass via SUPERUSER-equivalent — em produção, CLI rodaria com
    role admin Sprint 6+. MVP: CLI roda como o role configurado no
    DATABASE_URL; admin queries assumem connection authorized.

    Smith H3 fix Fase 4.5b: emit warning stderr antes de execute para alertar
    operador que results podem ser empty se role não tem BYPASSRLS.
    """
    _emit_admin_warn_once()
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        result = await session.execute(text(query), params or {})
        return result


# ──────────────────────────────────────────────────────────────────────────────
# Click subgroup
# ──────────────────────────────────────────────────────────────────────────────


@click.group(name="analytics", help="Analytics dashboards CLI — Sati Eixo 5 MANDATORY (TD-SP04-04).")
def analytics_group() -> None:
    """Analytics subcommands — drop-off / tti / geral-pct / reclassification / pareto / privacy-audit / chain-verify / health."""


# ─── drop-off ───────────────────────────────────────────────────────────────
@analytics_group.command(name="drop-off")
@click.option("--period", default="7d", help="Período (ex: 7d, 30d, 90d).")
@click.option("--doctype", type=click.Choice(_VALID_DOCTYPES), default=None, help="Doctype filter (opcional).")
@click.option("--format", "fmt", type=click.Choice(["json", "text", "table"]), default="json")
def drop_off(period: str, doctype: str | None, fmt: str) -> None:
    """FR-ANALYTICS-01 — drop-off rate por doctype. Threshold ≤15% PASS."""
    days = _parse_period(period)

    async def _q():
        # Sessions com doctype_selected MAS sem contract_submitted (drop-off)
        clause_doctype = "AND doctype = :doctype" if doctype else ""
        params: dict[str, Any] = {"days": str(days)}
        if doctype:
            params["doctype"] = doctype

        result = await _run_admin_query(
            f"""
            WITH sessions_selected AS (
                SELECT DISTINCT session_id, doctype
                  FROM analytics_events
                 WHERE event_type = 'doctype_selected'
                   AND created_at >= NOW() - (:days || ' days')::interval
                   {clause_doctype}
            ),
            sessions_submitted AS (
                SELECT DISTINCT session_id
                  FROM analytics_events
                 WHERE event_type = 'contract_submitted'
                   AND created_at >= NOW() - (:days || ' days')::interval
            )
            SELECT
                COUNT(*) FILTER (WHERE s.session_id NOT IN (SELECT session_id FROM sessions_submitted)) AS dropped,
                COUNT(*) AS total
              FROM sessions_selected s
            """,
            params,
        )
        row = result.first()
        dropped = (row[0] or 0) if row else 0
        total = (row[1] or 0) if row else 0
        rate = (dropped / total) if total > 0 else 0.0

        payload = {
            "period_days": days,
            "doctype": doctype or "<all>",
            "sessions_dropped": dropped,
            "sessions_total": total,
            "drop_off_rate": round(rate, 4),
            "threshold_max": _THRESHOLD_DROPOFF_MAX,
            **_verdict(
                rate <= _THRESHOLD_DROPOFF_MAX,
                "Investigar UX onboarding — drop-off elevado pode indicar friction inicial.",
            ),
        }
        _emit(payload, fmt)

    asyncio.run(_q())


# ─── tti ────────────────────────────────────────────────────────────────────
@analytics_group.command(name="tti")
@click.option("--doctype", type=click.Choice(_VALID_DOCTYPES), default=None)
@click.option("--period", default="30d")
@click.option("--percentile", type=click.Choice(["p50", "p90", "p99"]), default="p90")
@click.option("--format", "fmt", type=click.Choice(["json", "text", "table"]), default="json")
def tti(doctype: str | None, period: str, percentile: str, fmt: str) -> None:
    """FR-ANALYTICS-02 — TTI seleção→submit delta. p90 default (Smith M2 fix); ≤90s PASS."""
    days = _parse_period(period)
    pct_map = {"p50": 0.5, "p90": 0.9, "p99": 0.99}
    pct_value = pct_map[percentile]

    async def _q():
        clause_doctype = "AND s.doctype = :doctype" if doctype else ""
        params: dict[str, Any] = {"days": str(days), "pct": pct_value}
        if doctype:
            params["doctype"] = doctype

        result = await _run_admin_query(
            f"""
            WITH pairs AS (
                SELECT s.session_id, s.doctype,
                       EXTRACT(EPOCH FROM (sub.occurred_at - s.occurred_at)) AS delta_sec
                  FROM analytics_events s
                  JOIN analytics_events sub
                    ON sub.session_id = s.session_id
                   AND sub.event_type = 'contract_submitted'
                 WHERE s.event_type = 'doctype_selected'
                   AND s.created_at >= NOW() - (:days || ' days')::interval
                   AND sub.created_at >= NOW() - (:days || ' days')::interval
                   AND sub.occurred_at > s.occurred_at
                   {clause_doctype}
            )
            SELECT PERCENTILE_CONT(:pct) WITHIN GROUP (ORDER BY delta_sec) AS pct_value,
                   COUNT(*) AS sample_size
              FROM pairs
            """,
            params,
        )
        row = result.first()
        tti_sec = float(row[0]) if row and row[0] is not None else None
        sample = (row[1] or 0) if row else 0

        passed = tti_sec is not None and tti_sec <= _THRESHOLD_TTI_P90_MAX_SEC
        payload = {
            "period_days": days,
            "doctype": doctype or "<all>",
            "percentile": percentile,
            "tti_seconds": round(tti_sec, 2) if tti_sec is not None else None,
            "sample_size": sample,
            "threshold_max_sec": _THRESHOLD_TTI_P90_MAX_SEC if percentile == "p90" else None,
            **_verdict(
                passed,
                "TTI elevado pode indicar UX confuso — investigar funil seleção→submit.",
            ),
        }
        _emit(payload, fmt)

    asyncio.run(_q())


# ─── geral-pct ──────────────────────────────────────────────────────────────
@analytics_group.command(name="geral-pct")
@click.option("--period", default="30d")
@click.option("--format", "fmt", type=click.Choice(["json", "text", "table"]), default="json")
def geral_pct(period: str, fmt: str) -> None:
    """FR-ANALYTICS-03 — % sessions com primeira escolha Geral. Threshold ≤10% PASS."""
    days = _parse_period(period)

    async def _q():
        result = await _run_admin_query(
            """
            WITH firsts AS (
                SELECT session_id, doctype
                  FROM analytics_events
                 WHERE event_type = 'first_doctype_selected'
                   AND created_at >= NOW() - (:days || ' days')::interval
            )
            SELECT
                COUNT(*) FILTER (WHERE doctype = 'geral') AS geral_count,
                COUNT(*) AS total
              FROM firsts
            """,
            {"days": str(days)},
        )
        row = result.first()
        geral = (row[0] or 0) if row else 0
        total = (row[1] or 0) if row else 0
        pct = (geral / total) if total > 0 else 0.0

        payload = {
            "period_days": days,
            "first_selection_geral": geral,
            "first_selection_total": total,
            "geral_pct": round(pct, 4),
            "threshold_max": _THRESHOLD_GERAL_MAX,
            **_verdict(
                pct <= _THRESHOLD_GERAL_MAX,
                "Geral pct elevado → considerar reordenação sidebar OR clarificar microcopy doctypes específicos.",
            ),
        }
        _emit(payload, fmt)

    asyncio.run(_q())


# ─── reclassification ───────────────────────────────────────────────────────
@analytics_group.command(name="reclassification")
@click.option("--period", default="30d")
@click.option("--breakdown-from-to/--no-breakdown-from-to", default=False)
@click.option("--format", "fmt", type=click.Choice(["json", "text", "table"]), default="json")
def reclassification(period: str, breakdown_from_to: bool, fmt: str) -> None:
    """FR-ANALYTICS-04 — % sessions com doctype_changed events. Threshold ≤5% PASS."""
    days = _parse_period(period)

    async def _q():
        # % sessions with at least one doctype_changed
        result = await _run_admin_query(
            """
            WITH sessions_selected AS (
                SELECT DISTINCT session_id
                  FROM analytics_events
                 WHERE event_type = 'doctype_selected'
                   AND created_at >= NOW() - (:days || ' days')::interval
            ),
            sessions_changed AS (
                SELECT DISTINCT session_id
                  FROM analytics_events
                 WHERE event_type = 'doctype_changed'
                   AND created_at >= NOW() - (:days || ' days')::interval
            )
            SELECT
                COUNT(*) FILTER (WHERE s.session_id IN (SELECT session_id FROM sessions_changed)) AS reclassified,
                COUNT(*) AS total
              FROM sessions_selected s
            """,
            {"days": str(days)},
        )
        row = result.first()
        recl = (row[0] or 0) if row else 0
        total = (row[1] or 0) if row else 0
        rate = (recl / total) if total > 0 else 0.0

        payload: dict[str, Any] = {
            "period_days": days,
            "sessions_reclassified": recl,
            "sessions_total": total,
            "reclassification_rate": round(rate, 4),
            "threshold_max": _THRESHOLD_RECLASS_MAX,
            **_verdict(
                rate <= _THRESHOLD_RECLASS_MAX,
                "Reclassification elevado → microcopy doctypes ambíguo. Investigar labels sidebar.",
            ),
        }

        if breakdown_from_to:
            matrix_result = await _run_admin_query(
                """
                SELECT
                    (payload_json->>'from_doctype') AS from_doc,
                    (payload_json->>'to_doctype') AS to_doc,
                    COUNT(*) AS n
                  FROM analytics_events
                 WHERE event_type = 'doctype_changed'
                   AND created_at >= NOW() - (:days || ' days')::interval
                 GROUP BY from_doc, to_doc
                 ORDER BY n DESC
                """,
                {"days": str(days)},
            )
            matrix = [
                {"from": r[0], "to": r[1], "count": r[2]}
                for r in matrix_result.all()
            ]
            payload["from_to_matrix"] = matrix

        _emit(payload, fmt)

    asyncio.run(_q())


# ─── pareto ─────────────────────────────────────────────────────────────────
@analytics_group.command(name="pareto")
@click.option("--period", default="30d")
@click.option("--format", "fmt", type=click.Choice(["json", "text", "table"]), default="json")
def pareto(period: str, fmt: str) -> None:
    """FR-ANALYTICS-05 — distribuição Pareto 7 doctypes. Top-3 ≥60% + Cauda ≥5% PASS."""
    days = _parse_period(period)

    async def _q():
        result = await _run_admin_query(
            """
            SELECT doctype, COUNT(*) AS n
              FROM analytics_events
             WHERE event_type = 'doctype_selected'
               AND created_at >= NOW() - (:days || ' days')::interval
               AND doctype IS NOT NULL
             GROUP BY doctype
             ORDER BY n DESC
            """,
            {"days": str(days)},
        )
        rows = result.all()
        total = sum(r[1] for r in rows)
        distribution = []
        for r in rows:
            doc, n = r[0], r[1]
            pct = (n / total) if total > 0 else 0.0
            distribution.append({"doctype": doc, "count": n, "pct": round(pct, 4)})

        top3_pct = sum(d["pct"] for d in distribution[:3])
        tail_pct = sum(d["pct"] for d in distribution[4:]) if len(distribution) > 4 else 0.0

        payload = {
            "period_days": days,
            "total_selections": total,
            "distribution": distribution,
            "top3_pct": round(top3_pct, 4),
            "tail_pct": round(tail_pct, 4),
            "threshold_top3_min": _THRESHOLD_PARETO_TOP3_MIN,
            "threshold_tail_min": _THRESHOLD_PARETO_TAIL_MIN,
            "caveat_smith_m4": (
                "Re-calibration recommended after 50+ empirical sessions — "
                "thresholds atuais provisórios (PRD v2.0.5.1 Smith M4 fix)."
            ),
            **_verdict(
                top3_pct >= _THRESHOLD_PARETO_TOP3_MIN
                and tail_pct >= _THRESHOLD_PARETO_TAIL_MIN,
                "Distribuição plana OU cauda morta → questionar expansão 4→7 hypothesis.",
            ),
        }
        _emit(payload, fmt)

    asyncio.run(_q())


# ─── privacy-audit ──────────────────────────────────────────────────────────
@analytics_group.command(name="privacy-audit")
@click.option("--period", default="30d")
@click.option("--format", "fmt", type=click.Choice(["json", "text", "table"]), default="json")
def privacy_audit(period: str, fmt: str) -> None:
    """NFR-PRIVACY-01 — 9 PII vectors compliance check. Scaneia payload_json últimos N dias."""
    days = _parse_period(period)

    pii_keys = [
        "contract_text", "advogada_nome", "advogado_nome", "cpf", "cnpj",
        "oab", "ip_full", "geo_country", "occurred_at_ms",
    ]

    async def _q():
        result = await _run_admin_query(
            """
            SELECT COUNT(*) AS total_events,
                   COUNT(*) FILTER (WHERE payload_json IS NOT NULL) AS with_payload
              FROM analytics_events
             WHERE created_at >= NOW() - (:days || ' days')::interval
            """,
            {"days": str(days)},
        )
        row = result.first()
        total = (row[0] or 0) if row else 0
        with_payload = (row[1] or 0) if row else 0

        violations: list[dict] = []
        for key in pii_keys:
            r = await _run_admin_query(
                """
                SELECT COUNT(*) FROM analytics_events
                 WHERE payload_json ? :key
                   AND created_at >= NOW() - (:days || ' days')::interval
                """,
                {"key": key, "days": str(days)},
            )
            count = r.scalar() or 0
            if count > 0:
                violations.append({"pii_vector": key, "events_count": count})

        payload = {
            "period_days": days,
            "events_total": total,
            "events_with_payload": with_payload,
            "pii_violations": violations,
            "pii_vectors_checked": pii_keys,
            **_verdict(
                len(violations) == 0,
                "PII leak detectada → audit log CRITICAL + backend defense-in-depth bypass investigation.",
            ),
        }
        _emit(payload, fmt)

    asyncio.run(_q())


# ─── chain-verify ───────────────────────────────────────────────────────────
@analytics_group.command(name="chain-verify")
@click.option("--period", default="7d")
@click.option("--tenant", required=True, help="Tenant UUID (admin operation).")
@click.option("--format", "fmt", type=click.Choice(["json", "text", "table"]), default="json")
def chain_verify(period: str, tenant: str, fmt: str) -> None:
    """NFR-PRIVACY-01.6 — HMAC chain integrity ad-hoc verify (default 7d). Smith C2 fix."""
    days = _parse_period(period)

    try:
        tenant_uuid = UUID(tenant)
    except ValueError as e:
        raise click.BadParameter(f"tenant UUID inválido: '{tenant}'") from e

    async def _q():
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session, with_tenant_context(session, tenant_uuid):
            intact, scanned, violations = await verify_chain_integrity(
                session, tenant_uuid, days=days
            )

        payload = {
            "period_days": days,
            "tenant_id": str(tenant_uuid),
            "chain_intact": intact,
            "events_scanned": scanned,
            "violations": violations,
            **_verdict(
                intact,
                "HMAC integrity violation → tenant quarantine + maintainer alert obrigatório.",
            ),
        }
        _emit(payload, fmt)

    asyncio.run(_q())


# ─── health ─────────────────────────────────────────────────────────────────
@analytics_group.command(name="health")
@click.option("--format", "fmt", type=click.Choice(["json", "text", "table"]), default="json")
def health(fmt: str) -> None:
    """NFR-OBSERVABILITY-01 — operational health (last event, total events, chain status)."""

    async def _q():
        result = await _run_admin_query(
            """
            SELECT
                COUNT(*) AS total_events,
                MAX(occurred_at) AS last_event_at,
                COUNT(DISTINCT tenant_id) AS tenants_active
              FROM analytics_events
            """,
        )
        row = result.first()
        payload = {
            "service": "analytics",
            "status": "healthy" if row else "degraded",
            "total_events": (row[0] or 0) if row else 0,
            "last_event_at": str(row[1]) if row and row[1] else None,
            "tenants_active": (row[2] or 0) if row else 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _emit(payload, fmt)

    asyncio.run(_q())


__all__ = ["analytics_group"]
