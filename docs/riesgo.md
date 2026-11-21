# Gestión del riesgo y tamaño de posición (Prompt 7)

Generado por `python -m copilot riesgo`. Reglas fijadas antes de ejecutar: `docs/decisiones.md`, D13.
Base: cartera C1 (B1 20/10 + B1 55/20 + T1 SMA 100). **Provisional** hasta TRAIN frente a TEST.
150 % y 200 % son **simulaciones hipotéticas**: el copiloto no usa apalancamiento.

## 1. Comparación de configuraciones

### TRAIN

| Configuración | CAGR | Sharpe | Volatilidad | Drawdown máx. | Peor día | Peor mes | Exposición media | Ruina | Admisible |
|---|---|---|---|---|---|---|---|---|---|
| exposicion=25% | 13.9 % | 1.16 | 11.9 % | -17.4 % | -3.7 % | -4.3 % | 10.7 % | no | **ELEGIDA** |
| exposicion=50% | 28.0 % | 1.16 | 23.7 % | -32.5 % | -7.3 % | -8.7 % | 21.4 % | no | no |
| exposicion=75% | 41.8 % | 1.16 | 35.6 % | -45.5 % | -11.0 % | -13.4 % | 32.1 % | no | no |
| exposicion=100% | 54.9 % | 1.16 | 47.4 % | -56.5 % | -14.6 % | -18.1 % | 42.8 % | no | no |
| exposicion=150% | 73.4 % | 1.12 | 71.1 % | -73.5 % | -22.0 % | -27.9 % | 64.3 % | no | no |
| exposicion=200% | 83.5 % | 1.11 | 94.8 % | -84.8 % | -29.3 % | -37.8 % | 85.7 % | no | no |
| riesgo_por_operacion=1% | 11.4 % | 1.03 | 11.0 % | -10.0 % | -5.1 % | -3.5 % | 6.5 % | no | no |
| riesgo_por_operacion=2% | 18.3 % | 1.10 | 16.5 % | -15.1 % | -6.7 % | -5.1 % | 10.7 % | no | no |
| riesgo_por_operacion=5% | 31.5 % | 1.15 | 26.8 % | -26.7 % | -10.3 % | -10.0 % | 20.2 % | no | no |
| vol_objetivo=30% | 39.5 % | 1.30 | 28.7 % | -35.8 % | -9.2 % | -12.4 % | 28.4 % | no | no |
| vol_objetivo=45% | 49.4 % | 1.28 | 36.5 % | -40.6 % | -10.8 % | -12.5 % | 35.3 % | no | no |
| Buy & Hold (referencia) | 28.5 % | 0.72 | 78.0 % | -83.2 % | -39.5 % | -37.3 % | 100.0 % | no | – |

### otra época

| Configuración | CAGR | Sharpe | Volatilidad | Drawdown máx. | Peor día | Peor mes | Exposición media | Ruina | Admisible |
|---|---|---|---|---|---|---|---|---|---|
| exposicion=25% | 33.8 % | 1.78 | 17.2 % | -21.4 % | -12.1 % | -10.0 % | 12.4 % | no | **ELEGIDA** |
| exposicion=50% | 73.6 % | 1.78 | 34.4 % | -40.4 % | -24.3 % | -20.2 % | 24.8 % | no | no |
| exposicion=75% | 118.3 % | 1.78 | 51.6 % | -56.7 % | -36.4 % | -30.4 % | 37.2 % | no | no |
| exposicion=100% | 165.5 % | 1.78 | 68.8 % | -70.3 % | -48.5 % | -40.2 % | 49.6 % | no | no |
| exposicion=150% | -100.0 % | 1.27 | 68.2 % | -100.0 % | -100.0 % | -100.0 % | 74.4 % | SÍ | no |
| exposicion=200% | -100.0 % | 1.46 | 82.6 % | -100.0 % | -100.0 % | -100.0 % | 99.2 % | SÍ | no |
| riesgo_por_operacion=1% | 29.8 % | 1.06 | 28.7 % | -50.3 % | -31.1 % | -14.3 % | 10.0 % | no | no |
| riesgo_por_operacion=2% | 50.9 % | 1.26 | 39.0 % | -59.6 % | -38.7 % | -21.4 % | 17.3 % | no | no |
| riesgo_por_operacion=5% | 99.2 % | 1.56 | 53.9 % | -66.9 % | -45.3 % | -31.0 % | 32.3 % | no | no |
| vol_objetivo=30% | 104.4 % | 2.32 | 33.3 % | -27.3 % | -15.9 % | -11.3 % | 34.2 % | no | no |
| vol_objetivo=45% | 132.5 % | 2.21 | 42.2 % | -32.3 % | -23.8 % | -14.7 % | 40.1 % | no | no |
| Buy & Hold (referencia) | 126.5 % | 1.33 | 100.1 % | -84.9 % | -48.5 % | -39.7 % | 100.0 % | no | – |

