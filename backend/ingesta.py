"""Predicta - Automatización de ingesta del MVP.

Ejecuta el pipeline de datos y el motor de decisiones en orden. Pensado para
cron, un POST /ingesta o ejecución manual:

    python backend/ingesta.py

Los CSV de data/entrada se reemplazan sin cambiar el esquema y el corte se toma de
docs/documentacion/parametros_prueba.json.
"""
from pathlib import Path
import json
import subprocess
import sys
import time

RAIZ = Path(__file__).resolve().parents[1]
SALIDAS = RAIZ / "data" / "salidas"


def ejecutar():
    inicio = time.time()
    # Las pruebas de aceptación son parte del pipeline: todo artefacto incluye su evidencia.
    for script in ("pipeline_datos.py", "motor_decisiones.py", "pruebas.py"):
        proceso = subprocess.run(
            [sys.executable, str(RAIZ / "backend" / script)],
            capture_output=True,
            text=True,
        )
        if proceso.returncode != 0:
            raise RuntimeError(f"{script} falló: {proceso.stderr[-800:]}")
    dashboard = json.loads((SALIDAS / "dashboard.json").read_text(encoding="utf-8"))
    pruebas = json.loads((SALIDAS / "pruebas.json").read_text(encoding="utf-8"))
    return {
        "producto": "Predicta",
        "estado": "ok",
        "corte": dashboard["corte"],
        "clientes": dashboard["kpis"]["clientes"],
        "frios": dashboard["kpis"]["frios"],
        "pruebas": f"{pruebas['ok']}/{pruebas['total']}",
        "duracion_s": round(time.time() - inicio, 2),
    }


if __name__ == "__main__":
    print(json.dumps(ejecutar(), ensure_ascii=False))
