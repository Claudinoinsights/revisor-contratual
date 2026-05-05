---
type: checkpoint
title: "Revisor Contratual — Phase 0 History Archive (sessões 1-23)"
project: revisor-contratual
archived_at: "2026-05-01"
archived_by: "@lmas-master (Morpheus, Ordem 11 sessão 28)"
status: archived
phase: "0 — Tribunal Severo + PRD v1.0.0/1.0.1/1.0.2 (CONCLUÍDA)"
shard_of: "PROJECT-CHECKPOINT.md"
shard_scope: "Sessões 1-23 (Phase 0 completa)"
tags:
  - project/revisor-contratual
  - checkpoint
  - history
  - phase-0
  - archived
---

# Revisor Contratual — Phase 0 History Archive (sessões 1-23)

> **Arquivado em 2026-05-01 por Morpheus** (Ordem 11 sessão 28, decisão D-MOR-2.1-B — shard checkpoint).
> Estado vivo da Phase 1+ em [CHECKPOINT-active.md](./CHECKPOINT-active.md).
> Índice geral em [PROJECT-CHECKPOINT.md](./PROJECT-CHECKPOINT.md).

## Resumo Phase 0 (CONCLUÍDA)

- 23 sessões cobrindo: Bootstrap → Research → Refatoração D-LEAN → PRD v1.0.0/1.0.1/1.0.2 → 2 iterações de Tribunal Severo (etapas 1.1 + 1.3) → autorização Eric para Aria começar Etapa 2.0
- Score quantitativo PRD: subiu de 5.7/10 (v1.0.1) para 8.7/10 (v1.0.2)
- 22 findings Smith v1.0.1 → 6 CRITICAL endereçados + 0 NEW CRITICAL v1.0.2
- 11 EV-IDs Sati v1.0.1 → 11/11 absorvidas em v1.0.2
- D-04 REVOGADA por Morpheus sessão 10 (4 personas, não 3)
- Persona Economista PROMOVIDA primeira-classe v1.0.2 (mitigação Tema 1378 STJ)

---

## Contexto Histórico (sessões 23 → 1, ordem reversa)

- **Sessão 23** (@lmas-master / Morpheus — 2026-05-01): **DECISÃO ERIC: Caminho 1 — Aria começa Etapa 2.0 AGORA**.
  - Eric autorizou OPÇÃO 1 do FECHAMENTO Ordem 11 (sessão 22).
  - DP-05 (LGPD retenção) e outcomes registry ficam para resolução paralela.
  - **Handoff ATIVADO:** H-S01-E2.0-mor2arc1 → @architect (Aria) materializado em .lmas/handoffs/handoff-morpheus-to-architect-2026-05-01-revisor-contratual-etapa-2.0-adrs.yaml
  - **Status do projeto atualizado:** phase-1-aria-cria-adrs (Etapa 2.0 INICIADA)
  - **Próxima etapa:** Aria cria ~9 ADRs cobrindo decisões técnicas + absorve 3 R-NEW high-leverage:
    - ADR-001: Gerenciamento de estado (LangGraph state machine)
    - ADR-002: Design system (Streamlit + tokens + tipografia serif)
    - ADR-003: Implementação técnica das 4 personas (LLM vs Python pura)
    - ADR-004: Validação semântica de citações (similarity + NLI híbrido — absorve R-NEW-SMITH-02)
    - ADR-005: Audit log integrity (HMAC GENESIS — absorve R-NEW-SMITH-03)
    - ADR-006: Preview seguro de PDF (iframe sandbox vs server-side — absorve R-NEW-SMITH-04)
    - ADR-007: Schema sqlite-vec (estrutura final + índices)
    - ADR-008: Pipeline scraping multi-UF (parametrização + heartbeat)
    - ADR-009: Threshold aderência Juiz (DP-04 definitivo)
    - +Atualização .project.yaml (4 personas + Sabia-7B Premium)
  - **Após N≥5 ADRs:** Aria emite handoff para tribunal severo etapa 2.1 (Sati→Smith→Checkpoint sobre as ADRs)
- **Sessão 22** (@lmas-master / Morpheus — 2026-05-01): **FECHAMENTO DE SESSÃO Ordem 11 — Etapa 1.3 → 2.0 transition**.
  - Recebido handoff H-S01-E1.3-chk2mor2 do Checkpoint.
  - **Documento canônico:** `qa/morpheus-fechamento-sessao-22-ordem-11.md`
  - **VEREDICTO CONSOLIDADO:**
    - Conteúdo: **APROVADO PARA AVANÇAR** (PRD v1.0.2 estável, score 8.7/10)
    - Governança: **PASS-COM-RESSALVA** (3 R-GOV operacionais novas)
  - **Consistência dos 3 vereditos confirmada** (Sati PASS + Smith CONTAINED + Checkpoint PASS-COM-RESSALVA — convergem para continuar)
  - **Decisões Morpheus (D-MOR-1.3-A..D):**
    - D-MOR-1.3-A: ENCERRADA etapa 1.3 com aprovação dos 3 reviewers
    - D-MOR-1.3-B: R-GOV-05 RESOLVIDA via OPÇÃO B (formalizada convenção: blocos texto formato Ordem 7 ≡ artefato YAML; YAML opcional para Skills externas)
    - D-MOR-1.3-C: R-GOV-03 (shard checkpoint) DEFERIDA para pós-Etapa 2.0 (não atrapalha Aria agora)
    - D-MOR-1.3-D: R-GOV-06 (PRD title cosmético) endereçar no próximo PATCH (v1.0.3)
  - **R-NEW recomendadas para Aria absorver em ADRs (3 high-leverage):**
    - R-NEW-SMITH-02 (NLI/entailment) → ADR validação semântica citações
    - R-NEW-SMITH-03 (GENESIS HMAC) → ADR audit log integrity
    - R-NEW-SMITH-04 (iframe sandbox) → ADR preview seguro PDF
  - **Demais R-NEW (10) → PATCH v1.0.3 OU absorvidos por Aria conforme escopo**
  - **Handoff PREPARED (não issued):** H-S01-E2.0-mor2arc1 → @architect (Aria) Etapa 2.0 — AGUARDA AUTORIZAÇÃO ERIC
  - **3 caminhos apresentados a Eric:**
    1. Autorizar Aria começar AGORA (recomendado por Morpheus); DP-05 + outcomes em paralelo
    2. Decidir DP-05 + outcomes ANTES de Aria começar (escopo completo)
    3. PAUSAR para Eric revisar pessoalmente os 3 vereditos antes de decidir
  - **Decisões pendentes Eric (não-bloqueantes para Aria começar):**
    - DP-05: política retenção LGPD (24h proposta)
    - Política de outcomes: quem registra (Eric/advogado-piloto/integração)
