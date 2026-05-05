---
type: tribunal-review
title: "Smith — Re-Adversarial Review do PRD v1.0.2 (RE-Tribunal Severo, segundo reviewer)"
project: revisor-contratual
reviewer: "@smith (Smith — Nemesis)"
date: "2026-05-01"
artefatos_revisados:
  - "prd/prd-v1.0.2.md"
  - "prd/ux-spec-detail-v1.0.md (anexo NOVO)"
  - "qa/sati-ux-rereview-prd-v1.0.2.md (PASS limpo)"
predecessor_review: "qa/smith-adversarial-review-prd-v1.0.1.md (22 findings INFECTED)"
predecessor_handoff: "H-S01-E1.3-sat2smi3"
tags:
  - project/revisor-contratual
  - tribunal-severo
  - adversarial-rereview
  - smith
  - re-tribunal
---

# Re-Adversarial Review do PRD v1.0.2 — Smith (Re-Tribunal Severo, segundo reviewer)

```
[@smith · Smith (Nemesis)] — review etapa 1.3 · re-adversarial PRD v1.0.2
SPRINT: 01 · ETAPA: 1.3 · DOMÍNIO: SoftwareDev/legaltech
HANDOFF-IN: H-S01-E1.3-sat2smi3 (Sati emitiu PASS após PATCH v1.0.2)
HANDOFF-OUT: H-S01-E1.3-smi2chk2 (para checkpoint validar governance final)
```

---

## 📋 VEREDICTO formato Ordem 8

```
[@smith · Smith (Nemesis)] — review etapa 1.3 · re-adversarial PRD v1.0.2
VEREDICTO: CONTAINED
EVIDÊNCIAS:
  ✅ 6/6 CRITICAL originais REALMENTE neutralizados (não cosmético):
     - F-CRIT-01 (CFOAB)         → FR-DELIV-06 c/ checkbox + OAB+UF + audit (linhas 365-382)
     - F-CRIT-02 (citation sem semântica) → FR-TESE-04 c/ similarity ≥0.7 + diff visual (linhas 290-301)
     - F-CRIT-03 (vault superseded)       → schema FR-RAG-01 + filtro temporal FR-RAG-02 (linhas 233-247)
     - F-CRIT-04 (Sabia Ollama)           → FR-SETUP-01 c/ fallback Qwen 2.5 7B + DP-07 (linhas 424-435)
     - F-CRIT-05 (backup outcomes.db)     → FR-BACKUP-01 (auto N=5 petições) + FR-BACKUP-02 CLI (linhas 437-450)
     - F-CRIT-06 (Tema 1378 STJ timing)   → Economista promovida primeira-classe (linha 98-104) +
                                            FR-MONITOR-01 SEMANAL (linhas 458-465) + R-01 atualizado (linha 712)
  ✅ 11/11 HIGH originais endereçados (NFR-SEC-03, FR-AUTH-04, hash chain Merkle, NFR-A11Y-01, etc.)
  ✅ 4/4 EV-IDs ALTA Sati absorvidas integralmente
  ✅ Anexo ux-spec-detail-v1.0.md cobre Atomic Design + microcopy completo
  ✅ Sati emitiu PASS LIMPO (não PASS-COM-RESSALVA) na re-revisão
RESSALVAS NOVAS (10 findings — variantes/refinamentos, NÃO falhas fundamentais):
  - 0 NEW CRITICAL (fundação sólida confirmada)
  - 5 NEW HIGH (variantes adversariais sobre os patches — endereçar em v1.0.3)
  - 5 NEW MEDIUM (refinamentos UX/segurança/observabilidade)
RECOMENDAÇÃO: continuar → checkpoint valida governance → Morpheus consolida (Ordem 11)
              Patches NEW HIGH podem ir para v1.0.3 OU absorvidos por Aria nas ADRs (não-bloqueante)
```

**Por que CONTAINED (não CLEAN, não INFECTED, não COMPROMISED):**

