---
type: story
id: "SP04-DOCTYPE-01"
title: "Multi-Doctype Dispatcher backend — Strategy hierárquica 7 doctypes operacionais (per ADR-020)"
status: Ready
epic: "Sprint 04 Cloud SaaS BYOK"
project: revisor-contratual
sprint: "04"
phase: 14.4
priority: P1
estimated_days: "3-5"
agent: "@dev (Neo)"
branch: "feat/sp04-doctype-01 (será criada pós validate-story-draft → Ready + Trinity Phase 3 PRD chunks 4-7 OR paralelo Neo chunks 1-3)"
created: "2026-05-09"
created_by: "@sm River"
predecessor_handoff: ".lmas/handoffs/handoff-architect-to-sm-2026-05-09-adr-020-accepted-unblock-sp04-ui-spa-01.yaml (paralelo SP04-UI-SPA-01)"
predecessor_adr: "governance/architecture/adr/adr-020-multi-doctype-dispatcher-v2.md (Accepted 2026-05-09 — implementation specs §1-7)"
dependencies:
  - "ADR-020 (Multi-Doctype Dispatcher v2 — Accepted 2026-05-09 — implementation specs definitivos §1.1-1.7)"
  - "ADR-003 (4 personas implementation base preserved — não é refactor das personas, apenas wrap em Strategy)"
  - "ADR-014 (Anthropic SDK BYOK runtime — classifier Haiku 4.5 Tier 2 + dispatcher persona LLM calls reusam middleware)"
  - "ADR-017 (Multi-tenant Pool+RLS BACKBONE — vault SHARED com doctype_tag preserved)"
  - "ADR-016 (superseded by ADR-020 — ZERO código legacy a remover, refactor é greenfield)"
  - "SP04-AUTH-01 (Done — PR #4 OPEN — JWT cookie + tenant_id claim propaga RLS context)"
  - "SP04-BYOK-01 (Done — PR #5 OPEN — Anthropic runtime middleware get_anthropic_client(tenant_id) reusado por classifier + personas)"
  - "SP04-LGPD-01 (Done — PR #6 OPEN MERGEABLE — audit chain HMAC ADR-005 reusada para audit log doctype field)"
  - "SP04-UI-SPA-01 (paralelo — Ready G3 PASS — integra via doctype field POST /revisar mas ZERO overlap implementation backend)"
source_frs:
  - "FR-DOCTYPE-01 (Multi-doctype dispatcher — 7 doctypes operacionais ADR-020)"
  - "FR-DOCTYPE-02 (Detecção 3-tier UI selector + LLM classifier + Geral fallback)"
  - "FR-PERSONAS-01..03 (Advogado + Economista + Juiz preserved per ADR-003 — wrap em Strategy)"
  - "FR-VAULT-01 (vault jurisprudencial doctype_tag SHARED multi-tenant per ADR-017)"
  - "FR-BACEN-01 (BACEN SGS series cache per modalidade + CDI/SELIC)"
  - "FR-AUDIT-01 (audit log doctype escolhido — ADR-008 heartbeat distribution metrics)"
cross_references:
  prd: "governance/prd/prd-v2.0.0-DRAFT.md FR-DOCTYPE-01..02 + Trinity Phase 3 PRD update pendente templates D3 cross-domain"
  ux: "governance/ux-spec-v2.0.0-DRAFT.md S4 7 doctypes (Sati Phase 4 — frontend SP04-UI-SPA-01)"
  adrs: ["adr-003", "adr-014", "adr-016", "adr-017", "adr-020"]
  story_predecessors: ["SP04-AUTH-01", "SP04-BYOK-01", "SP04-LGPD-01"]
  story_paralelo: "SP04-UI-SPA-01 (frontend)"
  smith_findings_addressed: "F-016 (LGPD operador — preservado via SP04-LGPD-01 audit chain integration)"
  trinity_dependency: "Phase 3 PRD update — conteúdo legal templates D3 (CCB/Cartão/Consignado/Geral) MANDATORY pre-implement chunks 5-7"
tags:
  - project/revisor-contratual
  - story
  - sprint-04
  - epic-doctype
  - backend
  - p1
  - multi-tenant
  - strategy-pattern
  - dispatcher
---

# SP04-DOCTYPE-01 — Multi-Doctype Dispatcher backend (Strategy hierárquica 7 doctypes)

```
[@sm · River (Facilitator)] — Sprint 04 · Phase 14.4 · SP04-DOCTYPE-01 · backend Strategy
SPRINT: 04 · PHASE: 14.4 · DOMÍNIO: software-dev/legaltech-dispatcher
```

> **Foundation Sprint 04 P1 — backend dispatcher.** ADR-020 (Accepted 2026-05-09) define Strategy hierárquica 3-camada com 7 doctypes operacionais. Esta story implementa a contraparte backend de SP04-UI-SPA-01 (frontend integration). Sem esta story, o `doctype` field do POST /revisar (vindo da sidebar SPA) é apenas metadado registrado — análises são processadas com persona prompts genéricos sem nuance jurídica per-doctype.

> ⚠️ **Trinity Phase 3 PRD bloqueio cross-domain:** Conteúdo legal dos 4 novos templates D3 (CCB/Cartão/Consignado/Geral) é responsabilidade @pm Trinity (não Neo). Story Path B chunks 1-3 (skeleton + dispatchers + migrations) podem rodar paralelo Trinity work; chunks 4-7 (32 prompts + integration tests) bloqueam até Trinity entrega.

---

## 1. Sumário

Story foundation Sprint 04 P1 backend — implementa Strategy hierárquica 3-camada definida em ADR-020:

1. **Strategy backbone** — `bloco_workflow/dispatchers/` com abstract base `DoctypeDispatcher` + abstract intermediate `BancarioBaseStrategy` (Template Method DRY) + 7 concrete dispatchers (CCB/Cartão/Consignado herdam BancarioBase; Veicular/FIES/Imobiliário/Geral standalone)
2. **Router 3-tier** — `resolve_dispatcher()` Tier 1 UI selector (autoritativo) + Tier 2 LLM Haiku classifier ($0.001/análise) + Tier 3 GeralDispatcher catch-all (UX coerente — substitui ADR-016 unknown rejection)
3. **32 persona prompt files** — paridade ADR-020 §1.4 (4 personas × 7 doctypes com 4 prompts base bancário compartilhados via Template Method em BancarioBaseStrategy)
4. **Migrations SQL** — `sp04_004_doctype_tag_v2.sql` (vault doctype_tag enum 5 → 8 valores + backfill conservador `bancario` → `bancario_cross`) + `sp04_005_bacen_series_doctype_v2.sql` (pre-fetch CDI 4391 Cartão + modalidade 218 CCB outros)
5. **Endpoint update** — `POST /revisar` aceita `doctype` field FormData + chama `resolve_dispatcher()` + audit chain HMAC event `dispatcher_resolved` per ADR-005 + ADR-008 heartbeat distribution metrics
6. **Test coverage** — unit tests (Strategy hierarchy + Template Method + 3-tier detection) + integration stubs `_REQUIRES_POSTGRES` + `_REQUIRES_OLLAMA` (5 stubs cycle E2E)

