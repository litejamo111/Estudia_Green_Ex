#!/usr/bin/env bash
# Aplica cada push a main en la VM. Uso: sudo bash deploy/gcp/autodeploy.sh [--now]
# El pipeline corre DENTRO del contenedor para que el modelo sea idéntico al del CI.
set -euo pipefail

cat >/etc/systemd/system/predicta-deploy.service <<'UNIT'
[Unit]
Description=Predicta autodeploy
[Service]
Type=oneshot
WorkingDirectory=/opt/predicta
ExecStart=/usr/bin/git pull --ff-only
ExecStart=/usr/bin/docker compose -f deploy/gcp/docker-compose.yml build
ExecStart=/usr/bin/docker compose -f deploy/gcp/docker-compose.yml run --rm -T api python backend/predicta.py ingesta
ExecStart=/usr/bin/docker compose -f deploy/gcp/docker-compose.yml run --rm -T api python backend/pruebas.py
ExecStart=/bin/bash deploy/build.sh
ExecStart=/usr/bin/docker compose -f deploy/gcp/docker-compose.yml up -d --force-recreate
UNIT
cat >/etc/systemd/system/predicta-deploy.timer <<'UNIT'
[Unit]
Description=Revisa cambios de Predicta cada 2 minutos
[Timer]
OnBootSec=2min
OnUnitActiveSec=2min
[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload
systemctl enable --now predicta-deploy.timer
echo "autodeploy activo (cada 2 min)"

if [[ "${1:-}" == "--now" ]]; then
  systemctl start predicta-deploy.service
  journalctl -u predicta-deploy.service -n 12 --no-pager || true
fi
