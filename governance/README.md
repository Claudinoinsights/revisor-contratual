# Governance — Revisor Contratual

Esta pasta contém os artefatos de governança e auditabilidade do MVP v0.1.0.

## Conteúdo

| Pasta/Arquivo | Conteúdo |
|---|---|
| `prd/` | Product Requirements Document (canônico: `prd-v1.0.2.md`) |
| `architecture/` | ADRs (Architecture Decision Records) + ADR Index |
| `qa/` | 16 QA gates + Morpheus consolidações |
| `decisions/` | Decisões pontuais (overflow de QA) |
| `research/` | Pesquisa pré-MVP (Phase 0) |
| `stories/` | Stories de desenvolvimento (vazio — closure) |
| `PROJECT-CHECKPOINT.md` | Índice de status executivo |
| `CHECKPOINT-active.md` | Histórico ativo Phase 1+ (sessões 24-83) |
| `CHECKPOINT-history-phase-0.md` | Histórico Phase 0 (sessões 1-23) |
| `TECH-DEBT.md` | Tech debt registry (13 active + 1 finding + 5 RESOLVED) |
| `orsheva-brandbook.html` | Brandbook visual (referência para frontend futuro) |

## Sobre referências a framework externo

Vários documentos históricos (ADRs, QA gates, Morpheus consolidações) referenciam paths como `.claude/rules/...` e `.lmas-core/...`. Esses paths **não existem** neste repositório — são referências históricas ao framework **LMAS** (`Claudinoinsights/the-matrix`) sob o qual o MVP foi desenvolvido durante o Sprint 01.

**Os documentos foram preservados intactos** como registro histórico/auditoria. As referências externas podem ser ignoradas em leitura — o conteúdo substantivo (decisões arquiteturais, gates de qualidade, retrospective) é independente do framework.

## Origem

Sprint 01 (15 stories Done | 15/15 PASS Oracle) executado entre 2026-04-30 e 2026-05-05 sob orquestração LMAS no monorepo `Claudinoinsights/the-matrix`. Extraído para repositório dedicado em 2026-05-05 como parte da independência do projeto.

Tag/Release histórica original: `v0.1.0-revisor-contratual` em `Claudinoinsights/the-matrix` (preservada).
