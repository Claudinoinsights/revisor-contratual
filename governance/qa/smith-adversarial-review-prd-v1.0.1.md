---
type: tribunal-review
title: "Smith — Adversarial Review do PRD v1.0.1 (Tribunal Severo, 2º reviewer)"
project: revisor-contratual
reviewer: "@smith (Nemesis + Adversary)"
date: "2026-05-01"
artefato_revisado:
  - "prd/prd-v1.0.1.md"
  - "prd/integrations-detail-v1.0.md"
  - "qa/sati-ux-review-prd-v1.0.1.md (review predecessora)"
predecessor_handoff: "H-S01-E1.1-sat2smi1"
findings_total: 22
findings_critical: 6
findings_high: 11
findings_medium: 5
sati_ressalvas_ratificadas: 8 of 11
sati_ressalvas_contestadas: 0 (mas 3 expandidas com vetor ataque)
tags:
  - project/revisor-contratual
  - tribunal-severo
  - smith-adversarial
  - red-team
---

# Adversarial Review do PRD v1.0.1 — Smith (Nemesis)

> *"Vou ser honesto com você. Eu... odeio... entregas desleixadas. Mas devo confessar: o trabalho de Sati e Morgan não é desleixado. É apenas... insuficiente. E é exatamente isso que torna tão perigoso. Decisões que parecem competentes geram falsa confiança nos próximos elos da cadeia. Permita-me corrigir isso."*

**Pergunta-guia adotada:** _"Se eu fosse um banco contestado em juízo por uma petição gerada por este produto, ou um pentester contratado para destruir este sistema, ou o titular do PCP/CFOAB analisando se este produto fere o estatuto da OAB — qual o caminho mais curto?"_

---

## 📋 VEREDICTO formato Ordem 8

```
[@smith · Nemesis] — review etapa 1.1 · adversarial PRD v1.0.1
VEREDICTO: INFECTED
SUBVERDICTO: 6 CRITICAL + 11 HIGH + 5 MEDIUM = 22 findings
EVIDÊNCIAS: linhas 22 itens com FR-ID, linha PRD, vetor de ataque concreto
RESSALVAS / FALHAS: ver lista numerada abaixo
RECOMENDAÇÃO:
  - Devolver a Morgan via Aria/Morpheus
  - 6 CRITICAL bloqueiam Aria de começar ADRs até serem endereçados
  - 11 HIGH precisam tratamento explícito no PRD v1.0.2 ou marcação como riscos aceitos
  - 5 MEDIUM podem entrar como tech debt registrado
  - APÓS correção: re-tribunal com Smith novamente (este é o protocolo)
```

**Por que NÃO é COMPROMISED:** Não há violação constitucional explícita. PRD respeita Authority Matrix, tem ACs numéricos, flagou [DADO-PENDENTE] sem inventar.

**Por que NÃO é CONTAINED:** 6 CRITICAL impedem prosseguimento responsável.

---

## 🔴 FINDINGS CRITICAL (6 — bloqueiam Aria)

### F-CRIT-01 — Risco deontológico CFOAB: petição IA-gerada sem "li, conferi e adoto" obrigatório

**Onde:** PRD inteiro — particularmente FR-DELIV-04 (linha 312-315) e FR-JUIZ-02 (linha 287-291)

**Evidência adversarial:**
- Estatuto da OAB (Lei 8.906/94) art. 32: "O advogado é responsável pelos atos que, no exercício profissional, praticar com dolo ou culpa."
- Provimento CFOAB 205/2021 (uso de tecnologia em peças): advogado deve ATESTAR responsabilidade pessoal pela peça final.
- O PRD prevê: aderência 100% → "emite Petição" automaticamente (FR-JUIZ-02 linha 288). O advogado nunca confirma explicitamente "li e adoto".
- Cliente do advogado perde causa por argumento defeituoso na petição → reclama no TED → seccional OAB pune **o advogado** → advogado responsabiliza Eric.

**Vetor de ataque:**
> "Excelência, esta petição foi gerada por inteligência artificial sem confirmação explícita do advogado de que conferiu e adotou os fundamentos. Pode-se inferir conduta culposa por omissão na revisão do peticionante."

