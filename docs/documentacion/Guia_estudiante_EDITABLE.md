# 01 | Qué contiene este paquete
## Recursos de prueba para IA en operaciones

Este paquete complementa la ficha de Green Services and Solutions SAS. Los registros se generaron para el ejercicio: no corresponden a clientes, ventas, precios, TRM, proveedores ni políticas reales de la empresa. Los nombres de productos representan categorías de práctica y no su portafolio confirmado.

La necesidad empresarial tomada de la ficha es integrar información de compras, ventas, TRM, recurrencia, clientes frecuentes o fríos y base instalada para apoyar decisiones más proactivas. El recurso denominado «com» sigue sin precisar y no se ha interpretado ni sustituido.

Corte del ejercicio: 31 de octubre de 2026. Historia de prueba: enero de 2025 a octubre de 2026. No se incluyen documentos de identidad, teléfonos, correos ni datos reales de personas.

Inicien por LEEME.md. Los CSV pueden abrirse en Excel, LibreOffice, Python o importarse en otra herramienta. Seleccionen UTF-8 y coma como separador. No necesitan una cuenta, una API ni software de pago para ejecutar el ejemplo en Python.

# 02 | Ruta del equipo
## Un MVP viable durante el encuentro

Elijan un usuario principal: Operaciones, equipo comercial o Gerencia Financiera. Formulen una pregunta concreta, por ejemplo: ¿qué clientes requieren seguimiento y con qué evidencia? Eviten intentar resolver todos los análisis y predicciones en una sola jornada.

Paso 1. Revisar datos y supuestos (20 minutos): inspeccionar tablas, claves, fechas y monedas. Paso 2. Integrar y construir una vista por cliente (40 minutos). Paso 3. Construir una capacidad de IA o analítica predictiva y una comparación sencilla (50 minutos). Paso 4. Diseñar la consulta o visualización (30 minutos). Paso 5. Probar con otro equipo y registrar mejoras (20 minutos). Ajusten esta ruta a los tiempos de la guía del facilitador.

MVP sugerido: vista por cliente con historial de productos, compras recientes, valor de ventas convertido a COP, situación de base instalada y una recomendación explicada de seguimiento. Una alerta por reglas es una línea base útil, pero por sí sola no demuestra un modelo de IA.

Para la parte de IA pueden estimar probabilidad de compra en los siguientes 30 días, predecir ventas agregadas o incorporar una consulta en lenguaje natural sobre datos calculados. Escojan una sola vía y expliquen sus límites. No es obligatorio utilizar un modelo generativo.

# 03 | Cómo se relacionan los datos
## Claves, unidades y reglas de lectura

clientes.cliente_id conecta ventas y base_instalada. productos.producto_id conecta ventas, compras y base_instalada. proveedores.proveedor_id conecta compras. trm_prueba.fecha conecta las operaciones en USD con la tasa de su fecha. No unan todas las filas de ventas con todas las compras por producto: esa relación muchos a muchos duplica importes. Agreguen primero según el análisis.

Cada fila de ventas representa una operación de un producto, no una factura con varias líneas. cantidad × precio_unitario × (1 - descuento_pct/100) es el importe en moneda de origen. Incluyan solo estado Confirmada. COP no se convierte; USD se multiplica por cop_por_usd de la misma fecha. No sumen monedas sin conversión.

compras registra adquisiciones a proveedores. No existe una trazabilidad compra-venta ni una valoración de inventarios; por ello no se puede afirmar un margen contable real. costo_referencia es orientativo y no incluye impuestos ni costos indirectos. Todos los importes del ejercicio se consideran antes de impuestos.

base_instalada es una fotografía de contratos o instalaciones de prueba, independiente del historial completo de facturación. fecha_fin significa fin previsto de cobertura. No equivale a una compra futura confirmada. Las vigencias se generaron usando meses de 30 días; no son una regla contractual de la empresa.