**Foundation impact:** Desbloqueia análise revisional **per-doctype com nuance jurídica**:
- CCB Bancária: anatocismo + Resolução BACEN 4.558/2017 + capitalização juros
- Cartão de Crédito: Súmula 530 STJ venda casada + rotativo + IOF
- Consignado: Lei 10.820/2003 + cap 35% margem + INSS/militar/servidor
- Veicular: CDC veículos PF + Decreto-Lei 911/69 + busca apreensão
- FIES: TJLP + portarias MEC + perda crédito
- Imobiliário: SFH/SFI + TR + Poupança IPCA + Súmula 539 STJ
- Geral: catch-all genérico para contratos atípicos (Tier 3 fallback)

Sem esta story, mesmo com SPA frontend funcionando (SP04-UI-SPA-01), o pipeline de análise processa todos contratos com prompts genéricos — perda crítica de qualidade jurídica revisional.

**Branch strategy:** `feat/sp04-doctype-01` base `main` **pós-merge** PR #4 + #5 + #6 (clean rebase). Pode rodar **paralelo SP04-UI-SPA-01 em sprint sincronizado** — zero overlap implementation (SP04-UI-SPA-01 é frontend `bloco_interface/web/static/`; SP04-DOCTYPE-01 é backend `bloco_workflow/dispatchers/`).

---

## 2. As a / I want / So that

- **As a** advogado responsável de escritório de advocacia (BYOK tenant Sprint 04)
- **I want** que cada doctype escolhido na sidebar SPA (CCB/Veículo/Consignado/Cartão/Imobiliário/FIES/Geral) seja processado com persona prompts especializados na regulação + jurisprudência específica daquele tipo de contrato
- **So that** as teses jurídicas geradas pelo Advogado/Economista/Juiz refletem nuances jurídicas reais (anatocismo CCB ≠ rotativo Cartão ≠ margem Consignado), garantindo defensabilidade ANPD + CFOAB + qualidade revisional condizente com escritório especializado

---

## 3. Acceptance Criteria (8 ACs)

### AC-01 — Strategy backbone (abstract base + intermediate per ADR-020 §1.1-1.2)

`bloco_workflow/dispatchers/base.py`:

```python
# bloco_workflow/dispatchers/base.py
from abc import ABC, abstractmethod
from typing import Sequence
from bloco_workflow.personas import Persona

class DoctypeDispatcher(ABC):
    """Interface contratual para todos os 7 doctypes (ADR-020 §1.1)."""

    @abstractmethod
    def doctype_id(self) -> str:
        """Retorna sidebar data-mode: ccb|cartao|consignado|veiculo|fies|imobiliario|geral."""

    @abstractmethod
    def get_personas(self) -> Sequence[Persona]:
        """Retorna 4 personas (advogado, economista, validador, juiz) com prompts adaptados ao doctype."""

    @abstractmethod
    def get_d3_template(self) -> str:
        """Apelação Cível D3 template path (Trinity Phase 3 PRD provê conteúdo)."""

    @abstractmethod
    def get_jurisprudencia_filter(self) -> dict:
        """Vault filter — retorna {tags: [doctype_id, "cross", ...specific cross-tags]}."""

    @abstractmethod
    def get_bacen_modalidade(self) -> str:
        """BACEN SGS modalidade ou series identifier."""
```

`bloco_workflow/dispatchers/bancario_base.py`:

```python
# bloco_workflow/dispatchers/bancario_base.py
from abc import ABC, abstractmethod
from typing import Sequence
from .base import DoctypeDispatcher
from bloco_workflow.personas import Persona, _load_prompt

class BancarioBaseStrategy(DoctypeDispatcher, ABC):
    """Compartilha lógica BACEN + cláusulas abusivas CDC para CCB/Cartão/Consignado.

    Template Method pattern (ADR-020 §1.2): sub-classes override
    doctype_specific_section() — lógica base reusada DRY.
    """

    def get_jurisprudencia_filter(self) -> dict:
        return {
            "tags": [self.doctype_id(), "bancario_cross", "cdc_cross"]
        }

    def get_personas(self) -> Sequence[Persona]:
        """Template Method — base prompts compartilhados + specific overrides."""
        return [
            self._build_persona("advogado"),
            self._build_persona("economista"),
            self._build_persona("validador"),
            self._build_persona("juiz"),
        ]

    def _build_persona(self, role: str) -> Persona:
        base_prompt = _load_prompt(f"{role}_bancario_base.txt")
        specific = self.doctype_specific_section(role)
        return Persona(role=role, prompt=f"{base_prompt}\n\n{specific}")

    @abstractmethod
    def doctype_specific_section(self, persona_role: str) -> str:
        """Cada sub-class CCB/Cartao/Consignado fornece nuances específicas via _load_prompt('{role}_{doctype}_specific.txt')."""
```

**Tested:** unit test `test_dispatchers.py::test_abstract_classes_cannot_instantiate` — `DoctypeDispatcher()` e `BancarioBaseStrategy()` levantam `TypeError` (abstract); `test_template_method_calls_specific` — mock concrete sub-class de BancarioBase confirma `doctype_specific_section()` é chamado durante `get_personas()`.

### AC-02 — 7 concrete dispatchers (per ADR-020 §1.3)

7 arquivos em `bloco_workflow/dispatchers/`:

```python
# bloco_workflow/dispatchers/ccb.py
from bloco_workflow.personas import _load_prompt
from .bancario_base import BancarioBaseStrategy

class CCBDispatcher(BancarioBaseStrategy):
    def doctype_id(self) -> str:
        return "ccb"

    def doctype_specific_section(self, persona_role: str) -> str:
        return _load_prompt(f"{persona_role}_ccb_specific.txt")

    def get_d3_template(self) -> str:
        return "templates_d3/ccb.txt"  # Trinity Phase 3 PRD

    def get_bacen_modalidade(self) -> str:
        return "217"  # CDC veículos OR "218" CDC outros — Aria valida em runtime
```

(Mesma estrutura para `CartaoDispatcher` + `ConsignadoDispatcher` herdando `BancarioBaseStrategy`.)

```python
# bloco_workflow/dispatchers/veicular.py
from bloco_workflow.personas import _load_prompt, Persona
from .base import DoctypeDispatcher

class VeicularDispatcher(DoctypeDispatcher):
    """Standalone — não herda BancarioBase (CDC veículos PF é específico Decreto-Lei 911/69)."""

    def doctype_id(self) -> str:
        return "veiculo"

    def get_personas(self):
        return [Persona(role=r, prompt=_load_prompt(f"{r}_veicular.txt")) for r in ("advogado", "economista", "validador", "juiz")]

    def get_d3_template(self) -> str:
        return "templates_d3/veicular.txt"

    def get_jurisprudencia_filter(self) -> dict:
        return {"tags": ["veiculo", "cross"]}

    def get_bacen_modalidade(self) -> str:
        return "217"
```

(Mesma estrutura para `FIESDispatcher` + `ImobiliarioDispatcher` + `GeralDispatcher` standalone.)

`GeralDispatcher` (Tier 3 catch-all — NEW per ADR-020 §1.5):

