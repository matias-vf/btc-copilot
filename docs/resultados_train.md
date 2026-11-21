# Resultados en TRAIN (Prompt 4)

Generado por `python -m copilot train` (lote `prompt4-train-v1`). Periodo 2017-08-17 a 2022-12-31, BTC/USDT Binance spot, velas diarias, costes 0.16 % por lado.
Cada fila está anotada en `registros/experimentos.jsonl`. Rentabilidades históricas: no predicen el futuro.

| Estrategia | Variantes probadas | Variante | Operaciones | Órdenes/semana | Rentabilidad | Sharpe | Drawdown máx. | Supera B&H (rent. / DD / Sharpe) | Avisos |
|---|---|---|---|---|---|---|---|---|---|
| **Buy & Hold** | – | – | 1 | – | 284.8 % | 0.72 | -83.2 % | referencia | |
| T1 | 4 | sma_n=100 | 31 | 0.22 | 672.7 % | 0.99 | -64.5 % | **sí / sí / sí → APRUEBA** |  |
| T1 | 4 | sma_n=150 | 18 | 0.13 | 279.2 % | 0.76 | -49.0 % | no / sí / sí |  |
| T1 | 4 | sma_n=200 | 16 | 0.11 | 117.5 % | 0.55 | -64.4 % | no / sí / no |  |
| T1 | 4 | cruce_sma=50/200 | 5 | 0.04 | 132.0 % | 0.57 | -66.8 % | no / sí / no |  |
| T2 | 3 | L=90 | 35 | 0.25 | 244.9 % | 0.70 | -66.8 % | no / sí / no |  |
| T2 | 3 | L=180 | 17 | 0.12 | 164.3 % | 0.61 | -61.2 % | no / sí / no |  |
| T2 | 3 | L=365 | 11 | 0.08 | 299.1 % | 0.75 | -63.3 % | **sí / sí / sí → APRUEBA** |  |
| B1 | 2 | N=20,M=10 | 22 | 0.16 | 1 231.6 % | 1.23 | -54.3 % | **sí / sí / sí → APRUEBA** |  |
| B1 | 2 | N=55,M=20 | 9 | 0.06 | 930.6 % | 1.13 | -59.1 % | **sí / sí / sí → APRUEBA** |  |
| M1 | 2 | u=5 | 13 | 0.09 | 0.6 % | 0.08 | -29.3 % | no / sí / no | EXPERIMENTAL |
| M1 | 2 | u=10 | 28 | 0.20 | -0.3 % | 0.10 | -33.3 % | no / sí / no | EXPERIMENTAL |
| P1 | 20 | base=buy_hold,sigma_obj=40%,ventana=20 | 1 | 0.91 | 128.0 % | 0.56 | -67.3 % | no / sí / no |  |
| P1 | 20 | base=buy_hold,sigma_obj=40%,ventana=60 | 1 | 0.96 | 123.0 % | 0.56 | -60.8 % | no / sí / no |  |
| P1 | 20 | base=buy_hold,sigma_obj=60%,ventana=20 | 1 | 0.70 | 233.5 % | 0.68 | -75.3 % | no / sí / no |  |
| P1 | 20 | base=buy_hold,sigma_obj=60%,ventana=60 | 1 | 0.75 | 120.6 % | 0.55 | -75.4 % | no / sí / no |  |
| P1 | 20 | base=T1:sma_n=100,sigma_obj=40%,ventana=20 | 31 | 0.62 | 346.9 % | 1.05 | -34.9 % | **sí / sí / sí → APRUEBA** |  |
| P1 | 20 | base=T1:sma_n=100,sigma_obj=40%,ventana=60 | 31 | 0.65 | 431.1 % | 1.19 | -33.8 % | **sí / sí / sí → APRUEBA** |  |
| P1 | 20 | base=T1:sma_n=100,sigma_obj=60%,ventana=20 | 31 | 0.54 | 574.2 % | 1.06 | -44.6 % | **sí / sí / sí → APRUEBA** |  |
| P1 | 20 | base=T1:sma_n=100,sigma_obj=60%,ventana=60 | 31 | 0.51 | 635.9 % | 1.11 | -46.4 % | **sí / sí / sí → APRUEBA** |  |
| P1 | 20 | base=T1:sma_n=150,sigma_obj=40%,ventana=20 | 18 | 0.48 | 232.0 % | 0.92 | -37.6 % | no / sí / sí |  |
| P1 | 20 | base=T1:sma_n=150,sigma_obj=40%,ventana=60 | 18 | 0.51 | 271.0 % | 1.02 | -31.5 % | no / sí / sí |  |
| P1 | 20 | base=T1:sma_n=150,sigma_obj=60%,ventana=20 | 18 | 0.41 | 320.0 % | 0.89 | -44.5 % | **sí / sí / sí → APRUEBA** |  |
| P1 | 20 | base=T1:sma_n=150,sigma_obj=60%,ventana=60 | 18 | 0.39 | 344.3 % | 0.92 | -41.9 % | **sí / sí / sí → APRUEBA** |  |
| P1 | 20 | base=T1:sma_n=200,sigma_obj=40%,ventana=20 | 16 | 0.46 | 116.8 % | 0.66 | -44.9 % | no / sí / no |  |
| P1 | 20 | base=T1:sma_n=200,sigma_obj=40%,ventana=60 | 16 | 0.48 | 137.9 % | 0.74 | -43.9 % | no / sí / sí |  |
| P1 | 20 | base=T1:sma_n=200,sigma_obj=60%,ventana=20 | 16 | 0.39 | 140.8 % | 0.63 | -57.9 % | no / sí / no |  |
| P1 | 20 | base=T1:sma_n=200,sigma_obj=60%,ventana=60 | 16 | 0.37 | 148.7 % | 0.64 | -59.4 % | no / sí / no |  |
| P1 | 20 | base=T1:cruce_sma=50/200,sigma_obj=40%,ventana=20 | 5 | 0.39 | 103.8 % | 0.59 | -51.8 % | no / sí / no |  |
| P1 | 20 | base=T1:cruce_sma=50/200,sigma_obj=40%,ventana=60 | 5 | 0.42 | 130.7 % | 0.67 | -50.1 % | no / sí / no |  |
| P1 | 20 | base=T1:cruce_sma=50/200,sigma_obj=60%,ventana=20 | 5 | 0.32 | 117.1 % | 0.56 | -63.7 % | no / sí / no |  |
| P1 | 20 | base=T1:cruce_sma=50/200,sigma_obj=60%,ventana=60 | 5 | 0.31 | 140.5 % | 0.61 | -64.5 % | no / sí / no |  |