La serie TRM se construyó matemáticamente, incluye fines de semana y nunca debe presentarse como tasa oficial. Las ciudades y sectores son atributos de prueba, no descripciones de la cartera real.

# 04 | Supuestos editables
## Convertir una necesidad en una decisión

Cliente frecuente: al menos 8 operaciones confirmadas acumuladas al corte. Cliente frío: 90 días o más sin compra confirmada. Cliente sin compras: categoría separada. Son etiquetas independientes: alguien puede ser frecuente y estar frío. Estos umbrales están en parametros_prueba.json y deben poder modificarse.

Renovación próxima: fecha_fin entre el corte y los siguientes 45 días, ambos incluidos. Vencida: fecha_fin anterior al corte. Vigente: fecha_inicio menor o igual al corte y fecha_fin mayor o igual al corte. No recomienden renovar un servicio ya renovado sin revisar el caso.

La prioridad de seguimiento del ejemplo es una regla transparente, no una probabilidad: primero clientes fríos; después clientes con renovaciones próximas o vencidas; luego el resto. Una prioridad alta indica revisar con el equipo comercial, no contactar automáticamente ni prometer una venta.

Preguntas pendientes para la empresa: definición real de cliente frío; periodicidad de renovación; indicadores de éxito; permisos de uso de la información; significado de «com»; calidad y disponibilidad histórica de datos. Registren estas preguntas sin inventar las respuestas.

# 05 | IA y validación temporal
## Predicciones que se puedan comprobar

Para una clasificación de compra a 30 días: creen fotografías mensuales por cliente usando solo datos conocidos al corte. Etiqueta 1 si existe una venta confirmada en los 30 días posteriores; 0 si no. Excluyan cortes sin una ventana futura completa dentro del conjunto de datos.

Ejemplo de partición: entrenamiento con cortes de marzo de 2025 a abril de 2026; ajuste con mayo y junio de 2026; prueba final con julio a septiembre de 2026. La ventana de septiembre termina el 30 de octubre y es observable. No usen octubre como etiqueta conocida del futuro posterior al 31 de octubre.

Comparen contra una regla simple (por ejemplo, compra reciente) y reporten precisión, exhaustividad y matriz de confusión; si hay pocas compras, la exactitud sola puede engañar. Para pronóstico mensual, reserven los últimos meses y comparen con el último valor observado, usando error absoluto medio. No mezclen filas al azar si eso introduce información futura.

Si eligen un asistente, el modelo debe consultar métricas calculadas, citar cliente y fecha de corte y reconocer cuando no hay información. Prohíban inventar ventas, cifras o políticas. Registren herramienta, versión y ejemplo de entrada y salida. El paquete funciona sin servicios externos; una integración con un modelo es opcional y requiere su propio entorno.

Los patrones del conjunto son de prueba. Un buen resultado aquí permite verificar el prototipo, no demuestra desempeño sobre operaciones reales de Green Services.

# 06 | Pruebas y entrega
## Qué debe demostrar el equipo

Prueben conversión USD/COP, exclusión de anuladas, identificación de cliente frío, renovación próxima, cliente inexistente y ausencia de datos futuros. En 05_Validacion hay casos controlados independientes y resultados de referencia. La copia con incidencias es opcional; nunca la mezclen con ventas.csv para construir el modelo.

Ejecuten python docs/ejemplos/ejemplo_operaciones.py desde la carpeta del paquete. Se crea una carpeta Salidas con resumen_clientes.csv y resumen_prueba.json. El ejemplo usa solo la biblioteca estándar, prepara indicadores y una línea base; no entrena IA ni constituye la solución completa.

Presenten: problema y usuario elegidos, demostración del MVP, fuente y tratamiento de datos, reglas o modelo, al menos una prueba realizada, limitaciones y próximos cambios. Usen las plantillas editables para documentarlo; no necesitan completar todas las funcionalidades posibles.

No utilicen este material para afirmar resultados o indicadores reales de la empresa. Cuando lleguen sus insumos, validen esquemas, autorizaciones y reglas antes de sustituir los datos de prueba.