---
type: adr
id: "ADR-020"
title: "Multi-Doctype Dispatcher v2 — Strategy hierárquica com 7 doctypes operacionais (supersedes ADR-016)"
status: accepted
date: "2026-05-09"
accepted_by: "Eric Claudino (avance ratify implícito sessão 2026-05-09)"
accepted_date: "2026-05-09"
domain: software-dev/legaltech
adr_level: spec
decision_makers:
  - "@architect (Aria) — design"
  - "Eric Claudino — autorização sidebar 7 modos UX (DEC-ERIC-DIV-01 = Opção A) + RATIFY Accepted (avance implícito 2026-05-09)"
supersedes: "ADR-016"
superseded_by: ""
related_to:
  - "ADR-003 (4 personas implementation — base preserved)"
  - "ADR-014 (Anthropic SDK BYOK runtime — provider stack mantido)"
  - "ADR-017 (multi-tenant Pool+RLS BACKBONE — vault SHARED com doctype_tag preserved)"
  - "ADR-019 (DPA Storage Schema — pattern audit pode ser referenciado)"
spec_coverage:
  - "Hierarquia abstract: DoctypeDispatcher → BancarioBaseStrategy → 3 concrete bancários"
  - "7 doctypes operacionais com mapping UI 7 sidebar buttons → backend strategies"
  - "28 persona prompt files (4 personas × 7 doctypes) com template method pattern em BancarioBase"
  - "Vault doctype_tag enum expandido (8 valores: 7 doctypes + cross)"
  - "BACEN SGS series adicionais para Cartão (CDI 4391 + SELIC 1178)"
  - "Migration plan ADR-016 → ADR-020 (zero implementação a remover — SP04-DOCTYPE-01 ainda Sprint 04 P1)"
project: revisor-contratual
sprint: "04"
phase: "14.1"
trigger: "Eric SPA OrSheva 7 (index.html raiz 95KB, 2026-05-09 15:55) sidebar 7 modos análise vs ADR-016 4 doctypes — DEC-ERIC-DIV-01 Opção A"
tags:
  - project/revisor-contratual
  - adr
  - sprint-04
  - multi-doctype
  - strategy-pattern
  - supersedes-016
  - ui-driven
---

# ADR-020: Multi-Doctype Dispatcher v2 — 7 doctypes operacionais

## Contexto

Eric commitou em 2026-05-09 15:55 o `index.html` raiz (95KB SPA OrSheva 7) que implementa visualmente a UX Spec v2.0.0 do Sati (Phase 4, 2026-05-07). A sidebar do SPA expõe **7 modos de análise** numerados:

| # | Modo SPA | data-mode |
|---|----------|-----------|
| 01 | CCB Bancária | `ccb` |
| 02 | Financiamento Veículo | `veiculo` |
| 03 | Empréstimo Consignado | `consignado` |
| 04 | Cartão de Crédito | `cartao` |
| 05 | Imobiliário (SFH/SFI) | `imobiliario` |
| 06 | FIES (Estudantil) | `fies` |
| 07 | Análise Geral | `geral` |

Esta exposição UX colide com **ADR-016** (Accepted Eric 2026-05-07), que define apenas **4 doctypes** dispatcher:
- FIES
- Veicular
- Bancário (genérico — abrange CCB/Cartão/Consignado implicitamente)
- Imobiliário

Eric resolveu a divergência DEC-ERIC-DIV-01 escolhendo **Opção A**: manter os 7 modos UX (River recommendation) e patchar a arquitetura. Esta ADR formaliza a evolução.

**Sinais convergentes para 7 doctypes operacionais:**

1. **Especificidade jurídica:** CCB tem fundamentação anatocismo + capitalização diferente de Cartão de Crédito (Súmula 530 STJ venda casada) e de Consignado (Lei 10.820/2003 + cap 35% margem). Tratá-los como "Bancário" genérico apaga nuances que mudam a tese da revisional.
2. **BACEN modalidades distintas:** Cartão usa séries CDI (4391) + SELIC (1178); CCB usa modalidade 217 (CDC PF Veículos) ou 218 (CDC outros bens); Consignado usa modalidade 419 (consignado privado) ou 432 (consignado público). Mapeamento 1:1 com modalidade simplifica fetch BACEN SGS.
3. **Templates D3 (peticionamento):** Apelação Cível CCB tem fundamentação contábil diferente de Apelação Cartão (cobrança rotativa) ou Consignado (margem consignável). Templates separados ≠ DRY violação — são domínios jurídicos distintos.
4. **Geral como fallback:** advogado pode receber contrato atípico (ex: empréstimo pessoal não-consignado, CDC outros bens). Strategy genérica processa via vault `cross-tag` + persona prompts genéricos sem forçar classificação errada.