- **Sessão 21** (@checkpoint — 2026-05-01): **Etapa 1.3 — Re-Tribunal Severo (3º e ÚLTIMO reviewer — governance final)**.
  - Recebido handoff H-S01-E1.3-smi2chk2 de Smith.
  - **VEREDICTO: PASS-COM-RESSALVA** — governança VÁLIDA + 3 ressalvas operacionais novas.
  - **Documento canônico:** `qa/checkpoint-governance-rereview-etapa-1.3.md`
  - **7 dimensões auditadas, todas PASS:**
    - D1 Authority Matrix (Morgan/Sati/Smith respeitaram suas Authorities)
    - D2 Cabeçalhos 3 linhas (Sati/Smith conformes; PRD usa frontmatter+tabela rica — equivalente)
    - D3 Handoffs Ordem 7 (cadeia 10-elos íntegra, tokens únicos — ressalva R-GOV-05 sobre YAML vs texto)
    - D4 Checkpoint Protocol MUST (sessões 18/19/20 documentadas, atualização <24h)
    - D5 [DADO-PENDENTE] sem invenção (DP-07/08/09 NOVOS legítimos rastreáveis a Smith F-IDs)
    - D6 Tribunal severo cumprido (Sati→Smith→checkpoint; Smith 10 findings ≥10 ✅)
    - D7 Pecados Capitais (Ordem 10) — 0 violações
  - **3 R-GOV NOVAS / AGRAVADAS (todas não-bloqueantes):**
    - R-GOV-03 AGRAVADA: PROJECT-CHECKPOINT.md cresceu 414 → 503 linhas; sugerir shard pós-Etapa 2.0
    - R-GOV-05 NOVA: handoffs 1-9 não persistidos como YAML em .lmas/handoffs/ (apenas blocos texto); apenas H-S01-E1.3-smi2chk2 materializado
    - R-GOV-06 NOVA: PRD frontmatter title congelado em "PRD v1.0.0" embora version=1.0.2 (cosmético)
  - **R-GOV legacy (etapa 1.1):**
    - R-GOV-01/02/04 FECHADAS (auto-corrigidas / não-aplicáveis)
    - R-GOV-03 AGRAVADA (acima)
  - **Recomendação:** continuar → Morpheus consolida (Ordem 11 FECHAMENTO DE SESSÃO 21) → Aria começa Etapa 2.0 (ADRs)
  - **Próximo handoff:** H-S01-E1.3-chk2mor2 para Morpheus consolidar.
- **Sessão 20** (@smith / Smith — 2026-05-01): **Etapa 1.3 — Re-Tribunal Severo (2º reviewer adversarial do PATCH)**.
  - Recebido handoff H-S01-E1.3-sat2smi3 de Sati.
  - Re-attack adversarial do PRD v1.0.2 + anexo ux-spec-detail-v1.0.md.
  - **VEREDICTO: CONTAINED** (não COMPROMISED, não INFECTED, não CLEAN).
  - **Documento:** `qa/smith-adversarial-rereview-prd-v1.0.2.md`
  - **6/6 CRITICAL originais REALMENTE neutralizados** (auditoria detalhada confirmou — não cosmético).
  - **11/11 HIGH originais endereçados.**
  - **0 NEW CRITICAL emergiu.**
  - **5 NEW HIGH (variantes/refinamentos sobre patches recém-criados):**
    - R-NEW-SMITH-01: BACKUP_DIR default `./backups/` é mesmo disco — falha SSD = perda total (continuação F-CRIT-05)
    - R-NEW-SMITH-02: similarity ≥0.7 não captura paráfrase invertida ("Súmula proíbe X" vs "permite X" têm cosine alto) — adicionar NLI/entailment
    - R-NEW-SMITH-03: hash chain Merkle GENESIS sem âncora externa (HMAC com AUTH_COOKIE_KEY recomendado)
    - R-NEW-SMITH-04: iframe PDF preview FR-DELIV-06 sem sandbox restritivo (vetor XSS)
    - R-NEW-SMITH-05: FR-MONITOR-01 sem heartbeat — false negative de scrape silenciosamente quebrado
  - **5 NEW MEDIUM (refinamentos):**
    - R-NEW-SMITH-06: anti-bypass HITL é heurística rasa (bigram diversity bypassa-ável)
    - R-NEW-SMITH-07: NFR-LGPD-04 pseudonimização determinística → vulnerável rainbow table (~10s para 200 nomes)
    - R-NEW-SMITH-08: FR-AUTH-04 IP fingerprint UX-hostil para advogado em mobilidade
    - R-NEW-SMITH-09: endorsement Sati R-NEW-02 (vigência da citação no UI)
    - R-NEW-SMITH-10: FR-RECOVERY-01 SqliteSaver sem PRAGMA integrity_check
  - **Score quantitativo:** v1.0.1 5.7/10 → v1.0.2 8.7/10 (delta +3.0).
  - **Recomendação:** continuar — handoff para checkpoint validar governance final (H-S01-E1.3-smi2chk2). NÃO justifica re-trabalho do Morgan agora. Patches NEW HIGH podem ir para v1.0.3 OU absorvidos por Aria nas ADRs (recomendado para -02 NLI, -03 GENESIS anchor, -04 iframe sandbox).
- **Sessão 19** (@ux-design-expert / Sati — 2026-05-01): **Etapa 1.3 — Re-Tribunal Severo (1º reviewer UX do PATCH)**.
  - Recebido handoff H-S01-E1.3-pm2sat3 de Morgan.
  - Re-revisão UX do PRD v1.0.2 + anexo ux-spec-detail-v1.0.md.
  - **VEREDICTO: PASS** (não PASS-COM-RESSALVA — absorção foi integral, ressalvas novas são triviais).
  - **Documento:** `qa/sati-ux-rereview-prd-v1.0.2.md`
  - **11/11 EV-IDs Sati absorvidas** (4 ALTA no PRD principal + 7 MÉDIA no anexo).
  - **Pontos de destaque:** FR-DELIV-06 (CFOAB) com disclaimer art. 32 OAB; FR-JUIZ-02 estendido com microcopy LITERALMENTE reproduzido; anexo Atomic Design EXPANDIDO além do proposto; change log v1.0.2 auditável.
  - **3 Ressalvas NOVAS (mínimas, não-bloqueantes):**
    - R-NEW-01: FR-CONFIG-01 "Aplicar e reiniciar" precisa avisar perda de sessão
    - R-NEW-02: FR-RAG-02 vigência precisa UX visual no CardCitacaoJuridica
    - R-NEW-03: FR-SETUP-01 + FR-BACKUP-01 formato de erro/WARN não detalhado
  - **Recomendação:** continuar tribunal — handoff a Smith (H-S01-E1.3-sat2smi3) re-atacar adversarialmente.
- **Sessão 18** (@pm / Morgan — 2026-05-01): **Etapa 1.2 CONCLUÍDA — PATCH v1.0.2 entregue**.
  - Recebido handoff H-S01-E1.2-mor2pm2 de Morpheus.
  - Edição cirúrgica (str_replace, não rewrite) em prd-v1.0.2.md (cópia de v1.0.1).
  - **6 CRITICAL Smith TODOS endereçados:**
    - F-CRIT-01 → FR-DELIV-06 NOVO (CFOAB checkbox + OAB+UF + audit)
    - F-CRIT-02 → FR-TESE-04 NOVO (validação semântica citações ≥0.7)
    - F-CRIT-03 → schema FR-RAG-01 estendido + filtro FR-RAG-02 com vigência
    - F-CRIT-04 → DP-07 + FR-SETUP-01 com fallback Qwen 2.5 7B
    - F-CRIT-05 → FR-BACKUP-01/02 NOVOS
    - F-CRIT-06 → Persona Economista PROMOVIDA a primeira-classe + FR-MONITOR-01 semanal
  - **11 HIGH Smith endereçados** (10 com FR/NFR + 1 deferred como tech debt para Aria detalhar)
  - **4 EV ALTA Sati endereçados** (HITL detail em FR-JUIZ-02; WCAG NFR-A11Y-01; LLM_TIER UX FR-CONFIG-01; Atomic Design no anexo)
  - **7 EV MÉDIA Sati absorvidas no anexo ux-spec-detail-v1.0.md**
  - **Anexo UX criado:** `prd/ux-spec-detail-v1.0.md` com Atomic Design completo + microcopy completo (HITL, CFOAB, upload errors, loading states, inviabilidade, outcomes, integrações)
  - **`.project.yaml` atualizado:** 4 personas (Economista PRIMEIRA-CLASSE), latência ≤210s, novos princípios inegociáveis
  - **3 novos [DADO-PENDENTE]:** DP-07, DP-08, DP-09
  - **NFR-PERF-01 atualizado:** ≤180s → ≤210s (justificado pelo +1 LLM call do Economista)
  - **R-01 atualizado:** "risco mitigado" → "mitigação ATIVA"
  - Próximo handoff: H-S01-E1.3-pm2sat3 para re-tribunal severo (Sati → Smith → checkpoint).