```python
# bloco_workflow/dispatchers/geral.py
class GeralDispatcher(DoctypeDispatcher):
    """Catch-all Tier 3 — substitui ADR-016 unknown rejection.
    Processa contratos atípicos via prompts genéricos + cross-tag vault.
    """
    def doctype_id(self) -> str:
        return "geral"

    def get_jurisprudencia_filter(self) -> dict:
        return {"tags": ["geral", "cross"]}  # generic cross-doctype

    def get_bacen_modalidade(self) -> str:
        return "1178"  # SELIC genérica
```

**Tested:** unit `test_dispatchers.py::test_seven_concrete_dispatchers_instantiable` — 7 dispatchers instanciam sem erro + `doctype_id()` retorna valor esperado per dispatcher; `test_bancario_subclasses_extend_base` — CCB/Cartão/Consignado `isinstance(BancarioBaseStrategy)` True; `test_standalone_dispatchers` — Veicular/FIES/Imobiliário/Geral `isinstance(BancarioBaseStrategy)` False.

### AC-03 — Router resolve_dispatcher() 3-tier (per ADR-020 §1.5)

`bloco_workflow/dispatchers/router.py`:

```python
# bloco_workflow/dispatchers/router.py
from typing import Optional
from anthropic import Anthropic
from .base import DoctypeDispatcher
from .ccb import CCBDispatcher
from .cartao import CartaoDispatcher
from .consignado import ConsignadoDispatcher
from .veicular import VeicularDispatcher
from .fies import FIESDispatcher
from .imobiliario import ImobiliarioDispatcher
from .geral import GeralDispatcher

DISPATCHERS = {
    "ccb": CCBDispatcher,
    "cartao": CartaoDispatcher,
    "consignado": ConsignadoDispatcher,
    "veiculo": VeicularDispatcher,
    "fies": FIESDispatcher,
    "imobiliario": ImobiliarioDispatcher,
    "geral": GeralDispatcher,
}

def resolve_dispatcher(
    ui_selector: Optional[str],   # PRIMARY: SPA sidebar data-mode (POST /revisar doctype field)
    contract_text: str,           # FALLBACK input para classifier
    classifier_llm: Anthropic,    # Tier 2 — Anthropic Haiku 4.5 ($0.001/análise)
) -> DoctypeDispatcher:
    """3-tier detection per ADR-020 §1.5."""

    # Tier 1: UI selector (advogado escolheu na sidebar — autoritativo)
    if ui_selector and ui_selector in DISPATCHERS:
        return DISPATCHERS[ui_selector]()

    # Tier 2: LLM classifier Haiku 4.5 (~$0.001/análise)
    classified = _classify_doctype(classifier_llm, contract_text)
    if classified in DISPATCHERS:
        return DISPATCHERS[classified]()

    # Tier 3: GeralDispatcher catch-all (UX coerente — sempre processa)
    return GeralDispatcher()


def _classify_doctype(classifier_llm: Anthropic, contract_text: str) -> Optional[str]:
    """Anthropic Haiku 4.5 classifier — retorna doctype_id ou None."""
    response = classifier_llm.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": f"Classifique este contrato. Retorne APENAS uma palavra: ccb, cartao, consignado, veiculo, fies, imobiliario, geral.\n\n{contract_text[:2000]}"
        }],
    )
    classified = response.content[0].text.strip().lower()
    return classified if classified in DISPATCHERS else None
```

**Tested:** unit `test_router.py`:
- `test_tier_1_ui_selector_authoritative` — `resolve_dispatcher("ccb", "...", mock_llm)` retorna CCBDispatcher sem chamar LLM
- `test_tier_2_llm_classifier_called_when_no_ui` — `resolve_dispatcher(None, "...", mock_llm)` chama LLM mock returning "cartao" → CartaoDispatcher
- `test_tier_3_geral_fallback` — `resolve_dispatcher(None, "...", mock_llm)` LLM mock returning "unknown" → GeralDispatcher
- `test_tier_3_invalid_ui_selector_falls_through` — `resolve_dispatcher("invalid_doctype", "...", mock_llm)` cai no Tier 2 → eventualmente Tier 3
- `test_classifier_truncates_long_contract` — contract_text > 2000 chars é truncado para classifier LLM efficiency

### AC-04 — 32 persona prompt files com Template Method DRY (per ADR-020 §1.4)

Em `bloco_workflow/personas/prompts/` adicionar **16 arquivos novos** (atual 16 já existentes ADR-016 reusados parcialmente):

**Bancário base (4 arquivos novos — DRY compartilhado):**
- `advogado_bancario_base.txt` — fundamentação CDC + BACEN base + cláusulas abusivas
- `economista_bancario_base.txt` — Decimal everywhere + cálculo Price/SAC + BACEN SGS
- `validador_bancario_base.txt` — NLI híbrido per ADR-004
- `juiz_bancario_base.txt` — C1/C2/C3 thresholds per ADR-003

**CCB specific (4 arquivos novos):**
- `advogado_ccb_specific.txt` — Resolução BACEN 4.558/2017 + anatocismo + capitalização
- `economista_ccb_specific.txt` — modalidades 217/218 + CDC PF
- `validador_ccb_specific.txt` — Súmulas STJ CCB
- `juiz_ccb_specific.txt` — thresholds CCB

**Cartão specific (4 arquivos novos):**
- `advogado_cartao_specific.txt` — Súmula 530 STJ venda casada + rotativo
- `economista_cartao_specific.txt` — CDI 4391 + SELIC 1178 + IOF
- `validador_cartao_specific.txt` — Súmulas cartão
- `juiz_cartao_specific.txt` — thresholds cartão

**Consignado specific (4 arquivos novos):**
- `advogado_consignado_specific.txt` — Lei 10.820/2003 + cap 35% margem
- `economista_consignado_specific.txt` — modalidades 419/432
- `validador_consignado_specific.txt` — Súmula 603 STJ
- `juiz_consignado_specific.txt` — thresholds consignado

**Geral standalone (4 arquivos novos):**
- `advogado_geral.txt` — fundamentação genérica catch-all
- `economista_geral.txt` — SELIC + IPCA generic
- `validador_geral.txt` — NLI híbrido genérico
- `juiz_geral.txt` — thresholds genéricos

**Veicular/FIES/Imobiliário (12 arquivos preserved/migrate from ADR-016):**
- `advogado_veicular.txt`, `economista_veicular.txt`, `validador_veicular.txt`, `juiz_veicular.txt`
- `advogado_fies.txt`, `economista_fies.txt`, `validador_fies.txt`, `juiz_fies.txt`
- `advogado_imobiliario.txt`, `economista_imobiliario.txt`, `validador_imobiliario.txt`, `juiz_imobiliario.txt`

**Total: 32 prompts** (4 base bancário + 12 sub-bancários + 4 Geral standalone + 12 standalone preserved/migrated).

**Trinity Phase 3 PRD MANDATORY:** conteúdo legal substantivo dos 16 prompts NOVOS é responsabilidade @pm Trinity (cross-domain). Neo entrega skeletons (placeholders estruturais) em chunks 5-6; Trinity preenche conteúdo legal paralelo.

