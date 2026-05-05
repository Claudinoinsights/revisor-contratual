---
type: adr
id: "ADR-008"
title: "Pipeline scraping multi-UF + heartbeat semanal anti-false-negative"
status: accepted
date: "2026-05-01"
domain: "pipeline-scraping"
decision_makers: ["@architect (Aria)"]
supersedes: null
superseded_by: null
absorves:
  - "R-NEW-SMITH-05 (false negative scrape silencioso)"
related_to:
  - "FR-RAG-05 (CLI multi-UF)"
  - "FR-MONITOR-01 (Tema 1378 STJ scrape semanal)"
  - "FR-ML-02 (refresh mensal jurisprudência)"
  - "R-03 (portais STF/STJ mudam layout)"
project: revisor-contratual
sprint: "01"
etapa: "2.0"
tags:
  - project/revisor-contratual
  - adr
  - scraping
  - multi-uf
  - heartbeat
---

# ADR-008 — Pipeline scraping multi-UF + heartbeat semanal anti-false-negative

```
[@architect · Aria (Visionary)] — etapa 2.0 · ADR-008 pipeline scraping
SPRINT: 01 · ETAPA: 2.0 · DOMÍNIO: SoftwareDev/legaltech
```

## Contexto

PRD v1.0.2 estabelece scraping de jurisprudência:
- **Vault inicial (FR-RAG-01):** STF Súmulas Vinculantes + Repercussão Geral; STJ Súmulas + Temas Repetitivos; TJBA acórdãos revisional CDC
- **Multi-UF first-class (FR-RAG-05):** CLI `python -m bloco_vault.seed.add_uf --uf SP --temas anatocismo,tabela_price`
- **Refresh mensal (FR-ML-02):** detecção de novos Temas/Súmulas
- **Monitoramento SEMANAL Tema 1378 STJ (FR-MONITOR-01):** mitigação ATIVA do risco temporal

R-03 (PRD): portais STF/STJ mudam layout HTML 2-3×/ano → scrapers quebram silenciosamente.

**Smith levantou na re-review (R-NEW-SMITH-05):** PRD diz "100% de detecção em ≤7 dias", MAS se scrape silenciosamente falha (mudança de layout), retorna 0 → sistema conclui "ainda não julgado" → false negative. Cenário catastrófico: Tema 1378 julgado, scrape quebrado, advogado peticiona com tese antiga, julgador cita Tema 1378 contra ele.

Aria precisa: arquitetura de scraping + error handling + heartbeat + detecção de breakage.

## Decisão

**Adotamos arquitetura de scrapers parametrizados por UF + heartbeat semanal + cross-check de sanidade contra contagem oficial.**

### Detalhes técnicos

```python
# bloco_vault/seed/scrapers/base.py

from abc import ABC, abstractmethod
from typing import Iterator
from pydantic import BaseModel
from datetime import datetime, timezone

class ScrapeResult(BaseModel):
    source: str               # ex: "STJ_temas_repetitivos"
    docs_found: int
    docs_new: int             # vs cache local
    docs_existing: int
    duration_ms: int
    success: bool
    error_message: str | None = None
    sanity_check_passed: bool # heartbeat: site respondeu vs site quebrado
    timestamp: datetime

class JurisprudenciaScraper(ABC):
    """Base abstrata. Cada tribunal/source tem implementação."""

    @abstractmethod
    def fetch_total_count(self) -> int:
        """Endpoint de contagem oficial (heartbeat).
        Ex: STJ tem /api/temas-repetitivos/total ou similar.
        Falha aqui = site quebrado, não 0 docs."""

    @abstractmethod
    def fetch_documents(self) -> Iterator[dict]:
        """Generator de docs raw. Subclasse implementa scraping específico."""

    def run(self) -> ScrapeResult:
        start = datetime.now(timezone.utc)

        # 1. SANITY CHECK (heartbeat)
        try:
            total_official = self.fetch_total_count()
            sanity_passed = total_official > 0
        except Exception as e:
            return ScrapeResult(
                source=self.__class__.__name__,
                docs_found=0, docs_new=0, docs_existing=0,
                duration_ms=int((datetime.now(timezone.utc) - start).total_seconds() * 1000),
                success=False,
                error_message=f"SANITY CHECK FAILED: {e}",
                sanity_check_passed=False,
                timestamp=start
            )

        # 2. SCRAPE
        try:
            docs = list(self.fetch_documents())
            new_count = self._dedupe_and_insert(docs)

            # 3. CROSS-CHECK: contagem local vs oficial
            local_count = self._count_local()
            discrepancy = abs(local_count - total_official) / max(total_official, 1)

            return ScrapeResult(
                source=self.__class__.__name__,
                docs_found=len(docs), docs_new=new_count,
                docs_existing=len(docs) - new_count,
                duration_ms=int((datetime.now(timezone.utc) - start).total_seconds() * 1000),
                success=True,
                sanity_check_passed=sanity_passed and discrepancy < 0.05,  # 5% tolerância
                error_message=(
                    f"⚠️ Discrepância {discrepancy:.1%} entre local ({local_count}) e oficial ({total_official})"
                    if discrepancy >= 0.05 else None
                ),
                timestamp=start
            )
        except Exception as e:
            return ScrapeResult(
                source=self.__class__.__name__,
                docs_found=0, docs_new=0, docs_existing=0,
                duration_ms=int((datetime.now(timezone.utc) - start).total_seconds() * 1000),
                success=False,
                error_message=f"SCRAPE FAILED: {e}",
                sanity_check_passed=sanity_passed,
                timestamp=start
            )
```