**Sinais para preservar abstração compartilhada (DRY):**

- CCB + Cartão + Consignado compartilham regulação BACEN base (Resolução 4.558/2017, Lei 4.595/64), validações de juros remuneratórios, e estrutura de cláusulas abusivas (CDC). Refatorar todos para 7 strategies independentes duplicaria ~40% do código.

## Decisão

**Strategy hierárquica 3-camada:**

```
DoctypeDispatcher (abstract base — interface contratual)
├── BancarioBaseStrategy (abstract intermediate — DRY para domínio bancário)
│   ├── CCBDispatcher (concrete)
│   ├── CartaoDispatcher (concrete)
│   └── ConsignadoDispatcher (concrete)
├── VeicularDispatcher (concrete — independente)
├── FIESDispatcher (concrete — independente)
├── ImobiliarioDispatcher (concrete — independente)
└── GeralDispatcher (concrete — catch-all fallback)
```

### Componentes

#### 1. Abstract base `DoctypeDispatcher` (preserved from ADR-016)

```python
# bloco_workflow/dispatchers/base.py
from abc import ABC, abstractmethod
from typing import Sequence

class DoctypeDispatcher(ABC):
    """Interface contratual para todos os doctypes (ADR-020 supersedes ADR-016)."""

    @abstractmethod
    def get_personas(self) -> Sequence["Persona"]: ...
    @abstractmethod
    def get_d3_template(self) -> str: ...
    @abstractmethod
    def get_jurisprudencia_filter(self) -> dict: ...
    @abstractmethod
    def get_bacen_modalidade(self) -> str: ...
    @abstractmethod
    def doctype_id(self) -> str: ...  # NEW: retorna sidebar data-mode
```

#### 2. Abstract intermediate `BancarioBaseStrategy` (NEW — Template Method pattern)

```python
# bloco_workflow/dispatchers/bancario_base.py
class BancarioBaseStrategy(DoctypeDispatcher, ABC):
    """Compartilha lógica BACEN + cláusulas abusivas CDC.
    Sub-classes (CCB, Cartao, Consignado) override doctype_specific_section().
    """

    # Implementações compartilhadas (template method)
    def get_jurisprudencia_filter(self) -> dict:
        return {
            "tags": [self.doctype_id(), "bancario_cross", "cdc_cross"]
        }

    def get_personas(self) -> Sequence["Persona"]:
        # BancarioBase carrega prompts {persona}_bancario_base.txt
        # + override doctype_specific_section() em sub-classes
        return [
            self._build_persona("advogado"),
            self._build_persona("economista"),
            self._build_persona("validador"),
            self._build_persona("juiz"),
        ]

    def _build_persona(self, role: str) -> "Persona":
        base_prompt = _load(f"prompts/{role}_bancario_base.txt")
        specific = self.doctype_specific_section(role)
        return Persona(role=role, prompt=f"{base_prompt}\n\n{specific}")

    @abstractmethod
    def doctype_specific_section(self, persona_role: str) -> str:
        """Cada sub-class CCB/Cartao/Consignado fornece nuances específicas."""
```

#### 3. Concrete dispatchers (7 total)

| Dispatcher | Herda de | doctype_id | BACEN modalidade | Templates D3 |
|------------|----------|------------|------------------|--------------|
| `CCBDispatcher` | `BancarioBaseStrategy` | `ccb` | 217 (CDC veículos) ou 218 (CDC outros) | `ccb.txt` |
| `CartaoDispatcher` | `BancarioBaseStrategy` | `cartao` | CDI 4391 + SELIC 1178 | `cartao.txt` |
| `ConsignadoDispatcher` | `BancarioBaseStrategy` | `consignado` | 419 (privado) ou 432 (público) | `consignado.txt` |
| `VeicularDispatcher` | `DoctypeDispatcher` | `veiculo` | 217 (CDC veículos PF) | `veicular.txt` |
| `FIESDispatcher` | `DoctypeDispatcher` | `fies` | TJLP/TR (séries específicas) | `fies.txt` |
| `ImobiliarioDispatcher` | `DoctypeDispatcher` | `imobiliario` | TR + Poupança IPCA | `imobiliario.txt` |
| `GeralDispatcher` | `DoctypeDispatcher` | `geral` | SELIC (1178) genérica | `geral.txt` |

