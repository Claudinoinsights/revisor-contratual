# Landing Institucional — Revisor Contratual

Página estática para deploy em `claudinoinsights.com/revisor-contratual` (ou subdomínio dedicado).

## ⚙️ Setup pronto para Cloudflare Pages

Tudo já está configurado neste diretório:

| Arquivo | Função |
|---|---|
| `index.html` | Landing single-page (7 seções) |
| `tokens.css` | Design tokens orsheva-brandbook |
| `styles.css` | Estilos completos |
| `_headers` | Security headers + cache rules |
| `_redirects` | Path routing rules |
| `robots.txt` | SEO |

## 🚀 Deploy Cloudflare Pages (3 cliques no dashboard)

### 1. Conectar repo

```
Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect to Git
→ Selecionar: Claudinoinsights/revisor-contratual
→ Branch: main
```

### 2. Build settings

```
Framework preset: None
Build command: (deixar vazio — site estático)
Build output directory: landing
Root directory (advanced): /
```

### 3. Deploy

```
Click "Save and Deploy"
→ Aguarda ~30s
→ URL gerada: https://revisor-contratual.pages.dev (ou similar)
```

## 🌐 Custom domain — `claudinoinsights.com/revisor-contratual`

⚠️ **Pré-requisito:** `claudinoinsights.com` precisa estar no Cloudflare DNS (orange cloud proxy). **Diagnóstico atual:** o domínio NÃO está em CF (IP `91.108.126.149` é VPS direto).

### Opção A — Mover DNS de claudinoinsights.com para Cloudflare

1. Cloudflare Dashboard → Add Site → `claudinoinsights.com`
2. Cloudflare gera nameservers (ex: `nina.ns.cloudflare.com`)
3. Atualizar nameservers no registrar (GoDaddy, Registro.br, etc)
4. Aguardar propagação (~24h)
5. Cuidado: app `/painel` pode precisar de reconfig (origin server precisa permanecer acessível)

### Opção B — Subdomínio dedicado (recomendado, sem mover DNS principal)

Se DNS principal está fora de CF mas você quer subdomínio em CF:

1. Adicionar zona separada para subdomínio (ex: `revisor.claudinoinsights.com`)
2. Apontar registrar do subdomínio para CF nameservers
3. Em Pages → Custom domains → Add: `revisor.claudinoinsights.com`

### Opção C — Reverse proxy no VPS atual

Configurar nginx/caddy no VPS `91.108.126.149`:

```nginx
location /revisor-contratual/ {
    proxy_pass https://revisor-contratual.pages.dev/;
    proxy_set_header Host revisor-contratual.pages.dev;
    proxy_ssl_server_name on;
}
```

## 🧪 Local preview

```bash
# Servidor estático Python
cd landing && python -m http.server 8080
# Abrir: http://localhost:8080
```

## 📐 Design system

Extraído de `governance/orsheva-brandbook.html`:

- **Paleta Or:** `#EE6B20` (primary accent)
- **Paleta Sh:** `#2C5380` (secondary)
- **Neutros:** pearl `#F8F4ED`, bone, stone, ink
- **Tipografia:** Fraunces (display) · Manrope (body) · JetBrains Mono (code)
- **Conceito:** Iluminar · Estruturar · Consolidar
