---
type: design-spec
title: "Frontend Spec — FastAPI + HTMX + Jinja2 UI"
project: revisor-contratual
designer: "@ux-design-expert (Sati)"
date: "2026-05-05"
sprint: "Sprint 02 (UI redesign)"
status: ready-for-implementation
delegated_to: "@dev (Neo)"
references:
  - governance/orsheva-brandbook.html (tokens fonte)
  - bloco_interface/streamlit_tokens.css (CSS já extraído, reutilizar)
tags:
  - project/revisor-contratual
  - design-spec
  - frontend
  - sprint-02
---

# Frontend Spec — Revisor Contratual UI Web (FastAPI + HTMX + Jinja2)

> **Substitui:** Streamlit UI (bloco_interface/streamlit_app.py + streamlit_tokens.css)
> **Filosofia:** ferramenta de trabalho diário, cores Orsheva, **só ações** (sem texto explicativo)

---

## 1. Diretivas de design (Eric)

Após 3 iterações Streamlit, Eric rejeitou cada uma com a mesma diretiva refinada:

1. ✅ Cores Orsheva (laranja accent + neutros)
2. ✅ **Apenas ações do operador** — upload, configurar, revisar, ver resultado
3. ❌ Sem textos grandes, sem hero, sem panels informativos
4. ❌ Sem informações desnecessárias para o uso
5. ❌ Sem decoração brandbook (que é para landing, não para tool)

**Conclusão Sati:** Streamlit limita controle CSS profundo + força sidebar pesada + chrome customization é hack. Migração para **FastAPI + HTMX + Jinja2** dá controle total preservando filosofia LEAN do PRD.

---

## 2. Stack arquitetural

| Camada | Tecnologia | Porquê |
|---|---|---|
| Web framework | **FastAPI** | Já candidato no ecossistema Python; async nativo |
| Template engine | **Jinja2** | Já em deps; HTML real, sem build pipeline |
| Interatividade | **HTMX 2.0** | Partial updates declarativos; sem JS framework; 14KB CDN |
| CSS | Vanilla + tokens orsheva | Sem Tailwind/SASS; `:root` vars + classes funcionais |
| Server | **uvicorn[standard]** | ASGI; reload em dev |

### Dependências a adicionar em `pyproject.toml`

```toml
"fastapi>=0.115",
"uvicorn[standard]>=0.32",
"python-multipart>=0.0.20",  # multipart/form-data para upload
```

### Dependências a remover (cleanup)

```toml
# Streamlit não precisa mais:
"streamlit>=1.40",                 # → REMOVER
"streamlit-authenticator>=0.3.3",  # → REMOVER (não usado)
```

---

## 3. Estrutura de arquivos

```
bloco_interface/
├── __init__.py                    # existente — manter
├── cli.py                         # existente — manter
├── error_handler.py               # existente — manter
├── output.py                      # existente — manter
└── web/                           # ← NOVO MÓDULO
    ├── __init__.py
    ├── app.py                     # FastAPI app + routes
    ├── templates/
    │   ├── base.html              # layout root
    │   ├── index.html             # entry point (estado idle)
    │   └── partials/              # fragments para HTMX swap
    │       ├── idle.html          # form upload + revisar
    │       ├── processing.html    # pipeline 7 steps
    │       ├── verdict.html       # resultado + critérios
    │       └── history-item.html  # item de histórico (loop)
    └── static/
        ├── tokens.css             # tokens orsheva (cores + tipografia)
        ├── app.css                # styles funcionais
        └── htmx.min.js            # HTMX local (1 file, sem CDN dependency)
```

### REMOVER após migração

```
bloco_interface/streamlit_app.py        # → DELETE
bloco_interface/streamlit_tokens.css    # → DELETE (tokens migram para web/static/)
```

---

## 4. Comando para rodar

