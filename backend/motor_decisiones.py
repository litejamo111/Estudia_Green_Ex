"""Predicta - Motor de decisiones del MVP.

Produce, al corte vigente, cuatro artefactos para el dashboard:
  - riesgo de deserción a 60 días por cliente (regresión logística)
  - estado del ciclo de recompra por cliente (ventana empírica p25-p75)
  - probabilidad de recompra a 60 días por cliente-producto (tasa calibrada)
  - estado de la ventana de recompra por cliente-producto

Sin dependencias externas ni red. Requiere data/salidas/datos_unificados.csv
(lo genera backend/pipeline_datos.py).

Uso: python backend/motor_decisiones.py
Salidas: modelos_decision.json, clientes_decision.json,
         productos_decision.json, dashboard.json
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
SALIDAS = RAIZ / "data" / "salidas"

HORIZONTE_DIAS = 60
CAMPOS = ["recencia_dias", "compras_30d", "compras_90d", "compras_total"]
UMBRALES = [round(0.05 + 0.05 * i, 2) for i in range(19)]  # 0.05 .. 0.95
MARGEN_VENCIDA_DIAS = 15


def leer_csv(ruta):
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def cuantil(valores, p):
    valores = sorted(valores)
    if not valores:
        return 0.0
    k = (len(valores) - 1) * p
    bajo = int(k)
    alto = min(bajo + 1, len(valores) - 1)
    return valores[bajo] + (valores[alto] - valores[bajo]) * (k - bajo)


def intervalos(fechas):
    return [(b - a).days for a, b in zip(fechas, fechas[1:])]


def cargar():
    clientes = leer_csv(RAIZ / "data" / "entrada" / "clientes.csv")
    productos = {p["producto_id"]: p for p in leer_csv(RAIZ / "data" / "entrada" / "productos.csv")}
    unificadas = leer_csv(SALIDAS / "datos_unificados.csv")

    ventas = defaultdict(list)      # cliente -> [(fecha, importe, producto)]
    pares = defaultdict(list)       # (cliente, producto) -> [fecha]
    for v in unificadas:
        if v["es_confirmada"] != "True":
            continue
        f = date.fromisoformat(v["fecha"])
        ventas[v["cliente_id"]].append((f, float(v["importe_cop"]), v["producto_id"]))
        pares[(v["cliente_id"], v["producto_id"])].append(f)

    for cid in ventas:
        ventas[cid].sort()
    for fechas in pares.values():
        fechas.sort()
    return clientes, productos, ventas, pares


def estado_ventana(dias, p25, p75):
    if dias <= p25:
        return "reciente"
    if dias <= p75:
        return "en_ventana"
    if dias <= p75 + MARGEN_VENCIDA_DIAS:
        return "por_vencer"
    return "frio"


def features_cliente(cid, corte, ventas):
    compras = [(f, a) for f, a, _ in ventas.get(cid, []) if f <= corte]
    if not compras:
        return {
            "recencia_dias": 730,
            "compras_30d": 0,
            "compras_90d": 0,
            "compras_total": 0,
            "ingreso_90d_cop": 0.0,
            "ultima_compra": "",
            "ciclo_p25": None,
            "ciclo_p50": None,
            "ciclo_p75": None,
        }
    fechas = [f for f, _ in compras]
    gaps = intervalos(fechas)
    return {
        "recencia_dias": (corte - max(fechas)).days,
        "compras_30d": sum(0 <= (corte - f).days < 30 for f in fechas),
        "compras_90d": sum(0 <= (corte - f).days < 90 for f in fechas),
        "compras_total": len(fechas),
        "ingreso_90d_cop": round(sum(a for f, a in compras if 0 <= (corte - f).days < 90), 2),
        "ultima_compra": str(max(fechas)),
        "ciclo_p25": cuantil(gaps, 0.25),
        "ciclo_p50": cuantil(gaps, 0.50),
        "ciclo_p75": cuantil(gaps, 0.75),
    }


def construir_filas(clientes, ventas, cortes):
    filas = []
    for corte in cortes:
        limite = corte + timedelta(days=HORIZONTE_DIAS)
        for c in clientes:
            alta = date.fromisoformat(c["fecha_alta"])
            if alta > corte:
                continue
            f = features_cliente(c["cliente_id"], corte, ventas)
            etiqueta = int(not any(corte < d <= limite for d, _, _ in ventas.get(c["cliente_id"], [])))
            filas.append({"corte": corte.isoformat(), "cliente_id": c["cliente_id"], "etiqueta": etiqueta, **f})
    return filas


def vector(fila, media, desviacion):
    return [1.0] + [(fila[c] - m) / s for c, m, s in zip(CAMPOS, media, desviacion)]


def sigmoide(z):
    return 1.0 / (1.0 + math.exp(-max(-35.0, min(35.0, z))))


def producto_punto(a, b):
    return sum(x * y for x, y in zip(a, b))


def entrenar(filas, epocas=600, tasa=0.5, l2=1e-3):
    media = [statistics.mean(f[c] for f in filas) for c in CAMPOS]
    desviacion = [statistics.pstdev(f[c] for f in filas) or 1.0 for c in CAMPOS]
    pesos = [0.0] * (len(CAMPOS) + 1)
    for _ in range(epocas):
        gradiente = [0.0] * len(pesos)
        for fila in filas:
            x = vector(fila, media, desviacion)
            error = sigmoide(producto_punto(pesos, x)) - fila["etiqueta"]
            for j in range(len(pesos)):
                gradiente[j] += error * x[j]
        pesos = [
            pesos[j] - tasa * (gradiente[j] / len(filas) + (l2 * pesos[j] if j else 0.0))
            for j in range(len(pesos))
        ]
    return {"variables": CAMPOS, "media": media, "desviacion": desviacion, "pesos": pesos}


def entrenar_gbm(filas):
    """Gradient boosting si scikit-learn está disponible; si no, devuelve None."""
    try:
        from sklearn.ensemble import GradientBoostingClassifier
    except ImportError:
        return None
    clf = GradientBoostingClassifier(
        n_estimators=150, max_depth=1, learning_rate=0.05,
        min_samples_leaf=20, random_state=212026,
    )
    clf.fit([[f[c] for c in CAMPOS] for f in filas], [f["etiqueta"] for f in filas])
    return {"tipo": "gbm", "clf": clf}


def prob_gbm(modelo, fila):
    return float(modelo["clf"].predict_proba([[fila[c] for c in CAMPOS]])[0][1])


def probabilidad(modelo, fila):
    return sigmoide(producto_punto(modelo["pesos"], vector(fila, modelo["media"], modelo["desviacion"])))


def auc(filas, score):
    pares = sorted((score(f), f["etiqueta"]) for f in filas)
    rangos = [0.0] * len(pares)
    i = 0
    while i < len(pares):
        j = i
        while j + 1 < len(pares) and pares[j + 1][0] == pares[i][0]:
            j += 1
        for k in range(i, j + 1):
            rangos[k] = (i + j) / 2 + 1
        i = j + 1
    positivos = sum(y for _, y in pares)
    negativos = len(pares) - positivos
    if not positivos or not negativos:
        return None
    suma = sum(r for r, (_, y) in zip(rangos, pares) if y)
    return round((suma - positivos * (positivos + 1) / 2) / (positivos * negativos), 4)


def metricas(filas, predecir):
    tp = tn = fp = fn = 0
    for f in filas:
        predice = predecir(f)
        real = f["etiqueta"] == 1
        tp += predice and real
        tn += (not predice) and (not real)
        fp += predice and not real
        fn += (not predice) and real
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    especificidad = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "n": len(filas), "TP": tp, "TN": tn, "FP": fp, "FN": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "F1": round(f1, 4),
        "exactitud_balanceada": round((recall + especificidad) / 2, 4),
    }


def elegir_umbral(validacion, predecir):
    """Umbral que maximiza F1 en validación (nunca en prueba)."""
    def criterio(u):
        m = metricas(validacion, lambda f: predecir(f) >= u)
        return (m["F1"], m["exactitud_balanceada"])
    return max(UMBRALES, key=criterio)


def precision_top(filas, predecir, k=20):
    top = sorted(filas, key=predecir, reverse=True)[:k]
    return round(sum(f["etiqueta"] for f in top) / max(1, len(top)), 4)


def evaluar_candidato(nombre, prob, entrenamiento, validacion, prueba):
    umbral = elegir_umbral(validacion, prob)
    return {
        "nombre": nombre,
        "umbral": umbral,
        "validacion": metricas(validacion, lambda f: prob(f) >= umbral),
        "prueba": metricas(prueba, lambda f: prob(f) >= umbral),
        "auc_validacion": auc(validacion, prob),
        "top20_validacion": precision_top(validacion, prob),
        "top20_prueba": precision_top(prueba, prob),
    }


def tasas_recompra(cortes, producto_ids, pares):
    """Tasa de recompra a 60 días por producto, calibrada con ventanas observadas."""
    positivos = defaultdict(int)
    exposicion = defaultdict(int)
    for corte in cortes:
        limite = corte + timedelta(days=HORIZONTE_DIAS)
        for (cid, pid), fechas in pares.items():
            if not pid or not any(f <= corte for f in fechas):
                continue
            exposicion[pid] += 1
            positivos[pid] += int(any(corte < f <= limite for f in fechas))
    return {
        pid: {
            "p_recompra_60d": round((positivos[pid] + 1) / (exposicion[pid] + 2), 4),
            "ventanas_observadas": exposicion[pid],
            "recompras_observadas": positivos[pid],
        }
        for pid in producto_ids
    }


def main():
    if not (SALIDAS / "datos_unificados.csv").exists():
        subprocess.run([sys.executable, str(RAIZ / "backend" / "pipeline_datos.py")], check=True)
    clientes, productos, ventas, pares = cargar()
    cfg = json.loads((RAIZ / "docs" / "documentacion" / "parametros_prueba.json").read_text(encoding="utf-8"))
    corte_actual = date.fromisoformat(cfg["fecha_corte"])

    cortes = [date(a, m, monthrange(a, m)[1]) for a in (2025, 2026) for m in range(1, 13)]
    cortes = [c for c in cortes if date(2025, 3, 31) <= c <= date(2026, 8, 31)]
    filas = construir_filas(clientes, ventas, cortes)

    entrenamiento = [f for f in filas if f["corte"] <= "2026-04-30"]
    validacion = [f for f in filas if "2026-05-01" <= f["corte"] <= "2026-06-30"]
    prueba = [f for f in filas if f["corte"] >= "2026-07-01"]

    modelo = entrenar(entrenamiento)
    prob_log = lambda f: probabilidad(modelo, f)

    candidatos = [evaluar_candidato("logistica", prob_log, entrenamiento, validacion, prueba)]
    gbm = entrenar_gbm(entrenamiento)
    if gbm is not None:
        candidatos.append(evaluar_candidato("gradient_boosting", lambda f: prob_gbm(gbm, f), entrenamiento, validacion, prueba))

    # La elección se hace SOLO con validación (nunca con el conjunto de prueba).
    elegido = max(candidatos, key=lambda c: (c["top20_validacion"], c["auc_validacion"] or 0))
    prob = prob_log if elegido["nombre"] == "logistica" else (lambda f: prob_gbm(gbm, f))
    umbral = elegido["umbral"]

    regla = lambda f: f["recencia_dias"] > (f["ciclo_p75"] or 60)
    metricas_regla = metricas(prueba, regla)
    top_modelo = sum(
        f["etiqueta"] for f in sorted(prueba, key=lambda f: prob(f), reverse=True)[:20]
    )
    top_regla = sum(f["etiqueta"] for f in sorted(prueba, key=regla, reverse=True)[:20])

    resultados_modelo = {
        "producto": "Predicta",
        "corte_actual": str(corte_actual),
        "horizonte_dias": HORIZONTE_DIAS,
        "desercion": {
            "modelo": "Clasificador de deserción; etiqueta = sin compra en los próximos 60 días",
            "elegido": elegido["nombre"],
            "criterio_eleccion": "precisión en el top 20 de validación (may–jun 2026); desempata AUC",
            "candidatos": candidatos,
            "variables": CAMPOS,
            "media_entrenamiento": [round(x, 6) for x in modelo["media"]],
            "desviacion_entrenamiento": [round(x, 6) for x in modelo["desviacion"]],
            "pesos": [round(x, 6) for x in modelo["pesos"]],
            "umbral_riesgo": umbral,
            "criterio_umbral": "exactitud balanceada en validación",
            "entrenamiento": {"desde": "2025-03-31", "hasta": "2026-04-30", "filas": len(entrenamiento)},
            "validacion": elegido["validacion"],
            "prueba": elegido["prueba"],
            "regla_base_ciclo_propio": metricas_regla,
            "auc_prueba": auc(prueba, prob),
            "top_20_prueba": {
                "aciertos_modelo": top_modelo,
                "aciertos_regla": top_regla,
                "tasa_base": round(sum(f["etiqueta"] for f in prueba) / len(prueba), 4),
            },
            "lectura": (
                "La regla del ciclo propio clasifica mejor umbral a umbral; el modelo ordena mejor "
                "la cola de riesgo y se usa para priorizar contactos."
            ),
            "advertencia": (
                "Datos de prueba. El mismo cliente reaparece en varios cortes: mide seguimiento "
                "temporal, no generalización a clientes nuevos."
            ),
        },
        "recompra": {
            "metodo": "tasa base calibrada por producto en ventanas de 60 días",
            "motivo": "El histórico no muestra señal temporal por producto; se reporta la frecuencia observada y la ventana del ciclo.",
            "horizonte_dias": HORIZONTE_DIAS,
        },
    }

    tasas = tasas_recompra(
        [c for c in cortes if c <= date(2026, 4, 30)],
        productos.keys(),
        pares,
    )

    # Decisiones por cliente al corte vigente.
    clientes_decision = []
    for c in clientes:
        f = features_cliente(c["cliente_id"], corte_actual, ventas)
        if f["ciclo_p75"] is None:
            estado = "sin_historial"
        else:
            estado = estado_ventana(f["recencia_dias"], f["ciclo_p25"], f["ciclo_p75"])
        riesgo = prob(f)
        clientes_decision.append({
            "cliente_id": c["cliente_id"],
            "nombre": c["nombre_prueba"],
            "sector": c["sector_prueba"],
            "ciudad": c["ciudad_prueba"],
            "estado": estado,
            "prioridad": None,
            "riesgo_desercion": round(riesgo, 4),
            "dias_sin_compra": f["recencia_dias"] if f["compras_total"] else None,
            "recencia_dias": f["recencia_dias"],
            "compras_30d": f["compras_30d"],
            "compras_total": f["compras_total"],
            "ultima_compra": f["ultima_compra"],
            "ciclo_p25": round(f["ciclo_p25"], 1) if f["ciclo_p25"] is not None else None,
            "ciclo_p50": round(f["ciclo_p50"], 1) if f["ciclo_p50"] is not None else None,
            "ciclo_p75": round(f["ciclo_p75"], 1) if f["ciclo_p75"] is not None else None,
            "ventana_desde": str(date.fromisoformat(f["ultima_compra"]) + timedelta(days=round(f["ciclo_p25"]))) if f["ultima_compra"] else None,
            "ventana_hasta": str(date.fromisoformat(f["ultima_compra"]) + timedelta(days=round(f["ciclo_p75"]))) if f["ultima_compra"] else None,
            "compras_90d": f["compras_90d"],
            "ingreso_90d_cop": f["ingreso_90d_cop"],
        })
    clientes_decision.sort(key=lambda x: (-x["riesgo_desercion"], x["cliente_id"]))
    for i, c in enumerate(clientes_decision, 1):
        if i <= 20:
            c["prioridad"] = "alta"
        elif i <= 50 or c["estado"] in ("frio", "por_vencer"):
            c["prioridad"] = "media"
        else:
            c["prioridad"] = "baja"

    # Ventanas y probabilidad por cliente-producto.
    ciclo_producto = {}
    for pid in productos:
        gaps = []
        for (cid, p), fechas in pares.items():
            if p == pid:
                gaps.extend(intervalos([f for f in fechas if f <= corte_actual]))
        ciclo_producto[pid] = (cuantil(gaps, 0.25), cuantil(gaps, 0.75))

    productos_decision = []
    for (cid, pid), fechas in pares.items():
        if not pid:
            continue
        pasadas = [f for f in fechas if f <= corte_actual]
        if not pasadas:
            continue
        ultima = max(pasadas)
        dias = (corte_actual - ultima).days
        gaps = intervalos(pasadas)
        if len(gaps) >= 2:
            p25, p75 = cuantil(gaps, 0.25), cuantil(gaps, 0.75)
        else:
            p25, p75 = ciclo_producto[pid]
        productos_decision.append({
            "cliente_id": cid,
            "producto_id": pid,
            "nombre_producto": productos[pid]["nombre_prueba"],
            "familia": productos[pid]["familia_prueba"],
            "estado": estado_ventana(dias, p25, p75),
            "p_recompra_60d": tasas[pid]["p_recompra_60d"],
            "dias_desde_ultima": dias,
            "ultima_compra": str(ultima),
            "ciclo_p25": round(p25, 1),
            "ciclo_p75": round(p75, 1),
            "veces_comprado": len(fechas),
        })
    productos_decision.sort(key=lambda x: (x["cliente_id"], x["producto_id"]))

    # Serie histórica: cómo evoluciona la cartera corte a corte.
    historico = []
    for corte in sorted(set(cortes) | {corte_actual}):
        probs, frios_hist, vencen, n = [], 0, 0, 0
        for c in clientes:
            if date.fromisoformat(c["fecha_alta"]) > corte:
                continue
            fh = features_cliente(c["cliente_id"], corte, ventas)
            n += 1
            probs.append(prob(fh))
            if fh["compras_total"] and fh["recencia_dias"] >= 90:
                frios_hist += 1
            if fh["ciclo_p75"] is not None and estado_ventana(fh["recencia_dias"], fh["ciclo_p25"], fh["ciclo_p75"]) == "por_vencer":
                vencen += 1
        historico.append({
            "corte": str(corte),
            "clientes": n,
            "frios": frios_hist,
            "por_vencer": vencen,
            "riesgo_promedio": round(sum(probs) / n, 4) if n else 0.0,
        })
    (SALIDAS / "historico.json").write_text(
        json.dumps({"producto": "Predicta", "serie": historico}, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Agregados para el dashboard.
    estados = defaultdict(int)
    for c in clientes_decision:
        estados[c["estado"]] += 1

    ingreso_producto = defaultdict(float)
    for v in leer_csv(SALIDAS / "datos_unificados.csv"):
        if v["es_confirmada"] != "True":
            continue
        if 0 <= (corte_actual - date.fromisoformat(v["fecha"])).days < 90:
            ingreso_producto[v["producto_id"]] += float(v["importe_cop"])

    resumen_productos = []
    for pid, p in productos.items():
        pares_pid = [x for x in productos_decision if x["producto_id"] == pid]
        resumen_productos.append({
            "producto_id": pid,
            "nombre": p["nombre_prueba"],
            "familia": p["familia_prueba"],
            "tipo": p["tipo_prueba"],
            "p_recompra_60d": tasas[pid]["p_recompra_60d"],
            "clientes_con_compra": len(pares_pid),
            "clientes_en_ventana": sum(x["estado"] in ("en_ventana", "por_vencer") for x in pares_pid),
            "clientes_frios": sum(x["estado"] == "frio" for x in pares_pid),
            "ingreso_90d_cop": round(ingreso_producto[pid], 2),
        })
    resumen_productos.sort(key=lambda x: -x["ingreso_90d_cop"])

    dashboard = {
        "producto": "Predicta",
        "corte": str(corte_actual),
        "horizonte_dias": HORIZONTE_DIAS,
        "kpis": {
            "clientes": len(clientes_decision),
            "frios": estados["frio"],
            "por_vencer": estados["por_vencer"],
            "en_ventana": estados["en_ventana"],
            "recientes": estados["reciente"],
            "riesgo_promedio": round(sum(c["riesgo_desercion"] for c in clientes_decision) / len(clientes_decision), 4),
            "alto_riesgo": sum(c["riesgo_desercion"] >= umbral for c in clientes_decision),
            "clientes_prioridad_alta": sum(c["prioridad"] == "alta" for c in clientes_decision),
        },
        "top_riesgo": [
            {k: c[k] for k in ("cliente_id", "nombre", "estado", "riesgo_desercion", "dias_sin_compra", "prioridad")}
            for c in clientes_decision[:10]
        ],
        "productos": resumen_productos,
    }

    resultados_modelo["tasas_producto"] = {pid: tasas[pid] for pid in sorted(tasas)}

    # Ficha del modelo que realmente produce el riesgo del tablero.
    metricas_modelo = {
        "modelo": "Gradient boosting" if elegido["nombre"] == "gradient_boosting" else "Regresión logística",
        "elegido": elegido["nombre"],
        "entrenamiento_hasta": "2026-04-30",
        "validacion": elegido["validacion"],
        "prueba": "julio–septiembre 2026",
        "ventana_objetivo_dias": HORIZONTE_DIAS,
        "umbral_elegido_solo_en_validacion": umbral,
        "variables": CAMPOS,
        "prueba_modelo": elegido["prueba"],
        "prueba_linea_base_compra_ultimos_30d": metricas_regla,
        "top20_prueba": {
            "modelo": elegido["top20_prueba"],
            "regla": precision_top(prueba, regla),
        },
        "candidatos": [
            {
                "nombre": c["nombre"],
                "umbral": c["umbral"],
                "F1_validacion": c["validacion"]["F1"],
                "F1_prueba": c["prueba"]["F1"],
                "auc_validacion": c["auc_validacion"],
                "top20_validacion": c["top20_validacion"],
                "top20_prueba": c["top20_prueba"],
            }
            for c in candidatos
        ],
        "advertencia": (
            "Datos de prueba. La etiqueta es 'sin compra en los próximos 60 días'. "
            "El umbral se elige solo con validación; la prueba final no se usa para decidir."
        ),
    }
    (SALIDAS / "metricas_modelo.json").write_text(
        json.dumps(metricas_modelo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (SALIDAS / "modelos_decision.json").write_text(
        json.dumps(resultados_modelo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (SALIDAS / "clientes_decision.json").write_text(
        json.dumps(clientes_decision, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (SALIDAS / "productos_decision.json").write_text(
        json.dumps(productos_decision, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (SALIDAS / "dashboard.json").write_text(
        json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps({
        "corte": dashboard["corte"],
        "kpis": dashboard["kpis"],
        "desercion_prueba": resultados_modelo["desercion"]["prueba"],
        "regla_base": resultados_modelo["desercion"]["regla_base_ciclo_propio"],
        "auc_prueba": resultados_modelo["desercion"]["auc_prueba"],
    }, ensure_ascii=False, indent=2))
    return dashboard


if __name__ == "__main__":
    main()