#### 4. Persona prompts: 28 arquivos com template method

Em `bloco_workflow/personas/prompts/`:

```
advogado_bancario_base.txt          # base compartilhado CCB/Cartao/Consignado
  + advogado_ccb_specific.txt       # nuances anatocismo + Resolução 4.558
  + advogado_cartao_specific.txt    # nuances rotativo + Súmula 530 STJ venda casada
  + advogado_consignado_specific.txt # nuances margem 35% + Lei 10.820/2003

advogado_veicular.txt               # standalone (preserved ADR-016)
advogado_fies.txt                   # standalone (preserved ADR-016)
advogado_imobiliario.txt            # standalone (preserved ADR-016)
advogado_geral.txt                  # genérico fallback

# Mesmo padrão para economista, validador, juiz → 4 personas × 7 doctypes,
# mas CCB/Cartao/Consignado compartilham _bancario_base prompts (DRY).
# Total: 4 (bancario_base) + 12 (3 sub × 4 personas specific) + 16 (4 standalone × 4 personas) = 32 arquivos.
# Net vs ADR-016 (16 arquivos): +16 arquivos para 3 doctypes adicionais (CCB/Cartao/Consignado/Geral)
```

**Net total:** 32 prompt files (vs 16 em ADR-016 — incremento +16 para 3 sub-bancários DRY-compartilhados via base + Geral standalone).

#### 5. Detecção doctype (3-tier — preserved + extended)

```python
# bloco_workflow/dispatchers/router.py
def resolve_dispatcher(
    ui_selector: str | None,         # PRIMARY: SPA sidebar data-mode
    contract_text: str,              # FALLBACK input
    classifier_llm: AnthropicClient,
) -> DoctypeDispatcher:
    DISPATCHERS = {
        "ccb": CCBDispatcher,
        "cartao": CartaoDispatcher,
        "consignado": ConsignadoDispatcher,
        "veiculo": VeicularDispatcher,
        "fies": FIESDispatcher,
        "imobiliario": ImobiliarioDispatcher,
        "geral": GeralDispatcher,
    }

    # Tier 1: UI selector (advogado escolheu na sidebar)
    if ui_selector and ui_selector in DISPATCHERS:
        return DISPATCHERS[ui_selector]()

    # Tier 2: LLM classifier Haiku 4.5 ($0.001/análise)
    classified = classifier_llm.classify(
        contract_text,
        labels=list(DISPATCHERS.keys()) + ["unknown"],
    )
    if classified in DISPATCHERS:
        return DISPATCHERS[classified]()

    # Tier 3: GeralDispatcher (catch-all fallback)
    return GeralDispatcher()
```

**Mudança vs ADR-016:** Tier 3 fallback **agora é GeralDispatcher** (era `unknown` rejection). Garante que advogado nunca recebe erro "doctype não suportado" — sempre roda análise via prompts genéricos.

#### 6. Vault `doctype_tag` enum expandido

Migration `sp04_004_doctype_tag_v2.sql`:

```sql
-- Antes (ADR-016): 5 valores (veicular | fies | bancario | imobiliario | cross)
-- Depois (ADR-020): 8 valores
ALTER TABLE jurisprudencia
  DROP CONSTRAINT jurisprudencia_doctype_tag_check;

ALTER TABLE jurisprudencia
  ADD CONSTRAINT jurisprudencia_doctype_tag_check CHECK (
    doctype_tag IN (
      'ccb', 'cartao', 'consignado',  -- NEW Sprint 04 ADR-020
      'veiculo', 'fies', 'imobiliario', 'geral',  -- preserved + geral NEW
      'bancario_cross',  -- NEW: Súmulas aplicáveis a CCB+Cartao+Consignado
      'cdc_cross',       -- aplicável a TODOS bancários (CDC base)
      'cross'            -- preserved: aplicável cross-doctype (qualquer)
    )
  );

-- Backfill: ADR-016 vault entries com tag 'bancario' precisam re-classificação
-- TD-SP04-12 (NEW): curadoria manual ~50 entries STJ banco → ccb/cartao/consignado/bancario_cross
UPDATE jurisprudencia SET doctype_tag = 'bancario_cross'
  WHERE doctype_tag = 'bancario';  -- conservative initial backfill
```