### Heartbeat semanal (FR-MONITOR-01 estendido)

```python
# bloco_vault/scheduler/heartbeat.py

def run_weekly_heartbeat() -> None:
    """
    Roda toda segunda-feira (cron OS-level via .env scheduler config).
    Audita TODOS os scrapers configurados.
    """
    sources = [
        STJTemasRepetitivosScraper(),
        STJSumulasScraper(),
        STFSumulasVinculantesScraper(),
        STFRepercussaoGeralScraper(),
        # TJ{UF} scrapers conforme adicionados
    ]

    for scraper in sources:
        result = scraper.run()
        _log_audit(result)

        # Detecção de scrape quebrado (R-NEW-SMITH-05)
        if not result.sanity_check_passed:
            _trigger_critical_alert(
                source=result.source,
                reason=result.error_message or "sanity check failed",
                last_success_check=_get_last_successful_run(scraper.__class__.__name__)
            )

    # Cross-check específico Tema 1378 STJ
    tema_1378 = _check_tema_1378_specific()
    if tema_1378.status == "julgado":
        _trigger_critical_alert(
            source="Tema_1378_STJ",
            reason=f"TEMA 1378 STJ JULGADO em {tema_1378.julgamento_date}. Pausar geração de petições e revisar tese padrão.",
            severity="CRITICAL_LEGAL"
        )

def _trigger_critical_alert(source: str, reason: str, severity: str = "HIGH"):
    """4 reações em cascata (FR-MONITOR-01):
    1. CRITICAL_ALERT no audit.jsonl
    2. Notificação visual persistente no header Streamlit (banner vermelho)
    3. Email para AUTH_EMAIL (se configurado)
    4. Pausa de novas gerações até confirmação de leitura
    """
    audit.append("CRITICAL_ALERT", {"source": source, "reason": reason, "severity": severity})
    streamlit_state.set_persistent_banner(reason, color="red")
    if os.environ.get("AUTH_EMAIL"):
        _send_email(subject=f"⚠️ {source}: {severity}", body=reason)
    if severity == "CRITICAL_LEGAL":
        streamlit_state.set_pause_generation(True, reason=reason)
```

### CLI multi-UF (FR-RAG-05)

```bash
# Adicionar nova UF (ex: SP)
python -m bloco_vault.seed.add_uf --uf SP --temas "anatocismo,tabela_price"
# Output: "✅ TJSP scraper registrado. Rodando primeira coleta..."

# Reindex após scrape
python -m bloco_vault.ingestao.pipeline_indexacao --uf SP
# Output: "✅ 287 docs TJSP indexados. Embeddings gerados em 4.2min."

# Verificar status de TODOS os scrapers
python -m bloco_vault.scheduler.heartbeat --check-all
# Output: tabela com source | last_success | docs_local | docs_oficial | discrepancy | status
```

### Detecção de mudança de layout HTML

Cada scraper implementa um **canary** — verificar elemento HTML que SEMPRE deve estar presente:

```python
class STJTemasRepetitivosScraper(JurisprudenciaScraper):
    CANARY_SELECTOR = "table.tabelaTemasRepetitivos"
    CANARY_MIN_ROWS = 100  # Esperado ≥100 temas a qualquer momento

    def fetch_total_count(self) -> int:
        soup = self._fetch_html("https://www.stj.jus.br/repetitivos/temas_repetitivos/")
        canary = soup.select_one(self.CANARY_SELECTOR)
        if not canary:
            raise ScrapeBreakageError(
                f"CANARY ausente: '{self.CANARY_SELECTOR}'. Layout STJ provavelmente mudou."
            )
        rows = canary.select("tr")
        if len(rows) < self.CANARY_MIN_ROWS:
            raise ScrapeBreakageError(
                f"CANARY anômalo: apenas {len(rows)} rows (esperado ≥{self.CANARY_MIN_ROWS}). Verificar manualmente."
            )
        return len(rows) - 1  # menos header
```