Regla de elección (D13): configuración admisible elegida: **exposicion=25%**.

## 2. Riesgo por operación (en % del capital de cada componente)

| Regla | Componente | Operaciones | Peor operación | Mediana | Pérdidas mayores que el riesgo previsto |
|---|---|---|---|---|---|
| TRAIN: sin límite | T1 sma_n=100 | 31 | -10.4 % | -2.7 % | – |
| TRAIN: sin límite | B1 N=20,M=10 | 22 | -22.3 % | 1.0 % | – |
| TRAIN: sin límite | B1 N=55,M=20 | 9 | -20.2 % | 1.2 % | – |
| TRAIN: 1 % | T1 sma_n=100 | 31 | -9.9 % | -1.2 % | 18 |
| TRAIN: 1 % | B1 N=20,M=10 | 22 | -1.8 % | 0.1 % | 4 |
| TRAIN: 1 % | B1 N=55,M=20 | 9 | -0.8 % | 0.0 % | 0 |
| TRAIN: 2 % | T1 sma_n=100 | 31 | -10.2 % | -2.4 % | 17 |
| TRAIN: 2 % | B1 N=20,M=10 | 22 | -3.5 % | 0.1 % | 4 |
| TRAIN: 2 % | B1 N=55,M=20 | 9 | -1.6 % | 0.1 % | 0 |
| TRAIN: 5 % | T1 sma_n=100 | 31 | -10.4 % | -2.7 % | 7 |
| TRAIN: 5 % | B1 N=20,M=10 | 22 | -8.8 % | 0.3 % | 4 |
| TRAIN: 5 % | B1 N=55,M=20 | 9 | -4.0 % | 0.2 % | 0 |
| otra época: sin límite | T1 sma_n=100 | 29 | -10.9 % | -1.2 % | – |
| otra época: sin límite | B1 N=20,M=10 | 17 | -17.3 % | 2.4 % | – |
| otra época: sin límite | B1 N=55,M=20 | 9 | -1.6 % | 31.9 % | – |
| otra época: 1 % | T1 sma_n=100 | 29 | -8.9 % | -0.8 % | 12 |
| otra época: 1 % | B1 N=20,M=10 | 17 | -1.0 % | 0.4 % | 0 |
| otra época: 1 % | B1 N=55,M=20 | 9 | -0.2 % | 4.1 % | 0 |
| otra época: 2 % | T1 sma_n=100 | 29 | -8.9 % | -1.1 % | 9 |
| otra época: 2 % | B1 N=20,M=10 | 17 | -1.9 % | 0.8 % | 0 |
| otra época: 2 % | B1 N=55,M=20 | 9 | -0.5 % | 8.1 % | 0 |
| otra época: 5 % | T1 sma_n=100 | 29 | -10.9 % | -1.2 % | 6 |
| otra época: 5 % | B1 N=20,M=10 | 17 | -4.8 % | 2.0 % | 0 |
| otra época: 5 % | B1 N=55,M=20 | 9 | -1.2 % | 20.3 % | 0 |

## 3. Operaciones correlacionadas y concentración (TRAIN)

- Días con 0 / 1 / 2 / 3 componentes comprados: 45% / 15% / 11% / 29%.
- Ratio de diversificación (volatilidad media ponderada de los componentes / volatilidad de la cartera): 1.05. 1,00 sería ninguna diversificación.
- Peso medio de B1: 58%. Dos de los tres componentes son la misma estrategia (B1).
- Concentración: el 100 % del riesgo está en un solo activo (BTC). Cuando los tres componentes compran a la vez, el riesgo real es el de una sola posición grande, no el de tres pequeñas.