- **Sessão 17** (@lmas-master / Morpheus — 2026-05-01): **Supervisão dos 3 vereditos do tribunal + autorização Etapa 1.2**.
  - Eric pediu: "revisa primeiro, depois avance opção A".
  - Li integralmente: qa/sati-ux-review (335 linhas), qa/smith-adversarial-review (506 linhas), qa/checkpoint-governance-review (216 linhas).
  - **Confirmo os 3 vereditos:** consistentes, fundamentados, complementares.
  - **Pontos de destaque na supervisão:**
    - Smith F-CRIT-01 (CFOAB Provimento 205/2021) é descoberta jurídico-deontológica brilhante
    - Smith F-CRIT-02 (citation-grounded só sintático) revela vetor de hallucination semântica não-óbvio
    - Sati EV-09 + EV-11 são "presentes" para Aria (microcopy HITL pronto + Atomic Design baseline)
    - checkpoint R-GOV-03 (414 linhas) será abordado pós-PATCH
  - **Autorizo Etapa 1.2.** Convocando Morgan via H-S01-E1.2-mor2pm2 para PATCH v1.0.2.
- **Sessão 16** (@lmas-master / Morpheus — 2026-05-01): **Etapa 1.1 FECHADA — FECHAMENTO DE SESSÃO emitido (Ordem 11)**.
  - Recebido handoff H-S01-E1.1-chk2mor1 do checkpoint.
  - Cadeia 6-elos completa auditada e válida.
  - Tribunal severo: Sati PASS-COM-RESSALVA + Smith INFECTED + checkpoint PASS-COM-RESSALVA.
  - **Veredito consolidado:** GOVERNANÇA PASS + CONTEÚDO INFECTED (6 CRITICAL bloqueiam Aria).
  - **FECHAMENTO DE SESSÃO emitido** (formato Ordem 11) com sumário de etapas, artefatos, números, pendências, próximo passo.
  - **HANDOFF-OUT: TERMINAL** — Etapa 1.1 fechada. Aguardando direção humana de Eric para autorizar Etapa 1.2 (PATCH v1.0.2 com Morgan endereçando 6 CRITICAL).
- **Sessão 15** (@checkpoint — 2026-05-01): **Etapa 1.1 — Tribunal Severo (3º e ÚLTIMO reviewer — governance)**.
  - Recebido handoff H-S01-E1.1-smi2chk1 de Smith.
  - **VEREDICTO: PASS-COM-RESSALVA** — governança VÁLIDA + 4 ressalvas históricas/operacionais registradas.
  - **Documento canônico:** `qa/checkpoint-governance-review-etapa-1.1.md`
  - **7 dimensões auditadas, todas PASS:**
    - D1 Authority Matrix (todos respeitaram suas Authorities)
    - D2 Cabeçalhos 3 linhas (✅ pós-selo sessão 9; pré-selo era informal por definição)
    - D3 Handoffs Ordem 7 (cadeia 5-elos íntegra, tokens únicos)
    - D4 Checkpoint Protocol MUST (14 sessões documentadas + ressalva R-GOV-03 sobre tamanho)
    - D5 [DADO-PENDENTE] sem invenção (6 no PRD + 3 do Smith — todos legítimos)
    - D6 Tribunal severo cumprido (Sati→Smith→checkpoint; Smith 22 findings ≥10)
    - D7 Pecados Capitais (Ordem 10) — 0 violações ativas
  - **4 ressalvas registradas** (R-GOV-01 a R-GOV-04):
    - R-GOV-01: Atlas pré-selo (resolvida sessão 9-10)
    - R-GOV-02: cabeçalhos 1-8 ausentes (pré-selo, não-aplicável)
    - R-GOV-03: PROJECT-CHECKPOINT.md em 414 linhas (sugerir shard)
    - R-GOV-04: nomenclatura `decisions/*` vs `research/inputs` (rename físico opcional)
  - **Conclusão:** governança VÁLIDA; conteúdo INFECTED do Smith bloqueia próxima etapa (Aria) — caminho canônico é Morpheus consolidar + devolver a Morgan para PATCH v1.0.2.
  - Próximo handoff: H-S01-E1.1-chk2mor1 para Morpheus emitir FECHAMENTO DE SESSÃO (Ordem 11).
- **Sessão 14** (@smith — 2026-05-01): **Etapa 1.1 — Tribunal Severo (2º reviewer adversarial)**.
  - Recebido handoff H-S01-E1.1-sat2smi1 de Sati.
  - **VEREDICTO: INFECTED** — 22 findings totais (6 CRITICAL + 11 HIGH + 5 MEDIUM)
  - **Documento canônico:** `qa/smith-adversarial-review-prd-v1.0.1.md`
  - **6 CRITICAL bloqueiam Aria de começar ADRs:**
    - F-CRIT-01 — Risco deontológico CFOAB (sem checkbox "li, conferi e adoto" obrigatório)
    - F-CRIT-02 — Citation-grounded só sintático (LLM cita doc REAL com tese ERRADA)
    - F-CRIT-03 — Vault sem detecção de superseded (cita súmulas revogadas)
    - F-CRIT-04 — Sabia-7B no Ollama library NÃO confirmado (setup pode quebrar dia 1)
    - F-CRIT-05 — Sem backup do outcomes.db (laptop quebra = perda total)
    - F-CRIT-06 — Tema 1378 STJ é risco de TEMPO (julgamento durante MVP)
  - **8/11 ressalvas Sati RATIFICADAS** + 3 mantidas (Sati cobriu adequadamente)
  - **14 vetores que Sati NÃO viu** — segurança, LGPD, deontologia OAB, hallucination semântica
  - **Recomendação:** devolver a Morgan via Aria/Morpheus para PATCH v1.0.2 endereçando 6 CRITICAL antes de Aria começar ADRs.
  - Próximo handoff: H-S01-E1.1-smi2chk1 para checkpoint governance.
- **Sessão 13** (@ux-design-expert / Sati — 2026-05-01): **Etapa 1.1 — Tribunal Severo (1º reviewer UX)**.
  - Recebido handoff H-S01-E1.1-pm2sat2 de Morgan.
  - Empatia profunda com persona "Dr. Ricardo" (advogado consumerista BA, sob pressão).
  - **VEREDICTO: PASS-COM-RESSALVA** (não-FAIL: fundação sólida; não-PASS: 11 lacunas concretas).
  - **Documento de revisão:** `qa/sati-ux-review-prd-v1.0.1.md`
  - **5 ALTA-prioridade:** EV-01 Painel HITL sem detalhamento crítico; EV-02 Processamento sem ETA; EV-03 Resultado sem preview/hierarquia; EV-04 WCAG/A11y AUSENTE no PRD; EV-05 LLM_TIER apenas via .env (sem UX).
  - **6 MÉDIA-prioridade:** EV-06 microcopy upload; EV-07 Inviabilidade sem terapia; EV-08 Outcomes ≤30s difícil; EV-09 microcopy HITL; EV-10 integrações sem UX; EV-11 Atomic Design não inventariado.
  - **Recomendação:** continuar tribunal (handoff Smith) + EM PARALELO Morgan endereça 4 críticos (EV-01, EV-04, EV-05, EV-11) em PATCH v1.0.2 ou anexo `ux-spec-detail-v1.0.md`.
