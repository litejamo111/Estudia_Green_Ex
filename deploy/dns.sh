#!/usr/bin/env bash
# Spin-up de predicta.jdlforge.dev (GitHub Pages + DNS).
# Requiere: gh autenticado. Opcional: CF_API_TOKEN + CF_ZONE_ID para Cloudflare.
# Uso: bash deploy/dns.sh
set -euo pipefail
# Carga .env (ignorado por git) si existe
if [[ -f .env ]]; then set -a; . ./.env; set +a; fi
DOMINIO="${DOMINIO:-predicta.jdlforge.dev}"
REPO="${REPO:-litejamo111/Estudia_Green_Ex}"
TARGET="${TARGET:-litejamo111.github.io}"

echo "== 1. Habilitar Pages con GitHub Actions en $REPO"
gh api -X POST "repos/$REPO/pages" -f "build_type=workflow" >/dev/null 2>&1 \
  || gh api -X PUT "repos/$REPO/pages" -f "build_type=workflow" >/dev/null 2>&1 \
  || echo "   (Pages ya estaba habilitado o requiere permisos admin)"

echo "== 2. Fijar dominio personalizado"
gh api -X PUT "repos/$REPO/pages" -f "cname=$DOMINIO" >/dev/null 2>&1 \
  && echo "   cname=$DOMINIO" || echo "   Ajusta el dominio manualmente en Settings > Pages"

echo "== 3. DNS"
if [[ -n "${CF_API_TOKEN:-}" ]]; then
  if [[ -z "${CF_ZONE_ID:-}" ]]; then
    CF_ZONE_ID=$(curl -s "https://api.cloudflare.com/client/v4/zones?name=${CF_ZONE_NAME:-jdlforge.dev}" \
      -H "Authorization: Bearer $CF_API_TOKEN" \
      | python3 -c 'import sys,json;r=json.load(sys.stdin).get("result") or [];print(r[0]["id"] if r else "")')
    [[ -z "$CF_ZONE_ID" ]] && { echo "   No pude resolver CF_ZONE_ID (¿token sin permiso Zone:Read?)"; exit 1; }
    echo "   zone_id=$CF_ZONE_ID"
  fi
  API="https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records"
  ID=$(curl -s -H "Authorization: Bearer $CF_API_TOKEN" "$API?type=CNAME&name=$DOMINIO" \
        | python3 -c 'import sys,json;r=json.load(sys.stdin)["result"];print(r[0]["id"] if r else "")')
  BODY="{\"type\":\"CNAME\",\"name\":\"$DOMINIO\",\"content\":\"$TARGET\",\"proxied\":false,\"ttl\":1}"
  if [[ -n "$ID" ]]; then
    curl -s -X PUT "$API/$ID" -H "Authorization: Bearer $CF_API_TOKEN" \
      -H "Content-Type: application/json" --data "$BODY" >/dev/null && echo "   CNAME actualizado -> $TARGET"
  else
    curl -s -X POST "$API" -H "Authorization: Bearer $CF_API_TOKEN" \
      -H "Content-Type: application/json" --data "$BODY" >/dev/null && echo "   CNAME creado -> $TARGET"
  fi
else
  cat <<TXT
   Crea este registro en tu proveedor de DNS (Cloudflare/Namecheap/Route53):
     Tipo:  CNAME
     Nombre: predicta
     Valor:  $TARGET
     Proxy:  DESACTIVADO (importante: GitHub debe poder emitir el certificado)
   Luego espera 5-30 min; GitHub emite el certificado TLS automáticamente.
TXT
fi

echo "== 4. Verificación"
echo "   curl -sI https://$DOMINIO | head -1"
