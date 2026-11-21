# Cartera combinada (Prompt 6)

Generado por `python -m copilot cartera`. Reglas fijadas antes de ejecutar: `docs/decisiones.md`, D11.
**Provisional:** B1 y T1 aún no han pasado la comprobación TRAIN frente a TEST (pendiente de «UNLOCK»).

## Correlación de rentabilidades diarias (TRAIN)

| | B1 N=20,M=10 | B1 N=55,M=20 | T1 sma_n=100 | Buy & Hold |
|---|---|---|---|---|
| B1 N=20,M=10 | 1.00 | 0.78 | 0.78 | 0.62 |
| B1 N=55,M=20 | 0.78 | 1.00 | 0.87 | 0.63 |
| T1 sma_n=100 | 0.78 | 0.87 | 1.00 | 0.66 |
| Buy & Hold | 0.62 | 0.63 | 0.66 | 1.00 |

## Correlación de rentabilidades diarias (otra época)

| | B1 N=20,M=10 | B1 N=55,M=20 | T1 sma_n=100 | Buy & Hold |
|---|---|---|---|---|
| B1 N=20,M=10 | 1.00 | 0.89 | 0.87 | 0.68 |
| B1 N=55,M=20 | 0.89 | 1.00 | 0.86 | 0.67 |
| T1 sma_n=100 | 0.87 | 0.86 | 1.00 | 0.77 |
| Buy & Hold | 0.68 | 0.67 | 0.77 | 1.00 |

## Cartera frente a Buy & Hold

| Época | | CAGR | Sharpe | Drawdown máx. | Rentabilidad total |
|---|---|---|---|---|---|
| TRAIN | Cartera C1 | 54.9 % | 1.16 | -56.5 % | 952.4 % |
| TRAIN | Buy & Hold | 28.5 % | 0.72 | -83.2 % | 284.8 % |
| TRAIN | (B1 N=20,M=10 sola) | 61.8 % | 1.23 | -54.3 % | 1 231.6 % |
| TRAIN | (B1 N=55,M=20 sola) | 54.3 % | 1.13 | -59.1 % | 930.6 % |
| TRAIN | (T1 sma_n=100 sola) | 46.3 % | 0.99 | -64.5 % | 672.7 % |
| otra época | Cartera C1 | 165.5 % | 1.78 | -70.3 % | 19 002.4 % |
| otra época | Buy & Hold | 126.5 % | 1.33 | -84.9 % | 8 028.4 % |
| otra época | (B1 N=20,M=10 sola) | 169.4 % | 1.81 | -70.3 % | 20 552.3 % |
| otra época | (B1 N=55,M=20 sola) | 152.5 % | 1.74 | -70.3 % | 14 471.2 % |
| otra época | (T1 sma_n=100 sola) | 152.6 % | 1.60 | -70.3 % | 14 514.3 % |

## Pesos de la cartera (TRAIN, cada reequilibrio mensual)

| Mes | B1 | T1 |
|---|---|---|
| 2017-08 | 50% | 50% |
| 2017-09 | 50% | 50% |
| 2017-10 | 50% | 50% |
| 2017-11 | 50% | 50% |
| 2017-12 | 29% | 71% |
| 2018-01 | 49% | 51% |
| 2018-02 | 55% | 45% |
| 2018-03 | 57% | 43% |
| 2018-04 | 70% | 30% |
| 2018-05 | 57% | 43% |
| 2018-06 | 61% | 39% |
| 2018-07 | 61% | 39% |
| 2018-08 | 59% | 41% |
| 2018-09 | 54% | 46% |
| 2018-10 | 58% | 42% |
| 2018-11 | 61% | 39% |
| 2018-12 | 66% | 34% |
| 2019-01 | 100% | 0% |
| 2019-02 | 100% | 0% |
| 2019-03 | 51% | 49% |
| 2019-04 | 51% | 49% |
| 2019-05 | 50% | 50% |
| 2019-06 | 50% | 50% |
| 2019-07 | 50% | 50% |
| 2019-08 | 53% | 47% |
| 2019-09 | 56% | 44% |
| 2019-10 | 61% | 39% |
| 2019-11 | 74% | 26% |
| 2019-12 | 53% | 47% |
| 2020-01 | 100% | 0% |
| 2020-02 | 54% | 46% |
| 2020-03 | 53% | 47% |
| 2020-04 | 57% | 43% |
| 2020-05 | 53% | 47% |
| 2020-06 | 54% | 46% |
| 2020-07 | 52% | 48% |
| 2020-08 | 53% | 47% |
| 2020-09 | 50% | 50% |
| 2020-10 | 55% | 45% |
| 2020-11 | 60% | 40% |
| 2020-12 | 55% | 45% |
| 2021-01 | 51% | 49% |
| 2021-02 | 50% | 50% |
| 2021-03 | 50% | 50% |
| 2021-04 | 50% | 50% |
| 2021-05 | 50% | 50% |
| 2021-06 | 50% | 50% |
| 2021-07 | 49% | 51% |
| 2021-08 | 48% | 52% |
| 2021-09 | 48% | 52% |
| 2021-10 | 51% | 49% |
| 2021-11 | 53% | 47% |
| 2021-12 | 57% | 43% |
| 2022-01 | 58% | 42% |
| 2022-02 | 64% | 36% |
| 2022-03 | 52% | 48% |
| 2022-04 | 51% | 49% |
| 2022-05 | 55% | 45% |
| 2022-06 | 59% | 41% |
| 2022-07 | 58% | 42% |
| 2022-08 | 100% | 0% |
| 2022-09 | 100% | 0% |
| 2022-10 | 49% | 51% |
| 2022-11 | 50% | 50% |
| 2022-12 | 51% | 49% |

Costes de reequilibrio pagados en TRAIN: 1.27 USD sobre 100 USD iniciales.

## Lectura
- **Diversifica poco.** Las tres variantes están muy correlacionadas (0,78 a 0,89): todas siguen la tendencia del mismo
  activo y están compradas o en liquidez a la vez casi siempre. Por eso la cartera queda entre sus componentes y no por
  encima de ellos: en TRAIN mejora a T1 sola, pero no a B1 20/10 sola.
- **Frente a Buy & Hold** mejora las tres medidas en las dos épocas: en TRAIN, CAGR 54,9 % frente a 28,5 %, Sharpe 1,16
  frente a 0,72 y drawdown -56,5 % frente a -83,2 %.
- **Pesos:** B1 pesó de media un 57 % (entre 29 % y 100 %). Llega al 100 % cuando T1 lleva 90 días en liquidez y su
  volatilidad es 0, como dice la regla.
- **Ningún resultado dispara las alertas** de "demasiado bueno" (en la otra época, CAGR +39 puntos sobre Buy & Hold y Sharpe 1,78).
- **Un drawdown del -56 % sigue siendo enorme.** Con 100 USD, en el peor momento habrían quedado unos 44.
- Rentabilidades históricas: no predicen el futuro. La cartera es provisional hasta la comprobación con TEST.
