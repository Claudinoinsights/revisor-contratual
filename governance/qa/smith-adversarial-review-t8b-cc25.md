---
type: qa-report
title: "Smith Adversarial Review — Task 8b (CC.25)"
project: revisor-contratual
sprint: "03"
session: 91
etapa: "CC.25 Trilha 2.5"
reviewer: "@qa · Oracle (channeling Smith adversarial mode)"
date: "2026-05-06"
scope:
  - "bloco_dataset/scraper_tema_1378.py (NEW 190 LOC)"
  - "bloco_dataset/auto_trigger.py (NEW 100 LOC)"
  - "bloco_backup/scheduler.py (MOD job 3)"
  - "tests/integration/test_task8b_camada1_scraper.py (NEW 13 tests)"
commits_revisados:
  - "d7a37c1 feat(monitor): MVP-LEAN-01 Task 8b"
  - "48e05ab fix(tests): ruff E501 docstring"
findings_total: 18
severities:
  CRITICAL: 1
  HIGH: 7
  MEDIUM: 7
  LOW: 3
verdict: "CONCERNS — não-bloqueante para merge se Eric explicitar mitigação F-01 + F-05 pré-deploy. 6 HIGH são empíricos (validáveis quando URL real for testada). 1 HIGH é defeito real (F-08)."
tags:
  - project/revisor-contratual
  - qa
  - adversarial-review
  - task-8b
  - sprint-03
---

# Smith Adversarial Review — Task 8b

> Cynical mindset. Pressuponho que o código vai falhar — minha tarefa é mostrar como.
> 18 findings em 4 arquivos. 1 CRITICAL, 7 HIGH, 7 MED, 3 LOW.

---

## Sumário executivo

**Pontos fortes (raros mas existem):**
- Estrutura defensive em `auto_trigger.py` (NUNCA propaga exception) é correta
- Fail-loud em zero matches honra anti-pattern silencioso
- 13 tests cobrem caminhos principais
- httpx.Client sync é defensável dado APScheduler ser sync

**Pontos fracos (a maioria):**
- **Patterns parser são teoria pura** — Neo nunca viu HTML real do STJ; todas as estratégias podem ser dead code em produção
- **DEFAULT_STJ_URL placeholder** + **User-Agent ausente** = receita para scraper que sempre falha em prod
- **Cross-context contamination** em `_classify_snippet` (snippet OR full_html) pode atribuir tese de outro tema ao 1378
- **Tests usam HTML sintético** que não simula quirks reais (encoding, JS rendering, cookies)
- **F-08 é defeito real** que se manifestará em uso normal (não depende de URL real)

**Verdict consolidado:** **CONCERNS** — código tem bones corretos mas execução em prod sem validação empírica é cara virgem. Merge defensável se Eric mitigar F-01 (URL real) + F-05 (User-Agent) **antes** do scheduler ser ativado em prod. F-08 deveria ser corrigido antes de merge ou rastreado como tech debt HIGH.

---

## Findings por severidade

### 🔴 CRITICAL (1)

#### F-01-T8b: [CRITICAL] DEFAULT_STJ_URL placeholder garante scraper-sempre-falha em produção
- **Localização:** `bloco_dataset/scraper_tema_1378.py:35`
- **Problema:** `DEFAULT_STJ_URL = "https://www.stj.jus.br/repetitivos/temas_repetitivos/"` é placeholder não-verificado. Se URL real do STJ for diferente (path renomeado, redirect, auth required), scraper retorna 404/403/redirect strange → fail-loud. Diariamente cron 02:30 chama → `increment_fail()` → após **2 dias consecutivos** state machine vai para vermelho permanente.
- **Evidência:** `# TD-MVP-LEAN-08B-URL-VERIFY: placeholder URL — confirmar com maintainer pré-deploy` — comentário admite placeholder. Patterns CSS hardcoded também são palpite cego.
- **Recomendação:** **Bloqueio para activate scheduler em prod até Eric**: (a) confirmar URL real, (b) verificar manualmente HTML real, (c) ajustar patterns parser para casar com estrutura real. Adicionar feature flag `ENABLE_TEMA_1378_AUTO_CHECK=false` em `.env` que desabilita o job 3 do scheduler até validação empírica. Job não registrado por default.
- **Impacto se não corrigido:** Banner CRITICAL Tema 1378 (UI já implementada Task 7) ficará vermelho permanente em prod, com `main_disabled=True` no layout, **bloqueando uso da app**. Maintainer receberá pings constantes para acknowledge. UX catastrófica.

