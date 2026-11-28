# Dump · Encuentros 1 y 2 — Predicta (Greenex / Green Services)

> Extracción y organización de lo declarado en `Hackathon.html` (equipo E-2AVJ, reto «IA en operaciones»), contrastado con `LEEME.md`, `docs/documentacion/Guia_estudiante_EDITABLE.md`, `docs/validacion/` y el estado real de `backend/` y `data/salidas/`.
> **No se construyó nada.** Este documento solo ordena: (a) lo que el plan dice, (b) lo que se puede / no se puede hacer, (c) brechas y pendientes de decisión.

---

## 1. Ficha de contexto

| Dato | Valor |
|---|---|
| Producto / MVP | **PREDICTA** (renombrado en el repo: commit `09937be`) |
| Equipo | E-2AVJ «Greenex» · equipo de 6 personas |
| Capa / nivel | Capa 2 · Inteligencia artificial · Intermedio |
| Reto | IA en operaciones (ficha `retos/2.pdf`) |
| Encuentro revisado | E1 Plan de trabajo (enviado 14 nov 2026, 12:36 p. m.) y E2 Construcción y pruebas (enviado 21 nov 2026, 10:50 a. m.) |
| Encuentro siguiente | E3 «Mejorar y presentar» (sáb. 28 nov 2026) |

---

## 2. Encuentro 1 · Plan de trabajo (lo declarado)

### 2.1 Solución propuesta
«Cerebro centralizado y automatizado» para Operaciones de Green CSS: unificar y analizar automáticamente ventas, compras, TRM y comportamiento de clientes, para pasar de decisiones en días a decisiones en minutos y con visión predictiva.

### 2.2 MVP declarado
1. Ingestión y unificación automática de planillas/datos dispersos.
2. Base de datos centralizada, limpia y estructurada.
3. Motor de análisis básico (compras, recurrencia, clientes fríos/frecuentes) + panel de control (dashboard) en entorno Linux.

### 2.3 Actividades (3 de 5 declaradas)
1. Mapeo y estructuración de fuentes actuales (formatos de Excel y criterio de unificación).
2. Backend en Python + bases de datos relacionales para automatizar limpieza y almacenamiento.
3. Consultas y lógica de negocio básica: cruce ventas ↔ comportamiento de clientes ↔ TRM, primeros reportes automatizados.
4. _(vacía)_
5. _(vacía)_

### 2.4 Recursos declarados
Computadores personales; Linux; Python (librerías de análisis); VS Code; Git; Docker; datos anonimizados del reto; documentación de la empresa (incluido el significado de «com»).
Condición del formulario: **no incluir software licenciado de pago**.

### 2.5 Prueba declarada
Piloto con lote histórico anonimizado: alimentar el sistema con planillas dispersas y ejecutar consolidación automática. Resultado esperado: unificación en segundos (vs. horas en Excel), vista clara de ventas por cliente y patrones de recurrencia, y **cero errores humanos de transcripción**.

---

## 3. Encuentro 2 · Bitácora (lo declarado)

### 3.1 Qué dicen que construyeron
- Dinámica de trabajo con **Scrumban**, dividida en dos frentes.
- **Equipo 1 (técnico):** repositorio en GitHub + script en Python para limpieza, transformación y unificación; primer **DataFrame** estructurado como base para IA.
- **Equipo 2 (producto):** conceptualización del MVP y definición de componentes.
- **Resultado:** organización inicial, repositorio y primer componente técnico (automatización del procesamiento).
- **Siguiente objetivo:** validar el script, comprobar calidad de los datos transformados e integrar con los requerimientos del MVP.

### 3.2 Pruebas declaradas (el formulario pide 5 o 6)
Solo hay **1 tarjeta**, en estado **Pendiente**, con dos ideas mezcladas:
- **P1a:** que el script de limpieza funcione con distintas fuentes de información y de forma automática cuando la empresa ingrese nuevos datos.
- **P1b:** que los repositorios estén actualizados y funcionando para el trabajo a distancia y la información unificada.
- **Resultado esperado:** datos procesados automáticamente con cada archivo nuevo y disponibles para el usuario final cuando se requieran.
- No hay campo de «qué pasó al realizarla» con contenido, ni marca de `Realizada`.

