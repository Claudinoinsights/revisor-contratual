"""Error handler central — MVP-LEAN-01 Task 6.

Implementa C6 Error pane catch-all `infra` + 7 variantes específicas (per ux-spec §4 C6).
Padrão obrigatório SOP-003: Diagnóstico → Causa → Solução → Alternativa.

Anti-pattern proibido: mensagens genéricas tipo "Erro 500" ou "Algo deu errado".
Toda mensagem é navegável pelos 4 elementos canônicos.

Mapping exception type → variant via EXCEPTION_TO_C6_VARIANT (linhas 760-771 ux-spec).
"""

from __future__ import annotations

import sqlite3
from typing import Any

# ── 8 variantes: 7 específicas + 1 catch-all `infra_unknown` ──────────────
# Microcopy EXATO per ux-spec §4 C6 linhas 787-796 (não inventar variações).

VARIANTS: dict[str, dict[str, str]] = {
    "infra_unknown": {
        "titulo": "Erro de infraestrutura local",
        "diagnostico": "Falha técnica não-mapeada — auditoria preserva o estado para diagnóstico",
        "causa": "Exception genérica capturada pelo handler central",
        "solucao": (
            "Re-execute a análise. Se persistir, "
            "verifique audit.jsonl para diagnóstico completo"
        ),
        "alternativa": "Contate o maintainer com job_id e timestamp do erro",
    },
    "disk_full_audit": {
        "titulo": "Não foi possível registrar a auditoria",
        "diagnostico": "Sem espaço em disco para gravar a auditoria",
        "causa": "OSError [Errno 28] No space left on device em audit.jsonl",
        "solucao": "Liberar espaço em ~/.local/share/revisor-contratual/",
        "alternativa": (
            "Backup do audit.jsonl atual + truncate + reiniciar app "
            "(perde histórico antigo, preserva HMAC chain via genesis re-anchor)"
        ),
    },
    "disk_full_uploads": {
        "titulo": "Não foi possível receber o PDF",
        "diagnostico": "Sem espaço em disco para receber o PDF",
        "causa": "OSError [Errno 28] em uploads/ durante encrypt-on-upload (FR-LGPD-MVP-01 L4)",
        "solucao": (
            "Liberar espaço em ~/.local/share/revisor-contratual/uploads/ "
            "(PDFs antigos podem ser deletados — pipeline já completou)"
        ),
        "alternativa": "Mover backups antigos (backups/{YYYY-MM-DD}/) para storage externo",
    },
    "vault_db_locked": {
        "titulo": "Banco de jurisprudência ocupado",
        "diagnostico": "Banco de dados de jurisprudência ocupado",
        "causa": "sqlite3.OperationalError: database is locked durante busca FR-RAG",
        "solucao": "Aguardar 30s e re-executar (lock é tipicamente transient)",
        "alternativa": "Reiniciar a app — força liberação de qualquer lock pendente",
    },
    "fernet_key_missing": {
        "titulo": "Não foi possível decifrar PDFs do upload",
        "diagnostico": "Chave de cifragem ausente — não é possível decifrar PDFs do upload",
        "causa": "FERNET_KEY ausente OR inválida em .env (FR-LGPD-MVP-01 L4)",
        "solucao": (
            "Regenerar via python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\" e adicionar a .env"
        ),
        "alternativa": (
            "SOP-001 setup script (a criar como follow-up trivial); atenção: regenerar "
            "invalida PDFs já cifrados em uploads/ — limpar diretório"
        ),
    },
    "session_secret_missing": {
        "titulo": "Login não pode ser estabelecido",
        "diagnostico": "Chave de sessão ausente — login não pode ser estabelecido",
        "causa": "SESSION_SECRET ausente em .env (FR-LGPD-MVP-01 L2)",
        "solucao": (
            "Regenerar via python -c \"import secrets; print(secrets.token_urlsafe(32))\" "
            "e adicionar a .env; reiniciar app"
        ),
        "alternativa": "SOP-001 setup script",
    },
    "ollama_subprocess_crash": {
        "titulo": "Persona LLM indisponível",
        "diagnostico": "A persona LLM não está disponível",
        "causa": (
            "Subprocess Ollama (Sabia-7B ou Qwen-7B) morreu sem responder ao timeout "
            "(ADR-011)"
        ),
        "solucao": (
            "Re-execute a análise — auto-Ollama lifecycle detecta processo morto "
            "e spawn novo no próximo phase-start"
        ),
        "alternativa": (
            "Reinicie a app para forçar respawn imediato; "
            "verifique LLM_TIER em .env se persistir"
        ),
    },
    "bacen_api_down": {
        "titulo": "API BACEN indisponível",
        "diagnostico": "API BACEN indisponível para verificar taxa média",
        "causa": "httpx.TimeoutException ou 5xx em endpoint BACEN (FR-BACEN)",
        "solucao": (
            "Re-execute em ~30min "
            "(taxas BACEN são publicadas diariamente; transient downtime)"
        ),
        "alternativa": (
            "Pipeline usa última taxa cacheada "
            "(warning visível em S6: 'Taxa BACEN de {data anterior} — re-execute')"
        ),
    },
    "weasyprint_render_fail": {
        "titulo": "PDF do Relatório Contábil não pôde ser gerado",
        "diagnostico": "Não foi possível gerar o PDF do Relatório Contábil",
        "causa": (
            "weasyprint.RenderError (D1 PDF) — pode ser tabela com formato anômalo "
            "OR fontes ausentes"
        ),
        "solucao": "Re-execute a análise (transient)",
        "alternativa": (
            "Baixe D2 e D3 (DOCX) primeiro — eles não dependem do WeasyPrint; "
            "D1 pode ser regenerado manualmente a partir do audit.jsonl"
        ),
    },
}