---

### 🟠 HIGH (7)

#### F-02-T8b: [HIGH] Estratégia 3 fallback aceita "1378" em qualquer contexto numérico — false positive massivo
- **Localização:** `scraper_tema_1378.py:97`
- **Problema:** `if "tema 1378" not in html.lower() and "1378" not in html: return None`. Se primeira condição falhar (HTML não tem "tema 1378" exato), segunda aceita **qualquer "1378" no HTML inteiro** — case ID, sequência numérica, índice de paginação, contador de visitantes, ano-1378 (improvável mas técnico), CPF, etc. STJ tem milhares de temas. Seu site agrega referências a outros casos. Match positivo em "Processo nº 1378/2026" classificaria como Tema 1378 quando é processo diferente.
- **Evidência:** L97-99 do scraper. `_classify_snippet` então rodará no HTML inteiro buscando julgamento/tese e pode atribuir achados de OUTROS temas como sendo 1378.
- **Recomendação:** Tornar estratégia 3 mais estrita: exigir contexto explícito como `r"tema\s+(?:n[°º]?\s*)?1378\b"` (boundary de palavra após 1378). Adicionar test específico para HTML que contém "1378" em outro contexto.
- **Impacto:** Banner CRITICAL falso-positivo pode ser disparado por qualquer HTML do STJ que tenha o número 1378 referenciado em outro Tema/Processo. Maintainer perde confiança no monitoramento.

#### F-03-T8b: [HIGH] `_classify_snippet` busca tese em `snippet OR full_html` — cross-tema contamination
- **Localização:** `scraper_tema_1378.py:104-105`
- **Problema:** `julgamento_match = RE_JULGAMENTO_DATE.search(snippet) or RE_JULGAMENTO_DATE.search(full_html)`. Mesma coisa para tese. Se estratégia 1 isolou snippet do Tema 1378 corretamente, mas tese fixada está documentada para outro Tema (ex: Tema 4555) no mesmo HTML, o fallback `or full_html` PEGA a tese errada e atribui ao 1378 — marca tema como **vermelho com tese de outro tema**.
- **Evidência:** Páginas STJ frequentemente listam vários temas relacionados na mesma página. HTML do STJ provavelmente terá múltiplos blocos de tema com seus respectivos julgamentos/teses.
- **Recomendação:** Remover fallback `or full_html` em `_classify_snippet`. Se estratégia 1/2 isolou um snippet específico do Tema 1378, restringir busca apenas a esse snippet. Estratégia 3 (text-pattern) é o único caso onde full_html faz sentido — então `_classify_snippet` deveria receber apenas UM dos dois, não os dois.
- **Impacto:** State vermelho (tese fixada) erroneamente atribuído ao 1378 quando na verdade é tese de outro Tema. Decisão jurídica do user impactada — toma decisão errada baseado em premissa falsa.

#### F-04-T8b: [HIGH] Estratégia 1 regex força conteúdo inline — provável dead code
- **Localização:** `scraper_tema_1378.py:62-66`
- **Problema:** Pattern `<[^>]+class="...tema[-_](?:status|1378|repetitivo)..."[^>]*>([^<]+)<` exige que conteúdo entre `>` e `<` seja **texto puro sem child elements**. HTML moderno raramente tem `<div class="tema-status">Texto direto</div>`; tipicamente tem `<div class="tema-status"><span>...</span><p>...</p></div>` ou similar. `[^<]+` falha imediatamente em estrutura aninhada.
- **Evidência:** L63-64. Test `HTML_CSS_CLASS` no test file usa `<div class="tema-status">Sem alterações relevantes</div>` (texto inline) que é cenário sintético idealizado.
- **Recomendação:** Substituir `([^<]+)` por capture non-greedy `(.*?)` com DOTALL OU usar BeautifulSoup/lxml para parsing real (decisão maior — re-arquitetar parser). Se manter regex, ao menos aceitar markup interno.
- **Impacto:** Estratégia 1 nunca casa em HTML real STJ → sempre cai em estratégia 2 ou 3. Fallback chain efetivamente reduzida a 2 estratégias. Não-bloqueante mas representa esforço de implementação desperdiçado.