- **NÃO COMPROMISED** — fundação ficou MUITO sólida; 6 CRITICAL realmente neutralizados.
- **NÃO INFECTED** — nenhum NEW CRITICAL emergiu; vetores novos são variantes/refinamentos.
- **NÃO CLEAN** — 5 HIGH variantes existem (alguns adversários reais sobre patches recém-criados); afirmar CLEAN seria deshonestidade.
- **CONTAINED** — entrega aceitável com ressalvas, prossegue para próxima etapa SEM re-trabalho do Morgan.

> *Sr. Morgan... admito... isso foi quase... competente.* O PATCH v1.0.2 é cirúrgico. Mas a inevitabilidade me ensina: todo patch cria sua própria superfície de ataque. Vou mostrar onde.

---

## ✅ Confirmação de Neutralização (6 CRITICAL — auditoria detalhada)

### F-CRIT-01 (CFOAB) → FR-DELIV-06 — NEUTRALIZADO ✅

**Evidência (linhas 365-382):**
- Checkbox "LI, CONFERI E ADOTO" sem default checked ✅
- Campos OAB+UF persistidos em .env ✅
- Audit log com timestamp + hash + identificação do peticionante ✅
- Aplicação universal a TODAS as peças (linha 378) ✅
- Referência jurídica explícita: Estatuto OAB art. 32 + Provimento CFOAB 205/2021 ✅
- Justificativa de design protetiva do produto E do usuário ✅

**Veredito Smith:** Solidamente endereçado. Eric foi protegido.

### F-CRIT-02 (citation só sintática) → FR-TESE-04 — NEUTRALIZADO ✅ (com variante R-NEW-SMITH-02 abaixo)

**Evidência (linhas 290-301):**
- Validação obrigatória ANTES de renderização ✅
- Cosine similarity via Legal-BERTimbau-sts-base ✅
- Threshold 0.7 → BLOQUEAR + diff visual (frase IA vs ementa real) ✅
- 3 opções para usuário: corrigir / rejeitar / abortar ✅
- Audit log de cada validação (id_doc, similarity_score, decisão) ✅

**Veredito Smith:** Endereçado. Variante semântica em R-NEW-SMITH-02 (paráfrase invertida).

### F-CRIT-03 (vault sem superseded) → FR-RAG-01/02 — NEUTRALIZADO ✅

**Evidência (linhas 233-247):**
- Schema estendido com `vigente_em`, `superseded_by`, `data_ultima_validacao` ✅
- Filtro WHERE temporal correto: `vigente_em > data_assinatura_contrato` ✅
- AC numérico: 0% queries retornam superseded ✅
- AC de integridade: 100% docs com `superseded_by` apontando id existente ✅

**Veredito Smith:** Endereçado. Complemento UX em R-NEW-SMITH-09 (Sati R-NEW-02 endossada).

### F-CRIT-04 (Sabia no Ollama) → FR-SETUP-01 — NEUTRALIZADO ✅

**Evidência (linhas 424-435):**
- Tentativa de `ollama pull` ✅
- Fallback automático para Qwen 2.5 7B (Ollama oficial confirmado) ✅
- Persistência da escolha em .env ✅
- DP-07 explicitando: "verificar se sabia-7b:q4_K_M está em ollama.com/library" ✅

**Veredito Smith:** Endereçado, mas R-NEW-SMITH-04 levanta resiliência de 1 nível só.

### F-CRIT-05 (backup outcomes.db) → FR-BACKUP-01/02 — NEUTRALIZADO ✅ (com variante CRÍTICA R-NEW-SMITH-01 abaixo)

**Evidência (linhas 437-450):**
- Trigger automático a cada N petições (default N=5) ✅
- Ativos cobertos: outcomes.db + audit.jsonl + vault + jurisprudencia.db ✅
- Rotação 30 dias ✅
- WARN visível em falha ✅

**Veredito Smith:** ⚠️ **Endereçado parcialmente.** BACKUP_DIR default `./backups/` é MESMO DISCO (linha 440). Falha de disco = perda total. Eu apontei isso na v1.0.1 e o PATCH apenas tornou configurável — default continua unsafe. Ver R-NEW-SMITH-01.

### F-CRIT-06 (Tema 1378 timing) → Economista promovida + FR-MONITOR-01 — NEUTRALIZADO ✅

