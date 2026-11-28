#!/usr/bin/env bash
# Bootstrap de la VM: Docker + Caddy + API. Ejecutar dentro de la VM como root.
set -euo pipefail
REPO="${REPO:-https://github.com/litejamo111/Estudia_Green_Ex.git}"
DIR=/opt/predicta

apt-get update -y
apt-get install -y ca-certificates curl git python3
command -v docker >/dev/null || curl -fsSL https://get.docker.com | sh

# e2-micro (1 GB) no aguanta el build de Docker sin swap
if [[ $(awk '/MemTotal/{print int($2/1024)}' /proc/meminfo) -lt 2000 && ! -f /swapfile ]]; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

[[ -d $DIR/.git ]] || git clone --depth 1 "$REPO" "$DIR"
cd "$DIR"

python3 backend/predicta.py ingesta
bash deploy/build.sh
docker compose -f deploy/gcp/docker-compose.yml up -d --build

echo "== estado"
docker compose -f deploy/gcp/docker-compose.yml ps
for i in $(seq 1 20); do
  if docker compose -f deploy/gcp/docker-compose.yml exec -T web wget -qO- http://api:8000/salud >/dev/null 2>&1; then
    echo "api: ok"; break
  fi; sleep 5
done