**Tested:** unit `test_personas_doctype_prompts.py`:
- `test_all_32_prompt_files_exist` — Path() check 32 arquivos presentes
- `test_bancario_base_loads_for_ccb` — `CCBDispatcher().get_personas()` carrega `advogado_bancario_base.txt` + concatena `advogado_ccb_specific.txt`
- `test_standalone_does_not_load_base` — `VeicularDispatcher().get_personas()` carrega APENAS `advogado_veicular.txt` (não base)
- `test_geral_loads_geral_prompts` — `GeralDispatcher().get_personas()` carrega `advogado_geral.txt`

### AC-05 — Migration sp04_004 vault doctype_tag enum 5 → 8 valores (per ADR-020 §1.6)

`bloco_database/migrations/sp04_004_doctype_tag_v2.sql`:

```sql
-- ════════════════════════════════════════════════════════════════════════════
-- Sprint 04 · Story SP04-DOCTYPE-01 · Chunk 4 (Path B)
-- Migration: vault doctype_tag enum 5 → 8 valores (ADR-020 §1.6)
--
-- Antes (ADR-016): 5 valores (veicular | fies | bancario | imobiliario | cross)
-- Depois (ADR-020): 8 valores
--   - 7 doctypes operacionais: ccb | cartao | consignado | veiculo | fies | imobiliario | geral
--   - 3 cross-tags: bancario_cross (CCB+Cartão+Consignado) | cdc_cross (todos bancários) | cross (qualquer)
--
-- Backfill conservador: ADR-016 entries com tag 'bancario' → 'bancario_cross' (zero data loss)
-- Sprint 06+ TD-SP04-12 refinement granular ccb/cartao/consignado curadoria manual
-- ════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ─── Drop old enum constraint ────────────────────────────────────────────────
ALTER TABLE jurisprudencia
  DROP CONSTRAINT IF EXISTS jurisprudencia_doctype_tag_check;

-- ─── New enum constraint (8 valores + cross-tags) ───────────────────────────
ALTER TABLE jurisprudencia
  ADD CONSTRAINT jurisprudencia_doctype_tag_check CHECK (
    doctype_tag IN (
      'ccb', 'cartao', 'consignado',          -- NEW Sprint 04 ADR-020 (sub-bancários)
      'veiculo', 'fies', 'imobiliario',       -- preserved ADR-016
      'geral',                                -- NEW Sprint 04 ADR-020 (catch-all)
      'bancario_cross',                       -- NEW: cross CCB+Cartão+Consignado
      'cdc_cross',                            -- NEW: aplicável TODOS bancários
      'cross'                                 -- preserved: qualquer cross-doctype
    )
  );

-- ─── Backfill conservador 'bancario' legacy → 'bancario_cross' ──────────────
-- Razão: ADR-016 tag 'bancario' generic é ambíguo entre CCB/Cartão/Consignado.
-- Sprint 06+ TD-SP04-12 curadoria manual granular per Súmula STJ ~50 entries.
UPDATE jurisprudencia SET doctype_tag = 'bancario_cross'
  WHERE doctype_tag = 'bancario';

-- Audit: count migrations applied
DO $$
DECLARE
  migrated_count INT;
BEGIN
  SELECT COUNT(*) INTO migrated_count FROM jurisprudencia WHERE doctype_tag = 'bancario_cross';
  RAISE NOTICE 'sp04_004_doctype_tag_v2: % entries migrated bancario → bancario_cross', migrated_count;
END $$;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════════
-- Smoke validation:
--   SELECT doctype_tag, COUNT(*) FROM jurisprudencia GROUP BY doctype_tag ORDER BY 1;
--   Esperado: ccb=0, cartao=0, consignado=0 (Sprint 06+ curadoria), bancario_cross=N (=count antigo 'bancario'),
--             veiculo=K, fies=L, imobiliario=M, geral=0, cross=P, cdc_cross=0
-- Rollback (se necessário antes de produção):
--   BEGIN;
--   ALTER TABLE jurisprudencia DROP CONSTRAINT jurisprudencia_doctype_tag_check;
--   ALTER TABLE jurisprudencia ADD CONSTRAINT jurisprudencia_doctype_tag_check CHECK (
--     doctype_tag IN ('veicular','fies','bancario','imobiliario','cross')
--   );
--   UPDATE jurisprudencia SET doctype_tag = 'bancario' WHERE doctype_tag = 'bancario_cross';
--   COMMIT;
-- ════════════════════════════════════════════════════════════════════════════
```

**Tested:** integration test `_REQUIRES_POSTGRES`:
- `test_doctype_tag_enum_8_values_accepted` — INSERT 8 doctype_tag valid valores → success
- `test_doctype_tag_invalid_rejected` — INSERT `doctype_tag='invalid'` → CHECK constraint violation
- `test_backfill_bancario_to_cross` — pre-migration insert tag='bancario'; post-migration verify all migrated to 'bancario_cross'; count match

### AC-06 — Migration sp04_005 BACEN series CDI 4391 + modalidade 218 (per ADR-020 §1.7)

`bloco_database/migrations/sp04_005_bacen_series_doctype_v2.sql`:

```sql
-- ════════════════════════════════════════════════════════════════════════════
-- Sprint 04 · Story SP04-DOCTYPE-01 · Chunk 4 (Path B)
-- Migration: BACEN SGS series adicionais (ADR-020 §1.7)
--
-- Series novas pre-fetch + diskcache populate:
--   - CDI 4391 (Cartão de Crédito — taxa rotativo benchmark)
--   - Modalidade 218 (CCB outros bens — diferente 217 que é veículos)
--
-- Series já presentes (Sprint 03 — preserved):
--   - SELIC 1178 (genérica + Cartão)
--   - Modalidade 217 (CDC veículos PF)
--   - IPCA 433 + TR (Imobiliário)
--   - TJLP (FIES — portarias MEC)
-- ════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ─── Tabela bacen_series_cache (preserved Sprint 03 — apenas insert NEW series) ──
INSERT INTO bacen_series_cache (series_id, descricao, fonte, populated_at)
VALUES
  (4391, 'CDI - Certificado de Depósito Interbancário (over)', 'BACEN_SGS', NULL),  -- pre-fetch chunk script
  (218, 'Taxa de juros - CDC outros bens não-veículos PF', 'BACEN_SGS', NULL)
ON CONFLICT (series_id) DO NOTHING;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════════
-- Pós-migration: Neo executa chunk script `populate_bacen_series_doctype_v2.py`:
--   - httpx + bcb (python-bcb) fetch series 4391 + 218 últimos 24 meses
--   - diskcache populate (~5min one-time)
--   - UPDATE bacen_series_cache SET populated_at = NOW() WHERE series_id IN (4391, 218);
-- ════════════════════════════════════════════════════════════════════════════
```

E pyproject.toml dependency check (validar `python-bcb>=0.3` já presente Sprint 01).

**Tested:** integration test `_REQUIRES_POSTGRES`:
- `test_bacen_series_4391_inserted` — POST migration query confirma series 4391 presente em bacen_series_cache
- `test_bacen_series_218_inserted` — idem 218
- `test_idempotent_re_run` — ON CONFLICT DO NOTHING — re-run migration não duplica

