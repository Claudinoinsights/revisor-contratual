# Landing Institucional — Revisor Contratual

Página estática de marketing/explicação para `claudinoinsights.com/revisor-contratual`.

## Princípio LGPD

**Esta landing NÃO processa dados de contratos.** Apenas explica o produto + fornece links para download/clone do código. Preserva NFR-LGPD-01 ("PDF nunca sai da máquina") porque nada é processado server-side.

## Conteúdo

| Arquivo | Descrição |
|---|---|
| `index.html` | Página única — hero + features + princípios + stack + download |
| `tokens.css` | Design tokens orsheva-brandbook (subset focado) |
| `styles.css` | Estilos da landing (orsheva applied) |

## Deploy — Cloudflare Pages

### Setup inicial (1×)

```bash
# Via Cloudflare Dashboard:
# 1. Pages → Create project → Connect to Git → Claudinoinsights/revisor-contratual
# 2. Build settings:
#    - Build command: (none — static)
#    - Build output directory: landing
#    - Root directory: /
# 3. Environment variables: (none)
# 4. Save and deploy
```

### Routing claudinoinsights.com/revisor-contratual

```bash
# Via Cloudflare Dashboard ou Worker:
# - Custom domain: claudinoinsights.com
# - Path-based routing: /revisor-contratual/* → revisor-contratual landing
# - Redirect /revisor-contratual → /revisor-contratual/ (trailing slash)
```

Alternativa via Cloudflare Worker:

```javascript
// _routes.json (ou Worker bindings)
{
  "version": 1,
  "include": ["/revisor-contratual/*"],
  "exclude": []
}
```

### Local preview

```bash
# Python http.server (any port livre)
cd landing && python -m http.server 8080
# Abrir: http://localhost:8080
```

## Roadmap

- [ ] Animations on scroll (Intersection Observer + CSS animations)
- [ ] Dark mode toggle
- [ ] Demo iframe Streamlit (após deploy de instância demo)
- [ ] i18n (EN para audiência internacional, opcional)
- [ ] Form de contato/lista de espera (sem processamento de dados sensíveis)
