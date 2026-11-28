# Predicta · pitch de 3 minutos (Green Services)

> Audiencia no técnica. Regla: cada frase es una idea, no un detalle técnico.

## 0:00–0:25 · El problema
"Ustedes hoy tienen la información repartida en planillas: ventas por un lado, compras por otro,
la TRM en otro archivo. Cuando alguien de Operaciones quiere saber **a quién llamar esta semana**,
tiene que abrir varios Excel y cruzarlos a mano. Para cuando el reporte está listo, la decisión
ya llegó tarde."

## 0:25–0:55 · Qué es Predicta
"Predicta toma esos archivos, los une sin que nadie los toque, y todos los días entrega **una lista
corta de acciones**: a quién llamar, por qué, y qué decirle. No es un tablero para mirar: es una
lista para trabajar."

Señalar la pantalla: `https://predicta.jdlforge.dev`

## 0:55–1:50 · Qué están viendo (3 clics)
1. **Arriba:** 120 clientes, 48 fríos, 14 coberturas por vencer. "Esto antes eran 4 archivos."
2. **Plan de hoy:** "El motor ordena por riesgo y por historia. Miren la primera tarjeta:
   *Reactivar cuenta · lleva 219 días sin comprar · suele comprar cada 9 · riesgo 48 %*.
   Eso es una llamada concreta, no un gráfico."
3. **Cartera:** escribir `CLI016` → ficha con última compra, ciclo, riesgo. "Cualquiera del equipo
   comercial puede hacer esto sin saber Excel." Bajar hasta **Estado del producto**: *9/9 pruebas en
   verde*. "Esto no es una maqueta: cada cifra tiene una prueba que la respalda."

## 1:50–2:30 · En vivo (el momento clave)
Clic en **"Recalcular con datos nuevos"** → 2–3 s → la página se recarga con cifras nuevas.

Guion mientras corre:
"Ese botón es el corazón del producto: es el mismo proceso que correría solo, cada noche o cada vez
que llegue un archivo nuevo. Nadie abre un Excel, nadie copia y pega."

Si la red falla: `curl -X POST https://predicta.jdlforge.dev/api/ingesta` en una terminal, o mostrar
`/api/docs` (Swagger) y decir "la misma acción está expuesta como servicio para su ERP".

## 2:30–3:00 · Límites y siguiente paso
"Tres cosas honestas: los datos que ven son de prueba, no de ustedes; el riesgo es una probabilidad,
no una orden de compra; y todavía no está conectado a su sistema real.
Lo que sigue es conectar la primera fuente y correr dos semanas en paralelo con su equipo comercial."

## Reglas de oro
- Nunca decir "inteligencia artificial" sin un ejemplo concreto de decisión.
- Nunca prometer integración que no existe: decir "el punto de conexión ya está hecho" y mostrar Swagger.
- Si preguntan por el margen o la TRM real: "eso queda fuera del alcance de esta versión".

## Preguntas probables
| Pregunta | Respuesta corta |
|---|---|
| ¿De dónde salen los datos? | Archivos de prueba provistos en el reto; el pipeline es el mismo que usaría con sus archivos. |
| ¿Qué tan confiable es? | Probamos dos modelos; se queda el que acierta más entre las 20 cuentas peores. En prueba acierta 8 de 20 (la regla simple, 11 de 20). La tabla está en el panel del modelo. |
| ¿Se integra con nuestro sistema? | Sí por API (`POST /api/ingesta`); hoy simulado con archivos. |
| ¿Cuánto cuesta? | Un servidor pequeño; corre sin licencias. |