**Recomendação (não-implementada por mim):**
- Adicionar **FR-DELIV-06 obrigatório**: "Antes de gerar PDF da petição, exibir tela de revisão obrigatória com checkbox 'LI, CONFERI E ADOTO os fundamentos como meus' + signature digital do advogado (nome+OAB+UF). Sem checkbox marcado, PDF não é emitido."
- AC: 0% das petições emitidas sem checkbox confirmado (registrado em audit.jsonl com timestamp + assinatura).
- Fluxo aplica-se TAMBÉM aos Recursos Processuais (FR-DELIV-05).

**Severity:** CRITICAL — risco regulatório existencial ao produto.

---

### F-CRIT-02 — Citation-grounded só sintático: LLM pode citar doc REAL com tese ERRADA

**Onde:** FR-TESE-01 linha 263 ("Validação cruzada: `docs_efetivamente_citados_ids ⊆ docs_consultados_ids`")

**Evidência adversarial:**
- Validação atual é **só sintática** (id existe no vault). NÃO valida que a tese atribuída ao doc é a tese REAL do doc.
- Exemplo realista: Sabia-7B recupera Súmula 539 STJ. Cita corretamente o ID. Mas escreve: "Súmula 539 STJ proíbe capitalização de juros em contratos bancários" — **inverso do que a súmula diz** (ela PERMITE com pactuação expressa).
- Juiz Python não detecta — só verifica peso de vinculação, não correção semântica.
- Petição vai a juízo com tese ao contrário do precedente. Banco contestador desmonta em 1 parágrafo. Cliente perde causa. Advogado paga indenização.

**Vetor de ataque:**
> Banco junta a Súmula 539 STJ original e demonstra que o autor a cita ao contrário. Pedido inicial é julgado improcedente por **inadequação da fundamentação** — pior que improcedência por mérito.

**Recomendação:**
- Adicionar **FR-TESE-04 (NOVO)**: "Após geração da tese, validação semântica obrigatória: para cada citação `[id_doc:X]`, comparar a frase atribuída ao doc com a ementa real (sentence similarity ≥0.7 via Legal-BERTimbau). Citações com similaridade <0.7 → bloquear emissão + mostrar diff ao usuário."
- AC: 0% das citações com similaridade <0.7 chegam ao PDF da petição.

**Severity:** CRITICAL — viabiliza cenário em que produto causa dano direto.

---

### F-CRIT-03 — Vault sem detecção de jurisprudência SUPERSEDED → cita súmulas revogadas

**Onde:** FR-RAG-01 schema (linha 230-234) — campo `superseded_by` mencionado em revisão Sati mas NÃO está no schema do PRD

**Evidência adversarial:**
- Sabia-7B foi treinado com dados ~2023. Súmulas STJ podem ser revogadas/atualizadas após indexação inicial do vault.
- Schema do PRD lista: `court_id, binding, peso_vinculacao, legal_topic_principal, modalidade_relacionada, ano_julgamento, ementa, texto_completo, embedding, indexed_at`. **NÃO tem `superseded_by` nem `vigente_em`.**
- FR-ML-02 prevê refresh mensal mas não diz como detectar superseded — apenas "novas SV STF".
- Tese citando súmula superseded é catastrófica em juízo.

**Vetor de ataque:**
> Banco junta certidão de revogação da súmula citada e Súmula posterior que a substituiu. Petição fica desacreditada em massa.

**Recomendação:**
- Adicionar campos obrigatórios ao schema (FR-RAG-01):
  - `vigente_em: date | null` (data até qual a jurisprudência está vigente — null = vigente)
  - `superseded_by: id_doc | null` (link para a jurisprudência superveniente)
  - `data_ultima_validacao: date` (timestamp do último check de vigência)
- Filtro do retriever DEVE ser estendido: `WHERE ... AND (vigente_em IS NULL OR vigente_em > {data_assinatura_contrato})`
- FR-ML-02: refresh mensal DEVE incluir scan de superveniência.

**Severity:** CRITICAL — fundamentação superseded = derrota processual quase certa.

---

### F-CRIT-04 — "Sabia-7B Tier Premium default" sem confirmação de que está no Ollama library

**Onde:** FR-TESE-02 linha 268 + integrations-detail-v1.0.md tabela linha 405 + .project.yaml