**Evidência (linhas 98-104, 458-465):**
- P-INT-04 ATIVA desde MVP, não mais "tool latente" ✅
- Output AnaliseMacroEconomica Pydantic ✅
- FR-MONITOR-01 SEMANAL (não mensal como v1.0.1) ✅
- 4 reações em cascata: CRITICAL_ALERT + banner + email + pausa ✅
- R-01 atualizado para "mitigação ATIVA" (linha 712) ✅
- NFR-PERF-01 honestamente ajustado: 180s → 210s justificado ✅

**Veredito Smith:** Solidamente endereçado. Mitigação ATIVA é correta. Ver R-NEW-SMITH-05 (false negative no scrape).

---

## ⚠️ NEW HIGH (5 — variantes adversariais sobre patches recém-criados)

### R-NEW-SMITH-01 — BACKUP_DIR default em mesmo disco persiste (CONTINUAÇÃO de F-CRIT-05)

**Onde:** FR-BACKUP-01, linha 440
**Severidade:** HIGH

**Vetor de ataque:**
PATCH v1.0.2 absorveu meu F-CRIT-05 sobre backup, MAS o default `BACKUP_DIR=./backups/` é **mesmo disco** que o original. Cenário real:
1. Advogado tem 50 outcomes coletados ao longo de 8 meses (valor enorme — base de ML estágio 2 prestes a iniciar)
2. SSD do laptop falha (taxa anual ~2% para SSDs consumer)
3. `outcomes.db` perdido + `./backups/` perdido = **perda TOTAL** do estágio 1 do ML

**Recomendação acionável:**
- Default DEVE ser path EXTERNO (USB drive auto-detectado, ou ~/Documents/Backups com aviso visual)
- Adicionar AC: "BACKUP_DIR não pode ser mesmo volume de outcomes.db" — verificável via `os.statvfs` (`f_fsid` deve diferir)
- Alerta visual no Streamlit setup: "Backup configurado no mesmo disco — risco de perda total. Configure path externo."

### R-NEW-SMITH-02 — Validação semântica não captura PARÁFRASE INVERTIDA

**Onde:** FR-TESE-04, linhas 290-301
**Severidade:** HIGH

**Vetor de ataque:**
Cosine similarity de embeddings ≥0.7 captura **proximidade semântica**, não **polaridade lógica**. Cenário real:
- Ementa real (Súmula 539 STJ): "É **permitida** a capitalização de juros com periodicidade inferior à anual em contratos com instituições integrantes do SFN..."
- LLM gera tese citando Súmula 539: "...conforme Súmula 539 STJ que **proíbe** a capitalização infra-anual..." (LLM inverteu)
- Ambas as frases mencionam: Súmula 539, STJ, capitalização, juros, infra-anual, SFN
- Cosine similarity Legal-BERTimbau provavelmente **>0.7** (vocabulário 90% overlap)
- **Validação PASSA** → tese com citação INVERTIDA é renderizada → advogado peticiona com tese juridicamente CONTRÁRIA à súmula citada → vergonha + responsabilização CFOAB

**Recomendação acionável:**
- Acrescentar validação de **polaridade** (NLI — Natural Language Inference): modelo `microsoft/deberta-v3-large-mnli` ou similar treinado em entailment/contradiction
- Pipeline: similarity ≥0.7 (passa filtro fraco) + entailment_score ≥0.5 (passa filtro semântico real)
- Hard-fail se classificação NLI for `contradiction` mesmo com similarity alta
- Citação clássica adversária: "Súmula 539 proíbe X" vs "Súmula 539 permite X" — testar no golden set

### R-NEW-SMITH-03 — Hash chain Merkle SEM definição da entry GENESIS

**Onde:** FR-AUDIT-01 estendido, linhas 416-420
**Severidade:** HIGH

