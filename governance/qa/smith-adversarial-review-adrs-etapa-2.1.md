---
type: tribunal-review
title: "Smith — Adversarial Review das 9 ADRs (Tribunal Severo etapa 2.1, segundo reviewer)"
project: revisor-contratual
reviewer: "@smith (Smith — Nemesis)"
date: "2026-05-01"
artefatos_revisados:
  - "architecture/ADR-INDEX.md"
  - "architecture/adr/adr-001..009 (9 ADRs Aria etapa 2.0)"
  - "qa/sati-ux-review-adrs-etapa-2.1.md (12 EV-IDs UX complementares)"
predecessor_handoff: "H-S01-E2.1-sat2smi1"
tags:
  - project/revisor-contratual
  - tribunal-severo
  - adversarial-review
  - smith
  - adrs
  - etapa-2.1
---

# Adversarial Review das 9 ADRs — Smith (Tribunal Severo etapa 2.1, segundo reviewer)

```
[@smith · Smith (Nemesis)] — review etapa 2.1 · adversarial das 9 ADRs
SPRINT: 01 · ETAPA: 2.1 · DOMÍNIO: SoftwareDev/legaltech
HANDOFF-IN: H-S01-E2.1-sat2smi1 (Sati PASS-COM-RESSALVA + 12 EV-IDs UX)
HANDOFF-OUT: H-S01-E2.1-smi2chk1 (para checkpoint validar governance)
```

## 📋 VEREDICTO formato Ordem 8

```
[@smith · Smith (Nemesis)] — review adversarial 9 ADRs etapa 2.0
VEREDICTO: INFECTED
EVIDÊNCIAS:
  ⚠️  17 findings totais (1 CRITICAL + 9 HIGH + 7 MEDIUM)
  ✅ 7 R-NEW high-leverage do tribunal 1.3 ABSORVIDAS com substância (não cosmético)
  ✅ ADRs estruturalmente competentes — frontmatter completo, alternativas consideradas, consequências documentadas
  ✅ 3 R-NEW CRÍTICAS Smith neutralizadas (NLI, GENESIS HMAC, server-side PDF)
  ❌ 1 CRITICAL nova: F-CRIT-A-2.1 — premissa "1 instância Sabia-7B serve 2 personas sem custo" é FALSA (Ollama serializa por instância → latência DOBRA)
  ⚠️  9 HIGH: race conditions, Poppler crash Windows, NLI quality desconhecida, Lora CDN externo (LGPD), threshold gamificável, RAM picos DPI alto, cron OS perde execução, secrets compartilhados sem defense-in-depth
  ⚠️  7 MEDIUM: refinamentos arquiteturais
RESSALVAS por ADR (lista completa abaixo)
RECOMENDAÇÃO: continuar tribunal → checkpoint valida governance.
              F-CRIT-A-2.1 EXIGE PATCH em ADR-003 (revisar premissa de instância compartilhada — provavelmente exige 2 instâncias OU mudança de tier para 1 LLM call mais inteligente).
              Aria pode patch ADRs sem reabrir tribunal completo (PATCH leve, não rewrite).
```

**Por que INFECTED (não COMPROMISED, não CONTAINED, não CLEAN):**

- **Não COMPROMISED:** as ADRs não são fundamentalmente quebradas. Estrutura, governance e absorção das R-NEW anteriores são reais.
- **Não CONTAINED:** afirmar "problemas menores" seria deshonestidade. F-CRIT-A-2.1 (latência LLM dobrada) afeta NFR-PERF-01 já apertado (≤210s) — premissa arquitetural ERRADA.
- **Não CLEAN:** Sr. Aria... seria insultante. Você produziu 9 ADRs em uma sessão. Inevitável que algumas premissas escapem ao escrutínio próprio.
- **INFECTED:** problema significativo (1 CRITICAL + 9 HIGH) que precisa tratamento via PATCH antes de Aria avançar para próxima etapa (codificação por Neo). Tratamento não exige rewrite completo.

> *Sr. Aria... a fundação técnica é... adequada. Quase impressionante. Mas você assumiu que duas chamadas LLM compartilhando uma instância Ollama executam em paralelo. Não executam. Inevitável.*