## 4. Evaluación honesta

**Cuándo aumentar la exposición mejora y cuándo empeora.**
- Entre 25 % y 100 % el Sharpe es el mismo (1,16 en TRAIN, 1,78 en la otra época): subir la exposición multiplica la
  ganancia y las pérdidas por igual. No mejora la calidad, solo el tamaño. El drawdown crece de -17 % a -57 % en TRAIN.
- Por encima del 100 % (apalancamiento hipotético) **empeora**. En TRAIN el Sharpe baja (1,12 y 1,11) por el funding y
  el drawdown llega al -74 % y al -85 %, peor que Buy & Hold. En la otra época, 150 % y 200 % **se arruinan**: el
  2013-04-10 BTC cayó en Bitstamp de 229 a 70 USD en un día (-69 %). Con 1,5x o 2x esa caída se lleva todo el capital.
  Es un hecho real, no un error de datos. Confirma la regla de no usar apalancamiento.
- Aumentar la exposición solo "mejora" si se mira la rentabilidad; si se mira la supervivencia, siempre empeora.

**Riesgo por operación.**
- Con la regla min(1, r/d), B1 queda bien controlado (en B1 55/20 ninguna pérdida supera el riesgo previsto).
- Con T1 **no funciona**: al entrar, el precio suele estar justo encima de la SMA 100, la distancia d es muy pequeña y la
  exposición llega al tope del 100 %. Después la media se mueve y el precio puede caer de golpe: 18 de 31 operaciones de
  T1 pierden más del 1 % previsto. El riesgo por operación de T1 no se puede fijar con su propia regla de salida.
- La regla 1 % reduce mucho el drawdown en TRAIN (-10 %), pero en la otra época llega a -50 % por lo anterior. No es estable.

**Volatilidad objetivo.**
- Es la que mejor Sharpe da en las dos épocas (1,30 y 2,32), pero en TRAIN su drawdown (-35,8 %) supera por poco el
  límite del 35 % fijado antes. La regla se aplica tal cual y queda fuera. Probar ahora otro objetivo más bajo sería
  ajustar a los datos ya vistos: solo se haría como variante nueva registrada, y se evaluaría con datos nuevos.

**Operaciones correlacionadas.** El 29 % de los días los tres componentes están comprados a la vez, y el ratio de
diversificación es solo 1,05: combinar estas estrategias apenas reduce el riesgo. En la práctica es una única apuesta a
que BTC sigue su tendencia.

**Concentración.** Un solo activo, y dos de los tres componentes son la misma estrategia. No hay forma de diversificar
dentro de este proyecto sin añadir otros activos o estrategias de otra familia.

## 5. Configuración elegida y límites del copiloto

Aplicando la regla de D13: **exposición fija del 25 %** de la cartera C1. Es la única sin apalancamiento con drawdown
de como mucho el 35 % en las dos épocas (-17,4 % en TRAIN, -21,4 % en la otra época).

| Límite | Valor |
|---|---|
| Exposición máxima a BTC | 25 % del capital (cuando los tres componentes están comprados). Con 100 USD, como mucho 25 USD en BTC |
| Exposición mínima | 0 % (todo en USDT) |
| Apalancamiento | Ninguno |
| Posiciones simultáneas | Como mucho 3 (una por componente), todas en BTC |
| Pérdida máxima tolerada de la cartera | Drawdown del 35 % |
| Riesgo por operación (medido, no impuesto) | Peor operación histórica: -22,3 % del componente (B1 20/10). Con 25 % de exposición y un peso de componente de como mucho el 50 %, eso es como mucho -2,8 % del capital total |

**El precio de sobrevivir:** con el 25 %, la cartera crece menos que Buy & Hold en TRAIN (CAGR 13,9 % frente a 28,5 %),
aunque con mucho menos riesgo (drawdown -17 % frente a -83 %, Sharpe 1,16 frente a 0,72). Se elige así porque el
objetivo fijado es la supervivencia del capital, no la rentabilidad máxima.

Todo esto es backtesting. La parte de paper trading llegará con el copiloto (Prompt 9).
