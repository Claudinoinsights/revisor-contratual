---
type: qa-adversarial-review
title: "Smith Sprint 04 Pivot — Adversarial Review (PRD v2.0.0 + 5 ADRs + UX)"
project: revisor-contratual
sprint: 04
phase: 5
review_mode: ULTRATHINK
reviewer: "@qa Smith (Oracle adversarial mode)"
date: "2026-05-07"
verdict: CONCERNS
findings_count_by_severity:
  CRITICAL: 4
  HIGH: 19
  MEDIUM: 13
  LOW: 2
total_findings: 38
tags:
  - project/revisor-contratual
  - qa-adversarial
  - sprint-04
  - ultrathink
---

# Smith Sprint 04 Pivot — Adversarial Review

> **Mr. Anderson...** o pivot tem ossos sólidos mas pele furada em 38 pontos. 4 CRITICAL exigem decisão Eric antes de Phase 7. 19 HIGH viram debt CC.43+. Document architecture is real; gaps are real too. Choose carefully which gaps to close before paying — and which to accept.

---

## 1. Sumário Executivo

**Verdict: CONCERNS** ⚠️

Pivot Sprint 04 é arquiteturalmente sólido (Atlas research robusto, Aria ADRs coerentes, Trinity PRD estruturado, Sati UX simplificado em harmonia com Phase 3.1). Mas **38 findings reais** identificam:

- **4 CRITICAL** que bloqueiam Phase 7 implementation se ignorados
- **19 HIGH** que viram tech debt acumulado durante Sprint 04
- **13 MEDIUM** debt CC.50+
- **2 LOW** polish

**Recomendação Eric:** patch 4 CRITICAL antes de PR creation. HIGH listados em TECH-DEBT.md endereçam-se em Sprint 04 stories conforme prioridade. Pivot **não está pronto para PR final** — precisa Phase 5.5 patches.

**Counts severidade:**

| Severidade | Count | Ação |
|---|---|---|
| CRITICAL | 4 | Patch antes Phase 7 implementation |
| HIGH | 19 | TECH-DEBT.md priorizados Sprint 04 stories |
| MEDIUM | 13 | TECH-DEBT.md CC.50+ |
| LOW | 2 | Polish opcional |
| **TOTAL** | **38** | Paridade Smith CC.41 (22 findings) atingida |

---

## 2. Escopo Declarado (lesson Smith CC.41)

**ESTE review cobre:**
- ✅ PRD v2.0.0 DRAFT (governance/prd/prd-v2.0.0-DRAFT.md)
- ✅ 5 ADRs Sprint 04 (adr-014..018)
- ✅ UX Spec v2.0.0 DRAFT (governance/ux-spec-v2.0.0-DRAFT.md)
- ✅ Atlas research v1+v2
- ✅ Coerência cross-document entre os 4 inputs

**ESTE review NÃO cobre:**
- ❌ Implementation code (não existe ainda — escopo @dev Phase 7+)
- ❌ PRD v1.1.2 deprecated (fora do pivot)
- ❌ ADR-001..006 + 008 + 012 (preserved Sprint 03, fora do escopo)
- ❌ OrSheva brandbook em vault Eric (input Sati, fora do escopo Smith)
- ❌ Penetration testing real RLS (requer ambiente staging — Phase 7+)
- ❌ Smoke E2E real (requer code — Phase 7+)

**Lesson aplicada:** Smith CC.37 errou por escopo estreito; CC.41 corrigiu wider. Esta review é wider que conforto, mas declarada.

---

## 3. Findings CRITICAL (4)

### F-003 [CRITICAL] — UX S6 expõe "Baixar Petição D3" sem FR-OUTPUT específico para D3

**Dimension:** D1 Coerência Cross-Document

**Evidence:**
- UX S6 wireframe inclui CTA "📥 Baixar Petição D3"
- PRD FR-OUTPUT-01..04 cobrem PDF de **análise** (relatório das 4 personas + Juiz)
- PRD FR-D3-01 atualizado Phase 3.1 diz "petição em PDF + mesmo flow FR-OUTPUT-03"
- Mas D3 tem template diferente, conteúdo diferente (Apelação Cível ≠ relatório de análise)
- Não há FR-OUTPUT-D3 específico

**Impact:** Phase 7 @dev implementa FR-OUTPUT-04 (relatório PDF) mas não tem spec clara para D3 PDF (estrutura, template Jinja2 distinto, signing legal?). Bug latente: D3 acaba copiando template análise OR fica órfão.