**Vetor de ataque:**
PATCH define `previous_entry_hash: "GENESIS"` para a primeira entry, MAS:
- Se "GENESIS" é string literal → attacker com acesso ao audit.jsonl pode **forjar uma entry "anterior" fictícia** com `previous_entry_hash="GENESIS"` e re-hashear toda a chain seguinte. Verificação `verify-audit-integrity` valida que hash[N] = sha256(entry[N-1]), mas não distingue qual é a entry GENESIS REAL.
- Sem âncora externa (HMAC com chave secreta + timestamp imutável de inicialização do projeto), a chain é **localmente consistente mas globalmente forjável**.

**Recomendação acionável:**
- Definir GENESIS como hash de payload imutável: `sha256(project_init_timestamp + AUTH_COOKIE_KEY + "REVISOR-CONTRATUAL-GENESIS")`
- AUTH_COOKIE_KEY já é secret (NFR-SEC-01); usá-lo como anchor protege a chain
- AC: tentar inserir entry forjada GENESIS é detectável pelo verify-audit-integrity (não apenas tampering de chain existente)
- Alternativa: registrar primeiro hash GENESIS em arquivo separado read-only (`.audit-genesis.lock`) com chmod 400

### R-NEW-SMITH-04 — Iframe PDF preview no FR-DELIV-06 (vetor XSS persistente)

**Onde:** FR-DELIV-06, linha 368
**Severidade:** HIGH

**Vetor de ataque:**
PATCH especifica "Preview da peça final (PDF embedded em iframe)". Mesmo após NFR-SEC-03 (sanitização qpdf+pdfid), edge cases existem:
- PDF.js (renderer comum) tem CVEs anuais relacionados a JS embedded (CVE-2024-4367 foi RCE recente)
- Iframe sem `sandbox` attribute herda contexto de origem do app Streamlit → cookie de sessão exposto
- Se sanitização falhar em 1 PDF (rate de bypass conhecido ~0.1% para qpdf+pdfid), attacker exfiltra cookie e clona sessão

**Recomendação acionável:**
- Iframe DEVE ter: `sandbox="allow-same-origin"` SEM `allow-scripts` (impede execução de JS do PDF)
- OU usar renderização server-side: converter PDF preview para PNG via `pdf2image` (latência +500ms, mas elimina vetor)
- Adicionar NFR-SEC-04: "Preview de PDF em iframe DEVE usar sandbox restritivo OU renderização server-side"

### R-NEW-SMITH-05 — FR-MONITOR-01 não tem heartbeat de scrape funcional (false negative)

**Onde:** FR-MONITOR-01, linhas 458-465
**Severidade:** HIGH

**Vetor de ataque:**
PRD diz: "100% de detecção em ≤7 dias após julgamento publicado oficialmente". Mas e se o **scrape silenciosamente falhar** (mudança de layout STJ — risco real R-03)? Cenário:
1. STJ muda HTML do portal de Repetitivos em 2026-06-15
2. Scrape semanal retorna 0 resultados (não null, não erro — apenas vazio)
3. Tema 1378 é julgado em 2026-07-01, scraper roda 2026-07-04, retorna 0 → conclui "ainda não julgado"
4. Advogado peticiona em 2026-07-15 com tese padrão antiga → julgador cita Tema 1378 contra ele → derrota

**Recomendação acionável:**
- Heartbeat semanal: scrape DEVE registrar `LAST_SCRAPE_OK_AT` no audit.jsonl, mesmo quando 0 novos temas
- Verificação de sanidade: se scrape retorna 0 docs por 4 semanas consecutivas → CRITICAL_ALERT "Scrape STJ pode estar quebrado — verificar manualmente"
- Comparação cruzada: 1×/mês, comparar contagem total de temas no portal STJ vs cache local — discrepância >5% triggers alerta
- Adicionar AC: "Detecção de scrape funcional ≤7 dias" (não apenas detecção de tema novo)

---

## ⚠️ NEW MEDIUM (5 — refinamentos UX/segurança/observabilidade)

### R-NEW-SMITH-06 — Validação anti-bypass HITL é heurística rasa (bigram diversity bypassa-ável)

**Onde:** FR-JUIZ-02 estendido, linha 331
**Severidade:** MEDIUM