```bash
# Substitui: streamlit run bloco_interface/streamlit_app.py

uvicorn bloco_interface.web.app:app --port 8501 --reload
# OU
python -m bloco_interface.web  # se app.py tiver if __name__ == "__main__"
```

Adicionar entry point em `pyproject.toml`:

```toml
[project.scripts]
revisor = "bloco_interface.cli:main"
revisor-web = "bloco_interface.web.app:run"   # ← NOVO
```

---

## 5. Endpoints (FastAPI routes)

| Método | Path | Returns | HTMX behavior |
|---|---|---|---|
| `GET` | `/` | `index.html` (full page) | Initial page load |
| `POST` | `/revisar` | `partials/processing.html` | Form submit → swap workspace |
| `GET` | `/pipeline-stream` | SSE stream com 7 steps | `hx-ext="sse"` consume event-stream |
| `GET` | `/verdict` | `partials/verdict.html` | Trigger pós SSE complete |
| `POST` | `/reset` | `partials/idle.html` | Botão "Nova revisão" → swap workspace |
| `GET` | `/static/{file}` | Static files | CSS/JS |

### Mock data (Sprint 02 STORY UI-1 conecta pipeline real)

```python
MOCK_HISTORY = [
    {"name": "contrato-bb-45.pdf", "verdict": "hitl", "label": "HITL", "score": 78, "when": "12m"},
    {"name": "caixa-5829.pdf", "verdict": "aprovado-100", "label": "100", "score": 100, "when": "ontem"},
    {"name": "santander-1.pdf", "verdict": "rejeitado", "label": "REJ", "score": 65, "when": "3d"},
]

MOCK_VERDICT = {
    "filename": "contrato.pdf",
    "status": "hitl",
    "status_label": "Aprovado com risco",
    "aderencia": 78,
    "criterios": [
        {"tag": "C1", "score": 1.00},
        {"tag": "C2", "score": 0.50},
        {"tag": "C3", "score": 1.00},
    ],
}
```

---

## 6. Design tokens (CSS custom properties)

Reutilizar paleta Orsheva já extraída. **NÃO** criar nova — usar as que já tem em `streamlit_tokens.css` v3 (versão minimal).

### tokens.css (extract para web/static/tokens.css)

```css
:root {
  /* Paleta Or (laranja — accent primary) */
  --or-50: #FFF4EC;
  --or-500: #EE6B20;
  --or-600: #D45710;
  --or-700: #AC4408;

  /* Paleta Sh (azul — secondary, raro) */
  --sh-500: #2C5380;

  /* Neutros */
  --bg: #FAFAF8;
  --surface: #FFFFFF;
  --surface-2: #F5F4F0;
  --border: #E8E4DC;
  --border-strong: #C9C3B5;
  --text: #1A1816;
  --text-muted: #6B6457;
  --text-dim: #9A9082;

  /* Semânticos */
  --accent: var(--or-500);
  --accent-hover: var(--or-600);
  --accent-soft: var(--or-50);
  --success: #2C7A4D;
  --success-soft: #E8F4ED;
  --danger: #B43D3D;
  --danger-soft: #FBEAEA;

  /* Tipografia */
  --f-ui: "Manrope", "Inter", system-ui, sans-serif;
  --f-display: "Fraunces", Georgia, serif;
  --f-mono: "JetBrains Mono", ui-monospace, monospace;

  /* Sizing */
  --r-md: 6px;
  --r-lg: 10px;
}
```

---

## 7. Wireframe — 3 estados

### Estado IDLE (initial)