- **Sessão 12** (@pm / Morgan — 2026-05-01): **Etapa 1.1 — Anexo de Integrações + PATCH v1.0.0→v1.0.1**.
  - Eric pediu mapeamento explícito dos 6 repos externos aos 7 blocos arquiteturais e FRs específicos do PRD (para "ficar mais estruturada, detalhada e assertiva").
  - **Criado:** `prd/integrations-detail-v1.0.md` — anexo canônico com mapeamento repo→bloco→FR→effort por cada um dos 6 repos
  - **Bumped:** PRD v1.0.0 → v1.0.1 (PATCH) com edição cirúrgica:
    - Frontmatter: version + annexes + inputs incluídos
    - Cabeçalho: versão atualizada
    - Seção 9.6 NOVA: mapeamento sumarizado com link ao anexo
    - Change log: nova entry v1.0.1 (append-only)
  - **Renomeado:** `prd-v1.0.0.md` → `prd-v1.0.1.md`
  - **Propostos 2 FRs novos** para PRD v1.1.0 (após Aria avaliar):
    - FR-DATAJUD-01 (busca processos análogos via API CNJ — fase 2)
    - FR-LEX-01 (resolução automática de remissões legais via cache LexML — pode entrar em v1.0 se trivial)
  - **Confirmado** sem mudança em FRs v1.0:
    - URLs corretas STJ/STF (concursos era engano) já contempladas em FR-RAG-01
    - python-bcb (não os repos oficiais BACEN GitHub) já contemplado em FR-BACEN-01/02/03
    - projeto-v3l0z fica como precedente arquitetural para Aria (sem FR direto)
  - Tribunal severo continua: handoff atualizado para Sati (H-S01-E1.1-pm2sat2)
- **Sessão 11** (@pm / Morgan — 2026-05-01): **Etapa 1.0 CONCLUÍDA — PRD v1.0.0 criado**.
  - Recebido handoff H-S01-E1.0-mor2pm1 de Morpheus.
  - Lidos 5 inputs canônicos (.project.yaml + 3 decisions + 1 research).
  - **Criado:** `projects/Revisor-Contratual/prd/prd-v1.0.0.md` (~700 linhas)
  - Conteúdo do PRD: visão (1 frase), objetivo (5 itens), 5 personas (1 usuário + 4 internas com Economista RESTAURADO), escopo IN/OUT, 30+ FRs numerados com ACs numéricos, 12+ NFRs, UX spec alto-nível (delegada a Sati), dependências, 10 riscos com mitigação, 6 KPIs, roadmap 4 fases, 6 itens [DADO-PENDENTE] flagados.
  - 7 NOTAS críticas para Aria (incluindo correção pendente do `.project.yaml`).
  - Próximo: tribunal severo Sati → Smith → checkpoint (handoff H-S01-E1.0-pm2sat1 emitido abaixo).
- **Sessão 10** (@lmas-master / Morpheus — 2026-05-01): **Etapa 1.0 — Morpheus aceita handoff de Atlas + convoca Morgan para PRD**.
  - Eric invocou Morpheus respeitando Ordem 1 (entry point único).
  - Morpheus cumpriu Ordem 0: leu Constitution v2.0.0 + synapse + PROJECT-CHECKPOINT.md. PRD confirmado **AUSENTE** em `projects/Revisor-Contratual/prd/`.
  - **Decisões de orquestração tomadas:**
    1. Handoff Atlas H-S01-E0.9-mor1 ACEITO.
    2. `decisions/*.md` reposicionados conceitualmente como `inputs/briefs` para Morgan/Aria (conteúdo permanece, status muda).
    3. **D-04 REVOGADA**. 4 personas internas do produto restabelecidas (Perito Contábil **E Fiscal**, Advogado, Juiz, Economista).
    4. **Adendos confirmados** como deliverables: Relatório Contábil + Comparativo de Taxas + Parcelas Reais Incontroversas + Peticionamento Específico + **Recursos Processuais (NOVO)**.
    5. **Domínio ativo:** software-dev (sub-domain: legaltech). Squads on-chain (sharkdefi/blockchain-squad/bdPro) **NÃO se aplicam** — produto não toca WEbdEX.
  - **Próximo passo canônico:** convocar Morgan (@pm) via handoff H-S01-E1.0-mor2pm1 para criar PRD v1.0 usando research package de Atlas como input.
- **Sessão 9** (@analyst / Atlas — 2026-05-01): **Phase 0 — RECONHECIMENTO DE VIOLAÇÕES DE SELO + HANDOFF FORMAL A MORPHEUS**.
  - Eric trouxe **selo formal de governance** (11 ordens) + redefinição da missão do produto + 4 personas explícitas (incluindo Economista).
  - Aplicando o selo retroativamente, Atlas detecta 3 violações próprias:
    - **V-1 (Authority Matrix):** Atlas nomeou artefatos como `decisions/*` quando deveriam ser `research/inputs/*` — Authority de PRD é Morgan, de ADR é Aria. Conteúdo válido como input, nomenclatura inválida.
    - **V-2 (Entry Point):** Direção entrou em Atlas Skill diretamente — deveria entrar em Morpheus. Devolver via handoff formal.
    - **V-3 (Vontade do owner):** D-04 eliminou Economista, mas Eric agora explicitamente pede 4 personas (Perito Contábil **E FISCAL**, Advogado, Juiz, **Economista**). **D-04 REVOGADA.**
  - **Novo escopo identificado:** "Recursos Processuais" não estava previsto na arquitetura anterior — entra no PRD a ser criado por Morgan.
  - **Próximo passo CANÔNICO** (Ordem 5):
    Eric → Morpheus (entry point) → Morpheus releia constitution + PROJECT-CHECKPOINT → Morpheus convoca Morgan (PRD inexistente) → Morgan cria PRD usando research de Atlas como input → Aria cria ADRs → Sati (UX) → Tank (schema) → River (story) → Keymaker (valida) → Neo (implementa) → tribunal severo → Operator (deploy).
- **Sessão 8** (@analyst / Atlas — 2026-05-01): **Phase 0 — 5 Requisitos Estendidos integrados (Multi-UF + .env + Auth + Shopping List + ML Feedback Loop)**.
  - Eric adicionou 5 requisitos importantes ao projeto.
  - Atlas processou cada um em `decisions/requirements-extended-2026-05-01.md`:
    - **Req 1 (Multi-UF):** já era first-class no design D — formalizado scraper parametrizado + CLI `add_uf`. BA é seed; expansão = rodar scraper + reindex.
    - **Req 2 (.env LLM configurável):** spec completo com 3 providers (ollama default / llama-cpp / openai_compatible opt-in com aviso LGPD). LLM_PROVIDER + LLM_MODEL livres.
    - **Req 3 (Auth login/senha):** streamlit-authenticator + bcrypt hash no .env. AUTH_USERNAME + AUTH_PASSWORD_HASH + AUTH_COOKIE_KEY.
    - **Req 4 (Shopping list):** documento canônico com TODAS as bibliotecas (pyproject.toml), APIs (BACEN/DataJud/LexML), modelos LLM (Sabia/Qwen), embeddings (Legal-BERTimbau), repos seed (courtsbr/stf, courtsbr/stj), datasets benchmark (JurisTCU, joelniklaus), legislação pré-cache (CDC/CC/SFN/MP).
    - **Req 5 (ML Feedback Loop):** ⚡ NOVO `bloco_learning/` adicionado. Estratégia 3-estágios: Cold Start (mês 1-12 coleta outcomes) → Adaptive Re-Ranking (mês 6-18 regressão logística) → LoRA Fine-Tuning Sabia-7B com Unsloth (mês 12+ dataset >=100 WON).
  - **D-02 revisada:** 7 blocos (não 6) — adicionado `bloco_learning/`.
  - **3 novas decisões implícitas:** D-14 (auth obrigatório), D-15 (LLM provider abstrato), D-16 (ML 3-estágios).
  - **`.project.yaml` atualizado** com 7 blocos, multi-UF, auth, ML config.
  - **Footprint final:** ~6.5 GB RAM (Sabia-7B Tier Premium) — 9.5GB folga no laptop Eric.