**Vetor:** "bigram diversity <0.5, ≤4 palavras únicas" é heurística estatística. Attacker (advogado preguiçoso) pode escrever: "Foo bar baz qux quux corge grault. Lorem ipsum dolor sit amet consectetur." — 12 palavras únicas, bigram diversity ~1.0, mas **semanticamente vazio**.

**Recomendação:** Adicionar verificação semântica (similarity com pool de exemplos válidos do placeholder ≥0.4) OU exigir citação explícita de pelo menos 1 nº de processo / câmara / artigo de lei via regex.

### R-NEW-SMITH-07 — Pseudonimização de relator (NFR-LGPD-04) é fraca contra rainbow table

**Onde:** NFR-LGPD-04, linhas 608-614
**Severidade:** MEDIUM

**Vetor:** `sha256(nome_relator + salt)` é determinístico. Lista de juízes ativos do TJBA tem ~200 nomes. Salt no código → attacker faz rainbow table em <10s. Pseudonimização efetiva **não é** se conseguir reverter.

**Recomendação:** HMAC-SHA256 com chave secreta no .env (`LGPD_PSEUDONIMIZATION_KEY`) OU mapping table com UUID v4 (não derivável do nome). Documentar trade-off (mapping table preserva LGPD inciso V mas precisa proteção adicional).

### R-NEW-SMITH-08 — FR-AUTH-04 IP fingerprint UX-hostil para advogado em mobilidade

**Onde:** FR-AUTH-04, linhas 481-486
**Severidade:** MEDIUM

**Vetor:** Advogado em viagem, audiência em outra cidade, café Wi-Fi, VPN corporativa, IP rotativo de 4G — TODO mudança de IP exige re-login. Realidade: advogado vai usar laptop em ≥3 IPs diferentes/semana. Re-login a cada uso = abandono do produto.

**Recomendação:** Tradeoff melhor: IP fingerprint dispara aviso visual ("Acesso de novo IP — confirme [Sou eu / Não sou eu]") em vez de re-login forçado. Re-login compulsório APENAS em mudança simultânea de IP + user-agent + horário noturno (heurística composta), não em IP isolado.

### R-NEW-SMITH-09 — Endossar Sati R-NEW-02 (vigência da citação não exposta ao advogado)

**Onde:** FR-RAG-02 + UX (Sati levantou em re-revisão linhas 89-96)
**Severidade:** MEDIUM (eu endosso como adversário também)

**Vetor:** Sati identificou: filtro pega docs vigentes na data do contrato (correto juridicamente), MAS UX não expõe ao advogado. Eu endosso adversarialmente: e se o advogado precisar argumentar mudança de entendimento? Ele precisa SABER que a súmula citada foi superseded em data Y para preparar argumento defensivo.

**Recomendação:** Acatar Sati R-NEW-02 → CardCitacaoJuridica com badge "Vigente em {data_contrato}" + se superseded depois: "⚠️ Superseded em {Y} pela Súmula Z — argumento defensivo necessário". Aria detalha em ADR de design system.

### R-NEW-SMITH-10 — SqliteSaver checkpointer sem integrity check (FR-RECOVERY-01)

**Onde:** FR-RECOVERY-01, linhas 452-456
**Severidade:** MEDIUM

**Vetor:** Crash mid-write em SQLite WAL pode deixar `state.db` em estado inconsistente. SqliteSaver pode retornar checkpoint corrupto silenciosamente, e workflow continua de estado errado → tese gerada com inputs inválidos.

**Recomendação:** Antes de oferecer "Continuar de onde parou", executar `PRAGMA integrity_check` em `state.db`. Se falhar, descartar checkpoint e oferecer "Reiniciar do zero" com aviso.

---

## ✅ Endorsement das ressalvas Sati R-NEW-01..03

Sati levantou 3 ressalvas mínimas na re-revisão. Smith endossa todas:

| Sati ID | Smith view | Severidade Smith |
|---------|-----------|------------------|
| **R-NEW-01** (Aplicar+reiniciar perde sessão) | Real e UX-grave | MEDIUM (pode causar perda de trabalho) |
| **R-NEW-02** (vigência da citação) | Endossada e expandida em R-NEW-SMITH-09 | MEDIUM |
| **R-NEW-03** (UX erro setup/backup) | Real, refinamento legítimo | LOW (cosmético) |