**Remediation:** Trinity Phase 5.5 patch — adicionar FR-OUTPUT-D3 explícito com:
- Template Jinja2 separado (`templates_d3/{doctype}.txt`)
- Estrutura distinta (cabeçalho legal, fundamentação, pedidos)
- Watermark "Petição IA — Revisão por Advogado Obrigatória" (ou similar)
- Conteúdo legal pendente Eric advogado (já flaggado)

---

### F-007 [CRITICAL] — Tab fechada durante S5 processing: comportamento não declarado

**Dimension:** D2 Workflow Gaps

**Evidence:**
- Atlas v1 + ADR-015 confirmam pipeline async (`asyncio.gather`) → análise continua server-side
- UX S5 mostra "💡 Pode fechar essa tela — você será notificado quando estiver pronto"
- Mas PRD não tem FR para notification mechanism (email? web push? in-app banner ao re-login?)
- Sem notification, advogado pode esquecer análise pendente → expiração 30 dias → perda
- Pior: análise pode ter consumido API tokens (escritório paga Anthropic) sem advogado saber

**Impact:** UX promete notificação mas implementação não tem mecanismo. Quando advogado fechar tab e voltar 2h depois, vê dashboard com análise em "approved-ready" status mas SEM toast/email — tem que descobrir por garimpagem. Quebra promessa UX explícita.

**Remediation:** PRD Phase 5.5 patch — FR-NOTIFY-01:
- Email transactional (SendGrid/Resend) quando análise muda para `pending_review`
- In-app banner persistente em S3 dashboard ao re-login
- Optional: web push notifications (Settings preference per usuário)

---

### F-012 [CRITICAL] — DPA acceptance storage/versioning não definido

**Dimension:** D3 LGPD Operador Robustez

**Evidence:**
- PRD FR-LGPD-01 diz "DPA Eric-escritório obrigatório no onboarding"
- UX S2 mostra "DPA acceptance" como passo do wizard
- Mas PRD/ADRs não detalham:
  - **Storage:** column boolean em `tenants`? Tabela `dpa_acceptances` separada? PDF do DPA aceito stored como BLOB?
  - **Versioning:** DPA v1 vs v2 — tenant que aceitou v1 precisa re-aceitar v2 quando atualizado?
  - **Hash:** registro criptográfico de qual versão exata foi aceita (audit trail legal)
  - **Timestamp:** UTC com timezone (ANPD pode pedir evidence em horário local BR)
  - **IP origin:** prova adicional de aceite real

**Impact:** ANPD pode auditar Eric (operador) e pedir evidence. Sem schema explícito, Eric não consegue provar quando/como/qual versão DPA foi aceita por escritório X. Risco LGPD multa Art. 52 (até 2% faturamento, R$ 50M cap). **Operador sem prova legal = exposição direta.**

**Remediation:** Aria Phase 5.5 patch ADR-019 OR estender ADR-017:
```sql
CREATE TABLE dpa_acceptances (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants,
  dpa_version VARCHAR(20) NOT NULL,
  dpa_text_hash VARCHAR(64) NOT NULL, -- SHA-256 do texto exato aceito
  accepted_at TIMESTAMP WITH TIME ZONE NOT NULL,
  accepted_by_user_id UUID NOT NULL REFERENCES users,
  ip_address INET,
  user_agent TEXT
);
-- RLS policy + retention permanent (legal evidence)
```

---

### F-016 [CRITICAL] — Argumento legal "Anthropic é subprocessor do escritório" não validado

**Dimension:** D3 LGPD Operador Robustez

**Evidence:**
- Atlas v2 Section 4 sugere Eric=operador, escritório=controlador, Anthropic=subprocessor
- Argumento implícito: "escritório cadastra SUA própria key Anthropic, então Anthropic é subprocessor DO escritório"
- Mas LGPD Art. 5º VIII define operador como "pessoa que realiza o tratamento de dados pessoais em nome do controlador"
- **Eric (operador) é quem TRANSMITE PII para Anthropic** via app — mesmo que key seja do escritório
- Argumento de "key do escritório = subprocessor do escritório" pode não passar em ANPD/judicial review
- Atlas v2 sugeriu MAS NÃO VALIDOU com advogado especializado LGPD

**Impact:** Se ANPD/judiciário decidir que **Eric é responsável solidário** por PII transmitida via app dele (mesmo com key escritório), exposição financeira direta. DPA template Atlas listou pontos mas advogado de LGPD precisa redigir/validar com a interpretação correta da relação tripartite.

**Remediation:** Eric Phase 5.5 — consultar advogado especializado LGPD (não apenas advocacia geral) para:
- Validar argumento "Anthropic = subprocessor escritório"
- Redigir DPA com interpretação correta
- Considerar arquitetura alternativa: app NÃO toca PII (apenas roteia bytes API → escritório → Anthropic), mas isso quebra OCR + caching (sistema precisa armazenar markdown para consulta)