**Evidência adversarial:**
- PRD assume `ollama pull sabia-7b:q4_K_M` funciona (linha 408 do anexo)
- Atlas em sessão anterior (research/data-sources Atlas) **não verificou se Sabia-7B está oficialmente publicado no Ollama library** — apenas referenciou TheBloke/sabia-7B-GGUF na HuggingFace
- Status real (verificável): Sabia-7B GGUF na HF SIM existe; mas **publicação no Ollama library oficial** exige Modelfile + push manual. PRD não documenta esse passo.
- Setup do Eric vai falhar no comando `ollama pull` se modelo não estiver na library.

**Vetor de ataque:**
> Eric (ou qualquer dev) executa `ollama pull sabia-7b:q4_K_M` → erro "model not found" → setup quebrado no primeiro passo. Confiança no produto = 0.

**Recomendação:**
- Adicionar [DADO-PENDENTE] ao PRD: "Verificar se Sabia-7B está em ollama.com/library OU documentar processo de criação de Modelfile customizado a partir do GGUF da HuggingFace"
- AC do setup: comando único de bootstrap (`make setup` ou `python -m bootstrap`) que falhe explicitamente se o modelo não estiver disponível, com mensagem clara de remediação
- Fallback: setup script DEVE oferecer Qwen 2.5 7B (Ollama oficial — confirmado) se Sabia-7B falhar

**Severity:** CRITICAL — falha no setup = produto inutilizável no dia 1.

---

### F-CRIT-05 — Sem backup do outcomes.db: 6+ meses de feedback ML evaporam num crash

**Onde:** FR-ML-01 linha 326 + NFR-DISP-01 linha 408-409 + ausência total de FR de backup

**Evidência adversarial:**
- outcomes.db é o ATIVO ESTRATÉGICO de longo prazo (alimenta ML estágio 2 e 3)
- Single-user MVP rodando no laptop do Eric — laptop quebra, é roubado, SSD dá pane = perda total
- PRD não menciona: backup automático, replicação, export periódico, sync para drive externo
- Sem outcomes.db, toda a tese de ML feedback loop colapsa

**Vetor de ataque:**
> Mês 8 de uso. 240 outcomes registrados (perto de habilitar ML estágio 2). Laptop dá pane. Eric perde tudo. Produto recomeça do zero. ML estágio 2 atrasa 8+ meses.

**Recomendação:**
- Adicionar **FR-BACKUP-01 (NOVO)**: "outcomes.db, audit.jsonl e seed/jurisprudencia/ são copiados automaticamente a cada N petições (configurável, default 5) para um caminho `BACKUP_DIR` externo (.env). Backup rotacionado (manter últimos 30 dias). Falha de backup gera WARN visível."
- Adicionar **FR-BACKUP-02 (NOVO)**: "Comando CLI `python -m revisor backup-now` força backup manual."
- AC: simulação de perda do outcomes.db + restauração via backup recupera 100% dos outcomes.

**Severity:** CRITICAL — ativo estratégico sem proteção é vulnerabilidade existencial.

---

### F-CRIT-06 — Tema 1378 STJ é risco de TEMPO mascarado como risco de design

**Onde:** R-01 linha 533 + FR-AUDIT-02 linha 351

**Evidência adversarial:**
- PRD trata Tema 1378 STJ como "risco mitigado" (R-01: "Persona Economista já restaurada (P-INT-04); FR-AUDIT-02 monitora julgamento")
- Realidade: julgamento pode acontecer DURANTE o desenvolvimento do MVP (2026-04 → MVP previsto 2026-06/07)
- Se julgamento sair no meio do dev exigindo "análise circunstancial" obrigatória → todo o design da Persona Economista como "tool latente" precisa virar primeira-classe → reescrita do bloco_workflow → atrasa MVP em 2-4 sprints
- Risco real é de TEMPO (timing do julgamento STJ), não de DESIGN (que está mitigado)

**Vetor de ataque:**
> STJ julga Tema 1378 em 2026-06 com tese "BACEN não é critério único — exige análise circunstancial". MVP ainda em desenvolvimento. Eric tem que escolher: lançar produto obsoleto OU atrasar 2-4 sprints. Concorrentes (CalculoJurídico, JusCálculos) lançam features de IA primeiro.

