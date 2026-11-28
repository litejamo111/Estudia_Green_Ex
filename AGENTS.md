# Contexto para agentes — Predicta (Greenex)

Producto: dashboard de priorización y riesgo de deserción sobre datos **de prueba** (corte 2026-10-31).
Regla dura: nunca presentar cifras como reales de Green Services. La TRM es sintética.

## Estructura
- `backend/` pipeline (`pipeline_datos.py`), motor (`motor_decisiones.py`), API opcional (`api.py`). Solo stdlib para el pipeline/motor.
- `data/entrada/` CSV de prueba (no editar a mano) · `data/salidas/` artefactos generados (no editar a mano).
- `frontend/` sitio estático (`index.html` + `assets/`), sin build ni dependencias.
- `deploy/` `build.sh`, `dns.sh`, notas de deploy · `.github/workflows/pages.yml`.
- `docs/` documentación, plantillas, validación y ejemplos.

## Comandos
```bash
python backend/predicta.py ingesta   # pipeline + motor -> data/salidas
bash deploy/build.sh                 # -> _site
python -m http.server --directory _site 8099
```

## Reglas
- Rutas relativas en el frontend (`data/...`, `assets/...`): el sitio se sirve desde la raíz del subdominio.
- No commitear `_site/` ni secretos.
- Cambios de umbrales: `docs/documentacion/parametros_prueba.json`, nunca hardcodeados.