---

## 4. Findings HIGH (19)

### F-001 [HIGH] — Watermark text customization não documentada
- D1 — FR-OUTPUT-04 hardcoda "Análise IA — Revisão por Advogado Obrigatória"; sem ADR sobre i18n/customization. Eric pode querer marca branded por escritório. Phase 7 vai improvise.

### F-002 [HIGH] — Persona prompt loading mechanism não especificado
- D1 — ADR-016 menciona 16 prompts arquivos, mas nenhum FR/ADR detalha mecanismo: filesystem read on-demand? Cached em memória? Recarrega quando arquivo muda?

### F-006 [HIGH] — Onboarding S2 Tier step não detalha payment flow
- D1+D2 — Trial gratuito? Cartão obrigatório no signup? Boleto pré-pago? Nem PRD nem UX clarificam. Risk: Phase 7 build wrong flow.

### F-008 [HIGH] — Login expira durante S4 upload: form data lost
- D2 — UX não declara behavior. Re-login mantém PDF in browser? Auto-save draft? Mensagem de erro? Frustração garantida sem spec.

### F-009 [HIGH] — Refresh em S6 pending_review: behavior não declarado
- D2 — F5 deve mostrar mesmo state? Refetch from server? Botões disponíveis se download ainda não feito? Sem spec, comportamento inconsistente.

### F-011 [HIGH] — Sem undo/grace period após approval
- D2+D4 — Approval click → billing event imediato. Não há janela 30s para retract. Advogado clica errado → Stripe invoice line. Refund flow inexistente.

### F-013 [HIGH] — RLS isolation verification beyond endpoint metadata
- D3 — `/tenant/audit/isolation` provê metadata mas não roda penetration test. Como provar isolamento concreto? Eric promete operador robustez mas só metadata = fraco evidence ANPD.

### F-014 [HIGH] — Retention 12 meses cron job não definido
- D3 — Sem job automatizado, logs acumulam infinitamente. Disk grows, performance degrada, LGPD claim "12 meses retention" vira mentira documentada.

### F-015 [HIGH] — `ocr_cache.markdown_text` armazena PII contradizendo zero-retention claim
- D3 — ADR-015 cache 90 dias com markdown text. Markdown contém PII original (CPF, nome, endereço, valores). PRD diz "PII zero-retention pós-resposta API" — **contradição direta**.

### F-017 [HIGH] — Cancel S5 mid-flight não tem refund flow
- D4 — API tokens consumidos, escritório paga Anthropic. Eric não cobra approval, mas escritório vê custo Anthropic sem completar. UX não comunica esse trade-off.

### F-019 [HIGH] — Stripe webhook async failure recovery não definida
- D4 — ADR-018 menciona "retry strategy" mas sem detalhes: backoff strategy, max attempts, dead-letter queue, manual retry tool. Risk: silent billing failures.

### F-021 [HIGH] — Anthropic Sonnet 4.6 deprecation: sem migration path
- D5 — ADR-014 hardcoda model. Anthropic typically deprecates 12-18 meses. Sem ADR de migration strategy → emergency refactor quando happen.

### F-023 [HIGH] — Anthropic API outage: sem degraded mode
- D5 — App fica inerte. Status page mencionado mas escritório precisa alternativa (manual upload? queue para retry quando back?).

### F-024 [HIGH] — WCAG contrast pairs incompletos — apenas 5 auditados
- D6 — Sati cobriu 5 pairs. Faltam: status badges (4 estados × 2 themes = 8), tier badges (3 × 2 = 6), notification toasts (3 × 2 = 6), form validation errors. ~20 pairs não auditados.

### F-027 [HIGH] — Audit chain HMAC adapt tenant_id: arquitetura não definida
- D7 — ADR-005 preserved. Multi-tenant adapt: chain por tenant ou compartilhada? Genesis entry tem tenant_id ou é global? Aria precisa decidir antes Phase 7.

### F-030 [HIGH] — Pricing benchmark ranges: comparação apples-to-oranges
- D8 — Astrea/ADVBOX são gestão (não análise jurídica IA). Atlas v2 ranges não comparam mesma vertical. Mifune precisa benchmark real (escasso BR).

### F-031 [HIGH] — PRD não pricou absoluto: implementation pode bloquear
- D8 — Trinity flag explícito. Risk: Eric+Mifune chegam a número que escritório recusa, retrabalho UX S2.