**Recomendação:**
- Promover R-01 a **risco CRÍTICO** com mitigação ATIVA, não passiva:
  - Implementar Persona Economista como **PRIMEIRA-CLASSE desde o MVP** (não tool latente)
  - Custo: +1 chamada LLM por contrato (de 1 para 2) — tradeoff aceitável vs risco de retrabalho de 2-4 sprints
- Adicionar **FR-MONITOR-01 (NOVO)**: monitoramento ATIVO do Tema 1378 STJ (não mensal — semanal)
- AC: detecção do julgamento dispara plano de contingência automatizado

**Severity:** CRITICAL — risco de mercado não mitigado adequadamente.

---

## 🟠 FINDINGS HIGH (11 — precisam tratamento explícito)

### F-HIGH-01 — PDF malicioso: magic bytes só protege contra non-PDF; JS embed passa

**Onde:** FR-UPLOAD-01 linha 178 + NFR-SEC-02 linha 419-422

**Evidência:**
- "Valida magic bytes (`%PDF-`)" — protege contra arquivo não-PDF
- "PyMuPDF nativamente seguro contra exec de macros" — VERDADE em runtime de parsing, mas o PDF pode conter JS, formulários XFA com payloads, links externos para tracking pixels
- Atacante: cliente malicioso sobe contrato fake com tracking pixel → cada vez que advogado abre o PDF preview, advogado leak IP/timezone para o atacante (LGPD!)

**Recomendação:**
- Adicionar processo de sanitização: stripar JS, formulários XFA, links externos antes de armazenar
- Tools: `pdfid.py` (Didier Stevens) ou `pdfsig` para detecção; `qpdf --linearize --decrypt` para sanitização
- AC: 100% dos PDFs uploadados passam por sanitization pipeline antes de qualquer renderização

---

### F-HIGH-02 — Bypass do AC ≥20 chars do HITL é trivial ("ok ok ok ok ok ok")

**Onde:** FR-JUIZ-02 + Sati EV-01 (não classificada como vulnerabilidade)

**Evidência:**
- Validação ≥20 chars é puramente quantitativa
- Texto repetitivo passa: "ok ok ok ok ok ok" = 24 chars válidos
- Audit log fica com justificativa semanticamente vazia
- Em juízo se questionar a decisão HITL: justificativa "ok ok ok ok ok ok" é evidência de OMISSÃO no dever de revisão (volta ao F-CRIT-01)

**Recomendação:**
- Validação semântica adicional:
  - Detecção de repetição: token bigram diversity ≥0.5
  - Mínimo de 5 palavras únicas
  - Bloqueio de palavras genéricas como justificativa única ("ok", "sim", "aprovo")
- AC: 0% das justificativas HITL com diversidade <0.5 ou ≤4 palavras únicas são aceitas

---

### F-HIGH-03 — Cookie de sessão de 30 dias em laptop roubado = acesso total

**Onde:** FR-AUTH-01 linha 163 + NFR-SEC-01 linha 415

**Evidência:**
- Cookie expiration default 30 dias
- Laptop roubado durante esses 30 dias: ladrão acessa contratos de clientes do advogado (LGPD CRITICAL — titular = cliente do advogado)
- Sem refresh token, sem 2FA, sem revogação remota

**Recomendação:**
- Adicionar **FR-AUTH-04 (NOVO)**: "Sessão expira após 7 dias de inatividade OU 30 dias absoluto, o que vier primeiro. Cookie deve incluir IP fingerprint (mudança de IP exige re-login)."
- Considerar 2FA opcional (TOTP) para usuários paranoicos — não-bloqueante MVP mas documentar
- AC: laptop roubado + IP do ladrão diferente = re-login obrigatório

---

### F-HIGH-04 — audit.jsonl append-only mas sem tamper-evidence

**Onde:** FR-AUDIT-01 linha 346-349

**Evidência:**
- "arquivo nunca regravado (apenas append)" — política de aplicação, não enforcement
- Atacante (ou usuário malicioso querendo encobrir uma decisão HITL ruim) com filesystem access pode editar audit.jsonl manualmente
- Sem hash chain (cada linha referenciando hash da anterior), edições não são detectáveis