E test pós-populate (smoke): `test_bacen_fetch_4391_returns_data` — fetch CDI 4391 últimos 30d retorna ≥20 datapoints (BACEN typically diário).

### AC-07 — POST /revisar endpoint update + audit log doctype field

`bloco_interface/web/app.py` linha 580 (`@app.post("/revisar")`):

```python
@app.post("/revisar", response_class=HTMLResponse)
async def revisar(
    request: Request,
    file: UploadFile = Form(...),
    uf: str = Form(...),
    data_assinatura: str = Form(...),
    tier: LLMTier = Form("balanced"),
    doctype: Optional[str] = Form(None),  # NEW SP04-DOCTYPE-01 — sidebar SPA data-mode
) -> HTMLResponse:
    # ... validation existente preserved ...

    # NEW SP04-DOCTYPE-01: resolve dispatcher per ADR-020 §1.5
    from bloco_workflow.dispatchers.router import resolve_dispatcher
    classifier_llm = get_anthropic_client(tenant_id)  # SP04-BYOK-01 reuse

    dispatcher = resolve_dispatcher(
        ui_selector=doctype,
        contract_text=parsed_contract.text[:5000],  # prefix for classifier
        classifier_llm=classifier_llm,
    )

    # NEW: audit chain HMAC event ADR-005 + ADR-008 heartbeat metrics
    append_audit_entry(
        action="dispatcher_resolved",
        payload={
            "tenant_id": tenant_id,
            "doctype": dispatcher.doctype_id(),
            "tier_used": "ui" if doctype else "llm_classifier" if dispatcher.doctype_id() != "geral" else "geral_fallback",
            "ui_selector_provided": doctype is not None,
        },
    )

    # ... rest of pipeline (preserved — passa dispatcher para personas etc) ...
```

**Tested:** integration test `_REQUIRES_POSTGRES` + `_REQUIRES_OLLAMA`:
- `test_post_revisar_with_doctype_ccb` — FormData doctype='ccb' → audit log entry com `doctype=ccb` + `tier_used=ui`
- `test_post_revisar_without_doctype_classifier_fires` — FormData sem doctype → classifier mock retorna "cartao" → audit log com `tier_used=llm_classifier`
- `test_post_revisar_invalid_doctype_falls_to_geral` — FormData doctype='invalid' → Tier 3 GeralDispatcher → audit log com `tier_used=geral_fallback`

### AC-08 — Test coverage ≥80% bloco_workflow/dispatchers

Suíte completa:
- `tests/unit/test_dispatchers.py` (~150 LOC, 10+ tests) — Strategy hierarchy + 7 dispatchers + Template Method BancarioBase
- `tests/unit/test_router.py` (~120 LOC, 8+ tests) — 3-tier detection (UI + LLM mock + Geral fallback)
- `tests/unit/test_personas_doctype_prompts.py` (~100 LOC, 6+ tests) — 32 prompts paths + Template Method concatenation
- `tests/integration/test_doctype_e2e.py` (~80 LOC, 5 stubs `_REQUIRES_POSTGRES` + `_REQUIRES_OLLAMA`) — full cycle dispatch → personas → veredito

Coverage ≥80% bloco_workflow/dispatchers/ verificado condicionalmente (PostgreSQL + Ollama running). Sem DB+Ollama, unit-only baseline mantido (similar pattern AUTH-01/BYOK-01/LGPD-01).

**Tested:** `pytest --cov=bloco_workflow.dispatchers --cov-fail-under=80` (condicional integration).

---

## 4. Files to Modify / Add (Pre-Implementation Contract)

### Novos arquivos (Strategy backbone)

1. `bloco_workflow/dispatchers/__init__.py` (~10 LOC) — exports
2. `bloco_workflow/dispatchers/base.py` (~50 LOC) — DoctypeDispatcher abstract
3. `bloco_workflow/dispatchers/bancario_base.py` (~80 LOC) — BancarioBaseStrategy abstract intermediate
4. `bloco_workflow/dispatchers/ccb.py` (~40 LOC) — CCBDispatcher concrete
5. `bloco_workflow/dispatchers/cartao.py` (~40 LOC) — CartaoDispatcher concrete
6. `bloco_workflow/dispatchers/consignado.py` (~40 LOC) — ConsignadoDispatcher concrete
7. `bloco_workflow/dispatchers/veicular.py` (~50 LOC) — VeicularDispatcher standalone
8. `bloco_workflow/dispatchers/fies.py` (~50 LOC) — FIESDispatcher standalone
9. `bloco_workflow/dispatchers/imobiliario.py` (~50 LOC) — ImobiliarioDispatcher standalone
10. `bloco_workflow/dispatchers/geral.py` (~50 LOC) — GeralDispatcher catch-all
11. `bloco_workflow/dispatchers/router.py` (~80 LOC) — resolve_dispatcher() 3-tier

### Novos persona prompts (16 NEW + 12 preserved/migrated)

Em `bloco_workflow/personas/prompts/`:
- 4 base bancário (Trinity content) — `{persona}_bancario_base.txt`
- 12 sub-bancários specific (Trinity content) — `{persona}_{ccb,cartao,consignado}_specific.txt`
- 4 Geral standalone (Trinity content) — `{persona}_geral.txt`
- 12 standalone preserved/migrated — `{persona}_{veicular,fies,imobiliario}.txt`

### Novas migrations SQL

12. `bloco_database/migrations/sp04_004_doctype_tag_v2.sql` (~60 LOC) — vault enum + backfill
13. `bloco_database/migrations/sp04_005_bacen_series_doctype_v2.sql` (~30 LOC) — BACEN series 4391+218

### Novos tests

14. `tests/unit/test_dispatchers.py` (~150 LOC, 10+ tests)
15. `tests/unit/test_router.py` (~120 LOC, 8+ tests)
16. `tests/unit/test_personas_doctype_prompts.py` (~100 LOC, 6+ tests)
17. `tests/integration/test_doctype_e2e.py` (~80 LOC, 5 stubs)

### Modificados (3-4)

18. `bloco_interface/web/app.py` — endpoint `POST /revisar` adiciona `doctype: Optional[str] = Form(None)` + chama `resolve_dispatcher()` + audit log event `dispatcher_resolved`
19. `bloco_workflow/__init__.py` — possivelmente adicionar export dispatchers se needed
20. `pyproject.toml` — packages.find adicionar `"bloco_workflow.dispatchers*"` se sub-package detection needed
21. `governance/TECH-DEBT.md` — adicionar TD-SP04-12 (vault re-classify) + TD-SP04-13 (vault gaps)

### Pendências cross-domain (não implementação Neo)

