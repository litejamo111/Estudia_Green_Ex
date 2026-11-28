#!/usr/bin/env bash
# Aplica cada push a main en la VM, sin entrar por SSH.
# Uso: sudo bash deploy/gcp/autodeploy.sh
set -euo pipefail
cat >/etc/systemd/system/predicta-deploy.service <<'UNIT'
[Unit]
Description=Predicta autodeploy
[Service]
Type=oneshot
WorkingDirectory=/opt/predicta
ExecStartPre=/usr/bin/git pull --ff-only
ExecStartPre=/usr/bin/python3 backend/predicta.py ingesta
ExecStartPre=/bin/bash deploy/build.sh
ExecStart=/usr/bin/docker compose -f deploy/gcp/docker-compose.yml up -d --build --force-recreate
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
echo "autodeploy activo: systemctl status predicta-deploy.timer"
