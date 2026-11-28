"""Predicta - API del dashboard accionable sobre los artefactos del motor.

Uso:
    python3.11 backend/api.py
    python3.11 -m uvicorn --app-dir backend api:app --host 127.0.0.1 --port 8000

No requiere base de datos: lee los JSON de data/salidas y los recarga cuando cambian.
La ingesta se dispara con POST /ingesta (o cron sobre backend/ingesta.py).
"""
from pathlib import Path
from typing import Optional
import json
import os
import subprocess
import sys
import threading
import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

RAIZ = Path(__file__).resolve().parents[1]
SALIDAS = RAIZ / "data" / "salidas"

app = FastAPI(
    title="Predicta API",
    version="0.1.0",
    description="Deserción y recompra por producto",
    # Detrás de Caddy con /api: Swagger debe pedir /api/openapi.json
    root_path=os.environ.get("ROOT_PATH", ""),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache = {}
_ingesta_lock = threading.Lock()
_ultima_ingesta = {"estado": "nunca"}


def datos(nombre):
    ruta = SALIDAS / nombre
    if not ruta.exists():
        raise HTTPException(503, detail=f"Falta {nombre}; ejecute POST /ingesta")
    mtime = ruta.stat().st_mtime
    if nombre not in _cache or _cache[nombre][0] != mtime:
        _cache[nombre] = (mtime, json.loads(ruta.read_text(encoding="utf-8")))
    return _cache[nombre][1]


@app.get("/")
def inicio():
    return {
        "producto": "Predicta",
        "servicio": "Predicta API",
        "corte": datos("dashboard.json")["corte"],
        "rutas": ["/salud", "/dashboard", "/clientes", "/clientes/{id}", "/productos", "/metricas", "/ingesta"],
    }


@app.get("/salud")
def salud():
    try:
        dashboard = datos("dashboard.json")
    except HTTPException:
        return {"producto": "Predicta", "estado": "sin_datos", "corte": None}
    return {"producto": "Predicta", "estado": "ok", "corte": dashboard["corte"]}


@app.get("/dashboard")
def dashboard():
    return datos("dashboard.json")


@app.get("/clientes")
def clientes(
    estado: Optional[str] = Query(None, description="frio | por_vencer | en_ventana | reciente"),
    prioridad: Optional[str] = Query(None, description="alta | media | baja"),
    riesgo_min: Optional[float] = Query(None, ge=0, le=1),
    limite: int = Query(50, ge=1, le=500),
):
    filas = datos("clientes_decision.json")
    if estado:
        filas = [f for f in filas if f["estado"] == estado]
    if prioridad:
        filas = [f for f in filas if f["prioridad"] == prioridad]
    if riesgo_min is not None:
        filas = [f for f in filas if f["riesgo_desercion"] >= riesgo_min]
    return {"total": len(filas), "clientes": filas[:limite]}


@app.get("/clientes/{cliente_id}")
def cliente(cliente_id: str):
    filas = datos("clientes_decision.json")
    encontrado = next((f for f in filas if f["cliente_id"] == cliente_id.upper()), None)
    if encontrado is None:
        raise HTTPException(404, detail="Cliente no encontrado")
    productos = [p for p in datos("productos_decision.json") if p["cliente_id"] == encontrado["cliente_id"]]
    productos.sort(key=lambda p: (-p["p_recompra_60d"], p["estado"] != "en_ventana", p["dias_desde_ultima"]))
    return {**encontrado, "productos": productos}


@app.get("/productos")
def productos():
    return {"productos": datos("dashboard.json")["productos"]}


@app.get("/metricas")
def metricas():
    return datos("modelos_decision.json")


@app.post("/ingesta")
def ingesta():
    global _ultima_ingesta
    if not _ingesta_lock.acquire(blocking=False):
        raise HTTPException(409, detail="Ingesta en curso")
    try:
        inicio = time.time()
        proceso = subprocess.run(
            [sys.executable, str(RAIZ / "backend" / "ingesta.py")],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if proceso.returncode != 0:
            raise HTTPException(500, detail=proceso.stderr[-800:] or "Ingesta falló")
        resultado = json.loads(proceso.stdout.strip().splitlines()[-1])
        resultado["duracion_total_s"] = round(time.time() - inicio, 2)
        _ultima_ingesta = {**resultado, "momento": time.strftime("%Y-%m-%dT%H:%M:%S")}
        _cache.clear()
        return _ultima_ingesta
    finally:
        _ingesta_lock.release()


@app.get("/ingesta/estado")
def estado_ingesta():
    return _ultima_ingesta


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8000")))