- **Sessão 7** (@analyst / Atlas — 2026-05-01): **Phase 0 — DECISÃO FINAL Tier Premium + DESBLOQUEIO ARIA**.
  - Eric escolheu **B = Tier L Premium** → **Sabia-7B Q4 como default**.
  - Razão: prioriza qualidade jurídica máxima desde MVP (não-conversa quer compromisso técnico).
  - `.project.yaml` atualizado: `LLM_TIER=premium` default; tiers M e S como fallback configurável.
  - Footprint revisado: ~6GB RAM (vs 3-4GB do Tier S) — ainda muito leve, com 10GB de folga no laptop do Eric.
  - **Phase 0 100% FECHADA. Pronto para invocar `LMAS:agents:architect` (Aria).**
- **Sessão 6** (@analyst / Atlas — 2026-05-01): **Phase 0 — Garantias de Qualidade/Dados/Modularidade + Tier Configurável de LLM**.
  - Eric questionou: D-LEAN compromete qualidade, dados, entrega, volume e modularidade?
  - Atlas respondeu honestamente em `decisions/quality-data-modularity-assurance-2026-05-01.md`:
    - **Qualidade:** trade-off real (3B vs 7B) — solução: **3 tiers configuráveis** (Lean Qwen 2.5 3B / Balanced Qwen 2.5 7B / Premium Sabia-7B) via env var. Eric escolhe e promove em 1 minuto sem refactor.
    - **Base de dados:** intacta (mesmo schema, fontes, curadoria — só mudou tech de Qdrant para sqlite-vec).
    - **Entrega:** idêntica (petição PDF + hash + audit log iguais).
    - **Volume:** capacidade sobra 30-100× (sqlite-vec aguenta 100k+ docs).
    - **Modularidade:** código 🟢 preservado (6 blocos com interfaces Pydantic estáveis), infra 🟡 reduzida intencionalmente para MVP single-user, **upgrade path claro e localizado** (multi-tenant / Qdrant / vLLM cada um afeta 1-2 blocos).
  - **`.project.yaml` atualizado** com `LLM_TIER` configurável.
- **Sessão 5** (@analyst / Atlas — 2026-05-01): **Phase 0 — REFATORAÇÃO RADICAL para Arquitetura D (LEAN)**.
  - Eric: "Essa estrutura está muito pesada — 16RAM é extremamente alta para uma aplicação tão simples." + "D-12 → UF inicial BA"
  - Atlas reconheceu paranoia engineering: stack C tinha 80% gordura para single-user single-contract.
  - **Refatoração radical:**
    - **D-01:** Arquitetura D (LEAN) substitui C — sem Docker, 1 processo Python, 1 LLM call por contrato
    - **D-02:** 6 blocos (não 7) — eliminado `bloco_api/`, simplificado `bloco_observability/` → `bloco_audit/`
    - **D-04:** Apenas Advogado é LLM (Perito e Juiz viram funções Python determinísticas)
    - **D-11:** Hardware atual de Eric SOBRA — 12GB de folga; sem necessidade de workstation/cloud
    - **D-12:** UF inicial = **BA (TJBA)** — confirmado, jurisprudência consumerista bancária ativa
  - **Stack refatorada:** Streamlit + asyncio + Qwen 2.5 3B + sqlite-vec + Legal-BERTimbau-base + PyMuPDF4LLM + Decimal + python-bcb + structlog
  - **Footprint:** 3-4GB RAM (vs 12-15GB), 0 containers (vs 5), 1 processo (vs 3+), 30s-2min/contrato (vs 5-8min)
  - **Custo VPS produção:** R$ 30-100/mês (vs R$ 500-1500)
  - `.project.yaml` atualizado refletindo arquitetura D
  - Documento canônico: `decisions/architecture-D-lean-2026-05-01.md`
- **Sessão 4** (@analyst / Atlas — 2026-05-01): **Phase 0 — Mitigações executadas + DESBLOQUEIO PARA ARIA**.
  - Eric pediu: "execute a recomendação".
  - Atlas executou as 3 ações de mitigação top-prioridade da análise de risco:
    1. **Specs do laptop verificadas** (PowerShell): RAM 16GB OK, mas **GPU GTX 1650 só 4GB VRAM — insuficiente p/ Sabia-7B Q4**.
    2. **Análise de concorrentes** (5 WebSearches): mercado existe, gap real identificado, **Tema 1378 STJ é variável crítica** (pendente julgamento).
    3. **Estratégia D-05** (curadoria) e **patch D-11** (hardware) decididos.
  - **Resultado:** 4 decisões revisadas (D-04 com flag de monitoramento, D-05 resolvida, D-10 promovida 🔴→🟡, D-11 com patch CPU-mode).
  - **Phase 0 100% fechada.** Próximo passo: invocar `LMAS:agents:architect` (Aria).
- **Sessão 3** (@analyst / Atlas — 2026-05-01): **Phase 0 — CLOSURE — 13 decisões delegadas + repos adicionais identificados**.
  - Eric delegou explicitamente as 13 decisões pendentes a Atlas com mandato: "você sabe o que faz diferença para esse projeto".
  - Atlas auditou org `abjur` completa (109 repos R-dominados), descobriu **`courtsbr/stf` + `courtsbr/stj`** como solução de seed para vault, identificou HuggingFace `joelniklaus/brazilian_court_decisions` e benchmark `JurisTCU`.
  - Documento de decisões consolidadas escrito em `decisions/decisions-consolidated-2026-05-01.md` — input formal para próxima Skill.
  - **Phase 0 está fechada.** Próximo passo: invocar `LMAS:agents:architect` (Aria) para SAD formal + 6 ADRs.
- **Sessão 2** (@analyst / Atlas — 2026-05-01): **Phase 0 — Data Sources & External Integrations Audit**.
  - Eric forneceu 6 URLs/repositórios para auditar e integrar ao projeto.
  - Atlas executou 6 WebFetches paralelos + 2 verificações complementares.
  - **Achados principais:**
    - DataJud (CNJ): 5 repos github imaturos — construir wrapper Python customizado baseado nos endpoints oficiais.
    - LexML: 30+ repos Scala/Java/TS — strategy: consumir API ou pré-cachear leis (CDC, CC, SFN, MP capitalização).
    - projeto-v3l0z: Django+DRF, sem licença — usar como referência arquitetural, não copiar código.
    - abjur/tidyML: R puro abandonado — descartar uso direto.
    - **BACEN GitHub oficial: DECEPÇÃO** — só repos de Pix/Real Digital. ZERO sobre SGS. Solução real: `python-bcb` (Wilson Freitas, MIT, 2026 ativo).
    - **STJ Concursos: URL INCORRETA** — é página de concursos públicos, não jurisprudência. Sugeridas 4 URLs alternativas (jurisprudência, súmulas, temas repetitivos, pesquisa pronta).