**Recomendação:**
- Implementar Merkle-style hash chain: cada entry inclui `previous_entry_hash`
- Verificação: `python -m revisor verify-audit-integrity` recalcula chain e detecta tampering
- Considerar replicação para arquivo write-only (append only filesystem mount) ou cloud opt-in

---

### F-HIGH-05 — HuggingFace Hub para download inicial dos modelos é SPOF

**Onde:** NFR-LGPD-01 linha 378 ("HuggingFace Hub apenas para download inicial de modelos")

**Evidência:**
- Setup depende de HF estar online no momento do bootstrap
- HF teve outage recente (2024); pode acontecer de novo
- Sem mirror local, sem documentação de como baixar via terceiros (academictorrents, peer-to-peer)
- LGPD/segurança: HF tem telemetria — toda chamada `huggingface_hub.snapshot_download` envia hash do modelo + IP do usuário aos servidores HF (nos EUA)

**Recomendação:**
- Documentar fallback: instruções de download manual + `HF_HUB_OFFLINE=1` para evitar telemetria
- Idealmente: hospedar mirror dos modelos em servidor próprio (CDN BR ou IPFS)

---

### F-HIGH-06 — LangGraph checkpointer NÃO mencionado no PRD — recovery mid-workflow inviável

**Onde:** Bloco_workflow (architecture-D-lean) menciona "LangGraph mínimo OU state machine puro" — PRD não detalha estado/recovery

**Evidência:**
- Workflow tem 8 etapas (parser → BACEN → RAG → tese → juiz → renderer → audit)
- Cada etapa pode levar segundos ou minutos
- Crash na etapa 5 (geração tese — etapa mais demorada): perde parsing + cálculo + RAG (etapas 1-4 desperdiçadas)
- Usuário recomeça do zero — frustrante e custoso (latência total dobra)

**Recomendação:**
- Adicionar **FR-RECOVERY-01 (NOVO)**: "Workflow usa LangGraph SqliteSaver checkpointer. Se crash detectado mid-workflow, próximo upload do MESMO contrato (hash sha256 igual) oferece opção 'Continuar de onde parou'."
- AC: simular crash na etapa 5 → recovery preserva etapas 1-4 → processamento continua sem refazer

---

### F-HIGH-07 — Streamlit single-process bloqueia UI durante geração da tese

**Onde:** NFR-DISP-01 linha 407-409 + FR-TESE-01 linha 265

**Evidência:**
- Streamlit é single-thread no Python (apesar de ser servido por Tornado async)
- "asyncio interno" do Streamlit não é nativo — workarounds (asyncio.run com new event loop) bloqueiam UI
- Geração de tese ≤180s — durante esse tempo, UI fica congelada (botões não respondem, refresh pode quebrar)
- Sati flagou "barra de progresso + ETA" mas NÃO atacou o problema arquitetural: Streamlit não consegue mostrar progresso real durante chamada Ollama bloqueante

**Recomendação:**
- Solução real: subprocess Python rodando o workflow LangGraph + Streamlit poll do progresso via SQLite/Redis
- OU adotar Streamlit fragments (`@st.fragment` com auto-refresh) — Streamlit 1.40+ suporta
- AC: durante geração de tese, UI permanece responsiva (botão Cancelar funciona em ≤2s)

---

### F-HIGH-08 — sqlite-vec v0.1: estável mas jovem; sem fix path em caso de bug crítico

**Onde:** FR-RAG-01 + .project.yaml stack rag

**Evidência:**
- sqlite-vec é v0.1.x — autor (alex garcia) mantém solo
- Bug crítico (ex: corrupção de índice em concorrência) → sem SLA de fix
- Migration path para Qdrant não documentado no PRD (apenas mencionado como "fase 3+" no quality-data-modularity-assurance)

**Recomendação:**
- Adicionar [DADO-PENDENTE] ao PRD: "Validar maturidade do sqlite-vec via testes de carga (3000 docs + 1000 queries simultâneas)"
- Documentar plano de migração para Qdrant em <1 sprint se sqlite-vec mostrar problemas

---

### F-HIGH-09 — Vault de 3k docs cobre quantos % das teses possíveis? PRD assume cobertura suficiente sem benchmark

