#!/usr/bin/env bash
# Instala el autodeploy. Uso: sudo bash deploy/gcp/autodeploy.sh [--now]
# El unit solo sincroniza el repo y llama a apply.sh (que puede cambiar sin reinstalar).
set -euo pipefail

cat >/etc/systemd/system/predicta-deploy.service <<'UNIT'
[Unit]
Description=Predicta autodeploy
[Service]
Type=oneshot
WorkingDirectory=/opt/predicta
ExecStart=/usr/bin/git fetch --quiet origin main
ExecStart=/usr/bin/git reset --hard origin/main
ExecStart=/bin/bash /opt/predicta/deploy/gcp/apply.sh
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
echo "autodeploy instalado (cada 2 min) · sincroniza con reset --hard origin/main"

if [[ "${1:-}" == "--now" ]]; then
  systemctl start predicta-deploy.service
  journalctl -u predicta-deploy.service -n 15 --no-pager || true
fi