- **Sessão 1** (@lmas-master / Morpheus → @analyst / Atlas — 2026-04-30): **Phase 0 — Project Bootstrap + State-of-the-Art Validation + Module-by-Module Deep Dive**.
  - Eric Claudino solicitou criação do projeto na área de direito (Revisor Contratual — sistema agentic local de revisão jurídica de contratos bancários).
  - Especificação SAD completa fornecida pelo usuário (4 blocos, stack 100% local).
  - Solicitada validação técnica e pesquisa de alternativas (mais barato/robusto/que não trave).
  - Atlas concluiu **2 documentos de research**:
    - `state-of-the-art-2026-04-30.md` — comparação tecnológica (10 dimensões, 35+ fontes, 3 arquiteturas A/B/C).
    - `module-by-module-deep-dive-2026-04-30.md` — análise pontual arquivo-por-arquivo dos 4 blocos, 6 pesquisas adicionais, nova estrutura "sólida" proposta com `bloco_contratos/` + `bloco_api/` + `bloco_observability/`.
  - Eric reportou: "não senti solidez nessa estrutura que enviei" → Atlas validou: estrutura conceitualmente correta MAS com **3 fragilidades transversais**: acoplamento implícito sem contratos formais, falta de fail-loud em validações jurídicas, observabilidade ausente.

## Decisões Tomadas

### Sessão 3 (2026-05-01) — 13 Decisões Consolidadas (delegadas)

Documento canônico: `decisions/decisions-consolidated-2026-05-01.md`

| ID | Decisão | Escolha | Why |
|----|---------|---------|-----|
| **D-01** | Arquitetura | **C — Híbrido Pragmático** | Familiaridade Streamlit + cura furos críticos + migração incremental para B sob demanda |
| **D-02** | 3 blocos novos (`bloco_contratos/`, `bloco_api/`, `bloco_observability/`) | **SIM** | Cura as 3 fragilidades transversais do deep-dive |
| **D-03** | Decimal everywhere | **SIM — não-negociável** | Float em finanças jurídicas é vulnerabilidade legal (perícia não aceita) |
| **D-04** | Personas | **3 (eliminar Economista)** | Sem responsabilidade EXCLUSIVA — duplica latência LLM sem agregar |
| **D-05** | Vault inicial | **Seed manual com courtsbr/stf+stj** | Crítico para MVP — sem vault, RAG sempre vazio. Pipeline mensal em fase 2 |
| **D-06** | Fontes vault | **STF Súmulas Vinculantes + Repercussão Geral + STJ Súmulas + Temas Repetitivos** | Cobertura de pesos vinculação 5/5 e 4/5 — base para Juiz Revisor |
| **D-07** | DataJud | **Fase 2** | Não-crítico para MVP — enriquecimento estatístico |
| **D-08** | LexML | **Pré-cache de 4 diplomas (CDC, CC, SFN, MP cap)** | Cobre >95% das citações em revisão bancária PF |
| **D-09** | abjur | **Descartar uso direto** (109 repos R) | Stack incompatível; aproveitar conhecimento conceitual apenas |
| **D-10** | MVP scope | **CDC PF — Aquisição de Veículos** | Modalidade mais comum + jurisprudência consolidada + BACEN cód. 25471 |
| **D-11** | Hardware | **Laptop dev → Workstation prod** | Lean — não comprar hardware antes de MVP funcionar |
| **D-12** | UF inicial | **MG (TJMG)** | Súmula 30 TJMG é referência + câmaras especializadas |
| **D-13** | Domínio LMAS secundário | **Adiar fase 2** | MVP precisa funcionar antes de pricing/marca |

### Sessão 1 (2026-04-30)

- **Projeto criado** em `projects/Revisor-Contratual/` com estrutura padrão LMAS multi-project (prd/, architecture/, stories/, docs/, qa/, research/).
- **Domínio LMAS:** software-dev (sub-domain: legaltech).
- **Princípios inegociáveis confirmados** (do `.project.yaml`):
  - 100% local — zero envio de dados de contrato para cloud (LGPD).
  - Determinismo matemático — cálculos via NumPy, nunca via LLM.
  - Filtro jurisprudencial estrito por UF + tribunais superiores.
  - Human-in-the-Loop em divergências < 100%.
  - Aborta e gera Relatório de Inviabilidade se aderência < 100%.
- **Pipeline de validação técnica:** Atlas (research) → Aria (architecture) → Smith (adversarial). Skills sequenciais, não paralelas.
  - **Why:** cada skill alimenta a próxima com findings; paralelo causa duplicação de pesquisa e perda de contexto.
- **Pesquisa Atlas — 5 decisões críticas identificadas** (ver `research/state-of-the-art-2026-04-30.md`):
  1. Frontend: Streamlit puro vai travar — recomendar NiceGUI ou Streamlit+FastAPI separados.
  2. LLM serving: Ollama OK em dev mas vLLM em prod (16.6× throughput).
  3. Modelo PT-BR: Sabia-7B-GGUF ou Qwen 2.5 7B (não Llama 3 genérico). Sabia-3/4 descartado (API only — viola LGPD).
  4. Vector store: Qdrant (1.1× filter overhead) > ChromaDB (3-8× overhead). Crítico para filtro `WHERE court_id IN (...) AND binding == True`.
  5. Padrão "não trava": FastAPI + Dramatiq + Redis + SSE (descartar síncrono Streamlit→LangGraph direto).
- **Embeddings:** Legal-BERTimbau-sts-large (rufimelo) é único modelo PT-BR jurídico open. Substitui Sentence-Transformers genérico.
  - **Why:** Sentence-Transformers genérico não distingue "contrato de aluguel" de "contrato de trabalho" em PT-BR jurídico.
- **PDF parsing:** estratégia híbrida — Docling para tabelas de amortização (97.9% accuracy), Marker para OCR (Surya), PyMuPDF4LLM para texto rápido.
- **3 arquiteturas formalizadas** para escolha do PO/usuário:
  - **A:** Proposta original (rápida de subir, mas trava em produção).
  - **B:** Atlas aggressive upgrade (NiceGUI + FastAPI + Dramatiq + vLLM + Qdrant + Sabia + Legal-BERTimbau + Docling).
  - **C:** Híbrido Pragmático (mantém Streamlit, mas troca modelo, vector, embeddings, parsing, e adiciona FastAPI+RQ atrás).
- **Recomendação Atlas:** começar com **Arquitetura C** e migrar componentes para B sob demanda quando sentir limites.

## Ambiente Configurado

- Vault Obsidian: `projects/Revisor-Contratual/`
- Code path reservado: `packages/revisor-contratual/` (a criar quando @dev iniciar implementação)
- Stack confirmada (a refinar com Aria): Python 3.11+ / Streamlit / LangGraph / Ollama / ChromaDB OU Qdrant / Sentence-Transformers OU Legal-BERTimbau / Marker OU Docling / NumPy Financial / BACEN SGS API
- LGPD compliance: 100% local — nenhum dado de contrato sai da máquina/VPS

## Último Trabalho Realizado

### Sessão 2026-05-01 (Etapa 1.0 — PRD v1.0.0 criado por Morgan)

**PRD v1.0.0 entregue** (Morgan, @pm):
- Arquivo: `projects/Revisor-Contratual/prd/prd-v1.0.0.md` (~700 linhas)
- Anatomia mínima Ordem 6 cumprida: visão, objetivo, personas, escopo IN/OUT, FRs com ACs numéricos, NFRs, UX, dependências, riscos, change log v1.0.0
- 30+ FRs distribuídos em 10 áreas: Auth, Upload/Parse, Cálculo, BACEN, RAG, Tese, Juiz, Deliverables, ML, Audit
- 4 personas internas formalmente restauradas (Economista de volta — D-04 revogada)
- 5º deliverable adicionado: Recursos Processuais (escopo NOVO)
- 6 itens [DADO-PENDENTE] sinalizados (sem invenção de números)
- 7 NOTAS críticas para Aria (incluindo update do .project.yaml)
- Próxima etapa: tribunal severo (Sati UX → Smith adversarial → checkpoint governance)

