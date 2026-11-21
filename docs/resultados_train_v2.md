# Resultados en TRAIN, segunda búsqueda (Prompt 4)

Generado por `python -m copilot train2` (lote `busqueda2-train-v1`). TRAIN 2017-08-17 a 2022-12-31, BTC/USDT Binance spot, costes 0.16 % por lado.
Criterio versión 2 (D23): drawdown máximo menor que Buy & Hold y Sharpe igual o mayor. No exige más rentabilidad.
Cada fila está en `registros/experimentos.jsonl`. Rentabilidades históricas: no predicen el futuro.

| Estrategia | Variantes | Variante | Operaciones | Órdenes/semana | Rentabilidad | Sharpe | Drawdown máx. | Supera B&H (DD / Sharpe) | Avisos |
|---|---|---|---|---|---|---|---|---|---|
| **Buy & Hold** | – | – | 1 | – | 284.8 % | 0.72 | -83.2 % | referencia | |
| N1 | 3 | L=1 | 71 | 0.50 | 138.6 % | 0.57 | -80.9 % | sí / no |  |
| N1 | 3 | L=2 | 41 | 0.29 | 1 054.7 % | 1.11 | -62.3 % | **sí / sí → APRUEBA** |  |
| N1 | 3 | L=4 | 29 | 0.20 | 1 446.3 % | 1.21 | -73.0 % | **sí / sí → APRUEBA** |  |
| N2 | 3 | n=5 | 251 | 1.79 | 278.7 % | 0.73 | -70.2 % | **sí / sí → APRUEBA** | costes x2: 69.6 %, Sharpe 0.44, NO aprueba; costes x3: -24.0 %, Sharpe 0.15, NO aprueba |
| N2 | 3 | n=10 | 163 | 1.16 | 284.3 % | 0.74 | -72.8 % | **sí / sí → APRUEBA** | costes x2: 128.1 %, Sharpe 0.55, NO aprueba; costes x3: 35.4 %, Sharpe 0.37, NO aprueba |
| N2 | 3 | n=20 | 103 | 0.73 | 631.6 % | 0.98 | -68.3 % | **sí / sí → APRUEBA** |  |
| N3 | 3 | n=50 | 10 | 0.07 | 562.9 % | 0.91 | -73.2 % | **sí / sí → APRUEBA** |  |
| N3 | 3 | n=150 | 4 | 0.03 | 28.9 % | 0.35 | -75.8 % | sí / no |  |
| N3 | 3 | n=200 | 2 | 0.01 | 198.6 % | 0.66 | -53.1 % | sí / no |  |
| N4 | 2 | x=10% | 16 | 0.11 | 236.8 % | 0.99 | -24.9 % | **sí / sí → APRUEBA** | EXPERIMENTAL |
| N4 | 2 | x=20% | 12 | 0.09 | 215.3 % | 0.80 | -40.5 % | **sí / sí → APRUEBA** | EXPERIMENTAL |

Variantes de esta búsqueda: 11. Experimentos acumulados en el registro: 101.

## Comprobaciones antes de dar por buenos los resultados
Ninguna variante dispara las alertas automáticas (Sharpe > 2, CAGR más de 50 puntos por encima de Buy & Hold,
drawdown menor del 15 %). Para las que más destacan se repitió la prueba de un día más de retraso (una filtración del
futuro haría que el resultado se hundiera). Diagnóstico: no es una variante nueva y no entra en el registro.

| Variante | Normal | Con 1 día más de retraso | Mejor operación | Operaciones ganadoras |
|---|---|---|---|---|
| N1 L=2 | 1 055 %, Sharpe 1,11 | 836 %, Sharpe 1,05 | +183 % | 16 de 41 |
| N1 L=4 | 1 446 %, Sharpe 1,21 | 1 486 %, Sharpe 1,21 | +436 % | 12 de 28 |
| N2 n=20 | 632 %, Sharpe 0,98 | 458 %, Sharpe 0,87 | +114 % | 26 de 103 |
| N3 n=50 | 563 %, Sharpe 0,91 | 673 %, Sharpe 0,96 | +431 % | 4 de 10 |
| N4 x=10 % | 237 %, Sharpe 0,99 | 244 %, Sharpe 1,00 | +99 % | 7 de 16 |

Ninguna se hunde: no hay indicios de filtración. Como en la primera búsqueda, la ganancia viene de pocas operaciones grandes.

## Lecturas con cuidado
- **El criterio v2 filtra poco en TRAIN:** 9 de 11 variantes aprueban. Buy & Hold cayó un 83 % en 2017-2022, así que
  casi cualquier regla que pase tiempo en liquidez tiene menos drawdown. El filtro de verdad tendrán que ser la otra
  época, TEST y el paper trading.
- **N2 con 5 y 10 días es frágil a los costes:** opera más de una vez por semana (1,79 y 1,16 órdenes) y con costes x2
  ya no aprueba (Sharpe 0,44 y 0,55). Si el slippage real fuera el doble del estimado, no serviría.
- **N1 L=1 no aprueba:** el momentum de una sola semana, el efecto que más destaca el artículo, no funciona aquí con costes.
- **N3 depende mucho del parámetro:** n = 50 aprueba; 150 y 200 no.
- **N4 x=10 % tiene el menor drawdown (-24,9 %)**, con 16 operaciones. Es EXPERIMENTAL.
- Experimentos acumulados: 101. Con tantos, alguna aprobación puede ser suerte.