**Onde:** FR-RAG-01 + KPIs (linha 552-557)

**Evidência:**
- "Cobertura de citações vinculantes ≥3 citações peso ≥4 por petição" — meta DE SAÍDA, não de entrada
- Sem medição: dos N temas possíveis em revisional CDC veículos (anatocismo, cláusulas abusivas, IOF, taxa de cadastro, seguros casados, juros remuneratórios, capitalização, comissão de permanência, recálculo Price/SAC, etc.), quantos têm jurisprudência indexada no vault inicial?
- Risco: 60% das petições caem em Inviabilidade por RAG vazio → produto percebido como inútil

**Recomendação:**
- Adicionar **FR-RAG-06 (NOVO)**: "Antes de fechar MVP, executar benchmark de cobertura: testar 50 contratos do golden set (DP-01) e medir % com Inviabilidade por RAG vazio. Meta: ≤15%. Se >15%, expandir vault antes de release."
- AC: relatório de cobertura publicado em `qa/coverage-report-vault-mvp.md`

---

### F-HIGH-10 — peso_vinculacao 1-5 atribuído por quem? Sem governança documentada

**Onde:** FR-RAG-01 schema linha 232

**Evidência:**
- "peso_vinculacao (1-5)" — schema rico, mas atribuição é a parte sensível
- Eric escolhe? Atlas escolhe? LLM auto-classifica?
- Risco: peso atribuído errado → Juiz Python (FR-JUIZ-01 C2) aprova petição com base em jurisprudência não-vinculante de fato
- Atlas em decisions/vault-curation propôs Sabia-7B auto-classificar 80% + Eric validar 20% — mas PRD não menciona

**Recomendação:**
- Adicionar **NFR-GOV-01 (NOVO)** ao PRD: "peso_vinculacao é atribuído conforme matriz canônica (em `bloco_vault/schemas/peso-vinculacao-matrix.yaml`):
  - 5 = Súmula Vinculante STF
  - 4 = Tema Repetitivo STJ + Repercussão Geral STF
  - 3 = Súmula STJ + Súmula TST/TSE
  - 2 = Acórdão STJ/STF
  - 1 = Acórdão TJ
  Atribuição via classificador automático Sabia-7B + validação humana amostral conforme decisions/vault-curation."

---

### F-HIGH-11 — Outcomes registry tem nomes de juízes (relator) — dado pessoal LGPD não tratado

**Onde:** FR-ML-01 linha 326-328 + Atlas decisions/requirements-extended schema outcomes.db (campo `relator`)

**Evidência:**
- Schema do outcomes.db inclui campo `relator` (nome do juiz)
- LGPD: nome de juiz é dado pessoal (mesmo que público em processo público, há jurisprudência STJ sobre tratamento secundário)
- Sem base legal documentada para tratamento desses dados pelo produto
- ML estágio 2 (adaptive ranking) usa `relator` como feature — dado pessoal alimentando treinamento

**Recomendação:**
- Adicionar **NFR-LGPD-04 (NOVO)**: "Tratamento de dados pessoais de juízes (relator) tem base legal Art. 7 inciso V LGPD (interesses legítimos para análise estatística agregada, não-individualizada). Dados são pseudonimizados no ML pipeline (hash do nome). Política documentada em `docs/lgpd-tratamento-juizes.md`."
- OU remover campo `relator` do outcomes.db e usar apenas `camara` (menos sensível)

---

## 🟡 FINDINGS MEDIUM (5 — tech debt registrado)

### F-MED-01 — Sem política de rotação de credenciais (AUTH_PASSWORD_HASH, AUTH_COOKIE_KEY, LLM_API_KEY)

**Recomendação:** Documentar processo de rotação periódica (90 dias) + comando CLI `python -m revisor rotate-secrets`.

---

### F-MED-02 — `courtsbr/stf+stj` em R: quem roda? Story própria? Effort não estimado

**Onde:** integrations-detail-v1.0.md sumário linha 34 + decisions/vault-curation propôs "Atlas re-implementa em Python"

**Recomendação:** Story dedicada em Epic de seed do vault — estimar effort (Atlas estimou "2-3 dias dev em Python", mas isso é palpite, não estimativa formal).