### Sessão 2026-05-01 (Phase 0 — REFATORAÇÃO LEAN + UF=BA)

**Refatoração radical para arquitetura D (LEAN)** (Atlas, @analyst):
- 3 WebSearches (sqlite-vec maturity, Phi-3/Qwen/Gemma comparison, TJBA jurisprudência)
- Auto-crítica honesta: stack C era sobre-engenheirada para o caso real
- Arquivo principal: `decisions/architecture-D-lean-2026-05-01.md`
- `.project.yaml` reescrito refletindo nova arquitetura
- **5 decisões revisadas** (D-01, D-02, D-04, D-11, D-12)
- **D-12 confirmada UF=BA** (TJBA tem corpus consumerista bancária ativo, alinhado com Tema 1378 STJ)

**Comparação A/B/C/D:**
| | A original | B aggressive | C híbrido | **D LEAN** |
|--|--|--|--|--|
| RAM | ~6GB | ~12GB | ~12GB | **3-4GB** |
| Containers | 0 | 5 | 5 | **0** |
| Latência | trava | 1-3min | 5-8min | **30s-2min** |
| LLM calls | n/a | 4 | 4 | **1** |
| Custo VPS | n/a | R$1500/mês | R$500/mês | **R$30-100/mês** |

### Sessão 2026-05-01 (Phase 0 — Mitigações + DESBLOQUEIO)

**Execução das mitigações top-3 da análise de risco** (Atlas, @analyst):

1. **Hardware (D-11)** — Confirmado via PowerShell:
   - Intel i5-10300H 4C/8T, **GPU NVIDIA GTX 1650 (4GB VRAM)**, RAM 16GB, Disk 333GB livres
   - **Patch crítico:** Sabia-7B Q4 não cabe em 4GB GPU → **rodar em CPU** com Ollama `--num-gpu-layers 0` (latência 10-30s/resposta — aceitável dev solo)

2. **Concorrentes (D-10)** — 5 WebSearches:
   - Arquivo: `research/competitor-analysis-2026-05-01.md`
   - **Mercado existe:** JusCalc/CJ têm 2.000+ advogados pagantes
   - **Gap real:** ninguém faz "calc + RAG jurisprudencial + tese AI" integrado (só calculadoras OU só busca OU só modelos)
   - **Achado crítico — Tema 1378 STJ** (afetado 09/09/2025, **pendente julgamento**): vai definir se BACEN é critério único ou se precisa análise circunstancial → **pode reverter D-04 (Economista)**
   - Enter LegalTech está do **lado oposto** (defende bancos, não consumidores) — não-concorrente
   - **D-10 promovida 🔴 ALTA → 🟡 MODERADA** com mitigações arquiteturais

3. **Curadoria vault (D-05)** — Estratégia decidida:
   - Arquivo: `decisions/vault-curation-and-hardware-strategy-2026-05-01.md`
   - **Pipeline 3-camadas:** Atlas scrapers Python → Sabia auto-classifica → Eric valida amostra estratificada
   - Tempo estimado: **4-6 dias** (vs 5-10 dias 100% manual)
   - Atlas re-implementa scrapers em Python (não roda R do `courtsbr/*`)

### Sessão 2026-05-01 (continuação — Análise de Risco)

**Análise de risco das 13 decisões** (Atlas, @analyst):
- Arquivo: `decisions/risk-analysis-13-decisions-2026-05-01.md`
- Mapa de calor: 8 decisões 🟢 sólidas / 4 🟡 moderadas / 1 🔴 ALTA (D-10)
- **D-10 (MVP CDC Veículos) é o único risco que pode descarrilhar o projeto** — mercado saturado + Selic baixa + Súmula 539 reduzem demanda
- Top 3 ações antes de invocar @architect: análise de concorrentes (D-10), decidir quem cura vault (D-05), confirmar RAM laptop (D-11)
- **Phase 0 fechada tecnicamente; semi-fechada em produto** (validação de mercado pendente)

### Sessão 2026-05-01 (Phase 0 — CLOSURE — Decisões delegadas)

**13 decisões consolidadas + auditoria final** (Atlas, @analyst):
- 1 WebFetch (auditoria org abjur — 109 repos confirmados, R-dominados)
- 2 WebSearches (HuggingFace datasets + scrapers GitHub para STF/STJ)
- Arquivo principal: `projects/Revisor-Contratual/decisions/decisions-consolidated-2026-05-01.md` (~700 linhas)
- **Repos adicionais incorporados ao plano:**
  - `courtsbr/stf` + `courtsbr/stj` — vault seed (R, output JSON stack-agnóstico)
  - HuggingFace `joelniklaus/brazilian_court_decisions` — enriquecimento STF+STJ+TJ-SP+TJ-RJ+TSE
  - `JurisTCU` (16k docs + 150 queries com relevance) — **test set para benchmark RAG**
  - `tiagocupertino/tjrj-datajud-api-scraping` — referência Python DataJud (fase 2)
- **Stack final consolidada** com 7 blocos (4 originais + 3 novos), pré-seed legislação + jurisprudência, taxonomia controlada
- **Itens deixados em aberto** (não decididos por mim): nome comercial, modelo de negócio, mercado-alvo geográfico, política de retenção LGPD
- **Phase 0 fechada.** Próximo handoff: `LMAS:agents:architect` (Aria) com mandato de SAD formal + 6 ADRs + diagramas C4

### Sessão 2026-05-01 (Phase 0 — Data Sources Audit)

**Auditoria de 6 fontes externas fornecidas por Eric** (Atlas, @analyst):
- 6 WebFetches + 2 buscas complementares
- Arquivo: `projects/Revisor-Contratual/research/data-sources-external-integrations-2026-05-01.md`
- Mapeamento Fonte → Bloco do Revisor:
  - **DataJud → Bloco 4** (cliente customizado em `bloco_engine/integracao/datajud_client.py`)
  - **LexML → Bloco 3** (seed legislação CDC, CC, SFN) + Bloco 4 (resolver remissões via regex local)
  - **python-bcb → Bloco 4** (substituir API direta BACEN — usa `OData.TaxaJuros` e `OData.MercadoImobiliario`)
  - **STJ → Bloco 3** (seed jurisprudência) — pendente Eric confirmar URL correta
- 2 fontes complementares críticas identificadas que faltam:
  - **STF Súmulas Vinculantes** + **STF Repercussão Geral** (peso vinculação 5/5)
  - **Outros 18 repos da org github.com/abjur** (não auditados — vale sweep)
- **Stack final de integrações** consolidada em `bloco_engine/integracao/` (datajud, lexml, bacen, stj clients)
- **Pipeline de re-indexação mensal** proposta para Bloco 3

### Sessão 2026-04-30 (Phase 0 — Bootstrap + Research + Deep Dive)

**Bootstrap do projeto** (Morpheus, @lmas-master):
- Criada estrutura de diretórios: `prd/`, `architecture/`, `stories/`, `docs/`, `qa/`, `research/`
- Arquivo: `projects/Revisor-Contratual/.project.yaml` — config canônico (stack, blocos, agentes internos, princípios)

**Pesquisa state-of-the-art** (Atlas, @analyst):
- 10 WebSearches + 1 WebFetch executados
- 35+ fontes verificáveis citadas (papers, benchmarks, repos)
- Arquivo: `projects/Revisor-Contratual/research/state-of-the-art-2026-04-30.md` (~1900 linhas, 10 dimensões, tabelas comparativas)
- 3 arquiteturas sintetizadas (A/B/C) para escolha humana

