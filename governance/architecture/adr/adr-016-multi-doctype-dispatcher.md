---
type: adr
id: "ADR-016"
title: "Multi-Doctype Dispatcher — Strategy Pattern com 4 doctypes"
status: proposed
date: "2026-05-07"
domain: infra
adr_level: design
decision_makers:
  - "@architect (Aria) — design"
  - "Eric Claudino — autorização escopo B (4 doctypes simultâneos)"
supersedes: ""
superseded_by: ""
related_to:
  - "ADR-003 (4 personas implementation — base preserved)"
  - "ADR-014 (Haiku 4.5 para classifier fallback)"
  - "ADR-017 (jurisprudência SHARED com tag por doctype)"
project: revisor-contratual
sprint: "04"
phase: "2.1"
tags:
  - project/revisor-contratual
  - adr
  - sprint-04
  - multi-doctype
  - strategy-pattern
---

# ADR-016: Multi-Doctype Dispatcher

## Contexto

Sprint 03 escopo era exclusivamente CDC Veicular PF (PRD v1.1.2 single doctype). Eric escolheu escopo B na elicitation Phase 1.7: **4 doctypes simultâneos** (FIES + CDC Veicular + Bancário + Imobiliário). Cada doctype tem:
- Jurisprudência específica (STJ Súmulas diferentes)
- Regulação BACEN diferente (modalidades, taxas, prazos)
- Personas de análise com prompts adaptados ao contexto jurídico
- Templates de petição D3 (Apelação Cível) com fundamentos diferentes

Sem dispatcher pattern, código teria 16 if/else combinations (4 personas × 4 doctypes) crescendo cubicamente com novos doctypes.

## Decisão

**Strategy pattern**: `DoctypeDispatcher` abstract class + 4 concrete implementations + persona prompts indexados por doctype. Detecção doctype primária via UI selector pelo advogado, fallback LLM classifier.

Componentes:

1. **Abstract class**:
   ```python
   class DoctypeDispatcher(ABC):
       @abstractmethod
       def get_personas(self) -> list[Persona]: ...
       @abstractmethod
       def get_d3_template(self) -> str: ...
       @abstractmethod
       def get_jurisprudencia_filter(self) -> dict: ...
       @abstractmethod
       def get_bacen_modalidade(self) -> str: ...
   ```

2. **4 concrete dispatchers**: `FIESDispatcher`, `VeicularDispatcher`, `BancarioDispatcher`, `ImobiliarioDispatcher` em `bloco_workflow/dispatchers/`

3. **Detecção doctype** (2-tier):
   - **PRIMARY**: UI selector S2 dropdown obrigatório (advogado escolhe ao fazer upload)
   - **FALLBACK**: LLM classifier Haiku 4.5 ($0,001/análise) — só dispara se advogado pular o selector
   - Classifier prompt: "Classifique este contrato como: FIES, Veicular CDC PF, Bancário (cheque especial/financiamento), Imobiliário, ou outro. Retorne apenas o tipo."

4. **Persona prompts adaptados**: 16 arquivos em `bloco_workflow/personas/prompts/{persona}_{doctype}.txt`
   - Ex: `aria_veicular.txt`, `aria_imobiliario.txt`, `economista_fies.txt`, ...
   - Loading dinâmico via `dispatcher.get_personas()` retorna instâncias com prompt correto

5. **Jurisprudência SHARED**: vault PostgreSQL com `doctype_tag VARCHAR(20)` per documento
   - Valores: `veicular | fies | bancario | imobiliario | cross` (cross = aplicável a múltiplos)
   - Filter via `get_jurisprudencia_filter()` retorna `{tags: [doctype, "cross"]}`

6. **Templates D3**: `bloco_workflow/templates_d3/{doctype}.txt` — Trinity Phase 3 PRD especifica conteúdo legal de cada (Aria define estrutura, não conteúdo jurídico)

## Razão

- **Strategy vs Registry com if/else**: 16 combinations crescem cubicamente; if/else fica unmaintainable em 6+ doctypes futuros. Strategy + composition isola cada doctype em sua classe — novo doctype = nova classe + 4 prompt files, sem tocar dispatcher principal
- **UI selector + LLM fallback (não LLM-only)**: advogado conhece o caso melhor que classifier — UI é signal mais confiável. Mas alguns advogados podem pular o dropdown; Haiku fallback ($0,001) protege sem custo significativo
- **SHARED jurisprudência vs per-doctype vault**: jurisprudência é dado público (não PII). Curadoria centralizada beneficia todos doctypes; algumas Súmulas aplicam a múltiplos (`cross` tag)
- **16 prompt files vs prompt templates parametrizados**: prompts jurídicos são denso e específicos — fundir em template parametrizado perderia nuance. Arquivos separados = revisão jurídica per-doctype possível, sem efeito colateral

## Alternativas Consideradas

### Registry com lookup table

**Rejeitada.** `{doctype: persona_class}` map inicial OK para 4×4=16 entries; mas nuances per-doctype (BACEN modalidade, jurisprudência filter, D3 template) crescem o map para 16×4 atributos. Strategy pattern encapsula coesão.

### LLM classifier sempre obrigatório (sem UI selector)

**Rejeitada.** Adiciona $0,001/análise para todos casos quando advogado já sabe o tipo. UI selector é UX clean + zero custo.

### Fundir 4 personas × 4 doctypes em 1 super-prompt

**Rejeitada.** Prompt único explodiria em ~20k tokens (vs 2k per persona/doctype). Custos cresceriam linearmente sem ganho de qualidade.

### Plugin architecture (entry points dinâmicos)

**Rejeitada.** Overkill para MVP — escritório nunca vai instalar plugins customizados. Strategy + 4 classes hardcoded é suficiente até CC.50+.

## Consequências

### Positivas
- Cada doctype é unidade encapsulada (test isolation, code review focused)
- Extensão clara: novo doctype = classe nova + 4 prompts, dispatcher principal intocado
- Prompt revision per-doctype isolada (advogado especialista pode revisar só FIES sem afetar Veicular)
- LLM fallback dá robustez sem custo significativo

### Negativas
- 16 prompt files = mais arquivos para manter (revisões periódicas necessárias)
- DoctypeDispatcher.get_d3_template() depende Trinity Phase 3 PRD — bloqueio sequencial
- LGPD: classifier Haiku roda em mesmo provider (Anthropic), mas tokens classifier somam ao custo escritório

### Neutras
- 4 doctypes é decisão de escopo Eric (B); se reduzir para 1 doctype no futuro, dispatcher pattern fica overkill mas removível sem refactor massivo
- Cross-tag jurisprudência (Súmula aplicável a múltiplos) requer curadoria — debt menor

## Cross-references

- **Eric autorização escopo B** — 4 doctypes simultâneos (Phase 1.7 elicitation)
- **Atlas v1** — pricing Haiku 4.5 para classifier
- **ADR-003 (preserved)** — 4 personas implementation base — Strategy pattern envolve, não substitui
- **ADR-014 (related)** — usa mesmo Anthropic SDK
- **ADR-017 (related)** — jurisprudência SHARED com `doctype_tag` em PostgreSQL multi-tenant
- **Trinity Phase 3 PRD** — especifica conteúdo legal templates D3 (cross-domain)