```
┌──────────────────────────────────────────────────────────┐
│ ⚖ Revisor                                                │  ← topbar 56px
├──────────────────────────────────────────────────────────┤
│                                                          │
│        ┌────────────────────────────────────┐            │
│        │                                    │            │
│        │   ⬆  PDF do contrato               │            │ ← upload card
│        │      drop ou clique                │            │
│        │                                    │            │
│        └────────────────────────────────────┘            │
│                                                          │
│        UF [BA]  Data [__/__/____]  Tier [Premium ▾]     │ ← form inline
│                                                          │
│        [ Revisar contrato → ]                            │ ← btn primary
│                                                          │
└──────────────────────────────────────────────────────────┘
              ↑ Sidebar (collapsed por default em mobile)
              ↓ Sidebar expandida (desktop)
┌─────────────────┐
│ HISTÓRICO       │
│ ───────         │
│ contrato-bb-45  │
│ HITL · 78% · 12m│
│ ───             │
│ caixa-5829      │
│ 100 · 100%·ontem│
│ ───             │
│ santander-1     │
│ REJ · 65% · 3d  │
└─────────────────┘
```

### Estado PROCESSING (após submit)

Workspace inteiro é substituído (HTMX swap target=`#workspace`).

```
┌──────────────────────────────────────────────────────────┐
│ ⚖ Revisor                                                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   Analisando contrato.pdf                                │
│                                                          │
│   ████████░░░░░░░  4/7                                  │ ← progress bar
│                                                          │
│   ✓ Parsing PDF                                          │
│   ✓ Cálculo Decimal                                      │ ← lista vertical
│   ✓ BACEN SGS                                            │
│   ✓ Vault busca                                          │   verde = done
│   ○ Personas              ← active (laranja, pulsa)      │   laranja = active
│   · Juiz                                                 │   cinza = pending
│   · Audit log                                            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Estado RESULT (após pipeline complete)

```
┌──────────────────────────────────────────────────────────┐
│ ⚖ Revisor                                                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   ┌────────────────────────────────────────────┐         │
│   │ Aprovado com risco                    78%  │         │ ← Fraunces
│   │ ─────────                                  │         │
│   │ ┌──────┬──────┬──────┐                    │         │
│   │ │ C1   │ C2   │ C3   │                    │         │ ← critérios
│   │ │ 1.00 │ 0.50 │ 1.00 │                    │         │
│   │ └──────┴──────┴──────┘                    │         │
│   └────────────────────────────────────────────┘         │
│                                                          │
│   [ Ver tese ]  [ Exportar peça ]  [ Nova revisão ]     │ ← actions
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 8. HTMX flow

### Form submit (idle → processing)

```html
<form
  hx-post="/revisar"
  hx-target="#workspace"
  hx-swap="innerHTML"
  hx-encoding="multipart/form-data"
  hx-indicator="#spinner"
>
  <input type="file" name="pdf" accept="application/pdf" required>
  <input name="uf" placeholder="UF" maxlength="2">
  <input name="data" type="date">
  <select name="tier">
    <option value="premium">Premium</option>
    <option value="balanced">Balanced</option>
    <option value="lean">Lean</option>
  </select>
  <button type="submit">Revisar contrato →</button>
</form>
```

### Pipeline progress (SSE)

`partials/processing.html`:

```html
<div hx-ext="sse" sse-connect="/pipeline-stream" sse-swap="step">
  <h2>Analisando <code>{{ filename }}</code></h2>
  <div class="progress"><div id="progress-bar"></div></div>
  <div class="pipeline" id="pipeline-steps">
    {% for step in steps %}
      <div class="step pending" data-index="{{ loop.index0 }}">
        <span class="step-icon">·</span>
        <span class="step-name">{{ step }}</span>
      </div>
    {% endfor %}
  </div>
</div>

<script>
  document.body.addEventListener('htmx:sseMessage', function(e) {
    const data = JSON.parse(e.detail.data);
    if (data.done) {
      htmx.ajax('GET', '/verdict', { target: '#workspace', swap: 'innerHTML' });
    } else {
      const steps = document.querySelectorAll('.step');
      steps.forEach((s, i) => {
        s.classList.remove('pending', 'active', 'done');
        if (i < data.index) {
          s.classList.add('done');
          s.querySelector('.step-icon').textContent = '✓';
        } else if (i === data.index) {
          s.classList.add('active');
          s.querySelector('.step-icon').textContent = '○';
        } else {
          s.classList.add('pending');
        }
      });
      const pct = ((data.index + 1) / data.total) * 100;
      document.getElementById('progress-bar').style.width = pct + '%';
    }
  });
</script>
```