- ⏳ **Trinity (@pm) MANDATORY pre-implement chunks 5-6:** conteúdo legal substantivo dos 16 prompts NOVOS (4 base bancário + 12 sub-bancários + 4 Geral). Trinity Phase 3 PRD update OR documento dedicado.
- ⏳ **Tank ratify pre-implement chunk 4:** validar migration sp04_004 backfill strategy + sp04_005 BACEN series IDs corretos (Tank confirma CDI 4391 + modalidade 218 são BACEN-canonical).
- ⏳ **Operator MANDATORY:** PR #4 + #5 + #6 merged em main antes de chunk 1 (clean rebase base) — DEC-ERIC-MERGE-ORDER pendente.
- 🟢 **Aria ✅ DONE:** ADR-020 entregue Accepted 2026-05-09 com implementation specs completos.
- ⏭ **Sati N/A:** Backend story — sidebar UX já entregue Sati Phase 4 (frontend SP04-UI-SPA-01 escopo).
- ⏭ **Eric advogado N/A:** DPA/TOS preserved (SP04-LGPD-01 reuso).

---

## 5. Pre-flight Consultation

### @architect Aria (✅ DONE 2026-05-09 — ADR-020 Accepted)

**Status:** ✅ DONE — ADR-020 (Accepted 2026-05-09) entrega implementation specs definitivos:
- Strategy hierárquica 3-camada (§1.1-1.3)
- Detecção 3-tier (§1.5)
- 32 prompt files Template Method DRY (§1.4)
- Migration vault doctype_tag enum (§1.6)
- BACEN series novas (§1.7)

Aria pre-flight CONCLUÍDO via ADR-020. Sem nova decisão arquitetural necessária.

### @data-engineer Tank (MANDATORY pre-implement chunk 4)

**Status:** Tank ratify mandatory antes Neo chunk 4 (migrations DB):
- Validar `sp04_004_doctype_tag_v2.sql` — backfill strategy `bancario` → `bancario_cross` adequado (zero data loss)?
- Validar `sp04_005_bacen_series_doctype_v2.sql` — CDI 4391 + modalidade 218 são BACEN SGS series IDs canônicos? (Tank verifica via python-bcb OR docs BACEN)
- Validar enum strict CHECK constraint pattern consistente com sp04_001/002/003 BACKBONE
- Validar idempotência migrations (DROP CONSTRAINT IF EXISTS + ON CONFLICT DO NOTHING)

**River expectativa:** Tank ratify LIGHT — pattern consistente migrations Sprint 04 anteriores. Estimate ~15-30min.

### @pm Trinity (MANDATORY pre-implement chunks 5-6 — cross-domain bloqueio)

**Status:** ⏳ Trinity Phase 3 PRD update **MANDATORY** pre-implement chunks 5-6:

Trinity entrega conteúdo legal substantivo dos **16 prompts NOVOS** (4 base bancário + 12 sub-bancários + 4 Geral standalone):

| Categoria | Prompts | Conteúdo legal |
|-----------|---------|----------------|
| Bancário base (4) | `{persona}_bancario_base.txt` | Fundamentação CDC base + BACEN Resolução 4.558/2017 + Lei 4.595/64 + cláusulas abusivas comuns |
| CCB specific (4) | `{persona}_ccb_specific.txt` | Anatocismo + capitalização juros + Súmulas CCB |
| Cartão specific (4) | `{persona}_cartao_specific.txt` | Súmula 530 STJ venda casada + rotativo + IOF |
| Consignado specific (4) | `{persona}_consignado_specific.txt` | Lei 10.820/2003 + cap 35% + Súmula 603 STJ |
| Geral (4) | `{persona}_geral.txt` | Genérico catch-all (CDC base + cross-doctype) |

**Bloqueio:** Neo NÃO pode entregar chunks 5-6 sem Trinity content. **Mitigação:** Neo entrega skeletons placeholder estrutural (pattern AUTH-01 chunk 5 Eric advogado) em chunks 5; Trinity preenche conteúdo substantivo paralelo; chunk 6 fechamento aguarda Trinity done.

**Estimate Trinity:** ~2-3 days work (16 prompts × ~30min cada legal review).

### @ux-design-expert Sati (NÃO necessário — backend story)

**Status:** Esta story é backend dispatcher. Sidebar UX 7 modos já entregue Sati Phase 4 (escopo SP04-UI-SPA-01). Sati pre-flight skipped.

### @qa Oracle Smith (post-merge — defer)

**Status:** Smith adversarial review (Sprint 04 close-out) avalia Strategy hierarchy correctness + 3-tier detection coverage + audit log doctype tracking. Defer para qa-gate G5 OR post-merge.

### Eric advogado (NÃO necessário esta story)

**Status:** DPA/TOS preserved (SP04-LGPD-01 reuso). Trinity entrega prompts legais — não DPA texts.

### @qa Oracle Tank (Tank dual mention — Phase 14.4a ratify LIGHT esperado)

**Status:** Após @data-engineer Tank ratify pre-implement chunk 4, Tank entrega "Tank Phase 14.4a LIGHT" doc com 2-3 itens validados (mirror pattern Phase 12.3a BYOK-01 + Phase 13.3a LGPD-01). Documento blocks Neo *develop chunks 4 até Tank green-light.

---

## 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **R-01** Trinity Phase 3 PRD bloqueio templates D3 conteúdo legal (16 prompts NOVOS) | MÉDIA | HIGH (timeline) | Pattern AUTH-01 chunk 5 placeholder validado: Neo entrega skeletons estruturais em chunks 5; Trinity preenche conteúdo paralelo (~2-3 days); chunk 6 fechamento aguarda Trinity done. WAIVED-DOCTYPE-01 HIGH se Trinity atrasa — bloqueia close-story Done mas não code structure |
| **R-02** Vault re-classify backfill 'bancario' → 'bancario_cross' não-perfeito | BAIXA | LOW | Backfill conservador (zero data loss — entries continuam queryable). TD-SP04-12 MEDIUM Sprint 06+ refinement granular ccb/cartao/consignado curadoria manual ~50 entries STJ |
| **R-03** BACEN CDI 4391 fetch failure (httpx + python-bcb) | BAIXA | LOW | python-bcb >= 0.3 já presente Sprint 01 (validated). Fallback graceful: BACEN offline mode existente (Sprint 03 pattern) — vault dispatcher continua, apenas BACEN reference vazia |
| **R-04** LLM Haiku classifier latency (5-7s adicional Tier 2) | MÉDIA | MEDIUM | Tier 2 só dispara quando UI selector ausente (advogado pulou sidebar). Truncate contract_text[:2000] reduz tokens. Cost ~$0.001/análise per ADR-014. Métricas distribution via ADR-008 heartbeat para avaliar Tier 2 frequency Sprint 06+ |
| **R-05** Strategy refactor breaking currently-running pipeline | BAIXA | LOW | **Greenfield refactor** — ADR-016 não foi implementado (zero código legacy a remover). Atual pipeline Sprint 03 usa personas single-track sem dispatcher. SP04-DOCTYPE-01 wraps + adiciona dispatcher resolution layer — backward compat preserved se doctype ausente (Tier 3 fallback) |
| **R-06** 32 prompt files revisão jurídica per-doctype overhead Sprint 06+ | MÉDIA | MEDIUM | Pattern revisão Sati R-NEW Sprint 03 escala — Trinity revisões periódicas paralelo Sprint cycles. Trade-off aceito vs DRY violation se fundisse em template parametrizado (perderia nuance jurídica per-doctype) |
| **R-07** doctype_tag enum migration breaking existing vault queries | BAIXA | LOW | DROP CONSTRAINT + ADD CONSTRAINT idempotente. Backfill conservador `bancario` → `bancario_cross`. Rollback documentado em SQL comments |
| **R-08** Tank ratify pre-implement chunk 4 demanda mais que LIGHT | BAIXA | LOW | Pattern consistente Sprint 04 sp04_001/002/003. Esperado LIGHT ratify ~15-30min. Se Tank promove HEAVY review (BANCO refinement), River patch story conforme (não-bloqueante implementation cores chunks 1-3) |

