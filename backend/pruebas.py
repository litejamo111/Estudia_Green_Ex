"""Predicta · pruebas de aceptación del MVP (solo stdlib).

Ejecuta las comprobaciones que exige la guía del reto y deja evidencia:

    python backend/pruebas.py

Salidas:
    data/salidas/pruebas.json          (lo consume el dashboard)
    docs/validacion/pruebas_ejecutadas.md

Código de salida 1 si alguna prueba falla (lo usa el CI).
"""
from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data" / "entrada"
SALIDAS = RAIZ / "data" / "salidas"
REPORTE = RAIZ / "docs" / "validacion" / "pruebas_ejecutadas.md"
CORTE = date(2026, 10, 31)
FRONTERA_FRIO = 90
VENTANA_RENOVACION = 45
TOLERANCIA = 0.01


def leer(nombre):
    with (DATOS / nombre).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def json_salida(nombre):
    return json.loads((SALIDAS / nombre).read_text(encoding="utf-8"))


def importe_cop(fila, trm):
    """cantidad × precio × (1 - descuento) y conversión con la TRM de su fecha."""
    base = float(fila["cantidad"]) * float(fila["precio_unitario"]) * (1 - float(fila["descuento_pct"]) / 100)
    if fila["moneda"] == "COP":
        return round(base, 2)
    return round(base * trm[fila["fecha"]], 2)