### 3.3 Mejoras / pendientes declarados (3.º campo)
1. Mejorar la definición de roles en la dinámica de trabajo.
2. Ser más autodidactas entre semana.
3. Aumentar el tiempo dedicado por fuera de clase.

---

## 4. Matriz «se puede / no se puede»

### 4.1 Alcance del producto
| ✅ Se puede | ❌ No se puede / no corresponde |
|---|---|
| Vista por cliente: historial de productos, compras recientes, ventas convertidas a COP, estado de base instalada, recomendación explicada de seguimiento. | Prometer una «aplicación empresarial completa» o el reemplazo total de las fuentes de la empresa. |
| Un motor de reglas transparente como **línea base** (frío / renovación próxima / resto). | Presentar una alerta por reglas como si fuera un modelo de IA. |
| Una sola capacidad predictiva verificable (p. ej. propensión de compra a 30 días) **o** una consulta asistida verificable. | Resolver todos los análisis y predicciones posibles en una jornada. |
| Backend + dashboard simple (lo declarado en E1) si el tiempo de E3 alcanza. | Cambiar de alcance sin registrarlo: el plan E1 prometió BD relacional y dashboard; E2 solo reportó repo + script + DataFrame. |

### 4.2 Datos
| ✅ Se puede | ❌ No se puede |
|---|---|
| Usar `data/entrada/*` (120 clientes, 10 productos, 1407 ventas, 240 compras, 243 instalaciones, 669 TRM de prueba). | Afirmar que son datos, precios, TRM o políticas reales de Green Services. |
| Convertir USD→COP con `cop_por_usd` de **la misma fecha**; dejar COP sin convertir. | Sumar monedas sin conversión. |
| Filtrar solo ventas `Confirmada`. | Incluir `Anulada` en los indicadores. |
| Agregar **antes** de cruzar ventas y compras. | Unir todas las filas de ventas con todas las de compras por producto (muchos-a-muchos duplica importes). |
| Tratar `fecha_fin` como fin previsto de cobertura. | Interpretarla como compra futura confirmada ni como regla contractual. |
| Leer `ventas_con_incidencias_OPCIONAL.csv` por separado y documentar fila a fila (corregir / aislar / pedir info). | Mezclar ese archivo con `ventas.csv` o inventar valores faltantes. |
| Declarar `costo_referencia` como orientativo. | Afirmar un margen contable real (no hay trazabilidad compra-venta ni inventarios). |
| Registrar las preguntas abiertas a la empresa (definición real de frío, periodicidad de renovación, permisos, «com», calidad histórica). | Inventar las respuestas de la empresa. |

### 4.3 IA y validación
| ✅ Se puede | ❌ No se puede |
|---|---|
| Fotografías mensuales por cliente usando solo datos conocidos al corte. | Mezclar filas al azar si eso filtra información del futuro. |
| Etiqueta 1/0 según venta confirmada en los 30 días posteriores, excluyendo ventanas futuras incompletas. | Usar octubre como etiqueta conocida de un futuro posterior al corte (31 oct 2026). |
| Partición temporal (entrena mar–abr 2026, ajusta may–jun, prueba jul–sep). | Reportar solo exactitud cuando hay pocas compras. |
| Comparar contra regla simple (p. ej. compra reciente) y reportar precisión, exhaustividad y matriz de confusión. | Presentar resultados de prueba como desempeño sobre operaciones reales. |
| Si hay asistente: debe consultar métricas calculadas, citar cliente y fecha de corte y admitir cuando no hay información. | Que el asistente invente ventas, cifras o políticas. |
| Reproducir las comprobaciones incluidas (COP/USD, anuladas, frío 90 días, renovación 45 días, cliente inexistente, ausencia de datos futuros). | Usar como insumo el software licenciado de pago. |

