# Robustez y filtrado (Prompt 5)

Generado por `python -m copilot robustez`. Reglas fijadas antes de ejecutar: `docs/decisiones.md`, D9.
TRAIN: Binance BTC/USDT 2017-08-17 a 2022-12-31. Otra época: Bitstamp BTC/USD 2011-08-18 a 2016-12-31. Costes x1 = 0,16 % por lado; x3 = 0,48 %.
Cada ejecución en la otra época está anotada en `registros/experimentos.jsonl`.

M1 no tenía ninguna variante aprobada en TRAIN: descartada sin más pruebas.

## 1. Las dos épocas lado a lado (todas las variantes = sensibilidad de parámetros)

| Estr. | Variante | TRAIN rent. | TRAIN Sharpe | TRAIN DD | Aprueba TRAIN | Otra rent. | Otra Sharpe | Otra DD | Otra rent. x3 | Aprueba otra |
|---|---|---|---|---|---|---|---|---|---|---|
| B&H | – | 284.8 % | 0.72 | -83.2 % | – | 8 028.4 % | 1.33 | -84.9 % | – | – |
| T1 | sma_n=100 | 672.7 % | 0.99 | -64.5 % | **sí** | 14 514.3 % | 1.60 | -70.3 % | 11 961.2 % | **sí** |
| T1 | sma_n=150 | 279.2 % | 0.76 | -49.0 % | no | 9 361.3 % | 1.50 | -72.7 % | 8 171.5 % | **sí** |
| T1 | sma_n=200 | 117.5 % | 0.55 | -64.4 % | no | 20 782.3 % | 1.71 | -70.8 % | 18 870.8 % | **sí** |
| T1 | cruce_sma=50/200 | 132.0 % | 0.57 | -66.8 % | no | 17 646.7 % | 1.66 | -78.2 % | 17 198.2 % | **sí** |
| T2 | L=90 | 244.9 % | 0.70 | -66.8 % | no | 12 950.2 % | 1.56 | -70.3 % | 10 465.6 % | **sí** |
| T2 | L=180 | 164.3 % | 0.61 | -61.2 % | no | 25 060.0 % | 1.74 | -71.0 % | 23 349.6 % | **sí** |
| T2 | L=365 | 299.1 % | 0.75 | -63.3 % | **sí** | 8 980.6 % | 1.50 | -71.4 % | 8 751.1 % | **sí** |
| B1 | N=20,M=10 | 1 231.6 % | 1.23 | -54.3 % | **sí** | 20 552.3 % | 1.81 | -70.3 % | 18 305.0 % | **sí** |
| B1 | N=55,M=20 | 930.6 % | 1.13 | -59.1 % | **sí** | 14 471.2 % | 1.74 | -70.3 % | 13 567.8 % | **sí** |
| P1 | base=buy_hold,sigma_obj=40%,ventana=20 | 128.0 % | 0.56 | -67.3 % | no | 2 592.5 % | 1.52 | -68.9 % | 2 371.8 % | no |
| P1 | base=buy_hold,sigma_obj=40%,ventana=60 | 123.0 % | 0.56 | -60.8 % | no | 6 905.8 % | 1.95 | -66.0 % | 6 598.5 % | no |
| P1 | base=buy_hold,sigma_obj=60%,ventana=20 | 233.5 % | 0.68 | -75.3 % | no | 4 836.5 % | 1.49 | -77.6 % | 4 537.5 % | no |
| P1 | base=buy_hold,sigma_obj=60%,ventana=60 | 120.6 % | 0.55 | -75.4 % | no | 11 540.9 % | 1.76 | -78.0 % | 11 118.1 % | **sí** |
| P1 | base=T1:sma_n=100,sigma_obj=40%,ventana=20 | 346.9 % | 1.05 | -34.9 % | **sí** | 2 414.1 % | 1.77 | -34.5 % | 1 967.6 % | no |
| P1 | base=T1:sma_n=100,sigma_obj=40%,ventana=60 | 431.1 % | 1.19 | -33.8 % | **sí** | 5 663.5 % | 2.13 | -32.9 % | 4 916.8 % | no |
| P1 | base=T1:sma_n=100,sigma_obj=60%,ventana=20 | 574.2 % | 1.06 | -44.6 % | **sí** | 4 941.8 % | 1.75 | -44.9 % | 4 008.8 % | no |
| P1 | base=T1:sma_n=100,sigma_obj=60%,ventana=60 | 635.9 % | 1.11 | -46.4 % | **sí** | 9 554.9 % | 1.94 | -45.0 % | 8 072.3 % | **sí** |
| P1 | base=T1:sma_n=150,sigma_obj=40%,ventana=20 | 232.0 % | 0.92 | -37.6 % | no | 2 121.1 % | 1.69 | -50.4 % | 1 834.2 % | no |
| P1 | base=T1:sma_n=150,sigma_obj=40%,ventana=60 | 271.0 % | 1.02 | -31.5 % | no | 5 365.7 % | 2.09 | -42.8 % | 4 813.7 % | no |
| P1 | base=T1:sma_n=150,sigma_obj=60%,ventana=20 | 320.0 % | 0.89 | -44.5 % | **sí** | 3 915.4 % | 1.65 | -60.6 % | 3 380.7 % | no |
| P1 | base=T1:sma_n=150,sigma_obj=60%,ventana=60 | 344.3 % | 0.92 | -41.9 % | **sí** | 8 582.5 % | 1.89 | -53.8 % | 7 567.1 % | **sí** |
| P1 | base=T1:sma_n=200,sigma_obj=40%,ventana=20 | 116.8 % | 0.66 | -44.9 % | no | 2 624.8 % | 1.75 | -53.9 % | 2 296.3 % | no |
| P1 | base=T1:sma_n=200,sigma_obj=40%,ventana=60 | 137.9 % | 0.74 | -43.9 % | no | 7 489.5 % | 2.23 | -41.3 % | 6 844.7 % | no |
| P1 | base=T1:sma_n=200,sigma_obj=60%,ventana=20 | 140.8 % | 0.63 | -57.9 % | no | 5 308.5 % | 1.74 | -62.1 % | 4 679.2 % | no |
| P1 | base=T1:sma_n=200,sigma_obj=60%,ventana=60 | 148.7 % | 0.64 | -59.4 % | no | 13 263.3 % | 2.04 | -54.9 % | 12 002.7 % | **sí** |
| P1 | base=T1:cruce_sma=50/200,sigma_obj=40%,ventana=20 | 103.8 % | 0.59 | -51.8 % | no | 2 072.2 % | 1.62 | -65.1 % | 1 909.1 % | no |
| P1 | base=T1:cruce_sma=50/200,sigma_obj=40%,ventana=60 | 130.7 % | 0.67 | -50.1 % | no | 5 961.9 % | 2.10 | -55.1 % | 5 666.0 % | no |
| P1 | base=T1:cruce_sma=50/200,sigma_obj=60%,ventana=20 | 117.1 % | 0.56 | -63.7 % | no | 4 420.3 % | 1.65 | -71.2 % | 4 147.5 % | no |
| P1 | base=T1:cruce_sma=50/200,sigma_obj=60%,ventana=60 | 140.5 % | 0.61 | -64.5 % | no | 10 720.1 % | 1.94 | -64.7 % | 10 250.5 % | **sí** |