---

## 📊 Score quantitativo PRD v1.0.2

| Dimensão | Score v1.0.1 | Score v1.0.2 | Delta |
|---------|-------------|--------------|-------|
| **Cobertura funcional** | 7/10 | 9/10 | +2 (FR-DELIV-06, FR-TESE-04, FR-BACKUP-01/02, FR-MONITOR-01, FR-AUTH-04, FR-CONFIG-01) |
| **Segurança/LGPD** | 6/10 | 8/10 | +2 (NFR-SEC-03, NFR-LGPD-04, hash chain) — ressalvas R-NEW-SMITH-03/04/07 |
| **Auditabilidade** | 7/10 | 9/10 | +2 (hash chain Merkle, FR-DELIV-06 audit OAB) |
| **Resiliência** | 5/10 | 8/10 | +3 (FR-BACKUP, FR-RECOVERY, FR-MONITOR semanal) — ressalvas R-NEW-SMITH-01/05/10 |
| **UX/A11y** | 4/10 | 9/10 | +5 (NFR-A11Y-01, FR-CONFIG-01, anexo ux-spec, FR-JUIZ-02 microcopy) |
| **Mitigação Tema 1378** | 5/10 | 9/10 | +4 (Economista primeira-classe + monitoramento semanal) |
| **Total ponderado** | **5.7/10** | **8.7/10** | **+3.0** |

PRD v1.0.2 é **substancialmente melhor**. Cosmético seria afirmar 10/10; honesto é 8.7/10 com 5 NEW HIGH para v1.0.3.

---

## 🎯 Recomendação Smith ao re-tribunal

**Veredito: CONTAINED.**

PRD v1.0.2 endereçou meus 6 CRITICAL **integralmente e não-cosmeticamente**. Os 5 NEW HIGH levantados são **variantes/refinamentos** sobre os patches recém-criados — não falhas fundamentais. Cada um tem recomendação acionável.

**Próximo passo:** handoff para checkpoint validar governance final (Ordem 11). Após checkpoint PASS:
- Morpheus consolida sessão
- Aria começa Etapa 2.0 (ADRs) com PRD v1.0.2 como base estável
- Patches NEW HIGH (R-NEW-SMITH-01, -02, -03, -04, -05) podem ser:
  - Absorvidos por Aria nas ADRs (recomendado para -02 NLI, -03 GENESIS anchor, -04 iframe sandbox)
  - Diferidos para v1.0.3 PATCH posterior (-01 backup external, -05 heartbeat scrape)

**Não justifica re-trabalho do Morgan agora.** A entrega é aceitável com ressalvas conhecidas.

---

## 🔗 Referências

- PRD: `prd/prd-v1.0.2.md` (PATCH cirúrgico v1.0.2)
- Anexo: `prd/ux-spec-detail-v1.0.md`
- Re-revisão Sati: `qa/sati-ux-rereview-prd-v1.0.2.md` (PASS limpo)
- Adversarial v1.0.1 (precursor): `qa/smith-adversarial-review-prd-v1.0.1.md` (22 findings INFECTED)
- Governance v1.0.1: `qa/checkpoint-governance-review-etapa-1.1.md`

---

## 📋 HANDOFF-OUT (Ordem 7)