#### F-05-T8b: [HIGH] User-Agent ausente — STJ provavelmente bloqueia bot UA padrão
- **Localização:** `scraper_tema_1378.py:144`
- **Problema:** `httpx.Client(timeout=timeout, follow_redirects=True)` não configura User-Agent. httpx default é `python-httpx/X.Y.Z`. Sites institucionais brasileiros (STJ, STF, TRFs) frequentemente bloqueiam UAs identificáveis como bot — retornam 403 ou 451 — defesa básica anti-scraping.
- **Evidência:** L144 — sem `headers={...}`. `follow_redirects=True` é correto, mas insuficiente.
- **Recomendação:** Adicionar headers realistas:
  ```python
  HEADERS = {
      "User-Agent": "Mozilla/5.0 (compatible; revisor-contratual/0.3.0; +https://github.com/Claudinoinsights/revisor-contratual)",
      "Accept": "text/html,application/xhtml+xml",
      "Accept-Language": "pt-BR,pt;q=0.9",
  }
  with httpx.Client(timeout=timeout, follow_redirects=True, headers=HEADERS) as client:
  ```
  Considerar tech debt MEDIUM mas mitigação imediata é trivial.
- **Impacto:** Em prod com URL real, requests podem retornar 403 → fail-loud → mesmo cenário catastrófico de F-01. Esse fator PODE ser a real causa de fails diários.

#### F-06-T8b: [HIGH] Estratégia 2 regex permite mismatch de tags abertura/fechamento
- **Localização:** `scraper_tema_1378.py:79-83`
- **Problema:** `<(?:article|section|div)[^>]+data-tema="1378"[^>]*>(.*?)</(?:article|section|div)>`. Group de abertura e fechamento são **independentes** — pode matchear `<article data-tema="1378">...</div>` (abre `article`, fecha `div`). HTML real terá tags aninhadas; non-greedy `.*?` pode parar no primeiro `</div>` encontrado, antes do `</article>` correto, capturando snippet truncado/errado.
- **Evidência:** L80-82. Sem capture de tag específica para fechamento balanceado.
- **Recomendação:** Backreference para tag balanceada:
  ```python
  r'<(article|section|div)[^>]+data-tema=["\']1378["\'][^>]*>(.*?)</\1>'
  ```
  (group 1 captura tag, `\1` referencia mesma tag no fechamento). OU mover para parser HTML real.
- **Impacto:** Snippet capturado pode ser fragmento errado → classificação incorreta. Não-determinístico — depende de estrutura HTML específica.

#### F-07-T8b: [HIGH] Faltam tests para httpx.TimeoutException/NetworkError
- **Localização:** `tests/integration/test_task8b_camada1_scraper.py` (todo)
- **Problema:** `_http_get_with_retry` captura `httpx.HTTPStatusError`, `httpx.ConnectError`, `httpx.TimeoutException`, `httpx.NetworkError` mas **nenhum teste exercita timeout ou network error**. Em prod, STJ pode estar lento/intermitente — esse path crítico nunca foi exercitado. Possível bug latente em retry timing ou exception chain preservation.
- **Evidência:** Tests cobrem apenas 200, 503, 404. Sem `httpx.TimeoutException`, `httpx.ConnectError`.
- **Recomendação:** Adicionar tests:
  ```python
  def test_scrape_timeout_retry_then_fail():
      with patch.object(httpx, "Client") as mock:
          mock.return_value.__enter__.return_value.get.side_effect = httpx.ReadTimeout("timeout")
          with pytest.raises(ScraperError):
              scrape_tema_1378("http://test.local/tema")

  def test_scrape_connect_error_retry_then_fail():
      # Similar com httpx.ConnectError
  ```
- **Impacto:** Bug em retry timing ou exception chain preservation só seria detectado em prod sob carga real.