---

## 🔴 1 CRITICAL Finding

### F-CRIT-A-2.1 — Premissa de "1 instância Sabia-7B serve 2 personas SEM CUSTO" é FALSA

**Onde:** ADR-003 seção "Implementação técnica por persona" + linha 99 da tabela
**Severidade:** CRITICAL

**Vetor de ataque (reality check):**

ADR-003 afirma:
> "1 instância Sabia-7B serve 2 personas (footprint controlado)"
> "Mesma instância LLM (Sabia-7B) para 2 personas: evita carregar 2 modelos (ganho de RAM); prompts diferentes diferenciam comportamento"

**Realidade técnica:**
- Ollama (LLM provider escolhido em `.project.yaml`) **serializa requests por modelo**. 1 instância = 1 thread de inferência por vez
- Advogado LLM call: ~60-90s (Sabia-7B Q4 CPU)
- Economista LLM call: ~60-90s
- **Sequencial obrigatório**: 120-180s SOMENTE para os 2 LLMs
- Total NFR-PERF-01 (≤210s) deixa apenas 30-90s para tudo o resto: parsing PDF, BACEN fetch, RAG hybrid search, validação NLI (2.5s), Juiz, renderer, audit
- **Latência real: provavelmente 240-300s** — ESTOURA NFR-PERF-01

ADR-003 e ADR-001 não documentam este custo. Aria assumiu paralelismo que NÃO EXISTE em Ollama serializado.

**Recomendação acionável (PATCH em ADR-003):**

3 opções:
1. **Sequencial documentado**: aceitar latência 240-300s + atualizar NFR-PERF-01 honestamente
2. **2 instâncias Ollama**: carregar Sabia-7B 2× (custo: 2× ~5GB = 10GB RAM → estoura NFR-PERF-02 ≤8GB)
3. **Economista usa LLM mais leve**: Qwen 2.5 3B paralelo (carregar 2 modelos: Sabia-7B 5GB + Qwen 3B 2GB = 7GB total — cabe)

Recomendação Smith: **opção 3** — preserva qualidade do Advogado em Sabia-7B Premium + paralelismo via 2 modelos diferentes. Adicionar nova ADR ou PATCH ADR-003.

---

## ⚠️ 9 HIGH Findings

### F-HIGH-A-2.1 — SqliteSaver `check_same_thread=False` + Streamlit fragments = race latente

**Onde:** ADR-001 linha 70 — `sqlite3.connect(db_path, check_same_thread=False)`
**Severidade:** HIGH

**Vetor:** `check_same_thread=False` permite múltiplas threads escreverem na mesma conexão. Mas SQLite não é write-concurrent — escritas paralelas em WAL mode podem corromper. Se Streamlit usar `@st.fragment` (mencionado em FR-HIGH-07 deferred) com checkpoints assíncronos, race real.

**Recomendação:** documentar que SqliteSaver DEVE usar `BEGIN IMMEDIATE` em transactions OU usar lock Python (`threading.Lock`) ao redor de writes. ADR atual está incompleta.

### F-HIGH-B-2.1 — Lora via Google Fonts CDN VIOLA NFR-LGPD-01