## 2. Regímenes de mercado (variantes aprobadas en TRAIN)

Rentabilidad compuesta en los meses de cada régimen. Entre paréntesis, Buy & Hold en esos mismos meses.

| Estr. | Variante | Época | alcista | bajista | lateral | vol. alta | vol. baja |
|---|---|---|---|---|---|---|---|
| | | | meses: 25 / 25 | meses: 16 / 14 | meses: 24 / 26 | meses: 32 / 32 | meses: 33 / 33 |
| T1 | sma_n=100 | TRAIN | 3 978.1 % (52 442.6 %) | -59.6 % (-98.4 %) | -53.1 % (-55.0 %) | 229.7 % (65.5 %) | 134.4 % (132.6 %) |
| T1 | sma_n=100 | otra | 129 699.2 % (494 379.0 %) | -72.4 % (-98.3 %) | -59.2 % (-1.3 %) | 1 350.5 % (396.3 %) | 907.5 % (1 537.6 %) |
| T2 | L=365 | TRAIN | 3 077.7 % (52 442.6 %) | -76.7 % (-98.4 %) | -46.1 % (-55.0 %) | 87.9 % (65.5 %) | 112.5 % (132.6 %) |
| T2 | L=365 | otra | 81 551.3 % (494 379.0 %) | -87.1 % (-98.3 %) | -13.6 % (-1.3 %) | 1 304.6 % (396.3 %) | 546.5 % (1 537.6 %) |
| B1 | N=20,M=10 | TRAIN | 5 602.4 % (52 442.6 %) | -43.0 % (-98.4 %) | -59.0 % (-55.0 %) | 431.2 % (65.5 %) | 150.7 % (132.6 %) |
| B1 | N=20,M=10 | otra | 88 585.4 % (494 379.0 %) | -51.0 % (-98.3 %) | -52.4 % (-1.3 %) | 1 198.9 % (396.3 %) | 1 490.0 % (1 537.6 %) |
| B1 | N=55,M=20 | TRAIN | 4 106.1 % (52 442.6 %) | -48.2 % (-98.4 %) | -52.7 % (-55.0 %) | 516.4 % (65.5 %) | 67.2 % (132.6 %) |
| B1 | N=55,M=20 | otra | 57 784.1 % (494 379.0 %) | -69.3 % (-98.3 %) | -17.9 % (-1.3 %) | 1 330.4 % (396.3 %) | 918.7 % (1 537.6 %) |
| P1 | base=T1:sma_n=100,sigma_obj=40%,ventana=20 | TRAIN | 1 267.1 % (52 442.6 %) | -39.6 % (-98.4 %) | -45.9 % (-55.0 %) | 192.6 % (65.5 %) | 52.7 % (132.6 %) |
| P1 | base=T1:sma_n=100,sigma_obj=40%,ventana=20 | otra | 11 087.3 % (494 379.0 %) | -53.3 % (-98.3 %) | -51.8 % (-1.3 %) | 191.6 % (396.3 %) | 762.1 % (1 537.6 %) |
| P1 | base=T1:sma_n=100,sigma_obj=40%,ventana=60 | TRAIN | 1 246.7 % (52 442.6 %) | -34.7 % (-98.4 %) | -39.6 % (-55.0 %) | 196.5 % (65.5 %) | 79.1 % (132.6 %) |
| P1 | base=T1:sma_n=100,sigma_obj=40%,ventana=60 | otra | 13 274.8 % (494 379.0 %) | -42.9 % (-98.3 %) | -24.5 % (-1.3 %) | 417.3 % (396.3 %) | 1 014.2 % (1 537.6 %) |
| P1 | base=T1:sma_n=100,sigma_obj=60%,ventana=20 | TRAIN | 2 656.3 % (52 442.6 %) | -48.3 % (-98.4 %) | -52.7 % (-55.0 %) | 256.2 % (65.5 %) | 89.3 % (132.6 %) |
| P1 | base=T1:sma_n=100,sigma_obj=60%,ventana=20 | otra | 31 897.1 % (494 379.0 %) | -62.7 % (-98.3 %) | -57.8 % (-1.3 %) | 426.3 % (396.3 %) | 857.9 % (1 537.6 %) |
| P1 | base=T1:sma_n=100,sigma_obj=60%,ventana=60 | TRAIN | 2 797.0 % (52 442.6 %) | -47.2 % (-98.4 %) | -51.9 % (-55.0 %) | 255.8 % (65.5 %) | 106.8 % (132.6 %) |
| P1 | base=T1:sma_n=100,sigma_obj=60%,ventana=60 | otra | 35 892.1 % (494 379.0 %) | -52.0 % (-98.3 %) | -44.1 % (-1.3 %) | 784.2 % (396.3 %) | 992.0 % (1 537.6 %) |
| P1 | base=T1:sma_n=150,sigma_obj=60%,ventana=20 | TRAIN | 1 439.4 % (52 442.6 %) | -51.9 % (-98.4 %) | -43.3 % (-55.0 %) | 157.9 % (65.5 %) | 62.9 % (132.6 %) |
| P1 | base=T1:sma_n=150,sigma_obj=60%,ventana=20 | otra | 21 757.0 % (494 379.0 %) | -74.6 % (-98.3 %) | -27.6 % (-1.3 %) | 281.9 % (396.3 %) | 951.5 % (1 537.6 %) |
| P1 | base=T1:sma_n=150,sigma_obj=60%,ventana=60 | TRAIN | 1 554.1 % (52 442.6 %) | -54.1 % (-98.4 %) | -41.5 % (-55.0 %) | 160.3 % (65.5 %) | 70.7 % (132.6 %) |
| P1 | base=T1:sma_n=150,sigma_obj=60%,ventana=60 | otra | 28 634.2 % (494 379.0 %) | -64.8 % (-98.3 %) | -14.2 % (-1.3 %) | 573.3 % (396.3 %) | 1 189.6 % (1 537.6 %) |

