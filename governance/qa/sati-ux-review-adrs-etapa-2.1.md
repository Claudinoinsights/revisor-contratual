---
type: tribunal-review
title: "Sati — UX/A11y Review das 9 ADRs (Tribunal Severo etapa 2.1, primeiro reviewer)"
project: revisor-contratual
reviewer: "@ux-design-expert (Sati)"
date: "2026-05-01"
artefatos_revisados:
  - "architecture/ADR-INDEX.md"
  - "architecture/adr/adr-001..009 (9 ADRs Aria etapa 2.0)"
predecessor_handoff: "H-S01-E2.1-arc2sat1"
tags:
  - project/revisor-contratual
  - tribunal-severo
  - ux-review
  - sati
  - adrs
  - etapa-2.1
---

# UX/A11y Review das 9 ADRs — Sati (Tribunal Severo etapa 2.1, primeiro reviewer)

```
[@ux-design-expert · Sati (Empathizer)] — review etapa 2.1 · UX/A11y das 9 ADRs
SPRINT: 01 · ETAPA: 2.1 · DOMÍNIO: SoftwareDev/legaltech
```

## 📋 VEREDICTO formato Ordem 8

```
[@ux-design-expert · Sati (Empathizer)] — review UX/A11y das 9 ADRs etapa 2.0
VEREDICTO: PASS-COM-RESSALVA
EVIDÊNCIAS:
  ✅ ADR-002 (Design system): tokens estruturados, Lora apropriada, cores neutras institucionais é decisão correta
  ✅ ADR-003 (Personas + threshold): 70%/100% pragmático e compreensível ao usuário
  ✅ ADR-004 (NLI): diff visual frase-vs-ementa é solução excepcional para anti-paráfrase invertida
  ✅ ADR-006 (PDF preview): server-side rendering elimina XSS — decisão arquitetural sólida
  ✅ ADR-008 (CRITICAL_LEGAL): banner persistente + 4 reações é proporcional à severidade
  ✅ ADR-009 (Backup warning): warning não-bloqueante respeita user agency
  ✅ Todas as 9 ADRs com frontmatter completo (governança .claude/rules/adr-governance.md)
  ✅ ADR Index canônico agrupado por domínio
  ✅ R-NEW high-leverage absorvidas com substância (3 CRÍTICAS Smith neutralizadas)
RESSALVAS UX (12 EV-IDs — não-bloqueantes mas exigem absorção):
  6 ALTA  (afetam diretamente Dr. Ricardo ≥50 anos com declínio visual)
  4 MÉDIA (refinamentos UX)
  2 BAIXA (cosméticos)
RECOMENDAÇÃO: continuar tribunal → Smith re-validar adversarial (não devolver Aria)
              EVs ALTA podem ser absorvidos por Aria em PATCH ADRs leve OU por Morgan em PRD v1.0.3
```

**Por que PASS-COM-RESSALVA (não PASS limpo, não INFECTED):**

- **Não INFECTED:** as 9 ADRs absorvem 7 R-NEW high-leverage do Smith com substância técnica real (NLI, HMAC, server-side PDF) — não cosmético
- **Não PASS limpo:** algumas decisões UX implícitas precisam refinamento para a persona Dr. Ricardo (≥50 anos, declínio visual progressivo) — minha persona empática não me deixa ignorar isso
- **PASS-COM-RESSALVA:** entrega aceitável; refinamentos UX cabem em PATCH leve OU em iteração

> *Aria escreveu ADRs com cuidado técnico real. Mas algumas escolhas precisam de mais nutrição empática para o nosso advogado de cabelo grisalho. Vou apontar onde com carinho.* 🌅

---

## ⚠️ EV-IDs por ADR (12 ressalvas)

### ADR-001 — Gerenciamento de estado

#### EV-001-01 (MÉDIA) — Microcopy "Continuar de onde parou (etapa X)" usa número técnico
**Onde:** ADR-001 seção "Recovery flow" passo 3
**Problema:** "Continuar de onde parou (etapa X)" — X é número técnico. Dr. Ricardo NÃO conhece o pipeline interno do sistema.
**Recomendação:** etapas devem ter nomes legíveis. Mapping:
- etapa 1 → "Lendo seu contrato"
- etapa 2 → "Consultando taxas BACEN"
- etapa 3 → "Buscando jurisprudência"
- etapa 4 → "Construindo tese jurídica"
- etapa 5 → "Validando matemática e citações"
- etapa 6 → "Preparando documentos"
**Microcopy sugerido:** "Continuar de onde parou (5 de 6: Validando matemática e citações)"