def main():
    ventas = leer("ventas.csv")
    trm = {f["fecha"]: float(f["cop_por_usd"]) for f in leer("trm_prueba.csv")}
    instalaciones = leer("base_instalada.csv")
    clientes = {c["cliente_id"] for c in leer("clientes.csv")}
    referencia = json.loads((RAIZ / "docs" / "validacion" / "Referencia_resumen_prueba.json").read_text(encoding="utf-8"))
    dashboard = json_salida("dashboard.json")
    calidad = json_salida("reporte_calidad.json")

    pruebas = []

    def registrar(nombre, esperado, obtenido, ok, detalle=""):
        pruebas.append({
            "nombre": nombre,
            "esperado": esperado,
            "obtenido": obtenido,
            "ok": bool(ok),
            "detalle": detalle,
        })

    # P1 · Conversión COP sin TRM
    v = {"cantidad": "2", "precio_unitario": "100000", "descuento_pct": "10", "moneda": "COP", "fecha": "2026-01-01"}
    registrar("Conversión en COP", "180.000,00 COP", f"{importe_cop(v, trm):,.2f} COP".replace(",", "."),
              abs(importe_cop(v, trm) - 180000) < TOLERANCIA)

    # P2 · Conversión USD con la TRM del día (nunca la última)
    fecha = next(f for f in sorted(trm) if f in {x["fecha"] for x in ventas})
    v = {"cantidad": "3", "precio_unitario": "100", "descuento_pct": "0", "moneda": "USD", "fecha": fecha}
    esperado = 300 * trm[fecha]
    registrar("Conversión USD→COP con TRM del día", f"{esperado:,.2f} COP", f"{importe_cop(v, trm):,.2f} COP",
              abs(importe_cop(v, trm) - esperado) < TOLERANCIA, f"TRM {fecha} = {trm[fecha]}")

    # P3 · Ventas anuladas fuera de los indicadores
    confirmadas = [f for f in ventas if f["estado"] == "Confirmada"]
    ok = (len(confirmadas) == calidad["ventas_confirmadas"]
          and len(ventas) - len(confirmadas) == calidad["ventas_anuladas"]
          and abs(calidad["ingreso_confirmado_cop"] - referencia["ingreso_cop"]) < TOLERANCIA)
    registrar("Exclusión de ventas anuladas",
              f"{calidad['ventas_confirmadas']} confirmadas · {calidad['ventas_anuladas']} anuladas",
              f"{len(confirmadas)} confirmadas · {len(ventas) - len(confirmadas)} anuladas", ok)

    # P4 · Frontera de cliente frío (90 días, inclusiva)
    def dias_sin(ultima):
        return (CORTE - date.fromisoformat(ultima)).days

    frio_90 = dias_sin("2026-08-02") >= FRONTERA_FRIO
    casi_frio = dias_sin("2026-08-03") >= FRONTERA_FRIO
    registrar("Frontera de cliente frío (90 días)",
              "90 días = frío · 89 días = no frío",
              f"90 días = {'frío' if frio_90 else 'no frío'} · 89 días = {'frío' if casi_frio else 'no frío'}",
              frio_90 and not casi_frio)

    # P5 · Frontera de renovación próxima (45 días, ambos extremos incluidos)
    limite = CORTE + timedelta(days=VENTANA_RENOVACION)
    dentro = CORTE <= limite <= limite
    fuera = CORTE <= limite + timedelta(days=1) <= limite
    registrar("Frontera de renovación (45 días)",
              "día 45 = próximo · día 46 = fuera",
              f"día 45 = {'próximo' if dentro else 'fuera'} · día 46 = {'próximo' if fuera else 'fuera'}",
              dentro and not fuera)

    # P5b · Coherencia entre el tablero y las decisiones por cliente
    decisiones = json_salida("clientes_decision.json")
    por_vencer = sum(c["estado"] == "por_vencer" for c in decisiones)
    registrar("Coherencia tablero ↔ decisiones",
              f"{por_vencer} por vencer en ambos",
              f"tablero {dashboard['kpis']['por_vencer']} · decisiones {por_vencer}",
              por_vencer == dashboard["kpis"]["por_vencer"])

    # P6 · Cliente inexistente no se inventa
    ids = {f["cliente_id"] for f in ventas} | set(clientes)
    registrar("Cliente inexistente (CLI999)",
              "no aparece en la cartera",
              "no aparece" if "CLI999" not in ids else "aparece", "CLI999" not in ids)

    # P7 · Sin datos posteriores al corte
    max_fecha = max(date.fromisoformat(f["fecha"]) for f in ventas)
    registrar("Ausencia de datos futuros",
              f"fecha máxima ≤ {CORTE}",
              f"fecha máxima = {max_fecha}",
              max_fecha <= CORTE)

    # P8 · Integridad referencial de claves
    huerfanos = [f for f in ventas if f["cliente_id"] not in clientes]
    registrar("Integridad de claves de cliente",
              "0 ventas huérfanas", f"{len(huerfanos)} ventas huérfanas", not huerfanos)

    total = len(pruebas)
    ok = sum(p["ok"] for p in pruebas)
    payload = {
        "producto": "Predicta",
        "generado": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "corte": str(CORTE),
        "total": total,
        "ok": ok,
        "pruebas": pruebas,
    }
    (SALIDAS / "pruebas.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lineas = [
        "# Pruebas de aceptación · Predicta",
        "",
        f"Generado: {payload['generado']} · corte {payload['corte']} · **{ok}/{total} en verde**",
        "",
        "| # | Prueba | Esperado | Obtenido | Estado |",
        "|---|---|---|---|---|",
    ]
    for i, p in enumerate(pruebas, 1):
        lineas.append(f"| {i} | {p['nombre']} | {p['esperado']} | {p['obtenido']} | {'✅' if p['ok'] else '❌'} |")
    lineas += ["", "Datos de prueba; no demuestra desempeño sobre operaciones reales de Green Services.", ""]
    REPORTE.write_text("\n".join(lineas), encoding="utf-8")

    for i, p in enumerate(pruebas, 1):
        print(f"{'OK ' if p['ok'] else 'FALLA'} P{i} · {p['nombre']}: {p['obtenido']}")
    print(f"\n{ok}/{total} pruebas en verde · evidencia en {REPORTE.relative_to(RAIZ)}")
    raise SystemExit(0 if ok == total else 1)


if __name__ == "__main__":
    main()
