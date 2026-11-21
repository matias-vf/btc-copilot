# Resultados en TRAIN, segunda búsqueda, ventana alineada (Prompt 4)

Lote `busqueda2-train-v2`. BTC/USDT Binance spot, velas diarias, costes 0.16 % por lado. Criterio versión 2 (D23): drawdown menor que Buy & Hold y Sharpe igual o mayor. Ventana alineada (D27): cada variante y Buy & Hold se miden desde el primer día en que la variante puede operar.
Cada fila está en `registros/experimentos.jsonl`. Rentabilidades históricas: no predicen el futuro.

| Estrategia | Variantes | Variante | Desde | Operaciones | Órdenes/semana | Rentabilidad | Sharpe | Drawdown máx. | B&H en la misma ventana (rent. / Sharpe / DD) | Supera B&H (drawdown / sharpe) | Avisos |
|---|---|---|---|---|---|---|---|---|---|---|---|
| N1 | 3 | L=1 | 2017-08-25 | 71 | 0.50 | 138.6 % | 0.57 | -80.9 % | 282.7 % / 0.72 / -83.2 % | sí / no |  |
| N1 | 3 | L=2 | 2017-09-01 | 41 | 0.29 | 1 054.7 % | 1.12 | -62.3 % | 249.6 % / 0.70 / -83.2 % | **sí / sí → APRUEBA** |  |
| N1 | 3 | L=4 | 2017-09-15 | 29 | 0.21 | 1 446.3 % | 1.22 | -73.0 % | 417.9 % / 0.79 / -83.2 % | **sí / sí → APRUEBA** |  |
| N2 | 3 | n=5 | 2017-08-22 | 251 | 1.79 | 278.7 % | 0.73 | -70.2 % | 311.3 % / 0.73 / -83.2 % | **sí / sí → APRUEBA** | costes x2: 69.6 %, Sharpe 0.44, NO aprueba; costes x3: -24.0 %, Sharpe 0.15, NO aprueba |
| N2 | 3 | n=10 | 2017-08-27 | 163 | 1.17 | 284.3 % | 0.74 | -72.8 % | 280.8 % / 0.72 / -83.2 % | **sí / sí → APRUEBA** | costes x2: 128.1 %, Sharpe 0.55, NO aprueba; costes x3: 35.4 %, Sharpe 0.37, NO aprueba |
| N2 | 3 | n=20 | 2017-09-06 | 103 | 0.74 | 631.6 % | 0.98 | -68.3 % | 278.2 % / 0.72 / -83.2 % | **sí / sí → APRUEBA** |  |
| N3 | 3 | n=50 | 2017-10-07 | 10 | 0.07 | 562.9 % | 0.92 | -73.2 % | 278.0 % / 0.72 / -83.2 % | **sí / sí → APRUEBA** |  |
| N3 | 3 | n=150 | 2018-01-15 | 4 | 0.03 | 28.9 % | 0.36 | -75.8 % | 22.6 % / 0.44 / -76.6 % | sí / no |  |
| N3 | 3 | n=200 | 2018-03-06 | 2 | 0.02 | 198.6 % | 0.70 | -53.1 % | 44.2 % / 0.47 / -76.6 % | **sí / sí → APRUEBA** |  |
| N4 | 2 | x=10% | 2018-08-17 | 16 | 0.14 | 236.8 % | 1.10 | -24.9 % | 161.7 % / 0.67 / -76.6 % | **sí / sí → APRUEBA** | EXPERIMENTAL |
| N4 | 2 | x=20% | 2018-08-17 | 12 | 0.11 | 215.3 % | 0.89 | -40.5 % | 161.7 % / 0.67 / -76.6 % | **sí / sí → APRUEBA** | EXPERIMENTAL |

Variantes de este lote: 11. Experimentos acumulados en el registro: 112.