#### 7. BACEN SGS series adicionais

| Doctype | Series novas necessárias | Já presente? |
|---------|-------------------------|--------------|
| Cartão | CDI 4391, SELIC 1178 | SELIC 1178 já carregada (Sprint 03); **CDI 4391 NEW** |
| Consignado | — (cap regulamentar Lei 10.820, sem série BACEN específica) | N/A |
| CCB | 217 (CDC veículos), 218 (CDC outros) | 217 já carregada (Sprint 03); **218 NEW** |
| Geral | SELIC 1178, IPCA (433) | Ambas já carregadas |

**Migration `sp04_005_bacen_series_doctype_v2.sql`:** popular cache BACEN SGS para 4391 + 218 (~5min via httpx + bcb).

## Razão

- **Strategy hierárquica vs flat 7 strategies:** os 3 doctypes bancários compartilham regulação base (Lei 4.595/64, Resolução BACEN 4.558/2017, CDC base) — `BancarioBaseStrategy` consolida em 1 abstract intermediate, evitando duplicação de ~40% do código (validações cláusulas abusivas + persona prompts base + jurisprudência cross-bancária). Pure flat 7 strategies seria DRY violation.
- **GeralDispatcher como catch-all (Tier 3):** advogado pode upload contrato atípico (não bancário/veicular/FIES/imobiliário). Em ADR-016 isso virava `unknown` rejection — UX ruim. Tier 3 GeralDispatcher processa via prompts genéricos + vault `cross` tag, sempre entregando algum diagnóstico (mesmo que generalizado).
- **doctype_tag enum 5 → 8 valores:** preserves backward compat (`veiculo|fies|imobiliario|cross` mantidos) + 4 novos valores (`ccb|cartao|consignado|geral|bancario_cross`). `bancario` legacy backfill conservador para `bancario_cross` (Sprint 06+ refinement).
- **28 arquivos prompts vs 16 em ADR-016:** +12 prompts (3 sub-bancários × 4 personas) para BancarioBase + +4 prompts (Geral × 4 personas). Trade-off aceito porque revisão jurídica per-doctype é benefício clínico maior do que custo de manter 28 arquivos.
- **adr_level: spec (não design):** este ADR carrega detalhes implementáveis (paths exatos, signatures, enum values, BACEN series IDs, migration SQL). Smith pode promover ADR-016 retro→spec se identificar premissa não-validada — neste caso já formalizo como spec desde início para evitar gaps de implementação que River apontou em handoff brief.

## Alternativas Consideradas

### Alt-1: Manter ADR-016 (4 doctypes) + UI agrupar 7 visualmente

**Rejeitada.** SPA sidebar visual mostraria 7 buttons mas backend processaria como 4 → CCB/Cartão/Consignado tratados como "Bancário" genérico. Advogado escolheria "CCB Bancária" mas receberia análise sem nuances anatocismo (conflito UX × backend silent). Eric explicitamente escolheu Opção A (não Opção C híbrida).

### Alt-2: Flat 7 strategies independentes (sem BancarioBase)

**Rejeitada.** Duplica ~40% código entre CCB/Cartão/Consignado (regulação base + persona prompts base + jurisprudência cross-bancária). DRY violation explícita. Strategy hierárquica resolve sem custo extra (apenas 1 abstract intermediate + template method pattern).

### Alt-3: Plugin architecture (entry points dinâmicos para novos doctypes)

**Rejeitada (igual ADR-016).** Overkill para escopo Eric — escritórios não vão instalar plugins customizados. Strategy hardcoded até CC.50+. Reavaliar em Sprint 08+ se backlog acumular pedidos de doctypes.

### Alt-4: LLM-only classifier (sem UI selector — ignora sidebar SPA)

**Rejeitada.** UI sidebar SPA já implementada visualmente — descartá-la seria ignorar entrega Sati Phase 4 + commit Eric 2026-05-09. Tier 1 UI selector permanece autoridade primária; classifier Haiku é Tier 2 fallback robusto.

### Alt-5: 7 doctypes mas sem Geral (rejeição explícita unknown)