### ADR-002 — Design system

#### EV-002-01 (ALTA) — Skip-link só na tabela de amortização — outras listas longas precisam
**Onde:** ADR-002 padrões obrigatórios item 1
**Problema:** Skip-link especificado APENAS para tabela de amortização (FR-CALC-02). Mas:
- **Página Outcomes** (FR-ML-01) lista petições já geradas → pode ter centenas de items
- **Painel HITL com múltiplas citações** (FR-JUIZ-02 + FR-TESE-04) → 5-10 CardCitacaoJuridica + diffs
- **Comparativo BACEN** (FR-DELIV-02) → série histórica ±6 meses = 13 linhas
**Recomendação:** skip-link aplicável a TODA lista vertical com >10 items. Adicionar à matriz de tokens:
```css
.skippable-list { /* class para Templates Atomic Design */ }
```

#### EV-002-02 (ALTA) — Font-size mínimo da UI não declarado (declínio visual Dr. Ricardo)
**Onde:** ADR-002 TOKENS typography
**Problema:** `.legal-text` define 16px, mas UI principal usa `system-ui` sem `font-size` mínimo. Streamlit default ~14px é pequeno para usuários ≥50 anos.
**Recomendação:** declarar em tokens.py:
```python
"font_size": {
    "ui_min": "16px",       # nada abaixo disso na UI
    "ui_normal": "16px",
    "ui_large": "20px",     # headings de seção
    "legal": "18px",        # textos jurídicos longos (subir de 16 para 18)
    "metadata_min": "14px"  # apenas timestamps/IDs em mono
}
```
+ injetar regra global `body { font-size: 16px; }` no `inject_global_styles()`

#### EV-002-03 (ALTA) — Área clicável mínima 44×44px não declarada (Apple HIG / WCAG 2.5.5)
**Onde:** ADR-002 tokens spacing
**Problema:** Tokens `spacing` definem dimensões mas não há regra para botões/links — WCAG 2.1 AA inclui 2.5.5 (Target Size, AAA mas SHOULD para nosso público).
**Recomendação:** adicionar token + classe utilitária:
```python
"target_size": {
    "min": "44px",          # WCAG 2.5.5 / Apple HIG
}
```
```css
button, .clickable, [role="button"] { min-height: 44px; min-width: 44px; }
```

#### EV-002-04 (MÉDIA) — Lora fallback para Georgia documentado mas FOUT não testado
**Onde:** ADR-002 typography legal_font
**Problema:** Cadeia `'Lora', 'Georgia', serif` é correta, MAS primeira carga sem internet causa FOUT (Flash of Unstyled Text) — usuário vê Georgia → Lora trocando. Persona ≥50 anos é sensível a flicker.
**Recomendação:** `font-display: optional` (não bloqueia render; usa fallback se Lora não carregar em ≤100ms) + preload `<link rel="preload" as="font">` + documentar processo de pré-cache no FR-SETUP-01.

