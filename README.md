# Predicta

Dashboard accionable de operaciones: convierte ventas, compras, TRM y base instalada en
**una lista diaria de a quién llamar, por qué y qué ofrecer**.

- **Demo:** https://predicta.jdlforge.dev
- **API:** https://predicta.jdlforge.dev/api/docs · `GET /api/salud`
- **Datos:** de prueba (corte 2026-10-31). No son cifras reales de Green Services.

## Cómo funciona

```
data/entrada/*.csv ──► backend/pipeline_datos.py ──► data/salidas/datos_unificados.csv
                                  │
                                  ▼
                     backend/motor_decisiones.py  (modelo + reglas)
                                  │
                                  ▼
                  data/salidas/*.json ──► frontend/ (estático)  y  API (opcional)
```

- Modelo: logística o gradient boosting, entrenados en el build; se elige por top-20 en validación (sklearn es opcional, hay respaldo en stdlib).
- La prioridad de seguimiento es una regla transparente; el riesgo es una probabilidad.
- `backend/pruebas.py` ejecuta 9 pruebas de aceptación y deja evidencia en
  `docs/validacion/pruebas_ejecutadas.md`; el CI falla si alguna no pasa.

## Comandos

```bash
python backend/predicta.py ingesta   # pipeline + motor -> data/salidas
python backend/pruebas.py            # 9 pruebas de aceptación
bash deploy/build.sh                 # ensambla _site
python -m http.server --directory _site 8099
# API local: pip install -r backend/requirements.txt && python backend/predicta.py api
```

## Estructura

| Carpeta | Contenido |
|---|---|
| `backend/` | pipeline, motor, API opcional (FastAPI), pruebas |
| `data/entrada/` | CSV de prueba (no editar a mano) |
| `data/salidas/` | artefactos generados (JSON/CSV) |
| `frontend/` | sitio estático sin dependencias |
| `deploy/` | build, DNS, GCP (`docker-compose`, Caddy, bootstrap, autodeploy) |
| `docs/` | documentación del reto, plantillas, validación y guion de pitch |

## Despliegue

- **GitHub Pages:** push a `main` → workflow `deploy-pages` (corre pruebas + build).
- **VM/GCP:** `deploy/gcp/QUICK.md`; autodeploy cada 2 min tras `deploy/gcp/autodeploy.sh`.
- **Render:** `render.yaml` (alternativa gestionada para la API).

## Límites declarados

Datos de práctica; TRM sintética; sin trazabilidad compra-venta (no hay margen contable);
la prioridad alta indica revisar, no contactar automáticamente.