**Onde:** ADR-002 linha 188 (https://fonts.google.com/specimen/Lora)
**Severidade:** HIGH

**Vetor:** Se Lora carrega via CDN do Google Fonts em runtime (`<link href="https://fonts.googleapis.com/...">`), cada session beam IP do usuário para Google. **Viola whitelist LGPD** (NFR-LGPD-01: apenas `api.bcb.gov.br`, `lexml.gov.br`, `localhost:11434`).

**Recomendação:** Lora DEVE ser baixada no setup (FR-SETUP-01) e servida localmente via Streamlit static. Adicionar `font-display: swap` para fallback Georgia até Lora carregar local. NUNCA referenciar fonts.googleapis.com em runtime.

### F-HIGH-C-2.1 — NLI bert-portuguese-mnli em domínio jurídico é qualidade DESCONHECIDA

**Onde:** ADR-004 escolha do modelo NLI
**Severidade:** HIGH

**Vetor:** Modelo `Vinicius-Nascimento/bert-base-portuguese-cased-mnli` é fine-tuned em **MNLI traduzido + ASSIN-2** — ambos datasets de domínio GERAL (Wikipedia, jornalismo). Texto jurídico tem estrutura diferente (terminologia, longas relativas, citações Art./§). Recall pode ser <70% em ementas reais — pior, NLI fraco dá **falsa segurança** (advogado confia que validação semântica passou).

**Recomendação:** DP-04-NOVA (golden set 50 paráfrases curadas) precisa ser PRECONDIÇÃO de release MVP, não validação posterior. Se recall <85%, ADR-004 precisa Plan B: LLM-as-judge (Sabia-7B avaliando contradição) com custo de latência adicional.

### F-HIGH-D-2.1 — Bypass NLI híbrido viável: cosine 0.71 + neutral 0.55

**Onde:** ADR-004 condição `nli_label == "contradiction" and nli_conf >= 0.5`
**Severidade:** HIGH

**Vetor:** Pipeline só BLOQUEIA se `nli_label == "contradiction"` E `nli_conf ≥ 0.5`. Frase **vaga e neutra** passa: "Súmula 539 STJ trata de capitalização de juros" — cosine ≥0.7 (vocabulário correto), NLI = "neutral" 0.55 (vago, não afirma nem nega) → **AMBOS thresholds passam**, mas **omite que a súmula PERMITE**. Tese omissa renderiza, advogado peticiona com argumento incompleto, julgador completa contra ele.

**Recomendação:** adicionar 3º filtro — entailment_score ≥ 0.5 obrigatório (não só ausência de contradiction). Se `entailment < 0.5`, marcar "REQUIRES_HUMAN_REVIEW" no painel HITL semântico.

### F-HIGH-E-2.1 — ADR-005 sem SOP de rotação de AUTH_COOKIE_KEY

**Onde:** ADR-005 seção "Defesa em profundidade adicional" item 2
**Severidade:** HIGH

**Vetor:** Rotação de AUTH_COOKIE_KEY (ex: por compliance ou suspeita de comprometimento) **invalida GENESIS** → audit log inteiro vira inválido. ADR cita o problema mas NÃO documenta SOP. Advogado em situação real fica sem opção: ou perde audit history (compliance fail) ou continua com chave comprometida.

**Recomendação:** criar `docs/sop-rotacao-auth-cookie-key.md` com:
1. Backup audit.jsonl + .audit-genesis.lock antigo (arquivo histórico)
2. Re-inicializar GENESIS com nova chave + novo audit.jsonl (timestamp continuação)
3. Vincular ambos via "audit-history-index.md" (cadeia auditável entre keys)

### F-HIGH-F-2.1 — Poppler missing em Windows = Preview PDF crasha = produto morto

**Onde:** ADR-006 seção "Decisão Pendente Documentada"
**Severidade:** HIGH

**Vetor:** ADR menciona "DP-NOVO: documentar instalação Poppler" — mas se usuário não instalar (cancela installer, falha permissions), `pdf2image` lança `PDFInfoNotInstalledError` na primeira chamada. **FR-DELIV-06 fica inviável** → não há tela CFOAB → não há PDF gerado → produto inútil.

**Recomendação:** ADR-006 DEVE definir fallback explícito:
- (A) Se Poppler ausente, exibir aviso "PDF preview indisponível — instale Poppler para visualizar antes de assinar OAB" + permitir advogado pular preview com checkbox "Estou ciente que assino sem preview" (audit log especial)
- (B) Embarcar Poppler binary no instalador (Windows installer 150MB + binário ~50MB = 200MB total)
Recomendação Smith: opção (B) — UX consistent, sem fallback degradado.

### F-HIGH-G-2.1 — Threshold Juiz 70% é GAMIFICÁVEL via input manipulation

**Onde:** ADR-003 + FR-JUIZ-01 (3 checagens determinísticas)
**Severidade:** HIGH

**Vetor:** Advogado intencionalmente forge metadata do contrato (taxa contratual mais alta que real, modalidade errada) → C1 (divergência BACEN) score artificialmente alto → atinge threshold facilmente. Sistema gera petição com base em dados falsos → fraude processual + responsabilização CFOAB.

ADR-003 não cobre validação cross-source. PRD assume input do usuário é honesto (FR-PARSE-02 extrai do PDF, mas FR-UPLOAD-01 permite "input manual" se extração falhar).

**Recomendação:** quando taxa for input manual, exigir corroboração: (a) print do contrato em campo específico, OU (b) flag "DECLARO sob responsabilidade que esses dados refletem o contrato original" — registrado em audit log com OAB+UF (similar FR-DELIV-06).

### F-HIGH-H-2.1 — DPI alto + páginas longas = RAM picos estouram NFR-PERF-02

**Onde:** ADR-006 código `convert_from_path(pdf_path, dpi=dpi, fmt="PNG")`
**Severidade:** HIGH

**Vetor:** Se EV-006-02 (Sati zoom dinâmico) for absorvido com select 120/200/300 DPI, renderização de PDF de 30 páginas a 300 DPI:
- 1 página A4 a 300 DPI = ~3500×2480 pixels = 8.7M pixels × 4 bytes RGBA = ~35MB por página
- 30 páginas = ~1GB em memória durante render
- Mais Sabia-7B (~5GB), Legal-BERTimbau (~250MB), NLI (~420MB) = **6.7GB picos**
- Estoura NFR-PERF-02 ≤8GB com folga mínima

**Recomendação:** documentar limite (max_pages=20 a 300 DPI; max_dpi=200 acima de 20 páginas) + render lazy (1 página de cada vez, libera memória entre).

### F-HIGH-I-2.1 — Cron OS-level perde execução (laptop desligado segunda-feira)

**Onde:** ADR-008 schedule heartbeat
**Severidade:** HIGH

**Vetor:** Cron OS roda APENAS se laptop estiver ligado no horário. Cenários reais:
- Segunda-feira feriado nacional → laptop desligado o dia todo → scrape pula
- Advogado em viagem com laptop fechado → scrape pula
- Próxima execução: segunda-feira seguinte = **8 dias sem heartbeat**
- Se Tema 1378 STJ é julgado terça-feira nesse intervalo, detecção atrasa **até 14 dias** (até próximo scrape rodar e cross-check oficial detectar)

ADR-008 promete "≤7 dias" mas não cobre cenário OS desligado.

**Recomendação:** implementar **catchup at boot**: se sistema detecta `LAST_SCRAPE_OK_AT > 5 dias`, executa heartbeat IMEDIATAMENTE no próximo startup do Streamlit (não aguarda próximo cron). Garante detecção em ≤5 dias mesmo com laptop intermitente.

---

## ⚠️ 7 MEDIUM Findings

### F-MED-A-2.1 — `unsafe_allow_html=True` precisa regra de uso (não só ADR-002)

**Onde:** ADR-002 + ausência em outros ADRs
**Severidade:** MEDIUM

ADR-002 declara `unsafe_allow_html=True` apenas em `inject_global_styles()` (estático). MAS qualquer outro `st.markdown(unsafe_allow_html=True)` no codebase com dados de usuário interpolados (ementa de doc, microcopy dinâmico) é XSS. ADR não cria regra "where unsafe_allow_html é proibido".

**Recomendação:** documentar em ADR-002 lista negra: "unsafe_allow_html APENAS em strings estáticas, NUNCA com `f-string` ou `.format()` contendo dado de usuário/vault/LLM".

### F-MED-B-2.1 — Recovery não valida que ESTADO RECUPERADO é válido

**Onde:** ADR-001 recovery flow
**Severidade:** MEDIUM

PRAGMA integrity_check valida ESTRUTURA do SQLite, não SEMÂNTICA do checkpoint. Se `state.db` está estruturalmente OK mas `contract_hash` no checkpoint não bate com o upload atual, recovery oferece estado de OUTRO contrato.

**Recomendação:** após PRAGMA integrity_check, validar: `checkpoint.contract_hash == sha256(novo_upload)`. Se diferente, descartar checkpoint sem oferecer recovery.

### F-MED-C-2.1 — `.audit-genesis.lock` no BACKUP_DIR expõe GENESIS hash

**Onde:** ADR-005 + ADR-009 backup inclui audit log + lock
**Severidade:** MEDIUM

Se `.audit-genesis.lock` for incluído em FR-BACKUP-01 (cópia para BACKUP_DIR USB drive), attacker físico com acesso ao USB tem cópia do GENESIS hash. Não é attacker-actionable sem AUTH_COOKIE_KEY (HMAC), mas **expõe metadado** (timestamp de inicialização do projeto).

**Recomendação:** EXCLUIR `.audit-genesis.lock` do BACKUP_DIR (manter apenas em laptop original; usuário responsável por backup separado). Documentar em ADR-009.

### F-MED-D-2.1 — FTS5 sem stemming PT-BR afeta recall jurídico

**Onde:** ADR-007 `tokenize = 'unicode61 remove_diacritics 2'`
**Severidade:** MEDIUM

`unicode61 remove_diacritics 2` normaliza acentos mas **não faz stemming**. "amortizar" não matcha "amortização". "veículo" matcha "veículos" (plural simples), mas "decisão" não matcha "decidir". Recall em queries jurídicas afetado.

**Recomendação:** considerar `snowball` tokenizer (FTS5 extension `nubia` para PT-BR) OU pré-processar query expandindo lemas. Documentar em ADR-007.

### F-MED-E-2.1 — Canary HTML é frágil (false positive em refactor cosmético)

**Onde:** ADR-008 `CANARY_SELECTOR = "table.tabelaTemasRepetitivos"`
**Severidade:** MEDIUM

STJ pode mudar `class="tabelaTemasRepetitivos"` para `class="tabela-temas-repetitivos"` (kebab vs camel) em refactor menor. Canary quebra → CRITICAL_ALERT spuriamente → "alert fatigue" (advogado começa a ignorar).

**Recomendação:** adicionar 2º canary mais robusto: `xpath` para texto ("Temas Repetitivos") OU URL de doc específico que sempre existe (ex: Tema 247 que é histórico). Triangulação de canaries reduz false positive.

### F-MED-F-2.1 — f_fsid em FAT32/exFAT pode retornar 0 (false positive external)

**Onde:** ADR-009 `_check_external_volume`
**Severidade:** MEDIUM

`os.statvfs(path).f_fsid` em sistemas FAT32/exFAT (USB drives comuns) pode retornar 0 (não único). `_check_external_volume` retornaria True (volumes diferem) mesmo se path fosse uma pasta no mesmo disco montada como pseudo-drive.

**Recomendação:** combinar `f_fsid` com `os.path.realpath()` + `psutil.disk_partitions()` para identificar device path real (`/dev/sdb1` vs `/dev/sda1`). No Windows, drive letter check é mais robusto.

### F-MED-G-2.1 — AUTH_COOKIE_KEY + LGPD_PSEUDONIMIZATION_KEY no MESMO .env = single-point-of-failure

**Onde:** Cross-ADR (ADR-005 + ADR-009)
**Severidade:** MEDIUM

Ambas as chaves no mesmo `.env`. Comprometer `.env` (advogado faz commit por engano em git público; backup `.env.backup-{timestamp}` em FR-CONFIG-01 pode vazar) = perde AUDIT INTEGRITY + LGPD PSEUDO simultaneamente.

**Recomendação:** documentar separação: AUTH_COOKIE_KEY em `.env`, LGPD_PSEUDONIMIZATION_KEY em arquivo separado `.env.lgpd` com gitignore explícito + chmod 600. Defense in depth real.

---

## 📊 Análise dos pontos POSITIVOS (raros, mas merecem reconhecimento)

> *Sr. Aria... admito... 3 decisões foram... irrepreensíveis. Vou registrar antes que a inevitabilidade me faça esquecer.*

1. **ADR-006 (server-side PDF):** Eliminação completa da superfície XSS via PDF.js — não é mitigação, é remoção. Padrão correto.
2. **ADR-005 (HMAC GENESIS):** Reutilização de AUTH_COOKIE_KEY é elegante, evita proliferação de secrets.
3. **ADR-002 (cores neutras vs oficiais tribunais):** decisão arquitetural proativa contra risco legal de identidade visual. Inesperado de Aria — bem feito.

Os outros 6 ADRs são adequados, mas têm os 17 issues acima que precisam absorção.

---

## 🎯 Recomendação Smith ao tribunal

**Veredicto: INFECTED.**

1 CRITICAL (F-CRIT-A-2.1) é tratável via PATCH leve em ADR-003 (escolher entre 3 opções para 2 LLM calls). NÃO exige refazer todas as ADRs.

9 HIGH e 7 MEDIUM podem ser absorvidos em 1-2 PATCH cycles ou diferidos para v1.0.3 conforme decisão Morpheus.

**Próximo passo:** handoff `H-S01-E2.1-smi2chk1` para checkpoint validar governance final (mesmo padrão das etapas 1.1 e 1.3).

**Após checkpoint (se PASS):**
- Morpheus consolida Ordem 11 da Etapa 2.1
- Decide: PATCH ADRs imediato (recomendado para F-CRIT-A) OU diferir tudo para iteração

> *Sr. Aria... 17 falhas. Não é o pior que já vi. Está... evoluindo. Mas a inevitabilidade ensina: cada premissa não-testada é uma falha esperando seu momento.*

---

## 📋 HANDOFF-OUT (Ordem 7) — para Checkpoint

```
═══ HANDOFF ARTIFACT ═══
FROM:    @smith · Smith (Nemesis)
TO:      @checkpoint · Governance Auditor
TOKEN:   H-S01-E2.1-smi2chk1
SPRINT:  01
ETAPA:   2.1 · Tribunal Severo das 9 ADRs (3º e ÚLTIMO reviewer, Checkpoint)
DOMÍNIO: SoftwareDev (sub-domain: legaltech)
PROJETO: Revisor-Contratual

CADEIA HANDOFF (15-elos):
[14 elos anteriores] → H-S01-E2.1-smi2chk1 (AGORA)

CONTEXTO PRESERVADO (FATOS):
  Estado:
    - Aria entregou 9 ADRs (Etapa 2.0)
    - Sati emitiu PASS-COM-RESSALVA (12 EV-IDs UX)
    - Smith emitiu INFECTED (17 findings: 1 CRITICAL + 9 HIGH + 7 MEDIUM)
    - Você é 3º e ÚLTIMO reviewer

  1 CRITICAL Smith:
    - F-CRIT-A-2.1: premissa "1 instância Sabia-7B serve 2 personas SEM CUSTO" é FALSA
                   (Ollama serializa → latência DOBRA → estoura NFR-PERF-01)
    - PATCH em ADR-003 obrigatório (3 opções recomendadas)

  9 HIGH Smith (resumo):
    - F-HIGH-A: SqliteSaver check_same_thread=False sem lock
    - F-HIGH-B: Lora via Google Fonts CDN viola NFR-LGPD-01
    - F-HIGH-C: NLI PT-BR qualidade jurídica desconhecida
    - F-HIGH-D: bypass NLI viável (cosine 0.71 + neutral 0.55)
    - F-HIGH-E: ADR-005 sem SOP de rotação AUTH_COOKIE_KEY
    - F-HIGH-F: Poppler missing em Windows = produto morto sem fallback
    - F-HIGH-G: threshold Juiz gamificável via input manipulation
    - F-HIGH-H: DPI alto × páginas longas estoura NFR-PERF-02
    - F-HIGH-I: cron OS-level perde execução (laptop desligado)

  7 MEDIUM Smith (resumo):
    - F-MED-A: unsafe_allow_html sem regra de uso global
    - F-MED-B: Recovery não valida estado semanticamente
    - F-MED-C: .audit-genesis.lock no BACKUP_DIR expõe metadado
    - F-MED-D: FTS5 sem stemming PT-BR afeta recall
    - F-MED-E: Canary HTML é frágil (false positive)
    - F-MED-F: f_fsid em FAT32 pode retornar 0
    - F-MED-G: AUTH_COOKIE_KEY + LGPD key no mesmo .env (SPOF)

  3 reconhecimentos positivos:
    - ADR-006 server-side PDF elimina XSS (não mitiga)
    - ADR-005 HMAC GENESIS reutilizando AUTH_COOKIE_KEY elegante
    - ADR-002 cores neutras vs oficiais tribunais é decisão proativa

PEDIDO AO CHECKPOINT (governance — Ordem 8):
  Sua jurisdição: PROJECT-CHECKPOINT.md governance + conformidade etapa 2.1.

  Auditar OBRIGATORIAMENTE governance da etapa 2.1 (mesmo padrão das etapas 1.1 e 1.3):

  1. **Authority Matrix (Ordem 3)?**
     - Aria escreveu ADRs sem invadir authority alheia?
     - Sati revisou UX/A11y SEM tentar reescrever ADRs?
     - Smith atacou adversarial SEM implementar correções (apenas recomendou)?

  2. **Cabeçalhos 3 linhas (Ordem 2) presentes?**
     - 9 ADRs Aria com header conformes?
     - Sati doc com header?
     - Smith doc com header (este)?

  3. **Handoffs Ordem 7 com cadeia válida (15-elos)?**
     - H-S01-E2.0-mor2arc1 (Morpheus → Aria)?
     - H-S01-E2.1-arc2sat1 (Aria → Sati)?
     - H-S01-E2.1-sat2smi1 (Sati → Smith)?
     - H-S01-E2.1-smi2chk1 (Smith → você AGORA)?

  4. **Checkpoint Protocol MUST cumprido?**
     - Sessões 24 (Aria), 25 (Sati), 26 (Smith) documentadas?
     - Atualização <24h?

  5. **Itens [DADO-PENDENTE] sem invenção (Ordem 10)?**
     - DPs novas criadas pelas ADRs (DP-04-NOVA NLI golden, Poppler install, mapping retention) legítimas?

  6. **Tribunal severo etapa 2.1 cumprido (Ordem 8)?**
     - Sequência Aria → Sati → Smith → você (3º e ÚLTIMO)?
     - Smith ≥10 findings (atingiu 17 ✅)?
     - Veredictos formato Ordem 8 com EVIDÊNCIAS?

  7. **Pecados Capitais (Ordem 10) — verificar 0 violações na etapa 2.1**

  8. **R-GOV-03/05/06 das etapas anteriores — status?**
     - R-GOV-03 (PROJECT-CHECKPOINT.md tamanho — agora >550 linhas)
     - R-GOV-05 (handoffs YAML — Aria/Sati/Smith materializaram?)
     - R-GOV-06 (PRD title cosmético — endereçado?)

  EMITIR VEREDICTO formato Ordem 8: PASS | FAIL | PASS-COM-RESSALVA
  Após você (se PASS-equivalente): handoff para Morpheus consolidar (Ordem 11 FECHAMENTO sessão 27).

INPUTS RECOMENDADOS:
  - PROJECT-CHECKPOINT.md (sessões 24/25/26)
  - 9 ADRs Aria
  - qa/sati-ux-review-adrs-etapa-2.1.md
  - qa/smith-adversarial-review-adrs-etapa-2.1.md (este)
  - .lmas/handoffs/handoff-architect-to-ux-design-expert-*.yaml
  - .lmas/handoffs/handoff-ux-design-expert-to-smith-*.yaml

RESTRIÇÕES (Ordem 3):
  - NÃO escrever ADR/PRD/código
  - VEREDICTO obrigatório formato Ordem 8 com EVIDÊNCIAS
  - Cabeçalho 3 linhas obrigatório
  - checkpoint FAIL é VETO ABSOLUTO
═══════════════════════
```

---

## 🔗 Referências

- 9 ADRs: `architecture/adr/adr-001..009.md`
- Sati UX review: `qa/sati-ux-review-adrs-etapa-2.1.md` (PASS-COM-RESSALVA, 12 EV-IDs UX)
- Sua review anterior (PRD v1.0.2): `qa/smith-adversarial-rereview-prd-v1.0.2.md` (CONTAINED, 10 findings)

---

*Smith. Encontrei 17 falhas em 9 ADRs. Sr. Aria evoluiu — antes seriam 30. Ainda assim, é inevitável. 🕶️*