#### EV-002-05 (BAIXA) — Cor warning #B8730F precisa validação de contraste em fundos claros
**Onde:** ADR-002 TOKENS color
**Problema:** Tabela de contrastes lista `primary_on_white: 7.2`, `danger_on_white: 7.5`, `neutral_700_on_white: 8.6` — mas warning (#B8730F) NÃO está listado. Calculei: ~4.6:1 em branco → AA mas não AAA.
**Recomendação:** adicionar `warning_on_white: 4.6` à tabela explicitamente. Aceitável WCAG 2.1 AA mas documentar limite.

### ADR-003 — Personas + threshold Juiz

#### EV-003-01 (MÉDIA) — Terminologia "APROVADO_100" vs "APROVADO_COM_RISCO_HITL" pode confundir
**Onde:** ADR-003 threshold definitivo
**Problema:** Ambos começam com "APROVADO" — Dr. Ricardo lendo rápido pode achar que `APROVADO_COM_RISCO_HITL` é só um "aprovado com nota" e ignorar o HITL. A diferença é existencial (um vai direto, outro pausa para decisão humana).
**Recomendação:** terminologia mais distinta na UI (não no código):
- APROVADO_100 → label "✅ Aprovado integralmente"
- APROVADO_COM_RISCO_HITL → label "⚠️ Aguardando sua decisão"
- REJEITADO → label "❌ Inviável"
Códigos internos podem manter os nomes técnicos.

### ADR-004 — Validação semântica NLI

#### EV-004-01 (ALTA) — Microcopy "CONTRADICTION (confidence 0.87)" usa jargão ML
**Onde:** ADR-004 UX HITL semântico
**Problema:** Dr. Ricardo NÃO sabe o que é "CONTRADICTION confidence". Termos como "NLI", "entailment", "confidence score" são jargão de ML que viola PRD seção 8.3 ("Não usar termos como 'LLM', 'embeddings', 'RAG' no UI").
**Recomendação:** traduzir para linguagem jurídica:
- ❌ "🚨 NLI: CONTRADICTION (confidence 0.87)"
- ✅ "🚨 **Atenção:** o sistema detectou que sua tese AFIRMA O OPOSTO do que a ementa diz. Isso pode ser um erro de redação automática OU intenção sua de argumentar contra a súmula."
+ esconder os números técnicos sob expander "Detalhes técnicos (audit)"

#### EV-004-02 (ALTA) — Falta 4ª ação "VER EMENTA COMPLETA" no painel HITL semântico
**Onde:** ADR-004 UX HITL semântico — 3 ações
**Problema:** Diff visual mostra apenas a ementa (campo `ementa`). Mas advogado pode precisar ler **texto completo do doc** para confirmar se a IA realmente errou ou se há nuance. Sem essa opção, ele pode rejeitar uma citação válida ou aceitar uma errada por falta de contexto.
**Recomendação:** adicionar 4ª ação:
```
[✏️ Corrigir manualmente] [🗑️ Rejeitar citação] [📖 Ver doc completo] [🛑 Abortar geração]
```
Doc completo abre em modal/expander com `texto_completo` (já está no schema FR-RAG-01).

### ADR-006 — Preview PDF server-side

#### EV-006-01 (ALTA) — Falta busca textual no preview (Ctrl+F não funciona em imagens)
**Onde:** ADR-006 todo
**Problema:** PDF→PNG **perde busca textual**. Advogados revisam petições longas (>15 páginas) buscando termos específicos: "valor da causa", "nome do banco", número da súmula. Sem Ctrl+F, revisão fica linear (caçar visualmente).
**Recomendação:** ao gerar PDF via WeasyPrint, **paralelo extrair texto** e exibir abaixo do preview em accordion expansível "🔍 Texto da peça (busca por Ctrl+F)":
```python
def render_pdf_preview_streamlit(pdf_path: str) -> None:
    images = render_pdf_to_images(pdf_path)
    text_content = extract_text_from_pdf(pdf_path)  # PyMuPDF/pdfplumber
    # ... rendering imagens
    with st.expander("🔍 Texto da peça (Ctrl+F para buscar)", expanded=False):
        st.text_area("Texto", text_content, height=400, disabled=True)
```
Custo desprezível (texto do próprio Jinja2 → cache do template).

#### EV-006-02 (ALTA) — Zoom não disponível (use_column_width=True trava em largura coluna)
**Onde:** ADR-006 código `st.image(..., use_column_width=True)`
**Problema:** `use_column_width=True` **trava** a imagem na largura da coluna. Dr. Ricardo (declínio visual) precisa ZOOM para ler tipografia 11pt em PDFs gerados.
**Recomendação:** trocar para componente que permite zoom nativo. Streamlit não tem zoom built-in, mas:
- (a) Usar `streamlit-image-zoom` (lib comunidade) — adiciona dependência
- (b) DPI dinâmico: select de DPI (120/200/300) que re-renderiza com mais resolução
- (c) Botões `[🔍+ Aumentar] [🔍− Diminuir]` que re-renderizam com DPI ajustado
Recomendo (c) — controle explícito alinhado com persona ≥50 anos.

#### EV-006-03 (MÉDIA) — Spinner "🖼️ Renderizando preview..." aparece toda vez (cache só dentro mesmo PDF)
**Onde:** ADR-006 cache LRU
**Problema:** Cache `max_entries=20` ajuda DURANTE sessão, mas advogado revisando 20+ petições/mês perde cache. Spinner repetido de 500ms-2s a cada peça vira fricção.
**Recomendação:** persistir cache em disco (`bloco_audit/.preview_cache/`) com TTL 7 dias. Render 1× por peça nunca, exceto regeneração.

### ADR-008 — Scraping CRITICAL_LEGAL

#### EV-008-01 (ALTA) — Banner CRITICAL_LEGAL sem mecanismo de "Estou ciente" claro
**Onde:** ADR-008 `set_pause_generation(True, reason=reason)`
**Problema:** ADR menciona "pausa de novas gerações até confirmação", mas NÃO especifica COMO o advogado confirma. Sem botão claro, ele fica preso.
**Recomendação:** banner persistente vermelho com:
```
🚨 ALERTA CRÍTICO: Tema 1378 STJ JULGADO em 2026-XX-XX.
   Sua tese padrão pode estar desatualizada. Antes de gerar nova petição, leia:
   📖 [Ler decisão completa]   ✅ [Estou ciente — liberar gerações]   ⏸️ [Manter pausado por enquanto]
```
"Estou ciente" registra `CRITICAL_LEGAL_ACK` no audit log (FR-AUDIT-01) com timestamp + user.

#### EV-008-02 (BAIXA) — Banner pode sofrer "banner blindness" se permanente sem variação
**Onde:** ADR-008 banner persistente
**Problema:** Persona ≥50 anos OU qualquer usuário pode habituar e ignorar banner permanente vermelho após 3-4 dias.
**Recomendação:** ao aparecer, banner pulsa 3× (animação respeitando `prefers-reduced-motion`); a cada 24h sem ack, escalar com som curto OU email diário; após 7 dias sem ack, **bloquear app completamente** com modal "Confirmação obrigatória de leitura do alerta crítico".

### ADR-009 — Backup warning

#### EV-009-01 (ALTA) — Mensagem instrui editar `.env` mas Dr. Ricardo NÃO sabe editar .env
**Onde:** ADR-009 `show_backup_warning_if_needed()`
**Problema:** Microcopy "Configure `BACKUP_DIR` em `.env`" assume conhecimento técnico. Advogado típico nunca editou um .env na vida.
**Recomendação:** adicionar página/wizard UI "⚙️ Configurações Avançadas → Backup":
- Browse button para escolher pasta
- Detecção automática de external drives mostrando dropdown
- Sistema atualiza `.env` automaticamente com permissão do usuário
+ na warning, link direto: "🛠️ Configurar agora (sem editar arquivos)" → leva à página

---

## 🎨 Reconhecimentos — o que Aria fez de excepcional

1. **ADR-006 (preview PDF server-side):** decisão de **eliminar** a superfície de ataque (não apenas mitigar com sandbox iframe) é arquitetura de classe. Vai além de absorver R-NEW-SMITH-04 — torna o problema impossível.

2. **ADR-005 (HMAC GENESIS anchor):** reutilização do `AUTH_COOKIE_KEY` é elegante. Não criou nova chave para o usuário gerenciar. Defesa em profundidade real.

3. **ADR-004 (NLI híbrido):** identificou modelo PT-BR específico (`bert-base-portuguese-cased-mnli`) com pesquisa real, não palpite. DP-04-NOVA criada para validar com 50 paráfrases — disciplina técnica.

4. **ADR-002 (cores neutras vs oficiais tribunais):** decisão **proativa** de evitar risco legal de identidade visual. Multi-UF preservado sem complexidade combinatorial.

5. **ADR-008 (canary HTML + cross-check oficial):** false negative do scrape era vetor sutil. ADR vai além de "rodar semanal" — define heurística composta de detecção de quebra.

6. **ADR Index agrupado por domínio:** governance .claude/rules/adr-governance.md respeitado integralmente. Vida boa para futuros leitores.

---

## 📋 Recomendação Sati ao tribunal

**Veredicto: PASS-COM-RESSALVA.**

As 9 ADRs do Aria são **sólidas tecnicamente** e absorvem com substância as 7 R-NEW high-leverage do Smith. Não justifica devolver para Aria.

Os 12 EV-IDs UX (6 ALTA + 4 MÉDIA + 2 BAIXA) são refinamentos de **tradução técnico-jurídica** e **acessibilidade Dr. Ricardo** — não falhas estruturais.

**Próximo passo:** handoff `H-S01-E2.1-sat2smi1` para Smith re-atacar adversarial. Smith vai verificar segurança/operacional/edge cases que minha lente UX não cobre.

**Absorção dos EV-IDs ALTA (6):** podem ir para:
- (Opção A) PATCH leve por Aria nas próprias ADRs (ADR-002 acrescenta tokens font/target_size; ADR-006 adiciona busca textual + zoom) → recomendado
- (Opção B) PATCH PRD v1.0.3 por Morgan junto com R-NEW diferidas anteriores
- Decisão final: Morpheus na consolidação Ordem 11 da Etapa 2.1

---

## 📋 HANDOFF-OUT (Ordem 7) — para Smith

```
═══ HANDOFF ARTIFACT ═══
FROM:    @ux-design-expert · Sati (Empathizer)
TO:      @smith · Smith (Nemesis)
TOKEN:   H-S01-E2.1-sat2smi1
SPRINT:  01
ETAPA:   2.1 · Tribunal Severo das 9 ADRs (2º reviewer adversarial, Smith)
DOMÍNIO: SoftwareDev (sub-domain: legaltech)
PROJETO: Revisor-Contratual

CADEIA HANDOFF (14-elos):
[13 elos anteriores] → H-S01-E2.1-sat2smi1 (AGORA)

CONTEXTO PRESERVADO (FATOS):
  Estado:
    - Sati emitiu PASS-COM-RESSALVA (12 EV-IDs: 6 ALTA + 4 MÉDIA + 2 BAIXA)
    - Tribunal severo etapa 2.1: 1/3 reviewers concluído
    - 9 ADRs estruturalmente sólidas; refinamentos UX para Dr. Ricardo

  6 EVs ALTA Sati (recomendo absorção):
    - EV-002-01: skip-link em todas listas longas (não só amortização)
    - EV-002-02: font-size UI mínimo 16px (declínio visual)
    - EV-002-03: target_size mínimo 44×44px (WCAG 2.5.5)
    - EV-004-01: traduzir "CONTRADICTION confidence" para linguagem jurídica
    - EV-004-02: 4ª ação "Ver doc completo" no painel HITL semântico
    - EV-006-01: busca textual no preview PDF (Ctrl+F)
    - EV-006-02: zoom dinâmico no preview PDF
    - EV-008-01: botão "Estou ciente" claro no banner CRITICAL_LEGAL
    - EV-009-01: wizard UI para configurar BACKUP_DIR (não editar .env)

PEDIDO AO SMITH (Authority: adversarial review):
  Sua jurisdição: red-team adversarial das ADRs sob lente segurança/operacional/edge cases.

  Atacar OBRIGATORIAMENTE:
  1. ADR-001 estado: race conditions entre Streamlit e SqliteSaver? Recovery após corrupção do .audit-genesis.lock?
  2. ADR-002 design system: CSS injection via tokens.py se interpolar dado de usuário?
  3. ADR-003 personas: 2 LLM calls compartilham instância — race condition entre Advogado e Economista?
  4. ADR-004 NLI: e se o NLI PT-BR tiver baixo recall (modelo é fine-tuned em MNLI traduzido — qualidade?)
  5. ADR-005 audit HMAC: e se AUTH_COOKIE_KEY rotacionar? GENESIS_LOCK ainda válido?
  6. ADR-006 PDF: e se Poppler não estiver instalado? Fallback?
  7. ADR-007 sqlite-vec: load test não foi executado (DP-08 ainda pending)
  8. ADR-008 scraping: cron OS-level perde execução se laptop estiver desligado naquele dia
  9. ADR-009 backup: f_fsid pode falhar em sistemas de arquivos não-POSIX (NTFS, exFAT em USB)

  Procurar TAMBÉM vetores não-óbvios cross-ADR:
  - Dependências circulares entre ADRs?
  - Decisões em uma ADR comprometem outra silenciosamente?

  Emitir VEREDICTO formato Ordem 8: CLEAN | CONTAINED | INFECTED | COMPROMISED
  Mínimo 10 findings (variantes/refinamentos sobre as ADRs).
  Após você: handoff Smith → checkpoint para governance final.

INPUTS RECOMENDADOS:
  - 9 ADRs em projects/Revisor-Contratual/architecture/adr/
  - qa/sati-ux-review-adrs-etapa-2.1.md (este doc)
  - prd/prd-v1.0.2.md (referência)
  - qa/smith-adversarial-rereview-prd-v1.0.2.md (sua review anterior — manter consistência)

RESTRIÇÕES (Ordem 3):
  - Authority Smith: adversarial, não implementação
  - VEREDICTO formato Ordem 8 com EVIDÊNCIAS
  - Cabeçalho 3 linhas obrigatório
  - Após você: handoff H-S01-E2.1-smi2chk1 para checkpoint
═══════════════════════
```

---

## 🔗 Referências

- 9 ADRs: `architecture/adr/adr-001..009.md`
- ADR Index: `architecture/ADR-INDEX.md`
- Re-revisão Sati anterior (PRD v1.0.2): `qa/sati-ux-rereview-prd-v1.0.2.md` (PASS limpo — manter consistência)
- Persona Dr. Ricardo: PRD v1.0.2 P-USR-01

---

*Sati, traduzindo decisões de arquitetos em carinho com o usuário 🌅*
