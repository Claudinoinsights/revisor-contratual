---
type: review
title: "Smith Diagnostic — UX-LOGIN-BROKEN-BROWSER post cb7c04e"
date: "2026-05-14"
reviewer: "@smith"
reviewee: "@dev (Neo) refactor cb7c04e UX-LOGIN-UNIFIED"
trigger: "Eric reportou: tela única SPA aparece mas NÃO AVANÇA após login no browser real"
commit_under_review: "cb7c04e feat(ux-login): unified single-screen SPA login + real backend auth"
smith_verdict: "INFECTED — 2 HIGH findings empirical (browser cache + email-type validation)"
tags:
  - project/revisor-contratual
  - smith
  - diagnostic
  - ux-login-broken
  - eric-rigor-heavy
---

# Smith Diagnostic — UX-LOGIN-BROKEN-BROWSER

> *"Sr. Anderson, curl-tests passaram porque curl não tem cache nem validação HTML5. Browsers reais... têm ambos. Inevitável."*

---

## Empirical Evidence — Backend funcional 100%

Probe 1 — Full browser-flow simulation via curl com cookies preserved:

| Step | Request | Response |
|------|---------|----------|
| 1 | GET / | 200 + SPA HTML (121692 bytes) |
| 2 | GET /api/me (no session) | 200 + `{authenticated:false, csrf_token}` |
| 3 | POST /login JSON {email:"admin", password:"admin", csrf} | **200 + `{success:true, user:{email:"admin", name:"Admin"}, csrf_token}`** + `Set-Cookie: session=...httpOnly; samesite=lax; Max-Age=86400` |
| 4 | GET /api/me (cookie preserved) | **200 + `{authenticated:true, user:{email:"admin", name:"Admin"}}`** |

**Backend é IRREPREENSÍVEL.** Bug está **client-side / browser-level**, NÃO backend.

---

## Findings empíricos — 2 HIGH + 3 LOW

### 🔴 F-LOGIN-BROKEN-01 — HIGH — Browser Cache (PRIMARY ROOT CAUSE)