### Heartbeat schedule (cron-style)

Como D-LEAN é single-process Python sem daemon, scheduler é via:
- **Linux/Mac:** `crontab` do OS chama `python -m bloco_vault.scheduler.heartbeat`
- **Windows:** Task Scheduler chama mesmo script
- **Documentado em FR-SETUP-01** (instruções de instalação cron)

Alternativa runtime: `apscheduler` rodando em thread Streamlit (avaliar — ver Alt 3).

## Razão

- **Sanity check obrigatório antes de declarar "0 docs":** distingue site quebrado de "nenhum doc novo"
- **Cross-check contagem local vs oficial:** detecta drift; tolerância 5% absorve dessincronização normal
- **Canary HTML em cada scraper:** falha rápido quando layout muda (R-03 + R-NEW-SMITH-05)
- **CRITICAL_LEGAL severidade especial para Tema 1378:** pausa geração até confirmação humana (proteção máxima)
- **Cron OS-level vs daemon Python:** mais robusto (sobrevive a crash Streamlit); coerente com D-LEAN (sem processo extra)
- **CLI multi-UF (`add_uf`):** zero código para adicionar nova UF, só rodar comando

## Alternativas Consideradas

### Alt 1 — Manter scrape semanal sem heartbeat (PRD original)
- **Prós:** simples
- **Contras:** **vulnerável conforme R-NEW-SMITH-05** — false negative silencioso
- **Rejeitada:** absorver R-NEW-SMITH-05 é mandatório

### Alt 2 — APIs oficiais (DataJud para STJ/STF)
- **Prós:** estável, sem scraping
- **Contras:** DataJud cobre processos, NÃO súmulas/temas; APIs oficiais para súmulas/temas inexistem ou são limitadas
- **Rejeitada para vault MVP:** scraping é necessário; DataJud entra em fase 2 para FR-DATAJUD-01

### Alt 3 — APScheduler em thread Streamlit (em vez de cron OS)
- **Prós:** sem dependência de OS scheduler
- **Contras:** se Streamlit crasha, scheduler para; thread interno complica debugging
- **Rejeitada:** cron OS é mais robusto

### Alt 4 — Fila de scraping (Celery + Redis)
- **Prós:** retry automático, paralelismo
- **Contras:** **viola D-LEAN**; overkill para 5-10 sources rodando 1×/semana
- **Rejeitada:** decisão arquitetural firme

### Alt 5 — Headless browser (Playwright) em vez de requests + BeautifulSoup
- **Prós:** suporta JS-rendered SPAs
- **Contras:** +500MB Chromium; maior superfície; portais jurídicos brasileiros são SSR estáticos
- **Rejeitada para MVP:** revisitar se algum portal migrar para SPA

## Consequências

### Positivas
- **R-NEW-SMITH-05 NEUTRALIZADO:** false negative impossível com sanity check + canary + cross-check
- Detecção de quebra de scraper em ≤7 dias (próximo ciclo semanal)
- Multi-UF first-class operacional (FR-RAG-05 ✅)
- 4 reações em cascata para Tema 1378 STJ (FR-MONITOR-01 ✅)
- Cron OS-level robusto (sobrevive a crash Streamlit)

### Negativas / Tradeoffs
- Cron OS-level exige documentação por SO (Linux/Mac/Windows) em FR-SETUP-01
- Sanity check adiciona ~500ms por scrape (5 sources × 500ms = 2.5s extras semanais — desprezível)
- Canary HTML pode dar false positive se site mudar levemente (mitigação: alerta ≠ pausa de produção, exceto Tema 1378)
- DP-NOVO: documentar processo manual quando alerta CRITICAL_LEGAL dispara (advogado precisa decidir esperar julgamento ou recalibrar tese)

### Neutras
- Adicionar nova fonte de scraping requer apenas nova subclasse de `JurisprudenciaScraper` (NFR-MAINT-01 preservada)

## Decisão Pendente Documentada

**DP-NOVO (criada por esta ADR):** documentar processo manual de resposta a CRITICAL_LEGAL alert (advogado precisa de SOP claro). Output esperado: `docs/sop-critical-legal-alert.md`. Owner: @pm em coordenação com Eric.

## Referências

- PRD v1.0.2: FR-RAG-05 (linhas 258-261), FR-MONITOR-01 (linhas 458-465), FR-ML-02 (linhas 391-394), R-03 (linha 714)
- Smith re-review: R-NEW-SMITH-05 (qa/smith-adversarial-rereview-prd-v1.0.2.md)
- BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/
- ADR-007 (schema vault destino dos docs scraped)

---

*Aria, garantindo que o silêncio não seja confundido com paz. 🏗️*