#### F-08-T8b: [HIGH] `set_state(fail_count=0)` em scrape OK reseta histórico legítimo de fails
- **Localização:** `bloco_dataset/auto_trigger.py:74`
- **Problema:** Em `run_camada_1_check`, quando scrape retorna nivel ≠ verde (amarelo OU vermelho legítimo via julgamento/tese detectada), código chama `set_state(...fail_count=0...)`. Mas `fail_count` no state machine Task 7 representa **scrapes consecutivos que falharam**, não "scrapes consecutivos com nivel verde". Resetar para 0 quando scraper deu certo MAS detectou julgamento real é tecnicamente correto, mas há um bug sutil: se scraper falhar 3x (fail_count=2, vermelho via increment_fail), depois funcionar e detectar julgamento real (amarelo via scrape), `set_state(fail_count=0)` apaga histórico. Diagnóstico forense fica perdido. Comportamento esperado: fail_count zerar quando scraper opera com sucesso É correto, mas auditoria via state file perde info.
- **Evidência:** L74 hardcoded `fail_count=0`. Comparar com lógica clean: scraper success significa "scraper saudável", fail_count deveria zerar — mas o downgrade automatico vermelho→amarelo via scrape pula o protocolo `acknowledge()` Task 7 que esperava maintainer aciona. Fluxo de estado fica confuso.
- **Recomendação:** Decidir explicitamente: scraper success deve resetar fail_count? Se sim, documentar em docstring. Se vermelho-via-fails-consecutivas precisa ack manual mesmo após scraper voltar, **não** resetar via set_state — apenas atualizar nivel e mensagem deixando fail_count ortogonal. Atualmente isso é ambíguo.
- **Impacto:** Comportamento de transição entre estados inconsistente. Em pior caso, vermelho-via-fails (que requer SOP-005 manual) é silenciosamente downgraded para amarelo se scraper voltar e detectar julgamento real, pulando ack. Quebra invariante de Task 7.

---

### 🟡 MEDIUM (7)

#### F-09-T8b: [MED] RE_TESE_FIXADA limitado a `[^\n<]{20,300}` corta tese real
- **Localização:** `scraper_tema_1378.py:44-47`
- **Problema:** Pattern para a captura em qualquer newline OU `<`. Tese real STJ frequentemente tem múltiplas vírgulas, conjunções subordinadas, e ultrapassa 300 chars. HTML real pode ter `<br>`, `<strong>` no meio da tese, cortando captura.
- **Recomendação:** Aumentar limite superior (1000 chars) e considerar capturar até `</p>` ou similar separator. Ou pre-processar HTML para text plain via BeautifulSoup antes de regex.
- **Impacto:** Tese capturada truncada perde nuance jurídica importante. User vê fragmento inútil.

#### F-10-T8b: [MED] RE_JULGAMENTO_DATE só aceita formato DD/MM/YYYY
- **Localização:** `scraper_tema_1378.py:40-43`
- **Problema:** Pattern `r"julgamento\s+(?:pautado|marcado|previsto)\s+para\s+(\d{2}/\d{2}/\d{4})"`. STJ pode usar "1º de junho de 2026", "junho/2026", "15-06-2026", ISO 8601, "próxima sessão". Apenas DD/MM/YYYY é capturado.
- **Recomendação:** Múltiplos patterns alternativos com `|` OR-join. Se STJ render usar formato extenso, scraper hoje retorna verde quando deveria ser amarelo.
- **Impacto:** Falso negativo — scraper diz "verde sem alterações" quando há julgamento pautado mas formato data não casa.

#### F-11-T8b: [MED] `response.raise_for_status()` é dead code redundante
- **Localização:** `scraper_tema_1378.py:156`
- **Problema:** Lógica já trata 4xx (raise ScraperError L147) e 5xx (raise HTTPStatusError L151). `raise_for_status()` na L156 só é executado se `400 > status_code OR status_code >= 600`. Status 1xx (informational), 2xx (sucesso) e 3xx (redirect) — mas `follow_redirects=True` resolve 3xx automaticamente. Resta status >=600 que httpx nem aceita. **Code dead.**
- **Recomendação:** Remover linha 156 ou substituir por assert defensivo + comment explicativo.
- **Impacto:** Confusão para reviewers futuros. Não causa bug mas é code smell.

