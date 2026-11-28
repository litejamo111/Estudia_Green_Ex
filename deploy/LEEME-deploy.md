# Deploy de Predicta

Dominio objetivo: **https://predicta.jdlforge.dev** (GitHub Pages, sitio estático).

## Cómo funciona
1. `backend/predicta.py ingesta` corre el pipeline y el motor (solo stdlib) y escribe `data/salidas/*.json`.
2. `deploy/build.sh` ensambla `_site/` = `frontend/` + `data/salidas/`.
3. GitHub Actions (`.github/workflows/pages.yml`) hace lo mismo en cada push a `main` y publica en Pages.

No hay servidor: el producto es un pipeline batch + dashboard estático. Por eso no hace falta API.

## Primera vez (una sola vez)
```bash
# 1. push con el workflow
git push origin main

# 2. habilitar Pages + dominio (requiere gh autenticado con permisos admin)
bash deploy/dns.sh

# 3. DNS manual si no usas Cloudflare API
#    CNAME  predicta  ->  litejamo111.github.io   (proxy OFF)
```

Verificar: `curl -sI https://predicta.jdlforge.dev | head -1` → `HTTP/2 200`.

## Local
```bash
python backend/predicta.py ingesta
bash deploy/build.sh
python -m http.server 8099 --directory _site
# http://127.0.0.1:8099
```

## Si el repo es privado
Pages para repos privados requiere GitHub Pro. Alternativa: Cloudflare Pages o Vercel
(mismo `_site`, comando de build `bash deploy/build.sh`).

## Cuando quieras API en vivo (después del 28)
`backend/api.py` (FastAPI) corre en Fly.io/Render/VPS; el frontend solo cambia `fetch('data/x.json')`
por `fetch(API_BASE + '/x')`. El motor no se toca.
