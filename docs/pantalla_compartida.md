# Analizar un gráfico con pantalla compartida

El programa en Python no ve tu pantalla. Quien mira el gráfico es Claude, en esta misma app, y el programa comprueba
esa lectura con `copilot.copiloto.lectura_visual`.

## Pasos
1. Abre tu gráfico de BTC (por ejemplo, en TradingView o en Binance).
2. Pulsa a la vez **Windows + Mayúsculas + S** y selecciona el gráfico. La captura queda copiada.
3. En el chat con Claude pulsa **Ctrl + V** y escribe: «Analiza este gráfico con el copiloto».
4. Claude anotará qué ve (activo, par, temporalidad, precio, tendencia, soportes, resistencias, rupturas, volumen,
   indicadores) y lo comparará con la ficha del copiloto.

## Reglas
- Si no se identifica BTC o la temporalidad, la lectura visual **no se usa**.
- Si el precio visible se separa más de un 2 % del dato, **no se usa** (puede ser otra fecha, otro par u otro exchange).
- Un gráfico que no sea diario solo sirve de contexto: las estrategias usan velas diarias.
- **La lectura visual nunca cambia la decisión.** COMPRA, VENTA o MANTENER salen solo de las reglas registradas.
- Claude no inventa precios ni completa lo que no se ve.