### F-034 [HIGH] — Backup/restore strategy não definida
- D7 — PostgreSQL Pool tenants — backup diário? RPO/RTO? Disaster recovery? Sem ADR = operacional debt latente.

### F-037 [HIGH] — Admin Eric (S8) precisa BYPASS RLS — não documentado
- D1 — UX S8 mostra cross-tenant data. ADR-017 RLS força filter por tenant_id. Sem ADR sobre admin role exception, FR-ADMIN-01 fica imposible de implementar correctly.

---

## 5. Findings MEDIUM (13)

### F-004 [MEDIUM] — Versionamento de prompts: governance não definido
- D1 — Quem aprova mudança de prompt? Audit trail mudanças? Rollback? Prompt é código?

### F-005 [MEDIUM] — `tenant_subscription` definido em 2 ADRs (overlap)
- D1 — ADR-017 + ADR-018 ambos mencionam. Schema authoritative em qual? Risco de divergence.

### F-010 [MEDIUM] — Onboarding S2 sem help inline para API key Anthropic
- D2 — Advogado leigo em tech: onde busca a key? Anthropic Console step-by-step screenshots ausentes.

### F-018 [MEDIUM] — Tier downgrade meio mês: behavior não declarado
- D4 — Pro→Starter quando 28/30 já usado vs novo limite 5? Block? Permite até reset?

### F-020 [MEDIUM] — Approval idempotência: schema UNIQUE não declarado
- D4 — Double-click rápido pode criar 2 billing_events. ADR-018 schema não tem `UNIQUE(analysis_id)`.

### F-022 [MEDIUM] — Anthropic price hike: sem ADR de pricing review trigger
- D5 — Hike vai direto escritório. Eric pode perder churn. Sem ADR de monitoring + comms strategy.

### F-025 [MEDIUM] — SSE live region polite vs assertive: distinção não documentada
- D6 — Errors devem interrupt screen reader. Sati só mencionou polite.

### F-028 [MEDIUM] — `bloco_audit/chain.py` migration SQLite→PostgreSQL: refactor profundo
- D7 — Não é trivial como ADR-017 sugere. Storage backend change implica abstrair persistence.

### F-029 [MEDIUM] — MVP-LEAN-01 deprecation parcial: clareza developers
- D7 — Story file ainda existe sem watermark "DEPRECATED". Future devs podem confundir.

### F-032 [MEDIUM] — Margem Eric vs custo manual: premium positioning não validado
- D8 — Atlas estimou R$ 400-1200 manual. Real varia massivamente. Marketing message convincente requer validação mercado.

### F-033 [MEDIUM] — Multi-user lifecycle: suspend/reactivate session behavior
- D2 — Advogado X suspended pelo escritório: força logout? Mantém sessão? PRD não cobre.

### F-035 [MEDIUM] — Localization: pt-BR assumption implícita
- D7 — UX em pt-BR. Anthropic API responses em pt-BR? Persona prompts pt-BR? Implicit assumption.

### F-038 [MEDIUM] — Custo médio API em S7 Settings: cálculo não definido
- D1 — UX mostra "R$ 4,18/análise" mas onde calculado? Real-time Anthropic API ou estimativa hardcoded?

---

## 6. Findings LOW (2)

### F-026 [LOW] — `prefers-reduced-motion` cobertura incerta
- D6 — Sati mencionou mas não fez audit completo de todas animações. C3 modal fade? C7 toast slide-in?

### F-036 [LOW] — SEO: meta tags / schema.org não cobertos
- D7 — SaaS público precisa achar. Sati não cobriu. Marketing/SEO debt.

---

## 7. Verificação Cross-Document Matrix

| Documento | PRD v2.0.0 | ADR-014 | ADR-015 | ADR-016 | ADR-017 | ADR-018 | UX Spec | Verdict |
|---|---|---|---|---|---|---|---|---|
| FRs alinhados | — | ✅ | ✅ | ⚠️ F-002 | ✅ | ✅ | ⚠️ F-003 F-006 F-009 F-037 | CONCERNS |
| ADRs entre si | — | ✅ | ✅ | ✅ | ⚠️ F-005 (overlap 018) | ⚠️ F-005 | — | CONCERNS |
| Telas ↔ FRs | ⚠️ F-003 | — | — | — | — | — | ⚠️ F-006 F-037 | CONCERNS |
| LGPD compliance | ⚠️ F-012 F-015 F-016 | — | ⚠️ F-015 | — | ⚠️ F-013 F-014 | — | — | **CRITICAL gaps** |

