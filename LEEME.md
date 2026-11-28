# Green Services | IA en operaciones
## Recursos de prueba - EstudIA, Capa 2, intermedio
Este material fue creado para practicar mientras llegan los insumos empresariales. No contiene datos ni políticas reales de Green Services y no implica validación por la empresa.

1. Lean la guía PDF de docs/documentacion (también editable en Markdown).
2. Exploren data/entrada. Datos principales: 120 clientes, 10 productos, 1407 ventas, 240 compras, 243 instalaciones y 669 tasas diarias de prueba.
3. Elijan un alcance y documenten decisiones en docs/plantillas.
4. Opcional: ejecuten `python docs/ejemplos/ejemplo_operaciones.py` con Python 3.10 o superior. No instala dependencias ni envía datos a internet. También funciona desde cualquier carpeta porque resuelve rutas relativas al script.
5. Comparen con los casos controlados en docs/validacion.

La ficha original se conserva como referencia. Donde menciona insumos aún no recibidos, este paquete aporta sustitutos de prueba; no modifica la ficha ni confirma detalles pendientes. Las predicciones deben contrastarse temporalmente y nunca presentarse como resultados reales.

## Alternativa sin código
Importen CSV en una hoja de cálculo, relacionen claves, conviertan USD a COP usando la tasa de cada fecha y construyan una vista por cliente. Una tabla por reglas sirve como línea base; para demostrar IA agreguen una capacidad predictiva o una consulta asistida verificable.

## Versión
1.0 | 20 de noviembre de 2026 | Semilla reproducible 212026. Archivos UTF-8; decimales con punto; sin datos personales. No se requieren credenciales ni herramientas de pago.

## Ejemplo predictivo y visor
También se incluye `docs/ejemplos/modelo_compra.py`, que entrena una regresión logística sin dependencias externas y la compara con una regla base. Lean COMO_EJECUTAR.md. `Visor_local_de_referencia.html` muestra los indicadores precalculados sin internet; no es un asistente de IA.
