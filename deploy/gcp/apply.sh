#!/usr/bin/env bash
# Aplica el estado de origin/main: imagen, artefactos y sitio. Lo llama el timer.
set -euo pipefail
cd /opt/predicta
COMPOSE="docker compose -f deploy/gcp/docker-compose.yml"

$COMPOSE build
# Una sola pasada dentro del contenedor: pipeline + motor + pruebas + artefactos
$COMPOSE run --rm -T api python backend/predicta.py ingesta
bash deploy/build.sh
$COMPOSE up -d