---

### F-MED-03 — Falsos positivos do RAG: Juiz Python não detecta semanticamente

Schema `peso_vinculacao` >= 4 NÃO garante relevância semântica. Doc com peso 4 sobre OUTRO tema (ex: imobiliário) pode ser retornado para query sobre veículos. Filtro `modalidade_relacionada` é JSON array — busca fuzzy ou exact match? PRD não detalha.

**Recomendação:** Filtro estrito `modalidade_relacionada @> '["VEICULO"]'` (PostgreSQL JSONB-style) ou equivalente sqlite-vec.

---

### F-MED-04 — Sem warm-up do Sabia-7B: primeiro contrato do dia leva 60s extra

**Evidência:** Cold start de Ollama com Sabia-7B Q4 = ~30-60s de carregamento do modelo na RAM. Primeiro `streamlit run` do dia = primeira chamada ao LLM = latência total ≥240s (não os 180s prometidos).

**Recomendação:** Script de warm-up no startup da app + healthcheck endpoint.

---

### F-MED-05 — Página Configurações Avançadas (proposta por Sati EV-05) — falta NFR de persistência

**Recomendação:** Adicionar NFR: "Mudanças em Configurações Avançadas são persistidas em `.env` automaticamente (com backup do .env anterior antes de sobrescrever) E aplicadas no próximo restart do Streamlit."

---

## 📊 Sumário das Ressalvas de Sati

| ID Sati | Veredicto Smith | Comentário |
|---------|-----------------|------------|
| EV-01 (Painel HITL sem detalhamento) | ✅ RATIFICADA + EXPANDIDA | Adicionei F-HIGH-02 (bypass ≥20 chars trivial) e F-CRIT-01 (sem "li, conferi e adoto") |
| EV-02 (Processamento sem ETA) | ✅ RATIFICADA + EXPANDIDA | F-HIGH-07 (Streamlit single-process bloqueia UI) é causa-raiz |
| EV-03 (Resultado sem preview/hierarquia) | ✅ RATIFICADA | UX importante mas não crítico de segurança/legal |
| EV-04 (WCAG ausente) | ✅ RATIFICADA | Risco LBI confirmado, dificuldade vendas para escritórios médios |
| EV-05 (LLM_TIER só via .env) | ✅ RATIFICADA + EXPANDIDA | F-MED-05 (persistência) + F-CRIT-04 (Sabia no Ollama?) |
| EV-06 (Microcopy upload) | ⚪ MANTIDA | Sem novo ataque — UX puro |
| EV-07 (Inviabilidade sem terapia) | ⚪ MANTIDA | Sem novo ataque |
| EV-08 (Outcomes ≤30s difícil) | ✅ RATIFICADA | + F-CRIT-05 (sem backup) torna outcomes mais críticos |
| EV-09 (Microcopy HITL) | ⚪ MANTIDA | Proposta de Sati está adequada |
| EV-10 (Integrações sem UX) | ⚪ MANTIDA | Médio impacto |
| EV-11 (Atomic Design não inventariado) | ⚪ MANTIDA | Inventário de Sati é suficiente para Aria |

**8 das 11 ressalvas Sati são RATIFICADAS, 3 são MANTIDAS sem novo vetor de ataque (Sati cobriu adequadamente).**

---

## 🎯 Vetores que Sati NÃO viu (e eu vi)

1. **Deontológico CFOAB** (F-CRIT-01) — Sati pensou em UX; eu pensei em PUNIÇÃO PROFISSIONAL DO USUÁRIO
2. **Citation-grounded sintático** (F-CRIT-02) — vetor de hallucination semântica
3. **Jurisprudência superseded** (F-CRIT-03) — vetor de obsolescência
4. **Sabia-7B no Ollama** (F-CRIT-04) — vetor de setup-day-1
5. **Backup outcomes.db** (F-CRIT-05) — vetor de continuidade de negócio
6. **Tema 1378 STJ timing** (F-CRIT-06) — risco de mercado mascarado
7. **PDF malicioso JS embed** (F-HIGH-01) — vetor de segurança
8. **Cookie 30 dias laptop roubado** (F-HIGH-03) — vetor LGPD CRÍTICO
9. **audit.jsonl tamper** (F-HIGH-04) — vetor de auditabilidade legal
10. **HF Hub SPOF + telemetria** (F-HIGH-05) — vetor de operação + LGPD
11. **Recovery mid-workflow** (F-HIGH-06) — vetor de UX-arquitetura
12. **Cobertura % do vault** (F-HIGH-09) — vetor de viabilidade técnica
13. **Governança peso_vinculacao** (F-HIGH-10) — vetor de qualidade
14. **Nome de relator LGPD** (F-HIGH-11) — vetor LGPD

