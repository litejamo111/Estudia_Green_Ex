"""Capa de IA del MVP v0.1 - Propensión de compra a 30 días.

Entrena una regresión logística con descenso de gradiente sobre la tabla
unificada del pipeline, compara contra una regla base y genera una lista de
clientes priorizados con la explicación de cada puntaje.

Sin dependencias externas ni red. Requiere 06_Mvp/pipeline_datos.py ejecutado
(se ejecuta automáticamente si falta Salidas/datos_unificados.csv).

Uso: python 06_Mvp/capa_ia.py
Salidas:
  Salidas/ia_modelo.json          pesos, umbral y métricas
  Salidas/ia_predicciones.csv     prueba temporal con probabilidad y etiqueta
  Salidas/ia_priorizados.csv      ranking al corte + motivo y alertas
"""
from pathlib import Path
from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
import csv
import json
import math
import statistics
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]
SALIDAS = RAIZ / "Salidas"

CAMPOS = ["recencia_dias", "compras_30d", "compras_90d", "compras_total"]
ETIQUETAS = {
    "recencia_dias": "días desde la última compra",
    "compras_30d": "compras en 30 días",
    "compras_90d": "compras en 90 días",
    "compras_total": "historial de compras",
}
UMBRALES = [round(0.10 + 0.05 * i, 2) for i in range(17)]  # 0.10 .. 0.90


def leer_csv(ruta):
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def asegurar_datos():
    if not (SALIDAS / "datos_unificados.csv").exists():
        subprocess.run([sys.executable, str(RAIZ / "06_Mvp" / "pipeline_datos.py")], check=True)


def fin_de_mes(anio, mes):
    return date(anio, mes, monthrange(anio, mes)[1])


def cargar():
    clientes = leer_csv(RAIZ / "01_Datos" / "clientes.csv")
    unificadas = leer_csv(SALIDAS / "datos_unificados.csv")
    instalaciones = leer_csv(RAIZ / "01_Datos" / "base_instalada.csv")

    historial = defaultdict(list)
    for v in unificadas:
        if v["es_confirmada"] != "True":
            continue
        historial[v["cliente_id"]].append((date.fromisoformat(v["fecha"]), float(v["importe_cop"])))

    coberturas = defaultdict(list)
    for x in instalaciones:
        coberturas[x["cliente_id"]].append(
            (date.fromisoformat(x["fecha_inicio"]), date.fromisoformat(x["fecha_fin"]))
        )
    return clientes, historial, coberturas


def features(cliente_id, corte, clientes_idx, historial, coberturas):
    cliente = clientes_idx[cliente_id]
    alta = date.fromisoformat(cliente["fecha_alta"])
    if alta > corte:
        return None

    compras = [(f, a) for f, a in historial.get(cliente_id, []) if f <= corte]
    fechas = [f for f, _ in compras]
    ingreso_90 = sum(a for f, a in compras if 0 <= (corte - f).days < 90)
    cob = coberturas.get(cliente_id, [])

    fila = {
        "recencia_dias": (corte - max(fechas)).days if fechas else 730,
        "compras_30d": sum(0 <= (corte - f).days < 30 for f in fechas),
        "compras_90d": sum(0 <= (corte - f).days < 90 for f in fechas),
        "compras_total": len(compras),
        # contexto para la ficha del asesor, no entra al modelo
        "ultima_compra": str(max(fechas)) if fechas else "",
        "ingreso_90d_cop": round(ingreso_90, 2),
        "instalaciones_activas": sum(i <= corte <= f for i, f in cob),
        "coberturas_vencidas": sum(f < corte for i, f in cob),
        "renovaciones_45d": sum(0 <= (f - corte).days <= 45 for i, f in cob),
        "antiguedad_dias": (corte - alta).days,
    }
    return fila


def construir_muestras(cortes, clientes, historial, coberturas, ventana):
    idx = {c["cliente_id"]: c for c in clientes}
    filas = []
    for corte in cortes:
        limite = corte + timedelta(days=ventana)
        for cid in idx:
            f = features(cid, corte, idx, historial, coberturas)
            if f is None:
                continue
            etiqueta = int(any(corte < d <= limite for d, _ in historial.get(cid, [])))
            filas.append({"corte": corte.isoformat(), "cliente_id": cid, "etiqueta": etiqueta, **f})
    return filas


def vector(fila, media, desviacion):
    return [1.0] + [(fila[c] - m) / s for c, m, s in zip(CAMPOS, media, desviacion)]


def sigmoide(z):
    return 1.0 / (1.0 + math.exp(-max(-35.0, min(35.0, z))))


def producto(a, b):
    return sum(x * y for x, y in zip(a, b))