**Resumo cross-doc:** 3 dos 4 quadrantes têm gaps. PRD ↔ UX é onde mais gap (4 findings). ADRs entre si é o mais coerente (1 overlap menor). LGPD spread em múltiplos artefatos (4 findings).

---

## 8. Edge Cases Mapeados (cenários documentos pularam)

1. **Análise órfã:** análise iniciada com tier Pro, escritório downgrade Starter mid-flight — qual tier cobra?
2. **Concurrent approve:** dois advogados do mesmo escritório clicam Aprovar na mesma análise simultaneamente — race condition
3. **API key revoked mid-analysis:** OCR completo, personas a meio caminho, escritório revoga key — análise crashes ou recovers?
4. **DPA atualizado mid-subscription:** escritório aceitou v1, Eric publica v2 — block uso até re-aceite ou grace period?
5. **Browser back button em S5:** advogado clica Voltar durante processing — análise continua server-side mas UI loses thread?
6. **PDF generation timeout:** Sonnet 4.6 PDF render falha 3 retries — análise vira `failed` mas tokens já consumidos?
7. **Stripe customer deleted:** Eric deleta customer Stripe by accident — billing events orphans?
8. **Tenant deletion (LGPD Art. 18):** escritório pede eliminação completa LGPD — RLS isolation deve permitir TRUNCATE TABLE WHERE tenant_id, mas não há FR-LGPD-DELETE
9. **Internal admin gone rogue:** Eric admin user comprometido — admin RLS bypass + cross-tenant view = catástrofe; sem MFA forçado?
10. **WebSocket vs SSE choice:** UX assume SSE em S5 mas Aria não confirmou em ADR — gap implementation

---

## 9. Recomendações Estratégicas (não-bloqueantes, advisory)

1. **Phase 5.5 patches obrigatórios** antes Phase 7: 4 CRITICAL findings (F-003, F-007, F-012, F-016)
2. **Penetration testing externo** antes launch beta: validar RLS multi-tenant via firma especializada (R$ 5-15k)
3. **Advogado LGPD especializado** consult Eric: F-012 + F-016 são jurídicos, não técnicos
4. **TECH-DEBT.md** populated com 19 HIGH + 13 MEDIUM + 2 LOW (34 items para CC.43+)
5. **Mifune dispatch** cross-domain antes Phase 7: F-030 + F-031 valores absolutos pricing crítico
6. **Architecture review iteração 2** depois de F-012+F-016 redesigned: pode invalidar ADR-017 partes
7. **Beta launch limit 4 escritórios** TBD per PRD audience: permite Smith iterar review em produção real
8. **Smith Sprint 05+ recurrent**: adversarial review por sprint (não só uma vez)

---

## 10. Verdict Final

**CONCERNS** ⚠️

### Justificativa Formal

PASS impossível: 4 CRITICAL findings reais (F-003 D3 PDF spec gap, F-007 notification mechanism, F-012 DPA storage, F-016 LGPD argument validation) bloqueiam Phase 7 implementation responsável.

FAIL inadequado: pivot é arquiteturalmente sólido. Atlas research robusto, ADRs Aria coerentes, Trinity PRD estruturado, Sati UX simplificado. Findings são gaps endereçáveis, não falhas fundamentais.

CONCERNS é veredito honesto: pivot **pode prosseguir com patches Phase 5.5** + remediation paths claros + tech debt documentado.

### Path Forward Recomendado

**Phase 5.5 (patches CRITICAL) — obrigatório antes PR:**
- Trinity: F-003 + F-007 (PRD patches)
- Aria: F-012 ADR-019 (DPA storage schema)
- Eric: F-016 advogado especializado LGPD validation

**Phase 6 (Morpheus consolidação) — ratifica patches:**
- Apresentar findings + remediation a Eric
- Eric decide: patches all OR aceitar como debt explícito (CC.43+)
- Aprovado → PR creation + tag v0.2.0-alpha

**Sprint 04 stories implementation (Phase 7+):**
- HIGH findings (19) → TECH-DEBT.md prioridade alta
- MEDIUM findings (13) → TECH-DEBT.md CC.50+
- LOW findings (2) → polish opcional

### Recomendação a Morpheus

Apresentar a Eric com clareza:
1. Verdict CONCERNS (não FAIL — pivot sound)
2. 4 CRITICAL com remediation paths claros
3. 19 HIGH como debt aceitável Sprint 04
4. Decisão Eric: Phase 5.5 patches OR aceitar debt explícito
5. Após decisão: PR creation + Phase 6 final

**There is no spoon, Mr. Anderson — but there are 38 holes in the bowl. Patch the 4 deepest before you serve.**

— Smith ULTRATHINK mode 🛡️ adversarial cynical