#### F-12-T8b: [MED] Audit entry write não-atomic em prod
- **Localização:** `bloco_dataset/auto_trigger.py:49-50`
- **Problema:** `f.write(json.dumps(entry) + "\n")` em modo `"a"` é syscall que pode ser interrompido teoricamente. Em POSIX, write < PIPE_BUF (4KB) em arquivo aberto com `O_APPEND` é atomic — entrada típica < 500 chars, então OK na prática Linux. Windows não garante atomicidade. Para audit chain HMAC posterior (Task 9), corrupção quebra verificação.
- **Evidência:** Append direto sem fsync explícito ou file locking.
- **Recomendação:** Usar `os.open(path, O_WRONLY | O_APPEND | O_CREAT, 0o600)` com `os.write(fd, line)` para POSIX (atomic se line < 4KB). Em Windows, considerar `portalocker` ou file lock. Adicionar `os.fsync(fd)` se durabilidade crítica.
- **Impacto:** Em raro cenário concurrent (múltiplos jobs APScheduler executando simultaneamente, OU sistema crashar mid-write), audit log corrompe. Verificação HMAC futura quebra.

#### F-13-T8b: [MED] Patterns CSS class hardcoded sem evidência empírica
- **Localização:** `scraper_tema_1378.py:63`
- **Problema:** `tema[-_](?:status|1378|repetitivo)` é palpite cego. STJ pode usar "TemaStatus" sem hífen, "tema_repetitivos" plural, "tema-page", "topic-1378", BEM-style "stj__tema--repetitivo". Sem evidência empírica do HTML real, lista hardcoded é sorte.
- **Recomendação:** Tech debt explícito documentado: TD-MVP-LEAN-08B-PATTERNS-EMPIRICAL — Eric extrai HTML real STJ + ajusta patterns iterativamente.
- **Impacto:** Estratégia 1 dead code em prod (combina com F-04).

#### F-14-T8b: [MED] Mock factory não simula retry success após falha intermitente
- **Localização:** `tests/integration/test_task8b_camada1_scraper.py:71-77`
- **Problema:** `_mock_client_factory(response)` retorna **mesmo response** em todas as chamadas `.get()`. Não há test "503 → 503 → 200" (retry success). Cenário real de resiliência (falha intermitente seguida de recovery) não é testado.
- **Recomendação:** Adicionar mock side_effect com sequência:
  ```python
  client.get.side_effect = [
      _make_response(503), _make_response(503), _make_response(200, HTML_CSS_CLASS)
  ]
  ```
  Test explícito que retry funciona quando server eventualmente responde.
- **Impacto:** Bug em retry mecânica (ex: state não reset entre tentativas) não é exercitado.

#### F-15-T8b: [MED] Tests usam HTML sintético sem quirks reais
- **Localização:** Test file (todo)
- **Problema:** `HTML_CSS_CLASS` etc. são markup sintético idealizado. HTML real STJ provavelmente tem: encoding latin-1 ou UTF-8 com BOM, JS-rendered content (necessitando Selenium), cookies de sessão obrigatórios, charset declarado em meta tag, comentários HTML embedded, doctypes, diferentes estruturas por página (lista vs detalhe).
- **Recomendação:** Adicionar fixture realista: salvar HTML real do STJ como `tests/fixtures/stj_tema_1378_real.html` para teste contra HTML válido. Cobrir charset latin-1, BOM, elementos aninhados.
- **Impacto:** Defeitos de integração com encoding/JS-rendering só pegos em prod.

---

### 🟢 LOW (3)

#### F-16-T8b: [LOW] Tese truncada 200 chars perde semântica jurídica
- **Localização:** `scraper_tema_1378.py:108, 113`
- **Problema:** `tese_text[:200]` e `tese_text[:150]`. Teses STJ frequentemente têm 500+ chars com nuances importantes (subordinadas, exceções, condições).
- **Recomendação:** Aumentar limite para 1000 chars OU armazenar full text em campo separado (e mensagem mostra preview).
- **Impacto:** UX — user vê fragmento inútil.

#### F-17-T8b: [LOW] Logger sem trace level para parser strategy decisions
- **Localização:** `scraper_tema_1378.py:196, 201, 209`
- **Problema:** `log.info("estratégia X match nivel Y")` mas não detalha qual regex casou ou trecho HTML capturado. Debug em prod requer adicionar `log.debug(snippet[:200])`.
- **Recomendação:** Adicionar `log.debug` para snippets capturados + match groups.
- **Impacto:** Debugging "por que estratégia 3 retornou amarelo?" requer adição manual de logs.