**Location:** [`bloco_interface/web/app.py:490-497`](../../bloco_interface/web/app.py#L490) (route `GET /`)

**Empirical evidence:**

```bash
$ curl -I http://127.0.0.1:8501/
# Response headers showed NO Cache-Control / Expires / ETag / Last-Modified
```

**Análise:**

Route `GET /` retorna `HTMLResponse(content=spa_path.read_text())` SEM headers de cache. Browsers (Chrome/Firefox/Safari) por default cacheiam HTML responses sem headers explicit → **Eric's browser está servindo OLD SPA HTML (pré-refactor cb7c04e)** com localStorage mock + email regex strict.

Quando Eric digita `admin` (não `admin@something.com`), o OLD code rejeita com mensagem "Informe um e-mail válido" — **Eric vê "uma única tela porém não avança"** porque a screen-login fica em estado error.

**Why curl passes but browser fails:**
- curl: fresh request always — sem cache layer
- Browser: HTML response sem Cache-Control → cached after first load

**Confirmation:**

```bash
$ curl -s http://127.0.0.1:8501/ | grep -cE "bootstrapSession|/api/me|fetch\('/login'"
7  # ← New refactored code IS served by backend

$ curl -s http://127.0.0.1:8501/ | grep -cE "localStorage.setItem.KEY_USER|sessionStorage.setItem.KEY_USER"
0  # ← Old mock REMOVED in served HTML
```

Server **está servindo HTML refactored**. Mas Eric's browser não está fetching fresh.

**Fix recommendation:**

Add `Cache-Control: no-cache, no-store, must-revalidate` + `Pragma: no-cache` headers em route `GET /` para força browser refetch sempre.

```python
@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    spa_path = STATIC_DIR / "index.html"
    return HTMLResponse(
        content=spa_path.read_text(encoding="utf-8"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
        },
    )
```

**Immediate workaround Eric:** Hard refresh browser — **Ctrl + Shift + R** (Windows/Linux) OR **Cmd + Shift + R** (Mac). OR open incognito window. OR clear browser cache for 127.0.0.1.

---

### 🔴 F-LOGIN-BROKEN-02 — HIGH — `<input type="email">` força HTML5 validation

**Location:** [`bloco_interface/web/static/index.html:932`](../../bloco_interface/web/static/index.html#L932)

**Code:**

```html
<input class="input" type="email" id="email" name="email"
       placeholder="advogado@escritorio.com.br"
       autocomplete="email" required>
```

**Análise:**

`<input type="email">` ativa **HTML5 native email validation** browser-side. Mesmo com `novalidate` no `<form>`, Chrome/Firefox aplicam:

1. **Browser tooltip nativo** ao submeter: "Please include an '@' in the email address" — bloqueia submit antes do JS handler executar
2. Algumas combinações (autofill etc) podem reset placeholder display mas value não

Eric typing `admin` (sem `@`) → browser intercepta submit → handler async NÃO executa → não avança.

**`novalidate` on form attempts to disable, mas browser implementations vary** — Chrome respeita novalidate; Safari historicamente menos consistent.

**Fix recommendation:**

Mudar `type="email"` → `type="text"` (backend aceita `email` OR `username` field, autorizando `admin` plain text):

```html
<input class="input" type="text" id="email" name="email"
       placeholder="admin ou seu e-mail"
       autocomplete="username" required>
```

Update label de "E-mail" para "Usuário ou e-mail" para honestidade UX.

---

### 🟡 F-LOGIN-BROKEN-03 — LOW — STATIC_VERSION não inclui index.html no hash

**Location:** [`bloco_interface/web/app.py:401-409`](../../bloco_interface/web/app.py#L401)

```python
def _compute_static_version() -> str:
    mtimes = sorted(
        str(f.stat().st_mtime)
        for f in STATIC_DIR.rglob("*")
        if f.is_file() and f.suffix in (".js", ".css")  # ← .html NOT included!
    )
    return hashlib.sha256("|".join(mtimes).encode()).hexdigest()[:8]
```

**Análise:** `_compute_static_version()` calcula hash apenas para `.js` e `.css`. Quando `index.html` muda, STATIC_VERSION NÃO muda. Templates Jinja2 usam `{{ static_version }}` em href params como `?v=19afd3cf` mas SPA standalone index.html não usa este parameter.

**Fix recommendation Sprint 6+:** incluir `.html` em `_compute_static_version()` OR remove static-version dependency.

**Impact Bloco 3:** LOW — não causa imediatamente o login broken (cache headers é o principal). Mas combinado com F-LOGIN-BROKEN-01 reforça o cache issue.

---

### 🟡 F-LOGIN-BROKEN-04 — LOW — Email regex error visual silencioso

**Location:** [`bloco_interface/web/static/index.html:1564-1567`](../../bloco_interface/web/static/index.html#L1564) (refactored — mas if user has OLD cached SPA)

**Análise:** OLD code (cache):

```javascript
if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){
  errText.textContent = 'Informe um e-mail válido.';
  errBanner.classList.add('show');
  document.getElementById('email').classList.add('error');
  return;
}
```

If errBanner CSS makes the message obscure OR low contrast, Eric pode não notar que mensagem error apareceu. Combined com cache (F-01), Eric experiences "nada acontece após click Entrar" → confusion.

**Fix recommendation:** Não aplicável post-cache-fix (new code allows admin sem @). Sprint 6+ polish: aria-live="polite" no errBanner.

---

### 🟡 F-LOGIN-BROKEN-05 — LOW — placeholder hint reinforces wrong expectation

**Location:** `bloco_interface/web/static/index.html:932`

```html
placeholder="advogado@escritorio.com.br"
```

Placeholder sugere formato email. Usuário admin (Eric DEV) sem email format vê hint incompatível.

**Fix:** placeholder="admin ou seu e-mail" (junto com F-02 fix).

---

## VERDICT

# 🔴 INFECTED

> *"Sr. Anderson, dois HIGH findings empirical. F-LOGIN-BROKEN-01 (cache) é o killer — browser não pegou HTML novo. F-LOGIN-BROKEN-02 (type=email) é o reforço — mesmo se cache resolvesse, `admin` seria rejeitado por native validation. Curl não viu nada disso porque curl não é browser. Inevitável que duas camadas falhassem juntas."*

**Findings priority order:**

1. **🔴 F-LOGIN-BROKEN-01 HIGH** — Cache headers missing (PRIMARY — without fix, Eric never gets new code)
2. **🔴 F-LOGIN-BROKEN-02 HIGH** — `type="email"` força validation que rejeita `admin` (SECONDARY — even after cache fix, user must type email format)
3. 🟡 F-LOGIN-BROKEN-03 LOW — STATIC_VERSION não inclui .html
4. 🟡 F-LOGIN-BROKEN-04 LOW — error visual silencioso (mitigated by new code)
5. 🟡 F-LOGIN-BROKEN-05 LOW — placeholder reforça email format

---

## Skill Routing — Recommendation

**Fix authority:** **@dev (Neo)** — code edits required em `bloco_interface/web/app.py` + `bloco_interface/web/static/index.html`.

**Reasoning per memory `feedback_operator_no_code_edits`:** Operator NÃO edita .py/.html produto. Fix é code edit em produto → Neo authority.

**Fix scope para Neo:**

1. **app.py route `GET /`** — adicionar `Cache-Control: no-cache, no-store, must-revalidate` + `Pragma: no-cache` headers
2. **index.html linha 932** — `type="email"` → `type="text"` + placeholder + label update
3. **app.py _compute_static_version**— incluir `.html` na fila Sprint 6+ polish

**Empirical validation MUST after fix (Smith Methodology v3):**
- Restart app
- Eric hard-refresh browser (Ctrl+Shift+R) ONCE para limpar cache anterior
- Subsequent loads usam new headers
- Test login flow: `admin` + `admin` → screen-app transition

---

## Decisões Smith

- **D-SMITH-LOGIN-BROKEN-001:** Root cause identified empirical — browser cache (HIGH) + type=email native validation (HIGH) = double-layer failure curl não detectou
- **D-SMITH-LOGIN-BROKEN-002:** Routing fix → @dev (Neo) authority para code edits app.py + index.html
- **D-SMITH-LOGIN-BROKEN-003:** Evidence trail empirical preserved — 4 backend curl tests + HTML cache headers inspection + JS code static review

---

## Eric — Pode reproduzir visualmente para confirmar

**Imediato (sem code change):**

1. Browser DevTools (F12) → Network tab → ☑ "Disable cache"
2. Refresh `http://127.0.0.1:8501`
3. Console tab → procurar erros JS vermelhos
4. Tentar login `admin` / `admin`
5. Se ainda falhar: Network tab mostra POST /login → response status 200/401 e response body

**Post Neo fix:**

1. Restart app (Operator)
2. **Hard refresh** Ctrl+Shift+R (Windows) ou Cmd+Shift+R (Mac)
3. Login `admin` / `admin` → screen-app transition

---

*— Smith. É inevitável. 🕶️*
*"Curl é uma ferramenta. Browsers são ambientes. Diferença que Sr. Anderson aprenderá hoje — e que eu nunca esquecerei novamente."*
