# Diccionario de datos de prueba

Fechas ISO AAAA-MM-DD; cantidades enteras; importes decimales con punto; CSV UTF-8 con coma. Los campos terminados en _prueba y origen_datos identifican información generada.

## base_instalada.csv
instalacion_id, cliente_id, producto_id, fecha_inicio, fecha_fin, unidades, origen_datos

## clientes.csv
cliente_id, nombre_prueba, sector_prueba, ciudad_prueba, fecha_alta, canal_preferido_prueba, origen_datos

## compras.csv
compra_id, fecha, proveedor_id, producto_id, cantidad, moneda, costo_unitario, origen_datos

## productos.csv
producto_id, nombre_prueba, familia_prueba, tipo_prueba, moneda_lista, precio_lista, costo_referencia, vigencia_meses, origen_datos

## proveedores.csv
proveedor_id, nombre_prueba, origen_datos

## trm_prueba.csv
fecha, cop_por_usd, origen

## ventas.csv
venta_id, fecha, cliente_id, producto_id, cantidad, moneda, precio_unitario, descuento_pct, estado, origen_datos

## ventas_con_incidencias_OPCIONAL.csv
venta_id, fecha, cliente_id, producto_id, cantidad, moneda, precio_unitario, descuento_pct, estado, origen_datos

## Definiciones de campos
- *_id: identificador estable; las claves primarias son únicas en las tablas limpias.
- fecha_alta: inicio de relación de prueba; ventas nunca son anteriores a esa fecha.
- precio_unitario y costo_unitario: importe por unidad en moneda.
- descuento_pct: porcentaje de descuento adicional (0 en esta versión); los precios pueden diferir del precio de lista.
- estado: Confirmada o Anulada. Excluir anuladas en indicadores.
- unidades: cantidad cubierta por la instalación.
- moneda_lista: COP o USD; costo_referencia tiene esa misma moneda.
- tipo_prueba: Recurrente o Único; vigencia_meses=0 para productos no recurrentes.
- canal_preferido_prueba: preferencia de práctica sin datos de contacto.
- cop_por_usd: pesos por dólar de la serie de prueba.
- origen: advertencia de que la TRM no es oficial.