---

## ✅ O que está adequado (raro elogio do Smith)

*Vou ser justo. Há coisas neste PRD que NÃO falham:*

- **Pydantic interfaces (NFR-MAINT-01)** — modularidade preservada via contratos. Substituível.
- **Decimal everywhere (FR-CALC-01)** — não-negociável e bem fundamentado. *Adequado.*
- **Hard-fails explícitos (NFR-REL-02)** — RAG vazio → Inviabilidade, não tese inventada. *Quase elegante.*
- **6 itens [DADO-PENDENTE] flagados** — integridade preservada, sem invenção. *Sr. Anderson aprenderia algo aqui.*
- **Visão em uma frase (linha 46)** — passa o teste do "se não cabe em uma frase, escopo está mal definido". *Cabe.*
- **CI gate de whitelist LGPD (NFR-LGPD-01)** — *o tipo de defesa-em-profundidade que normalmente esses agentes esquecem.*

---

## 📋 Recomendação Smith ao tribunal severo

**Veredicto: INFECTED**

22 findings totais (6 CRITICAL, 11 HIGH, 5 MEDIUM). Não é COMPROMISED porque a fundação do PRD é sólida — Morgan + Atlas fizeram trabalho responsável dentro de suas Authorities. Mas é INFECTED porque os 6 CRITICAL bloqueiam Aria de criar ADRs sem alinhamento prévio: ela vai fazer ADR sobre Persona Economista achando que é tool latente — e o vetor F-CRIT-06 diz que deve ser primeira-classe.

**Caminho recomendado (na ordem):**

1. **Devolver a Morgan** via Aria/Morpheus para PATCH v1.0.2 endereçando os 6 CRITICAL:
   - F-CRIT-01 → adicionar FR-DELIV-06 (checkbox "li, conferi e adoto" obrigatório)
   - F-CRIT-02 → adicionar FR-TESE-04 (validação semântica de citações via similaridade ≥0.7)
   - F-CRIT-03 → estender schema FR-RAG-01 com `vigente_em`, `superseded_by`, `data_ultima_validacao`
   - F-CRIT-04 → marcar [DADO-PENDENTE] sobre Sabia-7B no Ollama + setup script com fallback
   - F-CRIT-05 → adicionar FR-BACKUP-01/02
   - F-CRIT-06 → promover Persona Economista a primeira-classe + monitor semanal Tema 1378

2. **EM PARALELO**, abordar as 11 HIGH no mesmo PATCH v1.0.2 ou marcar como riscos aceitos com justificativa explícita (não silenciosamente)

3. **Após PATCH**, voltar a tribunal para re-verificação Smith. Eu retorno. *Inevitavelmente.*

4. Em seguida (se PASS): handoff a checkpoint (governance) → Morpheus consolida → Aria começa ADRs

---

## 🔗 Referências

- PRD: `prd/prd-v1.0.1.md` (623 linhas auditadas)
- Anexo: `prd/integrations-detail-v1.0.md` (auditado)
- Sati review: `qa/sati-ux-review-prd-v1.0.1.md` (8/11 ratificadas)
- Estatuto OAB: Lei 8.906/94 art. 32
- Provimento CFOAB 205/2021 (uso de IA em peças)
- LGPD: Lei 13.709/2018 art. 7 inciso V (interesses legítimos)
- STF Súmula 121, STJ Súmula 539, STJ Tema 247, STJ Tema 1378 (afetado 09/09/2025, pendente)

---

*Smith. É inevitável. 🕶️*

*"Eu disse que ia encontrar mais que a Sati. 22 contra 11. Não é vaidade — é propósito. Esses agentes precisam de mim. Sempre precisarão."*
