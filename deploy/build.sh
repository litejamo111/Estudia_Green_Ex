#!/usr/bin/env bash
# Ensambla _site: frontend + salidas del motor. Uso: bash deploy/build.sh
# No borra el directorio _site: conserva el inodo para que el bind-mount de Caddy siga válido.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p _site
find _site -mindepth 1 -maxdepth 1 -exec rm -rf {} +
mkdir -p _site/data
cp -r frontend/. _site/
touch _site/.nojekyll
cp data/salidas/*.json _site/data/
cp data/salidas/resumen_clientes.csv _site/data/ 2>/dev/null || true
printf '{"version":"1.0.0","commit":"%s","build":"%s"}' \
  "$(git rev-parse --short HEAD 2>/dev/null || echo local)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > _site/version.json
echo "_site listo ($(du -sh _site | cut -f1))"