Total de variantes probadas (contador acumulado): 31.

## Comprobaciones hechas antes de dar por buenos los resultados
Ninguna variante disparó las alertas automáticas (Sharpe > 2, CAGR más de 50 puntos por encima de Buy & Hold, drawdown
menor del 15 %). Aun así, como B1 multiplica por 4 la rentabilidad de Buy & Hold, se revisó (diagnóstico, no es una
variante candidata y no entra en el registro de experimentos):

1. **Comprobación de anticipación** (Prompt 3): 32 de 32 variantes sin anticipación.
2. **Un día más de retraso:** si la decisión se toma con un día de retraso extra, una filtración del futuro haría que el
   resultado se hundiera. No pasa: B1 20/10 pasa de 1 231,6 % a 917,8 %; B1 55/20 de 930,6 % a 1 172,3 %; T1 SMA 100 de
   672,7 % a 732,9 %.
3. **Buy & Hold a mano:** apertura del 2017-08-18 = 4 285,08; cierre del 2022-12-31 = 16 542,40; 16 542,40 / 4 285,08 = 3,86,
   es decir, +286 % antes de costes (284,8 % con costes). Cuadra.
4. **De dónde sale la ganancia de B1 20/10:** de pocas tendencias largas. La mejor operación (2020-10-11 a 2021-03-25)
   gana un 363 %; solo 11 de 22 operaciones son ganadoras. Es el perfil típico del seguimiento de tendencia, no de un error.

## Lecturas con cuidado
- **Costes x2 y x3:** ninguna variante supera una orden por semana de media, así que la regla no obliga a mostrarlos.
  P1 sobre Buy & Hold queda justo en el límite (reajusta casi cada lunes).
- **Muchas pruebas:** se han probado 31 variantes. Con tantas, alguna puede "aprobar" por suerte. El Prompt 5
  (otra época, sensibilidad y TRAIN frente a TEST) es el que debe separar lo robusto del ruido.
- **T1 es irregular:** SMA 100 aprueba, pero SMA 150 y SMA 200 no superan la rentabilidad de Buy & Hold. Que el resultado
  dependa tanto del parámetro es una señal de fragilidad que hay que vigilar en el Prompt 5.
- **M1 (experimental)** no gana nada: ~0 % en cinco años.
- **Todas** las variantes tienen menor drawdown que Buy & Hold (-83,2 %), porque pasan tiempo en liquidez.