## 3. Veredicto provisional (regla D9)

(a) alguna variante aprobada en TRAIN aprueba también en la otra época; (b) al menos la mitad de las variantes con Sharpe >= Buy & Hold en cada época.

| Estrategia | (a) | (b) TRAIN | (b) otra | Veredicto |
|---|---|---|---|---|
| B1 | sí | sí | sí | **CONSERVAR (provisional)** |
| P1 | sí | no | sí | **DESCARTAR** |
| T1 | sí | sí | sí | **CONSERVAR (provisional)** |
| T2 | sí | no | sí | **DESCARTAR** |

## 4. TRAIN frente a TEST

Pendiente: necesita los datos de TEST, que siguen bloqueados hasta que el usuario escriba «UNLOCK».

## 5. Alertas de "demasiado bueno" en la otra época y comprobaciones
Seis variantes disparan una alerta en Bitstamp: T2 L=180 (CAGR 180 % frente a 127 % de Buy & Hold, más de 50 puntos) y
cinco de P1 con Sharpe > 2 (de 2,04 a 2,23). Se trataron como posible error antes de aceptarlas (diagnósticos, no son
variantes nuevas y no entran en el registro):

| Variante | Anticipación | Sharpe normal | Sharpe con 1 día más de retraso | Sharpe sin 2011 (B&H sin 2011: 1,62) |
|---|---|---|---|---|
| T2 L=180 | OK | 1,74 | 1,73 | 1,75 |
| P1 T1:SMA100, 40 %, 60 | OK | 2,13 | 2,23 | 2,27 |
| P1 T1:SMA150, 40 %, 60 | OK | 2,09 | 2,21 | 2,24 |
| P1 T1:SMA200, 40 %, 60 | OK | 2,23 | 2,33 | 2,07 |
| P1 T1:SMA200, 60 %, 60 | OK | 2,04 | 2,12 | 1,91 |
| P1 cruce 50/200, 40 %, 60 | OK | 2,10 | 2,11 | 1,92 |

