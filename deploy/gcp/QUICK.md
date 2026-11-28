# GCP → VM para Predicta

## 1. Crear la VM
```bash
export PROYECTO=tu-proyecto
gcloud config set project $PROYECTO
gcloud services enable compute.googleapis.com

# Opción A — free tier (1 GB RAM, 30 GB): alcanza para API + dashboard, NO para LLM
gcloud compute instances create predicta \
  --zone=us-central1-a --machine-type=e2-micro \
  --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB --tags=http-server,https-server

# Opción B — para LLM local (Qwen 0.5B en CPU): 4 GB
# --machine-type=e2-medium
```

## 2. IP fija + firewall
```bash
gcloud compute addresses create predicta-ip --region=us-central1
gcloud compute addresses describe predicta-ip --region=us-central1 --format='value(address)'
gcloud compute firewall-rules create predicta-web \
  --allow=tcp:80,tcp:443 --target-tags=http-server,https-server
```

## 3. DNS (cambio de cutover)
En Cloudflare borra el CNAME actual de `predicta` y crea:
```
Tipo: A   Nombre: predicta   Valor: <IP fija>   Proxy: OFF
```
`.dev` está en HSTS preload: no hay HTTP, Caddy necesita el certificado antes de servir.
Deja el registro viejo (CNAME a github.io) hasta que la VM responda, luego lo cambias.

## 4. Bootstrap (una línea)
```bash
gcloud compute ssh predicta --zone=us-central1-a --command='curl -fsSL https://raw.githubusercontent.com/litejamo111/Estudia_Green_Ex/main/deploy/gcp/bootstrap.sh | bash'
```

## 5. Verificación
```bash
curl -sI https://predicta.jdlforge.dev | head -1     # 200
curl -s  https://predicta.jdlforge.dev/api/salud     # {"estado":"ok",...}
curl -sI https://predicta.jdlforge.dev/api/docs      # Swagger
```

## Notas
- Firewall de GCP: por defecto el tráfico entre servicios internos ya está permitido; Caddy habla con `api:8000` por la red de Docker.
- Costo: e2-micro free tier (1 egress GB/mes). e2-medium ≈ US$25/mes. Apaga con `gcloud compute instances stop predicta --zone=us-central1-a`.
- SQLite en la VM sí persiste (disco real), a diferencia de Render free.
- `data/salidas` se regenera en cada arranque en ~2,5 s; no necesitas volumen para eso, solo para escrituras futuras.
