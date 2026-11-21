# Evaluación en TEST

Generado por `python -m copilot test`. Regla decidida antes de ver resultados: `docs/decisiones.md`, D21.
TEST: BTC/USDT Binance 2023-01-01 a 2026-11-20, costes 0,16 % por lado. Cada fila está en el registro (lote `test-v1`).

## Resultados

| Estrategia | Variante | En el copiloto | Operaciones | Rentabilidad | Sharpe | Drawdown máx. | Supera B&H (rent. / DD / Sharpe) | Aprueba TEST |
|---|---|---|---|---|---|---|---|---|
| **Buy & Hold** | – | – | – | 255.8 % | 0.93 | -53.0 % | referencia | – |
| B1 | N=20,M=10 | sí | 22 | 125.4 % | 0.83 | -38.4 % | no / sí / no | no |
| B1 | N=55,M=20 | sí | 14 | 37.0 % | 0.42 | -32.4 % | no / sí / no | no |
| T1 | sma_n=100 | sí | 28 | 208.0 % | 1.00 | -36.8 % | no / sí / sí | no |
| T1 | sma_n=150 | no | 19 | 216.8 % | 1.00 | -26.4 % | no / sí / sí | no |
| T1 | sma_n=200 | no | 17 | 195.1 % | 0.93 | -32.0 % | no / sí / no | no |
| T1 | cruce_sma=50/200 | no | 5 | 38.7 % | 0.41 | -53.1 % | no / no / no | no |

## Consistencia TRAIN frente a TEST (D9)

| Variante | Sharpe TRAIN | Sharpe TEST |
|---|---|---|
| B1 N=20,M=10 | 1.23 | 0.83 |
| B1 N=55,M=20 | 1.13 | 0.42 |
| T1 sma_n=100 | 0.99 | 1.00 |
| T1 sma_n=150 | 0.76 | 1.00 |
| T1 sma_n=200 | 0.55 | 0.93 |
| T1 cruce_sma=50/200 | 0.57 | 0.41 |

- T1: Spearman = 0.60 -> superficie **estable** (estable >= 0,5; ruido < 0).
- B1: el orden entre 20/10 y 55/20 se mantiene (con 2 variantes no hay más que medir).

## Cartera C1 al 25 % en TEST (informativo)

Rentabilidad 28.0 %, CAGR 6.6 %, Sharpe 0.88, drawdown -8.0 % (límite del 35 %: respetado). Buy & Hold: CAGR 38.6 %.

## Consecuencia para el copiloto (D21)

**Ninguna variante del copiloto aprueba TEST.** El copiloto solo dirá NO OPERAR.