Ningún indicio de filtración: la comprobación de anticipación pasa, el retraso extra no hunde el resultado y quitar 2011
(el año menos líquido) no lo cambia mucho. El Sharpe alto viene de la época: de 2012 a 2016 incluso Buy & Hold tuvo un
Sharpe de 1,62 (+19 164 %). Frente a Buy & Hold, la mejora es del mismo orden que en TRAIN.

## 6. Lectura
- **La otra época discrimina poco.** Casi todas las variantes de tendencia "aprueban" en Bitstamp porque Buy & Hold cayó un
  85 % en 2014-2015 y cualquier regla que pase a liquidez en caídas largas reduce el drawdown. La prueba más exigente es TRAIN frente a TEST.
- **Consistente en las dos épocas:** las estrategias de tendencia protegen mucho en meses bajistas (pierden un 40-87 %
  donde Buy & Hold pierde un 98 %), pero **pierden bastante en meses laterales** (hasta -59 %, frente a -1 % y -55 % de
  Buy & Hold), por las entradas y salidas en falso. También se quedan muy por detrás en meses alcistas.
- **Sensibilidad:** en T1, SMA 100 es la mejor en TRAIN, pero en la otra época la mejor es SMA 200, que en TRAIN era la peor.
  La clasificación de parámetros no se repite: indicio de que elegir "el mejor parámetro" es en parte ruido.
- **Descartes por poco:** P1 tiene 9 de 20 variantes con Sharpe >= Buy & Hold en TRAIN (hacían falta 10) y T2 tiene 1 de 3.
  La regla se fijó antes y se aplica tal cual.
- **Costes x3** (cerca de las comisiones reales de Bitstamp entonces) bajan la rentabilidad pero no cambian ninguna conclusión.
