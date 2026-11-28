# Pruebas de aceptación · Predicta

Generado: 2026-11-28T00:59:12 · corte 2026-10-31 · **9/9 en verde**

| # | Prueba | Esperado | Obtenido | Estado |
|---|---|---|---|---|
| 1 | Conversión en COP | 180.000,00 COP | 180.000.00 COP | ✅ |
| 2 | Conversión USD→COP con TRM del día | 1,228,218.00 COP | 1,228,218.00 COP | ✅ |
| 3 | Exclusión de ventas anuladas | 1371 confirmadas · 36 anuladas | 1371 confirmadas · 36 anuladas | ✅ |
| 4 | Frontera de cliente frío (90 días) | 90 días = frío · 89 días = no frío | 90 días = frío · 89 días = no frío | ✅ |
| 5 | Frontera de renovación (45 días) | día 45 = próximo · día 46 = fuera | día 45 = próximo · día 46 = fuera | ✅ |
| 6 | Coherencia tablero ↔ decisiones | 14 por vencer en ambos | tablero 14 · decisiones 14 | ✅ |
| 7 | Cliente inexistente (CLI999) | no aparece en la cartera | no aparece | ✅ |
| 8 | Ausencia de datos futuros | fecha máxima ≤ 2026-10-31 | fecha máxima = 2026-10-30 | ✅ |
| 9 | Integridad de claves de cliente | 0 ventas huérfanas | 0 ventas huérfanas | ✅ |

Datos de prueba; no demuestra desempeño sobre operaciones reales de Green Services.