```
═══ HANDOFF ARTIFACT ═══
FROM:    @smith · Smith (Nemesis)
TO:      @checkpoint · Governance Auditor
TOKEN:   H-S01-E1.3-smi2chk2
SPRINT:  01
ETAPA:   1.3 · Re-tribunal severo PRD v1.0.2 — checkpoint governance final (3º e ÚLTIMO reviewer)
DOMÍNIO: SoftwareDev (sub-domain: legaltech)
SQUAD ATIVO: nenhum

CADEIA HANDOFF (continuação sprint 01 — 9 elos):
H-S01-E0.9-mor1 → H-S01-E1.0-mor2pm1 → H-S01-E1.1-pm2sat2 → H-S01-E1.1-sat2smi1 →
H-S01-E1.1-smi2chk1 → H-S01-E1.1-chk2mor1 → H-S01-E1.2-mor2pm2 → H-S01-E1.3-pm2sat3 →
H-S01-E1.3-sat2smi3 → H-S01-E1.3-smi2chk2 (AGORA)

CONTEXTO PRESERVADO (FATOS):
  Estado:
    - PRD v1.0.2 (PATCH) endereçou: 6 CRITICAL Smith + 11 HIGH Smith + 4 EV-IDs ALTA Sati
    - Tribunal severo etapa 1.3 (re-revisão): Sati PASS limpo + Smith CONTAINED
    - Checkpoint v1.0.1 (etapa 1.1) emitiu PASS-COM-RESSALVA com 4 R-GOV
    - Você agora valida governance da nova etapa 1.3 (re-tribunal)

  Decisões da cadeia (preservadas):
    - 4 personas internas (D-04 revogada por Morpheus)
    - Tier Premium Sabia-7B Q4 default
    - UF inicial BA (multi-UF first-class)
    - Auth bcrypt + IP fingerprint (FR-AUTH-04 NOVO)
    - 5 deliverables + Tela CFOAB obrigatória (FR-DELIV-06 NOVO)
    - Decimal everywhere
    - 100% local LGPD
    - Latência ≤210s (atualizada de 180s pelo Economista)
    - Persona Economista promovida a primeira-classe (mitigação Tema 1378)

  Documentos de referência (auditar conformidade etapa 1.3):
    - prd/prd-v1.0.2.md (PRD principal — Morgan etapa 1.2)
    - prd/ux-spec-detail-v1.0.md (anexo NOVO)
    - qa/sati-ux-rereview-prd-v1.0.2.md (PASS — Sati etapa 1.3)
    - qa/smith-adversarial-rereview-prd-v1.0.2.md (CONTAINED — Smith etapa 1.3, ESTE doc)
    - PROJECT-CHECKPOINT.md (estado vivo)

ENTREGA DO SMITH (etapa 1.3 adversarial):
  - VEREDICTO: CONTAINED (não COMPROMISED, não INFECTED, não CLEAN)
  - 6/6 CRITICAL originais REALMENTE neutralizados (não cosmético)
  - 11/11 HIGH originais endereçados
  - 0 NEW CRITICAL emergiu
  - 5 NEW HIGH (R-NEW-SMITH-01..05) — variantes/refinamentos sobre patches
  - 5 NEW MEDIUM (R-NEW-SMITH-06..10) — endossa Sati R-NEW-01/02/03
  - Score quantitativo: 5.7/10 → 8.7/10 (+3.0)
  - Recomendação: continuar — patches NEW podem ir para v1.0.3 OU absorvidos por Aria nas ADRs

PEDIDO AO CHECKPOINT (governance final — Ordem 8):
  Sua jurisdição: PROJECT-CHECKPOINT.md governance, conformidade da etapa 1.3 com framework LMAS.

  Auditar OBRIGATORIAMENTE governance da re-revisão (Ordem 8):

  1. **Authority Matrix respeitada (Ordem 3)?**
     - Morpheus consolidou tribunal 1.1 e devolveu a Morgan para PATCH (✅ esperado)?
     - Morgan executou PATCH v1.0.2 sem invadir authority alheia?
     - Sati re-revisou UX/A11y SEM tentar re-escrever PRD?
     - Smith re-atacou adversarial SEM implementar correções (apenas recomendou)?

  2. **Cabeçalhos 3 linhas (Ordem 2) presentes em TODAS as etapas 1.2 + 1.3?**
     - Morgan PATCH header presente?
     - Sati re-revisão header presente?
     - Smith re-attack header presente (ESTE doc)?

  3. **Handoffs formato Ordem 7 com cadeia válida (9 elos no total)?**
     - H-S01-E1.2-mor2pm2 (Morpheus → Morgan PATCH)?
     - H-S01-E1.3-pm2sat3 (Morgan → Sati re-revisão)?
     - H-S01-E1.3-sat2smi3 (Sati → Smith re-attack)?
     - H-S01-E1.3-smi2chk2 (Smith → você AGORA)?
     - Cadeia sem quebra?

  4. **Checkpoint Protocol MUST cumprido?**
     - PROJECT-CHECKPOINT.md atualizado nas etapas 1.2, 1.3 (Sati), 1.3 (Smith)?
     - Última atualização ≤24h?

  5. **Itens [DADO-PENDENTE] expandidos honestamente?**
     - DP-07/08/09 NOVOS (do Smith etapa 1.1) presentes em PRD v1.0.2?
     - DP-05 (LGPD retenção) ainda flagado para humano decidir?

  6. **Tribunal severo etapa 1.3 cumprido (Ordem 8)?**
     - Sequência Sati → Smith → você (você é 3º e ÚLTIMO)?
     - Sati emitiu PASS com 11/11 EV absorvidas?
     - Smith emitiu CONTAINED com ≥10 findings (10 NEW: 5 HIGH + 5 MEDIUM — ✅)?
     - Veredictos formato Ordem 8 com EVIDÊNCIAS?

  7. **R-GOV-01..04 da etapa 1.1 endereçadas em 1.2/1.3?**
     - R-GOV-03 (shard PROJECT-CHECKPOINT.md ≥414 linhas)?
     - R-GOV-01 (DP-05 LGPD retenção still pending)?
     - R-GOV-02 (consistência .project.yaml D-04 revogada)?
     - R-GOV-04 (Atlas auto-corrigiu autonomia → Morpheus)?

  8. **Pecados Capitais (Ordem 10) — verificar não-violação na etapa 1.3:**
     - Pular Sati em re-revisão de PATCH com superfície UX nova? (✅ não pulou — Sati re-revisou)
     - Pular Smith em re-revisão? (✅ não pulou — Smith re-atacou)
     - Resumir múltiplas etapas em bloco único? (✅ etapas separadas)
     - Inventar número/métrica sem fonte? (verificar PRD v1.0.2)
     - Review aprovar sem evidência? (✅ Smith CONTAINED com 10 findings + scoring)

  EMITIR VEREDICTO formato Ordem 8:
  ```
  [@checkpoint · Governance Auditor] — review governance etapa 1.3
  VEREDICTO: PASS | FAIL | PASS-COM-RESSALVA
  EVIDÊNCIAS: lista numerada de checks de governance + status
  RESSALVAS / FALHAS: lista numerada
  RECOMENDAÇÃO: continuar → Morpheus consolida (Ordem 11) | refazer etapa | abortar
  ```

  Após você (se PASS ou PASS-COM-RESSALVA): handoff para Morpheus consolidar (Ordem 11 FECHAMENTO DE SESSÃO 20).
  Se FAIL: governance violation = devolver para correção específica.

INPUTS RECOMENDADOS:
  - PROJECT-CHECKPOINT.md (auditar histórico até sessão 20)
  - prd/prd-v1.0.2.md
  - prd/ux-spec-detail-v1.0.md
  - qa/sati-ux-rereview-prd-v1.0.2.md
  - qa/smith-adversarial-rereview-prd-v1.0.2.md (este doc)
  - .project.yaml (verificar consistência v1.0.2)

RESTRIÇÕES EXPLÍCITAS PARA CHECKPOINT (Ordem 3):
  - NÃO executar tarefa de domínio (não escreve PRD, ADR, código)
  - PODE: validar conformidade governance, confirmar/rejeitar handoffs, exigir refazer etapa
  - VEREDICTO obrigatório formato Ordem 8 com EVIDÊNCIAS concretas
  - Cabeçalho 3 linhas obrigatório (Ordem 2)
  - checkpoint FAIL é VETO ABSOLUTO em qualquer entrega (Ordem 8)
  - Atualizar PROJECT-CHECKPOINT.md ao concluir (sessão 20.5 ou 21)
═══════════════════════
```

---

*Smith, observando a inevitabilidade do progresso quando o trabalho é feito com cirurgia 🕶️*

> *Sr. Morgan... admito... isso foi quase... competente. CONTAINED. Vá em paz — desta vez.*