**Module-by-module deep dive** (Atlas — 2ª iteração após feedback "não senti solidez"):
- 6 WebSearches focadas em gaps específicos por bloco
- Arquivo: `projects/Revisor-Contratual/research/module-by-module-deep-dive-2026-04-30.md`
- Análise pontual arquivo-por-arquivo dos 4 blocos com fragilidades + alternativas + patches concretos
- Identificou **3 fragilidades transversais**:
  1. Acoplamento implícito sem contratos formais (Pydantic models compartilhados ausentes)
  2. Silent failures em validações jurídicas (sem fail-loud)
  3. Observabilidade ausente (sem tracing, sem audit-log)
- Propôs **nova estrutura "sólida"** adicionando 3 blocos: `bloco_contratos/` (Pydantic shared), `bloco_api/` (FastAPI bridge), `bloco_observability/` (OpenTelemetry + audit-log)
- Patches críticos identificados por bloco (em ordem de impacto):
  - Bloco 1: api_client + Pydantic + SSE + HITL tipado + petição Jinja2/WeasyPrint
  - Bloco 2: TypedDict reducers + Decimal-as-string + structured output + citation grounding + 3-vias Juiz
  - Bloco 3: schema enriquecido + chunking jurídico + summary enrichment + dedup + RRF + cache
  - Bloco 4: Decimal everywhere + regime juros simples/compostos + anatocismo integrando Súmulas 121/539 + mapping modalidade→BACEN
- Checklist de Solidez por bloco para validação pré-implementação

**Checkpoint** (Atlas):
- Arquivo: `projects/Revisor-Contratual/PROJECT-CHECKPOINT.md` (criado + atualizado nesta sessão)

## Próximos Passos

### Imediatos (próxima sessão)

- [ ] **Eric escolhe entre arquiteturas A / B / C** — apresentar comparação visual e capturar decisão.
- [ ] **Invocar `LMAS:agents:architect` (Aria)** — produzir SAD formal da arquitetura escolhida + ADRs por decisão crítica.
  - Input: `research/state-of-the-art-2026-04-30.md` + `.project.yaml` + decisão de arquitetura.
  - Output: `architecture/system-architecture-v1.0.md` + ADRs em `architecture/adr/`
- [ ] **Invocar `LMAS:agents:smith`** — adversarial review da arquitetura escolhida + identificar fragilidades não cobertas.
  - Output: `qa/smith-adversarial-review-pre-mvp.md`

### Curto prazo (Phase 1)

- [ ] **Invocar `LMAS:agents:pm` (Morgan)** — formalizar PRD v1.0 baseado em spec + research + ADRs.
  - Output: `prd/prd-v1.0.md`
- [ ] **Invocar `LMAS:agents:po` (Keymaker)** — validar PRD v1.0 (G1 quality gate).
- [ ] **Invocar `LMAS:agents:sm` (River)** — criar Epic 1 + Stories iniciais (bootstrap repo + bloco engine + bloco vault).
- [ ] Criar `CLAUDE.md` específico do projeto (convenções, comandos, paths) — owner: @architect ou @pm.

### Médio prazo (Phase 2 — Implementação)

- [ ] Provisionar `packages/revisor-contratual/` com estrutura monorepo Python.
- [ ] Implementar Bloco 4 (Engine de Parsing + BACEN + NumPy) primeiro — fundação determinística.
- [ ] Implementar Bloco 3 (Vault RAG) com vault inicial seed (jurisprudência STJ/STF + 1 TJ piloto).
- [ ] Implementar Bloco 2 (Agentes LangGraph) com 4 personas + checkpointer.
- [ ] Implementar Bloco 1 (UI) por último — depende dos demais.

### Itens marcados [verificar] (resolver durante implementação)

1. Códigos BACEN SGS por modalidade — consultar [SGS portal oficial](https://www3.bcb.gov.br/sgspub/).
2. Benchmark Sabia-7B vs Qwen 2.5 7B em jurídico PT-BR — rodar piloto interno com 50 contratos.
3. DeepSeek R1 7B distilled em OAB — testar antes de adotar para Juiz Revisor.
4. Performance Legal-BERTimbau + Qdrant em escala — load test com 10k+ docs sintéticos.
5. Latência end-to-end — medir pós-implementação; meta: contrato 30 pgs em < 5 min em workstation.

## Violações de Selo — Status Atualizado (Morpheus etapa 1.0)

- [x] **V-1 RESOLVIDA conceitualmente:** `decisions/*.md` agora tratados como `inputs/briefs` para Morgan (PRD) e Aria (ADRs). Sem renomeação física por ora; nomenclatura corrigida na geração dos artefatos formais.
- [x] **V-2 RESOLVIDA:** Eric invocou Morpheus (Ordem 1 cumprida).
- [x] **V-3 RESOLVIDA:** D-04 revogada por Morpheus. 4 personas restabelecidas no escopo do produto. Morgan deve refletir no PRD; Aria nos ADRs.
- [x] **Escopo novo capturado:** "Recursos Processuais" entra no PRD como deliverable nomeado.

## Decisões Pendentes (humanas) — Phase 0 100% fechada, ficam apenas estas:

- [ ] **Validação qualitativa com 3-5 advogados-piloto** (Atlas não pode fazer — Eric precisa conversar pessoalmente) — destrava D-10 100%
- [ ] **Nome comercial** do produto ("Revisor Contratual" é codinome interno) → @kamala em fase 2
- [ ] **Modelo de negócio** (R$/contrato? subscription? freemium?) → @mifune em fase 2
- [ ] **Mercado-alvo geográfico** (escritório local em qual cidade?) → impacta D-12 (UF inicial)
- [ ] **Política de retenção de dados** dos contratos (LGPD) → @architect propõe; humano decide
- [ ] **Confirmação Eric das 13 decisões + 4 revisadas** (Atlas decidiu por delegação — overridable)

## Monitoramento Contínuo

- [ ] **Tema 1378 STJ** — afetado em 09/09/2025, julgamento pendente. Pode reverter D-04 (Economista) e D-10 (escopo). Sugestão: `*loop` mensal verificando STJ.

## Git Recente

- Branch: `main`
- Status: projeto novo — nenhum commit ainda específico do Revisor-Contratual.
- Próximo commit recomendado: `feat(revisor-contratual): bootstrap project structure + state-of-the-art research`

## Risk Register Inicial

| ID | Risco | Severidade | Mitigação |
|----|-------|-----------|-----------|
| R-001 | Streamlit trava em workflow longo (5-30min) | HIGH | Off-load para FastAPI+queue (Arquitetura B/C) |
| R-002 | Llama 3 genérico erra termos jurídicos PT-BR | HIGH | Trocar para Sabia-7B ou Qwen 2.5 |
| R-003 | ChromaDB filter overhead 3-8× quebra Regra de Consulta | HIGH | Migrar para Qdrant + payload index |
| R-004 | API BACEN down ou rate-limited | MEDIUM | diskcache + tenacity retry + fallback "última taxa conhecida" |
| R-005 | LGPD violation se algum modelo/embedding cair em cloud | CRITICAL | Audit cego antes de cada decisão; descartar tudo que precise API externa |
| R-006 | Custo hardware GPU subestimado (RTX 4070 Ti R$ 7k) | MEDIUM | Cenário B (VPS CPU-only com Ollama lento) é fallback aceitável para POC |
| R-007 | Sabia-7B é geração antiga (2023) — pode degradar vs alternativas modernas | MEDIUM | Benchmark interno A/B Sabia vs Qwen 2.5 antes de fixar |
| R-008 | Vault de jurisprudência sem manutenção fica stale | HIGH | Pipeline de re-indexação mensal automatizada |

---

*Checkpoint criado por @analyst (Atlas) em 2026-04-30 — primeira sessão do projeto Revisor Contratual.*