### Reset (result → idle)

```html
<button hx-post="/reset" hx-target="#workspace" hx-swap="innerHTML">
  Nova revisão
</button>
```

---

## 9. CSS components (web/static/app.css)

Aplicar tokens em classes funcionais (não mais Streamlit-specific overrides):

### Topbar

```css
.topbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 32px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}
.topbar .mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: var(--accent);
  color: white;
  border-radius: var(--r-md);
  font-weight: 700;
}
```

### Layout principal

```css
body {
  margin: 0;
  font-family: var(--f-ui);
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  line-height: 1.5;
}

.container {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px;
}
```

### Upload (drop zone)

```css
.upload {
  display: block;
  background: var(--surface);
  border: 1.5px dashed var(--border-strong);
  border-radius: var(--r-lg);
  padding: 40px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 200ms ease;
}
.upload:hover {
  background: var(--accent-soft);
  border-color: var(--accent);
  border-style: solid;
}
.upload input[type="file"] {
  display: none;
}
.upload .icon { font-size: 24px; margin-bottom: 8px; }
.upload .label { color: var(--text); font-weight: 500; }
.upload .hint { color: var(--text-muted); font-size: 12px; margin-top: 4px; }
```

### Form row inline

```css
.form-row {
  display: grid;
  grid-template-columns: 80px 1fr 1fr;
  gap: 12px;
  margin: 16px 0;
}

input[type="text"], input[type="date"], select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  background: var(--surface);
  font-family: var(--f-ui);
  font-size: 14px;
  color: var(--text);
}

input:focus, select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}
```

### Buttons

```css
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 18px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--r-md);
  font-family: var(--f-ui);
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: background 150ms ease;
}
.btn-primary:hover { background: var(--accent-hover); }
.btn-primary:disabled { background: var(--border); color: var(--text-dim); cursor: not-allowed; }

.btn-secondary {
  /* ... similar mas border + transparent */
}
```

### Pipeline steps

```css
.pipeline {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 16px;
}

.step {
  display: grid;
  grid-template-columns: 20px 1fr;
  gap: 12px;
  align-items: center;
  padding: 10px 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  font-size: 13px;
  transition: all 200ms ease;
}

.step.done { border-color: var(--success); background: var(--success-soft); }
.step.done .step-icon { color: var(--success); }
.step.active { border-color: var(--accent); background: var(--accent-soft); }
.step.active .step-icon { color: var(--accent); animation: pulse 1.5s ease infinite; }
.step.pending { color: var(--text-dim); }
.step.pending .step-icon { color: var(--text-dim); }

.step-icon { font-weight: 700; text-align: center; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
```

### Verdict card

```css
.verdict {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 24px;
}

.verdict-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
}

.verdict-status {
  font-family: var(--f-display);
  font-weight: 500;
  font-size: 24px;
  letter-spacing: -0.02em;
  line-height: 1.2;
}
.verdict-status.aprovado-100 { color: var(--success); }
.verdict-status.hitl { color: var(--accent); }
.verdict-status.rejeitado { color: var(--danger); }

.verdict-num {
  font-family: var(--f-display);
  font-weight: 500;
  font-size: 44px;
  line-height: 1;
  letter-spacing: -0.03em;
  color: var(--accent);
}

.criterios {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  overflow: hidden;
}

.criterio {
  padding: 14px 16px;
  border-right: 1px solid var(--border);
  background: var(--surface);
}
.criterio:last-child { border-right: none; }

.criterio-tag {
  display: inline-block;
  padding: 1px 6px;
  background: var(--accent-soft);
  color: var(--accent-hover);
  font-family: var(--f-mono);
  font-size: 10px;
  font-weight: 600;
  border-radius: 3px;
  margin-bottom: 6px;
}

.criterio-score {
  font-family: var(--f-display);
  font-weight: 500;
  font-size: 24px;
  letter-spacing: -0.02em;
}
```