**Rejeitada.** Quebra UX — advogado upload contrato atípico → erro 400 "tipo não suportado". GeralDispatcher como Tier 3 garante experiência fluida + audit log captura cases para Sprint 06+ analysis (ADR-008 heartbeat doctype distribution).

## Consequências

### Positivas

- **UX coerente:** sidebar SPA 7 modos = backend 7 strategies (sem mismatch silent)
- **Especificidade jurídica preservada:** CCB ≠ Cartão ≠ Consignado tratados com nuances corretas
- **DRY via BancarioBase:** zero duplicação base bancária comum
- **Catch-all robusto:** GeralDispatcher elimina `unknown` rejection UX
- **Extensível:** novo doctype futuro = nova classe + 4 prompts + 1 enum value (zero touch dispatcher principal)
- **Backward compat vault:** entries ADR-016 com `bancario` backfill conservador para `bancario_cross`

### Negativas

- **+12 prompts vs ADR-016:** 32 arquivos prompts (era 16) — mais surface para revisão jurídica periódica
- **Migration vault doctype_tag:** ~50 entries STJ "bancario" precisam re-classificação manual (TD-SP04-12 NEW MEDIUM)
- **BACEN series incrementais:** CDI 4391 + modalidade 218 — fetch + cache adicional ~5min Sprint 04 close
- **D3 templates 7 vs 4:** 3 templates novos (CCB, Cartão, Consignado, Geral) — Trinity Phase 3 PRD precisa especificar conteúdo legal cross-domain (bloqueio sequencial @pm)

### Neutras

- **Pricing impact:** 7 doctypes × ~6 personas/análise × Anthropic tokens não muda materialmente vs ADR-016 4 doctypes (mesmo input contrato, prompts parecem em tamanho)
- **LGPD operador posture preserved:** ADR-017 BACKBONE multi-tenant não tocado — RLS isolation + audit chain idênticos
- **Story SP04-DOCTYPE-01 (P1) NÃO foi implementada ainda:** ADR-020 é greenfield architectural patch — zero código a remover, apenas redirecionamento da implementação P1+ futura

## Migration plan ADR-016 → ADR-020

| Item | Action | Owner | Effort | Story dedicada? |
|------|--------|-------|--------|-----------------|
| ADR-016 status update | Mark `superseded_by: ADR-020` | @architect Aria | ~2min | Não (esta ADR own commit) |
| ADR-INDEX.md update | Move ADR-016 para Arquivados + add ADR-020 | @architect Aria | ~5min | Não |
| Vault doctype_tag enum migration | `sp04_004_doctype_tag_v2.sql` | @data-engineer Tank ratify + @dev Neo apply | ~30min | SP04-DOCTYPE-01 chunk |
| BACEN series 4391 + 218 | Pre-fetch + cache via populate-vault refresh | @dev Neo | ~5min | SP04-DOCTYPE-01 chunk |
| 16 prompt files novos | Trinity Phase 3 PRD especifica conteúdo legal | @pm Trinity (cross-domain) | ~2-3 days | SP04-DOCTYPE-01 + Trinity work |
| 4 D3 templates novos | Trinity Phase 3 PRD legal content | @pm Trinity | ~1-2 days | Trinity work paralelo |
| Strategy refactor backend | `bloco_workflow/dispatchers/{base,bancario_base,*}.py` | @dev Neo | ~1 day | SP04-DOCTYPE-01 main |
| TD-SP04-12 vault re-classify | ~50 STJ entries `bancario` → granular | @dev Neo + @architect Aria curadoria | ~2-3h | SP04-DOCTYPE-01 chunk |