### 4.4 Recursos y forma de trabajo
| ✅ Se puede | ❌ No se puede |
|---|---|
| Python 3.10+, solo biblioteca estándar para pipeline/modelo; FastAPI + uvicorn solo para la API. | Depender de credenciales, cuentas o servicios de pago para la demo. |
| Git/GitHub, VS Code, Linux, Docker (declarados en E1). | Exigir internet para la ejecución base (el paquete funciona offline). |
| Reparto en dos frentes (técnico / producto) tipo Scrumban. | Dejar la edición de la bitácora en manos de varias personas a la vez (la edita una sola). |

### 4.5 Comunicación de resultados
| ✅ Se puede | ❌ No se puede |
|---|---|
| Decir «datos de práctica» y «prototipo verificable». | Decir «resultados reales de Green Services». |
| Presentar limitaciones y próximos cambios. | Presentar la serie TRM como tasa oficial. |
| Citar fuente y tratamiento de datos. | Ocultar que los umbrales (8 operaciones, 90/45 días) son supuestos editables (`parametros_prueba.json`). |

---

## 5. Brechas e inconsistencias detectadas (no corregidas)

1. **Cobertura de pruebas incompleta:** el formulario de E2 exige 5–6 pruebas; hay 1 y está `Pendiente`. Faltan: conversión USD/COP, exclusión de anuladas, cliente frío, renovación próxima, cliente inexistente, ausencia de datos futuros.
2. **Prueba mal delimitada:** la P1 mezcla un test de producto (limpieza multi-fuente) con uno de proceso (repos actualizados).
3. **Sin evidencia de ejecución:** ninguna prueba marcada `Realizada`, aunque el logro afirma que el script ya genera un DataFrame.
4. **Criterio no medible:** «pocos segundos» y «cero errores» no tienen umbral ni forma de comprobación.
5. **Deriva de alcance E1 → E2:** se prometió BD relacional + dashboard; se reportó repo + script + DataFrame.
6. **Recursos vs. realidad:** E1 lista Docker y BD relacional; `backend/` usa CSV/JSON + FastAPI, sin BD.
7. **Usuario objetivo difuso:** la solución menciona «la gerencia y los comerciales»; la guía pide **un** usuario principal (Operaciones, comercial o Gerencia Financiera).
8. **Mejoras de E2 centradas en el equipo** (roles, autodidactismo), no en producto ni en hallazgos de pruebas.
9. **Duplicidad de pruebas** entre la prueba piloto de E1 y la P1 de E2, sin trazabilidad entre ambas.

---

## 6. Pendientes de decisión para E3 (no ejecutados)

- [ ] Cerrar el alcance demostrable: ¿dashboard, API o solo pipeline + reporte?
- [ ] Completar 4–5 pruebas con criterio medible y marcarlas `Realizada` con «qué pasó».
- [ ] Elegir un usuario principal único y una pregunta concreta de negocio.
- [ ] Declarar límites: datos de práctica, TRM sintética, sin margen real, «com» sin interpretar.
- [ ] Definir qué se muestra en la demo (guion) y qué se dice como limitación.

---

## 7. Estado real del repo (referencia, sin modificar)

| Componente | Archivo | Nota |
|---|---|---|
| Punto de entrada | `06_Mvp/predicta.py` | `ingesta` (pipeline + motor) / `api` (FastAPI) |
| Ingesta | `06_Mvp/ingesta.py` | — |
| Pipeline | `06_Mvp/pipeline_datos.py` | limpieza y unificación |
| Motor | `06_Mvp/motor_decisiones.py` | 449 líneas, el más extenso |
| API | `06_Mvp/api.py` + `requirements.txt` | fastapi, pydantic<2, uvicorn |
| Salidas | `Salidas/*.json, *.csv` | 11 artefactos ya generados |
| Ejemplos guía | `docs/ejemplos/ejemplo_operaciones.py`, `modelo_compra.py` | stdlib, sin dependencias |

> Conclusión del dump: el producto declarado es viable con los recursos dados, pero la bitácora de E2 **no documenta** las pruebas exigidas ni evidencia su estado. Ese es el hueco principal a resolver antes de E3.