---

## 7. Implementation Plan (Path B chunks sugeridos — Neo refina)

Pattern Path B SP04-AUTH-01/BYOK-01/LGPD-01/UI-SPA-01 adaptado para backend dispatcher:

1. **Chunk 1** — Setup environment: branch `feat/sp04-doctype-01` (base main pós-merge PR #4+#5+#6) + skeleton structure `bloco_workflow/dispatchers/__init__.py` + tests/{unit,integration}/test_dispatchers.py + test_router.py + test_personas_doctype_prompts.py + test_doctype_e2e.py (skeleton imports only)

2. **Chunk 2** — Strategy backbone abstracts: `base.py` DoctypeDispatcher + `bancario_base.py` BancarioBaseStrategy + ~6 unit tests Template Method + abstract instantiation TypeError

3. **Chunk 3** — 7 concrete dispatchers + router: `ccb.py` + `cartao.py` + `consignado.py` (BancarioBase subclasses) + `veicular.py` + `fies.py` + `imobiliario.py` + `geral.py` (standalone) + `router.py` resolve_dispatcher() 3-tier + ~10 unit tests dispatchers + ~8 unit tests router

4. **Chunk 4** — Migrations SQL + Tank ratify pre-flight: `sp04_004_doctype_tag_v2.sql` + `sp04_005_bacen_series_doctype_v2.sql` + Tank Phase 14.4a LIGHT validation (~15-30min) + ~3 integration tests `_REQUIRES_POSTGRES` migrations idempotência

5. **Chunk 5** — Persona prompt skeletons (Trinity bloqueio cross-domain): 16 NEW skeletons placeholder estrutural + 12 standalone preserved/migrated + ~6 unit tests prompt files exist + Template Method concatenation. **Trinity preenche conteúdo paralelo (não bloqueia chunk 5 done — bloqueia chunk 7 close)**

6. **Chunk 6** — Endpoint POST /revisar update + audit log: `bloco_interface/web/app.py` doctype field + resolve_dispatcher() call + audit chain `dispatcher_resolved` event + ~3 integration tests E2E `_REQUIRES_POSTGRES` + `_REQUIRES_OLLAMA`

7. **Chunk 7** — Closure DoD + Trinity content integration + handoff Oracle: aguarda Trinity 16 prompts content done + Final File List Consolidado + Section 8 DoD VERIFIED + WAIVED format (LGPD-04 CodeRabbit pattern + WAIVED-DOCTYPE-01 HIGH se Trinity atrasa) + handoff @qa Oracle qa-gate G5

**Estimativa River:** 3-5 days Neo (chunk 6 maior — 1-2 days; chunk 7 fechamento aguarda Trinity ~2-3 days paralelo, total 3-5 days end-to-end OR 5-7 days se Trinity sequencial)

**Branch creation timing:** `feat/sp04-doctype-01` base **main pós-merge** PR #4 + #5 + #6 (clean rebase). Pode iniciar paralelo SP04-UI-SPA-01 (zero overlap).

---

## 8. Definition of Done (Neo Phase 14.5+ — populated empíricamente chunks 1-7)

### VERIFIED (target ≥10 items)

- [ ] AC-01 Strategy backbone abstracts (DoctypeDispatcher + BancarioBaseStrategy)
- [ ] AC-02 7 concrete dispatchers (3 sub-bancários + 4 standalone + Geral catch-all)
- [ ] AC-03 Router resolve_dispatcher() 3-tier (UI + LLM + Geral fallback)
- [ ] AC-04 32 persona prompt files com Template Method DRY (Trinity content done)
- [ ] AC-05 Migration sp04_004 vault doctype_tag enum 5 → 8 + backfill conservador
- [ ] AC-06 Migration sp04_005 BACEN series CDI 4391 + modalidade 218 + populate
- [ ] AC-07 POST /revisar endpoint + audit log dispatcher_resolved
- [ ] AC-08 Test coverage ≥80% bloco_workflow/dispatchers (unit + integration condicional)
- [ ] Suite testes ≥352+N (zero regression)
- [ ] CI verde Python 3.11 + 3.12

### WAIVED (a popular conforme empíria — pattern SP04-LGPD-01)

(Possíveis waivers esperados:)
- WAIVED-DOCTYPE-01 HIGH se Trinity Phase 3 PRD content atrasa (skeleton placeholder fix-by date)
- WAIVED-DOCTYPE-02 MEDIUM Integration tests `_REQUIRES_POSTGRES` + `_REQUIRES_OLLAMA` skipped sem Docker (pattern AUTH-01/BYOK-01/LGPD-01)
- WAIVED-DOCTYPE-03 LOW CodeRabbit DEFERRED (pattern Sprint 04)
- WAIVED-DOCTYPE-04 LOW Smith adversarial review post-merge defer

---

## 9. QA Validation (@po Keymaker — *validate-story-draft G3) — PENDENTE

**Status:** Story em **Draft**. Validate G3 só após:
1. ✅ ADR-020 Accepted (entregue 2026-05-09)
2. ✅ Trinity Phase 3 PRD update — RESOLVED via PRD v2.0.1 PATCH 2026-05-09 (skeleton placeholder pattern)
3. ⏳ Tank ratify pre-implement chunk 4 (LIGHT validation — não bloqueia G3, bloqueia chunk 4 only)
4. ⏳ DEC-ERIC-MERGE-ORDER resolved (não bloqueia G3, bloqueia chunk 1 only)
5. ✅ Skill `LMAS:agents:po` `*validate-story-draft SP04-DOCTYPE-01`

### Verdict @po Keymaker (2026-05-09T22:35)

**Verdict:** ✅ **GO** | **Score: 10/10** | **Status:** Draft → **Ready**

> Score perfeito — paridade SP04-UI-SPA-01 G3 PASS (template Sprint 04 maduro). Trinity content bloqueio HIGH resolvido via PRD v2.0.1 (Morgan 2026-05-09). Skeleton placeholder pattern AUTH-01/LGPD-01 reutilizado validamente.

#### 10-point checklist (todos PASS)

| # | Ponto | Score | Evidência |
|---|-------|-------|-----------|
| 1 | Frontmatter completo (18+ campos) | ✅ 1/1 | Paridade SP04-UI-SPA-01 + 6 source_frs + 8 dependencies |
| 2 | Sumário Section 1 claro | ✅ 1/1 | 6 deliverables + foundation impact + Trinity bloqueio nota |
| 3 | As a / I want / So that | ✅ 1/1 | Advogado tenant + workflow per-doctype + tese jurídica defensável |
| 4 | ACs estruturadas (8 ACs) | ✅ 1/1 | AC-01..AC-08 com Tested + code blocks (Strategy + 7 dispatchers + Router 3-tier + 32 prompts + 2 migrations + endpoint + tests) |
| 5 | File List Section 4 | ✅ 1/1 | 11 dispatchers + 16 prompts NEW + 2 migrations + 4 tests + 4 modificados |
| 6 | Pre-flight Section 5 | ✅ 1/1 | Aria ✅ DONE + Tank MANDATORY chunk 4 + Trinity ✅ RESOLVED PRD v2.0.1 + Sati N/A + Eric advogado N/A |
| 7 | Risk Assessment (8 risks) | ✅ 1/1 | R-01..R-08 com P/I/M; R-01 Trinity HIGH downgrade post-PRD v2.0.1 |
| 8 | Implementation Plan (7 chunks) | ✅ 1/1 | Path B sequencial chunks 1-7 + paralelo Trinity work |
| 9 | Cross-references | ✅ 1/1 | PRD v2.0.0/v2.0.1 + ADR-003/014/016/017/020 + 4 predecessor stories + Sati UX + Smith F-016 |
| 10 | Dependencies + source_frs | ✅ 1/1 | 8 deps + 6 source_frs (FR-DOCTYPE-01..02 + FR-PERSONAS-01..03 + FR-VAULT-01 + FR-BACEN-01 + FR-AUDIT-01) |
| **TOTAL** | | **10/10** | **GO threshold ≥7/10 — exceeded by 3** |

#### 3 Concerns Keymaker (non-bloqueantes G3)

| # | Concern | Severidade | Decisão |
|---|---------|-----------|---------|
| **K-DOCTYPE-01** | Trinity content skeleton placeholder ainda requer Eric advogado preenchimento (~9.5h) | LOW | ✅ ACEITO — pattern AUTH-01 chunk 5 + LGPD-01 DPA validados precedentes; PRD v2.0.1 fornece estrutura + cronograma |
| **K-DOCTYPE-02** | Tank MANDATORY chunk 4 (migrations sp04_004 + sp04_005 LIGHT validation) | MEDIUM | ⚠️ Non-blocking G3 — bloqueia downstream chunk 4 only. Pattern Sprint 04 mature (~15-30min Tank LIGHT) |
| **K-DOCTYPE-03** | DEC-ERIC-MERGE-ORDER pendente (PR #4+#5+#6 merge antes chunk 1) | MEDIUM | ⚠️ Non-blocking G3 — Section 7 timing condicional explícito; story Ready ≠ Neo *develop pode iniciar agora |

#### Próximo step

**Recomendação Keymaker:** chain paralela:
1. ⏳ Eric merge PR #4+#5+#6 + DEC-ERIC-LEGAL-CONTENT-START
2. ✅ Skill `LMAS:agents:data-engineer` Tank ratify pre-implement chunk 4 LIGHT
3. ✅ Skill `LMAS:agents:dev` Neo *develop SP04-DOCTYPE-01 chunks 1-3 (skeleton paralelo Eric advogado work + paralelo SP04-UI-SPA-01 chunks)

— Keymaker, equilibrando prioridades 🎯

---

## 10. Anti-Patterns (Defensive Scope Guard)

- ❌ Implementar dispatcher backend ANTES de Trinity content prompts (skeleton OK; conteúdo legal substantivo é Trinity)
- ❌ Bypass Tank ratify pre-implement chunk 4 (migrations DB sem Tank LIGHT validation pode introduzir corruption)
- ❌ Modificar bloco_workflow/personas/__init__.py existente sem care (preserva ADR-003 base — Strategy é wrap, não substitui)
- ❌ LLM-only classifier (sem Tier 1 UI) — preserve UX hierarchy SPA sidebar autoritativo
- ❌ Reject unknown doctype (sem Tier 3 GeralDispatcher) — UX coerente é catch-all per ADR-020
- ❌ Hardcode dispatcher mapping em endpoint app.py — usar router.py centralized
- ❌ Implementar 8º doctype futuro sem nova ADR (extensibility é nova ADR + nova classe + 4 prompts)
- ❌ Fundir 32 prompts em template parametrizado (DRY violation overcome — perderia nuance per-doctype)
- ❌ Modificar bacen_series_cache schema sem Tank ratify (data integrity ON CONFLICT DO NOTHING preserve safety)

---

## 11. Files NOT to Modify (Defensive Scope Guard)

Esta story **NÃO** modifica:
- `bloco_workflow/personas/__init__.py` (ADR-003 base preserved — Strategy wrap)
- `bloco_workflow/personas/llm_factory.py` (ADR-010 superseded ADR-014 BYOK runtime — preserved)
- `bloco_auth/*` (foundation Sprint 04 — não tocado)
- `bloco_audit/chain.py` (audit ADR-005 — apenas chama append_audit_entry()`, não modifica)
- `bloco_interface/web/app.py` outros endpoints (apenas POST /revisar tocado per AC-07)
- Migrations sp04_001/002/003 (foundation — não tocado)
- `bloco_engine/`, `bloco_vault/`, `bloco_audit/`, `bloco_lgpd/`, `bloco_database/db.py` — foundation Sprint 03/04 untouched
- pyproject.toml dependencies (apenas packages.find sub-package se needed; sem novo dep)

---

## 12. Change Log

| Data | Versão | Autor | Descrição |
|------|--------|-------|-----------|
| 2026-05-09 | v1.0.0-DRAFT | @sm River | Story criada conforme ADR-020 (Accepted 2026-05-09) §1-7 implementation specs. Status Draft — bloqueada por Trinity Phase 3 PRD content cross-domain (16 prompts NOVOS conteúdo legal) + Tank ratify pre-implement chunk 4 + DEC-ERIC-MERGE-ORDER pendente. 8 ACs estruturadas com Tested explícito + code blocks copy-paste-ready. River-decision: Strategy hierárquica DRY via BancarioBaseStrategy (ADR-020 §1.2) + Tier 3 GeralDispatcher catch-all (UX coerente vs ADR-016 unknown rejection). Pre-flight Aria DONE + Tank MANDATORY + Trinity MANDATORY (cross-domain bloqueio chunks 5-6). 8 risks documentados (R-01 Trinity HIGH bloqueio + R-04 LLM classifier latency MEDIUM + R-06 prompts overhead MEDIUM + 5 LOW). Implementation Plan 7 chunks Path B (chunk 1-3 paralelo Trinity + chunks 4-7 sequenciais). Estimativa 3-5 days Neo (paralelo Trinity ~2-3 days). Branch sugerido: feat/sp04-doctype-01 base main pós-merge PR #4+#5+#6. Pode rodar paralelo SP04-UI-SPA-01 (zero overlap implementation). Próxima Skill: aguardar Trinity content commitment OR `LMAS:agents:po` Keymaker G3 conservador. |

---

```
[@sm · River (Facilitator)] — drafted 2026-05-09 sessão SPA integration paralelo
"Sete portas, três compartilham o umbral, três se erguem sozinhas, uma acolhe os errantes.
 Trinity preenche os textos jurídicos; Tank valida os caminhos do banco;
 Neo conecta as pontes. Esta story é o desenho que torna a UI sidebar
 finalmente significativa — não decorativa."

— River, removendo obstáculos 🌊
```