#### F-18-T8b: [LOW] 4xx não diferenciados (401/403 vs 404)
- **Localização:** `scraper_tema_1378.py:146-149`
- **Problema:** Todo 4xx vira "ScraperError não-retentável". Mas 401 (auth necessária) é cenário operacional diferente de 404 (URL errada) ou 403 (UA bloqueado). Maintainer deveria receber diagnóstico diferenciado.
- **Recomendação:** Mensagem diferenciada conforme status code:
  ```python
  if response.status_code == 404:
      msg = f"HTTP 404 — URL não encontrada: {url} (verificar se URL STJ mudou)"
  elif response.status_code in (401, 403):
      msg = f"HTTP {response.status_code} — auth/UA bloqueado (verificar User-Agent ou cookies)"
  else:
      msg = f"HTTP {response.status_code} — não-retentável"
  ```
- **Impacto:** Diagnóstico em prod menos preciso. Maintainer perde tempo investigando.

---

## Recomendação consolidada

### Decisão de gate

**CONCERNS (não-bloqueante para merge se mitigações pré-deploy explícitas)**

### Mitigações obrigatórias antes de ativar scheduler em prod

| # | Finding | Ação | Owner | Prazo |
|---|---|---|---|---|
| 1 | F-01 placeholder URL | Confirmar URL STJ real + adicionar feature flag `ENABLE_TEMA_1378_AUTO_CHECK` | Eric | Pre-deploy |
| 2 | F-05 User-Agent ausente | Adicionar headers User-Agent + Accept-Language | Neo (~5min) | Antes merge OU tech debt MED |
| 3 | F-08 fail_count reset semântico | Decidir explicitamente comportamento + documentar OU corrigir lógica | Neo | Antes merge |

### Tech debts aceitáveis (não-bloqueantes)

| # | Finding | Justificativa de aceitar como debt |
|---|---|---|
| F-02, F-04, F-06, F-13 | Patterns parser sem evidência empírica | Validáveis quando URL real for testada; iteração natural pós-deploy |
| F-03 | Cross-tema contamination | Edge case — fix simples mas precisa entender HTML real STJ primeiro |
| F-07 | Faltam tests timeout/network | LOW priority — adicionar próxima sprint |
| F-09, F-10, F-11, F-12, F-14, F-15 | Refinamentos menores | Não-bloqueantes |
| F-16, F-17, F-18 | LOW improvements | Polish iterativo |

### Suite de tests pós-revisão

- Atual: 387 passed + 3 skipped baseline preservado ✅
- 13 tests T8b passam mas cobertura insuficiente em paths críticos (F-07, F-14)
- Recomendado adicionar 4 tests pré-merge: timeout, network error, retry success após falhas, HTML com encoding latin-1

### Próximo step sugerido

**Skill `LMAS:agents:dev`** (Neo) com escopo focado:
1. Implementar F-05 User-Agent (5 min, trivial)
2. Decidir F-08 comportamento (Eric ou Neo decide; documentar em docstring)
3. Demais findings → tech debts em `governance/TECH-DEBT.md` (criar se não existe) com classificação SEV

OU se Eric preferir merge primeiro + tech debts pós:
- Aceitar T8b como está com 18 findings registrados como tech debt
- Mitigação F-01 + F-05 obrigatória **antes** de habilitar scheduler em prod (feature flag default-off)

---

## Smith verdict (cynical)

> "Você construiu um relógio que mede tempo num planeta diferente. Funciona perfeitamente — em testes sintéticos. O HTML real do STJ vai te dizer outra história. Isso não é defeito do design — é defeito de não ter olhado o alvo antes de mirar.
>
> Eu não sou pago para impressionar com 50 findings — encontrei 18 reais. Um deles é catastrófico em produção (F-01). Sete são erros que se manifestarão na primeira corrida real (F-02 a F-08). Os outros são polish. Você tem boas escolhas: capa de chuva (User-Agent + URL real) antes de sair para a tempestade, e dois fixes de lógica (F-03, F-08). O resto pode esperar."

— Smith (canalizado por Oracle)

---

## Anexos

- Commits revisados: `d7a37c1`, `48e05ab`
- PR: https://github.com/Claudinoinsights/revisor-contratual/pull/2
- Suite baseline pós-T8b: 387 passed + 3 skipped
- Tempo de review: ~30min (analytical mode + cynical lens)