def entrenar(filas, epocas=600, tasa=0.5, l2=1e-3):
    media = [statistics.mean(f[c] for f in filas) for c in CAMPOS]
    desviacion = [statistics.pstdev(f[c] for f in filas) or 1.0 for c in CAMPOS]
    pesos = [0.0] * (len(CAMPOS) + 1)
    for _ in range(epocas):
        gradiente = [0.0] * len(pesos)
        for fila in filas:
            x = vector(fila, media, desviacion)
            error = sigmoide(producto(pesos, x)) - fila["etiqueta"]
            for j in range(len(pesos)):
                gradiente[j] += error * x[j]
        pesos = [
            pesos[j] - tasa * (gradiente[j] / len(filas) + (l2 * pesos[j] if j else 0.0))
            for j in range(len(pesos))
        ]
    return {"variables": CAMPOS, "media": media, "desviacion": desviacion, "pesos": pesos}


def probabilidad(modelo, fila):
    return sigmoide(producto(modelo["pesos"], vector(fila, modelo["media"], modelo["desviacion"])))


def auc(filas, modelo):
    pares = sorted((probabilidad(modelo, f), f["etiqueta"]) for f in filas)
    rangos = [0.0] * len(pares)
    i = 0
    while i < len(pares):
        j = i
        while j + 1 < len(pares) and pares[j + 1][0] == pares[i][0]:
            j += 1
        rango = (i + j) / 2 + 1
        for k in range(i, j + 1):
            rangos[k] = rango
        i = j + 1
    positivos = sum(etiqueta for _, etiqueta in pares)
    negativos = len(pares) - positivos
    if not positivos or not negativos:
        return None
    suma = sum(r for r, (_, etiqueta) in zip(rangos, pares) if etiqueta)
    return round((suma - positivos * (positivos + 1) / 2) / (positivos * negativos), 4)


def metricas(filas, modelo, umbral):
    tp = tn = fp = fn = 0
    for f in filas:
        predice = probabilidad(modelo, f) >= umbral
        real = f["etiqueta"] == 1
        tp += predice and real
        tn += (not predice) and (not real)
        fp += predice and not real
        fn += (not predice) and real
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "n": len(filas),
        "TP": tp, "TN": tn, "FP": fp, "FN": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "F1": round(f1, 4),
    }


def metricas_regla(filas):
    """Línea base: contactar a quien compró en los últimos 30 días."""
    tp = tn = fp = fn = 0
    for f in filas:
        predice = f["compras_30d"] > 0
        real = f["etiqueta"] == 1
        tp += predice and real
        tn += (not predice) and (not real)
        fp += predice and not real
        fn += (not predice) and real
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"n": len(filas), "TP": tp, "TN": tn, "FP": fp, "FN": fn,
            "precision": round(precision, 4), "recall": round(recall, 4), "F1": round(f1, 4)}


def elegir_umbral(validacion, modelo):
    def criterio(u):
        f1 = metricas(validacion, modelo, u)["F1"]
        return (f1, -abs(u - 0.5))
    return max(UMBRALES, key=criterio)


def factores(modelo, fila, limite=3):
    x = vector(fila, modelo["media"], modelo["desviacion"])
    aportes = sorted(
        ((modelo["pesos"][j + 1] * x[j + 1], c) for j, c in enumerate(CAMPOS) if modelo["pesos"][j + 1] * x[j + 1] > 0),
        key=lambda t: t[0],
        reverse=True,
    )
    if not aportes:
        return "sin señales positivas relevantes"
    return "; ".join(f"{ETIQUETAS[c]} {aporte:+.2f}" for aporte, c in aportes[:limite])


def motivo(fila):
    partes = []
    if fila["compras_total"]:
        partes.append(f"{fila['compras_90d']} compras en 90 días; última hace {fila['recencia_dias']} días")
    else:
        partes.append("sin compras desde el alta")
    if fila["renovaciones_45d"]:
        partes.append(f"{fila['renovaciones_45d']} renovación(es) en 45 días")
    if fila["coberturas_vencidas"]:
        partes.append(f"{fila['coberturas_vencidas']} cobertura(s) vencida(s)")
    return "; ".join(partes)


