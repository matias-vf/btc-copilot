# Nasdaq (QQQ): búsqueda propia con el universo de 1000 (D45, D47)

Reglas fijadas antes de ejecutar: D42, D45 y D47. TEST no estaba bloqueado.
TRAIN 2011-2018 desde la vela 365 (1647 días). Buy & Hold de QQQ: rentabilidad 148.2 %, Sharpe 0.95, drawdown -23.2 %.

## Embudo

- Criterio v2 y costes en TRAIN: 51 de 1000.
- Además, Sharpe deflactado >= 0,95: **0** (el mayor: 0.517).
- Criterio v2 también en la otra época y en TEST: **4**.
- Elegidas (máximo 5, correlación <= 0,9): **2**.

| Id | Familia | Variante | TRAIN Sharpe (DD) | Otra Sharpe (DD) | TEST Sharpe (DD) | TEST rent. (B&H) | Sharpe deflactado | Significativa |
|---|---|---|---|---|---|---|---|---|
| U0229 | F04 Momentum de serie temporal diario (con umbral) | L=182,umbral=0.1 | 0.98 (-10.7 %) | 0.42 (-18.8 %) | 0.85 (-18.3 %) | 169.8 % (294.2 %) | 0.237 | NO (sin significación estadística) |
| U0750 | F14 Cerca del máximo de N días | ventana=180,x=0.15 | 0.95 (-16.4 %) | 0.52 (-29.9 %) | 0.97 (-23.5 %) | 267.2 % (294.2 %) | 0.219 | NO (sin significación estadística) |