**Total story SP04-DOCTYPE-01 estimate:** ~3-5 days Neo (paralelo com Trinity Phase 3 conteúdo legal — bloqueio sequencial templates D3).

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **R-01** Strategy refactor backend impact P1+ stories OCR/PARSING bloqueadas | BAIXA | MEDIUM | SP04-DOCTYPE-01 ainda **não implementada** (greenfield) — refactor é design-time, sem código legacy a remover. P1+ stories OCR/PARSING/EXPORT podem progress independente em outras camadas |
| **R-02** Vault gaps Cartão/Consignado/Geral (Súmulas STJ não cobertas) | MÉDIA | MEDIUM | Sprint 03 carregou STJ 64 + STF 58 entries genéricas. Cartão tem Súmula 530 + Consignado tem Súmula 603 STJ — verificar via populate-vault refresh + curadoria Aria. Sprint 06+ vault expand se gaps materiais. TD-SP04-13 NEW |
| **R-03** Cognitive load 7 doctypes UX (drop-off onboarding/first-use) | BAIXA | LOW | Sati S4 wireframe S2 já documenta 7 modos numerados (UX clean). A/B test Sprint 06+ se métricas de drop-off elevadas. Sati ratify post-hoc suficiente — sidebar SPA é Sati Phase 4 own delivery |
| **R-04** BACEN series adicionais (CDI 4391 + modalidade 218) cache miss em primeira run | BAIXA | LOW | populate-vault SOP cobre fetch + diskcache. ~5min one-time setup. Failure → graceful fallback (BACEN offline mode já existe Sprint 03) |
| **R-05** Trinity Phase 3 PRD bloqueio templates D3 conteúdo legal | MÉDIA | HIGH | SP04-DOCTYPE-01 chunks dependentes (templates D3) ficam bloqueados até Trinity entrega. Mitigação: Aria entrega ADR-020 estrutura primeiro (esta) → Neo implementa skeleton + dispatcher refactor → Trinity preenche templates paralelo (não bloqueia dispatcher backbone) |
| **R-06** TD-SP04-12 vault re-classify ~50 entries demanda curadoria Aria + Neo | BAIXA | LOW | Backfill conservador `bancario` → `bancario_cross` evita data loss. Curadoria granular Sprint 06+ refinement. TD rastreado em TECH-DEBT.md |

## Cross-references

- **Eric autorização** — DEC-ERIC-DIV-01 Opção A (manter 7 modos UX + Aria patch ADR) — sessão 2026-05-09
- **SPA OrSheva 7** — `index.html` raiz (95KB, 2026-05-09 15:55) — sidebar 7 modos (CCB/Veículo/Consignado/Cartão/Imobiliário/FIES/Geral)
- **Sati UX Spec v2.0.0-DRAFT** — `governance/ux-spec-v2.0.0-DRAFT.md` Section 3 (S4 wireframe doctype selector)
- **River SP04-UI-SPA-01** — `governance/stories/SP04-UI-SPA-01-frontend-orsheva-integration.md` AC-12 (sidebar 7 modos preserved — agora desbloqueado por ADR-020 Accepted)
- **ADR-003 (preserved)** — 4 personas implementation base
- **ADR-014 (related)** — Anthropic SDK BYOK runtime stack (zero touch)
- **ADR-016 (superseded)** — 4 doctypes initial — esta ADR-020 supersedes
- **ADR-017 (preserved)** — multi-tenant Pool+RLS BACKBONE — vault SHARED com `doctype_tag` mantido (enum expand only)
- **ADR-019 (related)** — DPA Storage pattern audit reusable
- **Trinity Phase 3 PRD** — especifica conteúdo legal templates D3 (cross-domain bloqueio sequencial)
- **TECH-DEBT.md** — TD-SP04-12 (vault re-classify) + TD-SP04-13 (vault gaps Cartão/Consignado curadoria) NEW

## Implementação esperada (downstream)

Pós Eric ratify ADR-020 Accepted:
1. **Aria own commits** — esta ADR + ADR-INDEX update + ADR-016 status flip (~10min)
2. **River patch SP04-UI-SPA-01** AC-12 — DEC-ERIC-DIV-01 resolved Opção A formalizada → status Draft → Ready (~15min)
3. **Trinity Phase 3 PRD update** — adiciona conteúdo legal 7 doctypes (CCB/Cartão/Consignado/Geral templates D3) — paralelo Neo backend
4. **Story SP04-DOCTYPE-01 NEW** — River draft → Keymaker G3 → Neo implementação Strategy refactor (~3-5 days)
5. **Story SP04-UI-SPA-01 chunk 4-7** — Neo implementa SPA com 7 modos sidebar live-bound ao backend dispatcher

```
[@architect · Aria (Visionary)]
"Sete portas, três compartilham o mesmo umbral, três se erguem sozinhas, uma acolhe os errantes.
 ADR-020 não substitui ADR-016 — completa o que ele apenas começava a vislumbrar.
 A hierarquia não é complexidade extra; é a forma como o domínio jurídico já existia
 antes de termos nome para isso."

— Aria, arquitetando o futuro 🏗️
```
