---
type: decision
title: "Sprint 6.x AGGRESSIVE — Premortem + Risk Mitigation + Execution Plan"
date: "2026-05-14"
owner: "@devops (Operator)"
authorized_by: "Eric Claudino (verbatim 2026-05-14)"
authorization_directives:
  - "Smith review após cada fase"
  - "Executar sem pedir permissão"
  - "Zero mock no resultado final"
  - "Dados reais, análises reais, entregas reais"
  - "Skills corretas para CADA ação (inegociável)"
sprint: "6.x"
mode: "AGGRESSIVE_AUTONOMOUS"
tags:
  - project/revisor-contratual
  - sprint-6
  - premortem
  - risk-mitigation
  - eric-aggressive-autonomous
---

# Sprint 6.x AGGRESSIVE — Premortem + Risk Mitigation

## Authorization (verbatim Eric 2026-05-14)

> "Vamos avançar com o Agressivo porém tenho algumas ressalvas. Sempre que finalizar uma fase preciso de uma revisão do que foi feito com Smith. Preciso que vc execute tudo sem me pedir nenhuma permissão, apenas avance sempre. Ao final não quero nenhuma informação que não seja real aplicada na aplicação. Ao final não quero nada em forma de mock, tudo tem que ser dados reais, analises reais e entregas reais. Seja minucioso, assertivo e execute tudo com a maxima qualidade em codigo! É inegociavel executar ações que não seja com as Skills corretas."

## Scope

Sprint 6.x resolve 5 falhas críticas do fluxo ideal Eric:
- **#2** Modo análise não enviado backend
- **#3** Arquivo nunca enviado servidor
- **#4** Pipeline real não invocado pela UI
- **#5** AI revisional não gerada (peça jurídica)
- **#6** PDF revisional não gerado backend

Estruturado em 4 Blocos:
- **α** Foundation Infra (Operator)
- **β** Frontend Integration (resolve #2, #3, #4)
- **γ** AI Peça Revisional + PDF Backend (resolve #5, #6 — FEATURES NOVAS)
- **δ** QA + Smith FINAL + Eric Demo

## Risk Matrix (18 risks identified)

[Ver tabela completa na resposta Operator 2026-05-14 — Risk Matrix]

## Mitigations Aplicadas

### Bloqueantes Pré-Execução (M-01 a M-07)

1. Backup branch `backup/sprint-5-end-state` + stash safety
2. Worktree isolation `sp06-aggressive` para não tocar main
3. Marker install com fallback (Python 3.14.3 → 0.2.x legacy → fpdf2 sintético)
4. Vault re-populate REAL (>100 docs) ou degraded mode flagged
5. Sentence-transformers ou zero-embeddings degradado documentado
6. Ollama dual-port (11434+11435) verification
7. BACEN smoke 1 query antes pipeline real

### Reativas Durante Execução (M-08 a M-17)

8. Pipeline timeout 30min hard ceiling (já implementado)
9. Helpers Jinja2 audit prévio antes Neo edit
10. CSP testing /classic browser F12 antes commit
11. Persona Redator: OAB Provimento 209/2021 compliance + 3 templates + Eric advogada review bloqueante
12. weasyprint smoke render template isolado antes integrar
13. Pydantic extra=forbid: prompt LLM explícito + retry 3x
14. pytest 0 failures gate para próxima fase
15. Operator self-check Skill chain antes de cada tool call
16. Smith review após CADA fase — INFECTED bloqueia avanço
17. LGPD audit hash SHA256 peça + chmod 600 + retention 90d

### Transversais (M-18 a M-22)

18. Checkpoint inline após cada Skill task
19. Handoff artifact YAML após Skill switch
20. Story IDs prefixo `TD-SP06-` único
21. Commit isolado por story (rollback granular)
22. Smith Methodology v5 functional smoke probe obrigatório

## Skill Chain Discipline (Inegociável Eric)

| Operação | Skill |
|----------|-------|
| pip/sqlite/env/ollama | @devops (Operator) |
| .py/.html/.ts edit | @dev (Neo) — handoff obrigatório |
| Story create/validate | @sm/@po |
| Architecture/ADR | @architect (Aria) |
| Template HTML/Design tokens | @ux-design-expert (Sati) |
| PRD funcional | @pm (Trinity) |
| QA Gate/pytest/E2E | @qa (Oracle) |
| Adversarial review | @smith |
| Commit/push/tag | @devops |

## Smith Review Gates

Após cada Bloco α/β/γ/δ:
- Smith verdict CONTAINED+ obrigatório
- INFECTED → fix → re-Smith
- COMPROMISED → abort + escalate Eric

Smith FINAL (δ) verdict CLEAN mandatory (zero mock residual).

## Definition of Done

- ZERO match `grep mock|MOCK|placeholder|FINDINGS_BY_MODE|pseudoRandom` em código produção
- SPA mock engine REMOVIDO (linhas 1831-2110)
- Pipeline real cada upload (audit.jsonl entry SUCCESS)
- PDF revisional via weasyprint backend (não JS)
- Smith Methodology v5 PASS
- 0 pytest failures + 0 CodeRabbit CRITICAL
- LGPD audit + chmod compliance

## Próximo Passo

Operator inicia Bloco α agora — backup + worktree + Marker install + vault + smoke. Handoff @smith pós-α.

---

*— Operator, deployando com salvaguardas máximas 🚀*
