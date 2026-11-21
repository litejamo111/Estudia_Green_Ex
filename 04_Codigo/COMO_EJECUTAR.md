# Dos ejemplos independientes
Requieren Python 3.10 o superior. No instalan paquetes, no usan credenciales y no acceden a internet.

Desde la carpeta del paquete:
```
python 04_Codigo/ejemplo_operaciones.py
python 04_Codigo/modelo_compra.py
```
El primero integra ventas y base instalada y produce indicadores por cliente. El segundo entrena una regresión logística de compra a 30 días, selecciona el umbral con validación temporal y compara con una regla de compra reciente. Salidas: CSV y JSON dentro de Salidas. En Windows, si `python` no está disponible, pueden probar `py`.

No se ha implementado una aplicación empresarial completa. Lean el código, revisen las limitaciones y cambien decisiones justificadamente. Los resultados de referencia están en 05_Validacion. La carpeta Salidas incluida corresponde a una ejecución de prueba y se reemplaza al ejecutar de nuevo.

El visor HTML abre localmente y filtra el resumen precalculado. No recalcula al cambiar CSV; ejecuten el script para obtener las nuevas salidas y construyan su propia interfaz si cambian datos o parámetros. El entrenamiento se limita a fotografías mensuales con ventanas futuras observables; no es un pronóstico real de la empresa.
