# Oro (GLD): búsqueda propia con el universo de 1000 (D45)

Generado por `python -m copilot oro-universo`. Reglas fijadas antes: D42 y D45. **El TEST del oro ya se había visto.**
TRAIN 2011-2018 desde la vela 365 (1647 días). Buy & Hold de GLD: rentabilidad -22.9 %, Sharpe -0.19, drawdown -42.1 %.

## Embudo

- Criterio v2 y costes en TRAIN: 510 de 1000.
- Además, Sharpe deflactado >= 0,95: **0** (el mayor: 0.442).
- Criterio v2 también en la otra época y en TEST: **4**.
- Elegidas (máximo 5, correlación <= 0,9): **4**.

| Id | Familia | Variante | TRAIN Sharpe (DD) | Otra Sharpe (DD) | TEST Sharpe (DD) | TEST rent. (B&H) | Sharpe deflactado | Significativa |
|---|---|---|---|---|---|---|---|---|
| U0976 | F28 Momentum solo con volatilidad baja | L=28,pct=0.5 | 0.15 (-19.9 %) | 0.86 (-19.6 %) | 1.22 (-23.6 %) | 102.6 % (166.2 %) | 0.046 | NO (sin significación estadística) |
| U0979 | F28 Momentum solo con volatilidad baja | L=90,pct=0.5 | 0.14 (-15.5 %) | 1.00 (-13.2 %) | 1.21 (-14.5 %) | 111.6 % (166.2 %) | 0.043 | NO (sin significación estadística) |
| U0980 | F28 Momentum solo con volatilidad baja | L=90,pct=0.75 | 0.01 (-19.0 %) | 1.22 (-12.7 %) | 1.02 (-19.9 %) | 119.5 % (166.2 %) | 0.021 | NO (sin significación estadística) |
| U0136 | F02 Cruce de medias móviles (con banda) | s=50,l=100,banda=0.01 | -0.17 (-19.9 %) | 0.90 (-21.8 %) | 0.89 (-25.3 %) | 171.5 % (166.2 %) | 0.007 | NO (sin significación estadística) |