def main():
    asegurar_datos()
    cfg = json.loads((RAIZ / "02_Documentacion" / "parametros_prueba.json").read_text(encoding="utf-8"))
    ventana = int(cfg["horizonte_prediccion_dias"])
    corte_actual = date.fromisoformat(cfg["fecha_corte"])

    clientes, historial, coberturas = cargar()
    idx = {c["cliente_id"]: c for c in clientes}

    cortes = [fin_de_mes(a, m) for a in (2025, 2026) for m in range(1, 13)]
    cortes = [c for c in cortes if date(2025, 3, 31) <= c <= date(2026, 9, 30)]
    muestras = construir_muestras(cortes, clientes, historial, coberturas, ventana)

    entrenamiento = [f for f in muestras if f["corte"] <= "2026-04-30"]
    validacion = [f for f in muestras if "2026-05-01" <= f["corte"] <= "2026-06-30"]
    prueba = [f for f in muestras if f["corte"] >= "2026-07-01"]

    modelo = entrenar(entrenamiento)
    umbral = elegir_umbral(validacion, modelo)

    resultado = {
        "modelo": "Regresión logística didáctica entrenada sobre datos de prueba",
        "ventana_objetivo_dias": ventana,
        "entrenamiento_hasta": "2026-04-30",
        "validacion": "mayo-junio 2026",
        "prueba": "julio-septiembre 2026",
        "variables": CAMPOS,
        "media_entrenamiento": [round(x, 6) for x in modelo["media"]],
        "desviacion_entrenamiento": [round(x, 6) for x in modelo["desviacion"]],
        "pesos": [round(x, 6) for x in modelo["pesos"]],
        "umbral_elegido_solo_en_validacion": umbral,
        "validacion_modelo": metricas(validacion, modelo, umbral),
        "prueba_modelo": metricas(prueba, modelo, umbral),
        "prueba_linea_base_ultimos_30d": metricas_regla(prueba),
        "auc_prueba": auc(prueba, modelo),
        "advertencia": (
            "No demuestra rendimiento en datos empresariales. El mismo cliente reaparece en varios "
            "cortes mensuales: mide seguimiento temporal, no generalización a clientes nuevos."
        ),
    }

    # Top-k sobre la prueba: ¿cuántos de los priorizados compraron?
    ordenados = sorted(prueba, key=lambda f: probabilidad(modelo, f), reverse=True)
    base = sum(f["etiqueta"] for f in prueba) / len(prueba)
    resultado["top_k_prueba"] = {
        str(k): {
            "aciertos": sum(f["etiqueta"] for f in ordenados[:k]),
            "tasa": round(sum(f["etiqueta"] for f in ordenados[:k]) / k, 4),
            "tasa_base": round(base, 4),
        }
        for k in (10, 20, 40)
    }

    (SALIDAS / "ia_modelo.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

    with (SALIDAS / "ia_predicciones.csv").open("w", encoding="utf-8-sig", newline="") as f:
        campos = ["corte", "cliente_id", "probabilidad", "prediccion", "compra_30d"]
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        for x in prueba:
            p = probabilidad(modelo, x)
            escritor.writerow({
                "corte": x["corte"],
                "cliente_id": x["cliente_id"],
                "probabilidad": round(p, 6),
                "prediccion": int(p >= umbral),
                "compra_30d": x["etiqueta"],
            })

    # Priorización al corte vigente, con contexto y explicación.
    puntajes = []
    for cid in idx:
        fila = features(cid, corte_actual, idx, historial, coberturas)
        if fila is None:
            continue
        fila["cliente_id"] = cid
        fila["nombre"] = idx[cid]["nombre_prueba"]
        fila["probabilidad"] = probabilidad(modelo, fila)
        puntajes.append(fila)

    puntajes.sort(key=lambda f: f["probabilidad"], reverse=True)
    total = len(puntajes)
    with (SALIDAS / "ia_priorizados.csv").open("w", encoding="utf-8-sig", newline="") as f:
        campos = [
            "ranking", "cliente_id", "nombre", "sector", "ciudad",
            "probabilidad", "prioridad", "compras_90d", "ultima_compra",
            "ingreso_90d_cop", "renovaciones_45d", "coberturas_vencidas",
            "motivo", "factores_modelo",
        ]
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        for i, x in enumerate(puntajes, 1):
            if i <= total * 0.2:
                prioridad = "Alta"
            elif i <= total * 0.5:
                prioridad = "Media"
            else:
                prioridad = "Baja"
            escritor.writerow({
                "ranking": i,
                "cliente_id": x["cliente_id"],
                "nombre": x["nombre"],
                "sector": idx[x["cliente_id"]]["sector_prueba"],
                "ciudad": idx[x["cliente_id"]]["ciudad_prueba"],
                "probabilidad": round(x["probabilidad"], 6),
                "prioridad": prioridad,
                "compras_90d": x["compras_90d"],
                "ultima_compra": x["ultima_compra"],
                "ingreso_90d_cop": x["ingreso_90d_cop"],
                "renovaciones_45d": x["renovaciones_45d"],
                "coberturas_vencidas": x["coberturas_vencidas"],
                "motivo": motivo(x),
                "factores_modelo": factores(modelo, x),
            })

    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return resultado


if __name__ == "__main__":
    main()
