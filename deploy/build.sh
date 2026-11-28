#!/usr/bin/env bash
# Ensambla _site: frontend + salidas del motor. Uso: bash deploy/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf _site
mkdir -p _site/data
cp -r frontend/. _site/
touch _site/.nojekyll
cp data/salidas/*.json _site/data/
cp data/salidas/resumen_clientes.csv _site/data/ 2>/dev/null || true
echo "_site listo ($(du -sh _site | cut -f1))"