# ── Mapping exception → variant_key (per ux-spec linhas 760-771) ──────────
# Keys são strings descritivas (não classes Python diretas) para suportar
# distinção fina (ex: OSError-28 audit vs uploads — mesma exception, paths diferentes).

EXCEPTION_TO_C6_VARIANT: dict[str, str] = {
    "OSError-28-audit": "disk_full_audit",
    "OSError-28-uploads": "disk_full_uploads",
    "sqlite3.OperationalError-locked": "vault_db_locked",
    "InvalidToken": "fernet_key_missing",
    "RuntimeError-session-secret": "session_secret_missing",
    "OllamaProcessNotResponding": "ollama_subprocess_crash",
    "httpx.TimeoutException-bacen": "bacen_api_down",
    "weasyprint.RenderError": "weasyprint_render_fail",
    # Catch-all (último recurso, NÃO deve cair aqui em produção)
    "*": "infra_unknown",
}


def classify_exception(exc: BaseException) -> str:
    """Classifica uma exception em uma variant key per EXCEPTION_TO_C6_VARIANT.

    Estratégia (em ordem de precedência):
    1. Match exato por classe + atributos (ex: OSError errno=28 + path contém 'audit')
    2. Match por classe (sqlite3.OperationalError com 'locked' na message)
    3. Match por nome qualificado (httpx.TimeoutException com URL bacen)
    4. Fallback `infra_unknown`
    """
    exc_class = type(exc).__name__
    exc_module = type(exc).__module__
    exc_msg = str(exc).lower()

    # OSError errno 28 — distinguir audit vs uploads via path/message
    if isinstance(exc, OSError) and getattr(exc, "errno", None) == 28:
        if "audit" in exc_msg or "audit.jsonl" in exc_msg:
            return "disk_full_audit"
        if "upload" in exc_msg or "uploads" in exc_msg:
            return "disk_full_uploads"
        # Default OSError-28 sem path identificável → audit (mais comum)
        return "disk_full_audit"

    # sqlite3.OperationalError com "locked" na mensagem
    if isinstance(exc, sqlite3.OperationalError) and "locked" in exc_msg:
        return "vault_db_locked"

    # InvalidToken (cryptography.fernet) — match por nome de classe
    if exc_class == "InvalidToken":
        return "fernet_key_missing"

    # RuntimeError com SESSION_SECRET na message
    if isinstance(exc, RuntimeError) and (
        "session_secret" in exc_msg or "session secret" in exc_msg
    ):
        return "session_secret_missing"

    # OllamaProcessNotResponding — match por nome
    if exc_class == "OllamaProcessNotResponding":
        return "ollama_subprocess_crash"

    # httpx.TimeoutException — match por module + URL bacen
    if exc_module.startswith("httpx") and "Timeout" in exc_class and "bacen" in exc_msg:
        return "bacen_api_down"

    # weasyprint.RenderError
    if exc_module.startswith("weasyprint") and "Render" in exc_class:
        return "weasyprint_render_fail"

    # Catch-all
    return "infra_unknown"


def get_c6_payload(
    variant_key: str,
    exc: BaseException | None = None,
    job_id: str | None = None,
) -> dict[str, Any]:
    """Retorna payload completo para template C6 com 6 campos.

    Para `infra_unknown`, enriquece diagnostico/causa com dados da exception se fornecida
    (per ux-spec linhas 774-780).

    Returns:
        dict com keys: titulo, diagnostico, causa, solucao, alternativa, acoes
    """
    base = VARIANTS.get(variant_key, VARIANTS["infra_unknown"]).copy()

    # Enriquecimento `infra_unknown` com contexto da exception (per ux-spec linhas 776-779)
    if variant_key == "infra_unknown" and exc is not None:
        exc_class = type(exc).__name__
        exc_module = type(exc).__module__
        exc_msg = str(exc)
        first_line = exc_msg.split("\n")[0] if exc_msg else "(sem mensagem)"
        base["diagnostico"] = f"{exc_class}: {first_line}"
        base["causa"] = f"{exc_module}.{exc_class}"

    if job_id and variant_key == "infra_unknown":
        base["alternativa"] = f"Contate o maintainer com job_id={job_id} e timestamp do erro"

    # Ações default (per ux-spec linha 553)
    base["acoes"] = [
        {"label": "Tentar novamente", "action": "reset", "href": "/"},
        {"label": "Ver log audit", "action": "audit", "href": "/audit.jsonl"},
    ]

    return base
