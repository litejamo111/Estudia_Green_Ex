"""Predicta - Limpieza y unificación de las tablas de prueba de Green Services.

Lee los CSV de 01_Datos, valida claves y tipos, convierte USD a COP con la TRM
de la fecha de cada venta y escribe una única tabla a nivel de venta lista para
consumo (analítica o capa de IA). Sin dependencias externas ni red.

Uso: python 06_Mvp/pipeline_datos.py
Salidas: Salidas/datos_unificados.csv, Salidas/reporte_calidad.json
"""
from pathlib import Path
from collections import defaultdict, Counter
from datetime import date
import csv
import json

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "01_Datos"
SALIDAS = RAIZ / "Salidas"

ESTADOS = {"Confirmada", "Anulada"}
MONEDAS = {"COP", "USD"}


def leer(nombre):
    with (DATOS / nombre).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fecha(texto):
    return date.fromisoformat(texto)


def unicos(filas, campo):
    vistos = Counter(f[campo] for f in filas)
    return sorted(k for k, n in vistos.items() if n > 1)


def main():
    clientes = leer("clientes.csv")
    productos = leer("productos.csv")
    proveedores = leer("proveedores.csv")
    ventas = leer("ventas.csv")
    compras = leer("compras.csv")
    instalaciones = leer("base_instalada.csv")
    trm = {f["fecha"]: float(f["cop_por_usd"]) for f in leer("trm_prueba.csv")}

    idx_clientes = {c["cliente_id"]: c for c in clientes}
    idx_productos = {p["producto_id"]: p for p in productos}
    idx_proveedores = {p["proveedor_id"]: p for p in proveedores}

    errores = []
    if unicos(clientes, "cliente_id"):
        errores.append(f"clientes: ids duplicados {unicos(clientes, 'cliente_id')}")
    if unicos(productos, "producto_id"):
        errores.append(f"productos: ids duplicados {unicos(productos, 'producto_id')}")
    if unicos(ventas, "venta_id"):
        errores.append(f"ventas: ids duplicados {unicos(ventas, 'venta_id')}")
    if unicos(instalaciones, "instalacion_id"):
        errores.append(f"instalaciones: ids duplicados {unicos(instalaciones, 'instalacion_id')}")

    unificadas = []
    descartadas = []
    for v in ventas:
        cliente = idx_clientes.get(v["cliente_id"])
        producto = idx_productos.get(v["producto_id"])
        motivo = None
        if cliente is None:
            motivo = "cliente inexistente"
        elif producto is None:
            motivo = "producto inexistente"
        elif v["estado"] not in ESTADOS:
            motivo = f"estado no admitido: {v['estado']}"
        elif v["moneda"] not in MONEDAS:
            motivo = f"moneda no admitida: {v['moneda']}"
        elif int(v["cantidad"]) <= 0:
            motivo = "cantidad no positiva"
        elif float(v["precio_unitario"]) < 0:
            motivo = "precio negativo"
        elif not 0 <= float(v["descuento_pct"]) <= 100:
            motivo = "descuento fuera de rango"
        elif v["moneda"] == "USD" and v["fecha"] not in trm:
            motivo = "sin TRM para la fecha"

        if motivo:
            descartadas.append({"venta_id": v["venta_id"], "motivo": motivo})
            continue

        cantidad = int(v["cantidad"])
        precio = float(v["precio_unitario"])
        descuento = float(v["descuento_pct"])
        factor = 1 - descuento / 100
        tasa = trm[v["fecha"]] if v["moneda"] == "USD" else 1.0
        importe = cantidad * precio * factor * tasa
        confirmada = v["estado"] == "Confirmada"

        unificadas.append({
            "venta_id": v["venta_id"],
            "fecha": v["fecha"],
            "anio_mes": v["fecha"][:7],
            "cliente_id": v["cliente_id"],
            "nombre_cliente": cliente["nombre_prueba"],
            "sector": cliente["sector_prueba"],
            "ciudad": cliente["ciudad_prueba"],
            "canal_preferido": cliente["canal_preferido_prueba"],
            "fecha_alta": cliente["fecha_alta"],
            "producto_id": v["producto_id"],
            "nombre_producto": producto["nombre_prueba"],
            "familia": producto["familia_prueba"],
            "tipo_producto": producto["tipo_prueba"],
            "cantidad": cantidad,
            "moneda": v["moneda"],
            "precio_unitario": v["precio_unitario"],
            "descuento_pct": v["descuento_pct"],
            "estado": v["estado"],
            "trm_usada": round(tasa, 6),
            "importe_cop": round(importe, 2) if confirmada else 0.0,
            "es_confirmada": confirmada,
        })

    SALIDAS.mkdir(exist_ok=True)
    with (SALIDAS / "datos_unificados.csv").open("w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(unificadas[0]))
        escritor.writeheader()
        escritor.writerows(unificadas)

    confirmadas = [u for u in unificadas if u["es_confirmada"]]
    ingreso = sum(u["importe_cop"] for u in confirmadas)
    reporte = {
        "filas_por_tabla": {
            "clientes": len(clientes),
            "productos": len(productos),
            "proveedores": len(proveedores),
            "ventas": len(ventas),
            "compras": len(compras),
            "base_instalada": len(instalaciones),
            "trm_prueba": len(trm),
        },
        "ventas_confirmadas": len(confirmadas),
        "ventas_anuladas": len(unificadas) - len(confirmadas),
        "ventas_en_cop": sum(u["moneda"] == "COP" for u in unificadas),
        "ventas_en_usd": sum(u["moneda"] == "USD" for u in unificadas),
        "ingreso_confirmado_cop": round(ingreso, 2),
        "rango_fechas_ventas": [min(u["fecha"] for u in unificadas), max(u["fecha"] for u in unificadas)],
        "filas_unificadas": len(unificadas),
        "filas_descartadas": descartadas,
        "errores_estructurales": errores,
        "nota": "Datos y resultados de prueba; no son cifras reales de Green Services.",
    }
    (SALIDAS / "reporte_calidad.json").write_text(
        json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(reporte, ensure_ascii=False, indent=2))
    return reporte


if __name__ == "__main__":
    main()