### History (sidebar)

```css
.sidebar {
  position: fixed;
  left: 0; top: 56px; bottom: 0;
  width: 240px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 24px 20px;
  overflow-y: auto;
}

.sidebar h3 {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin: 0 0 12px;
}

.hist-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  margin-bottom: 6px;
  cursor: pointer;
}

.hist-item:hover {
  border-color: var(--border-strong);
  background: var(--surface-2);
}
```

---

## 10. Acceptance Criteria (todos MUST)

### Funcionalidade
- [ ] `GET /` retorna HTML com form upload + sidebar histórico (3 mock items)
- [ ] `POST /revisar` aceita multipart (pdf + uf + data + tier) e retorna processing.html
- [ ] `GET /pipeline-stream` emite 7 SSE events em ~3s (mock)
- [ ] HTMX automaticamente faz swap do workspace ao receber `done: true`
- [ ] `GET /verdict` retorna verdict.html com mock APROVADO_COM_RISCO_HITL 78%
- [ ] `POST /reset` retorna idle.html (volta ao estado inicial)
- [ ] Static files servidos via `/static/*`

### Visual
- [ ] **Apenas 1 viewport sem scroll** em monitor 1080p (estado idle)
- [ ] Cores Orsheva: laranja `#EE6B20` em mark + botão primário + accent + states
- [ ] Tipografia: Manrope corpo + Fraunces APENAS em verdict status/score/criterios
- [ ] Zero texto explicativo (sem panels "privacidade", "latência", "como funciona")
- [ ] Sidebar histórico com 3 mock items + badges de veredito

### Quality
- [ ] Sem dependências JS externas além de HTMX (que pode ser local)
- [ ] CSS organizado: `tokens.css` (vars) + `app.css` (classes funcionais)
- [ ] Suite testes 232/1 não quebra (UI nova é separada)

### Cleanup
- [ ] `bloco_interface/streamlit_app.py` removido
- [ ] `bloco_interface/streamlit_tokens.css` removido
- [ ] Deps `streamlit` e `streamlit-authenticator` removidas de pyproject.toml

### Deploy
- [ ] `uvicorn bloco_interface.web.app:app --port 8501` levanta sem erro
- [ ] HTTP 200 em `/`, HTTP 200 em assets
- [ ] HTMX presente em DevTools network tab
- [ ] Form submit funciona end-to-end (idle → processing → result → reset)

---

## 11. Out of scope (Sprint 02 STORY UI-1)

- Conectar `/revisar` ao pipeline real `bloco_workflow.pipeline.revisar_contrato`
- Substituir mock verdict por `VeredictoJuiz` real
- Histórico real consumindo `audit.jsonl`
- Auth (streamlit-authenticator vai virar fastapi auth quando necessário)
- Botões "Ver tese" / "Exportar peça" / "Audit log" funcionais

---

## 12. Estimativa

- **Phase A** (deps + estrutura): 10 min
- **Phase B** (templates + CSS): 30 min
- **Phase C** (routes + HTMX): 30 min
- **Phase D** (cleanup Streamlit): 5 min
- **Phase E** (validate + commit): 10 min

**Total: ~85 min** autônomo execução por Neo.

---

## 13. Risk + mitigation

| Risco | Mitigação |
|---|---|
| HTMX SSE complexo | Fallback: HTMX polling (`hx-trigger="every 500ms"`) |
| FastAPI multipart issues | python-multipart deps obrigatória; validar com curl |
| CSS grid não funciona em mobile | Media query @max-width 720px → 1 coluna |
| Suite testes quebra | UI é separada; suite atual não toca em web/ |

---

*Spec entregue por Sati (sessão 84) · pronto para handoff Neo*
